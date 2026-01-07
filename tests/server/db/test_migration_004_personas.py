"""Tests for personas table migration (004).

This module tests the migration that creates the personas table,
adds persona_id column to test_scenarios, and removes persona_json.
"""

import importlib.util
from pathlib import Path
from unittest.mock import patch

import sqlalchemy as sa
from alembic import op


def _load_migration_module():
    """Load the migration module dynamically."""
    migration_path = (
        Path(__file__).parent.parent.parent.parent
        / "src"
        / "voiceobs"
        / "server"
        / "db"
        / "alembic"
        / "versions"
        / "20260107_000000_004_add_personas_table.py"
    )
    spec = importlib.util.spec_from_file_location("migration_004", migration_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestMigration004Upgrade:
    """Tests for migration 004 upgrade."""

    def test_creates_personas_table(self):
        """Test that upgrade creates personas table with all required columns."""
        # Load the migration module
        migration_004 = _load_migration_module()

        # Mock op.create_table to capture the call
        with patch.object(op, "create_table") as mock_create_table:
            with patch.object(op, "create_index"):
                with patch.object(op, "add_column"):
                    with patch.object(op, "create_foreign_key"):
                        with patch.object(op, "drop_column"):
                            # Call upgrade
                            migration_004.upgrade()

            # Verify create_table was called for personas
            personas_calls = [
                call for call in mock_create_table.call_args_list if call[0][0] == "personas"
            ]
            assert len(personas_calls) == 1

            # Get the columns from the call
            call_args = personas_calls[0]
            columns = call_args[0][1:]  # Skip table name

            # Verify all required columns exist
            column_names = [col.name for col in columns]
            expected_columns = [
                "id",
                "name",
                "description",
                "aggression",
                "patience",
                "verbosity",
                "traits",
                "tts_provider",
                "tts_config",
                "preview_audio_url",
                "preview_audio_text",
                "metadata",
                "created_at",
                "updated_at",
                "created_by",
                "is_active",
            ]

            for expected_col in expected_columns:
                assert expected_col in column_names, f"Column {expected_col} missing"

    def test_creates_check_constraints(self):
        """Test that upgrade creates CHECK constraints for trait values."""
        migration_004 = _load_migration_module()

        with patch.object(op, "create_table") as mock_create_table:
            with patch.object(op, "create_index"):
                with patch.object(op, "add_column"):
                    with patch.object(op, "create_foreign_key"):
                        with patch.object(op, "drop_column"):
                            migration_004.upgrade()

            # Get the personas table call
            personas_calls = [
                call for call in mock_create_table.call_args_list if call[0][0] == "personas"
            ]
            call_args = personas_calls[0]
            columns = call_args[0][1:]

            # Find check constraints
            check_constraints = [col for col in columns if isinstance(col, sa.CheckConstraint)]

            # Should have 3 check constraints (aggression, patience, verbosity)
            assert len(check_constraints) == 3

    def test_creates_indexes_on_personas(self):
        """Test that upgrade creates indexes on personas table."""
        migration_004 = _load_migration_module()

        with patch.object(op, "create_index") as mock_create_index:
            with patch.object(op, "create_table"):
                with patch.object(op, "add_column"):
                    with patch.object(op, "create_foreign_key"):
                        with patch.object(op, "drop_column"):
                            migration_004.upgrade()

            # Verify indexes were created
            index_calls = mock_create_index.call_args_list
            index_names = [call[0][0] for call in index_calls]

            expected_indexes = [
                "idx_personas_name",
                "idx_personas_is_active",
                "idx_personas_created_at",
                "idx_personas_tts_provider",
            ]

            for expected_idx in expected_indexes:
                assert expected_idx in index_names, f"Index {expected_idx} missing"

    def test_adds_persona_id_to_test_scenarios(self):
        """Test that upgrade adds persona_id column to test_scenarios."""
        migration_004 = _load_migration_module()

        with patch.object(op, "add_column") as mock_add_column:
            with patch.object(op, "create_table"):
                with patch.object(op, "create_index"):
                    with patch.object(op, "create_foreign_key"):
                        with patch.object(op, "drop_column"):
                            migration_004.upgrade()

            # Verify add_column was called for test_scenarios
            add_column_calls = mock_add_column.call_args_list
            test_scenarios_calls = [
                call for call in add_column_calls if call[0][0] == "test_scenarios"
            ]

            assert len(test_scenarios_calls) == 1

            # Verify the column is persona_id
            column = test_scenarios_calls[0][0][1]
            assert column.name == "persona_id"
            assert not column.nullable  # Should be NOT NULL

    def test_creates_foreign_key_constraint(self):
        """Test that upgrade creates foreign key from test_scenarios to personas."""
        migration_004 = _load_migration_module()

        with patch.object(op, "create_foreign_key") as mock_create_fk:
            with patch.object(op, "create_table"):
                with patch.object(op, "create_index"):
                    with patch.object(op, "add_column"):
                        with patch.object(op, "drop_column"):
                            migration_004.upgrade()

            # Verify foreign key was created
            fk_calls = mock_create_fk.call_args_list
            assert len(fk_calls) >= 1

            # Find the test_scenarios -> personas foreign key
            fk_call = fk_calls[0]
            assert fk_call[0][1] == "test_scenarios"
            assert fk_call[0][2] == "personas"

    def test_drops_persona_json_column(self):
        """Test that upgrade drops persona_json column from test_scenarios."""
        migration_004 = _load_migration_module()

        with patch.object(op, "drop_column") as mock_drop_column:
            with patch.object(op, "create_table"):
                with patch.object(op, "create_index"):
                    with patch.object(op, "add_column"):
                        with patch.object(op, "create_foreign_key"):
                            migration_004.upgrade()

            # Verify drop_column was called for persona_json
            drop_calls = mock_drop_column.call_args_list
            test_scenarios_drops = [
                call
                for call in drop_calls
                if call[0][0] == "test_scenarios" and call[0][1] == "persona_json"
            ]

            assert len(test_scenarios_drops) == 1


class TestMigration004Downgrade:
    """Tests for migration 004 downgrade."""

    def test_restores_persona_json_column(self):
        """Test that downgrade restores persona_json column."""
        migration_004 = _load_migration_module()

        with patch.object(op, "add_column") as mock_add_column:
            with patch.object(op, "drop_index"):
                with patch.object(op, "drop_constraint"):
                    with patch.object(op, "drop_column"):
                        with patch.object(op, "drop_table"):
                            migration_004.downgrade()

            # Verify persona_json was restored
            add_column_calls = [
                call for call in mock_add_column.call_args_list if call[0][0] == "test_scenarios"
            ]
            assert len(add_column_calls) == 1

            column = add_column_calls[0][0][1]
            assert column.name == "persona_json"

    def test_drops_persona_id_column(self):
        """Test that downgrade removes persona_id column from test_scenarios."""
        migration_004 = _load_migration_module()

        with patch.object(op, "drop_column") as mock_drop_column:
            with patch.object(op, "add_column"):
                with patch.object(op, "drop_index"):
                    with patch.object(op, "drop_constraint"):
                        with patch.object(op, "drop_table"):
                            migration_004.downgrade()

            # Verify persona_id was dropped
            drop_calls = [
                call
                for call in mock_drop_column.call_args_list
                if call[0][0] == "test_scenarios" and call[0][1] == "persona_id"
            ]
            assert len(drop_calls) == 1

    def test_drops_foreign_key_constraint(self):
        """Test that downgrade drops foreign key constraint."""
        migration_004 = _load_migration_module()

        with patch.object(op, "drop_constraint") as mock_drop_constraint:
            with patch.object(op, "add_column"):
                with patch.object(op, "drop_index"):
                    with patch.object(op, "drop_column"):
                        with patch.object(op, "drop_table"):
                            migration_004.downgrade()

            # Verify foreign key constraint was dropped
            drop_constraint_calls = mock_drop_constraint.call_args_list
            fk_drops = [
                call
                for call in drop_constraint_calls
                if call[0][0] == "fk_test_scenarios_persona_id" and call[0][1] == "test_scenarios"
            ]
            assert len(fk_drops) == 1

    def test_drops_personas_table(self):
        """Test that downgrade drops personas table."""
        migration_004 = _load_migration_module()

        with patch.object(op, "drop_table") as mock_drop_table:
            with patch.object(op, "add_column"):
                with patch.object(op, "drop_index"):
                    with patch.object(op, "drop_constraint"):
                        with patch.object(op, "drop_column"):
                            migration_004.downgrade()

            # Verify personas table was dropped
            drop_table_calls = [
                call for call in mock_drop_table.call_args_list if call[0][0] == "personas"
            ]
            assert len(drop_table_calls) == 1

    def test_drops_all_indexes(self):
        """Test that downgrade drops all indexes on personas table."""
        migration_004 = _load_migration_module()

        with patch.object(op, "drop_index") as mock_drop_index:
            with patch.object(op, "add_column"):
                with patch.object(op, "drop_constraint"):
                    with patch.object(op, "drop_column"):
                        with patch.object(op, "drop_table"):
                            migration_004.downgrade()

            # Verify indexes were dropped
            drop_index_calls = mock_drop_index.call_args_list
            index_names = [call[0][0] for call in drop_index_calls]

            expected_indexes = [
                "idx_personas_created_at",
                "idx_personas_is_active",
                "idx_personas_name",
                "idx_personas_tts_provider",
                "idx_test_scenarios_persona_id",
            ]

            for expected_idx in expected_indexes:
                assert expected_idx in index_names, f"Index {expected_idx} not dropped"


class TestMigration004Metadata:
    """Tests for migration 004 metadata."""

    def test_revision_is_004(self):
        """Test that migration revision is 004."""
        migration_004 = _load_migration_module()

        assert migration_004.revision == "004"

    def test_down_revision_is_003(self):
        """Test that migration down_revision is 003."""
        migration_004 = _load_migration_module()

        assert migration_004.down_revision == "003"

    def test_has_docstring(self):
        """Test that migration has a docstring."""
        migration_004 = _load_migration_module()

        assert migration_004.__doc__ is not None
        assert "personas" in migration_004.__doc__.lower()
