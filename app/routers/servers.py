"""
Servers API endpoints
Based on PRD_Server_Monitoring.md
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import math

from app.dependencies import get_db
from app.routers.auth import get_current_user_optional
from app.models.server import ServerCategory, Server
from app.models.system_event import SystemEvent
from app.utils.enums import EnumServerStatus
from app.schemas.server import (
    ServerCreate,
    ServerUpdate,
    ServerResponse,
    ServerCategorySummary
)
from app.schemas.common import ApiResponse, ApiSingleResponse, PaginationMeta

router = APIRouter(tags=["Servers"])


def _server_to_response(server: Server) -> ServerResponse:
    """Server 모델을 ServerResponse로 변환하는 헬퍼 함수"""
    return ServerResponse(
        id=server.id,
        category_id=server.category_id,
        name=server.name,
        status=server.status.value,
        ip_address=server.ip_address,
        port=server.port,
        hostname=server.hostname,
        user_name=server.user_name,
        user_password=server.user_password,
        threshold_config=server.threshold_config,
        created_at=server.created_at,
        updated_at=server.updated_at
    )


@router.get("/summary", response_model=ApiSingleResponse[list[ServerCategorySummary]])
async def get_server_summary(
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    대시보드 서버 요약 조회

    카테고리별 서버 상태 요약 정보를 조회합니다.
    각 카테고리의 서버 수와 상태별 개수를 반환합니다.

    **Response**: 카테고리별 서버 요약 목록
    - **id**: 카테고리 ID
    - **name**: 카테고리 이름
    - **type_server**: 서버 타입
    - **total**: 전체 서버 수
    - **normal**: 정상 서버 수
    - **warning**: 경고 서버 수
    - **error**: 오류 서버 수
    - **servers**: 서버 목록
    """
    # Get all categories ordered by sort_order
    categories = db.query(ServerCategory).order_by(ServerCategory.sort_order).all()

    summaries = []
    for category in categories:
        # Get servers for this category
        servers = db.query(Server).filter(Server.category_id == category.id).all()

        # Count by status
        normal_count = sum(1 for s in servers if s.status == EnumServerStatus.NORMAL)
        warning_count = sum(1 for s in servers if s.status == EnumServerStatus.WARNING)
        error_count = sum(1 for s in servers if s.status == EnumServerStatus.ERROR)

        # Create server responses
        server_responses = [_server_to_response(s) for s in servers]

        summary = ServerCategorySummary(
            id=category.id,
            name=category.name,
            type_server=category.type_server.value,
            total=len(servers),
            normal=normal_count,
            warning=warning_count,
            error=error_count,
            servers=server_responses
        )
        summaries.append(summary)

    return ApiSingleResponse(
        success=True,
        message="Server summary retrieved successfully",
        data=summaries
    )


@router.get("", response_model=ApiResponse[list[ServerResponse]])
async def get_servers(
    page: int = Query(1, ge=1, description="페이지 번호 (기본값: 1)"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수 (기본값: 20, 최대: 100)"),
    category_id: Optional[int] = Query(None, description="카테고리 ID로 필터링"),
    status: Optional[str] = Query(None, description="서버 상태로 필터링 (NORMAL, WARNING, ERROR)"),
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    서버 목록 조회 (페이지네이션)

    서버 목록을 페이지네이션하여 조회합니다.
    카테고리 및 상태로 필터링할 수 있습니다.

    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    - **category_id**: 카테고리 ID로 필터링 (선택)
    - **status**: 서버 상태로 필터링 (선택, NORMAL/WARNING/ERROR)

    **Response**: 서버 목록 및 페이지네이션 정보
    """
    query = db.query(Server)

    # Apply filters
    if category_id is not None:
        query = query.filter(Server.category_id == category_id)
    if status is not None:
        query = query.filter(Server.status == status)

    # Get total count
    total = query.count()

    # Calculate pagination
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    # Get paginated results (order by id for stable pagination)
    servers = query.order_by(Server.id).offset(skip).limit(limit).all()

    # Convert to response format
    server_responses = [_server_to_response(s) for s in servers]

    pagination = PaginationMeta(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages
    )

    return ApiResponse(
        success=True,
        message="Servers retrieved successfully",
        data=server_responses,
        pagination=pagination
    )


@router.get("/{server_id}", response_model=ApiSingleResponse[ServerResponse])
async def get_server(
    server_id: int,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    서버 단건 조회

    ID로 서버 정보를 조회합니다.

    - **server_id**: 서버 ID (Path Parameter)

    **Response**: 서버 상세 정보

    **Error**:
    - 404: 서버를 찾을 수 없음
    """
    server = db.query(Server).filter(Server.id == server_id).first()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server with id {server_id} not found"
        )

    return ApiSingleResponse(
        success=True,
        message="Server retrieved successfully",
        data=_server_to_response(server)
    )


@router.get("/{server_id}/system-events")
async def get_server_system_events(
    server_id: int,
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    서버별 시스템 이벤트 조회

    특정 서버에서 발생한 시스템 이벤트 목록을 조회합니다.

    - **server_id**: 서버 ID (Path Parameter)
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)

    **Response**: 해당 서버의 시스템 이벤트 목록

    **Error**:
    - 404: 서버를 찾을 수 없음
    """
    # 서버 존재 확인
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server with id {server_id} not found"
        )

    # 해당 서버의 시스템 이벤트 조회
    query = db.query(SystemEvent).filter(SystemEvent.server_id == server_id)
    query = query.order_by(SystemEvent.created_at.desc())

    offset = (page - 1) * limit
    events = query.offset(offset).limit(limit).all()

    # 응답 변환
    event_responses = []
    for event in events:
        event_responses.append({
            "id": event.id,
            "server_id": event.server_id,
            "server_description": event.server_description,
            "type_event": event.type_event.value if event.type_event else None,
            "severity": event.severity.value if event.severity else None,
            "title": event.title,
            "message": event.message,
            "detail": event.detail,
            "is_acknowledged": event.is_acknowledged,
            "acknowledged_by": event.acknowledged_by,
            "acknowledged_at": event.acknowledged_at,
            "created_at": event.created_at
        })

    return ApiSingleResponse(
        success=True,
        message="Server system events retrieved successfully",
        data=event_responses
    )


@router.post("", response_model=ApiSingleResponse[ServerResponse], status_code=status.HTTP_201_CREATED)
async def create_server(
    server_data: ServerCreate,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    서버 생성

    새로운 서버를 생성합니다.
    유효한 카테고리 ID가 필요합니다.

    **Request Body**:
    - **category_id**: 소속 카테고리 ID (필수)
    - **name**: 서버 이름 (필수)
    - **status**: 서버 상태 EnumServerStatus (선택, 기본값: NORMAL)
    - **ip_address**: IP 주소 (필수)
    - **port**: 포트 번호 (필수)
    - **hostname**: 호스트명 (선택)
    - **threshold_config**: 임계치 설정 JSON (선택)

    **Response**: 생성된 서버 정보

    **Error**:
    - 404: 카테고리를 찾을 수 없음
    """
    # Verify category exists
    category = db.query(ServerCategory).filter(
        ServerCategory.id == server_data.category_id
    ).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server category with id {server_data.category_id} not found"
        )

    # Create new server
    new_server = Server(
        category_id=server_data.category_id,
        name=server_data.name,
        status=server_data.status,
        ip_address=server_data.ip_address,
        port=server_data.port,
        hostname=server_data.hostname,
        user_name=server_data.user_name,
        user_password=server_data.user_password,
        threshold_config=server_data.threshold_config
    )

    db.add(new_server)
    db.commit()
    db.refresh(new_server)

    return ApiSingleResponse(
        success=True,
        message="Server created successfully",
        data=_server_to_response(new_server)
    )


@router.patch("/{server_id}", response_model=ApiSingleResponse[ServerResponse])
async def update_server(
    server_id: int,
    server_data: ServerUpdate,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    서버 부분 수정 (PATCH)

    서버의 일부 필드만 수정합니다.
    제공된 필드만 업데이트되며, 나머지는 유지됩니다.

    - **server_id**: 서버 ID (Path Parameter)

    **Request Body** (모든 필드 선택):
    - **category_id**: 소속 카테고리 ID
    - **name**: 서버 이름
    - **status**: 서버 상태 EnumServerStatus
    - **ip_address**: IP 주소
    - **port**: 포트 번호
    - **hostname**: 호스트명
    - **threshold_config**: 임계치 설정 JSON

    **Response**: 수정된 서버 정보

    **Error**:
    - 404: 서버 또는 카테고리를 찾을 수 없음
    """
    server = db.query(Server).filter(Server.id == server_id).first()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server with id {server_id} not found"
        )

    # Verify category if being changed
    if server_data.category_id is not None:
        category = db.query(ServerCategory).filter(
            ServerCategory.id == server_data.category_id
        ).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server category with id {server_data.category_id} not found"
            )

    # Update fields if provided
    update_data = server_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(server, field, value)

    db.commit()
    db.refresh(server)

    return ApiSingleResponse(
        success=True,
        message="Server updated successfully",
        data=_server_to_response(server)
    )


@router.put("/{server_id}", response_model=ApiSingleResponse[ServerResponse])
async def replace_server(
    server_id: int,
    server_data: ServerCreate,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    서버 전체 수정 (PUT)

    서버의 모든 필드를 교체합니다.
    모든 필드가 필수입니다.

    - **server_id**: 서버 ID (Path Parameter)

    **Request Body** (모든 필드 필수):
    - **category_id**: 소속 카테고리 ID
    - **name**: 서버 이름
    - **status**: 서버 상태 EnumServerStatus
    - **ip_address**: IP 주소
    - **port**: 포트 번호
    - **hostname**: 호스트명
    - **threshold_config**: 임계치 설정 JSON

    **Response**: 수정된 서버 정보

    **Error**:
    - 404: 서버 또는 카테고리를 찾을 수 없음
    """
    server = db.query(Server).filter(Server.id == server_id).first()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server with id {server_id} not found"
        )

    # Verify category exists
    category = db.query(ServerCategory).filter(
        ServerCategory.id == server_data.category_id
    ).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server category with id {server_data.category_id} not found"
        )

    # Replace all fields
    server.category_id = server_data.category_id
    server.name = server_data.name
    server.status = server_data.status
    server.ip_address = server_data.ip_address
    server.port = server_data.port
    server.hostname = server_data.hostname
    server.user_name = server_data.user_name
    server.user_password = server_data.user_password
    server.threshold_config = server_data.threshold_config

    db.commit()
    db.refresh(server)

    return ApiSingleResponse(
        success=True,
        message="Server replaced successfully",
        data=_server_to_response(server)
    )


@router.delete("/{server_id}", response_model=ApiSingleResponse[dict])
async def delete_server(
    server_id: int,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    서버 삭제

    서버를 삭제합니다.

    - **server_id**: 서버 ID (Path Parameter)

    **Response**: 삭제된 서버 ID

    **Error**:
    - 404: 서버를 찾을 수 없음
    """
    server = db.query(Server).filter(Server.id == server_id).first()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server with id {server_id} not found"
        )

    db.delete(server)
    db.commit()

    return ApiSingleResponse(
        success=True,
        message="Server deleted successfully",
        data={"id": server_id}
    )
