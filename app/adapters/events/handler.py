"""Base protocol for event handlers."""

from abc import ABC, abstractmethod
from typing import TypeVar

from app.adapters.events.base import BaseEvent
from app.domain.events.registry.envelope import Envelope

TEvent = TypeVar("TEvent", bound=BaseEvent)


class EventHandler[TEvent](ABC):
    """Base class for event handlers."""

    @abstractmethod
    async def handle(self, event: TEvent, envelope: Envelope) -> None:
        """Handle an event."""
