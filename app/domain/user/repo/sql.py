"""SQL repository for User domain."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncConnection

from app.domain.user.model import CreateUser, User, UserUpdate
from app.domain.user.persistence.queries import (
    count_users,
    delete_user,
    insert_user,
    select_user_by_email,
    select_user_by_id,
    select_users_list,
    update_user,
    update_user_by_id,
)
from app.domain.user.repo.base import UserRepository as BaseUserRepository
from app.infrastructure.db.exceptions import DatabaseError, NoFieldsToUpdateError
from app.infrastructure.db.update_mapper import build_update_values
from app.observability.logging import get_logger

if TYPE_CHECKING:
    from sqlalchemy import Result
else:
    Result = object  # Placeholder for runtime

logger = get_logger(__name__)


class UserRepository(BaseUserRepository):
    """SQL implementation of User repository using SQLAlchemy."""

    def __init__(self, conn: AsyncConnection) -> None:
        """Initialize repository with a database connection."""
        self._conn = conn

    async def create(self, create_user: CreateUser) -> User:
        """Create a new user."""
        try:
            stmt = insert_user().values(
                id=create_user.id,
                email=create_user.email,
                name=create_user.name,
                age=create_user.age,
                created_at=create_user.created_at,
                updated_at=create_user.updated_at,
            )
            result: Result = await self._conn.execute(stmt)
            row = result.first()

            if row is None:
                raise DatabaseError()

            return User(**row._mapping)
        except Exception as e:
            logger.exception("Database error while creating user")
            raise DatabaseError() from e

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Get user by ID."""
        logger.info("Getting user by ID", user_id=user_id)
        try:
            stmt = select_user_by_id()
            result: Result = await self._conn.execute(stmt, {"user_id": user_id})
            row = result.first()

            if row is None:
                return None

            return User(**row._mapping)
        except Exception as e:
            logger.exception("Database error while retrieving user by ID")
            raise DatabaseError() from e

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        try:
            stmt = select_user_by_email()
            result: Result = await self._conn.execute(stmt, {"email": email})
            row = result.first()

            if row is None:
                return None

            return User(**row._mapping)

        except Exception as e:
            logger.exception("Database error while retrieving user by email")
            raise DatabaseError() from e

    async def update(self, user: User) -> User:
        """Update an existing user."""
        try:
            stmt = update_user().values(
                email=user.email,
                name=user.name,
                updated_at=user.updated_at,
            )
            result: Result = await self._conn.execute(stmt, {"user_id": user.id})
            row = result.first()

            if row is None:
                raise DatabaseError()

            return User(**row._mapping)

        except Exception as e:
            logger.exception("Database error while updating user")
            raise DatabaseError() from e

    async def update_partial(self, user_id: UUID, update: UserUpdate) -> User:
        """Update a user with sparse patching support."""
        try:
            values = build_update_values(update)
            if not values:
                raise NoFieldsToUpdateError()

            # Always update the updated_at timestamp
            values["updated_at"] = datetime.now()

            stmt = update_user_by_id(values)
            result: Result = await self._conn.execute(stmt, {"user_id": user_id})
            row = result.first()

            if not row:
                raise DatabaseError("Query returned no rows when updating user")

            return User(**row._mapping)

        except NoFieldsToUpdateError:
            raise

        except Exception as e:
            logger.exception("Database error while partially updating user")
            raise DatabaseError() from e

    async def delete(self, user_id: UUID) -> None:
        """Delete a user by ID."""
        try:
            stmt = delete_user()
            await self._conn.execute(stmt, {"user_id": user_id})
        except Exception as e:
            logger.exception("Database error while deleting user")
            raise DatabaseError() from e

    async def list(self, limit: int, offset: int) -> list[User]:
        """List users with pagination."""
        try:
            stmt = select_users_list()
            result: Result = await self._conn.execute(stmt, {"limit": limit, "offset": offset})
            rows = result.all()
            return [User(**row._mapping) for row in rows]
        except Exception as e:
            logger.exception("Database error while listing users")
            raise DatabaseError() from e

    async def count(self) -> int:
        """Get total count of users."""
        try:
            stmt = count_users()
            result: Result = await self._conn.execute(stmt)
            count = result.scalar()
            return count if count is not None else 0
        except Exception as e:
            logger.exception("Database error while counting users")
            raise DatabaseError() from e
