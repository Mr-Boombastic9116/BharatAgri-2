from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.core.database import Base

class Truck(Base):
    __tablename__ = "trucks"
    id = Column(Integer, primary_key=True, index=True)
    truck_number = Column(String(50), unique=True, nullable=False, index=True)
    driver_name = Column(String(100), nullable=False)
    driver_phone = Column(String(20), nullable=False)
    capacity_quintals = Column(Numeric(10, 2), nullable=False)
    current_status = Column(String(50), default="AVAILABLE")
    assigned_centre_id = Column(String(50), nullable=False, index=True)
    is_available = Column(Boolean, default=True)

class TruckRequest(Base):
    __tablename__ = "truck_requests"
    id = Column(Integer, primary_key=True, index=True)
    request_code = Column(String(50), unique=True, nullable=False, index=True)
    centre_id = Column(String(50), nullable=False, index=True)
    required_date = Column(Date, nullable=False)
    required_capacity_quintals = Column(Numeric(10, 2), nullable=False)
    reason = Column(String(255), nullable=False)
    status = Column(String(50), default="PENDING")
    created_at = Column(DateTime, server_default=func.now())

class TruckAllocation(Base):
    __tablename__ = "truck_allocations"
    id = Column(Integer, primary_key=True, index=True)
    allocation_code = Column(String(50), unique=True, nullable=False, index=True)
    request_id = Column(Integer, nullable=True)
    truck_id = Column(Integer, ForeignKey("trucks.id", ondelete="CASCADE"), nullable=False)
    centre_id = Column(String(50), nullable=False, index=True)
    allocation_date = Column(Date, nullable=False)
    assigned_quantity_quintals = Column(Numeric(10, 2), nullable=False)
    status = Column(String(50), default="ALLOCATED")
    route_distance_km = Column(Numeric(6, 2), default=25.50)
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    truck = relationship("Truck")

class TruckCollectionRoute(Base):
    __tablename__ = "truck_collection_routes"
    id = Column(Integer, primary_key=True, index=True)
    allocation_id = Column(Integer, ForeignKey("truck_allocations.id", ondelete="CASCADE"), nullable=False)
    stop_sequence = Column(Integer, nullable=False)
    farmer_id = Column(String(100), nullable=False)
    village_name = Column(String(100), nullable=False)
    estimated_quantity_quintals = Column(Numeric(10, 2), nullable=False)
    visited = Column(Boolean, default=False)
    visited_at = Column(DateTime, nullable=True)
