from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class ComplaintCreate(BaseModel):
    centre_id: str
    category: str
    priority: Optional[str] = "MEDIUM"
    subject: str
    description: str

class ComplaintMessageCreate(BaseModel):
    message: str

class ComplaintStatusUpdate(BaseModel):
    status: str
    resolution: Optional[str] = None
