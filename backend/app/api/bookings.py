import random
from datetime import datetime, date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, text, cast, String

from backend.app.core.database import get_db
from backend.app.core.helpers import resolve_centre
from backend.app.models.booking import Booking, BookingStatusHistory, QRCode
from backend.app.models.centre import Slot, DailyCapacity, NonOperationalDate, ProcurementCentre
from backend.app.models.farmer import Farmer
from backend.app.models.user import User
from backend.app.models.audit import AuditLog
from backend.app.schemas.booking import BookingCreate, StatusUpdateRequest

router = APIRouter(prefix="/bookings", tags=["Bookings"])

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

    # 6. Crop support check
    if centre.supported_crops:
        supp = [c.strip().lower() for c in centre.supported_crops.split(",") if c.strip()]
        if req.crop.strip().lower() not in supp:
            raise HTTPException(status_code=400, detail=f"Crop '{req.crop}' is not supported by {centre.centre_name}.")

    # 7. Generate Appointment ID & QR Code
    appt_id = generate_appointment_id(str(slot_date), db)
    qr_token = f"BA-QR-{appt_id}"

    try:
        new_booking = Booking(
            appointment_id=appt_id,
            booking_id=appt_id,
            farmer_id=req.farmer_id.strip(),
            centre_id=req.centre_id.strip(),
            slot_id=req.slot_id,
            crop=req.crop.strip(),
            quantity=req.quantity,
            status="CONFIRMED",
            qr_token=qr_token
        )
        db.add(new_booking)
        db.flush()

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
            changed_by=req.farmer_id.strip(),
            notes="Initial appointment confirmed"
        ))

        # Audit
        db.add(AuditLog(
            user_id=req.farmer_id.strip(),
            action="BOOKING_CREATED",
            entity="BOOKING",
            entity_id=appt_id,
            new_value=f"Centre: {req.centre_id}, Crop: {req.crop}, Qty: {req.quantity}Q"
        ))

        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Transaction failed while creating booking: {str(e)}")

    # Fetch farmer name for response
    farmer = db.query(Farmer).filter(Farmer.user_id == req.farmer_id).first()
    f_user = db.query(User).filter(User.user_id == req.farmer_id).first()
    f_name = farmer.name if farmer else (f_user.name if f_user else req.farmer_id)
    f_mobile = farmer.mobile if farmer else (f_user.mobile if f_user else "")

    return {
        "message": "Appointment booked successfully!",
        "booking": {
            "id": new_booking.id,
            "appointment_id": appt_id,
            "booking_id": appt_id,
            "farmer_id": req.farmer_id,
            "farmer_name": f_name,
            "farmer_mobile": f_mobile,
            "centre_id": centre.centre_id,
            "centre_name": centre.centre_name,
            "location": centre.location,
            "crop": req.crop,
            "quantity": req.quantity,
            "date": str(slot.date),
            "start_time": slot.start_time,
            "end_time": slot.end_time,
            "time_slot": f"{slot.start_time} - {slot.end_time}",
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
    bookings = (
        db.query(Booking, Slot, ProcurementCentre)
        .join(Slot, Booking.slot_id == Slot.id)
        .join(ProcurementCentre, Booking.centre_id == ProcurementCentre.centre_id)
        .filter(Booking.farmer_id == farmer_id)
        .order_by(Booking.id.desc())
        .all()
    )

    f_user = db.query(User).filter(User.user_id == farmer_id).first()
    f_name = f_user.name if f_user else farmer_id
    f_mobile = f_user.mobile if f_user else ""

    result = []
    for b, s, pc in bookings:
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
            "qr_token": b.qr_token,
            "redirected_from_centre_id": b.redirected_from_centre_id,
            "verified_at": str(b.verified_at) if b.verified_at else None,
            "created_at": str(b.created_at)
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
