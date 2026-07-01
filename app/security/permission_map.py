"""
권한 중앙 매핑 — (HTTP 메서드 × 경로 템플릿) → (module, verb)
PRD: "매트릭스 미들웨어" 방향 (사용자 결정 2026-06-30)

설계:
- 권한 매트릭스(그룹 JSONB)가 **정책/데이터**, 본 맵 + matrix_enforcer 가 **단일 집행점(미들웨어)**.
- 경로 템플릿의 path-param 은 `{}` 로 정규화 → 파라미터 명(camera_id/event_id 등) 변동에 견고.
- 본 맵은 기존 27개 `require_perm_optional` 데코레이터와 **동일 커버리지**(token 모드 동작 불변).
  추가 라우트 보호는 여기 한 곳에 등록 → 데코레이터 누락으로 뚫리는 사고 구조적 차단(default-allow→점진 default-deny 가능).
"""
from __future__ import annotations

import re
from typing import Optional, Tuple

_PARAM_RE = re.compile(r"\{[^}]+\}")


def normalize_path(path: str) -> str:
    """경로 템플릿의 `{param}` 을 `{}` 로 정규화. 트레일링 슬래시 제거."""
    norm = _PARAM_RE.sub("{}", path or "")
    if len(norm) > 1 and norm.endswith("/"):
        norm = norm[:-1]
    return norm


# (METHOD, 정규화 경로) → (module, verb)
# 기존 27개 require_perm_optional 데코레이터를 1:1 반영(actions/cameras/controllers/detections/malfunctions/sensors/servers).
PERMISSION_MAP: dict[Tuple[str, str], Tuple[str, str]] = {
    # 이벤트 — actions
    ("POST", "/api/events/actions"): ("events", "edit"),
    ("PATCH", "/api/events/actions/{}"): ("events", "edit"),
    ("PUT", "/api/events/actions/{}"): ("events", "edit"),
    ("DELETE", "/api/events/actions/{}"): ("events", "delete"),
    # 이벤트 — detections
    ("POST", "/api/events/detections"): ("events", "edit"),
    ("PATCH", "/api/events/detections/{}"): ("events", "edit"),
    ("PUT", "/api/events/detections/{}"): ("events", "edit"),
    ("DELETE", "/api/events/detections/{}"): ("events", "delete"),
    # 이벤트 — malfunctions
    ("POST", "/api/events/malfunctions"): ("events", "edit"),
    ("PATCH", "/api/events/malfunctions/{}"): ("events", "edit"),
    ("PUT", "/api/events/malfunctions/{}"): ("events", "edit"),
    ("DELETE", "/api/events/malfunctions/{}"): ("events", "delete"),
    # 장비 — cameras (control 은 별도 PTZ 경로에서 추후 등록)
    ("POST", "/api/devices/cameras"): ("cameras", "edit"),
    ("PATCH", "/api/devices/cameras/{}"): ("cameras", "edit"),
    ("PUT", "/api/devices/cameras/{}"): ("cameras", "edit"),
    ("DELETE", "/api/devices/cameras/{}"): ("cameras", "delete"),
    # 장비 — controllers
    ("POST", "/api/devices/controllers"): ("devices", "edit"),
    ("PATCH", "/api/devices/controllers/{}"): ("devices", "edit"),
    ("PUT", "/api/devices/controllers/{}"): ("devices", "edit"),
    ("DELETE", "/api/devices/controllers/{}"): ("devices", "delete"),
    # 장비 — sensors
    ("POST", "/api/devices/sensors"): ("devices", "edit"),
    ("PATCH", "/api/devices/sensors/{}"): ("devices", "edit"),
    ("PUT", "/api/devices/sensors/{}"): ("devices", "edit"),
    ("DELETE", "/api/devices/sensors/{}"): ("devices", "delete"),
    # 서버
    ("POST", "/api/servers"): ("servers", "edit"),
    ("PUT", "/api/servers/{}"): ("servers", "edit"),
    ("DELETE", "/api/servers/{}"): ("servers", "delete"),
}


def lookup_permission(method: str, path: str) -> Optional[Tuple[str, str]]:
    """(method, 경로템플릿) 에 요구되는 (module, verb). 미등록이면 None(=요구 없음)."""
    return PERMISSION_MAP.get((method.upper(), normalize_path(path)))
