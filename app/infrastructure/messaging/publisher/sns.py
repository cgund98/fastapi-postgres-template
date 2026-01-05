"""AWS SNS implementation of event publisher."""

import json

from botocore.exceptions import ClientError

from app.config.settings import Settings
from app.infrastructure.aws.client import create_boto3_client
from app.infrastructure.messaging.base import BaseEvent
from app.infrastructure.messaging.publisher.base import BasePublisher
from app.observability.logging import get_logger

logger = get_logger(__name__)


class SNSPublisher(BasePublisher):
    """AWS SNS implementation of BasePublisher."""

    def __init__(self, settings: Settings, topic_arn: str) -> None:
        """Initialize SNS publisher."""
        self._settings = settings
        self._topic_arn = topic_arn
        self._sns_client = create_boto3_client(settings, "sns")

    async def publish(self, event: BaseEvent) -> None:
        """Publish an event to SNS."""
        if not self._topic_arn:
            raise ValueError("Topic ARN must be provided")

        try:
            message = json.dumps(event.model_dump(), default=str)
            response = self._sns_client.publish(
                TopicArn=self._topic_arn,
                Message=message,
                MessageAttributes={
                    "event_type": {"DataType": "String", "StringValue": event.event_type},
                    "message_type": {"DataType": "String", "StringValue": event.event_type},  # Alias for filtering
                    "aggregate_type": {
                        "DataType": "String",
                        "StringValue": event.aggregate_type,
                    },
                },
            )
            logger.info(
                "Published event",
                event_id=str(event.event_id),
                event_type=event.event_type,
                message_id=response.get("MessageId"),
            )
        except ClientError as e:
            logger.error(
                "Failed to publish event",
                event_id=str(event.event_id),
                error=str(e),
                exc_info=True,
            )
            raise
