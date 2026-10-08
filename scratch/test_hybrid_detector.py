import sys, os
sys.path.insert(0, os.path.abspath('.'))
from PIL import Image, ImageDraw
import numpy as np
import scipy.ndimage as ndi

def detect_hybrid(img):
    w, h = img.size
    max_dim = 640
    scale = min(1.0, max_dim / max(w, h))
    sw = max(50, int(w * scale))
    sh = max(50, int(h * scale))
    img_small = img.resize((sw, sh), Image.Resampling.BILINEAR)
    rgb_np = np.array(img_small, dtype=np.float32)

    r, g, b = rgb_np[..., 0], rgb_np[..., 1], rgb_np[..., 2]
    l_est = 0.299 * r + 0.587 * g + 0.114 * b
    a_est = (r - g) * 0.7 + 128.0
    b_est = (r + g - 2.0 * b) * 0.4 + 128.0
    chroma = np.hypot(a_est - 128.0, b_est - 128.0)

    is_yellow = (r > b * 1.10) & (g > b * 0.92) & (b_est > 128.0) & (l_est > 35.0) & (l_est < 248.0)
    is_green = (g > r * 0.90) & (g > b * 1.02) & (chroma > 8.0) & (l_est > 30.0) & (l_est < 245.0)
    is_breaking = (r > b * 1.04) & (g > b * 0.96) & (chroma > 10.0) & (l_est > 35.0) & (l_est < 248.0)
    peel_raw = is_yellow | is_green | is_breaking
    peel_clean = ndi.binary_closing(peel_raw, structure=np.ones((7, 7), dtype=bool))
    peel_clean = ndi.binary_fill_holes(peel_clean)

    # Multi-channel edge gradients
    gx_l = ndi.sobel(l_est, axis=1)
    gy_l = ndi.sobel(l_est, axis=0)
    grad_l = np.hypot(gx_l, gy_l)

    gx_a = ndi.sobel(a_est, axis=1)
    gy_a = ndi.sobel(a_est, axis=0)
    grad_a = np.hypot(gx_a, gy_a)

    gx_b = ndi.sobel(b_est, axis=1)
    gy_b = ndi.sobel(b_est, axis=0)
    grad_b = np.hypot(gx_b, gy_b)

    total_grad = grad_l + 0.7 * (grad_a + grad_b)

    # Detect internal seams / shadow valleys
    peel_grads = total_grad[peel_clean]
    if len(peel_grads) == 0:
        return 0

    p75 = np.percentile(peel_grads, 75)
    seams = (total_grad > max(14.0, float(p75))) & peel_clean

    # Thin seam barrier
    seam_barrier = ndi.binary_dilation(seams, structure=np.ones((3, 3), dtype=bool))
    separated_peel = peel_clean & (~seam_barrier)
    separated_peel = ndi.binary_opening(separated_peel, structure=np.ones((3, 3), dtype=bool))

    # Distance transform on separated cores
    dist_cores = ndi.distance_transform_edt(separated_peel)
    max_d_c = float(np.max(dist_cores)) if np.sum(separated_peel) > 0 else 0.0

    # Markers from separated cores
    lbl_c, n_c = ndi.label(separated_peel)
    sizes = ndi.sum(separated_peel, lbl_c, range(1, n_c + 1)) if n_c > 0 else []

    markers = np.zeros(peel_clean.shape, dtype=np.int32)
    marker_count = 0
    marker_centers = []

    if n_c > 0 and len(sizes) > 0:
        dom_size = float(np.max(sizes))
        min_c_thresh = max(80.0, dom_size * 0.05)
        for idx_c, s in enumerate(sizes, 1):
            if s >= min_c_thresh:
                # Core mask
                c_mask = (lbl_c == idx_c)
                c_dist = dist_cores.copy()
                c_dist[~c_mask] = 0
                max_in_c = float(np.max(c_dist))
                # Check if this core is itself multiple merged mangoes
                # If core is elongated and has multiple peaks:
                fp = max(9, int(max_in_c * 0.40)) | 1
                c_peaks = (c_dist == ndi.maximum_filter(c_dist, footprint=np.ones((fp, fp), dtype=bool))) & (c_dist > max(10.0, max_in_c * 0.40))
                lbl_cp, n_cp = ndi.label(c_peaks)
                if n_cp > 1 and s > dom_size * 0.45:
                    for cp_i in range(1, n_cp + 1):
                        ys, xs = np.where(lbl_cp == cp_i)
                        marker_count += 1
                        markers[lbl_cp == cp_i] = marker_count
                        marker_centers.append((float(np.mean(xs)), float(np.mean(ys))))
                else:
                    marker_count += 1
                    markers[c_mask] = marker_count
                    ys, xs = np.where(c_mask)
                    marker_centers.append((float(np.mean(xs)), float(np.mean(ys))))

    if marker_count < 2:
        # Fallback to EDT on full peel
        dist_full = ndi.distance_transform_edt(peel_clean)
        max_d_f = float(np.max(dist_full))
        fp = max(15, int(max_d_f * 0.35)) | 1
        local_max = (dist_full == ndi.maximum_filter(dist_full, footprint=np.ones((fp, fp), dtype=bool))) & (dist_full > max_d_f * 0.30) & peel_clean
        lbl_p, n_p = ndi.label(local_max)
        if n_p >= 2:
            markers = np.zeros(peel_clean.shape, dtype=np.int32)
            marker_count = 0
            for p in range(1, n_p + 1):
                marker_count += 1
                markers[lbl_p == p] = marker_count
        else:
            lbl_f, _ = ndi.label(peel_clean)
            markers = lbl_f.astype(np.int32)
            marker_count = 1

    # Watershed / Geodesic Voronoi
    _, indices = ndi.distance_transform_edt(markers == 0, return_indices=True)
    segmented = markers[indices[0], indices[1]]
    segmented[~peel_clean] = 0

    # Merging false splits
    labels = [l for l in np.unique(segmented) if l > 0]
    changed = True
    while changed and len(labels) > 1:
        changed = False
        pairs = []
        for i in range(len(labels)):
            for j in range(i + 1, len(labels)):
                l1, l2 = labels[i], labels[j]
                m1 = (segmented == l1)
                m2 = (segmented == l2)
                m1_dil = ndi.binary_dilation(m1, structure=np.ones((3, 3), dtype=bool))
                if np.sum(m1_dil & m2) > 0:
                    pairs.append((l1, l2))

        for l1, l2 in pairs:
            m1 = (segmented == l1)
            m2 = (segmented == l2)
            a1, a2 = float(np.sum(m1)), float(np.sum(m2))
            if a1 == 0 or a2 == 0:
                continue

            # Merge tiny fragments (< 12%)
            if (min(a1, a2) / max(a1, a2)) < 0.12:
                segmented[segmented == l2] = l1
                labels = [l for l in np.unique(segmented) if l > 0]
                changed = True
                break

            # Seam gradient check
            seam = ndi.binary_dilation(m1, structure=np.ones((3, 3), bool)) & ndi.binary_dilation(m2, structure=np.ones((3, 3), bool)) & peel_clean
            if np.sum(seam) > 0:
                seam_grad = float(np.mean(total_grad[seam]))
                mean_L1 = float(np.mean(l_est[m1]))
                mean_L2 = float(np.mean(l_est[m2]))
                if seam_grad < 10.0 and abs(mean_L1 - mean_L2) < 5.0:
                    segmented[segmented == l2] = l1
                    labels = [l for l in np.unique(segmented) if l > 0]
                    changed = True
                    break

    final_labels = [l for l in np.unique(segmented) if l > 0 and np.sum(segmented == l) >= 200]
    return len(final_labels)

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
print("600x450 result:", detect_hybrid(img600))

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
print("1200x900 result:", detect_hybrid(img1200))

# Test single mango
img_single = Image.new("RGB", (400, 300), (240, 240, 240))
draw_s = ImageDraw.Draw(img_single)
draw_s.ellipse([100, 60, 300, 240], fill=(230, 180, 25))
print("Single mango result:", detect_hybrid(img_single))
