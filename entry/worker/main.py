"""Async event consumer worker entrypoint."""

import asyncio
from typing import Any, cast

from app.config.settings import get_settings
from app.domain.billing.invoice.consumers.invoice_events import (
    InvoiceCreatedEventHandler,
    InvoicePaidEventHandler,
)
from app.domain.billing.invoice.consumers.payment_requested import (
    InvoicePaymentRequestedHandler,
)
from app.domain.billing.invoice.events.constants import InvoiceEventType
from app.domain.billing.invoice.events.invoice_events import (
    InvoiceCreatedEvent,
    InvoicePaidEvent,
    InvoicePaymentRequestedEvent,
)
from app.domain.user.consumers.user_events import (
    UserCreatedEventHandler,
    UserUpdatedEventHandler,
)
from app.domain.user.events.constants import UserEventType
from app.domain.user.events.user_events import UserCreatedEvent, UserUpdatedEvent
from app.infrastructure.messaging.base import BaseEvent
from app.infrastructure.messaging.consumer import SQSConsumer, SQSConsumerConfig
from app.infrastructure.messaging.handler import EventHandler
from app.infrastructure.messaging.publisher import EventPublisher, SNSPublisher
from app.infrastructure.postgres.pool import PostgresPool
from app.observability.logging import get_logger, setup_logging

logger = get_logger(__name__)
settings = get_settings()

# Event type to event class mapping
EVENT_CLASSES: dict[str, type[BaseEvent]] = {
    UserEventType.CREATED: UserCreatedEvent,
    UserEventType.UPDATED: UserUpdatedEvent,
    InvoiceEventType.CREATED: InvoiceCreatedEvent,
    InvoiceEventType.PAYMENT_REQUESTED: InvoicePaymentRequestedEvent,
    InvoiceEventType.PAID: InvoicePaidEvent,
}


def create_event_handlers(event_publisher: EventPublisher) -> dict[str, EventHandler]:
    """Create event handlers with their dependencies."""
    return {
        UserEventType.CREATED: cast(EventHandler, UserCreatedEventHandler()),
        UserEventType.UPDATED: cast(EventHandler, UserUpdatedEventHandler()),
        InvoiceEventType.CREATED: cast(EventHandler, InvoiceCreatedEventHandler()),
        InvoiceEventType.PAYMENT_REQUESTED: cast(EventHandler, InvoicePaymentRequestedHandler(event_publisher)),
        InvoiceEventType.PAID: cast(EventHandler, InvoicePaidEventHandler()),
    }


def deserialize_event(event_type: str, event_data: dict[str, Any]) -> BaseEvent:
    """Deserialize event data to the appropriate event class."""
    event_class = EVENT_CLASSES.get(event_type)
    if not event_class:
        # Fallback to BaseEvent for unknown event types
        logger.warning("Unknown event type, using BaseEvent", event_type=event_type)
        return BaseEvent(**event_data)

    return event_class(**event_data)


async def consume_queue(event_type: str, queue_url: str, event_handlers: dict[str, EventHandler]) -> None:
    """Consume events from a specific queue for a specific event type."""
    handler = event_handlers.get(event_type)
    if not handler:
        logger.warning("No handler found for event type, skipping queue", event_type=event_type, queue_url=queue_url)
        return

    logger.info("Starting consumer for event type", event_type=event_type, queue_url=queue_url)

    def deserializer(event_data: dict[str, Any]) -> BaseEvent:
        """Deserialize event data for this specific event type."""
        # Extract event_type from the event data itself
        actual_event_type = event_data.get("event_type")
        if not actual_event_type:
            logger.warning(
                "Event data missing event_type, using queue event_type",
                queue_event_type=event_type,
                event_data_keys=list(event_data.keys()),
            )
            actual_event_type = event_type

        # Validate that the event type matches the queue's expected type
        if actual_event_type != event_type:
            logger.warning(
                "Event type mismatch between queue and message",
                queue_event_type=event_type,
                message_event_type=actual_event_type,
            )

        return deserialize_event(actual_event_type, event_data)

    async def event_handler(event: BaseEvent) -> None:
        """Handle an event from this queue."""
        try:
            logger.info(
                "Processing event",
                event_id=str(event.event_id),
                event_type=event.event_type,
                aggregate_id=event.aggregate_id,
            )
            await handler.handle(event)
            logger.info(
                "Successfully processed event",
                event_id=str(event.event_id),
                event_type=event.event_type,
            )
        except Exception as e:
            logger.error(
                "Error processing event",
                event_id=str(event.event_id),
                event_type=event.event_type,
                error=str(e),
                exc_info=True,
            )
            raise

    consumer_config = SQSConsumerConfig(
        queue_url=queue_url,
        aws_region=settings.aws_region,
        aws_endpoint_url=settings.aws_endpoint_url,
        use_localstack=settings.use_localstack,
        max_messages=1,
        wait_time_seconds=5,
    )
    consumer = SQSConsumer(consumer_config, deserializer=deserializer)
    try:
        await consumer.consume(event_handler)
    except KeyboardInterrupt:
        logger.info("Received shutdown signal for consumer", event_type=event_type)
        raise
    except Exception as e:
        logger.error("Fatal error in consumer", event_type=event_type, error=str(e), exc_info=True)
        raise


async def main() -> None:
    """Main worker function."""
    setup_logging(settings)
    logger.info("Starting event consumer worker", environment=settings.environment)

    # Initialize database pool
    await PostgresPool.create_pool(settings)
    logger.info("Database pool initialized")

    # Create event publisher for handlers that need it
    topic_arn = settings.default_event_topic_arn
    if not topic_arn:
        raise ValueError("Default event topic ARN must be configured")
    sns_publisher = SNSPublisher(settings, topic_arn)
    event_publisher = EventPublisher(sns_publisher)

    # Create event handlers with dependencies
    event_handlers = create_event_handlers(event_publisher)

    # Get queue URLs from settings
    queue_urls = settings.event_queue_urls
    if not queue_urls:
        raise ValueError("Event queue URLs must be configured")

    logger.info("Queue URLs", queue_urls=queue_urls)

    # Create tasks for each event type queue
    tasks = []
    for event_type, queue_url in queue_urls.items():
        if not queue_url:
            logger.warning("Skipping event type with empty queue URL", event_type=event_type)
            continue
        task = asyncio.create_task(consume_queue(event_type, queue_url, event_handlers))
        tasks.append(task)

    if not tasks:
        raise ValueError("No valid queue URLs configured")

    logger.info("Starting consumers", num_queues=len(tasks))

    try:
        # Run all consumers concurrently
        # Use return_exceptions=True so one consumer failure doesn't stop others
        results = await asyncio.gather(*tasks, return_exceptions=True)
        # Log any exceptions that occurred
        for i, result in enumerate(results):
            if isinstance(result, Exception) and not isinstance(result, KeyboardInterrupt):
                logger.error(
                    "Consumer task failed",
                    task_index=i,
                    error=str(result),
                    exc_info=result,
                )
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        # Cancel all tasks
        for task in tasks:
            task.cancel()
        # Wait for tasks to complete cancellation
        await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == "__main__":
    asyncio.run(main())
