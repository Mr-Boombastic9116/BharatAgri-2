from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.core.database import get_db
from backend.app.models.booking import Booking, BookingStatusHistory, QRCode
from backend.app.models.centre import Slot, ProcurementCentre
from backend.app.models.user import User
from backend.app.models.audit import AuditLog
from backend.app.schemas.booking import VerifyQRRequest

router = APIRouter(tags=["QR System"])

@router.post("/appointments/verify")
def verify_appointment_qr(req: VerifyQRRequest, db: Session = Depends(get_db)):
    if not req.qr_token or not req.centre_id:
        return {
            "success": False,
            "code": "INVALID_REQUEST",
            "error": "INVALID APPOINTMENT ✕",
            "message": "QR token and Centre ID are required."
        }

    clean_token = req.qr_token.strip()

    # Query booking matching token, appointment_id, or booking_id
    booking = (
        db.query(Booking)
        .filter(
            (func.lower(Booking.qr_token) == func.lower(clean_token)) |
            (func.lower(Booking.appointment_id) == func.lower(clean_token)) |
            (func.lower(Booking.booking_id) == func.lower(clean_token))
        )
        .first()
    )

    if not booking:
        return {
            "success": False,
            "code": "INVALID_QR",
            "error": "INVALID APPOINTMENT ✕",
            "message": "Entry Not Accepted. Unrecognized QR code."
        }

    if booking.centre_id != req.centre_id:
        return {
            "success": False,
            "code": "WRONG_CENTRE",
            "error": "WRONG PROCUREMENT CENTRE ✕",
            "message": f"Appointment belongs to centre '{booking.centre_id}', not this centre."
        }

    if booking.status in ["COLLECTED", "RECEIVED", "QUALITY_CHECKED", "WEIGHED", "PROCURED", "STORED", "PAYMENT_INITIATED", "PAID"]:
        return {
            "success": False,
            "code": "ALREADY_PROCESSED",
            "error": "ALREADY PROCESSED",
            "message": f"Appointment has already progressed past arrival (Status: {booking.status})."
        }

    if booking.status == "REJECTED":
        return {
            "success": False,
            "code": "REJECTED",
            "error": "APPOINTMENT REJECTED ✕",
            "message": "This appointment has been marked rejected."
        }

    slot = db.query(Slot).filter(Slot.id == booking.slot_id).first()
    today_str = datetime.utcnow().date().strftime("%Y-%m-%d")
    if slot and str(slot.date) < today_str:
        return {
            "success": False,
            "code": "EXPIRED",
            "error": "APPOINTMENT EXPIRED",
            "message": f"Scheduled arrival date ({slot.date}) has already passed."
        }

    # Verify and transition to ARRIVED
    verified_at = datetime.utcnow()
    old_st = booking.status
    booking.status = "ARRIVED"
    booking.verified_at = verified_at

    # Update QRCode record
    qr_rec = db.query(QRCode).filter(QRCode.qr_code_value == booking.qr_token).first()
    if qr_rec:
        qr_rec.is_used = True
        qr_rec.used_at = verified_at

    # History
    db.add(BookingStatusHistory(
        booking_id=booking.id,
        old_status=old_st,
        new_status="ARRIVED",
        changed_by=req.centre_id,
        notes="QR code scanned at arrival gate — Farmer Arrived"
    ))

    # Audit
    db.add(AuditLog(
        user_id=req.centre_id,
        action="QR_ENTRY_VERIFIED",
        entity="BOOKING",
        entity_id=booking.appointment_id,
        old_value=old_st,
        new_value="ARRIVED"
    ))

    db.commit()

    f_user = db.query(User).filter(User.user_id == booking.farmer_id).first()
    centre = db.query(ProcurementCentre).filter(ProcurementCentre.centre_id == booking.centre_id).first()

    return {
        "success": True,
        "code": "SUCCESS",
        "title": "APPOINTMENT FOUND ✓",
        "message": "Appointment verified successfully. Farmer checked-in at centre gate.",
        "appointment": {
            "appointment_id": booking.appointment_id,
            "farmer_id": booking.farmer_id,
            "farmer_name": f_user.name if f_user else booking.farmer_id,
            "farmer_mobile": f_user.mobile if f_user else "",
            "centre_id": booking.centre_id,
            "centre_name": centre.centre_name if centre else booking.centre_id,
            "location": centre.location if centre else "",
            "crop": booking.crop,
            "quantity": float(booking.quantity),
            "date": str(slot.date) if slot else today_str,
            "start_time": slot.start_time if slot else "09:00 AM",
            "end_time": slot.end_time if slot else "11:00 AM",
            "time_slot": f"{slot.start_time} - {slot.end_time}" if slot else "09:00 AM - 11:00 AM",
            "status": "ARRIVED",
            "verified_at": str(verified_at)
        }
    }
