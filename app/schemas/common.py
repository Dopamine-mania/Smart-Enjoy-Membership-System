"""Common response schemas."""
from pydantic import BaseModel
from typing import Optional


class ErrorResponse(BaseModel):
    """Error response."""
    code: str
    message: str
    trace_id: str
    details: Optional[str] = None


class SuccessResponse(BaseModel):
    """Success response."""
    message: str
    data: Optional[dict] = None
