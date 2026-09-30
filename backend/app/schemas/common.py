from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel

T = TypeVar("T")

class StandardResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None

class ErrorDetail(BaseModel):
    code: str
    message: str

class StandardErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
