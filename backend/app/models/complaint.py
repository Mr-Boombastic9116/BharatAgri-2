from sqlalchemy import Column, Integer, String, DateTime, Text, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.core.database import Base

class Complaint(Base):
    __tablename__ = "complaints"
    id = Column(Integer, primary_key=True, index=True)
    complaint_code = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(String(100), nullable=False)
    user_role = Column(String(50), nullable=False)
    centre_id = Column(String(50), nullable=False, index=True)
    category = Column(String(100), nullable=False)
    priority = Column(Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL'), nullable=False, default="MEDIUM")
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(Enum('OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED', 'REJECTED'), nullable=False, default="OPEN", index=True)
    resolution = Column(Text, nullable=True)
    assigned_to = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    resolved_at = Column(DateTime, nullable=True)

    messages = relationship("ComplaintMessage", back_populates="complaint", cascade="all, delete-orphan")
    status_history = relationship("ComplaintStatusHistory", back_populates="complaint", cascade="all, delete-orphan")

class ComplaintMessage(Base):
    __tablename__ = "complaint_messages"
    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(String(100), nullable=False)
    sender_role = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    complaint = relationship("Complaint", back_populates="messages")

class ComplaintStatusHistory(Base):
    __tablename__ = "complaint_status_history"
    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False)
    old_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    changed_by = Column(String(100), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    complaint = relationship("Complaint", back_populates="status_history")
