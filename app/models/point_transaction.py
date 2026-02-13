"""Point transaction model."""
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Index
from sqlalchemy.sql import func
import enum
from app.db.session import Base


def _enum_values(enum_cls):
    return [e.value for e in enum_cls]


class PointTransactionType(str, enum.Enum):
    """Point transaction type enum."""
    EARN = "earn"
    DEDUCT = "deduct"
    ADJUST = "adjust"


class PointTransactionReason(str, enum.Enum):
    """Point transaction reason enum."""
    ORDER_COMPLETE = "order_complete"
    ORDER_REFUND = "order_refund"
    ADMIN_ADJUST = "admin_adjust"
    BENEFIT_REWARD = "benefit_reward"


class PointTransaction(Base):
    """Point transaction model."""
    __tablename__ = "point_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    transaction_type = Column(Enum(PointTransactionType, native_enum=False, values_callable=_enum_values), nullable=False)
    reason = Column(Enum(PointTransactionReason, native_enum=False, values_callable=_enum_values), nullable=False)
    points = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)

    order_id = Column(Integer, ForeignKey("orders.id"), index=True)
    idempotency_key = Column(String(255), unique=True, index=True)

    description = Column(String(500))
    admin_user_id = Column(Integer, ForeignKey("admin_users.id"))

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_user_created', 'user_id', 'created_at'),
    )
