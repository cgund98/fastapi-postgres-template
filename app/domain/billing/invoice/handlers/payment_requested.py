"""Handler for invoice payment requested events."""

from uuid import UUID

from app.adapters.billing.invoice.repo import InvoiceRepository
from app.adapters.events.handler import EventHandler
from app.adapters.sql.transaction import SQLTransactionManager
from app.adapters.user.repo import UserRepository
from app.domain.billing.invoice.service import InvoiceService
from app.domain.events.publisher import EventPublisher
from app.domain.events.registry.billing.v1.invoice import InvoiceEventTypes, InvoicePaymentRequestedEvent
from app.domain.events.registry.envelope import Envelope
from app.observability.logging import get_logger

logger = get_logger(__name__)


class InvoicePaymentRequestedHandler(EventHandler[InvoicePaymentRequestedEvent]):
    """Handler for invoice.payment_requested events."""

    def __init__(self, event_publisher: EventPublisher, transaction_manager: SQLTransactionManager) -> None:
        """Initialize handler with event publisher and transaction manager."""
        self._event_publisher = event_publisher
        self._transaction_manager = transaction_manager

    async def handle(self, event: InvoicePaymentRequestedEvent, envelope: Envelope) -> None:
        """Handle invoice.payment_requested event."""
        logger.info(
            f"Processing {InvoiceEventTypes.PAYMENT_REQUESTED} event",
            event_id=envelope.id,
            invoice_id=event.invoice_id,
            correlation_id=envelope.attributes.correlation_id,
        )

        # Use transaction manager which creates a session per transaction
        repository = InvoiceRepository()
        user_repository = UserRepository()

        service = InvoiceService(repository, self._transaction_manager, self._event_publisher, user_repository)

        # Mark invoice as paid (this will publish InvoicePaidEvent)
        invoice_id = UUID(event.aggregate_id())
        await service.mark_invoice_paid(invoice_id)
        logger.info(
            "Successfully marked invoice as paid",
            invoice_id=event.invoice_id,
            correlation_id=envelope.attributes.correlation_id,
        )
