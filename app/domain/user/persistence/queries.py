"""User query builders."""

from typing import TYPE_CHECKING, Any

from sqlalchemy import bindparam, delete, func, insert, select, update

from .table import users_table

if TYPE_CHECKING:
    from sqlalchemy import Delete, Insert, Select, Update


def insert_user() -> "Insert":
    """Create an INSERT query for users."""
    return insert(users_table).returning(
        users_table.c.id,
        users_table.c.email,
        users_table.c.name,
        users_table.c.age,
        users_table.c.created_at,
        users_table.c.updated_at,
    )


def select_user_by_id() -> "Select":
    """Create a SELECT query to get a user by ID."""
    return select(
        users_table.c.id,
        users_table.c.email,
        users_table.c.name,
        users_table.c.age,
        users_table.c.created_at,
        users_table.c.updated_at,
    ).where(users_table.c.id == bindparam("user_id"))


def select_user_by_email() -> "Select":
    """Create a SELECT query to get a user by email."""
    return select(
        users_table.c.id,
        users_table.c.email,
        users_table.c.name,
        users_table.c.age,
        users_table.c.created_at,
        users_table.c.updated_at,
    ).where(users_table.c.email == bindparam("email"))


def update_user() -> "Update":
    """Create an UPDATE query for users."""
    return (
        update(users_table)
        .where(users_table.c.id == bindparam("user_id"))
        .returning(
            users_table.c.id,
            users_table.c.email,
            users_table.c.name,
            users_table.c.age,
            users_table.c.created_at,
            users_table.c.updated_at,
        )
    )


def update_user_by_id(values: dict[str, Any]) -> "Update":
    """Create an UPDATE query for users with dynamic values."""
    if not values:
        raise ValueError("No fields to update")

    return (
        update(users_table)
        .where(users_table.c.id == bindparam("user_id"))
        .values(**values)
        .returning(
            users_table.c.id,
            users_table.c.email,
            users_table.c.name,
            users_table.c.age,
            users_table.c.created_at,
            users_table.c.updated_at,
        )
    )


def delete_user() -> "Delete":
    """Create a DELETE query for users."""
    return delete(users_table).where(users_table.c.id == bindparam("user_id"))


def select_users_list() -> "Select":
    """Create a SELECT query to list users with pagination."""
    return (
        select(
            users_table.c.id,
            users_table.c.email,
            users_table.c.name,
            users_table.c.age,
            users_table.c.created_at,
            users_table.c.updated_at,
        )
        .order_by(users_table.c.created_at.desc())
        .limit(bindparam("limit"))
        .offset(bindparam("offset"))
    )


def count_users() -> "Select":
    """Create a SELECT query to count users."""
    return select(func.count()).select_from(users_table)
