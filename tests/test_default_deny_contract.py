"""FR-09 — matrix_enforcer default-deny 계약.

미등록 경로 정책 3-모드: off(현행 default-allow) / observe(로그+통과, 미분류 수집) /
enforce(공개 allowlist 외 403). 기본 off = 현행 동작 100% 보존(NFR-07).

미등록 경로 판정은 user 해석 이전(perm is None 분기)이라 DB 불요 → enforce_matrix(req, None) 로 구동.
※ enforce 실제 활성은 observe 로 '미분류 0' 확인 + 배포 게이트 후(본 테스트는 로직 계약만).
"""
from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.config import settings
from app.security.matrix_enforcer import enforce_matrix, is_public_allowlisted

UNREGISTERED = "/api/some/unregistered-path"


def _req(method: str, path: str):
    scope = {"type": "http", "method": method, "headers": [],
             "route": SimpleNamespace(path=path), "query_string": b""}
    return Request(scope)


def _run(method: str, path: str):
    """미등록/공개 경로에 대한 enforce_matrix 결과: 'ALLOW' | int(status)."""
    try:
        asyncio.run(enforce_matrix(_req(method, path), None))
        return "ALLOW"
    except HTTPException as e:
        return e.status_code


@pytest.fixture
def token_mode(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_MODE", "token")


def test_should_allow_unregistered_when_mode_off(token_mode, monkeypatch):
    monkeypatch.setattr(settings, "MATRIX_DENY_MODE", "off")
    assert _run("GET", UNREGISTERED) == "ALLOW"


def test_should_allow_unregistered_when_mode_observe(token_mode, monkeypatch):
    # observe: 차단 안 함(로그만) → 통과. 라이브에서 미분류 경로 수집용.
    monkeypatch.setattr(settings, "MATRIX_DENY_MODE", "observe")
    assert _run("GET", UNREGISTERED) == "ALLOW"


def test_should_403_unregistered_when_mode_enforce(token_mode, monkeypatch):
    monkeypatch.setattr(settings, "MATRIX_DENY_MODE", "enforce")
    assert _run("GET", UNREGISTERED) == 403


def test_should_allow_public_allowlist_when_mode_enforce(token_mode, monkeypatch):
    monkeypatch.setattr(settings, "MATRIX_DENY_MODE", "enforce")
    assert _run("GET", "/health") == "ALLOW"
    assert _run("GET", "/docs") == "ALLOW"
    assert _run("GET", "/openapi.json") == "ALLOW"
    assert _run("POST", "/api/auth/login") == "ALLOW"


def test_should_bypass_deny_when_public_auth_mode(monkeypatch):
    # AUTH_MODE=public → enforce_matrix 즉시 통과(default-deny 모드 무관)
    monkeypatch.setattr(settings, "AUTH_MODE", "public")
    monkeypatch.setattr(settings, "MATRIX_DENY_MODE", "enforce")
    assert _run("GET", UNREGISTERED) == "ALLOW"


def test_should_classify_public_paths_in_allowlist_helper():
    assert is_public_allowlisted("GET", "/health") is True
    assert is_public_allowlisted("GET", "/docs") is True
    assert is_public_allowlisted("POST", "/api/auth/login") is True
    assert is_public_allowlisted("GET", "/api/devices/cameras") is False  # 인증 필요 read
