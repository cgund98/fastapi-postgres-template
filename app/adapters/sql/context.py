from asyncpg.pool import PoolConnectionProxy

from app.adapters.db.context import DBContextProtocol


class SQLContext(DBContextProtocol):
    """SQL context."""

    _connection: PoolConnectionProxy

    def __init__(self, connection: PoolConnectionProxy) -> None:
        self._connection = connection

    @property
    def connection(self) -> PoolConnectionProxy:
        return self._connection
