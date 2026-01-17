"""User domain diff utilities."""

from app.domain.user.commands import UserUpdate
from app.domain.user.model import User


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

    # Check email changes
    if user_update.email is not None and user_update.email != original_user.email:
        changes["email"] = {"old": original_user.email, "new": user_update.email}

    # Check name changes
    if user_update.name is not None and user_update.name != original_user.name:
        changes["name"] = {"old": original_user.name, "new": user_update.name}

    # Check age changes
    if user_update.age is not None and user_update.age != original_user.age:
        changes["age"] = {
            "old": str(original_user.age) if original_user.age is not None else "None",
            "new": str(user_update.age) if user_update.age is not None else "None",
        }

    return changes
