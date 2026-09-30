from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.core.database import Base

class Agent(Base):
    __tablename__ = "agents"
    id = Column(Integer, primary_key=True, index=True)
    agent_code = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(String(100), unique=True, nullable=False, index=True)
    agency_type = Column(String(50), default="CSC")
    organization_name = Column(String(150), nullable=False)
    name = Column(String(150), nullable=False)
    mobile = Column(String(20), nullable=False)
    email = Column(String(150), nullable=True)
    state = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    taluka = Column(String(100), nullable=False)
    status = Column(String(20), default="ACTIVE")
    created_at = Column(DateTime, server_default=func.now())

class AgentFarmerAssignment(Base):
    __tablename__ = "agent_farmer_assignments"
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    farmer_id = Column(Integer, ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False)
    assigned_at = Column(DateTime, server_default=func.now())

    __table_args__ = (UniqueConstraint("agent_id", "farmer_id", name="uq_agent_farmer"),)
