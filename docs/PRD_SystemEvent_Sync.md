# PRD: System Event 문서-코드 동기화

**문서 버전**: v1.2
**작성일**: 2026-01-20
**작성자**: AI Assistant
**상태**: Draft

---

## 1. 개요

### 1.1 목적

PRD_System_Event.md, GOP_Restful_Api_연동설계.md, 실제 코드(enums.py) 간의 **EnumSystemEventType** 불일치를 해결하고 일관성을 확보합니다.

### 1.2 System Event의 본래 정의

> **System Event = 시스템이 자동 감지하는 서버/디바이스 상태 변화 이벤트**

PRD_System_Event.md Section 1.1~1.2에 명시된 목적:
- GOP 시스템을 구성하는 **서버들의** 상태 변화, 리소스 현황, 시스템 알림 등을 로깅
- **Server(서버) 레벨**의 이벤트 (서버 상태 변화, 리소스 임계치 초과, 시스템 경고 등)
- Device Event와 독립적인 별도 스키마
- **자동 감지 이벤트만 포함** (사용자 CRUD 작업은 ConfigChangeLog에서 관리)

### 1.3 현황 분석

| 문서/코드 | 버전 | 타입 수 | 명명 규칙 |
|-----------|------|---------|-----------|
| PRD_System_Event.md | v1.2 | 17개 | UPPER_SNAKE_CASE |
| GOP_Restful_Api_연동설계.md | v2.9 | 14개 | lower_snake_case |
| app/utils/enums.py | - | 24개 | UPPER_SNAKE_CASE |

### 1.4 핵심 문제점

1. **명명 규칙 불일치**: GOP 문서만 lowercase 사용
2. **타입 수 불일치**: 문서별로 정의된 타입이 다름
3. **목적 외 타입 혼입**: 코드에 USER_* 이벤트 9개가 System Event에 포함됨 (본래 목적과 불일치)
4. **ConfigChangeLog와 중복**: DEVICE_ADDED, DEVICE_REMOVED 등 CRUD 관련 타입이 중복
5. **미구현 타입**: PRD에 정의되었으나 코드에 없는 타입 존재

---

## 2. 이벤트 분류 체계

### 2.1 System Event에 포함되어야 할 이벤트

**시스템이 자동 감지하는 이벤트만 포함** (사용자 CRUD 작업은 ConfigChangeLog에서 관리)

| 카테고리 | 이벤트 유형 | 설명 |
|----------|-------------|------|
| **리소스 모니터링** | RESOURCE_THRESHOLD | 리소스 임계치 초과 (CPU, RAM, Disk, Network) |
| **서버 상태** | SERVER_CONNECTED | 서버 연결됨 (자동 감지) |
| | SERVER_DISCONNECTED | 서버 연결 해제됨 (자동 감지) |
| | SERVER_ERROR | 서버 오류 발생 |
| | CONNECTION_LOST | 네트워크 연결 끊김 (자동 감지) |
| | CONNECTION_RESTORED | 네트워크 연결 복구 (자동 감지) |
| **서비스 상태** | SERVICE_STARTED | 서비스 시작됨 (자동 감지) |
| | SERVICE_STOPPED | 서비스 중지됨 (자동 감지) |
| | SERVICE_ERROR | 서비스 오류 발생 |
| **백업** | BACKUP_STARTED | 백업 시작됨 |
| | BACKUP_COMPLETED | 백업 완료됨 |
| | BACKUP_FAILED | 백업 실패함 |
| **보안** | SECURITY_ALERT | 보안 경고 (침입 시도, 비정상 접근 등) |
| **업데이트** | SYSTEM_UPDATE | 시스템/펌웨어 업데이트 |
| **디바이스 연결** | DEVICE_CONNECTED | 디바이스 연결됨 (물리적 자동 감지) |

**총 15개 타입**

### 2.2 ConfigChangeLog로 이동한 이벤트 (중복 제거)

| 이전 SystemEvent 타입 | ConfigChangeLog 타입 | 이동 사유 |
|----------------------|---------------------|----------|
| CONFIG_CHANGED | UPDATED | 사용자 API 호출로 설정 변경 시 |
| DEVICE_ADDED | CREATED | 사용자가 디바이스 등록 시 |
| DEVICE_REMOVED | DELETED | 사용자가 디바이스 삭제 시 |
| DEVICE_STATUS_CHANGED | STATUS_CHANGED | 사용자가 상태 수동 변경 시 |

> **원칙**: API 호출에 의한 변경 → ConfigChangeLog, 시스템 자동 감지 → SystemEvent

### 2.3 System Event에서 제외해야 할 이벤트 (User Activity Log로 이동)

**사용자 활동 관련 이벤트는 별도 테이블에서 관리**

| 현재 위치 | 이벤트 유형 | 적합한 위치 | 사유 |
|-----------|-------------|-------------|------|
| EnumSystemEventType | USER_LOGIN | UserLoginLog | 사용자 활동 |
| EnumSystemEventType | USER_LOGOUT | UserLoginLog | 사용자 활동 |
| EnumSystemEventType | USER_LOGIN_FAILED | UserLoginLog | 사용자 활동 |
| EnumSystemEventType | USER_LOCKED | AuditLog / UserLoginLog | 계정 관리 |
| EnumSystemEventType | USER_UNLOCKED | AuditLog / UserLoginLog | 계정 관리 |
| EnumSystemEventType | USER_CREATED | AuditLog | 관리자 작업 |
| EnumSystemEventType | USER_UPDATED | AuditLog | 관리자 작업 |
| EnumSystemEventType | USER_DELETED | AuditLog | 관리자 작업 |
| EnumSystemEventType | SESSION_FORCED_LOGOUT | UserLoginLog | 세션 관리 |

> **Note**: 이미 `user_login_logs` 테이블이 존재하며, 이 테이블에서 LOGIN, LOGOUT, LOGIN_FAILED 등을 기록하고 있음. 중복 방지를 위해 System Event에서 제외.

### 2.4 PRD에서 제거할 타입 (불명확/중복)

| 타입 | 제거 사유 | 대체 방안 |
|------|----------|----------|
| SERVER_STATUS_CHANGE | 불명확, 다른 타입과 중복 | SERVER_CONNECTED/DISCONNECTED/ERROR 사용 |
| SERVICE_START | 명명 불일치 (과거형 권장) | SERVICE_STARTED |
| SERVICE_STOP | 명명 불일치 | SERVICE_STOPPED |
| SERVICE_RESTART | 불필요 (STOPPED + STARTED 조합) | 두 이벤트로 분리 기록 |
| UPDATE_AVAILABLE | 알림용, 이벤트로 부적합 | detail JSONB에 기록 |
| UPDATE_INSTALLED | SYSTEM_UPDATE와 중복 | SYSTEM_UPDATE 사용 |
| SYSTEM_INFO | 불명확, severity=INFO로 대체 | severity 필드 활용 |
| SYSTEM_WARNING | 불명확, severity=WARNING으로 대체 | severity 필드 활용 |
| SYSTEM_ERROR | SERVER_ERROR/SERVICE_ERROR와 중복 | 구체적 타입 사용 |
| CUSTOM | 불명확, 확장성 부족 | detail JSONB로 확장 |
| CONFIG_CHANGED | ConfigChangeLog와 중복 | ConfigChangeLog.UPDATED 사용 |
| DEVICE_ADDED | ConfigChangeLog와 중복 | ConfigChangeLog.CREATED 사용 |
| DEVICE_REMOVED | ConfigChangeLog와 중복 | ConfigChangeLog.DELETED 사용 |
| DEVICE_STATUS_CHANGED | ConfigChangeLog와 중복 | ConfigChangeLog.STATUS_CHANGED 사용 |

---

## 3. 최종 EnumSystemEventType 정의 (15개)

### 3.1 통합 Enum 목록

```python
class EnumSystemEventType(str, Enum):
    """
    System Event type enumeration (15종)

    목적: 시스템이 자동 감지하는 서버/디바이스 상태 변화 이벤트 기록
    주의: 사용자 CRUD 작업은 ConfigChangeLog에서 관리

    PRD Reference: PRD_System_Event.md, PRD_SystemEvent_Sync.md, PRD_ConfigChangeLog.md
    """

    # ========================================
    # 리소스 모니터링 (1종)
    # ========================================
    RESOURCE_THRESHOLD = "RESOURCE_THRESHOLD"   # 리소스 임계치 초과 (CPU, RAM, Disk, Network)

    # ========================================
    # 서버 상태 (5종)
    # ========================================
    SERVER_CONNECTED = "SERVER_CONNECTED"       # 서버 연결됨 (자동 감지)
    SERVER_DISCONNECTED = "SERVER_DISCONNECTED" # 서버 연결 해제됨 (자동 감지)
    SERVER_ERROR = "SERVER_ERROR"               # 서버 오류 발생
    CONNECTION_LOST = "CONNECTION_LOST"         # 네트워크 연결 끊김 (자동 감지)
    CONNECTION_RESTORED = "CONNECTION_RESTORED" # 네트워크 연결 복구 (자동 감지)

    # ========================================
    # 서비스 상태 (3종)
    # ========================================
    SERVICE_STARTED = "SERVICE_STARTED"         # 서비스 시작됨 (자동 감지)
    SERVICE_STOPPED = "SERVICE_STOPPED"         # 서비스 중지됨 (자동 감지)
    SERVICE_ERROR = "SERVICE_ERROR"             # 서비스 오류 발생

    # ========================================
    # 백업 (3종)
    # ========================================
    BACKUP_STARTED = "BACKUP_STARTED"           # 백업 시작됨
    BACKUP_COMPLETED = "BACKUP_COMPLETED"       # 백업 완료됨
    BACKUP_FAILED = "BACKUP_FAILED"             # 백업 실패함

    # ========================================
    # 보안 및 업데이트 (2종)
    # ========================================
    SECURITY_ALERT = "SECURITY_ALERT"           # 보안 경고 (침입 시도, 비정상 접근 등)
    SYSTEM_UPDATE = "SYSTEM_UPDATE"             # 시스템/펌웨어 업데이트

    # ========================================
    # 디바이스 연결 (1종)
    # ========================================
    DEVICE_CONNECTED = "DEVICE_CONNECTED"       # 디바이스 연결됨 (물리적 자동 감지)
```

### 3.2 변경 요약

| 구분 | 이전 | 이후 | 변경 내용 |
|------|------|------|----------|
| PRD 정의 | 17개 | 15개 | 불명확 타입 제거, ConfigChangeLog 중복 4개 제거 |
| GOP 문서 | 14개 (lowercase) | 15개 (UPPERCASE) | 명명규칙 통일, ConfigChangeLog 분리 반영 |
| 코드 | 24개 | 15개 | USER_* 9개 제거, ConfigChangeLog 중복 4개 제거, DEVICE_CONNECTED 추가 |

### 3.3 SystemEvent vs ConfigChangeLog 역할 분리

| 구분 | SystemEvent (15개) | ConfigChangeLog |
|------|-------------------|-----------------|
| **트리거** | 시스템 자동 감지 | 사용자 API 호출 |
| **목적** | "무엇이 발생했나" (모니터링) | "누가 무엇을 변경했나" (감사) |
| **데이터** | 이벤트 발생 시점 상태 | before/after 상태, 변경자 정보 |
| **예시** | 서버 연결 끊김, 임계치 초과 | 디바이스 추가, 설정 변경 |

---

## 4. 변경 범위

### 4.1 영향 받는 파일

| 파일 | 변경 유형 | 우선순위 |
|------|----------|----------|
| app/utils/enums.py | **수정** - USER_* 제거, 누락 타입 추가 | HIGH |
| docs/PRD_System_Event.md | **업데이트** - Enum 섹션 재정의 | HIGH |
| GOP_Restful_Api_연동설계.md | **업데이트** - Section 8.7.1 수정 | HIGH |
| app/routers/auth.py | **검토** - USER_* 사용 부분 확인 | MEDIUM |
| tests/test_system_event.py | **업데이트** - 테스트 수정 | MEDIUM |

### 4.2 변경하지 않는 항목

- EnumSystemEventSeverity (4개 값 - INFO, WARNING, ERROR, CRITICAL)
- API Endpoints 구조
- threshold_config 구조
- user_login_logs 테이블 (이미 존재)

---

## 5. 구현 계획

### 5.1 Task Breakdown

| ID | Task | 파일 | 우선순위 |
|----|------|------|----------|
| SE-SYNC-1 | enums.py에서 USER_* 9개 타입 제거 | app/utils/enums.py | HIGH |
| SE-SYNC-2 | enums.py에 누락된 3개 타입 추가 | app/utils/enums.py | HIGH |
| SE-SYNC-3 | PRD_System_Event.md Enum 섹션 업데이트 | docs/PRD_System_Event.md | HIGH |
| SE-SYNC-4 | GOP 문서 Section 8.7.1 업데이트 | GOP_Restful_Api_연동설계.md | HIGH |
| SE-SYNC-5 | USER_* 사용 코드 검토 및 수정 | app/routers/*.py | MEDIUM |
| SE-SYNC-6 | 테스트 코드 업데이트 | tests/test_system_event.py | MEDIUM |

### 5.2 SE-SYNC-1: enums.py에서 제거할 타입

```python
# 제거할 타입 (9개) - User Activity Log로 이동
USER_LOGIN = "USER_LOGIN"
USER_LOGOUT = "USER_LOGOUT"
USER_LOGIN_FAILED = "USER_LOGIN_FAILED"
USER_LOCKED = "USER_LOCKED"
USER_UNLOCKED = "USER_UNLOCKED"
USER_CREATED = "USER_CREATED"
USER_UPDATED = "USER_UPDATED"
USER_DELETED = "USER_DELETED"
SESSION_FORCED_LOGOUT = "SESSION_FORCED_LOGOUT"

# 제거할 타입 (4개) - ConfigChangeLog로 이동
CONFIG_CHANGED = "CONFIG_CHANGED"
DEVICE_ADDED = "DEVICE_ADDED"
DEVICE_REMOVED = "DEVICE_REMOVED"
DEVICE_STATUS_CHANGED = "DEVICE_STATUS_CHANGED"
```

### 5.3 SE-SYNC-2: enums.py에 추가할 타입

```python
# 추가/유지할 타입
CONNECTION_LOST = "CONNECTION_LOST"         # 네트워크 연결 끊김 (자동 감지)
CONNECTION_RESTORED = "CONNECTION_RESTORED" # 네트워크 연결 복구 (자동 감지)
SECURITY_ALERT = "SECURITY_ALERT"           # 보안 경고
DEVICE_CONNECTED = "DEVICE_CONNECTED"       # 디바이스 연결됨 (물리적 자동 감지)
```

### 5.4 SE-SYNC-5: USER_* 사용 코드 확인 필요

현재 USER_* 타입이 사용되는 곳을 확인하고, 해당 코드가 user_login_logs 테이블을 사용하도록 수정 필요.

**예상 영향 범위**:
- `app/routers/auth.py` - 로그인/로그아웃 시 이벤트 기록
- `app/routers/users.py` - 사용자 CRUD 시 이벤트 기록

**수정 방향**:
- SystemEvent 대신 UserLoginLog 또는 AuditLog 사용
- 기존 `user_login_logs` 테이블의 `action` 필드 활용

---

## 6. GOP 문서 업데이트 내용

### 6.1 Section 8.7.1 변경 내용

**Before** (lower_snake_case, 14개):
```markdown
| 값 | 설명 |
|----|------|
| server_start | 서버 시작 |
| threshold_warning | 임계치 경고 |
...
```

**After** (UPPER_SNAKE_CASE, 15개):
```markdown
**EnumSystemEventType** (이벤트 유형 - 15종):

시스템이 자동 감지하는 서버/디바이스 상태 변화 이벤트를 기록합니다.

| 카테고리 | 값 | 설명 |
|----------|-----|------|
| 리소스 | RESOURCE_THRESHOLD | 리소스 임계치 초과 |
| 서버 | SERVER_CONNECTED | 서버 연결됨 (자동 감지) |
| 서버 | SERVER_DISCONNECTED | 서버 연결 해제됨 (자동 감지) |
| 서버 | SERVER_ERROR | 서버 오류 |
| 서버 | CONNECTION_LOST | 네트워크 연결 끊김 (자동 감지) |
| 서버 | CONNECTION_RESTORED | 네트워크 연결 복구 (자동 감지) |
| 서비스 | SERVICE_STARTED | 서비스 시작됨 (자동 감지) |
| 서비스 | SERVICE_STOPPED | 서비스 중지됨 (자동 감지) |
| 서비스 | SERVICE_ERROR | 서비스 오류 |
| 백업 | BACKUP_STARTED | 백업 시작됨 |
| 백업 | BACKUP_COMPLETED | 백업 완료됨 |
| 백업 | BACKUP_FAILED | 백업 실패함 |
| 보안 | SECURITY_ALERT | 보안 경고 |
| 업데이트 | SYSTEM_UPDATE | 시스템 업데이트 |
| 디바이스 | DEVICE_CONNECTED | 디바이스 연결됨 (물리적 자동 감지) |

> **Note**:
> - 사용자 관련 이벤트(로그인, 로그아웃, 계정 관리)는 `user_login_logs` 테이블에서 관리합니다.
> - 사용자 CRUD 작업(디바이스 추가/삭제, 설정 변경 등)은 `config_change_logs` 테이블에서 관리합니다.
```

---

## 7. 테스트 케이스

### 7.1 Enum 동기화 테스트

```python
# tests/test_system_event.py에 추가

class TestEnumSystemEventTypeSync:
    """SE-SYNC: Enum 타입 동기화 검증"""

    def test_enum_has_15_types(self):
        """SE-SYNC: EnumSystemEventType이 15개 타입을 가짐"""
        from app.utils.enums import EnumSystemEventType
        assert len(EnumSystemEventType) == 15

    def test_enum_no_user_types(self):
        """SE-SYNC: USER_* 타입이 없음 (User Activity Log로 분리)"""
        from app.utils.enums import EnumSystemEventType

        user_types = [
            'USER_LOGIN', 'USER_LOGOUT', 'USER_LOGIN_FAILED',
            'USER_LOCKED', 'USER_UNLOCKED', 'USER_CREATED',
            'USER_UPDATED', 'USER_DELETED', 'SESSION_FORCED_LOGOUT'
        ]

        for user_type in user_types:
            assert not hasattr(EnumSystemEventType, user_type), \
                f"{user_type} should not be in EnumSystemEventType"

    def test_enum_no_configchangelog_overlap_types(self):
        """SE-SYNC: ConfigChangeLog 중복 타입이 없음"""
        from app.utils.enums import EnumSystemEventType

        # ConfigChangeLog로 이동된 타입들
        overlap_types = [
            'CONFIG_CHANGED', 'DEVICE_ADDED', 'DEVICE_REMOVED', 'DEVICE_STATUS_CHANGED'
        ]

        for overlap_type in overlap_types:
            assert not hasattr(EnumSystemEventType, overlap_type), \
                f"{overlap_type} should be in ConfigChangeLog, not SystemEvent"

    def test_enum_has_required_server_types(self):
        """SE-SYNC: 서버 관련 필수 타입 존재"""
        from app.utils.enums import EnumSystemEventType

        required_types = [
            'SERVER_CONNECTED', 'SERVER_DISCONNECTED', 'SERVER_ERROR',
            'CONNECTION_LOST', 'CONNECTION_RESTORED'
        ]

        for type_name in required_types:
            assert hasattr(EnumSystemEventType, type_name), \
                f"{type_name} should exist in EnumSystemEventType"

    def test_enum_has_device_connected_type(self):
        """SE-SYNC: 디바이스 자동 감지 타입 존재"""
        from app.utils.enums import EnumSystemEventType

        # 물리적 연결 자동 감지만 SystemEvent에 포함
        assert hasattr(EnumSystemEventType, 'DEVICE_CONNECTED')

    def test_enum_uses_upper_snake_case(self):
        """SE-SYNC: 모든 타입이 UPPER_SNAKE_CASE 사용"""
        from app.utils.enums import EnumSystemEventType

        for member in EnumSystemEventType:
            assert member.value == member.value.upper()
            assert member.name == member.value
```

---

## 8. 마이그레이션 고려사항

### 8.1 기존 데이터 처리

기존 `system_events` 테이블에 USER_* 타입의 레코드가 있는 경우:

```sql
-- 옵션 1: 기존 USER_* 이벤트는 그대로 유지 (읽기 전용)
-- 새 이벤트만 18개 타입으로 제한

-- 옵션 2: USER_* 이벤트를 user_login_logs로 마이그레이션 (권장하지 않음)
-- 데이터 손실 위험, 구조 차이
```

**권장**: 기존 데이터는 유지하고, 새 이벤트 생성 시에만 15개 타입으로 제한

### 8.2 하위 호환성

1. **API 입력 검증**: 새 이벤트 생성 시 15개 타입만 허용
2. **API 응답**: 기존 데이터 조회 시 USER_* 타입 및 ConfigChangeLog 중복 타입도 반환 (레거시 지원)
3. **문서화**: deprecated 타입 명시

---

## 9. 검증 체크리스트

### 9.1 코드 변경 완료 후 확인

- [ ] `EnumSystemEventType`이 15개 타입을 포함
- [ ] USER_* 9개 타입이 제거됨
- [ ] ConfigChangeLog 중복 4개 타입이 제거됨 (CONFIG_CHANGED, DEVICE_ADDED, DEVICE_REMOVED, DEVICE_STATUS_CHANGED)
- [ ] DEVICE_CONNECTED 타입 추가됨 (물리적 자동 감지)
- [ ] 모든 타입이 UPPER_SNAKE_CASE
- [ ] 기존 테스트 통과
- [ ] 신규 동기화 테스트 통과

### 9.2 문서 변경 완료 후 확인

- [ ] PRD_System_Event.md Section 3.1.1 업데이트됨
- [ ] GOP_Restful_Api_연동설계.md Section 8.7.1 업데이트됨
- [ ] 두 문서의 Enum 목록이 코드와 일치
- [ ] User Activity Log 분리 내용 명시됨

---

## 10. 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| v1.0 | 2026-01-20 | 초안 작성 - 문서-코드 동기화 계획 수립 |
| v1.1 | 2026-01-20 | **System Event 목적 재정의**<br>• USER_* 이벤트 9개를 User Activity Log로 분리<br>• 최종 타입 27개 → 18개로 축소<br>• 서버/디바이스 관련 이벤트만 포함하도록 정리 |
| v1.2 | 2026-01-20 | **ConfigChangeLog와 중복 제거**<br>• 18개 → 15개로 축소<br>• ConfigChangeLog 중복 4개 타입 제거 (CONFIG_CHANGED, DEVICE_ADDED, DEVICE_REMOVED, DEVICE_STATUS_CHANGED)<br>• DEVICE_CONNECTED 타입 추가 (물리적 자동 감지)<br>• SystemEvent = 자동 감지, ConfigChangeLog = 사용자 CRUD로 역할 분리 명확화 |

---

## 11. 참조 문서

- [PRD_System_Event.md](./PRD_System_Event.md) - System Event PRD (v1.2)
- [PRD_ConfigChangeLog.md](./PRD_ConfigChangeLog.md) - Config Change Log PRD (사용자 CRUD 작업 로깅)
- [GOP_Restful_Api_연동설계.md](../GOP_Restful_Api_연동설계.md) - API 연동 설계서 (v2.9)
- [PRD_Account_Design.md](./PRD_Account_Design.md) - Account 설계 PRD (User Activity Log 정의)

---

**문서 끝**
