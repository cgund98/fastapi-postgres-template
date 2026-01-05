"""Constants for invoice domain events."""

from enum import Enum


class InvoiceAggregateType(str, Enum):
    """Invoice aggregate type."""

    INVOICE = "invoice"


class InvoiceEventType(str, Enum):
    """Invoice event types."""

    CREATED = "invoice.created"
    PAYMENT_REQUESTED = "invoice.payment_requested"
    PAID = "invoice.paid"
