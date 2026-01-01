# Configuration Guide

voiceobs can be configured via a YAML configuration file or environment variables.

## Configuration File

Generate a default configuration file:

```bash
voiceobs init
```

This creates `voiceobs.yaml` in the current directory with default settings.

## Configuration Structure

```yaml
# Exporters configuration
exporters:
  jsonl:
    enabled: true
    path: ./traces.jsonl
  console:
    enabled: true

# Failure detection thresholds
failures:
  thresholds:
    excessive_silence_ms: 3000.0
    slow_asr_ms: 2000.0
    slow_llm_ms: 2000.0
    slow_tts_ms: 2000.0
    asr_min_confidence: 0.7
    llm_min_relevance: 0.5

# Regression detection thresholds
regression:
  thresholds:
    latency_warning_pct: 10.0
    latency_critical_pct: 25.0
    silence_warning_pct: 15.0
    silence_critical_pct: 30.0
    interruption_warning_pp: 5.0
    interruption_critical_pp: 15.0

# LLM evaluator configuration
eval:
  provider: openai
  model: gpt-4
  api_key: ${OPENAI_API_KEY}
  temperature: 0.0

# Server configuration
server:
  host: 0.0.0.0
  port: 8765
  database_url: postgresql://voiceobs:voiceobs@localhost:5432/voiceobs
```

## Exporters

Configure how spans are exported:

### JSONL Exporter

Export spans to a JSONL file:

```yaml
exporters:
  jsonl:
    enabled: true
    path: ./traces.jsonl
```

### Console Exporter

Print spans to console:

```yaml
exporters:
  console:
    enabled: true
```

### OTLP Exporter

Send spans to an OTLP endpoint:

```yaml
exporters:
  otlp:
    enabled: true
    endpoint: http://localhost:4317
    headers:
      Authorization: Bearer ${OTLP_TOKEN}
```

## Failure Thresholds

Configure when failures are detected:

```yaml
failures:
  thresholds:
    # Silence after user turn (ms)
    excessive_silence_ms: 3000.0

    # Stage duration thresholds (ms)
    slow_asr_ms: 2000.0
    slow_llm_ms: 2000.0
    slow_tts_ms: 2000.0

    # Confidence thresholds (0-1)
    asr_min_confidence: 0.7
    llm_min_relevance: 0.5
```

## Regression Thresholds

Configure regression detection for CI/CD:

```yaml
regression:
  thresholds:
    # Latency regression thresholds (%)
    latency_warning_pct: 10.0
    latency_critical_pct: 25.0

    # Silence regression thresholds (%)
    silence_warning_pct: 15.0
    silence_critical_pct: 30.0

    # Interruption regression thresholds (percentage points)
    interruption_warning_pp: 5.0
    interruption_critical_pp: 15.0
```

## LLM Evaluator

Configure semantic evaluation:

```yaml
eval:
  provider: openai  # openai, anthropic, gemini
  model: gpt-4
  api_key: ${OPENAI_API_KEY}
  temperature: 0.0
```

Supported providers:
- `openai` - OpenAI GPT models
- `anthropic` - Anthropic Claude models
- `gemini` - Google Gemini models

## Server Configuration

Configure the REST API server:

```yaml
server:
  host: 0.0.0.0
  port: 8765
  database_url: postgresql://voiceobs:voiceobs@localhost:5432/voiceobs
```

## Environment Variables

Override configuration with environment variables:

```bash
# JSONL output file
export VOICEOBS_JSONL_OUT=./traces.jsonl

# Configuration file path
export VOICEOBS_CONFIG=./config/voiceobs.yaml

# Database URL
export VOICEOBS_DATABASE_URL=postgresql://user:pass@localhost/voiceobs

# Server settings
export VOICEOBS_SERVER_HOST=0.0.0.0
export VOICEOBS_SERVER_PORT=8765

# LLM evaluator
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export GOOGLE_API_KEY=...
```

## Configuration Precedence

Configuration is loaded in this order (later overrides earlier):

1. Default values
2. Configuration file (`voiceobs.yaml`)
3. Environment variables

## Custom Configuration Path

Specify a custom configuration file:

```bash
# Via environment variable
export VOICEOBS_CONFIG=./config/voiceobs.yaml

# Via command line (for init)
voiceobs init --path ./config/voiceobs.yaml
```

## Examples

### Development Configuration

```yaml
exporters:
  console:
    enabled: true
  jsonl:
    enabled: true
    path: ./dev-traces.jsonl

failures:
  thresholds:
    excessive_silence_ms: 5000.0  # More lenient for dev
```

### Production Configuration

```yaml
exporters:
  otlp:
    enabled: true
    endpoint: https://otel-collector.example.com:4317

failures:
  thresholds:
    excessive_silence_ms: 2000.0  # Stricter for production
    slow_llm_ms: 1500.0

server:
  host: 0.0.0.0
  port: 8765
  database_url: ${DATABASE_URL}
```

### CI/CD Configuration

```yaml
exporters:
  jsonl:
    enabled: true
    path: ./ci-traces.jsonl

regression:
  thresholds:
    latency_warning_pct: 5.0   # Stricter for CI
    latency_critical_pct: 15.0
```

## Next Steps

- [CLI Guide](./cli.md)
- [Server Guide](./server.md)
- [Failure Taxonomy](../advanced/failures.md)
