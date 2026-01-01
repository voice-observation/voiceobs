"""Exporters package for voiceobs."""

from voiceobs.exporters.exporters import (
    JSONLSpanExporter,
    get_jsonl_exporter_from_config,
)

try:
    from voiceobs.exporters.otlp import (
        OTLPSpanExporter,
        get_otlp_exporter_from_config,
    )

    __all__ = [
        "JSONLSpanExporter",
        "get_jsonl_exporter_from_config",
        "OTLPSpanExporter",
        "get_otlp_exporter_from_config",
    ]
except ImportError:
    # OTLP dependencies not installed
    __all__ = ["JSONLSpanExporter", "get_jsonl_exporter_from_config"]
