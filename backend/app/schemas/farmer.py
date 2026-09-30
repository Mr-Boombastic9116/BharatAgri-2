from typing import Optional, List
from datetime import date
from pydantic import BaseModel

class CropInfo(BaseModel):
    id: Optional[int] = None
    crop_name: str
    season: str
    sowing_date: Optional[date] = None
    expected_harvest_date: Optional[date] = None
    estimated_quantity_quintals: float

class FarmerUpdate(BaseModel):
    name: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    land_area_hectares: Optional[float] = None
    bank_name: Optional[str] = None
    bank_account_no: Optional[str] = None
    bank_ifsc: Optional[str] = None

class FarmerResponse(BaseModel):
    id: int
    farmer_code: str
    user_id: str
    name: str
    mobile: str
    email: Optional[str] = None
    dob: Optional[date] = None
    address: Optional[str] = None
    state: str
    district: str
    taluka: str
    village: str
    land_area_hectares: float
    ekyc_status: str
    aadhaar_masked: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_no: Optional[str] = None
    bank_ifsc: Optional[str] = None
    crops: Optional[List[CropInfo]] = []
