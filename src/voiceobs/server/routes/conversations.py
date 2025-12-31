"""Conversation routes."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from voiceobs.analyzer import analyze_spans
from voiceobs.server.dependencies import (
    get_conversation_repository,
    get_storage,
    is_using_postgres,
)
from voiceobs.server.models import (
    ConversationDetail,
    ConversationsListResponse,
    ConversationSummary,
    ErrorResponse,
    TurnResponse,
)
from voiceobs.server.utils import analysis_result_to_response, parse_iso_datetime

router = APIRouter(tags=["Conversations"])


def _group_spans_by_conversation(all_spans: list[dict]) -> dict[str, list[dict]]:
    """Group spans by conversation ID.

    Args:
        all_spans: List of span dictionaries.

    Returns:
        Dictionary mapping conversation IDs to lists of spans.
    """
    conversations: dict[str, list[dict]] = {}
    for span in all_spans:
        conv_id = span.get("attributes", {}).get("voice.conversation.id")
        if conv_id:
            if conv_id not in conversations:
                conversations[conv_id] = []
            conversations[conv_id].append(span)
    return conversations


def _apply_time_range_filter(
    conversations: dict[str, list[dict]],
    start_time: datetime | None,
    end_time: datetime | None,
) -> dict[str, list[dict]]:
    """Apply time range filter to conversations.

    Args:
        conversations: Dictionary of conversation ID to spans.
        start_time: Filter by start time.
        end_time: Filter by end time.

    Returns:
        Filtered conversations dictionary.
    """
    if not (start_time or end_time):
        return conversations

    return {
        k: v
        for k, v in conversations.items()
        if any(
            (span_start_str := s.get("start_time"))
            and (span_start := parse_iso_datetime(span_start_str))
            and (not start_time or span_start >= start_time)
            and (not end_time or span_start <= end_time)
            for s in v
        )
    }


def _apply_actor_filter(conversations: dict[str, list[dict]], actor: str) -> dict[str, list[dict]]:
    """Apply actor filter to conversations.

    Args:
        conversations: Dictionary of conversation ID to spans.
        actor: Actor to filter by.

    Returns:
        Filtered conversations dictionary.
    """
    return {
        k: v
        for k, v in conversations.items()
        if any(
            s.get("attributes", {}).get("voice.actor") == actor
            for s in v
            if s.get("name") == "voice.turn"
        )
    }


def _apply_min_latency_filter(
    conversations: dict[str, list[dict]], min_latency_ms: float
) -> dict[str, list[dict]]:
    """Apply minimum latency filter to conversations.

    Args:
        conversations: Dictionary of conversation ID to spans.
        min_latency_ms: Minimum latency threshold.

    Returns:
        Filtered conversations dictionary.
    """
    return {
        k: v
        for k, v in conversations.items()
        if any((dur := s.get("duration_ms")) is not None and dur >= min_latency_ms for s in v)
    }


def _apply_in_memory_filters(
    conversations: dict[str, list[dict]],
    start_time: datetime | None,
    end_time: datetime | None,
    actor: str | None,
    min_latency_ms: float | None,
) -> dict[str, list[dict]]:
    """Apply filters to conversations in in-memory mode.

    Args:
        conversations: Dictionary of conversation ID to spans.
        start_time: Filter by start time.
        end_time: Filter by end time.
        actor: Filter by actor.
        min_latency_ms: Filter by minimum latency.

    Returns:
        Filtered conversations dictionary.
    """
    filtered = _apply_time_range_filter(conversations, start_time, end_time)

    if actor:
        filtered = _apply_actor_filter(filtered, actor)

    if min_latency_ms is not None:
        filtered = _apply_min_latency_filter(filtered, min_latency_ms)

    return filtered


def _build_conversation_summaries(
    filtered_conversations: dict[str, list[dict]],
) -> list[dict[str, Any]]:
    """Build conversation summaries with metadata for sorting.

    Args:
        filtered_conversations: Dictionary of conversation ID to spans.

    Returns:
        List of summary dictionaries with metadata.
    """
    summaries_data = []
    for conv_id, spans in filtered_conversations.items():
        turn_count = sum(1 for s in spans if s.get("name") == "voice.turn")

        # Calculate min start_time and avg latency for sorting
        start_times = [
            parse_iso_datetime(s.get("start_time")) for s in spans if s.get("start_time")
        ]
        start_times = [st for st in start_times if st is not None]
        min_start = min(start_times) if start_times else None

        latencies = [s.get("duration_ms") for s in spans if s.get("duration_ms") is not None]
        avg_latency = sum(latencies) / len(latencies) if latencies else None

        summaries_data.append(
            {
                "summary": ConversationSummary(
                    id=conv_id,
                    turn_count=turn_count,
                    span_count=len(spans),
                    has_failures=False,  # Will be updated when failures are checked
                ),
                "min_start_time": min_start,
                "avg_latency": avg_latency,
                "transcripts": [
                    str(s.get("attributes", {}).get("voice.transcript", "")) for s in spans
                ],
            }
        )
    return summaries_data


def _apply_in_memory_search(
    summaries_data: list[dict[str, Any]], query: str
) -> list[dict[str, Any]]:
    """Apply search filter to summaries in in-memory mode.

    Args:
        summaries_data: List of summary dictionaries.
        query: Search query string.

    Returns:
        Filtered summaries list.
    """
    q_lower = query.lower()
    return [
        s
        for s in summaries_data
        if q_lower in s["summary"].id.lower() or any(q_lower in t.lower() for t in s["transcripts"])
    ]


def _apply_in_memory_sorting(
    summaries_data: list[dict[str, Any]], sort: str, sort_order: str
) -> list[dict[str, Any]]:
    """Apply sorting to summaries in in-memory mode.

    Args:
        summaries_data: List of summary dictionaries.
        sort: Sort field (start_time, latency, relevance).
        sort_order: Sort order (asc, desc).

    Returns:
        Sorted summaries list.
    """
    if sort == "start_time":
        summaries_data.sort(
            key=lambda x: (
                x["min_start_time"] if x["min_start_time"] is not None else datetime.min
            ),
            reverse=(sort_order.lower() == "desc"),
        )
    elif sort == "latency":
        summaries_data.sort(
            key=lambda x: x["avg_latency"] or 0.0,
            reverse=(sort_order.lower() == "desc"),
        )
    else:
        # Default sort by conversation ID
        summaries_data.sort(
            key=lambda x: x["summary"].id,
            reverse=(sort_order.lower() == "desc"),
        )
    return summaries_data


@router.get(
    "/conversations",
    response_model=ConversationsListResponse,
    summary="List conversations with search and filtering",
    description="""
    Get a list of conversations with optional search, filtering, pagination, and sorting.

    Supports:
    - Full-text search via `q` parameter
    - Time range filtering via `start_time` and `end_time`
    - Actor filtering via `actor` parameter
    - Failure filtering via `has_failures` and `failure_type`
    - Latency filtering via `min_latency_ms`
    - Pagination via `limit` and `offset`
    - Sorting via `sort` and `sort_order`
    """,
)
async def list_conversations(
    q: str | None = Query(None, description="Full-text search query"),
    start_time: datetime | None = Query(
        None, description="Filter conversations starting after this time (ISO 8601)"
    ),
    end_time: datetime | None = Query(
        None, description="Filter conversations starting before this time (ISO 8601)"
    ),
    actor: str | None = Query(None, description="Filter by actor (user, agent, system)"),
    has_failures: bool | None = Query(None, description="Filter by failure status"),
    failure_type: str | None = Query(None, description="Filter by failure type"),
    min_latency_ms: float | None = Query(
        None, description="Filter by minimum latency threshold (ms)"
    ),
    sort: str = Query("start_time", description="Sort field (start_time, latency, relevance)"),
    sort_order: str = Query("desc", description="Sort order (asc, desc)"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
) -> ConversationsListResponse:
    """List conversations with optional search and filtering."""
    # Use PostgreSQL search if available
    if is_using_postgres():
        repo = get_conversation_repository()
        if repo is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database repository not available",
            )

        results, total = await repo.search(
            query=q,
            start_time=start_time,
            end_time=end_time,
            actor=actor,
            has_failures=has_failures,
            failure_type=failure_type,
            min_latency_ms=min_latency_ms,
            sort=sort,
            sort_order=sort_order,
            limit=limit,
            offset=offset,
        )

        summaries = [
            ConversationSummary(
                id=r["id"],
                turn_count=r["turn_count"],
                span_count=r["span_count"],
                has_failures=r["has_failures"],
            )
            for r in results
        ]

        return ConversationsListResponse(
            count=len(summaries),
            total=total,
            conversations=summaries,
            limit=limit,
            offset=offset,
        )

    # Fallback to in-memory storage
    return await _list_conversations_in_memory(
        q=q,
        start_time=start_time,
        end_time=end_time,
        actor=actor,
        min_latency_ms=min_latency_ms,
        sort=sort,
        sort_order=sort_order,
        limit=limit,
        offset=offset,
    )


async def _list_conversations_in_memory(
    q: str | None,
    start_time: datetime | None,
    end_time: datetime | None,
    actor: str | None,
    min_latency_ms: float | None,
    sort: str,
    sort_order: str,
    limit: int,
    offset: int,
) -> ConversationsListResponse:
    """List conversations using in-memory storage.

    Args:
        q: Search query.
        start_time: Filter by start time.
        end_time: Filter by end time.
        actor: Filter by actor.
        min_latency_ms: Filter by minimum latency.
        sort: Sort field.
        sort_order: Sort order.
        limit: Maximum results.
        offset: Results to skip.

    Returns:
        Conversations list response.
    """
    storage = get_storage()
    all_spans = await storage.get_spans_as_dicts()

    # Group spans by conversation ID
    conversations = _group_spans_by_conversation(all_spans)

    # Apply filters
    filtered_conversations = _apply_in_memory_filters(
        conversations, start_time, end_time, actor, min_latency_ms
    )

    # Build summaries with metadata
    summaries_data = _build_conversation_summaries(filtered_conversations)

    # Apply search if provided
    if q:
        summaries_data = _apply_in_memory_search(summaries_data, q)

    # Apply sorting
    summaries_data = _apply_in_memory_sorting(summaries_data, sort, sort_order)

    # Extract summaries and apply pagination
    summaries = [s["summary"] for s in summaries_data]
    total = len(summaries)
    summaries = summaries[offset : offset + limit]

    return ConversationsListResponse(
        count=len(summaries),
        total=total,
        conversations=summaries,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/conversations/search",
    response_model=ConversationsListResponse,
    summary="Search conversations",
    description="Full-text search across conversation transcripts and IDs.",
)
async def search_conversations(
    q: str = Query(..., description="Search query"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
) -> ConversationsListResponse:
    """Search conversations using full-text search."""
    # Redirect to main list endpoint with search query
    return await list_conversations(
        q=q,
        start_time=None,
        end_time=None,
        actor=None,
        has_failures=None,
        failure_type=None,
        min_latency_ms=None,
        sort="relevance",
        sort_order="desc",
        limit=limit,
        offset=offset,
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetail,
    summary="Get conversation details",
    description="Get detailed information about a specific conversation.",
    responses={
        404: {"model": ErrorResponse, "description": "Conversation not found"},
    },
)
async def get_conversation(conversation_id: str) -> ConversationDetail:
    """Get detailed conversation information."""
    storage = get_storage()
    all_spans = await storage.get_spans_as_dicts()

    # Filter spans by conversation ID
    conv_spans = [
        span
        for span in all_spans
        if span.get("attributes", {}).get("voice.conversation.id") == conversation_id
    ]

    if not conv_spans:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found",
        )

    # Extract turns
    turns = []
    for span in conv_spans:
        if span.get("name") == "voice.turn":
            attrs = span.get("attributes", {})
            turns.append(
                TurnResponse(
                    id=attrs.get("voice.turn.id", "unknown"),
                    actor=attrs.get("voice.actor", "unknown"),
                    turn_index=attrs.get("voice.turn.index"),
                    duration_ms=span.get("duration_ms"),
                    transcript=attrs.get("voice.transcript"),
                    attributes=attrs,
                )
            )

    # Sort turns by index
    turns.sort(key=lambda t: t.turn_index if t.turn_index is not None else 0)

    # Analyze conversation
    result = analyze_spans(conv_spans)
    analysis = analysis_result_to_response(result)

    return ConversationDetail(
        id=conversation_id,
        turns=turns,
        span_count=len(conv_spans),
        analysis=analysis,
    )
