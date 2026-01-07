"""Tests for persona-related Pydantic models."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from voiceobs.server.models import (
    PersonaAudioPreviewResponse,
    PersonaCreateRequest,
    PersonaListItem,
    PersonaResponse,
    PersonasListResponse,
    PersonaUpdateRequest,
    TestScenarioCreateRequest,
    TestScenarioUpdateRequest,
)


class TestPersonaResponse:
    """Tests for PersonaResponse model."""

    def test_persona_response_creation_with_all_fields(self):
        """Test creating PersonaResponse with all fields."""
        persona = PersonaResponse(
            id="550e8400-e29b-41d4-a716-446655440000",
            name="Angry Customer",
            description="An aggressive customer persona",
            aggression=0.8,
            patience=0.2,
            verbosity=0.6,
            traits=["impatient", "demanding"],
            tts_provider="openai",
            tts_config={"model": "tts-1", "voice": "alloy"},
            preview_audio_url="https://example.com/audio/preview.mp3",
            preview_audio_text="Hello, this is how I sound.",
            metadata={"category": "customer"},
            created_at=datetime(2024, 1, 15, 10, 0, 0),
            updated_at=datetime(2024, 1, 15, 11, 0, 0),
            created_by="user@example.com",
            is_active=True,
        )

        assert persona.id == "550e8400-e29b-41d4-a716-446655440000"
        assert persona.name == "Angry Customer"
        assert persona.description == "An aggressive customer persona"
        assert persona.aggression == 0.8
        assert persona.patience == 0.2
        assert persona.verbosity == 0.6
        assert persona.traits == ["impatient", "demanding"]
        assert persona.tts_provider == "openai"
        assert persona.tts_config == {"model": "tts-1", "voice": "alloy"}
        assert persona.preview_audio_url == "https://example.com/audio/preview.mp3"
        assert persona.preview_audio_text == "Hello, this is how I sound."
        assert persona.metadata == {"category": "customer"}
        assert persona.is_active is True

    def test_persona_response_creation_with_minimal_fields(self):
        """Test creating PersonaResponse with minimal required fields."""
        persona = PersonaResponse(
            id="550e8400-e29b-41d4-a716-446655440000",
            name="Basic Persona",
            description=None,
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            traits=[],
            tts_provider="openai",
            tts_config={},
            preview_audio_url=None,
            preview_audio_text=None,
            metadata={},
            created_at=None,
            updated_at=None,
            created_by=None,
            is_active=True,
        )

        assert persona.id == "550e8400-e29b-41d4-a716-446655440000"
        assert persona.name == "Basic Persona"
        assert persona.description is None
        assert persona.aggression == 0.5
        assert persona.traits == []
        assert persona.tts_config == {}
        assert persona.preview_audio_url is None


class TestPersonaCreateRequest:
    """Tests for PersonaCreateRequest model with validation."""

    def test_persona_create_request_valid(self):
        """Test creating valid PersonaCreateRequest."""
        request = PersonaCreateRequest(
            name="Test Persona",
            description="A test persona",
            aggression=0.5,
            patience=0.7,
            verbosity=0.6,
            traits=["polite", "helpful"],
            tts_provider="openai",
            tts_config={"model": "tts-1", "voice": "nova"},
            metadata={"source": "test"},
            created_by="test@example.com",
        )

        assert request.name == "Test Persona"
        assert request.description == "A test persona"
        assert request.aggression == 0.5
        assert request.patience == 0.7
        assert request.verbosity == 0.6
        assert request.traits == ["polite", "helpful"]
        assert request.tts_provider == "openai"
        assert request.tts_config == {"model": "tts-1", "voice": "nova"}

    def test_persona_create_request_minimal(self):
        """Test creating PersonaCreateRequest with minimal fields."""
        request = PersonaCreateRequest(
            name="Minimal Persona",
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            tts_provider="elevenlabs",
        )

        assert request.name == "Minimal Persona"
        assert request.description is None
        assert request.traits == []
        assert request.tts_config == {}
        assert request.metadata == {}
        assert request.created_by is None

    def test_persona_create_request_aggression_validation_min(self):
        """Test aggression validation - below minimum."""
        with pytest.raises(ValidationError) as exc_info:
            PersonaCreateRequest(
                name="Test",
                aggression=-0.1,  # Invalid: below 0.0
                patience=0.5,
                verbosity=0.5,
                tts_provider="openai",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("aggression",) for e in errors)

    def test_persona_create_request_aggression_validation_max(self):
        """Test aggression validation - above maximum."""
        with pytest.raises(ValidationError) as exc_info:
            PersonaCreateRequest(
                name="Test",
                aggression=1.1,  # Invalid: above 1.0
                patience=0.5,
                verbosity=0.5,
                tts_provider="openai",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("aggression",) for e in errors)

    def test_persona_create_request_patience_validation_min(self):
        """Test patience validation - below minimum."""
        with pytest.raises(ValidationError) as exc_info:
            PersonaCreateRequest(
                name="Test",
                aggression=0.5,
                patience=-0.1,  # Invalid: below 0.0
                verbosity=0.5,
                tts_provider="openai",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("patience",) for e in errors)

    def test_persona_create_request_patience_validation_max(self):
        """Test patience validation - above maximum."""
        with pytest.raises(ValidationError) as exc_info:
            PersonaCreateRequest(
                name="Test",
                aggression=0.5,
                patience=1.1,  # Invalid: above 1.0
                verbosity=0.5,
                tts_provider="openai",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("patience",) for e in errors)

    def test_persona_create_request_verbosity_validation_min(self):
        """Test verbosity validation - below minimum."""
        with pytest.raises(ValidationError) as exc_info:
            PersonaCreateRequest(
                name="Test",
                aggression=0.5,
                patience=0.5,
                verbosity=-0.1,  # Invalid: below 0.0
                tts_provider="openai",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("verbosity",) for e in errors)

    def test_persona_create_request_verbosity_validation_max(self):
        """Test verbosity validation - above maximum."""
        with pytest.raises(ValidationError) as exc_info:
            PersonaCreateRequest(
                name="Test",
                aggression=0.5,
                patience=0.5,
                verbosity=1.1,  # Invalid: above 1.0
                tts_provider="openai",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("verbosity",) for e in errors)

    def test_persona_create_request_name_required(self):
        """Test name is required."""
        with pytest.raises(ValidationError) as exc_info:
            PersonaCreateRequest(
                aggression=0.5,
                patience=0.5,
                verbosity=0.5,
                tts_provider="openai",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("name",) for e in errors)

    def test_persona_create_request_name_min_length(self):
        """Test name minimum length validation."""
        with pytest.raises(ValidationError) as exc_info:
            PersonaCreateRequest(
                name="",  # Invalid: empty string
                aggression=0.5,
                patience=0.5,
                verbosity=0.5,
                tts_provider="openai",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("name",) for e in errors)

    def test_persona_create_request_name_max_length(self):
        """Test name maximum length validation."""
        with pytest.raises(ValidationError) as exc_info:
            PersonaCreateRequest(
                name="a" * 256,  # Invalid: 256 characters (max is 255)
                aggression=0.5,
                patience=0.5,
                verbosity=0.5,
                tts_provider="openai",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("name",) for e in errors)

    def test_persona_create_request_tts_provider_required(self):
        """Test tts_provider is required."""
        with pytest.raises(ValidationError) as exc_info:
            PersonaCreateRequest(
                name="Test",
                aggression=0.5,
                patience=0.5,
                verbosity=0.5,
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("tts_provider",) for e in errors)

    def test_persona_create_request_boundary_values(self):
        """Test boundary values for trait ranges."""
        # Test exact boundaries (should be valid)
        request = PersonaCreateRequest(
            name="Boundary Test",
            aggression=0.0,
            patience=1.0,
            verbosity=0.0,
            tts_provider="openai",
        )
        assert request.aggression == 0.0
        assert request.patience == 1.0
        assert request.verbosity == 0.0


class TestPersonaUpdateRequest:
    """Tests for PersonaUpdateRequest model."""

    def test_persona_update_request_all_fields(self):
        """Test PersonaUpdateRequest with all fields."""
        request = PersonaUpdateRequest(
            name="Updated Persona",
            description="Updated description",
            aggression=0.9,
            patience=0.1,
            verbosity=0.7,
            traits=["updated"],
            tts_provider="elevenlabs",
            tts_config={"voice_id": "abc123"},
            metadata={"updated": True},
        )

        assert request.name == "Updated Persona"
        assert request.description == "Updated description"
        assert request.aggression == 0.9
        assert request.patience == 0.1
        assert request.verbosity == 0.7
        assert request.traits == ["updated"]
        assert request.tts_provider == "elevenlabs"

    def test_persona_update_request_partial(self):
        """Test PersonaUpdateRequest with partial fields."""
        request = PersonaUpdateRequest(
            name="New Name",
            aggression=0.8,
        )

        assert request.name == "New Name"
        assert request.aggression == 0.8
        assert request.description is None
        assert request.patience is None
        assert request.verbosity is None
        assert request.traits is None
        assert request.tts_provider is None

    def test_persona_update_request_empty(self):
        """Test PersonaUpdateRequest with no fields (all optional)."""
        request = PersonaUpdateRequest()

        assert request.name is None
        assert request.description is None
        assert request.aggression is None
        assert request.patience is None
        assert request.verbosity is None
        assert request.traits is None
        assert request.tts_provider is None
        assert request.tts_config is None

    def test_persona_update_request_aggression_validation(self):
        """Test aggression validation in update request."""
        with pytest.raises(ValidationError) as exc_info:
            PersonaUpdateRequest(aggression=1.5)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("aggression",) for e in errors)

    def test_persona_update_request_patience_validation(self):
        """Test patience validation in update request."""
        with pytest.raises(ValidationError) as exc_info:
            PersonaUpdateRequest(patience=-0.5)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("patience",) for e in errors)

    def test_persona_update_request_verbosity_validation(self):
        """Test verbosity validation in update request."""
        with pytest.raises(ValidationError) as exc_info:
            PersonaUpdateRequest(verbosity=2.0)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("verbosity",) for e in errors)

    def test_persona_update_request_name_min_length(self):
        """Test name minimum length validation in update."""
        with pytest.raises(ValidationError) as exc_info:
            PersonaUpdateRequest(name="")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("name",) for e in errors)

    def test_persona_update_request_name_max_length(self):
        """Test name maximum length validation in update."""
        with pytest.raises(ValidationError) as exc_info:
            PersonaUpdateRequest(name="a" * 256)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("name",) for e in errors)


class TestPersonaListItem:
    """Tests for PersonaListItem model (simplified persona for lists)."""

    def test_persona_list_item_creation(self):
        """Test creating PersonaListItem with all fields."""
        item = PersonaListItem(
            id="550e8400-e29b-41d4-a716-446655440000",
            name="Angry Customer",
            description="An aggressive customer persona",
            aggression=0.8,
            patience=0.2,
            verbosity=0.6,
            traits=["impatient", "demanding"],
            preview_audio_url="https://example.com/audio/preview.mp3",
            preview_audio_text="Hello, this is how I sound.",
            is_active=True,
        )

        assert item.id == "550e8400-e29b-41d4-a716-446655440000"
        assert item.name == "Angry Customer"
        assert item.description == "An aggressive customer persona"
        assert item.aggression == 0.8
        assert item.patience == 0.2
        assert item.verbosity == 0.6
        assert item.traits == ["impatient", "demanding"]
        assert item.preview_audio_url == "https://example.com/audio/preview.mp3"
        assert item.preview_audio_text == "Hello, this is how I sound."
        assert item.is_active is True

    def test_persona_list_item_minimal(self):
        """Test PersonaListItem with minimal fields."""
        item = PersonaListItem(
            id="550e8400-e29b-41d4-a716-446655440000",
            name="Basic Persona",
            description=None,
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            traits=[],
            preview_audio_url=None,
            preview_audio_text=None,
            is_active=True,
        )

        assert item.id == "550e8400-e29b-41d4-a716-446655440000"
        assert item.name == "Basic Persona"
        assert item.description is None
        assert item.traits == []
        assert item.preview_audio_url is None

    def test_persona_list_item_excludes_sensitive_fields(self):
        """Test that PersonaListItem doesn't have sensitive fields."""
        item = PersonaListItem(
            id="id1",
            name="Test",
            description=None,
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            traits=[],
            preview_audio_url=None,
            preview_audio_text=None,
            is_active=True,
        )

        # Verify excluded fields are not present
        assert not hasattr(item, "tts_provider")
        assert not hasattr(item, "tts_config")
        assert not hasattr(item, "metadata")
        assert not hasattr(item, "created_at")
        assert not hasattr(item, "updated_at")
        assert not hasattr(item, "created_by")


class TestPersonasListResponse:
    """Tests for PersonasListResponse model."""

    def test_personas_list_response_with_personas(self):
        """Test PersonasListResponse with multiple personas."""
        persona1 = PersonaListItem(
            id="id1",
            name="Persona 1",
            description=None,
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            traits=[],
            preview_audio_url=None,
            preview_audio_text=None,
            is_active=True,
        )
        persona2 = PersonaListItem(
            id="id2",
            name="Persona 2",
            description=None,
            aggression=0.7,
            patience=0.3,
            verbosity=0.8,
            traits=["trait1"],
            preview_audio_url=None,
            preview_audio_text=None,
            is_active=True,
        )

        response = PersonasListResponse(
            count=2,
            personas=[persona1, persona2],
        )

        assert response.count == 2
        assert len(response.personas) == 2
        assert response.personas[0].name == "Persona 1"
        assert response.personas[1].name == "Persona 2"

    def test_personas_list_response_empty(self):
        """Test PersonasListResponse with no personas."""
        response = PersonasListResponse(
            count=0,
            personas=[],
        )

        assert response.count == 0
        assert response.personas == []


class TestPersonaAudioPreviewResponse:
    """Tests for PersonaAudioPreviewResponse model."""

    def test_persona_audio_preview_response_creation(self):
        """Test creating PersonaAudioPreviewResponse."""
        response = PersonaAudioPreviewResponse(
            audio_url="https://example.com/audio/preview.mp3",
            text="Hello, this is how I sound.",
            format="audio/mpeg",
        )

        assert response.audio_url == "https://example.com/audio/preview.mp3"
        assert response.text == "Hello, this is how I sound."
        assert response.format == "audio/mpeg"

    def test_persona_audio_preview_response_different_format(self):
        """Test PersonaAudioPreviewResponse with different audio format."""
        response = PersonaAudioPreviewResponse(
            audio_url="https://example.com/audio/preview.wav",
            text="Test preview text",
            format="audio/wav",
        )

        assert response.audio_url == "https://example.com/audio/preview.wav"
        assert response.text == "Test preview text"
        assert response.format == "audio/wav"


class TestUpdatedTestScenarioModels:
    """Tests for updated TestScenario models with persona_id."""

    def test_test_scenario_create_request_with_persona_id(self):
        """Test TestScenarioCreateRequest with required persona_id."""
        request = TestScenarioCreateRequest(
            suite_id="550e8400-e29b-41d4-a716-446655440000",
            name="Test Scenario",
            goal="Test goal",
            persona_id="550e8400-e29b-41d4-a716-446655440001",
            max_turns=10,
            timeout=300,
        )

        assert request.suite_id == "550e8400-e29b-41d4-a716-446655440000"
        assert request.name == "Test Scenario"
        assert request.goal == "Test goal"
        assert request.persona_id == "550e8400-e29b-41d4-a716-446655440001"
        assert request.max_turns == 10
        assert request.timeout == 300

    def test_test_scenario_create_request_persona_id_required(self):
        """Test that persona_id is required in TestScenarioCreateRequest."""
        with pytest.raises(ValidationError) as exc_info:
            TestScenarioCreateRequest(
                suite_id="550e8400-e29b-41d4-a716-446655440000",
                name="Test Scenario",
                goal="Test goal",
                # Missing persona_id
                max_turns=10,
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("persona_id",) for e in errors)

    def test_test_scenario_create_request_no_persona_json(self):
        """Test that persona_json is not accepted in TestScenarioCreateRequest."""
        # persona_json should not be in the model anymore
        request = TestScenarioCreateRequest(
            suite_id="550e8400-e29b-41d4-a716-446655440000",
            name="Test Scenario",
            goal="Test goal",
            persona_id="550e8400-e29b-41d4-a716-446655440001",
        )
        # Verify persona_json is not an attribute
        assert not hasattr(request, "persona_json")

    def test_test_scenario_update_request_with_persona_id(self):
        """Test TestScenarioUpdateRequest with persona_id."""
        request = TestScenarioUpdateRequest(
            name="Updated Name",
            persona_id="550e8400-e29b-41d4-a716-446655440002",
            max_turns=15,
        )

        assert request.name == "Updated Name"
        assert request.persona_id == "550e8400-e29b-41d4-a716-446655440002"
        assert request.max_turns == 15

    def test_test_scenario_update_request_persona_id_optional(self):
        """Test that persona_id is optional in TestScenarioUpdateRequest."""
        request = TestScenarioUpdateRequest(
            name="Updated Name",
            goal="Updated goal",
        )

        assert request.name == "Updated Name"
        assert request.goal == "Updated goal"
        assert request.persona_id is None

    def test_test_scenario_update_request_no_persona_json(self):
        """Test that persona_json is not in TestScenarioUpdateRequest."""
        request = TestScenarioUpdateRequest(
            persona_id="550e8400-e29b-41d4-a716-446655440001",
        )
        # Verify persona_json is not an attribute
        assert not hasattr(request, "persona_json")
