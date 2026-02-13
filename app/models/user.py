"""User model."""
from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean, Numeric
from sqlalchemy.sql import func
from datetime import datetime
import enum
from app.db.session import Base


def _enum_values(enum_cls):
    return [e.value for e in enum_cls]


class MemberLevel(str, enum.Enum):
    """Member level enum."""
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class Gender(str, enum.Enum):
    """Gender enum."""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class User(Base):
    """User model."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    nickname = Column(String(100))
    avatar_url = Column(String(500))
    gender = Column(Enum(Gender, native_enum=False, values_callable=_enum_values))
    birthday = Column(DateTime(timezone=True))
    id_card_last_four = Column(String(4))

    member_level = Column(
        Enum(MemberLevel, native_enum=False, values_callable=_enum_values),
        default=MemberLevel.BRONZE,
        nullable=False,
        index=True,
    )
    available_points = Column(Integer, default=0, nullable=False)
    total_earned_points = Column(Integer, default=0, nullable=False)

    is_locked = Column(Boolean, default=False, nullable=False)
    locked_at = Column(DateTime(timezone=True))
    locked_reason = Column(String(500))

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
