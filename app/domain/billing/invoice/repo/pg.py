"""PostgreSQL repository for Invoice domain."""

import asyncpg
from asyncpg.pool import PoolConnectionProxy

from app.domain.billing.invoice.model import Invoice, InvoiceStatus
from app.domain.billing.invoice.repo.create import CreateInvoice


class InvoiceRepository:
    """PostgreSQL implementation of Invoice repository."""

    def __init__(self, connection: PoolConnectionProxy) -> None:
        """Initialize repository with a database connection from a pool."""
        self._conn = connection

    async def create(self, create_invoice: CreateInvoice) -> Invoice:
        """Create a new invoice."""
        row = await self._conn.fetchrow(
            """
            INSERT INTO invoices (id, user_id, amount, status, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, user_id, amount, status, created_at, paid_at, updated_at
            """,
            str(create_invoice.id),
            str(create_invoice.user_id),
            create_invoice.amount,
            InvoiceStatus.PENDING.value,
            create_invoice.created_at,
            create_invoice.updated_at,
        )
        if row is None:
            raise RuntimeError("Failed to create invoice: no row returned")
        return self._row_to_invoice(row)

    async def get_by_id(self, invoice_id: str) -> Invoice | None:
        """Get invoice by ID."""
        row = await self._conn.fetchrow(
            """
            SELECT id, user_id, amount, status, created_at, paid_at, updated_at
            FROM invoices
            WHERE id = $1
            """,
            invoice_id,
        )
        if row is None:
            return None
        return self._row_to_invoice(row)

    async def update(self, invoice: Invoice) -> Invoice:
        """Update an existing invoice."""
        row = await self._conn.fetchrow(
            """
            UPDATE invoices
            SET status = $2, paid_at = $3, updated_at = $4
            WHERE id = $1
            RETURNING id, user_id, amount, status, created_at, paid_at, updated_at
            """,
            str(invoice.id),
            invoice.status.value,
            invoice.paid_at,
            invoice.updated_at,
        )
        if row is None:
            raise RuntimeError("Failed to update invoice: no row returned")
        return self._row_to_invoice(row)

    async def delete_by_user_id(self, user_id: str) -> None:
        """Delete all invoices for a user."""
        await self._conn.execute(
            """
            DELETE FROM invoices
            WHERE user_id = $1
            """,
            user_id,
        )

    async def list(self, limit: int, offset: int, user_id: str | None = None) -> list[Invoice]:
        """List invoices with pagination and optional user_id filter."""
        if user_id:
            rows = await self._conn.fetch(
                """
                SELECT id, user_id, amount, status, created_at, paid_at, updated_at
                FROM invoices
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
                """,
                user_id,
                limit,
                offset,
            )
        else:
            rows = await self._conn.fetch(
                """
                SELECT id, user_id, amount, status, created_at, paid_at, updated_at
                FROM invoices
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
                """,
                limit,
                offset,
            )
        return [self._row_to_invoice(row) for row in rows]

    async def count(self, user_id: str | None = None) -> int:
        """Get total count of invoices, optionally filtered by user_id."""
        if user_id:
            count = await self._conn.fetchval("SELECT COUNT(*) FROM invoices WHERE user_id = $1", user_id)
        else:
            count = await self._conn.fetchval("SELECT COUNT(*) FROM invoices")
        return count if count is not None else 0

    def _row_to_invoice(self, row: asyncpg.Record) -> Invoice:
        """Convert database row to Invoice entity."""
        return Invoice.model_validate(dict(row))
