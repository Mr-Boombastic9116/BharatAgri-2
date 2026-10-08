from typing import Optional, List, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel

class CollectionCreate(BaseModel):
    booking_id: int
    collected_quantity: Optional[float] = None
    gross_weight_quintals: Optional[float] = None
    collected_bags: Optional[int] = None
    centre_id: Optional[str] = None
    farmer_id: Optional[str] = None
    truck_number: Optional[str] = None
    village_collected: Optional[str] = None
    collected_by: Optional[str] = "Procurement Staff"
    notes: Optional[str] = None

class QualityCheckCreate(BaseModel):
    collection_id: Optional[str] = None
    booking_id: Optional[int] = None
    moisture_content_pct: float
    foreign_matter_pct: float
    broken_grains_pct: Optional[float] = 0.0
    damaged_grains_pct: Optional[float] = 0.0
    quality_grade: Optional[str] = "Grade A"
    inspector_name: Optional[str] = "Inspector"
    passed: bool = True
    remarks: Optional[str] = None
    notes: Optional[str] = None

class WeighmentCreate(BaseModel):
    collection_id: Optional[str] = None
    quality_check_id: Optional[str] = None
    booking_id: Optional[int] = None
    gross_weight_quintals: float
    tare_weight_quintals: float
    weighbridge_id: Optional[str] = "WB-01"
    operator_name: Optional[str] = "Scale Operator"
    scale_operator_name: Optional[str] = None

class ProcureCreate(BaseModel):
    booking_id: Optional[int] = None
    collection_id: Optional[str] = None
    weighment_id: Optional[str] = None
    procured_quantity_quintals: Optional[float] = None
    msp_rate_per_quintal: Optional[float] = None
    rate_per_quintal_inr: Optional[float] = None
    bardan_bags_used: Optional[int] = 0
    procurement_officer: Optional[str] = "Procurement Officer"

class StorageLotCreate(BaseModel):
    procurement_id: str
    warehouse_name: str
    stack_number: str

class PaymentCreate(BaseModel):
    procurement_id: str
    payment_mode: Optional[str] = "DBT_NEFT"
    bank_ref_number: Optional[str] = None

class TraceabilityLotResponse(BaseModel):
    lot_id: str
    status: str
    crop: str
    quantity_quintals: float
    procurement_id: str
    booking_id: int
    appointment_id: str
    farmer_id: str
    farmer_name: str
    farmer_mobile: str
    centre_id: str
    centre_name: str
    collection_id: str
    collection_date: date
    truck_number: Optional[str] = None
    quality_grade: str
    moisture_content_pct: float
    gross_weight_quintals: float
    tare_weight_quintals: float
    net_weight_quintals: float
    msp_rate_per_quintal: float
    total_procurement_value: float
    warehouse_name: str
    stack_number: str
    storage_date: date
    payment_status: str
    transaction_ref: Optional[str] = None
    paid_at: Optional[datetime] = None


class ProcessStepSubmit(BaseModel):
    step_number: int
    data: Dict[str, Any] = {}
    notes: Optional[str] = None


class ProcessStepCorrectionRequest(BaseModel):
    step_number: int
    field_name: str
    new_value: str
    correction_reason: str


class StorageCheckRequest(BaseModel):
    storage_employee_id: Optional[str] = None
    storage_employee_name: Optional[str] = None
    received_quantity_quintals: float
    storage_condition: str = "Optimal Humidity & Temperature"
    physical_condition: str = "Intact - No Infestation / Good Stacking"
    remarks: Optional[str] = None
    evidence_url: Optional[str] = None
