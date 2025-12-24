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
