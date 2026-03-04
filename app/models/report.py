"""
Report System Models
PRD: PRD_Report_System.md Section 4

- ReportTemplate: 비정형 보고서 템플릿
- ReportGeneration: 보고서 생성 이력
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base
from app.config import settings


class ReportTemplate(Base):
    """
    비정형 보고서 템플릿
    PRD: PRD_Report_System.md Section 4.1
    """
    __tablename__ = "report_templates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    report_type = Column(String(20), nullable=False, default="CUSTOM")

    owner_id = Column(Integer, ForeignKey("account_users.id", ondelete="SET NULL"), nullable=True)
    is_public = Column(Boolean, nullable=False, default=False)

    components = Column(JSON, nullable=False)
    default_period = Column(String(20), default="7d")

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(settings.tz).replace(tzinfo=None), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(settings.tz).replace(tzinfo=None), onupdate=lambda: datetime.now(settings.tz).replace(tzinfo=None), nullable=False)

    # Relationships
    owner = relationship("AccountUser", back_populates="report_templates")
    generations = relationship("ReportGeneration", back_populates="template")


class ReportGeneration(Base):
    """
    보고서 생성 이력
    PRD: PRD_Report_System.md Section 4.2

    Note: updated_at 없음 - 생성 후 변경 불가 (completed_at만 존재)
    """
    __tablename__ = "report_generations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # 보고서 정보
    report_type = Column(String(20), nullable=False)
    template_id = Column(Integer, ForeignKey("report_templates.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(200), nullable=False)

    # 기간 설정
    period_type = Column(String(20), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)

    # 생성자 정보 (스냅샷)
    generator_id = Column(Integer, ForeignKey("account_users.id", ondelete="SET NULL"), nullable=True)
    generator_name = Column(String(100), nullable=True)
    generator_department = Column(String(100), nullable=True)

    # 필터 설정
    severity_filter = Column(JSON, nullable=True)

    # 결과 데이터
    summary_data = Column(JSON, nullable=True)

    # 파일 정보
    pdf_file_path = Column(String(500), nullable=True)
    pdf_file_size = Column(Integer, nullable=True)

    # 상태
    status = Column(String(20), nullable=False, default="PENDING")
    error_message = Column(String(1000), nullable=True)

    # 타임스탬프 (created_at만 - 변경 불가)
    created_at = Column(DateTime, default=lambda: datetime.now(settings.tz).replace(tzinfo=None), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    template = relationship("ReportTemplate", back_populates="generations")
    generator = relationship("AccountUser", back_populates="report_generations")
