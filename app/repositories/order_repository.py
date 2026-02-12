"""Order repository."""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from datetime import datetime
from app.models.order import Order, OrderStatus


class OrderRepository:
    """Order repository."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, order_id: int) -> Optional[Order]:
        """Get order by ID."""
        return self.db.query(Order).filter(Order.id == order_id).first()

    def get_by_order_no(self, order_no: str) -> Optional[Order]:
        """Get order by order number."""
        return self.db.query(Order).filter(Order.order_no == order_no).first()

    def list_by_user(
        self,
        user_id: int,
        status: OrderStatus = None,
        start_date: datetime = None,
        end_date: datetime = None,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[List[Order], int]:
        """List user orders with filters."""
        query = self.db.query(Order).filter(Order.user_id == user_id)

        if status:
            query = query.filter(Order.status == status)

        if start_date:
            query = query.filter(Order.created_at >= start_date)

        if end_date:
            query = query.filter(Order.created_at <= end_date)

        total = query.count()
        orders = query.order_by(desc(Order.created_at)).offset(skip).limit(limit).all()
        return orders, total

    def list_all(
        self,
        status: OrderStatus = None,
        start_date: datetime = None,
        end_date: datetime = None,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[List[Order], int]:
        """List all orders with filters (admin)."""
        query = self.db.query(Order)

        if status:
            query = query.filter(Order.status == status)

        if start_date:
            query = query.filter(Order.created_at >= start_date)

        if end_date:
            query = query.filter(Order.created_at <= end_date)

        total = query.count()
        orders = query.order_by(desc(Order.created_at)).offset(skip).limit(limit).all()
        return orders, total
