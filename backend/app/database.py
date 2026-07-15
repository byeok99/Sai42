"""Database metadata and asynchronous session factory."""

from collections.abc import AsyncIterator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()


class Base(DeclarativeBase):
    """Base class shared by all SQLAlchemy models."""


engine = create_async_engine(
    settings.database_url,
    connect_args={"timeout": settings.sqlite_busy_timeout_ms / 1000},
    hide_parameters=True,
)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


@event.listens_for(engine.sync_engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection: object, _: object) -> None:
    """Apply required SQLite connection policies."""
    cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute(f"PRAGMA busy_timeout={settings.sqlite_busy_timeout_ms}")
    finally:
        cursor.close()


async def get_database_session() -> AsyncIterator[AsyncSession]:
    """Yield one request-scoped asynchronous database session."""
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def dispose_database_engine() -> None:
    """Release pooled connections during application shutdown."""
    await engine.dispose()
