"""AWS SQS implementation of event consumer."""

import asyncio
import json
import os
from collections.abc import Awaitable, Callable
from typing import Any

import boto3
from botocore.exceptions import ClientError

from app.infrastructure.messaging.base import BaseEvent
from app.infrastructure.messaging.consumer.base import BaseConsumer
from app.infrastructure.messaging.consumer.config import SQSConsumerConfig
from app.observability.logging import get_logger

logger = get_logger(__name__)


class SQSConsumer(BaseConsumer):
    """
    AWS SQS implementation of BaseConsumer.

    We wrap the boto3 client in a thread pool executor to avoid blocking the event loop.
    """

    def __init__(
        self,
        config: SQSConsumerConfig,
        deserializer: Callable[[dict[str, Any]], BaseEvent] | None = None,
    ) -> None:
        """Initialize SQS consumer."""
        self._config = config
        self._deserializer = deserializer or (lambda data: BaseEvent(**data))
        self._sqs_client = self._create_sqs_client()
        self._logger = get_logger(__name__).bind(queue_url=self._config.queue_url)

    def _create_sqs_client(self) -> Any:
        """Create a boto3 SQS client with LocalStack support."""
        kwargs: dict[str, Any] = {
            "service_name": "sqs",
            "region_name": self._config.aws_region,
        }

        # Add endpoint URL for LocalStack
        if self._config.aws_endpoint_url:
            kwargs["endpoint_url"] = self._config.aws_endpoint_url

        # Use test credentials for LocalStack
        if self._config.use_localstack:
            # Set credentials as environment variables for boto3 to pick up
            # This is done here rather than in the client kwargs because boto3
            # prefers environment variables over explicit credentials
            os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
            os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
            os.environ.setdefault("AWS_DEFAULT_REGION", self._config.aws_region)

        return boto3.client(**kwargs)

    async def consume(self, handler: Callable[[BaseEvent], Awaitable[None]]) -> None:
        """Start consuming events from SQS queue."""
        self._logger.info("Starting SQS consumer")

        while True:
            try:
                # Run blocking boto3 call in thread pool to avoid blocking event loop
                response = await asyncio.to_thread(
                    self._sqs_client.receive_message,
                    QueueUrl=self._config.queue_url,
                    MaxNumberOfMessages=self._config.max_messages,
                    WaitTimeSeconds=self._config.wait_time_seconds,
                    MessageAttributeNames=["All"],
                )

                messages = response.get("Messages", [])
                if not messages:
                    continue

                for message in messages:
                    receipt_handle = message["ReceiptHandle"]
                    try:
                        # With raw message delivery, the body is the raw JSON string payload
                        # Message attributes are available in message["MessageAttributes"]
                        body_str = message["Body"]
                        body = json.loads(body_str)

                        # Handle raw message delivery (when RawMessageDelivery is enabled)
                        # Raw messages are delivered directly without SNS wrapper
                        if isinstance(body, dict) and "TopicArn" in body and "Message" in body:
                            # SNS wrapped message (fallback for non-raw delivery)
                            event_data = json.loads(body["Message"])
                        else:
                            # Raw message delivery - body is the event data directly
                            # The body is already parsed JSON, so use it directly
                            event_data = body

                        event = self._deserializer(event_data)
                        await handler(event)
                        await self.ack(receipt_handle)
                    except Exception as e:
                        logger.error(
                            "Error processing message",
                            receipt_handle=receipt_handle,
                            error=str(e),
                            exc_info=True,
                        )
                        await self.nack(receipt_handle)

            except ClientError as e:
                self._logger.error("Error receiving messages", error=str(e), exc_info=True)
                # Continue consuming despite errors

    async def ack(self, receipt_handle: str) -> None:
        """Acknowledge successful processing."""
        try:
            # Run blocking boto3 call in thread pool to avoid blocking event loop
            await asyncio.to_thread(
                self._sqs_client.delete_message,
                QueueUrl=self._config.queue_url,
                ReceiptHandle=receipt_handle,
            )
        except ClientError as e:
            self._logger.error(
                "Failed to acknowledge message",
                receipt_handle=receipt_handle,
                error=str(e),
                exc_info=True,
            )
            raise

    async def nack(self, receipt_handle: str) -> None:
        """Negatively acknowledge failed processing."""
        # For SQS, nack means not deleting the message, which will make it
        # visible again after visibility timeout
        self._logger.warning("Nacking message", receipt_handle=receipt_handle)
