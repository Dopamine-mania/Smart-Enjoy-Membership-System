"""Order schemas."""
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from app.models.order import OrderStatus


class OrderResponse(BaseModel):
    """Order response."""
    id: int
    order_no: str
    amount: Decimal
    status: OrderStatus
    product_name: Optional[str]
    product_description: Optional[str]
    paid_at: Optional[str]
    completed_at: Optional[str]
    cancelled_at: Optional[str]
    refunded_at: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True
