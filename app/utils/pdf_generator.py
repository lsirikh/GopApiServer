"""
PDF Generator Utility
PRD: PRD_Report_System.md - Phase 3: 시각화
Generates PDF reports using reportlab
"""
import io
from typing import Dict, List, Any, Optional
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image,
    PageBreak
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


class PDFGenerator:
    """PDF 보고서 생성 유틸리티"""

    # 페이지 여백 설정
    PAGE_MARGIN = 20 * mm
    # 한글 폰트 이름 (등록 후 사용)
    FONT_NAME = 'Helvetica'
    FONT_NAME_BOLD = 'Helvetica-Bold'
    _fonts_registered = False

    @classmethod
    def _register_fonts(cls):
        """한글 폰트(맑은 고딕) 등록. 실패 시 Helvetica fallback."""
        if cls._fonts_registered:
            return
        try:
            pdfmetrics.registerFont(TTFont('MalgunGothic', 'malgun.ttf'))
            pdfmetrics.registerFont(TTFont('MalgunGothicBold', 'malgunbd.ttf'))
            cls.FONT_NAME = 'MalgunGothic'
            cls.FONT_NAME_BOLD = 'MalgunGothicBold'
        except Exception:
            cls.FONT_NAME = 'Helvetica'
            cls.FONT_NAME_BOLD = 'Helvetica-Bold'
        cls._fonts_registered = True

    @classmethod
    def generate_report(
        cls,
        title: str,
        period: str,
        generator_name: Optional[str] = None,
        generator_department: Optional[str] = None,
        sections: Optional[List[Dict[str, Any]]] = None
    ) -> bytes:
        """
        PDF 보고서 생성

        Args:
            title: 보고서 제목
            period: 보고 기간 (예: "2024-01-01 ~ 2024-01-31")
            generator_name: 작성자 이름
            generator_department: 작성자 부서
            sections: 섹션 리스트, 각 섹션은 다음 키 포함 가능:
                - title: 섹션 제목
                - content: 텍스트 내용
                - chart_image: 차트 이미지 bytes (PNG)
                - table: {"headers": [...], "rows": [[...], ...]}

        Returns:
            PDF bytes
        """
        cls._register_fonts()
        buf = io.BytesIO()

        # PDF 문서 생성
        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            leftMargin=cls.PAGE_MARGIN,
            rightMargin=cls.PAGE_MARGIN,
            topMargin=cls.PAGE_MARGIN,
            bottomMargin=cls.PAGE_MARGIN
        )

        # 스타일 설정
        styles = cls._get_styles()

        # 컨텐츠 빌드
        story = []

        # 헤더 (제목, 기간, 작성자)
        story.extend(cls._build_header(title, period, generator_name, generator_department, styles))

        # 섹션들
        if sections:
            for section in sections:
                story.extend(cls._build_section(section, styles))

        # PDF 생성
        doc.build(story)

        buf.seek(0)
        return buf.read()

    @classmethod
    def _get_styles(cls) -> Dict[str, ParagraphStyle]:
        """스타일시트 반환"""
        styles = getSampleStyleSheet()

        # 제목 스타일
        styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=styles['Heading1'],
            fontName=cls.FONT_NAME,
            fontSize=24,
            spaceAfter=10,
            alignment=1  # 가운데 정렬
        ))

        # 서브 제목 스타일 (기간, 작성자)
        styles.add(ParagraphStyle(
            name='ReportSubtitle',
            parent=styles['Normal'],
            fontName=cls.FONT_NAME,
            fontSize=12,
            textColor=colors.grey,
            alignment=1,
            spaceAfter=5
        ))

        # 섹션 제목 스타일
        styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=styles['Heading2'],
            fontName=cls.FONT_NAME,
            fontSize=16,
            spaceBefore=20,
            spaceAfter=10
        ))

        # 섹션 내용 스타일
        styles.add(ParagraphStyle(
            name='SectionContent',
            parent=styles['Normal'],
            fontName=cls.FONT_NAME,
            fontSize=11,
            spaceAfter=10,
            leading=14  # 줄 간격
        ))

        return styles

    @classmethod
    def _build_header(
        cls,
        title: str,
        period: str,
        generator_name: Optional[str],
        generator_department: Optional[str],
        styles: Dict
    ) -> List:
        """헤더 섹션 빌드"""
        story = []

        # 제목
        story.append(Paragraph(title, styles['ReportTitle']))

        # 기간
        story.append(Paragraph(f"기간: {period}", styles['ReportSubtitle']))

        # 작성자 정보
        if generator_name or generator_department:
            author_info = []
            if generator_department:
                author_info.append(generator_department)
            if generator_name:
                author_info.append(generator_name)
            story.append(Paragraph(f"작성: {' / '.join(author_info)}", styles['ReportSubtitle']))

        # 생성 일시
        story.append(Paragraph(
            f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            styles['ReportSubtitle']
        ))

        story.append(Spacer(1, 20))

        return story

    @classmethod
    def _build_section(cls, section: Dict[str, Any], styles: Dict) -> List:
        """섹션 빌드"""
        story = []

        # 섹션 제목
        if 'title' in section:
            story.append(Paragraph(section['title'], styles['SectionTitle']))

        # 텍스트 내용
        if 'content' in section:
            story.append(Paragraph(section['content'], styles['SectionContent']))

        # 차트 이미지
        if 'chart_image' in section:
            story.extend(cls._build_chart_image(section['chart_image']))

        # 테이블
        if 'table' in section:
            story.extend(cls._build_table(section['table']))

        return story

    @classmethod
    def _build_chart_image(cls, image_bytes: bytes) -> List:
        """차트 이미지 빌드"""
        story = []

        # bytes를 BytesIO로 변환
        img_buf = io.BytesIO(image_bytes)
        img = Image(img_buf, width=160 * mm, height=100 * mm)

        story.append(img)
        story.append(Spacer(1, 10))

        return story

    @classmethod
    def _build_table(cls, table_data: Dict[str, Any]) -> List:
        """테이블 빌드"""
        story = []

        headers = table_data.get('headers', [])
        rows = table_data.get('rows', [])

        # 테이블 데이터 구성
        data = [headers] + rows

        table = Table(data)
        table.setStyle(TableStyle([
            # 한글 폰트 적용
            ('FONTNAME', (0, 0), (-1, -1), cls.FONT_NAME),

            # 헤더 스타일
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),

            # 데이터 행 스타일
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

            # 전체 테두리
            ('GRID', (0, 0), (-1, -1), 1, colors.black),

            # 홀수/짝수 행 배경색
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))

        story.append(table)
        story.append(Spacer(1, 10))

        return story
