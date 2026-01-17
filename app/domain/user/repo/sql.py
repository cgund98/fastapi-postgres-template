"""SQL repository for User domain."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlmodel import Field, SQLModel

from app.domain.user.commands import CreateUser, UserUpdate
from app.domain.user.model import User
from app.domain.user.repo.base import UserRepository as BaseUserRepository
from app.infrastructure.db.exceptions import DatabaseError, NoFieldsToUpdateError
from app.infrastructure.sql.context import SQLContext
from app.observability.logging import get_logger

logger = get_logger(__name__)


class UserORM(SQLModel, table=True):
    """User ORM model for database persistence."""

    __tablename__ = "users"

    id: UUID = Field(primary_key=True)
    email: str = Field(unique=True, index=True)
    name: str
    age: int | None = None
    created_at: datetime
    updated_at: datetime


class UserRepository(BaseUserRepository[SQLContext]):
    """SQL implementation of User repository using SQLModel."""

    @staticmethod
    def _orm_to_domain(orm_user: UserORM) -> User:
        """Convert ORM model to domain model."""
        return User(
            id=orm_user.id,
            email=orm_user.email,
            name=orm_user.name,
            age=orm_user.age,
            created_at=orm_user.created_at,
            updated_at=orm_user.updated_at,
        )

    async def create(self, context: SQLContext, create_user: CreateUser) -> User:
        """Create a new user."""
        try:
            orm_user = UserORM(
                id=create_user.id,
                email=create_user.email,
                name=create_user.name,
                age=create_user.age,
                created_at=create_user.created_at,
                updated_at=create_user.updated_at,
            )

            context.session.add(orm_user)
            await context.session.flush()
            await context.session.refresh(orm_user)

            return self._orm_to_domain(orm_user)
        except Exception as e:
            logger.exception("Database error while creating user")
            raise DatabaseError() from e

    async def get_by_id(self, context: SQLContext, user_id: UUID) -> User | None:
        """Get user by ID."""
        logger.info("Getting user by ID", user_id=user_id)

        try:
            orm_user = await context.session.get(UserORM, user_id)

            if orm_user is None:
                return None

            return self._orm_to_domain(orm_user)
        except Exception as e:
            logger.exception("Database error while retrieving user by ID")
            raise DatabaseError() from e

    async def get_by_email(self, context: SQLContext, email: str) -> User | None:
        """Get user by email."""
        try:
            statement = select(UserORM).where(UserORM.email == email)
            result = await context.session.execute(statement)
            orm_user = result.scalar_one_or_none()

            if orm_user is None:
                return None

            return self._orm_to_domain(orm_user)
        except Exception as e:
            logger.exception("Database error while retrieving user by email")
            raise DatabaseError() from e

    async def update(self, context: SQLContext, user: User) -> User:
        """Update an existing user."""
        try:
            # Get the existing user from the database
            orm_user = await context.session.get(UserORM, user.id)

            if orm_user is None:
                raise DatabaseError("User not found")

            # Update fields
            orm_user.email = user.email
            orm_user.name = user.name
            orm_user.updated_at = datetime.now()

            await context.session.flush()
            await context.session.refresh(orm_user)

            return self._orm_to_domain(orm_user)
        except Exception as e:
            logger.exception("Database error while updating user")
            raise DatabaseError() from e

    async def update_partial(self, context: SQLContext, user_id: UUID, update: UserUpdate) -> User:
        """Update a user with sparse patching support."""
        try:
            # Get the existing user
            orm_user = await context.session.get(UserORM, user_id)

            if orm_user is None:
                raise DatabaseError("User not found")

            # Track if any fields are being updated
            has_updates = False

            # Update only non-None fields explicitly
            if update.email is not None:
                orm_user.email = update.email
                has_updates = True

            if update.name is not None:
                orm_user.name = update.name
                has_updates = True

            if update.age is not None:
                orm_user.age = update.age
                has_updates = True

            if not has_updates:
                raise NoFieldsToUpdateError()

            # Always update the updated_at timestamp when fields change
            orm_user.updated_at = datetime.now()

            await context.session.flush()
            await context.session.refresh(orm_user)

            return self._orm_to_domain(orm_user)

        except NoFieldsToUpdateError:
            raise

        except Exception as e:
            logger.exception("Database error while partially updating user")
            raise DatabaseError() from e

    async def delete(self, context: SQLContext, user_id: UUID) -> None:
        """Delete a user by ID."""
        try:
            orm_user = await context.session.get(UserORM, user_id)

            if orm_user is not None:
                await context.session.delete(orm_user)
                await context.session.flush()
        except Exception as e:
            logger.exception("Database error while deleting user")
            raise DatabaseError() from e

    async def list(self, context: SQLContext, limit: int, offset: int) -> list[User]:
        """List users with pagination."""
        try:
            statement = select(UserORM).order_by(UserORM.created_at.desc()).limit(limit).offset(offset)

            result = await context.session.execute(statement)
            orm_users = result.scalars().all()

            return [self._orm_to_domain(orm_user) for orm_user in orm_users]
        except Exception as e:
            logger.exception("Database error while listing users")
            raise DatabaseError() from e

    async def count(self, context: SQLContext) -> int:
        """Get total count of users."""
        try:
            statement = select(func.count()).select_from(UserORM)

            result = await context.session.execute(statement)
            count = result.scalar()

            return count if count is not None else 0
        except Exception as e:
            logger.exception("Database error while counting users")
            raise DatabaseError() from e
