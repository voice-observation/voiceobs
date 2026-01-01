# CLI Guide

The voiceobs CLI provides command-line tools for analyzing, comparing, and reporting on voice conversation traces.

## Installation

```bash
pip install voiceobs
```

## Commands Overview

| Command | Description |
|---------|-------------|
| `voiceobs demo` | Run a demo conversation |
| `voiceobs doctor` | Check OpenTelemetry configuration |
| `voiceobs init` | Generate configuration file |
| `voiceobs analyze` | Analyze trace files |
| `voiceobs compare` | Compare baseline vs current runs |
| `voiceobs report` | Generate reports |
| `voiceobs server` | Start the REST API server |
| `voiceobs db` | Database management commands |

## Demo

See voiceobs in action without writing any code:

```bash
voiceobs demo
```

This simulates a 4-turn conversation and prints the spans to the console.

## Doctor

Check your OpenTelemetry configuration:

```bash
voiceobs doctor
```

This command verifies that OpenTelemetry is properly configured and shows diagnostic information about your tracer provider.

## Init

Generate a configuration file:

```bash
# Create voiceobs.yaml in current directory
voiceobs init

# Overwrite existing config
voiceobs init --force

# Custom path
voiceobs init --path ./config/voiceobs.yaml
```

The generated `voiceobs.yaml` includes:
- Exporter settings (JSONL, console)
- Failure detection thresholds
- Regression comparison thresholds
- LLM evaluator configuration

## Analyze

Analyze trace files to see latency metrics:

```bash
# Analyze a JSONL trace file
voiceobs analyze --input traces.jsonl

# Output JSON format
voiceobs analyze --input traces.jsonl --json

# Short form
voiceobs analyze -i traces.jsonl
```

Output shows:
- Stage latencies (ASR/LLM/TTS) with percentiles
- Response latency (silence after user)
- Interruption rate
- Semantic evaluation metrics (if available)

### Example Output

```
voiceobs Analysis Report
==================================================

Stage Latencies (ms)
------------------------------
  ASR (n=2):
    mean: 165.2
    p50:  165.2
    p95:  180.0
  LLM (n=2):
    mean: 785.0
    p50:  785.0
    p95:  850.0
  TTS (n=2):
    mean: 300.0
    p50:  300.0
    p95:  320.0

Response Latency (silence after user)
------------------------------
  Samples: 2
  mean: 1115.0ms
  p95:  1250.0ms

Interruptions
------------------------------
  Agent turns: 2
  Interruptions: 0
  Rate: 0.0%
```

## Compare

Compare runs and detect regressions:

```bash
# Compare baseline vs current
voiceobs compare --baseline baseline.jsonl --current current.jsonl

# Short form
voiceobs compare -b baseline.jsonl -c current.jsonl

# Fail on regression (for CI)
voiceobs compare -b baseline.jsonl -c current.jsonl --fail-on-regression

# JSON output
voiceobs compare -b baseline.jsonl -c current.jsonl --json
```

The compare command detects:
- Latency regressions (ASR/LLM/TTS p95)
- Response latency increases
- Interruption rate increases
- Semantic score decreases

### Regression Thresholds

Default thresholds:
- **Latency**: +10% warning, +25% critical
- **Silence**: +15% warning, +30% critical
- **Interruptions**: +5pp warning, +15pp critical
- **Semantic**: -5pp warning, -15pp critical

## Report

Generate shareable reports:

```bash
# HTML report
voiceobs report --input traces.jsonl --format html --output report.html

# JSON report
voiceobs report --input traces.jsonl --format json --output report.json

# Short form
voiceobs report -i traces.jsonl -f html -o report.html
```

## Server

Start the REST API server:

```bash
# Start with defaults (localhost:8765)
voiceobs server

# Custom host and port
voiceobs server --host 0.0.0.0 --port 8000

# With PostgreSQL database
voiceobs server --database-url postgresql://user:pass@localhost/voiceobs
```

See the [Server Guide](./server.md) for more details.

## Database Commands

Manage database migrations:

```bash
# Run database migrations
voiceobs db migrate

# Show current revision
voiceobs db current

# Show migration history
voiceobs db history
```

## JSON Output

Many commands support `--json` flag for machine-readable output:

```bash
# Parse with jq
voiceobs analyze -i traces.jsonl --json | jq '.stages.llm.p95_ms'

# Use in scripts
if voiceobs compare -b baseline.jsonl -c current.jsonl --json | jq -e '.has_regressions'; then
  echo "Regressions detected!"
  exit 1
fi
```

See [JSON Schema Reference](../api/json-schema.md) for complete schema documentation.

## Environment Variables

Configure voiceobs via environment variables:

```bash
# JSONL output file
export VOICEOBS_JSONL_OUT=./traces.jsonl

# Configuration file path
export VOICEOBS_CONFIG=./config/voiceobs.yaml

# Database URL (for server)
export VOICEOBS_DATABASE_URL=postgresql://user:pass@localhost/voiceobs
```

## Next Steps

- [Configuration Guide](./configuration.md)
- [Server Guide](./server.md)
- [CI Workflow Guide](../advanced/ci-workflow.md)
