from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.core.database import Base

class CollectionRecord(Base):
    __tablename__ = "collection_records"
    id = Column(Integer, primary_key=True, index=True)
    collection_id = Column(String(50), unique=True, nullable=False, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False)
    farmer_id = Column(String(100), nullable=False)
    centre_id = Column(String(50), nullable=False)
    crop = Column(String(100), nullable=False)
    collected_quantity = Column(Numeric(10, 2), nullable=False)
    collection_date = Column(Date, nullable=False)
    collection_method = Column(String(50), default="DIRECT_CENTRE")
    truck_number = Column(String(50), nullable=True)
    collected_by = Column(String(100), nullable=False)
    status = Column(String(50), default="COLLECTED")
    created_at = Column(DateTime, server_default=func.now())

    booking = relationship("Booking")
    quality_check = relationship("QualityCheck", back_populates="collection", uselist=False)
    weighment = relationship("Weighment", back_populates="collection", uselist=False)

class QualityCheck(Base):
    __tablename__ = "quality_checks"
    id = Column(Integer, primary_key=True, index=True)
    check_id = Column(String(50), unique=True, nullable=False, index=True)
    collection_id = Column(String(50), ForeignKey("collection_records.collection_id", ondelete="CASCADE"), nullable=False)
    moisture_content_pct = Column(Numeric(5, 2), nullable=False)
    foreign_matter_pct = Column(Numeric(5, 2), nullable=False)
    broken_grains_pct = Column(Numeric(5, 2), nullable=False)
    quality_grade = Column(String(20), nullable=False, default="GRADE_A")
    inspector_name = Column(String(100), nullable=False)
    passed = Column(Boolean, nullable=False, default=True)
    remarks = Column(Text, nullable=True)
    checked_at = Column(DateTime, server_default=func.now())

    collection = relationship("CollectionRecord", back_populates="quality_check")

class Weighment(Base):
    __tablename__ = "weighments"
    id = Column(Integer, primary_key=True, index=True)
    weighment_id = Column(String(50), unique=True, nullable=False, index=True)
    collection_id = Column(String(50), ForeignKey("collection_records.collection_id", ondelete="CASCADE"), nullable=False)
    gross_weight_quintals = Column(Numeric(10, 2), nullable=False)
    tare_weight_quintals = Column(Numeric(10, 2), nullable=False)
    net_weight_quintals = Column(Numeric(10, 2), nullable=False)
    weighbridge_id = Column(String(50), default="WB-01")
    operator_name = Column(String(100), nullable=False)
    weighed_at = Column(DateTime, server_default=func.now())

    collection = relationship("CollectionRecord", back_populates="weighment")

class ProcurementRecord(Base):
    __tablename__ = "procurement_records"
    id = Column(Integer, primary_key=True, index=True)
    procurement_id = Column(String(50), unique=True, nullable=False, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False)
    collection_id = Column(String(50), ForeignKey("collection_records.collection_id", ondelete="CASCADE"), nullable=False)
    farmer_id = Column(String(100), nullable=False, index=True)
    centre_id = Column(String(50), nullable=False, index=True)
    crop = Column(String(100), nullable=False)
    quality_grade = Column(String(20), default="GRADE_A")
    moisture_content_pct = Column(Numeric(5, 2), default=12.50)
    procured_quantity_quintals = Column(Numeric(10, 2), nullable=False)
    msp_rate_per_quintal = Column(Numeric(10, 2), nullable=False)
    total_procurement_value = Column(Numeric(12, 2), nullable=False)
    status = Column(String(50), default="CONFIRMED")
    warehouse_location = Column(String(150), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    @property
    def procurement_date(self):
        return self.created_at.date() if self.created_at else None

    booking = relationship("Booking")
    collection = relationship("CollectionRecord")
    storage_lot = relationship("StorageLot", back_populates="procurement", uselist=False)
    payment = relationship("Payment", back_populates="procurement", uselist=False)

class StorageLot(Base):
    __tablename__ = "storage_lots"
    id = Column(Integer, primary_key=True, index=True)
    lot_id = Column(String(60), unique=True, nullable=False, index=True)
    procurement_id = Column(String(50), ForeignKey("procurement_records.procurement_id", ondelete="CASCADE"), nullable=False)
    centre_id = Column(String(50), nullable=False, index=True)
    crop = Column(String(100), nullable=False)
    quantity_quintals = Column(Numeric(10, 2), nullable=False)
    warehouse_name = Column(String(150), nullable=False)
    stack_number = Column(String(50), nullable=False)
    storage_date = Column(Date, nullable=False)
    status = Column(String(50), default="STORED")
    storage_employee = Column(String(150), nullable=True)
    storage_condition = Column(String(100), nullable=True)
    physical_condition = Column(String(100), nullable=True)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    procurement = relationship("ProcurementRecord", back_populates="storage_lot")

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(String(50), unique=True, nullable=False, index=True)
    procurement_id = Column(String(50), ForeignKey("procurement_records.procurement_id", ondelete="CASCADE"), nullable=False)
    farmer_id = Column(String(100), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    msp_rate = Column(Numeric(10, 2), nullable=False)
    quantity_quintals = Column(Numeric(10, 2), nullable=False)
    payment_mode = Column(String(50), default="DBT_NEFT")
    payment_status = Column(Enum('PENDING', 'INITIATED', 'PAID', 'FAILED'), nullable=False, default="INITIATED")
    transaction_ref = Column(String(100), nullable=True)
    initiated_at = Column(DateTime, server_default=func.now())
    paid_at = Column(DateTime, nullable=True)
    remarks = Column(String(255), nullable=True)

    procurement = relationship("ProcurementRecord", back_populates="payment")

    @property
    def status(self):
        return self.payment_status

    @property
    def amount_paid(self):
        return float(self.amount) if self.amount else 0.0

    @property
    def payment_amount(self):
        return float(self.amount) if self.amount else 0.0

    @property
    def transaction_reference(self):
        return self.transaction_ref

    @property
    def payment_reference(self):
        return self.transaction_ref

    @property
    def payment_date(self):
        return self.paid_at or self.initiated_at

    @property
    def created_at(self):
        return self.initiated_at


class ProcurementEvidence(Base):
    __tablename__ = "procurement_evidence"
    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=True, index=True)
    appointment_id = Column(String(50), nullable=True, index=True)
    procurement_id = Column(String(50), nullable=True)
    process_step = Column(String(50), nullable=True, index=True)
    evidence_type = Column(String(50), nullable=False, index=True)
    file_path = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=True, default="")
    file_size_bytes = Column(Integer, nullable=True, default=0)
    mime_type = Column(String(100), nullable=True, default="image/jpeg")
    notes = Column(Text, nullable=True)
    uploaded_by = Column(String(100), nullable=False)
    uploaded_at = Column(DateTime, server_default=func.now())

    booking = relationship("Booking")


class ProcurementProcessStep(Base):
    __tablename__ = "procurement_process_steps"
    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True)
    appointment_id = Column(String(50), nullable=False, index=True)
    step_number = Column(Integer, nullable=False, index=True)
    step_type = Column(String(50), nullable=False)
    status = Column(Enum('PENDING', 'IN_PROGRESS', 'COMPLETED', 'CORRECTED', 'SKIPPED'), nullable=False, default="PENDING")
    completed_by = Column(String(100), nullable=True)
    employee_name = Column(String(150), nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    booking = relationship("Booking")


class AIQualityInspection(Base):
    __tablename__ = "ai_quality_inspections"
    id = Column(Integer, primary_key=True, index=True)
    inspection_code = Column(String(50), unique=True, nullable=False, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True)
    appointment_id = Column(String(50), nullable=False, index=True)
    centre_id = Column(String(50), nullable=False, index=True)
    crop = Column(String(100), nullable=False, default="Mango")
    image_path = Column(String(255), nullable=False)
    annotated_image_path = Column(String(255), nullable=True)
    model_version = Column(String(50), nullable=False, default="mango-quality-v1")
    model_type = Column(String(100), nullable=False, default="SVM+KNN Fusion CIELAB")
    sample_count = Column(Integer, nullable=False, default=0)
    healthy_count = Column(Integer, nullable=False, default=0)
    defect_count = Column(Integer, nullable=False, default=0)
    anthracnose_count = Column(Integer, nullable=False, default=0)
    scab_count = Column(Integer, nullable=False, default=0)
    bacterial_canker_count = Column(Integer, nullable=False, default=0)
    stem_end_rot_count = Column(Integer, nullable=False, default=0)
    other_count = Column(Integer, nullable=False, default=0)
    ripe_count = Column(Integer, nullable=False, default=0)
    nearly_ripe_count = Column(Integer, nullable=False, default=0)
    not_ripe_count = Column(Integer, nullable=False, default=0)
    uncertain_count = Column(Integer, nullable=False, default=0)
    affected_percentage = Column(Numeric(5, 2), nullable=False, default=0.00)
    visual_grade = Column(String(50), nullable=False, default="Grade A")
    confidence = Column(Numeric(5, 2), nullable=False, default=0.00)
    status = Column(Enum('COMPLETED', 'NEEDS_REVIEW', 'MANUALLY_OVERRIDDEN'), nullable=False, default="COMPLETED")
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    booking = relationship("Booking")
    detections = relationship("AIInspectionDetection", back_populates="inspection", cascade="all, delete-orphan")


class AIInspectionDetection(Base):
    __tablename__ = "ai_inspection_detections"
    id = Column(Integer, primary_key=True, index=True)
    inspection_id = Column(Integer, ForeignKey("ai_quality_inspections.id", ondelete="CASCADE"), nullable=False, index=True)
    sample_index = Column(Integer, nullable=False)
    predicted_class = Column(String(50), nullable=False)
    ripeness = Column(String(50), nullable=False, default="Uncertain")
    confidence = Column(Numeric(5, 2), nullable=False, default=0.00)
    box_x = Column(Integer, nullable=False, default=0)
    box_y = Column(Integer, nullable=False, default=0)
    box_w = Column(Integer, nullable=False, default=0)
    box_h = Column(Integer, nullable=False, default=0)
    crop_image_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    inspection = relationship("AIQualityInspection", back_populates="detections")


class ProcessStepCorrection(Base):
    __tablename__ = "process_step_corrections"
    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True)
    appointment_id = Column(String(50), nullable=False)
    step_number = Column(Integer, nullable=False)
    field_name = Column(String(100), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=False)
    correction_reason = Column(Text, nullable=False)
    corrected_by = Column(String(100), nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class ProcessAuditLog(Base):
    __tablename__ = "process_audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    centre_id = Column(String(50), nullable=False, index=True)
    appointment_id = Column(String(50), nullable=False, index=True)
    process_step = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False)
    record_id = Column(String(100), nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    correction_reason = Column(Text, nullable=True)
    ip_address = Column(String(50), default="127.0.0.1")
    created_at = Column(DateTime, server_default=func.now())

