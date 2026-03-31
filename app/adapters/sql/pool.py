"""Asyncpg database pool management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import asyncpg
from asyncpg.pool import Pool, PoolConnectionProxy

from app.config.settings import Settings


class AsyncpgPool:
    """Manages asyncpg database pool with lifecycle."""

    def __init__(self, settings: Settings) -> None:
        self._dsn = (
            f"postgresql://{settings.postgres_user}:{settings.postgres_password}"
            f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_database}"
        )
        self._min_size = settings.postgres_min_pool_size
        self._max_size = settings.postgres_max_pool_size
        self._pool: Pool | None = None

    @property
    def pool(self) -> Pool:
        if self._pool is None:
            raise RuntimeError("Pool not connected — call connect() first")
        return self._pool

    async def connect(self) -> None:
        """Create the connection pool. Must be called before use."""
        self._pool = await asyncpg.create_pool(
            self._dsn,
            min_size=self._min_size,
            max_size=self._max_size,
        )

    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[PoolConnectionProxy, None]:
        """Acquire a connection from the pool."""
        async with self.pool.acquire() as connection:
            yield connection

    async def close(self) -> None:
        """Close the database pool and dispose of connections."""
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
