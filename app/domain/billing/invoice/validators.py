"""Invoice domain validators."""

from uuid import UUID

from app.domain.exceptions import NotFoundError
from app.domain.user.repo.base import UserRepository


async def validate_create_invoice_request(user_id: UUID, user_repository: UserRepository) -> None:
    """
    Validate invoice creation request.

    Args:
        user_id: The user ID to validate
        user_repository: User repository to check if user exists

    Raises:
        NotFoundError: If user does not exist
    """
    user = await user_repository.get_by_id(user_id)
    if user is None:
        raise NotFoundError(entity_type="User", identifier=str(user_id))
