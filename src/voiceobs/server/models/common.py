"""Common/shared models for the voiceobs server API."""

from pydantic import BaseModel, ConfigDict


class SpanAttributes(BaseModel):
    """Attributes for a span."""

    # Allow any additional attributes
    model_config = ConfigDict(extra="allow")
