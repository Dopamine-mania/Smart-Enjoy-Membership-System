"""Authentication middleware."""
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import decode_access_token
from app.core.error_codes import ErrorCode, BusinessException
from app.services.auth_service import AuthService
from app.db.session import get_db
from app.repositories.user_repository import UserRepository
from app.repositories.admin_repository import AdminRepository
from sqlalchemy.orm import Session


security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """
    Get current authenticated user from JWT token.

    Raises:
        HTTPException: If token is invalid or user not found
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": ErrorCode.UNAUTHORIZED[0], "message": ErrorCode.UNAUTHORIZED[1]},
        )

    token = credentials.credentials

    try:
        # Decode token
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))
        jti = payload.get("jti")

        # Check if token is blacklisted
        auth_service = AuthService(db)

        if auth_service.is_token_blacklisted(jti):
            raise BusinessException(ErrorCode.TOKEN_BLACKLISTED)

        # Get user
        user_repo = UserRepository(db)
        user = user_repo.get_by_id(user_id)

        if not user:
            raise BusinessException(ErrorCode.USER_NOT_FOUND)

        # Check if user is locked
        if user.is_locked:
            raise BusinessException(ErrorCode.ACCOUNT_LOCKED)

        # Store in request state
        request.state.user = user
        request.state.jti = jti
        request.state.token_exp = payload.get("exp")

        return user

    except BusinessException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": e.code, "message": e.message},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": ErrorCode.INVALID_TOKEN[0], "message": ErrorCode.INVALID_TOKEN[1]},
        )


async def get_current_admin(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """
    Get current authenticated admin from JWT token.

    Raises:
        HTTPException: If token is invalid or admin not found
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": ErrorCode.UNAUTHORIZED[0], "message": ErrorCode.UNAUTHORIZED[1]},
        )

    token = credentials.credentials

    try:
        # Decode token
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))

        # Admin tokens have negative user_id
        if user_id >= 0:
            raise BusinessException(ErrorCode.PERMISSION_DENIED)

        admin_id = abs(user_id)

        # Get admin
        admin_repo = AdminRepository(db)
        admin = admin_repo.get_admin_by_id(admin_id)

        if not admin:
            raise BusinessException(ErrorCode.ADMIN_NOT_FOUND)

        # Check if active
        if not admin.is_active:
            raise BusinessException(ErrorCode.ACCOUNT_LOCKED)

        # Store in request state
        request.state.admin = admin

        return admin

    except BusinessException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": e.code, "message": e.message},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": ErrorCode.INVALID_TOKEN[0], "message": ErrorCode.INVALID_TOKEN[1]},
        )
