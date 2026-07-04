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
    # 이벤트 — connections (v6.0 후속 Phase 5 확대)
    ("POST", "/api/events/connections"): ("events", "edit"),
    ("PATCH", "/api/events/connections/{}"): ("events", "edit"),
    ("PUT", "/api/events/connections/{}"): ("events", "edit"),
    ("DELETE", "/api/events/connections/{}"): ("events", "delete"),
    # 장비 — speakers (v6.0 후속 Phase 5 확대)
    ("POST", "/api/devices/speakers"): ("devices", "edit"),
    ("PATCH", "/api/devices/speakers/{}"): ("devices", "edit"),
    ("PUT", "/api/devices/speakers/{}"): ("devices", "edit"),
    ("DELETE", "/api/devices/speakers/{}"): ("devices", "delete"),
    # 장비 — enclosures (v6.0 후속 Phase 5 확대)
    ("POST", "/api/devices/enclosures"): ("devices", "edit"),
    ("PATCH", "/api/devices/enclosures/{}"): ("devices", "edit"),
    ("PUT", "/api/devices/enclosures/{}"): ("devices", "edit"),
    ("DELETE", "/api/devices/enclosures/{}"): ("devices", "delete"),
    ("PATCH", "/api/devices/enclosures/{}/status"): ("devices", "edit"),
    ("POST", "/api/devices/enclosures/{}/control"): ("devices", "edit"),
    # 장비 — lamps (v6.0 후속 Phase 5 확대)
    ("POST", "/api/devices/lamps"): ("devices", "edit"),
    ("PATCH", "/api/devices/lamps/{}"): ("devices", "edit"),
    ("PUT", "/api/devices/lamps/{}"): ("devices", "edit"),
    ("DELETE", "/api/devices/lamps/{}"): ("devices", "delete"),
    # 장비 — device_groups (v6.0 후속 Phase 5 확대)
    ("POST", "/api/devices/groups"): ("devices", "edit"),
    ("PATCH", "/api/devices/groups/{}"): ("devices", "edit"),
    ("PUT", "/api/devices/groups/{}"): ("devices", "edit"),
    ("DELETE", "/api/devices/groups/{}"): ("devices", "delete"),
    # 함체 metrics (v6.0 후속 Phase 5 확대)
    ("POST", "/api/enclosure-metrics"): ("devices", "edit"),
    ("DELETE", "/api/enclosure-metrics/{}"): ("devices", "delete"),
    # 서버
    ("POST", "/api/servers"): ("servers", "edit"),
    ("PATCH", "/api/servers/{}"): ("servers", "edit"),  # v6.0 후속: PATCH 추가 (기존 PUT만)
    ("PUT", "/api/servers/{}"): ("servers", "edit"),
    ("DELETE", "/api/servers/{}"): ("servers", "delete"),
    # 서버 카테고리 (v6.0 후속 Phase 5 확대)
    ("POST", "/api/servers/categories"): ("servers", "edit"),
    ("PATCH", "/api/servers/categories/{}"): ("servers", "edit"),
    ("PUT", "/api/servers/categories/{}"): ("servers", "edit"),
    ("DELETE", "/api/servers/categories/{}"): ("servers", "delete"),
    # 서버 metrics (v6.0 후속 Phase 5 확대)
    ("POST", "/api/servers/{}/metrics"): ("servers", "edit"),
    # 서버 proxy_settings (v6.0 후속 Phase 5 확대)
    ("PATCH", "/api/servers/{}/proxy-settings"): ("servers", "edit"),
    ("PUT", "/api/servers/{}/proxy-settings"): ("servers", "edit"),
    # 시스템 이벤트 (v6.0 후속 Phase 5 확대)
    ("POST", "/api/system-events"): ("events", "edit"),
    ("PATCH", "/api/system-events/{}/acknowledge"): ("events", "edit"),
    ("DELETE", "/api/system-events/{}"): ("events", "delete"),
    # Integrations — event mappings (v6.0 후속 Phase 5 확대)
    ("POST", "/api/integrations/event-mappings"): ("integrations", "edit"),
    ("PATCH", "/api/integrations/event-mappings/{}"): ("integrations", "edit"),
    ("PUT", "/api/integrations/event-mappings/{}"): ("integrations", "edit"),
    ("DELETE", "/api/integrations/event-mappings/{}"): ("integrations", "delete"),
    # Integrations — bulk mapping cameras/lamps/speakers (v6.0 후속 Phase 5 확대)
    ("POST", "/api/integrations/event-mappings/{}/cameras"): ("integrations", "edit"),
    ("DELETE", "/api/integrations/event-mappings/{}/cameras"): ("integrations", "delete"),
    ("POST", "/api/integrations/event-mappings/{}/lamps"): ("integrations", "edit"),
    ("DELETE", "/api/integrations/event-mappings/{}/lamps"): ("integrations", "delete"),
    ("POST", "/api/integrations/event-mappings/{}/speakers"): ("integrations", "edit"),
    ("DELETE", "/api/integrations/event-mappings/{}/speakers"): ("integrations", "delete"),
    # File groups (v6.0 후속 Phase 5 확대)
    ("POST", "/api/file-groups"): ("files", "edit"),
    ("PATCH", "/api/file-groups/{}"): ("files", "edit"),
    ("PUT", "/api/file-groups/{}"): ("files", "edit"),
    ("DELETE", "/api/file-groups/{}"): ("files", "delete"),
    # Thumbnails (v6.0 후속 Phase 5 확대)
    ("POST", "/api/thumbnails"): ("files", "edit"),
    ("DELETE", "/api/thumbnails/{}"): ("files", "delete"),
    # Camera settings / presets / ROIs / xypoints (v6.0 후속 Phase 5 확대)
    ("POST", "/api/devices/cameras/{}/settings"): ("cameras", "edit"),
    ("PATCH", "/api/devices/cameras/{}/settings"): ("cameras", "edit"),
    ("PUT", "/api/devices/cameras/{}/settings"): ("cameras", "edit"),
    ("POST", "/api/devices/cameras/{}/presets"): ("cameras", "edit"),
    ("PATCH", "/api/devices/cameras/{}/presets/{}"): ("cameras", "edit"),
    ("PUT", "/api/devices/cameras/{}/presets/{}"): ("cameras", "edit"),
    ("DELETE", "/api/devices/cameras/{}/presets/{}"): ("cameras", "delete"),
    # 보고서 — v5.4 P2-2 (클라 REQ #2 서버측 verb RBAC 집행)
    ("POST", "/api/reports/generate"): ("reports", "edit"),
    ("POST", "/api/reports/templates"): ("reports", "edit"),
    ("PATCH", "/api/reports/templates/{}"): ("reports", "edit"),
    ("PUT", "/api/reports/templates/{}"): ("reports", "edit"),
    ("DELETE", "/api/reports/templates/{}"): ("reports", "delete"),
    ("DELETE", "/api/reports/generations/{}"): ("reports", "delete"),
    # v6.0 후속: 진행 중 리포트 생성 취소 (권한은 delete와 동급)
    ("POST", "/api/reports/generations/{}/cancel"): ("reports", "delete"),
    ("GET", "/api/reports/preview/{}"): ("reports", "view"),
    ("GET", "/api/reports/generations/{}/download"): ("reports", "view"),
    ("GET", "/api/reports/generations/{}/preview"): ("reports", "view"),
    ("GET", "/api/reports/generations/{}/preview-page"): ("reports", "view"),
}


def lookup_permission(method: str, path: str) -> Optional[Tuple[str, str]]:
    """(method, 경로템플릿) 에 요구되는 (module, verb). 미등록이면 None(=요구 없음)."""
    return PERMISSION_MAP.get((method.upper(), normalize_path(path)))
