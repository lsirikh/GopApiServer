"""
Report System Schemas
PRD: PRD_Report_System.md Section 5

- ReportComponentConfig: 컴포넌트 설정
- ReportTemplateCreate/Update/Response: 템플릿 스키마
- ReportGenerateRequest: 보고서 생성 요청
- ReportGenerationResponse: 보고서 생성 결과
"""
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from datetime import datetime, timedelta
from app.schemas.common import KSTDatetime
from typing import Optional, List, Any

from app.utils.enums import EnumReportType, EnumReportPeriod, EnumReportStatus
from app.config import settings
from app.utils.datetime import to_utc  # datetime-unification: 입력 aware UTC 정규화


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

    v6.0-response_schema_audit (2026-07-07): report_type/default_period 를 Enum → str.
    DB 컬럼이 String 이라 옛/임의 값 저장 가능 → strict Enum 응답이면 목록 500 (Postel's Law).
    """
    id: int
    name: str
    report_type: str
    owner_id: Optional[int] = None
    is_public: bool
    components: List[Any]  # JSON stored as list of dicts
    default_period: str
    description: Optional[str] = None
    created_at: KSTDatetime
    updated_at: KSTDatetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# ReportGeneration Schemas
# ============================================================

class ReportGenerateRequest(BaseModel):
    """
    보고서 생성 요청 스키마
    PRD: PRD_Report_System.md Section 5.5

    v6.0-report_date_range (2026-07-05, FR-RCD-01~03):
    - start_date/end_date 커스텀 범위 지원 (Optional, KSTDatetime).
    - 둘 다 주어지면 period_type은 무시하고 "custom"으로 저장.
    - period_type은 Optional 완화 (start/end 없을 때만 필수).
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
    period_type: Optional[EnumReportPeriod] = Field(
        default=None,
        description="조회 기간 유형 (7d/30d/90d/1y/custom). start_date+end_date를 함께 주면 무시되고 'custom' 저장.",
        json_schema_extra={"example": "7d"}
    )
    start_date: Optional[KSTDatetime] = Field(
        default=None,
        description="커스텀 시작일 (KST). end_date와 함께 사용. 날짜만(00:00) 오면 그대로 사용.",
        json_schema_extra={"example": "2026-06-01T00:00:00+09:00"}
    )
    end_date: Optional[KSTDatetime] = Field(
        default=None,
        description="커스텀 종료일 (KST). 00:00 시각이면 그날 23:59:59.999로 정규화 (끝일 포함).",
        json_schema_extra={"example": "2026-06-15T23:59:59+09:00"}
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
                    "title": "주간 운영 보고서 (프리셋)",
                    "period_type": "7d"
                },
                {
                    "report_type": "STANDARD",
                    "title": "커스텀 범위 보고서 (2주)",
                    "start_date": "2026-06-01T00:00:00+09:00",
                    "end_date": "2026-06-15T23:59:59+09:00"
                },
                {
                    "report_type": "CUSTOM",
                    "title": "월간 보안 보고서 (템플릿)",
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

    @model_validator(mode='after')
    def validate_date_range(self) -> "ReportGenerateRequest":
        """v6.0-report_date_range FR-RCD-03: 날짜 범위 상호 검증.

        - start_date/end_date는 둘 다 있거나 둘 다 없어야 함
        - end_date >= start_date
        - (end - start).days <= REPORT_MAX_RANGE_DAYS
        - 둘 다 없으면 period_type 필수
        """
        has_start = self.start_date is not None
        has_end = self.end_date is not None

        # 하나만 있으면 422
        if has_start != has_end:
            raise ValueError(
                "start_date와 end_date는 함께 지정해야 합니다 (둘 다 or 둘 다 없음)."
            )

        if has_start and has_end:
            # datetime-unification(FR-07): 입력(aware/naive/date-only)을 aware UTC 로 통일 후 비교/저장
            self.start_date = to_utc(self.start_date)
            self.end_date = to_utc(self.end_date)
            # end >= start
            if self.end_date < self.start_date:
                raise ValueError(
                    f"end_date({self.end_date.isoformat()})가 "
                    f"start_date({self.start_date.isoformat()})보다 이릅니다."
                )
            # 범위 상한
            span_days = (self.end_date - self.start_date).days
            if span_days > settings.REPORT_MAX_RANGE_DAYS:
                raise ValueError(
                    f"범위가 상한을 초과합니다 ({span_days}일 > "
                    f"REPORT_MAX_RANGE_DAYS={settings.REPORT_MAX_RANGE_DAYS}일)."
                )
        else:
            # 커스텀 범위 없으면 period_type 필수
            if self.period_type is None:
                raise ValueError(
                    "period_type 또는 (start_date + end_date) 중 하나는 필수입니다."
                )

        return self


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
    """보고서 미리보기 응답 (v6.0-response_schema_audit: period_type Enum→str)"""
    id: int
    title: str
    period_type: str
    start_date: KSTDatetime
    end_date: KSTDatetime
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
    """템플릿 목록 응답 (경량) — v6.0-response_schema_audit: report_type/default_period Enum→str"""
    id: int
    name: str
    description: Optional[str] = None
    report_type: str
    owner_id: Optional[int] = None
    is_public: bool
    component_count: int
    default_period: str
    created_at: KSTDatetime

    model_config = ConfigDict(from_attributes=True)


class ReportGenerationListResponse(BaseModel):
    """보고서 생성 목록 응답 (경량) — v6.0-response_schema_audit: report_type/period_type/status Enum→str"""
    id: int
    report_type: str
    title: str
    period_type: str
    status: str
    created_at: KSTDatetime
    generator_name: Optional[str] = None
    completed_at: Optional[KSTDatetime] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# ReportGeneration Schemas
# ============================================================

class ReportGenerationResponse(BaseModel):
    """
    보고서 생성 결과 응답 스키마
    PRD: PRD_Report_System.md Section 5.6
    """
    # v6.0-response_schema_audit: report_type/period_type/status Enum→str (String 컬럼 지뢰)
    id: int
    report_type: str
    title: str
    period_type: str
    start_date: KSTDatetime
    end_date: KSTDatetime
    status: str
    created_at: KSTDatetime

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
    completed_at: Optional[KSTDatetime] = None

    model_config = ConfigDict(from_attributes=True)
