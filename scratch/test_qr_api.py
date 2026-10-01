import httpx

BASE_URL = "http://localhost:5000"

with httpx.Client(timeout=10.0) as client:
    # 1. Login as centre@bharatagri.demo
    login_res = client.post(f"{BASE_URL}/api/auth/login", json={
        "user_id": "centre@bharatagri.demo",
        "password": "BharatAgri@2026"
    })
    assert login_res.status_code == 200, f"Centre login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    centre_id = login_res.json().get("user", {}).get("centre_id") or "CENTRE-GOA-01"
    print(f"Logged in as centre: {centre_id}")

    # 2. Test Invalid QR Token
    res_invalid = client.post(f"{BASE_URL}/api/appointments/verify", headers=headers, json={
        "qr_token": "TOTALLY_FAKE_QR_99999",
        "centre_id": centre_id
    })
    print("\nTest 1 - Invalid QR:")
    print(f"Status: {res_invalid.status_code}, Response: {res_invalid.json()}")
    assert res_invalid.json().get("success") is False
    assert res_invalid.json().get("code") == "INVALID_QR"

    # 3. Test Cross-Centre QR (Booking belongs to CENTRE-MH-08, but verified by CENTRE-GOA-01)
    res_cross = client.post(f"{BASE_URL}/api/appointments/verify", headers=headers, json={
        "qr_token": "BA-QR-PF-261009-8610",
        "centre_id": centre_id
    })
    print("\nTest 2 - Cross-Centre QR:")
    print(f"Status: {res_cross.status_code}, Response: {res_cross.json()}")
    assert res_cross.json().get("success") is False
    assert res_cross.json().get("code") == "WRONG_CENTRE"

    # 4. Test Cross-Centre User Authorization (User claims target centre is CENTRE-MH-08, but user is authorized for CENTRE-GOA-01)
    res_unauth = client.post(f"{BASE_URL}/api/appointments/verify", headers=headers, json={
        "qr_token": "BA-QR-PF-261009-8610",
        "centre_id": "CENTRE-MH-08"
    })
    print("\nTest 3 - Cross-Centre Target Override:")
    print(f"Status: {res_unauth.status_code}, Response: {res_unauth.json()}")
    assert res_unauth.json().get("success") is False
    assert res_unauth.json().get("code") == "UNAUTHORIZED_CENTRE"

    # 5. Test Valid QR for this Centre
    res_valid = client.post(f"{BASE_URL}/api/appointments/verify", headers=headers, json={
        "qr_token": "a8451e7202d2e4556b01230c61478ea9",
        "centre_id": centre_id
    })
    print("\nTest 4 - Valid QR for CENTRE-GOA-01:")
    print(f"Status: {res_valid.status_code}, Response: {res_valid.json()}")
    assert res_valid.json().get("success") is True
    appt = res_valid.json().get("appointment", {})
    assert appt.get("status") == "ARRIVED"
    assert appt.get("centre_id") == "CENTRE-GOA-01"
    print("All backend QR verification security and workflow checks passed!")
