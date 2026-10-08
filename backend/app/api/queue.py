from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
import pandas as pd
import os
import datetime

from backend.app.core.database import get_db
from backend.app.models.queue import Notification, ProcurementTransaction, Appointment
from backend.app.models.farmer import Farmer
from backend.app.models.booking import Booking
from sqlalchemy import cast, String
from backend.app.services.queue_engine import (
    queue_engine, get_live_centre_queue, track_token_or_appointment,
    recommend_best_centre, get_centre_congestion_forecast,
    query_procurement_copilot, detect_operational_anomalies,
    get_dynamic_recommended_slots, query_centre_copilot
)

def resolve_farmer_ids(farmer_id: str, db: Session) -> List[str]:
    fid = (farmer_id or "").strip()
    ids = [fid]
    farmer = db.query(Farmer).filter(
        (Farmer.user_id == fid) | (Farmer.farmer_code == fid) | (cast(Farmer.id, String) == fid)
    ).first()
    if not farmer and (fid == "farmer@bharatagri.demo" or fid.lower() == "farmer"):
        farmer = db.query(Farmer).filter(Farmer.farmer_code == "F00001").first()
    if farmer:
        for candidate in [farmer.farmer_code, farmer.user_id, str(farmer.id)]:
            if candidate and candidate not in ids:
                ids.append(candidate)
    return ids


router = APIRouter(prefix="/queue", tags=["Dynamic AI Queue & Intelligence"])

CROPS_MASTER_PATH = "data/processed/crops/crops_master.csv"

@router.get("/live/{centre_id}")
def get_live_queue(centre_id: str, db: Session = Depends(get_db)):
    """Live queue status driven by real queue events and ML engine."""
    res = get_live_centre_queue(centre_id, db)
    if not res:
        raise HTTPException(status_code=404, detail=f"Centre {centre_id} not found.")
    return {"success": True, "data": res}


@router.get("/token/{token_or_id}")
def track_token(token_or_id: str, db: Session = Depends(get_db)):
    """Live digital token tracking, position, estimated wait, and departure time."""
    res = track_token_or_appointment(token_or_id, db)
    if not res:
        raise HTTPException(status_code=404, detail=f"Token or Appointment '{token_or_id}' not found.")
    return {"success": True, "data": res}


@router.post("/recommend-centre")
def recommend_centre(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """Dynamic centre recommendation considering crop, distance, queue, wait time, and capacity."""
    crop = payload.get("crop", "Paddy")
    qty = float(payload.get("quantity", 50.0))
    farmer_id = payload.get("farmer_id")
    district = payload.get("district")

    recommendations = recommend_best_centre(crop, qty, farmer_id, district, db)
    return {
        "success": True,
        "crop": crop,
        "quantity": qty,
        "centres": recommendations,
        "best_centre": recommendations[0] if recommendations else None
    }


@router.get("/recommended-slots/{centre_id}")
def get_recommended_slots(
    centre_id: str,
    date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Dynamic slot allocation with predicted congestion, queue depth, and explainable recommendations."""
    return get_dynamic_recommended_slots(centre_id, date, db)


@router.post("/predict-wait")
def predict_wait(payload: Dict[str, Any] = Body(...)):
    """Queue prediction engine comparing baseline queueing formula against ML model."""
    q_len = int(payload.get("queue_before", 15))
    machines = int(payload.get("active_weighing_machines", 2))
    staff = int(payload.get("staff_available", 8))
    eq_fail = int(payload.get("equipment_failure_flag", 0))
    w_delay = int(payload.get("weather_delay_flag", 0))
    dist_km = float(payload.get("travel_distance_km", 15.0))
    hist_proc = float(payload.get("historical_avg_processing_min", 16.0))
    hr = int(payload.get("hour", 10))
    dow = int(payload.get("day_of_week", 2))
    peak = int(payload.get("is_peak_hour", 0))

    res = queue_engine.predict_wait_time(
        queue_before=q_len,
        active_weighing_machines=machines,
        staff_available=staff,
        equipment_failure_flag=eq_fail,
        weather_delay_flag=w_delay,
        travel_distance_km=dist_km,
        historical_avg_processing_min=hist_proc,
        hour=hr,
        day_of_week=dow,
        is_peak_hour=peak
    )
    return {"success": True, "data": res}


@router.get("/congestion-forecast/{centre_id}")
def get_congestion_forecast(centre_id: str, db: Session = Depends(get_db)):
    """Hourly congestion forecast (8 AM - 5 PM) based on historical daily metrics."""
    res = get_centre_congestion_forecast(centre_id, db)
    if not res:
        raise HTTPException(status_code=404, detail=f"Centre {centre_id} not found.")
    return {"success": True, "data": res}


@router.get("/notifications/{farmer_id}")
def get_farmer_notifications(farmer_id: str, db: Session = Depends(get_db)):
    """Notifications including COME_NOW alerts and queue updates."""
    ids = resolve_farmer_ids(farmer_id, db)
    notifs = db.query(Notification).filter(
        Notification.farmer_id.in_(ids)
    ).order_by(Notification.sent_at.desc()).limit(20).all()

    items = [
        {
            "notification_id": n.notification_id,
            "type": n.notification_type,
            "channel": n.channel,
            "message": n.message or f"Update for {n.notification_type}",
            "sent_at": n.sent_at.strftime("%d %b %Y, %I:%M %p") if n.sent_at else "",
            "delivery_status": n.delivery_status,
            "response": n.response
        } for n in notifs
    ]
    return {"success": True, "farmer_id": farmer_id, "notifications": items}


@router.post("/copilot")
def copilot_query(payload: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    """Officer Procurement Copilot answering operational queries with actual database state."""
    q_text = payload.get("query", "").strip()
    if not q_text:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    res = query_procurement_copilot(q_text, db)
    return {"success": True, "data": res}


@router.post("/centre-copilot/{centre_id}")
def centre_copilot_query(centre_id: str, payload: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    """Scoped Centre Copilot strictly isolated to the authenticated centre_id."""
    q_text = payload.get("query", "").strip()
    if not q_text:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    res = query_centre_copilot(centre_id, q_text, db)
    return {"success": True, "data": res}


@router.get("/anomalies")
def get_anomalies(db: Session = Depends(get_db)):
    """AI Anomaly & Transparency Review flags for human review."""
    anoms = detect_operational_anomalies(db)
    return {
        "success": True,
        "total_anomalies": len(anoms),
        "status_notice": "Alerts are flagged for human review, not automated accusation.",
        "anomalies": anoms
    }


@router.get("/crops-master")
def get_crops_master():
    """Returns normalized crop master list from data/processed/crops/crops_master.csv."""
    if not os.path.exists(CROPS_MASTER_PATH):
        raise HTTPException(status_code=404, detail="crops_master.csv not found.")
    df = pd.read_csv(CROPS_MASTER_PATH)
    records = df.to_dict(orient="records")
    return {"success": True, "total_crops": len(records), "crops": records}


@router.get("/farmer-overview/{farmer_id}")
def get_farmer_overview(farmer_id: str, db: Session = Depends(get_db)):
    """
    Simplified single-call endpoint for Farmer Dashboard:
    Returns upcoming booking, live token, payment summary, and come-now alert.
    """
    ids = resolve_farmer_ids(farmer_id, db)

    # 1. Latest / upcoming appointment or booking
    appt = db.query(Appointment).filter(
        Appointment.farmer_id.in_(ids)
    ).order_by(Appointment.slot_start.desc()).first()

    token_data = None
    if appt:
        token_data = track_token_or_appointment(appt.appointment_id, db)
    else:
        # Fallback to Booking model
        b = db.query(Booking).filter(
            Booking.farmer_id.in_(ids)
        ).order_by(Booking.id.desc()).first()
        if b:
            token_data = track_token_or_appointment(b.appointment_id or b.qr_token, db)

    # 2. Payment summary from ProcurementTransaction
    transactions = db.query(ProcurementTransaction).filter(
        ProcurementTransaction.farmer_id.in_(ids)
    ).order_by(ProcurementTransaction.procurement_timestamp.desc()).all()

    total_procured_rs = sum(float(t.gross_amount_rs) for t in transactions)
    paid_rs = sum(float(t.gross_amount_rs) for t in transactions if t.payment_status == 'PAID')
    pending_rs = total_procured_rs - paid_rs

    recent_txns = [
        {
            "procurement_id": t.procurement_id,
            "crop": t.crop,
            "quantity_quintals": float(t.quantity_quintals),
            "rate_rs_per_quintal": float(t.procurement_rate_rs_per_quintal),
            "gross_amount_rs": float(t.gross_amount_rs),
            "payment_status": t.payment_status,
            "date": t.procurement_timestamp.strftime("%d %b %Y") if t.procurement_timestamp else ""
        } for t in transactions[:5]
    ]

    return {
        "success": True,
        "farmer_id": farmer_id,
        "has_active_token": token_data is not None,
        "token_tracking": token_data,
        "payment_summary": {
            "total_earnings_rs": round(total_procured_rs, 2),
            "paid_rs": round(paid_rs, 2),
            "pending_rs": round(pending_rs, 2),
            "total_transactions": len(transactions),
            "recent_transactions": recent_txns
        }
    }
