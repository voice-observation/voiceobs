"""Tests for web agent verifier."""

import pytest

from voiceobs.server.services.agent_verification.web_verifier import WebAgentVerifier


class TestWebAgentVerifier:
    """Tests for WebAgentVerifier."""

    def test_init(self):
        """Should initialize the verifier."""
        verifier = WebAgentVerifier()
        assert verifier is not None

    def test_get_agent_type(self):
        """Should return 'web' as agent type."""
        verifier = WebAgentVerifier()
        assert verifier.get_agent_type() == "web"


class TestVerify:
    """Tests for verify method."""

    @pytest.mark.asyncio
    async def test_verify_missing_web_url_raises(self):
        """Should raise ValueError when web_url is missing."""
        verifier = WebAgentVerifier()
        with pytest.raises(ValueError) as exc_info:
            await verifier.verify({})
        assert "web_url is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_verify_empty_web_url_raises(self):
        """Should raise ValueError when web_url is empty."""
        verifier = WebAgentVerifier()
        with pytest.raises(ValueError) as exc_info:
            await verifier.verify({"web_url": ""})
        assert "web_url is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_verify_none_web_url_raises(self):
        """Should raise ValueError when web_url is None."""
        verifier = WebAgentVerifier()
        with pytest.raises(ValueError) as exc_info:
            await verifier.verify({"web_url": None})
        assert "web_url is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_verify_invalid_url_format(self):
        """Should return failure for invalid URL format."""
        verifier = WebAgentVerifier()
        is_verified, error_msg = await verifier.verify({"web_url": "not-a-url"})
        assert is_verified is False
        assert "Invalid web URL format" in error_msg

    @pytest.mark.asyncio
    async def test_verify_invalid_url_without_scheme(self):
        """Should return failure for URL without scheme."""
        verifier = WebAgentVerifier()
        is_verified, error_msg = await verifier.verify({"web_url": "example.com/agent"})
        assert is_verified is False
        assert "Invalid web URL format" in error_msg

    @pytest.mark.asyncio
    async def test_verify_valid_http_url(self):
        """Should return success for valid HTTP URL."""
        verifier = WebAgentVerifier()
        is_verified, error_msg = await verifier.verify({"web_url": "http://example.com/agent"})
        assert is_verified is True
        assert error_msg is None

    @pytest.mark.asyncio
    async def test_verify_valid_https_url(self):
        """Should return success for valid HTTPS URL."""
        verifier = WebAgentVerifier()
        is_verified, error_msg = await verifier.verify(
            {"web_url": "https://api.example.com/v1/agent"}
        )
        assert is_verified is True
        assert error_msg is None

    @pytest.mark.asyncio
    async def test_verify_valid_url_with_port(self):
        """Should return success for valid URL with port."""
        verifier = WebAgentVerifier()
        is_verified, error_msg = await verifier.verify(
            {"web_url": "https://api.example.com:8080/agent"}
        )
        assert is_verified is True
        assert error_msg is None

    @pytest.mark.asyncio
    async def test_verify_valid_url_with_query_params(self):
        """Should return success for valid URL with query parameters."""
        verifier = WebAgentVerifier()
        is_verified, error_msg = await verifier.verify(
            {"web_url": "https://api.example.com/agent?key=value"}
        )
        assert is_verified is True
        assert error_msg is None

    @pytest.mark.asyncio
    async def test_verify_valid_localhost_url(self):
        """Should return success for localhost URL."""
        verifier = WebAgentVerifier()
        is_verified, error_msg = await verifier.verify({"web_url": "http://localhost:3000/agent"})
        assert is_verified is True
        assert error_msg is None

    @pytest.mark.asyncio
    async def test_verify_file_url_invalid(self):
        """Should return failure for file:// URLs."""
        verifier = WebAgentVerifier()
        is_verified, error_msg = await verifier.verify({"web_url": "file:///etc/passwd"})
        assert is_verified is False
        assert "Invalid web URL format" in error_msg

    @pytest.mark.asyncio
    async def test_verify_ftp_url_invalid(self):
        """Should return failure for non-HTTP/HTTPS URLs."""
        verifier = WebAgentVerifier()
        is_verified, error_msg = await verifier.verify({"web_url": "ftp://example.com/file"})
        assert is_verified is False
        assert "Invalid web URL format" in error_msg
