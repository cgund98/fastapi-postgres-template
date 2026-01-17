"""FastAPI dependencies for user routes."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends

from app.domain.billing.invoice.service import InvoiceService
from app.domain.user.repo.sql import UserRepository
from app.domain.user.service import UserService
from app.infrastructure.messaging.publisher import EventPublisher
from app.infrastructure.sql.transaction import SQLTransactionManager
from app.presentation.deps import (
    get_event_publisher,
    get_invoice_service,
    get_transaction_manager,
    get_user_repository,
)


async def get_user_service(
    repository: Annotated[UserRepository, Depends(get_user_repository)],
    tx_manager: Annotated[SQLTransactionManager, Depends(get_transaction_manager)],
    event_publisher: Annotated[EventPublisher, Depends(get_event_publisher)],
    invoice_service: Annotated[InvoiceService, Depends(get_invoice_service)],
) -> AsyncGenerator[UserService, None]:
    """Dependency to get user service."""
    yield UserService(repository, tx_manager, event_publisher, invoice_service)
