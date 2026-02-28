"""Message format for execution queue."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class ExecutionMessage(BaseModel):
    """Message body for test execution queue."""

    execution_id: str = Field(..., description="Test execution UUID")

    @classmethod
    def create(cls, execution_id: UUID) -> ExecutionMessage:
        """Create message from execution UUID."""
        return cls(execution_id=str(execution_id))
