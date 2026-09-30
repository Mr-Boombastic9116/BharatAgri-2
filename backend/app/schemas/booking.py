from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class BookingCreate(BaseModel):
    farmer_id: str
    centre_id: str
    slot_id: int
    crop: str
    quantity: float

class StatusUpdateRequest(BaseModel):
    status: str
    notes: Optional[str] = None

class BookingResponse(BaseModel):
    id: int
    appointment_id: str
    booking_id: Optional[str] = None
    farmer_id: str
    farmer_name: Optional[str] = None
    farmer_mobile: Optional[str] = None
    centre_id: str
    centre_name: Optional[str] = None
    location: Optional[str] = None
    crop: str
    quantity: float
    date: str
    start_time: str
    end_time: str
    time_slot: str
    status: str
    qr_token: str
    redirected_from_centre_id: Optional[str] = None
    redirection_reason: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

class VerifyQRRequest(BaseModel):
    qr_token: str
    centre_id: str
