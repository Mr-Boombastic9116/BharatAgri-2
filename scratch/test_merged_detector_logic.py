import sys, os
sys.path.insert(0, os.path.abspath('.'))
from PIL import Image, ImageDraw
import numpy as np
import scipy.ndimage as ndi

def detect_test(img):
    w, h = img.size
    max_dim = 640
    scale = min(1.0, max_dim / max(w, h))
    sw = max(50, int(w * scale))
    sh = max(50, int(h * scale))
    img_small = img.resize((sw, sh), Image.Resampling.BILINEAR)
    rgb_np = np.array(img_small, dtype=np.float32)

    r = rgb_np[..., 0]
    g = rgb_np[..., 1]
    b = rgb_np[..., 2]

    l_est = 0.299 * r + 0.587 * g + 0.114 * b
    a_est = (r - g) * 0.7 + 128.0
    b_est = (r + g - 2.0 * b) * 0.4 + 128.0
    chroma = np.hypot(a_est - 128.0, b_est - 128.0)

    is_yellow = (r > b * 1.10) & (g > b * 0.92) & (b_est > 128.0) & (l_est > 35.0) & (l_est < 248.0)
    is_green = (g > r * 0.90) & (g > b * 1.02) & (chroma > 8.0) & (l_est > 30.0) & (l_est < 245.0)
    is_breaking = (r > b * 1.04) & (g > b * 0.96) & (chroma > 10.0) & (l_est > 35.0) & (l_est < 248.0)
    peel_raw = is_yellow | is_green | is_breaking

    struct = np.ones((7, 7), dtype=bool)
    peel_clean = ndi.binary_closing(peel_raw, structure=struct)
    peel_clean = ndi.binary_fill_holes(peel_clean)

    # Edge gradient creases & shadow valleys
    gx = ndi.sobel(l_est, axis=1)
    gy = ndi.sobel(l_est, axis=0)
    grad = np.hypot(gx, gy)
    peel_grads = grad[peel_clean]
    p85 = np.percentile(peel_grads, 85) if len(peel_grads) > 0 else 35.0
    edge_thresh = max(24.0, float(p85))
    raw_edges = (grad > edge_thresh) & peel_clean

    lbl_e, n_e = ndi.label(raw_edges)
    edge_sizes = ndi.sum(raw_edges, lbl_e, range(1, n_e + 1)) if n_e > 0 else []
    clean_creases = np.zeros_like(raw_edges, dtype=bool)
    for idx_e, s in enumerate(edge_sizes, 1):
        if s >= 15:
            clean_creases[lbl_e == idx_e] = True

    crease_barrier = ndi.binary_dilation(clean_creases, structure=np.ones((3, 3), dtype=bool))
    separated_peel = peel_clean & (~crease_barrier)
    separated_peel = ndi.binary_opening(separated_peel, structure=np.ones((5, 5), dtype=bool))

    lbl_cores, n_cores = ndi.label(separated_peel)
    sizes = ndi.sum(separated_peel, lbl_cores, range(1, n_cores + 1)) if n_cores > 0 else []

    markers = np.zeros(separated_peel.shape, dtype=np.int32)
    marker_count = 0
    marker_centers = []

    if n_cores > 0 and len(sizes) > 0:
        dom_size = float(np.max(sizes))
        min_core_thresh = max(250.0, dom_size * 0.12)
        dist_sep = ndi.distance_transform_edt(separated_peel)

        for idx_c, s in enumerate(sizes, 1):
            if s < min_core_thresh:
                continue
            c_mask = (lbl_cores == idx_c)
            c_dist = dist_sep.copy()
            c_dist[~c_mask] = 0.0
            max_c_d = float(np.max(c_dist))

            # Look for sub-peaks within large or elongated core
            fp = max(11, int(max_c_d * 0.38)) | 1
            local_max = (c_dist == ndi.maximum_filter(c_dist, footprint=np.ones((fp, fp), dtype=bool))) & (c_dist > max(10.0, max_c_d * 0.35))
            lbl_p, n_p = ndi.label(local_max)

            if n_p > 1 and s >= min_core_thresh * 1.5:
                # Core contains multiple touching fruits
                peak_points = []
                for p_idx in range(1, n_p + 1):
                    ys, xs = np.where(lbl_p == p_idx)
                    val = float(np.mean(c_dist[ys, xs]))
                    peak_points.append((float(np.mean(xs)), float(np.mean(ys)), val, p_idx))
                peak_points.sort(key=lambda p: p[2], reverse=True)
                min_peak_dist = max(20.0, max_c_d * 0.40)
                kept_centers = []
                for cx, cy, val, p_idx in peak_points:
                    if not any(np.hypot(cx - kx, cy - ky) < min_peak_dist for kx, ky in kept_centers):
                        marker_count += 1
                        markers[lbl_p == p_idx] = marker_count
                        kept_centers.append((cx, cy))
            else:
                marker_count += 1
                markers[c_mask] = marker_count

    if marker_count < 2:
        # Fallback to EDT on full peel
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
                if not any(np.hypot(cx - kx, cy - ky) < min_peak_dist for kx, ky in kept_centers):
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

    # Voronoi / Marker-controlled partition
    _, indices = ndi.distance_transform_edt(markers == 0, return_indices=True)
    segmented_instances = markers[indices[0], indices[1]]
    segmented_instances[~peel_clean] = 0

    # Post-watershed merger
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

            # Asymmetry check
            if (min(a1, a2) / max(a1, a2)) < 0.12:
                segmented_instances[segmented_instances == l2] = l1
                labels = [l for l in np.unique(segmented_instances) if l > 0]
                changed = True
                break

            # Box containment
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

            if containment > 0.80:
                segmented_instances[segmented_instances == l2] = l1
                labels = [l for l in np.unique(segmented_instances) if l > 0]
                changed = True
                break

            # Distance between centers
            cy1, cx1 = np.mean(y1_1), np.mean(x1_1)
            cy2, cx2 = np.mean(y1_2), np.mean(x1_2)
            center_dist = float(np.hypot(cx1 - cx2, cy1 - cy2))
            m_comb = m1 | m2
            dist_comb = ndi.distance_transform_edt(m_comb)
            max_d_comb = float(np.max(dist_comb))
            min_realistic_center_dist = max(22.0, max_d_comb * 0.42)
            seam = ndi.binary_dilation(m1, structure=np.ones((3, 3), bool)) & ndi.binary_dilation(m2, structure=np.ones((3, 3), bool)) & m_comb
            seam_max = float(np.max(dist_comb[seam])) if np.sum(seam) > 0 else 0.0
            seam_ratio = seam_max / max(1.0, max_d_comb)

            if center_dist < min_realistic_center_dist or seam_ratio > 0.90:
                segmented_instances[segmented_instances == l2] = l1
                labels = [l for l in np.unique(segmented_instances) if l > 0]
                changed = True
                break

    return len([l for l in np.unique(segmented_instances) if l > 0])

# Test 600x450
w, h = 600, 450
img600 = Image.new("RGB", (w, h), (235, 235, 235))
draw600 = ImageDraw.Draw(img600)
positions = [
    (80, 80, 220, 240, (230, 190, 25)),
    (180, 70, 320, 230, (220, 175, 20)),
    (280, 90, 420, 250, (130, 195, 40)),
    (130, 200, 270, 360, (215, 160, 30)),
    (240, 210, 380, 370, (225, 185, 35)),
]
for x1, y1, x2, y2, color in positions:
    draw600.ellipse([x1, y1, x2, y2], fill=color)
print("600x450 count:", detect_test(img600))

# Test 1200x900
w, h = 1200, 900
img1200 = Image.new("RGB", (w, h), (235, 235, 235))
draw1200 = ImageDraw.Draw(img1200)
scale = w / 600.0
positions1200 = [
    (int(80*scale), int(80*scale), int(220*scale), int(240*scale), (230, 190, 25)),
    (int(180*scale), int(70*scale), int(320*scale), int(230*scale), (220, 175, 20)),
    (int(280*scale), int(90*scale), int(420*scale), int(250*scale), (130, 195, 40)),
    (int(130*scale), int(200*scale), int(270*scale), int(360*scale), (215, 160, 30)),
    (int(240*scale), int(210*scale), int(380*scale), int(370*scale), (225, 185, 35)),
]
for x1, y1, x2, y2, color in positions1200:
    draw1200.ellipse([x1, y1, x2, y2], fill=color)
print("1200x900 count:", detect_test(img1200))

# Test single
img_single = Image.new("RGB", (400, 300), (240, 240, 240))
draw_s = ImageDraw.Draw(img_single)
draw_s.ellipse([100, 60, 300, 240], fill=(230, 180, 25))
print("Single mango count:", detect_test(img_single))
