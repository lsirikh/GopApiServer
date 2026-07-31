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
    {
        "name": "프록시 서버",
        "type_server": EnumServerType.PROXY,
        "description": "PidsProxy 서버 (장비 등록/운용 관문)",
        "sort_order": 10
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
    {"type_server": EnumServerType.PROXY,         "name": "PROXY-ab0001",   "status": EnumServerStatus.NORMAL,  "ip_address": "192.168.1.100", "port": 8100, "hostname": "proxy-server-01"},
]


# 필수 서버 유형 — 유형 기준 보장. 해당 유형 서버가 하나도 없으면 기본 인스턴스 생성.
# (사용자가 직접 등록한 동일 유형 서버가 있으면 중복 생성하지 않음.)
# "일단" 4종 (추후 확장 가능). 나머지는 데모 취급(빈 테이블일 때만 최초 시드).
MANDATORY_SERVER_TYPES = {
    EnumServerType.PROXY,
    EnumServerType.VMS,
    EnumServerType.NVR_API,
    EnumServerType.BROKER,
}


def _build_sample_server_rows(category_map: dict) -> list[tuple]:
    """DEFAULT_SAMPLE_SERVERS를 (type_server, insert-ready row) 목록으로 변환.

    카테고리 매핑이 없으면 그 인스턴스는 스킵. sync/async 공통 사용.
    """
    rows: list[tuple] = []
    for entry in DEFAULT_SAMPLE_SERVERS:
        category_id = category_map.get(entry["type_server"])
        if category_id is None:
            continue
        row = {k: v for k, v in entry.items() if k != "type_server"}
        row["category_id"] = category_id
        rows.append((entry["type_server"], row))
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
    """서버 인스턴스 시드.

    - 필수(MANDATORY_SERVER_TYPES): 해당 '유형'에 서버가 하나도 없을 때만 기본 인스턴스 생성.
      유형 기준 보장이라 사용자가 직접 등록한 동일 유형 서버가 있으면 중복 생성하지 않음.
    - 데모(그 외): servers 테이블이 비었을 때만 최초 1회 시드 (사용자 삭제 존중).
    """
    rows = _build_sample_server_rows(category_map)
    demo_seeded_before = db.query(Server).count() > 0   # 루프 전 스냅샷

    # 필수 유형별 '이미 서버가 있는가' 스냅샷 (사용자 등록분 존중 — 중복 방지)
    mandatory_type_has_server = {
        t: db.query(Server).filter(Server.category_id == category_map[t]).first() is not None
        for t in MANDATORY_SERVER_TYPES if t in category_map
    }

    created_mandatory = 0
    created_demo = 0
    for type_server, row in rows:
        if type_server in MANDATORY_SERVER_TYPES:
            if mandatory_type_has_server.get(type_server):
                continue   # 그 유형 서버가 이미 존재 → 보장 충족(중복 안 만듦)
            db.add(Server(**row))
            created_mandatory += 1
        else:
            if demo_seeded_before:
                continue
            db.add(Server(**row))
            created_demo += 1

    if created_mandatory or created_demo:
        db.commit()
    print(f"[OK] Servers ensured (mandatory +{created_mandatory}, demo +{created_demo})")


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
    """Async: 서버 인스턴스 시드 (필수=유형 기준 보장 / 데모=count 가드)."""
    from sqlalchemy import func
    rows = _build_sample_server_rows(category_map)

    total = (await db.execute(select(func.count()).select_from(Server))).scalar() or 0
    demo_seeded_before = total > 0

    # 필수 유형별 '이미 서버가 있는가' 스냅샷 (사용자 등록분 존중 — 중복 방지)
    mandatory_type_has_server = {}
    for t in MANDATORY_SERVER_TYPES:
        if t not in category_map:
            continue
        exists = (await db.execute(
            select(Server).where(Server.category_id == category_map[t])
        )).scalars().first()
        mandatory_type_has_server[t] = exists is not None

    created_mandatory = 0
    created_demo = 0
    for type_server, row in rows:
        if type_server in MANDATORY_SERVER_TYPES:
            if mandatory_type_has_server.get(type_server):
                continue   # 그 유형 서버가 이미 존재 → 보장 충족(중복 안 만듦)
            db.add(Server(**row))
            created_mandatory += 1
        else:
            if demo_seeded_before:
                continue
            db.add(Server(**row))
            created_demo += 1

    if created_mandatory or created_demo:
        await db.commit()
    print(f"[OK] Servers ensured async (mandatory +{created_mandatory}, demo +{created_demo})")


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
