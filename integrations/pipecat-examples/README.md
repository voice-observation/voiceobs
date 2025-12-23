# voiceobs + Pipecat Integration

This integration demonstrates how to add voice turn observability to [Pipecat](https://github.com/pipecat-ai/pipecat) voice agents using voiceobs.

## Overview

voiceobs instruments your Pipecat pipeline to emit OpenTelemetry spans for each voice turn:
- **User turns**: Tracked when transcription frames are received
- **Agent turns**: Tracked when the bot starts/stops speaking
- **Conversations**: Wrap entire sessions for correlation

## Quick Start

### 1. Install voiceobs

```bash
pip install voiceobs
```

### 2. Add voiceobs to your bot

```python
from voiceobs import ensure_tracing_initialized, voice_conversation, voice_turn

# Initialize tracing at startup
ensure_tracing_initialized()
```

### 3. Create Frame Processors for Turn Tracking

```python
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection
from pipecat.frames.frames import (
    TranscriptionFrame,
    BotStartedSpeakingFrame,
    BotStoppedSpeakingFrame,
)

class VoiceObsUserTurnTracker(FrameProcessor):
    """Tracks user turns from transcription frames."""

    def __init__(self):
        super().__init__()
        self._user_turn_context = None

    async def process_frame(self, frame, direction):
        await super().process_frame(frame, direction)

        if isinstance(frame, TranscriptionFrame):
            # End previous turn
            if self._user_turn_context:
                self._user_turn_context.__exit__(None, None, None)

            # Start new user turn
            self._user_turn_context = voice_turn("user")
            self._user_turn_context.__enter__()

        await self.push_frame(frame, direction)


class VoiceObsAgentTurnTracker(FrameProcessor):
    """Tracks agent turns from speaking frames."""

    def __init__(self):
        super().__init__()
        self._agent_turn_context = None

    async def process_frame(self, frame, direction):
        await super().process_frame(frame, direction)

        if isinstance(frame, BotStartedSpeakingFrame):
            if not self._agent_turn_context:
                self._agent_turn_context = voice_turn("agent")
                self._agent_turn_context.__enter__()

        elif isinstance(frame, BotStoppedSpeakingFrame):
            if self._agent_turn_context:
                self._agent_turn_context.__exit__(None, None, None)
                self._agent_turn_context = None

        await self.push_frame(frame, direction)
```

### 4. Add Trackers to Your Pipeline

```python
user_tracker = VoiceObsUserTurnTracker()
agent_tracker = VoiceObsAgentTurnTracker()

pipeline = Pipeline([
    transport.input(),
    user_tracker,      # Track user turns
    # ... your processors ...
    agent_tracker,     # Track agent turns
    transport.output(),
])
```

### 5. Wrap the Conversation

```python
async def run_bot(transport):
    # Start conversation tracking
    conversation_ctx = voice_conversation()
    conv = conversation_ctx.__enter__()

    # ... setup pipeline and run ...

    @transport.event_handler("on_client_disconnected")
    async def on_disconnect(transport, client):
        # End conversation tracking
        conversation_ctx.__exit__(None, None, None)
        await task.cancel()
```

## Files

- `bot-openai-voiceobs.py` - Complete instrumented example based on simple-chatbot
- `patch/0001-add-voiceobs-turn-spans.patch` - Diff showing the changes

## Example Output

When running with voiceobs, you'll see spans like:

```json
{
    "name": "voice.turn",
    "attributes": {
        "voice.schema.version": "0.0.1",
        "voice.conversation.id": "abc123-...",
        "voice.turn.id": "def456-...",
        "voice.turn.index": 0,
        "voice.actor": "user"
    }
}
```

## Running the Example

1. Clone pipecat-examples:
   ```bash
   git clone https://github.com/pipecat-ai/pipecat-examples.git
   ```

2. Copy the instrumented bot:
   ```bash
   cp bot-openai-voiceobs.py pipecat-examples/
   ```

3. Set up environment variables:
   ```bash
   export OPENAI_API_KEY=your-key
   export ELEVENLABS_API_KEY=your-key
   ```

4. Run the bot:
   ```bash
   cd pipecat-examples
   python bot-openai-voiceobs.py
   ```

Spans will be printed to the console showing each voice turn.

## Exporting to Other Backends

To export spans to Jaeger, OTLP, or other backends, configure OpenTelemetry before calling `ensure_tracing_initialized()`:

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Configure your exporter
provider = TracerProvider()
exporter = OTLPSpanExporter(endpoint="http://localhost:4317")
provider.add_span_processor(BatchSpanProcessor(exporter))
trace.set_tracer_provider(provider)

# voiceobs will detect and use your provider
from voiceobs import ensure_tracing_initialized
ensure_tracing_initialized()  # Returns False, keeps your config
```

## Span Attributes

Each `voice.turn` span includes:

| Attribute | Description |
|-----------|-------------|
| `voice.schema.version` | voiceobs schema version (0.0.1) |
| `voice.conversation.id` | UUID identifying the conversation |
| `voice.turn.id` | UUID identifying this turn |
| `voice.turn.index` | Sequential turn number (0, 1, 2...) |
| `voice.actor` | Who is speaking: "user", "agent", or "system" |
