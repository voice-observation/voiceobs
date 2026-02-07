"""FastAPI dependencies for authentication."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import Header, HTTPException, status

from voiceobs.server.auth.jwt import JWTValidationError, decode_supabase_jwt
from voiceobs.server.db.models import UserRow
from voiceobs.server.dependencies import get_organization_service, get_user_repository

log = logging.getLogger(__name__)


async def get_current_user(
    authorization: str | None = Header(None, alias="Authorization"),
) -> UserRow:
    """Get current authenticated user from JWT.

    Validates the JWT, extracts user info, and upserts in local database.

    Args:
        authorization: The Authorization header value (e.g., "Bearer <token>").

    Returns:
        The authenticated user's database row.

    Raises:
        HTTPException: If authentication fails or user is inactive.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization[7:]  # Remove "Bearer " prefix
    try:
        # Decode JWT using JWKS from Supabase (reads SUPABASE_URL from env)
        payload = decode_supabase_jwt(token)
        log.debug(f"JWT payload decoded: sub={payload.get('sub')}")
    except JWTValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except RuntimeError as e:
        # RuntimeError is raised when SUPABASE_URL is not set
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

    # Extract user info from JWT
    user_id = UUID(payload["sub"])
    email = payload.get("email", "")
    user_metadata = payload.get("user_metadata", {})
    app_metadata = payload.get("app_metadata", {})

    name = user_metadata.get("name") or user_metadata.get("full_name")
    avatar_url = user_metadata.get("avatar_url")
    auth_provider = app_metadata.get("provider", "email")

    # Upsert user in local database
    repo = get_user_repository()
    if repo is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        )

    user = await repo.upsert(
        user_id=user_id,
        email=email,
        name=name,
        avatar_url=avatar_url,
        auth_provider=auth_provider,
    )

    # Ensure user has at least one organization
    org_service = get_organization_service()
    if org_service:
        await org_service.ensure_user_has_org(user)

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    return user


async def get_current_user_optional(
    authorization: str | None = Header(None, alias="Authorization"),
) -> UserRow | None:
    """Get current user if authenticated, None otherwise.

    This is useful for endpoints that can work both with and without
    authentication, providing different behavior based on auth state.

    Args:
        authorization: The Authorization header value (e.g., "Bearer <token>").

    Returns:
        The authenticated user's database row, or None if not authenticated.
    """
    if not authorization:
        return None

    try:
        return await get_current_user(authorization)
    except HTTPException:
        return None
