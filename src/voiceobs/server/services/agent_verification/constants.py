"""Constants for agent verification."""

# Room configuration
DEFAULT_ROOM_EMPTY_TIMEOUT = 120
DEFAULT_MAX_PARTICIPANTS = 5

# Conversation limits
MIN_VERIFICATION_TURNS = 2
MAX_CONVERSATION_WAIT_SECONDS = 30

# Provider models (can be overridden via config)
DEFAULT_LLM_MODEL = "gpt-4o-mini"
DEFAULT_TTS_MODEL = "eleven_flash_v2_5"
DEFAULT_TTS_STREAMING_LATENCY = 3

# Participant naming
VERIFIER_AGENT_IDENTITY = "verifier-agent"
SIP_PARTICIPANT_PREFIX = "sip_"

# Room naming
ROOM_NAME_PREFIX = "verify"
