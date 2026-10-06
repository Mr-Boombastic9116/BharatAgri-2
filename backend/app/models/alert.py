from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, Boolean
from sqlalchemy.sql import func
from backend.app.core.database import Base

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_code = Column(String(50), unique=True, nullable=False, index=True)
    scope = Column(Enum('CENTRE', 'GOVERNMENT'), nullable=False, index=True)
    centre_id = Column(String(50), nullable=True, index=True)
    state = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)
    alert_type = Column(String(100), nullable=False)
    severity = Column(Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL'), nullable=False, index=True)
    what = Column(Text, nullable=False)
    where_location = Column(String(255), nullable=False)
    when_timestamp = Column(DateTime, nullable=False)
    why = Column(Text, nullable=False)
    recommended_action = Column(Text, nullable=False)
    is_resolved = Column(Boolean, default=False, index=True)
    resolved_by = Column(String(100), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    @property
    def title(self):
        return self.what

    @property
    def what_happened(self):
        return self.what

    @property
    def why_reason(self):
        return self.why

    @property
    def where(self):
        return self.where_location

