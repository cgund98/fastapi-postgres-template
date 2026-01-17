"""Utility to access application container from FastAPI app."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from fastapi import FastAPI

from app.infrastructure.sql.sqlalchemy_pool import SQLAlchemyPool
from app.infrastructure.sql.transaction import SQLTransactionManager

if TYPE_CHECKING:
    from fastapi import Request


@dataclass
class AppContainer:
    """Container for application-scoped dependencies with lifecycle."""

    db_pool: SQLAlchemyPool
    transaction_manager: SQLTransactionManager


def get_container(app: FastAPI) -> AppContainer:
    """Get the application container from the FastAPI app."""
    container = getattr(app.state, "container", None)
    if container is None or not isinstance(container, AppContainer):
        raise RuntimeError("Application container not initialized. Check lifespan setup.")
    return cast(AppContainer, container)


def get_container_from_request(request: "Request") -> AppContainer:
    """Get the application container from a FastAPI request."""
    return get_container(request.app)
