"""Trigger result model for execution orchestration."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class TriggerResult(BaseModel):
    """Result of triggering a suite or scenario run."""

    suite_run_id: UUID = Field(..., description="Test suite run UUID")
    total_scenarios: int = Field(..., description="Total number of scenarios in run")
