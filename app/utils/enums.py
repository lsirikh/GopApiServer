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
    PRD: PRD_Lamp_Device.md v1.1 - LAMP added (v3.4)
    """
    CONTROLLER = "controller"
    SENSOR = "sensor"
    CAMERA = "camera"
    SPEAKER = "speaker"  # v2.5: Speaker Device
    ENCLOSURE = "enclosure"  # v2.6: Enclosure Device (함체관리장비)
    LAMP = "lamp"  # v3.4: Lamp Device (경광등)


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
    # v3.4: PRD_Lamp_Device.md
    Lamp = "Lamp"              # 경광등
    Enclosure = "Enclosure"    # 함체


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


# ============================================================
# Lamp Device Enums (PRD: PRD_Lamp_Device.md v1.1)
# ============================================================

class EnumLampColor(str, Enum):
    """
    Lamp color enumeration (5종)
    PRD: PRD_Lamp_Device.md Section 2.3

    경광등 색상
    """
    RED = "Red"         # 빨간색 (위험/침입)
    ORANGE = "Orange"   # 주황색 (경고)
    GREEN = "Green"     # 녹색 (정상/안전)
    BLUE = "Blue"       # 파란색 (정보)
    WHITE = "White"     # 흰색 (일반)


class EnumBuzzerSound(str, Enum):
    """
    Buzzer sound pattern enumeration (5종)
    PRD: PRD_Lamp_Device.md Section 2.4

    부저 소리 패턴
    """
    FIRE_AWANG = "Fire A-WANG"    # 화재 경보음
    EMERGENCY = "Emergency"        # 비상 경보음
    AMBULANCE = "Ambulance"        # 구급차 사이렌
    PI_PI_PI = "PI-PI-PI"          # 단속음 (기본값)
    PI_CONTINUE = "PI_continue"    # 연속음


class EnumLightMode(str, Enum):
    """
    Lamp light mode enumeration (2종)
    PRD: PRD_Lamp_Device.md Section 2.5

    점등 모드
    """
    STEADY = "steady"       # 계속 점등 (기본값)
    BLINKING = "blinking"   # 점멸


class EnumSystemEventType(str, Enum):
    """
    System Event type enumeration (15종)
    PRD: PRD_System_Event.md Section 3.1
    PRD: PRD_SystemEvent_Sync.md v1.2

    시스템 레벨 이벤트 유형을 정의합니다.
    디바이스/센서 이벤트(Event 테이블)와 별개의 시스템 운영 이벤트입니다.

    Note: USER_* 9종은 UserLoginLog로, ConfigChangeLog 중복 4종은 제거됨
    - USER_* → UserLoginLog (PRD_Account_Design.md Section 9.2)
    - CONFIG_CHANGED, DEVICE_ADDED, DEVICE_REMOVED, DEVICE_STATUS_CHANGED → ConfigChangeLog
    """
    # 리소스 관련 (1종)
    RESOURCE_THRESHOLD = "RESOURCE_THRESHOLD"   # 리소스 임계치 초과

    # 서버 상태 (3종)
    SERVER_CONNECTED = "SERVER_CONNECTED"       # 서버 연결됨
    SERVER_DISCONNECTED = "SERVER_DISCONNECTED" # 서버 연결 해제됨
    SERVER_ERROR = "SERVER_ERROR"               # 서버 오류

    # 서비스 상태 (3종)
    SERVICE_STARTED = "SERVICE_STARTED"         # 서비스 시작됨
    SERVICE_STOPPED = "SERVICE_STOPPED"         # 서비스 중지됨
    SERVICE_ERROR = "SERVICE_ERROR"             # 서비스 오류

    # 연결 상태 (2종) - NEW
    CONNECTION_LOST = "CONNECTION_LOST"         # 연결 끊김
    CONNECTION_RESTORED = "CONNECTION_RESTORED" # 연결 복구됨

    # 보안 (1종) - NEW
    SECURITY_ALERT = "SECURITY_ALERT"           # 보안 경고

    # 디바이스 연결 (1종) - NEW
    DEVICE_CONNECTED = "DEVICE_CONNECTED"       # 디바이스 연결됨

    # 백업 관련 (3종)
    BACKUP_STARTED = "BACKUP_STARTED"           # 백업 시작됨
    BACKUP_COMPLETED = "BACKUP_COMPLETED"       # 백업 완료됨
    BACKUP_FAILED = "BACKUP_FAILED"             # 백업 실패함

    # 시스템 업데이트 (1종)
    SYSTEM_UPDATE = "SYSTEM_UPDATE"             # 시스템 업데이트


class EnumSystemEventSeverity(str, Enum):
    """
    System Event severity enumeration (4종)
    PRD: PRD_System_Event.md Section 3.2

    시스템 이벤트 심각도를 정의합니다.
    """
    INFO = "INFO"           # 정보 (일반 알림)
    WARNING = "WARNING"     # 경고 (주의 필요)
    ERROR = "ERROR"         # 오류 (조치 필요)
    CRITICAL = "CRITICAL"   # 심각 (즉시 조치 필요)


class EnumUserRole(str, Enum):
    """
    User role enumeration (5종)
    PRD: PRD_Account_Design.md Section 3.2

    사용자 등급 (권한 높은 순)
    """
    ADMIN = "ADMIN"               # 관리자 - 시스템 전체 관리
    MAINTAINER = "MAINTAINER"     # 유지보수자 - 장비/시스템 관리
    OPERATOR = "OPERATOR"         # 운영자 - 일반 운영
    VIEWER = "VIEWER"             # 조회자 - 조회 전용
    GUEST = "GUEST"               # 게스트 - 제한된 접근


class EnumLogoutReason(str, Enum):
    """
    Logout reason enumeration (6종)
    PRD: PRD_Account_Design.md Section 5.2

    로그아웃 사유
    """
    MANUAL = "MANUAL"                     # 사용자 직접 로그아웃
    EXPIRED = "EXPIRED"                   # 세션 만료
    FORCED = "FORCED"                     # 관리자 강제 로그아웃
    LOCKED = "LOCKED"                     # 계정 잠금으로 인한 로그아웃
    PASSWORD_CHANGED = "PASSWORD_CHANGED" # 비밀번호 변경
    DUPLICATE = "DUPLICATE"               # 중복 로그인으로 인한 기존 세션 종료


class EnumLoginAction(str, Enum):
    """
    Login action enumeration (3종)
    PRD: PRD_Account_Design.md Section 6.1

    로그인 로그 행위 유형
    """
    LOGIN = "LOGIN"     # 로그인 시도
    LOGOUT = "LOGOUT"   # 로그아웃
    REFRESH = "REFRESH" # 토큰 갱신


class EnumLoginResult(str, Enum):
    """
    Login result enumeration (2종)
    PRD: PRD_Account_Design.md Section 6.1

    로그인 결과
    """
    SUCCESS = "SUCCESS"   # 성공
    FAILURE = "FAILURE"   # 실패


class EnumLoginFailureReason(str, Enum):
    """
    Login failure reason enumeration (7종)
    PRD: PRD_Account_Design.md Section 6.2

    로그인 실패 사유
    """
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"   # 아이디/비밀번호 불일치
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"             # 계정 잠금
    ACCOUNT_INACTIVE = "ACCOUNT_INACTIVE"         # 비활성화 계정
    PASSWORD_EXPIRED = "PASSWORD_EXPIRED"         # 비밀번호 만료
    IP_BLOCKED = "IP_BLOCKED"                     # IP 차단
    TIME_RESTRICTED = "TIME_RESTRICTED"           # 접속 시간 제한
    MAX_SESSIONS = "MAX_SESSIONS"                 # 최대 세션 수 초과


# ============================================================
# Audit Log Enums (PRD: PRD_Audit_Log.md)
# ============================================================

class EnumAuditActionType(str, Enum):
    """
    Audit action type enumeration (18종)
    PRD: PRD_Audit_Log.md Section 2.2.1

    감사 로그 행위 유형
    """
    # 사용자 관리 (7종)
    USER_CREATED = "USER_CREATED"           # 사용자 생성
    USER_UPDATED = "USER_UPDATED"           # 사용자 정보 수정
    USER_DELETED = "USER_DELETED"           # 사용자 삭제
    USER_LOCKED = "USER_LOCKED"             # 계정 잠금
    USER_UNLOCKED = "USER_UNLOCKED"         # 계정 잠금 해제
    USER_ACTIVATED = "USER_ACTIVATED"       # 계정 활성화
    USER_DEACTIVATED = "USER_DEACTIVATED"   # 계정 비활성화

    # 비밀번호 관리 (2종)
    PASSWORD_CHANGED = "PASSWORD_CHANGED"   # 비밀번호 변경 (본인)
    PASSWORD_RESET = "PASSWORD_RESET"       # 비밀번호 초기화 (관리자)

    # 권한/역할 관리 (2종)
    ROLE_CHANGED = "ROLE_CHANGED"           # 역할 변경
    GROUP_ASSIGNED = "GROUP_ASSIGNED"       # 그룹 할당

    # 그룹 관리 (4종)
    GROUP_CREATED = "GROUP_CREATED"         # 그룹 생성
    GROUP_UPDATED = "GROUP_UPDATED"         # 그룹 수정
    GROUP_DELETED = "GROUP_DELETED"         # 그룹 삭제
    PERMISSION_CHANGED = "PERMISSION_CHANGED"  # 권한 변경

    # 세션 관리 (3종)
    SESSION_CREATED = "SESSION_CREATED"     # 세션 생성 (로그인)
    SESSION_TERMINATED = "SESSION_TERMINATED"  # 세션 종료 (로그아웃)
    SESSION_FORCED_LOGOUT = "SESSION_FORCED_LOGOUT"  # 강제 로그아웃


class EnumAuditResourceType(str, Enum):
    """
    Audit resource type enumeration (4종)
    PRD: PRD_Audit_Log.md Section 2.2.2

    감사 대상 리소스 유형
    """
    USER = "USER"                   # 사용자 (AccountUser)
    USER_GROUP = "USER_GROUP"       # 사용자 그룹 (UserGroup)
    USER_SESSION = "USER_SESSION"   # 사용자 세션 (UserSession)
    PASSWORD = "PASSWORD"           # 비밀번호


class EnumAuditStatus(str, Enum):
    """
    Audit status enumeration (2종)
    PRD: PRD_Audit_Log.md Section 2.2.3

    감사 결과 상태
    """
    SUCCESS = "SUCCESS"   # 성공
    FAILURE = "FAILURE"   # 실패


class EnumConfigResourceType(str, Enum):
    """
    Config change log resource type enumeration (19종)
    PRD: PRD_ConfigChangeLog.md v1.2 Section 2.1
    PRD: PRD_Lamp_Device.md v1.1 - LAMP, EVENT_MAPPING_LAMP added (v3.4)

    설정 변경 대상 리소스 유형

    카테고리별 분류:
    - Device 계열: 11개
    - Event 계열: 4개
    - Integration 계열: 4개

    Note: SERVER, SERVER_CATEGORY는 SystemEvent에서 관리
    """
    # Device 계열 (11개)
    CONTROLLER = "CONTROLLER"           # 컨트롤러
    SENSOR = "SENSOR"                   # 센서
    CAMERA = "CAMERA"                   # 카메라
    SPEAKER = "SPEAKER"                 # 스피커
    ENCLOSURE = "ENCLOSURE"             # 함체
    LAMP = "LAMP"                       # 경광등 (v3.4)
    DEVICE_GROUP = "DEVICE_GROUP"       # 디바이스 그룹
    CAMERA_PRESET = "CAMERA_PRESET"     # 카메라 프리셋
    ROI = "ROI"                         # ROI
    XY_POINT = "XY_POINT"               # XY 포인트
    FILE_GROUP = "FILE_GROUP"           # 파일 그룹

    # Event 계열 (4개)
    DETECTION_EVENT = "DETECTION_EVENT"       # 탐지 이벤트
    MALFUNCTION_EVENT = "MALFUNCTION_EVENT"   # 고장 이벤트
    CONNECTION_EVENT = "CONNECTION_EVENT"     # 연결 이벤트
    ACTION_EVENT = "ACTION_EVENT"             # 액션 이벤트

    # Integration 계열 (4개)
    EVENT_MAPPING = "EVENT_MAPPING"                   # 이벤트 매핑
    EVENT_MAPPING_CAMERA = "EVENT_MAPPING_CAMERA"     # 이벤트 매핑 카메라
    EVENT_MAPPING_SPEAKER = "EVENT_MAPPING_SPEAKER"   # 이벤트 매핑 스피커
    EVENT_MAPPING_LAMP = "EVENT_MAPPING_LAMP"         # 이벤트 매핑 경광등 (v3.4)


class EnumConfigActionType(str, Enum):
    """
    Config change log action type enumeration (6종)
    PRD: PRD_ConfigChangeLog.md Section 2.2

    설정 변경 액션 유형
    """
    # CRUD 액션 (3개)
    CREATED = "CREATED"             # 생성
    UPDATED = "UPDATED"             # 수정
    DELETED = "DELETED"             # 삭제

    # 특수 액션 (3개)
    STATUS_CHANGED = "STATUS_CHANGED"   # 상태 변경 (Enclosure status 등)
    ASSIGNED = "ASSIGNED"               # 할당 (DeviceGroup에 디바이스 할당)
    UNASSIGNED = "UNASSIGNED"           # 할당 해제 (DeviceGroup에서 디바이스 제거)


# ============================================================
# Report System Enums (PRD: PRD_Report_System.md Section 3)
# ============================================================

class EnumReportType(str, Enum):
    """
    Report type enumeration (2종)
    PRD: PRD_Report_System.md Section 3.1

    보고서 유형
    """
    STANDARD = "STANDARD"   # 정형 보고서
    CUSTOM = "CUSTOM"       # 비정형 보고서


class EnumReportPeriod(str, Enum):
    """
    Report period enumeration (4종)
    PRD: PRD_Report_System.md Section 3.1

    보고서 기간
    """
    DAYS_7 = "7d"           # 7일
    DAYS_30 = "30d"         # 30일 (1개월)
    DAYS_90 = "90d"         # 90일 (3개월)
    YEAR_1 = "1y"           # 1년


class EnumReportStatus(str, Enum):
    """
    Report status enumeration (4종)
    PRD: PRD_Report_System.md Section 3.1

    보고서 생성 상태
    """
    PENDING = "PENDING"         # 대기 중
    GENERATING = "GENERATING"   # 생성 중
    COMPLETED = "COMPLETED"     # 완료
    FAILED = "FAILED"           # 실패


class EnumChartType(str, Enum):
    """
    Chart type enumeration (4종)
    PRD: PRD_Report_System.md Section 3.1

    차트 유형
    """
    LINE = "LINE"       # 라인 차트
    BAR = "BAR"         # 막대 차트
    DONUT = "DONUT"     # 도넛 차트
    PIE = "PIE"         # 파이 차트


class EnumReportComponent(str, Enum):
    """
    Report component enumeration (21종)
    PRD: PRD_Report_System.md v1.4 Section 3.1

    보고서 컴포넌트
    """
    # SUMMARY (1종)
    SUMMARY_CARD = "SUMMARY_CARD"

    # DEVICE (3종)
    DEVICE_STATUS_PIE = "DEVICE_STATUS_PIE"
    DEVICE_TYPE_BAR = "DEVICE_TYPE_BAR"
    DEVICE_GRID = "DEVICE_GRID"

    # EVENT (6종)
    EVENT_SUMMARY_PIE = "EVENT_SUMMARY_PIE"
    EVENT_TREND_LINE = "EVENT_TREND_LINE"
    EVENT_DAILY_BAR = "EVENT_DAILY_BAR"
    EVENT_DETECTION_GRID = "EVENT_DETECTION_GRID"
    EVENT_MALFUNCTION_GRID = "EVENT_MALFUNCTION_GRID"
    EVENT_ACTION_GRID = "EVENT_ACTION_GRID"

    # SYSTEM (5종)
    SYSTEM_SEVERITY_BAR = "SYSTEM_SEVERITY_BAR"
    SYSTEM_TREND_LINE = "SYSTEM_TREND_LINE"
    SYSTEM_CONFIG_GRID = "SYSTEM_CONFIG_GRID"
    SYSTEM_EVENT_GRID = "SYSTEM_EVENT_GRID"
    SYSTEM_AUDIT_GRID = "SYSTEM_AUDIT_GRID"

    # USER (6종) - PRD v1.4
    USER_ROLE_PIE = "USER_ROLE_PIE"                     # 역할별 사용자 분포
    USER_LOGIN_TREND_LINE = "USER_LOGIN_TREND_LINE"     # 일별 로그인 추이
    USER_LOGIN_RESULT_PIE = "USER_LOGIN_RESULT_PIE"     # 로그인 성공/실패 분포
    USER_GRID = "USER_GRID"                             # 사용자 목록
    USER_LOGIN_GRID = "USER_LOGIN_GRID"                 # 로그인 이력
    USER_SESSION_GRID = "USER_SESSION_GRID"             # 세션 목록
