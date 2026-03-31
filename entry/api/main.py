"""FastAPI server entrypoint."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

import boto3
from fastapi import Depends, FastAPI, status
from fastapi.responses import JSONResponse

from app.adapters.aws.client import get_boto3_client_kwargs
from app.adapters.events.publisher.sns import SNSPublisher
from app.adapters.sql.pool import AsyncpgPool
from app.adapters.sql.transaction import SQLTransactionManager
from app.config.settings import get_settings
from app.observability.logging import get_logger, setup_logging
from app.presentation.fastapi.billing import routes as billing_routes
from app.presentation.fastapi.container import AppContainer, get_container
from app.presentation.fastapi.exceptions import register_exception_handlers
from app.presentation.fastapi.user import routes as user_routes

logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    setup_logging(settings)
    logger.info("Starting API server", environment=settings.environment)

    # Initialize application container with lifecycle dependencies
    db_pool = AsyncpgPool(settings)
    await db_pool.connect()
    transaction_manager = SQLTransactionManager(db_pool)

    boto3_args = get_boto3_client_kwargs(settings)
    sns_client = boto3.client("sns", **boto3_args)
    event_publisher = SNSPublisher(sns_client, topic_arn=settings.event_topic_arn)

    container = AppContainer(db_pool=db_pool, transaction_manager=transaction_manager, event_publisher=event_publisher)

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
register_exception_handlers(app)

# Include routers
app.include_router(user_routes.router)
app.include_router(billing_routes.router)


@app.get("/health")
async def health_check(container: Annotated[AppContainer, Depends(get_container)]) -> JSONResponse:
    """Health check endpoint that tests database connectivity."""
    try:
        db_pool = container.db_pool

        async with db_pool.get_connection() as conn:
            await conn.fetchval("SELECT 1")

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
