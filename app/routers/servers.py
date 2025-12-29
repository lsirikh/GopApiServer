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
from app.utils.enums import EnumServerStatus
from app.schemas.server import (
    ServerCreate,
    ServerUpdate,
    ServerResponse,
    ServerCategorySummary
)
from app.schemas.common import ApiResponse, PaginationMeta

router = APIRouter(tags=["Servers"])


@router.get("/summary", response_model=ApiResponse[list[ServerCategorySummary]])
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
        server_responses = [
            ServerResponse(
                id=s.id,
                category_id=s.category_id,
                name=s.name,
                status=s.status.value,
                ip_address=s.ip_address,
                port=s.port,
                hostname=s.hostname,
                cpu_usage=s.cpu_usage,
                ram_usage=s.ram_usage,
                disk_usage=s.disk_usage,
                network_throughput=s.network_throughput,
                created_at=s.created_at,
                updated_at=s.updated_at
            )
            for s in servers
        ]

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

    return ApiResponse(
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

    # Get paginated results
    servers = query.offset(skip).limit(limit).all()

    # Convert to response format
    server_responses = [
        ServerResponse(
            id=s.id,
            category_id=s.category_id,
            name=s.name,
            status=s.status.value,
            ip_address=s.ip_address,
            port=s.port,
            hostname=s.hostname,
            cpu_usage=s.cpu_usage,
            ram_usage=s.ram_usage,
            disk_usage=s.disk_usage,
            network_throughput=s.network_throughput,
            created_at=s.created_at,
            updated_at=s.updated_at
        )
        for s in servers
    ]

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


@router.get("/{server_id}", response_model=ApiResponse[ServerResponse])
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

    server_response = ServerResponse(
        id=server.id,
        category_id=server.category_id,
        name=server.name,
        status=server.status.value,
        ip_address=server.ip_address,
        port=server.port,
        hostname=server.hostname,
        cpu_usage=server.cpu_usage,
        ram_usage=server.ram_usage,
        disk_usage=server.disk_usage,
        network_throughput=server.network_throughput,
        created_at=server.created_at,
        updated_at=server.updated_at
    )

    return ApiResponse(
        success=True,
        message="Server retrieved successfully",
        data=server_response
    )


@router.post("", response_model=ApiResponse[ServerResponse], status_code=status.HTTP_201_CREATED)
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
    - **cpu_usage**: CPU 사용률 (선택)
    - **ram_usage**: RAM 사용률 (선택)
    - **disk_usage**: 디스크 사용률 (선택)
    - **network_throughput**: 네트워크 처리량 (선택)

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
        cpu_usage=server_data.cpu_usage,
        ram_usage=server_data.ram_usage,
        disk_usage=server_data.disk_usage,
        network_throughput=server_data.network_throughput
    )

    db.add(new_server)
    db.commit()
    db.refresh(new_server)

    server_response = ServerResponse(
        id=new_server.id,
        category_id=new_server.category_id,
        name=new_server.name,
        status=new_server.status.value,
        ip_address=new_server.ip_address,
        port=new_server.port,
        hostname=new_server.hostname,
        cpu_usage=new_server.cpu_usage,
        ram_usage=new_server.ram_usage,
        disk_usage=new_server.disk_usage,
        network_throughput=new_server.network_throughput,
        created_at=new_server.created_at,
        updated_at=new_server.updated_at
    )

    return ApiResponse(
        success=True,
        message="Server created successfully",
        data=server_response
    )


@router.patch("/{server_id}", response_model=ApiResponse[ServerResponse])
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
    - **cpu_usage**: CPU 사용률
    - **ram_usage**: RAM 사용률
    - **disk_usage**: 디스크 사용률
    - **network_throughput**: 네트워크 처리량

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

    server_response = ServerResponse(
        id=server.id,
        category_id=server.category_id,
        name=server.name,
        status=server.status.value,
        ip_address=server.ip_address,
        port=server.port,
        hostname=server.hostname,
        cpu_usage=server.cpu_usage,
        ram_usage=server.ram_usage,
        disk_usage=server.disk_usage,
        network_throughput=server.network_throughput,
        created_at=server.created_at,
        updated_at=server.updated_at
    )

    return ApiResponse(
        success=True,
        message="Server updated successfully",
        data=server_response
    )


@router.put("/{server_id}", response_model=ApiResponse[ServerResponse])
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
    - **cpu_usage**: CPU 사용률
    - **ram_usage**: RAM 사용률
    - **disk_usage**: 디스크 사용률
    - **network_throughput**: 네트워크 처리량

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
    server.cpu_usage = server_data.cpu_usage
    server.ram_usage = server_data.ram_usage
    server.disk_usage = server_data.disk_usage
    server.network_throughput = server_data.network_throughput

    db.commit()
    db.refresh(server)

    server_response = ServerResponse(
        id=server.id,
        category_id=server.category_id,
        name=server.name,
        status=server.status.value,
        ip_address=server.ip_address,
        port=server.port,
        hostname=server.hostname,
        cpu_usage=server.cpu_usage,
        ram_usage=server.ram_usage,
        disk_usage=server.disk_usage,
        network_throughput=server.network_throughput,
        created_at=server.created_at,
        updated_at=server.updated_at
    )

    return ApiResponse(
        success=True,
        message="Server replaced successfully",
        data=server_response
    )


@router.delete("/{server_id}", response_model=ApiResponse[dict])
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

    return ApiResponse(
        success=True,
        message="Server deleted successfully",
        data={"id": server_id}
    )
