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

    # Thumbnail Storage
    THUMBNAIL_STORAGE_PATH: str = "data/thumbnails"

    # CORS
    CORS_ORIGINS: str = '["*"]'

    # Timezone
    TIMEZONE: str = "Asia/Seoul"

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
