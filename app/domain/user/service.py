"""User domain service."""

from datetime import datetime
from uuid import UUID

from uuid_extensions import uuid7

from app.domain.billing.invoice.service import InvoiceService
from app.domain.exceptions import NotFoundError
from app.domain.types import UNSET, OptionalOrUnset, RequiredOrUnset
from app.domain.user.diff import generate_user_changes
from app.domain.user.events.user_events import UserCreatedEvent, UserUpdatedEvent
from app.domain.user.model import CreateUser, User, UserUpdate
from app.domain.user.repo.sql import UserRepository
from app.domain.user.validators import validate_email_not_duplicate, validate_name
from app.infrastructure.db.exceptions import DuplicateError, NoFieldsToUpdateError
from app.infrastructure.db.transaction import TransactionManager
from app.infrastructure.messaging.publisher import EventPublisher


class UserService:
    """User domain service."""

    def __init__(
        self,
        repository: UserRepository,
        transaction_manager: TransactionManager,
        event_publisher: EventPublisher,
        invoice_service: InvoiceService,
    ) -> None:
        """Initialize user service."""
        self._repo = repository
        self._tx_manager = transaction_manager
        self._event_publisher = event_publisher
        self._invoice_service = invoice_service

    async def create_user(self, email: str, name: str, age: int | None = None) -> User:
        """Create a new user."""
        async with self._tx_manager.transaction():
            # Check if user already exists
            existing = await self._repo.get_by_email(email)
            if existing is not None:
                raise DuplicateError(entity_type="User", field="email", value=email)

            # Generate V7 UUID (timestamp-centric) and timestamps
            user_id = uuid7()
            now = datetime.now()
            create_user = CreateUser(id=user_id, email=email, name=name, age=age, created_at=now, updated_at=now)
            user = await self._repo.create(create_user)

            # Publish event (after commit)
            event = UserCreatedEvent(aggregate_id=str(user.id), email=user.email, name=user.name)
            await self._event_publisher.publish(event)

            return user

    async def get_user(self, user_id: UUID) -> User | None:
        """Get user by ID."""
        async with self._tx_manager.transaction():
            return await self._repo.get_by_id(user_id)

    async def patch_user(
        self,
        user_id: UUID,
        email: RequiredOrUnset[str] = UNSET,
        name: RequiredOrUnset[str] = UNSET,
        age: OptionalOrUnset[int] = UNSET,
    ) -> User:
        """Patch a user with sparse updates."""
        async with self._tx_manager.transaction():
            user = await self._repo.get_by_id(user_id)
            if user is None:
                raise NotFoundError(entity_type="User", identifier=str(user_id))

            # Build UserUpdate from provided fields
            user_update = UserUpdate(
                email=email,
                name=name,
                age=age,
            )

            # Validate name if provided (name is RequiredOrUnset, so can't be None)
            validate_name(name)

            # Check for duplicate email if email is being updated (email is RequiredOrUnset, so can't be None)
            await validate_email_not_duplicate(email, user.email, self._repo)

            # Generate changes dictionary for event
            changes = generate_user_changes(user_update, user)

            # Perform partial update
            try:
                updated_user = await self._repo.update_partial(user_id, user_update)
            except NoFieldsToUpdateError:
                return user

            # Publish event if there were changes
            if changes:
                event = UserUpdatedEvent(aggregate_id=str(updated_user.id), changes=changes)
                await self._event_publisher.publish(event)

            return updated_user

    async def list_users(self, limit: int, offset: int) -> tuple[list[User], int]:
        """List users with pagination."""
        async with self._tx_manager.transaction():
            users = await self._repo.list(limit=limit, offset=offset)
            total = await self._repo.count()
            return users, total

    async def delete_user(self, user_id: UUID) -> None:
        """Delete a user and their associated invoices."""
        async with self._tx_manager.transaction():
            user = await self._repo.get_by_id(user_id)
            if user is None:
                raise NotFoundError(entity_type="User", identifier=str(user_id))

            # Delete associated invoices if invoice service is available
            # Use internal method to avoid nested transactions
            await self._invoice_service._delete_invoices_by_user_id_in_transaction(user.id)

            # Delete the user
            await self._repo.delete(user_id)
