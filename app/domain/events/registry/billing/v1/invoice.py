"""Invoice domain events."""

from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import Field

from app.domain.events.registry.payload import Payload


class InvoiceEventTypes(StrEnum):
    CREATED = "invoice.v1.created"
    PAYMENT_REQUESTED = "invoice.v1.payment_requested"
    PAID = "invoice.v1.paid"


class InvoiceCreatedEvent(Payload):
    """Event emitted when an invoice is created."""

    invoice_id: UUID
    user_id: UUID
    amount: Decimal = Field(gt=0, description="Invoice amount must be positive")

    @classmethod
    def event_type(cls) -> str:
        return InvoiceEventTypes.CREATED

    def aggregate_id(self) -> str:
        return str(self.invoice_id)


class InvoicePaymentRequestedEvent(Payload):
    """Event emitted when payment for an invoice is requested."""

    invoice_id: UUID

    @classmethod
    def event_type(cls) -> str:
        return InvoiceEventTypes.PAYMENT_REQUESTED

    def aggregate_id(self) -> str:
        return str(self.invoice_id)


class InvoicePaidEvent(Payload):
    """Event emitted when an invoice is paid."""

    invoice_id: UUID
    user_id: UUID
    amount: Decimal = Field(gt=0, description="Invoice amount must be positive")

    @classmethod
    def event_type(cls) -> str:
        return InvoiceEventTypes.PAID

    def aggregate_id(self) -> str:
        return str(self.invoice_id)
