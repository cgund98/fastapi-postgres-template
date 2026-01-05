"""User domain validators."""

from app.domain.exceptions import ValidationError
from app.domain.types import RequiredOrUnset, Unset
from app.domain.user.repo.sql import UserRepository


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
