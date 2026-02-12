"""Benefit schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from app.models.benefit import BenefitType
from app.models.user import MemberLevel


class BenefitResponse(BaseModel):
    """Benefit response."""
    id: int
    name: str
    description: Optional[str]
    benefit_type: BenefitType
    member_level: MemberLevel
    value: Optional[str]
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


class BenefitDistributionResponse(BaseModel):
    """Benefit distribution response."""
    id: int
    benefit_id: int
    benefit_name: str
    benefit_type: BenefitType
    period: str
    distributed_at: str
    expires_at: str
    is_used: bool
    used_at: Optional[str]

    class Config:
        from_attributes = True


class CreateBenefitRequest(BaseModel):
    """Create benefit request."""
    name: str = Field(..., max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    benefit_type: BenefitType
    member_level: MemberLevel
    value: Optional[str] = Field(None, max_length=100)


class DistributeBenefitRequest(BaseModel):
    """Distribute benefit request."""
    user_id: int
    benefit_id: int
    period: str = Field(..., pattern=r"^\d{4}-\d{2}$")
