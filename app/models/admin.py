"""Admin user and RBAC models."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Table
from sqlalchemy.sql import func
from app.db.session import Base


class AdminUser(Base):
    """Admin user model."""
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    full_name = Column(String(100))
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Role(Base):
    """Role model."""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200))

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Permission(Base):
    """Permission model."""
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    resource = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)
    description = Column(String(200))

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


# Many-to-many relationship tables
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)

admin_user_roles = Table(
    'admin_user_roles',
    Base.metadata,
    Column('admin_user_id', Integer, ForeignKey('admin_users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)


class AuditLog(Base):
    """Audit log model."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    admin_user_id = Column(Integer, ForeignKey("admin_users.id"), nullable=False, index=True)

    action = Column(String(100), nullable=False)
    resource = Column(String(100), nullable=False)
    resource_id = Column(String(100), index=True)

    details = Column(String(2000))
    ip_address = Column(String(50))
    trace_id = Column(String(50), index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
