"""Tests for UserRow model."""

from uuid import uuid4

from voiceobs.server.db.models.user import UserRow


def test_user_row_creation():
    """Test creating a UserRow with required fields."""
    user_id = uuid4()
    user = UserRow(
        id=user_id,
        email="test@example.com",
    )
    assert user.id == user_id
    assert user.email == "test@example.com"
    assert user.name is None
    assert user.is_active is True


def test_user_row_with_all_fields():
    """Test creating a UserRow with all fields."""
    user_id = uuid4()
    org_id = uuid4()
    user = UserRow(
        id=user_id,
        email="test@example.com",
        name="Test User",
        avatar_url="https://example.com/avatar.jpg",
        auth_provider="google",
        is_active=True,
        last_active_org_id=org_id,
    )
    assert user.id == user_id
    assert user.email == "test@example.com"
    assert user.name == "Test User"
    assert user.avatar_url == "https://example.com/avatar.jpg"
    assert user.auth_provider == "google"
    assert user.last_active_org_id == org_id


def test_user_row_last_active_org_id_defaults_to_none():
    """Test that last_active_org_id defaults to None."""
    user = UserRow(
        id=uuid4(),
        email="test@example.com",
    )
    assert user.last_active_org_id is None
