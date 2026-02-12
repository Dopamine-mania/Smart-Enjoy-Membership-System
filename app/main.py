"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.utils.redis_client import redis_client
from app.middleware.error_handler import error_handler_middleware
from app.middleware.request_id import request_id_middleware
from app.api.v1 import auth, members, points, benefits, orders, admin


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
