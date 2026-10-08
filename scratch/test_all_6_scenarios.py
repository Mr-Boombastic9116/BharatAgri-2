import sys
sys.path.insert(0, ".")
import os
from io import BytesIO
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.deps import get_current_user
from backend.app.models.user import User

test_user = User(user_id='test_admin', role='admin', centre_id=None, name='Test Admin')
app.dependency_overrides[get_current_user] = lambda: test_user

client = TestClient(app, raise_server_exceptions=True)
APPOINTMENT_ID = "PF-260918-0003"
WORKSPACE_ROOT = os.path.abspath(os.path.dirname(__file__) + "/..")

def verify_response(name, resp, expected_count=None, expect_defects=None):
    print(f"\n--- Scenario: {name} ---")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data["success"] is True
    
    count = data.get("count", data.get("mangoes_detected", 0))
    defects = data.get("defect_count", 0)
    healthy = data.get("healthy_count", 0)
    grade = data.get("visual_grade")
    
    print(f"HTTP: {resp.status_code} | Mango Count: {count} | Healthy: {healthy} | Defective: {defects} | Grade: {grade}")
    
    if expected_count is not None:
        assert count == expected_count, f"Expected count {expected_count}, got {count}"
        
    if expect_defects is not None:
        if expect_defects:
            assert defects >= 1, f"Expected defects >= 1, got {defects}"
        else:
            assert defects == 0, f"Expected defects == 0, got {defects}"

    # Verify per-mango detection fields and crop images
    detections = data.get("detections", [])
    assert len(detections) == count, f"Detections length {len(detections)} does not match count {count}"
    
    for idx, d in enumerate(detections, 1):
        assert "ripeness" in d, f"Missing ripeness in detection {idx}"
        assert "health_status" in d, f"Missing health_status in detection {idx}"
        assert "quality_grade" in d, f"Missing quality_grade in detection {idx}"
        assert "crop_url" in d, f"Missing crop_url in detection {idx}"
        
        crop_url = d["crop_url"]
        if crop_url:
            # Check crop exists on disk
            rel_path = crop_url.lstrip("/")
            local_path = os.path.join(WORKSPACE_ROOT, "backend", rel_path)
            if not os.path.exists(local_path):
                local_path = os.path.join(WORKSPACE_ROOT, rel_path)
            assert os.path.exists(local_path), f"Crop file missing on disk: {local_path}"
            
    print(f"PASS: {name} completed successfully. All crops verified on disk.")
    return data

# Test 1: One normal mango
with open("ml/data/mango/extracted/MangoDHDS/Healthy/Healthy/He1.jpg", "rb") as f:
    he1_bytes = f.read()
resp1 = client.post(
    "/api/procurement/quality/mango-scan",
    data={"appointment_id": APPOINTMENT_ID},
    files={"file": ("He1.jpg", he1_bytes, "image/jpeg")}
)
verify_response("1. One Normal Mango (He1.jpg)", resp1, expected_count=1, expect_defects=False)

# Test 2: Multiple separated mangoes (3 separated mangoes)
img_sep = Image.new("RGB", (600, 350), color=(235, 235, 235))
d_sep = ImageDraw.Draw(img_sep)
d_sep.ellipse([40, 80, 180, 260], fill=(235, 185, 25))
d_sep.ellipse([220, 80, 360, 260], fill=(130, 195, 40))
d_sep.ellipse([400, 80, 540, 260], fill=(225, 175, 30))
buf = BytesIO()
img_sep.save(buf, format="JPEG")
resp2 = client.post(
    "/api/procurement/quality/mango-scan",
    data={"appointment_id": APPOINTMENT_ID},
    files={"file": ("separated.jpg", buf.getvalue(), "image/jpeg")}
)
verify_response("2. Multiple Separated Mangoes", resp2, expected_count=3)

# Test 3: Touching mangoes (2 touching mangoes)
img_touch = Image.new("RGB", (500, 350), color=(235, 235, 235))
d_touch = ImageDraw.Draw(img_touch)
d_touch.ellipse([80, 80, 240, 250], fill=(230, 180, 25))
d_touch.ellipse([210, 75, 370, 245], fill=(130, 195, 40))
buf = BytesIO()
img_touch.save(buf, format="JPEG")
resp3 = client.post(
    "/api/procurement/quality/mango-scan",
    data={"appointment_id": APPOINTMENT_ID},
    files={"file": ("touching.jpg", buf.getvalue(), "image/jpeg")}
)
verify_response("3. Touching Mangoes", resp3, expected_count=2)

# Test 4: Image with NO detectable mango (textured cool/blue background)
img_none = Image.new("RGB", (400, 300), color=(100, 140, 180))
d_none = ImageDraw.Draw(img_none)
for y in range(0, 300, 10):
    d_none.line([(0, y), (400, y)], fill=(80, 120, 160), width=2)
for x in range(0, 400, 15):
    d_none.line([(x, 0), (x, 300)], fill=(70, 110, 150), width=1)
buf = BytesIO()
img_none.save(buf, format="JPEG")
resp4 = client.post(
    "/api/procurement/quality/mango-scan",
    data={"appointment_id": APPOINTMENT_ID},
    files={"file": ("no_mango.jpg", buf.getvalue(), "image/jpeg")}
)
data4 = verify_response("4. Image with NO Detectable Mango", resp4, expected_count=0)
assert "No mangoes detected" in data4["message"] or data4["count"] == 0

# Test 5: Mango with black spots (An1.jpg)
with open("ml/data/mango/extracted/MangoDHDS/Anthracnose/Anthracnose/An1.jpg", "rb") as f:
    an1_bytes = f.read()
resp5 = client.post(
    "/api/procurement/quality/mango-scan",
    data={"appointment_id": APPOINTMENT_ID},
    files={"file": ("An1.jpg", an1_bytes, "image/jpeg")}
)
verify_response("5. Mango with Black Spots (An1.jpg)", resp5, expected_count=1, expect_defects=True)

# Test 6: Image containing no black spots (He2.jpg)
with open("ml/data/mango/extracted/MangoDHDS/Healthy/Healthy/He2.jpg", "rb") as f:
    he2_bytes = f.read()
resp6 = client.post(
    "/api/procurement/quality/mango-scan",
    data={"appointment_id": APPOINTMENT_ID},
    files={"file": ("He2.jpg", he2_bytes, "image/jpeg")}
)
verify_response("6. Image Containing NO Black Spots (He2.jpg)", resp6, expected_count=1, expect_defects=False)

print("\n" + "="*60)
print("ALL 6 TEST SCENARIOS PASSED WITH ZERO ERRORS!")
print("="*60)
