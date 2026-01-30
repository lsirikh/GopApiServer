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
from app.models.event import Event, DetectionEvent, MalfunctionEvent, ActionEvent
from app.models.system_event import SystemEvent
from app.models.config_change_log import ConfigChangeLog
from app.models.audit_log import AuditLog
from app.models.user import AccountUser, UserLoginLog, UserSession
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

    # ==================================================================
    # Phase 3: User Statistics
    # ==================================================================

    def get_user_statistics(self, days: int = 7) -> Dict[str, Any]:
        """
        사용자 통계 수집

        Returns:
            dict: {
                "role_counts": {"ADMIN": n, "VIEWER": m, ...},
                "login_daily_trend": [{"date": "2024-01-01", "count": 10}, ...],
                "login_result_counts": {"SUCCESS": n, "FAILURE": m}
            }
        """
        # Role distribution
        role_counts = {}
        role_query = (
            self.db.query(AccountUser.role, func.count(AccountUser.id))
            .group_by(AccountUser.role)
            .all()
        )
        for role, count in role_query:
            role_counts[role] = count

        # Login daily trend
        start_date = datetime.now() - timedelta(days=days)
        login_daily_trend = []
        login_query = (
            self.db.query(
                func.date(UserLoginLog.created_at).label("date"),
                func.count(UserLoginLog.id).label("count")
            )
            .filter(UserLoginLog.created_at >= start_date)
            .group_by(func.date(UserLoginLog.created_at))
            .order_by(func.date(UserLoginLog.created_at))
            .all()
        )
        for row in login_query:
            login_daily_trend.append({
                "date": str(row.date) if row.date else None,
                "count": row.count
            })

        # Login result distribution (SUCCESS/FAILURE)
        login_result_counts = {}
        result_query = (
            self.db.query(UserLoginLog.result, func.count(UserLoginLog.id))
            .group_by(UserLoginLog.result)
            .all()
        )
        for result, count in result_query:
            login_result_counts[result] = count

        return {
            "role_counts": role_counts,
            "login_daily_trend": login_daily_trend,
            "login_result_counts": login_result_counts,
        }

    # ==================================================================
    # Phase 4: Grid Data Queries
    # ==================================================================

    def get_device_grid_data(self) -> Dict[str, Any]:
        """장비 목록 그리드 데이터"""
        columns = ["ID", "유형", "이름", "상태", "IP"]
        devices = self.db.query(Device).all()
        rows = []
        for d in devices:
            rows.append([
                d.id,
                d.category_device.value if hasattr(d.category_device, 'value') else str(d.category_device) if d.category_device else "",
                d.name_device or "",
                d.status or "",
                getattr(d, 'ip_address', "") or "",
            ])
        return {"columns": columns, "rows": rows, "total_rows": len(rows)}

    def get_detection_grid_data(self, days: int = 7) -> Dict[str, Any]:
        """탐지 이벤트 그리드 데이터"""
        columns = ["ID", "일시", "탐지유형", "존", "장비ID"]
        start_date = datetime.now() - timedelta(days=days)
        events = (
            self.db.query(DetectionEvent)
            .filter(DetectionEvent.created_at >= start_date)
            .order_by(DetectionEvent.created_at.desc())
            .limit(100)
            .all()
        )
        rows = []
        for e in events:
            rows.append([
                e.id,
                e.created_at.strftime('%Y-%m-%d %H:%M:%S') if e.created_at else "",
                e.type_detection or "",
                getattr(e, 'zone', "") or "",
                e.device_id if hasattr(e, 'device_id') else "",
            ])
        return {"columns": columns, "rows": rows, "total_rows": len(rows)}

    def get_malfunction_grid_data(self, days: int = 7) -> Dict[str, Any]:
        """장애 이벤트 그리드 데이터"""
        columns = ["ID", "일시", "장애유형", "장비ID"]
        start_date = datetime.now() - timedelta(days=days)
        events = (
            self.db.query(MalfunctionEvent)
            .filter(MalfunctionEvent.created_at >= start_date)
            .order_by(MalfunctionEvent.created_at.desc())
            .limit(100)
            .all()
        )
        rows = []
        for e in events:
            rows.append([
                e.id,
                e.created_at.strftime('%Y-%m-%d %H:%M:%S') if e.created_at else "",
                e.type_fault or "",
                e.device_id if hasattr(e, 'device_id') else "",
            ])
        return {"columns": columns, "rows": rows, "total_rows": len(rows)}

    def get_action_grid_data(self, days: int = 7) -> Dict[str, Any]:
        """조치 이벤트 그리드 데이터"""
        columns = ["ID", "일시", "이벤트유형", "내용", "조치자"]
        start_date = datetime.now() - timedelta(days=days)
        events = (
            self.db.query(ActionEvent)
            .filter(ActionEvent.created_at >= start_date)
            .order_by(ActionEvent.created_at.desc())
            .limit(100)
            .all()
        )
        rows = []
        for e in events:
            rows.append([
                e.id,
                e.created_at.strftime('%Y-%m-%d %H:%M:%S') if e.created_at else "",
                e.type_event or "",
                getattr(e, 'content', "") or "",
                getattr(e, 'user', "") or "",
            ])
        return {"columns": columns, "rows": rows, "total_rows": len(rows)}

    def get_system_event_grid_data(self, days: int = 7) -> Dict[str, Any]:
        """시스템 이벤트 그리드 데이터"""
        columns = ["ID", "일시", "유형", "심각도", "메시지"]
        start_date = datetime.now() - timedelta(days=days)
        events = (
            self.db.query(SystemEvent)
            .filter(SystemEvent.created_at >= start_date)
            .order_by(SystemEvent.created_at.desc())
            .limit(100)
            .all()
        )
        rows = []
        for e in events:
            rows.append([
                e.id,
                e.created_at.strftime('%Y-%m-%d %H:%M:%S') if e.created_at else "",
                e.type_event.value if hasattr(e.type_event, 'value') else str(e.type_event) if e.type_event else "",
                e.severity.value if hasattr(e.severity, 'value') else str(e.severity) if e.severity else "",
                e.message or "",
            ])
        return {"columns": columns, "rows": rows, "total_rows": len(rows)}

    def get_config_grid_data(self, days: int = 7) -> Dict[str, Any]:
        """설정 변경 이력 그리드 데이터"""
        columns = ["ID", "일시", "리소스유형", "액션", "리소스ID"]
        start_date = datetime.now() - timedelta(days=days)
        logs = (
            self.db.query(ConfigChangeLog)
            .filter(ConfigChangeLog.created_at >= start_date)
            .order_by(ConfigChangeLog.created_at.desc())
            .limit(100)
            .all()
        )
        rows = []
        for log in logs:
            rows.append([
                log.id,
                log.created_at.strftime('%Y-%m-%d %H:%M:%S') if log.created_at else "",
                log.resource_type or "",
                log.action or "",
                log.resource_id if hasattr(log, 'resource_id') else "",
            ])
        return {"columns": columns, "rows": rows, "total_rows": len(rows)}

    def get_audit_grid_data(self, days: int = 7) -> Dict[str, Any]:
        """감사 로그 그리드 데이터"""
        columns = ["ID", "일시", "액션", "상태", "리소스", "행위자"]
        start_date = datetime.now() - timedelta(days=days)
        logs = (
            self.db.query(AuditLog)
            .filter(AuditLog.created_at >= start_date)
            .order_by(AuditLog.created_at.desc())
            .limit(100)
            .all()
        )
        rows = []
        for log in logs:
            rows.append([
                log.id,
                log.created_at.strftime('%Y-%m-%d %H:%M:%S') if log.created_at else "",
                log.action_type or "",
                log.action_status or "",
                log.resource_type or "",
                log.actor_name or "",
            ])
        return {"columns": columns, "rows": rows, "total_rows": len(rows)}

    def get_user_grid_data(self) -> Dict[str, Any]:
        """사용자 목록 그리드 데이터"""
        columns = ["ID", "로그인ID", "이름", "역할", "이메일"]
        users = self.db.query(AccountUser).all()
        rows = []
        for u in users:
            rows.append([
                u.id,
                u.login_id or "",
                u.name or "",
                u.role or "",
                u.email or "",
            ])
        return {"columns": columns, "rows": rows, "total_rows": len(rows)}

    def get_user_login_grid_data(self, days: int = 7) -> Dict[str, Any]:
        """로그인 이력 그리드 데이터"""
        columns = ["ID", "일시", "로그인ID", "액션", "결과", "IP"]
        start_date = datetime.now() - timedelta(days=days)
        logs = (
            self.db.query(UserLoginLog)
            .filter(UserLoginLog.created_at >= start_date)
            .order_by(UserLoginLog.created_at.desc())
            .limit(100)
            .all()
        )
        rows = []
        for log in logs:
            rows.append([
                log.id,
                log.created_at.strftime('%Y-%m-%d %H:%M:%S') if log.created_at else "",
                log.login_id or "",
                log.action or "",
                log.result or "",
                log.ip_address or "",
            ])
        return {"columns": columns, "rows": rows, "total_rows": len(rows)}

    def get_user_session_grid_data(self) -> Dict[str, Any]:
        """사용자 세션 그리드 데이터"""
        columns = ["ID", "사용자ID", "IP", "생성일", "만료일"]
        sessions = (
            self.db.query(UserSession)
            .order_by(UserSession.created_at.desc())
            .limit(100)
            .all()
        )
        rows = []
        for s in sessions:
            rows.append([
                s.id,
                s.user_id,
                s.ip_address or "",
                s.created_at.strftime('%Y-%m-%d %H:%M:%S') if s.created_at else "",
                s.expires_at.strftime('%Y-%m-%d %H:%M:%S') if s.expires_at else "",
            ])
        return {"columns": columns, "rows": rows, "total_rows": len(rows)}

    # ==================================================================
    # Phase 5: Structured Preview Data
    # ==================================================================

    def get_structured_preview_data(self, days: int = 7) -> Dict[str, Any]:
        """
        구조화된 보고서 미리보기 데이터 생성
        PRD: PRD_Report_System.md Section 5 - ReportPreviewResponse 형식

        Returns ChartData/GridConfig 형식의 sections
        """
        device_stats = self.get_device_statistics()
        event_stats = self.get_event_statistics(days)
        system_stats = self.get_system_statistics(days)
        user_stats = self.get_user_statistics(days)

        sections = [
            {
                "name": "summary",
                "title": "요약",
                "charts": [
                    {
                        "id": "SUMMARY_CARD",
                        "title": "전체 요약",
                        "type": "SUMMARY",
                        "data": {
                            "labels": ["장비", "이벤트", "시스템"],
                            "values": [
                                sum(device_stats["type_counts"].values()),
                                sum(event_stats["event_type_counts"].values()),
                                sum(system_stats["severity_counts"].values()),
                            ]
                        }
                    }
                ],
                "grids": [],
            },
            {
                "name": "device",
                "title": "장비 현황",
                "charts": [
                    {
                        "id": "DEVICE_STATUS_PIE",
                        "title": "장비 상태 분포",
                        "type": "PIE",
                        "data": {
                            "labels": list(device_stats["status_counts"].keys()),
                            "values": list(device_stats["status_counts"].values()),
                            "colors": ["#4CAF50", "#F44336", "#9E9E9E"],
                        }
                    },
                    {
                        "id": "DEVICE_TYPE_BAR",
                        "title": "장비 유형별 현황",
                        "type": "BAR",
                        "data": {
                            "labels": list(device_stats["type_counts"].keys()),
                            "values": list(device_stats["type_counts"].values()),
                        }
                    },
                ],
                "grids": [
                    {**self.get_device_grid_data(), "id": "DEVICE_GRID", "title": "장비 목록"},
                ],
            },
            {
                "name": "event",
                "title": "이벤트 현황",
                "charts": [
                    {
                        "id": "EVENT_SUMMARY_PIE",
                        "title": "이벤트 유형 분포",
                        "type": "PIE",
                        "data": {
                            "labels": list(event_stats["event_type_counts"].keys()),
                            "values": list(event_stats["event_type_counts"].values()),
                        }
                    },
                    {
                        "id": "EVENT_TREND_LINE",
                        "title": "이벤트 발생 추이",
                        "type": "LINE",
                        "data": {
                            "labels": [d["date"] for d in event_stats["daily_trend"]],
                            "values": [d["count"] for d in event_stats["daily_trend"]],
                        }
                    },
                ],
                "grids": [
                    {**self.get_detection_grid_data(days), "id": "EVENT_DETECTION_GRID", "title": "탐지 이벤트 목록"},
                    {**self.get_malfunction_grid_data(days), "id": "EVENT_MALFUNCTION_GRID", "title": "장애 이벤트 목록"},
                    {**self.get_action_grid_data(days), "id": "EVENT_ACTION_GRID", "title": "조치 이벤트 목록"},
                ],
            },
            {
                "name": "system",
                "title": "시스템 현황",
                "charts": [
                    {
                        "id": "SYSTEM_SEVERITY_BAR",
                        "title": "심각도별 시스템 이벤트",
                        "type": "BAR",
                        "data": {
                            "labels": list(system_stats["severity_counts"].keys()),
                            "values": list(system_stats["severity_counts"].values()),
                        }
                    },
                    {
                        "id": "SYSTEM_TREND_LINE",
                        "title": "시스템 이벤트 추이",
                        "type": "LINE",
                        "data": {
                            "labels": [d["date"] for d in system_stats["daily_trend"]],
                            "values": [d["count"] for d in system_stats["daily_trend"]],
                        }
                    },
                ],
                "grids": [
                    {**self.get_system_event_grid_data(days), "id": "SYSTEM_EVENT_GRID", "title": "시스템 이벤트 목록"},
                    {**self.get_config_grid_data(days), "id": "SYSTEM_CONFIG_GRID", "title": "설정 변경 이력"},
                    {**self.get_audit_grid_data(days), "id": "SYSTEM_AUDIT_GRID", "title": "감사 로그"},
                ],
            },
            {
                "name": "user",
                "title": "사용자 현황",
                "charts": [
                    {
                        "id": "USER_ROLE_PIE",
                        "title": "역할별 사용자 분포",
                        "type": "PIE",
                        "data": {
                            "labels": list(user_stats["role_counts"].keys()),
                            "values": list(user_stats["role_counts"].values()),
                        }
                    },
                    {
                        "id": "USER_LOGIN_TREND_LINE",
                        "title": "일별 로그인 추이",
                        "type": "LINE",
                        "data": {
                            "labels": [d["date"] for d in user_stats["login_daily_trend"]],
                            "values": [d["count"] for d in user_stats["login_daily_trend"]],
                        }
                    },
                    {
                        "id": "USER_LOGIN_RESULT_PIE",
                        "title": "로그인 성공/실패 분포",
                        "type": "PIE",
                        "data": {
                            "labels": list(user_stats["login_result_counts"].keys()),
                            "values": list(user_stats["login_result_counts"].values()),
                        }
                    },
                ],
                "grids": [
                    {**self.get_user_grid_data(), "id": "USER_GRID", "title": "사용자 목록"},
                    {**self.get_user_login_grid_data(days), "id": "USER_LOGIN_GRID", "title": "로그인 이력"},
                    {**self.get_user_session_grid_data(), "id": "USER_SESSION_GRID", "title": "세션 목록"},
                ],
            },
        ]

        return {"sections": sections}

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
            user_stats = self.get_user_statistics()

            # 2.1 Collect grid data for tables
            device_grid = self.get_device_grid_data()
            detection_grid = self.get_detection_grid_data()
            malfunction_grid = self.get_malfunction_grid_data()
            action_grid = self.get_action_grid_data()
            system_event_grid = self.get_system_event_grid_data()
            config_grid = self.get_config_grid_data()
            audit_grid = self.get_audit_grid_data()
            user_grid = self.get_user_grid_data()
            user_login_grid = self.get_user_login_grid_data()
            user_session_grid = self.get_user_session_grid_data()

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
                        f"총 시스템 이벤트 수: {sum(system_stats['severity_counts'].values())}건\n"
                        f"총 사용자 수: {sum(user_stats['role_counts'].values())}명"
                    )
                }
            ]

            # Add chart sections
            for title, chart_image in charts:
                sections.append({
                    "title": title,
                    "chart_image": chart_image
                })

            # 4.1 Add table sections for grid data
            grid_tables = [
                ("장비 목록", device_grid),
                ("탐지 이벤트 목록", detection_grid),
                ("장애 이벤트 목록", malfunction_grid),
                ("조치 이벤트 목록", action_grid),
                ("시스템 이벤트 목록", system_event_grid),
                ("설정 변경 이력", config_grid),
                ("감사 로그", audit_grid),
                ("사용자 목록", user_grid),
                ("로그인 이력", user_login_grid),
                ("세션 목록", user_session_grid),
            ]
            for table_title, grid_data in grid_tables:
                if grid_data["rows"]:
                    sections.append({
                        "title": table_title,
                        "table": {
                            "headers": grid_data["columns"],
                            "rows": grid_data["rows"],
                        }
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
                "user_count": sum(user_stats['role_counts'].values()),
                "device_stats": device_stats,
                "event_stats": event_stats,
                "system_stats": system_stats,
                "user_stats": user_stats,
                "grid_counts": {
                    "device_grid": device_grid["total_rows"],
                    "detection_grid": detection_grid["total_rows"],
                    "malfunction_grid": malfunction_grid["total_rows"],
                    "action_grid": action_grid["total_rows"],
                    "system_event_grid": system_event_grid["total_rows"],
                    "config_grid": config_grid["total_rows"],
                    "audit_grid": audit_grid["total_rows"],
                    "user_grid": user_grid["total_rows"],
                    "user_login_grid": user_login_grid["total_rows"],
                    "user_session_grid": user_session_grid["total_rows"],
                },
            }
            self.db.commit()

        except Exception as e:
            # Error handling
            generation.status = "FAILED"
            generation.error_message = str(e)
            self.db.commit()
