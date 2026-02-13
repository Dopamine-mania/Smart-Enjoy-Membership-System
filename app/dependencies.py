"""Dependencies for FastAPI."""
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.auth_service import AuthService
from app.services.point_service import PointService
from app.services.benefit_service import BenefitService
from app.services.admin_service import AdminService
from app.services.order_service import OrderService


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Get auth service."""
    return AuthService(db)


def get_point_service(db: Session = Depends(get_db)) -> PointService:
    """Get point service."""
    return PointService(db)


def get_benefit_service(db: Session = Depends(get_db)) -> BenefitService:
    """Get benefit service."""
    return BenefitService(db)


def get_admin_service(db: Session = Depends(get_db)) -> AdminService:
    """Get admin service."""
    return AdminService(db)


def get_order_service(db: Session = Depends(get_db)) -> OrderService:
    """Get order service."""
    return OrderService(db)
