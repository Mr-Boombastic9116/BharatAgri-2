import sys, os
sys.path.insert(0, os.path.abspath('.'))
import time
import numpy as np
from PIL import Image, ImageDraw
from ml.inference.mango_detector import MangoDetector
from ml.inference.mango_quality_scanner import get_mango_quality_scanner

def profile_scanner():
    print("=== PROFILING MANGO AI PIPELINE ===")
    
    # 1. Image generation/loading
    t0 = time.perf_counter()
    w, h = 1200, 900
    img = Image.new("RGB", (w, h), (235, 235, 235))
    draw = ImageDraw.Draw(img)
    # 5 touching mangoes bunch
    positions = [
        (160, 160, 440, 480, (230, 190, 25)),
        (360, 140, 640, 460, (220, 175, 20)),
        (560, 180, 840, 500, (130, 195, 40)),
        (260, 400, 540, 720, (215, 160, 30)),
        (480, 420, 760, 740, (225, 185, 35)),
    ]
    for x1, y1, x2, y2, color in positions:
        draw.ellipse([x1, y1, x2, y2], fill=color)
    t_load = (time.perf_counter() - t0) * 1000

    # 2. Scanner initialization (Model loading once)
    t0 = time.perf_counter()
    scanner = get_mango_quality_scanner()
    t_init = (time.perf_counter() - t0) * 1000

    # 3. Detection & segmentation
    t0 = time.perf_counter()
    detector = scanner.detector
    validated_img = detector.validate_image(img)
    t_val = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    orig_img, boxes = detector.detect_mangoes(img)
    t_detect = (time.perf_counter() - t0) * 1000

    # 4. End-to-end full lot inspection
    t0 = time.perf_counter()
    res = scanner.inspect_lot_image(img)
    t_full = (time.perf_counter() - t0) * 1000

    print(f"Image Load/Prep:        {t_load:.2f} ms")
    print(f"Scanner Get/Init:       {t_init:.2f} ms")
    print(f"Image Validation:       {t_val:.2f} ms")
    print(f"Detection & Watershed:  {t_detect:.2f} ms")
    print(f"Full Lot Pipeline:      {t_full:.2f} ms")
    print(f"Detections count:       {len(boxes)}")
    print(f"Lot result:             {res.get('lot_status')}, {res.get('mangoes_detected')} fruits")

if __name__ == "__main__":
    profile_scanner()
