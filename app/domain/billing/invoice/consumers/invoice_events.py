"""Invoice domain event consumers."""

from app.domain.billing.invoice.events.constants import InvoiceEventType
from app.domain.billing.invoice.events.invoice_events import (
    InvoiceCreatedEvent,
    InvoicePaidEvent,
)
from app.infrastructure.messaging.base import BaseEvent
from app.observability.logging import get_logger

logger = get_logger(__name__)


class InvoiceCreatedEventHandler:
    """Handler for invoice.created events."""

    async def handle(self, event: BaseEvent) -> None:
        """Handle invoice.created event."""
        if not isinstance(event, InvoiceCreatedEvent):
            raise TypeError(f"Expected InvoiceCreatedEvent, got {type(event)}")
        invoice_event = event  # Type narrowing
        logger.info(
            f"Processing {InvoiceEventType.CREATED} event",
            event_id=str(invoice_event.event_id),
            aggregate_id=invoice_event.aggregate_id,
            user_id=invoice_event.user_id,
            amount=str(invoice_event.amount),
        )
        # Add your business logic here
        # Example: send invoice email, update accounting system, etc.


class InvoicePaidEventHandler:
    """Handler for invoice.paid events."""

    async def handle(self, event: BaseEvent) -> None:
        """Handle invoice.paid event."""
        if not isinstance(event, InvoicePaidEvent):
            raise TypeError(f"Expected InvoicePaidEvent, got {type(event)}")
        invoice_event = event  # Type narrowing
        logger.info(
            f"Processing {InvoiceEventType.PAID} event",
            event_id=str(invoice_event.event_id),
            aggregate_id=invoice_event.aggregate_id,
            user_id=invoice_event.user_id,
            amount=str(invoice_event.amount),
        )
        # Add your business logic here
        # Example: update payment records, trigger fulfillment, etc.
