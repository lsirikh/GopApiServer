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
    EventMappingNestedResponse,
    EventMappingLampBulkCreateRequest,
    EventMappingLampBulkCreateFailure,
    EventMappingLampBulkCreateResponse,
    EventMappingLampBulkUnassignRequest,
    EventMappingLampBulkUnassignResponse,
)
from app.schemas.common import ApiSingleResponse
from app.routers.auth import get_current_account_user_optional
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
    response_model=ApiSingleResponse[dict],
    summary="List lamp configs for event mapping",
    description="Get all lamp configurations for a specific event mapping"
)
def list_event_mapping_lamps(
    mapping_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_account_user_optional)
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
    response_model=ApiSingleResponse[dict],
    summary="Get single lamp config for event mapping",
    description="Get a specific lamp configuration for an event mapping"
)
def get_event_mapping_lamp(
    mapping_id: int,
    config_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_account_user_optional)
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
    response_model=ApiSingleResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Create lamp config for event mapping",
    description="Create a new lamp configuration for an event mapping"
)
def create_event_mapping_lamp(
    mapping_id: int,
    lamp_data: EventMappingLampCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_account_user_optional)
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
    response_model=ApiSingleResponse[dict],
    summary="Update lamp config for event mapping",
    description="Partially update a lamp configuration for an event mapping"
)
def update_event_mapping_lamp(
    mapping_id: int,
    config_id: int,
    lamp_data: EventMappingLampUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_account_user_optional)
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
    response_model=ApiSingleResponse[dict],
    summary="Replace lamp config for event mapping",
    description="Completely replace a lamp configuration for an event mapping"
)
def replace_event_mapping_lamp(
    mapping_id: int,
    config_id: int,
    lamp_data: EventMappingLampReplace,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_account_user_optional)
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
    response_model=ApiSingleResponse[None],
    summary="Delete lamp config for event mapping",
    description="Delete a lamp configuration for an event mapping"
)
def delete_event_mapping_lamp(
    mapping_id: int,
    config_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_account_user_optional)
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
        "message": "Event mapping lamp deleted successfully",
        "data": None
    }


# ============================================================
# 독립 List API (PRD_MappingSubResource_ListAPI.md v1.0)
# ============================================================

flat_router = APIRouter(tags=["Mapping Lamps"])


@flat_router.get(
    "",
    response_model=ApiSingleResponse[dict],
    summary="List all mapping lamps",
    description="Get all EventMappingLamp records across all event mappings"
)
def list_all_mapping_lamps(
    event_mapping_id: Optional[int] = None,
    lamp_id: Optional[int] = None,
    is_enable: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_account_user_optional)
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

# ============================================
# Bulk endpoints (PRD_EventMapping_BulkOperations.md §5)
# ============================================
@router.post(
    "/{mapping_id}/lamps/bulk",
    response_model=ApiSingleResponse[EventMappingLampBulkCreateResponse],
    status_code=status.HTTP_200_OK,
    summary="Bulk create lamp configs for event mapping",
    description="Create N lamp configurations for an event mapping in a single call (1~100). Best-effort: returns created_ids + failed_items.",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Event mapping not found"},
    },
)
def bulk_create_event_mapping_lamps(
    mapping_id: int,
    request: EventMappingLampBulkCreateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_account_user_optional),
):
    """POST /api/event-mappings/{mapping_id}/lamps/bulk"""
    # Check EventMapping exists
    event_mapping = db.query(EventMapping).filter(EventMapping.id == mapping_id).first()
    if not event_mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event mapping with id {mapping_id} not found"
        )

    created_ids: list[int] = []
    failed_items: list[EventMappingLampBulkCreateFailure] = []
    created_rows: list[EventMappingLamp] = []
    # PR-B (v4.5): 실 분류 로직
    skipped_config_ids: list[int] = []     # 이미 (mapping_id, lamp_id) 매핑 존재 시 기존 row PK
    not_found_config_ids: list[int] = []   # lamps 테이블에 lamp_id 부재 시 그 lamp_id
    # v4.6 FR-5: 같은 request 내 동일 lamp_id 중복 추적
    seen_in_request: set[int] = set()

    for idx, item in enumerate(request.items):
        # v4.6 FR-5: 같은 request 내 동일 lamp_id → 무시 (멱등, DB UNIQUE 충돌 방지)
        if item.lamp_id in seen_in_request:
            continue
        seen_in_request.add(item.lamp_id)

        # PR-B: Lamp FK 미존재 → not_found_config_ids
        lamp = db.query(Lamp).filter(Lamp.id == item.lamp_id).first()
        if not lamp:
            not_found_config_ids.append(item.lamp_id)
            continue

        # PR-B: (mapping_id, lamp_id) 중복 매핑 → skipped_config_ids
        existing = db.query(EventMappingLamp).filter(
            EventMappingLamp.event_mapping_id == mapping_id,
            EventMappingLamp.lamp_id == item.lamp_id,
        ).first()
        if existing:
            skipped_config_ids.append(existing.id)
            continue

        eml = EventMappingLamp(
            event_mapping_id=mapping_id,
            lamp_id=item.lamp_id,
            color=item.color,
            buzzer_time=item.buzzer_time,
            buzzer_sound=item.buzzer_sound,
            light_mode=item.light_mode,
            is_enable=item.is_enable,
            priority=item.priority,
        )
        db.add(eml)
        created_rows.append(eml)

    # PK 채번 후 단일 commit (원자성)
    db.flush()
    for row in created_rows:
        created_ids.append(row.id)
    db.commit()

    # PR-A (v4.5): 무조건 1건/요청 (CREATED) — 0건 케이스도 발행
    log_config_change(
        db=db,
        resource_type=EnumConfigResourceType.EVENT_MAPPING_LAMP,
        resource_id=mapping_id,
        resource_name=f"EventMapping-{mapping_id} lamps (bulk)",
        action=EnumConfigActionType.CREATED,
        after_state={"config_ids": created_ids, "count": len(created_ids)},
        description=f"EventMapping에 {len(created_ids)}개 Lamp 연동 일괄 생성 (bulk)",
    )

    parts = [f"{len(created_ids)}개 Lamp 연동 생성 완료"]
    if skipped_config_ids:
        parts.append(f"{len(skipped_config_ids)}개 중복")
    if not_found_config_ids:
        parts.append(f"{len(not_found_config_ids)}개 없음")
    if failed_items:
        parts.append(f"{len(failed_items)}개 실패")
    message = ", ".join(parts)

    return ApiSingleResponse[EventMappingLampBulkCreateResponse](
        success=True,
        message=message,
        data=EventMappingLampBulkCreateResponse(
            mapping_id=mapping_id,
            created_ids=created_ids,
            failed_items=failed_items,
            skipped_config_ids=skipped_config_ids,
            not_found_config_ids=not_found_config_ids,
            message=message,
        ),
    )


@router.delete(
    "/{mapping_id}/lamps",
    response_model=ApiSingleResponse[EventMappingLampBulkUnassignResponse],
    summary="Bulk unassign lamp configs from event mapping",
    description="Unassign N lamp configurations from an event mapping in a single call (1~100). Idempotent: removed/skipped/not_found 3-way classification.",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Event mapping not found"},
    },
)
def bulk_delete_event_mapping_lamps(
    mapping_id: int,
    request: EventMappingLampBulkUnassignRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_account_user_optional),
):
    """DELETE /api/event-mappings/{mapping_id}/lamps"""
    # Check EventMapping exists
    event_mapping = db.query(EventMapping).filter(EventMapping.id == mapping_id).first()
    if not event_mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event mapping with id {mapping_id} not found"
        )

    # 중복 ID 제거 (멱등성)
    unique_ids = list(dict.fromkeys(request.config_ids))

    removed: list[int] = []
    skipped: list[int] = []
    not_found: list[int] = []

    for config_id in unique_ids:
        row = db.query(EventMappingLamp).filter(
            EventMappingLamp.id == config_id
        ).first()
        if not row:
            not_found.append(config_id)
            continue
        if row.event_mapping_id != mapping_id:
            skipped.append(config_id)
            continue
        db.delete(row)
        removed.append(config_id)

    db.commit()  # 단일 commit (원자성)

    # ConfigChangeLog: 1건/요청 (DELETED) — removed가 있을 때만
    if removed:
        log_config_change(
            db=db,
            resource_type=EnumConfigResourceType.EVENT_MAPPING_LAMP,
            resource_id=mapping_id,
            resource_name=f"EventMapping-{mapping_id} lamps (bulk)",
            action=EnumConfigActionType.DELETED,
            before_state={"config_ids": removed, "count": len(removed)},
            description=f"EventMapping에서 {len(removed)}개 Lamp 연동 일괄 해제 (bulk)",
        )

    parts = [f"{len(removed)}개 Lamp 연동 해제 완료"]
    if skipped:
        parts.append(f"{len(skipped)}개 건너뜀")
    if not_found:
        parts.append(f"{len(not_found)}개 없음")
    message = ", ".join(parts)

    return ApiSingleResponse[EventMappingLampBulkUnassignResponse](
        success=True,
        message=message,
        data=EventMappingLampBulkUnassignResponse(
            mapping_id=mapping_id,
            removed_config_ids=removed,
            skipped_config_ids=skipped,
            not_found_config_ids=not_found,
            message=message,
        ),
    )
