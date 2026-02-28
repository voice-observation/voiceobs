"""Prompt templates for test execution evaluation."""

EVALUATION_PROMPT_TEMPLATE = """Evaluate this voice conversation between a caller (persona) and an agent.

## Transcript
{transcript}

## Success Criteria
- Scenario goal: {scenario_goal}
{intent_section}
{behaviors_section}

## Evaluation Instructions
{guidance}

Assess whether the agent fulfilled the scenario goal, handled the expected intent,
and met the success criteria. Provide per-criterion breakdown with evidence."""

STRICTNESS_GUIDANCE = {
    "strict": (
        "Be strict: the agent must hit all criteria precisely. Minor deviations count as failure."
    ),
    "balanced": ("Be balanced: core criteria must pass, minor issues are tolerated."),
    "flexible": (
        "Be flexible: only major failures (wrong info, call drop, unresponsive) count as failure."
    ),
}
