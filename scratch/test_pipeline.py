import sys
sys.path.insert(0, '.')
from PIL import Image, ImageDraw
import numpy as np
from ml.inference.mango_quality_scanner import get_mango_quality_scanner

w, h = 600, 450
img = Image.new('RGB', (w, h), (235, 235, 235))
draw = ImageDraw.Draw(img)

# 3 TOUCHING mangoes:
# Mango 1: Ripe & Healthy (yellow)
# Mango 2: Ripe & Defective (yellow with dark anthracnose lesions)
# Mango 3: Unripe & Healthy (green)
draw.ellipse([80, 120, 240, 320], fill=(235, 185, 25))
draw.ellipse([210, 110, 370, 310], fill=(230, 180, 20))
draw.ellipse([340, 130, 500, 330], fill=(115, 185, 45))

# Draw black/brown necrotic anthracnose spots on Mango 2
draw.ellipse([270, 170, 310, 210], fill=(25, 20, 15))
draw.ellipse([290, 215, 335, 260], fill=(30, 25, 20))

scanner = get_mango_quality_scanner()
res = scanner.inspect_lot_image(img)
print("Detected mangoes:", res["mangoes_detected"])
print("Lot Visual Grade:", res["visual_grade"])
print("Lot Health: Healthy=", res["healthy_count"], "Defective=", res["defect_count"], "Uncertain=", res["uncertain_count"])
print("Ripeness Breakdown:", res["ripeness_summary"])
print("--- INDIVIDUAL MANGOES ---")
for d in res["detections"]:
    print(f"Mango #{d['sample_index']}: Status={d['health_status']} | Defect={d['defect_type']} | Ripeness={d['ripeness']} | Quality={d['quality_grade']} | Conf={d['confidence']}% | Affected={d['affected_area_pct']}%")
    print(f"   Evidence: {d['visual_evidence']}")
