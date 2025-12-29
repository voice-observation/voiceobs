# JSON Output Schema

This document describes the JSON output schema for voiceobs CLI commands when using the `--json` flag.

## Commands with JSON Output

- `voiceobs analyze --input <file> --json`
- `voiceobs compare --baseline <file> --current <file> --json`
- `voiceobs report --input <file> --format json`

## Analyze Command Schema

The `analyze` command outputs analysis results for a single JSONL trace file.

```json
{
  "summary": {
    "total_spans": 100,
    "total_conversations": 5,
    "total_turns": 20
  },
  "stages": {
    "asr": {
      "stage_type": "asr",
      "count": 15,
      "mean_ms": 150.5,
      "p50_ms": 140.0,
      "p95_ms": 200.0,
      "p99_ms": 250.0
    },
    "llm": {
      "stage_type": "llm",
      "count": 15,
      "mean_ms": 500.0,
      "p50_ms": 450.0,
      "p95_ms": 800.0,
      "p99_ms": 950.0
    },
    "tts": {
      "stage_type": "tts",
      "count": 15,
      "mean_ms": 200.0,
      "p50_ms": 180.0,
      "p95_ms": 300.0,
      "p99_ms": 350.0
    }
  },
  "turns": {
    "silence_samples": 10,
    "silence_mean_ms": 250.0,
    "silence_p95_ms": 400.0,
    "total_agent_turns": 10,
    "interruptions": 1,
    "interruption_rate": 10.0
  },
  "eval": {
    "total_evals": 10,
    "intent_correct_count": 8,
    "intent_incorrect_count": 2,
    "intent_correct_rate": 80.0,
    "intent_failure_rate": 20.0,
    "avg_relevance_score": 0.85,
    "min_relevance_score": 0.6,
    "max_relevance_score": 1.0
  }
}
```

### Field Descriptions

#### Summary
| Field | Type | Description |
|-------|------|-------------|
| `total_spans` | integer | Total number of spans in the trace file |
| `total_conversations` | integer | Number of unique conversations |
| `total_turns` | integer | Number of voice turns |

#### Stages (asr, llm, tts)
| Field | Type | Description |
|-------|------|-------------|
| `stage_type` | string | Stage type ("asr", "llm", "tts") |
| `count` | integer | Number of spans for this stage |
| `mean_ms` | float \| null | Mean duration in milliseconds |
| `p50_ms` | float \| null | Median (50th percentile) duration |
| `p95_ms` | float \| null | 95th percentile duration |
| `p99_ms` | float \| null | 99th percentile duration |

#### Turns
| Field | Type | Description |
|-------|------|-------------|
| `silence_samples` | integer | Number of silence measurements |
| `silence_mean_ms` | float \| null | Mean silence after user turn |
| `silence_p95_ms` | float \| null | 95th percentile silence duration |
| `total_agent_turns` | integer | Total number of agent turns |
| `interruptions` | integer | Number of detected interruptions |
| `interruption_rate` | float \| null | Interruption rate as percentage |

#### Eval (Semantic Evaluation)
| Field | Type | Description |
|-------|------|-------------|
| `total_evals` | integer | Number of evaluated turns |
| `intent_correct_count` | integer | Turns with correct intent |
| `intent_incorrect_count` | integer | Turns with incorrect intent |
| `intent_correct_rate` | float \| null | Intent correctness percentage |
| `intent_failure_rate` | float \| null | Intent failure percentage |
| `avg_relevance_score` | float \| null | Average relevance score (0.0-1.0) |
| `min_relevance_score` | float \| null | Minimum relevance score |
| `max_relevance_score` | float \| null | Maximum relevance score |

## Compare Command Schema

The `compare` command outputs comparison results between baseline and current runs.

```json
{
  "files": {
    "baseline": "baseline.jsonl",
    "current": "current.jsonl"
  },
  "deltas": {
    "asr_p95": {
      "name": "ASR p95",
      "baseline": 200.0,
      "current": 250.0,
      "delta": 50.0,
      "delta_percent": 25.0,
      "unit": "ms",
      "is_regression": true
    },
    "llm_p95": {
      "name": "LLM p95",
      "baseline": 500.0,
      "current": 480.0,
      "delta": -20.0,
      "delta_percent": -4.0,
      "unit": "ms",
      "is_regression": false
    }
  },
  "regressions": [
    {
      "metric": "ASR p95",
      "baseline_value": 200.0,
      "current_value": 250.0,
      "delta": 50.0,
      "delta_percent": 25.0,
      "severity": "warning",
      "description": "ASR p95 latency increased by 25.0%"
    }
  ],
  "has_regressions": true,
  "has_critical_regressions": false
}
```

### Field Descriptions

#### Files
| Field | Type | Description |
|-------|------|-------------|
| `baseline` | string | Path to baseline file |
| `current` | string | Path to current file |

#### Deltas
Each delta object contains:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Metric name |
| `baseline` | float \| null | Baseline value |
| `current` | float \| null | Current value |
| `delta` | float \| null | Absolute change (current - baseline) |
| `delta_percent` | float \| null | Percentage change |
| `unit` | string | Unit of measurement |
| `is_regression` | boolean | Whether this represents a regression |

Available delta keys:
- `asr_p95` - ASR 95th percentile latency
- `llm_p95` - LLM 95th percentile latency
- `tts_p95` - TTS 95th percentile latency
- `silence_mean` - Mean silence after user
- `silence_p95` - 95th percentile silence
- `interruptions` - Interruption count
- `interruption_rate` - Interruption rate
- `intent_correct_rate` - Intent correctness rate
- `avg_relevance` - Average relevance score

#### Regressions
Each regression object contains:

| Field | Type | Description |
|-------|------|-------------|
| `metric` | string | Name of the regressed metric |
| `baseline_value` | float | Baseline value |
| `current_value` | float | Current value |
| `delta` | float | Absolute change |
| `delta_percent` | float | Percentage change |
| `severity` | string | "warning" or "critical" |
| `description` | string | Human-readable description |

#### Top-level Flags
| Field | Type | Description |
|-------|------|-------------|
| `has_regressions` | boolean | True if any regressions detected |
| `has_critical_regressions` | boolean | True if critical regressions detected |

## Report Command (JSON format)

When using `--format json`, the report command outputs the same schema as the analyze command.

```bash
voiceobs report --input run.jsonl --format json
```

## Usage Examples

### Parse analyze output in shell

```bash
# Get LLM p95 latency
voiceobs analyze --input run.jsonl --json | jq '.stages.llm.p95_ms'

# Check if there are any interruptions
voiceobs analyze --input run.jsonl --json | jq '.turns.interruptions'
```

### Parse compare output in shell

```bash
# Check for regressions
voiceobs compare -b baseline.jsonl -c current.jsonl --json | jq '.has_regressions'

# Get all regression descriptions
voiceobs compare -b baseline.jsonl -c current.jsonl --json | jq '.regressions[].description'
```

### Use in CI/CD

```bash
# Fail if any regressions detected
if voiceobs compare -b baseline.jsonl -c current.jsonl --json | jq -e '.has_regressions'; then
  echo "Regressions detected!"
  exit 1
fi
```

## Null Values

Fields that cannot be computed (e.g., no data available) will be `null`:

```json
{
  "stages": {
    "asr": {
      "stage_type": "asr",
      "count": 0,
      "mean_ms": null,
      "p50_ms": null,
      "p95_ms": null,
      "p99_ms": null
    }
  }
}
```

Always check for `null` values before using numeric fields in calculations.
