"""Admin schemas."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List


class AdminLoginRequest(BaseModel):
    """Admin login request."""
    username: str
    password: str


class AdminUserResponse(BaseModel):
    """Admin user response."""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


class AdjustPointsRequest(BaseModel):
    """Adjust points request."""
    user_id: int
    points: int = Field(..., description="Positive for add, negative for deduct")
    reason: str = Field(..., max_length=500)


class UpdateUserRequest(BaseModel):
    """Update user request (admin)."""
    nickname: Optional[str] = Field(None, max_length=100)
    member_level: Optional[str] = None
    is_locked: Optional[bool] = None
    locked_reason: Optional[str] = Field(None, max_length=500)


class AuditLogResponse(BaseModel):
    """Audit log response."""
    id: int
    admin_user_id: int
    admin_username: str
    action: str
    resource: str
    resource_id: Optional[str]
    details: Optional[str]
    ip_address: Optional[str]
    trace_id: Optional[str]
    created_at: str

    class Config:
        from_attributes = True
