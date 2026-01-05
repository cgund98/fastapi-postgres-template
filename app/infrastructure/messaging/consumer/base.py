"""Base classes for event consumers."""

from abc import ABC, abstractmethod
from collections.abc import Awaitable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from app.infrastructure.messaging.base import BaseEvent


class BaseConsumer(ABC):
    """Base class for event consumers."""

    @abstractmethod
    async def consume(self, handler: "Callable[[BaseEvent], Awaitable[None]]") -> None:
        """Start consuming events and call handler for each event."""
        ...

    @abstractmethod
    async def ack(self, receipt_handle: str) -> None:
        """Acknowledge successful processing of an event."""
        ...

    @abstractmethod
    async def nack(self, receipt_handle: str) -> None:
        """Negatively acknowledge failed processing of an event."""
        ...
