"""Main FastAPI application."""
import uuid
import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
from app.config import settings
from app.utils.redis_client import redis_client
from app.middleware.error_handler import error_handler_middleware
from app.middleware.request_id import request_id_middleware
from app.api.v1 import auth, members, points, benefits, orders, admin
from app.core.error_codes import ErrorCode
from app.core.logging_config import setup_logging


setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    if settings.APP_ENV == "production" and settings.ADMIN_PASSWORD == "admin123":
        logger.critical("\033[91m[CRITICAL] Production mode detected with default admin password! Server refusal to start.\033[0m")
        raise RuntimeError("Refusing to start in production with default ADMIN_PASSWORD. Set ADMIN_PASSWORD to a strong value.")

    if settings.APP_ENV == "production" and settings.JWT_SECRET_KEY == "your-secret-key-change-in-production":
        raise RuntimeError("Refusing to start in production with default JWT_SECRET_KEY. Set JWT_SECRET_KEY to a strong value.")

    if settings.APP_ENV == "production":
        # Extra safeguard: refuse to start if database still contains default admin password hash.
        # Default hash corresponds to "admin123" in docker/init-db.sql.
        default_admin_hash = "$2b$12$fluRnLYsajPpXfV6QMKdfOURBjxZxf3GJ3KEEY.BznQaAHkbQ9HWO"
        try:
            from sqlalchemy import text
            from app.db.session import engine

            with engine.connect() as conn:
                row = conn.execute(
                    text("SELECT password_hash FROM admin_users WHERE username='admin' LIMIT 1")
                ).fetchone()
                if row and row[0] == default_admin_hash:
                    logger.critical("\033[91m[CRITICAL] Production mode detected with default admin password! Server refusal to start.\033[0m")
                    raise RuntimeError("Refusing to start in production with default admin password hash in database. Change admin password.")
        except RuntimeError:
            raise
        except Exception:
            # Any database access issue in production is treated as fatal for safety.
            logger.critical("\033[91m[CRITICAL] Production mode admin password validation failed! Server refusal to start.\033[0m")
            raise

    # Startup
    if settings.APP_ENV != "test":
        redis_client.connect()
        logger.info("Redis connected")

    yield

    # Shutdown
    if settings.APP_ENV != "test":
        redis_client.disconnect()
        logger.info("Redis disconnected")


# Create FastAPI app
app = FastAPI(
    title="智享会员系统",
    description="Comprehensive membership system with authentication, points, benefits, and admin management",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.middleware("http")(request_id_middleware)
app.middleware("http")(error_handler_middleware)

# Exception handlers
@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return unified error format for request validation errors."""
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "code": ErrorCode.INVALID_INPUT[0],
            "message": ErrorCode.INVALID_INPUT[1],
            "trace_id": trace_id,
            "details": exc.errors(),
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Return unified error format for HTTP errors (auth, 404, etc.)."""
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))

    code = None
    message = None
    details = None

    if isinstance(exc.detail, dict):
        code = exc.detail.get("code")
        message = exc.detail.get("message")
        details = exc.detail.get("details")

    if not code or not message:
        if exc.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN):
            code, message = ErrorCode.UNAUTHORIZED
        elif exc.status_code == status.HTTP_404_NOT_FOUND:
            code, message = ErrorCode.RESOURCE_NOT_FOUND
        else:
            code, message = ErrorCode.INVALID_INPUT

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": code,
            "message": message,
            "trace_id": trace_id,
            "details": details,
        },
    )

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(members.router, prefix="/api/v1")
app.include_router(points.router, prefix="/api/v1")
app.include_router(benefits.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "智享会员系统 API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
