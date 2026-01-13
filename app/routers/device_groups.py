"""
DeviceGroup API endpoints
PRD: PRD_Device_Structure_Refactoring.md - Phase 6
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional
import math

from app.dependencies import get_db
from app.routers.auth import get_current_user_optional
from app.models.device_group import DeviceGroup, DeviceGroupMapping
from app.utils.enums import EnumDeviceCategory
from app.models.device import Device, Controller, Sensor, Camera
from app.schemas.device_group import (
    DeviceGroupCreate,
    DeviceGroupUpdate,
    DeviceGroupResponse,
    DeviceGroupDetailResponse,
    DeviceAssignRequest,
    DeviceAssignResponse,
    DeviceRemoveResponse,
    ControllerSummary,
    SensorSummary,
    CameraSummary,
)
from app.schemas.common import ApiResponse, PaginationMeta, ValidationErrorResponse

router = APIRouter(prefix="/devices/groups", tags=["DeviceGroups"])


@router.get(
    "",
    response_model=ApiResponse[list[DeviceGroupResponse]],
    responses={
        200: {
            "description": "디바이스 그룹 목록 조회 성공",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "디바이스 그룹 목록 조회 성공",
                        "data": [
                            {"id": 1, "name": "GOP 1구역", "description": "GOP 1구역 장비 그룹", "device_count": 5, "created_at": "2025-01-01T00:00:00.000Z", "updated_at": "2025-01-01T00:00:00.000Z"},
                            {"id": 2, "name": "GOP 2구역", "description": "GOP 2구역 장비 그룹", "device_count": 3, "created_at": "2025-01-02T00:00:00.000Z", "updated_at": "2025-01-02T00:00:00.000Z"}
                        ],
                        "pagination": {"page": 1, "limit": 20, "total": 2, "total_pages": 1},
                        "meta": {"timestamp": "2025-01-10T10:30:00.000Z", "request_id": "550e8400-e29b-41d4-a716-446655440000"}
                    }
                }
            }
        },
        422: {
            "model": ValidationErrorResponse,
            "description": "Validation Error - 잘못된 쿼리 파라미터",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "Validation error",
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "details": [
                                {"field": "page", "message": "Page must be greater than 0"},
                                {"field": "limit", "message": "Limit must be between 1 and 100"}
                            ]
                        }
                    }
                }
            }
        }
    }
)
async def get_device_groups(
    page: int = Query(1, ge=1, description="페이지 번호 (기본값: 1)"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수 (기본값: 20, 최대: 100)"),
    name: Optional[str] = Query(None, description="이름으로 필터링 (부분 검색)"),
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    디바이스 그룹 목록 조회 (페이지네이션)

    디바이스 그룹 목록을 페이지네이션하여 조회합니다.
    이름으로 필터링할 수 있습니다.

    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    - **name**: 이름으로 부분 검색 (선택)

    **Response**: 디바이스 그룹 목록 및 페이지네이션 정보
    """
    query = db.query(DeviceGroup)

    if name:
        query = query.filter(DeviceGroup.name.contains(name))

    total = query.count()
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    groups = query.offset(skip).limit(limit).all()

    group_responses = []
    for g in groups:
        group_responses.append(DeviceGroupResponse(
            id=g.id,
            name=g.name,
            description=g.description,
            device_count=g.device_mappings.count(),
            created_at=g.created_at,
            updated_at=g.updated_at
        ))

    pagination = PaginationMeta(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages
    )

    return ApiResponse(
        success=True,
        data=group_responses,
        pagination=pagination,
        message="디바이스 그룹 목록 조회 성공"
    )


@router.get(
    "/{group_id}",
    responses={
        200: {
            "description": "디바이스 그룹 상세 조회 성공",
            "content": {
                "application/json": {
                    "examples": {
                        "include_devices_true": {
                            "summary": "include_devices=true (기본값) - 디바이스 목록 포함",
                            "value": {
                                "success": True,
                                "message": "디바이스 그룹 조회 성공",
                                "data": {
                                    "id": 1,
                                    "name": "GOP 1구역",
                                    "description": "GOP 1구역 장비 그룹",
                                    "device_count": 3,
                                    "created_at": "2025-01-01T00:00:00.000Z",
                                    "updated_at": "2025-01-01T00:00:00.000Z",
                                    "devices": [
                                        {
                                            "id": 1,
                                            "number_device": 1,
                                            "group_device": 1,
                                            "name_device": "Controller-A",
                                            "type_device": "Controller",
                                            "version": "v2.1.0",
                                            "status": "ACTIVATED",
                                            "ip_address": "192.168.1.100",
                                            "ip_port": 8001,
                                            "geolocation": {
                                                "location": "GOP 1구역 전방 초소",
                                                "latitude": 38.1234,
                                                "longitude": 127.5678
                                            },
                                            "device_groups": [
                                                {"id": 1, "name": "GOP 1구역", "description": "GOP 1구역 장비 그룹", "device_count": 5}
                                            ]
                                        },
                                        {
                                            "id": 101,
                                            "number_device": 1,
                                            "group_device": 1,
                                            "name_device": "Sensor-A-1",
                                            "type_device": "Multi",
                                            "version": "v1.5.0",
                                            "status": "ACTIVATED",
                                            "controller_id": 1,
                                            "geolocation": {
                                                "location": "GOP 1구역 전방 초소",
                                                "latitude": 38.1234,
                                                "longitude": 127.5678
                                            },
                                            "device_groups": [
                                                {"id": 1, "name": "GOP 1구역", "description": "GOP 1구역 장비 그룹", "device_count": 5}
                                            ]
                                        },
                                        {
                                            "id": 201,
                                            "number_device": 1,
                                            "group_device": 1,
                                            "name_device": "Camera-A-1",
                                            "type_device": "IpCamera",
                                            "version": "v1.0.0",
                                            "status": "ACTIVATED",
                                            "ip_address": "192.168.1.200",
                                            "ip_port": 80,
                                            "user_name": "admin",
                                            "user_password": "admin1234",
                                            "mode": "RTSP",
                                            "camera_category": "PTZ",
                                            "is_record": True,
                                            "urls": {
                                                "streams": {
                                                    "rtsp": {"main": "rtsp://192.168.1.200:554/stream1"}
                                                }
                                            },
                                            "hardware_spec": {
                                                "manufacturer": "Samsung",
                                                "model": "SNP-6320H",
                                                "firmware": "2.20.01"
                                            },
                                            "geolocation": {
                                                "location": "GOP 1구역 전방 초소",
                                                "latitude": 38.1234,
                                                "longitude": 127.5678
                                            },
                                            "device_groups": [
                                                {"id": 1, "name": "GOP 1구역", "description": "GOP 1구역 장비 그룹", "device_count": 5}
                                            ]
                                        }
                                    ]
                                },
                                "meta": {"timestamp": "2025-01-10T10:31:00.000Z", "request_id": "550e8401-e29b-41d4-a716-446655440000"}
                            }
                        },
                        "include_devices_false": {
                            "summary": "include_devices=false - 디바이스 목록 미포함",
                            "value": {
                                "success": True,
                                "message": "디바이스 그룹 조회 성공",
                                "data": {
                                    "id": 1,
                                    "name": "GOP 1구역",
                                    "description": "GOP 1구역 장비 그룹",
                                    "device_count": 3,
                                    "created_at": "2025-01-01T00:00:00.000Z",
                                    "updated_at": "2025-01-01T00:00:00.000Z"
                                },
                                "meta": {"timestamp": "2025-01-10T10:31:00.000Z", "request_id": "550e8401-e29b-41d4-a716-446655440000"}
                            }
                        }
                    }
                }
            }
        },
        404: {
            "description": "DeviceGroup not found",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {"code": "NOT_FOUND", "message": "DeviceGroup ID 999 not found", "details": "No device group exists with the specified ID"},
                        "meta": {"timestamp": "2025-01-10T10:31:00.000Z", "request_id": "550e8401-e29b-41d4-a716-446655440000"}
                    }
                }
            }
        }
    }
)
async def get_device_group(
    group_id: int,
    include_devices: bool = Query(True, description="디바이스 목록 포함 여부 (기본값: true)"),
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    디바이스 그룹 상세 조회

    ID로 디바이스 그룹을 조회합니다.
    include_devices=true(기본값)이면 소속된 디바이스 목록도 함께 반환합니다.

    - **group_id**: 그룹 ID
    - **include_devices**: 디바이스 목록 포함 여부 (기본값: true)

    **Response**:
    - include_devices=true (기본값): DeviceGroupDetailResponse (devices 포함)
    - include_devices=false: DeviceGroupResponse (devices 미포함)

    PRD: PRD_API_Gap_Analysis.md (IMP-003)
    """
    group = db.query(DeviceGroup).filter(DeviceGroup.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": f"DeviceGroup ID {group_id} not found"}
        )

    # Device count calculation (always needed)
    device_count = group.device_mappings.count()

    # include_devices=false: return basic response without devices
    if not include_devices:
        response = DeviceGroupResponse(
            id=group.id,
            name=group.name,
            description=group.description,
            device_count=device_count,
            created_at=group.created_at,
            updated_at=group.updated_at
        )
        return ApiResponse(
            success=True,
            data=response,
            message="디바이스 그룹 조회 성공"
        )

    # include_devices=true (default): return detail response with devices
    # 소속 디바이스 목록 조회 (Device Base 클래스로 polymorphic query)
    mappings = group.device_mappings.all()
    devices = []
    for mapping in mappings:
        # Device base class로 조회 - polymorphic inheritance로 모든 디바이스 타입 조회
        device = db.query(Device).filter(Device.id == mapping.device_id).first()
        if device:
            # 공통 필드 준비
            base_data = {
                "id": device.id,
                "number_device": device.number_device,
                "group_device": device.group_device,
                "name_device": device.name_device,
                "type_device": device.type_device.value if hasattr(device.type_device, 'value') else str(device.type_device),
                "version": device.version,
                "status": device.status.value if hasattr(device.status, 'value') else str(device.status)
            }

            # 디바이스 타입별로 적절한 스키마 사용
            if isinstance(device, Controller):
                devices.append(ControllerSummary(
                    **base_data,
                    ip_address=device.ip_address,
                    ip_port=device.ip_port
                ))
            elif isinstance(device, Sensor):
                devices.append(SensorSummary(
                    **base_data,
                    controller_id=device.controller_id
                ))
            elif isinstance(device, Camera):
                # PRD_Camera_Urls_JsonB.md: urls JSONB 통합 (rtsp_uri/rtsp_port 제거)
                from app.schemas.device import CameraUrls
                urls_data = None
                if device.urls:
                    urls_data = CameraUrls.model_validate(device.urls) if isinstance(device.urls, dict) else device.urls
                devices.append(CameraSummary(
                    **base_data,
                    ip_address=device.ip_address,
                    ip_port=device.ip_port,
                    user_name=device.user_name,
                    user_password=device.user_password,
                    urls=urls_data,
                    mode=device.mode.value if hasattr(device.mode, 'value') else str(device.mode),
                    camera_category=device.category.value if hasattr(device.category, 'value') else str(device.category),
                    is_record=device.is_record,
                    hardware_spec=device.hardware_spec,
                    geolocation=device.geolocation
                ))

    response = DeviceGroupDetailResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        device_count=len(devices),
        devices=devices,
        created_at=group.created_at,
        updated_at=group.updated_at
    )

    return ApiResponse(
        success=True,
        data=response,
        message="디바이스 그룹 조회 성공"
    )


@router.post("", response_model=ApiResponse[DeviceGroupResponse], status_code=status.HTTP_201_CREATED)
async def create_device_group(
    group_data: DeviceGroupCreate,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    디바이스 그룹 생성

    새로운 디바이스 그룹을 생성합니다.

    - **name**: 그룹 이름 (필수, UNIQUE)
    - **description**: 그룹 설명 (선택)

    **Response**: 생성된 디바이스 그룹 정보
    """
    # 이름 중복 검사
    existing = db.query(DeviceGroup).filter(DeviceGroup.name == group_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": f"DeviceGroup name '{group_data.name}' already exists"}
        )

    group = DeviceGroup(
        name=group_data.name,
        description=group_data.description
    )
    db.add(group)
    db.commit()
    db.refresh(group)

    response = DeviceGroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        device_count=0,
        created_at=group.created_at,
        updated_at=group.updated_at
    )

    return ApiResponse(
        success=True,
        data=response,
        message="디바이스 그룹 생성 성공"
    )


@router.patch("/{group_id}", response_model=ApiResponse[DeviceGroupResponse])
async def patch_device_group(
    group_id: int,
    group_data: DeviceGroupUpdate,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    디바이스 그룹 부분 수정 (PATCH)

    디바이스 그룹의 특정 필드만 수정합니다.

    - **group_id**: 그룹 ID
    - **name**: 그룹 이름 (선택)
    - **description**: 그룹 설명 (선택)

    **Response**: 수정된 디바이스 그룹 정보
    """
    group = db.query(DeviceGroup).filter(DeviceGroup.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": f"DeviceGroup ID {group_id} not found"}
        )

    # 부분 업데이트
    if group_data.name is not None:
        # 이름 중복 검사 (자기 자신 제외)
        existing = db.query(DeviceGroup).filter(
            DeviceGroup.name == group_data.name,
            DeviceGroup.id != group_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "message": f"DeviceGroup name '{group_data.name}' already exists"}
            )
        group.name = group_data.name

    if group_data.description is not None:
        group.description = group_data.description

    db.commit()
    db.refresh(group)

    response = DeviceGroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        device_count=group.device_mappings.count(),
        created_at=group.created_at,
        updated_at=group.updated_at
    )

    return ApiResponse(
        success=True,
        data=response,
        message="디바이스 그룹 수정 성공"
    )


@router.put("/{group_id}", response_model=ApiResponse[DeviceGroupResponse])
async def put_device_group(
    group_id: int,
    group_data: DeviceGroupCreate,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    디바이스 그룹 전체 수정 (PUT)

    디바이스 그룹의 모든 필드를 수정합니다.

    - **group_id**: 그룹 ID
    - **name**: 그룹 이름 (필수)
    - **description**: 그룹 설명 (선택)

    **Response**: 수정된 디바이스 그룹 정보
    """
    group = db.query(DeviceGroup).filter(DeviceGroup.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": f"DeviceGroup ID {group_id} not found"}
        )

    # 이름 중복 검사 (자기 자신 제외)
    existing = db.query(DeviceGroup).filter(
        DeviceGroup.name == group_data.name,
        DeviceGroup.id != group_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": f"DeviceGroup name '{group_data.name}' already exists"}
        )

    group.name = group_data.name
    group.description = group_data.description

    db.commit()
    db.refresh(group)

    response = DeviceGroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        device_count=group.device_mappings.count(),
        created_at=group.created_at,
        updated_at=group.updated_at
    )

    return ApiResponse(
        success=True,
        data=response,
        message="디바이스 그룹 수정 성공"
    )


@router.delete("/{group_id}", response_model=ApiResponse[dict])
async def delete_device_group(
    group_id: int,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    디바이스 그룹 삭제

    디바이스 그룹을 삭제합니다.
    CASCADE로 인해 소속 매핑도 함께 삭제됩니다.

    - **group_id**: 그룹 ID

    **Response**: 삭제 결과
    """
    group = db.query(DeviceGroup).filter(DeviceGroup.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": f"DeviceGroup ID {group_id} not found"}
        )

    db.delete(group)
    db.commit()

    return ApiResponse(
        success=True,
        data={"id": group_id},
        message="디바이스 그룹 삭제 성공"
    )


@router.post("/{group_id}/devices", response_model=ApiResponse[DeviceAssignResponse])
async def assign_devices_to_group(
    group_id: int,
    request: DeviceAssignRequest,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    디바이스 그룹에 디바이스 할당

    하나 이상의 디바이스를 그룹에 할당합니다.

    - **group_id**: 그룹 ID
    - **device_ids**: 할당할 디바이스 ID 목록

    **Response**: 할당 결과 (성공/건너뜀 목록)
    """
    group = db.query(DeviceGroup).filter(DeviceGroup.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": f"DeviceGroup ID {group_id} not found"}
        )

    assigned = []
    skipped = []

    for device_id in request.device_ids:
        # 디바이스 존재 확인
        device = db.query(Controller).filter(Controller.id == device_id).first()
        if not device:
            skipped.append(device_id)
            continue

        # 이미 할당된 경우 건너뜀
        existing_mapping = db.query(DeviceGroupMapping).filter(
            DeviceGroupMapping.device_id == device_id,
            DeviceGroupMapping.category_device == EnumDeviceCategory.CONTROLLER,
            DeviceGroupMapping.group_id == group_id
        ).first()

        if existing_mapping:
            skipped.append(device_id)
        else:
            mapping = DeviceGroupMapping(device_id=device_id, category_device=EnumDeviceCategory.CONTROLLER, group_id=group_id)
            db.add(mapping)
            assigned.append(device_id)

    db.commit()

    message = f"{len(assigned)}개 디바이스 할당 완료"
    if skipped:
        message += f", {len(skipped)}개 건너뜀"

    response = DeviceAssignResponse(
        group_id=group_id,
        assigned_device_ids=assigned,
        skipped_device_ids=skipped,
        message=message
    )

    return ApiResponse(
        success=True,
        data=response,
        message=message
    )


@router.delete("/{group_id}/devices/{device_id}", response_model=ApiResponse[DeviceRemoveResponse])
async def remove_device_from_group(
    group_id: int,
    device_id: int,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    디바이스 그룹에서 디바이스 제거

    특정 디바이스를 그룹에서 제거합니다.

    - **group_id**: 그룹 ID
    - **device_id**: 제거할 디바이스 ID

    **Response**: 제거 결과
    """
    group = db.query(DeviceGroup).filter(DeviceGroup.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": f"DeviceGroup ID {group_id} not found"}
        )

    mapping = db.query(DeviceGroupMapping).filter(
        DeviceGroupMapping.device_id == device_id,
        DeviceGroupMapping.category_device == EnumDeviceCategory.CONTROLLER,
        DeviceGroupMapping.group_id == group_id
    ).first()

    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": f"Device ID {device_id} is not assigned to group {group_id}"}
        )

    db.delete(mapping)
    db.commit()

    response = DeviceRemoveResponse(
        group_id=group_id,
        device_id=device_id,
        message="디바이스 그룹에서 제거 성공"
    )

    return ApiResponse(
        success=True,
        data=response,
        message="디바이스 그룹에서 제거 성공"
    )
