"""User domain diff utilities."""

from app.domain.types import UNSET
from app.domain.user.model import User, UserUpdate


def generate_user_changes(user_update: UserUpdate, original_user: User) -> dict[str, dict[str, str]]:
    """
    Generate a dictionary of changes between UserUpdate and original User.

    Args:
        user_update: The update object with sparse fields
        original_user: The original user object

    Returns:
        Dictionary mapping field names to old/new value pairs
        Format: {"field_name": {"old": "old_value", "new": "new_value"}}
    """
    changes: dict[str, dict[str, str]] = {}

    # Check email changes (RequiredOrUnset[str])
    if user_update.email is not UNSET:
        email_str: str = user_update.email  # type: ignore[assignment]
        if email_str != original_user.email:
            changes["email"] = {"old": original_user.email, "new": email_str}

    # Check name changes (RequiredOrUnset[str])
    if user_update.name is not UNSET:
        name_str: str = user_update.name  # type: ignore[assignment]
        if name_str != original_user.name:
            changes["name"] = {"old": original_user.name, "new": name_str}

    # Check age changes (OptionalOrUnset[int])
    if user_update.age is not UNSET:
        age_value: int | None = user_update.age  # type: ignore[assignment]
        if age_value != original_user.age:
            changes["age"] = {
                "old": str(original_user.age) if original_user.age is not None else "None",
                "new": str(age_value) if age_value is not None else "None",
            }

    return changes
