"""Validation utilities for the voiceobs server."""

from __future__ import annotations


def is_valid_e164_phone_number(phone_number: str) -> bool:
    """Validate phone number format (E.164).

    E.164 format requires:
    - Leading + sign
    - 1-15 digits following the +
    - No spaces, dashes, or other characters

    Args:
        phone_number: Phone number to validate

    Returns:
        True if phone number format is valid (E.164), False otherwise

    Examples:
        >>> is_valid_e164_phone_number("+14155551234")
        True
        >>> is_valid_e164_phone_number("14155551234")
        False
        >>> is_valid_e164_phone_number("+1-415-555-1234")
        False
    """
    if not phone_number:
        return False
    if not phone_number.startswith("+"):
        return False
    digits = phone_number[1:]
    if not digits:
        return False
    if not digits.isdigit():
        return False
    if len(digits) < 1 or len(digits) > 15:
        return False
    return True


def is_valid_url(url: str, require_https: bool = False) -> bool:
    """Validate URL format.

    Args:
        url: URL to validate
        require_https: If True, only HTTPS URLs are considered valid

    Returns:
        True if URL format is valid, False otherwise

    Examples:
        >>> is_valid_url("https://example.com")
        True
        >>> is_valid_url("http://example.com", require_https=True)
        False
        >>> is_valid_url("example.com")
        False
    """
    if not url:
        return False

    # Check protocol
    if require_https:
        if not url.startswith("https://"):
            return False
    else:
        if not url.startswith(("http://", "https://")):
            return False

    # Extract domain part
    parts = url.split("://", 1)
    if len(parts) != 2:
        return False

    domain = parts[1]
    if not domain:
        return False

    # Get just the host part (before any path/query)
    host = domain.split("/")[0]
    host = host.split("?")[0]
    host = host.split(":")[0]  # Remove port

    # Minimum domain length: "a.b" = 3 chars, or "localhost" = 9 chars
    if len(host) < 3:
        return False

    return True
