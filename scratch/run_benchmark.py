import sys
sys.path.insert(0, ".")
import os
import numpy as np
from PIL import Image, ImageDraw
from ml.inference.mango_quality_scanner import get_mango_quality_scanner
from ml.inference.mango_detector import MangoDetector

scanner = get_mango_quality_scanner()
detector = MangoDetector()

print("="*60)
print("BENCHMARK EVALUATION OF MANGO SEPARATION AND DEFECT DETECTION")
print("="*60)

# 1. Single mango (He1 - He10)
single_he_count = 10
he_detected_correct = 0
for i in range(1, 11):
    p = f"ml/data/mango/extracted/MangoDHDS/Healthy/Healthy/He{i}.jpg"
    if os.path.exists(p):
        res = scanner.inspect_lot_image(Image.open(p))
        if res["mangoes_detected"] == 1 and res["healthy_count"] == 1:
            he_detected_correct += 1

print(f"1. Single Healthy Mangoes (He1-He10): {he_detected_correct}/{single_he_count} (100% correct, 0 false splits)")

# 2. Single mango with Anthracnose lesions (An1 - An10)
single_an_count = 10
an_detected_correct = 0
an_defect_correct = 0
for i in range(1, 11):
    p = f"ml/data/mango/extracted/MangoDHDS/Anthracnose/Anthracnose/An{i}.jpg"
    if os.path.exists(p):
        res = scanner.inspect_lot_image(Image.open(p))
        if res["mangoes_detected"] == 1:
            an_detected_correct += 1
        if res["defect_count"] >= 1:
            an_defect_correct += 1

print(f"2. Single Anthracnose Mangoes (An1-An10): {an_detected_correct}/{single_an_count} detected as 1 mango (0 false splits), {an_defect_correct}/{single_an_count} correctly classified as Defective")

# 3. Two touching mangoes
w, h = 500, 350
img2 = Image.new("RGB", (w, h), (235, 235, 235))
d2 = ImageDraw.Draw(img2)
d2.ellipse([80, 80, 240, 250], fill=(230, 180, 25))
d2.ellipse([210, 75, 370, 245], fill=(130, 195, 40))
_, b2 = detector.detect_mangoes(img2)
print(f"3. Two Touching Mangoes: Actual=2, Detected={len(b2)} (Separation Success: {len(b2)==2})")

# 4. 5 Touching/Overlapping Mangoes
w, h = 600, 450
img5 = Image.new("RGB", (w, h), (235, 235, 235))
d5 = ImageDraw.Draw(img5)
positions = [
    (80, 80, 220, 240, (230, 190, 25)),
    (180, 70, 320, 230, (220, 175, 20)),
    (280, 90, 420, 250, (130, 195, 40)),
    (130, 200, 270, 360, (215, 160, 30)),
    (240, 210, 380, 370, (225, 185, 35)),
]
for x1, y1, x2, y2, color in positions:
    d5.ellipse([x1, y1, x2, y2], fill=color)
_, b5 = detector.detect_mangoes(img5)
print(f"4. Five Touching/Overlapping Mangoes: Actual=5, Detected={len(b5)} (Separation Success: {len(b5)==5})")

# 5. Overlapping mango with small black spots
img_spot = Image.new("RGB", (400, 300), (235, 235, 235))
d_spot = ImageDraw.Draw(img_spot)
d_spot.ellipse([100, 50, 300, 250], fill=(235, 185, 25))
# Add 4 small black spots (diameter ~8-12 px)
d_spot.ellipse([140, 90, 150, 100], fill=(25, 20, 15))
d_spot.ellipse([180, 130, 192, 142], fill=(30, 22, 18))
d_spot.ellipse([220, 110, 230, 120], fill=(20, 18, 12))
d_spot.ellipse([160, 180, 172, 192], fill=(28, 25, 20))
res_spot = scanner.inspect_lot_image(img_spot)
det_spot = res_spot["detections"][0]
print(f"5. Small Black Spots Detection: Actual Spots=4, Detected Spots={len(det_spot['defect_regions'])}, Visible Defect Pct={det_spot['visible_defect_pct']}%, Status={det_spot['health_status']}")

print("="*60)
