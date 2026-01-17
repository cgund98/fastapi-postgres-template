"""SQLModel database session management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from app.config.settings import Settings


class SQLAlchemyPool:
    """Manages SQLModel database session pool with lifecycle."""

    def __init__(self, settings: Settings) -> None:
        """Initialize the database pool with settings."""
        # Use asyncpg driver with SQLAlchemy
        database_url = (
            f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}"
            f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_database}"
        )
        self._engine = create_async_engine(
            database_url,
            pool_size=settings.postgres_min_pool_size,
            max_overflow=settings.postgres_max_pool_size - settings.postgres_min_pool_size,
            pool_pre_ping=True,
            echo=False,
        )

    @property
    def engine(self) -> AsyncEngine:
        """Get the database engine."""
        return self._engine

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an async session from the engine."""
        async with AsyncSession(self._engine, expire_on_commit=False) as session:
            yield session

    async def close(self) -> None:
        """Close the database engine and dispose of connections."""
        await self._engine.dispose()
