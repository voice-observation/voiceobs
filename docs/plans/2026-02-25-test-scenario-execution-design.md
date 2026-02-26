# Test Scenario Execution - Design Document

**Author:** Claude
**Date:** 2026-02-25
**Status:** Approved

## Overview

This document describes the design for executing test scenarios against voice AI agents. Users can execute a single scenario or an entire test suite. Executions run in parallel via an SQS-based two-queue pipeline, with dedicated workers for call execution and LLM evaluation. Each execution captures full audio and real-time transcript, which are displayed on the frontend.

## Problem Statement

Test scenarios exist but cannot be executed. Users need to trigger test calls against their voice AI agents, observe results (audio, transcript, pass/fail), and run suites of tests at scale. The system must be scalable (thousands of concurrent executions) and fault-tolerant (retries, no duplicate calls).

## Goals

1. Execute single scenarios or full test suites against voice AI agents
2. Parallel execution via SQS with horizontally scalable workers
3. Capture full audio recording and real-time transcript per execution
4. LLM-based evaluation of conversation quality (pass/fail, score, reasoning)
5. Frontend polling for execution status with audio/transcript display
6. Auto-retry failed executions with dead-letter queue for unrecoverable failures

## Non-Goals

- WebSocket/SSE for real-time status updates (polling is sufficient for MVP)
- Rule-based evaluation (LLM-only for now)
- Scheduling/recurring test runs
- Cross-agent test suites

---

## Design

### Data Model Changes

#### New: TestSuiteRun

Groups all scenario executions from a single trigger. Always created, even for single-scenario runs (uniform code path).

```
test_suite_runs
├── id: UUID (PK)
├── org_id: UUID (FK → organizations)
├── suite_id: UUID (FK → test_suites)
├── status: VARCHAR          # pending → running → completed → failed → cancelled
├── total_scenarios: INT
├── completed_scenarios: INT (default 0)
├── failed_scenarios: INT (default 0)
├── triggered_by: VARCHAR    # user_id or "api"
├── started_at: TIMESTAMP | NULL
├── completed_at: TIMESTAMP | NULL
├── created_at: TIMESTAMP
```

**Status transitions:**
```
pending ──► running ──► completed
                   ──► failed
                   ──► cancelled
```

- Transitions to `running` when the first execution starts calling.
- Transitions to `completed` when all executions reach a terminal state.

#### Updated: TestExecution

Extends the existing stub with audio, transcript, evaluation, and retry tracking.

```
test_executions (updated)
├── id: UUID (PK)
├── org_id: UUID (FK → organizations)
├── suite_run_id: UUID (FK → test_suite_runs)    # NEW
├── scenario_id: UUID (FK → test_scenarios)
├── status: VARCHAR          # pending → queued → calling → evaluating → completed → failed
├── attempt: INT (default 1)                      # NEW - retry tracking
├── max_attempts: INT (default 3)                 # NEW
├── audio_url: VARCHAR | NULL                     # NEW - S3 path to recording
├── transcript: JSONB | NULL                      # NEW - [{role, text, timestamp_ms}]
├── evaluation_result: JSONB | NULL               # NEW - {passed, score, reasoning, criteria}
├── error_message: VARCHAR | NULL                 # NEW
├── started_at: TIMESTAMP | NULL
├── completed_at: TIMESTAMP | NULL
├── duration_seconds: FLOAT | NULL                # NEW
├── created_at: TIMESTAMP
```

**Status flow:**
```
pending → queued (in SQS) → calling (phone call active) → evaluating (LLM eval) → completed/failed
```

---

### API Design

#### Trigger Execution

**Run entire suite:**
```
POST /api/v1/orgs/{org_id}/test-suites/{suite_id}/run
```

Response (202 Accepted):
```json
{
  "suite_run_id": "uuid",
  "status": "pending",
  "total_scenarios": 12
}
```

**Run single scenario:**
```
POST /api/v1/orgs/{org_id}/test-scenarios/{scenario_id}/run
```

Response (202 Accepted):
```json
{
  "suite_run_id": "uuid",
  "status": "pending",
  "total_scenarios": 1
}
```

Both return a `suite_run_id` for polling.

#### Poll Status

**Suite run status (primary polling endpoint):**
```
GET /api/v1/orgs/{org_id}/suite-runs/{suite_run_id}
```

Response:
```json
{
  "id": "uuid",
  "suite_id": "uuid",
  "status": "running",
  "total_scenarios": 12,
  "completed_scenarios": 8,
  "failed_scenarios": 1,
  "started_at": "...",
  "executions": [
    {
      "id": "uuid",
      "scenario_id": "uuid",
      "scenario_name": "Order pizza happy path",
      "status": "completed",
      "audio_url": "https://...",
      "transcript": [...],
      "evaluation_result": {"passed": true, "score": 0.92, "reasoning": "..."},
      "duration_seconds": 45.2
    },
    {
      "id": "uuid",
      "scenario_id": "uuid",
      "scenario_name": "Cancel order angry customer",
      "status": "calling",
      "audio_url": null,
      "transcript": null
    }
  ]
}
```

**Individual execution detail:**
```
GET /api/v1/orgs/{org_id}/executions/{execution_id}
```

**Audio pre-signed URL:**
```
GET /api/v1/orgs/{org_id}/executions/{execution_id}/audio
```

Returns a time-limited pre-signed S3 URL.

#### Cancel a Run

```
POST /api/v1/orgs/{org_id}/suite-runs/{suite_run_id}/cancel
```

Marks pending/queued executions as cancelled. In-progress calls complete naturally.

---

### Two-Queue Pipeline Architecture

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ FastAPI   │────►│ Execution    │────►│ Evaluation   │────►│ Database     │
│ enqueues  │     │ Queue (SQS)  │     │ Queue (SQS)  │     │ + S3         │
└──────────┘     └──────┬───────┘     └──────┬───────┘     └──────────────┘
                        │                     │
                 ┌──────▼───────┐     ┌──────▼───────┐
                 │ Call Workers │     │ Eval Workers │
                 │ (LiveKit/SIP)│     │ (LLM calls)  │
                 └──────────────┘     └──────────────┘
```

**Why two queues:** Call execution and LLM evaluation are fundamentally different workloads. Calls hold live connections and are I/O bound; evaluation is a quick LLM API call. If evaluation fails, we retry evaluation only — no re-dial. Each queue has independent retry/DLQ configuration.

#### Flow

1. **API receives run request** → creates TestSuiteRun + TestExecution rows (status=`pending`) → enqueues one SQS message per scenario to Execution Queue
2. **Call Worker picks up message** → updates status to `calling` → dials agent via LiveKit/SIP → runs persona-driven conversation with real-time Deepgram STT → records audio → uploads to S3 → saves transcript to DB → enqueues message to Evaluation Queue → updates status to `evaluating`
3. **Eval Worker picks up message** → fetches transcript + scenario goal/criteria → calls LLM for evaluation → saves result to DB → updates status to `completed` → increments `completed_scenarios` on suite run
4. **Suite run completion** → when all executions reach terminal state, mark suite run as `completed`

#### Worker Process

Single worker codebase with two async polling loops:

```python
# voiceobs worker start
async def main():
    call_worker = CallWorker(concurrency=10)   # configurable via env
    eval_worker = EvalWorker(concurrency=20)    # LLM calls are lighter
    await asyncio.gather(
        call_worker.poll_loop(),
        eval_worker.poll_loop()
    )
```

Both worker types share the same process but can also be deployed independently for separate scaling.

#### Scaling

- Per-worker concurrency is configurable (default: 10 calls, 20 evals)
- Scale horizontally by adding worker instances
- Auto-scale worker count based on SQS queue depth (CloudWatch alarm → ECS/K8s scaling)
- SQS naturally distributes messages across all polling workers

---

### Call Execution Detail

#### LiveKit AgentSession Setup

Reuses the existing agent verification pattern, extended for full conversations:

1. Fetch TestScenario + Persona + Agent from DB
2. Create LiveKit Room
3. Configure AgentSession:
   - **TTS:** Persona's `tts_provider` + `tts_config` (ElevenLabs/OpenAI/Deepgram)
   - **STT:** Deepgram real-time with speaker diarization
   - **LLM:** Drives persona behavior using scenario goal + persona traits
   - **System prompt:** "You are {persona.name}. Your traits: {traits}. Your goal: {scenario.goal}. Behave naturally."
4. Dial agent via SIP trunk (`agent.contact_info.phone_number`)
5. Run conversation until:
   - Scenario goal achieved (LLM determines)
   - `max_turns` reached
   - Timeout exceeded (`scenario.timeout`, default 120s)
   - Call drops / SIP error
6. Collect: full audio recording, transcript, call metadata (duration, turns, who hung up)
7. Upload audio to S3, save transcript + `audio_url` to DB

#### Persona as Caller

The persona drives the conversation — the LLM acts as the "customer" calling the agent. Inputs:

- **Scenario goal:** What the persona is trying to accomplish
- **Persona traits:** aggression, patience, verbosity levels + trait tags
- **Caller behaviors:** From `test_scenario.caller_behaviors` (e.g., "interrupt after 3 seconds")
- **Max turns:** Hard stop for runaway conversations

#### Audio Recording

- LiveKit composite recording captures both sides of the call
- Stored as single audio file (WAV or MP3) in S3
- Path format: `audio/executions/{org_id}/{suite_run_id}/{execution_id}.wav`

---

### LLM Evaluation

#### Evaluation Flow

1. Fetch transcript, scenario (goal, intent, caller_behaviors), agent context, `evaluation_strictness` from suite
2. Build evaluation prompt with full transcript + success criteria
3. Call `LLMService.generate_structured()` with evaluation schema
4. Save result to `test_execution.evaluation_result`

#### Evaluation Output Schema

```python
class CriterionResult(BaseModel):
    name: str           # e.g., "greeting", "order_confirmation", "tone"
    passed: bool
    score: float        # 0.0 - 1.0
    evidence: str       # Quote from transcript supporting the judgment

class EvaluationResult(BaseModel):
    passed: bool                    # Overall pass/fail
    score: float                    # 0.0 - 1.0
    goal_achieved: bool             # Did the agent fulfill the scenario goal?
    intent_handled: bool            # Did the agent handle the expected intent?
    criteria: list[CriterionResult] # Breakdown by criterion
    reasoning: str                  # LLM's explanation
```

#### Strictness Mapping

- **Strict:** Agent must hit all criteria precisely. Minor deviations = fail.
- **Balanced:** Core criteria must pass, minor issues tolerated.
- **Flexible:** Only major failures (wrong info, call drop, unresponsive) count as fail.

Maps to the existing `evaluation_strictness` field on TestSuite.

---

### Status Polling & Frontend Integration

#### Polling Strategy

- **While `status = running`:** Poll every 3 seconds
- **While `status = pending`:** Poll every 5 seconds
- **Once terminal (`completed`/`failed`/`cancelled`):** Stop polling

#### Execution Status Display

| Status | Frontend Display |
|--------|-----------------|
| `pending` | Queued, waiting |
| `queued` | In queue, about to start |
| `calling` | Live call in progress |
| `evaluating` | Call done, evaluating results |
| `completed` | Audio player + transcript + eval results |
| `failed` | Error message + retry attempt count |

#### Audio & Transcript Display

Once `completed`:
- **Audio:** Fetch pre-signed URL from `/executions/{id}/audio`, render audio player
- **Transcript:** Chat-style view with speaker labels (agent vs persona) and timestamps
- **Evaluation:** Pass/fail badge, score, expandable reasoning + per-criterion breakdown

---

### Failure Handling & Safeguards

#### Failure Scenarios

| Failure | Handling |
|---------|----------|
| SIP dial fails | Retry via SQS (up to 3 attempts). Mark failed after exhaustion. |
| Call drops mid-conversation | Save partial audio/transcript. Retry the full call. |
| LiveKit room creation fails | Retry via SQS. |
| Deepgram STT fails | Call continues, transcript may be incomplete. Flag in result. |
| Audio upload to S3 fails | Retry upload 3x. If still fails, mark execution as failed (transcript still saved). |
| LLM evaluation fails | Retry via Evaluation DLQ. Call results preserved — no re-dial. |
| Worker crashes mid-call | SQS visibility timeout expires → message re-delivered → another worker retries. |
| Suite run cancelled | Pending/queued executions marked cancelled. In-progress calls finish naturally. |

#### Safeguards

- **Idempotency:** Workers check execution status before starting. If already `calling`/`completed`, skip. Prevents duplicate calls on SQS re-delivery.
- **Visibility timeout:** Set to exceed max call duration (5 min) so SQS doesn't re-deliver while a call is active.
- **Dead-letter queues:** Messages that fail all retries go to DLQ. Alert triggers (CloudWatch alarm).
- **Circuit breaker:** If >50% of executions in a suite run fail, pause remaining queued executions and notify user.
- **Concurrency limit per org:** Optional future cap to prevent one org from monopolizing all workers.

#### SQS Configuration

- **Execution Queue:** Visibility timeout = 300s, max receives = 3, DLQ after exhaustion
- **Evaluation Queue:** Visibility timeout = 60s, max receives = 3, DLQ after exhaustion

---

## Error Handling

| Error | Handling |
|-------|----------|
| Agent not found/inactive | 400 on run trigger |
| Suite has no ready scenarios | 400 on run trigger |
| Suite already running | 409 Conflict |
| SQS unavailable | 503, retry enqueue |
| Execution not found | 404 on status poll |
| Suite run not found | 404 on status poll |

---

## Security Considerations

- Audio recordings may contain sensitive conversation data — S3 bucket must be private, pre-signed URLs time-limited
- SQS messages should contain only IDs, not full scenario/agent data (fetched from DB by worker)
- Rate limit run trigger endpoints to prevent abuse
- Org-scoped access control on all endpoints

---

## Future Considerations

1. **WebSocket/SSE for real-time updates** — Replace polling for better UX
2. **Scheduled/recurring runs** — Cron-based test suite execution
3. **Rule-based evaluation** — Complement LLM eval with deterministic checks
4. **Comparative runs** — Run same suite against different agent versions, compare results
5. **Cost tracking** — Track per-execution costs (SIP, LLM, STT, storage)
6. **Concurrency limits per org** — Fair resource allocation in multi-tenant setup

---

## Alternatives Considered

### 1. Single SQS Queue (Execution + Evaluation Combined)
**Rejected:** If evaluation fails, the entire message retries — including re-dialing the agent. Two queues decouple these concerns cleanly.

### 2. In-Process asyncio (No SQS)
**Rejected:** Tasks lost on process restart. Cannot scale horizontally. Not suitable for production workloads.

### 3. Celery + Redis/RabbitMQ
**Rejected:** Heavier to operate than SQS. No advantage over managed SQS for this use case.

### 4. AWS Step Functions
**Rejected:** Significant AWS coupling, complex to develop/test locally, overkill for current needs.

### 5. Lambda per Execution
**Rejected:** LiveKit calls can run 2-5+ minutes. Lambda cold starts and timeout limits (15 min max) make it a poor fit for long-running voice calls.

### 6. No TestSuiteRun (Executions Only)
**Rejected:** Without a parent entity, frontend must aggregate status across individual executions. Two code paths for single vs. suite execution. Uniform suite run model is simpler.

---

## Implementation Plan

See: `docs/plans/2026-02-25-test-scenario-execution.md` (to be created)
