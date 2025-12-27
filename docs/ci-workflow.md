# CI Workflow Guide

This guide explains how to use voiceobs in a CI/CD pipeline to detect voice AI regressions before shipping.

## Overview

voiceobs provides a local-first workflow for regression detection that requires no hosted services. The workflow is:

1. **Capture baseline** - Record spans from a known-good version
2. **Make changes** - Modify your voice AI code
3. **Capture current** - Record spans from the new version
4. **Compare** - Detect regressions between baseline and current

## Quick Start

```bash
# 1. Capture baseline run (known-good version)
VOICEOBS_JSONL_OUT=baseline.jsonl python your_test_script.py

# 2. Make code changes...

# 3. Capture current run
VOICEOBS_JSONL_OUT=current.jsonl python your_test_script.py

# 4. Compare and fail on regression
voiceobs compare -b baseline.jsonl -c current.jsonl --fail-on-regression
```

## Detailed Workflow

### Step 1: Create a Test Script

Create a script that exercises your voice AI pipeline with consistent test cases:

```python
# test_voice_pipeline.py
from voiceobs import voice_conversation, voice_turn, voice_stage, ensure_tracing_initialized

# Initialize tracing (will use VOICEOBS_JSONL_OUT env var)
ensure_tracing_initialized()

def run_test_conversation():
    """Run a test conversation through the voice pipeline."""
    with voice_conversation() as conv:
        # Simulate user turn
        with voice_turn("user") as turn:
            turn.set_transcript("What's the weather like today?")

        # Simulate agent turn with stages
        with voice_turn("agent") as turn:
            with voice_stage("asr"):
                # Your ASR processing here
                pass

            with voice_stage("llm"):
                # Your LLM processing here
                pass

            with voice_stage("tts"):
                # Your TTS processing here
                pass

            turn.set_transcript("It's sunny and 72 degrees.")

if __name__ == "__main__":
    # Run multiple test conversations for statistical significance
    for i in range(10):
        run_test_conversation()
```

### Step 2: Capture Baseline

Before making changes, capture a baseline from your known-good version:

```bash
# Set the output file
export VOICEOBS_JSONL_OUT=baseline.jsonl

# Run your test script
python test_voice_pipeline.py

# Verify the baseline was captured
voiceobs analyze -i baseline.jsonl
```

**Tip**: Commit your baseline file to version control so it can be used in CI.

### Step 3: Capture Current Run

After making changes, capture the current version:

```bash
export VOICEOBS_JSONL_OUT=current.jsonl
python test_voice_pipeline.py
```

### Step 4: Compare Runs

Compare the baseline and current runs:

```bash
# View comparison report
voiceobs compare -b baseline.jsonl -c current.jsonl

# Fail if regressions detected (for CI)
voiceobs compare -b baseline.jsonl -c current.jsonl --fail-on-regression
```

## Regression Thresholds

voiceobs uses the following default thresholds to detect regressions:

### Latency Regressions

| Metric | Warning | Critical |
|--------|---------|----------|
| ASR/LLM/TTS p95 latency | +10% | +25% |

### Response Latency (Silence)

| Metric | Warning | Critical |
|--------|---------|----------|
| Mean silence after user | +15% | +30% |
| p95 silence after user | +15% | +30% |

### Interruption Rate

| Metric | Warning | Critical |
|--------|---------|----------|
| Interruption rate | +5pp | +15pp |

(pp = percentage points, e.g., 8% → 13% is +5pp)

### Semantic Scores

| Metric | Warning | Critical |
|--------|---------|----------|
| Intent correctness | -5pp | -15pp |
| Avg relevance score | -10% | -20% |

### Custom Thresholds

You can customize thresholds programmatically:

```python
from voiceobs.compare import RegressionThresholds, compare_runs
from voiceobs.analyzer import analyze_file

# Stricter thresholds for production
strict = RegressionThresholds(
    latency_warning_pct=5.0,      # 5% instead of 10%
    latency_critical_pct=15.0,    # 15% instead of 25%
    silence_warning_pct=10.0,     # 10% instead of 15%
    silence_critical_pct=20.0,    # 20% instead of 30%
)

baseline = analyze_file("baseline.jsonl")
current = analyze_file("current.jsonl")

result = compare_runs(baseline, current, thresholds=strict)
if result.has_regressions:
    print("Regression detected!")
    exit(1)
```

## GitHub Actions Example

Here's a complete GitHub Actions workflow for regression detection:

```yaml
# .github/workflows/voice-regression.yml
name: Voice AI Regression Test

on:
  pull_request:
    branches: [main]

jobs:
  regression-test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install voiceobs
          pip install -r requirements.txt

      # Option 1: Use committed baseline
      - name: Run regression test (committed baseline)
        run: |
          # Capture current run
          VOICEOBS_JSONL_OUT=current.jsonl python test_voice_pipeline.py

          # Compare against committed baseline
          voiceobs compare -b baseline.jsonl -c current.jsonl --fail-on-regression

      # Option 2: Generate baseline from main branch
      # - name: Checkout main for baseline
      #   run: |
      #     git fetch origin main
      #     git checkout origin/main -- src/
      #     VOICEOBS_JSONL_OUT=baseline.jsonl python test_voice_pipeline.py
      #     git checkout HEAD -- src/
      #
      # - name: Capture current and compare
      #   run: |
      #     VOICEOBS_JSONL_OUT=current.jsonl python test_voice_pipeline.py
      #     voiceobs compare -b baseline.jsonl -c current.jsonl --fail-on-regression
```

## GitLab CI Example

```yaml
# .gitlab-ci.yml
voice-regression:
  stage: test
  image: python:3.11
  script:
    - pip install voiceobs
    - pip install -r requirements.txt
    - VOICEOBS_JSONL_OUT=current.jsonl python test_voice_pipeline.py
    - voiceobs compare -b baseline.jsonl -c current.jsonl --fail-on-regression
  only:
    - merge_requests
```

## Best Practices

### 1. Use Consistent Test Cases

Run the same test conversations for baseline and current to ensure fair comparison:

```python
TEST_CASES = [
    ("What's the weather?", "get_weather"),
    ("Set a timer for 5 minutes", "set_timer"),
    ("Play some music", "play_music"),
]

for user_input, expected_intent in TEST_CASES:
    run_conversation(user_input, expected_intent)
```

### 2. Run Multiple Iterations

Single runs can be noisy. Run multiple iterations for statistical significance:

```bash
# Run 10 iterations
for i in $(seq 1 10); do
    python test_voice_pipeline.py
done
```

### 3. Commit Your Baseline

Keep your baseline in version control:

```bash
# Add baseline to git
git add baseline.jsonl
git commit -m "Update voice regression baseline"
```

### 4. Update Baseline Intentionally

When you intentionally change performance characteristics:

```bash
# After intentional changes, update baseline
VOICEOBS_JSONL_OUT=baseline.jsonl python test_voice_pipeline.py
git add baseline.jsonl
git commit -m "Update baseline: improved LLM latency"
```

### 5. Use Semantic Evaluation for Intent Testing

For semantic regressions, run the evaluator after capturing spans:

```python
from voiceobs.eval import SemanticEvaluator, EvalConfig, EvalInput

evaluator = SemanticEvaluator(EvalConfig())

# Evaluate each turn
result = evaluator.evaluate(EvalInput(
    user_transcript="What's the weather?",
    agent_response="It's sunny and 72 degrees.",
    expected_intent="get_weather",
))

if not result.passed:
    print(f"Semantic failure: {result.explanation}")
```

## Troubleshooting

### No Regressions Detected But Performance Seems Worse

- Check if you're running enough iterations for statistical significance
- Verify both runs use the same test cases
- Look at absolute numbers in the report, not just regression flags

### False Positives (Regressions on Good Changes)

- Adjust thresholds using `RegressionThresholds`
- Ensure test environment is consistent (same machine, no competing processes)
- Consider running tests in isolated containers

### JSONL File Not Created

- Ensure `VOICEOBS_JSONL_OUT` is set before importing voiceobs
- Call `ensure_tracing_initialized()` in your script
- Check file permissions for the output path

## Summary

The voiceobs CI workflow provides:

- **Local-first**: No hosted services required
- **Deterministic**: Rule-based regression detection
- **Configurable**: Adjustable thresholds
- **CI-ready**: Works with GitHub Actions, GitLab CI, etc.
- **Semantic-aware**: Optional LLM-as-judge evaluation

Use `voiceobs compare --fail-on-regression` in your CI pipeline to catch voice AI regressions before they reach production.
