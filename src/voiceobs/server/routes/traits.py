"""Trait vocabulary routes."""

from fastapi import APIRouter

from voiceobs.server.models.response import TraitVocabularyResponse
from voiceobs.server.services.scenario_generation.trait_vocabulary import TRAIT_VOCABULARY

router = APIRouter(prefix="/api/v1/traits", tags=["Traits"])


@router.get(
    "",
    response_model=TraitVocabularyResponse,
    summary="Get trait vocabulary",
    description="Get the available persona traits organized by category.",
)
async def get_trait_vocabulary() -> TraitVocabularyResponse:
    """Get the trait vocabulary for persona creation."""
    return TraitVocabularyResponse(vocabulary=TRAIT_VOCABULARY)
