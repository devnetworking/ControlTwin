"""Async PostgreSQL database setup and utilities."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_postgres_dsn
from app.models.models import Base

engine = create_async_engine(get_postgres_dsn(), pool_pre_ping=True, future=True)
SessionLocal = async_sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=AsyncSession)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield async DB session dependency."""
    async with SessionLocal() as session:
        yield session


async def init_db() -> None:
    """Initialize database schema."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def check_db_health() -> tuple[bool, str]:
    """Check PostgreSQL health."""
    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return True, "ok"
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)
