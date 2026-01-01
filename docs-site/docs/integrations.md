# Integrations

voiceobs provides out-of-box support for popular voice AI frameworks.

## Supported Integrations

| Framework | Status | Documentation |
|-----------|--------|---------------|
| [LiveKit Agents](https://livekit.io/) | ✅ Supported | [LiveKit Integration](#livekit-agents) |
| [Vocode](https://vocode.dev/) | ✅ Supported | [Vocode Integration](#vocode) |

## LiveKit Agents

Auto-instrument LiveKit voice pipelines with voiceobs.

### Installation

```bash
pip install voiceobs
```

### Usage

```python
from voiceobs.integrations.livekit import instrument_livekit_agent

# Instrument your LiveKit agent
instrument_livekit_agent(agent)
```

See [examples/livekit/](https://github.com/voice-observation/voiceobs/tree/main/examples/livekit) for a complete example.

## Vocode

Auto-instrument Vocode conversations.

### Installation

```bash
pip install voiceobs
```

### Usage

```python
from voiceobs.integrations.vocode import instrument_vocode_conversation

# Instrument your Vocode conversation
instrument_vocode_conversation(conversation)
```

See [examples/vocode/](https://github.com/voice-observation/voiceobs/tree/main/examples/vocode) for a complete example.

## Custom Integration

To integrate voiceobs with other frameworks:

1. Use `voice_conversation()` to wrap conversations
2. Use `voice_turn()` to track turns
3. Use `voice_stage()` to track pipeline stages

Example:

```python
from voiceobs import voice_conversation, voice_turn, voice_stage

def my_voice_handler():
    with voice_conversation() as conv:
        # User turn
        with voice_turn("user"):
            transcript = transcribe_audio(audio)

        # Agent turn with stages
        with voice_turn("agent"):
            with voice_stage("asr"):
                # ASR processing
                pass

            with voice_stage("llm"):
                # LLM processing
                response = generate_response(transcript)

            with voice_stage("tts"):
                # TTS processing
                synthesize_speech(response)
```

## Next Steps

- [Overview](./overview.md)
- [Examples](./examples.md)
- [API Reference](./api/json-schema.md)
