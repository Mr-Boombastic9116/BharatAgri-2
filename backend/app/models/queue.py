from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.sql import func
from backend.app.core.database import Base

class QueueEvent(Base):
    __tablename__ = "queue_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(50), unique=True, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    centre_id = Column(String(50), nullable=False, index=True)
    queue_length = Column(Integer, nullable=False, default=0)
    farmers_in_service = Column(Integer, nullable=False, default=0)
    active_stations = Column(Integer, nullable=False, default=1)
    processing_rate_farmers_per_hour = Column(Numeric(6, 2), nullable=False, default=3.50)
    avg_processing_time_min = Column(Numeric(6, 2), nullable=False, default=17.00)
    equipment_failure_flag = Column(Integer, nullable=False, default=0)
    weather_delay_flag = Column(Integer, nullable=False, default=0)
    estimated_wait_min = Column(Numeric(6, 2), nullable=False, default=25.00)
    created_at = Column(DateTime, server_default=func.now())


class CentreDailyMetric(Base):
    __tablename__ = "centre_daily_metrics"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    centre_id = Column(String(50), nullable=False, index=True)
    capacity_farmers = Column(Integer, nullable=False, default=120)
    arrivals = Column(Integer, nullable=False, default=0)
    processed = Column(Integer, nullable=False, default=0)
    no_shows = Column(Integer, nullable=False, default=0)
    avg_wait_min = Column(Numeric(6, 2), nullable=False, default=45.00)
    peak_queue = Column(Integer, nullable=False, default=0)
    equipment_downtime_min = Column(Integer, nullable=False, default=0)
    congestion_score = Column(Numeric(6, 3), nullable=False, default=0.500)
    high_congestion_flag = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, server_default=func.now())


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    notification_id = Column(String(50), unique=True, nullable=False, index=True)
    farmer_id = Column(String(50), nullable=False, index=True)
    notification_type = Column(String(50), nullable=False, default="QUEUE_UPDATE")
    channel = Column(String(50), nullable=False, default="APP_PUSH")
    message = Column(Text, nullable=True)
    sent_at = Column(DateTime, nullable=False, index=True)
    delivery_status = Column(String(50), nullable=False, default="DELIVERED")
    response = Column(String(50), nullable=True, default="PENDING")
    created_at = Column(DateTime, server_default=func.now())


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(String(50), unique=True, nullable=False, index=True)
    farmer_id = Column(String(50), nullable=False, index=True)
    centre_id = Column(String(50), nullable=False, index=True)
    appointment_date = Column(Date, nullable=False, index=True)
    slot_start = Column(DateTime, nullable=False, index=True)
    slot_duration_min = Column(Integer, nullable=False, default=30)
    queue_before = Column(Integer, nullable=False, default=0)
    active_weighing_machines = Column(Integer, nullable=False, default=2)
    staff_available = Column(Integer, nullable=False, default=8)
    equipment_failure_flag = Column(Integer, nullable=False, default=0)
    weather_delay_flag = Column(Integer, nullable=False, default=0)
    travel_distance_km = Column(Numeric(6, 2), nullable=False, default=15.00)
    historical_avg_processing_min = Column(Numeric(6, 2), nullable=False, default=16.00)
    predicted_wait_min = Column(Numeric(6, 2), nullable=False, default=35.00)
    actual_wait_min = Column(Numeric(6, 2), nullable=True)
    no_show = Column(Integer, nullable=False, default=0)
    status = Column(String(50), nullable=False, default="BOOKED", index=True)
    crop = Column(String(100), nullable=True)
    quantity_quintals = Column(Numeric(10, 2), nullable=True)
    token_number = Column(String(20), nullable=True, index=True)
    qr_token = Column(String(100), nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now())


class ProcurementTransaction(Base):
    __tablename__ = "procurement_transactions"

    id = Column(Integer, primary_key=True, index=True)
    procurement_id = Column(String(50), unique=True, nullable=False, index=True)
    appointment_id = Column(String(50), nullable=False, index=True)
    farmer_id = Column(String(50), nullable=False, index=True)
    centre_id = Column(String(50), nullable=False, index=True)
    crop = Column(String(100), nullable=False, index=True)
    quantity_quintals = Column(Numeric(10, 2), nullable=False)
    quality_score = Column(Numeric(5, 2), nullable=False, default=85.00)
    procurement_rate_rs_per_quintal = Column(Numeric(10, 2), nullable=False)
    gross_amount_rs = Column(Numeric(12, 2), nullable=False)
    procurement_timestamp = Column(DateTime, nullable=False, index=True)
    payment_status = Column(String(50), nullable=False, default="PENDING", index=True)
    dbt_reference = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
