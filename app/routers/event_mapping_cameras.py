"""
EventMappingCamera Router

PRD: PRD_CameraEventMapping_Refactoring.md v2.1 - Section 5

Endpoints: /api/event-mappings/{mapping_id}/cameras
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.dependencies import get_db
from app.models.integration import EventMapping, EventMappingCamera
from app.models.device import Camera
from app.models.camera_preset import CameraPreset
from app.models.device_group import DeviceGroupMapping
from app.schemas.integration import (
    EventMappingCameraCreate,
    EventMappingCameraUpdate,
    EventMappingCameraResponse,
    EventMappingCameraListResponse,
    CameraNestedResponseIntegration as CameraNestedResponse,
    PresetNestedResponse
)
from app.schemas.device import DeviceGroupNestedResponse
from app.routers.auth import get_current_user_optional

router = APIRouter(tags=["Event Mapping Cameras"])


def _build_camera_nested(camera: Camera, db: Session) -> Optional[CameraNestedResponse]:
    """Build CameraNestedResponse from Camera model"""
    if not camera:
        return None

    # Get device groups
    mappings = db.query(DeviceGroupMapping).filter(
        DeviceGroupMapping.device_id == camera.id,
        DeviceGroupMapping.category_device == "camera"
    ).all()

    device_groups = []
    for mapping in mappings:
        if mapping.group:
            device_groups.append(DeviceGroupNestedResponse(
                id=mapping.group.id,
                name=mapping.group.name,
                description=mapping.group.description,
                device_count=0  # Can be computed if needed
            ))

    return CameraNestedResponse(
        id=camera.id,
        number_device=camera.number_device,
        group_device=camera.group_device,
        name_device=camera.name_device,
        type_device=camera.type_device.value if hasattr(camera.type_device, 'value') else str(camera.type_device),
        version=camera.version,
        status=camera.status.value if hasattr(camera.status, 'value') else str(camera.status),
        ip_address=camera.ip_address,
        ip_port=camera.ip_port,
        mode=camera.mode.value if hasattr(camera.mode, 'value') else str(camera.mode),
        category=camera.category.value if hasattr(camera.category, 'value') else str(camera.category),
        is_record=camera.is_record if hasattr(camera, 'is_record') and camera.is_record is not None else False,
        hardware_spec=camera.hardware_spec if hasattr(camera, 'hardware_spec') else None,
        geolocation=camera.geolocation if hasattr(camera, 'geolocation') else None,
        urls=camera.urls if hasattr(camera, 'urls') else None,
        device_groups=device_groups
    )


def _build_preset_nested(preset: CameraPreset) -> Optional[PresetNestedResponse]:
    """Build PresetNestedResponse from CameraPreset model"""
    if not preset:
        return None

    return PresetNestedResponse(
        id=preset.id,
        camera_id=preset.camera_id,
        camera_name=preset.camera_name,
        preset_index=preset.preset_index,
        preset_name=preset.preset_name,
        touring_time=preset.touring_time
    )


def _build_response(emc: EventMappingCamera, db: Session) -> EventMappingCameraResponse:
    """Build EventMappingCameraResponse from model"""
    return EventMappingCameraResponse(
        id=emc.id,
        event_mapping_id=emc.event_mapping_id,
        camera=_build_camera_nested(emc.camera, db) if emc.camera else None,
        target_preset=_build_preset_nested(emc.target_preset) if emc.target_preset else None,
        home_preset=_build_preset_nested(emc.home_preset) if emc.home_preset else None,
        delay_time=emc.delay_time,
        is_enable=emc.is_enable,
        priority=emc.priority,
        created_at=emc.created_at,
        updated_at=emc.updated_at
    )


@router.get(
    "/{mapping_id}/cameras",
    response_model=dict,
    summary="List camera configs for event mapping",
    description="Get all camera configurations for a specific event mapping"
)
def list_event_mapping_cameras(
    mapping_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """GET /api/event-mappings/{mapping_id}/cameras"""
    # Check EventMapping exists
    event_mapping = db.query(EventMapping).filter(EventMapping.id == mapping_id).first()
    if not event_mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event mapping with id {mapping_id} not found"
        )

    # Get all cameras for this mapping
    cameras = db.query(EventMappingCamera).filter(
        EventMappingCamera.event_mapping_id == mapping_id
    ).all()

    items = [_build_response(emc, db) for emc in cameras]

    return {
        "success": True,
        "message": "Event mapping cameras retrieved successfully",
        "data": {
            "items": [item.model_dump() for item in items],
            "total": len(items)
        }
    }


@router.get(
    "/{mapping_id}/cameras/{config_id}",
    response_model=dict,
    summary="Get camera config by ID",
    description="Get a specific camera configuration"
)
def get_event_mapping_camera(
    mapping_id: int,
    config_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """GET /api/event-mappings/{mapping_id}/cameras/{config_id}"""
    # Check EventMapping exists
    event_mapping = db.query(EventMapping).filter(EventMapping.id == mapping_id).first()
    if not event_mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event mapping with id {mapping_id} not found"
        )

    # Get camera config
    emc = db.query(EventMappingCamera).filter(
        EventMappingCamera.id == config_id,
        EventMappingCamera.event_mapping_id == mapping_id
    ).first()

    if not emc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera config with id {config_id} not found for mapping {mapping_id}"
        )

    return {
        "success": True,
        "message": "Event mapping camera retrieved successfully",
        "data": _build_response(emc, db).model_dump()
    }


@router.post(
    "/{mapping_id}/cameras",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create camera config",
    description="Create a new camera configuration for an event mapping"
)
def create_event_mapping_camera(
    mapping_id: int,
    data: EventMappingCameraCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """POST /api/event-mappings/{mapping_id}/cameras"""
    # Check EventMapping exists
    event_mapping = db.query(EventMapping).filter(EventMapping.id == mapping_id).first()
    if not event_mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event mapping with id {mapping_id} not found"
        )

    # Check Camera exists
    camera = db.query(Camera).filter(Camera.id == data.camera_id).first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with id {data.camera_id} not found"
        )

    # Check target_preset exists (if provided)
    if data.target_preset_id:
        target_preset = db.query(CameraPreset).filter(CameraPreset.id == data.target_preset_id).first()
        if not target_preset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target preset with id {data.target_preset_id} not found"
            )

    # Check home_preset exists (if provided)
    if data.home_preset_id:
        home_preset = db.query(CameraPreset).filter(CameraPreset.id == data.home_preset_id).first()
        if not home_preset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Home preset with id {data.home_preset_id} not found"
            )

    # Create EventMappingCamera
    emc = EventMappingCamera(
        event_mapping_id=mapping_id,
        camera_id=data.camera_id,
        target_preset_id=data.target_preset_id,
        home_preset_id=data.home_preset_id,
        delay_time=data.delay_time,
        is_enable=data.is_enable,
        priority=data.priority
    )
    db.add(emc)
    db.commit()
    db.refresh(emc)

    return {
        "success": True,
        "message": "Event mapping camera created successfully",
        "data": _build_response(emc, db).model_dump()
    }


@router.patch(
    "/{mapping_id}/cameras/{config_id}",
    response_model=dict,
    summary="Update camera config (partial)",
    description="Partially update a camera configuration"
)
def patch_event_mapping_camera(
    mapping_id: int,
    config_id: int,
    data: EventMappingCameraUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """PATCH /api/event-mappings/{mapping_id}/cameras/{config_id}"""
    # Check EventMapping exists
    event_mapping = db.query(EventMapping).filter(EventMapping.id == mapping_id).first()
    if not event_mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event mapping with id {mapping_id} not found"
        )

    # Get camera config
    emc = db.query(EventMappingCamera).filter(
        EventMappingCamera.id == config_id,
        EventMappingCamera.event_mapping_id == mapping_id
    ).first()

    if not emc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera config with id {config_id} not found for mapping {mapping_id}"
        )

    # Update only provided fields
    update_data = data.model_dump(exclude_unset=True)

    # Validate camera_id if provided
    if "camera_id" in update_data and update_data["camera_id"] is not None:
        camera = db.query(Camera).filter(Camera.id == update_data["camera_id"]).first()
        if not camera:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Camera with id {update_data['camera_id']} not found"
            )

    # Validate target_preset_id if provided
    if "target_preset_id" in update_data and update_data["target_preset_id"] is not None:
        preset = db.query(CameraPreset).filter(CameraPreset.id == update_data["target_preset_id"]).first()
        if not preset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target preset with id {update_data['target_preset_id']} not found"
            )

    # Validate home_preset_id if provided
    if "home_preset_id" in update_data and update_data["home_preset_id"] is not None:
        preset = db.query(CameraPreset).filter(CameraPreset.id == update_data["home_preset_id"]).first()
        if not preset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Home preset with id {update_data['home_preset_id']} not found"
            )

    for key, value in update_data.items():
        setattr(emc, key, value)

    db.commit()
    db.refresh(emc)

    return {
        "success": True,
        "message": "Event mapping camera updated successfully",
        "data": _build_response(emc, db).model_dump()
    }


@router.put(
    "/{mapping_id}/cameras/{config_id}",
    response_model=dict,
    summary="Replace camera config",
    description="Fully replace a camera configuration"
)
def put_event_mapping_camera(
    mapping_id: int,
    config_id: int,
    data: EventMappingCameraCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """PUT /api/event-mappings/{mapping_id}/cameras/{config_id}"""
    # Check EventMapping exists
    event_mapping = db.query(EventMapping).filter(EventMapping.id == mapping_id).first()
    if not event_mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event mapping with id {mapping_id} not found"
        )

    # Get camera config
    emc = db.query(EventMappingCamera).filter(
        EventMappingCamera.id == config_id,
        EventMappingCamera.event_mapping_id == mapping_id
    ).first()

    if not emc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera config with id {config_id} not found for mapping {mapping_id}"
        )

    # Validate camera_id
    camera = db.query(Camera).filter(Camera.id == data.camera_id).first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with id {data.camera_id} not found"
        )

    # Validate target_preset_id if provided
    if data.target_preset_id:
        preset = db.query(CameraPreset).filter(CameraPreset.id == data.target_preset_id).first()
        if not preset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target preset with id {data.target_preset_id} not found"
            )

    # Validate home_preset_id if provided
    if data.home_preset_id:
        preset = db.query(CameraPreset).filter(CameraPreset.id == data.home_preset_id).first()
        if not preset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Home preset with id {data.home_preset_id} not found"
            )

    # Replace all fields
    emc.camera_id = data.camera_id
    emc.target_preset_id = data.target_preset_id
    emc.home_preset_id = data.home_preset_id
    emc.delay_time = data.delay_time
    emc.is_enable = data.is_enable
    emc.priority = data.priority

    db.commit()
    db.refresh(emc)

    return {
        "success": True,
        "message": "Event mapping camera replaced successfully",
        "data": _build_response(emc, db).model_dump()
    }


@router.delete(
    "/{mapping_id}/cameras/{config_id}",
    response_model=dict,
    summary="Delete camera config",
    description="Delete a camera configuration"
)
def delete_event_mapping_camera(
    mapping_id: int,
    config_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """DELETE /api/event-mappings/{mapping_id}/cameras/{config_id}"""
    # Check EventMapping exists
    event_mapping = db.query(EventMapping).filter(EventMapping.id == mapping_id).first()
    if not event_mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event mapping with id {mapping_id} not found"
        )

    # Get camera config
    emc = db.query(EventMappingCamera).filter(
        EventMappingCamera.id == config_id,
        EventMappingCamera.event_mapping_id == mapping_id
    ).first()

    if not emc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera config with id {config_id} not found for mapping {mapping_id}"
        )

    db.delete(emc)
    db.commit()

    return {
        "success": True,
        "message": "Event mapping camera deleted successfully",
        "data": None
    }
