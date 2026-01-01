# Overview

**voiceobs** is an open, vendor-neutral observability library for voice AI conversations. It instruments your voice applications as OpenTelemetry spans, giving you turn-level visibility into conversations.

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
- **Stage-level latency**: Track ASR, LLM, and TTS processing separately
- **Failure detection**: Automatically identify high latency, interruptions, and errors
- **Conversation correlation**: All turns in a conversation share a conversation ID
- **CLI analysis tools**: Analyze, compare, and report on trace data
- **Zero config**: Works out of the box with console output

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
        "voice.schema.version": "0.0.2",
        "voice.conversation.id": "550e8400-e29b-41d4-a716-446655440000",
        "voice.turn.id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
        "voice.turn.index": 0,
        "voice.actor": "user"
    }
}
```

## Key Features

### 🖥️ REST API Server
Run voiceobs as a standalone server for team-wide observability:

```bash
# Install server dependencies
pip install voiceobs[server]

# Start the server
voiceobs server --host 0.0.0.0 --port 8765
```

Access the API documentation at `http://localhost:8765/docs` (Swagger UI) or `http://localhost:8765/redoc` (ReDoc).

### 🎯 Decorator API
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

### ⚙️ Configuration System
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

### 📊 CLI Analysis Tools

```bash
# Analyze latency and failures
voiceobs analyze --input traces.jsonl

# Compare runs and detect regressions
voiceobs compare --baseline baseline.jsonl --current current.jsonl

# Generate shareable reports
voiceobs report --input traces.jsonl --format html --output report.html
```

## Next Steps

- [Install voiceobs](./installation.md)
- [Learn about configuration](./guides/configuration.md)
- [Explore the CLI tools](./guides/cli.md)
- [Set up the server](./guides/server.md)
- [Check out examples](./examples.md)
- [View changelog](./changelog.md)
