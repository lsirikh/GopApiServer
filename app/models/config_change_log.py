"""
ConfigChangeLog model for tracking configuration changes
PRD: PRD_ConfigChangeLog.md v1.0
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, Enum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base
from app.config import settings
from app.utils.enums import EnumConfigResourceType, EnumConfigActionType


class ConfigChangeLog(Base):
    """
    설정 변경 로그 모델

    Device, Server, Event, Integration 계열 리소스의 CRUD 작업에 대한
    변경 이력을 추적하고 기록합니다.

    PRD: PRD_ConfigChangeLog.md Section 3
    """
    __tablename__ = "config_change_logs"

    id = Column(Integer, primary_key=True, index=True)

    # 변경 대상 리소스
    resource_type = Column(
        Enum(EnumConfigResourceType),
        nullable=False,
        index=True
    )
    resource_id = Column(Integer, nullable=False, index=True)
    resource_name = Column(String(200))  # 식별용 (예: "Camera-201 (정문 CCTV)")

    # 변경 액션
    action = Column(
        Enum(EnumConfigActionType),
        nullable=False,
        index=True
    )

    # 변경 전/후 상태 (JSON)
    before_state = Column(JSON)  # 변경 전 상태
    after_state = Column(JSON)   # 변경 후 상태

    # 수행자 정보
    actor_id = Column(
        Integer,
        ForeignKey("account_users.id", ondelete="SET NULL"),
        index=True
    )
    actor_name = Column(String(100))
    actor_ip = Column(String(45))  # IPv6 호환

    # 설명
    description = Column(Text)

    # 타임스탬프
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(settings.tz),
        nullable=False,
        index=True
    )

    # Relationships
    actor = relationship("AccountUser", foreign_keys=[actor_id])

    def __repr__(self):
        return f"<ConfigChangeLog {self.id}: {self.action.value} {self.resource_type.value}-{self.resource_id}>"


# Additional indexes for query performance
Index("idx_config_change_logs_resource", ConfigChangeLog.resource_type, ConfigChangeLog.resource_id)
Index("idx_config_change_logs_created_at_desc", ConfigChangeLog.created_at.desc())
