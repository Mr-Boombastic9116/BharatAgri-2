import pytest
from fastapi.testclient import TestClient
from datetime import date, timedelta
from backend.app.main import app

client = TestClient(app)

DEMO_PASSWORD = "BharatAgri@2026"

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"
    assert data["ai"] == "available"

def test_login_all_four_roles():
    roles = [
        ("admin@bharatagri.demo", "GOVERNMENT"),
        ("centre@bharatagri.demo", "PROCUREMENT_CENTRE"),
        ("agent@bharatagri.demo", "AGENT"),
        ("farmer@bharatagri.demo", "FARMER")
    ]
    for email, expected_role in roles:
        res = client.post("/api/auth/login", json={
            "user_id": email,
            "password": DEMO_PASSWORD
        })
        assert res.status_code == 200, f"Failed login for {email}: {res.text}"
        body = res.json()
        assert body["user"]["role"].upper() in (expected_role, "CENTRE", "PROCUREMENT_CENTRE")
        assert "token" in body or "access_token" in body

def test_rbac_protection():
    # Login as farmer
    farmer_res = client.post("/api/auth/login", json={
        "user_id": "farmer@bharatagri.demo",
        "password": DEMO_PASSWORD
    })
    farmer_token = farmer_res.json()["token"]

    # Farmer attempts to access Government KPIs -> 403 Forbidden
    kpi_res = client.get("/api/government/kpis", headers={"Authorization": f"Bearer {farmer_token}"})
    assert kpi_res.status_code == 403

    # Login as government admin
    admin_res = client.post("/api/auth/login", json={
        "user_id": "admin@bharatagri.demo",
        "password": DEMO_PASSWORD
    })
    admin_token = admin_res.json()["token"]

    # Admin accesses Government KPIs -> 200 OK
    admin_kpi_res = client.get("/api/government/kpis", headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_kpi_res.status_code == 200
    kpis = admin_kpi_res.json()["data"]
    assert kpis["registered_farmers"] >= 2000
    assert kpis["active_centres"] >= 20

def test_centres_listing():
    res = client.get("/api/centres")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 20
    assert "centre_id" in data[0]
    assert "centre_name" in data[0]

def test_farmer_profile():
    farmer_res = client.post("/api/auth/login", json={
        "user_id": "farmer@bharatagri.demo",
        "password": DEMO_PASSWORD
    })
    token = farmer_res.json()["token"]
    user_id = farmer_res.json()["user"]["user_id"]

    res = client.get(f"/api/farmers/{user_id}", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    farmer_data = res.json()
    assert farmer_data["user_id"] == user_id
    assert "crops" in farmer_data
    assert "land_area_hectares" in farmer_data

def test_booking_workflow_and_qr():
    # Login as farmer
    farmer_res = client.post("/api/auth/login", json={
        "user_id": "farmer@bharatagri.demo",
        "password": DEMO_PASSWORD
    })
    farmer_token = farmer_res.json()["token"]
    farmer_id = farmer_res.json()["user"]["user_id"]

    target_date = (date.today() + timedelta(days=10)).strftime("%Y-%m-%d")

    # Get slots for CENTRE-GOA-01
    slots_res = client.get(f"/api/slots?centre_id=CENTRE-GOA-01&date={target_date}")
    assert slots_res.status_code == 200
    slots_data = slots_res.json()

    slot_id = None
    if isinstance(slots_data, list) and len(slots_data) > 0:
        slot_id = slots_data[0]["id"]
    elif isinstance(slots_data, dict) and slots_data.get("data") and len(slots_data["data"]) > 0:
        slot_id = slots_data["data"][0]["id"]
    else:
        # Create a slot as centre
        centre_res = client.post("/api/auth/login", json={
            "user_id": "centre@bharatagri.demo",
            "password": DEMO_PASSWORD
        })
        centre_token = centre_res.json()["token"]
        create_slot_res = client.post("/api/slots", headers={"Authorization": f"Bearer {centre_token}"}, json={
            "centre_id": "CENTRE-GOA-01",
            "date": target_date,
            "start_time": "10:00 AM",
            "end_time": "12:00 PM",
            "max_capacity": 50
        })
        created_slot = create_slot_res.json()
        slot_id = created_slot["slot"]["id"] if "slot" in created_slot else created_slot["id"]

    # Book slot
    booking_res = client.post("/api/bookings", headers={"Authorization": f"Bearer {farmer_token}"}, json={
        "farmer_id": farmer_id,
        "centre_id": "CENTRE-GOA-01",
        "slot_id": slot_id,
        "crop": "Paddy",
        "quantity": 25.0
    })
    assert booking_res.status_code in (200, 201)
    b_resp = booking_res.json()
    booking_data = b_resp.get("booking") or b_resp.get("data")
    qr_token = booking_data["qr_token"]
    booking_code = booking_data["appointment_id"] if "appointment_id" in booking_data else booking_data["booking_code"]

    # Verify QR Token as centre
    centre_res = client.post("/api/auth/login", json={
        "user_id": "centre@bharatagri.demo",
        "password": DEMO_PASSWORD
    })
    centre_token = centre_res.json()["token"]

    verify_res = client.post("/api/appointments/verify", headers={"Authorization": f"Bearer {centre_token}"}, json={
        "qr_token": qr_token,
        "centre_id": "CENTRE-GOA-01"
    })
    assert verify_res.status_code == 200
    v_data = verify_res.json()
    assert v_data.get("valid") is True or v_data.get("success") is True

def test_full_procurement_lifecycle():
    # Login as centre
    centre_res = client.post("/api/auth/login", json={
        "user_id": "centre@bharatagri.demo",
        "password": DEMO_PASSWORD
    })
    centre_token = centre_res.json()["token"]
    headers = {"Authorization": f"Bearer {centre_token}"}

    from backend.app.core.database import SessionLocal
    from backend.app.models.booking import Booking
    db = SessionLocal()
    active_b = db.query(Booking).filter(Booking.status.in_(["BOOKED", "CONFIRMED"])).first()
    db.close()
    b_id = active_b.id if active_b else 1
    c_id = active_b.centre_id if active_b else "CENTRE-GOA-01"
    f_id = active_b.farmer_id if active_b else "farmer@bharatagri.demo"

    # Step 1: Collection
    coll_res = client.post("/api/procurement/collection", headers=headers, json={
        "booking_id": b_id,
        "centre_id": c_id,
        "farmer_id": f_id,
        "collected_bags": 50,
        "gross_weight_quintals": 25.50,
        "truck_number": "GA-01-TR-1001",
        "village_collected": "Ponda",
        "notes": "Good dry condition"
    })
    assert coll_res.status_code == 201
    coll_data = coll_res.json()

    # Step 2: Quality Check
    qc_res = client.post("/api/procurement/quality", headers=headers, json={
        "collection_id": coll_data["collection_id"],
        "moisture_content_pct": 13.2,
        "foreign_matter_pct": 0.8,
        "damaged_grains_pct": 1.0,
        "quality_grade": "Grade A",
        "passed": True,
        "inspector_name": "R. Naik",
        "notes": "Approved for storage"
    })
    assert qc_res.status_code == 201
    qc_data = qc_res.json()

    # Step 3: Weighment
    weigh_res = client.post("/api/procurement/weighment", headers=headers, json={
        "quality_check_id": qc_data["check_id"],
        "gross_weight_quintals": 26.20,
        "tare_weight_quintals": 1.20,
        "scale_operator_name": "M. Parab"
    })
    assert weigh_res.status_code == 201
    weigh_data = weigh_res.json()

    # Step 4: Final Procurement & Lot generation
    proc_res = client.post("/api/procurement/procure", headers=headers, json={
        "weighment_id": weigh_data["weighment_id"],
        "rate_per_quintal_inr": 2300.0,
        "bardan_bags_used": 50,
        "procurement_officer": "S. Desai"
    })
    assert proc_res.status_code == 201
    proc_data = proc_res.json()
    lot_id = proc_data["lot_id"]
    assert lot_id.startswith("LOT-")

    # Step 5: Traceability
    trace_res = client.get(f"/api/procurement/traceability/{proc_data['procurement_id']}", headers=headers)
    assert trace_res.status_code == 200
    trace_data = trace_res.json()["data"]
    assert trace_data["lot_id"] == lot_id
    assert trace_data["quality"]["grade"] == "Grade A"

    # Step 6: Payment Completion
    payment_id = trace_data["payment"]["id"]
    pay_res = client.post(f"/api/procurement/payment/{payment_id}/complete", headers=headers, json={
        "bank_ref_number": "UTR99281726354"
    })
    assert pay_res.status_code == 200
    assert pay_res.json()["data"]["payment_status"] == "PAID"

def test_ai_supply_forecast():
    admin_res = client.post("/api/auth/login", json={
        "user_id": "admin@bharatagri.demo",
        "password": DEMO_PASSWORD
    })
    token = admin_res.json()["token"]

    res = client.post("/api/ai/supply-forecast", headers={"Authorization": f"Bearer {token}"}, json={
        "centre_id": "CENTRE-GOA-01",
        "crop": "Paddy",
        "month": 10,
        "year": 2026,
        "registered_farmers": 200,
        "booked_quantity": 600.0
    })
    assert res.status_code == 200
    data = res.json()["data"]
    pred = data["prediction"]
    assert pred["predicted_procurement_quantity"] > 0
    assert pred["confidence_score"] > 0

def test_ai_congestion_calculation():
    admin_res = client.post("/api/auth/login", json={
        "user_id": "admin@bharatagri.demo",
        "password": DEMO_PASSWORD
    })
    token = admin_res.json()["token"]

    res = client.get("/api/ai/congestion?centre_id=CENTRE-GOA-01", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) >= 1
    assert data[0]["congestion_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert "recommended_action" in data[0]

def test_ai_truck_allocation_optimization():
    centre_res = client.post("/api/auth/login", json={
        "user_id": "centre@bharatagri.demo",
        "password": DEMO_PASSWORD
    })
    token = centre_res.json()["token"]

    res = client.post("/api/ai/truck-allocation", headers={"Authorization": f"Bearer {token}"}, json={
        "centre_id": "CENTRE-GOA-01",
        "requests": [
            {"request_id": "R1", "village": "Ponda North", "quantity_quintals": 40.0, "distance_km": 12.0, "urgency": "HIGH"},
            {"request_id": "R2", "village": "Ponda South", "quantity_quintals": 60.0, "distance_km": 18.0, "urgency": "MEDIUM"}
        ],
        "trucks": [
            {"truck_id": 1, "truck_number": "GA-01-TR-1001", "capacity_quintals": 100.0, "driver_name": "Dev", "current_centre_id": "CENTRE-GOA-01"}
        ]
    })
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["engine"] == "Optimization Engine (Google OR-Tools)"
    assert res_data["success"] is True

def test_bardan_forecast():
    admin_res = client.post("/api/auth/login", json={
        "user_id": "admin@bharatagri.demo",
        "password": DEMO_PASSWORD
    })
    token = admin_res.json()["token"]

    res = client.get("/api/bardan/forecast?centre_id=CENTRE-GOA-01", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) >= 1
    assert "projected_requirement" in data[0]
    assert data[0]["status"] in ("SAFE", "LOW", "WARNING", "SHORTAGE")

def test_complaints_end_to_end():
    farmer_res = client.post("/api/auth/login", json={
        "user_id": "farmer@bharatagri.demo",
        "password": DEMO_PASSWORD
    })
    farmer_token = farmer_res.json()["token"]

    # File complaint
    file_res = client.post("/api/complaints", headers={"Authorization": f"Bearer {farmer_token}"}, json={
        "centre_id": "CENTRE-GOA-01",
        "category": "Weighment Discrepancy",
        "priority": "HIGH",
        "subject": "Delay in Weighment Processing",
        "description": "Waiting for 4 hours at the electronic weighbridge."
    })
    assert file_res.status_code == 200
    complaint_id = file_res.json()["data"]["id"]

    # View complaint
    view_res = client.get(f"/api/complaints/{complaint_id}", headers={"Authorization": f"Bearer {farmer_token}"})
    assert view_res.status_code == 200
    assert len(view_res.json()["data"]["messages"]) >= 1

    # Centre responds and updates status
    centre_res = client.post("/api/auth/login", json={
        "user_id": "centre@bharatagri.demo",
        "password": DEMO_PASSWORD
    })
    centre_token = centre_res.json()["token"]

    reply_res = client.post(f"/api/complaints/{complaint_id}/messages", headers={"Authorization": f"Bearer {centre_token}"}, json={
        "message": "Scale 2 is now calibrated and operating. Processing has resumed."
    })
    assert reply_res.status_code == 200

    status_res = client.put(f"/api/complaints/{complaint_id}/status", headers={"Authorization": f"Bearer {centre_token}"}, json={
        "status": "RESOLVED",
        "resolution": "Scale 2 brought online; farmer truck weighed successfully."
    })
    assert status_res.status_code == 200
    assert status_res.json()["data"]["status"] == "RESOLVED"
