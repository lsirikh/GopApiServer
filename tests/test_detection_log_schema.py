"""
Test: Detection Log 스키마 검증
PRD: PRD_DetectionLog_API.md v1.0
"""
from pydantic import BaseModel
from typing import get_type_hints, Optional
from datetime import datetime


class TestActionNestedSchema:
    """1.1: ActionNested 스키마 필드 검증"""

    def test_action_nested_has_required_fields(self):
        """ActionNested should have id, content, user, created_at, updated_at fields"""
        from app.schemas.event import ActionNested

        fields = ActionNested.model_fields
        assert "id" in fields, "ActionNested should have 'id' field"
        assert "content" in fields, "ActionNested should have 'content' field"
        assert "user" in fields, "ActionNested should have 'user' field"
        assert "created_at" in fields, "ActionNested should have 'created_at' field"
        assert "updated_at" in fields, "ActionNested should have 'updated_at' field"

    def test_action_nested_has_no_from_event(self):
        """ActionNested should NOT have from_event field (avoid circular reference)"""
        from app.schemas.event import ActionNested

        fields = ActionNested.model_fields
        assert "from_event" not in fields, "ActionNested should NOT have 'from_event' field"
        assert "from_event_id" not in fields, "ActionNested should NOT have 'from_event_id' field"

    def test_action_nested_functional(self):
        """ActionNested should be instantiable with valid data"""
        from app.schemas.event import ActionNested

        now = datetime.now()
        action = ActionNested(
            id=1,
            content="침입 확인 완료",
            user="operator1",
            created_at=now,
            updated_at=now
        )
        assert action.id == 1
        assert action.content == "침입 확인 완료"
        assert action.user == "operator1"


class TestDetectionLogResponseSchema:
    """1.2: DetectionLogResponse 스키마 필드 검증"""

    def test_detection_log_response_has_detection_fields(self):
        """DetectionLogResponse should have all DetectionEventResponse fields"""
        from app.schemas.event import DetectionLogResponse

        fields = DetectionLogResponse.model_fields
        # DetectionEventResponse 기본 필드
        assert "id" in fields
        assert "type_event" in fields
        assert "action_reported" in fields
        assert "result" in fields
        assert "device" in fields
        assert "device_description" in fields
        assert "detail" in fields
        assert "created_at" in fields
        assert "updated_at" in fields

    def test_detection_log_response_has_action_field(self):
        """DetectionLogResponse should have 'action' field (ActionNested)"""
        from app.schemas.event import DetectionLogResponse

        fields = DetectionLogResponse.model_fields
        assert "action" in fields, "DetectionLogResponse should have 'action' field"

    def test_detection_log_response_action_is_optional(self):
        """1.3: DetectionLogResponse.action should be Optional (null when no action)"""
        from app.schemas.event import DetectionLogResponse, ActionNested
        from datetime import datetime

        # action=None 허용 확인
        log = DetectionLogResponse(
            id=1,
            type_event="Intrusion",
            action_reported="False",
            result="PIR_SENSOR",
            device=None,
            device_description=None,
            detail=None,
            action=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        assert log.action is None

    def test_detection_log_response_action_with_data(self):
        """DetectionLogResponse.action should accept ActionNested"""
        from app.schemas.event import DetectionLogResponse, ActionNested
        from datetime import datetime

        now = datetime.now()
        action = ActionNested(
            id=10,
            content="현장 확인 완료",
            user="operator_kim",
            created_at=now,
            updated_at=now
        )

        log = DetectionLogResponse(
            id=1,
            type_event="Intrusion",
            action_reported="True",
            result="PIR_SENSOR",
            device=None,
            device_description=None,
            detail=None,
            action=action,
            created_at=now,
            updated_at=now
        )
        assert log.action is not None
        assert log.action.id == 10
        assert log.action.content == "현장 확인 완료"
        assert log.action.user == "operator_kim"
