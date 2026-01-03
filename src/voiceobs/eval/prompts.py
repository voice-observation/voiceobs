"""Prompt templates for scenario generation."""

# fmt: off
DISCOVERY_PROMPT = """You are an expert at generating diverse test scenarios for voice AI agents. \
Your task is to create realistic, varied scenarios that test different aspects of agent behavior, \
including edge cases and stress conditions.

## Agent Description
{agent_description}

## Your Task
Generate exactly {count} diverse JSON scenarios for testing this agent. \
Each scenario should include:

1. **name**: A descriptive name for the scenario \
   (e.g., "Urgent Appointment Request")
2. **goal**: The user's primary objective in this scenario \
   (e.g., "Schedule appointment within 24 hours")
3. **persona**: User personality traits:
   - **name**: User's name (e.g., "John", "Sarah")
   - **gender**: User's gender (e.g., "male", "female", "non-binary", "prefer not to say")
   - **age**: User's age (integer, typically 18-100)
   - **aggression**: How aggressive/frustrated the user is (0.0 = calm, 1.0 = very aggressive)
   - **patience**: How patient the user is (0.0 = impatient, 1.0 = very patient)
   - **verbosity**: How verbose/detailed the user speaks (0.0 = brief, 1.0 = very detailed). \
     Example: High verbosity (0.8): You speak in detail
4. **edge_cases**: A list of edge cases this scenario should test. Must include at least one of:
   - "barge_in": User interrupts the agent mid-sentence
   - "silence": User has long pauses or doesn't respond promptly
   - "interruption": User frequently interrupts
   - "stress": High-stress situation requiring urgent handling
   - "confusion": User is confused or unclear
   - Or empty list [] if no specific edge cases

## Requirements
- Ensure scenarios are diverse (different goals, personas, edge cases)
{edge_case_requirements}
- Persona aggression, patience, and verbosity values must be between 0.0 and 1.0
- Edge cases should be realistic and relevant to the agent's domain

## Output Format
Return a JSON array of scenarios matching the structure above."""
# fmt: on


def build_discovery_prompt(agent_description: str, count: int) -> str:
    """Build the discovery prompt for scenario generation.

    Args:
        agent_description: One-sentence description of the agent.
        count: Number of scenarios to generate.

    Returns:
        The formatted prompt string.
    """
    # Build edge case requirements based on count
    edge_case_requirements = []
    if count >= 4:
        edge_case_requirements.append("- Include at least 2 scenarios that test barge-in behavior")
        edge_case_requirements.append("- Include at least 1 scenario that tests silence handling")
        edge_case_requirements.append(
            "- Include at least 1 stress scenario (high urgency/aggression)"
        )
    elif count >= 3:
        edge_case_requirements.append("- Include at least 1 scenario that tests barge-in behavior")
        edge_case_requirements.append("- Include at least 1 scenario that tests silence handling")
    elif count >= 2:
        edge_case_requirements.append(
            "- Include at least 1 scenario that tests an edge case "
            "(barge-in, silence, or stress)"
        )
    else:
        edge_case_requirements.append("- Include edge cases when appropriate for the scenario")

    edge_case_requirements_str = "\n".join(edge_case_requirements) if edge_case_requirements else ""

    return DISCOVERY_PROMPT.format(
        agent_description=agent_description,
        count=count,
        edge_case_requirements=edge_case_requirements_str,
    )
