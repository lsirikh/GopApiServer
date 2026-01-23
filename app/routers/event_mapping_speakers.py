"""
EventMappingSpeaker Router

PRD: PRD_EventMappingSpeaker.md v1.0

Endpoints: /api/event-mappings/{mapping_id}/speakers
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.dependencies import get_db
from app.models.integration import EventMapping, EventMappingSpeaker
from app.models.device import Speaker
from app.models.file_group import FileGroup
from app.schemas.integration import (
    EventMappingSpeakerCreate,
    EventMappingSpeakerUpdate,
    EventMappingSpeakerReplace,
    EventMappingSpeakerResponse,
    SpeakerNestedResponseIntegration,
    FileGroupNestedResponse
)
from app.routers.auth import get_current_user_optional
from app.utils.enums import EnumConfigResourceType, EnumConfigActionType
from app.services.config_log_service import log_config_change, get_changed_fields, model_to_dict

router = APIRouter(tags=["Event Mapping Speakers"])


def _build_speaker_nested(speaker: Speaker) -> Optional[SpeakerNestedResponseIntegration]:
    """Build SpeakerNestedResponseIntegration from Speaker model (Full Property, timestamp 제외)"""
    if not speaker:
        return None

    return SpeakerNestedResponseIntegration(
        # Device 공통 필드
        id=speaker.id,
        number_device=speaker.number_device,
        group_device=speaker.group_device,
        name_device=speaker.name_device,
        type_device=speaker.type_device.value if hasattr(speaker.type_device, 'value') else str(speaker.type_device),
        version=speaker.version,
        status=speaker.status.value if hasattr(speaker.status, 'value') else str(speaker.status),
        is_enable=speaker.is_enable if speaker.is_enable is not None else True,
        # Speaker 고유 필드
        speaker_type=speaker.speaker_type.value if hasattr(speaker.speaker_type, 'value') else str(speaker.speaker_type),
        server_id=speaker.server_id,
        description=speaker.description,
        geolocation=speaker.geolocation
    )


def _build_file_group_nested(file_group: FileGroup) -> Optional[FileGroupNestedResponse]:
    """Build FileGroupNestedResponse from FileGroup model"""
    if not file_group:
        return None

    return FileGroupNestedResponse(
        id=file_group.id,
        server_id=file_group.server_id,
        group_id=file_group.group_id,
        group_name=file_group.group_name,
        files=file_group.files
    )


def _build_response(ems: EventMappingSpeaker) -> EventMappingSpeakerResponse:
    """Build EventMappingSpeakerResponse from model"""
    return EventMappingSpeakerResponse(
        id=ems.id,
        event_mapping_id=ems.event_mapping_id,
        speaker=_build_speaker_nested(ems.speaker) if ems.speaker else None,
        file_group=_build_file_group_nested(ems.file_group) if ems.file_group else None,
        repeat_count=ems.repeat_count,
        is_enable=ems.is_enable,
        priority=ems.priority,
        created_at=ems.created_at,
        updated_at=ems.updated_at
    )


@router.get(
    "/{mapping_id}/speakers",
    response_model=dict,
    summary="List speaker configs for event mapping",
    description="Get all speaker configurations for a specific event mapping"
)
def list_event_mapping_speakers(
    mapping_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """GET /api/event-mappings/{mapping_id}/speakers"""
    # Check EventMapping exists
    event_mapping = db.query(EventMapping).filter(EventMapping.id == mapping_id).first()
    if not event_mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event mapping with id {mapping_id} not found"
        )

    # Get all speakers for this mapping
    speakers = db.query(EventMappingSpeaker).filter(
        EventMappingSpeaker.event_mapping_id == mapping_id
    ).all()

    items = [_build_response(ems) for ems in speakers]

    return {
        "success": True,
        "message": "Event mapping speakers retrieved successfully",
        "data": {
            "items": [item.model_dump() for item in items],
            "total": len(items)
        }
    }


@router.get(
    "/{mapping_id}/speakers/{config_id}",
    response_model=dict,
    summary="Get single speaker config for event mapping",
    description="Get a specific speaker configuration for an event mapping"
)
def get_event_mapping_speaker(
    mapping_id: int,
    config_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """GET /api/event-mappings/{mapping_id}/speakers/{config_id}"""
    # Check EventMapping exists
    event_mapping = db.query(EventMapping).filter(EventMapping.id == mapping_id).first()
    if not event_mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event mapping with id {mapping_id} not found"
        )

    # Get the specific speaker config
    ems = db.query(EventMappingSpeaker).filter(
        EventMappingSpeaker.id == config_id,
        EventMappingSpeaker.event_mapping_id == mapping_id
    ).first()

    if not ems:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Speaker config with id {config_id} not found"
        )

    return {
        "success": True,
        "message": "Event mapping speaker retrieved successfully",
        "data": _build_response(ems).model_dump()
    }


@router.post(
    "/{mapping_id}/speakers",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create speaker config for event mapping",
    description="Create a new speaker configuration for an event mapping"
)
def create_event_mapping_speaker(
    mapping_id: int,
    speaker_data: EventMappingSpeakerCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """POST /api/event-mappings/{mapping_id}/speakers"""
    # Check EventMapping exists
    event_mapping = db.query(EventMapping).filter(EventMapping.id == mapping_id).first()
    if not event_mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event mapping with id {mapping_id} not found"
        )

    # Check Speaker exists
    speaker = db.query(Speaker).filter(Speaker.id == speaker_data.speaker_id).first()
    if not speaker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Speaker with id {speaker_data.speaker_id} not found"
        )

    # Check FileGroup exists (if provided)
    if speaker_data.file_group_id:
        file_group = db.query(FileGroup).filter(FileGroup.id == speaker_data.file_group_id).first()
        if not file_group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"FileGroup with id {speaker_data.file_group_id} not found"
            )

    # Create EventMappingSpeaker
    ems = EventMappingSpeaker(
        event_mapping_id=mapping_id,
        speaker_id=speaker_data.speaker_id,
        file_group_id=speaker_data.file_group_id,
        repeat_count=speaker_data.repeat_count,
        is_enable=speaker_data.is_enable,
        priority=speaker_data.priority
    )
    db.add(ems)
    db.commit()
    db.refresh(ems)

    # ConfigChangeLog: CREATED 로그 기록 (PRD v1.2)
    log_config_change(
        db=db,
        resource_type=EnumConfigResourceType.EVENT_MAPPING_SPEAKER,
        resource_id=ems.id,
        resource_name=f"EventMappingSpeaker-{ems.id} (speaker_id: {ems.speaker_id})",
        action=EnumConfigActionType.CREATED,
        after_state={"id": ems.id, "speaker_id": ems.speaker_id},
        description="EventMappingSpeaker 생성"
    )

    return {
        "success": True,
        "message": "Event mapping speaker created successfully",
        "data": _build_response(ems).model_dump()
    }


@router.patch(
    "/{mapping_id}/speakers/{config_id}",
    response_model=dict,
    summary="Update speaker config for event mapping",
    description="Partially update a speaker configuration for an event mapping"
)
def update_event_mapping_speaker(
    mapping_id: int,
    config_id: int,
    speaker_data: EventMappingSpeakerUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """PATCH /api/event-mappings/{mapping_id}/speakers/{config_id}"""
    # Check EventMapping exists
    event_mapping = db.query(EventMapping).filter(EventMapping.id == mapping_id).first()
    if not event_mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event mapping with id {mapping_id} not found"
        )

    # Get the specific speaker config
    ems = db.query(EventMappingSpeaker).filter(
        EventMappingSpeaker.id == config_id,
        EventMappingSpeaker.event_mapping_id == mapping_id
    ).first()

    if not ems:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Speaker config with id {config_id} not found"
        )

    # ConfigChangeLog: before_state 캡처 (PRD v1.2)
    before_state = model_to_dict(ems)

    # Update only provided fields
    update_data = speaker_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ems, field, value)

    db.commit()
    db.refresh(ems)

    # ConfigChangeLog: UPDATED 로그 기록 (PRD v1.2)
    after_state = model_to_dict(ems)
    before_changes, after_changes = get_changed_fields(before_state, after_state)
    if before_changes or after_changes:
        log_config_change(
            db=db,
            resource_type=EnumConfigResourceType.EVENT_MAPPING_SPEAKER,
            resource_id=ems.id,
            resource_name=f"EventMappingSpeaker-{ems.id} (speaker_id: {ems.speaker_id})",
            action=EnumConfigActionType.UPDATED,
            before_state=before_changes,
            after_state=after_changes,
            description="EventMappingSpeaker 수정"
        )

    return {
        "success": True,
        "message": "Event mapping speaker updated successfully",
        "data": _build_response(ems).model_dump()
    }


@router.put(
    "/{mapping_id}/speakers/{config_id}",
    response_model=dict,
    summary="Replace speaker config for event mapping",
    description="Completely replace a speaker configuration for an event mapping"
)
def replace_event_mapping_speaker(
    mapping_id: int,
    config_id: int,
    speaker_data: EventMappingSpeakerReplace,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """PUT /api/event-mappings/{mapping_id}/speakers/{config_id}"""
    # Check EventMapping exists
    event_mapping = db.query(EventMapping).filter(EventMapping.id == mapping_id).first()
    if not event_mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event mapping with id {mapping_id} not found"
        )

    # Get the specific speaker config
    ems = db.query(EventMappingSpeaker).filter(
        EventMappingSpeaker.id == config_id,
        EventMappingSpeaker.event_mapping_id == mapping_id
    ).first()

    if not ems:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Speaker config with id {config_id} not found"
        )

    # Replace all fields
    ems.speaker_id = speaker_data.speaker_id
    ems.file_group_id = speaker_data.file_group_id
    ems.repeat_count = speaker_data.repeat_count
    ems.is_enable = speaker_data.is_enable
    ems.priority = speaker_data.priority

    db.commit()
    db.refresh(ems)

    return {
        "success": True,
        "message": "Event mapping speaker replaced successfully",
        "data": _build_response(ems).model_dump()
    }


@router.delete(
    "/{mapping_id}/speakers/{config_id}",
    response_model=dict,
    summary="Delete speaker config for event mapping",
    description="Delete a speaker configuration for an event mapping"
)
def delete_event_mapping_speaker(
    mapping_id: int,
    config_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """DELETE /api/event-mappings/{mapping_id}/speakers/{config_id}"""
    # Check EventMapping exists
    event_mapping = db.query(EventMapping).filter(EventMapping.id == mapping_id).first()
    if not event_mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event mapping with id {mapping_id} not found"
        )

    # Get the specific speaker config
    ems = db.query(EventMappingSpeaker).filter(
        EventMappingSpeaker.id == config_id,
        EventMappingSpeaker.event_mapping_id == mapping_id
    ).first()

    if not ems:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Speaker config with id {config_id} not found"
        )

    # ConfigChangeLog: 삭제 전 identifier 캡처 (PRD v1.2)
    deleted_id = ems.id
    deleted_identifier = {"id": ems.id, "speaker_id": ems.speaker_id}
    deleted_name = f"EventMappingSpeaker-{ems.id} (speaker_id: {ems.speaker_id})"

    db.delete(ems)
    db.commit()

    # ConfigChangeLog: DELETED 로그 기록 (PRD v1.2)
    log_config_change(
        db=db,
        resource_type=EnumConfigResourceType.EVENT_MAPPING_SPEAKER,
        resource_id=deleted_id,
        resource_name=deleted_name,
        action=EnumConfigActionType.DELETED,
        before_state=deleted_identifier,
        description="EventMappingSpeaker 삭제"
    )

    return {
        "success": True,
        "message": "Event mapping speaker deleted successfully"
    }
