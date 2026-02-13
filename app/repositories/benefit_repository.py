"""Benefit repository."""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from datetime import datetime
from app.models.benefit import Benefit, BenefitDistribution, BenefitType
from app.models.user import MemberLevel


class BenefitRepository:
    """Benefit repository."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, benefit_id: int) -> Optional[Benefit]:
        """Get benefit by ID."""
        return self.db.query(Benefit).filter(Benefit.id == benefit_id).first()

    def create(
        self,
        name: str,
        benefit_type: BenefitType,
        member_level: MemberLevel,
        description: str = None,
        value: str = None
    ) -> Benefit:
        """Create benefit."""
        benefit = Benefit(
            name=name,
            description=description,
            benefit_type=benefit_type,
            member_level=member_level,
            value=value,
            is_active=True
        )
        self.db.add(benefit)
        self.db.flush()
        return benefit

    def list_by_level(self, member_level: MemberLevel) -> List[Benefit]:
        """List active benefits by member level."""
        return self.db.query(Benefit).filter(
            and_(
                Benefit.member_level == member_level,
                Benefit.is_active == True
            )
        ).all()

    def list_all(self, skip: int = 0, limit: int = 50) -> tuple[List[Benefit], int]:
        """List all benefits."""
        query = self.db.query(Benefit)
        total = query.count()
        benefits = query.order_by(desc(Benefit.created_at)).offset(skip).limit(limit).all()
        return benefits, total

    def list_by_ids(self, benefit_ids: List[int]) -> List[Benefit]:
        """List benefits by IDs."""
        if not benefit_ids:
            return []
        return self.db.query(Benefit).filter(Benefit.id.in_(benefit_ids)).all()

    def get_distribution(self, user_id: int, benefit_id: int, period: str) -> Optional[BenefitDistribution]:
        """Get benefit distribution record."""
        return self.db.query(BenefitDistribution).filter(
            and_(
                BenefitDistribution.user_id == user_id,
                BenefitDistribution.benefit_id == benefit_id,
                BenefitDistribution.period == period
            )
        ).first()

    def create_distribution(
        self,
        user_id: int,
        benefit_id: int,
        period: str,
        expires_at: datetime
    ) -> BenefitDistribution:
        """Create benefit distribution."""
        distribution = BenefitDistribution(
            user_id=user_id,
            benefit_id=benefit_id,
            period=period,
            expires_at=expires_at,
            is_used=False
        )
        self.db.add(distribution)
        self.db.flush()
        return distribution

    def list_user_distributions(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[List[BenefitDistribution], int]:
        """List user benefit distributions."""
        query = self.db.query(BenefitDistribution).filter(BenefitDistribution.user_id == user_id)
        total = query.count()
        distributions = query.order_by(desc(BenefitDistribution.distributed_at)).offset(skip).limit(limit).all()
        return distributions, total
