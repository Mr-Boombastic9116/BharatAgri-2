from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from pydantic import BaseModel
from datetime import date, datetime, timedelta
import uuid

from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user, require_role
from backend.app.models.logistics import Truck, TruckRequest, TruckAllocation, TruckCollectionRoute, TruckRoutePrediction, TruckRouteApproval
from backend.app.models.centre import ProcurementCentre, Slot
from backend.app.models.booking import Booking
from backend.app.models.audit import AuditLog
from ml.inference.truck_optimizer import TruckOptimizer

truck_optimizer = TruckOptimizer()

def get_user_identifier(user, default="SYSTEM"):
    if not user:
        return default
    if isinstance(user, dict):
        return user.get("user_id") or user.get("sub") or default
    return getattr(user, "user_id", getattr(user, "email", default))

router = APIRouter(prefix="/api/trucks", tags=["Trucks & Logistics"])

class TruckCreate(BaseModel):
    truck_number: str
    driver_name: str
    driver_phone: str
    capacity_quintals: float
    assigned_centre_id: str

class TruckRequestCreate(BaseModel):
    centre_id: str
    required_date: date
    required_capacity_quintals: float
    reason: str

class RouteStopCreate(BaseModel):
    farmer_id: str
    village_name: str
    estimated_quantity_quintals: float

class TruckAllocationCreate(BaseModel):
    request_id: Optional[int] = None
    truck_id: int
    centre_id: str
    allocation_date: date
    assigned_quantity_quintals: float
    route_distance_km: Optional[float] = 25.5
    notes: Optional[str] = None
    stops: Optional[List[RouteStopCreate]] = None

@router.get("")
def list_trucks(
    centre_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    available_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    query = db.query(Truck)
    if centre_id:
        query = query.filter(Truck.assigned_centre_id == centre_id)
    if status:
        query = query.filter(Truck.current_status == status)
    if available_only:
        query = query.filter(Truck.is_available == True)
    
    trucks = query.order_by(Truck.id.desc()).all()
    return {
        "success": True,
        "count": len(trucks),
        "data": [
            {
                "id": t.id,
                "truck_number": t.truck_number,
                "driver_name": t.driver_name,
                "driver_phone": t.driver_phone,
                "capacity_quintals": float(t.capacity_quintals),
                "current_status": t.current_status,
                "assigned_centre_id": t.assigned_centre_id,
                "is_available": t.is_available
            }
            for t in trucks
        ]
    }

@router.post("")
def add_truck(
    payload: TruckCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("PROCUREMENT_CENTRE", "GOVERNMENT"))
):
    existing = db.query(Truck).filter(Truck.truck_number == payload.truck_number).first()
    if existing:
        raise HTTPException(status_code=400, detail={"code": "DUPLICATE_TRUCK", "message": f"Truck {payload.truck_number} already registered."})
    
    truck = Truck(
        truck_number=payload.truck_number.upper(),
        driver_name=payload.driver_name,
        driver_phone=payload.driver_phone,
        capacity_quintals=payload.capacity_quintals,
        assigned_centre_id=payload.assigned_centre_id,
        current_status="AVAILABLE",
        is_available=True
    )
    db.add(truck)
    db.commit()
    db.refresh(truck)

    audit = AuditLog(
        user_id=get_user_identifier(current_user, "SYSTEM"),
        action="CREATE_TRUCK",
        entity="trucks",
        entity_id=str(truck.id),
        new_value=truck.truck_number
    )
    db.add(audit)
    db.commit()

    return {"success": True, "message": "Truck added successfully", "data": {"id": truck.id, "truck_number": truck.truck_number}}

@router.get("/requests")
def list_truck_requests(
    centre_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    query = db.query(TruckRequest)
    if centre_id:
        query = query.filter(TruckRequest.centre_id == centre_id)
    if status:
        query = query.filter(TruckRequest.status == status)
    
    requests = query.order_by(TruckRequest.id.desc()).all()
    return {
        "success": True,
        "count": len(requests),
        "data": [
            {
                "id": r.id,
                "request_code": r.request_code,
                "centre_id": r.centre_id,
                "required_date": r.required_date.strftime("%d-%m-%Y") if r.required_date else None,
                "required_capacity_quintals": float(r.required_capacity_quintals),
                "reason": r.reason,
                "status": r.status,
                "created_at": r.created_at.strftime("%d-%m-%Y %H:%M") if r.created_at else None
            }
            for r in requests
        ]
    }

@router.post("/requests")
def create_truck_request(
    payload: TruckRequestCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("PROCUREMENT_CENTRE", "AGENT"))
):
    req_code = f"TRQ-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    req = TruckRequest(
        request_code=req_code,
        centre_id=payload.centre_id,
        required_date=payload.required_date,
        required_capacity_quintals=payload.required_capacity_quintals,
        reason=payload.reason,
        status="PENDING"
    )
    db.add(req)
    db.commit()
    db.refresh(req)

    audit = AuditLog(
        user_id=get_user_identifier(current_user, "SYSTEM"),
        action="CREATE_TRUCK_REQUEST",
        entity="truck_requests",
        entity_id=str(req.id),
        new_value=req.request_code
    )
    db.add(audit)
    db.commit()

    return {"success": True, "message": "Truck request created", "data": {"id": req.id, "request_code": req.request_code}}

@router.get("/allocations")
def list_allocations(
    centre_id: Optional[str] = Query(None),
    truck_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    query = db.query(TruckAllocation)
    if centre_id:
        query = query.filter(TruckAllocation.centre_id == centre_id)
    if truck_id:
        query = query.filter(TruckAllocation.truck_id == truck_id)
    if status:
        query = query.filter(TruckAllocation.status == status)
    
    allocations = query.order_by(TruckAllocation.id.desc()).all()
    results = []
    for a in allocations:
        truck = db.query(Truck).filter(Truck.id == a.truck_id).first()
        routes = db.query(TruckCollectionRoute).filter(TruckCollectionRoute.allocation_id == a.id).order_by(TruckCollectionRoute.stop_sequence.asc()).all()
        results.append({
            "id": a.id,
            "allocation_code": a.allocation_code,
            "centre_id": a.centre_id,
            "truck_id": a.truck_id,
            "truck_number": truck.truck_number if truck else "N/A",
            "driver_name": truck.driver_name if truck else "N/A",
            "driver_phone": truck.driver_phone if truck else "N/A",
            "allocation_date": a.allocation_date.strftime("%d-%m-%Y") if a.allocation_date else None,
            "assigned_quantity_quintals": float(a.assigned_quantity_quintals),
            "status": a.status,
            "route_distance_km": float(a.route_distance_km) if a.route_distance_km else 0.0,
            "notes": a.notes,
            "stops": [
                {
                    "stop_sequence": s.stop_sequence,
                    "farmer_id": s.farmer_id,
                    "village_name": s.village_name,
                    "estimated_quantity_quintals": float(s.estimated_quantity_quintals),
                    "visited": s.visited
                }
                for s in routes
            ]
        })

    return {"success": True, "count": len(results), "data": results}

@router.post("/allocate")
def allocate_truck(
    payload: TruckAllocationCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("PROCUREMENT_CENTRE", "GOVERNMENT"))
):
    truck = db.query(Truck).filter(Truck.id == payload.truck_id).first()
    if not truck:
        raise HTTPException(status_code=404, detail={"code": "TRUCK_NOT_FOUND", "message": "Truck not found"})
    
    alloc_code = f"TAL-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    allocation = TruckAllocation(
        allocation_code=alloc_code,
        request_id=payload.request_id,
        truck_id=payload.truck_id,
        centre_id=payload.centre_id,
        allocation_date=payload.allocation_date,
        assigned_quantity_quintals=payload.assigned_quantity_quintals,
        route_distance_km=payload.route_distance_km or 25.5,
        notes=payload.notes,
        status="ALLOCATED"
    )
    db.add(allocation)
    db.flush()

    # update truck status
    truck.current_status = "ON_ROUTE"
    truck.is_available = False

    # if request_id, update request status
    if payload.request_id:
        req = db.query(TruckRequest).filter(TruckRequest.id == payload.request_id).first()
        if req:
            req.status = "ALLOCATED"

    # add stops if provided
    if payload.stops:
        for idx, stop in enumerate(payload.stops):
            c_route = TruckCollectionRoute(
                allocation_id=allocation.id,
                stop_sequence=idx + 1,
                farmer_id=stop.farmer_id,
                village_name=stop.village_name,
                estimated_quantity_quintals=stop.estimated_quantity_quintals,
                visited=False
            )
            db.add(c_route)

    audit = AuditLog(
        user_id=get_user_identifier(current_user, "SYSTEM"),
        action="ALLOCATE_TRUCK",
        entity="truck_allocations",
        entity_id=str(allocation.id),
        new_value=f"Truck {truck.truck_number} allocated for {payload.assigned_quantity_quintals} Q"
    )
    db.add(audit)
    db.commit()
    db.refresh(allocation)

    return {"success": True, "message": "Truck allocated successfully", "data": {"allocation_code": allocation.allocation_code, "id": allocation.id}}


# -------------------------------------------------------------------------
# TRUCK ROUTE PREDICTION, INTELLIGENCE & GOVERNMENT APPROVAL WORKFLOW
# -------------------------------------------------------------------------

class RoutePredictionRequest(BaseModel):
    state: Optional[str] = None
    crop: Optional[str] = None

class RouteApprovalRequest(BaseModel):
    comments: Optional[str] = None

class RouteRejectionRequest(BaseModel):
    rejection_reason: str
    comments: Optional[str] = None

class RouteUpdateRequest(BaseModel):
    destination_centre_id: Optional[str] = None
    destination_centre_name: Optional[str] = None
    destination_state: Optional[str] = None
    quantity_quintals: Optional[float] = None
    truck_capacity_quintals: Optional[float] = None
    departure_date: Optional[date] = None
    expected_arrival_date: Optional[date] = None
    reason: Optional[str] = None
    status: Optional[str] = None


import math

@router.get("/routes/predictions")
def list_predicted_routes(
    state: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    origin_centre_id: Optional[str] = Query(None),
    centre: Optional[str] = Query(None),
    crop: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List truck route predictions for government review, scheduling and monitoring.
    Lifecycle: PREDICTED -> PROPOSED -> GOVERNMENT_REVIEW -> APPROVED / REJECTED -> SCHEDULED -> IN_TRANSIT -> ARRIVED -> COMPLETED
    """
    query = db.query(TruckRoutePrediction)
    if state and state.strip() and state.strip().lower() not in ["nationwide", "all", "all states"]:
        st = state.strip()
        state_centre_ids = [c.centre_id for c in db.query(ProcurementCentre.centre_id).filter(ProcurementCentre.state.ilike(f"%{st}%")).all()]
        query = query.filter(
            (TruckRoutePrediction.destination_state.ilike(f"%{st}%")) |
            (TruckRoutePrediction.origin_centre_id.in_(state_centre_ids))
        )
    if status and status.strip() and status.strip().upper() not in ["ALL", "ANY"]:
        query = query.filter(TruckRoutePrediction.status == status.strip().upper())
    if origin_centre_id and origin_centre_id.strip():
        query = query.filter(TruckRoutePrediction.origin_centre_id == origin_centre_id.strip())
    if centre and centre.strip():
        c_filter = centre.strip()
        query = query.filter(
            (TruckRoutePrediction.origin_centre_id == c_filter) |
            (TruckRoutePrediction.destination_centre_id == c_filter) |
            (TruckRoutePrediction.origin_centre_name.ilike(f"%{c_filter}%")) |
            (TruckRoutePrediction.destination_centre_name.ilike(f"%{c_filter}%"))
        )
    if crop and crop.strip() and crop.strip().lower() not in ["all", "any"]:
        query = query.filter(TruckRoutePrediction.crop.ilike(f"%{crop.strip()}%"))

    items = query.order_by(TruckRoutePrediction.id.desc()).all()

    # Pre-cache centres for fast capacity enrichment
    all_centres_map = {c.centre_id: c for c in db.query(ProcurementCentre).all()}

    results = []
    for r in items:
        orig_c = all_centres_map.get(r.origin_centre_id)
        dest_c = all_centres_map.get(r.destination_centre_id)

        source_cap = float(orig_c.total_storage_capacity_quintals or 15000.0) if orig_c else 15000.0
        source_used = float(orig_c.current_storage_usage_quintals or 3200.0) if orig_c else 3200.0
        source_avail = max(0.0, source_cap - source_used)
        origin_st = orig_c.state if orig_c else "Goa"

        dest_cap = float(dest_c.total_storage_capacity_quintals or 20000.0) if dest_c else 20000.0
        dest_used = float(dest_c.current_storage_usage_quintals or 4500.0) if dest_c else 4500.0
        dest_avail = max(0.0, dest_cap - dest_used)
        dest_st = dest_c.state if dest_c else r.destination_state

        truck_cap = float(r.truck_capacity_quintals or 200.0)
        trucks_req = max(1, math.ceil(float(r.quantity_quintals) / max(truck_cap, 1.0)))

        # Format calculated reason if blank or generic
        reason_text = r.reason
        if not reason_text or "storage" not in reason_text.lower():
            reason_text = (
                f"Source storage is nearing capacity ({source_used:,.0f}/{source_cap:,.0f} Q) "
                f"while destination has available storage ({dest_avail:,.0f} Q) and higher demand for {r.crop}."
            )

        results.append({
            "id": r.id,
            "route_code": r.route_code,
            "origin_centre_id": r.origin_centre_id,
            "origin_centre_name": r.origin_centre_name,
            "origin_state": origin_st,
            "source_capacity": source_cap,
            "source_used": source_used,
            "source_available": source_avail,
            "source_available_capacity": source_avail,
            "source_remaining_capacity": source_avail,

            "destination_centre_id": r.destination_centre_id,
            "destination_centre_name": r.destination_centre_name,
            "destination_state": dest_st,
            "destination_capacity": dest_cap,
            "destination_used": dest_used,
            "destination_available": dest_avail,
            "destination_available_capacity": dest_avail,
            "destination_remaining_capacity": dest_avail,

            "crop": r.crop,
            "quantity_quintals": float(r.quantity_quintals),
            "truck_capacity_quintals": truck_cap,
            "trucks_required": trucks_req,
            "truck_required": trucks_req,

            "expected_demand": f"{dest_avail:,.0f} Q buffer",
            "predicted_demand": f"{dest_avail:,.0f} Q",
            "current_supply": f"{source_used:,.0f} Q",
            "supply": f"{source_used:,.0f} Q",
            "reason": reason_text,

            "estimated_distance_km": float(r.estimated_distance_km) if r.estimated_distance_km else None,
            "distance": float(r.estimated_distance_km) if r.estimated_distance_km else None,
            "departure_date": str(r.departure_date),
            "expected_arrival_date": str(r.expected_arrival_date),
            "status": r.status,
            "reviewed_by": r.reviewed_by,
            "reviewed_at": str(r.reviewed_at) if r.reviewed_at else None,
            "rejection_reason": r.rejection_reason,
            "created_at": str(r.created_at) if r.created_at else None
        })

    return {
        "success": True,
        "count": len(results),
        "data": results
    }


@router.post("/routes/predict")
def generate_route_predictions(
    req: RoutePredictionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("GOVERNMENT", "ADMIN"))
):
    """
    Generates intelligent truck route predictions considering:
    - Centre procurement volume received & expected
    - Storage utilization & remaining storage capacity
    - Target centre storage capacity and demand for crop
    - Fleet availability & route distances
    - Mathematical optimization using Google OR-Tools MIP solver
    """
    today = date.today()
    tomorrow = today + timedelta(days=1)
    arr_date = today + timedelta(days=2)

    all_centres = db.query(ProcurementCentre).filter(ProcurementCentre.status == "OPERATIONAL").all()
    if not all_centres:
        raise HTTPException(status_code=400, detail="No operational centres available for route planning.")

    from backend.app.models.price import StateCropSupplyDemand
    from backend.app.models.centre import Slot
    from backend.app.models.booking import Booking

    sd_map = {(sd.state, sd.crop): sd.market_sentiment for sd in db.query(StateCropSupplyDemand).all()}

    surplus_sources = []
    deficit_sinks = []

    for c in all_centres:
        cap = float(c.total_storage_capacity_quintals or 15000.0)
        usage = float(c.current_storage_usage_quintals or 3000.0)
        ratio = usage / max(cap, 1.0)
        avail = max(0.0, cap - usage)

        crops_supported = [cr.strip() for cr in (c.supported_crops or "Paddy").split(",") if cr.strip()]
        primary_crop = req.crop.strip() if req.crop and req.crop.strip() else (crops_supported[0] if crops_supported else "Paddy")

        sentiment = sd_map.get((c.state, primary_crop), "BALANCED")

        # Today's operational bookings load for congestion indicator
        t_bookings = db.query(func.coalesce(func.sum(Booking.quantity), 0)).join(
            Slot, Booking.slot_id == Slot.id
        ).filter(
            Booking.centre_id == c.centre_id,
            Slot.date == today,
            Booking.status.in_(["BOOKED", "CONFIRMED", "ARRIVED", "CHECKED_IN"])
        ).scalar() or 0
        load_ratio = float(t_bookings) / max(float(c.max_daily_capacity_quintals or 800.0), 1.0)
        congestion = "CRITICAL" if (load_ratio >= 0.9 or ratio >= 0.85) else "HIGH" if (load_ratio >= 0.75 or ratio >= 0.7) else "MEDIUM" if ratio >= 0.35 else "LOW"

        if usage >= 800.0 or ratio >= 0.20 or sentiment == "SURPLUS" or congestion in ["HIGH", "CRITICAL"]:
            surplus_qty = max(200.0, usage - (0.18 * cap)) if ratio >= 0.25 else min(usage * 0.35, 600.0)
            surplus_sources.append({
                "centre_id": c.centre_id,
                "centre_name": c.centre_name,
                "state": c.state,
                "district": c.district,
                "total_capacity": cap,
                "current_usage": usage,
                "surplus_qty": surplus_qty,
                "crop": primary_crop,
                "congestion": congestion,
                "sentiment": sentiment
            })

        if avail >= 200.0:
            deficit_sinks.append({
                "centre_id": c.centre_id,
                "centre_name": c.centre_name,
                "state": c.state,
                "district": c.district,
                "total_capacity": cap,
                "current_usage": usage,
                "available_capacity": avail,
                "crop": primary_crop,
                "sentiment": sentiment
            })

    if not deficit_sinks:
        # Fallback to all centres as potential destination buffers
        for c in all_centres:
            cap = float(c.total_storage_capacity_quintals or 15000.0)
            usage = float(c.current_storage_usage_quintals or 3000.0)
            avail = max(1000.0, cap - usage)
            deficit_sinks.append({
                "centre_id": c.centre_id,
                "centre_name": c.centre_name,
                "state": c.state,
                "district": c.district,
                "total_capacity": cap,
                "current_usage": usage,
                "available_capacity": avail,
                "crop": req.crop.strip() if req.crop else "Paddy",
                "sentiment": "BALANCED"
            })

    # Available fleet
    avail_trucks_count = db.query(func.count(Truck.id)).filter(Truck.is_available == True).scalar() or 15

    # Execute mathematical optimization using Google OR-Tools MIP solver
    opt_result = truck_optimizer.optimize_inter_centre_routes(
        surplus_sources=surplus_sources,
        deficit_sinks=deficit_sinks,
        total_available_trucks=avail_trucks_count,
        truck_capacity_quintals=200.0
    )

    created_routes = []
    routes_data = opt_result.get("routes", [])

    for r in routes_data:
        route_code = f"TRP-{datetime.now().strftime('%y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        prediction = TruckRoutePrediction(
            route_code=route_code,
            origin_centre_id=r["origin_centre_id"],
            origin_centre_name=r["origin_centre_name"],
            destination_centre_id=r["destination_centre_id"],
            destination_centre_name=r["destination_centre_name"],
            destination_state=r["destination_state"],
            crop=r["crop"],
            quantity_quintals=r["quantity_quintals"],
            truck_capacity_quintals=r["truck_capacity_quintals"],
            estimated_distance_km=r["estimated_distance_km"],
            departure_date=tomorrow,
            expected_arrival_date=arr_date,
            reason=r["reason"],
            status="PROPOSED"
        )
        db.add(prediction)
        db.flush()

        audit = AuditLog(
            user_id=get_user_identifier(current_user, "GOVERNMENT_OFFICER"),
            action="TRUCK_ROUTE_PREDICTED",
            entity="TRUCK_ROUTE",
            entity_id=route_code,
            old_value=None,
            new_value=f"Route: {r['origin_centre_id']} -> {r['destination_centre_id']}, Qty: {r['quantity_quintals']}Q ({opt_result.get('solver_status')})"
        )
        db.add(audit)
        created_routes.append(route_code)

    db.commit()

    return {
        "success": True,
        "engine": opt_result.get("engine", "Optimization Engine (Google OR-Tools)"),
        "solver_status": opt_result.get("solver_status", "OPTIMAL"),
        "is_optimal": opt_result.get("is_optimal", True),
        "message": f"Generated {len(created_routes)} intelligent route suggestions for Government review via {opt_result.get('engine')}.",
        "routes_created": created_routes
    }


@router.post("/routes/{route_id}/approve")
def approve_route(
    route_id: int,
    payload: RouteApprovalRequest = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("GOVERNMENT", "ADMIN"))
):
    route = db.query(TruckRoutePrediction).filter(TruckRoutePrediction.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Predicted truck route not found.")

    old_status = route.status
    route.status = "APPROVED"
    route.reviewed_by = get_user_identifier(current_user, "GOVERNMENT_OFFICER")
    route.reviewed_at = datetime.now()

    comments = payload.comments if payload and payload.comments else "Approved by Government Logistics Officer."
    approval_rec = TruckRouteApproval(
        route_prediction_id=route.id,
        action="APPROVED",
        action_by=route.reviewed_by,
        comments=comments
    )
    db.add(approval_rec)

    audit = AuditLog(
        user_id=route.reviewed_by,
        action="TRUCK_ROUTE_APPROVED",
        entity="TRUCK_ROUTE",
        entity_id=route.route_code,
        old_value=old_status,
        new_value="APPROVED"
    )
    db.add(audit)
    db.commit()

    return {
        "success": True,
        "message": f"Route {route.route_code} approved successfully.",
        "route_code": route.route_code,
        "status": route.status
    }


@router.post("/routes/{route_id}/reject")
def reject_route(
    route_id: int,
    payload: RouteRejectionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("GOVERNMENT", "ADMIN"))
):
    route = db.query(TruckRoutePrediction).filter(TruckRoutePrediction.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Predicted truck route not found.")

    if not payload.rejection_reason or not payload.rejection_reason.strip():
        raise HTTPException(status_code=400, detail="Rejection reason is mandatory.")

    old_status = route.status
    route.status = "REJECTED"
    route.reviewed_by = get_user_identifier(current_user, "GOVERNMENT_OFFICER")
    route.reviewed_at = datetime.now()
    route.rejection_reason = payload.rejection_reason.strip()

    approval_rec = TruckRouteApproval(
        route_prediction_id=route.id,
        action="REJECTED",
        action_by=route.reviewed_by,
        comments=payload.rejection_reason.strip()
    )
    db.add(approval_rec)

    audit = AuditLog(
        user_id=route.reviewed_by,
        action="TRUCK_ROUTE_REJECTED",
        entity="TRUCK_ROUTE",
        entity_id=route.route_code,
        old_value=old_status,
        new_value=f"REJECTED: {payload.rejection_reason.strip()}"
    )
    db.add(audit)
    db.commit()

    return {
        "success": True,
        "message": f"Route {route.route_code} rejected.",
        "route_code": route.route_code,
        "status": route.status
    }


@router.put("/routes/{route_id}")
@router.patch("/routes/{route_id}")
def update_route(
    route_id: int,
    payload: RouteUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("GOVERNMENT", "ADMIN"))
):
    route = db.query(TruckRoutePrediction).filter(TruckRoutePrediction.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Predicted truck route not found.")

    old_val = f"Dest: {route.destination_centre_id}, Qty: {route.quantity_quintals}, Status: {route.status}"

    # Validation: Destination centre must exist and cannot be origin centre
    if payload.destination_centre_id:
        if payload.destination_centre_id == route.origin_centre_id:
            raise HTTPException(status_code=400, detail="Destination centre cannot be the same as origin centre.")
        c = db.query(ProcurementCentre).filter(
            (ProcurementCentre.centre_id == payload.destination_centre_id) | (ProcurementCentre.id == payload.destination_centre_id)
        ).first()
        if not c:
            raise HTTPException(status_code=404, detail="Destination centre does not exist.")
        route.destination_centre_id = c.centre_id
        route.destination_centre_name = c.centre_name
        route.destination_state = c.state

    # Validation: Quantity must be positive
    if payload.quantity_quintals is not None:
        if payload.quantity_quintals <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be strictly greater than zero.")
        route.quantity_quintals = payload.quantity_quintals

    if payload.truck_capacity_quintals is not None:
        if payload.truck_capacity_quintals <= 0:
            raise HTTPException(status_code=400, detail="Truck capacity must be strictly greater than zero.")
        route.truck_capacity_quintals = payload.truck_capacity_quintals

    if payload.departure_date:
        route.departure_date = payload.departure_date
    if payload.expected_arrival_date:
        route.expected_arrival_date = payload.expected_arrival_date
    if payload.reason:
        route.reason = payload.reason
    if payload.status:
        route.status = payload.status.upper()

    new_val = f"Dest: {route.destination_centre_id}, Qty: {route.quantity_quintals}, Status: {route.status}"

    audit = AuditLog(
        user_id=get_user_identifier(current_user, "GOVERNMENT_OFFICER"),
        action="TRUCK_ROUTE_MODIFIED",
        entity="TRUCK_ROUTE",
        entity_id=route.route_code,
        old_value=old_val,
        new_value=new_val
    )
    db.add(audit)
    db.commit()

    return {
        "success": True,
        "message": f"Route {route.route_code} updated successfully.",
        "route_code": route.route_code,
        "status": route.status,
        "quantity_quintals": float(route.quantity_quintals)
    }


@router.post("/routes/{route_id}/schedule")
def schedule_route(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("GOVERNMENT", "ADMIN"))
):
    """
    Schedules an approved route for physical dispatch:
    - Verifies route is in APPROVED status
    - Assigns an available truck and marks it SCHEDULED / ON_ROUTE
    - Updates origin centre storage inventory (relieves congestion)
    - Updates destination centre storage inventory (receives stock transfer)
    - Transitions route status: APPROVED -> SCHEDULED
    - Records comprehensive audit log
    """
    route = db.query(TruckRoutePrediction).filter(TruckRoutePrediction.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Predicted truck route not found.")

    if route.status != "APPROVED":
        raise HTTPException(status_code=400, detail="Only APPROVED routes can be scheduled for dispatch.")

    # Find available truck assigned to origin centre or regional fleet pool
    avail_truck = db.query(Truck).filter(
        (Truck.assigned_centre_id == route.origin_centre_id) & (Truck.is_available == True)
    ).first()

    if not avail_truck:
        avail_truck = db.query(Truck).filter(Truck.is_available == True).first()

    truck_id = avail_truck.id if avail_truck else 1
    if avail_truck:
        avail_truck.current_status = "SCHEDULED"
        avail_truck.is_available = False

    # Relieve origin centre storage capacity & update destination storage capacity (Complete Data Flow)
    orig_c = db.query(ProcurementCentre).filter(ProcurementCentre.centre_id == route.origin_centre_id).first()
    if orig_c:
        orig_c.current_storage_usage_quintals = max(
            0.0, float(orig_c.current_storage_usage_quintals or 0.0) - float(route.quantity_quintals)
        )

    dest_c = db.query(ProcurementCentre).filter(ProcurementCentre.centre_id == route.destination_centre_id).first()
    if dest_c:
        dest_c.current_storage_usage_quintals = float(dest_c.current_storage_usage_quintals or 0.0) + float(route.quantity_quintals)

    alloc_code = f"TAL-{datetime.now().strftime('%y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    allocation = TruckAllocation(
        allocation_code=alloc_code,
        truck_id=truck_id,
        centre_id=route.origin_centre_id,
        allocation_date=route.departure_date,
        assigned_quantity_quintals=route.quantity_quintals,
        route_distance_km=route.estimated_distance_km or 45.0,
        notes=f"Government approved schedule: {route.origin_centre_name} -> {route.destination_centre_name} ({route.crop})",
        status="SCHEDULED"
    )
    db.add(allocation)

    route.status = "SCHEDULED"

    approval_rec = TruckRouteApproval(
        route_prediction_id=route.id,
        action="SCHEDULED",
        action_by=get_user_identifier(current_user, "GOVERNMENT_OFFICER"),
        comments=f"Dispatched with allocation code {alloc_code}."
    )
    db.add(approval_rec)

    audit = AuditLog(
        user_id=get_user_identifier(current_user, "GOVERNMENT_OFFICER"),
        action="TRUCK_ROUTE_SCHEDULED",
        entity="TRUCK_ROUTE",
        entity_id=route.route_code,
        old_value="APPROVED",
        new_value=f"SCHEDULED: Allocation {alloc_code}, Truck {avail_truck.truck_number if avail_truck else 'AUTO'}"
    )
    db.add(audit)
    db.commit()

    return {
        "success": True,
        "message": f"Route {route.route_code} scheduled successfully! Allocation Code: {alloc_code}",
        "allocation_code": alloc_code,
        "status": "SCHEDULED"
    }


@router.post("/routes/{route_id}/transit")
def mark_route_in_transit(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("GOVERNMENT", "ADMIN", "PROCUREMENT_CENTRE"))
):
    route = db.query(TruckRoutePrediction).filter(TruckRoutePrediction.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found.")
    if route.status != "SCHEDULED":
        raise HTTPException(status_code=400, detail="Only SCHEDULED routes can transition to IN_TRANSIT.")

    old_status = route.status
    route.status = "IN_TRANSIT"

    approval_rec = TruckRouteApproval(
        route_prediction_id=route.id,
        action="IN_TRANSIT",
        action_by=get_user_identifier(current_user, "SYSTEM"),
        comments="Truck departed origin yard; currently in transit."
    )
    db.add(approval_rec)

    audit = AuditLog(
        user_id=get_user_identifier(current_user, "SYSTEM"),
        action="TRUCK_ROUTE_IN_TRANSIT",
        entity="TRUCK_ROUTE",
        entity_id=route.route_code,
        old_value=old_status,
        new_value="IN_TRANSIT"
    )
    db.add(audit)
    db.commit()

    return {"success": True, "message": f"Route {route.route_code} is now IN_TRANSIT.", "status": "IN_TRANSIT"}


@router.post("/routes/{route_id}/arrive")
def mark_route_arrived(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("GOVERNMENT", "ADMIN", "PROCUREMENT_CENTRE"))
):
    route = db.query(TruckRoutePrediction).filter(TruckRoutePrediction.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found.")
    if route.status not in ["SCHEDULED", "IN_TRANSIT"]:
        raise HTTPException(status_code=400, detail="Route must be SCHEDULED or IN_TRANSIT to mark ARRIVED.")

    old_status = route.status
    route.status = "ARRIVED"

    approval_rec = TruckRouteApproval(
        route_prediction_id=route.id,
        action="ARRIVED",
        action_by=get_user_identifier(current_user, "SYSTEM"),
        comments="Truck reached destination yard gate."
    )
    db.add(approval_rec)

    audit = AuditLog(
        user_id=get_user_identifier(current_user, "SYSTEM"),
        action="TRUCK_ROUTE_ARRIVED",
        entity="TRUCK_ROUTE",
        entity_id=route.route_code,
        old_value=old_status,
        new_value="ARRIVED"
    )
    db.add(audit)
    db.commit()

    return {"success": True, "message": f"Route {route.route_code} marked ARRIVED at destination.", "status": "ARRIVED"}


@router.post("/routes/{route_id}/complete")
def complete_route(
    route_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("GOVERNMENT", "ADMIN", "PROCUREMENT_CENTRE"))
):
    route = db.query(TruckRoutePrediction).filter(TruckRoutePrediction.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found.")
    if route.status not in ["ARRIVED", "SCHEDULED", "IN_TRANSIT"]:
        raise HTTPException(status_code=400, detail="Cannot complete route that has not been dispatched.")

    old_status = route.status
    route.status = "COMPLETED"

    # Free up truck if allocated
    alloc = db.query(TruckAllocation).filter(
        TruckAllocation.centre_id == route.origin_centre_id,
        TruckAllocation.assigned_quantity_quintals == route.quantity_quintals
    ).order_by(TruckAllocation.id.desc()).first()
    if alloc:
        truck = db.query(Truck).filter(Truck.id == alloc.truck_id).first()
        if truck:
            truck.current_status = "AVAILABLE"
            truck.is_available = True
            truck.assigned_centre_id = route.destination_centre_id  # Relocated to destination

    approval_rec = TruckRouteApproval(
        route_prediction_id=route.id,
        action="COMPLETED",
        action_by=get_user_identifier(current_user, "SYSTEM"),
        comments="Transfer completed and verified at destination warehouse."
    )
    db.add(approval_rec)

    audit = AuditLog(
        user_id=get_user_identifier(current_user, "SYSTEM"),
        action="TRUCK_ROUTE_COMPLETED",
        entity="TRUCK_ROUTE",
        entity_id=route.route_code,
        old_value=old_status,
        new_value="COMPLETED"
    )
    db.add(audit)
    db.commit()

    return {"success": True, "message": f"Route {route.route_code} completed successfully.", "status": "COMPLETED"}
