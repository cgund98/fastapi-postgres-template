"""Tests for user event handlers."""

from uuid import uuid4

import pytest

from app.domain.events.registry.envelope import Envelope
from app.domain.events.registry.payload import Payload
from app.domain.events.registry.user.v1.events import UserCreatedEvent, UserUpdatedEvent
from app.domain.user.handlers import UserCreatedEventHandler, UserUpdatedEventHandler


def _make_envelope(payload: Payload) -> Envelope:
    return Envelope.build(payload=payload, source="test")


@pytest.mark.asyncio
async def test_user_created_handler(
    user_created_handler: UserCreatedEventHandler,
) -> None:
    """Test UserCreatedEventHandler."""
    event = UserCreatedEvent(user_id=uuid4(), email="test@example.com", name="Test User")
    await user_created_handler.handle(event, _make_envelope(event))


@pytest.mark.asyncio
async def test_user_updated_handler(
    user_updated_handler: UserUpdatedEventHandler,
) -> None:
    """Test UserUpdatedEventHandler."""
    event = UserUpdatedEvent(
        user_id=uuid4(),
        changes={"name": {"old": "Old Name", "new": "New Name"}},
    )
    await user_updated_handler.handle(event, _make_envelope(event))
