"""
Camera API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
import math

from app.dependencies import get_db
from app.routers.auth import get_current_user_optional
from app.models.device import Camera, EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType
from app.models.device_group import DeviceGroup, DeviceGroupMapping
from app.utils.enums import EnumDeviceCategory, EnumConfigResourceType, EnumConfigActionType
from app.schemas.device import CameraCreate, CameraResponse, CameraUpdate, HardwareSpec, Geolocation, DeviceGroupNestedResponse, CameraUrls, CameraWithPresetsResponse
from app.schemas.device_group import DeviceGroupResponse
from app.schemas.common import ApiResponse, PaginationMeta
from app.schemas.camera_preset import CameraPresetNestedResponse, ROIListNestedResponse
from app.models.camera_preset import CameraPreset, ROI
from app.services.config_log_service import log_config_change, get_identifier, get_changed_fields, model_to_dict

router = APIRouter(tags=["Cameras"])


def _get_device_groups_nested(db: Session, device_id: int, category_device: EnumDeviceCategory = EnumDeviceCategory.CAMERA) -> List[DeviceGroupNestedResponse]:
    """Get device groups for a camera (v2.4: timestamp 제외)"""
    mappings = db.query(DeviceGroupMapping).filter(
        DeviceGroupMapping.device_id == device_id,
        DeviceGroupMapping.category_device == category_device
    ).all()

    groups = []
    for mapping in mappings:
        group = db.query(DeviceGroup).filter(DeviceGroup.id == mapping.group_id).first()
        if group:
            device_count = db.query(DeviceGroupMapping).filter(
                DeviceGroupMapping.group_id == group.id
            ).count()
            groups.append(DeviceGroupNestedResponse(
                id=group.id,
                name=group.name,
                description=group.description,
                device_count=device_count
            ))
    return groups


def _update_device_group_mappings(db: Session, device_id: int, group_ids: List[int], category_device: EnumDeviceCategory = EnumDeviceCategory.CAMERA):
    """Update device group mappings for a camera"""
    # Remove existing mappings
    db.query(DeviceGroupMapping).filter(
        DeviceGroupMapping.device_id == device_id,
        DeviceGroupMapping.category_device == category_device
    ).delete()

    # Create new mappings
    for group_id in group_ids:
        # Verify group exists
        group = db.query(DeviceGroup).filter(DeviceGroup.id == group_id).first()
        if group:
            mapping = DeviceGroupMapping(
                device_id=device_id,
                category_device=category_device,
                group_id=group_id
            )
            db.add(mapping)


def _camera_to_response(camera: Camera, db: Session) -> CameraResponse:
    """Convert Camera model to CameraResponse schema with extended fields and device_groups"""
    # Convert hardware_spec dict to HardwareSpec if exists
    hw_spec = None
    if camera.hardware_spec:
        hw_spec = HardwareSpec(**camera.hardware_spec)

    # Convert geolocation dict to Geolocation if exists
    geo = None
    if camera.geolocation:
        geo = Geolocation(**camera.geolocation)

    # Convert urls dict to CameraUrls if exists (PRD_Camera_Urls_JsonB.md)
    urls = None
    if camera.urls:
        urls = CameraUrls(**camera.urls)

    # v2.4: Nested Response 규칙 적용 - device_groups에서 timestamp 제외
    device_groups = _get_device_groups_nested(db, camera.id, EnumDeviceCategory.CAMERA)

    return CameraResponse(
        id=camera.id,
        number_device=camera.number_device,
        group_device=camera.group_device,
        name_device=camera.name_device,
        type_device=camera.type_device.value,
        version=camera.version,
        status=camera.status.value,
        is_enable=camera.is_enable,
        ip_address=camera.ip_address,
        ip_port=camera.ip_port,
        user_name=camera.user_name,
        user_password=camera.user_password,
        mode=camera.mode.value,
        category=camera.category.value,
        is_record=camera.is_record,
        hardware_spec=hw_spec,
        geolocation=geo,
        urls=urls,
        created_at=camera.created_at,
        updated_at=camera.updated_at,
        device_groups=device_groups
    )


@router.get("", response_model=ApiResponse[list[CameraResponse]])
async def get_cameras(
    page: int = Query(1, ge=1, description="페이지 번호 (기본값: 1)"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수 (기본값: 20, 최대: 100)"),
    group_device: Optional[int] = Query(None, description="장치 그룹으로 필터링 (레거시 1:1)"),
    group_id: Optional[int] = Query(None, description="DeviceGroup ID로 필터링 (N:N 관계)"),
    type_device: Optional[str] = Query(None, description="장치 유형으로 필터링"),
    status: Optional[str] = Query(None, description="상태로 필터링"),
    mode: Optional[str] = Query(None, description="카메라 모드로 필터링"),
    category: Optional[str] = Query(None, description="카메라 카테고리로 필터링"),
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    카메라 목록 조회 (페이지네이션)

    카메라 목록을 페이지네이션하여 조회합니다. 다양한 필터 옵션을 지원합니다.

    **파라미터**:
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    - **group_device**: 장치 그룹으로 필터링 - 레거시 1:1 관계
    - **group_id**: DeviceGroup ID로 필터링 - N:N 관계
    - **type_device**: 장치 유형으로 필터링
    - **status**: 상태로 필터링
    - **mode**: 카메라 모드로 필터링
    - **category**: 카메라 카테고리로 필터링

    **Response**: 카메라 목록 및 페이지네이션 정보
    """
    # Build query
    query = db.query(Camera)

    # Apply filters
    if group_device is not None:
        query = query.filter(Camera.group_device == group_device)
    if group_id is not None:
        # N:N filtering via DeviceGroupMapping junction table
        subquery = db.query(DeviceGroupMapping.device_id).filter(
            DeviceGroupMapping.group_id == group_id,
            DeviceGroupMapping.category_device == EnumDeviceCategory.CAMERA
        ).subquery()
        query = query.filter(Camera.id.in_(subquery))
    if type_device is not None:
        query = query.filter(Camera.type_device == type_device)
    if status is not None:
        query = query.filter(Camera.status == status)
    if mode is not None:
        query = query.filter(Camera.mode == mode)
    if category is not None:
        query = query.filter(Camera.category == category)

    # Get total count
    total = query.count()

    # Calculate pagination
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    # Get paginated results
    cameras = query.offset(skip).limit(limit).all()

    # Convert to response format using helper function
    camera_responses = [_camera_to_response(c, db) for c in cameras]

    pagination = PaginationMeta(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages
    )

    return ApiResponse(
        success=True,
        message="Cameras retrieved successfully",
        data=camera_responses,
        pagination=pagination
    )


@router.get("/{camera_id}")
async def get_camera(
    camera_id: int,
    include_presets: bool = Query(False, description="프리셋 정보 포함 여부 (기본값: false)"),
    include_rois: bool = Query(False, description="ROI 정보 포함 여부 (기본값: false, include_presets=true 필요)"),
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    카메라 단건 조회

    특정 카메라의 상세 정보를 조회합니다.

    **파라미터**:
    - **camera_id**: 카메라 ID (Path Parameter)
    - **include_presets**: 프리셋 정보 포함 여부 (기본값: false)
    - **include_rois**: ROI 정보 포함 여부 (기본값: false, include_presets=true일 때만 유효)

    **Response**: 카메라 상세 정보 (include_presets=true 시 presets 포함)

    **Error**:
    - 404: 카메라를 찾을 수 없음
    """
    camera = db.query(Camera).filter(Camera.id == camera_id).first()

    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with id {camera_id} not found"
        )

    # include_rois=true implies include_presets=true
    if include_rois:
        include_presets = True

    # If include_presets is requested, return CameraWithPresetsResponse
    if include_presets:
        camera_response = _camera_to_response(camera, db)
        presets = _get_camera_presets_nested(db, camera_id, include_rois)

        return ApiResponse(
            success=True,
            message="Camera retrieved successfully",
            data=CameraWithPresetsResponse(
                **camera_response.model_dump(),
                presets=presets
            )
        )

    return ApiResponse(
        success=True,
        message="Camera retrieved successfully",
        data=_camera_to_response(camera, db)
    )


def _get_camera_presets_nested(db: Session, camera_id: int, include_rois: bool = False) -> List[CameraPresetNestedResponse]:
    """Get camera presets as nested response (v2.11: for include_presets query param)"""
    from app.models.camera_preset import XyPoint  # Import for point_count query

    presets = db.query(CameraPreset).filter(CameraPreset.camera_id == camera_id).all()

    result = []
    for preset in presets:
        rois_list = []
        if include_rois:
            rois = db.query(ROI).filter(ROI.preset_id == preset.id).all()
            for roi in rois:
                # Use explicit query instead of lazy-loaded dynamic relationship
                point_count = db.query(XyPoint).filter(XyPoint.roi_id == roi.id).count()
                rois_list.append(ROIListNestedResponse(
                    id=roi.id,
                    preset_id=roi.preset_id,
                    name=roi.name,
                    resolution_width=roi.resolution_width,
                    resolution_height=roi.resolution_height,
                    is_enable=roi.is_enable,
                    point_count=point_count
                ))

        roi_count = db.query(ROI).filter(ROI.preset_id == preset.id).count()

        result.append(CameraPresetNestedResponse(
            id=preset.id,
            camera_id=preset.camera_id,
            preset_index=preset.preset_index,
            preset_name=preset.preset_name,
            touring_time=preset.touring_time,
            roi_count=roi_count,
            rois=rois_list
        ))

    return result


@router.post("", response_model=ApiResponse[CameraResponse], status_code=status.HTTP_201_CREATED)
async def create_camera(
    camera_data: CameraCreate,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    카메라 생성

    새로운 카메라를 생성합니다.

    **Request Body**:
    - **number_device**: 장치 번호 (필수)
    - **group_device**: 장치 그룹 (필수)
    - **name_device**: 장치 이름 (필수)
    - **type_device**: 장치 유형 (필수)
    - **version**: 버전 (필수)
    - **status**: 상태 (필수)
    - **ip_address**: IP 주소 (필수)
    - **ip_port**: IP 포트 (필수)
    - **user_name**: 사용자 이름 (선택)
    - **user_password**: 사용자 비밀번호 (선택)
    - **urls**: 카메라 URL 정보 JSONB (선택) - PRD_Camera_Urls_JsonB.md
    - **mode**: 카메라 모드 (필수)
    - **category**: 카메라 카테고리 (필수)

    **Response**: 생성된 카메라 정보

    **Error**:
    - 422: 유효하지 않은 enum 값
    """
    # Convert string enum values to enum types
    try:
        device_type = EnumDeviceType(camera_data.type_device)
        device_status = EnumDeviceStatus(camera_data.status)
        camera_mode = EnumCameraMode(camera_data.mode)
        camera_category = EnumCameraType(camera_data.category)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid enum value: {str(e)}"
        )

    # Convert extended fields to dict for JSON storage
    hw_spec_dict = camera_data.hardware_spec.model_dump(exclude_none=True) if camera_data.hardware_spec else None
    geo_dict = camera_data.geolocation.model_dump(exclude_none=True) if camera_data.geolocation else None
    # PRD_Camera_Urls_JsonB.md: Convert urls to dict for JSONB storage
    urls_dict = camera_data.urls.model_dump(exclude_none=True) if camera_data.urls else None

    # Create new camera with extended fields
    new_camera = Camera(
        number_device=camera_data.number_device,
        group_device=camera_data.group_device,
        name_device=camera_data.name_device,
        type_device=device_type,
        version=camera_data.version,
        status=device_status,
        is_enable=camera_data.is_enable,
        ip_address=camera_data.ip_address,
        ip_port=camera_data.ip_port,
        user_name=camera_data.user_name,
        user_password=camera_data.user_password,
        urls=urls_dict,
        mode=camera_mode,
        category=camera_category,
        is_record=camera_data.is_record,
        hardware_spec=hw_spec_dict,
        geolocation=geo_dict
    )

    db.add(new_camera)
    db.commit()
    db.refresh(new_camera)

    # Handle group_ids if provided (N:N relationship)
    if camera_data.group_ids:
        _update_device_group_mappings(db, new_camera.id, camera_data.group_ids, "camera")
        db.commit()

    # ConfigChangeLog: CREATED 로깅 (PRD v1.2)
    log_config_change(
        db=db,
        resource_type=EnumConfigResourceType.CAMERA,
        resource_id=new_camera.id,
        resource_name=f"Camera-{new_camera.id} ({new_camera.name_device})",
        action=EnumConfigActionType.CREATED,
        after_state=get_identifier(new_camera),
        description="Camera 생성"
    )

    return ApiResponse(
        success=True,
        message="Camera created successfully",
        data=_camera_to_response(new_camera, db)
    )


@router.patch("/{camera_id}", response_model=ApiResponse[CameraResponse])
async def update_camera(
    camera_id: int,
    camera_data: CameraUpdate,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    카메라 부분 수정 (PATCH)

    카메라의 일부 필드만 수정합니다. 제공된 필드만 업데이트됩니다.

    **파라미터**:
    - **camera_id**: 카메라 ID (Path Parameter)

    **Request Body** (모든 필드 선택):
    - **number_device**: 장치 번호
    - **group_device**: 장치 그룹
    - **name_device**: 장치 이름
    - **type_device**: 장치 유형
    - **version**: 버전
    - **status**: 상태
    - **ip_address**: IP 주소
    - **ip_port**: IP 포트
    - **user_name**: 사용자 이름
    - **user_password**: 사용자 비밀번호
    - **urls**: 카메라 URL 정보 JSONB (PRD_Camera_Urls_JsonB.md)
    - **mode**: 카메라 모드
    - **category**: 카메라 카테고리

    **Response**: 수정된 카메라 정보

    **Error**:
    - 404: 카메라를 찾을 수 없음
    - 422: 유효하지 않은 enum 값
    """
    camera = db.query(Camera).filter(Camera.id == camera_id).first()

    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with id {camera_id} not found"
        )

    # ConfigChangeLog: 변경 전 상태 캡처
    before_state = model_to_dict(camera)

    # Update fields if provided
    update_data = camera_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if field == "type_device" and value is not None:
            try:
                value = EnumDeviceType(value)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid type_device value: {value}"
                )
        elif field == "status" and value is not None:
            try:
                value = EnumDeviceStatus(value)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid status value: {value}"
                )
        elif field == "mode" and value is not None:
            try:
                value = EnumCameraMode(value)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid mode value: {value}"
                )
        elif field == "category" and value is not None:
            try:
                value = EnumCameraType(value)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid category value: {value}"
                )
        elif field == "hardware_spec" and value is not None:
            # Convert Pydantic model to dict for JSON storage
            value = value if isinstance(value, dict) else value
        elif field == "geolocation" and value is not None:
            # Convert Pydantic model to dict for JSON storage
            value = value if isinstance(value, dict) else value
        elif field == "urls" and value is not None:
            # PRD_Camera_Urls_JsonB.md: Convert Pydantic model to dict for JSONB storage
            value = value if isinstance(value, dict) else value
        elif field == "group_ids":
            # Handle group_ids separately (N:N relationship)
            if value is not None:
                _update_device_group_mappings(db, camera_id, value, "camera")
            continue

        setattr(camera, field, value)

    db.commit()
    db.refresh(camera)

    # ConfigChangeLog: UPDATED 로깅 (PRD v1.2 - 변경된 필드만 저장)
    after_state = model_to_dict(camera)
    before_changes, after_changes = get_changed_fields(before_state, after_state)
    if before_changes or after_changes:
        log_config_change(
            db=db,
            resource_type=EnumConfigResourceType.CAMERA,
            resource_id=camera.id,
            resource_name=f"Camera-{camera.id} ({camera.name_device})",
            action=EnumConfigActionType.UPDATED,
            before_state=before_changes,
            after_state=after_changes,
            description="Camera 수정"
        )

    return ApiResponse(
        success=True,
        message="Camera updated successfully",
        data=_camera_to_response(camera, db)
    )


@router.put("/{camera_id}", response_model=ApiResponse[CameraResponse])
async def replace_camera(
    camera_id: int,
    camera_data: CameraCreate,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    카메라 전체 수정 (PUT)

    카메라의 모든 필드를 교체합니다. 모든 필드가 필수입니다.

    **파라미터**:
    - **camera_id**: 카메라 ID (Path Parameter)

    **Request Body** (모든 필드 필수):
    - **number_device**: 장치 번호
    - **group_device**: 장치 그룹
    - **name_device**: 장치 이름
    - **type_device**: 장치 유형
    - **version**: 버전
    - **status**: 상태
    - **ip_address**: IP 주소
    - **ip_port**: IP 포트
    - **user_name**: 사용자 이름
    - **user_password**: 사용자 비밀번호
    - **urls**: 카메라 URL 정보 JSONB (PRD_Camera_Urls_JsonB.md)
    - **mode**: 카메라 모드
    - **category**: 카메라 카테고리

    **Response**: 수정된 카메라 정보

    **Error**:
    - 404: 카메라를 찾을 수 없음
    - 422: 유효하지 않은 enum 값
    """
    camera = db.query(Camera).filter(Camera.id == camera_id).first()

    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with id {camera_id} not found"
        )

    # Convert string enum values to enum types
    try:
        device_type = EnumDeviceType(camera_data.type_device)
        device_status = EnumDeviceStatus(camera_data.status)
        camera_mode = EnumCameraMode(camera_data.mode)
        camera_category = EnumCameraType(camera_data.category)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid enum value: {str(e)}"
        )

    # Convert extended fields to dict for JSON storage
    hw_spec_dict = camera_data.hardware_spec.model_dump(exclude_none=True) if camera_data.hardware_spec else None
    geo_dict = camera_data.geolocation.model_dump(exclude_none=True) if camera_data.geolocation else None
    # PRD_Camera_Urls_JsonB.md: Convert urls to dict for JSONB storage
    urls_dict = camera_data.urls.model_dump(exclude_none=True) if camera_data.urls else None

    # Replace all fields (PUT = full replacement)
    camera.number_device = camera_data.number_device
    camera.group_device = camera_data.group_device
    camera.name_device = camera_data.name_device
    camera.type_device = device_type
    camera.version = camera_data.version
    camera.status = device_status
    camera.is_enable = camera_data.is_enable
    camera.ip_address = camera_data.ip_address
    camera.ip_port = camera_data.ip_port
    camera.user_name = camera_data.user_name
    camera.user_password = camera_data.user_password
    camera.urls = urls_dict
    camera.mode = camera_mode
    camera.category = camera_category
    camera.is_record = camera_data.is_record
    camera.hardware_spec = hw_spec_dict
    camera.geolocation = geo_dict

    db.commit()
    db.refresh(camera)

    # Handle group_ids if provided (N:N relationship)
    if camera_data.group_ids is not None:
        _update_device_group_mappings(db, camera.id, camera_data.group_ids, "camera")
        db.commit()

    return ApiResponse(
        success=True,
        message="Camera replaced successfully",
        data=_camera_to_response(camera, db)
    )


@router.delete("/{camera_id}", response_model=ApiResponse[None])
async def delete_camera(
    camera_id: int,
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    카메라 삭제

    특정 카메라를 삭제합니다.

    **파라미터**:
    - **camera_id**: 카메라 ID (Path Parameter)

    **Response**: 삭제 확인 정보

    **Error**:
    - 404: 카메라를 찾을 수 없음
    """
    camera = db.query(Camera).filter(Camera.id == camera_id).first()

    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with id {camera_id} not found"
        )

    # ConfigChangeLog: 삭제 전 식별 정보 캡처
    deleted_identifier = get_identifier(camera)
    resource_name = f"Camera-{camera.id} ({camera.name_device})"

    # Delete associated device group mappings first (no FK cascade for polymorphic relation)
    db.query(DeviceGroupMapping).filter(
        DeviceGroupMapping.device_id == camera_id,
        DeviceGroupMapping.category_device == EnumDeviceCategory.CAMERA
    ).delete()

    db.delete(camera)
    db.commit()

    # ConfigChangeLog: DELETED 로깅 (PRD v1.2)
    log_config_change(
        db=db,
        resource_type=EnumConfigResourceType.CAMERA,
        resource_id=camera_id,
        resource_name=resource_name,
        action=EnumConfigActionType.DELETED,
        before_state=deleted_identifier,
        description="Camera 삭제"
    )

    return ApiResponse(
        success=True,
        message="Camera deleted successfully",
        data=None
    )
