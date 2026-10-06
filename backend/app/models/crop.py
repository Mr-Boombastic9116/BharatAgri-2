from sqlalchemy import Column, Integer, String, Numeric, DateTime, Boolean, Enum
from sqlalchemy.sql import func
from backend.app.core.database import Base

class CropMetadata(Base):
    __tablename__ = "crop_metadata"

    id = Column(Integer, primary_key=True, index=True)
    crop_name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(50), nullable=False)
    season = Column(String(50), nullable=False, index=True)
    is_perishable = Column(Boolean, nullable=False, default=False, index=True)
    shelf_life_days = Column(Integer, nullable=False)
    urgency_level = Column(Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL'), nullable=False, default="LOW")
    perishability_score = Column(Numeric(4, 2), nullable=False, default=0.20)
    storage_requirements = Column(String(255), nullable=False)
    demand_patterns = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    @property
    def crop_category(self):
        return self.category

    @property
    def approx_shelf_life_days(self):
        return self.shelf_life_days

    @property
    def storage_type(self):
        return self.storage_requirements

    @property
    def demand_level(self):
        if self.urgency_level in ['HIGH', 'CRITICAL']:
            return "HIGH"
        if "HIGH" in str(self.demand_patterns).upper():
            return "HIGH"
        return "MEDIUM"

