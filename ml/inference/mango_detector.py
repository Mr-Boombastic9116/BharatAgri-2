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

        # HSV representation for illumination and saturation separation
        c_max = np.maximum(np.maximum(r, g), b)
        c_min = np.minimum(np.minimum(r, g), b)
        c_rng = c_max - c_min
        sat = np.where(c_max > 1.0, c_rng / (c_max + 1e-6), 0.0)

        # 1. White Background Estimation (Controlled white sheet/table prior)
        # Operators photograph mangoes on a clean white background under white overhead lighting.
        # Estimate reference white illumination from image border margins
        bg_margin_h = max(2, int(sh * 0.08))
        bg_margin_w = max(2, int(sw * 0.08))
        border_mask = np.zeros((sh, sw), dtype=bool)
        border_mask[:bg_margin_h, :] = True
        border_mask[-bg_margin_h:, :] = True
        border_mask[:, :bg_margin_w] = True
        border_mask[:, -bg_margin_w:] = True

        border_L = l_est[border_mask]
        border_sat = sat[border_mask]
        white_border_l = border_L[(border_sat <= 0.20) & (border_L >= 160.0)]
        bg_white_ref = float(np.percentile(white_border_l, 80)) if len(white_border_l) > 20 else 240.0
        bg_white_ref = max(185.0, min(255.0, bg_white_ref))
        l_norm = l_est / bg_white_ref

        is_pure_white = (l_est >= 200.0) & (sat <= 0.18) & (chroma <= 18.0)
        is_near_white = (l_est >= 175.0) & (sat <= 0.14) & (chroma <= 16.0) & (c_rng <= 35.0)
        white_bg = is_pure_white | is_near_white

        # 2. Shadow / Neutral Illumination Candidate Suppression
        # Includes both deep neutral shadows and whitish-grey penumbra cast shadows with color bounce
        is_neutral_shadow = (l_est >= 38.0) & (l_est <= 218.0) & (sat <= 0.15) & (chroma <= 16.0) & (c_rng <= 28.0)
        is_whitish_grey_shadow = (l_est >= 130.0) & (l_est <= 235.0) & (sat <= 0.22) & (chroma <= 22.0) & (c_rng <= 52.0)
        shadow_mask = is_neutral_shadow | is_whitish_grey_shadow
        is_dark_bg = (l_est <= 38.0) & (sat <= 0.20) & (chroma <= 12.0) & border_mask
        bg_and_shadow = white_bg | shadow_mask

        # 3. Foreground Mango Peel Segmentation:
        # Accounts for ripe yellow/orange peel, green unripe peel, breaking peel, and dark/black peel
        # Strongly rejects white background, neutral shadows, and whitish-grey cast shadows
        is_yellow = (r > b * 1.14) & (g > b * 0.95) & (b_est > 130.0) & (sat >= 0.19) & (chroma >= 14.0) & (l_est >= 35.0) & (l_est < 250.0) & (~bg_and_shadow)
        is_green = (g > r * 0.88) & (g > b * 1.02) & (chroma >= 8.0) & (sat >= 0.10) & (l_est >= 28.0) & (l_est < 245.0) & (~white_bg) & (~is_neutral_shadow)
        is_breaking = (r > b * 1.06) & (g > b * 0.96) & (chroma >= 13.0) & (sat >= 0.16) & (l_est >= 35.0) & (l_est < 250.0) & (~bg_and_shadow)
        is_dark_fruit = (~white_bg) & (~shadow_mask) & (~border_mask) & (l_est < 40.0)
        peel_raw = (is_yellow | is_green | is_breaking | is_dark_fruit) & (~is_dark_bg) & (~border_mask)

        # Morphology: small opening to remove whisker bridges without merging gaps,
        # followed by closing and hole filling to retain interior defects
        peel_opened = ndi.binary_opening(peel_raw, structure=np.ones((3, 3), dtype=bool))
        peel_closed = ndi.binary_closing(peel_opened, structure=np.ones((3, 3), dtype=bool))
        peel_filled = ndi.binary_fill_holes(peel_closed)

        # Boundary Refinement: Strip outer perimeter shadow fringes adjacent to white background
        # Inspect boundary section pixels extending towards surrounding white sheet:
        eroded_peel_5 = ndi.binary_erosion(peel_filled, structure=np.ones((5, 5), dtype=bool))
        eroded_peel_9 = ndi.binary_erosion(peel_filled, structure=np.ones((9, 9), dtype=bool))
        outer_perim_narrow = peel_filled & (~eroded_peel_5)
        outer_perim_wide = peel_filled & (~eroded_peel_9)

        # External cast shadows on white sheet exhibit low chroma, neutral saturation, or grey tone
        is_outer_cast_shadow = outer_perim_wide & (
            ((sat < 0.22) & (chroma < 20.0)) |
            ((l_est > 140.0) & (sat < 0.26)) |
            ((l_est > 190.0) & (chroma < 25.0)) |
            ((c_rng < 35.0) & (l_est > 100.0) & (sat < 0.28))
        ) & (~is_green) & (~is_dark_fruit)

        # Also strip ambiguous dark border outline pixels touching the white background
        is_dark_outline = outer_perim_narrow & (l_est < 45.0) & (sat < 0.25) & (chroma < 18.0)

        is_boundary_shadow = is_outer_cast_shadow | is_dark_outline
        peel_refined = peel_filled & (~is_boundary_shadow)
        peel_clean = ndi.binary_fill_holes(peel_refined)

        # Track excluded shadow ledger
        raw_fg_pixels = int(np.sum(peel_filled))
        refined_mask_pixels = int(np.sum(peel_clean))
        excluded_shadow_mask = peel_filled & (~peel_clean)
        excluded_shadow_pixels = int(np.sum(excluded_shadow_mask))
        shadow_exclusion_ratio = round(float(excluded_shadow_pixels) / float(max(1, raw_fg_pixels)), 4)

        # Filter out tiny disconnected noise specks, border clutter, and rectangular dark crates from peel_clean
        lbl_raw, n_raw = ndi.label(peel_clean)
        if n_raw >= 1:
            raw_sizes = ndi.sum(peel_clean, lbl_raw, range(1, n_raw + 1))
            dom_raw = float(np.max(raw_sizes)) if len(raw_sizes) > 0 else 0.0
            min_keep = max(350.0, dom_raw * 0.05)
            filtered_peel = np.zeros_like(peel_clean)
            for idx_r, s in enumerate(raw_sizes, 1):
                if s >= min_keep:
                    m_comp = (lbl_raw == idx_r)
                    ys_c, xs_c = np.where(m_comp)
                    bw_c = np.max(xs_c) - np.min(xs_c) + 1
                    bh_c = np.max(ys_c) - np.min(ys_c) + 1
                    rect_c = float(s) / float(max(1, bw_c * bh_c))
                    mean_l_c = float(np.mean(l_est[m_comp]))

                    # If dark object (L < 42) and either touches border or is rectangular (> 0.86), it is background clutter
                    is_border_clutter = (mean_l_c < 42.0) and (np.sum(m_comp & border_mask) > int(s * 0.08))
                    is_dark_crate = (mean_l_c < 42.0) and (rect_c > 0.86)

                    if not (is_border_clutter or is_dark_crate):
                        filtered_peel[m_comp] = True
            peel_clean = filtered_peel

        total_peel_pixels = float(np.sum(peel_clean))
        if total_peel_pixels < 250:
            self.last_debug_data = {
                'peel_clean': peel_clean,
                'white_bg_mask': white_bg,
                'shadow_mask': shadow_mask,
                'raw_foreground': peel_filled,
                'refined_mask': peel_clean,
                'excluded_shadow_mask': excluded_shadow_mask,
                'excluded_shadow_pixels': excluded_shadow_pixels,
                'raw_foreground_pixels': raw_fg_pixels,
                'refined_mask_pixels': refined_mask_pixels,
                'shadow_exclusion_ratio': shadow_exclusion_ratio,
                'markers': np.zeros_like(peel_clean, dtype=np.int32),
                'segmented_instances': np.zeros_like(peel_clean, dtype=np.int32),
                'scale': scale
            }
            if return_debug:
                return img, [], self.generate_debug_images(img, [])
            return img, []

        # 4. Connected-Component Analysis & Conditional Watershed
        # Rule 7: If objects are already separated connected components, DO NOT watershed between them!
        lbl_cc, n_cc = ndi.label(peel_clean)
        dist_full = ndi.distance_transform_edt(peel_clean)

        markers = np.zeros(peel_clean.shape, dtype=np.int32)
        marker_count = 0
        total_candidate_markers = 0
        total_accepted_markers = 0
        total_rejected_markers = 0
        rejected_reasons = []

        # Signal B: Boundary edge gradient creases to detect contact seams between touching mangoes
        eroded_peel = ndi.binary_erosion(peel_clean, structure=np.ones((5, 5), bool))
        outer_perim = peel_clean & (~eroded_peel)
        gx = ndi.sobel(l_est, axis=1)
        gy = ndi.sobel(l_est, axis=0)
        grad = np.hypot(gx, gy)
        peel_grads = grad[peel_clean]
        p85 = np.percentile(peel_grads, 85) if len(peel_grads) > 0 else 35.0
        edge_thresh = max(28.0, float(p85))
        raw_edges = (grad > edge_thresh) & peel_clean

        lbl_e, n_e = ndi.label(raw_edges)
        clean_creases = np.zeros_like(raw_edges, dtype=bool)
        for idx_e in range(1, n_e + 1):
            m_e = (lbl_e == idx_e)
            if np.sum(m_e) >= 20 and np.sum(m_e & outer_perim) >= 5:
                clean_creases[m_e] = True

        crease_barrier = ndi.binary_dilation(clean_creases, structure=np.ones((3, 3), dtype=bool))
        separated_peel = peel_clean & (~crease_barrier)
        separated_peel = ndi.binary_opening(separated_peel, structure=np.ones((5, 5), dtype=bool))

        lbl_cores, n_cores = ndi.label(separated_peel)
        sizes = ndi.sum(separated_peel, lbl_cores, range(1, n_cores + 1)) if n_cores > 0 else []

        # If boundary creases separated touching mangoes into distinct cores:
        if n_cores > 1 and len(sizes) > 0:
            dom_size = float(np.max(sizes))
            min_core_thresh = max(350.0, dom_size * 0.15)
            for idx_c, s in enumerate(sizes, 1):
                if s >= min_core_thresh:
                    marker_count += 1
                    markers[lbl_cores == idx_c] = marker_count
                    total_candidate_markers += 1
                    total_accepted_markers += 1

        # Signal A & C: Distance transform peaks if boundary creases were insufficient (< 2 markers)
        if marker_count < 2:
            dist = ndi.distance_transform_edt(peel_clean)
            max_d = float(np.max(dist))
            fp = max(9, int(max_d * 0.22)) | 1
            local_max = (dist == ndi.maximum_filter(dist, footprint=np.ones((fp, fp), dtype=bool))) & (dist > max(10.0, max_d * 0.25)) & peel_clean
            lbl_p, n_p = ndi.label(local_max)
            if n_p >= 2:
                peak_points = []
                for p_idx in range(1, n_p + 1):
                    ys, xs = np.where(lbl_p == p_idx)
                    val = float(np.mean(dist[ys, xs]))
                    peak_points.append((float(np.mean(xs)), float(np.mean(ys)), val, p_idx))
                peak_points.sort(key=lambda p: p[2], reverse=True)
                min_peak_dist = max(24.0, max_d * 0.35)
                kept_markers = np.zeros(peel_clean.shape, dtype=np.int32)
                kept_count = 0
                kept_centers = []
                for cx, cy, val, p_idx in peak_points:
                    total_candidate_markers += 1
                    if not any(np.hypot(cx - kx, cy - ky) < min_peak_dist for kx, ky in kept_centers):
                        is_valid_peak = True
                        if kept_centers:
                            nearest_k = min(kept_centers, key=lambda k: np.hypot(cx - k[0], cy - k[1]))
                            dist_to_k = np.hypot(cx - nearest_k[0], cy - nearest_k[1])
                            num_s = int(dist_to_k)
                            if num_s > 0:
                                xs_line = np.linspace(cx, nearest_k[0], num_s).astype(int)
                                ys_line = np.linspace(cy, nearest_k[1], num_s).astype(int)
                                line_vals = dist[ys_line, xs_line]
                                min_line = np.min(line_vals)
                                dip = (max(val, dist[int(nearest_k[1]), int(nearest_k[0])]) - min_line) / max_d
                                if dip < 0.05:
                                    is_valid_peak = False
                                    total_rejected_markers += 1
                                    rejected_reasons.append(f"Insufficient dip {dip:.3f} < 0.05")
                        if is_valid_peak:
                            kept_count += 1
                            total_accepted_markers += 1
                            kept_centers.append((cx, cy))
                            kept_markers[lbl_p == p_idx] = kept_count
                    else:
                        total_rejected_markers += 1
                        rejected_reasons.append(f"Peak too close (< {min_peak_dist:.1f})")
                if kept_count >= 2:
                    markers = kept_markers
                    marker_count = kept_count
                else:
                    lbl_fallback, _ = ndi.label(peel_clean)
                    markers = lbl_fallback.astype(np.int32)
                    marker_count = 1
                    total_accepted_markers = 1
            else:
                lbl_fallback, _ = ndi.label(peel_clean)
                markers = lbl_fallback.astype(np.int32)
                marker_count = 1
                total_accepted_markers = 1

        # Marker-controlled distance partition (Geodesic Voronoi / Watershed)
        if marker_count >= 2:
            _, indices = ndi.distance_transform_edt(markers == 0, return_indices=True)
            segmented_instances = markers[indices[0], indices[1]]
            segmented_instances[~peel_clean] = 0
        else:
            lbl_fallback, _ = ndi.label(peel_clean)
            segmented_instances = lbl_fallback.astype(np.int32)

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
        dist_map = ndi.distance_transform_edt(peel_clean)
        while changed and len(labels) > 1:
            changed = False

            # Check 0: False Middle Fragment / Bridge Sliver between two larger instances
            # (Solves over-segmentation where 2 mangoes ~1 cm apart produce 3 mangoes)
            if len(labels) >= 3:
                for l_mid in labels:
                    m_mid = (segmented_instances == l_mid)
                    a_mid = float(np.sum(m_mid))
                    if a_mid == 0:
                        continue
                    m_mid_d = ndi.binary_dilation(m_mid, structure=np.ones((5, 5), dtype=bool))
                    neighbor_labels = [l_other for l_other in labels if l_other != l_mid and np.sum(m_mid_d & (segmented_instances == l_other)) > 0]
                    if len(neighbor_labels) >= 2:
                        for idx_a in range(len(neighbor_labels)):
                            for idx_b in range(idx_a + 1, len(neighbor_labels)):
                                la, lb = neighbor_labels[idx_a], neighbor_labels[idx_b]
                                ma = (segmented_instances == la)
                                mb = (segmented_instances == lb)
                                aa, ab = float(np.sum(ma)), float(np.sum(mb))
                                if aa == 0 or ab == 0:
                                    continue
                                min_ab = min(aa, ab)
                                d_mid = float(np.max(dist_map[m_mid]))
                                d_a = float(np.max(dist_map[ma]))
                                d_b = float(np.max(dist_map[mb]))
                                min_d_ab = min(d_a, d_b)
                                mean_d_mid = float(np.mean(dist_map[m_mid]))
                                mean_d_a = float(np.mean(dist_map[ma]))
                                mean_d_b = float(np.mean(dist_map[mb]))
                                min_mean_ab = min(mean_d_a, mean_d_b)

                                # Section 10-12: Reject artificial bridge slivers and white-gap artifacts
                                is_sliver = (
                                    (a_mid < min_ab * 0.88 and (d_mid < min_d_ab * 0.72 or mean_d_mid < min_mean_ab * 0.65))
                                    or (d_mid < min_d_ab * 0.65)
                                    or (a_mid < min_ab * 0.40)
                                )

                                mid_sat = float(np.mean(sat[m_mid])) if np.sum(m_mid) > 0 else 0.0
                                mid_chroma = float(np.mean(chroma[m_mid])) if np.sum(m_mid) > 0 else 0.0
                                mid_l = float(np.mean(l_est[m_mid])) if np.sum(m_mid) > 0 else 0.0
                                is_gap_artifact = (mid_l > 195.0) or ((mid_l > 140.0) and ((mid_sat < 0.16) or (mid_chroma < 14.0)))

                                if is_sliver or is_gap_artifact:
                                    if is_gap_artifact:
                                        # Exclude background gap artifact completely
                                        segmented_instances[m_mid] = 0
                                    else:
                                        # Merge bridge neck into adjacent real mangoes
                                        _, nn_idx = ndi.distance_transform_edt(~(ma | mb), return_indices=True)
                                        segmented_instances[m_mid] = segmented_instances[nn_idx[0][m_mid], nn_idx[1][m_mid]]
                                    labels = [l for l in np.unique(segmented_instances) if l > 0]
                                    changed = True
                                    break
                            if changed:
                                break
                    if changed:
                        break
                if changed:
                    continue

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

                # 1. Asymmetry / tiny fragment check (< 8% of pair)
                if (min(a1, a2) / max(a1, a2)) < 0.08:
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

                if containment > 0.88:
                    segmented_instances[segmented_instances == l2] = l1
                    labels = [l for l in np.unique(segmented_instances) if l > 0]
                    changed = True
                    break

                # 3. Distance between proposed centers and seam core cut check
                cy1, cx1 = np.mean(y1_1), np.mean(x1_1)
                cy2, cx2 = np.mean(y1_2), np.mean(x1_2)
                center_dist = float(np.hypot(cx1 - cx2, cy1 - cy2))
                m_comb = m1 | m2
                dist_comb = ndi.distance_transform_edt(m_comb)
                max_d_comb = float(np.max(dist_comb))
                seam = ndi.binary_dilation(m1, structure=np.ones((3, 3), bool)) & ndi.binary_dilation(m2, structure=np.ones((3, 3), bool)) & m_comb
                seam_max = float(np.max(dist_comb[seam])) if np.sum(seam) > 0 else 0.0

                # Only merge if centers are nearly coincident with zero saddle drop
                if center_dist < max(18.0, max_d_comb * 0.25) and seam_max >= max_d_comb * 0.98:
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
        # Adaptively scale minimum fruit area so multi-fruit sack samples / dense trays (10-20 mangoes) are not discarded
        min_fruit_area_scaled = max(300.0, min(float(sw * sh) * 0.005, total_peel_pixels * 0.015))
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

            # Reject border clutter (crates, corner shadows, conveyor edges)
            if np.sum(inst_mask_s & border_mask) > int(area_s * 0.12):
                continue

            aspect = float(bw_s) / float(max(bh_s, 1))
            if not (0.28 <= aspect <= 3.5):
                continue

            # Shape prior validation: enforce organic curved mango boundary
            box_area_s = float(bw_s * bh_s)
            rectangularity = area_s / max(1.0, box_area_s)
            if rectangularity > 0.86:
                mean_inst_l = float(np.mean(l_est[inst_mask_s])) if np.sum(inst_mask_s) > 0 else 0.0
                if mean_inst_l < 42.0:
                    continue
                # Mask has unnatural rectangular cut edges; round off with morphological opening
                inst_mask_s = ndi.binary_opening(inst_mask_s, structure=np.ones((5, 5), dtype=bool))

            inst_mask_s = ndi.binary_closing(inst_mask_s, structure=np.ones((5, 5), dtype=bool))
            inst_mask_s = ndi.binary_fill_holes(inst_mask_s)

            # Scale mask back to full resolution with smooth boundary interpolation
            inst_mask_s_uint = (inst_mask_s.astype(np.uint8) * 255)
            inst_mask_full_img = Image.fromarray(inst_mask_s_uint).resize((orig_w, orig_h), Image.Resampling.BILINEAR)
            inst_mask_full = np.array(inst_mask_full_img) > 115
            inst_mask_full = ndi.binary_closing(inst_mask_full, structure=np.ones((5, 5), dtype=bool))
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
            solidity = min(1.0, float(np.sum(inst_mask_full)) / max(1.0, self._get_convex_hull_area(inst_mask_full)))
            conf = min(99.0, max(82.0, 85.0 + solidity * 12.0))

            valid_detections.append({
                'box': [x1_pad, y1_pad, bw, bh],
                'bbox': [x1_pad, y1_pad, bw, bh],
                'width': bw,
                'height': bh,
                'crop': masked_crop_img,
                'area': float(np.sum(inst_mask_full)),
                'mask': inst_mask_full,
                'crop_mask': sub_mask,
                'contour': contour_pts,
                'centroid': (cx, cy),
                'solidity': round(solidity, 3),
                'aspect_ratio': round(float(bw) / float(max(bh, 1)), 2),
                'confidence': round(conf, 1),
                'segmentation_confidence': round(conf, 1),
                'cc_before_watershed': n_cc,
                'candidate_markers': total_candidate_markers,
                'accepted_markers': total_accepted_markers,
                'rejected_markers': total_rejected_markers,
                'rejected_reason': (rejected_reasons[0] if rejected_reasons else "None"),
                'excluded_shadow_pixels': excluded_shadow_pixels,
                'raw_foreground_pixels': raw_fg_pixels,
                'refined_mask_pixels': refined_mask_pixels,
                'shadow_exclusion_ratio': shadow_exclusion_ratio
            })

        # Return empty detections if no valid instances parsed
        if not valid_detections:
            self.last_debug_data = {
                'peel_clean': peel_clean,
                'white_bg_mask': white_bg,
                'shadow_mask': shadow_mask,
                'raw_foreground': peel_filled,
                'refined_mask': peel_clean,
                'excluded_shadow_mask': excluded_shadow_mask,
                'excluded_shadow_pixels': excluded_shadow_pixels,
                'raw_foreground_pixels': raw_fg_pixels,
                'refined_mask_pixels': refined_mask_pixels,
                'shadow_exclusion_ratio': shadow_exclusion_ratio,
                'connected_components': lbl_cc,
                'n_connected_components': n_cc,
                'dist_map': dist_full,
                'candidate_markers_count': total_candidate_markers,
                'accepted_markers_count': total_accepted_markers,
                'rejected_markers_count': total_rejected_markers,
                'rejected_reasons': rejected_reasons,
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
            'white_bg_mask': white_bg,
            'shadow_mask': shadow_mask,
            'raw_foreground': peel_filled,
            'refined_mask': peel_clean,
            'excluded_shadow_mask': excluded_shadow_mask,
            'excluded_shadow_pixels': excluded_shadow_pixels,
            'raw_foreground_pixels': raw_fg_pixels,
            'refined_mask_pixels': refined_mask_pixels,
            'shadow_exclusion_ratio': shadow_exclusion_ratio,
            'connected_components': lbl_cc,
            'n_connected_components': n_cc,
            'dist_map': dist_full,
            'candidate_markers_count': total_candidate_markers,
            'accepted_markers_count': total_accepted_markers,
            'rejected_markers_count': total_rejected_markers,
            'rejected_reasons': rejected_reasons,
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

        # DEVELOPER INSPECTION STAGES (SHADOW CORRECTION PIPELINE)
        # Stage A: Estimated White Sheet Background
        white_bg_m = d_data.get('white_bg_mask')
        if white_bg_m is not None:
            wbg_arr = np.full((h, w, 3), (15, 23, 42), dtype=np.uint8)
            wbg_full = Image.fromarray(white_bg_m.astype(np.uint8) * 255).resize((w, h), Image.Resampling.NEAREST)
            wbg_m_full = np.array(wbg_full) > 0
            wbg_arr[wbg_m_full] = (220, 235, 252)
            debug_wbg = Image.fromarray(wbg_arr)
        else:
            debug_wbg = orig_img.copy()
        d_wbg = ImageDraw.Draw(debug_wbg)
        d_wbg.text((12, 12), "DEV STAGE: Estimated White Sheet Background", fill=(255, 255, 255))

        # Stage B: Shadow Mask (Neutral & Whitish-Grey Penumbra)
        sh_m = d_data.get('shadow_mask')
        if sh_m is not None:
            sh_arr = np.full((h, w, 3), (15, 23, 42), dtype=np.uint8)
            sh_full = Image.fromarray(sh_m.astype(np.uint8) * 255).resize((w, h), Image.Resampling.NEAREST)
            sh_m_full = np.array(sh_full) > 0
            sh_arr[sh_m_full] = (168, 85, 247)
            debug_sh = Image.fromarray(sh_arr)
        else:
            debug_sh = orig_img.copy()
        d_sh = ImageDraw.Draw(debug_sh)
        d_sh.text((12, 12), "DEV STAGE: Detected Cast Shadows (Neutral & Whitish-Grey)", fill=(255, 255, 255))

        # Stage C: Raw Foreground Candidate Mask
        raw_fg = d_data.get('raw_foreground')
        if raw_fg is not None:
            rfg_arr = np.full((h, w, 3), (15, 23, 42), dtype=np.uint8)
            rfg_full = Image.fromarray(raw_fg.astype(np.uint8) * 255).resize((w, h), Image.Resampling.NEAREST)
            rfg_m_full = np.array(rfg_full) > 0
            rfg_arr[rfg_m_full] = (245, 158, 11)
            debug_rfg = Image.fromarray(rfg_arr)
        else:
            debug_rfg = orig_img.copy()
        d_rfg = ImageDraw.Draw(debug_rfg)
        d_rfg.text((12, 12), "DEV STAGE: Raw Foreground Candidate Mask", fill=(255, 255, 255))

        # Stage D: Refined Fruit Mask (Shadow Excluded)
        ref_m = d_data.get('refined_mask')
        if ref_m is not None:
            ref_arr = np.full((h, w, 3), (15, 23, 42), dtype=np.uint8)
            ref_full = Image.fromarray(ref_m.astype(np.uint8) * 255).resize((w, h), Image.Resampling.NEAREST)
            ref_m_full = np.array(ref_full) > 0
            ref_arr[ref_m_full] = (16, 185, 129)
            debug_ref = Image.fromarray(ref_arr)
        else:
            debug_ref = orig_img.copy()
        d_ref = ImageDraw.Draw(debug_ref)
        d_ref.text((12, 12), "DEV STAGE: Refined Mango Mask (Shadow-Excluded)", fill=(255, 255, 255))

        # Stage E: Excluded Shadow Pixels Overlay
        debug_exsh = orig_img.copy().convert("RGBA")
        exsh_ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        exsh_m = d_data.get('excluded_shadow_mask')
        if exsh_m is not None:
            exsh_full = Image.fromarray(exsh_m.astype(np.uint8) * 255).resize((w, h), Image.Resampling.NEAREST)
            ex_ys, ex_xs = np.where(np.array(exsh_full) > 0)
            ex_d = ImageDraw.Draw(exsh_ov)
            for ex, ey in zip(ex_xs, ex_ys):
                ex_d.point((ex, ey), fill=(236, 72, 153, 220))
        debug_exsh = Image.alpha_composite(debug_exsh, exsh_ov).convert("RGB")
        d_exsh = ImageDraw.Draw(debug_exsh)
        d_exsh.text((12, 12), f"DEV STAGE: Excluded Shadow Pixels ({d_data.get('excluded_shadow_pixels', 0)} px stripped)", fill=(255, 255, 255))

        # Stage F: Candidate White / Pale Patches (Section 6.6.E)
        debug_cwp = orig_img.copy().convert("RGBA")
        cwp_ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d_cwp = ImageDraw.Draw(cwp_ov)
        for det in detections:
            bx, by, bw, bh = det['box']
            d_cwp.rectangle([bx, by, bx + bw, by + bh], outline=(6, 182, 212, 180), width=1)
            for box in det.get('defect_boxes', []):
                dbx, dby, dbw, dbh = box
                d_cwp.rectangle([bx + dbx, by + dby, bx + dbx + dbw, by + dby + dbh], outline=(255, 255, 255, 240), fill=(6, 182, 212, 80), width=2)
        debug_cwp = Image.alpha_composite(debug_cwp, cwp_ov).convert("RGB")
        d_cwp_draw = ImageDraw.Draw(debug_cwp)
        d_cwp_draw.text((12, 12), "DEV STAGE: Candidate White/Pale Disease Patches (Local Analysis)", fill=(255, 255, 255))

        # Stage G: Candidate Grey-Shadow Regions (Section 6.6.E)
        debug_cgs = orig_img.copy().convert("RGBA")
        cgs_ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d_cgs = ImageDraw.Draw(cgs_ov)
        if exsh_m is not None:
            ex_ys, ex_xs = np.where(np.array(exsh_full) > 0)
            for ex, ey in zip(ex_xs, ex_ys):
                d_cgs.point((ex, ey), fill=(100, 116, 139, 180))
        for det in detections:
            bx, by, bw, bh = det['box']
            d_cgs.rectangle([bx, by, bx + bw, by + bh], outline=(148, 163, 184, 160), width=1)
        debug_cgs = Image.alpha_composite(debug_cgs, cgs_ov).convert("RGB")
        d_cgs_draw = ImageDraw.Draw(debug_cgs)
        d_cgs_draw.text((12, 12), "DEV STAGE: Candidate Grey Shadows on Background & Skin", fill=(255, 255, 255))

        # Stage H: Local Context Windows (Section 6.6.E)
        debug_lcw = orig_img.copy().convert("RGBA")
        lcw_ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d_lcw = ImageDraw.Draw(lcw_ov)
        for det in detections:
            bx, by, bw, bh = det['box']
            for box in det.get('defect_boxes', []):
                dbx, dby, dbw, dbh = box
                pad_w = max(6, int(max(dbw, dbh) * 1.2))
                wx1 = max(bx, bx + dbx - pad_w)
                wy1 = max(by, by + dby - pad_w)
                wx2 = min(bx + bw, bx + dbx + dbw + pad_w)
                wy2 = min(by + bh, by + dby + dbh + pad_w)
                d_lcw.rectangle([wx1, wy1, wx2, wy2], outline=(245, 158, 11, 220), width=2)
                d_lcw.rectangle([bx + dbx, by + dby, bx + dbx + dbw, by + dby + dbh], outline=(239, 68, 68, 255), width=2)
        debug_lcw = Image.alpha_composite(debug_lcw, lcw_ov).convert("RGB")
        d_lcw_draw = ImageDraw.Draw(debug_lcw)
        d_lcw_draw.text((12, 12), "DEV STAGE: Local Context Windows (Surrounding Skin Inspection)", fill=(255, 255, 255))

        # Stage I: Pixel Classification Map (Section 6.6.E)
        # Colors: Background (15, 23, 42), Shadow (59, 130, 246), Mango Skin (16, 185, 129), Confirmed Defect (239, 68, 68)
        px_arr = np.full((h, w, 3), (15, 23, 42), dtype=np.uint8)
        if ref_m is not None:
            ref_full = Image.fromarray(ref_m.astype(np.uint8) * 255).resize((w, h), Image.Resampling.NEAREST)
            ref_mask = np.array(ref_full) > 0
            px_arr[ref_mask] = (16, 185, 129)  # Mango skin
        if exsh_m is not None:
            exsh_full = Image.fromarray(exsh_m.astype(np.uint8) * 255).resize((w, h), Image.Resampling.NEAREST)
            sh_mask = np.array(exsh_full) > 0
            px_arr[sh_mask] = (59, 130, 246)  # Shadow
        debug_pxc = Image.fromarray(px_arr)
        d_pxc = ImageDraw.Draw(debug_pxc)
        for det in detections:
            bx, by, bw, bh = det['box']
            for box in det.get('defect_boxes', []):
                dbx, dby, dbw, dbh = box
                d_pxc.rectangle([bx + dbx, by + dby, bx + dbx + dbw, by + dby + dbh], fill=(239, 68, 68), outline=(255, 255, 255), width=1)
        d_pxc.text((12, 12), "DEV STAGE: Pixel Classification (Green: Skin, Blue: Shadow, Red: Defect, Dark: BG)", fill=(255, 255, 255))

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
            "debug_10_final_grade": debug_10,
            "debug_stage_white_bg": debug_wbg,
            "debug_stage_shadow_mask": debug_sh,
            "debug_stage_raw_foreground": debug_rfg,
            "debug_stage_refined_mask": debug_ref,
            "debug_stage_excluded_shadow": debug_exsh,
            "debug_stage_candidate_white_patches": debug_cwp,
            "debug_stage_candidate_grey_shadows": debug_cgs,
            "debug_stage_local_context_windows": debug_lcw,
            "debug_stage_pixel_classification": debug_pxc
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
