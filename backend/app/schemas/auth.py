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
    user_id: Optional[str] = None
    farmer_id: Optional[str] = None
    user_code: Optional[str] = None
    name: str
    mobile: str
    email: Optional[str] = None
    dob: Optional[str] = None
    password: str
    address: Optional[str] = None
    village: Optional[str] = "Main Village"
    taluka: Optional[str] = "Bicholim"
    district: Optional[str] = "North Goa"
    state: Optional[str] = "Goa"
    land_area: Optional[float] = 2.5
    preferred_language: Optional[str] = "English"
    bank_name: Optional[str] = "State Bank of India"
    bank_account_no: Optional[str] = None
    bank_ifsc: Optional[str] = "SBIN0001234"
    ekyc_status: Optional[str] = "VERIFIED"

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

class AgentRegisterRequest(BaseModel):
    name: str
    agent_code: Optional[str] = None
    user_id: Optional[str] = None
    organization_name: str = "Panchayat CSC Facilitation Centre"
    agency_type: Optional[str] = "CSC"
    mobile: str
    email: Optional[str] = None
    password: str
    state: Optional[str] = "Goa"
    district: Optional[str] = "North Goa"
    taluka: Optional[str] = "Bicholim"
    preferred_language: Optional[str] = "English"

class GovernmentRegisterRequest(BaseModel):
    name: str
    user_id: Optional[str] = None
    email: Optional[str] = None
    official_email: Optional[str] = None
    mobile: Optional[str] = "9876543210"
    password: str
    employee_id: Optional[str] = None
    designation: Optional[str] = "District Procurement Officer"
    department: Optional[str] = "Department of Food & Public Distribution"
    state: Optional[str] = "Goa"
    district: Optional[str] = "North Goa"
    preferred_language: Optional[str] = "English"

