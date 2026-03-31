from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.domain.events.registry.payload import Payload


@dataclass
class PublishArgs:
    payload: Payload
    source: str


class EventPublisher(ABC):
    """Event publisher."""

    @abstractmethod
    async def publish(self, args: PublishArgs) -> None:
        """Publish an event."""

    @abstractmethod
    async def publish_many(self, args: list[PublishArgs]) -> None:
        """Publish many events."""
