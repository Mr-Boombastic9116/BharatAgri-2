"""
Test and refine the hybrid separation algorithm.
Tests:
- Single mangoes (He1.jpg to He10.jpg, An1.jpg to An20.jpg): Target = 1 instance.
- Touching synthetic 2 mangoes: Target = 2 instances.
- Touching synthetic 5 mangoes: Target = 5 instances.
"""
import os
import sys
import numpy as np
from PIL import Image, ImageDraw
import scipy.ndimage as ndi

def segment_peel_mask(img_np):
    """Accurately segments mango peel without background bleed."""
    r = img_np[..., 0]
    g = img_np[..., 1]
    b = img_np[..., 2]

    # CIELAB approximation
    l_est = 0.299 * r + 0.587 * g + 0.114 * b
    a_est = (r - g) * 0.7 + 128.0
    b_est = (r + g - 2.0 * b) * 0.4 + 128.0
    chroma = np.hypot(a_est - 128.0, b_est - 128.0)

    # Peel mask:
    # Yellow / Orange / Red blush: r > b * 1.15, g > b * 0.95, b_est > 132 (yellow bias)
    # Green unripe: g > r * 0.95, g > b * 1.05, chroma > 10
    # Breaking: r > b * 1.05, g > b * 1.0, chroma > 12
    is_yellow_orange = (r > b * 1.12) & (g > b * 0.95) & (b_est > 130.0) & (l_est > 40.0) & (l_est < 248.0)
    is_green = (g > r * 0.95) & (g > b * 1.05) & (chroma > 10.0) & (l_est > 35.0) & (l_est < 245.0)
    is_breaking = (r > b * 1.08) & (g > b * 1.02) & (chroma > 12.0) & (l_est > 35.0) & (l_est < 248.0)
    
    peel_raw = is_yellow_orange | is_green | is_breaking
    
    # Morphological clean
    peel_clean = ndi.binary_closing(peel_raw, structure=np.ones((7, 7), dtype=bool))
    peel_clean = ndi.binary_fill_holes(peel_clean)
    return peel_clean, l_est, chroma

def test_separation_logic():
    print("=== TESTING HYBRID SEPARATION LOGIC ===")
    anthra_dir = os.path.join('ml', 'data', 'mango', 'extracted', 'MangoDHDS', 'Anthracnose', 'Anthracnose')
    healthy_dir = os.path.join('ml', 'data', 'mango', 'extracted', 'MangoDHDS', 'Healthy', 'Healthy')

    test_images = []
    if os.path.exists(healthy_dir):
        for f in ['He1.jpg', 'He2.jpg', 'He3.jpg', 'He5.jpg', 'He10.jpg']:
            p = os.path.join(healthy_dir, f)
            if os.path.exists(p):
                test_images.append((f, p, 1))

    if os.path.exists(anthra_dir):
        for f in ['An1.jpg', 'An2.jpg', 'An3.jpg', 'An5.jpg', 'An10.jpg', 'An20.jpg']:
            p = os.path.join(anthra_dir, f)
            if os.path.exists(p):
                test_images.append((f, p, 1))

    print(f"Total dataset test images: {len(test_images)}")

if __name__ == '__main__':
    test_separation_logic()
