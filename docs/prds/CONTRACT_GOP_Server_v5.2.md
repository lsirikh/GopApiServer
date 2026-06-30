# CONTRACT — GOP Server ↔ .NET Client v5.2

> **상태**: 서버측 구현 완료(로컬 PASS), 클라 짝 PRD 통지용 계약 버전 고정.
> **대상**: .NET 클라이언트팀 (Force-Logout / Session-Settings 짝 PRD)
> **서버 커밋**: `73ecc5e` (HEAD) — `f00f7ca`·`4ff9a05`·`785c313`·`73ecc5e`
> **기준 PRD**: [`PRD_GOP_Server_Force_Logout.md`](PRD_GOP_Server_Force_Logout.md) · [`PRD_GOP_Server_Session_Settings.md`](PRD_GOP_Server_Session_Settings.md)
> **작성일**: 2026-06-30 / **문서 버전**: v5.2-contract-1

---

## 0. 한눈 요약 (두괄식)

| 계약 | 핵심 | 변경 불가 |
|---|---|---|
| **C1 sid** | JWT `sid` 클레임 = `UserSession.id`. login/refresh 응답 `session_id` 필드로도 노출. refresh 시 **sid 고정·jti만 회전** | 클라 강제로그아웃 매칭키 |
| **C2 subject** | `sensorway.{unit}.account.{user_id}.session.{session_id}.revoke` — per-session 전용. **광역 `all.>`/와일드 발행 금지** | 클라는 자기 세션 subject만 subscribe |
| **C3 payload** | HMAC-SHA256 + 전용 `REVOKE_SIGNING_KEY`. canonical = sort_keys·compact·UTF-8·**null 명시**. `reason`=EnumLogoutReason 6종 | 골든벡터 §4 |
| **C4 401** | revoked 세션 접근 → **401** `error.code=SESSION_REVOKED` (403=권한부족과 구분) | error.code 리터럴 |

> ⚠️ **활성화 게이트**: 서버 NATS revoke 발행은 `NATS_REVOKE_ENABLED=False`(기본) 상태로 **미발행**. 무효화 권위는 **서버 DB 블랙리스트**이며, NATS 발행은 클라가 ≤60s 캐시 staleness 창을 건너뛰는 **가속 경로**일 뿐. 게이트 ON 전제조건은 §6 참조.

---

## 1. C1 — 세션 식별자 `sid`

- **정의**: JWT access/refresh 양쪽에 `sid` 클레임 = `UserSession.id`(정수의 문자열).
- **응답 노출**: `POST /api/auth/login`, `POST /api/auth/refresh` 응답 `data.session_id`.
- **불변성**: refresh 시 `sid`는 **승계(고정)**, `jti`만 회전. 세션 행은 새 토큰 쌍으로 재바인딩(orphan 방지).
- **레거시 호환**: `sid` 없는 옛 토큰은 점진 롤아웃 동안 허용(refresh 시 재바인딩 skip).

### login 응답 (발췌)
```json
{
  "success": true,
  "data": {
    "access_token": "…",
    "refresh_token": "…",
    "token_type": "bearer",
    "session_id": "42",
    "user": { "id": 7, "login_id": "...", "role": "...", "permissions": null }
  }
}
```

### refresh 응답 (발췌)
```json
{
  "success": true,
  "data": {
    "access_token": "…",
    "refresh_token": "…",
    "token_type": "bearer",
    "session_id": "42"
  }
}
```

> **클라 작업**: 로그인/리프레시 시 `data.session_id`를 보관 → 자신의 revoke subject(§2) 구독에 사용.

---

## 2. C2 — per-session revoke subject

```
sensorway.{unit}.account.{user_id}.session.{session_id}.revoke
```

| 토큰 | 값 출처 | 예시 |
|---|---|---|
| `{unit}` | 서버 `NATS_UNIT_ID` (기본 `unit001`) | `unit001` |
| `{user_id}` | AccountUser.id | `7` |
| `{session_id}` | `sid` = UserSession.id | `42` |

- **예시**: `sensorway.unit001.account.7.session.42.revoke`
- 클라는 **자기 세션 subject만** subscribe. 서버만 `account.>` publish(발행 ACL은 §6 B 전제).
- **광역 발행 금지**: `all.>` 등 fan-out subject 사용 안 함(피싱/오발행 표면 제거).

---

## 3. C3 — revoke payload + 서명

### 필드 (서명 포함 7개)
| 필드 | 타입 | 의미 |
|---|---|---|
| `message_id` | string(uuid) | 메시지 고유 id |
| `session_id` | string \| null | 무효화 대상 세션 |
| `jti` | string \| null | **있으면 그 세션만**, 없고 user_id 있으면 **그 사용자 전체** |
| `user_id` | int \| null | 대상 사용자 |
| `reason` | enum(string) | EnumLogoutReason 6종 (§3.1) |
| `issued_at` | string | **RFC3339 UTC `Z` 고정** `YYYY-MM-DDTHH:MM:SSZ` |
| `signature` | string(hex) | HMAC-SHA256, 서명 입력에서 **제외** |

### 3.1 EnumLogoutReason (free text/URL 금지)
`MANUAL` · `EXPIRED` · `FORCED` · `LOCKED` · `PASSWORD_CHANGED` · `DUPLICATE`

### 3.2 canonical (서명 입력) 규칙 — **양측 결정성 보장**
1. `signature` 필드 **제외**.
2. JSON 직렬화: **키 알파벳 정렬**(`sort_keys=True`), **공백 없음**(`separators=(",",":")`), `ensure_ascii=False` → **UTF-8 바이트**.
3. `null` 필드(jti/session_id 등)는 **생략하지 않고 명시**(`"jti":null`).
4. `signature` = `HMAC_SHA256(REVOKE_SIGNING_KEY, canonical_bytes)` 의 **소문자 hex**.
5. 검증은 **상수시간 비교**(`hmac.compare_digest`).

### 3.3 서명 키
- 전용 `REVOKE_SIGNING_KEY` — **`JWT_SECRET_KEY`와 반드시 분리**(재사용 시 클라가 access 토큰 위조 가능).
- 운영 키는 §6 B 배포 시 별도 전달(이 문서에 미포함).

---

## 4. 골든벡터 (클라 단위테스트용)

> **테스트 전용 키**: `dev-revoke-signing-key-change-in-production`
> 아래 canonical 문자열 → 위 키로 HMAC-SHA256 → signature 가 일치해야 클라 구현이 호환됨.

### V1 — per-session 무효화 (`jti` 있음 → 그 세션만)
```
canonical:
{"issued_at":"2026-06-30T12:00:00Z","jti":"aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee","message_id":"11111111-1111-1111-1111-111111111111","reason":"FORCED","session_id":"42","user_id":7}

signature:
b2f6f33862dc84cc902a062731c1a0ffd0e2d7e14f355bf829f8d7fa3367104b
```

### V2 — 사용자 전체 무효화 (`jti=null` → user 전체)
```
canonical:
{"issued_at":"2026-06-30T12:00:00Z","jti":null,"message_id":"22222222-2222-2222-2222-222222222222","reason":"PASSWORD_CHANGED","session_id":"42","user_id":7}

signature:
95ef24f57e12b25d31065a7c5266918c60eab2d27c050434589ad1a5df1dffd0
```

> 참고: V1·V2는 `jti` null 여부만 다르며, **null이 canonical에 명시**됨에 유의(V2 `"jti":null`).

---

## 5. C4 — 폐기 세션 401 + P2 세션설정 API

### 5.1 revoked 접근 응답
- revoked/블랙리스트 토큰으로 보호 자원 접근 → **HTTP 401**, 본문 `error.code = "SESSION_REVOKED"`.
- **403(권한부족)과 구분** — 클라는 `SESSION_REVOKED` 수신 시 **즉시 로그아웃 UI**로 전환(재시도 금지).

### 5.2 `GET /api/settings/session` (ADMIN 전용)
응답 `data`:
| 필드 | 타입 | 비고 |
|---|---|---|
| `session_timeout_hours` | int (1~168) | 편집 가능 |
| `refresh_expiration_days` | int (1~90) | 편집 가능 |
| `lockout_threshold` | int (**0 또는 3~20**) | 편집 가능(1~2 금지) |
| `session_enabled` | bool | 편집 가능 |
| `auth_mode` | string | **읽기전용**(.env 배포 전용) |
| `jwt_algorithm` | string | **읽기전용** |

> `jwt_secret`은 **절대 미노출**(NFR-SVS-03).

### 5.3 `PUT /api/settings/session` (ADMIN 전용)
- 편집 **부분집합만** 수용(미지정 필드 불변).
- 경계 위반 → **422**. 특히 `lockout_threshold`는 **0(비활성) 또는 3~20**만 허용(1~2 → 422).
- 효과: `app_settings` UPSERT + `ConfigChangeLog` 감사 + 캐시 무효화 + 런타임 만료/잠금 즉시 반영.
- 요청 예:
```json
{ "session_timeout_hours": 8, "lockout_threshold": 5 }
```

---

## 6. 클라 통지 + 활성화 전제(서버 잔여)

| 항목 | 주체 | 상태 |
|---|---|---|
| **B-1** subject 클라 `EffectiveSubject` 매칭 확인 (V-SVF-05) | 클라↔서버 | ⬜ 미확인 |
| **B-2** NATS 발행 ACL — 서버만 `account.>` publish, 클라 subscribe-only (FR-SVF-08) | 인프라 | ⬜ |
| **B-3** 운영 `REVOKE_SIGNING_KEY` 배포 + `NATS_REVOKE_ENABLED=true` | 서버 배포 | ⬜ (B-1·B-2 완료 후) |

> B-1·B-2 완료 전까지 서버는 **블랙리스트만** 수행(NATS 미발행). 클라는 게이트 OFF 동안에도 ≤60s 캐시 만료로 revoked 세션을 401로 인지 가능.

---

**검토 요청**: 위 C1~C4 + 골든벡터(§4) + P2 스키마(§5)를 클라 짝 PRD에 반영하고, §6 B-1(subject 매칭)을 회신 바랍니다.
