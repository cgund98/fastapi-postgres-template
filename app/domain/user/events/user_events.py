"""User domain events."""

from pydantic import EmailStr, Field

from app.domain.user.events.constants import (
    UserAggregateType,
    UserEventType,
)
from app.infrastructure.messaging.base import BaseEvent


class UserCreatedEvent(BaseEvent):
    """Event emitted when a user is created."""

    event_type: str = Field(default=UserEventType.CREATED, frozen=True)
    aggregate_type: str = Field(default=UserAggregateType.USER, frozen=True)
    email: EmailStr
    name: str = Field(min_length=1, max_length=255)


class UserUpdatedEvent(BaseEvent):
    """Event emitted when a user is updated."""

    event_type: str = Field(default=UserEventType.UPDATED, frozen=True)
    aggregate_type: str = Field(default=UserAggregateType.USER, frozen=True)
    changes: dict[str, dict[str, str]] = Field(description="Dictionary of changed fields with old and new values")
