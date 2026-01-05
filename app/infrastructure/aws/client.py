"""AWS client configuration utilities."""

import os
from typing import Any

import boto3

from app.config.settings import Settings


def get_boto3_client_kwargs(settings: Settings, service_name: str) -> dict[str, Any]:
    """Get kwargs for creating a boto3 client with LocalStack support.

    Automatically uses test credentials when LocalStack is detected.
    """
    kwargs: dict = {
        "service_name": service_name,
        "region_name": settings.aws_region,
    }

    # Add endpoint URL for LocalStack
    if settings.aws_endpoint_url:
        kwargs["endpoint_url"] = settings.aws_endpoint_url

    # Use test credentials for LocalStack
    if settings.use_localstack:
        # Set credentials as environment variables for boto3 to pick up
        # This is done here rather than in the client kwargs because boto3
        # prefers environment variables over explicit credentials
        os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
        os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
        os.environ.setdefault("AWS_DEFAULT_REGION", settings.aws_region)

    return kwargs


def create_boto3_client(settings: Settings, service_name: str) -> Any:
    """Create a boto3 client with LocalStack support."""
    kwargs = get_boto3_client_kwargs(settings, service_name)
    return boto3.client(**kwargs)
