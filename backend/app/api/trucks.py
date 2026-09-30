from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import date, datetime
import uuid

from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user, require_role
from backend.app.models.logistics import Truck, TruckRequest, TruckAllocation, TruckCollectionRoute
from backend.app.models.audit import AuditLog

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
        user_id=current_user.get("user_id", "SYSTEM"),
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
        user_id=current_user.get("user_id", "SYSTEM"),
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
        user_id=current_user.get("user_id", "SYSTEM"),
        action="ALLOCATE_TRUCK",
        entity="truck_allocations",
        entity_id=str(allocation.id),
        new_value=f"Truck {truck.truck_number} allocated for {payload.assigned_quantity_quintals} Q"
    )
    db.add(audit)
    db.commit()
    db.refresh(allocation)

    return {"success": True, "message": "Truck allocated successfully", "data": {"allocation_code": allocation.allocation_code, "id": allocation.id}}
