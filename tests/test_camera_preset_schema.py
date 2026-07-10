"""
Tests for CameraPreset, ROI, XyPoint schemas
TDD Phase 1.2: Schema Tests
"""
import pytest
from pydantic import ValidationError


class TestCameraPresetSchema:
    """Phase 1.2: CameraPreset Schema Tests"""

    def test_camera_preset_create_schema_validates_required_fields(self):
        """Test: CameraPresetCreate schema validates required fields (preset_index, preset_name)"""
        from app.schemas.camera_preset import CameraPresetCreate

        # Valid data
        valid_data = {"preset_index": 1, "preset_name": "Home Position"}
        schema = CameraPresetCreate(**valid_data)
        assert schema.preset_index == 1
        assert schema.preset_name == "Home Position"

        # Missing preset_index
        with pytest.raises(ValidationError):
            CameraPresetCreate(preset_name="Home Position")

        # Missing preset_name
        with pytest.raises(ValidationError):
            CameraPresetCreate(preset_index=1)

    def test_camera_preset_create_schema_has_default_touring_time(self):
        """Test: CameraPresetCreate schema has default touring_time=10"""
        from app.schemas.camera_preset import CameraPresetCreate

        # Create without touring_time
        schema = CameraPresetCreate(preset_index=1, preset_name="Home Position")
        assert schema.touring_time == 10

        # Create with custom touring_time
        schema = CameraPresetCreate(preset_index=1, preset_name="Home Position", touring_time=20)
        assert schema.touring_time == 20

    def test_camera_preset_response_schema_includes_roi_count(self):
        """Test: CameraPresetResponse schema includes roi_count"""
        from app.schemas.camera_preset import CameraPresetResponse
        from datetime import datetime

        data = {
            "id": 1,
            "camera_id": 101,
            "camera_name": "Test Camera",
            "preset_index": 1,
            "preset_name": "Home Position",
            "touring_time": 10,
            "roi_count": 3,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        schema = CameraPresetResponse(**data)
        assert schema.roi_count == 3

    def test_camera_preset_detail_response_schema_includes_rois_list(self):
        """Test: CameraPresetDetailResponse schema includes rois list"""
        from app.schemas.camera_preset import CameraPresetDetailResponse, ROIDetailResponse
        from datetime import datetime

        now = datetime.now()
        data = {
            "id": 1,
            "camera_id": 101,
            "camera_name": "Test Camera",
            "preset_index": 1,
            "preset_name": "Home Position",
            "touring_time": 10,
            "rois": [
                {
                    "id": 1,
                    "preset_id": 1,
                    "name": "Entry Zone",
                    "resolution_width": 1920.0,
                    "resolution_height": 1080.0,
                    "is_enable": True,
                    "points": [
                        {"id": 1, "x": 0.1, "y": 0.1, "order": 0},
                        {"id": 2, "x": 0.9, "y": 0.1, "order": 1}
                    ],
                    "created_at": now,
                    "updated_at": now
                }
            ],
            "created_at": now,
            "updated_at": now
        }
        schema = CameraPresetDetailResponse(**data)
        assert len(schema.rois) == 1
        assert schema.rois[0].name == "Entry Zone"
        assert len(schema.rois[0].points) == 2


class TestROISchema:
    """Phase 2.2: ROI Schema Tests"""

    def test_roi_create_schema_validates_required_fields(self):
        """Test: ROICreate schema validates required fields (name, resolution_width, resolution_height)"""
        from app.schemas.camera_preset import ROICreate

        # Valid data
        valid_data = {
            "name": "Entry Zone",
            "resolution_width": 1920.0,
            "resolution_height": 1080.0
        }
        schema = ROICreate(**valid_data)
        assert schema.name == "Entry Zone"
        assert schema.resolution_width == 1920.0
        assert schema.resolution_height == 1080.0

        # Missing name
        with pytest.raises(ValidationError):
            ROICreate(resolution_width=1920.0, resolution_height=1080.0)

        # Missing resolution_width
        with pytest.raises(ValidationError):
            ROICreate(name="Entry Zone", resolution_height=1080.0)

    def test_roi_create_schema_accepts_optional_points_list(self):
        """Test: ROICreate schema accepts optional points list"""
        from app.schemas.camera_preset import ROICreate

        # Without points
        schema = ROICreate(
            name="Entry Zone",
            resolution_width=1920.0,
            resolution_height=1080.0
        )
        assert schema.points is None

        # With points
        schema = ROICreate(
            name="Entry Zone",
            resolution_width=1920.0,
            resolution_height=1080.0,
            points=[
                {"x": 0.1, "y": 0.1, "order": 0},
                {"x": 0.9, "y": 0.1, "order": 1},
                {"x": 0.9, "y": 0.9, "order": 2}
            ]
        )
        assert len(schema.points) == 3
        assert schema.points[0].x == 0.1

    def test_roi_response_schema_includes_point_count(self):
        """Test: ROIResponse schema includes point_count"""
        from app.schemas.camera_preset import ROIResponse
        from datetime import datetime

        now = datetime.now()
        data = {
            "id": 1,
            "preset_id": 1,
            "name": "Entry Zone",
            "resolution_width": 1920.0,
            "resolution_height": 1080.0,
            "is_enable": True,
            "point_count": 4,
            "created_at": now,
            "updated_at": now
        }
        schema = ROIResponse(**data)
        assert schema.point_count == 4

    def test_roi_detail_response_schema_includes_points_list(self):
        """Test: ROIDetailResponse schema includes points list"""
        from app.schemas.camera_preset import ROIDetailResponse
        from datetime import datetime

        now = datetime.now()
        data = {
            "id": 1,
            "preset_id": 1,
            "name": "Entry Zone",
            "resolution_width": 1920.0,
            "resolution_height": 1080.0,
            "is_enable": True,
            "points": [
                {"id": 1, "x": 0.1, "y": 0.1, "order": 0},
                {"id": 2, "x": 0.9, "y": 0.1, "order": 1},
                {"id": 3, "x": 0.9, "y": 0.9, "order": 2},
                {"id": 4, "x": 0.1, "y": 0.9, "order": 3}
            ],
            "created_at": now,
            "updated_at": now
        }
        schema = ROIDetailResponse(**data)
        assert len(schema.points) == 4
        assert schema.points[0].x == 0.1
        assert schema.points[0].order == 0


class TestXyPointSchema:
    """Phase 3.2: XyPoint Schema Tests"""

    def test_xypoint_create_schema_validates_required_fields(self):
        """Test: XyPointCreate schema validates required fields (x, y, order)"""
        from app.schemas.camera_preset import XyPointCreate

        # Valid data
        valid_data = {"x": 0.5, "y": 0.5, "order": 0}
        schema = XyPointCreate(**valid_data)
        assert schema.x == 0.5
        assert schema.y == 0.5
        assert schema.order == 0

        # Missing x
        with pytest.raises(ValidationError):
            XyPointCreate(y=0.5, order=0)

        # Missing y
        with pytest.raises(ValidationError):
            XyPointCreate(x=0.5, order=0)

        # Missing order
        with pytest.raises(ValidationError):
            XyPointCreate(x=0.5, y=0.5)

    def test_xypoint_response_schema_returns_all_fields(self):
        """Test: XyPointResponse schema returns all fields"""
        from app.schemas.camera_preset import XyPointResponse

        data = {
            "id": 1,
            "x": 0.25,
            "y": 0.75,
            "order": 2
        }
        schema = XyPointResponse(**data)
        assert schema.id == 1
        assert schema.x == 0.25
        assert schema.y == 0.75
        assert schema.order == 2
