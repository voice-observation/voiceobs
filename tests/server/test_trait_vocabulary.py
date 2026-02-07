"""Tests for the trait vocabulary module."""

from voiceobs.server.services.scenario_generation.trait_vocabulary import (
    ALL_TRAITS,
    TRAIT_VOCABULARY,
)


class TestTraitVocabulary:
    """Tests for the trait vocabulary constants."""

    def test_trait_vocabulary_has_expected_categories(self):
        """Test that TRAIT_VOCABULARY has all expected categories."""
        expected_categories = {
            "emotional_state",
            "communication_style",
            "patience_level",
            "cooperation",
            "expertise",
        }
        assert set(TRAIT_VOCABULARY.keys()) == expected_categories

    def test_all_traits_is_flat_list_of_strings(self):
        """Test that ALL_TRAITS is a flat list of all traits."""
        assert isinstance(ALL_TRAITS, list)
        assert all(isinstance(t, str) for t in ALL_TRAITS)

    def test_all_traits_contains_traits_from_all_categories(self):
        """Test that ALL_TRAITS contains traits from every category."""
        for category, traits in TRAIT_VOCABULARY.items():
            for trait in traits:
                assert trait in ALL_TRAITS, f"{trait} from {category} not in ALL_TRAITS"

    def test_all_traits_has_no_duplicates(self):
        """Test that ALL_TRAITS has no duplicate entries."""
        assert len(ALL_TRAITS) == len(set(ALL_TRAITS))

    def test_emotional_state_contains_expected_traits(self):
        """Test that emotional_state category has expected traits."""
        expected = {
            "angry",
            "frustrated",
            "calm",
            "anxious",
            "cheerful",
            "neutral",
            "irritated",
            "nervous",
        }
        assert expected.issubset(set(TRAIT_VOCABULARY["emotional_state"]))

    def test_cooperation_contains_expected_traits(self):
        """Test that cooperation category has expected traits."""
        expected = {
            "cooperative",
            "uncooperative",
            "demanding",
            "agreeable",
            "difficult",
            "flexible",
        }
        assert expected.issubset(set(TRAIT_VOCABULARY["cooperation"]))
