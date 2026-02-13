"""Order service for order lifecycle and points integration."""
import random
from decimal import Decimal
from sqlalchemy.orm import Session

from app.core.error_codes import ErrorCode, BusinessException
from app.models.order import Order, OrderStatus
from app.repositories.order_repository import OrderRepository
from app.services.point_service import PointService
from app.utils.timezone_utils import get_current_beijing_time, utc_now


class OrderService:
    """Order service."""

    def __init__(self, db: Session):
        self.db = db
        self.order_repo = OrderRepository(db)
        self.point_service = PointService(db)

    def _generate_order_no(self) -> str:
        ts = get_current_beijing_time().strftime("%Y%m%d%H%M%S")
        suffix = random.randint(1000, 9999)
        return f"ORD{ts}{suffix}"

    def create_order(
        self,
        user_id: int,
        amount: Decimal,
        product_name: str = None,
        product_description: str = None,
    ) -> Order:
        """Create a new order (pending)."""
        for _ in range(5):
            order_no = self._generate_order_no()
            if not self.order_repo.get_by_order_no(order_no):
                break
        else:
            raise BusinessException(ErrorCode.INTERNAL_ERROR, details="生成订单号失败")

        order = Order(
            order_no=order_no,
            user_id=user_id,
            amount=amount,
            status=OrderStatus.PENDING,
            product_name=product_name,
            product_description=product_description,
        )
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return order

    def complete_order(self, order_id: int, user_id: int) -> Order:
        """Mark an order completed and earn points (1 yuan = 1 point)."""
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise BusinessException(ErrorCode.ORDER_NOT_FOUND)
        if order.user_id != user_id:
            raise BusinessException(ErrorCode.PERMISSION_DENIED)

        if order.status in (OrderStatus.CANCELLED, OrderStatus.REFUNDED):
            raise BusinessException(ErrorCode.INVALID_INPUT, details="订单状态不允许完成")

        if order.status != OrderStatus.COMPLETED:
            order.status = OrderStatus.COMPLETED
            order.completed_at = utc_now()
            if not order.paid_at:
                order.paid_at = utc_now()

        # Points are idempotent by order_id.
        self.point_service.earn_points_from_order(order.user_id, order.id, float(order.amount))
        self.db.commit()
        self.db.refresh(order)
        return order

    def refund_order(self, order_id: int, user_id: int) -> Order:
        """Refund an order and deduct previously earned points."""
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise BusinessException(ErrorCode.ORDER_NOT_FOUND)
        if order.user_id != user_id:
            raise BusinessException(ErrorCode.PERMISSION_DENIED)

        if order.status == OrderStatus.REFUNDED:
            return order

        if order.status == OrderStatus.CANCELLED:
            raise BusinessException(ErrorCode.INVALID_INPUT, details="已取消订单无法退款")

        # Only deduct points if order had been completed.
        if order.status == OrderStatus.COMPLETED:
            points = int(float(order.amount))
            if points > 0:
                self.point_service.deduct_points_for_refund(order.user_id, order.id, points)

        order.status = OrderStatus.REFUNDED
        order.refunded_at = utc_now()
        self.db.commit()
        self.db.refresh(order)
        return order

