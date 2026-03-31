"""Billing API schemas."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.billing.invoice.model import InvoiceStatus


class InvoiceCreateRequest(BaseModel):
    """Request schema for creating an invoice."""

    user_id: UUID
    amount: Decimal = Field(..., gt=0, description="Invoice amount must be positive")


class InvoiceResponse(BaseModel):
    """Response schema for invoice."""

    id: UUID
    user_id: UUID
    amount: Decimal
    status: InvoiceStatus
    created_at: datetime
    paid_at: datetime | None
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True
