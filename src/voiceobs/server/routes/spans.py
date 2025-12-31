"""Span ingestion and retrieval routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from voiceobs.server.models import (
    ErrorResponse,
    IngestResponse,
    SpanBatchInput,
    SpanInput,
)
from voiceobs.server.store import get_span_store

router = APIRouter(tags=["Spans"])


@router.post(
    "/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest spans",
    description="Ingest one or more spans for analysis.",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid span data"},
    },
)
async def ingest(
    payload: SpanInput | SpanBatchInput,
) -> IngestResponse:
    """Ingest spans endpoint.

    Accepts either a single span or a batch of spans.
    """
    store = get_span_store()
    span_ids: list[UUID] = []

    # Handle single span or batch
    if isinstance(payload, SpanBatchInput):
        spans = payload.spans
    else:
        spans = [payload]

    for span in spans:
        # Convert datetime to ISO string if present
        start_time_str = span.start_time.isoformat() if span.start_time else None
        end_time_str = span.end_time.isoformat() if span.end_time else None

        span_id = store.add_span(
            name=span.name,
            start_time=start_time_str,
            end_time=end_time_str,
            duration_ms=span.duration_ms,
            attributes=span.attributes,
            trace_id=span.trace_id,
            span_id=span.span_id,
            parent_span_id=span.parent_span_id,
        )
        span_ids.append(span_id)

    return IngestResponse(
        accepted=len(span_ids),
        span_ids=span_ids,
    )


@router.get(
    "/spans",
    summary="List all spans",
    description="Get all ingested spans.",
)
async def list_spans() -> dict:
    """List all ingested spans."""
    store = get_span_store()
    spans = store.get_all_spans()
    return {
        "count": len(spans),
        "spans": [
            {
                "id": str(span.id),
                "name": span.name,
                "duration_ms": span.duration_ms,
                "attributes": span.attributes,
            }
            for span in spans
        ],
    }


@router.get(
    "/spans/{span_id}",
    summary="Get span by ID",
    description="Get a specific span by its ID.",
    responses={
        404: {"model": ErrorResponse, "description": "Span not found"},
    },
)
async def get_span(span_id: UUID) -> dict:
    """Get a specific span by ID."""
    store = get_span_store()
    span = store.get_span(span_id)

    if span is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Span with ID {span_id} not found",
        )

    return {
        "id": str(span.id),
        "name": span.name,
        "start_time": span.start_time,
        "end_time": span.end_time,
        "duration_ms": span.duration_ms,
        "attributes": span.attributes,
        "trace_id": span.trace_id,
        "span_id": span.span_id,
        "parent_span_id": span.parent_span_id,
    }


@router.delete(
    "/spans",
    summary="Clear all spans",
    description="Delete all ingested spans from the store.",
)
async def clear_spans() -> dict:
    """Clear all spans from the store."""
    store = get_span_store()
    count = store.clear()
    return {"cleared": count}
