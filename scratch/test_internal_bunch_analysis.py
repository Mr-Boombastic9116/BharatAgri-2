import sys, os
sys.path.insert(0, os.path.abspath('.'))
from PIL import Image, ImageDraw
import numpy as np
import scipy.ndimage as ndi

def test_internal_analysis():
    w, h = 1200, 900
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

    scale_img = min(1.0, 640.0 / max(w, h))
    sw = max(50, int(w * scale_img))
    sh = max(50, int(h * scale_img))
    img_small = img.resize((sw, sh), Image.Resampling.BILINEAR)
    rgb_np = np.array(img_small, dtype=np.float32)
    r, g, b = rgb_np[..., 0], rgb_np[..., 1], rgb_np[..., 2]
    l_est = 0.299 * r + 0.587 * g + 0.114 * b
    a_est = (r - g) * 0.7 + 128.0
    b_est = (r + g - 2.0 * b) * 0.4 + 128.0
    chroma = np.hypot(a_est - 128.0, b_est - 128.0)

    # 1. Peel mask
    is_yellow = (r > b * 1.10) & (g > b * 0.92) & (b_est > 128.0) & (l_est > 35.0) & (l_est < 248.0)
    is_green = (g > r * 0.90) & (g > b * 1.02) & (chroma > 8.0) & (l_est > 30.0) & (l_est < 245.0)
    is_breaking = (r > b * 1.04) & (g > b * 0.96) & (chroma > 10.0) & (l_est > 35.0) & (l_est < 248.0)
    peel_raw = is_yellow | is_green | is_breaking
    peel_clean = ndi.binary_closing(peel_raw, structure=np.ones((7, 7), dtype=bool))
    peel_clean = ndi.binary_fill_holes(peel_clean)

    # 2. Multi-channel internal boundary gradients
    # Gradients in Luminance (L*), a*, b*
    gx_l = ndi.sobel(l_est, axis=1)
    gy_l = ndi.sobel(l_est, axis=0)
    grad_l = np.hypot(gx_l, gy_l)

    gx_a = ndi.sobel(a_est, axis=1)
    gy_a = ndi.sobel(a_est, axis=0)
    grad_a = np.hypot(gx_a, gy_a)

    gx_b = ndi.sobel(b_est, axis=1)
    gy_b = ndi.sobel(b_est, axis=0)
    grad_b = np.hypot(gx_b, gy_b)

    total_grad = grad_l + 0.8 * (grad_a + grad_b)

    # Internal edges/boundaries inside the bunch
    peel_grads = total_grad[peel_clean]
    # Edge threshold: boundaries between touching mangoes have prominent gradient
    p70 = np.percentile(peel_grads, 70) if len(peel_grads) > 0 else 20.0
    internal_seams = (total_grad > max(15.0, float(p70))) & peel_clean

    # Thin & filter seams
    seams_dil = ndi.binary_dilation(internal_seams, structure=np.ones((3, 3), dtype=bool))

    # Mask with internal seams removed
    partitioned_peel = peel_clean & (~seams_dil)
    partitioned_peel = ndi.binary_opening(partitioned_peel, structure=np.ones((3, 3), dtype=bool))

    # Compute distance transform on partitioned peel
    dist_part = ndi.distance_transform_edt(partitioned_peel)

    # Peaks of distance transform inside the partitioned cores
    fp = 11
    local_max = (dist_part == ndi.maximum_filter(dist_part, footprint=np.ones((fp, fp), dtype=bool)))
    local_max = local_max & (dist_part >= 10.0) & partitioned_peel
    lbl_m, n_m = ndi.label(local_max)

    print(f"Internal analysis found {n_m} marker cores!")
    for m in range(1, n_m + 1):
        ys, xs = np.where(lbl_m == m)
        print(f"  Marker {m}: center=({int(np.mean(xs))}, {int(np.mean(ys))}), val={np.mean(dist_part[ys, xs]):.1f}")

if __name__ == "__main__":
    test_internal_analysis()
