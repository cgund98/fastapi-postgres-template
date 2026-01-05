"""Shared FastAPI dependencies."""

from collections.abc import AsyncGenerator

from asyncpg.pool import PoolConnectionProxy
from fastapi import Depends

from app.config.settings import Settings, get_settings
from app.domain.billing.invoice.repo.pg import InvoiceRepository
from app.domain.billing.invoice.service import InvoiceService
from app.domain.user.repo.pg import UserRepository
from app.infrastructure.messaging.publisher import EventPublisher, SNSPublisher
from app.infrastructure.postgres.pool import PostgresPool
from app.infrastructure.postgres.transaction import PostgresTransactionManager


async def get_db_connection() -> AsyncGenerator[PoolConnectionProxy, None]:
    """Get a database connection from the pool."""
    pool = PostgresPool.get_pool()
    connection = await pool.acquire()
    try:
        yield connection
    finally:
        # Release connection back to pool
        # Note: If a transaction manager was used, it may have already released the connection
        # asyncpg's pool.release() handles already-released connections gracefully
        await pool.release(connection)


def get_event_publisher(settings: Settings = Depends(get_settings)) -> EventPublisher:
    """Get event publisher instance."""

    topic_arn = settings.default_event_topic_arn
    if not topic_arn:
        raise ValueError("Default event topic ARN must be configured")

    sns_publisher = SNSPublisher(settings, topic_arn)
    return EventPublisher(sns_publisher)


def get_transaction_manager(
    connection: PoolConnectionProxy = Depends(get_db_connection),
) -> PostgresTransactionManager:
    """Get a transaction manager for the given connection."""
    return PostgresTransactionManager(connection)


def get_user_repository(
    connection: PoolConnectionProxy = Depends(get_db_connection),
) -> UserRepository:
    """Get a user repository for the given connection."""
    return UserRepository(connection)


def get_invoice_repository(
    connection: PoolConnectionProxy = Depends(get_db_connection),
) -> InvoiceRepository:
    """Get an invoice repository for the given connection."""
    return InvoiceRepository(connection)


def get_invoice_service(
    repository: InvoiceRepository = Depends(get_invoice_repository),
    tx_manager: PostgresTransactionManager = Depends(get_transaction_manager),
    event_publisher: EventPublisher = Depends(get_event_publisher),
) -> InvoiceService:
    """Get an invoice service instance."""
    return InvoiceService(repository, tx_manager, event_publisher)
