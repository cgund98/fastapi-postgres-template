"""Shared FastAPI dependencies."""

from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncConnection

from app.config.settings import Settings, get_settings
from app.domain.billing.invoice.repo.sql import InvoiceRepository
from app.domain.billing.invoice.service import InvoiceService
from app.domain.user.repo.sql import UserRepository
from app.infrastructure.messaging.publisher import EventPublisher, SNSPublisher
from app.infrastructure.sql.sqlalchemy_pool import SQLAlchemyPool
from app.infrastructure.sql.transaction import SQLTransactionManager


async def get_db_connection() -> AsyncGenerator[AsyncConnection, None]:
    """Get a database connection from the SQLAlchemy pool."""
    async with SQLAlchemyPool.get_connection() as connection:
        yield connection


def get_event_publisher(settings: Settings = Depends(get_settings)) -> EventPublisher:
    """Get event publisher instance."""

    topic_arn = settings.default_event_topic_arn
    if not topic_arn:
        raise ValueError("Default event topic ARN must be configured")

    sns_publisher = SNSPublisher(settings, topic_arn)
    return EventPublisher(sns_publisher)


def get_transaction_manager(
    connection: AsyncConnection = Depends(get_db_connection),
) -> SQLTransactionManager:
    """Get a transaction manager for the given connection."""
    return SQLTransactionManager(connection)


def get_user_repository(
    connection: AsyncConnection = Depends(get_db_connection),
) -> UserRepository:
    """Get a user repository for the given connection."""
    return UserRepository(connection)


def get_invoice_repository(
    connection: AsyncConnection = Depends(get_db_connection),
) -> InvoiceRepository:
    """Get an invoice repository for the given connection."""
    return InvoiceRepository(connection)


def get_invoice_service(
    repository: InvoiceRepository = Depends(get_invoice_repository),
    tx_manager: SQLTransactionManager = Depends(get_transaction_manager),
    event_publisher: EventPublisher = Depends(get_event_publisher),
    user_repository: UserRepository = Depends(get_user_repository),
) -> InvoiceService:
    """Get an invoice service instance."""
    return InvoiceService(repository, tx_manager, event_publisher, user_repository)
