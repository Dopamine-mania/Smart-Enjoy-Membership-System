"""Pydantic schemas for API requests and responses."""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
from app.models.user import MemberLevel, Gender


class VerificationCodeRequest(BaseModel):
    """Request to send verification code."""
    email: EmailStr
    purpose: str = Field(..., pattern="^(register|login)$")


class RegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    code: str = Field(..., pattern=r"^\d{6}$")
    nickname: Optional[str] = Field(None, max_length=100)


class LoginRequest(BaseModel):
    """User login request."""
    email: EmailStr
    code: str = Field(..., pattern=r"^\d{6}$")


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserProfileResponse(BaseModel):
    """User profile response."""
    id: int
    email: str
    nickname: Optional[str]
    avatar_url: Optional[str]
    gender: Optional[Gender]
    birthday: Optional[str]
    id_card_last_four: Optional[str]
    member_level: MemberLevel
    available_points: int
    total_earned_points: int
    created_at: str

    class Config:
        from_attributes = True


class UpdateProfileRequest(BaseModel):
    """Update user profile request."""
    nickname: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = Field(None, max_length=500)
    gender: Optional[Gender] = None
    birthday: Optional[datetime] = None


class PointBalanceResponse(BaseModel):
    """Points balance response."""
    available_points: int
    total_earned_points: int


class PointTransactionResponse(BaseModel):
    """Point transaction response."""
    id: int
    transaction_type: str
    reason: str
    points: int
    balance_after: int
    description: Optional[str]
    created_at: str

    class Config:
        from_attributes = True
