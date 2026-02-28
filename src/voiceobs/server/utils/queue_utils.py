"""Queue utility functions (e.g. SQS URL parsing)."""

from __future__ import annotations


def region_from_queue_url(queue_url: str) -> str | None:
    """Extract AWS region from SQS queue URL.

    Format: https://sqs.{region}.amazonaws.com/{account}/{queue_name}

    Args:
        queue_url: Full SQS queue URL.

    Returns:
        Region string (e.g. "us-west-1") or None if URL format is unrecognized.
    """
    if not queue_url.startswith("https://sqs."):
        return None
    rest = queue_url[len("https://sqs.") :]
    region = rest.split(".amazonaws.com")[0]
    return region if region else None
