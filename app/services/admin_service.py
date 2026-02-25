"""Admin service."""
from sqlalchemy.orm import Session
from typing import List, Set
from app.core.security import verify_password, create_access_token
from app.core.error_codes import ErrorCode, BusinessException
from app.models.admin import AdminUser, AuditLog
from app.models.user import MemberLevel
from app.models.order import Order, OrderStatus
from app.repositories.admin_repository import AdminRepository
from app.repositories.user_repository import UserRepository
from app.repositories.order_repository import OrderRepository
from app.services.point_service import PointService
from datetime import datetime
from typing import Optional, Tuple


class AdminService:
    """Admin service."""

    def __init__(self, db: Session):
        self.db = db
        self.admin_repo = AdminRepository(db)
        self.user_repo = UserRepository(db)
        self.order_repo = OrderRepository(db)
        self.point_service = PointService(db)

    def login(self, username: str, password: str) -> tuple[str, AdminUser]:
        """
        Admin login.

        Args:
            username: Admin username
            password: Admin password

        Returns:
            Tuple of (access_token, admin_user)
        """
        # Get admin user
        admin = self.admin_repo.get_admin_by_username(username)
        if not admin:
            raise BusinessException(ErrorCode.ADMIN_NOT_FOUND)

        # Verify password
        if not verify_password(password, admin.password_hash):
            raise BusinessException(ErrorCode.LOGIN_FAILED)

        # Check if active
        if not admin.is_active:
            raise BusinessException(ErrorCode.ACCOUNT_LOCKED)

        # Create access token with explicit role claim.
        access_token, jti = create_access_token(subject_id=admin.id, role="admin")

        return access_token, admin

    def get_admin_permissions(self, admin_id: int) -> Set[str]:
        """
        Get admin permissions.

        Returns:
            Set of permission strings like "users.edit", "points.adjust"
        """
        # Get admin roles
        roles = self.admin_repo.get_admin_roles(admin_id)

        permissions = set()
        for role in roles:
            # Get role permissions
            role_perms = self.admin_repo.get_role_permissions(role.id)
            for perm in role_perms:
                permissions.add(f"{perm.resource}.{perm.action}")

        return permissions

    def check_permission(self, admin_id: int, required_permission: str) -> bool:
        """Check if admin has required permission."""
        permissions = self.get_admin_permissions(admin_id)
        return required_permission in permissions

    def log_action(
        self,
        admin_user_id: int,
        action: str,
        resource: str,
        resource_id: str = None,
        details: str = None,
        ip_address: str = None,
        trace_id: str = None
    ) -> AuditLog:
        """Log admin action."""
        log = self.admin_repo.create_audit_log(
            admin_user_id=admin_user_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            trace_id=trace_id
        )
        self.db.commit()
        return log

    def list_audit_logs(self, admin_user_id: int = None, skip: int = 0, limit: int = 50) -> tuple[List[tuple[AuditLog, str]], int]:
        """List audit logs with admin username."""
        return self.admin_repo.list_audit_logs(admin_user_id, skip, limit)

    def list_users(self, skip: int = 0, limit: int = 20):
        """List users with pagination."""
        return self.user_repo.list_users(skip, limit)

    def update_user(self, user_id: int, update_request) -> object:
        """Update user fields (admin)."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise BusinessException(ErrorCode.USER_NOT_FOUND)

        if update_request.nickname is not None:
            user.nickname = update_request.nickname

        if update_request.member_level is not None:
            user.member_level = MemberLevel(update_request.member_level)

        if update_request.is_locked is not None:
            user.is_locked = update_request.is_locked
            if update_request.is_locked and update_request.locked_reason:
                user.locked_reason = update_request.locked_reason

        return self.user_repo.update(user)

    def lock_user(self, user_id: int, reason: str):
        """Lock user account."""
        user = self.user_repo.lock_user(user_id, reason)
        if not user:
            raise BusinessException(ErrorCode.USER_NOT_FOUND)
        return user

    def list_all_orders(
        self,
        status: Optional[OrderStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Order], int]:
        """List all orders with filters (admin)."""
        return self.order_repo.list_all(
            status=status,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit,
        )
