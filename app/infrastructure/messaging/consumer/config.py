"""Configuration for message consumers."""

from dataclasses import dataclass


@dataclass
class SQSConsumerConfig:
    """Configuration for SQS consumer."""

    queue_url: str
    aws_region: str
    aws_endpoint_url: str | None = None
    use_localstack: bool = False
    max_messages: int = 10  # Maximum number of messages to receive per batch
    wait_time_seconds: int = 20  # Long polling wait time in seconds
