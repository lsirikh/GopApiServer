"""
Report System initial data (Seed)
Based on PRD_Report_System.md Section 3.1

샘플 보고서 템플릿 5종:
1. 주간 운영 보고서 - 전체 운영 현황 요약
2. 장비 상태 보고서 - 디바이스 중심 분석
3. 이벤트 분석 보고서 - 이벤트 탐지/장애 분석
4. 보안 감사 보고서 - 시스템/사용자 보안 감사
5. 월간 종합 보고서 - 전체 컴포넌트 포함
"""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.report import ReportTemplate
from app.utils.enums import EnumReportType, EnumReportPeriod, EnumReportComponent


# ============================================================
# 샘플 보고서 템플릿 데이터 (5종)
# ============================================================

SAMPLE_REPORT_TEMPLATES = [
    # 1. 주간 운영 보고서 (Weekly Operation Report)
    {
        "name": "주간 운영 보고서",
        "description": "주간 단위 전체 운영 현황을 요약하는 표준 보고서입니다. 요약 카드, 장비 상태, 이벤트 추이를 포함합니다.",
        "report_type": EnumReportType.STANDARD.value,
        "is_public": True,
        "default_period": EnumReportPeriod.DAYS_7.value,
        "components": [
            {"id": EnumReportComponent.SUMMARY_CARD.value, "order": 1, "enabled": True, "title": "운영 요약"},
            {"id": EnumReportComponent.DEVICE_STATUS_PIE.value, "order": 2, "enabled": True, "title": "장비 상태 분포"},
            {"id": EnumReportComponent.EVENT_TREND_LINE.value, "order": 3, "enabled": True, "title": "이벤트 발생 추이"},
            {"id": EnumReportComponent.EVENT_SUMMARY_PIE.value, "order": 4, "enabled": True, "title": "이벤트 유형 분포"},
            {"id": EnumReportComponent.SYSTEM_SEVERITY_BAR.value, "order": 5, "enabled": True, "title": "심각도별 시스템 이벤트"},
        ],
    },
    # 2. 장비 상태 보고서 (Device Status Report)
    {
        "name": "장비 상태 보고서",
        "description": "디바이스 현황 중심의 보고서입니다. 장비 상태, 유형별 분포, 장비 목록 및 장애 이력을 확인할 수 있습니다.",
        "report_type": EnumReportType.STANDARD.value,
        "is_public": True,
        "default_period": EnumReportPeriod.DAYS_30.value,
        "components": [
            {"id": EnumReportComponent.SUMMARY_CARD.value, "order": 1, "enabled": True, "title": "장비 요약"},
            {"id": EnumReportComponent.DEVICE_STATUS_PIE.value, "order": 2, "enabled": True, "title": "장비 상태 분포"},
            {"id": EnumReportComponent.DEVICE_TYPE_BAR.value, "order": 3, "enabled": True, "title": "유형별 장비 수"},
            {"id": EnumReportComponent.DEVICE_GRID.value, "order": 4, "enabled": True, "title": "장비 목록"},
            {"id": EnumReportComponent.EVENT_MALFUNCTION_GRID.value, "order": 5, "enabled": True, "title": "장애 이력"},
        ],
    },
    # 3. 이벤트 분석 보고서 (Event Analysis Report)
    {
        "name": "이벤트 분석 보고서",
        "description": "이벤트 탐지 및 장애 분석에 특화된 보고서입니다. 일별 이벤트 추이, 탐지/장애/조치 이력을 상세히 확인할 수 있습니다.",
        "report_type": EnumReportType.STANDARD.value,
        "is_public": True,
        "default_period": EnumReportPeriod.DAYS_7.value,
        "components": [
            {"id": EnumReportComponent.SUMMARY_CARD.value, "order": 1, "enabled": True, "title": "이벤트 요약"},
            {"id": EnumReportComponent.EVENT_SUMMARY_PIE.value, "order": 2, "enabled": True, "title": "이벤트 유형 분포"},
            {"id": EnumReportComponent.EVENT_TREND_LINE.value, "order": 3, "enabled": True, "title": "이벤트 발생 추이"},
            {"id": EnumReportComponent.EVENT_DAILY_BAR.value, "order": 4, "enabled": True, "title": "일별 이벤트 현황"},
            {"id": EnumReportComponent.EVENT_DETECTION_GRID.value, "order": 5, "enabled": True, "title": "탐지 이벤트 목록"},
            {"id": EnumReportComponent.EVENT_MALFUNCTION_GRID.value, "order": 6, "enabled": True, "title": "장애 이벤트 목록"},
            {"id": EnumReportComponent.EVENT_ACTION_GRID.value, "order": 7, "enabled": True, "title": "조치 이력"},
        ],
    },
    # 4. 보안 감사 보고서 (Security Audit Report)
    {
        "name": "보안 감사 보고서",
        "description": "시스템 보안 및 사용자 활동 감사를 위한 보고서입니다. 로그인 현황, 감사 로그, 설정 변경 이력을 포함합니다.",
        "report_type": EnumReportType.CUSTOM.value,
        "is_public": False,
        "default_period": EnumReportPeriod.DAYS_90.value,
        "components": [
            {"id": EnumReportComponent.SUMMARY_CARD.value, "order": 1, "enabled": True, "title": "보안 요약"},
            {"id": EnumReportComponent.USER_LOGIN_RESULT_PIE.value, "order": 2, "enabled": True, "title": "로그인 성공/실패 분포"},
            {"id": EnumReportComponent.USER_LOGIN_TREND_LINE.value, "order": 3, "enabled": True, "title": "일별 로그인 추이"},
            {"id": EnumReportComponent.SYSTEM_AUDIT_GRID.value, "order": 4, "enabled": True, "title": "감사 로그"},
            {"id": EnumReportComponent.SYSTEM_CONFIG_GRID.value, "order": 5, "enabled": True, "title": "설정 변경 이력"},
            {"id": EnumReportComponent.USER_SESSION_GRID.value, "order": 6, "enabled": True, "title": "세션 목록"},
            {"id": EnumReportComponent.SYSTEM_EVENT_GRID.value, "order": 7, "enabled": True, "title": "시스템 이벤트"},
        ],
    },
    # 5. 월간 종합 보고서 (Monthly Comprehensive Report)
    {
        "name": "월간 종합 보고서",
        "description": "월간 전체 운영 현황을 종합적으로 분석하는 보고서입니다. 장비, 이벤트, 시스템, 사용자 전 영역을 포함합니다.",
        "report_type": EnumReportType.STANDARD.value,
        "is_public": True,
        "default_period": EnumReportPeriod.DAYS_30.value,
        "components": [
            {"id": EnumReportComponent.SUMMARY_CARD.value, "order": 1, "enabled": True, "title": "종합 요약"},
            {"id": EnumReportComponent.DEVICE_STATUS_PIE.value, "order": 2, "enabled": True, "title": "장비 상태"},
            {"id": EnumReportComponent.DEVICE_TYPE_BAR.value, "order": 3, "enabled": True, "title": "유형별 장비"},
            {"id": EnumReportComponent.EVENT_TREND_LINE.value, "order": 4, "enabled": True, "title": "이벤트 추이"},
            {"id": EnumReportComponent.EVENT_DAILY_BAR.value, "order": 5, "enabled": True, "title": "일별 이벤트"},
            {"id": EnumReportComponent.SYSTEM_SEVERITY_BAR.value, "order": 6, "enabled": True, "title": "심각도별 이벤트"},
            {"id": EnumReportComponent.SYSTEM_TREND_LINE.value, "order": 7, "enabled": True, "title": "시스템 이벤트 추이"},
            {"id": EnumReportComponent.USER_ROLE_PIE.value, "order": 8, "enabled": True, "title": "사용자 역할 분포"},
            {"id": EnumReportComponent.USER_LOGIN_TREND_LINE.value, "order": 9, "enabled": True, "title": "로그인 추이"},
            {"id": EnumReportComponent.DEVICE_GRID.value, "order": 10, "enabled": True, "title": "장비 목록"},
            {"id": EnumReportComponent.EVENT_DETECTION_GRID.value, "order": 11, "enabled": True, "title": "탐지 이력"},
            {"id": EnumReportComponent.USER_GRID.value, "order": 12, "enabled": True, "title": "사용자 목록"},
        ],
    },
]


def create_sample_report_templates(db: Session):
    """
    Create sample report templates if none exist.

    Args:
        db: Database session
    """
    existing_count = db.query(ReportTemplate).count()
    if existing_count > 0:
        print(f"[OK] Report templates already exist: {existing_count}")
        return

    created_count = 0
    for tmpl_data in SAMPLE_REPORT_TEMPLATES:
        template = ReportTemplate(**tmpl_data)
        db.add(template)
        created_count += 1

    db.commit()
    print(f"[OK] Sample report templates created: {created_count}")


def initialize_report_data(db: Session):
    """
    Initialize report system data.

    Args:
        db: Database session
    """
    print("Initializing report data...")
    create_sample_report_templates(db)
    print("[OK] Report data initialization complete")


# ============================================================
# Async variants (v6.0 P8 dual-stack)
# ============================================================

async def create_sample_report_templates_async(db: AsyncSession) -> None:
    """
    Create sample report templates if none exist (async variant).

    Args:
        db: Async database session
    """
    result = await db.execute(select(func.count()).select_from(ReportTemplate))
    existing_count = result.scalar() or 0
    if existing_count > 0:
        print(f"[OK] Report templates already exist: {existing_count}")
        return

    created_count = 0
    for tmpl_data in SAMPLE_REPORT_TEMPLATES:
        template = ReportTemplate(**tmpl_data)
        db.add(template)
        created_count += 1

    await db.commit()
    print(f"[OK] Sample report templates created: {created_count}")


async def initialize_report_data_async(db: AsyncSession) -> None:
    """
    Initialize report system data (async variant).

    Args:
        db: Async database session
    """
    print("Initializing report data...")
    await create_sample_report_templates_async(db)
    print("[OK] Report data initialization complete")
