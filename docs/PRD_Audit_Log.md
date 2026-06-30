# PRD: 감사 로그 (Audit Log) 시스템 설계

**문서 버전**: v1.0
**작성일**: 2026-01-19
**상태**: Draft

---

## 1. 개요

### 1.1 목적

GOP 통합 관제 시스템의 Account 관련 사용자 활동을 추적하고 기록하는 감사 로그(Audit Log) 시스템을 설계한다. 이 시스템은 보안 감사, 문제 추적, 규정 준수를 위한 완전한 활동 이력을 제공한다.

### 1.2 범위

- **포함**: Account 시스템 관련 모든 CRUD 작업 추적
  - 사용자 계정 (AccountUser) 생성/수정/삭제/잠금/해제
  - 사용자 그룹 (UserGroup) 생성/수정/삭제
  - 세션 관리 (UserSession) 생성/강제종료
  - 비밀번호 변경/초기화
  - 권한 변경

- **제외**: 기존 시스템 이벤트(SystemEvent), API 로그(ApiLog), 로그인 로그(UserLoginLog)는 별도 유지

### 1.3 기존 로그 시스템과의 차이점

| 구분 | SystemEvent | ApiLog | UserLoginLog | **AuditLog (신규)** |
|------|-------------|--------|--------------|---------------------|
| 목적 | 서버/시스템 상태 | API 호출 이력 | 로그인/로그아웃 | **사용자 활동 감사** |
| 대상 | 서버, 서비스 | 모든 API 요청 | 인증 활동만 | **Account CRUD 작업** |
| 변경 내역 | X | Body만 저장 | X | **Before/After 저장** |
| 보존 정책 | 삭제 가능 | 삭제 가능 | 보존 | **영구 보존** |

---

## 2. 데이터 모델 설계

### 2.1 AuditLog 테이블

```sql
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,

    -- 행위 정보
    action_type VARCHAR(50) NOT NULL,           -- EnumAuditActionType
    action_status VARCHAR(20) NOT NULL DEFAULT 'SUCCESS', -- EnumAuditStatus

    -- 대상 리소스 정보
    resource_type VARCHAR(50) NOT NULL,         -- EnumAuditResourceType
    resource_id INTEGER,                        -- 대상 리소스 ID (삭제되어도 유지)
    resource_name VARCHAR(200),                 -- 대상 리소스 이름 (스냅샷)

    -- 행위자 정보
    actor_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    actor_login_id VARCHAR(50) NOT NULL,        -- 행위자 로그인 ID (스냅샷)
    actor_name VARCHAR(100),                    -- 행위자 이름 (스냅샷)
    actor_role VARCHAR(20),                     -- 행위자 역할 (스냅샷)

    -- 변경 상세
    changes JSONB,                              -- {before: {...}, after: {...}}
    description VARCHAR(500),                   -- 활동 설명

    -- 클라이언트 정보
    ip_address VARCHAR(45),                     -- IPv6 호환
    user_agent VARCHAR(500),

    -- 오류 정보 (실패 시)
    error_message VARCHAR(1000),

    -- 타임스탬프
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for query performance
CREATE INDEX idx_audit_logs_action_type ON audit_logs(action_type);
CREATE INDEX idx_audit_logs_resource_type ON audit_logs(resource_type);
CREATE INDEX idx_audit_logs_resource_id ON audit_logs(resource_id);
CREATE INDEX idx_audit_logs_actor_id ON audit_logs(actor_id);
CREATE INDEX idx_audit_logs_actor_login_id ON audit_logs(actor_login_id);
CREATE INDEX idx_audit_logs_action_status ON audit_logs(action_status);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
```

### 2.2 Enum 정의

#### 2.2.1 EnumAuditActionType (감사 행위 유형 - 18종)

```python
class EnumAuditActionType(str, Enum):
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
    PERMISSION_CHANGED = "PERMISSION_CHANGED" # 권한 변경

    # 세션 관리 (3종)
    SESSION_CREATED = "SESSION_CREATED"     # 세션 생성 (로그인)
    SESSION_TERMINATED = "SESSION_TERMINATED" # 세션 종료 (로그아웃)
    SESSION_FORCED_LOGOUT = "SESSION_FORCED_LOGOUT" # 강제 로그아웃
```

#### 2.2.2 EnumAuditResourceType (감사 대상 리소스 유형 - 4종)

```python
class EnumAuditResourceType(str, Enum):
    USER = "USER"               # 사용자 (AccountUser)
    USER_GROUP = "USER_GROUP"   # 사용자 그룹 (UserGroup)
    USER_SESSION = "USER_SESSION" # 사용자 세션 (UserSession)
    PASSWORD = "PASSWORD"       # 비밀번호
```

#### 2.2.3 EnumAuditStatus (감사 결과 상태 - 2종)

```python
class EnumAuditStatus(str, Enum):
    SUCCESS = "SUCCESS"   # 성공
    FAILURE = "FAILURE"   # 실패
```

### 2.3 SQLAlchemy 모델

**파일**: `app/models/audit_log.py`

```python
"""
Audit Log model for tracking user activities
"""
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base
from app.config import settings
from app.utils.enums import EnumAuditActionType, EnumAuditResourceType, EnumAuditStatus


class AuditLog(Base):
    """
    감사 로그 모델

    사용자의 Account 관련 CRUD 작업을 추적하고 기록합니다.
    삭제된 리소스에 대한 참조도 스냅샷으로 보존됩니다.
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    # 행위 정보
    action_type = Column(String(50), nullable=False, index=True)
    action_status = Column(String(20), nullable=False, default="SUCCESS", index=True)

    # 대상 리소스 정보 (스냅샷 - 삭제 후에도 유지)
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(Integer, index=True)
    resource_name = Column(String(200))

    # 행위자 정보 (스냅샷 - 삭제 후에도 유지)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True)
    actor_login_id = Column(String(50), nullable=False, index=True)
    actor_name = Column(String(100))
    actor_role = Column(String(20))

    # 변경 상세
    changes = Column(JSONB)  # {before: {...}, after: {...}}
    description = Column(String(500))

    # 클라이언트 정보
    ip_address = Column(String(45))
    user_agent = Column(String(500))

    # 오류 정보
    error_message = Column(String(1000))

    # 타임스탬프
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(settings.tz),
        nullable=False,
        index=True
    )

    # Relationships
    actor = relationship("AccountUser", foreign_keys=[actor_id])

    def __repr__(self):
        return f"<AuditLog {self.id}: {self.action_type} by {self.actor_login_id}>"
```

---

## 3. Pydantic 스키마 설계

**파일**: `app/schemas/audit_log.py`

```python
"""
Audit Log Pydantic schemas
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime


# ============================================================
# Request Schemas
# ============================================================

class AuditLogCreate(BaseModel):
    """감사 로그 생성 스키마 (내부 사용)"""
    action_type: str = Field(
        ...,
        description="행위 유형 (EnumAuditActionType)",
        json_schema_extra={"example": "USER_CREATED"}
    )
    action_status: str = Field(
        default="SUCCESS",
        description="행위 결과 (SUCCESS, FAILURE)",
        json_schema_extra={"example": "SUCCESS"}
    )
    resource_type: str = Field(
        ...,
        description="대상 리소스 유형 (EnumAuditResourceType)",
        json_schema_extra={"example": "USER"}
    )
    resource_id: Optional[int] = Field(
        None,
        description="대상 리소스 ID",
        json_schema_extra={"example": 1}
    )
    resource_name: Optional[str] = Field(
        None,
        description="대상 리소스 이름 (스냅샷)",
        json_schema_extra={"example": "홍길동 (operator01)"}
    )
    actor_id: Optional[int] = Field(
        None,
        description="행위자 ID",
        json_schema_extra={"example": 1}
    )
    actor_login_id: str = Field(
        ...,
        description="행위자 로그인 ID (스냅샷)",
        json_schema_extra={"example": "admin"}
    )
    actor_name: Optional[str] = Field(
        None,
        description="행위자 이름 (스냅샷)",
        json_schema_extra={"example": "관리자"}
    )
    actor_role: Optional[str] = Field(
        None,
        description="행위자 역할 (스냅샷)",
        json_schema_extra={"example": "ADMIN"}
    )
    changes: Optional[Dict[str, Any]] = Field(
        None,
        description="변경 내역 {before: {...}, after: {...}}",
        json_schema_extra={"example": {
            "before": {"role": "VIEWER"},
            "after": {"role": "OPERATOR"}
        }}
    )
    description: Optional[str] = Field(
        None,
        description="활동 설명",
        json_schema_extra={"example": "사용자 역할 변경: VIEWER → OPERATOR"}
    )
    ip_address: Optional[str] = Field(
        None,
        description="클라이언트 IP 주소",
        json_schema_extra={"example": "192.168.1.100"}
    )
    user_agent: Optional[str] = Field(
        None,
        description="클라이언트 User-Agent"
    )
    error_message: Optional[str] = Field(
        None,
        description="오류 메시지 (실패 시)"
    )


# ============================================================
# Response Schemas
# ============================================================

class AuditLogResponse(BaseModel):
    """감사 로그 응답 스키마"""
    id: int = Field(..., description="로그 ID", json_schema_extra={"example": 1})

    # 행위 정보
    action_type: str = Field(..., description="행위 유형", json_schema_extra={"example": "USER_CREATED"})
    action_status: str = Field(..., description="행위 결과", json_schema_extra={"example": "SUCCESS"})

    # 대상 리소스 정보
    resource_type: str = Field(..., description="대상 리소스 유형", json_schema_extra={"example": "USER"})
    resource_id: Optional[int] = Field(None, description="대상 리소스 ID", json_schema_extra={"example": 5})
    resource_name: Optional[str] = Field(None, description="대상 리소스 이름", json_schema_extra={"example": "홍길동 (operator01)"})

    # 행위자 정보
    actor_id: Optional[int] = Field(None, description="행위자 ID", json_schema_extra={"example": 1})
    actor_login_id: str = Field(..., description="행위자 로그인 ID", json_schema_extra={"example": "admin"})
    actor_name: Optional[str] = Field(None, description="행위자 이름", json_schema_extra={"example": "관리자"})
    actor_role: Optional[str] = Field(None, description="행위자 역할", json_schema_extra={"example": "ADMIN"})

    # 변경 상세
    changes: Optional[Dict[str, Any]] = Field(None, description="변경 내역")
    description: Optional[str] = Field(None, description="활동 설명")

    # 클라이언트 정보
    ip_address: Optional[str] = Field(None, description="IP 주소", json_schema_extra={"example": "192.168.1.100"})
    user_agent: Optional[str] = Field(None, description="User-Agent")

    # 오류 정보
    error_message: Optional[str] = Field(None, description="오류 메시지")

    # 타임스탬프
    created_at: datetime = Field(..., description="생성 시간", json_schema_extra={"example": "2026-01-19T10:30:00+09:00"})

    model_config = ConfigDict(from_attributes=True)
```

---

## 4. API 엔드포인트 설계

### 4.1 Endpoint 목록

| Method | Endpoint | 설명 | 권한 |
|--------|----------|------|------|
| GET | `/api/audit-logs` | 감사 로그 목록 조회 | ADMIN, MAINTAINER |
| GET | `/api/audit-logs/{log_id}` | 감사 로그 상세 조회 | ADMIN, MAINTAINER |

> **참고**: 감사 로그는 보안 목적으로 **생성/수정/삭제 API를 제공하지 않음**. 시스템 내부에서만 자동 생성됨.

### 4.2 GET `/api/audit-logs`

**설명**: 감사 로그 목록 조회 (필터링, 페이지네이션)

**Query Parameters**:

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| page | int | 아니오 | 페이지 번호 (기본값: 1) |
| limit | int | 아니오 | 페이지당 항목 수 (기본값: 20, 최대: 100) |
| action_type | string | 아니오 | 행위 유형 필터 (EnumAuditActionType) |
| resource_type | string | 아니오 | 리소스 유형 필터 (EnumAuditResourceType) |
| resource_id | int | 아니오 | 리소스 ID 필터 |
| actor_login_id | string | 아니오 | 행위자 로그인 ID 필터 |
| action_status | string | 아니오 | 결과 상태 필터 (SUCCESS, FAILURE) |
| start_date | datetime | 아니오 | 시작 일시 |
| end_date | datetime | 아니오 | 종료 일시 |

**Response (200 OK)**:
```json
{
  "success": true,
  "data": [
    {
      "id": 100,
      "action_type": "USER_CREATED",
      "action_status": "SUCCESS",
      "resource_type": "USER",
      "resource_id": 5,
      "resource_name": "홍길동 (operator01)",
      "actor_id": 1,
      "actor_login_id": "admin",
      "actor_name": "관리자",
      "actor_role": "ADMIN",
      "changes": {
        "after": {
          "login_id": "operator01",
          "name": "홍길동",
          "role": "OPERATOR"
        }
      },
      "description": "사용자 생성: operator01",
      "ip_address": "192.168.1.100",
      "created_at": "2026-01-19T10:30:00+09:00"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 1250,
    "total_pages": 63
  }
}
```

### 4.3 GET `/api/audit-logs/{log_id}`

**설명**: 감사 로그 단건 상세 조회

**Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "id": 100,
    "action_type": "ROLE_CHANGED",
    "action_status": "SUCCESS",
    "resource_type": "USER",
    "resource_id": 5,
    "resource_name": "홍길동 (operator01)",
    "actor_id": 1,
    "actor_login_id": "admin",
    "actor_name": "관리자",
    "actor_role": "ADMIN",
    "changes": {
      "before": {"role": "VIEWER"},
      "after": {"role": "OPERATOR"}
    },
    "description": "역할 변경: VIEWER → OPERATOR",
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "created_at": "2026-01-19T10:30:00+09:00"
  }
}
```

---

## 5. 자동 감사 로그 생성 규칙

### 5.1 감사 대상 작업

| API Endpoint | Action Type | Resource Type | 변경 내역 기록 |
|--------------|-------------|---------------|----------------|
| POST `/api/users` | USER_CREATED | USER | after만 기록 |
| PATCH `/api/users/{id}` | USER_UPDATED | USER | before/after 기록 |
| PUT `/api/users/{id}` | USER_UPDATED | USER | before/after 기록 |
| DELETE `/api/users/{id}` | USER_DELETED | USER | before만 기록 |
| POST `/api/users/{id}/lock` | USER_LOCKED | USER | reason 기록 |
| POST `/api/users/{id}/unlock` | USER_UNLOCKED | USER | - |
| PUT `/api/users/me/password` | PASSWORD_CHANGED | PASSWORD | - (비밀번호 미기록) |
| POST `/api/users/{id}/reset-password` | PASSWORD_RESET | PASSWORD | - (비밀번호 미기록) |
| POST `/api/user-groups` | GROUP_CREATED | USER_GROUP | after만 기록 |
| PATCH `/api/user-groups/{id}` | GROUP_UPDATED | USER_GROUP | before/after 기록 |
| DELETE `/api/user-groups/{id}` | GROUP_DELETED | USER_GROUP | before만 기록 |
| DELETE `/api/user-sessions/{id}` | SESSION_FORCED_LOGOUT | USER_SESSION | reason 기록 |

### 5.2 민감 정보 제외

다음 필드는 `changes`에 기록하지 않음:
- `password`, `password_hash` (비밀번호)
- `token`, `refresh_token` (토큰)
- `user_password` (서버 인증정보)

### 5.3 스냅샷 보존 정책

- `resource_name`: 대상 리소스가 삭제되어도 로그에서 식별 가능하도록 보존
- `actor_login_id`, `actor_name`, `actor_role`: 행위자가 삭제되어도 로그에서 식별 가능하도록 보존

---

## 6. 구현 체크리스트

### 6.1 코드 변경 (Phase 1: Model & Schema)

- [ ] **AC-AL-1**: `app/utils/enums.py`에 Enum 추가
  - [ ] EnumAuditActionType (18종)
  - [ ] EnumAuditResourceType (4종)
  - [ ] EnumAuditStatus (2종)

- [ ] **AC-AL-2**: `app/models/audit_log.py` 생성
  - [ ] AuditLog 모델 정의
  - [ ] 인덱스 정의

- [ ] **AC-AL-3**: `app/schemas/audit_log.py` 생성
  - [ ] AuditLogCreate 스키마
  - [ ] AuditLogResponse 스키마 (with examples)

### 6.2 코드 변경 (Phase 2: Router & Service)

- [ ] **AC-AL-4**: `app/routers/audit_logs.py` 생성
  - [ ] GET /api/audit-logs
  - [ ] GET /api/audit-logs/{log_id}

- [ ] **AC-AL-5**: `app/services/audit_service.py` 생성
  - [ ] `log_action()` 유틸리티 함수
  - [ ] `get_changes()` 변경 내역 추출 함수
  - [ ] `sanitize_changes()` 민감정보 제거 함수

### 6.3 코드 변경 (Phase 3: Integration)

- [ ] **AC-AL-6**: `app/routers/users.py` 수정
  - [ ] 사용자 CRUD 작업에 감사 로그 호출 추가

- [ ] **AC-AL-7**: `app/routers/user_groups.py` 수정
  - [ ] 그룹 CRUD 작업에 감사 로그 호출 추가

- [ ] **AC-AL-8**: `app/routers/user_sessions.py` 수정
  - [ ] 세션 강제 종료에 감사 로그 호출 추가

- [ ] **AC-AL-9**: `app/main.py` 수정
  - [ ] audit_logs 라우터 등록
  - [ ] tags_metadata에 Audit Logs 태그 추가

### 6.4 테스트 코드

- [ ] **AC-AL-10**: `tests/test_audit_log.py` 생성
  - [ ] 모델 테스트
  - [ ] 스키마 테스트
  - [ ] API 엔드포인트 테스트
  - [ ] 자동 로깅 통합 테스트

### 6.5 문서 업데이트

- [ ] **AC-AL-11**: `docs/GOP_스키마_전체.md` 업데이트
  - [ ] 10장 Audit 섹션 추가
  - [ ] 10.1 audit_logs 테이블
  - [ ] Enum 섹션에 Audit Enum 추가 (9.17, 9.18, 9.19)

- [ ] **AC-AL-12**: `GOP_Restful_Api_연동설계.md` 업데이트
  - [ ] 4.6 Audit Enum 섹션 추가
  - [ ] 9.6 Audit Logs API 섹션 추가
  - [ ] 변경이력 v3.1 추가

---

## 7. 문서 업데이트 상세

### 7.1 GOP_스키마_전체.md 업데이트

#### 7.1.1 목차 추가

```markdown
10. [Audit 스키마](#10-audit-스키마)
   - 10.1 [audit_logs 테이블](#101-audit_logs-테이블)
```

#### 7.1.2 Enum 섹션 추가 (9.17 ~ 9.19)

```markdown
### 9.17 EnumAuditActionType (감사 행위 유형 - 18종)

| 값 | 설명 |
|----|------|
| USER_CREATED | 사용자 생성 |
| USER_UPDATED | 사용자 정보 수정 |
| USER_DELETED | 사용자 삭제 |
| USER_LOCKED | 계정 잠금 |
| USER_UNLOCKED | 계정 잠금 해제 |
| USER_ACTIVATED | 계정 활성화 |
| USER_DEACTIVATED | 계정 비활성화 |
| PASSWORD_CHANGED | 비밀번호 변경 (본인) |
| PASSWORD_RESET | 비밀번호 초기화 (관리자) |
| ROLE_CHANGED | 역할 변경 |
| GROUP_ASSIGNED | 그룹 할당 |
| GROUP_CREATED | 그룹 생성 |
| GROUP_UPDATED | 그룹 수정 |
| GROUP_DELETED | 그룹 삭제 |
| PERMISSION_CHANGED | 권한 변경 |
| SESSION_CREATED | 세션 생성 |
| SESSION_TERMINATED | 세션 종료 |
| SESSION_FORCED_LOGOUT | 강제 로그아웃 |

### 9.18 EnumAuditResourceType (감사 대상 유형 - 4종)

| 값 | 설명 |
|----|------|
| USER | 사용자 (AccountUser) |
| USER_GROUP | 사용자 그룹 (UserGroup) |
| USER_SESSION | 사용자 세션 (UserSession) |
| PASSWORD | 비밀번호 |

### 9.19 EnumAuditStatus (감사 결과 - 2종)

| 값 | 설명 |
|----|------|
| SUCCESS | 성공 |
| FAILURE | 실패 |
```

#### 7.1.3 audit_logs 테이블 섹션 (10.1)

```markdown
## 10. Audit 스키마

### 10.1 audit_logs 테이블

사용자 활동 감사 로그를 저장하는 테이블입니다.

#### PostgreSQL CREATE TABLE

[CREATE TABLE 문 - 2.1절 참조]

#### 필드 정의

| 필드명 | 타입 | NULL 허용 | 기본값 | 설명 |
|--------|------|-----------|--------|------|
| id | SERIAL | NO | AUTO | 고유 식별자 (PK) |
| action_type | VARCHAR(50) | NO | - | 행위 유형 (EnumAuditActionType) |
| action_status | VARCHAR(20) | NO | 'SUCCESS' | 결과 상태 (EnumAuditStatus) |
| resource_type | VARCHAR(50) | NO | - | 대상 리소스 유형 |
| resource_id | INTEGER | YES | NULL | 대상 리소스 ID |
| resource_name | VARCHAR(200) | YES | NULL | 대상 리소스 이름 (스냅샷) |
| actor_id | INTEGER | YES | NULL | FK → users.id (SET NULL) |
| actor_login_id | VARCHAR(50) | NO | - | 행위자 로그인 ID (스냅샷) |
| actor_name | VARCHAR(100) | YES | NULL | 행위자 이름 (스냅샷) |
| actor_role | VARCHAR(20) | YES | NULL | 행위자 역할 (스냅샷) |
| changes | JSONB | YES | NULL | 변경 내역 {before, after} |
| description | VARCHAR(500) | YES | NULL | 활동 설명 |
| ip_address | VARCHAR(45) | YES | NULL | 클라이언트 IP |
| user_agent | VARCHAR(500) | YES | NULL | User-Agent |
| error_message | VARCHAR(1000) | YES | NULL | 오류 메시지 |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 생성 시간 |
```

### 7.2 GOP_Restful_Api_연동설계.md 업데이트

#### 7.2.1 헤더 업데이트

```markdown
**최종 수정일**: 2026-01-19
**버전**: v3.1
```

#### 7.2.2 목차 추가

```markdown
   - 9.6 [Audit Logs API](#96-audit-logs-api) *(v3.1 신규)*
```

#### 7.2.3 Enum 섹션 추가 (4.6)

```markdown
### 4.6 Audit Enum (v3.1 신규)

> **v3.1 신규**: PRD_Audit_Log.md 참조
> 사용자 활동 감사 로그 관련 Enum

[EnumAuditActionType, EnumAuditResourceType, EnumAuditStatus 정의]
```

#### 7.2.4 API 섹션 추가 (9.6)

```markdown
### 9.6 Audit Logs API

#### 9.6.1 Endpoint 목록

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/audit-logs` | 감사 로그 목록 조회 |
| GET | `/api/audit-logs/{id}` | 감사 로그 상세 조회 |

[각 엔드포인트 상세 - 4절 참조]
```

#### 7.2.5 변경 이력 추가

```markdown
| v3.1 | 2026-01-19 | **Audit Log API 추가**<br><br>**[1. Audit Enum 추가 (4.6)]**<br>- **EnumAuditActionType (18종)**: USER_CREATED, USER_UPDATED, USER_DELETED 등<br>- **EnumAuditResourceType (4종)**: USER, USER_GROUP, USER_SESSION, PASSWORD<br>- **EnumAuditStatus (2종)**: SUCCESS, FAILURE<br><br>**[2. Audit Logs API 신규 (9.6)]**<br>- **GET /api/audit-logs**: 목록 조회 (필터링, 페이지네이션)<br>- **GET /api/audit-logs/{id}**: 상세 조회<br>- **자동 로깅**: Account CRUD 작업 시 자동 감사 로그 생성<br>- **변경 내역 추적**: before/after JSON 기록<br>- **스냅샷 보존**: 삭제된 리소스/행위자 정보 유지 |
```

---

## 8. 향후 확장 고려사항

### 8.1 로그 보존 정책

- 감사 로그는 법적 요구사항에 따라 최소 3년 보존 권장
- 자동 아카이브 기능 추가 고려

### 8.2 알림 연동

- 특정 행위(예: 다수 실패, 권한 변경) 시 알림 발송
- SystemEvent와 연계하여 CRITICAL 이벤트 생성

### 8.3 대시보드

- 실시간 감사 로그 모니터링 대시보드
- 이상 행위 탐지 시각화

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| v1.0 | 2026-01-19 | 초안 작성 |
