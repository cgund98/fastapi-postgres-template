"""SQL transaction manager implementation."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncConnection

from app.infrastructure.db.transaction import TransactionManager
from app.observability.logging import get_logger

logger = get_logger(__name__)


class SQLTransactionManager(TransactionManager):
    """SQL implementation of TransactionManager using SQLAlchemy."""

    def __init__(self, conn: AsyncConnection) -> None:
        """Initialize with a SQLAlchemy connection."""
        self.conn = conn

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[None, Exception | None]:
        """
        Context manager that will commit transactions or roll back if an exception is raised.
        """
        async with self.conn.begin():
            try:
                yield
                await self.conn.commit()
            except Exception as ex:
                logger.debug("Encountered exception when handling transaction. Rolling back transaction...")
                await self.conn.rollback()
                raise ex
