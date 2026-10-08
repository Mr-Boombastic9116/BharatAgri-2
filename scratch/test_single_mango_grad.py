import sys, os
sys.path.insert(0, os.path.abspath('.'))
from PIL import Image, ImageDraw
import numpy as np
import scipy.ndimage as ndi

def test_single_mango():
    w, h = 400, 300
    img = Image.new("RGB", (w, h), (240, 240, 240))
    draw = ImageDraw.Draw(img)
    draw.ellipse([100, 60, 300, 240], fill=(230, 180, 25))

    rgb_np = np.array(img, dtype=np.float32)
    r, g, b = rgb_np[..., 0], rgb_np[..., 1], rgb_np[..., 2]
    l_est = 0.299 * r + 0.587 * g + 0.114 * b
    a_est = (r - g) * 0.7 + 128.0
    b_est = (r + g - 2.0 * b) * 0.4 + 128.0
    chroma = np.hypot(a_est - 128.0, b_est - 128.0)

    is_yellow = (r > b * 1.10) & (g > b * 0.92) & (b_est > 128.0) & (l_est > 35.0) & (l_est < 248.0)
    peel_clean = ndi.binary_closing(is_yellow, structure=np.ones((7, 7), dtype=bool))
    peel_clean = ndi.binary_fill_holes(peel_clean)

    # Gradients
    gx_l = ndi.sobel(l_est, axis=1)
    gy_l = ndi.sobel(l_est, axis=0)
    grad_l = np.hypot(gx_l, gy_l)

    # Internal gradient: for a single mango, internal gradient is smooth/flat
    peel_grads = grad_l[peel_clean]
    # Check if there are internal seams
    # Erode peel to inspect interior
    inner_peel = ndi.binary_erosion(peel_clean, structure=np.ones((7, 7), dtype=bool))
    inner_grads = grad_l[inner_peel] if np.sum(inner_peel) > 0 else []
    max_inner_grad = float(np.max(inner_grads)) if len(inner_grads) > 0 else 0.0
    mean_inner_grad = float(np.mean(inner_grads)) if len(inner_grads) > 0 else 0.0

    print(f"Single Mango: max_inner_grad={max_inner_grad:.1f}, mean_inner_grad={mean_inner_grad:.1f}")

if __name__ == "__main__":
    test_single_mango()
