"""Tests for metrics utility functions."""

from voiceobs.server.db.repositories.metrics_utils import MetricsUtils


class TestMetricsUtils:
    """Tests for MetricsUtils class."""

    def test_parse_window_hour(self):
        """Test parsing hour window."""
        value, unit = MetricsUtils.parse_window("1h")
        assert value == 1
        assert unit == "h"

    def test_parse_window_day(self):
        """Test parsing day window."""
        value, unit = MetricsUtils.parse_window("2d")
        assert value == 2
        assert unit == "d"

    def test_parse_window_week(self):
        """Test parsing week window."""
        value, unit = MetricsUtils.parse_window("1w")
        assert value == 1
        assert unit == "w"

    def test_parse_window_multiple_hours(self):
        """Test parsing multiple hour window."""
        value, unit = MetricsUtils.parse_window("24h")
        assert value == 24
        assert unit == "h"

    def test_parse_window_invalid_defaults(self):
        """Test parsing invalid window takes last character as unit."""
        value, unit = MetricsUtils.parse_window("invalid")
        assert value == 1  # "invalid"[:-1] = "invali" which is not a digit, so defaults to 1
        assert unit == "d"  # Last character of "invalid" is "d"

    def test_parse_window_empty_string(self):
        """Test parsing empty string defaults to 1h."""
        value, unit = MetricsUtils.parse_window("")
        assert value == 1
        assert unit == "h"

    def test_get_time_truncation_hour(self):
        """Test getting time truncation for hour."""
        trunc, fmt = MetricsUtils.get_time_truncation("h")
        assert "date_trunc('hour'" in trunc
        assert 'HH24:00:00"Z"' in fmt

    def test_get_time_truncation_day(self):
        """Test getting time truncation for day."""
        trunc, fmt = MetricsUtils.get_time_truncation("d")
        assert "date_trunc('day'" in trunc
        assert '00:00:00"Z"' in fmt

    def test_get_time_truncation_week(self):
        """Test getting time truncation for week."""
        trunc, fmt = MetricsUtils.get_time_truncation("w")
        assert "date_trunc('week'" in trunc
        assert '00:00:00"Z"' in fmt

    def test_get_time_truncation_invalid_defaults(self):
        """Test getting time truncation for invalid unit defaults to hour."""
        trunc, fmt = MetricsUtils.get_time_truncation("x")
        assert "date_trunc('hour'" in trunc
        assert 'HH24:00:00"Z"' in fmt

    def test_get_conversation_volume_truncation_hour(self):
        """Test getting conversation volume truncation for hour."""
        trunc, fmt = MetricsUtils.get_conversation_volume_truncation("hour")
        assert "date_trunc('hour', c.created_at)" in trunc
        assert 'HH24:00:00"Z"' in fmt

    def test_get_conversation_volume_truncation_day(self):
        """Test getting conversation volume truncation for day."""
        trunc, fmt = MetricsUtils.get_conversation_volume_truncation("day")
        assert "date_trunc('day', c.created_at)" in trunc
        assert '00:00:00"Z"' in fmt

    def test_get_conversation_volume_truncation_week(self):
        """Test getting conversation volume truncation for week."""
        trunc, fmt = MetricsUtils.get_conversation_volume_truncation("week")
        assert "date_trunc('week', c.created_at)" in trunc
        assert '00:00:00"Z"' in fmt

    def test_get_conversation_volume_truncation_invalid_defaults(self):
        """Test getting conversation volume truncation for invalid defaults to hour."""
        trunc, fmt = MetricsUtils.get_conversation_volume_truncation("invalid")
        assert "date_trunc('hour', c.created_at)" in trunc
        assert 'HH24:00:00"Z"' in fmt
