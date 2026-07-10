"""
Tests for PDF Korean Font Fix
PRD: PRD_Report_PDF_Korean_Fix.md
TDD: Red -> Green -> Refactor
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base
from app.dependencies import get_db
from app.models.report import ReportGeneration


# Test database setup (same pattern as test_reports_router.py)
TEST_DATABASE_URL = "sqlite:///./test_pdf_korean.db"
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
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    import os
    if os.path.exists("./test_pdf_korean.db"):
        try:
            os.remove("./test_pdf_korean.db")
        except PermissionError:
            pass


@pytest.fixture(scope="function")
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.query(ReportGeneration).delete()
        session.commit()
        session.close()


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    return TestClient(app)


class TestPDFRegisterFonts:
    """Phase 1.1: _register_fonts() 한글 폰트 등록 검증"""

    def test_register_fonts_adds_malgun_gothic(self):
        """_register_fonts() 호출 후 MalgunGothic이 reportlab에 등록되어야 함"""
        from app.utils.pdf_generator import PDFGenerator
        from reportlab.pdfbase.pdfmetrics import getRegisteredFontNames

        PDFGenerator._register_fonts()

        registered = list(getRegisteredFontNames())
        assert 'MalgunGothic' in registered


class TestPDFStylesKoreanFont:
    """Phase 1.3: _get_styles() 한글 폰트 적용 검증"""

    def test_all_styles_use_malgun_gothic_font(self):
        """_get_styles() 반환 스타일 4개에 fontName='MalgunGothic'이 적용되어야 함"""
        from app.utils.pdf_generator import PDFGenerator

        PDFGenerator._register_fonts()
        styles = PDFGenerator._get_styles()

        style_names = ['ReportTitle', 'ReportSubtitle', 'SectionTitle', 'SectionContent']
        for name in style_names:
            assert styles[name].fontName == 'MalgunGothic', f"{name} fontName should be MalgunGothic"


class TestPDFKoreanEmbedding:
    """Phase 1.5: 한글 PDF 생성 시 폰트 임베딩 검증"""

    def test_generated_pdf_embeds_malgun_gothic_font(self):
        """한글 제목+내용+테이블 포함 PDF 생성 시 MalgunGothic 폰트가 임베딩되어야 함"""
        from app.utils.pdf_generator import PDFGenerator

        sections = [
            {"title": "장비 현황", "content": "온라인 장비 50대, 오프라인 10대"},
            {
                "title": "이벤트 목록",
                "table": {
                    "headers": ["일자", "유형", "건수"],
                    "rows": [["2026-01-01", "탐지", "10"]]
                }
            }
        ]

        result = PDFGenerator.generate_report(
            title="주간 운영 보고서",
            period="2026-01-01 ~ 2026-01-07",
            generator_name="홍길동",
            generator_department="운영팀",
            sections=sections
        )

        assert result[:5] == b'%PDF-'
        assert b'MalgunGothic' in result


class TestMatplotlibKoreanFont:
    """Phase 2.1: matplotlib 한글 폰트 설정 검증"""

    def test_matplotlib_font_family_is_malgun_gothic(self):
        """chart_generator import 후 rcParams['font.family']에 'Malgun Gothic' 포함되어야 함"""
        import importlib
        import app.utils.chart_generator
        importlib.reload(app.utils.chart_generator)
        import matplotlib
        assert 'Malgun Gothic' in matplotlib.rcParams['font.family']

    def test_matplotlib_unicode_minus_disabled(self):
        """rcParams['axes.unicode_minus']가 False여야 함"""
        import matplotlib
        assert matplotlib.rcParams['axes.unicode_minus'] is False


class TestChartKoreanLabels:
    """Phase 2.2: 한글 레이블 차트 생성 검증"""

    def test_pie_chart_with_korean_labels(self):
        """한글 레이블 포함 pie 차트가 예외 없이 PNG bytes를 반환해야 함"""
        from app.utils.chart_generator import ChartGenerator

        data = {"센서": 50, "카메라": 30, "스피커": 20}
        result = ChartGenerator.generate_pie_chart(data=data, title="장비 유형별 분포")

        assert isinstance(result, bytes)
        assert result[:4] == b'\x89PNG'

    def test_bar_chart_with_korean_labels(self):
        """한글 레이블 포함 bar 차트가 예외 없이 PNG bytes를 반환해야 함"""
        from app.utils.chart_generator import ChartGenerator

        data = {"탐지": 40, "장애": 10, "조치": 25}
        result = ChartGenerator.generate_bar_chart(
            data=data, title="이벤트 유형별 건수", xlabel="유형", ylabel="건수"
        )

        assert isinstance(result, bytes)
        assert result[:4] == b'\x89PNG'


class TestDownloadFilenameEncoding:
    """Phase 3.1: 다운로드 파일명 RFC 5987 인코딩 검증"""

    def test_download_korean_title_has_ascii_fallback_and_utf8(self, client, db):
        """한글 제목 다운로드 시 Content-Disposition에 ASCII fallback filename + filename* 모두 포함"""
        import tempfile, os
        from datetime import datetime, timezone

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-1.4 test content")
            pdf_path = f.name

        try:
            gen = ReportGeneration(
                report_type="STANDARD",
                title="주간 운영 보고서",
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

            cd = response.headers.get("content-disposition", "")
            # ASCII fallback filename (RFC 6266)
            assert f'filename="report_{gen.id}.pdf"' in cd
            # UTF-8 encoded filename* (RFC 5987)
            assert "filename*=UTF-8''" in cd or "filename*=utf-8''" in cd
        finally:
            os.unlink(pdf_path)
