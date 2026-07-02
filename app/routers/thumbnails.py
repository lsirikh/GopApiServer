"""
Thumbnail Image API endpoints

PRD: PRD_Thumbnail_Image.md v1.1
- POST /api/thumbnails: 이미지 업로드 (multipart form data, client file_name)
- GET /api/thumbnails: 목록 조회 (날짜 필터링, 페이지네이션)
- GET /api/thumbnails/{id}: 메타데이터 조회
- GET /api/thumbnails/{id}/image: 이미지 바이너리 반환 (ID 기반)
- GET /api/thumbnails/images/{file_name}: 이미지 바이너리 반환 (파일명 기반)
- DELETE /api/thumbnails/{id}: 파일 + DB 삭제
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional
from datetime import datetime
from io import BytesIO
from PIL import Image
import os
import math

from app.dependencies import get_db
from app.routers.auth import get_current_account_user_optional
from app.models.thumbnail import Thumbnail
from app.schemas.thumbnail import ThumbnailResponse
from app.schemas.common import ApiResponse, ApiSingleResponse, PaginationMeta
from app.config import settings

router = APIRouter(tags=["Thumbnails"])

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}


# ===== POST /api/thumbnails =====

@router.post(
    "",
    response_model=ApiSingleResponse[ThumbnailResponse],
    status_code=status.HTTP_201_CREATED,
    summary="썸네일 이미지 업로드",
    responses={
        400: {"description": "지원하지 않는 파일 형식"},
        409: {"description": "동일 file_name 이미 존재"},
        422: {"description": "file_name 또는 file 누락"},
    },
)
async def upload_thumbnail(
    file: UploadFile = File(..., description="이미지 파일 (image/jpeg, image/png, image/gif, image/webp)"),
    file_name: str = Form(..., description="저장할 파일명 (클라이언트 지정, 예: CAM-001_2026-02-19_14-30-25-123.jpg)"),
    current_user=Depends(get_current_account_user_optional),
    db: Session = Depends(get_db),
):
    """
    썸네일 이미지 업로드

    multipart/form-data로 이미지 파일과 file_name을 전송합니다.
    파일명은 클라이언트가 지정하며, 서버는 날짜별 폴더에 저장합니다.

    **Form Parameters**:
    - **file**: 이미지 파일 (Swagger UI에서 파일 탐색기로 선택)
    - **file_name**: 저장할 파일명 (클라이언트 지정, UNIQUE)

    **파일명 컨벤션**: `{camera_id}_{YYYY-MM-DD}_{HH-MM-SS-fff}.{ext}`

    **Response**: 생성된 썸네일 메타데이터 (image_url 포함)

    **Error**:
    - 400: 지원하지 않는 파일 형식 (image/jpeg, png, gif, webp만 허용)
    - 409: 동일 file_name이 이미 존재
    - 422: file_name 또는 file 누락
    """
    # Validate MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}. Allowed: {', '.join(ALLOWED_MIME_TYPES)}",
        )

    # Build file path: {storage}/{YYYY-MM-DD}/{file_name}
    now = datetime.now(settings.tz)
    date_dir = now.strftime("%Y-%m-%d")
    dir_path = os.path.join(settings.THUMBNAIL_STORAGE_PATH, date_dir)
    file_path = os.path.join(dir_path, file_name)

    # Create directory if not exists
    os.makedirs(dir_path, exist_ok=True)

    # Save file to disk
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Extract width/height from image
    width, height = None, None
    try:
        img = Image.open(BytesIO(content))
        width, height = img.size
    except Exception:
        pass

    # Create DB record
    thumbnail = Thumbnail(
        file_path=file_path,
        file_name=file_name,
        file_size=len(content),
        mime_type=file.content_type,
        width=width,
        height=height,
    )
    db.add(thumbnail)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # Clean up the saved file
        try:
            os.remove(file_path)
        except FileNotFoundError:
            pass
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Thumbnail with file_name '{file_name}' already exists",
        )
    db.refresh(thumbnail)

    return ApiSingleResponse(
        success=True,
        message="Thumbnail uploaded successfully",
        data=ThumbnailResponse.model_validate(thumbnail),
    )


# ===== GET /api/thumbnails =====

@router.get(
    "",
    response_model=ApiResponse[list[ThumbnailResponse]],
    summary="썸네일 목록 조회",
)
async def list_thumbnails(
    page: int = Query(1, ge=1, description="페이지 번호 (기본값: 1)"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수 (기본값: 20, 최대: 100)"),
    start_date: Optional[datetime] = Query(None, description="시작 날짜 필터 (ISO 8601)"),
    end_date: Optional[datetime] = Query(None, description="종료 날짜 필터 (ISO 8601)"),
    current_user=Depends(get_current_account_user_optional),
    db: Session = Depends(get_db),
):
    """
    썸네일 목록 조회 (페이지네이션)

    썸네일 목록을 페이지네이션하여 조회합니다. 날짜 범위 필터를 지원합니다.

    **파라미터**:
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    - **start_date**: 시작 날짜 필터 (ISO 8601 형식)
    - **end_date**: 종료 날짜 필터 (ISO 8601 형식)

    **Response**: 썸네일 목록 및 페이지네이션 정보
    """
    query = db.query(Thumbnail)

    if start_date:
        query = query.filter(Thumbnail.created_at >= start_date)
    if end_date:
        query = query.filter(Thumbnail.created_at <= end_date)

    total = query.count()
    total_pages = math.ceil(total / limit) if total > 0 else 0

    thumbnails = (
        query.order_by(Thumbnail.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return ApiResponse(
        success=True,
        message="Thumbnails retrieved successfully",
        data=[ThumbnailResponse.model_validate(t) for t in thumbnails],
        pagination=PaginationMeta(
            page=page,
            limit=limit,
            total=total,
            total_pages=total_pages,
        ),
    )


# ===== GET /api/thumbnails/images/{file_name} =====

@router.get(
    "/images/{file_name}",
    summary="썸네일 이미지 다운로드 (파일명 기반)",
    responses={
        200: {"content": {"image/*": {}}, "description": "이미지 바이너리"},
        404: {"description": "썸네일을 찾을 수 없음 또는 파일이 디스크에 없음"},
    },
)
async def get_thumbnail_image_by_file_name(
    file_name: str,
    db: Session = Depends(get_db),
):
    """
    썸네일 이미지 바이너리 반환 (파일명 기반)

    파일명으로 이미지를 조회하여 바이너리를 반환합니다.
    DetectionEvent.detail.thumbnail에 이 URL을 저장하여 서브시스템이 직접 조회합니다.

    **파라미터**:
    - **file_name**: 저장된 파일명 (Path Parameter, 예: CAM-001_2026-02-19_14-30-25-123.jpg)

    **Response**: 이미지 바이너리 (FileResponse, Content-Type: image/*)

    **Error**:
    - 404: 해당 file_name의 DB 레코드 없음 또는 파일이 디스크에 존재하지 않음
    """
    thumbnail = db.query(Thumbnail).filter(Thumbnail.file_name == file_name).first()
    if not thumbnail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thumbnail with file_name '{file_name}' not found",
        )

    if not os.path.exists(thumbnail.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thumbnail file not found on disk",
        )

    return FileResponse(
        path=thumbnail.file_path,
        media_type=thumbnail.mime_type,
    )


# ===== GET /api/thumbnails/{thumbnail_id} =====

@router.get(
    "/{thumbnail_id}",
    response_model=ApiSingleResponse[ThumbnailResponse],
    summary="썸네일 메타데이터 조회",
    responses={
        404: {"description": "썸네일을 찾을 수 없음"},
    },
)
async def get_thumbnail(
    thumbnail_id: int,
    current_user=Depends(get_current_account_user_optional),
    db: Session = Depends(get_db),
):
    """
    썸네일 메타데이터 단건 조회

    특정 썸네일의 메타데이터를 조회합니다.

    **파라미터**:
    - **thumbnail_id**: 썸네일 ID (Path Parameter)

    **Response**: 썸네일 메타데이터 (image_url 포함)

    **Error**:
    - 404: 썸네일을 찾을 수 없음
    """
    thumbnail = db.query(Thumbnail).filter(Thumbnail.id == thumbnail_id).first()
    if not thumbnail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thumbnail with id {thumbnail_id} not found",
        )

    return ApiSingleResponse(
        success=True,
        message="Thumbnail retrieved successfully",
        data=ThumbnailResponse.model_validate(thumbnail),
    )


# ===== GET /api/thumbnails/{thumbnail_id}/image =====

@router.get(
    "/{thumbnail_id}/image",
    summary="썸네일 이미지 다운로드 (ID 기반)",
    responses={
        200: {"content": {"image/*": {}}, "description": "이미지 바이너리"},
        404: {"description": "썸네일을 찾을 수 없음 또는 파일이 디스크에 없음"},
    },
)
async def get_thumbnail_image(
    thumbnail_id: int,
    db: Session = Depends(get_db),
):
    """
    썸네일 이미지 바이너리 반환 (ID 기반)

    썸네일 ID로 이미지를 조회하여 바이너리를 반환합니다.

    **파라미터**:
    - **thumbnail_id**: 썸네일 ID (Path Parameter)

    **Response**: 이미지 바이너리 (FileResponse, Content-Type: image/*)

    **Error**:
    - 404: 썸네일 DB 레코드 없음 또는 파일이 디스크에 존재하지 않음
    """
    thumbnail = db.query(Thumbnail).filter(Thumbnail.id == thumbnail_id).first()
    if not thumbnail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thumbnail with id {thumbnail_id} not found",
        )

    if not os.path.exists(thumbnail.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thumbnail file not found on disk",
        )

    return FileResponse(
        path=thumbnail.file_path,
        media_type=thumbnail.mime_type,
    )


# ===== DELETE /api/thumbnails/{thumbnail_id} =====

@router.delete(
    "/{thumbnail_id}",
    response_model=ApiSingleResponse[None],
    summary="썸네일 삭제",
    responses={
        404: {"description": "썸네일을 찾을 수 없음"},
    },
)
async def delete_thumbnail(
    thumbnail_id: int,
    current_user=Depends(get_current_account_user_optional),
    db: Session = Depends(get_db),
):
    """
    썸네일 삭제

    특정 썸네일을 삭제합니다 (파일 + DB 레코드).

    **파라미터**:
    - **thumbnail_id**: 썸네일 ID (Path Parameter)

    **Response**: 삭제 확인 정보

    **Error**:
    - 404: 썸네일을 찾을 수 없음
    """
    thumbnail = db.query(Thumbnail).filter(Thumbnail.id == thumbnail_id).first()
    if not thumbnail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thumbnail with id {thumbnail_id} not found",
        )

    # Delete file from disk (ignore if already missing)
    try:
        os.remove(thumbnail.file_path)
    except FileNotFoundError:
        pass

    db.delete(thumbnail)
    db.commit()

    return ApiSingleResponse(
        success=True,
        message="Thumbnail deleted successfully",
        data=None,
    )
