"""Base classes for event publishers."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.infrastructure.messaging.base import BaseEvent


class BasePublisher(ABC):
    """Base class for event publishers."""

    @abstractmethod
    async def publish(self, event: "BaseEvent") -> None:
        """Publish an event to the message bus."""
        ...
