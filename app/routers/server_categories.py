"""
Server Categories API endpoints
Based on PRD_Server_Monitoring.md
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import math

from app.dependencies import get_db
from app.routers.auth import get_current_user_optional
from app.models.server import ServerCategory, Server
from app.utils.enums import EnumServerType, EnumServerStatus
from app.schemas.server import (
    ServerCategoryCreate,
    ServerCategoryUpdate,
    ServerCategoryResponse,
    ServerCategoryWithServers,
    ServerResponse
)
from app.schemas.common import ApiResponse, ApiSingleResponse, PaginationMeta

router = APIRouter(tags=["Server Categories"])


@router.get("", response_model=ApiResponse[list[ServerCategoryResponse]])
async def get_server_categories(
    page: int = Query(1, ge=1, description="페이지 번호 (기본값: 1)"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수 (기본값: 20, 최대: 100)"),
    type_server: Optional[str] = Query(None, description="서버 타입으로 필터링 (EnumServerType)"),
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    서버 카테고리 목록 조회 (페이지네이션)

    서버 카테고리 목록을 페이지네이션하여 조회합니다.
    sort_order 기준으로 정렬됩니다.

    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    - **type_server**: 서버 타입으로 필터링 (선택)

    **Response**: 서버 카테고리 목록 및 페이지네이션 정보
    """
    query = db.query(ServerCategory)

    # Apply filter
    if type_server is not None:
        query = query.filter(ServerCategory.type_server == type_server)

    # Order by sort_order
    query = query.order_by(ServerCategory.sort_order)

    # Get total count
    total = query.count()

    # Calculate pagination
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    # Get paginated results (order by id for stable pagination)
    categories = query.order_by(ServerCategory.id).offset(skip).limit(limit).all()

    # Convert to response format
    category_responses = [
        ServerCategoryResponse(
            id=c.id,
            name=c.name,
            type_server=c.type_server.value,
            description=c.description,
            sort_order=c.sort_order,
            created_at=c.created_at,
            updated_at=c.updated_at
        )
        for c in categories
    ]

    pagination = PaginationMeta(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages
    )

    return ApiResponse(
        success=True,
        message="Server categories retrieved successfully",
        data=category_responses,
        pagination=pagination
    )


@router.get("/{category_id}", response_model=ApiSingleResponse[ServerCategoryWithServers])
async def get_server_category(
    category_id: int,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    서버 카테고리 단건 조회

    ID로 서버 카테고리를 조회합니다.
    해당 카테고리에 속한 서버 목록도 함께 반환됩니다.

    - **category_id**: 서버 카테고리 ID (Path Parameter)

    **Response**: 서버 카테고리 정보 및 소속 서버 목록

    **Error**:
    - 404: 카테고리를 찾을 수 없음
    """
    category = db.query(ServerCategory).filter(ServerCategory.id == category_id).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server category with id {category_id} not found"
        )

    # Get servers for this category
    servers = db.query(Server).filter(Server.category_id == category_id).all()
    server_responses = [
        ServerResponse(
            id=s.id,
            category_id=s.category_id,
            name=s.name,
            status=s.status.value,
            ip_address=s.ip_address,
            port=s.port,
            hostname=s.hostname,
            user_name=s.user_name,
            user_password=s.user_password,
            threshold_config=s.threshold_config,
            created_at=s.created_at,
            updated_at=s.updated_at
        )
        for s in servers
    ]

    category_response = ServerCategoryWithServers(
        id=category.id,
        name=category.name,
        type_server=category.type_server.value,
        description=category.description,
        sort_order=category.sort_order,
        created_at=category.created_at,
        updated_at=category.updated_at,
        servers=server_responses
    )

    return ApiSingleResponse(
        success=True,
        message="Server category retrieved successfully",
        data=category_response
    )


@router.post("", response_model=ApiSingleResponse[ServerCategoryResponse], status_code=status.HTTP_201_CREATED)
async def create_server_category(
    category_data: ServerCategoryCreate,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    서버 카테고리 생성

    새로운 서버 카테고리를 생성합니다.
    type_server는 유니크하므로 중복될 수 없습니다.

    **Request Body**:
    - **name**: 카테고리 이름 (필수)
    - **type_server**: 서버 타입 EnumServerType (필수, 유니크)
    - **description**: 카테고리 설명 (선택)
    - **sort_order**: 정렬 순서 (선택, 기본값: 0)

    **Response**: 생성된 서버 카테고리 정보

    **Error**:
    - 409: 동일한 type_server가 이미 존재함
    """
    # Check for duplicate type_server (unique constraint)
    existing = db.query(ServerCategory).filter(
        ServerCategory.type_server == category_data.type_server
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Server category with type_server '{category_data.type_server.value}' already exists"
        )

    # Create new category
    new_category = ServerCategory(
        name=category_data.name,
        type_server=category_data.type_server,
        description=category_data.description,
        sort_order=category_data.sort_order
    )

    db.add(new_category)
    db.commit()
    db.refresh(new_category)

    category_response = ServerCategoryResponse(
        id=new_category.id,
        name=new_category.name,
        type_server=new_category.type_server.value,
        description=new_category.description,
        sort_order=new_category.sort_order,
        created_at=new_category.created_at,
        updated_at=new_category.updated_at
    )

    return ApiSingleResponse(
        success=True,
        message="Server category created successfully",
        data=category_response
    )


@router.patch("/{category_id}", response_model=ApiSingleResponse[ServerCategoryResponse])
async def update_server_category(
    category_id: int,
    category_data: ServerCategoryUpdate,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    서버 카테고리 부분 수정 (PATCH)

    서버 카테고리의 일부 필드만 수정합니다.
    제공된 필드만 업데이트되며, 나머지는 유지됩니다.

    - **category_id**: 서버 카테고리 ID (Path Parameter)

    **Request Body** (모든 필드 선택):
    - **name**: 카테고리 이름
    - **type_server**: 서버 타입 EnumServerType (유니크)
    - **description**: 카테고리 설명
    - **sort_order**: 정렬 순서

    **Response**: 수정된 서버 카테고리 정보

    **Error**:
    - 404: 카테고리를 찾을 수 없음
    - 409: 변경하려는 type_server가 이미 존재함
    """
    category = db.query(ServerCategory).filter(ServerCategory.id == category_id).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server category with id {category_id} not found"
        )

    # Check for type_server conflict
    if category_data.type_server is not None:
        existing = db.query(ServerCategory).filter(
            ServerCategory.type_server == category_data.type_server,
            ServerCategory.id != category_id
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Server category with type_server '{category_data.type_server.value}' already exists"
            )

    # Update fields if provided
    update_data = category_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)

    category_response = ServerCategoryResponse(
        id=category.id,
        name=category.name,
        type_server=category.type_server.value,
        description=category.description,
        sort_order=category.sort_order,
        created_at=category.created_at,
        updated_at=category.updated_at
    )

    return ApiSingleResponse(
        success=True,
        message="Server category updated successfully",
        data=category_response
    )


@router.put("/{category_id}", response_model=ApiSingleResponse[ServerCategoryResponse])
async def replace_server_category(
    category_id: int,
    category_data: ServerCategoryCreate,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    서버 카테고리 전체 수정 (PUT)

    서버 카테고리의 모든 필드를 교체합니다.
    모든 필드가 필수입니다.

    - **category_id**: 서버 카테고리 ID (Path Parameter)

    **Request Body** (모든 필드 필수):
    - **name**: 카테고리 이름
    - **type_server**: 서버 타입 EnumServerType (유니크)
    - **description**: 카테고리 설명
    - **sort_order**: 정렬 순서

    **Response**: 수정된 서버 카테고리 정보

    **Error**:
    - 404: 카테고리를 찾을 수 없음
    - 409: 변경하려는 type_server가 이미 존재함
    """
    category = db.query(ServerCategory).filter(ServerCategory.id == category_id).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server category with id {category_id} not found"
        )

    # Check for type_server conflict
    if category_data.type_server != category.type_server:
        existing = db.query(ServerCategory).filter(
            ServerCategory.type_server == category_data.type_server,
            ServerCategory.id != category_id
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Server category with type_server '{category_data.type_server.value}' already exists"
            )

    # Replace all fields
    category.name = category_data.name
    category.type_server = category_data.type_server
    category.description = category_data.description
    category.sort_order = category_data.sort_order

    db.commit()
    db.refresh(category)

    category_response = ServerCategoryResponse(
        id=category.id,
        name=category.name,
        type_server=category.type_server.value,
        description=category.description,
        sort_order=category.sort_order,
        created_at=category.created_at,
        updated_at=category.updated_at
    )

    return ApiSingleResponse(
        success=True,
        message="Server category replaced successfully",
        data=category_response
    )


@router.delete("/{category_id}", response_model=ApiSingleResponse[None])
async def delete_server_category(
    category_id: int,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    서버 카테고리 삭제

    서버 카테고리를 삭제합니다.
    해당 카테고리에 속한 모든 서버도 함께 삭제됩니다 (Cascade Delete).

    - **category_id**: 서버 카테고리 ID (Path Parameter)

    **Response**: 삭제된 카테고리 ID

    **Error**:
    - 404: 카테고리를 찾을 수 없음
    """
    category = db.query(ServerCategory).filter(ServerCategory.id == category_id).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server category with id {category_id} not found"
        )

    db.delete(category)
    db.commit()

    return ApiSingleResponse(
        success=True,
        message=f"Server category {category_id} deleted successfully",
        data=None
    )
