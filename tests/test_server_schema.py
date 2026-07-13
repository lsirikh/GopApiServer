"""
Tests for Server Schemas
TDD: Test First
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas.server import (
    ServerCategoryCreate,
    ServerCategoryUpdate,
    ServerCategoryResponse,
    ServerCreate,
    ServerUpdate,
    ServerResponse,
    ServerCategorySummary,
    ServerCategoryWithServers
)
from app.utils.enums import EnumServerType, EnumServerStatus


class TestServerCategorySchemas:
    """Tests for ServerCategory schemas"""

    def test_server_category_create_schema(self):
        """ServerCategoryCreate 스키마 테스트"""
        data = {
            "name": "VMS 서버",
            "type_server": "VMS",
            "description": "Video Management System",
            "sort_order": 1
        }
        schema = ServerCategoryCreate(**data)
        assert schema.name == "VMS 서버"
        assert schema.type_server == EnumServerType.VMS
        assert schema.description == "Video Management System"
        assert schema.sort_order == 1

    def test_server_category_create_minimal(self):
        """ServerCategoryCreate 최소 필드 테스트"""
        data = {
            "name": "AI 분석 서버",
            "type_server": "AI_ANALYSIS"
        }
        schema = ServerCategoryCreate(**data)
        assert schema.name == "AI 분석 서버"
        assert schema.type_server == EnumServerType.AI_ANALYSIS
        assert schema.description is None
        assert schema.sort_order == 0  # default

    def test_server_category_create_validation_error(self):
        """ServerCategoryCreate 유효성 검사 오류 테스트"""
        with pytest.raises(ValidationError):
            ServerCategoryCreate(name="", type_server="VMS")  # empty name

    def test_server_category_update_schema(self):
        """ServerCategoryUpdate 스키마 테스트"""
        data = {
            "name": "VMS 서버 (수정)",
            "description": "수정된 설명"
        }
        schema = ServerCategoryUpdate(**data)
        assert schema.name == "VMS 서버 (수정)"
        assert schema.description == "수정된 설명"

    def test_server_category_update_partial(self):
        """ServerCategoryUpdate 부분 업데이트 테스트"""
        data = {"description": "설명만 수정"}
        schema = ServerCategoryUpdate(**data)
        assert schema.name is None
        assert schema.description == "설명만 수정"

    def test_server_category_response_schema(self):
        """ServerCategoryResponse 스키마 테스트"""
        now = datetime.now()
        data = {
            "id": 1,
            "name": "VMS 서버",
            "type_server": "VMS",
            "description": "Video Management System",
            "sort_order": 1,
            "created_at": now,
            "updated_at": now
        }
        schema = ServerCategoryResponse(**data)
        assert schema.id == 1
        assert schema.name == "VMS 서버"
        assert schema.type_server == "VMS"


class TestServerSchemas:
    """Tests for Server schemas"""

    def test_server_create_schema(self):
        """ServerCreate 스키마 테스트"""
        data = {
            "category_id": 1,
            "name": "VMS-ab1120",
            "status": "NORMAL",
            "ip_address": "192.168.1.10",
            "port": 8080,
            "hostname": "vms-server-01",
            "cpu_usage": 45.0,
            "ram_usage": 62.0,
            "disk_usage": 78.0,
            "network_throughput": "125MB/s"
        }
        schema = ServerCreate(**data)
        assert schema.name == "VMS-ab1120"
        assert schema.status == EnumServerStatus.NORMAL
        assert schema.ip_address == "192.168.1.10"
        assert schema.port == 8080
        assert schema.cpu_usage == 45.0

    def test_server_create_minimal(self):
        """ServerCreate 최소 필드 테스트"""
        data = {
            "category_id": 1,
            "name": "AI-ab2201",
            "ip_address": "192.168.1.20",
            "port": 8081
        }
        schema = ServerCreate(**data)
        assert schema.name == "AI-ab2201"
        assert schema.status == EnumServerStatus.NORMAL  # default
        assert schema.hostname is None
        assert schema.cpu_usage is None

    def test_server_create_validation_error(self):
        """ServerCreate 유효성 검사 오류 테스트"""
        with pytest.raises(ValidationError):
            ServerCreate(
                category_id=1,
                name="",  # empty name
                ip_address="192.168.1.10",
                port=8080
            )

    def test_server_update_schema(self):
        """ServerUpdate 스키마 테스트"""
        data = {
            "status": "WARNING",
            "cpu_usage": 85.0,
            "ram_usage": 78.0
        }
        schema = ServerUpdate(**data)
        assert schema.status == EnumServerStatus.WARNING
        assert schema.cpu_usage == 85.0
        assert schema.ram_usage == 78.0

    def test_server_update_partial(self):
        """ServerUpdate 부분 업데이트 테스트"""
        data = {"cpu_usage": 95.0}
        schema = ServerUpdate(**data)
        assert schema.cpu_usage == 95.0
        assert schema.status is None
        assert schema.name is None

    def test_server_response_schema(self):
        """ServerResponse 스키마 테스트"""
        now = datetime.now()
        data = {
            "id": 1,
            "category_id": 1,
            "name": "VMS-ab1120",
            "status": "NORMAL",
            "ip_address": "192.168.1.10",
            "port": 8080,
            "hostname": "vms-server-01",
            "cpu_usage": 45.0,
            "ram_usage": 62.0,
            "disk_usage": 78.0,
            "network_throughput": "125MB/s",
            "created_at": now,
            "updated_at": now
        }
        schema = ServerResponse(**data)
        assert schema.id == 1
        assert schema.name == "VMS-ab1120"
        assert schema.status == "NORMAL"


class TestServerSummarySchemas:
    """Tests for Server Summary schemas"""

    def test_server_category_with_servers_schema(self):
        """ServerCategoryWithServers 스키마 테스트"""
        now = datetime.now()
        data = {
            "id": 1,
            "name": "VMS 서버",
            "type_server": "VMS",
            "description": "Video Management System",
            "sort_order": 1,
            "created_at": now,
            "updated_at": now,
            "servers": [
                {
                    "id": 1,
                    "category_id": 1,
                    "name": "VMS-ab1120",
                    "status": "NORMAL",
                    "ip_address": "192.168.1.10",
                    "port": 8080,
                    "hostname": "vms-server-01",
                    "cpu_usage": 45.0,
                    "ram_usage": 62.0,
                    "disk_usage": 78.0,
                    "network_throughput": "125MB/s",
                    "created_at": now,
                    "updated_at": now
                }
            ]
        }
        schema = ServerCategoryWithServers(**data)
        assert len(schema.servers) == 1
        assert schema.servers[0].name == "VMS-ab1120"

    def test_server_category_summary_schema(self):
        """ServerCategorySummary 스키마 테스트"""
        now = datetime.now()
        data = {
            "id": 1,
            "name": "VMS 서버",
            "type_server": "VMS",
            "total": 2,
            "normal": 2,
            "warning": 0,
            "error": 0,
            "servers": [
                {
                    "id": 1,
                    "category_id": 1,
                    "name": "VMS-ab1120",
                    "status": "NORMAL",
                    "ip_address": "192.168.1.10",
                    "port": 8080,
                    "hostname": None,
                    "cpu_usage": 45.0,
                    "ram_usage": 62.0,
                    "disk_usage": 78.0,
                    "network_throughput": "125MB/s",
                    "created_at": now,
                    "updated_at": now
                }
            ]
        }
        schema = ServerCategorySummary(**data)
        assert schema.total == 2
        assert schema.normal == 2
        assert schema.warning == 0
        assert schema.error == 0
