"""Point transaction repository."""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.point_transaction import PointTransaction, PointTransactionType, PointTransactionReason


class PointRepository:
    """Point transaction repository."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: int,
        transaction_type: PointTransactionType,
        reason: PointTransactionReason,
        points: int,
        balance_after: int,
        order_id: int = None,
        idempotency_key: str = None,
        description: str = None,
        admin_user_id: int = None
    ) -> PointTransaction:
        """Create point transaction."""
        transaction = PointTransaction(
            user_id=user_id,
            transaction_type=transaction_type,
            reason=reason,
            points=points,
            balance_after=balance_after,
            order_id=order_id,
            idempotency_key=idempotency_key,
            description=description,
            admin_user_id=admin_user_id
        )
        self.db.add(transaction)
        self.db.flush()
        return transaction

    def get_by_idempotency_key(self, idempotency_key: str) -> Optional[PointTransaction]:
        """Get transaction by idempotency key."""
        return self.db.query(PointTransaction).filter(
            PointTransaction.idempotency_key == idempotency_key
        ).first()

    def list_by_user(self, user_id: int, skip: int = 0, limit: int = 20) -> tuple[List[PointTransaction], int]:
        """
        List user transactions with pagination.

        Returns:
            Tuple of (transactions, total_count)
        """
        query = self.db.query(PointTransaction).filter(PointTransaction.user_id == user_id)
        total = query.count()
        transactions = query.order_by(desc(PointTransaction.created_at)).offset(skip).limit(limit).all()
        return transactions, total
