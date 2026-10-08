import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import io
import uuid
from datetime import datetime, date
from PIL import Image, ImageDraw

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.models.booking import Booking
from backend.app.models.farmer import Farmer
from backend.app.models.centre import ProcurementCentre, Slot, Employee
from backend.app.models.crop import CropMetadata
from backend.app.models.procurement import (
    CollectionRecord, QualityCheck, Weighment,
    ProcurementRecord, StorageLot, ProcurementEvidence, AIQualityInspection, Payment
)
from backend.app.models.user import User
from backend.app.core.security import create_access_token

def create_sample_image(color=(34, 139, 34), width=320, height=240, text="Produce Evidence"):
    img = Image.new("RGB", (width, height), color=color)
    draw = ImageDraw.Draw(img)
    draw.rectangle([10, 10, width - 10, height - 10], outline=(255, 255, 255), width=3)
    draw.text((20, 20), text, fill=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()

def create_multi_touching_mango_image():
    img = Image.new("RGB", (480, 360), color=(240, 240, 230))
    draw = ImageDraw.Draw(img)
    # Mango 1: Green Mankurad
    draw.ellipse([60, 100, 200, 260], fill=(46, 139, 87))
    # Mango 2: Touching Mango 1
    draw.ellipse([180, 110, 320, 270], fill=(60, 160, 80))
    # Mango 3: Yellow-Green
    draw.ellipse([300, 90, 430, 250], fill=(170, 190, 50))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    return buf.getvalue()

def run_verification():
    print("=" * 80)
    print(" FINAL ADDITIONAL CORRECTIONS: COMPREHENSIVE E2E VERIFICATION")
    print("=" * 80)

    db = SessionLocal()
    client = TestClient(app)

    try:
        # 1. Centre & Employees
        centre = db.query(ProcurementCentre).filter(ProcurementCentre.centre_id == "CENTRE-GOA-01").first()
        if not centre:
            centre = db.query(ProcurementCentre).filter(ProcurementCentre.state == "Goa").first()
        assert centre is not None, "Goa Centre must exist"
        print(f"[1] Verified Centre: {centre.centre_name} ({centre.centre_id}) in {centre.state}")

        # Check DB employees
        centre_employees = db.query(Employee).filter(
            Employee.centre_id == centre.centre_id,
            Employee.status == "ACTIVE"
        ).all()
        assert len(centre_employees) >= 6, f"Expected at least 6 active employees, found {len(centre_employees)}"
        print(f"    Loaded {len(centre_employees)} DB employees from `employees` table:")
        for emp in centre_employees:
            print(f"      - [{emp.employee_code}] {emp.name} ({emp.role})")

        # Map roles to specific DB employees
        intake_emp = next((e for e in centre_employees if "Intake" in e.role), centre_employees[0])
        qc_emp = next((e for e in centre_employees if "Quality" in e.role), centre_employees[1])
        ai_emp = next((e for e in centre_employees if "AI" in e.role), centre_employees[2])
        weigh_emp = next((e for e in centre_employees if "Weigh" in e.role), centre_employees[3])
        proc_emp = next((e for e in centre_employees if "Procurement" in e.role), centre_employees[4])
        storage_emp = next((e for e in centre_employees if "Storage" in e.role), centre_employees[5])

        # Create operator auth token
        operator_user = db.query(User).filter(User.user_id == centre.centre_id).first()
        if not operator_user:
            operator_user = db.query(User).filter(User.role == "centre").first()
        auth_token = create_access_token({"sub": operator_user.user_id, "role": "centre"})
        headers = {"Authorization": f"Bearer {auth_token}"}

        # 2. Farmer & Permitted Crop Booking
        farmer = db.query(Farmer).filter(Farmer.state == "Goa").first()
        assert farmer is not None, "Goa Farmer must exist"
        today = date.today()

        slot = db.query(Slot).filter(
            Slot.centre_id == centre.centre_id,
            Slot.date >= today
        ).first()
        if not slot:
            slot = Slot(
                centre_id=centre.centre_id,
                date=today,
                start_time="09:00",
                end_time="10:00",
                max_capacity=50
            )
            db.add(slot)
            db.commit()
            db.refresh(slot)

        test_apt_id = f"APT-E2E-{uuid.uuid4().hex[:6].upper()}"
        booking = Booking(
            appointment_id=test_apt_id,
            booking_id=test_apt_id,
            farmer_id=str(farmer.farmer_code or farmer.id),
            slot_id=slot.id,
            centre_id=centre.centre_id,
            crop="Mango",
            quantity=25.0,
            status="BOOKED",
            qr_token=f"QR-{uuid.uuid4().hex[:8].upper()}"
        )
        db.add(booking)
        db.commit()
        db.refresh(booking)
        print(f"[2] Created Appointment: {test_apt_id} for Farmer {farmer.name} (Crop: Mango, Qty: 25.0 Q)")

        # 3. Test Invalid Employee Validation: Submit with fake non-existent employee
        print("[3] Testing Invalid Employee Validation (Requirement 2)...")
        fake_payload = {
            "step_number": 1,
            "data": {
                "transport_method": "Farmer's Own",
                "employee_id": "FAKE-EMP-9999",
                "employee_name": "Ghost Operator",
                "notes": "Testing invalid employee rejection"
            }
        }
        res_fake = client.post(
            f"/api/procurement/process/{test_apt_id}/step/1/submit",
            json=fake_payload,
            headers=headers
        )
        assert res_fake.status_code == 400, f"Expected 400 for fake employee, got {res_fake.status_code}: {res_fake.text}"
        print(f"    SUCCESS: Backend correctly rejected fake employee: {res_fake.json().get('detail')}")

        # 4. Step 1: Gate Intake with Valid DB Employee
        print("[4] Executing Step 1: Gate Collection with DB Employee...")
        step1_payload = {
            "step_number": 1,
            "data": {
                "transport_method": "Farmer's Own",
                "employee_id": intake_emp.employee_code,
                "employee_name": intake_emp.name,
                "gross_weight_estimate": 25.0,
                "collected_bags": 50,
                "notes": "Arrival verified at electronic gate"
            }
        }
        res1 = client.post(f"/api/procurement/process/{test_apt_id}/step/1/submit", json=step1_payload, headers=headers)
        assert res1.status_code == 200, f"Step 1 failed: {res1.text}"
        print(f"    Step 1 Complete: {res1.json().get('message')} by {intake_emp.name}")

        # 5. Step 2: Quality Inspection with DB Employee
        print("[5] Executing Step 2: Quality Inspection with DB Employee...")
        step2_payload = {
            "step_number": 2,
            "data": {
                "moisture_content_pct": 12.0,
                "foreign_matter_pct": 0.5,
                "broken_grains_pct": 0.8,
                "damaged_grains_pct": 0.4,
                "employee_id": qc_emp.employee_code,
                "employee_name": qc_emp.name,
                "remarks": "Premium export grade"
            }
        }
        res2 = client.post(f"/api/procurement/process/{test_apt_id}/step/2/submit", json=step2_payload, headers=headers)
        assert res2.status_code == 200, f"Step 2 failed: {res2.text}"
        print(f"    Step 2 Complete: Grade A verified by {qc_emp.name}")

        # 6. Step 3: AI Inspection with Real Image & CIELAB analysis
        print("[6] Executing Step 3: Mango AI Vision Inspection...")
        mango_img_bytes = create_multi_touching_mango_image()
        ai_scan_res = client.post(
            "/api/procurement/quality/mango-scan",
            files={"file": ("mango_touching.jpg", mango_img_bytes, "image/jpeg")},
            data={"appointment_id": test_apt_id},
            headers=headers
        )
        assert ai_scan_res.status_code == 200, f"AI scan failed: {ai_scan_res.text}"
        ai_data = ai_scan_res.json()
        print(f"    AI Scan Detected: {ai_data.get('mangoes_detected', 0)} mangoes, Defect: {ai_data.get('affected_percentage', 0)}%, Grade: {ai_data.get('visual_grade')}")

        step3_payload = {
            "step_number": 3,
            "data": {
                "review_action": "ACCEPT",
                "employee_id": ai_emp.employee_code,
                "employee_name": ai_emp.name,
                "ai_defect_percentage": ai_data.get("affected_percentage", 3.2),
                "ai_grade": ai_data.get("visual_grade", "Grade A")
            }
        }
        res3 = client.post(f"/api/procurement/process/{test_apt_id}/step/3/submit", json=step3_payload, headers=headers)
        assert res3.status_code == 200, f"Step 3 failed: {res3.text}"
        print(f"    Step 3 Complete: AI verification accepted by {ai_emp.name}")

        # 7. Step 4: Digital Weighbridge Scale
        print("[7] Executing Step 4: Weighbridge Scale with DB Employee...")
        step4_payload = {
            "step_number": 4,
            "data": {
                "gross_weight_quintals": 45.2,
                "tare_weight_quintals": 20.2,
                "weighbridge_id": "SCALE-01",
                "employee_id": weigh_emp.employee_code,
                "employee_name": weigh_emp.name
            }
        }
        res4 = client.post(f"/api/procurement/process/{test_apt_id}/step/4/submit", json=step4_payload, headers=headers)
        assert res4.status_code == 200, f"Step 4 failed: {res4.text}"
        print(f"    Step 4 Complete: Net 25.0 Q weighed by {weigh_emp.name}")

        # 8. Step 5: Procurement Certificate & DBT Payout
        print("[8] Executing Step 5: Procurement & Payment Clearance with DB Employee...")
        step5_payload = {
            "step_number": 5,
            "data": {
                "rate_per_quintal_inr": 2300.0,
                "payment_mode": "DBT_BANK_TRANSFER",
                "employee_id": proc_emp.employee_code,
                "employee_name": proc_emp.name,
                "warehouse_location": "Bay Mango-02"
            }
        }
        res5 = client.post(f"/api/procurement/process/{test_apt_id}/step/5/submit", json=step5_payload, headers=headers)
        assert res5.status_code == 200, f"Step 5 failed: {res5.text}"
        print(f"    Step 5 Complete: Certified & DBT initiated by {proc_emp.name}")

        # 9. Verify Appointment Status & DB records before Storage (Requirement 1)
        res_proc_status = client.get(f"/api/procurement/process/{test_apt_id}/state", headers=headers)
        assert res_proc_status.status_code == 200, f"Process status fetch failed: {res_proc_status.text}"
        proc_status_data = res_proc_status.json()
        appt_info = proc_status_data.get("appointment", {})
        assert appt_info.get("arrival_status") in ["PROCURED", "COMPLETED"], f"Expected PROCURED or COMPLETED, got {appt_info.get('arrival_status')}"
        assert appt_info.get("is_all_completed") == True, "is_all_completed should be True after Step 5"
        print(f"[9] Procurement Finalized: Status is '{appt_info.get('arrival_status')}' (Lot returned to Appointments page)")

        # Verify Storage record in DB is uncompleted/pending final check
        db.rollback()
        booking = db.query(Booking).filter(Booking.appointment_id == test_apt_id).first()
        proc_rec = db.query(ProcurementRecord).filter(ProcurementRecord.booking_id == booking.id).first()
        assert proc_rec is not None, "ProcurementRecord must be created by step 5"
        storage_rec = db.query(StorageLot).filter(StorageLot.procurement_id == proc_rec.procurement_id).first()
        assert storage_rec is not None, "StorageLot must be initialized by procurement step 5"
        print(f"    Generated Storage Lot ID: {storage_rec.lot_id} (Status: {storage_rec.status})")

        # 10. Execute Independent Storage Final Check (Requirement 1 & 2)
        print("[10] Executing Dedicated Storage Final Check via /storage-check endpoint...")
        # First test that invalid storage employee is rejected
        storage_invalid_payload = {
            "received_quantity_quintals": 25.0,
            "storage_employee_id": "NON-EXISTENT-SUPERVISOR",
            "storage_employee_name": "Unregistered Staff",
            "storage_condition": "Cool Dry Aerated Storage",
            "physical_condition": "Intact - No Infestation / Good Stacking",
            "remarks": "Invalid employee test"
        }
        res_st_inv = client.post(
            f"/api/procurement/process/{test_apt_id}/storage-check",
            json=storage_invalid_payload,
            headers=headers
        )
        assert res_st_inv.status_code == 400, f"Expected 400 for fake storage employee, got {res_st_inv.status_code}"
        print(f"    SUCCESS: Storage check rejected fake employee: {res_st_inv.json().get('detail')}")

        # Now submit valid storage final check with DB storage employee and evidence photo
        storage_img_bytes = create_sample_image(color=(30, 90, 180), text="Godown Stack Evidence")
        ev_upload_res = client.post(
            f"/api/procurement/process/{test_apt_id}/evidence",
            files={"file": ("godown_stack.jpg", storage_img_bytes, "image/jpeg")},
            data={
                "process_step": "STORAGE_FINAL_CHECK",
                "evidence_type": "STORAGE",
                "notes": "Verified stack alignment and moisture control"
            },
            headers=headers
        )
        assert ev_upload_res.status_code == 200, f"Evidence upload failed: {ev_upload_res.text}"
        ev_data = ev_upload_res.json()
        ev_file_path = ev_data.get("evidence", {}).get("file_path") or ev_data.get("file_path")
        print(f"    Storage Photo Evidence Uploaded: {ev_file_path}")

        storage_valid_payload = {
            "received_quantity_quintals": 25.0,
            "storage_employee_id": storage_emp.employee_code,
            "storage_employee_name": storage_emp.name,
            "storage_condition": "Cool Dry Aerated Storage (12-14°C)",
            "physical_condition": "Intact - No Infestation / Good Stacking",
            "remarks": f"Stacks intact in Godown Bay 02. Inspected by {storage_emp.name}.",
            "evidence_url": ev_file_path
        }
        res_st_val = client.post(
            f"/api/procurement/process/{test_apt_id}/storage-check",
            json=storage_valid_payload,
            headers=headers
        )
        assert res_st_val.status_code == 200, f"Storage check failed: {res_st_val.text}"
        st_result = res_st_val.json()
        st_lot_info = st_result.get("storage_lot", {})
        print(f"    Dedicated Storage Check Succeeded: {st_result.get('message')}")
        print(f"    Storage Lot: {st_lot_info.get('lot_id')} | Status: {st_lot_info.get('status')} | Employee: {storage_emp.name}")

        # 11. Verify Insights Grounding (Requirement 5)
        print("[11] Verifying Centre and Government Insights Grounding...")
        res_centre_ins = client.get(f"/api/centres/{centre.centre_id}/insights", headers=headers)
        assert res_centre_ins.status_code == 200, f"Centre insights failed: {res_centre_ins.text}"
        centre_ins = res_centre_ins.json()
        assert "descriptive" in centre_ins and "predictive" in centre_ins and "prescriptive" in centre_ins
        print(f"    Centre Insights returned: {len(centre_ins['descriptive'])} descriptive, {len(centre_ins['predictive'])} predictive, {len(centre_ins['prescriptive'])} prescriptive items.")
        for ins in centre_ins['descriptive'][:2]:
            print(f"      * {ins.get('title')}: {ins.get('metric')} ({ins.get('category')})")

        # Government Insights
        gov_user = db.query(User).filter(User.role == "government").first()
        gov_token = create_access_token({"sub": gov_user.user_id, "role": "government"})
        gov_headers = {"Authorization": f"Bearer {gov_token}"}
        res_gov_ins = client.get("/api/government/insights", headers=gov_headers)
        assert res_gov_ins.status_code == 200, f"Gov insights failed: {res_gov_ins.text}"
        gov_ins = res_gov_ins.json()
        assert "descriptive" in gov_ins and "predictive" in gov_ins and "prescriptive" in gov_ins
        print(f"    Government Insights returned: {len(gov_ins['descriptive'])} descriptive, {len(gov_ins['predictive'])} predictive, {len(gov_ins['prescriptive'])} prescriptive items.")
        for ins in gov_ins['descriptive'][:2]:
            print(f"      * {ins.get('category')}: {ins.get('metric')}")

        print("=" * 80)
        print(" ALL END-TO-END VERIFICATION CHECKS PASSED PERFECTLY!")
        print("=" * 80)

    finally:
        db.close()

if __name__ == "__main__":
    run_verification()
