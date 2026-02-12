"""Authentication service."""
import random
from datetime import timedelta
from sqlalchemy.orm import Session
from app.core.security import generate_verification_code, create_access_token, verify_password, hash_password
from app.core.rate_limiter import RateLimiter
from app.core.error_codes import ErrorCode, BusinessException
from app.utils.redis_client import redis_client
from app.config import settings
from app.models.user import User
from app.repositories.user_repository import UserRepository


class AuthService:
    """Authentication service."""

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def send_verification_code(self, email: str, purpose: str) -> str:
        """
        Send verification code to email.

        Args:
            email: User email
            purpose: "register" or "login"

        Returns:
            Verification code (for mock implementation)
        """
        # Check rate limit
        RateLimiter.check_verification_code_rate_limit(email)

        # Generate code
        code = generate_verification_code()

        # Store in Redis
        key = f"verification_code:{email}:{purpose}"
        redis_client.set(key, code, ex=settings.VERIFICATION_CODE_EXPIRY_MINUTES * 60)

        # Increment rate limit counters
        RateLimiter.increment_verification_code_counter(email)

        # TODO: Send real email via SMTP
        # For now, just log it
        print(f"[MOCK EMAIL] Verification code for {email}: {code}")

        return code

    def verify_code(self, email: str, code: str, purpose: str) -> bool:
        """
        Verify verification code.

        Args:
            email: User email
            code: Verification code
            purpose: "register" or "login"

        Returns:
            True if valid
        """
        key = f"verification_code:{email}:{purpose}"
        stored_code = redis_client.get(key)

        if not stored_code or stored_code != code:
            return False

        # Delete code after verification
        redis_client.delete(key)
        return True

    def register(self, email: str, code: str, nickname: str = None) -> User:
        """
        Register new user.

        Args:
            email: User email
            code: Verification code
            nickname: Optional nickname

        Returns:
            Created user

        Raises:
            BusinessException: If code invalid or user exists
        """
        # Verify code
        if not self.verify_code(email, code, "register"):
            raise BusinessException(ErrorCode.INVALID_VERIFICATION_CODE)

        # Check if user exists
        existing_user = self.user_repo.get_by_email(email)
        if existing_user:
            raise BusinessException(ErrorCode.USER_ALREADY_EXISTS)

        # Create user
        user = self.user_repo.create(email=email, nickname=nickname)
        return user

    def login(self, email: str, code: str) -> tuple[str, User]:
        """
        Login user.

        Args:
            email: User email
            code: Verification code

        Returns:
            Tuple of (access_token, user)

        Raises:
            BusinessException: If code invalid or account locked
        """
        # Check account lock
        RateLimiter.check_account_lock(email)

        # Verify code
        if not self.verify_code(email, code, "login"):
            # Increment failure counter
            RateLimiter.increment_login_failure(email)
            raise BusinessException(ErrorCode.INVALID_VERIFICATION_CODE)

        # Get user
        user = self.user_repo.get_by_email(email)
        if not user:
            RateLimiter.increment_login_failure(email)
            raise BusinessException(ErrorCode.USER_NOT_FOUND)

        # Check if user is locked
        if user.is_locked:
            raise BusinessException(ErrorCode.ACCOUNT_LOCKED)

        # Reset login failure counter
        RateLimiter.reset_login_failure(email)

        # Create access token
        access_token, jti = create_access_token(user.id)

        return access_token, user

    def logout(self, token: str, jti: str, exp: int) -> None:
        """
        Logout user by blacklisting token.

        Args:
            token: JWT token
            jti: Token ID
            exp: Token expiration timestamp
        """
        from datetime import datetime, timezone

        # Calculate remaining TTL
        now = datetime.now(timezone.utc).timestamp()
        ttl = int(exp - now)

        if ttl > 0:
            # Add to blacklist
            key = f"jwt_blacklist:{jti}"
            redis_client.set(key, "1", ex=ttl)

    def is_token_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted."""
        key = f"jwt_blacklist:{jti}"
        return redis_client.exists(key)
