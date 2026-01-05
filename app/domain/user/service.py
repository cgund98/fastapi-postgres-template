"""User domain service."""

from datetime import datetime

from uuid_extensions import uuid7

from app.domain.billing.invoice.service import InvoiceService
from app.domain.exceptions import NotFoundError, ValidationError
from app.domain.user.events.user_events import UserCreatedEvent, UserUpdatedEvent
from app.domain.user.model import User
from app.domain.user.repo.create import CreateUser
from app.domain.user.repo.pg import UserRepository
from app.infrastructure.db.exceptions import DuplicateError
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

    async def create_user(self, email: str, name: str) -> User:
        """Create a new user."""
        async with self._tx_manager.transaction():
            # Check if user already exists
            existing = await self._repo.get_by_email(email)
            if existing is not None:
                raise DuplicateError(entity_type="User", field="email", value=email)

            # Generate V7 UUID (timestamp-centric) and timestamps
            user_id = uuid7()
            now = datetime.now()
            create_user = CreateUser(id=user_id, email=email, name=name, created_at=now, updated_at=now)
            user = await self._repo.create(create_user)

            # Publish event (after commit)
            event = UserCreatedEvent(aggregate_id=str(user.id), email=user.email, name=user.name)
            await self._event_publisher.publish(event)

            return user

    async def get_user(self, user_id: str) -> User | None:
        """Get user by ID."""
        async with self._tx_manager.transaction():
            return await self._repo.get_by_id(user_id)

    async def update_user_name(self, user_id: str, name: str) -> User:
        """Update user name."""
        async with self._tx_manager.transaction():
            user = await self._repo.get_by_id(user_id)
            if user is None:
                raise NotFoundError(entity_type="User", identifier=user_id)

            # Validate name
            if not name or not name.strip():
                raise ValidationError("Name cannot be empty", field="name")

            old_name = user.name
            # Create updated user with new name and updated timestamp
            updated_user = User(
                id=user.id,
                email=user.email,
                name=name,
                created_at=user.created_at,
                updated_at=datetime.now(),
            )
            updated_user = await self._repo.update(updated_user)

            # Publish event (after commit)
            event = UserUpdatedEvent(
                aggregate_id=str(updated_user.id),
                changes={"name": {"old": old_name, "new": updated_user.name}},
            )
            await self._event_publisher.publish(event)

            return updated_user

    async def list_users(self, limit: int, offset: int) -> tuple[list[User], int]:
        """List users with pagination."""
        async with self._tx_manager.transaction():
            users = await self._repo.list(limit=limit, offset=offset)
            total = await self._repo.count()
            return users, total

    async def delete_user(self, user_id: str) -> None:
        """Delete a user and their associated invoices."""
        async with self._tx_manager.transaction():
            user = await self._repo.get_by_id(user_id)
            if user is None:
                raise NotFoundError(entity_type="User", identifier=user_id)

            # Delete associated invoices if invoice service is available
            # Use internal method to avoid nested transactions
            await self._invoice_service._delete_invoices_by_user_id_in_transaction(user.id)

            # Delete the user
            await self._repo.delete(user_id)
