"""Async and timing helpers with no heavy dependencies.

This module is intentionally kept lightweight to avoid circular imports.
Import from here instead of utils.common when loading early in the import chain
(e.g. from agent_verification.phone_verifier).
"""

from __future__ import annotations

import logging
import time
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any


@contextmanager
def log_timing(logger: logging.Logger, operation: str) -> Generator[None, None, None]:
    """Context manager to log operation timing.

    Args:
        logger: Logger instance to use for logging
        operation: Description of the operation being timed

    Yields:
        None

    Examples:
        >>> import logging
        >>> logger = logging.getLogger(__name__)
        >>> with log_timing(logger, "Database query"):
        ...     # do something
        ...     pass
        # Logs: "Database query took 0.123s"
    """
    start = time.monotonic()
    try:
        yield
    finally:
        duration = time.monotonic() - start
        logger.info("%s took %.3fs", operation, duration)


async def safe_cleanup(*closables: Any, logger: logging.Logger | None = None) -> None:
    """Safely close multiple async resources, ignoring errors.

    This helper attempts to close each resource in order, continuing even if
    some closures fail. It checks for common close methods in order:
    aclose(), disconnect(), close().

    Args:
        *closables: Resources to close (can include None values)
        logger: Optional logger to log cleanup errors at DEBUG level

    Examples:
        >>> async def example():
        ...     session = aiohttp.ClientSession()
        ...     room = rtc.Room()
        ...     api_client = api.LiveKitAPI()
        ...     # ... use resources ...
        ...     await safe_cleanup(session, room, api_client)
    """
    for closable in closables:
        if closable is None:
            continue
        try:
            if hasattr(closable, "aclose"):
                await closable.aclose()
            elif hasattr(closable, "disconnect"):
                await closable.disconnect()
            elif hasattr(closable, "close"):
                result = closable.close()
                # Handle both sync and async close methods
                if hasattr(result, "__await__"):
                    await result
        except Exception:
            if logger:
                logger.debug("Cleanup error for %s", type(closable).__name__, exc_info=True)
