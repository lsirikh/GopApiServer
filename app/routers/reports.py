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

v6.0 P8 VeryComplex — 라우터 async 전환:
- 시그니처 async def 유지
- 응답 스키마 완전 유지 (v5.4 P0-1/P0-5/P1-2/P1-3/P1-4 유지)
- Dependency: get_async_db / get_current_account_user_async / require_perm_optional_async
- Query: select() + await db.execute(...).scalars() 패턴

v6.0 P8-b (SessionLocal 완전 제거):
- 라우터/백그라운드 전체를 AsyncSession 으로 통일 — sync SessionLocal 3곳 제거.
- 백그라운드 생성: AsyncSessionLocal + ReportServiceAsync + build_master_data_async
  + render_report_html_async + asyncio.to_thread(html_to_pdf_bytes) 조합으로
  이벤트루프 논블로킹 실행.
- Preview (JSON) / Preview page (HTML): 요청 AsyncSession 위에서 ReportServiceAsync
  및 async 마스터 빌더/렌더러 사용.
"""
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Request
from fastapi.responses import FileResponse, RedirectResponse, HTMLResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, timedelta
from urllib.parse import quote
import os

from app.dependencies import get_async_db
from app.routers.auth import get_current_account_user_async, require_perm_optional_async
from app.models.user import AccountUser
from app.services.report_service import ReportServiceAsync
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
# - get_current_account_user_async 는 jti 블랙리스트도 검사 → 로그아웃/강등 즉시 차단.
# - require_perm_optional_async(reports, view/edit/delete) 도메인별 부착은 v5.2 완료 (FR-SV-04).
# v6.0 P8: get_current_account_user → get_current_account_user_async 로 교체 (라우터 async 전환).
router = APIRouter(dependencies=[Depends(get_current_account_user_async)])


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
            dependencies=[Depends(require_perm_optional_async("reports", "view"))])
async def get_components():
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
            dependencies=[Depends(require_perm_optional_async("reports", "view"))])
async def get_report_engine_status(db: AsyncSession = Depends(get_async_db)):
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
        await db.execute(
            select(ReportGeneration)
            .where(ReportGeneration.status.in_(busy_statuses))
            .order_by(ReportGeneration.created_at.asc())
        )
    ).scalars().all()
    last = (
        await db.execute(
            select(ReportGeneration)
            .where(ReportGeneration.status == "COMPLETED")
            .order_by(ReportGeneration.completed_at.desc())
        )
    ).scalars().first()
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
            dependencies=[Depends(require_perm_optional_async("reports", "view"))])
async def get_templates(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    보고서 템플릿 목록 조회

    **파라미터**:
    - **page**: 페이지 번호 (default: 1)
    - **limit**: 페이지당 항목 수 (default: 20, max: 100)

    PRD Reference: PRD_Report_System.md Section 6
    """
    offset = (page - 1) * limit
    templates = (
        await db.execute(
            select(ReportTemplate)
            .order_by(ReportTemplate.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
    ).scalars().all()

    return ApiResponse(
        success=True,
        message="Report templates retrieved successfully",
        data=[_template_to_list_response(t) for t in templates]
    )


@router.post("/templates", status_code=201,
             dependencies=[Depends(require_perm_optional_async("reports", "edit"))])
async def create_template(
    template_data: ReportTemplateCreate,
    db: AsyncSession = Depends(get_async_db)
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
    await db.commit()
    await db.refresh(template)

    return ApiResponse(
        success=True,
        message="Report template created successfully",
        data=_template_to_response(template)
    )


@router.get("/templates/{template_id}",
            dependencies=[Depends(require_perm_optional_async("reports", "view"))])
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """
    보고서 템플릿 상세 조회

    **파라미터**:
    - **template_id**: 템플릿 ID

    PRD Reference: PRD_Report_System.md Section 6
    """
    template = (
        await db.execute(
            select(ReportTemplate).where(ReportTemplate.id == template_id)
        )
    ).scalars().first()

    if not template:
        raise HTTPException(status_code=404, detail="Report template not found")

    return ApiResponse(
        success=True,
        message="Report template retrieved successfully",
        data=_template_to_response(template)
    )


@router.patch("/templates/{template_id}",
              dependencies=[Depends(require_perm_optional_async("reports", "edit"))])
async def update_template(
    template_id: int,
    template_data: ReportTemplateUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """
    보고서 템플릿 수정 (부분 업데이트)

    **파라미터**:
    - **template_id**: 템플릿 ID
    - **body**: 수정할 필드만 포함

    PRD Reference: PRD_Report_System.md Section 6
    """
    template = (
        await db.execute(
            select(ReportTemplate).where(ReportTemplate.id == template_id)
        )
    ).scalars().first()

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

    await db.commit()
    await db.refresh(template)

    return ApiResponse(
        success=True,
        message="Report template updated successfully",
        data=_template_to_response(template)
    )


@router.delete("/templates/{template_id}",
               dependencies=[Depends(require_perm_optional_async("reports", "delete"))])
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """
    보고서 템플릿 삭제

    **파라미터**:
    - **template_id**: 템플릿 ID

    PRD Reference: PRD_Report_System.md Section 6
    """
    template = (
        await db.execute(
            select(ReportTemplate).where(ReportTemplate.id == template_id)
        )
    ).scalars().first()

    if not template:
        raise HTTPException(status_code=404, detail="Report template not found")

    await db.delete(template)
    await db.commit()

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


# v6.0 후속: 진행 중 리포트 생성 태스크 추적 — cancel endpoint용.
# key = generation_id, value = asyncio.Task
_active_generation_tasks: dict[int, asyncio.Task] = {}


async def _run_report_generation(generation_id: int) -> None:
    """BackgroundTasks에서 실행되는 보고서 생성 함수 (async).

    v6.0 P8-b: sync SessionLocal 제거 — 전 파이프라인 async 화.
    - AsyncSessionLocal 로 별도 세션 개시 (요청 세션 라이프사이클 밖에서 실행).
    - ReportServiceAsync.get_enabled_components → build_master_data_async
      → render_report_html_async → asyncio.to_thread(html_to_pdf_bytes) 체인.
    - Chromium PDF 렌더링(Playwright sync API)은 여전히 blocking 이므로
      asyncio.to_thread 로 오프로드해 이벤트루프 보호.

    FastAPI BackgroundTasks 는 async 함수 자동 감지 → await 로 실행.

    v6.0 후속: 취소 지원 — current_task를 dict에 등록해 cancel endpoint에서 참조.
    CancelledError 발생 시 status=CANCELLED로 마킹 후 propagate.
    """
    from app.database import AsyncSessionLocal
    from app.services.report_master_builder import build_master_data_async, build_report_meta
    from app.services.report_html_renderer import render_report_html_async
    from app.utils.html_to_pdf import html_to_pdf_bytes

    # v6.0 후속: 현재 태스크를 dict에 등록 (cancel endpoint용)
    current = asyncio.current_task()
    if current is not None:
        _active_generation_tasks[generation_id] = current

    async with AsyncSessionLocal() as db:
        generation = (
            await db.execute(
                select(ReportGeneration).where(ReportGeneration.id == generation_id)
            )
        ).scalars().first()
        if not generation:
            _active_generation_tasks.pop(generation_id, None)
            return

        # 이미 CANCELLED로 마킹된 상태면 즉시 종료 (레이스 조건)
        if generation.status == "CANCELLED":
            _active_generation_tasks.pop(generation_id, None)
            return

        # v6.0 후속 Quick Win Q2: 파일 경로를 로컬 변수로 미리 보관 —
        # generation.pdf_file_path에 반영되기 전 취소돼도 파일 삭제 가능.
        _pending_pdf_path: str | None = None
        try:
            generation.status = "GENERATING"
            await db.commit()

            service = ReportServiceAsync(db)
            enabled = await service.get_enabled_components(generation)
            enabled_set = set(enabled) if enabled is not None else None
            kind = "비정형" if generation.report_type == "CUSTOM" else "정형"
            meta = build_report_meta(generation)

            # v6.0 Phase 3 hotfix: asyncpg는 tz-aware/naive datetime 혼용 거부.
            # start_date/end_date는 timestamptz(+09:00), events.created_at은 naive → tzinfo 제거로 정합.
            _start_naive = generation.start_date.replace(tzinfo=None) if generation.start_date.tzinfo else generation.start_date
            _end_naive = generation.end_date.replace(tzinfo=None) if generation.end_date.tzinfo else generation.end_date
            data = await build_master_data_async(
                db, _start_naive, _end_naive, meta, enabled_set,
                severity_filter=generation.severity_filter,
            )
            html = await render_report_html_async(data, mode="full")
            pdf_bytes = await asyncio.to_thread(html_to_pdf_bytes, html)

            reports_dir = os.path.join(os.getcwd(), "reports")
            os.makedirs(reports_dir, exist_ok=True)
            filename = f"report_{generation.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            file_path = os.path.join(reports_dir, filename)
            _pending_pdf_path = file_path  # 파일 쓰기 도중 취소돼도 삭제 대상 확보
            with open(file_path, "wb") as f:
                f.write(pdf_bytes)

            generation.status = "COMPLETED"
            generation.pdf_file_path = file_path
            generation.pdf_file_size = len(pdf_bytes)
            generation.completed_at = datetime.now()
            generation.summary_data = {
                "section_count": len(data["sections"]),
                "report_kind": kind,
            }
            await db.commit()

        except asyncio.CancelledError:
            # v6.0 후속 Quick Win Q2: 부분 생성된 PDF 파일 best-effort 삭제.
            # generation.pdf_file_path(커밋된 경로) 및 _pending_pdf_path(쓰기 도중 경로) 모두 정리.
            for _p in (getattr(generation, "pdf_file_path", None), _pending_pdf_path):
                if _p and os.path.exists(_p):
                    try:
                        os.remove(_p)
                    except OSError:
                        pass  # 파일 삭제 실패는 무시 (best-effort)
            try:
                generation.status = "CANCELLED"
                generation.error_message = "Cancelled by user"
                generation.completed_at = datetime.now()
                await db.commit()
            except Exception:
                pass  # 커밋 실패해도 취소 자체는 진행
            raise
        except Exception as e:
            generation.status = "FAILED"
            generation.error_message = str(e)
            await db.commit()
        finally:
            # 태스크 종료 시 dict에서 제거 (성공/실패/취소 모두)
            _active_generation_tasks.pop(generation_id, None)


@router.post("/generate", status_code=202,
             dependencies=[Depends(require_perm_optional_async("reports", "edit"))])
async def generate_report(
    request_data: ReportGenerateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db),
    current_user: AccountUser = Depends(get_current_account_user_async),
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
        template = (
            await db.execute(
                select(ReportTemplate).where(ReportTemplate.id == request_data.template_id)
            )
        ).scalars().first()
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
    await db.commit()
    await db.refresh(generation)

    # Start background PDF generation (sync 서비스 — v6.1 이월)
    background_tasks.add_task(_run_report_generation, generation.id)

    return ApiResponse(
        success=True,
        message="Report generation requested successfully",
        data=_generation_to_response(generation)
    )


@router.get("/generations",
            dependencies=[Depends(require_perm_optional_async("reports", "view"))])
async def get_generations(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    status: Optional[str] = Query(None, description="상태 필터 (PENDING, GENERATING, COMPLETED, FAILED)"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    보고서 생성 이력 목록 조회

    **파라미터**:
    - **page**: 페이지 번호 (default: 1)
    - **limit**: 페이지당 항목 수 (default: 20, max: 100)
    - **status**: 상태 필터 (optional)

    PRD Reference: PRD_Report_System.md Section 6
    """
    stmt = select(ReportGeneration)

    # Status filter
    if status:
        stmt = stmt.where(ReportGeneration.status == status)

    # 정렬 및 페이지네이션
    offset = (page - 1) * limit
    generations = (
        await db.execute(
            stmt.order_by(ReportGeneration.created_at.desc()).offset(offset).limit(limit)
        )
    ).scalars().all()

    return ApiResponse(
        success=True,
        message="Report generations retrieved successfully",
        data=[_generation_to_response(g) for g in generations]
    )


@router.get("/generations/{generation_id}",
            dependencies=[Depends(require_perm_optional_async("reports", "view"))])
async def get_generation(
    generation_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """
    보고서 생성 이력 상세 조회

    **파라미터**:
    - **generation_id**: 생성 이력 ID

    PRD Reference: PRD_Report_System.md Section 6
    """
    generation = (
        await db.execute(
            select(ReportGeneration).where(ReportGeneration.id == generation_id)
        )
    ).scalars().first()

    if not generation:
        raise HTTPException(status_code=404, detail="Report generation not found")

    return ApiResponse(
        success=True,
        message="Report generation retrieved successfully",
        data=_generation_to_response(generation)
    )


@router.delete("/generations/{generation_id}",
               dependencies=[Depends(require_perm_optional_async("reports", "delete"))])
async def delete_generation(
    generation_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: AccountUser = Depends(get_current_account_user_async),
):
    """
    보고서 생성 이력 삭제 — v5.4 P1-4 (클라 REQ #3 해결).

    - DB row 삭제
    - pdf_file_path에 파일 있으면 함께 삭제 (best-effort)
    - v5.5 인가 강화 시 `require_perm("reports.delete")` 추가 예정

    **응답**: 성공 시 { success: true, message } (204 대신 200 + 엔벨로프로 일관)
    """
    generation = (
        await db.execute(
            select(ReportGeneration).where(ReportGeneration.id == generation_id)
        )
    ).scalars().first()

    if not generation:
        raise HTTPException(status_code=404, detail="Report generation not found")

    # best-effort 파일 삭제 (파일 삭제 실패해도 row는 지운다)
    if generation.pdf_file_path and os.path.exists(generation.pdf_file_path):
        try:
            os.remove(generation.pdf_file_path)
        except OSError:
            pass  # 파일 삭제 실패는 무시 (row 삭제는 계속)

    await db.delete(generation)
    await db.commit()

    return ApiResponse(
        success=True,
        message=f"Report generation {generation_id} deleted successfully",
        data=None,
    )


@router.post("/generations/{generation_id}/cancel",
             dependencies=[Depends(require_perm_optional_async("reports", "delete"))])
async def cancel_generation(
    generation_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: AccountUser = Depends(get_current_account_user_async),
):
    """
    보고서 생성 취소 — v6.0 후속 신설.

    - PENDING or GENERATING 상태만 취소 가능
    - COMPLETED/FAILED/CANCELLED는 400 (이미 종료)
    - 진행 중 asyncio.Task 참조를 dict에서 조회해 task.cancel() 호출
    - _run_report_generation의 CancelledError 핸들러가 status를 CANCELLED로 마킹
    - 권한: reports.delete (DELETE와 동급)

    **응답**: 성공 시 { success: true, message, data: {id, status} }
    **Error**:
    - 404: 리포트 이력 없음
    - 400: 이미 종료된 상태 (COMPLETED/FAILED/CANCELLED)
    """
    generation = (
        await db.execute(
            select(ReportGeneration).where(ReportGeneration.id == generation_id)
        )
    ).scalars().first()

    if not generation:
        raise HTTPException(status_code=404, detail="Report generation not found")

    if generation.status in ("COMPLETED", "FAILED", "CANCELLED"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel: generation is already {generation.status}",
        )

    # dict에서 태스크 참조 조회 → cancel 호출
    # _run_report_generation의 except asyncio.CancelledError 블록이 status=CANCELLED 마킹.
    # 태스크가 이미 종료됐거나 참조 없으면 DB 마킹만 수행 (레이스 조건 안전 커버).
    task = _active_generation_tasks.get(generation_id)
    task_cancelled = False
    if task is not None and not task.done():
        task.cancel()
        task_cancelled = True

    # 태스크가 없거나 이미 종료된 경우 직접 DB 마킹
    # (레이스: task 취소 후 CancelledError 핸들러가 커밋하기 전 응답할 수 있으므로
    #  안전하게 여기서도 마킹. 중복 커밋은 무해)
    if not task_cancelled:
        generation.status = "CANCELLED"
        generation.error_message = f"Cancelled by user {current_user.login_id}"
        generation.completed_at = datetime.now()
        await db.commit()

    return ApiResponse(
        success=True,
        message=f"Report generation {generation_id} cancellation requested",
        data={
            "id": generation.id,
            "status": "CANCELLED",
            "task_cancelled": task_cancelled,
        },
    )


@router.get("/generations/{generation_id}/download",
            dependencies=[Depends(require_perm_optional_async("reports", "view"))])
async def download_report(
    generation_id: int,
    db: AsyncSession = Depends(get_async_db)
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
    generation = (
        await db.execute(
            select(ReportGeneration).where(ReportGeneration.id == generation_id)
        )
    ).scalars().first()

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
            dependencies=[Depends(require_perm_optional_async("reports", "view"))])
async def preview_report(
    generation_id: int,
    db: AsyncSession = Depends(get_async_db)
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
    generation = (
        await db.execute(
            select(ReportGeneration).where(ReportGeneration.id == generation_id)
        )
    ).scalars().first()

    if not generation:
        raise HTTPException(status_code=404, detail="Report generation not found")

    if generation.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="Report is not COMPLETED yet")

    # CUSTOM 타입이면 템플릿 컴포넌트 조회하여 필터링
    enabled_components = None
    if generation.report_type == "CUSTOM" and generation.template_id:
        template = (
            await db.execute(
                select(ReportTemplate).where(ReportTemplate.id == generation.template_id)
            )
        ).scalars().first()
        if template and template.components:
            enabled_components = [
                c["id"] for c in template.components
                if c.get("enabled", True)
            ]

    # v6.0 P8-b: sync SessionLocal 제거 — 요청 AsyncSession 위에서 ReportServiceAsync 사용.
    service = ReportServiceAsync(db)
    # Calculate days from period_type
    period_days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
    days = period_days.get(generation.period_type, 7)
    structured_data = await service.get_structured_preview_data(days, enabled_components)

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
            dependencies=[Depends(require_perm_optional_async("reports", "view"))])
async def preview_page_redirect(generation_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    보고서 미리보기 (HTML 페이지로 이동)

    Swagger에서 실행하면 브라우저의 보고서 미리보기 페이지로 리다이렉트됩니다.
    차트, 그리드, 요약 카드를 시각적으로 확인할 수 있습니다.

    **파라미터**:
    - **generation_id**: 생성 이력 ID
    """
    generation = (
        await db.execute(
            select(ReportGeneration).where(ReportGeneration.id == generation_id)
        )
    ).scalars().first()

    if not generation:
        raise HTTPException(status_code=404, detail="Report generation not found")

    return RedirectResponse(url=f"/api/reports/preview/{generation_id}")


@router.get("/preview/{generation_id}", response_class=HTMLResponse,
            dependencies=[Depends(require_perm_optional_async("reports", "view"))])
async def report_preview_page(
    request: Request,
    generation_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: AccountUser = Depends(get_current_account_user_async),
):
    """
    보고서 미리보기 페이지 (HTML)

    v5.4 P0-1: 이전 `/reports/preview/{id}` (main.py, 무인증) → 본 라우터 이관.
    - 라우터 레벨 `get_current_account_user_async` 로 Bearer 필수 (401 차단).
    - jti 블랙리스트 검사 자동 (로그아웃/강등 토큰 차단).
    - v5.5 인가 강화 시 `require_perm("reports.view")` 추가 예정.

    PRD Reference: PRD_Report_System.md Section 10
    """
    generation = (
        await db.execute(
            select(ReportGeneration).where(ReportGeneration.id == generation_id)
        )
    ).scalars().first()

    if not generation:
        raise HTTPException(status_code=404, detail="Report generation not found")

    # PRD_Report_Master_Redesign: 프리뷰 == PDF 동일 HTML (정형=전체, 비정형=template 컴포넌트 필터)
    # 브라우저 기본은 compact(검토용), ?mode=full 로 전체 페이지네이션 확인 가능.
    # v6.0 P8-b: sync SessionLocal 제거 — 요청 AsyncSession + async 마스터 빌더/렌더러.
    from app.services.report_master_builder import build_master_data_async, build_report_meta
    from app.services.report_html_renderer import render_report_html_async

    service = ReportServiceAsync(db)
    enabled = await service.get_enabled_components(generation)
    enabled_set = set(enabled) if enabled is not None else None
    meta = build_report_meta(generation)
    # v5.4 P1-3: 프리뷰도 severity_filter 반영 (PDF와 동일 HTML 유지)
    # v6.0 Phase 3 hotfix: tz-aware → naive 정합 (asyncpg 엄격 검사)
    _start_naive = generation.start_date.replace(tzinfo=None) if generation.start_date.tzinfo else generation.start_date
    _end_naive = generation.end_date.replace(tzinfo=None) if generation.end_date.tzinfo else generation.end_date
    data = await build_master_data_async(
        db, _start_naive, _end_naive, meta, enabled_set,
        severity_filter=generation.severity_filter,
    )

    mode = "full" if request.query_params.get("mode") == "full" else "compact"
    html = await render_report_html_async(data, mode=mode)
    return HTMLResponse(html)
