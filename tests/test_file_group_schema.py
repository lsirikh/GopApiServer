"""
Tests for FileGroup Schema
PRD: PRD_Speaker_Device.md - Phase 5: FileGroup Schema
TDD: Red -> Green -> Refactor
"""
import pytest
from pydantic import ValidationError


class TestFileGroupCreateSchema:
    """Test FileGroup Create Schema"""

    def test_file_group_create_schema_exists(self):
        """FileGroupCreate schema should exist"""
        from app.schemas.file_group import FileGroupCreate
        assert FileGroupCreate is not None

    def test_file_group_create_has_server_id_required(self):
        """FileGroupCreate should require server_id"""
        from app.schemas.file_group import FileGroupCreate

        with pytest.raises(ValidationError):
            FileGroupCreate(group_id=1, group_name="화재경보")  # Missing server_id

    def test_file_group_create_has_group_id_required(self):
        """FileGroupCreate should require group_id"""
        from app.schemas.file_group import FileGroupCreate

        with pytest.raises(ValidationError):
            FileGroupCreate(server_id=1, group_name="화재경보")  # Missing group_id

    def test_file_group_create_has_group_name_required(self):
        """FileGroupCreate should require group_name"""
        from app.schemas.file_group import FileGroupCreate

        with pytest.raises(ValidationError):
            FileGroupCreate(server_id=1, group_id=1)  # Missing group_name

    def test_file_group_create_has_files_optional(self):
        """FileGroupCreate files should be optional"""
        from app.schemas.file_group import FileGroupCreate

        schema = FileGroupCreate(server_id=1, group_id=1, group_name="화재경보")
        assert schema.files is None


class TestFileGroupUpdateSchema:
    """Test FileGroup Update Schema"""

    def test_file_group_update_schema_exists(self):
        """FileGroupUpdate schema should exist"""
        from app.schemas.file_group import FileGroupUpdate
        assert FileGroupUpdate is not None

    def test_file_group_update_all_fields_optional(self):
        """FileGroupUpdate should have all fields optional"""
        from app.schemas.file_group import FileGroupUpdate

        # Should not raise error with no fields
        schema = FileGroupUpdate()
        assert schema.group_name is None
        assert schema.files is None


class TestFileGroupResponseSchema:
    """Test FileGroup Response Schema"""

    def test_file_group_response_schema_exists(self):
        """FileGroupResponse schema should exist"""
        from app.schemas.file_group import FileGroupResponse
        assert FileGroupResponse is not None

    def test_file_group_response_has_all_fields(self):
        """FileGroupResponse should have all required fields"""
        from app.schemas.file_group import FileGroupResponse

        fields = FileGroupResponse.model_fields.keys()
        assert 'id' in fields
        assert 'server_id' in fields
        assert 'group_id' in fields
        assert 'group_name' in fields
        assert 'files' in fields

    def test_file_group_response_has_timestamps(self):
        """FileGroupResponse should have created_at and updated_at"""
        from app.schemas.file_group import FileGroupResponse

        fields = FileGroupResponse.model_fields.keys()
        assert 'created_at' in fields
        assert 'updated_at' in fields
