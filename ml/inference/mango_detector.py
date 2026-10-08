import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import scipy.ndimage as ndi
from scipy.spatial import ConvexHull
from typing import Dict, Any, List, Tuple

class MangoDetector:
    """
    Object-level multi-mango detection and instance separation engine.
    Uses Euclidean distance transform (EDT) + marker-controlled Watershed +
    boundary concavity/crease evidence + geometric convexity/solidity validation
    to isolate individual mango fruits accurately even when touching or overlapping,
    while strictly preventing false over-segmentation on single fruits.
    """
    def __init__(self, min_area=600, max_area_ratio=0.98):
        self.min_area = min_area
        self.max_area_ratio = max_area_ratio
        self.last_debug_data = {}

    def validate_image(self, image_input):
        """
        Validates image format and performs essential quality checks:
        - Minimum resolution (>= 100x100)
        - Excessive darkness / underexposure (< 25)
        - Excessive brightness / overexposure (> 248)
        - Severe blur detection via Laplacian variance (< 8.0)
        """
        if isinstance(image_input, (bytes, bytearray)):
            from io import BytesIO
            img = Image.open(BytesIO(image_input)).convert('RGB')
        elif isinstance(image_input, str):
            if not os.path.exists(image_input):
                raise ValueError(f"Image file does not exist at {image_input}")
            img = Image.open(image_input).convert('RGB')
        elif isinstance(image_input, Image.Image):
            img = image_input.convert('RGB')
        else:
            raise ValueError("Invalid image input: Expected file path, bytes, or PIL Image.")

        w, h = img.size
        if w < 100 or h < 100:
            raise ValueError(
                f"Image quality insufficient: Dimensions ({w}x{h}) are too small for inspection. "
                "Minimum 100x100 resolution required."
            )

        rgb_arr = np.array(img, dtype=np.float32)

        mean_brightness = float(np.mean(rgb_arr))
        if mean_brightness < 25.0:
            raise ValueError(
                "Image quality insufficient: Photograph is excessively dark (underexposed). "
                "Please retake the photograph with adequate illumination."
            )
        if mean_brightness > 248.0:
            raise ValueError(
                "Image quality insufficient: Photograph is excessively bright (overexposed / washed out). "
                "Please retake the photograph without excessive glare."
            )

        # Severe blur check via Laplacian variance on grayscale
        gray = 0.299 * rgb_arr[..., 0] + 0.587 * rgb_arr[..., 1] + 0.114 * rgb_arr[..., 2]
        if max(w, h) > 800:
            scale_blur = 800.0 / max(w, h)
            gray = ndi.zoom(gray, scale_blur, order=1)
        lap = ndi.laplace(gray)
        blur_variance = float(np.var(lap))
        if blur_variance < 8.0:
            raise ValueError(
                "Image quality insufficient: Photograph is severely blurred. "
                "Please hold the camera steady and retake with clear optical focus."
            )

        return img

    @staticmethod
    def _get_convex_hull_area(mask: np.ndarray) -> float:
        """Calculates area of the 2D convex hull of a binary mask."""
        ys, xs = np.where(mask)
        if len(xs) < 4:
            return float(len(xs))
        points = np.column_stack((xs, ys))
        try:
            hull = ConvexHull(points)
            return float(hull.volume)
        except Exception:
            return float(len(xs))

    @staticmethod
    def _extract_contour_points(mask: np.ndarray) -> List[Tuple[int, int]]:
        """Extracts ordered outer contour boundary coordinates."""
        eroded = ndi.binary_erosion(mask, structure=np.ones((3, 3), dtype=bool))
        boundary = mask & (~eroded)
        ys, xs = np.where(boundary)
        if len(xs) == 0:
            return []
        cx, cy = np.mean(xs), np.mean(ys)
        angles = np.arctan2(ys - cy, xs - cx)
        order = np.argsort(angles)
        step = max(1, len(order) // 80)
        return [(int(xs[idx]), int(ys[idx])) for idx in order[::step]]

    def detect_mangoes(self, image_input, return_debug: bool = False):
        """
        Detects, separates, and isolates individual mango fruits.
        Produces one instance mask/contour/crop per physical fruit.
        Uses boundary evidence, EDT peaks, and post-watershed convexity validation.
        """
        img = self.validate_image(image_input)
        orig_w, orig_h = img.size

        # Scale proxy for efficient, robust segmentation
        max_dim = 640
        scale = min(1.0, max_dim / max(orig_w, orig_h))
        sw = max(50, int(orig_w * scale))
        sh = max(50, int(orig_h * scale))
        img_small = img.resize((sw, sh), Image.Resampling.BILINEAR)
        rgb_np = np.array(img_small, dtype=np.float32)

        r = rgb_np[..., 0]
        g = rgb_np[..., 1]
        b = rgb_np[..., 2]

        # CIELAB representation approximation
        l_est = 0.299 * r + 0.587 * g + 0.114 * b
        a_est = (r - g) * 0.7 + 128.0
        b_est = (r + g - 2.0 * b) * 0.4 + 128.0
        chroma = np.hypot(a_est - 128.0, b_est - 128.0)

        # Foreground mango peel segmentation:
        # Accounts for ripe yellow/orange peel, green unripe peel, and breaking peel
        # Strictly rejects cool blue/grey/white background and dark non-mango shadows
        is_yellow = (r > b * 1.10) & (g > b * 0.92) & (b_est > 128.0) & (l_est > 35.0) & (l_est < 248.0)
        is_green = (g > r * 0.90) & (g > b * 1.02) & (chroma > 8.0) & (l_est > 30.0) & (l_est < 245.0)
        is_breaking = (r > b * 1.04) & (g > b * 0.96) & (chroma > 10.0) & (l_est > 35.0) & (l_est < 248.0)
        peel_raw = is_yellow | is_green | is_breaking

        struct = np.ones((7, 7), dtype=bool)
        peel_clean = ndi.binary_closing(peel_raw, structure=struct)
        peel_clean = ndi.binary_fill_holes(peel_clean)

        # Filter out tiny disconnected noise specks from peel_clean
        lbl_raw, n_raw = ndi.label(peel_clean)
        if n_raw > 1:
            raw_sizes = ndi.sum(peel_clean, lbl_raw, range(1, n_raw + 1))
            dom_raw = float(np.max(raw_sizes))
            min_keep = max(350.0, dom_raw * 0.05)
            filtered_peel = np.zeros_like(peel_clean)
            for idx_r, s in enumerate(raw_sizes, 1):
                if s >= min_keep:
                    filtered_peel[lbl_raw == idx_r] = True
            peel_clean = filtered_peel

        total_peel_pixels = float(np.sum(peel_clean))
        if total_peel_pixels < 250:
            self.last_debug_data = {
                'peel_clean': peel_clean,
                'markers': np.zeros_like(peel_clean, dtype=np.int32),
                'segmented_instances': np.zeros_like(peel_clean, dtype=np.int32),
                'scale': scale
            }
            if return_debug:
                return img, [], self.generate_debug_images(img, [])
            return img, []

        # Boundary edge gradient detection to find creases and contact seams
        gx = ndi.sobel(l_est, axis=1)
        gy = ndi.sobel(l_est, axis=0)
        grad = np.hypot(gx, gy)
        peel_grads = grad[peel_clean]
        p85 = np.percentile(peel_grads, 85) if len(peel_grads) > 0 else 35.0
        edge_thresh = max(28.0, float(p85))
        raw_edges = (grad > edge_thresh) & peel_clean

        # Filter out tiny texture noise: only keep continuous edge creases with area >= 20 px
        lbl_e, n_e = ndi.label(raw_edges)
        edge_sizes = ndi.sum(raw_edges, lbl_e, range(1, n_e + 1)) if n_e > 0 else []
        clean_creases = np.zeros_like(raw_edges, dtype=bool)
        for idx_e, s in enumerate(edge_sizes, 1):
            if s >= 20:
                clean_creases[lbl_e == idx_e] = True

        crease_barrier = ndi.binary_dilation(clean_creases, structure=np.ones((3, 3), dtype=bool))
        separated_peel = peel_clean & (~crease_barrier)
        separated_peel = ndi.binary_opening(separated_peel, structure=np.ones((5, 5), dtype=bool))

        lbl_cores, n_cores = ndi.label(separated_peel)
        sizes = ndi.sum(separated_peel, lbl_cores, range(1, n_cores + 1)) if n_cores > 0 else []

        valid_cores = np.zeros(separated_peel.shape, dtype=np.int32)
        valid_core_count = 0
        markers = np.zeros(separated_peel.shape, dtype=np.int32)
        marker_count = 0

        if n_cores > 0 and len(sizes) > 0:
            dom_size = float(np.max(sizes))
            med_size = float(np.median(sizes))
            min_core_thresh = max(350.0, dom_size * 0.18)
            dist_sep = ndi.distance_transform_edt(separated_peel)

            for idx_c, s in enumerate(sizes, 1):
                if s < min_core_thresh:
                    continue
                c_mask = (lbl_cores == idx_c)

                # Check if this core is large enough to contain multiple fused mangoes
                if s > max(18000.0, med_size * 1.7):
                    c_dist = dist_sep.copy()
                    c_dist[~c_mask] = 0.0
                    max_cd = float(np.max(c_dist))
                    fp = max(13, int(max_cd * 0.38)) | 1
                    c_peaks = (c_dist == ndi.maximum_filter(c_dist, footprint=np.ones((fp, fp), dtype=bool))) & (c_dist > max(12.0, max_cd * 0.35))
                    lbl_cp, n_cp = ndi.label(c_peaks)
                    if n_cp > 1:
                        peak_pts = []
                        for cp_i in range(1, n_cp + 1):
                            ys, xs = np.where(lbl_cp == cp_i)
                            peak_pts.append((float(np.mean(xs)), float(np.mean(ys)), float(np.mean(c_dist[ys, xs])), cp_i))
                        peak_pts.sort(key=lambda p: p[2], reverse=True)
                        min_peak_d = max(24.0, max_cd * 0.42)
                        kept_pts = []
                        for cx, cy, v, cp_i in peak_pts:
                            if not any(np.hypot(cx - kx, cy - ky) < min_peak_d for kx, ky in kept_pts):
                                marker_count += 1
                                markers[lbl_cp == cp_i] = marker_count
                                kept_pts.append((cx, cy))
                    else:
                        marker_count += 1
                        markers[c_mask] = marker_count
                else:
                    marker_count += 1
                    markers[c_mask] = marker_count

        # Fallback to EDT on full peel if crease cores yielded fewer than 2 markers
        if marker_count < 2:
            dist = ndi.distance_transform_edt(peel_clean)
            max_d = float(np.max(dist))
            footprint_rad = max(20, int(max_d * 0.42))
            local_max = (dist == ndi.maximum_filter(dist, footprint=np.ones((footprint_rad, footprint_rad), dtype=bool))) & (dist > max_d * 0.35) & peel_clean
            lbl_p, n_p = ndi.label(local_max)
            if n_p >= 2:
                peak_points = []
                for p_idx in range(1, n_p + 1):
                    ys, xs = np.where(lbl_p == p_idx)
                    val = float(np.mean(dist[ys, xs]))
                    peak_points.append((float(np.mean(xs)), float(np.mean(ys)), val, p_idx))
                peak_points.sort(key=lambda p: p[2], reverse=True)
                min_peak_dist = max(28.0, max_d * 0.45)
                kept_markers = np.zeros(peel_clean.shape, dtype=np.int32)
                kept_count = 0
                kept_centers = []
                for cx, cy, val, p_idx in peak_points:
                    too_close = False
                    for kx, ky in kept_centers:
                        if np.hypot(cx - kx, cy - ky) < min_peak_dist:
                            too_close = True
                            break
                    if not too_close:
                        kept_count += 1
                        kept_centers.append((cx, cy))
                        kept_markers[lbl_p == p_idx] = kept_count
                if kept_count >= 2:
                    markers = kept_markers
                else:
                    lbl_fallback, _ = ndi.label(peel_clean)
                    markers = lbl_fallback.astype(np.int32)
            else:
                lbl_fallback, _ = ndi.label(peel_clean)
                markers = lbl_fallback.astype(np.int32)

        # Geodesic Voronoi / Marker-controlled distance partition
        _, indices = ndi.distance_transform_edt(markers == 0, return_indices=True)
        segmented_instances = markers[indices[0], indices[1]]
        segmented_instances[~peel_clean] = 0

        # Resolve internal junction artifacts (clusters where intersecting fruits create an enclosed central core)
        init_labels = [l for l in np.unique(segmented_instances) if l > 0]
        if len(init_labels) > 1:
            for l in init_labels:
                m = (segmented_instances == l)
                if np.sum(m) == 0:
                    continue
                ext_touch = np.sum(ndi.binary_dilation(m, structure=np.ones((3, 3), dtype=bool)) & (~peel_clean))
                total_perim = np.sum(ndi.binary_dilation(m, structure=np.ones((3, 3), dtype=bool)) & (~m))
                if ext_touch < max(14, int(total_perim * 0.05)):
                    other_mask = (segmented_instances > 0) & (segmented_instances != l)
                    if np.sum(other_mask) > 0:
                        _, nn_idx = ndi.distance_transform_edt(~other_mask, return_indices=True)
                        segmented_instances[m] = segmented_instances[nn_idx[0][m], nn_idx[1][m]]

        # Post-watershed geometric validation & false-split merger
        labels = [l for l in np.unique(segmented_instances) if l > 0]
        changed = True
        while changed and len(labels) > 1:
            changed = False
            pairs = []
            for i in range(len(labels)):
                for j in range(i + 1, len(labels)):
                    l1, l2 = labels[i], labels[j]
                    m1 = (segmented_instances == l1)
                    m2 = (segmented_instances == l2)
                    m1_dil = ndi.binary_dilation(m1, structure=np.ones((5, 5), dtype=bool))
                    if np.sum(m1_dil & m2) > 0:
                        pairs.append((l1, l2))

            for l1, l2 in pairs:
                m1 = (segmented_instances == l1)
                m2 = (segmented_instances == l2)
                a1 = float(np.sum(m1))
                a2 = float(np.sum(m2))
                if a1 == 0 or a2 == 0:
                    continue

                # 1. Asymmetry / tiny fragment check (< 15% of pair)
                if (min(a1, a2) / max(a1, a2)) < 0.15:
                    segmented_instances[segmented_instances == l2] = l1
                    labels = [l for l in np.unique(segmented_instances) if l > 0]
                    changed = True
                    break

                # 2. Box containment check: if one bounding box is almost entirely inside the other
                y1_1, x1_1 = np.where(m1)
                y1_2, x1_2 = np.where(m2)
                bx1_1, bx2_1, by1_1, by2_1 = np.min(x1_1), np.max(x1_1), np.min(y1_1), np.max(y1_1)
                bx1_2, bx2_2, by1_2, by2_2 = np.min(x1_2), np.max(x1_2), np.min(y1_2), np.max(y1_2)

                inter_x = max(0, min(bx2_1, bx2_2) - max(bx1_1, bx1_2))
                inter_y = max(0, min(by2_1, by2_2) - max(by1_1, by1_2))
                inter_area = inter_x * inter_y
                box_area1 = (bx2_1 - bx1_1) * (by2_1 - by1_1)
                box_area2 = (bx2_2 - bx1_2) * (by2_2 - by1_2)
                containment = inter_area / max(1.0, min(box_area1, box_area2))

                if containment > 0.75:
                    segmented_instances[segmented_instances == l2] = l1
                    labels = [l for l in np.unique(segmented_instances) if l > 0]
                    changed = True
                    break

                # 3. Distance between proposed centers and seam core cut check:
                cy1, cx1 = np.mean(y1_1), np.mean(x1_1)
                cy2, cx2 = np.mean(y1_2), np.mean(x1_2)
                center_dist = float(np.hypot(cx1 - cx2, cy1 - cy2))
                m_comb = m1 | m2
                dist_comb = ndi.distance_transform_edt(m_comb)
                max_d_comb = float(np.max(dist_comb))
                min_realistic_center_dist = max(25.0, max_d_comb * 0.50)
                seam = ndi.binary_dilation(m1, structure=np.ones((3, 3), bool)) & ndi.binary_dilation(m2, structure=np.ones((3, 3), bool)) & m_comb
                seam_max = float(np.max(dist_comb[seam])) if np.sum(seam) > 0 else 0.0
                seam_ratio = seam_max / max(1.0, max_d_comb)

                if center_dist < min_realistic_center_dist or seam_ratio > 0.88:
                    segmented_instances[segmented_instances == l2] = l1
                    labels = [l for l in np.unique(segmented_instances) if l > 0]
                    changed = True
                    break

        # 5. Touching contact seam refinement between touching/overlapping mangoes
        unique_labels = [l for l in np.unique(segmented_instances) if l > 0]
        if len(unique_labels) > 1:
            for i in range(len(unique_labels)):
                for j in range(i + 1, len(unique_labels)):
                    l1, l2 = unique_labels[i], unique_labels[j]
                    m1 = (segmented_instances == l1)
                    m2 = (segmented_instances == l2)
                    m1_d = ndi.binary_dilation(m1, structure=np.ones((3, 3), dtype=bool))
                    m2_d = ndi.binary_dilation(m2, structure=np.ones((3, 3), dtype=bool))
                    seam_touch = m1_d & m2_d & peel_clean
                    if np.sum(seam_touch) > 0:
                        # Carve out the dark/grey contact shadow crease so neither fruit claims it
                        segmented_instances[seam_touch] = 0

        # 6. Build rich instance outputs mapped back to full resolution
        min_fruit_area_scaled = max(400.0, float(sw * sh) * 0.02)
        max_fruit_area_scaled = float(sw * sh) * 0.98

        orig_rgb_arr = np.array(img, dtype=np.float32)
        full_l = 0.299 * orig_rgb_arr[..., 0] + 0.587 * orig_rgb_arr[..., 1] + 0.114 * orig_rgb_arr[..., 2]

        valid_detections = []
        for l in unique_labels:
            inst_mask_s = (segmented_instances == l)
            area_s = float(np.sum(inst_mask_s))
            if area_s < min_fruit_area_scaled or area_s > max_fruit_area_scaled:
                continue

            ys_s, xs_s = np.where(inst_mask_s)
            if len(ys_s) == 0 or len(xs_s) == 0:
                continue

            bx1_s, bx2_s = int(np.min(xs_s)), int(np.max(xs_s))
            by1_s, by2_s = int(np.min(ys_s)), int(np.max(ys_s))
            bw_s = bx2_s - bx1_s
            bh_s = by2_s - by1_s

            aspect = float(bw_s) / float(max(bh_s, 1))
            if not (0.28 <= aspect <= 3.5):
                continue

            # Shape prior validation: check rectangularity
            box_area_s = float(bw_s * bh_s)
            rectangularity = area_s / max(1.0, box_area_s)
            if rectangularity > 0.90 and area_s > 12000.0:
                # Mask is unnatural rectangular box; refine using elliptical morph closing
                inst_mask_s = ndi.binary_opening(inst_mask_s, structure=np.ones((7, 7), dtype=bool))

            # Scale mask back to full resolution with smooth boundary interpolation
            inst_mask_s_uint = (inst_mask_s.astype(np.uint8) * 255)
            inst_mask_full_img = Image.fromarray(inst_mask_s_uint).resize((orig_w, orig_h), Image.Resampling.BILINEAR)
            inst_mask_full = np.array(inst_mask_full_img) > 115
            inst_mask_full = ndi.binary_closing(inst_mask_full, structure=np.ones((5, 5), dtype=bool))
            inst_mask_full = ndi.binary_fill_holes(inst_mask_full)

            # Ensure solid fruit instance mask (interior black spots and lesions stay inside fruit)
            inst_mask_full = ndi.binary_fill_holes(inst_mask_full)

            ys_f, xs_f = np.where(inst_mask_full)
            if len(ys_f) == 0 or len(xs_f) == 0:
                continue

            bx1 = int(np.min(xs_f))
            by1 = int(np.min(ys_f))
            bx2 = int(np.max(xs_f))
            by2 = int(np.max(ys_f))

            pad_x = int((bx2 - bx1) * 0.04)
            pad_y = int((by2 - by1) * 0.04)
            x1_pad = max(0, bx1 - pad_x)
            y1_pad = max(0, by1 - pad_y)
            x2_pad = min(orig_w, bx2 + pad_x)
            y2_pad = min(orig_h, by2 + pad_y)
            bw = x2_pad - x1_pad
            bh = y2_pad - y1_pad

            # Generate individual masked crop:
            # Set background and adjacent mangoes outside instance mask to clean white
            sub_crop = img.crop((x1_pad, y1_pad, x2_pad, y2_pad))
            sub_mask = inst_mask_full[y1_pad:y2_pad, x1_pad:x2_pad]
            crop_np = np.array(sub_crop).copy()
            crop_np[~sub_mask] = [255, 255, 255]
            masked_crop_img = Image.fromarray(crop_np)

            # Contour & centroid
            contour_pts = self._extract_contour_points(inst_mask_full)
            cx = int(np.mean(xs_f))
            cy = int(np.mean(ys_f))
            solidity = float(np.sum(inst_mask_full)) / max(1.0, self._get_convex_hull_area(inst_mask_full))
            conf = min(99.0, max(82.0, 85.0 + solidity * 12.0))

            valid_detections.append({
                'box': [x1_pad, y1_pad, bw, bh],
                'bbox': [x1_pad, y1_pad, bw, bh],
                'crop': masked_crop_img,
                'area': float(np.sum(inst_mask_full)),
                'mask': inst_mask_full,
                'crop_mask': sub_mask,
                'contour': contour_pts,
                'centroid': (cx, cy),
                'solidity': round(solidity, 3),
                'aspect_ratio': round(float(bw) / float(max(bh, 1)), 2),
                'segmentation_confidence': round(conf, 1)
            })

        # Return empty detections if no valid instances parsed
        if not valid_detections:
            self.last_debug_data = {
                'peel_clean': peel_clean,
                'markers': markers,
                'segmented_instances': segmented_instances,
                'scale': scale
            }
            if return_debug:
                return img, [], self.generate_debug_images(img, [])
            return img, []

        # Sort left-to-right (then top-to-bottom) for natural fruit ordering
        valid_detections.sort(key=lambda d: (d['box'][1] // 100, d['box'][0]))
        for idx, d in enumerate(valid_detections, 1):
            d['index'] = idx

        # Cache debug data for visualization
        self.last_debug_data = {
            'peel_clean': peel_clean,
            'markers': markers,
            'segmented_instances': segmented_instances,
            'scale': scale
        }

        if return_debug:
            debug_images = self.generate_debug_images(img, valid_detections)
            return img, valid_detections, debug_images

        return img, valid_detections

    def generate_debug_images(self, orig_img: Image.Image, detections: list, lot_summary: dict = None) -> Dict[str, Image.Image]:
        """
        Generates the 10 Visual Debug stages:
        1. original image
        2. bunch bounding box & peel outline
        3. separation boundaries & EDT peaks
        4. individual mango instance masks (colored map)
        5. individual mango crops montage
        6. background & non-mango excluded region
        7. detected defect candidate pixels
        8. final validated defect mask
        9. defect percentage & metrics card
        10. final quality grade & decision breakdown
        """
        w, h = orig_img.size
        d_data = getattr(self, 'last_debug_data', {})
        peel_clean = d_data.get('peel_clean')
        seg_inst = d_data.get('segmented_instances')

        # 1. Original image
        debug_1 = orig_img.copy()

        # 2. Bunch Bounding Box & Peel Outline
        debug_2 = orig_img.copy()
        d2 = ImageDraw.Draw(debug_2)
        if detections:
            all_x1 = min(d['box'][0] for d in detections)
            all_y1 = min(d['box'][1] for d in detections)
            all_x2 = max(d['box'][0] + d['box'][2] for d in detections)
            all_y2 = max(d['box'][1] + d['box'][3] for d in detections)
            d2.rectangle([all_x1, all_y1, all_x2, all_y2], outline=(234, 179, 8), width=3)
            d2.rectangle([all_x1, max(0, all_y1 - 22), all_x1 + 130, all_y1], fill=(234, 179, 8))
            d2.text((all_x1 + 6, max(0, all_y1 - 20)), "BUNCH BOUNDS", fill=(15, 23, 42))

        for det in detections:
            bx, by, bw, bh = det['box']
            d2.rectangle([bx, by, bx + bw, by + bh], outline=(34, 197, 94), width=2)
        d2.text((12, 12), "STAGE 2: Bunch & Mango Bounding Boxes", fill=(255, 255, 255))

        # 3. Proposed Separation Boundaries & Distance Peaks
        debug_3 = orig_img.copy().convert("RGBA")
        overlay_3 = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d3 = ImageDraw.Draw(overlay_3)

        if seg_inst is not None:
            gx = ndi.sobel(seg_inst, axis=1)
            gy = ndi.sobel(seg_inst, axis=0)
            boundaries_s = (np.hypot(gx, gy) > 0) & (seg_inst > 0)
            bound_full = Image.fromarray(boundaries_s.astype(np.uint8) * 255).resize((w, h), Image.Resampling.NEAREST)
            b_ys, b_xs = np.where(np.array(bound_full) > 0)
            for bx, by in zip(b_xs, b_ys):
                d3.rectangle([bx-1, by-1, bx+1, by+1], fill=(239, 68, 68, 220))

        for det in detections:
            cx, cy = det.get('centroid', (0, 0))
            idx_num = det.get('sample_index', det.get('index', 1))
            d3.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=(59, 130, 246, 240), outline=(255, 255, 255, 255), width=2)
            d3.text((cx + 10, cy - 10), f"Peak #{idx_num}", fill=(255, 255, 255, 255))

        debug_3 = Image.alpha_composite(debug_3, overlay_3).convert("RGB")
        d3_draw = ImageDraw.Draw(debug_3)
        d3_draw.text((12, 12), "STAGE 3: Separation Crease Seams & Distance Peaks", fill=(255, 255, 255))

        # 4. Final Individual Masks
        palette = [
            (16, 185, 129),   # Emerald Green
            (245, 158, 11),   # Amber
            (59, 130, 246),   # Sky Blue
            (236, 72, 153),   # Pink
            (139, 92, 246),   # Violet
            (20, 184, 166),   # Teal
            (249, 115, 22),   # Orange
        ]
        debug_4_arr = np.zeros((h, w, 3), dtype=np.uint8)
        for idx, det in enumerate(detections):
            inst_m = det.get('mask')
            if inst_m is not None:
                color = palette[idx % len(palette)]
                debug_4_arr[inst_m] = color
        debug_4 = Image.fromarray(debug_4_arr)
        d4 = ImageDraw.Draw(debug_4)
        d4.text((12, 12), f"STAGE 4: Individual Mango Instance Masks ({len(detections)} Mangoes)", fill=(255, 255, 255))

        # 5. Final Mango #1, #2, #3... Crops Montage
        num_crops = len(detections)
        crop_size = 180
        montage_w = max(crop_size * num_crops + 20 * (num_crops + 1), 320)
        montage_h = crop_size + 60
        debug_5 = Image.new("RGB", (montage_w, montage_h), (241, 245, 249))
        d5 = ImageDraw.Draw(debug_5)
        d5.text((15, 10), "STAGE 5: Isolated Individual Mango Crops", fill=(15, 23, 42))
        if num_crops == 0:
            d5.text((20, 50), "No individual mangoes detected in image", fill=(100, 116, 139))

        cur_x = 20
        for det in detections:
            idx_num = det.get('sample_index', det.get('index', 1))
            c_area = int(det.get('area', 0))
            if 'crop' in det and det['crop']:
                c_img = det['crop'].copy().resize((crop_size, crop_size), Image.Resampling.BILINEAR)
            else:
                bx, by, bw, bh = det['box']
                c_img = orig_img.crop((bx, by, bx + bw, by + bh)).resize((crop_size, crop_size), Image.Resampling.BILINEAR)
            debug_5.paste(c_img, (cur_x, 35))
            d5.rectangle([cur_x, 35, cur_x + crop_size, 35 + crop_size], outline=(203, 213, 225), width=2)
            d5.text((cur_x + 6, 35 + crop_size + 4), f"Mango #{idx_num} ({c_area} px)", fill=(30, 41, 59))
            cur_x += crop_size + 20

        # 6. Background Excluded Region
        debug_6_arr = np.full((h, w, 3), (15, 23, 42), dtype=np.uint8)
        orig_arr = np.array(orig_img)
        combined_fruit_mask = np.zeros((h, w), dtype=bool)
        for det in detections:
            m = det.get('mask')
            if m is not None and m.shape == (h, w):
                combined_fruit_mask |= m
        debug_6_arr[combined_fruit_mask] = orig_arr[combined_fruit_mask]
        debug_6 = Image.fromarray(debug_6_arr)
        d6 = ImageDraw.Draw(debug_6)
        d6.text((12, 12), "STAGE 6: Valid Fruit Mask (Background Excluded in Slate)", fill=(255, 255, 255))

        # 7. Defect Candidate Pixels
        debug_7 = orig_img.copy().convert("RGBA")
        overlay_7 = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d7 = ImageDraw.Draw(overlay_7)
        for det in detections:
            bx, by, _, _ = det['box']
            for dbox in det.get('defect_regions', []):
                lx1, ly1, lw_b, lh_b = dbox
                d7.rectangle([bx + lx1, by + ly1, bx + lx1 + lw_b, by + ly1 + lh_b], outline=(239, 68, 68, 255), width=2)
                d7.rectangle([bx + lx1, by + ly1, bx + lx1 + lw_b, by + ly1 + lh_b], fill=(239, 68, 68, 90))
        debug_7 = Image.alpha_composite(debug_7, overlay_7).convert("RGB")
        d7_draw = ImageDraw.Draw(debug_7)
        d7_draw.text((12, 12), "STAGE 7: Detected Defect Candidate Lesions", fill=(255, 255, 255))

        # 8. Final Validated Defect Mask
        debug_8_arr = np.full((h, w, 3), (15, 23, 42), dtype=np.uint8)
        debug_8_arr[combined_fruit_mask] = (40, 50, 70)
        for det in detections:
            bx, by, _, _ = det['box']
            for dbox in det.get('defect_regions', []):
                lx1, ly1, lw_b, lh_b = dbox
                y1 = max(0, by + ly1)
                y2 = min(h, by + ly1 + lh_b)
                x1 = max(0, bx + lx1)
                x2 = min(w, bx + lx1 + lw_b)
                debug_8_arr[y1:y2, x1:x2] = (239, 68, 68)
        debug_8 = Image.fromarray(debug_8_arr)
        d8 = ImageDraw.Draw(debug_8)
        d8.text((12, 12), "STAGE 8: Final Validated Defect Mask (Inside Safe Interior Only)", fill=(255, 255, 255))

        # 9. Defect Percentage & Metrics Overlay
        debug_9 = orig_img.copy()
        d9 = ImageDraw.Draw(debug_9)
        for det in detections:
            bx, by, bw, bh = det['box']
            idx_num = det.get('sample_index', det.get('index', 1))
            pct = det.get('visible_defect_pct', det.get('affected_area_pct', 0.0))
            hlth = det.get('health_status', 'Healthy')
            col = (34, 197, 94) if hlth == 'Healthy' else (239, 68, 68)
            d9.rectangle([bx, by, bx + bw, by + bh], outline=col, width=2)
            d9.rectangle([bx, max(0, by - 24), bx + 160, by], fill=col)
            d9.text((bx + 4, max(0, by - 20)), f"#{idx_num} Defect: {pct:.1f}%", fill=(255, 255, 255))
        d9.text((12, 12), "STAGE 9: Defect Percentage Overlay (Inside Valid Peel Only)", fill=(255, 255, 255))

        # 10. Final Quality Grade Card
        debug_10 = Image.new("RGB", (max(w, 480), max(h, 280)), (19, 28, 46))
        d10 = ImageDraw.Draw(debug_10)
        lot_grade = (lot_summary or {}).get('visual_grade', 'Grade A')
        lot_defect = (lot_summary or {}).get('lot_defect_pct', 0.0)
        sample_c = len(detections)
        d10.text((20, 20), "STAGE 10: Final Lot Optical Quality Assessment", fill=(248, 250, 252))
        d10.rectangle([20, 60, 220, 160], fill=(22, 163, 74) if 'Grade A' in lot_grade else (234, 179, 8) if 'Grade B' in lot_grade else (220, 38, 38))
        d10.text((36, 75), "FINAL GRADE", fill=(255, 255, 255))
        d10.text((36, 100), lot_grade, fill=(255, 255, 255))
        d10.text((250, 70), f"Sampled Mango Instances: {sample_c}", fill=(203, 213, 225))
        d10.text((250, 95), f"Average Defect Rate: {lot_defect:.1f}%", fill=(203, 213, 225))
        d10.text((250, 120), "Evaluation: Strictly Computed from Valid Fruit Surface", fill=(148, 163, 184))
        d10.text((20, 180), "Disclaimer: Optical AI baseline estimate for procurement gate triage.", fill=(100, 116, 139))

        return {
            "debug_1_original": debug_1,
            "debug_2_peel_mask": debug_2,
            "debug_2_bunch_bbox": debug_2,
            "debug_3_separation_boundaries": debug_3,
            "debug_4_instance_masks": debug_4,
            "debug_5_crops_montage": debug_5,
            "debug_6_background_excluded": debug_6,
            "debug_7_defect_candidates": debug_7,
            "debug_8_final_defect_mask": debug_8,
            "debug_9_defect_percentage": debug_9,
            "debug_10_final_grade": debug_10
        }

    def annotate_image(self, original_img: Image.Image, detections: list, save_path: str = None) -> Image.Image:
        """
        Draws comprehensive visual inspection annotations:
        - Instance contours drawn on the original image
        - Mango bounding boxes and decoupled status banners
        - Localized defect lesion highlights
        """
        annotated = original_img.copy().convert("RGBA")
        overlay = Image.new("RGBA", original_img.size, (0, 0, 0, 0))
        draw_ov = ImageDraw.Draw(overlay)
        draw = ImageDraw.Draw(annotated)

        status_colors = {
            "Healthy": "#10B981",
            "Defective": "#EF4444",
            "Uncertain": "#F59E0B"
        }

        defect_colors = {
            "Anthracnose": "#DC2626",
            "Bacterial Canker": "#991B1B",
            "Scab": "#D97706",
            "Stem End Rot": "#7C3AED",
            "Surface Blemish": "#EA580C",
            "Other": "#EC4899"
        }

        for det in detections:
            x, y, w, h = det['box']
            idx = det.get('sample_index', det.get('index', 1))
            health_status = det.get('health_status', 'Healthy' if det.get('predicted_class') == 'Healthy' else 'Defective')
            defect_type = det.get('defect_type', det.get('predicted_class', 'None'))
            ripeness = det.get('ripeness', 'Uncertain')
            quality_grade = det.get('quality_grade', 'Grade A' if health_status == 'Healthy' else 'Reject')
            conf = det.get('confidence', det.get('segmentation_confidence', 0.0))
            affected_pct = det.get('visible_defect_pct', det.get('affected_area_pct', 0.0))

            if health_status == "Healthy":
                color = status_colors["Healthy"]
                display_status = "Healthy"
            elif health_status == "Defective":
                color = defect_colors.get(defect_type, status_colors["Defective"])
                display_status = f"Defective ({defect_type})"
            else:
                color = status_colors["Uncertain"]
                display_status = "Uncertain"

            # Draw outer contour if available
            contour_pts = det.get('contour', [])
            if len(contour_pts) > 2:
                for ci in range(len(contour_pts)):
                    p1 = contour_pts[ci]
                    p2 = contour_pts[(ci + 1) % len(contour_pts)]
                    draw_ov.line([p1, p2], fill=color, width=3)

            # Draw outer rectangle
            line_w = max(2, int(min(original_img.size) * 0.004))
            draw.rectangle([x, y, x + w, y + h], outline=color, width=line_w)

            # Draw defect lesion highlights
            defect_boxes = det.get('defect_regions', [])
            if defect_boxes:
                for db in defect_boxes:
                    lx1 = x + db[0]
                    ly1 = y + db[1]
                    lx2 = min(x + w, lx1 + db[2])
                    ly2 = min(y + h, ly1 + db[3])
                    draw.rectangle([lx1, ly1, lx2, ly2], outline="#EF4444", width=2)
                    draw_ov.rectangle([lx1, ly1, lx2, ly2], fill=(239, 68, 68, 80))

            # Decoupled label banner
            if health_status == "Healthy":
                text = f"#{idx} [Healthy] {conf:.1f}% | {ripeness} | {quality_grade}"
            else:
                text = f"#{idx} [{display_status}] {conf:.1f}% | {ripeness} | {affected_pct}% aff."

            banner_h = 24
            banner_w = len(text) * 8 + 14
            banner_y1 = max(0, y - banner_h)
            banner_y2 = y
            draw.rectangle([x, banner_y1, min(original_img.width, x + banner_w), banner_y2], fill=color)
            draw.text((x + 6, max(2, banner_y1 + 4)), text, fill="#FFFFFF")

        annotated = Image.alpha_composite(annotated, overlay).convert("RGB")

        if save_path:
            os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
            annotated.save(save_path, quality=92)

        return annotated
