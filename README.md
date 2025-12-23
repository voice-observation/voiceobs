# voiceobs

**Open, vendor-neutral observability for voice AI conversations.**

Voice AI lacks a standardized way to observe and reason about conversations as time-based interactions. This makes production failures hard to detect, explain, and fix.

**voiceobs** provides a simple, OpenTelemetry-native way to instrument voice AI applications, giving you visibility into every conversation turn.

## Goals

- Create an open standard for observing voice AI conversations
- Integrate seamlessly with existing observability ecosystems (OpenTelemetry)
- Make voice interaction failures easy to see, explain, and fix
- Remain vendor-neutral and open source

## Installation

```bash
pip install voiceobs
```

## Quick Start

```python
from voiceobs import voice_conversation, voice_turn

with voice_conversation():
    with voice_turn(actor="user"):
        # Handle user speech
        pass

    with voice_turn(actor="agent"):
        # Generate agent response
        pass
```

## Features (Planned)

- **Conversation Context**: Automatic propagation of conversation IDs
- **Turn Tracking**: Instrument user and agent turns as OpenTelemetry spans
- **Zero Config**: Works out of the box with console output
- **Non-Invasive**: Won't override your existing OpenTelemetry setup

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
