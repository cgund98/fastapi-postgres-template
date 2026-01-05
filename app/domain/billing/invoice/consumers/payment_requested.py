"""Handler for invoice payment requested events."""

from uuid import UUID

from app.config.settings import get_settings
from app.domain.billing.invoice.events.constants import InvoiceEventType
from app.domain.billing.invoice.events.invoice_events import InvoicePaymentRequestedEvent
from app.domain.billing.invoice.repo.pg import InvoiceRepository
from app.domain.billing.invoice.service import InvoiceService
from app.infrastructure.messaging.base import BaseEvent
from app.infrastructure.messaging.publisher import EventPublisher, SNSPublisher
from app.infrastructure.postgres.pool import PostgresPool
from app.infrastructure.postgres.transaction import PostgresTransactionManager
from app.observability.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class InvoicePaymentRequestedHandler:
    """Handler for invoice.payment_requested events."""

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

        # Initialize database connection and service
        pool = PostgresPool.get_pool()
        connection = await pool.acquire()
        tx_manager = PostgresTransactionManager(connection)
        repository = InvoiceRepository(connection)

        # Create event publisher for publishing InvoicePaidEvent
        topic_arn = settings.default_event_topic_arn
        if not topic_arn:
            raise ValueError("Default event topic ARN must be configured")
        sns_publisher = SNSPublisher(settings, topic_arn)
        event_publisher = EventPublisher(sns_publisher)

        service = InvoiceService(repository, tx_manager, event_publisher)

        try:
            # Mark invoice as paid (this will publish InvoicePaidEvent)
            invoice_id = UUID(payment_event.aggregate_id)
            await service.mark_invoice_paid(invoice_id)
            logger.info(
                "Successfully marked invoice as paid",
                invoice_id=payment_event.aggregate_id,
            )
        finally:
            # Ensure connection is released
            if not tx_manager._released:
                await pool.release(connection)
