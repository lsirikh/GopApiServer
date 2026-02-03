"""
Report System API Router
PRD: PRD_Report_System.md Section 6

Endpoints:
- GET /api/reports/templates - 템플릿 목록 조회
- POST /api/reports/templates - 템플릿 생성
- GET /api/reports/templates/{id} - 템플릿 상세 조회
- PATCH /api/reports/templates/{id} - 템플릿 수정
- DELETE /api/reports/templates/{id} - 템플릿 삭제
- POST /api/reports/generate - 보고서 생성 요청
- GET /api/reports/generations - 생성 이력 조회
- GET /api/reports/generations/{id} - 생성 상세 조회
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
import os

from app.dependencies import get_db
from app.services.report_service import ReportService
from app.config import settings
from app.models.report import ReportTemplate, ReportGeneration
from app.schemas.report import (
    ReportTemplateCreate,
    ReportTemplateUpdate,
    ReportTemplateResponse,
    ReportGenerateRequest,
    ReportGenerationResponse,
)
from app.schemas.common import ApiResponse
from app.utils.enums import EnumReportComponent

router = APIRouter()


# ==============================================================================
# Component Categories Data
# ==============================================================================

COMPONENT_CATEGORIES = [
    {
        "category": "SUMMARY",
        "label": "요약",
        "components": [
            {"id": EnumReportComponent.SUMMARY_CARD.value, "name": "요약 카드", "description": "전체 현황 요약", "chart_type": None},
        ]
    },
    {
        "category": "DEVICE",
        "label": "장비",
        "components": [
            {"id": EnumReportComponent.DEVICE_STATUS_PIE.value, "name": "장비 상태 파이", "description": "장비 상태별 분포", "chart_type": "PIE"},
            {"id": EnumReportComponent.DEVICE_TYPE_BAR.value, "name": "장비 유형 바", "description": "장비 유형별 현황", "chart_type": "BAR"},
            {"id": EnumReportComponent.DEVICE_GRID.value, "name": "장비 그리드", "description": "장비 목록 테이블", "chart_type": None},
        ]
    },
    {
        "category": "EVENT",
        "label": "이벤트",
        "components": [
            {"id": EnumReportComponent.EVENT_SUMMARY_PIE.value, "name": "이벤트 요약 파이", "description": "이벤트 유형별 분포", "chart_type": "PIE"},
            {"id": EnumReportComponent.EVENT_TREND_LINE.value, "name": "이벤트 추이 라인", "description": "이벤트 발생 추이", "chart_type": "LINE"},
            {"id": EnumReportComponent.EVENT_DAILY_BAR.value, "name": "일별 이벤트 바", "description": "일별 이벤트 현황", "chart_type": "BAR"},
            {"id": EnumReportComponent.EVENT_DETECTION_GRID.value, "name": "탐지 이벤트 그리드", "description": "탐지 이벤트 목록", "chart_type": None},
            {"id": EnumReportComponent.EVENT_MALFUNCTION_GRID.value, "name": "장애 이벤트 그리드", "description": "장애 이벤트 목록", "chart_type": None},
            {"id": EnumReportComponent.EVENT_ACTION_GRID.value, "name": "조치 이벤트 그리드", "description": "조치 이벤트 목록", "chart_type": None},
        ]
    },
    {
        "category": "SYSTEM",
        "label": "시스템",
        "components": [
            {"id": EnumReportComponent.SYSTEM_SEVERITY_BAR.value, "name": "심각도 바", "description": "심각도별 분포", "chart_type": "BAR"},
            {"id": EnumReportComponent.SYSTEM_TREND_LINE.value, "name": "시스템 추이 라인", "description": "시스템 현황 추이", "chart_type": "LINE"},
            {"id": EnumReportComponent.SYSTEM_CONFIG_GRID.value, "name": "설정 그리드", "description": "시스템 설정 목록", "chart_type": None},
            {"id": EnumReportComponent.SYSTEM_EVENT_GRID.value, "name": "시스템 이벤트 그리드", "description": "시스템 이벤트 목록", "chart_type": None},
            {"id": EnumReportComponent.SYSTEM_AUDIT_GRID.value, "name": "감사 로그 그리드", "description": "감사 로그 목록", "chart_type": None},
        ]
    },
    {
        "category": "USER",
        "label": "사용자",
        "components": [
            {"id": EnumReportComponent.USER_ROLE_PIE.value, "name": "역할별 사용자 분포", "description": "역할별 사용자 현황", "chart_type": "PIE"},
            {"id": EnumReportComponent.USER_LOGIN_TREND_LINE.value, "name": "일별 로그인 추이", "description": "일별 로그인 시도 추이", "chart_type": "LINE"},
            {"id": EnumReportComponent.USER_LOGIN_RESULT_PIE.value, "name": "로그인 결과 분포", "description": "로그인 성공/실패 분포", "chart_type": "PIE"},
            {"id": EnumReportComponent.USER_GRID.value, "name": "사용자 그리드", "description": "사용자 상세 목록", "chart_type": None},
            {"id": EnumReportComponent.USER_LOGIN_GRID.value, "name": "로그인 이력 그리드", "description": "로그인 시도 이력", "chart_type": None},
            {"id": EnumReportComponent.USER_SESSION_GRID.value, "name": "세션 그리드", "description": "사용자 세션 목록", "chart_type": None},
        ]
    },
]


# ==============================================================================
# Helper Functions
# ==============================================================================

def _template_to_response(template: ReportTemplate) -> dict:
    """ReportTemplate 모델을 응답 딕셔너리로 변환 (상세 조회용)"""
    return {
        "id": template.id,
        "name": template.name,
        "description": template.description,
        "report_type": template.report_type,
        "owner_id": template.owner_id,
        "is_public": template.is_public,
        "components": template.components,
        "default_period": template.default_period,
        "created_at": template.created_at,
        "updated_at": template.updated_at,
    }


def _template_to_list_response(template: ReportTemplate) -> dict:
    """ReportTemplate 모델을 목록 응답 딕셔너리로 변환 (경량)"""
    return {
        "id": template.id,
        "name": template.name,
        "description": template.description,
        "report_type": template.report_type,
        "owner_id": template.owner_id,
        "is_public": template.is_public,
        "component_count": len(template.components) if template.components else 0,
        "default_period": template.default_period,
        "created_at": template.created_at,
    }


# ==============================================================================
# Report Components Endpoints
# ==============================================================================

@router.get("/components")
def get_components():
    """
    보고서 컴포넌트 목록 조회

    **응답**:
    - 4개 카테고리: SUMMARY, DEVICE, EVENT, SYSTEM
    - 각 카테고리별 컴포넌트 목록

    PRD Reference: PRD_Report_System.md Section 3.1
    """
    return ApiResponse(
        success=True,
        message="Report components retrieved successfully",
        data=COMPONENT_CATEGORIES
    )


# ==============================================================================
# Report Templates Endpoints
# ==============================================================================

@router.get("/templates")
def get_templates(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    db: Session = Depends(get_db)
):
    """
    보고서 템플릿 목록 조회

    **파라미터**:
    - **page**: 페이지 번호 (default: 1)
    - **limit**: 페이지당 항목 수 (default: 20, max: 100)

    PRD Reference: PRD_Report_System.md Section 6
    """
    query = db.query(ReportTemplate)

    # 정렬 및 페이지네이션
    query = query.order_by(ReportTemplate.created_at.desc())
    offset = (page - 1) * limit
    templates = query.offset(offset).limit(limit).all()

    return ApiResponse(
        success=True,
        message="Report templates retrieved successfully",
        data=[_template_to_list_response(t) for t in templates]
    )


@router.post("/templates", status_code=201)
def create_template(
    template_data: ReportTemplateCreate,
    db: Session = Depends(get_db)
):
    """
    보고서 템플릿 생성

    **필수 필드**:
    - **name**: 템플릿 이름
    - **components**: 컴포넌트 설정 목록

    PRD Reference: PRD_Report_System.md Section 6
    """
    # Convert components to dict list for JSON storage
    components_data = [comp.model_dump() for comp in template_data.components]

    template = ReportTemplate(
        name=template_data.name,
        description=template_data.description,
        report_type=template_data.report_type.value if template_data.report_type else "CUSTOM",
        is_public=template_data.is_public if template_data.is_public is not None else False,
        components=components_data,
        default_period=template_data.default_period.value if template_data.default_period else "7d",
    )

    db.add(template)
    db.commit()
    db.refresh(template)

    return ApiResponse(
        success=True,
        message="Report template created successfully",
        data=_template_to_response(template)
    )


@router.get("/templates/{template_id}")
def get_template(
    template_id: int,
    db: Session = Depends(get_db)
):
    """
    보고서 템플릿 상세 조회

    **파라미터**:
    - **template_id**: 템플릿 ID

    PRD Reference: PRD_Report_System.md Section 6
    """
    template = db.query(ReportTemplate).filter(ReportTemplate.id == template_id).first()

    if not template:
        raise HTTPException(status_code=404, detail="Report template not found")

    return ApiResponse(
        success=True,
        message="Report template retrieved successfully",
        data=_template_to_response(template)
    )


@router.patch("/templates/{template_id}")
def update_template(
    template_id: int,
    template_data: ReportTemplateUpdate,
    db: Session = Depends(get_db)
):
    """
    보고서 템플릿 수정 (부분 업데이트)

    **파라미터**:
    - **template_id**: 템플릿 ID
    - **body**: 수정할 필드만 포함

    PRD Reference: PRD_Report_System.md Section 6
    """
    template = db.query(ReportTemplate).filter(ReportTemplate.id == template_id).first()

    if not template:
        raise HTTPException(status_code=404, detail="Report template not found")

    # Update only provided fields
    update_data = template_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "components" and value is not None:
            # Convert components to dict list
            value = [comp.model_dump() if hasattr(comp, 'model_dump') else comp for comp in value]
        if field == "report_type" and value is not None:
            value = value.value if hasattr(value, 'value') else value
        if field == "default_period" and value is not None:
            value = value.value if hasattr(value, 'value') else value
        setattr(template, field, value)

    db.commit()
    db.refresh(template)

    return ApiResponse(
        success=True,
        message="Report template updated successfully",
        data=_template_to_response(template)
    )


@router.delete("/templates/{template_id}")
def delete_template(
    template_id: int,
    db: Session = Depends(get_db)
):
    """
    보고서 템플릿 삭제

    **파라미터**:
    - **template_id**: 템플릿 ID

    PRD Reference: PRD_Report_System.md Section 6
    """
    template = db.query(ReportTemplate).filter(ReportTemplate.id == template_id).first()

    if not template:
        raise HTTPException(status_code=404, detail="Report template not found")

    db.delete(template)
    db.commit()

    return ApiResponse(
        success=True,
        message="Report template deleted successfully",
        data={"id": template_id}
    )


# ==============================================================================
# Report Generation Endpoints
# ==============================================================================

def _calculate_date_range(period_type: str) -> tuple[datetime, datetime]:
    """기간 타입에 따른 시작일/종료일 계산"""
    end_date = datetime.now(settings.tz)

    period_days = {
        "7d": 7,
        "30d": 30,
        "90d": 90,
        "1y": 365,
    }

    days = period_days.get(period_type, 7)
    start_date = end_date - timedelta(days=days)

    return start_date, end_date


def _generation_to_response(generation: ReportGeneration) -> dict:
    """ReportGeneration 모델을 응답 딕셔너리로 변환"""
    response = {
        "id": generation.id,
        "report_type": generation.report_type,
        "template_id": generation.template_id,
        "title": generation.title,
        "period_type": generation.period_type,
        "start_date": generation.start_date,
        "end_date": generation.end_date,
        "generator_id": generation.generator_id,
        "generator_name": generation.generator_name,
        "status": generation.status,
        "created_at": generation.created_at,
        "completed_at": generation.completed_at,
    }

    # Preview URL (항상 포함)
    response["preview_html_url"] = f"/reports/preview/{generation.id}"

    # COMPLETED 상태이고 pdf_file_path가 있으면 다운로드 URL 포함
    if generation.status == "COMPLETED" and generation.pdf_file_path:
        response["pdf_download_url"] = f"/api/reports/generations/{generation.id}/download"

    return response


def _run_report_generation(generation_id: int):
    """BackgroundTasks에서 실행되는 보고서 생성 함수"""
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        service = ReportService(db)
        service.generate_report_async(generation_id)
    finally:
        db.close()


@router.post("/generate", status_code=202)
def generate_report(
    request_data: ReportGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    보고서 생성 요청

    **필수 필드**:
    - **report_type**: 보고서 유형 (STANDARD, CUSTOM)
    - **title**: 보고서 제목
    - **period_type**: 기간 유형 (7d, 30d, 90d, 1y)

    **선택 필드**:
    - **template_id**: 사용자 정의 템플릿 ID (CUSTOM일 경우)
    - **severity_filter**: 심각도 필터

    PRD Reference: PRD_Report_System.md Section 6

    Note: 보고서 생성은 BackgroundTasks로 비동기 실행됩니다.
    """
    # Calculate date range from period_type
    start_date, end_date = _calculate_date_range(request_data.period_type.value)

    generation = ReportGeneration(
        report_type=request_data.report_type.value,
        template_id=request_data.template_id,
        title=request_data.title,
        period_type=request_data.period_type.value,
        start_date=start_date,
        end_date=end_date,
        severity_filter=request_data.severity_filter,
        status="PENDING",
    )

    db.add(generation)
    db.commit()
    db.refresh(generation)

    # Start background PDF generation
    background_tasks.add_task(_run_report_generation, generation.id)

    return ApiResponse(
        success=True,
        message="Report generation requested successfully",
        data=_generation_to_response(generation)
    )


@router.get("/generations")
def get_generations(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    status: Optional[str] = Query(None, description="상태 필터 (PENDING, GENERATING, COMPLETED, FAILED)"),
    db: Session = Depends(get_db)
):
    """
    보고서 생성 이력 목록 조회

    **파라미터**:
    - **page**: 페이지 번호 (default: 1)
    - **limit**: 페이지당 항목 수 (default: 20, max: 100)
    - **status**: 상태 필터 (optional)

    PRD Reference: PRD_Report_System.md Section 6
    """
    query = db.query(ReportGeneration)

    # Status filter
    if status:
        query = query.filter(ReportGeneration.status == status)

    # 정렬 및 페이지네이션
    query = query.order_by(ReportGeneration.created_at.desc())
    offset = (page - 1) * limit
    generations = query.offset(offset).limit(limit).all()

    return ApiResponse(
        success=True,
        message="Report generations retrieved successfully",
        data=[_generation_to_response(g) for g in generations]
    )


@router.get("/generations/{generation_id}")
def get_generation(
    generation_id: int,
    db: Session = Depends(get_db)
):
    """
    보고서 생성 이력 상세 조회

    **파라미터**:
    - **generation_id**: 생성 이력 ID

    PRD Reference: PRD_Report_System.md Section 6
    """
    generation = db.query(ReportGeneration).filter(ReportGeneration.id == generation_id).first()

    if not generation:
        raise HTTPException(status_code=404, detail="Report generation not found")

    return ApiResponse(
        success=True,
        message="Report generation retrieved successfully",
        data=_generation_to_response(generation)
    )


@router.get("/generations/{generation_id}/download")
def download_report(
    generation_id: int,
    db: Session = Depends(get_db)
):
    """
    보고서 다운로드

    **파라미터**:
    - **generation_id**: 생성 이력 ID

    **응답**:
    - COMPLETED 상태가 아닌 경우 400 에러
    - 존재하지 않는 ID의 경우 404 에러

    PRD Reference: PRD_Report_System.md Section 6
    """
    generation = db.query(ReportGeneration).filter(ReportGeneration.id == generation_id).first()

    if not generation:
        raise HTTPException(status_code=404, detail="Report generation not found")

    if generation.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="Report is not COMPLETED yet")

    if not generation.pdf_file_path:
        raise HTTPException(status_code=404, detail="PDF file not found")

    if not os.path.exists(generation.pdf_file_path):
        raise HTTPException(status_code=404, detail="PDF file not found on disk")

    return FileResponse(
        path=generation.pdf_file_path,
        filename=f"{generation.title}.pdf",
        media_type="application/pdf"
    )


@router.get("/generations/{generation_id}/preview")
def preview_report(
    generation_id: int,
    db: Session = Depends(get_db)
):
    """
    보고서 미리보기

    **파라미터**:
    - **generation_id**: 생성 이력 ID

    **응답**:
    - COMPLETED 상태가 아닌 경우 400 에러
    - 존재하지 않는 ID의 경우 404 에러

    PRD Reference: PRD_Report_System.md Section 6
    """
    generation = db.query(ReportGeneration).filter(ReportGeneration.id == generation_id).first()

    if not generation:
        raise HTTPException(status_code=404, detail="Report generation not found")

    if generation.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="Report is not COMPLETED yet")

    # Get structured preview data with charts and grids
    service = ReportService(db)
    # Calculate days from period_type
    period_days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
    days = period_days.get(generation.period_type, 7)
    structured_data = service.get_structured_preview_data(days)

    return ApiResponse(
        success=True,
        message="Report preview retrieved successfully",
        data={
            "id": generation.id,
            "title": generation.title,
            "report_type": generation.report_type,
            "period_type": generation.period_type,
            "start_date": generation.start_date,
            "end_date": generation.end_date,
            "sections": structured_data["sections"],
        }
    )


@router.get("/generations/{generation_id}/preview-page")
def preview_page_redirect(generation_id: int, db: Session = Depends(get_db)):
    """
    보고서 미리보기 (HTML 페이지로 이동)

    Swagger에서 실행하면 브라우저의 보고서 미리보기 페이지로 리다이렉트됩니다.
    차트, 그리드, 요약 카드를 시각적으로 확인할 수 있습니다.

    **파라미터**:
    - **generation_id**: 생성 이력 ID
    """
    generation = db.query(ReportGeneration).filter(ReportGeneration.id == generation_id).first()

    if not generation:
        raise HTTPException(status_code=404, detail="Report generation not found")

    return RedirectResponse(url=f"/reports/preview/{generation_id}")
