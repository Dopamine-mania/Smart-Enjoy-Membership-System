"""Database session management."""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import StaticPool
from app.config import settings

database_url = settings.DATABASE_URL
is_sqlite = database_url.startswith("sqlite")

# Create engine
engine_kwargs = {"pool_pre_ping": True}
if is_sqlite:
    # SQLite is used for local/unit tests; keep configuration compatible.
    engine_kwargs.update(
        connect_args={"check_same_thread": False},
    )
    if database_url.endswith(":memory:"):
        engine_kwargs["poolclass"] = StaticPool
else:
    engine_kwargs.update(pool_size=10, max_overflow=20)

engine = create_engine(database_url, **engine_kwargs)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
