"""Base protocol for event handlers."""

from abc import ABC, abstractmethod
from typing import TypeVar

from app.infrastructure.messaging.base import BaseEvent

TEvent = TypeVar("TEvent", bound=BaseEvent)


class EventHandler[TEvent](ABC):
    """Base class for event handlers."""

    @abstractmethod
    async def handle(self, event: TEvent) -> None:
        """Handle an event."""
