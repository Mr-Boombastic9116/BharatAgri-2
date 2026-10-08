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

# Scale proxy
max_dim = 640
scale_img = min(1.0, max_dim / max(w, h))
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

gx = ndi.sobel(l_est, axis=1)
gy = ndi.sobel(l_est, axis=0)
grad = np.hypot(gx, gy)
peel_grads = grad[peel_clean]
p85 = np.percentile(peel_grads, 85)
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
print(f"1200x900: sw={sw}, sh={sh}, edge_thresh={edge_thresh:.1f}, n_e={n_e}, clean_creases={np.sum(clean_creases)}")
print(f"1200x900: n_cores={n_cores}, sizes={sizes}")
if n_cores > 0 and len(sizes) > 0:
    dom_size = float(np.max(sizes))
    min_core_thresh = max(350.0, dom_size * 0.18)
    valid_count = sum(1 for s in sizes if s >= min_core_thresh)
    print(f"1200x900: dom_size={dom_size}, min_core_thresh={min_core_thresh}, valid_count={valid_count}")
