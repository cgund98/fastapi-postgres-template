"""User creation data structures."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class CreateUser:
    """Data structure for creating a new user."""

    id: str
    email: str
    name: str
    created_at: datetime
    updated_at: datetime
