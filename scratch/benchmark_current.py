import os
import sys
sys.path.insert(0, os.path.abspath('.'))
from PIL import Image
from ml.inference.mango_quality_scanner import get_mango_quality_scanner

scanner = get_mango_quality_scanner()
print("--- TESTING ANTHRACNOSE IMAGES ---")
anthra_dir = os.path.join('ml', 'data', 'mango', 'extracted', 'MangoDHDS', 'Anthracnose', 'Anthracnose')
for fname in ['An1.jpg', 'An2.jpg', 'An3.jpg', 'An5.jpg', 'An10.jpg', 'An15.jpg', 'An20.jpg']:
    p = os.path.join(anthra_dir, fname)
    if os.path.exists(p):
        img = Image.open(p)
        res = scanner.inspect_lot_image(img)
        d0 = res['detections'][0]
        print(f"{fname}: detected={res['mangoes_detected']}, health={d0['health_status']}, defect_type={d0['defect_type']}, affected%={d0['visible_defect_pct']}, defect_boxes={len(d0['defect_regions'])}, decision={d0['visual_evidence']}")

print("\n--- TESTING HEALTHY IMAGES ---")
healthy_dir = os.path.join('ml', 'data', 'mango', 'extracted', 'MangoDHDS', 'Healthy', 'Healthy')
for fname in ['He1.jpg', 'He2.jpg', 'He3.jpg', 'He5.jpg', 'He10.jpg']:
    p = os.path.join(healthy_dir, fname)
    if os.path.exists(p):
        img = Image.open(p)
        res = scanner.inspect_lot_image(img)
        d0 = res['detections'][0]
        print(f"{fname}: detected={res['mangoes_detected']}, health={d0['health_status']}, affected%={d0['visible_defect_pct']}, defect_boxes={len(d0['defect_regions'])}")
