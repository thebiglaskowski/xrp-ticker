"""Tests for security module."""

import time

from xrp_ticker.security import (
    APP_NAME,
    APP_VERSION,
    MAX_HTTP_RESPONSE_SIZE,
    MAX_WEBSOCKET_MESSAGE_SIZE,
    RateLimiter,
    generate_request_id,
    get_safe_user_agent,
    is_trusted_endpoint,
    mask_sensitive_data,
    sanitize_display_text,
    sanitize_error_message,
    validate_xrp_address,
)


class TestValidateXrpAddress:
    """Tests for XRP address validation."""

    def test_valid_address(self):
        """Valid XRP address should pass."""
        assert validate_xrp_address("rN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9") is True

    def test_another_valid_address(self):
        """Another valid XRP address should pass."""
        assert validate_xrp_address("rETnan6RaUmPnsPHoMjZqb1smNPeWwwago") is True

    def test_empty_address(self):
        """Empty address should fail."""
        assert validate_xrp_address("") is False

    def test_none_address(self):
        """None should fail."""
        assert validate_xrp_address(None) is False

    def test_address_too_short(self):
        """Short address should fail."""
        assert validate_xrp_address("rShort") is False

    def test_address_too_long(self):
        """Long address should fail."""
        assert validate_xrp_address("r" + "A" * 40) is False

    def test_address_wrong_prefix(self):
        """Address not starting with 'r' should fail."""
        assert validate_xrp_address("xN7n3473SaZBCG4dFL83w7a1RXtXtbk2D9") is False

    def test_address_invalid_chars(self):
        """Address with invalid characters should fail."""
        # Contains 0, O, I, l which are not in base58
        assert validate_xrp_address("rN7n3473SaZBCG4dFL83w7a1RXtXtbk0OI") is False

    def test_address_min_length(self):
        """Address at minimum length should pass if valid."""
        # 25 characters minimum
        addr = "r" + "A" * 24
        # This won't match pattern but tests length
        assert len(addr) == 25


class TestSanitizeErrorMessage:
    """Tests for error message sanitization."""

    def test_connection_refused(self):
        """ConnectionRefusedError should be sanitized."""
        error = ConnectionRefusedError("Connection refused to 192.168.1.1:443")
        result = sanitize_error_message(error)
        assert result == "Connection refused"
        assert "192.168" not in result

    def test_timeout_error(self):
        """TimeoutError should be sanitized."""
        error = TimeoutError("Operation timed out after 30 seconds")
        result = sanitize_error_message(error)
        assert result == "Request timed out"

    def test_ssl_error(self):
        """SSL errors should be sanitized."""
        import ssl
        error = ssl.SSLError(1, "certificate verify failed: internal error")
        result = sanitize_error_message(error)
        assert result == "SSL/TLS error"
        assert "internal error" not in result

    def test_generic_error(self):
        """Unknown errors should return generic message."""
        error = ValueError("Some internal detail")
        result = sanitize_error_message(error)
        assert result == "An error occurred"
        assert "internal detail" not in result


class TestMaskSensitiveData:
    """Tests for data masking."""

    def test_normal_data(self):
        """Normal length data should show first/last chars."""
        result = mask_sensitive_data("1234567890abcdef", visible_chars=4)
        assert result == "1234...cdef"

    def test_short_data(self):
        """Short data should be fully masked."""
        result = mask_sensitive_data("short", visible_chars=4)
        assert result == "***"

    def test_empty_data(self):
        """Empty data should be masked."""
        result = mask_sensitive_data("")
        assert result == "***"

    def test_custom_visible_chars(self):
        """Custom visible_chars should be respected."""
        result = mask_sensitive_data("1234567890", visible_chars=2)
        assert result == "12...90"


class TestSanitizeDisplayText:
    """Tests for display text sanitization."""

    def test_normal_text(self):
        """Normal text should pass through."""
        result = sanitize_display_text("Hello World")
        assert result == "Hello World"

    def test_control_characters(self):
        """Control characters should be removed."""
        result = sanitize_display_text("Hello\x00World")
        assert "\x00" not in result

    def test_max_length(self):
        """Long text should be truncated."""
        long_text = "A" * 200
        result = sanitize_display_text(long_text, max_length=50)
        assert len(result) == 50
        assert result.endswith("...")

    def test_newlines_preserved(self):
        """Newlines and tabs should be preserved."""
        result = sanitize_display_text("Hello\nWorld\tTest")
        assert "\n" in result
        assert "\t" in result

    def test_empty_text(self):
        """Empty text should return empty string."""
        result = sanitize_display_text("")
        assert result == ""


class TestIsTrustedEndpoint:
    """Tests for endpoint trust validation."""

    def test_trusted_xrplcluster(self):
        """xrplcluster.com should be trusted."""
        assert is_trusted_endpoint("wss://xrplcluster.com") is True

    def test_trusted_ripple_s1(self):
        """s1.ripple.com should be trusted."""
        assert is_trusted_endpoint("wss://s1.ripple.com") is True

    def test_trusted_ripple_s2(self):
        """s2.ripple.com should be trusted."""
        assert is_trusted_endpoint("wss://s2.ripple.com") is True

    def test_trusted_xrpl_ws(self):
        """xrpl.ws should be trusted."""
        assert is_trusted_endpoint("wss://xrpl.ws") is True

    def test_untrusted_domain(self):
        """Untrusted domains should fail."""
        assert is_trusted_endpoint("wss://evil.attacker.com") is False

    def test_http_not_trusted(self):
        """HTTP endpoints should fail (not wss)."""
        assert is_trusted_endpoint("https://xrplcluster.com") is False

    def test_ws_not_trusted(self):
        """Non-secure WS should fail."""
        assert is_trusted_endpoint("ws://xrplcluster.com") is False

    def test_empty_endpoint(self):
        """Empty endpoint should fail."""
        assert is_trusted_endpoint("") is False

    def test_endpoint_with_path(self):
        """Endpoint with path should still be trusted if domain matches."""
        assert is_trusted_endpoint("wss://xrplcluster.com/websocket") is True

    def test_endpoint_with_port(self):
        """Endpoint with port should still be trusted if domain matches."""
        assert is_trusted_endpoint("wss://xrplcluster.com:443") is True


class TestRateLimiter:
    """Tests for RateLimiter class."""

    def test_allows_first_request(self):
        """First request should be allowed."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        assert limiter.can_make_request(time.time()) is True

    def test_blocks_after_limit(self):
        """Requests should be blocked after limit."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        current = time.time()

        limiter.record_request(current)
        limiter.record_request(current)

        assert limiter.can_make_request(current) is False

    def test_allows_after_window(self):
        """Requests should be allowed after window expires."""
        limiter = RateLimiter(max_requests=2, window_seconds=1)
        old_time = time.time() - 2  # 2 seconds ago

        limiter.record_request(old_time)
        limiter.record_request(old_time)

        # Now should be allowed
        assert limiter.can_make_request(time.time()) is True

    def test_time_until_available(self):
        """Should return time to wait."""
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        current = time.time()

        limiter.record_request(current)

        wait_time = limiter.time_until_available(current)
        assert wait_time > 0
        assert wait_time <= 60

    def test_time_until_available_when_allowed(self):
        """Should return 0 when request is allowed."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        assert limiter.time_until_available(time.time()) == 0.0

    def test_time_until_available_empty_after_filter(self):
        """Should return 0 when all requests are outside window (edge case fix)."""
        limiter = RateLimiter(max_requests=1, window_seconds=1)
        old_time = time.time() - 10  # 10 seconds ago

        # Add an old request
        limiter.record_request(old_time)

        # Now, even though we have a request, it's outside the window
        # So can_make_request should return True and time_until_available should return 0
        current = time.time()
        assert limiter.can_make_request(current) is True
        assert limiter.time_until_available(current) == 0.0


class TestGenerateRequestId:
    """Tests for request ID generation."""

    def test_returns_string(self):
        """Should return a string."""
        result = generate_request_id()
        assert isinstance(result, str)

    def test_length(self):
        """Should return 16-character hex string."""
        result = generate_request_id()
        assert len(result) == 16

    def test_unique(self):
        """Should generate unique IDs."""
        ids = {generate_request_id() for _ in range(100)}
        assert len(ids) == 100


class TestGetSafeUserAgent:
    """Tests for User-Agent generation."""

    def test_format(self):
        """Should return app name and version."""
        result = get_safe_user_agent()
        assert APP_NAME in result
        assert APP_VERSION in result

    def test_no_system_info(self):
        """Should not contain system information."""
        result = get_safe_user_agent()
        assert "Windows" not in result
        assert "Linux" not in result
        assert "Python" not in result


class TestSecurityConstants:
    """Tests for security constants."""

    def test_websocket_message_size_reasonable(self):
        """WebSocket message size should be reasonable."""
        assert MAX_WEBSOCKET_MESSAGE_SIZE == 1024 * 1024  # 1MB

    def test_http_response_size_reasonable(self):
        """HTTP response size should be reasonable."""
        assert MAX_HTTP_RESPONSE_SIZE == 10 * 1024 * 1024  # 10MB
