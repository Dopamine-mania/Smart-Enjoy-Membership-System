"""Admin API endpoints."""
from fastapi import APIRouter, Depends, Query, Request
from typing import Optional
from datetime import datetime
from app.schemas.admin import (
    AdminLoginRequest,
    AdminUserResponse,
    AdjustPointsRequest,
    UpdateUserRequest,
    AuditLogResponse
)
from app.schemas.user import UserProfileResponse
from app.schemas.order import OrderResponse
from app.schemas.benefit import BenefitResponse, CreateBenefitRequest, DistributeBenefitRequest
from app.schemas.common import SuccessResponse, ErrorResponse
from app.utils.pagination import PaginatedResponse
from app.middleware.auth import get_current_admin, security
from app.models.admin import AdminUser
from app.models.order import OrderStatus
from app.services.admin_service import AdminService
from app.services.point_service import PointService
from app.services.benefit_service import BenefitService
from app.repositories.user_repository import UserRepository
from app.repositories.order_repository import OrderRepository
from app.dependencies import get_admin_service, get_point_service, get_benefit_service
from app.db.session import get_db
from sqlalchemy.orm import Session
from app.utils.timezone_utils import to_beijing_time
from app.utils.data_masking import mask_email
from app.core.error_codes import ErrorCode, BusinessException
from app.config import settings

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/auth/login")
async def admin_login(
    request: AdminLoginRequest,
    admin_service: AdminService = Depends(get_admin_service)
):
    """Admin login."""
    access_token, admin = admin_service.login(request.username, request.password)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_EXPIRY_HOURS * 3600,
        "admin": AdminUserResponse(
            id=admin.id,
            username=admin.username,
            email=admin.email,
            full_name=admin.full_name,
            is_active=admin.is_active,
            created_at=to_beijing_time(admin.created_at)
        )
    }


@router.get("/users", response_model=PaginatedResponse[UserProfileResponse])
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    request: Request = None,
    current_admin: AdminUser = Depends(get_current_admin),
    admin_service: AdminService = Depends(get_admin_service),
    db: Session = Depends(get_db)
):
    """List all users (admin)."""
    # Check permission
    if not admin_service.check_permission(current_admin.id, "users.view"):
        raise BusinessException(ErrorCode.PERMISSION_DENIED)

    user_repo = UserRepository(db)
    skip = (page - 1) * page_size
    users, total = user_repo.list_users(skip, page_size)

    items = [
        UserProfileResponse(
            id=u.id,
            email=mask_email(u.email),
            nickname=u.nickname,
            avatar_url=u.avatar_url,
            gender=u.gender,
            birthday=to_beijing_time(u.birthday),
            id_card_last_four=u.id_card_last_four,
            member_level=u.member_level,
            available_points=u.available_points,
            total_earned_points=u.total_earned_points,
            created_at=to_beijing_time(u.created_at)
        )
        for u in users
    ]

    # Log action
    admin_service.log_action(
        admin_user_id=current_admin.id,
        action="list",
        resource="users",
        trace_id=getattr(request.state, 'trace_id', None)
    )

    return PaginatedResponse.create(items, total, page, page_size)


@router.patch("/users/{user_id}", response_model=SuccessResponse)
async def update_user(
    user_id: int,
    update_request: UpdateUserRequest,
    request: Request = None,
    current_admin: AdminUser = Depends(get_current_admin),
    admin_service: AdminService = Depends(get_admin_service),
    db: Session = Depends(get_db)
):
    """Update user (admin)."""
    # Check permission
    if not admin_service.check_permission(current_admin.id, "users.edit"):
        raise BusinessException(ErrorCode.PERMISSION_DENIED)

    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)

    if not user:
        raise BusinessException(ErrorCode.USER_NOT_FOUND)

    # Update fields
    if update_request.nickname is not None:
        user.nickname = update_request.nickname

    if update_request.member_level is not None:
        from app.models.user import MemberLevel
        user.member_level = MemberLevel(update_request.member_level)

    if update_request.is_locked is not None:
        user.is_locked = update_request.is_locked
        if update_request.is_locked and update_request.locked_reason:
            user.locked_reason = update_request.locked_reason

    user_repo.update(user)

    # Log action
    admin_service.log_action(
        admin_user_id=current_admin.id,
        action="update",
        resource="users",
        resource_id=str(user_id),
        details=f"Updated user: {update_request.dict(exclude_none=True)}",
        trace_id=getattr(request.state, 'trace_id', None)
    )

    return SuccessResponse(message="用户更新成功")


@router.post("/users/{user_id}/lock", response_model=SuccessResponse)
async def lock_user(
    user_id: int,
    reason: str,
    request: Request = None,
    current_admin: AdminUser = Depends(get_current_admin),
    admin_service: AdminService = Depends(get_admin_service),
    db: Session = Depends(get_db)
):
    """Lock user account (admin)."""
    # Check permission
    if not admin_service.check_permission(current_admin.id, "users.lock"):
        raise BusinessException(ErrorCode.PERMISSION_DENIED)

    user_repo = UserRepository(db)
    user = user_repo.lock_user(user_id, reason)

    if not user:
        raise BusinessException(ErrorCode.USER_NOT_FOUND)

    # Log action
    admin_service.log_action(
        admin_user_id=current_admin.id,
        action="lock",
        resource="users",
        resource_id=str(user_id),
        details=f"Locked user: {reason}",
        trace_id=getattr(request.state, 'trace_id', None)
    )

    return SuccessResponse(message="用户已锁定")


@router.post("/points/adjust", response_model=SuccessResponse)
async def adjust_points(
    adjust_request: AdjustPointsRequest,
    request: Request = None,
    current_admin: AdminUser = Depends(get_current_admin),
    admin_service: AdminService = Depends(get_admin_service),
    point_service: PointService = Depends(get_point_service)
):
    """Adjust user points (admin)."""
    # Check permission
    if not admin_service.check_permission(current_admin.id, "points.adjust"):
        raise BusinessException(ErrorCode.PERMISSION_DENIED)

    # Adjust points
    transaction = point_service.adjust_points(
        user_id=adjust_request.user_id,
        points=adjust_request.points,
        reason=adjust_request.reason,
        admin_user_id=current_admin.id
    )

    # Log action
    admin_service.log_action(
        admin_user_id=current_admin.id,
        action="adjust",
        resource="points",
        resource_id=str(adjust_request.user_id),
        details=f"Adjusted points: {adjust_request.points}, reason: {adjust_request.reason}",
        trace_id=getattr(request.state, 'trace_id', None)
    )

    return SuccessResponse(message="积分调整成功")


@router.post("/benefits", response_model=BenefitResponse)
async def create_benefit(
    benefit_request: CreateBenefitRequest,
    request: Request = None,
    current_admin: AdminUser = Depends(get_current_admin),
    admin_service: AdminService = Depends(get_admin_service),
    benefit_service: BenefitService = Depends(get_benefit_service)
):
    """Create benefit (admin)."""
    # Check permission
    if not admin_service.check_permission(current_admin.id, "benefits.create"):
        raise BusinessException(ErrorCode.PERMISSION_DENIED)

    benefit = benefit_service.create_benefit(
        name=benefit_request.name,
        description=benefit_request.description,
        benefit_type=benefit_request.benefit_type,
        member_level=benefit_request.member_level,
        value=benefit_request.value
    )

    # Log action
    admin_service.log_action(
        admin_user_id=current_admin.id,
        action="create",
        resource="benefits",
        resource_id=str(benefit.id),
        details=f"Created benefit: {benefit.name}",
        trace_id=getattr(request.state, 'trace_id', None)
    )

    return BenefitResponse(
        id=benefit.id,
        name=benefit.name,
        description=benefit.description,
        benefit_type=benefit.benefit_type,
        member_level=benefit.member_level,
        value=benefit.value,
        is_active=benefit.is_active,
        created_at=to_beijing_time(benefit.created_at)
    )


@router.post("/benefits/distribute", response_model=SuccessResponse)
async def distribute_benefit(
    distribute_request: DistributeBenefitRequest,
    request: Request = None,
    current_admin: AdminUser = Depends(get_current_admin),
    admin_service: AdminService = Depends(get_admin_service),
    benefit_service: BenefitService = Depends(get_benefit_service)
):
    """Distribute benefit to user (admin)."""
    # Check permission
    if not admin_service.check_permission(current_admin.id, "benefits.distribute"):
        raise BusinessException(ErrorCode.PERMISSION_DENIED)

    distribution = benefit_service._distribute_single_benefit(
        user_id=distribute_request.user_id,
        benefit_id=distribute_request.benefit_id,
        period=distribute_request.period
    )

    # Log action
    admin_service.log_action(
        admin_user_id=current_admin.id,
        action="distribute",
        resource="benefits",
        resource_id=str(distribute_request.benefit_id),
        details=f"Distributed to user {distribute_request.user_id}, period {distribute_request.period}",
        trace_id=getattr(request.state, 'trace_id', None)
    )

    return SuccessResponse(message="权益发放成功")


@router.get("/orders", response_model=PaginatedResponse[OrderResponse])
async def list_all_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[OrderStatus] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_admin: AdminUser = Depends(get_current_admin),
    admin_service: AdminService = Depends(get_admin_service),
    db: Session = Depends(get_db)
):
    """List all orders (admin)."""
    # Check permission
    if not admin_service.check_permission(current_admin.id, "orders.view"):
        raise BusinessException(ErrorCode.PERMISSION_DENIED)

    order_repo = OrderRepository(db)
    skip = (page - 1) * page_size

    orders, total = order_repo.list_all(
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


@router.get("/audit-logs", response_model=PaginatedResponse[AuditLogResponse])
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    admin_user_id: Optional[int] = None,
    current_admin: AdminUser = Depends(get_current_admin),
    admin_service: AdminService = Depends(get_admin_service)
):
    """List audit logs (admin)."""
    # Check permission
    if not admin_service.check_permission(current_admin.id, "audit_logs.view"):
        raise BusinessException(ErrorCode.PERMISSION_DENIED)

    skip = (page - 1) * page_size
    logs, total = admin_service.list_audit_logs(admin_user_id, skip, page_size)

    items = [
        AuditLogResponse(
            id=log.id,
            admin_user_id=log.admin_user_id,
            admin_username="",  # Will be populated by join in production
            action=log.action,
            resource=log.resource,
            resource_id=log.resource_id,
            details=log.details,
            ip_address=log.ip_address,
            trace_id=log.trace_id,
            created_at=to_beijing_time(log.created_at)
        )
        for log in logs
    ]

    return PaginatedResponse.create(items, total, page, page_size)
