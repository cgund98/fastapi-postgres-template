"""Invoice domain event consumers."""

from app.domain.billing.invoice.events.constants import InvoiceEventType
from app.domain.billing.invoice.events.invoice_events import (
    InvoiceCreatedEvent,
    InvoicePaidEvent,
)
from app.infrastructure.messaging.handler import EventHandler
from app.observability.logging import get_logger

logger = get_logger(__name__)


class InvoiceCreatedEventHandler(EventHandler[InvoiceCreatedEvent]):
    """Handler for invoice.created events."""

    async def handle(self, event: InvoiceCreatedEvent) -> None:
        """Handle invoice.created event."""
        logger.info(
            f"Processing {InvoiceEventType.CREATED} event",
            event_id=str(event.event_id),
            aggregate_id=event.aggregate_id,
            user_id=event.user_id,
            amount=str(event.amount),
        )
        # Add your business logic here
        # Example: send invoice email, update accounting system, etc.


class InvoicePaidEventHandler(EventHandler[InvoicePaidEvent]):
    """Handler for invoice.paid events."""

    async def handle(self, event: InvoicePaidEvent) -> None:
        """Handle invoice.paid event."""
        logger.info(
            f"Processing {InvoiceEventType.PAID} event",
            event_id=str(event.event_id),
            aggregate_id=event.aggregate_id,
            user_id=event.user_id,
            amount=str(event.amount),
        )
        # Add your business logic here
        # Example: update payment records, trigger fulfillment, etc.
