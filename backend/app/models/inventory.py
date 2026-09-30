from sqlalchemy import Column, Integer, String, Date, DateTime, Enum, Text, UniqueConstraint
from sqlalchemy.sql import func
from backend.app.core.database import Base

class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(Integer, primary_key=True, index=True)
    centre_id = Column(String(50), nullable=False, index=True)
    item_type = Column(String(50), nullable=False)
    item_name = Column(String(100), nullable=False)
    current_stock = Column(Integer, nullable=False)
    reserved_stock = Column(Integer, nullable=False, default=0)
    unit = Column(String(20), nullable=False, default="Pieces")
    reorder_level = Column(Integer, nullable=False, default=500)
    last_restocked_at = Column(DateTime, server_default=func.now())

    __table_args__ = (UniqueConstraint("centre_id", "item_type", "item_name", name="uq_centre_inventory"),)

class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"
    id = Column(Integer, primary_key=True, index=True)
    centre_id = Column(String(50), nullable=False, index=True)
    item_type = Column(String(50), nullable=False)
    transaction_type = Column(Enum('STOCK_IN', 'CONSUMED', 'DAMAGED', 'RETURNED'), nullable=False)
    quantity = Column(Integer, nullable=False)
    reference_id = Column(String(100), nullable=True)
    reference_type = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(String(100), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class BardanStock(Base):
    __tablename__ = "bardan_stock"
    id = Column(Integer, primary_key=True, index=True)
    centre_id = Column(String(50), unique=True, nullable=False, index=True)
    total_bags = Column(Integer, nullable=False, default=25000)
    bags_in_use = Column(Integer, nullable=False, default=6500)
    bags_damaged = Column(Integer, nullable=False, default=200)
    available_bags = Column(Integer, nullable=False, default=18300)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class BardanForecast(Base):
    __tablename__ = "bardan_forecasts"
    id = Column(Integer, primary_key=True, index=True)
    centre_id = Column(String(50), nullable=False, index=True)
    forecast_date = Column(Date, nullable=False)
    current_stock = Column(Integer, nullable=False)
    projected_consumption = Column(Integer, nullable=False)
    projected_requirement = Column(Integer, nullable=False)
    expected_shortage = Column(Integer, nullable=False, default=0)
    status = Column(Enum('SAFE', 'LOW', 'WARNING', 'SHORTAGE'), nullable=False, default="SAFE")
    created_at = Column(DateTime, server_default=func.now())
