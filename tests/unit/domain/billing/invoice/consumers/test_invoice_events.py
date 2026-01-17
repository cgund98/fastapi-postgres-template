"""Tests for invoice event handlers."""

from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.billing.invoice.consumers.invoice_events import (
    InvoiceCreatedEventHandler,
    InvoicePaidEventHandler,
)
from app.domain.billing.invoice.events.invoice_events import InvoiceCreatedEvent, InvoicePaidEvent
from app.infrastructure.messaging.base import BaseEvent


@pytest.mark.asyncio
async def test_invoice_created_handler(
    invoice_created_handler: InvoiceCreatedEventHandler,
) -> None:
    """Test InvoiceCreatedEventHandler."""
    event = InvoiceCreatedEvent(
        aggregate_id=str(uuid4()),
        user_id=str(uuid4()),
        amount=Decimal("100.00"),
    )

    # Should not raise an exception
    await invoice_created_handler.handle(event)


@pytest.mark.asyncio
async def test_invoice_created_handler_wrong_type(
    invoice_created_handler: InvoiceCreatedEventHandler,
) -> None:
    """Test InvoiceCreatedEventHandler with wrong event type."""
    wrong_event = BaseEvent(
        aggregate_id=str(uuid4()),
        event_type="test.event",
        aggregate_type="test",
    )

    with pytest.raises(TypeError):
        await invoice_created_handler.handle(wrong_event)


@pytest.mark.asyncio
async def test_invoice_paid_handler(
    invoice_paid_handler: InvoicePaidEventHandler,
) -> None:
    """Test InvoicePaidEventHandler."""
    event = InvoicePaidEvent(
        aggregate_id=str(uuid4()),
        user_id=str(uuid4()),
        amount=Decimal("50.00"),
    )

    # Should not raise an exception
    await invoice_paid_handler.handle(event)


@pytest.mark.asyncio
async def test_invoice_paid_handler_wrong_type(
    invoice_paid_handler: InvoicePaidEventHandler,
) -> None:
    """Test InvoicePaidEventHandler with wrong event type."""
    wrong_event = BaseEvent(
        aggregate_id=str(uuid4()),
        event_type="test.event",
        aggregate_type="test",
    )

    with pytest.raises(TypeError):
        await invoice_paid_handler.handle(wrong_event)
