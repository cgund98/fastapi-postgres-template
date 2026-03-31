from dataclasses import dataclass
from typing import Any

from app.adapters.events.handler import EventHandler
from app.domain.events.registry.envelope import Envelope
from app.domain.events.registry.payload import Payload


@dataclass
class RouteRegistration[TModel: Payload]:
    model: type[TModel]
    handler: EventHandler[TModel]


class EventRouter:
    """Event router."""

    def __init__(self) -> None:
        self._routes: dict[str, RouteRegistration[Any]] = {}

    def register[TModel: Payload](self, model: type[TModel], handler: EventHandler[TModel]) -> None:
        """Register a route for an event."""

        self._routes[model.event_type()] = RouteRegistration[TModel](model=model, handler=handler)

    async def route(self, envelope: Envelope) -> None:
        """Route many events."""
        if envelope.type not in self._routes:
            raise ValueError(f"No route registered for event type: {envelope.type}")

        route = self._routes.get(envelope.type)
        if route is None:
            raise ValueError(f"No route registered for event type: {envelope.type}")

        payload = route.model.model_validate_json(envelope.data)
        await route.handler.handle(event=payload, envelope=envelope)
