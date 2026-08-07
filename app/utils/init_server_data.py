"""
Server Monitoring initial data (Seed)
Based on GOP_서버모니터링_스키마.md
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.config import settings
from app.models.server import ServerCategory, Server
from app.utils.enums import EnumServerType, EnumServerStatus


# 기본 서버 카테고리 (Static seed — 무조건 시드)
DEFAULT_SERVER_CATEGORIES = [
    {
        "name": "VMS 서버",
        "type_server": EnumServerType.VMS,
        "description": "Video Management System",
        "sort_order": 1
    },
    {
        "name": "지능형영상 분석 서버",
        "type_server": EnumServerType.AI_ANALYSIS,
        "description": "AI 기반 영상 분석 서버",
        "sort_order": 2
    },
    {
        "name": "스트리밍 서버",
        "type_server": EnumServerType.STREAMING,
        "description": "실시간 스트리밍 서버",
        "sort_order": 3
    },
    {
        "name": "트랜스코더 서버",
        "type_server": EnumServerType.TRANSCODER,
        "description": "영상 변환 서버",
        "sort_order": 4
    },
    {
        "name": "브로커서버",
        "type_server": EnumServerType.BROKER,
        "description": "메시지 브로커 서버",
        "sort_order": 5
    },
    {
        "name": "DB API 서버",
        "type_server": EnumServerType.DB_API,
        "description": "데이터베이스 API 서버",
        "sort_order": 6
    },
    {
        "name": "NVR API 서버",
        "type_server": EnumServerType.NVR_API,
        "description": "Network Video Recorder API 서버",
        "sort_order": 7
    },
    {
        "name": "SPEAKER API 서버",
        "type_server": EnumServerType.SPEAKER_API,
        "description": "스피커 제어 API 서버",
        "sort_order": 8
    },
    {
        "name": "함체관리 API 서버",
        "type_server": EnumServerType.ENCLOSURE_API,
        "description": "함체 관리 API 서버",
        "sort_order": 9
    },
    {
        "name": "프록시 서버",
        "type_server": EnumServerType.PROXY,
        "description": "PidsProxy 서버 (장비 등록/운용 관문)",
        "sort_order": 10
    },
]


# 필수 유형 기본 인스턴스 정의 — 유형당 정확히 1행.
#   v6.3-server_seed_env_gate(2026-08-07) 2차: **데모 인스턴스 정의 전량 삭제**(PM 지시).
#   과거 15행(데모 11 + 필수 4)에서 필수 4행만 남겼다. 실체 없는 데모 서버가 관제
#   대시보드에 가짜 WARNING/ERROR 로 집계되던 문제의 근본 제거 — 게이트로 끄는 게 아니라
#   정의 자체를 없앤다.
# Server 모델 필드만 사용: category_id/name/status/ip_address/port/hostname
# (cpu/ram/disk 등 실시간 메트릭은 ServerMetric 테이블 소관 — 별도 워커가 채움.
#  ★ 메트릭 미수신을 감지해 status 를 바꾸는 watchdog 은 없다 — status 는 아래 리터럴이나
#    PUT /servers/{id} 로만 바뀐다. 그래서 여기 리터럴이 곧 대시보드 집계값이 된다.
#    따라서 아래 4행은 반드시 NORMAL 이어야 한다.)
DEFAULT_MANDATORY_SERVERS = [
    {"type_server": EnumServerType.PROXY,   "name": "PROXY-ab0001",  "status": EnumServerStatus.NORMAL, "ip_address": "192.168.1.100", "port": 8100, "hostname": "proxy-server-01"},
    {"type_server": EnumServerType.VMS,     "name": "VMS-ab1120",    "status": EnumServerStatus.NORMAL, "ip_address": "192.168.1.10",  "port": 8080, "hostname": "vms-server-01"},
    {"type_server": EnumServerType.NVR_API, "name": "NVRAPI-ab7701", "status": EnumServerStatus.NORMAL, "ip_address": "192.168.1.70",  "port": 8090, "hostname": "nvrapi-server-01"},
    {"type_server": EnumServerType.BROKER,  "name": "BROKER-ab5501", "status": EnumServerStatus.NORMAL, "ip_address": "192.168.1.50",  "port": 5672, "hostname": "broker-server-01"},
]


# 필수 서버 유형 — 유형 기준 보장. 해당 유형 서버가 하나도 없으면 기본 인스턴스 1개 생성.
# (사용자가 직접 등록한 동일 유형 서버가 있으면 중복 생성하지 않음.)
# "일단" 4종 (추후 확장 가능). DEFAULT_MANDATORY_SERVERS 와 1:1 대응이어야 한다.
MANDATORY_SERVER_TYPES = {
    EnumServerType.PROXY,
    EnumServerType.VMS,
    EnumServerType.NVR_API,
    EnumServerType.BROKER,
}


def _build_mandatory_server_rows(category_map: dict) -> list[tuple]:
    """DEFAULT_MANDATORY_SERVERS를 (type_server, insert-ready row) 목록으로 변환.

    카테고리 매핑이 없으면 그 인스턴스는 스킵. sync/async 공통 사용.
    """
    rows: list[tuple] = []
    for entry in DEFAULT_MANDATORY_SERVERS:
        category_id = category_map.get(entry["type_server"])
        if category_id is None:
            continue
        row = {k: v for k, v in entry.items() if k != "type_server"}
        row["category_id"] = category_id
        rows.append((entry["type_server"], row))
    return rows


def create_server_categories(db: Session, *, create_missing: bool = True) -> dict:
    """
    Create default server categories if not exists

    Args:
        db: Database session
        create_missing: False 면 누락 카테고리를 만들지 않고 '기존 것만' 매핑한다
            (INIT_SERVER_CATEGORIES=false — 운영자가 지운 카테고리의 부활 차단).
            끄더라도 인스턴스 시드가 기존 카테고리에는 계속 붙을 수 있게 map 은 반환한다.

    Returns:
        Dictionary mapping type_server to category_id
    """
    category_map = {}
    created_count = 0
    existing_count = 0
    skipped_count = 0

    for cat_data in DEFAULT_SERVER_CATEGORIES:
        # Check if category already exists
        existing = db.query(ServerCategory).filter(
            ServerCategory.type_server == cat_data["type_server"]
        ).first()

        if existing:
            category_map[cat_data["type_server"]] = existing.id
            existing_count += 1
        elif not create_missing:
            skipped_count += 1
        else:
            # Create new category
            category = ServerCategory(**cat_data)
            db.add(category)
            db.commit()
            db.refresh(category)
            category_map[cat_data["type_server"]] = category.id
            created_count += 1

    if created_count > 0:
        print(f"[OK] Server categories created: {created_count}")
    if existing_count > 0:
        print(f"[OK] Server categories already exist: {existing_count}")
    if skipped_count > 0:
        print(f"[SKIP] Server categories not created: {skipped_count} (INIT_SERVER_CATEGORIES=false)")

    return category_map


def ensure_mandatory_servers(
    db: Session,
    category_map: dict,
    *,
    include_mandatory: bool | None = None,
):
    """필수 유형 서버 인스턴스 보장.

    해당 '유형'에 서버가 하나도 없을 때만 기본 인스턴스를 **정확히 1개** 생성한다.
    유형 기준 보장이라 사용자가 직접 등록한 동일 유형 서버가 있으면 중복 생성하지 않는다.

    Args:
        include_mandatory: None 이면 settings.INIT_SERVER_MANDATORY 를 따른다.
    """
    if include_mandatory is None:
        include_mandatory = settings.INIT_SERVER_MANDATORY

    if not include_mandatory:
        print("[SKIP] Mandatory servers (INIT_SERVER_MANDATORY=false)")
        return

    rows = _build_mandatory_server_rows(category_map)

    # 필수 유형별 '이미 서버가 있는가' 스냅샷 (사용자 등록분 존중 — 중복 방지)
    mandatory_type_has_server = {
        t: db.query(Server).filter(Server.category_id == category_map[t]).first() is not None
        for t in MANDATORY_SERVER_TYPES if t in category_map
    }

    created = 0
    for type_server, row in rows:
        if mandatory_type_has_server.get(type_server, False):
            continue   # 그 유형 서버가 이미 존재 → 보장 충족(중복 안 만듦)
        db.add(Server(**row))
        # ★ 스냅샷 즉시 갱신 — 정의가 유형당 1행이라 지금은 방어적이지만, 향후 같은 유형이
        #   여러 행 추가돼도 '유형당 1개' 보장이 깨지지 않게 유지한다(2026-08-07 VMS 2개 부활 사고).
        mandatory_type_has_server[type_server] = True
        created += 1

    if created:
        db.commit()
    print(f"[OK] Mandatory servers ensured (+{created})")


def initialize_server_data(
    db: Session,
    *,
    include_categories: bool | None = None,
    include_mandatory: bool | None = None,
):
    """Initialize server monitoring data.

    Args:
        db: Database session
        include_categories: None 이면 settings.INIT_SERVER_CATEGORIES.
        include_mandatory: None 이면 settings.INIT_SERVER_MANDATORY.

    Note:
        v6.3-server_seed_env_gate — 서버 시드는 INIT_SAMPLE_DATA 와 무관한 독립 게이트다.
        2차(2026-08-07)에 데모 인스턴스 정의·게이트를 전량 제거해 카테고리/필수 2단만 남겼다.
        인자를 명시하면 env 를 덮어쓴다(테스트 결정성 확보용).
    """
    print("Initializing server monitoring data...")

    if include_categories is None:
        include_categories = settings.INIT_SERVER_CATEGORIES

    category_map = create_server_categories(db, create_missing=include_categories)
    ensure_mandatory_servers(db, category_map, include_mandatory=include_mandatory)

    print("[OK] Server monitoring data initialization complete")


# ============================================================================
# Async variants (v6.0 Phase 2 — asyncpg / AsyncSession)
# ============================================================================


async def create_server_categories_async(
    db: AsyncSession, *, create_missing: bool = True
) -> dict:
    """
    Async: Create default server categories if not exists.

    Args:
        db: AsyncSession
        create_missing: sync `create_server_categories` 와 동일 계약.

    Returns:
        Dictionary mapping type_server to category_id
    """
    category_map: dict = {}
    created_count = 0
    existing_count = 0
    skipped_count = 0

    for cat_data in DEFAULT_SERVER_CATEGORIES:
        # Check if category already exists
        result = await db.execute(
            select(ServerCategory).where(
                ServerCategory.type_server == cat_data["type_server"]
            )
        )
        existing = result.scalars().first()

        if existing:
            category_map[cat_data["type_server"]] = existing.id
            existing_count += 1
        elif not create_missing:
            skipped_count += 1
        else:
            # Create new category
            category = ServerCategory(**cat_data)
            db.add(category)
            await db.commit()
            await db.refresh(category)
            category_map[cat_data["type_server"]] = category.id
            created_count += 1

    if created_count > 0:
        print(f"[OK] Server categories created: {created_count}")
    if existing_count > 0:
        print(f"[OK] Server categories already exist: {existing_count}")
    if skipped_count > 0:
        print(f"[SKIP] Server categories not created: {skipped_count} (INIT_SERVER_CATEGORIES=false)")

    return category_map


async def ensure_mandatory_servers_async(
    db: AsyncSession,
    category_map: dict,
    *,
    include_mandatory: bool | None = None,
) -> None:
    """Async: 필수 유형 서버 인스턴스 보장 (유형당 정확히 1개).

    sync `ensure_mandatory_servers` 와 동일 계약 — 게이트·중복방지 시맨틱을 함께 유지한다.
    """
    if include_mandatory is None:
        include_mandatory = settings.INIT_SERVER_MANDATORY

    if not include_mandatory:
        print("[SKIP] Mandatory servers async (INIT_SERVER_MANDATORY=false)")
        return

    rows = _build_mandatory_server_rows(category_map)

    # 필수 유형별 '이미 서버가 있는가' 스냅샷 (사용자 등록분 존중 — 중복 방지)
    mandatory_type_has_server = {}
    for t in MANDATORY_SERVER_TYPES:
        if t not in category_map:
            continue
        exists = (await db.execute(
            select(Server).where(Server.category_id == category_map[t])
        )).scalars().first()
        mandatory_type_has_server[t] = exists is not None

    created = 0
    for type_server, row in rows:
        if mandatory_type_has_server.get(type_server, False):
            continue
        db.add(Server(**row))
        mandatory_type_has_server[type_server] = True   # sync 와 동일 방어
        created += 1

    if created:
        await db.commit()
    print(f"[OK] Mandatory servers ensured async (+{created})")


async def initialize_server_data_async(
    db: AsyncSession,
    *,
    include_categories: bool | None = None,
    include_mandatory: bool | None = None,
) -> None:
    """Async: Initialize server monitoring data.

    sync `initialize_server_data` 와 동일 계약.

    Note:
        현재 main.py 의 `initialize_database_async()` 는 sync 경로를 호출하므로 이 함수는
        아직 미사용이다. 재배선 시 게이트가 누락되지 않도록 동일 시맨틱을 유지한다.
    """
    print("Initializing server monitoring data (async)...")

    if include_categories is None:
        include_categories = settings.INIT_SERVER_CATEGORIES

    category_map = await create_server_categories_async(db, create_missing=include_categories)
    await ensure_mandatory_servers_async(
        db, category_map, include_mandatory=include_mandatory
    )

    print("[OK] Server monitoring data initialization complete (async)")
