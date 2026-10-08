import os
import json
import uuid
import joblib
import numpy as np
from PIL import Image, ImageDraw
import scipy.ndimage as ndi
from typing import Dict, Any, List, Tuple

from ml.preprocessing.cielab_extractor import extract_mango_features, rgb_to_cielab
from ml.inference.mango_detector import MangoDetector
from ml.inference.quality_decision_tree import MangoQualityDecisionLayer

# Reference the training decision fusion class so joblib can unpickle cleanly
from ml.training.train_mango import DecisionFusionClassifier

MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models', 'mango'))
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
BACKEND_UPLOADS_DIR = os.path.abspath(os.path.join(WORKSPACE_ROOT, 'backend', 'uploads', 'mango_inspections'))
ROOT_UPLOADS_DIR = os.path.abspath(os.path.join(WORKSPACE_ROOT, 'uploads', 'mango_inspections'))
os.makedirs(BACKEND_UPLOADS_DIR, exist_ok=True)
os.makedirs(ROOT_UPLOADS_DIR, exist_ok=True)
UPLOADS_DIR = BACKEND_UPLOADS_DIR

def sanitize_for_json(obj):
    """
    Recursively converts NumPy types, arrays, bytes, and non-serializable objects
    into standard JSON-compliant Python primitives.
    """
    if isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {str(k): sanitize_for_json(v) for k, v in obj.items() if k not in ("mask", "crop_mask", "crop", "annotated_image_bytes")}
    elif isinstance(obj, (list, tuple)):
        return [sanitize_for_json(x) for x in obj]
    elif isinstance(obj, (bytes, bytearray)):
        return None
    elif isinstance(obj, Image.Image):
        return None
    return obj

class MangoQualityScanner:
    """
    Production inference engine for Mango Quality Inspection.
    Executes the decoupled multi-task mango inspection pipeline:
    Image -> Image Quality Validation -> Instance Watershed/Edge Separation ->
    Individual Mango Crops ->
    Task 1: Individual Mango Detection & Instance Localization
    Task 2: Visual Ripeness Estimation (Ripeness != Quality)
    Task 3: Defect & Disease Analysis (Spatial Lesion Detection + ML Classification)
    Task 4: Grounded Visual Explainability & Evidence Mapping
    Task 5: Lot-Level Aggregation & Final Lot Quality Assessment.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MangoQualityScanner, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_filename="mango_best_model.joblib"):
        if getattr(self, '_initialized', False):
            return

        self.model_path = os.path.join(MODELS_DIR, model_filename)
        self.detector = MangoDetector()
        self.decision_layer = MangoQualityDecisionLayer()
        self.model = None
        self.model_version = "mango-quality-v1"
        self.classes = ["Anthracnose", "Bacterial Canker", "Healthy", "Other", "Scab", "Stem End Rot"]
        self._load_model()
        self._initialized = True

    def _load_model(self):
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                if hasattr(self.model, 'classes_'):
                    self.classes = list(self.model.classes_)

                meta_p = os.path.join(MODELS_DIR, "model_metadata.json")
                if os.path.exists(meta_p):
                    with open(meta_p, 'r', encoding='utf-8') as f:
                        m_meta = json.load(f)
                        self.model_type = m_meta.get("best_model_name", "RBF SVM (CIELAB L*a*b*)")
                        self.model_version = m_meta.get("model_version", "mango-quality-v1")
                else:
                    self.model_type = "RBF SVM (CIELAB L*a*b*)"

                print(f"[MangoQualityScanner] Loaded model artifact from {self.model_path} ({self.model_type})")
            except Exception as e:
                print(f"[MangoQualityScanner] Warning: Could not load model: {e}")
        else:
            print(f"[MangoQualityScanner] Model artifact not found at {self.model_path} yet.")

    def reload_model(self):
        self._load_model()

    def estimate_ripeness(self, crop_img: Image.Image) -> Tuple[str, float]:
        """
        Task 2: Estimates physiological ripeness stage of an individual mango fruit:
        - Ripe
        - Nearly Ripe
        - Not Ripe
        - Overripe
        - Uncertain

        Uses comprehensive spatial surface distribution across both HSV and CIELAB color spaces.
        Calculates chromatic fractions of green, turning/breaker, yellow, and blush tissue.
        CRITICAL: Ripeness is evaluated INDEPENDENTLY of defect/quality status.
        A mango can be Ripe + Defective or Unripe + Healthy.
        """
        try:
            thumb = crop_img.resize((80, 80), Image.Resampling.BILINEAR)
            rgb_f = np.array(thumb, dtype=np.float32) / 255.0
            r, g, b = rgb_f[..., 0], rgb_f[..., 1], rgb_f[..., 2]

            cmax = np.maximum(np.maximum(r, g), b)
            cmin = np.minimum(np.minimum(r, g), b)
            diff = cmax - cmin

            h_ch = np.zeros_like(r)
            mask_r = (cmax == r) & (diff > 0.001)
            mask_g = (cmax == g) & (diff > 0.001)
            mask_b = (cmax == b) & (diff > 0.001)

            h_ch[mask_r] = (60.0 * ((g[mask_r] - b[mask_r]) / diff[mask_r]) + 360.0) % 360.0
            h_ch[mask_g] = (60.0 * ((b[mask_g] - r[mask_g]) / diff[mask_g]) + 120.0) % 360.0
            h_ch[mask_b] = (60.0 * ((r[mask_b] - g[mask_b]) / diff[mask_b]) + 240.0) % 360.0

            s_ch = np.where(cmax > 0.001, diff / (cmax + 1e-6), 0.0)
            v_ch = cmax

            peel_fg = (v_ch > 0.15) & (v_ch < 0.98) & (s_ch > 0.12)
            total_peel = float(np.sum(peel_fg))
            if total_peel < 20:
                return "Uncertain", 50.0

            green_fraction = float(np.sum(peel_fg & (h_ch >= 65.0) & (h_ch <= 130.0))) / total_peel
            turning_fraction = float(np.sum(peel_fg & (h_ch >= 48.0) & (h_ch < 65.0))) / total_peel
            yellow_fraction = float(np.sum(peel_fg & (h_ch >= 25.0) & (h_ch < 48.0))) / total_peel
            blush_fraction = float(np.sum(peel_fg & ((h_ch < 25.0) | (h_ch >= 340.0)))) / total_peel
            overripe_dark = float(np.sum(peel_fg & (v_ch < 0.35) & (s_ch < 0.35))) / total_peel

            if overripe_dark > 0.35 and (yellow_fraction + turning_fraction) > 0.30:
                return "Overripe", round(min(96.0, 75.0 + overripe_dark * 30.0), 1)
            elif (yellow_fraction + blush_fraction) >= 0.50:
                conf = min(98.0, 75.0 + (yellow_fraction + blush_fraction) * 25.0)
                return "Ripe", round(conf, 1)
            elif green_fraction >= 0.65:
                conf = min(98.0, 75.0 + green_fraction * 25.0)
                return "Not Ripe", round(conf, 1)
            elif (turning_fraction + yellow_fraction) >= 0.35 or (turning_fraction >= 0.25):
                conf = min(92.0, 70.0 + (turning_fraction + yellow_fraction) * 25.0)
                return "Nearly Ripe", round(conf, 1)
            elif yellow_fraction > green_fraction:
                return "Nearly Ripe", 72.0
            else:
                return "Not Ripe", 72.0
        except Exception:
            return "Uncertain", 50.0

    def analyze_fruit_defects(self, crop_img: Image.Image, inst_mask: np.ndarray = None, crop_mask: np.ndarray = None, bbox: List[int] = None) -> Dict[str, Any]:
        """
        Task 3 & 4: Performs localized spatial defect analysis and visual explainability
        on an individual mango fruit:
        - Runs at native resolution (no destructive downscaling) to detect small black spots.
        - Combines multi-signal contrast (luminance drop relative to peel, deep necrotic pits, scab gradient).
        - Strictly operates within the individual fruit boundary.
        - Excludes white crop padding, black/grey background pixels, and touching seam shadows.
        - Employs boundary safety margin erosion so seam/edge transition pixels are never counted as defects.
        - Calculates visible defect surface area percentage strictly as:
          (defect pixels inside valid mango mask) / (total valid mango mask pixels) * 100.
        """
        w, h = crop_img.size
        rgb_arr = np.array(crop_img, dtype=np.float32)
        r = rgb_arr[..., 0]
        g = rgb_arr[..., 1]
        b = rgb_arr[..., 2]

        # CIELAB estimation
        l_est = 0.299 * r + 0.587 * g + 0.114 * b
        a_est = (r - g) * 0.7 + 128.0
        b_est = (r + g - 2.0 * b) * 0.4 + 128.0
        chroma = np.hypot(a_est - 128.0, b_est - 128.0)

        # 1. Determine individual mango peel mask
        fruit_peel = None
        if crop_mask is not None and isinstance(crop_mask, np.ndarray) and crop_mask.size > 0:
            if crop_mask.shape == (h, w):
                fruit_peel = crop_mask.astype(bool).copy()
            else:
                fruit_peel = np.array(Image.fromarray(crop_mask.astype(np.uint8)).resize((w, h), Image.Resampling.NEAREST)) > 0
        elif inst_mask is not None and isinstance(inst_mask, np.ndarray) and inst_mask.size > 0:
            if inst_mask.shape == (h, w):
                fruit_peel = inst_mask.astype(bool).copy()
            elif bbox is not None and len(bbox) == 4:
                bx, by, bw, bh = [int(v) for v in bbox]
                im_h, im_w = inst_mask.shape
                sy1 = max(0, min(im_h, by))
                sy2 = max(0, min(im_h, by + bh))
                sx1 = max(0, min(im_w, bx))
                sx2 = max(0, min(im_w, bx + bw))
                sub = inst_mask[sy1:sy2, sx1:sx2]
                if sub.shape == (h, w):
                    fruit_peel = sub.astype(bool).copy()
                else:
                    fruit_peel = np.array(Image.fromarray(sub.astype(np.uint8)).resize((w, h), Image.Resampling.NEAREST)) > 0
            else:
                fruit_peel = np.array(Image.fromarray(inst_mask.astype(np.uint8)).resize((w, h), Image.Resampling.NEAREST)) > 0

        if fruit_peel is None:
            is_yellow = (r > b * 1.08) & (g > b * 0.90) & (b_est > 128.0) & (l_est > 35.0) & (l_est < 248.0)
            is_green = (g > r * 0.90) & (g > b * 1.02) & (chroma > 8.0) & (l_est > 30.0) & (l_est < 245.0)
            is_breaking = (r > b * 1.04) & (g > b * 0.96) & (chroma > 10.0) & (l_est > 35.0) & (l_est < 248.0)
            fruit_peel = is_yellow | is_green | is_breaking
            fruit_peel = ndi.binary_fill_holes(ndi.binary_closing(fruit_peel, structure=np.ones((7, 7), dtype=bool)))

        # 2. Strict background exclusion
        # Exclude surrounding white padding outside mango crop, while preserving interior defects
        is_white_pad = (r > 245) & (g > 245) & (b > 245)
        fruit_peel = fruit_peel & (~is_white_pad)
        fruit_peel = ndi.binary_fill_holes(fruit_peel)

        # Retain dominant connected component to clean up stray background fragments
        lbl_f, n_f = ndi.label(fruit_peel)
        if n_f > 1:
            sizes_f = ndi.sum(fruit_peel, lbl_f, range(1, n_f + 1))
            max_idx = np.argmax(sizes_f) + 1
            fruit_peel = (lbl_f == max_idx)

        total_mango_pixels = float(np.sum(fruit_peel))
        if total_mango_pixels < 100:
            return {
                "affected_area_pct": 0.0,
                "defect_boxes": [],
                "defect_mask": np.zeros((h, w), dtype=bool),
                "total_defect_pixels": 0,
                "largest_defect_pixels": 0,
                "num_regions": 0,
                "confidence": 0.0
            }

        # 3. Boundary erosion safety margin
        # Prevents uncertain perimeter edge pixels and contact seam shadows from being counted as defects
        erode_rad = max(3, min(10, int(round(min(w, h) * 0.045))))
        inner_peel = ndi.binary_erosion(fruit_peel, structure=np.ones((erode_rad * 2 + 1, erode_rad * 2 + 1), dtype=bool))
        if np.sum(inner_peel) < 40:
            inner_peel = ndi.binary_erosion(fruit_peel, structure=np.ones((3, 3), dtype=bool))
        if np.sum(inner_peel) < 20:
            inner_peel = fruit_peel

        peel_L = l_est[inner_peel]
        median_L = float(np.median(peel_L))

        gx = ndi.sobel(l_est, axis=1)
        gy = ndi.sobel(l_est, axis=0)
        grad = np.hypot(gx, gy)

        # Multi-signal defect detection:
        dark_necrosis = (l_est < 75.0) & (l_est < (median_L - 15.0))
        sunken_black = (l_est < 45.0)
        collapsed = (l_est < 88.0) & (chroma < 20.0) & (l_est < (median_L - 25.0))
        scab_edge = (grad > 25.0) & (l_est < 85.0) & (l_est < (median_L - 28.0))

        # Strictly evaluate inside inner_peel & valid fruit_peel
        raw_defects = (dark_necrosis | sunken_black | collapsed | scab_edge) & inner_peel & fruit_peel

        # Reject natural healthy green peel
        is_healthy_green = (g > r * 1.08) & (g > b * 1.15) & (l_est > 55.0)
        raw_defects = raw_defects & (~is_healthy_green)

        # Filter noise, but strictly preserve real black spots (>= 6 pixels)
        lbl_d, n_d = ndi.label(raw_defects)
        sizes = ndi.sum(raw_defects, lbl_d, range(1, n_d + 1)) if n_d > 0 else []

        clean_mask = np.zeros_like(raw_defects, dtype=bool)
        defect_boxes = []
        largest_region = 0

        for idx_d, s in enumerate(sizes, 1):
            if s >= 6:
                clean_mask[lbl_d == idx_d] = True
                if s > largest_region:
                    largest_region = int(s)

                dys, dxs = np.where(lbl_d == idx_d)
                bx1 = int(np.min(dxs))
                by1 = int(np.min(dys))
                bw_b = int(np.max(dxs) - bx1 + 1)
                bh_b = int(np.max(dys) - by1 + 1)
                defect_boxes.append([bx1, by1, bw_b, bh_b])

        total_defect_pixels = int(np.sum(clean_mask))
        # Defect percentage strictly calculated over valid mango pixels, NOT bounding box
        affected_pct = round((total_defect_pixels / max(1.0, total_mango_pixels)) * 100.0, 1)

        # Sort defect boxes by size descending
        defect_boxes.sort(key=lambda b: b[2] * b[3], reverse=True)

        conf = min(99.0, 75.0 + min(22.0, affected_pct * 4.0)) if total_defect_pixels > 0 else 0.0

        return {
            "affected_area_pct": affected_pct,
            "defect_boxes": defect_boxes[:16],
            "defect_mask": clean_mask,
            "total_defect_pixels": total_defect_pixels,
            "largest_defect_pixels": largest_region,
            "num_regions": len(defect_boxes),
            "confidence": round(conf, 1)
        }

    def inspect_lot_image(self, image_input, inspection_code: str = None) -> Dict[str, Any]:
        """
        Analyze a representative sample photograph containing one or multiple mangoes.
        Produces individual detection results (bounding boxes, condition, ripeness, quality, evidence)
        and lot-level aggregated quality assessment.
        """
        if self.model is None:
            self._load_model()
            if self.model is None:
                raise RuntimeError("Mango quality model artifact is not loaded. Train model first.")

        if not inspection_code:
            inspection_code = f"INSP-{uuid.uuid4().hex[:8].upper()}"

        os.makedirs(UPLOADS_DIR, exist_ok=True)

        # 1. Detection of individual mangoes with distance-transform & edge-crease separation
        original_img, raw_boxes = self.detector.detect_mangoes(image_input)

        detections = []
        class_counts = {
            "Healthy": 0,
            "Anthracnose": 0,
            "Scab": 0,
            "Bacterial Canker": 0,
            "Stem End Rot": 0,
            "Other": 0
        }

        ripeness_counts = {
            "Ripe": 0,
            "Nearly Ripe": 0,
            "Not Ripe": 0,
            "Overripe": 0,
            "Uncertain": 0
        }

        confidences = []

        scaler = self.model.named_steps.get('scaler') if hasattr(self.model, 'named_steps') else None
        use_l = (scaler.n_features_in_ == 24) if scaler and hasattr(scaler, 'n_features_in_') else False

        # 2. Individual mango independent analysis: Task 2 (Ripeness) + Task 3 (Quality/Defects)
        for b in raw_boxes:
            crop_img = b['crop']

            # Task 2: Ripeness estimation (Maturity only, independent of quality)
            ripeness_stage, ripeness_conf = self.estimate_ripeness(crop_img)

            # Task 3: Spatial lesion analysis & defect extraction using exact crop mask and bbox
            defect_info = self.analyze_fruit_defects(
                crop_img,
                inst_mask=b.get('mask'),
                crop_mask=b.get('crop_mask'),
                bbox=b.get('box')
            )
            affected_pct = defect_info["affected_area_pct"]
            defect_regions = defect_info["defect_boxes"]

            # Feature extraction: RGB -> CIELAB -> statistics for ML classification
            feat_vec = extract_mango_features(crop_img, use_l=use_l).reshape(1, -1)

            # ML disease model prediction
            raw_pred_class = str(self.model.predict(feat_vec)[0])
            if hasattr(self.model, 'predict_proba'):
                proba = self.model.predict_proba(feat_vec)[0]
                cls_idx = list(self.model.classes_).index(raw_pred_class)
                top_conf = float(proba[cls_idx]) * 100.0
                healthy_idx = list(self.model.classes_).index("Healthy") if "Healthy" in self.model.classes_ else -1
                healthy_prob = float(proba[healthy_idx]) * 100.0 if healthy_idx >= 0 else 50.0
                disease_prob = 100.0 - healthy_prob
                conf = max(top_conf, disease_prob) if raw_pred_class != "Healthy" else top_conf
            else:
                conf = 88.0

            # Decision Tree Quality Decision Layer:
            # Evaluates multi-task vision outputs (Ripeness, Pathogen prediction, Lesion area %, Geometry)
            eval_res = self.decision_layer.evaluate_mango(
                ripeness=ripeness_stage,
                ripeness_conf=ripeness_conf,
                defect_class=raw_pred_class,
                defect_conf=conf,
                visible_defect_pct=affected_pct,
                defect_boxes=defect_regions
            )
            health_status = eval_res["health_status"]
            quality_grade = eval_res["quality_grade"]
            defect_severity = eval_res["defect_severity"]
            estimated_total_severity = eval_res["estimated_total_surface_severity"]
            visual_evidence = eval_res["grounded_rationale"]
            defect_type = raw_pred_class if health_status == "Defective" and raw_pred_class != "Healthy" else ("Surface Blemish" if health_status == "Defective" else "None")

            class_counts[defect_type if defect_type in class_counts else ("Other" if health_status == "Defective" else "Healthy")] += 1
            ripeness_counts[ripeness_stage if ripeness_stage in ripeness_counts else "Uncertain"] += 1
            confidences.append(conf)

            # Draw clearly visible defect boundary highlights on individual crop
            highlighted_crop = crop_img.copy().convert("RGBA")
            if defect_regions:
                ov_crop = Image.new("RGBA", crop_img.size, (0, 0, 0, 0))
                d_ov = ImageDraw.Draw(ov_crop)
                for db in defect_regions:
                    lx1, ly1, lw_box, lh_box = db
                    d_ov.rectangle([lx1, ly1, lx1 + lw_box, ly1 + lh_box], outline=(239, 68, 68, 255), width=2)
                    d_ov.rectangle([lx1, ly1, lx1 + lw_box, ly1 + lh_box], fill=(239, 68, 68, 80))
                highlighted_crop = Image.alpha_composite(highlighted_crop, ov_crop).convert("RGB")
            else:
                highlighted_crop = crop_img.convert("RGB")

            # Save individual crop with highlighted defects to both backend and root uploads directories
            crop_fname = f"{inspection_code}_crop_{b['index']}.jpg"
            crop_path_backend = os.path.join(BACKEND_UPLOADS_DIR, crop_fname)
            crop_path_root = os.path.join(ROOT_UPLOADS_DIR, crop_fname)
            highlighted_crop.save(crop_path_backend, quality=92)
            try:
                highlighted_crop.save(crop_path_root, quality=92)
            except Exception:
                pass
            rel_crop_url = f"/uploads/mango_inspections/{crop_fname}"

            # Transparent Baseline AI Potential Grading & Explainability Factors (Part 10)
            sig_defect_count = sum(1 for db in defect_regions if (db[2] * db[3] >= 15))
            crop_np = np.array(crop_img)
            if crop_np.size > 0:
                color_std = float(np.std(crop_np, axis=(0, 1)).mean())
                uniformity_score = round(max(10.0, min(100.0, 100.0 - (color_std * 0.8))), 1)
            else:
                uniformity_score = 75.0

            aspect_ratio = round(float(b.get('aspect_ratio', 1.0)), 2)
            solidity = round(float(b.get('solidity', 1.0)), 2)
            area_px = int(b.get('area', 0))

            if solidity < 0.82:
                visibility_status = "Partially Occluded"
            elif b['box'][0] <= 5 or b['box'][1] <= 5:
                visibility_status = "Edge Boundary"
            else:
                visibility_status = "Full View"

            comm_grade = eval_res.get("commercial_grade", "Grade A" if health_status == "Healthy" else "Grade C")
            ai_estimated_grade = comm_grade
            potential_grade = f"{comm_grade} (AI Estimate)"

            rationale_parts = []
            if comm_grade == "Grade A":
                rationale_parts.append(f"Assigned Potential Grade A: Sound peel with {affected_pct:.1f}% defect coverage.")
            elif comm_grade == "Grade B":
                rationale_parts.append(f"Assigned Potential Grade B: Minor markings ({affected_pct:.1f}% defect coverage, {sig_defect_count} spot(s)).")
            elif comm_grade == "Grade C":
                rationale_parts.append(f"Assigned Potential Grade C: Noticeable {defect_type} lesions ({affected_pct:.1f}% defect coverage, {sig_defect_count} spot(s)).")
            else:
                rationale_parts.append(f"Assigned Potential Reject: Severe {defect_type} rot ({affected_pct:.1f}% coverage exceeds acceptable threshold).")

            rationale_parts.append(f"Maturity: {ripeness_stage} ({round(ripeness_conf, 1)}% conf).")
            rationale_parts.append(f"Peel uniformity score: {uniformity_score}/100. Shape ratio: {aspect_ratio} ({visibility_status}).")
            rationale_parts.append("Note: Transparent AI baseline estimate; not a statutory APMC certification.")
            grading_rationale = " ".join(rationale_parts)

            grading_factors = {
                "ripeness": ripeness_stage,
                "ripeness_confidence": round(ripeness_conf, 1),
                "visible_defect_pct": affected_pct,
                "significant_defect_count": sig_defect_count,
                "colour_uniformity_score": uniformity_score,
                "shape_aspect_ratio": aspect_ratio,
                "solidity": solidity,
                "area_px": area_px,
                "visibility": visibility_status,
                "defect_confidence": round(conf, 1),
                "is_official_standard": False,
                "disclaimer": "AI-estimated potential grade based on optical inspection baseline; not an official statutory APMC certification."
            }

            box_coords = b['box']
            detections.append({
                "sample_index": b['index'],
                "box": box_coords,
                "bbox": box_coords,
                "predicted_class": defect_type if health_status == "Defective" else "Healthy",
                "condition": defect_type if health_status == "Defective" else "Healthy",
                "class": defect_type if health_status == "Defective" else "Healthy",
                "health_status": health_status,
                "defect_type": defect_type,
                "defect_severity": defect_severity,
                "ripeness": ripeness_stage,
                "ripeness_confidence": ripeness_conf,
                "confidence": round(conf, 1),
                "quality_grade": quality_grade,
                "commercial_grade": comm_grade,
                "potential_grade": potential_grade,
                "ai_estimated_grade": ai_estimated_grade,
                "grading_rationale": grading_rationale,
                "grading_factors": grading_factors,
                "affected_area_pct": affected_pct,
                "visible_defect_pct": affected_pct,
                "estimated_total_surface_severity": estimated_total_severity,
                "visual_evidence": visual_evidence,
                "decision_path": eval_res["decision_path"],
                "defect_regions": [[int(c) for c in r] for r in defect_regions],
                "crop_url": rel_crop_url,
                "crop": crop_img,
                "mask": b.get('mask'),
                "crop_mask": b.get('crop_mask'),
                "area": area_px,
                "contour": [[int(pt[0]), int(pt[1])] for pt in b.get('contour', [])],
                "centroid": [int(b.get('centroid', (0, 0))[0]), int(b.get('centroid', (0, 0))[1])]
            })

        # 3. Task 5: Lot-Level Aggregation strictly calculated from individual mango results
        total_samples = len(detections)
        healthy_count = sum(1 for d in detections if d["health_status"] == "Healthy")
        defect_count = sum(1 for d in detections if d["health_status"] == "Defective")
        uncertain_count = sum(1 for d in detections if d["health_status"] == "Uncertain")

        lot_defect_pct = round((defect_count / total_samples * 100.0), 1) if total_samples > 0 else 0.0
        avg_confidence = round(float(np.mean(confidences)), 1) if confidences else 0.0

        # Grade counts across 6-tier quality distribution
        grade_counts = {
            "Excellent": sum(1 for d in detections if d.get("quality_grade") == "Excellent"),
            "Very Good": sum(1 for d in detections if d.get("quality_grade") == "Very Good"),
            "Good": sum(1 for d in detections if d.get("quality_grade") == "Good"),
            "Slightly Defective": sum(1 for d in detections if d.get("quality_grade") == "Slightly Defective"),
            "Defective": sum(1 for d in detections if d.get("quality_grade") == "Defective"),
            "Reject": sum(1 for d in detections if d.get("quality_grade") == "Reject"),
        }

        # Lot-level quality assessment rules:
        if total_samples == 0:
            lot_quality_grade = "Needs Review"
            visual_grade = "Needs Review"
            status = "NEEDS_REVIEW"
        elif uncertain_count > 0.4 * total_samples or avg_confidence < 60.0:
            lot_quality_grade = "Manual Review Required"
            visual_grade = "Manual Review Required"
            status = "NEEDS_REVIEW"
        elif grade_counts["Reject"] > 0.10 * total_samples or lot_defect_pct > 30.0:
            lot_quality_grade = "Reject"
            visual_grade = "Reject"
            status = "COMPLETED"
        elif grade_counts["Defective"] + grade_counts["Reject"] > 0.20 * total_samples:
            lot_quality_grade = "Defective"
            visual_grade = "Grade C"
            status = "COMPLETED"
        elif grade_counts["Slightly Defective"] > 0.30 * total_samples or lot_defect_pct > 15.0:
            lot_quality_grade = "Slightly Defective"
            visual_grade = "Grade B"
            status = "COMPLETED"
        elif grade_counts["Excellent"] + grade_counts["Very Good"] >= 0.70 * total_samples:
            lot_quality_grade = "Excellent" if grade_counts["Excellent"] >= 0.50 * total_samples else "Very Good"
            visual_grade = "Grade A"
            status = "COMPLETED"
        else:
            lot_quality_grade = "Good"
            visual_grade = "Grade B"
            status = "COMPLETED"

        # 4. Save annotated image with individual bounding boxes, defect overlays & decoupled badges
        annotated_fname = f"{inspection_code}_annotated.jpg"
        annotated_path_backend = os.path.join(BACKEND_UPLOADS_DIR, annotated_fname)
        annotated_path_root = os.path.join(ROOT_UPLOADS_DIR, annotated_fname)
        self.detector.annotate_image(original_img, detections, save_path=annotated_path_backend)
        try:
            self.detector.annotate_image(original_img, detections, save_path=annotated_path_root)
        except Exception:
            pass
        annotated_url = f"/uploads/mango_inspections/{annotated_fname}"
        annotated_bytes = None
        if os.path.exists(annotated_path_backend):
            with open(annotated_path_backend, "rb") as af:
                annotated_bytes = af.read()

        # 5. Generate and save the 10 DEBUG mode visual stages
        lot_summary = {
            "total_samples": total_samples,
            "healthy_count": healthy_count,
            "defect_count": defect_count,
            "lot_defect_pct": lot_defect_pct,
            "visual_grade": visual_grade,
            "lot_potential_grade": f"{visual_grade} (AI Estimate)",
        }
        debug_images = self.detector.generate_debug_images(original_img, detections, lot_summary=lot_summary)
        debug_urls = {}
        for dbg_key, dbg_img in debug_images.items():
            dbg_fname = f"{inspection_code}_{dbg_key}.jpg"
            dbg_p_backend = os.path.join(BACKEND_UPLOADS_DIR, dbg_fname)
            dbg_p_root = os.path.join(ROOT_UPLOADS_DIR, dbg_fname)
            dbg_img.save(dbg_p_backend, quality=90)
            try:
                dbg_img.save(dbg_p_root, quality=90)
            except Exception:
                pass
            debug_urls[dbg_key] = f"/uploads/mango_inspections/{dbg_fname}"

        return {
            "inspection_code": inspection_code,
            "crop": "Mango",
            "model_version": self.model_version,
            "model_type": getattr(self, "model_type", "RBF SVM (CIELAB L*a*b*)"),
            "sample_count": total_samples,
            "mangoes_detected": total_samples,
            "healthy": healthy_count,
            "healthy_count": healthy_count,
            "defect_count": defect_count,
            "uncertain_count": uncertain_count,
            "anthracnose": class_counts.get("Anthracnose", 0),
            "anthracnose_count": class_counts.get("Anthracnose", 0),
            "scab": class_counts.get("Scab", 0),
            "scab_count": class_counts.get("Scab", 0),
            "bacterial_canker": class_counts.get("Bacterial Canker", 0),
            "bacterial_canker_count": class_counts.get("Bacterial Canker", 0),
            "stem_end_rot": class_counts.get("Stem End Rot", 0),
            "stem_end_rot_count": class_counts.get("Stem End Rot", 0),
            "other": class_counts.get("Other", 0),
            "other_count": class_counts.get("Other", 0),
            "ripe_count": ripeness_counts.get("Ripe", 0),
            "nearly_ripe_count": ripeness_counts.get("Nearly Ripe", 0),
            "not_ripe_count": ripeness_counts.get("Not Ripe", 0),
            "overripe_count": ripeness_counts.get("Overripe", 0),
            "ripeness_summary": {
                "Ripe": ripeness_counts.get("Ripe", 0),
                "Nearly Ripe": ripeness_counts.get("Nearly Ripe", 0),
                "Not Ripe": ripeness_counts.get("Not Ripe", 0),
                "Overripe": ripeness_counts.get("Overripe", 0),
                "Uncertain": ripeness_counts.get("Uncertain", 0)
            },
            "grade_counts": grade_counts,
            "lot_quality_grade": lot_quality_grade,
            "lot_potential_grade": f"{visual_grade} (AI Estimate)",
            "ai_estimated_grade": visual_grade,
            "lot_grading_summary": f"Lot evaluation: {visual_grade} based on {total_samples} sampled fruit instance(s) ({healthy_count} Healthy, {defect_count} Defective, {uncertain_count} Uncertain). Average defect rate: {lot_defect_pct}%.",
            "grading_disclaimer": "AI-estimated potential grade based on multi-factor optical analysis; transparent baseline for decision support, not an official statutory APMC certification.",
            "affected_percentage": lot_defect_pct,
            "visual_grade": visual_grade,
            "confidence": avg_confidence,
            "status": status,
            "annotated_image_url": annotated_url,
            "annotated_image_bytes": annotated_bytes,
            "class_counts": class_counts,
            "debug_images": debug_urls,
            "detections": detections
        }

    def inspect_multi_view_mango(self, views: List[Image.Image], mango_id: str = "Mango-1") -> Dict[str, Any]:
        """
        Multi-View Inspection Workflow:
        Combines 2-3 images of different visible sides of the SAME mango.
        Aggregates observed defects, increases total observed surface area coverage from ~45% to ~85%,
        and tightens the 3D surface uncertainty range.
        """
        view_results = []
        for idx, view_img in enumerate(views):
            defect_info = self.analyze_fruit_defects(view_img)
            ripeness_stage, r_conf = self.estimate_ripeness(view_img)
            view_results.append({
                "view_index": idx + 1,
                "visible_defect_pct": defect_info["affected_area_pct"],
                "defect_boxes": defect_info["defect_boxes"],
                "ripeness": ripeness_stage,
                "ripeness_conf": r_conf
            })

        avg_visible_pct = float(np.mean([v["visible_defect_pct"] for v in view_results]))
        max_visible_pct = float(np.max([v["visible_defect_pct"] for v in view_results]))
        all_boxes = [b for v in view_results for b in v["defect_boxes"]]

        # With multi-view coverage, observed surface is ~85%.
        # Uncertainty interval contracts significantly:
        est_min = round(avg_visible_pct * 0.85, 1)
        est_max = round(min(100.0, max_visible_pct * 1.15), 1)

        consensus_ripeness = view_results[0]["ripeness"]
        eval_res = self.decision_layer.evaluate_mango(
            ripeness=consensus_ripeness,
            ripeness_conf=view_results[0]["ripeness_conf"],
            defect_class="Anthracnose" if avg_visible_pct >= 4.0 else "Healthy",
            defect_conf=85.0 if avg_visible_pct >= 4.0 else 90.0,
            visible_defect_pct=avg_visible_pct,
            defect_boxes=all_boxes
        )

        return {
            "mango_id": mango_id,
            "views_analyzed": len(views),
            "surface_coverage_est": f"{min(95, len(views) * 45)}%",
            "multi_view_avg_defect_pct": avg_visible_pct,
            "estimated_total_surface_severity": {
                "min_pct": est_min,
                "max_pct": est_max,
                "range_str": f"{est_min}% - {est_max}%"
            },
            "consensus_ripeness": consensus_ripeness,
            "health_status": eval_res["health_status"],
            "quality_grade": eval_res["quality_grade"],
            "decision_path": eval_res["decision_path"],
            "views_breakdown": view_results
        }

def get_mango_quality_scanner() -> MangoQualityScanner:
    """Return singleton instance of MangoQualityScanner."""
    return MangoQualityScanner()
