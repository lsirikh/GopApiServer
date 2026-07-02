"""
ProxySetting Router
PRD: PRD_Device_Setting.md Section 5.1

GET/PATCH /api/servers/{server_id}/proxy-settings
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.routers.auth import get_current_account_user_optional
from app.models.server import Server
from app.models.device_setting import ProxySetting
from app.schemas.device_setting import ProxySettingCreate, ProxySettingUpdate, ProxySettingResponse
from app.schemas.common import ApiSingleResponse

router = APIRouter(tags=["Proxy Settings"])


@router.get(
    "/{server_id}/proxy-settings",
    response_model=ApiSingleResponse[ProxySettingResponse],
)
async def get_proxy_settings(
    server_id: int,
    current_user=Depends(get_current_account_user_optional),
    db: Session = Depends(get_db),
):
    """서버 Proxy 설정 조회 (없으면 기본값으로 Lazy 생성)"""
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server with id {server_id} not found",
        )

    setting = db.query(ProxySetting).filter(ProxySetting.server_id == server_id).first()
    if not setting:
        setting = ProxySetting(server_id=server_id)
        db.add(setting)
        db.commit()
        db.refresh(setting)

    return ApiSingleResponse(
        success=True,
        message="Proxy settings retrieved successfully",
        data=ProxySettingResponse.model_validate(setting),
    )


@router.patch(
    "/{server_id}/proxy-settings",
    response_model=ApiSingleResponse[ProxySettingResponse],
)
async def update_proxy_settings(
    server_id: int,
    update_data: ProxySettingUpdate,
    current_user=Depends(get_current_account_user_optional),
    db: Session = Depends(get_db),
):
    """서버 Proxy 설정 부분 수정 (없으면 Upsert)"""
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server with id {server_id} not found",
        )

    setting = db.query(ProxySetting).filter(ProxySetting.server_id == server_id).first()
    if not setting:
        setting = ProxySetting(server_id=server_id)
        db.add(setting)

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(setting, key, value)

    db.commit()
    db.refresh(setting)

    return ApiSingleResponse(
        success=True,
        message="Proxy settings updated successfully",
        data=ProxySettingResponse.model_validate(setting),
    )


@router.put(
    "/{server_id}/proxy-settings",
    response_model=ApiSingleResponse[ProxySettingResponse],
)
async def replace_proxy_settings(
    server_id: int,
    create_data: ProxySettingCreate,
    current_user=Depends(get_current_account_user_optional),
    db: Session = Depends(get_db),
):
    """서버 Proxy 설정 전체 교체 (없으면 Upsert)"""
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server with id {server_id} not found",
        )

    setting = db.query(ProxySetting).filter(ProxySetting.server_id == server_id).first()
    if not setting:
        setting = ProxySetting(server_id=server_id)
        db.add(setting)

    for key, value in create_data.model_dump().items():
        setattr(setting, key, value)

    db.commit()
    db.refresh(setting)

    return ApiSingleResponse(
        success=True,
        message="Proxy settings replaced successfully",
        data=ProxySettingResponse.model_validate(setting),
    )
