"""Base Invoice repository interface."""

from abc import ABC, abstractmethod

from app.domain.billing.invoice.model import CreateInvoice, Invoice


class InvoiceRepository(ABC):
    """Base interface for Invoice repository."""

    @abstractmethod
    async def create(self, create_invoice: CreateInvoice) -> Invoice:
        """Create a new invoice."""
        ...

    @abstractmethod
    async def get_by_id(self, invoice_id: str) -> Invoice | None:
        """Get invoice by ID."""
        ...

    @abstractmethod
    async def update(self, invoice: Invoice) -> Invoice:
        """Update an existing invoice."""
        ...

    @abstractmethod
    async def delete_by_user_id(self, user_id: str) -> None:
        """Delete all invoices for a user."""
        ...

    @abstractmethod
    async def list(self, limit: int, offset: int, user_id: str | None = None) -> list[Invoice]:
        """List invoices with pagination and optional user_id filter."""
        ...

    @abstractmethod
    async def count(self, user_id: str | None = None) -> int:
        """Get total count of invoices, optionally filtered by user_id."""
        ...
