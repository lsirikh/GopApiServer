# PRD: UserSession API 개선 및 Account API 문서 동기화

## 1. 개요

### 1.1 목적
UserSession API의 응답 형식 개선, 불필요한 필드 정리, 그리고 GOP_Restful_Api_연동설계.md 문서와 실제 코드 간의 불일치를 해결한다.

### 1.2 범위
- UserSession 모델에서 미사용 필드 제거
- 로그인 시 클라이언트 정보(IP, User-Agent) 저장 기능 추가
- API 응답에서 사용자 식별 정보 개선 (user_id → login_id, role)
- **[NEW] GOP_Restful_Api_연동설계.md 문서와 실제 코드 동기화**
- **[NEW] Account 관련 API의 created_at/updated_at 필드 일관성 확보**

### 1.3 문서 버전
| 버전 | 날짜 | 작성자 | 변경 내용 |
|-----|------|--------|----------|
| 1.0 | 2026-01-20 | System | 초안 작성 |
| 1.1 | 2026-01-20 | System | 문서 동기화 요구사항 추가 |
| 1.2 | 2026-01-20 | System | UserSession 필드명 표준화 (login_at→created_at, last_activity→updated_at) |

---

## 2. 현재 상태 분석

### 2.1 현재 UserSession 모델 (app/models/user.py)
```python
class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("account_users.id"))
    token = Column(String(500))
    refresh_token = Column(String(500))
    ip_address = Column(String(45))      # ✓ 유지 (현재 null로 저장됨)
    user_agent = Column(String(500))     # ✓ 유지 (현재 null로 저장됨)
    device_type = Column(String(50))     # ✗ 미사용 - 제거 대상
    location = Column(String(255))       # ✗ 미사용 - 제거 대상
    login_at = Column(DateTime)          # ✗ created_at으로 변경 대상
    expires_at = Column(DateTime)
    last_activity = Column(DateTime)     # ✗ updated_at으로 변경 대상
    logged_out_at = Column(DateTime)
    is_active = Column(Boolean)
    logout_reason = Column(String(50))
    forced_by = Column(Integer)
```

### 2.2 현재 API 응답 (UserSessionResponse)
```json
{
  "id": 1,
  "user_id": 5,              // 문제: 숫자만으로는 사용자 식별 어려움
  "ip_address": null,        // 문제: 항상 null
  "user_agent": null,        // 문제: 항상 null
  "device_type": null,       // 문제: 미사용 필드
  "location": null,          // 문제: 미사용 필드
  "login_at": "2026-01-20T10:00:00+09:00",       // 문제: created_at으로 변경 필요
  "expires_at": "2026-01-20T18:00:00+09:00",
  "last_activity": "2026-01-20T10:00:00+09:00",  // 문제: updated_at으로 변경 필요
  "is_active": true,
  "logout_reason": null,
  "logged_out_at": null
}
```

### 2.3 문제점 요약
| 문제 | 설명 | 영향 |
|-----|------|------|
| 미사용 필드 | `device_type`, `location` 필드가 정의되어 있지만 어디서도 값이 설정되지 않음 | DB 스키마 불필요 필드 |
| 클라이언트 정보 미저장 | 로그인 시 `ip_address`, `user_agent`가 저장되지 않음 | 세션 추적 불가 |
| 사용자 식별 어려움 | API 응답에 `user_id`만 있어 세션 목록에서 사용자 식별이 어려움 | 관리 화면 UX 저하 |
| 필드명 비일관성 | `login_at`, `last_activity`가 다른 모델의 `created_at`, `updated_at` 패턴과 불일치 | 스키마 일관성 저하 |

---

## 3. 문서-코드 불일치 분석 (v1.1 추가)

### 3.1 GOP_Restful_Api_연동설계.md vs 실제 코드 비교

#### 3.1.1 UserSession API 불일치

**문서 (9.5.2 GET `/api/user-sessions`)**:
```json
{
  "id": 101,
  "user_id": 1,
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "login_at": "2026-01-19T08:30:00+09:00",
  "expires_at": "2026-01-19T20:30:00+09:00",
  "is_active": true
}
```

**실제 코드 (UserSessionResponse 스키마)**:
```json
{
  "id": 101,
  "user_id": 1,
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "device_type": null,           // 문서에 누락
  "location": null,              // 문서에 누락
  "login_at": "2026-01-19T08:30:00+09:00",
  "expires_at": "2026-01-19T20:30:00+09:00",
  "last_activity": "...",        // 문서에 누락
  "is_active": true,
  "logout_reason": null,         // 문서에 누락
  "logged_out_at": null          // 문서에 누락
}
```

**누락된 필드**:
| 필드 | 설명 | 조치 |
|-----|------|------|
| `device_type` | 미사용 | 코드에서 제거 예정 → 문서 반영 불필요 |
| `location` | 미사용 | 코드에서 제거 예정 → 문서 반영 불필요 |
| `last_activity` | 마지막 활동 시간 | 문서에 추가 필요 |
| `logout_reason` | 로그아웃 사유 | 문서에 추가 필요 |
| `logged_out_at` | 로그아웃 시간 | 문서에 추가 필요 |

#### 3.1.2 Users API 불일치

**문서 (9.3.2 GET `/api/users`)**:
```json
{
  "id": 1,
  "login_id": "operator01",
  "name": "홍길동",
  "department": "경계부대 1중대",
  "role": "OPERATOR",
  "group_id": 1,
  "is_active": true,
  "is_locked": false,
  "created_at": "2026-01-01T09:00:00+09:00"
}
```

**실제 코드 (AccountUserResponse 스키마)**:
```json
{
  "id": 1,
  "login_id": "operator01",
  "name": "홍길동",
  "email": "operator01@gop.mil.kr",         // 문서에 누락
  "department": "경계부대 1중대",
  "position": "상병",                        // 문서에 누락
  "employee_number": "21-12345678",         // 문서에 누락
  "photo_url": null,                        // 문서에 누락
  "phone": "010-1234-5678",                 // 문서에 누락
  "role": "OPERATOR",
  "group_id": 1,
  "is_active": true,
  "is_locked": false,
  "lock_reason": null,                      // 문서에 누락
  "locked_at": null,                        // 문서에 누락
  "last_login_at": "2026-01-19T09:00:00+09:00",  // 문서에 누락
  "last_login_ip": "192.168.1.100",         // 문서에 누락
  "created_at": "2026-01-01T09:00:00+09:00",
  "updated_at": "2026-01-15T10:00:00+09:00" // 문서에 누락 ⚠️
}
```

**누락된 필드**:
| 필드 | 설명 | 문서 반영 |
|-----|------|---------|
| `email` | 이메일 | 추가 필요 |
| `position` | 직책 | 추가 필요 |
| `employee_number` | 군번/사번 | 추가 필요 |
| `photo_url` | 프로필 사진 URL | 추가 필요 |
| `phone` | 전화번호 | 추가 필요 |
| `lock_reason` | 잠금 사유 | 추가 필요 |
| `locked_at` | 잠금 시간 | 추가 필요 |
| `last_login_at` | 마지막 로그인 시간 | 추가 필요 |
| `last_login_ip` | 마지막 로그인 IP | 추가 필요 |
| `updated_at` | 수정 시간 | **추가 필요 ⚠️** |

#### 3.1.3 Users POST 응답 불일치

**문서 (9.3.3 POST `/api/users`)**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "login_id": "operator01",
    "name": "홍길동",
    "role": "OPERATOR"
  }
}
```

**권장 수정**: 전체 AccountUserResponse 반환으로 변경

#### 3.1.4 UserGroup API 불일치

**문서 (9.4.2 POST `/api/user-groups`)**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "1중대 운영팀",
    "is_active": true
  }
}
```

**실제 코드 (UserGroupResponse 스키마)**:
```json
{
  "id": 1,
  "name": "1중대 운영팀",
  "description": "1중대 경계 시스템 운영 담당",  // 문서에 누락
  "permissions": {...},                         // 문서에 누락
  "is_active": true,
  "user_count": 5,                              // 문서에 누락
  "created_at": "2026-01-01T09:00:00+09:00",    // 문서에 누락
  "updated_at": "2026-01-15T10:00:00+09:00"     // 문서에 누락 ⚠️
}
```

### 3.2 created_at/updated_at 일관성 문제

#### 3.2.1 기본 스키마 패턴 (다른 API 참조)
대부분의 API (Device, Camera, Event 등)는 `created_at`, `updated_at`을 포함:
```json
{
  "id": 1,
  "name": "...",
  "created_at": "2026-01-01T09:00:00+09:00",
  "updated_at": "2026-01-15T10:00:00+09:00"
}
```

#### 3.2.2 Account API 현황
| API | created_at | updated_at | 상태 |
|-----|-----------|-----------|------|
| AccountUser | ✓ 코드 | ✗ 문서 누락 | 문서 수정 필요 |
| UserGroup | ✓ 코드 | ✗ 문서 누락 | 문서 수정 필요 |
| UserSession | ✗ (login_at 사용) | ✗ (last_activity 사용) | **필드명 변경 필요** |
| UserLoginLog | ✓ 코드 | ✗ 해당없음 (로그는 생성만) | 정상 |

#### 3.2.3 UserSession 필드명 표준화 (v1.2 변경)
기존 필드명이 다른 모델과 일관성이 없으므로 표준 패턴으로 변경:

| 변경 전 | 변경 후 | 설명 |
|--------|--------|------|
| `login_at` | `created_at` | 세션 생성 시간 (= 로그인 시간) |
| `last_activity` | `updated_at` | 마지막 활동/수정 시간 |

> **참고**: 의미론적으로 `login_at`이 더 명확하지만, 전체 스키마 일관성을 위해 `created_at`으로 통일

---

## 4. 개선 요구사항

### 4.1 DB 모델 변경

#### 4.1.1 제거할 필드
```python
# 제거 대상 (migration 필요)
device_type = Column(String(50), nullable=True)   # 삭제
location = Column(String(255), nullable=True)     # 삭제
```

#### 4.1.2 Migration 스크립트
```sql
-- Alembic migration
-- 1. 미사용 컬럼 제거
ALTER TABLE user_sessions DROP COLUMN device_type;
ALTER TABLE user_sessions DROP COLUMN location;

-- 2. 컬럼명 변경 (표준 패턴 적용)
ALTER TABLE user_sessions RENAME COLUMN login_at TO created_at;
ALTER TABLE user_sessions RENAME COLUMN last_activity TO updated_at;
```

### 4.2 로그인 시 클라이언트 정보 저장

#### 4.2.1 auth.py 수정 (login 함수)
```python
@router.post("/login")
async def login(
    login_data: AccountLoginRequest,
    request: Request,  # 추가: Request 객체 주입
    db: Session = Depends(get_db)
):
    # ... 인증 로직 ...

    # ip_address와 user_agent 추출
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    # UserSession 생성 시 클라이언트 정보 포함
    session = UserSession(
        user_id=user.id,
        token=access_token,
        refresh_token=refresh_token,
        ip_address=client_ip,        # 추가
        user_agent=user_agent,       # 추가
        expires_at=datetime.now(settings.tz) + timedelta(hours=settings.JWT_EXPIRATION_HOURS),
        is_active=True
    )

    # UserLoginLog에도 클라이언트 정보 저장
    login_log = UserLoginLog(
        user_id=user.id,
        login_id=user.login_id,
        action="LOGIN",
        result="SUCCESS",
        ip_address=client_ip,        # 추가
        user_agent=user_agent        # 추가
    )
```

### 4.3 API 응답 형식 개선

#### 4.3.1 목표 응답 형식 (UserSession)
```json
{
  "id": 1,
  "login_id": "operator01",
  "role": "OPERATOR",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "expires_at": "2026-01-20T18:00:00+09:00",
  "is_active": true,
  "logout_reason": null,
  "logged_out_at": null,
  "created_at": "2026-01-20T10:00:00+09:00",
  "updated_at": "2026-01-20T10:00:00+09:00"
}
```

#### 4.3.2 스키마 변경 (app/schemas/user.py)
```python
class UserSessionResponse(BaseModel):
    """Schema for user session response"""
    id: int
    login_id: str                          # JOIN으로 가져옴
    role: str                              # JOIN으로 가져옴
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    expires_at: datetime
    is_active: bool
    logout_reason: Optional[str] = None
    logged_out_at: Optional[datetime] = None
    created_at: datetime                   # login_at 대체
    updated_at: Optional[datetime] = None  # last_activity 대체

    model_config = {"from_attributes": True}
```

#### 4.3.3 라우터 변경 (app/routers/user_sessions.py)
```python
@router.get("")
async def get_user_sessions(...):
    # JOIN으로 사용자 정보 함께 조회
    query = db.query(UserSession, AccountUser).join(
        AccountUser, UserSession.user_id == AccountUser.id
    )

    # 결과 변환
    results = []
    for session, user in query.all():
        session_data = {
            "id": session.id,
            "login_id": user.login_id,
            "role": user.role,
            "ip_address": session.ip_address,
            "user_agent": session.user_agent,
            "expires_at": session.expires_at,
            "is_active": session.is_active,
            "logout_reason": session.logout_reason,
            "logged_out_at": session.logged_out_at,
            "created_at": session.created_at,
            "updated_at": session.updated_at
        }
        results.append(session_data)

    return {"success": True, "data": results}
```

---

## 5. 문서 동기화 계획 (v1.1 추가)

### 5.1 GOP_Restful_Api_연동설계.md 수정 항목

#### 5.1.1 Section 9.5.2 GET `/api/user-sessions` 수정
**변경 전**:
```json
{
  "id": 101,
  "user_id": 1,
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "login_at": "2026-01-19T08:30:00+09:00",
  "expires_at": "2026-01-19T20:30:00+09:00",
  "is_active": true
}
```

**변경 후**:
```json
{
  "success": true,
  "data": [
    {
      "id": 101,
      "login_id": "operator01",
      "role": "OPERATOR",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0",
      "expires_at": "2026-01-19T20:30:00+09:00",
      "is_active": true,
      "logout_reason": null,
      "logged_out_at": null,
      "created_at": "2026-01-19T08:30:00+09:00",
      "updated_at": "2026-01-19T10:15:00+09:00"
    }
  ]
}
```

> **필드 순서 규칙**: id → 식별자(login_id, role) → 데이터 필드 → 상태 필드(is_active) → 로그아웃 정보 → created_at → updated_at

#### 5.1.2 Section 9.3.2 GET `/api/users` 수정
**추가할 필드**:
- `email`, `position`, `employee_number`, `photo_url`, `phone`
- `lock_reason`, `locked_at`, `last_login_at`, `last_login_ip`
- `updated_at` ⚠️ (기본 스키마 패턴 준수)

#### 5.1.3 Section 9.3.3 POST `/api/users` 수정
**변경 전**: 최소 필드만 반환
```json
{
  "id": 1,
  "login_id": "operator01",
  "name": "홍길동",
  "role": "OPERATOR"
}
```

**변경 후**: 전체 AccountUserResponse 반환
```json
{
  "success": true,
  "data": {
    "id": 1,
    "login_id": "operator01",
    "name": "홍길동",
    "email": "operator01@gop.mil.kr",
    "department": "경계부대 1중대",
    "position": "상병",
    "employee_number": null,
    "photo_url": null,
    "phone": null,
    "role": "OPERATOR",
    "group_id": 1,
    "is_active": true,
    "is_locked": false,
    "lock_reason": null,
    "locked_at": null,
    "last_login_at": null,
    "last_login_ip": null,
    "created_at": "2026-01-20T09:00:00+09:00",
    "updated_at": "2026-01-20T09:00:00+09:00"
  }
}
```

> **필드 순서 규칙**: id → 식별자(login_id) → 개인정보 → 역할/그룹 → 상태 필드 → 잠금 정보 → 로그인 정보 → created_at → updated_at

#### 5.1.4 Section 9.4 UserGroup API 수정
**추가할 필드**:
- `description`, `permissions`, `user_count`
- `created_at`, `updated_at` ⚠️ (기본 스키마 패턴 준수)

---

## 6. 구현 계획

### 6.1 Phase 1: DB 스키마 정리 (Breaking Change)
| 단계 | 작업 | 파일 |
|-----|------|------|
| 1-1 | `device_type`, `location` 컬럼 제거 | app/models/user.py |
| 1-2 | `login_at` → `created_at` 컬럼명 변경 | app/models/user.py |
| 1-3 | `last_activity` → `updated_at` 컬럼명 변경 | app/models/user.py |
| 1-4 | Migration 스크립트 작성 및 실행 | alembic/versions/xxx.py |
| 1-5 | 스키마에서 필드 변경 반영 | app/schemas/user.py |

### 6.2 Phase 2: 클라이언트 정보 저장
| 단계 | 작업 | 파일 |
|-----|------|------|
| 2-1 | login 함수에 Request 의존성 추가 | app/routers/auth.py |
| 2-2 | ip_address, user_agent 추출 및 저장 | app/routers/auth.py |
| 2-3 | UserLoginLog에도 동일하게 저장 | app/routers/auth.py |

### 6.3 Phase 3: API 응답 개선
| 단계 | 작업 | 파일 |
|-----|------|------|
| 3-1 | UserSessionResponse 스키마 수정 | app/schemas/user.py |
| 3-2 | user_sessions.py 라우터에서 JOIN 적용 | app/routers/user_sessions.py |
| 3-3 | 모든 세션 관련 엔드포인트 업데이트 | app/routers/user_sessions.py |

### 6.4 Phase 4: 테스트 업데이트
| 단계 | 작업 | 파일 |
|-----|------|------|
| 4-1 | 기존 테스트 수정 (필드 변경 반영) | tests/test_user_sessions.py |
| 4-2 | ip_address, user_agent 저장 테스트 추가 | tests/test_auth.py |
| 4-3 | JOIN 응답 테스트 추가 | tests/test_user_sessions.py |

### 6.5 Phase 5: 문서 동기화 (v1.1 추가)
| 단계 | 작업 | 파일 |
|-----|------|------|
| 5-1 | UserSession API 응답 업데이트 | GOP_Restful_Api_연동설계.md §9.5 |
| 5-2 | Users API 응답 업데이트 (누락 필드 추가) | GOP_Restful_Api_연동설계.md §9.3 |
| 5-3 | UserGroup API 응답 업데이트 | GOP_Restful_Api_연동설계.md §9.4 |
| 5-4 | created_at/updated_at 일관성 검토 | GOP_Restful_Api_연동설계.md 전체 |

---

## 7. 영향 분석

### 7.1 Breaking Changes
| 항목 | 변경 전 | 변경 후 | 영향 |
|-----|--------|--------|------|
| user_id 필드 | 응답에 포함 | 응답에서 제거 | 클라이언트 코드 수정 필요 |
| login_id 필드 | 없음 | 응답에 추가 | 신규 필드 |
| role 필드 | 없음 | 응답에 추가 | 신규 필드 |
| device_type 필드 | 응답에 포함 (null) | 응답에서 제거 | 클라이언트 코드 수정 필요 |
| location 필드 | 응답에 포함 (null) | 응답에서 제거 | 클라이언트 코드 수정 필요 |
| login_at 필드 | 응답에 포함 | `created_at`으로 변경 | 클라이언트 코드 수정 필요 |
| last_activity 필드 | 응답에 포함 | `updated_at`으로 변경 | 클라이언트 코드 수정 필요 |

### 7.2 영향받는 API 엔드포인트
- `GET /api/user-sessions` - 세션 목록 조회
- `GET /api/user-sessions/{session_id}` - 세션 상세 조회
- `GET /api/user-sessions/me` - 내 세션 목록 조회
- `DELETE /api/user-sessions/{session_id}` - 세션 강제 로그아웃 (응답은 변경 없음)
- `DELETE /api/user-sessions/user/{user_id}` - 사용자 전체 세션 로그아웃 (응답은 변경 없음)
- `DELETE /api/user-sessions/me/{session_id}` - 내 세션 종료 (응답은 변경 없음)

### 7.3 영향받는 화면 (프론트엔드)
- 세션 관리 화면: 사용자 식별 필드 변경 (user_id → login_id + role)

---

## 8. 테스트 요구사항

### 8.1 단위 테스트
```python
def test_login_stores_client_info():
    """로그인 시 ip_address와 user_agent가 저장되는지 확인"""

def test_session_response_includes_login_id_and_role():
    """세션 응답에 login_id와 role이 포함되는지 확인"""

def test_session_response_excludes_deprecated_fields():
    """세션 응답에 device_type, location이 없는지 확인"""
```

### 8.2 통합 테스트
```python
def test_session_list_with_user_info():
    """세션 목록 조회 시 사용자 정보가 JOIN되어 반환되는지 확인"""

def test_my_sessions_with_user_info():
    """내 세션 목록 조회 시 사용자 정보가 포함되는지 확인"""
```

---

## 9. 롤백 계획

### 9.1 DB 롤백 (Phase 1)
```sql
-- 삭제된 컬럼 복원 (데이터 손실)
ALTER TABLE user_sessions ADD COLUMN device_type VARCHAR(50);
ALTER TABLE user_sessions ADD COLUMN location VARCHAR(255);
```

### 9.2 코드 롤백
- Git revert를 통한 코드 원복
- 스키마, 라우터, 테스트 파일 모두 원복 필요

---

## 10. 체크리스트

### 10.1 구현 전 확인
- [ ] 기존 API를 사용하는 클라이언트 파악
- [ ] Breaking change 공지 필요 여부 확인
- [ ] DB 백업 완료

### 10.2 구현 중 확인
- [ ] Migration 스크립트 테스트 (dev 환경)
- [ ] API 응답 형식 변경 테스트
- [ ] 기존 테스트 수정 완료

### 10.3 구현 후 확인
- [ ] 모든 테스트 통과
- [ ] Swagger 문서 업데이트 확인
- [ ] 실제 로그인 시 ip_address, user_agent 저장 확인
- [ ] 세션 목록에서 login_id, role 표시 확인

### 10.4 문서 동기화 확인 (v1.1 추가)
- [ ] UserSession API 응답 예제 업데이트 완료
- [ ] Users API 응답 예제 업데이트 완료 (전체 필드)
- [ ] UserGroup API 응답 예제 업데이트 완료 (전체 필드)
- [ ] created_at/updated_at 일관성 확인

---

## 11. 부록

### 11.1 관련 문서
- PRD_Account_Design.md - AccountUser 모델 설계
- AUDIT_LOG_SCREEN_DESIGN.md - 감사 로그 화면 설계
- GOP_Restful_Api_연동설계.md - API 연동 설계 문서

### 11.2 관련 코드
- app/models/user.py - UserSession 모델
- app/schemas/user.py - UserSessionResponse 스키마
- app/routers/user_sessions.py - 세션 API 라우터
- app/routers/auth.py - 로그인/로그아웃 API

### 11.3 필드 매핑 테이블 (v1.1 추가)

#### 필드 순서 표준 규칙
모든 API Response는 다음 순서를 따름:
1. **id** - 기본 키
2. **식별자** - login_id, name 등 엔티티 식별 정보
3. **데이터 필드** - 핵심 비즈니스 데이터
4. **상태 필드** - is_active, is_locked 등
5. **부가 정보** - 로그아웃 사유, 잠금 사유 등
6. **created_at** - 생성 시간
7. **updated_at** - 수정 시간

#### AccountUserResponse 전체 필드
> **순서**: id → 식별자 → 개인정보 → 역할/그룹 → 상태 → 잠금 → 로그인 → timestamps

| # | 필드 | 타입 | 필수 | 설명 | 비밀성 |
|---|-----|------|------|------|--------|
| 1 | id | int | Y | 사용자 ID | 공개 |
| 2 | login_id | str | Y | 로그인 ID | 공개 |
| 3 | name | str | Y | 사용자 이름 | 공개 |
| 4 | email | str | N | 이메일 | 공개 |
| 5 | department | str | N | 부서 | 공개 |
| 6 | position | str | N | 직책 | 공개 |
| 7 | employee_number | str | N | 군번/사번 | 공개 |
| 8 | photo_url | str | N | 프로필 사진 URL | 공개 |
| 9 | phone | str | N | 전화번호 | 공개 |
| 10 | role | str | Y | 사용자 역할 | 공개 |
| 11 | group_id | int | N | 소속 그룹 ID | 공개 |
| 12 | is_active | bool | Y | 활성 상태 | 공개 |
| 13 | is_locked | bool | Y | 잠금 상태 | 공개 |
| 14 | lock_reason | str | N | 잠금 사유 | 공개 |
| 15 | locked_at | datetime | N | 잠금 시간 | 공개 |
| 16 | last_login_at | datetime | N | 마지막 로그인 시간 | 공개 |
| 17 | last_login_ip | str | N | 마지막 로그인 IP | 공개 |
| 18 | created_at | datetime | Y | 생성 시간 | 공개 |
| 19 | updated_at | datetime | Y | 수정 시간 | 공개 |
| - | password_hash | str | - | 비밀번호 해시 | **비공개** ⚠️ |

#### UserSessionResponse 전체 필드 (개선 후)
> **순서**: id → 식별자(login_id, role) → 접속정보 → 상태 → 로그아웃 → timestamps

| # | 필드 | 타입 | 필수 | 설명 | 비밀성 |
|---|-----|------|------|------|--------|
| 1 | id | int | Y | 세션 ID | 공개 |
| 2 | login_id | str | Y | 사용자 로그인 ID (JOIN) | 공개 |
| 3 | role | str | Y | 사용자 역할 (JOIN) | 공개 |
| 4 | ip_address | str | N | 접속 IP 주소 | 공개 |
| 5 | user_agent | str | N | 브라우저 정보 | 공개 |
| 6 | expires_at | datetime | Y | 만료 시간 | 공개 |
| 7 | is_active | bool | Y | 활성 상태 | 공개 |
| 8 | logout_reason | str | N | 로그아웃 사유 | 공개 |
| 9 | logged_out_at | datetime | N | 로그아웃 시간 | 공개 |
| 10 | created_at | datetime | Y | 생성 시간 (= 로그인 시간) | 공개 |
| 11 | updated_at | datetime | N | 수정 시간 (= 마지막 활동 시간) | 공개 |
| - | token | str | - | 액세스 토큰 | **비공개** ⚠️ |
| - | refresh_token | str | - | 리프레시 토큰 | **비공개** ⚠️ |

#### UserGroupResponse 전체 필드
> **순서**: id → 기본정보 → 권한 → 상태 → 통계 → timestamps

| # | 필드 | 타입 | 필수 | 설명 | 비밀성 |
|---|-----|------|------|------|--------|
| 1 | id | int | Y | 그룹 ID | 공개 |
| 2 | name | str | Y | 그룹 이름 | 공개 |
| 3 | description | str | N | 그룹 설명 | 공개 |
| 4 | permissions | json | N | 권한 설정 | 공개 |
| 5 | is_active | bool | Y | 활성 상태 | 공개 |
| 6 | user_count | int | N | 소속 사용자 수 | 공개 |
| 7 | created_at | datetime | Y | 생성 시간 | 공개 |
| 8 | updated_at | datetime | Y | 수정 시간 | 공개 |
