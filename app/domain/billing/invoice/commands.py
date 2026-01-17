"""Invoice domain commands for operations."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass
class CreateInvoice:
    """Command for creating a new invoice."""

    id: UUID
    user_id: UUID
    amount: Decimal
    created_at: datetime
    updated_at: datetime
