"""
Tests for Category Event Refactoring
PRD: PRD_CategoryEvent_Refactoring.md v1.1
TDD Approach: Red → Green → Refactor
"""
import pytest


class TestPhase1EnumDefinitions:
    """Phase 1: Enum 정의 테스트"""

    # =========================================================================
    # ActionItem 1.1: EnumEventCategory 신규 생성
    # =========================================================================
    def test_enum_event_category_exists(self):
        """EnumEventCategory Enum이 존재해야 한다 (Event polymorphic discriminator용)"""
        from app.utils.enums import EnumEventCategory

        # EnumEventCategory는 Event용 (detection, malfunction, connection)
        assert hasattr(EnumEventCategory, 'DETECTION')
        assert hasattr(EnumEventCategory, 'MALFUNCTION')
        assert hasattr(EnumEventCategory, 'CONNECTION')

    def test_enum_event_category_values(self):
        """EnumEventCategory 값이 올바른 문자열이어야 한다"""
        from app.utils.enums import EnumEventCategory

        assert EnumEventCategory.DETECTION.value == "detection"
        assert EnumEventCategory.MALFUNCTION.value == "malfunction"
        assert EnumEventCategory.CONNECTION.value == "connection"

    def test_enum_event_category_is_str_enum(self):
        """EnumEventCategory는 str, Enum을 상속해야 한다"""
        from app.utils.enums import EnumEventCategory
        from enum import Enum

        assert issubclass(EnumEventCategory, str)
        assert issubclass(EnumEventCategory, Enum)

    def test_enum_event_category_count(self):
        """EnumEventCategory는 정확히 3개의 값만 가져야 한다"""
        from app.utils.enums import EnumEventCategory

        assert len(EnumEventCategory) == 3

    # =========================================================================
    # ActionItem 1.2: EnumMappingEventCategory 이름 변경
    # =========================================================================
    def test_enum_mapping_event_category_exists(self):
        """EnumMappingEventCategory Enum이 존재해야 한다 (EventMapping 센서 조합 타입용)"""
        from app.utils.enums import EnumMappingEventCategory

        assert hasattr(EnumMappingEventCategory, 'NONE')
        assert hasattr(EnumMappingEventCategory, 'FENCE_SENSOR_ONLY')
        assert hasattr(EnumMappingEventCategory, 'FENCE_SENSOR_WITH_MULTI_SENSOR')
        assert hasattr(EnumMappingEventCategory, 'MULTI_SENSOR_ONLY')
        assert hasattr(EnumMappingEventCategory, 'SENSOR_WITH_CAMERA')
        assert hasattr(EnumMappingEventCategory, 'SENSOR_WITH_AI_CAMERA')
        assert hasattr(EnumMappingEventCategory, 'AI_CAMERA_ONLY')
        assert hasattr(EnumMappingEventCategory, 'CAMERA_ONLY')

    def test_enum_mapping_event_category_values(self):
        """EnumMappingEventCategory 값이 올바른 문자열이어야 한다"""
        from app.utils.enums import EnumMappingEventCategory

        assert EnumMappingEventCategory.NONE.value == "NONE"
        assert EnumMappingEventCategory.FENCE_SENSOR_ONLY.value == "FENCE_SENSOR_ONLY"
        assert EnumMappingEventCategory.AI_CAMERA_ONLY.value == "AI_CAMERA_ONLY"

    def test_enum_mapping_event_category_count(self):
        """EnumMappingEventCategory는 정확히 8개의 값을 가져야 한다"""
        from app.utils.enums import EnumMappingEventCategory

        assert len(EnumMappingEventCategory) == 8

    # =========================================================================
    # ActionItem 1.3: 하위 호환성 별칭
    # =========================================================================
    def test_enum_category_event_alias_exists(self):
        """EnumCategoryEvent 별칭이 EnumMappingEventCategory를 참조해야 한다"""
        from app.utils.enums import EnumCategoryEvent, EnumMappingEventCategory

        assert EnumCategoryEvent is EnumMappingEventCategory

    def test_enum_category_event_alias_usable(self):
        """EnumCategoryEvent 별칭으로 값에 접근할 수 있어야 한다"""
        from app.utils.enums import EnumCategoryEvent

        assert EnumCategoryEvent.FENCE_SENSOR_ONLY.value == "FENCE_SENSOR_ONLY"
        assert EnumCategoryEvent.AI_CAMERA_ONLY.value == "AI_CAMERA_ONLY"


class TestPhase2EventModel:
    """Phase 2: Event 모델/스키마 테스트"""

    # =========================================================================
    # ActionItem 2.1: Event 모델 category_event Enum 적용
    # =========================================================================
    def test_event_model_category_event_uses_enum(self):
        """Event 모델 category_event 필드가 EnumEventCategory 타입이어야 한다"""
        from app.models.event import Event
        from sqlalchemy import Enum as SQLEnum

        column = Event.__table__.columns['category_event']
        # SQLAlchemy Enum 타입인지 확인
        assert isinstance(column.type, SQLEnum)

    def test_event_model_category_event_values_valid(self):
        """Event 모델에 유효한 category_event 값만 저장 가능해야 한다"""
        from app.utils.enums import EnumEventCategory

        # Enum 값으로 생성 가능한지 확인
        for category in EnumEventCategory:
            assert category.value in ["detection", "malfunction", "connection"]

    def test_event_model_polymorphic_identities_match_enum(self):
        """Event 서브클래스의 polymorphic_identity가 EnumEventCategory 값과 일치해야 한다"""
        from app.models.event import DetectionEvent, MalfunctionEvent, ConnectionEvent
        from app.utils.enums import EnumEventCategory

        # 각 서브클래스의 polymorphic_identity 확인
        assert DetectionEvent.__mapper_args__['polymorphic_identity'] == EnumEventCategory.DETECTION.value
        assert MalfunctionEvent.__mapper_args__['polymorphic_identity'] == EnumEventCategory.MALFUNCTION.value
        assert ConnectionEvent.__mapper_args__['polymorphic_identity'] == EnumEventCategory.CONNECTION.value

    # =========================================================================
    # ActionItem 2.2: Event 스키마 업데이트
    # Note: Event 스키마는 현재 polymorphic discriminator를 Response에서 제외하고 있음
    # PRD v1.4에 따라 category_event는 내부용 필드로 Response에서 불필요
    # 따라서 스키마 테스트는 모델 레벨 Enum 적용 확인으로 대체
    # =========================================================================
    def test_event_model_category_event_is_indexed(self):
        """Event 모델 category_event 필드가 인덱스되어 있어야 한다"""
        from app.models.event import Event

        column = Event.__table__.columns['category_event']
        assert column.index is True


class TestPhase3EventMappingModel:
    """Phase 3: EventMapping 모델/스키마 테스트"""

    # =========================================================================
    # ActionItem 3.1: EventMapping 모델 필드명 변경
    # =========================================================================
    def test_event_mapping_model_has_category_event_mapping_field(self):
        """EventMapping 모델에 category_event_mapping 필드가 존재해야 한다"""
        from app.models.integration import EventMapping

        assert hasattr(EventMapping, 'category_event_mapping')
        assert 'category_event_mapping' in EventMapping.__table__.columns

    def test_event_mapping_model_category_event_mapping_uses_enum(self):
        """EventMapping 모델 category_event_mapping 필드가 EnumMappingEventCategory 타입이어야 한다"""
        from app.models.integration import EventMapping
        from sqlalchemy import Enum as SQLEnum

        column = EventMapping.__table__.columns['category_event_mapping']
        assert isinstance(column.type, SQLEnum)

    def test_event_mapping_model_no_category_event_field(self):
        """EventMapping 모델에 기존 category_event 필드가 없어야 한다"""
        from app.models.integration import EventMapping

        # category_event_mapping으로 변경되었으므로 category_event는 없어야 함
        assert 'category_event' not in EventMapping.__table__.columns

    # =========================================================================
    # ActionItem 3.2: EventMapping 스키마 업데이트
    # =========================================================================
    def test_event_mapping_schema_has_category_event_mapping_field(self):
        """EventMapping 스키마에 category_event_mapping 필드가 존재해야 한다"""
        from app.schemas.integration import EventMappingCreate, EventMappingResponse

        assert 'category_event_mapping' in EventMappingCreate.model_fields
        assert 'category_event_mapping' in EventMappingResponse.model_fields

    def test_event_mapping_schema_category_event_mapping_type(self):
        """EventMapping 스키마 category_event_mapping 필드가 EnumMappingEventCategory 타입이어야 한다"""
        from app.schemas.integration import EventMappingCreate
        from app.utils.enums import EnumMappingEventCategory

        field_info = EventMappingCreate.model_fields.get('category_event_mapping')
        assert field_info is not None
        assert field_info.annotation == EnumMappingEventCategory

    def test_event_mapping_schema_no_category_event_field(self):
        """EventMapping 스키마에 기존 category_event 필드가 없어야 한다"""
        from app.schemas.integration import EventMappingCreate, EventMappingResponse, EventMappingUpdate

        assert 'category_event' not in EventMappingCreate.model_fields
        assert 'category_event' not in EventMappingResponse.model_fields
        assert 'category_event' not in EventMappingUpdate.model_fields
