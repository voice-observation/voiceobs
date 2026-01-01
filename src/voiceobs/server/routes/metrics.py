"""Metrics aggregation routes."""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status

from voiceobs.server.dependencies import get_metrics_repository, is_using_postgres
from voiceobs.server.models import (
    ConversationVolumeResponse,
    FailureBreakdownResponse,
    LatencyBreakdownResponse,
    MetricsSummaryResponse,
    TrendResponse,
)

router = APIRouter(tags=["Metrics"])


@router.get(
    "/metrics/summary",
    response_model=MetricsSummaryResponse,
    summary="Get overall metrics summary",
    description="""
    Get overall statistics including:
    - Total conversations, turns, duration
    - Average latency (P50/P95/P99) by stage
    - Failure rate and breakdown
    - Silence and overlap statistics

    Supports filtering by time range and conversation ID.
    """,
)
async def get_metrics_summary(
    start_time: datetime | None = Query(None, description="Filter by start time (ISO 8601)"),
    end_time: datetime | None = Query(None, description="Filter by end time (ISO 8601)"),
    conversation_id: str | None = Query(None, description="Filter by conversation ID"),
) -> MetricsSummaryResponse:
    """Get overall metrics summary."""
    if not is_using_postgres():
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Metrics API requires PostgreSQL database",
        )

    repo = get_metrics_repository()
    if repo is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Metrics repository not available",
        )

    summary = await repo.get_summary(
        start_time=start_time,
        end_time=end_time,
        conversation_id=conversation_id,
    )

    return MetricsSummaryResponse(**summary)


@router.get(
    "/metrics/latency",
    response_model=LatencyBreakdownResponse,
    summary="Get latency breakdown by group",
    description="""
    Get latency metrics broken down by stage or other grouping.

    Supports:
    - Grouping by stage (default) or custom span attribute
    - Time range filtering
    - Conversation ID filtering

    Returns P50, P95, P99 percentiles for each group.
    """,
)
async def get_latency_breakdown(
    group_by: str = Query("stage", description="Group by field (default: 'stage')"),
    start_time: datetime | None = Query(None, description="Filter by start time (ISO 8601)"),
    end_time: datetime | None = Query(None, description="Filter by end time (ISO 8601)"),
    conversation_id: str | None = Query(None, description="Filter by conversation ID"),
) -> LatencyBreakdownResponse:
    """Get latency breakdown grouped by specified field."""
    if not is_using_postgres():
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Metrics API requires PostgreSQL database",
        )

    repo = get_metrics_repository()
    if repo is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Metrics repository not available",
        )

    breakdown = await repo.get_latency_breakdown(
        group_by=group_by,
        start_time=start_time,
        end_time=end_time,
        conversation_id=conversation_id,
    )

    from voiceobs.server.models import LatencyBreakdownItem

    return LatencyBreakdownResponse(breakdown=[LatencyBreakdownItem(**item) for item in breakdown])


@router.get(
    "/metrics/failures",
    response_model=FailureBreakdownResponse,
    summary="Get failure breakdown by group",
    description="""
    Get failure counts broken down by type or severity.

    Supports:
    - Grouping by type (default) or severity
    - Time range filtering
    - Conversation ID filtering

    Returns counts and percentages for each group.
    """,
)
async def get_failure_breakdown(
    group_by: str = Query(
        "type", description="Group by field ('type' or 'severity', default: 'type')"
    ),
    start_time: datetime | None = Query(None, description="Filter by start time (ISO 8601)"),
    end_time: datetime | None = Query(None, description="Filter by end time (ISO 8601)"),
    conversation_id: str | None = Query(None, description="Filter by conversation ID"),
) -> FailureBreakdownResponse:
    """Get failure breakdown grouped by specified field."""
    if not is_using_postgres():
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Metrics API requires PostgreSQL database",
        )

    repo = get_metrics_repository()
    if repo is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Metrics repository not available",
        )

    breakdown, total = await repo.get_failure_breakdown(
        group_by=group_by,
        start_time=start_time,
        end_time=end_time,
        conversation_id=conversation_id,
    )

    from voiceobs.server.models import FailureBreakdownItem

    return FailureBreakdownResponse(
        breakdown=[FailureBreakdownItem(**item) for item in breakdown],
        total=total,
    )


@router.get(
    "/metrics/conversations",
    response_model=ConversationVolumeResponse,
    summary="Get conversation volume over time",
    description="""
    Get conversation volume aggregated by time buckets.

    Supports:
    - Grouping by hour, day, or week
    - Time range filtering
    - Conversation ID filtering

    Returns time series data suitable for charting.
    """,
)
async def get_conversation_volume(
    group_by: str = Query(
        "hour", description="Time grouping ('hour', 'day', 'week', default: 'hour')"
    ),
    start_time: datetime | None = Query(None, description="Filter by start time (ISO 8601)"),
    end_time: datetime | None = Query(None, description="Filter by end time (ISO 8601)"),
    conversation_id: str | None = Query(None, description="Filter by conversation ID"),
) -> ConversationVolumeResponse:
    """Get conversation volume over time."""
    if not is_using_postgres():
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Metrics API requires PostgreSQL database",
        )

    repo = get_metrics_repository()
    if repo is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Metrics repository not available",
        )

    volume = await repo.get_conversation_volume(
        group_by=group_by,
        start_time=start_time,
        end_time=end_time,
        conversation_id=conversation_id,
    )

    from voiceobs.server.models import ConversationVolumeItem

    return ConversationVolumeResponse(volume=[ConversationVolumeItem(**item) for item in volume])


@router.get(
    "/metrics/trends",
    response_model=TrendResponse,
    summary="Get time-series trends",
    description="""
    Get time-series trends for metrics with rolling averages.

    Supports:
    - Metrics: latency, failures, conversations
    - Time windows: 1h, 1d, 1w (and multiples)
    - Time range filtering
    - Conversation ID filtering

    Returns data points with values and rolling averages.
    """,
)
async def get_trends(
    metric: str = Query(
        "latency", description="Metric name ('latency', 'failures', 'conversations')"
    ),
    window: str = Query("1h", description="Time window (e.g., '1h', '1d', '1w')"),
    start_time: datetime | None = Query(None, description="Filter by start time (ISO 8601)"),
    end_time: datetime | None = Query(None, description="Filter by end time (ISO 8601)"),
    conversation_id: str | None = Query(None, description="Filter by conversation ID"),
) -> TrendResponse:
    """Get time-series trends for a metric."""
    if not is_using_postgres():
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Metrics API requires PostgreSQL database",
        )

    repo = get_metrics_repository()
    if repo is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Metrics repository not available",
        )

    data_points = await repo.get_trends(
        metric=metric,
        window=window,
        start_time=start_time,
        end_time=end_time,
        conversation_id=conversation_id,
    )

    from voiceobs.server.models import TrendDataPoint

    return TrendResponse(
        metric=metric,
        window=window,
        data_points=[TrendDataPoint(**item) for item in data_points],
    )
