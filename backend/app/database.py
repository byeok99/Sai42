"""Database metadata and asynchronous session factory."""

import os
from collections.abc import AsyncIterator

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/sai42.db")


class Base(DeclarativeBase):
    """Base class shared by all SQLAlchemy models."""


engine = create_async_engine(DATABASE_URL)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection: object, _: object) -> None:
    """Enable SQLite foreign-key enforcement for every connection."""
    cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
    finally:
        cursor.close()


async def get_database_session() -> AsyncIterator[AsyncSession]:
    """Yield one request-scoped asynchronous database session."""
    async with async_session_factory() as session:
        yield session
