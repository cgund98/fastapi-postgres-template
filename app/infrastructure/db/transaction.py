"""Generic transaction manager interface."""

from contextlib import AbstractAsyncContextManager
from typing import Protocol, runtime_checkable


@runtime_checkable
class TransactionManager(Protocol):
    """Protocol for transaction managers."""

    def transaction(self) -> AbstractAsyncContextManager[None]:
        """Return an async context manager for transaction lifecycle."""
        ...
