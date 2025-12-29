"""
CameraEventMapping API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import math

from app.dependencies import get_db
from app.routers.auth import get_current_user_optional
from app.models.integration import CameraEventMapping, CameraEventPreset
from app.schemas.integration import (
    CameraEventMappingCreate,
    CameraEventMappingResponse,
    CameraEventMappingUpdate,
    CameraEventPresetResponse,
    CameraUrls
)
from app.schemas.common import ApiResponse, PaginationMeta
from app.utils.enums import EnumCategoryEvent

router = APIRouter(tags=[])


def _build_urls_object(preset) -> CameraUrls | None:
    """Helper: 모델에서 CameraUrls 객체 생성"""
    if preset.url_live or preset.url_record:
        return CameraUrls(live=preset.url_live, record=preset.url_record)
    return None


def _build_preset_response(p) -> CameraEventPresetResponse:
    """Helper: 모델에서 CameraEventPresetResponse 생성"""
    return CameraEventPresetResponse(
        id=p.id,
        cam_id=p.cam_id,
        urls=_build_urls_object(p),
        category=p.category,
        preset_id=p.preset_id,
        preset_time=p.preset_time,
        home_preset=p.home_preset,
        home_time=p.home_time
    )


@router.get("", response_model=ApiResponse[list[CameraEventMappingResponse]])
async def get_camera_event_mappings(
    page: int = Query(1, ge=1, description="페이지 번호 (기본값: 1)"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수 (기본값: 20, 최대: 100)"),
    group_event: Optional[str] = Query(None, description="이벤트 그룹으로 필터링"),
    category_event: Optional[str] = Query(None, description="이벤트 카테고리로 필터링"),
    status_filter: Optional[bool] = Query(None, alias="status", description="상태로 필터링"),
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    카메라 이벤트 매핑 목록 조회 (페이지네이션)

    카메라 이벤트 매핑 목록을 페이지네이션하여 조회합니다. 다양한 필터 옵션을 지원합니다.

    **파라미터**:
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    - **group_event**: 이벤트 그룹으로 필터링
    - **category_event**: 이벤트 카테고리로 필터링
    - **status**: 상태로 필터링

    **Response**: 카메라 이벤트 매핑 목록 및 페이지네이션 정보
    """
    query = db.query(CameraEventMapping)

    # Apply filters
    if group_event is not None:
        query = query.filter(CameraEventMapping.group_event == group_event)
    if category_event is not None:
        try:
            category_enum_value = EnumCategoryEvent(category_event)
            query = query.filter(CameraEventMapping.category_event == category_enum_value)
        except ValueError:
            pass  # Invalid enum value, ignore filter
    if status_filter is not None:
        query = query.filter(CameraEventMapping.status == status_filter)

    # Get total count
    total = query.count()

    # Calculate pagination
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    # Get paginated results
    mappings = query.offset(skip).limit(limit).all()

    # Convert to response format
    mapping_responses = [
        CameraEventMappingResponse(
            id=m.id,
            name_event=m.name_event,
            group_event=m.group_event,
            category_event=m.category_event.value if isinstance(m.category_event, EnumCategoryEvent) else m.category_event,
            description=m.description,
            status=m.status,
            camera_presets=[_build_preset_response(p) for p in m.camera_presets],
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
        message="Camera event mappings retrieved successfully",
        data=mapping_responses,
        pagination=pagination
    )


@router.get("/{mapping_id}", response_model=ApiResponse[CameraEventMappingResponse])
async def get_camera_event_mapping(
    mapping_id: int,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    카메라 이벤트 매핑 단건 조회

    특정 카메라 이벤트 매핑의 상세 정보를 조회합니다.

    **파라미터**:
    - **mapping_id**: 카메라 이벤트 매핑 ID (Path Parameter)

    **Response**: 카메라 이벤트 매핑 상세 정보

    **Error**:
    - 404: 카메라 이벤트 매핑을 찾을 수 없음
    """
    mapping = db.query(CameraEventMapping).filter(CameraEventMapping.id == mapping_id).first()

    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera event mapping with id {mapping_id} not found"
        )

    mapping_response = CameraEventMappingResponse(
        id=mapping.id,
        name_event=mapping.name_event,
        group_event=mapping.group_event,
        category_event=mapping.category_event.value if isinstance(mapping.category_event, EnumCategoryEvent) else mapping.category_event,
        description=mapping.description,
        status=mapping.status,
        camera_presets=[_build_preset_response(p) for p in mapping.camera_presets],
        created_at=mapping.created_at,
        updated_at=mapping.updated_at
    )

    return ApiResponse(
        success=True,
        message="Camera event mapping retrieved successfully",
        data=mapping_response
    )


@router.post("", response_model=ApiResponse[CameraEventMappingResponse], status_code=status.HTTP_201_CREATED)
async def create_camera_event_mapping(
    mapping: CameraEventMappingCreate,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    카메라 이벤트 매핑 생성

    새로운 카메라 이벤트 매핑을 생성합니다.

    **Request Body**:
    - **name_event**: 이벤트 이름 (필수)
    - **group_event**: 이벤트 그룹 (필수)
    - **category_event**: 이벤트 카테고리 (필수)
    - **description**: 설명 (선택)
    - **status**: 상태 (필수)
    - **camera_presets**: 카메라 프리셋 목록 (선택)

    **Response**: 생성된 카메라 이벤트 매핑 정보

    **Error**:
    - 422: 유효하지 않은 category_event 값
    """
    # Convert category_event string to enum
    try:
        category_event_enum = EnumCategoryEvent(mapping.category_event)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid category_event value: {mapping.category_event}"
        )

    new_mapping = CameraEventMapping(
        name_event=mapping.name_event,
        group_event=mapping.group_event,  # Plain string
        category_event=category_event_enum,
        description=mapping.description,
        status=mapping.status
    )

    db.add(new_mapping)
    db.commit()
    db.refresh(new_mapping)

    # Create presets if provided
    for preset_data in mapping.camera_presets:
        preset = CameraEventPreset(
            mapping_id=new_mapping.id,
            cam_id=preset_data.cam_id,
            url_live=preset_data.urls.live if preset_data.urls else None,
            url_record=preset_data.urls.record if preset_data.urls else None,
            category=preset_data.category,
            preset_id=preset_data.preset_id,
            preset_time=preset_data.preset_time,
            home_preset=preset_data.home_preset,
            home_time=preset_data.home_time
        )
        db.add(preset)

    if mapping.camera_presets:
        db.commit()
        db.refresh(new_mapping)

    mapping_response = CameraEventMappingResponse(
        id=new_mapping.id,
        name_event=new_mapping.name_event,
        group_event=new_mapping.group_event,
        category_event=new_mapping.category_event.value if isinstance(new_mapping.category_event, EnumCategoryEvent) else new_mapping.category_event,
        description=new_mapping.description,
        status=new_mapping.status,
        camera_presets=[_build_preset_response(p) for p in new_mapping.camera_presets],
        created_at=new_mapping.created_at,
        updated_at=new_mapping.updated_at
    )

    return ApiResponse(
        success=True,
        message="Camera event mapping created successfully",
        data=mapping_response
    )


@router.patch("/{mapping_id}", response_model=ApiResponse[CameraEventMappingResponse])
async def update_camera_event_mapping_partial(
    mapping_id: int,
    mapping: CameraEventMappingUpdate,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    카메라 이벤트 매핑 부분 수정 (PATCH)

    카메라 이벤트 매핑의 일부 필드만 수정합니다. 제공된 필드만 업데이트됩니다.

    **파라미터**:
    - **mapping_id**: 카메라 이벤트 매핑 ID (Path Parameter)

    **Request Body** (모든 필드 선택):
    - **name_event**: 이벤트 이름
    - **group_event**: 이벤트 그룹
    - **category_event**: 이벤트 카테고리
    - **description**: 설명
    - **status**: 상태
    - **camera_presets**: 카메라 프리셋 목록

    **Response**: 수정된 카메라 이벤트 매핑 정보

    **Error**:
    - 404: 카메라 이벤트 매핑을 찾을 수 없음
    - 422: 유효하지 않은 category_event 값
    """
    existing_mapping = db.query(CameraEventMapping).filter(CameraEventMapping.id == mapping_id).first()

    if not existing_mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera event mapping with id {mapping_id} not found"
        )

    # Update only provided fields
    update_data = mapping.model_dump(exclude_unset=True)

    # Handle camera_presets separately
    camera_presets_data = update_data.pop("camera_presets", None)

    for field, value in update_data.items():
        if field == "category_event" and value is not None:
            try:
                value = EnumCategoryEvent(value)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid category_event value: {value}"
                )
        setattr(existing_mapping, field, value)

    # Update presets if provided (replace all)
    if camera_presets_data is not None:
        # Delete existing presets
        db.query(CameraEventPreset).filter(
            CameraEventPreset.mapping_id == mapping_id
        ).delete()

        # Create new presets
        for preset_data in camera_presets_data:
            urls_data = preset_data.get("urls")
            preset = CameraEventPreset(
                mapping_id=mapping_id,
                cam_id=preset_data["cam_id"],
                url_live=urls_data.get("live") if urls_data else None,
                url_record=urls_data.get("record") if urls_data else None,
                category=preset_data["category"],
                preset_id=preset_data.get("preset_id"),
                preset_time=preset_data.get("preset_time", 0),
                home_preset=preset_data.get("home_preset", 0),
                home_time=preset_data.get("home_time", 0)
            )
            db.add(preset)

    db.commit()
    db.refresh(existing_mapping)

    mapping_response = CameraEventMappingResponse(
        id=existing_mapping.id,
        name_event=existing_mapping.name_event,
        group_event=existing_mapping.group_event,
        category_event=existing_mapping.category_event.value if isinstance(existing_mapping.category_event, EnumCategoryEvent) else existing_mapping.category_event,
        description=existing_mapping.description,
        status=existing_mapping.status,
        camera_presets=[_build_preset_response(p) for p in existing_mapping.camera_presets],
        created_at=existing_mapping.created_at,
        updated_at=existing_mapping.updated_at
    )

    return ApiResponse(
        success=True,
        message="Camera event mapping updated successfully",
        data=mapping_response
    )


@router.put("/{mapping_id}", response_model=ApiResponse[CameraEventMappingResponse])
async def update_camera_event_mapping_full(
    mapping_id: int,
    mapping: CameraEventMappingCreate,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    카메라 이벤트 매핑 전체 수정 (PUT)

    카메라 이벤트 매핑의 모든 필드를 교체합니다. 모든 필드가 필수입니다.

    **파라미터**:
    - **mapping_id**: 카메라 이벤트 매핑 ID (Path Parameter)

    **Request Body** (모든 필드 필수):
    - **name_event**: 이벤트 이름
    - **group_event**: 이벤트 그룹
    - **category_event**: 이벤트 카테고리
    - **description**: 설명
    - **status**: 상태
    - **camera_presets**: 카메라 프리셋 목록

    **Response**: 수정된 카메라 이벤트 매핑 정보

    **Error**:
    - 404: 카메라 이벤트 매핑을 찾을 수 없음
    - 422: 유효하지 않은 category_event 값
    """
    existing_mapping = db.query(CameraEventMapping).filter(CameraEventMapping.id == mapping_id).first()

    if not existing_mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera event mapping with id {mapping_id} not found"
        )

    # Convert category_event string to enum
    try:
        category_event_enum = EnumCategoryEvent(mapping.category_event)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid category_event value: {mapping.category_event}"
        )

    # Update all fields
    existing_mapping.name_event = mapping.name_event
    existing_mapping.group_event = mapping.group_event  # Plain string
    existing_mapping.category_event = category_event_enum
    existing_mapping.description = mapping.description
    existing_mapping.status = mapping.status

    # Delete existing presets and create new ones
    db.query(CameraEventPreset).filter(
        CameraEventPreset.mapping_id == mapping_id
    ).delete()

    for preset_data in mapping.camera_presets:
        preset = CameraEventPreset(
            mapping_id=mapping_id,
            cam_id=preset_data.cam_id,
            url_live=preset_data.urls.live if preset_data.urls else None,
            url_record=preset_data.urls.record if preset_data.urls else None,
            category=preset_data.category,
            preset_id=preset_data.preset_id,
            preset_time=preset_data.preset_time,
            home_preset=preset_data.home_preset,
            home_time=preset_data.home_time
        )
        db.add(preset)

    db.commit()
    db.refresh(existing_mapping)

    mapping_response = CameraEventMappingResponse(
        id=existing_mapping.id,
        name_event=existing_mapping.name_event,
        group_event=existing_mapping.group_event,
        category_event=existing_mapping.category_event.value if isinstance(existing_mapping.category_event, EnumCategoryEvent) else existing_mapping.category_event,
        description=existing_mapping.description,
        status=existing_mapping.status,
        camera_presets=[_build_preset_response(p) for p in existing_mapping.camera_presets],
        created_at=existing_mapping.created_at,
        updated_at=existing_mapping.updated_at
    )

    return ApiResponse(
        success=True,
        message="Camera event mapping updated successfully",
        data=mapping_response
    )


@router.delete("/{mapping_id}", response_model=ApiResponse[dict])
async def delete_camera_event_mapping(
    mapping_id: int,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    카메라 이벤트 매핑 삭제

    특정 카메라 이벤트 매핑을 삭제합니다.

    **파라미터**:
    - **mapping_id**: 카메라 이벤트 매핑 ID (Path Parameter)

    **Response**: 삭제 확인 정보

    **Error**:
    - 404: 카메라 이벤트 매핑을 찾을 수 없음
    """
    mapping = db.query(CameraEventMapping).filter(CameraEventMapping.id == mapping_id).first()

    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera event mapping with id {mapping_id} not found"
        )

    db.delete(mapping)
    db.commit()

    return ApiResponse(
        success=True,
        message="Camera event mapping deleted successfully",
        data={"id": mapping_id}
    )
