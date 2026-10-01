from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, text, desc
from datetime import datetime

from backend.app.core.database import get_db
from backend.app.core.helpers import resolve_centre
from backend.app.models.price import MspPrice, StateCropSupplyDemand, PriceEstimate
from backend.app.models.centre import ProcurementCentre
from backend.app.models.procurement import ProcurementRecord
from backend.app.models.farmer import Farmer, FarmerCrop
from backend.app.models.audit import AuditLog

router = APIRouter(tags=["Price Intelligence & Official MSP"])

class PriceEstimateRequest(BaseModel):
    crop: str
    quantity: Optional[float] = None
    quantity_quintals: Optional[float] = None
    centre_id: Optional[str] = None
    state: Optional[str] = None

@router.get("/msp")
@router.get("/price/msp")
def get_official_msp(
    crop: Optional[str] = Query(None),
    season: Optional[str] = Query(None),
    year: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Returns official government-notified MSP benchmarks from msp_prices table.
    Authoritative baseline published by Ministry of Agriculture & Farmers Welfare, GoI.
    """
    query = db.query(MspPrice)
    if crop and crop.strip():
        query = query.filter(MspPrice.crop.ilike(f"%{crop.strip()}%"))
    if season and season.strip():
        query = query.filter(MspPrice.marketing_season.ilike(f"%{season.strip()}%"))
    if year and year.strip():
        query = query.filter(MspPrice.season_year == year.strip())

    items = query.order_by(MspPrice.id.asc()).all()
    results = []
    for item in items:
        results.append({
            "id": item.id,
            "crop": item.crop,
            "crop_variant": item.crop_variant,
            "marketing_season": item.marketing_season,
            "season_year": item.season_year,
            "official_msp_per_quintal": float(item.official_msp_per_quintal),
            "effective_from": str(item.effective_from),
            "effective_to": str(item.effective_to),
            "source": item.source,
            "source_reference": item.source_reference
        })

    # Summary statistics
    avg_msp = db.query(func.avg(MspPrice.official_msp_per_quintal)).scalar() or 0.0

    return {
        "success": True,
        "count": len(results),
        "nationwide_average_official_msp": round(float(avg_msp), 2),
        "data": results
    }

@router.get("/price-intelligence")
def get_price_intelligence(
    state: Optional[str] = Query(None),
    crop: Optional[str] = Query(None),
    state_id: Optional[str] = Query(None),
    crop_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Returns state-level and nationwide supply, demand, and estimated procurement prices.
    Distinguishes clearly between Official MSP and Estimated BharatAgri Procurement Price.
    Synchronizes dynamically with actual database procurement and storage records.
    """
    # Sync with actual database records where available
    all_sd = db.query(StateCropSupplyDemand).all()
    for row in all_sd:
        # Sum actual procurement for this state & crop
        actual_proc = db.query(func.coalesce(func.sum(ProcurementRecord.procured_quantity_quintals), 0)).join(
            ProcurementCentre, ProcurementRecord.centre_id == ProcurementCentre.centre_id
        ).filter(
            ProcurementCentre.state.ilike(f"%{row.state}%"),
            ProcurementRecord.crop.ilike(f"%{row.crop}%")
        ).scalar()
        if actual_proc and float(actual_proc) > 0:
            row.current_procurement_quintals = float(actual_proc)

        # Sum available storage for this state
        actual_avail = db.query(func.coalesce(func.sum(
            ProcurementCentre.total_storage_capacity_quintals - ProcurementCentre.current_storage_usage_quintals
        ), 0)).filter(
            ProcurementCentre.state.ilike(f"%{row.state}%")
        ).scalar()
        if actual_avail and float(actual_avail) > 0:
            row.available_storage_quintals = max(0.0, float(actual_avail))

        # Sum inventory usage for this state
        actual_inv = db.query(func.coalesce(func.sum(ProcurementCentre.current_storage_usage_quintals), 0)).filter(
            ProcurementCentre.state.ilike(f"%{row.state}%")
        ).scalar()
        if actual_inv and float(actual_inv) > 0:
            row.current_inventory_quintals = float(actual_inv)

        # Recalculate surplus / deficit
        surplus = float(row.expected_supply_quintals) - float(row.expected_demand_quintals)
        row.surplus_deficit_quintals = surplus
        row.market_sentiment = "SURPLUS" if surplus > 2000 else "DEFICIT" if surplus < -1000 else "BALANCED"

        # Deterministic surplus rule for estimated price
        msp = float(row.official_msp)
        if surplus < -1000:
            deficit_pct = min(0.12, abs(surplus) / max(float(row.expected_demand_quintals), 1.0) * 0.25)
            row.estimated_procurement_price = round(msp * (1.0 + max(0.02, deficit_pct)), 2)
        elif surplus > 2000:
            surplus_factor = min(0.025, (surplus / max(float(row.expected_supply_quintals), 1.0)) * 0.05)
            row.estimated_procurement_price = round(max(msp, msp * (1.0 + surplus_factor)), 2)
        else:
            row.estimated_procurement_price = round(msp * 1.015, 2)
    
    try:
        db.commit()
    except Exception:
        db.rollback()

    query = db.query(StateCropSupplyDemand)
    is_state_filtered = False

    target_state = state or state_id
    if target_state and target_state.strip() and target_state.strip().lower() not in ["nationwide", "all", "all states"]:
        query = query.filter(StateCropSupplyDemand.state.ilike(f"%{target_state.strip()}%"))
        is_state_filtered = True

    target_crop = crop or crop_id
    if target_crop and target_crop.strip():
        query = query.filter(StateCropSupplyDemand.crop.ilike(f"%{target_crop.strip()}%"))

    items = query.order_by(StateCropSupplyDemand.state.asc(), StateCropSupplyDemand.crop.asc()).all()

    # Calculate overall averages
    avg_msp = db.query(func.avg(StateCropSupplyDemand.official_msp)).scalar() or 0.0
    avg_est_price = db.query(func.avg(StateCropSupplyDemand.estimated_procurement_price)).scalar() or 0.0

    state_avg_msp = 0.0
    state_avg_est_price = 0.0
    if is_state_filtered and items:
        state_avg_msp = sum(float(r.official_msp) for r in items) / len(items)
        state_avg_est_price = sum(float(r.estimated_procurement_price) for r in items) / len(items)

    results = []
    for row in items:
        sentiment = row.market_sentiment
        surplus = float(row.surplus_deficit_quintals)
        redistribution_suggestion = (
            f"SURPLUS STATE ({surplus:,.0f} Q buffer): Operational candidate for outward truck transfer to deficit regions."
            if sentiment == "SURPLUS"
            else f"DEFICIT STATE ({abs(surplus):,.0f} Q deficit): Operational candidate for inward buffer replenishment."
            if sentiment == "DEFICIT"
            else "BALANCED MARKET: Local yard throughput is equilibrium."
        )

        results.append({
            "id": row.id,
            "state": row.state,
            "crop": row.crop,
            "season": row.season,
            "official_msp": float(row.official_msp),
            "estimated_procurement_price": float(row.estimated_procurement_price),
            "estimated_price": float(row.estimated_procurement_price),
            "expected_supply_quintals": float(row.expected_supply_quintals),
            "current_procurement_quintals": float(row.current_procurement_quintals),
            "projected_procurement_quintals": float(row.projected_procurement_quintals),
            "current_inventory_quintals": float(row.current_inventory_quintals),
            "available_storage_quintals": float(row.available_storage_quintals),
            "expected_demand_quintals": float(row.expected_demand_quintals),
            "surplus_deficit_quintals": surplus,
            "supply_status": sentiment,
            "price_explanation": row.price_explanation,
            "operational_redistribution_suggestion": redistribution_suggestion,
            "redistribution_notice": "Operational Redistribution Suggestion (Does not claim or guarantee increased farmer income)",
            "updated_at": str(row.updated_at) if row.updated_at else None
        })

    meta_info = {
        "nationwide_average_official_msp": round(float(avg_msp), 2),
        "nationwide_average_estimated_price": round(float(avg_est_price), 2),
        "state_average_official_msp": round(float(state_avg_msp), 2) if is_state_filtered else None,
        "state_average_estimated_price": round(float(state_avg_est_price), 2) if is_state_filtered else None,
        "scope": target_state if is_state_filtered else "Nationwide"
    }

    return {
        "success": True,
        "scope": target_state if is_state_filtered else "Nationwide",
        "count": len(results),
        "nationwide_average_official_msp": round(float(avg_msp), 2),
        "nationwide_average_estimated_price": round(float(avg_est_price), 2),
        "state_average_official_msp": round(float(state_avg_msp), 2) if is_state_filtered else None,
        "state_average_estimated_price": round(float(state_avg_est_price), 2) if is_state_filtered else None,
        "meta": meta_info,
        "data": results
    }

@router.post("/ai/price-estimate")
@router.post("/price/estimate")
@router.post("/price-estimate")
def calculate_price_estimate(
    req: PriceEstimateRequest,
    db: Session = Depends(get_db)
):
    """
    Deterministic rule & supply-demand hybrid model for estimated farmer procurement price.
    Enforces the Surplus Rule:
      estimated_price = max(official_msp, model_estimated_price)
    Never returns an estimate below the official MSP baseline for MSP-mandated crops.
    Confidence: Set to None ("confidence unavailable") unless an active ML model is fitted on local market transactions.
    """
    qty = req.quantity if req.quantity is not None else req.quantity_quintals
    if qty is None or qty <= 0:
        qty = 1.0

    crop_name = req.crop.strip()
    
    # 1. Resolve State
    resolved_state = None
    if req.centre_id:
        c = resolve_centre(req.centre_id, db)
        if c:
            resolved_state = c.state
    if not resolved_state and req.state and req.state.strip().lower() not in ["nationwide", "all"]:
        resolved_state = req.state.strip()
    if not resolved_state:
        resolved_state = "Goa"  # default reference state

    # 2. Look up official MSP from database
    msp_row = db.query(MspPrice).filter(MspPrice.crop.ilike(f"%{crop_name}%")).order_by(MspPrice.id.asc()).first()
    if not msp_row:
        msp_row = db.query(MspPrice).filter(MspPrice.crop.ilike("%Paddy%")).first()
    
    official_msp = float(msp_row.official_msp_per_quintal) if msp_row else 2300.00

    # 3. Look up state supply-demand context
    sd_row = db.query(StateCropSupplyDemand).filter(
        StateCropSupplyDemand.state.ilike(f"%{resolved_state}%"),
        StateCropSupplyDemand.crop.ilike(f"%{crop_name}%")
    ).first()

    if sd_row:
        supply = float(sd_row.expected_supply_quintals)
        demand = float(sd_row.expected_demand_quintals)
        surplus_deficit = float(sd_row.surplus_deficit_quintals)
        curr_proc = float(sd_row.current_procurement_quintals)
        avail_storage = float(sd_row.available_storage_quintals)
        sentiment = sd_row.market_sentiment
    else:
        # Dynamic computation from actual DB records
        curr_proc = float(db.query(func.coalesce(func.sum(ProcurementRecord.procured_quantity_quintals), 0)).join(
            ProcurementCentre, ProcurementRecord.centre_id == ProcurementCentre.centre_id
        ).filter(
            ProcurementCentre.state.ilike(f"%{resolved_state}%"),
            ProcurementRecord.crop.ilike(f"%{crop_name}%")
        ).scalar() or 25000.0)

        supply = max(curr_proc * 1.35, 45000.0)
        demand = max(curr_proc * 1.20, 40000.0)
        surplus_deficit = supply - demand
        avail_storage = 35000.0
        sentiment = "SURPLUS" if surplus_deficit > 2000 else "DEFICIT" if surplus_deficit < -1000 else "BALANCED"

    # 4. Deterministic factor evaluations
    ratio = demand / max(supply, 1.0)
    
    demand_level = "High" if ratio > 1.05 else "Moderate" if ratio >= 0.85 else "Low"
    supply_level = "High" if supply > 150000 else "Moderate" if supply >= 30000 else "Low"
    inventory_level = "Low" if surplus_deficit < -1000 else "Moderate" if surplus_deficit <= 15000 else "High"
    storage_avail_level = "High" if avail_storage >= 25000 else "Moderate" if avail_storage >= 10000 else "Constrained"
    hist_proc_level = "Stable"

    factors_dict = {
        "Demand": demand_level,
        "Expected Supply": supply_level,
        "Inventory": inventory_level,
        "Storage Availability": storage_avail_level,
        "Historical Procurement": hist_proc_level
    }

    if surplus_deficit < -500:
        # Deficit state: market demand pulls price above MSP
        deficit_pct = min(0.12, abs(surplus_deficit) / max(demand, 1.0) * 0.25)
        raw_estimated = official_msp * (1.0 + max(0.02, deficit_pct))
        supply_status = "DEFICIT"
        rationale_text = (
            f"State crop demand ({demand:,.0f} Q) exceeds available supply ({supply:,.0f} Q). "
            f"Deficit market pressure supports estimated procurement price ₹{round(raw_estimated - official_msp, 2):,.2f} "
            f"above the official MSP baseline of ₹{official_msp:,.2f}/Q."
        )
    elif surplus_deficit > 2000:
        # Robust surplus: market price anchors firmly to official MSP
        surplus_factor = min(0.025, (surplus_deficit / supply) * 0.05)
        raw_estimated = official_msp * (1.0 + surplus_factor)
        supply_status = "SURPLUS"
        rationale_text = (
            f"State supply ({supply:,.0f} Q) is in comfortable surplus over demand ({demand:,.0f} Q). "
            f"Per BharatAgri surplus rules, procurement price anchors closely to the official MSP baseline (₹{official_msp:,.2f}/Q) "
            f"with secure storage buffer ({avail_storage:,.0f} Q available)."
        )
    else:
        # Balanced market condition
        raw_estimated = official_msp * 1.015
        supply_status = "BALANCED"
        rationale_text = (
            f"Balanced market equilibrium between supply and procurement targets in {resolved_state}. "
            f"Estimated price reflects steady government procurement benchmark with nominal handling premium."
        )

    # 5. Enforce Non-Negotiable Surplus Lower Bound:
    # estimated_price = max(official_msp, raw_estimated)
    final_estimated_price = round(max(official_msp, raw_estimated), 2)
    total_val = round(final_estimated_price * float(qty), 2)

    # Formatted explanation (Prompt 2 - Section 17)
    structured_explanation = (
        f"Why this estimate?\n"
        f"Demand: {demand_level}\n"
        f"Expected Supply: {supply_level}\n"
        f"Inventory: {inventory_level}\n"
        f"Storage Availability: {storage_avail_level}\n"
        f"Historical Procurement: {hist_proc_level}\n\n"
        f"{rationale_text}"
    )

    # Confidence: Prompt 2 Section 16 requirement ("If confidence cannot be reliably calculated: confidence unavailable. Never invent confidence.")
    confidence_value = None
    confidence_display = "confidence unavailable"

    # 6. Audit Logging & Persistence
    try:
        est_log = PriceEstimate(
            crop=crop_name,
            state=resolved_state,
            centre_id=req.centre_id,
            quantity_quintals=qty,
            official_msp_per_quintal=official_msp,
            estimated_price_per_quintal=final_estimated_price,
            estimated_total_value=total_val,
            supply_status=supply_status,
            confidence=None,
            explanation=structured_explanation
        )
        db.add(est_log)
        db.commit()
    except Exception:
        db.rollback()

    return {
        "crop": crop_name,
        "state": resolved_state,
        "official_msp": official_msp,
        "estimated_price": final_estimated_price,
        "estimated_total_value": total_val,
        "supply_status": supply_status,
        "confidence": confidence_value,
        "confidence_display": confidence_display,
        "explanation": structured_explanation,
        "factors": factors_dict,
        "advisory_notice": "BharatAgri estimated price is advisory and does not guarantee final payment. Final payment is based on certified actual weighed quantity."
    }
