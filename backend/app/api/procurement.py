import os
import uuid
import random
from datetime import datetime, date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user, get_current_user_optional
from backend.app.core.helpers import resolve_centre
from backend.app.models.booking import Booking, BookingStatusHistory
from backend.app.models.procurement import (
    CollectionRecord, QualityCheck, Weighment, ProcurementRecord, StorageLot, Payment, ProcurementEvidence
)
from backend.app.models.centre import ProcurementCentre, Slot
from backend.app.models.farmer import Farmer
from backend.app.models.user import User
from backend.app.models.audit import AuditLog
from backend.app.schemas.procurement import (
    CollectionCreate, QualityCheckCreate, WeighmentCreate, ProcureCreate, StorageLotCreate, PaymentCreate
)

router = APIRouter(prefix="/procurement", tags=["Procurement & Traceability"])


@router.post("/collection", status_code=201)
def record_collection(req: CollectionCreate, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == req.booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")

    if booking.status == "RECEIVED":
        existing_col = db.query(CollectionRecord).filter(CollectionRecord.booking_id == booking.id).first()
        if existing_col:
            return {
                "success": True,
                "message": "Collection already recorded for this booking",
                "collection_id": existing_col.collection_id,
                "booking_id": booking.id,
                "appointment_id": booking.appointment_id,
                "data": {
                    "collection_id": existing_col.collection_id,
                    "booking_id": booking.id,
                    "appointment_id": booking.appointment_id,
                    "status": "RECEIVED"
                }
            }

    if booking.status not in ["BOOKED", "CHECKED_IN", "CONFIRMED", "ARRIVED", "VERIFIED", "RECEIVED"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot record collection for booking in state '{booking.status}'. Farmer must be booked/checked-in/arrived."
        )

    col_count = db.query(CollectionRecord).count() + 1
    collection_id = f"COL-{booking.centre_id}-{col_count:05d}"
    today_dt = datetime.utcnow().date()

    collected_qty = req.collected_quantity or req.gross_weight_quintals or float(booking.quantity) or 25.0

    col = CollectionRecord(
        collection_id=collection_id,
        booking_id=booking.id,
        farmer_id=booking.farmer_id,
        centre_id=booking.centre_id,
        crop=booking.crop,
        collected_quantity=collected_qty,
        collection_date=today_dt,
        collection_method="DIRECT_CENTRE" if not req.truck_number else "TRUCK_GATE",
        truck_number=req.truck_number or "DIRECT_ARRIVAL",
        collected_by=req.collected_by or "Procurement Staff",
        status="RECEIVED"
    )
    db.add(col)

    old_st = booking.status
    booking.status = "RECEIVED"

    db.add(BookingStatusHistory(
        booking_id=booking.id,
        old_status=old_st,
        new_status="RECEIVED",
        changed_by=req.collected_by or "Procurement Staff",
        notes=f"Produce received at collection dock ({collected_qty} Quintals)"
    ))

    db.add(AuditLog(
        user_id=booking.centre_id,
        action="COLLECTION_RECORDED",
        entity="COLLECTION",
        entity_id=collection_id,
        new_value=f"Booking: {booking.appointment_id}, Qty: {collected_qty}Q"
    ))

    db.commit()
    return {
        "success": True,
        "message": "Collection recorded successfully",
        "collection_id": collection_id,
        "booking_id": booking.id,
        "appointment_id": booking.appointment_id,
        "data": {
            "collection_id": collection_id,
            "booking_id": booking.id,
            "appointment_id": booking.appointment_id,
            "status": "RECEIVED"
        }
    }

@router.post("/quality", status_code=201)
def record_quality_check(req: QualityCheckCreate, db: Session = Depends(get_db)):
    col = None
    if req.collection_id:
        col = db.query(CollectionRecord).filter(CollectionRecord.collection_id == req.collection_id).first()
    if not col and req.booking_id:
        col = db.query(CollectionRecord).filter(CollectionRecord.booking_id == req.booking_id).first()

    if not col:
        raise HTTPException(status_code=404, detail="Collection record not found.")

    booking = db.query(Booking).filter(Booking.id == col.booking_id).first()

    existing_qc = db.query(QualityCheck).filter(QualityCheck.collection_id == col.collection_id).first()
    if existing_qc:
        return {
            "success": True,
            "message": "Quality check already completed for this collection",
            "check_id": existing_qc.check_id,
            "passed": existing_qc.passed,
            "data": {"check_id": existing_qc.check_id, "passed": existing_qc.passed}
        }

    check_count = db.query(QualityCheck).count() + 1
    check_id = f"QC-{col.centre_id}-{check_count:05d}"
    inspector = req.inspector_name or "Inspector"
    grade = req.quality_grade or "Grade A"
    remarks = req.remarks or req.notes or "Standard Fair Average Quality verified"

    qc = QualityCheck(
        check_id=check_id,
        collection_id=col.collection_id,
        moisture_content_pct=req.moisture_content_pct,
        foreign_matter_pct=req.foreign_matter_pct,
        broken_grains_pct=req.broken_grains_pct or req.damaged_grains_pct or 0.0,
        quality_grade=grade,
        inspector_name=inspector,
        passed=req.passed,
        remarks=remarks
    )
    db.add(qc)

    if booking:
        old_st = booking.status
        booking.status = "QUALITY_CHECKED" if req.passed else "REJECTED"
        db.add(BookingStatusHistory(
            booking_id=booking.id,
            old_status=old_st,
            new_status=booking.status,
            changed_by=inspector,
            notes=f"Quality check Grade: {qc.quality_grade}, Moisture: {qc.moisture_content_pct}%"
        ))

    db.add(AuditLog(
        user_id=col.centre_id,
        action="QUALITY_CHECK_COMPLETED",
        entity="QUALITY_CHECK",
        entity_id=check_id,
        new_value=f"Collection: {col.collection_id}, Grade: {qc.quality_grade}, Passed: {req.passed}"
    ))

    db.commit()
    return {
        "success": True,
        "message": "Quality check recorded successfully",
        "check_id": check_id,
        "passed": req.passed,
        "data": {"check_id": check_id, "passed": req.passed}
    }

@router.post("/weighment", status_code=201)
def record_weighment(req: WeighmentCreate, db: Session = Depends(get_db)):
    col = None
    if req.collection_id:
        col = db.query(CollectionRecord).filter(CollectionRecord.collection_id == req.collection_id).first()
    elif req.quality_check_id:
        qc_rec = db.query(QualityCheck).filter(QualityCheck.check_id == req.quality_check_id).first()
        if qc_rec:
            col = db.query(CollectionRecord).filter(CollectionRecord.collection_id == qc_rec.collection_id).first()
    elif req.booking_id:
        col = db.query(CollectionRecord).filter(CollectionRecord.booking_id == req.booking_id).first()

    if not col:
        raise HTTPException(status_code=404, detail="Collection record not found.")

    qc = db.query(QualityCheck).filter(QualityCheck.collection_id == col.collection_id).first()
    if not qc or not qc.passed:
        raise HTTPException(status_code=400, detail="Weighment cannot proceed before quality check approval.")

    existing_wb = db.query(Weighment).filter(Weighment.collection_id == col.collection_id).first()
    if existing_wb:
        return {
            "success": True,
            "message": "Weighment already recorded for this collection",
            "weighment_id": existing_wb.weighment_id,
            "net_weight_quintals": float(existing_wb.net_weight_quintals),
            "data": {"weighment_id": existing_wb.weighment_id, "net_weight_quintals": float(existing_wb.net_weight_quintals)}
        }

    net_wt = round(req.gross_weight_quintals - req.tare_weight_quintals, 2)
    if net_wt <= 0:
        raise HTTPException(status_code=400, detail="Net weight must be strictly positive.")

    wb_count = db.query(Weighment).count() + 1
    weighment_id = f"WB-{col.centre_id}-{wb_count:05d}"
    operator = req.operator_name or req.scale_operator_name or "Scale Operator"

    wb = Weighment(
        weighment_id=weighment_id,
        collection_id=col.collection_id,
        gross_weight_quintals=req.gross_weight_quintals,
        tare_weight_quintals=req.tare_weight_quintals,
        net_weight_quintals=net_wt,
        weighbridge_id=req.weighbridge_id or "WB-01",
        operator_name=operator
    )
    db.add(wb)

    booking = db.query(Booking).filter(Booking.id == col.booking_id).first()
    if booking:
        old_st = booking.status
        booking.status = "WEIGHED"
        db.add(BookingStatusHistory(
            booking_id=booking.id,
            old_status=old_st,
            new_status="WEIGHED",
            changed_by=operator,
            notes=f"Net weighment recorded: {net_wt} Quintals"
        ))

    db.add(AuditLog(
        user_id=col.centre_id,
        action="WEIGHMENT_RECORDED",
        entity="WEIGHMENT",
        entity_id=weighment_id,
        new_value=f"Net Weight: {net_wt}Q, Gross: {req.gross_weight_quintals}Q"
    ))

    db.commit()
    return {
        "success": True,
        "message": "Weighment recorded successfully",
        "weighment_id": weighment_id,
        "net_weight_quintals": net_wt,
        "data": {"weighment_id": weighment_id, "net_weight_quintals": net_wt}
    }

@router.post("/procure", status_code=201)
def record_procurement(req: ProcureCreate, db: Session = Depends(get_db)):
    booking = None
    col = None
    wb = None

    if req.weighment_id:
        wb = db.query(Weighment).filter(Weighment.weighment_id == req.weighment_id).first()
        if not wb:
            raise HTTPException(status_code=404, detail="Weighment record not found.")
        col = db.query(CollectionRecord).filter(CollectionRecord.collection_id == wb.collection_id).first()
        if col:
            booking = db.query(Booking).filter(Booking.id == col.booking_id).first()
    else:
        if req.booking_id:
            booking = db.query(Booking).filter(Booking.id == req.booking_id).first()
        if req.collection_id:
            col = db.query(CollectionRecord).filter(CollectionRecord.collection_id == req.collection_id).first()
        if not col and booking:
            col = db.query(CollectionRecord).filter(CollectionRecord.booking_id == booking.id).first()
        if col and not booking:
            booking = db.query(Booking).filter(Booking.id == col.booking_id).first()
        if col and not wb:
            wb = db.query(Weighment).filter(Weighment.collection_id == col.collection_id).first()

    if not booking or not col or not wb:
        raise HTTPException(status_code=400, detail="Cannot procure without matching booking, collection, and weighment.")

    proc_count = db.query(ProcurementRecord).count() + 1
    procurement_id = f"PRC-{booking.centre_id}-{proc_count:05d}"
    procured_qty = req.procured_quantity_quintals or float(wb.net_weight_quintals)
    rate = req.msp_rate_per_quintal or req.rate_per_quintal_inr or 2300.0
    tot_val = round(procured_qty * rate, 2)

    qc = db.query(QualityCheck).filter(QualityCheck.collection_id == col.collection_id).first() if col else None
    grade = (qc.quality_grade if qc else "GRADE_A")
    moisture = (float(qc.moisture_content_pct) if qc else 12.50)

    proc = ProcurementRecord(
        procurement_id=procurement_id,
        booking_id=booking.id,
        collection_id=col.collection_id,
        farmer_id=booking.farmer_id,
        centre_id=booking.centre_id,
        crop=booking.crop,
        quality_grade=grade,
        moisture_content_pct=moisture,
        procured_quantity_quintals=procured_qty,
        msp_rate_per_quintal=rate,
        total_procurement_value=tot_val,
        status="CONFIRMED"
    )
    db.add(proc)
    db.flush()

    # Automatically generate Storage Lot and Lot ID (LOT-2026-STATE-CENTRE-000123)
    centre = db.query(ProcurementCentre).filter(ProcurementCentre.centre_id == booking.centre_id).first()
    st_code = centre.state[:2].upper() if centre and centre.state else "IN"
    lot_id = f"LOT-2026-{st_code}-{booking.centre_id}-{proc_count:06d}"

    storage = StorageLot(
        lot_id=lot_id,
        procurement_id=procurement_id,
        centre_id=booking.centre_id,
        crop=booking.crop,
        quantity_quintals=procured_qty,
        warehouse_name=f"{centre.centre_name if centre else 'Central'} Warehouse Stack-A",
        stack_number=f"Stack-{random.randint(1, 15)}",
        storage_date=datetime.utcnow().date(),
        status="STORED"
    )
    db.add(storage)

    # Automatically initialize Payment in INITIATED state
    pay_count = db.query(Payment).count() + 1
    payment_id = f"PAY-{booking.centre_id}-{pay_count:05d}"
    pay = Payment(
        payment_id=payment_id,
        procurement_id=procurement_id,
        farmer_id=booking.farmer_id,
        amount=tot_val,
        msp_rate=rate,
        quantity_quintals=procured_qty,
        payment_mode="DBT_NEFT",
        payment_status="INITIATED",
        remarks="Direct Benefit Transfer pending bank confirmation"
    )
    db.add(pay)

    old_st = booking.status
    booking.status = "PAYMENT_INITIATED"

    db.add(BookingStatusHistory(
        booking_id=booking.id,
        old_status=old_st,
        new_status="PAYMENT_INITIATED",
        changed_by=req.procurement_officer or "PROCUREMENT_MANAGER",
        notes=f"Procured {procured_qty}Q at MSP {rate}. Stored at {lot_id}. Payment initiated Rs {tot_val}"
    ))

    db.add(AuditLog(
        user_id=booking.centre_id,
        action="PROCUREMENT_COMPLETED",
        entity="PROCUREMENT",
        entity_id=procurement_id,
        new_value=f"Lot: {lot_id}, Amount: Rs {tot_val}"
    ))

    db.commit()

    return {
        "success": True,
        "message": "Procurement completed successfully",
        "procurement_id": proc.id,
        "procurement_code": procurement_id,
        "lot_id": lot_id,
        "payment_id": payment_id,
        "total_value": tot_val,
        "data": {
            "procurement_id": proc.id,
            "procurement_code": procurement_id,
            "lot_id": lot_id,
            "payment_id": payment_id,
            "total_value": tot_val
        }
    }

@router.post("/payment/{payment_id}/complete")
def complete_payment(payment_id: str, body: Optional[dict] = None, db: Session = Depends(get_db)):
    pay = None
    if payment_id.isdigit():
        pay = db.query(Payment).filter(Payment.id == int(payment_id)).first()
    if not pay:
        pay = db.query(Payment).filter(Payment.payment_id == payment_id).first()

    if not pay:
        raise HTTPException(status_code=404, detail="Payment record not found.")

    ref = (body and (body.get("bank_ref_number") or body.get("transaction_ref"))) or f"UTR2026{random.randint(100000000, 999999999)}"
    pay.payment_status = "PAID"
    pay.paid_at = datetime.utcnow()
    pay.transaction_ref = ref

    # Update booking status to PAID
    proc = db.query(ProcurementRecord).filter(ProcurementRecord.procurement_id == pay.procurement_id).first()
    if proc:
        booking = db.query(Booking).filter(Booking.id == proc.booking_id).first()
        if booking:
            old_st = booking.status
            booking.status = "PAID"
            db.add(BookingStatusHistory(
                booking_id=booking.id,
                old_status=old_st,
                new_status="PAID",
                changed_by="FINANCE_GATEWAY",
                notes=f"DBT payment confirmed. Ref: {pay.transaction_ref}"
            ))

    db.add(AuditLog(
        user_id="FINANCE_SYSTEM",
        action="PAYMENT_CONFIRMED",
        entity="PAYMENT",
        entity_id=pay.payment_id,
        new_value=f"Ref: {pay.transaction_ref}, Amount: Rs {pay.amount}"
    ))

    db.commit()
    return {
        "success": True,
        "message": "Payment confirmed successfully via DBT",
        "payment_id": pay.payment_id,
        "transaction_ref": pay.transaction_ref,
        "status": "PAID",
        "data": {
            "id": pay.id,
            "payment_id": pay.payment_id,
            "payment_status": "PAID",
            "transaction_ref": pay.transaction_ref
        }
    }

@router.get("/traceability/{lot_or_booking_id}")
def get_traceability_lot(lot_or_booking_id: str, db: Session = Depends(get_db)):
    lot = None
    # 1. Try by lot_id
    lot = db.query(StorageLot).filter(StorageLot.lot_id == lot_or_booking_id).first()
    # 2. Try by procurement_id string
    if not lot:
        lot = db.query(StorageLot).filter(StorageLot.procurement_id == lot_or_booking_id).first()
    # 3. If integer or digit, try by ProcurementRecord.id or Booking.id
    if not lot and lot_or_booking_id.isdigit():
        p_id = int(lot_or_booking_id)
        proc = db.query(ProcurementRecord).filter(ProcurementRecord.id == p_id).first()
        if proc:
            lot = db.query(StorageLot).filter(StorageLot.procurement_id == proc.procurement_id).first()
        if not lot:
            b = db.query(Booking).filter(Booking.id == p_id).first()
            if b:
                proc = db.query(ProcurementRecord).filter(ProcurementRecord.booking_id == b.id).first()
                if proc:
                    lot = db.query(StorageLot).filter(StorageLot.procurement_id == proc.procurement_id).first()
    # 4. Try by appointment_id
    if not lot:
        proc = db.query(ProcurementRecord).filter(
            ProcurementRecord.booking_id.in_(
                db.query(Booking.id).filter(Booking.appointment_id == lot_or_booking_id)
            )
        ).first()
        if proc:
            lot = db.query(StorageLot).filter(StorageLot.procurement_id == proc.procurement_id).first()

    if not lot:
        raise HTTPException(status_code=404, detail="Traceability lot not found.")

    proc = db.query(ProcurementRecord).filter(ProcurementRecord.procurement_id == lot.procurement_id).first()
    col = db.query(CollectionRecord).filter(CollectionRecord.collection_id == proc.collection_id).first() if proc else None
    booking = db.query(Booking).filter(Booking.id == proc.booking_id).first() if proc else None
    qc = db.query(QualityCheck).filter(QualityCheck.collection_id == col.collection_id).first() if col else None
    wb = db.query(Weighment).filter(Weighment.collection_id == col.collection_id).first() if col else None
    pay = db.query(Payment).filter(Payment.procurement_id == proc.procurement_id).first() if proc else None
    centre = db.query(ProcurementCentre).filter(ProcurementCentre.centre_id == lot.centre_id).first()
    farmer = db.query(Farmer).filter(Farmer.user_id == proc.farmer_id).first() if proc else None

    result = {
        "lot_id": lot.lot_id,
        "status": lot.status,
        "crop": lot.crop,
        "quantity_quintals": float(lot.quantity_quintals),
        "warehouse_name": lot.warehouse_name,
        "stack_number": lot.stack_number,
        "storage_date": str(lot.storage_date),
        "farmer": {
            "farmer_code": farmer.farmer_code if farmer else "N/A",
            "name": farmer.name if farmer else (proc.farmer_id if proc else "N/A"),
            "mobile": farmer.mobile if farmer else "N/A",
            "village": farmer.village if farmer else "N/A",
            "district": farmer.district if farmer else "N/A",
            "land_area": float(farmer.land_area_hectares) if farmer else 2.5
        },
        "booking": {
            "appointment_id": booking.appointment_id if booking else "N/A",
            "booking_date": str(booking.slot.date) if booking and booking.slot else "N/A",
            "status": booking.status if booking else "N/A"
        },
        "collection": {
            "collection_id": col.collection_id if col else "N/A",
            "date": str(col.collection_date) if col else "N/A",
            "truck_number": col.truck_number if col else "N/A",
            "method": col.collection_method if col else "DIRECT_CENTRE"
        },
        "quality": {
            "check_id": qc.check_id if qc else "N/A",
            "grade": qc.quality_grade if qc else "Grade A",
            "moisture_content_pct": float(qc.moisture_content_pct) if qc else 13.5,
            "foreign_matter_pct": float(qc.foreign_matter_pct) if qc else 1.2,
            "passed": qc.passed if qc else True,
            "inspector": qc.inspector_name if qc else "Inspector"
        },
        "weighment": {
            "weighment_id": wb.weighment_id if wb else "N/A",
            "gross_weight": float(wb.gross_weight_quintals) if wb else 0.0,
            "tare_weight": float(wb.tare_weight_quintals) if wb else 0.0,
            "net_weight": float(wb.net_weight_quintals) if wb else float(lot.quantity_quintals)
        },
        "procurement": {
            "procurement_id": proc.procurement_id if proc else "N/A",
            "msp_rate": float(proc.msp_rate_per_quintal) if proc else 2300.0,
            "total_value": float(proc.total_procurement_value) if proc else 0.0,
            "centre_name": centre.centre_name if centre else lot.centre_id
        },
        "payment": {
            "id": pay.id if pay else 1,
            "payment_id": pay.payment_id if pay else "N/A",
            "status": pay.payment_status if pay else "PENDING",
            "payment_status": pay.payment_status if pay else "PENDING",
            "amount": float(pay.amount) if pay else 0.0,
            "transaction_ref": pay.transaction_ref if pay else None,
            "paid_at": str(pay.paid_at) if pay and pay.paid_at else None
        }
    }
    return {
        "success": True,
        "data": result,
        **result
    }

@router.get("/lots")
def list_procurement_lots(
    centre_id: Optional[str] = None,
    crop: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(StorageLot)
    if centre_id:
        query = query.filter(StorageLot.centre_id == centre_id)
    if crop:
        query = query.filter(StorageLot.crop == crop)

    total = query.count()
    items = query.order_by(StorageLot.id.desc()).offset((page - 1) * limit).limit(limit).all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "lots": [
            {
                "id": lot.id,
                "lot_id": lot.lot_id,
                "procurement_id": lot.procurement_id,
                "centre_id": lot.centre_id,
                "crop": lot.crop,
                "quantity_quintals": float(lot.quantity_quintals),
                "warehouse_name": lot.warehouse_name,
                "stack_number": lot.stack_number,
                "storage_date": str(lot.storage_date),
                "status": lot.status
            }
            for lot in items
        ]
    }


ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/pjpeg", "image/png", "image/webp", "image/jpg"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


@router.post("/evidence/upload")
async def upload_procurement_evidence(
    file: UploadFile = File(...),
    booking_id: int = Form(...),
    evidence_type: str = Form(...),
    notes: Optional[str] = Form(None),
    procurement_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    ev_type = evidence_type.upper().strip()
    if ev_type not in ["QUALITY", "WEIGHING", "MOISTURE"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid evidence type '{evidence_type}'. Must be QUALITY, WEIGHING, or MOISTURE."
        )

    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail=f"Booking with ID {booking_id} not found.")

    # Authorization check: Centre staff can only upload for their assigned centre
    if getattr(current_user, 'role', '').lower() in ['centre', 'procurement_centre']:
        user_centre = resolve_centre(getattr(current_user, 'centre_id', None) or current_user.user_id, db)
        if user_centre and user_centre.centre_id != booking.centre_id:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied: You are assigned to '{user_centre.centre_id}', but booking belongs to '{booking.centre_id}'."
            )

    # Validate filename extension and MIME type
    orig_name = file.filename or "evidence.jpg"
    ext = os.path.splitext(orig_name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    content_type = (file.content_type or "").lower()
    if content_type and content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid MIME type '{content_type}'. Must be JPEG, PNG, or WEBP."
        )

    # Read and validate size
    file_bytes = await file.read()
    file_size = len(file_bytes)
    if file_size == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds maximum allowed limit of 5MB.")

    # Safe unique filename preventing collision and traversal
    safe_filename = f"{ev_type.lower()}_{booking.id}_{uuid.uuid4().hex[:12]}{ext}"
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "evidence"))
    os.makedirs(base_dir, exist_ok=True)
    destination = os.path.join(base_dir, safe_filename)

    with open(destination, "wb") as f:
        f.write(file_bytes)

    web_path = f"/uploads/evidence/{safe_filename}"

    evidence = ProcurementEvidence(
        booking_id=booking.id,
        procurement_id=procurement_id,
        evidence_type=ev_type,
        file_path=web_path,
        original_filename=orig_name,
        file_size_bytes=file_size,
        mime_type=content_type or f"image/{ext.replace('.', '')}",
        notes=notes,
        uploaded_by=current_user.name or current_user.user_id,
        uploaded_at=datetime.utcnow()
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)

    return {
        "success": True,
        "message": f"{ev_type} photo evidence saved successfully.",
        "evidence": {
            "id": evidence.id,
            "booking_id": evidence.booking_id,
            "procurement_id": evidence.procurement_id,
            "evidence_type": evidence.evidence_type,
            "file_path": evidence.file_path,
            "original_filename": evidence.original_filename,
            "file_size_bytes": evidence.file_size_bytes,
            "mime_type": evidence.mime_type,
            "notes": evidence.notes,
            "uploaded_by": evidence.uploaded_by,
            "uploaded_at": str(evidence.uploaded_at)
        }
    }


@router.get("/evidence/{booking_id}")
def get_procurement_evidence(
    booking_id: int,
    db: Session = Depends(get_db)
):
    evidence_items = (
        db.query(ProcurementEvidence)
        .filter(ProcurementEvidence.booking_id == booking_id)
        .order_by(ProcurementEvidence.id.asc())
        .all()
    )

    by_type = {"QUALITY": [], "WEIGHING": [], "MOISTURE": []}
    all_list = []
    for ev in evidence_items:
        item = {
            "id": ev.id,
            "booking_id": ev.booking_id,
            "procurement_id": ev.procurement_id,
            "evidence_type": ev.evidence_type,
            "file_path": ev.file_path,
            "original_filename": ev.original_filename,
            "file_size_bytes": ev.file_size_bytes,
            "mime_type": ev.mime_type,
            "notes": ev.notes,
            "uploaded_by": ev.uploaded_by,
            "uploaded_at": str(ev.uploaded_at)
        }
        all_list.append(item)
        if ev.evidence_type in by_type:
            by_type[ev.evidence_type].append(item)

    return {
        "success": True,
        "booking_id": booking_id,
        "total": len(all_list),
        "evidence": all_list,
        "by_type": by_type
    }

