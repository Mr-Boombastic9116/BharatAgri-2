import httpx
import io
import sys

BASE_URL = "http://localhost:5000"

def test_qr_and_evidence():
    # 1. Login as centre user
    login_resp = httpx.post(f"{BASE_URL}/api/auth/login", json={
        "username": "centre@bharatagri.demo",
        "password": "Password@123"
    })
    assert login_resp.status_code == 200, f"Centre login failed: {login_resp.text}"
    token_data = login_resp.json()
    token = token_data.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    print("[1] Centre login OK. Token acquired.")

    # 2. Get Centre Bookings
    bookings_resp = httpx.get(f"{BASE_URL}/api/bookings/centre/CENTRE-GOA-01", headers=headers)
    assert bookings_resp.status_code == 200, f"Fetch bookings failed: {bookings_resp.text}"
    b_data = bookings_resp.json()
    bookings = b_data.get("bookings", [])
    print(f"[2] Fetched {len(bookings)} bookings for CENTRE-GOA-01.")
    assert len(bookings) > 0, "No bookings found for CENTRE-GOA-01"
    
    # Pick a booking
    sample_booking = bookings[0]
    booking_id = sample_booking["id"]
    qr_token = sample_booking.get("qr_token") or sample_booking.get("appointment_id")
    print(f"    Sample booking ID: {booking_id}, appointment_id: {sample_booking.get('appointment_id')}, qr_token: {qr_token}")

    # 3. Test QR Verification - Valid
    verify_resp = httpx.post(f"{BASE_URL}/api/appointments/verify", json={
        "qr_token": qr_token,
        "centre_id": "CENTRE-GOA-01"
    }, headers=headers)
    print(f"[3] QR verify response (status {verify_resp.status_code}): {verify_resp.json().get('code')} - {verify_resp.json().get('message')}")
    assert verify_resp.json().get("code") in ["SUCCESS", "ALREADY_PROCESSED"], "QR verify unexpected result"

    # 4. Test QR Verification - Invalid QR
    invalid_resp = httpx.post(f"{BASE_URL}/api/appointments/verify", json={
        "qr_token": "TOTALLY_INVALID_QR_CODE_12345",
        "centre_id": "CENTRE-GOA-01"
    }, headers=headers)
    assert invalid_resp.json().get("code") == "INVALID_QR", f"Expected INVALID_QR, got {invalid_resp.text}"
    print(f"[4] Invalid QR correctly rejected: {invalid_resp.json().get('code')}")

    # 5. Test QR Verification - Cross Centre Check
    # CENTRE-MH-01 verifying CENTRE-GOA-01's booking
    cross_resp = httpx.post(f"{BASE_URL}/api/appointments/verify", json={
        "qr_token": qr_token,
        "centre_id": "CENTRE-MH-01"
    }, headers=headers)
    cross_code = cross_resp.json().get("code")
    print(f"[5] Cross-centre scan response code: {cross_code}")
    assert cross_code in ["WRONG_CENTRE", "UNAUTHORIZED_CENTRE"], f"Expected wrong/unauthorized centre, got {cross_resp.text}"

    # 6. Test Photo Evidence Uploads for all 3 categories: QUALITY, WEIGHING, MOISTURE
    dummy_image = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9"

    for ev_type in ["QUALITY", "WEIGHING", "MOISTURE"]:
        files = {
            "file": (f"test_{ev_type.lower()}.jpg", io.BytesIO(dummy_image), "image/jpeg")
        }
        data = {
            "booking_id": booking_id,
            "evidence_type": ev_type,
            "notes": f"Verification photo for {ev_type} check"
        }
        up_resp = httpx.post(f"{BASE_URL}/api/procurement/evidence/upload", files=files, data=data, headers=headers)
        assert up_resp.status_code == 200, f"Upload {ev_type} failed: {up_resp.text}"
        res_data = up_resp.json()
        assert res_data.get("success") is True, f"Upload unsuccessful: {res_data}"
        print(f"[6.{ev_type}] Uploaded {ev_type} evidence: {res_data.get('evidence', {}).get('file_path')}")

    # 7. Test Retrieval of Uploaded Evidence
    ev_get = httpx.get(f"{BASE_URL}/api/procurement/evidence/{booking_id}", headers=headers)
    assert ev_get.status_code == 200, f"Fetch evidence failed: {ev_get.text}"
    ev_json = ev_get.json()
    assert ev_json.get("total") >= 3, f"Expected at least 3 evidence items, got {ev_json.get('total')}"
    assert len(ev_json.get("by_type", {}).get("QUALITY", [])) > 0
    assert len(ev_json.get("by_type", {}).get("WEIGHING", [])) > 0
    assert len(ev_json.get("by_type", {}).get("MOISTURE", [])) > 0
    print(f"[7] Evidence retrieved successfully: total = {ev_json.get('total')}")

    # 8. Test Static File Serving
    first_path = ev_json["evidence"][0]["file_path"]
    img_resp = httpx.get(f"{BASE_URL}{first_path}")
    assert img_resp.status_code == 200, f"Static image serving failed at {first_path}: {img_resp.status_code}"
    print(f"[8] Static file serving verified for {first_path} (length: {len(img_resp.content)} bytes)")

    print("\nALL BACKEND API VERIFICATIONS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_qr_and_evidence()
