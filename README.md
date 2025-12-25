# voiceobs

**Open, vendor-neutral observability for voice AI conversations.**

[![PyPI version](https://badge.fury.io/py/voiceobs.svg)](https://pypi.org/project/voiceobs/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

## The Problem

Voice AI applications are hard to debug. When a conversation goes wrong, you're left asking:

- Which turn caused the issue?
- How long did each turn take?
- Was it the user's input or the agent's response?
- How do I correlate this with my existing traces?

Traditional logging doesn't capture the **temporal, turn-based nature** of voice conversations. You need observability that understands voice interactions.

## The Solution

**voiceobs** instruments voice AI conversations as OpenTelemetry spans, giving you:

- **Turn-level visibility**: See every user and agent turn as a span
- **Conversation correlation**: All turns in a conversation share a conversation ID
- **Timing data**: Know exactly how long each turn took
- **Zero config**: Works out of the box with console output
- **Non-invasive**: Won't override your existing OpenTelemetry setup

## 30-Second Quickstart

```bash
pip install voiceobs
```

```python
from voiceobs import ensure_tracing_initialized, voice_conversation, voice_turn

# Initialize tracing (uses ConsoleSpanExporter by default)
ensure_tracing_initialized()

# Instrument your conversation
with voice_conversation() as conv:
    print(f"Conversation: {conv.conversation_id}")

    with voice_turn("user"):
        # Process user speech/transcription
        pass

    with voice_turn("agent"):
        # Generate and speak agent response
        pass
```

**Output:**
```json
{
    "name": "voice.turn",
    "attributes": {
        "voice.schema.version": "0.0.1",
        "voice.conversation.id": "550e8400-e29b-41d4-a716-446655440000",
        "voice.turn.id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
        "voice.turn.index": 0,
        "voice.actor": "user"
    }
}
```

## CLI Demo

See voiceobs in action without writing any code:

```bash
voiceobs demo
```

This simulates a 4-turn conversation and prints the spans to the console.

Check your OpenTelemetry configuration:

```bash
voiceobs doctor
```

Analyze trace files to see latency metrics:

```bash
voiceobs analyze --input traces.jsonl
```

## Installation

```bash
pip install voiceobs
```

**Requirements:** Python 3.9+

## Usage

### Basic Conversation Tracking

```python
from voiceobs import voice_conversation, voice_turn

with voice_conversation() as conv:
    # User says something
    with voice_turn("user"):
        transcript = transcribe_audio(audio)
        process_user_input(transcript)

    # Agent responds
    with voice_turn("agent"):
        response = generate_response(transcript)
        synthesize_speech(response)
```

### Custom Conversation IDs

```python
# Use your own conversation ID for correlation with other systems
with voice_conversation(conversation_id="call-12345") as conv:
    with voice_turn("user"):
        pass
```

### Nested Turns (System Processing)

```python
with voice_conversation():
    with voice_turn("user"):
        # User turn spans the entire user processing

        with voice_turn("system"):
            # Nested system turn for internal processing
            run_safety_check()
```

### With Existing OpenTelemetry Setup

voiceobs detects and respects your existing OpenTelemetry configuration:

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Your existing setup
provider = TracerProvider()
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
trace.set_tracer_provider(provider)

# voiceobs will use your provider, not override it
from voiceobs import ensure_tracing_initialized
ensure_tracing_initialized()  # Returns False, keeps your config
```

### Accessing Current Context

```python
from voiceobs import get_current_conversation, get_current_turn

with voice_conversation():
    with voice_turn("user"):
        conv = get_current_conversation()
        turn = get_current_turn()

        print(f"Conversation: {conv.conversation_id}")
        print(f"Turn {turn.turn_index} by {turn.actor}")
```

## Span Attributes

Each `voice.turn` span includes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `voice.schema.version` | string | Schema version (currently "0.0.1") |
| `voice.conversation.id` | string | UUID identifying the conversation |
| `voice.turn.id` | string | UUID identifying this specific turn |
| `voice.turn.index` | int | Sequential turn number (0, 1, 2...) |
| `voice.actor` | string | Who is speaking: "user", "agent", or "system" |
| `voice.silence.after_user_ms` | float | Response latency from user speech end to agent speech start |
| `voice.turn.overlap_ms` | float | Overlap duration in ms (positive = interruption) |
| `voice.interruption.detected` | bool | True if agent started speaking before user finished |

## JSONL Export and Analysis

Export traces to a JSONL file for offline analysis:

```bash
# Enable JSONL export
VOICEOBS_JSONL_OUT=./traces.jsonl python your_app.py

# Analyze the traces
voiceobs analyze --input traces.jsonl
```

Output shows stage latencies (ASR/LLM/TTS), response latency, and interruption rate:

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

## Examples

See the [examples/](examples/) directory for complete, runnable examples:

| Example | Description |
|---------|-------------|
| [voice_pipeline](examples/voice_pipeline/) | Complete voice chat with ASR (Deepgram), LLM (Gemini), TTS (Cartesia) |
| [overlap_detection](examples/overlap_detection/) | Demonstrates barge-in and overlap/interruption detection |

Each example includes setup instructions, API key configuration, and demonstrates different voiceobs features.

## Integrations

### Pipecat

See [integrations/pipecat-examples/](integrations/pipecat-examples/) for a complete example of instrumenting a Pipecat voice bot.

```python
from voiceobs import voice_conversation, voice_turn
from pipecat.processors.frame_processor import FrameProcessor

class VoiceObsUserTurnTracker(FrameProcessor):
    async def process_frame(self, frame, direction):
        if isinstance(frame, TranscriptionFrame):
            # Track user turn
            self._turn = voice_turn("user")
            self._turn.__enter__()
        await self.push_frame(frame, direction)
```

## API Reference

### `voice_conversation(conversation_id: Optional[str] = None)`

Context manager for a voice conversation. Auto-generates UUID if not provided.

### `voice_turn(actor: Literal["user", "agent", "system"])`

Context manager for a voice turn. Creates an OpenTelemetry span with voice attributes.

### `ensure_tracing_initialized() -> bool`

Safely initializes tracing with ConsoleSpanExporter if no provider exists. Returns `True` if initialized, `False` if existing config was kept.

### `get_tracer_provider_info() -> dict`

Returns diagnostic info about the current tracer provider.

### `get_current_conversation() -> Optional[ConversationContext]`

Returns the current conversation context, or `None` if outside a conversation.

### `get_current_turn() -> Optional[TurnContext]`

Returns the current turn context, or `None` if outside a turn.

## Development

```bash
# Clone the repository
git clone https://github.com/voiceobs/voiceobs.git
cd voiceobs

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check src tests
```

## License

Apache-2.0 - see [LICENSE](LICENSE) for details.
