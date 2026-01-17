"""SQL repository for Invoice domain."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlmodel import Field, SQLModel

from app.domain.billing.invoice.commands import CreateInvoice
from app.domain.billing.invoice.model import Invoice, InvoiceStatus
from app.domain.billing.invoice.repo.base import InvoiceRepository as BaseInvoiceRepository
from app.infrastructure.db.exceptions import DatabaseError
from app.infrastructure.sql.context import SQLContext
from app.observability.logging import get_logger

logger = get_logger(__name__)


class InvoiceORM(SQLModel, table=True):
    """Invoice ORM model for database persistence."""

    __tablename__ = "invoices"

    id: UUID = Field(primary_key=True)
    user_id: UUID = Field(foreign_key="users.id")
    amount: Decimal
    status: str
    created_at: datetime
    updated_at: datetime
    paid_at: datetime | None = None


class InvoiceRepository(BaseInvoiceRepository[SQLContext]):
    """SQL implementation of Invoice repository using SQLModel."""

    @staticmethod
    def _orm_to_domain(orm_invoice: InvoiceORM) -> Invoice:
        """Convert ORM model to domain model."""
        return Invoice(
            id=orm_invoice.id,
            user_id=orm_invoice.user_id,
            amount=orm_invoice.amount,
            status=orm_invoice.status,
            created_at=orm_invoice.created_at,
            updated_at=orm_invoice.updated_at,
            paid_at=orm_invoice.paid_at,
        )

    async def create(self, context: SQLContext, create_invoice: CreateInvoice) -> Invoice:
        """Create a new invoice."""
        try:
            orm_invoice = InvoiceORM(
                id=create_invoice.id,
                user_id=create_invoice.user_id,
                amount=create_invoice.amount,
                status=InvoiceStatus.PENDING,
                created_at=create_invoice.created_at,
                updated_at=create_invoice.updated_at,
            )

            context.session.add(orm_invoice)
            await context.session.flush()
            await context.session.refresh(orm_invoice)

            return self._orm_to_domain(orm_invoice)
        except Exception as e:
            logger.exception("Database error while creating invoice")
            raise DatabaseError() from e

    async def get_by_id(self, context: SQLContext, invoice_id: str) -> Invoice | None:
        """Get invoice by ID."""
        try:
            orm_invoice = await context.session.get(InvoiceORM, UUID(invoice_id))

            if orm_invoice is None:
                return None

            return self._orm_to_domain(orm_invoice)
        except Exception as e:
            logger.exception("Database error while retrieving invoice by ID")
            raise DatabaseError() from e

    async def update(self, context: SQLContext, invoice: Invoice) -> Invoice:
        """Update an existing invoice."""
        try:
            # Get the existing invoice from the database
            orm_invoice = await context.session.get(InvoiceORM, invoice.id)

            if orm_invoice is None:
                raise DatabaseError("Invoice not found")

            # Update fields
            orm_invoice.status = invoice.status
            orm_invoice.paid_at = invoice.paid_at
            orm_invoice.updated_at = invoice.updated_at

            await context.session.flush()
            await context.session.refresh(orm_invoice)

            return self._orm_to_domain(orm_invoice)
        except Exception as e:
            logger.exception("Database error while updating invoice")
            raise DatabaseError() from e

    async def delete_by_user_id(self, context: SQLContext, user_id: str) -> None:
        """Delete all invoices for a user."""
        try:
            statement = select(InvoiceORM).where(InvoiceORM.user_id == UUID(user_id))

            result = await context.session.execute(statement)
            orm_invoices = result.scalars().all()

            for orm_invoice in orm_invoices:
                await context.session.delete(orm_invoice)

            await context.session.flush()
        except Exception as e:
            logger.exception("Database error while deleting invoices by user_id")
            raise DatabaseError() from e

    async def list(self, context: SQLContext, limit: int, offset: int, user_id: str | None = None) -> list[Invoice]:
        """List invoices with pagination and optional user_id filter."""
        try:
            statement = select(InvoiceORM).order_by(InvoiceORM.created_at.desc())

            if user_id:
                statement = statement.where(InvoiceORM.user_id == UUID(user_id))

            statement = statement.limit(limit).offset(offset)

            result = await context.session.execute(statement)
            orm_invoices = result.scalars().all()

            return [self._orm_to_domain(orm_invoice) for orm_invoice in orm_invoices]
        except Exception as e:
            logger.exception("Database error while listing invoices")
            raise DatabaseError() from e

    async def count(self, context: SQLContext, user_id: str | None = None) -> int:
        """Get total count of invoices, optionally filtered by user_id."""
        try:
            statement = select(func.count()).select_from(InvoiceORM)

            if user_id:
                statement = statement.where(InvoiceORM.user_id == UUID(user_id))

            result = await context.session.execute(statement)
            count = result.scalar()

            return count if count is not None else 0
        except Exception as e:
            logger.exception("Database error while counting invoices")
            raise DatabaseError() from e
