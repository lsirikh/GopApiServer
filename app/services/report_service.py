"""
Report Service
PRD: PRD_Report_System.md Section 8

데이터 수집 및 처리 서비스
"""
import os
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from app.models.device import Device
from app.models.event import Event
from app.models.system_event import SystemEvent
from app.models.report import ReportGeneration


class ReportService:
    """보고서 데이터 수집 및 처리 서비스"""

    def __init__(self, db: Session):
        self.db = db

    def get_device_statistics(self) -> Dict[str, Any]:
        """
        장비 통계 수집

        Returns:
            dict: {
                "status_counts": {"ACTIVATED": n, "ERROR": m, "DEACTIVATED": k},
                "type_counts": {"controller": a, "sensor": b, "camera": c, ...}
            }
        """
        # Status counts
        status_counts = {}
        status_query = (
            self.db.query(Device.status, func.count(Device.id))
            .group_by(Device.status)
            .all()
        )
        for status, count in status_query:
            status_counts[status] = count

        # Type (category_device) counts
        type_counts = {}
        type_query = (
            self.db.query(Device.category_device, func.count(Device.id))
            .group_by(Device.category_device)
            .all()
        )
        for category, count in type_query:
            # Convert enum to string value
            type_counts[category.value if hasattr(category, 'value') else category] = count

        return {
            "status_counts": status_counts,
            "type_counts": type_counts,
        }

    def get_event_statistics(self, days: int = 7) -> Dict[str, Any]:
        """
        이벤트 통계 수집

        Args:
            days: 통계 기간 (기본 7일)

        Returns:
            dict: {
                "event_type_counts": {"Intrusion": n, "Fault": m, "Action": k},
                "daily_trend": [{"date": "2024-01-01", "count": 10}, ...]
            }

        Note: Connection 이벤트는 제외
        """
        # Excluded event types
        excluded_types = ["Connection"]

        # Event type counts (excluding Connection)
        event_type_counts = {}
        type_query = (
            self.db.query(Event.type_event, func.count(Event.id))
            .filter(Event.type_event.notin_(excluded_types))
            .group_by(Event.type_event)
            .all()
        )
        for event_type, count in type_query:
            event_type_counts[event_type] = count

        # Daily trend for the last N days
        start_date = datetime.now() - timedelta(days=days)
        daily_trend = []
        daily_query = (
            self.db.query(
                func.date(Event.created_at).label("date"),
                func.count(Event.id).label("count")
            )
            .filter(Event.created_at >= start_date)
            .filter(Event.type_event.notin_(excluded_types))
            .group_by(func.date(Event.created_at))
            .order_by(func.date(Event.created_at))
            .all()
        )
        for row in daily_query:
            daily_trend.append({
                "date": str(row.date) if row.date else None,
                "count": row.count
            })

        return {
            "event_type_counts": event_type_counts,
            "daily_trend": daily_trend,
        }

    def get_system_statistics(self, days: int = 7) -> Dict[str, Any]:
        """
        시스템 이벤트 통계 수집

        Args:
            days: 통계 기간 (기본 7일)

        Returns:
            dict: {
                "severity_counts": {"INFO": n, "WARNING": m, "ERROR": k, "CRITICAL": l},
                "daily_trend": [{"date": "2024-01-01", "count": 10}, ...]
            }
        """
        # Severity counts
        severity_counts = {}
        severity_query = (
            self.db.query(SystemEvent.severity, func.count(SystemEvent.id))
            .group_by(SystemEvent.severity)
            .all()
        )
        for severity, count in severity_query:
            # Convert enum to string value
            key = severity.value if hasattr(severity, 'value') else severity
            severity_counts[key] = count

        # Daily trend for the last N days
        start_date = datetime.now() - timedelta(days=days)
        daily_trend = []
        daily_query = (
            self.db.query(
                func.date(SystemEvent.created_at).label("date"),
                func.count(SystemEvent.id).label("count")
            )
            .filter(SystemEvent.created_at >= start_date)
            .group_by(func.date(SystemEvent.created_at))
            .order_by(func.date(SystemEvent.created_at))
            .all()
        )
        for row in daily_query:
            daily_trend.append({
                "date": str(row.date) if row.date else None,
                "count": row.count
            })

        return {
            "severity_counts": severity_counts,
            "daily_trend": daily_trend,
        }

    def get_preview_data(self, days: int = 7) -> Dict[str, Any]:
        """
        보고서 미리보기 데이터 생성

        Args:
            days: 통계 기간 (기본 7일)

        Returns:
            dict: {
                "sections": [
                    {
                        "title": "장비 현황",
                        "charts": [...],
                        "grids": [...]
                    },
                    ...
                ]
            }
        """
        device_stats = self.get_device_statistics()
        event_stats = self.get_event_statistics(days)
        system_stats = self.get_system_statistics(days)

        sections = [
            {
                "title": "요약",
                "charts": [
                    {
                        "type": "SUMMARY_CARD",
                        "data": {
                            "device_count": sum(device_stats["type_counts"].values()),
                            "event_count": sum(event_stats["event_type_counts"].values()),
                            "system_event_count": sum(system_stats["severity_counts"].values()),
                        }
                    }
                ],
            },
            {
                "title": "장비 현황",
                "charts": [
                    {
                        "type": "DEVICE_STATUS_PIE",
                        "data": device_stats["status_counts"]
                    },
                    {
                        "type": "DEVICE_TYPE_BAR",
                        "data": device_stats["type_counts"]
                    }
                ],
                "grids": [
                    {
                        "type": "DEVICE_GRID",
                        "data": []  # Placeholder for device list
                    }
                ]
            },
            {
                "title": "이벤트 현황",
                "charts": [
                    {
                        "type": "EVENT_SUMMARY_PIE",
                        "data": event_stats["event_type_counts"]
                    },
                    {
                        "type": "EVENT_TREND_LINE",
                        "data": event_stats["daily_trend"]
                    }
                ],
                "grids": [
                    {
                        "type": "EVENT_DETECTION_GRID",
                        "data": []
                    }
                ]
            },
            {
                "title": "시스템 현황",
                "charts": [
                    {
                        "type": "SYSTEM_SEVERITY_BAR",
                        "data": system_stats["severity_counts"]
                    },
                    {
                        "type": "SYSTEM_TREND_LINE",
                        "data": system_stats["daily_trend"]
                    }
                ],
                "grids": [
                    {
                        "type": "SYSTEM_EVENT_GRID",
                        "data": []
                    }
                ]
            }
        ]

        return {
            "sections": sections
        }

    def generate_report_async(self, generation_id: int) -> None:
        """
        보고서 비동기 생성

        Args:
            generation_id: ReportGeneration ID

        Process:
            1. status를 GENERATING으로 변경
            2. 통계 데이터 수집
            3. PDF 생성
            4. 파일 저장
            5. status를 COMPLETED로 변경, pdf_file_path 설정
            6. 에러 시 status를 FAILED로 변경, error_message 설정
        """
        from app.utils.chart_generator import ChartGenerator
        from app.utils.pdf_generator import PDFGenerator

        # Get generation record
        generation = self.db.query(ReportGeneration).filter(
            ReportGeneration.id == generation_id
        ).first()

        if not generation:
            return

        try:
            # 1. Update status to GENERATING
            generation.status = "GENERATING"
            self.db.commit()

            # 2. Collect statistics
            preview_data = self.get_preview_data()
            device_stats = self.get_device_statistics()
            event_stats = self.get_event_statistics()
            system_stats = self.get_system_statistics()

            # 3. Generate charts
            charts = []

            # Device status pie chart
            if device_stats["status_counts"]:
                pie_chart = ChartGenerator.generate_pie_chart(
                    data=device_stats["status_counts"],
                    title="장비 상태"
                )
                charts.append(("장비 상태 분포", pie_chart))

            # Device type bar chart
            if device_stats["type_counts"]:
                bar_chart = ChartGenerator.generate_bar_chart(
                    data=device_stats["type_counts"],
                    title="장비 유형별 현황",
                    xlabel="유형",
                    ylabel="개수"
                )
                charts.append(("장비 유형별 현황", bar_chart))

            # Event type pie chart
            if event_stats["event_type_counts"]:
                event_pie = ChartGenerator.generate_donut_chart(
                    data=event_stats["event_type_counts"],
                    title="이벤트 유형"
                )
                charts.append(("이벤트 유형 분포", event_pie))

            # System severity bar chart
            if system_stats["severity_counts"]:
                severity_bar = ChartGenerator.generate_bar_chart(
                    data=system_stats["severity_counts"],
                    title="시스템 이벤트 심각도",
                    xlabel="심각도",
                    ylabel="건수"
                )
                charts.append(("시스템 이벤트 심각도", severity_bar))

            # 4. Build PDF sections
            sections = [
                {
                    "title": "1. 요약",
                    "content": (
                        f"보고서 기간: {generation.start_date.strftime('%Y-%m-%d')} ~ "
                        f"{generation.end_date.strftime('%Y-%m-%d')}\n"
                        f"총 장비 수: {sum(device_stats['type_counts'].values())}대\n"
                        f"총 이벤트 수: {sum(event_stats['event_type_counts'].values())}건\n"
                        f"총 시스템 이벤트 수: {sum(system_stats['severity_counts'].values())}건"
                    )
                }
            ]

            # Add chart sections
            for title, chart_image in charts:
                sections.append({
                    "title": title,
                    "chart_image": chart_image
                })

            # 5. Generate PDF
            pdf_bytes = PDFGenerator.generate_report(
                title=generation.title,
                period=f"{generation.start_date.strftime('%Y-%m-%d')} ~ {generation.end_date.strftime('%Y-%m-%d')}",
                generator_name=generation.generator_name,
                generator_department=generation.generator_department,
                sections=sections
            )

            # 6. Save PDF file
            reports_dir = os.path.join(os.getcwd(), "reports")
            os.makedirs(reports_dir, exist_ok=True)

            filename = f"report_{generation.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            file_path = os.path.join(reports_dir, filename)

            with open(file_path, 'wb') as f:
                f.write(pdf_bytes)

            # 7. Update generation record
            generation.status = "COMPLETED"
            generation.pdf_file_path = file_path
            generation.pdf_file_size = len(pdf_bytes)
            generation.completed_at = datetime.now()
            generation.summary_data = {
                "device_count": sum(device_stats['type_counts'].values()),
                "event_count": sum(event_stats['event_type_counts'].values()),
                "system_event_count": sum(system_stats['severity_counts'].values()),
                "device_stats": device_stats,
                "event_stats": event_stats,
                "system_stats": system_stats,
            }
            self.db.commit()

        except Exception as e:
            # Error handling
            generation.status = "FAILED"
            generation.error_message = str(e)
            self.db.commit()
