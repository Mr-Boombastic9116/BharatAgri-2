from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from backend.app.core.database import get_db
from backend.app.models.centre import Slot, DailyCapacity, NonOperationalDate, ProcurementCentre
from backend.app.models.booking import Booking
from backend.app.schemas.centre import SlotCreate, SlotUpdate, SlotResponse, ApplyScheduleRangeRequest

router = APIRouter(prefix="/slots", tags=["Slots"])

day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

def get_weekday_name(d_str: str) -> str:
    dt = datetime.strptime(d_str, "%Y-%m-%d")
    return day_names[dt.weekday()]

@router.get("", response_model=List[SlotResponse])
def get_slots(centre_id: str = Query(...), date: str = Query(...), db: Session = Depends(get_db)):
    slots = (
        db.query(
            Slot,
            func.coalesce(func.sum(case((Booking.status != 'REJECTED', 1), else_=0)), 0).label("booked_count")
        )

        .outerjoin(Booking, Booking.slot_id == Slot.id)
        .filter(Slot.centre_id == centre_id, Slot.date == date)
        .group_by(Slot.id)
        .order_by(Slot.id.asc())
        .all()
    )

    formatted = []
    for s, booked in slots:
        rem = max(0, s.max_capacity - booked)
        if rem <= 0:
            status_label = "Full"
        elif booked > 0:
            status_label = "Partially Booked"
        else:
            status_label = "Available"

        formatted.append({
            "id": s.id,
            "centre_id": s.centre_id,
            "date": str(s.date),
            "start_time": s.start_time,
            "end_time": s.end_time,
            "max_capacity": s.max_capacity,
            "booked_count": booked,
            "remaining_capacity": rem,
            "status_label": status_label,
            "is_full": rem <= 0
        })

    return formatted

@router.post("", status_code=201)
def create_slot(req: SlotCreate, db: Session = Depends(get_db)):
    if req.max_capacity <= 0:
        raise HTTPException(status_code=400, detail="Maximum capacity must be a positive number.")

    existing = db.query(Slot).filter(
        Slot.centre_id == req.centre_id,
        Slot.date == req.date,
        Slot.start_time == req.start_time,
        Slot.end_time == req.end_time
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"A slot for {req.start_time} - {req.end_time} already exists on {req.date}.")

    new_slot = Slot(
        centre_id=req.centre_id,
        date=req.date,
        start_time=req.start_time,
        end_time=req.end_time,
        max_capacity=req.max_capacity
    )
    db.add(new_slot)
    db.commit()
    db.refresh(new_slot)

    return {
        "message": "Slot created successfully",
        "slot": {
            "id": new_slot.id,
            "centre_id": new_slot.centre_id,
            "date": str(new_slot.date),
            "start_time": new_slot.start_time,
            "end_time": new_slot.end_time,
            "max_capacity": new_slot.max_capacity,
            "booked_count": 0,
            "remaining_capacity": new_slot.max_capacity,
            "status_label": "Available",
            "is_full": False
        }
    }

@router.put("/{slot_id}")
def update_slot(slot_id: int, req: SlotUpdate, db: Session = Depends(get_db)):
    if req.max_capacity <= 0:
        raise HTTPException(status_code=400, detail="Maximum capacity must be a positive number.")

    slot = db.query(Slot).filter(Slot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found.")

    booked_count = db.query(Booking).filter(Booking.slot_id == slot_id, Booking.status != "REJECTED").count()
    if req.max_capacity < booked_count:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reduce slot capacity below existing farmer bookings ({booked_count} booked)."
        )

    slot.max_capacity = req.max_capacity
    db.commit()

    return {
        "message": "Slot capacity updated successfully",
        "id": slot.id,
        "max_capacity": slot.max_capacity,
        "booked_count": booked_count,
        "remaining_capacity": slot.max_capacity - booked_count
    }

@router.delete("/{slot_id}")
def delete_slot(slot_id: int, db: Session = Depends(get_db)):
    booked_count = db.query(Booking).filter(Booking.slot_id == slot_id, Booking.status != "REJECTED").count()
    if booked_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete slot with active farmer bookings ({booked_count} booked)."
        )

    slot = db.query(Slot).filter(Slot.id == slot_id).first()
    if slot:
        db.delete(slot)
        db.commit()

    return {"message": "Slot deleted successfully."}

@router.post("/apply-schedule-range")
def apply_schedule_range(req: ApplyScheduleRangeRequest, db: Session = Depends(get_db)):
    from_date = req.from_date or req.start_date
    to_date = req.to_date or req.end_date

    if not from_date or not to_date or not req.time_slots:
        raise HTTPException(status_code=400, detail="from_date/start_date, to_date/end_date, and time_slots are required.")

    centre = db.query(ProcurementCentre).filter(ProcurementCentre.centre_id == req.centre_id).first()
    op_days = centre.operating_days if centre and centre.operating_days else "Monday,Tuesday,Wednesday,Thursday,Friday,Saturday"
    allowed_days = [d.strip().lower() for d in op_days.split(",") if d.strip()]

    exceptions = db.query(NonOperationalDate).filter(NonOperationalDate.centre_id == req.centre_id).all()
    exception_map = {str(e.date): e.reason for e in exceptions}

    start_dt = datetime.strptime(from_date, "%Y-%m-%d").date()
    end_dt = datetime.strptime(to_date, "%Y-%m-%d").date()

    created_count = 0
    skipped_dates = []

    curr = start_dt
    while curr <= end_dt:
        d_str = curr.strftime("%Y-%m-%d")
        w_name = get_weekday_name(d_str).lower()

        if w_name not in allowed_days:
            skipped_dates.append({"date": d_str, "reason": f"Non-operational day ({w_name.capitalize()})"})
            curr += timedelta(days=1)
            continue

        if d_str in exception_map:
            skipped_dates.append({"date": d_str, "reason": f"Holiday exception ({exception_map[d_str]})"})
            curr += timedelta(days=1)
            continue

        # Upsert daily capacity
        cap_row = db.query(DailyCapacity).filter(DailyCapacity.centre_id == req.centre_id, DailyCapacity.date == d_str).first()
        if not cap_row:
            db.add(DailyCapacity(centre_id=req.centre_id, date=d_str, max_quintals_per_day=req.max_quintals_per_day or 800.0))

        for ts in req.time_slots:
            slot_exists = db.query(Slot).filter(
                Slot.centre_id == req.centre_id,
                Slot.date == d_str,
                Slot.start_time == ts.start_time,
                Slot.end_time == ts.end_time
            ).first()
            if not slot_exists:
                db.add(Slot(
                    centre_id=req.centre_id,
                    date=d_str,
                    start_time=ts.start_time,
                    end_time=ts.end_time,
                    max_capacity=ts.max_capacity
                ))

        created_count += 1
        curr += timedelta(days=1)

    db.commit()

    return {
        "message": f"Schedule applied to {created_count} operational dates. Skipped {len(skipped_dates)} non-operational dates.",
        "created_dates_count": created_count,
        "skipped_dates_count": len(skipped_dates),
        "skipped_dates": skipped_dates
    }
