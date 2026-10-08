import sys
sys.path.insert(0, ".")
from PIL import Image
from ml.inference.mango_quality_scanner import get_mango_quality_scanner

scanner = get_mango_quality_scanner()
for fname in ['An1.jpg', 'An5.jpg', 'He1.jpg']:
    sub = "Anthracnose/Anthracnose" if fname.startswith("An") else "Healthy/Healthy"
    path = f"ml/data/mango/extracted/MangoDHDS/{sub}/{fname}"
    img = Image.open(path)
    res = scanner.inspect_lot_image(img)
    det = res["detections"][0]
    print(f"{fname}: detected={res['mangoes_detected']}, healthy={res['healthy_count']}, defect={res['defect_count']}, status={det['health_status']}, grade={det['quality_grade']}, defect_pct={det['visible_defect_pct']}, spots={len(det['defect_regions'])}")
