from sqlalchemy import Column, Integer, String, Numeric, DateTime, Enum, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.core.database import Base

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(String(50), unique=True, nullable=False, index=True)
    booking_id = Column(String(50), nullable=True)
    farmer_id = Column(String(100), nullable=False, index=True)
    centre_id = Column(String(50), nullable=False, index=True)
    slot_id = Column(Integer, ForeignKey("slots.id"), nullable=False)
    crop = Column(String(100), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    status = Column(
        String(50),
        nullable=False,
        default='CONFIRMED',
        index=True
    )
    qr_token = Column(String(100), unique=True, nullable=False, index=True)
    redirected_from_centre_id = Column(String(50), nullable=True)
    redirection_reason = Column(String(255), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    slot = relationship("Slot")
    status_history = relationship("BookingStatusHistory", back_populates="booking", cascade="all, delete-orphan")

class BookingStatusHistory(Base):
    __tablename__ = "booking_status_history"
    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False)
    old_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    changed_by = Column(String(100), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    booking = relationship("Booking", back_populates="status_history")

class QRCode(Base):
    __tablename__ = "qr_codes"
    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(100), nullable=False)
    qr_code_value = Column(String(150), unique=True, nullable=False, index=True)
    is_used = Column(Boolean, default=False)
    used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
