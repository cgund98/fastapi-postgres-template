"""User domain model."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.domain.types import UNSET, OptionalOrUnset, RequiredOrUnset


class User(BaseModel):
    """User domain entity."""

    id: UUID
    email: str
    name: str
    age: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"frozen": True}


@dataclass
class CreateUser:
    """Data structure for creating a new user."""

    id: str
    email: str
    name: str
    age: int | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class UserUpdate:
    """Data structure for updating a user with sparse patching support."""

    email: RequiredOrUnset[str] = UNSET
    name: RequiredOrUnset[str] = UNSET
    age: OptionalOrUnset[int] = UNSET
