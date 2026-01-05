"""FastAPI server entrypoint."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config.settings import get_settings
from app.domain.exceptions import BusinessRuleError, DomainError, ValidationError
from app.infrastructure.db.exceptions import DatabaseError, DuplicateError, NotFoundError, RepositoryError
from app.infrastructure.sql.sqlalchemy_pool import SQLAlchemyPool
from app.observability.logging import get_logger, setup_logging
from app.presentation.billing import routes as billing_routes
from app.presentation.exceptions import handle_domain_exceptions
from app.presentation.user import routes as user_routes

logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # noqa: ARG001
    """Application lifespan manager."""
    # Startup
    setup_logging(settings)
    logger.info("Starting API server", environment=settings.environment)

    # Initialize SQLAlchemy database engine
    SQLAlchemyPool.create_engine(settings)
    logger.info("Database engine initialized")

    yield

    # Shutdown
    logger.info("Shutting down API server")
    await SQLAlchemyPool.close_engine()
    logger.info("Database engine closed")


app = FastAPI(
    title="FastAPI PostgreSQL Template",
    description="A template demonstrating 3-tier architecture with FastAPI and PostgreSQL",
    version="0.1.0",
    lifespan=lifespan,
)

# Register exception handlers
app.add_exception_handler(ValidationError, handle_domain_exceptions)
app.add_exception_handler(BusinessRuleError, handle_domain_exceptions)
app.add_exception_handler(DomainError, handle_domain_exceptions)
app.add_exception_handler(NotFoundError, handle_domain_exceptions)
app.add_exception_handler(DuplicateError, handle_domain_exceptions)
app.add_exception_handler(DatabaseError, handle_domain_exceptions)
app.add_exception_handler(RepositoryError, handle_domain_exceptions)

# Include routers
app.include_router(user_routes.router)
app.include_router(billing_routes.router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "entry.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development",
    )
