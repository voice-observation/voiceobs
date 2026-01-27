"""Tests for validation utilities."""

from voiceobs.server.utils.validators import is_valid_e164_phone_number, is_valid_url


class TestIsValidE164PhoneNumber:
    """Tests for E.164 phone number validation."""

    def test_valid_us_number(self):
        """Valid US phone number should pass."""
        assert is_valid_e164_phone_number("+14155551234") is True

    def test_valid_uk_number(self):
        """Valid UK phone number should pass."""
        assert is_valid_e164_phone_number("+442071234567") is True

    def test_valid_short_number(self):
        """Valid short phone number (minimum length) should pass."""
        assert is_valid_e164_phone_number("+1") is True

    def test_valid_max_length_number(self):
        """Valid 15-digit phone number (maximum E.164 length) should pass."""
        assert is_valid_e164_phone_number("+123456789012345") is True

    def test_missing_plus_prefix(self):
        """Phone number without + prefix should fail."""
        assert is_valid_e164_phone_number("14155551234") is False

    def test_empty_string(self):
        """Empty string should fail."""
        assert is_valid_e164_phone_number("") is False

    def test_only_plus(self):
        """Just + without digits should fail."""
        assert is_valid_e164_phone_number("+") is False

    def test_non_digit_characters(self):
        """Phone number with non-digit characters should fail."""
        assert is_valid_e164_phone_number("+1-415-555-1234") is False

    def test_letters_in_number(self):
        """Phone number with letters should fail."""
        assert is_valid_e164_phone_number("+1415abc1234") is False

    def test_too_long_number(self):
        """Phone number exceeding 15 digits should fail."""
        assert is_valid_e164_phone_number("+1234567890123456") is False

    def test_spaces_in_number(self):
        """Phone number with spaces should fail."""
        assert is_valid_e164_phone_number("+1 415 555 1234") is False


class TestIsValidUrl:
    """Tests for URL validation."""

    def test_valid_http_url(self):
        """Valid HTTP URL should pass."""
        assert is_valid_url("http://example.com") is True

    def test_valid_https_url(self):
        """Valid HTTPS URL should pass."""
        assert is_valid_url("https://example.com") is True

    def test_url_with_path(self):
        """URL with path should pass."""
        assert is_valid_url("https://example.com/api/v1") is True

    def test_url_with_port(self):
        """URL with port should pass."""
        assert is_valid_url("http://localhost:8080") is True

    def test_missing_protocol(self):
        """URL without protocol should fail."""
        assert is_valid_url("example.com") is False

    def test_empty_string(self):
        """Empty string should fail."""
        assert is_valid_url("") is False

    def test_invalid_protocol(self):
        """URL with invalid protocol should fail."""
        assert is_valid_url("ftp://example.com") is False

    def test_only_protocol(self):
        """Just protocol without domain should fail."""
        assert is_valid_url("http://") is False

    def test_protocol_only_with_slashes(self):
        """Protocol with only slashes should fail."""
        assert is_valid_url("https://a") is False

    def test_require_https_with_http(self):
        """HTTP URL should fail when HTTPS required."""
        assert is_valid_url("http://example.com", require_https=True) is False

    def test_require_https_with_https(self):
        """HTTPS URL should pass when HTTPS required."""
        assert is_valid_url("https://example.com", require_https=True) is True

    def test_domain_too_short(self):
        """Domain shorter than minimum length should fail."""
        assert is_valid_url("http://ab") is False

    def test_localhost_valid(self):
        """localhost URL should pass."""
        assert is_valid_url("http://localhost") is True
