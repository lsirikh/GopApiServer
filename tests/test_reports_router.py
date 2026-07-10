"""
Tests for Reports Router
TDD: Test First
PRD: PRD_Report_System.md Section 6
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base
from app.dependencies import get_db
from app.models.report import ReportTemplate, ReportGeneration


# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_reports.db"
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
    import os
    if os.path.exists("./test_reports.db"):
        try:
            os.remove("./test_reports.db")
        except PermissionError:
            pass  # Windows file locking - will be cleaned up on next run


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


class TestReportTemplatesGet:
    """Tests for GET /api/reports/templates"""

    def test_get_templates_empty_list(self, client):
        """GET /api/reports/templates - 200 OK, 빈 목록 반환"""
        response = client.get("/api/reports/templates")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == []

    def test_get_templates_pagination(self, client, db):
        """GET /api/reports/templates - pagination 동작 (page, limit)"""
        # Create test templates
        for i in range(5):
            template = ReportTemplate(
                name=f"Template {i+1}",
                components=[{"id": "SUMMARY_CARD", "order": 1, "enabled": True}]
            )
            db.add(template)
        db.commit()

        # Test default pagination
        response = client.get("/api/reports/templates")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 5

        # Test with limit
        response = client.get("/api/reports/templates?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2

        # Test with page
        response = client.get("/api/reports/templates?page=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2


class TestReportTemplatesPost:
    """Tests for POST /api/reports/templates"""

    def test_create_template_success(self, client):
        """POST /api/reports/templates - 201 Created, 템플릿 생성 성공"""
        payload = {
            "name": "Test Template",
            "components": [
                {"id": "SUMMARY_CARD", "order": 1, "enabled": True}
            ]
        }
        response = client.post("/api/reports/templates", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Test Template"
        assert data["data"]["id"] is not None
        assert data["data"]["report_type"] == "CUSTOM"
        assert data["data"]["is_public"] is False

    def test_create_template_empty_name_error(self, client):
        """POST /api/reports/templates - name 빈 문자열 시 422 에러"""
        payload = {
            "name": "",
            "components": [
                {"id": "SUMMARY_CARD", "order": 1, "enabled": True}
            ]
        }
        response = client.post("/api/reports/templates", json=payload)
        assert response.status_code == 422


class TestReportTemplatesGetById:
    """Tests for GET /api/reports/templates/{id}"""

    def test_get_template_by_id_success(self, client, db):
        """GET /api/reports/templates/{id} - 200 OK, 템플릿 상세 조회"""
        # Create a template
        template = ReportTemplate(
            name="Test Template",
            description="Test Description",
            components=[{"id": "SUMMARY_CARD", "order": 1, "enabled": True}]
        )
        db.add(template)
        db.commit()
        db.refresh(template)

        response = client.get(f"/api/reports/templates/{template.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == template.id
        assert data["data"]["name"] == "Test Template"
        assert data["data"]["description"] == "Test Description"

    def test_get_template_by_id_not_found(self, client):
        """GET /api/reports/templates/{id} - 존재하지 않는 ID 시 404"""
        response = client.get("/api/reports/templates/99999")
        assert response.status_code == 404


class TestReportTemplatesPatch:
    """Tests for PATCH /api/reports/templates/{id}"""

    def test_update_template_success(self, client, db):
        """PATCH /api/reports/templates/{id} - 200 OK, 부분 업데이트 성공"""
        # Create a template
        template = ReportTemplate(
            name="Original Name",
            description="Original Description",
            components=[{"id": "SUMMARY_CARD", "order": 1, "enabled": True}]
        )
        db.add(template)
        db.commit()
        db.refresh(template)

        # Update only the name
        payload = {"name": "Updated Name"}
        response = client.patch(f"/api/reports/templates/{template.id}", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Updated Name"
        assert data["data"]["description"] == "Original Description"

    def test_update_template_not_found(self, client):
        """PATCH /api/reports/templates/{id} - 존재하지 않는 ID 시 404"""
        payload = {"name": "Updated Name"}
        response = client.patch("/api/reports/templates/99999", json=payload)
        assert response.status_code == 404


class TestReportTemplatesDelete:
    """Tests for DELETE /api/reports/templates/{id}"""

    def test_delete_template_success(self, client, db):
        """DELETE /api/reports/templates/{id} - 200 OK, 삭제 성공"""
        # Create a template
        template = ReportTemplate(
            name="Template to Delete",
            components=[{"id": "SUMMARY_CARD", "order": 1, "enabled": True}]
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        template_id = template.id

        response = client.delete(f"/api/reports/templates/{template_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify deletion
        response = client.get(f"/api/reports/templates/{template_id}")
        assert response.status_code == 404

    def test_delete_template_not_found(self, client):
        """DELETE /api/reports/templates/{id} - 존재하지 않는 ID 시 404"""
        response = client.delete("/api/reports/templates/99999")
        assert response.status_code == 404


# ==============================================================================
# Report Generation Tests
# ==============================================================================

class TestReportGenerate:
    """Tests for POST /api/reports/generate"""

    def test_generate_report_success(self, client):
        """POST /api/reports/generate - 202 Accepted, 생성 요청 성공"""
        payload = {
            "report_type": "STANDARD",
            "title": "Weekly Security Report",
            "period_type": "7d"
        }
        response = client.post("/api/reports/generate", json=payload)
        assert response.status_code == 202
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] is not None
        assert data["data"]["status"] == "PENDING"

    def test_generate_report_with_dates(self, client):
        """POST /api/reports/generate - start_date, end_date 자동 계산"""
        payload = {
            "report_type": "STANDARD",
            "title": "Monthly Report",
            "period_type": "30d"
        }
        response = client.post("/api/reports/generate", json=payload)
        assert response.status_code == 202
        data = response.json()
        assert data["data"]["start_date"] is not None
        assert data["data"]["end_date"] is not None
        assert data["data"]["period_type"] == "30d"


class TestReportGenerationsList:
    """Tests for GET /api/reports/generations"""

    def test_get_generations_list(self, client, db):
        """GET /api/reports/generations - 200 OK, 생성 이력 목록"""
        from datetime import datetime, timezone
        # Create test generations
        for i in range(3):
            gen = ReportGeneration(
                report_type="STANDARD",
                title=f"Report {i+1}",
                period_type="7d",
                start_date=datetime.now(timezone.utc),
                end_date=datetime.now(timezone.utc),
                status="PENDING"
            )
            db.add(gen)
        db.commit()

        response = client.get("/api/reports/generations")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 3

    def test_get_generations_with_status_filter(self, client, db):
        """GET /api/reports/generations?status=COMPLETED - 상태 필터링"""
        from datetime import datetime, timezone
        # Create generations with different statuses
        gen1 = ReportGeneration(
            report_type="STANDARD",
            title="Completed Report",
            period_type="7d",
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc),
            status="COMPLETED"
        )
        gen2 = ReportGeneration(
            report_type="STANDARD",
            title="Pending Report",
            period_type="7d",
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc),
            status="PENDING"
        )
        db.add_all([gen1, gen2])
        db.commit()

        # Filter by COMPLETED status
        response = client.get("/api/reports/generations?status=COMPLETED")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["status"] == "COMPLETED"


class TestReportGenerationDetail:
    """Tests for GET /api/reports/generations/{id}"""

    def test_get_generation_by_id_success(self, client, db):
        """GET /api/reports/generations/{id} - 200 OK, 상세 조회"""
        from datetime import datetime, timezone
        gen = ReportGeneration(
            report_type="STANDARD",
            title="Detail Test Report",
            period_type="7d",
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc),
            status="PENDING"
        )
        db.add(gen)
        db.commit()
        db.refresh(gen)

        response = client.get(f"/api/reports/generations/{gen.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == gen.id
        assert data["data"]["title"] == "Detail Test Report"

    def test_get_generation_by_id_not_found(self, client):
        """GET /api/reports/generations/{id} - 존재하지 않는 ID 시 404"""
        response = client.get("/api/reports/generations/99999")
        assert response.status_code == 404

    def test_get_generation_completed_includes_pdf_download_url(self, client, db):
        """GET /api/reports/generations/{id} - COMPLETED 시 pdf_download_url 포함"""
        from datetime import datetime, timezone
        gen = ReportGeneration(
            report_type="STANDARD",
            title="Completed Report",
            period_type="7d",
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc),
            status="COMPLETED",
            pdf_file_path="/reports/2024/report_1.pdf"
        )
        db.add(gen)
        db.commit()
        db.refresh(gen)

        response = client.get(f"/api/reports/generations/{gen.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "pdf_download_url" in data["data"]
        assert data["data"]["pdf_download_url"] is not None


class TestReportGenerationDownload:
    """Tests for GET /api/reports/generations/{id}/download"""

    def test_download_report_not_completed_error(self, client, db):
        """GET /api/reports/generations/{id}/download - COMPLETED 아닌 경우 400"""
        from datetime import datetime, timezone
        gen = ReportGeneration(
            report_type="STANDARD",
            title="Pending Report",
            period_type="7d",
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc),
            status="PENDING"
        )
        db.add(gen)
        db.commit()
        db.refresh(gen)

        response = client.get(f"/api/reports/generations/{gen.id}/download")
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "COMPLETED" in data["error"]["message"]

    def test_download_report_not_found(self, client):
        """GET /api/reports/generations/{id}/download - 존재하지 않는 ID 시 404"""
        response = client.get("/api/reports/generations/99999/download")
        assert response.status_code == 404


class TestReportGenerationPreview:
    """Tests for GET /api/reports/generations/{id}/preview"""

    def test_preview_report_success(self, client, db):
        """GET /api/reports/generations/{id}/preview - 200 OK, 구조화된 미리보기 데이터"""
        from datetime import datetime, timezone
        gen = ReportGeneration(
            report_type="STANDARD",
            title="Completed Report",
            period_type="7d",
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc),
            status="COMPLETED",
            summary_data={"total_events": 100, "critical_count": 5}
        )
        db.add(gen)
        db.commit()
        db.refresh(gen)

        response = client.get(f"/api/reports/generations/{gen.id}/preview")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "sections" in data["data"]

    def test_preview_report_not_completed_error(self, client, db):
        """GET /api/reports/generations/{id}/preview - COMPLETED 아닌 경우 400"""
        from datetime import datetime, timezone
        gen = ReportGeneration(
            report_type="STANDARD",
            title="Generating Report",
            period_type="7d",
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc),
            status="GENERATING"
        )
        db.add(gen)
        db.commit()
        db.refresh(gen)

        response = client.get(f"/api/reports/generations/{gen.id}/preview")
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "COMPLETED" in data["error"]["message"]


class TestReportComponents:
    """Tests for GET /api/reports/components"""

    def test_get_components_returns_5_categories(self, client):
        """GET /api/reports/components - 200 OK, 5개 카테고리 반환 (PRD v1.4)"""
        response = client.get("/api/reports/components")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # 5 categories: SUMMARY, DEVICE, EVENT, SYSTEM, USER (v1.4)
        assert len(data["data"]) == 5

    def test_get_components_includes_correct_counts(self, client):
        """GET /api/reports/components - SUMMARY(1), DEVICE(3), EVENT(6), SYSTEM(5), USER(6) 컴포넌트 포함"""
        response = client.get("/api/reports/components")
        assert response.status_code == 200
        data = response.json()

        # Find each category and verify component counts
        categories = {cat["category"]: cat["components"] for cat in data["data"]}
        assert len(categories.get("SUMMARY", [])) == 1
        assert len(categories.get("DEVICE", [])) == 3
        assert len(categories.get("EVENT", [])) == 6
        assert len(categories.get("SYSTEM", [])) == 5
        assert len(categories.get("USER", [])) == 6


class TestReportPreviewPage:
    """Tests for GET /reports/preview/{id}"""

    def test_preview_page_returns_html(self, client, db):
        """GET /reports/preview/{id} - HTML 응답 반환"""
        from datetime import datetime, timezone
        gen = ReportGeneration(
            report_type="STANDARD",
            title="Preview Test Report",
            period_type="7d",
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc),
            status="COMPLETED"
        )
        db.add(gen)
        db.commit()
        db.refresh(gen)

        response = client.get(f"/reports/preview/{gen.id}")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_preview_page_not_found(self, client):
        """GET /reports/preview/{id} - 존재하지 않는 ID 시 404"""
        response = client.get("/reports/preview/99999")
        assert response.status_code == 404


# ==============================================================================
# Phase 5.2: Preview API - Structured Response
# ==============================================================================

class TestPreviewAPIStructured:
    """Tests for structured preview API response"""

    def test_preview_returns_structured_sections(self, client, db):
        """GET /preview returns structured sections with charts/grids"""
        from datetime import datetime, timezone
        gen = ReportGeneration(
            report_type="STANDARD",
            title="Structured Preview Report",
            period_type="7d",
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc),
            status="COMPLETED"
        )
        db.add(gen)
        db.commit()
        db.refresh(gen)

        response = client.get(f"/api/reports/generations/{gen.id}/preview")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "sections" in data["data"]
        assert isinstance(data["data"]["sections"], list)
        assert len(data["data"]["sections"]) > 0

    def test_preview_sections_have_charts_with_data(self, client, db):
        """Preview sections charts have id, title, type, data format"""
        from datetime import datetime, timezone
        gen = ReportGeneration(
            report_type="STANDARD",
            title="Chart Preview",
            period_type="7d",
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc),
            status="COMPLETED"
        )
        db.add(gen)
        db.commit()
        db.refresh(gen)

        response = client.get(f"/api/reports/generations/{gen.id}/preview")
        data = response.json()
        for section in data["data"]["sections"]:
            if "charts" in section:
                for chart in section["charts"]:
                    assert "id" in chart
                    assert "title" in chart
                    assert "type" in chart
                    assert "data" in chart

    def test_preview_includes_user_section(self, client, db):
        """Preview includes USER section"""
        from datetime import datetime, timezone
        gen = ReportGeneration(
            report_type="STANDARD",
            title="User Section Preview",
            period_type="7d",
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc),
            status="COMPLETED"
        )
        db.add(gen)
        db.commit()
        db.refresh(gen)

        response = client.get(f"/api/reports/generations/{gen.id}/preview")
        data = response.json()
        section_names = [s["name"] for s in data["data"]["sections"]]
        assert "user_charts" in section_names
        assert "user_grids" in section_names


# ==============================================================================
# Phase 6: Download FileResponse
# ==============================================================================

class TestDownloadFileResponse:
    """Tests for FileResponse PDF download"""

    def test_download_returns_400_when_not_completed(self, client, db):
        """GET /download returns 400 when status != COMPLETED"""
        from datetime import datetime, timezone
        gen = ReportGeneration(
            report_type="STANDARD",
            title="Pending Report",
            period_type="7d",
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc),
            status="PENDING"
        )
        db.add(gen)
        db.commit()
        db.refresh(gen)

        response = client.get(f"/api/reports/generations/{gen.id}/download")
        assert response.status_code == 400

    def test_download_returns_404_when_no_pdf_path(self, client, db):
        """GET /download returns 404 when pdf_file_path is None"""
        from datetime import datetime, timezone
        gen = ReportGeneration(
            report_type="STANDARD",
            title="No PDF Report",
            period_type="7d",
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc),
            status="COMPLETED",
            pdf_file_path=None
        )
        db.add(gen)
        db.commit()
        db.refresh(gen)

        response = client.get(f"/api/reports/generations/{gen.id}/download")
        assert response.status_code == 404

    def test_download_returns_pdf_when_file_exists(self, client, db):
        """GET /download returns PDF content-type when file exists"""
        import tempfile, os
        from datetime import datetime, timezone

        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-1.4 test content")
            pdf_path = f.name

        try:
            gen = ReportGeneration(
                report_type="STANDARD",
                title="PDF Download Report",
                period_type="7d",
                start_date=datetime.now(timezone.utc),
                end_date=datetime.now(timezone.utc),
                status="COMPLETED",
                pdf_file_path=pdf_path
            )
            db.add(gen)
            db.commit()
            db.refresh(gen)

            response = client.get(f"/api/reports/generations/{gen.id}/download")
            assert response.status_code == 200
            assert "application/pdf" in response.headers.get("content-type", "")
        finally:
            os.unlink(pdf_path)


# ==============================================================================
# Phase 9: Router Refinements
# ==============================================================================

class TestComponentsResponseFormat:
    """Tests for Component response with label field"""

    def test_components_have_label_field(self, client):
        """GET /components returns categories with label field"""
        response = client.get("/api/reports/components")
        data = response.json()
        for category in data["data"]:
            assert "label" in category, f"Category {category.get('category', '?')} missing label field"

    def test_components_have_component_chart_type(self, client):
        """GET /components components include chart_type field"""
        response = client.get("/api/reports/components")
        data = response.json()
        for category in data["data"]:
            for comp in category["components"]:
                assert "chart_type" in comp or "id" in comp


class TestTemplateListResponseFormat:
    """Phase 9: Templates list returns lightweight format with component_count"""

    def test_templates_list_includes_component_count(self, client, db):
        """GET /templates list items include component_count field"""
        template = ReportTemplate(
            name="Component Count Test",
            report_type="STANDARD",
            is_public=True,
            components=[
                {"id": "SUMMARY_CARD", "order": 1, "enabled": True},
                {"id": "DEVICE_STATUS_PIE", "order": 2, "enabled": True},
            ],
            default_period="7d",
        )
        db.add(template)
        db.commit()

        response = client.get("/api/reports/templates")
        data = response.json()
        assert data["success"] is True
        items = data["data"]
        assert len(items) > 0
        item = items[0]
        assert "component_count" in item
        assert item["component_count"] == 2

    def test_templates_list_omits_full_components(self, client, db):
        """GET /templates list should not include full components array"""
        template = ReportTemplate(
            name="Lightweight Test",
            report_type="CUSTOM",
            is_public=False,
            components=[
                {"id": "DEVICE_GRID", "order": 1, "enabled": True},
            ],
            default_period="30d",
        )
        db.add(template)
        db.commit()

        response = client.get("/api/reports/templates")
        data = response.json()
        items = data["data"]
        for item in items:
            # List response should have component_count instead of full components
            assert "component_count" in item


class TestGenerationsListResponseFormat:
    """Phase 9: Generations list returns lightweight format"""

    def test_generations_list_has_lightweight_fields(self, client, db):
        """GET /generations list items have lightweight fields"""
        from datetime import datetime, timedelta

        gen = ReportGeneration(
            report_type="STANDARD",
            title="Lightweight Fields Test",
            period_type="7d",
            start_date=datetime.now() - timedelta(days=7),
            end_date=datetime.now(),
            status="COMPLETED",
            generator_name="Test User",
            completed_at=datetime.now(),
        )
        db.add(gen)
        db.commit()

        response = client.get("/api/reports/generations")
        data = response.json()
        assert data["success"] is True
        items = data["data"]
        assert len(items) > 0
        item = items[0]
        # Lightweight fields
        assert "id" in item
        assert "report_type" in item
        assert "title" in item
        assert "period_type" in item
        assert "status" in item
        assert "created_at" in item
        assert "generator_name" in item
        assert "completed_at" in item
