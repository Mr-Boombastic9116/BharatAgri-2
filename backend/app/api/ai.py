from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import date, datetime
import uuid

from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user, require_role
from backend.app.models.centre import ProcurementCentre, Slot

from backend.app.models.farmer import FarmerCrop
from backend.app.models.booking import Booking
from backend.app.models.procurement import ProcurementRecord
from backend.app.models.logistics import Truck, TruckRequest, TruckAllocation
from backend.app.models.ai import SupplyForecast, CentreCongestion, AnomalyRecord, AIModelMetric
from backend.app.models.audit import AuditLog

# Import inference engines
from ml.inference.supply_predictor import SupplyPredictor
from ml.inference.congestion_engine import calculate_congestion
from ml.inference.anomaly_detector import AnomalyDetector
from ml.inference.truck_optimizer import TruckOptimizer

router = APIRouter(prefix="/api/ai", tags=["AI & Optimization Intelligence"])

# Initialize singletons
supply_predictor = SupplyPredictor()
anomaly_detector = AnomalyDetector()
truck_optimizer = TruckOptimizer()

class SupplyForecastRequest(BaseModel):
    centre_id: str
    crop: str
    month: Optional[int] = None
    year: Optional[int] = None
    registered_farmers: Optional[int] = None
    booked_quantity: Optional[float] = None
    daily_capacity: Optional[float] = None

class AnomalyStatusUpdate(BaseModel):
    status: str  # 'OPEN', 'UNDER REVIEW', 'RESOLVED', 'DISMISSED'
    notes: Optional[str] = None

class TransactionAnomalyCheck(BaseModel):
    entity_type: str = "PROCUREMENT"
    entity_id: str
    centre_id: str
    booked_quantity: float
    collected_quantity: float
    weighed_quantity: float
    procured_quantity: float
    moisture_content: Optional[float] = 13.5
    processing_time_mins: Optional[float] = 60.0

class TruckOptimizationRequest(BaseModel):
    centre_id: Optional[str] = None
    requests: Optional[List[Dict[str, Any]]] = None
    trucks: Optional[List[Dict[str, Any]]] = None

@router.post("/supply-forecast")
def get_supply_forecast(
    payload: SupplyForecastRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    centre = db.query(ProcurementCentre).filter(
        (ProcurementCentre.centre_id == payload.centre_id) | (ProcurementCentre.id == payload.centre_id)
    ).first()
    if not centre:
        raise HTTPException(status_code=404, detail={"code": "CENTRE_NOT_FOUND", "message": "Procurement centre not found"})

    now = datetime.now()
    target_month = payload.month or now.month
    target_year = payload.year or now.year

    # Gather database values if not explicitly provided
    if payload.registered_farmers is None:
        reg_farmers = db.query(func.count(FarmerCrop.id)).filter(FarmerCrop.crop_name == payload.crop).scalar() or 120
    else:
        reg_farmers = payload.registered_farmers

    if payload.daily_capacity is None:
        daily_cap = float(centre.max_daily_capacity_quintals or 800.0)
    else:
        daily_cap = payload.daily_capacity


    if payload.booked_quantity is None:
        # Sum current month bookings for this crop
        b_sum = db.query(func.coalesce(func.sum(Booking.quantity), 0)).filter(
            Booking.centre_id == centre.centre_id,
            Booking.crop == payload.crop
        ).scalar()
        booked_qty = float(b_sum) if float(b_sum) > 0 else 450.0
    else:
        booked_qty = payload.booked_quantity

    pred_res = supply_predictor.predict(
        centre_id=payload.centre_id,
        state=centre.state or "Goa",
        district=centre.district or "North Goa",
        crop=payload.crop,
        month=target_month,
        day_of_week=now.weekday(),
        registered_farmers=reg_farmers,
        booked_quantity=booked_qty,
        daily_capacity=daily_cap
    )

    # Save to supply_forecasts table for audit & caching
    try:
        forecast_rec = SupplyForecast(
            centre_id=payload.centre_id,
            crop=payload.crop,
            forecast_month=target_month,
            forecast_year=target_year,
            predicted_procurement_quantity=pred_res["predicted_procurement_quantity"],
            predicted_arrivals=pred_res["predicted_arrivals"],
            predicted_collection=pred_res["predicted_collection"],
            confidence_score=pred_res["confidence_score"],
            model_version=pred_res["model_version"]
        )
        db.add(forecast_rec)
        db.commit()
    except Exception as e:
        db.rollback()

    return {
        "success": True,
        "data": {
            "centre_id": payload.centre_id,
            "centre_name": centre.centre_name,
            "crop": payload.crop,
            "forecast_period": f"{target_month:02d}-{target_year}",
            "prediction": pred_res,
            "system_note": "Rule-based operational forecast fallback active" if pred_res.get("is_fallback") else "XGBoost Machine Learning model active"
        }
    }

@router.get("/congestion")
def get_congestion_levels(
    centre_id: Optional[str] = Query(None),
    calculation_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    target_date = calculation_date or date.today()

    target_centres = []
    if centre_id:
        c = db.query(ProcurementCentre).filter((ProcurementCentre.centre_id == centre_id) | (ProcurementCentre.id == centre_id)).first()
        if not c:
            raise HTTPException(status_code=404, detail={"code": "CENTRE_NOT_FOUND", "message": "Centre not found"})
        target_centres = [c]
    else:
        target_centres = db.query(ProcurementCentre).filter(ProcurementCentre.status != "INACTIVE").limit(25).all()

    results = []
    for c in target_centres:
        daily_cap = float(c.max_daily_capacity_quintals or 800.0)

        # Existing bookings for that date
        b_sum = db.query(func.coalesce(func.sum(Booking.quantity), 0)).join(
            Slot, Booking.slot_id == Slot.id
        ).filter(
            Booking.centre_id == c.centre_id,
            Slot.date == target_date,
            Booking.status.in_(["BOOKED", "CONFIRMED", "CHECKED_IN"])
        ).scalar()
        existing_bookings = float(b_sum)

        # Expected arrivals based on historical booking show-up rate
        predicted_arrivals = round(existing_bookings * 0.95, 2)
        expected_collection = round(existing_bookings * 0.20, 2)

        cong = calculate_congestion(
            predicted_arrivals=predicted_arrivals,
            existing_bookings_qty=existing_bookings,
            expected_collection_qty=expected_collection,
            daily_capacity=daily_cap
        )

        results.append({
            "centre_id": c.id,
            "centre_name": c.centre_name,
            "district": c.district,
            "state": c.state,
            "date": target_date.strftime("%d-%m-%Y"),
            "daily_capacity": daily_cap,
            "existing_bookings_qty": existing_bookings,
            "predicted_arrivals": predicted_arrivals,
            "expected_collection_qty": expected_collection,
            "total_estimated_load": cong["total_estimated_load"],
            "utilization_percent": cong["utilization_percent"],
            "congestion_level": cong["congestion_level"],
            "recommended_action": cong["recommended_action"],
            "threshold_guide": cong["threshold_guide"]
        })

    return {"success": True, "count": len(results), "data": results}

@router.get("/anomalies")
def list_anomalies(
    centre_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    query = db.query(AnomalyRecord)
    if centre_id:
        query = query.filter(AnomalyRecord.centre_id == centre_id)
    if status:
        query = query.filter(AnomalyRecord.status == status)
    if risk_level:
        query = query.filter(AnomalyRecord.risk_level == risk_level)

    total = query.count()
    anomalies = query.order_by(AnomalyRecord.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "success": True,
        "total": total,
        "offset": offset,
        "limit": limit,
        "classification": "Potential anomaly (Never confirmed fraud)",
        "data": [
            {
                "id": a.id,
                "anomaly_code": a.anomaly_code,
                "entity_type": a.entity_type,
                "entity_id": a.entity_id,
                "centre_id": a.centre_id,
                "anomaly_type": a.anomaly_type,
                "anomaly_score": float(a.anomaly_score),
                "risk_level": a.risk_level,
                "reason": a.reason,
                "status": a.status,
                "resolved_by": a.resolved_by,
                "resolution_notes": a.resolution_notes,
                "created_at": a.created_at.strftime("%d-%m-%Y %H:%M") if a.created_at else None
            }
            for a in anomalies
        ]
    }

@router.post("/anomalies/detect")
def detect_transaction_anomaly(
    payload: TransactionAnomalyCheck,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    eval_res = anomaly_detector.evaluate_transaction(
        booked_qty=payload.booked_quantity,
        collected_qty=payload.collected_quantity,
        weighed_qty=payload.weighed_quantity,
        procured_qty=payload.procured_quantity,
        moisture_content=payload.moisture_content or 13.5,
        processing_time_mins=payload.processing_time_mins or 60.0
    )

    if eval_res["is_anomaly"]:
        # Record into database
        code = f"ANM-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        anomaly = AnomalyRecord(
            anomaly_code=code,
            entity_type=payload.entity_type,
            entity_id=payload.entity_id,
            centre_id=payload.centre_id,
            anomaly_type="Weight / Volume Discrepancy",
            anomaly_score=eval_res["anomaly_score"],
            risk_level=eval_res["risk_level"],
            reason=eval_res["reason"],
            status="OPEN"
        )
        db.add(anomaly)
        db.commit()
        db.refresh(anomaly)
        eval_res["anomaly_code"] = anomaly.anomaly_code
        eval_res["recorded"] = True
    else:
        eval_res["recorded"] = False

    return {"success": True, "data": eval_res}

@router.put("/anomalies/{anomaly_id}/status")
def update_anomaly_status(
    anomaly_id: int,
    payload: AnomalyStatusUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("GOVERNMENT", "PROCUREMENT_CENTRE"))
):
    anomaly = db.query(AnomalyRecord).filter(AnomalyRecord.id == anomaly_id).first()
    if not anomaly:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Anomaly record not found"})

    old_status = anomaly.status
    anomaly.status = payload.status
    anomaly.resolved_by = current_user.get("user_id", "SYSTEM")
    anomaly.resolution_notes = payload.notes or f"Status updated to {payload.status}"

    audit = AuditLog(
        user_id=current_user.get("user_id", "SYSTEM"),
        action="UPDATE_ANOMALY_STATUS",
        entity="anomaly_records",
        entity_id=str(anomaly.id),
        old_value=old_status,
        new_value=f"New: {payload.status}, Notes: {payload.notes or 'None'}"
    )
    db.add(audit)
    db.commit()

    return {
        "success": True,
        "message": "Anomaly status updated",
        "data": {
            "id": anomaly.id,
            "anomaly_code": anomaly.anomaly_code,
            "status": anomaly.status,
            "resolution_notes": anomaly.resolution_notes
        }
    }

@router.post("/truck-allocation")
def optimize_truck_dispatch(
    payload: TruckOptimizationRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("PROCUREMENT_CENTRE", "GOVERNMENT"))
):
    requests_data = payload.requests
    trucks_data = payload.trucks

    # If requests or trucks omitted, retrieve pending requests and available trucks from database
    if not requests_data:
        q = db.query(TruckRequest).filter(TruckRequest.status == "PENDING")
        if payload.centre_id:
            q = q.filter(TruckRequest.centre_id == payload.centre_id)
        db_reqs = q.limit(10).all()
        requests_data = [
            {
                "request_id": r.request_code,
                "village": f"Sector-{r.id}",
                "quantity_quintals": float(r.required_capacity_quintals),
                "distance_km": 15.0 + (r.id % 20),
                "urgency": "HIGH" if (r.id % 2 == 0) else "MEDIUM"
            }
            for r in db_reqs
        ]

    if not trucks_data:
        t_query = db.query(Truck).filter(Truck.is_available == True)
        if payload.centre_id:
            t_query = t_query.filter(Truck.assigned_centre_id == payload.centre_id)
        db_trucks = t_query.limit(10).all()
        trucks_data = [
            {
                "truck_id": t.id,
                "truck_number": t.truck_number,
                "capacity_quintals": float(t.capacity_quintals),
                "driver_name": t.driver_name,
                "current_centre_id": t.assigned_centre_id
            }
            for t in db_trucks
        ]

    # Run mathematical optimization with OR-Tools
    res = truck_optimizer.optimize_allocation(
        requests=requests_data,
        available_trucks=trucks_data
    )

    audit = AuditLog(
        user_id=current_user.get("user_id", "SYSTEM"),
        action="RUN_TRUCK_OPTIMIZATION",
        entity="truck_allocations",
        entity_id=payload.centre_id or "ALL",
        new_value=f"Allocated {len(res.get('allocations', []))} trucks for {len(requests_data)} requests via {res.get('engine')}"
    )
    db.add(audit)
    db.commit()

    return res

@router.get("/model-metrics")
def get_ai_metrics(db: Session = Depends(get_db)):
    metrics = db.query(AIModelMetric).all()
    return {
        "success": True,
        "demonstration_notice": "Synthetic demonstration dataset (Seed 42) used for benchmark metrics",
        "data": [
            {
                "id": m.id,
                "model_name": m.model_name,
                "model_type": m.model_type,
                "mae": float(m.mae) if m.mae is not None else None,
                "rmse": float(m.rmse) if m.rmse is not None else None,
                "r2_score": float(m.r2_score) if m.r2_score is not None else None,
                "precision": float(m.precision_score) if m.precision_score is not None else None,
                "recall": float(m.recall_score) if m.recall_score is not None else None,
                "f1_score": float(m.f1_score) if m.f1_score is not None else None,
                "evaluation_date": m.evaluation_date.strftime("%d-%m-%Y %H:%M") if m.evaluation_date else None,
                "dataset_info": m.dataset_info
            }
            for m in metrics
        ]
    }
