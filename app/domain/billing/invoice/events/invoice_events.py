"""Invoice domain events."""

from decimal import Decimal

from pydantic import Field, field_validator

from app.domain.billing.invoice.events.constants import (
    InvoiceAggregateType,
    InvoiceEventType,
)
from app.infrastructure.messaging.base import BaseEvent


class InvoiceCreatedEvent(BaseEvent):
    """Event emitted when an invoice is created."""

    event_type: str = Field(default=InvoiceEventType.CREATED, frozen=True)
    aggregate_type: str = Field(default=InvoiceAggregateType.INVOICE, frozen=True)
    user_id: str
    amount: Decimal = Field(gt=0, description="Invoice amount must be positive")

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Validate that amount is positive."""
        if v <= 0:
            raise ValueError("Invoice amount must be positive")
        return v


class InvoicePaymentRequestedEvent(BaseEvent):
    """Event emitted when payment for an invoice is requested."""

    event_type: str = Field(default=InvoiceEventType.PAYMENT_REQUESTED, frozen=True)
    aggregate_type: str = Field(default=InvoiceAggregateType.INVOICE, frozen=True)


class InvoicePaidEvent(BaseEvent):
    """Event emitted when an invoice is paid."""

    event_type: str = Field(default=InvoiceEventType.PAID, frozen=True)
    aggregate_type: str = Field(default=InvoiceAggregateType.INVOICE, frozen=True)
    user_id: str
    amount: Decimal = Field(gt=0, description="Invoice amount must be positive")

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Validate that amount is positive."""
        if v <= 0:
            raise ValueError("Invoice amount must be positive")
        return v
