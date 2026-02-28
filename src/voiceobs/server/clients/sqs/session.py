"""SQS client creation using boto3 Session (matches S3 credential pattern)."""

from __future__ import annotations

import os
from typing import Any


def create_sqs_client(
    aws_access_key_id: str | None = None,
    aws_secret_access_key: str | None = None,
    region_name: str | None = None,
) -> Any:
    """Create SQS client using boto3 Session with explicit credentials.

    Matches S3 initialization pattern for consistent AWS credential handling.
    Uses AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION from env when
    not provided.

    Args:
        aws_access_key_id: AWS access key (optional, uses env).
        aws_secret_access_key: AWS secret key (optional, uses env).
        region_name: AWS region (optional, uses env, default us-east-1).

    Returns:
        boto3 SQS client.
    """
    import boto3

    access_key = aws_access_key_id or os.environ.get("AWS_ACCESS_KEY_ID")
    secret_key = aws_secret_access_key or os.environ.get("AWS_SECRET_ACCESS_KEY")
    region = region_name or os.environ.get("AWS_REGION", "us-east-1")
    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
    )
    client = session.client("sqs")
    return client
