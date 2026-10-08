import numpy as np
from PIL import Image, ImageDraw, ImageFont
import scipy.ndimage as ndi
from scipy.spatial import ConvexHull

def extract_contour_points(mask):
    """Extract outer contour (x, y) coordinates of a binary mask."""
    # Find boundary pixels: mask & (~eroded_mask)
    eroded = ndi.binary_erosion(mask, structure=np.ones((3, 3), dtype=bool))
    boundary = mask & (~eroded)
    ys, xs = np.where(boundary)
    if len(xs) == 0:
        return []
    # Sample up to 100 contour points sorted by angle from centroid
    cx, cy = np.mean(xs), np.mean(ys)
    angles = np.arctan2(ys - cy, xs - cx)
    order = np.argsort(angles)
    step = max(1, len(order) // 80)
    sampled = [(int(xs[idx]), int(ys[idx])) for idx in order[::step]]
    return sampled

def test_contour():
    m = np.zeros((100, 100), dtype=bool)
    m[20:80, 20:80] = True
    pts = extract_contour_points(m)
    print("Contour points count:", len(pts), pts[:4])

test_contour()
