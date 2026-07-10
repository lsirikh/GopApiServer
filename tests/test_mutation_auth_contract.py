"""
AUTH-01 — mutation 인증 contract 테스트.

모든 POST/PUT/PATCH/DELETE(/api) operation 은 OpenAPI security 를 가져야 한다
(= 인증 dependency 부착). 의도적 공개(로그인/토큰 갱신)만 명시 허용목록으로 예외.
새 mutation 이 인증 없이 추가되면 이 테스트가 실패해 회귀를 잡는다.
"""
from app.main import app

# 의도적으로 인증이 없는(=공개) mutation — 인증 없이 호출되어야 하는 엔드포인트.
PUBLIC_MUTATIONS = {
    ("POST", "/api/auth/login"),    # 로그인 자체는 인증 불가
    ("POST", "/api/auth/refresh"),  # refresh 토큰(body)으로 재발급 — bearer 불요
}


def _mutations_without_security() -> list[tuple[str, str]]:
    spec = app.openapi()
    global_sec = spec.get("security")
    out = []
    for path, item in spec["paths"].items():
        for method, op in item.items():
            if method.upper() not in ("POST", "PUT", "PATCH", "DELETE"):
                continue
            sec = op.get("security", global_sec)
            if not sec:
                out.append((method.upper(), path))
    return out


def test_should_have_security_on_all_mutations_except_allowlist():
    naked = set(_mutations_without_security())
    unexpected = naked - PUBLIC_MUTATIONS
    assert not unexpected, (
        "인증 없는 mutation 발견(허용목록 외) — 인가 dependency 부착 필요: "
        + ", ".join(f"{m} {p}" for m, p in sorted(unexpected))
    )


def test_allowlisted_public_mutations_still_exist():
    """허용목록이 stale 되지 않도록 — 목록의 공개 endpoint 가 실제 존재하는지 확인."""
    spec = app.openapi()
    for method, path in PUBLIC_MUTATIONS:
        assert path in spec["paths"], f"allowlist stale: {path} 없음"
        assert method.lower() in spec["paths"][path], f"allowlist stale: {method} {path} 없음"
