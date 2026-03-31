"""SQL repository for Invoice domain."""

from uuid import UUID

import asyncpg

from app.adapters.db.exceptions import DatabaseError
from app.adapters.sql.context import SQLContext
from app.domain.billing.invoice.commands import CreateInvoiceCommand
from app.domain.billing.invoice.model import Invoice, InvoiceStatus
from app.domain.billing.invoice.repo import InvoiceRepository as BaseInvoiceRepository
from app.observability.logging import get_logger

logger = get_logger(__name__)

_COLUMNS = "id, user_id, amount, status, created_at, updated_at, paid_at"


def _row_to_domain(row: asyncpg.Record) -> Invoice:
    return Invoice(
        id=row["id"],
        user_id=row["user_id"],
        amount=row["amount"],
        status=InvoiceStatus(row["status"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        paid_at=row["paid_at"],
    )


class InvoiceRepository(BaseInvoiceRepository[SQLContext]):
    """SQL implementation of Invoice repository using asyncpg."""

    async def create(self, context: SQLContext, create_invoice: CreateInvoiceCommand) -> Invoice:
        try:
            row = await context.connection.fetchrow(
                f"""
                INSERT INTO invoices (id, user_id, amount, status, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING {_COLUMNS}
                """,
                create_invoice.id,
                create_invoice.user_id,
                create_invoice.amount,
                InvoiceStatus.PENDING.value,
                create_invoice.created_at,
                create_invoice.updated_at,
            )

            if row is None:
                raise DatabaseError("Invoice not created")

            return _row_to_domain(row)
        except Exception as e:
            logger.exception("Database error while creating invoice")
            raise DatabaseError() from e

    async def get_by_id(self, context: SQLContext, invoice_id: str) -> Invoice | None:
        try:
            row = await context.connection.fetchrow(
                f"SELECT {_COLUMNS} FROM invoices WHERE id = $1",
                UUID(invoice_id),
            )
            return _row_to_domain(row) if row else None
        except Exception as e:
            logger.exception("Database error while retrieving invoice by ID")
            raise DatabaseError() from e

    async def update(self, context: SQLContext, invoice: Invoice) -> Invoice:
        try:
            row = await context.connection.fetchrow(
                f"""
                UPDATE invoices
                SET status = $2, paid_at = $3, updated_at = $4
                WHERE id = $1
                RETURNING {_COLUMNS}
                """,
                invoice.id,
                invoice.status.value,
                invoice.paid_at,
                invoice.updated_at,
            )
            if row is None:
                raise DatabaseError("Invoice not found")
            return _row_to_domain(row)
        except DatabaseError:
            raise
        except Exception as e:
            logger.exception("Database error while updating invoice")
            raise DatabaseError() from e

    async def delete_by_user_id(self, context: SQLContext, user_id: str) -> None:
        try:
            await context.connection.execute(
                "DELETE FROM invoices WHERE user_id = $1",
                UUID(user_id),
            )
        except Exception as e:
            logger.exception("Database error while deleting invoices by user_id")
            raise DatabaseError() from e

    async def list(self, context: SQLContext, limit: int, offset: int, user_id: str | None = None) -> list[Invoice]:
        try:
            if user_id:
                rows = await context.connection.fetch(
                    f"""
                    SELECT {_COLUMNS} FROM invoices
                    WHERE user_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2 OFFSET $3
                    """,
                    UUID(user_id),
                    limit,
                    offset,
                )
            else:
                rows = await context.connection.fetch(
                    f"""
                    SELECT {_COLUMNS} FROM invoices
                    ORDER BY created_at DESC
                    LIMIT $1 OFFSET $2
                    """,
                    limit,
                    offset,
                )
            return [_row_to_domain(row) for row in rows]
        except Exception as e:
            logger.exception("Database error while listing invoices")
            raise DatabaseError() from e

    async def count(self, context: SQLContext, user_id: str | None = None) -> int:
        try:
            if user_id:
                result = await context.connection.fetchval(
                    "SELECT COUNT(*) FROM invoices WHERE user_id = $1",
                    UUID(user_id),
                )
            else:
                result = await context.connection.fetchval(
                    "SELECT COUNT(*) FROM invoices",
                )
            return result if result is not None else 0
        except Exception as e:
            logger.exception("Database error while counting invoices")
            raise DatabaseError() from e
