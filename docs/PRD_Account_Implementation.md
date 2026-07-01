# 사용자 계정 관리 시스템 구현 계획서

**문서 버전**: v1.1
**작성일**: 2026-01-19
**기준 문서**: PRD_Account_Design.md v1.1
**상태**: Draft

> **중요**: 사용자와 그룹은 1:1 관계입니다. 사용자는 하나의 그룹에만 소속될 수 있습니다.

---

## 1. 개요

### 1.1 목적

본 문서는 PRD_Account_Design.md에 정의된 사용자 계정 관리 시스템을 실제 구현하기 위한 상세 계획을 정의한다.

### 1.2 구현 범위

| 항목 | 설명 | 상태 |
|------|------|------|
| **코드 구현** | Models, Schemas, Routers, Services | 신규 |
| **데이터베이스** | 테이블 생성 및 마이그레이션 | 신규 |
| **API 문서화** | Swagger/OpenAPI, Docs, Redoc | 신규 |
| **스키마 문서** | GOP_스키마_전체.md 업데이트 | 업데이트 |
| **API 연동 문서** | GOP_Restful_Api_연동설계.md 업데이트 | 업데이트 |

### 1.3 참조 문서

- PRD_Account_Design.md (사용자 계정 관리 시스템 설계서)
- GOP_스키마_전체.md (v2.0)
- GOP_Restful_Api_연동설계.md (v2.9)

---

## 2. 코드 구현

### 2.1 디렉토리 구조

```
app/
├── models/
│   ├── __init__.py          # User, UserGroup 등 export 추가
│   ├── user.py              # User 모델 (신규)
│   ├── user_group.py        # UserGroup 모델 (신규)
│   ├── user_session.py      # UserSession 모델 (신규)
│   └── user_login_log.py    # UserLoginLog 모델 (신규)
├── schemas/
│   ├── __init__.py          # 스키마 export 추가
│   ├── user.py              # User 스키마 (신규)
│   ├── user_group.py        # UserGroup 스키마 (신규)
│   ├── user_session.py      # UserSession 스키마 (신규)
│   └── auth.py              # 인증 관련 스키마 (신규)
├── routers/
│   ├── __init__.py          # 라우터 등록
│   ├── users.py             # /api/users 라우터 (신규)
│   ├── user_groups.py       # /api/user-groups 라우터 (신규)
│   ├── user_sessions.py     # /api/user-sessions 라우터 (신규)
│   └── auth.py              # /api/auth 라우터 (신규)
├── services/
│   ├── auth_service.py      # 인증 서비스 (신규)
│   └── user_service.py      # 사용자 서비스 (신규)
└── utils/
    ├── enums.py             # EnumUserRole, EnumLogoutReason 등 추가
    ├── security.py          # 비밀번호 해싱, JWT 처리 (신규)
    └── dependencies.py      # 인증 dependency (신규)
```

### 2.2 Enum 추가 (app/utils/enums.py)

```python
class EnumUserRole(str, Enum):
    """사용자 등급 (권한 높은 순)"""
    ADMIN = "ADMIN"               # 관리자
    MAINTAINER = "MAINTAINER"     # 유지보수자
    OPERATOR = "OPERATOR"         # 운영자
    VIEWER = "VIEWER"             # 조회자
    GUEST = "GUEST"               # 게스트


class EnumLogoutReason(str, Enum):
    """로그아웃 사유"""
    MANUAL = "MANUAL"                     # 사용자 직접 로그아웃
    EXPIRED = "EXPIRED"                   # 세션 만료
    FORCED = "FORCED"                     # 관리자 강제 로그아웃
    LOCKED = "LOCKED"                     # 계정 잠금으로 인한 로그아웃
    PASSWORD_CHANGED = "PASSWORD_CHANGED" # 비밀번호 변경
    DUPLICATE = "DUPLICATE"               # 중복 로그인으로 인한 기존 세션 종료


class EnumLoginAction(str, Enum):
    """로그인 행위"""
    LOGIN = "LOGIN"       # 로그인
    LOGOUT = "LOGOUT"     # 로그아웃
    REFRESH = "REFRESH"   # 토큰 갱신


class EnumLoginResult(str, Enum):
    """로그인 결과"""
    SUCCESS = "SUCCESS"   # 성공
    FAILURE = "FAILURE"   # 실패


class EnumLoginFailureReason(str, Enum):
    """로그인 실패 사유"""
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"   # 아이디/비밀번호 불일치
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"             # 계정 잠금
    ACCOUNT_INACTIVE = "ACCOUNT_INACTIVE"         # 비활성화 계정
    PASSWORD_EXPIRED = "PASSWORD_EXPIRED"         # 비밀번호 만료
    IP_BLOCKED = "IP_BLOCKED"                     # IP 차단
    TIME_RESTRICTED = "TIME_RESTRICTED"           # 접속 시간 제한
    MAX_SESSIONS = "MAX_SESSIONS"                 # 최대 세션 수 초과


class EnumDeviceType(str, Enum):
    """디바이스 유형"""
    PC = "PC"
    MOBILE = "MOBILE"
    TABLET = "TABLET"
```

### 2.3 Model 구현

#### 2.3.1 User 모델 (app/models/user.py)

```python
"""
User model
Based on PRD_Account_Design.md Section 3
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base
from app.config import settings
from app.utils.enums import EnumUserRole


class User(Base):
    """
    사용자 모델

    Attributes:
        id: Primary key
        login_id: 로그인 아이디 (unique)
        password_hash: 비밀번호 해시 (bcrypt)
        name: 이름
        department: 소속 (부서/부대)
        position: 직급
        employee_number: 소속번호 (사번/군번)
        photo_url: 사진 URL
        email: 이메일
        phone: 연락처
        role: 등급 (ADMIN, MAINTAINER, OPERATOR, VIEWER, GUEST)
        group_id: FK → user_groups.id (1:1 관계)
        is_active: 활성화 여부
        is_locked: 계정 잠금 여부
        lock_reason: 잠금 사유
        locked_at: 잠금 시간
        locked_by: 잠금 처리자
        password_changed_at: 비밀번호 변경일
        password_expires_at: 비밀번호 만료일
        failed_login_count: 로그인 실패 횟수
        last_login_at: 마지막 로그인
        last_login_ip: 마지막 로그인 IP
        created_at: 생성 시간
        updated_at: 수정 시간
        created_by: 생성자
        updated_by: 수정자
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    login_id = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # 인적 정보
    name = Column(String(100), nullable=False)
    department = Column(String(100), nullable=True)
    position = Column(String(50), nullable=True)
    employee_number = Column(String(50), nullable=True)
    photo_url = Column(String(500), nullable=True)
    email = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)

    # 권한/등급
    role = Column(
        SQLEnum(EnumUserRole),
        nullable=False,
        default=EnumUserRole.VIEWER,
        index=True
    )
    group_id = Column(
        Integer,
        ForeignKey("user_groups.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )  # 사용자 그룹 (1:1 관계)

    # 상태
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    is_locked = Column(Boolean, nullable=False, default=False)
    lock_reason = Column(String(200), nullable=True)
    locked_at = Column(DateTime, nullable=True)
    locked_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # 비밀번호 정책
    password_changed_at = Column(DateTime, nullable=True)
    password_expires_at = Column(DateTime, nullable=True)
    failed_login_count = Column(Integer, nullable=False, default=0)

    # 마지막 활동
    last_login_at = Column(DateTime, nullable=True)
    last_login_ip = Column(String(45), nullable=True)

    # 타임스탬프
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(settings.tz),
        nullable=False
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(settings.tz),
        onupdate=lambda: datetime.now(settings.tz),
        nullable=False
    )
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships (1:1 with UserGroup)
    group = relationship("UserGroup", back_populates="users", foreign_keys=[group_id])
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    login_logs = relationship("UserLoginLog", back_populates="user")
    locked_by_user = relationship("User", remote_side=[id], foreign_keys=[locked_by])

    def __repr__(self):
        return f"<User(id={self.id}, login_id='{self.login_id}', role='{self.role.value}')>"
```

#### 2.3.2 UserGroup 모델 (app/models/user_group.py)

```python
"""
UserGroup model
Based on PRD_Account_Design.md Section 4
사용자와 그룹은 1:1 관계입니다. 사용자는 하나의 그룹에만 소속될 수 있습니다.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base
from app.config import settings


class UserGroup(Base):
    """
    사용자 그룹 모델

    Attributes:
        id: Primary key
        name: 그룹명
        description: 설명
        permissions: 세부 권한 설정 (JSONB)
        is_active: 활성화 여부
        created_at: 생성 시간
        updated_at: 수정 시간
        created_by: 생성자
        updated_by: 수정자
        users: 그룹 소속 사용자 목록 (1:N - 그룹 관점)
    """
    __tablename__ = "user_groups"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(String(500), nullable=True)
    permissions = Column(JSON, nullable=True)  # JSONB
    is_active = Column(Boolean, nullable=False, default=True)

    # 타임스탬프
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(settings.tz),
        nullable=False
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(settings.tz),
        onupdate=lambda: datetime.now(settings.tz),
        nullable=False
    )
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships (1:N - 그룹은 여러 사용자를 가질 수 있음)
    users = relationship("User", back_populates="group", foreign_keys="User.group_id")

    def __repr__(self):
        return f"<UserGroup(id={self.id}, name='{self.name}')>"
```

> **Note**: 사용자-그룹은 1:1 관계입니다. 기존 N:N 관계를 위한 `user_group_mappings` 테이블은 사용하지 않습니다.
> 사용자의 그룹 변경은 `/users/{id}` PUT API의 `group_id` 필드를 통해 수행합니다.

#### 2.3.3 UserSession 모델 (app/models/user_session.py)

```python
"""
UserSession model
Based on PRD_Account_Design.md Section 5
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base
from app.config import settings
from app.utils.enums import EnumLogoutReason, EnumDeviceType


class UserSession(Base):
    """
    사용자 세션 모델

    Attributes:
        id: Primary key
        user_id: FK → users.id
        token: JWT 또는 세션 토큰
        refresh_token: 리프레시 토큰
        ip_address: 접속 IP
        user_agent: 브라우저/클라이언트 정보
        device_type: PC, MOBILE, TABLET
        location: 접속 위치 (GeoIP)
        login_at: 로그인 시간
        expires_at: 만료 시간
        last_activity: 마지막 활동 시간
        is_active: 활성 여부
        logged_out_at: 로그아웃 시간
        logout_reason: 로그아웃 사유
        forced_by: 강제 로그아웃 처리자
    """
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 토큰 정보
    token = Column(String(500), unique=True, nullable=False, index=True)
    refresh_token = Column(String(500), nullable=True)

    # 접속 정보
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(String(500), nullable=True)
    device_type = Column(SQLEnum(EnumDeviceType), nullable=True)
    location = Column(String(200), nullable=True)

    # 세션 상태
    login_at = Column(
        DateTime,
        default=lambda: datetime.now(settings.tz),
        nullable=False,
        index=True
    )
    expires_at = Column(DateTime, nullable=False, index=True)
    last_activity = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    # 로그아웃 정보
    logged_out_at = Column(DateTime, nullable=True)
    logout_reason = Column(SQLEnum(EnumLogoutReason), nullable=True)
    forced_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    user = relationship("User", back_populates="sessions", foreign_keys=[user_id])
    forced_by_user = relationship("User", foreign_keys=[forced_by])

    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, is_active={self.is_active})>"
```

#### 2.3.4 UserLoginLog 모델 (app/models/user_login_log.py)

```python
"""
UserLoginLog model
Based on PRD_Account_Design.md Section 6
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base
from app.config import settings
from app.utils.enums import EnumLoginAction, EnumLoginResult


class UserLoginLog(Base):
    """
    사용자 로그인 로그 모델

    Attributes:
        id: Primary key
        user_id: FK → users.id (SET NULL)
        login_id: 시도한 로그인 ID
        action: LOGIN, LOGOUT, REFRESH
        ip_address: 접속 IP
        user_agent: 브라우저/클라이언트 정보
        result: SUCCESS, FAILURE
        failure_reason: 실패 사유
        created_at: 생성 시간
    """
    __tablename__ = "user_login_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    login_id = Column(String(50), nullable=False, index=True)

    # 행위
    action = Column(SQLEnum(EnumLoginAction), nullable=False, index=True)

    # 접속 정보
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(String(500), nullable=True)

    # 결과
    result = Column(SQLEnum(EnumLoginResult), nullable=False, index=True)
    failure_reason = Column(String(100), nullable=True)

    # 타임스탬프
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(settings.tz),
        nullable=False,
        index=True
    )

    # Relationships
    user = relationship("User", back_populates="login_logs")

    def __repr__(self):
        return f"<UserLoginLog(id={self.id}, login_id='{self.login_id}', action='{self.action.value}')>"
```

### 2.4 API Endpoint 정의

#### 2.4.1 인증 API (/api/auth)

| Method | Endpoint | 설명 | 권한 |
|--------|----------|------|------|
| POST | `/api/auth/login` | 로그인 | Public |
| POST | `/api/auth/logout` | 로그아웃 | 로그인 사용자 |
| POST | `/api/auth/refresh` | 토큰 갱신 | 로그인 사용자 |
| GET | `/api/auth/me` | 현재 사용자 정보 | 로그인 사용자 |

#### 2.4.2 사용자 API (/api/users)

| Method | Endpoint | 설명 | 권한 |
|--------|----------|------|------|
| GET | `/api/users` | 사용자 목록 조회 | ADMIN |
| GET | `/api/users/{id}` | 사용자 상세 조회 | ADMIN |
| POST | `/api/users` | 사용자 생성 | ADMIN |
| PUT | `/api/users/{id}` | 사용자 수정 | ADMIN |
| DELETE | `/api/users/{id}` | 사용자 삭제 | ADMIN |
| POST | `/api/users/{id}/lock` | 계정 잠금 | ADMIN |
| POST | `/api/users/{id}/unlock` | 계정 잠금 해제 | ADMIN |
| POST | `/api/users/{id}/reset-password` | 비밀번호 초기화 | ADMIN |
| GET | `/api/users/me` | 내 정보 조회 | 로그인 사용자 |
| PUT | `/api/users/me` | 내 정보 수정 | 로그인 사용자 |
| PUT | `/api/users/me/password` | 내 비밀번호 변경 | 로그인 사용자 |

#### 2.4.3 사용자 그룹 API (/api/user-groups)

| Method | Endpoint | 설명 | 권한 |
|--------|----------|------|------|
| GET | `/api/user-groups` | 그룹 목록 조회 | ADMIN |
| GET | `/api/user-groups/{id}` | 그룹 상세 조회 | ADMIN |
| POST | `/api/user-groups` | 그룹 생성 | ADMIN |
| PUT | `/api/user-groups/{id}` | 그룹 수정 | ADMIN |
| DELETE | `/api/user-groups/{id}` | 그룹 삭제 | ADMIN |
| GET | `/api/user-groups/{id}/users` | 그룹 소속 사용자 목록 | ADMIN |

> **Note**: 사용자의 그룹 변경은 `/users/{id}` PUT API의 `group_id` 필드를 통해 수행합니다. (1:1 관계)

#### 2.4.4 사용자 세션 API (/api/user-sessions)

| Method | Endpoint | 설명 | 권한 |
|--------|----------|------|------|
| GET | `/api/user-sessions` | 활성 세션 목록 | ADMIN |
| GET | `/api/user-sessions/{id}` | 세션 상세 조회 | ADMIN |
| DELETE | `/api/user-sessions/{id}` | 강제 로그아웃 | ADMIN |
| DELETE | `/api/user-sessions/user/{user_id}` | 특정 사용자 전체 세션 종료 | ADMIN |
| GET | `/api/user-sessions/me` | 내 세션 목록 | 로그인 사용자 |
| DELETE | `/api/user-sessions/me/{id}` | 내 다른 세션 종료 | 로그인 사용자 |

---

## 3. 데이터베이스 스키마

### 3.1 테이블 생성 순서

의존성 순서에 따라 테이블을 생성해야 한다:

1. `user_groups` (먼저 생성하여 users에서 참조 가능하게 함)
2. `users` (user_groups.id를 FK로 참조, 자기 참조 FK도 포함)
3. `user_sessions` (users 참조)
4. `user_login_logs` (users 참조)

> **Note**: 사용자-그룹은 1:1 관계이므로 `user_group_mappings` 테이블은 사용하지 않습니다.

### 3.2 PostgreSQL DDL

```sql
-- ============================================
-- 1. ENUM 타입 생성
-- ============================================
CREATE TYPE enum_user_role AS ENUM ('ADMIN', 'MAINTAINER', 'OPERATOR', 'VIEWER', 'GUEST');
CREATE TYPE enum_logout_reason AS ENUM ('MANUAL', 'EXPIRED', 'FORCED', 'LOCKED', 'PASSWORD_CHANGED', 'DUPLICATE');
CREATE TYPE enum_login_action AS ENUM ('LOGIN', 'LOGOUT', 'REFRESH');
CREATE TYPE enum_login_result AS ENUM ('SUCCESS', 'FAILURE');
CREATE TYPE enum_device_type AS ENUM ('PC', 'MOBILE', 'TABLET');

-- ============================================
-- 2. users 테이블
-- ============================================
CREATE TABLE users (
    id                    SERIAL PRIMARY KEY,
    login_id              VARCHAR(50) NOT NULL UNIQUE,
    password_hash         VARCHAR(255) NOT NULL,

    -- 인적 정보
    name                  VARCHAR(100) NOT NULL,
    department            VARCHAR(100),
    position              VARCHAR(50),
    employee_number       VARCHAR(50),
    photo_url             VARCHAR(500),
    email                 VARCHAR(200),
    phone                 VARCHAR(50),

    -- 권한/등급
    role                  enum_user_role NOT NULL DEFAULT 'VIEWER',
    group_id              INTEGER REFERENCES user_groups(id) ON DELETE SET NULL,  -- 소속 그룹 (1:1)

    -- 상태
    is_active             BOOLEAN NOT NULL DEFAULT TRUE,
    is_locked             BOOLEAN NOT NULL DEFAULT FALSE,
    lock_reason           VARCHAR(200),
    locked_at             TIMESTAMP WITH TIME ZONE,
    locked_by             INTEGER REFERENCES users(id) ON DELETE SET NULL,

    -- 비밀번호 정책
    password_changed_at   TIMESTAMP WITH TIME ZONE,
    password_expires_at   TIMESTAMP WITH TIME ZONE,
    failed_login_count    INTEGER NOT NULL DEFAULT 0,

    -- 마지막 활동
    last_login_at         TIMESTAMP WITH TIME ZONE,
    last_login_ip         VARCHAR(45),

    -- 타임스탬프
    created_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by            INTEGER REFERENCES users(id) ON DELETE SET NULL,
    updated_by            INTEGER REFERENCES users(id) ON DELETE SET NULL
);

-- 인덱스
CREATE INDEX idx_users_login_id ON users(login_id);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_group_id ON users(group_id);  -- 그룹 조회용 인덱스
CREATE INDEX idx_users_department ON users(department);
CREATE INDEX idx_users_is_active ON users(is_active);

-- ============================================
-- 3. user_groups 테이블
-- ============================================
CREATE TABLE user_groups (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    description     VARCHAR(500),
    permissions     JSONB,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by      INTEGER REFERENCES users(id) ON DELETE SET NULL,
    updated_by      INTEGER REFERENCES users(id) ON DELETE SET NULL
);

-- 인덱스
CREATE INDEX idx_user_groups_name ON user_groups(name);

-- ============================================
-- 4. user_sessions 테이블
-- ============================================
-- Note: user_group_mappings 테이블은 사용하지 않습니다. (1:1 관계로 변경됨)
CREATE TABLE user_sessions (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- 토큰 정보
    token           VARCHAR(500) NOT NULL UNIQUE,
    refresh_token   VARCHAR(500),

    -- 접속 정보
    ip_address      VARCHAR(45) NOT NULL,
    user_agent      VARCHAR(500),
    device_type     enum_device_type,
    location        VARCHAR(200),

    -- 세션 상태
    login_at        TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at      TIMESTAMP WITH TIME ZONE NOT NULL,
    last_activity   TIMESTAMP WITH TIME ZONE,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,

    -- 로그아웃 정보
    logged_out_at   TIMESTAMP WITH TIME ZONE,
    logout_reason   enum_logout_reason,
    forced_by       INTEGER REFERENCES users(id) ON DELETE SET NULL
);

-- 인덱스
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_token ON user_sessions(token);
CREATE INDEX idx_user_sessions_is_active ON user_sessions(is_active);
CREATE INDEX idx_user_sessions_login_at ON user_sessions(login_at);
CREATE INDEX idx_user_sessions_expires_at ON user_sessions(expires_at);

-- ============================================
-- 5. user_login_logs 테이블
-- ============================================
CREATE TABLE user_login_logs (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER REFERENCES users(id) ON DELETE SET NULL,
    login_id        VARCHAR(50) NOT NULL,

    -- 행위
    action          enum_login_action NOT NULL,

    -- 접속 정보
    ip_address      VARCHAR(45) NOT NULL,
    user_agent      VARCHAR(500),

    -- 결과
    result          enum_login_result NOT NULL,
    failure_reason  VARCHAR(100),

    -- 타임스탬프
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- 인덱스
CREATE INDEX idx_user_login_logs_user_id ON user_login_logs(user_id);
CREATE INDEX idx_user_login_logs_login_id ON user_login_logs(login_id);
CREATE INDEX idx_user_login_logs_action ON user_login_logs(action);
CREATE INDEX idx_user_login_logs_result ON user_login_logs(result);
CREATE INDEX idx_user_login_logs_created_at ON user_login_logs(created_at);
```

### 3.3 초기 데이터 (Seed)

```sql
-- 기본 관리자 계정 생성 (비밀번호: Admin@123!)
INSERT INTO users (login_id, password_hash, name, role, is_active)
VALUES (
    'admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NTMhWO.DKK1qHa',
    '시스템 관리자',
    'ADMIN',
    TRUE
);
```

---

## 4. API 문서화 (Swagger/OpenAPI)

### 4.1 태그 정의

```python
# main.py 또는 app/__init__.py
tags_metadata = [
    # ... 기존 태그 ...
    {
        "name": "Auth",
        "description": "인증 관련 API (로그인, 로그아웃, 토큰 갱신)"
    },
    {
        "name": "Users",
        "description": "사용자 관리 API"
    },
    {
        "name": "UserGroups",
        "description": "사용자 그룹 관리 API"
    },
    {
        "name": "UserSessions",
        "description": "사용자 세션 관리 API"
    },
]
```

### 4.2 API 문서 접근 경로

| 경로 | 설명 |
|------|------|
| `/docs` | Swagger UI |
| `/redoc` | ReDoc UI |
| `/openapi.json` | OpenAPI JSON 스펙 |

### 4.3 보안 스키마 추가

```python
# FastAPI app 설정
from fastapi.security import HTTPBearer

security = HTTPBearer()

app = FastAPI(
    # ...
    openapi_tags=tags_metadata,
    components={
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        }
    }
)
```

---

## 5. GOP_스키마_전체.md 업데이트

### 5.1 업데이트 위치

GOP_스키마_전체.md 문서에 다음 섹션을 추가한다:

1. **목차 추가** (섹션 번호 부여)
   - 11. [User 관련 테이블](#11-user-관련-테이블)
     - 11.1 [users 테이블](#111-users-테이블)
     - 11.2 [user_groups 테이블](#112-user_groups-테이블)
     - 11.3 [user_sessions 테이블](#113-user_sessions-테이블)
     - 11.4 [user_login_logs 테이블](#114-user_login_logs-테이블)

2. **Enum 타입 추가** (섹션 8)
   - enum_user_role
   - enum_logout_reason
   - enum_login_action
   - enum_login_result
   - enum_device_type

3. **ERD 다이어그램 업데이트** (섹션 9)

4. **변경 이력 업데이트** (섹션 10)

### 5.2 추가할 내용 템플릿

```markdown
## 11. User 관련 테이블

### 11.1 users 테이블

사용자 계정 정보를 저장하는 테이블입니다.

#### PostgreSQL CREATE TABLE

```sql
-- (섹션 3.2의 users DDL 삽입)
```

#### 필드 정의

| 필드명 | 타입 | NULL 허용 | 기본값 | 설명 |
|--------|------|-----------|--------|------|
| id | SERIAL | NO | AUTO | 고유 식별자 (PK) |
| login_id | VARCHAR(50) | NO | - | 로그인 아이디 (UNIQUE) |
| password_hash | VARCHAR(255) | NO | - | 비밀번호 해시 (bcrypt) |
| name | VARCHAR(100) | NO | - | 이름 |
| department | VARCHAR(100) | YES | NULL | 소속 (부서/부대) |
| position | VARCHAR(50) | YES | NULL | 직급 |
| employee_number | VARCHAR(50) | YES | NULL | 소속번호 (사번/군번) |
| photo_url | VARCHAR(500) | YES | NULL | 사진 URL |
| email | VARCHAR(200) | YES | NULL | 이메일 |
| phone | VARCHAR(50) | YES | NULL | 연락처 |
| role | ENUM | NO | VIEWER | 등급 |
| group_id | INTEGER | YES | NULL | FK → user_groups.id (소속 그룹, 1:1) |
| is_active | BOOLEAN | NO | TRUE | 활성화 여부 |
| is_locked | BOOLEAN | NO | FALSE | 계정 잠금 여부 |
| lock_reason | VARCHAR(200) | YES | NULL | 잠금 사유 |
| locked_at | TIMESTAMP | YES | NULL | 잠금 시간 |
| locked_by | INTEGER | YES | NULL | FK → users.id (잠금 처리자) |
| password_changed_at | TIMESTAMP | YES | NULL | 비밀번호 변경일 |
| password_expires_at | TIMESTAMP | YES | NULL | 비밀번호 만료일 |
| failed_login_count | INTEGER | NO | 0 | 로그인 실패 횟수 |
| last_login_at | TIMESTAMP | YES | NULL | 마지막 로그인 |
| last_login_ip | VARCHAR(45) | YES | NULL | 마지막 로그인 IP |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 생성 시간 |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 수정 시간 |
| created_by | INTEGER | YES | NULL | FK → users.id (생성자) |
| updated_by | INTEGER | YES | NULL | FK → users.id (수정자) |

<!-- 나머지 테이블들도 동일한 형식으로 작성 -->
```

### 5.3 변경 이력 추가

```markdown
| 버전 | 일자 | 작성자 | 변경 내용 |
|------|------|--------|-----------|
| v2.1 | 2026-01-19 | - | User 관련 테이블 추가 (users, user_groups, user_sessions, user_login_logs). 사용자-그룹 1:1 관계 |
```

---

## 6. GOP_Restful_Api_연동설계.md 업데이트

### 6.1 업데이트 규칙

1. **관련 응답 구조 업데이트**: 영향받는 모든 엔드포인트의 Response 구조 수정
2. **삭제 항목 처리**: 변경된 항목은 기존 내용 삭제 후 새 내용으로 교체
3. **문서 상단 버전/날짜 업데이트**: 버전 v3.0, 날짜 2026-01-19
4. **부록 변경 이력**: 같은 날짜 변경사항은 하나의 항목으로 그룹핑

### 6.2 목차 추가

```markdown
11. [User API 설계](#11-user-api-설계)
    - 11.1 [개요](#111-개요)
    - 11.2 [Auth API](#112-auth-api)
    - 11.3 [User API](#113-user-api)
    - 11.4 [UserGroup API](#114-usergroup-api)
    - 11.5 [UserSession API](#115-usersession-api)
```

### 6.3 섹션 11 추가 내용

```markdown
## 11. User API 설계

### 11.1 개요

사용자 계정, 그룹, 세션 관리를 위한 API입니다.

**관련 테이블**: users, user_groups, user_sessions, user_login_logs

> **Note**: 사용자와 그룹은 1:1 관계입니다. users 테이블의 group_id FK로 user_groups를 참조합니다.

**권한 체계**:
| 등급 | 코드 | 설명 |
|------|------|------|
| 관리자 | ADMIN | 시스템 전체 관리 |
| 유지보수자 | MAINTAINER | 장비/시스템 관리 |
| 운영자 | OPERATOR | 일반 운영 |
| 조회자 | VIEWER | 조회 전용 |
| 게스트 | GUEST | 제한된 접근 |

---

### 11.2 Auth API

인증 관련 API입니다.

#### 11.2.1 로그인

**POST** `/api/auth/login`

로그인하여 JWT 토큰을 발급받습니다.

**Request Body:**
```json
{
  "login_id": "operator01",
  "password": "SecureP@ss123!"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "Bearer",
    "expires_in": 43200,
    "user": {
      "id": 1,
      "login_id": "operator01",
      "name": "홍길동",
      "department": "경계부대 1중대",
      "position": "상병",
      "role": "OPERATOR",
      "role_display": "운영자",
      "photo_url": "/uploads/photos/user_001.jpg",
      "permissions": {
        "modules": {
          "events": {"view": true, "edit": true, "delete": false},
          "cameras": {"view": true, "edit": false, "control": true},
          "devices": {"view": true, "edit": false},
          "reports": {"view": true, "export": true},
          "settings": {"view": false, "edit": false},
          "users": {"view": false, "edit": false}
        },
        "device_groups": [1, 2, 3],
        "time_restriction": {
          "enabled": true,
          "allowed_hours": {"start": "08:00", "end": "18:00"},
          "allowed_days": ["MON", "TUE", "WED", "THU", "FRI"]
        }
      }
    }
  },
  "meta": {
    "timestamp": "2026-01-19T10:30:00+09:00"
  }
}
```

**Error Response (401 Unauthorized):**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "아이디 또는 비밀번호가 올바르지 않습니다."
  }
}
```

#### 11.2.2 로그아웃

**POST** `/api/auth/logout`

현재 세션을 종료합니다.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

#### 11.2.3 토큰 갱신

**POST** `/api/auth/refresh`

리프레시 토큰으로 새 액세스 토큰을 발급받습니다.

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 43200
  }
}
```

#### 11.2.4 현재 사용자 정보

**GET** `/api/auth/me`

현재 로그인한 사용자 정보를 조회합니다.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "login_id": "operator01",
    "name": "홍길동",
    "department": "경계부대 1중대",
    "position": "상병",
    "role": "OPERATOR",
    "role_display": "운영자",
    "email": "operator01@example.com",
    "phone": "010-1234-5678",
    "photo_url": "/uploads/photos/user_001.jpg",
    "group": {
      "id": 1,
      "name": "1중대 운영팀"
    },
    "last_login_at": "2026-01-19T08:30:00+09:00"
  }
}
```

> **Note**: 사용자와 그룹은 1:1 관계입니다. 사용자는 하나의 그룹에만 소속될 수 있습니다.

---

### 11.3 User API

사용자 관리 API입니다. (ADMIN 권한 필요)

#### 11.3.1 사용자 목록 조회

**GET** `/api/users`

**Query Parameters:**
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| page | integer | N | 페이지 번호 (기본: 1) |
| limit | integer | N | 페이지당 항목 수 (기본: 20) |
| role | string | N | 등급 필터 |
| department | string | N | 소속 필터 |
| is_active | boolean | N | 활성화 필터 |
| search | string | N | 검색어 (login_id, name) |

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "login_id": "operator01",
      "name": "홍길동",
      "department": "경계부대 1중대",
      "position": "상병",
      "role": "OPERATOR",
      "role_display": "운영자",
      "is_active": true,
      "is_locked": false,
      "last_login_at": "2026-01-19T08:30:00+09:00",
      "created_at": "2026-01-01T09:00:00+09:00"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 45,
    "total_pages": 3
  }
}
```

#### 11.3.2 사용자 생성

**POST** `/api/users`

**Request Body:**
```json
{
  "login_id": "operator01",
  "password": "SecureP@ss123!",
  "name": "홍길동",
  "department": "경계부대 1중대",
  "position": "상병",
  "employee_number": "21-12345678",
  "email": "operator01@example.com",
  "phone": "010-1234-5678",
  "role": "OPERATOR",
  "group_id": 1
}
```

> **Note**: `group_id`는 사용자가 소속될 그룹의 ID입니다. (1:1 관계)

**Response (201 Created):**
```json
{
  "success": true,
  "message": "User created successfully",
  "data": {
    "id": 10,
    "login_id": "operator01",
    "name": "홍길동",
    "role": "OPERATOR"
  }
}
```

#### 11.3.3 사용자 상세 조회

**GET** `/api/users/{id}`

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "login_id": "operator01",
    "name": "홍길동",
    "department": "경계부대 1중대",
    "position": "상병",
    "employee_number": "21-12345678",
    "photo_url": "/uploads/photos/user_001.jpg",
    "email": "operator01@example.com",
    "phone": "010-1234-5678",
    "role": "OPERATOR",
    "role_display": "운영자",
    "is_active": true,
    "is_locked": false,
    "last_login_at": "2026-01-19T08:30:00+09:00",
    "last_login_ip": "192.168.1.100",
    "group": {
      "id": 1,
      "name": "1중대 운영팀"
    },
    "created_at": "2026-01-01T09:00:00+09:00",
    "updated_at": "2026-01-15T14:30:00+09:00"
  }
}
```

#### 11.3.4 사용자 수정

**PUT** `/api/users/{id}`

**Request Body:**
```json
{
  "name": "홍길동",
  "department": "경계부대 2중대",
  "position": "병장",
  "email": "operator01@example.com",
  "role": "OPERATOR",
  "is_active": true,
  "group_id": 1
}
```

> **Note**: 사용자의 그룹 변경은 `group_id` 필드를 통해 수행합니다. (1:1 관계)

**Response (200 OK):**
```json
{
  "success": true,
  "message": "User updated successfully"
}
```

#### 11.3.5 사용자 삭제

**DELETE** `/api/users/{id}`

**Response (200 OK):**
```json
{
  "success": true,
  "message": "User deleted successfully"
}
```

#### 11.3.6 계정 잠금

**POST** `/api/users/{id}/lock`

**Request Body:**
```json
{
  "reason": "보안 위반으로 인한 계정 잠금"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Account locked successfully"
}
```

#### 11.3.7 계정 잠금 해제

**POST** `/api/users/{id}/unlock`

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Account unlocked successfully"
}
```

#### 11.3.8 비밀번호 초기화

**POST** `/api/users/{id}/reset-password`

**Request Body (선택):**
```json
{
  "new_password": "NewP@ss123!"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Password reset successfully",
  "data": {
    "temporary_password": "TempPass@456!"
  }
}
```

---

### 11.4 UserGroup API

사용자 그룹 관리 API입니다. (ADMIN 권한 필요)

#### 11.4.1 그룹 목록 조회

**GET** `/api/user-groups`

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "1중대 운영팀",
      "description": "1중대 경계 시스템 운영 담당",
      "is_active": true,
      "user_count": 5,
      "created_at": "2026-01-01T09:00:00+09:00"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 10,
    "total_pages": 1
  }
}
```

#### 11.4.2 그룹 생성

**POST** `/api/user-groups`

**Request Body:**
```json
{
  "name": "1중대 운영팀",
  "description": "1중대 경계 시스템 운영 담당",
  "permissions": {
    "modules": {
      "events": {"view": true, "edit": true, "delete": false},
      "cameras": {"view": true, "edit": true, "control": true},
      "devices": {"view": true, "edit": false},
      "reports": {"view": true, "export": true},
      "settings": {"view": false, "edit": false},
      "users": {"view": false, "edit": false}
    },
    "device_groups": [1, 2, 3],
    "time_restriction": {
      "enabled": true,
      "allowed_hours": {"start": "08:00", "end": "18:00"},
      "allowed_days": ["MON", "TUE", "WED", "THU", "FRI"]
    }
  }
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "User group created successfully",
  "data": {
    "id": 5
  }
}
```

#### 11.4.3 그룹 상세 조회

**GET** `/api/user-groups/{id}`

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "1중대 운영팀",
    "description": "1중대 경계 시스템 운영 담당",
    "permissions": {
      "modules": {
        "events": {"view": true, "edit": true, "delete": false},
        "cameras": {"view": true, "edit": true, "control": true},
        "devices": {"view": true, "edit": false},
        "reports": {"view": true, "export": true},
        "settings": {"view": false, "edit": false},
        "users": {"view": false, "edit": false}
      },
      "device_groups": [1, 2, 3],
      "time_restriction": {
        "enabled": true,
        "allowed_hours": {"start": "08:00", "end": "18:00"},
        "allowed_days": ["MON", "TUE", "WED", "THU", "FRI"]
      }
    },
    "is_active": true,
    "user_count": 5,
    "users": [
      {"id": 1, "login_id": "operator01", "name": "홍길동", "role": "OPERATOR"},
      {"id": 2, "login_id": "operator02", "name": "김철수", "role": "OPERATOR"}
    ],
    "created_at": "2026-01-01T09:00:00+09:00",
    "updated_at": "2026-01-15T14:30:00+09:00"
  }
}
```

> **Note**: 사용자의 그룹 변경은 `/users/{id}` PUT API의 `group_id` 필드를 통해 수행합니다. (1:1 관계)
> 기존 N:N 관계를 위한 그룹-사용자 추가/제거 API는 더 이상 제공하지 않습니다.

---

### 11.5 UserSession API

사용자 세션 관리 API입니다.

#### 11.5.1 활성 세션 목록 (관리자)

**GET** `/api/user-sessions`

**Query Parameters:**
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| user_id | integer | N | 사용자 ID 필터 |
| is_active | boolean | N | 활성 여부 필터 |

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": 101,
      "user": {
        "id": 1,
        "login_id": "operator01",
        "name": "홍길동",
        "department": "경계부대 1중대",
        "position": "상병",
        "role": "OPERATOR",
        "role_display": "운영자",
        "photo_url": "/uploads/photos/user_001.jpg"
      },
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0",
      "device_type": "PC",
      "login_at": "2026-01-19T08:30:00+09:00",
      "last_activity": "2026-01-19T10:40:00+09:00",
      "duration_minutes": 135,
      "expires_at": "2026-01-19T20:30:00+09:00",
      "is_active": true
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 15,
    "total_pages": 1
  }
}
```

#### 11.5.2 강제 로그아웃

**DELETE** `/api/user-sessions/{id}`

특정 세션을 강제 종료합니다.

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Session terminated successfully"
}
```

#### 11.5.3 내 세션 목록

**GET** `/api/user-sessions/me`

현재 사용자의 모든 활성 세션을 조회합니다.

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": 101,
      "ip_address": "192.168.1.100",
      "user_agent": "Chrome/120.0 (Windows)",
      "device_type": "PC",
      "login_at": "2026-01-19T08:30:00+09:00",
      "is_current": true
    },
    {
      "id": 102,
      "ip_address": "192.168.1.150",
      "user_agent": "Safari (iPhone)",
      "device_type": "MOBILE",
      "login_at": "2026-01-18T19:00:00+09:00",
      "is_current": false
    }
  ]
}
```
```

### 6.4 문서 상단 버전 업데이트

```markdown
**최종 수정일**: 2026-01-19
**버전**: v3.0
```

### 6.5 부록 변경 이력 추가

```markdown
### 10.4 User API 추가 변경사항 (v3.0)

**변경일**: 2026-01-19

#### 추가된 API

| 분류 | Endpoint | 설명 |
|------|----------|------|
| Auth | POST `/api/auth/login` | 로그인 |
| Auth | POST `/api/auth/logout` | 로그아웃 |
| Auth | POST `/api/auth/refresh` | 토큰 갱신 |
| Auth | GET `/api/auth/me` | 현재 사용자 정보 |
| Users | GET `/api/users` | 사용자 목록 조회 |
| Users | POST `/api/users` | 사용자 생성 |
| Users | GET `/api/users/{id}` | 사용자 상세 조회 |
| Users | PUT `/api/users/{id}` | 사용자 수정 |
| Users | DELETE `/api/users/{id}` | 사용자 삭제 |
| Users | POST `/api/users/{id}/lock` | 계정 잠금 |
| Users | POST `/api/users/{id}/unlock` | 계정 잠금 해제 |
| Users | POST `/api/users/{id}/reset-password` | 비밀번호 초기화 |
| Users | GET `/api/users/me` | 내 정보 조회 |
| Users | PUT `/api/users/me` | 내 정보 수정 |
| Users | PUT `/api/users/me/password` | 내 비밀번호 변경 |
| UserGroups | GET `/api/user-groups` | 그룹 목록 조회 |
| UserGroups | POST `/api/user-groups` | 그룹 생성 |
| UserGroups | GET `/api/user-groups/{id}` | 그룹 상세 조회 |
| UserGroups | PUT `/api/user-groups/{id}` | 그룹 수정 |
| UserGroups | DELETE `/api/user-groups/{id}` | 그룹 삭제 |
| UserGroups | GET `/api/user-groups/{id}/users` | 그룹 소속 사용자 목록 |
| UserSessions | GET `/api/user-sessions` | 활성 세션 목록 |
| UserSessions | GET `/api/user-sessions/{id}` | 세션 상세 조회 |
| UserSessions | DELETE `/api/user-sessions/{id}` | 강제 로그아웃 |
| UserSessions | DELETE `/api/user-sessions/user/{user_id}` | 특정 사용자 전체 세션 종료 |
| UserSessions | GET `/api/user-sessions/me` | 내 세션 목록 |
| UserSessions | DELETE `/api/user-sessions/me/{id}` | 내 다른 세션 종료 |

#### 추가된 테이블

- users (사용자) - group_id FK로 user_groups 참조 (1:1 관계)
- user_groups (사용자 그룹)
- user_sessions (사용자 세션)
- user_login_logs (로그인 로그)

> **Note**: 사용자-그룹은 1:1 관계입니다. `user_group_mappings` 테이블은 사용하지 않습니다.

#### 추가된 Enum

- enum_user_role: ADMIN, MAINTAINER, OPERATOR, VIEWER, GUEST
- enum_logout_reason: MANUAL, EXPIRED, FORCED, LOCKED, PASSWORD_CHANGED, DUPLICATE
- enum_login_action: LOGIN, LOGOUT, REFRESH
- enum_login_result: SUCCESS, FAILURE
- enum_device_type: PC, MOBILE, TABLET
```

---

## 7. 구현 체크리스트

### 7.1 코드 구현

- [ ] app/utils/enums.py - Enum 추가
- [ ] app/utils/security.py - 보안 유틸리티 (bcrypt, JWT)
- [ ] app/utils/dependencies.py - 인증 dependency
- [ ] app/models/user.py - User 모델 (group_id FK 포함)
- [ ] app/models/user_group.py - UserGroup 모델 (1:1 관계)
- [ ] app/models/user_session.py - UserSession 모델
- [ ] app/models/user_login_log.py - UserLoginLog 모델
- [ ] app/models/__init__.py - 모델 export 추가
- [ ] app/schemas/user.py - User 스키마
- [ ] app/schemas/user_group.py - UserGroup 스키마
- [ ] app/schemas/user_session.py - UserSession 스키마
- [ ] app/schemas/auth.py - 인증 스키마
- [ ] app/services/auth_service.py - 인증 서비스
- [ ] app/services/user_service.py - 사용자 서비스
- [ ] app/routers/auth.py - Auth 라우터
- [ ] app/routers/users.py - Users 라우터
- [ ] app/routers/user_groups.py - UserGroups 라우터
- [ ] app/routers/user_sessions.py - UserSessions 라우터
- [ ] app/main.py - 라우터 등록, 태그 추가

### 7.2 데이터베이스

- [ ] Alembic 마이그레이션 스크립트 생성
- [ ] ENUM 타입 생성
- [ ] 테이블 생성 (user_groups → users → user_sessions → user_login_logs)
- [ ] 인덱스 생성 (idx_users_group_id 포함)
- [ ] 초기 admin 계정 Seed

> **Note**: 사용자-그룹은 1:1 관계입니다. `user_group_mappings` 테이블은 생성하지 않습니다.

### 7.3 문서 업데이트

- [ ] GOP_스키마_전체.md - 섹션 11 추가 (user_group_mappings 제외)
- [ ] GOP_스키마_전체.md - Enum 추가
- [ ] GOP_스키마_전체.md - 변경 이력 추가 (1:1 관계 명시)
- [ ] GOP_Restful_Api_연동설계.md - 섹션 11 추가 (1:1 관계 반영)
- [ ] GOP_Restful_Api_연동설계.md - 버전/날짜 업데이트
- [ ] GOP_Restful_Api_연동설계.md - 부록 변경 이력 추가
- [ ] GOP_Restful_Api_연동설계.md - 목차 업데이트

### 7.4 테스트

- [ ] 단위 테스트 작성
- [ ] 통합 테스트 작성
- [ ] API 테스트 (Swagger UI)

---

## 8. 변경 이력

| 버전 | 일자 | 작성자 | 변경 내용 |
|------|------|--------|-----------|
| v1.0 | 2026-01-19 | - | 초안 작성 |
| v1.1 | 2026-01-19 | - | 사용자-그룹 관계를 N:N에서 1:1로 변경. UserGroupMapping 테이블 제거, users 테이블에 group_id FK 추가. permissions 예시에서 dashboard 모듈 제거, PRD_Account_Design.md v1.1과 동기화 |