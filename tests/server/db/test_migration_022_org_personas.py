"""Tests for migration 022: add org scope to personas."""

import importlib.util
from pathlib import Path
from unittest.mock import patch

from alembic import op


def _load_migration_module():
    """Load the migration module dynamically.

    Module names starting with digits cannot be imported via normal Python
    import syntax, so we use importlib.util to load by file path.
    """
    migration_path = (
        Path(__file__).parent.parent.parent.parent
        / "src"
        / "voiceobs"
        / "server"
        / "db"
        / "alembic"
        / "versions"
        / "20260208_000000_022_add_org_scope_to_personas.py"
    )
    spec = importlib.util.spec_from_file_location("migration_022", migration_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestMigration022Metadata:
    """Tests for migration 022 metadata."""

    def test_revision_is_022(self):
        """Migration revision must be '022'."""
        m = _load_migration_module()
        assert m.revision == "022"

    def test_down_revision_is_021(self):
        """Migration down_revision must be '021'."""
        m = _load_migration_module()
        assert m.down_revision == "021"

    def test_upgrade_and_downgrade_are_callable(self):
        """Migration must expose callable upgrade and downgrade."""
        m = _load_migration_module()
        assert callable(m.upgrade)
        assert callable(m.downgrade)

    def test_branch_labels_and_depends_on_are_none(self):
        """Branch labels and depends_on should be None."""
        m = _load_migration_module()
        assert m.branch_labels is None
        assert m.depends_on is None

    def test_has_docstring_mentioning_org_id(self):
        """Migration module must have a docstring mentioning org_id."""
        m = _load_migration_module()
        assert m.__doc__ is not None
        assert "org_id" in m.__doc__


class TestMigration022Upgrade:
    """Tests for the upgrade function."""

    def _run_upgrade(self):
        """Load and run upgrade with all alembic ops mocked."""
        m = _load_migration_module()

        with (
            patch.object(op, "add_column") as mock_add_column,
            patch.object(op, "execute") as mock_execute,
            patch.object(op, "alter_column") as mock_alter_column,
            patch.object(op, "create_foreign_key") as mock_create_fk,
            patch.object(op, "create_index") as mock_create_index,
            patch.object(op, "create_unique_constraint") as mock_create_uq,
            patch.object(op, "drop_index") as mock_drop_index,
            patch.object(op, "create_check_constraint") as mock_create_check,
        ):
            m.upgrade()

        return {
            "add_column": mock_add_column,
            "execute": mock_execute,
            "alter_column": mock_alter_column,
            "create_foreign_key": mock_create_fk,
            "create_index": mock_create_index,
            "create_unique_constraint": mock_create_uq,
            "drop_index": mock_drop_index,
            "create_check_constraint": mock_create_check,
        }

    def test_adds_org_id_column(self):
        """Upgrade must add org_id column to personas (nullable initially)."""
        mocks = self._run_upgrade()

        add_column_calls = mocks["add_column"].call_args_list
        org_id_calls = [
            c for c in add_column_calls if c[0][0] == "personas" and c[0][1].name == "org_id"
        ]
        assert len(org_id_calls) == 1

        col = org_id_calls[0][0][1]
        assert col.nullable is True

    def test_adds_persona_type_column(self):
        """Upgrade must add persona_type column with server_default 'custom'."""
        mocks = self._run_upgrade()

        add_column_calls = mocks["add_column"].call_args_list
        persona_type_calls = [
            c for c in add_column_calls if c[0][0] == "personas" and c[0][1].name == "persona_type"
        ]
        assert len(persona_type_calls) == 1

        col = persona_type_calls[0][0][1]
        assert col.nullable is False
        assert col.server_default is not None

    def test_deletes_existing_rows(self):
        """Upgrade must delete test_scenarios and personas rows (clean slate)."""
        mocks = self._run_upgrade()

        execute_calls = [c[0][0] for c in mocks["execute"].call_args_list]
        assert "DELETE FROM test_scenarios" in execute_calls
        assert "DELETE FROM personas" in execute_calls

        # test_scenarios must be deleted before personas (FK order)
        ts_idx = execute_calls.index("DELETE FROM test_scenarios")
        p_idx = execute_calls.index("DELETE FROM personas")
        assert ts_idx < p_idx

    def test_makes_org_id_not_null(self):
        """After deleting rows, org_id must be altered to NOT NULL."""
        mocks = self._run_upgrade()

        alter_calls = mocks["alter_column"].call_args_list
        org_id_alter = [c for c in alter_calls if c[0][0] == "personas" and c[0][1] == "org_id"]
        assert len(org_id_alter) == 1
        assert org_id_alter[0][1]["nullable"] is False

    def test_creates_foreign_key(self):
        """Upgrade must create FK from personas.org_id to organizations.id."""
        mocks = self._run_upgrade()

        fk_calls = mocks["create_foreign_key"].call_args_list
        assert len(fk_calls) == 1

        fk = fk_calls[0]
        assert fk[0][0] == "fk_personas_org_id"
        assert fk[0][1] == "personas"
        assert fk[0][2] == "organizations"
        assert fk[0][3] == ["org_id"]
        assert fk[0][4] == ["id"]
        assert fk[1]["ondelete"] == "CASCADE"

    def test_creates_org_id_index(self):
        """Upgrade must create index on personas.org_id."""
        mocks = self._run_upgrade()

        idx_calls = mocks["create_index"].call_args_list
        idx_names = [c[0][0] for c in idx_calls]
        assert "idx_personas_org_id" in idx_names

    def test_creates_unique_constraint(self):
        """Upgrade must create unique constraint on (org_id, name)."""
        mocks = self._run_upgrade()

        uq_calls = mocks["create_unique_constraint"].call_args_list
        assert len(uq_calls) == 1
        assert uq_calls[0][0][0] == "uq_personas_org_id_name"
        assert uq_calls[0][0][1] == "personas"
        assert uq_calls[0][0][2] == ["org_id", "name"]

    def test_drops_old_name_index(self):
        """Upgrade must drop old idx_personas_name index."""
        mocks = self._run_upgrade()

        drop_idx_calls = mocks["drop_index"].call_args_list
        assert len(drop_idx_calls) == 1
        assert drop_idx_calls[0][0][0] == "idx_personas_name"
        assert drop_idx_calls[0][0][1] == "personas"

    def test_creates_check_constraint(self):
        """Upgrade must create CHECK constraint for persona_type."""
        mocks = self._run_upgrade()

        check_calls = mocks["create_check_constraint"].call_args_list
        assert len(check_calls) == 1
        assert check_calls[0][0][0] == "check_persona_type"
        assert check_calls[0][0][1] == "personas"


class TestMigration022Downgrade:
    """Tests for the downgrade function."""

    def _run_downgrade(self):
        """Load and run downgrade with all alembic ops mocked."""
        m = _load_migration_module()

        with (
            patch.object(op, "drop_constraint") as mock_drop_constraint,
            patch.object(op, "create_index") as mock_create_index,
            patch.object(op, "drop_index") as mock_drop_index,
            patch.object(op, "drop_column") as mock_drop_column,
        ):
            m.downgrade()

        return {
            "drop_constraint": mock_drop_constraint,
            "create_index": mock_create_index,
            "drop_index": mock_drop_index,
            "drop_column": mock_drop_column,
        }

    def test_drops_check_constraint(self):
        """Downgrade must drop the check_persona_type constraint."""
        mocks = self._run_downgrade()

        check_drops = [
            c for c in mocks["drop_constraint"].call_args_list if c[0][0] == "check_persona_type"
        ]
        assert len(check_drops) == 1

    def test_restores_name_index(self):
        """Downgrade must restore idx_personas_name index."""
        mocks = self._run_downgrade()

        idx_calls = mocks["create_index"].call_args_list
        name_idx = [c for c in idx_calls if c[0][0] == "idx_personas_name"]
        assert len(name_idx) == 1

    def test_drops_unique_constraint(self):
        """Downgrade must drop uq_personas_org_id_name constraint."""
        mocks = self._run_downgrade()

        uq_drops = [
            c
            for c in mocks["drop_constraint"].call_args_list
            if c[0][0] == "uq_personas_org_id_name"
        ]
        assert len(uq_drops) == 1

    def test_drops_org_id_index(self):
        """Downgrade must drop idx_personas_org_id index."""
        mocks = self._run_downgrade()

        idx_drops = mocks["drop_index"].call_args_list
        org_idx_drops = [c for c in idx_drops if c[0][0] == "idx_personas_org_id"]
        assert len(org_idx_drops) == 1

    def test_drops_foreign_key(self):
        """Downgrade must drop fk_personas_org_id constraint."""
        mocks = self._run_downgrade()

        fk_drops = [
            c for c in mocks["drop_constraint"].call_args_list if c[0][0] == "fk_personas_org_id"
        ]
        assert len(fk_drops) == 1

    def test_drops_persona_type_column(self):
        """Downgrade must drop persona_type column."""
        mocks = self._run_downgrade()

        drop_col_calls = mocks["drop_column"].call_args_list
        persona_type_drops = [
            c for c in drop_col_calls if c[0][0] == "personas" and c[0][1] == "persona_type"
        ]
        assert len(persona_type_drops) == 1

    def test_drops_org_id_column(self):
        """Downgrade must drop org_id column."""
        mocks = self._run_downgrade()

        drop_col_calls = mocks["drop_column"].call_args_list
        org_id_drops = [c for c in drop_col_calls if c[0][0] == "personas" and c[0][1] == "org_id"]
        assert len(org_id_drops) == 1
