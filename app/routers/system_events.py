"""
System Event API Router
Based on PRD_System_Event.md Section 3

Endpoints:
- GET /api/system-events - 목록 조회 (필터링, 페이지네이션)
- GET /api/system-events/{id} - 단건 조회
- POST /api/system-events - 생성
- PATCH /api/system-events/{id} - 수정
- DELETE /api/system-events/{id} - 삭제
- POST /api/system-events/{id}/acknowledge - 확인 처리
- GET /api/system-events/summary - 요약 통계
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from app.config import settings
from app.dependencies import get_async_db
from app.models.system_event import SystemEvent
from app.models.server import Server
from app.schemas.system_event import (
    SystemEventCreate,
    SystemEventUpdate,
    SystemEventResponse,
    SystemEventAcknowledge,
    SystemEventSummary
)
from app.schemas.common import ApiResponse
from app.utils.enums import EnumSystemEventType, EnumSystemEventSeverity
from app.routers.auth import require_perm_optional_async

# AUTH-01 (2026-07-09): system-events 쓰기 4종(POST/PATCH/DELETE/acknowledge)이 무인증 노출이던 것 차단.
# 서버 모니터링 도메인이므로 servers 모듈 매트릭스로 게이트. 형제 도메인(servers/cameras)과 동일한
# require_perm_optional 패턴 — AUTH_MODE=token 에서 집행, public 에서 휴면(현 동작 보존, 무파손).
# GET(조회)은 관측 목적상 optional 인증 유지(별도 변경 없음).

router = APIRouter()


# ==============================================================================
# Helper Functions
# ==============================================================================

def _system_event_to_response(event: SystemEvent) -> dict:
    """SystemEvent 모델을 응답 딕셔너리로 변환"""
    return {
        "id": event.id,
        "server_id": event.server_id,
        "server_description": event.server_description,
        "type_event": event.type_event.value if event.type_event else None,
        "severity": event.severity.value if event.severity else None,
        "title": event.title,
        "message": event.message,
        "detail": event.detail,
        "source": event.source,  # PRD 3.2
        "is_acknowledged": event.is_acknowledged,
        "acknowledged_by": event.acknowledged_by,
        "acknowledged_at": event.acknowledged_at,
        "created_at": event.created_at,
        "updated_at": event.updated_at  # PRD 3.2
    }


# ==============================================================================
# GET Endpoints
# ==============================================================================

@router.get("/summary")
async def get_system_events_summary(db: AsyncSession = Depends(get_async_db)):
    """
    시스템 이벤트 요약 통계 조회

    **Response**:
    - **total_count**: 전체 이벤트 수
    - **unacknowledged_count**: 미확인 이벤트 수
    - **by_severity**: 심각도별 이벤트 수
    - **by_type**: 유형별 이벤트 수
    - **recent_critical**: 최근 CRITICAL 이벤트 목록

    PRD Reference: PRD_System_Event.md Section 3
    """
    # 전체 이벤트 수
    total_count = (await db.execute(select(func.count(SystemEvent.id)))).scalar()

    # 미확인 이벤트 수
    unacknowledged_count = (await db.execute(
        select(func.count(SystemEvent.id)).where(SystemEvent.is_acknowledged == False)
    )).scalar()

    # 심각도별 이벤트 수
    by_severity = {}
    severity_counts = (await db.execute(
        select(SystemEvent.severity, func.count(SystemEvent.id)).group_by(SystemEvent.severity)
    )).all()
    for sev, count in severity_counts:
        by_severity[sev.value] = count

    # 유형별 이벤트 수
    by_type = {}
    type_counts = (await db.execute(
        select(SystemEvent.type_event, func.count(SystemEvent.id)).group_by(SystemEvent.type_event)
    )).all()
    for type_event, count in type_counts:
        by_type[type_event.value] = count

    # 최근 CRITICAL 이벤트 (최대 5개)
    critical_events = (await db.execute(
        select(SystemEvent)
        .where(SystemEvent.severity == EnumSystemEventSeverity.CRITICAL)
        .order_by(SystemEvent.created_at.desc())
        .limit(5)
    )).scalars().all()
    recent_critical = [_system_event_to_response(e) for e in critical_events]

    return ApiResponse(
        success=True,
        message="System event summary retrieved successfully",
        data={
            "total_count": total_count,
            "unacknowledged_count": unacknowledged_count,
            "by_severity": by_severity,
            "by_type": by_type,
            "recent_critical": recent_critical
        }
    )


@router.get("")
async def get_system_events(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    server_id: Optional[int] = Query(None, description="서버 ID 필터"),
    type_event: Optional[str] = Query(None, description="이벤트 유형 필터"),
    severity: Optional[str] = Query(None, description="심각도 필터"),
    is_acknowledged: Optional[bool] = Query(None, description="확인 여부 필터"),
    start_date: Optional[datetime] = Query(None, description="시작 일시"),
    end_date: Optional[datetime] = Query(None, description="종료 일시"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    시스템 이벤트 목록 조회

    **파라미터**:
    - **page**: 페이지 번호 (default: 1)
    - **limit**: 페이지당 항목 수 (default: 20, max: 100)
    - **server_id**: 서버 ID 필터
    - **type_event**: 이벤트 유형 필터
    - **severity**: 심각도 필터 (INFO, WARNING, ERROR, CRITICAL)
    - **is_acknowledged**: 확인 여부 필터
    - **start_date**: 시작 일시 필터
    - **end_date**: 종료 일시 필터

    PRD Reference: PRD_System_Event.md Section 3
    """
    stmt = select(SystemEvent)

    # 필터 적용
    if server_id is not None:
        stmt = stmt.where(SystemEvent.server_id == server_id)

    if type_event:
        try:
            type_enum = EnumSystemEventType(type_event)
            stmt = stmt.where(SystemEvent.type_event == type_enum)
        except ValueError:
            pass  # 유효하지 않은 값은 무시

    if severity:
        try:
            severity_enum = EnumSystemEventSeverity(severity)
            stmt = stmt.where(SystemEvent.severity == severity_enum)
        except ValueError:
            pass

    if is_acknowledged is not None:
        stmt = stmt.where(SystemEvent.is_acknowledged == is_acknowledged)

    if start_date:
        stmt = stmt.where(SystemEvent.created_at >= start_date)

    if end_date:
        stmt = stmt.where(SystemEvent.created_at <= end_date)

    # 정렬 및 페이지네이션
    stmt = stmt.order_by(SystemEvent.created_at.desc())
    offset = (page - 1) * limit
    stmt = stmt.offset(offset).limit(limit)
    events = (await db.execute(stmt)).scalars().all()

    return ApiResponse(
        success=True,
        message="System events retrieved successfully",
        data=[_system_event_to_response(e) for e in events]
    )


@router.get("/{event_id}")
async def get_system_event(event_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    시스템 이벤트 단건 조회

    **파라미터**:
    - **event_id**: 이벤트 ID

    PRD Reference: PRD_System_Event.md Section 3
    """
    event = (await db.execute(
        select(SystemEvent).where(SystemEvent.id == event_id)
    )).scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail=f"SystemEvent with id {event_id} not found")

    return ApiResponse(
        success=True,
        message="System event retrieved successfully",
        data=_system_event_to_response(event)
    )


# ==============================================================================
# POST Endpoints
# ==============================================================================

@router.post("", status_code=201,
             dependencies=[Depends(require_perm_optional_async("servers", "edit"))])
async def create_system_event(event_data: SystemEventCreate, db: AsyncSession = Depends(get_async_db)):
    """
    시스템 이벤트 생성

    **파라미터**:
    - **event_data**: 이벤트 생성 데이터

    PRD Reference: PRD_System_Event.md Section 3
    """
    # server_id 유효성 검사
    if event_data.server_id:
        server = (await db.execute(
            select(Server).where(Server.id == event_data.server_id)
        )).scalars().first()
        if not server:
            raise HTTPException(
                status_code=400,
                detail=f"Server with id {event_data.server_id} not found"
            )
        # server_description 자동 설정
        if not event_data.server_description:
            event_data.server_description = f"{server.name} ({server.ip_address})"

    # 이벤트 생성
    event = SystemEvent(
        server_id=event_data.server_id,
        server_description=event_data.server_description,
        type_event=event_data.type_event,
        severity=event_data.severity,
        title=event_data.title,
        message=event_data.message,
        detail=event_data.detail,
        source=event_data.source,  # PRD 3.2
        is_acknowledged=False
    )

    db.add(event)
    await db.commit()
    await db.refresh(event)

    return ApiResponse(
        success=True,
        message="System event created successfully",
        data=_system_event_to_response(event)
    )


@router.post("/{event_id}/acknowledge",
             dependencies=[Depends(require_perm_optional_async("servers", "control"))])
async def acknowledge_system_event(
    event_id: int,
    ack_data: SystemEventAcknowledge,
    db: AsyncSession = Depends(get_async_db)
):
    """
    시스템 이벤트 확인 처리

    **파라미터**:
    - **event_id**: 이벤트 ID
    - **ack_data**: 확인 처리 데이터 (acknowledged_by 필수)

    PRD Reference: PRD_System_Event.md Section 3
    """
    event = (await db.execute(
        select(SystemEvent).where(SystemEvent.id == event_id)
    )).scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail=f"SystemEvent with id {event_id} not found")

    # 이미 확인된 경우 400 반환
    if event.is_acknowledged:
        raise HTTPException(status_code=400, detail="Event is already acknowledged")

    # 확인 처리
    event.is_acknowledged = True
    event.acknowledged_by = ack_data.acknowledged_by
    event.acknowledged_at = datetime.now(settings.tz).replace(tzinfo=None)

    await db.commit()
    await db.refresh(event)

    return ApiResponse(
        success=True,
        message="System event acknowledged successfully",
        data=_system_event_to_response(event)
    )


# ==============================================================================
# PATCH Endpoints
# ==============================================================================

@router.patch("/{event_id}",
              dependencies=[Depends(require_perm_optional_async("servers", "edit"))])
async def update_system_event(
    event_id: int,
    update_data: SystemEventUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """
    시스템 이벤트 수정

    **파라미터**:
    - **event_id**: 이벤트 ID
    - **update_data**: 수정할 데이터

    PRD Reference: PRD_System_Event.md Section 3
    """
    event = (await db.execute(
        select(SystemEvent).where(SystemEvent.id == event_id)
    )).scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail=f"SystemEvent with id {event_id} not found")

    # 부분 업데이트
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(event, field, value)

    await db.commit()
    await db.refresh(event)

    return ApiResponse(
        success=True,
        message="System event updated successfully",
        data=_system_event_to_response(event)
    )


# ==============================================================================
# DELETE Endpoints
# ==============================================================================

@router.delete("/{event_id}",
               dependencies=[Depends(require_perm_optional_async("servers", "delete"))])
async def delete_system_event(event_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    시스템 이벤트 삭제

    **파라미터**:
    - **event_id**: 이벤트 ID

    PRD Reference: PRD_System_Event.md Section 3
    """
    event = (await db.execute(
        select(SystemEvent).where(SystemEvent.id == event_id)
    )).scalars().first()
    if not event:
        raise HTTPException(status_code=404, detail=f"SystemEvent with id {event_id} not found")

    await db.delete(event)
    await db.commit()

    return ApiResponse(
        success=True,
        message="System event deleted successfully",
        data=None
    )
