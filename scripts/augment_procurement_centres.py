import os
import sys
import uuid
from datetime import date, datetime, timedelta, time
from decimal import Decimal
import random
from sqlalchemy.sql import func

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
    ProcurementRecord, StorageLot, Payment
)

NEW_CENTRES_DEF = [
    {
        "centre_id": "C021",
        "centre_name": "Kolhapur Regional APMC Hub",
        "location": "Shiroli Industrial Area, Kolhapur",
        "state": "Maharashtra",
        "district": "Kolhapur",
        "contact_number": "0231-2654321",
        "operating_days": "Monday,Tuesday,Wednesday,Thursday,Friday,Saturday",
        "opening_time": "08:00 AM",
        "closing_time": "06:00 PM",
        "supported_crops": "Paddy,Soybean,Maize,Sugarcane",
        "max_daily_capacity_quintals": 1200.0,
        "total_storage_capacity_quintals": 22000.0,
        "current_storage_usage_quintals": 6400.0,
        "daily_capacity_farmers": 160,
        "weighing_machines": 4,
        "quality_stations": 3,
        "staff_count": 16,
        "status": "OPERATIONAL",
        "equipment_condition": "Optimal / High Throughput"
    },
    {
        "centre_id": "C022",
        "centre_name": "Amravati Vidarbha Cotton Yard",
        "location": "Badnera Mandi Complex, Amravati",
        "state": "Maharashtra",
        "district": "Amravati",
        "contact_number": "0721-2512345",
        "operating_days": "Monday,Tuesday,Wednesday,Thursday,Friday,Saturday",
        "opening_time": "08:30 AM",
        "closing_time": "05:30 PM",
        "supported_crops": "Cotton,Soybean,Wheat,Paddy",
        "max_daily_capacity_quintals": 950.0,
        "total_storage_capacity_quintals": 18000.0,
        "current_storage_usage_quintals": 4800.0,
        "daily_capacity_farmers": 130,
        "weighing_machines": 3,
        "quality_stations": 2,
        "staff_count": 12,
        "status": "OPERATIONAL",
        "equipment_condition": "Weighbridge #2 sensor calibration scheduled"
    },
    {
        "centre_id": "C023",
        "centre_name": "Jabalpur Narmada Krishi Mandi",
        "location": "Bhedaghat Bypass Road, Jabalpur",
        "state": "Madhya Pradesh",
        "district": "Jabalpur",
        "contact_number": "0761-2401122",
        "operating_days": "Monday,Tuesday,Wednesday,Thursday,Friday,Saturday",
        "opening_time": "08:30 AM",
        "closing_time": "05:00 PM",
        "supported_crops": "Wheat,Paddy,Maize,Soybean",
        "max_daily_capacity_quintals": 1100.0,
        "total_storage_capacity_quintals": 20000.0,
        "current_storage_usage_quintals": 5200.0,
        "daily_capacity_farmers": 140,
        "weighing_machines": 3,
        "quality_stations": 2,
        "staff_count": 14,
        "status": "OPERATIONAL",
        "equipment_condition": "Optimal"
    },
    {
        "centre_id": "C024",
        "centre_name": "Hoshangabad Wheat Procurement Depot",
        "location": "Itarsi Mandi Road, Narmadapuram",
        "state": "Madhya Pradesh",
        "district": "Hoshangabad",
        "contact_number": "07574-252110",
        "operating_days": "Monday,Tuesday,Wednesday,Thursday,Friday,Saturday",
        "opening_time": "08:00 AM",
        "closing_time": "06:00 PM",
        "supported_crops": "Wheat,Soybean,Paddy",
        "max_daily_capacity_quintals": 1350.0,
        "total_storage_capacity_quintals": 25000.0,
        "current_storage_usage_quintals": 7800.0,
        "daily_capacity_farmers": 180,
        "weighing_machines": 4,
        "quality_stations": 3,
        "staff_count": 18,
        "status": "OPERATIONAL",
        "equipment_condition": "Peak harvest volume; all 4 lanes active"
    },
    {
        "centre_id": "C025",
        "centre_name": "Jalandhar Doaba APMC Centre",
        "location": "GT Road, Jalandhar Cantt",
        "state": "Punjab",
        "district": "Jalandhar",
        "contact_number": "0181-2223344",
        "operating_days": "Monday,Tuesday,Wednesday,Thursday,Friday,Saturday",
        "opening_time": "08:00 AM",
        "closing_time": "05:00 PM",
        "supported_crops": "Wheat,Paddy,Maize",
        "max_daily_capacity_quintals": 1000.0,
        "total_storage_capacity_quintals": 19000.0,
        "current_storage_usage_quintals": 4100.0,
        "daily_capacity_farmers": 130,
        "weighing_machines": 3,
        "quality_stations": 2,
        "staff_count": 12,
        "status": "OPERATIONAL",
        "equipment_condition": "Optimal"
    },
    {
        "centre_id": "C026",
        "centre_name": "Bhatinda Malwa Grain Terminal",
        "location": "Dabwali Road, Bathinda",
        "state": "Punjab",
        "district": "Bathinda",
        "contact_number": "0164-2211990",
        "operating_days": "Monday,Tuesday,Wednesday,Thursday,Friday,Saturday",
        "opening_time": "08:00 AM",
        "closing_time": "06:00 PM",
        "supported_crops": "Wheat,Cotton,Paddy,Maize",
        "max_daily_capacity_quintals": 1250.0,
        "total_storage_capacity_quintals": 24000.0,
        "current_storage_usage_quintals": 6100.0,
        "daily_capacity_farmers": 160,
        "weighing_machines": 4,
        "quality_stations": 3,
        "staff_count": 15,
        "status": "OPERATIONAL",
        "equipment_condition": "Optimal"
    },
    {
        "centre_id": "C027",
        "centre_name": "Varanasi Purvanchal Krishi Hub",
        "location": "Rohania Mandi Yard, Varanasi",
        "state": "Uttar Pradesh",
        "district": "Varanasi",
        "contact_number": "0542-2508899",
        "operating_days": "Monday,Tuesday,Wednesday,Thursday,Friday,Saturday",
        "opening_time": "08:30 AM",
        "closing_time": "05:30 PM",
        "supported_crops": "Paddy,Wheat,Maize,Soybean",
        "max_daily_capacity_quintals": 900.0,
        "total_storage_capacity_quintals": 16000.0,
        "current_storage_usage_quintals": 3200.0,
        "daily_capacity_farmers": 120,
        "weighing_machines": 3,
        "quality_stations": 2,
        "staff_count": 12,
        "status": "OPERATIONAL",
        "equipment_condition": "Low demand period; surplus intake capacity"
    },
    {
        "centre_id": "C028",
        "centre_name": "Bareilly Rohilkhand Mandi Yard",
        "location": "Pilibhit Bypass Road, Bareilly",
        "state": "Uttar Pradesh",
        "district": "Bareilly",
        "contact_number": "0581-2554433",
        "operating_days": "Monday,Tuesday,Wednesday,Thursday,Friday,Saturday",
        "opening_time": "08:30 AM",
        "closing_time": "05:00 PM",
        "supported_crops": "Wheat,Paddy,Sugarcane,Maize",
        "max_daily_capacity_quintals": 850.0,
        "total_storage_capacity_quintals": 15000.0,
        "current_storage_usage_quintals": 2900.0,
        "daily_capacity_farmers": 110,
        "weighing_machines": 2,
        "quality_stations": 2,
        "staff_count": 11,
        "status": "OPERATIONAL",
        "equipment_condition": "Optimal"
    },
    {
        "centre_id": "C029",
        "centre_name": "Hubballi North Karnataka APMC Terminal",
        "location": "Amargol APMC Yard, Hubballi",
        "state": "Karnataka",
        "district": "Dharwad",
        "contact_number": "0836-2227766",
        "operating_days": "Monday,Tuesday,Wednesday,Thursday,Friday,Saturday",
        "opening_time": "08:30 AM",
        "closing_time": "05:30 PM",
        "supported_crops": "Cotton,Maize,Soybean,Paddy",
        "max_daily_capacity_quintals": 1050.0,
        "total_storage_capacity_quintals": 19500.0,
        "current_storage_usage_quintals": 4500.0,
        "daily_capacity_farmers": 140,
        "weighing_machines": 3,
        "quality_stations": 2,
        "staff_count": 13,
        "status": "OPERATIONAL",
        "equipment_condition": "Optimal"
    },
    {
        "centre_id": "PC-GOA-02",
        "centre_name": "Margao South Goa Horticultural Terminal",
        "location": "Madgaon Wholesale Market, South Goa",
        "state": "Goa",
        "district": "South Goa",
        "contact_number": "0832-2731144",
        "operating_days": "Monday,Tuesday,Wednesday,Thursday,Friday,Saturday",
        "opening_time": "08:30 AM",
        "closing_time": "04:30 PM",
        "supported_crops": "Mango,Banana,Tomato",
        "max_daily_capacity_quintals": 500.0,
        "total_storage_capacity_quintals": 9500.0,
        "current_storage_usage_quintals": 1400.0,
        "daily_capacity_farmers": 75,
        "weighing_machines": 2,
        "quality_stations": 2,
        "staff_count": 8,
        "status": "OPERATIONAL",
        "equipment_condition": "Specialized horticultural grading benches active"
    }
]

CROP_MSP_MAP = {
    "Wheat": Decimal("2275.00"),
    "Paddy": Decimal("2183.00"),
    "Cotton": Decimal("6620.00"),
    "Soybean": Decimal("4600.00"),
    "Maize": Decimal("2090.00"),
    "Mango": Decimal("3800.00"),
    "Banana": Decimal("1650.00"),
    "Tomato": Decimal("1400.00"),
    "Sugarcane": Decimal("315.00")
}

SLOT_SCHEDULE = [
    ("08:30 AM", "09:30 AM"),
    ("09:30 AM", "10:30 AM"),
    ("10:30 AM", "11:30 AM"),
    ("11:30 AM", "12:30 PM"),
    ("01:30 PM", "02:30 PM"),
    ("02:30 PM", "03:30 PM"),
    ("03:30 PM", "04:30 PM")
]

def augment_centres():
    db = SessionLocal()
    print("=" * 80)
    print(" AUGMENTING REALISTIC PROCUREMENT CENTRES & CONNECTED OPERATIONAL DATA")
    print("=" * 80)

    today = date.today()
    dates = [today - timedelta(days=d) for d in range(7, 0, -1)] + [today] + [today + timedelta(days=d) for d in range(1, 5)]

    added_centres = 0
    added_appts = 0
    added_procs = 0
    added_payments = 0

    try:
        # Get existing farmers to connect realistically
        farmers = db.query(Farmer).all()
        farmer_by_state = {}
        for f in farmers:
            st = f.state or "Maharashtra"
            farmer_by_state.setdefault(st, []).append(f)

        for c_def in NEW_CENTRES_DEF:
            cid = c_def["centre_id"]
            centre = db.query(ProcurementCentre).filter(ProcurementCentre.centre_id == cid).first()
            if not centre:
                centre = ProcurementCentre(
                    centre_id=cid,
                    centre_name=c_def["centre_name"],
                    location=c_def["location"],
                    state=c_def["state"],
                    district=c_def["district"],
                    contact_number=c_def["contact_number"],
                    operating_days=c_def["operating_days"],
                    opening_time=c_def["opening_time"],
                    closing_time=c_def["closing_time"],
                    supported_crops=c_def["supported_crops"],
                    max_daily_capacity_quintals=Decimal(str(c_def["max_daily_capacity_quintals"])),
                    total_storage_capacity_quintals=Decimal(str(c_def["total_storage_capacity_quintals"])),
                    current_storage_usage_quintals=Decimal(str(c_def["current_storage_usage_quintals"])),
                    daily_capacity_farmers=c_def["daily_capacity_farmers"],
                    weighing_machines=c_def["weighing_machines"],
                    quality_stations=c_def["quality_stations"],
                    staff_count=c_def["staff_count"],
                    status=c_def["status"]
                )
                db.add(centre)
                db.flush()
                added_centres += 1
                print(f"[Added Centre] {centre.centre_name} ({cid}) - {centre.state}")
            else:
                centre.centre_name = c_def["centre_name"]
                centre.supported_crops = c_def["supported_crops"]
                centre.state = c_def["state"]
                centre.district = c_def["district"]
                centre.max_daily_capacity_quintals = Decimal(str(c_def["max_daily_capacity_quintals"]))
                centre.status = c_def["status"]
                db.flush()
                print(f"[Updated Centre] {centre.centre_name} ({cid})")

            # 2. Add Daily Capacities & Slots
            for d in dates:
                cap = db.query(DailyCapacity).filter(DailyCapacity.centre_id == cid, DailyCapacity.date == d).first()
                if not cap:
                    db.add(DailyCapacity(
                        centre_id=cid,
                        date=d,
                        max_quintals_per_day=Decimal(str(c_def["max_daily_capacity_quintals"]))
                    ))
                for st, et in SLOT_SCHEDULE:
                    slot = db.query(Slot).filter(Slot.centre_id == cid, Slot.date == d, Slot.start_time == st).first()
                    if not slot:
                        db.add(Slot(
                            centre_id=cid,
                            date=d,
                            start_time=st,
                            end_time=et,
                            max_capacity=int(c_def["daily_capacity_farmers"] // len(SLOT_SCHEDULE))
                        ))
            db.flush()

            # 3. Add Connected Operational History & Live Queue for this centre
            eligible_crops = [x.strip() for x in c_def["supported_crops"].split(",") if x.strip()]
            state_farmers = farmer_by_state.get(c_def["state"], farmers[:20])
            if len(state_farmers) < 10:
                state_farmers = farmers[:30]

            random.seed(int(cid.replace("C", "").replace("PC-GOA-", "")) if cid.replace("C", "").replace("PC-GOA-", "").isdigit() else 42)

            for day_offset in range(-6, 3):
                op_date = today + timedelta(days=day_offset)
                # Number of arrivals varies by centre type and day
                n_farmers = random.randint(6, 14) if day_offset <= 0 else random.randint(4, 9)

                daily_total_q = Decimal("0.0")

                for i in range(n_farmers):
                    f = state_farmers[(i + abs(day_offset) * 3) % len(state_farmers)]
                    f_code = f.farmer_code or f.user_id

                    crop_choice = eligible_crops[i % len(eligible_crops)]
                    # Ensure farmer has this crop registered
                    f_crops = [c.crop_name.lower() for c in f.crops]
                    if crop_choice.lower() not in f_crops:
                        db.add(FarmerCrop(
                            farmer_id=f.id,
                            crop_name=crop_choice,
                            season="Kharif 2026" if crop_choice in ["Paddy", "Cotton", "Soybean", "Maize"] else "Rabi 2025-26",
                            estimated_quantity_quintals=Decimal("60.00")
                        ))
                        db.flush()

                    slot_st, slot_et = SLOT_SCHEDULE[i % len(SLOT_SCHEDULE)]
                    appt_id = f"AP-{cid}-{op_date.strftime('%y%m%d')}-{i+1:03d}"

                    existing_appt = db.query(Appointment).filter(Appointment.appointment_id == appt_id).first()
                    if existing_appt:
                        continue

                    # Quantities
                    expected_q = Decimal(str(random.randint(30, 85)))
                    allocated_q = expected_q

                    if day_offset < 0:
                        status = "COMPLETED"
                        checkin_time = datetime.combine(op_date, time(9 + (i % 6), (i * 12) % 60))
                        service_start = checkin_time + timedelta(minutes=15)
                        service_end = service_start + timedelta(minutes=20)
                    elif day_offset == 0:
                        if i < 4:
                            status = "COMPLETED"
                            checkin_time = datetime.combine(op_date, time(8, 30)) + timedelta(minutes=i * 15)
                            service_start = checkin_time + timedelta(minutes=12)
                            service_end = service_start + timedelta(minutes=18)
                        elif i < 7:
                            status = "IN_SERVICE"
                            checkin_time = datetime.combine(op_date, time(10, 15))
                            service_start = datetime.combine(op_date, time(10, 30))
                            service_end = None
                        elif i < 11:
                            status = "WAITING"
                            checkin_time = datetime.combine(op_date, time(10, 45))
                            service_start = None
                            service_end = None
                        else:
                            status = "CONFIRMED"
                            checkin_time = None
                            service_start = None
                            service_end = None
                    else:
                        status = "CONFIRMED"
                        checkin_time = None
                        service_start = None
                        service_end = None

                    slot_start_dt = datetime.combine(op_date, time(8 + (i % 7), 30))
                    appt = Appointment(
                        appointment_id=appt_id,
                        farmer_id=f_code,
                        centre_id=cid,
                        crop=crop_choice,
                        appointment_date=op_date,
                        slot_start=slot_start_dt,
                        slot_duration_min=60,
                        token_number=f"T-{cid[-3:]}-{i+1:02d}",
                        queue_before=i,
                        status=status,
                        active_weighing_machines=c_def["weighing_machines"],
                        staff_available=c_def["staff_count"],
                        quantity_quintals=allocated_q,
                        travel_distance_km=Decimal(str(random.randint(5, 25))),
                        created_at=datetime.combine(op_date - timedelta(days=2), time(10, 0))
                    )
                    db.add(appt)
                    added_appts += 1

                    # Add connected Booking
                    bkg_id = f"BK-{cid}-{op_date.strftime('%y%m%d')}-{i+1:03d}"
                    existing_bkg = db.query(Booking).filter(Booking.appointment_id == appt_id).first()
                    if not existing_bkg:
                        # Find slot id
                        cur_slot = db.query(Slot).filter(Slot.centre_id == cid, Slot.date == op_date, Slot.start_time == slot_st).first()
                        slot_id_val = cur_slot.id if cur_slot else 1
                        db.add(Booking(
                            appointment_id=appt_id,
                            booking_id=bkg_id,
                            farmer_id=f_code,
                            centre_id=cid,
                            slot_id=slot_id_val,
                            crop=crop_choice,
                            quantity=allocated_q,
                            status=status,
                            qr_token=f"QR-{cid}-{op_date.strftime('%y%m%d')}-{i+1:03d}",
                            created_at=datetime.combine(op_date - timedelta(days=2), time(10, 0))
                        ))

                    # If completed, add ProcurementTransaction, CollectionRecord, ProcurementRecord & Payment
                    if status == "COMPLETED":
                        actual_weighed_q = expected_q - Decimal(str(random.choice([-1.5, -0.5, 0.0, 0.5, 1.0])))
                        rate = CROP_MSP_MAP.get(crop_choice, Decimal("2183.00"))
                        gross_amt = (actual_weighed_q * rate).quantize(Decimal("0.01"))
                        proc_timestamp = datetime.combine(op_date, time(11, 30))

                        txn_id = f"PT-{cid}-{op_date.strftime('%y%m%d')}-{i+1:03d}"
                        existing_txn = db.query(ProcurementTransaction).filter(ProcurementTransaction.procurement_id == txn_id).first()
                        if not existing_txn:
                            proc_txn = ProcurementTransaction(
                                procurement_id=txn_id,
                                appointment_id=appt_id,
                                centre_id=cid,
                                farmer_id=f_code,
                                crop=crop_choice,
                                quantity_quintals=actual_weighed_q,
                                quality_score=Decimal("88.50"),
                                procurement_rate_rs_per_quintal=rate,
                                gross_amount_rs=gross_amt,
                                payment_status="PAID" if day_offset < 0 else "PROCESSING",
                                dbt_reference=f"PAY-{cid}-{op_date.strftime('%y%m%d')}-{i+1:03d}",
                                procurement_timestamp=proc_timestamp
                            )
                            db.add(proc_txn)
                            added_procs += 1

                        # Collection Record
                        col_id = f"COL-{cid}-{op_date.strftime('%y%m%d')}-{i+1:03d}"
                        existing_col = db.query(CollectionRecord).filter(CollectionRecord.collection_id == col_id).first()
                        if not existing_col:
                            col_rec = CollectionRecord(
                                collection_id=col_id,
                                booking_id=existing_bkg.id if existing_bkg else 1,
                                farmer_id=f_code,
                                centre_id=cid,
                                crop=crop_choice,
                                collected_quantity=actual_weighed_q,
                                collection_date=op_date,
                                truck_number=f"MH-{random.randint(10, 48)}-TR-{random.randint(1000, 9999)}",
                                collected_by="Mandi Yard Officer",
                                status="COLLECTED"
                            )
                            db.add(col_rec)
                            db.flush()

                        # Procurement Record
                        pr_id = f"PR-{cid}-{op_date.strftime('%y%m%d')}-{i+1:03d}"
                        existing_pr = db.query(ProcurementRecord).filter(ProcurementRecord.procurement_id == pr_id).first()
                        if not existing_pr:
                            proc_rec = ProcurementRecord(
                                procurement_id=pr_id,
                                booking_id=existing_bkg.id if existing_bkg else 1,
                                collection_id=col_id,
                                farmer_id=f_code,
                                centre_id=cid,
                                crop=crop_choice,
                                quality_grade="GRADE_A",
                                moisture_content_pct=Decimal("11.80"),
                                procured_quantity_quintals=actual_weighed_q,
                                msp_rate_per_quintal=rate,
                                total_procurement_value=gross_amt,
                                status="CONFIRMED",
                                warehouse_location=f"Storage Bay {cid[-2:]}",
                                created_at=proc_timestamp
                            )
                            db.add(proc_rec)
                            db.flush()

                            # Payment Record
                            pay_id = f"PAY-{cid}-{op_date.strftime('%y%m%d')}-{i+1:03d}"
                            existing_pay = db.query(Payment).filter(Payment.payment_id == pay_id).first()
                            if not existing_pay:
                                db.add(Payment(
                                    payment_id=pay_id,
                                    procurement_id=pr_id,
                                    farmer_id=f_code,
                                    amount=gross_amt,
                                    msp_rate=rate,
                                    quantity_quintals=actual_weighed_q,
                                    payment_mode="DBT_NEFT",
                                    payment_status="PAID" if day_offset < 0 else "INITIATED",
                                    transaction_ref=f"TXN-DBT-{uuid.uuid4().hex[:10].upper()}",
                                    paid_at=proc_timestamp + timedelta(hours=2) if day_offset < 0 else None
                                ))
                                added_payments += 1

                        daily_total_q += actual_weighed_q

                # Add QueueEvent & CentreDailyMetric for this day
                existing_qe = db.query(QueueEvent).filter(QueueEvent.centre_id == cid, func.date(QueueEvent.timestamp) == op_date).first()
                if not existing_qe:
                    db.add(QueueEvent(
                        event_id=f"QE-{cid}-{op_date.strftime('%y%m%d')}",
                        centre_id=cid,
                        queue_length=4 if day_offset == 0 else random.randint(2, 8),
                        estimated_wait_min=Decimal(str(random.randint(12, 28))),
                        processing_rate_farmers_per_hour=Decimal(str(round(random.uniform(3.5, 5.2), 1))),
                        equipment_failure_flag=1 if cid == "C022" and day_offset == 0 else 0,
                        timestamp=datetime.combine(op_date, time(11, 0))
                    ))

                existing_cdm = db.query(CentreDailyMetric).filter(CentreDailyMetric.centre_id == cid, CentreDailyMetric.date == op_date).first()
                if not existing_cdm:
                    db.add(CentreDailyMetric(
                        centre_id=cid,
                        date=op_date,
                        capacity_farmers=c_def["daily_capacity_farmers"],
                        arrivals=n_farmers,
                        processed=n_farmers if day_offset < 0 else 4,
                        avg_wait_min=Decimal(str(random.randint(14, 25))),
                        peak_queue=n_farmers // 2 + 3,
                        equipment_downtime_min=45 if cid == "C022" and day_offset == 0 else 0
                    ))

            db.commit()
            print(f"[Finished Centre {cid}] Generated history & live operations.")

        print("=" * 80)
        print(f"AUGMENTATION COMPLETED SUCCESSFULLY:")
        print(f"  New Centres Added/Verified : {len(NEW_CENTRES_DEF)}")
        print(f"  New Appointments Created   : {added_appts}")
        print(f"  New Procurements Created   : {added_procs}")
        print(f"  New Payments Created       : {added_payments}")
        print("=" * 80)

    except Exception as e:
        db.rollback()
        print(f"ERROR during augmentation: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    augment_centres()
