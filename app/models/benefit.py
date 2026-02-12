"""Benefit models."""
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Boolean, UniqueConstraint, Index
from sqlalchemy.sql import func
import enum
from app.db.session import Base
from app.models.user import MemberLevel


class BenefitType(str, enum.Enum):
    """Benefit type enum."""
    DISCOUNT_COUPON = "discount_coupon"
    POINTS_REWARD = "points_reward"
    FREE_SHIPPING = "free_shipping"
    EXCLUSIVE_ACCESS = "exclusive_access"


class Benefit(Base):
    """Benefit definition model."""
    __tablename__ = "benefits"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(String(1000))
    benefit_type = Column(Enum(BenefitType), nullable=False)

    member_level = Column(Enum(MemberLevel), nullable=False, index=True)
    value = Column(String(100))  # e.g., "100" for 100 points, "10%" for discount

    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class BenefitDistribution(Base):
    """Benefit distribution record model."""
    __tablename__ = "benefit_distributions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    benefit_id = Column(Integer, ForeignKey("benefits.id"), nullable=False)

    period = Column(String(7), nullable=False)  # Format: "YYYY-MM"
    distributed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    is_used = Column(Boolean, default=False, nullable=False)
    used_at = Column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint('user_id', 'benefit_id', 'period', name='uq_user_benefit_period'),
        Index('idx_user_expires', 'user_id', 'expires_at'),
    )
