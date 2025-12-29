# Changelog

All notable changes to voiceobs will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.2] - 2025-12-28

### Added

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

#### Configuration System
- YAML configuration file support (`voiceobs.yaml`)
- `voiceobs init` command to generate starter config
- Configurable: exporters, failure thresholds, LLM settings, regression thresholds
- Precedence: CLI args > project config > user config

#### Decorator API
- `@voice_conversation_decorator()` - wrap functions as conversations
- `@voice_turn_decorator(actor="user"|"agent")` - wrap functions as turns
- `@voice_stage_decorator(stage="asr"|"llm"|"tts")` - wrap functions as stages
- Support for both sync and async functions

#### CLI Commands
- `voiceobs init` - generate configuration file
- `voiceobs analyze` - analyze JSONL traces with latency metrics
- `voiceobs compare` - compare two trace files, detect regressions
- `voiceobs report` - generate HTML or Markdown reports
- `--json` flag for machine-readable output on all commands
- `--quiet` flag to suppress non-essential output

#### Report Generation
- Markdown and HTML report formats
- Self-contained HTML with inline CSS
- Summary, latency breakdown, failure analysis, recommendations

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
