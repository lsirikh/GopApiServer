"""
Speaker API endpoints
PRD: PRD_Speaker_Device.md - Section 6.1
URL Pattern: /api/devices/speakers (Device 하위 리소스)
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import math

from app.dependencies import get_db
from app.routers.auth import get_current_user_optional
from app.models.speaker import Speaker
from app.models.server import Server
from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumSpeakerType
from app.schemas.speaker import SpeakerCreate, SpeakerUpdate, SpeakerResponse
from app.schemas.server import ServerNestedResponse
from app.schemas.common import ApiResponse, PaginationMeta

router = APIRouter(tags=["Speakers"])


def _speaker_to_response(speaker: Speaker, db: Session) -> SpeakerResponse:
    """Convert Speaker model to SpeakerResponse schema"""
    # Build ServerNestedResponse if server exists
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
            cpu_usage=speaker.server.cpu_usage,
            ram_usage=speaker.server.ram_usage,
            disk_usage=speaker.server.disk_usage,
            network_throughput=speaker.server.network_throughput
        )

    return SpeakerResponse(
        id=speaker.id,
        category_device=speaker.category_device.value,
        number_device=speaker.number_device,
        group_device=speaker.group_device,
        name_device=speaker.name_device,
        type_device=speaker.type_device.value,
        version=speaker.version,
        status=speaker.status.value,
        created_at=speaker.created_at,
        updated_at=speaker.updated_at,
        speaker_type=speaker.speaker_type.value,
        description=speaker.description,
        server=server_nested
    )


@router.get("", response_model=ApiResponse[list[SpeakerResponse]])
async def get_speakers(
    page: int = Query(1, ge=1, description="페이지 번호 (기본값: 1)"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수 (기본값: 20, 최대: 100)"),
    server_id: Optional[int] = Query(None, description="서버 ID로 필터링"),
    status: Optional[str] = Query(None, description="상태로 필터링 (EnumDeviceStatus)"),
    speaker_type: Optional[str] = Query(None, description="스피커 타입으로 필터링 (EnumSpeakerType)"),
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
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
    # Build query
    query = db.query(Speaker)

    # Apply filters
    if server_id is not None:
        query = query.filter(Speaker.server_id == server_id)
    if status is not None:
        query = query.filter(Speaker.status == status)
    if speaker_type is not None:
        query = query.filter(Speaker.speaker_type == speaker_type)

    # Get total count
    total = query.count()

    # Calculate pagination
    skip = (page - 1) * limit
    total_pages = math.ceil(total / limit) if total > 0 else 1

    # Get paginated results
    speakers = query.offset(skip).limit(limit).all()

    # Convert to response format
    speaker_responses = [_speaker_to_response(s, db) for s in speakers]

    pagination = PaginationMeta(
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages
    )

    return ApiResponse(
        success=True,
        message="Speakers retrieved successfully",
        data=speaker_responses,
        pagination=pagination
    )


@router.get("/{speaker_id}", response_model=ApiResponse[SpeakerResponse])
async def get_speaker(
    speaker_id: int,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    스피커 단건 조회

    ID로 스피커 정보를 조회합니다.

    - **speaker_id**: 스피커 ID (Path Parameter)

    **Response**: 스피커 상세 정보

    **Error**:
    - 404: 스피커를 찾을 수 없음
    """
    speaker = db.query(Speaker).filter(Speaker.id == speaker_id).first()

    if not speaker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Speaker with id {speaker_id} not found"
        )

    speaker_response = _speaker_to_response(speaker, db)

    return ApiResponse(
        success=True,
        message="Speaker retrieved successfully",
        data=speaker_response
    )


@router.post("", response_model=ApiResponse[SpeakerResponse], status_code=status.HTTP_201_CREATED)
async def create_speaker(
    speaker_data: SpeakerCreate,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
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
        server = db.query(Server).filter(Server.id == speaker_data.server_id).first()
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server with id {speaker_data.server_id} not found"
            )

    # Create new speaker
    new_speaker = Speaker(
        number_device=speaker_data.number_device,
        group_device=speaker_data.group_device,
        name_device=speaker_data.name_device,
        type_device=speaker_data.type_device,
        version=speaker_data.version,
        status=speaker_data.status,
        speaker_type=speaker_data.speaker_type,
        server_id=speaker_data.server_id,
        description=speaker_data.description
    )

    db.add(new_speaker)
    db.commit()
    db.refresh(new_speaker)

    speaker_response = _speaker_to_response(new_speaker, db)

    return ApiResponse(
        success=True,
        message="Speaker created successfully",
        data=speaker_response
    )


@router.patch("/{speaker_id}", response_model=ApiResponse[SpeakerResponse])
async def update_speaker(
    speaker_id: int,
    speaker_data: SpeakerUpdate,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
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
    speaker = db.query(Speaker).filter(Speaker.id == speaker_id).first()

    if not speaker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Speaker with id {speaker_id} not found"
        )

    # Update fields if provided
    update_data = speaker_data.model_dump(exclude_unset=True)

    # Validate server_id if provided and not null
    if "server_id" in update_data and update_data["server_id"] is not None:
        server = db.query(Server).filter(Server.id == update_data["server_id"]).first()
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server with id {update_data['server_id']} not found"
            )

    for field, value in update_data.items():
        setattr(speaker, field, value)

    db.commit()
    db.refresh(speaker)

    speaker_response = _speaker_to_response(speaker, db)

    return ApiResponse(
        success=True,
        message="Speaker updated successfully",
        data=speaker_response
    )


@router.put("/{speaker_id}", response_model=ApiResponse[SpeakerResponse])
async def replace_speaker(
    speaker_id: int,
    speaker_data: SpeakerCreate,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
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
    speaker = db.query(Speaker).filter(Speaker.id == speaker_id).first()

    if not speaker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Speaker with id {speaker_id} not found"
        )

    # Validate server_id if provided
    if speaker_data.server_id is not None:
        server = db.query(Server).filter(Server.id == speaker_data.server_id).first()
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server with id {speaker_data.server_id} not found"
            )

    # Replace all fields
    speaker.number_device = speaker_data.number_device
    speaker.group_device = speaker_data.group_device
    speaker.name_device = speaker_data.name_device
    speaker.type_device = speaker_data.type_device
    speaker.version = speaker_data.version
    speaker.status = speaker_data.status
    speaker.speaker_type = speaker_data.speaker_type
    speaker.server_id = speaker_data.server_id
    speaker.description = speaker_data.description

    db.commit()
    db.refresh(speaker)

    speaker_response = _speaker_to_response(speaker, db)

    return ApiResponse(
        success=True,
        message="Speaker replaced successfully",
        data=speaker_response
    )


@router.delete("/{speaker_id}", response_model=ApiResponse[dict])
async def delete_speaker(
    speaker_id: int,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    스피커 삭제

    스피커를 삭제합니다.

    - **speaker_id**: 스피커 ID (Path Parameter)

    **Response**: 삭제된 스피커 ID

    **Error**:
    - 404: 스피커를 찾을 수 없음
    """
    speaker = db.query(Speaker).filter(Speaker.id == speaker_id).first()

    if not speaker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Speaker with id {speaker_id} not found"
        )

    db.delete(speaker)
    db.commit()

    return ApiResponse(
        success=True,
        message="Speaker deleted successfully",
        data={"id": speaker_id}
    )
