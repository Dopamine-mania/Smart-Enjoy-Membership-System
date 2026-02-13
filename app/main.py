"""Main FastAPI application."""
import uuid
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    redis_client.connect()
    print("✓ Redis connected")

    yield

    # Shutdown
    redis_client.disconnect()
    print("✓ Redis disconnected")


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
