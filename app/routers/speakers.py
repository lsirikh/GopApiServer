"""
Speaker API endpoints
PRD: PRD_Speaker_Device.md - Section 6.1
PRD: PRD_Speaker_Geolocation.md v1.0 - geolocation JSONB 추가
URL Pattern: /api/devices/speakers (Device 하위 리소스)

v6.0 P7: async 전환 (Polymorphic Device)
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Optional, List
import math

from app.dependencies import get_async_db
from app.routers.auth import get_current_account_user_optional_async
from app.models.device import Speaker
from app.models.device_group import DeviceGroup, DeviceGroupMapping
from app.models.server import Server
from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumSpeakerType, EnumDeviceCategory, EnumConfigResourceType, EnumConfigActionType
from app.schemas.device import SpeakerCreate, SpeakerUpdate, SpeakerResponse, DeviceGroupNestedResponse
from app.schemas.server import ServerNestedResponse
from app.schemas.common import ApiResponse, ApiSingleResponse, PaginationMeta
from app.services.config_log_service import log_config_change_async, get_identifier, get_changed_fields, model_to_dict

router = APIRouter(tags=["Speakers"])


async def _get_device_groups_nested(
    db: AsyncSession,
    device_id: int,
    category_device: EnumDeviceCategory = EnumDeviceCategory.SPEAKER,
) -> List[DeviceGroupNestedResponse]:
    """Get device groups for a speaker (PRD_DeviceGroup_Support_Completion.md)"""
    mappings = (await db.execute(
        select(DeviceGroupMapping).where(
            DeviceGroupMapping.device_id == device_id,
            DeviceGroupMapping.category_device == category_device,
        )
    )).scalars().all()

    if not mappings:
        return []

    group_ids = [m.group_id for m in mappings]
    groups = (await db.execute(
        select(DeviceGroup).where(DeviceGroup.id.in_(group_ids))
    )).scalars().all()

    result: List[DeviceGroupNestedResponse] = []
    for g in groups:
        device_count = (await db.execute(
            select(func.count()).select_from(DeviceGroupMapping).where(
                DeviceGroupMapping.group_id == g.id
            )
        )).scalar()
        result.append(
            DeviceGroupNestedResponse(
                id=g.id,
                name=g.name,
                description=g.description,
                device_count=device_count,
            )
        )
    return result


async def _update_device_group_mappings(
    db: AsyncSession,
    device_id: int,
    group_ids: List[int],
    category_device: EnumDeviceCategory = EnumDeviceCategory.SPEAKER,
):
    """Update device group mappings for a speaker (PRD_DeviceGroup_Support_Completion.md)"""
    await db.execute(
        delete(DeviceGroupMapping).where(
            DeviceGroupMapping.device_id == device_id,
            DeviceGroupMapping.category_device == category_device,
        )
    )

    for group_id in group_ids:
        group = (await db.execute(
            select(DeviceGroup).where(DeviceGroup.id == group_id)
        )).scalars().first()
        if group:
            mapping = DeviceGroupMapping(
                device_id=device_id,
                category_device=category_device,
                group_id=group_id,
            )
            db.add(mapping)


async def _speaker_to_response(speaker: Speaker, db: AsyncSession) -> SpeakerResponse:
    """Convert Speaker model to SpeakerResponse schema"""
    # Build ServerNestedResponse if server exists (server is preloaded via selectinload)
    server_nested = None
    if speaker.server:
        server_nested = ServerNestedResponse(
            id=speaker.server.id,
            category_id=speaker.server.category_id,
            name=speaker.server.name,
            status=speaker.server.status.value,
            ip_address=speaker.server.ip_address,
            port=speaker.server.port,
            hostname=speaker.server.hostname,
            user_name=speaker.server.user_name,
            user_password=speaker.server.user_password,
            threshold_config=speaker.server.threshold_config,
        )

    # PRD_DeviceGroup_Support_Completion.md: device_groups 조회
    device_groups = await _get_device_groups_nested(db, speaker.id, EnumDeviceCategory.SPEAKER)

    return SpeakerResponse(
        id=speaker.id,
        category_device=speaker.category_device.value,
        number_device=speaker.number_device,
        group_device=speaker.group_device,
        name_device=speaker.name_device,
        type_device=speaker.type_device.value,
        version=speaker.version,
        status=speaker.status.value,
        is_enable=speaker.is_enable,
        created_at=speaker.created_at,
        updated_at=speaker.updated_at,
        speaker_type=speaker.speaker_type.value,
        description=speaker.description,
        geolocation=speaker.geolocation,  # PRD_Speaker_Geolocation.md v1.0
        server=server_nested,
        device_groups=device_groups,
    )


@router.get("", response_model=ApiResponse[list[SpeakerResponse]])
async def get_speakers(
    page: int = Query(1, ge=1, description="페이지 번호 (기본값: 1)"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수 (기본값: 20, 최대: 100)"),
    server_id: Optional[int] = Query(None, description="서버 ID로 필터링"),
    status: Optional[str] = Query(None, description="상태로 필터링 (EnumDeviceStatus)"),
    speaker_type: Optional[str] = Query(None, description="스피커 타입으로 필터링 (EnumSpeakerType)"),
    current_user=Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db),
):
    """
    스피커 목록 조회 (페이지네이션)

    스피커 목록을 페이지네이션하여 조회합니다.

    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    - **server_id**: 서버 ID로 필터링 (선택)
    - **status**: 상태로 필터링 (선택)
    - **speaker_type**: 스피커 타입으로 필터링 (선택)

    **Response**: 스피커 목록 및 페이지네이션 정보
    """
    # Build query — selectinload(Speaker.server) 로 async lazy load 함정 회피
    stmt = select(Speaker).options(selectinload(Speaker.server))
    count_stmt = select(func.count()).select_from(Speaker)

    # Apply filters (mirror on both)
    if server_id is not None:
        stmt = stmt.where(Speaker.server_id == server_id)
        count_stmt = count_stmt.where(Speaker.server_id == server_id)
    if status is not None:
        stmt = stmt.where(Speaker.status == status)
        count_stmt = count_stmt.where(Speaker.status == status)
    if speaker_type is not None:
        stmt = stmt.where(Speaker.speaker_type == speaker_type)
        count_stmt = count_stmt.where(Speaker.speaker_type == speaker_type)

    # Get total count
    total = (await db.execute(count_stmt)).scalar()

    # Calculate pagination
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    # Get paginated results (order by id for stable pagination)
    speakers = (await db.execute(
        stmt.order_by(Speaker.id).offset(skip).limit(limit)
    )).scalars().all()

    # Convert to response format
    speaker_responses = [await _speaker_to_response(s, db) for s in speakers]

    pagination = PaginationMeta(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages,
    )

    return ApiResponse(
        success=True,
        message="Speakers retrieved successfully",
        data=speaker_responses,
        pagination=pagination,
    )


@router.get("/{speaker_id}", response_model=ApiSingleResponse[SpeakerResponse])
async def get_speaker(
    speaker_id: int,
    current_user=Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db),
):
    """
    스피커 단건 조회

    ID로 스피커 정보를 조회합니다.

    - **speaker_id**: 스피커 ID (Path Parameter)

    **Response**: 스피커 상세 정보

    **Error**:
    - 404: 스피커를 찾을 수 없음
    """
    speaker = (await db.execute(
        select(Speaker)
        .options(selectinload(Speaker.server))
        .where(Speaker.id == speaker_id)
    )).scalars().first()

    if not speaker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Speaker with id {speaker_id} not found",
        )

    speaker_response = await _speaker_to_response(speaker, db)

    return ApiSingleResponse(
        success=True,
        message="Speaker retrieved successfully",
        data=speaker_response,
    )


@router.post("", response_model=ApiSingleResponse[SpeakerResponse], status_code=status.HTTP_201_CREATED)
async def create_speaker(
    speaker_data: SpeakerCreate,
    current_user=Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db),
):
    """
    스피커 생성

    새로운 스피커를 생성합니다.

    **Request Body**:
    - **number_device**: 단말 번호 (필수)
    - **name_device**: 장치 이름 (필수)
    - **speaker_type**: 스피커 타입 (기본값: NORMAL)
    - **server_id**: 방송서버 ID (선택)
    - **description**: 설명 (선택)

    **Response**: 생성된 스피커 정보

    **Error**:
    - 404: 서버를 찾을 수 없음
    - 422: 잘못된 Enum 값
    """
    # Validate server_id if provided
    if speaker_data.server_id is not None:
        server = (await db.execute(
            select(Server).where(Server.id == speaker_data.server_id)
        )).scalars().first()
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server with id {speaker_data.server_id} not found",
            )

    # PRD_Speaker_Geolocation.md v1.0: geolocation 처리
    geolocation_dict = None
    if speaker_data.geolocation:
        geolocation_dict = speaker_data.geolocation.model_dump(exclude_none=True)

    # Create new speaker
    new_speaker = Speaker(
        number_device=speaker_data.number_device,
        group_device=speaker_data.group_device,
        name_device=speaker_data.name_device,
        type_device=speaker_data.type_device,
        version=speaker_data.version,
        status=speaker_data.status,
        is_enable=speaker_data.is_enable,
        speaker_type=speaker_data.speaker_type,
        server_id=speaker_data.server_id,
        description=speaker_data.description,
        geolocation=geolocation_dict,  # PRD_Speaker_Geolocation.md v1.0
    )

    db.add(new_speaker)
    await db.commit()
    await db.refresh(new_speaker)

    # PRD_DeviceGroup_Support_Completion.md: group_ids 처리
    if speaker_data.group_ids is not None:
        await _update_device_group_mappings(db, new_speaker.id, speaker_data.group_ids, EnumDeviceCategory.SPEAKER)
        await db.commit()

    # ConfigChangeLog: CREATED 로그 기록 (PRD v1.2)
    await log_config_change_async(
        db=db,
        resource_type=EnumConfigResourceType.SPEAKER,
        resource_id=new_speaker.id,
        resource_name=f"Speaker-{new_speaker.id} ({new_speaker.name_device})",
        action=EnumConfigActionType.CREATED,
        after_state=get_identifier(new_speaker),
        description="Speaker 생성",
    )

    # Reload speaker with server relationship preloaded for response
    new_speaker = (await db.execute(
        select(Speaker)
        .options(selectinload(Speaker.server))
        .where(Speaker.id == new_speaker.id)
    )).scalars().first()

    speaker_response = await _speaker_to_response(new_speaker, db)

    return ApiSingleResponse(
        success=True,
        message="Speaker created successfully",
        data=speaker_response,
    )


@router.patch("/{speaker_id}", response_model=ApiSingleResponse[SpeakerResponse])
async def update_speaker(
    speaker_id: int,
    speaker_data: SpeakerUpdate,
    current_user=Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db),
):
    """
    스피커 부분 수정 (PATCH)

    스피커의 일부 필드만 수정합니다.

    - **speaker_id**: 스피커 ID (Path Parameter)

    **Request Body** (모든 필드 선택):
    - **number_device**: 단말 번호
    - **name_device**: 장치 이름
    - **speaker_type**: 스피커 타입
    - **server_id**: 방송서버 ID (null 가능)
    - **description**: 설명

    **Response**: 수정된 스피커 정보

    **Error**:
    - 404: 스피커를 찾을 수 없음
    """
    speaker = (await db.execute(
        select(Speaker)
        .options(selectinload(Speaker.server))
        .where(Speaker.id == speaker_id)
    )).scalars().first()

    if not speaker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Speaker with id {speaker_id} not found",
        )

    # ConfigChangeLog: before_state 캡처 (PRD v1.2)
    before_state = model_to_dict(speaker)

    # Update fields if provided
    update_data = speaker_data.model_dump(exclude_unset=True)

    # PRD_DeviceGroup_Support_Completion.md: group_ids 분리 처리
    group_ids = update_data.pop("group_ids", None)

    # Validate server_id if provided and not null
    if "server_id" in update_data and update_data["server_id"] is not None:
        server = (await db.execute(
            select(Server).where(Server.id == update_data["server_id"])
        )).scalars().first()
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server with id {update_data['server_id']} not found",
            )

    # PRD_Speaker_Geolocation.md v1.0: geolocation 처리
    if "geolocation" in update_data and update_data["geolocation"] is not None:
        # Pydantic dict로 변환
        update_data["geolocation"] = {k: v for k, v in update_data["geolocation"].items() if v is not None}

    for field, value in update_data.items():
        setattr(speaker, field, value)

    # PRD_DeviceGroup_Support_Completion.md: group_ids 처리
    if group_ids is not None:
        await _update_device_group_mappings(db, speaker.id, group_ids, EnumDeviceCategory.SPEAKER)

    await db.commit()
    await db.refresh(speaker)

    # ConfigChangeLog: UPDATED 로그 기록 (PRD v1.2)
    after_state = model_to_dict(speaker)
    before_changes, after_changes = get_changed_fields(before_state, after_state)
    if before_changes or after_changes:
        await log_config_change_async(
            db=db,
            resource_type=EnumConfigResourceType.SPEAKER,
            resource_id=speaker.id,
            resource_name=f"Speaker-{speaker.id} ({speaker.name_device})",
            action=EnumConfigActionType.UPDATED,
            before_state=before_changes,
            after_state=after_changes,
            description="Speaker 수정",
        )

    # Reload speaker with server relationship preloaded for response
    speaker = (await db.execute(
        select(Speaker)
        .options(selectinload(Speaker.server))
        .where(Speaker.id == speaker.id)
    )).scalars().first()

    speaker_response = await _speaker_to_response(speaker, db)

    return ApiSingleResponse(
        success=True,
        message="Speaker updated successfully",
        data=speaker_response,
    )


@router.put("/{speaker_id}", response_model=ApiSingleResponse[SpeakerResponse])
async def replace_speaker(
    speaker_id: int,
    speaker_data: SpeakerCreate,
    current_user=Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db),
):
    """
    스피커 전체 수정 (PUT)

    스피커의 모든 필드를 교체합니다.

    - **speaker_id**: 스피커 ID (Path Parameter)

    **Request Body** (필수 필드):
    - **number_device**: 단말 번호
    - **name_device**: 장치 이름

    **Response**: 수정된 스피커 정보

    **Error**:
    - 404: 스피커를 찾을 수 없음
    """
    speaker = (await db.execute(
        select(Speaker)
        .options(selectinload(Speaker.server))
        .where(Speaker.id == speaker_id)
    )).scalars().first()

    if not speaker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Speaker with id {speaker_id} not found",
        )

    # Validate server_id if provided
    if speaker_data.server_id is not None:
        server = (await db.execute(
            select(Server).where(Server.id == speaker_data.server_id)
        )).scalars().first()
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server with id {speaker_data.server_id} not found",
            )

    # PRD_Speaker_Geolocation.md v1.0: geolocation 처리
    geolocation_dict = None
    if speaker_data.geolocation:
        geolocation_dict = speaker_data.geolocation.model_dump(exclude_none=True)

    # Replace all fields
    speaker.number_device = speaker_data.number_device
    speaker.group_device = speaker_data.group_device
    speaker.name_device = speaker_data.name_device
    speaker.type_device = speaker_data.type_device
    speaker.version = speaker_data.version
    speaker.status = speaker_data.status
    speaker.is_enable = speaker_data.is_enable
    speaker.speaker_type = speaker_data.speaker_type
    speaker.server_id = speaker_data.server_id
    speaker.description = speaker_data.description
    speaker.geolocation = geolocation_dict  # PRD_Speaker_Geolocation.md v1.0

    # PRD_DeviceGroup_Support_Completion.md: group_ids 처리
    if speaker_data.group_ids is not None:
        await _update_device_group_mappings(db, speaker.id, speaker_data.group_ids, EnumDeviceCategory.SPEAKER)

    await db.commit()
    await db.refresh(speaker)

    # Reload speaker with server relationship preloaded for response
    speaker = (await db.execute(
        select(Speaker)
        .options(selectinload(Speaker.server))
        .where(Speaker.id == speaker.id)
    )).scalars().first()

    speaker_response = await _speaker_to_response(speaker, db)

    return ApiSingleResponse(
        success=True,
        message="Speaker replaced successfully",
        data=speaker_response,
    )


@router.delete("/{speaker_id}", response_model=ApiSingleResponse[None])
async def delete_speaker(
    speaker_id: int,
    current_user=Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db),
):
    """
    스피커 삭제

    스피커를 삭제합니다.

    - **speaker_id**: 스피커 ID (Path Parameter)

    **Response**: 삭제된 스피커 ID

    **Error**:
    - 404: 스피커를 찾을 수 없음
    """
    speaker = (await db.execute(
        select(Speaker).where(Speaker.id == speaker_id)
    )).scalars().first()

    if not speaker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Speaker with id {speaker_id} not found",
        )

    # ConfigChangeLog: 삭제 전 identifier 캡처 (PRD v1.2)
    deleted_id = speaker.id
    deleted_identifier = get_identifier(speaker)
    deleted_name = f"Speaker-{speaker.id} ({speaker.name_device})"

    # Delete associated device group mappings first (no FK cascade for polymorphic relation)
    await db.execute(
        delete(DeviceGroupMapping).where(
            DeviceGroupMapping.device_id == speaker_id,
            DeviceGroupMapping.category_device == EnumDeviceCategory.SPEAKER,
        )
    )

    await db.delete(speaker)
    await db.commit()

    # ConfigChangeLog: DELETED 로그 기록 (PRD v1.2)
    await log_config_change_async(
        db=db,
        resource_type=EnumConfigResourceType.SPEAKER,
        resource_id=deleted_id,
        resource_name=deleted_name,
        action=EnumConfigActionType.DELETED,
        before_state=deleted_identifier,
        description="Speaker 삭제",
    )

    return ApiSingleResponse(
        success=True,
        message="Speaker deleted successfully",
        data=None,
    )
