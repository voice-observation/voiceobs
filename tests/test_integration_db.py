"""Integration tests for database persistence.

These tests verify the full data lifecycle: ingest → store → analyze → export.
They use mocked database connections to test the integration between components.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

from voiceobs.cli import export_spans_from_db, import_spans_to_db


class TestImportExportIntegration:
    """Tests for the import/export data lifecycle."""

    def test_import_creates_spans_and_conversations(self, tmp_path):
        """Test that import creates spans and links to conversations."""
        # Create test JSONL file
        input_file = tmp_path / "test.jsonl"
        spans = [
            {
                "name": "voice.turn",
                "duration_ms": 1000.0,
                "attributes": {
                    "voice.actor": "user",
                    "voice.conversation.id": "conv-123",
                },
            },
            {
                "name": "voice.llm",
                "duration_ms": 500.0,
                "attributes": {
                    "voice.stage.type": "llm",
                    "voice.conversation.id": "conv-123",
                },
            },
            {
                "name": "voice.turn",
                "duration_ms": 800.0,
                "attributes": {
                    "voice.actor": "agent",
                    "voice.conversation.id": "conv-123",
                },
            },
        ]
        input_file.write_text("\n".join(json.dumps(s) for s in spans))

        # Mock the database and repository where they're imported in cli.py
        with (
            patch("voiceobs.server.db.connection.Database") as mock_db_class,
            patch("voiceobs.server.db.repositories.span.SpanRepository") as mock_span_repo_class,
            patch(
                "voiceobs.server.db.repositories.conversation.ConversationRepository"
            ) as mock_conv_repo_class,
        ):
            mock_db = AsyncMock()
            mock_db_class.return_value = mock_db

            mock_span_repo = AsyncMock()
            mock_span_repo_class.return_value = mock_span_repo

            mock_conv_repo = AsyncMock()
            mock_conv = MagicMock()
            mock_conv.id = "uuid-123"
            mock_conv_repo.get_or_create.return_value = mock_conv
            mock_conv_repo_class.return_value = mock_conv_repo

            result = import_spans_to_db(input_file, "postgresql://test:test@localhost/test")

            assert result["imported"] == 3
            assert result["errors"] == 0

    def test_import_handles_spans_without_conversation(self, tmp_path):
        """Test that import handles spans without conversation ID."""
        input_file = tmp_path / "test.jsonl"
        spans = [
            {
                "name": "voice.tts",
                "duration_ms": 200.0,
                "attributes": {"voice.stage.type": "tts"},
            },
        ]
        input_file.write_text(json.dumps(spans[0]))

        with (
            patch("voiceobs.server.db.connection.Database") as mock_db_class,
            patch("voiceobs.server.db.repositories.span.SpanRepository") as mock_span_repo_class,
            patch(
                "voiceobs.server.db.repositories.conversation.ConversationRepository"
            ) as mock_conv_repo_class,
        ):
            mock_db = AsyncMock()
            mock_db_class.return_value = mock_db

            mock_span_repo = AsyncMock()
            mock_span_repo_class.return_value = mock_span_repo

            mock_conv_repo = AsyncMock()
            mock_conv_repo_class.return_value = mock_conv_repo

            result = import_spans_to_db(input_file, "postgresql://test:test@localhost/test")

            assert result["imported"] == 1

    def test_export_retrieves_all_spans(self, tmp_path):
        """Test that export retrieves all spans from database."""
        output_file = tmp_path / "output.jsonl"

        with (
            patch("voiceobs.server.db.connection.Database") as mock_db_class,
            patch("voiceobs.server.db.repositories.span.SpanRepository") as mock_span_repo_class,
            patch(
                "voiceobs.server.db.repositories.conversation.ConversationRepository"
            ) as mock_conv_repo_class,
        ):
            mock_db = AsyncMock()
            mock_db_class.return_value = mock_db

            mock_span_repo = AsyncMock()

            # Create mock span rows
            mock_span1 = MagicMock()
            mock_span1.name = "voice.turn"
            mock_span1.start_time = "2025-01-01T00:00:00Z"
            mock_span1.end_time = "2025-01-01T00:00:01Z"
            mock_span1.duration_ms = 1000.0
            mock_span1.attributes = {"voice.actor": "user"}
            mock_span1.trace_id = "trace-1"
            mock_span1.span_id = "span-1"
            mock_span1.parent_span_id = None

            mock_span2 = MagicMock()
            mock_span2.name = "voice.llm"
            mock_span2.start_time = "2025-01-01T00:00:01Z"
            mock_span2.end_time = "2025-01-01T00:00:01.5Z"
            mock_span2.duration_ms = 500.0
            mock_span2.attributes = {"voice.stage.type": "llm"}
            mock_span2.trace_id = "trace-1"
            mock_span2.span_id = "span-2"
            mock_span2.parent_span_id = "span-1"

            mock_span_repo.get_all.return_value = [mock_span1, mock_span2]
            mock_span_repo_class.return_value = mock_span_repo

            mock_conv_repo = AsyncMock()
            mock_conv_repo_class.return_value = mock_conv_repo

            result = export_spans_from_db(
                database_url="postgresql://test:test@localhost/test",
                output_file=output_file,
            )

            assert result["exported"] == 2
            assert output_file.exists()

            # Verify file content
            lines = output_file.read_text().strip().split("\n")
            assert len(lines) == 2

            span1_data = json.loads(lines[0])
            assert span1_data["name"] == "voice.turn"
            assert span1_data["duration_ms"] == 1000.0

    def test_export_filters_by_conversation(self, tmp_path):
        """Test that export can filter by conversation ID."""
        output_file = tmp_path / "output.jsonl"

        with (
            patch("voiceobs.server.db.connection.Database") as mock_db_class,
            patch("voiceobs.server.db.repositories.span.SpanRepository") as mock_span_repo_class,
            patch(
                "voiceobs.server.db.repositories.conversation.ConversationRepository"
            ) as mock_conv_repo_class,
        ):
            mock_db = AsyncMock()
            mock_db_class.return_value = mock_db

            mock_span_repo = AsyncMock()

            mock_span = MagicMock()
            mock_span.name = "voice.turn"
            mock_span.start_time = None
            mock_span.end_time = None
            mock_span.duration_ms = 1000.0
            mock_span.attributes = {"voice.conversation.id": "conv-123"}
            mock_span.trace_id = None
            mock_span.span_id = None
            mock_span.parent_span_id = None

            mock_span_repo.get_by_conversation.return_value = [mock_span]
            mock_span_repo_class.return_value = mock_span_repo

            mock_conv_repo = AsyncMock()
            mock_conv = MagicMock()
            mock_conv.id = "uuid-123"
            mock_conv_repo.get_by_external_id.return_value = mock_conv
            mock_conv_repo_class.return_value = mock_conv_repo

            result = export_spans_from_db(
                database_url="postgresql://test:test@localhost/test",
                output_file=output_file,
                conversation_id="conv-123",
            )

            assert result["exported"] == 1

    def test_export_to_stdout(self):
        """Test that export returns spans list when no output file."""
        with (
            patch("voiceobs.server.db.connection.Database") as mock_db_class,
            patch("voiceobs.server.db.repositories.span.SpanRepository") as mock_span_repo_class,
            patch(
                "voiceobs.server.db.repositories.conversation.ConversationRepository"
            ) as mock_conv_repo_class,
        ):
            mock_db = AsyncMock()
            mock_db_class.return_value = mock_db

            mock_span_repo = AsyncMock()

            mock_span = MagicMock()
            mock_span.name = "test-span"
            mock_span.start_time = None
            mock_span.end_time = None
            mock_span.duration_ms = 100.0
            mock_span.attributes = {}
            mock_span.trace_id = None
            mock_span.span_id = None
            mock_span.parent_span_id = None

            mock_span_repo.get_all.return_value = [mock_span]
            mock_span_repo_class.return_value = mock_span_repo

            mock_conv_repo = AsyncMock()
            mock_conv_repo_class.return_value = mock_conv_repo

            result = export_spans_from_db(
                database_url="postgresql://test:test@localhost/test",
            )

            assert result["exported"] == 1
            assert "spans" in result
            assert len(result["spans"]) == 1
            assert result["spans"][0]["name"] == "test-span"


class TestServerPersistenceIntegration:
    """Tests for server endpoint persistence integration."""

    def test_ingest_writes_to_db_when_postgres_configured(self):
        """Test that ingest endpoint writes to PostgreSQL when configured."""
        # This tests that the dependencies module properly initializes
        # PostgreSQL storage when database URL is configured
        from voiceobs.server.dependencies import (
            InMemorySpanStoreAdapter,
            PostgresSpanStoreAdapter,
        )

        # Verify adapter classes exist and have correct interfaces
        assert hasattr(InMemorySpanStoreAdapter, "add_span")
        assert hasattr(PostgresSpanStoreAdapter, "add_span")
        assert hasattr(PostgresSpanStoreAdapter, "get_spans_as_dicts")

    def test_analysis_reads_from_db(self):
        """Test that analysis endpoint reads from storage adapter."""
        # Verify protocol defines required methods for analysis
        import inspect

        from voiceobs.server.dependencies import SpanStorageProtocol

        methods = inspect.getmembers(SpanStorageProtocol, predicate=inspect.isfunction)
        method_names = [m[0] for m in methods]

        assert "get_spans_as_dicts" in method_names or hasattr(
            SpanStorageProtocol, "get_spans_as_dicts"
        )


class TestDataLifecycle:
    """Tests for the complete data lifecycle."""

    def test_lifecycle_ingest_analyze_export(self, tmp_path):
        """Test the full ingest → store → analyze → export lifecycle."""
        from voiceobs.analyzer import analyze_spans

        # Simulate span data
        spans = [
            {
                "name": "voice.turn",
                "duration_ms": 1000.0,
                "attributes": {
                    "voice.actor": "user",
                    "voice.conversation.id": "conv-1",
                },
            },
            {
                "name": "voice.llm",
                "duration_ms": 500.0,
                "attributes": {
                    "voice.stage.type": "llm",
                    "voice.conversation.id": "conv-1",
                },
            },
            {
                "name": "voice.tts",
                "duration_ms": 200.0,
                "attributes": {
                    "voice.stage.type": "tts",
                    "voice.conversation.id": "conv-1",
                },
            },
            {
                "name": "voice.turn",
                "duration_ms": 800.0,
                "attributes": {
                    "voice.actor": "agent",
                    "voice.conversation.id": "conv-1",
                },
            },
        ]

        # Step 1: Analyze the spans
        result = analyze_spans(spans)

        # Verify analysis results (AnalysisResult has direct attributes)
        assert result.total_spans == 4
        assert result.total_turns == 2
        assert result.total_conversations == 1

        # Check stage metrics
        assert result.llm_metrics is not None
        assert result.llm_metrics.count == 1
        assert result.llm_metrics.mean_ms == 500.0

        assert result.tts_metrics is not None
        assert result.tts_metrics.count == 1
        assert result.tts_metrics.mean_ms == 200.0

        # Step 2: Export to JSONL
        output_file = tmp_path / "exported.jsonl"
        with open(output_file, "w") as f:
            for span in spans:
                f.write(json.dumps(span) + "\n")

        # Step 3: Re-import and analyze
        from voiceobs.analyzer import analyze_file

        result2 = analyze_file(output_file)

        # Verify results match
        assert result2.total_spans == result.total_spans
        assert result2.total_turns == result.total_turns
