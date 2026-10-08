import numpy as np
from PIL import Image, ImageDraw, ImageFont
import scipy.ndimage as ndi

def generate_debug_visuals(orig_img, peel_mask, markers, segmented_instances, detections):
    """
    Generate the 5 requested DEBUG mode visualization images:
    1. original image
    2. initial combined mango mask
    3. proposed separation boundaries
    4. final individual masks
    5. final Mango #1, #2, #3... crops
    """
    w, h = orig_img.size
    
    # 1. Original Image
    debug_1 = orig_img.copy()
    
    # 2. Combined Mango Mask (white silhouette on dark navy background)
    debug_2 = Image.new("RGB", (w, h), (15, 23, 42))
    peel_rgb = np.zeros((h, w, 3), dtype=np.uint8)
    peel_rgb[peel_mask] = [251, 191, 36]  # Amber yellow for mango peel
    debug_2_img = Image.fromarray(peel_rgb)
    debug_2 = Image.blend(debug_2, debug_2_img, 0.9)
    d2 = ImageDraw.Draw(debug_2)
    d2.text((12, 12), "DEBUG 2: Initial Combined Mango Peel Mask", fill=(255, 255, 255))
    
    # 3. Proposed Separation Boundaries & Distance Peaks
    debug_3 = orig_img.copy().convert("RGBA")
    overlay_3 = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d3 = ImageDraw.Draw(overlay_3)
    
    # Draw partition boundaries where neighboring labels meet
    gx = ndi.sobel(segmented_instances, axis=1)
    gy = ndi.sobel(segmented_instances, axis=0)
    boundaries = (np.hypot(gx, gy) > 0) & (segmented_instances > 0)
    b_ys, b_xs = np.where(boundaries)
    for bx, by in zip(b_xs, b_ys):
        d3.rectangle([bx-1, by-1, bx+1, by+1], fill=(239, 68, 68, 220)) # Red crease lines
        
    # Draw detected centroid peaks
    for det in detections:
        cx, cy = det.get('centroid', (0, 0))
        d3.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=(59, 130, 246, 230), outline=(255, 255, 255, 255), width=2)
        d3.text((cx + 10, cy - 10), f"Center #{det['index']}", fill=(255, 255, 255, 255))
        
    debug_3 = Image.alpha_composite(debug_3, overlay_3).convert("RGB")
    d3_draw = ImageDraw.Draw(debug_3)
    d3_draw.text((12, 12), "DEBUG 3: Proposed Separation Boundaries & Centroid Seeds", fill=(255, 255, 255))

    # 4. Final Individual Masks (Color-coded instance map)
    palette = [
        (16, 185, 129),   # Emerald Green
        (245, 158, 11),   # Amber
        (59, 130, 246),   # Sky Blue
        (236, 72, 153),   # Pink
        (139, 92, 246),   # Violet
        (20, 184, 166),   # Teal
        (249, 115, 22),   # Orange
    ]
    debug_4_arr = np.zeros((h, w, 3), dtype=np.uint8)
    for idx, det in enumerate(detections):
        inst_m = det.get('mask')
        if inst_m is not None:
            color = palette[idx % len(palette)]
            debug_4_arr[inst_m] = color
    debug_4 = Image.fromarray(debug_4_arr)
    d4 = ImageDraw.Draw(debug_4)
    d4.text((12, 12), f"DEBUG 4: Final Individual Instance Masks ({len(detections)} Mangoes)", fill=(255, 255, 255))

    # 5. Final Mango #1, #2, #3... Crops Montage
    num_crops = len(detections)
    crop_size = 180
    montage_w = max(crop_size * num_crops + 20 * (num_crops + 1), 320)
    montage_h = crop_size + 60
    debug_5 = Image.new("RGB", (montage_w, montage_h), (241, 245, 249))
    d5 = ImageDraw.Draw(debug_5)
    d5.text((15, 10), "DEBUG 5: Final Individual Segmented Mango Crops", fill=(15, 23, 42))
    
    cur_x = 20
    for det in detections:
        c_img = det['crop'].copy().resize((crop_size, crop_size), Image.Resampling.BILINEAR)
        debug_5.paste(c_img, (cur_x, 35))
        d5.rectangle([cur_x, 35, cur_x + crop_size, 35 + crop_size], outline=(203, 213, 225), width=2)
        d5.text((cur_x + 6, 35 + crop_size + 4), f"Mango #{det['index']} ({int(det['area'])} px)", fill=(30, 41, 59))
        cur_x += crop_size + 20

    return {
        "debug_1_original": debug_1,
        "debug_2_peel_mask": debug_2,
        "debug_3_separation_boundaries": debug_3,
        "debug_4_instance_masks": debug_4,
        "debug_5_crops_montage": debug_5
    }

print("Debug visuals helper defined successfully.")
