"""
Tests for Report System Schemas
TDD: Test First
PRD: PRD_Report_System.md Section 5
"""
import pytest
from pydantic import ValidationError


class TestReportComponentConfigSchema:
    """Tests for ReportComponentConfig schema"""

    def test_report_component_config_has_required_fields(self):
        """ReportComponentConfig 스키마가 id, order, enabled, title 필드를 가지는지 확인"""
        from app.schemas.report import ReportComponentConfig

        # Valid data
        config = ReportComponentConfig(
            id="SUMMARY_CARD",
            order=1,
            enabled=True,
            title="Summary"
        )
        assert config.id == "SUMMARY_CARD"
        assert config.order == 1
        assert config.enabled is True
        assert config.title == "Summary"

    def test_report_component_config_title_optional(self):
        """ReportComponentConfig.title이 optional인지 확인"""
        from app.schemas.report import ReportComponentConfig

        config = ReportComponentConfig(
            id="SUMMARY_CARD",
            order=1,
            enabled=True
        )
        assert config.title is None


class TestReportTemplateCreateSchema:
    """Tests for ReportTemplateCreate schema"""

    def test_report_template_create_required_fields(self):
        """ReportTemplateCreate에 name, components 필수 필드 확인"""
        from app.schemas.report import ReportTemplateCreate, ReportComponentConfig

        # Valid data with required fields
        template = ReportTemplateCreate(
            name="Test Template",
            components=[
                ReportComponentConfig(id="SUMMARY_CARD", order=1, enabled=True)
            ]
        )
        assert template.name == "Test Template"
        assert len(template.components) == 1

    def test_report_template_create_optional_fields(self):
        """ReportTemplateCreate에 description, report_type, is_public, default_period 선택 필드 확인"""
        from app.schemas.report import ReportTemplateCreate, ReportComponentConfig
        from app.utils.enums import EnumReportType, EnumReportPeriod

        template = ReportTemplateCreate(
            name="Test Template",
            components=[
                ReportComponentConfig(id="SUMMARY_CARD", order=1, enabled=True)
            ],
            description="Test description",
            report_type=EnumReportType.CUSTOM,
            is_public=True,
            default_period=EnumReportPeriod.DAYS_30
        )
        assert template.description == "Test description"
        assert template.report_type == EnumReportType.CUSTOM
        assert template.is_public is True
        assert template.default_period == EnumReportPeriod.DAYS_30

    def test_report_template_create_name_empty_validation_error(self):
        """ReportTemplateCreate.name 빈 문자열 시 ValidationError 확인"""
        from app.schemas.report import ReportTemplateCreate, ReportComponentConfig

        with pytest.raises(ValidationError):
            ReportTemplateCreate(
                name="",
                components=[
                    ReportComponentConfig(id="SUMMARY_CARD", order=1, enabled=True)
                ]
            )


class TestReportTemplateUpdateSchema:
    """Tests for ReportTemplateUpdate schema"""

    def test_report_template_update_all_fields_optional(self):
        """ReportTemplateUpdate의 모든 필드가 Optional인지 확인"""
        from app.schemas.report import ReportTemplateUpdate

        # Empty update should work
        update = ReportTemplateUpdate()
        assert update.name is None
        assert update.components is None
        assert update.description is None

    def test_report_template_update_partial(self):
        """ReportTemplateUpdate 부분 업데이트 가능 확인"""
        from app.schemas.report import ReportTemplateUpdate

        update = ReportTemplateUpdate(name="Updated Name")
        assert update.name == "Updated Name"
        assert update.components is None


class TestReportTemplateResponseSchema:
    """Tests for ReportTemplateResponse schema"""

    def test_report_template_response_has_all_fields(self):
        """ReportTemplateResponse에 모든 필드 포함 확인"""
        from app.schemas.report import ReportTemplateResponse
        from datetime import datetime

        now = datetime.now()
        response = ReportTemplateResponse(
            id=1,
            name="Test Template",
            report_type="CUSTOM",
            owner_id=1,
            is_public=False,
            components=[{"id": "SUMMARY_CARD", "order": 1, "enabled": True}],
            default_period="7d",
            created_at=now,
            updated_at=now
        )
        assert response.id == 1
        assert response.name == "Test Template"
        assert response.report_type == "CUSTOM"
        assert response.created_at == now


class TestReportGenerateRequestSchema:
    """Tests for ReportGenerateRequest schema"""

    def test_report_generate_request_required_fields(self):
        """ReportGenerateRequest에 report_type, title, period_type 필수 필드 확인"""
        from app.schemas.report import ReportGenerateRequest
        from app.utils.enums import EnumReportType, EnumReportPeriod

        request = ReportGenerateRequest(
            report_type=EnumReportType.STANDARD,
            title="Weekly Report",
            period_type=EnumReportPeriod.DAYS_7
        )
        assert request.report_type == EnumReportType.STANDARD
        assert request.title == "Weekly Report"
        assert request.period_type == EnumReportPeriod.DAYS_7

    def test_report_generate_request_optional_fields(self):
        """ReportGenerateRequest에 template_id, severity_filter 선택 필드 확인"""
        from app.schemas.report import ReportGenerateRequest
        from app.utils.enums import EnumReportType, EnumReportPeriod

        request = ReportGenerateRequest(
            report_type=EnumReportType.CUSTOM,
            title="Custom Report",
            period_type=EnumReportPeriod.DAYS_30,
            template_id=1,
            severity_filter=["ERROR", "CRITICAL"]
        )
        assert request.template_id == 1
        assert request.severity_filter == ["ERROR", "CRITICAL"]

    def test_report_generate_request_title_empty_validation_error(self):
        """ReportGenerateRequest.title 빈 문자열 시 ValidationError 확인"""
        from app.schemas.report import ReportGenerateRequest
        from app.utils.enums import EnumReportType, EnumReportPeriod

        with pytest.raises(ValidationError):
            ReportGenerateRequest(
                report_type=EnumReportType.STANDARD,
                title="",
                period_type=EnumReportPeriod.DAYS_7
            )


class TestReportGenerationResponseSchema:
    """Tests for ReportGenerationResponse schema"""

    def test_report_generation_response_has_required_fields(self):
        """ReportGenerationResponse에 필수 필드 포함 확인"""
        from app.schemas.report import ReportGenerationResponse
        from datetime import datetime

        now = datetime.now()
        response = ReportGenerationResponse(
            id=1,
            report_type="STANDARD",
            title="Weekly Report",
            period_type="7d",
            start_date=now,
            end_date=now,
            status="COMPLETED",
            created_at=now
        )
        assert response.id == 1
        assert response.report_type == "STANDARD"
        assert response.status == "COMPLETED"

    def test_report_generation_response_nullable_fields(self):
        """ReportGenerationResponse에 nullable 필드 확인"""
        from app.schemas.report import ReportGenerationResponse
        from datetime import datetime

        now = datetime.now()
        response = ReportGenerationResponse(
            id=1,
            report_type="STANDARD",
            title="Weekly Report",
            period_type="7d",
            start_date=now,
            end_date=now,
            status="PENDING",
            created_at=now,
            template_id=None,
            generator_id=None,
            generator_name=None,
            completed_at=None
        )
        assert response.template_id is None
        assert response.generator_id is None
        assert response.generator_name is None
        assert response.completed_at is None


# ============================================================
# Phase 2: Missing Schemas (PRD Section 5)
# ============================================================

class TestChartDataSchema:
    """Tests for ChartData schema (PRD Section 5)"""

    def test_chart_data_has_labels_and_values(self):
        """ChartData에 labels, values 필수 필드 확인"""
        from app.schemas.report import ChartData

        data = ChartData(
            labels=["정상", "고장", "비활성"],
            values=[145, 3, 2]
        )
        assert data.labels == ["정상", "고장", "비활성"]
        assert data.values == [145, 3, 2]

    def test_chart_data_colors_optional(self):
        """ChartData.colors가 optional인지 확인"""
        from app.schemas.report import ChartData

        data = ChartData(labels=["A"], values=[1])
        assert data.colors is None

        data_with_colors = ChartData(
            labels=["A", "B"],
            values=[1, 2],
            colors=["#4CAF50", "#F44336"]
        )
        assert data_with_colors.colors == ["#4CAF50", "#F44336"]


class TestChartConfigSchema:
    """Tests for ChartConfig schema (PRD Section 5)"""

    def test_chart_config_has_required_fields(self):
        """ChartConfig에 id, title, type, data 필수 필드 확인"""
        from app.schemas.report import ChartConfig, ChartData

        config = ChartConfig(
            id="DEVICE_STATUS_PIE",
            title="장비 상태 분포",
            type="PIE",
            data=ChartData(labels=["정상", "고장"], values=[10, 2])
        )
        assert config.id == "DEVICE_STATUS_PIE"
        assert config.title == "장비 상태 분포"
        assert config.type == "PIE"
        assert len(config.data.labels) == 2


class TestGridConfigSchema:
    """Tests for GridConfig schema (PRD Section 5)"""

    def test_grid_config_has_required_fields(self):
        """GridConfig에 id, title, columns, rows, total_rows 필수 필드 확인"""
        from app.schemas.report import GridConfig

        grid = GridConfig(
            id="DEVICE_GRID",
            title="장비 목록",
            columns=["ID", "유형", "이름", "상태"],
            rows=[[1, "Controller", "CTL-001", "정상"]],
            total_rows=150
        )
        assert grid.id == "DEVICE_GRID"
        assert grid.title == "장비 목록"
        assert len(grid.columns) == 4
        assert len(grid.rows) == 1
        assert grid.total_rows == 150


class TestReportSectionSchema:
    """Tests for ReportSection schema (PRD Section 5)"""

    def test_report_section_has_required_fields(self):
        """ReportSection에 name, title 필수, charts/grids 기본값 빈 배열"""
        from app.schemas.report import ReportSection

        section = ReportSection(name="device", title="장비 현황")
        assert section.name == "device"
        assert section.title == "장비 현황"
        assert section.charts == []
        assert section.grids == []

    def test_report_section_with_charts_and_grids(self):
        """ReportSection에 charts, grids 포함"""
        from app.schemas.report import ReportSection, ChartConfig, ChartData, GridConfig

        section = ReportSection(
            name="device",
            title="장비 현황",
            charts=[
                ChartConfig(
                    id="DEVICE_STATUS_PIE",
                    title="장비 상태",
                    type="PIE",
                    data=ChartData(labels=["A"], values=[1])
                )
            ],
            grids=[
                GridConfig(
                    id="DEVICE_GRID",
                    title="장비 목록",
                    columns=["ID"],
                    rows=[[1]],
                    total_rows=1
                )
            ]
        )
        assert len(section.charts) == 1
        assert len(section.grids) == 1


class TestReportPreviewResponseSchema:
    """Tests for ReportPreviewResponse schema (PRD Section 5)"""

    def test_report_preview_response_has_required_fields(self):
        """ReportPreviewResponse에 id, title, period_type, sections 필수 필드"""
        from app.schemas.report import ReportPreviewResponse
        from datetime import datetime

        now = datetime.now()
        preview = ReportPreviewResponse(
            id=1,
            title="주간 보고서",
            period_type="7d",
            start_date=now,
            end_date=now,
            sections=[]
        )
        assert preview.id == 1
        assert preview.title == "주간 보고서"
        assert preview.sections == []

    def test_report_preview_response_optional_fields(self):
        """ReportPreviewResponse에 generator_name, generator_department optional"""
        from app.schemas.report import ReportPreviewResponse
        from datetime import datetime

        now = datetime.now()
        preview = ReportPreviewResponse(
            id=1,
            title="주간 보고서",
            period_type="7d",
            start_date=now,
            end_date=now,
            sections=[],
            generator_name="홍길동",
            generator_department="운영팀"
        )
        assert preview.generator_name == "홍길동"
        assert preview.generator_department == "운영팀"


class TestComponentInfoSchema:
    """Tests for ComponentInfo schema (PRD Section 5)"""

    def test_component_info_has_required_fields(self):
        """ComponentInfo에 id, label, description, chart_type, category 필드"""
        from app.schemas.report import ComponentInfo

        info = ComponentInfo(
            id="DEVICE_STATUS_PIE",
            label="장비 상태 파이차트",
            description="정상/고장/비활성 분포",
            chart_type="PIE",
            category="DEVICE"
        )
        assert info.id == "DEVICE_STATUS_PIE"
        assert info.chart_type == "PIE"
        assert info.category == "DEVICE"

    def test_component_info_chart_type_optional(self):
        """ComponentInfo.chart_type이 optional (Grid의 경우 None)"""
        from app.schemas.report import ComponentInfo

        info = ComponentInfo(
            id="DEVICE_GRID",
            label="장비 목록",
            description="장비 상세 목록",
            category="DEVICE"
        )
        assert info.chart_type is None


class TestComponentCategoryResponseSchema:
    """Tests for ComponentCategoryResponse schema (PRD Section 5)"""

    def test_component_category_response_has_fields(self):
        """ComponentCategoryResponse에 name, label, components 필드"""
        from app.schemas.report import ComponentCategoryResponse, ComponentInfo

        category = ComponentCategoryResponse(
            name="DEVICE",
            label="장비",
            components=[
                ComponentInfo(
                    id="DEVICE_STATUS_PIE",
                    label="장비 상태 파이차트",
                    description="분포",
                    chart_type="PIE",
                    category="DEVICE"
                )
            ]
        )
        assert category.name == "DEVICE"
        assert category.label == "장비"
        assert len(category.components) == 1


class TestReportTemplateListResponseSchema:
    """Tests for ReportTemplateListResponse schema (PRD Section 5)"""

    def test_report_template_list_response_has_component_count(self):
        """ReportTemplateListResponse에 component_count 필드 포함"""
        from app.schemas.report import ReportTemplateListResponse
        from datetime import datetime

        response = ReportTemplateListResponse(
            id=1,
            name="주간 보고서",
            report_type="CUSTOM",
            owner_id=1,
            is_public=True,
            component_count=10,
            default_period="7d",
            created_at=datetime.now()
        )
        assert response.component_count == 10
        assert response.name == "주간 보고서"


class TestReportGenerationListResponseSchema:
    """Tests for ReportGenerationListResponse schema (PRD Section 5)"""

    def test_report_generation_list_response_has_required_fields(self):
        """ReportGenerationListResponse에 경량 필드만 포함"""
        from app.schemas.report import ReportGenerationListResponse
        from datetime import datetime

        now = datetime.now()
        response = ReportGenerationListResponse(
            id=1,
            report_type="STANDARD",
            title="주간 보고서",
            period_type="7d",
            status="COMPLETED",
            created_at=now
        )
        assert response.id == 1
        assert response.status == "COMPLETED"

    def test_report_generation_list_response_optional_fields(self):
        """ReportGenerationListResponse에 generator_name, completed_at optional"""
        from app.schemas.report import ReportGenerationListResponse
        from datetime import datetime

        now = datetime.now()
        response = ReportGenerationListResponse(
            id=1,
            report_type="STANDARD",
            title="주간 보고서",
            period_type="7d",
            status="COMPLETED",
            created_at=now,
            generator_name="홍길동",
            completed_at=now
        )
        assert response.generator_name == "홍길동"
        assert response.completed_at is not None
