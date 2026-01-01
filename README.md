# voiceobs

**Open, vendor-neutral observability for voice AI conversations.**

[![PyPI version](https://badge.fury.io/py/voiceobs.svg)](https://pypi.org/project/voiceobs/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

📚 **[Documentation](https://voice-observation.github.io/voiceobs/)** | 🐛 [Issues](https://github.com/voice-observation/voiceobs/issues) | 💬 [Discussions](https://github.com/voice-observation/voiceobs/discussions)

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

- 🎯 **Turn-based tracking** - Every user and agent turn as an OpenTelemetry span
- ⚡ **Stage-level latency** - Track ASR, LLM, and TTS separately
- 🔍 **Failure detection** - Automatic detection of interruptions, high latency, and errors
- 📊 **CLI analysis** - Analyze, compare, and generate reports from trace files
- 🖥️ **REST API server** - Centralized observability for teams
- 🔌 **Framework integrations** - Out-of-box support for LiveKit, Vocode, and more
- ⚙️ **Zero config** - Works out of the box, configure as needed
- 📈 **CI/CD ready** - Regression detection for voice AI pipelines

## Installation

```bash
pip install voiceobs
```

**Requirements:** Python 3.9+

For complete documentation, examples, API reference, and more, visit the **[documentation website](https://voice-observation.github.io/voiceobs/)**.

## License

Apache-2.0 - see [LICENSE](LICENSE) for details.
