"""Utility functions for the voiceobs server."""

from __future__ import annotations

import logging
import time
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status

from voiceobs.analyzer import AnalysisResult
from voiceobs.server.models import (
    AnalysisResponse,
    AnalysisSummary,
    EvalMetricsResponse,
    StageMetricsResponse,
    StagesResponse,
    TurnMetricsResponse,
)


def analysis_result_to_response(result: AnalysisResult) -> AnalysisResponse:
    """Convert an AnalysisResult to an AnalysisResponse.

    Args:
        result: The analysis result from the analyzer.

    Returns:
        The response model for the API.
    """
    return AnalysisResponse(
        summary=AnalysisSummary(
            total_spans=result.total_spans,
            total_conversations=result.total_conversations,
            total_turns=result.total_turns,
        ),
        stages=StagesResponse(
            asr=StageMetricsResponse(
                stage_type="asr",
                count=result.asr_metrics.count,
                mean_ms=result.asr_metrics.mean_ms,
                p50_ms=result.asr_metrics.p50_ms,
                p95_ms=result.asr_metrics.p95_ms,
                p99_ms=result.asr_metrics.p99_ms,
            ),
            llm=StageMetricsResponse(
                stage_type="llm",
                count=result.llm_metrics.count,
                mean_ms=result.llm_metrics.mean_ms,
                p50_ms=result.llm_metrics.p50_ms,
                p95_ms=result.llm_metrics.p95_ms,
                p99_ms=result.llm_metrics.p99_ms,
            ),
            tts=StageMetricsResponse(
                stage_type="tts",
                count=result.tts_metrics.count,
                mean_ms=result.tts_metrics.mean_ms,
                p50_ms=result.tts_metrics.p50_ms,
                p95_ms=result.tts_metrics.p95_ms,
                p99_ms=result.tts_metrics.p99_ms,
            ),
        ),
        turns=TurnMetricsResponse(
            silence_samples=len(result.turn_metrics.silence_after_user_ms),
            silence_mean_ms=result.turn_metrics.silence_mean_ms,
            silence_p95_ms=result.turn_metrics.silence_p95_ms,
            total_agent_turns=result.turn_metrics.total_agent_turns,
            interruptions=result.turn_metrics.interruptions,
            interruption_rate=result.turn_metrics.interruption_rate,
        ),
        eval=EvalMetricsResponse(
            total_evals=result.eval_metrics.total_evals,
            intent_correct_count=result.eval_metrics.intent_correct_count,
            intent_incorrect_count=result.eval_metrics.intent_incorrect_count,
            intent_correct_rate=result.eval_metrics.intent_correct_rate,
            intent_failure_rate=result.eval_metrics.intent_failure_rate,
            avg_relevance_score=result.eval_metrics.avg_relevance_score,
            min_relevance_score=result.eval_metrics.min_relevance_score,
            max_relevance_score=result.eval_metrics.max_relevance_score,
        ),
    )


def parse_iso_datetime(dt_str: str) -> datetime | None:
    """Parse ISO datetime string.

    Args:
        dt_str: ISO 8601 datetime string.

    Returns:
        Parsed datetime object or None if parsing fails.
    """
    try:
        if isinstance(dt_str, str):
            # Remove Z and convert to +00:00 if needed
            if dt_str.endswith("Z"):
                dt_str = dt_str[:-1] + "+00:00"
            return datetime.fromisoformat(dt_str)
    except (ValueError, AttributeError, TypeError):
        return None
    return None


def parse_uuid(uuid_str: str, resource_name: str = "resource") -> UUID:
    """Parse and validate UUID string.

    Args:
        uuid_str: UUID string to parse.
        resource_name: Name of the resource for error messages.

    Returns:
        Parsed UUID.

    Raises:
        HTTPException: If UUID format is invalid.
    """
    try:
        return UUID(uuid_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {resource_name} ID format: {uuid_str}",
        )


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
        logger.info(f"{operation} took {duration:.3f}s")


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
                logger.debug(f"Cleanup error for {type(closable).__name__}", exc_info=True)
