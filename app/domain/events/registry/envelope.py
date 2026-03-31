from datetime import UTC, datetime
from uuid import uuid4

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from app.domain.events.correlation import get_correlation_id
from app.domain.events.registry.payload import Payload


def _generate_correlation_id() -> str:
    """Generate a correlation ID."""
    return get_correlation_id() or str(uuid4())


class EventAttributes(BaseModel):
    """
    Attributes for the Event. These are additional metadata that are not part of the payload.
    """

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    correlation_id: str = Field(default_factory=_generate_correlation_id)
    aggregate_id: str | None = None


class Envelope(BaseModel):
    """
    CloudEvents-compatible envelope DTO.
    """

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    id: str
    type: str
    time: AwareDatetime
    data: str
    source: str
    specversion: str = "1.0"

    attributes: EventAttributes

    def to_json(self) -> str:
        """
        Serialize the Envelope to a JSON string.
        """
        return self.model_dump_json()

    @classmethod
    def build(cls, *, payload: Payload, source: str) -> "Envelope":
        """
        Build an Envelope from a data message and source.
        """

        attributes = EventAttributes(
            aggregate_id=payload.aggregate_id(),
        )

        return cls(
            id=str(uuid4()),
            type=payload.event_type(),
            time=datetime.now(UTC),
            data=payload.to_json(),
            source=source,
            attributes=attributes,
        )
