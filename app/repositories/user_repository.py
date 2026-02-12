"""User repository for database operations."""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.user import User, MemberLevel


class UserRepository:
    """User repository."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()

    def create(self, email: str, nickname: str = None) -> User:
        """Create new user."""
        user = User(
            email=email,
            nickname=nickname,
            member_level=MemberLevel.BRONZE,
            available_points=0,
            total_earned_points=0,
            is_locked=False
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user: User) -> User:
        """Update user."""
        self.db.commit()
        self.db.refresh(user)
        return user

    def list_users(self, skip: int = 0, limit: int = 20) -> tuple[List[User], int]:
        """
        List users with pagination.

        Returns:
            Tuple of (users, total_count)
        """
        query = self.db.query(User)
        total = query.count()
        users = query.order_by(desc(User.created_at)).offset(skip).limit(limit).all()
        return users, total

    def lock_user(self, user_id: int, reason: str) -> User:
        """Lock user account."""
        from datetime import datetime, timezone

        user = self.get_by_id(user_id)
        if not user:
            return None

        user.is_locked = True
        user.locked_at = datetime.now(timezone.utc)
        user.locked_reason = reason

        return self.update(user)

    def unlock_user(self, user_id: int) -> User:
        """Unlock user account."""
        user = self.get_by_id(user_id)
        if not user:
            return None

        user.is_locked = False
        user.locked_at = None
        user.locked_reason = None

        return self.update(user)
