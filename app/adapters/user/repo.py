"""SQL repository for User domain."""

from datetime import datetime
from uuid import UUID

import asyncpg

from app.adapters.db.exceptions import DatabaseError, NoFieldsToUpdateError
from app.adapters.sql.context import SQLContext
from app.domain.user.commands import CreateUserCommand, UserUpdateCommand
from app.domain.user.model import User
from app.domain.user.repo import UserRepository as BaseUserRepository
from app.observability.logging import get_logger

logger = get_logger(__name__)

_COLUMNS = "id, email, name, age, created_at, updated_at"


def _row_to_domain(row: asyncpg.Record) -> User:
    return User(
        id=row["id"],
        email=row["email"],
        name=row["name"],
        age=row["age"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class UserRepository(BaseUserRepository[SQLContext]):
    """SQL implementation of User repository using asyncpg."""

    async def create(self, context: SQLContext, create_user: CreateUserCommand) -> User:
        try:
            row = await context.connection.fetchrow(
                f"""
                INSERT INTO users (id, email, name, age, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING {_COLUMNS}
                """,
                create_user.id,
                create_user.email,
                create_user.name,
                create_user.age,
                create_user.created_at,
                create_user.updated_at,
            )

            if row is None:
                raise DatabaseError("User not created")

            return _row_to_domain(row)
        except Exception as e:
            logger.exception("Database error while creating user")
            raise DatabaseError() from e

    async def get_by_id(self, context: SQLContext, user_id: UUID) -> User | None:
        logger.info("Getting user by ID", user_id=user_id)
        try:
            row = await context.connection.fetchrow(
                f"SELECT {_COLUMNS} FROM users WHERE id = $1",
                user_id,
            )
            return _row_to_domain(row) if row else None
        except Exception as e:
            logger.exception("Database error while retrieving user by ID")
            raise DatabaseError() from e

    async def get_by_email(self, context: SQLContext, email: str) -> User | None:
        try:
            row = await context.connection.fetchrow(
                f"SELECT {_COLUMNS} FROM users WHERE email = $1",
                email,
            )
            return _row_to_domain(row) if row else None
        except Exception as e:
            logger.exception("Database error while retrieving user by email")
            raise DatabaseError() from e

    async def update(self, context: SQLContext, user: User) -> User:
        try:
            row = await context.connection.fetchrow(
                f"""
                UPDATE users
                SET email = $2, name = $3, age = $4, updated_at = $5
                WHERE id = $1
                RETURNING {_COLUMNS}
                """,
                user.id,
                user.email,
                user.name,
                user.age,
                datetime.now(),
            )
            if row is None:
                raise DatabaseError("User not found")
            return _row_to_domain(row)
        except DatabaseError:
            raise
        except Exception as e:
            logger.exception("Database error while updating user")
            raise DatabaseError() from e

    async def update_partial(self, context: SQLContext, user_id: UUID, update: UserUpdateCommand) -> User:
        try:
            if update.email is None and update.name is None and update.age is None:
                raise NoFieldsToUpdateError()

            row = await context.connection.fetchrow(
                f"""
                UPDATE users SET
                    email = COALESCE($2, email),
                    name = COALESCE($3, name),
                    age = COALESCE($4, age),
                    updated_at = $5
                WHERE id = $1
                RETURNING {_COLUMNS}
                """,
                user_id,
                update.email,
                update.name,
                update.age,
                datetime.now(),
            )
            if row is None:
                raise DatabaseError("User not found")
            return _row_to_domain(row)

        except (NoFieldsToUpdateError, DatabaseError):
            raise
        except Exception as e:
            logger.exception("Database error while partially updating user")
            raise DatabaseError() from e

    async def delete(self, context: SQLContext, user_id: UUID) -> None:
        try:
            await context.connection.execute(
                "DELETE FROM users WHERE id = $1",
                user_id,
            )
        except Exception as e:
            logger.exception("Database error while deleting user")
            raise DatabaseError() from e

    async def list(self, context: SQLContext, limit: int, offset: int) -> list[User]:
        try:
            rows = await context.connection.fetch(
                f"""
                SELECT {_COLUMNS} FROM users
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
                """,
                limit,
                offset,
            )
            return [_row_to_domain(row) for row in rows]
        except Exception as e:
            logger.exception("Database error while listing users")
            raise DatabaseError() from e

    async def count(self, context: SQLContext) -> int:
        try:
            result = await context.connection.fetchval("SELECT COUNT(*) FROM users")
            return result if result is not None else 0
        except Exception as e:
            logger.exception("Database error while counting users")
            raise DatabaseError() from e
