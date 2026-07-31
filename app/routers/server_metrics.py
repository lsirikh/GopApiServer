"""
Server Metrics API endpoints
Based on PRD_System_Event.md Section 2.4
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from app.dependencies import get_async_db
from app.routers.auth import get_current_account_user_optional_async
from app.models.server import Server, ServerMetrics
from app.models.system_event import SystemEvent
from app.utils.enums import EnumSystemEventType, EnumSystemEventSeverity
from app.schemas.server import (
    ServerMetricsCreate,
    ServerMetricsResponse,
    ServerMetricsLatestResponse
)
from app.schemas.common import ApiResponse, ApiSingleResponse
from app.config import settings

router = APIRouter()


def _to_naive_kst(dt: Optional[datetime]) -> Optional[datetime]:
    """tz-aware datetime 을 naive-KST 로 정규화.

    `server_metrics.collected_at` 컬럼은 TIMESTAMP WITHOUT TIME ZONE(naive)이고,
    프로젝트 표준 타임스탬프도 `datetime.now(settings.tz).replace(tzinfo=None)`(naive-KST)다.
    클라/워커가 KST(+09:00) 등 tz-aware 값을 보내면 asyncpg 가
    "can't subtract offset-naive and offset-aware datetimes" 로 INSERT 를 거부하므로,
    aware 입력은 KST 벽시계로 변환 후 tzinfo 를 제거해 naive-KST 로 저장한다. (naive 입력은 그대로)
    """
    if dt is not None and dt.tzinfo is not None:
        return dt.astimezone(settings.tz).replace(tzinfo=None)
    return dt


def _metrics_to_response(
    metrics: ServerMetrics,
    threshold_exceeded: dict = None
) -> ServerMetricsResponse:
    """ServerMetrics 모델을 Response로 변환"""
    return ServerMetricsResponse(
        id=metrics.id,
        server_id=metrics.server_id,
        cpu_usage=metrics.cpu_usage,
        ram_usage=metrics.ram_usage,
        ram_total_gb=metrics.ram_total_gb,
        ram_used_gb=metrics.ram_used_gb,
        disk_usage=metrics.disk_usage,
        disk_total_gb=metrics.disk_total_gb,
        disk_used_gb=metrics.disk_used_gb,
        network_in_mbps=metrics.network_in_mbps,
        network_out_mbps=metrics.network_out_mbps,
        process_count=metrics.process_count,
        detail=metrics.detail,
        collected_at=metrics.collected_at,
        created_at=metrics.created_at,
        threshold_exceeded=threshold_exceeded
    )


def _check_thresholds(metrics: ServerMetrics, threshold_config: dict) -> dict:
    """임계치 초과 여부 확인"""
    if not threshold_config:
        return None

    exceeded = {}

    # CPU 체크
    if metrics.cpu_usage is not None and "cpu" in threshold_config:
        cpu_config = threshold_config["cpu"]
        if cpu_config.get("critical") and metrics.cpu_usage >= cpu_config["critical"]:
            exceeded["cpu"] = {"level": "critical", "value": metrics.cpu_usage, "threshold": cpu_config["critical"]}
        elif cpu_config.get("warning") and metrics.cpu_usage >= cpu_config["warning"]:
            exceeded["cpu"] = {"level": "warning", "value": metrics.cpu_usage, "threshold": cpu_config["warning"]}

    # RAM 체크
    if metrics.ram_usage is not None and "ram" in threshold_config:
        ram_config = threshold_config["ram"]
        if ram_config.get("critical") and metrics.ram_usage >= ram_config["critical"]:
            exceeded["ram"] = {"level": "critical", "value": metrics.ram_usage, "threshold": ram_config["critical"]}
        elif ram_config.get("warning") and metrics.ram_usage >= ram_config["warning"]:
            exceeded["ram"] = {"level": "warning", "value": metrics.ram_usage, "threshold": ram_config["warning"]}

    # Disk 체크
    if metrics.disk_usage is not None and "disk" in threshold_config:
        disk_config = threshold_config["disk"]
        if disk_config.get("critical") and metrics.disk_usage >= disk_config["critical"]:
            exceeded["disk"] = {"level": "critical", "value": metrics.disk_usage, "threshold": disk_config["critical"]}
        elif disk_config.get("warning") and metrics.disk_usage >= disk_config["warning"]:
            exceeded["disk"] = {"level": "warning", "value": metrics.disk_usage, "threshold": disk_config["warning"]}

    # Network 체크 (PRD: threshold_config.network)
    if "network" in threshold_config:
        network_config = threshold_config["network"]
        # network_in_mbps와 network_out_mbps 중 큰 값으로 체크
        network_max = None
        if metrics.network_in_mbps is not None and metrics.network_out_mbps is not None:
            network_max = max(metrics.network_in_mbps, metrics.network_out_mbps)
        elif metrics.network_in_mbps is not None:
            network_max = metrics.network_in_mbps
        elif metrics.network_out_mbps is not None:
            network_max = metrics.network_out_mbps

        if network_max is not None:
            if network_config.get("critical_mbps") and network_max >= network_config["critical_mbps"]:
                exceeded["network"] = {"level": "critical", "value": network_max, "threshold": network_config["critical_mbps"]}
            elif network_config.get("warning_mbps") and network_max >= network_config["warning_mbps"]:
                exceeded["network"] = {"level": "warning", "value": network_max, "threshold": network_config["warning_mbps"]}

    return exceeded if exceeded else None


def _create_threshold_event(
    db: AsyncSession,
    server: Server,
    resource_type: str,
    threshold_info: dict
) -> SystemEvent:
    """임계치 초과 시 SystemEvent 생성"""
    level = threshold_info["level"]
    value = threshold_info["value"]
    threshold = threshold_info["threshold"]

    # severity 결정
    severity = EnumSystemEventSeverity.CRITICAL if level == "critical" else EnumSystemEventSeverity.WARNING

    # 이벤트 생성
    event = SystemEvent(
        server_id=server.id,
        server_description=f"{server.name} ({server.ip_address})",
        type_event=EnumSystemEventType.RESOURCE_THRESHOLD,
        severity=severity,
        title=f"{resource_type.upper()} 임계치 초과 ({level})",
        message=f"{resource_type.upper()} 사용률 {value:.1f}%가 임계치 {threshold}%를 초과했습니다.",
        detail={
            "resource_type": resource_type,
            "level": level,
            "value": value,
            "threshold": threshold
        },
        is_acknowledged=False
    )

    db.add(event)
    return event


async def _create_threshold_events(
    db: AsyncSession,
    server: Server,
    threshold_exceeded: dict
) -> None:
    """모든 임계치 초과에 대해 SystemEvent 생성"""
    if not threshold_exceeded:
        return

    for resource_type, threshold_info in threshold_exceeded.items():
        _create_threshold_event(db, server, resource_type, threshold_info)

    await db.commit()


@router.post(
    "/{server_id}/metrics",
    response_model=ApiSingleResponse[ServerMetricsResponse],
    status_code=status.HTTP_201_CREATED
)
async def create_server_metrics(
    server_id: int,
    metrics_data: ServerMetricsCreate,
    current_user=Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db)
):
    """
    서버 메트릭 저장

    서버의 리소스 사용 현황을 저장합니다.
    임계치 설정이 있는 경우 초과 여부를 응답에 포함합니다.

    **파라미터**:
    - **server_id**: 서버 ID (Path Parameter)

    **Request Body**:
    - **cpu_usage**: CPU 사용률 (%)
    - **ram_usage**: RAM 사용률 (%)
    - **ram_total_gb**: RAM 전체 크기 (GB)
    - **ram_used_gb**: RAM 사용 크기 (GB)
    - **disk_usage**: Disk 사용률 (%)
    - **disk_total_gb**: Disk 전체 크기 (GB)
    - **disk_used_gb**: Disk 사용 크기 (GB)
    - **network_in_mbps**: 네트워크 수신 속도 (Mbps)
    - **network_out_mbps**: 네트워크 송신 속도 (Mbps)
    - **process_count**: 프로세스 수
    - **detail**: 추가 상세 정보 (JSON)
    - **collected_at**: 수집 시간

    **Response**: 저장된 메트릭 정보 + threshold_exceeded (초과 시)

    **Error**:
    - 404: 서버를 찾을 수 없음
    """
    # 서버 존재 확인
    server = (await db.execute(select(Server).where(Server.id == server_id))).scalars().first()
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server with id {server_id} not found"
        )

    # 메트릭 저장
    new_metrics = ServerMetrics(
        server_id=server_id,
        cpu_usage=metrics_data.cpu_usage,
        ram_usage=metrics_data.ram_usage,
        ram_total_gb=metrics_data.ram_total_gb,
        ram_used_gb=metrics_data.ram_used_gb,
        disk_usage=metrics_data.disk_usage,
        disk_total_gb=metrics_data.disk_total_gb,
        disk_used_gb=metrics_data.disk_used_gb,
        network_in_mbps=metrics_data.network_in_mbps,
        network_out_mbps=metrics_data.network_out_mbps,
        process_count=metrics_data.process_count,
        detail=metrics_data.detail,
        collected_at=_to_naive_kst(metrics_data.collected_at)  # tz-aware(KST) → naive-KST (asyncpg naive 컬럼)
    )

    db.add(new_metrics)
    await db.commit()
    await db.refresh(new_metrics)

    # 임계치 체크
    threshold_exceeded = _check_thresholds(new_metrics, server.threshold_config)

    # 임계치 초과 시 시스템 이벤트 생성
    if threshold_exceeded:
        await _create_threshold_events(db, server, threshold_exceeded)

    return ApiSingleResponse(
        success=True,
        message="Server metrics created successfully",
        data=_metrics_to_response(new_metrics, threshold_exceeded)
    )


@router.get(
    "/{server_id}/metrics",
    response_model=ApiResponse[list[ServerMetricsResponse]]
)
async def get_server_metrics(
    server_id: int,
    limit: int = Query(100, ge=1, le=1000, description="조회할 메트릭 수 (기본값: 100, 최대: 1000)"),
    start_time: Optional[datetime] = Query(None, description="시작 시간 (ISO 8601)"),
    end_time: Optional[datetime] = Query(None, description="종료 시간 (ISO 8601)"),
    current_user=Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db)
):
    """
    서버 메트릭 목록 조회

    서버의 리소스 사용 이력을 조회합니다.

    **파라미터**:
    - **server_id**: 서버 ID (Path Parameter)
    - **limit**: 조회할 메트릭 수 (기본값: 100)
    - **start_time**: 시작 시간 필터 (ISO 8601)
    - **end_time**: 종료 시간 필터 (ISO 8601)

    **Response**: 메트릭 목록 (최신순)

    **Error**:
    - 404: 서버를 찾을 수 없음
    """
    # 서버 존재 확인
    server = (await db.execute(select(Server).where(Server.id == server_id))).scalars().first()
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server with id {server_id} not found"
        )

    # 쿼리 빌드
    stmt = select(ServerMetrics).where(ServerMetrics.server_id == server_id)

    if start_time:
        stmt = stmt.where(ServerMetrics.created_at >= start_time)
    if end_time:
        stmt = stmt.where(ServerMetrics.created_at <= end_time)

    # 최신순 정렬 및 제한
    stmt = stmt.order_by(ServerMetrics.created_at.desc()).limit(limit)
    metrics_list = (await db.execute(stmt)).scalars().all()

    return ApiResponse(
        success=True,
        message="Server metrics retrieved successfully",
        data=[_metrics_to_response(m) for m in metrics_list]
    )


@router.get(
    "/{server_id}/metrics/latest",
    response_model=ApiSingleResponse[ServerMetricsLatestResponse]
)
async def get_server_metrics_latest(
    server_id: int,
    current_user=Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db)
):
    """
    서버 최신 메트릭 조회

    서버의 가장 최근 리소스 사용 현황을 조회합니다.

    **파라미터**:
    - **server_id**: 서버 ID (Path Parameter)

    **Response**: 최신 메트릭 정보

    **Error**:
    - 404: 서버를 찾을 수 없음
    """
    # 서버 존재 확인
    server = (await db.execute(select(Server).where(Server.id == server_id))).scalars().first()
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server with id {server_id} not found"
        )

    # 최신 메트릭 조회
    latest_metrics = (
        await db.execute(
            select(ServerMetrics)
            .where(ServerMetrics.server_id == server_id)
            .order_by(ServerMetrics.created_at.desc())
        )
    ).scalars().first()

    latest_response = None
    if latest_metrics:
        threshold_exceeded = _check_thresholds(latest_metrics, server.threshold_config)
        latest_response = _metrics_to_response(latest_metrics, threshold_exceeded)

    return ApiSingleResponse(
        success=True,
        message="Latest server metrics retrieved successfully",
        data=ServerMetricsLatestResponse(
            server_id=server_id,
            server_name=server.name,
            latest_metrics=latest_response
        )
    )


@router.delete(
    "/{server_id}/metrics",
    response_model=ApiSingleResponse[None]
)
async def delete_old_server_metrics(
    server_id: int,
    older_than_days: int = Query(30, ge=1, description="삭제할 메트릭의 기준 일수 (기본값: 30일 이전)"),
    current_user=Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db)
):
    """
    오래된 서버 메트릭 삭제

    지정된 일수 이전의 메트릭을 삭제합니다.

    **파라미터**:
    - **server_id**: 서버 ID (Path Parameter)
    - **older_than_days**: 삭제 기준 일수 (기본값: 30일 이전)

    **Response**: 삭제된 메트릭 수

    **Error**:
    - 404: 서버를 찾을 수 없음
    """
    from datetime import timedelta

    # 서버 존재 확인
    server = (await db.execute(select(Server).where(Server.id == server_id))).scalars().first()
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server with id {server_id} not found"
        )

    # 삭제 기준 시간 계산
    from app.config import settings
    cutoff_time = datetime.now(settings.tz) - timedelta(days=older_than_days)

    # 오래된 메트릭 삭제
    result = await db.execute(
        delete(ServerMetrics).where(
            ServerMetrics.server_id == server_id,
            ServerMetrics.created_at < cutoff_time
        )
    )
    deleted_count = result.rowcount

    await db.commit()

    return ApiSingleResponse(
        success=True,
        message=f"Deleted {deleted_count} old metrics for server {server_id}",
        data=None
    )
