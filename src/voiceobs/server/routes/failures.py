"""Failure detection routes."""

from fastapi import APIRouter

from voiceobs.classifier import FailureClassifier
from voiceobs.server.models import FailureResponse, FailuresListResponse
from voiceobs.server.store import get_span_store

router = APIRouter(tags=["Failures"])


@router.get(
    "/failures",
    response_model=FailuresListResponse,
    summary="List detected failures",
    description="Get all detected failures with optional filtering by severity.",
)
async def list_failures(
    severity: str | None = None,
    type: str | None = None,
) -> FailuresListResponse:
    """List all detected failures."""
    store = get_span_store()
    all_spans = store.get_spans_as_dicts()

    # Classify failures
    classifier = FailureClassifier()
    classification = classifier.classify(all_spans)

    # Convert to response format
    failures = []
    by_severity: dict[str, int] = {}
    by_type: dict[str, int] = {}

    for failure in classification.failures:
        # Apply filters
        if severity and failure.severity.value != severity:
            continue
        if type and failure.type.value != type:
            continue

        failures.append(
            FailureResponse(
                id=str(len(failures)),
                type=failure.type.value,
                severity=failure.severity.value,
                message=failure.message,
                conversation_id=failure.conversation_id,
                turn_id=failure.turn_id,
                turn_index=failure.turn_index,
                signal_name=failure.signal_name,
                signal_value=failure.signal_value,
                threshold=failure.threshold,
            )
        )

        # Count by severity and type
        sev = failure.severity.value
        by_severity[sev] = by_severity.get(sev, 0) + 1
        ftype = failure.type.value
        by_type[ftype] = by_type.get(ftype, 0) + 1

    return FailuresListResponse(
        count=len(failures),
        failures=failures,
        by_severity=by_severity,
        by_type=by_type,
    )
