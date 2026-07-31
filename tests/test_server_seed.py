"""
서버 시드 로직 테스트 — 필수 서버(PROXY/VMS/NVR/BROKER) 항상 보장 + 데모 count 가드.

근거: proxy-server-default-seed 결정(필수4 name-idempotent, 옵션A 비파괴).
- 카테고리: 유형별 idempotent (PROXY 포함 10종)
- 인스턴스 필수: 유형 기준 보장 — 그 유형 서버가 하나도 없을 때만 기본 생성(사용자 등록분 존중)
- 인스턴스 데모: servers 비었을 때만 최초 시드 (사용자 삭제 존중)
"""
from app.models.server import Server, ServerCategory
from app.utils.enums import EnumServerType, EnumServerStatus
from app.utils.init_server_data import (
    create_server_categories,
    create_sample_servers,
    initialize_server_data,
    DEFAULT_SERVER_CATEGORIES,
    DEFAULT_SAMPLE_SERVERS,
    MANDATORY_SERVER_TYPES,
)


def _server_by_name(db, name: str) -> Server | None:
    return db.query(Server).filter(Server.name == name).first()


def test_should_include_four_mandatory_types_when_defined():
    assert MANDATORY_SERVER_TYPES == {
        EnumServerType.PROXY,
        EnumServerType.VMS,
        EnumServerType.NVR_API,
        EnumServerType.BROKER,
    }


def test_should_register_proxy_category_when_seeded(test_db):
    category_map = create_server_categories(test_db)

    assert EnumServerType.PROXY in category_map
    proxy_cat = test_db.query(ServerCategory).filter(
        ServerCategory.type_server == EnumServerType.PROXY
    ).first()
    assert proxy_cat is not None
    assert proxy_cat.name == "프록시 서버"
    # 기존 9종 + PROXY = 10종
    assert test_db.query(ServerCategory).count() == len(DEFAULT_SERVER_CATEGORIES) == 10


def test_should_seed_all_when_table_empty(test_db):
    initialize_server_data(test_db)  # include_samples=True 기본

    assert test_db.query(ServerCategory).count() == 10
    assert test_db.query(Server).count() == len(DEFAULT_SAMPLE_SERVERS) == 15
    assert _server_by_name(test_db, "PROXY-ab0001") is not None


def test_should_ensure_mandatory_server_when_table_not_empty(test_db):
    # Arrange: 카테고리 생성 후 데모 유형 서버 1개 선삽입 → '비어있지 않은 DB' 모사
    category_map = create_server_categories(test_db)
    test_db.add(Server(
        category_id=category_map[EnumServerType.DB_API],
        name="EXISTING-1",
        status=EnumServerStatus.NORMAL,
        ip_address="10.0.0.1",
        port=8000,
    ))
    test_db.commit()
    assert test_db.query(Server).count() == 1

    # Act
    create_sample_servers(test_db, category_map)

    # Assert: 필수 4종은 테이블이 비어있지 않아도 등록됨 (핵심 버그 수정)
    assert _server_by_name(test_db, "PROXY-ab0001") is not None
    assert _server_by_name(test_db, "VMS-ab1120") is not None
    assert _server_by_name(test_db, "NVRAPI-ab7701") is not None
    assert _server_by_name(test_db, "BROKER-ab5501") is not None
    # 데모(AI 등)는 사용자 삭제 존중 — 비어있지 않았으므로 backfill 안 함
    assert _server_by_name(test_db, "AI-ab2201") is None


def test_should_not_duplicate_when_run_twice(test_db):
    initialize_server_data(test_db)
    first = test_db.query(Server).count()

    initialize_server_data(test_db)  # 재부팅 모사
    second = test_db.query(Server).count()

    assert first == second == 15
    assert test_db.query(ServerCategory).count() == 10


def test_should_recreate_mandatory_when_deleted(test_db):
    initialize_server_data(test_db)
    proxy = _server_by_name(test_db, "PROXY-ab0001")
    assert proxy is not None
    test_db.delete(proxy)
    test_db.commit()
    assert _server_by_name(test_db, "PROXY-ab0001") is None

    # 재부팅 모사 — 필수 유형에 서버가 없으므로 기본 인스턴스 재생성
    category_map = create_server_categories(test_db)
    create_sample_servers(test_db, category_map)

    assert _server_by_name(test_db, "PROXY-ab0001") is not None


def test_should_not_create_default_when_user_registered_same_type(test_db):
    """사용자가 직접 등록한 PROXY(다른 이름)가 있으면 기본 placeholder를 만들지 않는다.

    실사고 재현: 유형 기준 보장이라 그 유형에 서버가 1개라도 있으면 중복 생성 안 함.
    """
    category_map = create_server_categories(test_db)
    # 사용자가 커스텀 이름/주소로 PROXY 직접 등록
    test_db.add(Server(
        category_id=category_map[EnumServerType.PROXY],
        name="PROXY-user-01",
        status=EnumServerStatus.NORMAL,
        ip_address="192.168.1.30",
        port=8500,
        hostname="pids-proxy-01",
    ))
    test_db.commit()

    create_sample_servers(test_db, category_map)

    # 사용자 PROXY 유지 + 기본 placeholder는 생성 안 됨 → PROXY 유형은 1개뿐
    assert _server_by_name(test_db, "PROXY-user-01") is not None
    assert _server_by_name(test_db, "PROXY-ab0001") is None
    proxy_count = (
        test_db.query(Server)
        .filter(Server.category_id == category_map[EnumServerType.PROXY])
        .count()
    )
    assert proxy_count == 1
