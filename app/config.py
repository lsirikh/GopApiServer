"""
Application configuration using Pydantic Settings
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List
import json
import os
import warnings
from zoneinfo import ZoneInfo


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    # Environment (v4.6 FR-9): dev/staging/prod 분기 결정
    ENVIRONMENT: str = "dev"  # "dev" / "staging" / "prod"

    # Authentication (v4.6 FR-9)
    AUTH_MODE: str = "token"  # "token" or "public" — dev=public 허용, staging/prod=token 강제
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    # PRD v4.9 Phase 2-A3: refresh_token TTL settings 분리 (이전 하드코딩 7일)
    JWT_REFRESH_EXPIRATION_DAYS: int = 7

    # Force_Logout FR-SVF-07: revoke 서명 전용 키 (JWT_SECRET_KEY 와 반드시 분리 — 재사용 시 토큰 위조 위험)
    REVOKE_SIGNING_KEY: str = "dev-revoke-signing-key-change-in-production"
    # 클라 replay 방어용 issued_at 허용 오차(초)
    REVOKE_FRESHNESS_WINDOW_SECONDS: int = 30

    # Force_Logout FR-SVF-05/08: NATS revoke 발행 (워커 db_monitor/gis_ingest 와 동일 기본값)
    NATS_URL: str = "nats://nats-server-01:4222"
    NATS_UNIT_ID: str = "unit001"
    # ★ 활성화 게이트(기본 False): subject 클라 EffectiveSubject 매칭 확인(V-SVF-05) +
    #    발행 ACL(FR-SVF-08) 적용 후에만 True 로. False면 force_logout 은 블랙리스트만 수행.
    NATS_REVOKE_ENABLED: bool = False

    # Grant sweep 주기(분) — FR-08(grant-enforcement-hardening). 만료 grant 의 is_active 정리(표시/통지 백스톱용).
    # ★ 보안 비의존: 요청시점 계산(_active_grants)이 인가 권위. 본 값은 표시 최신성·자연만료 통지 지연 상한만 좌우.
    GRANT_SWEEP_INTERVAL_MINUTES: int = 10
    # FR-07 per-grant 실시간 만료 통지: valid_until 발화 job 등록 지평(시간, 0=무제한). 스케일 상한(RISK-03).
    GRANT_JOB_HORIZON_HOURS: int = 0
    # FR-09 default-deny 모드: off(현행 default-allow) / observe(미분류 로그만·통과) / enforce(미등록 비allowlist 403).
    # ★ enforce 활성은 observe 로 미분류 0 확인 + 배포 게이트 후에만. 기본 off = 현행 동작 100% 보존.
    MATRIX_DENY_MODE: str = "off"

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def reject_default_jwt_secret(cls, v: str) -> str:
        """v4.6 FR-1: JWT_SECRET_KEY 디폴트 리터럴 거부 — staging/prod 환경에서 임의 토큰 위조 방지"""
        env = os.environ.get("ENVIRONMENT", "dev")
        forbidden = ("your-secret-key", "change-in-production", "change-me")
        is_default = any(token in v.lower() for token in forbidden)
        if is_default:
            if env in ("staging", "prod"):
                raise ValueError(
                    f"JWT_SECRET_KEY는 {env} 환경에서 디폴트값 사용 금지. "
                    "운영용 랜덤값으로 교체 필수 (예: python -c 'import os; print(os.urandom(32).hex())')"
                )
            else:
                # dev 환경은 경고만
                warnings.warn(
                    "JWT_SECRET_KEY가 디폴트값 — dev 환경은 허용하나 staging/prod 배포 전 반드시 교체",
                    UserWarning,
                    stacklevel=2,
                )
        if len(v) < 16:
            raise ValueError("JWT_SECRET_KEY는 최소 16자 이상")
        return v

    @field_validator("REVOKE_SIGNING_KEY")
    @classmethod
    def validate_revoke_signing_key(cls, v: str, info) -> str:
        """Force_Logout FR-SVF-07: revoke 서명 전용 키 가드.
        - JWT_SECRET_KEY 재사용 금지(공유 시 클라가 access 토큰 위조 가능 → 권한상승).
        - staging/prod 디폴트 리터럴 금지, 최소 16자."""
        env = os.environ.get("ENVIRONMENT", "dev")
        jwt_secret = info.data.get("JWT_SECRET_KEY") if info and info.data else None
        if jwt_secret is not None and v == jwt_secret:
            raise ValueError(
                "REVOKE_SIGNING_KEY는 JWT_SECRET_KEY와 달라야 함 — 키 재사용 시 클라가 access 토큰 위조 가능"
            )
        if any(tok in v.lower() for tok in ("change-in-production", "change-me")):
            if env in ("staging", "prod"):
                raise ValueError(f"REVOKE_SIGNING_KEY는 {env} 환경에서 디폴트값 사용 금지")
        if len(v) < 16:
            raise ValueError("REVOKE_SIGNING_KEY는 최소 16자 이상")
        return v

    @field_validator("AUTH_MODE")
    @classmethod
    def validate_auth_mode_per_env(cls, v: str) -> str:
        """v4.6 FR-9: staging/prod에서 AUTH_MODE=public 거부"""
        env = os.environ.get("ENVIRONMENT", "dev")
        if env in ("staging", "prod") and v != "token":
            raise ValueError(
                f"AUTH_MODE={v}는 {env} 환경에서 허용 안 됨 — token으로 설정 필수"
            )
        return v

    # Database
    DATABASE_URL: str = "sqlite:///./data/gop.db"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # Logging
    LOG_LEVEL: str = "INFO"

    # Initialization
    INIT_SAMPLE_DATA: bool = False

    # Report Generation (v6.0-report_lifecycle_persistence, 2026-07-05)
    # v6.0-report_progress_perf: wall-clock timeout 제거, stall timeout으로 대체.
    # progress_updated_at이 STALL_TIMEOUT_SEC 이상 정체되면 hang으로 판정하고 FAILED.
    # 정상 진행 중인 큰 리포트는 시간 무제한 완료 가능.
    REPORT_GEN_STALL_TIMEOUT_SEC: int = 60  # 진행률 정체 감지 임계 (초)
    REPORT_GEN_STALL_CHECK_INTERVAL_SEC: int = 10  # 워치도그 체크 주기 (초)
    # (DEPRECATED) REPORT_GEN_TIMEOUT_SEC — v6.0-report_progress_perf에서 제거
    # PRD_GOP_Server_Reports_PDF_Persistence FR-RPP-05
    REPORTS_DIR: str = "/app/reports"  # PDF 저장 디렉터리 (docker-compose named volume 마운트)
    # v6.0-report_date_range (FR-RCD-03): 커스텀 날짜 범위 상한 (기본 366일 = 1년+윤년 여유)
    REPORT_MAX_RANGE_DAYS: int = 366

    # Thumbnail Storage
    THUMBNAIL_STORAGE_PATH: str = "data/thumbnails"

    # Profile Photo Storage — 호스트 ./data 바인드 마운트라 컨테이너 재생성/재빌드에도 영속
    PROFILE_STORAGE_PATH: str = "data/profiles"

    # CORS
    CORS_ORIGINS: str = '["*"]'

    # Timezone
    TIMEZONE: str = "Asia/Seoul"

    @field_validator("CORS_ORIGINS")
    @classmethod
    def validate_cors_per_env(cls, v: str) -> str:
        """OPS-03: staging/prod 에서 CORS 와일드카드('*') 거부.
        allow_credentials=True 와 '*' 조합은 브라우저 스펙상 위험 + 임의 오리진 신뢰.
        dev 는 편의상 허용(경고 없음). 파싱 실패 시 다른 validator 흐름 방해 않도록 그대로 통과."""
        env = os.environ.get("ENVIRONMENT", "dev")
        if env in ("staging", "prod"):
            try:
                origins = json.loads(v)
            except (ValueError, TypeError):
                return v
            if "*" in origins:
                raise ValueError(
                    f"CORS_ORIGINS 에 '*' 는 {env} 환경에서 허용 안 됨 — "
                    "명시적 허용 도메인 목록으로 설정 필수 (allow_credentials=True 와 와일드카드 조합 위험)"
                )
        return v

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS string to list"""
        return json.loads(self.CORS_ORIGINS)

    @property
    def tz(self) -> ZoneInfo:
        """Get timezone object"""
        return ZoneInfo(self.TIMEZONE)


# Create settings instance
settings = Settings()

# Set timezone environment variable for system
os.environ['TZ'] = settings.TIMEZONE
