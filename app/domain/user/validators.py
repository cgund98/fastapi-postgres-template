"""User domain validators."""

from typing import TYPE_CHECKING
from uuid import UUID

from app.domain.exceptions import NotFoundError, ValidationError
from app.domain.types import RequiredOrUnset, Unset
from app.domain.user.repo.base import UserRepository

if TYPE_CHECKING:
    from app.domain.user.model import User


def validate_name(name: RequiredOrUnset[str]) -> None:
    """
    Validate user name.

    Args:
        name: The name to validate (must be str if not UNSET)

    Raises:
        ValidationError: If name is empty or whitespace-only
    """
    if isinstance(name, Unset):
        return

    if not name or not name.strip():
        raise ValidationError("Name cannot be empty", field="name")


async def validate_email_not_duplicate(
    email: RequiredOrUnset[str],
    current_email: str,
    repository: UserRepository,
) -> None:
    """
    Validate that email is not a duplicate.

    Args:
        email: The email to validate (must be str if not UNSET)
        current_email: The current email of the user being updated
        repository: User repository to check for duplicates

    Raises:
        DuplicateError: If email already exists for another user
    """
    from app.infrastructure.db.exceptions import DuplicateError

    if isinstance(email, Unset):
        return

    if email != current_email:
        existing = await repository.get_by_email(email)
        if existing is not None:
            raise DuplicateError(entity_type="User", field="email", value=email)


async def validate_create_user_request(email: str, name: str, repository: UserRepository) -> None:
    """
    Validate user creation request.

    Args:
        email: The email to validate
        name: The name to validate
        repository: User repository to check for duplicates

    Raises:
        DuplicateError: If email already exists
        ValidationError: If name is empty or whitespace-only
    """
    from app.infrastructure.db.exceptions import DuplicateError

    # Validate name
    if not name or not name.strip():
        raise ValidationError("Name cannot be empty", field="name")

    # Check if user already exists
    existing = await repository.get_by_email(email)
    if existing is not None:
        raise DuplicateError(entity_type="User", field="email", value=email)


async def validate_patch_user_request(
    user_id: UUID,
    email: RequiredOrUnset[str],
    name: RequiredOrUnset[str],
    repository: UserRepository,
) -> "User":
    """
    Validate user patch request.

    Args:
        user_id: The user ID to validate exists
        email: The email to validate (if provided)
        name: The name to validate (if provided)
        repository: User repository for validation checks

    Returns:
        The user if validation passes

    Raises:
        NotFoundError: If user does not exist
        ValidationError: If name is empty or whitespace-only
        DuplicateError: If email already exists for another user
    """
    # Validate user exists
    user = await repository.get_by_id(user_id)
    if user is None:
        raise NotFoundError(entity_type="User", identifier=str(user_id))

    # Validate name if provided
    validate_name(name)

    # Validate email if provided
    await validate_email_not_duplicate(email, user.email, repository)

    return user


async def validate_delete_user_request(user_id: UUID, repository: UserRepository) -> "User":
    """
    Validate user deletion request.

    Args:
        user_id: The user ID to validate exists
        repository: User repository to check if user exists

    Returns:
        The user if validation passes

    Raises:
        NotFoundError: If user does not exist
    """
    user = await repository.get_by_id(user_id)
    if user is None:
        raise NotFoundError(entity_type="User", identifier=str(user_id))

    return user
