"""User domain event consumers."""

from app.domain.user.events.constants import UserEventType
from app.domain.user.events.user_events import UserCreatedEvent, UserUpdatedEvent
from app.infrastructure.messaging.handler import EventHandler
from app.observability.logging import get_logger

logger = get_logger(__name__)


class UserCreatedEventHandler(EventHandler[UserCreatedEvent]):
    """Handler for user.created events."""

    async def handle(self, event: UserCreatedEvent) -> None:
        """Handle user.created event."""
        user_event = event  # Type narrowing
        logger.info(
            f"Processing {UserEventType.CREATED} event",
            event_id=str(user_event.event_id),
            aggregate_id=user_event.aggregate_id,
            email=user_event.email,
            name=user_event.name,
        )
        # Add your business logic here
        # Example: send welcome email, create user profile, etc.


class UserUpdatedEventHandler(EventHandler[UserUpdatedEvent]):
    """Handler for user.updated events."""

    async def handle(self, event: UserUpdatedEvent) -> None:
        """Handle user.updated event."""
        user_event = event  # Type narrowing
        logger.info(
            f"Processing {UserEventType.UPDATED} event",
            event_id=str(user_event.event_id),
            aggregate_id=user_event.aggregate_id,
            changes=user_event.changes,
        )
        # Add your business logic here
        # Example: update search index, notify other services, etc.
