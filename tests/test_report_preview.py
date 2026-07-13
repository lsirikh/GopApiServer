"""
Tests for Report Preview Page (Chart.js Integration)
PRD: PRD_Report_System.md - Section 10: 개발용 Preview 페이지
TDD: Red -> Green -> Refactor
"""
import pytest
import os
from datetime import datetime, timedelta


class TestPreviewTemplateExists:
    """RS-12.1: preview.html 템플릿 존재 테스트"""

    def test_preview_template_directory_exists(self):
        """app/templates/reports 디렉토리가 존재해야 함"""
        template_dir = os.path.join("app", "templates", "reports")
        assert os.path.exists(template_dir), f"Directory {template_dir} should exist"

    def test_preview_html_file_exists(self):
        """app/templates/reports/preview.html 파일이 존재해야 함"""
        template_path = os.path.join("app", "templates", "reports", "preview.html")
        assert os.path.exists(template_path), f"File {template_path} should exist"


class TestPreviewTemplateContent:
    """RS-12.2: preview.html 템플릿 내용 테스트"""

    def test_preview_template_has_chart_js_cdn(self):
        """템플릿에 Chart.js CDN이 포함되어야 함"""
        template_path = os.path.join("app", "templates", "reports", "preview.html")
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        assert "chart.js" in content.lower() or "chartjs" in content.lower()

    def test_preview_template_has_jinja2_report_variable(self):
        """템플릿에 report 변수 사용이 포함되어야 함"""
        template_path = os.path.join("app", "templates", "reports", "preview.html")
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        assert "{{ report." in content or "{{report." in content

    def test_preview_template_has_jinja2_preview_variable(self):
        """템플릿에 preview 변수 사용이 포함되어야 함"""
        template_path = os.path.join("app", "templates", "reports", "preview.html")
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        assert "{{ preview." in content or "{{preview." in content or "preview.sections" in content

    def test_preview_template_has_canvas_for_charts(self):
        """템플릿에 차트용 canvas 요소가 포함되어야 함"""
        template_path = os.path.join("app", "templates", "reports", "preview.html")
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        assert "<canvas" in content

    def test_preview_template_has_download_button(self):
        """템플릿에 PDF 다운로드 버튼이 포함되어야 함"""
        template_path = os.path.join("app", "templates", "reports", "preview.html")
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        assert "/download" in content


class TestMainPyTemplateIntegration:
    """RS-12.3: main.py Jinja2Templates 연동 테스트"""

    def test_main_has_jinja2_templates_import(self):
        """main.py에 Jinja2Templates import가 있어야 함"""
        main_path = os.path.join("app", "main.py")
        with open(main_path, 'r', encoding='utf-8') as f:
            content = f.read()
        assert "Jinja2Templates" in content

    def test_main_has_templates_instance(self):
        """main.py에 templates 인스턴스가 있어야 함"""
        main_path = os.path.join("app", "main.py")
        with open(main_path, 'r', encoding='utf-8') as f:
            content = f.read()
        assert "templates = Jinja2Templates" in content or 'templates=Jinja2Templates' in content

    def test_preview_route_uses_template_response(self):
        """preview 라우트가 TemplateResponse를 사용해야 함"""
        main_path = os.path.join("app", "main.py")
        with open(main_path, 'r', encoding='utf-8') as f:
            content = f.read()
        assert "TemplateResponse" in content


class TestPreviewRouteAPI:
    """RS-12.4: Preview Route API 테스트"""

    def test_preview_route_returns_html(self, client, test_db, test_report_generation):
        """Preview 라우트가 HTML을 반환해야 함"""
        response = client.get(f"/reports/preview/{test_report_generation.id}")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_preview_route_contains_report_title(self, client, test_db, test_report_generation):
        """Preview 페이지에 보고서 제목이 포함되어야 함"""
        response = client.get(f"/reports/preview/{test_report_generation.id}")
        assert test_report_generation.title in response.text

    def test_preview_route_contains_chartjs_script(self, client, test_db, test_report_generation):
        """Preview 페이지에 Chart.js 스크립트가 포함되어야 함"""
        response = client.get(f"/reports/preview/{test_report_generation.id}")
        assert "chart.js" in response.text.lower() or "chartjs" in response.text.lower()

    def test_preview_route_404_for_invalid_id(self, client, test_db):
        """존재하지 않는 ID로 요청 시 404 반환"""
        response = client.get("/reports/preview/99999")
        assert response.status_code == 404


class TestPreviewSwaggerAccess:
    """Phase 8: Swagger에서 Preview 접근 가능 테스트"""

    def test_preview_route_included_in_openapi_schema(self, client):
        """preview 엔드포인트가 OpenAPI 스키마에 포함되어야 함"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        paths = schema.get("paths", {})
        # Should find preview route in the paths
        preview_paths = [p for p in paths if "preview" in p and "{generation_id}" in p]
        assert len(preview_paths) > 0, "Preview route should be in OpenAPI schema"

    def test_preview_route_tag_is_reports(self, client):
        """preview 엔드포인트의 태그가 Reports여야 함"""
        response = client.get("/openapi.json")
        schema = response.json()
        paths = schema.get("paths", {})
        preview_paths = [p for p in paths if "preview" in p and "{generation_id}" in p]
        if preview_paths:
            path_info = paths[preview_paths[0]]
            get_info = path_info.get("get", {})
            tags = get_info.get("tags", [])
            assert "Reports" in tags


class TestPreviewStructuredRendering:
    """Phase 8: Preview 페이지가 구조화된 데이터를 처리하는지 테스트"""

    def test_preview_page_renders_structured_sections(self, client, test_db, test_report_generation):
        """Preview 페이지에 구조화된 섹션이 렌더링되어야 함"""
        response = client.get(f"/reports/preview/{test_report_generation.id}")
        assert response.status_code == 200
        # Should contain section titles from structured data
        assert "장비 현황" in response.text or "요약" in response.text

    def test_preview_page_renders_grid_tables(self, client, test_db, test_report_generation):
        """Preview 페이지에 그리드 테이블 헤더가 표시되어야 함"""
        response = client.get(f"/reports/preview/{test_report_generation.id}")
        assert response.status_code == 200
        # Grid tables should have column headers rendered
        assert "<th>" in response.text


@pytest.fixture
def test_report_generation(test_db):
    """테스트용 ReportGeneration 레코드"""
    from app.models.report import ReportGeneration

    generation = ReportGeneration(
        report_type="STANDARD",
        title="Test Preview Report",
        period_type="7d",
        start_date=datetime.now() - timedelta(days=7),
        end_date=datetime.now(),
        status="COMPLETED"
    )
    test_db.add(generation)
    test_db.commit()
    test_db.refresh(generation)
    return generation
