"""Tests for InvoiceService."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest

from app.domain.billing.invoice.model import Invoice, InvoiceStatus
from app.domain.billing.invoice.service import InvoiceService
from app.domain.exceptions import BusinessRuleError, NotFoundError


@pytest.mark.asyncio
async def test_create_invoice(
    invoice_service: InvoiceService,
    mock_invoice_repository: Any,
    mock_event_publisher: Any,
    mock_user_repository: Any,
) -> None:
    """Test creating an invoice."""
    user_id = uuid4()
    amount = Decimal("100.50")
    invoice_id = uuid4()
    now = datetime.now()

    # Mock repository response
    created_invoice = Invoice(
        id=invoice_id,
        user_id=user_id,
        amount=amount,
        status=InvoiceStatus.PENDING,
        created_at=now,
        updated_at=now,
    )
    mock_invoice_repository.create.return_value = created_invoice

    with patch(
        "app.domain.billing.invoice.service.validate_create_invoice_request", new_callable=AsyncMock
    ) as mock_validate:
        invoice = await invoice_service.create_invoice(user_id=user_id, amount=amount)

        assert invoice.user_id == user_id
        assert invoice.amount == amount
        assert invoice.status == InvoiceStatus.PENDING
        assert isinstance(invoice.id, UUID)
        assert invoice.created_at is not None
        assert invoice.updated_at is not None

        # Verify validator was called (with context)
        assert mock_validate.call_count == 1
        call_args = mock_validate.call_args
        assert call_args.kwargs["user_id"] == user_id
        assert call_args.kwargs["user_repository"] == mock_user_repository

        # Verify repository was called with correct args: create(context, create_invoice)
        assert mock_invoice_repository.create.call_count == 1
        create_call = mock_invoice_repository.create.call_args

        assert len(create_call.args) == 2  # context, create_invoice
        assert create_call.args[1].user_id == user_id
        assert create_call.args[1].amount == amount

        # Verify events were published
        assert mock_event_publisher.publish.call_count >= 1


@pytest.mark.asyncio
async def test_get_invoice(
    invoice_service: InvoiceService,
    mock_invoice_repository: Any,
) -> None:
    """Test getting an invoice by ID."""
    invoice_id = uuid4()
    user_id = uuid4()
    amount = Decimal("50.00")
    now = datetime.now()

    expected_invoice = Invoice(
        id=invoice_id,
        user_id=user_id,
        amount=amount,
        status=InvoiceStatus.PENDING,
        created_at=now,
        updated_at=now,
    )
    mock_invoice_repository.get_by_id.return_value = expected_invoice

    retrieved_invoice = await invoice_service.get_invoice(invoice_id)

    assert retrieved_invoice is not None
    assert retrieved_invoice.id == invoice_id
    assert retrieved_invoice.user_id == user_id
    assert retrieved_invoice.amount == amount

    # Verify repository was called with correct args: get_by_id(context, str(invoice_id))
    assert mock_invoice_repository.get_by_id.call_count == 1
    get_call = mock_invoice_repository.get_by_id.call_args
    assert len(get_call.args) == 2  # context, invoice_id
    assert get_call.args[1] == str(invoice_id)


@pytest.mark.asyncio
async def test_get_invoice_not_found(
    invoice_service: InvoiceService,
    mock_invoice_repository: Any,
) -> None:
    """Test getting a non-existent invoice returns None."""
    invoice_id = uuid4()
    mock_invoice_repository.get_by_id.return_value = None

    invoice = await invoice_service.get_invoice(invoice_id)
    assert invoice is None

    # Verify repository was called with correct args: get_by_id(context, str(invoice_id))
    assert mock_invoice_repository.get_by_id.call_count == 1
    get_call = mock_invoice_repository.get_by_id.call_args
    assert len(get_call.args) == 2  # context, invoice_id
    assert get_call.args[1] == str(invoice_id)


@pytest.mark.asyncio
async def test_mark_invoice_paid(
    invoice_service: InvoiceService,
    mock_invoice_repository: Any,
    mock_event_publisher: Any,
) -> None:
    """Test marking an invoice as paid."""
    invoice_id = uuid4()
    user_id = uuid4()
    amount = Decimal("75.00")
    now = datetime.now()

    # Mock initial invoice
    pending_invoice = Invoice(
        id=invoice_id,
        user_id=user_id,
        amount=amount,
        status=InvoiceStatus.PENDING,
        created_at=now,
        updated_at=now,
    )
    # Mock updated invoice
    paid_invoice = Invoice(
        id=invoice_id,
        user_id=user_id,
        amount=amount,
        status=InvoiceStatus.PAID,
        created_at=now,
        updated_at=now,
        paid_at=now,
    )
    mock_invoice_repository.get_by_id.return_value = pending_invoice
    mock_invoice_repository.update.return_value = paid_invoice

    result = await invoice_service.mark_invoice_paid(invoice_id)

    assert result.status == InvoiceStatus.PAID
    assert result.paid_at is not None
    assert result.id == invoice_id

    # Verify repository calls (with context)
    assert mock_invoice_repository.get_by_id.call_count == 1
    get_call = mock_invoice_repository.get_by_id.call_args
    assert len(get_call.args) == 2  # context, invoice_id
    assert get_call.args[1] == str(invoice_id)

    # Verify update was called with correct args: update(context, invoice)
    assert mock_invoice_repository.update.call_count == 1
    update_call = mock_invoice_repository.update.call_args
    assert len(update_call.args) == 2  # context, invoice
    assert update_call.args[1].status == InvoiceStatus.PAID

    # Verify event was published
    mock_event_publisher.publish.assert_called()
    published_event = mock_event_publisher.publish.call_args[0][0]
    assert published_event.aggregate_id == str(invoice_id)


@pytest.mark.asyncio
async def test_mark_invoice_paid_not_found(
    invoice_service: InvoiceService,
    mock_invoice_repository: Any,
) -> None:
    """Test marking a non-existent invoice as paid raises error."""
    invoice_id = uuid4()
    mock_invoice_repository.get_by_id.return_value = None

    with pytest.raises(NotFoundError) as exc_info:
        await invoice_service.mark_invoice_paid(invoice_id)

    assert exc_info.value.entity_type == "Invoice"

    # Verify repository was called with correct args: get_by_id(context, str(invoice_id))
    assert mock_invoice_repository.get_by_id.call_count == 1
    get_call = mock_invoice_repository.get_by_id.call_args

    assert len(get_call.args) == 2  # context, invoice_id
    assert get_call.args[1] == str(invoice_id)


@pytest.mark.asyncio
async def test_mark_invoice_paid_already_paid(
    invoice_service: InvoiceService,
    mock_invoice_repository: Any,
) -> None:
    """Test marking an already paid invoice raises error."""
    invoice_id = uuid4()
    user_id = uuid4()
    amount = Decimal("25.00")
    now = datetime.now()

    # Mock already paid invoice
    paid_invoice = Invoice(
        id=invoice_id,
        user_id=user_id,
        amount=amount,
        status=InvoiceStatus.PAID,
        created_at=now,
        updated_at=now,
        paid_at=now,
    )
    mock_invoice_repository.get_by_id.return_value = paid_invoice

    # Try to mark as paid again
    with pytest.raises(BusinessRuleError) as exc_info:
        await invoice_service.mark_invoice_paid(invoice_id)

    assert "already paid" in str(exc_info.value).lower()

    # Verify repository was called with context
    assert mock_invoice_repository.get_by_id.call_count == 1


@pytest.mark.asyncio
async def test_request_payment(
    invoice_service: InvoiceService,
    mock_invoice_repository: Any,
    mock_event_publisher: Any,
) -> None:
    """Test requesting payment for an invoice."""
    invoice_id = uuid4()
    user_id = uuid4()
    amount = Decimal("200.00")
    now = datetime.now()

    invoice = Invoice(
        id=invoice_id,
        user_id=user_id,
        amount=amount,
        status=InvoiceStatus.PENDING,
        created_at=now,
        updated_at=now,
    )
    mock_invoice_repository.get_by_id.return_value = invoice

    result = await invoice_service.request_payment(invoice_id)

    assert result.id == invoice_id

    # Verify repository was called with correct args: get_by_id(context, str(invoice_id))
    assert mock_invoice_repository.get_by_id.call_count == 1
    get_call = mock_invoice_repository.get_by_id.call_args
    assert len(get_call.args) == 2  # context, invoice_id
    assert get_call.args[1] == str(invoice_id)

    # Verify event was published
    mock_event_publisher.publish.assert_called()
    published_event = mock_event_publisher.publish.call_args[0][0]
    assert published_event.aggregate_id == str(invoice_id)


@pytest.mark.asyncio
async def test_request_payment_not_found(
    invoice_service: InvoiceService,
    mock_invoice_repository: Any,
) -> None:
    """Test requesting payment for a non-existent invoice raises error."""
    invoice_id = uuid4()
    mock_invoice_repository.get_by_id.return_value = None

    with pytest.raises(NotFoundError) as exc_info:
        await invoice_service.request_payment(invoice_id)

    assert exc_info.value.entity_type == "Invoice"

    # Verify repository was called with correct args: get_by_id(context, str(invoice_id))
    assert mock_invoice_repository.get_by_id.call_count == 1
    get_call = mock_invoice_repository.get_by_id.call_args
    assert len(get_call.args) == 2  # context, invoice_id
    assert get_call.args[1] == str(invoice_id)


@pytest.mark.asyncio
async def test_list_invoices(
    invoice_service: InvoiceService,
    mock_invoice_repository: Any,
) -> None:
    """Test listing invoices with pagination."""
    user_id = uuid4()
    now = datetime.now()

    # Mock repository responses
    mock_invoices = [
        Invoice(
            id=uuid4(),
            user_id=user_id,
            amount=Decimal(f"{10 * i}.00"),
            status=InvoiceStatus.PENDING,
            created_at=now,
            updated_at=now,
        )
        for i in range(3)
    ]
    mock_invoice_repository.list.return_value = mock_invoices
    mock_invoice_repository.count.return_value = 5

    invoices, total = await invoice_service.list_invoices(limit=3, offset=0)

    assert len(invoices) == 3
    assert total == 5
    # Verify repository was called with correct args: list(context, limit=limit, offset=offset, user_id=None)
    assert mock_invoice_repository.list.call_count == 1
    list_call = mock_invoice_repository.list.call_args
    assert len(list_call.args) == 1  # context
    assert list_call.kwargs["limit"] == 3
    assert list_call.kwargs["offset"] == 0
    assert list_call.kwargs["user_id"] is None

    # Verify count was called: count(context, user_id=None)
    assert mock_invoice_repository.count.call_count == 1
    count_call = mock_invoice_repository.count.call_args
    assert len(count_call.args) == 1  # context
    assert count_call.kwargs["user_id"] is None


@pytest.mark.asyncio
async def test_list_invoices_filtered_by_user_id(
    invoice_service: InvoiceService,
    mock_invoice_repository: Any,
) -> None:
    """Test listing invoices filtered by user_id."""
    user_id_1 = uuid4()
    now = datetime.now()

    # Mock repository responses
    mock_invoices = [
        Invoice(
            id=uuid4(),
            user_id=user_id_1,
            amount=Decimal(f"{10 * i}.00"),
            status=InvoiceStatus.PENDING,
            created_at=now,
            updated_at=now,
        )
        for i in range(3)
    ]
    mock_invoice_repository.list.return_value = mock_invoices
    mock_invoice_repository.count.return_value = 3

    invoices, total = await invoice_service.list_invoices(limit=10, offset=0, user_id=user_id_1)

    assert len(invoices) == 3
    assert total == 3
    assert all(invoice.user_id == user_id_1 for invoice in invoices)

    # Verify repository was called with correct args: list(context, limit=limit, offset=offset, user_id=str(user_id))
    assert mock_invoice_repository.list.call_count == 1
    list_call = mock_invoice_repository.list.call_args
    assert len(list_call.args) == 1  # context
    assert list_call.kwargs["limit"] == 10
    assert list_call.kwargs["offset"] == 0
    assert list_call.kwargs["user_id"] == str(user_id_1)

    # Verify count was called: count(context, user_id=str(user_id))
    assert mock_invoice_repository.count.call_count == 1
    count_call = mock_invoice_repository.count.call_args
    assert len(count_call.args) == 1  # context
    assert count_call.kwargs["user_id"] == str(user_id_1)


@pytest.mark.asyncio
async def test_delete_invoices_by_user_id(
    invoice_service: InvoiceService,
    mock_invoice_repository: Any,
) -> None:
    """Test deleting invoices for a user."""
    user_id = uuid4()

    await invoice_service.delete_invoices_by_user_id(user_id)

    # Verify repository was called with correct args: delete_by_user_id(context, str(user_id))
    assert mock_invoice_repository.delete_by_user_id.call_count == 1
    delete_call = mock_invoice_repository.delete_by_user_id.call_args
    assert len(delete_call.args) == 2  # context, user_id
    assert delete_call.args[1] == str(user_id)
