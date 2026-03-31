"""User domain event consumers."""

from app.adapters.events.handler import EventHandler
from app.domain.events.registry.envelope import Envelope
from app.domain.events.registry.user.v1.events import UserCreatedEvent, UserEventTypes, UserUpdatedEvent
from app.observability.logging import get_logger

logger = get_logger(__name__)


class UserCreatedEventHandler(EventHandler[UserCreatedEvent]):
    """Handler for user.created events."""

    async def handle(self, event: UserCreatedEvent, envelope: Envelope) -> None:
        """Handle user.created event."""
        user_event = event  # Type narrowing
        logger.info(
            f"Processing {UserEventTypes.CREATED} event",
            event_id=envelope.id,
            user_id=user_event.user_id,
            email=user_event.email,
            name=user_event.name,
        )
        # Add your business logic here
        # Example: send welcome email, create user profile, etc.


class UserUpdatedEventHandler(EventHandler[UserUpdatedEvent]):
    """Handler for user.updated events."""

    async def handle(self, event: UserUpdatedEvent, envelope: Envelope) -> None:
        """Handle user.updated event."""
        user_event = event  # Type narrowing
        logger.info(
            f"Processing {UserEventTypes.UPDATED} event",
            event_id=envelope.id,
            user_id=user_event.user_id,
            changes=user_event.changes,
        )
        # Add your business logic here
        # Example: update search index, notify other services, etc.
