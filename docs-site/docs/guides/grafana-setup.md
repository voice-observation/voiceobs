# Grafana Setup Guide for voiceobs

This guide explains how to set up Grafana dashboards for voiceobs observability. voiceobs exports OpenTelemetry traces via OTLP, which can be visualized in Grafana using Tempo (for traces) and Prometheus (for metrics derived from traces).

## Overview

voiceobs provides two pre-built Grafana dashboards:

1. **voiceobs-overview.json** - High-level metrics across all conversations:
   - Latency breakdown (ASR/LLM/TTS)
   - Latency percentiles over time
   - Failure rate by type
   - Conversation volume
   - Silence duration distribution
   - Top failures table

2. **voiceobs-detailed.json** - Detailed view for a specific conversation:
   - Conversation trace timeline
   - Stage latencies by turn
   - Turn details table
   - Failures in conversation

## Architecture

```
voiceobs Application
    ↓ (OTLP traces)
OpenTelemetry Collector
    ↓ (traces)        ↓ (metrics)
Tempo              Prometheus
    ↓                    ↓
    └───────── Grafana ─────┘
```

## Prerequisites

- Grafana 10.0 or later
- OpenTelemetry Collector (OTel Collector)
- Tempo (for trace storage)
- Prometheus (for metrics storage)

## Option 1: Using Docker Compose (Recommended)

The easiest way to get started is using the provided Docker Compose setup.

### Step 1: Start the Infrastructure

```bash
docker-compose -f docker-compose.grafana.yml up -d
```

This starts:
- Grafana (port 3000)
- Tempo (port 4317 for OTLP, 3200 for HTTP)
- Prometheus (port 9090)
- OpenTelemetry Collector (port 4318 for OTLP)

### Step 2: Configure voiceobs

Update your `voiceobs.yaml` configuration:

```yaml
exporters:
  otlp:
    enabled: true
    endpoint: "http://localhost:4318"  # OTel Collector endpoint
    protocol: "grpc"
```

### Step 3: Import Dashboards

1. Open Grafana at http://localhost:3000
2. Default credentials: `admin` / `admin`
3. Go to **Dashboards** → **Import**
4. Upload `dashboards/voiceobs-overview.json`
5. Upload `dashboards/voiceobs-detailed.json`

The dashboards will automatically detect the Prometheus and Tempo datasources.

## Option 2: Manual Setup

### Step 1: Install Components

#### Grafana

```bash
# macOS
brew install grafana

# Linux (Ubuntu/Debian)
sudo apt-get install -y grafana

# Or use Docker
docker run -d -p 3000:3000 grafana/grafana
```

#### Tempo

```bash
# Using Docker
docker run -d -p 4317:4317 -p 3200:3200 \
  -v $(pwd)/tempo-config.yaml:/etc/tempo/tempo-config.yaml \
  grafana/tempo:latest \
  -config.file=/etc/tempo/tempo-config.yaml
```

#### Prometheus

```bash
# Using Docker
docker run -d -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus:latest
```

#### OpenTelemetry Collector

Download from https://github.com/open-telemetry/opentelemetry-collector-releases/releases

### Step 2: Configure OpenTelemetry Collector

Create `otel-collector-config.yaml`:

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4318
      cors:
        allowed_origins:
          - "*"

processors:
  batch:
    timeout: 1s
    send_batch_size: 1024
  # Transform traces to metrics
  transform:
    trace_statements:
      - context: span
        statements:
          # Stage duration metrics
          - set(metric["voice_stage_duration_ms"], attributes["voice.stage.duration_ms"])
          - set(metric["voice_stage_duration_ms_bucket"], attributes["voice.stage.duration_ms"])
          # Silence duration metrics
          - set(metric["voice_silence_duration_ms"], attributes["voice.silence.after_user_ms"])
          - set(metric["voice_silence_duration_ms_bucket"], attributes["voice.silence.after_user_ms"])
          # Failure metrics
          - set(metric["voice_failures_total"], 1) where attributes["voice.failure.type"] != nil
          # Conversation metrics
          - set(metric["voice_conversations_total"], 1) where name == "voice.conversation"

exporters:
  # Export traces to Tempo
  otlp/tempo:
    endpoint: tempo:4317
    tls:
      insecure: true

  # Export metrics to Prometheus
  prometheus:
    endpoint: "0.0.0.0:8889"
    const_labels:
      service: voiceobs

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch, transform]
      exporters: [otlp/tempo]
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus]
```

### Step 3: Configure Prometheus

Create `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'otel-collector'
    static_configs:
      - targets: ['otel-collector:8889']
```

### Step 4: Configure Grafana Datasources

1. Open Grafana → **Configuration** → **Data Sources**
2. Add **Prometheus** datasource:
   - URL: `http://prometheus:9090`
   - Access: Server (default)
3. Add **Tempo** datasource:
   - URL: `http://tempo:3200`
   - Access: Server (default)
   - Enable **TraceQL** query language

### Step 5: Import Dashboards

1. Go to **Dashboards** → **Import**
2. Upload `dashboards/voiceobs-overview.json`
3. Upload `dashboards/voiceobs-detailed.json`

## Option 3: Grafana Cloud Setup

If you're using Grafana Cloud, you can use the managed Tempo and Prometheus services.

### Step 1: Get Your Credentials

From your Grafana Cloud dashboard, get:
- Tempo endpoint and API key
- Prometheus endpoint and API key
- Grafana API key

### Step 2: Configure OTLP Exporter

Update `voiceobs.yaml`:

```yaml
exporters:
  otlp:
    enabled: true
    endpoint: "https://tempo-us-central1.grafana.net:443"  # Your Tempo endpoint
    protocol: "grpc"
    headers:
      Authorization: "Basic <your-tempo-api-key>"
```

### Step 3: Configure Grafana Datasources

In Grafana Cloud:
1. Go to **Connections** → **Data Sources**
2. Add **Prometheus** (should already be configured)
3. Add **Tempo** with your Tempo endpoint and API key

### Step 4: Import Dashboards

Import the dashboard JSON files as described above.

## Dashboard Variables

Both dashboards include variables for filtering:

- **Conversation ID**: Filter by specific conversation
- **Failure Type**: Filter by failure type (interruption, excessive_silence, etc.)
- **Time Range**: Adjustable time range selector

## Metrics Reference

The dashboards use Prometheus metrics derived from OpenTelemetry traces. The provided `otel-collector-config.yaml` uses the `spanmetrics` processor to automatically generate basic metrics from spans.

### Automatically Generated Metrics (via spanmetrics)

The `spanmetrics` processor creates:
- `calls_total{service_name="voiceobs", ...}` - Total span count
- `latency{service_name="voiceobs", ...}` - Span duration histogram
- Metrics include dimensions from span attributes (e.g., `voice.stage.type`, `voice.conversation.id`)

### Custom Metrics (Advanced)

For full dashboard functionality, you may want to extract additional metrics from span attributes. The dashboards expect:

**Stage Metrics**:
- `voice_stage_duration_ms{stage_type="asr|llm|tts", conversation_id="..."}` - Stage duration in milliseconds
- `voice_stage_duration_ms_bucket{le="...", stage_type="..."}` - Histogram buckets for percentiles

**Silence Metrics**:
- `voice_silence_duration_ms{conversation_id="..."}` - Silence duration after user turn
- `voice_silence_duration_ms_bucket{le="..."}` - Histogram buckets

**Failure Metrics**:
- `voice_failures_total{failure_type="...", severity="...", conversation_id="..."}` - Failure counter

**Conversation Metrics**:
- `voice_conversations_total{conversation_id="..."}` - Conversation counter

**Note**: To generate these custom metrics, you'll need to extend the OpenTelemetry Collector configuration with a custom processor or exporter. Alternatively, you can query traces directly in Grafana using TraceQL (see the detailed dashboard for examples).

For most use cases, the automatically generated `spanmetrics` will provide sufficient observability. You can customize the dashboards to use these metrics instead.

## Trace Attributes

The dashboards query traces using these OpenTelemetry attributes:

- `voice.conversation.id` - Conversation identifier
- `voice.turn.id` - Turn identifier
- `voice.turn.index` - Turn index in conversation
- `voice.actor` - Actor type (user/agent/system)
- `voice.stage.type` - Stage type (asr/llm/tts)
- `voice.stage.duration_ms` - Stage duration
- `voice.stage.provider` - Stage provider (e.g., "deepgram", "openai")
- `voice.stage.model` - Stage model (e.g., "nova-2", "gpt-4")
- `voice.silence.after_user_ms` - Silence duration after user turn
- `voice.turn.overlap_ms` - Overlap duration (interruption)
- `voice.failure.type` - Failure type
- `voice.failure.severity` - Failure severity (low/medium/high)

## Troubleshooting

### No Data in Dashboards

1. **Check OTLP Export**: Verify traces are being exported:
   ```python
   from voiceobs.tracing import ensure_tracing_initialized
   ensure_tracing_initialized()
   ```

2. **Check Collector Logs**:
   ```bash
   docker logs otel-collector
   ```

3. **Check Tempo**: Verify traces are being received:
   ```bash
   curl http://localhost:3200/api/traces
   ```

4. **Check Prometheus**: Verify metrics are being scraped:
   ```bash
   curl http://localhost:9090/api/v1/query?query=voice_conversations_total
   ```

### Metrics Not Appearing

If metrics don't appear in Prometheus, ensure the OpenTelemetry Collector is configured to transform traces to metrics (see `otel-collector-config.yaml` above).

### Dashboard Variables Not Working

Ensure the Prometheus datasource is correctly configured and that metrics with the expected labels exist.

## Next Steps

- Customize dashboards for your specific needs
- Set up alerts based on failure rates or latency thresholds
- Add custom panels for your specific metrics
- Integrate with other observability tools

## Additional Resources

- [OpenTelemetry Collector Documentation](https://opentelemetry.io/docs/collector/)
- [Grafana Tempo Documentation](https://grafana.com/docs/tempo/latest/)
- [Grafana Dashboard Best Practices](https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/best-practices/)
