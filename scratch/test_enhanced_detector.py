import sys, os
sys.path.insert(0, os.path.abspath('.'))
import numpy as np
from PIL import Image, ImageDraw
import scipy.ndimage as ndi
from scipy.spatial import ConvexHull

def detect_mangoes_enhanced(img, min_area=400):
    orig_w, orig_h = img.size
    
    # Scale proxy for segmentation
    max_dim = 640
    scale = min(1.0, max_dim / max(orig_w, orig_h))
    sw = max(50, int(orig_w * scale))
    sh = max(50, int(orig_h * scale))
    img_small = img.resize((sw, sh), Image.Resampling.BILINEAR)
    rgb_np = np.array(img_small, dtype=np.float32)

    r, g, b = rgb_np[..., 0], rgb_np[..., 1], rgb_np[..., 2]
    l_est = 0.299 * r + 0.587 * g + 0.114 * b
    a_est = (r - g) * 0.7 + 128.0
    b_est = (r + g - 2.0 * b) * 0.4 + 128.0
    chroma = np.hypot(a_est - 128.0, b_est - 128.0)

    # Peel mask
    is_yellow = (r > b * 1.10) & (g > b * 0.92) & (b_est > 128.0) & (l_est > 35.0) & (l_est < 248.0)
    is_green = (g > r * 0.90) & (g > b * 1.02) & (chroma > 8.0) & (l_est > 30.0) & (l_est < 245.0)
    is_breaking = (r > b * 1.04) & (g > b * 0.96) & (chroma > 10.0) & (l_est > 35.0) & (l_est < 248.0)
    peel_raw = is_yellow | is_green | is_breaking

    # Dynamic closing kernel relative to scale
    k_close = max(3, int(round(5 * scale))) | 1
    peel_clean = ndi.binary_closing(peel_raw, structure=np.ones((k_close, k_close), dtype=bool))
    peel_clean = ndi.binary_fill_holes(peel_clean)

    # Filter tiny noise
    lbl_raw, n_raw = ndi.label(peel_clean)
    if n_raw > 1:
        raw_sizes = ndi.sum(peel_clean, lbl_raw, range(1, n_raw + 1))
        dom_raw = float(np.max(raw_sizes))
        min_keep = max(150.0, dom_raw * 0.04)
        filtered_peel = np.zeros_like(peel_clean)
        for idx_r, s in enumerate(raw_sizes, 1):
            if s >= min_keep:
                filtered_peel[lbl_raw == idx_r] = True
        peel_clean = filtered_peel

    if np.sum(peel_clean) < 200:
        return []

    # Stage 1: Detect bunches
    lbl_bunches, n_bunches = ndi.label(peel_clean)

    # Edge gradients
    gx = ndi.sobel(l_est, axis=1)
    gy = ndi.sobel(l_est, axis=0)
    grad = np.hypot(gx, gy)

    all_instance_masks = []
    global_instance_id = 0

    for b_idx in range(1, n_bunches + 1):
        bunch_mask = (lbl_bunches == b_idx)
        bunch_size = float(np.sum(bunch_mask))
        if bunch_size < 250:
            continue

        # Distance transform
        dist = ndi.distance_transform_edt(bunch_mask)
        max_d = float(np.max(dist))
        if max_d < 5.0:
            continue

        # Estimate typical single fruit radius within this bunch
        # Typical fruit radius in downscaled image:
        r_est = max(12.0, min(max_d, 55.0))

        # Depth / shadow valleys & gradient creases:
        local_mean_L = ndi.uniform_filter(l_est, size=max(5, int(r_est * 0.4)))
        shadow_valleys = (l_est < (local_mean_L - 8.0)) & bunch_mask
        
        peel_grads = grad[bunch_mask]
        p80 = np.percentile(peel_grads, 80) if len(peel_grads) > 0 else 25.0
        edge_creases = (grad > max(20.0, float(p80))) & bunch_mask

        # Boundary penalty for distance transform
        penalized_dist = dist.copy()
        penalized_dist[shadow_valleys | edge_creases] *= 0.5

        # Peak detection with adaptive footprint
        footprint_rad = max(8, int(r_est * 0.32)) | 1
        local_max = (penalized_dist == ndi.maximum_filter(penalized_dist, footprint=np.ones((footprint_rad, footprint_rad), dtype=bool)))
        local_max = local_max & (penalized_dist > max(6.0, max_d * 0.20)) & bunch_mask

        lbl_p, n_p = ndi.label(local_max)
        peaks = []
        for p in range(1, n_p + 1):
            ys, xs = np.where(lbl_p == p)
            v = float(np.mean(dist[ys, xs]))
            peaks.append((float(np.mean(xs)), float(np.mean(ys)), v, p))

        peaks.sort(key=lambda x: x[2], reverse=True)

        # Adaptive minimum peak distance
        min_peak_dist = max(18.0, r_est * 0.45)
        kept_markers = np.zeros(bunch_mask.shape, dtype=np.int32)
        kept_centers = []
        kept_count = 0
        for cx, cy, val, p in peaks:
            too_close = False
            for kx, ky in kept_centers:
                if np.hypot(cx - kx, cy - ky) < min_peak_dist:
                    too_close = True
                    break
            if not too_close:
                kept_count += 1
                kept_centers.append((cx, cy))
                kept_markers[lbl_p == p] = kept_count

        if kept_count <= 1:
            # Single mango bunch
            global_instance_id += 1
            all_instance_masks.append(bunch_mask)
        else:
            # Multi-mango bunch -> Marker-controlled Voronoi/Watershed
            _, indices = ndi.distance_transform_edt(kept_markers == 0, return_indices=True)
            segmented_bunch = kept_markers[indices[0], indices[1]]
            segmented_bunch[~bunch_mask] = 0

            # Candidate validation & fragment merging
            labels = [l for l in np.unique(segmented_bunch) if l > 0]
            changed = True
            while changed and len(labels) > 1:
                changed = False
                pairs = []
                for i in range(len(labels)):
                    for j in range(i + 1, len(labels)):
                        l1, l2 = labels[i], labels[j]
                        m1 = (segmented_bunch == l1)
                        m2 = (segmented_bunch == l2)
                        m1_dil = ndi.binary_dilation(m1, structure=np.ones((3, 3), dtype=bool))
                        if np.sum(m1_dil & m2) > 0:
                            pairs.append((l1, l2))

                for l1, l2 in pairs:
                    m1 = (segmented_bunch == l1)
                    m2 = (segmented_bunch == l2)
                    a1 = float(np.sum(m1))
                    a2 = float(np.sum(m2))
                    if a1 == 0 or a2 == 0:
                        continue

                    # Merge tiny fragments (< 10% of pair)
                    if (min(a1, a2) / max(a1, a2)) < 0.10:
                        segmented_bunch[segmented_bunch == l2] = l1
                        labels = [l for l in np.unique(segmented_bunch) if l > 0]
                        changed = True
                        break

                    # Check interface boundary evidence: if no shadow valley and low gradient, merge
                    seam = ndi.binary_dilation(m1, structure=np.ones((3, 3), bool)) & ndi.binary_dilation(m2, structure=np.ones((3, 3), bool)) & bunch_mask
                    if np.sum(seam) > 0:
                        seam_grad_mean = float(np.mean(grad[seam]))
                        seam_valley_ratio = float(np.mean(shadow_valleys[seam]))
                        mean_L1 = float(np.mean(l_est[m1]))
                        mean_L2 = float(np.mean(l_est[m2]))
                        diff_L = abs(mean_L1 - mean_L2)
                        # If seam has almost no edge and no valley and identical color
                        if seam_grad_mean < 12.0 and seam_valley_ratio < 0.05 and diff_L < 6.0:
                            segmented_bunch[segmented_bunch == l2] = l1
                            labels = [l for l in np.unique(segmented_bunch) if l > 0]
                            changed = True
                            break

            for l in np.unique(segmented_bunch):
                if l > 0:
                    cand_m = (segmented_bunch == l)
                    if np.sum(cand_m) >= 200:
                        all_instance_masks.append(cand_m)

    return all_instance_masks

# Test on 600x450 and 1200x900
for (w, h) in [(600, 450), (1200, 900)]:
    img = Image.new("RGB", (w, h), (235, 235, 235))
    draw = ImageDraw.Draw(img)
    scale = w / 600.0
    positions = [
        (int(80*scale), int(80*scale), int(220*scale), int(240*scale), (230, 190, 25)),
        (int(180*scale), int(70*scale), int(320*scale), int(230*scale), (220, 175, 20)),
        (int(280*scale), int(90*scale), int(420*scale), int(250*scale), (130, 195, 40)),
        (int(130*scale), int(200*scale), int(270*scale), int(360*scale), (215, 160, 30)),
        (int(240*scale), int(210*scale), int(380*scale), int(370*scale), (225, 185, 35)),
    ]
    for x1, y1, x2, y2, color in positions:
        draw.ellipse([x1, y1, x2, y2], fill=color)

    res = detect_mangoes_enhanced(img)
    print(f"Enhanced Detector {w}x{h}: Detected {len(res)} mango instances")

# Also test single isolated mango to make sure NO over-segmentation!
img_single = Image.new("RGB", (400, 300), (240, 240, 240))
draw_s = ImageDraw.Draw(img_single)
draw_s.ellipse([100, 60, 300, 240], fill=(230, 180, 25))
res_s = detect_mangoes_enhanced(img_single)
print(f"Single Mango Test: Detected {len(res_s)} mango instance")
