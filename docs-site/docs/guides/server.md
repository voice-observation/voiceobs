# Server Guide

The voiceobs server provides a REST API for centralized observability of voice AI conversations.

## Quick Start

### In-Memory (Development)

For development and testing, run with in-memory storage:

```bash
# Install server dependencies
pip install voiceobs[server]

# Start the server
voiceobs server
```

The server starts at `http://127.0.0.1:8765`.

### With PostgreSQL (Production)

For production use with persistent storage:

```bash
# Start PostgreSQL
docker compose up -d postgres

# Run database migrations
voiceobs db migrate

# Start the server
voiceobs server
```

## Docker Setup

Use the provided `docker-compose.yml`:

```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: voiceobs
      POSTGRES_USER: voiceobs
      POSTGRES_PASSWORD: voiceobs
    ports:
      - "5432:5432"
    volumes:
      - voiceobs_data:/var/lib/postgresql

volumes:
  voiceobs_data:
```

Start PostgreSQL:

```bash
docker compose up -d postgres
```

## Interactive Documentation

The server provides interactive API documentation:

- **Swagger UI**: `http://localhost:8765/docs` - Interactive API explorer
- **ReDoc**: `http://localhost:8765/redoc` - Alternative documentation view
- **OpenAPI Spec**: `http://localhost:8765/openapi.json` - Raw OpenAPI schema

## Configuration

### Configuration File

Create `voiceobs.yaml`:

```yaml
server:
  host: 0.0.0.0
  port: 8765
  database_url: postgresql://voiceobs:voiceobs@localhost:5432/voiceobs
```

### Environment Variables

Or use environment variables:

```bash
export VOICEOBS_DATABASE_URL=postgresql://voiceobs:voiceobs@localhost:5432/voiceobs
voiceobs server
```

### Command Line Options

```bash
# Custom host and port
voiceobs server --host 0.0.0.0 --port 8000

# Custom database URL
voiceobs server --database-url postgresql://user:pass@localhost/voiceobs
```

## Database Migrations

Initialize and run database migrations:

```bash
# Run database migrations
voiceobs db migrate

# Show current revision
voiceobs db current

# Show migration history
voiceobs db history
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/ingest` | POST | Ingest spans (single or batch) |
| `/spans` | GET | List all spans |
| `/spans/{id}` | GET | Get span by ID |
| `/spans` | DELETE | Clear all spans |
| `/analyze` | GET | Analyze all spans |
| `/analyze/{conversation_id}` | GET | Analyze specific conversation |
| `/conversations` | GET | List conversations |
| `/conversations/{id}` | GET | Get conversation details |
| `/failures` | GET | List detected failures |

## Ingesting Spans

### Single Span

```bash
curl -X POST http://localhost:8765/ingest \
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

### Batch Ingest

```bash
curl -X POST http://localhost:8765/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "spans": [
      {
        "name": "voice.turn",
        "duration_ms": 2500.0,
        "attributes": {
          "voice.conversation.id": "conv-123",
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

## Querying Data

### List Conversations

```bash
curl http://localhost:8765/conversations
```

### Get Analysis

```bash
# Analyze all spans
curl http://localhost:8765/analyze

# Analyze specific conversation
curl http://localhost:8765/analyze/conv-123
```

### List Failures

```bash
# All failures
curl http://localhost:8765/failures

# Filter by severity
curl "http://localhost:8765/failures?severity=high"

# Filter by type
curl "http://localhost:8765/failures?type=high_latency"
```

## Integration with Applications

### Using OpenTelemetry OTLP Exporter

Configure your application to send spans to the voiceobs server:

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Configure OTLP exporter to send to voiceobs server
provider = TracerProvider()
exporter = OTLPSpanExporter(
    endpoint="http://localhost:8765/ingest",
    headers={"Content-Type": "application/json"}
)
provider.add_span_processor(BatchSpanProcessor(exporter))
trace.set_tracer_provider(provider)
```

### Using HTTP Client

Send spans directly via HTTP:

```python
import requests

span = {
    "name": "voice.turn",
    "duration_ms": 2500.0,
    "attributes": {
        "voice.conversation.id": "conv-123",
        "voice.actor": "user"
    }
}

response = requests.post(
    "http://localhost:8765/ingest",
    json={"spans": [span]},
    headers={"Content-Type": "application/json"}
)
```

## Production Deployment

### Environment Variables

Set production configuration:

```bash
export VOICEOBS_DATABASE_URL=postgresql://user:pass@db-host:5432/voiceobs
export VOICEOBS_SERVER_HOST=0.0.0.0
export VOICEOBS_SERVER_PORT=8765
```

## Monitoring

### Health Check

```bash
curl http://localhost:8765/health
```

Response:
```json
{
  "status": "healthy",
  "version": "0.0.2",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Metrics

The server exposes metrics that can be scraped by Prometheus (if configured):

- Request count
- Request latency
- Database connection pool status
- Span ingestion rate

## Next Steps

- [CLI Guide](./cli.md)
- [Configuration Guide](./configuration.md)
