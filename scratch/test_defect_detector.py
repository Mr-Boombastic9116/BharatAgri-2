"""
Develop and benchmark localized defect segmentation inside mango masks.
"""
import os
import sys
import numpy as np
from PIL import Image
import scipy.ndimage as ndi

def detect_defects_in_mango(crop_img, inst_mask=None):
    """
    Detects necrotic lesions, black spots, anthracnose, and cankers
    strictly within the mango peel boundary.
    Operates at native resolution with local contrast enhancement.
    """
    w, h = crop_img.size
    rgb_arr = np.array(crop_img, dtype=np.float32)
    r = rgb_arr[..., 0]
    g = rgb_arr[..., 1]
    b = rgb_arr[..., 2]

    # CIELAB calculation
    l_est = 0.299 * r + 0.587 * g + 0.114 * b
    a_est = (r - g) * 0.7 + 128.0
    b_est = (r + g - 2.0 * b) * 0.4 + 128.0
    chroma = np.hypot(a_est - 128.0, b_est - 128.0)

    # 1. Determine mango peel mask if not provided
    if inst_mask is not None:
        # Resize inst_mask to crop size if needed
        if inst_mask.shape != (h, w):
            inst_mask = np.array(Image.fromarray(inst_mask.astype(np.uint8)).resize((w, h), Image.Resampling.NEAREST)) > 0
        fruit_peel = inst_mask
    else:
        # Self-segment peel from crop:
        is_yellow = (r > b * 1.10) & (g > b * 0.92) & (b_est > 128.0) & (l_est > 35.0) & (l_est < 248.0)
        is_green = (g > r * 0.92) & (g > b * 1.02) & (chroma > 8.0) & (l_est > 30.0) & (l_est < 245.0)
        is_blush = (r > 120.0) & (r > g * 1.05) & (chroma > 12.0) & (l_est > 35.0)
        fruit_peel = is_yellow | is_green | is_blush
        fruit_peel = ndi.binary_fill_holes(ndi.binary_closing(fruit_peel, structure=np.ones((7, 7), dtype=bool)))

    total_mango_pixels = float(np.sum(fruit_peel))
    if total_mango_pixels < 200:
        return {
            "affected_area_pct": 0.0,
            "defect_boxes": [],
            "defect_mask": np.zeros((h, w), dtype=bool),
            "total_defect_pixels": 0,
            "largest_defect_pixels": 0,
            "num_regions": 0,
            "confidence": 0.0
        }

    # Slightly erode outer boundary by 3 pixels to prevent boundary shadow false positives
    inner_peel = ndi.binary_erosion(fruit_peel, structure=np.ones((5, 5), dtype=bool))
    if np.sum(inner_peel) < 100:
        inner_peel = fruit_peel

    peel_L = l_est[inner_peel]
    median_L = float(np.median(peel_L))
    p75_L = float(np.percentile(peel_L, 75))

    # Compute local mean luminance using uniform filter (radius ~15 pixels)
    # to capture local contrast differences
    filter_radius = max(9, int(min(w, h) * 0.08))
    if filter_radius % 2 == 0:
        filter_radius += 1
    local_mean_L = ndi.uniform_filter(l_est, size=filter_radius)

    # Gradients for edge texture of lesions
    gx = ndi.sobel(l_est, axis=1)
    gy = ndi.sobel(l_est, axis=0)
    grad = np.hypot(gx, gy)

    # DEFECT SIGNAL COMBINATION:
    # 1. Dark necrotic lesions: significantly darker than local surrounding peel
    # Threshold scales with peel brightness (brighter peel has higher contrast drop)
    contrast_drop = max(22.0, (median_L - 30.0) * 0.28)
    local_dark = (l_est < (local_mean_L - contrast_drop)) & (l_est < (median_L - 18.0))
    
    # 2. Deep necrotic black/brown spots (absolute dark & low chroma relative to peel)
    deep_dark = (l_est < 65.0) & (l_est < (median_L - 15.0))
    sunken_black = (l_est < 45.0)
    
    # 3. Rough scab / canker texture: high gradient edge + noticeably darker
    canker_lesion = (grad > 28.0) & (l_est < (median_L - 25.0)) & (l_est < 95.0)

    # Combine candidates within the inner peel
    candidate_defects = (local_dark | deep_dark | sunken_black | canker_lesion) & inner_peel

    # Reject natural healthy green peel:
    # Healthy green has g > r * 1.05 and g > b * 1.10 and l_est > 60
    is_healthy_green = (g > r * 1.05) & (g > b * 1.10) & (l_est > 60.0)
    candidate_defects = candidate_defects & (~is_healthy_green)

    # Filter noise: remove isolated single-pixel noise, but keep small spots >= 6 pixels
    lbl_d, n_d = ndi.label(candidate_defects)
    sizes = ndi.sum(candidate_defects, lbl_d, range(1, n_d + 1)) if n_d > 0 else []

    clean_mask = np.zeros_like(candidate_defects, dtype=bool)
    largest_region = 0
    defect_boxes = []
    
    for idx_d, s in enumerate(sizes, 1):
        if s >= 6:  # Preserves small spots!
            clean_mask[lbl_d == idx_d] = True
            if s > largest_region:
                largest_region = int(s)
            
            d_region = (lbl_d == idx_d)
            dys, dxs = np.where(d_region)
            bx1 = int(np.min(dxs))
            by1 = int(np.min(dys))
            bw_box = int(np.max(dxs) - bx1 + 1)
            bh_box = int(np.max(dys) - by1 + 1)
            defect_boxes.append([bx1, by1, bw_box, bh_box])

    total_defect_pixels = int(np.sum(clean_mask))
    affected_pct = round((total_defect_pixels / total_mango_pixels) * 100.0, 1)

    # Sort defect boxes by area descending
    defect_boxes.sort(key=lambda b: b[2] * b[3], reverse=True)

    # Defect confidence
    if total_defect_pixels > 0:
        conf = min(99.0, 75.0 + min(20.0, affected_pct * 4.0))
    else:
        conf = 0.0

    return {
        "affected_area_pct": affected_pct,
        "defect_boxes": defect_boxes[:12],
        "defect_mask": clean_mask,
        "total_defect_pixels": total_defect_pixels,
        "largest_defect_pixels": largest_region,
        "num_regions": len(defect_boxes),
        "confidence": round(conf, 1)
    }

if __name__ == '__main__':
    print("Testing defect detector on real dataset images...")
    anthra_dir = os.path.join('ml', 'data', 'mango', 'extracted', 'MangoDHDS', 'Anthracnose', 'Anthracnose')
    healthy_dir = os.path.join('ml', 'data', 'mango', 'extracted', 'MangoDHDS', 'Healthy', 'Healthy')

    print("\n--- ANTHRACNOSE (BLACK SPOTS) ---")
    for f in ['An1.jpg', 'An2.jpg', 'An3.jpg', 'An5.jpg', 'An10.jpg', 'An15.jpg', 'An20.jpg']:
        p = os.path.join(anthra_dir, f)
        if os.path.exists(p):
            im = Image.open(p)
            res = detect_defects_in_mango(im)
            print(f"{f}: affected%={res['affected_area_pct']}%, spots={res['num_regions']}, total_px={res['total_defect_pixels']}, largest={res['largest_defect_pixels']}")

    print("\n--- HEALTHY (CLEAN PEEL) ---")
    for f in ['He1.jpg', 'He2.jpg', 'He3.jpg', 'He5.jpg', 'He10.jpg']:
        p = os.path.join(healthy_dir, f)
        if os.path.exists(p):
            im = Image.open(p)
            res = detect_defects_in_mango(im)
            print(f"{f}: affected%={res['affected_area_pct']}%, spots={res['num_regions']}, total_px={res['total_defect_pixels']}, largest={res['largest_defect_pixels']}")
