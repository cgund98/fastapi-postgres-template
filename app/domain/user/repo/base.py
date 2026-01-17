"""Base User repository interface."""

from abc import ABC, abstractmethod
from typing import TypeVar
from uuid import UUID

from app.domain.user.commands import CreateUser, UserUpdate
from app.domain.user.model import User
from app.infrastructure.db.context import DBContextProtocol

TContext = TypeVar("TContext", bound=DBContextProtocol)


class UserRepository[TContext](ABC):
    """Base interface for User repository."""

    @abstractmethod
    async def create(self, context: TContext, create_user: CreateUser) -> User:
        """Create a new user."""
        ...

    @abstractmethod
    async def get_by_id(self, context: TContext, user_id: UUID) -> User | None:
        """Get user by ID."""
        ...

    @abstractmethod
    async def get_by_email(self, context: TContext, email: str) -> User | None:
        """Get user by email."""
        ...

    @abstractmethod
    async def update(self, context: TContext, user: User) -> User:
        """Update an existing user."""
        ...

    @abstractmethod
    async def update_partial(self, context: TContext, user_id: UUID, update: UserUpdate) -> User:
        """Update a user with sparse patching support."""
        ...

    @abstractmethod
    async def delete(self, context: TContext, user_id: UUID) -> None:
        """Delete a user by ID."""
        ...

    @abstractmethod
    async def list(self, context: TContext, limit: int, offset: int) -> list[User]:
        """List users with pagination."""
        ...

    @abstractmethod
    async def count(self, context: TContext) -> int:
        """Get total count of users."""
        ...
