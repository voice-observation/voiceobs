"""Traits response models."""

from pydantic import BaseModel


class TraitVocabularyResponse(BaseModel):
    """Response model for trait vocabulary."""

    vocabulary: dict[str, list[str]]
