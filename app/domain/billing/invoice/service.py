"""Invoice domain service."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from uuid_extensions import uuid7

from app.domain.billing.invoice.events.invoice_events import (
    InvoiceCreatedEvent,
    InvoicePaidEvent,
    InvoicePaymentRequestedEvent,
)
from app.domain.billing.invoice.model import Invoice, InvoiceStatus
from app.domain.billing.invoice.repo.create import CreateInvoice
from app.domain.billing.invoice.repo.pg import InvoiceRepository
from app.domain.exceptions import BusinessRuleError, NotFoundError
from app.infrastructure.db.transaction import TransactionManager
from app.infrastructure.messaging.publisher import EventPublisher


class InvoiceService:
    """Invoice domain service."""

    def __init__(
        self,
        repository: InvoiceRepository,
        transaction_manager: TransactionManager,
        event_publisher: EventPublisher,
    ) -> None:
        """Initialize invoice service."""
        self._repo = repository
        self._tx_manager = transaction_manager
        self._event_publisher = event_publisher

    async def create_invoice(self, user_id: UUID, amount: Decimal) -> Invoice:
        """Create a new invoice."""
        async with self._tx_manager.transaction():
            # Generate V7 UUID (timestamp-centric) and timestamps
            invoice_id = uuid7()
            now = datetime.now()
            create_invoice = CreateInvoice(
                id=invoice_id, user_id=user_id, amount=amount, created_at=now, updated_at=now
            )
            invoice = await self._repo.create(create_invoice)

            # Publish event (after commit)
            created_event = InvoiceCreatedEvent(
                aggregate_id=str(invoice.id), user_id=str(invoice.user_id), amount=invoice.amount
            )
            await self._event_publisher.publish(created_event)

        # Emit payment requested event after transaction is committed
        # This is just to simulate an external event to the system.
        # You wouldn't normally do this in a real application.
        payment_requested_event = InvoicePaymentRequestedEvent(aggregate_id=str(invoice.id))
        await self._event_publisher.publish(payment_requested_event)

        return invoice

    async def get_invoice(self, invoice_id: UUID) -> Invoice | None:
        """Get invoice by ID."""
        async with self._tx_manager.transaction():
            return await self._repo.get_by_id(str(invoice_id))

    async def mark_invoice_paid(self, invoice_id: UUID) -> Invoice:
        """Mark an invoice as paid."""
        async with self._tx_manager.transaction():
            invoice = await self._repo.get_by_id(str(invoice_id))
            if invoice is None:
                raise NotFoundError(entity_type="Invoice", identifier=str(invoice_id))

            # Validate business rule
            if invoice.status == InvoiceStatus.PAID:
                raise BusinessRuleError("Invoice is already paid")

            # Create updated invoice with paid status and updated timestamp
            updated_invoice = Invoice(
                id=invoice.id,
                user_id=invoice.user_id,
                amount=invoice.amount,
                status=InvoiceStatus.PAID,
                created_at=invoice.created_at,
                paid_at=datetime.now(),
                updated_at=datetime.now(),
            )
            updated_invoice = await self._repo.update(updated_invoice)

            # Publish event (after commit)
            event = InvoicePaidEvent(
                aggregate_id=str(updated_invoice.id),
                user_id=str(updated_invoice.user_id),
                amount=updated_invoice.amount,
            )
            await self._event_publisher.publish(event)

            return updated_invoice

    async def delete_invoices_by_user_id(self, user_id: UUID) -> None:
        """Delete all invoices for a user."""
        async with self._tx_manager.transaction():
            await self._delete_invoices_by_user_id_in_transaction(user_id)

    async def request_payment(self, invoice_id: UUID) -> Invoice:
        """Request payment for an invoice (publishes payment requested event)."""
        async with self._tx_manager.transaction():
            invoice = await self._repo.get_by_id(str(invoice_id))
            if invoice is None:
                raise NotFoundError(entity_type="Invoice", identifier=str(invoice_id))

            # Publish payment requested event (worker will process it)
            event = InvoicePaymentRequestedEvent(aggregate_id=str(invoice_id))
            await self._event_publisher.publish(event)

            return invoice

    async def list_invoices(self, limit: int, offset: int, user_id: UUID | None = None) -> tuple[list[Invoice], int]:
        """List invoices with pagination and optional user_id filter."""
        async with self._tx_manager.transaction():
            user_id_str = str(user_id) if user_id else None
            invoices = await self._repo.list(limit=limit, offset=offset, user_id=user_id_str)
            total = await self._repo.count(user_id=user_id_str)
            return invoices, total

    async def _delete_invoices_by_user_id_in_transaction(self, user_id: UUID) -> None:
        """
        Delete invoices when already in a transaction.

        This method should only be called when already within an active transaction.
        It does not manage transaction lifecycle, allowing it to be called from
        another service that manages the transaction (e.g., UserService).
        """
        await self._repo.delete_by_user_id(str(user_id))
