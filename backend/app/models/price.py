from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, Text
from sqlalchemy.sql import func
from backend.app.core.database import Base

class MspPrice(Base):
    __tablename__ = "msp_prices"

    id = Column(Integer, primary_key=True, index=True)
    crop = Column(String(100), nullable=False, index=True)
    crop_variant = Column(String(100), default="Standard")
    marketing_season = Column(String(50), nullable=False)
    season_year = Column(String(20), nullable=False)
    official_msp_per_quintal = Column(Numeric(10, 2), nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=False)
    source = Column(String(150), default="Ministry of Agriculture & Farmers Welfare, Govt of India")
    source_reference = Column(String(150), default="CACP Price Policy Kharif/Rabi Notification")
    created_at = Column(DateTime, server_default=func.now())


class StateCropSupplyDemand(Base):
    __tablename__ = "state_crop_supply_demand"

    id = Column(Integer, primary_key=True, index=True)
    state = Column(String(100), nullable=False, index=True)
    crop = Column(String(100), nullable=False, index=True)
    season = Column(String(50), nullable=False, default="Kharif 2026")
    official_msp = Column(Numeric(10, 2), nullable=False)
    expected_supply_quintals = Column(Numeric(12, 2), nullable=False)
    current_procurement_quintals = Column(Numeric(12, 2), nullable=False)
    projected_procurement_quintals = Column(Numeric(12, 2), nullable=False)
    current_inventory_quintals = Column(Numeric(12, 2), nullable=False)
    available_storage_quintals = Column(Numeric(12, 2), nullable=False)
    expected_demand_quintals = Column(Numeric(12, 2), nullable=False)
    surplus_deficit_quintals = Column(Numeric(12, 2), nullable=False)
    market_sentiment = Column(String(20), default="BALANCED")
    estimated_procurement_price = Column(Numeric(10, 2), nullable=False)
    price_explanation = Column(Text, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class PriceEstimate(Base):
    __tablename__ = "price_estimates"

    id = Column(Integer, primary_key=True, index=True)
    crop = Column(String(100), nullable=False, index=True)
    state = Column(String(100), nullable=True, index=True)
    centre_id = Column(String(50), nullable=True)
    quantity_quintals = Column(Numeric(10, 2), nullable=False)
    official_msp_per_quintal = Column(Numeric(10, 2), nullable=False)
    estimated_price_per_quintal = Column(Numeric(10, 2), nullable=False)
    estimated_total_value = Column(Numeric(14, 2), nullable=False)
    supply_status = Column(String(20), default="BALANCED")
    confidence = Column(Numeric(5, 2), nullable=True)
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
