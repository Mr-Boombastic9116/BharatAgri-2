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
from backend.app.schemas.farmer import FarmerUpdate, FarmerResponse, CropCreate, CropUpdate

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

def get_authenticated_target_farmer(id_or_uid: str, db: Session, current_user = None) -> Farmer:
    target_id = id_or_uid.strip() if id_or_uid else ""
    if target_id.lower() in ["me", "self", "current"]:
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required to access own profile.")
        target_id = current_user.user_id

    farmer = db.query(Farmer).filter(
        (Farmer.user_id == target_id) | (Farmer.farmer_code == target_id) | (cast(Farmer.id, String) == target_id)
    ).first()

    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found.")

    # Authorization verification: if requesting user is a farmer, they cannot access another farmer's data
    if current_user and getattr(current_user, "role", "").lower() == "farmer":
        user_uid = str(current_user.user_id).strip()
        if farmer.user_id != user_uid and farmer.farmer_code != user_uid and str(farmer.id) != user_uid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You cannot access or modify another farmer's records."
            )

    return farmer


@router.get("/{id_or_uid}")
def get_farmer_profile(
    id_or_uid: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    farmer = get_authenticated_target_farmer(id_or_uid, db, current_user)

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
def update_farmer_profile(
    id_or_uid: str,
    req: FarmerUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    farmer = get_authenticated_target_farmer(id_or_uid, db, current_user)

    old_data = f"Name: {farmer.name}, Mobile: {farmer.mobile}, Land: {farmer.land_area_hectares}, Village: {farmer.village}"

    if req.name is not None and req.name.strip(): farmer.name = req.name.strip()
    if req.mobile is not None and req.mobile.strip(): farmer.mobile = req.mobile.strip()
    if req.email is not None: farmer.email = req.email.strip()
    if req.dob is not None: farmer.dob = req.dob
    if req.gender is not None and req.gender.strip(): farmer.gender = req.gender.strip()
    if req.address is not None: farmer.address = req.address.strip()
    if req.state is not None and req.state.strip(): farmer.state = req.state.strip()
    if req.district is not None and req.district.strip(): farmer.district = req.district.strip()
    if req.taluka is not None and req.taluka.strip(): farmer.taluka = req.taluka.strip()
    if req.village is not None and req.village.strip(): farmer.village = req.village.strip()
    if req.land_area_hectares is not None and req.land_area_hectares > 0:
        farmer.land_area_hectares = req.land_area_hectares
    if req.bank_name is not None: farmer.bank_name = req.bank_name.strip()
    if req.bank_account_no is not None: farmer.bank_account_no = req.bank_account_no.strip()
    if req.bank_ifsc is not None: farmer.bank_ifsc = req.bank_ifsc.strip()

    new_data = f"Name: {farmer.name}, Mobile: {farmer.mobile}, Land: {farmer.land_area_hectares}, Village: {farmer.village}"

    audit = AuditLog(
        user_id=current_user.user_id if current_user else farmer.user_id,
        action="FARMER_PROFILE_UPDATED",
        entity="FARMER",
        entity_id=farmer.farmer_code,
        old_value=old_data,
        new_value=new_data
    )
    db.add(audit)
    db.commit()
    db.refresh(farmer)

    return {
        "message": "Farmer profile updated successfully.",
        "farmer": {
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
            "bank_name": farmer.bank_name,
            "bank_account_no": farmer.bank_account_no,
            "bank_ifsc": farmer.bank_ifsc
        }
    }


# ====================================================
# FARMER CROPS CRUD (STRICT FARMER ISOLATION & VALIDATION)
# ====================================================

@router.get("/{id_or_uid}/crops")
def list_farmer_crops(
    id_or_uid: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    farmer = get_authenticated_target_farmer(id_or_uid, db, current_user)
    return [
        {
            "id": c.id,
            "farmer_id": c.farmer_id,
            "crop_name": c.crop_name,
            "season": c.season,
            "sowing_date": str(c.sowing_date) if c.sowing_date else None,
            "expected_harvest_date": str(c.expected_harvest_date) if c.expected_harvest_date else None,
            "estimated_quantity_quintals": float(c.estimated_quantity_quintals)
        }
        for c in farmer.crops
    ]


@router.post("/{id_or_uid}/crops", status_code=201)
def add_farmer_crop(
    id_or_uid: str,
    req: CropCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    farmer = get_authenticated_target_farmer(id_or_uid, db, current_user)

    if not req.crop_name or not req.crop_name.strip():
        raise HTTPException(status_code=400, detail="Crop name is required.")
    if req.estimated_quantity_quintals <= 0:
        raise HTTPException(status_code=400, detail="Estimated quantity must be greater than 0 Quintals.")

    new_crop = FarmerCrop(
        farmer_id=farmer.id,
        crop_name=req.crop_name.strip(),
        season=req.season.strip() if req.season else "Kharif 2026-27",
        sowing_date=req.sowing_date,
        expected_harvest_date=req.expected_harvest_date,
        estimated_quantity_quintals=req.estimated_quantity_quintals
    )
    db.add(new_crop)
    db.flush()

    audit = AuditLog(
        user_id=current_user.user_id if current_user else farmer.user_id,
        action="FARMER_CROP_ADDED",
        entity="FARMER_CROP",
        entity_id=str(new_crop.id),
        old_value=None,
        new_value=f"Crop: {new_crop.crop_name}, Qty: {new_crop.estimated_quantity_quintals} Q, Season: {new_crop.season}"
    )
    db.add(audit)
    db.commit()

    return {
        "message": f"Crop '{new_crop.crop_name}' added successfully.",
        "crop": {
            "id": new_crop.id,
            "farmer_id": new_crop.farmer_id,
            "crop_name": new_crop.crop_name,
            "season": new_crop.season,
            "sowing_date": str(new_crop.sowing_date) if new_crop.sowing_date else None,
            "expected_harvest_date": str(new_crop.expected_harvest_date) if new_crop.expected_harvest_date else None,
            "estimated_quantity_quintals": float(new_crop.estimated_quantity_quintals)
        }
    }


@router.put("/{id_or_uid}/crops/{crop_id}")
def update_farmer_crop(
    id_or_uid: str,
    crop_id: int,
    req: CropUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    farmer = get_authenticated_target_farmer(id_or_uid, db, current_user)

    crop = db.query(FarmerCrop).filter(
        FarmerCrop.id == crop_id,
        FarmerCrop.farmer_id == farmer.id
    ).first()

    if not crop:
        raise HTTPException(status_code=404, detail="Crop record not found for this farmer.")

    old_info = f"{crop.crop_name} - {crop.estimated_quantity_quintals} Q"

    if req.crop_name is not None and req.crop_name.strip():
        crop.crop_name = req.crop_name.strip()
    if req.season is not None and req.season.strip():
        crop.season = req.season.strip()
    if req.sowing_date is not None:
        crop.sowing_date = req.sowing_date
    if req.expected_harvest_date is not None:
        crop.expected_harvest_date = req.expected_harvest_date
    if req.estimated_quantity_quintals is not None:
        if req.estimated_quantity_quintals <= 0:
            raise HTTPException(status_code=400, detail="Estimated quantity must be greater than 0 Quintals.")
        crop.estimated_quantity_quintals = req.estimated_quantity_quintals

    audit = AuditLog(
        user_id=current_user.user_id if current_user else farmer.user_id,
        action="FARMER_CROP_UPDATED",
        entity="FARMER_CROP",
        entity_id=str(crop.id),
        old_value=old_info,
        new_value=f"{crop.crop_name} - {crop.estimated_quantity_quintals} Q"
    )
    db.add(audit)
    db.commit()

    return {
        "message": f"Crop '{crop.crop_name}' updated successfully.",
        "crop": {
            "id": crop.id,
            "farmer_id": crop.farmer_id,
            "crop_name": crop.crop_name,
            "season": crop.season,
            "sowing_date": str(crop.sowing_date) if crop.sowing_date else None,
            "expected_harvest_date": str(crop.expected_harvest_date) if crop.expected_harvest_date else None,
            "estimated_quantity_quintals": float(crop.estimated_quantity_quintals)
        }
    }


@router.delete("/{id_or_uid}/crops/{crop_id}")
def delete_farmer_crop(
    id_or_uid: str,
    crop_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    farmer = get_authenticated_target_farmer(id_or_uid, db, current_user)

    crop = db.query(FarmerCrop).filter(
        FarmerCrop.id == crop_id,
        FarmerCrop.farmer_id == farmer.id
    ).first()

    if not crop:
        raise HTTPException(status_code=404, detail="Crop record not found for this farmer.")

    crop_name = crop.crop_name
    db.delete(crop)

    audit = AuditLog(
        user_id=current_user.user_id if current_user else farmer.user_id,
        action="FARMER_CROP_DELETED",
        entity="FARMER_CROP",
        entity_id=str(crop_id),
        old_value=crop_name,
        new_value=None
    )
    db.add(audit)
    db.commit()

    return {"message": f"Crop '{crop_name}' removed successfully."}


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
