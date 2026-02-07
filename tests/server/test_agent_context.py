"""Tests for agent context field."""

from voiceobs.server.models import AgentCreateRequest, AgentResponse, AgentUpdateRequest


class TestAgentContextField:
    """Tests for the agent context field."""

    def test_agent_create_request_accepts_context(self):
        """Test that AgentCreateRequest accepts context field."""
        request = AgentCreateRequest(
            name="Pizza Bot",
            goal="Help customers order pizza",
            agent_type="phone",
            contact_info={"phone_number": "+15551234567"},
            supported_intents=["order_pizza", "check_status"],
            context="This is a pizza ordering assistant for Papa John's. "
            "It handles orders, checks order status, and processes refunds.",
        )

        assert request.context == (
            "This is a pizza ordering assistant for Papa John's. "
            "It handles orders, checks order status, and processes refunds."
        )

    def test_agent_create_request_context_is_optional(self):
        """Test that context field is optional."""
        request = AgentCreateRequest(
            name="Simple Bot",
            goal="Help customers",
            agent_type="phone",
            contact_info={"phone_number": "+15551234567"},
            supported_intents=["help"],
        )

        assert request.context is None

    def test_agent_response_includes_context(self):
        """Test that AgentResponse includes context field."""
        response = AgentResponse(
            id="550e8400-e29b-41d4-a716-446655440000",
            name="Pizza Bot",
            goal="Help customers order pizza",
            agent_type="phone",
            contact_info={"phone_number": "+15551234567"},
            supported_intents=["order_pizza"],
            connection_status="pending",
            verification_attempts=0,
            is_active=True,
            context="Pizza ordering context",
        )

        assert response.context == "Pizza ordering context"

    def test_agent_response_context_is_optional(self):
        """Test that AgentResponse context is optional and defaults to None."""
        response = AgentResponse(
            id="550e8400-e29b-41d4-a716-446655440000",
            name="Simple Bot",
            goal="Help customers",
            agent_type="phone",
            contact_info={"phone_number": "+15551234567"},
            supported_intents=["help"],
            connection_status="pending",
            verification_attempts=0,
            is_active=True,
        )

        assert response.context is None

    def test_agent_update_request_accepts_context(self):
        """Test that AgentUpdateRequest accepts context field."""
        request = AgentUpdateRequest(context="Updated context information")
        assert request.context == "Updated context information"
