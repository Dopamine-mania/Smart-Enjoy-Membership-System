import os
import time
from dataclasses import dataclass
from typing import Any, Optional

import pytest


# Ensure settings are loaded with test-friendly defaults before importing app modules.
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:////tmp/membership_test.db")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")


@dataclass
class _Value:
    value: str
    expires_at: Optional[float] = None


class FakeRedis:
    def __init__(self):
        self._store: dict[str, _Value] = {}

    def close(self) -> None:
        return None

    def _now(self) -> float:
        return time.time()

    def _is_expired(self, key: str) -> bool:
        item = self._store.get(key)
        if not item:
            return True
        if item.expires_at is None:
            return False
        return self._now() >= item.expires_at

    def _purge_if_expired(self, key: str) -> None:
        if key in self._store and self._is_expired(key):
            del self._store[key]

    def get(self, key: str) -> Optional[str]:
        self._purge_if_expired(key)
        item = self._store.get(key)
        return item.value if item else None

    def set(self, key: str, value: str, ex: int = None) -> bool:
        expires_at = self._now() + ex if ex else None
        self._store[key] = _Value(str(value), expires_at)
        return True

    def delete(self, key: str) -> int:
        existed = 1 if key in self._store else 0
        self._store.pop(key, None)
        return existed

    def incr(self, key: str) -> int:
        self._purge_if_expired(key)
        current = int(self.get(key) or "0")
        new_val = current + 1
        expires_at = self._store.get(key).expires_at if key in self._store else None
        self._store[key] = _Value(str(new_val), expires_at)
        return new_val

    def expire(self, key: str, seconds: int) -> bool:
        self._purge_if_expired(key)
        if key not in self._store:
            return False
        self._store[key].expires_at = self._now() + seconds
        return True

    def ttl(self, key: str) -> int:
        self._purge_if_expired(key)
        item = self._store.get(key)
        if not item:
            return -2
        if item.expires_at is None:
            return -1
        return max(int(item.expires_at - self._now()), -2)

    def exists(self, key: str) -> int:
        self._purge_if_expired(key)
        return 1 if key in self._store else 0

    def setnx(self, key: str, value: str) -> bool:
        self._purge_if_expired(key)
        if key in self._store:
            return False
        self._store[key] = _Value(str(value), None)
        return True


@pytest.fixture(scope="session")
def fake_redis() -> FakeRedis:
    return FakeRedis()


@pytest.fixture(autouse=True)
def _patch_redis(fake_redis, monkeypatch):
    from app.utils.redis_client import redis_client

    # Prevent real connections in tests.
    monkeypatch.setattr(redis_client, "connect", lambda: None)
    monkeypatch.setattr(redis_client, "disconnect", lambda: None)
    redis_client._client = fake_redis
    yield
    # Keep fake redis for inspection across a test if needed.


@pytest.fixture(autouse=True)
def _reset_db():
    # Import after env vars are set.
    from app.db.session import Base, engine

    # Ensure all models are registered in metadata.
    from app.models import admin  # noqa: F401
    from app.models import benefit  # noqa: F401
    from app.models import order  # noqa: F401
    from app.models import point_transaction  # noqa: F401
    from app.models import user  # noqa: F401

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def app():
    from app.main import app as fastapi_app

    return fastapi_app

