"""
AppSettings model — 런타임 세션/인증 정책 key-value 저장소.
PRD: docs/prds/PRD_GOP_Server_Session_Settings.md (FR-SVS-01)

편집 가능한 안전 부분집합(세션만료·refresh만료·잠금임계·세션사용여부)만 저장한다.
AUTH_MODE / JWT_SECRET / JWT_ALGORITHM 등 배포전용 값은 여기에 저장하지 않는다.
시드 후 DB(app_settings)가 권위, .env/config 는 최초 1회 기본값 시드 소스(FR-SVS-06).
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer

from app.database import Base
from app.config import settings


class AppSettings(Base):
    """런타임 설정 key-value 행."""
    __tablename__ = "app_settings"

    setting_key = Column(String(100), primary_key=True)
    setting_value = Column(Text, nullable=False)            # 직렬화 문자열
    value_type = Column(String(10), nullable=False)         # 'int' | 'bool' | 'str'
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(settings.tz).replace(tzinfo=None),
        onupdate=lambda: datetime.now(settings.tz).replace(tzinfo=None),
        nullable=False,
    )
    updated_by = Column(Integer, ForeignKey("account_users.id", ondelete="SET NULL"), nullable=True)

    def __repr__(self):
        return f"<AppSettings {self.setting_key}={self.setting_value} ({self.value_type})>"
