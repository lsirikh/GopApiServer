# API Server 전체 재검토 보고서

- 검토일: 2026-07-10
- 대상: `api-server`, PostgreSQL, `db-monitor`, `gis-ingest`, Docker Compose, OpenAPI/Swagger, 최근 `CHANGELOG.md`
- 기준 환경: Docker Compose 실행 중, API는 HTTPS `https://localhost:8000`, `AUTH_MODE=token`
- 이전 보고서: `docs/Analysis/API_Server_Overall_Review_20260708.md`, `docs/Analysis/Account_Auth_Session_Analysis_20260708.md`

## 1. 요약 결론

현재 API 서버는 v6.0 이후 상당히 많이 보강되어 있다. 특히 2026-07-09~10 사이에 이전 리뷰에서 나온 인증/세션/권한/DB SYNC 관련 항목 다수가 이미 수정됐다.

다만 현재 기준으로도 운영 전 확인해야 할 핵심 문제는 남아 있다.

| 우선순위 | 영역 | 결론 |
|---|---|---|
| P0 | 인증/인가 | `AUTH_MODE=token`인데도 일부 민감 GET API가 무인증 200으로 열린다. |
| P0 | 세션/토큰 | refresh 후 이전 access token이 orphan으로 남을 수 있다. force logout 시 현재 `session.token`만 기준으로 막으면 과거 access token은 exp까지 살아남을 수 있다. |
| P1 | 세션/토큰 | 공통 `session_revoke_service`가 생겼지만 `logout`, `user_sessions` force logout, 비밀번호 변경 일부 경로는 아직 직접 blacklist 구현을 사용한다. `session_enabled=false` 장기 로그인 모드와 결합하면 TTL 불일치 위험이 남는다. |
| P1 | NATS | DB 변경 SYNC는 정상 경로가 갖춰져 있으나, API 서버의 Force-Logout/permissions NATS publish는 compose 네트워크/env 구성이 빠져 있어 실제 활성화 시 실패 가능성이 높다. |
| P1 | 테스트/개발환경 | 현재 호스트/컨테이너 테스트 환경에서 pytest가 바로 실행되지 않는다. `DEBUG=release` 환경변수 충돌과 `aiosqlite` 누락이 확인됐다. |
| P2 | 운영 설정 | dev 환경이라 허용되지만, 현재 런타임은 기본 JWT secret, 기본 revoke signing key, CORS `*` 상태다. 운영 전 반드시 교체/제한 필요. |

`session_enabled=false` 자체는 “세션 만료 없이 계속 로그인 유지”라는 의도된 기능으로 보는 것이 맞다. 문제는 그 모드에서 토큰 회수/강제 로그아웃/refresh rotation이 같은 수명 모델로 일관되게 동작해야 한다는 점이다.

## 2. 현재 실행 상태

### 2.1 Docker Compose

확인 결과 주요 컨테이너는 실행 중이다.

| 서비스 | 상태 |
|---|---|
| `pids-api-server` | Up, healthy |
| `pids-api-postgres` | Up, healthy |
| `pids-api-db-monitor` | Up, healthy |
| `pids-api-gis-ingest` | Up |
| `pids-api-autoheal` | Up, healthy |
| `pids-api-db-admin` | Up |

API는 HTTP가 아니라 HTTPS로 응답한다.

- `http://localhost:8000/health` → empty reply
- `https://localhost:8000/health` → 200, `{ "status": "healthy", "auth_mode": "token", "db": "ok" }`

### 2.2 OpenAPI/Swagger

런타임 OpenAPI 기준:

| 항목 | 값 |
|---|---|
| title | GOP RESTful API Server |
| version | 6.0.0 |
| path count | 128 |
| operation count | 241 |
| security scheme | `BearerAuth` |
| 중복 method/path | 0건 |

주요 tag별 operation 수:

| 영역 | operation 수 |
|---|---:|
| Reports | 17 |
| Users | 13 |
| DeviceGroups | 9 |
| Event Mapping Cameras/Speakers/Lamps | 각 8 |
| Enclosures / Servers | 각 8 |
| Authentication | 5 |
| Settings / Audit Logs / Config Change Logs / Detection Logs / Logs | 각 2 |

### 2.3 현재 DB 설정

`app_settings` 기준:

| 설정 | 현재값 |
|---|---|
| `session_enabled` | `true` |
| `session_timeout_hours` | `12` |
| `refresh_expiration_days` | `7` |
| `lockout_threshold` | `5` |

계정/세션 요약:

| 항목 | 값 |
|---|---:|
| ADMIN 계정 | 9 |
| USER 계정 | 4 |
| locked 계정 | 0 |
| active user sessions | 0 |
| token blacklist rows | 47 |
| expired blacklist rows | 8 |

> 진단 중 생성된 admin 테스트 세션 `418`, `419`는 분석 종료 전에 `USER_LOGOUT` 처리하고 해당 token jti를 `DIAGNOSTIC_CLEANUP` 사유로 blacklist에 등록했다. `admin.failed_login_count`도 0으로 복구했다.

## 3. 기능 목록

### 3.1 인증/계정

- `/api/auth/login`
- `/api/auth/logout`
- `/api/auth/refresh`
- `/api/auth/me`
- `/api/auth/me/permissions`
- `/api/users`
- `/api/user-groups`
- `/api/grants`, `/api/users/{id}/grants`
- `/api/user-sessions`
- `/api/settings/session`

최근 반영된 주요 보강:

- active/locked 계정 기존 token 차단
- refresh 시 `sid`/세션 활성 검증
- refresh CAS로 동시 refresh race 완화
- 로그인 성공 시 실패 카운트 reset
- 실패 로그인 감사 기록
- inactive group 권한 미집행
- 마지막 ADMIN lockout 방지
- token blacklist cleanup scheduler 진입점 추가

### 3.2 장비/디바이스

- Controllers, Sensors, Cameras, Speakers, Enclosures, Lamps
- Device Groups / Device Group Mappings
- Camera Settings, Camera Presets, ROI, XY Points
- File Groups, Thumbnails
- Enclosure Metrics

### 3.3 이벤트/연동

- Detection, Malfunction, Connection, Action events
- Detection Logs
- System Events
- Event Statistics
- Event Mappings
- Mapping Cameras/Speakers/Lamps

### 3.4 서버/리포트/로그

- Server Categories, Servers
- Server Metrics
- Proxy Settings
- Reports / Report Templates / Report Generations / PDF preview/download
- Audit Logs
- Config Change Logs
- API Logs

### 3.5 NATS/DB 변경 감시

- PostgreSQL trigger → `pg_notify('gop_sync', payload)`
- `db-monitor` LISTEN `gop_sync` → NATS publish
- `gis-ingest` NATS subscribe → tracking history 저장
- API 서버 Force-Logout revoke publisher는 별도 `app/services/nats_revoke_publisher.py`

## 4. 최근 수정으로 해결된 것으로 확인된 항목

`CHANGELOG.md`와 현재 코드 기준으로 아래 항목은 이전 리뷰 이후 개선되어 있다.

| 항목 | 상태 |
|---|---|
| API 로그 무인증 조회 및 민감 body 평문 저장 | 보강됨: `/api/logs` 권한 부착, body redaction 추가 |
| system-events mutation 무인증 노출 | 보강됨: POST/PATCH/DELETE/acknowledge route guard 추가 |
| permission map stale contract | 보강됨: stale map contract test 추가 |
| DB monitor 재연결 부재 | 보강됨: liveness probe + supervised reconnect |
| subtype-only UPDATE NATS 미발행 | 보강됨: subtype table UPDATE trigger 추가 |
| api_logs 미래 partition 미생성 | 보강됨: startup/scheduler partition ensure |
| active/locked 계정 token 통과 | 보강됨: strict auth dependency에서 active/locked 확인 |
| lock/reset-password의 token family revoke | 상당 부분 보강됨: `session_revoke_service` 추가 및 `users.py` 일부 경로 적용 |
| refresh race | 보강됨: `with_for_update()` + current refresh token CAS |
| inactive group 권한 계속 적용 | 보강됨 |

## 5. 현재 남은 문제점

### P0-01. `AUTH_MODE=token`에서도 민감 GET API가 무인증으로 열린다

런타임 실측:

| 요청 | 무토큰 상태 |
|---|---:|
| `GET /api/users` | 401 |
| `GET /api/devices/cameras` | 401 |
| `GET /api/reports/templates` | 401 |
| `GET /api/config-change-logs` | 200 |
| `GET /api/config-change-logs/{id}` | 200 |
| `GET /api/system-events` | 200 |
| `GET /api/system-events/summary` | 200 |
| `GET /api/events/statistics/summary?start_date=...&end_date=...` | 200 |
| `GET /api/events/statistics/dashboard?start_date=...&end_date=...` | 200 |

원인:

- `app/security/matrix_enforcer.py`는 permission map에 없는 경로를 `default-allow` 한다.
- `app/routers/config_change_logs.py` GET 2종은 인증/인가 dependency가 없다.
- `app/routers/system_events.py`는 mutation만 guard가 있고 GET은 공개로 남아 있다.
- `app/routers/event_statistics.py`는 모든 GET에 인증/인가 dependency가 없다.

위험:

- `ConfigChangeLog`는 actor, resource, before/after state가 포함될 수 있어 운영 정보 누출 가능성이 있다.
- `SystemEvent`는 장애/보안 이벤트 정보가 포함될 수 있다.
- `EventStatistics`는 감시장비/이벤트 통계가 외부에 노출될 수 있다.

권고:

1. 운영 기준으로 아래 GET에 권한을 붙인다.
   - `config-change-logs`: `require_perm_async("audit_logs", "view")` 또는 별도 `config_logs:view`
   - `system-events`: `require_perm_optional_async("events", "view")` 또는 `servers:view`
   - `event-statistics`: `require_perm_optional_async("events", "view")`
2. `matrix_enforcer`를 `/api/*` default-deny + 명시 allowlist 방식으로 전환한다.
3. allowlist는 `/api/auth/login`, `/api/auth/refresh`, `/health`, `/`, 정적 이미지 다운로드 등으로 명시한다.
4. mutation contract뿐 아니라 “민감 GET contract” 테스트를 추가한다.

### P0-02. refresh 후 이전 access token이 orphan으로 남을 수 있다

현재 refresh 흐름:

- refresh token 검증
- old refresh jti만 blacklist
- 새 access/refresh 발급
- `UserSession.token`, `UserSession.refresh_token`을 새 값으로 overwrite

문제:

- refresh 전 access token jti는 blacklist되지 않는다.
- `UserSession.token`이 새 access token으로 덮이므로, 이후 force logout은 “현재 session.token”만 blacklist한다.
- 과거 access token이 탈취/보관되어 있으면 exp까지 계속 통과할 수 있다.
- 일반 요청의 `get_current_account_user*`는 `sid`가 가리키는 `UserSession.is_active`를 매번 확인하지 않는다. 즉 access token 자체가 blacklist되지 않으면 통과 가능성이 있다.

특히 `session_enabled=false`에서는 access token exp도 10년이므로 이 문제가 커진다.

권고:

1. refresh 시 기존 `session.token`의 access jti를 새 access 발급 전에 blacklist한다.
2. 또는 access token을 짧게 유지하고 refresh만 장기화한다.
3. 가장 확실한 방식은 인증 dependency에서 `sid` 기준 `UserSession.is_active`와 token family version을 확인하는 것이다.
4. 최소한 force logout 시 과거 access token까지 회수할 수 있도록 access token family history를 저장한다.

### P1-01. 공통 `session_revoke_service`가 일부 경로에만 적용되어 revoke TTL 정책이 흔들린다

좋은 점:

- `app/services/session_revoke_service.py`가 생겼고, token의 실제 `exp`를 읽어 blacklist TTL로 쓰는 방향이 맞다.
- `users.py`의 lock/reset 계열 일부는 이 서비스를 사용한다.

남은 문제:

- `app/routers/auth.py` logout은 여전히 access blacklist TTL을 `JWT_EXPIRATION_HOURS` 기준으로 계산한다.
- refresh token logout TTL도 `resolve_session_expiry()`가 아니라 `refresh_expiration_days` 설정값만 본다.
- `app/routers/user_sessions.py` bulk/single force logout은 `JWT_EXPIRATION_HOURS`, `JWT_REFRESH_EXPIRATION_DAYS` 기준 직접 구현을 사용한다.
- `app/routers/users.py`의 비밀번호 변경 시 다른 세션 무효화 경로도 직접 blacklist 구현이 남아 있다.

위험:

- `session_enabled=false` 장기 로그인 모드에서 실제 token exp는 10년인데 blacklist row는 24시간/7일 뒤 삭제될 수 있다.
- 삭제 이후 token이 exp 전까지 다시 통과할 수 있다.

권고:

1. 모든 세션 회수 경로를 `revoke_session_family(_async)`로 통일한다.
2. 직접 `add_to_blacklist*` 호출은 예외적 유틸 내부로만 제한한다.
3. 테스트 케이스를 `session_enabled=false`로 두고 logout/force logout/password-change/reset/duplicate-login 후 기존 access/refresh가 계속 401인지 확인한다.

### P1-02. API 서버 Force-Logout NATS publisher는 현재 compose 구성상 실사용 준비가 안 되어 있다

DB 변경 SYNC:

- `db-monitor`는 `nats-core_nats-network`에 붙어 있다.
- `db-monitor`에서 `nats-server-01` 이름 해석이 된다.
- PostgreSQL listener도 `pg_stat_activity`에서 확인된다.
- trigger도 48건 설치되어 있다.
- `pg_notification_queue_usage()`는 0이다.

API 서버 Force-Logout NATS:

- `api-server`는 `nats_external` 네트워크에 붙어 있지 않다.
- `api-server`에서 `nats-server-01` 이름 해석이 실패한다.
- `api-server` compose environment에 `NATS_URL`, `NATS_UNIT_ID`, `NATS_REVOKE_ENABLED`, `REVOKE_SIGNING_KEY`가 전달되지 않는다.
- 현재 런타임 `NATS_REVOKE_ENABLED=False`.

결론:

- PostgreSQL 변경 → NATS SYNC는 현재 구조상 정상 경로가 있다.
- 하지만 API 서버에서 직접 보내는 Force-Logout revoke / permissions_changed NATS는 현재 off이며, 켜도 네트워크/DNS 때문에 실패할 가능성이 높다.

권고:

1. `api-server`도 `nats_external` 네트워크에 연결한다.
2. compose에 아래 env를 명시한다.
   - `NATS_URL=${NATS_URL:-nats://nats-server-01:4222}`
   - `NATS_UNIT_ID=${UNIT_ID:-unit001}` 또는 `NATS_UNIT_ID=${NATS_UNIT_ID:-unit001}`
   - `NATS_REVOKE_ENABLED=${NATS_REVOKE_ENABLED:-false}`
   - `REVOKE_SIGNING_KEY=${REVOKE_SIGNING_KEY:-...}`
3. enabled=true 상태에서 실제 force logout → NATS publish 로그/구독 수신을 E2E로 검증한다.

### P1-03. 테스트 환경이 즉시 실행되지 않는다

선별 테스트 실행:

```text
pytest tests/test_permission_map_contract.py tests/test_mutation_auth_contract.py tests/test_account_lowrisk_fixes.py -q
```

1차 실패:

- 호스트 환경변수 `DEBUG=release`
- `Settings.DEBUG`는 bool이라 `release`를 파싱하지 못해 import 단계에서 실패

2차 실패:

- `DEBUG`를 제거하고 재시도하면 `ModuleNotFoundError: No module named 'aiosqlite'`
- `requirements.txt`에 `aiosqlite`가 없다.
- 테스트 fixture는 SQLite async URL을 만들기 때문에 `aiosqlite`가 필요하다.

권고:

1. `requirements.txt`에 `aiosqlite` 추가.
2. 테스트 실행 스크립트에서 `DEBUG` 같은 일반 OS 환경변수 충돌을 차단하거나, 앱 설정명을 `APP_DEBUG`처럼 네임스페이스화한다.
3. CI에서 `pytest tests/test_permission_map_contract.py tests/test_mutation_auth_contract.py tests/test_account_lowrisk_fixes.py`를 기본 smoke로 돌린다.

### P2-01. 운영 전 secret/CORS 설정 교체 필요

현재 런타임:

| 항목 | 값 |
|---|---|
| `ENVIRONMENT` | `dev` |
| `AUTH_MODE` | `token` |
| JWT secret | 기본값 계열 사용 중 |
| revoke signing key | 기본값 계열 사용 중 |
| CORS | `["*"]` |
| DEBUG | false |

dev 환경에서는 validator가 warning만 내므로 서버는 뜬다. staging/prod에서는 validator가 막도록 되어 있어 방향은 맞다.

권고:

1. 운영 배포 전 `ENVIRONMENT=prod`.
2. JWT secret / revoke signing key를 각각 별도 랜덤 값으로 교체.
3. `CORS_ORIGINS`를 실제 UI origin으로 제한.
4. `.env`가 이미지에 포함되지 않도록 유지하되, compose environment 또는 secret 관리로 명시 전달.

### P2-02. OpenAPI 기준 public GET allowlist가 문서화되어 있지 않다

현재 OpenAPI에서 security가 없는 `/api/*`:

- expected public:
  - `POST /api/auth/login`
  - `POST /api/auth/refresh`
  - `GET /api/users/photo/{file_name}`
  - `GET /api/thumbnails/...`
  - `GET /api/tracking/health`
- 검토 필요:
  - `GET /api/config-change-logs`
  - `GET /api/config-change-logs/{log_id}`
  - `GET /api/system-events`
  - `GET /api/system-events/{event_id}`
  - `GET /api/system-events/summary`
  - `GET /api/events/statistics/*`

권고:

- public endpoint allowlist를 코드와 문서에 동시에 명시한다.
- OpenAPI에 `security: []`가 붙은 public endpoint만 공개로 간주하는 contract test를 만든다.

### P3-01. 잘못된 enum filter를 조용히 무시한다

`config_change_logs.py`, `system_events.py`는 invalid enum filter가 들어와도 `pass`로 무시한다.

영향:

- 클라이언트 오타가 422로 드러나지 않고 전체/다른 결과가 반환될 수 있다.
- 운영 검색/감사 화면에서 “필터가 적용된 줄 알았는데 실제로는 무시”되는 문제가 생길 수 있다.

권고:

- 요청 filter enum은 Pydantic/Query enum 또는 명시 422로 처리한다.

## 6. NATS/DB 변경 감시 검증 결과

### 6.1 DB trigger 설치 상태

`trg_sync_%` trigger 48건 확인.

주요 대상:

- `devices`
- `controllers`, `sensors`, `cameras`, `speakers`, `enclosures`, `lamps`
- `servers`, `server_categories`
- `device_groups`, `device_group_mappings`
- `event_mappings`
- `event_mapping_cameras`, `event_mapping_speakers`, `event_mapping_lamps`
- `camera_presets`, `rois`
- `file_groups`
- `camera_settings`
- `proxy_settings`

### 6.2 db-monitor 상태

- `pg_stat_activity`: `application_name='db_monitor'`, state idle, query `SELECT 1`
- `pg_notification_queue_usage()`: 0
- 로그: `Listening on gop_sync → NATS nats://nats-server-01:4222`
- 재연결 로그도 확인됨: `session ended ... reconnect ... Listening ...`

결론:

- PostgreSQL 데이터 변경 → `pg_notify` → `db-monitor` → NATS SYNC 경로는 현재 설치/연결 상태가 정상이다.
- 단, 실제 NATS consumer 수신까지는 별도 구독 E2E가 필요하다.

## 7. 우선 수정 순서

### 1순위: 민감 GET API 인증 적용

- `config-change-logs`
- `system-events`
- `event-statistics`
- default-allow 구조를 `/api/*` default-deny + allowlist로 전환 검토

### 2순위: refresh/access token orphan 제거

- refresh 시 기존 access jti blacklist
- 또는 per-request `sid`/session 상태 검증
- 장기 로그인 모드 테스트 추가

### 3순위: 세션 revoke 경로 통일

- `auth.logout`
- `user_sessions` bulk/single force logout
- password change other-session revoke
- 모두 `session_revoke_service` 사용

### 4순위: API 서버 NATS revoke 활성화 준비

- `api-server`를 `nats_external`에 연결
- NATS env 전달
- 실제 publish E2E 검증

### 5순위: 테스트 실행성 복구

- `aiosqlite` requirements 추가
- `DEBUG` 환경변수 충돌 제거
- 선별 contract tests CI 등록

## 8. 최종 판단

현재 API 서버는 v6.0 이후 안정화가 많이 진행됐고, DB 변경 NATS SYNC 쪽은 구조적으로 정상에 가깝다. 하지만 운영 관점에서는 아직 “인증 기본 정책”과 “세션 token family 회수 정책”이 가장 중요하다.

특히 지금 남은 P0 두 가지는 서로 연결된다.

1. 일부 GET API가 token 모드에서도 공개다.
2. refresh 이후 과거 access token이 남으면 장기 세션 모드에서 회수 불능 토큰이 생길 수 있다.

따라서 다음 수정은 기능 추가보다 인증/세션 권위 모델을 마무리하는 쪽이 우선이다.
