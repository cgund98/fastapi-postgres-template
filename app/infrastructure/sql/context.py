from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.context import DBContextProtocol


class SQLContext(DBContextProtocol):
    """SQL context."""

    session: AsyncSession

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
