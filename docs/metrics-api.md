# Metrics Aggregation API

The Metrics Aggregation API provides pre-computed aggregated metrics for building dashboards and monitoring voice AI conversations. These endpoints enable you to retrieve statistics without writing complex queries.

**Note**: All metrics endpoints require a PostgreSQL database connection. They will return `501 Not Implemented` if using in-memory storage.

## Overview

The Metrics API includes 5 endpoints:

| Endpoint | Description |
|----------|-------------|
| `GET /metrics/summary` | Overall statistics (conversations, turns, latency, failures) |
| `GET /metrics/latency` | Latency breakdown by stage or custom attribute |
| `GET /metrics/failures` | Failure breakdown by type or severity |
| `GET /metrics/conversations` | Conversation volume over time |
| `GET /metrics/trends` | Time-series trends with rolling averages |

## Common Parameters

All metrics endpoints support the following optional query parameters:

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `start_time` | datetime | Filter by start time (ISO 8601) | `2024-01-15T00:00:00Z` |
| `end_time` | datetime | Filter by end time (ISO 8601) | `2024-01-15T23:59:59Z` |
| `conversation_id` | string | Filter by conversation ID | `conv-123` |

## GET /metrics/summary

Get overall statistics including total conversations, turns, latency percentiles, failure rates, and silence/overlap metrics.

### Request

```bash
# Get overall summary
curl http://localhost:8000/metrics/summary

# With time range filter
curl "http://localhost:8000/metrics/summary?start_time=2024-01-15T00:00:00Z&end_time=2024-01-15T23:59:59Z"

# Filter by conversation
curl "http://localhost:8000/metrics/summary?conversation_id=conv-123"
```

### Response

```json
{
  "total_conversations": 100,
  "total_turns": 500,
  "total_duration_ms": 125000.0,
  "avg_latency_p50_ms": 150.0,
  "avg_latency_p95_ms": 300.0,
  "avg_latency_p99_ms": 450.0,
  "failure_rate": 2.5,
  "total_failures": 25,
  "silence_mean_ms": 850.0,
  "overlap_count": 10
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `total_conversations` | integer | Total number of conversations |
| `total_turns` | integer | Total number of turns |
| `total_duration_ms` | float | Total duration in milliseconds |
| `avg_latency_p50_ms` | float | P50 (median) latency across all stages |
| `avg_latency_p95_ms` | float | P95 latency across all stages |
| `avg_latency_p99_ms` | float | P99 latency across all stages |
| `failure_rate` | float | Failure rate percentage |
| `total_failures` | integer | Total number of failures |
| `silence_mean_ms` | float | Mean silence duration in milliseconds |
| `overlap_count` | integer | Number of overlaps detected |

## GET /metrics/latency

Get latency metrics broken down by stage or custom span attribute.

### Request Parameters

| Parameter | Type | Default | Description |
|-----------|------|--------|-------------|
| `group_by` | string | `"stage"` | Group by field (e.g., `"stage"` or custom span attribute) |

### Request Examples

```bash
# Breakdown by stage (default)
curl http://localhost:8000/metrics/latency?group_by=stage

# With filters
curl "http://localhost:8000/metrics/latency?group_by=stage&start_time=2024-01-15T00:00:00Z"

# Group by custom attribute
curl "http://localhost:8000/metrics/latency?group_by=voice.model.name"
```

### Response

```json
{
  "breakdown": [
    {
      "group": "asr",
      "count": 100,
      "mean_ms": 145.5,
      "p50_ms": 132.0,
      "p95_ms": 210.5,
      "p99_ms": 285.0
    },
    {
      "group": "llm",
      "count": 100,
      "mean_ms": 850.0,
      "p50_ms": 750.0,
      "p95_ms": 1200.0,
      "p99_ms": 1500.0
    },
    {
      "group": "tts",
      "count": 100,
      "mean_ms": 220.0,
      "p50_ms": 200.0,
      "p95_ms": 350.0,
      "p99_ms": 420.0
    }
  ]
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `breakdown` | array | List of latency breakdown items |
| `breakdown[].group` | string | Group identifier (stage name, etc.) |
| `breakdown[].count` | integer | Number of samples |
| `breakdown[].mean_ms` | float | Mean latency in milliseconds |
| `breakdown[].p50_ms` | float | P50 (median) latency |
| `breakdown[].p95_ms` | float | P95 latency |
| `breakdown[].p99_ms` | float | P99 latency |

## GET /metrics/failures

Get failure counts grouped by type or severity.

### Request Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `group_by` | string | `"type"` | Group by `"type"` or `"severity"` |

### Request Examples

```bash
# Breakdown by type (default)
curl http://localhost:8000/metrics/failures?group_by=type

# Breakdown by severity
curl http://localhost:8000/metrics/failures?group_by=severity

# With filters
curl "http://localhost:8000/metrics/failures?group_by=type&start_time=2024-01-15T00:00:00Z"
```

### Response

```json
{
  "breakdown": [
    {
      "group": "high_latency",
      "count": 10,
      "percentage": 40.0
    },
    {
      "group": "interruption",
      "count": 15,
      "percentage": 60.0
    }
  ],
  "total": 25
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `breakdown` | array | List of failure breakdown items |
| `breakdown[].group` | string | Group identifier (failure type or severity) |
| `breakdown[].count` | integer | Number of failures |
| `breakdown[].percentage` | float | Percentage of total failures |
| `total` | integer | Total number of failures |

## GET /metrics/conversations

Get conversation volume aggregated by time buckets (hour, day, or week).

### Request Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `group_by` | string | `"hour"` | Time grouping: `"hour"`, `"day"`, or `"week"` |

### Request Examples

```bash
# Volume by hour (default)
curl http://localhost:8000/metrics/conversations?group_by=hour

# Volume by day
curl http://localhost:8000/metrics/conversations?group_by=day

# Volume by week
curl http://localhost:8000/metrics/conversations?group_by=week

# With time range
curl "http://localhost:8000/metrics/conversations?group_by=hour&start_time=2024-01-15T00:00:00Z&end_time=2024-01-15T23:59:59Z"
```

### Response

```json
{
  "volume": [
    {
      "time_bucket": "2024-01-15T10:00:00Z",
      "count": 5
    },
    {
      "time_bucket": "2024-01-15T11:00:00Z",
      "count": 8
    },
    {
      "time_bucket": "2024-01-15T12:00:00Z",
      "count": 12
    }
  ]
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `volume` | array | List of volume data points |
| `volume[].time_bucket` | string | Time bucket identifier (ISO 8601) |
| `volume[].count` | integer | Number of conversations in this bucket |

## GET /metrics/trends

Get time-series trends for metrics with rolling averages. Supports latency, failures, and conversations metrics.

### Request Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `metric` | string | `"latency"` | Metric name: `"latency"`, `"failures"`, or `"conversations"` |
| `window` | string | `"1h"` | Time window: `"1h"`, `"1d"`, `"1w"` (or multiples like `"2h"`, `"3d"`) |

### Request Examples

```bash
# Latency trends with 1-hour window
curl "http://localhost:8000/metrics/trends?metric=latency&window=1h"

# Failure trends with 1-day window
curl "http://localhost:8000/metrics/trends?metric=failures&window=1d"

# Conversation trends with 1-week window
curl "http://localhost:8000/metrics/trends?metric=conversations&window=1w"

# With filters
curl "http://localhost:8000/metrics/trends?metric=latency&window=1h&start_time=2024-01-15T00:00:00Z&conversation_id=conv-123"
```

### Response

```json
{
  "metric": "latency",
  "window": "1h",
  "data_points": [
    {
      "timestamp": "2024-01-15T10:00:00Z",
      "value": 150.0,
      "rolling_avg": 145.5
    },
    {
      "timestamp": "2024-01-15T11:00:00Z",
      "value": 160.0,
      "rolling_avg": 155.0
    },
    {
      "timestamp": "2024-01-15T12:00:00Z",
      "value": 155.0,
      "rolling_avg": 155.0
    }
  ]
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `metric` | string | Metric name |
| `window` | string | Time window used |
| `data_points` | array | List of trend data points |
| `data_points[].timestamp` | string | Timestamp (ISO 8601) |
| `data_points[].value` | float | Metric value at this timestamp |
| `data_points[].rolling_avg` | float | Rolling average value |

### Window Format

The `window` parameter accepts time windows in the format `{number}{unit}`:

- `{number}`: Integer value (e.g., `1`, `2`, `24`)
- `{unit}`: Time unit - `h` (hour), `d` (day), `w` (week)

Examples:
- `1h` - 1 hour window
- `2h` - 2 hour window
- `1d` - 1 day window
- `1w` - 1 week window

The rolling average is calculated over the specified window size.

## Error Responses

### 501 Not Implemented

Returned when using in-memory storage (PostgreSQL required):

```json
{
  "detail": "Metrics API requires PostgreSQL database"
}
```

### 500 Internal Server Error

Returned when the metrics repository is not available:

```json
{
  "detail": "Metrics repository not available"
}
```

## Performance Considerations

- **On-demand computation**: Metrics are computed on-demand using optimized SQL aggregation queries
- **PostgreSQL required**: All metrics endpoints require PostgreSQL for efficient aggregation
- **Indexing**: Ensure proper indexes are in place on `created_at`, `conversation_id`, and `start_time` columns
- **Time ranges**: Large time ranges may take longer to compute; consider using appropriate filters

## Best Practices

1. **Use appropriate time ranges**: Don't request metrics for very large time ranges without filters
2. **Cache results**: Consider caching metrics results for frequently accessed dashboards
3. **Filter when possible**: Use `conversation_id` or time range filters to reduce query time
4. **Monitor query performance**: Large aggregations may take time; monitor and optimize as needed
5. **Combine endpoints**: Use multiple endpoints together to build comprehensive dashboards
