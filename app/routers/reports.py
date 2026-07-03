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
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Request
from fastapi.responses import FileResponse, RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from urllib.parse import quote
import os

from app.dependencies import get_db
from app.routers.auth import get_current_account_user, require_perm_optional
from app.models.user import AccountUser
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

# v5.1 FR-SV-02 (PRD_GOP_Server_RBAC_Enforcement):
# Router 레벨 의존성으로 모든 reports endpoint에 인증 강제 (이전 무인증 노출 LIVE 위험 차단).
# - 12 endpoint(템플릿 CRUD/components/generate/generations/download/preview)이 토큰 없이도 PII 집계 노출 가능했음.
# - get_current_account_user는 jti 블랙리스트도 검사 → 로그아웃/강등 즉시 차단.
# - require_perm(reports, view/edit/delete) 도메인별 부착은 v5.2 권고 (FR-SV-04 비계정 라우터 적용 단계).
router = APIRouter(dependencies=[Depends(get_current_account_user)])


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

@router.get("/components",
            dependencies=[Depends(require_perm_optional("reports", "view"))])
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
# Report Engine Status (Busy / Ready)
# ==============================================================================

@router.get("/status",
            dependencies=[Depends(require_perm_optional("reports", "view"))])
def get_report_engine_status(db: Session = Depends(get_db)):
    """
    보고서 엔진 Busy/Ready 상태 (read-only)

    PRD: PRD_Report_Master_Redesign — 정형 전체는 Chromium 렌더가 무거워 비동기 생성된다.
    클라이언트는 generation id 없이도 이 엔드포인트를 polling 하여 엔진이 작업 중인지 확인할 수 있다.

    **응답 data**:
    - **busy**: 진행 중(PENDING/GENERATING) 작업이 하나라도 있으면 true
    - **ready**: busy 의 반대 (새 생성 즉시 처리 가능)
    - **in_progress_count / in_progress**: 진행 중 작업 목록
    - **last_completed**: 가장 최근 완료 보고서(다운로드 URL 포함) — 없으면 null
    """
    busy_statuses = ("PENDING", "GENERATING")
    in_progress = (
        db.query(ReportGeneration)
        .filter(ReportGeneration.status.in_(busy_statuses))
        .order_by(ReportGeneration.created_at.asc())
        .all()
    )
    last = (
        db.query(ReportGeneration)
        .filter(ReportGeneration.status == "COMPLETED")
        .order_by(ReportGeneration.completed_at.desc())
        .first()
    )
    busy = len(in_progress) > 0

    return ApiResponse(
        success=True,
        message="Report engine status retrieved successfully",
        data={
            "busy": busy,
            "ready": not busy,
            "in_progress_count": len(in_progress),
            "in_progress": [
                {
                    "id": g.id,
                    "title": g.title,
                    "status": g.status,
                    "created_at": g.created_at,
                }
                for g in in_progress
            ],
            "last_completed": (
                {
                    "id": last.id,
                    "title": last.title,
                    "completed_at": last.completed_at,
                    "pdf_download_url": f"/api/reports/generations/{last.id}/download",
                }
                if last and last.pdf_file_path
                else None
            ),
        },
    )


# ==============================================================================
# Report Templates Endpoints
# ==============================================================================

@router.get("/templates",
            dependencies=[Depends(require_perm_optional("reports", "view"))])
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


@router.post("/templates", status_code=201,
             dependencies=[Depends(require_perm_optional("reports", "edit"))])
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


@router.get("/templates/{template_id}",
            dependencies=[Depends(require_perm_optional("reports", "view"))])
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


@router.patch("/templates/{template_id}",
              dependencies=[Depends(require_perm_optional("reports", "edit"))])
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


@router.delete("/templates/{template_id}",
               dependencies=[Depends(require_perm_optional("reports", "delete"))])
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
        message=f"Report template {template_id} deleted successfully",
        data=None
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
    # v5.4 P0-1: /reports/preview → /api/reports/preview 이동 (무인증 PII 봉합, router 인증 부착)
    response["preview_html_url"] = f"/api/reports/preview/{generation.id}"

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


@router.post("/generate", status_code=202,
             dependencies=[Depends(require_perm_optional("reports", "edit"))])
def generate_report(
    request_data: ReportGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: AccountUser = Depends(get_current_account_user),
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

    v5.4 P1-2: generator_id/name/department 스냅샷 기록 (작성자 감사 이력).
    """
    # v5.4 P0-5: template_id 존재 검증 — psycopg2 FK violation raw 500 노출 차단.
    if request_data.template_id is not None:
        template = db.query(ReportTemplate).filter(
            ReportTemplate.id == request_data.template_id
        ).first()
        if template is None:
            raise HTTPException(
                status_code=404,
                detail=f"Report template not found: template_id={request_data.template_id}",
            )

    # Calculate date range from period_type
    start_date, end_date = _calculate_date_range(request_data.period_type.value)

    generation = ReportGeneration(
        report_type=request_data.report_type.value,
        template_id=request_data.template_id,
        title=request_data.title,
        period_type=request_data.period_type.value,
        start_date=start_date,
        end_date=end_date,
        # v5.4 P1-2: 작성자 스냅샷 기록 (미인증이면 None — v5.5 required 전환 시 항상 채워짐)
        generator_id=current_user.id if current_user else None,
        generator_name=current_user.name if current_user else None,
        generator_department=current_user.department if current_user else None,
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


@router.get("/generations",
            dependencies=[Depends(require_perm_optional("reports", "view"))])
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


@router.get("/generations/{generation_id}",
            dependencies=[Depends(require_perm_optional("reports", "view"))])
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


@router.delete("/generations/{generation_id}",
               dependencies=[Depends(require_perm_optional("reports", "delete"))])
def delete_generation(
    generation_id: int,
    db: Session = Depends(get_db),
    current_user: AccountUser = Depends(get_current_account_user),
):
    """
    보고서 생성 이력 삭제 — v5.4 P1-4 (클라 REQ #3 해결).

    - DB row 삭제
    - pdf_file_path에 파일 있으면 함께 삭제 (best-effort)
    - v5.5 인가 강화 시 `require_perm("reports.delete")` 추가 예정

    **응답**: 성공 시 { success: true, message } (204 대신 200 + 엔벨로프로 일관)
    """
    generation = db.query(ReportGeneration).filter(ReportGeneration.id == generation_id).first()

    if not generation:
        raise HTTPException(status_code=404, detail="Report generation not found")

    # best-effort 파일 삭제 (파일 삭제 실패해도 row는 지운다)
    if generation.pdf_file_path and os.path.exists(generation.pdf_file_path):
        try:
            os.remove(generation.pdf_file_path)
        except OSError:
            pass  # 파일 삭제 실패는 무시 (row 삭제는 계속)

    db.delete(generation)
    db.commit()

    return ApiResponse(
        success=True,
        message=f"Report generation {generation_id} deleted successfully",
        data=None,
    )


@router.get("/generations/{generation_id}/download",
            dependencies=[Depends(require_perm_optional("reports", "view"))])
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

    encoded_name = quote(f"{generation.title}.pdf")
    headers = {
        "Content-Disposition": f'attachment; filename="report_{generation_id}.pdf"; filename*=UTF-8\'\'{encoded_name}'
    }
    return FileResponse(
        path=generation.pdf_file_path,
        headers=headers,
        media_type="application/pdf"
    )


@router.get("/generations/{generation_id}/preview",
            dependencies=[Depends(require_perm_optional("reports", "view"))])
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

    # CUSTOM 타입이면 템플릿 컴포넌트 조회하여 필터링
    enabled_components = None
    if generation.report_type == "CUSTOM" and generation.template_id:
        template = db.query(ReportTemplate).filter(
            ReportTemplate.id == generation.template_id
        ).first()
        if template and template.components:
            enabled_components = [
                c["id"] for c in template.components
                if c.get("enabled", True)
            ]

    # Get structured preview data with charts and grids
    service = ReportService(db)
    # Calculate days from period_type
    period_days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
    days = period_days.get(generation.period_type, 7)
    structured_data = service.get_structured_preview_data(days, enabled_components)

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


@router.get("/generations/{generation_id}/preview-page",
            dependencies=[Depends(require_perm_optional("reports", "view"))])
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

    return RedirectResponse(url=f"/api/reports/preview/{generation_id}")


@router.get("/preview/{generation_id}", response_class=HTMLResponse,
            dependencies=[Depends(require_perm_optional("reports", "view"))])
def report_preview_page(
    request: Request,
    generation_id: int,
    db: Session = Depends(get_db),
    current_user: AccountUser = Depends(get_current_account_user),
):
    """
    보고서 미리보기 페이지 (HTML)

    v5.4 P0-1: 이전 `/reports/preview/{id}` (main.py, 무인증) → 본 라우터 이관.
    - 라우터 레벨 `get_current_account_user` 로 Bearer 필수 (401 차단).
    - jti 블랙리스트 검사 자동 (로그아웃/강등 토큰 차단).
    - v5.5 인가 강화 시 `require_perm("reports.view")` 추가 예정.

    PRD Reference: PRD_Report_System.md Section 10
    """
    generation = db.query(ReportGeneration).filter(ReportGeneration.id == generation_id).first()

    if not generation:
        raise HTTPException(status_code=404, detail="Report generation not found")

    # PRD_Report_Master_Redesign: 프리뷰 == PDF 동일 HTML (정형=전체, 비정형=template 컴포넌트 필터)
    # 브라우저 기본은 compact(검토용), ?mode=full 로 전체 페이지네이션 확인 가능.
    from app.services.report_master_builder import build_master_data, build_report_meta
    from app.services.report_html_renderer import render_report_html

    service = ReportService(db)
    enabled = service.get_enabled_components(generation)
    enabled_set = set(enabled) if enabled is not None else None
    meta = build_report_meta(generation)
    # v5.4 P1-3: 프리뷰도 severity_filter 반영 (PDF와 동일 HTML 유지)
    data = build_master_data(
        db, generation.start_date, generation.end_date, meta, enabled_set,
        severity_filter=generation.severity_filter,
    )
    mode = "full" if request.query_params.get("mode") == "full" else "compact"
    return HTMLResponse(render_report_html(data, mode=mode))
