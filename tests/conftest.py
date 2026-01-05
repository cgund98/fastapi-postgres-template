"""Pytest configuration and fixtures."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.config.settings import Settings
from app.domain.billing.invoice.consumers.invoice_events import (
    InvoiceCreatedEventHandler,
    InvoicePaidEventHandler,
)
from app.domain.billing.invoice.consumers.payment_requested import InvoicePaymentRequestedHandler
from app.domain.billing.invoice.repo.pg import InvoiceRepository
from app.domain.billing.invoice.service import InvoiceService
from app.domain.user.consumers.user_events import UserCreatedEventHandler, UserUpdatedEventHandler
from app.domain.user.repo.pg import UserRepository
from app.domain.user.service import UserService
from app.infrastructure.db.transaction import TransactionManager
from app.infrastructure.messaging.publisher import EventPublisher


@pytest.fixture
def test_settings() -> Settings:
    """Test settings fixture."""
    return Settings(
        postgres_host="localhost",
        postgres_port=5432,
        postgres_user="postgres",
        postgres_password="postgres",
        postgres_database="app_test",
        environment="test",
    )


@pytest.fixture
def mock_event_publisher() -> EventPublisher:
    """Create a mock event publisher."""
    mock_publisher = MagicMock(spec=EventPublisher)
    mock_publisher.publish = AsyncMock()
    return mock_publisher


@pytest.fixture
def mock_transaction_manager() -> TransactionManager:
    """Create a mock transaction manager."""
    mock_tx = MagicMock(spec=TransactionManager)

    @asynccontextmanager
    async def mock_transaction() -> AsyncGenerator[None, None]:
        yield None

    mock_tx.transaction = MagicMock(return_value=mock_transaction())
    return mock_tx


@pytest.fixture
def mock_user_repository() -> UserRepository:
    """Create a mock user repository."""
    mock_repo = MagicMock(spec=UserRepository)
    mock_repo.create = AsyncMock()
    mock_repo.get_by_id = AsyncMock()
    mock_repo.get_by_email = AsyncMock()
    mock_repo.update = AsyncMock()
    mock_repo.delete = AsyncMock()
    mock_repo.list = AsyncMock()
    mock_repo.count = AsyncMock()
    return mock_repo


@pytest.fixture
def mock_invoice_repository() -> InvoiceRepository:
    """Create a mock invoice repository."""
    mock_repo = MagicMock(spec=InvoiceRepository)
    mock_repo.create = AsyncMock()
    mock_repo.get_by_id = AsyncMock()
    mock_repo.update = AsyncMock()
    mock_repo.delete_by_user_id = AsyncMock()
    mock_repo.list = AsyncMock()
    mock_repo.count = AsyncMock()
    return mock_repo


@pytest.fixture
def invoice_service(
    mock_invoice_repository: InvoiceRepository,
    mock_transaction_manager: TransactionManager,
    mock_event_publisher: EventPublisher,
) -> InvoiceService:
    """Get an invoice service for testing with mocked dependencies."""
    return InvoiceService(mock_invoice_repository, mock_transaction_manager, mock_event_publisher)


@pytest.fixture
def user_service(
    mock_user_repository: UserRepository,
    mock_transaction_manager: TransactionManager,
    mock_event_publisher: EventPublisher,
    mock_invoice_service: InvoiceService,
) -> UserService:
    """Get a user service for testing with mocked dependencies."""
    return UserService(mock_user_repository, mock_transaction_manager, mock_event_publisher, mock_invoice_service)


@pytest.fixture
def mock_invoice_service() -> InvoiceService:
    """Create a mock invoice service."""
    mock_service = MagicMock(spec=InvoiceService)
    mock_service.create_invoice = AsyncMock()
    mock_service.get_invoice = AsyncMock()
    mock_service.mark_invoice_paid = AsyncMock()
    mock_service.request_payment = AsyncMock()
    mock_service.list_invoices = AsyncMock()
    mock_service.delete_invoices_by_user_id = AsyncMock()
    mock_service._delete_invoices_by_user_id_in_transaction = AsyncMock()
    return mock_service


@pytest.fixture
def user_created_handler() -> UserCreatedEventHandler:
    """Get a user created event handler for testing."""
    return UserCreatedEventHandler()


@pytest.fixture
def user_updated_handler() -> UserUpdatedEventHandler:
    """Get a user updated event handler for testing."""
    return UserUpdatedEventHandler()


@pytest.fixture
def invoice_created_handler() -> InvoiceCreatedEventHandler:
    """Get an invoice created event handler for testing."""
    return InvoiceCreatedEventHandler()


@pytest.fixture
def invoice_paid_handler() -> InvoicePaidEventHandler:
    """Get an invoice paid event handler for testing."""
    return InvoicePaidEventHandler()


@pytest.fixture
def invoice_payment_requested_handler(
    mock_event_publisher: EventPublisher,
) -> InvoicePaymentRequestedHandler:
    """Get an invoice payment requested handler for testing."""
    return InvoicePaymentRequestedHandler(mock_event_publisher)
