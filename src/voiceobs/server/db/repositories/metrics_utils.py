"""Utility functions for metrics repository."""


class MetricsUtils:
    """Utility class for metrics-related operations."""

    @staticmethod
    def parse_window(window: str) -> tuple[int, str]:
        """Parse window string into value and unit.

        Args:
            window: Time window string (e.g., '1h', '2d', '1w').

        Returns:
            Tuple of (window_value, window_unit).
        """
        window_value = int(window[:-1]) if window[:-1].isdigit() else 1
        window_unit = window[-1] if len(window) > 0 else "h"
        return window_value, window_unit

    @staticmethod
    def get_time_truncation(window_unit: str) -> tuple[str, str]:
        """Get time truncation SQL and format string based on window unit.

        Args:
            window_unit: Time unit ('h', 'd', 'w').

        Returns:
            Tuple of (time_trunc_sql, time_format).
        """
        if window_unit == "h":
            return "date_trunc('hour', time_col)", 'YYYY-MM-DD"T"HH24:00:00"Z"'
        elif window_unit == "d":
            return "date_trunc('day', time_col)", 'YYYY-MM-DD"T"00:00:00"Z"'
        elif window_unit == "w":
            return "date_trunc('week', time_col)", 'YYYY-MM-DD"T"00:00:00"Z"'
        else:
            return "date_trunc('hour', time_col)", 'YYYY-MM-DD"T"HH24:00:00"Z"'

    @staticmethod
    def get_conversation_volume_truncation(group_by: str) -> tuple[str, str]:
        """Get time truncation SQL and format string for conversation volume.

        Args:
            group_by: Time grouping ('hour', 'day', 'week').

        Returns:
            Tuple of (time_trunc_sql, time_format).
        """
        if group_by == "hour":
            return "date_trunc('hour', c.created_at)", 'YYYY-MM-DD"T"HH24:00:00"Z"'
        elif group_by == "day":
            return "date_trunc('day', c.created_at)", 'YYYY-MM-DD"T"00:00:00"Z"'
        elif group_by == "week":
            return "date_trunc('week', c.created_at)", 'YYYY-MM-DD"T"00:00:00"Z"'
        else:
            return "date_trunc('hour', c.created_at)", 'YYYY-MM-DD"T"HH24:00:00"Z"'
