"""Tests for Invoice validators."""

from datetime import datetime
from typing import Any
from uuid import uuid4

import pytest

from app.domain.billing.invoice.validators import validate_create_invoice_request
from app.domain.exceptions import NotFoundError
from app.domain.user.model import User


@pytest.mark.asyncio
async def test_validate_create_invoice_request_success(
    mock_user_repository: Any,
) -> None:
    """Test validating a valid invoice creation request."""
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

    # Should not raise
    await validate_create_invoice_request(user_id, mock_user_repository)

    mock_user_repository.get_by_id.assert_called_once_with(user_id)


@pytest.mark.asyncio
async def test_validate_create_invoice_request_user_not_found(
    mock_user_repository: Any,
) -> None:
    """Test validating invoice creation with non-existent user raises error."""
    user_id = uuid4()

    mock_user_repository.get_by_id.return_value = None

    with pytest.raises(NotFoundError) as exc_info:
        await validate_create_invoice_request(user_id, mock_user_repository)

    assert exc_info.value.entity_type == "User"
    assert exc_info.value.identifier == str(user_id)
    mock_user_repository.get_by_id.assert_called_once_with(user_id)
