"""Base classes for event consumers."""

from abc import ABC, abstractmethod

from app.domain.events.router import EventRouter


class EventConsumer(ABC):
    """Base class for event consumers."""

    @abstractmethod
    async def consume(self, router: "EventRouter") -> None:
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
