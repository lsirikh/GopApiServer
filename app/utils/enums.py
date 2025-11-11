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
    FISHEYES = "FISHEYES"
    THERMAL = "THERMAL"


class EnumEventType(str, Enum):
    """Event type enumeration"""
    None_ = "None"  # Using None_ to avoid conflict with Python keyword
    Intrusion = "Intrusion"
    ContactOn = "ContactOn"
    ContactOff = "ContactOff"
    Connection = "Connection"
    Action = "Action"
    Fault = "Fault"
    WindyMode = "WindyMode"

    # Alias for API compatibility
    @classmethod
    def _missing_(cls, value):
        if value == "None":
            return cls.None_
        return None


class EnumDetectionType(str, Enum):
    """Detection type enumeration"""
    NONE = "NONE"
    CABLE_CUTTING = "CABLE_CUTTING"
    CABLE_CONNECTED = "CABLE_CONNECTED"
    PIR_SENSOR = "PIR_SENSOR"
    THERMAL_SENSOR = "THERMAL_SENSOR"
    VIBRATION_SENSOR = "VIBRATION_SENSOR"
    CONTACT_SENSOR = "CONTACT_SENSOR"
    DISTANCE_SENSOR = "DISTANCE_SENSOR"


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
