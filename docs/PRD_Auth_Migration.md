# 인증 체계 마이그레이션 PRD

**문서 버전**: v1.0
**작성일**: 2026-01-19
**상태**: Planning

---

## 1. 개요

### 1.1 목적

기존 OAuth2PasswordBearer 기반 레거시 인증 체계를 새로운 AccountUser 기반 JSON 인증 체계로 마이그레이션한다.

### 1.2 현재 상태

```
┌─────────────────────────────────────────────────────────────────────┐
│                        현재 인증 체계 (AS-IS)                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  [레거시 체계]                          [신규 체계]                   │
│  ├─ Model: User                        ├─ Model: AccountUser        │
│  ├─ Login: /api/auth/login/oauth2      ├─ Login: /api/auth/login    │
│  ├─ Format: x-www-form-urlencoded      ├─ Format: application/json  │
│  ├─ Swagger: OAuth2PasswordBearer      ├─ Swagger: (미연동)          │
│  └─ Dependency: get_current_user       └─ Dependency: get_current_account_user
│                                                                     │
│  [문제점]                                                            │
│  1. Swagger UI에서 OAuth2 로그인 폼만 표시됨                          │
│  2. 새로운 AccountUser 인증이 Swagger에서 불편함                      │
│  3. 두 가지 인증 체계가 혼재되어 혼란 유발                            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.3 목표 상태

```
┌─────────────────────────────────────────────────────────────────────┐
│                        목표 인증 체계 (TO-BE)                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  [통합 체계]                                                         │
│  ├─ Model: AccountUser (단일)                                       │
│  ├─ Login: /api/auth/login (JSON 기반)                              │
│  ├─ Swagger: HTTP Bearer Token 방식                                 │
│  └─ Dependency: get_current_account_user (단일)                     │
│                                                                     │
│  [레거시 유지 (호환성)]                                               │
│  └─ /api/auth/login/oauth2 → Deprecated 표시, 향후 제거 예정         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. 현재 코드 분석

### 2.1 레거시 인증 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `app/utils/auth.py` | OAuth2PasswordBearer 스키마 정의 | ✓ 수정 |
| `app/routers/auth.py` | /login/oauth2 엔드포인트 | ✓ 수정 |
| `app/models/user.py` | User (레거시), AccountUser (신규) | 유지 |
| `app/dependencies.py` | get_current_user, get_current_account_user | ✓ 수정 |

### 2.2 현재 OAuth2 스키마 (app/utils/auth.py)

```python
# 현재 코드
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login/oauth2")
```

이 설정으로 인해 Swagger UI에 OAuth2PasswordBearer 인증 폼이 표시됨.

### 2.3 Swagger UI 현재 모습

```
┌─────────────────────────────────────────────────────────────────────┐
│  Available authorizations                                      ✕    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  OAuth2PasswordBearer (OAuth2, password)                            │
│                                                                     │
│  Token URL: /api/auth/login/oauth2                                  │
│  Flow: password                                                     │
│                                                                     │
│  username: [________________]                                       │
│  password: [________________]                                       │
│                                                                     │
│  Client credentials location: [Authorization header ▼]              │
│                                                                     │
│  client_id: [________________]                                      │
│  client_secret: [________________]                                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**문제점**:
- OAuth2 폼 기반으로 불필요한 필드(client_id, client_secret) 표시
- 새로운 JSON 기반 로그인과 맞지 않음
- Bearer Token 직접 입력이 불편함

---

## 3. 변경 사항

### 3.1 Swagger UI 인증 방식 변경

**Before**: OAuth2PasswordBearer (폼 기반)
**After**: HTTPBearer (토큰 직접 입력)

```
┌─────────────────────────────────────────────────────────────────────┐
│  Available authorizations                                      ✕    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  HTTPBearer (http, Bearer)                                          │
│                                                                     │
│  Bearer authentication with JWT token.                              │
│  Login via POST /api/auth/login to get token.                       │
│                                                                     │
│  Value: [Bearer eyJhbGciOiJIUzI1NiIs...]                           │
│                                                                     │
│                                        [Authorize]  [Close]         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 코드 변경 상세

#### 3.2.1 app/utils/auth.py 수정

```python
# Before
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login/oauth2")

# After
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# HTTP Bearer 스키마 (Swagger UI용)
bearer_scheme = HTTPBearer(
    scheme_name="HTTPBearer",
    description="Bearer authentication with JWT token. Login via POST /api/auth/login to get token.",
    auto_error=False  # 토큰 없을 때 자동 에러 방지
)

# 레거시 호환용 (Deprecated)
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login/oauth2",
    auto_error=False
)
```

#### 3.2.2 app/dependencies.py 수정

```python
# Before
async def get_current_account_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> AccountUser:
    ...

# After
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

bearer_scheme = HTTPBearer(auto_error=False)

async def get_current_account_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> AccountUser:
    """
    현재 로그인한 AccountUser 반환

    Swagger UI에서 "Authorize" 버튼으로 Bearer 토큰 입력 가능
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = credentials.credentials
    # 기존 토큰 검증 로직...
```

#### 3.2.3 app/routers/auth.py 수정

```python
# /login/oauth2 엔드포인트에 Deprecated 표시 추가

@router.post("/login/oauth2", deprecated=True)
async def login_oauth2(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    [DEPRECATED] OAuth2 폼 기반 로그인

    이 엔드포인트는 레거시 호환성을 위해 유지됩니다.
    새로운 클라이언트는 POST /api/auth/login 을 사용하세요.

    향후 버전에서 제거될 예정입니다.
    """
    ...
```

### 3.3 Swagger 문서 개선

#### main.py 또는 설정 파일

```python
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="GOP API Server",
    description="""
## 인증 방법

1. **로그인**: `POST /api/auth/login` 호출
   ```json
   {
     "login_id": "admin",
     "password": "admin123"
   }
   ```

2. **토큰 획득**: Response에서 `access_token` 복사

3. **Swagger 인증**:
   - 우측 상단 [Authorize] 버튼 클릭
   - `Bearer {access_token}` 입력
   - [Authorize] 클릭

## API 그룹

- **Auth**: 인증 관련 (로그인, 로그아웃, 토큰 갱신)
- **Users**: 사용자 관리 (ADMIN 전용)
- **User Groups**: 사용자 그룹 관리 (ADMIN 전용)
- **User Sessions**: 세션 관리 (ADMIN 전용)
    """,
    version="2.9"
)
```

---

## 4. 마이그레이션 단계

### Phase 1: Swagger UI 개선 (즉시)

| 단계 | 작업 | 파일 |
|------|------|------|
| 1-1 | HTTPBearer 스키마 추가 | app/utils/auth.py |
| 1-2 | get_current_account_user 의존성 수정 | app/dependencies.py |
| 1-3 | Swagger 설명 개선 | app/main.py |
| 1-4 | 테스트 | - |

### Phase 2: 레거시 정리 (선택적)

| 단계 | 작업 | 파일 |
|------|------|------|
| 2-1 | /login/oauth2 에 deprecated=True 추가 | app/routers/auth.py |
| 2-2 | 레거시 User 모델 사용처 확인 | 전체 검색 |
| 2-3 | get_current_user → get_current_account_user 전환 | 각 라우터 |

### Phase 3: 레거시 제거 (향후)

| 단계 | 작업 | 비고 |
|------|------|------|
| 3-1 | /login/oauth2 엔드포인트 제거 | 충분한 공지 후 |
| 3-2 | User 모델 제거 또는 병합 | 데이터 마이그레이션 필요 |
| 3-3 | oauth2_scheme 제거 | - |

---

## 5. 영향 범위

### 5.1 영향 받는 API

| 라우터 | 현재 의존성 | 변경 후 |
|--------|-------------|---------|
| /api/users | get_current_account_user | 유지 (HTTPBearer) |
| /api/user-groups | get_current_account_user | 유지 (HTTPBearer) |
| /api/user-sessions | get_current_account_user | 유지 (HTTPBearer) |
| /api/cameras | get_current_user_optional | 검토 필요 |
| /api/sensors | get_current_user_optional | 검토 필요 |
| /api/controllers | get_current_user_optional | 검토 필요 |

### 5.2 영향 받지 않는 것

- 기존 장비 관련 API (cameras, sensors, controllers 등)
  - 이들은 `get_current_user_optional` 사용
  - 인증 없이도 동작 가능하도록 설계됨
  - 별도 검토 후 전환 여부 결정

### 5.3 클라이언트 영향

| 클라이언트 | 영향 | 대응 |
|------------|------|------|
| Swagger UI | ✓ 개선됨 | HTTPBearer 방식으로 변경 |
| 프론트엔드 앱 | 없음 | 이미 JSON 로그인 사용 중 |
| 외부 연동 | 확인 필요 | OAuth2 사용 시 공지 필요 |

---

## 6. 테스트 계획

### 6.1 단위 테스트

```python
# test_auth_migration.py

def test_login_returns_bearer_token():
    """JSON 로그인이 Bearer 토큰을 반환하는지 확인"""
    response = client.post("/api/auth/login", json={
        "login_id": "admin",
        "password": "admin123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()["data"]

def test_bearer_auth_works():
    """Bearer 토큰으로 인증이 동작하는지 확인"""
    # 로그인
    login_response = client.post("/api/auth/login", json={
        "login_id": "admin",
        "password": "admin123"
    })
    token = login_response.json()["data"]["access_token"]

    # Bearer 토큰으로 API 호출
    response = client.get(
        "/api/users",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

def test_oauth2_login_still_works():
    """레거시 OAuth2 로그인이 여전히 동작하는지 확인"""
    response = client.post(
        "/api/auth/login/oauth2",
        data={"username": "admin", "password": "admin123"}
    )
    assert response.status_code == 200

def test_no_auth_returns_401():
    """인증 없이 보호된 API 호출 시 401 반환"""
    response = client.get("/api/users")
    assert response.status_code == 401
```

### 6.2 Swagger UI 테스트

1. Swagger UI 접속 (`/docs`)
2. [Authorize] 버튼 클릭
3. HTTPBearer 인증 폼 확인
4. `/api/auth/login` 호출하여 토큰 획득
5. `Bearer {token}` 형식으로 입력
6. 보호된 API 호출 테스트

---

## 7. 롤백 계획

문제 발생 시 롤백:

1. `app/utils/auth.py`에서 `bearer_scheme` 제거
2. `app/dependencies.py`에서 원래 `oauth2_scheme` 복원
3. 서버 재시작

---

## 8. 일정

| 단계 | 예상 소요 | 비고 |
|------|----------|------|
| Phase 1 | 1시간 | 즉시 적용 가능 |
| Phase 2 | 2시간 | 선택적 |
| Phase 3 | 별도 계획 | 데이터 마이그레이션 포함 |

---

## 9. 체크리스트

### Phase 1 완료 조건

- [ ] HTTPBearer 스키마 추가됨
- [ ] Swagger UI에서 Bearer 토큰 입력 가능
- [ ] 기존 테스트 모두 통과
- [ ] 새로운 테스트 추가 및 통과

### Phase 2 완료 조건

- [ ] /login/oauth2에 deprecated 표시
- [ ] 모든 라우터에서 get_current_account_user 사용
- [ ] 문서 업데이트

---

## 10. 변경 이력

| 버전 | 일자 | 작성자 | 변경 내용 |
|------|------|--------|-----------|
| v1.0 | 2026-01-19 | - | 초안 작성 |
