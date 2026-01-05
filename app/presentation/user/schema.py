"""User API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserCreateRequest(BaseModel):
    """Request schema for creating a user."""

    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)


class UserUpdateRequest(BaseModel):
    """Request schema for updating a user."""

    name: str = Field(..., min_length=1, max_length=255)


class UserResponse(BaseModel):
    """Response schema for user."""

    id: UUID
    email: str
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True
