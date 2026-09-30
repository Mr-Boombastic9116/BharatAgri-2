from typing import Optional
from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    user_id: str
    password: str
    role: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    user_id: str
    name: str
    email: Optional[str] = None
    mobile: str
    role: str
    preferred_language: Optional[str] = "English"
    status: str = "ACTIVE"

class LoginResponse(BaseModel):
    message: str
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class FarmerRegisterRequest(BaseModel):
    name: str
    mobile: str
    village: str
    user_id: str
    password: str
    preferred_language: Optional[str] = "English"
    land_area: Optional[float] = 2.5
    state: Optional[str] = "Goa"
    district: Optional[str] = "North Goa"
    taluka: Optional[str] = "Bicholim"

class CentreRegisterRequest(BaseModel):
    centre_name: str
    centre_id: str
    password: str
    location: Optional[str] = "Main Market Yard"
    contact_number: Optional[str] = "9876543210"
    operating_days: Optional[str] = "Monday,Tuesday,Wednesday,Thursday,Friday,Saturday"
    opening_time: Optional[str] = "09:00 AM"
    closing_time: Optional[str] = "05:00 PM"
    supported_crops: Optional[str] = "Paddy,Wheat,Maize,Cotton"
