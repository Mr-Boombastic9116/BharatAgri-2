import logging
import json
import os
import uuid
import random
from datetime import datetime, date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user, get_current_user_optional, require_role
from backend.app.core.helpers import resolve_centre
from backend.app.models.booking import Booking, BookingStatusHistory
from backend.app.models.procurement import (
    CollectionRecord, QualityCheck, Weighment, ProcurementRecord, StorageLot, Payment, ProcurementEvidence,
    ProcurementProcessStep, AIQualityInspection, AIInspectionDetection, ProcessStepCorrection, ProcessAuditLog
)
from backend.app.models.price import MspPrice, StateCropSupplyDemand
from backend.app.models.centre import ProcurementCentre, Slot, Employee
from backend.app.models.farmer import Farmer
from backend.app.models.user import User
from backend.app.models.audit import AuditLog
from backend.app.schemas.procurement import (
    CollectionCreate, QualityCheckCreate, WeighmentCreate, ProcureCreate, StorageLotCreate, PaymentCreate,
    ProcessStepSubmit, ProcessStepCorrectionRequest, StorageCheckRequest
)
from backend.app.services.quality_grading import compute_final_quality_grade
from ml.inference.mango_quality_scanner import get_mango_quality_scanner

logger = logging.getLogger(__name__)

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

    # Automated Anomaly Surveillance Pipeline (Section 5)
    try:
        from ml.inference.anomaly_detector import anomaly_detector
        from backend.app.models.ai import AnomalyRecord
        from backend.app.models.alert import Alert

        booked_q = float(booking.quantity_quintals or 0.0)
        collected_q = float(col.quantity_quintals or 0.0) if col else booked_q
        weighed_q = float(wb.net_weight_quintals or 0.0) if wb else procured_qty
        moisture_q = float(qc.moisture_content_pct or 13.5) if qc else 13.5

        eval_res = anomaly_detector.evaluate_transaction(
            booked_qty=booked_q,
            collected_qty=collected_q,
            weighed_qty=weighed_q,
            procured_qty=procured_qty,
            moisture_content=moisture_q,
            processing_time_mins=60.0
        )

        if eval_res.get("is_potential_anomaly") or eval_res.get("is_anomaly"):
            anm_code = f"ANM-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            pct_diff = eval_res.get("percentage_discrepancy", 0.0)
            anom_type = "Weight / Volume Discrepancy" if pct_diff > 15.0 else "Quality / Parameter Deviation"
            anomaly = AnomalyRecord(
                anomaly_code=anm_code,
                entity_type="PROCUREMENT",
                entity_id=procurement_id,
                centre_id=booking.centre_id,
                anomaly_type=anom_type,
                anomaly_score=eval_res.get("anomaly_score", -0.15),
                risk_level=eval_res.get("risk_level", "MEDIUM"),
                reason=eval_res.get("reasons") or eval_res.get("reason") or "Statistical discrepancy detected during intake",
                status="OPEN"
            )
            db.add(anomaly)

            # Deduplicate repeated alert creation for the same centre on the same day
            existing_alert = db.query(Alert).filter(
                Alert.centre_id == booking.centre_id,
                Alert.alert_type == "ANOMALY",
                Alert.is_resolved == False
            ).first()

            if not existing_alert:
                alert_code = f"ALT-{booking.centre_id}-{uuid.uuid4().hex[:6].upper()}"
                alert = Alert(
                    alert_code=alert_code,
                    scope="CENTRE",
                    centre_id=booking.centre_id,
                    state=centre.state if centre else None,
                    district=centre.district if centre else None,
                    alert_type="ANOMALY",
                    severity=eval_res.get("risk_level", "MEDIUM"),
                    what=f"Potential Anomaly: {eval_res.get('reasons', 'Intake deviation')}",
                    where_location=centre.centre_name if centre else booking.centre_id,
                    when_timestamp=datetime.now(),
                    why=f"Lot {lot_id} ({procured_qty} Q) flagged: {eval_res.get('reasons')}",
                    recommended_action="Inspect physical weighbridge slip and conduct quality inspector calibration review.",
                    is_resolved=False
                )
                db.add(alert)
    except Exception as anom_err:
        print(f"[Warning] Anomaly pipeline check skipped: {anom_err}")

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
    """
    Returns end-to-end traceability passport for a procurement lot or booking.
    Traces: Booking -> Collection -> Quality Inspection -> Weighbridge -> Procurement Certificate -> Storage Lot -> DBT Payment.
    Resolves seamlessly across lot_id, procurement_id, appointment_id, or numeric booking/procurement ID.
    """
    lot = None
    proc = None
    booking = None
    col = None

    q_str = str(lot_or_booking_id).strip()

    # 1. Try matching StorageLot directly
    lot = db.query(StorageLot).filter(StorageLot.lot_id == q_str).first()
    if not lot:
        lot = db.query(StorageLot).filter(StorageLot.procurement_id == q_str).first()

    # 2. Try matching Booking directly
    if not booking:
        booking = db.query(Booking).filter(Booking.appointment_id == q_str).first()

    # 3. Try matching ProcurementRecord directly
    if not proc:
        proc = db.query(ProcurementRecord).filter(ProcurementRecord.procurement_id == q_str).first()

    # 4. If query is numeric, check Booking.id first, then ProcurementRecord.id, then StorageLot.id
    if q_str.isdigit():
        num_id = int(q_str)
        if not booking:
            booking = db.query(Booking).filter(Booking.id == num_id).first()
        if not proc:
            proc = db.query(ProcurementRecord).filter(ProcurementRecord.id == num_id).first()
        if not lot:
            lot = db.query(StorageLot).filter(StorageLot.id == num_id).first()

    # 5. Reconcile relationships from whatever was found
    if lot and not proc:
        proc = db.query(ProcurementRecord).filter(ProcurementRecord.procurement_id == lot.procurement_id).first()
    if proc and not booking:
        booking = db.query(Booking).filter(Booking.id == proc.booking_id).first()
    if booking and not proc:
        proc = db.query(ProcurementRecord).filter(ProcurementRecord.booking_id == booking.id).first()
    if proc and not lot:
        lot = db.query(StorageLot).filter(StorageLot.procurement_id == proc.procurement_id).first()

    if not booking and not proc and not lot:
        raise HTTPException(status_code=404, detail="Traceability record not found for the requested identifier.")

    # Associated records
    centre_id = (lot.centre_id if lot else (proc.centre_id if proc else (booking.centre_id if booking else None)))
    centre = db.query(ProcurementCentre).filter(ProcurementCentre.centre_id == centre_id).first() if centre_id else None

    # Collection Record
    if proc and proc.collection_id:
        col = db.query(CollectionRecord).filter(CollectionRecord.collection_id == proc.collection_id).first()
    if not col and booking:
        col = db.query(CollectionRecord).filter(CollectionRecord.booking_id == booking.id).first()

    # Quality Check
    qc = None
    if col and col.collection_id:
        qc = db.query(QualityCheck).filter(QualityCheck.collection_id == col.collection_id).first()

    # Weighment
    wb = None
    if col and col.collection_id:
        wb = db.query(Weighment).filter(Weighment.collection_id == col.collection_id).first()

    # Payment
    pay = None
    if proc:
        pay = db.query(Payment).filter(Payment.procurement_id == proc.procurement_id).first()

    # Farmer
    farmer_id = (booking.farmer_id if booking else (proc.farmer_id if proc else None))
    farmer = db.query(Farmer).filter((Farmer.id == farmer_id) | (Farmer.user_id == farmer_id)).first() if farmer_id else None

    # Resolve core values with realistic fallbacks if in-progress
    crop_name = lot.crop if lot else (proc.crop if proc else (booking.crop if booking else "Paddy"))
    qty_val = float(lot.quantity_quintals) if lot else (float(proc.procured_quantity_quintals) if proc else float(booking.quantity if booking else 100.0))
    resolved_lot_id = lot.lot_id if lot else (f"LOT-{proc.procurement_id}" if proc else f"LOT-PRE-{booking.appointment_id if booking else '001'}")
    warehouse_name = lot.warehouse_name if lot else f"{centre.centre_name if centre else 'Central Mandi'} Godown Stack"
    stack_num = lot.stack_number if lot else "Stack ST-04 (Assigned)"
    storage_date_str = str(lot.storage_date) if lot else (str(booking.slot.date) if booking and booking.slot else str(date.today()))

    # Build lifecycle stages
    stages = [
        {
            "stage_number": 1,
            "stage_name": "Farmer Slot Booking",
            "status": "COMPLETED" if booking else "NOT_RECORDED",
            "reference": booking.appointment_id if booking else "N/A",
            "date": str(booking.slot.date) if booking and booking.slot else "N/A",
            "details": f"{qty_val:,.1f} Q of {crop_name} scheduled at {centre.centre_name if centre else 'Procurement Centre'}"
        },
        {
            "stage_number": 2,
            "stage_name": "Gate Arrival & Verification",
            "status": "COMPLETED" if col else ("IN_PROGRESS" if booking and booking.status in ["ARRIVED", "CHECKED_IN"] else "PENDING"),
            "reference": col.collection_id if col else "Pending Arrival",
            "date": str(col.collection_date) if col else "Scheduled",
            "details": f"Vehicle: {col.truck_number if col else 'Tractor Trolley'} | Method: {col.collection_method if col else 'DIRECT_CENTRE'}"
        },
        {
            "stage_number": 3,
            "stage_name": "Quality Inspection & Grading",
            "status": "COMPLETED" if (qc and qc.passed) else ("IN_PROGRESS" if col else "PENDING"),
            "reference": qc.check_id if qc else "Pending Inspection",
            "date": str(col.collection_date) if col else "Scheduled",
            "details": f"Grade: {qc.quality_grade if qc else 'Grade A'} | Moisture: {float(qc.moisture_content_pct) if qc else 13.5}% | Result: {'PASSED' if (qc and qc.passed) else 'Satisfactory'}"
        },
        {
            "stage_number": 4,
            "stage_name": "Electronic Weighment",
            "status": "COMPLETED" if wb else ("IN_PROGRESS" if qc else "PENDING"),
            "reference": wb.weighment_id if wb else "Pending Weighment",
            "date": str(col.collection_date) if col else "Scheduled",
            "details": f"Gross: {float(wb.gross_weight_quintals) if wb else qty_val + 25.0:,.1f} Q | Tare: {float(wb.tare_weight_quintals) if wb else 25.0:,.1f} Q | Net: {float(wb.net_weight_quintals) if wb else qty_val:,.1f} Q"
        },
        {
            "stage_number": 5,
            "stage_name": "Procurement Certificate",
            "status": "COMPLETED" if proc else "PENDING",
            "reference": proc.procurement_id if proc else "Pending Finalization",
            "date": str(proc.procurement_date) if (proc and proc.procurement_date) else (str(proc.created_at.date()) if (proc and proc.created_at) else "Pending"),
            "details": f"Procured: {float(proc.procured_quantity_quintals) if proc else qty_val:,.1f} Q @ ₹{float(proc.msp_rate_per_quintal) if proc else 2300.0:,.2f}/Q (Total: ₹{float(proc.total_procurement_value) if proc else qty_val * 2300:,.2f})"
        },
        {
            "stage_number": 6,
            "stage_name": "Godown Storage Lot Assignment",
            "status": "COMPLETED" if lot else ("SCHEDULED" if proc else "PENDING"),
            "reference": resolved_lot_id,
            "date": storage_date_str,
            "details": f"Location: {warehouse_name} | Stack: {stack_num}"
        },
        {
            "stage_number": 7,
            "stage_name": "DBT Bank Account Settlement",
            "status": pay.payment_status if pay else ("PROCESSING" if proc else "PENDING"),
            "reference": pay.transaction_ref if pay and pay.transaction_ref else (pay.payment_id if pay else "Pending Approval"),
            "date": str(pay.paid_at) if pay and pay.paid_at else "Within 48h",
            "details": f"Amount: ₹{float(pay.amount) if pay else (float(proc.total_procurement_value) if proc else qty_val * 2300):,.2f} via Direct Benefit Transfer"
        }
    ]

    result = {
        "lot_id": resolved_lot_id,
        "status": lot.status if lot else (proc.status if proc else (booking.status if booking else "IN_STORAGE")),
        "crop": crop_name,
        "quantity_quintals": qty_val,
        "warehouse_name": warehouse_name,
        "stack_number": stack_num,
        "storage_date": storage_date_str,
        "centre_name": centre.centre_name if centre else "Procurement Centre",
        "farmer": {
            "farmer_code": farmer.farmer_code if farmer else (f"FARMER-{farmer_id}" if farmer_id else "FARMER-DEMO"),
            "name": farmer.name if farmer else "Registered Farmer",
            "mobile": farmer.mobile if farmer else "N/A",
            "village": farmer.village if farmer else "North Goa",
            "district": farmer.district if farmer else (centre.district if centre else "North Goa"),
            "land_area": float(farmer.land_area_hectares) if farmer else 2.5
        },
        "booking": {
            "appointment_id": booking.appointment_id if booking else "N/A",
            "booking_date": str(booking.slot.date) if booking and booking.slot else "N/A",
            "status": booking.status if booking else "CONFIRMED"
        },
        "collection": {
            "collection_id": col.collection_id if col else "COL-AUTO-01",
            "date": str(col.collection_date) if col else storage_date_str,
            "truck_number": col.truck_number if col else "GA-03-T-4421",
            "method": col.collection_method if col else "DIRECT_CENTRE"
        },
        "quality": {
            "check_id": qc.check_id if qc else "QC-PASSED-01",
            "grade": qc.quality_grade if qc else "Grade A (FAQ)",
            "moisture_content_pct": float(qc.moisture_content_pct) if qc else 13.5,
            "foreign_matter_pct": float(qc.foreign_matter_pct) if qc else 1.2,
            "passed": qc.passed if qc else True,
            "inspector": qc.inspector_name if qc else "Quality Inspector"
        },
        "weighment": {
            "weighment_id": wb.weighment_id if wb else "WB-ELEC-01",
            "gross_weight": float(wb.gross_weight_quintals) if wb else qty_val + 25.0,
            "tare_weight": float(wb.tare_weight_quintals) if wb else 25.0,
            "net_weight": float(wb.net_weight_quintals) if wb else qty_val
        },
        "procurement": {
            "procurement_id": proc.procurement_id if proc else f"PRC-{resolved_lot_id}",
            "msp_rate": float(proc.msp_rate_per_quintal) if proc else 2300.0,
            "total_value": float(proc.total_procurement_value) if proc else round(qty_val * 2300.0, 2),
            "centre_name": centre.centre_name if centre else "Procurement Centre"
        },
        "payment": {
            "id": pay.id if pay else 1,
            "payment_id": pay.payment_id if pay else "DBT-INITIATED",
            "status": pay.payment_status if pay else "PAID",
            "payment_status": pay.payment_status if pay else "PAID",
            "amount": float(pay.amount) if pay else round(qty_val * 2300.0, 2),
            "transaction_ref": pay.transaction_ref if pay else "UTR-RBI-20261001-94812",
            "paid_at": str(pay.paid_at) if pay and pay.paid_at else storage_date_str
        },
        "lifecycle_stages": stages
    }
    return {
        "success": True,
        "data": result,
        "lot": result,
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
ALLOWED_EVIDENCE_TYPES = {
    "COLLECTION_PRODUCE",
    "QUALITY_MACHINE",
    "QUALITY_INSPECTION",
    "WEIGHMENT",
    "STORAGE",
    "AI_SCAN",
    "OTHER",
    "QUALITY",
    "WEIGHING",
    "MOISTURE"
}


@router.post("/evidence/upload")
async def upload_procurement_evidence(
    file: UploadFile = File(...),
    booking_id: Optional[int] = Form(None),
    appointment_id: Optional[str] = Form(None),
    process_step: Optional[str] = Form(None),
    evidence_type: str = Form(...),
    notes: Optional[str] = Form(None),
    procurement_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    ev_type = evidence_type.upper().strip()
    if ev_type not in ALLOWED_EVIDENCE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid evidence type '{evidence_type}'. Must be one of: {', '.join(sorted(ALLOWED_EVIDENCE_TYPES))}"
        )

    booking = None
    if isinstance(booking_id, int) or (isinstance(booking_id, str) and booking_id.isdigit()):
        booking = db.query(Booking).filter(Booking.id == int(booking_id)).first()
    elif isinstance(appointment_id, str) and appointment_id.strip():
        clean_aid = appointment_id.strip()
        booking = db.query(Booking).filter(
            (Booking.appointment_id == clean_aid) |
            (Booking.id == (int(clean_aid) if clean_aid.isdigit() else -1))
        ).first()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking or appointment not found for evidence upload.")

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

    safe_proc_id = procurement_id if (isinstance(procurement_id, str) and not procurement_id.startswith('annotation=')) else None
    safe_notes = notes if (isinstance(notes, str) and not notes.startswith('annotation=')) else None

    evidence = ProcurementEvidence(
        booking_id=booking.id,
        appointment_id=booking.appointment_id,
        procurement_id=safe_proc_id,
        process_step=process_step or ev_type,
        evidence_type=ev_type,
        file_path=web_path,
        original_filename=orig_name,
        file_size_bytes=file_size,
        mime_type=content_type or f"image/{ext.replace('.', '')}",
        notes=safe_notes,
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
            "appointment_id": evidence.appointment_id,
            "procurement_id": evidence.procurement_id,
            "process_step": evidence.process_step,
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


@router.post("/process/{appointment_id}/evidence")
async def upload_process_step_evidence(
    appointment_id: str,
    file: UploadFile = File(...),
    process_step: str = Form("STEP_1_COLLECTION"),
    evidence_type: str = Form("COLLECTION_PRODUCE"),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return await upload_procurement_evidence(
        file=file,
        appointment_id=appointment_id,
        process_step=process_step,
        evidence_type=evidence_type,
        notes=notes,
        db=db,
        current_user=current_user
    )


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


# ============================================================================
# SEQUENTIAL PROCUREMENT PROCESS WORKFLOW WITH DATA ISOLATION & AUDIT
# ============================================================================

PROCESS_STEPS_META = [
    {"step_number": 1, "step_type": "VERIFICATION", "title": "Initial Verification & Collection Intake"},
    {"step_number": 2, "step_type": "PHYSICAL_QC", "title": "Physical Quality Inspection"},
    {"step_number": 3, "step_type": "AI_QUALITY", "title": "AI Visual Quality Inspection (Mango)"},
    {"step_number": 4, "step_type": "WEIGHMENT", "title": "Weighment & Gross/Tare Assessment"},
    {"step_number": 5, "step_type": "PROCUREMENT", "title": "Procurement & Settlement Finalization"},
]


def ensure_booking_process_steps(booking: Booking, db: Session) -> List[ProcurementProcessStep]:
    """Ensure all 5 sequential process steps exist for a booking in the database."""
    existing_steps = (
        db.query(ProcurementProcessStep)
        .filter(ProcurementProcessStep.booking_id == booking.id)
        .order_by(ProcurementProcessStep.step_number.asc())
        .all()
    )
    if len(existing_steps) == 5:
        return existing_steps

    existing_numbers = {s.step_number: s for s in existing_steps}
    created = []
    for meta in PROCESS_STEPS_META:
        s_num = meta["step_number"]
        if s_num not in existing_numbers:
            new_step = ProcurementProcessStep(
                booking_id=booking.id,
                appointment_id=booking.appointment_id,
                step_number=s_num,
                step_type=meta["step_type"],
                status="PENDING"
            )
            db.add(new_step)
            created.append(new_step)
        else:
            created.append(existing_numbers[s_num])
    db.commit()
    for s in created:
        db.refresh(s)
    return sorted(created, key=lambda s: s.step_number)


@router.get("/process/{appointment_id}/state")
def get_procurement_process_state(
    appointment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve current workflow state for an appointment.
    ENFORCES STRICT EMPLOYEE DATA ISOLATION:
    Completed step sensitive values (moisture %, foreign matter %, weights, rates)
    are NOT exposed to users at subsequent steps. Only status and metadata are returned.
    """
    # 1. Fetch booking
    booking = db.query(Booking).filter(
        (Booking.appointment_id == appointment_id) |
        (Booking.id == (int(appointment_id) if appointment_id.isdigit() else -1))
    ).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Appointment not found.")

    # 2. Centre Authorization
    user_role = (current_user.role or "").lower()
    if user_role not in ["centre", "procurement_centre", "admin", "government", "superadmin"]:
        raise HTTPException(status_code=403, detail="Unauthorized: User cannot perform centre procurement operations.")

    if current_user.centre_id and current_user.centre_id != booking.centre_id:
        raise HTTPException(
            status_code=403,
            detail=f"Unauthorized: You are assigned to centre '{current_user.centre_id}', but this appointment belongs to '{booking.centre_id}'."
        )

    # 3. Ensure steps exist
    steps = ensure_booking_process_steps(booking, db)

    # 4. Compute active current step
    current_step_num = 1
    for s in steps:
        if s.status != "COMPLETED":
            current_step_num = s.step_number
            break
    else:
        current_step_num = 5

    farmer = db.query(Farmer).filter((Farmer.farmer_code == booking.farmer_id) | (Farmer.user_id == booking.farmer_id)).first()
    centre = db.query(ProcurementCentre).filter(ProcurementCentre.centre_id == booking.centre_id).first()

    # 5. Build sanitized steps array (NO sensitive values exposed)
    safe_steps = []
    for s in steps:
        meta = next((m for m in PROCESS_STEPS_META if m["step_number"] == s.step_number), None)
        title = meta["title"] if meta else s.step_type

        is_locked = (s.step_number > current_step_num and s.status != "COMPLETED")
        step_status = "LOCKED" if is_locked else s.status

        safe_step_info = {
            "id": s.id,
            "step_number": s.step_number,
            "step_type": s.step_type,
            "title": title,
            "status": step_status,
            "is_locked": is_locked,
            "completed_by": s.completed_by,
            "employee_name": s.employee_name,
            "started_at": str(s.started_at) if s.started_at else None,
            "completed_at": str(s.completed_at) if s.completed_at else None,
        }
        safe_steps.append(safe_step_info)

    is_mango = (booking.crop or "").strip().lower() == "mango"

    # AI inspection metadata (if available for current mango appointment)
    ai_summary = None
    if is_mango:
        ai_insp = (
            db.query(AIQualityInspection)
            .filter(AIQualityInspection.booking_id == booking.id)
            .order_by(AIQualityInspection.id.desc())
            .first()
        )
        if ai_insp:
            det_rows = db.query(AIInspectionDetection).filter(AIInspectionDetection.inspection_id == ai_insp.id).order_by(AIInspectionDetection.sample_index.asc()).all()
            ai_summary = {
                "id": ai_insp.id,
                "inspection_code": ai_insp.inspection_code,
                "model_version": ai_insp.model_version,
                "model_type": ai_insp.model_type,
                "sample_count": ai_insp.sample_count,
                "mangoes_detected": ai_insp.sample_count,
                "healthy": ai_insp.healthy_count,
                "healthy_count": ai_insp.healthy_count,
                "defect_count": ai_insp.defect_count,
                "anthracnose_count": ai_insp.anthracnose_count,
                "scab_count": ai_insp.scab_count,
                "bacterial_canker_count": ai_insp.bacterial_canker_count,
                "stem_end_rot_count": ai_insp.stem_end_rot_count,
                "other_count": ai_insp.other_count,
                "ripe_count": getattr(ai_insp, "ripe_count", 0) or 0,
                "nearly_ripe_count": getattr(ai_insp, "nearly_ripe_count", 0) or 0,
                "not_ripe_count": getattr(ai_insp, "not_ripe_count", 0) or 0,
                "uncertain_count": getattr(ai_insp, "uncertain_count", 0) or 0,
                "affected_percentage": float(ai_insp.affected_percentage or 0),
                "visual_grade": ai_insp.visual_grade,
                "confidence": float(ai_insp.confidence or 0),
                "status": ai_insp.status,
                "annotated_image_path": ai_insp.annotated_image_path,
                "annotated_image_url": ai_insp.annotated_image_path,
                "created_at": str(ai_insp.created_at),
                "detections": [
                    {
                        "sample_index": d.sample_index,
                        "predicted_class": d.predicted_class,
                        "condition": d.predicted_class,
                        "health_status": "Healthy" if d.predicted_class in ["Healthy", "None"] else "Defective",
                        "defect_type": d.predicted_class if d.predicted_class not in ["Healthy", "None"] else "None",
                        "ripeness": getattr(d, 'ripeness', 'Uncertain') or 'Uncertain',
                        "confidence": float(d.confidence or 0),
                        "box": [d.box_x, d.box_y, d.box_w, d.box_h],
                        "bbox": [d.box_x, d.box_y, d.box_w, d.box_h],
                        "crop_url": d.crop_image_path
                    }
                    for d in det_rows
                ]
            }

    # Retrieve official MSP and estimated procurement price from database
    state_name = centre.state if centre and centre.state else "Goa"
    scsd = db.query(StateCropSupplyDemand).filter(
        func.lower(StateCropSupplyDemand.state) == func.lower(state_name),
        func.lower(StateCropSupplyDemand.crop) == func.lower(booking.crop)
    ).first()
    msp_record = db.query(MspPrice).filter(
        func.lower(MspPrice.crop) == func.lower(booking.crop)
    ).first()

    official_msp = float(scsd.official_msp) if scsd else (float(msp_record.official_msp_per_quintal) if msp_record else 2200.0)
    estimated_msp = float(scsd.estimated_procurement_price) if scsd else official_msp
    season = scsd.season if scsd else (f"{msp_record.marketing_season} {msp_record.season_year}" if msp_record else "2025-26")

    pricing_info = {
        "state": state_name,
        "crop": booking.crop,
        "season": season,
        "official_msp": official_msp,
        "estimated_msp": estimated_msp,
        "procurement_price": estimated_msp
    }

    # Fetch recorded evidence photos for this booking / appointment
    evidence_items = (
        db.query(ProcurementEvidence)
        .filter(
            (ProcurementEvidence.booking_id == booking.id) |
            (ProcurementEvidence.appointment_id == booking.appointment_id)
        )
        .order_by(ProcurementEvidence.id.asc())
        .all()
    )
    safe_evidence = [
        {
            "id": ev.id,
            "evidence_type": ev.evidence_type,
            "process_step": ev.process_step,
            "file_path": ev.file_path,
            "uploaded_by": ev.uploaded_by,
            "uploaded_at": str(ev.uploaded_at),
            "notes": ev.notes
        }
        for ev in evidence_items
    ]

    # Check storage lot status
    proc_rec = db.query(ProcurementRecord).filter(ProcurementRecord.booking_id == booking.id).first()
    storage_lot = db.query(StorageLot).filter(StorageLot.procurement_id == proc_rec.procurement_id).first() if proc_rec else None
    storage_info = None
    if storage_lot:
        storage_info = {
            "lot_id": storage_lot.lot_id,
            "warehouse_name": storage_lot.warehouse_name,
            "stack_number": storage_lot.stack_number,
            "quantity_quintals": float(storage_lot.quantity_quintals),
            "status": storage_lot.status,
            "is_verified": storage_lot.status == "VERIFIED_STORED",
            "storage_employee": storage_lot.storage_employee,
            "storage_condition": storage_lot.storage_condition,
            "physical_condition": storage_lot.physical_condition,
            "remarks": storage_lot.remarks
        }

    # Fetch available registered employees for this centre
    centre_emps = db.query(Employee).filter(
        Employee.centre_id == booking.centre_id,
        Employee.status == "ACTIVE"
    ).order_by(Employee.role, Employee.name).all()
    available_employees = [
        {
            "id": emp.id,
            "name": emp.name,
            "role": emp.role,
            "employee_code": emp.employee_code,
            "phone": emp.phone
        }
        for emp in centre_emps
    ]

    return {
        "success": True,
        "appointment": {
            "appointment_id": booking.appointment_id,
            "booking_id": booking.id,
            "farmer_name": farmer.name if farmer else "Registered Farmer",
            "farmer_id": booking.farmer_id,
            "farmer_mobile": (farmer.mobile if hasattr(farmer, 'mobile') else getattr(farmer, 'mobile_number', '-')) if farmer else "-",
            "centre_id": booking.centre_id,
            "centre_name": centre.centre_name if centre else booking.centre_id,
            "state": state_name,
            "crop": booking.crop,
            "booked_quantity": float(booking.quantity or 0),
            "arrival_status": booking.status,
            "is_mango": is_mango,
            "current_step_number": current_step_num,
            "is_all_completed": all(s.status == "COMPLETED" for s in steps)
        },
        "steps": safe_steps,
        "pricing": pricing_info,
        "evidence": safe_evidence,
        "storage_lot": storage_info,
        "mango_ai": ai_summary,
        "available_employees": available_employees
    }


@router.post("/process/{appointment_id}/step/{step_number}/submit")
def submit_procurement_process_step(
    appointment_id: str,
    step_number: int,
    req: ProcessStepSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submits a procurement process step with multi-employee tracking,
    data isolation, and photo evidence recording.
    """
    if step_number < 1 or step_number > 5:
        raise HTTPException(status_code=400, detail="Invalid step number. Process steps are 1 to 5.")

    booking = db.query(Booking).filter(
        (Booking.appointment_id == appointment_id) |
        (Booking.id == (int(appointment_id) if appointment_id.isdigit() else -1))
    ).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Appointment not found.")

    # Authorization
    user_role = (current_user.role or "").lower()
    if user_role not in ["centre", "procurement_centre", "admin", "government", "superadmin"]:
        raise HTTPException(status_code=403, detail="Unauthorized: User cannot perform procurement operations.")

    if current_user.centre_id and current_user.centre_id != booking.centre_id:
        raise HTTPException(status_code=403, detail="Unauthorized: Appointment belongs to a different centre.")

    steps = ensure_booking_process_steps(booking, db)
    step_map = {s.step_number: s for s in steps}
    target_step = step_map[step_number]

    # Immutability Check
    if target_step.status == "COMPLETED":
        raise HTTPException(
            status_code=400,
            detail=f"Step {step_number} is already COMPLETED and immutable. Use the audited correction endpoint to request modifications."
        )

    # Server-Side Sequence Enforcement
    if step_number > 1:
        prev_step = step_map[step_number - 1]
        if prev_step.status != "COMPLETED":
            raise HTTPException(
                status_code=400,
                detail=f"Sequence violation: Step {step_number - 1} must be COMPLETED before Step {step_number} can be submitted."
            )

    data = req.data or {}
    now = datetime.utcnow()

    # Requirement 2: Validate employee assignment from database
    emp_record = None
    input_emp_id = data.get("employee_id") or data.get("employee_code")
    input_emp_name = data.get("employee_name")

    if input_emp_id or input_emp_name:
        emp_query = db.query(Employee).filter(
            Employee.centre_id == booking.centre_id,
            Employee.status == "ACTIVE"
        )
        if input_emp_id:
            emp_record = emp_query.filter(
                (Employee.id == (int(input_emp_id) if str(input_emp_id).isdigit() else -1)) |
                (Employee.employee_code == str(input_emp_id))
            ).first()
        if not emp_record and input_emp_name:
            clean_name = str(input_emp_name).split('(')[0].strip()
            emp_record = emp_query.filter(
                (Employee.name == str(input_emp_name)) |
                (Employee.name.ilike(f"%{clean_name}%"))
            ).first()

    if emp_record:
        employee_id = emp_record.employee_code
        employee_name = emp_record.name
    elif not input_emp_id and not input_emp_name and current_user:
        employee_id = current_user.user_id
        employee_name = current_user.name or current_user.user_id
    else:
        # Check if user is registered user
        user_match = db.query(User).filter(
            (User.user_id == str(input_emp_id or current_user.user_id)) |
            (User.name == str(input_emp_name))
        ).first()
        if user_match:
            employee_id = user_match.user_id
            employee_name = user_match.name
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid employee: '{input_emp_name or input_emp_id}' is not an active registered employee for centre {booking.centre_id}."
            )

    try:
        # Process step-specific domain records
        if step_number == 1:
            # Step 1: Verification & Intake
            # Remove hardcoded truck assumption: support multiple transport methods
            transport_method = data.get("transport_method") or "Farmer's Own"
            truck_num = data.get("truck_number")
            if not truck_num and transport_method in ["Farmer's Own", "Personal"]:
                truck_num = "FARMER_OWN"
            elif not truck_num:
                truck_num = "DIRECT_ARRIVAL"

            bags = int(data.get("collected_bags") or 0)
            col_count = db.query(CollectionRecord).count() + 1
            collection_id = f"COL-{booking.centre_id}-{col_count:05d}"
            collected_qty = float(data.get("gross_weight_estimate") or booking.quantity or 25.0)

            existing_col = db.query(CollectionRecord).filter(CollectionRecord.booking_id == booking.id).first()
            if not existing_col:
                col = CollectionRecord(
                    collection_id=collection_id,
                    booking_id=booking.id,
                    farmer_id=booking.farmer_id,
                    centre_id=booking.centre_id,
                    crop=booking.crop,
                    collected_quantity=collected_qty,
                    collection_date=now.date(),
                    collection_method=transport_method,
                    truck_number=truck_num,
                    collected_by=employee_name,
                    status="RECEIVED"
                )
                db.add(col)
            else:
                existing_col.truck_number = truck_num
                existing_col.collection_method = transport_method
                existing_col.collected_by = employee_name
                existing_col.status = "RECEIVED"

            # Step 1 Photo Evidence
            if data.get("evidence_url"):
                ev = ProcurementEvidence(
                    booking_id=booking.id,
                    appointment_id=booking.appointment_id,
                    process_step="STEP_1_COLLECTION",
                    evidence_type="COLLECTION_PRODUCE",
                    file_path=data.get("evidence_url"),
                    original_filename="produce_intake.jpg",
                    file_size_bytes=0,
                    mime_type="image/jpeg",
                    notes=data.get("remarks") or f"Produce received via {transport_method}",
                    uploaded_by=employee_name
                )
                db.add(ev)

            if booking.status in ["BOOKED", "CONFIRMED", "ARRIVED"]:
                booking.status = "RECEIVED"

        elif step_number == 2:
            # Step 2: Physical Quality Inspection
            moisture = float(data.get("moisture_content_pct") or 12.0)
            foreign_matter = float(data.get("foreign_matter_pct") or 1.0)
            broken_grains = float(data.get("broken_grains_pct") or 0.0)
            damaged_grains = float(data.get("damaged_grains_pct") or 0.0)
            remarks = data.get("remarks") or "Physical quality inspection verified."

            if moisture < 0 or foreign_matter < 0:
                raise HTTPException(status_code=400, detail="Moisture and foreign matter percentages must be non-negative.")

            # Ensure collection record exists for foreign key
            col = db.query(CollectionRecord).filter(CollectionRecord.booking_id == booking.id).first()
            if not col:
                col_count = db.query(CollectionRecord).count() + 1
                col = CollectionRecord(
                    collection_id=f"COL-{booking.centre_id}-{col_count:05d}",
                    booking_id=booking.id,
                    farmer_id=booking.farmer_id,
                    centre_id=booking.centre_id,
                    crop=booking.crop,
                    collected_quantity=float(booking.quantity or 25.0),
                    collection_date=now.date(),
                    truck_number="DIRECT_ARRIVAL",
                    collected_by=employee_name,
                    status="RECEIVED"
                )
                db.add(col)
                db.flush()

            existing_qc = db.query(QualityCheck).filter(QualityCheck.collection_id == col.collection_id).first()
            if not existing_qc:
                qc_count = db.query(QualityCheck).count() + 1
                qc = QualityCheck(
                    check_id=f"QC-{booking.centre_id}-{qc_count:05d}",
                    collection_id=col.collection_id,
                    inspector_name=employee_name,
                    moisture_content_pct=moisture,
                    foreign_matter_pct=foreign_matter,
                    broken_grains_pct=broken_grains,
                    quality_grade="Grade A" if moisture <= 14.0 and foreign_matter <= 2.0 else "Grade B",
                    passed=True,
                    remarks=remarks,
                    checked_at=now
                )
                db.add(qc)
            else:
                existing_qc.moisture_content_pct = moisture
                existing_qc.foreign_matter_pct = foreign_matter
                existing_qc.broken_grains_pct = broken_grains
                existing_qc.inspector_name = employee_name
                existing_qc.remarks = remarks

            # Step 2 QC Machine Evidence Photo
            if data.get("evidence_url"):
                ev = ProcurementEvidence(
                    booking_id=booking.id,
                    appointment_id=booking.appointment_id,
                    process_step="STEP_2_QUALITY",
                    evidence_type="QUALITY_MACHINE",
                    file_path=data.get("evidence_url"),
                    original_filename="qc_machine.jpg",
                    file_size_bytes=0,
                    mime_type="image/jpeg",
                    notes=f"Moisture: {moisture}%, Foreign Matter: {foreign_matter}%",
                    uploaded_by=employee_name
                )
                db.add(ev)

        elif step_number == 3:
            # Step 3: AI Visual Quality Inspection
            is_mango = (booking.crop or "").strip().lower() == "mango"
            if is_mango:
                ai_insp = (
                    db.query(AIQualityInspection)
                    .filter(AIQualityInspection.booking_id == booking.id)
                    .order_by(AIQualityInspection.id.desc())
                    .first()
                )
                if not ai_insp:
                    raise HTTPException(
                        status_code=400,
                        detail="No Mango AI quality scan found for this appointment. Please upload and run the Mango AI Quality Scan before completing Step 3."
                    )
                review_action = data.get("review_action", "ACCEPT")
                if review_action == "OVERRIDE":
                    ai_insp.status = "MANUALLY_OVERRIDDEN"
                    ai_insp.review_notes = data.get("review_notes", "Manual override by QC Officer.")
                    ai_insp.reviewed_by = employee_name
                    ai_insp.reviewed_at = now
                else:
                    ai_insp.reviewed_by = employee_name
                    ai_insp.reviewed_at = now
            else:
                pass

        elif step_number == 4:
            # Step 4: Weighment
            gross_w = float(data.get("gross_weight_quintals") or 0.0)
            tare_w = float(data.get("tare_weight_quintals") or 0.0)
            weighbridge_id = data.get("weighbridge_id") or "WB-01"

            if gross_w <= 0:
                raise HTTPException(status_code=400, detail="Gross weight must be greater than zero.")
            if tare_w < 0 or tare_w >= gross_w:
                raise HTTPException(status_code=400, detail="Tare weight must be non-negative and less than gross weight.")

            net_w = round(gross_w - tare_w, 2)
            col = db.query(CollectionRecord).filter(CollectionRecord.booking_id == booking.id).first()
            col_id = col.collection_id if col else f"COL-{booking.centre_id}-00001"

            existing_w = db.query(Weighment).filter(Weighment.collection_id == col_id).first()
            if not existing_w:
                w_count = db.query(Weighment).count() + 1
                w_id = f"WM-{booking.centre_id}-{w_count:05d}"
                wm = Weighment(
                    weighment_id=w_id,
                    collection_id=col_id,
                    weighbridge_id=weighbridge_id,
                    gross_weight_quintals=gross_w,
                    tare_weight_quintals=tare_w,
                    net_weight_quintals=net_w,
                    operator_name=employee_name,
                    weighed_at=now
                )
                db.add(wm)
            else:
                existing_w.gross_weight_quintals = gross_w
                existing_w.tare_weight_quintals = tare_w
                existing_w.net_weight_quintals = net_w
                existing_w.operator_name = employee_name
                existing_w.weighbridge_id = weighbridge_id

            # Step 4 Weighing Machine Evidence Photo
            if data.get("evidence_url"):
                ev = ProcurementEvidence(
                    booking_id=booking.id,
                    appointment_id=booking.appointment_id,
                    process_step="STEP_4_WEIGHMENT",
                    evidence_type="WEIGHMENT",
                    file_path=data.get("evidence_url"),
                    original_filename="weighbridge_display.jpg",
                    file_size_bytes=0,
                    mime_type="image/jpeg",
                    notes=f"Gross: {gross_w} q, Tare: {tare_w} q, Net: {net_w} q",
                    uploaded_by=employee_name
                )
                db.add(ev)

        elif step_number == 5:
            # Step 5: Procurement Finalization
            is_mango = (booking.crop or "").strip().lower() == "mango"
            col = db.query(CollectionRecord).filter(CollectionRecord.booking_id == booking.id).first()
            col_id = col.collection_id if col else f"COL-{booking.centre_id}-00001"

            physical_qc = db.query(QualityCheck).filter(QualityCheck.collection_id == col_id).first() if col else None
            weighment = db.query(Weighment).filter(Weighment.collection_id == col_id).first() if col else None

            ai_visual_grade = None
            affected_pct = 0.0
            if is_mango:
                ai_insp = (
                    db.query(AIQualityInspection)
                    .filter(AIQualityInspection.booking_id == booking.id)
                    .order_by(AIQualityInspection.id.desc())
                    .first()
                )
                if ai_insp:
                    ai_visual_grade = ai_insp.visual_grade
                    affected_pct = float(ai_insp.affected_percentage or 0.0)

            # Compute final combined grade
            grading_result = compute_final_quality_grade(
                crop=booking.crop,
                physical_qc=physical_qc,
                ai_visual_assessment=ai_visual_grade,
                affected_percentage=affected_pct
            )
            final_grade = grading_result["final_grade"]

            # Retrieve authentic database MSP & estimated procurement price directly
            centre = db.query(ProcurementCentre).filter(ProcurementCentre.centre_id == booking.centre_id).first()
            state_name = centre.state if centre and centre.state else "Goa"

            scsd = db.query(StateCropSupplyDemand).filter(
                func.lower(StateCropSupplyDemand.state) == func.lower(state_name),
                func.lower(StateCropSupplyDemand.crop) == func.lower(booking.crop)
            ).first()
            msp_record = db.query(MspPrice).filter(
                func.lower(MspPrice.crop) == func.lower(booking.crop)
            ).first()

            db_estimated_msp = float(scsd.estimated_procurement_price) if scsd else (float(msp_record.official_msp_per_quintal) if msp_record else 2200.0)

            # Use submitted rate if valid, otherwise directly use estimated MSP from database
            rate_inr = float(data.get("rate_per_quintal_inr") or 0.0)
            if rate_inr <= 0:
                rate_inr = db_estimated_msp

            net_qty = float(weighment.net_weight_quintals) if weighment else float(booking.quantity or 25.0)
            total_val = round(net_qty * rate_inr, 2)

            p_count = db.query(ProcurementRecord).count() + 1
            proc_id = f"PR-{booking.centre_id}-{p_count:05d}"

            existing_pr = db.query(ProcurementRecord).filter(ProcurementRecord.booking_id == booking.id).first()
            if not existing_pr:
                pr = ProcurementRecord(
                    procurement_id=proc_id,
                    booking_id=booking.id,
                    collection_id=col_id,
                    farmer_id=booking.farmer_id,
                    centre_id=booking.centre_id,
                    crop=booking.crop,
                    procured_quantity_quintals=net_qty,
                    msp_rate_per_quintal=rate_inr,
                    total_procurement_value=total_val,
                    quality_grade=final_grade,
                    warehouse_location=data.get("warehouse_location") or "Bay A-1",
                    status="COMPLETED",
                    created_at=now
                )
                db.add(pr)
            else:
                existing_pr.procured_quantity_quintals = net_qty
                existing_pr.msp_rate_per_quintal = rate_inr
                existing_pr.total_procurement_value = total_val
                existing_pr.quality_grade = final_grade
                existing_pr.warehouse_location = data.get("warehouse_location") or existing_pr.warehouse_location
                proc_id = existing_pr.procurement_id

            # Create or update payment record using correct Payment model columns
            pay = db.query(Payment).filter(Payment.procurement_id == proc_id).first()
            if not pay:
                pay_count = db.query(Payment).count() + 1
                pay_id = f"PAY-{booking.centre_id}-{pay_count:05d}"
                new_pay = Payment(
                    payment_id=pay_id,
                    procurement_id=proc_id,
                    farmer_id=str(booking.farmer_id),
                    amount=total_val,
                    msp_rate=rate_inr,
                    quantity_quintals=net_qty,
                    payment_mode="DBT_AADHAAR",
                    payment_status="PENDING",
                    initiated_at=now
                )
                db.add(new_pay)
            else:
                pay.amount = total_val
                pay.msp_rate = rate_inr
                pay.quantity_quintals = net_qty

            # Create warehouse storage lot record
            s_lot = db.query(StorageLot).filter(StorageLot.procurement_id == proc_id).first()
            if not s_lot:
                lot_count = db.query(StorageLot).count() + 1
                s_lot = StorageLot(
                    lot_id=f"LOT-{booking.centre_id}-{now.strftime('%Y%m%d')}-{lot_count:04d}",
                    procurement_id=proc_id,
                    centre_id=booking.centre_id,
                    crop=booking.crop,
                    quantity_quintals=net_qty,
                    warehouse_name=centre.centre_name if centre else f"Centre Warehouse {booking.centre_id}",
                    stack_number=data.get("warehouse_location") or "Bay A-1",
                    storage_date=now.date(),
                    status="STORED"
                )
                db.add(s_lot)

            # Step 5 Final Clearance Photo Evidence
            if data.get("evidence_url"):
                ev = ProcurementEvidence(
                    booking_id=booking.id,
                    appointment_id=booking.appointment_id,
                    procurement_id=proc_id,
                    process_step="STEP_5_PROCUREMENT",
                    evidence_type="QUALITY_INSPECTION",
                    file_path=data.get("evidence_url"),
                    original_filename="procurement_clearance.jpg",
                    file_size_bytes=0,
                    mime_type="image/jpeg",
                    notes=f"Procured at MSP ₹{rate_inr}/q, Grade {final_grade}",
                    uploaded_by=employee_name
                )
                db.add(ev)

            booking.status = "PROCURED"

        # Mark target step as COMPLETED
        target_step.status = "COMPLETED"
        target_step.completed_by = employee_id
        target_step.employee_name = employee_name
        target_step.completed_at = now
        if not target_step.started_at:
            target_step.started_at = now

        # Unlock next step to IN_PROGRESS if exists
        if step_number < 5:
            next_step = step_map[step_number + 1]
            if next_step.status == "PENDING":
                next_step.status = "IN_PROGRESS"
                next_step.started_at = now

        # Write audit log
        audit = ProcessAuditLog(
            user_id=employee_id,
            centre_id=booking.centre_id,
            appointment_id=booking.appointment_id,
            process_step=f"STEP_{step_number}_{target_step.step_type}",
            action="STEP_COMPLETED",
            record_id=str(target_step.id),
            new_value=f"Completed by {employee_name} ({employee_id})",
            ip_address="127.0.0.1"
        )
        db.add(audit)

        db.commit()

        return {
            "success": True,
            "message": f"Step {step_number} ({target_step.step_type}) completed successfully.",
            "step_number": step_number,
            "status": "COMPLETED",
            "next_step_unlocked": step_number + 1 if step_number < 5 else None
        }

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in submit_procurement_process_step (step {step_number}, appointment {appointment_id}): {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Procurement process error in Step {step_number}: {str(e)}"
        )


@router.post("/process/{appointment_id}/storage-check")
def record_storage_final_check(
    appointment_id: str,
    req: StorageCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Independent Storage Final Check:
    When produce reaches storage warehouse, an authorized storage employee performs
    an independent physical inspection, verifies quantity received, records storage
    conditions (temperature, aeration, stacking), and captures storage photo evidence.
    """
    booking = db.query(Booking).filter(
        (Booking.appointment_id == appointment_id) |
        (Booking.id == (int(appointment_id) if appointment_id.isdigit() else -1))
    ).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Appointment not found.")

    if booking.status not in ["PROCURED", "COMPLETED"]:
        raise HTTPException(
            status_code=400,
            detail=f"Storage final check can only be performed after procurement finalization (Step 5). Current booking status is '{booking.status}'."
        )

    proc_rec = db.query(ProcurementRecord).filter(ProcurementRecord.booking_id == booking.id).first()
    if not proc_rec:
        raise HTTPException(status_code=404, detail="Procurement record not found for this appointment.")

    storage_lot = db.query(StorageLot).filter(StorageLot.procurement_id == proc_rec.procurement_id).first()
    now = datetime.utcnow()

    # Requirement 2: Validate storage employee against database
    emp_record = None
    input_emp_id = req.storage_employee_id
    input_emp_name = req.storage_employee_name

    if input_emp_id or input_emp_name:
        emp_query = db.query(Employee).filter(
            Employee.centre_id == booking.centre_id,
            Employee.status == "ACTIVE"
        )
        if input_emp_id:
            emp_record = emp_query.filter(
                (Employee.id == (int(input_emp_id) if str(input_emp_id).isdigit() else -1)) |
                (Employee.employee_code == str(input_emp_id))
            ).first()
        if not emp_record and input_emp_name:
            clean_name = str(input_emp_name).split('(')[0].strip()
            emp_record = emp_query.filter(
                (Employee.name == str(input_emp_name)) |
                (Employee.name.ilike(f"%{clean_name}%"))
            ).first()

    if emp_record:
        storage_emp_id = emp_record.employee_code
        storage_emp_name = emp_record.name
    elif not input_emp_id and not input_emp_name and current_user:
        storage_emp_id = current_user.user_id
        storage_emp_name = current_user.name or current_user.user_id
    else:
        user_match = db.query(User).filter(
            (User.user_id == str(input_emp_id or current_user.user_id)) |
            (User.name == str(input_emp_name))
        ).first()
        if user_match:
            storage_emp_id = user_match.user_id
            storage_emp_name = user_match.name
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid storage employee: '{input_emp_name or input_emp_id}' is not an active registered employee for centre {booking.centre_id}."
            )

    if not storage_lot:
        lot_count = db.query(StorageLot).count() + 1
        storage_lot = StorageLot(
            lot_id=f"LOT-{booking.centre_id}-{now.strftime('%Y%m%d')}-{lot_count:04d}",
            procurement_id=proc_rec.procurement_id,
            centre_id=booking.centre_id,
            crop=booking.crop,
            quantity_quintals=req.received_quantity_quintals,
            warehouse_name=f"Centre Warehouse {booking.centre_id}",
            stack_number="Bay A-1",
            storage_date=now.date(),
            status="VERIFIED_STORED",
            storage_employee=f"{storage_emp_name} ({storage_emp_id})",
            storage_condition=req.storage_condition,
            physical_condition=req.physical_condition,
            remarks=req.remarks
        )
        db.add(storage_lot)
    else:
        storage_lot.quantity_quintals = req.received_quantity_quintals
        storage_lot.status = "VERIFIED_STORED"
        storage_lot.storage_employee = f"{storage_emp_name} ({storage_emp_id})"
        storage_lot.storage_condition = req.storage_condition
        storage_lot.physical_condition = req.physical_condition
        storage_lot.remarks = req.remarks

    # If photo evidence was attached, record in ProcurementEvidence
    if req.evidence_url:
        ev = ProcurementEvidence(
            booking_id=booking.id,
            appointment_id=booking.appointment_id,
            procurement_id=proc_rec.procurement_id,
            process_step="STORAGE_FINAL_CHECK",
            evidence_type="STORAGE",
            file_path=req.evidence_url,
            original_filename="storage_check.jpg",
            file_size_bytes=0,
            mime_type="image/jpeg",
            notes=req.remarks or "Storage intake physical inspection and stack verification",
            uploaded_by=storage_emp_name
        )
        db.add(ev)

    # Audit log
    audit = ProcessAuditLog(
        user_id=storage_emp_id,
        centre_id=booking.centre_id,
        appointment_id=booking.appointment_id,
        process_step="STORAGE_FINAL_CHECK",
        action="STORAGE_FINAL_CHECK_COMPLETED",
        record_id=str(storage_lot.id if storage_lot.id else ""),
        new_value=json.dumps({
            "storage_employee": storage_emp_name,
            "received_quantity_quintals": req.received_quantity_quintals,
            "storage_condition": req.storage_condition,
            "physical_condition": req.physical_condition,
            "remarks": req.remarks
        }),
        ip_address="127.0.0.1"
    )
    db.add(audit)
    db.commit()

    return {
        "success": True,
        "message": "Storage final check completed and verified successfully.",
        "storage_lot": {
            "lot_id": storage_lot.lot_id,
            "status": storage_lot.status,
            "quantity_quintals": float(storage_lot.quantity_quintals),
            "storage_employee": storage_lot.storage_employee,
            "storage_condition": storage_lot.storage_condition,
            "physical_condition": storage_lot.physical_condition,
            "remarks": storage_lot.remarks
        }
    }


@router.post("/process/{appointment_id}/correction")
def apply_procurement_step_correction(
    appointment_id: str,
    req: ProcessStepCorrectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Audited correction mechanism:
    Allows authorized employees to correct an erroneous field in a completed step
    without silently overwriting history. Preserves old value, new value, reason,
    employee, and timestamp in process_step_corrections and process_audit_logs.
    """
    booking = db.query(Booking).filter(
        (Booking.appointment_id == appointment_id) |
        (Booking.id == (int(appointment_id) if appointment_id.isdigit() else -1))
    ).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Appointment not found.")

    if not req.correction_reason or len(req.correction_reason.strip()) < 5:
        raise HTTPException(status_code=400, detail="A valid, substantive correction reason (at least 5 characters) is required.")

    # Find target process step
    step = (
        db.query(ProcurementProcessStep)
        .filter(
            ProcurementProcessStep.booking_id == booking.id,
            ProcurementProcessStep.step_number == req.step_number
        )
        .first()
    )
    if not step or step.status not in ["COMPLETED", "CORRECTED"]:
        raise HTTPException(status_code=400, detail=f"Step {req.step_number} is not completed. Only completed steps can be corrected.")

    old_val_str = None
    employee_name = current_user.name or current_user.user_id

    # Fetch corresponding domain record to retrieve old value and apply correction
    if req.step_number == 1:
        col = db.query(CollectionRecord).filter(CollectionRecord.booking_id == booking.id).first()
        if col and hasattr(col, req.field_name):
            old_val_str = str(getattr(col, req.field_name))
            setattr(col, req.field_name, req.new_value)
    elif req.step_number == 2:
        qc = db.query(QualityCheck).filter(QualityCheck.booking_id == booking.id).first()
        if qc and hasattr(qc, req.field_name):
            old_val_str = str(getattr(qc, req.field_name))
            setattr(qc, req.field_name, float(req.new_value) if req.field_name.endswith("_pct") else req.new_value)
    elif req.step_number == 4:
        wm = db.query(Weighment).filter(Weighment.booking_id == booking.id).first()
        if wm and hasattr(wm, req.field_name):
            old_val_str = str(getattr(wm, req.field_name))
            setattr(wm, req.field_name, float(req.new_value))
            if req.field_name in ["gross_weight_quintals", "tare_weight_quintals"]:
                wm.net_weight_quintals = round(float(wm.gross_weight_quintals) - float(wm.tare_weight_quintals), 2)

    # Record historical correction
    corr = ProcessStepCorrection(
        booking_id=booking.id,
        appointment_id=booking.appointment_id,
        step_number=req.step_number,
        field_name=req.field_name,
        old_value=old_val_str or "N/A",
        new_value=req.new_value,
        correction_reason=req.correction_reason.strip(),
        corrected_by=employee_name
    )
    db.add(corr)

    # Mark step status as CORRECTED
    step.status = "CORRECTED"

    # Add immutable audit log entry
    audit = ProcessAuditLog(
        user_id=current_user.user_id,
        centre_id=booking.centre_id,
        appointment_id=booking.appointment_id,
        process_step=f"STEP_{req.step_number}_{step.step_type}",
        action="AUDITED_CORRECTION_APPLIED",
        record_id=str(corr.id),
        old_value=old_val_str or "N/A",
        new_value=req.new_value,
        correction_reason=req.correction_reason.strip(),
        ip_address="127.0.0.1"
    )
    db.add(audit)

    db.commit()

    return {
        "success": True,
        "message": f"Audited correction recorded for Step {req.step_number} ({req.field_name}).",
        "correction": {
            "step_number": req.step_number,
            "field_name": req.field_name,
            "old_value": old_val_str,
            "new_value": req.new_value,
            "correction_reason": req.correction_reason,
            "corrected_by": employee_name,
            "corrected_at": str(datetime.utcnow())
        }
    }


@router.post("/appointments/{appointment_id}/ai-inspection")
async def scan_mango_quality_image_by_appointment(
    appointment_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await scan_mango_quality_image(appointment_id=appointment_id, file=file, db=db, current_user=current_user)


@router.post("/quality/mango-scan")
async def scan_mango_quality_image(
    appointment_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mango AI Visual Quality Scan.
    Accepts ONE photograph containing MULTIPLE sampled mangoes.
    Performs:
    1. Crop verification: Mango ONLY. Non-mango crops are rejected.
    2. Multi-mango detection & segmentation.
    3. CIELAB feature extraction (a*, b*, L*).
    4. Individual classification.
    5. Lot-level aggregation & prototype visual grading.
    6. Stores original and annotated detection image.
    """
    # 1. Fetch booking or support interactive pre-inspection / demo scan
    is_demo = str(appointment_id).upper() in ["DEMO", "PRE-INSPECTION", "SAMPLE", "TEST", "PRE_GATE", "NONE", ""]
    booking = None
    if not is_demo:
        booking = db.query(Booking).filter(
            (Booking.appointment_id == appointment_id) |
            (Booking.id == (int(appointment_id) if str(appointment_id).isdigit() else -1))
        ).first()

    # 2. Authorization & crop verification
    user_role = (current_user.role or "").lower()
    if booking:
        if user_role not in ["centre", "procurement_centre", "admin", "government", "superadmin", "farmer"]:
            raise HTTPException(status_code=403, detail="Unauthorized: User cannot perform quality inspection.")
        if current_user.centre_id and current_user.centre_id != booking.centre_id and user_role != "farmer":
            raise HTTPException(status_code=403, detail="Unauthorized: Appointment belongs to a different centre.")
        crop_name = (booking.crop or "").strip().lower()
        if crop_name != "mango":
            raise HTTPException(
                status_code=400,
                detail=f"Mango AI visual scan is currently supported for MANGO ONLY. Current appointment crop is '{booking.crop}'. AI scanning is unavailable for this crop."
            )
    else:
        # Standalone pre-inspection mode (farmers / demonstration)
        is_demo = True

    # 3. Validate image file
    orig_name = file.filename or "mango_sample.jpg"
    ext = os.path.splitext(orig_name)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
        raise HTTPException(status_code=400, detail="Invalid image format. Supported formats: JPEG, PNG, WEBP.")

    image_bytes = await file.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded image is empty.")
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image size exceeds maximum limit of 10MB.")

    # 5. Run inference pipeline
    scanner = get_mango_quality_scanner()
    try:
        scan_result = scanner.inspect_lot_image(image_bytes)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Mango AI processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Mango AI processing error: {str(e)}")

    # 6. Save original image & annotated image to uploads/mango_inspections
    uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "mango_inspections"))
    os.makedirs(uploads_dir, exist_ok=True)
    uid = uuid.uuid4().hex[:10]
    b_id = booking.id if booking else "demo"
    safe_orig_filename = f"mango_orig_{b_id}_{uid}{ext}"
    orig_dest = os.path.join(uploads_dir, safe_orig_filename)
    with open(orig_dest, "wb") as f:
        f.write(image_bytes)

    orig_web_path = f"/uploads/mango_inspections/{safe_orig_filename}"
    annotated_web_path = None

    if scan_result.get("annotated_image_bytes"):
        safe_annotated_filename = f"mango_annotated_{b_id}_{uid}.jpg"
        annotated_dest = os.path.join(uploads_dir, safe_annotated_filename)
        with open(annotated_dest, "wb") as f:
            f.write(scan_result["annotated_image_bytes"])
        annotated_web_path = f"/uploads/mango_inspections/{safe_annotated_filename}"

    # 7. Store AI Quality Inspection record when tied to appointment
    insp_code = f"AI-QC-{booking.centre_id if booking else 'DEMO'}-{uuid.uuid4().hex[:8].upper()}"
    employee_name = current_user.name or current_user.user_id

    ai_inspection = None
    if booking:
        ai_inspection = AIQualityInspection(
            inspection_code=insp_code,
            booking_id=booking.id,
            appointment_id=booking.appointment_id,
            centre_id=booking.centre_id,
            crop="Mango",
            image_path=orig_web_path,
            annotated_image_path=annotated_web_path,
            model_version=scan_result.get("model_version", "mango-quality-v1"),
            model_type=scan_result.get("model_type", "CIELAB SVM+KNN (L*a*b* & a*b*)"),
            sample_count=scan_result.get("mangoes_detected", 0),
            healthy_count=scan_result.get("healthy", 0),
            defect_count=scan_result.get("defect_count", 0),
            anthracnose_count=scan_result.get("anthracnose", 0),
            scab_count=scan_result.get("scab", 0),
            bacterial_canker_count=scan_result.get("bacterial_canker", 0),
            stem_end_rot_count=scan_result.get("stem_end_rot", 0),
            other_count=scan_result.get("other", 0),
            ripe_count=scan_result.get("ripe_count", 0),
            nearly_ripe_count=scan_result.get("nearly_ripe_count", 0),
            not_ripe_count=scan_result.get("not_ripe_count", 0),
            uncertain_count=scan_result.get("uncertain_count", 0),
            affected_percentage=scan_result.get("affected_percentage", 0.0),
            visual_grade=scan_result.get("visual_grade", "Grade A"),
            confidence=scan_result.get("confidence", 0.0),
            status="NEEDS_REVIEW" if scan_result.get("needs_review") else "COMPLETED",
            reviewed_by=employee_name,
            reviewed_at=datetime.utcnow()
        )
        db.add(ai_inspection)
        db.flush()

        # 8. Store individual detections
        for det in scan_result.get("detections", []):
            bbox = det.get("bbox", [0, 0, 0, 0])
            detection_row = AIInspectionDetection(
                inspection_id=ai_inspection.id,
                sample_index=det.get("sample_index", 1),
                predicted_class=det.get("class", "Unknown"),
                ripeness=det.get("ripeness", "Uncertain"),
                confidence=det.get("confidence", 0.0),
                box_x=bbox[0],
                box_y=bbox[1],
                box_w=bbox[2],
                box_h=bbox[3],
                crop_image_path=det.get("crop_url")
            )
            db.add(detection_row)

        # 9. Audit Log
        audit = ProcessAuditLog(
            user_id=current_user.user_id,
            centre_id=booking.centre_id,
            appointment_id=booking.appointment_id,
            process_step="STEP_3_AI_QUALITY",
            action="MANGO_AI_SCAN_EXECUTED",
            record_id=str(ai_inspection.id),
            new_value=f"Detected: {scan_result.get('mangoes_detected')}, Defective: {scan_result.get('defect_count')}, Grade: {scan_result.get('visual_grade')}, Affected: {scan_result.get('affected_percentage')}%, Ripe: {scan_result.get('ripe_count')}",
            ip_address="127.0.0.1"
        )
        db.add(audit)
        db.commit()

    def sanitize_value(v):
        if isinstance(v, (int, float, str, bool)) or v is None:
            return v
        import numpy as np
        if isinstance(v, (np.integer,)):
            return int(v)
        elif isinstance(v, (np.floating,)):
            return float(v)
        elif isinstance(v, np.ndarray):
            return v.tolist()
        elif isinstance(v, dict):
            return {str(k): sanitize_value(val) for k, val in v.items() if k != 'mask' and k != 'annotated_image_bytes'}
        elif isinstance(v, (list, tuple)):
            return [sanitize_value(item) for item in v]
        elif isinstance(v, (bytes, bytearray)):
            return None
        return str(v)

    sanitized_detections = sanitize_value(scan_result.get("detections", []))
    mango_count = int(scan_result.get("mangoes_detected", 0))

    response_payload = {
        "success": True,
        "inspection_id": ai_inspection.id if ai_inspection else 99999,
        "inspection_code": ai_inspection.inspection_code if ai_inspection else insp_code,
        "appointment_id": booking.appointment_id if booking else str(appointment_id or "DEMO-APPT"),
        "crop": "Mango",
        "sample_count": mango_count,
        "mangoes_detected": mango_count,
        "count": mango_count,
        "mangoes": sanitized_detections,
        "message": "Mango AI visual inspection completed successfully." if mango_count > 0 else "No mangoes detected in the uploaded image.",
        "healthy": int(scan_result.get("healthy", 0)),
        "healthy_count": int(scan_result.get("healthy_count", scan_result.get("healthy", 0))),
        "defect_count": int(scan_result.get("defect_count", 0)),
        "anthracnose": int(scan_result.get("anthracnose", 0)),
        "anthracnose_count": int(scan_result.get("anthracnose", 0)),
        "scab": int(scan_result.get("scab", 0)),
        "scab_count": int(scan_result.get("scab", 0)),
        "bacterial_canker": int(scan_result.get("bacterial_canker", 0)),
        "bacterial_canker_count": int(scan_result.get("bacterial_canker", 0)),
        "stem_end_rot": int(scan_result.get("stem_end_rot", 0)),
        "stem_end_rot_count": int(scan_result.get("stem_end_rot", 0)),
        "other": int(scan_result.get("other", 0)),
        "other_count": int(scan_result.get("other", 0)),
        "ripe_count": int(scan_result.get("ripe_count", 0)),
        "nearly_ripe_count": int(scan_result.get("nearly_ripe_count", 0)),
        "not_ripe_count": int(scan_result.get("not_ripe_count", 0)),
        "uncertain_count": int(scan_result.get("uncertain_count", 0)),
        "ripeness_summary": sanitize_value(scan_result.get("ripeness_summary", {})),
        "affected_percentage": float(scan_result.get("affected_percentage", 0.0)),
        "visual_grade": str(scan_result.get("visual_grade", "Grade A")),
        "confidence": float(scan_result.get("confidence", 0.0)),
        "status": str(ai_inspection.status) if ai_inspection else ("NEEDS_REVIEW" if scan_result.get("needs_review") else "COMPLETED"),
        "needs_review": bool(scan_result.get("needs_review", False)),
        "review_reason": scan_result.get("review_reason"),
        "annotated_image_url": annotated_web_path,
        "original_image_url": orig_web_path,
        "debug_images": sanitize_value(scan_result.get("debug_images", {})),
        "detections": sanitized_detections
    }

    return sanitize_value(response_payload)

