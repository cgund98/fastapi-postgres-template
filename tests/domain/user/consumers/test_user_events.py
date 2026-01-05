"""Tests for user event handlers."""

from uuid import uuid4

import pytest

from app.domain.user.consumers.user_events import UserCreatedEventHandler, UserUpdatedEventHandler
from app.domain.user.events.user_events import UserCreatedEvent, UserUpdatedEvent
from app.infrastructure.messaging.base import BaseEvent


@pytest.mark.asyncio
async def test_user_created_handler(
    user_created_handler: UserCreatedEventHandler,
) -> None:
    """Test UserCreatedEventHandler."""
    event = UserCreatedEvent(aggregate_id=str(uuid4()), email="test@example.com", name="Test User")

    # Should not raise an exception
    await user_created_handler.handle(event)


@pytest.mark.asyncio
async def test_user_created_handler_wrong_type(
    user_created_handler: UserCreatedEventHandler,
) -> None:
    """Test UserCreatedEventHandler with wrong event type."""
    wrong_event = BaseEvent(
        aggregate_id=str(uuid4()),
        event_type="test.event",
        aggregate_type="test",
    )

    with pytest.raises(TypeError):
        await user_created_handler.handle(wrong_event)


@pytest.mark.asyncio
async def test_user_updated_handler(
    user_updated_handler: UserUpdatedEventHandler,
) -> None:
    """Test UserUpdatedEventHandler."""
    event = UserUpdatedEvent(
        aggregate_id=str(uuid4()),
        changes={"name": {"old": "Old Name", "new": "New Name"}},
    )

    # Should not raise an exception
    await user_updated_handler.handle(event)


@pytest.mark.asyncio
async def test_user_updated_handler_wrong_type(
    user_updated_handler: UserUpdatedEventHandler,
) -> None:
    """Test UserUpdatedEventHandler with wrong event type."""
    wrong_event = BaseEvent(
        aggregate_id=str(uuid4()),
        event_type="test.event",
        aggregate_type="test",
    )

    with pytest.raises(TypeError):
        await user_updated_handler.handle(wrong_event)
