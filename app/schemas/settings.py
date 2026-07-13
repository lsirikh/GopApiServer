"""
세션 설정 API 스키마 — Session_Settings FR-SVS-03/04, NFR-SVS-04.

편집 가능: session_timeout_hours(1~168), refresh_expiration_days(1~90),
           lockout_threshold(0 또는 3~20), lockout_duration_minutes(0=영구 또는 1~1440),
           session_enabled(bool).
읽기전용(응답에만 노출, 배포전용): auth_mode, jwt_algorithm. jwt_secret 은 절대 미노출.
"""
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class SessionSettingsResponse(BaseModel):
    """GET/PUT 응답 — 편집 가능 + 읽기전용 필드. 시크릿 미포함."""
    session_timeout_hours: int
    refresh_expiration_days: int
    lockout_threshold: int
    lockout_duration_minutes: int
    session_enabled: bool
    # 읽기전용(배포/.env 전용 — 런타임 편집 불가)
    auth_mode: str
    jwt_algorithm: str


class SessionSettingsUpdate(BaseModel):
    """PUT 요청 — 편집 가능 부분집합만. 경계 위반 시 422."""
    session_timeout_hours: Optional[int] = Field(None, ge=1, le=168)
    refresh_expiration_days: Optional[int] = Field(None, ge=1, le=90)
    lockout_threshold: Optional[int] = Field(None, ge=0, le=20)
    lockout_duration_minutes: Optional[int] = Field(None, ge=0, le=1440)
    session_enabled: Optional[bool] = None

    @field_validator("lockout_threshold")
    @classmethod
    def validate_lockout_threshold(cls, v: Optional[int]) -> Optional[int]:
        """0(비활성) 또는 3~20만 허용. 1~2는 무의미 구간 → 422."""
        if v is None or v == 0 or 3 <= v <= 20:
            return v
        raise ValueError("lockout_threshold must be 0 (disabled) or between 3 and 20")
