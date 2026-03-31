"""Invoice domain event consumers."""

from app.adapters.events.handler import EventHandler
from app.domain.events.registry.billing.v1.invoice import (
    InvoiceCreatedEvent,
    InvoiceEventTypes,
    InvoicePaidEvent,
)
from app.domain.events.registry.envelope import Envelope
from app.observability.logging import get_logger

logger = get_logger(__name__)


class InvoiceCreatedEventHandler(EventHandler[InvoiceCreatedEvent]):
    """Handler for invoice.created events."""

    async def handle(self, event: InvoiceCreatedEvent, envelope: Envelope) -> None:
        """Handle invoice.created event."""
        logger.info(
            f"Processing {InvoiceEventTypes.CREATED} event",
            event_id=envelope.id,
            aggregate_id=event.aggregate_id,
            user_id=event.user_id,
            amount=str(event.amount),
        )
        # Add your business logic here
        # Example: send invoice email, update accounting system, etc.


class InvoicePaidEventHandler(EventHandler[InvoicePaidEvent]):
    """Handler for invoice.paid events."""

    async def handle(self, event: InvoicePaidEvent, envelope: Envelope) -> None:
        """Handle invoice.paid event."""
        logger.info(
            f"Processing {InvoiceEventTypes.PAID} event",
            event_id=envelope.id,
            aggregate_id=event.aggregate_id,
            user_id=event.user_id,
            amount=str(event.amount),
        )
        # Add your business logic here
        # Example: update payment records, trigger fulfillment, etc.
