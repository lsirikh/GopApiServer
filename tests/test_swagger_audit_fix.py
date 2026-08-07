"""Swagger 전수 감사(2026-08-07) 수정분 회귀 고정 — `v6.3-swagger_audit_fix`.

라이브 서버 없이 **순수 단위**로 고정 가능한 것만 담는다(라우터 HTTP E2E 는 라이브 검증 스크립트가 담당).
목적은 "고친 것이 다시 무너지지 않게" 소스/스키마 레벨에서 못박는 것.

대상:
- A-01/A-02  auth.py 가 출력 시각에 `.replace(tzinfo=)`(라벨 교체)를 쓰지 않는다
- S3-01      통계 버킷이 DISPLAY_TIMEZONE 으로 변환된다
- S3-02      이벤트 요청 스키마에 기계판독 enum 이 실린다
- S3-04      interval 이 hour|day 로 제한된다
- S3-06      억제 PATCH 가 NOT NULL 필드의 명시적 null 을 거부한다
- S5-01      /api/logs 날짜 파라미터가 datetime 으로 승격됐다
- A-04       lock 요청 스키마(UserLockRequest)가 존재한다
- X-01/X-02  파괴적 Example 이 무해값으로 고정됐다
"""
from __future__ import annotations

import inspect
import re
from datetime import datetime, timedelta, timezone

import pytest


# ─────────────────────────────────────────────────────────────
# A-01 / A-02 — 출력 시각은 라벨 교체가 아니라 변환이어야 한다
# ─────────────────────────────────────────────────────────────

def test_should_not_relabel_tzinfo_when_rendering_auth_output():
    """auth.py 에 `.replace(tzinfo=...)` 호출이 **실행 코드로** 남아 있으면 실패.

    이 패턴이 9시간 오차의 직접 원인이었다(값은 UTC, 라벨만 KST).
    주석·docstring 의 언급은 허용해야 하므로 문자열 검색이 아니라 **AST 로 실제 호출만** 본다.
    """
    import ast

    from app.routers import auth as auth_mod

    tree = ast.parse(inspect.getsource(auth_mod))
    offenders = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "replace"
        and any(kw.arg == "tzinfo" for kw in node.keywords)
    ]
    assert not offenders, f"auth.py 실행 코드에 tzinfo 라벨 교체가 남아있음 (lines={offenders})"


def test_should_expose_utc_semantics_in_now_helper_name():
    """`_kst_now` 라는 오해 유발 이름이 부활하면 실패 (실제 반환은 aware UTC)."""
    from app.routers import auth as auth_mod

    assert hasattr(auth_mod, "_now_utc"), "_now_utc 헬퍼가 있어야 한다"
    assert not hasattr(auth_mod, "_kst_now"), "_kst_now 는 이름이 실체와 달라 폐기됨"
    now = auth_mod._now_utc()
    assert now.tzinfo is not None, "aware 여야 한다"
    assert now.utcoffset() == timedelta(0), "UTC 여야 한다"


def test_should_convert_not_relabel_when_to_display():
    """to_display 는 값을 변환한다 — 회귀 시 9시간 오차가 되살아난다."""
    from app.config import settings
    from app.utils.datetime import to_display

    src = datetime(2026, 8, 7, 4, 16, 49, tzinfo=timezone.utc)   # = 13:16:49 KST
    out = to_display(src)
    assert out.utcoffset() == settings.display_tz.utcoffset(src)
    assert out.replace(tzinfo=None) != src.replace(tzinfo=None), "라벨만 바뀌면 안 된다"
    assert out.timestamp() == src.timestamp(), "같은 순간이어야 한다"


# ─────────────────────────────────────────────────────────────
# S3-01 / S3-04 — 통계
# ─────────────────────────────────────────────────────────────

def test_should_bucket_by_display_timezone_when_postgresql():
    """PostgreSQL 경로가 `timezone(<DISPLAY_TZ>, col)` 로 감싸 포맷하는지."""
    from app.config import settings
    from app.models.event import Event
    from app.routers.event_statistics import _time_bucket_expr

    class _Dialect:
        name = "postgresql"

    class _Bind:
        dialect = _Dialect()

    class _Db:
        def get_bind(self):
            return _Bind()

    expr = str(_time_bucket_expr(Event.created_at, "hour", _Db()))
    assert "to_char" in expr
    assert "timezone" in expr, f"DISPLAY_TZ 변환이 빠짐: {expr}"
    # 바인드 파라미터로 들어가므로 리터럴 비교 대신 컴파일 인자 확인
    compiled = _time_bucket_expr(Event.created_at, "hour", _Db()).compile(
        compile_kwargs={"literal_binds": True}
    )
    assert settings.DISPLAY_TIMEZONE in str(compiled), str(compiled)


@pytest.mark.parametrize("path", ["/api/events/statistics/trend", "/api/events/statistics/dashboard"])
def test_should_restrict_trend_interval_to_hour_or_day(path):
    """interval 이 임의 문자열을 받아 hour 로 조용히 폴백하면 실패.

    FieldInfo 내부 표현은 버전에 따라 달라지므로 **생성된 OpenAPI 스키마**로 계약을 고정한다.
    """
    from app.main import app
    from app.routers.event_statistics import TREND_INTERVALS

    assert TREND_INTERVALS == ("hour", "day")
    params = app.openapi()["paths"][path]["get"]["parameters"]
    interval = next(p for p in params if p["name"] == "interval")
    assert interval["schema"].get("pattern") == "^(hour|day)$", interval["schema"]


# ─────────────────────────────────────────────────────────────
# S3-02 — 이벤트 요청 스키마 enum 노출
# ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "schema_name, field, expected_member",
    [
        ("DetectionEventCreate", "result", "PIR_SENSOR"),
        ("DetectionEventReplace", "result", "AI_DETECT"),
        ("DetectionEventUpdate", "result", "CABLE_CUTTING"),
        ("MalfunctionEventCreate", "reason", "FAULT_CONTROLLER"),
        ("MalfunctionEventReplace", "reason", "FAULT_FENCE"),
        ("MalfunctionEventUpdate", "reason", "FAULT_ETC"),
    ],
)
def test_should_publish_machine_readable_enum_for_event_request_fields(
    schema_name, field, expected_member
):
    """생성 클라(.NET)가 자유 문자열로 받지 않도록 JSON Schema 에 enum 이 실려야 한다."""
    from app.schemas import event as event_schemas

    model = getattr(event_schemas, schema_name)
    prop = model.model_json_schema()["properties"][field]
    # Optional 필드는 anyOf 로 감싸일 수 있어 평탄화해서 찾는다
    candidates = [prop] + prop.get("anyOf", [])
    enums = [c["enum"] for c in candidates if "enum" in c]
    assert enums, f"{schema_name}.{field} 에 enum 이 없음: {prop}"
    assert expected_member in enums[0], f"{expected_member} 누락: {enums[0]}"


# ─────────────────────────────────────────────────────────────
# S3-06 — 억제 PATCH 명시적 null
# ─────────────────────────────────────────────────────────────

def test_should_guard_explicit_null_for_non_nullable_suppression_fields():
    """NOT NULL 컬럼 목록이 라우터 가드에 실제로 들어 있는지(소스 고정)."""
    from app.routers import event_suppression_schedules as mod

    src = inspect.getsource(mod.patch_suppression_schedule)
    assert "_non_nullable" in src, "명시적 null 가드가 없음"
    for f in ("name", "target_type", "target_side", "event_scope", "window_start", "window_end"):
        assert f'"{f}"' in src, f"NOT NULL 가드에 {f} 누락"


# ─────────────────────────────────────────────────────────────
# S5-01 — /api/logs 날짜 파라미터
# ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("param", ["start_date", "end_date"])
def test_should_type_log_date_params_as_datetime(param):
    """`str` 로 두면 핸들러 내부 파싱이 터져 500 이 된다."""
    from app.routers.logs import get_logs

    ann = inspect.signature(get_logs).parameters[param].annotation
    assert "datetime" in str(ann), f"{param} 이 datetime 이 아님: {ann}"


# ─────────────────────────────────────────────────────────────
# A-04 / X-01 / X-02 — 스키마·Example
# ─────────────────────────────────────────────────────────────

def test_should_provide_optional_lock_reason_schema():
    """lock 사유를 받을 수 있어야 하고, 바디는 **선택**이라 기존 호출과 호환돼야 한다."""
    from app.schemas.user import UserLockRequest

    assert UserLockRequest().reason is None, "바디 없이도 생성 가능(선택)"
    assert UserLockRequest(reason="점검").reason == "점검"
    schema = UserLockRequest.model_json_schema()
    assert not schema.get("required"), "필수 필드가 있으면 기존 호출이 깨진다"


def test_should_keep_session_settings_example_minimal_and_harmless():
    """세션설정 Example 은 즉시 운영 반영되므로 최소 1키로 고정한다."""
    from app.schemas.settings import SessionSettingsUpdate

    example = SessionSettingsUpdate.model_json_schema().get("example")
    assert example == {"session_timeout_hours": 24}, f"위험한 Example 복귀: {example}"
    # 특히 이 두 키는 운영 세션에 즉시 영향 → Example 에 있으면 안 된다
    assert "session_concurrency_policy" not in example
    assert "session_enabled" not in example


def test_should_keep_suppression_example_window_in_the_past():
    """억제 Example 창이 미래가 되면 Execute 만으로 실제 억제가 시작된다."""
    from app.schemas.event_suppression import EventSuppressionScheduleCreate

    props = EventSuppressionScheduleCreate.model_json_schema()["properties"]
    start = props["window_start"]["example"]
    end = props["window_end"]["example"]
    assert datetime.fromisoformat(end) > datetime.fromisoformat(start)
    # 하드코딩 과거 고정 — 연도가 올라가면 재검토 필요
    assert datetime.fromisoformat(start).year <= 2026


# ─────────────────────────────────────────────────────────────
# S4-01 / A-03 / S3-03 / S4-02 — 가드가 라우터에 실재하는지(소스 고정)
# ─────────────────────────────────────────────────────────────

def test_should_block_category_delete_when_servers_attached():
    from app.routers import server_categories as mod

    src = inspect.getsource(mod.delete_server_category)
    assert "HTTP_409_CONFLICT" in src, "CASCADE 동반삭제 가드 없음"
    assert "Server.category_id" in src


def test_should_block_self_delete():
    from app.routers import users as mod

    src = inspect.getsource(mod.delete_user)
    assert re.search(r"current_user\.id\s*==\s*user_id", src), "자기삭제 가드 없음"
    assert "HTTP_409_CONFLICT" in src


def test_should_reject_duplicated_lamp_mapping_with_conflict():
    from app.routers import event_mapping_lamps as mod

    src = inspect.getsource(mod.create_event_mapping_lamp)
    assert "HTTP_409_CONFLICT" in src, "중복 램프 매핑이 500 으로 터진다"


def test_should_validate_device_group_on_event_mapping_create():
    from app.routers import event_mappings as mod

    src = inspect.getsource(mod.create_event_mapping)
    assert "DeviceGroup" in src and "HTTP_404_NOT_FOUND" in src, "device_group_id 검증 없음"
