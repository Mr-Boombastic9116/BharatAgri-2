from typing import Optional, List, Union
from datetime import date
from pydantic import BaseModel

class NonOperationalException(BaseModel):
    id: Optional[int] = None
    date: str
    reason: str

class OperatingConfigResponse(BaseModel):
    centre_id: str
    operating_days: str
    opening_time: str
    closing_time: str
    non_operational_dates: List[NonOperationalException]

class OperatingDaysUpdate(BaseModel):
    operating_days: Union[str, List[str]]

class OperatingConfigUpdate(BaseModel):
    operating_days: Optional[Union[str, List[str]]] = None
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None
    supported_crops: Optional[Union[str, List[str]]] = None
    max_daily_capacity_quintals: Optional[float] = None

class NonOperationalDateCreate(BaseModel):
    date: str
    reason: Optional[str] = "Non-operational date"

class DailyCapacityUpdate(BaseModel):
    centre_id: str
    date: str
    max_quintals_per_day: float

class SlotCreate(BaseModel):
    centre_id: str
    date: str
    start_time: str
    end_time: str
    max_capacity: int = 20

class SlotUpdate(BaseModel):
    max_capacity: int

class SlotResponse(BaseModel):
    id: int
    centre_id: str
    date: str
    start_time: str
    end_time: str
    max_capacity: int
    booked_count: int
    remaining_capacity: int
    status_label: str
    is_full: bool

class SlotRangeItem(BaseModel):
    start_time: str
    end_time: str
    max_capacity: int = 20

class ApplyScheduleRangeRequest(BaseModel):
    centre_id: str
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    max_quintals_per_day: Optional[float] = 800.0
    time_slots: List[SlotRangeItem]
