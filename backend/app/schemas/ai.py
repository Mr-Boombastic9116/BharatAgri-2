from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class SupplyForecastRequest(BaseModel):
    centre_id: str
    crop: str
    month: Optional[int] = 10
    day_of_week: Optional[int] = 2
    booked_quantity: float
    state: Optional[str] = "Goa"
    district: Optional[str] = "North Goa"
    registered_farmers: Optional[int] = 150
    daily_capacity: Optional[float] = 800.0

class AnomalyStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None
    resolution_notes: Optional[str] = None

class TruckOptimizationRequest(BaseModel):
    centre_id: str
    requests: Optional[List[Dict[str, Any]]] = None
