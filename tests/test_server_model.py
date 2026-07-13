"""
Tests for Server Model
TDD: Test First
"""
import pytest
from datetime import datetime
from sqlalchemy import inspect

from app.models.server import Server, ServerCategory
from app.utils.enums import EnumServerType, EnumServerStatus


class TestServerModel:
    """Tests for Server model"""

    def test_server_model_exists(self):
        """Server 모델이 존재하는지 확인"""
        assert Server is not None

    def test_server_tablename(self):
        """테이블명이 servers인지 확인"""
        assert Server.__tablename__ == "servers"

    def test_server_has_id_column(self):
        """id 컬럼이 존재하는지 확인"""
        mapper = inspect(Server)
        assert "id" in [col.key for col in mapper.columns]

    def test_server_has_category_id_column(self):
        """category_id 컬럼이 존재하는지 확인"""
        mapper = inspect(Server)
        assert "category_id" in [col.key for col in mapper.columns]

    def test_server_has_name_column(self):
        """name 컬럼이 존재하는지 확인"""
        mapper = inspect(Server)
        assert "name" in [col.key for col in mapper.columns]

    def test_server_has_status_column(self):
        """status 컬럼이 존재하는지 확인"""
        mapper = inspect(Server)
        assert "status" in [col.key for col in mapper.columns]

    def test_server_has_ip_address_column(self):
        """ip_address 컬럼이 존재하는지 확인"""
        mapper = inspect(Server)
        assert "ip_address" in [col.key for col in mapper.columns]

    def test_server_has_port_column(self):
        """port 컬럼이 존재하는지 확인"""
        mapper = inspect(Server)
        assert "port" in [col.key for col in mapper.columns]

    def test_server_has_hostname_column(self):
        """hostname 컬럼이 존재하는지 확인"""
        mapper = inspect(Server)
        assert "hostname" in [col.key for col in mapper.columns]

    def test_server_has_cpu_usage_column(self):
        """cpu_usage 컬럼이 존재하는지 확인"""
        mapper = inspect(Server)
        assert "cpu_usage" in [col.key for col in mapper.columns]

    def test_server_has_ram_usage_column(self):
        """ram_usage 컬럼이 존재하는지 확인"""
        mapper = inspect(Server)
        assert "ram_usage" in [col.key for col in mapper.columns]

    def test_server_has_disk_usage_column(self):
        """disk_usage 컬럼이 존재하는지 확인"""
        mapper = inspect(Server)
        assert "disk_usage" in [col.key for col in mapper.columns]

    def test_server_has_network_throughput_column(self):
        """network_throughput 컬럼이 존재하는지 확인"""
        mapper = inspect(Server)
        assert "network_throughput" in [col.key for col in mapper.columns]

    def test_server_has_created_at_column(self):
        """created_at 컬럼이 존재하는지 확인"""
        mapper = inspect(Server)
        assert "created_at" in [col.key for col in mapper.columns]

    def test_server_has_updated_at_column(self):
        """updated_at 컬럼이 존재하는지 확인"""
        mapper = inspect(Server)
        assert "updated_at" in [col.key for col in mapper.columns]

    def test_server_has_category_relationship(self):
        """category 관계가 존재하는지 확인"""
        mapper = inspect(Server)
        assert "category" in [rel.key for rel in mapper.relationships]


class TestServerModelCRUD:
    """Tests for Server CRUD operations"""

    def test_create_server(self, db_session):
        """Server 생성 테스트"""
        # 먼저 카테고리 생성
        category = ServerCategory(
            name="VMS 서버",
            type_server=EnumServerType.VMS,
            sort_order=1
        )
        db_session.add(category)
        db_session.commit()

        # 서버 생성
        server = Server(
            category_id=category.id,
            name="VMS-ab1120",
            status=EnumServerStatus.NORMAL,
            ip_address="192.168.1.10",
            port=8080,
            hostname="vms-server-01",
            cpu_usage=45.0,
            ram_usage=62.0,
            disk_usage=78.0,
            network_throughput="125MB/s"
        )
        db_session.add(server)
        db_session.commit()
        db_session.refresh(server)

        assert server.id is not None
        assert server.category_id == category.id
        assert server.name == "VMS-ab1120"
        assert server.status == EnumServerStatus.NORMAL
        assert server.ip_address == "192.168.1.10"
        assert server.port == 8080
        assert server.hostname == "vms-server-01"
        assert server.cpu_usage == 45.0
        assert server.ram_usage == 62.0
        assert server.disk_usage == 78.0
        assert server.network_throughput == "125MB/s"
        assert server.created_at is not None
        assert server.updated_at is not None

    def test_read_server(self, db_session):
        """Server 조회 테스트"""
        category = ServerCategory(
            name="AI 분석 서버",
            type_server=EnumServerType.AI_ANALYSIS,
            sort_order=2
        )
        db_session.add(category)
        db_session.commit()

        server = Server(
            category_id=category.id,
            name="AI-ab2201",
            status=EnumServerStatus.WARNING,
            ip_address="192.168.1.20",
            port=8081
        )
        db_session.add(server)
        db_session.commit()

        found = db_session.query(Server).filter_by(name="AI-ab2201").first()

        assert found is not None
        assert found.status == EnumServerStatus.WARNING

    def test_update_server_metrics(self, db_session):
        """Server 메트릭 수정 테스트"""
        category = ServerCategory(
            name="스트리밍 서버",
            type_server=EnumServerType.STREAMING,
            sort_order=3
        )
        db_session.add(category)
        db_session.commit()

        server = Server(
            category_id=category.id,
            name="STREAM-ab3301",
            status=EnumServerStatus.NORMAL,
            ip_address="192.168.1.30",
            port=1935,
            cpu_usage=50.0
        )
        db_session.add(server)
        db_session.commit()

        # 메트릭 업데이트
        server.cpu_usage = 85.0
        server.status = EnumServerStatus.WARNING
        db_session.commit()
        db_session.refresh(server)

        assert server.cpu_usage == 85.0
        assert server.status == EnumServerStatus.WARNING

    def test_delete_server(self, db_session):
        """Server 삭제 테스트"""
        category = ServerCategory(
            name="트랜스코더 서버",
            type_server=EnumServerType.TRANSCODER,
            sort_order=4
        )
        db_session.add(category)
        db_session.commit()

        server = Server(
            category_id=category.id,
            name="TRANS-ab4401",
            status=EnumServerStatus.NORMAL,
            ip_address="192.168.1.40",
            port=8082
        )
        db_session.add(server)
        db_session.commit()
        server_id = server.id

        db_session.delete(server)
        db_session.commit()

        found = db_session.query(Server).filter_by(id=server_id).first()
        assert found is None

    def test_server_category_relationship(self, db_session):
        """Server-Category 관계 테스트"""
        category = ServerCategory(
            name="브로커 서버",
            type_server=EnumServerType.BROKER,
            sort_order=5
        )
        db_session.add(category)
        db_session.commit()

        server = Server(
            category_id=category.id,
            name="BROKER-ab5501",
            status=EnumServerStatus.ERROR,
            ip_address="192.168.1.50",
            port=5672
        )
        db_session.add(server)
        db_session.commit()

        # 관계 확인
        assert server.category is not None
        assert server.category.name == "브로커 서버"
        assert server.category.type_server == EnumServerType.BROKER

    def test_category_servers_relationship(self, db_session):
        """Category-Servers 관계 테스트 (1:N)"""
        category = ServerCategory(
            name="DB API 서버",
            type_server=EnumServerType.DB_API,
            sort_order=6
        )
        db_session.add(category)
        db_session.commit()

        server1 = Server(
            category_id=category.id,
            name="DB-ab6601",
            status=EnumServerStatus.NORMAL,
            ip_address="192.168.1.60",
            port=5432
        )
        server2 = Server(
            category_id=category.id,
            name="DB-ab6602",
            status=EnumServerStatus.NORMAL,
            ip_address="192.168.1.61",
            port=5432
        )
        db_session.add_all([server1, server2])
        db_session.commit()

        # 카테고리에서 서버 목록 조회
        db_session.refresh(category)
        assert len(category.servers) == 2
        assert any(s.name == "DB-ab6601" for s in category.servers)
        assert any(s.name == "DB-ab6602" for s in category.servers)

    def test_cascade_delete(self, db_session):
        """카테고리 삭제 시 서버도 함께 삭제되는지 테스트"""
        category = ServerCategory(
            name="NVR API 서버",
            type_server=EnumServerType.NVR_API,
            sort_order=7
        )
        db_session.add(category)
        db_session.commit()

        server = Server(
            category_id=category.id,
            name="NVR-ab7701",
            status=EnumServerStatus.NORMAL,
            ip_address="192.168.1.70",
            port=8083
        )
        db_session.add(server)
        db_session.commit()
        server_id = server.id

        # 카테고리 삭제
        db_session.delete(category)
        db_session.commit()

        # 서버도 함께 삭제되었는지 확인
        found = db_session.query(Server).filter_by(id=server_id).first()
        assert found is None
