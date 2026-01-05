"""Base classes for async task execution."""

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any

from app.infrastructure.messaging.base import BaseEvent


class TaskRunner(ABC):
    """Base class for async task runners."""

    @abstractmethod
    async def run(self, task: Callable[..., Awaitable[Any]], *args: Any, **kwargs: Any) -> Any:
        """Run an async task."""
        ...

    @abstractmethod
    async def run_event_handler(self, handler: Callable[[BaseEvent], Awaitable[None]], event: BaseEvent) -> None:
        """Run an event handler task."""
        ...
