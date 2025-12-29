"""
Server Monitoring initial data (Seed)
Based on GOP_서버모니터링_스키마.md
"""
from sqlalchemy.orm import Session

from app.models.server import ServerCategory, Server
from app.utils.enums import EnumServerType, EnumServerStatus


# 기본 서버 카테고리 데이터 (9종)
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
        print(f"✓ Server categories created: {created_count}")
    if existing_count > 0:
        print(f"✓ Server categories already exist: {existing_count}")

    return category_map


def create_sample_servers(db: Session, category_map: dict):
    """
    Create sample server instances for testing/demo

    Args:
        db: Database session
        category_map: Dictionary mapping type_server to category_id
    """
    # Check if any servers exist
    existing_count = db.query(Server).count()
    if existing_count > 0:
        print(f"✓ Sample servers already exist: {existing_count}")
        return

    # Sample server data
    sample_servers = [
        # VMS 서버 인스턴스
        {
            "category_id": category_map.get(EnumServerType.VMS),
            "name": "VMS-ab1120",
            "status": EnumServerStatus.NORMAL,
            "ip_address": "192.168.1.10",
            "port": 8080,
            "hostname": "vms-server-01",
            "cpu_usage": 45.0,
            "ram_usage": 62.0,
            "disk_usage": 78.0,
            "network_throughput": "125MB/s"
        },
        {
            "category_id": category_map.get(EnumServerType.VMS),
            "name": "VMS-ab1121",
            "status": EnumServerStatus.NORMAL,
            "ip_address": "192.168.1.11",
            "port": 8080,
            "hostname": "vms-server-02",
            "cpu_usage": 38.0,
            "ram_usage": 55.0,
            "disk_usage": 65.0,
            "network_throughput": "98MB/s"
        },
        # 지능형영상 분석 서버 인스턴스
        {
            "category_id": category_map.get(EnumServerType.AI_ANALYSIS),
            "name": "AI-ab2201",
            "status": EnumServerStatus.WARNING,
            "ip_address": "192.168.1.20",
            "port": 8081,
            "hostname": "ai-server-01",
            "cpu_usage": 82.0,
            "ram_usage": 78.0,
            "disk_usage": 45.0,
            "network_throughput": "256MB/s"
        },
        {
            "category_id": category_map.get(EnumServerType.AI_ANALYSIS),
            "name": "AI-ab2202",
            "status": EnumServerStatus.NORMAL,
            "ip_address": "192.168.1.21",
            "port": 8081,
            "hostname": "ai-server-02",
            "cpu_usage": 65.0,
            "ram_usage": 70.0,
            "disk_usage": 52.0,
            "network_throughput": "189MB/s"
        },
        {
            "category_id": category_map.get(EnumServerType.AI_ANALYSIS),
            "name": "AI-ab2203",
            "status": EnumServerStatus.NORMAL,
            "ip_address": "192.168.1.22",
            "port": 8081,
            "hostname": "ai-server-03",
            "cpu_usage": 58.0,
            "ram_usage": 68.0,
            "disk_usage": 48.0,
            "network_throughput": "203MB/s"
        },
        # 스트리밍 서버 인스턴스
        {
            "category_id": category_map.get(EnumServerType.STREAMING),
            "name": "STREAM-ab3301",
            "status": EnumServerStatus.NORMAL,
            "ip_address": "192.168.1.30",
            "port": 1935,
            "hostname": "stream-server-01",
            "cpu_usage": 52.0,
            "ram_usage": 48.0,
            "disk_usage": 35.0,
            "network_throughput": "512MB/s"
        },
        {
            "category_id": category_map.get(EnumServerType.STREAMING),
            "name": "STREAM-ab3302",
            "status": EnumServerStatus.NORMAL,
            "ip_address": "192.168.1.31",
            "port": 1935,
            "hostname": "stream-server-02",
            "cpu_usage": 48.0,
            "ram_usage": 52.0,
            "disk_usage": 38.0,
            "network_throughput": "489MB/s"
        },
        # 브로커 서버 인스턴스 (오류 상태 포함)
        {
            "category_id": category_map.get(EnumServerType.BROKER),
            "name": "BROKER-ab5501",
            "status": EnumServerStatus.ERROR,
            "ip_address": "192.168.1.50",
            "port": 5672,
            "hostname": "broker-server-01",
            "cpu_usage": 95.0,
            "ram_usage": 88.0,
            "disk_usage": 92.0,
            "network_throughput": "45MB/s"
        },
        {
            "category_id": category_map.get(EnumServerType.BROKER),
            "name": "BROKER-ab5502",
            "status": EnumServerStatus.NORMAL,
            "ip_address": "192.168.1.51",
            "port": 5672,
            "hostname": "broker-server-02",
            "cpu_usage": 42.0,
            "ram_usage": 55.0,
            "disk_usage": 68.0,
            "network_throughput": "78MB/s"
        },
    ]

    # Create servers
    created_count = 0
    for server_data in sample_servers:
        if server_data["category_id"] is not None:
            server = Server(**server_data)
            db.add(server)
            created_count += 1

    db.commit()
    print(f"✓ Sample servers created: {created_count}")


def initialize_server_data(db: Session, include_samples: bool = False):
    """
    Initialize server monitoring data

    Args:
        db: Database session
        include_samples: If True, also create sample server instances
    """
    print("Initializing server monitoring data...")

    # Create categories
    category_map = create_server_categories(db)

    # Optionally create sample servers
    if include_samples:
        create_sample_servers(db, category_map)

    print("✓ Server monitoring data initialization complete")
