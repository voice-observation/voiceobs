"""Pydantic models for the voiceobs server API.

This package provides request, response, and common models organized by domain.
All models are re-exported here for backward compatibility.
"""

# Common models
from voiceobs.server.models.common import SpanAttributes

# Request models
from voiceobs.server.models.request import (
    AgentCreateRequest,
    AgentUpdateRequest,
    AgentVerificationRequest,
    PersonaCreateRequest,
    PersonaUpdateRequest,
    SpanBatchInput,
    SpanInput,
    TestRunRequest,
    TestScenarioCreateRequest,
    TestScenarioUpdateRequest,
    TestSuiteCreateRequest,
    TestSuiteUpdateRequest,
)

# Response models
from voiceobs.server.models.response import (
    AgentListItem,
    AgentResponse,
    AgentsListResponse,
    AnalysisResponse,
    AnalysisSummary,
    ClearSpansResponse,
    ConversationDetail,
    ConversationSummary,
    ConversationsListResponse,
    ConversationVolumeItem,
    ConversationVolumeResponse,
    ErrorResponse,
    EvalMetricsResponse,
    FailureBreakdownItem,
    FailureBreakdownResponse,
    FailureResponse,
    FailuresListResponse,
    HealthResponse,
    IngestResponse,
    LatencyBreakdownItem,
    LatencyBreakdownResponse,
    MetricsSummaryResponse,
    PersonaAudioPreviewResponse,
    PersonaListItem,
    PersonaResponse,
    PersonasListResponse,
    SpanDetailResponse,
    SpanListItem,
    SpanResponse,
    SpansListResponse,
    StageMetricsResponse,
    StagesResponse,
    TestExecutionResponse,
    TestRunResponse,
    TestScenarioResponse,
    TestScenariosListResponse,
    TestSummaryResponse,
    TestSuiteResponse,
    TestSuitesListResponse,
    TrendDataPoint,
    TrendResponse,
    TurnMetricsResponse,
    TurnResponse,
)

__all__ = [
    # Common
    "SpanAttributes",
    # Requests
    "SpanInput",
    "SpanBatchInput",
    "TestSuiteCreateRequest",
    "TestSuiteUpdateRequest",
    "TestScenarioCreateRequest",
    "TestScenarioUpdateRequest",
    "TestRunRequest",
    "PersonaCreateRequest",
    "PersonaUpdateRequest",
    "AgentCreateRequest",
    "AgentUpdateRequest",
    "AgentVerificationRequest",
    # Responses - Common
    "HealthResponse",
    "ErrorResponse",
    # Responses - Span
    "SpanResponse",
    "IngestResponse",
    "SpanListItem",
    "SpansListResponse",
    "SpanDetailResponse",
    "ClearSpansResponse",
    # Responses - Analysis
    "StageMetricsResponse",
    "TurnMetricsResponse",
    "EvalMetricsResponse",
    "AnalysisSummary",
    "StagesResponse",
    "AnalysisResponse",
    # Responses - Conversation
    "TurnResponse",
    "ConversationSummary",
    "ConversationDetail",
    "ConversationsListResponse",
    # Responses - Failure
    "FailureResponse",
    "FailuresListResponse",
    # Responses - Metrics
    "MetricsSummaryResponse",
    "LatencyBreakdownItem",
    "LatencyBreakdownResponse",
    "FailureBreakdownItem",
    "FailureBreakdownResponse",
    "ConversationVolumeItem",
    "ConversationVolumeResponse",
    "TrendDataPoint",
    "TrendResponse",
    # Responses - Test
    "TestSuiteResponse",
    "TestSuitesListResponse",
    "TestScenarioResponse",
    "TestScenariosListResponse",
    "TestRunResponse",
    "TestExecutionResponse",
    "TestSummaryResponse",
    # Responses - Persona
    "PersonaResponse",
    "PersonaListItem",
    "PersonasListResponse",
    "PersonaAudioPreviewResponse",
    # Responses - Agent
    "AgentResponse",
    "AgentListItem",
    "AgentsListResponse",
]

