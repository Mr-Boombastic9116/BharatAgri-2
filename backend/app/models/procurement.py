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

class ProcurementEvidence(Base):
    __tablename__ = "procurement_evidence"
    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True)
    procurement_id = Column(String(50), nullable=True)
    evidence_type = Column(Enum('QUALITY', 'WEIGHING', 'MOISTURE'), nullable=False, index=True)
    file_path = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    notes = Column(String(255), nullable=True)
    uploaded_by = Column(String(100), nullable=False)
    uploaded_at = Column(DateTime, server_default=func.now())

    booking = relationship("Booking")
