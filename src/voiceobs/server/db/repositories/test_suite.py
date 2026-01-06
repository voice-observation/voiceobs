"""Test suite repository for database operations."""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from voiceobs.server.db.connection import Database
from voiceobs.server.db.models import TestSuiteRow


class TestSuiteRepository:
    """Repository for test suite operations."""

    def __init__(self, db: Database) -> None:
        """Initialize the test suite repository.

        Args:
            db: Database connection manager.
        """
        self._db = db

    async def create(
        self,
        name: str,
        description: str | None = None,
    ) -> TestSuiteRow:
        """Create a new test suite.

        Args:
            name: Test suite name.
            description: Test suite description.

        Returns:
            The created test suite row.
        """
        suite_id = uuid4()
        await self._db.execute(
            """
            INSERT INTO test_suites (id, name, description, status)
            VALUES ($1, $2, $3, 'pending')
            """,
            suite_id,
            name,
            description,
        )

        row = await self._db.fetchrow(
            """
            SELECT id, name, description, status, created_at
            FROM test_suites WHERE id = $1
            """,
            suite_id,
        )

        if row is None:
            raise RuntimeError("Failed to create test suite")

        return TestSuiteRow(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            status=row["status"],
            created_at=row["created_at"],
        )

    async def get(self, suite_id: UUID) -> TestSuiteRow | None:
        """Get a test suite by UUID.

        Args:
            suite_id: The test suite UUID.

        Returns:
            The test suite row, or None if not found.
        """
        row = await self._db.fetchrow(
            """
            SELECT id, name, description, status, created_at
            FROM test_suites WHERE id = $1
            """,
            suite_id,
        )

        if row is None:
            return None

        return TestSuiteRow(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            status=row["status"],
            created_at=row["created_at"],
        )

    async def list_all(self) -> list[TestSuiteRow]:
        """List all test suites.

        Returns:
            List of test suites.
        """
        rows = await self._db.fetch(
            """
            SELECT id, name, description, status, created_at
            FROM test_suites
            ORDER BY created_at DESC
            """
        )

        return [
            TestSuiteRow(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                status=row["status"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    async def update(
        self,
        suite_id: UUID,
        name: str | None = None,
        description: str | None = None,
        status: str | None = None,
    ) -> TestSuiteRow | None:
        """Update a test suite.

        Args:
            suite_id: The test suite UUID.
            name: New name (optional).
            description: New description (optional).
            status: New status (optional).

        Returns:
            The updated test suite row, or None if not found.
        """
        updates = []
        params: list[Any] = []
        param_idx = 1

        if name is not None:
            updates.append(f"name = ${param_idx}")
            params.append(name)
            param_idx += 1

        if description is not None:
            updates.append(f"description = ${param_idx}")
            params.append(description)
            param_idx += 1

        if status is not None:
            updates.append(f"status = ${param_idx}")
            params.append(status)
            param_idx += 1

        if not updates:
            # No updates, just return the existing suite
            return await self.get(suite_id)

        params.append(suite_id)
        await self._db.execute(
            f"""
            UPDATE test_suites
            SET {", ".join(updates)}
            WHERE id = ${param_idx}
            """,
            *params,
        )

        return await self.get(suite_id)

    async def delete(self, suite_id: UUID) -> bool:
        """Delete a test suite.

        Args:
            suite_id: The test suite UUID.

        Returns:
            True if deleted, False if not found.
        """
        result = await self._db.execute(
            """
            DELETE FROM test_suites WHERE id = $1
            """,
            suite_id,
        )
        return result == "DELETE 1"
