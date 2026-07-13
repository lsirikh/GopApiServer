"""
Tests for ServerCategory Model
TDD: Test First
"""
import pytest
from datetime import datetime
from sqlalchemy import inspect

from app.models.server import ServerCategory
from app.utils.enums import EnumServerType


class TestServerCategoryModel:
    """Tests for ServerCategory model"""

    def test_server_category_model_exists(self):
        """ServerCategory 모델이 존재하는지 확인"""
        assert ServerCategory is not None

    def test_server_category_tablename(self):
        """테이블명이 server_categories인지 확인"""
        assert ServerCategory.__tablename__ == "server_categories"

    def test_server_category_has_id_column(self):
        """id 컬럼이 존재하는지 확인"""
        mapper = inspect(ServerCategory)
        assert "id" in [col.key for col in mapper.columns]

    def test_server_category_has_name_column(self):
        """name 컬럼이 존재하는지 확인"""
        mapper = inspect(ServerCategory)
        assert "name" in [col.key for col in mapper.columns]

    def test_server_category_has_type_server_column(self):
        """type_server 컬럼이 존재하는지 확인"""
        mapper = inspect(ServerCategory)
        assert "type_server" in [col.key for col in mapper.columns]

    def test_server_category_has_description_column(self):
        """description 컬럼이 존재하는지 확인"""
        mapper = inspect(ServerCategory)
        assert "description" in [col.key for col in mapper.columns]

    def test_server_category_has_sort_order_column(self):
        """sort_order 컬럼이 존재하는지 확인"""
        mapper = inspect(ServerCategory)
        assert "sort_order" in [col.key for col in mapper.columns]

    def test_server_category_has_created_at_column(self):
        """created_at 컬럼이 존재하는지 확인"""
        mapper = inspect(ServerCategory)
        assert "created_at" in [col.key for col in mapper.columns]

    def test_server_category_has_updated_at_column(self):
        """updated_at 컬럼이 존재하는지 확인"""
        mapper = inspect(ServerCategory)
        assert "updated_at" in [col.key for col in mapper.columns]

    def test_server_category_has_servers_relationship(self):
        """servers 관계가 존재하는지 확인"""
        mapper = inspect(ServerCategory)
        assert "servers" in [rel.key for rel in mapper.relationships]


class TestServerCategoryModelCRUD:
    """Tests for ServerCategory CRUD operations"""

    def test_create_server_category(self, db_session):
        """ServerCategory 생성 테스트"""
        category = ServerCategory(
            name="VMS 서버",
            type_server=EnumServerType.VMS,
            description="Video Management System",
            sort_order=1
        )
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)

        assert category.id is not None
        assert category.name == "VMS 서버"
        assert category.type_server == EnumServerType.VMS
        assert category.description == "Video Management System"
        assert category.sort_order == 1
        assert category.created_at is not None
        assert category.updated_at is not None

    def test_read_server_category(self, db_session):
        """ServerCategory 조회 테스트"""
        category = ServerCategory(
            name="AI 분석 서버",
            type_server=EnumServerType.AI_ANALYSIS,
            sort_order=2
        )
        db_session.add(category)
        db_session.commit()

        found = db_session.query(ServerCategory).filter_by(
            type_server=EnumServerType.AI_ANALYSIS
        ).first()

        assert found is not None
        assert found.name == "AI 분석 서버"

    def test_update_server_category(self, db_session):
        """ServerCategory 수정 테스트"""
        category = ServerCategory(
            name="스트리밍 서버",
            type_server=EnumServerType.STREAMING,
            sort_order=3
        )
        db_session.add(category)
        db_session.commit()

        category.description = "실시간 스트리밍 서버"
        db_session.commit()
        db_session.refresh(category)

        assert category.description == "실시간 스트리밍 서버"

    def test_delete_server_category(self, db_session):
        """ServerCategory 삭제 테스트"""
        category = ServerCategory(
            name="트랜스코더 서버",
            type_server=EnumServerType.TRANSCODER,
            sort_order=4
        )
        db_session.add(category)
        db_session.commit()
        category_id = category.id

        db_session.delete(category)
        db_session.commit()

        found = db_session.query(ServerCategory).filter_by(id=category_id).first()
        assert found is None

    def test_type_server_unique_constraint(self, db_session):
        """type_server UNIQUE 제약조건 테스트"""
        category1 = ServerCategory(
            name="브로커 서버 1",
            type_server=EnumServerType.BROKER,
            sort_order=5
        )
        db_session.add(category1)
        db_session.commit()

        category2 = ServerCategory(
            name="브로커 서버 2",
            type_server=EnumServerType.BROKER,  # 동일한 type_server
            sort_order=6
        )
        db_session.add(category2)

        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()
