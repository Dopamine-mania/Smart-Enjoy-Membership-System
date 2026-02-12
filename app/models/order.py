"""Order model."""
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Numeric, Index
from sqlalchemy.sql import func
import enum
from app.db.session import Base


class OrderStatus(str, enum.Enum):
    """Order status enum."""
    PENDING = "pending"
    PAID = "paid"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class Order(Base):
    """Order model."""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False, index=True)

    product_name = Column(String(200))
    product_description = Column(String(1000))

    paid_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    cancelled_at = Column(DateTime(timezone=True))
    refunded_at = Column(DateTime(timezone=True))

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_user_created', 'user_id', 'created_at'),
    )
