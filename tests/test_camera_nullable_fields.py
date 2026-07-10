"""
Test: Camera nullable fields (user_name, user_password, urls)
PRD: PRD_Device_Inheritance_Structure_Refactoring.md v1.2
PRD: PRD_Camera_Urls_JsonB.md v1.0 - rtsp_uri/rtsp_port replaced with urls JSONB

TDD Phase 3: Red - Write failing tests for Camera nullable fields
"""
import pytest
from sqlalchemy import inspect


class TestCameraNullableFields:
    """Camera nullable 필드 테스트"""

    def test_camera_user_name_is_nullable(self):
        """Camera.user_name 컬럼이 nullable=True인지 확인"""
        from app.models.device import Camera

        mapper = inspect(Camera)
        column = mapper.columns['user_name']
        assert column.nullable is True, "Camera.user_name should be nullable=True per PRD v1.2"

    def test_camera_user_password_is_nullable(self):
        """Camera.user_password 컬럼이 nullable=True인지 확인"""
        from app.models.device import Camera

        mapper = inspect(Camera)
        column = mapper.columns['user_password']
        assert column.nullable is True, "Camera.user_password should be nullable=True per PRD v1.2"

    def test_camera_urls_is_nullable(self):
        """Camera.urls 컬럼이 nullable=True인지 확인

        PRD: PRD_Camera_Urls_JsonB.md v1.0
        - rtsp_uri/rtsp_port 제거, urls JSONB로 대체
        """
        from app.models.device import Camera

        mapper = inspect(Camera)
        column = mapper.columns['urls']
        assert column.nullable is True, "Camera.urls should be nullable=True per PRD v1.0"

    def test_create_camera_without_auth_fields(self, db_session):
        """인증 필드 없이 Camera 생성이 가능한지 테스트

        PRD: PRD_Camera_Urls_JsonB.md v1.0
        - urls=None 허용
        """
        from app.models.device import Camera
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType

        camera = Camera(
            number_device=88888,
            group_device=1,
            name_device="Test Camera No Auth",
            type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.200",
            ip_port=80,
            user_name=None,  # nullable
            user_password=None,  # nullable
            urls=None,  # nullable (PRD_Camera_Urls_JsonB.md)
            mode=EnumCameraMode.NONE,
            category=EnumCameraType.FIXED,
            version=None
        )

        db_session.add(camera)
        db_session.commit()

        assert camera.id is not None
        assert camera.user_name is None
        assert camera.user_password is None
        assert camera.urls is None

        # Cleanup
        db_session.delete(camera)
        db_session.commit()

    def test_create_camera_with_partial_auth_fields(self, db_session):
        """일부 인증 필드만으로 Camera 생성 테스트

        PRD: PRD_Camera_Urls_JsonB.md v1.0
        - urls JSONB 사용
        """
        from app.models.device import Camera
        from app.utils.enums import EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType

        camera = Camera(
            number_device=88887,
            group_device=1,
            name_device="Test Camera Partial Auth",
            type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.201",
            ip_port=80,
            user_name="admin",  # 제공
            user_password=None,  # nullable
            urls={"streams": {"rtsp": {"main": "rtsp://192.168.1.201:554/stream"}}},  # urls JSONB
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ,
            version="1.0.0"
        )

        db_session.add(camera)
        db_session.commit()

        assert camera.id is not None
        assert camera.user_name == "admin"
        assert camera.user_password is None
        assert camera.urls is not None
        assert camera.urls["streams"]["rtsp"]["main"] == "rtsp://192.168.1.201:554/stream"

        # Cleanup
        db_session.delete(camera)
        db_session.commit()
