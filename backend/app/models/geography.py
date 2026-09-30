from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class State(Base):
    __tablename__ = "states"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    districts = relationship("District", back_populates="state", cascade="all, delete-orphan")

class District(Base):
    __tablename__ = "districts"
    id = Column(Integer, primary_key=True, index=True)
    state_id = Column(Integer, ForeignKey("states.id"), nullable=False)
    name = Column(String(100), nullable=False)
    state = relationship("State", back_populates="districts")
    blocks = relationship("Block", back_populates="district", cascade="all, delete-orphan")

class Block(Base):
    __tablename__ = "blocks"
    id = Column(Integer, primary_key=True, index=True)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=False)
    name = Column(String(100), nullable=False)
    district = relationship("District", back_populates="blocks")
    villages = relationship("Village", back_populates="block", cascade="all, delete-orphan")

class Village(Base):
    __tablename__ = "villages"
    id = Column(Integer, primary_key=True, index=True)
    block_id = Column(Integer, ForeignKey("blocks.id"), nullable=False)
    name = Column(String(100), nullable=False)
    block = relationship("Block", back_populates="villages")
