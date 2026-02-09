"""
CameraSetting Router
PRD: PRD_Device_Setting.md Section 5.2

GET/PATCH /api/devices/cameras/{camera_id}/settings
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.routers.auth import get_current_user_optional
from app.models.device import Camera
from app.models.device_setting import CameraSetting
from app.schemas.device_setting import CameraSettingCreate, CameraSettingUpdate, CameraSettingResponse
from app.schemas.common import ApiSingleResponse

router = APIRouter(tags=["Camera Settings"])


@router.get(
    "/{camera_id}/settings",
    response_model=ApiSingleResponse[CameraSettingResponse],
)
async def get_camera_settings(
    camera_id: int,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """카메라 설정 조회 (없으면 기본값으로 Lazy 생성)"""
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with id {camera_id} not found",
        )

    setting = db.query(CameraSetting).filter(CameraSetting.camera_id == camera_id).first()
    if not setting:
        setting = CameraSetting(camera_id=camera_id)
        db.add(setting)
        db.commit()
        db.refresh(setting)

    return ApiSingleResponse(
        success=True,
        message="Camera settings retrieved successfully",
        data=CameraSettingResponse.model_validate(setting),
    )


@router.patch(
    "/{camera_id}/settings",
    response_model=ApiSingleResponse[CameraSettingResponse],
)
async def update_camera_settings(
    camera_id: int,
    update_data: CameraSettingUpdate,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """카메라 설정 부분 수정 (없으면 Upsert)"""
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with id {camera_id} not found",
        )

    setting = db.query(CameraSetting).filter(CameraSetting.camera_id == camera_id).first()
    if not setting:
        setting = CameraSetting(camera_id=camera_id)
        db.add(setting)

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(setting, key, value)

    db.commit()
    db.refresh(setting)

    return ApiSingleResponse(
        success=True,
        message="Camera settings updated successfully",
        data=CameraSettingResponse.model_validate(setting),
    )


@router.put(
    "/{camera_id}/settings",
    response_model=ApiSingleResponse[CameraSettingResponse],
)
async def replace_camera_settings(
    camera_id: int,
    create_data: CameraSettingCreate,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """카메라 설정 전체 교체 (없으면 Upsert)"""
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera with id {camera_id} not found",
        )

    setting = db.query(CameraSetting).filter(CameraSetting.camera_id == camera_id).first()
    if not setting:
        setting = CameraSetting(camera_id=camera_id)
        db.add(setting)

    for key, value in create_data.model_dump().items():
        setattr(setting, key, value)

    db.commit()
    db.refresh(setting)

    return ApiSingleResponse(
        success=True,
        message="Camera settings replaced successfully",
        data=CameraSettingResponse.model_validate(setting),
    )
