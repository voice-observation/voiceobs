"""Generic retry logic for AWS and other clients."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import TypeVar

logger = logging.getLogger(__name__)

# AWS error codes that are retryable (throttling, transient failures)
AWS_RETRYABLE_ERROR_CODES = frozenset(
    {
        "RequestThrottled",
        "Throttling",
        "ThrottlingException",
        "ThrottledException",
        "OverLimit",
        "ServiceUnavailable",
        "InternalServerError",
        "RequestTimeout",
        "RequestTimeoutException",
    }
)


def is_aws_error_retryable(error: BaseException) -> bool:
    """Check if an AWS/boto3 exception is retryable.

    Args:
        error: The exception to check.

    Returns:
        True if the error is transient and worth retrying.
    """
    from botocore.exceptions import ClientError

    if isinstance(error, ClientError):
        code = error.response.get("Error", {}).get("Code", "")
        return code in AWS_RETRYABLE_ERROR_CODES
    return isinstance(error, (ConnectionError, TimeoutError))


_T = TypeVar("_T")


def retry(
    operation: str,
    fn: Callable[[], _T],
    max_retries: int = 2,
    base_delay: float = 1.0,
    is_retryable: Callable[[BaseException], bool] | None = None,
) -> _T:
    """Execute fn with retries on transient failures.

    Args:
        operation: Name of the operation (for logging).
        fn: Callable to execute. Takes no args, returns result.
        max_retries: Number of retries (default 2 = 3 total attempts).
        base_delay: Base delay in seconds for exponential backoff.
        is_retryable: Predicate to determine if an exception is retryable.
            Defaults to is_aws_error_retryable for AWS clients.

    Returns:
        The result of fn().

    Raises:
        The last exception if all attempts fail or error is not retryable.
    """
    predicate = is_retryable or is_aws_error_retryable
    last_exc: BaseException | None = None
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except BaseException as e:
            last_exc = e
            if attempt < max_retries and predicate(e):
                delay = base_delay * (2**attempt)
                logger.warning(
                    "%s failed (attempt %d/%d): %s, retrying in %.1fs",
                    operation,
                    attempt + 1,
                    max_retries + 1,
                    e,
                    delay,
                )
                time.sleep(delay)
            else:
                raise
    raise last_exc  # type: ignore[misc]


def retryable(
    operation: str,
    *,
    max_retries: int | None = None,
    base_delay: float | None = None,
):
    """Decorator for methods that should retry on transient failures.

    Reads max_retries and base_delay from self._max_retries and self._retry_base_delay
    when not provided. Use for instance methods on clients that have those attributes.

    Args:
        operation: Name of the operation (for logging).
        max_retries: Override retry count. If None, uses self._max_retries.
        base_delay: Override base delay. If None, uses self._retry_base_delay.

    Example:
        @retryable("send_message")
        def send_message(self, body: dict) -> str:
            ...
    """

    def decorator(fn: Callable[..., _T]) -> Callable[..., _T]:
        def wrapper(*args: object, **kwargs: object) -> _T:
            mr = max_retries
            bd = base_delay
            if args and hasattr(args[0], "_max_retries"):
                obj = args[0]
                if mr is None:
                    mr = getattr(obj, "_max_retries", 2)
                if bd is None:
                    bd = getattr(obj, "_retry_base_delay", 1.0)
            mr = mr if mr is not None else 2
            bd = bd if bd is not None else 1.0

            def _do() -> _T:
                return fn(*args, **kwargs)

            return retry(operation, _do, mr, bd)

        return wrapper  # type: ignore[return-value]

    return decorator
