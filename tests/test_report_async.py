"""
Tests for Async Report Generation
PRD: PRD_Report_System.md - Phase 2: 서비스 로직 (Async)
TDD: Red -> Green -> Refactor
"""
import pytest
import os
import time
from datetime import datetime, timedelta


class TestReportServiceGenerateReportAsync:
    """RS-11.1: generate_report_async 메서드 테스트"""

    def test_generate_report_async_method_exists(self):
        """generate_report_async 메서드가 존재해야 함"""
        from app.services.report_service import ReportService

        assert hasattr(ReportService, 'generate_report_async')

    def test_generate_report_async_changes_status_to_generating(self, test_db):
        """generate_report_async가 status를 GENERATING으로 변경해야 함"""
        from app.services.report_service import ReportService
        from app.models.report import ReportGeneration

        # Create a PENDING generation
        generation = ReportGeneration(
            report_type="STANDARD",
            title="Test Report",
            period_type="7d",
            start_date=datetime.now() - timedelta(days=7),
            end_date=datetime.now(),
            status="PENDING"
        )
        test_db.add(generation)
        test_db.commit()
        test_db.refresh(generation)

        generation_id = generation.id

        # Call generate_report_async (synchronous part)
        service = ReportService(test_db)
        service.generate_report_async(generation_id)

        # Refresh and check status
        test_db.refresh(generation)
        # Status should be either GENERATING or COMPLETED (if fast enough)
        assert generation.status in ["GENERATING", "COMPLETED"]


class TestReportServicePDFGeneration:
    """RS-11.2: PDF 생성 및 상태 업데이트 테스트"""

    def test_generate_report_async_completes_with_status_completed(self, test_db):
        """generate_report_async 완료 시 status가 COMPLETED여야 함"""
        from app.services.report_service import ReportService
        from app.models.report import ReportGeneration

        generation = ReportGeneration(
            report_type="STANDARD",
            title="Completed Test Report",
            period_type="7d",
            start_date=datetime.now() - timedelta(days=7),
            end_date=datetime.now(),
            status="PENDING"
        )
        test_db.add(generation)
        test_db.commit()
        test_db.refresh(generation)

        generation_id = generation.id

        service = ReportService(test_db)
        service.generate_report_async(generation_id)

        test_db.refresh(generation)
        assert generation.status == "COMPLETED"

    def test_generate_report_async_sets_pdf_file_path(self, test_db):
        """generate_report_async 완료 시 pdf_file_path가 설정되어야 함"""
        from app.services.report_service import ReportService
        from app.models.report import ReportGeneration

        generation = ReportGeneration(
            report_type="STANDARD",
            title="PDF Path Test Report",
            period_type="7d",
            start_date=datetime.now() - timedelta(days=7),
            end_date=datetime.now(),
            status="PENDING"
        )
        test_db.add(generation)
        test_db.commit()
        test_db.refresh(generation)

        generation_id = generation.id

        service = ReportService(test_db)
        service.generate_report_async(generation_id)

        test_db.refresh(generation)
        assert generation.pdf_file_path is not None
        assert generation.pdf_file_path.endswith('.pdf')

    def test_generate_report_async_sets_completed_at(self, test_db):
        """generate_report_async 완료 시 completed_at이 설정되어야 함"""
        from app.services.report_service import ReportService
        from app.models.report import ReportGeneration

        generation = ReportGeneration(
            report_type="STANDARD",
            title="Timestamp Test Report",
            period_type="7d",
            start_date=datetime.now() - timedelta(days=7),
            end_date=datetime.now(),
            status="PENDING"
        )
        test_db.add(generation)
        test_db.commit()
        test_db.refresh(generation)

        generation_id = generation.id

        service = ReportService(test_db)
        service.generate_report_async(generation_id)

        test_db.refresh(generation)
        assert generation.completed_at is not None

    def test_generate_report_async_sets_summary_data(self, test_db):
        """generate_report_async 완료 시 summary_data가 설정되어야 함"""
        from app.services.report_service import ReportService
        from app.models.report import ReportGeneration

        generation = ReportGeneration(
            report_type="STANDARD",
            title="Summary Data Test Report",
            period_type="7d",
            start_date=datetime.now() - timedelta(days=7),
            end_date=datetime.now(),
            status="PENDING"
        )
        test_db.add(generation)
        test_db.commit()
        test_db.refresh(generation)

        generation_id = generation.id

        service = ReportService(test_db)
        service.generate_report_async(generation_id)

        test_db.refresh(generation)
        assert generation.summary_data is not None

    def test_generate_report_async_creates_pdf_file(self, test_db):
        """generate_report_async가 실제 PDF 파일을 생성해야 함"""
        from app.services.report_service import ReportService
        from app.models.report import ReportGeneration

        generation = ReportGeneration(
            report_type="STANDARD",
            title="File Creation Test",
            period_type="7d",
            start_date=datetime.now() - timedelta(days=7),
            end_date=datetime.now(),
            status="PENDING"
        )
        test_db.add(generation)
        test_db.commit()
        test_db.refresh(generation)

        generation_id = generation.id

        service = ReportService(test_db)
        service.generate_report_async(generation_id)

        test_db.refresh(generation)

        # Check file exists
        if generation.pdf_file_path:
            assert os.path.exists(generation.pdf_file_path)
            # Cleanup
            os.remove(generation.pdf_file_path)


class TestReportAsyncPDFTables:
    """Phase 7: PDF에 테이블 데이터가 포함되는지 검증"""

    def test_generate_report_async_summary_includes_user_stats(self, test_db):
        """generate_report_async 완료 시 summary_data에 user_stats가 포함되어야 함"""
        from app.services.report_service import ReportService
        from app.models.report import ReportGeneration

        generation = ReportGeneration(
            report_type="STANDARD",
            title="User Stats Test",
            period_type="7d",
            start_date=datetime.now() - timedelta(days=7),
            end_date=datetime.now(),
            status="PENDING"
        )
        test_db.add(generation)
        test_db.commit()
        test_db.refresh(generation)

        service = ReportService(test_db)
        service.generate_report_async(generation.id)

        test_db.refresh(generation)
        assert generation.status == "COMPLETED"
        assert "user_stats" in generation.summary_data

    def test_generate_report_async_summary_includes_grid_counts(self, test_db):
        """generate_report_async 완료 시 summary_data에 grid_counts가 포함되어야 함"""
        from app.services.report_service import ReportService
        from app.models.report import ReportGeneration

        generation = ReportGeneration(
            report_type="STANDARD",
            title="Grid Counts Test",
            period_type="7d",
            start_date=datetime.now() - timedelta(days=7),
            end_date=datetime.now(),
            status="PENDING"
        )
        test_db.add(generation)
        test_db.commit()
        test_db.refresh(generation)

        service = ReportService(test_db)
        service.generate_report_async(generation.id)

        test_db.refresh(generation)
        assert generation.status == "COMPLETED"
        # summary_data should include table/grid counts
        assert "grid_counts" in generation.summary_data

    def test_generate_report_async_pdf_includes_device_table(self, test_db):
        """generate_report_async가 장비 목록 테이블을 포함하는 PDF를 생성해야 함"""
        from app.services.report_service import ReportService
        from app.models.report import ReportGeneration

        generation = ReportGeneration(
            report_type="STANDARD",
            title="Device Table Test",
            period_type="7d",
            start_date=datetime.now() - timedelta(days=7),
            end_date=datetime.now(),
            status="PENDING"
        )
        test_db.add(generation)
        test_db.commit()
        test_db.refresh(generation)

        service = ReportService(test_db)
        service.generate_report_async(generation.id)

        test_db.refresh(generation)
        assert generation.status == "COMPLETED"
        assert generation.pdf_file_path is not None
        # PDF file should exist and have content
        assert os.path.exists(generation.pdf_file_path)
        file_size = os.path.getsize(generation.pdf_file_path)
        assert file_size > 0
        # grid_counts should include device table count
        assert generation.summary_data["grid_counts"]["device_grid"] >= 0
        # Cleanup
        os.remove(generation.pdf_file_path)


class TestReportServiceErrorHandling:
    """RS-11.2: 에러 처리 테스트"""

    def test_generate_report_async_handles_invalid_generation_id(self, test_db):
        """존재하지 않는 generation_id로 호출 시 에러 없이 처리"""
        from app.services.report_service import ReportService

        service = ReportService(test_db)
        # Should not raise exception
        service.generate_report_async(99999)


class TestBackgroundTasksIntegration:
    """RS-11.3: BackgroundTasks 연동 테스트"""

    def test_post_generate_includes_background_tasks_param(self):
        """POST /api/reports/generate 엔드포인트가 BackgroundTasks 파라미터를 가져야 함"""
        import inspect
        from app.routers.reports import generate_report

        sig = inspect.signature(generate_report)
        param_names = list(sig.parameters.keys())

        assert 'background_tasks' in param_names

    def test_run_report_generation_function_exists(self):
        """_run_report_generation 함수가 존재해야 함"""
        from app.routers.reports import _run_report_generation

        assert _run_report_generation is not None
        assert callable(_run_report_generation)


@pytest.fixture
def test_db():
    """테스트용 DB 세션"""
    from app.database import SessionLocal, engine, Base

    # Create tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
