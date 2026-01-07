"""
FileGroup Router: CRUD API for FileGroup (방송음원 파일풀)
PRD: PRD_Speaker_Device.md - Section 6
URL Pattern: /api/file-groups
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional
import math

from app.dependencies import get_db
from app.routers.auth import get_current_user_optional
from app.models.file_group import FileGroup
from app.models.server import Server
from app.schemas.file_group import FileGroupCreate, FileGroupUpdate, FileGroupResponse
from app.schemas.common import ApiResponse, PaginationMeta


router = APIRouter(tags=["FileGroups"])


# ============================================
# GET /api/file-groups - List all file groups
# ============================================
@router.get("", response_model=ApiResponse[list[FileGroupResponse]])
async def get_file_groups(
    page: int = Query(1, ge=1, description="페이지 번호 (기본값: 1)"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수 (기본값: 20, 최대: 100)"),
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    server_id: Optional[int] = Query(None, description="서버 ID로 필터링"),
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    파일 그룹 목록 조회 (페이지네이션)

    파일 그룹 목록을 페이지네이션하여 조회합니다.

    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    - **skip**: 건너뛸 항목 수
    - **server_id**: 서버 ID로 필터링 (선택)

    **Response**: 파일 그룹 목록 및 페이지네이션 정보
    """
    # Build query
    query = db.query(FileGroup)

    # Apply filters
    if server_id is not None:
        query = query.filter(FileGroup.server_id == server_id)

    # Get total count
    total = query.count()

    # Calculate pagination - support both page and skip/limit style
    if skip > 0:
        offset = skip
    else:
        offset = (page - 1) * limit

    total_pages = math.ceil(total / limit) if total > 0 else 1

    # Apply pagination
    file_groups = query.offset(offset).limit(limit).all()

    # Convert to response format
    response_data = [FileGroupResponse.model_validate(fg) for fg in file_groups]

    return ApiResponse(
        success=True,
        message="FileGroup list retrieved",
        data=response_data,
        pagination=PaginationMeta(
            page=page,
            limit=limit,
            total=total,
            total_pages=total_pages
        )
    )


# ============================================
# GET /api/file-groups/{id} - Get single file group
# ============================================
@router.get("/{file_group_id}", response_model=ApiResponse[FileGroupResponse])
async def get_file_group(
    file_group_id: int,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    파일 그룹 단일 조회

    ID로 파일 그룹을 조회합니다.

    - **file_group_id**: 파일 그룹 ID

    **Response**: 파일 그룹 정보
    """
    file_group = db.query(FileGroup).filter(FileGroup.id == file_group_id).first()

    if not file_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"FileGroup with id {file_group_id} not found"
        )

    return ApiResponse(
        success=True,
        message="FileGroup retrieved",
        data=FileGroupResponse.model_validate(file_group)
    )


# ============================================
# POST /api/file-groups - Create file group
# ============================================
@router.post("", response_model=ApiResponse[FileGroupResponse], status_code=status.HTTP_201_CREATED)
async def create_file_group(
    file_group_data: FileGroupCreate,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    파일 그룹 생성

    새로운 파일 그룹을 생성합니다.

    - **server_id**: 서버 ID (필수)
    - **group_id**: 그룹 ID (필수)
    - **group_name**: 그룹 이름 (필수)
    - **files**: 파일 목록 (선택)

    **Response**: 생성된 파일 그룹 정보
    """
    # Validate server exists
    server = db.query(Server).filter(Server.id == file_group_data.server_id).first()
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server with id {file_group_data.server_id} not found"
        )

    # Create FileGroup
    file_group = FileGroup(
        server_id=file_group_data.server_id,
        group_id=file_group_data.group_id,
        group_name=file_group_data.group_name,
        files=file_group_data.files
    )

    try:
        db.add(file_group)
        db.commit()
        db.refresh(file_group)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"FileGroup with server_id={file_group_data.server_id} and group_id={file_group_data.group_id} already exists"
        )

    return ApiResponse(
        success=True,
        message="FileGroup created",
        data=FileGroupResponse.model_validate(file_group)
    )


# ============================================
# PATCH /api/file-groups/{id} - Partial update
# ============================================
@router.patch("/{file_group_id}", response_model=ApiResponse[FileGroupResponse])
async def patch_file_group(
    file_group_id: int,
    file_group_data: FileGroupUpdate,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    파일 그룹 부분 수정 (PATCH)

    파일 그룹의 일부 필드만 수정합니다.

    - **file_group_id**: 파일 그룹 ID
    - **group_name**: 그룹 이름 (선택)
    - **files**: 파일 목록 (선택)

    **Response**: 수정된 파일 그룹 정보
    """
    file_group = db.query(FileGroup).filter(FileGroup.id == file_group_id).first()

    if not file_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"FileGroup with id {file_group_id} not found"
        )

    # Update only provided fields
    update_data = file_group_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(file_group, field, value)

    db.commit()
    db.refresh(file_group)

    return ApiResponse(
        success=True,
        message="FileGroup updated",
        data=FileGroupResponse.model_validate(file_group)
    )


# ============================================
# PUT /api/file-groups/{id} - Full replace
# ============================================
@router.put("/{file_group_id}", response_model=ApiResponse[FileGroupResponse])
async def put_file_group(
    file_group_id: int,
    file_group_data: FileGroupCreate,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    파일 그룹 전체 수정 (PUT)

    파일 그룹의 모든 필드를 교체합니다.

    - **file_group_id**: 파일 그룹 ID
    - **server_id**: 서버 ID (필수)
    - **group_id**: 그룹 ID (필수)
    - **group_name**: 그룹 이름 (필수)
    - **files**: 파일 목록 (선택, 미제공시 null)

    **Response**: 수정된 파일 그룹 정보
    """
    file_group = db.query(FileGroup).filter(FileGroup.id == file_group_id).first()

    if not file_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"FileGroup with id {file_group_id} not found"
        )

    # Validate server exists if changing
    if file_group_data.server_id != file_group.server_id:
        server = db.query(Server).filter(Server.id == file_group_data.server_id).first()
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server with id {file_group_data.server_id} not found"
            )

    # Replace all fields
    file_group.server_id = file_group_data.server_id
    file_group.group_id = file_group_data.group_id
    file_group.group_name = file_group_data.group_name
    file_group.files = file_group_data.files

    db.commit()
    db.refresh(file_group)

    return ApiResponse(
        success=True,
        message="FileGroup replaced",
        data=FileGroupResponse.model_validate(file_group)
    )


# ============================================
# DELETE /api/file-groups/{id} - Delete file group
# ============================================
@router.delete("/{file_group_id}", response_model=ApiResponse)
async def delete_file_group(
    file_group_id: int,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    파일 그룹 삭제

    파일 그룹을 삭제합니다.

    - **file_group_id**: 파일 그룹 ID

    **Response**: 삭제 성공 메시지
    """
    file_group = db.query(FileGroup).filter(FileGroup.id == file_group_id).first()

    if not file_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"FileGroup with id {file_group_id} not found"
        )

    db.delete(file_group)
    db.commit()

    return ApiResponse(
        success=True,
        message="FileGroup deleted",
        data={"id": file_group_id}
    )
