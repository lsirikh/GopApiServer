"""
P2-02 (review0710): Public GET allowlist 계약 테스트 — P0-01 재발 방지.

배경: review0710 P0-01 에서 config-change-logs·system-events·event-statistics 3개 라우터의 GET 이
permission_map 누락으로 전역 enforce_matrix(default-allow, 미매핑 경로 통과)를 타 **무토큰 200** 노출됐다.
수정: 각 라우터 GET 에 route-level 가드(require_perm_async / require_perm_optional_async)를 부착.

본 계약은 두 층으로 재발을 못박는다.
  1) 구조(단위, 서버 불요): 3개 민감 라우터의 모든 GET 이 route-level 인증 의존성을 갖는지 introspection.
  2) 행동(라이브, 서버 기동 시에만): /openapi.json 의 모든 GET 을 무토큰 호출 →
     PUBLIC_GET_ALLOWLIST 외 어떤 경로도 2xx(데이터 노출)를 반환하지 않음을 검증.

- 라이브 층은 서버 미기동 시 skip(CI 헤드리스 안전). dev 컨테이너 대상 5중 싱크 검증 시 실행된다.
- BASE_URL 기본 https://localhost:8000, GOP_CONTRACT_BASE_URL 로 재정의.
"""
from __future__ import annotations

import os
import re

import pytest

# route-level 인증을 표상하는 의존성 콜러블 이름(auth.py 의 클로저/함수).
#   require_perm_async→_perm_checker, require_perm_optional_async→_perm_checker_optional,
#   require_admin_async→_role_checker, 직접 주입→get_current_account_user(_async).
#   전역 enforce_matrix 는 default-allow 라 '보호 신호'가 아니므로 의도적으로 제외.
_AUTH_CALLABLES = {
    "_perm_checker",
    "_perm_checker_optional",
    "_role_checker",
    "get_current_account_user",
    "get_current_account_user_async",
}

# P0-01 로 route-level 가드를 부착한 민감 라우터(모듈경로, 표시명).
_SENSITIVE_ROUTER_MODULES = [
    ("app.routers.config_change_logs", "config_change_logs"),
    ("app.routers.system_events", "system_events"),
    ("app.routers.event_statistics", "event_statistics"),
]

BASE_URL = os.environ.get("GOP_CONTRACT_BASE_URL", "https://localhost:8000")

# 무토큰 2xx 가 '의도된 공개' 인 GET 경로(openapi path 템플릿 그대로).
#   / , /health , /api/tracking/health : 공개 헬스/랜딩
#   /api/users/photo/{file_name} : <img src> 렌더용 프로필 사진(비추측 파일명 전제) — 의도된 공개
PUBLIC_GET_ALLOWLIST = {
    "/",
    "/health",
    "/api/tracking/health",
    "/api/users/photo/{file_name}",
}


def _flatten_dependency_names(dependant) -> set[str]:
    """route.dependant 트리를 재귀 평탄화해 모든 의존성 콜러블의 __name__ 집합을 반환."""
    names: set[str] = set()
    for sub in dependant.dependencies:
        if sub.call is not None:
            names.add(getattr(sub.call, "__name__", ""))
        names |= _flatten_dependency_names(sub)
    return names


def _iter_get_routes(router):
    """APIRouter 의 GET APIRoute 를 순회."""
    from fastapi.routing import APIRoute

    for route in router.routes:
        if isinstance(route, APIRoute) and "GET" in route.methods:
            yield route


# ---------------------------------------------------------------------------
# 1) 구조 계약 — 서버/DB 불요 (CI 상시 실행)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("module_path,display_name", _SENSITIVE_ROUTER_MODULES)
def test_should_have_route_level_auth_when_sensitive_router_get(module_path, display_name):
    """민감 라우터의 모든 GET 은 route-level 인증 의존성을 가져야 한다 (P0-01 구조 재발 방지)."""
    import importlib

    module = importlib.import_module(module_path)
    routes = list(_iter_get_routes(module.router))
    assert routes, f"{display_name}: GET 라우트가 없음 — introspection 경로 확인 필요"

    unguarded = [
        route.path
        for route in routes
        if not (_flatten_dependency_names(route.dependant) & _AUTH_CALLABLES)
    ]
    assert not unguarded, (
        f"{display_name}: route-level 인증 미부착 GET = {unguarded} "
        f"(허용 콜러블 {sorted(_AUTH_CALLABLES)})"
    )


# ---------------------------------------------------------------------------
# 2) 행동 계약 — 라이브 서버 대상 (미기동 시 skip)
# ---------------------------------------------------------------------------

def _server_up() -> bool:
    try:
        import httpx

        httpx.Client(verify=False, timeout=3.0).get(BASE_URL + "/health")
        return True
    except Exception:
        return False


_LIVE = _server_up()
_live_only = pytest.mark.skipif(
    not _LIVE,
    reason=f"라이브 서버({BASE_URL}) 미기동 — 행동 계약은 dev 컨테이너 기동 시에만 실행",
)


def _live_get_paths() -> list[str]:
    import httpx

    client = httpx.Client(verify=False, timeout=10.0)
    spec = client.get(BASE_URL + "/openapi.json").json()
    return [path for path, ops in spec["paths"].items() if "get" in ops]


@_live_only
def test_should_not_serve_2xx_without_token_when_not_in_allowlist():
    """무토큰 GET 은 PUBLIC_GET_ALLOWLIST 외 어떤 경로도 2xx 를 반환하지 않는다."""
    import httpx

    client = httpx.Client(verify=False, timeout=10.0)
    violations = []
    for path in _live_get_paths():
        if path in PUBLIC_GET_ALLOWLIST:
            continue
        url = BASE_URL + re.sub(r"\{[^}]+\}", "999999", path)  # path param → dummy
        code = client.get(url).status_code
        if 200 <= code < 300:
            violations.append((path, code))
    assert not violations, (
        f"무토큰 2xx 노출(가드 유실 또는 allowlist 누락): {violations}"
    )


@_live_only
@pytest.mark.parametrize(
    "path",
    ["/api/config-change-logs", "/api/system-events", "/api/events/statistics/summary"],
)
def test_should_reject_with_401_when_sensitive_get_without_token(path):
    """P0-01 민감 GET 3종은 무토큰 시 명시적으로 401 이어야 한다."""
    import httpx

    client = httpx.Client(verify=False, timeout=10.0)
    code = client.get(BASE_URL + path).status_code
    assert code == 401, f"{path} 무토큰 응답 {code} (기대 401)"


@_live_only
@pytest.mark.parametrize("path", ["/", "/health", "/api/tracking/health"])
def test_should_be_reachable_when_public_allowlist_get(path):
    """PUBLIC_GET_ALLOWLIST 의 무파라미터 공개 경로는 무토큰으로도 2xx 여야 한다(allowlist 노후화 감지)."""
    import httpx

    client = httpx.Client(verify=False, timeout=10.0)
    code = client.get(BASE_URL + path).status_code
    assert 200 <= code < 300, f"{path} 공개 경로 응답 {code} (기대 2xx)"
