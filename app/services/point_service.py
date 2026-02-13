"""Point service for points management."""
from sqlalchemy.orm import Session
from app.models.point_transaction import PointTransaction, PointTransactionType, PointTransactionReason
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.point_repository import PointRepository
from app.core.error_codes import ErrorCode, BusinessException
from app.utils.redis_client import redis_client


class PointService:
    """Point service."""

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.point_repo = PointRepository(db)

    def earn_points_from_order(self, user_id: int, order_id: int, amount: float) -> PointTransaction:
        """
        Earn points from order completion.

        Args:
            user_id: User ID
            order_id: Order ID
            amount: Order amount (1 yuan = 1 point)

        Returns:
            Point transaction record
        """
        # Calculate points (1 yuan = 1 point)
        points = int(amount)

        # Idempotency key
        idempotency_key = f"order_points:{order_id}"

        # Check if already processed
        existing = self.point_repo.get_by_idempotency_key(idempotency_key)
        if existing:
            return existing

        # Use distributed lock
        lock_key = f"idempotency:{idempotency_key}"
        if not redis_client.setnx(lock_key, "1"):
            # Already being processed
            raise BusinessException(ErrorCode.IDEMPOTENCY_CONFLICT)

        try:
            redis_client.expire(lock_key, 300)  # 5 minutes

            # Get user
            user = self.user_repo.get_by_id(user_id)
            if not user:
                raise BusinessException(ErrorCode.USER_NOT_FOUND)

            # Update user points
            user.available_points += points
            user.total_earned_points += points

            # Create transaction record
            transaction = self.point_repo.create(
                user_id=user_id,
                transaction_type=PointTransactionType.EARN,
                reason=PointTransactionReason.ORDER_COMPLETE,
                points=points,
                balance_after=user.available_points,
                order_id=order_id,
                idempotency_key=idempotency_key,
                description=f"订单完成奖励积分"
            )

            self.db.commit()
            return transaction

        finally:
            redis_client.delete(lock_key)

    def deduct_points_for_refund(self, user_id: int, order_id: int, points: int) -> PointTransaction:
        """
        Deduct points for order refund.

        Args:
            user_id: User ID
            order_id: Order ID
            points: Points to deduct

        Returns:
            Point transaction record
        """
        # Idempotency key
        idempotency_key = f"refund_points:{order_id}"

        # Check if already processed
        existing = self.point_repo.get_by_idempotency_key(idempotency_key)
        if existing:
            return existing

        # Use distributed lock
        lock_key = f"idempotency:{idempotency_key}"
        if not redis_client.setnx(lock_key, "1"):
            raise BusinessException(ErrorCode.IDEMPOTENCY_CONFLICT)

        try:
            redis_client.expire(lock_key, 300)

            # Get user
            user = self.user_repo.get_by_id(user_id)
            if not user:
                raise BusinessException(ErrorCode.USER_NOT_FOUND)

            # Check sufficient points
            if user.available_points < points:
                raise BusinessException(ErrorCode.INSUFFICIENT_POINTS)

            # Update user points
            user.available_points -= points

            # Create transaction record
            transaction = self.point_repo.create(
                user_id=user_id,
                transaction_type=PointTransactionType.DEDUCT,
                reason=PointTransactionReason.ORDER_REFUND,
                points=-points,
                balance_after=user.available_points,
                order_id=order_id,
                idempotency_key=idempotency_key,
                description=f"订单退款扣除积分"
            )

            self.db.commit()
            return transaction

        finally:
            redis_client.delete(lock_key)

    def adjust_points(self, user_id: int, points: int, reason: str, admin_user_id: int) -> PointTransaction:
        """
        Admin adjust user points.

        Args:
            user_id: User ID
            points: Points to adjust (positive for add, negative for deduct)
            reason: Adjustment reason
            admin_user_id: Admin user ID

        Returns:
            Point transaction record
        """
        # Get user
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise BusinessException(ErrorCode.USER_NOT_FOUND)

        # Check if deduction would result in negative balance
        if points < 0 and user.available_points < abs(points):
            raise BusinessException(ErrorCode.INSUFFICIENT_POINTS)

        # Update user points
        user.available_points += points
        if points > 0:
            user.total_earned_points += points

        # Determine transaction type
        transaction_type = PointTransactionType.ADJUST

        # Create transaction record
        transaction = self.point_repo.create(
            user_id=user_id,
            transaction_type=transaction_type,
            reason=PointTransactionReason.ADMIN_ADJUST,
            points=points,
            balance_after=user.available_points,
            description=reason,
            admin_user_id=admin_user_id
        )

        self.db.commit()
        return transaction

    def get_transactions(self, user_id: int, skip: int = 0, limit: int = 20) -> tuple[list, int]:
        """Get user point transactions."""
        return self.point_repo.list_by_user(user_id, None, None, skip, limit)

    def get_transactions_by_time(
        self,
        user_id: int,
        start_date=None,
        end_date=None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list, int]:
        """Get user point transactions with optional time filters."""
        return self.point_repo.list_by_user(user_id, start_date, end_date, skip, limit)
