"""
세션 설정 API 스키마 — Session_Settings FR-SVS-03/04, NFR-SVS-04.

편집 가능: session_timeout_hours(1~168), refresh_expiration_days(1~90),
           lockout_threshold(0 또는 3~20), lockout_duration_minutes(0=영구 또는 1~1440),
           session_enabled(bool).
읽기전용(응답에만 노출, 배포전용): auth_mode, jwt_algorithm. jwt_secret 은 절대 미노출.
"""
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class SessionSettingsResponse(BaseModel):
    """GET/PUT 응답 — 편집 가능 + 읽기전용 필드. 시크릿 미포함."""
    session_timeout_hours: int
    refresh_expiration_days: int
    lockout_threshold: int
    lockout_duration_minutes: int
    session_enabled: bool
    # v6.3-session_concurrency
    session_concurrency_policy: str
    max_concurrent_sessions: int
    session_history_retention_days: int
    login_anomaly_event_enabled: bool
    session_self_replace_enabled: bool
    # 읽기전용(배포/.env 전용 — 런타임 편집 불가)
    auth_mode: str
    jwt_algorithm: str


class SessionSettingsUpdate(BaseModel):
    """PUT 요청 — 편집 가능 부분집합만. 경계 위반 시 422.

    ★ **Swagger Example 안전화 (2026-08-07)**: 예시를 지정하지 않으면 Swagger UI 가 스키마 제약의
      경계값으로 전 필드 예시를 자동 생성한다. 본 엔드포인트는 **즉시 운영 반영**이라, 문서를 열람한
      사람이 Example 을 그대로 `Execute` 하기만 해도 `session_enabled=true`·`concurrency=evict_all`
      (로그인 시 타 세션 강제축출)·`lockout_duration=1440분` 이 실제로 적용됐다(실측).
      → **전 필드가 Optional 인 부분 업데이트**임을 살려, 현행 기본값 1개만 담은 최소 예시로 고정한다.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"session_timeout_hours": 24},
            "description": (
                "전 필드 선택(부분 업데이트). 보낸 키만 변경되며 **즉시 운영 반영**된다. "
                "동시세션 정책(session_concurrency_policy)·session_enabled 변경은 "
                "운영 중 세션에 즉시 영향을 주므로 값을 반드시 확인하고 호출할 것."
            ),
        }
    )

    session_timeout_hours: Optional[int] = Field(None, ge=1, le=168)
    refresh_expiration_days: Optional[int] = Field(None, ge=1, le=90)
    lockout_threshold: Optional[int] = Field(None, ge=0, le=20)
    lockout_duration_minutes: Optional[int] = Field(None, ge=0, le=1440)
    session_enabled: Optional[bool] = None
    # v6.3-session_concurrency
    session_concurrency_policy: Optional[str] = Field(None, pattern="^(evict_all|allow)$")
    max_concurrent_sessions: Optional[int] = Field(None, ge=0, le=100)
    session_history_retention_days: Optional[int] = Field(None, ge=0, le=3650)
    login_anomaly_event_enabled: Optional[bool] = None
    session_self_replace_enabled: Optional[bool] = None

    @field_validator("lockout_threshold")
    @classmethod
    def validate_lockout_threshold(cls, v: Optional[int]) -> Optional[int]:
        """0(비활성) 또는 3~20만 허용. 1~2는 무의미 구간 → 422."""
        if v is None or v == 0 or 3 <= v <= 20:
            return v
        raise ValueError("lockout_threshold must be 0 (disabled) or between 3 and 20")
