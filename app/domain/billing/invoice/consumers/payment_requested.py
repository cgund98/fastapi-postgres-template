"""Handler for invoice payment requested events."""

from uuid import UUID

from app.domain.billing.invoice.events.constants import InvoiceEventType
from app.domain.billing.invoice.events.invoice_events import InvoicePaymentRequestedEvent
from app.domain.billing.invoice.repo.sql import InvoiceRepository
from app.domain.billing.invoice.service import InvoiceService
from app.domain.user.repo.sql import UserRepository
from app.infrastructure.messaging.base import BaseEvent
from app.infrastructure.messaging.handler import EventHandler
from app.infrastructure.messaging.publisher import EventPublisher
from app.infrastructure.sql.transaction import SQLTransactionManager
from app.observability.logging import get_logger

logger = get_logger(__name__)


class InvoicePaymentRequestedHandler(EventHandler[InvoicePaymentRequestedEvent]):
    """Handler for invoice.payment_requested events."""

    def __init__(self, event_publisher: EventPublisher, transaction_manager: SQLTransactionManager) -> None:
        """Initialize handler with event publisher and transaction manager."""
        self._event_publisher = event_publisher
        self._transaction_manager = transaction_manager

    async def handle(self, event: BaseEvent) -> None:
        """Handle invoice.payment_requested event."""
        if not isinstance(event, InvoicePaymentRequestedEvent):
            raise TypeError(f"Expected InvoicePaymentRequestedEvent, got {type(event)}")
        payment_event = event  # Type narrowing

        logger.info(
            f"Processing {InvoiceEventType.PAYMENT_REQUESTED} event",
            event_id=str(payment_event.event_id),
            aggregate_id=payment_event.aggregate_id,
        )

        # Use transaction manager which creates a session per transaction
        repository = InvoiceRepository()
        user_repository = UserRepository()

        service = InvoiceService(repository, self._transaction_manager, self._event_publisher, user_repository)

        # Mark invoice as paid (this will publish InvoicePaidEvent)
        invoice_id = UUID(payment_event.aggregate_id)
        await service.mark_invoice_paid(invoice_id)
        logger.info(
            "Successfully marked invoice as paid",
            invoice_id=payment_event.aggregate_id,
        )
