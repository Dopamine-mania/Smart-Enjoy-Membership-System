"""Order schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from app.models.order import OrderStatus


class CreateOrderRequest(BaseModel):
    """Create order request."""
    amount: Decimal = Field(..., gt=0)
    product_name: Optional[str] = Field(None, max_length=200)
    product_description: Optional[str] = Field(None, max_length=1000)


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
