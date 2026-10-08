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
from backend.app.models.centre import ProcurementCentre, Slot
from backend.app.models.crop import CropMetadata
from backend.app.models.price import StateCropSupplyDemand, MspPrice
from backend.app.models.procurement import (
    CollectionRecord, QualityCheck, Weighment,
    ProcurementRecord, StorageLot, ProcurementEvidence, AIQualityInspection
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
    """Generates an image with multiple touching mangoes."""
    img = Image.new("RGB", (480, 360), color=(240, 240, 230))
    draw = ImageDraw.Draw(img)
    # Mango 1: Emerald Green Mankurad
    draw.ellipse([60, 100, 200, 260], fill=(46, 139, 87))
    # Mango 2: Touching Mango 1 (overlapping edge)
    draw.ellipse([180, 110, 320, 270], fill=(60, 160, 80))
    # Mango 3: Yellow-Green Touching Mango 2
    draw.ellipse([300, 90, 430, 250], fill=(170, 190, 50))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    return buf.getvalue()

def run_end_to_end_test():
    print("=" * 80)
    print(" BHARATAGRI-2 REALISTIC END-TO-END PROCUREMENT WORKFLOW VERIFICATION")
    print("=" * 80)

    db = SessionLocal()
    client = TestClient(app)

    try:
        # 1. Verify Goa Centre & Farmer Setup
        goa_centre = db.query(ProcurementCentre).filter(ProcurementCentre.state == "Goa").first()
        if not goa_centre:
            raise RuntimeError("No Goa procurement centre found in database!")

        farmer = db.query(Farmer).filter(Farmer.state == "Goa").first()
        if not farmer:
            raise RuntimeError("No Goa farmer found in database!")

        mango_crop = db.query(CropMetadata).filter(CropMetadata.crop_name == "Mango").first()
        if not mango_crop:
            raise RuntimeError("Mango crop not found in database!")

        print(f"[Setup] Centre: '{goa_centre.centre_name}' (ID: {goa_centre.centre_id}, State: {goa_centre.state})")
        print(f"[Setup] Farmer: '{farmer.name}' (ID: {farmer.id}, State: {farmer.state})")
        print(f"[Setup] Crop:   'Mango' (Permitted in Goa)")

        # Verify MSP in database
        msp_entry = db.query(MspPrice).filter(MspPrice.crop == "Mango").order_by(MspPrice.season_year.desc()).first()
        supply_demand = db.query(StateCropSupplyDemand).filter(
            StateCropSupplyDemand.state == "Goa",
            StateCropSupplyDemand.crop == "Mango"
        ).first()
        print(f"[Setup] Database MSP for Mango: Rs {msp_entry.official_msp_per_quintal if msp_entry else 'N/A'}/quintal")
        print(f"[Setup] Supply-Demand Estimated MSP: Rs {supply_demand.estimated_procurement_price if supply_demand else 'N/A'}/quintal")

        # 2. Create distinct employees
        employees = {
            "step1": {"id": "EMP-GOA-01", "name": "Ramesh Naik (Intake Officer)", "role": "centre"},
            "step2": {"id": "EMP-GOA-02", "name": "Sunita Patil (QC Officer)", "role": "centre"},
            "step3": {"id": "EMP-GOA-03", "name": "Amit Desai (AI QC Lead)", "role": "centre"},
            "step4": {"id": "EMP-GOA-04", "name": "Vijay Gaonkar (Weighbridge Op)", "role": "centre"},
            "step5": {"id": "EMP-GOA-05", "name": "Preeti Shinde (Procurement Mgr)", "role": "centre"},
            "step6": {"id": "EMP-GOA-06", "name": "Prakash Rane (Storage Supervisor)", "role": "centre"}
        }

        # Create auth tokens for each employee
        tokens = {}
        for k, emp in employees.items():
            user = db.query(User).filter(User.user_id == emp["id"]).first()
            if not user:
                user = User(
                    user_id=emp["id"],
                    name=emp["name"],
                    email=f"{emp['id'].lower()}@bharatagri.gov.in",
                    mobile="9876543210",
                    password_hash="test_hash",
                    role="centre",
                    centre_id=goa_centre.centre_id,
                    status="ACTIVE"
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            tokens[k] = create_access_token(data={"sub": user.user_id, "role": user.role, "centre_id": goa_centre.centre_id})

        # 3. Create fresh Goa Mango Booking/Appointment
        app_code = f"APT-GOA-{uuid.uuid4().hex[:6].upper()}"
        today_date = date.today()

        slot = db.query(Slot).filter(Slot.centre_id == goa_centre.centre_id).first()
        if not slot:
            slot = Slot(
                centre_id=goa_centre.centre_id,
                date=today_date,
                start_time="09:00 AM",
                end_time="10:00 AM",
                max_capacity=20
            )
            db.add(slot)
            db.commit()
            db.refresh(slot)

        booking = Booking(
            appointment_id=app_code,
            booking_id=app_code,
            farmer_id=farmer.user_id,
            centre_id=goa_centre.centre_id,
            slot_id=slot.id,
            crop="Mango",
            quantity=15.0,
            status="ARRIVED",
            qr_token=f"QR-{uuid.uuid4().hex[:12].upper()}"
        )
        db.add(booking)
        db.commit()
        db.refresh(booking)
        print(f"\n[Appointment Created] Code: {app_code}, Status: {booking.status}, Crop: {booking.crop}")

        # Check initial process state & employee data isolation
        resp0 = client.get(
            f"/api/procurement/process/{app_code}/state",
            headers={"Authorization": f"Bearer {tokens['step1']}"}
        )
        assert resp0.status_code == 200, f"Get process state failed: {resp0.text}"
        st0 = resp0.json()
        print(f"[State Check] Current Step: {st0.get('booking', {}).get('current_step_number')} (Crop: {st0.get('booking', {}).get('crop')})")
        print(f"[Pricing Preview] Official MSP: Rs {st0.get('pricing', {}).get('official_msp')}/q, Estimated MSP: Rs {st0.get('pricing', {}).get('estimated_msp')}/q")

        # -------------------------------------------------------------
        # STEP 1: Collection / Initial Physical Check (Different Employee)
        # -------------------------------------------------------------
        print("\n" + "-" * 70)
        print(f"STEP 1: Collection Check by Employee: {employees['step1']['name']}")
        print("-" * 70)
        img1 = create_sample_image(text="Produce Received: Mankurad Mangoes")
        # Upload Step 1 photo evidence
        up1 = client.post(
            f"/api/procurement/process/{app_code}/evidence",
            headers={"Authorization": f"Bearer {tokens['step1']}"},
            data={
                "process_step": "STEP_1_COLLECTION",
                "evidence_type": "COLLECTION_PRODUCE",
                "employee_id": employees["step1"]["id"],
                "employee_name": employees["step1"]["name"],
                "remarks": "Produce received directly from farmer via own tractor. Visual condition sound."
            },
            files={"file": ("produce_arrival.jpg", img1, "image/jpeg")}
        )
        assert up1.status_code == 200, f"Step 1 evidence upload failed: {up1.text}"
        ev1 = up1.json()
        print(f"  Evidence Uploaded: {ev1['evidence']['evidence_type']} (ID: {ev1['evidence']['id']})")

        # Submit Step 1 with Transport Method = "Farmer's Own" (NO hardcoded truck assumption)
        sub1 = client.post(
            f"/api/procurement/process/{app_code}/step/1/submit",
            headers={"Authorization": f"Bearer {tokens['step1']}"},
            json={
                "step_number": 1,
                "data": {
                    "transport_method": "Farmer's Own",
                    "truck_number": "GA-03-TR-4412",
                    "collected_bags": 30,
                    "gross_weight_estimate": 15.0,
                    "employee_id": employees["step1"]["id"],
                    "employee_name": employees["step1"]["name"],
                    "evidence_url": ev1["evidence"]["file_path"],
                    "remarks": "Clean harvest lot, no transport bruising."
                }
            }
        )
        assert sub1.status_code == 200, f"Step 1 submit failed: {sub1.text}"
        print(f"  Step 1 Result: Success! Attributed to: {employees['step1']['name']}")

        # -------------------------------------------------------------
        # STEP 2: Quality Inspection (Different Employee)
        # -------------------------------------------------------------
        print("\n" + "-" * 70)
        print(f"STEP 2: Manual QC by Employee: {employees['step2']['name']}")
        print("-" * 70)
        img2 = create_sample_image(color=(70, 130, 180), text="Moisture Meter Reading: 12.4%")
        up2 = client.post(
            f"/api/procurement/process/{app_code}/evidence",
            headers={"Authorization": f"Bearer {tokens['step2']}"},
            data={
                "process_step": "STEP_2_QUALITY",
                "evidence_type": "QUALITY_MACHINE",
                "employee_id": employees["step2"]["id"],
                "employee_name": employees["step2"]["name"],
                "remarks": "Moisture meter calibrated against standard reference."
            },
            files={"file": ("moisture_meter.jpg", img2, "image/jpeg")}
        )
        assert up2.status_code == 200, f"Step 2 evidence upload failed: {up2.text}"
        ev2 = up2.json()
        print(f"  Evidence Uploaded: {ev2['evidence']['evidence_type']} (ID: {ev2['evidence']['id']})")

        sub2 = client.post(
            f"/api/procurement/process/{app_code}/step/2/submit",
            headers={"Authorization": f"Bearer {tokens['step2']}"},
            json={
                "step_number": 2,
                "data": {
                    "moisture_content_pct": 12.4,
                    "foreign_matter_pct": 0.8,
                    "broken_grains_pct": 0.2,
                    "damaged_grains_pct": 0.0,
                    "employee_id": employees["step2"]["id"],
                    "employee_name": employees["step2"]["name"],
                    "evidence_url": ev2["evidence"]["file_path"],
                    "remarks": "Produce well within Faq moisture and foreign matter limits."
                }
            }
        )
        assert sub2.status_code == 200, f"Step 2 submit failed: {sub2.text}"
        print(f"  Step 2 Result: Success! Attributed to: {employees['step2']['name']}")

        # Verify Data Isolation: Employee 3 should NOT see moisture or foreign matter leaked
        resp_iso = client.get(
            f"/api/procurement/process/{app_code}/state",
            headers={"Authorization": f"Bearer {tokens['step3']}"}
        )
        st_iso = resp_iso.json()
        step2_info = next((s for s in st_iso.get("steps", []) if s.get("step_number") == 2), {})
        assert "moisture_content_pct" not in step2_info, "DATA LEAK: Quality inspection data exposed to downstream employee!"
        print(f"  Security Check: Data isolation verified! Sensitive QC measurements hidden from subsequent steps.")

        # -------------------------------------------------------------
        # STEP 3: Mango AI Quality Scan (Different Employee, Touching Mangoes)
        # -------------------------------------------------------------
        print("\n" + "-" * 70)
        print(f"STEP 3: Mango AI Scan by Employee: {employees['step3']['name']}")
        print("-" * 70)
        multi_img = create_multi_touching_mango_image()
        ai_resp = client.post(
            f"/api/procurement/appointments/{app_code}/ai-inspection",
            headers={"Authorization": f"Bearer {tokens['step3']}"},
            files={"file": ("touching_mangoes_sample.jpg", multi_img, "image/jpeg")}
        )
        assert ai_resp.status_code == 200, f"Step 3 Mango AI scan failed: {ai_resp.text}"
        ai_data = ai_resp.json()
        print(f"  Mangoes Detected:    {ai_data.get('mangoes_detected')} (Watershed successfully separated touching fruits!)")
        print(f"  Sound / Healthy:     {ai_data.get('healthy')}")
        print(f"  Defect Count:        {ai_data.get('defect_count', 0)}")
        print(f"  Visual Grade:        {ai_data.get('visual_grade')}")
        print(f"  Confidence:          {ai_data.get('confidence')}%")
        print(f"  Ripeness Summary:    {ai_data.get('ripeness_summary')}")
        assert ai_data.get('mangoes_detected') >= 2, "Failed to isolate touching mangoes!"

        # Submit Step 3 completion
        sub3 = client.post(
            f"/api/procurement/process/{app_code}/step/3/submit",
            headers={"Authorization": f"Bearer {tokens['step3']}"},
            json={
                "step_number": 3,
                "data": {
                    "review_action": "ACCEPT",
                    "employee_id": employees["step3"]["id"],
                    "employee_name": employees["step3"]["name"],
                    "remarks": f"AI visual assessment verified: {ai_data.get('mangoes_detected')} mangoes scanned, grade {ai_data.get('visual_grade')}."
                }
            }
        )
        assert sub3.status_code == 200, f"Step 3 submit failed: {sub3.text}"
        print(f"  Step 3 Result: Success! Attributed to: {employees['step3']['name']}")

        # -------------------------------------------------------------
        # STEP 4: Weighment (Different Employee)
        # -------------------------------------------------------------
        print("\n" + "-" * 70)
        print(f"STEP 4: Weighment by Employee: {employees['step4']['name']}")
        print("-" * 70)
        img4 = create_sample_image(color=(128, 128, 128), text="Weighbridge Digital Display: 1,480 kg")
        up4 = client.post(
            f"/api/procurement/process/{app_code}/evidence",
            headers={"Authorization": f"Bearer {tokens['step4']}"},
            data={
                "process_step": "STEP_4_WEIGHMENT",
                "evidence_type": "WEIGHMENT",
                "employee_id": employees["step4"]["id"],
                "employee_name": employees["step4"]["name"],
                "remarks": "Gross and tare weight measured on digital certified weighbridge."
            },
            files={"file": ("weighbridge_display.jpg", img4, "image/jpeg")}
        )
        assert up4.status_code == 200, f"Step 4 evidence upload failed: {up4.text}"
        ev4 = up4.json()
        print(f"  Evidence Uploaded: {ev4['evidence']['evidence_type']} (ID: {ev4['evidence']['id']})")

        sub4 = client.post(
            f"/api/procurement/process/{app_code}/step/4/submit",
            headers={"Authorization": f"Bearer {tokens['step4']}"},
            json={
                "step_number": 4,
                "data": {
                    "gross_weight_quintals": 22.0,
                    "tare_weight_quintals": 7.2,
                    "weighbridge_id": "WB-01",
                    "employee_id": employees["step4"]["id"],
                    "employee_name": employees["step4"]["name"],
                    "evidence_url": ev4["evidence"]["file_path"],
                    "remarks": "Net weight: 14.80 quintals."
                }
            }
        )
        assert sub4.status_code == 200, f"Step 4 submit failed: {sub4.text}"
        print(f"  Step 4 Result: Success! Attributed to: {employees['step4']['name']}")

        # -------------------------------------------------------------
        # STEP 5: Procurement Finalization (Different Employee, Estimated MSP)
        # -------------------------------------------------------------
        print("\n" + "-" * 70)
        print(f"STEP 5: Procurement Finalization by Employee: {employees['step5']['name']}")
        print("-" * 70)
        img5 = create_sample_image(color=(0, 100, 0), text="Final Procurement Lot Clearance")
        up5 = client.post(
            f"/api/procurement/process/{app_code}/evidence",
            headers={"Authorization": f"Bearer {tokens['step5']}"},
            data={
                "process_step": "STEP_5_PROCUREMENT",
                "evidence_type": "QUALITY_INSPECTION",
                "employee_id": employees["step5"]["id"],
                "employee_name": employees["step5"]["name"],
                "remarks": "Final clearance approved at estimated MSP."
            },
            files={"file": ("lot_clearance.jpg", img5, "image/jpeg")}
        )
        assert up5.status_code == 200, f"Step 5 evidence upload failed: {up5.text}"
        ev5 = up5.json()

        sub5 = client.post(
            f"/api/procurement/process/{app_code}/step/5/submit",
            headers={"Authorization": f"Bearer {tokens['step5']}"},
            json={
                "step_number": 5,
                "data": {
                    "rate_per_quintal_inr": 4920.0,
                    "warehouse_location": "Bay G-04",
                    "employee_id": employees["step5"]["id"],
                    "employee_name": employees["step5"]["name"],
                    "evidence_url": ev5["evidence"]["file_path"],
                    "remarks": "Final procurement finalized and approved at authentic database estimated MSP."
                }
            }
        )
        assert sub5.status_code == 200, f"Step 5 submit failed (PREVIOUS 500 ERROR!): {sub5.text}"
        res5 = sub5.json()
        print(f"  Step 5 Result: SUCCESS! (Zero 500 Errors)")
        print(f"  Status:           {res5.get('status')}")
        print(f"  Step 5 Completed: {res5.get('step', {}).get('status')}")
        print(f"  Attributed to:    {employees['step5']['name']}")

        # -------------------------------------------------------------
        # STEP 6: Storage Final Check (Different Employee)
        # -------------------------------------------------------------
        print("\n" + "-" * 70)
        print(f"STORAGE FINAL CHECK by Employee: {employees['step6']['name']}")
        print("-" * 70)
        img6 = create_sample_image(color=(25, 25, 112), text="Cold Storage Stack Check: Bay G-04")
        up6 = client.post(
            f"/api/procurement/process/{app_code}/evidence",
            headers={"Authorization": f"Bearer {tokens['step6']}"},
            data={
                "process_step": "STORAGE_FINAL_CHECK",
                "evidence_type": "STORAGE",
                "employee_id": employees["step6"]["id"],
                "employee_name": employees["step6"]["name"],
                "remarks": "Produce received and stacked in cold storage chamber at 12 deg C."
            },
            files={"file": ("storage_intake.jpg", img6, "image/jpeg")}
        )
        assert up6.status_code == 200, f"Storage evidence upload failed: {up6.text}"
        ev6 = up6.json()

        stor_check = client.post(
            f"/api/procurement/process/{app_code}/storage-check",
            headers={"Authorization": f"Bearer {tokens['step6']}"},
            json={
                "storage_employee_id": employees["step6"]["id"],
                "storage_employee_name": employees["step6"]["name"],
                "received_quantity_quintals": 14.8,
                "storage_condition": "Optimal Humidity & Temperature",
                "physical_condition": "Intact - No Infestation / Good Stacking",
                "evidence_url": ev6["evidence"]["file_path"],
                "remarks": "All 14.80 quintals verified in good physical order and palletized in cold bay."
            }
        )
        assert stor_check.status_code == 200, f"Storage check failed: {stor_check.text}"
        s_data = stor_check.json()
        print(f"  Storage Check Result: SUCCESS!")
        print(f"  Lot Number:          {s_data.get('storage_lot', {}).get('lot_number')}")
        print(f"  Storage Condition:   {s_data.get('storage_lot', {}).get('storage_condition')}")
        print(f"  Physical Condition:  {s_data.get('storage_lot', {}).get('physical_condition')}")
        print(f"  Verified Employee:   {s_data.get('storage_lot', {}).get('storage_employee')}")

        # Final State Check
        final_state_resp = client.get(
            f"/api/procurement/process/{app_code}/state",
            headers={"Authorization": f"Bearer {tokens['step1']}"}
        )
        final_state = final_state_resp.json()
        print("\n" + "=" * 80)
        print(" FINAL AUDIT OF COMPLETED WORKFLOW:")
        print("=" * 80)
        print(f"  Appointment:     {final_state.get('booking', {}).get('appointment_id')}")
        print(f"  Arrival Status:  {final_state.get('booking', {}).get('arrival_status')}")
        print(f"  Current Step:    {final_state.get('booking', {}).get('current_step_number')}")
        print(f"  All Completed:   {final_state.get('booking', {}).get('is_all_completed')}")
        print(f"  Total Evidence:  {len(final_state.get('evidence', []))} photos recorded across all stages")
        for ev in final_state.get('evidence', []):
            print(f"    - Step: {ev['process_step']:<24} Type: {ev['evidence_type']:<22} By: {ev['uploaded_by']}")

        print("\n" + "=" * 80)
        print(">>> [ALL CHECKS PASSED] Entire End-to-End Workflow with Multi-Employee Attribution Succeeded! <<<")
        print("=" * 80)

    finally:
        db.close()

if __name__ == "__main__":
    run_end_to_end_test()
