"""Shared FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends, Request

from app.config.settings import Settings, get_settings
from app.domain.billing.invoice.repo.sql import InvoiceRepository
from app.domain.billing.invoice.service import InvoiceService
from app.domain.user.repo.sql import UserRepository
from app.infrastructure.messaging.publisher import EventPublisher, SNSPublisher
from app.infrastructure.sql.transaction import SQLTransactionManager
from app.presentation.container import AppContainer, get_container_from_request


def get_container(request: Request) -> AppContainer:
    """Get the application container from the request."""
    return get_container_from_request(request)


def get_event_publisher(settings: Annotated[Settings, Depends(get_settings)]) -> EventPublisher:
    """Get event publisher instance."""

    topic_arn = settings.default_event_topic_arn
    if not topic_arn:
        raise ValueError("Default event topic ARN must be configured")

    sns_publisher = SNSPublisher(settings, topic_arn)
    return EventPublisher(sns_publisher)


def get_transaction_manager(
    container: Annotated[AppContainer, Depends(get_container)],
) -> SQLTransactionManager:
    """Get the transaction manager from the container."""
    return container.transaction_manager


def get_user_repository() -> UserRepository:
    """Get a user repository instance (stateless, context passed per method)."""
    return UserRepository()


def get_invoice_repository() -> InvoiceRepository:
    """Get an invoice repository instance (stateless, context passed per method)."""
    return InvoiceRepository()


def get_invoice_service(
    repository: Annotated[InvoiceRepository, Depends(get_invoice_repository)],
    tx_manager: Annotated[SQLTransactionManager, Depends(get_transaction_manager)],
    event_publisher: Annotated[EventPublisher, Depends(get_event_publisher)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> InvoiceService:
    """Get an invoice service instance."""
    return InvoiceService(repository, tx_manager, event_publisher, user_repository)
