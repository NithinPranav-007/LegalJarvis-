"""Database session management and engine configuration."""

import os
from collections.abc import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


# Base declarative class
class Base(DeclarativeBase):
    pass


# Async engine for FastAPI requests
DATABASE_URL = os.getenv("DATABASE_URL", settings.DATABASE_URL)
if DATABASE_URL.startswith("sqlite:///"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")
else:
    ASYNC_DATABASE_URL = DATABASE_URL

try:
    async_engine = create_async_engine(
        ASYNC_DATABASE_URL,
        echo=settings.DEBUG,
        pool_pre_ping=True,
    )
    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
except Exception:
    async_engine = None  # type: ignore[assignment]
    async_session_maker = None  # type: ignore[assignment]
# Synchronous engine for Alembic migrations and CLI jobs
if os.getenv("SYNC_DATABASE_URL"):
    SYNC_DATABASE_URL = os.environ["SYNC_DATABASE_URL"]
elif DATABASE_URL.startswith("sqlite"):
    SYNC_DATABASE_URL = DATABASE_URL
else:
    SYNC_DATABASE_URL = settings.SYNC_DATABASE_URL

sync_connect_args = {"check_same_thread": False} if SYNC_DATABASE_URL.startswith("sqlite") else {}

sync_engine = create_engine(
    SYNC_DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    connect_args=sync_connect_args,
)

sync_session_maker = sessionmaker(
    sync_engine,
    expire_on_commit=False,
)


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an async database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
