"""Utility functions for the voiceobs server."""

from voiceobs.analyzer import AnalysisResult
from voiceobs.server.models import (
    AnalysisResponse,
    AnalysisSummary,
    EvalMetricsResponse,
    StageMetricsResponse,
    StagesResponse,
    TurnMetricsResponse,
)


def analysis_result_to_response(result: AnalysisResult) -> AnalysisResponse:
    """Convert an AnalysisResult to an AnalysisResponse.

    Args:
        result: The analysis result from the analyzer.

    Returns:
        The response model for the API.
    """
    return AnalysisResponse(
        summary=AnalysisSummary(
            total_spans=result.total_spans,
            total_conversations=result.total_conversations,
            total_turns=result.total_turns,
        ),
        stages=StagesResponse(
            asr=StageMetricsResponse(
                stage_type="asr",
                count=result.asr_metrics.count,
                mean_ms=result.asr_metrics.mean_ms,
                p50_ms=result.asr_metrics.p50_ms,
                p95_ms=result.asr_metrics.p95_ms,
                p99_ms=result.asr_metrics.p99_ms,
            ),
            llm=StageMetricsResponse(
                stage_type="llm",
                count=result.llm_metrics.count,
                mean_ms=result.llm_metrics.mean_ms,
                p50_ms=result.llm_metrics.p50_ms,
                p95_ms=result.llm_metrics.p95_ms,
                p99_ms=result.llm_metrics.p99_ms,
            ),
            tts=StageMetricsResponse(
                stage_type="tts",
                count=result.tts_metrics.count,
                mean_ms=result.tts_metrics.mean_ms,
                p50_ms=result.tts_metrics.p50_ms,
                p95_ms=result.tts_metrics.p95_ms,
                p99_ms=result.tts_metrics.p99_ms,
            ),
        ),
        turns=TurnMetricsResponse(
            silence_samples=len(result.turn_metrics.silence_after_user_ms),
            silence_mean_ms=result.turn_metrics.silence_mean_ms,
            silence_p95_ms=result.turn_metrics.silence_p95_ms,
            total_agent_turns=result.turn_metrics.total_agent_turns,
            interruptions=result.turn_metrics.interruptions,
            interruption_rate=result.turn_metrics.interruption_rate,
        ),
        eval=EvalMetricsResponse(
            total_evals=result.eval_metrics.total_evals,
            intent_correct_count=result.eval_metrics.intent_correct_count,
            intent_incorrect_count=result.eval_metrics.intent_incorrect_count,
            intent_correct_rate=result.eval_metrics.intent_correct_rate,
            intent_failure_rate=result.eval_metrics.intent_failure_rate,
            avg_relevance_score=result.eval_metrics.avg_relevance_score,
            min_relevance_score=result.eval_metrics.min_relevance_score,
            max_relevance_score=result.eval_metrics.max_relevance_score,
        ),
    )
