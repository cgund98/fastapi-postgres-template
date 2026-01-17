"""Database context protocol for type-safe session management."""

from typing import Protocol, TypeVar

# Type variable for database context
DBContext = TypeVar("DBContext", bound="DBContextProtocol")


class DBContextProtocol(Protocol):
    """Protocol for database context objects."""

    pass
