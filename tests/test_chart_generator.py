"""
Tests for Chart Generator
PRD: PRD_Report_System.md - Phase 3: 시각화
TDD: Red -> Green -> Refactor
"""
import pytest


class TestChartGeneratorExists:
    """RS-10.2: ChartGenerator 클래스 존재 테스트"""

    def test_chart_generator_class_exists(self):
        """ChartGenerator 클래스가 존재해야 함"""
        from app.utils.chart_generator import ChartGenerator
        assert ChartGenerator is not None


class TestChartGeneratorPieChart:
    """RS-10.3: PIE 차트 생성 테스트"""

    def test_generate_pie_chart_returns_bytes(self):
        """generate_pie_chart()가 bytes 이미지를 반환해야 함"""
        from app.utils.chart_generator import ChartGenerator

        data = {"Online": 50, "Offline": 30, "Error": 20}
        result = ChartGenerator.generate_pie_chart(
            data=data,
            title="Device Status"
        )

        assert isinstance(result, bytes)
        assert len(result) > 0
        # PNG 헤더 확인 (PNG magic bytes: 89 50 4E 47)
        assert result[:4] == b'\x89PNG'


class TestChartGeneratorBarChart:
    """RS-10.4: BAR 차트 생성 테스트"""

    def test_generate_bar_chart_returns_bytes(self):
        """generate_bar_chart()가 bytes 이미지를 반환해야 함"""
        from app.utils.chart_generator import ChartGenerator

        data = {"Camera": 10, "Speaker": 5, "Sensor": 8}
        result = ChartGenerator.generate_bar_chart(
            data=data,
            title="Device Types",
            xlabel="Type",
            ylabel="Count"
        )

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert result[:4] == b'\x89PNG'


class TestChartGeneratorLineChart:
    """RS-10.5: LINE 차트 생성 테스트"""

    def test_generate_line_chart_returns_bytes(self):
        """generate_line_chart()가 bytes 이미지를 반환해야 함"""
        from app.utils.chart_generator import ChartGenerator

        labels = ["Mon", "Tue", "Wed", "Thu", "Fri"]
        datasets = [
            {"label": "Events", "data": [10, 20, 15, 25, 30]},
            {"label": "Errors", "data": [5, 8, 3, 10, 7]}
        ]
        result = ChartGenerator.generate_line_chart(
            labels=labels,
            datasets=datasets,
            title="Event Trend"
        )

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert result[:4] == b'\x89PNG'


class TestChartGeneratorDonutChart:
    """RS-10.6: DONUT 차트 생성 테스트"""

    def test_generate_donut_chart_returns_bytes(self):
        """generate_donut_chart()가 bytes 이미지를 반환해야 함"""
        from app.utils.chart_generator import ChartGenerator

        data = {"Detection": 40, "Malfunction": 35, "Action": 25}
        result = ChartGenerator.generate_donut_chart(
            data=data,
            title="Event Types"
        )

        assert isinstance(result, bytes)
        assert len(result) > 0
        assert result[:4] == b'\x89PNG'


class TestMatplotlibImport:
    """RS-10.1: matplotlib 패키지 import 테스트"""

    def test_matplotlib_importable(self):
        """matplotlib 패키지가 import 가능해야 함"""
        import matplotlib
        assert matplotlib is not None

    def test_matplotlib_pyplot_importable(self):
        """matplotlib.pyplot이 import 가능해야 함"""
        import matplotlib.pyplot as plt
        assert plt is not None
