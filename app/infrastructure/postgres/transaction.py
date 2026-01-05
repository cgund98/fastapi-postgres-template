"""PostgreSQL transaction manager implementation."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from asyncpg.pool import PoolConnectionProxy

from app.infrastructure.db.transaction import TransactionManager
from app.infrastructure.postgres.pool import PostgresPool
from app.observability.logging import get_logger

logger = get_logger(__name__)


class PostgresTransactionManager(TransactionManager):
    """PostgreSQL implementation of TransactionManager."""

    def __init__(self, conn: PoolConnectionProxy) -> None:
        """Initialize with a connection from a pool."""
        self.conn = conn
        self._released = False

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[None, Exception | None]:
        """
        Context manager that will commit transactions or roll back if an exception is raised.
        """
        tx = self.conn.transaction()
        await tx.start()
        try:
            yield
            await tx.commit()
        except Exception as ex:
            logger.debug("Encountered exception when handling transaction. Rolling back transaction...")
            await tx.rollback()
            raise ex
        finally:
            # Release connection back to pool
            if not self._released:
                pool = PostgresPool.get_pool()
                await pool.release(self.conn)
                self._released = True

    @property
    def connection(self) -> PoolConnectionProxy:
        """Get the current connection."""
        return self.conn
