"""
Tests for CameraPreset, ROI, XyPoint models
TDD Phase 1: Model Tests

PRD: PRD_Camera_Urls_JsonB.md v1.0 - Updated to use urls JSONB instead of rtsp_uri/rtsp_port
"""
import pytest
from sqlalchemy import inspect
from datetime import datetime


class TestCameraPresetModel:
    """Phase 1.1: CameraPreset Model Tests"""

    def test_camera_preset_model_has_required_fields(self, db_session):
        """Test: CameraPreset model has required fields"""
        from app.models.camera_preset import CameraPreset

        # Check table exists and has required columns
        inspector = inspect(db_session.bind)
        columns = {col['name'] for col in inspector.get_columns('camera_presets')}

        required_fields = {
            'id', 'camera_id', 'camera_name', 'preset_index',
            'preset_name', 'touring_time', 'created_at', 'updated_at'
        }

        assert required_fields.issubset(columns), f"Missing columns: {required_fields - columns}"

    def test_camera_preset_has_fk_relationship_to_camera(self, db_session):
        """Test: CameraPreset has FK relationship to Camera"""
        from app.models.camera_preset import CameraPreset
        from app.models.device import Camera
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType, EnumDeviceCategory

        # Create a camera
        camera = Camera(
            category_device=EnumDeviceCategory.CAMERA,
            number_device=1,
            group_device=1,
            name_device="Test Camera",
            type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.100",
            ip_port=80,
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ
        )
        db_session.add(camera)
        db_session.commit()
        db_session.refresh(camera)

        # Create a preset linked to camera
        preset = CameraPreset(
            camera_id=camera.id,
            camera_name=camera.name_device,
            preset_index=1,
            preset_name="Home Position",
            touring_time=10
        )
        db_session.add(preset)
        db_session.commit()
        db_session.refresh(preset)

        # Verify FK relationship
        assert preset.camera_id == camera.id
        assert preset.camera.id == camera.id
        assert preset.camera.name_device == "Test Camera"

    def test_camera_preset_unique_constraint_on_camera_id_preset_index(self, db_session):
        """Test: CameraPreset unique constraint on (camera_id, preset_index)"""
        from app.models.camera_preset import CameraPreset
        from app.models.device import Camera
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType, EnumDeviceCategory
        from sqlalchemy.exc import IntegrityError

        # Create a camera
        camera = Camera(
            category_device=EnumDeviceCategory.CAMERA,
            number_device=1,
            group_device=1,
            name_device="Test Camera",
            type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.100",
            ip_port=80,
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ
        )
        db_session.add(camera)
        db_session.commit()
        db_session.refresh(camera)

        # Create first preset with preset_index=1
        preset1 = CameraPreset(
            camera_id=camera.id,
            camera_name=camera.name_device,
            preset_index=1,
            preset_name="Home Position",
            touring_time=10
        )
        db_session.add(preset1)
        db_session.commit()

        # Try to create second preset with same camera_id and preset_index
        preset2 = CameraPreset(
            camera_id=camera.id,
            camera_name=camera.name_device,
            preset_index=1,  # Duplicate
            preset_name="Duplicate Position",
            touring_time=15
        )
        db_session.add(preset2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_camera_preset_cascade_delete_when_camera_is_deleted(self, db_session):
        """Test: CameraPreset cascade delete when Camera is deleted"""
        from app.models.camera_preset import CameraPreset
        from app.models.device import Camera
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType, EnumDeviceCategory

        # Create a camera
        camera = Camera(
            category_device=EnumDeviceCategory.CAMERA,
            number_device=1,
            group_device=1,
            name_device="Test Camera",
            type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.100",
            ip_port=80,
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ
        )
        db_session.add(camera)
        db_session.commit()
        db_session.refresh(camera)
        camera_id = camera.id

        # Create presets
        preset1 = CameraPreset(
            camera_id=camera.id,
            camera_name=camera.name_device,
            preset_index=1,
            preset_name="Home Position",
            touring_time=10
        )
        preset2 = CameraPreset(
            camera_id=camera.id,
            camera_name=camera.name_device,
            preset_index=2,
            preset_name="Gate View",
            touring_time=15
        )
        db_session.add_all([preset1, preset2])
        db_session.commit()

        # Verify presets exist
        presets = db_session.query(CameraPreset).filter_by(camera_id=camera_id).all()
        assert len(presets) == 2

        # Delete camera
        db_session.delete(camera)
        db_session.commit()

        # Verify presets are cascade deleted
        presets = db_session.query(CameraPreset).filter_by(camera_id=camera_id).all()
        assert len(presets) == 0


class TestROIModel:
    """Phase 2.1: ROI Model Tests"""

    def test_roi_model_has_required_fields(self, db_session):
        """Test: ROI model has required fields"""
        from sqlalchemy import inspect

        inspector = inspect(db_session.bind)
        columns = {col['name'] for col in inspector.get_columns('rois')}

        required_fields = {
            'id', 'preset_id', 'name', 'resolution_width',
            'resolution_height', 'is_enable', 'created_at', 'updated_at'
        }

        assert required_fields.issubset(columns), f"Missing columns: {required_fields - columns}"

    def test_roi_has_fk_relationship_to_camera_preset(self, db_session):
        """Test: ROI has FK relationship to CameraPreset"""
        from app.models.camera_preset import CameraPreset, ROI
        from app.models.device import Camera
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType, EnumDeviceCategory

        # Create camera
        camera = Camera(
            category_device=EnumDeviceCategory.CAMERA,
            number_device=1,
            group_device=1,
            name_device="Test Camera",
            type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.100",
            ip_port=80,
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ
        )
        db_session.add(camera)
        db_session.commit()

        # Create preset
        preset = CameraPreset(
            camera_id=camera.id,
            camera_name=camera.name_device,
            preset_index=1,
            preset_name="Home Position",
            touring_time=10
        )
        db_session.add(preset)
        db_session.commit()

        # Create ROI
        roi = ROI(
            preset_id=preset.id,
            name="Entry Zone",
            resolution_width=1920.0,
            resolution_height=1080.0,
            is_enable=True
        )
        db_session.add(roi)
        db_session.commit()
        db_session.refresh(roi)

        # Verify FK relationship
        assert roi.preset_id == preset.id
        assert roi.preset.id == preset.id
        assert roi.preset.preset_name == "Home Position"

    def test_roi_cascade_delete_when_camera_preset_is_deleted(self, db_session):
        """Test: ROI cascade delete when CameraPreset is deleted"""
        from app.models.camera_preset import CameraPreset, ROI
        from app.models.device import Camera
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType, EnumDeviceCategory

        # Create camera
        camera = Camera(
            category_device=EnumDeviceCategory.CAMERA,
            number_device=1,
            group_device=1,
            name_device="Test Camera",
            type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.100",
            ip_port=80,
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ
        )
        db_session.add(camera)
        db_session.commit()

        # Create preset
        preset = CameraPreset(
            camera_id=camera.id,
            camera_name=camera.name_device,
            preset_index=1,
            preset_name="Home Position",
            touring_time=10
        )
        db_session.add(preset)
        db_session.commit()
        preset_id = preset.id

        # Create ROIs
        roi1 = ROI(preset_id=preset.id, name="Zone A", resolution_width=1920.0, resolution_height=1080.0)
        roi2 = ROI(preset_id=preset.id, name="Zone B", resolution_width=1920.0, resolution_height=1080.0)
        db_session.add_all([roi1, roi2])
        db_session.commit()

        # Verify ROIs exist
        rois = db_session.query(ROI).filter_by(preset_id=preset_id).all()
        assert len(rois) == 2

        # Delete preset
        db_session.delete(preset)
        db_session.commit()

        # Verify ROIs are cascade deleted
        rois = db_session.query(ROI).filter_by(preset_id=preset_id).all()
        assert len(rois) == 0

    def test_roi_default_is_enable_true(self, db_session):
        """Test: ROI default is_enable=True"""
        from app.models.camera_preset import CameraPreset, ROI
        from app.models.device import Camera
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType, EnumDeviceCategory

        # Create camera
        camera = Camera(
            category_device=EnumDeviceCategory.CAMERA,
            number_device=1,
            group_device=1,
            name_device="Test Camera",
            type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.100",
            ip_port=80,
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ
        )
        db_session.add(camera)
        db_session.commit()

        # Create preset
        preset = CameraPreset(
            camera_id=camera.id,
            camera_name=camera.name_device,
            preset_index=1,
            preset_name="Home Position",
            touring_time=10
        )
        db_session.add(preset)
        db_session.commit()

        # Create ROI without specifying is_enable
        roi = ROI(
            preset_id=preset.id,
            name="Entry Zone",
            resolution_width=1920.0,
            resolution_height=1080.0
            # is_enable not specified - should default to True
        )
        db_session.add(roi)
        db_session.commit()
        db_session.refresh(roi)

        assert roi.is_enable is True


class TestXyPointModel:
    """Phase 3.1: XyPoint Model Tests"""

    def test_xypoint_model_has_required_fields(self, db_session):
        """Test: XyPoint model has required fields"""
        from sqlalchemy import inspect

        inspector = inspect(db_session.bind)
        columns = {col['name'] for col in inspector.get_columns('xy_points')}

        required_fields = {'id', 'roi_id', 'x', 'y', 'order', 'created_at', 'updated_at'}

        assert required_fields.issubset(columns), f"Missing columns: {required_fields - columns}"

    def test_xypoint_has_fk_relationship_to_roi(self, db_session):
        """Test: XyPoint has FK relationship to ROI"""
        from app.models.camera_preset import CameraPreset, ROI, XyPoint
        from app.models.device import Camera
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType, EnumDeviceCategory

        # Create camera
        camera = Camera(
            category_device=EnumDeviceCategory.CAMERA,
            number_device=1,
            group_device=1,
            name_device="Test Camera",
            type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.100",
            ip_port=80,
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ
        )
        db_session.add(camera)
        db_session.commit()

        # Create preset
        preset = CameraPreset(
            camera_id=camera.id,
            camera_name=camera.name_device,
            preset_index=1,
            preset_name="Home Position",
            touring_time=10
        )
        db_session.add(preset)
        db_session.commit()

        # Create ROI
        roi = ROI(
            preset_id=preset.id,
            name="Entry Zone",
            resolution_width=1920.0,
            resolution_height=1080.0
        )
        db_session.add(roi)
        db_session.commit()

        # Create XyPoint
        point = XyPoint(roi_id=roi.id, x=0.1, y=0.1, order=0)
        db_session.add(point)
        db_session.commit()
        db_session.refresh(point)

        # Verify FK relationship
        assert point.roi_id == roi.id
        assert point.roi.id == roi.id
        assert point.roi.name == "Entry Zone"

    def test_xypoint_unique_constraint_on_roi_id_order(self, db_session):
        """Test: XyPoint unique constraint on (roi_id, order)"""
        from app.models.camera_preset import CameraPreset, ROI, XyPoint
        from app.models.device import Camera
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType, EnumDeviceCategory
        from sqlalchemy.exc import IntegrityError

        # Create camera
        camera = Camera(
            category_device=EnumDeviceCategory.CAMERA,
            number_device=1,
            group_device=1,
            name_device="Test Camera",
            type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.100",
            ip_port=80,
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ
        )
        db_session.add(camera)
        db_session.commit()

        # Create preset
        preset = CameraPreset(
            camera_id=camera.id,
            camera_name=camera.name_device,
            preset_index=1,
            preset_name="Home Position",
            touring_time=10
        )
        db_session.add(preset)
        db_session.commit()

        # Create ROI
        roi = ROI(
            preset_id=preset.id,
            name="Entry Zone",
            resolution_width=1920.0,
            resolution_height=1080.0
        )
        db_session.add(roi)
        db_session.commit()

        # Create first point with order=0
        point1 = XyPoint(roi_id=roi.id, x=0.1, y=0.1, order=0)
        db_session.add(point1)
        db_session.commit()

        # Try to create second point with same roi_id and order
        point2 = XyPoint(roi_id=roi.id, x=0.9, y=0.9, order=0)  # Duplicate order
        db_session.add(point2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_xypoint_cascade_delete_when_roi_is_deleted(self, db_session):
        """Test: XyPoint cascade delete when ROI is deleted"""
        from app.models.camera_preset import CameraPreset, ROI, XyPoint
        from app.models.device import Camera
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType, EnumDeviceCategory

        # Create camera
        camera = Camera(
            category_device=EnumDeviceCategory.CAMERA,
            number_device=1,
            group_device=1,
            name_device="Test Camera",
            type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.100",
            ip_port=80,
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ
        )
        db_session.add(camera)
        db_session.commit()

        # Create preset
        preset = CameraPreset(
            camera_id=camera.id,
            camera_name=camera.name_device,
            preset_index=1,
            preset_name="Home Position",
            touring_time=10
        )
        db_session.add(preset)
        db_session.commit()

        # Create ROI
        roi = ROI(
            preset_id=preset.id,
            name="Entry Zone",
            resolution_width=1920.0,
            resolution_height=1080.0
        )
        db_session.add(roi)
        db_session.commit()
        roi_id = roi.id

        # Create points
        points = [
            XyPoint(roi_id=roi.id, x=0.1, y=0.1, order=0),
            XyPoint(roi_id=roi.id, x=0.9, y=0.1, order=1),
            XyPoint(roi_id=roi.id, x=0.9, y=0.9, order=2),
            XyPoint(roi_id=roi.id, x=0.1, y=0.9, order=3)
        ]
        db_session.add_all(points)
        db_session.commit()

        # Verify points exist
        db_points = db_session.query(XyPoint).filter_by(roi_id=roi_id).all()
        assert len(db_points) == 4

        # Delete ROI
        db_session.delete(roi)
        db_session.commit()

        # Verify points are cascade deleted
        db_points = db_session.query(XyPoint).filter_by(roi_id=roi_id).all()
        assert len(db_points) == 0
