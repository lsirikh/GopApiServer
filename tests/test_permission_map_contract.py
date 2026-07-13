"""
AUTH-01 후속 — permission_map ↔ OpenAPI 정합 contract 테스트.

중앙 permission_map 의 모든 (method, path) 키는 실제 OpenAPI 라우트와 매칭돼야 한다.
매칭 안 되는 stale 항목은 enforce_matrix 가 절대 발화하지 않는 죽은 코드 →
"보호되는 것처럼 보이나 실제로는 무집행"인 위험한 착시를 만든다.
이 테스트가 stale 재유입을 회귀로 잡는다. (리뷰 AUTH-01 제안 #1: map↔OpenAPI 자동 비교.)
"""
from app.main import app
from app.security.permission_map import PERMISSION_MAP, normalize_path


def _real_routes() -> set[tuple[str, str]]:
    real = set()
    for path, item in app.openapi()["paths"].items():
        for method, op in item.items():
            if method.upper() in ("GET", "POST", "PUT", "PATCH", "DELETE"):
                real.add((method.upper(), normalize_path(path)))
    return real


def test_should_have_no_stale_entries_in_permission_map():
    """permission_map 의 모든 키가 실제 OpenAPI 라우트에 존재해야 한다(stale=0)."""
    real = _real_routes()
    stale = [(m, p) for (m, p) in PERMISSION_MAP if (m, p) not in real]
    assert not stale, (
        "permission_map 에 실제 라우트와 매칭되지 않는 stale 항목 존재(무집행 착시): "
        + ", ".join(f"{m} {p}" for m, p in sorted(stale))
    )


def test_permission_map_values_are_module_verb_pairs():
    """모든 값이 (module, verb) 형태이고 verb 가 허용된 4종인지 확인(오타 방지)."""
    allowed_verbs = {"view", "edit", "delete", "control"}
    bad = [
        (k, v) for k, v in PERMISSION_MAP.items()
        if not (isinstance(v, tuple) and len(v) == 2 and v[1] in allowed_verbs)
    ]
    assert not bad, f"잘못된 (module, verb) 값: {bad}"
