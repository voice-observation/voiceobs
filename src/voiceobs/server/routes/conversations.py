"""Conversation routes."""

from fastapi import APIRouter, HTTPException, status

from voiceobs.analyzer import analyze_spans
from voiceobs.server.models import (
    ConversationDetail,
    ConversationsListResponse,
    ConversationSummary,
    ErrorResponse,
    TurnResponse,
)
from voiceobs.server.store import get_span_store
from voiceobs.server.utils import analysis_result_to_response

router = APIRouter(tags=["Conversations"])


@router.get(
    "/conversations",
    response_model=ConversationsListResponse,
    summary="List all conversations",
    description="Get a list of all conversations.",
)
async def list_conversations() -> ConversationsListResponse:
    """List all conversations."""
    store = get_span_store()
    all_spans = store.get_spans_as_dicts()

    # Group spans by conversation ID
    conversations: dict[str, list[dict]] = {}
    for span in all_spans:
        conv_id = span.get("attributes", {}).get("voice.conversation.id")
        if conv_id:
            if conv_id not in conversations:
                conversations[conv_id] = []
            conversations[conv_id].append(span)

    # Build summaries
    summaries = []
    for conv_id, spans in conversations.items():
        turn_count = sum(1 for s in spans if s.get("name") == "voice.turn")
        summaries.append(
            ConversationSummary(
                id=conv_id,
                turn_count=turn_count,
                span_count=len(spans),
                has_failures=False,  # Will be updated when failures are checked
            )
        )

    return ConversationsListResponse(
        count=len(summaries),
        conversations=summaries,
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
    store = get_span_store()
    all_spans = store.get_spans_as_dicts()

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
