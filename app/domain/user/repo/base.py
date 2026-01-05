"""Base User repository interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.user.model import CreateUser, User, UserUpdate


class UserRepository(ABC):
    """Base interface for User repository."""

    @abstractmethod
    async def create(self, create_user: CreateUser) -> User:
        """Create a new user."""
        ...

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None:
        """Get user by ID."""
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        ...

    @abstractmethod
    async def update(self, user: User) -> User:
        """Update an existing user."""
        ...

    @abstractmethod
    async def update_partial(self, user_id: UUID, update: UserUpdate) -> User | None:
        """Update a user with sparse patching support."""
        ...

    @abstractmethod
    async def delete(self, user_id: UUID) -> None:
        """Delete a user by ID."""
        ...

    @abstractmethod
    async def list(self, limit: int, offset: int) -> list[User]:
        """List users with pagination."""
        ...

    @abstractmethod
    async def count(self) -> int:
        """Get total count of users."""
        ...
