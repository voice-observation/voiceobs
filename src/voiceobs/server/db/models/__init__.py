"""Database models for voiceobs server.

These dataclasses represent rows in the PostgreSQL database tables.
"""

from voiceobs.server.db.models.agent import AgentRow
from voiceobs.server.db.models.conversation import ConversationRow
from voiceobs.server.db.models.failure import FailureRow
from voiceobs.server.db.models.persona import PersonaRow
from voiceobs.server.db.models.span import SpanRow
from voiceobs.server.db.models.test_execution import TestExecutionRow
from voiceobs.server.db.models.test_scenario import TestScenarioRow
from voiceobs.server.db.models.test_suite import TestSuiteRow
from voiceobs.server.db.models.turn import TurnRow

__all__ = [
    "AgentRow",
    "ConversationRow",
    "FailureRow",
    "PersonaRow",
    "SpanRow",
    "TestExecutionRow",
    "TestScenarioRow",
    "TestSuiteRow",
    "TurnRow",
]
