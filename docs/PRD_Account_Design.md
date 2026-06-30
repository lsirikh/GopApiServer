# 사용자 계정 관리 시스템 설계서

**문서 버전**: v1.1
**작성일**: 2026-01-19
**상태**: Implemented  

---

## 1. 개요

### 1.1 목적
GOP 시스템의 사용자 계정, 그룹, 세션 관리 기능을 정의한다.
관리자가 사용자를 생성/수정/삭제하고, 세션을 모니터링하며, 권한을 제어할 수 있도록 한다.

### 1.2 주요 기능
- **사용자 관리**: 계정 생성, 수정, 삭제, 활성화/비활성화
- **사용자 그룹**: 사용자를 그룹으로 묶어 일괄 권한 관리
- **사용자 세션**: 로그인 현황 모니터링, 강제 로그아웃, 접근 차단

### 1.3 화면 구성

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  관리자 메뉴                                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ○ 사용자           ──▶  사용자 목록 (DataGrid) + 상세 정보                  │
│  ○ 사용자 그룹      ──▶  그룹 목록 + 소속 사용자 관리                        │
│  ○ 사용자 세션      ──▶  활성 세션 모니터링 + 강제 로그아웃                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 데이터 모델

### 2.1 ERD 구조

```
┌─────────────────┐                             ┌─────────────────┐
│     users       │                             │   user_groups   │
├─────────────────┤                             ├─────────────────┤
│ id (PK)         │                             │ id (PK)         │
│ login_id        │                          ┌──│ name            │
│ password_hash   │                          │  │ description     │
│ name            │                          │  │ permissions     │
│ department      │                          │  │ is_active       │
│ position        │                          │  │ created_at      │
│ employee_number │                          │  │ updated_at      │
│ photo_url       │                          │  └─────────────────┘
│ role            │                          │
│ group_id (FK)   │──────────────────────────┘  (1:1 관계)
│ is_active       │
│ is_locked       │       ┌─────────────────────┐
│ last_login_at   │       │   user_sessions     │
│ created_at      │       ├─────────────────────┤
│ updated_at      │       │ id (PK)             │
└─────────────────┘       │ user_id (FK)        │───────┐
                          │ token               │       │
                          │ ip_address          │       │
                          │ user_agent          │       │
                          │ login_at            │       │
                          │ expires_at          │       │
                          │ is_active           │       │
                          │ logged_out_at       │       │
                          │ logout_reason       │       │
                          └─────────────────────┘       │
                                                        │
                          ┌─────────────────────┐       │
                          │   user_login_logs   │       │
                          ├─────────────────────┤       │
                          │ id (PK)             │       │
                          │ user_id (FK)        │───────┘
                          │ action              │
                          │ ip_address          │
                          │ user_agent          │
                          │ result              │
                          │ failure_reason      │
                          │ created_at          │
                          └─────────────────────┘
```

---

## 3. 사용자 (Users)

### 3.1 테이블 스키마

```sql
CREATE TABLE users (
    -- 기본 정보
    id                  SERIAL PRIMARY KEY,
    login_id            VARCHAR(50) NOT NULL UNIQUE,      -- 로그인 아이디
    password_hash       VARCHAR(255) NOT NULL,            -- 비밀번호 해시 (bcrypt)

    -- 인적 정보
    name                VARCHAR(100) NOT NULL,            -- 이름
    department          VARCHAR(100),                     -- 소속 (부서/부대)
    position            VARCHAR(50),                      -- 직급
    employee_number     VARCHAR(50),                      -- 소속번호 (사번/군번)
    photo_url           VARCHAR(500),                     -- 사진 URL
    email               VARCHAR(200),                     -- 이메일
    phone               VARCHAR(50),                      -- 연락처

    -- 권한/등급
    role                VARCHAR(20) NOT NULL DEFAULT 'VIEWER',  -- 등급
    group_id            INTEGER REFERENCES user_groups(id) ON DELETE SET NULL,  -- 소속 그룹 (1:1)

    -- 상태
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,    -- 활성화 여부
    is_locked           BOOLEAN NOT NULL DEFAULT FALSE,   -- 계정 잠금 여부
    lock_reason         VARCHAR(200),                     -- 잠금 사유
    locked_at           TIMESTAMP WITH TIME ZONE,         -- 잠금 시간
    locked_by           INTEGER REFERENCES users(id),     -- 잠금 처리자

    -- 비밀번호 정책
    password_changed_at TIMESTAMP WITH TIME ZONE,         -- 비밀번호 변경일
    password_expires_at TIMESTAMP WITH TIME ZONE,         -- 비밀번호 만료일
    failed_login_count  INTEGER NOT NULL DEFAULT 0,       -- 로그인 실패 횟수

    -- 마지막 활동
    last_login_at       TIMESTAMP WITH TIME ZONE,         -- 마지막 로그인
    last_login_ip       VARCHAR(45),                      -- 마지막 로그인 IP

    -- 타임스탬프
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by          INTEGER REFERENCES users(id),     -- 생성자
    updated_by          INTEGER REFERENCES users(id)      -- 수정자
);

-- 인덱스
CREATE INDEX idx_users_login_id ON users(login_id);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_group_id ON users(group_id);
CREATE INDEX idx_users_department ON users(department);
CREATE INDEX idx_users_is_active ON users(is_active);
```

### 3.2 사용자 등급 (Role)

| 등급 | 코드 | 설명 | 권한 범위 |
|------|------|------|-----------|
| **관리자** | ADMIN | 시스템 전체 관리 | 모든 기능 접근, 사용자/설정 관리 |
| **유지보수자** | MAINTAINER | 장비/시스템 관리 | 장비 설정, 서버 관리, 로그 조회 |
| **운영자** | OPERATOR | 일반 운영 | 이벤트 처리, 카메라 제어, 조치 입력 |
| **조회자** | VIEWER | 조회 전용 | 모니터링, 이벤트 조회 (수정 불가) |
| **게스트** | GUEST | 제한된 접근 | 특정 화면만 조회 가능 |

```python
class EnumUserRole(str, Enum):
    """사용자 등급 (권한 높은 순)"""
    ADMIN = "ADMIN"               # 관리자
    MAINTAINER = "MAINTAINER"     # 유지보수자
    OPERATOR = "OPERATOR"         # 운영자
    VIEWER = "VIEWER"             # 조회자
    GUEST = "GUEST"               # 게스트
```

### 3.3 사용자 API

| Method | Endpoint | 설명 | 권한 |
|--------|----------|------|------|
| GET | `/users` | 사용자 목록 조회 | ADMIN |
| GET | `/users/{id}` | 사용자 상세 조회 | ADMIN |
| POST | `/users` | 사용자 생성 | ADMIN |
| PUT | `/users/{id}` | 사용자 수정 | ADMIN |
| DELETE | `/users/{id}` | 사용자 삭제 | ADMIN |
| POST | `/users/{id}/lock` | 계정 잠금 | ADMIN |
| POST | `/users/{id}/unlock` | 계정 잠금 해제 | ADMIN |
| POST | `/users/{id}/reset-password` | 비밀번호 초기화 | ADMIN |
| GET | `/users/me` | 내 정보 조회 | 로그인 사용자 |
| PUT | `/users/me` | 내 정보 수정 | 로그인 사용자 |
| PUT | `/users/me/password` | 내 비밀번호 변경 | 로그인 사용자 |

### 3.4 사용자 Request/Response

**사용자 생성 Request:**
```json
{
  "login_id": "operator01",
  "password": "SecureP@ss123!",
  "name": "홍길동",
  "department": "경계부대 1중대",
  "position": "상병",
  "employee_number": "21-12345678",
  "photo_url": "/uploads/photos/user_001.jpg",
  "email": "operator01@example.com",
  "phone": "010-1234-5678",
  "role": "OPERATOR",
  "group_id": 1
}
```

**사용자 상세 Response:**
```json
{
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
```

---

## 4. 사용자 그룹 (User Groups)

### 4.1 테이블 스키마

```sql
CREATE TABLE user_groups (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,                -- 그룹명
    description     VARCHAR(500),                         -- 설명

    -- 그룹 권한 (JSONB)
    permissions     JSONB,                                -- 세부 권한 설정

    -- 상태
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,

    -- 타임스탬프
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by      INTEGER REFERENCES users(id),
    updated_by      INTEGER REFERENCES users(id)
);

-- 인덱스
CREATE INDEX idx_user_groups_name ON user_groups(name);
```

> **Note**: 사용자와 그룹은 1:1 관계입니다. 사용자는 하나의 그룹에만 소속될 수 있습니다.
> 사용자-그룹 관계는 `users.group_id` FK로 관리됩니다.

### 4.2 그룹 권한 (Permissions) 구조

#### 4.2.1 모듈 권한 (modules)

UI 화면/기능 단위의 접근 권한입니다. 실제 프론트엔드 메뉴 구조와 대응됩니다.

| 모듈 | 설명 | 권한 옵션 |
|------|------|----------|
| `events` | 이벤트 목록/상세 | view, edit (확인 처리), delete |
| `cameras` | 카메라 영상/제어 | view, edit (설정), control (PTZ) |
| `devices` | 장비 관리 | view, edit (설정 변경) |
| `reports` | 리포트/통계 | view, export (다운로드) |
| `settings` | 시스템 설정 (서버 등록/삭제, 환경설정) | view, edit |
| `users` | 사용자 관리 | view, edit (ADMIN 전용) |

#### 4.2.2 데이터 접근 범위 (device_groups)

접근 가능한 장비 그룹 ID 목록입니다. 카메라, 센서, 컨트롤러 등 모든 Device는 DeviceGroup으로 그룹핑되므로, 이 필드 하나로 전체 장비 접근 범위를 제어합니다.

| 값 | 의미 | 사용 예시 |
|---|------|----------|
| `["*"]` | 모든 장비 그룹 접근 가능 | ADMIN, 전체 관제 운영자 |
| `[1, 2, 3]` | 특정 그룹만 접근 가능 | 1중대 담당자 (해당 구역만) |
| `[]` | 모든 장비 접근 불가 | 조회 전용 사용자 |
| `null` 또는 미설정 | `["*"]`과 동일 (하위 호환) | - |

#### 4.2.3 시간 제한 (time_restriction)

특정 시간대/요일에만 시스템 접근을 허용합니다. 야간 근무조, 주말 근무자 등 구분에 활용합니다.

**allowed_days (허용 요일)**

| 값 | 의미 | 사용 예시 |
|---|------|----------|
| `["*"]` | 모든 요일 접근 가능 | ADMIN, 24시간 관제 운영자 |
| `["MON", "TUE", "WED", "THU", "FRI"]` | 평일만 접근 가능 | 주간 근무자 |
| `["SAT", "SUN"]` | 주말만 접근 가능 | 주말 당직 근무자 |
| `[]` | 모든 요일 접근 불가 | (사용 안함) |

> 요일 코드: `MON`, `TUE`, `WED`, `THU`, `FRI`, `SAT`, `SUN`

**allowed_hours (허용 시간대)**

| 값 | 의미 | 사용 예시 |
|---|------|----------|
| `{"start": "00:00", "end": "23:59"}` | 24시간 접근 가능 | ADMIN, 24시간 관제 |
| `{"start": "08:00", "end": "18:00"}` | 주간 근무 시간 | 일반 운영자 |
| `{"start": "18:00", "end": "06:00"}` | 야간 근무 시간 | 야간 당직 |
| `null` 또는 미설정 | 24시간 접근 가능 | - |

**enabled (제한 활성화)**

| 값 | 의미 |
|---|------|
| `true` | 시간/요일 제한 적용 |
| `false` | 시간/요일 제한 미적용 (24시간/모든 요일 허용) |

#### 4.2.4 전체 구조 예시

```json
{
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
```

> **Note**: `device_groups`로 카메라 포함 모든 장비 접근을 제어합니다. 별도의 `camera_groups`는 불필요합니다.

### 4.3 사용자 그룹 API

| Method | Endpoint | 설명 | 권한 |
|--------|----------|------|------|
| GET | `/user-groups` | 그룹 목록 조회 | ADMIN |
| GET | `/user-groups/{id}` | 그룹 상세 조회 | ADMIN |
| POST | `/user-groups` | 그룹 생성 | ADMIN |
| PUT | `/user-groups/{id}` | 그룹 수정 | ADMIN |
| DELETE | `/user-groups/{id}` | 그룹 삭제 | ADMIN |
| GET | `/user-groups/{id}/users` | 그룹 소속 사용자 목록 | ADMIN |

> **Note**: 사용자의 그룹 변경은 `/users/{id}` PUT API의 `group_id` 필드를 통해 수행합니다.

### 4.4 사용자 그룹 Response

```json
{
  "id": 1,
  "name": "1중대 운영팀",
  "description": "1중대 경계 시스템 운영 담당",
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
```

---

## 5. 사용자 세션 (User Sessions)

### 5.1 테이블 스키마

```sql
CREATE TABLE user_sessions (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- 토큰 정보
    token           VARCHAR(500) NOT NULL UNIQUE,         -- JWT 또는 세션 토큰
    refresh_token   VARCHAR(500),                         -- 리프레시 토큰

    -- 접속 정보
    ip_address      VARCHAR(45) NOT NULL,                 -- 접속 IP (IPv4/IPv6)
    user_agent      VARCHAR(500),                         -- 브라우저/클라이언트 정보
    
    -- 세션 상태
    login_at        TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at      TIMESTAMP WITH TIME ZONE NOT NULL,    -- 만료 시간
    last_activity   TIMESTAMP WITH TIME ZONE,             -- 마지막 활동 시간
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,        -- 활성 여부

    -- 로그아웃 정보
    logged_out_at   TIMESTAMP WITH TIME ZONE,             -- 로그아웃 시간
    logout_reason   VARCHAR(50),                          -- MANUAL, EXPIRED, FORCED, LOCKED
    forced_by       INTEGER REFERENCES users(id)          -- 강제 로그아웃 처리자
);

-- 인덱스
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_token ON user_sessions(token);
CREATE INDEX idx_user_sessions_is_active ON user_sessions(is_active);
CREATE INDEX idx_user_sessions_login_at ON user_sessions(login_at);
CREATE INDEX idx_user_sessions_expires_at ON user_sessions(expires_at);
```

### 5.2 로그아웃 사유 (Logout Reason)

```python
class EnumLogoutReason(str, Enum):
    """로그아웃 사유"""
    MANUAL = "MANUAL"           # 사용자 직접 로그아웃
    EXPIRED = "EXPIRED"         # 세션 만료
    FORCED = "FORCED"           # 관리자 강제 로그아웃
    LOCKED = "LOCKED"           # 계정 잠금으로 인한 로그아웃
    PASSWORD_CHANGED = "PASSWORD_CHANGED"  # 비밀번호 변경
    DUPLICATE = "DUPLICATE"     # 중복 로그인으로 인한 기존 세션 종료
```

### 5.3 사용자 세션 API

| Method | Endpoint | 설명 | 권한 |
|--------|----------|------|------|
| GET | `/user-sessions` | 활성 세션 목록 | ADMIN |
| GET | `/user-sessions/{id}` | 세션 상세 조회 | ADMIN |
| DELETE | `/user-sessions/{id}` | 강제 로그아웃 | ADMIN |
| DELETE | `/user-sessions/user/{user_id}` | 특정 사용자 전체 세션 종료 | ADMIN |
| GET | `/user-sessions/me` | 내 세션 목록 | 로그인 사용자 |
| DELETE | `/user-sessions/me/{id}` | 내 다른 세션 종료 | 로그인 사용자 |

### 5.4 세션 목록 화면 (관리자)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  사용자 세션 관리                                              활성 세션: 15        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │ ☑ │ 사용자      │ 등급    │ 로그인 시간          │ IP 주소        │ 작업    │   │
│  ├───┼─────────────┼─────────┼──────────────────────┼────────────────┼─────────┤   │
│  │ ☐ │ 홍길동      │ 운영자  │ 2026-01-19 08:30:00 │ 192.168.1.100  │ [로그아웃] │   │
│  │   │ operator01  │         │ 2시간 15분 전        │ Chrome/Win     │         │   │
│  ├───┼─────────────┼─────────┼──────────────────────┼────────────────┼─────────┤   │
│  │ ☐ │ 김철수      │ 조회자  │ 2026-01-19 09:45:00 │ 192.168.1.105  │ [로그아웃] │   │
│  │   │ viewer01    │         │ 1시간 00분 전        │ Firefox/Mac    │         │   │
│  ├───┼─────────────┼─────────┼──────────────────────┼────────────────┼─────────┤   │
│  │ ☐ │ 이영희      │ 관리자  │ 2026-01-19 07:00:00 │ 192.168.1.50   │ [로그아웃] │   │
│  │   │ admin01     │         │ 3시간 45분 전        │ Edge/Win       │         │   │
│  └───┴─────────────┴─────────┴──────────────────────┴────────────────┴─────────┘   │
│                                                                                     │
│  [선택 로그아웃]  [전체 로그아웃]  [새로고침]                                         │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 5.5 세션 목록 Response

```json
{
  "total": 15,
  "items": [
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
      "login_at": "2026-01-19T08:30:00+09:00",
      "last_activity": "2026-01-19T10:40:00+09:00",
      "duration_minutes": 135,
      "expires_at": "2026-01-19T20:30:00+09:00",
      "is_active": true
    }
  ]
}
```

---

## 6. 로그인 로그 (User Login Logs)

### 6.1 테이블 스키마

```sql
CREATE TABLE user_login_logs (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER REFERENCES users(id) ON DELETE SET NULL,
    login_id        VARCHAR(50) NOT NULL,                 -- 시도한 로그인 ID (user 삭제되어도 보존)

    -- 행위
    action          VARCHAR(20) NOT NULL,                 -- LOGIN, LOGOUT, REFRESH

    -- 접속 정보
    ip_address      VARCHAR(45) NOT NULL,
    user_agent      VARCHAR(500),

    -- 결과
    result          VARCHAR(20) NOT NULL,                 -- SUCCESS, FAILURE
    failure_reason  VARCHAR(100),                         -- 실패 사유

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

### 6.2 로그인 실패 사유

```python
class EnumLoginFailureReason(str, Enum):
    """로그인 실패 사유"""
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"   # 아이디/비밀번호 불일치
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"             # 계정 잠금
    ACCOUNT_INACTIVE = "ACCOUNT_INACTIVE"         # 비활성화 계정
    PASSWORD_EXPIRED = "PASSWORD_EXPIRED"         # 비밀번호 만료
    IP_BLOCKED = "IP_BLOCKED"                     # IP 차단
    TIME_RESTRICTED = "TIME_RESTRICTED"           # 접속 시간 제한
    MAX_SESSIONS = "MAX_SESSIONS"                 # 최대 세션 수 초과
```

---

## 7. 인증/인가 흐름

### 7.1 로그인 흐름

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│    Client    │       │   GOP API    │       │   Database   │
└──────┬───────┘       └──────┬───────┘       └──────┬───────┘
       │                      │                      │
       │  1. POST /auth/login │                      │
       │  {login_id, password}│                      │
       │─────────────────────▶│                      │
       │                      │  2. 사용자 조회       │
       │                      │─────────────────────▶│
       │                      │◀─────────────────────│
       │                      │                      │
       │                      │  3. 비밀번호 검증     │
       │                      │  4. 계정 상태 확인    │
       │                      │  5. 로그인 로그 기록  │
       │                      │─────────────────────▶│
       │                      │                      │
       │                      │  6. 세션 생성        │
       │                      │  7. JWT 토큰 발급    │
       │                      │─────────────────────▶│
       │                      │                      │
       │  8. Response         │                      │
       │  {access_token,      │                      │
       │   refresh_token,     │                      │
       │   user_info}         │                      │
       │◀─────────────────────│                      │
       │                      │                      │
```

### 7.2 인증 API

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/auth/login` | 로그인 |
| POST | `/auth/logout` | 로그아웃 |
| POST | `/auth/refresh` | 토큰 갱신 |
| GET | `/auth/me` | 현재 사용자 정보 |

### 7.3 로그인 Response

```json
{
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
}
```

---

## 8. 보안 정책

### 8.1 비밀번호 정책

| 항목 | 기본값 | 설명 |
|------|--------|------|
| 최소 길이 | 8자 | 비밀번호 최소 길이 |
| 복잡도 | 필수 | 대/소문자, 숫자, 특수문자 포함 |
| 만료 기간 | 90일 | 비밀번호 변경 주기 |
| 이전 비밀번호 재사용 금지 | 5회 | 최근 N개 비밀번호 재사용 불가 |
| 초기 비밀번호 변경 | 필수 | 최초 로그인 시 변경 강제 |

### 8.2 계정 잠금 정책

| 항목 | 기본값 | 설명 |
|------|--------|------|
| 로그인 실패 허용 횟수 | 5회 | 연속 실패 시 잠금 |
| 자동 잠금 해제 시간 | 30분 | 일정 시간 후 자동 해제 |
| 관리자 수동 잠금 | 가능 | 관리자가 직접 잠금 처리 |

### 8.3 세션 정책

| 항목 | 기본값 | 설명 |
|------|--------|------|
| 세션 유효 시간 | 12시간 | Access Token 만료 시간 |
| 리프레시 토큰 유효 시간 | 7일 | Refresh Token 만료 시간 |
| 동시 세션 수 | 3개 | 사용자당 최대 동시 로그인 |
| 유휴 세션 타임아웃 | 30분 | 활동 없을 시 자동 로그아웃 |

---

## 9. 시스템 연동

### 9.1 SystemEvent 연동

사용자 관련 이벤트는 SystemEvent 테이블에 기록:

```json
{
  "type_event": "USER_LOGIN",
  "severity": "INFO",
  "title": "사용자 로그인",
  "message": "operator01(홍길동)이 로그인했습니다.",
  "detail": {
    "user_id": 1,
    "login_id": "operator01",
    "ip_address": "192.168.1.100"
  },
  "source": "AUTH_SERVICE"
}
```

### 9.2 관련 SystemEvent 유형

- `USER_LOGIN`: 사용자 로그인
- `USER_LOGOUT`: 사용자 로그아웃
- `USER_LOGIN_FAILED`: 로그인 실패
- `USER_LOCKED`: 계정 잠금
- `USER_UNLOCKED`: 계정 잠금 해제
- `USER_CREATED`: 사용자 생성
- `USER_UPDATED`: 사용자 수정
- `USER_DELETED`: 사용자 삭제
- `SESSION_FORCED_LOGOUT`: 강제 로그아웃

---

## 10. 변경 이력

| 버전 | 일자 | 작성자 | 변경 내용 |
|------|------|--------|-----------|
| v1.0 | 2026-01-19 | - | 초안 작성 |
| v1.1 | 2026-01-19 | - | User-Group 1:1 관계 정립, permissions 구조 정리 (camera_groups 제거, device_groups 와일드카드 `["*"]` 지원, allowed_days 와일드카드 `["*"]` 지원, 모듈 설명 추가, dashboard/maps 모듈 제거) |