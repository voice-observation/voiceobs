"""Criterion result model for evaluation."""

from pydantic import BaseModel, Field


class CriterionResult(BaseModel):
    """Result for a single evaluation criterion."""

    name: str = Field(..., description="Criterion name (e.g., 'greeting', 'tone')")
    passed: bool = Field(..., description="Whether this criterion passed")
    score: float = Field(..., ge=0.0, le=1.0, description="Score for this criterion")
    evidence: str = Field(..., description="Transcript quote supporting judgment")
