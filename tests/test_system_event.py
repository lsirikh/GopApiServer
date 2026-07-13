"""
System Event TDD Tests
Based on PRD_System_Event.md v1.2
"""
import pytest
from sqlalchemy import inspect, create_engine
from sqlalchemy.orm import Session, sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base
from app.dependencies import get_db


# ==============================================================================
# Phase SE-1: Server Schema Refactoring
# ==============================================================================

class TestServerSchemaRefactoring:
    """Server 모델 리팩토링 테스트 - threshold_config 추가, 리소스 필드 제거"""

    # --------------------------------------------------------------------------
    # SE-1.1: Model Tests
    # --------------------------------------------------------------------------

    def test_server_model_has_threshold_config(self):
        """Server 모델에 threshold_config 필드가 존재해야 함"""
        from app.models.server import Server

        mapper = inspect(Server)
        column_names = [col.key for col in mapper.columns]

        assert "threshold_config" in column_names, \
            "Server 모델에 threshold_config 필드가 없습니다"

    def test_server_model_no_cpu_usage(self):
        """Server 모델에 cpu_usage 필드가 없어야 함 (server_metrics로 이동)"""
        from app.models.server import Server

        mapper = inspect(Server)
        column_names = [col.key for col in mapper.columns]

        assert "cpu_usage" not in column_names, \
            "Server 모델에 cpu_usage 필드가 존재합니다 (server_metrics로 이동해야 함)"

    def test_server_model_no_ram_usage(self):
        """Server 모델에 ram_usage 필드가 없어야 함 (server_metrics로 이동)"""
        from app.models.server import Server

        mapper = inspect(Server)
        column_names = [col.key for col in mapper.columns]

        assert "ram_usage" not in column_names, \
            "Server 모델에 ram_usage 필드가 존재합니다 (server_metrics로 이동해야 함)"

    def test_server_model_no_disk_usage(self):
        """Server 모델에 disk_usage 필드가 없어야 함 (server_metrics로 이동)"""
        from app.models.server import Server

        mapper = inspect(Server)
        column_names = [col.key for col in mapper.columns]

        assert "disk_usage" not in column_names, \
            "Server 모델에 disk_usage 필드가 존재합니다 (server_metrics로 이동해야 함)"

    def test_server_model_no_network_throughput(self):
        """Server 모델에 network_throughput 필드가 없어야 함 (server_metrics로 이동)"""
        from app.models.server import Server

        mapper = inspect(Server)
        column_names = [col.key for col in mapper.columns]

        assert "network_throughput" not in column_names, \
            "Server 모델에 network_throughput 필드가 존재합니다 (server_metrics로 이동해야 함)"

    # --------------------------------------------------------------------------
    # SE-1.3: Schema Tests
    # --------------------------------------------------------------------------

    def test_server_create_has_threshold_config(self):
        """ServerCreate 스키마에 threshold_config 필드가 존재해야 함"""
        from app.schemas.server import ServerCreate

        fields = ServerCreate.model_fields
        assert "threshold_config" in fields, \
            "ServerCreate 스키마에 threshold_config 필드가 없습니다"

    def test_server_response_has_threshold_config(self):
        """ServerResponse 스키마에 threshold_config 필드가 존재해야 함"""
        from app.schemas.server import ServerResponse

        fields = ServerResponse.model_fields
        assert "threshold_config" in fields, \
            "ServerResponse 스키마에 threshold_config 필드가 없습니다"

    def test_server_response_no_resource_fields(self):
        """ServerResponse에 리소스 필드(cpu_usage, ram_usage, disk_usage, network_throughput)가 없어야 함"""
        from app.schemas.server import ServerResponse

        fields = ServerResponse.model_fields
        resource_fields = ["cpu_usage", "ram_usage", "disk_usage", "network_throughput"]

        for field in resource_fields:
            assert field not in fields, \
                f"ServerResponse에 {field} 필드가 존재합니다 (server_metrics로 이동해야 함)"

    # --------------------------------------------------------------------------
    # SE-1.5: ThresholdConfig Schema Tests
    # --------------------------------------------------------------------------

    def test_threshold_config_schema_structure(self):
        """ThresholdConfig 스키마 구조 검증 - Dict[str, Any] 타입"""
        from app.schemas.server import ServerCreate

        # threshold_config 필드가 Optional[Dict[str, Any]] 타입인지 확인
        field_info = ServerCreate.model_fields.get("threshold_config")
        assert field_info is not None, "threshold_config 필드가 없습니다"

        # threshold_config로 유효한 JSON 구조 생성 가능한지 테스트
        threshold_data = {
            "cpu": {"warning": 70, "critical": 90},
            "ram": {"warning": 70, "critical": 90},
            "disk": {"warning": 80, "critical": 95},
            "network": {"warning": None, "critical": None}
        }
        server = ServerCreate(
            category_id=1,
            name="Test Server",
            ip_address="192.168.1.1",
            port=8080,
            threshold_config=threshold_data
        )
        assert server.threshold_config == threshold_data, \
            "threshold_config 데이터가 올바르게 설정되지 않았습니다"

    def test_threshold_config_accepts_partial_config(self):
        """ThresholdConfig - 부분 설정도 허용해야 함"""
        from app.schemas.server import ServerCreate

        # 일부 리소스만 설정
        partial_config = {
            "cpu": {"warning": 80, "critical": 95}
        }
        server = ServerCreate(
            category_id=1,
            name="Test Server",
            ip_address="192.168.1.1",
            port=8080,
            threshold_config=partial_config
        )
        assert server.threshold_config == partial_config

    def test_threshold_config_defaults_to_none(self):
        """ThresholdConfig - 미설정 시 None이어야 함"""
        from app.schemas.server import ServerCreate

        server = ServerCreate(
            category_id=1,
            name="Test Server",
            ip_address="192.168.1.1",
            port=8080
        )
        assert server.threshold_config is None, \
            "threshold_config 기본값이 None이 아닙니다"


# ==============================================================================
# Phase SE-2: Server Metrics Model
# ==============================================================================

class TestServerMetricsModel:
    """ServerMetrics 모델 테스트"""

    def test_server_metrics_model_exists(self):
        """ServerMetrics 모델 클래스가 존재해야 함"""
        from app.models.server import ServerMetrics

        assert ServerMetrics is not None, "ServerMetrics 모델이 존재하지 않습니다"

    def test_server_metrics_has_server_fk(self):
        """ServerMetrics 모델에 server_id FK 필드가 존재해야 함"""
        from app.models.server import ServerMetrics

        mapper = inspect(ServerMetrics)
        column_names = [col.key for col in mapper.columns]

        assert "server_id" in column_names, \
            "ServerMetrics 모델에 server_id FK 필드가 없습니다"

    def test_server_metrics_has_resource_fields(self):
        """ServerMetrics 모델에 리소스 필드들이 존재해야 함"""
        from app.models.server import ServerMetrics

        mapper = inspect(ServerMetrics)
        column_names = [col.key for col in mapper.columns]

        required_fields = [
            "cpu_usage",
            "ram_usage",
            "ram_total_gb",
            "ram_used_gb",
            "disk_usage",
            "disk_total_gb",
            "disk_used_gb",
            "network_in_mbps",
            "network_out_mbps",
            "process_count"
        ]

        for field in required_fields:
            assert field in column_names, \
                f"ServerMetrics 모델에 {field} 필드가 없습니다"

    def test_server_metrics_has_detail_jsonb(self):
        """ServerMetrics 모델에 detail JSONB 필드가 존재해야 함"""
        from app.models.server import ServerMetrics

        mapper = inspect(ServerMetrics)
        column_names = [col.key for col in mapper.columns]

        assert "detail" in column_names, \
            "ServerMetrics 모델에 detail JSONB 필드가 없습니다"

    def test_server_metrics_has_timestamps(self):
        """ServerMetrics 모델에 collected_at, created_at 필드가 존재해야 함"""
        from app.models.server import ServerMetrics

        mapper = inspect(ServerMetrics)
        column_names = [col.key for col in mapper.columns]

        assert "collected_at" in column_names, \
            "ServerMetrics 모델에 collected_at 필드가 없습니다"
        assert "created_at" in column_names, \
            "ServerMetrics 모델에 created_at 필드가 없습니다"


# ==============================================================================
# Phase SE-3: Server Metrics Schema
# ==============================================================================

class TestServerMetricsSchema:
    """ServerMetrics Pydantic 스키마 테스트"""

    def test_server_metrics_create_schema(self):
        """ServerMetricsCreate 스키마 구조 검증"""
        from app.schemas.server import ServerMetricsCreate

        fields = ServerMetricsCreate.model_fields
        required_fields = [
            "cpu_usage",
            "ram_usage",
            "ram_total_gb",
            "ram_used_gb",
            "disk_usage",
            "disk_total_gb",
            "disk_used_gb"
        ]

        for field in required_fields:
            assert field in fields, \
                f"ServerMetricsCreate에 {field} 필드가 없습니다"

    def test_server_metrics_response_schema(self):
        """ServerMetricsResponse 스키마 구조 검증"""
        from app.schemas.server import ServerMetricsResponse

        fields = ServerMetricsResponse.model_fields
        required_fields = [
            "id",
            "server_id",
            "cpu_usage",
            "ram_usage",
            "disk_usage",
            "created_at"
        ]

        for field in required_fields:
            assert field in fields, \
                f"ServerMetricsResponse에 {field} 필드가 없습니다"

    def test_server_metrics_create_optional_fields(self):
        """ServerMetricsCreate - Optional 필드 검증"""
        from app.schemas.server import ServerMetricsCreate
        from datetime import datetime

        # 최소 필수 필드만 설정
        metrics = ServerMetricsCreate(
            cpu_usage=50.0,
            ram_usage=60.0,
            disk_usage=70.0
        )

        assert metrics.cpu_usage == 50.0
        assert metrics.ram_usage == 60.0
        assert metrics.disk_usage == 70.0
        assert metrics.network_in_mbps is None  # Optional
        assert metrics.network_out_mbps is None  # Optional


# ==============================================================================
# Phase SE-4: Server Metrics API
# ==============================================================================

# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_system_event.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def test_client():
    """테스트용 FastAPI 클라이언트"""
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)

    import os
    if os.path.exists("./test_system_event.db"):
        try:
            os.remove("./test_system_event.db")
        except:
            pass


@pytest.fixture(scope="module")
def test_db():
    """테스트용 DB 세션"""
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=test_engine)


class TestServerMetricsApi:
    """Server Metrics API 테스트"""

    @pytest.fixture(autouse=True)
    def setup(self, test_client, test_db):
        """각 테스트 전 기본 데이터 생성"""
        self.client = test_client
        self.db = test_db

        # 서버 카테고리 생성
        from app.models.server import ServerCategory, Server
        from app.utils.enums import EnumServerType, EnumServerStatus

        # 기존 데이터 확인
        category = self.db.query(ServerCategory).filter(
            ServerCategory.type_server == EnumServerType.VMS
        ).first()

        if not category:
            category = ServerCategory(
                name="VMS 서버",
                type_server=EnumServerType.VMS,
                sort_order=1
            )
            self.db.add(category)
            self.db.commit()
            self.db.refresh(category)

        self.category_id = category.id

        # 서버 생성
        server = self.db.query(Server).filter(
            Server.name == "Test VMS Server"
        ).first()

        if not server:
            server = Server(
                category_id=self.category_id,
                name="Test VMS Server",
                status=EnumServerStatus.NORMAL,
                ip_address="192.168.1.100",
                port=8080,
                threshold_config={
                    "cpu": {"warning": 70, "critical": 90},
                    "ram": {"warning": 70, "critical": 90},
                    "disk": {"warning": 80, "critical": 95}
                }
            )
            self.db.add(server)
            self.db.commit()
            self.db.refresh(server)

        self.server_id = server.id

    def test_post_server_metrics_success(self):
        """POST /api/servers/{id}/metrics 201 성공"""
        metrics_data = {
            "cpu_usage": 45.5,
            "ram_usage": 60.0,
            "ram_total_gb": 32.0,
            "ram_used_gb": 19.2,
            "disk_usage": 55.0,
            "disk_total_gb": 500.0,
            "disk_used_gb": 275.0,
            "network_in_mbps": 100.5,
            "network_out_mbps": 50.3,
            "process_count": 150
        }

        response = self.client.post(
            f"/api/servers/{self.server_id}/metrics",
            json=metrics_data
        )

        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["success"] is True
        assert data["data"]["server_id"] == self.server_id
        assert data["data"]["cpu_usage"] == 45.5

    def test_post_server_metrics_server_not_found(self):
        """존재하지 않는 서버에 메트릭 전송 시 404"""
        metrics_data = {"cpu_usage": 45.5, "ram_usage": 60.0, "disk_usage": 55.0}

        response = self.client.post(
            "/api/servers/99999/metrics",
            json=metrics_data
        )

        assert response.status_code == 404

    def test_post_server_metrics_returns_full_data(self):
        """POST 응답에 전체 데이터가 포함되어야 함"""
        metrics_data = {
            "cpu_usage": 50.0,
            "ram_usage": 65.0,
            "ram_total_gb": 32.0,
            "ram_used_gb": 20.8,
            "disk_usage": 60.0,
            "disk_total_gb": 500.0,
            "disk_used_gb": 300.0,
            "network_in_mbps": 80.0,
            "network_out_mbps": 40.0,
            "process_count": 120,
            "detail": {"top_process": "nginx"}
        }

        response = self.client.post(
            f"/api/servers/{self.server_id}/metrics",
            json=metrics_data
        )

        assert response.status_code == 201
        data = response.json()["data"]

        # 모든 필드가 응답에 포함되어야 함
        assert data["cpu_usage"] == 50.0
        assert data["ram_usage"] == 65.0
        assert data["ram_total_gb"] == 32.0
        assert data["ram_used_gb"] == 20.8
        assert data["disk_usage"] == 60.0
        assert data["disk_total_gb"] == 500.0
        assert data["disk_used_gb"] == 300.0
        assert data["network_in_mbps"] == 80.0
        assert data["network_out_mbps"] == 40.0
        assert data["process_count"] == 120
        assert data["detail"] == {"top_process": "nginx"}
        assert "id" in data
        assert "server_id" in data
        assert "created_at" in data

    def test_post_server_metrics_threshold_exceeded(self):
        """임계치 초과 시 threshold_exceeded 반환"""
        # 서버의 threshold_config: cpu warning=70, critical=90
        metrics_data = {
            "cpu_usage": 95.0,  # critical 초과
            "ram_usage": 75.0,  # warning 초과
            "disk_usage": 50.0  # 정상
        }

        response = self.client.post(
            f"/api/servers/{self.server_id}/metrics",
            json=metrics_data
        )

        assert response.status_code == 201
        data = response.json()["data"]

        # threshold_exceeded 응답 확인
        assert "threshold_exceeded" in data
        threshold = data["threshold_exceeded"]
        assert threshold is not None

        # CPU critical 초과
        assert "cpu" in threshold
        assert threshold["cpu"]["level"] == "critical"
        assert threshold["cpu"]["value"] == 95.0

        # RAM warning 초과
        assert "ram" in threshold
        assert threshold["ram"]["level"] == "warning"

        # Disk는 정상이므로 포함 안 됨
        assert "disk" not in threshold

    def test_get_server_metrics_list(self):
        """GET /api/servers/{id}/metrics 200 성공"""
        # 먼저 여러 메트릭 저장
        for i in range(3):
            self.client.post(
                f"/api/servers/{self.server_id}/metrics",
                json={"cpu_usage": 30.0 + i * 10, "ram_usage": 40.0, "disk_usage": 50.0}
            )

        response = self.client.get(f"/api/servers/{self.server_id}/metrics")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 3

    def test_get_server_metrics_with_limit(self):
        """GET /api/servers/{id}/metrics - limit 파라미터 동작"""
        response = self.client.get(f"/api/servers/{self.server_id}/metrics?limit=2")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) <= 2

    def test_get_server_metrics_latest(self):
        """GET /api/servers/{id}/metrics/latest 200 성공"""
        # 최신 메트릭 저장
        self.client.post(
            f"/api/servers/{self.server_id}/metrics",
            json={"cpu_usage": 88.8, "ram_usage": 66.6, "disk_usage": 44.4}
        )

        response = self.client.get(f"/api/servers/{self.server_id}/metrics/latest")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["server_id"] == self.server_id
        assert data["data"]["server_name"] == "Test VMS Server"
        assert "latest_metrics" in data["data"]

    def test_delete_server_metrics_old(self):
        """DELETE /api/servers/{id}/metrics 200 성공"""
        response = self.client.delete(
            f"/api/servers/{self.server_id}/metrics?older_than_days=30"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "deleted_count" in data["data"]


# ==============================================================================
# Phase SE-5: System Event Enum
# ==============================================================================

class TestSystemEventEnum:
    """System Event Enum 테스트"""

    def test_enum_system_event_type_exists(self):
        """EnumSystemEventType Enum 존재 확인"""
        from app.utils.enums import EnumSystemEventType

        assert EnumSystemEventType is not None

    def test_enum_system_event_type_values(self):
        """EnumSystemEventType 15개 이벤트 유형 값 검증 (PRD_SystemEvent_Sync.md v1.2)"""
        from app.utils.enums import EnumSystemEventType

        expected_values = [
            "RESOURCE_THRESHOLD",
            "SERVER_CONNECTED",
            "SERVER_DISCONNECTED",
            "SERVER_ERROR",
            "SERVICE_STARTED",
            "SERVICE_STOPPED",
            "SERVICE_ERROR",
            "CONNECTION_LOST",
            "CONNECTION_RESTORED",
            "SECURITY_ALERT",
            "DEVICE_CONNECTED",
            "BACKUP_STARTED",
            "BACKUP_COMPLETED",
            "BACKUP_FAILED",
            "SYSTEM_UPDATE"
        ]

        for value in expected_values:
            assert hasattr(EnumSystemEventType, value), f"EnumSystemEventType에 {value} 값이 없습니다"

        # 정확히 15개 값만 존재
        assert len(EnumSystemEventType) == 15, f"Expected 15 types, got {len(EnumSystemEventType)}"

    def test_enum_system_event_severity_exists(self):
        """EnumSystemEventSeverity Enum 존재 확인"""
        from app.utils.enums import EnumSystemEventSeverity

        assert EnumSystemEventSeverity is not None

    def test_enum_system_event_severity_values(self):
        """EnumSystemEventSeverity INFO, WARNING, ERROR, CRITICAL 값 검증"""
        from app.utils.enums import EnumSystemEventSeverity

        expected_values = ["INFO", "WARNING", "ERROR", "CRITICAL"]

        for value in expected_values:
            assert hasattr(EnumSystemEventSeverity, value), f"EnumSystemEventSeverity에 {value} 값이 없습니다"

        # 정확히 4개 값만 존재
        assert len(EnumSystemEventSeverity) == 4


# ==============================================================================
# Phase SE-6: System Event Model
# ==============================================================================

class TestSystemEventModel:
    """SystemEvent 모델 테스트"""

    def test_system_event_model_exists(self):
        """SystemEvent 모델 클래스가 존재해야 함"""
        from app.models.system_event import SystemEvent

        assert SystemEvent is not None, "SystemEvent 모델이 존재하지 않습니다"

    def test_system_event_has_server_fk(self):
        """SystemEvent 모델에 server_id FK 필드가 존재해야 함 (SET NULL)"""
        from app.models.system_event import SystemEvent
        from sqlalchemy import inspect

        mapper = inspect(SystemEvent)
        column_names = [col.key for col in mapper.columns]

        assert "server_id" in column_names, \
            "SystemEvent 모델에 server_id FK 필드가 없습니다"

    def test_system_event_has_type_event(self):
        """SystemEvent 모델에 type_event Enum 필드가 존재해야 함"""
        from app.models.system_event import SystemEvent
        from sqlalchemy import inspect

        mapper = inspect(SystemEvent)
        column_names = [col.key for col in mapper.columns]

        assert "type_event" in column_names, \
            "SystemEvent 모델에 type_event 필드가 없습니다"

    def test_system_event_has_severity(self):
        """SystemEvent 모델에 severity Enum 필드가 존재해야 함"""
        from app.models.system_event import SystemEvent
        from sqlalchemy import inspect

        mapper = inspect(SystemEvent)
        column_names = [col.key for col in mapper.columns]

        assert "severity" in column_names, \
            "SystemEvent 모델에 severity 필드가 없습니다"

    def test_system_event_has_content_fields(self):
        """SystemEvent 모델에 title, message, detail 필드가 존재해야 함"""
        from app.models.system_event import SystemEvent
        from sqlalchemy import inspect

        mapper = inspect(SystemEvent)
        column_names = [col.key for col in mapper.columns]

        assert "title" in column_names, "SystemEvent 모델에 title 필드가 없습니다"
        assert "message" in column_names, "SystemEvent 모델에 message 필드가 없습니다"
        assert "detail" in column_names, "SystemEvent 모델에 detail 필드가 없습니다"

    def test_system_event_has_acknowledge_fields(self):
        """SystemEvent 모델에 is_acknowledged, acknowledged_by, acknowledged_at 필드가 존재해야 함"""
        from app.models.system_event import SystemEvent
        from sqlalchemy import inspect

        mapper = inspect(SystemEvent)
        column_names = [col.key for col in mapper.columns]

        assert "is_acknowledged" in column_names, \
            "SystemEvent 모델에 is_acknowledged 필드가 없습니다"
        assert "acknowledged_by" in column_names, \
            "SystemEvent 모델에 acknowledged_by 필드가 없습니다"
        assert "acknowledged_at" in column_names, \
            "SystemEvent 모델에 acknowledged_at 필드가 없습니다"


# ==============================================================================
# Phase SE-7: System Event Schema
# ==============================================================================

class TestSystemEventSchema:
    """SystemEvent Pydantic 스키마 테스트"""

    def test_system_event_create_schema(self):
        """SystemEventCreate 스키마 구조 검증"""
        from app.schemas.system_event import SystemEventCreate
        from app.utils.enums import EnumSystemEventType, EnumSystemEventSeverity

        fields = SystemEventCreate.model_fields
        required_fields = ["type_event", "severity", "title"]

        for field in required_fields:
            assert field in fields, \
                f"SystemEventCreate에 {field} 필드가 없습니다"

        # 선택 필드 확인
        optional_fields = ["server_id", "server_description", "message", "detail"]
        for field in optional_fields:
            assert field in fields, \
                f"SystemEventCreate에 {field} 필드가 없습니다"

        # 스키마 인스턴스 생성 테스트
        event = SystemEventCreate(
            type_event=EnumSystemEventType.RESOURCE_THRESHOLD,
            severity=EnumSystemEventSeverity.WARNING,
            title="CPU 사용률 임계치 초과",
            message="CPU 사용률이 90%를 초과했습니다",
            server_id=1
        )
        assert event.type_event == EnumSystemEventType.RESOURCE_THRESHOLD
        assert event.severity == EnumSystemEventSeverity.WARNING
        assert event.title == "CPU 사용률 임계치 초과"

    def test_system_event_update_schema(self):
        """SystemEventUpdate 스키마 구조 검증"""
        from app.schemas.system_event import SystemEventUpdate

        fields = SystemEventUpdate.model_fields

        # 모든 필드가 Optional이어야 함
        expected_fields = ["severity", "title", "message", "detail"]
        for field in expected_fields:
            assert field in fields, \
                f"SystemEventUpdate에 {field} 필드가 없습니다"

        # 빈 업데이트 가능해야 함
        update = SystemEventUpdate()
        assert update is not None

    def test_system_event_response_schema(self):
        """SystemEventResponse 스키마 구조 검증"""
        from app.schemas.system_event import SystemEventResponse

        fields = SystemEventResponse.model_fields
        required_fields = [
            "id",
            "type_event",
            "severity",
            "title",
            "is_acknowledged",
            "created_at"
        ]

        for field in required_fields:
            assert field in fields, \
                f"SystemEventResponse에 {field} 필드가 없습니다"

        # 선택 필드
        optional_fields = [
            "server_id",
            "server_description",
            "message",
            "detail",
            "acknowledged_by",
            "acknowledged_at"
        ]
        for field in optional_fields:
            assert field in fields, \
                f"SystemEventResponse에 {field} 필드가 없습니다"

    def test_system_event_acknowledge_schema(self):
        """SystemEventAcknowledge 스키마 구조 검증"""
        from app.schemas.system_event import SystemEventAcknowledge

        fields = SystemEventAcknowledge.model_fields

        assert "acknowledged_by" in fields, \
            "SystemEventAcknowledge에 acknowledged_by 필드가 없습니다"

        # 스키마 인스턴스 생성 테스트
        ack = SystemEventAcknowledge(acknowledged_by="admin")
        assert ack.acknowledged_by == "admin"


# ==============================================================================
# Phase SE-8: System Event API (Basic CRUD)
# ==============================================================================

class TestSystemEventApiCrud:
    """System Event API CRUD 테스트"""

    @pytest.fixture(autouse=True)
    def setup(self, test_client, test_db):
        """각 테스트 전 기본 데이터 생성"""
        self.client = test_client
        self.db = test_db

        # 서버 카테고리 및 서버 생성
        from app.models.server import ServerCategory, Server
        from app.utils.enums import EnumServerType, EnumServerStatus

        category = self.db.query(ServerCategory).filter(
            ServerCategory.type_server == EnumServerType.VMS
        ).first()

        if not category:
            category = ServerCategory(
                name="VMS 서버",
                type_server=EnumServerType.VMS,
                sort_order=1
            )
            self.db.add(category)
            self.db.commit()
            self.db.refresh(category)

        self.category_id = category.id

        server = self.db.query(Server).filter(
            Server.name == "Test VMS Server"
        ).first()

        if not server:
            server = Server(
                category_id=self.category_id,
                name="Test VMS Server",
                status=EnumServerStatus.NORMAL,
                ip_address="192.168.1.100",
                port=8080
            )
            self.db.add(server)
            self.db.commit()
            self.db.refresh(server)

        self.server_id = server.id

    # --------------------------------------------------------------------------
    # SE-8.3: POST API Tests
    # --------------------------------------------------------------------------

    def test_create_system_event_success(self):
        """POST /api/system-events 201 성공"""
        event_data = {
            "type_event": "RESOURCE_THRESHOLD",
            "severity": "WARNING",
            "title": "CPU 사용률 임계치 초과",
            "message": "CPU 사용률이 85%를 초과했습니다",
            "server_id": self.server_id
        }

        response = self.client.post("/api/system-events", json=event_data)

        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["success"] is True
        assert data["data"]["title"] == "CPU 사용률 임계치 초과"
        assert data["data"]["type_event"] == "RESOURCE_THRESHOLD"
        assert data["data"]["severity"] == "WARNING"
        assert data["data"]["is_acknowledged"] is False

    def test_create_system_event_without_server(self):
        """서버 없이 전역 이벤트 생성"""
        event_data = {
            "type_event": "SYSTEM_UPDATE",
            "severity": "INFO",
            "title": "시스템 업데이트 완료"
        }

        response = self.client.post("/api/system-events", json=event_data)

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["server_id"] is None
        assert data["title"] == "시스템 업데이트 완료"

    def test_create_system_event_invalid_server(self):
        """존재하지 않는 server_id로 생성 시 400"""
        event_data = {
            "type_event": "SERVER_ERROR",
            "severity": "ERROR",
            "title": "서버 오류",
            "server_id": 99999
        }

        response = self.client.post("/api/system-events", json=event_data)

        assert response.status_code == 400 or response.status_code == 404

    # --------------------------------------------------------------------------
    # SE-8.1: GET List API Tests
    # --------------------------------------------------------------------------

    def test_get_system_events_list(self):
        """GET /api/system-events 200 성공"""
        # 먼저 이벤트 생성
        self.client.post("/api/system-events", json={
            "type_event": "SERVER_CONNECTED",
            "severity": "INFO",
            "title": "서버 연결됨"
        })

        response = self.client.get("/api/system-events")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_get_system_events_with_pagination(self):
        """GET /api/system-events?page=1&limit=5 페이지네이션"""
        response = self.client.get("/api/system-events?page=1&limit=5")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) <= 5

    def test_get_system_events_filter_by_severity(self):
        """GET /api/system-events?severity=WARNING 심각도 필터"""
        # WARNING 이벤트 생성
        self.client.post("/api/system-events", json={
            "type_event": "RESOURCE_THRESHOLD",
            "severity": "WARNING",
            "title": "경고 이벤트"
        })

        response = self.client.get("/api/system-events?severity=WARNING")

        assert response.status_code == 200
        data = response.json()
        # 모든 결과가 WARNING이어야 함
        for event in data["data"]:
            assert event["severity"] == "WARNING"

    def test_get_system_events_filter_by_type(self):
        """GET /api/system-events?type_event=RESOURCE_THRESHOLD 유형 필터"""
        response = self.client.get("/api/system-events?type_event=RESOURCE_THRESHOLD")

        assert response.status_code == 200
        data = response.json()
        for event in data["data"]:
            assert event["type_event"] == "RESOURCE_THRESHOLD"

    # --------------------------------------------------------------------------
    # SE-8.2: GET Single API Tests
    # --------------------------------------------------------------------------

    def test_get_system_event_by_id(self):
        """GET /api/system-events/{id} 200 성공"""
        # 먼저 이벤트 생성
        create_response = self.client.post("/api/system-events", json={
            "type_event": "SERVER_CONNECTED",
            "severity": "INFO",
            "title": "서버 연결됨"
        })
        event_id = create_response.json()["data"]["id"]

        response = self.client.get(f"/api/system-events/{event_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == event_id
        assert data["data"]["title"] == "서버 연결됨"

    def test_get_system_event_not_found(self):
        """GET /api/system-events/{id} 존재하지 않는 ID 404"""
        response = self.client.get("/api/system-events/99999")

        assert response.status_code == 404

    # --------------------------------------------------------------------------
    # SE-8.4: PATCH API Tests
    # --------------------------------------------------------------------------

    def test_update_system_event_success(self):
        """PATCH /api/system-events/{id} 200 성공"""
        # 먼저 이벤트 생성
        create_response = self.client.post("/api/system-events", json={
            "type_event": "SERVER_ERROR",
            "severity": "ERROR",
            "title": "서버 오류 발생"
        })
        event_id = create_response.json()["data"]["id"]

        # 업데이트
        update_data = {"severity": "CRITICAL", "message": "심각한 오류로 업그레이드됨"}
        response = self.client.patch(f"/api/system-events/{event_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["severity"] == "CRITICAL"
        assert data["data"]["message"] == "심각한 오류로 업그레이드됨"

    def test_update_system_event_not_found(self):
        """PATCH /api/system-events/{id} 존재하지 않는 ID 404"""
        response = self.client.patch("/api/system-events/99999", json={"title": "Updated"})

        assert response.status_code == 404

    # --------------------------------------------------------------------------
    # SE-8.5: DELETE API Tests
    # --------------------------------------------------------------------------

    def test_delete_system_event_success(self):
        """DELETE /api/system-events/{id} 200 성공"""
        # 먼저 이벤트 생성
        create_response = self.client.post("/api/system-events", json={
            "type_event": "CONNECTION_LOST",
            "severity": "WARNING",
            "title": "연결 끊김"
        })
        event_id = create_response.json()["data"]["id"]

        response = self.client.delete(f"/api/system-events/{event_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] is None

        # 삭제 확인
        get_response = self.client.get(f"/api/system-events/{event_id}")
        assert get_response.status_code == 404

    def test_delete_system_event_not_found(self):
        """DELETE /api/system-events/{id} 존재하지 않는 ID 404"""
        response = self.client.delete("/api/system-events/99999")

        assert response.status_code == 404


# ==============================================================================
# Phase SE-9: System Event API (Advanced)
# ==============================================================================

class TestSystemEventApiAdvanced:
    """System Event API Advanced 테스트 - Acknowledge, Summary, Server-specific"""

    @pytest.fixture(autouse=True)
    def setup(self, test_client, test_db):
        """각 테스트 전 기본 데이터 생성"""
        self.client = test_client
        self.db = test_db

        # 서버 카테고리 및 서버 생성
        from app.models.server import ServerCategory, Server
        from app.utils.enums import EnumServerType, EnumServerStatus

        category = self.db.query(ServerCategory).filter(
            ServerCategory.type_server == EnumServerType.VMS
        ).first()

        if not category:
            category = ServerCategory(
                name="VMS 서버",
                type_server=EnumServerType.VMS,
                sort_order=1
            )
            self.db.add(category)
            self.db.commit()
            self.db.refresh(category)

        self.category_id = category.id

        server = self.db.query(Server).filter(
            Server.name == "Test VMS Server"
        ).first()

        if not server:
            server = Server(
                category_id=self.category_id,
                name="Test VMS Server",
                status=EnumServerStatus.NORMAL,
                ip_address="192.168.1.100",
                port=8080
            )
            self.db.add(server)
            self.db.commit()
            self.db.refresh(server)

        self.server_id = server.id

    # --------------------------------------------------------------------------
    # SE-9.1: Acknowledge API Tests
    # --------------------------------------------------------------------------

    def test_acknowledge_system_event_success(self):
        """POST /api/system-events/{id}/acknowledge 200 성공"""
        # 먼저 이벤트 생성
        create_response = self.client.post("/api/system-events", json={
            "type_event": "SERVER_ERROR",
            "severity": "ERROR",
            "title": "서버 오류 발생",
            "server_id": self.server_id
        })
        event_id = create_response.json()["data"]["id"]

        # Acknowledge
        response = self.client.post(
            f"/api/system-events/{event_id}/acknowledge",
            json={"acknowledged_by": "admin"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["is_acknowledged"] is True
        assert data["data"]["acknowledged_by"] == "admin"
        assert data["data"]["acknowledged_at"] is not None

    def test_acknowledge_system_event_not_found(self):
        """POST /api/system-events/{id}/acknowledge 존재하지 않는 ID 404"""
        response = self.client.post(
            "/api/system-events/99999/acknowledge",
            json={"acknowledged_by": "admin"}
        )

        assert response.status_code == 404

    def test_acknowledge_already_acknowledged(self):
        """이미 확인된 이벤트 재확인 시도"""
        # 먼저 이벤트 생성 및 확인
        create_response = self.client.post("/api/system-events", json={
            "type_event": "SERVICE_STOPPED",
            "severity": "WARNING",
            "title": "서비스 중지됨"
        })
        event_id = create_response.json()["data"]["id"]

        # 첫 번째 확인
        self.client.post(
            f"/api/system-events/{event_id}/acknowledge",
            json={"acknowledged_by": "admin1"}
        )

        # 두 번째 확인 시도
        response = self.client.post(
            f"/api/system-events/{event_id}/acknowledge",
            json={"acknowledged_by": "admin2"}
        )

        # 이미 확인된 경우 400 반환 또는 그냥 성공
        assert response.status_code in [200, 400]

    # --------------------------------------------------------------------------
    # SE-9.2: Summary API Tests
    # --------------------------------------------------------------------------

    def test_get_system_events_summary(self):
        """GET /api/system-events/summary 200 성공"""
        # 다양한 유형의 이벤트 생성
        self.client.post("/api/system-events", json={
            "type_event": "RESOURCE_THRESHOLD",
            "severity": "WARNING",
            "title": "Warning 1"
        })
        self.client.post("/api/system-events", json={
            "type_event": "SERVER_ERROR",
            "severity": "ERROR",
            "title": "Error 1"
        })
        self.client.post("/api/system-events", json={
            "type_event": "SERVER_DISCONNECTED",
            "severity": "CRITICAL",
            "title": "Critical 1"
        })

        response = self.client.get("/api/system-events/summary")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "total_count" in data["data"]
        assert "unacknowledged_count" in data["data"]
        assert "by_severity" in data["data"]
        assert "by_type" in data["data"]

    def test_summary_by_severity_count(self):
        """심각도별 카운트 확인"""
        response = self.client.get("/api/system-events/summary")

        assert response.status_code == 200
        data = response.json()["data"]
        assert isinstance(data["by_severity"], dict)

    def test_summary_unacknowledged_count(self):
        """미확인 이벤트 카운트 확인"""
        # 이벤트 생성
        create_response = self.client.post("/api/system-events", json={
            "type_event": "BACKUP_FAILED",
            "severity": "ERROR",
            "title": "백업 실패"
        })
        event_id = create_response.json()["data"]["id"]

        # 미확인 카운트 확인
        response = self.client.get("/api/system-events/summary")
        data = response.json()["data"]
        initial_unack = data["unacknowledged_count"]

        # 확인 처리
        self.client.post(
            f"/api/system-events/{event_id}/acknowledge",
            json={"acknowledged_by": "admin"}
        )

        # 미확인 카운트가 감소했는지 확인
        response2 = self.client.get("/api/system-events/summary")
        data2 = response2.json()["data"]
        assert data2["unacknowledged_count"] < initial_unack

    # --------------------------------------------------------------------------
    # SE-9.3: Server-specific API Tests
    # --------------------------------------------------------------------------

    def test_get_server_system_events(self):
        """GET /api/servers/{id}/system-events 200 성공"""
        # 서버에 연결된 이벤트 생성
        self.client.post("/api/system-events", json={
            "type_event": "SERVER_CONNECTED",
            "severity": "INFO",
            "title": "서버 연결됨",
            "server_id": self.server_id
        })

        response = self.client.get(f"/api/servers/{self.server_id}/system-events")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        # 모든 이벤트가 해당 서버의 것이어야 함
        for event in data["data"]:
            assert event["server_id"] == self.server_id

    def test_get_server_system_events_empty(self):
        """이벤트 없는 서버 - 빈 배열 반환"""
        # 다른 서버 생성
        from app.models.server import Server
        from app.utils.enums import EnumServerStatus

        new_server = Server(
            category_id=self.category_id,
            name="Empty Server",
            status=EnumServerStatus.NORMAL,
            ip_address="192.168.1.200",
            port=9090
        )
        self.db.add(new_server)
        self.db.commit()
        self.db.refresh(new_server)

        response = self.client.get(f"/api/servers/{new_server.id}/system-events")

        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []


# ==============================================================================
# Phase SE-10: Metrics → Events Integration Tests
# ==============================================================================

class TestMetricsEventIntegration:
    """SE-10: 메트릭 임계치 초과 시 system_events 자동 생성 테스트"""

    @pytest.fixture(autouse=True)
    def setup(self, test_client, test_db):
        """각 테스트 전 기본 데이터 생성"""
        self.client = test_client
        self.db = test_db

        # 서버 카테고리 및 서버 생성
        from app.models.server import ServerCategory, Server
        from app.utils.enums import EnumServerType, EnumServerStatus

        category = self.db.query(ServerCategory).filter(
            ServerCategory.type_server == EnumServerType.VMS
        ).first()

        if not category:
            category = ServerCategory(
                name="VMS 서버",
                type_server=EnumServerType.VMS,
                sort_order=1
            )
            self.db.add(category)
            self.db.commit()
            self.db.refresh(category)

        self.category_id = category.id

        server = self.db.query(Server).filter(
            Server.name == "Test VMS Server"
        ).first()

        if not server:
            server = Server(
                category_id=category.id,
                name="Test VMS Server",
                status=EnumServerStatus.NORMAL,
                ip_address="192.168.1.100",
                port=8080
            )
            self.db.add(server)
            self.db.commit()
            self.db.refresh(server)

        self.server_id = server.id

        # 서버에 threshold_config 설정
        server.threshold_config = {
            "cpu": {"warning": 70, "critical": 90},
            "ram": {"warning": 80, "critical": 95},
            "disk": {"warning": 85, "critical": 95}
        }
        self.db.commit()

    # --------------------------------------------------------------------------
    # SE-10.1: Integration Tests
    # --------------------------------------------------------------------------

    def test_metrics_threshold_creates_event(self):
        """임계치 초과 시 system_event 자동 생성"""
        # CPU 90% 초과 메트릭 전송 (critical)
        response = self.client.post(f"/api/servers/{self.server_id}/metrics", json={
            "cpu_usage": 95.0,
            "ram_usage": 50.0,
            "disk_usage": 40.0
        })
        assert response.status_code == 201

        # system_events에서 RESOURCE_THRESHOLD 이벤트 확인
        events_response = self.client.get(
            f"/api/system-events?server_id={self.server_id}&type_event=RESOURCE_THRESHOLD"
        )
        assert events_response.status_code == 200
        events = events_response.json()["data"]
        assert len(events) >= 1  # 최소 1개 이벤트 생성

    def test_metrics_no_event_below_threshold(self):
        """정상 범위 메트릭 시 이벤트 미생성"""
        # 먼저 기존 이벤트 수 확인
        initial_response = self.client.get(
            f"/api/system-events?server_id={self.server_id}&type_event=RESOURCE_THRESHOLD"
        )
        initial_count = len(initial_response.json()["data"])

        # 정상 범위 메트릭 전송
        response = self.client.post(f"/api/servers/{self.server_id}/metrics", json={
            "cpu_usage": 30.0,
            "ram_usage": 40.0,
            "disk_usage": 50.0
        })
        assert response.status_code == 201

        # 이벤트 수 확인 - 증가하지 않아야 함
        after_response = self.client.get(
            f"/api/system-events?server_id={self.server_id}&type_event=RESOURCE_THRESHOLD"
        )
        after_count = len(after_response.json()["data"])
        assert after_count == initial_count

    def test_metrics_event_type_resource_threshold(self):
        """생성된 이벤트의 type_event가 RESOURCE_THRESHOLD"""
        # 임계치 초과 메트릭 전송
        self.client.post(f"/api/servers/{self.server_id}/metrics", json={
            "cpu_usage": 92.0,
            "ram_usage": 50.0
        })

        # 이벤트 확인
        events_response = self.client.get(
            f"/api/system-events?server_id={self.server_id}"
        )
        events = events_response.json()["data"]

        # RESOURCE_THRESHOLD 타입 이벤트 존재
        resource_events = [e for e in events if e["type_event"] == "RESOURCE_THRESHOLD"]
        assert len(resource_events) >= 1

    def test_metrics_event_severity_warning(self):
        """warning 임계치 초과 시 WARNING severity"""
        # CPU 75% (warning 70 초과, critical 90 미만)
        self.client.post(f"/api/servers/{self.server_id}/metrics", json={
            "cpu_usage": 75.0,
            "ram_usage": 50.0,
            "disk_usage": 50.0
        })

        # 이벤트 확인
        events_response = self.client.get(
            f"/api/system-events?server_id={self.server_id}&type_event=RESOURCE_THRESHOLD"
        )
        events = events_response.json()["data"]

        # WARNING severity 이벤트 존재
        warning_events = [e for e in events if e["severity"] == "WARNING"]
        assert len(warning_events) >= 1

    def test_metrics_event_severity_critical(self):
        """critical 임계치 초과 시 CRITICAL severity"""
        # CPU 95% (critical 90 초과)
        self.client.post(f"/api/servers/{self.server_id}/metrics", json={
            "cpu_usage": 95.0,
            "ram_usage": 50.0,
            "disk_usage": 50.0
        })

        # 이벤트 확인
        events_response = self.client.get(
            f"/api/system-events?server_id={self.server_id}&type_event=RESOURCE_THRESHOLD"
        )
        events = events_response.json()["data"]

        # CRITICAL severity 이벤트 존재
        critical_events = [e for e in events if e["severity"] == "CRITICAL"]
        assert len(critical_events) >= 1


# ==============================================================================
# Phase SE-11: Response Format Validation (meta attribute)
# ==============================================================================

class TestResponseFormatValidation:
    """응답 형식 검증 - GOP_Restful_Api_연동설계.md 표준 준수"""

    @pytest.fixture(autouse=True)
    def setup(self, test_client, test_db):
        """각 테스트 전 기본 데이터 생성"""
        self.client = test_client
        self.db = test_db

    def test_system_events_list_has_meta(self):
        """GET /api/system-events 응답에 meta 속성 포함"""
        response = self.client.get("/api/system-events")

        assert response.status_code == 200
        data = response.json()
        assert "meta" in data, "응답에 meta 속성이 없습니다 (GOP 표준 위반)"
        assert "timestamp" in data["meta"], "meta에 timestamp 속성이 없습니다"

    def test_system_events_detail_has_meta(self):
        """GET /api/system-events/{id} 응답에 meta 속성 포함"""
        # 이벤트 생성
        create_response = self.client.post("/api/system-events", json={
            "type_event": "SERVER_CONNECTED",
            "severity": "INFO",
            "title": "테스트 이벤트"
        })
        event_id = create_response.json()["data"]["id"]

        # 단건 조회
        response = self.client.get(f"/api/system-events/{event_id}")

        assert response.status_code == 200
        data = response.json()
        assert "meta" in data, "응답에 meta 속성이 없습니다 (GOP 표준 위반)"
        assert "timestamp" in data["meta"], "meta에 timestamp 속성이 없습니다"

    def test_system_events_create_has_meta(self):
        """POST /api/system-events 응답에 meta 속성 포함"""
        response = self.client.post("/api/system-events", json={
            "type_event": "SERVER_CONNECTED",
            "severity": "INFO",
            "title": "테스트 이벤트"
        })

        assert response.status_code == 201
        data = response.json()
        assert "meta" in data, "응답에 meta 속성이 없습니다 (GOP 표준 위반)"
        assert "timestamp" in data["meta"], "meta에 timestamp 속성이 없습니다"

    def test_system_events_summary_has_meta(self):
        """GET /api/system-events/summary 응답에 meta 속성 포함"""
        response = self.client.get("/api/system-events/summary")

        assert response.status_code == 200
        data = response.json()
        assert "meta" in data, "응답에 meta 속성이 없습니다 (GOP 표준 위반)"
        assert "timestamp" in data["meta"], "meta에 timestamp 속성이 없습니다"

    def test_server_system_events_has_meta(self):
        """GET /api/servers/{id}/system-events 응답에 meta 속성 포함"""
        # 서버 생성
        from app.models.server import ServerCategory, Server
        from app.utils.enums import EnumServerType, EnumServerStatus

        category = self.db.query(ServerCategory).filter(
            ServerCategory.type_server == EnumServerType.VMS
        ).first()

        if not category:
            category = ServerCategory(
                name="VMS 서버",
                type_server=EnumServerType.VMS,
                sort_order=1
            )
            self.db.add(category)
            self.db.commit()
            self.db.refresh(category)

        server = Server(
            category_id=category.id,
            name="Meta Test Server",
            status=EnumServerStatus.NORMAL,
            ip_address="192.168.1.200",
            port=8080
        )
        self.db.add(server)
        self.db.commit()
        self.db.refresh(server)

        response = self.client.get(f"/api/servers/{server.id}/system-events")

        assert response.status_code == 200
        data = response.json()
        assert "meta" in data, "응답에 meta 속성이 없습니다 (GOP 표준 위반)"
        assert "timestamp" in data["meta"], "meta에 timestamp 속성이 없습니다"


# ==============================================================================
# Phase SE-SYNC: EnumSystemEventType 동기화 테스트
# PRD: PRD_SystemEvent_Sync.md v1.2
# ==============================================================================

class TestEnumSystemEventTypeSync:
    """
    SE-SYNC: EnumSystemEventType 문서-코드 동기화 검증

    목표: 24개 → 15개 타입으로 축소
    - USER_* 9개 제거 (UserLoginLog 사용)
    - ConfigChangeLog 중복 4개 제거
    - 신규 4개 추가 (CONNECTION_LOST, CONNECTION_RESTORED, SECURITY_ALERT, DEVICE_CONNECTED)
    """

    # --------------------------------------------------------------------------
    # SE-SYNC-1.1: 타입 수 검증 테스트
    # --------------------------------------------------------------------------

    def test_enum_has_15_types(self):
        """SE-SYNC-1.1: EnumSystemEventType이 정확히 15개 타입을 가짐"""
        from app.utils.enums import EnumSystemEventType

        assert len(EnumSystemEventType) == 15, \
            f"EnumSystemEventType은 15개 타입이어야 합니다. 현재: {len(EnumSystemEventType)}개"

    # --------------------------------------------------------------------------
    # SE-SYNC-1.2: 제거된 타입 검증 테스트
    # --------------------------------------------------------------------------

    def test_enum_no_user_types(self):
        """SE-SYNC-1.2: USER_* 9개 타입이 없음 (UserLoginLog로 분리)"""
        from app.utils.enums import EnumSystemEventType

        user_types = [
            'USER_LOGIN', 'USER_LOGOUT', 'USER_LOGIN_FAILED',
            'USER_LOCKED', 'USER_UNLOCKED', 'USER_CREATED',
            'USER_UPDATED', 'USER_DELETED', 'SESSION_FORCED_LOGOUT'
        ]

        for user_type in user_types:
            assert not hasattr(EnumSystemEventType, user_type), \
                f"{user_type}은 EnumSystemEventType에 없어야 합니다 (UserLoginLog 사용)"

    def test_enum_no_configchangelog_overlap_types(self):
        """SE-SYNC-1.2: ConfigChangeLog 중복 타입이 없음"""
        from app.utils.enums import EnumSystemEventType

        # ConfigChangeLog로 이동된 타입들
        overlap_types = [
            'CONFIG_CHANGED', 'DEVICE_ADDED', 'DEVICE_REMOVED', 'DEVICE_STATUS_CHANGED'
        ]

        for overlap_type in overlap_types:
            assert not hasattr(EnumSystemEventType, overlap_type), \
                f"{overlap_type}은 ConfigChangeLog에서 관리해야 합니다"

    # --------------------------------------------------------------------------
    # SE-SYNC-1.3: 필수 타입 존재 테스트
    # --------------------------------------------------------------------------

    def test_enum_has_required_server_types(self):
        """SE-SYNC-1.3: 서버 관련 필수 타입 존재 (5종)"""
        from app.utils.enums import EnumSystemEventType

        required_types = [
            'SERVER_CONNECTED', 'SERVER_DISCONNECTED', 'SERVER_ERROR',
            'CONNECTION_LOST', 'CONNECTION_RESTORED'
        ]

        for type_name in required_types:
            assert hasattr(EnumSystemEventType, type_name), \
                f"{type_name}이 EnumSystemEventType에 존재해야 합니다"

    def test_enum_has_required_service_types(self):
        """SE-SYNC-1.3: 서비스 관련 필수 타입 존재 (3종)"""
        from app.utils.enums import EnumSystemEventType

        required_types = [
            'SERVICE_STARTED', 'SERVICE_STOPPED', 'SERVICE_ERROR'
        ]

        for type_name in required_types:
            assert hasattr(EnumSystemEventType, type_name), \
                f"{type_name}이 EnumSystemEventType에 존재해야 합니다"

    def test_enum_has_required_backup_types(self):
        """SE-SYNC-1.3: 백업 관련 필수 타입 존재 (3종)"""
        from app.utils.enums import EnumSystemEventType

        required_types = [
            'BACKUP_STARTED', 'BACKUP_COMPLETED', 'BACKUP_FAILED'
        ]

        for type_name in required_types:
            assert hasattr(EnumSystemEventType, type_name), \
                f"{type_name}이 EnumSystemEventType에 존재해야 합니다"

    def test_enum_has_resource_threshold_type(self):
        """SE-SYNC-1.3: 리소스 모니터링 타입 존재 (1종)"""
        from app.utils.enums import EnumSystemEventType

        assert hasattr(EnumSystemEventType, 'RESOURCE_THRESHOLD'), \
            "RESOURCE_THRESHOLD가 EnumSystemEventType에 존재해야 합니다"

    def test_enum_has_security_and_update_types(self):
        """SE-SYNC-1.3: 보안/업데이트 타입 존재 (2종)"""
        from app.utils.enums import EnumSystemEventType

        required_types = ['SECURITY_ALERT', 'SYSTEM_UPDATE']

        for type_name in required_types:
            assert hasattr(EnumSystemEventType, type_name), \
                f"{type_name}이 EnumSystemEventType에 존재해야 합니다"

    def test_enum_has_device_connected_type(self):
        """SE-SYNC-1.3: 디바이스 자동 감지 타입 존재 (1종)"""
        from app.utils.enums import EnumSystemEventType

        # 물리적 연결 자동 감지만 SystemEvent에 포함
        assert hasattr(EnumSystemEventType, 'DEVICE_CONNECTED'), \
            "DEVICE_CONNECTED가 EnumSystemEventType에 존재해야 합니다"

    def test_enum_uses_upper_snake_case(self):
        """SE-SYNC-1.3: 모든 타입이 UPPER_SNAKE_CASE 사용"""
        from app.utils.enums import EnumSystemEventType

        for member in EnumSystemEventType:
            # 이름과 값이 모두 대문자여야 함
            assert member.value == member.value.upper(), \
                f"{member.name}의 값 '{member.value}'이 UPPER_SNAKE_CASE가 아닙니다"
            assert member.name == member.value, \
                f"{member.name}의 name과 value가 일치해야 합니다"

    def test_enum_final_15_types_list(self):
        """SE-SYNC-1.3: 최종 15개 타입 목록 검증"""
        from app.utils.enums import EnumSystemEventType

        expected_types = [
            # 리소스 (1종)
            'RESOURCE_THRESHOLD',
            # 서버 (5종)
            'SERVER_CONNECTED', 'SERVER_DISCONNECTED', 'SERVER_ERROR',
            'CONNECTION_LOST', 'CONNECTION_RESTORED',
            # 서비스 (3종)
            'SERVICE_STARTED', 'SERVICE_STOPPED', 'SERVICE_ERROR',
            # 백업 (3종)
            'BACKUP_STARTED', 'BACKUP_COMPLETED', 'BACKUP_FAILED',
            # 보안/업데이트 (2종)
            'SECURITY_ALERT', 'SYSTEM_UPDATE',
            # 디바이스 (1종)
            'DEVICE_CONNECTED'
        ]

        # 모든 예상 타입이 존재하는지 확인
        for expected in expected_types:
            assert hasattr(EnumSystemEventType, expected), \
                f"{expected}가 EnumSystemEventType에 존재해야 합니다"

        # 예상 타입만 존재하는지 확인 (정확히 15개)
        actual_types = [member.name for member in EnumSystemEventType]
        assert len(actual_types) == 15, \
            f"정확히 15개 타입이어야 합니다. 현재: {len(actual_types)}개"
