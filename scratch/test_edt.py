import numpy as np
from PIL import Image, ImageDraw
import scipy.ndimage as ndi

def analyze_edt(mask):
    """Analyze distance transform peaks on a binary mask."""
    dist = ndi.distance_transform_edt(mask)
    max_dist = np.max(dist)
    if max_dist < 5:
        return dist, []

    # Dynamic local maxima with minimum peak distance based on max_dist
    min_dist_filter = max(15, int(max_dist * 0.45))
    footprint = np.ones((min_dist_filter, min_dist_filter), dtype=bool)
    local_max = (dist == ndi.maximum_filter(dist, footprint=footprint)) & (dist > max_dist * 0.35)
    
    labeled_peaks, num_peaks = ndi.label(local_max)
    centers = []
    for i in range(1, num_peaks + 1):
        ys, xs = np.where(labeled_peaks == i)
        cy = int(np.mean(ys))
        cx = int(np.mean(xs))
        d_val = dist[cy, cx]
        centers.append((cx, cy, d_val))
    return dist, centers

# Test 1: Single mango An5.jpg
im = Image.open('ml/data/mango/extracted/MangoDHDS/Anthracnose/Anthracnose/An5.jpg')
arr = np.array(im, dtype=np.float32)
r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
peel = ((r > b * 1.1) & (g > b * 0.95)) | ((g > r * 0.95) & (g > b * 1.05))
peel = ndi.binary_fill_holes(ndi.binary_closing(peel, structure=np.ones((7, 7), dtype=bool)))
dist, centers = analyze_edt(peel)
print("An5.jpg peaks:", len(centers), centers)

# Test 2: Synthetic 5 touching mangoes
w, h = 600, 450
img_synth = Image.new("L", (w, h), 0)
draw = ImageDraw.Draw(img_synth)
positions = [
    (80, 80, 220, 240),
    (180, 70, 320, 230),
    (280, 90, 420, 250),
    (130, 200, 270, 360),
    (240, 210, 380, 370),
]
for x1, y1, x2, y2 in positions:
    draw.ellipse([x1, y1, x2, y2], fill=255)
mask_synth = np.array(img_synth) > 128
dist_s, centers_s = analyze_edt(mask_synth)
print("Synthetic 5 mangoes peaks:", len(centers_s), centers_s)
