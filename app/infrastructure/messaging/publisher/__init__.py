"""Event publisher implementations."""

from app.infrastructure.messaging.base import BaseEvent
from app.infrastructure.messaging.publisher.base import BasePublisher
from app.infrastructure.messaging.publisher.sns import SNSPublisher


class EventPublisher:
    """Generic event publisher that delegates to implementation."""

    def __init__(self, publisher: BasePublisher) -> None:
        """Initialize with a publisher implementation."""
        self._publisher = publisher

    async def publish(self, event: BaseEvent) -> None:
        """Publish an event."""
        await self._publisher.publish(event)


__all__ = ["EventPublisher", "BasePublisher", "SNSPublisher"]
