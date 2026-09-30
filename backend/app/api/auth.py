from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.core.database import get_db
from backend.app.core.security import verify_password, get_password_hash, create_access_token
from backend.app.core.deps import get_current_user
from backend.app.schemas.auth import LoginRequest, LoginResponse, FarmerRegisterRequest, CentreRegisterRequest, UserResponse
from backend.app.models.user import User
from backend.app.models.farmer import Farmer, FarmerCrop
from backend.app.models.centre import ProcurementCentre
from backend.app.models.audit import AuditLog

router = APIRouter(prefix="", tags=["Authentication"])

@router.post("/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    if not req.user_id or not req.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide User ID and Password."
        )

    clean_uid = req.user_id.strip()
    query = db.query(User).filter(func.lower(User.user_id) == func.lower(clean_uid))

    if req.role:
        clean_role = req.role.strip().lower()
        # map common aliases: procurement_centre -> centre
        if clean_role in ["procurement_centre", "procurement centre"]:
            clean_role = "centre"
        query = query.filter(User.role == clean_role)

    user = query.first()

    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid User ID or Password for the selected role."
        )

    access_token = create_access_token(data={"sub": user.user_id, "role": user.role, "id": user.id})

    # Record Audit Log
    try:
        audit = AuditLog(
            user_id=user.user_id,
            action="LOGIN_SUCCESS",
            entity="USER",
            entity_id=user.user_id,
            old_value=None,
            new_value=f"Role: {user.role}, Status: {user.status}"
        )
        db.add(audit)
        db.commit()
    except Exception:
        db.rollback()

    user_dict = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "mobile": user.mobile,
        "user_id": user.user_id,
        "preferred_language": user.preferred_language or "English",
        "role": user.role,
        "status": user.status
    }

    return {
        "success": True,
        "message": "Login successful",
        "token": access_token,
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_dict
    }


@router.post("/farmers/register", status_code=status.HTTP_201_CREATED)
def register_farmer(req: FarmerRegisterRequest, db: Session = Depends(get_db)):
    clean_uid = req.user_id.strip()
    existing = db.query(User).filter(func.lower(User.user_id) == func.lower(clean_uid)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Farmer ID already exists. Please choose a different ID."
        )

    pw_hash = get_password_hash(req.password)

    new_user = User(
        user_id=clean_uid,
        name=req.name.strip(),
        mobile=req.mobile.strip(),
        password_hash=pw_hash,
        role="farmer",
        preferred_language=req.preferred_language or "English",
        status="ACTIVE"
    )
    db.add(new_user)
    db.flush()

    farmer_code = f"FRM-2026-{new_user.id:05d}"
    new_farmer = Farmer(
        farmer_code=farmer_code,
        user_id=clean_uid,
        name=req.name.strip(),
        mobile=req.mobile.strip(),
        village=req.village.strip(),
        taluka=req.taluka or req.village.strip(),
        district=req.district or "North Goa",
        state=req.state or "Goa",
        land_area_hectares=req.land_area or 2.5,
        ekyc_status="VERIFIED"
    )
    db.add(new_farmer)
    db.flush()

    # Add default crop
    new_crop = FarmerCrop(
        farmer_id=new_farmer.id,
        crop_name="Paddy",
        season="Kharif",
        estimated_quantity_quintals=50.0
    )
    db.add(new_crop)

    audit = AuditLog(
        user_id=clean_uid,
        action="FARMER_REGISTERED",
        entity="FARMER",
        entity_id=farmer_code,
        new_value=f"Name: {req.name}, Mobile: {req.mobile}"
    )
    db.add(audit)
    db.commit()

    return {
        "message": "Farmer registered successfully",
        "user": {
            "name": new_user.name,
            "mobile": new_user.mobile,
            "village": new_farmer.village,
            "user_id": new_user.user_id,
            "preferred_language": new_user.preferred_language,
            "role": "farmer"
        }
    }

@router.post("/centres/register", status_code=status.HTTP_201_CREATED)
def register_centre(req: CentreRegisterRequest, db: Session = Depends(get_db)):
    clean_id = req.centre_id.strip()
    existing = db.query(User).filter(func.lower(User.user_id) == func.lower(clean_id)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Centre ID is already registered."
        )

    pw_hash = get_password_hash(req.password)

    new_user = User(
        user_id=clean_id,
        name=req.centre_name.strip(),
        mobile=req.contact_number or "9876543210",
        password_hash=pw_hash,
        role="centre",
        status="ACTIVE"
    )
    db.add(new_user)
    db.flush()

    new_centre = ProcurementCentre(
        centre_id=clean_id,
        centre_name=req.centre_name.strip(),
        location=req.location or "Main Market Yard",
        contact_number=req.contact_number or "9876543210",
        state="Goa",
        district="North Goa",
        operating_days=req.operating_days or "Monday,Tuesday,Wednesday,Thursday,Friday,Saturday",
        opening_time=req.opening_time or "09:00 AM",
        closing_time=req.closing_time or "05:00 PM",
        supported_crops=req.supported_crops or "Paddy,Wheat,Maize,Cotton",
        max_daily_capacity_quintals=800.0,
        status="OPERATIONAL"
    )
    db.add(new_centre)

    audit = AuditLog(
        user_id=clean_id,
        action="CENTRE_REGISTERED",
        entity="PROCUREMENT_CENTRE",
        entity_id=clean_id,
        new_value=f"Name: {req.centre_name}"
    )
    db.add(audit)
    db.commit()

    return {
        "message": "Procurement Centre registered successfully",
        "user": {
            "name": new_centre.centre_name,
            "user_id": new_centre.centre_id,
            "location": new_centre.location,
            "contact_number": new_centre.contact_number,
            "operating_days": new_centre.operating_days,
            "opening_time": new_centre.opening_time,
            "closing_time": new_centre.closing_time,
            "supported_crops": new_centre.supported_crops,
            "role": "centre"
        }
    }

@router.get("/auth/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "user_id": current_user.user_id,
        "name": current_user.name,
        "email": current_user.email,
        "mobile": current_user.mobile,
        "role": current_user.role,
        "preferred_language": current_user.preferred_language,
        "status": current_user.status
    }
