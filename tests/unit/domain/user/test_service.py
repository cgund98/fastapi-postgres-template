"""Tests for UserService."""

from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest

from app.domain.user.model import User
from app.domain.user.service import UserService
from app.infrastructure.db.exceptions import NoFieldsToUpdateError


@pytest.mark.asyncio
async def test_create_user(
    user_service: UserService,
    mock_user_repository: Any,
    mock_event_publisher: Any,
) -> None:
    """Test creating a user."""
    email = "test@example.com"
    name = "Test User"
    age = 25
    user_id = uuid4()
    now = datetime.now()

    # Mock repository responses
    created_user = User(
        id=user_id,
        email=email,
        name=name,
        age=age,
        created_at=now,
        updated_at=now,
    )
    mock_user_repository.create.return_value = created_user

    with patch("app.domain.user.service.validate_create_user_request", new_callable=AsyncMock) as mock_validate:
        user = await user_service.create_user(email=email, name=name, age=age)

        assert user.email == email
        assert user.name == name
        assert user.age == age
        assert isinstance(user.id, UUID)
        assert user.created_at is not None
        assert user.updated_at is not None

        # Verify validator was called (with context)
        assert mock_validate.call_count == 1
        call_args = mock_validate.call_args
        assert call_args.kwargs["email"] == email
        assert call_args.kwargs["name"] == name
        assert call_args.kwargs["repository"] == mock_user_repository

        # Verify repository was called with correct args: create(context, create_user)
        assert mock_user_repository.create.call_count == 1
        create_call = mock_user_repository.create.call_args
        assert len(create_call.args) == 2  # context, create_user
        assert create_call.args[1].email == email
        assert create_call.args[1].name == name

        # Verify event was published
        mock_event_publisher.publish.assert_called_once()
        published_event = mock_event_publisher.publish.call_args[0][0]
        assert published_event.aggregate_id == str(user.id)
        assert published_event.email == email
        assert published_event.name == name


@pytest.mark.asyncio
async def test_get_user(
    user_service: UserService,
    mock_user_repository: Any,
) -> None:
    """Test getting a user by ID."""
    user_id = uuid4()
    email = "get@example.com"
    name = "Get User"
    age = 30
    now = datetime.now()

    expected_user = User(
        id=user_id,
        email=email,
        name=name,
        age=age,
        created_at=now,
        updated_at=now,
    )
    mock_user_repository.get_by_id.return_value = expected_user

    retrieved_user = await user_service.get_user(user_id)

    assert retrieved_user is not None
    assert retrieved_user.id == user_id
    assert retrieved_user.email == email
    assert retrieved_user.name == name
    assert retrieved_user.age == age

    # Verify repository was called with correct args: get_by_id(context, user_id)
    assert mock_user_repository.get_by_id.call_count == 1
    get_call = mock_user_repository.get_by_id.call_args
    assert len(get_call.args) == 2  # context, user_id
    assert get_call.args[1] == user_id


@pytest.mark.asyncio
async def test_get_user_not_found(
    user_service: UserService,
    mock_user_repository: Any,
) -> None:
    """Test getting a non-existent user returns None."""
    user_id = uuid4()
    mock_user_repository.get_by_id.return_value = None

    user = await user_service.get_user(user_id)
    assert user is None

    # Verify repository was called with correct args: get_by_id(context, user_id)
    assert mock_user_repository.get_by_id.call_count == 1
    get_call = mock_user_repository.get_by_id.call_args
    assert len(get_call.args) == 2  # context, user_id
    assert get_call.args[1] == user_id


@pytest.mark.asyncio
async def test_list_users(
    user_service: UserService,
    mock_user_repository: Any,
) -> None:
    """Test listing users with pagination."""
    now = datetime.now()

    # Mock repository responses
    mock_users = [
        User(
            id=uuid4(),
            email=f"user{i}@example.com",
            name=f"User {i}",
            age=20 + i,
            created_at=now,
            updated_at=now,
        )
        for i in range(3)
    ]
    mock_user_repository.list.return_value = mock_users
    mock_user_repository.count.return_value = 5

    users, total = await user_service.list_users(limit=3, offset=0)

    assert len(users) == 3
    assert total == 5

    # Verify repository was called with correct args: list(context, limit=limit, offset=offset)
    assert mock_user_repository.list.call_count == 1
    list_call = mock_user_repository.list.call_args
    assert len(list_call.args) == 1  # context
    assert list_call.kwargs["limit"] == 3
    assert list_call.kwargs["offset"] == 0

    # Verify count was called: count(context)
    assert mock_user_repository.count.call_count == 1
    count_call = mock_user_repository.count.call_args
    assert len(count_call.args) == 1  # context


@pytest.mark.asyncio
async def test_delete_user(
    user_service: UserService,
    mock_user_repository: Any,
    mock_invoice_service: Any,
) -> None:
    """Test deleting a user."""
    user_id = uuid4()
    email = "delete@example.com"
    name = "Delete User"
    age = 35
    now = datetime.now()

    existing_user = User(
        id=user_id,
        email=email,
        name=name,
        age=age,
        created_at=now,
        updated_at=now,
    )

    with patch("app.domain.user.service.validate_delete_user_request", new_callable=AsyncMock) as mock_validate:
        mock_validate.return_value = existing_user

        # Delete the user
        await user_service.delete_user(user_id)

        # Verify validator was called (with context)
        assert mock_validate.call_count == 1
        call_args = mock_validate.call_args
        assert call_args.kwargs["user_id"] == user_id
        assert call_args.kwargs["repository"] == mock_user_repository

        # Verify repository calls (with context)
        assert mock_invoice_service._delete_invoices_by_user_id_in_transaction.call_count == 1

        # Verify delete was called with correct args: delete(context, user_id)
        assert mock_user_repository.delete.call_count == 1
        delete_call = mock_user_repository.delete.call_args
        assert len(delete_call.args) == 2  # context, user_id
        assert delete_call.args[1] == user_id


@pytest.mark.asyncio
async def test_patch_user(
    user_service: UserService,
    mock_user_repository: Any,
    mock_event_publisher: Any,
) -> None:
    """Test patching a user with sparse updates."""
    user_id = uuid4()
    email = "patch@example.com"
    name = "Patch User"
    age = 28
    now = datetime.now()

    original_user = User(
        id=user_id,
        email=email,
        name=name,
        age=age,
        created_at=now,
        updated_at=now,
    )
    updated_user = User(
        id=user_id,
        email=email,
        name="Updated Name",
        age=age,
        created_at=now,
        updated_at=now,
    )

    mock_user_repository.update_partial.return_value = updated_user

    with patch("app.domain.user.service.validate_patch_user_request", new_callable=AsyncMock) as mock_validate:
        mock_validate.return_value = original_user

        result = await user_service.patch_user(user_id, name="Updated Name")

        assert result.name == "Updated Name"
        assert result.email == email
        assert result.age == age

        # Verify validator was called (with context)
        assert mock_validate.call_count == 1
        call_args = mock_validate.call_args
        assert call_args.kwargs["user_id"] == user_id
        assert call_args.kwargs["email"] is None
        assert call_args.kwargs["name"] == "Updated Name"
        assert call_args.kwargs["repository"] == mock_user_repository

        # Verify repository was called with correct args: update_partial(context, user_id, user_update)
        assert mock_user_repository.update_partial.call_count == 1
        update_call = mock_user_repository.update_partial.call_args
        assert len(update_call.args) == 3  # context, user_id, user_update
        assert update_call.args[1] == user_id
        assert update_call.args[2].name == "Updated Name"
        mock_event_publisher.publish.assert_called_once()


@pytest.mark.asyncio
async def test_patch_user_no_changes(
    user_service: UserService,
    mock_user_repository: Any,
    mock_event_publisher: Any,
) -> None:
    """Test patching a user with no changes returns original user."""
    user_id = uuid4()
    email = "nochange@example.com"
    name = "No Change User"
    age = 30
    now = datetime.now()

    original_user = User(
        id=user_id,
        email=email,
        name=name,
        age=age,
        created_at=now,
        updated_at=now,
    )

    mock_user_repository.update_partial.side_effect = NoFieldsToUpdateError()

    with patch("app.domain.user.service.validate_patch_user_request", new_callable=AsyncMock) as mock_validate:
        mock_validate.return_value = original_user

        result = await user_service.patch_user(user_id)

        assert result == original_user

        # Verify validator was called (with context)
        assert mock_validate.call_count == 1
        call_args = mock_validate.call_args
        assert call_args.kwargs["user_id"] == user_id
        assert call_args.kwargs["email"] is None
        assert call_args.kwargs["name"] is None
        assert call_args.kwargs["repository"] == mock_user_repository

        # Verify repository was called with correct args: update_partial(context, user_id, user_update)
        assert mock_user_repository.update_partial.call_count == 1
        update_call = mock_user_repository.update_partial.call_args
        assert len(update_call.args) == 3  # context, user_id, user_update
        assert update_call.args[1] == user_id

        # No event should be published if no changes
        mock_event_publisher.publish.assert_not_called()
