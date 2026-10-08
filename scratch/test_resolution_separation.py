import sys, os
sys.path.insert(0, os.path.abspath('.'))
from PIL import Image, ImageDraw
from ml.inference.mango_detector import MangoDetector

def test_sizes():
    detector = MangoDetector()
    for (w, h) in [(600, 450), (1200, 900)]:
        img = Image.new("RGB", (w, h), (235, 235, 235))
        draw = ImageDraw.Draw(img)
        scale = w / 600.0
        positions = [
            (int(80*scale), int(80*scale), int(220*scale), int(240*scale), (230, 190, 25)),
            (int(180*scale), int(70*scale), int(320*scale), int(230*scale), (220, 175, 20)),
            (int(280*scale), int(90*scale), int(420*scale), int(250*scale), (130, 195, 40)),
            (int(130*scale), int(200*scale), int(270*scale), int(360*scale), (215, 160, 30)),
            (int(240*scale), int(210*scale), int(380*scale), int(370*scale), (225, 185, 35)),
        ]
        for x1, y1, x2, y2, color in positions:
            draw.ellipse([x1, y1, x2, y2], fill=color)
        
        _, boxes = detector.detect_mangoes(img)
        print(f"Resolution {w}x{h} -> Detected {len(boxes)} mangoes")

if __name__ == "__main__":
    test_sizes()
