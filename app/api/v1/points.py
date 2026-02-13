"""Points API endpoints."""
from fastapi import APIRouter, Depends, Query
from app.schemas.user import PointBalanceResponse, PointTransactionResponse
from app.utils.pagination import PaginatedResponse
from app.middleware.auth import get_current_user
from app.models.user import User
from app.services.point_service import PointService
from app.dependencies import get_point_service
from app.utils.timezone_utils import to_beijing_time
from datetime import datetime

router = APIRouter(prefix="/points", tags=["Points"])


@router.get("/balance", response_model=PointBalanceResponse)
async def get_balance(
    current_user: User = Depends(get_current_user)
):
    """Get points balance."""
    return PointBalanceResponse(
        available_points=current_user.available_points,
        total_earned_points=current_user.total_earned_points
    )


@router.get("/transactions", response_model=PaginatedResponse[PointTransactionResponse])
async def get_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    start_date: datetime = None,
    end_date: datetime = None,
    current_user: User = Depends(get_current_user),
    point_service: PointService = Depends(get_point_service)
):
    """Get point transaction history."""
    skip = (page - 1) * page_size
    transactions, total = point_service.get_transactions_by_time(current_user.id, start_date, end_date, skip, page_size)

    items = [
        PointTransactionResponse(
            id=t.id,
            transaction_type=t.transaction_type.value,
            reason=t.reason.value,
            points=t.points,
            balance_after=t.balance_after,
            description=t.description,
            created_at=to_beijing_time(t.created_at)
        )
        for t in transactions
    ]

    return PaginatedResponse.create(items, total, page, page_size)
