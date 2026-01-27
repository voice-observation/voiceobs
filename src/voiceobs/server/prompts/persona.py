"""Prompt templates for persona-related LLM operations."""

# fmt: off
PERSONA_ATTRIBUTES_PROMPT = """Based on the following persona information, determine appropriate personality attributes and TTS configuration.

Persona Name: {name}
Description: {description}

Please determine:
1. Aggression level (0.0 = passive/submissive, 1.0 = assertive/dominant)
2. Patience level (0.0 = impatient/quick to react, 1.0 = patient/calm)
3. Verbosity level (0.0 = concise/brief, 1.0 = verbose/detailed)
4. Recommended TTS provider (openai, elevenlabs, or deepgram)
5. Recommended TTS model key from the selected provider

Available TTS models:
{available_models}

Return your recommendations as JSON with the following structure:
- aggression: float between 0.0 and 1.0
- patience: float between 0.0 and 1.0
- verbosity: float between 0.0 and 1.0
- tts_provider: one of "openai", "elevenlabs", or "deepgram"
- tts_model_key: a valid model key from the selected provider's models

Consider the persona's name and description when making recommendations. For example:
- A "Friendly Customer Service" persona might have low aggression (0.2), high patience (0.8), and moderate verbosity (0.5)
- A "Technical Support Expert" might have moderate aggression (0.4), high patience (0.7), and high verbosity (0.8)
- A "Sales Representative" might have high aggression (0.7), moderate patience (0.5), and high verbosity (0.8)
"""
# fmt: on
