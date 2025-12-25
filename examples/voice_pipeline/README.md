# Voice Pipeline Example

A simple voice chat pipeline demonstrating voiceobs instrumentation with stage-level spans for ASR, LLM, and TTS operations.

## Overview

This example shows how to instrument a complete voice pipeline:

1. **User Turn**: Record audio with VAD, transcribe with Deepgram
2. **Agent Turn**: Generate response with Gemini, synthesize with Cartesia

Each stage (ASR, LLM, TTS) is wrapped with `voice_stage()` to capture timing and metadata.

## Setup

### 1. Install Dependencies

```bash
cd examples/voice_pipeline
uv sync
```

Note: This example requires Python 3.11+ and a working microphone.

### 2. Configure API Keys

Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```

Edit `.env`:

```
DEEPGRAM_API_KEY=your_deepgram_api_key
GOOGLE_API_KEY=your_google_api_key
CARTESIA_API_KEY=your_cartesia_api_key
```

### 3. Run the Pipeline

```bash
uv run python run.py
```

## Usage

1. Press Enter to start recording
2. Speak your message
3. Wait for silence detection (1 second of silence stops recording)
4. The AI will respond with synthesized speech
5. Press Ctrl+C to exit

## Observability Output

The pipeline emits OpenTelemetry spans to the console:

```
voice.conversation
├── voice.turn (actor=user)
│   └── voice.asr (provider=deepgram, model=nova-2)
└── voice.turn (actor=agent)
    ├── voice.llm (provider=google, model=gemini-2.0-flash)
    └── voice.tts (provider=cartesia, model=sonic-3)
```

### Stage Span Attributes

Each stage span includes:

| Attribute | Description |
|-----------|-------------|
| `voice.stage.type` | Stage type: "asr", "llm", or "tts" |
| `voice.stage.provider` | Service provider (e.g., "deepgram") |
| `voice.stage.model` | Model identifier (e.g., "nova-2") |
| `voice.stage.input_size` | Input size in bytes/characters |
| `voice.stage.output_size` | Output size in bytes/characters |
| `voice.stage.error` | Error message if the stage failed |

### Turn Timing Attributes

Agent turn spans include response latency metrics:

| Attribute | Description |
|-----------|-------------|
| `voice.silence.after_user_ms` | Response latency: time from user speech end to agent speech start |
| `voice.silence.before_agent_ms` | Same value as above (alias for clarity from agent's perspective) |

### Accurate Response Latency Measurement

For accurate latency measurement, use the speech event markers:

```python
from voiceobs import mark_speech_end, mark_speech_start

with voice_turn("user"):
    audio = record_audio()
    mark_speech_end()  # Call when user stops speaking
    transcript = transcribe(audio)

with voice_turn("agent"):
    response = generate_response(transcript)
    audio = synthesize(response)
    mark_speech_start()  # Call just before playing audio
    play_audio(audio)
```

This measures the actual user-perceived latency:
- **Without markers**: Falls back to measuring gap between turn context boundaries (~0ms)
- **With markers**: Measures from user speech end to agent speech start (includes ASR + LLM + TTS latency)

### Runtime Timing Output

The example prints timing metrics during execution:

```
[Conversation: abc123...]
Listening... (speak now, recording will stop when you pause)
Recording finished.
Transcribing with Deepgram...

User: Hello, how are you?
[User turn duration: 2450ms]
Generating response with Gemini...

AI: I'm doing well, thank you for asking!
Synthesizing speech with Cartesia...
[Response latency: 1823ms]
[Agent turn duration: 2150ms]

[Conversation ended]
```

## JSONL Export and Analysis

Export traces to a JSONL file for offline analysis:

### Enable JSONL Export

Set the `VOICEOBS_JSONL_OUT` environment variable:

```bash
VOICEOBS_JSONL_OUT=./traces.jsonl uv run python run.py
```

This creates a `traces.jsonl` file with one span per line.

### Analyze Traces

Use the `voiceobs analyze` command to compute latency metrics:

```bash
voiceobs analyze --input traces.jsonl
```

Example output:

```
voiceobs Analysis Report
==================================================

Summary
------------------------------
  Total spans: 11
  Conversations: 1
  Turns: 4

Stage Latencies (ms)
------------------------------
  ASR (n=2):
    mean: 165.2
    p50:  165.2
    p95:  180.0
    p99:  180.0
  LLM (n=2):
    mean: 785.0
    p50:  785.0
    p95:  850.0
    p99:  850.0
  TTS (n=2):
    mean: 300.0
    p50:  300.0
    p95:  320.0
    p99:  320.0

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

## Example Trace Output

```json
{
    "name": "voice.asr",
    "kind": "SpanKind.CLIENT",
    "attributes": {
        "voice.schema.version": "0.0.1",
        "voice.conversation.id": "abc123...",
        "voice.stage.type": "asr",
        "voice.stage.provider": "deepgram",
        "voice.stage.model": "nova-2",
        "voice.stage.input_size": 32000,
        "voice.stage.output_size": 42
    }
}
```
