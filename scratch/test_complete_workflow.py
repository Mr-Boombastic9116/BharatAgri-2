import httpx
import json
import os
import io
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:5000"
today_str = datetime.utcnow().date().strftime("%Y-%m-%d")

def test_full_centre_workflow():
    print("=== STARTING FULL CENTRE WORKFLOW TEST ===")
    
    with httpx.Client(timeout=30.0) as client:
        # 1. Login as Centre
        login_resp = client.post(f"{BASE_URL}/api/auth/login", json={
            "user_id": "centre@bharatagri.demo",
            "password": "BharatAgri@2026"
        })
        assert login_resp.status_code == 200, f"Centre login failed: {login_resp.text}"
        centre_data = login_resp.json()
        centre_token = centre_data["access_token"]
        centre_headers = {"Authorization": f"Bearer {centre_token}"}
        centre_id = centre_data.get("user", {}).get("centre_id") or "CENTRE-GOA-01"
        print(f"[OK] Centre Logged in: {centre_id}")

        # 2. Login as Farmer
        f_login = client.post(f"{BASE_URL}/api/auth/login", json={
            "user_id": "farmer@bharatagri.demo",
            "password": "BharatAgri@2026",
            "role": "farmer"
        })
        assert f_login.status_code == 200, f"Farmer login failed: {f_login.text}"
        farmer_token = f_login.json()["access_token"]
        farmer_headers = {"Authorization": f"Bearer {farmer_token}"}
        farmer_id = f_login.json().get("user", {}).get("user_id")
        print(f"[OK] Farmer Logged in: {farmer_id}")

        # 3. Create or find slot for today at centre
        slot_res = client.post(f"{BASE_URL}/api/slots", headers=centre_headers, json={
            "centre_id": centre_id,
            "date": today_str,
            "start_time": "11:00 AM",
            "end_time": "01:00 PM",
            "max_capacity": 50
        })
        slot_id = slot_res.json().get("slot", {}).get("id")
        if not slot_id:
            slots = client.get(f"{BASE_URL}/api/slots?centre_id={centre_id}&date={today_str}").json()
            slot_id = slots[0]["id"]
        print(f"[OK] Slot confirmed: ID={slot_id} for date {today_str}")

        # 4. Create fresh booking for farmer
        bk_res = client.post(f"{BASE_URL}/api/bookings", headers=farmer_headers, json={
            "farmer_id": farmer_id,
            "centre_id": centre_id,
            "slot_id": slot_id,
            "crop": "Paddy",
            "quantity": 30.0
        })
        assert bk_res.status_code in (200, 201), f"Booking failed: {bk_res.text}"
        bk = bk_res.json().get("booking", {})
        booking_id = bk.get("id")
        qr_token = bk.get("qr_token")
        appt_id = bk.get("appointment_id")
        print(f"[OK] Target Booking created: ID={booking_id}, ApptID={appt_id}, QR={qr_token}")

        # 5. QR Verification Tests
        print("\n--- Testing QR Verification ---")
        
        # 5a. Invalid QR Token Test
        bad_verify = client.post(f"{BASE_URL}/api/appointments/verify", headers=centre_headers, json={
            "qr_token": "INVALID-QR-TOKEN-XYZ",
            "centre_id": centre_id
        })
        bad_data = bad_verify.json()
        print(f"[OK] Invalid QR rejection: success={bad_data.get('success')}, code={bad_data.get('code')}")
        assert bad_data.get("success") is False
        assert bad_data.get("code") == "INVALID_QR"

        # 5b. Wrong Centre QR Test
        wrong_centre_verify = client.post(f"{BASE_URL}/api/appointments/verify", headers=centre_headers, json={
            "qr_token": qr_token,
            "centre_id": "CENTRE-DELHI-999"
        })
        wrong_data = wrong_centre_verify.json()
        print(f"[OK] Cross-centre QR rejection: success={wrong_data.get('success')}, code={wrong_data.get('code')}")
        assert wrong_data.get("success") is False
        assert wrong_data.get("code") in ["WRONG_CENTRE", "CENTRE_NOT_FOUND", "UNAUTHORIZED_CENTRE"]

        # 5c. Valid QR Verification Test
        valid_verify = client.post(f"{BASE_URL}/api/appointments/verify", headers=centre_headers, json={
            "qr_token": qr_token,
            "centre_id": centre_id
        })
        valid_data = valid_verify.json()
        print(f"[OK] Valid QR verify: success={valid_data.get('success')}, message={valid_data.get('message')}")
        assert valid_data.get("success") is True

        # 6. Procurement Workflow WITH Evidence Uploads
        print("\n--- Testing Procurement Workflow WITH Photo Evidence ---")
        
        # 6a. Step 1: Collection / Intake (Arrival)
        coll_resp = client.post(f"{BASE_URL}/api/procurement/collection", headers=centre_headers, json={
            "booking_id": booking_id,
            "actual_quantity": 30.0,
            "vehicle_number": "GA-01-AB-1234",
            "driver_name": "Ramesh",
            "notes": "Good arrival condition"
        })
        assert coll_resp.status_code in [200, 201], f"Collection failed: {coll_resp.text}"
        print(f"[OK] Step 1 (Intake/Collection) completed: {coll_resp.json().get('message')}")

        # 6b. Upload Quality Evidence
        fake_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        q_ev_resp = client.post(
            f"{BASE_URL}/api/procurement/evidence/upload",
            headers=centre_headers,
            data={"booking_id": str(booking_id), "evidence_type": "QUALITY", "notes": "Inspected FAQ grain sample"},
            files={"file": ("sample_quality.png", io.BytesIO(fake_png), "image/png")}
        )
        assert q_ev_resp.status_code == 200, f"Quality evidence upload failed: {q_ev_resp.text}"
        print(f"[OK] Quality Evidence Uploaded: {q_ev_resp.json().get('evidence', {}).get('file_path')}")

        # 6c. Upload Moisture Evidence
        m_ev_resp = client.post(
            f"{BASE_URL}/api/procurement/evidence/upload",
            headers=centre_headers,
            data={"booking_id": str(booking_id), "evidence_type": "MOISTURE", "notes": "Moisture meter 11.8%"},
            files={"file": ("moisture_meter.png", io.BytesIO(fake_png), "image/png")}
        )
        assert m_ev_resp.status_code == 200, f"Moisture evidence upload failed: {m_ev_resp.text}"
        print(f"[OK] Moisture Evidence Uploaded: {m_ev_resp.json().get('evidence', {}).get('file_path')}")

        # 6d. Step 2: Record Quality Check
        qc_resp = client.post(f"{BASE_URL}/api/procurement/quality", headers=centre_headers, json={
            "booking_id": booking_id,
            "quality_grade": "GRADE_A",
            "moisture_content_pct": 11.8,
            "foreign_matter_pct": 0.5,
            "damaged_grains_pct": 0.2,
            "weevilled_grains_pct": 0.0,
            "status": "APPROVED",
            "notes": "Passed Grade A inspection"
        })
        assert qc_resp.status_code in [200, 201], f"Quality check failed: {qc_resp.text}"
        print(f"[OK] Step 2 (Quality Check) completed: {qc_resp.json().get('message')}")

        # 6e. Upload Weighing Evidence
        w_ev_resp = client.post(
            f"{BASE_URL}/api/procurement/evidence/upload",
            headers=centre_headers,
            data={"booking_id": str(booking_id), "evidence_type": "WEIGHING", "notes": "Weighbridge gross receipt"},
            files={"file": ("weighing_scale.png", io.BytesIO(fake_png), "image/png")}
        )
        assert w_ev_resp.status_code == 200, f"Weighing evidence upload failed: {w_ev_resp.text}"
        print(f"[OK] Weighing Evidence Uploaded: {w_ev_resp.json().get('evidence', {}).get('file_path')}")

        # 6f. Step 3: Record Weighment
        w_resp = client.post(f"{BASE_URL}/api/procurement/weighment", headers=centre_headers, json={
            "booking_id": booking_id,
            "gross_weight_quintals": 30.5,
            "tare_weight_quintals": 0.5,
            "operator_name": "Scale Operator"
        })
        assert w_resp.status_code in [200, 201], f"Weighment failed: {w_resp.text}"
        w_data = w_resp.json()
        weighment_id = w_data.get("weighment_id") or w_data.get("data", {}).get("weighment_id")
        print(f"[OK] Step 3 (Weighment) completed: weighment_id={weighment_id}")

        # 6g. Step 4: Storage / Procure
        store_resp = client.post(f"{BASE_URL}/api/procurement/procure", headers=centre_headers, json={
            "booking_id": booking_id,
            "farmer_id": farmer_id,
            "centre_id": centre_id,
            "crop": "Paddy",
            "procured_quantity_quintals": 30.0,
            "rate_per_quintal_inr": 2300.0,
            "warehouse_location": "Silo A-2"
        })
        assert store_resp.status_code in [200, 201], f"Storage failed: {store_resp.text}"
        store_data = store_resp.json()
        payment_id = store_data.get("payment_id") or store_data.get("data", {}).get("payment_id")
        print(f"[OK] Step 4 (Storage/Procure) completed: payment_id={payment_id}")

        # 6h. Step 5: Payment
        if payment_id:
            pay_resp = client.post(f"{BASE_URL}/api/procurement/payment/{payment_id}/complete", headers=centre_headers, json={
                "bank_ref_number": f"UTR-TEST-{booking_id}"
            })
            assert pay_resp.status_code in [200, 201], f"Payment failed: {pay_resp.text}"
            print(f"[OK] Step 5 (Payment complete) completed: {pay_resp.json().get('message')}")

        # 6i. Verify Evidence Retrieval & Categorization
        ev_get = client.get(f"{BASE_URL}/api/procurement/evidence/{booking_id}", headers=centre_headers)
        assert ev_get.status_code == 200
        ev_data = ev_get.json()
        assert ev_data["total"] >= 3
        assert len(ev_data["by_type"]["QUALITY"]) >= 1
        assert len(ev_data["by_type"]["MOISTURE"]) >= 1
        assert len(ev_data["by_type"]["WEIGHING"]) >= 1
        print(f"[OK] Evidence Retrieval confirmed: {ev_data['total']} items properly categorized across QUALITY, MOISTURE, WEIGHING")

        # 7. TEST WORKFLOW WITHOUT ANY PHOTOS (OPTIONALITY TEST)
        print("\n--- Testing Workflow WITHOUT Any Photos (Verifying Optionality) ---")
        create2 = client.post(f"{BASE_URL}/api/bookings", headers=farmer_headers, json={
            "farmer_id": farmer_id,
            "centre_id": centre_id,
            "slot_id": slot_id,
            "crop": "Paddy",
            "quantity": 15.0
        })
        assert create2.status_code == 201
        b2 = create2.json().get("booking", {})
        b2_id = b2.get("id")
        print(f"[OK] Created 2nd booking for optionality test: ID={b2_id}")

        # Run complete workflow with NO photos uploaded
        c2 = client.post(f"{BASE_URL}/api/procurement/collection", headers=centre_headers, json={
            "booking_id": b2_id, "actual_quantity": 15.0
        })
        assert c2.status_code in [200, 201]

        q2 = client.post(f"{BASE_URL}/api/procurement/quality", headers=centre_headers, json={
            "booking_id": b2_id,
            "quality_grade": "GRADE_B",
            "moisture_content_pct": 13.0,
            "foreign_matter_pct": 1.2,
            "damaged_grains_pct": 0.5,
            "status": "APPROVED",
            "notes": "Passed without photos"
        })
        if q2.status_code not in [200, 201]:
            print(f"[DEBUG q2 failed]: {q2.status_code} {q2.text}")
        assert q2.status_code in [200, 201]

        w2 = client.post(f"{BASE_URL}/api/procurement/weighment", headers=centre_headers, json={
            "booking_id": b2_id, "gross_weight_quintals": 15.2, "tare_weight_quintals": 0.2, "operator_name": "Scale Operator"
        })
        assert w2.status_code in [200, 201]

        s2 = client.post(f"{BASE_URL}/api/procurement/procure", headers=centre_headers, json={
            "booking_id": b2_id,
            "farmer_id": farmer_id,
            "centre_id": centre_id,
            "crop": "Paddy",
            "procured_quantity_quintals": 15.0,
            "rate_per_quintal_inr": 2300.0,
            "warehouse_location": "Bay C"
        })
        assert s2.status_code in [200, 201]

        p2_id = s2.json().get("payment_id") or s2.json().get("data", {}).get("payment_id")
        if p2_id:
            p2 = client.post(f"{BASE_URL}/api/procurement/payment/{p2_id}/complete", headers=centre_headers, json={
                "bank_ref_number": f"UTR-TEST-{b2_id}"
            })
            assert p2.status_code in [200, 201]
        print("[OK] Zero-photo workflow succeeded without any errors or photo validation blockers!")

        # Verify evidence on 2nd booking is empty
        ev2_get = client.get(f"{BASE_URL}/api/procurement/evidence/{b2_id}", headers=centre_headers)
        assert ev2_get.status_code == 200
        assert ev2_get.json()["total"] == 0
        print("[OK] 2nd booking correctly has 0 evidence records.")

        print("\n=== ALL WORKFLOW TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    test_full_centre_workflow()
