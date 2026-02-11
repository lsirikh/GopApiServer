"""
EventMappingLamp Router

PRD: PRD_Lamp_Device.md v1.1

Endpoints: /api/event-mappings/{mapping_id}/lamps
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.dependencies import get_db
from app.models.integration import EventMapping, EventMappingLamp
from app.models.device import Lamp
from app.schemas.integration import (
    EventMappingLampCreate,
    EventMappingLampUpdate,
    EventMappingLampReplace,
    EventMappingLampResponse,
    LampNestedResponseIntegration,
    EventMappingNestedResponse
)
from app.routers.auth import get_current_user_optional
from app.utils.enums import EnumConfigResourceType, EnumConfigActionType
from app.services.config_log_service import log_config_change, get_changed_fields, model_to_dict

router = APIRouter(tags=["Event Mapping Lamps"])


def _build_lamp_nested(lamp: Lamp) -> Optional[LampNestedResponseIntegration]:
    """Build LampNestedResponseIntegration from Lamp model (Full Property, timestamp 제외)"""
    if not lamp:
        return None

    return LampNestedResponseIntegration(
        # Device 공통 필드
        id=lamp.id,
        number_device=lamp.number_device,
        group_device=lamp.group_device,
        name_device=lamp.name_device,
        type_device=lamp.type_device.value if hasattr(lamp.type_device, 'value') else str(lamp.type_device),
        version=lamp.version,
        status=lamp.status.value if hasattr(lamp.status, 'value') else str(lamp.status),
        is_enable=lamp.is_enable if lamp.is_enable is not None else True,
        # Lamp 고유 필드
        ip_address=lamp.ip_address,
        ip_port=lamp.ip_port,
        user_name=lamp.user_name,
        # user_password excluded for security (PRD v1.1)
        description=lamp.description,
        geolocation=lamp.geolocation
    )


def _build_event_mapping_nested(event_mapping: EventMapping) -> EventMappingNestedResponse:
    """Build EventMappingNestedResponse from EventMapping model"""
    return EventMappingNestedResponse(
        id=event_mapping.id,
        name_event=event_mapping.name_event,
        category_event_mapping=event_mapping.category_event_mapping.value if hasattr(event_mapping.category_event_mapping, 'value') else str(event_mapping.category_event_mapping)
    )


def _build_response(eml: EventMappingLamp) -> EventMappingLampResponse:
    """Build EventMappingLampResponse from model"""
    return EventMappingLampResponse(
        id=eml.id,
        event_mapping=_build_event_mapping_nested(eml.event_mapping),
        lamp=_build_lamp_nested(eml.lamp) if eml.lamp else None,
        color=eml.color.value if hasattr(eml.color, 'value') else str(eml.color),
        buzzer_time=eml.buzzer_time,
        buzzer_sound=eml.buzzer_sound.value if hasattr(eml.buzzer_sound, 'value') else str(eml.buzzer_sound),
        light_mode=eml.light_mode.value if hasattr(eml.light_mode, 'value') else str(eml.light_mode),
        is_enable=eml.is_enable,
        priority=eml.priority,
        created_at=eml.created_at,
        updated_at=eml.updated_at
    )


@router.get(
    "/{mapping_id}/lamps",
    response_model=dict,
    summary="List lamp configs for event mapping",
    description="Get all lamp configurations for a specific event mapping"
)
def list_event_mapping_lamps(
    mapping_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """GET /api/event-mappings/{mapping_id}/lamps"""
    # Check EventMapping exists
    event_mapping = db.query(EventMapping).filter(EventMapping.id == mapping_id).first()
    if not event_mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event mapping with id {mapping_id} not found"
        )

    # Get all lamps for this mapping
    lamps = db.query(EventMappingLamp).filter(
        EventMappingLamp.event_mapping_id == mapping_id
    ).all()

    items = [_build_response(eml) for eml in lamps]

    return {
        "success": True,
        "message": "Event mapping lamps retrieved successfully",
        "data": {
            "items": [item.model_dump() for item in items],
            "total": len(items)
        }
    }


@router.get(
    "/{mapping_id}/lamps/{config_id}",
    response_model=dict,
    summary="Get single lamp config for event mapping",
    description="Get a specific lamp configuration for an event mapping"
)
def get_event_mapping_lamp(
    mapping_id: int,
    config_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """GET /api/event-mappings/{mapping_id}/lamps/{config_id}"""
    # Check EventMapping exists
    event_mapping = db.query(EventMapping).filter(EventMapping.id == mapping_id).first()
    if not event_mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event mapping with id {mapping_id} not found"
        )

    # Get the specific lamp config
    eml = db.query(EventMappingLamp).filter(
        EventMappingLamp.id == config_id,
        EventMappingLamp.event_mapping_id == mapping_id
    ).first()

    if not eml:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lamp config with id {config_id} not found"
        )

    return {
        "success": True,
        "message": "Event mapping lamp retrieved successfully",
        "data": _build_response(eml).model_dump()
    }


@router.post(
    "/{mapping_id}/lamps",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create lamp config for event mapping",
    description="Create a new lamp configuration for an event mapping"
)
def create_event_mapping_lamp(
    mapping_id: int,
    lamp_data: EventMappingLampCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """POST /api/event-mappings/{mapping_id}/lamps"""
    # Check EventMapping exists
    event_mapping = db.query(EventMapping).filter(EventMapping.id == mapping_id).first()
    if not event_mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event mapping with id {mapping_id} not found"
        )

    # Check Lamp exists
    lamp = db.query(Lamp).filter(Lamp.id == lamp_data.lamp_id).first()
    if not lamp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lamp with id {lamp_data.lamp_id} not found"
        )

    # Create EventMappingLamp
    eml = EventMappingLamp(
        event_mapping_id=mapping_id,
        lamp_id=lamp_data.lamp_id,
        color=lamp_data.color,
        buzzer_time=lamp_data.buzzer_time,
        buzzer_sound=lamp_data.buzzer_sound,
        light_mode=lamp_data.light_mode,
        is_enable=lamp_data.is_enable,
        priority=lamp_data.priority
    )
    db.add(eml)
    db.commit()
    db.refresh(eml)

    # ConfigChangeLog: CREATED 로그 기록 (PRD v1.2)
    log_config_change(
        db=db,
        resource_type=EnumConfigResourceType.EVENT_MAPPING_LAMP,
        resource_id=eml.id,
        resource_name=f"EventMappingLamp-{eml.id} (lamp_id: {eml.lamp_id})",
        action=EnumConfigActionType.CREATED,
        after_state={"id": eml.id, "lamp_id": eml.lamp_id},
        description="EventMappingLamp 생성"
    )

    return {
        "success": True,
        "message": "Event mapping lamp created successfully",
        "data": _build_response(eml).model_dump()
    }


@router.patch(
    "/{mapping_id}/lamps/{config_id}",
    response_model=dict,
    summary="Update lamp config for event mapping",
    description="Partially update a lamp configuration for an event mapping"
)
def update_event_mapping_lamp(
    mapping_id: int,
    config_id: int,
    lamp_data: EventMappingLampUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """PATCH /api/event-mappings/{mapping_id}/lamps/{config_id}"""
    # Check EventMapping exists
    event_mapping = db.query(EventMapping).filter(EventMapping.id == mapping_id).first()
    if not event_mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event mapping with id {mapping_id} not found"
        )

    # Get the specific lamp config
    eml = db.query(EventMappingLamp).filter(
        EventMappingLamp.id == config_id,
        EventMappingLamp.event_mapping_id == mapping_id
    ).first()

    if not eml:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lamp config with id {config_id} not found"
        )

    # ConfigChangeLog: before_state 캡처 (PRD v1.2)
    before_state = model_to_dict(eml)

    # Update only provided fields
    update_data = lamp_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(eml, field, value)

    db.commit()
    db.refresh(eml)

    # ConfigChangeLog: UPDATED 로그 기록 (PRD v1.2)
    after_state = model_to_dict(eml)
    before_changes, after_changes = get_changed_fields(before_state, after_state)
    if before_changes or after_changes:
        log_config_change(
            db=db,
            resource_type=EnumConfigResourceType.EVENT_MAPPING_LAMP,
            resource_id=eml.id,
            resource_name=f"EventMappingLamp-{eml.id} (lamp_id: {eml.lamp_id})",
            action=EnumConfigActionType.UPDATED,
            before_state=before_changes,
            after_state=after_changes,
            description="EventMappingLamp 수정"
        )

    return {
        "success": True,
        "message": "Event mapping lamp updated successfully",
        "data": _build_response(eml).model_dump()
    }


@router.put(
    "/{mapping_id}/lamps/{config_id}",
    response_model=dict,
    summary="Replace lamp config for event mapping",
    description="Completely replace a lamp configuration for an event mapping"
)
def replace_event_mapping_lamp(
    mapping_id: int,
    config_id: int,
    lamp_data: EventMappingLampReplace,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """PUT /api/event-mappings/{mapping_id}/lamps/{config_id}"""
    # Check EventMapping exists
    event_mapping = db.query(EventMapping).filter(EventMapping.id == mapping_id).first()
    if not event_mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event mapping with id {mapping_id} not found"
        )

    # Get the specific lamp config
    eml = db.query(EventMappingLamp).filter(
        EventMappingLamp.id == config_id,
        EventMappingLamp.event_mapping_id == mapping_id
    ).first()

    if not eml:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lamp config with id {config_id} not found"
        )

    # Replace all fields
    eml.lamp_id = lamp_data.lamp_id
    eml.color = lamp_data.color
    eml.buzzer_time = lamp_data.buzzer_time
    eml.buzzer_sound = lamp_data.buzzer_sound
    eml.light_mode = lamp_data.light_mode
    eml.is_enable = lamp_data.is_enable
    eml.priority = lamp_data.priority

    db.commit()
    db.refresh(eml)

    return {
        "success": True,
        "message": "Event mapping lamp replaced successfully",
        "data": _build_response(eml).model_dump()
    }


@router.delete(
    "/{mapping_id}/lamps/{config_id}",
    response_model=dict,
    summary="Delete lamp config for event mapping",
    description="Delete a lamp configuration for an event mapping"
)
def delete_event_mapping_lamp(
    mapping_id: int,
    config_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """DELETE /api/event-mappings/{mapping_id}/lamps/{config_id}"""
    # Check EventMapping exists
    event_mapping = db.query(EventMapping).filter(EventMapping.id == mapping_id).first()
    if not event_mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event mapping with id {mapping_id} not found"
        )

    # Get the specific lamp config
    eml = db.query(EventMappingLamp).filter(
        EventMappingLamp.id == config_id,
        EventMappingLamp.event_mapping_id == mapping_id
    ).first()

    if not eml:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lamp config with id {config_id} not found"
        )

    # ConfigChangeLog: 삭제 전 identifier 캡처 (PRD v1.2)
    deleted_id = eml.id
    deleted_identifier = {"id": eml.id, "lamp_id": eml.lamp_id}
    deleted_name = f"EventMappingLamp-{eml.id} (lamp_id: {eml.lamp_id})"

    db.delete(eml)
    db.commit()

    # ConfigChangeLog: DELETED 로그 기록 (PRD v1.2)
    log_config_change(
        db=db,
        resource_type=EnumConfigResourceType.EVENT_MAPPING_LAMP,
        resource_id=deleted_id,
        resource_name=deleted_name,
        action=EnumConfigActionType.DELETED,
        before_state=deleted_identifier,
        description="EventMappingLamp 삭제"
    )

    return {
        "success": True,
        "message": "Event mapping lamp deleted successfully"
    }


# ============================================================
# 독립 List API (PRD_MappingSubResource_ListAPI.md v1.0)
# ============================================================

flat_router = APIRouter(tags=["Mapping Lamps"])


@flat_router.get(
    "",
    response_model=dict,
    summary="List all mapping lamps",
    description="Get all EventMappingLamp records across all event mappings"
)
def list_all_mapping_lamps(
    event_mapping_id: Optional[int] = None,
    lamp_id: Optional[int] = None,
    is_enable: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """GET /api/integrations/mapping-lamps"""
    query = db.query(EventMappingLamp)

    if event_mapping_id is not None:
        query = query.filter(EventMappingLamp.event_mapping_id == event_mapping_id)
    if lamp_id is not None:
        query = query.filter(EventMappingLamp.lamp_id == lamp_id)
    if is_enable is not None:
        query = query.filter(EventMappingLamp.is_enable == is_enable)

    lamps = query.all()

    items = [_build_response(eml) for eml in lamps]

    return {
        "success": True,
        "message": "Mapping lamps retrieved successfully",
        "data": {
            "items": [item.model_dump() for item in items],
            "total": len(items)
        }
    }
