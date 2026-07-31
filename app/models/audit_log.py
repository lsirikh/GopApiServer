"""
Audit Log model for tracking user activities
PRD: PRD_Audit_Log.md v1.0
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base
from app.models.types import UtcDateTime
from app.utils.datetime import utc_now
from app.config import settings


class AuditLog(Base):
    """
    감사 로그 모델

    사용자의 Account 관련 CRUD 작업을 추적하고 기록합니다.
    삭제된 리소스에 대한 참조도 스냅샷으로 보존됩니다.

    PRD: PRD_Audit_Log.md Section 2.3
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    # 행위 정보
    action_type = Column(String(50), nullable=False, index=True)
    action_status = Column(String(20), nullable=False, default="SUCCESS", index=True)

    # 대상 리소스 정보 (스냅샷 - 삭제 후에도 유지)
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(Integer, index=True)
    resource_name = Column(String(200))

    # 행위자 정보 (스냅샷 - 삭제 후에도 유지)
    actor_id = Column(Integer, ForeignKey("account_users.id", ondelete="SET NULL"), index=True)
    actor_login_id = Column(String(50), nullable=False, index=True)
    actor_name = Column(String(100))
    actor_role = Column(String(20))

    # 변경 상세
    changes = Column(JSON().with_variant(JSONB(), "postgresql"))  # {before: {...}, after: {...}}
    description = Column(String(500))

    # 클라이언트 정보
    ip_address = Column(String(45))  # IPv6 호환
    user_agent = Column(String(500))

    # 오류 정보
    error_message = Column(String(1000))

    # 타임스탬프
    created_at = Column(
        UtcDateTime,
        default=utc_now,
        nullable=False,
        index=True
    )

    # Relationships
    actor = relationship("AccountUser", foreign_keys=[actor_id])

    def __repr__(self):
        return f"<AuditLog {self.id}: {self.action_type} by {self.actor_login_id}>"


# Additional indexes for query performance
Index("idx_audit_logs_action_resource", AuditLog.action_type, AuditLog.resource_type)
Index("idx_audit_logs_created_at_desc", AuditLog.created_at.desc())
