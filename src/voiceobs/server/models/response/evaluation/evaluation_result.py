"""Evaluation result model for LLM-based test evaluation."""

from pydantic import BaseModel, Field

from voiceobs.server.models.response.evaluation.criterion_result import CriterionResult


class EvaluationResult(BaseModel):
    """Full evaluation result from LLM."""

    passed: bool = Field(..., description="Overall pass/fail")
    score: float = Field(..., ge=0.0, le=1.0, description="Overall score")
    goal_achieved: bool = Field(..., description="Did agent fulfill scenario goal?")
    intent_handled: bool = Field(..., description="Did agent handle the intent?")
    criteria: list[CriterionResult] = Field(..., description="Per-criterion breakdown")
    reasoning: str = Field(..., description="LLM explanation of evaluation")
