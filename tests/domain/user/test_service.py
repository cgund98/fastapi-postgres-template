"""Tests for UserService."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import pytest

from app.domain.exceptions import NotFoundError, ValidationError
from app.domain.user.model import User
from app.domain.user.service import UserService
from app.infrastructure.db.exceptions import DuplicateError


@pytest.mark.asyncio
async def test_create_user(
    user_service: UserService,
    mock_user_repository: Any,
    mock_event_publisher: Any,
) -> None:
    """Test creating a user."""
    email = "test@example.com"
    name = "Test User"
    user_id = uuid4()
    now = datetime.now()

    # Mock repository responses
    created_user = User(
        id=user_id,
        email=email,
        name=name,
        created_at=now,
        updated_at=now,
    )
    mock_user_repository.get_by_email.return_value = None  # No existing user
    mock_user_repository.create.return_value = created_user

    user = await user_service.create_user(email=email, name=name)

    assert user.email == email
    assert user.name == name
    assert isinstance(user.id, UUID)
    assert user.created_at is not None
    assert user.updated_at is not None

    # Verify repository was called
    mock_user_repository.get_by_email.assert_called_once_with(email)
    mock_user_repository.create.assert_called_once()
    # Verify event was published
    mock_event_publisher.publish.assert_called_once()
    published_event = mock_event_publisher.publish.call_args[0][0]
    assert published_event.aggregate_id == str(user.id)
    assert published_event.email == email
    assert published_event.name == name


@pytest.mark.asyncio
async def test_create_user_duplicate_email(
    user_service: UserService,
    mock_user_repository: Any,
) -> None:
    """Test creating a user with duplicate email raises error."""
    email = "duplicate@example.com"
    name = "Test User"
    user_id = uuid4()
    now = datetime.now()

    # Mock existing user
    existing_user = User(
        id=user_id,
        email=email,
        name=name,
        created_at=now,
        updated_at=now,
    )
    mock_user_repository.get_by_email.return_value = existing_user

    # Try to create another user with the same email
    with pytest.raises(DuplicateError) as exc_info:
        await user_service.create_user(email=email, name="Another User")

    assert exc_info.value.entity_type == "User"
    assert exc_info.value.field == "email"
    assert exc_info.value.value == email
    mock_user_repository.get_by_email.assert_called_once_with(email)


@pytest.mark.asyncio
async def test_get_user(
    user_service: UserService,
    mock_user_repository: Any,
) -> None:
    """Test getting a user by ID."""
    user_id = uuid4()
    email = "get@example.com"
    name = "Get User"
    now = datetime.now()

    expected_user = User(
        id=user_id,
        email=email,
        name=name,
        created_at=now,
        updated_at=now,
    )
    mock_user_repository.get_by_id.return_value = expected_user

    retrieved_user = await user_service.get_user(str(user_id))

    assert retrieved_user is not None
    assert retrieved_user.id == user_id
    assert retrieved_user.email == email
    assert retrieved_user.name == name
    mock_user_repository.get_by_id.assert_called_once_with(str(user_id))


@pytest.mark.asyncio
async def test_get_user_not_found(
    user_service: UserService,
    mock_user_repository: Any,
) -> None:
    """Test getting a non-existent user returns None."""
    user_id = "00000000-0000-0000-0000-000000000000"
    mock_user_repository.get_by_id.return_value = None

    user = await user_service.get_user(user_id)
    assert user is None
    mock_user_repository.get_by_id.assert_called_once_with(user_id)


@pytest.mark.asyncio
async def test_update_user_name(
    user_service: UserService,
    mock_user_repository: Any,
    mock_event_publisher: Any,
) -> None:
    """Test updating a user's name."""
    user_id = uuid4()
    email = "update@example.com"
    old_name = "Original Name"
    new_name = "Updated Name"
    now = datetime.now()

    # Mock existing user
    existing_user = User(
        id=user_id,
        email=email,
        name=old_name,
        created_at=now,
        updated_at=now,
    )
    # Mock updated user
    updated_user = User(
        id=user_id,
        email=email,
        name=new_name,
        created_at=now,
        updated_at=now,
    )
    mock_user_repository.get_by_id.return_value = existing_user
    mock_user_repository.update.return_value = updated_user

    result = await user_service.update_user_name(str(user_id), new_name)

    assert result.name == new_name
    assert result.email == email
    assert result.id == user_id

    # Verify repository calls
    mock_user_repository.get_by_id.assert_called_once_with(str(user_id))
    mock_user_repository.update.assert_called_once()
    # Verify event was published
    mock_event_publisher.publish.assert_called()
    published_event = mock_event_publisher.publish.call_args[0][0]
    assert published_event.aggregate_id == str(user_id)
    assert "name" in published_event.changes


@pytest.mark.asyncio
async def test_update_user_name_not_found(
    user_service: UserService,
    mock_user_repository: Any,
) -> None:
    """Test updating a non-existent user raises error."""
    user_id = "00000000-0000-0000-0000-000000000000"
    mock_user_repository.get_by_id.return_value = None

    with pytest.raises(NotFoundError) as exc_info:
        await user_service.update_user_name(user_id, "New Name")

    assert exc_info.value.entity_type == "User"
    mock_user_repository.get_by_id.assert_called_once_with(user_id)


@pytest.mark.asyncio
async def test_update_user_name_empty(
    user_service: UserService,
    mock_user_repository: Any,
) -> None:
    """Test updating user name with empty string raises error."""
    user_id = uuid4()
    email = "empty@example.com"
    name = "Test User"
    now = datetime.now()

    existing_user = User(
        id=user_id,
        email=email,
        name=name,
        created_at=now,
        updated_at=now,
    )
    mock_user_repository.get_by_id.return_value = existing_user

    with pytest.raises(ValidationError) as exc_info:
        await user_service.update_user_name(str(user_id), "")

    assert exc_info.value.field == "name"
    mock_user_repository.get_by_id.assert_called_once_with(str(user_id))


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
    mock_user_repository.list.assert_called_once_with(limit=3, offset=0)
    mock_user_repository.count.assert_called_once()


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
    now = datetime.now()

    existing_user = User(
        id=user_id,
        email=email,
        name=name,
        created_at=now,
        updated_at=now,
    )
    mock_user_repository.get_by_id.return_value = existing_user

    # Delete the user
    await user_service.delete_user(str(user_id))

    # Verify repository calls
    mock_user_repository.get_by_id.assert_called_once_with(str(user_id))
    mock_invoice_service._delete_invoices_by_user_id_in_transaction.assert_called_once_with(user_id)
    mock_user_repository.delete.assert_called_once_with(str(user_id))


@pytest.mark.asyncio
async def test_delete_user_not_found(
    user_service: UserService,
    mock_user_repository: Any,
) -> None:
    """Test deleting a non-existent user raises error."""
    user_id = "00000000-0000-0000-0000-000000000000"
    mock_user_repository.get_by_id.return_value = None

    with pytest.raises(NotFoundError) as exc_info:
        await user_service.delete_user(user_id)

    assert exc_info.value.entity_type == "User"
    mock_user_repository.get_by_id.assert_called_once_with(user_id)
