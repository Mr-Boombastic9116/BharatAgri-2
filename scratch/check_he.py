import sys; sys.path.insert(0, '.')
from PIL import Image
from ml.inference.mango_quality_scanner import get_mango_quality_scanner
scanner = get_mango_quality_scanner()
for i in range(1, 11):
    p = f'ml/data/mango/extracted/MangoDHDS/Healthy/Healthy/He{i}.jpg'
    res = scanner.inspect_lot_image(Image.open(p))
    det = res['detections'][0]
    print(f"He{i}: detected={res['mangoes_detected']}, status={det['health_status']}, grade={det['quality_grade']}, defect_pct={det['visible_defect_pct']}")
