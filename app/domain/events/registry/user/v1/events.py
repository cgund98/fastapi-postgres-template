"""User domain events."""

from enum import StrEnum
from uuid import UUID

from pydantic import EmailStr, Field

from app.domain.events.registry.payload import Payload


class UserEventTypes(StrEnum):
    CREATED = "user.v1.created"
    UPDATED = "user.v1.updated"
    DELETED = "user.v1.deleted"


class UserCreatedEvent(Payload):
    """Event emitted when a user is created."""

    user_id: UUID
    email: EmailStr
    name: str = Field(min_length=1, max_length=255)

    @classmethod
    def event_type(cls) -> str:
        return UserEventTypes.CREATED

    def aggregate_id(self) -> str:
        return str(self.user_id)


class UserUpdatedEvent(Payload):
    """Event emitted when a user is updated."""

    user_id: UUID
    changes: dict[str, dict[str, str]] = Field(description="Dictionary of changed fields with old and new values")

    @classmethod
    def event_type(cls) -> str:
        return UserEventTypes.UPDATED

    def aggregate_id(self) -> str:
        return str(self.user_id)
