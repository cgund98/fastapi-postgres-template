"""PostgreSQL connection pool management."""

import asyncpg

from app.config.settings import Settings


class PostgresPool:
    """Manages PostgreSQL connection pool."""

    _pool: asyncpg.Pool | None = None

    @classmethod
    async def create_pool(cls, settings: Settings) -> asyncpg.Pool:
        """Create and return a connection pool."""
        if cls._pool is None:
            cls._pool = await asyncpg.create_pool(
                host=settings.postgres_host,
                port=settings.postgres_port,
                user=settings.postgres_user,
                password=settings.postgres_password,
                database=settings.postgres_database,
                min_size=settings.postgres_min_pool_size,
                max_size=settings.postgres_max_pool_size,
            )
        return cls._pool

    @classmethod
    async def close_pool(cls) -> None:
        """Close the connection pool."""
        if cls._pool is not None:
            await cls._pool.close()
            cls._pool = None

    @classmethod
    def get_pool(cls) -> asyncpg.Pool:
        """Get the current pool. Raises if pool not initialized."""
        if cls._pool is None:
            raise RuntimeError("Pool not initialized. Call create_pool first.")
        return cls._pool
