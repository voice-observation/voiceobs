"""Analysis routes."""

from fastapi import APIRouter, HTTPException, status

from voiceobs.analyzer import analyze_spans
from voiceobs.server.dependencies import get_storage
from voiceobs.server.models import AnalysisResponse, ErrorResponse
from voiceobs.server.utils import analysis_result_to_response

router = APIRouter(tags=["Analysis"])


@router.get(
    "/analyze",
    response_model=AnalysisResponse,
    summary="Analyze all spans",
    description="Analyze all ingested spans and return metrics.",
)
async def analyze_all() -> AnalysisResponse:
    """Analyze all ingested spans."""
    storage = get_storage()
    spans = await storage.get_spans_as_dicts()
    result = analyze_spans(spans)
    return analysis_result_to_response(result)


@router.get(
    "/analyze/{conversation_id}",
    response_model=AnalysisResponse,
    summary="Analyze specific conversation",
    description="Analyze spans for a specific conversation.",
    responses={
        404: {"model": ErrorResponse, "description": "Conversation not found"},
    },
)
async def analyze_conversation(conversation_id: str) -> AnalysisResponse:
    """Analyze spans for a specific conversation."""
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

    result = analyze_spans(conv_spans)
    return analysis_result_to_response(result)
