"""Tests for agent verifier factory."""

import pytest

from voiceobs.server.services.agent_verification.base import AgentVerifier
from voiceobs.server.services.agent_verification.factory import AgentVerifierFactory


class MockVerifier(AgentVerifier):
    """Mock verifier for testing."""

    async def verify(self, contact_info):
        """Mock verify implementation."""
        return (True, None, None)

    def get_agent_type(self):
        """Return mock agent type."""
        return "mock"


class TestAgentVerifierFactory:
    """Tests for AgentVerifierFactory."""

    def setup_method(self):
        """Save original verifiers before each test."""
        self._original_verifiers = AgentVerifierFactory._verifiers.copy()

    def teardown_method(self):
        """Restore original verifiers after each test."""
        AgentVerifierFactory._verifiers = self._original_verifiers

    def test_register_verifier(self):
        """Should register a verifier."""
        AgentVerifierFactory.register_verifier("mock", MockVerifier)
        assert "mock" in AgentVerifierFactory._verifiers
        assert AgentVerifierFactory._verifiers["mock"] is MockVerifier

    def test_register_verifier_case_insensitive(self):
        """Should register verifiers case-insensitively."""
        AgentVerifierFactory.register_verifier("MOCK", MockVerifier)
        assert "mock" in AgentVerifierFactory._verifiers

    def test_list_verifiers(self):
        """Should list all registered verifiers."""
        AgentVerifierFactory._verifiers = {}
        AgentVerifierFactory.register_verifier("phone", MockVerifier)
        AgentVerifierFactory.register_verifier("web", MockVerifier)

        verifiers = AgentVerifierFactory.list_verifiers()
        assert "phone" in verifiers
        assert "web" in verifiers
        assert len(verifiers) == 2

    def test_create_with_registered_type(self):
        """Should create verifier for registered type."""
        AgentVerifierFactory.register_verifier("mock", MockVerifier)
        verifier = AgentVerifierFactory.create("mock")
        assert isinstance(verifier, MockVerifier)

    def test_create_case_insensitive(self):
        """Should create verifier case-insensitively."""
        AgentVerifierFactory.register_verifier("mock", MockVerifier)
        verifier = AgentVerifierFactory.create("MOCK")
        assert isinstance(verifier, MockVerifier)

    def test_create_unregistered_type_raises(self):
        """Should raise ValueError for unregistered type."""
        AgentVerifierFactory._verifiers = {"phone": MockVerifier}
        with pytest.raises(ValueError) as exc_info:
            AgentVerifierFactory.create("unsupported")
        assert "Unsupported agent type" in str(exc_info.value)
        assert "unsupported" in str(exc_info.value)
        assert "phone" in str(exc_info.value)  # Lists supported types

    def test_create_empty_registry_raises(self):
        """Should raise ValueError when no verifiers registered."""
        AgentVerifierFactory._verifiers = {}
        with pytest.raises(ValueError) as exc_info:
            AgentVerifierFactory.create("any")
        assert "Unsupported agent type" in str(exc_info.value)
