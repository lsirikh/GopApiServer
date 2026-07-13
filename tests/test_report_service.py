"""
Tests for Report Service
TDD: Test First
PRD: PRD_Report_System.md Section 8
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
# Import all models to ensure SQLAlchemy mappers are registered
from app.models import *  # noqa
from app.models.report import ReportTemplate, ReportGeneration  # noqa


# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_report_service.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Setup test database once for the module"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create database session for each test"""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


class TestReportServiceClass:
    """Tests for ReportService class existence"""

    def test_report_service_class_exists(self):
        """ReportService 클래스가 존재하는지 확인"""
        from app.services.report_service import ReportService
        assert ReportService is not None

    def test_report_service_instantiation(self, db):
        """ReportService 인스턴스 생성 확인"""
        from app.services.report_service import ReportService
        service = ReportService(db)
        assert service is not None
        assert service.db == db


class TestDeviceStatistics:
    """Tests for ReportService.get_device_statistics()"""

    def test_get_device_statistics_returns_status_counts(self, db):
        """get_device_statistics()가 상태별 카운트 반환"""
        from app.services.report_service import ReportService
        service = ReportService(db)

        result = service.get_device_statistics()

        assert "status_counts" in result
        # Should have counts for device statuses
        assert isinstance(result["status_counts"], dict)

    def test_get_device_statistics_returns_type_counts(self, db):
        """get_device_statistics()가 유형별 카운트 반환"""
        from app.services.report_service import ReportService
        service = ReportService(db)

        result = service.get_device_statistics()

        assert "type_counts" in result
        # Should have counts for device types (categories)
        assert isinstance(result["type_counts"], dict)


class TestEventStatistics:
    """Tests for ReportService.get_event_statistics()"""

    def test_get_event_statistics_returns_event_type_counts(self, db):
        """get_event_statistics()가 Detection, Malfunction, Action 카운트 반환"""
        from app.services.report_service import ReportService
        service = ReportService(db)

        result = service.get_event_statistics()

        assert "event_type_counts" in result
        assert isinstance(result["event_type_counts"], dict)

    def test_get_event_statistics_excludes_connection(self, db):
        """get_event_statistics()가 Connection 이벤트를 제외"""
        from app.services.report_service import ReportService
        service = ReportService(db)

        result = service.get_event_statistics()

        # Connection should not be in the counts
        assert "Connection" not in result.get("event_type_counts", {})

    def test_get_event_statistics_returns_daily_trend(self, db):
        """get_event_statistics()가 일별 추세 데이터 반환"""
        from app.services.report_service import ReportService
        service = ReportService(db)

        result = service.get_event_statistics()

        assert "daily_trend" in result
        assert isinstance(result["daily_trend"], list)


class TestSystemStatistics:
    """Tests for ReportService.get_system_statistics()"""

    def test_get_system_statistics_returns_severity_counts(self, db):
        """get_system_statistics()가 심각도별 카운트 반환"""
        from app.services.report_service import ReportService
        service = ReportService(db)

        result = service.get_system_statistics()

        assert "severity_counts" in result
        assert isinstance(result["severity_counts"], dict)

    def test_get_system_statistics_returns_daily_trend(self, db):
        """get_system_statistics()가 일별 추세 데이터 반환"""
        from app.services.report_service import ReportService
        service = ReportService(db)

        result = service.get_system_statistics()

        assert "daily_trend" in result
        assert isinstance(result["daily_trend"], list)


class TestPreviewData:
    """Tests for ReportService.get_preview_data()"""

    def test_get_preview_data_returns_sections(self, db):
        """get_preview_data()가 sections 배열 반환"""
        from app.services.report_service import ReportService
        service = ReportService(db)

        result = service.get_preview_data()

        assert "sections" in result
        assert isinstance(result["sections"], list)

    def test_get_preview_data_sections_have_charts_and_grids(self, db):
        """각 section에 charts와 grids 포함"""
        from app.services.report_service import ReportService
        service = ReportService(db)

        result = service.get_preview_data()

        # Check that sections exist and have expected structure
        for section in result["sections"]:
            assert "title" in section
            # Each section should have charts or grids (or both)
            assert "charts" in section or "grids" in section


# ============================================================
# Phase 3: User Statistics Service (PRD v1.4)
# ============================================================

class TestUserStatistics:
    """Tests for ReportService.get_user_statistics()"""

    def test_get_user_statistics_method_exists(self, db):
        """get_user_statistics() 메서드가 존재해야 함"""
        from app.services.report_service import ReportService
        service = ReportService(db)
        assert hasattr(service, 'get_user_statistics')

    def test_get_user_statistics_returns_role_counts(self, db):
        """get_user_statistics()가 역할별 분포 반환"""
        from app.services.report_service import ReportService
        service = ReportService(db)

        result = service.get_user_statistics()
        assert "role_counts" in result
        assert isinstance(result["role_counts"], dict)

    def test_get_user_statistics_returns_login_daily_trend(self, db):
        """get_user_statistics()가 일별 로그인 추이 반환"""
        from app.services.report_service import ReportService
        service = ReportService(db)

        result = service.get_user_statistics()
        assert "login_daily_trend" in result
        assert isinstance(result["login_daily_trend"], list)

    def test_get_user_statistics_returns_login_result_counts(self, db):
        """get_user_statistics()가 로그인 성공/실패 분포 반환"""
        from app.services.report_service import ReportService
        service = ReportService(db)

        result = service.get_user_statistics()
        assert "login_result_counts" in result
        assert isinstance(result["login_result_counts"], dict)


# ============================================================
# Phase 4: Grid Data Queries
# ============================================================

class TestDeviceGridData:
    """Tests for get_device_grid_data()"""

    def test_get_device_grid_data_returns_columns_and_rows(self, db):
        """get_device_grid_data()가 columns, rows, total_rows 반환"""
        from app.services.report_service import ReportService
        service = ReportService(db)

        result = service.get_device_grid_data()
        assert "columns" in result
        assert "rows" in result
        assert "total_rows" in result
        assert isinstance(result["columns"], list)
        assert isinstance(result["rows"], list)
        assert isinstance(result["total_rows"], int)


class TestEventGridData:
    """Tests for event grid data methods"""

    def test_get_detection_grid_data_returns_columns_and_rows(self, db):
        """get_detection_grid_data()가 columns, rows, total_rows 반환"""
        from app.services.report_service import ReportService
        service = ReportService(db)

        result = service.get_detection_grid_data()
        assert "columns" in result
        assert "rows" in result
        assert "total_rows" in result

    def test_get_malfunction_grid_data_returns_columns_and_rows(self, db):
        """get_malfunction_grid_data()가 columns, rows, total_rows 반환"""
        from app.services.report_service import ReportService
        service = ReportService(db)

        result = service.get_malfunction_grid_data()
        assert "columns" in result
        assert "rows" in result
        assert "total_rows" in result

    def test_get_action_grid_data_returns_columns_and_rows(self, db):
        """get_action_grid_data()가 columns, rows, total_rows 반환"""
        from app.services.report_service import ReportService
        service = ReportService(db)

        result = service.get_action_grid_data()
        assert "columns" in result
        assert "rows" in result
        assert "total_rows" in result


class TestSystemGridData:
    """Tests for system grid data methods"""

    def test_get_system_event_grid_data_returns_columns_and_rows(self, db):
        """get_system_event_grid_data()가 columns, rows, total_rows 반환"""
        from app.services.report_service import ReportService
        service = ReportService(db)

        result = service.get_system_event_grid_data()
        assert "columns" in result
        assert "rows" in result
        assert "total_rows" in result

    def test_get_config_grid_data_returns_columns_and_rows(self, db):
        """get_config_grid_data()가 columns, rows, total_rows 반환"""
        from app.services.report_service import ReportService
        service = ReportService(db)

        result = service.get_config_grid_data()
        assert "columns" in result
        assert "rows" in result
        assert "total_rows" in result

    def test_get_audit_grid_data_returns_columns_and_rows(self, db):
        """get_audit_grid_data()가 columns, rows, total_rows 반환"""
        from app.services.report_service import ReportService
        service = ReportService(db)

        result = service.get_audit_grid_data()
        assert "columns" in result
        assert "rows" in result
        assert "total_rows" in result


class TestUserGridData:
    """Tests for user grid data methods"""

    def test_get_user_grid_data_returns_columns_and_rows(self, db):
        """get_user_grid_data()가 columns, rows, total_rows 반환"""
        from app.services.report_service import ReportService
        service = ReportService(db)

        result = service.get_user_grid_data()
        assert "columns" in result
        assert "rows" in result
        assert "total_rows" in result

    def test_get_user_login_grid_data_returns_columns_and_rows(self, db):
        """get_user_login_grid_data()가 columns, rows, total_rows 반환"""
        from app.services.report_service import ReportService
        service = ReportService(db)

        result = service.get_user_login_grid_data()
        assert "columns" in result
        assert "rows" in result
        assert "total_rows" in result

    def test_get_user_session_grid_data_returns_columns_and_rows(self, db):
        """get_user_session_grid_data()가 columns, rows, total_rows 반환"""
        from app.services.report_service import ReportService
        service = ReportService(db)

        result = service.get_user_session_grid_data()
        assert "columns" in result
        assert "rows" in result
        assert "total_rows" in result


# ============================================================
# Phase 5: Structured Preview Data
# ============================================================

class TestStructuredPreviewData:
    """Tests for get_structured_preview_data()"""

    def test_get_structured_preview_data_returns_sections(self, db):
        """get_structured_preview_data()가 sections 리스트 반환"""
        from app.services.report_service import ReportService
        service = ReportService(db)

        result = service.get_structured_preview_data()
        assert "sections" in result
        assert isinstance(result["sections"], list)

    def test_sections_have_charts_with_chart_data_format(self, db):
        """sections의 charts가 ChartData 형식 (id, title, type, data.labels/values)"""
        from app.services.report_service import ReportService
        service = ReportService(db)

        result = service.get_structured_preview_data()
        for section in result["sections"]:
            if "charts" in section:
                for chart in section["charts"]:
                    assert "id" in chart
                    assert "title" in chart
                    assert "type" in chart
                    assert "data" in chart
                    assert "labels" in chart["data"]
                    assert "values" in chart["data"]

    def test_sections_have_grids_with_columns_rows(self, db):
        """sections의 grids가 columns/rows 형식"""
        from app.services.report_service import ReportService
        service = ReportService(db)

        result = service.get_structured_preview_data()
        for section in result["sections"]:
            if "grids" in section:
                for grid in section["grids"]:
                    assert "id" in grid
                    assert "title" in grid
                    assert "columns" in grid
                    assert "rows" in grid
                    assert "total_rows" in grid

    def test_user_section_included(self, db):
        """USER 섹션이 포함되어야 함 (11섹션 구조: user_charts + user_grids)"""
        from app.services.report_service import ReportService
        service = ReportService(db)

        result = service.get_structured_preview_data()
        section_names = [s["name"] for s in result["sections"]]
        assert "user_charts" in section_names
        assert "user_grids" in section_names


# ============================================================
# Phase 1: Detection Grid Bug Fix (PRD_Report_Preview_Debug BUG-1)
# ============================================================

class TestDetectionGridBugFix:
    """BUG-1: get_detection_grid_data()에서 e.type_detection 사용 → AttributeError"""

    def test_detection_grid_uses_result_field(self, db):
        """
        DetectionEvent 삽입 후 get_detection_grid_data() 호출 시
        result 값(예: THERMAL_SENSOR)이 행에 포함되어야 한다.
        RED: 현재 코드는 e.type_detection 접근 → AttributeError
        """
        from app.services.report_service import ReportService
        from app.models.event import DetectionEvent
        from app.utils.enums import EnumDetectionType, EnumEventCategory
        from datetime import datetime

        # 테스트 DetectionEvent 삽입
        event = DetectionEvent(
            category_event=EnumEventCategory.DETECTION,
            type_event="Intrusion",
            result=EnumDetectionType.THERMAL_SENSOR,
            action_reported="False",
        )
        db.add(event)
        db.commit()

        try:
            service = ReportService(db)
            result = service.get_detection_grid_data(days=30)

            # result 값이 행에 포함되어야 함
            assert result["total_rows"] >= 1
            # 탐지유형 컬럼에 "THERMAL_SENSOR" 값이 있어야 함
            found = False
            for row in result["rows"]:
                # 탐지유형은 컬럼 인덱스 2
                if "THERMAL_SENSOR" in str(row[2]):
                    found = True
                    break
            assert found, f"THERMAL_SENSOR not found in detection grid rows: {result['rows']}"
        finally:
            db.delete(event)
            db.commit()

    def test_detection_grid_has_mockup_columns(self, db):
        """
        탐지 이벤트 Grid 컬럼이 mockup과 일치해야 한다.
        mockup 컬럼: [ID, 일시, 탐지유형, 장비유형, 장비명, 조치보고일자, 조치자, 조치내용]
        RED: 현재 컬럼은 [ID, 일시, 탐지유형, 존, 장비ID]
        """
        from app.services.report_service import ReportService

        service = ReportService(db)
        result = service.get_detection_grid_data()

        expected_columns = ["ID", "일시", "탐지유형", "장비유형", "장비명",
                           "조치보고일자", "조치자", "조치내용"]
        assert result["columns"] == expected_columns, (
            f"Expected {expected_columns}, got {result['columns']}"
        )

    def test_detection_grid_includes_device_and_action_data(self, db):
        """
        탐지 이벤트에 연결된 Device와 ActionEvent 데이터가 행에 포함되어야 한다.
        """
        from app.services.report_service import ReportService
        from app.models.event import DetectionEvent, ActionEvent
        from app.models.device import Controller
        from app.utils.enums import (EnumDetectionType, EnumEventCategory,
                                      EnumDeviceCategory, EnumDeviceType)
        from datetime import datetime

        # Device 생성
        device = Controller(
            category_device=EnumDeviceCategory.CONTROLLER,
            type_device=EnumDeviceType.Controller,
            number_device=999,
            group_device=0,
            name_device="테스트 컨트롤러",
            ip_address="192.168.1.1",
            ip_port=8080,
        )
        db.add(device)
        db.flush()

        # DetectionEvent 생성 (Device 연결)
        event = DetectionEvent(
            category_event=EnumEventCategory.DETECTION,
            type_event="Intrusion",
            device_id=device.id,
            result=EnumDetectionType.PIR_SENSOR,
            action_reported="True",
        )
        db.add(event)
        db.flush()

        # ActionEvent 생성 (Event 연결)
        action = ActionEvent(
            from_event_id=event.id,
            content="조치 완료",
            user="admin",
        )
        db.add(action)
        db.commit()

        try:
            service = ReportService(db)
            result = service.get_detection_grid_data(days=30)

            # 해당 이벤트 행 찾기
            target_row = None
            for row in result["rows"]:
                if row[0] == event.id:
                    target_row = row
                    break

            assert target_row is not None, f"Event {event.id} not found in rows"
            # [ID, 일시, 탐지유형, 장비유형, 장비명, 조치보고일자, 조치자, 조치내용]
            assert target_row[2] == "PIR_SENSOR"        # 탐지유형
            assert "controller" in str(target_row[3]).lower()  # 장비유형 (category)
            assert target_row[4] == "테스트 컨트롤러"      # 장비명
            assert target_row[6] == "admin"              # 조치자
            assert target_row[7] == "조치 완료"           # 조치내용
        finally:
            db.delete(action)
            db.delete(event)
            db.delete(device)
            db.commit()


# ============================================================
# Phase 3: Event Statistics Category Grouping (PRD_Report_Preview_Debug BUG-4)
# ============================================================

class TestEventStatsCategoryGrouping:
    """BUG-4 + GAP-2: event_type_counts를 category 기준으로 변경"""

    def test_event_stats_groups_by_category(self, db):
        """
        Detection/Malfunction 이벤트 삽입 후 event_type_counts가
        category 기준으로 집계되어야 한다.
        기대 키: "detection", "malfunction", "action"
        RED: 현재는 type_event ("Intrusion", "Fault") 기준 집계
        """
        from app.services.report_service import ReportService
        from app.models.event import DetectionEvent, MalfunctionEvent, ActionEvent
        from app.utils.enums import (EnumDetectionType, EnumFaultType,
                                      EnumEventCategory)

        # Detection 2건
        d1 = DetectionEvent(
            category_event=EnumEventCategory.DETECTION,
            type_event="Intrusion",
            result=EnumDetectionType.THERMAL_SENSOR,
            action_reported="False",
        )
        d2 = DetectionEvent(
            category_event=EnumEventCategory.DETECTION,
            type_event="Intrusion",
            result=EnumDetectionType.PIR_SENSOR,
            action_reported="False",
        )
        # Malfunction 1건
        m1 = MalfunctionEvent(
            category_event=EnumEventCategory.MALFUNCTION,
            type_event="Fault",
            reason=EnumFaultType.FAULT_CONTROLLER,
            action_reported="False",
        )
        db.add_all([d1, d2, m1])
        db.flush()

        # Action 1건 (d1에 대한 조치)
        a1 = ActionEvent(
            from_event_id=d1.id,
            content="조치 완료",
            user="admin",
        )
        db.add(a1)
        db.commit()

        try:
            service = ReportService(db)
            result = service.get_event_statistics(days=30)
            counts = result["event_type_counts"]

            # category 기준 키가 존재해야 함
            assert "detection" in counts or "탐지(Detection)" in counts, \
                f"Expected detection category key, got: {counts}"
            assert "malfunction" in counts or "장애(Malfunction)" in counts, \
                f"Expected malfunction category key, got: {counts}"
            assert "action" in counts or "조치(Action)" in counts, \
                f"Expected action category key, got: {counts}"

            # type_event 키("Intrusion", "Fault")가 아닌 category 키여야 함
            assert "Intrusion" not in counts, \
                f"Should not group by type_event, got: {counts}"
        finally:
            db.delete(a1)
            db.delete(m1)
            db.delete(d2)
            db.delete(d1)
            db.commit()

    def test_event_trend_separated_by_category(self, db):
        """
        일별 이벤트 추이가 3개 datasets (탐지/장애/조치)로 분리되어야 한다.
        RED: 현재는 단일 합산 추이
        """
        from app.services.report_service import ReportService
        from app.models.event import DetectionEvent
        from app.utils.enums import EnumDetectionType, EnumEventCategory

        event = DetectionEvent(
            category_event=EnumEventCategory.DETECTION,
            type_event="Intrusion",
            result=EnumDetectionType.THERMAL_SENSOR,
            action_reported="False",
        )
        db.add(event)
        db.commit()

        try:
            service = ReportService(db)
            result = service.get_event_statistics(days=30)

            # daily_trend가 datasets 리스트를 포함해야 함
            assert "daily_trend" in result
            trend = result["daily_trend"]

            # datasets 형식이어야 함 (list of dicts with label/values)
            if isinstance(trend, list) and len(trend) > 0:
                if isinstance(trend[0], dict) and "label" in trend[0]:
                    # 새로운 형식: [{label, values}, ...]
                    labels = [ds["label"] for ds in trend]
                    assert len(labels) == 3, f"Expected 3 datasets, got {len(labels)}"
                else:
                    # 기존 합산 형식 → FAIL
                    assert False, (
                        f"daily_trend should be datasets format [{{'label':..,'values':..}}], "
                        f"got legacy format: {trend[:2]}"
                    )
        finally:
            db.delete(event)
            db.commit()


# ============================================================
# Phase 7: Service Restructure — 11 Sections (GAP-10)
# ============================================================

class TestStructured11Sections:
    """GAP-10: get_structured_preview_data() 5→11 섹션 구조 변경"""

    def test_structured_data_has_11_sections(self, db):
        """sections 리스트 길이 11 (RED: 현재 5)"""
        from app.services.report_service import ReportService
        service = ReportService(db)
        result = service.get_structured_preview_data()
        assert len(result["sections"]) == 11, (
            f"Expected 11 sections, got {len(result['sections'])}: "
            f"{[s['name'] for s in result['sections']]}"
        )

    def test_summary_section_has_category_data(self, db):
        """요약 섹션에 summary_data 포함"""
        from app.services.report_service import ReportService
        service = ReportService(db)
        result = service.get_structured_preview_data()
        summary = result["sections"][0]
        assert summary["name"] == "summary"
        assert "summary_data" in summary
        assert "device_categories" in summary["summary_data"]
        assert "event_counts" in summary["summary_data"]
        assert "server_status" in summary["summary_data"]

    def test_chart_sections_have_no_grids(self, db):
        """차트 섹션(인덱스 1~4)에 grids 비어있음"""
        from app.services.report_service import ReportService
        service = ReportService(db)
        result = service.get_structured_preview_data()
        # 섹션 인덱스 1~4 (2~5번 장비/이벤트/시스템/사용자 현황)
        for i in range(1, 5):
            section = result["sections"][i]
            assert section["grids"] == [], (
                f"Section {i} ({section['name']}) should have no grids, "
                f"got {len(section['grids'])} grids"
            )

    def test_grid_sections_have_no_charts(self, db):
        """그리드 섹션(인덱스 5~10)에 charts 비어있음"""
        from app.services.report_service import ReportService
        service = ReportService(db)
        result = service.get_structured_preview_data()
        # 섹션 인덱스 5~10 (6~11번 그리드 섹션)
        for i in range(5, 11):
            section = result["sections"][i]
            assert section["charts"] == [], (
                f"Section {i} ({section['name']}) should have no charts, "
                f"got {len(section['charts'])} charts"
            )

    def test_section_names_match_mockup(self, db):
        """섹션 이름이 mockup 구조와 일치"""
        from app.services.report_service import ReportService
        service = ReportService(db)
        result = service.get_structured_preview_data()
        names = [s["name"] for s in result["sections"]]
        expected = [
            "summary",           # 1. 요약
            "device_charts",     # 2. 장비 현황
            "event_charts",      # 3. 이벤트 현황
            "system_charts",     # 4. 시스템 현황
            "user_charts",       # 5. 사용자 현황
            "device_grid",       # 6. 장비 목록
            "event_grids",       # 7. 이벤트 상세
            "system_event_grid", # 8. 시스템 이벤트
            "config_grid",       # 9. 설정 변경 이력
            "audit_grid",        # 10. 감사 로그
            "user_grids",        # 11. 사용자 상세
        ]
        assert names == expected, f"Expected {expected}, got {names}"


# ============================================================
# Phase 6: Schema & Enum Serialization (GAP-16, GAP-17)
# ============================================================

class TestEnumSerialization:
    """GAP-16,17: Enum key 직렬화 확인"""

    def test_device_status_counts_use_string_keys(self, db):
        """
        status_counts 키가 Enum 객체가 아닌 문자열이어야 한다.
        """
        from app.services.report_service import ReportService
        from app.models.device import Controller
        from app.utils.enums import EnumDeviceCategory, EnumDeviceType, EnumDeviceStatus

        device = Controller(
            category_device=EnumDeviceCategory.CONTROLLER,
            type_device=EnumDeviceType.Controller,
            number_device=994, group_device=0,
            name_device="직렬화테스트",
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="10.0.0.3", ip_port=8080,
        )
        db.add(device)
        db.commit()

        try:
            service = ReportService(db)
            result = service.get_device_statistics()

            for key in result["status_counts"].keys():
                assert isinstance(key, str), (
                    f"status_counts key should be str, got {type(key)}: {key}"
                )
        finally:
            db.delete(device)
            db.commit()


class TestSchemaExtensions:
    """ChartData datasets 지원 + ReportSection summary_data"""

    def test_chart_data_supports_datasets(self):
        """ChartData에 datasets 필드 지원"""
        from app.schemas.report import ChartData

        # datasets 필드가 있어야 함
        data = ChartData(
            labels=["01-01", "01-02"],
            datasets=[{"label": "탐지", "values": [10, 20]}],
        )
        assert data.datasets is not None
        assert len(data.datasets) == 1

    def test_report_section_has_summary_data(self):
        """ReportSection에 summary_data optional 필드"""
        from app.schemas.report import ReportSection

        section = ReportSection(
            name="summary",
            title="요약",
            summary_data={"device_categories": [], "event_counts": {}, "server_status": []}
        )
        assert section.summary_data is not None
        assert "device_categories" in section.summary_data


# ============================================================
# Phase 5: Summary Data — Device/Server Category (GAP-1, GAP-3)
# ============================================================

class TestSummaryData:
    """GAP-1 + GAP-3: 장비 카테고리별 정상/전체, 서버 상태 요약"""

    def test_get_device_category_summary(self, db):
        """
        카테고리별 장비 {category, total, normal, status} 반환
        RED: 메서드가 아직 존재하지 않음
        """
        from app.services.report_service import ReportService
        from app.models.device import Controller
        from app.utils.enums import EnumDeviceCategory, EnumDeviceType, EnumDeviceStatus

        # 정상 장비 1대 + 오류 장비 1대
        d1 = Controller(
            category_device=EnumDeviceCategory.CONTROLLER,
            type_device=EnumDeviceType.Controller,
            number_device=996, group_device=0,
            name_device="정상 컨트롤러",
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="10.0.0.1", ip_port=8080,
        )
        d2 = Controller(
            category_device=EnumDeviceCategory.CONTROLLER,
            type_device=EnumDeviceType.Controller,
            number_device=995, group_device=0,
            name_device="오류 컨트롤러",
            status=EnumDeviceStatus.ERROR,
            ip_address="10.0.0.2", ip_port=8080,
        )
        db.add_all([d1, d2])
        db.commit()

        try:
            service = ReportService(db)
            result = service.get_device_category_summary()

            assert isinstance(result, list)
            # controller 카테고리 찾기
            controller_entry = None
            for entry in result:
                if entry["category"] == "controller":
                    controller_entry = entry
                    break

            assert controller_entry is not None, f"controller not found in {result}"
            assert controller_entry["total"] >= 2
            assert controller_entry["normal"] >= 1
            assert "status" in controller_entry  # "all-normal" or "has-issue"
            assert controller_entry["status"] == "has-issue"  # ERROR 장비가 있으므로
        finally:
            db.delete(d2)
            db.delete(d1)
            db.commit()

    def test_get_server_status_summary(self, db):
        """
        서버 카테고리별 {name, status, count} 반환
        RED: 메서드가 아직 존재하지 않음
        """
        from app.services.report_service import ReportService
        from app.models.server import ServerCategory, Server
        from app.utils.enums import EnumServerType, EnumServerStatus

        cat = ServerCategory(
            name="VMS 서버",
            type_server=EnumServerType.VMS,
            sort_order=1,
        )
        db.add(cat)
        db.flush()

        s1 = Server(
            category_id=cat.id,
            name="VMS-01",
            status=EnumServerStatus.NORMAL,
            ip_address="192.168.0.1",
            port=8080,
        )
        db.add(s1)
        db.commit()

        try:
            service = ReportService(db)
            result = service.get_server_status_summary()

            assert isinstance(result, list)
            vms_entry = None
            for entry in result:
                if "VMS" in entry["name"]:
                    vms_entry = entry
                    break

            assert vms_entry is not None, f"VMS not found in {result}"
            assert vms_entry["count"] >= 1
            assert vms_entry["status"] == "normal"
        finally:
            db.delete(s1)
            db.delete(cat)
            db.commit()


# ============================================================
# Phase 4: Device Grid Column Fix (PRD_Report_Preview_Debug GAP-7)
# ============================================================

class TestDeviceGridColumnFix:
    """GAP-7: 장비 Grid 컬럼 mockup 일치"""

    def test_device_grid_has_mockup_columns(self, db):
        """
        장비 Grid 컬럼이 mockup과 일치해야 한다.
        mockup: [ID, 장비명, 장비유형, 버전, 상태, 활성]
        RED: 현재 [ID, 유형, 이름, 상태, IP]
        """
        from app.services.report_service import ReportService

        service = ReportService(db)
        result = service.get_device_grid_data()

        expected_columns = ["ID", "장비명", "장비유형", "버전", "상태", "활성"]
        assert result["columns"] == expected_columns, (
            f"Expected {expected_columns}, got {result['columns']}"
        )

    def test_device_grid_row_includes_version_and_enable(self, db):
        """
        장비 행에 버전과 활성 필드가 포함되어야 한다.
        """
        from app.services.report_service import ReportService
        from app.models.device import Controller
        from app.utils.enums import EnumDeviceCategory, EnumDeviceType

        device = Controller(
            category_device=EnumDeviceCategory.CONTROLLER,
            type_device=EnumDeviceType.Controller,
            number_device=997,
            group_device=0,
            name_device="버전테스트",
            version="2.1.0",
            is_enable=True,
            ip_address="10.0.0.1",
            ip_port=9090,
        )
        db.add(device)
        db.commit()

        try:
            service = ReportService(db)
            result = service.get_device_grid_data()

            target_row = None
            for row in result["rows"]:
                if row[0] == device.id:
                    target_row = row
                    break

            assert target_row is not None
            # [ID, 장비명, 장비유형, 버전, 상태, 활성]
            assert target_row[1] == "버전테스트"          # 장비명
            assert "controller" in str(target_row[2]).lower() or "Controller" in str(target_row[2])
            assert target_row[3] == "2.1.0"              # 버전
            assert target_row[5] in [True, "True", "true"]  # 활성
        finally:
            db.delete(device)
            db.commit()


# ============================================================
# Phase 2: Malfunction Grid Bug Fix (PRD_Report_Preview_Debug BUG-2)
# ============================================================

class TestMalfunctionGridBugFix:
    """BUG-2: get_malfunction_grid_data()에서 e.type_fault 사용 → AttributeError"""

    def test_malfunction_grid_uses_reason_field(self, db):
        """
        MalfunctionEvent 삽입 후 get_malfunction_grid_data() 호출 시
        reason 값이 행에 포함되어야 한다.
        RED: 현재 코드는 e.type_fault 접근 → AttributeError
        """
        from app.services.report_service import ReportService
        from app.models.event import MalfunctionEvent
        from app.utils.enums import EnumFaultType, EnumEventCategory

        event = MalfunctionEvent(
            category_event=EnumEventCategory.MALFUNCTION,
            type_event="Fault",
            reason=EnumFaultType.FAULT_CONTROLLER,
            action_reported="False",
        )
        db.add(event)
        db.commit()

        try:
            service = ReportService(db)
            result = service.get_malfunction_grid_data(days=30)

            assert result["total_rows"] >= 1
            found = False
            for row in result["rows"]:
                if "FAULT_CONTROLLER" in str(row[2]):
                    found = True
                    break
            assert found, f"FAULT_CONTROLLER not found in malfunction grid rows"
        finally:
            db.delete(event)
            db.commit()

    def test_malfunction_grid_has_mockup_columns(self, db):
        """
        장애 이벤트 Grid 컬럼이 mockup과 일치해야 한다.
        mockup 컬럼: [ID, 일시, 장애유형, 장비유형, 장비명, 조치보고일자, 조치자, 조치내용]
        RED: 현재 컬럼은 [ID, 일시, 장애유형, 장비ID]
        """
        from app.services.report_service import ReportService

        service = ReportService(db)
        result = service.get_malfunction_grid_data()

        expected_columns = ["ID", "일시", "장애유형", "장비유형", "장비명",
                           "조치보고일자", "조치자", "조치내용"]
        assert result["columns"] == expected_columns

    def test_malfunction_grid_includes_device_and_action_data(self, db):
        """
        장애 이벤트에 연결된 Device와 ActionEvent 데이터가 행에 포함되어야 한다.
        """
        from app.services.report_service import ReportService
        from app.models.event import MalfunctionEvent, ActionEvent
        from app.models.device import Controller
        from app.utils.enums import (EnumFaultType, EnumEventCategory,
                                      EnumDeviceCategory, EnumDeviceType)

        # Controller 생성
        device = Controller(
            category_device=EnumDeviceCategory.CONTROLLER,
            type_device=EnumDeviceType.Controller,
            number_device=998,
            group_device=0,
            name_device="테스트 컨트롤러2",
            ip_address="192.168.1.2",
            ip_port=8080,
        )
        db.add(device)
        db.flush()

        event = MalfunctionEvent(
            category_event=EnumEventCategory.MALFUNCTION,
            type_event="Fault",
            device_id=device.id,
            reason=EnumFaultType.FAULT_FENCE,
            action_reported="True",
        )
        db.add(event)
        db.flush()

        action = ActionEvent(
            from_event_id=event.id,
            content="센서 교체 완료",
            user="operator",
        )
        db.add(action)
        db.commit()

        try:
            service = ReportService(db)
            result = service.get_malfunction_grid_data(days=30)

            target_row = None
            for row in result["rows"]:
                if row[0] == event.id:
                    target_row = row
                    break

            assert target_row is not None
            assert target_row[2] == "FAULT_FENCE"       # 장애유형
            assert "controller" in str(target_row[3]).lower() # 장비유형
            assert target_row[4] == "테스트 컨트롤러2"     # 장비명
            assert target_row[6] == "operator"            # 조치자
            assert target_row[7] == "센서 교체 완료"       # 조치내용
        finally:
            db.delete(action)
            db.delete(event)
            db.delete(device)
            db.commit()
