from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, String


from backend.app.core.database import get_db
from backend.app.core.deps import get_current_user_optional
from backend.app.models.farmer import Farmer, FarmerCrop
from backend.app.models.booking import Booking
from backend.app.models.procurement import StorageLot, Payment
from backend.app.models.audit import AuditLog
from backend.app.schemas.farmer import FarmerUpdate, FarmerResponse

router = APIRouter(prefix="/farmers", tags=["Farmers"])

@router.get("")
def list_farmers(
    district: Optional[str] = None,
    state: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(Farmer)
    if district:
        query = query.filter(Farmer.district == district)
    if state:
        query = query.filter(Farmer.state == state)
    if search:
        s = f"%{search.strip()}%"
        query = query.filter((Farmer.name.ilike(s)) | (Farmer.farmer_code.ilike(s)) | (Farmer.mobile.ilike(s)))

    total = query.count()
    items = query.order_by(Farmer.id.asc()).offset((page - 1) * limit).limit(limit).all()

    result = []
    for f in items:
        result.append({
            "id": f.id,
            "farmer_code": f.farmer_code,
            "user_id": f.user_id,
            "name": f.name,
            "mobile": f.mobile,
            "state": f.state,
            "district": f.district,
            "taluka": f.taluka,
            "village": f.village,
            "land_area_hectares": float(f.land_area_hectares),
            "ekyc_status": f.ekyc_status,
            "crops_count": len(f.crops)
        })

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "farmers": result
    }

@router.get("/{id_or_uid}")
def get_farmer_profile(id_or_uid: str, db: Session = Depends(get_db)):
    farmer = db.query(Farmer).filter(
        (Farmer.user_id == id_or_uid) | (Farmer.farmer_code == id_or_uid) | (cast(Farmer.id, String) == id_or_uid)
    ).first()

    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found.")

    crops_list = [
        {
            "id": c.id,
            "crop_name": c.crop_name,
            "season": c.season,
            "sowing_date": str(c.sowing_date) if c.sowing_date else None,
            "expected_harvest_date": str(c.expected_harvest_date) if c.expected_harvest_date else None,
            "estimated_quantity_quintals": float(c.estimated_quantity_quintals)
        }
        for c in farmer.crops
    ]

    return {
        "id": farmer.id,
        "farmer_code": farmer.farmer_code,
        "user_id": farmer.user_id,
        "name": farmer.name,
        "mobile": farmer.mobile,
        "email": farmer.email,
        "dob": str(farmer.dob) if farmer.dob else None,
        "gender": farmer.gender,
        "address": farmer.address,
        "state": farmer.state,
        "district": farmer.district,
        "taluka": farmer.taluka,
        "village": farmer.village,
        "land_area_hectares": float(farmer.land_area_hectares),
        "ekyc_status": farmer.ekyc_status,
        "aadhaar_masked": farmer.aadhaar_masked,
        "bank_name": farmer.bank_name,
        "bank_account_no": farmer.bank_account_no,
        "bank_ifsc": farmer.bank_ifsc,
        "crops": crops_list
    }

@router.put("/{id_or_uid}")
def update_farmer_profile(id_or_uid: str, req: FarmerUpdate, db: Session = Depends(get_db)):
    farmer = db.query(Farmer).filter(
        (Farmer.user_id == id_or_uid) | (Farmer.farmer_code == id_or_uid) | (cast(Farmer.id, String) == id_or_uid)
    ).first()

    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found.")

    old_data = f"Name: {farmer.name}, Mobile: {farmer.mobile}, Land: {farmer.land_area_hectares}"

    if req.name is not None: farmer.name = req.name.strip()
    if req.mobile is not None: farmer.mobile = req.mobile.strip()
    if req.email is not None: farmer.email = req.email.strip()
    if req.address is not None: farmer.address = req.address.strip()
    if req.land_area_hectares is not None: farmer.land_area_hectares = req.land_area_hectares
    if req.bank_name is not None: farmer.bank_name = req.bank_name.strip()
    if req.bank_account_no is not None: farmer.bank_account_no = req.bank_account_no.strip()
    if req.bank_ifsc is not None: farmer.bank_ifsc = req.bank_ifsc.strip()

    new_data = f"Name: {farmer.name}, Mobile: {farmer.mobile}, Land: {farmer.land_area_hectares}"

    audit = AuditLog(
        user_id=farmer.user_id,
        action="FARMER_PROFILE_UPDATED",
        entity="FARMER",
        entity_id=farmer.farmer_code,
        old_value=old_data,
        new_value=new_data
    )
    db.add(audit)
    db.commit()

    return {"message": "Farmer profile updated successfully."}

@router.get("/{id_or_uid}/summary")
def get_farmer_summary(id_or_uid: str, db: Session = Depends(get_db)):
    farmer = db.query(Farmer).filter(
        (Farmer.user_id == id_or_uid) | (Farmer.farmer_code == id_or_uid) | (cast(Farmer.id, String) == id_or_uid)
    ).first()

    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found.")

    # Recent booking
    recent_booking = db.query(Booking).filter(Booking.farmer_id == farmer.user_id).order_by(Booking.id.desc()).first()
    
    # Total bookings & total quantity
    bookings_count = db.query(Booking).filter(Booking.farmer_id == farmer.user_id).count()
    
    # Latest payment
    latest_payment = db.query(Payment).filter(Payment.farmer_id == farmer.user_id).order_by(Payment.id.desc()).first()

    return {
        "farmer_name": farmer.name,
        "farmer_code": farmer.farmer_code,
        "user_id": farmer.user_id,
        "village": farmer.village,
        "district": farmer.district,
        "ekyc_status": farmer.ekyc_status,
        "land_area_hectares": float(farmer.land_area_hectares),
        "crops": [{"crop_name": c.crop_name, "quantity": float(c.estimated_quantity_quintals)} for c in farmer.crops],
        "total_bookings": bookings_count,
        "recent_booking": {
            "appointment_id": recent_booking.appointment_id,
            "crop": recent_booking.crop,
            "quantity": float(recent_booking.quantity),
            "status": recent_booking.status,
            "qr_token": recent_booking.qr_token,
            "created_at": str(recent_booking.created_at)
        } if recent_booking else None,
        "latest_payment": {
            "payment_id": latest_payment.payment_id,
            "amount": float(latest_payment.amount),
            "payment_status": latest_payment.payment_status,
            "transaction_ref": latest_payment.transaction_ref
        } if latest_payment else None
    }
