"""PostgreSQL repository for User domain."""

import asyncpg
from asyncpg.pool import PoolConnectionProxy

from app.domain.user.model import User
from app.domain.user.repo.create import CreateUser


class UserRepository:
    """PostgreSQL implementation of User repository."""

    def __init__(self, connection: PoolConnectionProxy) -> None:
        """Initialize repository with a database connection from a pool."""
        self._conn = connection

    async def create(self, create_user: CreateUser) -> User:
        """Create a new user."""
        row = await self._conn.fetchrow(
            """
            INSERT INTO users (id, email, name, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, email, name, created_at, updated_at
            """,
            create_user.id,
            create_user.email,
            create_user.name,
            create_user.created_at,
            create_user.updated_at,
        )
        if row is None:
            raise RuntimeError("Failed to create user: no row returned")
        return self._row_to_user(row)

    async def get_by_id(self, user_id: str) -> User | None:
        """Get user by ID."""
        row = await self._conn.fetchrow(
            """
            SELECT id, email, name, created_at, updated_at
            FROM users
            WHERE id = $1
            """,
            user_id,
        )
        if row is None:
            return None
        return self._row_to_user(row)

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        row = await self._conn.fetchrow(
            """
            SELECT id, email, name, created_at, updated_at
            FROM users
            WHERE email = $1
            """,
            email,
        )
        if row is None:
            return None
        return self._row_to_user(row)

    async def update(self, user: User) -> User:
        """Update an existing user."""
        row = await self._conn.fetchrow(
            """
            UPDATE users
            SET email = $2, name = $3, updated_at = $4
            WHERE id = $1
            RETURNING id, email, name, created_at, updated_at
            """,
            user.id,
            user.email,
            user.name,
            user.updated_at,
        )
        if row is None:
            raise RuntimeError("Failed to update user: no row returned")
        return self._row_to_user(row)

    async def delete(self, user_id: str) -> None:
        """Delete a user by ID."""
        await self._conn.execute(
            """
            DELETE FROM users
            WHERE id = $1
            """,
            user_id,
        )

    async def list(self, limit: int, offset: int) -> list[User]:
        """List users with pagination."""
        rows = await self._conn.fetch(
            """
            SELECT id, email, name, created_at, updated_at
            FROM users
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
            """,
            limit,
            offset,
        )
        return [self._row_to_user(row) for row in rows]

    async def count(self) -> int:
        """Get total count of users."""
        count = await self._conn.fetchval("SELECT COUNT(*) FROM users")
        return count if count is not None else 0

    def _row_to_user(self, row: asyncpg.Record) -> User:
        """Convert database row to User entity."""
        return User.model_validate(dict(row))
