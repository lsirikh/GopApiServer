"""
ProxySetting Router
PRD: PRD_Device_Setting.md Section 5.1

GET/PATCH/PUT /api/servers/{server_id}/proxy-settings

기획상 PROXY 서버 전용(PidsProxy 운용설정) — 비-PROXY 서버 요청은 404 로 거부하며
lazy-create 하지 않는다. (v6.3 후속 proxy_settings_typed)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_async_db
from app.routers.auth import get_current_account_user_optional_async
from app.models.server import Server, ServerCategory
from app.models.device_setting import ProxySetting
from app.utils.enums import EnumServerType
from app.schemas.device_setting import ProxySettingCreate, ProxySettingUpdate, ProxySettingResponse
from app.schemas.common import ApiSingleResponse

router = APIRouter()


async def _get_proxy_server_or_404(db: AsyncSession, server_id: int) -> Server:
    """server_id 가 PROXY 유형 서버일 때만 반환. 아니면 404.

    proxy-settings 는 기획상 PROXY 서버 전용(PidsProxy 운용설정).
    비-PROXY 서버 요청은 lazy-create 하지 않고 404 로 거부한다.
    """
    row = (
        await db.execute(
            select(Server, ServerCategory.type_server)
            .join(ServerCategory, Server.category_id == ServerCategory.id)
            .where(Server.id == server_id)
        )
    ).first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server with id {server_id} not found",
        )
    server, type_server = row
    if type_server != EnumServerType.PROXY:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server {server_id} is not a PROXY server; proxy-settings applies to PROXY servers only",
        )
    return server


@router.get(
    "/{server_id}/proxy-settings",
    response_model=ApiSingleResponse[ProxySettingResponse],
)
async def get_proxy_settings(
    server_id: int,
    current_user=Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db),
):
    """PROXY 서버 전용 — Proxy 설정 조회 (없으면 기본값으로 Lazy 생성; 비-PROXY 서버는 404)"""
    await _get_proxy_server_or_404(db, server_id)

    setting = (
        await db.execute(select(ProxySetting).where(ProxySetting.server_id == server_id))
    ).scalars().first()
    if not setting:
        setting = ProxySetting(server_id=server_id)
        db.add(setting)
        await db.commit()
        await db.refresh(setting)

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
    current_user=Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db),
):
    """PROXY 서버 전용 — Proxy 설정 부분 수정 (없으면 Upsert; 비-PROXY 서버는 404)"""
    await _get_proxy_server_or_404(db, server_id)

    setting = (
        await db.execute(select(ProxySetting).where(ProxySetting.server_id == server_id))
    ).scalars().first()
    if not setting:
        setting = ProxySetting(server_id=server_id)
        db.add(setting)

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(setting, key, value)

    await db.commit()
    await db.refresh(setting)

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
    current_user=Depends(get_current_account_user_optional_async),
    db: AsyncSession = Depends(get_async_db),
):
    """PROXY 서버 전용 — Proxy 설정 전체 교체 (없으면 Upsert; 비-PROXY 서버는 404)"""
    await _get_proxy_server_or_404(db, server_id)

    setting = (
        await db.execute(select(ProxySetting).where(ProxySetting.server_id == server_id))
    ).scalars().first()
    if not setting:
        setting = ProxySetting(server_id=server_id)
        db.add(setting)

    for key, value in create_data.model_dump().items():
        setattr(setting, key, value)

    await db.commit()
    await db.refresh(setting)

    return ApiSingleResponse(
        success=True,
        message="Proxy settings replaced successfully",
        data=ProxySettingResponse.model_validate(setting),
    )
