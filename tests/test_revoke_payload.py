"""
Force-Logout revoke payload + signing (P1 Phase 2) tests.
PRD: docs/prds/PRD_GOP_Server_Force_Logout.md (FR-SVF-06/07/12)

Contract C3: HMAC-SHA256 over a canonical JSON (sorted keys, compact separators,
UTF-8, all fields EXCEPT `signature`) using a DEDICATED REVOKE_SIGNING_KEY.
The canonical form is a cross-language interop contract with the .NET client,
so it is pinned with a golden vector here.
"""
import pytest

from app.schemas.revoke import RevokePayload
from app.utils.enums import EnumLogoutReason
from app.utils.revoke_signing import canonical_bytes, sign_revoke, verify_revoke, build_signed_revoke


KEY = "test-revoke-signing-key-0123456789abcdef"


class TestRevokeCanonicalSerialization:
    def test_canonical_form_is_pinned_golden_vector(self):
        # Sorted keys, compact separators, signature excluded, nulls emitted explicitly.
        payload = {
            "message_id": "m1",
            "session_id": "42",
            "jti": "j1",
            "user_id": 7,
            "reason": "FORCED",
            "issued_at": "2026-06-30T00:00:00Z",
            "signature": "SHOULD_BE_EXCLUDED",
        }
        expected = (
            '{"issued_at":"2026-06-30T00:00:00Z","jti":"j1","message_id":"m1",'
            '"reason":"FORCED","session_id":"42","user_id":7}'
        )
        assert canonical_bytes(payload).decode("utf-8") == expected

    def test_canonical_emits_null_jti_explicitly(self):
        # Null semantics: jti absent (user-wide revoke) must serialize as null, not be omitted.
        payload = {
            "message_id": "m2", "session_id": None, "jti": None,
            "user_id": 9, "reason": "LOCKED", "issued_at": "2026-06-30T01:00:00Z",
        }
        text = canonical_bytes(payload).decode("utf-8")
        assert '"jti":null' in text and '"session_id":null' in text


class TestRevokeSignature:
    def test_signature_roundtrips(self):
        signed = build_signed_revoke(
            message_id="m1", session_id="42", jti="j1", user_id=7,
            reason=EnumLogoutReason.FORCED, issued_at="2026-06-30T00:00:00Z", key=KEY,
        )
        assert "signature" in signed and signed["signature"]
        assert verify_revoke(signed, KEY) is True

    def test_signature_detects_tamper(self):
        signed = build_signed_revoke(
            message_id="m1", session_id="42", jti="j1", user_id=7,
            reason=EnumLogoutReason.FORCED, issued_at="2026-06-30T00:00:00Z", key=KEY,
        )
        signed["session_id"] = "99"  # tamper after signing
        assert verify_revoke(signed, KEY) is False

    def test_verify_fails_with_wrong_key(self):
        signed = build_signed_revoke(
            message_id="m1", session_id="42", jti="j1", user_id=7,
            reason=EnumLogoutReason.FORCED, issued_at="2026-06-30T00:00:00Z", key=KEY,
        )
        assert verify_revoke(signed, "another-key-0000000000000000000000") is False


class TestRevokePayloadSchema:
    def test_accepts_valid_reason_enum(self):
        p = RevokePayload(
            message_id="m1", session_id="42", jti="j1", user_id=7,
            reason=EnumLogoutReason.FORCED, issued_at="2026-06-30T00:00:00Z",
        )
        assert p.reason == EnumLogoutReason.FORCED

    def test_rejects_free_text_reason(self):
        # FR-SVF-12: reason must be a predefined enum code, no free text / URLs.
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            RevokePayload(
                message_id="m1", session_id="42", jti="j1", user_id=7,
                reason="http://phishing.example/login", issued_at="2026-06-30T00:00:00Z",
            )

    def test_allows_null_jti_for_user_wide_revoke(self):
        p = RevokePayload(
            message_id="m2", session_id=None, jti=None, user_id=9,
            reason=EnumLogoutReason.PASSWORD_CHANGED, issued_at="2026-06-30T01:00:00Z",
        )
        assert p.jti is None and p.user_id == 9
