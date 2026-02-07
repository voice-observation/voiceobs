"""JWT validation for Supabase tokens using JWKS."""

from __future__ import annotations

import logging
import os
import time
from typing import Any

import httpx
from jose import JWTError, jwt
from jose.exceptions import JWKError

log = logging.getLogger(__name__)


class JWTValidationError(Exception):
    """Raised when JWT validation fails."""

    pass


# Cache for JWKS to avoid fetching on every request
_jwks_cache: dict[str, Any] | None = None
_jwks_cache_time: float = 0
_JWKS_CACHE_TTL = 3600  # Cache JWKS for 1 hour


def get_supabase_url() -> str:
    """Get the Supabase URL from environment.

    Returns:
        The Supabase project URL.

    Raises:
        RuntimeError: If SUPABASE_URL is not set.
    """
    url = os.environ.get("SUPABASE_URL")
    if not url:
        raise RuntimeError("SUPABASE_URL environment variable not set")
    return url.rstrip("/")


def _fetch_jwks(supabase_url: str) -> dict[str, Any]:
    """Fetch JWKS from Supabase.

    Args:
        supabase_url: The Supabase project URL.

    Returns:
        The JWKS response.

    Raises:
        JWTValidationError: If JWKS cannot be fetched.
    """
    global _jwks_cache, _jwks_cache_time

    # Return cached JWKS if still valid
    if _jwks_cache and (time.time() - _jwks_cache_time) < _JWKS_CACHE_TTL:
        return _jwks_cache

    jwks_url = f"{supabase_url}/auth/v1/.well-known/jwks.json"
    log.info(f"Fetching JWKS from {jwks_url}")

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(jwks_url)
            response.raise_for_status()
            jwks = response.json()
            log.debug(f"Fetched JWKS with {len(jwks.get('keys', []))} keys")

            # Cache the JWKS
            _jwks_cache = jwks
            _jwks_cache_time = time.time()

            return jwks
    except httpx.HTTPError as e:
        log.error(f"Failed to fetch JWKS: {e}")
        raise JWTValidationError(f"Failed to fetch JWKS: {e}") from e


def decode_supabase_jwt(token: str, supabase_url: str | None = None) -> dict:
    """Decode and validate a Supabase JWT using JWKS.

    Args:
        token: The JWT token string.
        supabase_url: The Supabase project URL. If not provided, reads from SUPABASE_URL env.

    Returns:
        The decoded JWT payload.

    Raises:
        JWTValidationError: If the token is invalid or expired.
    """
    if not supabase_url:
        supabase_url = get_supabase_url()

    try:
        # Peek at the token header to determine the algorithm
        unverified_header = jwt.get_unverified_header(token)
        alg = unverified_header.get("alg")
        log.debug(f"JWT header: alg={alg}, typ={unverified_header.get('typ')}")

        # Fetch JWKS from Supabase
        jwks = _fetch_jwks(supabase_url)

        # Decode and verify the token
        # Supabase uses ES256 (Elliptic Curve) for JWKS signing
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["ES256"],
            audience="authenticated",
        )
        log.debug(f"Decoded JWT payload: sub={payload.get('sub')}")
        return payload

    except JWKError as e:
        log.warning(f"JWK error: {e}")
        raise JWTValidationError(f"Invalid key: {e}") from e
    except JWTError as e:
        error_msg = str(e).lower()
        log.warning(f"JWT decode error: {e}")
        if "expired" in error_msg:
            raise JWTValidationError("Token has expired") from e
        if "signature" in error_msg:
            raise JWTValidationError("Invalid token signature") from e
        if "audience" in error_msg:
            raise JWTValidationError("Invalid token audience") from e
        raise JWTValidationError(f"Invalid token: {e}") from e


def clear_jwks_cache() -> None:
    """Clear the JWKS cache. Useful for testing."""
    global _jwks_cache, _jwks_cache_time
    _jwks_cache = None
    _jwks_cache_time = 0
