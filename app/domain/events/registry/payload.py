from abc import ABC, abstractmethod

from pydantic import BaseModel


class Payload(BaseModel, ABC):
    """Base class for all payloads."""

    @classmethod
    @abstractmethod
    def event_type(cls) -> str:
        """The event type of the payload."""

    @abstractmethod
    def aggregate_id(self) -> str:
        """The aggregate ID of the payload."""

    def to_json(self) -> str:
        """Serialize the payload to a JSON string."""
        return self.model_dump_json()
