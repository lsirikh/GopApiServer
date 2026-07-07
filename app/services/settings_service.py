"""
런타임 세션/인증 정책 service — Session_Settings FR-SVS-02/05/06.

- 메모리 캐시(단일 인스턴스 가정) + 최초조회/startup 시 .env/config 기본값 시드.
- get(key): 캐시 우선 → DB → (부재 시) 기본값 fallback.
- put(key, value): app_settings UPSERT + 캐시 무효화.
- 편집 가능한 키만 정의(AUTH_MODE/JWT_SECRET 등 배포전용은 제외).
시드 후 DB(app_settings)가 권위, .env 는 최초 1회 기본값(FR-SVS-06).

v6.0 P6 후속: sync/async dual-stack. 라우터가 async 세션 사용 시 *_async 호출.
"""
from typing import Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.config import settings as app_config
from app.models.app_settings import AppSettings


class SettingKey:
    """편집 가능한 런타임 설정 키(오타 방지 상수)."""
    SESSION_TIMEOUT_HOURS = "session_timeout_hours"
    REFRESH_EXPIRATION_DAYS = "refresh_expiration_days"
    LOCKOUT_THRESHOLD = "lockout_threshold"
    SESSION_ENABLED = "session_enabled"


# 기본값 표 — (default, value_type). default 는 .env/config 또는 현 하드코딩값에서 시드.
def _defaults() -> dict:
    return {
        SettingKey.SESSION_TIMEOUT_HOURS: (app_config.JWT_EXPIRATION_HOURS, "int"),
        SettingKey.REFRESH_EXPIRATION_DAYS: (app_config.JWT_REFRESH_EXPIRATION_DAYS, "int"),
        SettingKey.LOCKOUT_THRESHOLD: (5, "int"),   # auth.py 기존 하드코딩 >= 5
        SettingKey.SESSION_ENABLED: (True, "bool"),
    }


# 모듈 레벨 메모리 캐시 (단일 인스턴스 가정 — 멀티 배포 시 분산 캐시 필요)
_cache: dict = {}


def _serialize(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _deserialize(value: str, value_type: str) -> Any:
    if value_type == "int":
        return int(value)
    if value_type == "bool":
        return str(value).strip().lower() in ("true", "1", "yes")
    return value


def invalidate_cache() -> None:
    _cache.clear()


def seed_if_empty(db: Session) -> None:
    """편집 가능한 키 중 app_settings 에 없는 것을 기본값으로 시드(최초 1회, idempotent)."""
    inserted = False
    for key, (default, vtype) in _defaults().items():
        exists = db.query(AppSettings.setting_key).filter(AppSettings.setting_key == key).first()
        if not exists:
            db.add(AppSettings(setting_key=key, setting_value=_serialize(default), value_type=vtype))
            inserted = True
    if inserted:
        db.commit()
        invalidate_cache()


def get(db: Session, key: str) -> Any:
    """설정값 조회 — 캐시 우선, DB 폴백, 부재 시 기본값(시드 누락 안전망)."""
    if key in _cache:
        return _cache[key]
    row = db.query(AppSettings).filter(AppSettings.setting_key == key).first()
    if row is None:
        default, _ = _defaults().get(key, (None, "str"))
        value = default
    else:
        value = _deserialize(row.setting_value, row.value_type)
    _cache[key] = value
    return value


# v6.0-session_enabled (2026-07-07): 세션 만료 마스터 스위치.
# session_enabled=False 면 세션이 사실상 무기한 유지되도록 매우 긴 만료를 반환한다.
# (JWT 는 exp 가 필수라 진짜 무한대는 불가 → 10년으로 근사. session.expires_at·sweep 도 동일 정합.)
SESSION_DISABLED_TIMEOUT_HOURS = 24 * 365 * 10   # 10년
SESSION_DISABLED_REFRESH_DAYS = 365 * 10         # 10년


def resolve_session_expiry(db: Session) -> tuple[int, int]:
    """(access_timeout_hours, refresh_days) 를 session_enabled 반영해 반환.

    - session_enabled=True  → (session_timeout_hours, refresh_expiration_days) 설정값
    - session_enabled=False → 10년(사실상 무기한). 세션 기간성 자체를 끈다.
    로그인/리프레시가 이 값을 access·refresh exp + session.expires_at 에 일관 적용.
    """
    if not get(db, SettingKey.SESSION_ENABLED):
        return SESSION_DISABLED_TIMEOUT_HOURS, SESSION_DISABLED_REFRESH_DAYS
    return get(db, SettingKey.SESSION_TIMEOUT_HOURS), get(db, SettingKey.REFRESH_EXPIRATION_DAYS)


def put(db: Session, key: str, value: Any, actor_id: Optional[int] = None) -> Any:
    """편집 가능한 키의 값을 UPSERT + 캐시 무효화. value_type 은 기본값 정의에서 결정."""
    _, vtype = _defaults().get(key, (None, "str"))
    if vtype is None:
        raise ValueError(f"Unknown / non-editable setting key: {key}")
    row = db.query(AppSettings).filter(AppSettings.setting_key == key).first()
    if row is None:
        row = AppSettings(setting_key=key, setting_value=_serialize(value), value_type=vtype, updated_by=actor_id)
        db.add(row)
    else:
        row.setting_value = _serialize(value)
        row.value_type = vtype
        row.updated_by = actor_id
    db.commit()
    _cache.pop(key, None)
    return value


# ─── async dual-stack (v6.0 P6 후속) ────────────────────────────
async def seed_if_empty_async(db: AsyncSession) -> None:
    """seed_if_empty의 async 병존 버전."""
    inserted = False
    for key, (default, vtype) in _defaults().items():
        stmt = select(AppSettings.setting_key).where(AppSettings.setting_key == key)
        exists = (await db.execute(stmt)).scalar_one_or_none()
        if not exists:
            db.add(AppSettings(setting_key=key, setting_value=_serialize(default), value_type=vtype))
            inserted = True
    if inserted:
        await db.commit()
        invalidate_cache()


async def get_async(db: AsyncSession, key: str) -> Any:
    """get()의 async 병존 버전. 캐시 우선, DB 폴백, 부재 시 기본값."""
    if key in _cache:
        return _cache[key]
    stmt = select(AppSettings).where(AppSettings.setting_key == key)
    row = (await db.execute(stmt)).scalars().first()
    if row is None:
        default, _ = _defaults().get(key, (None, "str"))
        value = default
    else:
        value = _deserialize(row.setting_value, row.value_type)
    _cache[key] = value
    return value


async def put_async(db: AsyncSession, key: str, value: Any, actor_id: Optional[int] = None) -> Any:
    """put()의 async 병존 버전. UPSERT + 캐시 무효화."""
    _, vtype = _defaults().get(key, (None, "str"))
    if vtype is None:
        raise ValueError(f"Unknown / non-editable setting key: {key}")
    stmt = select(AppSettings).where(AppSettings.setting_key == key)
    row = (await db.execute(stmt)).scalars().first()
    if row is None:
        row = AppSettings(setting_key=key, setting_value=_serialize(value), value_type=vtype, updated_by=actor_id)
        db.add(row)
    else:
        row.setting_value = _serialize(value)
        row.value_type = vtype
        row.updated_by = actor_id
    await db.commit()
    _cache.pop(key, None)
    return value
