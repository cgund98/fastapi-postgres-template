"""AWS infrastructure utilities."""

from app.infrastructure.aws.client import create_boto3_client, get_boto3_client_kwargs

__all__ = ["create_boto3_client", "get_boto3_client_kwargs"]
