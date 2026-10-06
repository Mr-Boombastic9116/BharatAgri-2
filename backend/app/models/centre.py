from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from backend.app.core.database import Base

class ProcurementCentre(Base):
    __tablename__ = "procurement_centres"
    id = Column(Integer, primary_key=True, index=True)
    centre_id = Column(String(50), unique=True, nullable=False, index=True)
    centre_name = Column(String(150), nullable=False)
    location = Column(String(255), nullable=False)
    state = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False, index=True)
    contact_number = Column(String(20), nullable=False)
    operating_days = Column(String(255), default="Monday,Tuesday,Wednesday,Thursday,Friday,Saturday")
    opening_time = Column(String(20), default="09:00 AM")
    closing_time = Column(String(20), default="05:00 PM")
    supported_crops = Column(String(255), default="Paddy,Wheat,Maize,Soybean,Cotton")
    max_daily_capacity_quintals = Column(Numeric(10, 2), default=800.00)
    total_storage_capacity_quintals = Column(Numeric(12, 2), default=15000.00)
    current_storage_usage_quintals = Column(Numeric(12, 2), default=3200.00)
    status = Column(String(20), default="OPERATIONAL")
    created_at = Column(DateTime, server_default=func.now())

    @property
    def total_capacity_quintals(self):
        return self.total_storage_capacity_quintals

class DailyCapacity(Base):
    __tablename__ = "daily_capacity"
    id = Column(Integer, primary_key=True, index=True)
    centre_id = Column(String(50), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    max_quintals_per_day = Column(Numeric(10, 2), nullable=False, default=800.00)

    @property
    def daily_capacity_quintals(self):
        return self.max_quintals_per_day

    __table_args__ = (UniqueConstraint("centre_id", "date", name="uq_centre_date_capacity"),)

# Alias for compatibility
CentreCapacity = DailyCapacity


class NonOperationalDate(Base):
    __tablename__ = "non_operational_dates"
    id = Column(Integer, primary_key=True, index=True)
    centre_id = Column(String(50), nullable=False, index=True)
    date = Column(Date, nullable=False)
    reason = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (UniqueConstraint("centre_id", "date", name="uq_centre_non_operational"),)

class Slot(Base):
    __tablename__ = "slots"
    id = Column(Integer, primary_key=True, index=True)
    centre_id = Column(String(50), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    start_time = Column(String(20), nullable=False)
    end_time = Column(String(20), nullable=False)
    max_capacity = Column(Integer, nullable=False, default=20)
