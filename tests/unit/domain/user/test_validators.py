"""Tests for User validators."""

from datetime import datetime
from typing import Any
from uuid import uuid4

import pytest

from app.domain.exceptions import NotFoundError, ValidationError
from app.domain.types import UNSET
from app.domain.user.model import User
from app.domain.user.validators import (
    validate_create_user_request,
    validate_delete_user_request,
    validate_patch_user_request,
)
from app.infrastructure.db.exceptions import DuplicateError


@pytest.mark.asyncio
async def test_validate_create_user_request_success(
    mock_user_repository: Any,
) -> None:
    """Test validating a valid user creation request."""
    email = "test@example.com"
    name = "Test User"

    # Mock no existing user
    mock_user_repository.get_by_email.return_value = None

    # Should not raise
    await validate_create_user_request(email, name, mock_user_repository)

    mock_user_repository.get_by_email.assert_called_once_with(email)


@pytest.mark.asyncio
async def test_validate_create_user_request_duplicate_email(
    mock_user_repository: Any,
) -> None:
    """Test validating user creation with duplicate email raises error."""
    email = "duplicate@example.com"
    name = "Test User"
    now = datetime.now()

    existing_user = User(
        id=uuid4(),
        email=email,
        name="Existing User",
        age=None,
        created_at=now,
        updated_at=now,
    )
    mock_user_repository.get_by_email.return_value = existing_user

    with pytest.raises(DuplicateError) as exc_info:
        await validate_create_user_request(email, name, mock_user_repository)

    assert exc_info.value.entity_type == "User"
    assert exc_info.value.field == "email"
    assert exc_info.value.value == email
    mock_user_repository.get_by_email.assert_called_once_with(email)


@pytest.mark.asyncio
async def test_validate_create_user_request_empty_name(
    mock_user_repository: Any,
) -> None:
    """Test validating user creation with empty name raises error."""
    email = "test@example.com"
    name = ""

    mock_user_repository.get_by_email.return_value = None

    with pytest.raises(ValidationError) as exc_info:
        await validate_create_user_request(email, name, mock_user_repository)

    assert exc_info.value.field == "name"


@pytest.mark.asyncio
async def test_validate_create_user_request_whitespace_name(
    mock_user_repository: Any,
) -> None:
    """Test validating user creation with whitespace-only name raises error."""
    email = "test@example.com"
    name = "   "

    mock_user_repository.get_by_email.return_value = None

    with pytest.raises(ValidationError) as exc_info:
        await validate_create_user_request(email, name, mock_user_repository)

    assert exc_info.value.field == "name"


@pytest.mark.asyncio
async def test_validate_patch_user_request_success(
    mock_user_repository: Any,
) -> None:
    """Test validating a valid user patch request."""
    user_id = uuid4()
    email = "test@example.com"
    name = "Test User"
    now = datetime.now()

    existing_user = User(
        id=user_id,
        email=email,
        name=name,
        age=None,
        created_at=now,
        updated_at=now,
    )

    mock_user_repository.get_by_id.return_value = existing_user

    # Should return the user
    result = await validate_patch_user_request(user_id, UNSET, UNSET, mock_user_repository)

    assert result == existing_user
    mock_user_repository.get_by_id.assert_called_once_with(user_id)


@pytest.mark.asyncio
async def test_validate_patch_user_request_user_not_found(
    mock_user_repository: Any,
) -> None:
    """Test validating patch request for non-existent user raises error."""
    user_id = uuid4()

    mock_user_repository.get_by_id.return_value = None

    with pytest.raises(NotFoundError) as exc_info:
        await validate_patch_user_request(user_id, UNSET, UNSET, mock_user_repository)

    assert exc_info.value.entity_type == "User"
    assert exc_info.value.identifier == str(user_id)
    mock_user_repository.get_by_id.assert_called_once_with(user_id)


@pytest.mark.asyncio
async def test_validate_patch_user_request_empty_name(
    mock_user_repository: Any,
) -> None:
    """Test validating patch request with empty name raises error."""
    user_id = uuid4()
    email = "test@example.com"
    name = "Test User"
    now = datetime.now()

    existing_user = User(
        id=user_id,
        email=email,
        name=name,
        age=None,
        created_at=now,
        updated_at=now,
    )

    mock_user_repository.get_by_id.return_value = existing_user

    with pytest.raises(ValidationError) as exc_info:
        await validate_patch_user_request(user_id, UNSET, "", mock_user_repository)

    assert exc_info.value.field == "name"


@pytest.mark.asyncio
async def test_validate_patch_user_request_duplicate_email(
    mock_user_repository: Any,
) -> None:
    """Test validating patch request with duplicate email raises error."""
    user_id = uuid4()
    email = "original@example.com"
    duplicate_email = "duplicate@example.com"
    name = "Test User"
    now = datetime.now()

    original_user = User(
        id=user_id,
        email=email,
        name=name,
        age=None,
        created_at=now,
        updated_at=now,
    )
    existing_user = User(
        id=uuid4(),
        email=duplicate_email,
        name="Other User",
        age=None,
        created_at=now,
        updated_at=now,
    )

    mock_user_repository.get_by_id.return_value = original_user
    mock_user_repository.get_by_email.return_value = existing_user

    with pytest.raises(DuplicateError) as exc_info:
        await validate_patch_user_request(user_id, duplicate_email, UNSET, mock_user_repository)

    assert exc_info.value.entity_type == "User"
    assert exc_info.value.field == "email"
    assert exc_info.value.value == duplicate_email


@pytest.mark.asyncio
async def test_validate_patch_user_request_same_email_no_error(
    mock_user_repository: Any,
) -> None:
    """Test validating patch request with same email does not raise error."""
    user_id = uuid4()
    email = "test@example.com"
    name = "Test User"
    now = datetime.now()

    existing_user = User(
        id=user_id,
        email=email,
        name=name,
        age=None,
        created_at=now,
        updated_at=now,
    )

    mock_user_repository.get_by_id.return_value = existing_user

    # Should not raise even though email matches existing user (it's the same user)
    result = await validate_patch_user_request(user_id, email, UNSET, mock_user_repository)

    assert result == existing_user
    mock_user_repository.get_by_id.assert_called_once_with(user_id)
    # Should not check for duplicate since email hasn't changed
    mock_user_repository.get_by_email.assert_not_called()


@pytest.mark.asyncio
async def test_validate_delete_user_request_success(
    mock_user_repository: Any,
) -> None:
    """Test validating a valid user deletion request."""
    user_id = uuid4()
    now = datetime.now()

    existing_user = User(
        id=user_id,
        email="test@example.com",
        name="Test User",
        age=None,
        created_at=now,
        updated_at=now,
    )

    mock_user_repository.get_by_id.return_value = existing_user

    # Should return the user
    result = await validate_delete_user_request(user_id, mock_user_repository)

    assert result == existing_user
    mock_user_repository.get_by_id.assert_called_once_with(user_id)


@pytest.mark.asyncio
async def test_validate_delete_user_request_user_not_found(
    mock_user_repository: Any,
) -> None:
    """Test validating delete request for non-existent user raises error."""
    user_id = uuid4()

    mock_user_repository.get_by_id.return_value = None

    with pytest.raises(NotFoundError) as exc_info:
        await validate_delete_user_request(user_id, mock_user_repository)

    assert exc_info.value.entity_type == "User"
    assert exc_info.value.identifier == str(user_id)
    mock_user_repository.get_by_id.assert_called_once_with(user_id)
