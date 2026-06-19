"""
EventMapping API endpoints

PRD: PRD_CategoryEvent_Refactoring.md v1.1
- category_event → category_event_mapping 필드명 변경
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import math

from app.dependencies import get_db
from app.routers.auth import get_current_user_optional
from app.models.integration import EventMapping
from app.schemas.integration import EventMappingCreate, EventMappingResponse, EventMappingUpdate
from app.schemas.common import ApiResponse, ApiSingleResponse, PaginationMeta
from app.utils.enums import EnumMappingEventCategory, EnumConfigResourceType, EnumConfigActionType
from app.services.config_log_service import log_config_change, get_changed_fields, model_to_dict

router = APIRouter(tags=[])


@router.get("", response_model=ApiResponse[list[EventMappingResponse]])
async def get_event_mappings(
    page: int = Query(1, ge=1, description="페이지 번호 (기본값: 1)"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수 (기본값: 20, 최대: 100)"),
    name_event: Optional[str] = Query(None, description="이벤트 이름으로 필터링"),
    device_group_id: Optional[int] = Query(None, description="DeviceGroup ID로 필터링"),
    category_event_mapping: Optional[EnumMappingEventCategory] = Query(None, description="이벤트 매핑 카테고리로 필터링"),
    status_filter: Optional[bool] = Query(None, alias="status", description="상태로 필터링"),
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    이벤트 매핑 목록 조회 (페이지네이션)

    PRD v2.1: group_event → device_group_id (DeviceGroup FK)
    PRD: PRD_CategoryEvent_Refactoring.md - category_event → category_event_mapping

    이벤트 매핑 목록을 페이지네이션하여 조회합니다. 다양한 필터 옵션을 지원합니다.

    **파라미터**:
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    - **name_event**: 이벤트 이름으로 필터링
    - **device_group_id**: DeviceGroup ID로 필터링
    - **category_event_mapping**: 이벤트 매핑 카테고리로 필터링 (센서 조합 타입)
    - **status**: 상태로 필터링

    **Response**: 이벤트 매핑 목록 및 페이지네이션 정보
    """
    # Build query
    query = db.query(EventMapping)

    # Apply filters
    if name_event is not None:
        query = query.filter(EventMapping.name_event == name_event)
    if device_group_id is not None:
        query = query.filter(EventMapping.device_group_id == device_group_id)
    if category_event_mapping is not None:
        query = query.filter(EventMapping.category_event_mapping == category_event_mapping)
    if status_filter is not None:
        query = query.filter(EventMapping.status == status_filter)

    # Get total count
    total = query.count()

    # Calculate pagination
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    # Get paginated results (order by id for stable pagination)
    mappings = query.order_by(EventMapping.id).offset(skip).limit(limit).all()

    # Convert to response format (PRD v2.1: device_group_id 사용, PRD CategoryEvent: category_event_mapping)
    mapping_responses = [
        EventMappingResponse(
            id=m.id,
            name_event=m.name_event,
            device_group_id=m.device_group_id,
            category_event_mapping=m.category_event_mapping,
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


@router.get("/{mapping_id}", response_model=ApiSingleResponse[EventMappingResponse])
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

    # PRD v2.1: device_group_id 사용, PRD CategoryEvent: category_event_mapping
    mapping_response = EventMappingResponse(
        id=mapping.id,
        name_event=mapping.name_event,
        device_group_id=mapping.device_group_id,
        category_event_mapping=mapping.category_event_mapping,
        description=mapping.description,
        status=mapping.status,
        created_at=mapping.created_at,
        updated_at=mapping.updated_at
    )

    return ApiSingleResponse(
        success=True,
        message="Event mapping retrieved successfully",
        data=mapping_response
    )


@router.post("", response_model=ApiSingleResponse[EventMappingResponse], status_code=status.HTTP_201_CREATED)
async def create_event_mapping(
    mapping: EventMappingCreate,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    이벤트 매핑 생성

    새로운 이벤트 매핑을 생성합니다.

    PRD v2.1: group_event → device_group_id (DeviceGroup FK)
    PRD: PRD_CategoryEvent_Refactoring.md - category_event → category_event_mapping

    **Request Body**:
    - **name_event**: 이벤트 이름 (필수)
    - **device_group_id**: DeviceGroup ID (선택)
    - **category_event_mapping**: 이벤트 매핑 카테고리 (필수, 센서 조합 타입)
    - **description**: 설명 (선택)
    - **status**: 상태 (필수)

    **Response**: 생성된 이벤트 매핑 정보
    """
    new_mapping = EventMapping(
        name_event=mapping.name_event,
        device_group_id=mapping.device_group_id,
        category_event_mapping=mapping.category_event_mapping,
        description=mapping.description,
        status=mapping.status
    )

    db.add(new_mapping)
    db.commit()
    db.refresh(new_mapping)

    # ConfigChangeLog: CREATED 로그 기록 (PRD v1.2)
    log_config_change(
        db=db,
        resource_type=EnumConfigResourceType.EVENT_MAPPING,
        resource_id=new_mapping.id,
        resource_name=f"EventMapping-{new_mapping.id} ({new_mapping.name_event})",
        action=EnumConfigActionType.CREATED,
        after_state={"id": new_mapping.id, "name_event": new_mapping.name_event},
        description="EventMapping 생성"
    )

    # PRD v2.1: device_group_id 사용, PRD CategoryEvent: category_event_mapping
    mapping_response = EventMappingResponse(
        id=new_mapping.id,
        name_event=new_mapping.name_event,
        device_group_id=new_mapping.device_group_id,
        category_event_mapping=new_mapping.category_event_mapping,
        description=new_mapping.description,
        status=new_mapping.status,
        created_at=new_mapping.created_at,
        updated_at=new_mapping.updated_at
    )

    return ApiSingleResponse(
        success=True,
        message="Event mapping created successfully",
        data=mapping_response
    )


@router.patch("/{mapping_id}", response_model=ApiSingleResponse[EventMappingResponse])
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

    PRD v2.1: group_event → device_group_id (DeviceGroup FK)
    PRD: PRD_CategoryEvent_Refactoring.md - category_event → category_event_mapping

    **Request Body** (모든 필드 선택):
    - **name_event**: 이벤트 이름
    - **device_group_id**: DeviceGroup ID
    - **category_event_mapping**: 이벤트 매핑 카테고리 (센서 조합 타입)
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

    # ConfigChangeLog: before_state 캡처 (PRD v1.2)
    before_state = model_to_dict(existing_mapping)

    # Update only provided fields
    update_data = mapping.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(existing_mapping, field, value)

    db.commit()
    db.refresh(existing_mapping)

    # ConfigChangeLog: UPDATED 로그 기록 (PRD v1.2)
    after_state = model_to_dict(existing_mapping)
    before_changes, after_changes = get_changed_fields(before_state, after_state)
    if before_changes or after_changes:
        log_config_change(
            db=db,
            resource_type=EnumConfigResourceType.EVENT_MAPPING,
            resource_id=existing_mapping.id,
            resource_name=f"EventMapping-{existing_mapping.id} ({existing_mapping.name_event})",
            action=EnumConfigActionType.UPDATED,
            before_state=before_changes,
            after_state=after_changes,
            description="EventMapping 수정"
        )

    # PRD v2.1: device_group_id 사용, PRD CategoryEvent: category_event_mapping
    mapping_response = EventMappingResponse(
        id=existing_mapping.id,
        name_event=existing_mapping.name_event,
        device_group_id=existing_mapping.device_group_id,
        category_event_mapping=existing_mapping.category_event_mapping,
        description=existing_mapping.description,
        status=existing_mapping.status,
        created_at=existing_mapping.created_at,
        updated_at=existing_mapping.updated_at
    )

    return ApiSingleResponse(
        success=True,
        message="Event mapping updated successfully",
        data=mapping_response
    )


@router.put("/{mapping_id}", response_model=ApiSingleResponse[EventMappingResponse])
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

    PRD v2.1: group_event → device_group_id (DeviceGroup FK)
    PRD: PRD_CategoryEvent_Refactoring.md - category_event → category_event_mapping

    **Request Body** (모든 필드 필수):
    - **name_event**: 이벤트 이름
    - **device_group_id**: DeviceGroup ID
    - **category_event_mapping**: 이벤트 매핑 카테고리 (센서 조합 타입)
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

    # Update all fields (PRD v2.1: device_group_id 사용, PRD CategoryEvent: category_event_mapping)
    existing_mapping.name_event = mapping.name_event
    existing_mapping.device_group_id = mapping.device_group_id
    existing_mapping.category_event_mapping = mapping.category_event_mapping
    existing_mapping.description = mapping.description
    existing_mapping.status = mapping.status

    db.commit()
    db.refresh(existing_mapping)

    # PRD v2.1: device_group_id 사용, PRD CategoryEvent: category_event_mapping
    mapping_response = EventMappingResponse(
        id=existing_mapping.id,
        name_event=existing_mapping.name_event,
        device_group_id=existing_mapping.device_group_id,
        category_event_mapping=existing_mapping.category_event_mapping,
        description=existing_mapping.description,
        status=existing_mapping.status,
        created_at=existing_mapping.created_at,
        updated_at=existing_mapping.updated_at
    )

    return ApiSingleResponse(
        success=True,
        message="Event mapping updated successfully",
        data=mapping_response
    )


@router.delete("/{mapping_id}", response_model=ApiSingleResponse[None])
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

    # ConfigChangeLog: 삭제 전 identifier 캡처 (PRD v1.2)
    deleted_id = mapping.id
    deleted_identifier = {"id": mapping.id, "name_event": mapping.name_event}
    deleted_name = f"EventMapping-{mapping.id} ({mapping.name_event})"

    db.delete(mapping)
    db.commit()

    # ConfigChangeLog: DELETED 로그 기록 (PRD v1.2)
    log_config_change(
        db=db,
        resource_type=EnumConfigResourceType.EVENT_MAPPING,
        resource_id=deleted_id,
        resource_name=deleted_name,
        action=EnumConfigActionType.DELETED,
        before_state=deleted_identifier,
        description="EventMapping 삭제"
    )

    return ApiSingleResponse(
        success=True,
        message="Event mapping deleted successfully",
        data=None
    )
