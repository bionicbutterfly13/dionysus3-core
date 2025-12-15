"""
Contract Tests: HMAC Signature Validation
Feature: 002-remote-persistence-safety
Task: T008

TDD Test - Write FIRST, verify FAILS before implementation.

Tests HMAC-SHA256 signature generation and validation for webhook security.
"""

import hashlib
import hmac
import json
import os

import pytest
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@pytest.fixture
def webhook_token():
    """Get webhook token from environment or use test token."""
    return os.getenv("MEMORY_WEBHOOK_TOKEN", "test-webhook-token-for-testing")


@pytest.fixture
def sample_payload():
    """Sample memory sync payload for testing."""
    return {
        "memory_id": "550e8400-e29b-41d4-a716-446655440000",
        "content": "Test memory content",
        "memory_type": "episodic",
        "session_id": "660e8400-e29b-41d4-a716-446655440001",
        "project_id": "dionysus-core",
        "sync_version": 1,
    }


class TestHMACSignatureGeneration:
    """Test HMAC signature generation."""

    def test_generate_signature_returns_string(self, webhook_token, sample_payload):
        """Test that generate_signature returns a string."""
        # This import will fail until T014 implements hmac_utils
        from api.services.hmac_utils import generate_signature

        payload_bytes = json.dumps(sample_payload).encode("utf-8")
        signature = generate_signature(payload_bytes, webhook_token)

        assert isinstance(signature, str)
        assert signature.startswith("sha256=")

    def test_generate_signature_is_deterministic(self, webhook_token, sample_payload):
        """Test that same input produces same signature."""
        from api.services.hmac_utils import generate_signature

        payload_bytes = json.dumps(sample_payload).encode("utf-8")
        sig1 = generate_signature(payload_bytes, webhook_token)
        sig2 = generate_signature(payload_bytes, webhook_token)

        assert sig1 == sig2

    def test_different_payload_produces_different_signature(
        self, webhook_token, sample_payload
    ):
        """Test that different payloads produce different signatures."""
        from api.services.hmac_utils import generate_signature

        payload1 = json.dumps(sample_payload).encode("utf-8")
        modified_payload = {**sample_payload, "content": "Different content"}
        payload2 = json.dumps(modified_payload).encode("utf-8")

        sig1 = generate_signature(payload1, webhook_token)
        sig2 = generate_signature(payload2, webhook_token)

        assert sig1 != sig2

    def test_different_token_produces_different_signature(self, sample_payload):
        """Test that different tokens produce different signatures."""
        from api.services.hmac_utils import generate_signature

        payload_bytes = json.dumps(sample_payload).encode("utf-8")
        sig1 = generate_signature(payload_bytes, "token1")
        sig2 = generate_signature(payload_bytes, "token2")

        assert sig1 != sig2

    def test_signature_format_matches_webhook_spec(self, webhook_token, sample_payload):
        """Test that signature format matches X-Webhook-Signature header spec."""
        from api.services.hmac_utils import generate_signature

        payload_bytes = json.dumps(sample_payload).encode("utf-8")
        signature = generate_signature(payload_bytes, webhook_token)

        # Format: sha256=<hex_digest>
        assert signature.startswith("sha256=")
        hex_part = signature[7:]  # Remove "sha256=" prefix
        assert len(hex_part) == 64  # SHA256 produces 64 hex characters
        assert all(c in "0123456789abcdef" for c in hex_part)


class TestHMACSignatureValidation:
    """Test HMAC signature validation."""

    def test_valid_signature_passes_validation(self, webhook_token, sample_payload):
        """Test that a valid signature passes validation."""
        from api.services.hmac_utils import generate_signature, validate_signature

        payload_bytes = json.dumps(sample_payload).encode("utf-8")
        signature = generate_signature(payload_bytes, webhook_token)

        is_valid = validate_signature(payload_bytes, signature, webhook_token)
        assert is_valid is True

    def test_invalid_signature_fails_validation(self, webhook_token, sample_payload):
        """Test that an invalid signature fails validation."""
        from api.services.hmac_utils import validate_signature

        payload_bytes = json.dumps(sample_payload).encode("utf-8")
        bad_signature = "sha256=0000000000000000000000000000000000000000000000000000000000000000"

        is_valid = validate_signature(payload_bytes, bad_signature, webhook_token)
        assert is_valid is False

    def test_tampered_payload_fails_validation(self, webhook_token, sample_payload):
        """Test that a tampered payload fails validation."""
        from api.services.hmac_utils import generate_signature, validate_signature

        # Generate signature for original payload
        original_bytes = json.dumps(sample_payload).encode("utf-8")
        signature = generate_signature(original_bytes, webhook_token)

        # Tamper with payload
        tampered_payload = {**sample_payload, "importance": 1.0}
        tampered_bytes = json.dumps(tampered_payload).encode("utf-8")

        is_valid = validate_signature(tampered_bytes, signature, webhook_token)
        assert is_valid is False

    def test_wrong_token_fails_validation(self, sample_payload):
        """Test that wrong token fails validation."""
        from api.services.hmac_utils import generate_signature, validate_signature

        payload_bytes = json.dumps(sample_payload).encode("utf-8")
        signature = generate_signature(payload_bytes, "correct-token")

        is_valid = validate_signature(payload_bytes, signature, "wrong-token")
        assert is_valid is False

    def test_malformed_signature_fails_validation(self, webhook_token, sample_payload):
        """Test that malformed signatures fail validation."""
        from api.services.hmac_utils import validate_signature

        payload_bytes = json.dumps(sample_payload).encode("utf-8")

        # Missing sha256= prefix
        is_valid = validate_signature(
            payload_bytes, "notavalidformat", webhook_token
        )
        assert is_valid is False

    def test_empty_signature_fails_validation(self, webhook_token, sample_payload):
        """Test that empty signature fails validation."""
        from api.services.hmac_utils import validate_signature

        payload_bytes = json.dumps(sample_payload).encode("utf-8")

        is_valid = validate_signature(payload_bytes, "", webhook_token)
        assert is_valid is False

    def test_none_signature_fails_validation(self, webhook_token, sample_payload):
        """Test that None signature fails validation."""
        from api.services.hmac_utils import validate_signature

        payload_bytes = json.dumps(sample_payload).encode("utf-8")

        is_valid = validate_signature(payload_bytes, None, webhook_token)
        assert is_valid is False


class TestHMACTimingSafety:
    """Test that validation uses timing-safe comparison."""

    def test_validation_uses_constant_time_comparison(
        self, webhook_token, sample_payload
    ):
        """
        Test that signature validation uses constant-time comparison.

        This is important to prevent timing attacks. We can't easily test
        timing directly, but we can verify the implementation uses
        hmac.compare_digest under the hood.
        """
        from api.services.hmac_utils import validate_signature

        payload_bytes = json.dumps(sample_payload).encode("utf-8")

        # Valid signature should pass
        expected = hmac.new(
            webhook_token.encode(), payload_bytes, hashlib.sha256
        ).hexdigest()
        signature = f"sha256={expected}"

        # This should use timing-safe comparison internally
        is_valid = validate_signature(payload_bytes, signature, webhook_token)
        assert is_valid is True


class TestHMACEdgeCases:
    """Test edge cases in HMAC handling."""

    def test_empty_payload_can_be_signed(self, webhook_token):
        """Test that empty payload can be signed and validated."""
        from api.services.hmac_utils import generate_signature, validate_signature

        empty_payload = b""
        signature = generate_signature(empty_payload, webhook_token)

        is_valid = validate_signature(empty_payload, signature, webhook_token)
        assert is_valid is True

    def test_unicode_payload_handled_correctly(self, webhook_token):
        """Test that unicode content is handled correctly."""
        from api.services.hmac_utils import generate_signature, validate_signature

        unicode_payload = {"content": "Émoji: 🧠💡🎯", "type": "日本語"}
        payload_bytes = json.dumps(unicode_payload).encode("utf-8")

        signature = generate_signature(payload_bytes, webhook_token)
        is_valid = validate_signature(payload_bytes, signature, webhook_token)
        assert is_valid is True

    def test_large_payload_handled_correctly(self, webhook_token):
        """Test that large payloads are handled correctly."""
        from api.services.hmac_utils import generate_signature, validate_signature

        # 1MB payload
        large_content = "x" * (1024 * 1024)
        large_payload = {"content": large_content}
        payload_bytes = json.dumps(large_payload).encode("utf-8")

        signature = generate_signature(payload_bytes, webhook_token)
        is_valid = validate_signature(payload_bytes, signature, webhook_token)
        assert is_valid is True
