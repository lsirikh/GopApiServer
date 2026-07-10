"""
Tests for Report System Models
TDD: Test First
PRD: PRD_Report_System.md Section 4
"""
import pytest
from sqlalchemy import inspect


class TestReportTemplateModel:
    """Tests for ReportTemplate model"""

    def test_report_template_model_exists(self):
        """ReportTemplate 모델이 존재하는지 확인"""
        from app.models.report import ReportTemplate
        assert ReportTemplate is not None

    def test_report_template_tablename(self):
        """테이블명이 report_templates인지 확인"""
        from app.models.report import ReportTemplate
        assert ReportTemplate.__tablename__ == "report_templates"

    def test_report_template_has_required_columns(self):
        """필수 컬럼들이 존재하는지 확인 (id, name, report_type, components, created_at, updated_at)"""
        from app.models.report import ReportTemplate
        mapper = inspect(ReportTemplate)
        columns = [col.key for col in mapper.columns]

        required_columns = ["id", "name", "report_type", "components", "created_at", "updated_at"]
        for col in required_columns:
            assert col in columns, f"{col} should be in ReportTemplate"

    def test_report_template_description_nullable(self):
        """ReportTemplate.description이 nullable인지 확인"""
        from app.models.report import ReportTemplate
        mapper = inspect(ReportTemplate)
        description_col = mapper.columns["description"]
        assert description_col.nullable is True

    def test_report_template_owner_id_fk(self):
        """ReportTemplate.owner_id가 account_users.id를 참조하는지 확인"""
        from app.models.report import ReportTemplate
        mapper = inspect(ReportTemplate)
        owner_id_col = mapper.columns["owner_id"]
        fks = list(owner_id_col.foreign_keys)
        assert len(fks) == 1
        assert fks[0].target_fullname == "account_users.id"

    def test_report_template_is_public_default(self):
        """ReportTemplate.is_public이 Boolean이고 default=False인지 확인"""
        from app.models.report import ReportTemplate
        mapper = inspect(ReportTemplate)
        is_public_col = mapper.columns["is_public"]
        assert is_public_col.default.arg is False
        assert is_public_col.nullable is False

    def test_report_template_default_period_default(self):
        """ReportTemplate.default_period이 String이고 default='7d'인지 확인"""
        from app.models.report import ReportTemplate
        mapper = inspect(ReportTemplate)
        default_period_col = mapper.columns["default_period"]
        assert default_period_col.default.arg == "7d"


class TestReportGenerationModel:
    """Tests for ReportGeneration model"""

    def test_report_generation_model_exists(self):
        """ReportGeneration 모델이 존재하는지 확인"""
        from app.models.report import ReportGeneration
        assert ReportGeneration is not None

    def test_report_generation_tablename(self):
        """테이블명이 report_generations인지 확인"""
        from app.models.report import ReportGeneration
        assert ReportGeneration.__tablename__ == "report_generations"

    def test_report_generation_has_required_columns(self):
        """필수 컬럼들이 존재하는지 확인"""
        from app.models.report import ReportGeneration
        mapper = inspect(ReportGeneration)
        columns = [col.key for col in mapper.columns]

        required_columns = [
            "id", "report_type", "title", "period_type",
            "start_date", "end_date", "status", "created_at"
        ]
        for col in required_columns:
            assert col in columns, f"{col} should be in ReportGeneration"

    def test_report_generation_template_id_fk(self):
        """ReportGeneration.template_id가 report_templates.id를 참조하는지 확인"""
        from app.models.report import ReportGeneration
        mapper = inspect(ReportGeneration)
        template_id_col = mapper.columns["template_id"]
        fks = list(template_id_col.foreign_keys)
        assert len(fks) == 1
        assert fks[0].target_fullname == "report_templates.id"
        assert template_id_col.nullable is True

    def test_report_generation_generator_id_fk(self):
        """ReportGeneration.generator_id가 account_users.id를 참조하는지 확인"""
        from app.models.report import ReportGeneration
        mapper = inspect(ReportGeneration)
        generator_id_col = mapper.columns["generator_id"]
        fks = list(generator_id_col.foreign_keys)
        assert len(fks) == 1
        assert fks[0].target_fullname == "account_users.id"
        assert generator_id_col.nullable is True

    def test_report_generation_generator_snapshot_fields(self):
        """ReportGeneration.generator_name, generator_department이 nullable인지 확인"""
        from app.models.report import ReportGeneration
        mapper = inspect(ReportGeneration)

        generator_name_col = mapper.columns["generator_name"]
        assert generator_name_col.nullable is True

        generator_department_col = mapper.columns["generator_department"]
        assert generator_department_col.nullable is True

    def test_report_generation_json_fields_nullable(self):
        """ReportGeneration.severity_filter, summary_data가 JSON이고 nullable인지 확인"""
        from app.models.report import ReportGeneration
        mapper = inspect(ReportGeneration)

        severity_filter_col = mapper.columns["severity_filter"]
        assert severity_filter_col.nullable is True

        summary_data_col = mapper.columns["summary_data"]
        assert summary_data_col.nullable is True

    def test_report_generation_file_fields_nullable(self):
        """ReportGeneration.pdf_file_path, pdf_file_size가 nullable인지 확인"""
        from app.models.report import ReportGeneration
        mapper = inspect(ReportGeneration)

        pdf_file_path_col = mapper.columns["pdf_file_path"]
        assert pdf_file_path_col.nullable is True

        pdf_file_size_col = mapper.columns["pdf_file_size"]
        assert pdf_file_size_col.nullable is True

    def test_report_generation_completed_at_nullable(self):
        """ReportGeneration.completed_at이 nullable인지 확인 (updated_at 없음)"""
        from app.models.report import ReportGeneration
        mapper = inspect(ReportGeneration)
        columns = [col.key for col in mapper.columns]

        # completed_at is nullable
        completed_at_col = mapper.columns["completed_at"]
        assert completed_at_col.nullable is True

        # updated_at should NOT exist
        assert "updated_at" not in columns, "updated_at should NOT be in ReportGeneration"

    def test_report_generation_status_default(self):
        """ReportGeneration.status가 default='PENDING'인지 확인"""
        from app.models.report import ReportGeneration
        mapper = inspect(ReportGeneration)
        status_col = mapper.columns["status"]
        assert status_col.default.arg == "PENDING"


class TestUserReportRelationships:
    """Tests for User model Report relationships"""

    def test_user_has_report_templates_relationship(self):
        """AccountUser.report_templates relationship이 존재하는지 확인"""
        from app.models.user import AccountUser
        mapper = inspect(AccountUser)
        relationships = [rel.key for rel in mapper.relationships]
        assert "report_templates" in relationships

    def test_user_has_report_generations_relationship(self):
        """AccountUser.report_generations relationship이 존재하는지 확인"""
        from app.models.user import AccountUser
        mapper = inspect(AccountUser)
        relationships = [rel.key for rel in mapper.relationships]
        assert "report_generations" in relationships
