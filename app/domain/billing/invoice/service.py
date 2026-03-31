"""Invoice domain service."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from uuid_extensions import uuid7str

from app.adapters.db.transaction import TransactionManager
from app.domain.billing.invoice.commands import CreateInvoiceCommand
from app.domain.billing.invoice.model import Invoice, InvoiceStatus
from app.domain.billing.invoice.repo import InvoiceRepository
from app.domain.billing.invoice.validators import validate_create_invoice_request
from app.domain.events.publisher import EventPublisher, PublishArgs
from app.domain.events.registry.billing.v1.invoice import (
    InvoiceCreatedEvent,
    InvoicePaidEvent,
    InvoicePaymentRequestedEvent,
)
from app.domain.exceptions import NotFoundError
from app.domain.user.repo import UserRepository
from app.observability.logging import get_logger

logger = get_logger(__name__)


class InvoiceService[TContext]:
    """Invoice domain service."""

    def __init__(
        self,
        repository: InvoiceRepository[TContext],
        transaction_manager: TransactionManager[TContext],
        event_publisher: EventPublisher,
        user_repository: UserRepository[TContext],
    ) -> None:
        """Initialize invoice service."""
        self._repo = repository
        self._tx_manager = transaction_manager
        self._event_publisher = event_publisher
        self._user_repo = user_repository

    async def create_invoice(self, user_id: UUID, amount: Decimal) -> Invoice:
        """Create a new invoice."""
        async with self._tx_manager.transaction() as context:
            # Validate request
            await validate_create_invoice_request(user_id=user_id, user_repository=self._user_repo, context=context)

            # Generate V7 UUID (timestamp-centric) and timestamps
            invoice_id = uuid7str()
            now = datetime.now()
            create_invoice = CreateInvoiceCommand(
                id=invoice_id, user_id=user_id, amount=amount, created_at=now, updated_at=now
            )
            invoice = await self._repo.create(context, create_invoice)

            # Publish event (after commit)
            created_event = InvoiceCreatedEvent(invoice_id=invoice.id, user_id=invoice.user_id, amount=invoice.amount)
            publish_args = PublishArgs(payload=created_event, source="invoice.service.create_invoice")
            await self._event_publisher.publish(publish_args)

        # Emit payment requested event after transaction is committed
        # This is just to simulate an external event to the system.
        # You wouldn't normally do this in a real application.
        payment_requested_event = InvoicePaymentRequestedEvent(invoice_id=invoice.id)
        publish_args = PublishArgs(payload=payment_requested_event, source="invoice.service.request_payment")
        await self._event_publisher.publish(publish_args)

        return invoice

    async def get_invoice(self, invoice_id: UUID) -> Invoice | None:
        """Get invoice by ID."""
        async with self._tx_manager.transaction() as context:
            return await self._repo.get_by_id(context, str(invoice_id))

    async def mark_invoice_paid(self, invoice_id: UUID) -> Invoice:
        """Mark an invoice as paid."""
        async with self._tx_manager.transaction() as context:
            invoice = await self._repo.get_by_id(context, str(invoice_id))
            if invoice is None:
                raise NotFoundError(entity_type="Invoice", identifier=str(invoice_id))

            # Validate business rule
            if invoice.status == InvoiceStatus.PAID:
                logger.warning("Invoice is already paid", invoice_id=invoice_id)
                return invoice

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
            updated_invoice = await self._repo.update(context, updated_invoice)

            # Publish event (after commit)
            paid_event = InvoicePaidEvent(
                invoice_id=updated_invoice.id,
                user_id=updated_invoice.user_id,
                amount=updated_invoice.amount,
            )
            publish_args = PublishArgs(payload=paid_event, source="invoice.service.mark_invoice_paid")
            await self._event_publisher.publish(publish_args)

            return updated_invoice

    async def delete_invoices_by_user_id(self, user_id: UUID) -> None:
        """Delete all invoices for a user."""
        async with self._tx_manager.transaction() as context:
            await self._delete_invoices_by_user_id_in_transaction(context, user_id)

    async def request_payment(self, invoice_id: UUID) -> Invoice:
        """Request payment for an invoice (publishes payment requested event)."""
        async with self._tx_manager.transaction() as context:
            invoice = await self._repo.get_by_id(context, str(invoice_id))
            if invoice is None:
                raise NotFoundError(entity_type="Invoice", identifier=str(invoice_id))

            # Publish payment requested event (worker will process it)
            payment_requested_event = InvoicePaymentRequestedEvent(invoice_id=invoice.id)
            publish_args = PublishArgs(payload=payment_requested_event, source="invoice.service.request_payment")
            await self._event_publisher.publish(publish_args)

            return invoice

    async def list_invoices(self, limit: int, offset: int, user_id: UUID | None = None) -> tuple[list[Invoice], int]:
        """List invoices with pagination and optional user_id filter."""
        async with self._tx_manager.transaction() as context:
            user_id_str = str(user_id) if user_id else None
            invoices = await self._repo.list(context, limit=limit, offset=offset, user_id=user_id_str)
            total = await self._repo.count(context, user_id=user_id_str)
            return invoices, total

    async def _delete_invoices_by_user_id_in_transaction(self, context: TContext, user_id: UUID) -> None:
        """
        Delete invoices when already in a transaction.

        This method should only be called when already within an active transaction.
        It does not manage transaction lifecycle, allowing it to be called from
        another service that manages the transaction (e.g., UserService).
        """
        await self._repo.delete_by_user_id(context, str(user_id))
