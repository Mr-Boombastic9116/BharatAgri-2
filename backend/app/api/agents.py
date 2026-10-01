from typing import Optional, List
from datetime import date, timedelta
import random
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, String

from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user_optional, get_current_user, require_role
from backend.app.models.agent import Agent, AgentFarmerAssignment
from backend.app.models.farmer import Farmer, FarmerCrop
from backend.app.models.booking import Booking
from backend.app.models.centre import Slot
from backend.app.models.procurement import ProcurementRecord, Payment
from backend.app.models.audit import AuditLog

router = APIRouter(prefix="/agents", tags=["Agents"])

class AgentFarmerRegister(BaseModel):
    name: str
    mobile: str
    village: Optional[str] = "Ponda"
    district: Optional[str] = None
    state: Optional[str] = None
    taluka: Optional[str] = None
    aadhaar_hash: Optional[str] = "AADHAAR-OK"
    land_area_hectares: Optional[float] = 2.5
    primary_crop: Optional[str] = "Paddy"
    estimated_quantity: Optional[float] = 30.0

def resolve_agent(agent_id_or_uid: Optional[str], db: Session, current_user = None) -> Agent:
    aid = (agent_id_or_uid or "").strip()
    if not aid or aid.lower() in ["me", "self", "farmers", "stats"]:
        if current_user:
            aid = current_user.user_id
        else:
            aid = "agent@bharatagri.demo"

    agent = db.query(Agent).filter(
        (Agent.user_id == aid) | (Agent.agent_code == aid) | (cast(Agent.id, String) == aid)
    ).first()

    if not agent and current_user:
        agent = db.query(Agent).filter(
            (Agent.email == current_user.email) | (Agent.mobile == current_user.mobile)
        ).first()

    if not agent:
        agent = db.query(Agent).filter(Agent.user_id == "agent@bharatagri.demo").first()
        if not agent:
            agent = db.query(Agent).first()

    if not agent:
        raise HTTPException(status_code=404, detail="Agent profile not found.")
    return agent


@router.get("/stats")
def get_current_agent_stats(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    agent = resolve_agent("me", db, current_user)
    return compute_agent_stats(agent, db)


@router.get("/farmers")
def get_current_agent_farmers(
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    agent = resolve_agent("me", db, current_user)
    return fetch_agent_farmers(agent, search, page, limit, db)


@router.post("/farmers/register", status_code=201)
def register_farmer_by_agent(
    req: AgentFarmerRegister,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    agent = resolve_agent("me", db, current_user)

    if not req.name or not req.name.strip():
        raise HTTPException(status_code=400, detail="Farmer name is required.")
    if not req.mobile or not req.mobile.strip():
        raise HTTPException(status_code=400, detail="Farmer mobile is required.")

    # Generate farmer code & unique user_id
    rand_seq = random.randint(1000, 9999)
    f_code = f"FRM-2026-{rand_seq}"
    f_uid = f"farmer_{req.mobile.strip()}"

    # Check if already exists
    existing = db.query(Farmer).filter((Farmer.mobile == req.mobile.strip()) | (Farmer.farmer_code == f_code)).first()
    if existing:
        # Create assignment if not exists
        assign = db.query(AgentFarmerAssignment).filter(
            AgentFarmerAssignment.agent_id == agent.id,
            AgentFarmerAssignment.farmer_id == existing.id
        ).first()
        if not assign:
            new_assign = AgentFarmerAssignment(agent_id=agent.id, farmer_id=existing.id)
            db.add(new_assign)
            db.commit()
        return {
            "success": True,
            "message": f"Farmer {existing.name} already registered. Associated with your agency.",
            "farmer_id": existing.farmer_code,
            "id": existing.id
        }

    new_farmer = Farmer(
        farmer_code=f_code,
        user_id=f_uid,
        name=req.name.strip(),
        mobile=req.mobile.strip(),
        village=req.village.strip() if req.village else "Ponda",
        district=req.district.strip() if req.district else agent.district,
        state=req.state.strip() if req.state else agent.state,
        taluka=req.taluka.strip() if req.taluka else agent.taluka,
        land_area_hectares=req.land_area_hectares or 2.50,
        ekyc_status="VERIFIED",
        aadhaar_masked=f"XXXX-XXXX-{req.mobile.strip()[-4:]}",
        bank_name="State Bank of India",
        bank_account_no=f"10293847{random.randint(100, 999)}",
        bank_ifsc="SBIN0001234"
    )
    db.add(new_farmer)
    db.flush()

    # Create assignment
    assign = AgentFarmerAssignment(agent_id=agent.id, farmer_id=new_farmer.id)
    db.add(assign)

    # Add primary crop
    if req.primary_crop:
        c = FarmerCrop(
            farmer_id=new_farmer.id,
            crop_name=req.primary_crop.strip(),
            season="Kharif 2026-27",
            sowing_date=date.today() - timedelta(days=60),
            expected_harvest_date=date.today() + timedelta(days=20),
            estimated_quantity_quintals=req.estimated_quantity or 30.0
        )
        db.add(c)

    audit = AuditLog(
        user_id=agent.user_id,
        action="AGENT_REGISTERED_FARMER",
        entity="FARMER",
        entity_id=new_farmer.farmer_code,
        old_value=None,
        new_value=f"Agent: {agent.agent_code}, Farmer: {new_farmer.name} ({new_farmer.farmer_code})"
    )
    db.add(audit)
    db.commit()

    return {
        "success": True,
        "message": f"Farmer {new_farmer.name} registered and assigned successfully.",
        "farmer_id": new_farmer.farmer_code,
        "id": new_farmer.id
    }


@router.get("/{id_or_uid}/farmers")
def get_assigned_farmers(
    id_or_uid: str,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    agent = resolve_agent(id_or_uid, db, current_user)
    return fetch_agent_farmers(agent, search, page, limit, db)


@router.get("/{id_or_uid}/stats")
def get_agent_dashboard_stats(
    id_or_uid: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    agent = resolve_agent(id_or_uid, db, current_user)
    return compute_agent_stats(agent, db)


def compute_agent_stats(agent: Agent, db: Session):
    assigned_farmer_ids = [
        r[0] for r in db.query(AgentFarmerAssignment.farmer_id).filter(AgentFarmerAssignment.agent_id == agent.id).all()
    ]
    if not assigned_farmer_ids:
        # Fallback to farmers in agent's district
        assigned_farmer_ids = [
            r[0] for r in db.query(Farmer.id).filter(Farmer.district == agent.district).limit(50).all()
        ]

    farmers_assisted = len(assigned_farmer_ids)
    
    f_uids = [
        r[0] for r in db.query(Farmer.user_id).filter(Farmer.id.in_(assigned_farmer_ids)).all()
    ] if assigned_farmer_ids else []

    today = date.today()
    todays_bookings = 0
    pending_bookings = 0
    if f_uids:
        todays_bookings = (
            db.query(Booking)
            .join(Slot, Booking.slot_id == Slot.id)
            .filter(Booking.farmer_id.in_(f_uids), Slot.date == today)
            .count()
        )
        pending_bookings = (
            db.query(Booking)
            .filter(Booking.farmer_id.in_(f_uids), Booking.status.in_(["BOOKED", "CONFIRMED", "PENDING"]))
            .count()
        )

    upcoming_harvests = (
        db.query(FarmerCrop)
        .filter(
            FarmerCrop.farmer_id.in_(assigned_farmer_ids),
            FarmerCrop.expected_harvest_date >= today,
            FarmerCrop.expected_harvest_date <= today + timedelta(days=45)
        )
        .count()
    ) if assigned_farmer_ids else 0

    recent_farmers_list = []
    if assigned_farmer_ids:
        recent_farmers_obj = (
            db.query(Farmer)
            .filter(Farmer.id.in_(assigned_farmer_ids))
            .order_by(Farmer.id.desc())
            .limit(5)
            .all()
        )
        for rf in recent_farmers_obj:
            recent_farmers_list.append({
                "id": rf.id,
                "farmer_code": rf.farmer_code,
                "name": rf.name,
                "village": rf.village,
                "mobile": rf.mobile,
                "land_area": float(rf.land_area_hectares)
            })

    return {
        "agent_name": agent.name,
        "agent_code": agent.agent_code,
        "agency_type": agent.agency_type,
        "organization_name": agent.organization_name,
        "district": agent.district,
        "farmers_assisted": farmers_assisted,
        "todays_bookings": todays_bookings,
        "pending_requests": pending_bookings,
        "upcoming_harvests": upcoming_harvests,
        "recent_alerts": [
            f"Weather update for {agent.district}: Light showers predicted next week. Advise farmers to book harvesting slots early.",
            "Official MSP rate for Paddy benchmark confirmed at Rs 2,300/Quintal for Kharif 2026-27.",
            "Biometric e-KYC mandatory before booking appointment passes at procurement yards."
        ],
        "recent_farmers": recent_farmers_list
    }


def fetch_agent_farmers(agent: Agent, search: Optional[str], page: int, limit: int, db: Session):
    assigned_farmer_ids = [
        r[0] for r in db.query(AgentFarmerAssignment.farmer_id).filter(AgentFarmerAssignment.agent_id == agent.id).all()
    ]
    query = db.query(Farmer)
    if assigned_farmer_ids:
        query = query.filter(Farmer.id.in_(assigned_farmer_ids))
    else:
        query = query.filter(Farmer.district == agent.district)

    if search:
        s = f"%{search.strip()}%"
        query = query.filter((Farmer.name.ilike(s)) | (Farmer.farmer_code.ilike(s)) | (Farmer.mobile.ilike(s)))

    total = query.count()
    items = query.order_by(Farmer.id.desc()).offset((page - 1) * limit).limit(limit).all()

    result = []
    for f in items:
        active_b = db.query(Booking).filter(Booking.farmer_id == f.user_id).order_by(Booking.id.desc()).first()
        result.append({
            "id": f.id,
            "farmer_id": f.farmer_code,
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

    return result
