"""AWS infrastructure utilities."""

from app.adapters.aws.client import get_boto3_client_kwargs

__all__ = ["get_boto3_client_kwargs"]
