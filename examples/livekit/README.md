# LiveKit + voiceobs Example

Voice agent using LiveKit Agents SDK with voiceobs observability.

## Setup

1. Copy the environment template and add your API keys:
   ```bash
   cp .env.example .env
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Run the agent:
   ```bash
   uv run python main.py dev
   ```

## What Gets Tracked

The voiceobs integration automatically creates spans for:

- **Conversation**: Root span for the entire session
- **User turns**: When user speech is committed
- **Agent turns**: When agent speech is committed

## Analyzing Results

After running conversations, analyze the traces:

```bash
uv run voiceobs analyze --input voiceobs_run.jsonl
uv run voiceobs report --input voiceobs_run.jsonl --format html --output report.html
```
