"""Orders API endpoints."""
from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import datetime
from app.schemas.order import OrderResponse
from app.utils.pagination import PaginatedResponse
from app.middleware.auth import get_current_user
from app.models.user import User
from app.models.order import OrderStatus
from app.repositories.order_repository import OrderRepository
from app.db.session import get_db
from sqlalchemy.orm import Session
from app.utils.timezone_utils import to_beijing_time

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("", response_model=PaginatedResponse[OrderResponse])
async def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[OrderStatus] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user orders with filters."""
    order_repo = OrderRepository(db)
    skip = (page - 1) * page_size

    orders, total = order_repo.list_by_user(
        user_id=current_user.id,
        status=status,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=page_size
    )

    items = [
        OrderResponse(
            id=o.id,
            order_no=o.order_no,
            amount=o.amount,
            status=o.status,
            product_name=o.product_name,
            product_description=o.product_description,
            paid_at=to_beijing_time(o.paid_at),
            completed_at=to_beijing_time(o.completed_at),
            cancelled_at=to_beijing_time(o.cancelled_at),
            refunded_at=to_beijing_time(o.refunded_at),
            created_at=to_beijing_time(o.created_at),
            updated_at=to_beijing_time(o.updated_at)
        )
        for o in orders
    ]

    return PaginatedResponse.create(items, total, page, page_size)
