"""
Report System Schemas
PRD: PRD_Report_System.md Section 5

- ReportComponentConfig: 컴포넌트 설정
- ReportTemplateCreate/Update/Response: 템플릿 스키마
- ReportGenerateRequest: 보고서 생성 요청
- ReportGenerationResponse: 보고서 생성 결과
"""
from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime
from typing import Optional, List, Any

from app.utils.enums import EnumReportType, EnumReportPeriod


# ============================================================
# Component Config Schema
# ============================================================

class ReportComponentConfig(BaseModel):
    """
    보고서 컴포넌트 설정
    PRD: PRD_Report_System.md Section 5.1
    """
    id: str  # EnumReportComponent value
    order: int
    enabled: bool
    title: Optional[str] = None


# ============================================================
# ReportTemplate Schemas
# ============================================================

class ReportTemplateCreate(BaseModel):
    """
    보고서 템플릿 생성 스키마
    PRD: PRD_Report_System.md Section 5.2
    """
    name: str
    components: List[ReportComponentConfig]
    description: Optional[str] = None
    report_type: EnumReportType = EnumReportType.CUSTOM
    is_public: bool = False
    default_period: EnumReportPeriod = EnumReportPeriod.DAYS_7

    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('name cannot be empty')
        return v


class ReportTemplateUpdate(BaseModel):
    """
    보고서 템플릿 수정 스키마 (모든 필드 optional)
    PRD: PRD_Report_System.md Section 5.3
    """
    name: Optional[str] = None
    components: Optional[List[ReportComponentConfig]] = None
    description: Optional[str] = None
    report_type: Optional[EnumReportType] = None
    is_public: Optional[bool] = None
    default_period: Optional[EnumReportPeriod] = None


class ReportTemplateResponse(BaseModel):
    """
    보고서 템플릿 응답 스키마
    PRD: PRD_Report_System.md Section 5.4
    """
    id: int
    name: str
    report_type: str
    owner_id: Optional[int] = None
    is_public: bool
    components: List[Any]  # JSON stored as list of dicts
    default_period: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# ReportGeneration Schemas
# ============================================================

class ReportGenerateRequest(BaseModel):
    """
    보고서 생성 요청 스키마
    PRD: PRD_Report_System.md Section 5.5
    """
    report_type: EnumReportType
    title: str
    period_type: EnumReportPeriod
    template_id: Optional[int] = None
    severity_filter: Optional[List[str]] = None

    @field_validator('title')
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('title cannot be empty')
        return v


class ReportGenerationResponse(BaseModel):
    """
    보고서 생성 결과 응답 스키마
    PRD: PRD_Report_System.md Section 5.6
    """
    id: int
    report_type: str
    title: str
    period_type: str
    start_date: datetime
    end_date: datetime
    status: str
    created_at: datetime

    # Nullable fields
    template_id: Optional[int] = None
    generator_id: Optional[int] = None
    generator_name: Optional[str] = None
    generator_department: Optional[str] = None
    severity_filter: Optional[List[str]] = None
    summary_data: Optional[Any] = None
    pdf_file_path: Optional[str] = None
    pdf_file_size: Optional[int] = None
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
