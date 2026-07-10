"""
Tests for Event Detail JSONB feature

PRD: PRD_Event_Detail_JsonB.md v1.0
TDD Plan: plan_event_detail.md

Phase 1: Schema Tests
"""
import pytest
from pydantic import ValidationError


class TestDetectionDetailObjectSchema:
    """Phase 1.1: DetectionDetailObject schema tests"""

    def test_detection_detail_object_valid(self):
        """DetectionDetailObject should accept valid data"""
        from app.schemas.event import DetectionDetailObject

        obj = DetectionDetailObject(
            label="person",
            confidence=0.92,
            bbox=[100, 200, 150, 300]
        )
        assert obj.label == "person"
        assert obj.confidence == 0.92
        assert obj.bbox == [100, 200, 150, 300]

    def test_detection_detail_object_confidence_bounds(self):
        """DetectionDetailObject confidence must be 0.0 to 1.0"""
        from app.schemas.event import DetectionDetailObject

        # Valid boundary values
        obj_min = DetectionDetailObject(label="test", confidence=0.0, bbox=[0, 0, 0, 0])
        assert obj_min.confidence == 0.0

        obj_max = DetectionDetailObject(label="test", confidence=1.0, bbox=[0, 0, 0, 0])
        assert obj_max.confidence == 1.0

        # Invalid: above 1.0
        with pytest.raises(ValidationError):
            DetectionDetailObject(label="test", confidence=1.1, bbox=[0, 0, 0, 0])

        # Invalid: below 0.0
        with pytest.raises(ValidationError):
            DetectionDetailObject(label="test", confidence=-0.1, bbox=[0, 0, 0, 0])

    def test_detection_detail_object_bbox_length(self):
        """DetectionDetailObject bbox must have exactly 4 elements"""
        from app.schemas.event import DetectionDetailObject

        # Valid: exactly 4 elements
        obj = DetectionDetailObject(label="test", confidence=0.5, bbox=[1, 2, 3, 4])
        assert len(obj.bbox) == 4

        # Invalid: less than 4 elements
        with pytest.raises(ValidationError):
            DetectionDetailObject(label="test", confidence=0.5, bbox=[1, 2, 3])

        # Invalid: more than 4 elements
        with pytest.raises(ValidationError):
            DetectionDetailObject(label="test", confidence=0.5, bbox=[1, 2, 3, 4, 5])

    def test_detection_detail_object_required_fields(self):
        """DetectionDetailObject requires all fields"""
        from app.schemas.event import DetectionDetailObject

        # Missing label
        with pytest.raises(ValidationError):
            DetectionDetailObject(confidence=0.5, bbox=[1, 2, 3, 4])

        # Missing confidence
        with pytest.raises(ValidationError):
            DetectionDetailObject(label="test", bbox=[1, 2, 3, 4])

        # Missing bbox
        with pytest.raises(ValidationError):
            DetectionDetailObject(label="test", confidence=0.5)


class TestDetectionDetailSchema:
    """Phase 1.3: DetectionDetail schema tests"""

    def test_detection_detail_valid_ai(self):
        """DetectionDetail should accept valid AI detection data"""
        from app.schemas.event import DetectionDetail, DetectionDetailObject

        detail = DetectionDetail(
            result="AI_PERSON",
            signal=0,
            thumbnail="http://192.168.1.50:8080/events/12345/thumb.jpg",
            objects=[
                DetectionDetailObject(label="person", confidence=0.92, bbox=[100, 200, 150, 300])
            ],
            model="yolov8n",
            inference_ms=45
        )
        assert detail.result == "AI_PERSON"
        assert detail.signal == 0
        assert detail.thumbnail == "http://192.168.1.50:8080/events/12345/thumb.jpg"
        assert len(detail.objects) == 1
        assert detail.model == "yolov8n"
        assert detail.inference_ms == 45

    def test_detection_detail_valid_sensor(self):
        """DetectionDetail should accept valid sensor detection data"""
        from app.schemas.event import DetectionDetail

        detail = DetectionDetail(
            result="Fence",
            signal=2300,
            thumbnail="http://192.168.1.50:8080/events/12346/thumb.jpg",
            objects=None,
            model=None,
            inference_ms=None
        )
        assert detail.result == "Fence"
        assert detail.signal == 2300
        assert detail.thumbnail == "http://192.168.1.50:8080/events/12346/thumb.jpg"
        assert detail.objects is None

    def test_detection_detail_thumbnail_required(self):
        """DetectionDetail requires thumbnail field"""
        from app.schemas.event import DetectionDetail

        # thumbnail is required
        with pytest.raises(ValidationError):
            DetectionDetail(
                result="AI_PERSON",
                signal=0
            )

    def test_detection_detail_optional_fields(self):
        """DetectionDetail has optional fields except thumbnail"""
        from app.schemas.event import DetectionDetail

        # Only thumbnail is required
        detail = DetectionDetail(
            thumbnail="http://example.com/thumb.jpg"
        )
        assert detail.thumbnail == "http://example.com/thumb.jpg"
        assert detail.result is None
        assert detail.signal is None
        assert detail.objects is None
        assert detail.model is None
        assert detail.inference_ms is None


class TestMalfunctionDetailSchema:
    """Phase 1.5: MalfunctionDetail schema tests (2선 케이블 제어기 시스템)

    PRD_Event_Field_Normalization.md v1.0:
    - reason: 별도 컬럼으로 분리됨 (MalfunctionDetail에서 제거)
    - detail: 케이블 위치 정보만 포함 (first_start, first_end, second_start, second_end)
    """

    def test_malfunction_detail_valid(self):
        """MalfunctionDetail should accept valid cable position data"""
        from app.schemas.event import MalfunctionDetail

        # PRD v1.0: reason 제거, 케이블 위치 정보만 포함
        detail = MalfunctionDetail(
            first_start=5,
            first_end=5,
            second_start=0,
            second_end=0
        )
        assert detail.first_start == 5
        assert detail.first_end == 5
        assert detail.second_start == 0
        assert detail.second_end == 0

    def test_malfunction_detail_all_optional(self):
        """MalfunctionDetail all fields are optional"""
        from app.schemas.event import MalfunctionDetail

        # Empty detail is valid (all cable positions optional)
        detail = MalfunctionDetail()
        assert detail.first_start is None
        assert detail.first_end is None
        assert detail.second_start is None
        assert detail.second_end is None

    def test_malfunction_detail_partial(self):
        """MalfunctionDetail accepts partial data"""
        from app.schemas.event import MalfunctionDetail

        # Only first cable positions
        detail = MalfunctionDetail(first_start=10, first_end=15)
        assert detail.first_start == 10
        assert detail.first_end == 15
        assert detail.second_start is None
        assert detail.second_end is None

        # Only second cable positions
        detail2 = MalfunctionDetail(second_start=20, second_end=25)
        assert detail2.first_start is None
        assert detail2.second_start == 20
        assert detail2.second_end == 25


# ===== Phase 2: Model Tests =====

class TestDetectionEventDetailModel:
    """Phase 2.1: DetectionEvent.detail column tests"""

    def test_detection_event_has_detail_column(self):
        """DetectionEvent model should have detail column"""
        from app.models.event import DetectionEvent

        # Check that detail column exists
        assert hasattr(DetectionEvent, 'detail')

    def test_detection_event_detail_nullable(self):
        """DetectionEvent.detail column should be nullable"""
        from app.models.event import DetectionEvent
        from sqlalchemy import inspect

        mapper = inspect(DetectionEvent)
        detail_column = mapper.columns.get('detail')
        assert detail_column is not None
        assert detail_column.nullable is True

    def test_detection_event_detail_jsonb_type(self):
        """DetectionEvent.detail column should be JSON type"""
        from app.models.event import DetectionEvent
        from sqlalchemy import inspect
        from sqlalchemy.dialects.postgresql import JSONB
        from sqlalchemy import JSON

        mapper = inspect(DetectionEvent)
        detail_column = mapper.columns.get('detail')
        assert detail_column is not None
        # SQLite uses JSON, PostgreSQL uses JSONB
        assert isinstance(detail_column.type, (JSON, JSONB)) or str(detail_column.type) == 'JSON'


class TestMalfunctionEventDetailModel:
    """Phase 2.3: MalfunctionEvent.detail column tests"""

    def test_malfunction_event_has_detail_column(self):
        """MalfunctionEvent model should have detail column"""
        from app.models.event import MalfunctionEvent

        # Check that detail column exists
        assert hasattr(MalfunctionEvent, 'detail')

    def test_malfunction_event_detail_nullable(self):
        """MalfunctionEvent.detail column should be nullable"""
        from app.models.event import MalfunctionEvent
        from sqlalchemy import inspect

        mapper = inspect(MalfunctionEvent)
        detail_column = mapper.columns.get('detail')
        assert detail_column is not None
        assert detail_column.nullable is True

    def test_malfunction_event_detail_jsonb_type(self):
        """MalfunctionEvent.detail column should be JSON type"""
        from app.models.event import MalfunctionEvent
        from sqlalchemy import inspect
        from sqlalchemy.dialects.postgresql import JSONB
        from sqlalchemy import JSON

        mapper = inspect(MalfunctionEvent)
        detail_column = mapper.columns.get('detail')
        assert detail_column is not None
        # SQLite uses JSON, PostgreSQL uses JSONB
        assert isinstance(detail_column.type, (JSON, JSONB)) or str(detail_column.type) == 'JSON'


# ===== Phase 3: API Create/Response Schema Tests =====

class TestDetectionEventCreateDetail:
    """Phase 3.1: DetectionEventCreate.detail field tests"""

    def test_detection_event_create_has_detail_field(self):
        """DetectionEventCreate should have optional detail field"""
        from app.schemas.event import DetectionEventCreate

        # Without detail
        create = DetectionEventCreate(
            type_event="Intrusion",
            device_id=1,
            result="PIR_SENSOR"
        )
        assert create.detail is None

    def test_detection_event_create_with_detail(self):
        """DetectionEventCreate should accept detail dict"""
        from app.schemas.event import DetectionEventCreate

        detail_data = {
            "result": "AI_PERSON",
            "signal": 0,
            "thumbnail": "http://192.168.1.50:8080/events/12345/thumb.jpg",
            "objects": [{"label": "person", "confidence": 0.92, "bbox": [100, 200, 150, 300]}],
            "model": "yolov8n",
            "inference_ms": 45
        }
        create = DetectionEventCreate(
            type_event="Intrusion",
            device_id=1,
            result="AI_PERSON",
            detail=detail_data
        )
        assert create.detail == detail_data


class TestDetectionEventResponseDetail:
    """Phase 3.3: DetectionEventResponse.detail field tests"""

    def test_detection_event_response_has_detail_field(self):
        """DetectionEventResponse should have optional detail field"""
        from app.schemas.event import DetectionEventResponse
        from datetime import datetime

        now = datetime.now()
        # Without detail
        response = DetectionEventResponse(
            id=1,
            type_event="Intrusion",
            action_reported="False",
            result="PIR_SENSOR",
            device=None,
            device_description="Test Device",
            created_at=now,
            updated_at=now
        )
        assert response.detail is None

    def test_detection_event_response_with_detail(self):
        """DetectionEventResponse should include detail dict (PRD_Event_Detail_JsonB.md v1.0)"""
        from app.schemas.event import DetectionEventResponse
        from datetime import datetime

        now = datetime.now()
        detail_data = {
            "result": "AI_PERSON",
            "signal": 0,
            "thumbnail": "http://192.168.1.50:8080/events/12345/thumb.jpg",
            "objects": [{"label": "person", "confidence": 0.92, "bbox": [100, 200, 150, 300]}],
            "model": "yolov8n",
            "inference_ms": 45
        }
        response = DetectionEventResponse(
            id=1,
            type_event="Intrusion",
            action_reported="False",
            result="AI_DETECT",
            device=None,
            device_description="Test Device",
            created_at=now,
            updated_at=now,
            detail=detail_data
        )
        assert response.detail == detail_data


class TestMalfunctionEventCreateDetail:
    """Phase 3.5: MalfunctionEventCreate.detail field tests"""

    def test_malfunction_event_create_has_detail_field(self):
        """MalfunctionEventCreate should have optional detail field"""
        from app.schemas.event import MalfunctionEventCreate

        # Without detail
        create = MalfunctionEventCreate(
            type_event="Fault",
            device_id=1,
            reason="FAULT_CONTROLLER",
            first_start=0,
            first_end=0,
            second_start=0,
            second_end=0
        )
        assert create.detail is None

    def test_malfunction_event_create_with_detail(self):
        """MalfunctionEventCreate should accept detail dict"""
        from app.schemas.event import MalfunctionEventCreate

        detail_data = {
            "reason": "CABLE_CUT",
            "first_start": 5,
            "first_end": 10,
            "second_start": 0,
            "second_end": 0
        }
        create = MalfunctionEventCreate(
            type_event="Fault",
            device_id=1,
            reason="FAULT_CONTROLLER",
            first_start=0,
            first_end=0,
            second_start=0,
            second_end=0,
            detail=detail_data
        )
        assert create.detail == detail_data


class TestMalfunctionEventResponseDetail:
    """Phase 3.7: MalfunctionEventResponse.detail field tests"""

    def test_malfunction_event_response_has_detail_field(self):
        """MalfunctionEventResponse should have optional detail field"""
        from app.schemas.event import MalfunctionEventResponse
        from datetime import datetime

        now = datetime.now()
        response = MalfunctionEventResponse(
            id=1,
            type_event="Fault",
            action_reported="False",
            reason="FAULT_CONTROLLER",
            first_start=0,
            first_end=0,
            second_start=0,
            second_end=0,
            device=None,
            device_description="Test Device",
            created_at=now,
            updated_at=now
        )
        assert response.detail is None

    def test_malfunction_event_response_with_detail(self):
        """MalfunctionEventResponse should include detail dict"""
        from app.schemas.event import MalfunctionEventResponse
        from datetime import datetime

        now = datetime.now()
        detail_data = {
            "reason": "CABLE_CUT",
            "first_start": 5,
            "first_end": 10,
            "second_start": 0,
            "second_end": 0
        }
        response = MalfunctionEventResponse(
            id=1,
            type_event="Fault",
            action_reported="False",
            reason="FAULT_CONTROLLER",
            first_start=0,
            first_end=0,
            second_start=0,
            second_end=0,
            device=None,
            device_description="Test Device",
            created_at=now,
            updated_at=now,
            detail=detail_data
        )
        assert response.detail == detail_data


# ===== Phase 4: API Router Integration Tests =====

class TestDetectionEventAPIDetail:
    """Phase 4.1-4.6: Detection Event API with detail tests"""

    def test_detection_post_with_detail(self, client, sample_sensor):
        """POST /detection should accept and store detail (PRD_Event_Detail_JsonB.md v1.0)"""
        detail_data = {
            "result": "AI_PERSON",
            "signal": 0,
            "thumbnail": "http://192.168.1.50:8080/events/12345/thumb.jpg",
            "objects": [{"label": "person", "confidence": 0.92, "bbox": [100, 200, 150, 300]}],
            "model": "yolov8n",
            "inference_ms": 45
        }
        response = client.post("/api/events/detections", json={
            "type_event": "Intrusion",
            "device_id": sample_sensor.id,
            "result": "AI_DETECT",
            "detail": detail_data
        })
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["detail"] == detail_data

    def test_detection_post_without_detail(self, client, sample_sensor):
        """POST /detection should work without detail"""
        response = client.post("/api/events/detections", json={
            "type_event": "Intrusion",
            "device_id": sample_sensor.id,
            "result": "PIR_SENSOR"
        })
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["detail"] is None

    def test_detection_get_includes_detail(self, client, sample_sensor):
        """GET /detection/{id} should include detail"""
        # First create with detail
        detail_data = {
            "thumbnail": "http://192.168.1.50:8080/events/12346/thumb.jpg",
            "signal": 1500
        }
        post_response = client.post("/api/events/detections", json={
            "type_event": "Intrusion",
            "device_id": sample_sensor.id,
            "result": "THERMAL_SENSOR",
            "detail": detail_data
        })
        event_id = post_response.json()["data"]["id"]

        # Then get and check detail
        get_response = client.get(f"/api/events/detections/{event_id}")
        assert get_response.status_code == 200
        data = get_response.json()["data"]
        assert data["detail"] == detail_data

    def test_detection_patch_with_detail(self, client, sample_sensor):
        """PATCH /detection/{id} should update detail"""
        # First create without detail
        post_response = client.post("/api/events/detections", json={
            "type_event": "Intrusion",
            "device_id": sample_sensor.id,
            "result": "PIR_SENSOR"
        })
        assert post_response.status_code == 201
        event_id = post_response.json()["data"]["id"]
        assert post_response.json()["data"]["detail"] is None

        # Now update with detail
        new_detail = {
            "thumbnail": "http://192.168.1.50:8080/events/12347/thumb.jpg",
            "signal": 2000,
            "model": "updated_model"
        }
        patch_response = client.patch(f"/api/events/detections/{event_id}", json={
            "detail": new_detail
        })
        assert patch_response.status_code == 200
        data = patch_response.json()["data"]
        assert data["detail"] == new_detail

    def test_detection_patch_detail_to_null(self, client, sample_sensor):
        """PATCH /detection/{id} should allow setting detail to null"""
        # First create with detail
        initial_detail = {
            "thumbnail": "http://example.com/thumb.jpg",
            "signal": 100
        }
        post_response = client.post("/api/events/detections", json={
            "type_event": "Intrusion",
            "device_id": sample_sensor.id,
            "result": "PIR_SENSOR",
            "detail": initial_detail
        })
        assert post_response.status_code == 201
        event_id = post_response.json()["data"]["id"]

        # Now update detail to null
        patch_response = client.patch(f"/api/events/detections/{event_id}", json={
            "detail": None
        })
        assert patch_response.status_code == 200
        data = patch_response.json()["data"]
        assert data["detail"] is None


class TestMalfunctionEventAPIDetail:
    """Phase 4.7-4.12: Malfunction Event API with detail tests"""

    def test_malfunction_post_with_detail(self, client, sample_sensor):
        """POST /malfunction should accept and store detail"""
        detail_data = {
            "reason": "CABLE_CUT",
            "first_start": 5,
            "first_end": 10,
            "second_start": 0,
            "second_end": 0
        }
        response = client.post("/api/events/malfunctions", json={
            "type_event": "Fault",
            "device_id": sample_sensor.id,
            "reason": "FAULT_CONTROLLER",
            "first_start": 0,
            "first_end": 0,
            "second_start": 0,
            "second_end": 0,
            "detail": detail_data
        })
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["detail"] == detail_data

    def test_malfunction_post_without_detail(self, client, sample_sensor):
        """POST /malfunction should work without detail"""
        response = client.post("/api/events/malfunctions", json={
            "type_event": "Fault",
            "device_id": sample_sensor.id,
            "reason": "FAULT_CONTROLLER",
            "first_start": 0,
            "first_end": 0,
            "second_start": 0,
            "second_end": 0
        })
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["detail"] is None

    def test_malfunction_get_includes_detail(self, client, sample_sensor):
        """GET /malfunction/{id} should include detail"""
        # First create with detail
        detail_data = {
            "reason": "CABLE_CUT",
            "first_start": 15,
            "first_end": 20
        }
        post_response = client.post("/api/events/malfunctions", json={
            "type_event": "Fault",
            "device_id": sample_sensor.id,
            "reason": "FAULT_FENCE",
            "first_start": 0,
            "first_end": 0,
            "second_start": 0,
            "second_end": 0,
            "detail": detail_data
        })
        event_id = post_response.json()["data"]["id"]

        # Then get and check detail
        get_response = client.get(f"/api/events/malfunctions/{event_id}")
        assert get_response.status_code == 200
        data = get_response.json()["data"]
        assert data["detail"] == detail_data

    def test_malfunction_patch_with_detail(self, client, sample_sensor):
        """PATCH /malfunction/{id} should update detail"""
        # First create without detail
        post_response = client.post("/api/events/malfunctions", json={
            "type_event": "Fault",
            "device_id": sample_sensor.id,
            "reason": "FAULT_CONTROLLER",
            "first_start": 0,
            "first_end": 0,
            "second_start": 0,
            "second_end": 0
        })
        assert post_response.status_code == 201
        event_id = post_response.json()["data"]["id"]
        assert post_response.json()["data"]["detail"] is None

        # Now update with detail
        new_detail = {
            "reason": "CABLE_CUT",
            "first_start": 25,
            "first_end": 30
        }
        patch_response = client.patch(f"/api/events/malfunctions/{event_id}", json={
            "detail": new_detail
        })
        assert patch_response.status_code == 200
        data = patch_response.json()["data"]
        assert data["detail"] == new_detail

    def test_malfunction_patch_detail_to_null(self, client, sample_sensor):
        """PATCH /malfunction/{id} should allow setting detail to null"""
        # First create with detail
        initial_detail = {
            "reason": "CABLE_CUT",
            "first_start": 5
        }
        post_response = client.post("/api/events/malfunctions", json={
            "type_event": "Fault",
            "device_id": sample_sensor.id,
            "reason": "FAULT_CONTROLLER",
            "first_start": 0,
            "first_end": 0,
            "second_start": 0,
            "second_end": 0,
            "detail": initial_detail
        })
        assert post_response.status_code == 201
        event_id = post_response.json()["data"]["id"]

        # Now update detail to null
        patch_response = client.patch(f"/api/events/malfunctions/{event_id}", json={
            "detail": None
        })
        assert patch_response.status_code == 200
        data = patch_response.json()["data"]
        assert data["detail"] is None


@pytest.fixture
def sample_sensor(test_db, test_controller):
    """Create sample sensor for testing (uses test_controller from conftest.py)"""
    from app.models.device import Sensor
    from app.utils.enums import EnumDeviceType, EnumDeviceStatus

    sensor = Sensor(
        number_device=100,
        group_device=1,
        name_device="Test Sensor for Detail",
        type_device=EnumDeviceType.PIR,
        status=EnumDeviceStatus.ACTIVATED,
        controller_id=test_controller.id
    )
    test_db.add(sensor)
    test_db.commit()
    test_db.refresh(sensor)
    return sensor
