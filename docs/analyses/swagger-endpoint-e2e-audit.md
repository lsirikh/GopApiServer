# Swagger 실측 전수 검증 (E2E) — API v6.3.2

> **작성**: 2026-08-07 · **대상**: `https://localhost:8000` (pids-api-server) · **Swagger**: `/docs` (OAS 3.1, info.version=6.3.2)
> **계정**: `admin` / `admin123` (로컬 DB 해시 오프라인 검증. ※ 원격 테스트서버 `123.141.236.253:8136` 은 `sensorway1` 로 별개)
>
> 총 **251 오퍼레이션** / 45 태그.

## 검증 방식 (명확히 구분)

| 구분 | 방식 | 범위 |
|---|---|---|
| **(A) Swagger UI 실조작** | 브라우저에서 `/docs` 기동 → `Authorize` 모달에 Bearer 등록 → 오퍼레이션 펼침 → **`Try it out` → `Execute` 버튼 클릭** → 렌더된 `Curl` / `Request URL` / `Server response` 판독 | 로그인·인증 4건 + **경로파라미터 없는 GET 52건** + **경로파라미터 GET 15건** + **통계 4건** + **Example Value 무수정 실행 14건** |
| **(B) Swagger 페이지 컨텍스트 발사** | 같은 Swagger 페이지에서 **동일 토큰·동일 헤더**로 요청 발사 후 응답 수집 (버튼 클릭은 거치지 않음) | 경계값·권한조합·CRUD 매트릭스 등 **대량 반복 구간** |

> ⚠️ 초기에는 (B) 위주로 진행했고, PM 지적으로 (A) 로 전환해 **Swagger UI 조작 하네스**를 구축했다.
> 두 방식의 서버 응답은 동일하나, 본 문서는 어느 방식으로 얻은 근거인지 구분해 표기한다.
> **Example Value 감사(§7) 는 전부 (A)** — Swagger 가 채워준 값을 **한 글자도 고치지 않고** Execute 한 결과다.

---

## 0. 진행 현황

| 섹션 | 범위 | 오퍼레이션 | 상태 |
|---|---|---:|---|
| **S1 계정** | Authentication · Users · User Groups · Grants · User Sessions · Settings · Audit Logs | 42 | ✅ 완료 |
| **S2 디바이스** | Controllers · Sensors · Cameras · Lamps · Speakers · Enclosures · DeviceGroups · XyPoints · ROIs · CameraPresets · Camera Settings | 66 | ✅ 완료 |
| **S3 이벤트** | Detections · Malfunctions · Connections · Actions · Detection Logs · Event Statistics · Event Suppression · Event Mapping ×3 · Mapping ×3 | 66 | ✅ 완료 |
| **S4 서버/통합** | Servers · Server Categories · Server Metrics · Proxy Settings · Integration · Enclosure Metrics | 32 | ✅ 완료 |
| **S5 리포트/시스템** | Reports · Logs · System Events · Config Change Logs · Thumbnails · FileGroups · Tracking · Health · Root | 45 | ✅ 완료 |
| **§7 Example 감사** | 요청바디 보유 102 오퍼레이션 전수 대조 + 대표 14건 무수정 실행 | — | ✅ 완료 |

---

## 0-1. 전 구간 결함 총괄 (심각도순)

| # | 심각도 | 결함 | 섹션 |
|---|---|---|---|
| **X-01** | 🔴 **P0** | Swagger `PUT /api/settings/session` **Example 을 그대로 Execute 하면 운영 세션정책이 즉시 변경**(session_enabled→true, evict_all, timeout 1h) | §7 |
| **X-02** | 🔴 **P0** | Swagger `POST /api/event-suppression-schedules` Example 실행 시 **실제 억제창이 장비 11·12·13 에 생성** | §7 |
| **A-01** | 🔴 **P0** | `permissions.valid_until` 9시간 이르게 응답 → 클라가 유효 grant 를 만료로 오판 | §2 |
| **A-02** | 🔴 **P0** | `server_time` 9시간 이르게 응답 (시계보정 기준값 오염) | §2 |
| **S3-01** | 🟠 **P1** | 통계 `time_bucket` 이 **UTC** 인데 같은 응답 `start_date` 는 `+09:00` → **차트 X축 9시간 어긋남** | §8 |
| **S4-01** | 🟠 **P1** | **서버 카테고리 삭제가 소속 서버 전량을 경고 없이 CASCADE 삭제** | §9 |
| **A-03** | 🟠 **P1** | 본인 계정 DELETE → **500 + 감사로그 소실**(삭제는 성공) | §3 |
| **S3-02** | 🟠 **P1** | `result`/`reason` 이 OpenAPI 엔 `string` 인데 서버는 **enum 만 수락** → Swagger 대로 보내면 422 | §8 |
| **S2-01** | 🟠 **P1** | `number_device` **UNIQUE 없음** → 동일 번호 장비 중복 생성 (GIS/브로커 식별키) | §8 |
| **S3-03** | 🟠 **P1** | 이벤트매핑 램프 중복 → **500**(카메라·스피커는 201 허용) — 제약 비대칭 | §8 |
| **S5-01** | 🟠 **P1** | `GET /api/logs?start_date=notadate` → **500** (422여야 함) | §10 |
| **S3-06** | 🟡 P2 | 억제 PATCH 에 명시적 `null` → **500** | §8 |
| **S4-02** | 🟡 P2 | 이벤트매핑 생성 시 `device_group_id: 0` → **500** | §9 |
| **S2-02** | 🟡 P2 | 제어기 삭제가 **종속 센서를 경고·건수 표시 없이 연쇄 삭제** | §8 |
| **S2-03** | 🟡 P2 | 존재하지 않는 device_id 그룹 할당 → **200 인데 반영 0건**(조용한 실패) | §8 |
| **S4-03** | 🟡 P2 | 서버 메트릭 **범위 검증 없음**(cpu 150·memory −5 수락) + 오타 필드 조용히 폐기(`memory_usage`≠`ram_usage`) | §9 |
| **S5-02** | 🟡 P2 | `acknowledge` 가 **인증 주체가 아닌 클라 제공 문자열**을 확인자로 기록 | §10 |
| **A-04~A-13** | 🟡🟢 P2/P3 | 계정 도메인 10건 (잠금사유 미기록·pagination 부재·limit/size 불일치·이메일 미검증·약한 비번정책 등) | §1 |
| **X-03** | 🟡 P2 | 요청바디 보유 오퍼레이션 **39건의 Example 이 placeholder(`"string"`)** — 그대로 실행 시 422/404/500 또는 쓰레기 데이터 생성 | §7 |

---

## 1. 결함 요약 (S1 계정)

| # | 심각도 | 결함 | 위치 | 상태 |
|---|---|---|---|---|
| **A-01** | 🔴 **P0** | `permissions.valid_until` 가 **9시간 이르게** 응답 — 클라가 유효 grant 를 만료로 오판 | [auth.py:683](../../app/routers/auth.py#L683), [auth.py:1248](../../app/routers/auth.py#L1248) | 기지(F-0 파생) · **미수정** |
| **A-02** | 🔴 **P0** | `server_time` 이 **9시간 이르게** 응답 — 시계보정 기준값이 오염 | [auth.py:1249](../../app/routers/auth.py#L1249) | 기지(F-0) · **미수정** |
| **A-03** | 🟠 **P1** | 본인 계정 `DELETE` 시 **500** + **감사로그 소실** (삭제는 성공) | [users.py:911](../../app/routers/users.py#L911) | 기지(C-6 가드부재) · **미수정** |
| **A-04** | 🟡 P2 | 수동 `lock` 이 `lock_reason` 을 기록하지 못함(요청 바디 자체가 없음) | [users.py:931](../../app/routers/users.py#L931) | **신규** |
| **A-05** | 🟡 P2 | 목록 응답에 **`pagination` 블록 부재** — 총건수/페이지수 미제공 | users·user-groups·user-sessions | **신규** |
| **A-06** | 🟡 P2 | 페이지 크기 파라미터 **불일치**: `limit` vs `size`(grants만) | 계정 도메인 4개 목록 | **신규** |
| **A-07** | 🟡 P2 | `email` **형식 검증 없음** — `not-an-email` 저장됨 | `AccountUserCreate/Update` | **신규** |
| **A-08** | 🟡 P2 | 비밀번호 정책이 **길이 8자 뿐** — `12345678`·`password`·`login_id 와 동일` 전부 통과 | `AccountUserCreate` | **신규** |
| **A-09** | 🟢 P3 | `photo_url` 이 **절대/상대 혼재** (업로드분=절대, default=상대) | users 응답 전반 | **신규** |
| **A-10** | 🟢 P3 | `/api/auth/me` 만 **ApiResponse 봉투 미적용**(bare object) | [auth.py](../../app/routers/auth.py) | **신규** |
| **A-11** | 🟢 P3 | 잘못된 refresh 토큰 401 메시지에 **내부 코덱 오류 노출** | `Invalid header string: 'utf-8' codec can't decode...` | **신규** |
| **A-12** | 🟢 P3 | 폐기된 토큰으로도 `POST /auth/logout` 은 **200**(타 엔드포인트는 401) | logout 멱등 처리 | **신규** |
| **A-13** | 🟢 P3 | `role=NOPE` 등 잘못된 enum 필터가 **422 아닌 200 + 빈 배열** | `GET /api/users?role=` | **신규** |
| **A-14** | ℹ️ 정보 | 세션/토큰 만료 **2036년(10년)** — `session_enabled=false` 의 알려진 귀결(SEC-05) | 정책 | 기지·보류 |

### 오탐으로 배제한 항목 (검증 우선 원칙)

| 항목 | 초기 의심 | 실측 결론 |
|---|---|---|
| `GET /auth/me` 가 `last_login_at` 갱신 | 호출마다 값 변동 관측 | **오탐** — 3회 연속 호출 시 값 불변. 외부 클라이언트의 별도 로그인이 원인 |
| `lockout_threshold: 0` 무검증 수락 | 위험값 통과로 의심 | **오탐** — 스키마 `ge=0` + 검증기가 `0(비활성) 또는 3~20` 만 허용(1·2 는 422). **의도된 "잠금 비활성"** 값 |
| POST 시 여분 필드(`is_locked:true`) 주입 | 권한상승 우려 | **오탐** — 무시됨(레코드 반영 0). `extra=forbid` 아닌 lax 처리일 뿐 |

---

## 2. A-01 / A-02 — 시각 9시간 오차 (P0)

### 실측

동일 순간(브라우저 UTC `2026-08-07T04:16:49Z` = **KST 13:16:49**)의 응답:

| 출처 | 필드 | 응답값 | 판정 |
|---|---|---|---|
| `GET /api/users/62/grants` | `valid_until` | `2026-08-07T15:16:27+09:00` | ✅ **정확** |
| `POST /api/auth/login` | `data.user.permissions.valid_until` | **`2026-08-07T06:16:27+09:00`** | ❌ **-9h** |
| `GET /api/auth/me/permissions` | `data.valid_until` | **`2026-08-07T06:16:27+09:00`** | ❌ **-9h** |
| `GET /api/auth/me/permissions` | `data.server_time` | **`2026-08-07T04:16:49+09:00`** | ❌ **-9h** |
| `GET /api/auth/me` | `last_login_at` | `2026-08-07T13:10:12+09:00` | ✅ 정확 |

### 근본원인 (2단)

1. [auth.py:134-137](../../app/routers/auth.py#L134-L137) — `_kst_now()` 가 docstring("settings.tz 기준 naive now")과 달리 **`utc_now()` 를 반환**. `from app.config import settings` 는 사용조차 안 됨.
2. [auth.py:1248-1249](../../app/routers/auth.py#L1248-L1249) · [auth.py:683](../../app/routers/auth.py#L683) — 그 UTC 값에 `astimezone`/`to_display` 가 아니라 **`.replace(tzinfo=settings.tz)`** 를 적용해 **변환 없이 라벨만** `+09:00` 으로 교체.

```python
# 현재 (틀림) — 값은 UTC 인데 라벨만 KST
"server_time": now.replace(tzinfo=settings.tz),
"valid_until": valid_until.replace(tzinfo=settings.tz),

# 기대 — 값을 KST 로 변환
"server_time": to_display(now),
"valid_until": to_display(valid_until),
```

### 클라이언트 영향 (A-01 이 A-02 보다 위험)

- 실제 만료 **15:16 KST** 인 grant 를 서버가 **06:16 KST** 로 통지 → 현재 13:16 기준 **이미 7시간 전 만료**로 보임.
- `server_time` 과 `valid_until` 이 **같은 방향으로 shift** 되므로, 두 값끼리 비교하는 클라는 우연히 정상 동작.
- 그러나 **로그인 응답에는 `server_time` 이 없다** → 로그인 시 권한을 캐시하고 **로컬 시계와 비교**하는 자연스러운 구현은 **권한을 즉시 폐기**한다.
- 소비 주체: `Dotnet.Monitoring.Solution` / `Ironwall.Dotnet.Libraries` / `Dotnet.Rtsp.Viewer.Ui`.

> ※ `docs/analyses/datetime-tz-endpoint-audit.md` 의 **F-0** 과 동일 뿌리. 본 검증은 **운영 컨테이너에서 여전히 재현됨**과, `valid_until` 의 **구체적 클라 오판 시나리오**를 실증한 것.

---

## 3. A-03 — 본인 계정 삭제 시 500 + 감사 소실 (P1)

### 재현

ADMIN 계정(`swg_admin_try`, id=66)이 자기 토큰으로 `DELETE /api/users/66` 호출:

```
HTTP 500 Internal server error
```

### 서버 트레이스 (실 로그)

```
File "/app/app/routers/users.py", line 911, in delete_user
    await log_action_async(...)
sqlalchemy.exc.IntegrityError: ForeignKeyViolationError:
  insert or update on table "audit_logs" violates foreign key constraint "audit_logs_actor_id_fkey"
  DETAIL:  Key (actor_id)=(66) is not present in table "account_users".
```

### 결과 상태 (DB 실측)

| 확인 | 결과 |
|---|---|
| `account_users` 에 id=66 | **0 rows** (삭제 성공) |
| `audit_logs` 의 `USER_DELETED` for 66 | **없음** (최신 기록은 2026-07-03) |
| `audit_logs` 시퀀스 | **id 158 결번** — 롤백된 INSERT 자리 |
| 대조군 | 같은 날 타인 삭제 9건은 **전부 정상 기록**(177~185) |

### 문제 성격

1. **파괴적 작업이 성공했는데 5xx** 를 반환 → 클라는 실패로 오인해 재시도(이미 없어 404).
2. **감사 추적 소실** — 계정 삭제라는 최고위험 행위가 로그에 안 남음.
3. 근본은 `current_user.id == user_id` **자기삭제 가드 부재**(문서 `GOP_Server_API_OpenQuestions_RESPONSE.md` C-6, v4.x 지적 → v6.3.2 까지 미해결).

### 조치 방향

- (권장) 자기삭제 **409 차단** — 최소 변경, 의도도 명확.
- (대안) 감사 INSERT 를 삭제 **이전**에 수행하거나 `actor_id=None` 으로 익명화(기존 append-only 예외 정책과 정합).

---

## 4. A-04 ~ A-13 상세

### A-04 · 수동 잠금 사유 미기록

`POST /api/users/{id}/lock` 은 OpenAPI 상 **requestBody 자체가 없음**([users.py:931-936](../../app/routers/users.py#L931-L936)). `{"reason": "..."}` 을 보내도 조용히 무시되고 `lock_reason` 은 `null` 로 남는다.
자동잠금(로그인 실패)만 `lock_reason="Too many failed login attempts"` 를 기록하므로 **필드가 비대칭 충전**된다. 실측: `is_locked=true, lock_reason=null, locked_at=2026-08-07T13:14:17+09:00`.

### A-05 · `pagination` 블록 부재

Swagger 최상단 설명은 `{"success", "data", "pagination"}` 을 계약으로 명시하지만, 계정 도메인 목록 응답 키는 `["success","data"]` 뿐. `grants` 만 비표준 `total` 을 최상위에 둔다.
→ 클라가 **총 건수·다음 페이지 존재 여부를 알 수 없다**.

### A-06 · 페이지 파라미터 불일치

| 엔드포인트 | 페이지 크기 파라미터 |
|---|---|
| `GET /api/users` | `limit` (기본 100) |
| `GET /api/user-groups` | `limit` (기본 100) |
| `GET /api/user-sessions` | `limit` (기본 100) |
| `GET /api/grants` | **`size`** (기본 20) |

`?size=3` 을 `/api/users` 에 주면 **조용히 무시**되어 전건 반환(13건). 경계값은 정상: `limit=0/-5`, `page=0` → 422.

### A-07 · 이메일 미검증

`{"email": "not-an-email"}` → **201 CREATED**, DB 에 원문 저장. `str` 타입만 선언되어 있고 `EmailStr` 미사용.

### A-08 · 비밀번호 정책

`min_length=8` 이 유일한 제약. 실측 통과: `12345678`, `aaaaaaaa`, `password`, **`login_id` 와 동일한 값**.
프로젝트 보안 규칙(`.claude/rules/common/security.md`)의 인증 강화 지침 대비 미흡.

### A-09 · `photo_url` 절대/상대 혼재

동일 목록 응답 안에서 혼재한다.
```
{"id":23, "photo_url":"https://localhost:8000/api/users/photo/23_835528fd.jpg"}   ← 절대
{"id":21, "photo_url":"/api/users/photo/default.png"}                             ← 상대
```
클라가 base URL 을 붙이는 구현이면 업로드 계정에서 `https://host/api/users/photo/https://...` 로 깨진다.

### A-10 · 봉투 불일치

`GET /api/auth/me` 만 `{id, login_id, ...}` **bare object**. `GET /api/users/me` 는 `{success, data}`. 동일 정보·다른 계약.

### A-11 · 내부 오류 노출

```json
{"error":{"code":"UNAUTHORIZED",
 "message":"Invalid refresh token: Invalid header string: 'utf-8' codec can't decode byte 0x9e in position 0: invalid start byte"}}
```
프로젝트 규칙 "내부 에러 상세를 사용자에게 노출 금지" 위반. 일반 메시지로 축약 필요.

### A-12 · logout 멱등 비일관

폐기된(그러나 서명 유효한) 토큰으로 `POST /auth/logout` → **200**. 동일 토큰으로 `GET /auth/me` → 401.
서명 자체가 깨진 토큰은 401(정상). 멱등 UX 로 의도했을 수 있으나 **계약 문서화 필요**.

### A-13 · 잘못된 enum 필터

`GET /api/users?role=NOPE` → **200 + `[]`**. 오타가 "사용자 없음"으로 보여 오해를 유발. `role` 은 `ADMIN|USER` 2종이므로 422 가 적절.

---

## 5. 정상 확인 항목 (S1)

> **회귀 방지 기준선.** 아래는 전부 실측 PASS.

### 5.1 인증 · 토큰 (11/11)

| 시나리오 | 기대 | 실측 |
|---|---|---|
| 로그인 성공 | 200 + access/refresh/session_id | ✅ |
| 오답 로그인 안내 | `5회 중 N회 실패, M회 남음` + `error.details` | ✅ `{failed_count,threshold,remaining,locked}` |
| refresh 회전 | 새 access+refresh 발급 | ✅ |
| 옛 refresh 재사용 | 401 `SESSION_REVOKED/REFRESH_ROTATION` | ✅ |
| access 를 refresh 로 사용 | 401 `Token type mismatch` | ✅ |
| 회전 후 옛 access | 401 (orphan jti 제거) | ✅ |
| logout | 200 → 이후 401 | ✅ |
| logout 후 refresh | 401 `SESSION_REVOKED/USER_LOGOUT` | ✅ |
| 세션 자가삭제 | 200 → 토큰 401 `SELF_LOGOUT` | ✅ |
| reset-password 실효 | 새 비번 200 / 옛 비번 401 | ✅ |
| 본인 비번 변경 | 현재비번 오답 400 · 8자미만 422 · 정상 200 | ✅ |

### 5.2 무토큰 접근 차단 — **37/37 전부 401, 누수 0건**

`auth/me`·`users`(전 CRUD·lock·unlock·reset-password·photo)·`user-groups`(전 CRUD·permissions)·`grants`·`user-sessions`(전 6종)·`settings/session`·`audit-logs` 전부 401.
공개 경로는 `GET /api/users/photo/{file_name}` 하나뿐(프로필 사진 서빙, 파일명에 랜덤 해시 포함).

### 5.3 RBAC 상승 가드 — **13/13 정확** (최우수 항목)

`users:{view,edit,delete,control}` 전권 그룹을 **grant 로 한시 승격**한 USER 계정으로 검증:

| 행위 | 기대 | 실측 |
|---|---|---|
| 사용자 목록·타인 수정·잠금·해제 | 200 (매트릭스 통과) | ✅ 200 |
| 타인 `role` 변경 | 403 | ✅ `Only ADMIN role can change role or group assignment` |
| 타인 `group_id` 변경 | 403 | ✅ 동일 |
| **자기 자신 ADMIN 승격** | 403 | ✅ 동일 |
| ADMIN 대상 수정/비번초기화/잠금/삭제/사진 | 403 | ✅ `Only ADMIN role can modify an ADMIN account` |
| **자기 자신에게 grant 부여** | 403 | ✅ `requires one of ['ADMIN']` |
| 그룹 권한 자체 편집 | 403 | ✅ 동일 |
| 세션 설정 변경 | 403 | ✅ `requires setup_system:edit` |

→ **한시 승격이 영구 승격으로 전이되는 경로가 전부 차단**됨. 설계 의도대로 동작.

### 5.4 Grant 시간 처리 — 정확

| 입력 형식 | 보낸 값 | 응답 | 판정 |
|---|---|---|---|
| naive(KST 벽시계) | `2026-08-07T13:16:27` | `2026-08-07T13:16:27+09:00` | ✅ 왕복 일치 |
| offset-aware(UTC) | `2026-08-07T04:15:27.811+00:00` | `2026-08-07T13:15:27.811+09:00` | ✅ 정확 변환 |

검증: 종료<시작 422 · 없는 그룹/사용자 404 · `valid_from` 누락 422 · 날짜 파싱실패 422.
**회수 즉시성**: `DELETE /api/grants/{id}` 직후 **토큰 재발급 없이** 200→403 전환 확인. 재회수 200(멱등), 없는 id 404, `status=REVOKED` + `revoked_at` 기록.

### 5.5 자기수정 스키마 — `extra=forbid` 유효

`PUT /api/users/me` 에 `role`·`is_active`·`group_id` 주입 시 전부 **422 "Extra inputs are not permitted"**.
`photo_url: "../../etc/passwd"` → 422 (`http://`, `https://`, `/api/users/photo/` 만 허용). **v6.3-profile_photo_crud 수정이 실제로 작동**.

### 5.6 프로필 사진 CRUD (7/7)

업로드 200 · 다운로드 `image/png` 1360B · **매직바이트 위조 400 차단**(content_type 만 `image/png` 인 텍스트) · 재업로드 시 **옛 파일 orphan 제거 확인**(컨테이너 `/app/data/profiles` 실측) · 관리자→대상 업로드 200 · USER→타인 403 · 없는 대상 404 · 삭제 멱등 200(default 복귀).

### 5.7 User Groups (10/10)

생성 201 · **중복 이름 409** · 이름누락 422 · 권한 타입오류 422(`permissions.modules.events.view` 필드경로까지 정확) · 조회/수정 200 · `POST /permissions` 200 · **`PUT /permissions` 405 영구차단**(정책대로) · 404 2종.

### 5.8 감사 로그 — 행위자 귀속 정확

당일 47건 전수 확인. `USER_CREATED`/`USER_UPDATED`/`USER_LOCKED`/`USER_UNLOCKED`/`PASSWORD_RESET`/`PASSWORD_CHANGED`/`GROUP_*`/`PERMISSION_CHANGED`/`GRANT_CREATED`/`GRANT_REVOKED`/`SESSION_TERMINATED`/`USER_PHOTO_CHANGED`/`USER_PHOTO_DELETED`/`USER_DELETED` 기록.
행위자 분리 정확: 관리자 행위=`admin`, 한시승급자 행위=`swg_elevated`, 본인 셀프서비스=`swg_test_user`.

---

## 6. 테스트 데이터 정리

| 항목 | 처리 |
|---|---|
| 생성 계정 10건 (`swg_*`) | **9건 API 삭제 완료** · 1건(`swg_admin_try`)은 A-03 재현으로 이미 삭제됨 |
| 생성 그룹 2건 | **삭제 완료** |
| 생성 grant 4건 | 소속 계정 삭제로 정리 |
| `lockout_threshold` 임시 변경 | **5 로 원복 확인** |
| 최종 상태 | 계정 **13건**(원래대로) · 그룹 **5건**(원래대로) |

> ⚠️ 잔여: `/app/data/profiles` 에 이전 시기 orphan 2건(`1_64117cb4.png`, `1_df60fe41.jpg`, `63_6d8e44e2.jpg`) 존재 — 본 검증과 무관한 **v6.3-profile_photo_crud 수정 이전** 잔재.

---

## 7. Swagger **Example Value** 감사 ★

> PM 지시: "Example 로 있는 문구도 틀린 게 있으면 체크해서 같이 정정."
> **방식 (A)** — Swagger 가 채워준 Example Value 를 **한 글자도 고치지 않고** `Execute`.

### 7.1 기계적 대조 결과

`components.schemas` 전체의 example 값 **411개**를 enum·min/max·타입에 대조 → **불일치 0건**.
→ example 은 *선언된 스키마와는* 일치한다. **문제는 선언 자체가 실제 서버 검증과 다르거나, example 이 placeholder 라는 것.**

### 7.2 placeholder Example — **39 오퍼레이션**

Swagger 가 자동 생성한 `"string"` / `0` 이 그대로 노출된다.

| 대상 | placeholder 필드 |
|---|---|
| Controllers · Sensors (POST/PATCH/PUT) | `name_device` `type_device` `version` `status` `ip_address` `geolocation.location` |
| Cameras (POST/PATCH/PUT) | 위 + `user_name` `user_password` `mode` `category` `hardware_spec.*` 9필드 |
| Speakers · Enclosures | `name_device` `version` `description` / `geolocation.location` |
| Users (POST · PUT /me · PUT /{id}) | **`photo_url: "string"`** |
| Settings | **`session_concurrency_policy: "string"`** |
| Server Categories · FileGroups · EventMapping · ReportTemplates · CameraPresets · ROIs · Suppression · UserGroups(PUT) | `name` `description` `group_name` `name_event` `preset_name` `recurrence_rule` 등 |

### 7.3 **무수정 실행 실측** (Swagger UI `Execute` 버튼)

| 오퍼레이션 | 결과 | 판정 |
|---|---|---|
| `POST /api/auth/login` | **200** | ✅ example 정상 (`admin`/`admin123`/`vms-service`) |
| `POST /api/devices/controllers` | **422** | ❌ `Invalid enum value: 'string' is not a valid EnumDeviceType` |
| `POST /api/devices/cameras` | **422** | ❌ 동일 |
| `POST /api/devices/sensors` | **404** | ❌ `Controller with id 0 not found` (`controller_id: 0`) |
| `POST /api/devices/speakers` | **404** | ❌ `Server with id 1 not found` — example 이 **존재하지 않는 server_id** 를 가리킴 |
| `PUT /api/users/me` | **422** | ❌ `photo_url must start with http://, https://, or /api/users/photo/` |
| `POST /api/file-groups` | **404** | ❌ `Server with id 0 not found` |
| `POST /api/integrations/event-mappings` | **500** | ❌ `device_group_id: 0` 미처리 → **S4-02** |
| `POST /api/servers/categories` | **409** | ❌ `type_server 'VMS' already exists` — 실행 불가 example |
| `POST /api/devices/enclosures` | 201 | ⚠️ `name_device="string"` 쓰레기 레코드 생성 |
| `POST /api/reports/templates` | 201 | ⚠️ `name="string"` 쓰레기 템플릿 생성 |
| `POST /api/devices/groups` | 201 | ⚠️ "GOP 3구역" 생성(중복 가능) |
| `POST /api/users` | 201 | ⚠️ `operator01` 실계정 생성 |
| **`PUT /api/settings/session`** | **200** | 🔴 **X-01 — 운영 세션정책 즉시 변경** |
| **`POST /api/event-suppression-schedules`** | **201** | 🔴 **X-02 — 실제 억제창 생성** |

### 7.4 🔴 X-01 · 세션설정 Example 이 파괴적

`PUT /api/settings/session` 의 Example 을 그대로 Execute 하면 **200 으로 즉시 적용**된다.

| 필드 | 운영값(전) | Example 적용 후 |
|---|---|---|
| `session_timeout_hours` | 24 | **1** |
| `refresh_expiration_days` | 7 | **1** |
| `lockout_threshold` | 5 | **20** |
| `lockout_duration_minutes` | 30 | **1440** (24시간 잠금) |
| **`session_enabled`** | false | **true** |
| **`session_concurrency_policy`** | allow | **evict_all** ← 로그인 시 타 세션 강제축출 |
| `max_concurrent_sessions` | 0 | **100** |
| `session_history_retention_days` | 0 | **3650** |
| `login_anomaly_event_enabled` | false | **true** |
| `session_self_replace_enabled` | false | **true** |

**영향**: 문서를 열어본 사람이 호기심에 Execute 만 눌러도 **동시세션 정책이 evict_all 로 바뀌어 GIS/VMS 운영 세션이 축출**되고, 계정 잠금이 24시간으로 늘어난다.
**조치**: ① example 을 현행값과 동일한 무해값으로 교체 ② 또는 Swagger description 에 "본 엔드포인트는 즉시 운영 반영 — Example 그대로 실행 금지" 경고 명시.
※ 본 검증에서 변경분은 **전 항목 원복 확인** 완료.

### 7.5 🔴 X-02 · 억제 스케줄 Example 이 실제 억제창 생성

`POST /api/event-suppression-schedules` Example 은 `target_device_ids: [11,12,13]`, `window_start/end` 가 채워진 **실행 가능한 값**이라 그대로 **201 생성**된다 → 해당 장비 이벤트가 실제로 저장 억제된다.
**조치**: example 의 `window_start/window_end` 를 과거 시각으로 두거나(즉시 expired), 경고 문구 명시.
※ 생성분(id 54)은 soft-cancel → bulk-delete 로 **제거 확인**.

---

## 8. S2 디바이스 / S3 이벤트 상세

### S2-01 🟠 `number_device` UNIQUE 부재

동일 `number_device=90001` 로 제어기 2건 생성 성공(id 123·124). DB 확인:
```
Indexes: "ix_devices_number_device" btree (number_device)   ← UNIQUE 아님
```
대조군: 카메라 프리셋은 `preset_index` 중복 시 **409** 로 정상 차단 → 설계 의도가 아니라 **누락**.
**영향**: `number_device` 는 GIS·브로커가 장비를 지목하는 업무키. 중복 시 서브시스템이 다른 장비를 제어할 수 있다.

### S2-02 🟡 제어기 삭제 → 종속 센서 무경고 연쇄 삭제

`DELETE /api/devices/controllers/123` → **200 "Controller deleted successfully"**, 직후 종속 센서 125 는 **404**.
응답에 삭제된 하위 장비 수·경고가 전혀 없다. 센서 20대를 물린 제어기를 지우면 20대가 조용히 사라진다.

### S2-03 🟡 존재하지 않는 장비 할당이 조용히 성공

`POST /api/devices/groups/{id}/devices` 에 `device_ids:[999999]` → **200**, 그러나 `device_count` 불변(2→2). 클라는 성공으로 오인.
※ Swagger example 도 `[1, 101, 201]` 로 **실재하지 않을 수 있는 id** 를 제시.

### S3-01 🟠 통계 `time_bucket` 이 UTC (차트 9시간 왜곡)

실제 action 이벤트 8건의 `created_at`(KST): **15:43·15:47·15:47·15:52 / 16:00·16:04·16:04·16:36**
→ KST 15시대 4건 · 16시대 4건.

| 응답 필드 | 값 |
|---|---|
| `data.start_date` | `2026-08-06T13:29:50+09:00` (KST 라벨) |
| `data.series[].time_bucket` | **`2026-08-06 06`** = 4건 · **`2026-08-06 07`** = 4건 |

06/07 은 **UTC 시(=KST 15/16시)**. 한 응답 안에서 기간은 KST, 버킷은 UTC → **X축이 9시간 밀린다.**
`interval=day` 에서는 KST 오전 이벤트가 **전날 버킷**으로 떨어진다(기존 감사 F-1c 와 동일 뿌리, 시간 단위에서도 실측 확인).

### S3-02 🟠 OpenAPI 타입 선언이 실제 검증과 불일치

| 스키마 | 필드 | OpenAPI 선언 | 실제 서버 |
|---|---|---|---|
| `DetectionEventCreate` | `result` | `string` | **`EnumDetectionType`** — NONE·CABLE_CUTTING·CABLE_CONNECTED·PIR_SENSOR·THERMAL_SENSOR·VIBRATION_SENSOR·CONTACT_SENSOR·DISTANCE_SENSOR·AI_DETECT |
| `MalfunctionEventCreate` | `reason` | `string` | **`EnumFaultType`** — FAULT_CONTROLLER·FAULT_FENCE·FAULT_MULTI·FAULT_CABLE_CUTTING·FAULT_ETC |

자유 문자열을 넣으면 `Invalid enum value: '…' is not a valid EnumDetectionType` 로 422.
**.NET 클라 3종이 Swagger 를 계약 원천으로 쓰므로 반드시 정정 필요.**

### S3-03 🟠 이벤트매핑 중복 제약 비대칭

| 테이블 | UNIQUE 제약 | 중복 등록 시 |
|---|---|---|
| `event_mapping_lamps` | `uq_event_mapping_lamp (event_mapping_id, lamp_id)` | **500** (UniqueViolation 미처리 — 409여야 함) |
| `event_mapping_cameras` | **없음** | 201 (중복 허용 → 한 이벤트에 같은 카메라 2회 구동) |
| `event_mapping_speakers` | **없음** | 201 (동일) |

### S3-04 🟡 `interval` 미검증

`interval=minute`(미지원) → **200**, 응답은 `"interval":"minute"` 라고 echo 하지만 **실제 버킷은 hour**. 클라가 분 단위로 오해.

### S3-05 🟢 역순 기간 → 200

`start_date > end_date` → 200 + `total: 0`. 422 가 적절.

### S3-06 🟡 억제 PATCH 명시적 `null` → 500

`PATCH /api/event-suppression-schedules/{id}` 에 `{"name": null}` → **500**. (기존 감사에 기록된 미수정 항목 재확인)

### ✅ S2/S3 정상 확인

- 디바이스 6종 CRUD·enum 검증·404·연쇄삭제 동작
- Camera Settings / CameraPresets(중복 409) / ROIs(최소 3점 422) / XyPoints(replace) 전 구간 정상
- **v6.3.2 억제 PATCH 500 수정 회귀 PASS** — 이름만 변경·대상 교체·**겹치는 대상 교체**([12,13]→[13,14]) 전부 200
- 억제 검증 정상: 역순창 422 · 잘못된 target_type 422 · device 인데 ids 빈배열 422 · 단수 `target_device_id` 422(`extra=forbid`)
- bulk-delete 보호 정상: active/pending 은 `skipped_ids`, cancelled/expired 만 `deleted_ids`
- 이벤트 시각 처리 정상: `created_at` naive KST 입력 → `+09:00` 정확 반향

---

## 9. S4 서버 / 통합

### S4-01 🟠 카테고리 삭제가 소속 서버를 CASCADE 삭제

`DELETE /api/servers/categories/1` (VMS, 소속 서버 2대 보유) → **200 "deleted successfully"**.
DB 확인: `servers_category_id_fkey ... ON DELETE CASCADE` → 서버 15 → 13 대로 감소.
응답에 **경고도, 삭제된 서버 수도 없다.**
**조치**: 소속 서버가 있으면 409 차단(또는 `?force=true` 명시 요구) + 삭제 건수 반환.
※ 본 검증분은 시드 자가치유(MANDATORY VMS)로 복구 확인.

### S4-02 🟡 `device_group_id: 0` → 500

`POST /api/integrations/event-mappings` 에 `device_group_id: 0` → **500**. `null` 은 201 정상.
(Swagger Example 이 바로 `0` 이라 **문서대로 실행하면 500**)

### S4-03 🟡 메트릭 검증 공백

- `cpu_usage: 150`, `memory_usage: -5` → **201** (0~100 범위 제약 없음)
- 요청 필드는 **`ram_usage`** 인데 `memory_usage` 를 보내면 **조용히 폐기**(응답 `ram_usage: null`) — `extra=forbid` 아님
- 빈 바디 `{}` → 201 (전 필드 null 행 생성)

### ✅ S4 정상 확인

- **v6.3.1 `server_metrics` tz 수정 회귀 PASS** — aware `13:36:03+09:00` 전송 → `13:36:03+09:00` 반향 (수정 전엔 500)
- **`proxy-settings` PROXY 전용 강제 PASS** — VMS 서버 → `404 Server 21 is not a PROXY server; proxy-settings applies to PROXY servers only`
- 서버 CRUD·summary·system-events·404, 카테고리 `type_server` UNIQUE(409), enum 422 정상
- 함체 메트릭 저장/조회/최신/삭제 정상
- ⚠️ 관찰: 함체 메트릭 응답에서 `temperature`/`humidity` 는 **문자열**(`"25.5"`), `vibration` 은 **숫자**(10) — 타입 혼재

---

## 10. S5 리포트 / 시스템

### S5-01 🟠 `/api/logs` 잘못된 날짜 → 500

`GET /api/logs?start_date=notadate` → **500 Internal server error**.
원인: OpenAPI 상 `start_date` 가 `string|null` 로만 선언(`format: date-time` 없음) → FastAPI 파싱 미수행 → 핸들러 내부에서 파싱 실패.
(기존 감사 **F-3** 과 동일. v6.3.2 에서 **미수정** 재확인)

### S5-02 🟡 `acknowledge` 확인자 위조 가능

`POST /api/system-events/{id}/acknowledge` 는 **`acknowledged_by`(문자열) 를 필수로 요구**하고 그대로 기록한다.
인증 토큰의 실제 주체를 쓰지 않으므로 임의 이름으로 확인 처리가 가능 — 감사 무결성 약화.

### ✅ S5 정상 확인

- Reports: components·status·templates CRUD(`components` 는 `{id,order,enabled}` 객체 배열)·generate(202)·조회·미완료 preview 400·cancel 200·404 정상
- System Events: CRUD·summary·enum 422 정상
- FileGroups: CRUD + **복합 UNIQUE(server_id, group_id) 409** 정상
- Thumbnails: 업로드 201 → 메타/ID다운로드/파일명다운로드 전부 200 `image/png`
- Tracking: health·points(keyset cursor)·sessions 정상
- `/api/logs/viewer` HTML 200, `/health`, `/` 정상
- ⚠️ 관찰: `GET /` 응답 `version: "1.0.0"` — 실제 API 버전 6.3.2 와 불일치

---

## 11. 검증 중 발생한 상태 변경 및 원복

| 항목 | 조치 |
|---|---|
| 세션설정(Example 실행으로 10필드 변경) | **전 항목 원복 확인** (timeout 24 / refresh 7 / lockout 5·30 / enabled false / allow / 0 / 0 / false / false) |
| 억제 스케줄 id 54(Example 생성) | soft-cancel → bulk-delete, **목록 0건 확인** |
| 테스트 계정 12건·그룹 3건·디바이스 8건·이벤트 5건·서버 1건·템플릿 1건·썸네일 1건 | **전량 삭제 확인** (계정 13·그룹 5·디바이스그룹 3 원복) |
| VMS 카테고리(S4-01 재현으로 삭제) | 컨테이너 재기동 → 시드 자가치유(`VMS-ab1120`/`ab1121` 원본값 재생성) |
| `lockout_threshold` 임시 변경 | 5 로 원복 |

### ⚠️ 원복하지 않은 항목 — **동시 세션 작업분**

검증 중 `servers` 가 15 → 5 로 감소한 것을 발견해 추적한 결과, **본 검증의 결과가 아니다**:

- API `DELETE` 기록 없음(해당 구간 DELETE 8건 전부 다른 리소스)
- `app/utils/init_server_data.py` · `app/config.py` · `docker-compose.yml` · `tests/test_server_seed.py` 가 **2026-08-07 14:05 수정(미커밋)**
- 컨테이너 env 에 신규 게이트 **`INIT_SERVER_DEMO=false` / `INIT_SERVER_MANDATORY=true` / `INIT_SERVER_CATEGORIES=true`** 존재
- 컨테이너가 **14:31 재기동**(본인 조작 아님)

→ **동시 세션이 시드 게이팅 기능을 개발·검증 중**이며 데모 서버 제거는 그 작업의 일부로 판단. 남은 5대는 정확히 **MANDATORY 4유형**(PROXY·VMS·NVR_API·BROKER)에 대응. **임의 복구하지 않고 보존**했다.

---

## 12. 권고 조치 (PM 결정 필요)

| 순위 | 항목 | 규모 |
|---|---|---|
| 1 | **X-01/X-02** — 파괴적 Example 무해화 + 경고 문구 | Swagger example 2곳 |
| 2 | **A-01/A-02** — `_kst_now()` 정리 + `.replace(tzinfo=)` → `to_display()` | `auth.py` 4곳 |
| 3 | **S3-01** — 통계 버킷을 KST 기준으로 (`AT TIME ZONE` 명시) | 통계 서비스 |
| 4 | **S4-01** — 카테고리 삭제 시 소속 서버 보유하면 409 | `server_categories` 라우터 |
| 5 | **S3-02** — `result`/`reason` 스키마를 실제 enum 으로 선언 | 이벤트 스키마 2곳 |
| 6 | **A-03** — 자기삭제 409 차단 (또는 감사 선기록/actor 익명화) | `users.py` |
| 7 | **S2-01** — `number_device` UNIQUE 부여 여부 결정(기존 중복 정리 동반) | 마이그레이션 |
| 8 | **S5-01** — `/api/logs` 날짜 파라미터 `Optional[datetime]` 승격 | `logs.py` 4줄 |
| 9 | **S3-03** — 카메라/스피커 UNIQUE 추가 or 램프 500→409 (정책 통일) | 마이그 or 라우터 |
| 10 | **X-03** — placeholder example 39건 현실값으로 교체 | 스키마 `json_schema_extra` |

---
