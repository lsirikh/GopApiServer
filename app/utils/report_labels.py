"""보고서용 Enum → 한글 라벨 매핑 (중앙 집중).

PRD: PRD_Report_Master_Redesign (정형/비정형 통합 보고서 디자인 재설계)
보고서 생성기·프리뷰가 공통으로 사용한다. 매핑에 없는 값은 원본을 그대로 반환한다.
"""
from __future__ import annotations

# 탐지 유형 (EnumDetectionType)
DETECTION: dict[str, str] = {
    "THERMAL_SENSOR": "열선 감지", "VIBRATION_SENSOR": "진동 감지", "DISTANCE_SENSOR": "거리 감지",
    "PIR_SENSOR": "PIR 감지", "CONTACT_SENSOR": "접점 감지", "CABLE_CUTTING": "케이블 절단",
    "CABLE_CONNECTED": "케이블 연결", "AI_DETECT": "AI 감지", "NONE": "미분류",
}

# 장애 유형 (EnumFaultType)
FAULT: dict[str, str] = {
    "FAULT_CONTROLLER": "제어기 장애", "FAULT_FENCE": "펜스 장애", "FAULT_MULTI": "복합 장애",
    "FAULT_CABLE_CUTTING": "케이블 절단", "FAULT_ETC": "기타 장애", "NONE": "미분류",
}

# 장비 카테고리 (EnumDeviceCategory)
DEVICE_CATEGORY: dict[str, str] = {
    "CONTROLLER": "제어기", "SENSOR": "센서", "CAMERA": "카메라",
    "SPEAKER": "스피커", "ENCLOSURE": "함체", "LAMP": "경광등",
}

# 장비/서버 상태 (EnumDeviceStatus + 서버 상태)
STATUS: dict[str, str] = {
    "ACTIVATED": "정상", "DEACTIVATED": "비활성", "ERROR": "오류",
    "NORMAL": "정상", "WARNING": "경고",
}

# 시스템 이벤트 심각도
SEVERITY: dict[str, str] = {"INFO": "정보", "WARNING": "경고", "ERROR": "오류", "CRITICAL": "심각"}

# 사용자 역할
ROLE: dict[str, str] = {"ADMIN": "관리자", "MAINTAINER": "유지보수", "OPERATOR": "운영자", "VIEWER": "뷰어"}

# 로그인/감사 결과
RESULT: dict[str, str] = {"SUCCESS": "성공", "FAILURE": "실패"}

# 시스템 이벤트 유형 (EnumSystemEventType)
SYSTEM_EVENT: dict[str, str] = {
    "CONNECTION_LOST": "연결 끊김", "BACKUP_COMPLETED": "백업 완료", "SECURITY_ALERT": "보안 경보",
    "SYSTEM_UPDATE": "시스템 업데이트", "RESOURCE_THRESHOLD": "자원 임계 초과", "SERVICE_STOPPED": "서비스 중지",
    "SERVICE_STARTED": "서비스 시작", "CONNECTION_RESTORED": "연결 복구", "SERVER_CONNECTED": "서버 연결",
    "SERVER_DISCONNECTED": "서버 연결 끊김", "SERVER_ERROR": "서버 오류", "DEVICE_CONNECTED": "장비 연결",
    "BACKUP_STARTED": "백업 시작", "SERVICE_ERROR": "서비스 오류",
}

# 설정 변경 리소스 유형 (EnumConfigResourceType)
CONFIG_RESOURCE: dict[str, str] = {
    "MALFUNCTION_EVENT": "장애 이벤트", "LAMP": "경광등", "EVENT_MAPPING": "이벤트 매핑", "SENSOR": "센서",
    "DETECTION_EVENT": "탐지 이벤트", "DEVICE_GROUP": "장비 그룹", "CONTROLLER": "제어기",
    "ACTION_EVENT": "조치 이벤트", "CAMERA": "카메라", "ENCLOSURE": "함체", "SPEAKER": "스피커",
    "CONNECTION_EVENT": "연결 이벤트",
}

# 설정 변경 액션 (EnumConfigActionType)
CONFIG_ACTION: dict[str, str] = {
    "ASSIGNED": "할당", "CREATED": "생성", "UNASSIGNED": "할당 해제", "UPDATED": "수정", "DELETED": "삭제",
}

# 감사 로그 액션 유형
AUDIT_ACTION: dict[str, str] = {
    "SESSION_TERMINATED": "세션 종료", "SESSION_FORCED_LOGOUT": "강제 로그아웃", "PASSWORD_RESET": "비밀번호 초기화",
    "ROLE_CHANGED": "역할 변경", "GROUP_ASSIGNED": "그룹 할당", "USER_DELETED": "사용자 삭제", "USER_LOCKED": "계정 잠금",
    "USER_UNLOCKED": "계정 잠금 해제", "GROUP_DELETED": "그룹 삭제", "USER_UPDATED": "사용자 수정",
    "SESSION_CREATED": "세션 생성", "USER_CREATED": "사용자 생성", "GROUP_CREATED": "그룹 생성",
    "PASSWORD_CHANGED": "비밀번호 변경", "PERMISSION_CHANGED": "권한 변경",
}

# 감사 로그 리소스 유형
AUDIT_RESOURCE: dict[str, str] = {
    "PASSWORD": "비밀번호", "USER_GROUP": "사용자 그룹", "USER": "사용자", "USER_SESSION": "세션",
}

# 로그인 이력 액션
LOGIN_ACTION: dict[str, str] = {
    "REFRESH": "토큰 갱신", "FORCE_LOGOUT": "강제 로그아웃", "LOGOUT": "로그아웃", "LOGIN": "로그인",
}

# 조치 이벤트 유형
ACTION_TYPE: dict[str, str] = {"Action": "조치", "ACTION": "조치"}


def label(mapping: dict[str, str], value) -> str:
    """Enum/문자열 값을 한글 라벨로 변환. value가 Enum이면 .value를 사용한다."""
    if value is None:
        return ""
    key = value.value if hasattr(value, "value") else str(value)
    return mapping.get(key, key)
