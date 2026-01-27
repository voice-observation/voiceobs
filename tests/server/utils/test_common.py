"""Tests for server utility functions."""

import logging
import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from fastapi import HTTPException

from voiceobs.server.utils import parse_iso_datetime
from voiceobs.server.utils.common import (
    analysis_result_to_response,
    log_timing,
    parse_uuid,
    safe_cleanup,
)


class TestParseIsoDatetime:
    """Tests for parse_iso_datetime function."""

    def test_parse_iso_datetime_with_z_suffix(self):
        """Test parsing ISO datetime string with Z suffix."""
        dt_str = "2024-01-15T10:30:00Z"
        result = parse_iso_datetime(dt_str)

        assert result is not None
        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30
        assert result.second == 0
        assert result.tzinfo == timezone.utc

    def test_parse_iso_datetime_with_timezone_offset(self):
        """Test parsing ISO datetime string with timezone offset."""
        dt_str = "2024-01-15T10:30:00+05:00"
        result = parse_iso_datetime(dt_str)

        assert result is not None
        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30

    def test_parse_iso_datetime_without_timezone(self):
        """Test parsing ISO datetime string without timezone."""
        dt_str = "2024-01-15T10:30:00"
        result = parse_iso_datetime(dt_str)

        assert result is not None
        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30

    def test_parse_iso_datetime_with_microseconds(self):
        """Test parsing ISO datetime string with microseconds."""
        dt_str = "2024-01-15T10:30:00.123456Z"
        result = parse_iso_datetime(dt_str)

        assert result is not None
        assert isinstance(result, datetime)
        assert result.microsecond == 123456

    def test_parse_iso_datetime_invalid_format(self):
        """Test parsing invalid datetime string returns None."""
        dt_str = "not-a-datetime"
        result = parse_iso_datetime(dt_str)

        assert result is None

    def test_parse_iso_datetime_empty_string(self):
        """Test parsing empty string returns None."""
        dt_str = ""
        result = parse_iso_datetime(dt_str)

        assert result is None

    def test_parse_iso_datetime_none_input(self):
        """Test parsing None input returns None."""
        result = parse_iso_datetime(None)  # type: ignore[arg-type]

        assert result is None

    def test_parse_iso_datetime_non_string_input(self):
        """Test parsing non-string input returns None."""
        result = parse_iso_datetime(12345)  # type: ignore[arg-type]

        assert result is None

    def test_parse_iso_datetime_malformed_date(self):
        """Test parsing malformed date string returns None."""
        dt_str = "2024-13-45T25:70:99Z"
        result = parse_iso_datetime(dt_str)

        assert result is None

    def test_parse_iso_datetime_partial_string(self):
        """Test parsing partial datetime string (date only)."""
        dt_str = "2024-01-15"
        result = parse_iso_datetime(dt_str)

        # fromisoformat can parse date-only strings, so this should succeed
        assert result is not None
        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_parse_iso_datetime_negative_timezone(self):
        """Test parsing ISO datetime with negative timezone offset."""
        dt_str = "2024-01-15T10:30:00-05:00"
        result = parse_iso_datetime(dt_str)

        assert result is not None
        assert isinstance(result, datetime)
        assert result.year == 2024

    def test_parse_iso_datetime_utc_equivalent(self):
        """Test that Z suffix and +00:00 are equivalent."""
        dt_str_z = "2024-01-15T10:30:00Z"
        dt_str_utc = "2024-01-15T10:30:00+00:00"

        result_z = parse_iso_datetime(dt_str_z)
        result_utc = parse_iso_datetime(dt_str_utc)

        assert result_z is not None
        assert result_utc is not None
        # Both should represent the same moment in time
        assert result_z == result_utc


class TestLogTiming:
    """Tests for log_timing context manager."""

    def test_logs_operation_timing(self, caplog):
        """Should log operation with duration."""
        logger = logging.getLogger("test_timing")
        with caplog.at_level(logging.INFO):
            with log_timing(logger, "Test operation"):
                time.sleep(0.01)  # 10ms

        assert len(caplog.records) == 1
        assert "Test operation took" in caplog.records[0].message
        assert "s" in caplog.records[0].message

    def test_timing_is_accurate(self, caplog):
        """Logged timing should be approximately correct."""
        logger = logging.getLogger("test_timing")
        with caplog.at_level(logging.INFO):
            with log_timing(logger, "Sleep operation"):
                time.sleep(0.05)  # 50ms

        # Extract the timing from the log message
        message = caplog.records[0].message
        # Format: "Sleep operation took 0.050s"
        timing_str = message.split("took ")[1].rstrip("s")
        timing = float(timing_str)
        assert 0.04 <= timing <= 0.15  # Allow some tolerance

    def test_context_manager_yields(self):
        """Context manager should yield without blocking."""
        logger = logging.getLogger("test_timing")
        result = None
        with log_timing(logger, "Test"):
            result = 42
        assert result == 42

    def test_logs_on_exception(self, caplog):
        """Should still log timing even if exception occurs."""
        logger = logging.getLogger("test_timing")
        with caplog.at_level(logging.INFO):
            with pytest.raises(ValueError):
                with log_timing(logger, "Failing operation"):
                    raise ValueError("Test error")

        # Should still have logged the timing
        assert len(caplog.records) == 1
        assert "Failing operation took" in caplog.records[0].message


class TestSafeCleanup:
    """Tests for safe_cleanup async helper."""

    @pytest.mark.asyncio
    async def test_calls_aclose_on_objects(self):
        """Should call aclose() on objects that have it."""
        mock_obj = AsyncMock()
        mock_obj.aclose = AsyncMock()

        await safe_cleanup(mock_obj)

        mock_obj.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_calls_disconnect_on_objects(self):
        """Should call disconnect() on objects that have it."""
        mock_obj = MagicMock()
        mock_obj.disconnect = AsyncMock()
        # Remove aclose to test disconnect path
        del mock_obj.aclose

        await safe_cleanup(mock_obj)

        mock_obj.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_calls_close_on_objects(self):
        """Should call close() on objects that have it."""
        mock_obj = MagicMock()
        mock_obj.close = AsyncMock()
        # Remove aclose and disconnect to test close path
        del mock_obj.aclose
        del mock_obj.disconnect

        await safe_cleanup(mock_obj)

        mock_obj.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_none_values(self):
        """Should skip None values without error."""
        mock_obj = AsyncMock()
        mock_obj.aclose = AsyncMock()

        # Should not raise
        await safe_cleanup(None, mock_obj, None)

        mock_obj.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_multiple_objects(self):
        """Should close multiple objects."""
        mock1 = AsyncMock()
        mock1.aclose = AsyncMock()
        mock2 = AsyncMock()
        mock2.aclose = AsyncMock()

        await safe_cleanup(mock1, mock2)

        mock1.aclose.assert_called_once()
        mock2.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_continues_on_error(self):
        """Should continue closing other objects even if one fails."""
        mock1 = AsyncMock()
        mock1.aclose = AsyncMock(side_effect=Exception("Test error"))
        mock2 = AsyncMock()
        mock2.aclose = AsyncMock()

        # Should not raise
        await safe_cleanup(mock1, mock2)

        mock1.aclose.assert_called_once()
        mock2.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_logs_errors_when_logger_provided(self, caplog):
        """Should log errors when logger is provided."""
        mock_obj = AsyncMock()
        mock_obj.aclose = AsyncMock(side_effect=Exception("Test error"))
        logger = logging.getLogger("test_cleanup")

        with caplog.at_level(logging.DEBUG):
            await safe_cleanup(mock_obj, logger=logger)

        assert any("Cleanup error" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_skips_objects_without_close_methods(self):
        """Should skip objects without any close method."""
        mock_obj = MagicMock(spec=[])  # No methods

        # Should not raise
        await safe_cleanup(mock_obj)


class TestParseUUID:
    """Tests for parse_uuid function."""

    def test_valid_uuid(self):
        """Should return UUID for valid UUID string."""
        uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        result = parse_uuid(uuid_str, "test")
        assert isinstance(result, UUID)
        assert str(result) == uuid_str

    def test_valid_uuid_uppercase(self):
        """Should handle uppercase UUID strings."""
        uuid_str = "550E8400-E29B-41D4-A716-446655440000"
        result = parse_uuid(uuid_str, "test")
        assert isinstance(result, UUID)

    def test_invalid_uuid_raises_http_exception(self):
        """Should raise HTTPException for invalid UUID string."""
        with pytest.raises(HTTPException) as exc_info:
            parse_uuid("invalid-uuid", "conversation")

        assert exc_info.value.status_code == 400
        assert "Invalid conversation ID format" in exc_info.value.detail

    def test_empty_string_raises_http_exception(self):
        """Should raise HTTPException for empty string."""
        with pytest.raises(HTTPException) as exc_info:
            parse_uuid("", "span")

        assert exc_info.value.status_code == 400
        assert "Invalid span ID format" in exc_info.value.detail

    def test_partial_uuid_raises_http_exception(self):
        """Should raise HTTPException for partial UUID."""
        with pytest.raises(HTTPException) as exc_info:
            parse_uuid("550e8400-e29b", "turn")

        assert exc_info.value.status_code == 400


class TestAnalysisResultToResponse:
    """Tests for analysis_result_to_response function."""

    def test_converts_result_to_response(self):
        """Should convert AnalysisResult to AnalysisResponse."""
        from voiceobs.analyzer import AnalysisResult, EvalMetrics, StageMetrics, TurnMetrics
        from voiceobs.server.models.response.analysis import AnalysisResponse

        # Create StageMetrics with durations (count is computed from len(durations_ms))
        asr_metrics = StageMetrics("asr")
        asr_metrics.durations_ms = [90.0, 100.0, 110.0]  # 3 spans

        llm_metrics = StageMetrics("llm")
        llm_metrics.durations_ms = [180.0, 200.0, 220.0, 240.0]  # 4 spans

        tts_metrics = StageMetrics("tts")
        tts_metrics.durations_ms = [140.0, 150.0, 160.0]  # 3 spans

        # Create TurnMetrics
        turn_metrics = TurnMetrics()
        turn_metrics.silence_after_user_ms = [100.0, 200.0, 150.0]
        turn_metrics.total_agent_turns = 25
        turn_metrics.interruptions = 3

        # Create EvalMetrics
        eval_metrics = EvalMetrics()
        eval_metrics.total_evals = 20
        eval_metrics.intent_correct_count = 15
        eval_metrics.intent_incorrect_count = 5

        # Create AnalysisResult
        result = AnalysisResult(
            total_spans=100,
            total_conversations=10,
            total_turns=50,
            asr_metrics=asr_metrics,
            llm_metrics=llm_metrics,
            tts_metrics=tts_metrics,
            turn_metrics=turn_metrics,
            eval_metrics=eval_metrics,
        )

        response = analysis_result_to_response(result)

        assert isinstance(response, AnalysisResponse)
        assert response.summary.total_spans == 100
        assert response.summary.total_conversations == 10
        assert response.summary.total_turns == 50
        assert response.stages.asr.count == 3
        assert response.stages.llm.count == 4
        assert response.stages.tts.count == 3
        assert response.turns.silence_samples == 3
        assert response.turns.interruptions == 3
        assert response.eval.total_evals == 20
