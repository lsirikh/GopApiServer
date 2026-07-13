"""
SEC-01 — api_logs 요청 body 마스킹(redact_request_body) 단위 테스트.

로그인 비밀번호·토큰이 api_logs.body 에 평문 저장되던 문제를 코드 레벨에서 차단한다.
순수함수라 DB/async harness 없이 검증한다.
"""
import json

from app.middleware.logging import redact_request_body, _REDACTED


class TestRedactRequestBody:
    def test_should_mask_password_when_login_body(self):
        out = redact_request_body('{"login_id": "admin", "password": "secret1"}')
        parsed = json.loads(out)
        assert parsed["password"] == _REDACTED
        assert parsed["login_id"] == "admin"  # 비민감 필드는 보존

    def test_should_mask_all_sensitive_keys(self):
        raw = json.dumps({
            "current_password": "a", "new_password": "b", "user_password": "c",
            "access_token": "d", "refresh_token": "e", "token": "f",
            "secret": "g", "authorization": "h", "keep": "visible",
        })
        parsed = json.loads(redact_request_body(raw))
        for k in ("current_password", "new_password", "user_password",
                  "access_token", "refresh_token", "token", "secret", "authorization"):
            assert parsed[k] == _REDACTED
        assert parsed["keep"] == "visible"

    def test_should_mask_nested_and_list_values(self):
        raw = json.dumps({"outer": {"password": "x"}, "items": [{"token": "y"}]})
        parsed = json.loads(redact_request_body(raw))
        assert parsed["outer"]["password"] == _REDACTED
        assert parsed["items"][0]["token"] == _REDACTED

    def test_should_be_case_insensitive_on_keys(self):
        parsed = json.loads(redact_request_body('{"Password": "x", "REFRESH_TOKEN": "y"}'))
        assert parsed["Password"] == _REDACTED
        assert parsed["REFRESH_TOKEN"] == _REDACTED

    def test_should_return_none_when_non_json_body(self):
        # 폼/멀티파트/평문은 파싱 불가 → 원문 저장 금지(보수적 default-deny)
        assert redact_request_body("login_id=admin&password=secret") is None
        assert redact_request_body("--multipart-boundary--") is None

    def test_should_passthrough_none_and_empty(self):
        assert redact_request_body(None) is None
        assert redact_request_body("") == ""
