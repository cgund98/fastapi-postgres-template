"""Constants for user domain events."""

from enum import Enum


class UserAggregateType(str, Enum):
    """User aggregate type."""

    USER = "user"


class UserEventType(str, Enum):
    """User event types."""

    CREATED = "user.created"
    UPDATED = "user.updated"
