from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, String
from backend.app.core.database import get_db
from backend.app.models.agent import Agent, AgentFarmerAssignment
from backend.app.models.farmer import Farmer
from backend.app.models.booking import Booking
from backend.app.models.procurement import ProcurementRecord, Payment
from backend.app.models.audit import AuditLog

router = APIRouter(prefix="/agents", tags=["Agents"])

@router.get("/{id_or_uid}/farmers")
def get_assigned_farmers(
    id_or_uid: str,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db)
):
    agent = db.query(Agent).filter(
        (Agent.user_id == id_or_uid) | (Agent.agent_code == id_or_uid) | (cast(Agent.id, String) == id_or_uid)
    ).first()

    if not agent:
        raise HTTPException(status_code=404, detail="Agent profile not found.")

    query = (
        db.query(Farmer)
        .join(AgentFarmerAssignment, AgentFarmerAssignment.farmer_id == Farmer.id)
        .filter(AgentFarmerAssignment.agent_id == agent.id)
    )

    if search:
        s = f"%{search.strip()}%"
        query = query.filter((Farmer.name.ilike(s)) | (Farmer.farmer_code.ilike(s)) | (Farmer.mobile.ilike(s)))

    total = query.count()
    items = query.order_by(Farmer.id.asc()).offset((page - 1) * limit).limit(limit).all()

    result = []
    for f in items:
        # Check active booking
        active_b = db.query(Booking).filter(Booking.farmer_id == f.user_id).order_by(Booking.id.desc()).first()
        result.append({
            "id": f.id,
            "farmer_code": f.farmer_code,
            "user_id": f.user_id,
            "name": f.name,
            "mobile": f.mobile,
            "village": f.village,
            "district": f.district,
            "land_area_hectares": float(f.land_area_hectares),
            "ekyc_status": f.ekyc_status,
            "active_booking": active_b.appointment_id if active_b else "None",
            "active_status": active_b.status if active_b else "NO_BOOKING"
        })

    return {
        "agent_name": agent.name,
        "agent_code": agent.agent_code,
        "district": agent.district,
        "total_assigned_farmers": total,
        "page": page,
        "limit": limit,
        "farmers": result
    }

@router.get("/{id_or_uid}/stats")
def get_agent_dashboard_stats(id_or_uid: str, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(
        (Agent.user_id == id_or_uid) | (Agent.agent_code == id_or_uid) | (cast(Agent.id, String) == id_or_uid)
    ).first()

    if not agent:
        raise HTTPException(status_code=404, detail="Agent profile not found.")

    assigned_farmer_ids = [
        r[0] for r in db.query(AgentFarmerAssignment.farmer_id).filter(AgentFarmerAssignment.agent_id == agent.id).all()
    ]

    farmers_assisted = len(assigned_farmer_ids)
    
    # Farmer user_ids
    f_uids = [
        r[0] for r in db.query(Farmer.user_id).filter(Farmer.id.in_(assigned_farmer_ids)).all()
    ] if assigned_farmer_ids else []

    total_bookings = db.query(Booking).filter(Booking.farmer_id.in_(f_uids)).count() if f_uids else 0
    pending_bookings = db.query(Booking).filter(Booking.farmer_id.in_(f_uids), Booking.status == "CONFIRMED").count() if f_uids else 0
    completed_procurement = db.query(ProcurementRecord).filter(ProcurementRecord.farmer_id.in_(f_uids)).count() if f_uids else 0

    return {
        "agent_name": agent.name,
        "agent_code": agent.agent_code,
        "agency_type": agent.agency_type,
        "organization_name": agent.organization_name,
        "district": agent.district,
        "farmers_assisted": farmers_assisted,
        "total_bookings": total_bookings,
        "pending_bookings": pending_bookings,
        "completed_procurements": completed_procurement,
        "recent_alerts": [
            "Heavy rain expected next week. Advise farmers to book harvesting slots early.",
            "MSP rate for Paddy confirmed at Rs 2,300/Quintal for Kharif 2026.",
            "Biometric e-KYC mandatory before booking appointment passes."
        ]
    }
