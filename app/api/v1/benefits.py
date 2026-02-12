"""Benefits API endpoints."""
from fastapi import APIRouter, Depends, Query
from typing import List
from app.schemas.benefit import BenefitResponse, BenefitDistributionResponse
from app.utils.pagination import PaginatedResponse
from app.middleware.auth import get_current_user
from app.models.user import User
from app.services.benefit_service import BenefitService
from app.dependencies import get_benefit_service
from app.utils.timezone_utils import to_beijing_time

router = APIRouter(prefix="/benefits", tags=["Benefits"])


@router.get("", response_model=List[BenefitResponse])
async def list_benefits(
    current_user: User = Depends(get_current_user),
    benefit_service: BenefitService = Depends(get_benefit_service)
):
    """List available benefits for current user's level."""
    benefits = benefit_service.get_benefits_by_level(current_user.member_level)

    return [
        BenefitResponse(
            id=b.id,
            name=b.name,
            description=b.description,
            benefit_type=b.benefit_type,
            member_level=b.member_level,
            value=b.value,
            is_active=b.is_active,
            created_at=to_beijing_time(b.created_at)
        )
        for b in benefits
    ]


@router.get("/my-benefits", response_model=PaginatedResponse[BenefitDistributionResponse])
async def get_my_benefits(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    benefit_service: BenefitService = Depends(get_benefit_service)
):
    """Get user's distributed benefits."""
    skip = (page - 1) * page_size
    distributions, total = benefit_service.get_user_benefits(current_user.id, skip, page_size)

    items = [
        BenefitDistributionResponse(
            id=d.id,
            benefit_id=d.benefit_id,
            benefit_name="",  # Will be populated by join in production
            benefit_type=d.benefit_id,  # Placeholder
            period=d.period,
            distributed_at=to_beijing_time(d.distributed_at),
            expires_at=to_beijing_time(d.expires_at),
            is_used=d.is_used,
            used_at=to_beijing_time(d.used_at)
        )
        for d in distributions
    ]

    return PaginatedResponse.create(items, total, page, page_size)
