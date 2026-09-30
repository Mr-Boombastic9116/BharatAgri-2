from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, Enum, Text
from sqlalchemy.sql import func
from backend.app.core.database import Base

class SupplyForecast(Base):
    __tablename__ = "supply_forecasts"
    id = Column(Integer, primary_key=True, index=True)
    centre_id = Column(String(50), nullable=False, index=True)
    crop = Column(String(100), nullable=False)
    forecast_month = Column(Integer, nullable=False)
    forecast_year = Column(Integer, nullable=False)
    predicted_procurement_quantity = Column(Numeric(12, 2), nullable=False)
    predicted_arrivals = Column(Numeric(12, 2), nullable=False)
    predicted_collection = Column(Numeric(12, 2), nullable=False)
    confidence_score = Column(Numeric(5, 2), default=0.92)
    model_version = Column(String(50), default="xgboost_v1.0")
    created_at = Column(DateTime, server_default=func.now())

class CentreCongestion(Base):
    __tablename__ = "centre_congestions"
    id = Column(Integer, primary_key=True, index=True)
    centre_id = Column(String(50), nullable=False, index=True)
    calculation_date = Column(Date, nullable=False, index=True)
    predicted_arrivals = Column(Numeric(10, 2), nullable=False)
    existing_bookings_qty = Column(Numeric(10, 2), nullable=False)
    expected_collection_qty = Column(Numeric(10, 2), nullable=False)
    daily_capacity = Column(Numeric(10, 2), nullable=False)
    utilization_percent = Column(Numeric(5, 2), nullable=False)
    congestion_level = Column(Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL'), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class AnomalyRecord(Base):
    __tablename__ = "anomaly_records"
    id = Column(Integer, primary_key=True, index=True)
    anomaly_code = Column(String(50), unique=True, nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(100), nullable=False)
    centre_id = Column(String(50), nullable=False, index=True)
    anomaly_type = Column(String(100), nullable=False)
    anomaly_score = Column(Numeric(6, 4), nullable=False)
    risk_level = Column(Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL'), nullable=False, default="MEDIUM")
    reason = Column(Text, nullable=False)
    status = Column(Enum('OPEN', 'UNDER REVIEW', 'RESOLVED', 'DISMISSED'), nullable=False, default="OPEN", index=True)
    resolved_by = Column(String(100), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class AIModelMetric(Base):
    __tablename__ = "ai_model_metrics"
    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(100), nullable=False)
    model_type = Column(String(50), nullable=False)
    mae = Column(Numeric(8, 4), nullable=True)
    rmse = Column(Numeric(8, 4), nullable=True)
    r2_score = Column(Numeric(8, 4), nullable=True)
    precision_score = Column(Numeric(8, 4), nullable=True)
    recall_score = Column(Numeric(8, 4), nullable=True)
    f1_score = Column(Numeric(8, 4), nullable=True)
    evaluation_date = Column(DateTime, server_default=func.now())
    dataset_info = Column(String(255), default="Synthetic demonstration dataset (Seed 42)")
