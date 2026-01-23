"""
Chart Generator Utility
PRD: PRD_Report_System.md - Phase 3: 시각화
Generates chart images using matplotlib
"""
import io
from typing import Dict, List, Any

import matplotlib
matplotlib.use('Agg')  # Non-GUI backend for server-side rendering
import matplotlib.pyplot as plt


class ChartGenerator:
    """차트 이미지 생성 유틸리티"""

    # 기본 색상 팔레트
    COLORS = ['#4CAF50', '#F44336', '#FFC107', '#2196F3', '#9C27B0', '#FF9800']

    @classmethod
    def generate_pie_chart(
        cls,
        data: Dict[str, float],
        title: str = "",
        figsize: tuple = (8, 6)
    ) -> bytes:
        """
        PIE 차트 생성

        Args:
            data: {label: value} 딕셔너리
            title: 차트 제목
            figsize: 차트 크기 (width, height)

        Returns:
            PNG 이미지 bytes
        """
        fig, ax = plt.subplots(figsize=figsize)

        labels = list(data.keys())
        values = list(data.values())
        colors = cls.COLORS[:len(labels)]

        ax.pie(values, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax.set_title(title)

        return cls._fig_to_bytes(fig)

    @classmethod
    def generate_bar_chart(
        cls,
        data: Dict[str, float],
        title: str = "",
        xlabel: str = "",
        ylabel: str = "",
        figsize: tuple = (10, 6)
    ) -> bytes:
        """
        BAR 차트 생성

        Args:
            data: {label: value} 딕셔너리
            title: 차트 제목
            xlabel: X축 레이블
            ylabel: Y축 레이블
            figsize: 차트 크기

        Returns:
            PNG 이미지 bytes
        """
        fig, ax = plt.subplots(figsize=figsize)

        labels = list(data.keys())
        values = list(data.values())
        colors = cls.COLORS[:len(labels)]

        bars = ax.bar(labels, values, color=colors)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)

        # 막대 위에 값 표시
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                   f'{value}', ha='center', va='bottom')

        return cls._fig_to_bytes(fig)

    @classmethod
    def generate_line_chart(
        cls,
        labels: List[str],
        datasets: List[Dict[str, Any]],
        title: str = "",
        xlabel: str = "",
        ylabel: str = "",
        figsize: tuple = (10, 6)
    ) -> bytes:
        """
        LINE 차트 생성

        Args:
            labels: X축 레이블 리스트
            datasets: [{"label": str, "data": List[float]}] 데이터셋 리스트
            title: 차트 제목
            xlabel: X축 레이블
            ylabel: Y축 레이블
            figsize: 차트 크기

        Returns:
            PNG 이미지 bytes
        """
        fig, ax = plt.subplots(figsize=figsize)

        for i, dataset in enumerate(datasets):
            color = cls.COLORS[i % len(cls.COLORS)]
            ax.plot(labels, dataset['data'], label=dataset['label'],
                   color=color, marker='o', linewidth=2)

        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.7)

        return cls._fig_to_bytes(fig)

    @classmethod
    def generate_donut_chart(
        cls,
        data: Dict[str, float],
        title: str = "",
        figsize: tuple = (8, 6)
    ) -> bytes:
        """
        DONUT 차트 생성 (가운데 구멍이 있는 파이 차트)

        Args:
            data: {label: value} 딕셔너리
            title: 차트 제목
            figsize: 차트 크기

        Returns:
            PNG 이미지 bytes
        """
        fig, ax = plt.subplots(figsize=figsize)

        labels = list(data.keys())
        values = list(data.values())
        colors = cls.COLORS[:len(labels)]

        # 도넛 차트: wedgeprops로 가운데 구멍 생성
        wedges, texts, autotexts = ax.pie(
            values, labels=labels, colors=colors,
            autopct='%1.1f%%', startangle=90,
            wedgeprops=dict(width=0.5)  # 도넛 두께
        )
        ax.set_title(title)

        return cls._fig_to_bytes(fig)

    @staticmethod
    def _fig_to_bytes(fig: plt.Figure) -> bytes:
        """Figure를 PNG bytes로 변환"""
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)  # 메모리 해제
        return buf.read()
