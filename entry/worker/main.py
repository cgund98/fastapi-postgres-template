"""Async event consumer worker entrypoint."""

import asyncio
from typing import TYPE_CHECKING

import boto3

from app.adapters.aws.client import get_boto3_client_kwargs
from app.adapters.events.consumer.sqs import SQSConsumer, SQSConsumerConfig
from app.adapters.events.publisher.sns import SNSPublisher
from app.adapters.sql.pool import AsyncpgPool
from app.adapters.sql.transaction import SQLTransactionManager
from app.config.settings import get_settings
from app.domain.billing.invoice.handlers.invoice_events import InvoiceCreatedEventHandler, InvoicePaidEventHandler
from app.domain.billing.invoice.handlers.payment_requested import InvoicePaymentRequestedHandler
from app.domain.events.publisher import EventPublisher
from app.domain.events.registry.billing.v1.invoice import (
    InvoiceCreatedEvent,
    InvoicePaidEvent,
    InvoicePaymentRequestedEvent,
)
from app.domain.events.registry.user.v1.events import UserCreatedEvent, UserUpdatedEvent
from app.domain.events.router import EventRouter
from app.domain.user.handlers import UserCreatedEventHandler, UserUpdatedEventHandler
from app.observability.logging import get_logger, setup_logging

if TYPE_CHECKING:
    from types_boto3_sqs.client import SQSClient

logger = get_logger(__name__)
settings = get_settings()


def create_event_router(event_publisher: EventPublisher, transaction_manager: SQLTransactionManager) -> EventRouter:
    """Create event handlers with their dependencies."""
    router = EventRouter()
    router.register(UserCreatedEvent, UserCreatedEventHandler())
    router.register(UserUpdatedEvent, UserUpdatedEventHandler())
    router.register(InvoiceCreatedEvent, InvoiceCreatedEventHandler())
    router.register(InvoicePaymentRequestedEvent, InvoicePaymentRequestedHandler(event_publisher, transaction_manager))
    router.register(InvoicePaidEvent, InvoicePaidEventHandler())
    return router


async def consume_queue(queue_url: str, router: EventRouter, sqs_client: "SQSClient") -> None:
    """Consume events from a specific queue for a specific event type."""

    consumer_config = SQSConsumerConfig(
        queue_url=queue_url,
        max_messages=1,
        wait_time_seconds=5,
    )
    consumer = SQSConsumer(sqs_client, consumer_config)
    try:
        await consumer.consume(router)
    except KeyboardInterrupt:
        logger.info("Received shutdown signal for consumer", queue_url=queue_url)
        raise
    except Exception as e:
        logger.error("Fatal error in consumer", queue_url=queue_url, error=str(e), exc_info=True)
        raise


async def main() -> None:
    """Main worker function."""
    setup_logging(settings)
    logger.info("Starting event consumer worker", environment=settings.environment)

    # Initialize application container with lifecycle dependencies
    db_pool = AsyncpgPool(settings)
    await db_pool.connect()
    transaction_manager = SQLTransactionManager(db_pool)
    logger.info("Application container initialized")

    # Initialize publisher
    boto3_args = get_boto3_client_kwargs(settings)
    sns_client = boto3.client("sns", **boto3_args)
    event_publisher = SNSPublisher(sns_client, topic_arn=settings.event_topic_arn)

    # Create event router with dependencies
    router = create_event_router(event_publisher, transaction_manager)

    # Initialize SQS client
    sqs_client = boto3.client("sqs", **boto3_args)

    # Create event router with dependencies
    router = create_event_router(event_publisher, transaction_manager)

    logger.info("Starting consumer for queue", queue_url=settings.event_queue_url)

    # Create tasks for each event type queue
    task = asyncio.create_task(consume_queue(settings.event_queue_url, router, sqs_client))

    try:
        await task
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        task.cancel()
        await task
    finally:
        await db_pool.close()
        logger.info("Database pool closed")


if __name__ == "__main__":
    asyncio.run(main())
