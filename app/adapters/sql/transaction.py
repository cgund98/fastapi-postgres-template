"""SQL transaction manager implementation."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from app.adapters.sql.context import SQLContext
from app.adapters.sql.pool import AsyncpgPool
from app.observability.logging import get_logger

logger = get_logger(__name__)


class SQLTransactionManager:
    """SQL implementation of TransactionManager using SQLModel."""

    def __init__(self, db_pool: AsyncpgPool) -> None:
        """Initialize with a database pool."""
        self._db_pool = db_pool

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[SQLContext, Exception | None]:
        """
        Context manager that creates a new session for each transaction.
        Yields the session as the database context.
        Commits on success or rolls back if an exception is raised.
        """
        async with self._db_pool.get_connection() as connection, connection.transaction():
            yield SQLContext(connection=connection)
