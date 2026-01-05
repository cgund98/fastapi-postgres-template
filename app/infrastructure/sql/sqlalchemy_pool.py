"""SQLAlchemy database connection pool management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import ClassVar

from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine

from app.config.settings import Settings


class SQLAlchemyPool:
    """Manages SQLAlchemy database connection pool."""

    _engine: ClassVar[AsyncEngine | None] = None

    @classmethod
    def create_engine(cls, settings: Settings) -> AsyncEngine:
        """Create and return a SQLAlchemy async engine."""
        if cls._engine is None:
            # Use asyncpg driver with SQLAlchemy
            database_url = (
                f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}"
                f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_database}"
            )
            cls._engine = create_async_engine(
                database_url,
                pool_size=settings.postgres_min_pool_size,
                max_overflow=settings.postgres_max_pool_size - settings.postgres_min_pool_size,
                pool_pre_ping=True,
                echo=False,
            )
        return cls._engine

    @classmethod
    async def close_engine(cls) -> None:
        """Close the SQLAlchemy engine."""
        if cls._engine is not None:
            await cls._engine.dispose()
            cls._engine = None

    @classmethod
    def get_engine(cls) -> AsyncEngine:
        """Get the current engine. Raises if engine not initialized."""
        if cls._engine is None:
            raise RuntimeError("Engine not initialized. Call create_engine first.")
        return cls._engine

    @classmethod
    @asynccontextmanager
    async def get_connection(cls) -> AsyncGenerator[AsyncConnection, None]:
        """Get a connection from the engine."""
        engine = cls.get_engine()
        async with engine.connect() as conn:
            yield conn
