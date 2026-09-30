from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, String


from backend.app.core.database import get_db
from backend.app.models.centre import ProcurementCentre, DailyCapacity, NonOperationalDate, Slot
from backend.app.models.booking import Booking
from backend.app.models.procurement import ProcurementRecord, QualityCheck, CollectionRecord
from backend.app.models.logistics import Truck
from backend.app.models.inventory import BardanStock
from backend.app.models.ai import AnomalyRecord, CentreCongestion
from backend.app.models.audit import AuditLog
from backend.app.schemas.centre import OperatingDaysUpdate, NonOperationalDateCreate, DailyCapacityUpdate

router = APIRouter(tags=["Centres"])

@router.get("/centres")
def get_centres(db: Session = Depends(get_db)):
    centres = db.query(ProcurementCentre).order_by(ProcurementCentre.centre_name.asc()).all()
    result = []
    for c in centres:
        result.append({
            "id": c.id,
            "centre_id": c.centre_id,
            "centre_name": c.centre_name,
            "location": c.location,
            "state": c.state,
            "district": c.district,
            "contact_number": c.contact_number,
            "operating_days": c.operating_days,
            "opening_time": c.opening_time,
            "closing_time": c.closing_time,
            "supported_crops": c.supported_crops,
            "max_daily_capacity_quintals": float(c.max_daily_capacity_quintals or 800.0),
            "status": c.status
        })
    return result

@router.get("/centres/{centre_id}")
def get_centre_details(centre_id: str, db: Session = Depends(get_db)):
    c = db.query(ProcurementCentre).filter(
        (ProcurementCentre.centre_id == centre_id) | (cast(ProcurementCentre.id, String) == centre_id)

    ).first()

    if not c:
        raise HTTPException(status_code=404, detail="Procurement Centre not found.")

    return {
        "id": c.id,
        "centre_id": c.centre_id,
        "centre_name": c.centre_name,
        "location": c.location,
        "state": c.state,
        "district": c.district,
        "contact_number": c.contact_number,
        "operating_days": c.operating_days,
        "opening_time": c.opening_time,
        "closing_time": c.closing_time,
        "supported_crops": c.supported_crops,
        "max_daily_capacity_quintals": float(c.max_daily_capacity_quintals or 800.0),
        "total_storage_capacity_quintals": float(c.total_storage_capacity_quintals or 15000.0),
        "current_storage_usage_quintals": float(c.current_storage_usage_quintals or 3200.0),
        "status": c.status
    }

@router.get("/centres/{centre_id}/operating-config")
def get_operating_config(centre_id: str, db: Session = Depends(get_db)):
    c = db.query(ProcurementCentre).filter(ProcurementCentre.centre_id == centre_id).first()
    exceptions = db.query(NonOperationalDate).filter(NonOperationalDate.centre_id == centre_id).order_by(NonOperationalDate.date.asc()).all()

    op_days = c.operating_days if c and c.operating_days else "Monday,Tuesday,Wednesday,Thursday,Friday,Saturday"
    if op_days == "[object Object]":
        op_days = "Monday,Tuesday,Wednesday,Thursday,Friday,Saturday"

    return {
        "centre_id": centre_id,
        "operating_days": op_days,
        "opening_time": c.opening_time if c else "09:00 AM",
        "closing_time": c.closing_time if c else "05:00 PM",
        "non_operational_dates": [{"id": e.id, "date": str(e.date), "reason": e.reason} for e in exceptions]
    }

@router.put("/centres/{centre_id}/operating-days")
def update_operating_days(centre_id: str, req: OperatingDaysUpdate, db: Session = Depends(get_db)):
    days = req.operating_days
    if isinstance(days, list):
        formatted = ",".join(str(d).strip() for d in days if str(d).strip())
    else:
        formatted = str(days).strip()

    if not formatted:
        raise HTTPException(status_code=400, detail="operating_days cannot be empty.")

    c = db.query(ProcurementCentre).filter(ProcurementCentre.centre_id == centre_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Centre not found.")

    old_days = c.operating_days
    c.operating_days = formatted

    audit = AuditLog(
        user_id=centre_id,
        action="OPERATING_DAYS_UPDATED",
        entity="PROCUREMENT_CENTRE",
        entity_id=centre_id,
        old_value=old_days,
        new_value=formatted
    )
    db.add(audit)
    db.commit()

    return {"message": "Operating days updated successfully.", "operating_days": formatted}

@router.post("/centres/{centre_id}/non-operational-dates", status_code=201)
def add_non_operational_date(centre_id: str, req: NonOperationalDateCreate, db: Session = Depends(get_db)):
    if not req.date:
        raise HTTPException(status_code=400, detail="Date is required for non-operational exception.")

    # Check active bookings
    active_b = (
        db.query(Booking)
        .join(Slot, Booking.slot_id == Slot.id)
        .filter(Booking.centre_id == centre_id, Slot.date == req.date, Booking.status != "REJECTED")
        .count()
    )
    if active_b > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot mark {req.date} non-operational because {active_b} active farmer bookings exist."
        )

    existing = db.query(NonOperationalDate).filter(NonOperationalDate.centre_id == centre_id, NonOperationalDate.date == req.date).first()
    if existing:
        existing.reason = req.reason or "Non-operational date"
    else:
        new_ex = NonOperationalDate(
            centre_id=centre_id,
            date=req.date,
            reason=req.reason or "Non-operational date"
        )
        db.add(new_ex)

    audit = AuditLog(
        user_id=centre_id,
        action="NON_OPERATIONAL_DATE_ADDED",
        entity="PROCUREMENT_CENTRE",
        entity_id=centre_id,
        new_value=f"Date: {req.date}, Reason: {req.reason}"
    )
    db.add(audit)
    db.commit()

    return {"message": f"Non-operational date {req.date} added successfully.", "date": req.date, "reason": req.reason}

@router.delete("/centres/{centre_id}/non-operational-dates/{date_str}")
def delete_non_operational_date(centre_id: str, date_str: str, db: Session = Depends(get_db)):
    ex = db.query(NonOperationalDate).filter(NonOperationalDate.centre_id == centre_id, NonOperationalDate.date == date_str).first()
    if ex:
        db.delete(ex)
        db.commit()
    return {"message": f"Non-operational exception for {date_str} removed."}

# Daily capacity
@router.get("/daily-capacity")
def get_daily_capacity(centre_id: str, date: str, db: Session = Depends(get_db)):
    cap_row = db.query(DailyCapacity).filter(DailyCapacity.centre_id == centre_id, DailyCapacity.date == date).first()
    max_q = float(cap_row.max_quintals_per_day) if cap_row else 800.0

    sum_booked = (
        db.query(func.coalesce(func.sum(Booking.quantity), 0))
        .join(Slot, Booking.slot_id == Slot.id)
        .filter(Booking.centre_id == centre_id, Slot.date == date, Booking.status != "REJECTED")
        .scalar()
    )
    booked_q = float(sum_booked)
    remaining_q = max(0.0, max_q - booked_q)

    return {
        "centre_id": centre_id,
        "date": date,
        "max_quintals_per_day": max_q,
        "booked_quintals": round(booked_q, 2),
        "remaining_quintals": round(remaining_q, 2),
        "is_full": remaining_q <= 0
    }

@router.put("/daily-capacity")
def update_daily_capacity(req: DailyCapacityUpdate, db: Session = Depends(get_db)):
    if req.max_quintals_per_day <= 0:
        raise HTTPException(status_code=400, detail="Daily capacity must be a positive number.")

    sum_booked = (
        db.query(func.coalesce(func.sum(Booking.quantity), 0))
        .join(Slot, Booking.slot_id == Slot.id)
        .filter(Booking.centre_id == req.centre_id, Slot.date == req.date, Booking.status != "REJECTED")
        .scalar()
    )
    booked_q = float(sum_booked)

    if req.max_quintals_per_day < booked_q:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reduce daily capacity below the quantity already booked ({booked_q} Quintals booked)."
        )

    cap_row = db.query(DailyCapacity).filter(DailyCapacity.centre_id == req.centre_id, DailyCapacity.date == req.date).first()
    if cap_row:
        cap_row.max_quintals_per_day = req.max_quintals_per_day
    else:
        cap_row = DailyCapacity(
            centre_id=req.centre_id,
            date=req.date,
            max_quintals_per_day=req.max_quintals_per_day
        )
        db.add(cap_row)

    db.commit()
    return {
        "message": "Daily capacity updated successfully",
        "centre_id": req.centre_id,
        "date": req.date,
        "max_quintals_per_day": req.max_quintals_per_day,
        "booked_quintals": booked_q,
        "remaining_quintals": req.max_quintals_per_day - booked_q
    }

# Centre Overview Dashboard
@router.get("/centres/{centre_id}/overview")
def get_centre_overview(centre_id: str, db: Session = Depends(get_db)):
    centre = db.query(ProcurementCentre).filter(ProcurementCentre.centre_id == centre_id).first()
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found.")

    # Total Bookings today and upcoming
    total_bookings = db.query(Booking).filter(Booking.centre_id == centre_id).count()
    procured_count = db.query(ProcurementRecord).filter(ProcurementRecord.centre_id == centre_id).count()
    total_procured_qty = float(db.query(func.coalesce(func.sum(ProcurementRecord.procured_quantity_quintals), 0)).filter(ProcurementRecord.centre_id == centre_id).scalar())

    # Bardan Stock
    bardan = db.query(BardanStock).filter(BardanStock.centre_id == centre_id).first()
    avail_bags = bardan.available_bags if bardan else 18000

    # Trucks assigned
    trucks_count = db.query(Truck).filter(Truck.assigned_centre_id == centre_id).count()
    trucks_avail = db.query(Truck).filter(Truck.assigned_centre_id == centre_id, Truck.is_available == True).count()

    # Open Anomalies
    open_anomalies = db.query(AnomalyRecord).filter(AnomalyRecord.centre_id == centre_id, AnomalyRecord.status.in_(["OPEN", "UNDER REVIEW"])).count()

    # Congestion info
    cong = db.query(CentreCongestion).filter(CentreCongestion.centre_id == centre_id).order_by(CentreCongestion.id.desc()).first()

    return {
        "centre_id": centre.centre_id,
        "centre_name": centre.centre_name,
        "location": centre.location,
        "state": centre.state,
        "district": centre.district,
        "daily_capacity": float(centre.max_daily_capacity_quintals or 800.0),
        "total_bookings": total_bookings,
        "procured_count": procured_count,
        "total_procured_quintals": round(total_procured_qty, 2),
        "bardan_available_bags": avail_bags,
        "trucks_assigned": trucks_count,
        "trucks_available": trucks_avail,
        "open_anomalies": open_anomalies,
        "congestion_level": cong.congestion_level if cong else "LOW",
        "utilization_percent": float(cong.utilization_percent) if cong else 45.0
    }

# Dedicated Centre Detail Page for Government Monitoring
@router.get("/centres/{centre_id}/monitoring")
def get_centre_monitoring_details(centre_id: str, db: Session = Depends(get_db)):
    overview = get_centre_overview(centre_id, db)
    
    # Recent Bookings
    recent_bookings = (
        db.query(Booking)
        .filter(Booking.centre_id == centre_id)
        .order_by(Booking.id.desc())
        .limit(10)
        .all()
    )
    # Recent Quality checks
    recent_qc = (
        db.query(QualityCheck)
        .join(CollectionRecord, QualityCheck.collection_id == CollectionRecord.collection_id)
        .filter(CollectionRecord.centre_id == centre_id)
        .order_by(QualityCheck.id.desc())
        .limit(10)
        .all()
    )
    # Recent anomalies
    recent_anom = (
        db.query(AnomalyRecord)
        .filter(AnomalyRecord.centre_id == centre_id)
        .order_by(AnomalyRecord.id.desc())
        .limit(5)
        .all()
    )

    return {
        **overview,
        "recent_bookings": [
            {
                "appointment_id": b.appointment_id,
                "crop": b.crop,
                "quantity": float(b.quantity),
                "status": b.status,
                "date": str(b.slot.date) if b.slot else "2026-09-30"
            }
            for b in recent_bookings
        ],
        "recent_quality_checks": [
            {
                "check_id": q.check_id,
                "grade": q.quality_grade,
                "moisture": float(q.moisture_content_pct),
                "passed": q.passed,
                "inspector": q.inspector_name
            }
            for q in recent_qc
        ],
        "recent_anomalies": [
            {
                "code": a.anomaly_code,
                "type": a.anomaly_type,
                "risk": a.risk_level,
                "status": a.status,
                "reason": a.reason
            }
            for a in recent_anom
        ]
    }
