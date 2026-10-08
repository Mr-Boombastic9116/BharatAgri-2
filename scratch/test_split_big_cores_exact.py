import sys, os
sys.path.insert(0, os.path.abspath('.'))
from PIL import Image, ImageDraw
import numpy as np
import scipy.ndimage as ndi

def detect_robust(img):
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

    # Edge gradient
    gx = ndi.sobel(l_est, axis=1)
    gy = ndi.sobel(l_est, axis=0)
    grad = np.hypot(gx, gy)
    peel_grads = grad[peel_clean]
    p85 = np.percentile(peel_grads, 85) if len(peel_grads) > 0 else 35.0
    edge_thresh = max(28.0, float(p85))
    raw_edges = (grad > edge_thresh) & peel_clean

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

    markers = np.zeros(separated_peel.shape, dtype=np.int32)
    marker_count = 0

    if n_cores > 0 and len(sizes) > 0:
        med_size = float(np.median(sizes))
        dom_size = float(np.max(sizes))
        min_core_thresh = max(350.0, dom_size * 0.18)

        for idx_c, s in enumerate(sizes, 1):
            if s < min_core_thresh:
                continue
            c_mask = (lbl_cores == idx_c)

            # If core is huge compared to median (> 1.8x median) or has area > 20000:
            # Check for multiple internal distance transform peaks
            if s > max(20000.0, med_size * 1.8):
                c_dist = ndi.distance_transform_edt(c_mask)
                max_cd = float(np.max(c_dist))
                fp = max(15, int(max_cd * 0.38)) | 1
                c_peaks = (c_dist == ndi.maximum_filter(c_dist, footprint=np.ones((fp, fp), dtype=bool))) & (c_dist > max(15.0, max_cd * 0.35))
                lbl_cp, n_cp = ndi.label(c_peaks)
                if n_cp > 1:
                    peak_pts = []
                    for cp_i in range(1, n_cp + 1):
                        ys, xs = np.where(lbl_cp == cp_i)
                        peak_pts.append((float(np.mean(xs)), float(np.mean(ys)), float(np.mean(c_dist[ys, xs])), cp_i))
                    peak_pts.sort(key=lambda p: p[2], reverse=True)
                    min_peak_d = max(25.0, max_cd * 0.45)
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

    if marker_count < 2:
        # Fallback EDT
        dist = ndi.distance_transform_edt(peel_clean)
        max_d = float(np.max(dist))
        footprint_rad = max(20, int(max_d * 0.42))
        local_max = (dist == ndi.maximum_filter(dist, footprint=np.ones((footprint_rad, footprint_rad), dtype=bool))) & (dist > max_d * 0.35) & peel_clean
        lbl_p, n_p = ndi.label(local_max)
        if n_p >= 2:
            peak_points = []
            for p_idx in range(1, n_p + 1):
                ys, xs = np.where(lbl_p == p_idx)
                peak_points.append((float(np.mean(xs)), float(np.mean(ys)), float(np.mean(dist[ys, xs])), p_idx))
            peak_points.sort(key=lambda p: p[2], reverse=True)
            min_peak_dist = max(28.0, max_d * 0.45)
            kept_centers = []
            markers = np.zeros(peel_clean.shape, dtype=np.int32)
            marker_count = 0
            for cx, cy, val, p_idx in peak_points:
                if not any(np.hypot(cx - kx, cy - ky) < min_peak_dist for kx, ky in kept_centers):
                    marker_count += 1
                    markers[lbl_p == p_idx] = marker_count
                    kept_centers.append((cx, cy))
        else:
            lbl_fallback, _ = ndi.label(peel_clean)
            markers = lbl_fallback.astype(np.int32)

    # Voronoi
    _, indices = ndi.distance_transform_edt(markers == 0, return_indices=True)
    segmented = markers[indices[0], indices[1]]
    segmented[~peel_clean] = 0

    return len([l for l in np.unique(segmented) if l > 0])

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
print("600x450:", detect_robust(img600))

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
print("1200x900:", detect_robust(img1200))

# Test single
img_single = Image.new("RGB", (400, 300), (240, 240, 240))
draw_s = ImageDraw.Draw(img_single)
draw_s.ellipse([100, 60, 300, 240], fill=(230, 180, 25))
print("Single mango:", detect_robust(img_single))
