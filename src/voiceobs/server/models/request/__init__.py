"""Request models for the voiceobs server API."""

from voiceobs.server.models.request.agent import (
    AgentCreateRequest,
    AgentUpdateRequest,
    AgentVerificationRequest,
)
from voiceobs.server.models.request.persona import (
    PersonaCreateRequest,
    PersonaUpdateRequest,
)
from voiceobs.server.models.request.span import SpanBatchInput, SpanInput
from voiceobs.server.models.request.test import (
    TestRunRequest,
    TestScenarioCreateRequest,
    TestScenarioUpdateRequest,
    TestSuiteCreateRequest,
    TestSuiteUpdateRequest,
)

__all__ = [
    # Span requests
    "SpanInput",
    "SpanBatchInput",
    # Test requests
    "TestSuiteCreateRequest",
    "TestSuiteUpdateRequest",
    "TestScenarioCreateRequest",
    "TestScenarioUpdateRequest",
    "TestRunRequest",
    # Persona requests
    "PersonaCreateRequest",
    "PersonaUpdateRequest",
    # Agent requests
    "AgentCreateRequest",
    "AgentUpdateRequest",
    "AgentVerificationRequest",
]
