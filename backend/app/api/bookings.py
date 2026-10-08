import random
from datetime import datetime, date, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, text, cast, String

from backend.app.core.database import get_db
from backend.app.core.helpers import resolve_centre, resolve_farmer
from backend.app.models.booking import Booking, BookingStatusHistory, QRCode
from backend.app.models.centre import Slot, DailyCapacity, NonOperationalDate, ProcurementCentre
from backend.app.models.farmer import Farmer
from backend.app.models.user import User
from backend.app.models.audit import AuditLog
from backend.app.models.queue import Appointment, ProcurementTransaction
from backend.app.models.procurement import CollectionRecord, QualityCheck, Weighment, ProcurementRecord, StorageLot, Payment
from backend.app.schemas.booking import BookingCreate, StatusUpdateRequest

router = APIRouter(prefix="/bookings", tags=["Bookings"])

STATE_CROP_RULES = {
    "Maharashtra": ["Paddy", "Wheat", "Cotton", "Soybean", "Maize", "Sugarcane"],
    "Punjab": ["Paddy", "Wheat", "Cotton", "Soybean", "Maize"],
    "Madhya Pradesh": ["Paddy", "Wheat", "Cotton", "Soybean", "Maize"],
    "Uttar Pradesh": ["Paddy", "Wheat", "Cotton", "Soybean", "Maize"],
    "Karnataka": ["Paddy", "Maize", "Bajra"],
    "Goa": ["Mango", "Banana", "Tomato"],
}

day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

def get_weekday_name(d: date) -> str:
    return day_names[d.weekday()]

def generate_appointment_id(d_str: str, db: Session) -> str:
    clean_date = d_str.replace("-", "")[2:] if d_str else "260930"
    seq = random.randint(100, 999)
    appt_id = f"PF-{clean_date}-{seq}"
    existing = db.query(Booking).filter(Booking.appointment_id == appt_id).first()
    if existing:
        return generate_appointment_id(d_str, db)
    return appt_id

@router.post("", status_code=201)
def create_booking(req: BookingCreate, db: Session = Depends(get_db)):
    if req.quantity <= 0:
        raise HTTPException(status_code=400, detail="Please enter a valid quantity in Quintals.")

    # 1. Slot check
    slot = db.query(Slot).filter(Slot.id == req.slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Selected time slot does not exist.")

    slot_date = slot.date
    w_name = get_weekday_name(slot_date)

    # 2. Centre check & Operating Days
    centre = resolve_centre(req.centre_id, db)
    if not centre:
        raise HTTPException(status_code=404, detail="Procurement Centre does not exist.")
    actual_centre_id = centre.centre_id

    if centre.operating_days and centre.operating_days != "[object Object]":
        allowed = [d.strip().lower() for d in centre.operating_days.split(",") if d.strip()]
        if w_name.lower() not in allowed:
            raise HTTPException(status_code=400, detail=f"{centre.centre_name} is closed on {w_name}s.")

    # 3. Holiday Check
    holiday = db.query(NonOperationalDate).filter(
        NonOperationalDate.centre_id == actual_centre_id,
        NonOperationalDate.date == slot_date
    ).first()
    if holiday:
        raise HTTPException(status_code=400, detail=f"Centre Closed on {slot_date} ({holiday.reason}).")

    # 4. Slot Capacity check
    booked_count = db.query(Booking).filter(Booking.slot_id == req.slot_id, Booking.status != "REJECTED").count()
    if booked_count >= slot.max_capacity:
        raise HTTPException(status_code=400, detail="Sorry, this slot is now full.")

    # 5. Daily Capacity check
    cap_row = db.query(DailyCapacity).filter(DailyCapacity.centre_id == actual_centre_id, DailyCapacity.date == slot_date).first()
    max_q = float(cap_row.max_quintals_per_day) if cap_row else float(centre.max_daily_capacity_quintals or 800.0)

    sum_booked = float(
        db.query(func.coalesce(func.sum(Booking.quantity), 0))
        .join(Slot, Booking.slot_id == Slot.id)
        .filter(Booking.centre_id == actual_centre_id, Slot.date == slot_date, Booking.status != "REJECTED")
        .scalar()
    )

    remaining_q = max(0.0, max_q - sum_booked)
    if sum_booked + req.quantity > max_q:
        raise HTTPException(
            status_code=400,
            detail=f"Daily quantity limit reached. Only {remaining_q:.2f} Quintals remain available for this date."
        )

    # 6. Crop support check & State Crop Restrictions
    if centre.state and centre.state in STATE_CROP_RULES:
        allowed_state_crops = STATE_CROP_RULES[centre.state]
        if req.crop.strip().lower() not in [c.lower() for c in allowed_state_crops]:
            raise HTTPException(
                status_code=400,
                detail=f"Crop '{req.crop}' is not permitted for state '{centre.state}'. Permitted crops for {centre.state}: {', '.join(allowed_state_crops)}."
            )

    if centre.supported_crops:
        supp = [c.strip().lower() for c in centre.supported_crops.split(",") if c.strip()]
        if req.crop.strip().lower() not in supp:
            raise HTTPException(status_code=400, detail=f"Crop '{req.crop}' is not supported by {centre.centre_name}.")

    # 6.5 Duplicate & Conflict Booking Prevention (Part 27)
    farmer = resolve_farmer(req.farmer_id, db)
    actual_farmer_code = farmer.farmer_code if farmer else req.farmer_id.strip()
    farmer_uid_options = [actual_farmer_code, req.farmer_id.strip()]
    if farmer:
        if farmer.user_id and farmer.user_id not in farmer_uid_options:
            farmer_uid_options.append(farmer.user_id)
        if str(farmer.id) not in farmer_uid_options:
            farmer_uid_options.append(str(farmer.id))

    active_statuses = ["BOOKED", "CONFIRMED", "CHECKED_IN", "WAITING", "IN_SERVICE"]

    # Check 1: Duplicate active booking for same farmer, centre, crop, and date
    duplicate_booking = db.query(Booking).join(Slot, Booking.slot_id == Slot.id).filter(
        Booking.farmer_id.in_(farmer_uid_options),
        Booking.centre_id == actual_centre_id,
        Booking.crop == req.crop.strip(),
        Slot.date == slot_date,
        Booking.status.in_(active_statuses)
    ).first()

    if duplicate_booking:
        raise HTTPException(
            status_code=409,
            detail=f"Duplicate booking conflict: You already have an active appointment ({duplicate_booking.appointment_id}) for {req.crop} at {centre.centre_name} on {slot_date}. Please manage or cancel your existing appointment before creating another."
        )

    # Check 2: Time slot conflict on the exact same slot
    slot_conflict = db.query(Booking).join(Slot, Booking.slot_id == Slot.id).filter(
        Booking.farmer_id.in_(farmer_uid_options),
        Booking.slot_id == req.slot_id,
        Booking.status.in_(active_statuses)
    ).first()

    if slot_conflict:
        raise HTTPException(
            status_code=409,
            detail=f"Slot conflict: You already have an active booking ({slot_conflict.appointment_id}) for this exact time slot on {slot_date}."
        )

    # 7. Generate Appointment ID, Token & QR Code
    appt_id = generate_appointment_id(str(slot_date), db)
    qr_token = f"BA-QR-{appt_id}"

    # Generate sequential token (e.g. A184)
    appt_seq = db.query(Appointment).filter(
        Appointment.centre_id == actual_centre_id,
        Appointment.appointment_date == slot_date
    ).count() + 1
    token_val = f"A{appt_seq:03d}" if appt_seq <= 999 else f"A{random.randint(100, 999)}"

    # Estimate queue before and wait
    queue_before_val = max(1, booked_count)
    pred_wait = round(queue_before_val * 3.5, 1)

    try:
        new_booking = Booking(
            appointment_id=appt_id,
            booking_id=appt_id,
            farmer_id=actual_farmer_code,
            centre_id=actual_centre_id,
            slot_id=req.slot_id,
            crop=req.crop.strip(),
            quantity=req.quantity,
            status="CONFIRMED",
            qr_token=qr_token
        )
        db.add(new_booking)
        db.flush()

        # Parse slot start time for Appointment
        slot_time_str = slot.start_time or "09:00 AM"
        try:
            parsed_t = datetime.strptime(slot_time_str.strip(), "%I:%M %p").time()
        except Exception:
            try:
                parsed_t = datetime.strptime(slot_time_str.strip(), "%H:%M").time()
            except Exception:
                parsed_t = datetime.strptime("09:30", "%H:%M").time()
        slot_dt = datetime.combine(slot_date, parsed_t)

        new_appt = Appointment(
            appointment_id=appt_id,
            farmer_id=actual_farmer_code,
            centre_id=actual_centre_id,
            appointment_date=slot_date,
            slot_start=slot_dt,
            slot_duration_min=30,
            queue_before=queue_before_val,
            active_weighing_machines=2,
            staff_available=8,
            predicted_wait_min=pred_wait,
            status="CONFIRMED",
            crop=req.crop.strip(),
            quantity_quintals=req.quantity,
            token_number=token_val,
            qr_token=qr_token
        )
        db.add(new_appt)

        # Add QR record
        db.add(QRCode(
            entity_type="BOOKING",
            entity_id=appt_id,
            qr_code_value=qr_token,
            is_used=False
        ))

        # Add Status History
        db.add(BookingStatusHistory(
            booking_id=new_booking.id,
            old_status=None,
            new_status="CONFIRMED",
            changed_by=actual_farmer_code,
            notes="Initial appointment confirmed"
        ))

        # Audit
        db.add(AuditLog(
            user_id=actual_farmer_code,
            action="BOOKING_CREATED",
            entity="BOOKING",
            entity_id=appt_id,
            new_value=f"Centre: {actual_centre_id}, Crop: {req.crop}, Qty: {req.quantity}Q, Token: {token_val}"
        ))

        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Transaction failed while creating booking: {str(e)}")

    # Fetch farmer name for response
    f_user = db.query(User).filter((User.user_id == req.farmer_id) | (User.email == req.farmer_id)).first()
    f_name = farmer.name if farmer else (f_user.name if f_user else req.farmer_id)
    f_mobile = farmer.mobile if farmer else (f_user.mobile if f_user else "")

    return {
        "message": "Appointment booked successfully!",
        "booking": {
            "id": new_booking.id,
            "appointment_id": appt_id,
            "booking_id": appt_id,
            "token": token_val,
            "token_number": token_val,
            "farmer_id": actual_farmer_code,
            "farmer_name": f_name,
            "farmer_mobile": f_mobile,
            "centre_id": centre.centre_id,
            "centre_name": centre.centre_name,
            "location": centre.location,
            "crop": req.crop,
            "quantity": float(req.quantity),
            "date": str(slot.date),
            "start_time": slot.start_time,
            "end_time": slot.end_time,
            "time_slot": f"{slot.start_time} - {slot.end_time}",
            "farmers_ahead": queue_before_val,
            "expected_wait_min": pred_wait,
            "status": "CONFIRMED",
            "qr_token": qr_token,
            "created_at": str(new_booking.created_at)
        }
    }

# Dynamic Centre Redirection
@router.post("/check-and-redirect")
def check_capacity_and_redirect(
    centre_id: str = Query(...),
    date_str: str = Query(...),
    crop: str = Query(...),
    quantity: float = Query(...),
    db: Session = Depends(get_db)
):
    centre = resolve_centre(centre_id, db)
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found.")
    actual_centre_id = centre.centre_id

    # Check capacity of requested centre
    cap_row = db.query(DailyCapacity).filter(DailyCapacity.centre_id == actual_centre_id, DailyCapacity.date == date_str).first()
    max_q = float(cap_row.max_quintals_per_day) if cap_row else float(centre.max_daily_capacity_quintals or 800.0)

    sum_booked = float(
        db.query(func.coalesce(func.sum(Booking.quantity), 0))
        .join(Slot, Booking.slot_id == Slot.id)
        .filter(Booking.centre_id == actual_centre_id, Slot.date == date_str, Booking.status != "REJECTED")
        .scalar()
    )

    remaining_q = max(0.0, max_q - sum_booked)
    has_capacity = (sum_booked + quantity <= max_q)

    if has_capacity:
        return {
            "can_book_original": True,
            "centre_id": centre.centre_id,
            "centre_name": centre.centre_name,
            "remaining_quintals": round(remaining_q, 2),
            "message": "Selected centre has sufficient capacity."
        }

    # Centre is overloaded -> Search nearby alternative operational centres in the same district/state with crop support
    alt_centres = (
        db.query(ProcurementCentre)
        .filter(
            ProcurementCentre.centre_id != centre_id,
            ProcurementCentre.status == "OPERATIONAL",
            (ProcurementCentre.district == centre.district) | (ProcurementCentre.state == centre.state)
        )
        .all()
    )

    suggestions = []
    for ac in alt_centres:
        # Check crop support
        supp = [c.strip().lower() for c in (ac.supported_crops or "").split(",") if c.strip()]
        if crop.strip().lower() not in supp:
            continue

        # Check operational day
        dt = datetime.strptime(date_str, "%Y-%m-%d").date()
        w_name = get_weekday_name(dt)
        op_days = [d.strip().lower() for d in (ac.operating_days or "").split(",") if d.strip()]
        if w_name.lower() not in op_days:
            continue

        # Check holiday
        hol = db.query(NonOperationalDate).filter(NonOperationalDate.centre_id == ac.centre_id, NonOperationalDate.date == date_str).first()
        if hol:
            continue

        # Check alternative daily capacity
        ac_cap_row = db.query(DailyCapacity).filter(DailyCapacity.centre_id == ac.centre_id, DailyCapacity.date == date_str).first()
        ac_max_q = float(ac_cap_row.max_quintals_per_day) if ac_cap_row else float(ac.max_daily_capacity_quintals or 800.0)
        ac_booked = float(
            db.query(func.coalesce(func.sum(Booking.quantity), 0))
            .join(Slot, Booking.slot_id == Slot.id)
            .filter(Booking.centre_id == ac.centre_id, Slot.date == date_str, Booking.status != "REJECTED")
            .scalar()
        )
        ac_rem = max(0.0, ac_max_q - ac_booked)

        if ac_rem >= quantity:
            # Check available slots
            open_slot = (
                db.query(Slot)
                .filter(Slot.centre_id == ac.centre_id, Slot.date == date_str)
                .order_by(Slot.id.asc())
                .first()
            )
            suggestions.append({
                "centre_id": ac.centre_id,
                "centre_name": ac.centre_name,
                "location": ac.location,
                "district": ac.district,
                "remaining_quintals": round(ac_rem, 2),
                "suggested_slot_id": open_slot.id if open_slot else None,
                "suggested_slot_time": f"{open_slot.start_time} - {open_slot.end_time}" if open_slot else "09:00 AM - 11:00 AM"
            })

    return {
        "can_book_original": False,
        "original_centre": {
            "centre_id": centre.centre_id,
            "centre_name": centre.centre_name,
            "daily_capacity": max_q,
            "remaining_quintals": round(remaining_q, 2)
        },
        "reason": f"Original centre capacity full for {date_str} (Only {remaining_q:.2f}Q left, requested {quantity}Q).",
        "redirection_suggestions": suggestions[:3]
    }

@router.get("/farmer/{farmer_id}")
def get_farmer_bookings(farmer_id: str, db: Session = Depends(get_db)):
    farmer = resolve_farmer(farmer_id, db)
    farmer_identifiers = [farmer_id.strip()]
    if farmer:
        if farmer.farmer_code and farmer.farmer_code not in farmer_identifiers:
            farmer_identifiers.append(farmer.farmer_code)
        if farmer.user_id and farmer.user_id not in farmer_identifiers:
            farmer_identifiers.append(farmer.user_id)
        if str(farmer.id) not in farmer_identifiers:
            farmer_identifiers.append(str(farmer.id))

    # Pre-cache centres for instant lookup
    centres_map = {c.centre_id: c for c in db.query(ProcurementCentre).all()}

    # Pre-cache transactions for payment status
    pts_by_appt = {pt.appointment_id: pt for pt in db.query(ProcurementTransaction).filter(ProcurementTransaction.farmer_id.in_(farmer_identifiers)).all()}

    # 1. Fetch bookings from bookings table with outerjoins
    bk_rows = (
        db.query(Booking, Slot)
        .outerjoin(Slot, Booking.slot_id == Slot.id)
        .filter(Booking.farmer_id.in_(farmer_identifiers))
        .order_by(Booking.id.desc())
        .all()
    )

    result = []
    seen_appt_ids = set()

    f_user = db.query(User).filter((User.user_id == farmer_id) | (User.email == farmer_id)).first()
    f_name = farmer.name if farmer else (f_user.name if f_user else farmer_id)
    f_mobile = farmer.mobile if farmer else (f_user.mobile if f_user else "")

    for b, s in bk_rows:
        seen_appt_ids.add(b.appointment_id)
        pc = centres_map.get(b.centre_id)
        pt = pts_by_appt.get(b.appointment_id)

        # Linked appointment for token
        appt_rec = db.query(Appointment).filter(Appointment.appointment_id == b.appointment_id).first()
        token_num = appt_rec.token_number if appt_rec and appt_rec.token_number else f"A{b.id % 900 + 100:03d}"

        # Payment details
        payment_status = pt.payment_status if pt else ("COMPLETED" if b.status == "COMPLETED" else "PENDING")
        payment_amount = float(pt.gross_amount_rs) if pt else None
        procured_qty = float(pt.quantity_quintals) if pt else None

        result.append({
            "id": b.id,
            "appointment_id": b.appointment_id,
            "booking_id": b.id,
            "token": token_num,
            "token_number": token_num,
            "farmer_id": b.farmer_id,
            "farmer_name": f_name,
            "farmer_mobile": f_mobile,
            "centre_id": b.centre_id,
            "centre_name": pc.centre_name if pc else b.centre_id,
            "location": pc.location if pc else "",
            "crop": b.crop,
            "quantity": float(b.quantity),
            "date": str(s.date) if s else (str(appt_rec.appointment_date) if appt_rec else str(date.today())),
            "start_time": s.start_time if s else "09:30 AM",
            "end_time": s.end_time if s else "10:00 AM",
            "time_slot": f"{s.start_time} - {s.end_time}" if s else "09:30 AM - 10:00 AM",
            "status": b.status,
            "payment_status": payment_status,
            "payment_amount": payment_amount,
            "procured_quantity": procured_qty,
            "dbt_reference": pt.dbt_reference if pt else None,
            "qr_token": b.qr_token,
            "farmers_ahead": appt_rec.queue_before if appt_rec else 5,
            "estimated_wait_min": float(appt_rec.predicted_wait_min) if appt_rec and appt_rec.predicted_wait_min else 20.0,
            "redirected_from_centre_id": b.redirected_from_centre_id,
            "verified_at": str(b.verified_at) if b.verified_at else None,
            "created_at": str(b.created_at)
        })

    # 2. Also merge any appointments from Appointment table not present in Booking table
    appts_extra = (
        db.query(Appointment)
        .filter(Appointment.farmer_id.in_(farmer_identifiers))
        .order_by(Appointment.id.desc())
        .all()
    )
    for a in appts_extra:
        if a.appointment_id in seen_appt_ids:
            continue
        seen_appt_ids.add(a.appointment_id)
        pc = centres_map.get(a.centre_id)
        pt = pts_by_appt.get(a.appointment_id)
        payment_status = pt.payment_status if pt else ("COMPLETED" if a.status == "COMPLETED" else "PENDING")

        result.append({
            "id": a.id,
            "appointment_id": a.appointment_id,
            "booking_id": a.id,
            "token": a.token_number or f"A{a.id % 900 + 100:03d}",
            "token_number": a.token_number or f"A{a.id % 900 + 100:03d}",
            "farmer_id": a.farmer_id,
            "farmer_name": f_name,
            "farmer_mobile": f_mobile,
            "centre_id": a.centre_id,
            "centre_name": pc.centre_name if pc else a.centre_id,
            "location": pc.location if pc else "",
            "crop": a.crop or "Paddy",
            "quantity": float(a.quantity_quintals or 40.0),
            "date": str(a.appointment_date),
            "start_time": a.slot_start.strftime("%I:%M %p") if a.slot_start else "09:30 AM",
            "end_time": (a.slot_start + timedelta(minutes=a.slot_duration_min or 30)).strftime("%I:%M %p") if a.slot_start else "10:00 AM",
            "time_slot": f"{a.slot_start.strftime('%I:%M %p')} - {(a.slot_start + timedelta(minutes=a.slot_duration_min or 30)).strftime('%I:%M %p')}" if a.slot_start else "09:30 AM - 10:00 AM",
            "status": a.status,
            "payment_status": payment_status,
            "payment_amount": float(pt.gross_amount_rs) if pt else None,
            "procured_quantity": float(pt.quantity_quintals) if pt else None,
            "dbt_reference": pt.dbt_reference if pt else None,
            "qr_token": a.qr_token or f"QR-BA-{a.appointment_id}",
            "farmers_ahead": a.queue_before or 5,
            "estimated_wait_min": float(a.predicted_wait_min) if a.predicted_wait_min else 20.0,
            "created_at": str(a.created_at)
        })

    return result

@router.get("/centre/{centre_id}")
def get_centre_bookings(centre_id: str, date: Optional[str] = None, db: Session = Depends(get_db)):
    query = (
        db.query(Booking, Slot, ProcurementCentre)
        .join(Slot, Booking.slot_id == Slot.id)
        .join(ProcurementCentre, Booking.centre_id == ProcurementCentre.centre_id)
        .filter(Booking.centre_id == centre_id)
    )

    if date:
        query = query.filter(Slot.date == date)

    items = query.order_by(Booking.id.desc()).limit(200).all()

    result = []
    for b, s, pc in items:
        f_user = db.query(User).filter(User.user_id == b.farmer_id).first()
        f_name = f_user.name if f_user else b.farmer_id
        f_mobile = f_user.mobile if f_user else ""

        result.append({
            "id": b.id,
            "appointment_id": b.appointment_id,
            "booking_id": b.id,
            "farmer_id": b.farmer_id,
            "farmer_name": f_name,
            "farmer_mobile": f_mobile,
            "centre_id": b.centre_id,
            "centre_name": pc.centre_name,
            "location": pc.location,
            "crop": b.crop,
            "quantity": float(b.quantity),
            "date": str(s.date),
            "start_time": s.start_time,
            "end_time": s.end_time,
            "time_slot": f"{s.start_time} - {s.end_time}",
            "status": b.status,
            "verification_status": "VERIFIED ✓" if b.status in ["VERIFIED", "ARRIVED", "CHECKED_IN", "RECEIVED", "COLLECTED", "QUALITY_CHECKED", "WEIGHED", "PROCURED", "STORED", "PAYMENT_INITIATED", "PAID"] else "NOT VERIFIED",
            "qr_token": b.qr_token,
            "verified_at": str(b.verified_at) if b.verified_at else None,
            "created_at": str(b.created_at)
        })
    return result

@router.put("/{booking_id}/status")
def update_booking_status(booking_id: str, req: StatusUpdateRequest, db: Session = Depends(get_db)):
    b = db.query(Booking).filter(
        (Booking.appointment_id == booking_id) | (cast(Booking.id, String) == booking_id)

    ).first()

    if not b:
        raise HTTPException(status_code=404, detail="Appointment not found.")

    valid_statuses = [
        'BOOKED', 'CONFIRMED', 'CHECKED_IN', 'VERIFIED', 'ARRIVED', 'RECEIVED',
        'COLLECTED', 'QUALITY_CHECKED', 'WEIGHED', 'PROCURED', 'STORED',
        'PAYMENT_INITIATED', 'PAID', 'REJECTED', 'EXPIRED', 'CANCELLED'
    ]
    new_st = req.status.upper()
    if new_st not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid booking status.")

    old_st = b.status
    b.status = new_st
    if new_st in ["CHECKED_IN", "VERIFIED", "ARRIVED", "RECEIVED"] and not b.verified_at:
        b.verified_at = datetime.utcnow()

    # Log history
    db.add(BookingStatusHistory(
        booking_id=b.id,
        old_status=old_st,
        new_status=new_st,
        changed_by="OPERATOR",
        notes=req.notes or "Status update action"
    ))

    # Audit
    db.add(AuditLog(
        user_id=b.centre_id,
        action="BOOKING_STATUS_CHANGED",
        entity="BOOKING",
        entity_id=b.appointment_id,
        old_value=old_st,
        new_value=new_st
    ))

    db.commit()
    return {
        "message": f"Appointment status updated to {new_st}",
        "appointment_id": b.appointment_id,
        "status": new_st
    }


@router.get("/{booking_id}/workflow-status")
def get_booking_workflow_status(booking_id: str, db: Session = Depends(get_db)):
    """
    Live 8-Step Procurement Lifecycle Workflow Tracker:
    BOOKED -> CHECKED IN -> ARRIVED -> QUALITY CHECK -> WEIGHING -> STORAGE -> PAYMENT INITIATED -> PAID
    Includes current active process name, completed steps, pending steps,
    actual quantity received, quality/moisture metrics, payment status, and timestamps.
    """
    b = db.query(Booking).filter(
        (Booking.appointment_id == booking_id) | (cast(Booking.id, String) == booking_id)
    ).first()

    if not b:
        raise HTTPException(status_code=404, detail="Appointment not found.")

    slot = db.query(Slot).filter(Slot.id == b.slot_id).first()
    centre = db.query(ProcurementCentre).filter(ProcurementCentre.centre_id == b.centre_id).first()

    # Query related records
    collection = db.query(CollectionRecord).filter(CollectionRecord.booking_id == b.id).first()
    quality = None
    weighment = None
    if collection:
        quality = db.query(QualityCheck).filter(QualityCheck.collection_id == collection.collection_id).first()
        weighment = db.query(Weighment).filter(Weighment.collection_id == collection.collection_id).first()

    procurement = db.query(ProcurementRecord).filter(ProcurementRecord.booking_id == b.id).first()
    storage = None
    payment = None
    if procurement:
        storage = db.query(StorageLot).filter(StorageLot.procurement_id == procurement.procurement_id).first()
        payment = db.query(Payment).filter(Payment.procurement_id == procurement.procurement_id).first()

    b_status = (b.status or "BOOKED").upper()

    # Determine step completion statuses
    step1_done = True
    step1_time = b.created_at.strftime("%Y-%m-%d %H:%M") if b.created_at else None

    step2_done = bool(b.verified_at) or b_status in [
        "CHECKED_IN", "VERIFIED", "ARRIVED", "RECEIVED", "COLLECTED", "QUALITY_CHECKED", "WEIGHED", "PROCURED", "STORED", "PAYMENT_INITIATED", "PAID"
    ]
    step2_time = b.verified_at.strftime("%Y-%m-%d %H:%M") if b.verified_at else None

    step3_done = collection is not None or b_status in [
        "ARRIVED", "RECEIVED", "COLLECTED", "QUALITY_CHECKED", "WEIGHED", "PROCURED", "STORED", "PAYMENT_INITIATED", "PAID"
    ]
    step3_time = collection.created_at.strftime("%Y-%m-%d %H:%M") if (collection and collection.created_at) else None

    step4_done = (quality is not None and quality.passed) or b_status in [
        "QUALITY_CHECKED", "WEIGHED", "PROCURED", "STORED", "PAYMENT_INITIATED", "PAID"
    ]
    step4_time = quality.checked_at.strftime("%Y-%m-%d %H:%M") if (quality and quality.checked_at) else None

    step5_done = weighment is not None or b_status in [
        "WEIGHED", "PROCURED", "STORED", "PAYMENT_INITIATED", "PAID"
    ]
    step5_time = weighment.weighed_at.strftime("%Y-%m-%d %H:%M") if (weighment and weighment.weighed_at) else None

    step6_done = storage is not None or b_status in [
        "STORED", "PAYMENT_INITIATED", "PAID"
    ]
    step6_time = storage.created_at.strftime("%Y-%m-%d %H:%M") if (storage and storage.created_at) else None

    step7_done = (payment is not None and payment.status in ["INITIATED", "PROCESSING", "PAID"]) or b_status in [
        "PAYMENT_INITIATED", "PAID"
    ]
    step7_time = payment.created_at.strftime("%Y-%m-%d %H:%M") if (payment and payment.created_at) else None

    step8_done = (payment is not None and payment.status == "PAID") or b_status == "PAID"
    step8_time = payment.payment_date.strftime("%Y-%m-%d %H:%M") if (payment and payment.payment_date) else None

    steps = [
        {"step_number": 1, "step_id": "BOOKED", "name": "BOOKED", "step_name": "Booked", "completed": step1_done, "timestamp": step1_time, "description": f"Appointment booked for {b.crop} ({float(b.quantity)} Qtl)"},
        {"step_number": 2, "step_id": "CHECKED_IN", "name": "CHECKED IN", "step_name": "Checked In", "completed": step2_done, "timestamp": step2_time, "description": "Gate entry verified via QR Code"},
        {"step_number": 3, "step_id": "ARRIVED", "name": "ARRIVED", "step_name": "Arrived", "completed": step3_done, "timestamp": step3_time, "description": "Vehicle docked at intake queue"},
        {"step_number": 4, "step_id": "QUALITY_CHECK", "name": "QUALITY CHECK", "step_name": "Quality Check", "completed": step4_done, "timestamp": step4_time, "description": "Moisture, cleanliness and foreign matter assessed"},
        {"step_number": 5, "step_id": "WEIGHING", "name": "WEIGHING", "step_name": "Weighing", "completed": step5_done, "timestamp": step5_time, "description": "Gross & tare weight verified at certified weighbridge"},
        {"step_number": 6, "step_id": "STORAGE", "name": "STORAGE", "step_name": "Storage", "completed": step6_done, "timestamp": step6_time, "description": "Bags stacked and tagged in buffer warehouse"},
        {"step_number": 7, "step_id": "PAYMENT_INITIATED", "name": "PAYMENT INITIATED", "step_name": "Payment Initiated", "completed": step7_done, "timestamp": step7_time, "description": "DBT payment voucher generated & submitted to PFMS"},
        {"step_number": 8, "step_id": "PAID", "name": "PAID", "step_name": "Paid", "completed": step8_done, "timestamp": step8_time, "description": "Direct bank transfer credited to registered account"}
    ]

    completed_steps = [s for s in steps if s["completed"]]
    pending_steps = [s for s in steps if not s["completed"]]

    # Current process name
    if step8_done:
        current_process_name = "Procurement Complete & Paid"
    elif step7_done:
        current_process_name = "Bank Disbursement in Progress"
    elif step6_done:
        current_process_name = "Payment Order Generation"
    elif step5_done:
        current_process_name = "Warehouse Stacking & Storage Allocation"
    elif step4_done:
        current_process_name = "Gross & Tare Weighbridge Measurement"
    elif step3_done:
        current_process_name = "Quality & Moisture Grading"
    elif step2_done:
        current_process_name = "Vehicle Docking & Intake Queue"
    elif step1_done:
        current_process_name = "Awaiting Gate Arrival & Check-In"
    else:
        current_process_name = "Scheduled"

    # Actual quantity received
    actual_quantity = None
    if weighment and weighment.net_weight_quintals:
        actual_quantity = float(weighment.net_weight_quintals)
    elif procurement and procurement.procured_quantity_quintals:
        actual_quantity = float(procurement.procured_quantity_quintals)
    elif collection and collection.collected_quantity:
        actual_quantity = float(collection.collected_quantity)

    # Quality details
    quality_result = None
    if quality:
        quality_result = {
            "check_id": quality.check_id,
            "quality_grade": quality.quality_grade,
            "moisture_content_pct": float(quality.moisture_content_pct),
            "foreign_matter_pct": float(quality.foreign_matter_pct),
            "broken_grains_pct": float(quality.broken_grains_pct),
            "passed": quality.passed,
            "inspector_name": quality.inspector_name,
            "checked_at": quality.checked_at.strftime("%Y-%m-%d %H:%M") if quality.checked_at else None
        }

    # Payment details
    payment_info = None
    if payment:
        payment_info = {
            "payment_id": payment.payment_id,
            "status": payment.status,
            "amount_inr": float(payment.amount_paid or payment.payment_amount or 0.0),
            "reference_number": payment.transaction_reference or payment.payment_reference,
            "bank_account_last4": getattr(payment, "account_number", "")[-4:] if getattr(payment, "account_number", None) else "XXXX",
            "payment_date": payment.payment_date.strftime("%Y-%m-%d") if payment.payment_date else None
        }


    relevant_timestamp = step8_time or step7_time or step6_time or step5_time or step4_time or step3_time or step2_time or step1_time

    return {
        "success": True,
        "booking_id": b.id,
        "appointment_id": b.appointment_id,
        "crop": b.crop,
        "booked_quantity": float(b.quantity),
        "centre_name": centre.centre_name if centre else b.centre_id,
        "centre_location": centre.location if centre else "",
        "slot_date": str(slot.date) if slot else None,
        "time_slot": f"{slot.start_time} - {slot.end_time}" if slot else "",
        "current_status": b_status,
        "active_process": current_process_name,
        "current_process_name": current_process_name,
        "completed_count": len(completed_steps),
        "total_steps": 8,
        "progress_percentage": round((len(completed_steps) / 8.0) * 100, 1),
        "steps": steps,
        "completed_steps": [s["step_name"] for s in completed_steps],
        "pending_steps": [s["step_name"] for s in pending_steps],
        "actual_quantity_received": actual_quantity,
        "quality_result": quality_result,
        "payment_status": payment_info,
        "relevant_timestamp": relevant_timestamp
    }

