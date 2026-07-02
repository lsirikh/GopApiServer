# GOP Server API v5.3 — Legacy User 모델 제거 통지

- **작성일**: 2026-07-02
- **작성자**: GOP API 서버 팀 (이기호 차장)
- **수신**: .NET 클라 팀 (Dotnet.Monitoring.Solution / Ironwall.Dotnet.Libraries / Dotnet.Rtsp.Viewer.Ui) + GIS 팀
- **관련**: `PRD_Legacy_User_Removal.md` / `v5.3-final-stable` 태그 / commit `fe4a48a`
- **연관 이력**: v4.9 SEC-1 마스킹 회신 (`GOP_Server_API_v4.9_Review_RESPONSE.md`)

---

## 1. 배경

GIS 팀 요청 (2026-07-02): *"API를 활용하는 GIS 쪽에서 `User`와 `AccountUser` 두 파트가 혼용되어 있어 레거시는 정리 삭제하는 게 좋겠다"*

**팩트 조사 결과**:

| 항목 | Legacy `User` | 신규 `AccountUser` |
|---|---|---|
| DB 테이블 | `users` (admin 1건) | `account_users` (실 계정 8건) |
| FK 참조 (다른 테이블 → 이 테이블) | **0건** | 9건 (audit_logs / user_sessions / token_blacklist 등) |
| 라우터 사용 | Legacy `get_current_user_optional` 30 라우터 (실 로직 미사용) | `get_current_account_user` 7 라우터 (실 인증 검증) |

→ Legacy `User`는 사실상 사용 안 되는 dead code로 확인. **무위험 이주** 결정.

---

## 2. 삭제된 항목

### 2.1 Endpoint 제거

| Endpoint | 이전 상태 | 현재 |
|---|---|---|
| `POST /api/auth/login/oauth2` | `deprecated=True` (Legacy OAuth2 로그인) | ❌ **완전 제거** — Swagger에서 사라짐 |

### 2.2 Schema 제거 (Swagger `components.schemas`)

| Schema | 사용처 | 현재 |
|---|---|---|
| `UserResponse` | 없음 (모두 `AccountUserResponse` 사용 중) | ❌ **완전 제거** |
| `UserCreate` | 없음 (모두 `AccountUserCreate` 사용 중) | ❌ **완전 제거** |
| `Token` | 신규 `/api/auth/login`, `/api/auth/refresh` | ✅ **유지** (Legacy 표기만 제거) |

### 2.3 DB 스키마

| 테이블 | 이전 | 현재 |
|---|---|---|
| `users` (Legacy, 6 컬럼) | 존재 (admin 1건) | ❌ **DROP TABLE users CASCADE** (마이그레이션 `v56_drop_users_table.sql`) |
| `account_users` (신규, 26 컬럼) | 존재 | ✅ **유지** |

### 2.4 내부 코드 (참고용)

- `app/models/user.py` `class User` 삭제
- `app/routers/auth.py` — `get_current_user` / `get_current_user_optional` / `login_oauth2` (3 함수) 삭제
- `app/schemas/user.py` — `UserCreate` / `UserResponse` (2 schema) 삭제
- `app/utils/init_db.py` — `create_admin_user()` (Legacy admin 시드) 삭제
- 30 라우터: `get_current_user_optional` → `get_current_account_user_optional` 헬퍼 교체

---

## 3. 유지된 항목 (변경 없음)

### 3.1 URL/Method/Response schema 100% 유지

30 라우터 모든 endpoint의:
- URL 경로 동일
- HTTP method 동일
- Response envelope 동일 (`{success, message, data, pagination}`)
- Response schema 동일
- 응답 코드 동일 (200 / 401 / 404 등)

**즉 클라 측 호출 코드 변경 불필요** (아래 §5 예외 1건 제외).

### 3.2 인증 flow (신규 방식 유지)

```
POST /api/auth/login              (JSON body, 유지)
POST /api/auth/refresh            (JSON body, 유지)
POST /api/auth/logout             (JWT Bearer, 유지)
GET  /api/auth/me                 (JWT Bearer, 유지)
```

- Access token: JWT (HS256, 24h TTL)
- Refresh token: JWT (7d TTL)
- Blacklist 기반 즉시 무효화 (v4.9 도입)
- `AccountUser` 모델 완전 통일 (`login_id` / `password_hash` / `role` / `is_locked` / `is_active` etc.)

---

## 4. 클라 영향 요약

### 4.1 대부분의 클라 코드 = **영향 없음** ✅

- 신규 login (`POST /api/auth/login` JSON) 사용 중이면 → **변경 불필요**
- 30 라우터의 응답 형식/코드 동일 → **변경 불필요**
- `AccountUserResponse` 사용 중이면 → **변경 불필요**

### 4.2 실측 검증 결과 (2026-07-02, 14/14 PASS)

| 시나리오 | 결과 |
|---|:---:|
| admin login (`login_id`/`password` JSON) | **200** ✅ |
| Bearer 토큰으로 `/api/auth/me` | **200** ✅ |
| `/api/users`, `/user-groups`, `/user-sessions` | **200** ✅ (RBAC 통과) |
| `/api/audit-logs`, `/reports/templates` | **200** ✅ |
| `/api/servers`, `/devices/cameras/controllers/sensors` | **200** ✅ |
| `/api/events/actions/detections` | **200** ✅ |
| `/api/tracking/health`, `/api/tracking/points` | **200** ✅ |
| Swagger `UserResponse` / `UserCreate` schema 존재 | **False** ✅ (제거 확정) |
| Swagger `/api/auth/login/oauth2` endpoint 존재 | **False** ✅ (제거 확정) |

---

## 5. 대응 필요 사항 (해당 시)

### 5.1 `POST /api/auth/login/oauth2` 사용처가 있으면 → **JSON login으로 교체**

**과거 (Legacy)**:

```csharp
// OAuth2 form-encoded (제거됨)
var content = new FormUrlEncodedContent(new[] {
    new KeyValuePair<string, string>("username", "admin"),
    new KeyValuePair<string, string>("password", "admin123")
});
var response = await httpClient.PostAsync("/api/auth/login/oauth2", content);
// Token { access_token, token_type }
```

**신규 (JSON)** — 이미 v4.4에서 도입됨:

```csharp
// JSON body (사용 권장)
var body = new { login_id = "admin", password = "admin123" };
var response = await httpClient.PostAsJsonAsync("/api/auth/login", body);
// ApiResponse { success, data: { access_token, refresh_token, token_type, user: {...} } }
```

**차이점**:
- `username` → **`login_id`**
- Form → **JSON**
- 응답에 `refresh_token` + `user` 정보 포함 (권한 permissions 포함)

### 5.2 `UserResponse` / `UserCreate` schema 참조가 있으면 → **`AccountUserResponse` / `AccountUserCreate`로 교체**

.NET 자동 생성 클라이언트 (예: NSwag) 재생성 시 자동 반영됨.

### 5.3 DB 직접 접근 코드 (있으면) → **`account_users` 테이블 참조로 변경**

- `users.username` → `account_users.login_id`
- `users.hashed_password` → `account_users.password_hash`
- `users.role` → `account_users.role` (동일)
- 6 컬럼 → 26 컬럼 (프로필 + lock 메타 + audit 필드 추가)

---

## 6. 참조

| 항목 | 위치 |
|---|---|
| PRD | `docs/prds/PRD_Legacy_User_Removal.md` (Approved) |
| Plan | `docs/plans/Legacy_User_Removal-prd-plan.md` |
| CHANGELOG | `CHANGELOG.md` `[v5.3]` — 2026-07-02 |
| 명세서 | `GOP_Restful_Api_연동설계.md` v5.3 (변경 이력 v5.3 행) |
| Migration SQL | `app/migrations/v56_drop_users_table.sql` + `_reverse.sql` |
| commit | `fe4a48a` — feat(v5.3) |
| 안전점 태그 | `pre-legacy-user-removal` (롤백 가능) |
| 마감 태그 | `v5.3-final-stable` |
| Gitea | `v4.8` branch = `fe4a48a1` |
| origin | `feature/report-master-redesign` = `fe4a48a` |
| Swagger | `info.version = 5.3.0` / `API Version = 5.3` (2026-07-02) |

---

## 7. 문의

| 담당 | 채널 |
|---|---|
| GOP API 서버 팀 | 이기호 차장 |
| 명세 관련 | `GOP_Restful_Api_연동설계.md` 참조 |
| 회귀 발견 시 | 즉시 통지 요청 (안전점 태그로 롤백 가능) |

---

## 부록 A. 롤백 절차 (긴급 시)

```bash
# 코드 롤백
git reset --hard pre-legacy-user-removal

# DB 롤백 (구조만 재생성, 데이터 복원 X)
docker exec -i api-test-postgres psql -U gop_user -d gop < app/migrations/v56_drop_users_table_reverse.sql

# Container rebuild
docker compose build api-server && docker compose up -d --force-recreate api-server
```

---

**문서 버전**: v1.0 / **최종 수정**: 2026-07-02 / **상태**: Final (배포 통지용)
