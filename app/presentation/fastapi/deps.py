"""Shared FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends

from app.adapters.billing.invoice.repo import InvoiceRepository
from app.adapters.sql.transaction import SQLTransactionManager
from app.adapters.user.repo import UserRepository
from app.domain.billing.invoice.service import InvoiceService
from app.domain.events.publisher import EventPublisher
from app.presentation.fastapi.container import AppContainer, get_container


def get_event_publisher(container: Annotated[AppContainer, Depends(get_container)]) -> EventPublisher:
    """Get event publisher instance."""
    return container.event_publisher


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
