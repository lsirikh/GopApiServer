"""
Test: Camera URLs JSONB Schema - Phase 1
PRD Reference: docs/PRD_Camera_Urls_JsonB.md v1.0
TDD Phase: Red -> Green -> Refactor
"""
import pytest
from pydantic import ValidationError


# =============================================================================
# Phase 1.1: StreamUrls Schema Tests
# =============================================================================

class TestStreamUrlsSchema:
    """Phase 1.1: StreamUrls 스키마 테스트"""

    def test_stream_urls_has_main_field(self):
        """
        Test: StreamUrls has main field (Optional[str])

        Plan: Phase 1.1 - StreamUrls 스키마
        Expected: StreamUrls schema should have 'main' field as Optional[str]
        """
        from app.schemas.device import StreamUrls

        # Test with main field
        stream = StreamUrls(main="rtsp://192.168.0.10:554/stream1")
        assert stream.main == "rtsp://192.168.0.10:554/stream1"

        # Test main is optional (can be None)
        stream_none = StreamUrls()
        assert stream_none.main is None

    def test_stream_urls_has_sub_field(self):
        """
        Test: StreamUrls has sub field (Optional[str])

        Plan: Phase 1.1 - StreamUrls 스키마
        Expected: StreamUrls schema should have 'sub' field as Optional[str]
        """
        from app.schemas.device import StreamUrls

        # Test with sub field
        stream = StreamUrls(sub="rtsp://192.168.0.10:554/stream2")
        assert stream.sub == "rtsp://192.168.0.10:554/stream2"

        # Test sub is optional (can be None)
        stream_none = StreamUrls()
        assert stream_none.sub is None

    def test_stream_urls_allows_extra_fields(self):
        """
        Test: StreamUrls allows extra fields (extra="allow")

        Plan: Phase 1.1 - StreamUrls 스키마
        Expected: StreamUrls schema should allow extra fields for extensibility
        """
        from app.schemas.device import StreamUrls

        # Test with extra fields (should not raise error)
        stream = StreamUrls(
            main="rtsp://192.168.0.10:554/stream1",
            sub="rtsp://192.168.0.10:554/stream2",
            tertiary="rtsp://192.168.0.10:554/stream3",  # extra field
            mobile="rtsp://192.168.0.10:554/mobile"  # extra field
        )

        assert stream.main == "rtsp://192.168.0.10:554/stream1"
        assert stream.sub == "rtsp://192.168.0.10:554/stream2"
        # Extra fields should be accessible
        assert stream.tertiary == "rtsp://192.168.0.10:554/stream3"
        assert stream.mobile == "rtsp://192.168.0.10:554/mobile"


# =============================================================================
# Phase 1.2: HomepageUrl Schema Tests
# =============================================================================

class TestHomepageUrlSchema:
    """Phase 1.2: HomepageUrl 스키마 테스트"""

    def test_homepage_url_has_url_field(self):
        """
        Test: HomepageUrl has url field (Optional[str])

        Plan: Phase 1.2 - HomepageUrl 스키마
        Expected: HomepageUrl schema should have 'url' field as Optional[str]
        """
        from app.schemas.device import HomepageUrl

        # Test with url field
        homepage = HomepageUrl(url="https://192.168.0.10/")
        assert homepage.url == "https://192.168.0.10/"

        # Test url is optional (can be None)
        homepage_none = HomepageUrl()
        assert homepage_none.url is None


# =============================================================================
# Phase 1.3: OnvifUrl Schema Tests
# =============================================================================

class TestOnvifUrlSchema:
    """Phase 1.3: OnvifUrl 스키마 테스트"""

    def test_onvif_url_has_device_service_field(self):
        """
        Test: OnvifUrl has device_service field (Optional[str])

        Plan: Phase 1.3 - OnvifUrl 스키마
        Expected: OnvifUrl schema should have 'device_service' field as Optional[str]
        """
        from app.schemas.device import OnvifUrl

        # Test with device_service field
        onvif = OnvifUrl(device_service="http://192.168.0.10:8000/onvif/device_service")
        assert onvif.device_service == "http://192.168.0.10:8000/onvif/device_service"

        # Test device_service is optional (can be None)
        onvif_none = OnvifUrl()
        assert onvif_none.device_service is None

    def test_onvif_url_has_media_service_field(self):
        """
        Test: OnvifUrl has media_service field (Optional[str])

        Plan: Phase 1.3 - OnvifUrl 스키마
        Expected: OnvifUrl schema should have 'media_service' field as Optional[str]
        """
        from app.schemas.device import OnvifUrl

        # Test with media_service field
        onvif = OnvifUrl(media_service="http://192.168.0.10:8000/onvif/media_service")
        assert onvif.media_service == "http://192.168.0.10:8000/onvif/media_service"

        # Test media_service is optional (can be None)
        onvif_none = OnvifUrl()
        assert onvif_none.media_service is None

    def test_onvif_url_has_ptz_service_field(self):
        """
        Test: OnvifUrl has ptz_service field (Optional[str])

        Plan: Phase 1.3 - OnvifUrl 스키마
        Expected: OnvifUrl schema should have 'ptz_service' field as Optional[str]
        """
        from app.schemas.device import OnvifUrl

        # Test with ptz_service field
        onvif = OnvifUrl(ptz_service="http://192.168.0.10:8000/onvif/ptz_service")
        assert onvif.ptz_service == "http://192.168.0.10:8000/onvif/ptz_service"

        # Test ptz_service is optional (can be None)
        onvif_none = OnvifUrl()
        assert onvif_none.ptz_service is None


# =============================================================================
# Phase 1.4: CameraUrls Schema Tests
# =============================================================================

class TestCameraUrlsSchema:
    """Phase 1.4: CameraUrls 스키마 테스트"""

    def test_camera_urls_has_homepage_field(self):
        """
        Test: CameraUrls has homepage field (Optional[HomepageUrl])

        Plan: Phase 1.4 - CameraUrls 스키마
        Expected: CameraUrls schema should have 'homepage' field as Optional[HomepageUrl]
        """
        from app.schemas.device import CameraUrls, HomepageUrl

        # Test with homepage field
        urls = CameraUrls(homepage=HomepageUrl(url="https://192.168.0.10/"))
        assert urls.homepage is not None
        assert urls.homepage.url == "https://192.168.0.10/"

        # Test homepage is optional (can be None)
        urls_none = CameraUrls()
        assert urls_none.homepage is None

    def test_camera_urls_has_onvif_field(self):
        """
        Test: CameraUrls has onvif field (Optional[OnvifUrl])

        Plan: Phase 1.4 - CameraUrls 스키마
        Expected: CameraUrls schema should have 'onvif' field as Optional[OnvifUrl]
        """
        from app.schemas.device import CameraUrls, OnvifUrl

        # Test with onvif field
        urls = CameraUrls(onvif=OnvifUrl(
            device_service="http://192.168.0.10:8000/onvif/device_service"
        ))
        assert urls.onvif is not None
        assert urls.onvif.device_service == "http://192.168.0.10:8000/onvif/device_service"

        # Test onvif is optional (can be None)
        urls_none = CameraUrls()
        assert urls_none.onvif is None

    def test_camera_urls_has_streams_field(self):
        """
        Test: CameraUrls has streams field (Optional[Dict[str, StreamUrls]])

        Plan: Phase 1.4 - CameraUrls 스키마
        Expected: CameraUrls schema should have 'streams' field as Optional[Dict[str, StreamUrls]]
        """
        from app.schemas.device import CameraUrls, StreamUrls

        # Test with streams field
        urls = CameraUrls(streams={
            "rtsp": StreamUrls(main="rtsp://192.168.0.10:554/stream1"),
            "webrtc": StreamUrls(main="https://192.168.0.10/webrtc")
        })
        assert urls.streams is not None
        assert "rtsp" in urls.streams
        assert urls.streams["rtsp"].main == "rtsp://192.168.0.10:554/stream1"
        assert "webrtc" in urls.streams
        assert urls.streams["webrtc"].main == "https://192.168.0.10/webrtc"

        # Test streams is optional (can be None)
        urls_none = CameraUrls()
        assert urls_none.streams is None

    def test_camera_urls_has_snapshot_field(self):
        """
        Test: CameraUrls has snapshot field (Optional[Dict[str, str]])

        Plan: Phase 1.4 - CameraUrls 스키마
        Expected: CameraUrls schema should have 'snapshot' field as Optional[Dict[str, str]]
        """
        from app.schemas.device import CameraUrls

        # Test with snapshot field
        urls = CameraUrls(snapshot={
            "ch1": "http://192.168.0.10/snapshot/ch1.jpg",
            "ch2": "http://192.168.0.10/snapshot/ch2.jpg"
        })
        assert urls.snapshot is not None
        assert "ch1" in urls.snapshot
        assert urls.snapshot["ch1"] == "http://192.168.0.10/snapshot/ch1.jpg"
        assert "ch2" in urls.snapshot
        assert urls.snapshot["ch2"] == "http://192.168.0.10/snapshot/ch2.jpg"

        # Test snapshot is optional (can be None)
        urls_none = CameraUrls()
        assert urls_none.snapshot is None

    def test_camera_urls_allows_extra_fields(self):
        """
        Test: CameraUrls allows extra fields (extra="allow")

        Plan: Phase 1.4 - CameraUrls 스키마
        Expected: CameraUrls schema should allow extra fields for extensibility
        """
        from app.schemas.device import CameraUrls

        # Test with extra fields (should not raise error)
        urls = CameraUrls(
            custom_url="https://192.168.0.10/custom",  # extra field
            vendor_specific={"key": "value"}  # extra field
        )

        # Extra fields should be accessible
        assert urls.custom_url == "https://192.168.0.10/custom"
        assert urls.vendor_specific == {"key": "value"}


# =============================================================================
# Phase 2.1: CameraCreate Schema Tests
# =============================================================================

class TestCameraCreateUrlsSchema:
    """Phase 2.1: CameraCreate 스키마 수정 테스트"""

    def test_camera_create_has_urls_field(self):
        """
        Test: CameraCreate has urls field (Optional[CameraUrls])

        Plan: Phase 2.1 - CameraCreate 스키마
        Expected: CameraCreate schema should have 'urls' field as Optional[CameraUrls]
        """
        from app.schemas.device import CameraCreate, CameraUrls, StreamUrls

        camera_data = {
            "number_device": 2000,
            "group_device": 1,
            "name_device": "PTZ Camera 1",
            "type_device": "IpCamera",
            "version": "2.1.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.1.100",
            "ip_port": 80,
            "mode": "ONVIF",
            "category": "PTZ",
            "urls": {
                "streams": {
                    "rtsp": {"main": "rtsp://192.168.1.100:554/stream1"}
                }
            }
        }

        camera_create = CameraCreate(**camera_data)
        assert camera_create.urls is not None
        assert camera_create.urls.streams is not None
        assert camera_create.urls.streams["rtsp"].main == "rtsp://192.168.1.100:554/stream1"

    def test_camera_create_does_not_have_rtsp_uri_field(self):
        """
        Test: CameraCreate does NOT have rtsp_uri field

        Plan: Phase 2.1 - CameraCreate 스키마
        Expected: CameraCreate schema should NOT have 'rtsp_uri' field
        """
        from app.schemas.device import CameraCreate

        # Check that rtsp_uri is not a valid field
        assert not hasattr(CameraCreate.model_fields, 'rtsp_uri') or 'rtsp_uri' not in CameraCreate.model_fields

    def test_camera_create_does_not_have_rtsp_port_field(self):
        """
        Test: CameraCreate does NOT have rtsp_port field

        Plan: Phase 2.1 - CameraCreate 스키마
        Expected: CameraCreate schema should NOT have 'rtsp_port' field
        """
        from app.schemas.device import CameraCreate

        # Check that rtsp_port is not a valid field
        assert not hasattr(CameraCreate.model_fields, 'rtsp_port') or 'rtsp_port' not in CameraCreate.model_fields


# =============================================================================
# Phase 2.2: CameraResponse Schema Tests
# =============================================================================

class TestCameraResponseUrlsSchema:
    """Phase 2.2: CameraResponse 스키마 수정 테스트"""

    def test_camera_response_has_urls_field(self):
        """
        Test: CameraResponse has urls field (Optional[CameraUrls])

        Plan: Phase 2.2 - CameraResponse 스키마
        Expected: CameraResponse schema should have 'urls' field as Optional[CameraUrls]
        """
        from app.schemas.device import CameraResponse
        from datetime import datetime

        camera_data = {
            "id": 1,
            "number_device": 2000,
            "group_device": 1,
            "name_device": "PTZ Camera 1",
            "type_device": "IpCamera",
            "version": "2.1.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.1.100",
            "ip_port": 80,
            "mode": "ONVIF",
            "category": "PTZ",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "urls": {
                "streams": {
                    "rtsp": {"main": "rtsp://192.168.1.100:554/stream1"}
                }
            }
        }

        camera_response = CameraResponse(**camera_data)
        assert camera_response.urls is not None
        assert camera_response.urls.streams is not None

    def test_camera_response_does_not_have_rtsp_uri_field(self):
        """
        Test: CameraResponse does NOT have rtsp_uri field

        Plan: Phase 2.2 - CameraResponse 스키마
        Expected: CameraResponse schema should NOT have 'rtsp_uri' field
        """
        from app.schemas.device import CameraResponse

        # Check that rtsp_uri is not a valid field
        assert 'rtsp_uri' not in CameraResponse.model_fields

    def test_camera_response_does_not_have_rtsp_port_field(self):
        """
        Test: CameraResponse does NOT have rtsp_port field

        Plan: Phase 2.2 - CameraResponse 스키마
        Expected: CameraResponse schema should NOT have 'rtsp_port' field
        """
        from app.schemas.device import CameraResponse

        # Check that rtsp_port is not a valid field
        assert 'rtsp_port' not in CameraResponse.model_fields


# =============================================================================
# Phase 2.3: CameraUpdate Schema Tests
# =============================================================================

class TestCameraUpdateUrlsSchema:
    """Phase 2.3: CameraUpdate 스키마 수정 테스트"""

    def test_camera_update_has_urls_field(self):
        """
        Test: CameraUpdate has urls field (Optional[CameraUrls])

        Plan: Phase 2.3 - CameraUpdate 스키마
        Expected: CameraUpdate schema should have 'urls' field as Optional[CameraUrls]
        """
        from app.schemas.device import CameraUpdate

        camera_update = CameraUpdate(
            urls={
                "streams": {
                    "rtsp": {"main": "rtsp://192.168.1.100:554/stream1"}
                }
            }
        )
        assert camera_update.urls is not None

    def test_camera_update_does_not_have_rtsp_uri_field(self):
        """
        Test: CameraUpdate does NOT have rtsp_uri field

        Plan: Phase 2.3 - CameraUpdate 스키마
        Expected: CameraUpdate schema should NOT have 'rtsp_uri' field
        """
        from app.schemas.device import CameraUpdate

        # Check that rtsp_uri is not a valid field
        assert 'rtsp_uri' not in CameraUpdate.model_fields

    def test_camera_update_does_not_have_rtsp_port_field(self):
        """
        Test: CameraUpdate does NOT have rtsp_port field

        Plan: Phase 2.3 - CameraUpdate 스키마
        Expected: CameraUpdate schema should NOT have 'rtsp_port' field
        """
        from app.schemas.device import CameraUpdate

        # Check that rtsp_port is not a valid field
        assert 'rtsp_port' not in CameraUpdate.model_fields


# =============================================================================
# Phase 2.4: CameraNestedResponse Schema Tests
# =============================================================================

class TestCameraNestedResponseUrlsSchema:
    """Phase 2.4: CameraNestedResponse 스키마 수정 테스트"""

    def test_camera_nested_response_has_urls_field(self):
        """
        Test: CameraNestedResponse has urls field (Optional[CameraUrls])

        Plan: Phase 2.4 - CameraNestedResponse 스키마
        Expected: CameraNestedResponse schema should have 'urls' field as Optional[CameraUrls]
        """
        from app.schemas.device import CameraNestedResponse

        camera_data = {
            "id": 1,
            "number_device": 2000,
            "group_device": 1,
            "name_device": "PTZ Camera 1",
            "type_device": "IpCamera",
            "version": "2.1.0",
            "status": "ACTIVATED",
            "ip_address": "192.168.1.100",
            "ip_port": 80,
            "mode": "ONVIF",
            "category": "PTZ",
            "is_record": False,
            "urls": {
                "streams": {
                    "rtsp": {"main": "rtsp://192.168.1.100:554/stream1"}
                }
            }
        }

        camera_nested = CameraNestedResponse(**camera_data)
        assert camera_nested.urls is not None
        assert camera_nested.urls.streams is not None

    def test_camera_nested_response_does_not_have_rtsp_uri_field(self):
        """
        Test: CameraNestedResponse does NOT have rtsp_uri field

        Plan: Phase 2.4 - CameraNestedResponse 스키마
        Expected: CameraNestedResponse schema should NOT have 'rtsp_uri' field
        """
        from app.schemas.device import CameraNestedResponse

        # Check that rtsp_uri is not a valid field
        assert 'rtsp_uri' not in CameraNestedResponse.model_fields

    def test_camera_nested_response_does_not_have_rtsp_port_field(self):
        """
        Test: CameraNestedResponse does NOT have rtsp_port field

        Plan: Phase 2.4 - CameraNestedResponse 스키마
        Expected: CameraNestedResponse schema should NOT have 'rtsp_port' field
        """
        from app.schemas.device import CameraNestedResponse

        # Check that rtsp_port is not a valid field
        assert 'rtsp_port' not in CameraNestedResponse.model_fields


# =============================================================================
# Phase 2.5: DeviceNestedResponse Schema Tests
# =============================================================================

class TestDeviceNestedResponseUrlsSchema:
    """Phase 2.5: DeviceNestedResponse 스키마 수정 테스트"""

    def test_device_nested_response_has_urls_field(self):
        """
        Test: DeviceNestedResponse has urls field (Optional[CameraUrls])

        Plan: Phase 2.5 - DeviceNestedResponse 스키마
        Expected: DeviceNestedResponse schema should have 'urls' field as Optional[CameraUrls]
        """
        from app.schemas.device import DeviceNestedResponse

        # Camera type device with urls
        device_data = {
            "id": 1,
            "number_device": 2000,
            "group_device": 1,
            "name_device": "PTZ Camera 1",
            "type_device": "IpCamera",
            "status": "ACTIVATED",
            "ip_address": "192.168.1.100",
            "ip_port": 80,
            "mode": "ONVIF",
            "category": "PTZ",
            "urls": {
                "streams": {
                    "rtsp": {"main": "rtsp://192.168.1.100:554/stream1"}
                }
            }
        }

        device_nested = DeviceNestedResponse(**device_data)
        assert device_nested.urls is not None
        assert device_nested.urls.streams is not None

    def test_device_nested_response_does_not_have_rtsp_uri_field(self):
        """
        Test: DeviceNestedResponse does NOT have rtsp_uri field

        Plan: Phase 2.5 - DeviceNestedResponse 스키마
        Expected: DeviceNestedResponse schema should NOT have 'rtsp_uri' field
        """
        from app.schemas.device import DeviceNestedResponse

        # Check that rtsp_uri is not a valid field
        assert 'rtsp_uri' not in DeviceNestedResponse.model_fields

    def test_device_nested_response_does_not_have_rtsp_port_field(self):
        """
        Test: DeviceNestedResponse does NOT have rtsp_port field

        Plan: Phase 2.5 - DeviceNestedResponse 스키마
        Expected: DeviceNestedResponse schema should NOT have 'rtsp_port' field
        """
        from app.schemas.device import DeviceNestedResponse

        # Check that rtsp_port is not a valid field
        assert 'rtsp_port' not in DeviceNestedResponse.model_fields


# =============================================================================
# Phase 3.1: Camera Model Column Tests
# =============================================================================

class TestCameraModelColumns:
    """Phase 3.1: Camera 모델 컬럼 변경 테스트"""

    def test_camera_model_has_urls_column(self):
        """
        Test: Camera model has urls column (JSON type)

        Plan: Phase 3.1 - Camera 모델 컬럼 변경
        Expected: Camera model should have 'urls' column with JSON type
        """
        from app.models.device import Camera
        from sqlalchemy import inspect

        # Check column exists
        mapper = inspect(Camera)
        column_names = [col.key for col in mapper.columns]
        assert 'urls' in column_names

        # Check column type is JSON
        urls_column = mapper.columns['urls']
        from sqlalchemy import JSON
        assert isinstance(urls_column.type, JSON)

    def test_camera_model_does_not_have_rtsp_uri_column(self):
        """
        Test: Camera model does NOT have rtsp_uri column

        Plan: Phase 3.1 - Camera 모델 컬럼 변경
        Expected: Camera model should NOT have 'rtsp_uri' column
        """
        from app.models.device import Camera
        from sqlalchemy import inspect

        mapper = inspect(Camera)
        column_names = [col.key for col in mapper.columns]
        assert 'rtsp_uri' not in column_names

    def test_camera_model_does_not_have_rtsp_port_column(self):
        """
        Test: Camera model does NOT have rtsp_port column

        Plan: Phase 3.1 - Camera 모델 컬럼 변경
        Expected: Camera model should NOT have 'rtsp_port' column
        """
        from app.models.device import Camera
        from sqlalchemy import inspect

        mapper = inspect(Camera)
        column_names = [col.key for col in mapper.columns]
        assert 'rtsp_port' not in column_names

    def test_camera_urls_is_nullable(self):
        """
        Test: Camera.urls is nullable

        Plan: Phase 3.1 - Camera 모델 컬럼 변경
        Expected: Camera.urls column should be nullable
        """
        from app.models.device import Camera
        from sqlalchemy import inspect

        mapper = inspect(Camera)
        urls_column = mapper.columns['urls']
        assert urls_column.nullable is True


# =============================================================================
# Phase 3.2: Camera Model urls JSONB Storage Tests
# =============================================================================

class TestCameraModelUrlsStorage:
    """Phase 3.2: Camera 모델 urls JSONB 저장 테스트"""

    def test_camera_urls_can_store_homepage_structure(self, test_db):
        """
        Test: Camera.urls can store homepage structure

        Plan: Phase 3.2 - Camera 모델 urls JSONB 저장
        Expected: Camera.urls should be able to store homepage structure
        """
        from app.models.device import Camera, EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType

        camera = Camera(
            number_device=3001,
            group_device=1,
            name_device="Test Camera Homepage",
            type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.100",
            ip_port=80,
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ,
            urls={
                "homepage": {
                    "url": "https://192.168.1.100/"
                }
            }
        )
        test_db.add(camera)
        test_db.commit()
        test_db.refresh(camera)

        assert camera.urls is not None
        assert camera.urls["homepage"]["url"] == "https://192.168.1.100/"

    def test_camera_urls_can_store_onvif_structure(self, test_db):
        """
        Test: Camera.urls can store onvif structure

        Plan: Phase 3.2 - Camera 모델 urls JSONB 저장
        Expected: Camera.urls should be able to store onvif structure
        """
        from app.models.device import Camera, EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType

        camera = Camera(
            number_device=3002,
            group_device=1,
            name_device="Test Camera Onvif",
            type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.101",
            ip_port=80,
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ,
            urls={
                "onvif": {
                    "device_service": "http://192.168.1.101:8000/onvif/device_service",
                    "media_service": "http://192.168.1.101:8000/onvif/media_service",
                    "ptz_service": "http://192.168.1.101:8000/onvif/ptz_service"
                }
            }
        )
        test_db.add(camera)
        test_db.commit()
        test_db.refresh(camera)

        assert camera.urls is not None
        assert camera.urls["onvif"]["device_service"] == "http://192.168.1.101:8000/onvif/device_service"
        assert camera.urls["onvif"]["media_service"] == "http://192.168.1.101:8000/onvif/media_service"
        assert camera.urls["onvif"]["ptz_service"] == "http://192.168.1.101:8000/onvif/ptz_service"

    def test_camera_urls_can_store_streams_rtsp_structure(self, test_db):
        """
        Test: Camera.urls can store streams.rtsp structure

        Plan: Phase 3.2 - Camera 모델 urls JSONB 저장
        Expected: Camera.urls should be able to store streams.rtsp structure
        """
        from app.models.device import Camera, EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType

        camera = Camera(
            number_device=3003,
            group_device=1,
            name_device="Test Camera RTSP",
            type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.102",
            ip_port=80,
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ,
            urls={
                "streams": {
                    "rtsp": {
                        "main": "rtsp://192.168.1.102:554/stream1",
                        "sub": "rtsp://192.168.1.102:554/stream2"
                    }
                }
            }
        )
        test_db.add(camera)
        test_db.commit()
        test_db.refresh(camera)

        assert camera.urls is not None
        assert camera.urls["streams"]["rtsp"]["main"] == "rtsp://192.168.1.102:554/stream1"
        assert camera.urls["streams"]["rtsp"]["sub"] == "rtsp://192.168.1.102:554/stream2"

    def test_camera_urls_can_store_streams_webrtc_structure(self, test_db):
        """
        Test: Camera.urls can store streams.webrtc structure

        Plan: Phase 3.2 - Camera 모델 urls JSONB 저장
        Expected: Camera.urls should be able to store streams.webrtc structure
        """
        from app.models.device import Camera, EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType

        camera = Camera(
            number_device=3004,
            group_device=1,
            name_device="Test Camera WebRTC",
            type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.103",
            ip_port=80,
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ,
            urls={
                "streams": {
                    "webrtc": {
                        "main": "https://192.168.1.103/webrtc/stream1"
                    }
                }
            }
        )
        test_db.add(camera)
        test_db.commit()
        test_db.refresh(camera)

        assert camera.urls is not None
        assert camera.urls["streams"]["webrtc"]["main"] == "https://192.168.1.103/webrtc/stream1"

    def test_camera_urls_can_store_snapshot_structure(self, test_db):
        """
        Test: Camera.urls can store snapshot structure

        Plan: Phase 3.2 - Camera 모델 urls JSONB 저장
        Expected: Camera.urls should be able to store snapshot structure
        """
        from app.models.device import Camera, EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType

        camera = Camera(
            number_device=3005,
            group_device=1,
            name_device="Test Camera Snapshot",
            type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.104",
            ip_port=80,
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ,
            urls={
                "snapshot": {
                    "ch1": "http://192.168.1.104/snapshot/ch1.jpg",
                    "ch2": "http://192.168.1.104/snapshot/ch2.jpg"
                }
            }
        )
        test_db.add(camera)
        test_db.commit()
        test_db.refresh(camera)

        assert camera.urls is not None
        assert camera.urls["snapshot"]["ch1"] == "http://192.168.1.104/snapshot/ch1.jpg"
        assert camera.urls["snapshot"]["ch2"] == "http://192.168.1.104/snapshot/ch2.jpg"

    def test_camera_urls_can_store_full_nested_structure(self, test_db):
        """
        Test: Camera.urls can store full nested structure

        Plan: Phase 3.2 - Camera 모델 urls JSONB 저장
        Expected: Camera.urls should be able to store full nested structure
        """
        from app.models.device import Camera, EnumDeviceType, EnumDeviceStatus, EnumCameraMode, EnumCameraType

        full_urls = {
            "homepage": {
                "url": "https://192.168.1.105/"
            },
            "onvif": {
                "device_service": "http://192.168.1.105:8000/onvif/device_service",
                "media_service": "http://192.168.1.105:8000/onvif/media_service",
                "ptz_service": "http://192.168.1.105:8000/onvif/ptz_service"
            },
            "streams": {
                "rtsp": {
                    "main": "rtsp://192.168.1.105:554/stream1",
                    "sub": "rtsp://192.168.1.105:554/stream2"
                },
                "webrtc": {
                    "main": "https://192.168.1.105/webrtc/stream1"
                }
            },
            "snapshot": {
                "ch1": "http://192.168.1.105/snapshot/ch1.jpg"
            }
        }

        camera = Camera(
            number_device=3006,
            group_device=1,
            name_device="Test Camera Full",
            type_device=EnumDeviceType.IpCamera,
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="192.168.1.105",
            ip_port=80,
            mode=EnumCameraMode.ONVIF,
            category=EnumCameraType.PTZ,
            urls=full_urls
        )
        test_db.add(camera)
        test_db.commit()
        test_db.refresh(camera)

        assert camera.urls is not None
        # homepage
        assert camera.urls["homepage"]["url"] == "https://192.168.1.105/"
        # onvif
        assert camera.urls["onvif"]["device_service"] == "http://192.168.1.105:8000/onvif/device_service"
        # streams.rtsp
        assert camera.urls["streams"]["rtsp"]["main"] == "rtsp://192.168.1.105:554/stream1"
        # streams.webrtc
        assert camera.urls["streams"]["webrtc"]["main"] == "https://192.168.1.105/webrtc/stream1"
        # snapshot
        assert camera.urls["snapshot"]["ch1"] == "http://192.168.1.105/snapshot/ch1.jpg"
