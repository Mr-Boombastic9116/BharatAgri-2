from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.core.database import Base

class Farmer(Base):
    __tablename__ = "farmers"
    id = Column(Integer, primary_key=True, index=True)
    farmer_code = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    mobile = Column(String(20), nullable=False, index=True)
    email = Column(String(150), nullable=True)
    dob = Column(Date, nullable=True)
    gender = Column(String(10), default="Male")
    address = Column(Text, nullable=True)
    state = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False, index=True)
    taluka = Column(String(100), nullable=False)
    village = Column(String(100), nullable=False)
    land_area_hectares = Column(Numeric(8, 2), nullable=False, default=2.50)
    land_acres = Column(Numeric(8, 2), nullable=True)
    primary_crop = Column(String(100), nullable=True)
    expected_quantity_quintals = Column(Numeric(10, 2), nullable=True)
    distance_to_nearest_centre_km = Column(Numeric(8, 2), nullable=True)
    preferred_language = Column(String(20), default="hi")
    mobile_verified = Column(Boolean, default=True)
    ekyc_status = Column(String(20), default="VERIFIED")
    aadhaar_masked = Column(String(20), default="XXXX-XXXX-1234")
    bank_name = Column(String(100), default="State Bank of India")
    bank_account_no = Column(String(50), default="10293847561")
    bank_ifsc = Column(String(20), default="SBIN0001234")
    created_at = Column(DateTime, server_default=func.now())

    crops = relationship("FarmerCrop", back_populates="farmer", cascade="all, delete-orphan")

class FarmerCrop(Base):
    __tablename__ = "farmer_crops"
    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False)
    crop_name = Column(String(100), nullable=False)
    season = Column(String(50), nullable=False)
    sowing_date = Column(Date, nullable=True)
    expected_harvest_date = Column(Date, nullable=True)
    estimated_quantity_quintals = Column(Numeric(10, 2), nullable=False)

    farmer = relationship("Farmer", back_populates="crops")
