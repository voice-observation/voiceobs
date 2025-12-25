# Overlap Detection Example

A voice pipeline demonstrating overlap/interruption detection with voiceobs.

## Overview

This example shows how voiceobs tracks overlap between user and agent speech.
It includes a **barge-in mode** where the agent intentionally interrupts long
user messages to demonstrate overlap detection.

## Key Metrics

| Attribute | Description |
|-----------|-------------|
| `voice.turn.overlap_ms` | Overlap duration (positive = interruption) |
| `voice.interruption.detected` | True if agent started before user finished |

## Setup

### 1. Install Dependencies

```bash
cd examples/overlap_detection
uv sync
```

### 2. Configure API Keys

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Run the Pipeline

**Normal mode** (agent waits for user to finish):
```bash
uv run python run.py
```

**Barge-in mode** (agent interrupts after 2s of speech):
```bash
uv run python run.py --barge-in
```

## How It Works

### Normal Mode
1. User speaks until they pause
2. Agent waits for user to finish
3. Agent responds after processing
4. **Result**: Negative overlap (gap between speakers)

### Barge-in Mode
1. User starts speaking
2. After 2 seconds, agent triggers barge-in
3. The **barge-in timestamp** is captured (user is still speaking!)
4. Agent processes and responds
5. Agent speech_start is marked at the **barge-in timestamp** (not actual playback)
6. **Result**: Positive overlap (agent logically started before user finished)

> **Technical Note**
>
> Since we can't actually play audio while recording, the barge-in example
> *simulates* overlap by using `mark_speech_start(timestamp_ns=barge_in_time)`.
> This backdates the agent's speech start to the moment of barge-in, creating
> the overlap that would occur in a real streaming pipeline.

## Example Output

### Normal Mode
```
[User turn: 2450ms]
[Response latency: 1823ms]
[Agent turn: 2150ms]

✓ Normal turn-taking: 1823ms gap between speakers
```

### Barge-in Mode
```
⚡ BARGE-IN: Agent interrupting!
[User turn: 2000ms]
[Response latency: 0ms]
[Agent turn: 1800ms]

⚠️  OVERLAP DETECTED: Agent interrupted by 500ms
   (Agent started speaking before user finished)
```

## JSONL Export and Analysis

Export traces to analyze overlap patterns:

```bash
# Enable JSONL export
VOICEOBS_JSONL_OUT=./traces.jsonl uv run python run.py --barge-in

# Analyze the traces
voiceobs analyze --input traces.jsonl
```

The analyzer shows interruption rate across all agent turns.

## Limitations

> **Note: Push-to-Talk vs Streaming**
>
> This example simulates barge-in to demonstrate overlap detection.
> In real-world applications:
> - **Push-to-talk**: Overlap is always ≈0 (user must finish first)
> - **Streaming ASR**: Agent can respond while user is still speaking
> - **True barge-in**: Requires concurrent audio processing
