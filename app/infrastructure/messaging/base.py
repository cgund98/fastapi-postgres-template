"""Base classes for messaging infrastructure."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class BaseEvent(BaseModel):
    """Base class for all domain events."""

    model_config = ConfigDict()

    event_id: UUID = Field(default_factory=uuid4)
    event_type: str
    aggregate_id: str
    aggregate_type: str
    occurred_at: datetime = Field(default_factory=datetime.now)
    version: int = Field(default=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    payload: dict[str, Any] | None = Field(default=None)

    @field_serializer("event_id", "occurred_at")
    def serialize_field(self, value: UUID | datetime, _info: Any) -> str:
        """Serialize UUID and datetime fields to strings."""
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, datetime):
            return value.isoformat()
        return value
