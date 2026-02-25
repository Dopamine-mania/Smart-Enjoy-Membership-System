"""Member service for user profile operations."""

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UpdateProfileRequest


class MemberService:
    """Member service."""

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def update_profile(self, current_user: User, request: UpdateProfileRequest) -> User:
        """Update current user's profile fields."""
        if request.nickname is not None:
            current_user.nickname = request.nickname

        if request.avatar_url is not None:
            current_user.avatar_url = request.avatar_url

        if request.gender is not None:
            current_user.gender = request.gender

        if request.birthday is not None:
            current_user.birthday = request.birthday

        return self.user_repo.update(current_user)

