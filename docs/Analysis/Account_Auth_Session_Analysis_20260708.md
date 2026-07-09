# GOP API 서버 Account·인증·세션 집중 분석

**작성일**: 2026-07-08  
**대상 버전**: Swagger `6.0.0`  
**분석 범위**: AccountUser, UserGroup, UserGroupGrant, JWT, Session, RBAC, Audit, Session Settings, NATS revoke  
**검증 방식**: 코드·Swagger·CHANGELOG·PostgreSQL 실행 데이터·선택 테스트 교차 검증

---

## 1. 결론

Account 영역은 최근 v5.0~v6.0에서 기능적으로 크게 확장됐다.

- Legacy User 제거 및 `AccountUser` 단일화
- ADMIN/USER 2단계 role
- UserGroup permissions matrix
- 기간성 UserGroupGrant
- JWT access/refresh rotation
- DB 기반 token blacklist
- 세션 강제 로그아웃과 NATS revoke
- 런타임 세션·잠금 설정
- 마지막 ADMIN 보호와 권한상승 방지 가드
- AuditLog/UserLoginLog 기록

설계 방향 자체는 좋다. 특히 `ADMIN=전권 bypass`, `USER=기본 그룹 ∪ 기간성 Grant` 구조와 Grant를 요청 시점에 계산하는 방식은 합리적이다.

그러나 현재는 **DB의 계정·세션 상태와 실제 JWT 효력이 일치하지 않는 경로가 여러 개** 존재한다. 잠금·비활성화·세션 종료가 DB 표시만 바꾸고 기존 토큰을 계속 허용하거나, 비활성 세션의 refresh token이 새 access token을 발급할 수 있다.

| 우선순위 | 핵심 문제 | 영향 |
|---|---|---|
| **P0** | 로그인·refresh·비밀번호 요청 body가 API 로그에 평문 저장되고 로그 API가 무인증 공개 | 계정·토큰 즉시 탈취 가능 |
| **P0** | strict 인증 dependency가 `is_active`, `is_locked`, session 상태를 확인하지 않음 | 잠금·비활성 계정의 기존 JWT 계속 사용 가능 |
| **P0** | refresh가 사용자 상태와 활성 세션을 검증하기 전에 새 토큰 발급 | 종료·만료 세션 부활 가능 |
| **P0** | 로그인 중복 세션 정리가 access JTI만 폐기하고 refresh JTI는 남김 | 이전 기기 refresh로 재로그인 가능 |
| **P0** | 고정 ADMIN 9계정·공개 기본 비밀번호·개발 JWT 키 | 신규/오설정 운영 서버 전체 탈취 가능 |
| **P1** | lock/deactivate/reset-password/내 세션 종료 경로의 token family 폐기 불완전 | UI 상태와 실제 권한 불일치 |
| **P1** | 비활성 UserGroup, `device_groups`, `time_restriction`이 실제 인가에 반영되지 않음 | 설정은 존재하지만 보안 효과 없음 |
| **P1** | UserGroup 감사 기록이 잘못된 async 함수 사용으로 저장되지 않을 가능성 | 권한 변경 감사 공백 |
| **P1** | token blacklist 정리 scheduler가 연결되지 않아 만료 행 누적 | DB 증가 및 문서·실행 불일치 |

Account 영역은 기능 추가보다 먼저 **세션 권위 모델을 하나로 정리하고 모든 폐기 경로를 공통 서비스로 통합**해야 한다.

---

## 2. Account 시스템 구성

### 2.1 주요 컴포넌트

| 컴포넌트 | 역할 |
|---|---|
| `AccountUser` | 로그인 계정, role, 기본 group, 잠금·활성 상태 |
| `UserGroup` | module×verb permissions 및 device group 범위 |
| `UserGroupGrant` | 특정 사용자에게 권한그룹을 기간성으로 추가 부여 |
| `UserSession` | access/refresh token pair와 접속 정보·만료 상태 |
| `TokenBlacklist` | 폐기된 JWT JTI 저장 |
| `UserLoginLog` | 로그인·로그아웃·강제 로그아웃 이력 |
| `AuditLog` | 사용자·그룹·권한·세션 관리 행위 감사 |
| `AppSettings` | 세션 timeout, refresh 기간, lockout threshold |
| NATS revoke | 클라이언트에 세션 폐기를 빠르게 통지하는 보조 경로 |

주요 파일:

- [`app/models/user.py`](../../app/models/user.py)
- [`app/routers/auth.py`](../../app/routers/auth.py)
- [`app/routers/users.py`](../../app/routers/users.py)
- [`app/routers/user_groups.py`](../../app/routers/user_groups.py)
- [`app/routers/user_sessions.py`](../../app/routers/user_sessions.py)
- [`app/routers/grants.py`](../../app/routers/grants.py)
- [`app/services/token_blacklist_service.py`](../../app/services/token_blacklist_service.py)
- [`app/services/settings_service.py`](../../app/services/settings_service.py)
- [`app/services/nats_revoke_publisher.py`](../../app/services/nats_revoke_publisher.py)

### 2.2 전체 인증 흐름

```text
POST /api/auth/login
        │
        ├─ AccountUser 조회·상태 확인·bcrypt 검증
        ├─ 기존 활성 세션 DUPLICATE 처리
        ├─ UserSession placeholder INSERT/flush
        ├─ sid 포함 access/refresh JWT 발급
        ├─ UserSession에 token pair 저장
        └─ 기본 group ∪ 활성 grant 권한 반환

Authorization: Bearer access_token
        │
        ├─ JWT 서명·exp 검증
        ├─ JTI blacklist 검사
        ├─ AccountUser 조회
        └─ role/group/grant permission 검사

POST /api/auth/refresh
        │
        ├─ refresh JWT/type/JTI 검사
        ├─ 기존 refresh JTI blacklist 등록
        ├─ 같은 sid로 access/refresh 재발급
        └─ 활성 session이면 token pair 갱신
```

현재 결함은 마지막 흐름에서 **session을 찾지 못해도 발급 결과를 취소하지 않는 것**과, 인증 dependency에서 **계정·세션 상태를 확인하지 않는 것**이 핵심이다.

---

## 3. API 인벤토리

Swagger 기준 Account 관련 operation은 총 **37개**다.

### 3.1 Authentication — 5개

| Method | Path | 기능 |
|---|---|---|
| POST | `/api/auth/login` | 로그인 및 token pair 발급 |
| POST | `/api/auth/logout` | 현재 token family 폐기 |
| POST | `/api/auth/refresh` | refresh rotation |
| GET | `/api/auth/me` | 현재 사용자 정보 |
| GET | `/api/auth/me/permissions` | 현재 유효 권한 snapshot |

### 3.2 Users — 13개

- 사용자 목록·상세·생성·수정·삭제
- 잠금·잠금 해제
- 관리자 비밀번호 초기화
- 본인 정보 수정
- 본인 비밀번호 변경
- 본인 프로필 사진 업로드·조회

### 3.3 UserGroups — 7개

- 그룹 목록·상세·생성·수정·삭제
- 그룹 permissions 전체 교체
- 그룹 소속 사용자 목록

### 3.4 UserSessions — 6개

- 전체 세션 목록
- 세션 상세
- 사용자 전체 세션 강제 로그아웃
- 단일 세션 강제 로그아웃
- 내 세션 목록
- 내 세션 종료

### 3.5 Grants — 4개

- 사용자별 Grant 생성·조회
- 전체 Grant 목록
- Grant soft revoke

### 3.6 Session Settings — 2개

- 설정 조회
- 설정 전체/부분 갱신

### 3.7 API 계약 상태

37개 중 대부분은 Swagger security 표시가 있다. 공개 경로는 login, refresh, profile photo다.

하지만 37개 중 `GET /api/auth/me` 정도만 명시적인 response model을 사용하며, 다수 endpoint가 raw dict를 반환한다. 따라서 Swagger가 성공 응답 구조를 충분히 설명하지 못하고 Account API 간 envelope도 완전히 통일되지 않는다.

예:

- `/api/auth/me` → `AccountUserResponse` 객체 직접 반환
- `/api/users/me` → `{success, data}` envelope
- 일부 DELETE → `{success, message, data}`
- 일부 auth 응답 → response model 없음

---

## 4. 데이터 모델 분석

### 4.1 AccountUser

핵심 필드:

- `login_id`, `password_hash`
- 사용자 프로필 정보
- `role`: ADMIN 또는 USER
- `group_id`: 기본 권한 그룹
- `is_active`, `is_locked`
- 잠금/비밀번호/마지막 로그인 메타데이터

장점:

- 비밀번호는 bcrypt hash로 저장
- Legacy `users` 모델 제거
- `group_id` 삭제 시 SET NULL
- session/grant는 사용자 삭제 시 CASCADE

문제:

- `password_changed_at`, `password_expires_at`, `last_login_at`, `last_login_ip`, `locked_by`가 실질적으로 갱신되지 않는다.
- role은 DB String이라 직접 DB 변경 시 임의값 저장 가능하다.
- email은 EmailStr 검증이 아니라 일반 문자열이다.

### 4.2 UserSession

세션 행에 다음이 저장된다.

- access token 원문
- refresh token 원문
- IP/User-Agent
- `expires_at`
- active/logout 상태

장점:

- sid와 DB session id를 연결
- force logout 대상을 정확히 식별 가능
- access/refresh pair rotation 가능

위험:

- DB 또는 로그 접근자가 bearer token 원문을 그대로 획득할 수 있다.
- token 원문을 unique/index 컬럼으로 저장해 DB 크기와 인덱스 비용이 커진다.
- session을 권위로 쓸지 JWT+blacklist를 권위로 쓸지가 코드 경로마다 다르다.

권장 모델:

- DB에는 access/refresh 원문 대신 JTI 또는 token hash만 저장
- `session_id`, `access_jti`, `refresh_jti`, `refresh_token_hash`, `expires_at`, `refresh_expires_at` 분리
- 모든 인증 요청에서 최소 `sid` 기반 session 상태를 확인하거나, 폐기 경로가 항상 JTI를 원자적으로 blacklist하도록 강제

### 4.3 UserGroup과 permissions

permissions 형태:

```json
{
  "modules": {
    "users": {"view": true, "edit": false},
    "reports": {"view": true}
  },
  "device_groups": [1, 2],
  "time_restriction": {}
}
```

실제 EnumPermissionModule은 12개다.

- devices
- events
- reports
- cameras
- users
- user_groups
- audit_logs
- servers
- map
- broadcast
- setup_system
- setup_feature

문제:

- 일부 docstring은 아직 8개라고 설명한다.
- `UserGroup.is_active=false`가 실제 permission 계산에서 무시된다.
- `device_groups`는 권한 payload에는 포함되지만 장치/이벤트 query 범위에 적용되지 않는다.
- `time_restriction`은 입력·저장만 되고 집행되지 않는다.

### 4.4 UserGroupGrant

장점:

- 권한을 그룹 정의가 아닌 사용자-그룹 assignment에 기간성으로 부여
- `valid_from <= now < valid_until`을 요청 시점에 계산
- sweep 지연과 무관하게 만료 권한을 즉시 차단
- soft revoke와 감사 정보 보존

개선점:

- 같은 사용자·그룹의 중복/겹치는 Grant 생성이 가능하다.
- base group 또는 grant group이 inactive여도 권한이 유효하다.
- Grant NATS 통지는 `NATS_REVOKE_ENABLED`와 같은 switch를 공유한다.
- 그룹 permissions 변경 시 해당 그룹 사용자들에게 permissions.changed가 발행되지 않는다.

### 4.5 TokenBlacklist

장점:

- JTI unique index
- access/refresh 구분
- revoke reason 제공
- 60초 in-memory cache

문제:

- 주석은 1시간 cleanup scheduler를 설명하지만 실제 scheduler 등록이 없다.
- 실DB 388행 중 357행이 이미 만료된 상태로 남아 있었다.
- 다중 worker/replica에서는 process-local negative cache가 최대 60초 stale할 수 있다.
- `add_to_blacklist*()`가 내부에서 commit하여 상위 세션 종료 트랜잭션을 여러 조각으로 나눈다.

---

## 5. 로그인·토큰·세션 상세 분석

### 5.1 로그인

현재 로그인은 다음을 수행한다.

1. login_id 조회
2. active/locked 확인
3. bcrypt 검증
4. 실패 횟수 증가 및 임계 도달 시 잠금
5. 기존 활성 세션을 DUPLICATE 처리
6. 새 session id 생성
7. sid 포함 access/refresh 발급
8. UserLoginLog SUCCESS 기록
9. 유효 permissions 반환

좋은 점:

- 오류 메시지는 사용자 부재/비밀번호 오류에 동일 문자열 사용
- bcrypt 사용
- sid가 refresh에서도 유지됨
- 로그인 시 permissions snapshot 제공

문제:

- `async def` 안에서 sync Session과 sync bcrypt를 실행하여 event loop를 막는다.
- 존재하지 않는 login_id는 bcrypt를 수행하지 않아 timing enumeration 가능성이 있다.
- 실패 로그인 UserLoginLog를 기록하지 않는다.
- 성공 로그인 시 `failed_login_count`를 0으로 초기화하지 않는다.
- 성공 로그인 시 `last_login_at`, `last_login_ip`를 갱신하지 않는다.
- 중복 세션 종료 시 access JTI만 blacklist하고 refresh JTI는 남긴다.
- blacklist service가 loop 내부 commit하여 로그인 트랜잭션이 원자적이지 않다.

### 5.2 인증 dependency

strict 인증 함수는 현재 다음만 확인한다.

- JWT 서명·exp
- JTI blacklist
- AccountUser 존재

다음을 확인하지 않는다.

- `AccountUser.is_active`
- `AccountUser.is_locked`
- token의 `sid`가 가리키는 UserSession 존재 여부
- UserSession `is_active`
- UserSession `expires_at`

optional 인증 함수는 active/locked를 확인하지만, 보호 endpoint 대부분은 strict 인증 함수를 사용한다.

결과적으로 관리자 API에서 계정을 잠그거나 비활성화해도 기존 access token이 blacklist되지 않았다면 계속 보호 API를 호출할 수 있다.

### 5.3 Refresh rotation

현재 refresh 흐름:

1. refresh JWT/type 검증
2. blacklist 확인
3. 사용자 존재 확인
4. 이전 refresh JTI blacklist
5. 새 access/refresh 생성
6. sid의 활성 session이 있으면 token pair 갱신
7. session이 없어도 새 token pair 반환

핵심 결함:

```text
session이 inactive/expired/not found
    → session update는 건너뜀
    → 그러나 새 access/refresh는 이미 발급됨
    → 새 access는 strict 인증 dependency를 통과함
```

또한 refresh는 사용자의 `is_active`, `is_locked`를 확인하지 않는다.

수정 원칙:

- 사용자 active/unlocked 필수
- sid 필수
- session 존재 + active + expires_at 정책 확인 필수
- DB session에 저장된 현재 refresh JTI/hash와 요청 token 일치 필수
- 조건 실패 시 rotation 전에 401
- JTI 교체를 하나의 DB transaction 또는 compare-and-swap으로 처리

### 5.4 Logout 및 강제 로그아웃

정상 구현된 경로:

- `/auth/logout`은 현재 session을 찾으면 access+refresh JTI를 폐기
- 관리자 단건/벌크 force logout은 access+refresh JTI 폐기
- NATS revoke는 server blacklist를 보조하는 빠른 통지 경로

불완전한 경로:

| 동작 | Session inactive | Access blacklist | Refresh blacklist | 문제 |
|---|:---:|:---:|:---:|---|
| 정상 logout | O | O | O | session을 못 찾으면 refresh 폐기 불가 |
| 강제 logout | O | O | O | TTL이 runtime 설정과 불일치 가능 |
| 로그인 DUPLICATE | O | O | **X** | 이전 refresh로 부활 가능 |
| 내 세션 종료 | O | **X** | **X** | 종료한 기기 token 계속 사용 가능 |
| 계정 잠금 | O | **X** | **X** | strict 인증도 locked 미검사 |
| 계정 비활성화 | 보장 없음 | **X** | **X** | 기존 token 계속 사용 가능 |
| 관리자 password reset | 보장 없음 | **X** | **X** | 이전 token 계속 사용 가능 |
| 본인 password 변경 | 다른 세션 O | 다른 세션 O | 다른 세션 O | 현재 세션 유지 정책은 명시 필요 |

### 5.5 Blacklist TTL 정합

최근 logout/refresh 일부는 runtime refresh 기간을 사용하도록 수정됐다. 그러나 다른 경로는 여전히 정적 설정을 사용한다.

- force logout: 정적 `JWT_EXPIRATION_HOURS`, `JWT_REFRESH_EXPIRATION_DAYS`
- password change: 정적 설정
- 일부 access logout: 정적 access 설정

`session_enabled=false`면 access/refresh token은 10년인데 blacklist TTL은 24시간/7일이 될 수 있다.

현재 cleanup scheduler가 없어 만료 blacklist 행도 계속 조회되므로 당장은 폐기 상태가 유지된다. 하지만 문서대로 cleanup을 연결하면 TTL 이후 장기 token이 다시 유효해질 수 있다.

가장 안전한 방법은 설정값으로 TTL을 추정하지 않고 **각 JWT의 실제 `exp` claim을 decode하여 blacklist.expires_at으로 저장하는 것**이다.

### 5.6 Refresh 동시성

동일 refresh token으로 동시 요청이 들어오면 두 요청 모두 초기 blacklist 조회를 통과할 수 있다. 이후 JTI unique insert에서 한 요청이 실패하거나, 구현 순서에 따라 둘 다 token을 생성하려 할 수 있다.

권장:

- refresh session row `SELECT ... FOR UPDATE`
- DB에 현재 refresh JTI/hash 저장
- 요청 JTI와 DB 현재값 compare-and-swap
- 성공한 한 요청만 새 JTI로 교체
- 재사용 감지 시 해당 session family 전체 revoke

---

## 6. 사용자·그룹·Grant·RBAC 분석

### 6.1 잘 구현된 부분

- self update schema에서 role/group/is_active 필드 제거
- Pydantic `extra=forbid`
- 비-ADMIN의 role/group 변경 차단
- 비-ADMIN의 ADMIN 대상 수정·삭제·잠금·비밀번호 초기화 차단
- Grant 생성·회수와 group permissions 변경은 base ADMIN 전용
- 사용자 삭제/강등 시 마지막 ADMIN 보존을 위해 row lock 사용
- permissions는 StrictBool과 Enum module key 사용
- Grant 만료는 요청 시점에 계산하여 scheduler에 보안을 의존하지 않음

### 6.2 비활성 그룹 미집행

`UserGroup.is_active`는 목록 필터와 수정에는 사용되지만 permission 계산은 해당 값을 확인하지 않는다.

따라서 그룹을 비활성화해도:

- 기본 group permissions 유지
- 해당 group을 부여한 Grant permissions 유지

관리자가 “비활성화”를 긴급 권한 차단으로 이해할 가능성이 높아 위험하다.

### 6.3 device_groups 범위 미집행

permissions의 `device_groups`는 로그인/권한 조회 응답으로 반환되지만 실제 장치·이벤트·매핑 query에 filter로 사용되지 않는다.

즉 클라이언트 UI가 숨길 수는 있어도 서버 API는 module permission만 있으면 다른 device group 데이터도 조회·수정할 수 있다.

서버측 row-level scope로 구현하거나, 필드가 단순 UI metadata라면 명칭과 문서를 변경해야 한다.

### 6.4 time_restriction 미집행

`PermissionsSchema.time_restriction`은 입력과 DB 저장이 가능하지만 auth/matrix 코드에서 사용되지 않는다. 보안 기능처럼 보이는 dead configuration이다.

구현 전까지 schema에서 제거하거나 `not_enforced`로 명확히 표시하는 편이 안전하다.

### 6.5 권한 변경 통지 누락

Grant 생성·회수·만료는 `permissions.changed`를 발행한다. 하지만 다음은 통지하지 않는다.

- 기본 `group_id` 변경
- group permissions 수정
- group 활성/비활성 변경
- group 삭제

서버 authorization은 매 요청 DB 계산이라 안전하지만, 클라이언트 permissions cache와 UI는 stale할 수 있다.

### 6.6 마지막 ADMIN 보호 범위

삭제·강등·비활성화에는 마지막 ADMIN 가드가 있다. 하지만 lock endpoint에는 동일 가드가 없다.

인증 dependency가 locked 상태를 올바르게 검사하도록 수정하면, 모든 ADMIN을 순차적으로 잠가 API 복구가 불가능한 상태를 만들 수 있다.

lock에도 마지막 활성 ADMIN 보호 또는 별도 break-glass 절차가 필요하다.

---

## 7. 감사·로그 분석

### 7.1 UserGroup 감사 기록 구현 오류

`user_groups.py`는 AsyncSession을 사용하면서 `log_action()`을 호출한다.

`log_action()`은 `async def`지만 내부에서 sync 방식으로 다음을 호출한다.

```python
db.commit()
db.refresh(audit_log)
```

AsyncSession에서는 두 호출이 coroutine이므로 await되지 않고 실제 감사 row가 저장되지 않을 수 있다. UserGroup 생성·수정·permissions 변경·삭제 네 경로가 영향을 받는다.

동일 서비스에 정상 AsyncSession용 `log_action_async()`가 있으므로 import/call을 교체해야 한다.

### 7.2 실패 로그인 감사 부재

로그인 성공은 UserLoginLog를 남기지만 다음 실패는 남기지 않는다.

- 존재하지 않는 사용자
- 잘못된 비밀번호
- inactive account
- locked account

failed_login_count만으로는 공격 IP/User-Agent/시간 분석이 어렵다.

### 7.3 API 로그의 Account 비밀정보 노출

실환경 확인:

```text
GET /api/logs → 무인증 200
GET /api/logs/viewer → 무인증 200
로그인 로그 476건 중 474건 body에 password 키 포함
```

Account 관점에서 가장 먼저 수정해야 할 문제다.

저장 금지 대상:

- login password
- current/new/reset password
- access token
- refresh token
- Authorization header
- 장치 user_password

---

## 8. 세션 설정 분석

현재 runtime 설정:

| 설정 | 실DB 값 | 적용 상태 |
|---|---:|---|
| `session_timeout_hours` | 12 | login/access/session expiry에 적용 |
| `refresh_expiration_days` | 7 | refresh 발급에 적용 |
| `lockout_threshold` | 5 | 로그인 실패 잠금에 적용 |
| `session_enabled` | true | false면 10년 token 발급 |

장점:

- DB 설정이 권위
- 입력 범위 제한
- JWT secret과 algorithm은 runtime 편집 불가
- 설정 cache invalidation 구현

문제:

- cache가 process-local이라 멀티 worker/replica 변경 전파가 없다.
- `session_enabled=false`가 access token까지 10년으로 만든다.
- 모든 blacklist 경로가 runtime expiry를 일관되게 사용하지 않는다.
- refresh에서 session expiry 자체를 강제하지 않는다.

권장:

- access token은 15분~1시간 등 짧게 유지
- session/refresh만 장기화
- setting version 또는 PostgreSQL NOTIFY로 cache 무효화
- prod에서 session_enabled=false 제한

---

## 9. NATS Account 통지 분석

### 9.1 Session revoke

Subject:

```text
sensorway.{unit}.account.{user_id}.session.{session_id}.revoke
```

특징:

- per-session subject
- HMAC-SHA256 signature
- message id, sid, jti, user id, reason, issued_at
- 실패해도 DB blacklist 권위를 유지하는 best-effort

### 9.2 Permissions changed

Subject:

```text
sensorway.{unit}.account.{user_id}.permissions.changed
```

Grant 생성·회수·만료 후 클라이언트가 `/api/auth/me/permissions`를 다시 조회하도록 유도한다.

### 9.3 운영 상태

기본 `NATS_REVOKE_ENABLED=false`라 현재 revoke와 permissions.changed 모두 발행되지 않는다.

서버 보안은 NATS가 아니라 DB blacklist와 request-time permission 계산에 의존하므로 원칙적으로 맞다. 다만 앞서 확인한 blacklist/세션 경로 누락이 먼저 보완되어야 NATS를 꺼도 안전하다.

개선점:

- revoke와 permissions changed 활성 switch 분리
- 매 publish마다 NATS connect하지 않고 lifespan connection pool 사용
- publish 성공/실패 metric
- 그룹 permissions 변경에도 영향 사용자별 통지

---

## 10. 실행 데이터와 테스트 결과

### 10.1 PostgreSQL 현황

개인정보 값은 조회하지 않고 집계만 확인했다.

| 항목 | 수량 |
|---|---:|
| ADMIN active/unlocked | 9 |
| USER active/unlocked | 4 |
| 전체 UserSession | 355 |
| 활성 UserSession | 1 |
| TokenBlacklist | 388 |
| 만료된 TokenBlacklist | 357 |
| UserGroupGrant | 4 |
| 현재 유효 Grant | 0 |

### 10.2 선택 테스트

다음 순수/격리 테스트는 통과했다.

- 권한상승 가드
- Grant 파생 상태
- revoke payload signature
- permissions.changed payload

결과: **24 passed**

다만 전체 `tests/`는 Git에 추적되지 않고 async fixture 일부가 운영 PostgreSQL을 직접 사용하므로 전체 회귀의 재현성은 보장되지 않는다.

### 10.3 확인되지 않은 항목

운영 계정을 잠그거나 refresh를 재사용하는 실DB 파괴적 E2E는 수행하지 않았다. 해당 결함은 코드 경로 분석으로 확정했으며 수정 후 전용 test DB에서 검증해야 한다.

---

## 11. 문제 목록과 우선순위

### 11.1 P0

#### ACC-P0-01. Account 요청 비밀정보가 공개 API 로그에 저장됨

- 로그인 password와 refresh token 저장 가능
- 무인증 로그 조회 가능
- 즉시 endpoint 차단·redaction·기존 데이터 정리 필요

#### ACC-P0-02. 잠금·비활성 계정의 기존 access token을 strict 인증이 허용함

- strict dependency에서 user active/locked 미검사
- lock은 token blacklist 미등록
- deactivate도 token family 미폐기

#### ACC-P0-03. 비활성/만료 session refresh가 새 token을 발급할 수 있음

- refresh는 session 확인 전에 token 생성
- session을 찾지 못해도 token 반환
- 사용자 active/locked 미검사

#### ACC-P0-04. 중복 로그인 이전 refresh token이 폐기되지 않음

- access만 blacklist
- old refresh는 active session 검증 없는 refresh API로 부활 가능

#### ACC-P0-05. 고정 ADMIN 계정·기본 키

- 9개 ADMIN 고정 비밀번호
- dev JWT/revoke key 허용
- 운영 fail-fast 필요

### 11.2 P1

#### ACC-P1-01. Session 종료 경로가 서로 다른 폐기 규칙 사용

공통 `revoke_session_family()` 서비스로 통합해야 한다.

#### ACC-P1-02. Blacklist TTL이 실제 JWT exp가 아니라 설정값 추정

JWT `exp`를 직접 저장해야 한다.

#### ACC-P1-03. UserGroup 비활성·device scope·time restriction 미집행

UI metadata와 server authorization의 경계를 재정의해야 한다.

#### ACC-P1-04. UserGroup AuditLog 저장 오류

`log_action` → `log_action_async` 교체 및 회귀 테스트 필요.

#### ACC-P1-05. Token blacklist cleanup scheduler 미등록

현재 만료 row가 계속 누적된다.

#### ACC-P1-06. Auth 핵심 경로 sync I/O

login/logout/refresh/me/permissions를 완전 async화하고 bcrypt는 threadpool로 보내야 한다.

#### ACC-P1-07. Refresh rotation race

session row lock 및 compare-and-swap 필요.

#### ACC-P1-08. 마지막 ADMIN lockout 보호 누락

lock endpoint에도 마지막 활성 ADMIN 가드 필요.

#### ACC-P1-09. 실패 로그인 추적·rate limit 부족

- 실패 UserLoginLog 기록
- IP/user 기반 rate limit
- exponential delay
- known account lockout DoS 완화

#### ACC-P1-10. Session token 원문 DB 저장

JTI/hash 저장 방식으로 변경 권장.

### 11.3 P2

#### ACC-P2-01. 비밀번호 정책이 최소 6자뿐임

- 길이 상향
- 유출 비밀번호/공통 비밀번호 차단
- history 또는 최소 변경 검증
- 관리자 reset 후 임시 비밀번호 변경 요구 검토

#### ACC-P2-02. 사용되지 않는 계정 메타 필드

password 변경/만료, last login, locked_by 필드를 실제로 갱신하거나 제거한다.

#### ACC-P2-03. Account 성공 응답 OpenAPI schema 부족

37개 operation에 response model을 일관되게 선언한다.

#### ACC-P2-04. 공개 프로필 사진

UUID 기반 비공개성은 접근제어가 아니다. PII 정책에 따라 인증 필요 여부를 결정해야 한다.

#### ACC-P2-05. `/auth/me`와 `/users/me` 중복

역할과 response envelope를 명확히 분리하거나 하나로 통합한다.

---

## 12. 권장 개선 설계

### 12.1 인증 권위 모델 통일

권장 request 인증 조건:

```text
JWT signature/exp valid
AND jti not blacklisted
AND AccountUser exists, active, unlocked
AND sid exists
AND UserSession exists, active
AND session.user_id == user.id
AND session expiry policy valid
```

DB 조회 비용이 우려되면 session version 또는 `token_version`을 AccountUser/JWT에 포함하고 짧은 TTL cache를 사용할 수 있다. 하지만 잠금·강제 로그아웃의 최대 지연 시간을 명확히 해야 한다.

### 12.2 공통 token family revoke 서비스

모든 폐기 경로가 다음 하나를 호출하도록 한다.

```python
async def revoke_session_family(
    db,
    session,
    reason,
    actor_id=None,
    publish_nats=True,
    commit=False,
):
    # access/refresh 실제 exp 추출
    # 두 JTI blacklist UPSERT
    # session inactive/logged_out/reason
    # 감사 snapshot 생성
    # caller transaction에 참여
```

적용 대상:

- logout
- duplicate login
- self session terminate
- force logout single/bulk
- account lock/deactivate
- admin password reset
- self password change
- refresh reuse detection

### 12.3 Refresh rotation 원자화

```text
BEGIN
SELECT session FOR UPDATE
검증(user/session/current refresh hash)
old refresh revoke
new access/refresh 생성
session current JTI/hash 교체
COMMIT
```

NATS 통지는 commit 후 실행한다.

### 12.4 Permission scope 집행

- group `is_active=true` 필수
- Grant group도 active 필수
- `device_groups`를 query/filter 및 mutation target 검증에 적용
- `time_restriction` 구현 전 입력 금지
- group permissions 변경 시 영향 사용자 cache invalidation

### 12.5 Audit 원자성

현재 business commit 후 AuditLog를 별도 commit하는 경로가 많다. 감사가 필수라면 business row와 audit row를 같은 transaction에 넣고 최종 한 번만 commit해야 한다.

---

## 13. 수정 순서

### 즉시

1. `/api/logs` 보호 및 Account secret redaction
2. strict 인증에서 active/locked 확인
3. refresh에서 active session/user 확인 후 발급
4. duplicate login refresh JTI 폐기
5. lock/deactivate/reset/self-session 종료 token family 폐기
6. 운영 관리자 비밀번호와 JWT/revoke key 교체

### 다음 배포

1. 공통 revoke service 도입
2. JWT 실제 exp 기반 blacklist TTL
3. refresh row lock/CAS
4. UserGroup audit async 수정
5. inactive group/device scope 집행
6. blacklist cleanup scheduler
7. 마지막 ADMIN lock guard
8. auth async 전환

### 중기

1. token 원문 → JTI/hash 저장 migration
2. multi-instance cache invalidation
3. Account OpenAPI response model 통일
4. 실패 로그인·rate limit·보안 metric
5. 테스트 Git 복원 및 전용 PostgreSQL integration 환경

---

## 14. 필수 회귀 테스트

| ID | 시나리오 | 기대 결과 |
|---|---|---|
| A01 | 잠긴 계정의 기존 access token | 401 |
| A02 | 비활성 계정의 기존 access token | 401 |
| A03 | 잠긴/비활성 계정 refresh | 401 |
| A04 | inactive/expired/missing sid session refresh | 401 |
| A05 | duplicate login 이전 access/refresh | 둘 다 401 |
| A06 | 내 다른 세션 종료 후 대상 access/refresh | 둘 다 401 |
| A07 | 관리자 password reset 후 모든 이전 token | 401 |
| A08 | 계정 lock/deactivate 후 모든 session family | 401 |
| A09 | 동시 refresh 2건 | 정확히 1건 성공 |
| A10 | refresh token 재사용 | session family 전체 revoke |
| A11 | runtime expiry 90일 token revoke | 실제 exp까지 blacklist 유지 |
| A12 | inactive group 사용자 | 해당 group permission 거부 |
| A13 | device_groups 범위 밖 리소스 접근 | 403 또는 결과 제외 |
| A14 | UserGroup permissions 변경 | AuditLog 저장 및 클라이언트 통지 |
| A15 | 마지막 활성 ADMIN lock | 409 |
| A16 | 성공 로그인 | failed count reset, last login 갱신 |
| A17 | 실패 로그인 | UserLoginLog FAILURE 기록 |
| A18 | API 로그 | password/token 값 미저장 |

---

## 15. 최종 평가

| 영역 | 평가 | 설명 |
|---|---|---|
| 계정 모델 | 좋음 | AccountUser 단일화와 관계 구조가 명확함 |
| 비밀번호 저장 | 좋음 | bcrypt 적용 |
| JWT 기본 구조 | 보통 | JTI/sid/rotation은 있으나 claim·session 검증 부족 |
| 세션 무효화 | 위험 | 경로별 구현 차이로 token 부활 가능 |
| RBAC 모델 | 좋음 | ADMIN bypass + group/grant 합집합 방향은 타당 |
| RBAC 집행 | 보통 이하 | inactive group/device scope/time restriction 미집행 |
| 감사 | 보통 이하 | UserGroup async 기록 오류와 실패 로그인 공백 |
| NATS revoke | 보통 | 계약은 좋으나 기본 비활성·통지 범위 누락 |
| 운영 보안 | 위험 | 공개 credential 로그와 고정 관리자 계정 |
| 테스트 | 위험 | 로컬 테스트가 Git 미추적이고 async fixture 불완전 |

Account의 가장 중요한 개선 목표는 “JWT가 유효한가”만 보는 구조에서 벗어나 **사용자 상태·세션 상태·token family가 하나의 권위 모델로 일관되게 움직이도록 만드는 것**이다. 이 작업이 끝나야 잠금, 강제 로그아웃, 세션 만료, 비밀번호 변경, 중복 로그인, 기간성 권한이 실제 보안 계약대로 동작한다.

---

## 16. 참고 자료

- [`CHANGELOG.md`](../../CHANGELOG.md)
- [`docs/PRD_Account_Design.md`](../PRD_Account_Design.md)
- [`docs/PRD_Account_Implementation.md`](../PRD_Account_Implementation.md)
- [`docs/PRD_UserSession_Improvement.md`](../PRD_UserSession_Improvement.md)
- [`docs/PRD_v5.0_Permission_Management.md`](../PRD_v5.0_Permission_Management.md)
- [`docs/PRD_Audit_Log.md`](../PRD_Audit_Log.md)

