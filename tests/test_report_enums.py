"""
Test: Report System Enum 타입 정의 검증
PRD: PRD_Report_System.md Section 3
"""
from enum import Enum


def test_enum_report_type_exists():
    """Test that EnumReportType exists and has STANDARD, CUSTOM values"""
    from app.utils.enums import EnumReportType

    assert issubclass(EnumReportType, Enum), "EnumReportType should be an Enum"

    # Test required values exist (name check)
    required_names = ["STANDARD", "CUSTOM"]
    enum_names = [member.name for member in EnumReportType]

    for name in required_names:
        assert name in enum_names, f"{name} should be in EnumReportType"

    # Test values match PRD (str, Enum)
    assert EnumReportType.STANDARD.value == "STANDARD"
    assert EnumReportType.CUSTOM.value == "CUSTOM"


def test_enum_report_period_exists():
    """Test that EnumReportPeriod exists and has 7d, 30d, 90d, 1y values"""
    from app.utils.enums import EnumReportPeriod

    assert issubclass(EnumReportPeriod, Enum), "EnumReportPeriod should be an Enum"

    # Test required values exist (name check)
    required_names = ["DAYS_7", "DAYS_30", "DAYS_90", "YEAR_1"]
    enum_names = [member.name for member in EnumReportPeriod]

    for name in required_names:
        assert name in enum_names, f"{name} should be in EnumReportPeriod"

    # Test values match PRD (str values)
    assert EnumReportPeriod.DAYS_7.value == "7d"
    assert EnumReportPeriod.DAYS_30.value == "30d"
    assert EnumReportPeriod.DAYS_90.value == "90d"
    assert EnumReportPeriod.YEAR_1.value == "1y"


def test_enum_report_status_exists():
    """Test that EnumReportStatus exists and has PENDING, GENERATING, COMPLETED, FAILED values"""
    from app.utils.enums import EnumReportStatus

    assert issubclass(EnumReportStatus, Enum), "EnumReportStatus should be an Enum"

    # Test required values exist
    required_names = ["PENDING", "GENERATING", "COMPLETED", "FAILED"]
    enum_names = [member.name for member in EnumReportStatus]

    for name in required_names:
        assert name in enum_names, f"{name} should be in EnumReportStatus"

    # Test values match PRD
    assert EnumReportStatus.PENDING.value == "PENDING"
    assert EnumReportStatus.GENERATING.value == "GENERATING"
    assert EnumReportStatus.COMPLETED.value == "COMPLETED"
    assert EnumReportStatus.FAILED.value == "FAILED"


def test_enum_chart_type_exists():
    """Test that EnumChartType exists and has LINE, BAR, DONUT, PIE values"""
    from app.utils.enums import EnumChartType

    assert issubclass(EnumChartType, Enum), "EnumChartType should be an Enum"

    # Test required values exist
    required_names = ["LINE", "BAR", "DONUT", "PIE"]
    enum_names = [member.name for member in EnumChartType]

    for name in required_names:
        assert name in enum_names, f"{name} should be in EnumChartType"

    # Test values match PRD
    assert EnumChartType.LINE.value == "LINE"
    assert EnumChartType.BAR.value == "BAR"
    assert EnumChartType.DONUT.value == "DONUT"
    assert EnumChartType.PIE.value == "PIE"


def test_enum_report_component_exists():
    """Test that EnumReportComponent exists and has 21 component values (PRD v1.4)"""
    from app.utils.enums import EnumReportComponent

    assert issubclass(EnumReportComponent, Enum), "EnumReportComponent should be an Enum"

    # Test all 21 required components exist (PRD Section 3.1, v1.4)
    required_names = [
        # SUMMARY (1종)
        "SUMMARY_CARD",
        # DEVICE (3종)
        "DEVICE_STATUS_PIE", "DEVICE_TYPE_BAR", "DEVICE_GRID",
        # EVENT (6종)
        "EVENT_SUMMARY_PIE", "EVENT_TREND_LINE", "EVENT_DAILY_BAR",
        "EVENT_DETECTION_GRID", "EVENT_MALFUNCTION_GRID", "EVENT_ACTION_GRID",
        # SYSTEM (5종)
        "SYSTEM_SEVERITY_BAR", "SYSTEM_TREND_LINE", "SYSTEM_CONFIG_GRID",
        "SYSTEM_EVENT_GRID", "SYSTEM_AUDIT_GRID",
        # USER (6종) - v1.4
        "USER_ROLE_PIE", "USER_LOGIN_TREND_LINE", "USER_LOGIN_RESULT_PIE",
        "USER_GRID", "USER_LOGIN_GRID", "USER_SESSION_GRID"
    ]
    enum_names = [member.name for member in EnumReportComponent]

    assert len(enum_names) == 21, f"EnumReportComponent should have 21 values, got {len(enum_names)}"

    for name in required_names:
        assert name in enum_names, f"{name} should be in EnumReportComponent"
