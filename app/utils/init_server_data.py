"""
Server Monitoring initial data (Seed)
Based on GOP_서버모니터링_스키마.md
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

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
]


# Static seed — 9종 카테고리 각 1개 이상 인스턴스 보장 (v6.1: TRANSCODER/DB_API/NVR_API/SPEAKER_API/ENCLOSURE_API 5종 추가)
# Server 모델 필드만 사용: category_id/name/status/ip_address/port/hostname
# (cpu/ram/disk 등 실시간 메트릭은 ServerMetric 테이블 소관 — 별도 워커가 채움)
DEFAULT_SAMPLE_SERVERS = [
    {"type_server": EnumServerType.VMS,           "name": "VMS-ab1120",     "status": EnumServerStatus.NORMAL,  "ip_address": "192.168.1.10", "port": 8080, "hostname": "vms-server-01"},
    {"type_server": EnumServerType.VMS,           "name": "VMS-ab1121",     "status": EnumServerStatus.NORMAL,  "ip_address": "192.168.1.11", "port": 8080, "hostname": "vms-server-02"},
    {"type_server": EnumServerType.AI_ANALYSIS,   "name": "AI-ab2201",      "status": EnumServerStatus.WARNING, "ip_address": "192.168.1.20", "port": 8081, "hostname": "ai-server-01"},
    {"type_server": EnumServerType.AI_ANALYSIS,   "name": "AI-ab2202",      "status": EnumServerStatus.NORMAL,  "ip_address": "192.168.1.21", "port": 8081, "hostname": "ai-server-02"},
    {"type_server": EnumServerType.AI_ANALYSIS,   "name": "AI-ab2203",      "status": EnumServerStatus.NORMAL,  "ip_address": "192.168.1.22", "port": 8081, "hostname": "ai-server-03"},
    {"type_server": EnumServerType.STREAMING,     "name": "STREAM-ab3301",  "status": EnumServerStatus.NORMAL,  "ip_address": "192.168.1.30", "port": 1935, "hostname": "stream-server-01"},
    {"type_server": EnumServerType.STREAMING,     "name": "STREAM-ab3302",  "status": EnumServerStatus.NORMAL,  "ip_address": "192.168.1.31", "port": 1935, "hostname": "stream-server-02"},
    {"type_server": EnumServerType.TRANSCODER,    "name": "TRANS-ab4401",   "status": EnumServerStatus.NORMAL,  "ip_address": "192.168.1.40", "port": 8085, "hostname": "trans-server-01"},
    {"type_server": EnumServerType.BROKER,        "name": "BROKER-ab5501",  "status": EnumServerStatus.ERROR,   "ip_address": "192.168.1.50", "port": 5672, "hostname": "broker-server-01"},
    {"type_server": EnumServerType.BROKER,        "name": "BROKER-ab5502",  "status": EnumServerStatus.NORMAL,  "ip_address": "192.168.1.51", "port": 5672, "hostname": "broker-server-02"},
    {"type_server": EnumServerType.DB_API,        "name": "DBAPI-ab6601",   "status": EnumServerStatus.NORMAL,  "ip_address": "192.168.1.60", "port": 8000, "hostname": "dbapi-server-01"},
    {"type_server": EnumServerType.NVR_API,       "name": "NVRAPI-ab7701",  "status": EnumServerStatus.NORMAL,  "ip_address": "192.168.1.70", "port": 8090, "hostname": "nvrapi-server-01"},
    {"type_server": EnumServerType.SPEAKER_API,   "name": "SPKAPI-ab8801",  "status": EnumServerStatus.NORMAL,  "ip_address": "192.168.1.80", "port": 8091, "hostname": "spkapi-server-01"},
    {"type_server": EnumServerType.ENCLOSURE_API, "name": "ENCAPI-ab9901",  "status": EnumServerStatus.NORMAL,  "ip_address": "192.168.1.90", "port": 8092, "hostname": "encapi-server-01"},
]


def _build_sample_server_rows(category_map: dict) -> list[dict]:
    """DEFAULT_SAMPLE_SERVERS의 type_server를 category_id로 변환한 insert-ready row 목록.

    카테고리 매핑이 없으면 그 인스턴스는 스킵. sync/async 공통 사용.
    """
    rows: list[dict] = []
    for entry in DEFAULT_SAMPLE_SERVERS:
        category_id = category_map.get(entry["type_server"])
        if category_id is None:
            continue
        row = {k: v for k, v in entry.items() if k != "type_server"}
        row["category_id"] = category_id
        rows.append(row)
    return rows


def create_server_categories(db: Session) -> dict:
    """
    Create default server categories if not exists

    Args:
        db: Database session

    Returns:
        Dictionary mapping type_server to category_id
    """
    category_map = {}
    created_count = 0
    existing_count = 0

    for cat_data in DEFAULT_SERVER_CATEGORIES:
        # Check if category already exists
        existing = db.query(ServerCategory).filter(
            ServerCategory.type_server == cat_data["type_server"]
        ).first()

        if existing:
            category_map[cat_data["type_server"]] = existing.id
            existing_count += 1
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

    return category_map


def create_sample_servers(db: Session, category_map: dict):
    """Create sample server instances for testing/demo (idempotent).

    카테고리 9종을 모두 커버하는 인스턴스를 Static seed로 삽입.
    """
    existing_count = db.query(Server).count()
    if existing_count > 0:
        print(f"[OK] Sample servers already exist: {existing_count}")
        return

    rows = _build_sample_server_rows(category_map)
    for row in rows:
        db.add(Server(**row))

    db.commit()
    print(f"[OK] Sample servers created: {len(rows)}")


def initialize_server_data(db: Session, include_samples: bool = True):
    """Initialize server monitoring data.

    Args:
        db: Database session
        include_samples: v6.1부터 default True — Static seed 정책 (반드시 만들어져야 하는 서버).
    """
    print("Initializing server monitoring data...")

    category_map = create_server_categories(db)

    if include_samples:
        create_sample_servers(db, category_map)

    print("[OK] Server monitoring data initialization complete")


# ============================================================================
# Async variants (v6.0 Phase 2 — asyncpg / AsyncSession)
# ============================================================================


async def create_server_categories_async(db: AsyncSession) -> dict:
    """
    Async: Create default server categories if not exists.

    Args:
        db: AsyncSession

    Returns:
        Dictionary mapping type_server to category_id
    """
    category_map: dict = {}
    created_count = 0
    existing_count = 0

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

    return category_map


async def create_sample_servers_async(db: AsyncSession, category_map: dict) -> None:
    """Async: Create sample server instances for testing/demo (idempotent)."""
    from sqlalchemy import func
    result = await db.execute(select(func.count()).select_from(Server))
    existing_count = result.scalar() or 0
    if existing_count > 0:
        print(f"[OK] Sample servers already exist: {existing_count}")
        return

    rows = _build_sample_server_rows(category_map)
    for row in rows:
        db.add(Server(**row))

    await db.commit()
    print(f"[OK] Sample servers created: {len(rows)}")


async def initialize_server_data_async(
    db: AsyncSession, include_samples: bool = True
) -> None:
    """Async: Initialize server monitoring data.

    Args:
        db: AsyncSession
        include_samples: v6.1부터 default True — Static seed 정책.
    """
    print("Initializing server monitoring data (async)...")

    category_map = await create_server_categories_async(db)

    if include_samples:
        await create_sample_servers_async(db, category_map)

    print("[OK] Server monitoring data initialization complete (async)")
