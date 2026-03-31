"""Tests for InvoicePaymentRequestedHandler."""

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.domain.billing.invoice.handlers.payment_requested import InvoicePaymentRequestedHandler
from app.domain.billing.invoice.model import Invoice, InvoiceStatus
from app.domain.events.registry.billing.v1.invoice import InvoicePaymentRequestedEvent
from app.domain.events.registry.envelope import Envelope
from app.domain.events.registry.payload import Payload


def _make_envelope(payload: Payload) -> Envelope:
    return Envelope.build(payload=payload, source="test")


@pytest.mark.asyncio
async def test_invoice_payment_requested_handler(
    invoice_payment_requested_handler: InvoicePaymentRequestedHandler,
) -> None:
    """Test InvoicePaymentRequestedHandler."""
    invoice_id = uuid4()
    user_id = uuid4()
    amount = Decimal("75.00")
    now = datetime.now()

    mock_service = MagicMock()
    paid_invoice = Invoice(
        id=invoice_id,
        user_id=user_id,
        amount=amount,
        status=InvoiceStatus.PAID,
        created_at=now,
        updated_at=now,
        paid_at=now,
    )
    mock_service.mark_invoice_paid = AsyncMock(return_value=paid_invoice)

    event = InvoicePaymentRequestedEvent(invoice_id=invoice_id)

    with patch(
        "app.domain.billing.invoice.handlers.payment_requested.InvoiceService",
        return_value=mock_service,
    ):
        await invoice_payment_requested_handler.handle(event, _make_envelope(event))
        mock_service.mark_invoice_paid.assert_called_once_with(invoice_id)
