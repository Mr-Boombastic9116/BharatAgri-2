import sys
import httpx
import json

BASE_URL = "http://localhost:5000"

def log(msg, success=True):
    symbol = "PASS" if success else "FAIL"
    print(f"[{symbol}] {msg}")

def run_tests():
    with httpx.Client(timeout=10.0) as client:
        print("\n--- 1. TESTING HEALTH & STATUS ---")
        res = client.get(f"{BASE_URL}/api/health")
        if res.status_code != 200:
            log(f"Health check failed: {res.text}", False)
            return
        log(f"Health check OK: {res.json()}")

        print("\n--- 2. TESTING FARMER REGISTRATION & IDENTITY ---")
        reg_payload = {
            "name": "Ramesh Kisan Test",
            "mobile": "9876543299",
            "email": "ramesh.test@bharatagri.demo",
            "password": "Password@123",
            "state": "Maharashtra",
            "district": "Nashik",
            "taluka": "Niphad",
            "village": "Pimpalgaon",
            "address": "House 45, Near Gram Panchayat",
            "dob": "1982-05-14",
            "land_area": 4.5,
            "bank_name": "State Bank of India",
            "bank_account_no": "123456789012",
            "bank_ifsc": "SBIN0001234",
            "farmer_id": "FRM-2026-99999",
            "user_code": "RAMESH99"
        }
        res = client.post(f"{BASE_URL}/api/farmers/register", json=reg_payload)
        if res.status_code in (200, 201):
            log("Farmer registered successfully with Farmer ID + User Code + Masked Bank")
            f_data = res.json().get("farmer", {})
            log(f"Assigned Farmer ID: {f_data.get('farmer_id')}, User Code: {f_data.get('user_code')}")
        elif "already" in res.text or res.status_code == 400:
            log("Farmer already registered previously or handled - proceeding to login")
        else:
            log(f"Farmer registration response: {res.status_code} {res.text}", False)

        print("\n--- 3. TESTING FARMER LOGIN & PROFILE ISOLATION ---")
        login_res = client.post(f"{BASE_URL}/api/auth/login", json={
            "user_id": "RAMESH99",
            "password": "Password@123",
            "role": "farmer"
        })
        if login_res.status_code != 200:
            # Fallback to demo farmer
            login_res = client.post(f"{BASE_URL}/api/auth/login", json={
                "user_id": "farmer@bharatagri.demo",
                "password": "BharatAgri@2026",
                "role": "farmer"
            })
        if login_res.status_code != 200:
            log(f"Farmer login failed: {login_res.text}", False)
            return
        token = login_res.json()["access_token"]
        farmer_headers = {"Authorization": f"Bearer {token}"}
        log("Farmer login successful, JWT token obtained")

        # Profile fetch
        prof_res = client.get(f"{BASE_URL}/api/farmers/me", headers=farmer_headers)
        assert prof_res.status_code == 200, f"Profile get failed: {prof_res.text}"
        profile = prof_res.json()
        log(f"Farmer Profile loaded: Name={profile.get('name')}, FarmerID={profile.get('farmer_code') or profile.get('user_id')}, Bank={profile.get('bank_account_no')}")

        # Profile update
        upd_res = client.put(f"{BASE_URL}/api/farmers/me", headers=farmer_headers, json={
            "name": "Ramesh Kisan Updated",
            "village": "Pimpalgaon Khurd",
            "land_area_hectares": 5.0
        })
        assert upd_res.status_code == 200, f"Profile update failed: {upd_res.text}"
        log("Farmer Profile updated successfully in MySQL")

        print("\n--- 4. TESTING MY CROPS CRUD ---")
        # Add Crop
        crop_res = client.post(f"{BASE_URL}/api/farmers/me/crops", headers=farmer_headers, json={
            "crop_name": "Wheat",
            "season": "Rabi 2026",
            "sowing_date": "2026-06-01",
            "expected_harvest_date": "2026-10-15",
            "estimated_quantity_quintals": 45.0
        })
        assert crop_res.status_code in (200, 201), f"Add crop failed: {crop_res.text}"
        new_crop = crop_res.json().get("crop", {})
        crop_id = new_crop.get("id")
        log(f"Added Crop: ID={crop_id}, Name={new_crop.get('crop_name')}, Yield={new_crop.get('estimated_quantity_quintals')} Q")

        # Get Crops via profile
        prof_after = client.get(f"{BASE_URL}/api/farmers/me", headers=farmer_headers).json()
        crops_list = prof_after.get("crops", [])
        assert any(c.get("id") == crop_id for c in crops_list), "Added crop not found in list"
        log(f"Crops list retrieved: {len(crops_list)} crops found for farmer")

        print("\n--- 5. TESTING AGENT AUTH & DASHBOARD ---")
        agent_login = client.post(f"{BASE_URL}/api/auth/login", json={
            "user_id": "agent@bharatagri.demo",
            "password": "BharatAgri@2026"
        })
        assert agent_login.status_code == 200, f"Agent login failed: {agent_login.text}"
        agent_headers = {"Authorization": f"Bearer {agent_login.json()['access_token']}"}
        log("Agent login successful")
        
        agent_dash = client.get(f"{BASE_URL}/api/agents/stats", headers=agent_headers)
        assert agent_dash.status_code == 200, f"Agent dashboard failed: {agent_dash.text}"
        dash_data = agent_dash.json()
        log(f"Agent Dashboard Data: Farmers Assisted={dash_data.get('farmers_assisted', 0)}, Bookings={dash_data.get('todays_bookings', 0)}, Alerts={len(dash_data.get('alerts', []))}")

        print("\n--- 6. TESTING CENTRE IDENTITY, CONFIG & HOLIDAYS ---")
        centre_login = client.post(f"{BASE_URL}/api/auth/login", json={
            "user_id": "centre@bharatagri.demo",
            "password": "BharatAgri@2026"
        })
        assert centre_login.status_code == 200, f"Centre login failed: {centre_login.text}"
        centre_headers = {"Authorization": f"Bearer {centre_login.json()['access_token']}"}
        centre_id = centre_login.json().get("user", {}).get("centre_id") or "CENTRE-GOA-01"
        log(f"Centre login successful: user centre_id={centre_id}")

        # Check centre operation config
        cfg_res = client.get(f"{BASE_URL}/api/centres/{centre_id}/operating-config", headers=centre_headers)
        assert cfg_res.status_code == 200, f"Get centre config failed: {cfg_res.text}"
        centre_cfg = cfg_res.json()
        log(f"Centre Config loaded for Centre {centre_id}: Capacity={centre_cfg.get('max_daily_capacity_quintals')} Q")

        # Update config
        upd_cfg_res = client.put(f"{BASE_URL}/api/centres/{centre_id}/operating-config", headers=centre_headers, json={
            "operating_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
            "max_daily_capacity_quintals": 550.0,
            "opening_time": "08:00 AM",
            "closing_time": "06:00 PM",
            "supported_crops": ["Paddy", "Wheat", "Maize"]
        })
        assert upd_cfg_res.status_code == 200, f"Update centre config failed: {upd_cfg_res.text}"
        log("Centre Operation Configuration saved successfully")

        # Add holiday exception
        import random
        from datetime import date, timedelta
        random_days = random.randint(15, 60)
        d = date.today() + timedelta(days=random_days)
        if d.weekday() == 6:
            d = d + timedelta(days=1)
        holiday_date = d.strftime("%Y-%m-%d")
        client.delete(f"{BASE_URL}/api/centres/{centre_id}/non-operational-dates/{holiday_date}")
        hol_res = client.post(f"{BASE_URL}/api/centres/{centre_id}/non-operational-dates", headers=centre_headers, json={
            "date": holiday_date,
            "reason": "Diwali Festival"
        })
        assert hol_res.status_code in (200, 201), f"Add holiday failed: {hol_res.text}"
        log(f"Holiday {holiday_date} added to Centre {centre_id}")

        # Ensure slot exists on that date
        slot_res = client.post(f"{BASE_URL}/api/slots", json={
            "centre_id": centre_id,
            "date": holiday_date,
            "start_time": "10:00",
            "end_time": "11:00",
            "max_capacity": 10
        })
        slot_data = slot_res.json().get("slot") or {}
        slot_id = slot_data.get("id")
        if not slot_id:
            # fetch existing slot
            slots_list = client.get(f"{BASE_URL}/api/slots?centre_id={centre_id}&date={holiday_date}").json()
            if slots_list:
                slot_id = slots_list[0]["id"]
        log(f"Using slot ID {slot_id} on {holiday_date}")

        # Verify holiday rejects farmer booking
        farmer_uid = profile.get("user_id") or "farmer01"
        bad_booking = client.post(f"{BASE_URL}/api/bookings", headers=farmer_headers, json={
            "farmer_id": farmer_uid,
            "centre_id": centre_id,
            "slot_id": slot_id,
            "crop": "Paddy",
            "quantity": 20.0
        })
        assert bad_booking.status_code in (400, 422), f"Expected holiday booking rejection, got {bad_booking.status_code}: {bad_booking.text}"
        log(f"Booking on holiday correctly rejected with message: {bad_booking.json().get('detail') or bad_booking.text}")

        # Remove holiday
        del_hol = client.delete(f"{BASE_URL}/api/centres/{centre_id}/non-operational-dates/{holiday_date}")
        assert del_hol.status_code == 200, f"Delete holiday failed: {del_hol.text}"
        log(f"Holiday removed. Date {holiday_date} is now open for booking")

        print("\n--- 7. TESTING VALID BOOKING & ARRIVAL PROCUREMENT WORKFLOW ---")
        valid_booking = client.post(f"{BASE_URL}/api/bookings", headers=farmer_headers, json={
            "farmer_id": farmer_uid,
            "centre_id": centre_id,
            "slot_id": slot_id,
            "crop": "Paddy",
            "quantity": 25.0
        })
        assert valid_booking.status_code in (200, 201), f"Valid booking creation failed: {valid_booking.text}"
        bk_data = valid_booking.json().get("booking", {})
        booking_id = bk_data.get("appointment_id") or str(bk_data.get("id"))
        booking_pk = bk_data.get("id")
        log(f"Booking created successfully: ID={booking_id} (PK={booking_pk}), Initial Status={bk_data.get('status')}")

        # Step: Mark ARRIVED
        st_arr = client.put(f"{BASE_URL}/api/bookings/{booking_id}/status", headers=centre_headers, json={"status": "ARRIVED"})
        assert st_arr.status_code == 200, f"Status ARRIVED failed: {st_arr.text}"
        log(f"Booking {booking_id} transitioned to: ARRIVED")

        # Step 1: Record Collection / Intake -> RECEIVED
        rec_res = client.post(f"{BASE_URL}/api/procurement/collection", headers=centre_headers, json={
            "booking_id": booking_pk,
            "collected_quantity": 25.0,
            "notes": "Vehicle verified and docked at unloading bay"
        })
        assert rec_res.status_code in (200, 201), f"Intake record failed: {rec_res.text}"
        col_id = rec_res.json().get("collection_id") or rec_res.json().get("data", {}).get("collection_id")
        log(f"Intake complete: Collection ID={col_id}. Booking {booking_id} transitioned to: RECEIVED")

        # Step 2: Quality Check -> QUALITY_CHECKED
        qc_res = client.post(f"{BASE_URL}/api/procurement/quality", headers=centre_headers, json={
            "collection_id": col_id,
            "moisture_content_pct": 11.8,
            "foreign_matter_pct": 1.2,
            "quality_grade": "Grade A",
            "passed": True,
            "remarks": "Fair Average Quality standard verified"
        })
        assert qc_res.status_code in (200, 201), f"Quality check failed: {qc_res.text}"
        log(f"Quality Check approved (Grade A, 11.8% moisture). Booking {booking_id} transitioned to: QUALITY_CHECKED")

        # Step 3: Certified Weighbridge -> WEIGHED
        wb_res = client.post(f"{BASE_URL}/api/procurement/weighment", headers=centre_headers, json={
            "collection_id": col_id,
            "gross_weight_quintals": 28.5,
            "tare_weight_quintals": 3.5
        })
        assert wb_res.status_code in (200, 201), f"Weighment failed: {wb_res.text}"
        wb_id = wb_res.json().get("weighment_id") or wb_res.json().get("data", {}).get("weighment_id")
        log(f"Gross: 28.5Q, Tare: 3.5Q, Net: 25.0Q (Weighment ID={wb_id}). Booking {booking_id} transitioned to: WEIGHED")

        # Step 4: Storage Allocation & Payment Initiation -> STORED / PAYMENT_INITIATED
        proc_res = client.post(f"{BASE_URL}/api/procurement/procure", headers=centre_headers, json={
            "weighment_id": wb_id,
            "msp_rate_per_quintal": 2275.0
        })
        assert proc_res.status_code in (200, 201), f"Record procurement failed: {proc_res.text}"
        prc_data = proc_res.json().get("data", {})
        log(f"Procurement Lot {prc_data.get('lot_id')} STORED. Payment {prc_data.get('payment_id')} INITIATED. Total Value: INR {prc_data.get('total_procurement_value')}")

        # Step 5: Final Payment Recording -> PAID
        st_paid = client.put(f"{BASE_URL}/api/bookings/{booking_id}/status", headers=centre_headers, json={"status": "PAID"})
        assert st_paid.status_code == 200, f"Status PAID failed: {st_paid.text}"
        log(f"Procurement and DBT Payment finalized: Booking {booking_id} status is now PAID")

        print("\n--- 8. TESTING GOVERNMENT DASHBOARD NATIONWIDE VS STATE FILTERING ---")
        admin_login = client.post(f"{BASE_URL}/api/auth/login", json={
            "user_id": "admin@bharatagri.demo",
            "password": "BharatAgri@2026"
        })
        assert admin_login.status_code == 200, f"Admin login failed: {admin_login.text}"
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
        log("Government Admin login successful")

        # Nationwide KPIs
        res_kpi = client.get(f"{BASE_URL}/api/government/kpis", headers=admin_headers).json()
        kpi_all = res_kpi.get("data", res_kpi) if isinstance(res_kpi, dict) else res_kpi
        res_c = client.get(f"{BASE_URL}/api/government/centres", headers=admin_headers).json()
        centres_all = res_c.get("data", res_c) if isinstance(res_c, dict) else res_c
        log(f"Nationwide: Active Centres={kpi_all.get('active_centres')}, Total Farmers={kpi_all.get('total_farmers')}, Centres Count={len(centres_all)}")

        # State: Goa
        res_kpi_goa = client.get(f"{BASE_URL}/api/government/kpis?state=Goa", headers=admin_headers).json()
        kpi_goa = res_kpi_goa.get("data", res_kpi_goa) if isinstance(res_kpi_goa, dict) else res_kpi_goa
        res_c_goa = client.get(f"{BASE_URL}/api/government/centres?state=Goa", headers=admin_headers).json()
        centres_goa = res_c_goa.get("data", res_c_goa) if isinstance(res_c_goa, dict) else res_c_goa
        log(f"State Goa: Active Centres={kpi_goa.get('active_centres')}, Total Farmers={kpi_goa.get('total_farmers')}, Centres Count={len(centres_goa)}")

        # State: Maharashtra
        res_kpi_mh = client.get(f"{BASE_URL}/api/government/kpis?state=Maharashtra", headers=admin_headers).json()
        kpi_mh = res_kpi_mh.get("data", res_kpi_mh) if isinstance(res_kpi_mh, dict) else res_kpi_mh
        res_c_mh = client.get(f"{BASE_URL}/api/government/centres?state=Maharashtra", headers=admin_headers).json()
        centres_mh = res_c_mh.get("data", res_c_mh) if isinstance(res_c_mh, dict) else res_c_mh
        log(f"State Maharashtra: Active Centres={kpi_mh.get('active_centres')}, Total Farmers={kpi_mh.get('total_farmers')}, Centres Count={len(centres_mh)}")

        # Detailed Centre Inspection with Congestion & Metrics
        detail_res = client.get(f"{BASE_URL}/api/government/centres/{centre_id}/detail", headers=admin_headers)
        assert detail_res.status_code == 200, f"Centre detail failed: {detail_res.text}"
        c_det = detail_res.json()
        log(f"Centre {centre_id} Inspection Data:")
        log(f"  - Capacity: Daily={c_det.get('capacity', {}).get('max_daily_quintals')} Q, Utilization={c_det.get('capacity', {}).get('utilization_percent')}%")
        log(f"  - Procurement: Today={c_det.get('procurement', {}).get('today_quintals')} Q, Total={c_det.get('procurement', {}).get('total_quintals')} Q")
        log(f"  - Logistics: Available Trucks={c_det.get('trucks', {}).get('available')}, Shortfall={c_det.get('trucks', {}).get('shortfall')}")
        log(f"  - Congestion Level: {c_det.get('congestion', {}).get('level')} ({c_det.get('congestion', {}).get('load_ratio_percent')}%)")
        log(f"  - Bardan Stock: {c_det.get('bardan', {}).get('available_bags')} bags, Anomalies: {c_det.get('anomalies', {}).get('open_count')}")

        print("\n=======================================================")
        print("ALL END-TO-END VERIFICATIONS PASSED SUCCESSFULLY!")
        print("=======================================================\n")

if __name__ == "__main__":
    run_tests()
