"""
Enum definitions for GOP API
Based on Ironwall.Dotnet.Libraries.Enums
"""
from enum import Enum


class EnumDeviceCategory(str, Enum):
    """
    Device category enumeration (Polymorphic Discriminator)

    Used for Joined Table Inheritance discriminator in Device model.
    PRD: PRD_Device_Inheritance_Structure_Refactoring.md Section 8.1
    PRD: PRD_Speaker_Device.md - SPEAKER added (v2.5)
    PRD: PRD_Enclosure_Device.md v1.1 - ENCLOSURE added (v2.6)
    """
    CONTROLLER = "controller"
    SENSOR = "sensor"
    CAMERA = "camera"
    SPEAKER = "speaker"  # v2.5: Speaker Device
    ENCLOSURE = "enclosure"  # v2.6: Enclosure Device (함체관리장비)


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
    """
    Event category enumeration for Event polymorphic discriminator.
    PRD: PRD_CategoryEvent_Refactoring.md Section 2.1.1

    Used for Event model's category_event field (detection, malfunction, connection).
    """
    DETECTION = "detection"       # 침입 탐지 이벤트
    MALFUNCTION = "malfunction"   # 장애 이벤트
    CONNECTION = "connection"     # 연결 이벤트


class EnumMappingEventCategory(str, Enum):
    """
    Mapping event category enumeration for EventMapping sensor combination type.
    PRD: PRD_CategoryEvent_Refactoring.md Section 2.1.2

    Used for EventMapping model's category_event_mapping field.
    (Renamed from EnumEventCategory to avoid confusion)
    """
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
EnumCategoryEvent = EnumMappingEventCategory


class EnumSpeakerType(str, Enum):
    """
    Speaker device type enumeration
    Based on EnumBcastDeviceType from NATS message spec
    PRD: PRD_Speaker_Device.md Section 3.2
    """
    NORMAL = "NORMAL"     # 일반 스피커 단말
    ADMIN = "ADMIN"       # 관리자 단말
    MONITOR = "MONITOR"   # 모니터링 단말
    DEV = "DEV"           # 음원/마이크 단말 (입력 장치)


class EnumServerType(str, Enum):
    """
    Server type enumeration (25종)
    Based on GOP_서버모니터링_스키마.md
    """
    # 영상/미디어 관련 (8종)
    VMS = "VMS"                     # VMS 서버
    NVR_API = "NVR_API"             # NVR API 서버
    STREAMING = "STREAMING"         # 스트리밍 서버
    TRANSCODER = "TRANSCODER"       # 트랜스코더 서버
    MEDIA = "MEDIA"                 # 미디어 서버
    RECORDING = "RECORDING"         # 녹화 서버
    PLAYBACK = "PLAYBACK"           # 재생 서버
    STORAGE = "STORAGE"             # 스토리지 서버

    # AI/분석 관련 (4종)
    AI_ANALYSIS = "AI_ANALYSIS"     # 지능형영상 분석 서버
    AI_TRAINING = "AI_TRAINING"     # AI 학습 서버
    AI_INFERENCE = "AI_INFERENCE"   # AI 추론 서버
    ANALYTICS = "ANALYTICS"         # 분석 서버

    # API 서버 관련 (4종)
    DB_API = "DB_API"               # DB API 서버
    SPEAKER_API = "SPEAKER_API"     # SPEAKER API 서버
    ENCLOSURE_API = "ENCLOSURE_API" # 함체관리 API 서버
    PIDS_API = "PIDS_API"           # PIDS API 서버

    # 인프라/네트워크 관련 (6종)
    WEB = "WEB"                     # 웹 서버
    AUTH = "AUTH"                   # 인증 서버
    PROXY = "PROXY"                 # 프록시 서버
    BROKER = "BROKER"               # 브로커 서버
    GATEWAY = "GATEWAY"             # 게이트웨이 서버
    PUSH = "PUSH"                   # 푸시 서버

    # 운영/관리 관련 (3종)
    LOG = "LOG"                     # 로그 서버
    BACKUP = "BACKUP"               # 백업 서버
    MONITORING = "MONITORING"       # 모니터링 서버

    # 기타 (1종)
    ETC = "ETC"                     # 기타 서버


class EnumServerStatus(str, Enum):
    """
    Server status enumeration (3종)
    Based on GOP_서버모니터링_스키마.md
    """
    NORMAL = "NORMAL"       # 정상 (녹색)
    WARNING = "WARNING"     # 경고 (노란색)
    ERROR = "ERROR"         # 오류 (빨간색)


class EnumDoorStatus(str, Enum):
    """
    Door status enumeration for Enclosure device
    PRD: PRD_Enclosure_Device.md v1.1 Section 3.1.1

    Physical door sensor state (separate from EnumDeviceStatus operational state).
    - CLOSED: 도어 닫힘 (정상 운영 상태)
    - OPEN: 도어 열림 (센서 감지)

    운영 로직:
    - status=ACTIVATED + door_status=OPEN → 비정상 개방 알람 발생
    - status=DEACTIVATED + door_status=OPEN → 점검 중이므로 알람 무시
    - status=ERROR → 함체 이상 상태
    """
    CLOSED = "CLOSED"  # 도어 닫힘
    OPEN = "OPEN"      # 도어 열림
