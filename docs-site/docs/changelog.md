# Changelog

All notable changes to voiceobs will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.2] - 2025-12-28

### Added

#### 🖥️ REST API Server
Run voiceobs as a standalone server for team-wide observability:

```bash
# Install server dependencies
pip install voiceobs[server]

# Start the server
voiceobs server --host 0.0.0.0 --port 8765
```

Access the API documentation at `http://localhost:8765/docs` (Swagger UI) or `http://localhost:8765/redoc` (ReDoc).

#### 🎯 Decorator API
Reduce boilerplate with decorators:

```python
from voiceobs import voice_conversation_decorator, voice_turn_decorator

@voice_conversation_decorator()
async def handle_call():
    user_input = await get_user_input()
    response = await generate_response(user_input)
    return response

@voice_turn_decorator(actor="agent")
async def generate_response(text):
    # This function is automatically wrapped in a voice turn span
    return await llm.generate(text)
```

#### ⚙️ Configuration System
Configure voiceobs with a YAML file:

```bash
voiceobs init  # Generate voiceobs.yaml
```

```yaml
# voiceobs.yaml
exporters:
  jsonl:
    enabled: true
    path: ./traces.jsonl
  console:
    enabled: true

failures:
  thresholds:
    high_latency_ms: 3000
    interruption_rate: 0.1
```

#### 📊 CLI Analysis Tools

```bash
# Analyze latency and failures
voiceobs analyze --input traces.jsonl

# Compare runs and detect regressions
voiceobs compare --baseline baseline.jsonl --current current.jsonl

# Generate shareable reports
voiceobs report --input traces.jsonl --format html --output report.html
```

#### Stage-Level Observability
- `voice_stage()` context manager for tracking ASR, LLM, and TTS stages
- Stage span attributes: `voice.stage.provider`, `voice.stage.model`, `voice.stage.input_size`, `voice.stage.output_size`
- Automatic duration tracking for each processing stage

#### Timing & Latency Metrics
- Response latency detection with `voice.silence.after_user_ms` attribute
- `mark_speech_end()` and `mark_speech_start()` functions for precise timing
- Overlap/interruption detection with `voice.turn.overlap_ms` and `voice.interruption.detected`

#### Failure Detection & Classification
- `FailureClassifier` for automatic issue detection in conversations
- Built-in failure types: high latency, interruptions, empty responses, repeated errors
- Configurable severity levels and thresholds
- `classify_file()` and `classify_spans()` functions for batch analysis

#### LLM-Powered Evaluation
- Semantic evaluation using LLM providers (Google, OpenAI, Anthropic)
- Evaluate coherence, helpfulness, and conversation quality
- Caching support to reduce API costs
- `voiceobs.eval` module with extensible evaluator classes

#### Framework Integrations
- LiveKit Agents SDK integration
- Vocode integration
- `voiceobs.integrations` module with base classes

#### JSONL Export
- `JSONLSpanExporter` for exporting spans to JSONL files
- One span per line with full trace data
- Configure via `voiceobs.yaml` exporters section

### Changed
- Schema version updated to `0.0.2`
- Improved error messages with actionable hints

## [0.0.1] - 2024-12-01

### Added
- Initial release
- `voice_conversation()` context manager for conversation tracking
- `voice_turn()` context manager for turn tracking
- Basic OpenTelemetry span generation
- `ensure_tracing_initialized()` for safe tracer setup
- `voiceobs demo` and `voiceobs doctor` CLI commands
- Console span exporter by default
