# Failure Taxonomy

This document defines the canonical failure types for voice conversations in voiceobs. These failures represent common issues that can occur during voice AI interactions.

## Overview

Failures are detected by analyzing span attributes and metrics. Each failure type has:
- **Description**: What the failure means
- **Triggering Signals**: Which span attributes trigger detection
- **Default Threshold**: When the signal indicates a failure
- **Severity Levels**: Low, Medium, High based on magnitude

## Failure Types

### 1. Interruption (`interruption`)

**Description**: Agent started speaking before the user finished speaking. This indicates the agent interrupted the user, which can be jarring and indicates a turn-taking issue.

**Triggering Signals**:
- `voice.turn.overlap_ms` - Positive value indicates interruption
- `voice.interruption.detected` - Boolean flag

**Default Threshold**: `0 ms` (any positive overlap is an interruption)

**Severity Levels**:
| Severity | Condition |
|----------|-----------|
| Low | overlap > 0ms and ≤ 200ms |
| Medium | overlap > 200ms and ≤ 500ms |
| High | overlap > 500ms |

**Example**:
```
Agent started speaking 350ms before user finished
→ interruption (medium severity)
```

---

### 2. Excessive Silence (`excessive_silence`)

**Description**: Too long of a pause between user finishing and agent responding. This makes the conversation feel slow and unresponsive.

**Triggering Signals**:
- `voice.silence.after_user_ms`
- `voice.silence.before_agent_ms`

**Default Threshold**: `3000 ms` (3 seconds)

**Severity Levels**:
| Severity | Condition |
|----------|-----------|
| Low | silence > 3000ms and ≤ 5000ms |
| Medium | silence > 5000ms and ≤ 8000ms |
| High | silence > 8000ms |

**Example**:
```
User finished speaking, agent responded after 6500ms
→ excessive_silence (medium severity)
```

---

### 3. Slow Response (`slow_response`)

**Description**: An individual stage (ASR, LLM, or TTS) took too long to complete. This indicates a performance bottleneck in the pipeline.

**Triggering Signals**:
- `voice.asr.duration_ms` (via stage span)
- `voice.llm.duration_ms` (via stage span)
- `voice.tts.duration_ms` (via stage span)

**Default Threshold**: `2000 ms` per stage

**Severity Levels**:
| Severity | Condition |
|----------|-----------|
| Low | duration > 2000ms and ≤ 3000ms |
| Medium | duration > 3000ms and ≤ 5000ms |
| High | duration > 5000ms |

**Example**:
```
LLM stage took 4200ms to generate response
→ slow_response (medium severity, stage=llm)
```

---

### 4. ASR Low Confidence (`asr_low_confidence`)

**Description**: Speech recognition confidence is below the acceptable threshold. This may indicate poor audio quality, background noise, or unclear speech.

**Triggering Signals**:
- `voice.asr.confidence` (if provider returns confidence)

**Default Threshold**: `0.7` (70% confidence)

**Severity Levels**:
| Severity | Condition |
|----------|-----------|
| Low | confidence < 0.7 and ≥ 0.5 |
| Medium | confidence < 0.5 and ≥ 0.3 |
| High | confidence < 0.3 |

**Example**:
```
Deepgram returned transcript with 45% confidence
→ asr_low_confidence (medium severity)
```

**Note**: This failure type requires the ASR provider to return confidence scores. Not all providers expose this metric.

---

### 5. LLM Incorrect Intent (`llm_incorrect_intent`)

**Description**: The LLM misunderstood the user's intent or provided an incorrect or irrelevant response. This is determined by semantic evaluation (LLM-as-judge).

**Triggering Signals**:
- `eval.intent_correct` (boolean from evaluator)
- `eval.relevance_score` (0-1 from evaluator)

**Default Threshold**: `0.5` (50% relevance)

**Severity Levels**:
| Severity | Condition |
|----------|-----------|
| Low | relevance < 0.5 and ≥ 0.3 |
| Medium | relevance < 0.3 and ≥ 0.1 |
| High | relevance < 0.1 OR intent_correct = false |

**Example**:
```
User asked for weather, agent responded about restaurants
→ llm_incorrect_intent (high severity, relevance=0.05)
```

**Note**: This failure type requires running the semantic evaluator (`voiceobs eval`). It is marked as probabilistic since LLM judgments can vary.

---

### 6. Unknown (`unknown`)

**Description**: An unclassified failure that doesn't match known patterns. This may indicate a new type of issue that needs investigation.

**Triggering Signals**: None (catch-all)

**Default Threshold**: N/A

**Example**:
```
Exception occurred during processing
→ unknown (severity based on context)
```

---

## Configuration Reference

All thresholds are configurable via the `FailureThresholds` class. Here is the complete list of configuration options:

### Failure Detection Thresholds

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `interruption_overlap_ms` | float | `0.0` | Minimum overlap in ms to trigger interruption failure. 0 means any overlap triggers it. |
| `excessive_silence_ms` | float | `3000.0` | Silence duration in ms after which excessive_silence failure is triggered. |
| `slow_asr_ms` | float | `2000.0` | Maximum ASR stage duration in ms before slow_response failure. |
| `slow_llm_ms` | float | `2000.0` | Maximum LLM stage duration in ms before slow_response failure. |
| `slow_tts_ms` | float | `2000.0` | Maximum TTS stage duration in ms before slow_response failure. |
| `asr_min_confidence` | float | `0.7` | Minimum ASR confidence (0-1) before asr_low_confidence failure. |
| `llm_min_relevance` | float | `0.5` | Minimum relevance score (0-1) before llm_incorrect_intent failure. |

### Severity Thresholds

These thresholds determine the boundary between LOW, MEDIUM, and HIGH severity:

#### Interruption Severity
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `interruption_low_max_ms` | float | `200.0` | Max overlap for LOW severity. Above this → MEDIUM. |
| `interruption_medium_max_ms` | float | `500.0` | Max overlap for MEDIUM severity. Above this → HIGH. |

#### Excessive Silence Severity
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `silence_low_max_ms` | float | `5000.0` | Max silence for LOW severity. Above this → MEDIUM. |
| `silence_medium_max_ms` | float | `8000.0` | Max silence for MEDIUM severity. Above this → HIGH. |

#### Slow Response Severity
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `slow_low_max_ms` | float | `3000.0` | Max duration for LOW severity. Above this → MEDIUM. |
| `slow_medium_max_ms` | float | `5000.0` | Max duration for MEDIUM severity. Above this → HIGH. |

### Usage Example

```python
from voiceobs.failures import FailureThresholds

# Create custom thresholds for a more lenient configuration
lenient = FailureThresholds(
    # Detection thresholds
    excessive_silence_ms=5000.0,      # 5s instead of 3s
    slow_asr_ms=3000.0,               # 3s instead of 2s
    slow_llm_ms=4000.0,               # 4s instead of 2s
    slow_tts_ms=3000.0,               # 3s instead of 2s
    asr_min_confidence=0.5,           # 50% instead of 70%

    # Severity thresholds
    silence_low_max_ms=7000.0,        # 7s instead of 5s
    silence_medium_max_ms=12000.0,    # 12s instead of 8s
)

# Create strict thresholds for high-quality requirements
strict = FailureThresholds(
    # Detection thresholds
    excessive_silence_ms=1500.0,      # 1.5s instead of 3s
    slow_asr_ms=1000.0,               # 1s instead of 2s
    slow_llm_ms=1500.0,               # 1.5s instead of 2s
    slow_tts_ms=1000.0,               # 1s instead of 2s
    asr_min_confidence=0.85,          # 85% instead of 70%

    # Severity thresholds
    interruption_low_max_ms=100.0,    # 100ms instead of 200ms
    interruption_medium_max_ms=250.0, # 250ms instead of 500ms
)

# Use with the failure classifier (see Day 2)
# classifier = FailureClassifier(thresholds=strict)
# failures = classifier.classify(spans)
```

### Environment Variable Configuration (Future)

In a future release, thresholds may be configurable via environment variables:

```bash
# Not yet implemented - planned for Week 4
export VOICEOBS_EXCESSIVE_SILENCE_MS=5000
export VOICEOBS_SLOW_LLM_MS=3000
```

---

## Signal Availability

Not all signals are available for every conversation:

| Signal | Availability | How to Enable |
|--------|--------------|---------------|
| `voice.turn.overlap_ms` | Conditional | Call `mark_speech_end()` and `mark_speech_start()` |
| `voice.silence.after_user_ms` | Conditional | Call `mark_speech_end()` and `mark_speech_start()` |
| Stage durations | Always | Use `voice_stage()` context manager |
| `voice.asr.confidence` | Provider-dependent | Check if your ASR provider returns confidence |
| `eval.*` | Conditional | Run semantic evaluator (`voiceobs eval`) |

## Semantic Evaluation: Probabilistic Nature

**Important**: Semantic evaluation metrics (`eval.intent_correct`, `eval.relevance_score`) are generated by LLM-as-judge and are inherently **probabilistic**.

### What This Means

1. **Results may vary between runs**: Running the same evaluation twice may produce slightly different scores
2. **LLM judgment is subjective**: Different LLMs may evaluate the same response differently
3. **Temperature affects consistency**: Higher temperature settings increase variance
4. **Context matters**: Small changes in prompt or context can affect evaluation

### Recommendations

- **Interpret as trends**: Look at aggregate metrics over many evaluations, not individual scores
- **Set reasonable thresholds**: Don't fail CI on minor relevance differences (e.g., 0.78 vs 0.82)
- **Compare relative changes**: Focus on deltas between runs rather than absolute scores

### In Reports

The analyzer report clearly marks semantic evaluation metrics as probabilistic:

```
Semantic Evaluation (probabilistic)
------------------------------
  Note: These metrics come from LLM-as-judge evaluation
  and may vary slightly between runs.

  Evaluated turns: 50
  Intent correct: 92.0%
  Intent failures: 8.0%
  Avg relevance: 0.85
  Relevance range: 0.45 - 0.98
```

---

## Best Practices

1. **Start with defaults**: The default thresholds are reasonable for most applications
2. **Tune based on use case**: Adjust thresholds for your specific requirements
3. **Monitor severity distribution**: Track how many high/medium/low failures occur
4. **Investigate unknowns**: Unknown failures may indicate new issue patterns
5. **Use semantic eval sparingly**: LLM evaluation adds cost and latency
6. **Test threshold changes**: Verify new thresholds against historical data before deploying
7. **Treat eval metrics as probabilistic**: Don't over-rely on exact semantic scores
