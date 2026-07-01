"""Async SQLAlchemy engine, session factory, and DB lifecycle helpers.

Engine and session factory are created lazily so that tests can override
``DATABASE_URL`` before any connection is established.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

# ---------------------------------------------------------------------------
# Declarative base
# ---------------------------------------------------------------------------


class Base(DeclarativeBase):
    """SQLAlchemy 2.x declarative base shared by all models."""


# ---------------------------------------------------------------------------
# Lazy engine / session factory
# ---------------------------------------------------------------------------

_engine = None
_async_session_factory = None


def get_engine():
    """Return the global async engine, creating it on first call."""
    global _engine  # noqa: PLW0603
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            pool_pre_ping=True,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the global session factory, creating it on first call."""
    global _async_session_factory  # noqa: PLW0603
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session_factory


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an ``AsyncSession`` that auto-commits on success and rolls back on error."""
    async with get_session_factory()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ---------------------------------------------------------------------------
# Lifecycle helpers
# ---------------------------------------------------------------------------


async def init_db() -> None:
    """Create all tables — use for testing only. Production uses Alembic."""
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def reset_engine() -> None:
    """Tear down engine and session factory so the next call re-creates them.

    Used in tests to swap the database URL between runs.
    """
    global _engine, _async_session_factory  # noqa: PLW0603
    _engine = None
    _async_session_factory = None
