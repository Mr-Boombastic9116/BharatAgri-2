import sys
sys.path.insert(0, '.')
import datetime
from decimal import Decimal
from backend.app.core.database import SessionLocal
from backend.app.models.centre import ProcurementCentre, Slot
from backend.app.models.user import User
from backend.app.models.farmer import Farmer, FarmerCrop
from backend.app.models.booking import Booking
from backend.app.models.queue import Appointment, QueueEvent, CentreDailyMetric, ProcurementTransaction
from backend.app.models.procurement import CollectionRecord, ProcurementRecord, Payment
from backend.app.models.alert import Alert

def seed_demo_data():
    db = SessionLocal()
    try:
        print("[1] Ensuring C01 Sanquelim Procurement Centre 1...")
        c01 = db.query(ProcurementCentre).filter(ProcurementCentre.centre_id == "C01").first()
        if not c01:
            c01 = ProcurementCentre(centre_id="C01")
            db.add(c01)
        c01.centre_name = "Sanquelim Procurement Centre 1"
        c01.state = "Goa"
        c01.district = "North Goa"
        c01.location = "Bicholim Road, Sanquelim, North Goa"
        c01.contact_number = "9822770487"
        c01.operating_days = "Monday,Tuesday,Wednesday,Thursday,Friday,Saturday"
        c01.opening_time = "09:00 AM"
        c01.closing_time = "05:00 PM"
        c01.supported_crops = "Mango,Banana,Tomato,Paddy"
        c01.max_daily_capacity_quintals = 1200.0
        c01.total_storage_capacity_quintals = 15000.0
        c01.current_storage_usage_quintals = 4120.0
        c01.daily_capacity_farmers = 120
        c01.weighing_machines = 3
        c01.quality_stations = 2
        c01.staff_count = 14
        c01.status = "OPERATIONAL"

        # Ensure centre users
        u_mgr = db.query(User).filter(User.email == "centre@bharatagri.demo").first()
        if u_mgr:
            u_mgr.centre_id = "C01"
            u_mgr.name = "Sanquelim Centre Manager"
        u_c01 = db.query(User).filter(User.user_id == "C01").first()
        if u_c01:
            u_c01.centre_id = "C01"
            u_c01.name = "Sanquelim Centre Incharge"

        db.commit()

        print("[2] Setting up Demo Farmer FRM-DEMO-001 (Rameshwar Patil)...")
        demo_farmer = db.query(Farmer).filter((Farmer.farmer_code == "FRM-DEMO-001") | (Farmer.user_id == "farmer@bharatagri.demo")).first()
        if not demo_farmer:
            demo_farmer = Farmer(
                user_id="farmer@bharatagri.demo",
                farmer_code="FRM-DEMO-001",
                name="Rameshwar Patil",
                mobile="9822123456",
                email="farmer@bharatagri.demo",
                gender="Male",
                state="Goa",
                district="North Goa",
                taluka="Sanquelim",
                village="Surla",
                address="Survey No. 42, Surla, Sanquelim, North Goa",
                land_area_hectares=Decimal("4.50"),
                primary_crop="Mango",
                ekyc_status="VERIFIED",
                aadhaar_masked="XXXX-XXXX-4819",
                bank_name="State Bank of India",
                bank_account_no="304928174819",
                bank_ifsc="SBIN0001234",
                preferred_language="en"
            )
            db.add(demo_farmer)
            db.flush()
        else:
            demo_farmer.farmer_code = "FRM-DEMO-001"
            demo_farmer.user_id = "farmer@bharatagri.demo"
            demo_farmer.name = "Rameshwar Patil"
            demo_farmer.state = "Goa"
            demo_farmer.district = "North Goa"
            demo_farmer.primary_crop = "Mango"
            db.flush()

        # Add farmer crops
        crops_to_add = [
            ("Mango", "Kharif", 90.0),
            ("Banana", "Annual", 50.0),
            ("Tomato", "Rabi", 35.0),
        ]
        for cname, season, est_qty in crops_to_add:
            fc = db.query(FarmerCrop).filter(FarmerCrop.farmer_id == demo_farmer.id, FarmerCrop.crop_name == cname).first()
            if not fc:
                fc = FarmerCrop(farmer_id=demo_farmer.id, crop_name=cname, season=season, estimated_quantity_quintals=est_qty)
                db.add(fc)

        # Other Goan farmers
        goa_farmers = [
            ("F-GOA-901", "Ramesh Rane", "Bicholim", "North Goa", "Mango", Decimal("2.50")),
            ("F-GOA-902", "Antonio Fernandes", "Ponda", "North Goa", "Mango", Decimal("3.20")),
            ("F-GOA-903", "Deepa Sawant", "Sattari", "North Goa", "Paddy", Decimal("2.00")),
            ("F-GOA-904", "Sunita Naik", "Sanquelim", "North Goa", "Banana", Decimal("1.80")),
            ("F-GOA-905", "Prakash Gaonkar", "Sattari", "North Goa", "Tomato", Decimal("1.50")),
            ("F-GOA-906", "Fatima D'Souza", "Bardez", "North Goa", "Mango", Decimal("2.80")),
            ("F-GOA-907", "Mahesh Prabhu", "Bicholim", "North Goa", "Banana", Decimal("2.20")),
            ("F-GOA-908", "Rohan Shirodkar", "Ponda", "North Goa", "Tomato", Decimal("1.60")),
            ("F-GOA-909", "Anand Kerkar", "Sanquelim", "North Goa", "Mango", Decimal("3.50")),
            ("F-GOA-910", "Meera Kamat", "Sanquelim", "North Goa", "Paddy", Decimal("2.10")),
        ]
        farmer_map = {"FRM-DEMO-001": demo_farmer}
        for code, name, village, dist, crop, area in goa_farmers:
            f = db.query(Farmer).filter(Farmer.farmer_code == code).first()
            if not f:
                f = Farmer(
                    user_id=code,
                    farmer_code=code,
                    name=name,
                    village=village,
                    taluka=village,
                    district=dist,
                    state="Goa",
                    land_area_hectares=area,
                    mobile=f"982311{code[-4:]}",
                    aadhaar_masked=f"XXXX-XXXX-{code[-4:]}",
                    ekyc_status="VERIFIED",
                    bank_name="State Bank of India",
                    bank_account_no=f"30492817{code[-4:]}",
                    bank_ifsc="SBIN0001234"
                )
                db.add(f)
                db.flush()
            fc = db.query(FarmerCrop).filter(FarmerCrop.farmer_id == f.id, FarmerCrop.crop_name == crop).first()
            if not fc:
                fc = FarmerCrop(farmer_id=f.id, crop_name=crop, season="Kharif", estimated_quantity_quintals=float(area) * 20.0)
                db.add(fc)
            farmer_map[code] = f

        db.commit()

        print("[3] Generating Slots for C01 from -30 days to +7 days...")
        today = datetime.date.today()
        slot_defs = [
            ("09:00 AM", "11:00 AM"),
            ("11:00 AM", "01:00 PM"),
            ("02:00 PM", "04:00 PM"),
            ("04:00 PM", "06:00 PM"),
        ]

        slot_cache = {}
        for d_offset in range(-30, 8):
            dt = today + datetime.timedelta(days=d_offset)
            slot_cache[dt] = []
            for st, et in slot_defs:
                s = db.query(Slot).filter(Slot.centre_id == "C01", Slot.date == dt, Slot.start_time == st).first()
                if not s:
                    s = Slot(centre_id="C01", date=dt, start_time=st, end_time=et, max_capacity=30)
                    db.add(s)
                    db.flush()
                slot_cache[dt].append(s)

        db.commit()

        print("[4] Generating Longitudinal Historical, Today, and Future Data...")
        # Rates per quintal
        msp_rates = {
            "Mango": Decimal("4920.00"),
            "Paddy": Decimal("2300.00"),
            "Banana": Decimal("3100.00"),
            "Tomato": Decimal("1700.00")
        }

        # Demo Farmer Longitudinal Appointments
        # Past appointments across last 30 days
        demo_farmer_schedule = [
            (-24, "Mango", Decimal("40.00"), "COMPLETED", "PAID"),
            (-17, "Tomato", Decimal("18.00"), "COMPLETED", "PAID"),
            (-10, "Mango", Decimal("55.00"), "COMPLETED", "PAID"),
            (-3, "Banana", Decimal("28.00"), "COMPLETED", "PAID"),
            (-1, "Mango", Decimal("45.00"), "COMPLETED", "PAID"),
            (0, "Mango", Decimal("35.00"), "IN_SERVICE", "PENDING"),
            (2, "Mango", Decimal("40.00"), "BOOKED", None),
            (5, "Banana", Decimal("22.00"), "BOOKED", None)
        ]

        for offset, crop, qty, status, pay_status in demo_farmer_schedule:
            dt = today + datetime.timedelta(days=offset)
            appt_id = f"APPT-C01-DEMO-{dt.strftime('%Y%m%d')}"
            existing_appt = db.query(Appointment).filter(Appointment.appointment_id == appt_id).first()
            s_obj = slot_cache[dt][1]
            if not existing_appt:
                app = Appointment(
                    appointment_id=appt_id,
                    farmer_id="FRM-DEMO-001",
                    centre_id="C01",
                    slot_start=s_obj.start_time,
                    slot_duration_min=120,
                    crop=crop,
                    quantity_quintals=qty,
                    status=status,
                    token_number=f"T-D{abs(offset):02d}",
                    appointment_date=datetime.datetime.combine(dt, datetime.time(11, 15)),
                    queue_before=2 if status == "IN_SERVICE" else 0,
                    actual_wait_min=Decimal("15.00") if status == "COMPLETED" else None
                )
                db.add(app)
                db.flush()

                # Booking
                bk = Booking(
                    booking_id=f"BK-{appt_id}",
                    appointment_id=appt_id,
                    farmer_id="FRM-DEMO-001",
                    centre_id="C01",
                    slot_id=s_obj.id,
                    crop=crop,
                    quantity=qty,
                    status=status if status in ["BOOKED", "COMPLETED"] else "CONFIRMED",
                    qr_token=f"QR-{appt_id}"
                )
                db.add(bk)
                db.flush()

                if status == "COMPLETED":
                    pr_id = f"PR-DEMO-{dt.strftime('%Y%m%d')}"
                    rate = msp_rates.get(crop, Decimal("3000.00"))
                    val = qty * rate
                    pt = ProcurementTransaction(
                        procurement_id=pr_id,
                        appointment_id=appt_id,
                        farmer_id="FRM-DEMO-001",
                        centre_id="C01",
                        crop=crop,
                        quantity_quintals=qty,
                        quality_score=Decimal("95.50"),
                        procurement_rate_rs_per_quintal=rate,
                        gross_amount_rs=val,
                        procurement_timestamp=datetime.datetime.combine(dt, datetime.time(12, 30)),
                        payment_status=pay_status,
                        dbt_reference=f"DBT-GOA-{pr_id}"
                    )
                    db.add(pt)
                    db.flush()

                    pay = Payment(
                        payment_id=f"PAY-{pr_id}",
                        procurement_id=pr_id,
                        farmer_id="FRM-DEMO-001",
                        amount=val,
                        msp_rate=rate,
                        quantity_quintals=qty,
                        payment_mode="DBT_DIRECT",
                        payment_status=pay_status,
                        transaction_ref=f"DBT-GOA-{pr_id}",
                        initiated_at=datetime.datetime.combine(dt, datetime.time(13, 0)),
                        paid_at=datetime.datetime.combine(dt, datetime.time(13, 20)) if pay_status == "PAID" else None,
                        remarks="Demo Farmer Longitudinal Procurement Settlement"
                    )
                    db.add(pay)

        # Multi-farmer operational history across dates
        # Days: -7 to +3
        daily_plans = [
            (-7, [("F-GOA-901", "Mango", 40, "COMPLETED", "PAID"), ("F-GOA-903", "Paddy", 60, "COMPLETED", "PAID"), ("F-GOA-904", "Banana", 25, "COMPLETED", "PAID")]),
            (-6, [("F-GOA-902", "Mango", 50, "COMPLETED", "PAID"), ("F-GOA-905", "Tomato", 30, "COMPLETED", "PAID"), ("F-GOA-906", "Mango", 45, "COMPLETED", "PAID")]),
            (-5, [("F-GOA-907", "Banana", 35, "COMPLETED", "PAID"), ("F-GOA-909", "Mango", 70, "COMPLETED", "PAID"), ("F-GOA-910", "Paddy", 80, "COMPLETED", "PAID")]),
            (-4, [("F-GOA-901", "Mango", 55, "COMPLETED", "PAID"), ("F-GOA-908", "Tomato", 22, "COMPLETED", "PAID")]),
            (-3, [("F-GOA-902", "Mango", 65, "COMPLETED", "PAID"), ("F-GOA-903", "Paddy", 90, "COMPLETED", "PAID"), ("F-GOA-904", "Banana", 30, "COMPLETED", "PAID")]),
            (-2, [("F-GOA-905", "Tomato", 28, "COMPLETED", "PENDING"), ("F-GOA-906", "Mango", 50, "COMPLETED", "PAID"), ("F-GOA-909", "Mango", 60, "COMPLETED", "PAID")]),
            (-1, [("F-GOA-901", "Mango", 48, "COMPLETED", "PAID"), ("F-GOA-902", "Mango", 62, "COMPLETED", "PENDING"), ("F-GOA-903", "Paddy", 75, "COMPLETED", "PAID"), ("F-GOA-904", "Banana", 32, "COMPLETED", "PAID"), ("F-GOA-905", "Tomato", 20, "COMPLETED", "PENDING")]),
            (0, [("F-GOA-901", "Mango", 45, "COMPLETED", "PAID"), ("F-GOA-902", "Mango", 60, "CHECKED_IN", "PENDING"), ("F-GOA-904", "Banana", 35, "WAITING", "PENDING"), ("F-GOA-905", "Tomato", 25, "WAITING", "PENDING"), ("F-GOA-906", "Mango", 50, "WAITING", "PENDING"), ("F-GOA-907", "Banana", 30, "CONFIRMED", "PENDING")]),
            (1, [("F-GOA-903", "Paddy", 70, "BOOKED", None), ("F-GOA-908", "Tomato", 25, "BOOKED", None), ("F-GOA-909", "Mango", 55, "BOOKED", None), ("F-GOA-910", "Paddy", 65, "BOOKED", None)]),
            (2, [("F-GOA-901", "Mango", 40, "BOOKED", None), ("F-GOA-902", "Mango", 50, "BOOKED", None), ("F-GOA-904", "Banana", 30, "BOOKED", None)]),
        ]

        for offset, appt_list in daily_plans:
            dt = today + datetime.timedelta(days=offset)
            for idx, (f_code, crop, qty_num, status, pay_status) in enumerate(appt_list, 1):
                appt_id = f"APPT-C01-{dt.strftime('%Y%m%d')}-{idx:02d}"
                qty = Decimal(str(qty_num))
                existing_appt = db.query(Appointment).filter(Appointment.appointment_id == appt_id).first()
                s_obj = slot_cache[dt][idx % len(slot_defs)]
                if not existing_appt:
                    app = Appointment(
                        appointment_id=appt_id,
                        farmer_id=f_code,
                        centre_id="C01",
                        slot_start=s_obj.start_time,
                        slot_duration_min=120,
                        crop=crop,
                        quantity_quintals=qty,
                        status=status,
                        token_number=f"T-{idx:03d}",
                        appointment_date=datetime.datetime.combine(dt, datetime.time(9 + (idx % 6), 30)),
                        queue_before=idx if status == "WAITING" else 0,
                        actual_wait_min=Decimal("18.00") if status == "COMPLETED" else None
                    )
                    db.add(app)
                    db.flush()

                    bk = Booking(
                        booking_id=f"BK-{appt_id}",
                        appointment_id=appt_id,
                        farmer_id=f_code,
                        centre_id="C01",
                        slot_id=s_obj.id,
                        crop=crop,
                        quantity=qty,
                        status=status if status in ["BOOKED", "COMPLETED"] else "CONFIRMED",
                        qr_token=f"QR-{appt_id}"
                    )
                    db.add(bk)
                    db.flush()

                    if status == "COMPLETED":
                        pr_id = f"PR-C01-{dt.strftime('%Y%m%d')}-{idx:02d}"
                        rate = msp_rates.get(crop, Decimal("3000.00"))
                        val = qty * rate
                        pt = ProcurementTransaction(
                            procurement_id=pr_id,
                            appointment_id=appt_id,
                            farmer_id=f_code,
                            centre_id="C01",
                            crop=crop,
                            quantity_quintals=qty,
                            quality_score=Decimal("94.00"),
                            procurement_rate_rs_per_quintal=rate,
                            gross_amount_rs=val,
                            procurement_timestamp=datetime.datetime.combine(dt, datetime.time(11 + (idx % 4), 15)),
                            payment_status=pay_status,
                            dbt_reference=f"DBT-GOA-{pr_id}"
                        )
                        db.add(pt)
                        db.flush()

                        pay = Payment(
                            payment_id=f"PAY-{pr_id}",
                            procurement_id=pr_id,
                            farmer_id=f_code,
                            amount=val,
                            msp_rate=rate,
                            quantity_quintals=qty,
                            payment_mode="DBT_DIRECT",
                            payment_status=pay_status,
                            transaction_ref=f"DBT-GOA-{pr_id}",
                            initiated_at=datetime.datetime.combine(dt, datetime.time(12, 0)),
                            paid_at=datetime.datetime.combine(dt, datetime.time(12, 30)) if pay_status == "PAID" else None,
                            remarks="Operational Procurement Settlement"
                        )
                        db.add(pay)

        # Centre Daily Metrics for C01 from -14 to 0
        for offset in range(-14, 1):
            dt = today + datetime.timedelta(days=offset)
            cdm = db.query(CentreDailyMetric).filter(CentreDailyMetric.centre_id == "C01", CentreDailyMetric.date == dt).first()
            if not cdm:
                cdm = CentreDailyMetric(centre_id="C01", date=dt)
                db.add(cdm)
            # Create natural variation: yesterday (-1) had busy queue with slight equipment downtime
            if offset == -1:
                cdm.capacity_farmers = 120
                cdm.arrivals = 18
                cdm.processed = 16
                cdm.no_shows = 1
                cdm.avg_wait_min = Decimal("32.50")
                cdm.peak_queue = 9
                cdm.equipment_downtime_min = 45 # Causal explanation for why queue was high yesterday!
                cdm.congestion_score = Decimal("0.720")
                cdm.high_congestion_flag = 1
            elif offset == 0:
                cdm.capacity_farmers = 120
                cdm.arrivals = 12
                cdm.processed = 8
                cdm.no_shows = 0
                cdm.avg_wait_min = Decimal("19.00")
                cdm.peak_queue = 5
                cdm.equipment_downtime_min = 0
                cdm.congestion_score = Decimal("0.310")
                cdm.high_congestion_flag = 0
            else:
                cdm.capacity_farmers = 120
                cdm.arrivals = 10 + (abs(offset) % 5)
                cdm.processed = cdm.arrivals - (1 if abs(offset) % 3 == 0 else 0)
                cdm.no_shows = 1 if abs(offset) % 4 == 0 else 0
                cdm.avg_wait_min = Decimal(str(15.0 + (abs(offset) % 6)))
                cdm.peak_queue = 4 + (abs(offset) % 3)
                cdm.equipment_downtime_min = 30 if offset == -4 else 0
                cdm.congestion_score = Decimal("0.280")
                cdm.high_congestion_flag = 0

        # Latest Queue Event for C01
        db.query(QueueEvent).filter(QueueEvent.centre_id == "C01").delete()
        qe = QueueEvent(
            event_id="QE-C01-LIVE",
            centre_id="C01",
            timestamp=datetime.datetime.now(),
            queue_length=4,
            farmers_in_service=1,
            active_stations=3,
            processing_rate_farmers_per_hour=Decimal("4.20"),
            avg_processing_time_min=Decimal("14.50"),
            estimated_wait_min=Decimal("18.00"),
            equipment_failure_flag=0,
            weather_delay_flag=0
        )
        db.add(qe)

        db.commit()
        print("[+] Seeded realistic longitudinal history for C01 and FRM-DEMO-001 successfully!")
    finally:
        db.close()

if __name__ == '__main__':
    seed_demo_data()
