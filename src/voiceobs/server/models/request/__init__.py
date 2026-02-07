"""Request models for the voiceobs server API."""

from voiceobs.server.models.request.agent import (
    AgentCreateRequest,
    AgentUpdateRequest,
    AgentVerificationRequest,
)
from voiceobs.server.models.request.auth import UserUpdateRequest
from voiceobs.server.models.request.generate_scenarios import GenerateScenariosRequest
from voiceobs.server.models.request.organization import (
    CreateOrgRequest,
    SendInviteRequest,
    UpdateOrgRequest,
)
from voiceobs.server.models.request.persona import (
    PersonaActiveRequest,
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
    # Auth requests
    "UserUpdateRequest",
    # Span requests
    "SpanInput",
    "SpanBatchInput",
    # Test requests
    "TestSuiteCreateRequest",
    "TestSuiteUpdateRequest",
    "TestScenarioCreateRequest",
    "TestScenarioUpdateRequest",
    "TestRunRequest",
    "GenerateScenariosRequest",
    # Persona requests
    "PersonaCreateRequest",
    "PersonaUpdateRequest",
    "PersonaActiveRequest",
    # Agent requests
    "AgentCreateRequest",
    "AgentUpdateRequest",
    "AgentVerificationRequest",
    # Organization requests
    "CreateOrgRequest",
    "UpdateOrgRequest",
    "SendInviteRequest",
]
