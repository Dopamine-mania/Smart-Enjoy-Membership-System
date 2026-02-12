"""Benefit service for benefits management."""
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
from typing import List
from app.models.benefit import Benefit, BenefitDistribution, BenefitType
from app.models.user import User, MemberLevel
from app.repositories.benefit_repository import BenefitRepository
from app.repositories.user_repository import UserRepository
from app.core.error_codes import ErrorCode, BusinessException
from app.utils.redis_client import redis_client


class BenefitService:
    """Benefit service."""

    def __init__(self, db: Session):
        self.db = db
        self.benefit_repo = BenefitRepository(db)
        self.user_repo = UserRepository(db)

    def get_benefits_by_level(self, member_level: MemberLevel) -> List[Benefit]:
        """Get active benefits for member level."""
        return self.benefit_repo.list_by_level(member_level)

    def get_user_benefits(self, user_id: int, skip: int = 0, limit: int = 20) -> tuple[List[BenefitDistribution], int]:
        """Get user's distributed benefits."""
        return self.benefit_repo.list_user_distributions(user_id, skip, limit)

    def distribute_monthly_benefits(self, user_id: int, period: str) -> List[BenefitDistribution]:
        """
        Distribute monthly benefits to user.

        Args:
            user_id: User ID
            period: Period in format "YYYY-MM"

        Returns:
            List of distributed benefits
        """
        # Get user
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise BusinessException(ErrorCode.USER_NOT_FOUND)

        # Get benefits for user's level
        benefits = self.get_benefits_by_level(user.member_level)

        distributions = []
        for benefit in benefits:
            try:
                distribution = self._distribute_single_benefit(user_id, benefit.id, period)
                if distribution:
                    distributions.append(distribution)
            except BusinessException as e:
                # Skip if already distributed
                if e.code == ErrorCode.BENEFIT_ALREADY_DISTRIBUTED[0]:
                    continue
                raise

        return distributions

    def _distribute_single_benefit(self, user_id: int, benefit_id: int, period: str) -> BenefitDistribution:
        """
        Distribute single benefit with distributed lock.

        Args:
            user_id: User ID
            benefit_id: Benefit ID
            period: Period in format "YYYY-MM"

        Returns:
            Benefit distribution record
        """
        # Distributed lock
        lock_key = f"benefit_lock:{user_id}:{benefit_id}:{period}"
        if not redis_client.setnx(lock_key, "1"):
            raise BusinessException(ErrorCode.BENEFIT_ALREADY_DISTRIBUTED)

        try:
            redis_client.expire(lock_key, 300)  # 5 minutes

            # Check if already distributed
            existing = self.benefit_repo.get_distribution(user_id, benefit_id, period)
            if existing:
                raise BusinessException(ErrorCode.BENEFIT_ALREADY_DISTRIBUTED)

            # Get benefit
            benefit = self.benefit_repo.get_by_id(benefit_id)
            if not benefit:
                raise BusinessException(ErrorCode.BENEFIT_NOT_FOUND)

            # Calculate expiry (end of month)
            year, month = map(int, period.split('-'))
            expires_at = datetime(year, month, 1, tzinfo=timezone.utc) + relativedelta(months=1) - relativedelta(seconds=1)

            # Create distribution record
            distribution = self.benefit_repo.create_distribution(
                user_id=user_id,
                benefit_id=benefit_id,
                period=period,
                expires_at=expires_at
            )

            self.db.commit()
            return distribution

        finally:
            redis_client.delete(lock_key)

    def create_benefit(
        self,
        name: str,
        benefit_type: BenefitType,
        member_level: MemberLevel,
        description: str = None,
        value: str = None
    ) -> Benefit:
        """Create new benefit."""
        benefit = self.benefit_repo.create(
            name=name,
            description=description,
            benefit_type=benefit_type,
            member_level=member_level,
            value=value
        )
        self.db.commit()
        return benefit

    def list_benefits(self, skip: int = 0, limit: int = 50) -> tuple[List[Benefit], int]:
        """List all benefits."""
        return self.benefit_repo.list_all(skip, limit)
