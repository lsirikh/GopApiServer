"""
세션/인증 정책 런타임 관리 API — Session_Settings FR-SVS-03/04.

GET/PUT /api/settings/session (require_admin):
- 편집 가능: session_timeout_hours / refresh_expiration_days / lockout_threshold / session_enabled
- 읽기전용 노출: auth_mode / jwt_algorithm (배포전용). jwt_secret 은 절대 미노출(NFR-SVS-03).
- PUT 은 편집 부분집합만 수용, 경계 위반 422, app_settings UPSERT + ConfigChangeLog 감사 + 캐시 무효화.
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.routers.auth import require_admin, get_current_account_user
from app.models.user import AccountUser
from app.services import settings_service
from app.services.settings_service import SettingKey
from app.services.config_log_service import log_config_change
from app.schemas.settings import SessionSettingsResponse, SessionSettingsUpdate
from app.utils.enums import EnumConfigResourceType, EnumConfigActionType
from app.config import settings as app_config

router = APIRouter(tags=["Settings"])


def _current(db: Session) -> dict:
    """현재 세션 설정 스냅샷(편집 가능 + 읽기전용). 시크릿 미포함."""
    return {
        "session_timeout_hours": settings_service.get(db, SettingKey.SESSION_TIMEOUT_HOURS),
        "refresh_expiration_days": settings_service.get(db, SettingKey.REFRESH_EXPIRATION_DAYS),
        "lockout_threshold": settings_service.get(db, SettingKey.LOCKOUT_THRESHOLD),
        "session_enabled": settings_service.get(db, SettingKey.SESSION_ENABLED),
        "auth_mode": app_config.AUTH_MODE,        # 읽기전용
        "jwt_algorithm": app_config.JWT_ALGORITHM,  # 읽기전용
    }


@router.get("/session", response_model=None, dependencies=[Depends(require_admin)])
async def get_session_settings(
    db: Session = Depends(get_db),
    current_user: AccountUser = Depends(get_current_account_user),
):
    """현재 세션/인증 정책 조회 (ADMIN 전용)."""
    settings_service.seed_if_empty(db)
    return {"success": True, "data": SessionSettingsResponse(**_current(db)).model_dump()}


@router.put("/session", response_model=None, dependencies=[Depends(require_admin)])
async def update_session_settings(
    payload: SessionSettingsUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: AccountUser = Depends(get_current_account_user),
):
    """세션/인증 정책 변경 (ADMIN 전용) — 편집 부분집합만, 변경분 ConfigChangeLog 감사."""
    settings_service.seed_if_empty(db)
    before = _current(db)

    editable = {
        SettingKey.SESSION_TIMEOUT_HOURS: payload.session_timeout_hours,
        SettingKey.REFRESH_EXPIRATION_DAYS: payload.refresh_expiration_days,
        SettingKey.LOCKOUT_THRESHOLD: payload.lockout_threshold,
        SettingKey.SESSION_ENABLED: payload.session_enabled,
    }
    changed_keys = [k for k, v in editable.items() if v is not None]
    for key in changed_keys:
        settings_service.put(db, key, editable[key], actor_id=current_user.id)

    after = _current(db)

    if changed_keys:
        log_config_change(
            db=db,
            resource_type=EnumConfigResourceType.SETTINGS,
            resource_id=0,  # sentinel — 비-행 바운드 설정
            action=EnumConfigActionType.UPDATED,
            resource_name="session settings",
            before_state={k: before[k] for k in changed_keys},
            after_state={k: after[k] for k in changed_keys},
            actor_id=current_user.id,
            actor_name=current_user.name,
            actor_ip=request.client.host if request.client else None,
            description=f"세션 정책 변경: {', '.join(changed_keys)}",
        )

    return {"success": True, "data": SessionSettingsResponse(**after).model_dump()}
