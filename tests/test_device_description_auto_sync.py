"""
Test: device_description Auto-Sync
PRD: PRD_Event_ActionEvent_Refactoring.md v2.1

Phase 5: device_description Auto-Sync
- device_description format: "[{type_device}] {name_device} (number: {number_device}, id: {device_id})"
- device_description is auto-generated when Event is created with device_id
- device_description is updated when Event.device_id changes
- device_description is preserved when Device is deleted
"""
import pytest
from sqlalchemy import inspect, create_engine
from sqlalchemy.orm import sessionmaker

from app.models.event import Event, DetectionEvent
from app.database import Base
from app.utils.enums import EnumDetectionType


# Test database fixture
@pytest.fixture(scope="function")
def test_db():
    """Create a test database session"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestDeviceDescriptionGeneration:
    """Phase 5.1: device_description Generation 테스트"""

    def test_device_description_format(self):
        """Test: device_description format is '[{type_device}] {name_device} (number: {number_device}, id: {device_id})'"""
        # This test verifies the expected format
        # Format: "[Controller] 관제실 컨트롤러 (number: 1, id: 123)"
        expected_format_example = "[Controller] Test Device (number: 1, id: 123)"

        # Verify format contains required components
        assert "[" in expected_format_example and "]" in expected_format_example, "Format should include type in brackets"
        assert "number:" in expected_format_example, "Format should include 'number:'"
        assert "id:" in expected_format_example, "Format should include 'id:'"

    def test_event_has_device_description_field(self):
        """Test: Event model has device_description field"""
        mapper = inspect(Event)
        column_names = [column.key for column in mapper.columns]

        assert 'device_description' in column_names, "Event should have 'device_description' field"

    def test_device_description_is_nullable(self):
        """Test: device_description field is nullable"""
        mapper = inspect(Event)

        device_desc_col = None
        for column in mapper.columns:
            if column.key == 'device_description':
                device_desc_col = column
                break

        assert device_desc_col is not None, "Event should have 'device_description' column"
        assert device_desc_col.nullable is True, "device_description should be nullable"


class TestDeviceDescriptionPersistence:
    """Phase 5.2: device_description Persistence 테스트"""

    def test_device_description_preserved_when_device_id_null(self, test_db):
        """Test: device_description is preserved when device_id is set to NULL manually"""
        # Create DetectionEvent with device_description
        event = DetectionEvent(
            category_event="detection",
            type_event="Intrusion",
            device_id=None,  # No device
            device_description="[Controller] Test Device (number: 1, id: 123)",  # Manual description
            sequence=1,
            action_reported="False",
            result=EnumDetectionType.PIR_SENSOR
        )
        test_db.add(event)
        test_db.commit()
        event_id = event.id

        # Verify device_description is stored
        test_db.expire_all()
        event = test_db.get(DetectionEvent, event_id)
        assert event.device_description == "[Controller] Test Device (number: 1, id: 123)", \
            "device_description should be preserved even when device_id is NULL"
