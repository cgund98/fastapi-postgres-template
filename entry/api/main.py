"""FastAPI server entrypoint."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.config.settings import get_settings
from app.domain.exceptions import BusinessRuleError, DomainError, ValidationError
from app.infrastructure.db.exceptions import DatabaseError, DuplicateError, NotFoundError, RepositoryError
from app.infrastructure.sql.sqlalchemy_pool import SQLAlchemyPool
from app.infrastructure.sql.transaction import SQLTransactionManager
from app.observability.logging import get_logger, setup_logging
from app.presentation.billing import routes as billing_routes
from app.presentation.container import AppContainer, get_container
from app.presentation.exceptions import handle_domain_exceptions
from app.presentation.user import routes as user_routes

logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    setup_logging(settings)
    logger.info("Starting API server", environment=settings.environment)

    # Initialize application container with lifecycle dependencies
    db_pool = SQLAlchemyPool(settings)
    transaction_manager = SQLTransactionManager(db_pool)
    container = AppContainer(db_pool=db_pool, transaction_manager=transaction_manager)

    # Attach container to app state
    app.state.container = container
    logger.info("Application container initialized")

    yield

    # Shutdown
    logger.info("Shutting down API server")
    await db_pool.close()
    logger.info("Application container closed")


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
async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint that tests database connectivity."""
    from sqlalchemy import text

    try:
        # Get the database pool from the container
        container = get_container(request.app)
        db_pool = container.db_pool

        # Test database connection with a simple query
        async with db_pool.get_session() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar()

        return JSONResponse(
            content={"status": "healthy"},
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        logger.error("Health check failed", error=str(e), exc_info=True)
        return JSONResponse(
            content={"status": "unhealthy"},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "entry.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development",
    )
