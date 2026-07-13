# PRD: 통합 보고서 시스템 (Report System) 설계

**문서 버전**: v1.4
**작성일**: 2026-01-22
**상태**: Implementation Ready

---

## 1. 개요

### 1.1 목적

GOP 통합 관제 시스템의 운영 현황을 분석하고 PDF 보고서로 출력하는 시스템을 구현한다.

### 1.2 범위

| 포함 | 제외 |
|------|------|
| 정형 보고서 (고정 레이아웃) | 연결 이벤트 (Connection Event) |
| 비정형 보고서 (컴포넌트 선택) | 실시간 대시보드 |
| Device/Event/System 통계 | |
| 차트 시각화 + 데이터그리드 | |
| PDF 다운로드 | |

### 1.3 변경 영향 범위

| 영역 | 변경 내용 |
|------|-----------|
| **DB 스키마** | report_templates, report_generations 테이블 추가 |
| **Enum** | EnumReportType, EnumReportPeriod, EnumReportStatus, EnumChartType 추가 |
| **모델** | app/models/report.py 신규 |
| **스키마** | app/schemas/report.py 신규 |
| **라우터** | app/routers/reports.py 신규 |
| **서비스** | app/services/report_service.py 신규 |
| **유틸리티** | app/utils/chart_generator.py, pdf_generator.py 신규 |
| **main.py** | 라우터 등록, 태그 추가, Preview 페이지 라우트 |
| **템플릿** | app/templates/reports/preview.html (개발용 미리보기) |
| **GOP_스키마_전체.md** | Section 추가 |
| **GOP_Restful_Api_연동설계.md** | Section 추가 |

---

## 2. 데이터 모델 (DB 스키마)

### 2.1 report_templates 테이블

```sql
-- ============================================================
-- Report Templates Table
-- 비정형 보고서 템플릿 저장
-- ============================================================
CREATE TABLE report_templates (
    id SERIAL PRIMARY KEY,

    -- 기본 정보
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    report_type VARCHAR(20) NOT NULL DEFAULT 'CUSTOM',

    -- 소유자
    owner_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    is_public BOOLEAN NOT NULL DEFAULT FALSE,

    -- 컴포넌트 구성
    components JSONB NOT NULL,

    -- 기본 설정
    default_period VARCHAR(20) DEFAULT '7d',

    -- 타임스탬프
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_report_templates_owner_id ON report_templates(owner_id);
CREATE INDEX idx_report_templates_report_type ON report_templates(report_type);
CREATE INDEX idx_report_templates_is_public ON report_templates(is_public);
```

**필드 설명**:

| 필드 | 타입 | NULL | 기본값 | 설명 |
|------|------|------|--------|------|
| id | SERIAL | NO | AUTO | PK |
| name | VARCHAR(100) | NO | - | 템플릿명 |
| description | VARCHAR(500) | YES | NULL | 설명 |
| report_type | VARCHAR(20) | NO | 'CUSTOM' | STANDARD, CUSTOM |
| owner_id | INTEGER | YES | NULL | FK → users.id |
| is_public | BOOLEAN | NO | FALSE | 공유 여부 |
| components | JSONB | NO | - | 컴포넌트 배열 |
| default_period | VARCHAR(20) | YES | '7d' | 기본 기간 |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 생성일 |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 수정일 |

### 2.2 report_generations 테이블

```sql
-- ============================================================
-- Report Generations Table
-- 보고서 생성 이력 및 결과 저장
-- ============================================================
CREATE TABLE report_generations (
    id SERIAL PRIMARY KEY,

    -- 보고서 정보
    report_type VARCHAR(20) NOT NULL,
    template_id INTEGER REFERENCES report_templates(id) ON DELETE SET NULL,
    title VARCHAR(200) NOT NULL,

    -- 기간 설정
    period_type VARCHAR(20) NOT NULL,
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,

    -- 생성자 정보 (스냅샷)
    generator_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    generator_name VARCHAR(100),
    generator_department VARCHAR(100),

    -- 필터 설정
    severity_filter JSONB,

    -- 결과 데이터
    summary_data JSONB,

    -- 파일 정보
    pdf_file_path VARCHAR(500),
    pdf_file_size INTEGER,

    -- 상태
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    error_message VARCHAR(1000),

    -- 타임스탬프
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_report_generations_template_id ON report_generations(template_id);
CREATE INDEX idx_report_generations_generator_id ON report_generations(generator_id);
CREATE INDEX idx_report_generations_status ON report_generations(status);
CREATE INDEX idx_report_generations_created_at ON report_generations(created_at);
CREATE INDEX idx_report_generations_period ON report_generations(start_date, end_date);
```

**필드 설명**:

| 필드 | 타입 | NULL | 기본값 | 설명 |
|------|------|------|--------|------|
| id | SERIAL | NO | AUTO | PK |
| report_type | VARCHAR(20) | NO | - | STANDARD, CUSTOM |
| template_id | INTEGER | YES | NULL | FK → report_templates.id |
| title | VARCHAR(200) | NO | - | 보고서 제목 |
| period_type | VARCHAR(20) | NO | - | 7d, 30d, 90d, 1y |
| start_date | TIMESTAMP | NO | - | 시작일 |
| end_date | TIMESTAMP | NO | - | 종료일 |
| generator_id | INTEGER | YES | NULL | FK → users.id |
| generator_name | VARCHAR(100) | YES | NULL | 생성자 이름 (스냅샷) |
| generator_department | VARCHAR(100) | YES | NULL | 생성자 소속 (스냅샷) |
| severity_filter | JSONB | YES | NULL | 심각도 필터 |
| summary_data | JSONB | YES | NULL | 요약 통계 데이터 |
| pdf_file_path | VARCHAR(500) | YES | NULL | PDF 파일 경로 |
| pdf_file_size | INTEGER | YES | NULL | PDF 파일 크기 (bytes) |
| status | VARCHAR(20) | NO | 'PENDING' | PENDING, GENERATING, COMPLETED, FAILED |
| error_message | VARCHAR(1000) | YES | NULL | 오류 메시지 |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 생성 요청일 |
| completed_at | TIMESTAMP | YES | NULL | 완료일 |

---

## 3. Enum 정의

### 3.1 app/utils/enums.py 추가

```python
# ============================================================
# Report System Enums
# ============================================================

class EnumReportType(str, Enum):
    """보고서 유형"""
    STANDARD = "STANDARD"   # 정형 보고서
    CUSTOM = "CUSTOM"       # 비정형 보고서


class EnumReportPeriod(str, Enum):
    """보고서 기간"""
    DAYS_7 = "7d"           # 7일
    DAYS_30 = "30d"         # 30일 (1개월)
    DAYS_90 = "90d"         # 90일 (3개월)
    YEAR_1 = "1y"           # 1년


class EnumReportStatus(str, Enum):
    """보고서 생성 상태"""
    PENDING = "PENDING"         # 대기 중
    GENERATING = "GENERATING"   # 생성 중
    COMPLETED = "COMPLETED"     # 완료
    FAILED = "FAILED"           # 실패


class EnumChartType(str, Enum):
    """차트 유형"""
    LINE = "LINE"       # 라인 차트
    BAR = "BAR"         # 막대 차트
    DONUT = "DONUT"     # 도넛 차트
    PIE = "PIE"         # 파이 차트


class EnumReportComponent(str, Enum):
    """보고서 컴포넌트 (21종)"""
    # SUMMARY (1종)
    SUMMARY_CARD = "SUMMARY_CARD"

    # DEVICE (3종)
    DEVICE_STATUS_PIE = "DEVICE_STATUS_PIE"
    DEVICE_TYPE_BAR = "DEVICE_TYPE_BAR"
    DEVICE_GRID = "DEVICE_GRID"

    # EVENT (6종)
    EVENT_SUMMARY_PIE = "EVENT_SUMMARY_PIE"
    EVENT_TREND_LINE = "EVENT_TREND_LINE"
    EVENT_DAILY_BAR = "EVENT_DAILY_BAR"
    EVENT_DETECTION_GRID = "EVENT_DETECTION_GRID"
    EVENT_MALFUNCTION_GRID = "EVENT_MALFUNCTION_GRID"
    EVENT_ACTION_GRID = "EVENT_ACTION_GRID"

    # SYSTEM (5종)
    SYSTEM_SEVERITY_BAR = "SYSTEM_SEVERITY_BAR"
    SYSTEM_TREND_LINE = "SYSTEM_TREND_LINE"
    SYSTEM_CONFIG_GRID = "SYSTEM_CONFIG_GRID"
    SYSTEM_EVENT_GRID = "SYSTEM_EVENT_GRID"
    SYSTEM_AUDIT_GRID = "SYSTEM_AUDIT_GRID"

    # USER (6종) - v1.4
    USER_ROLE_PIE = "USER_ROLE_PIE"
    USER_LOGIN_TREND_LINE = "USER_LOGIN_TREND_LINE"
    USER_LOGIN_RESULT_PIE = "USER_LOGIN_RESULT_PIE"
    USER_GRID = "USER_GRID"
    USER_LOGIN_GRID = "USER_LOGIN_GRID"
    USER_SESSION_GRID = "USER_SESSION_GRID"
```

---

## 4. SQLAlchemy 모델

### 4.1 app/models/report.py (신규)

```python
"""
Report System Models
- ReportTemplate: 비정형 보고서 템플릿
- ReportGeneration: 보고서 생성 이력
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ReportTemplate(Base):
    """비정형 보고서 템플릿"""
    __tablename__ = "report_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    report_type = Column(String(20), nullable=False, default="CUSTOM")

    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_public = Column(Boolean, nullable=False, default=False)

    components = Column(JSON, nullable=False)
    default_period = Column(String(20), default="7d")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    owner = relationship("User", back_populates="report_templates")
    generations = relationship("ReportGeneration", back_populates="template")


class ReportGeneration(Base):
    """보고서 생성 이력"""
    __tablename__ = "report_generations"

    id = Column(Integer, primary_key=True, index=True)

    report_type = Column(String(20), nullable=False)
    template_id = Column(Integer, ForeignKey("report_templates.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(200), nullable=False)

    period_type = Column(String(20), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)

    generator_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    generator_name = Column(String(100), nullable=True)
    generator_department = Column(String(100), nullable=True)

    severity_filter = Column(JSON, nullable=True)
    summary_data = Column(JSON, nullable=True)

    pdf_file_path = Column(String(500), nullable=True)
    pdf_file_size = Column(Integer, nullable=True)

    status = Column(String(20), nullable=False, default="PENDING")
    error_message = Column(String(1000), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    template = relationship("ReportTemplate", back_populates="generations")
    generator = relationship("User", back_populates="report_generations")
```

### 4.2 app/models/user.py 수정

```python
# User 모델에 relationship 추가
class User(Base):
    # ... 기존 필드 ...

    # Report relationships
    report_templates = relationship("ReportTemplate", back_populates="owner")
    report_generations = relationship("ReportGeneration", back_populates="generator")
```

---

## 5. Pydantic 스키마

### 5.1 app/schemas/report.py (신규)

```python
"""
Report System Schemas
"""
from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime
from typing import Optional, List, Dict, Any

from app.utils.enums import EnumReportType, EnumReportPeriod, EnumReportStatus


# ============================================================
# Component Schema
# ============================================================

class ReportComponentConfig(BaseModel):
    """컴포넌트 설정"""
    id: str
    order: int
    enabled: bool = True
    title: Optional[str] = None


# ============================================================
# Report Template Schemas
# ============================================================

class ReportTemplateCreate(BaseModel):
    """템플릿 생성"""
    name: str
    description: Optional[str] = None
    report_type: EnumReportType = EnumReportType.CUSTOM
    is_public: bool = False
    components: List[ReportComponentConfig]
    default_period: EnumReportPeriod = EnumReportPeriod.DAYS_7

    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('name cannot be empty')
        return v


class ReportTemplateUpdate(BaseModel):
    """템플릿 수정 (PATCH)"""
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None
    components: Optional[List[ReportComponentConfig]] = None
    default_period: Optional[EnumReportPeriod] = None


class ReportTemplateResponse(BaseModel):
    """템플릿 응답"""
    id: int
    name: str
    description: Optional[str] = None
    report_type: str
    owner_id: Optional[int] = None
    is_public: bool
    components: List[Dict[str, Any]]
    default_period: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReportTemplateListResponse(BaseModel):
    """템플릿 목록 응답"""
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


# ============================================================
# Report Generation Schemas
# ============================================================

class ReportGenerateRequest(BaseModel):
    """보고서 생성 요청"""
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
    """보고서 생성 결과"""
    id: int
    report_type: str
    template_id: Optional[int] = None
    title: str
    period_type: str
    start_date: datetime
    end_date: datetime
    generator_id: Optional[int] = None
    generator_name: Optional[str] = None
    generator_department: Optional[str] = None
    severity_filter: Optional[List[str]] = None
    summary_data: Optional[Dict[str, Any]] = None
    pdf_file_path: Optional[str] = None
    pdf_file_size: Optional[int] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ReportGenerationListResponse(BaseModel):
    """보고서 생성 목록"""
    id: int
    report_type: str
    title: str
    period_type: str
    generator_name: Optional[str] = None
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Report Data Schemas (미리보기용)
# ============================================================

class ChartData(BaseModel):
    """차트 데이터"""
    labels: List[str]
    values: List[Any]
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
    """보고서 섹션"""
    name: str
    title: str
    charts: List[ChartConfig] = []
    grids: List[GridConfig] = []


class ReportPreviewResponse(BaseModel):
    """보고서 미리보기"""
    id: int
    title: str
    period_type: str
    generator_name: Optional[str] = None
    generator_department: Optional[str] = None
    start_date: datetime
    end_date: datetime
    sections: List[ReportSection]


# ============================================================
# Component List Schema
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
```

---

## 6. API 라우터

### 6.1 app/routers/reports.py (신규)

```python
"""
Report System API Router

Endpoints:
- GET /api/reports/templates - 템플릿 목록 조회
- GET /api/reports/templates/{id} - 템플릿 상세 조회
- POST /api/reports/templates - 템플릿 생성
- PATCH /api/reports/templates/{id} - 템플릿 수정
- DELETE /api/reports/templates/{id} - 템플릿 삭제
- POST /api/reports/generate - 보고서 생성 요청
- GET /api/reports/generations/{id} - 생성 상태 조회
- GET /api/reports/generations/{id}/download - PDF 다운로드
- GET /api/reports/generations/{id}/preview - 미리보기
- GET /api/reports/components - 컴포넌트 목록
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from app.dependencies import get_db, get_current_user
from app.models.report import ReportTemplate, ReportGeneration
from app.models.user import User
from app.schemas.report import (
    ReportTemplateCreate,
    ReportTemplateUpdate,
    ReportTemplateResponse,
    ReportTemplateListResponse,
    ReportGenerateRequest,
    ReportGenerationResponse,
    ReportGenerationListResponse,
    ReportPreviewResponse,
    ComponentCategoryResponse
)
from app.schemas.common import ApiResponse
from app.services.report_service import ReportService
from app.utils.enums import EnumReportType, EnumReportPeriod, EnumReportStatus

router = APIRouter()


# ============================================================
# Template Endpoints
# ============================================================

@router.get("/templates")
def get_templates(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    report_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """템플릿 목록 조회"""
    query = db.query(ReportTemplate)

    # 본인 소유 또는 공개 템플릿만 조회
    query = query.filter(
        (ReportTemplate.owner_id == current_user.id) |
        (ReportTemplate.is_public == True)
    )

    if report_type:
        query = query.filter(ReportTemplate.report_type == report_type)

    total = query.count()
    templates = query.offset((page - 1) * limit).limit(limit).all()

    return ApiResponse(
        success=True,
        message="Report templates retrieved successfully",
        data=[
            {
                **ReportTemplateListResponse.model_validate(t).model_dump(),
                "component_count": len(t.components) if t.components else 0
            }
            for t in templates
        ],
        pagination={
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit
        }
    )


@router.get("/templates/{template_id}")
def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """템플릿 상세 조회"""
    template = db.query(ReportTemplate).filter(ReportTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail=f"ReportTemplate with id {template_id} not found")

    # 권한 확인
    if template.owner_id != current_user.id and not template.is_public:
        raise HTTPException(status_code=403, detail="Access denied")

    return ApiResponse(
        success=True,
        message="Report template retrieved successfully",
        data=ReportTemplateResponse.model_validate(template).model_dump()
    )


@router.post("/templates", status_code=201)
def create_template(
    template_data: ReportTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """템플릿 생성"""
    template = ReportTemplate(
        name=template_data.name,
        description=template_data.description,
        report_type=template_data.report_type.value,
        owner_id=current_user.id,
        is_public=template_data.is_public,
        components=[c.model_dump() for c in template_data.components],
        default_period=template_data.default_period.value
    )

    db.add(template)
    db.commit()
    db.refresh(template)

    return ApiResponse(
        success=True,
        message="Report template created successfully",
        data=ReportTemplateResponse.model_validate(template).model_dump()
    )


@router.patch("/templates/{template_id}")
def update_template(
    template_id: int,
    update_data: ReportTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """템플릿 수정"""
    template = db.query(ReportTemplate).filter(ReportTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail=f"ReportTemplate with id {template_id} not found")

    # 소유자만 수정 가능
    if template.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only owner can update template")

    update_dict = update_data.model_dump(exclude_unset=True)
    if "components" in update_dict and update_dict["components"]:
        update_dict["components"] = [c.model_dump() if hasattr(c, 'model_dump') else c for c in update_dict["components"]]
    if "default_period" in update_dict and update_dict["default_period"]:
        update_dict["default_period"] = update_dict["default_period"].value

    for field, value in update_dict.items():
        setattr(template, field, value)

    db.commit()
    db.refresh(template)

    return ApiResponse(
        success=True,
        message="Report template updated successfully",
        data=ReportTemplateResponse.model_validate(template).model_dump()
    )


@router.delete("/templates/{template_id}")
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """템플릿 삭제"""
    template = db.query(ReportTemplate).filter(ReportTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail=f"ReportTemplate with id {template_id} not found")

    # 소유자만 삭제 가능
    if template.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only owner can delete template")

    db.delete(template)
    db.commit()

    return ApiResponse(
        success=True,
        message="Report template deleted successfully",
        data=None
    )


# ============================================================
# Generation Endpoints
# ============================================================

@router.post("/generate", status_code=202)
def generate_report(
    request: ReportGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """보고서 생성 요청"""
    # 기간 계산
    end_date = datetime.now()
    period_days = {
        EnumReportPeriod.DAYS_7: 7,
        EnumReportPeriod.DAYS_30: 30,
        EnumReportPeriod.DAYS_90: 90,
        EnumReportPeriod.YEAR_1: 365
    }
    start_date = end_date - timedelta(days=period_days.get(request.period_type, 7))

    # 생성 레코드 생성
    generation = ReportGeneration(
        report_type=request.report_type.value,
        template_id=request.template_id,
        title=request.title,
        period_type=request.period_type.value,
        start_date=start_date,
        end_date=end_date,
        generator_id=current_user.id,
        generator_name=current_user.name,
        generator_department=getattr(current_user, 'department', None),
        severity_filter=request.severity_filter,
        status=EnumReportStatus.PENDING.value
    )

    db.add(generation)
    db.commit()
    db.refresh(generation)

    # 백그라운드에서 보고서 생성 시작
    # TODO: Celery 또는 BackgroundTasks 사용
    ReportService.generate_report_async(generation.id, db)

    return ApiResponse(
        success=True,
        message="Report generation started",
        data={
            "generation_id": generation.id,
            "status": generation.status
        }
    )


@router.get("/generations")
def get_generations(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """보고서 생성 이력 조회"""
    query = db.query(ReportGeneration).filter(ReportGeneration.generator_id == current_user.id)

    if status:
        query = query.filter(ReportGeneration.status == status)

    query = query.order_by(ReportGeneration.created_at.desc())
    total = query.count()
    generations = query.offset((page - 1) * limit).limit(limit).all()

    return ApiResponse(
        success=True,
        message="Report generations retrieved successfully",
        data=[ReportGenerationListResponse.model_validate(g).model_dump() for g in generations],
        pagination={
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit
        }
    )


@router.get("/generations/{generation_id}")
def get_generation(
    generation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """보고서 생성 상태 조회"""
    generation = db.query(ReportGeneration).filter(ReportGeneration.id == generation_id).first()
    if not generation:
        raise HTTPException(status_code=404, detail=f"ReportGeneration with id {generation_id} not found")

    # 권한 확인
    if generation.generator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    response_data = ReportGenerationResponse.model_validate(generation).model_dump()
    if generation.status == EnumReportStatus.COMPLETED.value:
        response_data["pdf_download_url"] = f"/api/reports/generations/{generation_id}/download"

    return ApiResponse(
        success=True,
        message="Report generation retrieved successfully",
        data=response_data
    )


@router.get("/generations/{generation_id}/download")
def download_report(
    generation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """PDF 다운로드"""
    generation = db.query(ReportGeneration).filter(ReportGeneration.id == generation_id).first()
    if not generation:
        raise HTTPException(status_code=404, detail=f"ReportGeneration with id {generation_id} not found")

    if generation.generator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if generation.status != EnumReportStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="Report not completed yet")

    if not generation.pdf_file_path:
        raise HTTPException(status_code=404, detail="PDF file not found")

    return FileResponse(
        path=generation.pdf_file_path,
        filename=f"{generation.title}.pdf",
        media_type="application/pdf"
    )


@router.get("/generations/{generation_id}/preview")
def preview_report(
    generation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """보고서 미리보기 (JSON)"""
    generation = db.query(ReportGeneration).filter(ReportGeneration.id == generation_id).first()
    if not generation:
        raise HTTPException(status_code=404, detail=f"ReportGeneration with id {generation_id} not found")

    if generation.generator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if generation.status != EnumReportStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="Report not completed yet")

    # 미리보기 데이터 생성
    preview_data = ReportService.get_preview_data(generation, db)

    return ApiResponse(
        success=True,
        message="Report preview retrieved successfully",
        data=preview_data
    )


# ============================================================
# Component Endpoints
# ============================================================

@router.get("/components")
def get_components():
    """가용 컴포넌트 목록"""
    components = {
        "categories": [
            {
                "name": "SUMMARY",
                "label": "요약",
                "components": [
                    {"id": "SUMMARY_CARD", "label": "전체 요약 카드", "description": "장비/이벤트/시스템 요약", "chart_type": None, "category": "SUMMARY"}
                ]
            },
            {
                "name": "DEVICE",
                "label": "장비",
                "components": [
                    {"id": "DEVICE_STATUS_PIE", "label": "장비 상태 파이차트", "description": "정상/고장/비활성 분포", "chart_type": "PIE", "category": "DEVICE"},
                    {"id": "DEVICE_TYPE_BAR", "label": "장비 유형 막대차트", "description": "유형별 장비 현황", "chart_type": "BAR", "category": "DEVICE"},
                    {"id": "DEVICE_GRID", "label": "장비 목록", "description": "장비 상세 목록", "chart_type": None, "category": "DEVICE"}
                ]
            },
            {
                "name": "EVENT",
                "label": "이벤트",
                "components": [
                    {"id": "EVENT_SUMMARY_PIE", "label": "이벤트 유형 파이차트", "description": "탐지/장애/조치 분포", "chart_type": "PIE", "category": "EVENT"},
                    {"id": "EVENT_TREND_LINE", "label": "이벤트 추세 라인차트", "description": "일별 이벤트 추세", "chart_type": "LINE", "category": "EVENT"},
                    {"id": "EVENT_DAILY_BAR", "label": "일별 이벤트 막대차트", "description": "일별 이벤트 현황", "chart_type": "BAR", "category": "EVENT"},
                    {"id": "EVENT_DETECTION_GRID", "label": "탐지 이벤트 목록", "description": "탐지 이벤트 상세", "chart_type": None, "category": "EVENT"},
                    {"id": "EVENT_MALFUNCTION_GRID", "label": "장애 이벤트 목록", "description": "장애 이벤트 상세", "chart_type": None, "category": "EVENT"},
                    {"id": "EVENT_ACTION_GRID", "label": "조치 이벤트 목록", "description": "조치 이벤트 상세", "chart_type": None, "category": "EVENT"}
                ]
            },
            {
                "name": "SYSTEM",
                "label": "시스템",
                "components": [
                    {"id": "SYSTEM_SEVERITY_BAR", "label": "심각도별 막대차트", "description": "심각도별 로그 현황", "chart_type": "BAR", "category": "SYSTEM"},
                    {"id": "SYSTEM_TREND_LINE", "label": "시스템 로그 추세", "description": "일별 로그 추세", "chart_type": "LINE", "category": "SYSTEM"},
                    {"id": "SYSTEM_CONFIG_GRID", "label": "설정 변경 이력", "description": "설정 변경 목록", "chart_type": None, "category": "SYSTEM"},
                    {"id": "SYSTEM_EVENT_GRID", "label": "시스템 이벤트 목록", "description": "시스템 이벤트 상세", "chart_type": None, "category": "SYSTEM"},
                    {"id": "SYSTEM_AUDIT_GRID", "label": "감사 로그 목록", "description": "감사 로그 상세", "chart_type": None, "category": "SYSTEM"}
                ]
            },
            {
                "name": "USER",
                "label": "사용자",
                "components": [
                    {"id": "USER_ROLE_PIE", "label": "역할별 사용자 분포", "description": "역할별 사용자 현황", "chart_type": "PIE", "category": "USER"},
                    {"id": "USER_LOGIN_TREND_LINE", "label": "일별 로그인 추이", "description": "일별 로그인 시도 추이", "chart_type": "LINE", "category": "USER"},
                    {"id": "USER_LOGIN_RESULT_PIE", "label": "로그인 결과 분포", "description": "로그인 성공/실패 분포", "chart_type": "PIE", "category": "USER"},
                    {"id": "USER_GRID", "label": "사용자 목록", "description": "사용자 상세 목록", "chart_type": None, "category": "USER"},
                    {"id": "USER_LOGIN_GRID", "label": "로그인 이력", "description": "로그인 시도 이력", "chart_type": None, "category": "USER"},
                    {"id": "USER_SESSION_GRID", "label": "세션 목록", "description": "사용자 세션 목록", "chart_type": None, "category": "USER"}
                ]
            }
        ]
    }

    return ApiResponse(
        success=True,
        message="Report components retrieved successfully",
        data=components
    )
```

---

## 7. main.py 수정사항

### 7.1 import 추가

```python
from app.routers import ..., reports
```

### 7.2 tags_metadata 추가

```python
{
    "name": "Reports",
    "description": "통합 보고서 시스템 API. 정형/비정형 보고서 생성 및 PDF 다운로드.",
},
```

### 7.3 라우터 등록

```python
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
```

### 7.4 개발용 Preview 페이지 라우트 (Section 10 참조)

```python
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

templates = Jinja2Templates(directory="app/templates")

@app.get("/reports/preview/{generation_id}", response_class=HTMLResponse)
async def report_preview_page(request: Request, generation_id: int, db: Session = Depends(get_db)):
    """개발용 보고서 미리보기 페이지 - 차트/그리드를 HTML로 렌더링"""
    # 상세 구현은 Section 10.3 참조
    ...
```

**접근 방법**: 브라우저에서 `http://localhost:8000/reports/preview/{id}` 직접 접속

---

## 8. GOP_스키마_전체.md 업데이트 가이드

### 8.1 추가 위치

**Section 8. Report System** (신규 섹션)

### 8.2 추가 내용

```markdown
---

## 8. Report System

보고서 템플릿 및 생성 이력을 관리합니다.

### 8.1 report_templates 테이블

비정형 보고서 템플릿을 저장합니다.

#### PostgreSQL CREATE TABLE

```sql
CREATE TABLE report_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    report_type VARCHAR(20) NOT NULL DEFAULT 'CUSTOM',
    owner_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    is_public BOOLEAN NOT NULL DEFAULT FALSE,
    components JSONB NOT NULL,
    default_period VARCHAR(20) DEFAULT '7d',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

#### 필드 설명

| 필드 | 타입 | NULL | 기본값 | 설명 |
|------|------|------|--------|------|
| id | SERIAL | NO | AUTO | PK |
| name | VARCHAR(100) | NO | - | 템플릿명 |
| description | VARCHAR(500) | YES | NULL | 설명 |
| report_type | VARCHAR(20) | NO | 'CUSTOM' | STANDARD, CUSTOM |
| owner_id | INTEGER | YES | NULL | FK → users.id |
| is_public | BOOLEAN | NO | FALSE | 공유 여부 |
| components | JSONB | NO | - | 컴포넌트 배열 |
| default_period | VARCHAR(20) | YES | '7d' | 기본 기간 |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 생성일 |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 수정일 |

#### components JSON 구조

```json
[
  {
    "id": "DEVICE_STATUS_PIE",
    "order": 1,
    "enabled": true,
    "title": "장비 상태 현황"
  }
]
```

### 8.2 report_generations 테이블

보고서 생성 이력을 저장합니다.

#### PostgreSQL CREATE TABLE

```sql
CREATE TABLE report_generations (
    id SERIAL PRIMARY KEY,
    report_type VARCHAR(20) NOT NULL,
    template_id INTEGER REFERENCES report_templates(id) ON DELETE SET NULL,
    title VARCHAR(200) NOT NULL,
    period_type VARCHAR(20) NOT NULL,
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    generator_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    generator_name VARCHAR(100),
    generator_department VARCHAR(100),
    severity_filter JSONB,
    summary_data JSONB,
    pdf_file_path VARCHAR(500),
    pdf_file_size INTEGER,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    error_message VARCHAR(1000),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);
```

#### 필드 설명

| 필드 | 타입 | NULL | 기본값 | 설명 |
|------|------|------|--------|------|
| id | SERIAL | NO | AUTO | PK |
| report_type | VARCHAR(20) | NO | - | STANDARD, CUSTOM |
| template_id | INTEGER | YES | NULL | FK → report_templates.id |
| title | VARCHAR(200) | NO | - | 보고서 제목 |
| period_type | VARCHAR(20) | NO | - | 7d, 30d, 90d, 1y |
| start_date | TIMESTAMP | NO | - | 시작일 |
| end_date | TIMESTAMP | NO | - | 종료일 |
| generator_id | INTEGER | YES | NULL | FK → users.id |
| generator_name | VARCHAR(100) | YES | NULL | 생성자 이름 |
| generator_department | VARCHAR(100) | YES | NULL | 생성자 소속 |
| severity_filter | JSONB | YES | NULL | 심각도 필터 |
| summary_data | JSONB | YES | NULL | 요약 데이터 |
| pdf_file_path | VARCHAR(500) | YES | NULL | PDF 경로 |
| pdf_file_size | INTEGER | YES | NULL | PDF 크기 |
| status | VARCHAR(20) | NO | 'PENDING' | 상태 |
| error_message | VARCHAR(1000) | YES | NULL | 오류 메시지 |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 생성일 |
| completed_at | TIMESTAMP | YES | NULL | 완료일 |

### 8.3 Report Enum 정의

#### EnumReportType (보고서 유형)

| 값 | 설명 |
|----|------|
| STANDARD | 정형 보고서 |
| CUSTOM | 비정형 보고서 |

#### EnumReportPeriod (보고서 기간)

| 값 | 설명 |
|----|------|
| 7d | 7일 |
| 30d | 30일 |
| 90d | 90일 |
| 1y | 1년 |

#### EnumReportStatus (보고서 상태)

| 값 | 설명 |
|----|------|
| PENDING | 대기 중 |
| GENERATING | 생성 중 |
| COMPLETED | 완료 |
| FAILED | 실패 |

#### EnumReportComponent (컴포넌트 21종)

| 카테고리 | 값 | 설명 |
|----------|----|----|
| SUMMARY | SUMMARY_CARD | 전체 요약 |
| DEVICE | DEVICE_STATUS_PIE | 상태 파이차트 |
| DEVICE | DEVICE_TYPE_BAR | 유형 막대차트 |
| DEVICE | DEVICE_GRID | 장비 목록 |
| EVENT | EVENT_SUMMARY_PIE | 유형 파이차트 |
| EVENT | EVENT_TREND_LINE | 추세 라인차트 |
| EVENT | EVENT_DAILY_BAR | 일별 막대차트 |
| EVENT | EVENT_DETECTION_GRID | 탐지 목록 |
| EVENT | EVENT_MALFUNCTION_GRID | 장애 목록 |
| EVENT | EVENT_ACTION_GRID | 조치 목록 |
| SYSTEM | SYSTEM_SEVERITY_BAR | 심각도 막대차트 |
| SYSTEM | SYSTEM_TREND_LINE | 로그 추세 |
| SYSTEM | SYSTEM_CONFIG_GRID | 설정변경 목록 |
| SYSTEM | SYSTEM_EVENT_GRID | 시스템이벤트 목록 |
| SYSTEM | SYSTEM_AUDIT_GRID | 감사로그 목록 |
| USER | USER_ROLE_PIE | 역할별 사용자 분포 |
| USER | USER_LOGIN_TREND_LINE | 일별 로그인 추이 |
| USER | USER_LOGIN_RESULT_PIE | 로그인 성공/실패 분포 |
| USER | USER_GRID | 사용자 목록 |
| USER | USER_LOGIN_GRID | 로그인 이력 |
| USER | USER_SESSION_GRID | 세션 목록 |
```

### 8.3 변경 이력 업데이트

```markdown
| **v2.3** | 2026-01-22 | **Report System 추가**<br>• report_templates 테이블 추가<br>• report_generations 테이블 추가<br>• EnumReportType, EnumReportPeriod, EnumReportStatus, EnumReportComponent 추가 |
```

---

## 9. GOP_Restful_Api_연동설계.md 업데이트 가이드

### 9.1 문서 초반 버전 업데이트

```markdown
**문서 버전**: v3.0
**최종 업데이트**: 2026-01-22
```

### 9.2 목차 추가

```markdown
- [9. Report System API](#9-report-system-api)
  - [9.1 Report Templates API](#91-report-templates-api)
  - [9.2 Report Generation API](#92-report-generation-api)
  - [9.3 Report Components API](#93-report-components-api)
```

### 9.3 Section 9 추가 (Report System API)

```markdown
---

## 9. Report System API

보고서 템플릿 관리 및 보고서 생성을 위한 API입니다.

### 9.1 Report Templates API

#### 9.1.1 템플릿 목록 조회

**Endpoint**: `GET /api/reports/templates`

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| page | integer | N | 페이지 번호 (기본값: 1) |
| limit | integer | N | 페이지당 항목 수 (기본값: 20) |
| report_type | string | N | 보고서 유형 필터 |

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Report templates retrieved successfully",
  "data": [
    {
      "id": 1,
      "name": "주간 운영 보고서",
      "description": "주간 운영 현황 템플릿",
      "report_type": "CUSTOM",
      "owner_id": 1,
      "is_public": true,
      "component_count": 10,
      "default_period": "7d",
      "created_at": "2026-01-22T10:00:00.000000"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 5,
    "total_pages": 1
  }
}
```

#### 9.1.2 템플릿 상세 조회

**Endpoint**: `GET /api/reports/templates/{template_id}`

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Report template retrieved successfully",
  "data": {
    "id": 1,
    "name": "주간 운영 보고서",
    "description": "주간 운영 현황 템플릿",
    "report_type": "CUSTOM",
    "owner_id": 1,
    "is_public": true,
    "components": [
      {
        "id": "DEVICE_STATUS_PIE",
        "order": 1,
        "enabled": true,
        "title": "장비 상태"
      }
    ],
    "default_period": "7d",
    "created_at": "2026-01-22T10:00:00.000000",
    "updated_at": "2026-01-22T10:00:00.000000"
  }
}
```

#### 9.1.3 템플릿 생성

**Endpoint**: `POST /api/reports/templates`

**Request Body**:
```json
{
  "name": "커스텀 보고서",
  "description": "설명",
  "report_type": "CUSTOM",
  "is_public": false,
  "components": [
    {
      "id": "DEVICE_STATUS_PIE",
      "order": 1,
      "enabled": true,
      "title": "장비 상태"
    }
  ],
  "default_period": "7d"
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| name | string | Y | 템플릿명 |
| description | string | N | 설명 |
| report_type | string | N | STANDARD, CUSTOM (기본: CUSTOM) |
| is_public | boolean | N | 공유 여부 (기본: false) |
| components | array | Y | 컴포넌트 배열 |
| default_period | string | N | 기본 기간 (기본: 7d) |

**Response (201 Created)**: 생성된 템플릿 정보

#### 9.1.4 템플릿 수정

**Endpoint**: `PATCH /api/reports/templates/{template_id}`

**Request Body** (모든 필드 선택적):
```json
{
  "name": "수정된 이름",
  "is_public": true
}
```

#### 9.1.5 템플릿 삭제

**Endpoint**: `DELETE /api/reports/templates/{template_id}`

### 9.2 Report Generation API

#### 9.2.1 보고서 생성 요청

**Endpoint**: `POST /api/reports/generate`

**Request Body**:
```json
{
  "report_type": "STANDARD",
  "title": "2026년 1월 3주차 운영 보고서",
  "period_type": "7d",
  "template_id": null,
  "severity_filter": ["WARNING", "ERROR", "CRITICAL"]
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| report_type | string | Y | STANDARD, CUSTOM |
| title | string | Y | 보고서 제목 |
| period_type | string | Y | 7d, 30d, 90d, 1y |
| template_id | integer | N | CUSTOM일 때 템플릿 ID |
| severity_filter | array | N | 심각도 필터 |

**Response (202 Accepted)**:
```json
{
  "success": true,
  "message": "Report generation started",
  "data": {
    "generation_id": 100,
    "status": "PENDING"
  }
}
```

#### 9.2.2 보고서 생성 상태 조회

**Endpoint**: `GET /api/reports/generations/{generation_id}`

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Report generation retrieved successfully",
  "data": {
    "id": 100,
    "report_type": "STANDARD",
    "title": "2026년 1월 3주차 운영 보고서",
    "period_type": "7d",
    "start_date": "2026-01-15T00:00:00.000000",
    "end_date": "2026-01-22T00:00:00.000000",
    "generator_name": "홍길동",
    "generator_department": "운영팀",
    "summary_data": {
      "devices": {"total": 150, "normal": 145, "faulty": 3, "inactive": 2},
      "events": {"detection": 450, "malfunction": 48, "action": 25},
      "system_logs": {"total": 1200, "critical": 20, "error": 80}
    },
    "status": "COMPLETED",
    "pdf_download_url": "/api/reports/generations/100/download",
    "created_at": "2026-01-22T10:30:00.000000",
    "completed_at": "2026-01-22T10:30:45.000000"
  }
}
```

#### 9.2.3 보고서 생성 이력 조회

**Endpoint**: `GET /api/reports/generations`

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| page | integer | N | 페이지 번호 |
| limit | integer | N | 페이지당 항목 수 |
| status | string | N | 상태 필터 |

#### 9.2.4 PDF 다운로드

**Endpoint**: `GET /api/reports/generations/{generation_id}/download`

**Response**: PDF 파일 (Content-Type: application/pdf)

#### 9.2.5 보고서 미리보기

**Endpoint**: `GET /api/reports/generations/{generation_id}/preview`

**Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "id": 100,
    "title": "2026년 1월 3주차 운영 보고서",
    "sections": [
      {
        "name": "device",
        "title": "장비 현황",
        "charts": [
          {
            "id": "DEVICE_STATUS_PIE",
            "title": "장비 상태 분포",
            "type": "PIE",
            "data": {
              "labels": ["정상", "고장", "비활성"],
              "values": [145, 3, 2],
              "colors": ["#4CAF50", "#F44336", "#9E9E9E"]
            }
          }
        ],
        "grids": [
          {
            "id": "DEVICE_GRID",
            "title": "장비 목록",
            "columns": ["ID", "유형", "이름", "상태"],
            "rows": [[1, "Controller", "CTL-001", "정상"]],
            "total_rows": 150
          }
        ]
      }
    ]
  }
}
```

### 9.3 Report Components API

#### 9.3.1 컴포넌트 목록 조회

**Endpoint**: `GET /api/reports/components`

**Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "categories": [
      {
        "name": "DEVICE",
        "label": "장비",
        "components": [
          {
            "id": "DEVICE_STATUS_PIE",
            "label": "장비 상태 파이차트",
            "description": "정상/고장/비활성 분포",
            "chart_type": "PIE",
            "category": "DEVICE"
          }
        ]
      }
    ]
  }
}
```
```

### 9.4 부록 10.1 Endpoint 목록에 추가

```markdown
### Reports

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | /api/reports/templates | 템플릿 목록 조회 |
| GET | /api/reports/templates/{id} | 템플릿 상세 조회 |
| POST | /api/reports/templates | 템플릿 생성 |
| PATCH | /api/reports/templates/{id} | 템플릿 수정 |
| DELETE | /api/reports/templates/{id} | 템플릿 삭제 |
| POST | /api/reports/generate | 보고서 생성 요청 |
| GET | /api/reports/generations | 생성 이력 조회 |
| GET | /api/reports/generations/{id} | 생성 상태 조회 |
| GET | /api/reports/generations/{id}/download | PDF 다운로드 |
| GET | /api/reports/generations/{id}/preview | 미리보기 |
| GET | /api/reports/components | 컴포넌트 목록 |
```

### 9.5 변경 이력 업데이트

```markdown
| v3.0 | 2026-01-22 | **Report System API 추가**<br>• 9.1 Report Templates API (CRUD)<br>• 9.2 Report Generation API (생성/조회/다운로드/미리보기)<br>• 9.3 Report Components API<br>• 21종 컴포넌트: SUMMARY(1), DEVICE(3), EVENT(6), SYSTEM(5), USER(6)<br>• 부록 10.1 Endpoint 목록에 Reports 섹션 추가 |
```

---

## 10. 개발용 Preview 페이지

API 개발 중 보고서 결과물을 시각적으로 확인하기 위한 **단일 HTML 페이지**입니다.

### 10.1 목적

| 문제 | 해결 |
|------|------|
| Swagger에서 `/preview` 호출 → JSON만 봄 | HTML 페이지에서 차트/표 렌더링 |
| PDF 다운로드 후 열어봐야 확인 가능 | 브라우저에서 바로 미리보기 |

### 10.2 엔드포인트

```
GET /reports/preview/{generation_id}
```

- **용도**: 개발/테스트용 시각적 미리보기
- **응답**: HTML 페이지 (차트 + 그리드 렌더링)
- **인증**: 불필요 (개발 편의)

### 10.3 main.py 추가 코드

```python
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

templates = Jinja2Templates(directory="app/templates")

@app.get("/reports/preview/{generation_id}", response_class=HTMLResponse)
async def report_preview_page(request: Request, generation_id: int, db: Session = Depends(get_db)):
    """개발용 보고서 미리보기 페이지"""
    generation = db.query(ReportGeneration).filter(ReportGeneration.id == generation_id).first()
    if not generation:
        raise HTTPException(status_code=404, detail="Report not found")

    # 미리보기 데이터 조회
    preview_data = ReportService.get_preview_data(generation, db)

    return templates.TemplateResponse("reports/preview.html", {
        "request": request,
        "report": generation,
        "preview": preview_data
    })
```

### 10.4 preview.html 템플릿

```html
<!DOCTYPE html>
<html>
<head>
    <title>Report Preview - {{ report.title }}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: #1a365d; color: white; padding: 20px; margin-bottom: 20px; }
        .section { margin-bottom: 30px; border: 1px solid #ddd; padding: 15px; }
        .section-title { font-size: 18px; font-weight: bold; margin-bottom: 15px; }
        .chart-container { width: 400px; height: 300px; display: inline-block; margin: 10px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background: #f5f5f5; }
        .download-btn { background: #2563eb; color: white; padding: 10px 20px; text-decoration: none; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ report.title }}</h1>
        <p>기간: {{ report.start_date.strftime('%Y-%m-%d') }} ~ {{ report.end_date.strftime('%Y-%m-%d') }}</p>
        <p>생성자: {{ report.generator_name }} ({{ report.generator_department }})</p>
        <a href="/api/reports/generations/{{ report.id }}/download" class="download-btn">📥 PDF 다운로드</a>
    </div>

    {% for section in preview.sections %}
    <div class="section">
        <div class="section-title">{{ section.title }}</div>

        <!-- Charts -->
        {% for chart in section.charts %}
        <div class="chart-container">
            <canvas id="chart-{{ chart.id }}"></canvas>
        </div>
        <script>
            new Chart(document.getElementById('chart-{{ chart.id }}'), {
                type: '{{ chart.type|lower }}',
                data: {
                    labels: {{ chart.data.labels|tojson }},
                    datasets: [{
                        data: {{ chart.data.values|tojson }},
                        backgroundColor: {{ chart.data.colors|tojson if chart.data.colors else "['#4CAF50','#FF9800','#F44336','#2196F3']"|safe }}
                    }]
                },
                options: { plugins: { title: { display: true, text: '{{ chart.title }}' }}}
            });
        </script>
        {% endfor %}

        <!-- Grids -->
        {% for grid in section.grids %}
        <h4>{{ grid.title }} (총 {{ grid.total_rows }}건)</h4>
        <table>
            <thead><tr>{% for col in grid.columns %}<th>{{ col }}</th>{% endfor %}</tr></thead>
            <tbody>
                {% for row in grid.rows[:10] %}
                <tr>{% for cell in row %}<td>{{ cell }}</td>{% endfor %}</tr>
                {% endfor %}
            </tbody>
        </table>
        {% endfor %}
    </div>
    {% endfor %}
</body>
</html>
```

### 10.5 사용 흐름

```
1. POST /api/reports/generate     →  보고서 생성 요청
2. GET /api/reports/generations/1  →  상태 확인 (COMPLETED)
3. GET /reports/preview/1          →  브라우저에서 시각적 확인
4. GET /api/reports/generations/1/download  →  PDF 다운로드
```

---

## 11. 파일 구조

```
app/
├── models/
│   └── report.py                    # ReportTemplate, ReportGeneration 모델
├── schemas/
│   └── report.py                    # Pydantic 스키마
├── routers/
│   └── reports.py                   # API 라우터
├── services/
│   └── report_service.py            # 비즈니스 로직
├── utils/
│   ├── enums.py                     # Enum 추가 (EnumReportType 등)
│   ├── chart_generator.py           # 차트 생성 유틸리티
│   └── pdf_generator.py             # PDF 생성 유틸리티
└── templates/
    └── reports/
        └── preview.html             # 개발용 미리보기 페이지

generated_reports/                   # PDF 저장 디렉토리
└── {year}/{month}/
    └── report_{id}.pdf

docs/
├── GOP_스키마_전체.md               # Section 추가
└── GOP_Restful_Api_연동설계.md      # Section 추가
```

---

## 12. 구현 체크리스트

### Phase 1: 기반 구조

- [x] DB 마이그레이션 스크립트 작성
  - [x] report_templates 테이블 생성
  - [x] report_generations 테이블 생성
  - [x] 인덱스 생성
- [x] app/utils/enums.py에 Enum 추가
  - [x] EnumReportType, EnumReportPeriod, EnumReportStatus, EnumReportComponent (21종)
- [x] app/models/report.py 생성
- [x] app/models/user.py 수정 (relationship 추가)
- [x] app/schemas/report.py 생성
  - [x] ChartData, ChartConfig, GridConfig, ReportSection, ReportPreviewResponse
  - [x] ComponentInfo, ComponentCategoryResponse
  - [x] ReportTemplateListResponse, ReportGenerationListResponse
- [x] app/routers/reports.py 생성

### Phase 2: 서비스 로직

- [x] app/services/report_service.py 생성
  - [x] Device 통계 수집 (상태별, 유형별)
  - [x] Event 통계 수집 (Detection, Malfunction, Action / Connection 제외)
  - [x] System 로그 통계 수집 (심각도별, 일별 추세)
  - [x] User 통계 수집 (역할별 분포, 로그인 추이, 로그인 결과)
  - [x] Grid 데이터 조회 (Device, Detection, Malfunction, Action, SystemEvent, Config, Audit, User, UserLogin, UserSession)
  - [x] 구조화된 미리보기 데이터 (get_structured_preview_data)
  - [x] PDF 테이블 통합 (generate_report_async에 grid 데이터 포함)

### Phase 3: 시각화

- [x] requirements.txt 업데이트 (reportlab, matplotlib)
- [x] app/utils/chart_generator.py 생성 (PIE, BAR, LINE, DONUT)
- [x] app/utils/pdf_generator.py 생성 (_build_table 포함)

### Phase 4: main.py 연동

- [x] reports 라우터 import 및 등록
- [x] tags_metadata 추가
- [x] 개발용 Preview 페이지 라우트 추가 (구조화된 데이터 사용)

### Phase 5: Preview 페이지

- [x] app/templates/reports/preview.html 생성
- [x] Chart.js CDN 연동 (구조화된 labels/values 데이터 처리)
- [x] 차트/그리드 렌더링 (columns/rows 테이블 지원)

### Phase 6: Router 개선

- [x] Preview API: 구조화된 sections/charts/grids 응답
- [x] Download: FileResponse PDF 다운로드
- [x] Components: label, chart_type 필드 포함 (5개 카테고리)
- [x] Templates list: component_count 경량 응답
- [x] Generations list: 경량 필드 응답

### Phase 7: 문서 업데이트

- [x] GOP_스키마_전체.md - Section 추가
- [x] GOP_Restful_Api_연동설계.md - Section 추가
- [x] PRD_Report_System.md - 구현 체크리스트 반영

---

## 13. 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| v1.4 | 2026-01-30 | USER 컴포넌트 6종 추가 (EnumReportComponent 15종→21종) |
| v1.3 | 2026-01-22 | 개발용 Preview 페이지 추가 (Section 10), UI 간소화 |
| v1.2 | 2026-01-22 | 구현 가이드 추가 (코드, 스키마, 문서 업데이트 상세화) |
| v1.1 | 2026-01-22 | 옵션 간소화 (컴포넌트 34종→15종→v1.4에서 21종) |
| v1.0 | 2026-01-22 | 초기 PRD 작성 |

---

**문서 끝**
