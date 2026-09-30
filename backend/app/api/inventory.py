from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from pydantic import BaseModel
from datetime import date, datetime, timedelta

from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user, require_role
from backend.app.models.inventory import Inventory, InventoryTransaction, BardanStock, BardanForecast
from backend.app.models.centre import Slot
from backend.app.models.booking import Booking
from backend.app.models.procurement import ProcurementRecord

from backend.app.models.audit import AuditLog

router = APIRouter(prefix="/api/inventory", tags=["Inventory & Bardan"])

class InventoryTransactionCreate(BaseModel):
    centre_id: str
    item_type: str
    transaction_type: str  # 'STOCK_IN', 'CONSUMED', 'DAMAGED', 'RETURNED'
    quantity: int
    reference_id: Optional[str] = None
    reference_type: Optional[str] = None
    notes: Optional[str] = None

class BardanStockUpdate(BaseModel):
    total_bags: Optional[int] = None
    bags_in_use: Optional[int] = None
    bags_damaged: Optional[int] = None
    available_bags: Optional[int] = None

@router.get("")
def list_inventory(
    centre_id: Optional[str] = Query(None),
    item_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    query = db.query(Inventory)
    if centre_id:
        query = query.filter(Inventory.centre_id == centre_id)
    if item_type:
        query = query.filter(Inventory.item_type == item_type)
    
    items = query.order_by(Inventory.centre_id.asc(), Inventory.item_name.asc()).all()
    return {
        "success": True,
        "count": len(items),
        "data": [
            {
                "id": i.id,
                "centre_id": i.centre_id,
                "item_type": i.item_type,
                "item_name": i.item_name,
                "current_stock": i.current_stock,
                "reserved_stock": i.reserved_stock,
                "unit": i.unit,
                "reorder_level": i.reorder_level,
                "last_restocked_at": i.last_restocked_at.strftime("%d-%m-%Y %H:%M") if i.last_restocked_at else None,
                "needs_reorder": i.current_stock <= i.reorder_level
            }
            for i in items
        ]
    }

@router.post("/transaction")
def record_transaction(
    payload: InventoryTransactionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("PROCUREMENT_CENTRE", "GOVERNMENT"))
):
    inv = db.query(Inventory).filter(
        Inventory.centre_id == payload.centre_id,
        Inventory.item_type == payload.item_type
    ).first()

    if not inv:
        # Create inventory record if not present
        inv = Inventory(
            centre_id=payload.centre_id,
            item_type=payload.item_type,
            item_name=payload.item_type.replace("_", " ").title(),
            current_stock=0,
            reserved_stock=0,
            unit="Pieces" if "BARDAN" in payload.item_type or "BAG" in payload.item_type else "Units",
            reorder_level=500
        )
        db.add(inv)
        db.flush()

    if payload.transaction_type == "STOCK_IN":
        inv.current_stock += payload.quantity
    elif payload.transaction_type in ("CONSUMED", "DAMAGED"):
        if inv.current_stock < payload.quantity:
            raise HTTPException(status_code=400, detail={"code": "INSUFFICIENT_STOCK", "message": f"Insufficient stock. Available: {inv.current_stock}, requested: {payload.quantity}"})
        inv.current_stock -= payload.quantity
    elif payload.transaction_type == "RETURNED":
        inv.current_stock += payload.quantity
    else:
        raise HTTPException(status_code=400, detail={"code": "INVALID_TX_TYPE", "message": f"Unknown transaction type: {payload.transaction_type}"})

    tx = InventoryTransaction(
        centre_id=payload.centre_id,
        item_type=payload.item_type,
        transaction_type=payload.transaction_type,
        quantity=payload.quantity,
        reference_id=payload.reference_id,
        reference_type=payload.reference_type,
        notes=payload.notes,
        created_by=current_user.get("user_id", "SYSTEM")
    )
    db.add(tx)

    audit = AuditLog(
        user_id=current_user.get("user_id", "SYSTEM"),
        action="INVENTORY_TX",
        entity="inventory",
        entity_id=str(inv.id),
        new_value=f"{payload.transaction_type} {payload.quantity} {inv.item_name}. New stock: {inv.current_stock}"
    )
    db.add(audit)
    db.commit()

    return {
        "success": True,
        "message": "Inventory transaction recorded successfully",
        "data": {
            "item_name": inv.item_name,
            "new_stock": inv.current_stock,
            "unit": inv.unit
        }
    }

# Bardan router mounted under /api/bardan as well
bardan_router = APIRouter(prefix="/api/bardan", tags=["Bardan Management"])

@bardan_router.get("/stock")
def get_bardan_stock(
    centre_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    query = db.query(BardanStock)
    if centre_id:
        query = query.filter(BardanStock.centre_id == centre_id)
    
    stocks = query.order_by(BardanStock.centre_id.asc()).all()
    return {
        "success": True,
        "count": len(stocks),
        "data": [
            {
                "id": s.id,
                "centre_id": s.centre_id,
                "total_bags": s.total_bags,
                "bags_in_use": s.bags_in_use,
                "bags_damaged": s.bags_damaged,
                "available_bags": s.available_bags,
                "updated_at": s.updated_at.strftime("%d-%m-%Y %H:%M") if s.updated_at else None
            }
            for s in stocks
        ]
    }

@bardan_router.put("/stock/{centre_id}")
def update_bardan_stock(
    centre_id: str,
    payload: BardanStockUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_role("PROCUREMENT_CENTRE", "GOVERNMENT"))
):
    stock = db.query(BardanStock).filter(BardanStock.centre_id == centre_id).first()
    if not stock:
        stock = BardanStock(
            centre_id=centre_id,
            total_bags=payload.total_bags or 20000,
            bags_in_use=payload.bags_in_use or 0,
            bags_damaged=payload.bags_damaged or 0,
            available_bags=payload.available_bags or (payload.total_bags or 20000)
        )
        db.add(stock)
    else:
        if payload.total_bags is not None:
            stock.total_bags = payload.total_bags
        if payload.bags_in_use is not None:
            stock.bags_in_use = payload.bags_in_use
        if payload.bags_damaged is not None:
            stock.bags_damaged = payload.bags_damaged
        if payload.available_bags is not None:
            stock.available_bags = payload.available_bags
        else:
            stock.available_bags = max(0, stock.total_bags - stock.bags_in_use - stock.bags_damaged)
    
    db.commit()
    db.refresh(stock)

    audit = AuditLog(
        user_id=current_user.get("user_id", "SYSTEM"),
        action="UPDATE_BARDAN_STOCK",
        entity="bardan_stock",
        entity_id=centre_id,
        new_value=f"Avail: {stock.available_bags}, Total: {stock.total_bags}"
    )
    db.add(audit)
    db.commit()

    return {
        "success": True,
        "message": "Bardan stock updated successfully",
        "data": {
            "centre_id": stock.centre_id,
            "total_bags": stock.total_bags,
            "available_bags": stock.available_bags,
            "bags_in_use": stock.bags_in_use
        }
    }

@bardan_router.get("/forecast")
def get_bardan_forecast(
    centre_id: Optional[str] = Query(None),
    days_ahead: int = Query(7),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Computes realistic Bardan requirement forecast from stored database data:
    - Current available bags
    - Projected consumption = upcoming bookings sum(quantity_quintals) * 2 bags/quintal (50kg per gunny bag)
    - Projected requirement = Projected consumption * 1.15 (15% safety buffer)
    - Expected shortage = max(0, Projected requirement - Current available)
    - Status: SAFE, LOW, WARNING, SHORTAGE
    """
    today = date.today()
    end_date = today + timedelta(days=days_ahead)

    # First check if we have stored forecasts for today
    query = db.query(BardanForecast)
    if centre_id:
        query = query.filter(BardanForecast.centre_id == centre_id)
    
    db_forecasts = query.order_by(BardanForecast.forecast_date.desc()).limit(25).all()
    
    if db_forecasts and not centre_id:
        return {
            "success": True,
            "data": [
                {
                    "centre_id": f.centre_id,
                    "forecast_date": f.forecast_date.strftime("%d-%m-%Y"),
                    "current_stock": f.current_stock,
                    "projected_consumption": f.projected_consumption,
                    "projected_requirement": f.projected_requirement,
                    "expected_shortage": f.expected_shortage,
                    "status": f.status
                }
                for f in db_forecasts
            ]
        }

    # Dynamic calculation if centre_id provided or no stored forecasts
    target_centres = [centre_id] if centre_id else [s.centre_id for s in db.query(BardanStock).all()]
    results = []

    for cid in target_centres:
        stock = db.query(BardanStock).filter(BardanStock.centre_id == cid).first()
        avail = stock.available_bags if stock else 15000

        # Calculate upcoming booked quantity
        booked_qty = db.query(func.coalesce(func.sum(Booking.quantity), 0)).join(
            Slot, Booking.slot_id == Slot.id
        ).filter(
            Booking.centre_id == cid,
            Slot.date >= today,
            Slot.date <= end_date,
            Booking.status.in_(["BOOKED", "CONFIRMED", "CHECKED_IN"])
        ).scalar()


        booked_qty = float(booked_qty)
        if booked_qty == 0:
            # Fallback based on recent 7 days procurement average
            recent_avg = db.query(func.coalesce(func.avg(ProcurementRecord.procured_quantity_quintals), 45.0)).filter(
                ProcurementRecord.centre_id == cid
            ).scalar()
            projected_consumption = int(float(recent_avg) * 2 * days_ahead)
        else:
            projected_consumption = int(booked_qty * 2)  # 2 bags per quintal (50kg bag)

        projected_requirement = int(projected_consumption * 1.15)
        shortage = max(0, projected_requirement - avail)

        if shortage > 0:
            status_val = "SHORTAGE"
        elif avail < projected_requirement * 1.1:
            status_val = "WARNING"
        elif avail < projected_requirement * 1.5:
            status_val = "LOW"
        else:
            status_val = "SAFE"

        results.append({
            "centre_id": cid,
            "forecast_date": today.strftime("%d-%m-%Y"),
            "current_stock": avail,
            "projected_consumption": projected_consumption,
            "projected_requirement": projected_requirement,
            "expected_shortage": shortage,
            "status": status_val
        })

    return {"success": True, "data": results}
