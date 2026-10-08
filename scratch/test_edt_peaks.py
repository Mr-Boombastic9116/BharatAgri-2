import sys, os
sys.path.insert(0, os.path.abspath('.'))
from PIL import Image, ImageDraw
import numpy as np
import scipy.ndimage as ndi

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

is_yellow = (r > b * 1.10) & (g > b * 0.92) & (b_est > 128.0) & (l_est > 35.0) & (l_est < 248.0)
is_green = (g > r * 0.90) & (g > b * 1.02) & (chroma > 8.0) & (l_est > 30.0) & (l_est < 245.0)
is_breaking = (r > b * 1.04) & (g > b * 0.96) & (chroma > 10.0) & (l_est > 35.0) & (l_est < 248.0)
peel_raw = is_yellow | is_green | is_breaking
peel_clean = ndi.binary_closing(peel_raw, structure=np.ones((7, 7), dtype=bool))
peel_clean = ndi.binary_fill_holes(peel_clean)

# Compute EDT
dist = ndi.distance_transform_edt(peel_clean)
max_d = float(np.max(dist))
print("Max distance transform:", max_d)

# For various footprint sizes:
for fp in [15, 21, 25, 31, 35, 41]:
    local_max = (dist == ndi.maximum_filter(dist, footprint=np.ones((fp, fp), dtype=bool)))
    local_max = local_max & (dist > 15.0) & peel_clean
    lbl, n_peaks = ndi.label(local_max)
    print(f"Footprint {fp}x{fp}: n_peaks={n_peaks}")
    if n_peaks > 0:
        for p in range(1, n_peaks + 1):
            ys, xs = np.where(lbl == p)
            print(f"   Peak {p}: center=({int(np.mean(xs))}, {int(np.mean(ys))}), val={np.mean(dist[ys, xs]):.1f}")
