"""Generic transaction manager interface."""

from contextlib import AbstractAsyncContextManager
from typing import Protocol, TypeVar, runtime_checkable

from app.infrastructure.db.context import DBContextProtocol

TContext = TypeVar("TContext", bound=DBContextProtocol)


@runtime_checkable
class TransactionManager[TContext](Protocol):
    """Protocol for transaction managers."""

    def transaction(self) -> AbstractAsyncContextManager[TContext]:
        """Return an async context manager for transaction lifecycle."""
        ...
