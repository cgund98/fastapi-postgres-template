"""User API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.domain.types import UNSET_STR


class UserCreateRequest(BaseModel):
    """Request schema for creating a user."""

    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    age: int | None = Field(default=None, ge=0, description="User age")


class UserUpdateRequest(BaseModel):
    """Request schema for updating a user."""

    name: str = Field(..., min_length=1, max_length=255)


class UserPatchRequest(BaseModel):
    """Request schema for patching a user with sparse updates."""

    email: str = Field(default=UNSET_STR, description="Email to update")
    name: str = Field(default=UNSET_STR, min_length=1, max_length=255, description="Name to update")
    age: int | str | None = Field(default=UNSET_STR, ge=0, description="Age to update")


class UserResponse(BaseModel):
    """Response schema for user."""

    id: UUID
    email: str
    name: str
    age: int | None
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True
