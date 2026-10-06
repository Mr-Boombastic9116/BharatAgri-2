"""
Seasonal and Perishable Crop Intelligence & Transport Priority Calculator.

Formula specified in prompt:
  transport_priority = demand + perishability + expected quantity + storage availability + destination demand + congestion

Perishable and high-demand crops receive higher transport priority when operationally justified.
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models.crop import CropMetadata
from backend.app.models.price import StateCropSupplyDemand
from backend.app.models.centre import ProcurementCentre
from backend.app.models.booking import Booking

def calculate_transport_priority(
    crop: str,
    quantity_quintals: float,
    origin_centre: ProcurementCentre,
    destination_centre: Optional[ProcurementCentre] = None,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    qty = float(quantity_quintals) if quantity_quintals and quantity_quintals > 0 else 100.0

    # 1. Fetch Crop Metadata
    crop_meta = None
    if db:
        crop_meta = db.query(CropMetadata).filter(CropMetadata.crop_name.ilike(f"%{crop}%")).first()
    
    if crop_meta:
        is_perishable = bool(crop_meta.is_perishable)
        shelf_life_days = int(crop_meta.shelf_life_days)
        perishability_score = float(crop_meta.perishability_score)
        urgency_level = crop_meta.urgency_level
        storage_req = crop_meta.storage_requirements
        demand_pattern = crop_meta.demand_patterns
        season = crop_meta.season
        category = crop_meta.category
    else:
        # Defaults based on standard agricultural classification
        crop_lower = crop.lower()
        if any(p in crop_lower for p in ['sugarcane', 'tomato', 'potato', 'onion', 'fruit', 'vegetable']):
            is_perishable = True
            shelf_life_days = 3 if 'sugarcane' in crop_lower else 7 if 'tomato' in crop_lower else 45
            perishability_score = 0.95 if 'sugarcane' in crop_lower else 0.90 if 'tomato' in crop_lower else 0.70
            urgency_level = 'CRITICAL'
            storage_req = 'Immediate transit or cold chain'
            demand_pattern = 'HIGH_PEAK_HARVEST'
            season = 'All-Season'
            category = 'PERISHABLE'
        else:
            is_perishable = False
            shelf_life_days = 365
            perishability_score = 0.20
            urgency_level = 'LOW'
            storage_req = 'Dry ventilated godown'
            demand_pattern = 'YEAR_ROUND_STABLE'
            season = 'Kharif'
            category = 'GRAIN'

    # 2. Demand Factor (Origin state demand vs supply)
    demand_factor = 0.50
    surplus_deficit = 0.0
    if db and origin_centre:
        sd = db.query(StateCropSupplyDemand).filter(
            StateCropSupplyDemand.state.ilike(f"%{origin_centre.state}%"),
            StateCropSupplyDemand.crop.ilike(f"%{crop}%")
        ).first()
        if sd:
            surplus_deficit = float(sd.surplus_deficit_quintals)
            exp_demand = float(sd.expected_demand_quintals)
            exp_supply = float(sd.expected_supply_quintals)
            if exp_supply > 0:
                demand_factor = min(1.0, max(0.1, exp_demand / exp_supply))

    # 3. Destination Demand Factor
    dest_demand_factor = 0.50
    if db and destination_centre:
        dest_sd = db.query(StateCropSupplyDemand).filter(
            StateCropSupplyDemand.state.ilike(f"%{destination_centre.state}%"),
            StateCropSupplyDemand.crop.ilike(f"%{crop}%")
        ).first()
        if dest_sd:
            dest_surplus = float(dest_sd.surplus_deficit_quintals)
            if dest_surplus < 0:
                # Deficit state = higher evacuation priority towards destination
                dest_demand_factor = min(1.0, 0.60 + (abs(dest_surplus) / 50000.0) * 0.40)
            else:
                dest_demand_factor = 0.40

    # 4. Storage Availability & Urgency at Origin
    storage_urgency_factor = 0.40
    if origin_centre:
        tot_storage = float(origin_centre.total_storage_capacity_quintals or 15000.0)
        cur_storage = float(origin_centre.current_storage_usage_quintals or 3000.0)
        utilization = cur_storage / max(tot_storage, 1.0)
        # The fuller the storage, the higher the urgency to transport out
        storage_urgency_factor = min(1.0, max(0.1, utilization))

    # 5. Congestion Factor at Origin
    daily_cap = float(origin_centre.max_daily_capacity_quintals or 800.0) if origin_centre else 800.0
    congestion_factor = 0.40
    if db and origin_centre:
        # Sum active upcoming bookings
        sum_b = db.query(func.coalesce(func.sum(Booking.quantity), 0)).filter(
            Booking.centre_id == origin_centre.centre_id,
            Booking.status.in_(["BOOKED", "CONFIRMED", "ARRIVED", "CHECKED_IN"])
        ).scalar() or 0
        load_ratio = float(sum_b) / max(daily_cap, 1.0)
        congestion_factor = min(1.0, max(0.1, load_ratio))

    # 6. Expected Quantity Factor (larger bulk lots need prioritized fleet booking)
    quantity_factor = min(1.0, max(0.1, qty / 500.0))

    # 7. Weighted Composite Priority Score (0 to 100)
    # Weights reflecting prompt requirements:
    # demand (20) + perishability (30) + expected quantity (10) + storage availability (15) + destination demand (15) + congestion (10)
    raw_score = (
        (perishability_score * 30.0) +
        (demand_factor * 20.0) +
        (dest_demand_factor * 15.0) +
        (storage_urgency_factor * 15.0) +
        (congestion_factor * 10.0) +
        (quantity_factor * 10.0)
    )
    priority_score = round(min(100.0, max(5.0, raw_score)), 1)

    if priority_score >= 75.0:
        priority_level = "CRITICAL"
        dispatch_window = "Immediate (< 12 Hours)"
        justification = (
            f"CRITICAL TRANSPORT PRIORITY: High perishability score ({perishability_score:.2f}) "
            f"and shelf-life of {shelf_life_days} days require immediate green-corridor evacuation."
        )
    elif priority_score >= 55.0:
        priority_level = "HIGH"
        dispatch_window = "Expedited (< 24 Hours)"
        justification = (
            f"HIGH TRANSPORT PRIORITY: Strong market demand combined with storage utilization ({round(storage_urgency_factor * 100, 1)}%) "
            f"justifies expedited transport allotment."
        )
    elif priority_score >= 35.0:
        priority_level = "MEDIUM"
        dispatch_window = "Scheduled (24-48 Hours)"
        justification = (
            f"STANDARD OPERATIONAL SCHEDULE: Crop shelf-life of {shelf_life_days} days and moderate yard pressure "
            f"permit regular batch truck dispatch."
        )
    else:
        priority_level = "LOW"
        dispatch_window = "Flexible (> 48 Hours)"
        justification = (
            f"STABLE BUFFER STOCK: Robust shelf-life ({shelf_life_days} days) with adequate storage capacity "
            f"permits delayed logistics consolidation."
        )

    return {
        "crop": crop,
        "category": category,
        "season": season,
        "is_perishable": is_perishable,
        "shelf_life_days": shelf_life_days,
        "urgency_level": urgency_level,
        "perishability_score": perishability_score,
        "storage_requirements": storage_req,
        "demand_patterns": demand_pattern,
        "quantity_quintals": qty,
        "priority_score": priority_score,
        "priority_level": priority_level,
        "dispatch_window": dispatch_window,
        "justification": justification,
        "factors": {
            "perishability_component": round(perishability_score * 30.0, 1),
            "origin_demand_component": round(demand_factor * 20.0, 1),
            "destination_demand_component": round(dest_demand_factor * 15.0, 1),
            "storage_urgency_component": round(storage_urgency_factor * 15.0, 1),
            "congestion_component": round(congestion_factor * 10.0, 1),
            "quantity_component": round(quantity_factor * 10.0, 1)
        }
    }
