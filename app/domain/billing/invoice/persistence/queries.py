"""Invoice query builders."""

from typing import TYPE_CHECKING

from sqlalchemy import bindparam, delete, func, insert, select, update

from .table import invoices_table

if TYPE_CHECKING:
    from sqlalchemy import Delete, Insert, Select, Update


def insert_invoice() -> "Insert":
    """Create an INSERT query for invoices."""
    return insert(invoices_table).returning(
        invoices_table.c.id,
        invoices_table.c.user_id,
        invoices_table.c.amount,
        invoices_table.c.status,
        invoices_table.c.created_at,
        invoices_table.c.paid_at,
        invoices_table.c.updated_at,
    )


def select_invoice_by_id() -> "Select":
    """Create a SELECT query to get an invoice by ID."""
    return select(
        invoices_table.c.id,
        invoices_table.c.user_id,
        invoices_table.c.amount,
        invoices_table.c.status,
        invoices_table.c.created_at,
        invoices_table.c.paid_at,
        invoices_table.c.updated_at,
    ).where(invoices_table.c.id == bindparam("invoice_id"))


def update_invoice() -> "Update":
    """Create an UPDATE query for invoices."""
    return (
        update(invoices_table)
        .where(invoices_table.c.id == bindparam("invoice_id"))
        .returning(
            invoices_table.c.id,
            invoices_table.c.user_id,
            invoices_table.c.amount,
            invoices_table.c.status,
            invoices_table.c.created_at,
            invoices_table.c.paid_at,
            invoices_table.c.updated_at,
        )
    )


def delete_invoices_by_user_id() -> "Delete":
    """Create a DELETE query for invoices by user_id."""
    return delete(invoices_table).where(invoices_table.c.user_id == bindparam("user_id"))


def select_invoices_list() -> "Select":
    """Create a SELECT query to list invoices with pagination."""
    base_query = select(
        invoices_table.c.id,
        invoices_table.c.user_id,
        invoices_table.c.amount,
        invoices_table.c.status,
        invoices_table.c.created_at,
        invoices_table.c.paid_at,
        invoices_table.c.updated_at,
    ).order_by(invoices_table.c.created_at.desc())
    return base_query


def select_invoices_list_with_user_filter() -> "Select":
    """Create a SELECT query to list invoices filtered by user_id."""
    return (
        select_invoices_list()
        .where(invoices_table.c.user_id == bindparam("user_id"))
        .limit(bindparam("limit"))
        .offset(bindparam("offset"))
    )


def select_invoices_list_without_filter() -> "Select":
    """Create a SELECT query to list invoices without user filter."""
    return select_invoices_list().limit(bindparam("limit")).offset(bindparam("offset"))


def count_invoices() -> "Select":
    """Create a SELECT query to count invoices."""
    return select(func.count()).select_from(invoices_table)


def count_invoices_by_user_id() -> "Select":
    """Create a SELECT query to count invoices by user_id."""
    return select(func.count()).select_from(invoices_table).where(invoices_table.c.user_id == bindparam("user_id"))
