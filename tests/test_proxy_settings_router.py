"""
Test: ProxySetting Router — PROXY 서버 전용 강제 (v6.3 후속 proxy_settings_typed)
PRD: PRD_Device_Setting.md Section 5.1

★ 재작성 배경: 기존 sync `client`(TestClient) 방식은 async 라우터의 `get_async_db` 를
  오버라이드하지 않아, proxy_settings 라우터가 격리 :memory: 가 아니라 **실 파일 DB(data/gop.db)**
  를 읽던 사전 격리 버그가 있었다(id 우연일치로 통과). 리포 표준(test_grant_enforcement_http)대로
  **격리 aiosqlite(async_db 픽스처)에 엔드포인트 함수를 직접 태우는** 방식으로 전환.
"""
from __future__ import annotations

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select

from app.models.server import Server, ServerCategory
from app.models.device_setting import ProxySetting
from app.schemas.device_setting import ProxySettingCreate, ProxySettingUpdate
from app.utils.enums import EnumServerType, EnumServerStatus
from app.routers.proxy_settings import (
    _get_proxy_server_or_404,
    get_proxy_settings,
    update_proxy_settings,
    replace_proxy_settings,
)

pytestmark = pytest.mark.asyncio  # asyncio STRICT mode


async def _mk_server(db, type_server: EnumServerType) -> Server:
    cat = ServerCategory(name=f"{type_server.value} Cat", type_server=type_server)
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    srv = Server(
        name=f"{type_server.value}-SRV",
        category_id=cat.id,
        status=EnumServerStatus.NORMAL,
        ip_address="1.1.1.1",
        port=8080,
    )
    db.add(srv)
    await db.commit()
    await db.refresh(srv)
    return srv


# ----------------------------- 유형 가드 헬퍼 -----------------------------

async def test_should_return_server_when_type_is_proxy(async_db):
    srv = await _mk_server(async_db, EnumServerType.PROXY)
    got = await _get_proxy_server_or_404(async_db, srv.id)
    assert got.id == srv.id


async def test_should_404_when_helper_gets_non_proxy(async_db):
    srv = await _mk_server(async_db, EnumServerType.VMS)
    with pytest.raises(HTTPException) as ei:
        await _get_proxy_server_or_404(async_db, srv.id)
    assert ei.value.status_code == 404


async def test_should_404_when_helper_gets_missing_server(async_db):
    with pytest.raises(HTTPException) as ei:
        await _get_proxy_server_or_404(async_db, 9999)
    assert ei.value.status_code == 404


# ------------------------------- GET -------------------------------

async def test_should_lazy_create_when_get_proxy(async_db):
    srv = await _mk_server(async_db, EnumServerType.PROXY)
    resp = await get_proxy_settings(server_id=srv.id, current_user=None, db=async_db)
    assert resp.success is True
    assert resp.data.server_id == srv.id
    assert resp.data.operation_mode == "NORMAL"
    assert resp.data.windy_mode == "wind0"


async def test_should_return_same_setting_when_get_twice(async_db):
    srv = await _mk_server(async_db, EnumServerType.PROXY)
    first = await get_proxy_settings(server_id=srv.id, current_user=None, db=async_db)
    second = await get_proxy_settings(server_id=srv.id, current_user=None, db=async_db)
    assert first.data.id == second.data.id  # 중복 생성 안 함


async def test_should_404_when_get_non_proxy(async_db):
    srv = await _mk_server(async_db, EnumServerType.VMS)
    with pytest.raises(HTTPException) as ei:
        await get_proxy_settings(server_id=srv.id, current_user=None, db=async_db)
    assert ei.value.status_code == 404


async def test_should_not_lazy_create_when_get_non_proxy(async_db):
    """비-PROXY 서버는 lazy-create 도 하지 않음 → proxy_settings row 0"""
    srv = await _mk_server(async_db, EnumServerType.VMS)
    with pytest.raises(HTTPException):
        await get_proxy_settings(server_id=srv.id, current_user=None, db=async_db)
    count = (await async_db.execute(select(func.count()).select_from(ProxySetting))).scalar()
    assert count == 0


# ------------------------------- PATCH -------------------------------

async def test_should_upsert_when_patch_proxy(async_db):
    srv = await _mk_server(async_db, EnumServerType.PROXY)
    resp = await update_proxy_settings(
        server_id=srv.id,
        update_data=ProxySettingUpdate(operation_mode="REGISTER"),
        current_user=None,
        db=async_db,
    )
    assert resp.data.operation_mode == "REGISTER"
    assert resp.data.windy_mode == "wind0"  # default preserved


async def test_should_404_when_patch_non_proxy(async_db):
    srv = await _mk_server(async_db, EnumServerType.VMS)
    with pytest.raises(HTTPException) as ei:
        await update_proxy_settings(
            server_id=srv.id,
            update_data=ProxySettingUpdate(operation_mode="REGISTER"),
            current_user=None,
            db=async_db,
        )
    assert ei.value.status_code == 404


# ------------------------------- PUT -------------------------------

async def test_should_replace_when_put_proxy(async_db):
    srv = await _mk_server(async_db, EnumServerType.PROXY)
    resp = await replace_proxy_settings(
        server_id=srv.id,
        create_data=ProxySettingCreate(operation_mode="REGISTER", windy_mode="wind3"),
        current_user=None,
        db=async_db,
    )
    assert resp.data.operation_mode == "REGISTER"
    assert resp.data.windy_mode == "wind3"
    assert resp.message == "Proxy settings replaced successfully"


async def test_should_404_when_put_non_proxy(async_db):
    srv = await _mk_server(async_db, EnumServerType.VMS)
    with pytest.raises(HTTPException) as ei:
        await replace_proxy_settings(
            server_id=srv.id,
            create_data=ProxySettingCreate(operation_mode="NORMAL", windy_mode="wind0"),
            current_user=None,
            db=async_db,
        )
    assert ei.value.status_code == 404
