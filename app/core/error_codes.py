"""Error code definitions for unified error responses."""

class ErrorCode:
    # Authentication errors (1xxx)
    INVALID_VERIFICATION_CODE = ("INVALID_VERIFICATION_CODE", "验证码无效或已过期")
    VERIFICATION_CODE_RATE_LIMIT = ("VERIFICATION_CODE_RATE_LIMIT", "验证码发送过于频繁，请稍后再试")
    ACCOUNT_LOCKED = ("ACCOUNT_LOCKED", "账户已被锁定，请稍后再试")
    LOGIN_FAILED = ("LOGIN_FAILED", "登录失败，请检查邮箱和验证码")
    INVALID_TOKEN = ("INVALID_TOKEN", "无效的访问令牌")
    TOKEN_EXPIRED = ("TOKEN_EXPIRED", "访问令牌已过期")
    TOKEN_BLACKLISTED = ("TOKEN_BLACKLISTED", "访问令牌已失效")
    UNAUTHORIZED = ("UNAUTHORIZED", "未授权访问")

    # User errors (2xxx)
    USER_NOT_FOUND = ("USER_NOT_FOUND", "用户不存在")
    USER_ALREADY_EXISTS = ("USER_ALREADY_EXISTS", "用户已存在")
    INSUFFICIENT_POINTS = ("INSUFFICIENT_POINTS", "积分不足")

    # Permission errors (3xxx)
    PERMISSION_DENIED = ("PERMISSION_DENIED", "权限不足")
    ADMIN_NOT_FOUND = ("ADMIN_NOT_FOUND", "管理员不存在")

    # Resource errors (4xxx)
    RESOURCE_NOT_FOUND = ("RESOURCE_NOT_FOUND", "资源不存在")
    BENEFIT_NOT_FOUND = ("BENEFIT_NOT_FOUND", "权益不存在")
    ORDER_NOT_FOUND = ("ORDER_NOT_FOUND", "订单不存在")

    # Business logic errors (5xxx)
    BENEFIT_ALREADY_DISTRIBUTED = ("BENEFIT_ALREADY_DISTRIBUTED", "权益已发放")
    IDEMPOTENCY_CONFLICT = ("IDEMPOTENCY_CONFLICT", "操作已执行，请勿重复提交")

    # Validation errors (6xxx)
    INVALID_INPUT = ("INVALID_INPUT", "输入参数无效")
    INVALID_EMAIL = ("INVALID_EMAIL", "邮箱格式无效")

    # System errors (9xxx)
    INTERNAL_ERROR = ("INTERNAL_ERROR", "系统内部错误")
    DATABASE_ERROR = ("DATABASE_ERROR", "数据库错误")
    REDIS_ERROR = ("REDIS_ERROR", "缓存服务错误")


class BusinessException(Exception):
    """Business logic exception with error code."""

    def __init__(self, error_code: tuple[str, str], details: str = None):
        self.code = error_code[0]
        self.message = error_code[1]
        self.details = details
        super().__init__(self.message)
