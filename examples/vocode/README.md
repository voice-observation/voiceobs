# Vocode + voiceobs Example

Streaming voice conversation using Vocode with voiceobs observability.

## Setup

1. Copy the environment template and add your API keys:
   ```bash
   cp .env.example .env
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Run the conversation:
   ```bash
   uv run python main.py
   ```

## What Gets Tracked

The voiceobs integration automatically creates spans for:

- **Conversation lifecycle**: Start and end of the session

For detailed stage tracking, use the manual recording API:

```python
instrumented.instrumented.record_stage(stage="asr", provider="deepgram")
instrumented.instrumented.record_stage(stage="llm", provider="openai")
instrumented.instrumented.record_stage(stage="tts", provider="elevenlabs")
```

## Analyzing Results

After running conversations, analyze the traces:

```bash
uv run voiceobs analyze --input voiceobs_run.jsonl
uv run voiceobs report --input voiceobs_run.jsonl --format html --output report.html
```
