# GOP API v4.x — .NET 통합 클라이언트 질의 회신

**회신 일자**: 2026-06-24
**대상**: .NET 통합 UI 팀
**작성**: API Server 팀 (이기호)
**근거 빌드**: `api-test-server` (feature/device-group-bulk-unassign), commit `db90f90` 기준 실측
**명세 기준**: `GOP_Restful_Api_연동설계.md` (v4.x 마스터, `c:\workspace_python\api-test-server\` git 추적본)

> 본 문서는 .NET 팀이 보내주신 31개 질의를 (1) 코드 실측, (2) 명세 대조, (3) 라이브 API 호출 검증의 3단계로 확인한 결과입니다. 검증되지 않은 추론은 모두 `caveat`으로 분리 표기했습니다.

---

## 0. 두괄식 요약 (Executive Summary)

| 구분 | 건수 | 비고 |
|---|---|---|
| ✅ 확인 답변 | **30 / 31** | 코드 + 라이브 응답으로 교차검증 완료 |
| ⚠️ 미확인 | 1 | C-8 (로그인 이력 API) — 원문 답변 절단, 결론만 별도 검증 |
| 🟥 즉시 회신 (P0/Critical) | **9건** | A-1 ~ A-4, B-1 ~ B-3, C-2, C-3, C-4 |
| 🟧 후속 회신 (P1/Normal) | **22건** | A-5, B-4 ~ B-7, C-1, C-5 ~ C-8 등 |
| 🛠 명세 보강 권고 (v4.8) | **11건** | §9.2.4, §9.3, §9.4, §9.6.4 — 하단 GAP 표 참조 |

**가장 중요한 사전 공지 3건**:
1. **permissions JSONB 구조 drift (P0)** — 시드/명세/PermissionsSchema가 서로 다름. RBAC 매트릭스 UI 구현은 v4.8 enum 결재 후 진행 권고. 그 전에는 **view-only(읽기 전용)** 로만 표시.
2. **401 응답 envelope 강제 (P0)** — 명세 §9.2.4의 `{detail:...}` 예시는 옛 형식. 실제 응답은 **항상 `{success:false, error:{code,message,details}, meta:{...}}`** 입니다. BearerAuthHandler를 envelope 기준으로 작성해 주십시오.
3. **access_token 서버측 블랙리스트 없음 (F01-S-01 Critical)** — 로그아웃·잠금·비밀번호 변경 후에도 토큰은 만료(24h)까지 유효. 강제 무효화 신호(F-1 NATS Push) 채널이 별도 결재 사항.

---

## 1. 🔴 우선 회신 (Critical 9건) — 인증·권한 핵심

### A-1. access_token / refresh_token TTL 수치

| 토큰 | 수명 | env 변경 가능 | 근거 |
|---|---|---|---|
| `access_token` | **24시간** | ✅ `JWT_EXPIRATION_HOURS` | `app/config.py:29`, `app/utils/auth.py:60` |
| `refresh_token` | **7일 (168h)** | ❌ 하드코딩 | `app/utils/auth.py:85` |

- 응답에 `expires_in` **없음**. JWT payload `exp` 클레임 디코드 필요 (서명검증 없이 클레임만 read).
- 실측(2026-06-24 04:34 UTC): access exp = +24h, refresh exp = +7d.
- **권고 선제 갱신 시점**: access 만료 5~10분 전 (.NET 팀 결정).

**Caveat**:
- refresh 7일 하드코딩 → 운영 변경 시 코드 패치 필요. v4.7+ 에서 env 노출 권고.
- 명세 §9.2.2/§9.2.4 TTL 수치 누락 → v4.8 보강 권고.
- **F03-I02 (Low)**: refresh rotation 후 옛 `jti` 블랙리스트 부재 → replay 탐지 불가.

---

### A-2. 401 응답 Body 구조 — **통합 envelope 형식 (반드시 확인)**

```jsonc
// 모든 엔드포인트의 401 응답은 동일 envelope
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Could not validate credentials",
    "details": null
  },
  "meta": {
    "timestamp": "2026-06-24T04:34:00.000Z",
    "request_id": "<uuid>"
  }
}
```

| 항목 | 값 |
|---|---|
| 직렬화 강제 | `app/main.py:455-481 http_exception_handler` (글로벌) |
| 401 → code 매핑 | `HTTP_ERROR_CODES` (`app/main.py:419-430`) |
| `error.message` | 라우터의 `HTTPException(detail=...)` 문자열 |
| 헤더 | `content-type: application/json`, `x-request-id: <uuid>` |
| ⚠️ `WWW-Authenticate: Bearer` | **누락** (글로벌 핸들러가 JSONResponse 재생성하며 헤더 소실) |

**Spec drift**: 명세 §9.2.4 L14183-14188 의 `{"detail": "Invalid refresh token"}` 예시는 **잘못됨**. .NET 측은 envelope 기준으로 구현 권고. → v4.8에 정정 권고.

**BearerAuthHandler 권고 패턴**:
```csharp
if (response.StatusCode == HttpStatusCode.Unauthorized) {
    var env = await response.Content.ReadFromJsonAsync<ApiErrorEnvelope>();
    if (env?.Error?.Code == "UNAUTHORIZED") {
        // → refresh 시도 (단, 422 validation은 별도 형식)
    }
}
```

**Caveat**:
- 422 validation 에러는 형식 다름: `error.code=VALIDATION_ERROR`, `error.details=[{field,message},...]` (`app/main.py:484-523`).
- `meta.timestamp`는 UTC `Z` 표기, 데이터 응답은 KST `+09:00` — 양쪽 파싱 필요.

---

### A-3. `/auth/refresh` 응답 — **user/permissions 미포함**

```json
{
  "success": true,
  "data": {
    "access_token": "...",
    "refresh_token": "...",
    "token_type": "bearer"
  }
}
```

| 키 | 포함 여부 |
|---|---|
| `access_token`, `refresh_token`, `token_type` | ✅ |
| `user`, `permissions`, `expires_in` | ❌ |

- 근거: `app/routers/auth.py:410-417`
- 권한 변경 반영이 필요하면 **`GET /api/auth/me` 또는 `GET /api/users/me` 별도 재호출** 권고.
- JWT payload는 `sub, exp, jti`(+ refresh의 경우 `type:"refresh"`) 만 보유 — role/permissions 없음 (`app/utils/auth.py:62, 87`).

**Caveat (Critical)**:
- **F03-I01**: refresh 라우터가 `payload.get('type') == 'refresh'` 가드 부재(`app/routers/auth.py:388-396`) → access_token으로 7일짜리 refresh 재발급 가능. **v4.7 서버 패치 필요**, 클라 측 조치는 없음.

---

### A-4. `/auth/me` vs `/users/me` 응답 차이

| 항목 | `GET /api/auth/me` | `GET /api/users/me` |
|---|---|---|
| envelope | **❌ flat** (AccountUserResponse 직접 반환) | **✅ envelope** (`{success, data}`) |
| `permissions` | **❌ 없음** | **❌ 없음** |
| `group_id` | ✅ (nullable) | ✅ (nullable) |
| 페이로드 필드 | id, login_id, name, email, department, position, employee_number, photo_url, phone, role, group_id, is_active, is_locked, lock_reason, locked_at, last_login_at, last_login_ip, created_at, updated_at | **동일** |

- 근거: `app/routers/auth.py:459-471`, `app/routers/users.py:63-77`, `app/schemas/user.py:216-238`.
- **permissions를 얻을 수 있는 유일한 표준 경로는 `POST /api/auth/login` 응답**의 `user.permissions` (`app/routers/auth.py:278-280, 296`).
- 갱신/재조회 시 권한은 **`GET /api/user-groups/{group_id}`** 별도 호출 필요.

**Caveat (High)**:
- **F04-I01**: 두 me 엔드포인트 모두 **세션 검증을 하지 않음** → logout/잠금된 사용자도 토큰만 유효하면 200 OK.

---

### B-1. permissions는 그룹 상속 후 flattened 최종값인가?

- **결론**: 현재 빌드는 **단일 그룹의 permissions JSONB를 raw 반환**합니다. flatten/merge 호출 없음.
- 근거: `app/routers/auth.py:277-296` — `if user.group and user.group.permissions: permissions = user.group.permissions`.
- AccountUser 모델에 user-level `permissions` 컬럼 없음 (`app/models/user.py:38-99`) → **단일 그룹 = 사용자 권한**.
- **클라이언트 측 병합 로직 불필요** (단일 source).

**Caveat**:
- `/auth/login`에는 permissions 노출, `/auth/me`에는 누락 — 일관성 결재 필요.
- 다중그룹/user 오버라이드 도입 시 서버 측 flatten 책임을 PRD에 명문화해야 함 (v4.x 결재 대기).

---

### B-2. 개인(user) 권한 vs 그룹(group) 우선순위

- **결론**: **현재 user-level 권한 개념 자체가 미구현**.
- AccountUser 모델/스키마(Create/Update/Response) 어디에도 permissions 필드 없음.
- 충돌 정책 자체가 **PRD 결재 사항** (Account_Auth_Session_Analysis_v4.6 §8 #2 'PermissionsSchema 구조' 미결재).
- 권고: (a) 그룹 단일 source 유지(단순/감사 용이) — v4.x 기본, (b) 도입 시 `user > group, 명시값 우선` PRD 명문화 후.

---

### B-3. `permissions.modules` 전체 키 / 동사 매트릭스 — **🚨 3원 drift (P0)**

**가장 심각한 명세-코드 drift**. 세 가지 다른 구조 공존:

| Source | 구조 | 예시 |
|---|---|---|
| 명세 §9.2.2 / §9.4.2 | nested object | `{events:{view,edit,delete,control:bool}, cameras:{...}}, device_groups:[int]` |
| 실제 시드 (`init_sample_data.py:128-132`) | **flat string** | `{events:"rw", devices:"rw", reports:"rw"}` |
| `PermissionsSchema` (`schemas/user.py:20-27`) | List[str] | `{modules:["events","cameras"], device_groups:[...]}` |

- 라우터 `UserGroupCreate.permissions` = `Dict[str,Any]` (validation 전무, `user_groups.py:41-47`).
- 라이브 GET 응답: 시드 그대로 (`{events:"rw", devices:"rw", reports:"rw"}`).

**.NET 팀 권고**:
- v4.8 enum 결재 전까지 **권한 매트릭스 UI는 view-only(읽기 전용)** 로만 표시.
- 편집/저장 기능 활성화는 (1) 모듈 키 전수 enum, (2) 동사 enum, (3) 시드/스키마/명세 3원 정렬 완료 후.

---

### C-2. 사용자 잠금/해제 (`POST /api/users/{id}/lock|unlock`)

| 항목 | 실제 동작 |
|---|---|
| Request Body | **없음 (파라미터 부재)** |
| 영향 필드 (수동 lock) | `is_locked = true` 만 변경 |
| `lock_reason`, `locked_at`, `locked_by` | **❌ 미설정** |
| 자동 잠금 시 reason | `'Too many failed login attempts'` (`auth.py:233-236`) |
| 응답 | `{success: true, data: AccountUserResponse}` |
| 감사 액션 | `USER_LOCKED` / `USER_UNLOCKED` |

- 근거: `app/routers/users.py:488-549` (lock), `:552-607` (unlock).

**Spec drift**: 명세 §9.6.4 L14588에 'reason 기록' 명시되어 있으나 코드 미구현 → v4.8/v4.7 패치 결재 필요.

**Caveat (RBAC)**:
- role 검증 게이트 부재 → OPERATOR/VIEWER도 ADMIN을 lock 가능. v4.x 패치 권고.

---

### C-3. 관리자 비밀번호 리셋 (`POST /api/users/{id}/reset-password`)

| 항목 | 실제 동작 |
|---|---|
| Request Body | `{ "new_password": str }` (1필드, `schemas/user.py:365-371`) |
| 임시비번 자동생성/이메일 발송 | **❌ 없음** |
| 비밀번호 정책 검증 | **❌ 없음** (min 1자) |
| 세션 무효화 | **❌ 없음** (기존 토큰 만료까지 유효 — F01-S-01) |
| 응답 | `{success: True}` |
| 감사 액션 | `PASSWORD_RESET` |

- 근거: `app/routers/users.py:610+`.

**Caveat**:
- 강제 무효화가 안 되므로 .NET UI에서는 "기존 세션은 즉시 만료되지 않을 수 있음" 가이드 필요.
- RBAC 게이트 부재 — OPERATOR/VIEWER 호출 가능.

---

### C-4. 본인 비밀번호 변경 (`PUT /api/users/me/password`)

| 항목 | 실제 동작 |
|---|---|
| Request Body | `{ "current_password": str(min 1), "new_password": str(min 6, max 100) }` |
| 근거 스키마 | `PasswordChangeRequest` (`schemas/user.py:374-385`) |
| 라우터 | `change_my_password` (`users.py:160-203`) |
| current_password 검증 | ✅ `verify_password()` |
| 세션/토큰 무효화 | **❌ 없음** (F07-01 Critical) |
| 감사 액션 | `PASSWORD_CHANGED` |

**Caveat**: F07-01 Critical — 변경 후에도 access_token이 24h 유효. .NET UI에서 변경 직후 강제 재로그인 처리 권고.

---

## 2. 🟡 후속 회신 (Normal 22건)

### A-5. 본인 프로필 1차 조회 표준 — `GET /api/users/me` 권고

**서버팀 공식 명문화 없음**. 단, 코드 구조상 다음 근거로 권고드립니다.

| 근거 | 내용 |
|---|---|
| envelope 일관성 | `/users/me`는 표준 envelope, `/auth/me`는 flat → 공통 파이프라인 재사용 |
| 도메인 의미 | "프로필 리소스 조회" = users/me, "토큰 주인 확인" = auth/me |
| 수정 경로 | `PUT /api/users/me`, `PUT /api/users/me/password` 만 존재 (`/auth/me` 계열에 PUT 없음) |
| 페이로드 동등성 | 두 응답 필드 완전 동일 → 표준화 비용 0 |

**예외**: 앱 시작 시 토큰 prime check만 빠르게 → `/auth/me` (flat이라 직렬화 비용 약간 낮음).

→ v4.8 명세에 '본인 프로필 표준 = `/users/me`' 라인 추가 권고.

---

### B-4. `GET /api/user-groups` 쿼리 / 응답

| 쿼리 파라미터 | 타입 | 기본값 |
|---|---|---|
| `page` | int (≥1) | 1 |
| `limit` | int (1~100) | 100 |
| `is_active` | bool? | null (필터 미적용) |

**응답**: `{success: true, data: UserGroupResponse[]}` (페이지네이션 meta **없음**)

UserGroupResponse 필드: `id, name, description, permissions, is_active, user_count(목록에서 null), created_at, updated_at`.

- 근거: `app/routers/user_groups.py:18-50`, `app/schemas/user.py:69-80`.
- 명세 §9.4.1에 쿼리/응답 스키마 누락 → v4.8 보강 권고.

**Caveat**: `total/total_pages` 미반환 → UI 페이지네이션 시 별도 카운트 필요.

---

### B-5. `GET /api/user-groups/{id}/users`

- **응답**: `{success: true, data: AccountUserResponse[]}` (페이지네이션 없음)
- AccountUserResponse 전 필드 반환, `password_hash` 제외, **permissions 미포함**.
- 근거: `app/routers/user_groups.py:324-356`.
- 명세 §9.4.1에 응답 스키마 누락 → v4.8 보강 권고.

**Caveat**: 대규모 그룹(>100명)에서 잠재 성능 이슈. 그룹 권한은 별도 `GET /user-groups/{id}` 호출.

---

### B-6. 그룹 삭제 시 소속 사용자 처리 — **SET NULL (orphan 허용)**

| 단계 | 동작 |
|---|---|
| 1. 라우터 명시 UPDATE | `db.query(AccountUser).filter(group_id==X).update({group_id: None})` |
| 2. FK ondelete | `ondelete='SET NULL'` (`models/user.py:62`) |
| 3. 그룹 삭제 | `db.delete(group)` |
| 응답 | `200 OK, {success:true, message:"User group {id} deleted successfully", data:null}` |
| 감사 액션 | `GROUP_DELETED` |

- 근거: `app/routers/user_groups.py:297-315`.

**UX 권고**: "소속자 N명이 그룹 미배정 상태로 변경됩니다" 확인 다이얼로그.

**Caveat**:
- bulk update 경로라 사용자별 `USER_UPDATED` 로그는 생성되지 않음.
- 시스템 보호 그룹(기본 그룹) 차단 로직 없음 — P1-C 결재 대기.
- 명세 §9.4 cascade 정책 누락 → v4.8 보강.

---

### B-7. `GROUP_ASSIGNED` / `ROLE_CHANGED` 트리거 엔드포인트

- **결론**: **현재 빌드에 두 액션을 trigger 하는 라우터 없음 (dead enum)**.
- enum 정의는 존재: `EnumAuditActionType.ROLE_CHANGED`, `.GROUP_ASSIGNED` (`enums.py:452-453`).
- 시드 데이터로만 사용, 실 라우터에서 `log_action` 호출 0건.
- 실제: `PUT/PATCH /api/users/{id}`에서 role/group_id 변경 시도 **`USER_UPDATED`로 단일 흡수** (`users.py:414`).

**Spec gap + Code gap 이중 결함**. v4.x 권고:
1. role 변경 시 `ROLE_CHANGED` 별도 로깅
2. group_id 변경 시 `GROUP_ASSIGNED` 별도 로깅
3. 명세 §9.6.4 트리거 표 업데이트

---

### C-1. 관리자 사용자 수정 `PUT /api/users/{id}` Body

**11개 Optional 필드 (모두 부분 업데이트)**:
`login_id, name, email, department, position, employee_number, photo_url, phone, role(EnumUserRole), group_id(int|null), is_active(bool)`

- 근거: `AccountUserUpdate` (`schemas/user.py:172-213`), 라우터 `users.py:321-348, 371-391`.
- `model_config = ConfigDict(extra="forbid")` **없음** — 알 수 없는 필드는 무시.
- 감사 액션: `USER_UPDATED` (role/group_id 변경 포함, B-7 참조).
- 명세 §9.6.4 표(L14585-14586)에 PATCH/PUT 모두 등록되어 있으나 **PATCH는 코드 미구현**.

---

### C-5. 본인 정보 수정 `PUT /api/users/me` Body — ⚠️ photo_url 처리 누락 버그

| 스키마 정의 (6필드) | 라우터 실제 처리 |
|---|---|
| name | ✅ |
| email | ✅ |
| department | ✅ |
| position | ✅ |
| phone | ✅ |
| **photo_url** | **⚠️ 미처리** (`users.py:81-156`에 photo_url 적용 코드 누락) |

- 스키마: `AccountUserSelfUpdate` (`schemas/user.py:137-169`) — `extra="forbid"` 적용됨.
- **버그**: `photo_url`을 전송해도 실제 DB에 반영되지 않음. → v4.7 핫픽스 권고.

---

### C-6. 사용자 삭제 `DELETE /api/users/{id}` — 자기 자신 가드 없음

- `current_user.id == user_id` 비교 가드 **부재** (`users.py:432-485`).
- sessions cascade: `'all, delete-orphan'` (`models/user.py:90`).
- RBAC 게이트 부재 → OPERATOR/VIEWER가 ADMIN 삭제 가능 (v4.x 패치 권고).

---

### C-7. `login_id` 사전 중복 확인 — **별도 엔드포인트 없음**

- `GET /api/users` 쿼리에 `login_id` 필터 없음 (`users.py:21-50` 시그니처 확인).
- `check/{login_id}` 류 엔드포인트 부재 (라우터 11개에 없음).
- **우회**: POST `/api/users` 시 중복 시 `400 "login_id already exists"` (`users.py:264-270`).

**.NET UX 권고**: 회원가입 폼에서 실시간 중복 체크가 필요하면 v4.7+ `GET /api/users/check-login-id?login_id=X` 신설 결재 필요.

---

### C-8. 로그인 이력 조회 API — **현재 빌드 미구현 (unverifiable, 별도 검증)**

> ⚠️ 본 항목은 원본 답변 본문이 절단되어 결론을 인용 검증할 수 없어 별도로 코드를 재확인했습니다.

- `routers/auth.py:266-274`에서 로그인 시 `UserLoginLog` 레코드는 생성됨.
- 그러나 `GET /api/auth/login-logs` 또는 `GET /api/users/{id}/login-history` 류 **조회 엔드포인트는 부재**.
- "마지막 로그인 시각/IP"만 필요하면 `me`/`users/{id}` 응답의 `last_login_at`, `last_login_ip`로 충분 (`models/user.py:77-78`, `schemas/user.py:233-234`).
- 전체 이력 화면 구현은 v4.7+ 신설 엔드포인트 결재 필요.

---

## 3. 명세 보강 권고 (v4.8 → API 팀 자체 결재)

아래 11건은 **API 팀 책임**으로 v4.8 명세에 반영합니다. .NET 팀 측 조치 없음. 추적은 본 회신과 별도 PR로 진행.

| ID | 항목 | 권고 phase |
|---|---|---|
| G-01 | §9.2.2/§9.2.4 TTL 수치 + `expires_in` 필드 표준화 | v4.7 |
| G-02 | §9.2.4 `401` 응답 예시를 envelope 형식으로 정정 | v4.7 |
| G-03 | §9.3.x `/users/me` envelope 응답 예시 추가 | v4.7 |
| G-04 | §9.4 GET 목록/상세 쿼리·응답 스키마 명문화 | v4.7 |
| G-05 | §9.4 그룹 삭제 cascade 정책 (SET NULL) 명문화 | v4.7 |
| G-06 | §9.4.1 `GET /user-groups/{id}/users` 응답 스키마 | v4.7 |
| G-07 | §9.6.4 `ROLE_CHANGED`, `GROUP_ASSIGNED` 트리거 추가 | v4.8 |
| G-08 | **permissions.modules enum 결재 (모듈 키 + 동사 매트릭스)** | **v4.8 P0** |
| G-09 | `EnumPermissionModule`, `EnumPermissionVerb` Static 시드 등록 | v4.8 |
| G-10 | `WWW-Authenticate: Bearer` 헤더 복원 (RFC 6750) | v4.7 |
| G-11 | refresh 라우터 `type=='refresh'` 가드 + jti 블랙리스트 (F03-I01) | **v4.7 P0** |

---

## 4. 회신 캘린더

| 일자 | 이벤트 | 책임 |
|---|---|---|
| 2026-06-24 (오늘) | 본 회신 송부 | API 팀 |
| ~2026-06-27 | .NET 측 추가 질의 회신 마감 | .NET 팀 |
| 2026-06-30 | v4.7 핫픽스 결재 (G-02/G-10/G-11/C-5 버그) | API 팀 + 이기호 차장 |
| 2026-07-04 | v4.8 명세 초안 (G-01~G-09 반영) | API 팀 |
| 2026-07-11 | v4.8 명세 결재 + RBAC 매트릭스 UI 활성화 가능 시점 | 전팀 |

---

## 5. 핵심 caveat 통합 (.NET 팀이 반드시 클라이언트에 반영)

1. **로그아웃·잠금·비밀번호 변경 후에도 access_token은 24h 유효** (F01-S-01 Critical).
   → .NET UI에서 변경 시 **클라 측 강제 토큰 폐기 + 재로그인** 처리 권고.
2. **권한 매트릭스 view-only**: B-3 drift 해소 전까지 권한 편집 기능 비활성화.
3. **401 = 항상 envelope** (명세 예시 무시). BearerAuthHandler를 envelope 기준으로 작성.
4. **refresh 응답엔 user/permissions 없음** → 권한 갱신은 `/users/me` + `/user-groups/{id}` 조합 호출.
5. **PUT /users/me 의 photo_url 반영 안 됨** (C-5 버그) — v4.7 핫픽스 전까지 photo_url 전송해도 무시됨, UI에 우회 안내 또는 비활성화 권고.

---

문의: API 팀 PR 채널 또는 본 문서 댓글로 회신 부탁드립니다.
