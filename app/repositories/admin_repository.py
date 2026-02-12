"""Admin repository."""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.admin import AdminUser, Role, Permission, AuditLog, role_permissions, admin_user_roles


class AdminRepository:
    """Admin repository."""

    def __init__(self, db: Session):
        self.db = db

    def get_admin_by_username(self, username: str) -> Optional[AdminUser]:
        """Get admin by username."""
        return self.db.query(AdminUser).filter(AdminUser.username == username).first()

    def get_admin_by_id(self, admin_id: int) -> Optional[AdminUser]:
        """Get admin by ID."""
        return self.db.query(AdminUser).filter(AdminUser.id == admin_id).first()

    def get_admin_roles(self, admin_id: int) -> List[Role]:
        """Get admin roles."""
        return self.db.query(Role).join(
            admin_user_roles, Role.id == admin_user_roles.c.role_id
        ).filter(admin_user_roles.c.admin_user_id == admin_id).all()

    def get_role_permissions(self, role_id: int) -> List[Permission]:
        """Get role permissions."""
        return self.db.query(Permission).join(
            role_permissions, Permission.id == role_permissions.c.permission_id
        ).filter(role_permissions.c.role_id == role_id).all()

    def create_audit_log(
        self,
        admin_user_id: int,
        action: str,
        resource: str,
        resource_id: str = None,
        details: str = None,
        ip_address: str = None,
        trace_id: str = None
    ) -> AuditLog:
        """Create audit log."""
        log = AuditLog(
            admin_user_id=admin_user_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            trace_id=trace_id
        )
        self.db.add(log)
        self.db.flush()
        return log

    def list_audit_logs(
        self,
        admin_user_id: int = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[List[AuditLog], int]:
        """List audit logs."""
        query = self.db.query(AuditLog)

        if admin_user_id:
            query = query.filter(AuditLog.admin_user_id == admin_user_id)

        total = query.count()
        logs = query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()
        return logs, total
