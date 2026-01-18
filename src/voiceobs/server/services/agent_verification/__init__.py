"""Agent verification services package."""

from voiceobs.server.services.agent_verification.base import AgentVerifier
from voiceobs.server.services.agent_verification.factory import AgentVerifierFactory
from voiceobs.server.services.agent_verification.phone_verifier import PhoneAgentVerifier
from voiceobs.server.services.agent_verification.service import AgentVerificationService
from voiceobs.server.services.agent_verification.web_verifier import WebAgentVerifier

# Register verifiers with factory
AgentVerifierFactory.register_verifier("phone", PhoneAgentVerifier)
AgentVerifierFactory.register_verifier("web", WebAgentVerifier)

__all__ = [
    "AgentVerifier",
    "AgentVerifierFactory",
    "AgentVerificationService",
    "PhoneAgentVerifier",
    "WebAgentVerifier",
]
