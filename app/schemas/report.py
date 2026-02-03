"""
Report System Schemas
PRD: PRD_Report_System.md Section 5

- ReportComponentConfig: 컴포넌트 설정
- ReportTemplateCreate/Update/Response: 템플릿 스키마
- ReportGenerateRequest: 보고서 생성 요청
- ReportGenerationResponse: 보고서 생성 결과
"""
from pydantic import BaseModel, ConfigDict, Field, field_validator
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
    report_type: EnumReportType = Field(
        ...,
        description="보고서 유형",
        json_schema_extra={"example": "STANDARD"}
    )
    title: str = Field(
        ...,
        description="보고서 제목",
        json_schema_extra={"example": "주간 운영 보고서"}
    )
    period_type: EnumReportPeriod = Field(
        ...,
        description="조회 기간 유형",
        json_schema_extra={"example": "7d"}
    )
    template_id: Optional[int] = Field(
        default=None,
        description="사용자 정의 템플릿 ID (CUSTOM 유형일 경우 필수)",
        json_schema_extra={"example": 1}
    )
    severity_filter: Optional[List[str]] = Field(
        default=None,
        description="심각도 필터 목록 (예: CRITICAL, WARNING, INFO)",
        json_schema_extra={"example": ["CRITICAL", "WARNING"]}
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "report_type": "STANDARD",
                    "title": "주간 운영 보고서",
                    "period_type": "7d"
                },
                {
                    "report_type": "CUSTOM",
                    "title": "월간 보안 보고서",
                    "period_type": "30d",
                    "template_id": 1,
                    "severity_filter": ["CRITICAL", "WARNING"]
                }
            ]
        }
    )

    @field_validator('title')
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('title cannot be empty')
        return v


# ============================================================
# Report Data Schemas (미리보기/차트/그리드)
# PRD: PRD_Report_System.md Section 5
# ============================================================

class ChartDataset(BaseModel):
    """LINE 차트용 다중 데이터셋 (PRD_Report_Preview_Debug GAP-4)"""
    label: str
    values: List[Any]
    color: Optional[str] = None


class ChartData(BaseModel):
    """차트 데이터 (PRD_Report_Preview_Debug: datasets 지원 추가)"""
    labels: List[str]
    values: Optional[List[Any]] = None           # PIE/BAR 단일 데이터셋
    datasets: Optional[List[Any]] = None          # LINE 다중 데이터셋
    colors: Optional[List[str]] = None


class ChartConfig(BaseModel):
    """차트 설정"""
    id: str
    title: str
    type: str
    data: ChartData


class GridConfig(BaseModel):
    """그리드 설정"""
    id: str
    title: str
    columns: List[str]
    rows: List[List[Any]]
    total_rows: int


class ReportSection(BaseModel):
    """보고서 섹션 (PRD_Report_Preview_Debug: summary_data 추가)"""
    name: str
    title: str
    charts: List[ChartConfig] = []
    grids: List[GridConfig] = []
    summary_data: Optional[dict] = None  # 요약 섹션용 카테고리별 카드 데이터


class ReportPreviewResponse(BaseModel):
    """보고서 미리보기 응답"""
    id: int
    title: str
    period_type: str
    start_date: datetime
    end_date: datetime
    sections: List[ReportSection]
    generator_name: Optional[str] = None
    generator_department: Optional[str] = None


# ============================================================
# Component Schemas
# ============================================================

class ComponentInfo(BaseModel):
    """컴포넌트 정보"""
    id: str
    label: str
    description: str
    chart_type: Optional[str] = None
    category: str


class ComponentCategoryResponse(BaseModel):
    """컴포넌트 카테고리"""
    name: str
    label: str
    components: List[ComponentInfo]


# ============================================================
# List Response Schemas
# ============================================================

class ReportTemplateListResponse(BaseModel):
    """템플릿 목록 응답 (경량)"""
    id: int
    name: str
    description: Optional[str] = None
    report_type: str
    owner_id: Optional[int] = None
    is_public: bool
    component_count: int
    default_period: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReportGenerationListResponse(BaseModel):
    """보고서 생성 목록 응답 (경량)"""
    id: int
    report_type: str
    title: str
    period_type: str
    status: str
    created_at: datetime
    generator_name: Optional[str] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# ReportGeneration Schemas
# ============================================================

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
