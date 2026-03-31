"""Tests for invoice event handlers."""

from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.billing.invoice.handlers.invoice_events import (
    InvoiceCreatedEventHandler,
    InvoicePaidEventHandler,
)
from app.domain.events.registry.billing.v1.invoice import InvoiceCreatedEvent, InvoicePaidEvent
from app.domain.events.registry.envelope import Envelope
from app.domain.events.registry.payload import Payload


def _make_envelope(payload: Payload) -> Envelope:
    return Envelope.build(payload=payload, source="test")


@pytest.mark.asyncio
async def test_invoice_created_handler(
    invoice_created_handler: InvoiceCreatedEventHandler,
) -> None:
    """Test InvoiceCreatedEventHandler."""
    event = InvoiceCreatedEvent(
        invoice_id=uuid4(),
        user_id=uuid4(),
        amount=Decimal("100.00"),
    )
    await invoice_created_handler.handle(event, _make_envelope(event))


@pytest.mark.asyncio
async def test_invoice_paid_handler(
    invoice_paid_handler: InvoicePaidEventHandler,
) -> None:
    """Test InvoicePaidEventHandler."""
    event = InvoicePaidEvent(
        invoice_id=uuid4(),
        user_id=uuid4(),
        amount=Decimal("50.00"),
    )
    await invoice_paid_handler.handle(event, _make_envelope(event))
