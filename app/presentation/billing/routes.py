"""Billing API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.domain.billing.invoice.service import InvoiceService
from app.domain.exceptions import NotFoundError
from app.presentation.billing.schema import InvoiceCreateRequest, InvoiceResponse
from app.presentation.deps import get_invoice_service
from app.presentation.pagination import create_paginated_response, page_to_limit_offset
from app.presentation.schemas import PaginatedResponse

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.get("", response_model=PaginatedResponse[InvoiceResponse])
async def list_invoices(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Number of items per page"),
    user_id: UUID | None = Query(default=None, description="Filter by user ID"),
    service: InvoiceService = Depends(get_invoice_service),
) -> PaginatedResponse[InvoiceResponse]:
    """List invoices with pagination and optional user_id filter."""
    limit, offset = page_to_limit_offset(page, page_size)
    invoices, total = await service.list_invoices(limit=limit, offset=offset, user_id=user_id)

    return create_paginated_response(
        items=[
            InvoiceResponse(
                id=invoice.id,
                user_id=invoice.user_id,
                amount=invoice.amount,
                status=invoice.status,
                created_at=invoice.created_at,
                paid_at=invoice.paid_at,
                updated_at=invoice.updated_at,
            )
            for invoice in invoices
        ],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.post("", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    request: InvoiceCreateRequest,
    service: InvoiceService = Depends(get_invoice_service),
) -> InvoiceResponse:
    """Create a new invoice."""
    invoice = await service.create_invoice(user_id=request.user_id, amount=request.amount)
    return InvoiceResponse(
        id=invoice.id,
        user_id=invoice.user_id,
        amount=invoice.amount,
        status=invoice.status,
        created_at=invoice.created_at,
        paid_at=invoice.paid_at,
        updated_at=invoice.updated_at,
    )


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: UUID,
    service: InvoiceService = Depends(get_invoice_service),
) -> InvoiceResponse:
    """Get invoice by ID."""
    invoice = await service.get_invoice(invoice_id)

    if invoice is None:
        raise NotFoundError(entity_type="Invoice", identifier=str(invoice_id))

    return InvoiceResponse(
        id=invoice.id,
        user_id=invoice.user_id,
        amount=invoice.amount,
        status=invoice.status,
        created_at=invoice.created_at,
        paid_at=invoice.paid_at,
        updated_at=invoice.updated_at,
    )


@router.post("/{invoice_id}/pay", response_model=InvoiceResponse)
async def pay_invoice(
    invoice_id: UUID,
    service: InvoiceService = Depends(get_invoice_service),
) -> InvoiceResponse:
    """Request payment for an invoice (triggers async processing)."""
    invoice = await service.request_payment(invoice_id)

    return InvoiceResponse(
        id=invoice.id,
        user_id=invoice.user_id,
        amount=invoice.amount,
        status=invoice.status,
        created_at=invoice.created_at,
        paid_at=invoice.paid_at,
        updated_at=invoice.updated_at,
    )
