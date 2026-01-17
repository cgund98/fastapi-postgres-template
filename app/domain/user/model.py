"""User domain model."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class User(BaseModel):
    """User domain entity."""

    id: UUID
    email: str
    name: str
    age: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"frozen": True}
