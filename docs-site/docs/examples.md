# Examples

Complete, runnable examples demonstrating voiceobs features.

## Available Examples

| Example | Description | Location |
|---------|-------------|----------|
| [voice_pipeline](https://github.com/voice-observation/voiceobs/tree/main/examples/voice_pipeline) | Complete voice chat with ASR (Deepgram), LLM (Gemini), TTS (Cartesia) | `examples/voice_pipeline/` |
| [overlap_detection](https://github.com/voice-observation/voiceobs/tree/main/examples/overlap_detection) | Demonstrates barge-in and overlap/interruption detection | `examples/overlap_detection/` |
| [livekit](https://github.com/voice-observation/voiceobs/tree/main/examples/livekit) | LiveKit Agents integration example | `examples/livekit/` |
| [vocode](https://github.com/voice-observation/voiceobs/tree/main/examples/vocode) | Vocode integration example | `examples/vocode/` |

## Quick Start

Each example includes:
- Setup instructions
- API key configuration
- Runnable code demonstrating voiceobs features

### Running an Example

1. Clone the repository:
```bash
git clone https://github.com/voice-observation/voiceobs.git
cd voiceobs
```

2. Navigate to an example:
```bash
cd examples/voice_pipeline
```

3. Install dependencies:
```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys
```

5. Run the example:
```bash
# Using uv
uv run python run.py

# Or using pip
python run.py
```

## Example: Voice Pipeline

Complete voice chat application with:
- ASR using Deepgram
- LLM using Google Gemini
- TTS using Cartesia
- Full voiceobs instrumentation

See [examples/voice_pipeline/README.md](https://github.com/voice-observation/voiceobs/tree/main/examples/voice_pipeline/README.md) for details.

## Example: Overlap Detection

Demonstrates:
- Barge-in detection
- Overlap measurement
- Interruption detection

See [examples/overlap_detection/README.md](https://github.com/voice-observation/voiceobs/tree/main/examples/overlap_detection/README.md) for details.

## Example: LiveKit Integration

Shows how to integrate voiceobs with LiveKit Agents:
- Auto-instrumentation
- Turn tracking
- Stage latency measurement

See [examples/livekit/README.md](https://github.com/voice-observation/voiceobs/tree/main/examples/livekit/README.md) for details.

## Example: Vocode Integration

Shows how to integrate voiceobs with Vocode:
- Conversation tracking
- Turn instrumentation
- Analysis integration

See [examples/vocode/README.md](https://github.com/voice-observation/voiceobs/tree/main/examples/vocode/README.md) for details.

## Contributing Examples

We welcome example contributions! See [CONTRIBUTING.md](https://github.com/voice-observation/voiceobs/blob/main/CONTRIBUTING.md) for guidelines.

## Next Steps

- [Overview](./overview.md)
- [Installation](./installation.md)
- [Integrations](./integrations.md)
