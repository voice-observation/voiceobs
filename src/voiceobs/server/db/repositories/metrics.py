"""Metrics repository for aggregated metrics queries."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from voiceobs.server.db.connection import Database
from voiceobs.server.db.repositories.metrics_utils import MetricsUtils


class MetricsRepository:
    """Repository for metrics aggregation operations."""

    def __init__(self, db: Database) -> None:
        """Initialize the metrics repository.

        Args:
            db: Database connection manager.
        """
        self._db = db

    def _build_time_filter(
        self,
        start_time: datetime | None,
        end_time: datetime | None,
        conditions: list[str],
        params: list[Any],
        param_idx: int,
        time_column: str = "created_at",
    ) -> int:
        """Build time range filter conditions.

        Args:
            start_time: Start time threshold.
            end_time: End time threshold.
            conditions: List of SQL conditions to append to.
            params: List of SQL parameters to append to.
            param_idx: Current parameter index.
            time_column: Column name to filter on.

        Returns:
            Next parameter index.
        """
        if start_time:
            conditions.append(f"{time_column} >= ${param_idx}")
            params.append(start_time)
            param_idx += 1

        if end_time:
            conditions.append(f"{time_column} <= ${param_idx}")
            params.append(end_time)
            param_idx += 1

        return param_idx

    def _build_conversation_filter(
        self,
        conversation_id: str | None,
        conditions: list[str],
        params: list[Any],
        param_idx: int,
    ) -> int:
        """Build conversation ID filter condition.

        Args:
            conversation_id: Conversation ID to filter by.
            conditions: List of SQL conditions to append to.
            params: List of SQL parameters to append to.
            param_idx: Current parameter index.

        Returns:
            Next parameter index.
        """
        if conversation_id:
            conditions.append(f"c.conversation_id = ${param_idx}")
            params.append(conversation_id)
            param_idx += 1

        return param_idx

    async def get_summary(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        conversation_id: str | None = None,
    ) -> dict[str, Any]:
        """Get overall metrics summary.

        Args:
            start_time: Filter by start time.
            end_time: Filter by end time.
            conversation_id: Filter by conversation ID.

        Returns:
            Dictionary with summary metrics.
        """
        conditions: list[str] = []
        params: list[Any] = []
        param_idx = 1

        # Build filters
        if conversation_id:
            param_idx = self._build_conversation_filter(
                conversation_id, conditions, params, param_idx
            )

        if start_time or end_time:
            param_idx = self._build_time_filter(
                start_time, end_time, conditions, params, param_idx, "s.start_time"
            )

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        query = f"""
        SELECT
            COUNT(DISTINCT c.id) as total_conversations,
            COUNT(DISTINCT t.id) as total_turns,
            SUM(COALESCE(s.duration_ms, 0)) as total_duration_ms,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY s.duration_ms) as p50_latency,
            PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY s.duration_ms) as p95_latency,
            PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY s.duration_ms) as p99_latency,
            COUNT(DISTINCT f.id) as total_failures,
            AVG(CASE WHEN s.attributes->>'voice.silence.duration_ms' IS NOT NULL
                THEN (s.attributes->>'voice.silence.duration_ms')::float END) as silence_mean_ms,
            COUNT(
                CASE WHEN s.attributes->>'voice.overlap.detected' = 'true' THEN 1 END
            ) as overlap_count
        FROM conversations c
        LEFT JOIN spans s ON s.conversation_id = c.id
        LEFT JOIN turns t ON t.conversation_id = c.id
        LEFT JOIN failures f ON f.conversation_id = c.id
        {where_clause}
        """

        row = await self._db.fetchrow(query, *params)

        if row is None:
            return {
                "total_conversations": 0,
                "total_turns": 0,
                "total_duration_ms": None,
                "avg_latency_p50_ms": None,
                "avg_latency_p95_ms": None,
                "avg_latency_p99_ms": None,
                "failure_rate": None,
                "total_failures": 0,
                "silence_mean_ms": None,
                "overlap_count": 0,
            }

        total_conversations = row["total_conversations"] or 0
        total_failures = row["total_failures"] or 0
        failure_rate = (
            (total_failures / total_conversations * 100) if total_conversations > 0 else None
        )

        return {
            "total_conversations": total_conversations,
            "total_turns": row["total_turns"] or 0,
            "total_duration_ms": (
                float(row["total_duration_ms"]) if row["total_duration_ms"] else None
            ),
            "avg_latency_p50_ms": float(row["p50_latency"]) if row["p50_latency"] else None,
            "avg_latency_p95_ms": float(row["p95_latency"]) if row["p95_latency"] else None,
            "avg_latency_p99_ms": float(row["p99_latency"]) if row["p99_latency"] else None,
            "failure_rate": failure_rate,
            "total_failures": total_failures,
            "silence_mean_ms": float(row["silence_mean_ms"]) if row["silence_mean_ms"] else None,
            "overlap_count": row["overlap_count"] or 0,
        }

    async def get_latency_breakdown(
        self,
        group_by: str = "stage",
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        conversation_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get latency breakdown grouped by specified field.

        Args:
            group_by: Group by field ('stage' or other span attribute).
            start_time: Filter by start time.
            end_time: Filter by end time.
            conversation_id: Filter by conversation ID.

        Returns:
            List of breakdown items.
        """
        conditions: list[str] = []
        params: list[Any] = []
        param_idx = 1

        # Build filters
        if conversation_id:
            param_idx = self._build_conversation_filter(
                conversation_id, conditions, params, param_idx
            )

        if start_time or end_time:
            param_idx = self._build_time_filter(
                start_time, end_time, conditions, params, param_idx, "s.start_time"
            )

        # Build WHERE clause
        where_conditions = []
        if conditions:
            where_conditions.extend(conditions)
        where_conditions.append("s.duration_ms IS NOT NULL")

        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)

        # Determine grouping column
        if group_by == "stage":
            group_expr = "COALESCE(s.attributes->>'voice.stage.type', 'unknown')"
        else:
            # Group by custom attribute
            group_expr = f"COALESCE(s.attributes->>'{group_by}', 'unknown')"

        query = f"""
        SELECT
            {group_expr} as group_name,
            COUNT(*) as count,
            AVG(s.duration_ms) as mean_ms,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY s.duration_ms) as p50_ms,
            PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY s.duration_ms) as p95_ms,
            PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY s.duration_ms) as p99_ms
        FROM spans s
        LEFT JOIN conversations c ON s.conversation_id = c.id
        {where_clause}
        GROUP BY {group_expr}
        ORDER BY count DESC
        """

        rows = await self._db.fetch(query, *params)

        return [
            {
                "group": row["group_name"],
                "count": row["count"],
                "mean_ms": float(row["mean_ms"]) if row["mean_ms"] else None,
                "p50_ms": float(row["p50_ms"]) if row["p50_ms"] else None,
                "p95_ms": float(row["p95_ms"]) if row["p95_ms"] else None,
                "p99_ms": float(row["p99_ms"]) if row["p99_ms"] else None,
            }
            for row in rows
        ]

    async def get_failure_breakdown(
        self,
        group_by: str = "type",
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        conversation_id: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """Get failure breakdown grouped by specified field.

        Args:
            group_by: Group by field ('type' or 'severity').
            start_time: Filter by start time.
            end_time: Filter by end time.
            conversation_id: Filter by conversation ID.

        Returns:
            Tuple of (list of breakdown items, total count).
        """
        conditions: list[str] = []
        params: list[Any] = []
        param_idx = 1

        # Build filters
        if conversation_id:
            conditions.append(f"c.conversation_id = ${param_idx}")
            params.append(conversation_id)
            param_idx += 1

        if start_time or end_time:
            param_idx = self._build_time_filter(
                start_time, end_time, conditions, params, param_idx, "f.created_at"
            )

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        group_expr = self._get_failure_grouping_column(group_by)

        query = f"""
        SELECT
            {group_expr} as group_name,
            COUNT(*) as count
        FROM failures f
        LEFT JOIN conversations c ON f.conversation_id = c.id
        {where_clause}
        GROUP BY {group_expr}
        ORDER BY count DESC
        """

        rows = await self._db.fetch(query, *params)

        total = await self._get_failure_total_count(where_clause, params)

        breakdown = []
        for row in rows:
            count = row["count"]
            percentage = (count / total * 100) if total > 0 else None
            breakdown.append(
                {
                    "group": row["group_name"],
                    "count": count,
                    "percentage": float(percentage) if percentage is not None else None,
                }
            )

        return breakdown, total

    async def get_conversation_volume(
        self,
        group_by: str = "hour",
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        conversation_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get conversation volume over time.

        Args:
            group_by: Time grouping ('hour', 'day', 'week').
            start_time: Filter by start time.
            end_time: Filter by end time.
            conversation_id: Filter by conversation ID.

        Returns:
            List of volume items.
        """
        conditions: list[str] = []
        params: list[Any] = []
        param_idx = 1

        # Build filters
        if conversation_id:
            conditions.append(f"c.conversation_id = ${param_idx}")
            params.append(conversation_id)
            param_idx += 1

        if start_time or end_time:
            param_idx = self._build_time_filter(
                start_time, end_time, conditions, params, param_idx, "c.created_at"
            )

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        time_trunc, time_format = MetricsUtils.get_conversation_volume_truncation(group_by)

        query = f"""
        SELECT
            to_char({time_trunc}, '{time_format}') as time_bucket,
            COUNT(*) as count
        FROM conversations c
        {where_clause}
        GROUP BY {time_trunc}
        ORDER BY {time_trunc}
        """

        rows = await self._db.fetch(query, *params)

        return [
            {
                "time_bucket": row["time_bucket"],
                "count": row["count"],
            }
            for row in rows
        ]

    def _get_failure_grouping_column(self, group_by: str) -> str:
        """Get SQL expression for failure grouping column.

        Args:
            group_by: Group by field ('type' or 'severity').

        Returns:
            SQL expression for grouping.
        """
        if group_by == "type":
            return "f.failure_type"
        elif group_by == "severity":
            return "f.severity"
        else:
            return "f.failure_type"

    async def _get_failure_total_count(self, where_clause: str, params: list[Any]) -> int:
        """Get total failure count for breakdown percentage calculation.

        Args:
            where_clause: WHERE clause string.
            params: SQL parameters.

        Returns:
            Total count of failures.
        """
        total_query = f"""
        SELECT COUNT(*) as total
        FROM failures f
        LEFT JOIN conversations c ON f.conversation_id = c.id
        {where_clause}
        """
        total_row = await self._db.fetchrow(total_query, *params)
        return total_row["total"] or 0 if total_row else 0

    def _build_trend_filters(
        self,
        conversation_id: str | None,
        start_time: datetime | None,
        end_time: datetime | None,
        time_column: str,
        conditions: list[str],
        params: list[Any],
        param_idx: int,
    ) -> int:
        """Build filter conditions for trends query.

        Args:
            conversation_id: Conversation ID filter.
            start_time: Start time filter.
            end_time: End time filter.
            time_column: Column name for time filtering.
            conditions: List of SQL conditions to append to.
            params: List of SQL parameters to append to.
            param_idx: Current parameter index.

        Returns:
            Next parameter index.
        """
        if conversation_id:
            conditions.append(f"c.conversation_id = ${param_idx}")
            params.append(conversation_id)
            param_idx += 1

        if start_time or end_time:
            param_idx = self._build_time_filter(
                start_time, end_time, conditions, params, param_idx, time_column
            )

        return param_idx

    def _build_latency_trend_query(
        self,
        time_trunc: str,
        time_format: str,
        window_value: int,
        where_clause: str,
    ) -> str:
        """Build SQL query for latency trends.

        Args:
            time_trunc: Time truncation SQL expression.
            time_format: Time format string.
            window_value: Window size for rolling average.
            where_clause: WHERE clause string.

        Returns:
            SQL query string.
        """
        time_trunc_s = time_trunc.replace("time_col", "s.start_time")
        return f"""
        SELECT
            to_char({time_trunc_s}, '{time_format}') as timestamp,
            AVG(s.duration_ms) as value,
            AVG(AVG(s.duration_ms)) OVER (
                ORDER BY {time_trunc_s}
                ROWS BETWEEN {window_value} PRECEDING AND CURRENT ROW
            ) as rolling_avg
        FROM spans s
        LEFT JOIN conversations c ON s.conversation_id = c.id
        {where_clause}
        GROUP BY {time_trunc_s}
        ORDER BY {time_trunc_s}
        """

    def _build_failures_trend_query(
        self,
        time_trunc: str,
        time_format: str,
        window_value: int,
        where_clause: str,
    ) -> str:
        """Build SQL query for failures trends.

        Args:
            time_trunc: Time truncation SQL expression.
            time_format: Time format string.
            window_value: Window size for rolling average.
            where_clause: WHERE clause string.

        Returns:
            SQL query string.
        """
        time_trunc_f = time_trunc.replace("time_col", "f.created_at")
        return f"""
        SELECT
            to_char({time_trunc_f}, '{time_format}') as timestamp,
            COUNT(*)::float as value,
            AVG(COUNT(*)) OVER (
                ORDER BY {time_trunc_f}
                ROWS BETWEEN {window_value} PRECEDING AND CURRENT ROW
            ) as rolling_avg
        FROM failures f
        LEFT JOIN conversations c ON f.conversation_id = c.id
        {where_clause}
        GROUP BY {time_trunc_f}
        ORDER BY {time_trunc_f}
        """

    def _build_conversations_trend_query(
        self,
        time_trunc: str,
        time_format: str,
        window_value: int,
        where_clause: str,
    ) -> str:
        """Build SQL query for conversations trends.

        Args:
            time_trunc: Time truncation SQL expression.
            time_format: Time format string.
            window_value: Window size for rolling average.
            where_clause: WHERE clause string.

        Returns:
            SQL query string.
        """
        time_trunc_c = time_trunc.replace("time_col", "c.created_at")
        return f"""
        SELECT
            to_char({time_trunc_c}, '{time_format}') as timestamp,
            COUNT(*)::float as value,
            AVG(COUNT(*)) OVER (
                ORDER BY {time_trunc_c}
                ROWS BETWEEN {window_value} PRECEDING AND CURRENT ROW
            ) as rolling_avg
        FROM conversations c
        {where_clause}
        GROUP BY {time_trunc_c}
        ORDER BY {time_trunc_c}
        """

    async def get_trends(
        self,
        metric: str = "latency",
        window: str = "1h",
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        conversation_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get time-series trends for a metric.

        Args:
            metric: Metric name ('latency', 'failures', 'conversations').
            window: Time window ('1h', '1d', '1w').
            start_time: Filter by start time.
            end_time: Filter by end time.
            conversation_id: Filter by conversation ID.

        Returns:
            List of trend data points.
        """
        conditions: list[str] = []
        params: list[Any] = []
        param_idx = 1

        # Parse window and get time truncation
        window_value, window_unit = MetricsUtils.parse_window(window)
        time_trunc, time_format = MetricsUtils.get_time_truncation(window_unit)

        # Build query based on metric
        if metric == "latency":
            param_idx = self._build_trend_filters(
                conversation_id, start_time, end_time, "s.start_time", conditions, params, param_idx
            )

            where_clause = ""
            if conditions:
                where_clause = (
                    "WHERE " + " AND ".join(conditions) + " AND s.duration_ms IS NOT NULL"
                )
            else:
                where_clause = "WHERE s.duration_ms IS NOT NULL"

            query = self._build_latency_trend_query(
                time_trunc, time_format, window_value, where_clause
            )

        elif metric == "failures":
            param_idx = self._build_trend_filters(
                conversation_id,
                start_time,
                end_time,
                "f.created_at",
                conditions,
                params,
                param_idx,
            )

            where_clause = ""
            if conditions:
                where_clause = "WHERE " + " AND ".join(conditions)

            query = self._build_failures_trend_query(
                time_trunc, time_format, window_value, where_clause
            )

        else:  # conversations
            param_idx = self._build_trend_filters(
                conversation_id,
                start_time,
                end_time,
                "c.created_at",
                conditions,
                params,
                param_idx,
            )

            where_clause = ""
            if conditions:
                where_clause = "WHERE " + " AND ".join(conditions)

            query = self._build_conversations_trend_query(
                time_trunc, time_format, window_value, where_clause
            )

        rows = await self._db.fetch(query, *params)

        return [
            {
                "timestamp": row["timestamp"],
                "value": float(row["value"]) if row["value"] else None,
                "rolling_avg": float(row["rolling_avg"]) if row["rolling_avg"] else None,
            }
            for row in rows
        ]
