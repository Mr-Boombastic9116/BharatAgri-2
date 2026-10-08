import os
import sys
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.core.database import SessionLocal
from backend.app.core.security import get_password_hash
from backend.app.models.user import User
from backend.app.models.farmer import Farmer, FarmerCrop
from backend.app.models.centre import ProcurementCentre, Slot, DailyCapacity
from backend.app.models.booking import Booking, QRCode
from backend.app.models.queue import Appointment, ProcurementTransaction, Notification, QueueEvent, CentreDailyMetric
from backend.app.models.procurement import (
    CollectionRecord, QualityCheck, Weighment,
    ProcurementRecord, StorageLot, Payment, AIQualityInspection, AIInspectionDetection
)

def seed_mango_demo_centre():
    db = SessionLocal()
    print("=" * 80)
    print(" SEEDING COHERENT MANGO DEMO CENTRE (PC-GOA-01) OPERATIONAL ECOSYSTEM")
    print("=" * 80)

    try:
        # 1. Verify or create PC-GOA-01 Centre
        centre = db.query(ProcurementCentre).filter(ProcurementCentre.centre_id == "PC-GOA-01").first()
        if not centre:
            centre = ProcurementCentre(
                centre_id="PC-GOA-01",
                centre_name="Panaji Apex APMC Yard",
                location="Panaji Market Road, North Goa",
                state="Goa",
                district="North Goa",
                contact_number="0832-2420111",
                operating_days="Monday,Tuesday,Wednesday,Thursday,Friday,Saturday",
                opening_time="08:30 AM",
                closing_time="05:00 PM",
                supported_crops="Mango,Banana,Tomato",
                max_daily_capacity_quintals=600.0,
                total_storage_capacity_quintals=12000.0,
                current_storage_usage_quintals=1850.0,
                daily_capacity_farmers=90,
                weighing_machines=2,
                quality_stations=2,
                staff_count=8,
                status="OPERATIONAL"
            )
            db.add(centre)
            db.flush()
        else:
            centre.supported_crops = "Mango,Banana,Tomato"
            centre.state = "Goa"
            centre.district = "North Goa"
            centre.status = "OPERATIONAL"
            db.flush()

        print(f"[OK] Centre Verified: {centre.centre_name} ({centre.centre_id}) | Supported: {centre.supported_crops}")

        # 2. Daily capacity & operating slots for PC-GOA-01
        today = date.today()
        dates_to_seed = [today - timedelta(days=7), today - timedelta(days=5), today, today + timedelta(days=1), today + timedelta(days=2)]
        slot_times = [
            ("08:30 AM", "09:00 AM"),
            ("09:30 AM", "10:00 AM"),
            ("10:30 AM", "11:00 AM"),
            ("11:30 AM", "12:00 PM"),
            ("01:30 PM", "02:00 PM"),
            ("02:30 PM", "03:00 PM"),
            ("03:30 PM", "04:00 PM")
        ]

        slot_map = {}
        for d in dates_to_seed:
            cap = db.query(DailyCapacity).filter(DailyCapacity.centre_id == "PC-GOA-01", DailyCapacity.date == d).first()
            if not cap:
                db.add(DailyCapacity(centre_id="PC-GOA-01", date=d, max_quintals_per_day=600.0))
            for st, et in slot_times:
                s = db.query(Slot).filter(Slot.centre_id == "PC-GOA-01", Slot.date == d, Slot.start_time == st).first()
                if not s:
                    s = Slot(centre_id="PC-GOA-01", date=d, start_time=st, end_time=et, max_capacity=15)
                    db.add(s)
                    db.flush()
                slot_map[(str(d), st)] = s.id

        db.commit()
        print("[OK] Centre Slots & Daily Capacity Configured.")

        # 3. Create / Update Realistic Mango Farmers in Goa
        goa_farmers_meta = [
            {
                "farmer_code": "F-GOA-901",
                "user_id": "F-GOA-901",
                "login_username": "farmer_goa_1",
                "name": "Ramesh Rane",
                "mobile": "9823101111",
                "village": "Bicholim",
                "taluka": "Bicholim",
                "land_ha": 2.50,
                "crop": "Mango",
                "qty_q": 45.0,
                "bank": "State Bank of India",
                "acc": "304928174821",
                "ifsc": "SBIN0001234"
            },
            {
                "farmer_code": "F-GOA-902",
                "user_id": "F-GOA-902",
                "login_username": "farmer_goa_2",
                "name": "Antonio Fernandes",
                "mobile": "9823102222",
                "village": "Ponda",
                "taluka": "Ponda",
                "land_ha": 3.20,
                "crop": "Mango",
                "qty_q": 60.0,
                "bank": "HDFC Bank",
                "acc": "501004829102",
                "ifsc": "HDFC0000456"
            },
            {
                "farmer_code": "F-GOA-903",
                "user_id": "F-GOA-903",
                "login_username": "farmer_goa_3",
                "name": "Deepa Sawant",
                "mobile": "9823103333",
                "village": "Sattari",
                "taluka": "Sattari",
                "land_ha": 1.80,
                "crop": "Mango",
                "qty_q": 35.0,
                "bank": "Canara Bank",
                "acc": "284910284729",
                "ifsc": "CNRB0002345"
            }
        ]

        for fm in goa_farmers_meta:
            # User account
            u = db.query(User).filter((User.user_id == fm["user_id"]) | (User.email == f"{fm['login_username']}@bharatagri.com")).first()
            if not u:
                u = User(
                    user_id=fm["user_id"],
                    email=f"{fm['login_username']}@bharatagri.com",
                    password_hash=get_password_hash("farmer123"),
                    role="farmer",
                    name=fm["name"],
                    mobile=fm["mobile"],
                    status="ACTIVE"
                )
                db.add(u)
                db.flush()

            # Farmer profile
            f = db.query(Farmer).filter((Farmer.farmer_code == fm["farmer_code"]) | (Farmer.user_id == fm["user_id"])).first()
            if not f:
                f = Farmer(
                    farmer_code=fm["farmer_code"],
                    user_id=fm["user_id"],
                    name=fm["name"],
                    mobile=fm["mobile"],
                    email=f"{fm['login_username']}@bharatagri.com",
                    state="Goa",
                    district="North Goa",
                    taluka=fm["taluka"],
                    village=fm["village"],
                    address=f"{fm['village']}, {fm['taluka']}, North Goa",
                    land_area_hectares=Decimal(str(fm["land_ha"])),
                    ekyc_status="VERIFIED",
                    aadhaar_masked="XXXX-XXXX-9821",
                    bank_name=fm["bank"],
                    bank_account_no=fm["acc"],
                    bank_ifsc=fm["ifsc"]
                )
                db.add(f)
                db.flush()
            else:
                f.state = "Goa"
                f.district = "North Goa"
                f.bank_name = fm["bank"]
                f.bank_account_no = fm["acc"]
                f.bank_ifsc = fm["ifsc"]

            # FarmerCrop registration
            fc = db.query(FarmerCrop).filter(FarmerCrop.farmer_id == f.id, FarmerCrop.crop_name == "Mango").first()
            if not fc:
                fc = FarmerCrop(
                    farmer_id=f.id,
                    crop_name="Mango",
                    season="Summer 2026",
                    sowing_date=date(2025, 11, 15),
                    expected_harvest_date=date(2026, 4, 15),
                    estimated_quantity_quintals=Decimal(str(fm["qty_q"]))
                )
                db.add(fc)
                db.flush()

        db.commit()
        print("[OK] Mango Farmers & Registered Crops Created/Verified.")

        # 4. Clean up the 36 dangling test bookings (PF-TEST-...)
        old_test_bks = db.query(Booking).filter(Booking.appointment_id.like("PF-TEST-%")).all()
        if old_test_bks:
            for ot in old_test_bks:
                db.delete(ot)
            db.commit()
            print(f"[OK] Removed {len(old_test_bks)} dangling test booking placeholders.")

        # Also repair F00001's stray appointment PF-261007-353 to Cotton (F00001's valid crop)
        stray_appt = db.query(Appointment).filter(Appointment.appointment_id == "PF-261007-353").first()
        if stray_appt:
            stray_appt.crop = "Cotton"
            stray_appt.centre_id = "C001"
            stray_bk = db.query(Booking).filter(Booking.appointment_id == "PF-261007-353").first()
            if stray_bk:
                stray_bk.crop = "Cotton"
                stray_bk.centre_id = "C001"
            db.commit()
            print("[OK] Repaired stray appointment PF-261007-353 to Cotton at C001.")

        # 5. Build Coherent End-to-End Operational Mango Records
        # Record 1: Historical Completed Mango Procurement
        # Farmer: F-GOA-901 | Date: 7 days ago | Actual: 24.5 Quintals | Grade A
        d_hist1 = today - timedelta(days=7)
        appt_id_1 = f"PF-{d_hist1.strftime('%y%m%d')}-901"
        slot_id_1 = slot_map.get((str(d_hist1), "09:30 AM"), 1)

        b1 = db.query(Booking).filter(Booking.appointment_id == appt_id_1).first()
        if not b1:
            b1 = Booking(
                appointment_id=appt_id_1,
                booking_id=appt_id_1,
                farmer_id="F-GOA-901",
                centre_id="PC-GOA-01",
                slot_id=slot_id_1,
                crop="Mango",
                quantity=Decimal("25.00"),
                status="COMPLETED",
                qr_token=f"BA-QR-{appt_id_1}"
            )
            db.add(b1)
            db.flush()

        a1 = db.query(Appointment).filter(Appointment.appointment_id == appt_id_1).first()
        if not a1:
            a1 = Appointment(
                appointment_id=appt_id_1,
                farmer_id="F-GOA-901",
                centre_id="PC-GOA-01",
                appointment_date=d_hist1,
                slot_start=datetime.combine(d_hist1, datetime.strptime("09:30", "%H:%M").time()),
                slot_duration_min=30,
                queue_before=2,
                active_weighing_machines=2,
                staff_available=8,
                predicted_wait_min=Decimal("12.0"),
                actual_wait_min=Decimal("14.0"),
                status="COMPLETED",
                crop="Mango",
                quantity_quintals=Decimal("25.00"),
                token_number="A101",
                qr_token=f"BA-QR-{appt_id_1}"
            )
            db.add(a1)
            db.flush()

        # Step 1 Collection
        col1 = db.query(CollectionRecord).filter(CollectionRecord.collection_id == f"COL-{appt_id_1}").first()
        if not col1:
            col1 = CollectionRecord(
                collection_id=f"COL-{appt_id_1}",
                booking_id=b1.id,
                farmer_id="F-GOA-901",
                centre_id="PC-GOA-01",
                crop="Mango",
                collected_quantity=Decimal("24.50"),
                collection_date=d_hist1,
                truck_number="GA-03-T-4819",
                collected_by="Officer Shrikant Naik",
                status="COLLECTED"
            )
            db.add(col1)
            db.flush()

        # Step 2 Quality & Weighment
        qc1 = db.query(QualityCheck).filter(QualityCheck.check_id == f"QC-{appt_id_1}").first()
        if not qc1:
            qc1 = QualityCheck(
                check_id=f"QC-{appt_id_1}",
                collection_id=col1.collection_id,
                moisture_content_pct=Decimal("11.50"),
                foreign_matter_pct=Decimal("0.40"),
                broken_grains_pct=Decimal("0.00"),
                quality_grade="GRADE_A",
                inspector_name="K. Parab",
                passed=True,
                remarks="Premium Mankurad mangoes, excellent sound condition."
            )
            db.add(qc1)

        wm1 = db.query(Weighment).filter(Weighment.weighment_id == f"WM-{appt_id_1}").first()
        if not wm1:
            wm1 = Weighment(
                weighment_id=f"WM-{appt_id_1}",
                collection_id=col1.collection_id,
                gross_weight_quintals=Decimal("28.20"),
                tare_weight_quintals=Decimal("3.70"),
                net_weight_quintals=Decimal("24.50"),
                operator_name="Mahesh Borkar"
            )
            db.add(wm1)

        # AI Inspection Record
        ai1 = db.query(AIQualityInspection).filter(AIQualityInspection.inspection_code == f"AI-QC-PC-GOA-01-901").first()
        if not ai1:
            ai1 = AIQualityInspection(
                inspection_code="AI-QC-PC-GOA-01-901",
                booking_id=b1.id,
                appointment_id=appt_id_1,
                centre_id="PC-GOA-01",
                crop="Mango",
                image_path="/uploads/mango_inspections/sample_mango_healthy.jpg",
                annotated_image_path="/uploads/mango_inspections/sample_mango_healthy_annotated.jpg",
                model_version="mango-quality-v2",
                model_type="CIELAB SVM+KNN (L*a*b* & a*b*)",
                sample_count=24,
                healthy_count=23,
                defect_count=1,
                anthracnose_count=0,
                scab_count=1,
                bacterial_canker_count=0,
                stem_end_rot_count=0,
                other_count=0,
                ripe_count=20,
                nearly_ripe_count=4,
                not_ripe_count=0,
                uncertain_count=0,
                affected_percentage=Decimal("0.80"),
                visual_grade="Grade A",
                confidence=Decimal("94.50"),
                status="COMPLETED",
                reviewed_by="Shrikant Naik"
            )
            db.add(ai1)

        # Step 4 Procurement Record
        proc1 = db.query(ProcurementRecord).filter(ProcurementRecord.procurement_id == f"PR-{appt_id_1}").first()
        if not proc1:
            proc1 = ProcurementRecord(
                procurement_id=f"PR-{appt_id_1}",
                booking_id=b1.id,
                collection_id=col1.collection_id,
                farmer_id="F-GOA-901",
                centre_id="PC-GOA-01",
                crop="Mango",
                quality_grade="GRADE_A",
                moisture_content_pct=Decimal("11.50"),
                procured_quantity_quintals=Decimal("24.50"),
                msp_rate_per_quintal=Decimal("3200.00"),
                total_procurement_value=Decimal("78400.00"),
                status="CONFIRMED",
                warehouse_location="Cold Storage Bay 1, Panaji Yard"
            )
            db.add(proc1)
            db.flush()

        # Step 5 Payment
        pay1 = db.query(Payment).filter(Payment.payment_id == f"PAY-{appt_id_1}").first()
        if not pay1:
            pay1 = Payment(
                payment_id=f"PAY-{appt_id_1}",
                procurement_id=proc1.procurement_id,
                farmer_id="F-GOA-901",
                amount=Decimal("78400.00"),
                msp_rate=Decimal("3200.00"),
                quantity_quintals=Decimal("24.50"),
                payment_mode="DBT_NEFT",
                payment_status="PAID",
                transaction_ref=f"DBT{d_hist1.strftime('%Y%m%d')}90124",
                paid_at=datetime.combine(d_hist1, datetime.strptime("16:30", "%H:%M").time()),
                remarks="Direct Benefit Transfer disbursed successfully to SBI account."
            )
            db.add(pay1)

        pt1 = db.query(ProcurementTransaction).filter(ProcurementTransaction.procurement_id == f"PR-{appt_id_1}").first()
        if not pt1:
            pt1 = ProcurementTransaction(
                procurement_id=f"PR-{appt_id_1}",
                appointment_id=appt_id_1,
                farmer_id="F-GOA-901",
                centre_id="PC-GOA-01",
                crop="Mango",
                quantity_quintals=Decimal("24.50"),
                quality_score=Decimal("94.50"),
                procurement_rate_rs_per_quintal=Decimal("3200.00"),
                gross_amount_rs=Decimal("78400.00"),
                procurement_timestamp=datetime.combine(d_hist1, datetime.strptime("14:30", "%H:%M").time()),
                payment_status="COMPLETED",
                dbt_reference=f"DBT{d_hist1.strftime('%Y%m%d')}90124"
            )
            db.add(pt1)

        # Notification for F-GOA-901
        notif1 = db.query(Notification).filter(Notification.notification_id == f"NOTIF-{appt_id_1}").first()
        if notif1:
            db.delete(notif1)
        db.add(Notification(
            notification_id=f"NOTIF-{appt_id_1}",
            farmer_id="F-GOA-901",
            notification_type="PAYMENT_SUCCESS",
            channel="SMS_AND_APP",
            message=f"Mango Procurement Complete! 24.5 Quintals procured at ₹3,200/Q. Payment of ₹78,400 credited via DBT.",
            sent_at=datetime.combine(d_hist1, datetime.strptime("16:35", "%H:%M").time()),
            delivery_status="DELIVERED",
            response="ACKNOWLEDGED"
        ))

        # -------------------------------------------------------------
        # Record 2: Today Live IN_SERVICE Appointment (Deepa Sawant)
        # Deepa Sawant at Centre Yard for live demo scan
        # -------------------------------------------------------------
        appt_id_2 = f"PF-{today.strftime('%y%m%d')}-903"
        slot_id_2 = slot_map.get((str(today), "09:30 AM"), 2)

        b2 = db.query(Booking).filter(Booking.appointment_id == appt_id_2).first()
        if not b2:
            b2 = Booking(
                appointment_id=appt_id_2,
                booking_id=appt_id_2,
                farmer_id="F-GOA-903",
                centre_id="PC-GOA-01",
                slot_id=slot_id_2,
                crop="Mango",
                quantity=Decimal("18.00"),
                status="ARRIVED",
                qr_token=f"BA-QR-{appt_id_2}"
            )
            db.add(b2)
            db.flush()
        else:
            b2.status = "ARRIVED"

        a2 = db.query(Appointment).filter(Appointment.appointment_id == appt_id_2).first()
        if not a2:
            a2 = Appointment(
                appointment_id=appt_id_2,
                farmer_id="F-GOA-903",
                centre_id="PC-GOA-01",
                appointment_date=today,
                slot_start=datetime.combine(today, datetime.strptime("09:30", "%H:%M").time()),
                slot_duration_min=30,
                queue_before=0,
                active_weighing_machines=2,
                staff_available=8,
                predicted_wait_min=Decimal("4.0"),
                status="ARRIVED",
                crop="Mango",
                quantity_quintals=Decimal("18.00"),
                token_number="A101",
                qr_token=f"BA-QR-{appt_id_2}"
            )
            db.add(a2)
            db.flush()
        else:
            a2.status = "ARRIVED"

        # -------------------------------------------------------------
        # Record 3: Today Active Waiting Appointment for Ramesh Rane (F-GOA-901)
        # Next in Queue (Token A102, farmers ahead = 1, wait = 12 mins)
        # Displays on Farmer Dashboard & My Booking!
        # -------------------------------------------------------------
        appt_id_3 = f"PF-{today.strftime('%y%m%d')}-904"
        slot_id_3 = slot_map.get((str(today), "10:30 AM"), 3)

        b3 = db.query(Booking).filter(Booking.appointment_id == appt_id_3).first()
        if not b3:
            b3 = Booking(
                appointment_id=appt_id_3,
                booking_id=appt_id_3,
                farmer_id="F-GOA-901",
                centre_id="PC-GOA-01",
                slot_id=slot_id_3,
                crop="Mango",
                quantity=Decimal("20.00"),
                status="CONFIRMED",
                qr_token=f"BA-QR-{appt_id_3}"
            )
            db.add(b3)
            db.flush()
        else:
            b3.status = "CONFIRMED"

        a3 = db.query(Appointment).filter(Appointment.appointment_id == appt_id_3).first()
        if not a3:
            a3 = Appointment(
                appointment_id=appt_id_3,
                farmer_id="F-GOA-901",
                centre_id="PC-GOA-01",
                appointment_date=today,
                slot_start=datetime.combine(today, datetime.strptime("10:30", "%H:%M").time()),
                slot_duration_min=30,
                queue_before=1,
                active_weighing_machines=2,
                staff_available=8,
                predicted_wait_min=Decimal("12.0"),
                status="CONFIRMED",
                crop="Mango",
                quantity_quintals=Decimal("20.00"),
                token_number="A102",
                qr_token=f"BA-QR-{appt_id_3}"
            )
            db.add(a3)
            db.flush()
        else:
            a3.status = "CONFIRMED"

        # Active notification for Ramesh Rane
        notif3 = db.query(Notification).filter(Notification.notification_id == f"NOTIF-{appt_id_3}").first()
        if notif3:
            db.delete(notif3)
        db.add(Notification(
            notification_id=f"NOTIF-{appt_id_3}",
            farmer_id="F-GOA-901",
            notification_type="QUEUE_UPDATE",
            channel="APP_PUSH",
            message=f"Appointment Confirmed! Token: A102 at Panaji Apex APMC Yard. Only 1 farmer ahead of you. Recommended departure: 9:45 AM.",
            sent_at=datetime.now(),
            delivery_status="DELIVERED",
            response="PENDING"
        ))

        # -------------------------------------------------------------
        # Record 4: Upcoming Tomorrow Appointment for Antonio Fernandes
        # -------------------------------------------------------------
        d_tom = today + timedelta(days=1)
        appt_id_4 = f"PF-{d_tom.strftime('%y%m%d')}-905"
        slot_id_4 = slot_map.get((str(d_tom), "09:30 AM"), 4)

        b4 = db.query(Booking).filter(Booking.appointment_id == appt_id_4).first()
        if not b4:
            b4 = Booking(
                appointment_id=appt_id_4,
                booking_id=appt_id_4,
                farmer_id="F-GOA-902",
                centre_id="PC-GOA-01",
                slot_id=slot_id_4,
                crop="Mango",
                quantity=Decimal("30.00"),
                status="CONFIRMED",
                qr_token=f"BA-QR-{appt_id_4}"
            )
            db.add(b4)

        a4 = db.query(Appointment).filter(Appointment.appointment_id == appt_id_4).first()
        if not a4:
            a4 = Appointment(
                appointment_id=appt_id_4,
                farmer_id="F-GOA-902",
                centre_id="PC-GOA-01",
                appointment_date=d_tom,
                slot_start=datetime.combine(d_tom, datetime.strptime("09:30", "%H:%M").time()),
                slot_duration_min=30,
                queue_before=2,
                active_weighing_machines=2,
                staff_available=8,
                predicted_wait_min=Decimal("15.0"),
                status="CONFIRMED",
                crop="Mango",
                quantity_quintals=Decimal("30.00"),
                token_number="A103",
                qr_token=f"BA-QR-{appt_id_4}"
            )
            db.add(a4)

        # 6. Add QueueEvent and CentreDailyMetric for PC-GOA-01
        qe = db.query(QueueEvent).filter(QueueEvent.centre_id == "PC-GOA-01").order_by(QueueEvent.timestamp.desc()).first()
        if not qe or qe.timestamp.date() != today:
            db.add(QueueEvent(
                event_id=f"QE-PC-GOA-01-{uuid.uuid4().hex[:8]}",
                timestamp=datetime.now(),
                centre_id="PC-GOA-01",
                queue_length=2,
                farmers_in_service=1,
                active_stations=2,
                processing_rate_farmers_per_hour=Decimal("4.50"),
                avg_processing_time_min=Decimal("13.50"),
                equipment_failure_flag=0,
                weather_delay_flag=0,
                estimated_wait_min=Decimal("12.00")
            ))

        cdm = db.query(CentreDailyMetric).filter(CentreDailyMetric.centre_id == "PC-GOA-01", CentreDailyMetric.date == today).first()
        if not cdm:
            db.add(CentreDailyMetric(
                date=today,
                centre_id="PC-GOA-01",
                capacity_farmers=90,
                arrivals=4,
                processed=1,
                no_shows=0,
                avg_wait_min=Decimal("12.50"),
                peak_queue=3,
                equipment_downtime_min=0,
                congestion_score=Decimal("0.220"),
                high_congestion_flag=0
            ))

        db.commit()
        print(">>> SUCCESS: Mango Demo Centre (PC-GOA-01) Operational Records Fully Seeded & Synchronized! <<<")
        print("=" * 80)

    except Exception as e:
        db.rollback()
        print(f"[Error] Failed to seed mango demo centre records: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_mango_demo_centre()
