"""SQL repository for Invoice domain."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncConnection

from app.domain.billing.invoice.model import CreateInvoice, Invoice, InvoiceStatus
from app.domain.billing.invoice.persistence.queries import (
    count_invoices,
    count_invoices_by_user_id,
    delete_invoices_by_user_id,
    insert_invoice,
    select_invoice_by_id,
    select_invoices_list_with_user_filter,
    select_invoices_list_without_filter,
    update_invoice,
)
from app.domain.billing.invoice.repo.base import InvoiceRepository as BaseInvoiceRepository
from app.infrastructure.db.exceptions import DatabaseError
from app.observability.logging import get_logger

if TYPE_CHECKING:
    from sqlalchemy import Result
else:
    Result = object  # Placeholder for runtime

logger = get_logger(__name__)


class InvoiceRepository(BaseInvoiceRepository):
    """SQL implementation of Invoice repository using SQLAlchemy."""

    def __init__(self, conn: AsyncConnection) -> None:
        """Initialize repository with a database connection."""
        self._conn = conn

    async def create(self, create_invoice: CreateInvoice) -> Invoice:
        """Create a new invoice."""
        try:
            stmt = insert_invoice().values(
                id=create_invoice.id,
                user_id=create_invoice.user_id,
                amount=create_invoice.amount,
                status=InvoiceStatus.PENDING,
                created_at=create_invoice.created_at,
                updated_at=create_invoice.updated_at,
            )
            result: Result = await self._conn.execute(stmt)
            row = result.first()
            if row is None:
                raise DatabaseError()
            return Invoice(**row._mapping)
        except Exception as e:
            logger.exception("Database error while creating invoice")
            raise DatabaseError() from e

    async def get_by_id(self, invoice_id: str) -> Invoice | None:
        """Get invoice by ID."""
        try:
            stmt = select_invoice_by_id()
            result: Result = await self._conn.execute(stmt, {"invoice_id": UUID(invoice_id)})
            row = result.first()
            if row is None:
                return None
            return Invoice(**row._mapping)
        except Exception as e:
            logger.exception("Database error while retrieving invoice by ID")
            raise DatabaseError() from e

    async def update(self, invoice: Invoice) -> Invoice:
        """Update an existing invoice."""
        try:
            stmt = update_invoice().values(
                status=invoice.status,
                paid_at=invoice.paid_at,
                updated_at=invoice.updated_at,
            )
            result: Result = await self._conn.execute(stmt, {"invoice_id": invoice.id})
            row = result.first()
            if row is None:
                raise DatabaseError()
            return Invoice(**row._mapping)
        except Exception as e:
            logger.exception("Database error while updating invoice")
            raise DatabaseError() from e

    async def delete_by_user_id(self, user_id: str) -> None:
        """Delete all invoices for a user."""
        try:
            stmt = delete_invoices_by_user_id()
            await self._conn.execute(stmt, {"user_id": UUID(user_id)})
        except Exception as e:
            logger.exception("Database error while deleting invoices by user_id")
            raise DatabaseError() from e

    async def list(self, limit: int, offset: int, user_id: str | None = None) -> list[Invoice]:
        """List invoices with pagination and optional user_id filter."""
        try:
            if user_id:
                stmt = select_invoices_list_with_user_filter()
                params = {"user_id": UUID(user_id), "limit": limit, "offset": offset}
            else:
                stmt = select_invoices_list_without_filter()
                params = {"limit": limit, "offset": offset}
            query_result: Result = await self._conn.execute(stmt, params)
            rows = query_result.all()
            return [Invoice(**row._mapping) for row in rows]
        except Exception as e:
            logger.exception("Database error while listing invoices")
            raise DatabaseError() from e

    async def count(self, user_id: str | None = None) -> int:
        """Get total count of invoices, optionally filtered by user_id."""
        try:
            if user_id:
                stmt = count_invoices_by_user_id()
                params = {"user_id": UUID(user_id)}
            else:
                stmt = count_invoices()
                params = {}
            query_result: Result = await self._conn.execute(stmt, params)
            count = query_result.scalar()
            return count if count is not None else 0
        except Exception as e:
            logger.exception("Database error while counting invoices")
            raise DatabaseError() from e
