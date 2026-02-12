"""Rate limiting utilities."""
from app.utils.redis_client import redis_client
from app.config import settings
from app.core.error_codes import ErrorCode, BusinessException


class RateLimiter:
    """Rate limiter using Redis."""

    @staticmethod
    def check_verification_code_rate_limit(email: str) -> None:
        """
        Check verification code rate limit.

        Raises:
            BusinessException: If rate limit exceeded
        """
        # Check minute limit
        minute_key = f"rate_limit:verification:{email}:minute"
        minute_count = redis_client.get(minute_key)

        if minute_count and int(minute_count) >= settings.VERIFICATION_CODE_RATE_LIMIT_MINUTE:
            raise BusinessException(ErrorCode.VERIFICATION_CODE_RATE_LIMIT)

        # Check day limit
        day_key = f"rate_limit:verification:{email}:day"
        day_count = redis_client.get(day_key)

        if day_count and int(day_count) >= settings.VERIFICATION_CODE_RATE_LIMIT_DAY:
            raise BusinessException(ErrorCode.VERIFICATION_CODE_RATE_LIMIT)

    @staticmethod
    def increment_verification_code_counter(email: str) -> None:
        """Increment verification code counters."""
        # Increment minute counter
        minute_key = f"rate_limit:verification:{email}:minute"
        count = redis_client.incr(minute_key)
        if count == 1:
            redis_client.expire(minute_key, 60)

        # Increment day counter
        day_key = f"rate_limit:verification:{email}:day"
        count = redis_client.incr(day_key)
        if count == 1:
            redis_client.expire(day_key, 86400)

    @staticmethod
    def check_account_lock(email: str) -> None:
        """
        Check if account is locked.

        Raises:
            BusinessException: If account is locked
        """
        lock_key = f"account_locked:{email}"
        if redis_client.exists(lock_key):
            raise BusinessException(ErrorCode.ACCOUNT_LOCKED)

    @staticmethod
    def increment_login_failure(email: str) -> int:
        """
        Increment login failure counter.

        Returns:
            Current failure count
        """
        failure_key = f"login_failures:{email}"
        count = redis_client.incr(failure_key)

        if count == 1:
            redis_client.expire(failure_key, settings.LOGIN_LOCK_MINUTES * 60)

        # Lock account if threshold exceeded
        if count >= settings.LOGIN_FAILURE_LIMIT:
            lock_key = f"account_locked:{email}"
            redis_client.set(lock_key, "1", ex=settings.LOGIN_LOCK_MINUTES * 60)

        return count

    @staticmethod
    def reset_login_failure(email: str) -> None:
        """Reset login failure counter."""
        failure_key = f"login_failures:{email}"
        redis_client.delete(failure_key)
