import httpx
from datetime import datetime

BASE_URL = "http://localhost:5000"
today_str = datetime.utcnow().date().strftime("%Y-%m-%d")

with httpx.Client(timeout=10.0) as client:
    # 1. Login as centre
    login_res = client.post(f"{BASE_URL}/api/auth/login", json={
        "user_id": "centre@bharatagri.demo",
        "password": "BharatAgri@2026"
    })
    token = login_res.json()["access_token"]
    centre_headers = {"Authorization": f"Bearer {token}"}
    centre_id = login_res.json().get("user", {}).get("centre_id") or "CENTRE-GOA-01"

    # 2. Login as farmer
    f_login = client.post(f"{BASE_URL}/api/auth/login", json={
        "user_id": "farmer@bharatagri.demo",
        "password": "BharatAgri@2026",
        "role": "farmer"
    })
    f_token = f_login.json()["access_token"]
    farmer_headers = {"Authorization": f"Bearer {f_token}"}
    farmer_id = f_login.json().get("user", {}).get("user_id")

    # 3. Create or find slot for today at CENTRE-GOA-01
    slot_res = client.post(f"{BASE_URL}/api/slots", headers=centre_headers, json={
        "centre_id": centre_id,
        "date": today_str,
        "start_time": "11:00 AM",
        "end_time": "01:00 PM",
        "max_capacity": 20
    })
    slot_id = slot_res.json().get("slot", {}).get("id")
    if not slot_id:
        slots = client.get(f"{BASE_URL}/api/slots?centre_id={centre_id}&date={today_str}").json()
        slot_id = slots[0]["id"]

    # 4. Create booking for farmer
    bk_res = client.post(f"{BASE_URL}/api/bookings", headers=farmer_headers, json={
        "farmer_id": farmer_id,
        "centre_id": centre_id,
        "slot_id": slot_id,
        "crop": "Paddy",
        "quantity": 30.0
    })
    assert bk_res.status_code in (200, 201), f"Booking failed: {bk_res.text}"
    bk = bk_res.json().get("booking", {})
    qr_token = bk.get("qr_token")
    appt_id = bk.get("appointment_id")
    print(f"Created fresh booking: Appt ID={appt_id}, QR={qr_token}, Date={today_str}, Status={bk.get('status')}")

    # 5. Verify QR code
    v_res = client.post(f"{BASE_URL}/api/appointments/verify", headers=centre_headers, json={
        "qr_token": qr_token,
        "centre_id": centre_id
    })
    print(f"Verification result: Status={v_res.status_code}, Res={v_res.json()}")
    assert v_res.json().get("success") is True
    appt = v_res.json().get("appointment", {})
    assert appt.get("status") == "ARRIVED"
    assert appt.get("appointment_id") == appt_id
    print("VERIFICATION SUCCESS! Farmer marked ARRIVED.")
