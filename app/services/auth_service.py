"""Authentication service."""
from datetime import timedelta
import logging
from sqlalchemy.orm import Session
from app.core.security import generate_verification_code, create_access_token, verify_password, hash_password
from app.core.rate_limiter import RateLimiter
from app.core.error_codes import ErrorCode, BusinessException
from app.utils.redis_client import redis_client
from app.config import settings
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.benefit_service import BenefitService


logger = logging.getLogger(__name__)


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

        # Development-only mock: print verification code to stdout for manual testing.
        # Never return the code in API responses.
        if settings.APP_ENV in ("development", "test"):
            logger.info("[MOCK EMAIL] Verification code for %s: %s", email, code)
        else:
            # Pure mock implementation: do not send or print plaintext code in production.
            logger.info("Verification code generated for %s (delivery not configured)", email)

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

        # Auto-distribute monthly benefits for new user (best-effort).
        try:
            BenefitService(self.db).distribute_current_monthly_benefits(user.id)
        except Exception:
            pass

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

        # Auto-distribute monthly benefits on login (best-effort).
        try:
            BenefitService(self.db).distribute_current_monthly_benefits(user.id)
        except Exception:
            pass

        # Create access token
        access_token, jti = create_access_token(subject_id=user.id, role="user")

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
