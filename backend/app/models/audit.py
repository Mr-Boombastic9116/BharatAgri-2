from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from backend.app.core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    action = Column(String(100), nullable=False)
    entity = Column(String(100), nullable=False)
    entity_id = Column(String(100), nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    ip_address = Column(String(50), default="127.0.0.1")
    created_at = Column(DateTime, server_default=func.now())
