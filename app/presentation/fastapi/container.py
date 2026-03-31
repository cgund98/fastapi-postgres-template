"""Utility to access application container from FastAPI app."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from fastapi import Request

from app.adapters.sql.pool import AsyncpgPool
from app.adapters.sql.transaction import SQLTransactionManager
from app.domain.events.publisher import EventPublisher

if TYPE_CHECKING:
    pass


@dataclass
class AppContainer:
    """Container for application-scoped dependencies with lifecycle."""

    db_pool: AsyncpgPool
    transaction_manager: SQLTransactionManager
    event_publisher: EventPublisher


def get_container(request: Request) -> AppContainer:
    """Get the application container from the FastAPI app."""
    container = getattr(request.app.state, "container", None)

    if container is None or not isinstance(container, AppContainer):
        raise RuntimeError("Application container not initialized. Check lifespan setup.")

    return cast(AppContainer, container)
