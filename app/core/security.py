"""Security utilities for JWT and password hashing."""
from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings
from app.core.error_codes import ErrorCode, BusinessException

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: int, expires_delta: Optional[timedelta] = None) -> tuple[str, str]:
    """
    Create JWT access token.

    Returns:
        Tuple of (token, jti)
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRY_HOURS)

    jti = str(uuid.uuid4())

    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "jti": jti,
        "iat": datetime.now(timezone.utc)
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt, jti


def decode_access_token(token: str) -> dict:
    """
    Decode and validate JWT token.

    Raises:
        BusinessException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        if "expired" in str(e).lower():
            raise BusinessException(ErrorCode.TOKEN_EXPIRED)
        raise BusinessException(ErrorCode.INVALID_TOKEN)


def generate_verification_code() -> str:
    """Generate random verification code."""
    import random
    code_length = settings.VERIFICATION_CODE_LENGTH
    return ''.join([str(random.randint(0, 9)) for _ in range(code_length)])
