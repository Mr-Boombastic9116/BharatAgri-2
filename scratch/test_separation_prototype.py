import sys, os
sys.path.insert(0, os.path.abspath('.'))
import numpy as np
from PIL import Image, ImageDraw
import scipy.ndimage as ndi
from scipy.spatial import ConvexHull

def test_separated():
    w, h = 600, 450
    img = Image.new("RGB", (w, h), (235, 235, 235))
    draw = ImageDraw.Draw(img)

    # 5 touching/overlapping mangoes
    positions = [
        (80, 80, 220, 240, (230, 190, 25)),
        (180, 70, 320, 230, (220, 175, 20)),
        (280, 90, 420, 250, (130, 195, 40)),
        (130, 200, 270, 360, (215, 160, 30)),
        (240, 210, 380, 370, (225, 185, 35)),
    ]
    for x1, y1, x2, y2, color in positions:
        draw.ellipse([x1, y1, x2, y2], fill=color)

    rgb = np.array(img, dtype=np.float32)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
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

    # Stage 1: Detect bunches
    lbl_bunch, n_bunch = ndi.label(peel_clean)
    print(f"Detected {n_bunch} bunch(es)")

    gx = ndi.sobel(l_est, axis=1)
    gy = ndi.sobel(l_est, axis=0)
    grad = np.hypot(gx, gy)

    total_instances = 0
    for b_idx in range(1, n_bunch + 1):
        b_mask = (lbl_bunch == b_idx)
        if np.sum(b_mask) < 400:
            continue
        
        # Distance transform
        dist = ndi.distance_transform_edt(b_mask)
        max_d = float(np.max(dist))
        
        # Adaptive peak radius based on typical mango scale
        r_est = max(15.0, min(max_d, 60.0))
        footprint_rad = max(10, int(r_est * 0.35))
        
        local_max = (dist == ndi.maximum_filter(dist, footprint=np.ones((footprint_rad, footprint_rad), dtype=bool)))
        local_max = local_max & (dist > max_d * 0.25) & b_mask
        
        lbl_p, n_p = ndi.label(local_max)
        peak_points = []
        for p in range(1, n_p + 1):
            ys, xs = np.where(lbl_p == p)
            val = float(np.mean(dist[ys, xs]))
            peak_points.append((float(np.mean(xs)), float(np.mean(ys)), val, p))
            
        peak_points.sort(key=lambda x: x[2], reverse=True)
        min_peak_dist = max(20.0, r_est * 0.45)
        
        kept_markers = np.zeros(b_mask.shape, dtype=np.int32)
        kept_centers = []
        kept_count = 0
        for cx, cy, val, p in peak_points:
            too_close = False
            for kx, ky in kept_centers:
                if np.hypot(cx - kx, cy - ky) < min_peak_dist:
                    too_close = True
                    break
            if not too_close:
                kept_count += 1
                kept_centers.append((cx, cy))
                kept_markers[lbl_p == p] = kept_count

        print(f"Bunch {b_idx}: max_d={max_d:.1f}, candidate markers={kept_count}")
        total_instances += kept_count

    print(f"Total instances identified: {total_instances}")

if __name__ == "__main__":
    test_separated()
