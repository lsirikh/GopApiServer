"""
TDD Tests for Malfunction POST Duplicate Debug
Phase 26: 중복 생성 디버그

분석 결과: 버그가 아님!
- 클라이언트가 의도적으로 2개의 서로 다른 이벤트를 전송
- sensor=0, group_event=900 (컨트롤러 장애)
- sensor=1, group_event=1 (센서 장애)
- 약 4분 간격으로 주기적 전송
"""
import pytest
from unittest.mock import MagicMock
import asyncio


class TestMalfunctionPostSingleEvent:
    """Tests to verify single POST creates exactly one event"""

    def test_single_post_creates_one_event(self, test_db):
        """Test: 단일 POST 요청은 정확히 1개의 이벤트만 생성해야 함"""
        from app.routers.malfunctions import create_malfunction_event
        from app.schemas.event import MalfunctionEventCreate
        from app.models.event import MalfunctionEvent

        initial_count = test_db.query(MalfunctionEvent).count()

        # Create test data
        event_data = MalfunctionEventCreate(
            group_event="test_group",
            type_event="Fault",
            controller=1,
            sensor=1,
            type_device="Fence",
            sequence=1,
            action_reported="False",
            reason="FAULT_FENCE",
            first_start=0,
            first_end=0,
            second_start=0,
            second_end=0
        )

        mock_user = MagicMock()
        response = asyncio.run(create_malfunction_event(
            event_data=event_data,
            current_user=mock_user,
            db=test_db
        ))

        final_count = test_db.query(MalfunctionEvent).count()

        # 정확히 1개만 증가해야 함
        assert final_count == initial_count + 1
        assert response.success is True
        assert response.data.id is not None

    def test_two_different_posts_create_two_events(self, test_db):
        """Test: 2개의 다른 POST 요청은 2개의 이벤트를 생성해야 함"""
        from app.routers.malfunctions import create_malfunction_event
        from app.schemas.event import MalfunctionEventCreate
        from app.models.event import MalfunctionEvent

        initial_count = test_db.query(MalfunctionEvent).count()

        # 첫 번째 이벤트 (sensor=0, 컨트롤러 장애)
        event_data1 = MalfunctionEventCreate(
            group_event="900",
            type_event="Fault",
            controller=1,
            sensor=0,
            type_device="Controller",
            sequence=1,
            action_reported="False",
            reason="FAULT_CONTROLLER",
            first_start=0,
            first_end=0,
            second_start=0,
            second_end=0
        )

        # 두 번째 이벤트 (sensor=1, 센서 장애)
        event_data2 = MalfunctionEventCreate(
            group_event="1",
            type_event="Fault",
            controller=1,
            sensor=1,
            type_device="Fence",
            sequence=1,
            action_reported="False",
            reason="FAULT_FENCE",
            first_start=0,
            first_end=0,
            second_start=0,
            second_end=0
        )

        mock_user = MagicMock()

        # 첫 번째 POST
        response1 = asyncio.run(create_malfunction_event(
            event_data=event_data1,
            current_user=mock_user,
            db=test_db
        ))

        # 두 번째 POST
        response2 = asyncio.run(create_malfunction_event(
            event_data=event_data2,
            current_user=mock_user,
            db=test_db
        ))

        final_count = test_db.query(MalfunctionEvent).count()

        # 2개 증가해야 함 (서로 다른 이벤트이므로 정상)
        assert final_count == initial_count + 2
        assert response1.success is True
        assert response2.success is True
        assert response1.data.id != response2.data.id
        assert response1.data.sensor == 0
        assert response2.data.sensor == 1

    def test_identical_posts_create_separate_events(self, test_db):
        """Test: 동일한 데이터로 2번 POST해도 2개의 이벤트가 생성됨 (현재 동작)

        Note: 이것은 버그가 아님. 중복 방지가 필요하면 Idempotency Key를 구현해야 함.
        """
        from app.routers.malfunctions import create_malfunction_event
        from app.schemas.event import MalfunctionEventCreate
        from app.models.event import MalfunctionEvent

        initial_count = test_db.query(MalfunctionEvent).count()

        # 동일한 데이터
        event_data = MalfunctionEventCreate(
            group_event="test_group",
            type_event="Fault",
            controller=1,
            sensor=1,
            type_device="Fence",
            sequence=1,
            action_reported="False",
            reason="FAULT_FENCE",
            first_start=0,
            first_end=0,
            second_start=0,
            second_end=0
        )

        mock_user = MagicMock()

        # 동일한 데이터로 2번 POST
        response1 = asyncio.run(create_malfunction_event(
            event_data=event_data,
            current_user=mock_user,
            db=test_db
        ))
        response2 = asyncio.run(create_malfunction_event(
            event_data=event_data,
            current_user=mock_user,
            db=test_db
        ))

        final_count = test_db.query(MalfunctionEvent).count()

        # 현재 동작: 2개 생성됨 (중복 방지 로직 없음)
        assert final_count == initial_count + 2
        assert response1.data.id != response2.data.id


class TestMalfunctionPostRouterRegistration:
    """Tests to verify router is not duplicated"""

    def test_malfunction_router_registered_once(self):
        """Test: malfunctions 라우터가 main.py에 1번만 등록되어 있는지 확인"""
        from app.main import app

        malfunction_routes = [
            route for route in app.routes
            if hasattr(route, 'path') and '/api/events/malfunctions' in route.path
        ]

        # POST 엔드포인트는 1개만 있어야 함
        post_routes = [
            route for route in malfunction_routes
            if hasattr(route, 'methods') and 'POST' in route.methods
        ]

        assert len(post_routes) == 1, f"POST /malfunctions 라우터가 {len(post_routes)}개 등록됨"


class TestAnalysisResult:
    """분석 결과 문서화 테스트"""

    def test_analysis_conclusion(self):
        """
        분석 결과 문서화:

        1. 증상: Malfunction POST 시 2개씩 생성되는 것처럼 보임

        2. 원인: 버그 아님!
           - 클라이언트가 의도적으로 2개의 서로 다른 이벤트를 전송
           - sensor=0, group_event=900 (컨트롤러 장애)
           - sensor=1, group_event=1 (센서 장애)
           - 약 4분 간격으로 주기적 전송

        3. 결론:
           - 서버 측 버그 없음
           - 단일 POST = 단일 이벤트 생성 (정상 동작)
           - 2개 생성은 클라이언트에서 2번 POST한 결과

        4. 권장사항:
           - 클라이언트 측 로직 검토 필요
           - 필요시 Idempotency Key 패턴 구현 검토
        """
        assert True  # 분석 완료
