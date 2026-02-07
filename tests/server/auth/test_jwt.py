"""Tests for JWT validation using JWKS."""

import time
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from jose.exceptions import JWKError

from voiceobs.server.auth.jwt import (
    JWTValidationError,
    _fetch_jwks,
    clear_jwks_cache,
    decode_supabase_jwt,
    get_supabase_url,
)

# Test Supabase URL
TEST_SUPABASE_URL = "https://test-project.supabase.co"

# Mock JWKS response (simplified - in reality this would be a proper RSA key)
MOCK_JWKS = {
    "keys": [
        {
            "kty": "RSA",
            "kid": "test-key-id",
            "use": "sig",
            "alg": "RS256",
            "n": "test-n-value",
            "e": "AQAB",
        }
    ]
}

# Mock JWT header (Supabase uses ES256)
MOCK_HEADER = {"alg": "ES256"}


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear JWKS cache before each test."""
    clear_jwks_cache()
    yield
    clear_jwks_cache()


def test_get_supabase_url_returns_env_value():
    """Test get_supabase_url returns environment variable value."""
    with patch.dict("os.environ", {"SUPABASE_URL": TEST_SUPABASE_URL}):
        url = get_supabase_url()
        assert url == TEST_SUPABASE_URL


def test_get_supabase_url_strips_trailing_slash():
    """Test get_supabase_url strips trailing slash."""
    with patch.dict("os.environ", {"SUPABASE_URL": f"{TEST_SUPABASE_URL}/"}):
        url = get_supabase_url()
        assert url == TEST_SUPABASE_URL


def test_get_supabase_url_raises_when_not_set():
    """Test get_supabase_url raises RuntimeError when env var not set."""
    with patch.dict("os.environ", {}, clear=True):
        # Ensure SUPABASE_URL is not in environment
        with pytest.raises(RuntimeError, match="SUPABASE_URL"):
            get_supabase_url()


def test_fetch_jwks_success():
    """Test fetching JWKS from Supabase."""
    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_JWKS
    mock_response.raise_for_status = MagicMock()

    with patch("voiceobs.server.auth.jwt.httpx.Client") as mock_client:
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)
        mock_client.return_value = mock_client_instance

        jwks = _fetch_jwks(TEST_SUPABASE_URL)
        assert jwks == MOCK_JWKS
        mock_client_instance.get.assert_called_once_with(
            f"{TEST_SUPABASE_URL}/auth/v1/.well-known/jwks.json"
        )


def test_fetch_jwks_caches_result():
    """Test that JWKS is cached."""
    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_JWKS
    mock_response.raise_for_status = MagicMock()

    with patch("voiceobs.server.auth.jwt.httpx.Client") as mock_client:
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)
        mock_client.return_value = mock_client_instance

        # First call should fetch
        _fetch_jwks(TEST_SUPABASE_URL)
        # Second call should use cache
        _fetch_jwks(TEST_SUPABASE_URL)

        # Should only be called once due to caching
        assert mock_client_instance.get.call_count == 1


def test_decode_jwt_with_mocked_jwks():
    """Test decoding a JWT with mocked JWKS verification."""
    user_id = str(uuid4())
    expected_payload = {
        "sub": user_id,
        "email": "test@example.com",
        "aud": "authenticated",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
    }

    with patch("voiceobs.server.auth.jwt._fetch_jwks", return_value=MOCK_JWKS):
        with patch(
            "voiceobs.server.auth.jwt.jwt.get_unverified_header",
            return_value=MOCK_HEADER,
        ):
            with patch("voiceobs.server.auth.jwt.jwt.decode", return_value=expected_payload):
                with patch.dict("os.environ", {"SUPABASE_URL": TEST_SUPABASE_URL}):
                    payload = decode_supabase_jwt("test-token")

                    assert payload["sub"] == user_id
                    assert payload["email"] == "test@example.com"


def test_decode_expired_token():
    """Test decoding an expired JWT raises JWTValidationError."""
    from jose import JWTError

    with patch("voiceobs.server.auth.jwt._fetch_jwks", return_value=MOCK_JWKS):
        with patch(
            "voiceobs.server.auth.jwt.jwt.get_unverified_header",
            return_value=MOCK_HEADER,
        ):
            with patch(
                "voiceobs.server.auth.jwt.jwt.decode",
                side_effect=JWTError("Signature has expired"),
            ):
                with patch.dict("os.environ", {"SUPABASE_URL": TEST_SUPABASE_URL}):
                    with pytest.raises(JWTValidationError, match="expired"):
                        decode_supabase_jwt("expired-token")


def test_decode_invalid_signature():
    """Test decoding a JWT with invalid signature."""
    from jose import JWTError

    with patch("voiceobs.server.auth.jwt._fetch_jwks", return_value=MOCK_JWKS):
        with patch(
            "voiceobs.server.auth.jwt.jwt.get_unverified_header",
            return_value=MOCK_HEADER,
        ):
            with patch(
                "voiceobs.server.auth.jwt.jwt.decode",
                side_effect=JWTError("Signature verification failed"),
            ):
                with patch.dict("os.environ", {"SUPABASE_URL": TEST_SUPABASE_URL}):
                    with pytest.raises(JWTValidationError, match="signature"):
                        decode_supabase_jwt("bad-signature-token")


def test_decode_invalid_audience():
    """Test decoding a JWT with invalid audience."""
    from jose import JWTError

    with patch("voiceobs.server.auth.jwt._fetch_jwks", return_value=MOCK_JWKS):
        with patch(
            "voiceobs.server.auth.jwt.jwt.get_unverified_header",
            return_value=MOCK_HEADER,
        ):
            with patch(
                "voiceobs.server.auth.jwt.jwt.decode",
                side_effect=JWTError("Invalid audience"),
            ):
                with patch.dict("os.environ", {"SUPABASE_URL": TEST_SUPABASE_URL}):
                    with pytest.raises(JWTValidationError, match="audience"):
                        decode_supabase_jwt("wrong-audience-token")


def test_decode_malformed_token():
    """Test decoding a malformed JWT."""
    from jose import JWTError

    with patch("voiceobs.server.auth.jwt._fetch_jwks", return_value=MOCK_JWKS):
        with patch(
            "voiceobs.server.auth.jwt.jwt.get_unverified_header",
            return_value=MOCK_HEADER,
        ):
            with patch(
                "voiceobs.server.auth.jwt.jwt.decode",
                side_effect=JWTError("Invalid token"),
            ):
                with patch.dict("os.environ", {"SUPABASE_URL": TEST_SUPABASE_URL}):
                    with pytest.raises(JWTValidationError):
                        decode_supabase_jwt("not-a-valid-jwt")


def test_decode_jwk_error():
    """Test handling JWK errors."""
    with patch("voiceobs.server.auth.jwt._fetch_jwks", return_value=MOCK_JWKS):
        with patch(
            "voiceobs.server.auth.jwt.jwt.get_unverified_header",
            return_value=MOCK_HEADER,
        ):
            with patch(
                "voiceobs.server.auth.jwt.jwt.decode",
                side_effect=JWKError("Invalid key"),
            ):
                with patch.dict("os.environ", {"SUPABASE_URL": TEST_SUPABASE_URL}):
                    with pytest.raises(JWTValidationError, match="Invalid key"):
                        decode_supabase_jwt("test-token")


def test_decode_with_explicit_url():
    """Test decoding with explicitly provided Supabase URL."""
    user_id = str(uuid4())
    expected_payload = {
        "sub": user_id,
        "email": "test@example.com",
        "aud": "authenticated",
    }

    with patch("voiceobs.server.auth.jwt._fetch_jwks", return_value=MOCK_JWKS) as mock_fetch:
        with patch(
            "voiceobs.server.auth.jwt.jwt.get_unverified_header",
            return_value=MOCK_HEADER,
        ):
            with patch("voiceobs.server.auth.jwt.jwt.decode", return_value=expected_payload):
                payload = decode_supabase_jwt("test-token", supabase_url=TEST_SUPABASE_URL)

                assert payload["sub"] == user_id
                mock_fetch.assert_called_once_with(TEST_SUPABASE_URL)
