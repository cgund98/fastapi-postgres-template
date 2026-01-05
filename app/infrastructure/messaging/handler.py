"""Base protocol for event handlers."""

from typing import Protocol, runtime_checkable

from app.infrastructure.messaging.base import BaseEvent


@runtime_checkable
class EventHandler(Protocol):
    """Protocol for event handlers."""

    async def handle(self, event: BaseEvent) -> None:
        """Handle an event."""
        ...
