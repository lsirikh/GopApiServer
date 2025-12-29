"""
EventMapping API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import math

from app.dependencies import get_db
from app.routers.auth import get_current_user_optional
from app.models.integration import EventMapping
from app.schemas.integration import EventMappingCreate, EventMappingResponse, EventMappingUpdate
from app.schemas.common import ApiResponse, PaginationMeta

router = APIRouter(tags=[])


@router.get("", response_model=ApiResponse[list[EventMappingResponse]])
async def get_event_mappings(
    page: int = Query(1, ge=1, description="페이지 번호 (기본값: 1)"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수 (기본값: 20, 최대: 100)"),
    name_event: Optional[str] = Query(None, description="이벤트 이름으로 필터링"),
    group_event: Optional[str] = Query(None, description="이벤트 그룹으로 필터링"),
    category_event: Optional[str] = Query(None, description="이벤트 카테고리로 필터링"),
    status: Optional[bool] = Query(None, description="상태로 필터링"),
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    이벤트 매핑 목록 조회 (페이지네이션)

    이벤트 매핑 목록을 페이지네이션하여 조회합니다. 다양한 필터 옵션을 지원합니다.

    **파라미터**:
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    - **name_event**: 이벤트 이름으로 필터링
    - **group_event**: 이벤트 그룹으로 필터링
    - **category_event**: 이벤트 카테고리로 필터링
    - **status**: 상태로 필터링

    **Response**: 이벤트 매핑 목록 및 페이지네이션 정보
    """
    # Build query
    query = db.query(EventMapping)

    # Apply filters
    if name_event is not None:
        query = query.filter(EventMapping.name_event == name_event)
    if group_event is not None:
        query = query.filter(EventMapping.group_event == group_event)
    if category_event is not None:
        query = query.filter(EventMapping.category_event == category_event)
    if status is not None:
        query = query.filter(EventMapping.status == status)

    # Get total count
    total = query.count()

    # Calculate pagination
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    # Get paginated results
    mappings = query.offset(skip).limit(limit).all()

    # Convert to response format
    mapping_responses = [
        EventMappingResponse(
            id=m.id,
            name_event=m.name_event,
            group_event=m.group_event,
            category_event=m.category_event,
            description=m.description,
            status=m.status,
            created_at=m.created_at,
            updated_at=m.updated_at
        )
        for m in mappings
    ]

    pagination = PaginationMeta(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages
    )

    return ApiResponse(
        success=True,
        message="Event mappings retrieved successfully",
        data=mapping_responses,
        pagination=pagination
    )


@router.get("/{mapping_id}", response_model=ApiResponse[EventMappingResponse])
async def get_event_mapping(
    mapping_id: int,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    이벤트 매핑 단건 조회

    특정 이벤트 매핑의 상세 정보를 조회합니다.

    **파라미터**:
    - **mapping_id**: 이벤트 매핑 ID (Path Parameter)

    **Response**: 이벤트 매핑 상세 정보

    **Error**:
    - 404: 이벤트 매핑을 찾을 수 없음
    """
    mapping = db.query(EventMapping).filter(EventMapping.id == mapping_id).first()

    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event mapping with id {mapping_id} not found"
        )

    mapping_response = EventMappingResponse(
        id=mapping.id,
        name_event=mapping.name_event,
        group_event=mapping.group_event,
        category_event=mapping.category_event,
        description=mapping.description,
        status=mapping.status,
        created_at=mapping.created_at,
        updated_at=mapping.updated_at
    )

    return ApiResponse(
        success=True,
        message="Event mapping retrieved successfully",
        data=mapping_response
    )


@router.post("", response_model=ApiResponse[EventMappingResponse], status_code=status.HTTP_201_CREATED)
async def create_event_mapping(
    mapping: EventMappingCreate,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    이벤트 매핑 생성

    새로운 이벤트 매핑을 생성합니다.

    **Request Body**:
    - **name_event**: 이벤트 이름 (필수)
    - **group_event**: 이벤트 그룹 (필수)
    - **category_event**: 이벤트 카테고리 (필수)
    - **description**: 설명 (선택)
    - **status**: 상태 (필수)

    **Response**: 생성된 이벤트 매핑 정보
    """
    new_mapping = EventMapping(
        name_event=mapping.name_event,
        group_event=mapping.group_event,
        category_event=mapping.category_event,
        description=mapping.description,
        status=mapping.status
    )

    db.add(new_mapping)
    db.commit()
    db.refresh(new_mapping)

    mapping_response = EventMappingResponse(
        id=new_mapping.id,
        name_event=new_mapping.name_event,
        group_event=new_mapping.group_event,
        category_event=new_mapping.category_event,
        description=new_mapping.description,
        status=new_mapping.status,
        created_at=new_mapping.created_at,
        updated_at=new_mapping.updated_at
    )

    return ApiResponse(
        success=True,
        message="Event mapping created successfully",
        data=mapping_response
    )


@router.patch("/{mapping_id}", response_model=ApiResponse[EventMappingResponse])
async def update_event_mapping_partial(
    mapping_id: int,
    mapping: EventMappingUpdate,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    이벤트 매핑 부분 수정 (PATCH)

    이벤트 매핑의 일부 필드만 수정합니다. 제공된 필드만 업데이트됩니다.

    **파라미터**:
    - **mapping_id**: 이벤트 매핑 ID (Path Parameter)

    **Request Body** (모든 필드 선택):
    - **name_event**: 이벤트 이름
    - **group_event**: 이벤트 그룹
    - **category_event**: 이벤트 카테고리
    - **description**: 설명
    - **status**: 상태

    **Response**: 수정된 이벤트 매핑 정보

    **Error**:
    - 404: 이벤트 매핑을 찾을 수 없음
    """
    existing_mapping = db.query(EventMapping).filter(EventMapping.id == mapping_id).first()

    if not existing_mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event mapping with id {mapping_id} not found"
        )

    # Update only provided fields
    update_data = mapping.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(existing_mapping, field, value)

    db.commit()
    db.refresh(existing_mapping)

    mapping_response = EventMappingResponse(
        id=existing_mapping.id,
        name_event=existing_mapping.name_event,
        group_event=existing_mapping.group_event,
        category_event=existing_mapping.category_event,
        description=existing_mapping.description,
        status=existing_mapping.status,
        created_at=existing_mapping.created_at,
        updated_at=existing_mapping.updated_at
    )

    return ApiResponse(
        success=True,
        message="Event mapping updated successfully",
        data=mapping_response
    )


@router.put("/{mapping_id}", response_model=ApiResponse[EventMappingResponse])
async def update_event_mapping_full(
    mapping_id: int,
    mapping: EventMappingCreate,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    이벤트 매핑 전체 수정 (PUT)

    이벤트 매핑의 모든 필드를 교체합니다. 모든 필드가 필수입니다.

    **파라미터**:
    - **mapping_id**: 이벤트 매핑 ID (Path Parameter)

    **Request Body** (모든 필드 필수):
    - **name_event**: 이벤트 이름
    - **group_event**: 이벤트 그룹
    - **category_event**: 이벤트 카테고리
    - **description**: 설명
    - **status**: 상태

    **Response**: 수정된 이벤트 매핑 정보

    **Error**:
    - 404: 이벤트 매핑을 찾을 수 없음
    """
    existing_mapping = db.query(EventMapping).filter(EventMapping.id == mapping_id).first()

    if not existing_mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event mapping with id {mapping_id} not found"
        )

    # Update all fields
    existing_mapping.name_event = mapping.name_event
    existing_mapping.group_event = mapping.group_event
    existing_mapping.category_event = mapping.category_event
    existing_mapping.description = mapping.description
    existing_mapping.status = mapping.status

    db.commit()
    db.refresh(existing_mapping)

    mapping_response = EventMappingResponse(
        id=existing_mapping.id,
        name_event=existing_mapping.name_event,
        group_event=existing_mapping.group_event,
        category_event=existing_mapping.category_event,
        description=existing_mapping.description,
        status=existing_mapping.status,
        created_at=existing_mapping.created_at,
        updated_at=existing_mapping.updated_at
    )

    return ApiResponse(
        success=True,
        message="Event mapping updated successfully",
        data=mapping_response
    )


@router.delete("/{mapping_id}", response_model=ApiResponse[dict])
async def delete_event_mapping(
    mapping_id: int,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    이벤트 매핑 삭제

    특정 이벤트 매핑을 삭제합니다.

    **파라미터**:
    - **mapping_id**: 이벤트 매핑 ID (Path Parameter)

    **Response**: 삭제 확인 정보

    **Error**:
    - 404: 이벤트 매핑을 찾을 수 없음
    """
    mapping = db.query(EventMapping).filter(EventMapping.id == mapping_id).first()

    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event mapping with id {mapping_id} not found"
        )

    db.delete(mapping)
    db.commit()

    return ApiResponse(
        success=True,
        message="Event mapping deleted successfully",
        data={"id": mapping_id}
    )
