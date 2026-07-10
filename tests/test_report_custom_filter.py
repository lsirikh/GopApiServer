"""
Tests for Report Custom Template Component Filtering
TDD: Test First
PRD: PRD_Report_CustomTemplate_Filter.md
"""
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base
from app.dependencies import get_db
from app.models import *  # noqa
from app.models.report import ReportTemplate, ReportGeneration  # noqa


# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_report_custom_filter.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Setup test database once for the module"""
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create database session for each test"""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.query(ReportGeneration).delete()
        session.query(ReportTemplate).delete()
        session.commit()
        session.close()


@pytest.fixture(scope="function")
def client(db):
    """Create test client"""
    with TestClient(app) as test_client:
        yield test_client


# ============================================================
# Phase 1: get_structured_preview_data() 필터링
# ============================================================

class TestStructuredPreviewFilterRegression:
    """1.1: enabled_components=None 시 기존 동작 유지 (회귀 테스트)"""

    def test_no_filter_returns_all_11_sections(self, db):
        """enabled_components=None이면 기존과 동일하게 11개 섹션 반환"""
        from app.services.report_service import ReportService
        service = ReportService(db)

        result = service.get_structured_preview_data(days=7, enabled_components=None)
        sections = result["sections"]
        assert len(sections) == 11

        section_names = [s["name"] for s in sections]
        assert section_names == [
            "summary", "device_charts", "event_charts",
            "system_charts", "user_charts", "device_grid",
            "event_grids", "system_event_grid", "config_grid",
            "audit_grid", "user_grids",
        ]


class TestStructuredPreviewFilterSingleComponent:
    """1.2: 단일 컴포넌트 필터링 시 해당 섹션만 반환"""

    def test_filter_device_status_pie_only(self, db):
        """enabled_components=["DEVICE_STATUS_PIE"] → device_charts 섹션만 반환"""
        from app.services.report_service import ReportService
        service = ReportService(db)

        result = service.get_structured_preview_data(
            days=7, enabled_components=["DEVICE_STATUS_PIE"]
        )
        sections = result["sections"]
        section_names = [s["name"] for s in sections]

        assert "device_charts" in section_names
        assert len(sections) == 1

        # charts에 DEVICE_STATUS_PIE만 포함
        device_section = sections[0]
        chart_ids = [c["id"] for c in device_section["charts"]]
        assert "DEVICE_STATUS_PIE" in chart_ids
        assert "DEVICE_TYPE_BAR" not in chart_ids


class TestStructuredPreviewFilterMultiComponent:
    """1.4: 복수 컴포넌트 필터링 시 해당 섹션들만 반환"""

    def test_filter_two_components_across_sections(self, db):
        """enabled_components=["DEVICE_STATUS_PIE", "DEVICE_GRID"] → 2개 섹션"""
        from app.services.report_service import ReportService
        service = ReportService(db)

        result = service.get_structured_preview_data(
            days=7, enabled_components=["DEVICE_STATUS_PIE", "DEVICE_GRID"]
        )
        sections = result["sections"]
        section_names = [s["name"] for s in sections]

        assert len(sections) == 2
        assert "device_charts" in section_names
        assert "device_grid" in section_names


class TestStructuredPreviewFilterChartLevel:
    """1.5: 섹션 내 차트 레벨 필터링 확인"""

    def test_device_charts_section_filters_individual_charts(self, db):
        """DEVICE_STATUS_PIE만 enabled 시 device_charts에 PIE만, BAR 제외"""
        from app.services.report_service import ReportService
        service = ReportService(db)

        result = service.get_structured_preview_data(
            days=7, enabled_components=["DEVICE_STATUS_PIE"]
        )
        device_section = [s for s in result["sections"] if s["name"] == "device_charts"][0]

        assert len(device_section["charts"]) == 1
        assert device_section["charts"][0]["id"] == "DEVICE_STATUS_PIE"

    def test_both_device_charts_enabled(self, db):
        """DEVICE_STATUS_PIE + DEVICE_TYPE_BAR 모두 enabled → 2개 차트 모두 포함"""
        from app.services.report_service import ReportService
        service = ReportService(db)

        result = service.get_structured_preview_data(
            days=7, enabled_components=["DEVICE_STATUS_PIE", "DEVICE_TYPE_BAR"]
        )
        device_section = [s for s in result["sections"] if s["name"] == "device_charts"][0]

        assert len(device_section["charts"]) == 2


class TestStructuredPreviewFilterSummary:
    """1.6: SUMMARY_CARD 필터링 시 summary_data 포함 확인"""

    def test_summary_card_includes_summary_data(self, db):
        """SUMMARY_CARD enabled → summary 섹션 + summary_data 필드 존재"""
        from app.services.report_service import ReportService
        service = ReportService(db)

        result = service.get_structured_preview_data(
            days=7, enabled_components=["SUMMARY_CARD"]
        )
        sections = result["sections"]
        assert len(sections) == 1
        assert sections[0]["name"] == "summary"
        assert "summary_data" in sections[0]
        assert "device_categories" in sections[0]["summary_data"]


# ============================================================
# Phase 2: Router — Preview 엔드포인트 CUSTOM 분기
# ============================================================

class TestPreviewStandardRegression:
    """2.1: STANDARD preview는 전체 11개 섹션 반환 (회귀)"""

    def test_standard_preview_returns_all_sections(self, client, db):
        """STANDARD report_type generation → preview 시 11개 섹션"""
        gen = ReportGeneration(
            report_type="STANDARD",
            title="Standard Report",
            period_type="7d",
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc),
            status="COMPLETED",
        )
        db.add(gen)
        db.commit()
        db.refresh(gen)

        response = client.get(f"/api/reports/generations/{gen.id}/preview")
        assert response.status_code == 200
        data = response.json()
        sections = data["data"]["sections"]
        assert len(sections) == 11


class TestPreviewCustomFiltered:
    """2.2: CUSTOM preview는 template 컴포넌트에 따라 필터링"""

    def test_custom_preview_returns_filtered_sections(self, client, db):
        """CUSTOM report + template(DEVICE_STATUS_PIE, DEVICE_GRID) → 2개 섹션만"""
        # 1. 템플릿 생성 (2개 컴포넌트만 enabled)
        template = ReportTemplate(
            name="Custom Device Only",
            report_type="CUSTOM",
            components=[
                {"id": "DEVICE_STATUS_PIE", "order": 1, "enabled": True, "title": None},
                {"id": "DEVICE_GRID", "order": 2, "enabled": True, "title": None},
                {"id": "EVENT_SUMMARY_PIE", "order": 3, "enabled": False, "title": None},
            ],
            default_period="7d",
        )
        db.add(template)
        db.commit()
        db.refresh(template)

        # 2. 해당 템플릿으로 CUSTOM generation 생성
        gen = ReportGeneration(
            report_type="CUSTOM",
            template_id=template.id,
            title="Custom Device Report",
            period_type="7d",
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc),
            status="COMPLETED",
        )
        db.add(gen)
        db.commit()
        db.refresh(gen)

        response = client.get(f"/api/reports/generations/{gen.id}/preview")
        assert response.status_code == 200
        data = response.json()
        sections = data["data"]["sections"]
        section_names = [s["name"] for s in sections]

        assert len(sections) == 2
        assert "device_charts" in section_names
        assert "device_grid" in section_names
        # 비활성 EVENT_SUMMARY_PIE는 포함되지 않음
        assert "event_charts" not in section_names


class TestPreviewCustomFallback:
    """2.4: CUSTOM이지만 template 삭제된 경우 → 전체 섹션 반환 (fallback)"""

    def test_custom_with_deleted_template_falls_back_to_all(self, client, db):
        """template_id가 존재하지 않는 ID → 전체 11개 섹션 반환"""
        gen = ReportGeneration(
            report_type="CUSTOM",
            template_id=99999,  # 존재하지 않는 template
            title="Custom Deleted Template Report",
            period_type="7d",
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc),
            status="COMPLETED",
        )
        db.add(gen)
        db.commit()
        db.refresh(gen)

        response = client.get(f"/api/reports/generations/{gen.id}/preview")
        assert response.status_code == 200
        data = response.json()
        sections = data["data"]["sections"]
        assert len(sections) == 11  # fallback: 전체 반환

    def test_custom_without_template_id_falls_back(self, client, db):
        """template_id=None인 CUSTOM → 전체 11개 섹션 반환"""
        gen = ReportGeneration(
            report_type="CUSTOM",
            template_id=None,
            title="Custom No Template Report",
            period_type="7d",
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc),
            status="COMPLETED",
        )
        db.add(gen)
        db.commit()
        db.refresh(gen)

        response = client.get(f"/api/reports/generations/{gen.id}/preview")
        assert response.status_code == 200
        data = response.json()
        sections = data["data"]["sections"]
        assert len(sections) == 11


# ============================================================
# Phase 3: generate_report_async() PDF 필터링
# ============================================================

class TestGetEnabledComponents:
    """3.1: _get_enabled_components() 헬퍼 메서드 테스트"""

    def test_standard_returns_none(self, db):
        """STANDARD report → None 반환 (전체 포함)"""
        from app.services.report_service import ReportService
        gen = ReportGeneration(
            report_type="STANDARD",
            title="Standard",
            period_type="7d",
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc),
            status="COMPLETED",
        )
        db.add(gen)
        db.commit()
        db.refresh(gen)

        service = ReportService(db)
        result = service.get_enabled_components(gen)
        assert result is None

    def test_custom_with_template_returns_enabled_ids(self, db):
        """CUSTOM + template → enabled=True인 컴포넌트 ID 리스트"""
        from app.services.report_service import ReportService
        template = ReportTemplate(
            name="Test Template",
            report_type="CUSTOM",
            components=[
                {"id": "DEVICE_STATUS_PIE", "order": 1, "enabled": True, "title": None},
                {"id": "DEVICE_GRID", "order": 2, "enabled": True, "title": None},
                {"id": "EVENT_SUMMARY_PIE", "order": 3, "enabled": False, "title": None},
            ],
            default_period="7d",
        )
        db.add(template)
        db.commit()
        db.refresh(template)

        gen = ReportGeneration(
            report_type="CUSTOM",
            template_id=template.id,
            title="Custom",
            period_type="7d",
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc),
            status="COMPLETED",
        )
        db.add(gen)
        db.commit()
        db.refresh(gen)

        service = ReportService(db)
        result = service.get_enabled_components(gen)
        assert result is not None
        assert "DEVICE_STATUS_PIE" in result
        assert "DEVICE_GRID" in result
        assert "EVENT_SUMMARY_PIE" not in result
        assert len(result) == 2


class TestPdfComponentMaps:
    """3.2: PDF 차트/그리드 컴포넌트 매핑 상수 테스트"""

    def test_chart_component_map_exists(self):
        """CHART_COMPONENT_MAP 상수가 존재하고 9개 매핑 포함 (기존 4 + 신규 5)"""
        from app.services.report_service import CHART_COMPONENT_MAP
        assert len(CHART_COMPONENT_MAP) == 9
        assert "DEVICE_STATUS_PIE" in CHART_COMPONENT_MAP.values()
        assert "EVENT_TREND_LINE" in CHART_COMPONENT_MAP.values()
        assert "SYSTEM_TREND_LINE" in CHART_COMPONENT_MAP.values()
        assert "USER_ROLE_PIE" in CHART_COMPONENT_MAP.values()
        assert "USER_LOGIN_TREND_LINE" in CHART_COMPONENT_MAP.values()
        assert "USER_LOGIN_RESULT_PIE" in CHART_COMPONENT_MAP.values()

    def test_grid_component_map_exists(self):
        """GRID_COMPONENT_MAP 상수가 존재하고 10개 매핑 포함"""
        from app.services.report_service import GRID_COMPONENT_MAP
        assert len(GRID_COMPONENT_MAP) == 10
        assert "DEVICE_GRID" in GRID_COMPONENT_MAP.values()
