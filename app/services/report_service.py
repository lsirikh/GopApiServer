"""
Report Service
PRD: PRD_Report_System.md Section 8

데이터 수집 및 처리 서비스

v6.0 Phase 3: ReportServiceAsync 신설 — AsyncSession 기반 완전 async 구현.
기존 sync ReportService는 dual-stack 유지(기존 caller 호환).
"""
import os
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, cast, Date, select, text, case, and_, or_
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from app.models.device import Device
from app.models.event import Event, DetectionEvent, MalfunctionEvent, ActionEvent
from app.models.system_event import SystemEvent
from app.models.config_change_log import ConfigChangeLog
from app.models.audit_log import AuditLog
from app.models.user import AccountUser, UserLoginLog, UserSession
from app.models.report import ReportGeneration, ReportTemplate
from app.utils import report_labels as L

# PDF 차트/그리드 → EnumReportComponent 매핑 (PRD_Report_CustomTemplate_Filter)
CHART_COMPONENT_MAP = {
    "장비 상태 분포": "DEVICE_STATUS_PIE",
    "장비 유형별 현황": "DEVICE_TYPE_BAR",
    "이벤트 유형 분포": "EVENT_SUMMARY_PIE",
    "이벤트 발생 추이": "EVENT_TREND_LINE",
    "시스템 이벤트 심각도": "SYSTEM_SEVERITY_BAR",
    "시스템 이벤트 추이": "SYSTEM_TREND_LINE",
    "역할별 사용자 분포": "USER_ROLE_PIE",
    "일별 로그인 추이": "USER_LOGIN_TREND_LINE",
    "로그인 결과 분포": "USER_LOGIN_RESULT_PIE",
}

GRID_COMPONENT_MAP = {
    "장비 목록": "DEVICE_GRID",
    "탐지 이벤트 목록": "EVENT_DETECTION_GRID",
    "장애 이벤트 목록": "EVENT_MALFUNCTION_GRID",
    "조치 이벤트 목록": "EVENT_ACTION_GRID",
    "시스템 이벤트 목록": "SYSTEM_EVENT_GRID",
    "설정 변경 이력": "SYSTEM_CONFIG_GRID",
    "감사 로그": "SYSTEM_AUDIT_GRID",
    "사용자 목록": "USER_GRID",
    "로그인 이력": "USER_LOGIN_GRID",
    "세션 목록": "USER_SESSION_GRID",
}


class ReportService:
    """보고서 데이터 수집 및 처리 서비스"""

    def __init__(self, db: Session):
        self.db = db

    def get_enabled_components(self, generation: ReportGeneration) -> Optional[List[str]]:
        """
        ReportGeneration에서 활성화된 컴포넌트 ID 목록 추출

        Returns:
            None: STANDARD 또는 템플릿 없음 → 전체 포함
            List[str]: CUSTOM 템플릿의 enabled=True인 컴포넌트 ID 목록
        """
        if generation.report_type != "CUSTOM" or not generation.template_id:
            return None

        template = self.db.query(ReportTemplate).filter(
            ReportTemplate.id == generation.template_id
        ).first()

        if not template or not template.components:
            return None

        return [
            c["id"] for c in template.components
            if c.get("enabled", True)
        ]

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
            status_counts[status.value if hasattr(status, 'value') else status] = count

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

    def get_device_category_summary(self) -> List[Dict]:
        """카테고리별 장비 정상/전체 현황 (PRD_Report_Preview_Debug GAP-1)"""
        from sqlalchemy import case

        results = (
            self.db.query(
                Device.category_device,
                func.count(Device.id).label('total'),
                func.sum(case((Device.status == 'ACTIVATED', 1), else_=0)).label('normal')
            )
            .group_by(Device.category_device)
            .all()
        )
        return [
            {
                "category": r.category_device.value if hasattr(r.category_device, 'value') else str(r.category_device),
                "total": r.total,
                "normal": int(r.normal or 0),
                "status": "all-normal" if int(r.normal or 0) == r.total else "has-issue"
            }
            for r in results
        ]

    def get_server_status_summary(self) -> List[Dict]:
        """서버 카테고리별 상태 요약 (PRD_Report_Preview_Debug GAP-3)"""
        from app.models.server import ServerCategory, Server

        categories = self.db.query(ServerCategory).order_by(ServerCategory.sort_order).all()
        result = []
        for cat in categories:
            servers = self.db.query(Server).filter(Server.category_id == cat.id).all()
            worst_status = "normal"
            for s in servers:
                status_val = s.status.value if hasattr(s.status, 'value') else str(s.status) if s.status else ""
                if status_val == "ERROR":
                    worst_status = "error"
                    break
                elif status_val == "WARNING" and worst_status != "error":
                    worst_status = "warning"
            result.append({
                "name": cat.name,
                "status": worst_status,
                "count": len(servers)
            })
        return result

    def get_event_statistics(self, days: int = 7) -> Dict[str, Any]:
        """
        이벤트 통계 수집 (PRD_Report_Preview_Debug BUG-4 + GAP-2 + GAP-4)

        Args:
            days: 통계 기간 (기본 7일)

        Returns:
            dict: {
                "event_type_counts": {"detection": n, "malfunction": m, "action": k},
                "daily_trend": [
                    {"label": "탐지", "values": [...]},
                    {"label": "장애", "values": [...]},
                    {"label": "조치", "values": [...]}
                ]
            }

        Note: Connection 이벤트는 제외, category_event 기준 집계
        """
        start_date = datetime.now() - timedelta(days=days)

        # Category-based counts (BUG-4 fix)
        detection_count = self.db.query(func.count(DetectionEvent.id)).filter(
            DetectionEvent.created_at >= start_date
        ).scalar() or 0

        malfunction_count = self.db.query(func.count(MalfunctionEvent.id)).filter(
            MalfunctionEvent.created_at >= start_date
        ).scalar() or 0

        action_count = self.db.query(func.count(ActionEvent.id)).filter(
            ActionEvent.created_at >= start_date
        ).scalar() or 0

        event_type_counts = {
            "detection": detection_count,
            "malfunction": malfunction_count,
            "action": action_count,
        }

        # Daily trend separated by category (GAP-4)
        # Generate date labels for the period
        dates = []
        for i in range(days):
            d = start_date + timedelta(days=i)
            dates.append(str(d.date()) if hasattr(d, 'date') else str(d)[:10])

        # Detection daily trend
        detection_daily = {}
        det_query = (
            self.db.query(
                func.date(DetectionEvent.created_at).label("date"),
                func.count(DetectionEvent.id).label("count")
            )
            .filter(DetectionEvent.created_at >= start_date)
            .group_by(func.date(DetectionEvent.created_at))
            .all()
        )
        for row in det_query:
            detection_daily[str(row.date)] = row.count

        # Malfunction daily trend
        malfunction_daily = {}
        mal_query = (
            self.db.query(
                func.date(MalfunctionEvent.created_at).label("date"),
                func.count(MalfunctionEvent.id).label("count")
            )
            .filter(MalfunctionEvent.created_at >= start_date)
            .group_by(func.date(MalfunctionEvent.created_at))
            .all()
        )
        for row in mal_query:
            malfunction_daily[str(row.date)] = row.count

        # Action daily trend
        action_daily = {}
        act_query = (
            self.db.query(
                func.date(ActionEvent.created_at).label("date"),
                func.count(ActionEvent.id).label("count")
            )
            .filter(ActionEvent.created_at >= start_date)
            .group_by(func.date(ActionEvent.created_at))
            .all()
        )
        for row in act_query:
            action_daily[str(row.date)] = row.count

        daily_trend = [
            {"label": "탐지", "values": [detection_daily.get(d, 0) for d in dates]},
            {"label": "장애", "values": [malfunction_daily.get(d, 0) for d in dates]},
            {"label": "조치", "values": [action_daily.get(d, 0) for d in dates]},
        ]

        return {
            "event_type_counts": event_type_counts,
            "daily_trend": daily_trend,
            "daily_labels": dates,
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
                "role_counts": {"ADMIN": n, "USER": m},
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
        """장비 목록 그리드 데이터 (PRD_Report_Preview_Debug GAP-7)"""
        columns = ["ID", "장비명", "장비유형", "버전", "상태", "활성"]
        devices = self.db.query(Device).all()
        rows = []
        for d in devices:
            rows.append([
                d.id,
                d.name_device or "",
                d.type_device.value if hasattr(d.type_device, 'value') else str(d.type_device) if d.type_device else d.category_device.value if hasattr(d.category_device, 'value') else "",
                d.version or "",
                d.status.value if hasattr(d.status, 'value') else str(d.status) if d.status else "",
                d.is_enable,
            ])
        return {"columns": columns, "rows": rows, "total_rows": len(rows)}

    def get_detection_grid_data(self, days: int = 7) -> Dict[str, Any]:
        """탐지 이벤트 그리드 데이터 (PRD_Report_Preview_Debug GAP-5)"""
        columns = ["ID", "일시", "탐지유형", "장비유형", "장비명",
                   "조치보고일자", "조치자", "조치내용"]
        start_date = datetime.now() - timedelta(days=days)
        events = (
            self.db.query(DetectionEvent)
            .outerjoin(Device, DetectionEvent.device_id == Device.id)
            .filter(DetectionEvent.created_at >= start_date)
            .order_by(DetectionEvent.created_at.desc())
            .all()
        )
        rows = []
        for e in events:
            action = self.db.query(ActionEvent).filter(
                ActionEvent.from_event_id == e.id
            ).first()
            rows.append([
                e.id,
                e.created_at.strftime('%Y-%m-%d %H:%M:%S') if e.created_at else "",
                e.result.value if hasattr(e.result, 'value') else str(e.result) if e.result else "",
                e.device.category_device.value if e.device and hasattr(e.device.category_device, 'value') else "",
                e.device.name_device if e.device else "",
                action.created_at.strftime('%Y-%m-%d %H:%M:%S') if action and action.created_at else "-",
                action.user if action else "-",
                action.content if action else "-",
            ])
        return {"columns": columns, "rows": rows, "total_rows": len(rows)}

    def get_malfunction_grid_data(self, days: int = 7) -> Dict[str, Any]:
        """장애 이벤트 그리드 데이터 (PRD_Report_Preview_Debug GAP-6)"""
        columns = ["ID", "일시", "장애유형", "장비유형", "장비명",
                   "조치보고일자", "조치자", "조치내용"]
        start_date = datetime.now() - timedelta(days=days)
        events = (
            self.db.query(MalfunctionEvent)
            .outerjoin(Device, MalfunctionEvent.device_id == Device.id)
            .filter(MalfunctionEvent.created_at >= start_date)
            .order_by(MalfunctionEvent.created_at.desc())
            .all()
        )
        rows = []
        for e in events:
            action = self.db.query(ActionEvent).filter(
                ActionEvent.from_event_id == e.id
            ).first()
            rows.append([
                e.id,
                e.created_at.strftime('%Y-%m-%d %H:%M:%S') if e.created_at else "",
                e.reason.value if hasattr(e.reason, 'value') else str(e.reason) if e.reason else "",
                e.device.category_device.value if e.device and hasattr(e.device.category_device, 'value') else "",
                e.device.name_device if e.device else "",
                action.created_at.strftime('%Y-%m-%d %H:%M:%S') if action and action.created_at else "-",
                action.user if action else "-",
                action.content if action else "-",
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
                log.resource_type.value if hasattr(log.resource_type, 'value') else (log.resource_type or ""),
                log.action.value if hasattr(log.action, 'value') else (log.action or ""),
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

    def get_structured_preview_data(self, days: int = 7, enabled_components: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        구조화된 보고서 미리보기 데이터 생성
        PRD_Report_Preview_Debug GAP-10: 11섹션 구조 (차트/그리드 분리)
        PRD_Report_CustomTemplate_Filter: enabled_components로 비정형 필터링

        Args:
            days: 통계 기간
            enabled_components: 활성화된 컴포넌트 ID 목록.
                None이면 전체 반환 (STANDARD), 리스트면 해당 컴포넌트만 (CUSTOM)

        Sections:
        1. 요약 (summary_data: 장비/이벤트/서버 카드)
        2~5. 차트 섹션 (장비/이벤트/시스템/사용자)
        6~11. 그리드 섹션 (장비/이벤트/시스템이벤트/설정변경/감사/사용자)
        """
        device_stats = self.get_device_statistics()
        event_stats = self.get_event_statistics(days)
        system_stats = self.get_system_statistics(days)
        user_stats = self.get_user_statistics(days)

        sections = [
            # ─── 1. 요약 ───
            {
                "name": "summary",
                "title": "1. 요약",
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
                "summary_data": {
                    "device_categories": self.get_device_category_summary(),
                    "event_counts": event_stats["event_type_counts"],
                    "server_status": self.get_server_status_summary(),
                },
            },
            # ─── 2. 장비 현황 (Charts Only) ───
            {
                "name": "device_charts",
                "title": "2. 장비 현황",
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
                        "title": "유형별 장비 현황",
                        "type": "BAR",
                        "data": {
                            "labels": list(device_stats["type_counts"].keys()),
                            "values": list(device_stats["type_counts"].values()),
                        }
                    },
                ],
                "grids": [],
            },
            # ─── 3. 이벤트 현황 (Charts Only) ───
            {
                "name": "event_charts",
                "title": "3. 이벤트 현황",
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
                            "labels": event_stats.get("daily_labels", []),
                            "values": [],
                            "datasets": event_stats["daily_trend"],
                        }
                    },
                ],
                "grids": [],
            },
            # ─── 4. 시스템 현황 (Charts Only) ───
            {
                "name": "system_charts",
                "title": "4. 시스템 현황",
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
                "grids": [],
            },
            # ─── 5. 사용자 현황 (Charts Only) ───
            {
                "name": "user_charts",
                "title": "5. 사용자 현황",
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
                "grids": [],
            },
            # ─── 6. 장비 목록 (Grid Only) ───
            {
                "name": "device_grid",
                "title": "6. 장비 목록",
                "charts": [],
                "grids": [
                    {**self.get_device_grid_data(), "id": "DEVICE_GRID", "title": "장비 목록"},
                ],
            },
            # ─── 7. 이벤트 상세 (Grids Only) ───
            {
                "name": "event_grids",
                "title": "7. 이벤트 상세",
                "charts": [],
                "grids": [
                    {**self.get_detection_grid_data(days), "id": "EVENT_DETECTION_GRID", "title": "탐지 이벤트 목록"},
                    {**self.get_malfunction_grid_data(days), "id": "EVENT_MALFUNCTION_GRID", "title": "장애 이벤트 목록"},
                    {**self.get_action_grid_data(days), "id": "EVENT_ACTION_GRID", "title": "조치 이벤트 목록"},
                ],
            },
            # ─── 8. 시스템 이벤트 (Grid Only) ───
            {
                "name": "system_event_grid",
                "title": "8. 시스템 이벤트",
                "charts": [],
                "grids": [
                    {**self.get_system_event_grid_data(days), "id": "SYSTEM_EVENT_GRID", "title": "시스템 이벤트 목록"},
                ],
            },
            # ─── 9. 설정 변경 이력 (Grid Only) ───
            {
                "name": "config_grid",
                "title": "9. 설정 변경 이력",
                "charts": [],
                "grids": [
                    {**self.get_config_grid_data(days), "id": "SYSTEM_CONFIG_GRID", "title": "설정 변경 이력"},
                ],
            },
            # ─── 10. 감사 로그 (Grid Only) ───
            {
                "name": "audit_grid",
                "title": "10. 감사 로그",
                "charts": [],
                "grids": [
                    {**self.get_audit_grid_data(days), "id": "SYSTEM_AUDIT_GRID", "title": "감사 로그"},
                ],
            },
            # ─── 11. 사용자 상세 (Grids Only) ───
            {
                "name": "user_grids",
                "title": "11. 사용자 상세",
                "charts": [],
                "grids": [
                    {**self.get_user_grid_data(), "id": "USER_GRID", "title": "사용자 목록"},
                    {**self.get_user_login_grid_data(days), "id": "USER_LOGIN_GRID", "title": "로그인 이력"},
                    {**self.get_user_session_grid_data(), "id": "USER_SESSION_GRID", "title": "세션 목록"},
                ],
            },
        ]

        # 비정형 보고서 필터링: enabled_components가 제공되면 해당 컴포넌트만 포함
        if enabled_components is not None:
            filtered = []
            for section in sections:
                # charts 필터링
                charts = [c for c in section.get("charts", []) if c.get("id") in enabled_components]
                # grids 필터링
                grids = [g for g in section.get("grids", []) if g.get("id") in enabled_components]

                # summary_data가 있고 SUMMARY_CARD가 enabled면 유지
                has_summary = section.get("summary_data") and "SUMMARY_CARD" in enabled_components

                if charts or grids or has_summary:
                    new_section = {
                        "name": section["name"],
                        "title": section["title"],
                        "charts": charts,
                        "grids": grids,
                    }
                    if section.get("summary_data") and has_summary:
                        new_section["summary_data"] = section["summary_data"]
                    filtered.append(new_section)
            sections = filtered

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
        """보고서 비동기 생성 — 마스터 디자인(HTML→PDF, Playwright/Chromium).

        PRD_Report_Master_Redesign: 정형=전 섹션, 비정형=template 컴포넌트 필터.
        """
        from app.services.report_master_builder import build_master_data, build_report_meta
        from app.services.report_html_renderer import render_report_html
        from app.utils.html_to_pdf import html_to_pdf_bytes

        generation = self.db.query(ReportGeneration).filter(
            ReportGeneration.id == generation_id
        ).first()
        if not generation:
            return

        try:
            generation.status = "GENERATING"
            self.db.commit()

            enabled = self.get_enabled_components(generation)
            enabled_set = set(enabled) if enabled is not None else None
            kind = "비정형" if generation.report_type == "CUSTOM" else "정형"
            meta = build_report_meta(generation)

            data = build_master_data(
                self.db, generation.start_date, generation.end_date, meta, enabled_set,
                severity_filter=generation.severity_filter,
            )
            html = render_report_html(data, mode="full")
            pdf_bytes = html_to_pdf_bytes(html)

            # v6.0-report_persistence FR-RPP-05: 저장 경로 env 외부화 (docker named volume)
            from app.config import settings
            reports_dir = settings.REPORTS_DIR
            os.makedirs(reports_dir, exist_ok=True)
            filename = f"report_{generation.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            file_path = os.path.join(reports_dir, filename)
            with open(file_path, "wb") as f:
                f.write(pdf_bytes)

            generation.status = "COMPLETED"
            generation.pdf_file_path = file_path
            generation.pdf_file_size = len(pdf_bytes)
            generation.completed_at = datetime.now()
            generation.summary_data = {
                "section_count": len(data["sections"]),
                "report_kind": kind,
            }
            self.db.commit()

        except Exception as e:
            generation.status = "FAILED"
            generation.error_message = str(e)
            self.db.commit()


# ======================================================================
# v6.0 Phase 3: ReportServiceAsync — AsyncSession 기반 완전 async 구현
# ======================================================================


class ReportServiceAsync:
    """보고서 데이터 수집 및 처리 서비스 (async).

    ReportService 와 동일 시그니처를 async 로 재작성.
    dual-stack: 기존 sync caller 는 ReportService, async caller 는 이 클래스.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _resolve_range(
        days: int,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
    ) -> tuple[datetime, Optional[datetime]]:
        """v6.1 필터 윈도우 통일 — start_date/end_date가 있으면 그 값을, 없으면 now-days 사용.

        end_date가 None이면 상한 필터 없음(현재까지).
        """
        if start_date is not None:
            _start = start_date.replace(tzinfo=None) if start_date.tzinfo else start_date
        else:
            _start = datetime.now() - timedelta(days=days)
        _end = None
        if end_date is not None:
            _end = end_date.replace(tzinfo=None) if end_date.tzinfo else end_date
        return _start, _end

    async def get_enabled_components(self, generation: ReportGeneration) -> Optional[List[str]]:
        """ReportGeneration 에서 활성화된 컴포넌트 ID 목록 추출."""
        if generation.report_type != "CUSTOM" or not generation.template_id:
            return None

        result = await self.db.execute(
            select(ReportTemplate).where(ReportTemplate.id == generation.template_id)
        )
        template = result.scalars().first()

        if not template or not template.components:
            return None

        return [
            c["id"] for c in template.components
            if c.get("enabled", True)
        ]

    async def get_device_statistics(self) -> Dict[str, Any]:
        """장비 통계 수집."""
        # Status counts
        status_counts: Dict[str, int] = {}
        status_result = await self.db.execute(
            select(Device.status, func.count(Device.id)).group_by(Device.status)
        )
        for status, count in status_result.all():
            status_counts[status.value if hasattr(status, 'value') else status] = count

        # Type (category_device) counts
        type_counts: Dict[str, int] = {}
        type_result = await self.db.execute(
            select(Device.category_device, func.count(Device.id)).group_by(Device.category_device)
        )
        for category, count in type_result.all():
            type_counts[category.value if hasattr(category, 'value') else category] = count

        return {
            "status_counts": status_counts,
            "type_counts": type_counts,
        }

    async def get_device_category_summary(self) -> List[Dict]:
        """카테고리별 장비 정상/전체 현황."""
        result = await self.db.execute(
            select(
                Device.category_device,
                func.count(Device.id).label('total'),
                func.sum(case((Device.status == 'ACTIVATED', 1), else_=0)).label('normal'),
            ).group_by(Device.category_device)
        )
        results = result.all()
        return [
            {
                "category": r.category_device.value if hasattr(r.category_device, 'value') else str(r.category_device),
                "total": r.total,
                "normal": int(r.normal or 0),
                "status": "all-normal" if int(r.normal or 0) == r.total else "has-issue",
            }
            for r in results
        ]

    async def get_server_status_summary(self) -> List[Dict]:
        """서버 카테고리별 상태 요약."""
        from app.models.server import ServerCategory, Server

        cat_result = await self.db.execute(
            select(ServerCategory).order_by(ServerCategory.sort_order)
        )
        categories = cat_result.scalars().all()

        result: List[Dict] = []
        for cat in categories:
            srv_result = await self.db.execute(
                select(Server).where(Server.category_id == cat.id)
            )
            servers = srv_result.scalars().all()
            worst_status = "normal"
            for s in servers:
                status_val = s.status.value if hasattr(s.status, 'value') else str(s.status) if s.status else ""
                if status_val == "ERROR":
                    worst_status = "error"
                    break
                elif status_val == "WARNING" and worst_status != "error":
                    worst_status = "warning"
            result.append({
                "name": cat.name,
                "status": worst_status,
                "count": len(servers),
            })
        return result

    async def get_event_statistics(
        self,
        days: int = 7,
        *,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """이벤트 통계 수집. v6.1: start_date/end_date 우선 사용."""
        _start, _end = self._resolve_range(days, start_date, end_date)

        def _range(col):
            cond = col >= _start
            return cond if _end is None else and_(cond, col <= _end)

        # Category-based counts
        detection_count = (await self.db.execute(
            select(func.count(DetectionEvent.id)).where(_range(DetectionEvent.created_at))
        )).scalar() or 0

        malfunction_count = (await self.db.execute(
            select(func.count(MalfunctionEvent.id)).where(_range(MalfunctionEvent.created_at))
        )).scalar() or 0

        action_count = (await self.db.execute(
            select(func.count(ActionEvent.id)).where(_range(ActionEvent.created_at))
        )).scalar() or 0

        event_type_counts = {
            "detection": detection_count,
            "malfunction": malfunction_count,
            "action": action_count,
        }

        # v6.1: dates 라벨을 실제 기간 [start_date.date() … end_date.date()] inclusive 생성 (오늘 포함).
        end_marker = _end or datetime.now()
        cur = _start.date()
        stop = end_marker.date()
        dates: List[str] = []
        while cur <= stop:
            dates.append(str(cur))
            cur += timedelta(days=1)

        # Detection daily trend
        detection_daily: Dict[str, int] = {}
        det_result = await self.db.execute(
            select(
                func.date(DetectionEvent.created_at).label("date"),
                func.count(DetectionEvent.id).label("count"),
            )
            .where(_range(DetectionEvent.created_at))
            .group_by(func.date(DetectionEvent.created_at))
        )
        for row in det_result.all():
            detection_daily[str(row.date)] = row.count

        # Malfunction daily trend
        malfunction_daily: Dict[str, int] = {}
        mal_result = await self.db.execute(
            select(
                func.date(MalfunctionEvent.created_at).label("date"),
                func.count(MalfunctionEvent.id).label("count"),
            )
            .where(_range(MalfunctionEvent.created_at))
            .group_by(func.date(MalfunctionEvent.created_at))
        )
        for row in mal_result.all():
            malfunction_daily[str(row.date)] = row.count

        # Action daily trend
        action_daily: Dict[str, int] = {}
        act_result = await self.db.execute(
            select(
                func.date(ActionEvent.created_at).label("date"),
                func.count(ActionEvent.id).label("count"),
            )
            .where(_range(ActionEvent.created_at))
            .group_by(func.date(ActionEvent.created_at))
        )
        for row in act_result.all():
            action_daily[str(row.date)] = row.count

        daily_trend = [
            {"label": "탐지", "values": [detection_daily.get(d, 0) for d in dates]},
            {"label": "장애", "values": [malfunction_daily.get(d, 0) for d in dates]},
            {"label": "조치", "values": [action_daily.get(d, 0) for d in dates]},
        ]

        return {
            "event_type_counts": event_type_counts,
            "daily_trend": daily_trend,
            "daily_labels": dates,
        }

    async def get_system_statistics(
        self,
        days: int = 7,
        *,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """시스템 이벤트 통계 수집. v6.1: 심각도 라벨 한국어 통일."""
        _start, _end = self._resolve_range(days, start_date, end_date)

        def _range(col):
            cond = col >= _start
            return cond if _end is None else and_(cond, col <= _end)

        # Severity counts (한국어 라벨)
        severity_counts: Dict[str, int] = {}
        sev_result = await self.db.execute(
            select(SystemEvent.severity, func.count(SystemEvent.id))
            .where(_range(SystemEvent.created_at))
            .group_by(SystemEvent.severity)
        )
        for severity, count in sev_result.all():
            severity_counts[L.label(L.SEVERITY, severity)] = count

        # Daily trend
        daily_trend: List[Dict] = []
        daily_result = await self.db.execute(
            select(
                func.date(SystemEvent.created_at).label("date"),
                func.count(SystemEvent.id).label("count"),
            )
            .where(_range(SystemEvent.created_at))
            .group_by(func.date(SystemEvent.created_at))
            .order_by(func.date(SystemEvent.created_at))
        )
        for row in daily_result.all():
            daily_trend.append({
                "date": str(row.date) if row.date else None,
                "count": row.count,
            })

        return {
            "severity_counts": severity_counts,
            "daily_trend": daily_trend,
        }

    async def get_user_statistics(
        self,
        days: int = 7,
        *,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """사용자 통계 수집. v6.1: role/result 한국어 라벨 통일 + start_date/end_date."""
        _start, _end = self._resolve_range(days, start_date, end_date)

        def _range(col):
            cond = col >= _start
            return cond if _end is None else and_(cond, col <= _end)

        # Role distribution (한국어 라벨)
        role_counts: Dict[str, int] = {}
        role_result = await self.db.execute(
            select(AccountUser.role, func.count(AccountUser.id)).group_by(AccountUser.role)
        )
        for role, count in role_result.all():
            role_counts[L.label(L.ROLE, role)] = count

        # Login daily trend (기간 필터 적용)
        login_daily_trend: List[Dict] = []
        login_result = await self.db.execute(
            select(
                func.date(UserLoginLog.created_at).label("date"),
                func.count(UserLoginLog.id).label("count"),
            )
            .where(_range(UserLoginLog.created_at))
            .group_by(func.date(UserLoginLog.created_at))
            .order_by(func.date(UserLoginLog.created_at))
        )
        for row in login_result.all():
            login_daily_trend.append({
                "date": str(row.date) if row.date else None,
                "count": row.count,
            })

        # Login result distribution (한국어 라벨)
        login_result_counts: Dict[str, int] = {}
        result_res = await self.db.execute(
            select(UserLoginLog.result, func.count(UserLoginLog.id))
            .where(_range(UserLoginLog.created_at))
            .group_by(UserLoginLog.result)
        )
        for result_val, count in result_res.all():
            login_result_counts[L.label(L.RESULT, result_val)] = count

        return {
            "role_counts": role_counts,
            "login_daily_trend": login_daily_trend,
            "login_result_counts": login_result_counts,
        }

    async def get_device_grid_data(self) -> Dict[str, Any]:
        """장비 목록 그리드 데이터."""
        columns = ["ID", "장비명", "장비유형", "버전", "상태", "활성"]
        result = await self.db.execute(select(Device))
        devices = result.scalars().all()
        rows = []
        for d in devices:
            rows.append([
                d.id,
                d.name_device or "",
                d.type_device.value if hasattr(d.type_device, 'value') else str(d.type_device) if d.type_device else d.category_device.value if hasattr(d.category_device, 'value') else "",
                d.version or "",
                d.status.value if hasattr(d.status, 'value') else str(d.status) if d.status else "",
                d.is_enable,
            ])
        return {"columns": columns, "rows": rows, "total_rows": len(rows)}

    async def get_detection_grid_data(
        self,
        days: int = 7,
        *,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """탐지 이벤트 그리드 데이터. v6.1: N+1 제거 (action 1회 batch fetch) + 라벨 통일."""
        columns = ["ID", "일시", "탐지유형", "장비유형", "장비명",
                   "조치보고일자", "조치자", "조치내용"]
        _start, _end = self._resolve_range(days, start_date, end_date)

        def _range(col):
            cond = col >= _start
            return cond if _end is None else and_(cond, col <= _end)

        events_result = await self.db.execute(
            select(DetectionEvent)
            .options(selectinload(DetectionEvent.device))
            .where(_range(DetectionEvent.created_at))
            .order_by(DetectionEvent.created_at.desc())
        )
        events = events_result.scalars().all()

        # v6.1 N+1 제거: 이벤트 ID 목록으로 action 1회 조회 → dict 매핑
        event_ids = [e.id for e in events]
        action_by_event: Dict[int, ActionEvent] = {}
        if event_ids:
            act_all = await self.db.execute(
                select(ActionEvent).where(ActionEvent.from_event_id.in_(event_ids))
            )
            for a in act_all.scalars().all():
                action_by_event.setdefault(a.from_event_id, a)

        rows = []
        for e in events:
            action = action_by_event.get(e.id)
            rows.append([
                e.id,
                e.created_at.strftime('%Y-%m-%d %H:%M:%S') if e.created_at else "",
                L.label(L.DETECTION, e.result),
                L.label(L.DEVICE_CATEGORY, e.device.category_device) if e.device else "",
                e.device.name_device if e.device else "",
                action.created_at.strftime('%Y-%m-%d %H:%M:%S') if action and action.created_at else "-",
                action.user if action else "-",
                action.content if action else "-",
            ])
        return {"columns": columns, "rows": rows, "total_rows": len(rows)}

    async def get_malfunction_grid_data(
        self,
        days: int = 7,
        *,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """장애 이벤트 그리드 데이터. v6.1: N+1 제거 + 라벨 통일."""
        columns = ["ID", "일시", "장애유형", "장비유형", "장비명",
                   "조치보고일자", "조치자", "조치내용"]
        _start, _end = self._resolve_range(days, start_date, end_date)

        def _range(col):
            cond = col >= _start
            return cond if _end is None else and_(cond, col <= _end)

        events_result = await self.db.execute(
            select(MalfunctionEvent)
            .options(selectinload(MalfunctionEvent.device))
            .where(_range(MalfunctionEvent.created_at))
            .order_by(MalfunctionEvent.created_at.desc())
        )
        events = events_result.scalars().all()

        # v6.1 N+1 제거
        event_ids = [e.id for e in events]
        action_by_event: Dict[int, ActionEvent] = {}
        if event_ids:
            act_all = await self.db.execute(
                select(ActionEvent).where(ActionEvent.from_event_id.in_(event_ids))
            )
            for a in act_all.scalars().all():
                action_by_event.setdefault(a.from_event_id, a)

        rows = []
        for e in events:
            action = action_by_event.get(e.id)
            rows.append([
                e.id,
                e.created_at.strftime('%Y-%m-%d %H:%M:%S') if e.created_at else "",
                L.label(L.FAULT, e.reason),
                L.label(L.DEVICE_CATEGORY, e.device.category_device) if e.device else "",
                e.device.name_device if e.device else "",
                action.created_at.strftime('%Y-%m-%d %H:%M:%S') if action and action.created_at else "-",
                action.user if action else "-",
                action.content if action else "-",
            ])
        return {"columns": columns, "rows": rows, "total_rows": len(rows)}

    async def get_action_grid_data(
        self,
        days: int = 7,
        *,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """조치 이벤트 그리드 데이터."""
        columns = ["ID", "일시", "이벤트유형", "내용", "조치자"]
        _start, _end = self._resolve_range(days, start_date, end_date)

        def _range(col):
            cond = col >= _start
            return cond if _end is None else and_(cond, col <= _end)

        result = await self.db.execute(
            select(ActionEvent)
            .where(_range(ActionEvent.created_at))
            .order_by(ActionEvent.created_at.desc())
            .limit(100)
        )
        events = result.scalars().all()
        rows = []
        for e in events:
            rows.append([
                e.id,
                e.created_at.strftime('%Y-%m-%d %H:%M:%S') if e.created_at else "",
                L.label(L.ACTION_TYPE, e.type_event) if e.type_event else "",
                getattr(e, 'content', "") or "",
                getattr(e, 'user', "") or "",
            ])
        return {"columns": columns, "rows": rows, "total_rows": len(rows)}

    async def get_system_event_grid_data(
        self,
        days: int = 7,
        *,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """시스템 이벤트 그리드 데이터. v6.1: title 컬럼 추가 + 라벨 통일."""
        columns = ["ID", "일시", "유형", "심각도", "제목", "메시지"]
        _start, _end = self._resolve_range(days, start_date, end_date)

        def _range(col):
            cond = col >= _start
            return cond if _end is None else and_(cond, col <= _end)

        result = await self.db.execute(
            select(SystemEvent)
            .where(_range(SystemEvent.created_at))
            .order_by(SystemEvent.created_at.desc())
            .limit(100)
        )
        events = result.scalars().all()
        rows = []
        for e in events:
            rows.append([
                e.id,
                e.created_at.strftime('%Y-%m-%d %H:%M:%S') if e.created_at else "",
                L.label(L.SYSTEM_EVENT, e.type_event),
                L.label(L.SEVERITY, e.severity),
                e.title or "",
                e.message or "",
            ])
        return {"columns": columns, "rows": rows, "total_rows": len(rows)}

    async def get_config_grid_data(
        self,
        days: int = 7,
        *,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """설정 변경 이력 그리드 데이터. v6.1: actor/resource_name/description 컬럼 확장 + 라벨 통일."""
        columns = ["ID", "일시", "행위자", "IP", "리소스유형", "리소스명", "액션", "변경설명"]
        _start, _end = self._resolve_range(days, start_date, end_date)

        def _range(col):
            cond = col >= _start
            return cond if _end is None else and_(cond, col <= _end)

        result = await self.db.execute(
            select(ConfigChangeLog)
            .where(_range(ConfigChangeLog.created_at))
            .order_by(ConfigChangeLog.created_at.desc())
            .limit(100)
        )
        logs = result.scalars().all()
        rows = []
        for log in logs:
            rows.append([
                log.id,
                log.created_at.strftime('%Y-%m-%d %H:%M:%S') if log.created_at else "",
                getattr(log, 'actor_name', None) or "(system)",
                getattr(log, 'actor_ip', None) or "",
                L.label(L.CONFIG_RESOURCE, log.resource_type),
                getattr(log, 'resource_name', None) or (str(getattr(log, 'resource_id', '')) if getattr(log, 'resource_id', None) is not None else ""),
                L.label(L.CONFIG_ACTION, log.action),
                getattr(log, 'description', None) or "",
            ])
        return {"columns": columns, "rows": rows, "total_rows": len(rows)}

    async def get_audit_grid_data(
        self,
        days: int = 7,
        *,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """감사 로그 그리드 데이터. v6.1: actor_login_id 폴백 + 라벨 통일."""
        columns = ["ID", "일시", "액션", "상태", "리소스", "행위자"]
        _start, _end = self._resolve_range(days, start_date, end_date)

        def _range(col):
            cond = col >= _start
            return cond if _end is None else and_(cond, col <= _end)

        result = await self.db.execute(
            select(AuditLog)
            .where(_range(AuditLog.created_at))
            .order_by(AuditLog.created_at.desc())
            .limit(100)
        )
        logs = result.scalars().all()
        rows = []
        for log in logs:
            actor = log.actor_name or getattr(log, 'actor_login_id', None) or "(system)"
            rows.append([
                log.id,
                log.created_at.strftime('%Y-%m-%d %H:%M:%S') if log.created_at else "",
                L.label(L.AUDIT_ACTION, log.action_type),
                L.label(L.RESULT, log.action_status),
                L.label(L.AUDIT_RESOURCE, log.resource_type),
                actor,
            ])
        return {"columns": columns, "rows": rows, "total_rows": len(rows)}

    async def get_user_grid_data(self) -> Dict[str, Any]:
        """사용자 목록 그리드 데이터. v6.1: role 한국어 라벨 통일."""
        columns = ["ID", "로그인ID", "이름", "역할", "이메일"]
        result = await self.db.execute(select(AccountUser))
        users = result.scalars().all()
        rows = []
        for u in users:
            rows.append([
                u.id,
                u.login_id or "",
                u.name or "",
                L.label(L.ROLE, u.role),
                u.email or "",
            ])
        return {"columns": columns, "rows": rows, "total_rows": len(rows)}

    async def get_user_login_grid_data(
        self,
        days: int = 7,
        *,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """로그인 이력 그리드 데이터. v6.1: 라벨 통일."""
        columns = ["ID", "일시", "로그인ID", "액션", "결과", "IP"]
        _start, _end = self._resolve_range(days, start_date, end_date)

        def _range(col):
            cond = col >= _start
            return cond if _end is None else and_(cond, col <= _end)

        result = await self.db.execute(
            select(UserLoginLog)
            .where(_range(UserLoginLog.created_at))
            .order_by(UserLoginLog.created_at.desc())
            .limit(100)
        )
        logs = result.scalars().all()
        rows = []
        for log in logs:
            rows.append([
                log.id,
                log.created_at.strftime('%Y-%m-%d %H:%M:%S') if log.created_at else "",
                log.login_id or "",
                L.label(L.LOGIN_ACTION, log.action),
                L.label(L.RESULT, log.result),
                log.ip_address or "",
            ])
        return {"columns": columns, "rows": rows, "total_rows": len(rows)}

    async def get_user_session_grid_data(self) -> Dict[str, Any]:
        """사용자 세션 그리드 데이터. v6.1: account_users LEFT JOIN 으로 로그인ID/사용자명 노출."""
        columns = ["ID", "로그인ID", "사용자명", "IP", "생성일", "만료일"]
        result = await self.db.execute(
            select(
                UserSession.id,
                UserSession.user_id,
                UserSession.ip_address,
                UserSession.created_at,
                UserSession.expires_at,
                AccountUser.login_id,
                AccountUser.name,
            )
            .outerjoin(AccountUser, AccountUser.id == UserSession.user_id)
            .order_by(UserSession.created_at.desc())
            .limit(100)
        )
        rows = []
        for r in result.all():
            rows.append([
                r.id,
                r.login_id or f"(uid:{r.user_id})",
                r.name or "",
                r.ip_address or "",
                r.created_at.strftime('%Y-%m-%d %H:%M:%S') if r.created_at else "",
                r.expires_at.strftime('%Y-%m-%d %H:%M:%S') if r.expires_at else "",
            ])
        return {"columns": columns, "rows": rows, "total_rows": len(rows)}

    async def get_structured_preview_data(
        self,
        days: int = 7,
        enabled_components: Optional[List[str]] = None,
        *,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """구조화된 보고서 미리보기 데이터 생성 (11섹션).

        v6.1: start_date/end_date 우선 사용 (없으면 days로 now-N일 fallback).
        HTML/PDF 파이프라인(build_master_data_async)과 필터 소스 통일.
        """
        rng = {"start_date": start_date, "end_date": end_date}

        device_stats = await self.get_device_statistics()
        event_stats = await self.get_event_statistics(days, **rng)
        system_stats = await self.get_system_statistics(days, **rng)
        user_stats = await self.get_user_statistics(days, **rng)
        device_categories = await self.get_device_category_summary()
        server_status = await self.get_server_status_summary()

        device_grid = await self.get_device_grid_data()
        detection_grid = await self.get_detection_grid_data(days, **rng)
        malfunction_grid = await self.get_malfunction_grid_data(days, **rng)
        action_grid = await self.get_action_grid_data(days, **rng)
        system_event_grid = await self.get_system_event_grid_data(days, **rng)
        config_grid = await self.get_config_grid_data(days, **rng)
        audit_grid = await self.get_audit_grid_data(days, **rng)
        user_grid = await self.get_user_grid_data()
        user_login_grid = await self.get_user_login_grid_data(days, **rng)
        user_session_grid = await self.get_user_session_grid_data()

        sections = [
            # ─── 1. 요약 ───
            {
                "name": "summary",
                "title": "1. 요약",
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
                            ],
                        },
                    }
                ],
                "grids": [],
                "summary_data": {
                    "device_categories": device_categories,
                    "event_counts": event_stats["event_type_counts"],
                    "server_status": server_status,
                },
            },
            # ─── 2. 장비 현황 ───
            {
                "name": "device_charts",
                "title": "2. 장비 현황",
                "charts": [
                    {
                        "id": "DEVICE_STATUS_PIE",
                        "title": "장비 상태 분포",
                        "type": "PIE",
                        "data": {
                            "labels": list(device_stats["status_counts"].keys()),
                            "values": list(device_stats["status_counts"].values()),
                            "colors": ["#4CAF50", "#F44336", "#9E9E9E"],
                        },
                    },
                    {
                        "id": "DEVICE_TYPE_BAR",
                        "title": "유형별 장비 현황",
                        "type": "BAR",
                        "data": {
                            "labels": list(device_stats["type_counts"].keys()),
                            "values": list(device_stats["type_counts"].values()),
                        },
                    },
                ],
                "grids": [],
            },
            # ─── 3. 이벤트 현황 ───
            {
                "name": "event_charts",
                "title": "3. 이벤트 현황",
                "charts": [
                    {
                        "id": "EVENT_SUMMARY_PIE",
                        "title": "이벤트 유형 분포",
                        "type": "PIE",
                        "data": {
                            "labels": list(event_stats["event_type_counts"].keys()),
                            "values": list(event_stats["event_type_counts"].values()),
                        },
                    },
                    {
                        "id": "EVENT_TREND_LINE",
                        "title": "이벤트 발생 추이",
                        "type": "LINE",
                        "data": {
                            "labels": event_stats.get("daily_labels", []),
                            "values": [],
                            "datasets": event_stats["daily_trend"],
                        },
                    },
                ],
                "grids": [],
            },
            # ─── 4. 시스템 현황 ───
            {
                "name": "system_charts",
                "title": "4. 시스템 현황",
                "charts": [
                    {
                        "id": "SYSTEM_SEVERITY_BAR",
                        "title": "심각도별 시스템 이벤트",
                        "type": "BAR",
                        "data": {
                            "labels": list(system_stats["severity_counts"].keys()),
                            "values": list(system_stats["severity_counts"].values()),
                        },
                    },
                    {
                        "id": "SYSTEM_TREND_LINE",
                        "title": "시스템 이벤트 추이",
                        "type": "LINE",
                        "data": {
                            "labels": [d["date"] for d in system_stats["daily_trend"]],
                            "values": [d["count"] for d in system_stats["daily_trend"]],
                        },
                    },
                ],
                "grids": [],
            },
            # ─── 5. 사용자 현황 ───
            {
                "name": "user_charts",
                "title": "5. 사용자 현황",
                "charts": [
                    {
                        "id": "USER_ROLE_PIE",
                        "title": "역할별 사용자 분포",
                        "type": "PIE",
                        "data": {
                            "labels": list(user_stats["role_counts"].keys()),
                            "values": list(user_stats["role_counts"].values()),
                        },
                    },
                    {
                        "id": "USER_LOGIN_TREND_LINE",
                        "title": "일별 로그인 추이",
                        "type": "LINE",
                        "data": {
                            "labels": [d["date"] for d in user_stats["login_daily_trend"]],
                            "values": [d["count"] for d in user_stats["login_daily_trend"]],
                        },
                    },
                    {
                        "id": "USER_LOGIN_RESULT_PIE",
                        "title": "로그인 성공/실패 분포",
                        "type": "PIE",
                        "data": {
                            "labels": list(user_stats["login_result_counts"].keys()),
                            "values": list(user_stats["login_result_counts"].values()),
                        },
                    },
                ],
                "grids": [],
            },
            # ─── 6. 장비 목록 ───
            {
                "name": "device_grid",
                "title": "6. 장비 목록",
                "charts": [],
                "grids": [
                    {**device_grid, "id": "DEVICE_GRID", "title": "장비 목록"},
                ],
            },
            # ─── 7. 이벤트 상세 ───
            {
                "name": "event_grids",
                "title": "7. 이벤트 상세",
                "charts": [],
                "grids": [
                    {**detection_grid, "id": "EVENT_DETECTION_GRID", "title": "탐지 이벤트 목록"},
                    {**malfunction_grid, "id": "EVENT_MALFUNCTION_GRID", "title": "장애 이벤트 목록"},
                    {**action_grid, "id": "EVENT_ACTION_GRID", "title": "조치 이벤트 목록"},
                ],
            },
            # ─── 8. 시스템 이벤트 ───
            {
                "name": "system_event_grid",
                "title": "8. 시스템 이벤트",
                "charts": [],
                "grids": [
                    {**system_event_grid, "id": "SYSTEM_EVENT_GRID", "title": "시스템 이벤트 목록"},
                ],
            },
            # ─── 9. 설정 변경 이력 ───
            {
                "name": "config_grid",
                "title": "9. 설정 변경 이력",
                "charts": [],
                "grids": [
                    {**config_grid, "id": "SYSTEM_CONFIG_GRID", "title": "설정 변경 이력"},
                ],
            },
            # ─── 10. 감사 로그 ───
            {
                "name": "audit_grid",
                "title": "10. 감사 로그",
                "charts": [],
                "grids": [
                    {**audit_grid, "id": "SYSTEM_AUDIT_GRID", "title": "감사 로그"},
                ],
            },
            # ─── 11. 사용자 상세 ───
            {
                "name": "user_grids",
                "title": "11. 사용자 상세",
                "charts": [],
                "grids": [
                    {**user_grid, "id": "USER_GRID", "title": "사용자 목록"},
                    {**user_login_grid, "id": "USER_LOGIN_GRID", "title": "로그인 이력"},
                    {**user_session_grid, "id": "USER_SESSION_GRID", "title": "세션 목록"},
                ],
            },
        ]

        # 비정형 보고서 필터링
        if enabled_components is not None:
            filtered = []
            for section in sections:
                charts = [c for c in section.get("charts", []) if c.get("id") in enabled_components]
                grids = [g for g in section.get("grids", []) if g.get("id") in enabled_components]
                has_summary = section.get("summary_data") and "SUMMARY_CARD" in enabled_components
                if charts or grids or has_summary:
                    new_section = {
                        "name": section["name"],
                        "title": section["title"],
                        "charts": charts,
                        "grids": grids,
                    }
                    if section.get("summary_data") and has_summary:
                        new_section["summary_data"] = section["summary_data"]
                    filtered.append(new_section)
            sections = filtered

        return {"sections": sections}

    async def get_preview_data(self, days: int = 7) -> Dict[str, Any]:
        """보고서 미리보기 데이터 생성 (legacy 4섹션)."""
        device_stats = await self.get_device_statistics()
        event_stats = await self.get_event_statistics(days)
        system_stats = await self.get_system_statistics(days)

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
                        },
                    }
                ],
            },
            {
                "title": "장비 현황",
                "charts": [
                    {"type": "DEVICE_STATUS_PIE", "data": device_stats["status_counts"]},
                    {"type": "DEVICE_TYPE_BAR", "data": device_stats["type_counts"]},
                ],
                "grids": [{"type": "DEVICE_GRID", "data": []}],
            },
            {
                "title": "이벤트 현황",
                "charts": [
                    {"type": "EVENT_SUMMARY_PIE", "data": event_stats["event_type_counts"]},
                    {"type": "EVENT_TREND_LINE", "data": event_stats["daily_trend"]},
                ],
                "grids": [{"type": "EVENT_DETECTION_GRID", "data": []}],
            },
            {
                "title": "시스템 현황",
                "charts": [
                    {"type": "SYSTEM_SEVERITY_BAR", "data": system_stats["severity_counts"]},
                    {"type": "SYSTEM_TREND_LINE", "data": system_stats["daily_trend"]},
                ],
                "grids": [{"type": "SYSTEM_EVENT_GRID", "data": []}],
            },
        ]

        return {"sections": sections}

    async def generate_report(self, generation_id: int) -> None:
        """보고서 비동기 생성 — 마스터 디자인(HTML→PDF).

        NOTE: build_master_data 는 현재 sync Session 기반. Phase 3 범위에서는
        AsyncSession 만으로 대체 불가하여, 이 메서드는 async caller 에서 별도
        sync bridge (run_in_executor 등) 로 처리해야 함. 여기서는 async 파사드만
        제공하고, 실제 sync 구현은 ReportService.generate_report_async 를 재사용
        하지 않고 상위 라우터에서 BackgroundTasks 로 sync 함수 스케쥴을 유지한다.
        """
        raise NotImplementedError(
            "generate_report_async(sync) 를 BackgroundTasks 로 스케쥴하십시오. "
            "master builder 완전 async 화는 별도 Phase."
        )
