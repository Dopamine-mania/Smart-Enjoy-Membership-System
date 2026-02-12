"""Member API endpoints."""
from fastapi import APIRouter, Depends
from app.schemas.user import UserProfileResponse, UpdateProfileRequest
from app.middleware.auth import get_current_user
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.db.session import get_db
from sqlalchemy.orm import Session
from app.utils.timezone_utils import to_beijing_time
from app.utils.data_masking import mask_email, mask_id_card

router = APIRouter(prefix="/members", tags=["Members"])


@router.get("/me", response_model=UserProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user profile."""
    return UserProfileResponse(
        id=current_user.id,
        email=mask_email(current_user.email),
        nickname=current_user.nickname,
        avatar_url=current_user.avatar_url,
        gender=current_user.gender,
        birthday=to_beijing_time(current_user.birthday),
        id_card_last_four=current_user.id_card_last_four,
        member_level=current_user.member_level,
        available_points=current_user.available_points,
        total_earned_points=current_user.total_earned_points,
        created_at=to_beijing_time(current_user.created_at)
    )


@router.patch("/me", response_model=UserProfileResponse)
async def update_profile(
    request: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile."""
    user_repo = UserRepository(db)

    # Update fields
    if request.nickname is not None:
        current_user.nickname = request.nickname

    if request.avatar_url is not None:
        current_user.avatar_url = request.avatar_url

    if request.gender is not None:
        current_user.gender = request.gender

    if request.birthday is not None:
        current_user.birthday = request.birthday

    # Save changes
    user_repo.update(current_user)

    return UserProfileResponse(
        id=current_user.id,
        email=mask_email(current_user.email),
        nickname=current_user.nickname,
        avatar_url=current_user.avatar_url,
        gender=current_user.gender,
        birthday=to_beijing_time(current_user.birthday),
        id_card_last_four=current_user.id_card_last_four,
        member_level=current_user.member_level,
        available_points=current_user.available_points,
        total_earned_points=current_user.total_earned_points,
        created_at=to_beijing_time(current_user.created_at)
    )
