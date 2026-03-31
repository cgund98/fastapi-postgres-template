"""AWS SQS implementation of event consumer."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING, Any

from botocore.exceptions import ClientError

from app.domain.events.consumer import EventConsumer
from app.domain.events.registry.envelope import Envelope
from app.domain.events.router import EventRouter
from app.observability.logging import get_logger

if TYPE_CHECKING:
    from types_boto3_sqs.client import SQSClient
    from types_boto3_sqs.type_defs import MessageTypeDef

logger = get_logger(__name__)


@dataclass
class SQSConsumerConfig:
    queue_url: str
    wait_time_seconds: int
    max_messages: int


class SQSConsumer(EventConsumer):
    """
    AWS SQS implementation of BaseConsumer.

    We wrap the boto3 client in a thread pool executor to avoid blocking the event loop.
    """

    def __init__(
        self,
        sqs_client: "SQSClient",
        config: SQSConsumerConfig,
    ) -> None:
        """Initialize SQS consumer."""
        self._sqs_client = sqs_client
        self._config = config
        self._logger = get_logger(__name__).bind(queue_url=self._config.queue_url)

        self._executor = ThreadPoolExecutor(max_workers=1)

    @staticmethod
    def parse_envelope(message: dict[str, Any]) -> Envelope:
        """Parse an envelope from a SQS message."""
        try:
            # With raw message delivery, the body is the raw JSON string payload
            # Message attributes are available in message["MessageAttributes"]
            body_str = message["Body"]
            return Envelope.model_validate_json(body_str)
        except Exception as e:
            logger.exception("Error parsing envelope", error=str(e), exc_info=True)
            raise

    async def _handle_message(self, message: "MessageTypeDef", router: "EventRouter") -> None:
        """Handle a SQS message."""
        receipt_handle = message["ReceiptHandle"]
        try:
            envelope = self.parse_envelope(message)  # type: ignore[arg-type]

            await router.route(envelope)
            await self.ack(receipt_handle)
        except Exception:
            logger.exception("Error processing message", receipt_handle=message["ReceiptHandle"], exc_info=True)
            await self.nack(receipt_handle)

    async def _handle_batch(self, messages: list["MessageTypeDef"], router: "EventRouter") -> None:
        """Handle a batch of SQS messages."""
        for message in messages:
            await self._handle_message(message, router)

    async def consume(self, router: "EventRouter") -> None:
        """Start consuming events from SQS queue."""
        self._logger.info(
            "Starting SQS consumer",
            queue_url=self._config.queue_url,
            max_messages=self._config.max_messages,
            wait_time_seconds=self._config.wait_time_seconds,
        )

        while True:
            try:
                # Run blocking boto3 call in thread pool to avoid blocking event loop
                loop = asyncio.get_running_loop()
                receive_msg_partial = partial(
                    self._sqs_client.receive_message,
                    QueueUrl=self._config.queue_url,
                    MaxNumberOfMessages=self._config.max_messages,
                    WaitTimeSeconds=self._config.wait_time_seconds,
                    MessageAttributeNames=["All"],
                )
                response = await loop.run_in_executor(
                    self._executor,
                    receive_msg_partial,
                )

                messages = response.get("Messages", [])
                if not messages:
                    continue

                await self._handle_batch(messages, router)
            except Exception:
                logger.exception("Error consuming messages", exc_info=True)
                continue

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
