"""Tests for server utility functions."""

from datetime import datetime, timezone

from voiceobs.server.utils import parse_iso_datetime


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
