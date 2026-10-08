import sys, os
sys.path.insert(0, os.path.abspath('.'))
from PIL import Image, ImageDraw
from ml.inference.mango_detector import MangoDetector

detector = MangoDetector()
w, h = 600, 450
img = Image.new("RGB", (w, h), (235, 235, 235))
draw = ImageDraw.Draw(img)
positions = [
    (80, 80, 220, 240, (230, 190, 25)),
    (180, 70, 320, 230, (220, 175, 20)),
    (280, 90, 420, 250, (130, 195, 40)),
    (130, 200, 270, 360, (215, 160, 30)),
    (240, 210, 380, 370, (225, 185, 35)),
]
for x1, y1, x2, y2, color in positions:
    draw.ellipse([x1, y1, x2, y2], fill=color)

_, boxes = detector.detect_mangoes(img)
print(f"600x450 Current detector: {len(boxes)} boxes")
for b in boxes:
    print(b['index'], b['box'], b['area'])
