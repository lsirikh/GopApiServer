"""
Tests for PDF Generator
PRD: PRD_Report_System.md - Phase 3: 시각화
TDD: Red -> Green -> Refactor
"""
import pytest


class TestReportlabImport:
    """RS-10.1: reportlab 패키지 import 테스트"""

    def test_reportlab_importable(self):
        """reportlab 패키지가 import 가능해야 함"""
        import reportlab
        assert reportlab is not None

    def test_reportlab_pdfgen_importable(self):
        """reportlab.pdfgen이 import 가능해야 함"""
        from reportlab.pdfgen import canvas
        assert canvas is not None


class TestPDFGeneratorExists:
    """RS-10.7: PDFGenerator 클래스 존재 테스트"""

    def test_pdf_generator_class_exists(self):
        """PDFGenerator 클래스가 존재해야 함"""
        from app.utils.pdf_generator import PDFGenerator
        assert PDFGenerator is not None


class TestPDFGeneratorGenerateReport:
    """RS-10.8: PDF 보고서 생성 테스트"""

    def test_generate_report_returns_bytes(self):
        """generate_report()가 bytes PDF를 반환해야 함"""
        from app.utils.pdf_generator import PDFGenerator

        result = PDFGenerator.generate_report(
            title="테스트 보고서",
            period="2024-01-01 ~ 2024-01-31",
            generator_name="홍길동",
            generator_department="IT부서"
        )

        assert isinstance(result, bytes)
        assert len(result) > 0
        # PDF 헤더 확인 (%PDF-)
        assert result[:5] == b'%PDF-'

    def test_generate_report_with_sections(self):
        """generate_report()에 섹션(제목, 본문)을 포함할 수 있어야 함"""
        from app.utils.pdf_generator import PDFGenerator

        sections = [
            {
                "title": "1. 요약",
                "content": "이번 달 총 이벤트 건수: 150건"
            },
            {
                "title": "2. 장치 현황",
                "content": "온라인: 50대, 오프라인: 10대"
            }
        ]

        result = PDFGenerator.generate_report(
            title="월간 보고서",
            period="2024-01-01 ~ 2024-01-31",
            sections=sections
        )

        assert isinstance(result, bytes)
        assert result[:5] == b'%PDF-'

    def test_generate_report_with_chart_images(self):
        """generate_report()에 차트 이미지를 포함할 수 있어야 함"""
        from app.utils.pdf_generator import PDFGenerator
        from app.utils.chart_generator import ChartGenerator

        # 차트 이미지 생성
        pie_chart = ChartGenerator.generate_pie_chart(
            data={"Online": 50, "Offline": 30},
            title="Device Status"
        )

        sections = [
            {
                "title": "장치 상태",
                "chart_image": pie_chart
            }
        ]

        result = PDFGenerator.generate_report(
            title="차트 포함 보고서",
            period="2024-01-01 ~ 2024-01-31",
            sections=sections
        )

        assert isinstance(result, bytes)
        assert result[:5] == b'%PDF-'

    def test_generate_report_with_table(self):
        """generate_report()에 테이블을 포함할 수 있어야 함"""
        from app.utils.pdf_generator import PDFGenerator

        sections = [
            {
                "title": "이벤트 목록",
                "table": {
                    "headers": ["일자", "유형", "건수"],
                    "rows": [
                        ["2024-01-01", "Detection", "10"],
                        ["2024-01-02", "Malfunction", "5"],
                        ["2024-01-03", "Action", "8"]
                    ]
                }
            }
        ]

        result = PDFGenerator.generate_report(
            title="테이블 포함 보고서",
            period="2024-01-01 ~ 2024-01-31",
            sections=sections
        )

        assert isinstance(result, bytes)
        assert result[:5] == b'%PDF-'
