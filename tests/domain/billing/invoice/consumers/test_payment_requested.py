"""Tests for InvoicePaymentRequestedHandler."""

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.domain.billing.invoice.consumers.payment_requested import InvoicePaymentRequestedHandler
from app.domain.billing.invoice.events.invoice_events import InvoicePaymentRequestedEvent
from app.domain.billing.invoice.model import Invoice, InvoiceStatus
from app.infrastructure.messaging.base import BaseEvent


@pytest.mark.asyncio
async def test_invoice_payment_requested_handler(
    invoice_payment_requested_handler: InvoicePaymentRequestedHandler,
) -> None:
    """Test InvoicePaymentRequestedHandler."""
    invoice_id = uuid4()
    user_id = uuid4()
    amount = Decimal("75.00")
    now = datetime.now()

    # Mock invoice service
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

    # Mock SQLAlchemyPool connection context manager
    mock_connection = MagicMock()
    mock_connection_context = AsyncMock()
    mock_connection_context.__aenter__ = AsyncMock(return_value=mock_connection)
    mock_connection_context.__aexit__ = AsyncMock(return_value=None)

    event = InvoicePaymentRequestedEvent(aggregate_id=str(invoice_id))

    with (
        patch("app.domain.billing.invoice.consumers.payment_requested.SQLAlchemyPool") as mock_pool_class,
        patch("app.domain.billing.invoice.consumers.payment_requested.SQLTransactionManager") as mock_tx_class,
        patch("app.domain.billing.invoice.consumers.payment_requested.InvoiceService", return_value=mock_service),
    ):
        mock_pool_class.get_connection.return_value = mock_connection_context
        mock_tx_manager = MagicMock()
        mock_tx_class.return_value = mock_tx_manager

        # Should mark invoice as paid and not raise an exception
        await invoice_payment_requested_handler.handle(event)

        # Verify service was called
        mock_service.mark_invoice_paid.assert_called_once_with(invoice_id)
        # Verify connection context manager was used
        mock_pool_class.get_connection.assert_called_once()
        mock_connection_context.__aenter__.assert_called_once()
        mock_connection_context.__aexit__.assert_called_once()


@pytest.mark.asyncio
async def test_invoice_payment_requested_handler_wrong_type(
    invoice_payment_requested_handler: InvoicePaymentRequestedHandler,
) -> None:
    """Test InvoicePaymentRequestedHandler with wrong event type."""
    wrong_event = BaseEvent(
        aggregate_id=str(uuid4()),
        event_type="test.event",
        aggregate_type="test",
    )

    with pytest.raises(TypeError):
        await invoice_payment_requested_handler.handle(wrong_event)
