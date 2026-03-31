"""AWS SNS implementation of event publisher."""

from itertools import batched
from typing import TYPE_CHECKING

from botocore.exceptions import ClientError

from app.domain.events.publisher import EventPublisher, PublishArgs
from app.domain.events.registry.envelope import Envelope
from app.observability.logging import get_logger

if TYPE_CHECKING:
    from types_boto3_sns.client import SNSClient
    from types_boto3_sns.type_defs import PublishBatchRequestEntryTypeDef

logger = get_logger(__name__)

MAX_BATCH_SIZE = 10


class SNSPublisher(EventPublisher):
    """AWS SNS implementation of BasePublisher."""

    def __init__(self, boto3_client: "SNSClient", topic_arn: str) -> None:
        """Initialize SNS publisher."""
        self._sns_client = boto3_client
        self._topic_arn = topic_arn

    async def publish(self, args: PublishArgs) -> None:
        """Publish an event to SNS."""
        return await self.publish_many([args])

    async def publish_many(self, args: list[PublishArgs]) -> None:
        """Publish an event to SNS."""
        if not self._topic_arn:
            raise ValueError("Topic ARN must be provided")

        for arg_batch in batched(args, MAX_BATCH_SIZE):
            envelopes = [Envelope.build(payload=arg.payload, source=arg.source) for arg in arg_batch]

            items: list[PublishBatchRequestEntryTypeDef] = [
                {
                    "Id": envelope.id,
                    "Message": envelope.to_json(),
                    "MessageAttributes": {
                        "event_type": {"DataType": "String", "StringValue": envelope.type},
                    },
                }
                for envelope in envelopes
            ]

            try:
                self._sns_client.publish_batch(
                    TopicArn=self._topic_arn,
                    PublishBatchRequestEntries=items,
                )
                logger.info(
                    "Published event",
                    event_ids=[envelope.id for envelope in envelopes],
                    event_types=[envelope.type for envelope in envelopes],
                )
            except ClientError:
                logger.exception(
                    "Failed to publish event",
                    event_ids=[envelope.id for envelope in envelopes],
                    event_types=[envelope.type for envelope in envelopes],
                    exc_info=True,
                )
                raise
