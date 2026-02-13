"""Orders API endpoints."""
from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import datetime
from app.schemas.order import OrderResponse, CreateOrderRequest
from app.utils.pagination import PaginatedResponse
from app.middleware.auth import get_current_user
from app.models.user import User
from app.models.order import OrderStatus
from app.repositories.order_repository import OrderRepository
from app.db.session import get_db
from sqlalchemy.orm import Session
from app.utils.timezone_utils import to_beijing_time
from app.services.order_service import OrderService
from app.dependencies import get_order_service

router = APIRouter(prefix="/orders", tags=["Orders"])


def _to_order_response(o) -> OrderResponse:
    return OrderResponse(
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
        updated_at=to_beijing_time(o.updated_at),
    )


@router.post("", response_model=OrderResponse)
async def create_order(
    request: CreateOrderRequest,
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
):
    """Create an order (for demo/testing)."""
    order = order_service.create_order(
        user_id=current_user.id,
        amount=request.amount,
        product_name=request.product_name,
        product_description=request.product_description,
    )
    return _to_order_response(order)


@router.post("/{order_id}/complete", response_model=OrderResponse)
async def complete_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
):
    """Complete an order and earn points (1 yuan = 1 point)."""
    order = order_service.complete_order(order_id=order_id, user_id=current_user.id)
    return _to_order_response(order)


@router.post("/{order_id}/refund", response_model=OrderResponse)
async def refund_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
):
    """Refund an order and deduct earned points."""
    order = order_service.refund_order(order_id=order_id, user_id=current_user.id)
    return _to_order_response(order)


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

    items = [_to_order_response(o) for o in orders]

    return PaginatedResponse.create(items, total, page, page_size)
