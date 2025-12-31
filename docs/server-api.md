# voiceobs Server API Quickstart

The voiceobs server provides a REST API for ingesting and analyzing voice AI conversation data.

## Starting the Server

```bash
# Install with server dependencies
pip install "voiceobs[server]"

# Start the server
uvicorn voiceobs.server:app --host 0.0.0.0 --port 8000
```

The server will be available at `http://localhost:8000`.

## Interactive Documentation

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs) - Interactive API explorer
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc) - Alternative documentation view
- **OpenAPI Spec**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json) - Raw OpenAPI schema

## API Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/ingest` | POST | Ingest spans |
| `/spans` | GET | List all spans |
| `/spans/{id}` | GET | Get span by ID |
| `/spans` | DELETE | Clear all spans |
| `/analyze` | GET | Analyze all spans |
| `/analyze/{id}` | GET | Analyze specific conversation |
| `/conversations` | GET | List conversations |
| `/conversations/{id}` | GET | Get conversation details |
| `/failures` | GET | List detected failures |

## Quick Examples

### Check Server Health

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "version": "0.0.2",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Ingest a Single Span

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "name": "voice.turn",
    "duration_ms": 2500.0,
    "attributes": {
      "voice.conversation.id": "conv-123",
      "voice.turn.id": "turn-001",
      "voice.actor": "user",
      "voice.transcript": "Hello, I need help with my order"
    }
  }'
```

Response:
```json
{
  "accepted": 1,
  "span_ids": ["550e8400-e29b-41d4-a716-446655440000"]
}
```

### Ingest Multiple Spans (Batch)

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "spans": [
      {
        "name": "voice.turn",
        "duration_ms": 2500.0,
        "attributes": {
          "voice.conversation.id": "conv-123",
          "voice.turn.id": "turn-001",
          "voice.actor": "user"
        }
      },
      {
        "name": "voice.asr",
        "duration_ms": 150.5,
        "attributes": {
          "voice.conversation.id": "conv-123",
          "voice.stage.type": "asr"
        }
      }
    ]
  }'
```

### List All Spans

```bash
curl http://localhost:8000/spans
```

Response:
```json
{
  "count": 2,
  "spans": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "voice.turn",
      "duration_ms": 2500.0,
      "attributes": {"voice.actor": "user"}
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "voice.asr",
      "duration_ms": 150.0,
      "attributes": {"voice.stage.type": "asr"}
    }
  ]
}
```

### Get Span Details

```bash
curl http://localhost:8000/spans/550e8400-e29b-41d4-a716-446655440000
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "voice.turn",
  "start_time": "2024-01-15T10:30:00Z",
  "end_time": "2024-01-15T10:30:02.500Z",
  "duration_ms": 2500.0,
  "attributes": {
    "voice.conversation.id": "conv-123",
    "voice.turn.id": "turn-001",
    "voice.actor": "user",
    "voice.transcript": "Hello, I need help"
  },
  "trace_id": "abc123def456",
  "span_id": "span-001",
  "parent_span_id": null
}
```

### Analyze All Spans

```bash
curl http://localhost:8000/analyze
```

Response:
```json
{
  "summary": {
    "total_spans": 50,
    "total_conversations": 3,
    "total_turns": 20
  },
  "stages": {
    "asr": {
      "stage_type": "asr",
      "count": 15,
      "mean_ms": 145.5,
      "p50_ms": 132.0,
      "p95_ms": 210.5,
      "p99_ms": 285.0
    },
    "llm": {
      "stage_type": "llm",
      "count": 15,
      "mean_ms": 850.0,
      "p50_ms": 780.0,
      "p95_ms": 1200.0,
      "p99_ms": 1500.0
    },
    "tts": {
      "stage_type": "tts",
      "count": 15,
      "mean_ms": 220.0,
      "p50_ms": 200.0,
      "p95_ms": 350.0,
      "p99_ms": 420.0
    }
  },
  "turns": {
    "silence_samples": 10,
    "silence_mean_ms": 850.0,
    "silence_p95_ms": 1200.0,
    "total_agent_turns": 8,
    "interruptions": 1,
    "interruption_rate": 12.5
  },
  "eval": {
    "total_evals": 10,
    "intent_correct_count": 9,
    "intent_incorrect_count": 1,
    "intent_correct_rate": 90.0,
    "intent_failure_rate": 10.0,
    "avg_relevance_score": 0.85,
    "min_relevance_score": 0.65,
    "max_relevance_score": 0.98
  }
}
```

### List Conversations

```bash
curl http://localhost:8000/conversations
```

Response:
```json
{
  "count": 2,
  "conversations": [
    {
      "id": "conv-123",
      "turn_count": 8,
      "span_count": 24,
      "has_failures": false
    },
    {
      "id": "conv-456",
      "turn_count": 5,
      "span_count": 15,
      "has_failures": true
    }
  ]
}
```

### Get Conversation Details

```bash
curl http://localhost:8000/conversations/conv-123
```

Response includes all turns and analysis for the specific conversation.

### List Failures

```bash
# List all failures
curl http://localhost:8000/failures

# Filter by severity
curl "http://localhost:8000/failures?severity=high"

# Filter by type
curl "http://localhost:8000/failures?type=high_latency"
```

Response:
```json
{
  "count": 2,
  "failures": [
    {
      "id": "0",
      "type": "high_latency",
      "severity": "high",
      "message": "High latency detected in LLM stage",
      "conversation_id": "conv-123",
      "turn_id": "turn-003",
      "turn_index": 2,
      "signal_name": "llm_latency_ms",
      "signal_value": 3500.0,
      "threshold": 2000.0
    }
  ],
  "by_severity": {"high": 1, "medium": 1},
  "by_type": {"high_latency": 1, "interruption": 1}
}
```

### Clear All Spans

```bash
curl -X DELETE http://localhost:8000/spans
```

Response:
```json
{
  "cleared": 15
}
```

## Span Attributes

The voiceobs server expects spans with specific attributes for proper analysis:

| Attribute | Description | Example |
|-----------|-------------|---------|
| `voice.conversation.id` | Unique conversation identifier | `"conv-123"` |
| `voice.turn.id` | Unique turn identifier | `"turn-001"` |
| `voice.turn.index` | Turn sequence number | `0` |
| `voice.actor` | Speaker: `"user"`, `"agent"`, or `"system"` | `"user"` |
| `voice.stage.type` | Pipeline stage: `"asr"`, `"llm"`, or `"tts"` | `"asr"` |
| `voice.transcript` | Transcribed text | `"Hello, I need help"` |

## Error Handling

All errors return a consistent format:

```json
{
  "error": "not_found",
  "message": "Resource not found",
  "detail": "Span with ID 550e8400-e29b-41d4-a716-446655440000 not found"
}
```

Common HTTP status codes:
- `200` - Success
- `201` - Created (span ingestion)
- `400` - Bad request (invalid data)
- `404` - Not found
- `422` - Validation error

## OpenAPI Specification

The full OpenAPI specification is available at:
- JSON: `GET /openapi.json`
- YAML: See `docs/openapi.yaml` in the repository
