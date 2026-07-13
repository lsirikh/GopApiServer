"""
Tests for Report PDF ↔ Preview Data Sync
PRD: PRD_Report_PDF_Preview_Sync.md
TDD Plan: plan.md Phase 1~11
"""
import pytest
from enum import Enum as PyEnum
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import *  # noqa


TEST_DATABASE_URL = "sqlite:///./test_report_pdf_sync.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


# ============================================================
# Phase 1: Enum .value 변환 — get_device_statistics()
# ============================================================

class TestPhase1_DeviceStatusEnumValue:
    """Phase 1.1: status_counts 키가 순수 문자열이어야 함 (Enum 객체 아님)"""

    def test_status_counts_keys_are_plain_strings_not_enum(self, db):
        """
        status_counts 키가 Enum 객체가 아닌 순수 str이어야 한다.
        isinstance(key, str)은 str,Enum 서브클래스도 통과하므로
        type(key) is str로 검증한다.

        현재 코드(report_service.py:90): status_counts[status] = count
        → status는 EnumDeviceStatus 객체 → str(status) = "EnumDeviceStatus.ACTIVATED"
        → 차트 레이블이 "EnumDeviceStatus.ACTIVATED"로 렌더링되는 버그
        """
        from app.services.report_service import ReportService
        from app.models.device import Controller
        from app.utils.enums import EnumDeviceCategory, EnumDeviceType, EnumDeviceStatus

        device = Controller(
            category_device=EnumDeviceCategory.CONTROLLER,
            type_device=EnumDeviceType.Controller,
            number_device=888, group_device=0,
            name_device="EnumTest장비",
            status=EnumDeviceStatus.ACTIVATED,
            ip_address="10.0.0.88", ip_port=8080,
        )
        db.add(device)
        db.commit()

        try:
            service = ReportService(db)
            result = service.get_device_statistics()

            for key in result["status_counts"].keys():
                # Enum 서브클래스가 아니어야 함
                assert not isinstance(key, PyEnum), (
                    f"status_counts key should not be Enum, "
                    f"got {type(key).__name__}: {key!r}"
                )
                # str()이 "Enum" 접두사를 포함하면 안됨
                assert "Enum" not in str(key), (
                    f"status_counts key str() should not contain 'Enum', "
                    f"got: '{str(key)}'"
                )
        finally:
            db.delete(device)
            db.commit()


# ============================================================
# Phase 2: Enum .value 변환 — get_config_grid_data()
# ============================================================

class TestPhase2_ConfigGridEnumValue:
    """Phase 2.1: config grid rows의 resource_type/action이 Enum 접두사 없는 문자열이어야 함"""

    def test_config_grid_rows_no_enum_prefix(self, db):
        """
        get_config_grid_data() rows에서 resource_type(index 2), action(index 3) 셀이
        "Enum" 접두사를 포함하지 않아야 한다.

        현재 코드(report_service.py:502-503):
        log.resource_type or "" → Enum 객체 그대로 → str() = "EnumConfigResourceType.XXX"
        """
        from app.services.report_service import ReportService
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

        log = ConfigChangeLog(
            resource_type=EnumConfigResourceType.EVENT_MAPPING_CAMERA,
            action=EnumConfigActionType.UPDATED,
            resource_id=1,
            description="테스트 변경",
        )
        db.add(log)
        db.commit()

        try:
            service = ReportService(db)
            result = service.get_config_grid_data(days=30)

            assert result["total_rows"] >= 1
            for row in result["rows"]:
                if row[0] == log.id:
                    # resource_type (index 2)
                    assert "Enum" not in str(row[2]), (
                        f"resource_type should not contain 'Enum', got: '{row[2]}'"
                    )
                    # action (index 3)
                    assert "Enum" not in str(row[3]), (
                        f"action should not contain 'Enum', got: '{row[3]}'"
                    )
                    break
            else:
                pytest.fail(f"Log {log.id} not found in config grid rows")
        finally:
            db.delete(log)
            db.commit()


# ============================================================
# Phase 3: 요약 텍스트 줄바꿈 (\n → <br/>)
# ============================================================

class TestPhase3_SummaryLineBreak:
    """Phase 3.1: PDF 요약 섹션 content에 <br/> 태그가 사용되어야 함"""

    def test_summary_content_uses_br_tags_not_newlines(self, db):
        """
        generate_report_async()가 PDFGenerator에 전달하는 요약 content에
        \\n 대신 <br/> 태그가 있어야 한다.

        현재 코드(report_service.py:1043-1050): \\n 사용 → reportlab Paragraph가 무시
        """
        from app.services.report_service import ReportService
        from app.models.report import ReportGeneration

        now = datetime.now()
        generation = ReportGeneration(
            report_type="WEEKLY",
            title="테스트 보고서",
            period_type="WEEKLY",
            start_date=now - timedelta(days=7),
            end_date=now,
            status="PENDING",
        )
        db.add(generation)
        db.commit()

        try:
            with patch(
                'app.utils.pdf_generator.PDFGenerator.generate_report',
                return_value=b'%PDF-fake'
            ) as mock_generate, patch(
                'app.utils.chart_generator.ChartGenerator.generate_pie_chart',
                return_value=b'PNG-fake'
            ), patch(
                'app.utils.chart_generator.ChartGenerator.generate_bar_chart',
                return_value=b'PNG-fake'
            ), patch(
                'app.utils.chart_generator.ChartGenerator.generate_donut_chart',
                return_value=b'PNG-fake'
            ), patch(
                'app.utils.chart_generator.ChartGenerator.generate_line_chart',
                return_value=b'PNG-fake'
            ):

                service = ReportService(db)
                service.generate_report_async(generation.id)

                db.refresh(generation)

                # 에러가 있으면 디버그용으로 출력
                if generation.status == "FAILED":
                    pytest.fail(
                        f"generate_report_async failed: {generation.error_message}"
                    )

                # PDFGenerator.generate_report가 호출되었는지 확인
                assert mock_generate.called, (
                    "PDFGenerator.generate_report was not called"
                )

                # sections 인수 캡처
                call_kwargs = mock_generate.call_args
                sections = call_kwargs.kwargs.get('sections', [])

                # 요약 섹션 찾기
                summary_section = None
                for s in sections:
                    if 'content' in s:
                        summary_section = s
                        break

                assert summary_section is not None, (
                    f"No summary section with 'content' found in sections: "
                    f"{[s.get('title') for s in sections]}"
                )

                content = summary_section['content']
                # content에 \n이 있으면 안되고 <br/>가 있어야 함
                assert '\n' not in content, (
                    f"Summary content should not contain \\n, got: {content!r}"
                )
                assert '<br/>' in content, (
                    f"Summary content should contain <br/> tags, got: {content!r}"
                )
        finally:
            db.refresh(generation)
            db.delete(generation)
            db.commit()


# ============================================================
# Phase 4~8: 누락 차트 5건 추가
# ============================================================

def _run_generate_and_capture_sections(db):
    """generate_report_async 실행 후 PDFGenerator에 전달된 sections 캡처 헬퍼.
    차트 생성 조건 충족을 위해 샘플 데이터를 삽입한다."""
    from app.services.report_service import ReportService
    from app.models.report import ReportGeneration
    from app.models.system_event import SystemEvent
    from app.models.user import AccountUser, UserLoginLog
    from app.utils.enums import EnumSystemEventType, EnumSystemEventSeverity

    now = datetime.now()

    # 샘플 데이터 (차트 생성 조건 충족용)
    se = SystemEvent(
        type_event=EnumSystemEventType.RESOURCE_THRESHOLD,
        severity=EnumSystemEventSeverity.WARNING,
        title="테스트 시스템 이벤트",
    )
    db.add(se)
    db.flush()

    user = AccountUser(
        login_id=f"chart_test_{now.timestamp()}",
        password_hash="fakehash",
        name="차트테스트",
        role="ADMIN",
    )
    db.add(user)
    db.flush()

    login_log = UserLoginLog(
        user_id=user.id,
        login_id=user.login_id,
        action="LOGIN",
        result="SUCCESS",
    )
    db.add(login_log)

    generation = ReportGeneration(
        report_type="WEEKLY",
        title="차트테스트 보고서",
        period_type="WEEKLY",
        start_date=now - timedelta(days=7),
        end_date=now,
        status="PENDING",
    )
    db.add(generation)
    db.commit()

    sections = []
    try:
        with patch(
            'app.utils.pdf_generator.PDFGenerator.generate_report',
            return_value=b'%PDF-fake'
        ) as mock_generate, patch(
            'app.utils.chart_generator.ChartGenerator.generate_pie_chart',
            return_value=b'PNG-fake'
        ), patch(
            'app.utils.chart_generator.ChartGenerator.generate_bar_chart',
            return_value=b'PNG-fake'
        ), patch(
            'app.utils.chart_generator.ChartGenerator.generate_donut_chart',
            return_value=b'PNG-fake'
        ), patch(
            'app.utils.chart_generator.ChartGenerator.generate_line_chart',
            return_value=b'PNG-fake'
        ):
            service = ReportService(db)
            service.generate_report_async(generation.id)

            db.refresh(generation)
            if generation.status == "FAILED":
                raise RuntimeError(f"generate_report_async failed: {generation.error_message}")

            if mock_generate.called:
                sections = mock_generate.call_args.kwargs.get('sections', [])
    finally:
        db.refresh(generation)
        db.delete(generation)
        db.delete(login_log)
        db.delete(user)
        db.delete(se)
        db.commit()

    return sections


class TestPhase4_EventTrendLineChart:
    """Phase 4: PDF에 '이벤트 발생 추이' 차트 포함 확인"""

    def test_pdf_contains_event_trend_chart(self, db):
        """
        generate_report_async() 후 sections에 이벤트 발생 추이 차트가 있어야 한다.
        RED: 현재 4개 차트만 생성 (DEVICE_STATUS_PIE, DEVICE_TYPE_BAR, EVENT_SUMMARY_PIE, SYSTEM_SEVERITY_BAR)
        """
        sections = _run_generate_and_capture_sections(db)
        titles = [s.get('title', '') for s in sections]
        assert any('이벤트' in t and '추이' in t for t in titles), (
            f"Expected '이벤트 발생 추이' chart in sections, got titles: {titles}"
        )


class TestPhase5_SystemTrendLineChart:
    """Phase 5: PDF에 '시스템 이벤트 추이' 차트 포함 확인"""

    def test_pdf_contains_system_trend_chart(self, db):
        sections = _run_generate_and_capture_sections(db)
        titles = [s.get('title', '') for s in sections]
        assert any('시스템' in t and '추이' in t for t in titles), (
            f"Expected '시스템 이벤트 추이' chart in sections, got titles: {titles}"
        )


class TestPhase6_UserRolePieChart:
    """Phase 6: PDF에 '역할별 사용자 분포' 차트 포함 확인"""

    def test_pdf_contains_user_role_chart(self, db):
        sections = _run_generate_and_capture_sections(db)
        titles = [s.get('title', '') for s in sections]
        assert any('역할' in t and '사용자' in t for t in titles), (
            f"Expected '역할별 사용자 분포' chart in sections, got titles: {titles}"
        )


class TestPhase7_UserLoginTrendLineChart:
    """Phase 7: PDF에 '일별 로그인 추이' 차트 포함 확인"""

    def test_pdf_contains_user_login_trend_chart(self, db):
        sections = _run_generate_and_capture_sections(db)
        titles = [s.get('title', '') for s in sections]
        assert any('로그인' in t and '추이' in t for t in titles), (
            f"Expected '일별 로그인 추이' chart in sections, got titles: {titles}"
        )


class TestPhase8_UserLoginResultPieChart:
    """Phase 8: PDF에 '로그인 결과 분포' 차트 포함 확인"""

    def test_pdf_contains_user_login_result_chart(self, db):
        sections = _run_generate_and_capture_sections(db)
        titles = [s.get('title', '') for s in sections]
        assert any('로그인' in t and '결과' in t for t in titles), (
            f"Expected '로그인 결과 분포' chart in sections, got titles: {titles}"
        )


# ============================================================
# Phase 9: 테이블 오버플로 수정
# ============================================================

class TestPhase9_TableOverflow:
    """Phase 9: _build_table()이 colWidths 지정 + Paragraph 래핑 확인"""

    def test_build_table_has_col_widths(self):
        """
        _build_table()이 반환하는 Table에 colWidths가 지정되어 있어야 한다.
        RED: 현재 Table(data)에 colWidths 미지정 → A4 폭 초과
        """
        from app.utils.pdf_generator import PDFGenerator
        from reportlab.platypus import Table

        table_data = {
            "headers": ["ID", "일시", "유형", "장비명", "상태"],
            "rows": [
                [1, "2026-02-12", "controller", "테스트장비", "ACTIVATED"],
                [2, "2026-02-12", "camera", "카메라01", "ERROR"],
            ]
        }
        elements = PDFGenerator._build_table(table_data)

        # Table 요소 찾기
        table_elem = None
        for elem in elements:
            if isinstance(elem, Table):
                table_elem = elem
                break

        assert table_elem is not None, "No Table element found"
        assert table_elem._colWidths is not None, (
            "Table should have colWidths set to prevent overflow"
        )
        assert len(table_elem._colWidths) == 5, (
            f"Expected 5 colWidths, got {len(table_elem._colWidths)}"
        )
        # colWidths가 실제 숫자여야 함 (None이면 auto-size → overflow 가능)
        for w in table_elem._colWidths:
            assert w is not None and isinstance(w, (int, float)), (
                f"colWidth should be a number, got {w!r}"
            )

    def test_build_table_cells_are_paragraphs(self):
        """
        테이블 셀이 Paragraph로 래핑되어 있어야 한다 (긴 텍스트 자동 줄바꿈).
        RED: 현재 셀이 plain string → 줄바꿈 안됨
        """
        from app.utils.pdf_generator import PDFGenerator
        from reportlab.platypus import Table, Paragraph

        table_data = {
            "headers": ["ID", "설명"],
            "rows": [
                [1, "이것은 매우 긴 텍스트입니다 테이블 셀에서 자동 줄바꿈이 되어야 합니다"],
            ]
        }
        elements = PDFGenerator._build_table(table_data)

        table_elem = None
        for elem in elements:
            if isinstance(elem, Table):
                table_elem = elem
                break

        assert table_elem is not None
        # 데이터 행의 셀이 Paragraph여야 함
        data_rows = table_elem._cellvalues
        # data_rows[0]은 헤더, data_rows[1]은 첫 번째 데이터 행
        if len(data_rows) > 1:
            for cell in data_rows[1]:
                assert isinstance(cell, Paragraph), (
                    f"Table cell should be Paragraph, got {type(cell).__name__}: {cell}"
                )


# ============================================================
# Phase 10: 섹션 번호 부여
# ============================================================

class TestPhase10_SectionNumbering:
    """Phase 10: PDF sections 제목에 순번 포함 확인"""

    def test_all_sections_have_numbering(self, db):
        """
        generate_report_async() 후 모든 sections 제목이 "N. 제목" 형식이어야 한다.
        RED: 현재 "1. 요약"만 번호 있고, 나머지 차트/테이블은 번호 없음
        """
        import re
        sections = _run_generate_and_capture_sections(db)

        assert len(sections) > 1, "Need at least 2 sections for numbering test"

        for i, section in enumerate(sections):
            title = section.get('title', '')
            # "N. " 패턴으로 시작해야 함
            assert re.match(r'^\d+\.\s', title), (
                f"Section {i} title should start with 'N. ', got: '{title}'"
            )
