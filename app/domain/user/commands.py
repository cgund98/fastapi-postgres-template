"""User domain commands for operations."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class CreateUser:
    """Command for creating a new user."""

    id: UUID
    email: str
    name: str
    age: int | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class UserUpdate:
    """Command for updating a user with sparse patching support."""

    email: str | None = None
    name: str | None = None
    age: int | None = None
