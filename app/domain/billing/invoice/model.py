"""Invoice domain model."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class InvoiceStatus(str, Enum):
    """Invoice status enumeration."""

    PENDING = "pending"
    PAID = "paid"


class Invoice(BaseModel):
    """Invoice domain entity."""

    id: UUID
    user_id: UUID
    amount: Decimal
    status: InvoiceStatus
    created_at: datetime
    updated_at: datetime
    paid_at: datetime | None = None

    model_config = {"frozen": True}


@dataclass
class CreateInvoice:
    """Data structure for creating a new invoice."""

    id: UUID
    user_id: UUID
    amount: Decimal
    created_at: datetime
    updated_at: datetime
