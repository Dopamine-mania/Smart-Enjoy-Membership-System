"""Authentication API endpoints."""
from fastapi import APIRouter, Depends, Request
from app.schemas.user import (
    VerificationCodeRequest,
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserProfileResponse
)
from app.schemas.common import SuccessResponse
from app.services.auth_service import AuthService
from app.dependencies import get_auth_service
from app.middleware.auth import get_current_user, security
from app.config import settings
from app.utils.timezone_utils import to_beijing_time
from app.utils.data_masking import mask_email

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/send-code", response_model=SuccessResponse)
async def send_verification_code(
    request: VerificationCodeRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Send verification code to email."""
    code = auth_service.send_verification_code(request.email, request.purpose)

    return SuccessResponse(
        message="验证码已发送",
        data={"code": code}  # For testing only, remove in production
    )


@router.post("/register", response_model=TokenResponse)
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register new user."""
    user = auth_service.register(request.email, request.code, request.nickname)

    # Create access token
    from app.core.security import create_access_token
    access_token, jti = create_access_token(user.id)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_EXPIRY_HOURS * 3600
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Login user."""
    access_token, user = auth_service.login(request.email, request.code)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_EXPIRY_HOURS * 3600
    )


@router.post("/logout", response_model=SuccessResponse)
async def logout(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    current_user = Depends(get_current_user),
    credentials = Depends(security)
):
    """Logout user."""
    token = credentials.credentials
    jti = request.state.jti
    exp = request.state.token_exp

    auth_service.logout(token, jti, exp)

    return SuccessResponse(message="登出成功")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    current_user = Depends(get_current_user)
):
    """Refresh access token."""
    from app.core.security import create_access_token

    access_token, jti = create_access_token(current_user.id)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_EXPIRY_HOURS * 3600
    )
