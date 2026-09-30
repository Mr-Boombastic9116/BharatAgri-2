from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.sql import func
from backend.app.core.database import Base

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255), nullable=True)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    email = Column(String(150), nullable=True)
    mobile = Column(String(20), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum('farmer', 'agent', 'centre', 'government'), nullable=False, index=True)
    preferred_language = Column(String(20), default="English")
    status = Column(String(20), default="ACTIVE", index=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __getitem__(self, key):
        return getattr(self, key)

    def get(self, key, default=None):
        return getattr(self, key, default)


