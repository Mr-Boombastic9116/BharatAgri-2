from PIL import Image, ImageDraw
import numpy as np
import scipy.ndimage as ndi

def test_pipeline(img):
    w, h = img.size
    rgb_np = np.array(img, dtype=np.float32)
    r = rgb_np[..., 0]
    g = rgb_np[..., 1]
    b = rgb_np[..., 2]

    l_est = 0.299 * r + 0.587 * g + 0.114 * b
    a_est = (r - g) * 0.7 + 128.0
    b_est = (r + g - 2.0 * b) * 0.4 + 128.0
    chroma = np.hypot(a_est - 128.0, b_est - 128.0)

    is_yellow = (r > b * 1.08) & (g > b * 0.90) & (b_est > 128.0) & (l_est > 35.0) & (l_est < 248.0)
    is_green = (g > r * 0.90) & (g > b * 1.02) & (chroma > 8.0) & (l_est > 30.0) & (l_est < 245.0)
    is_breaking = (r > b * 1.04) & (g > b * 0.96) & (chroma > 10.0) & (l_est > 35.0) & (l_est < 248.0)
    peel_raw = is_yellow | is_green | is_breaking

    struct = np.ones((7, 7), dtype=bool)
    peel_clean = ndi.binary_closing(peel_raw, structure=struct)
    peel_clean = ndi.binary_fill_holes(peel_clean)

    # Boundary creases
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

    valid_cores = np.zeros(separated_peel.shape, dtype=np.int32)
    valid_core_count = 0
    if n_cores > 0 and len(sizes) > 0:
        dom_size = float(np.max(sizes))
        min_core_thresh = max(350.0, dom_size * 0.18)
        for idx_c, s in enumerate(sizes, 1):
            if s >= min_core_thresh:
                valid_core_count += 1
                valid_cores[lbl_cores == idx_c] = valid_core_count

    # If valid_core_count >= 2, use cores as seeds
    if valid_core_count >= 2:
        markers = valid_cores
    else:
        # Distance transform fallback for smooth touching fruits
        dist = ndi.distance_transform_edt(peel_clean)
        max_d = float(np.max(dist))
        footprint_rad = max(18, int(max_d * 0.38))
        local_max = (dist == ndi.maximum_filter(dist, footprint=np.ones((footprint_rad, footprint_rad), dtype=bool))) & (dist > max_d * 0.35) & peel_clean
        lbl_p, n_p = ndi.label(local_max)
        if n_p >= 2:
            markers = lbl_p.astype(np.int32)
        else:
            lbl_fallback, _ = ndi.label(peel_clean)
            markers = lbl_fallback.astype(np.int32)

    _, indices = ndi.distance_transform_edt(markers == 0, return_indices=True)
    segmented = markers[indices[0], indices[1]]
    segmented[~peel_clean] = 0

    # Post-validation merge:
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
                m1_dil = ndi.binary_dilation(m1, structure=np.ones((5, 5), dtype=bool))
                if np.sum(m1_dil & m2) > 0:
                    pairs.append((l1, l2))

        for l1, l2 in pairs:
            m1 = (segmented == l1)
            m2 = (segmented == l2)
            a1 = float(np.sum(m1))
            a2 = float(np.sum(m2))
            if a1 == 0 or a2 == 0:
                continue

            # Merge if one part is tiny and was an internal fragment (< 15% of pair)
            if (min(a1, a2) / max(a1, a2)) < 0.15:
                segmented[segmented == l2] = l1
                labels = [l for l in np.unique(segmented) if l > 0]
                changed = True
                break

            # Or if bounding boxes almost completely overlap (IoU > 0.45 or containment > 0.75)
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
                # One box is inside the other -> FALSE SPLIT! MERGE!
                segmented[segmented == l2] = l1
                labels = [l for l in np.unique(segmented) if l > 0]
                changed = True
                break

    return len(np.unique(segmented[segmented > 0]))

# Test 1: 5 synthetic touching mangoes
w, h = 600, 450
img_s = Image.new("RGB", (w, h), (235, 235, 235))
draw = ImageDraw.Draw(img_s)
positions = [
    (80, 80, 220, 240, (230, 190, 25)),
    (180, 70, 320, 230, (220, 175, 20)),
    (280, 90, 420, 250, (130, 195, 40)),
    (130, 200, 270, 360, (215, 160, 30)),
    (240, 210, 380, 370, (225, 185, 35)),
]
for x1, y1, x2, y2, color in positions:
    draw.ellipse([x1, y1, x2, y2], fill=color)

print("Synthetic 5 touching mangoes detected count:", test_pipeline(img_s))

# Test 2: Real He1.jpg
im_he = Image.open('ml/data/mango/extracted/MangoDHDS/Healthy/Healthy/He1.jpg')
print("Real He1.jpg detected count:", test_pipeline(im_he))

# Test 3: Real An5.jpg
im_an = Image.open('ml/data/mango/extracted/MangoDHDS/Anthracnose/Anthracnose/An5.jpg')
print("Real An5.jpg detected count:", test_pipeline(im_an))
