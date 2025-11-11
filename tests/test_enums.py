"""
Test: Enum 타입 정의 검증
"""
from enum import Enum


def test_enum_device_type_exists():
    """Test that EnumDeviceType exists and has all required values"""
    from app.utils.enums import EnumDeviceType

    assert issubclass(EnumDeviceType, Enum), "EnumDeviceType should be an Enum"

    # Test all required values exist
    required_values = [
        "NONE", "Controller", "Multi", "Fence", "Underground", "Contact",
        "PIR", "IoController", "Laser", "Cable", "IpCamera", "SmartSensor",
        "SmartSensor2", "SmartCompound", "IpSpeaker", "Radar", "OpticalCable", "Fence_Group"
    ]

    enum_values = [member.name for member in EnumDeviceType]
    for value in required_values:
        assert value in enum_values, f"{value} should be in EnumDeviceType"


def test_enum_device_status_exists():
    """Test that EnumDeviceStatus exists"""
    from app.utils.enums import EnumDeviceStatus

    assert issubclass(EnumDeviceStatus, Enum), "EnumDeviceStatus should be an Enum"

    required_values = ["ACTIVATED", "ERROR", "DEACTIVATED"]
    enum_values = [member.name for member in EnumDeviceStatus]

    for value in required_values:
        assert value in enum_values, f"{value} should be in EnumDeviceStatus"


def test_enum_camera_mode_exists():
    """Test that EnumCameraMode exists"""
    from app.utils.enums import EnumCameraMode

    assert issubclass(EnumCameraMode, Enum), "EnumCameraMode should be an Enum"

    required_values = ["NONE", "ONVIF", "EMSTONE_API", "INNODEP_API", "ETC"]
    enum_values = [member.name for member in EnumCameraMode]

    for value in required_values:
        assert value in enum_values, f"{value} should be in EnumCameraMode"


def test_enum_camera_type_exists():
    """Test that EnumCameraType exists"""
    from app.utils.enums import EnumCameraType

    assert issubclass(EnumCameraType, Enum), "EnumCameraType should be an Enum"

    required_values = ["NONE", "FIXED", "PTZ", "FISHEYES", "THERMAL"]
    enum_values = [member.name for member in EnumCameraType]

    for value in required_values:
        assert value in enum_values, f"{value} should be in EnumCameraType"


def test_enum_event_type_exists():
    """Test that EnumEventType exists"""
    from app.utils.enums import EnumEventType

    assert issubclass(EnumEventType, Enum), "EnumEventType should be an Enum"

    # Test enum members (using None_ instead of None due to Python keyword)
    required_values = ["None_", "Intrusion", "ContactOn", "ContactOff", "Connection", "Action", "Fault", "WindyMode"]
    enum_values = [member.name for member in EnumEventType]

    for value in required_values:
        assert value in enum_values, f"{value} should be in EnumEventType"

    # Test that "None" string value works via _missing_
    assert EnumEventType("None") == EnumEventType.None_, "Should support 'None' string via _missing_"


def test_enum_detection_type_exists():
    """Test that EnumDetectionType exists"""
    from app.utils.enums import EnumDetectionType

    assert issubclass(EnumDetectionType, Enum), "EnumDetectionType should be an Enum"

    required_values = [
        "NONE", "CABLE_CUTTING", "CABLE_CONNECTED", "PIR_SENSOR",
        "THERMAL_SENSOR", "VIBRATION_SENSOR", "CONTACT_SENSOR", "DISTANCE_SENSOR"
    ]
    enum_values = [member.name for member in EnumDetectionType]

    for value in required_values:
        assert value in enum_values, f"{value} should be in EnumDetectionType"


def test_enum_fault_type_exists():
    """Test that EnumFaultType exists"""
    from app.utils.enums import EnumFaultType

    assert issubclass(EnumFaultType, Enum), "EnumFaultType should be an Enum"

    required_values = [
        "FAULT_CONTROLLER", "FAULT_FENCE", "FAULT_MULTI", "FAULT_CABLE_CUTTING", "FAULT_ETC"
    ]
    enum_values = [member.name for member in EnumFaultType]

    for value in required_values:
        assert value in enum_values, f"{value} should be in EnumFaultType"


def test_enum_true_false_exists():
    """Test that EnumTrueFalse exists"""
    from app.utils.enums import EnumTrueFalse

    assert issubclass(EnumTrueFalse, Enum), "EnumTrueFalse should be an Enum"

    # Test enum members (using False_ and True_ due to Python keywords)
    required_values = ["False_", "True_"]
    enum_values = [member.name for member in EnumTrueFalse]

    for value in required_values:
        assert value in enum_values, f"{value} should be in EnumTrueFalse"

    # Test that "False" and "True" string values work via _missing_
    assert EnumTrueFalse("False") == EnumTrueFalse.False_, "Should support 'False' string via _missing_"
    assert EnumTrueFalse("True") == EnumTrueFalse.True_, "Should support 'True' string via _missing_"
