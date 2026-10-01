import httpx
import io

BASE_URL = "http://localhost:5000"

with httpx.Client(timeout=10.0) as client:
    # 1. Login as centre
    login_res = client.post(f"{BASE_URL}/api/auth/login", json={
        "user_id": "centre@bharatagri.demo",
        "password": "BharatAgri@2026"
    })
    token = login_res.json()["access_token"]
    centre_headers = {"Authorization": f"Bearer {token}"}

    # 2. Get a booking belonging to this centre (CENTRE-GOA-01)
    bks = client.get(f"{BASE_URL}/api/bookings/centre/CENTRE-GOA-01").json()
    assert len(bks) > 0, "No bookings found for centre"
    target_bk = bks[0]
    booking_id = target_bk["id"]
    print(f"Target booking for evidence: ID={booking_id}, Appt={target_bk.get('appointment_id')}")

    # 3. Create dummy image bytes (1x1 PNG)
    png_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xa75\x81\x84\x00\x00\x00\x00IEND\xaeB`\x82'

    # Test QUALITY evidence upload
    files = {"file": ("quality_sample.png", io.BytesIO(png_bytes), "image/png")}
    data = {
        "booking_id": str(booking_id),
        "evidence_type": "QUALITY",
        "notes": "FAQ Grade A inspection photo"
    }
    up_res = client.post(f"{BASE_URL}/api/procurement/evidence/upload", headers=centre_headers, data=data, files=files)
    print(f"Quality upload response: Status={up_res.status_code}, Res={up_res.json()}")
    assert up_res.status_code == 200
    assert up_res.json().get("success") is True

    # Test WEIGHING evidence upload
    files2 = {"file": ("weigh_scale.png", io.BytesIO(png_bytes), "image/png")}
    data2 = {
        "booking_id": str(booking_id),
        "evidence_type": "WEIGHING",
        "notes": "Certified scale reading display"
    }
    up_res2 = client.post(f"{BASE_URL}/api/procurement/evidence/upload", headers=centre_headers, data=data2, files=files2)
    print(f"Weighing upload response: Status={up_res2.status_code}, Res={up_res2.json()}")
    assert up_res2.status_code == 200
    assert up_res2.json().get("success") is True

    # Test MOISTURE evidence upload
    files3 = {"file": ("moisture_meter.png", io.BytesIO(png_bytes), "image/png")}
    data3 = {
        "booking_id": str(booking_id),
        "evidence_type": "MOISTURE",
        "notes": "Moisture meter 11.8% display"
    }
    up_res3 = client.post(f"{BASE_URL}/api/procurement/evidence/upload", headers=centre_headers, data=data3, files=files3)
    print(f"Moisture upload response: Status={up_res3.status_code}, Res={up_res3.json()}")
    assert up_res3.status_code == 200
    assert up_res3.json().get("success") is True

    # 4. Fetch evidence for this booking
    get_res = client.get(f"{BASE_URL}/api/procurement/evidence/{booking_id}", headers=centre_headers)
    print(f"Get evidence response: Status={get_res.status_code}, Total={get_res.json().get('total')}")
    assert get_res.status_code == 200
    by_type = get_res.json().get("by_type", {})
    assert len(by_type.get("QUALITY", [])) >= 1
    assert len(by_type.get("WEIGHING", [])) >= 1
    assert len(by_type.get("MOISTURE", [])) >= 1
    print("ALL THREE EVIDENCE CATEGORIES SAVED AND RETRIEVED SUCCESSFULLY!")
