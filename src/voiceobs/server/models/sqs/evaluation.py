"""Message format for evaluation queue."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class EvaluationMessage(BaseModel):
    """Message body for test evaluation queue."""

    execution_id: str = Field(..., description="Test execution UUID to evaluate")

    @classmethod
    def create(cls, execution_id: UUID) -> EvaluationMessage:
        """Create message from execution UUID."""
        return cls(execution_id=str(execution_id))
