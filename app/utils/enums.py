"""
Enum definitions for GOP API
Based on Ironwall.Dotnet.Libraries.Enums
"""
from enum import Enum


class EnumDeviceType(str, Enum):
    """Device type enumeration"""
    NONE = "NONE"
    Controller = "Controller"
    Multi = "Multi"
    Fence = "Fence"
    Underground = "Underground"
    Contact = "Contact"
    PIR = "PIR"
    IoController = "IoController"
    Laser = "Laser"
    Cable = "Cable"
    IpCamera = "IpCamera"
    SmartSensor = "SmartSensor"
    SmartSensor2 = "SmartSensor2"
    SmartCompound = "SmartCompound"
    IpSpeaker = "IpSpeaker"
    Radar = "Radar"
    OpticalCable = "OpticalCable"
    Fence_Group = "Fence_Group"


class EnumDeviceStatus(str, Enum):
    """Device status enumeration"""
    ACTIVATED = "ACTIVATED"
    ERROR = "ERROR"
    DEACTIVATED = "DEACTIVATED"


class EnumCameraMode(str, Enum):
    """Camera mode enumeration"""
    NONE = "NONE"
    ONVIF = "ONVIF"
    EMSTONE_API = "EMSTONE_API"
    INNODEP_API = "INNODEP_API"
    ETC = "ETC"


class EnumCameraType(str, Enum):
    """Camera type enumeration"""
    NONE = "NONE"
    FIXED = "FIXED"
    PTZ = "PTZ"


class EnumEventType(str, Enum):
    """Event type enumeration"""
    None_ = "None"          # 0
    Intrusion = "Intrusion" # 90 (0x5A)
    ContactOn = "ContactOn" # 86 (0x56)
    ContactOff = "ContactOff" # 102 (0x66)
    Connection = "Connection" # 104 (0x68)
    Action = "Action"       # 192 (0xC0)
    Fault = "Fault"         # 115 (0x73)
    WindyMode = "WindyMode" # 118 (0x76)

    # Alias for API compatibility
    @classmethod
    def _missing_(cls, value):
        if value == "None":
            return cls.None_
        return None


class EnumDetectionType(str, Enum):
    """Detection type enumeration"""
    NONE = "NONE"                       # 0
    CABLE_CUTTING = "CABLE_CUTTING"     # 1
    CABLE_CONNECTED = "CABLE_CONNECTED" # 2
    PIR_SENSOR = "PIR_SENSOR"           # 3
    THERMAL_SENSOR = "THERMAL_SENSOR"   # 5
    VIBRATION_SENSOR = "VIBRATION_SENSOR" # 6
    CONTACT_SENSOR = "CONTACT_SENSOR"   # 10
    DISTANCE_SENSOR = "DISTANCE_SENSOR" # 11
    AI_DETECT = "AI_DETECT"             # 12


class EnumFaultType(str, Enum):
    """Fault type enumeration"""
    FAULT_CONTROLLER = "FAULT_CONTROLLER"
    FAULT_FENCE = "FAULT_FENCE"
    FAULT_MULTI = "FAULT_MULTI"
    FAULT_CABLE_CUTTING = "FAULT_CABLE_CUTTING"
    FAULT_ETC = "FAULT_ETC"


class EnumTrueFalse(str, Enum):
    """True/False enumeration"""
    False_ = "False"  # Using False_ to avoid conflict with Python keyword
    True_ = "True"    # Using True_ to avoid conflict with Python keyword

    # Aliases for API compatibility
    @classmethod
    def _missing_(cls, value):
        if value == "False":
            return cls.False_
        elif value == "True":
            return cls.True_
        return None


class EnumEventCategory(str, Enum):
    """Event category enumeration for CameraEventMapping (C# EnumEventCategory)"""
    NONE = "NONE"                                       # 미정의
    FENCE_SENSOR_ONLY = "FENCE_SENSOR_ONLY"             # 펜스센서 단독
    FENCE_SENSOR_WITH_MULTI_SENSOR = "FENCE_SENSOR_WITH_MULTI_SENSOR"  # 펜스센서와 멀티센서 And 조건
    MULTI_SENSOR_ONLY = "MULTI_SENSOR_ONLY"             # 멀티센서 단독
    SENSOR_WITH_CAMERA = "SENSOR_WITH_CAMERA"           # 센서와 카메라 적용
    SENSOR_WITH_AI_CAMERA = "SENSOR_WITH_AI_CAMERA"     # 센서와 AI 카메라 판단 적용
    AI_CAMERA_ONLY = "AI_CAMERA_ONLY"                   # AI 카메라 판단 단독
    CAMERA_ONLY = "CAMERA_ONLY"                         # 카메라 단독

    @classmethod
    def _missing_(cls, value):
        """Legacy value mapping for backward compatibility"""
        legacy_mapping = {
            "SENSOR_ONLY": cls.FENCE_SENSOR_ONLY,
            "SENSOR_WITH_AI_DETECT": cls.SENSOR_WITH_AI_CAMERA,
            "AI_DETECT_ONLY": cls.AI_CAMERA_ONLY,
        }
        return legacy_mapping.get(value)


# Backward compatibility alias
EnumCategoryEvent = EnumEventCategory
