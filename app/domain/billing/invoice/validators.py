"""Invoice domain validators."""

from uuid import UUID

from app.domain.exceptions import NotFoundError
from app.domain.user.repo.base import UserRepository


async def validate_create_invoice_request[TContext](
    *, user_id: UUID, user_repository: UserRepository[TContext], context: TContext
) -> None:
    """
    Validate invoice creation request.

    Args:
        user_id: The user ID to validate
        user_repository: User repository to check if user exists
        context: Database context

    Raises:
        NotFoundError: If user does not exist
    """
    user = await user_repository.get_by_id(context, user_id)
    if user is None:
        raise NotFoundError(entity_type="User", identifier=str(user_id))
