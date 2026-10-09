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

db = SessionLocal()

print("[1] Updating C01 as Sanquelim Procurement Centre 1 in Goa...")
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
c01.supported_crops = "Mango,Banana,Tomato"
c01.max_daily_capacity_quintals = 1200.0
c01.total_storage_capacity_quintals = 15000.0
c01.current_storage_usage_quintals = 3450.0
c01.daily_capacity_farmers = 120
c01.weighing_machines = 2
c01.quality_stations = 2
c01.staff_count = 12
c01.status = "OPERATIONAL"

print("[2] Updating demo centre user centre@bharatagri.demo to C01...")
demo_u = db.query(User).filter(User.email == "centre@bharatagri.demo").first()
if demo_u:
    demo_u.centre_id = "C01"
    demo_u.name = "Sanquelim Centre Manager"

u_c01 = db.query(User).filter(User.user_id == "C01").first()
if u_c01:
    u_c01.centre_id = "C01"
    u_c01.name = "Sanquelim Centre Incharge"

db.commit()

print("[3] Adding/ensuring Goan farmers in North Goa...")
goa_farmers = [
    ("F-GOA-901", "Ramesh Rane", "Bicholim", "North Goa", "Mango", Decimal("2.50")),
    ("F-GOA-902", "Antonio Fernandes", "Ponda", "North Goa", "Mango", Decimal("3.20")),
    ("F-GOA-903", "Deepa Sawant", "Sattari", "North Goa", "Mango", Decimal("2.00")),
    ("F-GOA-904", "Sunita Naik", "Sanquelim", "North Goa", "Banana", Decimal("1.80")),
    ("F-GOA-905", "Prakash Gaonkar", "Sattari", "North Goa", "Tomato", Decimal("1.50")),
    ("F-GOA-906", "Fatima D'Souza", "Bardez", "North Goa", "Mango", Decimal("2.80")),
    ("F-GOA-907", "Mahesh Prabhu", "Bicholim", "North Goa", "Banana", Decimal("2.20")),
    ("F-GOA-908", "Rohan Shirodkar", "Ponda", "North Goa", "Tomato", Decimal("1.60")),
    ("F-GOA-909", "Anand Kerkar", "Sanquelim", "North Goa", "Mango", Decimal("3.50")),
    ("F-GOA-910", "Meera Kamat", "Sanquelim", "North Goa", "Mango", Decimal("2.10")),
]

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
    # Check crop
    existing_c = db.query(FarmerCrop).filter(FarmerCrop.farmer_id == f.id, FarmerCrop.crop_name == crop).first()
    if not existing_c:
        fc = FarmerCrop(farmer_id=f.id, crop_name=crop, season="Kharif", estimated_quantity_quintals=float(area) * 20.0)
        db.add(fc)

db.commit()

print("[4] Creating slots & appointments for C01...")
today = datetime.date.today()
slot_times = [
    ("09:00 AM", "11:00 AM"),
    ("11:00 AM", "01:00 PM"),
    ("02:00 PM", "04:00 PM"),
    ("04:00 PM", "06:00 PM"),
]

for d_offset in [-2, -1, 0, 1]:
    cur_date = today + datetime.timedelta(days=d_offset)
    for st, et in slot_times:
        s = db.query(Slot).filter(Slot.centre_id == "C01", Slot.date == cur_date, Slot.start_time == st).first()
        if not s:
            s = Slot(centre_id="C01", date=cur_date, start_time=st, end_time=et, max_capacity=30)
            db.add(s)

db.commit()

slots_today = db.query(Slot).filter(Slot.centre_id == "C01", Slot.date == today).order_by(Slot.id).all()
s0 = slots_today[0] if slots_today else None
s1 = slots_today[1] if len(slots_today) > 1 else s0
s2 = slots_today[2] if len(slots_today) > 2 else s1

today_appts = [
    ("PF-GOA-261008-01", "F-GOA-901", "Mango", Decimal("45.00"), "A001", "IN_SERVICE", s0),
    ("PF-GOA-261008-02", "F-GOA-902", "Mango", Decimal("60.00"), "A002", "CHECKED_IN", s0),
    ("PF-GOA-261008-03", "F-GOA-904", "Banana", Decimal("35.00"), "A003", "WAITING", s1),
    ("PF-GOA-261008-04", "F-GOA-905", "Tomato", Decimal("25.00"), "A004", "WAITING", s1),
    ("PF-GOA-261008-05", "F-GOA-906", "Mango", Decimal("50.00"), "A005", "WAITING", s2),
    ("PF-GOA-261008-06", "F-GOA-907", "Banana", Decimal("30.00"), "A006", "CONFIRMED", s2),
]

for appt_code, f_code, crop, qty, token, status, slot in today_appts:
    f_obj = db.query(Farmer).filter(Farmer.farmer_code == f_code).first()
    app = db.query(Appointment).filter(Appointment.appointment_id == appt_code).first()
    if not app:
        app = Appointment(
            appointment_id=appt_code,
            farmer_id=f_code,
            centre_id="C01",
            slot_start=slot.start_time if slot else "09:00 AM",
            slot_duration_min=120,
            crop=crop,
            quantity_quintals=qty,
            status=status,
            token_number=token,
            appointment_date=datetime.datetime.combine(today, datetime.time(9, 30))
        )
        db.add(app)
        db.flush()
    # Booking
    b = db.query(Booking).filter(Booking.booking_id == f"BK-{appt_code}").first()
    if not b:
        b = Booking(
            booking_id=f"BK-{appt_code}",
            appointment_id=appt_code,
            farmer_id=f_code,
            centre_id="C01",
            slot_id=slot.id if slot else 1,
            crop=crop,
            quantity=qty,
            status=status if status in ["CONFIRMED", "BOOKED"] else "BOOKED",
            qr_token=f"QR-{appt_code}"
        )
        db.add(b)

# Past completed procurements for C01
yest = today - datetime.timedelta(days=1)
slots_yest = db.query(Slot).filter(Slot.centre_id == "C01", Slot.date == yest).all()
sy = slots_yest[0] if slots_yest else s0

past_items = [
    ("PF-GOA-PAST-01", "P-GOA-001", "PAY-GOA-001", "F-GOA-903", "Mango", Decimal("35.00"), Decimal("4920.00")),
    ("PF-GOA-PAST-02", "P-GOA-002", "PAY-GOA-002", "F-GOA-908", "Tomato", Decimal("28.00"), Decimal("1707.50")),
    ("PF-GOA-PAST-03", "P-GOA-003", "PAY-GOA-003", "F-GOA-909", "Mango", Decimal("55.00"), Decimal("4920.00")),
]

for app_code, pr_code, pay_code, f_code, crop, qty, rate in past_items:
    f_obj = db.query(Farmer).filter(Farmer.farmer_code == f_code).first()
    app = db.query(Appointment).filter(Appointment.appointment_id == app_code).first()
    if not app:
        app = Appointment(
            appointment_id=app_code,
            farmer_id=f_code,
            centre_id="C01",
            slot_start=sy.start_time if sy else "09:00 AM",
            slot_duration_min=120,
            crop=crop,
            quantity_quintals=qty,
            status="COMPLETED",
            token_number="P010",
            appointment_date=datetime.datetime.combine(yest, datetime.time(11, 0))
        )
        db.add(app)
        db.flush()

    b = db.query(Booking).filter(Booking.booking_id == f"BK-{app_code}").first()
    if not b:
        b = Booking(
            booking_id=f"BK-{app_code}",
            appointment_id=app_code,
            farmer_id=f_code,
            centre_id="C01",
            slot_id=sy.id if sy else 1,
            crop=crop,
            quantity=qty,
            status="COMPLETED",
            qr_token=f"QR-{app_code}"
        )
        db.add(b)
        db.flush()

    col = db.query(CollectionRecord).filter(CollectionRecord.collection_id == f"COL-{app_code}").first()
    if not col:
        col = CollectionRecord(
            collection_id=f"COL-{app_code}",
            booking_id=b.id,
            farmer_id=f_code,
            centre_id="C01",
            crop=crop,
            collected_quantity=qty,
            collection_date=yest,
            collected_by="Officer Shrikant Naik",
            status="COLLECTED"
        )
        db.add(col)
        db.flush()

    if not db.query(ProcurementRecord).filter(ProcurementRecord.procurement_id == pr_code).first():
        tot_amt = qty * rate
        pr = ProcurementRecord(
            procurement_id=pr_code,
            booking_id=b.id,
            collection_id=col.collection_id,
            farmer_id=f_code,
            centre_id="C01",
            crop=crop,
            quality_grade="GRADE_A",
            procured_quantity_quintals=qty,
            msp_rate_per_quintal=rate,
            total_procurement_value=tot_amt,
            status="CONFIRMED",
            created_at=datetime.datetime.combine(yest, datetime.time(12, 0))
        )
        db.add(pr)
        db.flush()
        pay = Payment(
            payment_id=pay_code,
            procurement_id=pr_code,
            farmer_id=f_code,
            amount=tot_amt,
            msp_rate=rate,
            quantity_quintals=qty,
            payment_mode="DBT_DIRECT",
            payment_status="PAID",
            transaction_ref=f"DBT-NPCI-GOA-{pr_code}",
            initiated_at=datetime.datetime.combine(yest, datetime.time(13, 0)),
            paid_at=datetime.datetime.combine(yest, datetime.time(13, 15)),
            remarks="Government MSP DBT Settlement"
        )
        db.add(pay)

    if not db.query(ProcurementTransaction).filter(ProcurementTransaction.procurement_id == pr_code).first():
        tot_amt = qty * rate
        pt = ProcurementTransaction(
            procurement_id=pr_code,
            appointment_id=app_code,
            farmer_id=f_code,
            centre_id="C01",
            crop=crop,
            quantity_quintals=qty,
            quality_score=Decimal("94.50"),
            procurement_rate_rs_per_quintal=rate,
            gross_amount_rs=tot_amt,
            procurement_timestamp=datetime.datetime.combine(yest, datetime.time(12, 30)),
            payment_status="PAID",
            dbt_reference=f"DBT-NPCI-GOA-{pr_code}"
        )
        db.add(pt)

# Today's procurement transaction for C01
if not db.query(ProcurementTransaction).filter(ProcurementTransaction.procurement_id == "P-GOA-TODAY-01").first():
    today_pt = ProcurementTransaction(
        procurement_id="P-GOA-TODAY-01",
        appointment_id="PF-GOA-261008-01",
        farmer_id="F-GOA-901",
        centre_id="C01",
        crop="Mango",
        quantity_quintals=Decimal("45.00"),
        quality_score=Decimal("96.00"),
        procurement_rate_rs_per_quintal=Decimal("4920.00"),
        gross_amount_rs=Decimal("221400.00"),
        procurement_timestamp=datetime.datetime.combine(today, datetime.time(10, 15)),
        payment_status="PAID",
        dbt_reference="DBT-NPCI-GOA-TODAY-01"
    )
    db.add(today_pt)

# Queue event for C01
db.query(QueueEvent).filter(QueueEvent.centre_id == "C01").delete()
qe = QueueEvent(
    event_id="QE-C01-LATEST",
    centre_id="C01",
    timestamp=datetime.datetime.now(),
    queue_length=4,
    farmers_in_service=1,
    active_stations=2,
    processing_rate_farmers_per_hour=Decimal("3.50"),
    avg_processing_time_min=Decimal("17.00"),
    estimated_wait_min=Decimal("20.00"),
    equipment_failure_flag=0,
    weather_delay_flag=0
)
db.add(qe)

# Daily metric for C01
db.query(CentreDailyMetric).filter(CentreDailyMetric.centre_id == "C01").delete()
cdm_today = CentreDailyMetric(
    centre_id="C01",
    date=today,
    capacity_farmers=120,
    arrivals=8,
    processed=6,
    no_shows=0,
    avg_wait_min=Decimal("18.50"),
    peak_queue=5,
    equipment_downtime_min=0,
    congestion_score=Decimal("0.250"),
    high_congestion_flag=0
)
db.add(cdm_today)

cdm_yest = CentreDailyMetric(
    centre_id="C01",
    date=yest,
    capacity_farmers=120,
    arrivals=12,
    processed=11,
    no_shows=1,
    avg_wait_min=Decimal("17.00"),
    peak_queue=6,
    equipment_downtime_min=0,
    congestion_score=Decimal("0.200"),
    high_congestion_flag=0
)
db.add(cdm_yest)

print("[5] Fixing empty status payments in DB to 'PAID' where paid_at is set...")
updated_payments = db.query(Payment).filter(Payment.payment_status == "", Payment.paid_at.isnot(None)).update(
    {Payment.payment_status: "PAID"}, synchronize_session=False
)
print(f"Updated {updated_payments} payments with empty status to PAID.")

print("[6] Ensuring pending truck request and proposed route for C01...")
from backend.app.models.logistics import TruckRequest, TruckRoutePrediction
existing_trq = db.query(TruckRequest).filter(TruckRequest.centre_id == "C01", TruckRequest.status == "PENDING").first()
if not existing_trq:
    trq = TruckRequest(
        request_code="TRQ-20261008-C01-01",
        centre_id="C01",
        required_date=today,
        required_capacity_quintals=Decimal("180.00"),
        reason="Peak mango harvest intake requiring outbound logistics transfer to North Goa cold storage",
        status="PENDING"
    )
    db.add(trq)

existing_trp = db.query(TruckRoutePrediction).filter(TruckRoutePrediction.origin_centre_id == "C01", TruckRoutePrediction.status == "PROPOSED").first()
if not existing_trp:
    trp = TruckRoutePrediction(
        route_code="TRP-20261008-GOA-01",
        origin_centre_id="C01",
        origin_centre_name="Sanquelim Procurement Centre 1",
        destination_centre_id="PC-GOA-01",
        destination_centre_name="Panaji APMC Cold Storage",
        destination_state="Goa",
        crop="Mango",
        quantity_quintals=Decimal("180.00"),
        truck_capacity_quintals=Decimal("180.00"),
        estimated_distance_km=Decimal("32.50"),
        departure_date=today,
        expected_arrival_date=today,
        reason="Perishable Mankurad mango surplus redirection to Panaji central cold storage facility.",
        status="PROPOSED"
    )
    db.add(trp)

db.commit()
db.close()
print("Sanquelim Demo Centre & DBT data setup completed successfully!")
