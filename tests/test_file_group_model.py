"""
Tests for FileGroup Model
PRD: PRD_Speaker_Device.md - Phase 3: FileGroup Model
TDD: Red -> Green -> Refactor
"""
import pytest
from sqlalchemy import inspect


class TestFileGroupModelBasicStructure:
    """Test FileGroup Model Basic Structure"""

    def test_file_group_model_exists(self):
        """FileGroup model should exist"""
        from app.models.file_group import FileGroup
        assert FileGroup is not None

    def test_file_group_table_name_is_file_groups(self):
        """FileGroup table name should be 'file_groups'"""
        from app.models.file_group import FileGroup
        assert FileGroup.__tablename__ == "file_groups"

    def test_file_group_has_id_field(self):
        """FileGroup should have id field as primary key"""
        from app.models.file_group import FileGroup
        mapper = inspect(FileGroup)
        columns = {c.key: c for c in mapper.columns}
        assert 'id' in columns
        assert columns['id'].primary_key is True

    def test_file_group_has_server_id_fk(self):
        """FileGroup should have server_id field as FK to servers"""
        from app.models.file_group import FileGroup
        mapper = inspect(FileGroup)
        columns = {c.key: c for c in mapper.columns}
        assert 'server_id' in columns
        # Check FK reference
        server_id_col = columns['server_id']
        fks = list(server_id_col.foreign_keys)
        assert len(fks) > 0
        fk_target = str(fks[0].target_fullname)
        assert 'servers.id' in fk_target

    def test_file_group_has_group_id_field(self):
        """FileGroup should have group_id field"""
        from app.models.file_group import FileGroup
        mapper = inspect(FileGroup)
        columns = {c.key: c for c in mapper.columns}
        assert 'group_id' in columns

    def test_file_group_has_group_name_field(self):
        """FileGroup should have group_name field"""
        from app.models.file_group import FileGroup
        mapper = inspect(FileGroup)
        columns = {c.key: c for c in mapper.columns}
        assert 'group_name' in columns

    def test_file_group_has_files_jsonb_field(self):
        """FileGroup should have files field (JSONB)"""
        from app.models.file_group import FileGroup
        mapper = inspect(FileGroup)
        columns = {c.key: c for c in mapper.columns}
        assert 'files' in columns

    def test_file_group_has_timestamps(self):
        """FileGroup should have created_at and updated_at fields"""
        from app.models.file_group import FileGroup
        mapper = inspect(FileGroup)
        columns = {c.key: c for c in mapper.columns}
        assert 'created_at' in columns
        assert 'updated_at' in columns


class TestFileGroupModelConstraints:
    """Test FileGroup Model Constraints"""

    def test_file_group_server_id_group_id_unique_together(self, test_db):
        """FileGroup should have unique constraint on (server_id, group_id)"""
        from app.models.file_group import FileGroup
        from app.models.server import Server, ServerCategory
        from app.utils.enums import EnumServerType, EnumServerStatus
        from sqlalchemy.exc import IntegrityError

        # Create ServerCategory first
        category = ServerCategory(
            name="SPEAKER_API",
            type_server=EnumServerType.SPEAKER_API
        )
        test_db.add(category)
        test_db.commit()
        test_db.refresh(category)

        # Create Server
        server = Server(
            category_id=category.id,
            name="Test Speaker Server",
            status=EnumServerStatus.NORMAL,
            ip_address="192.168.1.100",
            port=8080
        )
        test_db.add(server)
        test_db.commit()
        test_db.refresh(server)

        # Create first FileGroup
        file_group1 = FileGroup(
            server_id=server.id,
            group_id=1,
            group_name="화재경보"
        )
        test_db.add(file_group1)
        test_db.commit()

        # Try to create duplicate FileGroup with same server_id and group_id
        file_group2 = FileGroup(
            server_id=server.id,
            group_id=1,  # Same group_id
            group_name="다른이름"
        )
        test_db.add(file_group2)

        with pytest.raises(IntegrityError):
            test_db.commit()


class TestFileGroupModelFKBehavior:
    """Test FileGroup Model FK Behavior"""

    def test_file_group_cascade_delete_on_server_delete(self, test_db):
        """When Server is deleted, FileGroup should be deleted (CASCADE)"""
        from app.models.file_group import FileGroup
        from app.models.server import Server, ServerCategory
        from app.utils.enums import EnumServerType, EnumServerStatus

        # Create ServerCategory first
        category = ServerCategory(
            name="SPEAKER_API",
            type_server=EnumServerType.SPEAKER_API
        )
        test_db.add(category)
        test_db.commit()
        test_db.refresh(category)

        # Create Server
        server = Server(
            category_id=category.id,
            name="Test Speaker Server",
            status=EnumServerStatus.NORMAL,
            ip_address="192.168.1.100",
            port=8080
        )
        test_db.add(server)
        test_db.commit()
        test_db.refresh(server)

        # Create FileGroup
        file_group = FileGroup(
            server_id=server.id,
            group_id=1,
            group_name="화재경보",
            files=["music01.mp3", "music02.mp3"]
        )
        test_db.add(file_group)
        test_db.commit()
        test_db.refresh(file_group)

        file_group_id = file_group.id
        assert file_group.server_id == server.id

        # Delete Server
        test_db.delete(server)
        test_db.commit()

        # FileGroup should be deleted
        test_db.expire_all()
        deleted_file_group = test_db.query(FileGroup).filter(FileGroup.id == file_group_id).first()
        assert deleted_file_group is None


class TestFileGroupModelRelationship:
    """Test FileGroup Model Relationship"""

    def test_file_group_has_server_relationship(self):
        """FileGroup should have 'server' relationship"""
        from app.models.file_group import FileGroup
        mapper = inspect(FileGroup)
        relationships = {r.key: r for r in mapper.relationships}
        assert 'server' in relationships
