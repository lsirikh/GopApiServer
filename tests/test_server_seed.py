"""
서버 시드 로직 테스트 — 2단 env 게이트 + 필수 유형당 정확히 1개 보장.

근거:
- proxy-server-default-seed 결정(필수4 유형 기준 보장)
- v6.3-server_seed_env_gate (2026-08-07)
  · 1차: INIT_SAMPLE_DATA 와 독립된 게이트 도입 + 결함 A(같은 유형 복수 생성) 수정
  · 2차: **데모 인스턴스 정의·게이트 전량 제거**(PM 지시) — 시드가 만드는 서버는 필수 4종뿐

계약:
- 카테고리: 유형별 idempotent (PROXY 포함 10종). INIT_SERVER_CATEGORIES=false 면 미생성.
- 인스턴스: 필수 4종만. 그 유형에 서버가 하나도 없을 때만 **유형당 1개** 생성.
  INIT_SERVER_MANDATORY=false 면 서버 인스턴스가 하나도 만들어지지 않는다.

※ 게이트는 테스트마다 명시 인자로 넘긴다 — settings(.env) 의존이면 환경에 따라 결과가 흔들린다.
"""
import pytest

from app.config import settings
from app.models.server import Server, ServerCategory
from app.utils.enums import EnumServerType, EnumServerStatus
from app.utils.init_server_data import (
    create_server_categories,
    ensure_mandatory_servers,
    initialize_server_data,
    DEFAULT_SERVER_CATEGORIES,
    DEFAULT_MANDATORY_SERVERS,
    MANDATORY_SERVER_TYPES,
)

# 모든 게이트를 켠 상태
ALL_ON = {"include_categories": True, "include_mandatory": True}

# 2차에서 제거된 데모 서버 이름 — 어떤 경로로도 다시 생기면 안 된다
REMOVED_DEMO_NAMES = [
    "AI-ab2201", "AI-ab2202", "AI-ab2203",
    "STREAM-ab3301", "STREAM-ab3302",
    "TRANS-ab4401",
    "DBAPI-ab6601",
    "SPKAPI-ab8801",
    "ENCAPI-ab9901",
    "VMS-ab1121",      # 필수 유형의 여분 행이었음
    "BROKER-ab5502",   # 필수 유형의 여분 행이었음
]


def _server_by_name(db, name: str) -> Server | None:
    return db.query(Server).filter(Server.name == name).first()


def _count_by_type(db, category_map: dict, type_server: EnumServerType) -> int:
    return (
        db.query(Server)
        .filter(Server.category_id == category_map[type_server])
        .count()
    )


# ---------------------------------------------------------------------------
# 정의 / 기본값
# ---------------------------------------------------------------------------


def test_should_include_four_mandatory_types_when_defined():
    assert MANDATORY_SERVER_TYPES == {
        EnumServerType.PROXY,
        EnumServerType.VMS,
        EnumServerType.NVR_API,
        EnumServerType.BROKER,
    }


def test_should_define_exactly_one_row_per_mandatory_type():
    """정의는 필수 유형과 1:1 — 데모 정의가 남아 있으면 실패한다."""
    types = [e["type_server"] for e in DEFAULT_MANDATORY_SERVERS]

    assert len(DEFAULT_MANDATORY_SERVERS) == 4
    assert set(types) == MANDATORY_SERVER_TYPES
    assert len(types) == len(set(types)), "유형당 1행이어야 한다(중복 정의 금지)"


def test_should_not_define_any_demo_server():
    """2차에서 제거한 데모 인스턴스가 정의에 되살아나지 않았는지 고정."""
    names = {e["name"] for e in DEFAULT_MANDATORY_SERVERS}

    for removed in REMOVED_DEMO_NAMES:
        assert removed not in names, f"제거된 데모 정의 {removed} 가 되살아났다"


def test_should_expose_two_gates_and_no_demo_gate():
    """게이트 기본값 — 카테고리/필수 2종만 존재하고 DEMO 게이트는 없다."""
    assert settings.INIT_SERVER_CATEGORIES is True
    assert settings.INIT_SERVER_MANDATORY is True
    assert not hasattr(settings, "INIT_SERVER_DEMO"), "INIT_SERVER_DEMO 는 제거된 게이트다"


def test_should_define_all_mandatory_servers_as_normal():
    """시드가 만드는 서버는 절대 ERROR/WARNING 으로 태어나면 안 된다.

    실사고: BROKER-ab5501 이 status=ERROR 리터럴이라 신규 클론이 곧바로
    /servers/summary error=1 (실체 없는 가짜 장애)로 떴다.
    메트릭 미수신을 감지해 status 를 되돌리는 watchdog 이 없으므로 영구히 남는다.
    """
    for entry in DEFAULT_MANDATORY_SERVERS:
        assert entry["status"] == EnumServerStatus.NORMAL, (
            f"{entry['name']} 이 {entry['status']} 로 정의됨"
        )


def test_should_never_hardcode_non_normal_server_status_in_any_seeder():
    """어떤 시더도 서버를 ERROR/WARNING 으로 만들어선 안 된다 (소스 레벨 고정).

    `init_sample_data.py`(INIT_SAMPLE_DATA 경로)에도 BROKER-01=ERROR / AI-02=WARNING
    리터럴이 sync·async 두 벌 있었다. INIT_SAMPLE_DATA=true 인 빈 DB 에서 가짜 장애가
    되살아나므로 2026-08-07 전부 NORMAL 로 정정했다. 재발을 소스에서 막는다.

    ※ SystemEvent 의 severity(EnumSystemEventSeverity.ERROR 등)는 이벤트 '이력' 이라
      server.status 와 무관하므로 이 검사 대상이 아니다.
    """
    import re
    from pathlib import Path

    import app.utils.init_sample_data as sample_mod
    import app.utils.init_server_data as seed_mod

    pattern = re.compile(r"EnumServerStatus\.(ERROR|WARNING)")
    for module in (seed_mod, sample_mod):
        source = Path(module.__file__).read_text(encoding="utf-8")
        # 주석 줄은 제외 — 사유 설명에 단어가 등장할 수 있다
        offenders = [
            line.strip()
            for line in source.splitlines()
            if pattern.search(line) and not line.strip().startswith("#")
        ]
        assert not offenders, (
            f"{Path(module.__file__).name} 에 비-NORMAL 서버 status 리터럴이 있다: {offenders}"
        )


# ---------------------------------------------------------------------------
# 카테고리
# ---------------------------------------------------------------------------


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


def test_should_not_create_categories_when_gate_off(test_db):
    """INIT_SERVER_CATEGORIES=false — 운영자가 지운 카테고리가 부활하지 않는다."""
    category_map = create_server_categories(test_db, create_missing=False)

    assert test_db.query(ServerCategory).count() == 0
    assert category_map == {}


def test_should_map_existing_categories_when_gate_off(test_db):
    """게이트를 꺼도 '이미 있는' 카테고리는 매핑돼야 인스턴스 시드가 계속 붙는다."""
    # Arrange: PROXY 카테고리만 선존재
    test_db.add(ServerCategory(
        name="프록시 서버", type_server=EnumServerType.PROXY, sort_order=10
    ))
    test_db.commit()

    # Act
    category_map = create_server_categories(test_db, create_missing=False)

    # Assert: 신규 생성 0, 기존 1건은 매핑됨
    assert test_db.query(ServerCategory).count() == 1
    assert list(category_map.keys()) == [EnumServerType.PROXY]


# ---------------------------------------------------------------------------
# 인스턴스 — 필수 4종만, 유형당 1개
# ---------------------------------------------------------------------------


def test_should_seed_only_four_mandatory_servers_when_table_empty(test_db):
    initialize_server_data(test_db, **ALL_ON)

    assert test_db.query(ServerCategory).count() == 10
    assert test_db.query(Server).count() == 4
    for name in ("PROXY-ab0001", "VMS-ab1120", "NVRAPI-ab7701", "BROKER-ab5501"):
        assert _server_by_name(test_db, name) is not None


def test_should_not_create_any_demo_server_when_seeded(test_db):
    """빈 DB 최초 시드에도 데모는 하나도 생기지 않는다."""
    initialize_server_data(test_db, **ALL_ON)

    for removed in REMOVED_DEMO_NAMES:
        assert _server_by_name(test_db, removed) is None, f"{removed} 가 생성됨"


@pytest.mark.parametrize("type_server", sorted(MANDATORY_SERVER_TYPES, key=lambda t: t.value))
def test_should_create_exactly_one_per_mandatory_type(test_db, type_server):
    category_map = create_server_categories(test_db)

    ensure_mandatory_servers(test_db, category_map, include_mandatory=True)

    assert _count_by_type(test_db, category_map, type_server) == 1


def test_should_create_no_instances_when_mandatory_gate_off(test_db):
    """INIT_SERVER_MANDATORY=false — 서버 인스턴스가 하나도 만들어지지 않는다."""
    initialize_server_data(test_db, include_categories=True, include_mandatory=False)

    assert test_db.query(ServerCategory).count() == 10
    assert test_db.query(Server).count() == 0


def test_should_create_nothing_when_all_gates_off(test_db):
    initialize_server_data(test_db, include_categories=False, include_mandatory=False)

    assert test_db.query(ServerCategory).count() == 0
    assert test_db.query(Server).count() == 0


def test_should_create_no_servers_when_categories_missing_on_empty_db(test_db):
    """카테고리가 없으면 붙일 곳이 없어 필수 게이트를 켜도 서버 0대."""
    initialize_server_data(test_db, include_categories=False, include_mandatory=True)

    assert test_db.query(ServerCategory).count() == 0
    assert test_db.query(Server).count() == 0


# ---------------------------------------------------------------------------
# 멱등성 / 사용자 데이터 존중
# ---------------------------------------------------------------------------


def test_should_ensure_mandatory_server_when_table_not_empty(test_db):
    # Arrange: 카테고리 생성 후 비필수 유형 서버 1개 선삽입 → '비어있지 않은 DB' 모사
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
    ensure_mandatory_servers(test_db, category_map, include_mandatory=True)

    # Assert: 필수 4종은 테이블이 비어있지 않아도 등록됨 (핵심 버그 수정)
    for name in ("PROXY-ab0001", "VMS-ab1120", "NVRAPI-ab7701", "BROKER-ab5501"):
        assert _server_by_name(test_db, name) is not None
    # 사용자 서버는 보존
    assert _server_by_name(test_db, "EXISTING-1") is not None
    assert test_db.query(Server).count() == 5


def test_should_not_duplicate_when_run_twice(test_db):
    initialize_server_data(test_db, **ALL_ON)
    first = test_db.query(Server).count()

    initialize_server_data(test_db, **ALL_ON)  # 재부팅 모사
    second = test_db.query(Server).count()

    assert first == second == 4
    assert test_db.query(ServerCategory).count() == 10


def test_should_recreate_mandatory_when_deleted(test_db):
    initialize_server_data(test_db, **ALL_ON)
    proxy = _server_by_name(test_db, "PROXY-ab0001")
    assert proxy is not None
    test_db.delete(proxy)
    test_db.commit()
    assert _server_by_name(test_db, "PROXY-ab0001") is None

    # 재부팅 모사 — 필수 유형에 서버가 없으므로 기본 인스턴스 재생성
    initialize_server_data(test_db, **ALL_ON)

    assert _server_by_name(test_db, "PROXY-ab0001") is not None
    assert test_db.query(Server).count() == 4


def test_should_not_recreate_mandatory_when_gate_off_and_deleted(test_db):
    """게이트 off 면 필수 유형이 비어도 부활하지 않는다 (운영자 삭제 의도 존중)."""
    initialize_server_data(test_db, **ALL_ON)
    test_db.delete(_server_by_name(test_db, "PROXY-ab0001"))
    test_db.commit()

    initialize_server_data(test_db, include_categories=True, include_mandatory=False)

    assert _server_by_name(test_db, "PROXY-ab0001") is None
    assert test_db.query(Server).count() == 3


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

    ensure_mandatory_servers(test_db, category_map, include_mandatory=True)

    # 사용자 PROXY 유지 + 기본 placeholder는 생성 안 됨 → PROXY 유형은 1개뿐
    assert _server_by_name(test_db, "PROXY-user-01") is not None
    assert _server_by_name(test_db, "PROXY-ab0001") is None
    assert _count_by_type(test_db, category_map, EnumServerType.PROXY) == 1


def test_should_not_resurrect_deleted_category_when_gate_off(test_db):
    """2026-08-07 VMS 사고 회귀 — 카테고리 삭제 후 재기동해도 부활하지 않는다."""
    initialize_server_data(test_db, **ALL_ON)
    vms_cat = test_db.query(ServerCategory).filter(
        ServerCategory.type_server == EnumServerType.VMS
    ).first()
    test_db.delete(vms_cat)   # cascade 로 VMS 서버도 함께 삭제
    test_db.commit()
    assert test_db.query(ServerCategory).count() == 9

    # 재부팅 모사 — 카테고리 게이트 off
    initialize_server_data(test_db, include_categories=False, include_mandatory=True)

    assert test_db.query(ServerCategory).filter(
        ServerCategory.type_server == EnumServerType.VMS
    ).first() is None
    assert _server_by_name(test_db, "VMS-ab1120") is None
