# Changelog

GOP RESTful API Test Server 변경 이력. [Keep a Changelog](https://keepachangelog.com/) 형식 따름.

## [Unreleased]

### v6.0-meta_hygiene — 계정 메타 위생 + 비밀번호 최소길이 상향 (P2-01/P2-02) (2026-07-10)

> Account 분석 §4.1/§P2. 존재하나 미갱신이던 메타 필드 활성화 + 비번 정책 강화.

- **P2-02 메타 갱신**: `password_changed_at`(self change·admin reset 시 기록), `locked_by`+`locked_at`(admin lock 시 수행자·시각 기록).
  기존엔 필드만 있고 항상 NULL이라 만료정책/감사에 못 쓰던 것 활성화.
- **P2-01 비번 정책**: 신규/변경/초기화 비밀번호 **min_length 6 → 8**(AccountUserCreate·PasswordReset·PasswordChange).
- 실측: 7자 생성 422/8자 201, reset 후 password_changed_at 기록, lock 후 locked_by=수행자 id.
- **Out of Scope**: 유출/공통 비밀번호 차단(wordlist/API 필요), 비번 만료 강제(password_expires_at 게이트).

### v6.0-refresh_cas — refresh rotation race 방지 (P1-07) (2026-07-10)

> Account 분석 §5.6. 동일 refresh 토큰 동시 요청 시 둘 다 회전해 orphan(무효화 안 된) 토큰이 생기던 동시성 취약점.

- `app/routers/auth.py` refresh 핸들러: 세션 조회에 **`with_for_update()`** 추가 → 동시 refresh 직렬화.
- **CAS**: 들어온 refresh 토큰이 세션의 **현재** `refresh_token` 과 일치할 때만 회전 허용.
  먼저 잠금 얻은 요청이 회전하면 session.refresh_token 갱신 → 뒤늦은(같은 옛 토큰) 요청은 불일치 → 401. orphan 토큰 방지.
- 실측: 정상 refresh 200, 회전된 OLD 토큰 재사용 401(새 토큰 200), 동시 2병렬 → 정확히 200+401.

### v6.0-login_hygiene — 실패 로그인 감사 기록 + 성공 위생 (P1-09 일부, §5.1) (2026-07-10)

> Account 분석 §7.2/§5.1. 실패 로그인이 UserLoginLog 에 안 남고, 성공 시 failed_count 미리셋·last_login 미갱신.

- **실패 로그인 감사(ACC-P1-09)**: `_record_login_failure` 헬퍼 신설 — 없는 계정/틀린 비번/비활성/잠김 4경로 모두
  UserLoginLog FAILURE 기록(login_id·failure_reason·**IP·User-Agent·시각**, 없는 계정은 user_id=NULL). 독립 commit·예외 삼킴(로그인 방해 금지).
  응답 문자열은 동일 유지(계정 존재 여부 비노출) — 감사만 상세.
- **성공 위생(§5.1/P2-02)**: 로그인 성공 시 `failed_login_count=0` 리셋 + `last_login_at`·`last_login_ip` 갱신.
  기존엔 성공해도 실패 카운트가 누적돼 오래된 실패로 잠금 오작동 소지가 있었음.
- 실측: 틀린비번/없는계정 → 401 + FAILURE 로그(reason INVALID_CREDENTIALS, IP 기록, 없는계정 user_id=NULL),
  성공 시 failed_count 3→0 + last_login 기록.
- **Out of Scope(후속)**: IP/계정 기반 rate limit·exponential delay(상태저장소 설계 필요).

### v6.0-inactive_group_enforce — 비활성 그룹 권한 미집행 수정 (P1-03) (2026-07-10)

> Account 분석 §6.2. `UserGroup.is_active=false` 가 권한 계산에서 무시되던 문제 — 관리자가 그룹을
> 비활성화 = 긴급 권한 차단 의도인데 권한이 그대로 유지되던 위험.

- **집행**: `_role_group_allows`(auth.py, 배정그룹·grant그룹·sync/async 공유 판정)에 `is_active` 가드 추가 →
  비활성 그룹은 권한 원천 불인정. enforce_matrix / require_perm 전 경로 일관 적용.
- **payload 정합**: `effective_permissions_payload`(sync+async) 병합부에서 비활성 그룹 제외 →
  클라 노출 스냅샷도 집행과 동일(비활성 그룹 권한 미표시).
- **문서화(§6.3/§6.4)**: `PermissionsSchema.device_groups`·`time_restriction` 은 **서버 미집행(UI 메타데이터)** 임을
  Field description 에 명시 — dead config 가 보안 기능으로 오인되던 문제 차단. (집행은 별도 PRD.)
- 실측: 활성 그룹 reports:view → 200 + payload True / 비활성화(같은 토큰, 요청시점) → **403 + payload None**. 단위 14 passed.

### v6.0-session_authority — 세션 권위 모델 통합: strict 상태검사 + refresh 세션검증 + 공통 폐기 서비스 (P0-02/03/04) (2026-07-09)

> PRD `docs/prds/account-session-authority-prd.md` (Approved). 분석 §12 처방. **auth 코어 변경** — 롤백태그+A01~A18 게이트로 진행.
> "JWT 유효한가"만 보던 인증을 사용자상태·세션상태·token family가 하나의 권위로 움직이도록 통합.

**FR-01 — 공통 `revoke_session_family` 서비스 (`app/services/session_revoke_service.py` 신설)**
- access+refresh JTI 를 **각 JWT 실제 exp**로 blacklist + 세션 inactive/logged_out/reason 마킹, 원자적.
- TTL 설정값 추정(24h/7d) 제거 → exp claim 사용(ACC-P1-02 동반). 만료 토큰도 폐기 위해 decode 시 exp 검증 off.
- dual-stack(sync/async) — login/refresh/logout=sync, users.py=async.

**FR-02 — strict 인증 상태 검사 (ACC-P0-02)**
- `get_current_account_user`(sync)·`get_current_account_user_async` 둘 다 `is_active==True AND is_locked==False` 검사, 위반 401.
- 기존엔 서명/exp/blacklist/존재만 검사 → 잠긴/비활성 계정 토큰이 blacklist 안 됐으면 통과하던 결함. optional 버전과 정합.

**FR-03 — refresh 발급 전 검증 (ACC-P0-03)**
- user active/unlocked + **sid 필수** + sid 세션 존재+`is_active` 확인을 **토큰 발급 전**에 수행, 실패 401.
- ※ `session.expires_at`(=access 만료)로 판정 금지(V-02) — 정상 refresh 오거부. 세션은 `is_active` 기준, 시간만료는 refresh JWT exp 담당.

**FR-04 — 중복 로그인 refresh 폐기 (ACC-P0-04)**
- 이전 세션을 `revoke_session_family`로 폐기 → access **+refresh 둘 다** blacklist. 기존 access-only 로 이전 기기 refresh 부활하던 것 차단.

**FR-05 — lock/reset-password token family 폐기**
- `_revoke_all_user_sessions` 헬퍼 — lock(기존 is_active=false만 → token blacklist까지), admin reset-password(기존 세션 무처치 → 폐기, A07).

**검증 (Live E2E A01~A18 핵심 10/10)**: A01 잠금→401, A02 비활성→401, A03 잠금 refresh→401, A04 종료세션 refresh→401,
A05 중복로그인 access+refresh→401, A07 reset 후 access+refresh→401, A16 정상 refresh 무회귀 200. 기존 단위 20 passed.

**Out of Scope(후속)**: 매 요청 세션 DB검사, refresh race CAS(P1-07), token 원문→hash(P1-10), 실패로그인 rate limit(P1-09), auth 완전 async화.

### v6.0-account_lowrisk — Account 분석 저위험 3건: 감사 async 교정(P1-04) + blacklist 정리 스케줄러(P1-05) + lock ADMIN 가드(P1-08) (2026-07-09)

> `docs/Analysis/Account_Auth_Session_Analysis_20260708.md` 의 검증된 저위험 항목. 코어(P0 세션권위)는 별도.

- **ACC-P1-04 — UserGroup 감사 유실**: `user_groups.py` 가 `AsyncSession` 인데 sync `log_action` 을 `await` →
  내부 `db.commit()/refresh()` 가 미await coroutine 이라 감사 row 가 커밋되지 않던 문제.
  `log_action_async` 로 교체(생성/수정/permissions/삭제 4경로).
- **ACC-P1-05 — token_blacklist 정리 미동작**: `cleanup_expired_async` 는 있으나 스케줄러 미등록이라
  만료 row 누적(실측 388행 중 357 만료). `run_blacklist_cleanup()` zero-arg 진입점 신설 +
  스케줄러 등록(interval 1h). 주석에 명시됐던 "1시간 cleanup" 을 실제 연결.
- **ACC-P1-08 — 마지막 ADMIN lockout 방지**: `lock_user` 에 삭제/강등과 동일한 가드 추가 —
  대상이 마지막 active·unlocked ADMIN 이면 잠금 거부(409). FOR UPDATE 로 TOCTOU 차단.
- `tests/test_account_lowrisk_fixes.py`: 3건 소스 계약 검증.

### v6.0-authz_map_contract — permission_map stale 정리 + system-events 모듈 정합 + contract 테스트 (2026-07-09)

> 외부 리뷰 AUTH-01 후속(stale map 정리 + map↔OpenAPI 자동비교). `enforce_matrix` 는 전역 dependency 로 활성.

- **permission_map stale 5건 제거** — enforce_matrix(전역)가 절대 발화 못 하는 죽은 항목(메서드/경로 오기재)이라
  "보호되는 듯하나 실제 무집행"인 착시를 유발. 실측 stale 5건:
  - `POST/DELETE /api/enclosure-metrics{,/{}}` — list_router(GET전용) 경로 오기재. 실제 create/delete 는
    `/api/devices/enclosures/{}/metrics` 이며 optional-auth(머신 인제스트 의도)로 운용 → 제거.
  - `PATCH /api/system-events/{}/acknowledge` — 실제 POST. 아래 route-level 가드로 대체 → 제거.
  - `POST /api/devices/cameras/{}/settings` — POST 라우트 없음(PATCH/PUT 유효 매핑 존재) → 중복 제거.
  - `PUT /api/reports/templates/{}` — PUT 라우트 없음(PATCH 유효 매핑 존재) → 중복 제거.
- **system-events 모듈 정합(AUTH-01 재조정)** — 직전 `review_authz` 에서 붙인 route 가드가 `servers` 였으나
  중앙 map(106/108)은 `system-events` 를 **`events`** 모듈로 규정 → 전역 enforce_matrix(events)와
  route 가드(servers)가 **이중집행 충돌**(둘 다 요구)해 무력화되던 것을, route 가드를 **`events`로 통일**해 해소.
  POST/PATCH/DELETE/acknowledge = events:edit/edit/delete/edit.
- **`tests/test_permission_map_contract.py`** — 모든 map 키가 실제 OpenAPI 라우트와 매칭(stale=0) + (module,verb) 유효성 검사. stale 재유입 회귀 차단.
- 실측: contract 통과, system-events 무인증 401 유지, ADMIN bypass 정상.

### v6.0-review_polish — 외부 리뷰 후속: Swagger tag 중복 제거(API-01) + 문서 버전 정합(DOC-01) (2026-07-09)

> `docs/Analysis/API_Server_Overall_Review_20260708.md` API-01/DOC-01 (cosmetic, 구조 변경).

- **API-01**: operation 168건에 동일 tag 2회 등록되던 문제 — router 선언(`APIRouter(tags=[...])`)과
  `include_router(tags=...)` 이중 지정 탓. **router 레벨 populated tags 를 28개 파일에서 제거**,
  `include_router`(main.py, 44개 일관)를 단일 소스로. `prefix=`/`dependencies=` 보존. 실측 **중복 168→0, 무태그 0**.
- **DOC-01**: 연동설계서 본문 헤더 버전 `v5.4 → v6.0`(Swagger `6.0.0` 정합). 내부 v5.0/v5.4 는 기능 이력 마커라 보존.

### v6.0-review_authz — 외부 리뷰 후속: system-events 무인증 노출 차단(AUTH-01) + CORS prod 검증(OPS-03) (2026-07-09)

> `docs/Analysis/API_Server_Overall_Review_20260708.md` AUTH-01/OPS-03. 검증 우선으로 실제 노출만 좁혀 수정.

**AUTH-01 — 무인증 mutation 실측 감사 + system-events 쓰기 4종 차단**
- 리뷰의 "미등록 46 mutation"은 **중앙 permission_map ↔ router 의존성 이중 집행**을 노출로 오인한 것.
  OpenAPI `security` 필드로 재감사 → 실제 인증 미부착 mutation 은 **6건**, 그중 `auth/login`·`auth/refresh`는
  의도적 공개. **실제 노출은 `system-events` 쓰기 4종**(POST/PATCH/DELETE/acknowledge).
- `app/routers/system_events.py`: 4종에 `require_perm_optional_async("servers", edit|control|delete)` 부착
  (서버 모니터링 도메인 = servers 매트릭스. 형제 도메인과 동일 optional 패턴 → token 모드 집행, public 휴면=무파손).
- `tests/test_mutation_auth_contract.py`: 모든 mutation 이 security 를 갖는지 검사(허용목록: login/refresh) — 회귀 방지.
- 실측: 4종 무인증 **422→401**, auth/login 공개 유지, contract 2 passed.
- (구조 결정 보류: 중앙 map 을 단일 choke point 로 삼는 default-deny 전환·stale 정리는 별도 차수.)

**OPS-03 — CORS 와일드카드 prod 방어**
- `app/config.py`: `CORS_ORIGINS` field_validator 추가 — staging/prod 에서 `'*'` 거부(기존 JWT/AUTH_MODE 검증기와 동일 패턴).
  `allow_credentials=True` + `'*'` 조합 위험 차단. dev 는 편의 허용.

### v6.0-review_reliability — 외부 리뷰 후속: api_logs 파티션 자동생성(DB-02) + subtype SYNC 트리거(MSG-01) + db-monitor 재연결(MSG-02) (2026-07-09)

> `docs/Analysis/API_Server_Overall_Review_20260708.md` 의 검증된 P1 신뢰성 3건.

**MSG-02 — db-monitor PostgreSQL 재연결 부재 (장애 후 조용한 SYNC 중단)**
- 기존: 1회 연결 후 `while True: sleep(1)` → PostgreSQL 재시작 시 LISTEN 유실되어도 컨테이너는 Up, SYNC 영구 중단.
- `db_monitor/main.py`: `run_supervised()` 감독 루프 신설 — liveness 프로브(`SELECT 1`)로 단절 감지 →
  지수 백오프+지터(상한 30s) 무한 재연결. NATS 는 클라 자체 무한 재연결(`max_reconnect_attempts=-1`).
  하트비트 파일(`/tmp/db_monitor_heartbeat`) 주기 기록.
- `docker-compose.yml`: db-monitor healthcheck 추가(하트비트 <60s 신선도) → autoheal(label=all)이 감시·재기동.
- 실측: 백엔드 강제 종료(`pg_terminate_backend`) → `session ended` 감지 → 1s 후 재연결(새 PID)·재-LISTEN,
  이후 camera UPDATE SYNC 정상 발행. healthcheck fresh→exit0, stale→exit1(autoheal 트리거) 검증.

**DB-02 — `api_logs` 파티션 만료 (2026-11 이후 INSERT 실패 위험)**
- v60 월별 파티셔닝이 2026-10 까지만 생성 + 자동확장/기본파티션 부재 → 경계 초과 시 INSERT 실패.
- `app/services/api_logs_partition_service.py` `ensure_api_log_partitions()` 신설 — 당월+6개월 파티션을
  `CREATE TABLE IF NOT EXISTS ... PARTITION OF`(멱등, PG11+) 로 생성. startup 1회 + 스케줄러(cron 00:05 일1회) 재보장.
- 실측: 파티션 2026-10 → **2027-01** 확장, 2026-12 경계 INSERT 성공.

**MSG-01 — subtype 전용 컬럼 UPDATE 시 NATS SYNC 미발행**
- `devices` 부모 트리거만 존재 → `cameras.mode` 등 subtype 전용 UPDATE 는 `devices` 미변경이라 미발화(실측 0건).
- `app/db_triggers.py`: 6개 subtype 테이블(controllers/sensors/cameras/speakers/enclosures/lamps)에
  **AFTER UPDATE** 트리거 추가, `devices` 트리거와 **byte-identical** SYNC_DEVICE payload 발행.
  부모+자식 동시 UPDATE 는 PostgreSQL NOTIFY 동일 (채널,payload) **자동 중복제거**로 1건만 전달
  (INSERT/DELETE 는 조인상속상 devices 도 함께 바뀌어 base 트리거가 담당 → subtype 은 UPDATE 만).
- 실측 3/3: subtype-only UPDATE **1건**(이전 0), 부모+자식 동일tx **1건**(dedup), base-only **1건**(회귀).

### v6.0-security_hardening — 로그 보안(무인증/평문) + 이미지 secret + 예외 노출 3건 (2026-07-09)

> 외부 LLM 전체 리뷰(`docs/Analysis/API_Server_Overall_Review_20260708.md`)의 검증된 지적 중
> P0/저위험 보안 3건을 코드 교차검증 후 수정. (SEC-02 고정계정·SEC-05 10년JWT 는 사용자 지시로 보류.)

**SEC-01 — API 로그 무인증 공개 + 민감 요청 본문 평문 저장 (P0)**
- `app/routers/logs.py`: `GET /api/logs`·`/api/logs/viewer` 에 `require_perm_async("audit_logs","view")` 부착
  — 무인증 조회 차단(ADMIN bypass 또는 `audit_logs:view`). 이전엔 인증 dependency 0.
- `app/middleware/logging.py`: `redact_request_body()` 신설 — 요청 body(JSON)의 민감 키
  (`password/current_password/new_password/user_password/access_token/refresh_token/token/secret/authorization`)
  를 재귀 마스킹(`***REDACTED***`). JSON 아니면(폼/멀티파트) 원문 미저장(보수적). 응답 body 추출 지역변수
  분리(`resp_body`)로 마스킹된 요청 body 를 덮어쓰던 잠복 결함도 제거.
- `app/migrations/v63_redact_sensitive_api_log_bodies.sql`: 과거 평문 body 정리(멱등, startup 자동적용).
- 실측: 민감 body **521 → 0**, 무인증 `/api/logs`·`/viewer` **401**, ADMIN **200**, 신규 login/reset-pw body `***REDACTED***`.
- 단위: `tests/test_log_body_redaction.py` 6 passed.

**SEC-03 — 이미지 레이어 secret 유출 (`.dockerignore`)**
- `COPY . .` 가 `.env`(존재) + `certs/server.key`(private key) 를 이미지 레이어에 굽던 문제.
- `.dockerignore` 에 `.env`·`.env.*`·`certs/*.key|crt|pem`·`certs/rootCA*` 추가. 인증서는 런타임 바인드 마운트라 이미지 불필요.

**SEC-04 — 500 응답에 내부 예외 문자열 노출**
- `app/main.py` 전역 500 핸들러가 `f"Internal server error: {str(exc)}"` 로 SQL·경로·드라이버 메시지 노출.
- 클라에는 고정 메시지 `"Internal server error"` + `request_id`(meta) 만 반환, 전체 스택트레이스는 `logging` 으로 서버 로그에만 기록.

### v6.0-rbac_matrix_gate — 계정/그룹/세션 관리 require_admin → 매트릭스 전환 (2026-07-07)

> 사용자 검토: monitor1(다른 사이트)에 한시 "ADMIN 그룹" grant 를 줬는데 안 먹힘.
> 근본원인: 계정/그룹/세션 관리 엔드포인트가 `require_admin`(role=="ADMIN" **문자열만** 검사)이라
> grant 로 병합된 **권한 매트릭스를 아예 안 봄**. grant 는 도메인(require_perm) 엔드포인트만 뚫었음.
> 설계 방향(사용자 확정): role=ADMIN=전권 bypass / USER=매트릭스(등급 ∪ grant), 스케쥴 만료 시 복귀.
> ADR_Permission_Model_v5.2 가 이미 문서화한 모델에 **코드를 정합**(반쪽 남았던 RBAC 이주 완성).

### 변경 — require_admin → require_perm 전환 (26 엔드포인트, 6 파일)

| 파일 | 매트릭스 개방(temp-admin 동작) | base-ADMIN 전용 유지 |
|---|---|---|
| `users.py` | GET·POST·PUT·DELETE·lock·unlock·reset-pw (users:view/edit/delete/control) | — (아래 가드로 상승 차단) |
| `user_groups.py` | GET 3종 (user_groups:view) | POST·PUT·permissions·DELETE (매트릭스 정의) |
| `user_sessions.py` | GET 2종(view)·force-logout 2종(control) (users) | — |
| `grants.py` | GET 2종 (users:view) | POST 부여·DELETE 회수 (승격 메커니즘) |
| `settings.py` | GET·PUT /session (setup_system:view/edit) | — |
| `servers.py` | PATCH → require_perm_optional(servers:edit) — 형제 POST/PUT/DELETE 와 정합 | — |

### 권한상승 가드 (한시성 복귀 보장 — `app/routers/users.py`)

grant 로 한시 승격된 USER 가 **영구 승격**을 자가 생성하는 경로를 base-ADMIN 전용으로 잠금:
- `_assert_can_define_permissions`: 비-ADMIN 의 **role·group_id 변경** 차단 (자기 승격/전권그룹 고정 방지)
- `_assert_can_modify_admin_target`: 비-ADMIN 의 **ADMIN 대상 계정 변경**(pw초기화/삭제/잠금/수정) 차단 (횡적 탈취 방지)
- grant 부여(POST)·그룹 매트릭스 편집은 라우터 레벨에서 base-ADMIN 유지

### 검증 (2026-07-07)

- **Live 컨테이너 E2E 10/10**: temp-admin grant 로 GET users/user-groups/user-sessions·PUT settings·프로필수정 = 200,
  self role=ADMIN·self group_id·self grant·ADMIN pw초기화·그룹매트릭스편집 = 403
- **단위 테스트**: `tests/test_users_escalation_guards.py` 7 passed (가드 순수함수)
- **무회귀**: base-ADMIN 은 전 구간 bypass(그룹/계정/grant 생성 정상), 마지막 ADMIN 가드 유지·강화

### 운영 주의

- 클라 "ADMIN 그룹"(예시)은 enum 12모듈 중 8개만 보유 → grant 시 `setup_system·broadcast·map·setup_feature` 미개방.
  완전 임시전권은 그룹에 4모듈 추가 필요(또는 role=ADMIN, 단 한시성 없음).
- 통합 테스트 harness 는 v6.0 async 전환 후 conftest 가 **sync dep 오버라이드** → async 라우터 미적용(401)로 사전파손. 본 변경과 무관.

### v6.0-session_enabled_switch — session_enabled 세션 만료 마스터 스위치 구현 (2026-07-07)

> 앞 검토(`session_settings_verify`)에서 `session_enabled` 가 저장만 되고 미연결이었음.
> 사용자 정의: **세션 기간성 on/off 스위치** — 켜면 `session_timeout` 동작, 끄면 세션 무기한 유지.

### 구현

`app/services/settings_service.py`:
- `resolve_session_expiry(db) -> (timeout_hours, refresh_days)` 헬퍼 신설
  - `session_enabled=True` → 설정값(`session_timeout_hours`, `refresh_expiration_days`)
  - `session_enabled=False` → **10년**(`SESSION_DISABLED_TIMEOUT_HOURS`/`_REFRESH_DAYS`) — JWT는 exp 필수라 진짜 무한대 불가 → 10년으로 근사(사실상 무기한)

`app/routers/auth.py`:
- login(L422) + refresh(L720) 두 지점을 `resolve_session_expiry(db)` 로 교체
- access token exp / refresh exp / `session.expires_at`(L468) 3계층 일관 적용
- session_sweep 은 expires_at 이 10년 후라 자동으로 안 건드림

### 동작

| session_enabled | access token exp | 의미 |
|---|---|---|
| **ON** | `session_timeout_hours` (예: 12h) | 세션 만료 동작 |
| **OFF** | 10년 (사실상 무기한) | 세션 기간성 끔 — 로그인 유지 |

### 실측 (2026-07-07)

- ON + timeout=12h → access token exp **12.0h**
- OFF → access token exp **87600h(10.0년)** + `session.expires_at` **~10년** (3계층 정합)
- 토글 즉시 반영 (settings_service 캐시 무효화)

### v6.0-session_settings_verify — 세션 설정 API 실동작 검증 + 블랙리스트 TTL 정합 (2026-07-07)

> 사용자 요청: 세션 시간·비밀번호 실패 횟수 등 설정 API가 실제로 동작하는지 검토.

### 검증 결과 — 설정 API는 실제 동작함 ✅

`GET`/`PUT /api/settings/session` 저장값이 인증 로직에 실시간 반영됨(실측):

| 설정 | 저장 | 실제 동작 | 실측 |
|---|---|---|---|
| `lockout_threshold` | ✅ | ✅ | 3 설정 → 정확히 3회째 계정 잠금(`is_locked=true`), 올바른 비번도 "Account is locked" 차단 |
| `session_timeout_hours` | ✅ | ✅ | 1h→access token exp 1.00h, 12h→12.00h (JWT exp 직접 확인) |
| `refresh_expiration_days` | ✅ | ✅ | 7일→refresh token exp 7.00일 |
| `session_enabled` | ✅ | ❌ 미사용 | 저장만 됨, auth 로직 어디서도 참조 안 함(별개 트랙) |

로그인(auth.py:402/422/468/478/480)이 `settings_service.get()` 으로 런타임 값을 읽어 잠금 임계·access·refresh exp에 적용. refresh 엔드포인트(L711~714)도 동적.

### 발견·수정한 경미한 결함 — 블랙리스트 TTL 불일치

`logout`(L629) + `refresh rotation`(L692)에서 폐기 refresh 를 블랙리스트 등재할 때 만료(TTL)를 **정적 env `JWT_REFRESH_EXPIRATION_DAYS`** 로 계산했음. 사용자가 `refresh_expiration_days` 를 늘리면(예: 30일) 실제 refresh 는 30일 유효한데 블랙리스트는 7일만 유지 → **8~30일차에 폐기된 refresh 가 블랙리스트에서 빠져 부활할 수 있는 틈**.

수정: 두 지점 모두 `settings_service.get(db, REFRESH_EXPIRATION_DAYS)` 동적 값 사용.

### 실측 (2026-07-07)

- `refresh_expiration_days=30` 설정 → logout → 블랙리스트 refresh 항목 TTL **29일**(≈30, 이전 7일)
- 전 검증 후 원복(7일)

### 별개 트랙
- `session_enabled` 는 정의만 있고 실제 로직 미연결 — 의도된 의미(세션 관리 기능 전체 on/off?) 확정 후 구현 필요

### v6.0-default_profile_image — 프로필 사진 없는 계정 default 이미지 제공 (2026-07-07)

> 사용자 요청: 계정 사진 없을 때 default 이미지 제공. 기존엔 `photo_url: null` + 없는 파일 요청 시 404.

### 구현 (방식 A+B)

| 파일 | 역할 |
|---|---|
| `app/utils/default_profile.py` (신규) | Pillow 로 `default.png` 생성 (256×256, 회색 배경 + 중립 실루엣) |
| `app/main.py` lifespan | startup 에서 `default.png` 없으면 자동 생성 — `data/profiles/` 는 gitignore 라 clone 배포엔 없으므로 |
| `app/schemas/user.py` | `AccountUserResponse` model_validator: `photo_url` null → `/api/users/photo/default.png` (모든 사용자 응답 경로 일괄) |
| `app/routers/users.py` | `GET /photo/{file_name}`: 파일 없으면 404 대신 default 반환 (없으면 즉석 생성) |

### 동작

- 사진 없는 계정 응답: `"photo_url": "/api/users/photo/default.png"` (이전 `null`)
- 없는 파일명 요청: **200 + default png** (이전 404)
- 실제 사진 있는 계정: 원본 URL 유지 (영향 없음)
- audit 로그 before/after 상태는 실제 null 보존 (감사 정확성 — 미변경)

### 견고성

`default.png` 는 개인 사진 폴더(gitignore)라 clone 엔 없지만, **startup 자동 생성 + 서빙 시 즉석 생성** 이중 안전망으로 신규 PC 배포에도 동작.

### 실측 (2026-07-07)

- startup 로그: `[OK] default profile image created: data/profiles/default.png`
- `GET /api/users/photo/default.png` → 200 image/png 1440B
- `GET /api/users` 응답: 12계정 중 10 default_url / 2 real_photo / **still_null 0**
- 없는 파일명 `GET /photo/nonexistent.jpg` → 200 (default 폴백, 이전 404)

### v6.0-force_logout_tz_fix — 강제 로그아웃 500 버그 수정 (tz-aware naive 정합) (2026-07-07)

> 사용자 지적: 세션 강제 로그아웃 실행 시 버그. 실측 재현 → HTTP 500.

### 근본 원인

`app/routers/user_sessions.py` 의 강제 로그아웃(`force_logout_session` L439) + 자기 로그아웃(`self logout` L326)에서:
```python
session.logged_out_at = datetime.now(settings.tz)   # tz-aware(Asia/Seoul)
```
`user_sessions.logged_out_at` 컬럼은 **naive DateTime**(TIMESTAMP WITHOUT TIME ZONE)이라, asyncpg 가 tz-aware 값을 거부:
```
asyncpg.exceptions.DataError: can't subtract offset-naive and offset-aware datetimes
UPDATE user_sessions SET logged_out_at=$1::TIMESTAMP WITHOUT TIME ZONE ...
```
→ 강제 로그아웃 전체가 500 + 롤백 → **세션 무효화·jti 블랙리스트도 롤백되어 토큰이 안 막힘** (이중 실패).

프로젝트의 **naive KST 컨벤션** 위반. 다른 곳(auth.py:588, users.py:250, user_sessions.py:182 벌크)은 이미 `.replace(tzinfo=None)` 있었으나 이 2곳만 누락.

### 픽스

`app/routers/user_sessions.py`:
- L326 (자기 세션 로그아웃): `datetime.now(settings.tz)` → `.replace(tzinfo=None)`
- L439 (단건 강제 로그아웃): 동일

(벌크 force_logout L182 는 이미 정상)

### 실측 검증 (2026-07-07)

| 단계 | 이전(버그) | 수정 후 |
|---|---|---|
| DELETE /user-sessions/{id} 강제로그아웃 | **HTTP 500** (DataError) | **200 success** |
| 강제로그아웃 후 그 토큰으로 /users/me | **200** (안 막힘) | **401** (차단) |

토큰 jti 블랙리스트 커밋도 정상화되어 강제 로그아웃 즉시 무효화 확인.

### v6.0-role_seed_normalize — Role 규칙(v5.3 2종) 시드/기존 데이터 재적용 (2026-07-07)

> 사용자 실측: `GET /api/users` 응답에 `operator1=OPERATOR`, `monitor1=VIEWER`, `maintainer1=MAINTAINER` (07-02 시드) — v5.3 role 2종(ADMIN/USER) 축소가 DB에 미반영.

### 원인 (2갈래)

1. **모델 default 미수정** — `app/models/user.py` `role = Column(..., default="VIEWER")` 였음. VIEWER 는 v5.3 폐지값인데 미지정 생성 시 옛 값 주입.
2. **정규화 마이그레이션 미적용** — 시드 코드(`SAMPLE_USERS`)는 이미 `role="USER"` 로 고쳐졌으나, **기존 볼륨 DB의 옛 시드 행(07-02)은 그대로**. 시드는 idempotent 스킵이라 코드 수정이 기존 행에 반영 안 됨. v57 role 정규화 마이그레이션은 수동 실행이라 신규/기존 배포에 누락.

### 픽스

- `app/models/user.py`: role default `VIEWER` → `USER`
- `app/migrations/v62_role_normalize.sql` (신규): `UPDATE account_users SET role='USER' WHERE role NOT IN ('ADMIN','USER')` — idempotent, 파괴적 DDL 없음
- `app/utils/init_db.py`: `IDEMPOTENT_MIGRATIONS` 화이트리스트에 v62 등록 → **매 startup 자동 정규화** (v6.0-clone_deploy_bugfix #5·#6 인프라 재활용)
- `app/routers/users.py`: docstring 옛 role 예시(OPERATOR/VIEWER) → ADMIN/USER 정정

### 검증 (2026-07-07)

- 사용자 DB 조건 재현: `gop_user=OPERATOR`, `gop_operator=VIEWER`, `test_user=MAINTAINER` 인위 주입
- 컨테이너 재시작 → startup 로그 `[OK] idempotent migration applied: v62_role_normalize.sql`
- 정규화 후 role 분포: **ADMIN 9 / USER 3** (OPERATOR/VIEWER/MAINTAINER 전부 → USER, ADMIN 유지)

### 사용자 조치

`git pull` + `docker compose up -d --no-deps api-server` → 재시작 시 기존 DB 옛 role 자동 정리.
(신규 시드는 `role="USER"` 로 이미 정상, 모델 default 도 USER 로 수정됨.)

### v6.0-response_schema_audit — 응답 스키마 지뢰 전수 감사·완화 (2026-07-07)

> 같은 버그(String 컬럼 + strict Enum 응답 → 목록 500)를 servers.port/users.role/audit.actor_role 로 4번 얻어걸린 뒤, 남은 지뢰를 예방적으로 전수 제거.

### 감사 방식 (introspection)

컨테이너 런타임에서 모든 `*Response` pydantic 필드 ↔ SQLAlchemy 컬럼 타입 대조:
- 응답 Enum 필드 + DB `String/JSON` 컬럼 → **LANDMINE** (옛/임의 값 저장 가능 → 응답 500)
- 응답 Enum 필드 + DB `SQLEnum` 컬럼 → safe (DB가 값 강제)

스캔: `*Response` 91개, Enum 응답 필드 ~100건 → **지뢰 21건 발견**, safe 77건.

### 완화 21건 (Enum → str, 요청 스키마는 유지)

| 파일 | 필드 |
|---|---|
| `report.py` | ReportGeneration(List)Response report_type/period_type/status, ReportTemplate(List)Response report_type/default_period, ReportPreviewResponse period_type |
| `event.py` | Detection/Log type_event·action_reported·result, Malfunction type_event·action_reported·reason, Connection/Action type_event |
| `user.py` | UserLoginLogResponse action·result·failure_reason, UserSessionResponse logout_reason |
| `audit_log.py` | AuditLogResponse action_status |

특히 **report_generations.period_type** 은 방금 `v6.0-report_date_range` 로 `custom` 추가 → 옛 행에 없던 값이라 목록 500 지뢰였음. 함께 제거.

### 검증 (2026-07-07)

- introspection 재실행: **LANDMINE 21 → 0**
- 회귀: GET /reports/generations·status, /events/detections·malfunctions·actions·connections, /audit-logs, /users 전부 **200**
- unknown 2건 (`DeviceNestedResponse.category/mode`): Camera 모델 `SQLEnum` 소스 → 안전 확인

### 클라 영향 — 없음

응답 JSON 값은 동일 문자열. Swagger enum 표시만 사라짐. 하위호환 100%.

### 재발 방지 정책

1. `*Response` 에는 Enum/제약을 붙이지 않는다 (Postel's Law) — 검증은 요청+DB 계층
2. DB `SQLEnum` 컬럼이면 응답 Enum 안전, `String` 컬럼일 때만 지뢰
3. 신규 Response 필드는 introspection 스크립트로 회귀 검사
4. 장기: String 컬럼 → SQLEnum 승격 마이그레이션 검토 (근본, 파괴적)

### 통지

`docs/GOP_Server_API_response_schema_audit_REPLY.md`

### v6.0-clone_deploy_bugfix — clone 배포 후 6개 버그 근본 해결 (2026-07-07)

> 이슈: 다른 PC gitea clone 배포 후 발견된 6개 버그 (`docs/reports/BUG_REPORT_*.md`).
> 근본 3갈래: (A) 응답 strict Enum 반복, (B) 마이그레이션 자동적용 부재, (C) 개별 코드 버그 2건.

| # | 리포트 | 원인 | 픽스 |
|---|---|---|---|
| 1 | USER_ROLE_ENUM | 응답 strict Enum + 생성 기본값 VIEWER + 샘플 OPERATOR | 응답완화(선행) + `users.py` 기본값 USER + `init_sample_data` actor_role USER |
| 2 | AUDIT_LOGS_ENUM | `AuditLogResponse.actor_role` strict Enum + append-only 옛값 | `Optional[EnumUserRole]`→`Optional[str]` + 목록 fault tolerance |
| 3 | CONNECTIONS_LAZYLOAD | async `mapping.group` lazy-load → greenlet_spawn | `selectinload(DeviceGroupMapping.group)` |
| 4 | EVENT_STATISTICS_TZ | tz-aware 입력 ↔ naive created_at 500 | `_naive_kst()` 헬퍼, 4 endpoint 진입부 정규화 |
| 5 | REPORT_GENERATIONS_LIST | progress_pct 컬럼 DB 미적용 | **startup 자동 마이그레이션** |
| 6 | REPORT_STATUS | 동일 | 동일 |

### 근본 픽스 — startup 자동 마이그레이션 (#5·#6)

`app/utils/init_db.py`:
- `IDEMPOTENT_MIGRATIONS` 화이트리스트 (`ADD COLUMN IF NOT EXISTS` 계열만, 파괴적 마이그레이션 제외)
- `apply_idempotent_migrations(engine)` — **BEGIN/COMMIT strip 후 psycopg2 raw cursor 실행**
  * ⚠️ 명시적 BEGIN/COMMIT 은 psycopg2 자동 트랜잭션과 충돌해 조용히 no-op → strip 필수 (실측으로 발견)
  * ⚠️ `exec_driver_sql` 은 파라미터 바인딩 이슈(immutabledict) → raw cursor + `raw.commit()` 사용

`app/main.py` lifespan: `apply_triggers` 옆에 결선 (매 startup 스키마 보정).

### 응답 스키마 완화 (#1·#2)

- `app/schemas/audit_log.py` `actor_role`: Enum → str
- `app/routers/audit_logs.py`: 목록 try/except + WARN skip
- (선행 `v6.0-users_role_response_relax` 로 users.role 은 이미 완화됨)

### 코드 버그 (#3·#4)

- `app/routers/connections.py`: `_build_device_nested_response` 에 `selectinload`
- `app/routers/event_statistics.py`: `_naive_kst()` + summary/by_device/trend/dashboard 정규화

### 데이터 원천 정리 (#1)

- `app/routers/users.py`: 생성 기본 role `VIEWER` → `USER`
- `app/utils/init_sample_data.py`: 감사로그 시드 `actor_role="OPERATOR"` → `"USER"` (sync+async)

### 실측 검증 (2026-07-07)

| 검증 | 결과 |
|---|---|
| #5·#6 자동복구 | 컬럼 3개 DROP(신규 PC 재현) → GET 500 → restart → `[OK] migration applied` → 컬럼 복구 → GET 200 |
| #3 connections | 200 |
| #4 tz-aware `+09:00` / naive | 200 / 200 (회귀 유지) |
| #2 audit_logs OPERATOR 주입 | 200 + OPERATOR 행 정상 노출 (이전 500) |
| #1 생성 기본 role | USER 확정 |

### 왜 개발 PC엔 무문제였나

- #5·#6: v61 수동 적용해둠 → 개발 DB엔 컬럼 존재. 신규 PC는 create_all()만 → 컬럼 없음
- #1·#2: 개발 `.env`는 INIT_SAMPLE_DATA=false. docker-compose 기본은 `:-true` → 신규 PC 샘플 시드가 OPERATOR 주입
- #3·#4: 해당 조건으로 endpoint 호출한 적 없어 미발견

### 통지

`docs/GOP_Server_API_clone_deploy_bugfix_REPLY.md` — 6개 버그 근본원인·수정·재발방지 정리.

### v6.0-installer_ps2exe_path_fix — 자동 설치 근본 원인(PS2EXE 경로 소실) 규명·해결 (2026-07-07)

> 이슈: 다른 PC에서 gitea clone 후 `bootstrap.ps1` 자동 설치 시 인증서 발급 실패 → HTTP 로그인됨.
> 원 문서: `docs/prds/GOP_API_Server_자동설치_문제점_정리.md` (설치 팀 작성, winget PATH 문제로 추정)

### 근본 원인 규명 (실측)

원 문서는 winget PATH 미반영으로 추정했으나 **현재 코드는 winget 미사용**(GitHub 직접 다운로드).
진짜 원인은 **PS2EXE로 빌드된 EXE에서 스크립트 경로 변수가 전부 빈 문자열**:

| 변수 (PS2EXE EXE 실행 시) | 값 |
|---|---|
| `$PSScriptRoot` | `''` |
| `$MyInvocation.MyCommand.Path` | `''` |
| `$PSCommandPath` | `''` |
| `$MyInvocation.MyCommand.Definition` | (소스코드 — 경로 아님) |
| **`MainModule.FileName`** | **EXE 절대경로** ← 유일 신뢰 가능 |

→ `server_install.ps1:25` else 분기 `Split-Path -Parent ''` → `ScriptRoot=''` → `CertDir=''` → `Join-Path '' 'server.crt'` 실패/CWD 오생성 → bootstrap이 `certs\server.crt` 못 찾아 실패.

### 왜 개발 PC엔 무문제였나

1. 개발 PC엔 `certs\server.crt/key` 이미 존재 → bootstrap이 EXE 실행 자체를 스킵
2. mkcert가 PATH에 이미 설치 → 다운로드 경로 안 탐
3. "신규 PC 조건(인증서 없음 + mkcert 없음)"을 EXE로 재현 테스트한 적 없음 → PS2EXE 경로 버그 잠복

### 픽스 (3층 + 부수)

| Layer | 파일 | 내용 |
|---|---|---|
| **L1** | `certs/installer_ps2exe/server_install.ps1` | 경로 획득을 `MainModule.FileName` 폴백으로 (PS2EXE-safe). CertDir 빈값 시 CWD 폴백 방어 |
| **L2** | `certs/installer_ps2exe/server_install.ps1` | `-NonInteractive` 스위치 — 추가 SAN 입력/종료 대기 `Read-Host` 스킵 (자동화 정지 제거) |
| **L3** | `bootstrap.ps1` | server_install.exe 호출에 `-CertDir "$certDir" -NonInteractive -WorkingDirectory $certDir` 명시. 발급 후 `certs\certs` 중첩 등 오생성 재귀 탐색 안전망 |
| **L4** | `.gitignore` | `certs/mkcert.exe`, `certs/tools/` 커밋 방지 (신규 PC 자동 다운로드 ~5MB) |
| **부수** | bootstrap.ps1 | `-NonInteractive` param + UAC 재실행 전파 + 완료 안내 Read-Host 조건화 |

### EXE 재빌드 + 실측 검증 (2026-07-07)

`build_install_exe.ps1` 로 `server_install.exe`·`client_install.exe` 재빌드. PS2EXE 경로 로직을 EXE로 실행 검증:

| 시나리오 | ScriptRoot | CertDir | crt 대상 |
|---|---|---|---|
| A. 신규 PC 재현 (EXE는 certs\, CWD=USERPROFILE) | `...\certs` ✅ | `...\certs` ✅ | `...\certs\server.crt` ✅ |
| B. `-CertDir` 명시 (bootstrap 방식) | `...\certs` ✅ | `...\certs` ✅ | `...\certs\server.crt` ✅ |

수정 전이었다면 A에서 CertDir=`''` → 실패. 수정 후 두 시나리오 모두 정확한 경로 반환.

### 재발 방지 원칙

1. PS2EXE 빌드 스크립트는 경로를 `MainModule.FileName` 으로 획득
2. 인증서 경로는 호출측(bootstrap)이 `-CertDir` 명시 전달
3. PS2EXE EXE는 `-NonInteractive` 로 무인 실행 가능해야
4. "신규 PC 시나리오" 릴리스 전 clean 환경 재현 검증 필수
5. 스크립트 수정 후 반드시 EXE 재빌드

### 통지 문서

`docs/GOP_Server_API_installer_ps2exe_path_fix_REPLY.md` — 설치 팀에 근본 원인·수정·재발방지 정리.

### v6.0-users_role_response_relax — AccountUserResponse.role 응답 500 근본 시정 (2026-07-06)

> 이슈 리포트: 다른 PC 배포 팀. `admin` 로그인 후 `GET /api/users?page=1&limit=100` → HTTP 500
> `INTERNAL_ERROR: input_value='OPERATOR', input_type=str` (Enum 검증 실패).
>
> **v6.0-servers_port_response_relax 와 정확히 동일 패턴** — 응답 스키마에 요청 제약 복사한 설계 실수.

### 원인 자인 (반복된 실수)

`v5.3 Phase 2` (2026-07-02) 에서 `EnumUserRole` 축소 (5종 → 2종: ADMIN/USER). 그러나:
- 응답 스키마 `AccountUserResponse.role: EnumUserRole` 그대로 유지 (요청과 동일 제약)
- DB에 옛 role 값(`OPERATOR`, `MAINTAINER`, `VIEWER`, `GUEST`) 잔재
- `example="OPERATOR"` 로 v5.3 이후 무효 값을 예시로 유지 (더 웃긴 지뢰)
- 결과: 옛 role 사용자가 목록에 있으면 pydantic 검증 실패 → 목록 전체 500

이전 사이클 `v6.0-servers_port_response_relax` §7 에서 "유사 필드 감사 별도 사이클 예정"이라 했으나 실행 지연 → 이번 재발.

### 픽스 2층 방어 (servers 케이스와 동일 방법론)

#### L1. 응답 스키마 Enum → str (`app/schemas/user.py`)

| 스키마 | 필드 | 이전 | 이후 |
|---|---|---|---|
| `AccountUserCreate.role` | 요청 | `Optional[EnumUserRole]` | **유지** (새 데이터 위생) |
| `AccountUserUpdate.role` | 요청 | `Optional[EnumUserRole]` | **유지** |
| **`AccountUserResponse.role`** | 응답 | `EnumUserRole` | **`str`** + description 갱신 + example `"OPERATOR"` → `"USER"` |
| **`AccountUserNestedResponse.role`** | 응답 (중첩) | `EnumUserRole` | **`str`** |
| **`UserSessionResponse.role`** | 응답 (세션 JOIN) | `Optional[EnumUserRole]` | **`Optional[str]`** |

#### L2. 목록 fault tolerance (`app/routers/users.py` `get_users`)

- `AccountUserResponse.model_validate(u)` 를 try/except로 감싸 실패 시 `logger.warning(...)` + skip
- 한 행이 스키마 위반이어도 나머지 정상 사용자는 그대로 반환
- 헬퍼 신설 대신 for 루프 인라인 (`servers` 케이스는 헬퍼 방식이었으나 여기는 사용처 1곳이라 인라인)

### 실측 (2026-07-06)

| # | 시나리오 | HTTP | 결과 |
|---|---|---|---|
| 1 | 회귀 (정상 상태) | 200 | 12 rows |
| 2 | `UPDATE account_users SET role='OPERATOR' WHERE id=23` 인위 주입 | — | 저장 확인 |
| 3 | **재실측** GET /api/users | **200** ✅ | **12 rows + id=23 role=OPERATOR 그대로 노출** |
| 4 | 원위치 `UPDATE ... SET role='USER'` | — | 정상 복구 |

이전 500 케이스가 이번 픽스 이후 200 정상 처리 확인.

### 데이터 위생 조치 (원격/다른 PC GOP DB 조치 요청)

REPLY 문서: `docs/GOP_Server_API_users_role_response_relax_REPLY.md`

```sql
BEGIN;
UPDATE account_users
   SET role = 'USER', updated_at = NOW()
 WHERE role IN ('OPERATOR', 'MAINTAINER', 'VIEWER', 'GUEST');
COMMIT;
```

`audit_logs.actor_role` 은 append-only 정책상 건드리지 않음 (이력 보존).

### 후속 감사 약속

`v6.0-servers_port_response_relax` §7 에서 예고한 "유사 필드 감사" 를 이번 이슈로 즉시 착수. 예정 태그: **`v6.0-response_schema_audit`**.

대상: 모든 `*Response` 스키마의 Enum/제약 필드가 응답 관대 원칙 위배하지 않는지 스캔.

### v6.0-swagger_v6_notes — Swagger description v6.0 업데이트 (2026-07-06)

> 사용자 요청 — "Swagger에도 v6.0 업데이트 내용 정리해줘. v5.4까지만 있어."
> `/docs` 상단 description에 v6.0 하이라이트를 담아 배포/클라 팀이 API 진입 시 즉시 최신 컨텍스트 파악 가능하도록.

### 변경 (`app/main.py` FastAPI description)

- `API Version: 5.4 (2026-06-30)` → `6.0 (release/v6.0 브랜치, 후속 픽스 진행 중)`
- 신규 섹션 **"v6.0 주요 업데이트 (2026-07-03 ~ 진행 중)"** 4 카테고리로 정리:
  - **Async 대전환** (`v6.0`): SQLAlchemy 2.x + asyncpg, 41 라우터 async 100%, api_logs 파티셔닝, autoheal
  - **리포트 시스템** (`v6.0-report_*` 4 태그): 컬럼 확장/필터 통일 · Startup 재조정 + PDF 영속화 · 진행률 + Stall 워치도그 + SQL 집계 이관 · 커스텀 날짜 범위
  - **인증 · 계정** (`v6.0-auth_*`, `v6.0-account_*` 3 태그): AUTH_MODE=token secure default · ADMIN 9종 Static seed
  - **API 계약 개선**: `ServerResponse.port` ge=1→ge=0 · PDF 소실 시 HTTP 410
  - **인프라 · 배포** (3 태그): pids-api-* rename · 인증서 fail-fast · bootstrap.ps1 1-Click
- 신규/변경 endpoint 표 6건 (`/generations/{id}` progress 필드, `/generate` start_date/end_date, `/detail.csv`, `/cancel`, `/download` 410, `/servers` port relax)

### 실측 검증

- `curl https://localhost:8000/openapi.json` → description 4,210 자
- 12 v6.0 태그 마커 전부 존재 확인 (`v6.0`, `v6.0-report_fixes`, ..., `v6.0-bootstrap_automation`)
- Swagger UI `/docs` 상단에서 렌더링 확인

### v6.0-bootstrap_automation — clone → 1클릭 HTTPS 배포 (2026-07-06)

> 사용자 요청 — "다른 PC 에서 git clone 하면 docker build 로 HTTPS 까지 자동으로 되나?"
> 완전 자동은 인증서의 호스트 관리자권한 특성상 불가지만, **1스크립트 실행**으로 최소화.

### 배포 절차 변화

| 시점 | 조치 |
|---|---|
| 이전 (수동 다단계) | clone → certs 발급 여부 확인 → mkcert 설치 판단 → docker build → up → cert 오류 시 원인 파악 |
| **v6.0-bootstrap_automation** | **clone → `bootstrap.ps1` 실행** — 나머지 자동 |

### 신규 파일

- **`bootstrap.ps1`** (프로젝트 루트) — Windows PowerShell 5.1+ 대상
  - 관리자 권한 UAC 자동 상승
  - Docker Desktop 실행 상태 검증
  - `.env` 없으면 `.env.example` 복사
  - `certs/server.crt` 없으면 `certs/server_install.exe` 자동 호출 → mkcert 다운로드 + rootCA 등록 + 인증서 발급
  - `docker compose build` → `up -d` → `pids-api-server` healthy 대기(최대 120s)
  - 접속 URL · 계정 · rootCA 배포 안내
  - **옵션 스위치**: `-SkipCerts`, `-SkipDocker`, `-Rebuild`, `-AllowHttpFallback`
  - UTF-8 BOM 저장 (WinPS 5.1 CP949 오해석 방지)

### 재빌드된 인스톨러 EXE (v6.0-cert_installer_fix 반영)

- `certs/server_install.exe` (35KB) — 버그 3 CertDir 로직 픽스 반영
- `certs/client_install.exe` (36KB) — rootCA embed

이전 EXE 는 옛 폴더 구조 참조 + BOM 없는 상태로 빌드된 지뢰였음. 이번 재빌드로 clone 시 즉시 사용 가능.

### README 업데이트

Quick Start 섹션 재구성:
- 🚀 **1-Click 배포** (권장) — `bootstrap.ps1` 실행 절차
- 🔧 **수동 배포** (Linux/macOS/세부 제어) — mkcert 직접 사용
- 매니저 계정 8종 안내 (m_manager 외 v6.0-account_managers_expand 5종 포함)
- 클라이언트 PC rootCA 배포 방법 (`certs/client_install.exe`)

### 자동화 한계 (기술적)

**완전 자동은 불가** — 근본 이유:
- 인증서(`certs/*.crt`, `*.key`, `*.pem`)는 gitignore 필수 (보안). clone 에 포함될 수 없음
- `mkcert` 는 호스트 OS 신뢰 저장소에 rootCA 를 등록해야 함 → **호스트 관리자권한 필수** → 컨테이너 안 자동 실행 불가

`bootstrap.ps1` 은 이 한계 안에서 **사용자 조치를 "스크립트 1회 실행"** 으로 압축한 방식이며, 이론상 이보다 더 자동화하기는 어려움.

### 실측

- PS2EXE 모듈 자동 설치 (`Install-Module -Name ps2exe -Scope CurrentUser`)
- `build_install_exe.ps1` 실행 → 새 EXE 2종 재빌드 성공 (2026-07-06 22:16:34)
- `bootstrap.ps1` PowerShell 파서 `PARSE OK` (0 syntax errors)
- BOM 확인: `efbbbf` ✅
- Docker Desktop 이미 실행 상태에서 기존 컨테이너 healthy 유지

### v6.0-servers_port_response_relax — servers.port=0 응답 500 근본 시정 (2026-07-06)

> 이슈 제기: SensorwayManagers 팀 (`docs/prds/GOPDB_servers_port0_issue.md`).
> 원격 GOPDB `GET /api/servers` 가 이미 저장된 `port=0` 행 때문에 목록 응답 직렬화 단계에서
> `ServerResponse.port ge=1` 검증에 걸려 **목록 전체 500 (INTERNAL_ERROR)** 발생.

### 원인 (서버측 설계 실수 자인)

**요청은 엄격, 응답은 관대**(Postel's Law)가 API 설계 원칙인데, **응답 스키마에도 요청과 동일한 `ge=1` 제약**을 그대로 부여한 것이 지뢰. DB에는 옛 SensorwayManagers 옵션 default(`ManagerServerPort=0`)로 저장된 `port=0` 행이 남았고, 스키마를 뒤에 강화하면서 그 행이 응답에 담길 때 pydantic 검증 실패 → 목록 전체 500.

**행 1개가 목록 엔드포인트 전체를 죽이는** blast radius 문제이기도 함.

### 픽스 (2층 방어)

#### L1. 응답 스키마 제약 완화 (`app/schemas/server.py`)

| 스키마 | 필드 | 이전 | 이후 |
|---|---|---|---|
| `ServerCreate.port` | 요청 | `Field(..., ge=1, le=65535)` | **유지** (새 데이터 위생) |
| `ServerUpdate.port` | 요청 | `Optional[int]... ge=1, le=65535` | **유지** |
| **`ServerResponse.port`** | 응답 | `Field(..., ge=1, le=65535)` | **`Field(..., ge=0, le=65535)`** — port=0 허용 |
| **`ServerNestedResponse.port`** | 응답 (중첩) | `Field(..., ge=1, le=65535)` | **`Field(..., ge=0, le=65535)`** |

description도 `"서버 포트 (0~65535, 0=미지정)"` 로 갱신.

#### L2. 목록 fault tolerance (`app/routers/servers.py`)

- `_safe_server_to_response(server)` 헬퍼 신설 — try/except로 감싸 실패 시 `logger.warning(...)` + `None` 반환
- `list_servers` / `get_server_summary` 목록 컴프리헨션을 walrus + `None` 필터로 변경
- **한 행이 스키마 위반이어도 나머지 정상 행은 그대로 반환**. WARN 로그로 관측 가능
- 단건 조회(`get_server`)는 이 헬퍼를 쓰지 않음 — 단건은 실패 시 명확히 알려주는 게 옳음

### 실측 (2026-07-06)

| 시나리오 | HTTP | 결과 |
|---|---|---|
| 회귀: 정상 상태 GET /api/servers | 200 | 14 rows 정상 |
| **인위 주입**: `UPDATE servers SET port=0 WHERE id=3` (VMS-ab1120) | — | port=0 저장 확인 |
| **재실측**: GET /api/servers (port=0 존재 상태) | **200** | **14 rows 정상 응답 + id=3의 port=0 그대로 노출** |
| 원위치: `UPDATE servers SET port=8080 WHERE id=3` | — | 정상 복구 |

**즉 이전엔 500이었을 상황이 이제 200으로 정상 처리됨.** L1이 근본 해소, L2는 미래 다른 스키마 위반 대비 방어깊이.

### 데이터 위생 (SensorwayManagers 팀 조치 요청)

서버측 픽스는 **응답 500을 막는 대증요법에 가깝고**, 근본은 **원격 GOPDB의 `port=0` 행 자체를 정리**하는 것.
아래 SQL을 GOP DB 관리자가 원격 실행 권장:

```sql
-- 진단
SELECT id, name, ip_address, port
  FROM servers
 WHERE port = 0;

-- 유효값으로 갱신 (권장 — 이력 보존)
UPDATE servers SET port = 1 WHERE port = 0;
```

응답 문서: `docs/GOP_Server_API_servers_port0_issue_REPLY.md`

### v6.0-account_managers_expand — 장비 도메인별 ADMIN 매니저 5종 추가 (2026-07-06)

> 사용자 요청 — 장비 도메인별 매니저 계정 5종 Static seed에 추가.

### 추가 계정 (DEFAULT_ADMIN_ACCOUNTS)

| login_id | password | role | 이름 |
|---|---|---|---|
| **CameraManager** | sensorway1 | ADMIN | Camera 매니저 |
| **BroadcastingManager** | sensorway1 | ADMIN | Broadcasting 매니저 |
| **QLiteLampManager** | sensorway1 | ADMIN | QLiteLamp 매니저 |
| **NVRManager** | sensorway1 | ADMIN | NVR 매니저 |
| **EnclosureManager** | sensorway1 | ADMIN | Enclosure 매니저 |

- 저장: bcrypt 해시. group_id NULL (ADMIN bypass).
- Idempotent — 재빌드/재시작 시 이미 존재하면 스킵 (사용자가 변경한 password 보존).

### 계정 인벤토리 (9종 ADMIN + 3종 USER)

| Static seed ADMIN (v6.2 + v6.0-account_managers_expand) |
|---|
| admin / m_manager / vms_manager / popup_manager |
| CameraManager / BroadcastingManager / QLiteLampManager / NVRManager / EnclosureManager |

### 실측 검증 (2026-07-06)
- Startup 로그: `[OK] AccountUser {5종} created (role: ADMIN)` (기존 4종은 `already exists`)
- DB: id 24~28 신규, role=ADMIN, group_id NULL 확인
- Login: 5계정 전부 `POST /api/auth/login` 200 + access_token (207~219자) 발급 성공

### v6.0-cert_installer_fix — 인증서 인스톨러 6 버그 픽스 + HTTPS 강제 (2026-07-06)

> 사용자 리포트: 다른 PC에서 git clone 후 build했더니 HTTP로 로그인됨. 클라(.NET) SSL 실패 → 503.
> **근본 원인**: 인증서 설치 실패 후 서버가 조용히 HTTP로 fallback → healthcheck·클라 HTTPS 강제와 충돌.
> 6 버그 일괄 정리 + HTTPS 정책 강화.

### 픽스 (6 버그)

| # | 버그 | 원인 | 픽스 |
|---|---|---|---|
| **1** | `server_install.ps1` UTF-8 BOM 없음 | Windows PS 5.1이 CP949로 오해석 → 한글 파싱 실패 | 현재 파일 BOM 있음 확인 (`efbbbf`). CERT_INSTALLER_README에 저장 규칙 명시 |
| **2** | 기존 `server_install.exe`가 깨진 스크립트로 빌드 | PS2EXE가 빌드 시점 코드 embed → 원본 수정해도 EXE 안 바뀜 | README에 재빌드 필요 시점 표 명시. 이번 픽스 반영 EXE 재빌드 필요 |
| **3** | `server_install.ps1` CertDir 경로 오류 | `Join-Path $PSScriptRoot 'certs'` — PS1 직접실행/EXE실행 구분 없음 | 본문 계산: `$script:ScriptRoot -like '*installer_ps2exe*'`이면 상위 폴더, 아니면 EXE 위치 사용 |
| **4** | `build_install_exe.ps1` 잘못된 경로 참조 | `certs\installer\scripts\server_install.ps1` (구 구조) 사용 | `Join-Path $PSScriptRoot 'server_install.ps1'` (같은 폴더) |
| **5** | `build_install_exe.ps1` param 기본값 null | `$MyInvocation.MyCommand.Path`가 `powershell.exe -File` 실행 시 null | param에 빈 문자열, 본문에서 `$PSScriptRoot` 기반 계산 |
| **6** | **HTTP fallback vs HTTPS 강제 충돌** | Dockerfile CMD가 인증서 없으면 조용히 HTTP fallback → healthcheck(HTTPS)/클라(HTTPS)와 충돌 | Fail-fast + opt-in HTTP (아래 상세) |

### Dockerfile CMD 정책 강화

3 모드 정의:

| 조건 | 동작 |
|---|---|
| `/app/certs/server.crt` + `server.key` 존재 | `[HTTPS] certs OK - uvicorn HTTPS 기동` → HTTPS 8000 |
| 인증서 없음 + `ALLOW_HTTP_FALLBACK=true` (opt-in) | `[WARN]` bar × 3줄 → HTTP 8000 (개발/시연 편의) |
| 인증서 없음 + `ALLOW_HTTP_FALLBACK=false` (기본) | **`[FATAL]` bar + 조치 안내 3줄 → exit 1** (재시작 루프) |

`docker-compose.yml`에 `ALLOW_HTTP_FALLBACK=${ALLOW_HTTP_FALLBACK:-false}` env 파이프 추가.

### 실측 검증 (2026-07-06)

| 시나리오 | 결과 |
|---|---|
| 인증서 있음 | `[HTTPS] certs OK - uvicorn HTTPS 기동`, `HTTPS=200` |
| 인증서 임시 rename (`server.crt.bak`) | `[FATAL] ... 미존재 - 서버 기동 중단` × 조치 3줄, `exit 1`, `Restarting (1)` 상태 |
| `ALLOW_HTTP_FALLBACK=true` 강제 opt-in | `Uvicorn running on http://0.0.0.0:8000`, `HTTP=200` (평문) |
| 인증서 원위치 | `[HTTPS] certs OK - uvicorn HTTPS 기동`, `HTTPS=200` 복구 |

### PS1 파일 인코딩 (필수)

**모든 `.ps1`는 UTF-8 BOM으로 저장한다.**
- VS Code: 우하단 인코딩 → "UTF-8 with BOM"
- 확인: 파일 첫 3바이트가 `EF BB BF` (Python `print(open('x.ps1','rb').read(3).hex())` = `efbbbf`)
- 현재 3 파일 모두 BOM 있음 확인 (`server_install.ps1`, `client_install.ps1`, `build_install_exe.ps1`)

### EXE 재빌드 필요 (사용자 조치)

기존 `certs/server_install.exe` / `client_install.exe`는 **버그 스크립트로 embed된 상태**입니다.
아래 명령으로 재빌드하세요 (BOM 유지 + 픽스 반영):

```powershell
cd certs\installer_ps2exe
pwsh -ExecutionPolicy Bypass -File build_install_exe.ps1
```

결과:
- `certs\server_install.exe` (새 로직으로 embed)
- `certs\client_install.exe` (새 로직으로 embed)

### 다음 예상 이슈 (사용자 리포트에 언급됨)

HTTPS 해결 후 `test_user`가 로그인 전 startup에서 `GET /api/servers/1/proxy-settings` 호출 → **401 Unauthorized** 예상 (AUTH_MODE=token, RBAC enforced 상태).
클라 조치 필요 (서버측 무관):
- 로그인 완료 후 프록시 설정 조회
- 또는 초기화 순서를 DeviceProviderService 패턴(로그인 게이팅)에 맞추기

### v6.0-rename_pids — 컨테이너/이미지 이름 pids-api-* 로 rename (2026-07-06)

> 사용자 요청 — `api-test-server` → `pids-api-server`로 브랜딩 변경. **A안 (최소 침습)**: 컨테이너/이미지 이름만 변경, 볼륨·네트워크·데이터 100% 보전.

### 변경 (docker-compose.yml)

| 이전 | 이후 |
|---|---|
| `container_name: api-test-server` | `container_name: pids-api-server` |
| `image: api-test-server:latest` | `image: pids-api-server:latest` |
| `container_name: api-test-postgres` | `container_name: pids-api-postgres` |
| `container_name: api-test-db-monitor` | `container_name: pids-api-db-monitor` |
| `image: api-test-db-monitor:latest` | `image: pids-api-db-monitor:latest` |
| `container_name: api-test-gis-ingest` | `container_name: pids-api-gis-ingest` |
| `image: api-test-gis-ingest:latest` | `image: pids-api-gis-ingest:latest` |
| `container_name: api-test-autoheal` | `container_name: pids-api-autoheal` |
| `container_name: api-test-db-admin` | `container_name: pids-api-db-admin` |

### 유지 (A안 원칙 — 데이터 보전)

- **볼륨 이름**: `api-test-pgdata`, `api-test-reports` 유지 → postgres 데이터 66,004 detections + 10 reports 등 100% 보전
- **볼륨 접두어**: `api-test-server_*` 유지 (compose 프로젝트 이름 = 폴더명 기반)
- **폴더 이름**: `c:\workspace_python\api-test-server` 유지
- **CLAUDE.md `project_name`**: 유지 (프로젝트 논리 이름)
- **서비스 이름** (compose 내): `api-server`, `postgres`, `db-monitor`, `gis-ingest` 유지 → 컨테이너간 통신(DATABASE_URL 등) 무영향

### 부수 정합화
- `scripts/seed_period_data.py:12` docstring — `docker exec api-test-server` → `docker exec pids-api-server`
- `README.md` 아키텍처 다이어그램 서비스 라벨 — `api-test-server` → `pids-api-server`

### 실측 검증 (2026-07-06)

| 항목 | 결과 |
|---|---|
| `docker compose down` (볼륨 보존) | ✅ 컨테이너 6개 제거, `api-test-server_default` 네트워크 제거 |
| `docker compose build` | ✅ 3 이미지 새 이름으로 빌드 (`pids-api-server:latest`, `pids-api-db-monitor:latest`, `pids-api-gis-ingest:latest`) |
| `docker compose up -d` | ✅ 6 컨테이너 전부 `pids-api-*` 이름으로 기동 |
| 볼륨 유지 | ✅ `api-test-server_api-test-pgdata`, `api-test-server_api-test-reports` 접근 정상 |
| Postgres 데이터 | ✅ users=7, servers=14, detection_events=66,004, report_generations=10 (rename 전과 동일) |
| Startup 로그 | ✅ 4개 ADMIN 이미 존재, sample servers 14대 존재, Reconciled: no stale |
| Auth | ✅ `AUTH_MODE=token (RBAC enforced)`, m_manager 로그인 200 + token 205자 발급 |
| Autoheal | ✅ `pids-api-server` label=autoheal 감지 (label 방식이라 이름 무관) |

### 잔여 옛 이미지 정리 (선택)

```bash
# 이전 이미지 3종 (재사용 불가) 정리하려면:
docker image rm api-test-server:latest api-test-db-monitor:latest api-test-gis-ingest:latest
# pre-v5.2 태그도 필요 없으면:
docker image rm api-test-server:pre-v5.2
```

### 위험도

**변경 없음** — Bearer 토큰 발급/응답 · DATABASE_URL · 앱 코드 · 클라(.NET) `localhost:8000` 접근 · NATS 통신 모두 무영향. 사용자 관점 유일한 변화는 `docker ps` 표시명과 `docker exec {이름} ...` 진입 이름.

### v6.0-report_date_range — 보고서 커스텀 날짜 범위 (2026-07-05)

> `PRD_GOP_Server_Reports_Custom_Date_Range` 구현. 클라(.NET) DatePicker 요청 대응.
> 파이프라인은 이미 임의 범위 지원 (`build_master_data_async(db, start, end, …)`) — 스키마 열기만 필요했음.

### 문제

- 요청 스키마 `ReportGenerateRequest`가 `period_type`(7d/30d/90d/1y)만 받음
- 핸들러가 무조건 `_calculate_date_range(period_type)` → `[now-N일, now]` 강제
- 클라가 임의 기간 (예: "2026-06-01 ~ 2026-06-15") 지정 불가

### 픽스 (FR-RCD-01~07)

| FR | 파일 | 픽스 |
|---|---|---|
| **FR-RCD-01** | `app/schemas/report.py` | `ReportGenerateRequest`에 `start_date/end_date: Optional[KSTDatetime]` 추가. `period_type` Optional 완화. Swagger example 3종 (프리셋/커스텀/템플릿) |
| **FR-RCD-02** | `app/routers/reports.py` `generate_report` | 분기: `start_date+end_date` 오면 그대로 사용 + `period_type="custom"` 저장. 없으면 기존 `_calculate_date_range(period_type)` (하위호환) |
| **FR-RCD-03** | `app/schemas/report.py` `model_validator` | 검증: 둘 다 있거나 둘 다 없음 / `end ≥ start` / `(end-start).days ≤ REPORT_MAX_RANGE_DAYS` |
| **FR-RCD-03** | `app/routers/reports.py` | 경계 정규화: `end` 시각이 `00:00:00.0`이면 `23:59:59.999999`로 확장 (끝일 포함 시맨틱) |
| **FR-RCD-04** | `app/utils/enums.py` | `EnumReportPeriod.CUSTOM = "custom"` 추가 |
| **FR-RCD-05** | `app/services/report_master_builder.py` `build_report_meta` | `period_label` / `period_days` 필드 신설. 프리셋은 "최근 7일" 유지, 커스텀은 "2026.06.14 ~ 2026.06.28 (15일)" 형식 |
| **FR-RCD-06** | `app/routers/reports.py` preview-page | `period_days` 재계산: `custom`이면 실제 `(end-start).days`, 프리셋이면 매핑값 fallback |
| **FR-RCD-07** | `app/config.py` | `REPORT_MAX_RANGE_DAYS: int = 366` env 신설 |

### 요청 예시

**하위호환 (기존)**:
```json
{ "report_type": "STANDARD", "period_type": "7d", "title": "주간 보고서" }
```

**커스텀 범위 (신규)**:
```json
{
  "report_type": "STANDARD",
  "title": "2주 커스텀 보고서",
  "start_date": "2026-06-15T00:00:00+09:00",
  "end_date": "2026-06-28T00:00:00+09:00"
}
```
저장 결과: `period_type="custom"`, `start_date=6/15 00:00 KST`, `end_date=6/28 23:59:59.999 KST` (끝일 포함).

### 실측 검증 (2026-07-05)

| 시나리오 | 결과 |
|---|---|
| [1] 하위호환 `period_type=7d`만 | HTTP 200, id=38, `period_type=7d`, start/end = now-7d ~ now |
| [2] 커스텀 (start+end 날짜만) | HTTP 200, id=39, `period_type=custom`, start=6/15 00:00 KST, end=6/28 23:59:59.999 KST |
| [3] `end < start` | HTTP **422** — "end_date가 start_date보다 이릅니다" |
| [4] 상한 초과 (430일 > 366) | HTTP **422** — "범위가 상한을 초과합니다 (430일 > REPORT_MAX_RANGE_DAYS=366일)" |
| [5] id=39 preview HTML 헤더 | `2026.06.14 — 2026.06.28` 실제 범위 표시 확인 |

### 클라 (.NET) 계약 통지

- 요청: `start_date`/`end_date` 필드 (KSTDatetime, ISO8601 `+09:00`) — 둘 다 필수 (한 개만 오면 422)
- 응답: `period_type="custom"` 시 프리셋 라벨 대신 실제 범위 표시
- 경계 시맨틱: **끝일 포함** (end가 `00:00`이면 자동으로 그날 23:59:59.999로 확장)
- 상한: 366일 (env `REPORT_MAX_RANGE_DAYS`로 조정 가능)

### v6.0-auth_mode_secure_default — AUTH_MODE 기본값 token 뒤집기 + 부팅 WARN (2026-07-05)

> 사용자 질문 "깃으로 받으면 public으로 동작하나?" 후속 조치. 깃 clone 후 그대로 `docker compose up` 하면 RBAC 무집행 상태로 노출되는 보안 위험 근본 봉합.

**이전 동작**:
- `.gitignore:49`에 `.env*` — 깃에는 `.env` 없음
- `docker-compose.yml:49`: `AUTH_MODE=${AUTH_MODE:-public}` → env 없으면 **public 폴백**
- 클론 → docker up → **Bearer 없이 API 접근 가능** (실수 배포 시 무인증 노출)

**변경**:
| 파일 | 이전 | 이후 |
|---|---|---|
| `docker-compose.yml:49` | `AUTH_MODE=${AUTH_MODE:-public}` | `AUTH_MODE=${AUTH_MODE:-token}` (secure by default) |
| `app/main.py` lifespan | `Authentication Mode: {mode}` 한 줄 | mode == "public" 이면 **큰 WARN 3줄** (`!!!!` bar + 원인 + 조치 안내) |
| `app/config.py:88` validator | 유지 (staging/prod에서 public 거부) | 유지 |

**Secure by default 3중 방어**:
1. **기본값 token** (docker-compose) — 클론 후 즉시 안전 상태
2. **부팅 WARN** (main.py) — 실수로 public 배포 시 즉시 로그로 감지
3. **staging/prod 거부** (config.py validator) — `ENVIRONMENT=production/staging`에서 public 강제 거부

**실측 검증 (2026-07-05)**:
- Env 없이 부팅 → `Authentication Mode: token (RBAC enforced)` (secure default)
- `AUTH_MODE=public docker compose up` (강제 override) → 부팅 로그:
  ```
  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  [WARN] Authentication Mode: PUBLIC — RBAC dormant, Bearer 없이 API 접근 가능
  [WARN] 프로덕션 배포 시 .env 또는 환경변수에 AUTH_MODE=token 명시 필요
  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  ```
- `.env`에 `AUTH_MODE=token` 있는 로컬 환경 → 동일 `Authentication Mode: token (RBAC enforced)` (기존 개발 동작 무변경)

**클라 관점 (v6.0_report_updates_NOTIFY.md 보완)**:
- 깃 clone + docker up으로 서버 띄운 클라 세션(.NET)은 이제 **Bearer 필수** 로 동작
- 개발 편의로 public이 필요하면 `.env`에 `AUTH_MODE=public` 명시적 지정 (당장 auth 없이 API 테스트 필요할 때)

### v6.0-report_progress_perf — 진행률 + Stall 워치도그 + SQL 집계 이관 (2026-07-05)

> 사용자 요청 — "타임아웃보다 진행률 계산하고 stall만 kill하는 게 낫지 않아?"
> id=30이 180s wall-clock으로 kill되던 사례를 근본 해결: **정상 진행 중이면 시간 무제한, hang만 kill**.

**성능 회복 실측**:
| 리포트 | 이전 (wall-clock 180s) | v6.0-report_progress_perf | 개선 |
|---|---|---|---|
| id=30 (7d, 66k det + 26k mal) | 180s → FAILED "timeout" | (해당 없음 — 파이썬 병목 제거로 회피) | ∞ → success |
| id=31 (v6.0-report_progress_perf test) | — | **20s 이내 COMPLETED** (T+10s 80%, T+20s 100%) | 사실상 신규 가능 상태 |

### P1. SQL 집계 이관 (build_master_data_async 최적화)
`app/services/report_master_builder.py` — 파이썬 for 루프에서 처리하던 통계(Counter)를 postgres GROUP BY로 이관.

| 섹션 | 이전 (파이썬 66k iter) | 이후 (SQL GROUP BY) |
|---|---|---|
| §3 탐지 by_type / by_zone / by_hour / det_done | Counter 4개 for 루프 | 4개 SQL 각 GROUP BY, zone은 sensors.geolocation approximation |
| §4 장애 mal_reason | Counter for 루프 | GROUP BY SQL |
| §3~9 상세 rows | 전량 fetch (수만~수십만) | `LIMIT 500` (사용자 결정 Y — 전량은 CSV 다운로드로 100% 보전) |

### P2. 진행률 스키마 (마이그레이션 v61)
`app/migrations/v61_report_generation_progress.sql`:
- `progress_pct INT DEFAULT 0` (0~100)
- `progress_stage VARCHAR(50)` — 예: `start`, `setup`, `master_data`, `html`, `pdf`, `done`
- `progress_updated_at TIMESTAMP` — stall 감지 기준
- 종료 상태(COMPLETED/FAILED/CANCELLED)는 100%로 백필
- `ix_report_generations_stall` 부분 인덱스 (status IN ('PENDING','GENERATING') 조건)

`app/models/report.py` 3 컬럼 동기 반영. `_generation_to_response` 응답에 3필드 포함.

### P3. Stage 진행률 발화 (`_do_generate`)
`app/routers/reports.py` — 각 stage 완료 후 `_progress(pct, stage)` 호출:

| pct | stage | 위치 |
|-----|-------|------|
| 5 | `start` | GENERATING 마킹 직후 |
| 10 | `setup` | ReportServiceAsync + meta 준비 완료 |
| 60 | `master_data` | build_master_data_async 완료 |
| 80 | `html` | render_report_html_async 완료 |
| 95 | `pdf` | Playwright PDF 렌더 완료 |
| 100 | `done` | 파일 저장 + DB 커밋 완료 |

### P4. Stall 워치도그 (wall-clock timeout 제거)
`app/config.py`:
- `REPORT_GEN_TIMEOUT_SEC` **제거 (DEPRECATED)**
- 신규 `REPORT_GEN_STALL_TIMEOUT_SEC=60` (기본), `REPORT_GEN_STALL_CHECK_INTERVAL_SEC=10`

`_stall_watcher(generation_id, gen_task)` 워치도그 태스크가 10s마다 postgres 조회로 `NOW() - progress_updated_at > 60s` 확인. Stall 감지 시 `gen_task.cancel()`. 사용자 취소와 stall을 워치도그 결과로 구분:
- stall → status=FAILED, error_message="generation stalled (60s no progress)"
- 사용자 취소 → status=CANCELLED, error_message="Cancelled by user"

### P5. 상세 CSV 다운로드 endpoint
`GET /api/reports/generations/{id}/detail.csv?type={grid}` — PDF에서 상위 500행으로 잘린 원본 rows 전량. UTF-8 BOM (Excel 한글 호환), StreamingResponse.

| type | 헤더 예 | 기간 필터 |
|---|---|---|
| detection | ID, 일시, 장비명, 탐지유형, 조치보고, 구역, 조치건수, 장비설명 | ✅ |
| malfunction | ID, 일시, 장애유형, 장비명, 구역, 조치건수, 장비설명 | ✅ |
| action | ID, 일시, 유형, 내용, 조치자 | ✅ |
| system | ID, 일시, 유형, 심각도, 제목, 메시지 | ✅ |
| config | ID, 일시, 행위자, IP, 리소스유형, 리소스명, 리소스ID, 액션, 변경설명 | ✅ |
| audit | ID, 일시, 액션, 상태, 리소스, 행위자 | ✅ |
| login | ID, 일시, 로그인ID, 액션, 결과, IP | ✅ |
| session | ID, 로그인ID, 사용자명, IP, 생성일, 만료일 | (전량) |

권한: `reports.view` (permission_map 등록).

### 실측 검증 (2026-07-05)
- id=31 리포트 폴링: `T+10s [GENERATING] 80% stage=html` → `T+20s [COMPLETED] 100% stage=done`
- CSV 다운로드 4종 실측: detection 11,953 lines / malfunction 4,785 / audit 43 / config 58 — 정상 응답 + UTF-8 BOM
- Stall 워치도그: 정상 리포트가 20s에 완료돼 실제 stall 발동 사례 없음 (코드 리뷰로 검증)

### v6.0-report_lifecycle_persistence — 리포트 생성 수명주기 + PDF 영속화 (2026-07-05)

> 두 PRD를 한 사이클에 통합. 컨테이너 recreate가 리포트 시스템의 DB 상태(GENERATING 고착)와 파일시스템(PDF 소실) 두 층을 동시에 파괴하던 취약점 봉합.

**참조 PRD**:
- `PRD_GOP_Server_Reports_Generation_Lifecycle.md` (Draft, 2026-07-05) — id=29 stuck GENERATING 실측 근거
- `PRD_GOP_Server_Reports_PDF_Persistence.md` (Draft, 2026-07-05) — 다운로드 전건 404 실측 근거

**증거 (배포 전)**:
- `report_generations.id=29 "월간 표준보고서"` GENERATING **26분+ 잔류** (BackgroundTasks 인프로세스·비영속 → recreate 시 태스크 소멸)
- `docker-compose.yml` api-server에 `/app/reports` 마운트 없음 → 최근 PDF 소실, DB만 dangling

### Lifecycle 픽스 (FR-RGL-01~04)

| FR | 픽스 |
|---|---|
| **FR-RGL-01** | `app/main.py` lifespan에 startup 재조정 — `UPDATE report_generations SET status='FAILED' WHERE status IN ('PENDING','GENERATING') RETURNING id`. `error_message='server restarted during generation'`, `completed_at=NOW()`. 부팅 시 인프로세스 태스크 소실분 자동 정리 |
| **FR-RGL-02** | `app/config.py` `REPORT_GEN_TIMEOUT_SEC=180` (env). `app/routers/reports.py` `_run_report_generation`의 실작업을 nested `_do_generate()`로 감싸 `asyncio.wait_for(_do_generate(), timeout=…)` 실행. TimeoutError → FAILED (`"generation timeout ({N}s exceeded)"`) |
| **FR-RGL-03** | try/except/finally 확장 — finally에서 여전히 `PENDING/GENERATING`이면 최종 안전망으로 FAILED 확정. except 블록 commit이 실패해도 재확정 |
| **FR-RGL-04** | 모든 상태 전이 SQL/코드에 `status IN ('PENDING','GENERATING')` 조건절 명시. CANCELLED 미간섭 |

### Persistence 픽스 (FR-RPP-01/02/03/05)

| FR | 픽스 |
|---|---|
| **FR-RPP-01** | `docker-compose.yml` api-server에 `- api-test-reports:/app/reports` named volume 마운트 + top-level `api-test-reports:` 선언. 컨테이너 recreate/재빌드에도 PDF 유지 |
| **FR-RPP-02** | 정책 (a) — 기존 dangling COMPLETED는 그대로 두고 사용자 재생성 유도 (FR-RPP-03 런타임 응답으로 보완) |
| **FR-RPP-03** | `app/routers/reports.py` download 엔드포인트가 파일 부재 시 `404` 대신 `HTTP 410 Gone` + `{error_code: PDF_FILE_MISSING, message, report_id}`. 클라가 "없는 보고서(404)"와 "PDF 소실(410)"을 구분 |
| **FR-RPP-05** | `app/config.py` `REPORTS_DIR="/app/reports"` (env). `reports.py` `_run_report_generation` + `report_service.py` sync 경로 모두 이 상수로 통일 |

### 실측 검증 (2026-07-05, image rebuild + recreate 후)

| 항목 | 결과 |
|---|---|
| id=29 (stuck 26분+) | startup 로그 `[OK] Report generation reconciled: 1 stale → FAILED (ids: [29])` — DB status=FAILED, error_message="server restarted during generation" |
| id=30 (신규, 렌더 지연) | 정확히 180s에 timeout → status=FAILED, error_message="generation timeout (180s exceeded)", elapsed 188s |
| docker volumes | `api-test-server_api-test-reports` 신규 생성, `/app/reports`에 이전 PDF 유지 확인 |
| download 파일부재 (id=25) | `HTTP 410` + `{"error_code":"PDF_FILE_MISSING","message":"PDF file has been removed from storage (report re-generation required)","report_id":25}` |

### 별도 트랙 (이 사이클 미포함)
- **FR-RPP-04** — 컨테이너 healthcheck TLS 리스너 준비 후에만 healthy. 별도 인프라 사이클
- **FR-RGL-05** — durable queue 이관. dev 단계는 FR-01/02/03로 충분
- **PDF 렌더 성능** — id=30이 180s 넘긴 사유(build_master_data_async + Playwright)는 별개 성능 튜닝 트랙

### v6.0-account_rbac — 기본 ADMIN 계정 3종 Static seed (2026-07-05)

> 사용자 요청 — 팀 매니저 자동 생성으로 컨테이너 빌드 즉시 로그인 가능.

- `app/utils/init_db.py`:
  - `DEFAULT_ADMIN_ACCOUNTS` 상수 신설 (admin, m_manager, vms_manager, popup_manager)
  - 신규 3계정: password `sensorway1`, role `ADMIN`, group_id `NULL`(bypass), is_active `True`
  - password는 `hash_password()`(bcrypt)로 해시 저장
  - `create_admin_account_user` / `create_admin_account_user_async` 두 함수 모두 idempotent 순회 로직으로 재작성 (login_id 존재 시 스킵)
- 실측 검증 (2026-07-05):
  - startup: `[OK] AccountUser {m_manager|vms_manager|popup_manager} created (role: ADMIN)`
  - `SELECT * FROM account_users` — id 20/21/22 3계정 ADMIN + group_id NULL 확인
  - 3계정 전부 `/api/auth/login` 200 + access_token 발급 성공
- 정책 참조: 서버 인스턴스 Static seed 승격(v6.1)과 동일 방향 — 기본 계정도 코드로 고정된 Static seed
- 보안 노트: 하드코딩 password는 dev/시연 기본값. 프로덕션 배포 시 최초 로그인 후 변경 권장 (README 반영 대상)

### v6.0-report_fixes — 리포트/서버 초기화 데이터 정합화 (2026-07-04)

> 사용자 리포트 다운로드 실측 → 4건 결함 발견 및 일괄 픽스. 3중 감사 워크플로우로 원인 진단 후 동일 사이클 통합.

| Issue | 결함 | 원인 | 픽스 |
|-------|------|------|------|
| **1(a)** | JSON preview vs HTML/PDF 필터 소스 이중화 | `ReportServiceAsync.get_structured_preview_data`가 `generation.period_type→days`로 재계산 (`datetime.now()-Ndays`), HTML/PDF는 `generation.start_date/end_date` 사용 → 같은 리포트 두 뷰가 다른 데이터 | `_resolve_range(days, start_date, end_date)` 헬퍼 도입, 라우터에서 `generation.start_date/end_date` 전달, 각 도메인 함수 시그니처 확장 |
| **1(b)** | role 라벨 소스별 상이 (ADMIN vs 관리자) | JSON preview는 원문, HTML/PDF는 `L.label(L.ROLE, ...)` | ReportServiceAsync 전 도메인에 `L.label` 통일 (ROLE/SEVERITY/DETECTION/FAULT/DEVICE_CATEGORY/CONFIG_RESOURCE/CONFIG_ACTION/AUDIT_ACTION/AUDIT_RESOURCE/LOGIN_ACTION/RESULT/SYSTEM_EVENT/ACTION_TYPE) |
| **1(c)** | event_statistics dates 라벨 off-by-one | `range(days)` → 오늘 미포함, DB 필터는 오늘 포함 | dates를 `[_start.date() … end.date()]` inclusive 생성 |
| **2** | 세션 목록 user_id 정수만 표시 | `select id, user_id, ip_address, ...` — account_users 조인 부재 | `LEFT JOIN account_users ON u.id = user_sessions.user_id`, 컬럼 `[ID, 로그인ID, 사용자명, IP, 생성일, 만료일]` 확장 (sync + async 두 파이프라인) |
| **3-a** | audit_logs 행위자 공란 | actor_name만 사용, nullable | `COALESCE(actor_name, actor_login_id, '(system)')` 폴백 |
| **3-b** | config_change_logs `누가 무엇을 어떻게` 미표시 | `[ID, 일시, 리소스유형, 액션, 리소스ID]` 만 노출 | `[ID, 일시, 행위자, IP, 리소스유형, 리소스명, 액션, 변경설명]` 8컬럼 확장 |
| **3-c** | system_events title 컬럼 누락 | title NOT NULL이지만 리포트에서 제외 | `[ID, 일시, 유형, 심각도, 제목, 메시지]` 6컬럼 확장 |
| **4** | Define된 서버 인스턴스 미생성 (servers 0행) | `init_db.py`가 `initialize_server_data(db)` (인자 없이) 호출 → default `include_samples=False`로 진입 | (1) default를 True로 뒤집기 (Static seed 정책), (2) `DEFAULT_SAMPLE_SERVERS` 상수화 + 9카테고리 전부 커버 (14대 — TRANSCODER/DB_API/NVR_API/SPEAKER_API/ENCLOSURE_API 5종 신규), (3) `_build_sample_server_rows` 헬퍼 sync/async 공용화 |
| **부수 B** | N+1 쿼리 (탐지/장애 그리드) | 이벤트당 `select ActionEvent where from_event_id=e.id` 개별 조회 (3320건=3320회) | `select where from_event_id.in_(event_ids)` 1회 batch fetch + dict lookup |

### Changed (v6.1)
- `app/utils/init_server_data.py`: `include_samples` default False → True; `DEFAULT_SAMPLE_SERVERS` 14종 (9 카테고리 커버); sync/async 공용 `_build_sample_server_rows` 헬퍼
- `app/services/report_service.py`: `ReportServiceAsync._resolve_range` 헬퍼, 10 도메인 함수 시그니처에 `start_date/end_date` keyword 추가, N+1 batch fetch, L.label 통일
- `app/services/report_master_builder.py`: sync `build_master_data` + async `build_master_data_async` 두 파이프라인의 §6/§7/§8/§9 SQL 확장 (title/actor/resource_name/description + LEFT JOIN account_users)
- `app/routers/reports.py`: `preview_report`에서 `start_date=generation.start_date, end_date=generation.end_date` 전달

### 실측 검증 (2026-07-04)
- 컨테이너 재빌드 후 startup 로그: `[OK] Sample servers created: 14`
- `SELECT category, count(*) FROM server_categories JOIN servers` — 9카테고리 전부 최소 1대
- 신규 리포트 24 생성 → JSON preview 실측: `USER_SESSION_GRID`가 `[ID, 로그인ID(admin), 사용자명(슈퍼사용자), IP, 생성일, 만료일]` 정상, `SYSTEM_CONFIG_GRID` 56행 8컬럼(행위자/IP/리소스명/변경설명 노출), `SYSTEM_AUDIT_GRID` 41행 폴백 정상, `SYSTEM_EVENT_GRID` 6컬럼(제목/메시지), `USER_GRID` 역할 "관리자" (한국어 라벨)

### 별도 트랙 (이 사이클 미포함)
- **부수 C**: `config_change_logs.actor_id` 95% NULL (56건 중 53건) — 서비스 레이어 로깅 헬퍼가 request context에서 `current_user` 주입 누락. 별도 사이클로 다룸.
- system_events / login FAILURE 시드 확장 — 데이터 부족은 별도 시드 확장 사이클.
- 두 리포트 파이프라인 단일화 로드맵 — 이번엔 필터/라벨/컬럼 정합만 통일, 정본 승격은 다음 사이클.

## [v6.0] — 2026-07-03

> **Async 대전환** (문서 A-7 근본 해결책 2). SQLAlchemy 2.x + asyncpg + AsyncSession 도입.
> 41 라우터 × 397 db.query → `await db.execute(select())` 전환. Dual-stack 원칙(sync 병존)으로 안전 롤아웃.

### Phase 별 완료 (P0~P11)

| Phase | 목표 | 결과 |
|:-:|---|:-:|
| **P0** | Foundation | asyncpg + async_engine + AsyncSessionLocal + get_async_db 병존 |
| **P1** | Relationship Hazards | 6개 라우터 × 22 hazards 명시 쿼리 교체 (Tidy First) |
| **P2** | Middleware | v5.4 to_thread 유지 결정 (v6.1 batch queue) |
| **P3** | Services 5종 | audit/grant/session_sweep/api_logs_sweep/token_blacklist dual-stack |
| **P4** | Auth/Security | get_current_account_user_async, matrix_enforcer async, bcrypt to_thread |
| **P5** | Simple 5 라우터 | audit_logs, config_change_logs, event_mappings, tracking, logs |
| **P6** | Medium 15 라우터 | camera_presets/settings, enclosures, file_groups, grants, lamps, proxy_settings, server_categories, server_metrics, settings, user_groups + enclosure_metrics, servers, system_events, thumbnails + settings_service/config_log_service dual-stack |
| **P7** | Device Polymorphic 4 | controllers, sensors, speakers, cameras (selectinload) |
| **P8** | VeryComplex 15 | detections, detection_logs, malfunctions, connections, actions (selectin_polymorphic), event_mapping_cameras/lamps/speakers (bulk flush), device_groups (selectin_polymorphic Device), rois, xypoints, users (bcrypt async), user_sessions, reports (service sync 유지), event_statistics |
| **P9** | init/main/Scheduler | asyncio.to_thread(initialize_database, apply_triggers) 래핑. 스케줄러 3종 P3 완료 |
| **P10** | 통합 검증 | 50 GET endpoint 전건 스캔 — 500-FAIL 0, 회귀 없음 |
| **P11** | 5중 싱크 마감 | 본 커밋 (Swagger/명세서/CHANGELOG/Image/Container/태그 v6.0) |

### Added
- **asyncpg** (requirements.txt 기존 — 신규 설치 무필요)
- `app/database.py`: async_engine + AsyncSessionLocal (Dual-stack)
- `app/dependencies.py`: get_async_db
- Services async 병존: log_action_async, is_blacklisted_async, add_to_blacklist_async, run_grant_sweep(async), run_session_sweep(async), run_api_logs_sweep(async), settings_service.*_async, log_config_change_async
- Auth async 병존: get_current_account_user_async, get_current_account_user_optional_async, require_admin_async, require_role_async, require_perm_async, require_perm_optional_async, _effective_allows_async, effective_permissions_payload_async
- utils/auth: hash_password_async, verify_password_async (to_thread bcrypt)
- Polymorphic eager load: selectin_polymorphic(Device, [...]) + selectinload(Event.device).selectin_polymorphic([Sensor, Camera, Controller, Speaker, Enclosure, Lamp])

### Changed
- **41 라우터 async 전환**: db.query() → await db.execute(select())
- **매 요청 이벤트루프 자유**: sync 커넥션 획득 절감, MissingGreenlet 회피
- **Swagger `info.version` 5.4.0 → 6.0.0**

### 실측 검증

- 스타트업: container Up (healthy), 스케줄러 3종 정상, traceback 0건
- 50 GET no-param endpoint 스캔: **500-FAIL 0**, 46 success, 4 422(필수 param), 0 timeout
- 폴리모픽 Device/Event 계층: detections/malfunctions/connections/detection_logs/actions 전건 200
- device_groups/{id} → 200 (selectin_polymorphic 적용)
- bcrypt async: 60자 hash + verify match/mismatch 정상
- postgres 커넥션: active=1, idle=4 (안정)

### v6.0 후속 (같은 날 통합, 하루 1버전 원칙) — GOPDB A-7 6/6 전건 반영 완결

> P11 5중 싱크 마감 후 **A-7 부분 반영 2건**(#1 batch queue, #6 파티셔닝) + **P0 임계 경로**(Report Service 완전 async) 이월 재편입.
> 6 Phase 순차 처리, 각 phase 커밋+push 규율 준수.

| Phase | 목표 | 결과 |
|:-:|---|:-:|
| **후속 P1** | Quick Wins 5건 | Docker autoheal / legacy 제거 / pytest async fixture / Force-Logout 가이드 / Docker prune cron (8/8 PASS) |
| **후속 P2** | Init 모듈 4개 완전 async | init_db/init_server_data/init_report_data/init_sample_data dual-stack (+1517 lines, _bulk_insert_async 500-row chunks) |
| **후속 P3** | Report Service 완전 async ⭐ Critical | ReportServiceAsync (+800 lines, 20 async 메서드) / build_master_data_async (+231 lines) / render_report_html_async (to_thread) / reports.py SessionLocal 3곳 완전 제거 |
| **후속 P4** | A-7 #1 + #6 완결 | APILoggingMiddleware asyncio.Queue batch consumer (100건/500ms) + api_logs PostgreSQL 파티셔닝 (월별 + before-partition catch-all) |
| **후속 P5** | RBAC 매트릭스 확대 | permission_map.py +72 lines, +62 endpoint (events/devices/servers/integrations/files/cameras) |
| **후속 P6** | 최종 통합 검증 + 태그 재정렬 | 50 GET endpoint 스캔 500-FAIL 0, 5중 싱크 완결, 태그 v6.0 최종 커밋 재정렬 |

**tz-aware/naive datetime 회귀 2건 (Phase 3, 4) 즉시 hotfix**:
- Phase 3: `_run_report_generation` + `report_preview_page` 진입 시 `.replace(tzinfo=None)`
- Phase 4: middleware log payload timestamp `.replace(tzinfo=None)`
- 원인: asyncpg 엄격 검사 vs psycopg2 auto-coerce 차이

**5중 싱크 최종 상태**:
- 코드: async 대전환 + init + report_service + middleware batch + partition 모두 반영
- Swagger: `info.version = 6.0.0`
- Docker Image: 재빌드 완료 (autoheal 컨테이너 포함)
- Container: `Up (healthy)`
- CHANGELOG: 본 섹션

**후속 실측**:
- Startup 로그 3종 스케줄러 + "API log batch consumer started" 정상
- api_logs partition 6 tables (parent + 4 monthly + before-partition)
- Batch flush 실측: 12 요청 → api_logs +16 rows (3초 내)
- 파일 이관: 2892 rows → api_logs_2026_07 파티션 라우팅 확인
- traceback 0건 (2건 hotfix 후)

### Deferred → v6.1

- ~~report_service.py + report_master_builder.py + report_html_renderer.py 완전 async~~ **→ v6.0 후속 P3 완결**
- init_*.py 5개 내부 완전 async (to_thread 래퍼 대신)
- APILoggingMiddleware batch INSERT queue
- pytest 스위트 async fixture 복구
- token_blacklist TTL 캐시 → Redis 분산 캐시

### Migration Guide

- 신규 라우터 작성 시 `Depends(get_async_db)` + `AsyncSession`
- Auth: `require_perm_optional_async("module", "verb")` 사용
- Bcrypt: `await hash_password_async(...)` / `await verify_password_async(...)`
- Audit: `await log_action_async(db, ...)` (async 라우터에서만)
- Polymorphic 관계 응답: `selectin_polymorphic` 필수
- DeviceGroupMapping.group 접근: `selectinload(DeviceGroupMapping.group)` 필수

## [v5.4] — 2026-07-03

> **하루 1버전 원칙**에 따라 오늘(2026-07-03) 진행된 모든 작업 통합:
> ① 클라 GET /api/grants 신설, ② Workflow 393 시나리오 검증 결과 P0 6건 hotfix, ③ 클라 결함 지적 5건(PII/RBAC/DELETE/작성자/severity) 대응, ④ **AUTH_MODE public → token 전환** (User/Admin 2계층 인가 강화 발효).

**REQ**: `docs/REQ_Server_Grants_ListAll.md` (클라 요청서)

### Added

- **GET /api/grants** (`app/routers/grants.py`, ADMIN 전용) — 전체 부여 목록. 쿼리 6종(page/size/user_id/group_id/status/active_only), `{success, data, total}` 엔벨로프.
- **GrantResponse 보강**: user_login_id + user_name (group_name과 대칭)
- **DELETE /api/reports/generations/{id}** (`app/routers/reports.py`) — 생성 이력 삭제 + best-effort PDF 파일 삭제 (클라 REQ #3)
- **GET /api/reports/preview/{id}** — 이관 신설(라우터 하위). 인증 강제. (P0-1, 클라 REQ #1)
- **reports 매트릭스 등록** (`app/security/permission_map.py`) — reports view/edit/delete verb RBAC 서버 집행 (클라 REQ #2)
- **Swagger** 5.3.5 → **5.4.0**

### Changed / Security

- **P0-1** `/reports/preview/{id}` 무인증 PII 창구 봉합 (main.py 삭제 → /api/reports/preview 이관, logging 제외 해제) — LIVE 은닉 취약점 해결
- **P0-2** `AccountUserCreate/Update.role`: `str` → `EnumUserRole` — v5.3 Phase 2 회귀 봉합(OPERATOR 등 삭제 role 422 차단, DB 오염 재발 차단)
- **P0-3** `DetectionEventCreate.type_event`: `str` → `EnumEventType` — 'Bogus' 등 임의값 422 차단
- **P0-4** Event Update 3종(`DetectionEventUpdate`/`MalfunctionEventUpdate`/`ConnectionEventUpdate`) `model_config = ConfigDict(extra='forbid')` — PATCH 표면 방어(v4.8 Phase 12 docstring 의도 → 코드화)
- **P0-5** `POST /api/reports/generate` template_id FK 위반 raw 500 → 404 명시 매핑
- **P0-6** `Server.port` `Field(ge=1, le=65535)` — 포트 범위 검증
- **P1-2** `POST /api/reports/generate` — generator_id/name/department 스냅샷 기록(작성자 감사 이력, 클라 REQ #4)
- **P1-3** `severity_filter` — `build_master_data`에 실적용(system_events 4개 쿼리에 severity IN 조건 화이트리스트 검증, 클라 REQ #5)
- **P2-1** `.env` **`AUTH_MODE=token`** (public→token) — Bearer 토큰 필수화, matrix_enforcer 활성

### Removed

- **`@app.get('/reports/preview/{id}')`** (main.py:685) — 무인증 PII 창구 완전 삭제. `include_in_schema=False` + 로그 제외 3중 은폐 해체.
- **middleware/logging.py** `/reports/preview` 로그 제외 해제

### Verified (실측)

- 무인증 `/api/users` → **401**, `/api/reports/preview/7` → **401**, 이전 `/reports/preview/7` → **404** (엔드포인트 삭제)
- admin 토큰 `/api/users` → 200, `/api/reports/preview/7` → 200, `/api/reports/generations` → 200
- `role=OPERATOR` 계정 생성 → **422**, `role=USER` → 201
- `type_event=Bogus` detection 생성 → **422**
- `POST /reports/generate template_id=99999` → **404** (500 아님)
- `POST /servers port=70000` → **422**
- `PATCH detections/{id} device_id=99999` → **422** (extra forbid)
- `PATCH detections/{id} type_event=Bogus` → **422** (enum)
- `DELETE reports/generations/99999` → **404** (엔드포인트 매핑 확인)

### Migration

- `.env`: AUTH_MODE=public → token
- schema 변경 없음 (`generator_id`/`generator_name`/`generator_department`는 기존 컬럼 활용)

### Notify (클라 후속)

- LoadAllGrantsAsync 계정 순회 → 단일 GET /api/grants 호출로 교체
- UserLabel 태깅 로직 제거 (user_login_id/user_name 필드 대체)
- .NET 3종(GIS/Ironwall/RtspViewer) — Bearer 토큰 부착 확인 필수 (AUTH_MODE=token 전환됨)
- 클라 결함 지적 5건 서버 대응 완료 → 클라 UI 주석/우회 로직 제거 가능

### Deferred (v5.5+)

- 108 endpoint × 인가 매트릭스 전면 매핑 (현 v5.4는 reports + 기존 30개 + 확장)
- audit append-only DB RULE/RLS
- require_perm 세분화 (control 등)

### v5.4 후속 — 클라 지적 계정 항목 4건 (같은 날, 하루 1버전 통합)

**클라 지적**: v5.4 태그 직후 클라팀이 계정 항목 미완 4건 지적 → 즉시 후속 반영.

- **P0-B** `PUT /api/users/{id}` group_id=null 해제 지원 — `is not None` 체크 제거, `model_fields_set` 기반 필드 판정.
  요청 body에 `{"group_id": null}` 명시 시 group_id 실제로 null로 갱신됨(구성원 해제).
- **P1-A** UserSession sweep 스케줄러 신설 — `app/services/session_sweep_service.py`. 5분 간격으로 `expires_at < now AND is_active=true` 세션에 `is_active=false + logout_reason=EXPIRED` 마킹. `app/main.py` startup에 `session_sweep` job 등록.
- **P1-B** SUPERSEDED 핸들러 — `POST /api/auth/login`에서 동일 계정 활성 세션들 자동 evict:
  1. `is_active=false + logout_reason=DUPLICATE + logged_out_at`
  2. 각 세션 access token jti → `token_blacklist` 등재 (reason=DUPLICATE)
  3. `publish_session_revoke()` NATS 발행 (best-effort, 게이트 off 시 무동작)
  결과: 이전 로그인의 토큰 즉시 401 (블랙리스트 hit).
- **P0-A** `GET /api/audit-logs?action_status=…` 500 재확인 — v5.4 AUTH_MODE=token 전환 후 200 정상 응답(실측 SUCCESS/FAILURE 필터 모두 통과). 클라 콘솔 500은 AUTH_MODE 이전 상태에서 발생한 것으로 판단.

**실측 검증 (SUPERSEDED)**:
```
로그인1 → TOKEN_A → /api/users = 200
로그인2 → TOKEN_B → /api/users = 200 (fresh)
                → TOKEN_A → /api/users = 401 (blacklist hit)
DB user_sessions: 이전 활성 세션 is_active=f logout_reason=DUPLICATE
```

**실측 검증 (group_id=null 해제)**:
```
BEFORE  probe user group_id=1
PUT {"group_id": null} → 200
AFTER   probe user group_id=NULL (해제 확인)
```

### v5.4 후속 (2) — 클라 REQ Reports verb-RBAC 서버 집행 (2026-07-03)

**요청서**: `docs/REQUEST_Reports_Verb_RBAC_Enforcement.md` (Dotnet.Monitoring.Solution 세션).

**배경**: v5.4 P2-2에서 `PERMISSION_MAP`에 reports 10경로를 등록했으나 중앙 `enforce_matrix`가 실제 게이팅을 못함(`perm=None` default-allow). 무권한 USER가 보고서 생성/삭제/PII 조회 가능한 상태였음.

**조치 — 요청서 §4.2 A안 채택**: `controllers.py`의 검증된 패턴(`require_perm_optional`) 재사용.
- `app/routers/reports.py` 9개 endpoint에 `dependencies=[Depends(require_perm_optional("reports", verb))]` 부착:
  - **edit (3)**: `POST /templates`, `PATCH /templates/{id}`, `POST /generate`
  - **delete (2)**: `DELETE /templates/{id}`, `DELETE /generations/{id}`
  - **view (4)**: `GET /preview/{id}`, `GET /generations/{id}/download`, `GET /generations/{id}/preview`, `GET /generations/{id}/preview-page`
  (요청서 §4.2의 PUT /templates/{id}는 코드에 존재하지 않아 제외 → 총 9개)
- ADMIN bypass · jti 블랙리스트 · 403 응답 모두 `require_perm_optional` 헬퍼가 담당.

**실측 검증 (요청서 §6 완료 기준)** — 무권한 USER(`group_id=null`) 토큰:
```
POST   /reports/generate           → 403 ✅
GET    /reports/preview/{id}       → 403 ✅
DELETE /reports/templates/{id}     → 403 ✅
DELETE /reports/generations/{id}   → 403 ✅
GET    /reports/generations/{id}/download → 403 ✅
[대조] ADMIN 토큰 POST /generate     → 202 (bypass 확인)
[대조] ADMIN 토큰 GET /preview/9999 → 404 (핸들러 도달)
```

**§4.3 선택·권장 추가 반영 (6개 view)** — 클라 UI 게이팅과 일관성 완결:
- `GET /components`, `GET /status`, `GET /templates`, `GET /templates/{id}`, `GET /generations`, `GET /generations/{id}` → `reports:view`

실측:
```
무권한 USER → GET /components/status/templates/generations 6개 전건 → 403 ✅
ADMIN       → GET /components → 200 (bypass)
```

**reports 라우터 총 15개 endpoint 최종 매트릭스**: edit 3 + delete 2 + view 10.

## [v5.3] — 2026-07-02

> GIS 팀 요청 대응 — Legacy User 모델 완전 삭제 + AccountUser 통일. v5.1 FR-SV-08 잔존 소진. 14/14 PASS.

**PRD**: `docs/prds/PRD_Legacy_User_Removal.md`  
**Plan**: `docs/plans/Legacy_User_Removal-prd-plan.md`  
**안전점**: `pre-legacy-user-removal`

### Removed

- **Legacy `User` 클래스** (`app/models/user.py:221~`)
- **Legacy auth 함수 3건** (`app/routers/auth.py`) — `get_current_user` / `get_current_user_optional` / `login_oauth2`
- **Legacy schema 2건** (`app/schemas/user.py`) — `UserCreate` / `UserResponse` (Token은 신규 login 사용 유지)
- **`create_admin_user()` Legacy 함수** (`app/utils/init_db.py`)
- **`POST /api/auth/login/oauth2` endpoint** (Swagger에서 사라짐)
- **DB `users` 테이블** — `DROP TABLE users CASCADE` (v56 마이그레이션)

### Changed

- **30 라우터 auth helper 이주** — `get_current_user_optional` → `get_current_account_user_optional` (AUTH_MODE=public에서 응답 무영향)
- **Swagger `info.version`** 5.2.0 → **5.3.0** + API Version 5.3
- `tests/conftest.py` — User import 정리

### Migration

- **`app/migrations/v56_drop_users_table.sql`** — FK 참조 0 검증 + DROP TABLE + 완료 검증
- **`app/migrations/v56_drop_users_table_reverse.sql`** — 롤백용 (구조만 재생성)

### Verified (14/14 PASS)

admin login + /me + tracking(2) + users + user-groups + audit-logs + reports + servers + user-sessions + cameras + actions + detections + controllers + sensors 모두 200. Swagger UserResponse/UserCreate/oauth2 endpoint 제거 확정. FK 파괴 0.

### Phase 2 — Role 축소 (5→2) + 등급 그룹 → Preset Group 정리

> 하루 1차수 묶음 원칙 준수 (2026-07-02 동일 일자 작업 통합). Phase 1(Legacy User Removal) 마감 후 차장님 지시 대응.

#### Changed (Phase 2)

- **`EnumUserRole` 축소** (`app/utils/enums.py`) — 5종 → 2종 (ADMIN/USER)
- **`user_groups` 정리** (마이그레이션 v57):
  - id=11 MAINTAINER → "Preset - 유지보수자"
  - id=12 OPERATOR → "Preset - 운영자"
  - id=13 VIEWER → "Preset - 조회자"
  - id=10 ADMIN 그룹 삭제 (bypass라 매트릭스 무의미)
  - id=14 GUEST 그룹 삭제 (배정 사용자 0명)
- **`account_users.role`** — 7건 UPDATE (admin 외 → USER)
- **admin.group_id = NULL** — ADMIN bypass
- **Swagger `info.version`** 5.3.0 → **5.3.5** (Phase 2 반영)

#### Migration (Phase 2)

- `app/migrations/v57_role_simplification.sql`
- `app/migrations/v57_role_simplification_reverse.sql`

#### Verified (Phase 2, 6/6 PASS)

- admin login 200 + role=ADMIN + group_id=None
- gop_maint/gop_op/op_tester/gop_viewer/monitor2 각 login 200 + role=USER + 매트릭스 유지
- Swagger `EnumUserRole.enum` = `["ADMIN", "USER"]` 확정
- 14 endpoint 응답 코드 유지

#### 관련 산출물 (Phase 2)

- **PRD**: `docs/prds/PRD_Role_Simplification.md`
- **Plan**: `docs/plans/Role_Simplification-prd-plan.md`
- **NOTIFY**: `docs/GOP_Server_API_v5.3_Phase2_Role_Simplification_NOTIFY.md`
- **안전점**: `pre-role-simplification`

### Deferred (v5.5+)

- AUTH_MODE 전환 (public → token) — .NET 클라 Bearer 동시 배포 필수
- require_perm 활성화 (27 라우터 부착)
- audit append-only DB RULE/RLS
- .NET 클라 팀 통지 문서

## [v5.2] — 2026-06-30

> 차장님 보고 "API 서버가 가끔 죽는데 원인 모름" → Workflow 7 agent 정밀 감사(498K token / 6.5분) 완료. Health 58/100, TOP 5 사망 원인 + 호스트 절전 가설 확정(Windows Event ID 41/6008, 5~9일 간격 비정상 종료). 5건 hot-fix 즉시 적용 + 실측 5/5 PASS. 본 세션 v5.1 자가 버그(force_logout kwarg 오타 → TypeError 500) 동시 fix. bcrypt async / APScheduler 청소 / db_monitor autoheal 등은 v5.3+ 권고.

**PRD**: `docs/PRD_v5.2_Stability_Hotfix.md`
**안전점**: `pre-stability-hotfix` @ `6eced61`

### Added (강제 로그아웃 전파 서버측 — Force_Logout PRD Phases 0-4)

> .NET 클라 세션에서 이관된 `docs/prds/PRD_GOP_Server_Force_Logout.md` (FR-SVF-01~12). 클라가 강제 로그아웃을 실시간 수신·매칭하기 위한 서버 선결: 불변 session_id, 토큰 패밀리 무효화, 서명된 per-session NATS revoke. 클라↔서버 계약 4건 PM 확정(2026-06-30).

- **Phase 0a (FR-SVF-03)** — `POST /auth/logout` 이 access jti 만이 아니라 **paired refresh jti 도 블랙리스트** 등록. 셀프 로그아웃 후 저장된 refresh_token 으로 `/refresh` 세션 부활하던 구멍 차단. `app/routers/auth.py`.
- **Phase 0b (FR-SVF-09)** — `force_logout` 단건/벌크 양 경로에 **마지막 활성 ADMIN 세션 가드**(409, FOR UPDATE TOCTOU 안전). 벌크 응답 `data.count` 계약 복원. `app/routers/user_sessions.py`.
- **Phase 1 (FR-SVF-01/02)** — access+refresh JWT 에 **`sid` 클레임(= UserSession.id)** + login/refresh 응답 `session_id`. 로그인 핸들러 재정렬(session flush→sid 박은 토큰 발급), refresh 는 sid 승계(불변)·jti 회전·UserSession 토큰 재바인딩(orphan 방지). `app/routers/auth.py`, `app/utils/auth.py`, `app/schemas/user.py`.
- **Phase 2 (FR-SVF-06/07/12)** — `RevokePayload` 스키마(reason=`EnumLogoutReason` 재사용) + canonical(sorted·compact·UTF-8·null 명시) HMAC-SHA256 서명 유틸 + 전용 `REVOKE_SIGNING_KEY`(JWT_SECRET 분리 검증)·freshness 설정. `app/schemas/revoke.py`, `app/utils/revoke_signing.py`, `app/config.py`.
- **Phase 3 (FR-SVF-05/08/11)** — per-session 전용 subject `sensorway.{unit}.account.{user_id}.session.{session_id}.revoke`(광역 `all.>` 금지) best-effort publisher, force_logout 단건/벌크 연결. **`NATS_REVOKE_ENABLED=False` 게이트** — subject 클라 확정(V-SVF-05) + 발행 ACL(FR-SVF-08) 후 활성화. `app/services/nats_revoke_publisher.py`.
- **Phase 5 (FR-SVF-10)** — 폐기 세션 → 401 **안정 `error.code=SESSION_REVOKED`**(+`details.reason`) 통일. 전역 핸들러가 detection 지점의 sub-code 우선 렌더, 클라는 메시지 문자열 아닌 코드로 분기. 일반 무효 토큰은 `UNAUTHORIZED` 유지(구분). `RevokedTokenError`(`app/exceptions.py`), `app/main.py`, `app/routers/auth.py`, `token_blacklist_service.get_blacklist_reason`.

**잔여**: FR-SVF-08 NATS 발행 ACL(인프라, repo 밖).
**검증**: P1 로컬 테스트 27건 PASS(Phases 0-5) + 회귀 0(stash baseline 교차검증). ※ `tests/` 는 `.gitignore` 대상(로컬 검증 전용).

### Added (세션 설정 런타임 관리 — Session_Settings PRD FR-SVS-01~06)

> 운영 중 세션/인증 정책(세션만료·refresh만료·잠금임계·세션사용여부)을 서버 재시작 없이 조회·변경하는 ADMIN API. `docs/prds/PRD_GOP_Server_Session_Settings.md`. AUTH_MODE/JWT_SECRET 은 편집 제외(배포/.env 전용, UI 변경 시 전원 잠금/토큰 전체 무효 사고 방지).

- **FR-SVS-01/02** — `app_settings` key-value 저장소(ORM + `v55_app_settings.sql`) + `settings_service`(메모리 캐시 + .env 기본값 시드 + get/put 캐시 무효화, 단일 인스턴스 가정). 시드 후 DB 권위. `app/models/app_settings.py`, `app/services/settings_service.py`.
- **FR-SVS-03/04** — `GET/PUT /api/settings/session`(require_admin). GET 은 편집가능 + 읽기전용(auth_mode/jwt_algorithm) 반환, **jwt_secret 절대 미노출**(NFR-SVS-03). PUT 은 편집 부분집합만 수용, 경계 위반 422(session_timeout 1~168 / refresh 1~90 / lockout 0 또는 3~20 / session_enabled bool), `app_settings` UPSERT + **ConfigChangeLog 감사**(resource_type=SETTINGS, resource_id=0 sentinel) + 캐시 무효화. `app/routers/settings.py`, `app/schemas/settings.py`.
- **FR-SVS-05/06** — `auth.py` 리팩터: 토큰 만료(access/refresh)·로그인 잠금 임계를 startup 상수/하드코딩(`>= 5`)이 아닌 `settings_service` 에서 읽음(threshold=0 이면 잠금 비활성). 변경이 재시작 없이 다음 토큰 발급/잠금 판정부터 반영(NFR-SVS-05). 기본 시드값 = .env 동일이라 미설정 시 기존 동작 유지.
- **NFR-SVS-02** — `EnumConfigResourceType.SETTINGS` 추가(비-행 바운드 설정 감사용).

**검증**: P2 로컬 테스트 11건 PASS(FR-SVS-01~06 + 런타임 적용/잠금 비활성). `tests/` 는 `.gitignore`.

### Added (권한그룹 시간기반 스케쥴링 — PRD_Permission_Group_Scheduling FR-01~07)

> 권한그룹을 사용자에게 **기간(valid_from~valid_until)을 정해 부여**하고 만료 시 자동 무효화. 외부 수리기사 한시 권한(예: 오늘13:00~내일14:00) / 부서 상시 권한(valid_until NULL). 휴면(public)이라 행동 무변, AUTH_MODE=token 플립 시 RBAC과 함께 활성. 차장님 시나리오 결재(2026-06-30, 옵션B 부여 테이블).

- **FR-01** — `UserGroupGrant` 모델(user_id/group_id CASCADE, valid_from/until, is_active, granted_by, revoked_at) + `v56_user_group_grants.sql`(멱등, 인덱스 2종). `app/models/user.py`.
- **FR-02** — `auth.py` `_active_grants`/`_effective_allows`: 유효권한 = 등급 매트릭스 ∪ 현재 유효 grant. **요청시점 `valid_until>now` 계산이 권위**(is_active/sweep 비의존 — 만료 grant 즉시 차단, NFR-01). require_perm/optional 배선.
- **FR-03/05** — 부여 관리 API `app/routers/grants.py`(prefix `/api`): `POST/GET /users/{id}/grants`·`DELETE /grants/{id}`(ADMIN, soft 회수) + 파생 status(ACTIVE/PENDING/EXPIRED/REVOKED, `grant_service.py`) + 감사 `GRANT_CREATED/REVOKED/EXPIRED`.
- **FR-04** — 경량 sweep 스케줄러(`main.py` lifespan APScheduler 10분, 방어적 — 미설치/실패가 기동 안 막음). 만료 grant `is_active=false`. `requirements.txt` APScheduler.
- **FR-06/07** — `GET /api/auth/me/permissions`({modules, device_groups, valid_until, server_time}) + 로그인 응답 permissions 를 grant 병합 + valid_until 동봉. 클라(Dotnet.Monitoring) 재평가·시계보정. 클라 가이드 `docs/prds/GUIDE_Grant_Scheduling_Client_v5.2.md`.
- **R1** — grant 생성/회수/만료 시 NATS `permissions_changed` 통지(`publish_permissions_changed`, best-effort, `NATS_REVOKE_ENABLED` 게이트 off 기본).

**검증**: 로컬 스케쥴링 스위트 31 PASS + 회귀 0. 라이브 컨테이너에 `user_group_grants` 테이블 적용 확인.

### Added (매트릭스 중앙 집행 + 권한모델 단순화 — R9 / ADR_Permission_Model_v5.2)

> 차장님 결정 "권한 매트릭스=미들웨어"(R9) + "권한모델 단순화"(R10, 리스크 최소안). 휴면(public)이라 행동 무변.

- **R9 매트릭스 중앙 집행** — `app/security/permission_map.py`(경로→module:verb 중앙맵, 기존 27 데코레이터 1:1) + `matrix_enforcer.py`(전역 단일 choke point, `main.py` `FastAPI(dependencies=[...])`). 휴면/ADMIN bypass/grant 합집합. 신규 write 라우트 보호를 한 곳에 등록 → 데코레이터 누락 사고 구조적 차단.
- **R10①②③ 권한원천 변경** — `_resolve_role_group` 의 `name==role` 자동해석 **폐기** → 권한 = **배정 그룹(group_id) + grant**. role 은 ADMIN만 특권(라벨화), `require_admin` 25곳·ADMIN bypass·마지막ADMIN 가드 불변. 시드: admin 사용자를 ADMIN 그룹에 배정(`init_db.py`). 임시 등급상승·프리셋 rename 붕괴 위험 제거.
- **R4** — 죽은 중복 `PermissionsSchema`(구 List[str] modules) 제거, v4.9 강타입 Dict 가 지배. `app/schemas/user.py`.

### Security (v5.1 자가 버그 fix)

- **Fix-2 (v5.1 본 세션 자가 버그)** — `force_logout_all_user_sessions` kwarg `expires_in` (실제 시그니처는 `expires_at`) → 벌크 force_logout 호출 시 `TypeError: unexpected keyword argument 'expires_in'` 500 회귀. `app/routers/user_sessions.py:131,146` 두 호출부 + 단건 force_logout `980abbc` 패턴 동일하게 `expires_at` 교체. settings TTL(`access_token_expire_minutes` / `refresh_token_expire_days`) 기반 `datetime.utcnow() + timedelta(...)` 계산값 전달. 실측 200 OK + `token_blacklist` `FORCE_LOGOUT_BULK` 행 등록 확인.

### Fixed (안정성 4건)

- **Fix-1 — 호스트 C: 99% 디스크 회수**: Docker images 99GB + build cache 45GB 누적 → `docker builder prune -af` + `docker image prune -af` 로 **45.63GB + 444MB 회수**. C: 점유율 99% → 98.1%. `docker system df` Build Cache `0B` (이전 45.63GB) 확정. (호스트 절전 외 2차 OOM/디스크풀 사망 인자 제거)
- **Fix-3 — PostgreSQL runaway tx 차단**: `gop` DB의 `statement_timeout=0` / `idle_in_transaction_session_timeout=0` (무제한) 정책 → 단일 쿼리/idle 트랜잭션이 connection pool 영구 점유 가능. `ALTER DATABASE gop SET statement_timeout='60s'` + `idle_in_transaction_session_timeout='5min'` 적용. `SHOW` 검증 60s / 300s 확정.
- **Fix-4 — docker-compose 로그 회전 표준화**: 모든 서비스 무제한 json-file 로그 → 디스크 소진 인자. `docker-compose.yml` 상단 YAML anchor `x-default-logging: &default-logging` 정의(driver `json-file`, `max-size: 10m`, `max-file: 3`) + 모든 서비스 `logging: *default-logging` 참조. `docker inspect` `LogConfig {max-file:3, max-size:10m}` 검증.
- **Fix-5 — healthcheck 경량화**: 기존 healthcheck `/docs`(3.6KB HTML 응답, 인증 의존) → 매 30초 호출이 응답 크기·인증 미들웨어 비용 누적. `/api/tracking/health`(약 30B JSON, 무인증) 로 교체. `docker inspect` `Healthcheck.Test = curl /api/tracking/health` 확정.

### Verified (5/5 PASS)

- Fix-1: `docker system df` Build Cache `0B` (45.63GB → 0), C: 98.1%.
- Fix-2: 벌크 force_logout 200 OK + `token_blacklist` `FORCE_LOGOUT_BULK` 등록.
- Fix-3: `SHOW statement_timeout` → `60s`, `SHOW idle_in_transaction_session_timeout` → `300s`.
- Fix-4: `docker inspect` `LogConfig` = `{max-file: 3, max-size: 10m}` 전 서비스.
- Fix-5: `docker inspect` `Healthcheck.Test` = `curl -f /api/tracking/health`.

### Diagnostics (Health Score 58/100)

- A. container-events 55/100 (7 findings / 3 likely-death)
- B. memory-leak 62/100 (8/2)
- C. db-connection 72/100 (7/1)
- D. async-patterns 42/100 (8/3) — bcrypt sync in async login 동시 30건 4170ms 270배 폭증 + CPU 95% pin
- E. startup-deps 62/100 (5/2)
- F. endpoint-stress 55/100 (7/2)
- **호스트 절전 가설 확정** — Windows Event ID 41 (Kernel-Power) + 6008 (Unexpected Shutdown), 2026-06-29 09:30 / 06-24 08:38 / 06-20 09:55 → 5~9일 간격. 형제 4 컨테이너 09:32 KST 일제 재기동 = Docker daemon 단위 재시작 패턴.

### Deferred (v5.3+, 별도 PR 권고)

- bcrypt async 전환 (`asyncio.to_thread`) — `auth.py:303`/`609` login + login_oauth2 + `users.py:184` password change 3곳 (TOP 1 사망 원인)
- APScheduler + cachetools 도입 — `token_blacklist` / `api_logs` / `user_sessions` / `track_points` 자동 청소 cron
- 트랜잭션 안전망 표준화 — `get_db` rollback 패턴 일괄 적용
- `APILoggingMiddleware` 비동기 큐 분리 — 매 요청 DB 세션 신규 생성 → pool 2배 소모 해소
- `db_monitor` 재시도 + autoheal 컨테이너 (`willfarrell/autoheal`)
- `uptime_watch.ps1` 매분 `docker inspect` 스냅샷
- 차장님 PC 절전 비활성화 (제어판 → 전원옵션)
- `events` / `api_logs` / `audit_logs` 보존 정책 (90일/180일/영구) PRD 결재

## [v5.1] — 2026-06-29

> 외부 세션 시뮬레이션 `wf_52155656`(22 agent / 218 시나리오 / 99 발견) 결과 PRD 도입 → 서버 RBAC 집행률 0% 확진. P0 5건 + P1 일부(SV-06/09) 즉시 적용. AUTH_MODE=token 전환 + 비계정 라우터 require_perm 일괄 부착은 v5.2 권고.

**PRD**: `docs/PRD_GOP_Server_RBAC_Enforcement.md`
**안전점**: `pre-rbac-enforcement` @ `a699a6f`

### Added (RBAC 인프라)

- **FR-SV-05** — `EnumPermissionModule` 8→12종 확장 (`map`/`broadcast`/`setup_system`/`setup_feature` 추가, `cameras` 표기 통일).
- **FR-SV-04** — `require_perm(module, verb)` 팩토리 신설 (`app/routers/auth.py`). ADMIN bypass + 역할명 등급 그룹 매트릭스 + jti 블랙리스트 검사.
- **FR-SV-03 helper** — `get_current_account_user_optional` 신설. AccountUser 기반 + jti 검사 + AUTH_MODE 분기. **AUTH_MODE 전환 자체는 미실시** (v5.2).

### Security (RBAC Enforcement)

- **FR-SV-01 잔여** — `user_sessions.py` 4 endpoint `require_admin` 부착 + 벌크 force_logout에 access+refresh jti 블랙리스트.
- **FR-SV-02** — `reports.py` 라우터 레벨 인증 강제 (12 endpoint 무인증 PII 노출 LIVE 차단).
- **FR-SV-09** — `servers.py PATCH /{id}` + `user_groups.py GET` 2종 `require_admin`.

### Fixed (Integrity)

- **FR-SV-06** — 마지막 ADMIN 원자 가드 (`users.py` PUT + DELETE). `with_for_update().all() + len()` (PG `FOR UPDATE + count` 비호환). TOCTOU 차단.

### Verified (12/12 PASS)

- reports 무인증 401 / admin 200 / components 401
- user_sessions admin 200 / OPERATOR 403 (GET + DELETE×2)
- user_groups OPERATOR GET 403 (목록 + 상세)
- servers OPERATOR PATCH 403
- 마지막 ADMIN DELETE/PUT role 강등 → 409
- Swagger EnumPermissionModule 12종 노출

### Deferred (v5.2+)

- FR-SV-03 ① AUTH_MODE 전환 (클라 Bearer 동시 배포)
- FR-SV-04 require_perm 비계정 라우터 적용 (cameras/sensors/actions write endpoint)
- FR-SV-07 감사 append-only DB 강제 (PostgreSQL RULE/RLS)
- FR-SV-08 도메인 jti 통일 (`get_current_user_optional` 전수 교체)
- FR-SV-10 비번 변경 세션 무효화
- FR-SV-11 RTSP URL 마스킹 + NATS ACL
- PRD §5-A V-SV-01~08 검증

## [v5.0] — 2026-06-29

> 하루 1차수 묶음 원칙 — 2026-06-29 작업(외부 세션 그룹 권한 endpoint 신설 + 9중 정합 정리 + 외부 세션 미반영 항목 마감)을 단일 차수 v5.0으로 묶음. 외부 세션이 신규 권한 관리 endpoint를 `# PRD v5.0` 주석으로 마킹 → "권한 관리(Permission Management) 도메인" 본격 분리의 새 보안 핵심으로 보아 v4.12 후속 정합 정리와 함께 v5.0으로 승격 (차장님 결재 동의). v4.12 RBAC가 *endpoint-level 인가*(ADMIN 게이트)였다면, v5.0은 *group-level 권한 정책*(modules × verb 매트릭스) 관리.

**안전점**: `pre-v5-spec-sync` / `pre-v412-sync-cleanup`

### Added (Permission Management Endpoint)

- **그룹 권한 관리 endpoint 신설 — `POST /api/user-groups/{group_id}/permissions` (ADMIN 전용)**: 외부 세션(2026-06-29 오전)이 본 차수 핵심으로 신규 도입. `dependencies=[Depends(require_admin)]`로 RBAC 강제 (v4.12 ADMIN 게이트 정책 계승). 일반 `PUT /api/user-groups/{group_id}`는 v4.8 Phase 12-7a "permissions 차단" **영구 정책** 유지 — 그룹 메타(name/description) 와 권한 정책의 변경 경로를 endpoint 단위로 분리. **PermissionsSchema strict input**(`app/schemas/user.py:46`):
  - `modules: Dict[EnumPermissionModule, ModulePermission]` — `EnumPermissionModule` 8종(`devices`/`events`/`reports`/`cameras`/`users`/`user_groups`/`audit_logs`/`servers`) × `ModulePermission` 4 verb `StrictBool`(`view`/`edit`/`delete`/`control`) 매트릭스.
  - `extra='forbid'` — 미정의 모듈/verb 422.
  - `device_groups: Optional[List[int]]` — 접근 가능한 디바이스 그룹 ID 목록.
- **JSONB 컬럼 호환 직렬화**: `permissions = schema.model_dump(mode='json', exclude_none=True)` → `account_user_groups.permissions` (JSONB) 에 안전 영속.
- **감사 로그 자동**: `log_action(action_type="PERMISSION_CHANGED", resource_type="USER_GROUP", actor_*, resource_id, resource_name, changes={before, after}, description=f"그룹 권한 변경: {group.name}")` — 변경 전/후 스냅샷 자동 캡처.
- **Error 매트릭스**: 403 (RBAC, 일반 사용자) / 404 (그룹 없음) / 422 (스키마 위반).
- **Swagger 노출**: `operationId=update_user_group_permissions`, `requestBody`에 `PermissionsSchema` `$ref=#/components/schemas/PermissionsSchema` 노출.
- **실측 검증**: 감사 로그 `PERMISSION_CHANGED` 1건 (`2026-06-29 10:23:29`) + Swagger `$ref` 노출 + ADMIN 외 사용자 403 확인.
- (`app/routers/user_groups.py:270`, `app/schemas/user.py:46`, 코드 주석 `# PRD v5.0` 마킹)

### Security (외부 세션 9중 정합 정리, Critical 7건 해소)

- **PII data/profiles/ 차단 (P0)**: v4.11 프로필 사진 업로드 도입 후 호스트 바인드 마운트 `./data/profiles/` 가 `.gitignore` 미등재 → 사용자 사진 3건이 git untracked로 commit 가능 노출. `.gitignore`에 `data/profiles/` 추가 + git rm --cached로 추적 해제 + 사용자 사진 commit 차단 확정.
- **사고 파일 정리**: 비정상 경로명 파일 `'c\357\200\272workspace_pythonapi-test-serverendpoints_spec.txt'` (백슬래시 누락 사고로 root에 생성) 삭제.
- **admin 계정 복구**: admin 계정 락업 상태 확인 → unlock + bcrypt(`admin123`) 재발급 + `failed_login_count=0` 리셋 (실 운영 환경 회복).
- **token_blacklist 17 row cleanup**: 만료 토큰 17건 잔존 → 일괄 정리 (자동 청소 cron은 v5.1+ 이연).
- (v4.12 정합 정리 commits `7756ec9` / `4afaed6` 본 v5.0 섹션에서 인용 — 하루 1차수 묶음 원칙 적용)

### Fixed (외부 세션 종료 미반영 항목)

- **Swagger version (FastAPI app metadata) 회귀 정정**: `app/main.py` `version="1.6.0"` (v4.5 이전 값) → `"4.12.0"` 동기화. 외부 세션이 코드 본문은 v4.12까지 진행했으나 app metadata 갱신 미반영 → 본 세션에서 commit.
- **API Version 응답 헤더 갱신**: `2.10` → `4.12` (`/api/system/version` 표시값).
- **PRD 목록 동기화**: 명세 PRD 목록(§서두 개요)에 `PRD_v4.11_Tracking_History` + `PRD_v4.12_Followup_AccountIntegration` 2건 누락 → 추가.
- **Image rebuild + Container force-recreate**: `docker compose build --no-cache api-test-server` + `docker compose up -d --force-recreate` → `Created 2026-06-29T00:59:01` 확정. 이전 컨테이너가 v4.10 이미지 유지 상태였음.
- **session-context.md 차수 표기 갱신**: 메모리 마지막 차수 `v4.10` → `v4.12` 정정 (v4.11/v4.12 작업 본문은 본 차수 이전부터 진행).

### Spec sync (`GOP_Restful_Api_연동설계.md`)

- **헤더/푸터 갱신** (L4-7 / L16045-46): 버전 `v4.12` → `v5.0`, 최종 수정일 `2026-06-27` → `2026-06-29`.
- **변경 이력 표 신설** (L16002 직전): `v5.0 — 2026-06-29 — 그룹 권한 endpoint 신설(ADMIN 전용, PermissionsSchema strict) + 9중 정합 정리 + 외부 세션 미반영 항목 마감` 행 추가.
- **§9.4 UserGroup API endpoint 표 1행 추가** (L14340): 기존 6행(GET 목록/단일, POST 생성, PUT 수정, DELETE 삭제, GET /users)에 7번째 행 추가:
  - `POST /api/user-groups/{group_id}/permissions` — 그룹 권한 정책 변경 (ADMIN 전용, PermissionsSchema).
- **§9.4.7 본문 신설**: PermissionsSchema 매트릭스(modules 8 × verb 4) + JSONB 직렬화 + 감사 로그 자동 + Error 403/404/422 + curl 예시 + 응답 예시.
- **§13.1 부록 UserGroups 블록 동기화**: v5.0 endpoint 추가 + PermissionsSchema 스키마 정의(EnumPermissionModule/ModulePermission/extra='forbid' NOTE).
- **§13.1 부록 Users 블록**: v4.11 신설 endpoint(`POST /api/users/me/photo`, `GET /api/users/photo/{file_name}`) 동기화 누락분 보강.

### Tags

- `v4.9-final-stable` — v4.9 마지막 안정점 (Phase 0~5 통합 + 3중 정합)
- `v4.10-final-stable` — v4.10 마지막 안정점 (Phase 1 평문 회귀 + Phase 2 HTTPS mkcert)
- `v4.11-final-stable` — v4.11 마지막 안정점 (Tracking API + 프로필 사진 + audit FK 익명화)
- `v4.12-final-stable` — v4.12 마지막 안정점 (계정 RBAC ADMIN 게이트 + gis-ingest 워커)
- 안전점: `pre-v5-spec-sync`, `pre-v412-sync-cleanup`

### Memory (4건 신설 + MEMORY.md 인덱스 갱신)

- `feedback_rbac_admin_gate_policy.md` — v4.12 계정 8 endpoint ADMIN 게이트 + 권한상승(T1) 차단 정책 (서버 RBAC가 권위 집행, 클라 UI 게이팅은 보조).
- `feedback_tracking_keyset_cursor.md` — v4.11 `/api/tracking/points` cursor envelope (`next_cursor`/`limit`/`has_more`) 패턴 (Playback 기간 청크 정렬 핵심).
- `feedback_profile_photo_storage.md` — v4.11 프로필 사진 PII 정책 (파일시스템 영속, DB엔 photo_url(URL)만, `./data/profiles/` 바인드 마운트, `data/profiles/` `.gitignore` 차단 v5.0).
- `feedback_audit_append_only_fk_anonymize.md` — v51.1 `fn_block_audit_modification` 트리거 예외 (FK 익명화 UPDATE만 허용, 행 삭제·내용 변경은 계속 차단 = append-only 유지).

### Deferred (v5.1+)

- **장비/이벤트/맵 쓰기 RBAC**: AUTH_MODE token 승격 + 인증 의존성 통일 + .NET 클라 Bearer 부착 선결 (미선결 시 앱 쓰기 전면 401 위험). PRD-GOP-01 v2.0 §7 V-PG-01 후속.
- **token_blacklist 자동 청소 cron**: 만료 jti 일괄 정리 워커 (현재는 수동 정리, v5.0에서 17 row 정리 인용).
- **태그 컨벤션 재명명**: `before-account-rbac` / `before-tracking-api` / `before-*` 신규 3 태그 → `pre-*` 컨벤션으로 재명명 (안전점 표기 일관화).
- **67 untracked PRD 정리**: `docs/PRD_*.md` 67건 → `docs/archive/legacy_prd/`로 이동 (현행 활성 PRD만 root 유지).
- **명세 §11.1 워커 차수 라벨 보강**: §11.1 추적 워커 본문에 "v4.11 신규 API / v4.12 인제스트 워커 분리" 차수 라벨 명시 (현재는 v4.11 본문에 인제스트 후속 NOTE만 존재).

## [v4.12] — 2026-06-27

> 하루 1차수 묶음 원칙 — 2026-06-27 작업(계정 RBAC + 추적 인제스트 워커)을 단일 차수 v4.12로 관리.

### Added
- **추적 이력 인제스트 워커(gis-ingest) 신설**: NATS `TRACKING_STATUS`(신버전 `targets[]`)를 구독해 `track_points`에 영속하는 독립 워커. §11(v4.11)에서 "후속"으로 둔 서버측 저장 경로를 실현(읽기 API ↔ 인제스트 분리 완성). `db_monitor`(pg_notify→NATS) **역방향 미러**: NATS 구독→asyncpg INSERT. 독립 compose 서비스 `api-test-gis-ingest`(asyncpg+nats-py, `nats_external` 망, postgres healthy 의존). `sensorway.*.gis.tracking-status` 구독 → `tracking=="active"` targets[]만 `INSERT ... ON CONFLICT (track_id, observed_at) DO NOTHING`(멱등). 순수 파서 `parse_tracking_status()` 분리(8 단위테스트), `observed_at`(UTC)→naive KST 변환, 구버전 단일 `target` 방어 정규화. **mock E2E**(NATS 발행→인제스트→멱등 검증→`/points`·`/sessions` 조회) 통과 + 테스트 데이터 정리. 발행 시 `created_at` NOT-NULL(raw asyncpg는 ORM Python default 미적용) 명시 지정 버그 E2E로 발견·수정. ⚠ 실 `AiAnalysis` 신 `targets[]` 발행 합의 미결(방어 파싱으로 호환). (`gis_ingest/main.py`·`Dockerfile`·`requirements.txt`, `docker-compose.yml`, 명세서 §11.1 구현 반영, 브랜치 `feature/tracking-gis-ingest`)

### Security
- **계정 관리 RBAC — ADMIN 전용 게이트 + 권한상승(T1) 차단**: 계정 CRUD/lock/unlock/reset-password 8개 엔드포인트(`/api/users` 목록·상세·생성·수정·삭제·lock·unlock·reset-password)에 `require_admin`(=`require_role("ADMIN")`, `app/routers/auth.py` 신설) 의존성 추가. 이전엔 인증(Bearer)만 검증하고 `role`을 인가에 미사용 → **임의 인증사용자가 `PUT /api/users/{id}` 본문 `role=ADMIN`으로 자기/타인을 ADMIN 격상(권한상승 T1)** 가능했음(users.py:445-446 무가드). role 미달 시 **403**. 본인 자원(`/me`·`/me/password`·`/me/photo`) self-service 유지, `GET /api/users/photo/{file_name}` 인증불요 유지. E2E: VIEWER GET/PUT/DELETE→403, T1 격상→403, admin→200, /me→200. **서버 RBAC가 권위 집행**(클라 UI 게이팅은 보조). ⚠ 장비/이벤트/맵 쓰기 RBAC는 후속 차수(AUTH_MODE token·인증 의존성 통일·.NET 클라 Bearer 부착 선결, 미선결 시 앱 쓰기 전면 401). PRD-GOP-01 v2.0 §7(V-PG-01 서버 RBAC 실태감사) 근거. (`app/routers/auth.py`, `app/routers/users.py`, 명세서 §9.3.1, 안전점 `before-account-rbac`, 브랜치 `feature/server-account-rbac`)

## [v4.11] — 2026-06-26

> 하루 1차수 묶음 원칙 — 2026-06-26 작업(추적 이력 API + 프로필 사진 + audit 하드닝)을 단일 차수 v4.11로 통합. 명세서 §11(추적 이력 API) 신설 + 변경 이력 동기화.

### Added
- **추적 이력(Tracking) REST API 신설**: GIS 추적(`TRACKING_STATUS` 신버전 `targets[]`) 영속·조회. `track_points` 테이블(`UNIQUE(track_id, observed_at)` 멱등 + `observed_at`/`(camera_id, observed_at)` 인덱스, 마이그레이션 `app/migrations/v54_tracking_points.sql`, startup `create_all` 자동 생성). 읽기전용 GET 3종: `GET /api/tracking/points`(기간 `from`~`to` + **keyset cursor** 청크, 정렬 `observed_at ASC, id ASC` — Playback 핵심) · `GET /api/tracking/sessions`(`track_id`(+`camera_id`) 단위 `MIN/MAX(observed_at)`·`COUNT(*)` 파생 집계) · `GET /api/tracking/health`(가용성 게이팅, 무인증). 응답 envelope에 cursor 슬롯이 없어 `/points` 전용 `cursor`(`next_cursor`/`limit`/`has_more`) 래퍼 도입. 인증=`get_current_user_optional`(`/health` 제외). 저장은 별도 독립 워커 `gis-ingest`(NATS 구독→`INSERT ... ON CONFLICT DO NOTHING`) — 클라 POST 배제. (`app/models/tracking.py`, `app/schemas/tracking.py`, `app/routers/tracking.py`, `app/main.py` 등록, 명세서 §11 신설 / 기존 §11 에러처리→§12·§12 부록→§13 재번호, 안전점 `before-tracking-api`, 브랜치 `feature/tracking-history-api`)
- **프로필 사진 업로드/서빙**: `POST /api/users/me/photo`(multipart, field `file`, image/jpeg·png·webp·gif, ≤5MB) → 호스트 바인드 마운트 `./data/profiles/`에 `{user_id}_{uuid8}.{ext}` 저장 + `account_users.photo_url`을 절대 API URL로 갱신. `GET /api/users/photo/{file_name}`(FileResponse, 인증 불필요, 경로 traversal 차단). 이미지는 **파일시스템**(썸네일 패턴), DB엔 photo_url(URL)만 — `./data` 바인드 마운트라 컨테이너 재빌드/재생성에도 **영속**. 검증: 업로드 200 / 서빙 200 / bad-type 400 / 강제재생성 후 GET 200. (`app/routers/users.py`, `app/config.py` PROFILE_STORAGE_PATH, 명세서 §9.3.1)

### Fixed
- **사용자 hard-delete 불가 (append-only ↔ FK SET NULL 충돌)**: `DELETE /api/users/{id}` 시 `user_login_logs.user_id` / `audit_logs.actor_id` / `config_change_logs.actor_id` FK 가 `ON DELETE SET NULL`(UPDATE)을 시도하는데 해당 테이블이 append-only 트리거로 UPDATE 차단 → 이력 있는 사용자 삭제가 500. `fn_block_audit_modification` 을 수정해 **FK 익명화(user_id/actor_id→NULL, 그 외 컬럼 불변) UPDATE 만 허용**(내용 변경·행 삭제는 계속 차단 = append-only 유지). (`app/migrations/v51_audit_immutability_triggers.sql` v51.1, 라이브 DB CREATE OR REPLACE 적용, 안전점 `pre-audit-fk-anon-fix`)
- **audit-logs 500 (append-only 데이터 하드닝)**: `AuditLogResponse.action_type` / `resource_type` 를 strict enum → **str(tolerant)**. `audit_logs` 는 append-only(§7 Phase 12-7f, UPDATE/DELETE 차단)라 과거 비-enum 값(테스트 잔재 `TEST_INS`/`TEST`)이 영구 잔존 → 전체 목록 직렬화 시 Pydantic 500. 데이터 삭제 불가(불변 트리거 = 설계)이므로 응답 스키마 완화로 해결. 생성 측 `AuditLogCreate` 도 str 이라 정합. (`app/schemas/audit_log.py`, 명세서 §9.6.2 NOTE)

## [v4.10] — 2026-06-25

**배경**: v4.9 Phase 5 SEC-1 마스킹 정책이 적용 24시간 만에 운영 한계 노출 — 마스킹된 `"********"`를 복원하는 **복호화 경로 미정** + .NET이 NVR/Speaker/Lamp/외부 서버에 평문 자격증명 필요. 차장님 결재 (2026-06-25): *"야 그냥 평문으로 보내. 복호화방법도 없는거 같은데"* → 평문 응답 회귀.

**PRD**: `docs/PRD_v4.10_Phase1_mask_rollback.md` (6.4KB, Workflow 1 agent, Track B)

**안전점**: `pre-v4.10-phase1` @ 31bb478

### Phase 2 — HTTPS 도입 (mkcert 폐쇄망) + Inno Setup rootCA 인스톨러 (6/6 PASS)

**배경**: Phase 1 평문 응답 정책 회복 직후, 통신 구간 암호화 필요 (JWT Bearer + user_password 평문 보호). 차장님 결재 (2026-06-25): "가장 간단·신뢰·폐쇄망 호환" + "서버 1대 + 여러 클라 PC" + "EXE 1클릭 자동 등록".

**선정**: mkcert (외부 인터넷 불필요) + Inno Setup (.iss 정식 GUI 인스톨러)

**PRD**: `docs/PRD_v4.10_Phase2_HTTPS_mkcert_Inno.md` (11.2KB, Workflow 2 agent / 옵션 A/B/C 비교)

**안전점**: `pre-v4.10-phase2` @ 8089877

**Added (mkcert 인증서 발급)**:
- `mkcert v1.4.4` 다운로드 (`~/bin/mkcert.exe`)
- `mkcert -install` — Windows 신뢰 저장소 local CA 자동 등록
- `mkcert -cert-file certs/server.crt -key-file certs/server.key localhost 127.0.0.1 host.docker.internal 192.168.202.160 ...` (만료 2028-09-25)
- `certs/installer/payload/rootCA.pem` (mkcert CAROOT에서 복사)

**Added (Docker HTTPS)**:
- `Dockerfile` CMD: `sh -c "if certs/server.crt exists then uvicorn --ssl-keyfile else HTTP fallback"`
- `docker-compose.yml`: `volumes: ./certs:/app/certs:ro` + healthcheck `curl -fk https://localhost:8000/docs`
- Uvicorn `https://0.0.0.0:8000` 시작 확인

**Added (Inno Setup 인스톨러 소스 — 8 파일)**:
- `certs/installer/src/install_gop_rootca.iss` (Inno Setup 메인 스크립트, PrivilegesRequired=admin)
- `certs/installer/src/post_install.ps1` (certutil -addstore -f Root + 한국어 로그)
- `certs/installer/src/pre_uninstall.ps1` (certutil -delstore, 제어판 제거 시 자동)
- `certs/installer/src/LICENSE_KO.txt` (한국어 Welcome 페이지)
- `certs/installer/scripts/build.ps1` (ISCC.exe 자동 탐색 + 컴파일)
- `certs/installer/scripts/verify.ps1` (등록 검증)
- `certs/installer/.gitignore` + `README.md`

**Verified (6/6 PASS)**:
- Uvicorn `https://0.0.0.0:8000` 시작
- `curl -k https://localhost:8000/docs` → 200
- HTTP (http://) → 000 (차단)
- 인증서 mkcert CA 발급 확인 (notAfter 2028-09-25)
- Bearer 토큰 발급 + `/api/auth/me` HTTPS 200
- Container Up healthy

**Security (.gitignore)**:
- `certs/*.crt` / `*.key` / `*.pem` commit 차단 (절대 금지)
- `!certs/installer/` 예외 (소스는 commit)
- `certs/installer/build/*.exe` / `payload/rootCA.pem` 차단

**Deferred**:
- Inno Setup Compiler 실 빌드 (차장님 PC에서 별도, `scripts/build.ps1` 실행)
- HSTS / Secure 쿠키 / CSP 헤더 (v5.x)
- adminer(8080) / NATS(4222) HTTPS (별도 차수)
- 외부 IP / 내부 IP 환경 SAN 재발급 (필요 시 mkcert 재실행)

### Phase 1 — SEC-1 마스킹 정책 폐기 / 평문 응답 복원 (6/6 PASS)

**Reverted (v4.9 Phase 5 마스킹 제거)**:
- `app/schemas/device.py` `from app.schemas._password_mask import` 제거 + `CameraResponse._mask_user_password` + `LampResponse._mask_user_password` `@field_serializer` 블록 제거
- `app/schemas/server.py` 동일 import 제거 + `ServerResponse._mask_user_password` + `ServerNestedResponse._mask_user_password` 블록 제거
- Field 설명 4건 회귀: `"접속 비밀번호 (응답 시 마스킹 — DB 평문 유지)"` → `"접속 비밀번호"`

**Reverted (OpenAPI example)**:
- `ServerResponse` / `ServerNestedResponse` / `ServerCategorySummary` nested example: `"********"` → `"password123"`
- `LampResponse` example: `"********"` → `"lamp1234"`

**Reverted (명세)**:
- `GOP_Restful_Api_연동설계.md` §5.3.x Camera 응답 예시 (L5103): `"********"` → `"admin1234"`

**Retained (heritage 보존)**:
- `app/schemas/_password_mask.py` 파일 유지 (사용처 0, v5.x secret API 재활용 가능)
- 명세 §9.2.2 로그인 자리표시자 `<your_login_id>/<your_password>` 유지 (로그인 자격증명 도메인 다름)
- DB 평문 / Create·Update 요청 schema / 백엔드 / 시드 / `SENSITIVE_FIELDS` Audit 마스킹 모두 변경 없음

**Verified (6/6 PASS)**:
- Camera/Lamp/Server 단일 응답 평문 (`sensorway1` / `lamp123` / `testpwd123`)
- Camera POST 3중 흐름: 요청 평문(`plain_v410`) → DB 저장 평문 → 응답 평문 일치
- OpenAPI ServerResponse example `"password123"` 평문 노출
- `grep mask_password_serializer app/schemas/*.py` → 0건
- Container Up healthy / Image rebuild

**메모리 정책 재전환**:
- `feedback_password_masking_policy` (v4.9 Phase 5) → **DEPRECATED**
- `feedback_password_plaintext_policy` → **RESTORED** (현행)
- `MEMORY.md` 인덱스 갱신 (의사결정 이력 동시 노출)

**.NET 회신 보강**:
- `docs/GOP_Server_API_v4.9_Review_RESPONSE.md`에 `## POLICY UPDATE 2026-06-25 — v4.10 Phase 1 회귀` 섹션 append

**Deferred (v4.10 잔존 + v5.x)**:
- v4.10: ENV-1 / AUTH-1 / AUTH-2 (P0) + FMT-1 / ENUM-1~2 / DEV-1~2 / EVT-1 / INT-1 / SVR-1 / AUTH-3~4 (P1) + B-4/5/7/8 잔존 + DOC-1~3 (~38-50h)
- v5.x 보안 차수: secret API + 복호화 경로 + .NET 측 사용 시점 패턴 종합 재설계

---

## [v4.9] — 2026-06-24

**배경**: 2026-06-24 오전 .NET 팀에 v4.8 마감 후속 회신(31건) 작성 → 클라가 동일 일자 `docs/GOP_Server_API_FollowupRequests.md` (12 항목 P0 4 + P1 8) 제출 → Workflow 39 agent로 50 시나리오 + 시뮬레이션 2회 + PRD 작성. R1 1/45 PASS → R2 41/4 PASS. **하루 1차수 묶음 원칙 — Phase 0~4 모두 v4.9 단일 차수**.

**PRD**: `docs/PRD_v4.9_Followup_AccountIntegration.md` (20.6KB / 536 라인)

**결재 3건 (PRD 권고 적용)**:
- D1 jti 블랙리스트 저장소 = **잠정 DB** (`IBlacklistStore` 추상화로 v5.0 Redis 전환 가능)
- D2 정적 자원 인증 정책 = **익명 + noindex** (단기, v4.10에서 토큰 필수 분기)
- D3 v52/v53 시드 마이그레이션 = **운영팀 사전 승인 가정** (dry-run + alembic downgrade 검증)

**안전점**:
- `pre-followup-prd` @ 64fa905 (Phase 0 회신 직후 PRD 진입 직전)
- `pre-v4.9-phase1` @ 8b28c9c (Phase 2~4 구현 진입 직전)

### Phase 0 — .NET 31건 질의 회신 (commit 5274dbb @ 2026-06-24 오전)

- Workflow 8 agent (653K token / 14분): A 인증 5 + B 권한 7 + C 사용자 8 + D 세션 3 + E 감사 3 + F NATS 1
- 산출: `docs/GOP_Server_API_OpenQuestions_RESPONSE.md` (14.5KB / 418줄, P0 3건 사전공지 + 명세 보강 권고 11건)
- 결과: .NET 팀이 본 회신 기반으로 12항목 Followup 제출 → Phase 1 진입

### Phase 1 — 안전점 + 명세 3 위치 초기화 (commit 4544d7c)

- 명세 헤더(L4-5) + 푸터(L15861-62) + 변경 이력 v4.9 / 2026-06-24 동시 갱신
- PRD `docs/PRD_v4.9_Followup_AccountIntegration.md` 신설

### Phase 2 — Auth 정합 (B-1 + A-3 + A-4) — 6/6 PASS (commit 9068e46)

**Fixed (B-1: 글로벌 핸들러 WWW-Authenticate 헤더 보존)**:
- `app/main.py:470-489` http_exception_handler — `getattr(exc, 'headers', None)` → JSONResponse `headers=` 전달 (RFC 6750/7235)

**Fixed (A-3: refresh_token TTL settings 분리)**:
- `app/config.py:30` `JWT_REFRESH_EXPIRATION_DAYS: int = 7` 신설
- `app/utils/auth.py:85` 하드코딩 7일 → `settings.JWT_REFRESH_EXPIRATION_DAYS`

**Added (A-4: jti 블랙리스트 + refresh type 가드)**:
- `app/utils/auth.py:93` `decode_token(token, expected_type=None)` — refresh type 가드 + jti/token_type 추출
- `app/schemas/user.py:331-336` `TokenData.jti` + `TokenData.token_type` 필드
- `app/models/token_blacklist.py` 신설 — TokenBlacklist 모델
- `app/services/token_blacklist_service.py` 신설 — `is_blacklisted/add_to_blacklist/cleanup_expired` + TTLCache 60s
- `app/routers/auth.py:97-119` `get_current_account_user` — jti 블랙리스트 검증
- `app/routers/auth.py:356-372` logout — `add_to_blacklist(reason=LOGOUT)`
- `app/routers/auth.py:392-432` refresh — `expected_type='refresh'` + 옛 jti rotation 등록
- `app/migrations/v52_token_blacklist.sql` 신설

**Verified (6/6 PASS)**: WWW-Authenticate header / refresh type 가드 401 / 정상 refresh 200 / 옛 refresh rotation 차단 / 로그아웃 전후 me 200→401

### Phase 3 — RBAC Permission 모델 (A-2 전건) — 5/5 PASS (commit 9068e46)

**Added (A-2.1~A-2.5)**:
- `app/utils/enums.py` `EnumPermissionModule` (8종: devices/events/reports/cameras/users/user_groups/audit_logs/servers) + `EnumPermissionVerb` (4종: view/edit/delete/control) Static 시드
- `app/schemas/user.py:32` `ModulePermission` (`extra="forbid"` + `StrictBool` 4종)
- `app/schemas/user.py:47` `PermissionsSchema` (modules Dict + `extra="forbid"`)
- `app/schemas/user.py:62-90` `UserGroupCreate` — `permissions: Optional[PermissionsSchema]` 강타입
- `app/routers/user_groups.py:121-128` `model_dump(mode="json", exclude_none=True)` JSONB 직렬화 호환

**Fixed (A-2.4: 시드 정규화)**:
- `app/utils/init_sample_data.py:126-138` flat `"rw"/"r"` 폐기, nested dict `{view,edit,delete,control}` 적용
- `app/migrations/v53_permissions_normalization.sql` 신설 — `pg_temp.fn_normalize_permission_value` + 시드 3개 그룹 in-place 변환

**Verified (5/5 PASS)**: 미정의 모듈(super_admin) 422 / 미정의 verb(destroy) 422 / StrictBool "yes" 422 / StrictBool 1(int) 422 / 정상 nested 201

### Phase 4 — Account Photo XSS Validator (A-1.2) — 6/6 PASS (commit 9068e46)

**Added**:
- `app/schemas/user.py:212-230` `AccountUserSelfUpdate.validate_photo_url_scheme` `@field_validator`
- 차단: `javascript:`/`data:`/`vbscript:`/`file:`/`about:` 스킴 → 422
- 허용: `http://`/`https://`/`/static/profiles/` 시작만

**Verified (6/6 PASS)**: 위험 스킴 4종 모두 422 / https & /static/profiles 200

### v4.9 잔존 (오늘 추가 처리 가능)

- A-1.3 + A-1.4: POST /me/photo multipart + 업로드 가드 7종 (~5h)
- A-3: ROLE_CHANGED/GROUP_ASSIGNED 트리거 분리 (1h)
- B-2: NATS SESSION_FORCED_LOGOUT push (4h)
- B-3: require_admin 의존성 + lock/unlock/delete/reset-password 적용 (5h)
- B-4~B-8: 5건 (~6.5h)

### Deferred (v4.10 cross-item)

- thumbnails.py 업로드 가드 / 정적 자원 인증 정책 / AuditChange.rejected 메타

### Phase 5 — SEC-1 user_password 응답 마스킹 (.NET v4.9 Review 회신, P0 보안)

**배경**: `docs/GOP_Server_API_v4.9_Review_Issues.md` SEC-1 (P0 보안) — Camera/Lamp/Server 응답에 user_password 평문 노출 지적.

**차장님 결재 (2026-06-24)**: "계정 비번 다 보호, 삭제가 아니라 마스킹"

**PRD**: `docs/PRD_v4.10_SEC1_password_masking.md` (16.5KB, Track C 4 agent Workflow)

**Added**:
- `app/schemas/_password_mask.py` — `PASSWORD_MASK = "********"` + `mask_password_serializer` 헬퍼
- 4 Response 클래스에 `@field_serializer("user_password")` 적용:
  - CameraResponse (`device.py:480`) / LampResponse (`device.py:1037`)
  - ServerResponse (`server.py:135`) / ServerNestedResponse (`server.py:178`)
- 안전점 `pre-v4.9-phase5` @ 8afcc45

**Fixed**:
- ServerResponse / ServerNestedResponse json_schema_extra example: `"password123"` → `"********"`
- LampResponse example: `"lamp1234"` → `"********"`
- ServerCreate / LampCreate / LampUpdate example: `<your_password>` 자리표시자
- 명세 §9.2.2 로그인 예시 (L14111-14114): `admin/admin123` → `<your_login_id>/<your_password>`
- 명세 §5.3.x Camera 응답 예시 (L5103): `"admin1234"` → `"********"`

**Verified** (8/8 PASS):
- Camera 목록/단일/POST 응답 마스킹
- Lamp 단일 응답 마스킹
- Server 단일 응답 마스킹
- DB 평문 유지 (`cameras.user_password='sensorway1'`, `servers.user_password='testpwd123'`)
- OpenAPI example `"********"` 노출
- DTO shape 변경 0 → .NET 호환성 100%

**Deferred (v4.10 .NET v4.9 Review 잔존)**:
- ENV-1 (Response envelope 5종 표준화, P0)
- AUTH-1 (expires_in/TTL 응답)
- AUTH-2 (PUT /me/password 본문 스키마)
- FMT-1 / ENUM-1~2 / DEV-1~2 / EVT-1 / INT-1 / SVR-1 / AUTH-3~4 (P1)
- DOC-1~3 (P2)

### 3중 정합 (명세 ↔ Swagger ↔ 코드) — Phase 0~5 적용 후

- ✅ 코드: 17/17 PASS
- ✅ Swagger (`/openapi.json`): `ModulePermission`/`PermissionsSchema`/`EnumPermissionModule`/`EnumPermissionVerb` 신규 schema 노출 / 401 응답에 `WWW-Authenticate: Bearer` 헤더 / 422 응답 보강
- ✅ 명세 GOP_Restful_Api_연동설계.md v4.9 행 본문 — Phase 0~4 각 코드 라인 매핑 명시

---



| 형식 | 의미 |
|---|---|
| **Added** | 신규 기능 |
| **Changed** | 기존 기능 변경 |
| **Fixed** | 버그 정정 |
| **Removed** | 기능 제거 |
| **Security** | 보안 관련 |
| **Deprecated** | 폐기 예정 |

---

## [v4.8] — 2026-06-22 (Phase 1~8 통합 — 하루 1차수 묶음 원칙)

**핵심**: DELETE 응답 envelope P1 sweep — 11 endpoint 일관성 통일

### Fixed
- **EM 단건 DELETE 3건** (v4.5 Phase 9 `'data': {}` 정책 정정):
  - `app/routers/event_mapping_cameras.py:442` — `ApiSingleResponse[dict]` → `[None]` + `'data': {}` → `'data': None`
  - `app/routers/event_mapping_speakers.py:354` — 동일
  - `app/routers/event_mapping_lamps.py:347` — 동일
- **일반 단건 DELETE 8건** envelope 표준화:
  - `app/routers/reports.py:293` templates/{id} — `data={"id":...}` → `data=None` (id는 message에)
  - `app/routers/users.py:429` {user_id} — `{"success": True}` envelope 위반 정정
  - `app/routers/user_groups.py:265` {group_id} — 동일
  - `app/routers/user_sessions.py:75/175/267` — 3 endpoint envelope 표준화 (count는 message에 보존)
  - `app/routers/server_metrics.py:339` {server_id}/metrics — `data=None`
  - `app/routers/enclosure_metrics.py:275` — 동일 (deleted_count는 message에)

### Verified
- OpenAPI 36 DELETE endpoint: `ApiSingleResponse_NoneType_` 통일 **22** / dict 잔존 **0** / $ref 없음 14 (별도 작업)
- 클라이언트팀 보고서 v2 §6 P1 11건 일괄 해소
- Container Up healthy / Image rebuild

### Deferred (v4.9+)
- `$ref` 없음 14 DELETE — response_model 일괄 부착 별도 PRD
- `ApiSingleResponse_Union[dict,None]` 4건 (detection/malfunction/connection/action events) — 동일 sweep 가능

### git tag
- `v4.8-final-stable` @ `5263317`

### Phase 8 — Events 4건 DELETE Union[dict,None] → None sweep (같은 날 추가)

**Fixed** (events 4 endpoint response_model 정정):
- `app/routers/detections.py:626` — `Optional[dict]` → `None` + `f"Detection event {event_id} ..."`
- `app/routers/malfunctions.py:629` — 동일 + `f"Malfunction event {event_id} ..."`
- `app/routers/connections.py:548` — 동일 + `f"Connection event {event_id} ..."`
- `app/routers/actions.py:626` — 동일 + `f"Action event {event_id} ..."`

**Verified**:
- OpenAPI 36 DELETE: `NoneType` **26** (Phase 2~7 22 + Phase 8 4) / `Union[dict,None]` **0** / `dict` **0** / $ref 없음 14
- 실 API: detection/connection/action DELETE → PASS
- Workflow 6 agent (337K token / 5분, verdict safe_to_apply)
- 안전점 `pre-events-delete-sweep`

**Manager Impact**: 클라이언트팀 `<bool>` 역직렬화 JsonReaderException 위험 0

### Phase 9 — device_group_mappings cascade 누락 정정 (같은 날 추가)

**클라이언트팀 보고 v3**: 장비 DELETE 시 그룹 `device_count` 미갱신 (스피커 케이스 — orphaned 멤버십)

**근본 원인**: `device_group_mappings.device_id`가 polymorphic FK (6개 자식 테이블) → DB FK 불가, ORM viewonly → cascade 자동 안 됨

**Fixed**:
- `app/routers/lamps.py:436` — `DeviceGroupMapping` 명시 cleanup 추가 (Camera 패턴 일관)
- `app/routers/speakers.py:491` — 동일
- `app/routers/enclosures.py:459` — 동일
- 6 라우터(Camera/Controller/Sensor/Speaker/Enclosure/Lamp) 모두 동일 패턴 통일

**Migration**:
- `app/migrations/v49_device_group_cascade_cleanup.sql` — orphaned 504건 일괄 정리 (SPEAKER 262 + SENSOR 242)
- 결과: 모든 category orphaned **0건**

**Verified**:
- DB 잔존: CONTROLLER 2 / SENSOR 160 / ENCLOSURE 30 / LAMP 60 = 252건 (모두 실 장비 대응)
- Container Up healthy / Image rebuild
- Workflow 3 agent (244K token / 10분)
- 안전점 `pre-cascade-fix`

**진단 정정**: 차장님 받은 가설("램프 정상 / 스피커 누락")은 코드 실측과 반대 — 실제 누락은 Lamp/Speaker/Enclosure 3종

**Deferred (v5.0)**: SQLAlchemy event listener 도입 (라우터 누락 구조적 차단)

### Phase 10 — Controller→Sensor cascade 우회 정정 (같은 날 추가)

**배경**: Phase 9 회신 후 차장님 의문 "Controller 삭제 시 자식 Sensor도 사라졌는데 왜 활성 버그?" → 실측 검증으로 활성 버그 확정 (Sensor row는 ORM cascade로 자동 삭제되지만 device_group_mappings는 잔존)

**근본 원인**: `Controller.sensors = relationship(cascade='all, delete-orphan')`이 ORM cascade로 자식 Sensor row 자동 삭제 → `delete_sensor` 핸들러는 호출 안 됨 → category=SENSOR 매핑 cleanup 우회 → polymorphic device_id에 FK 없어 DB cascade도 동작 불가

**SENSOR 242 orphan 실체**: 시드 후 controller 2개 삭제 시 자식 sensor 242개 row만 자동 삭제되고 매핑은 잔존 (Phase 9에서 정리한 242건의 진짜 원인)

**Fixed**:
- `app/routers/controllers.py:560` — `db.delete(controller)` 직전에 자식 sensor.id 조회 + category=SENSOR 매핑 명시 정리

**Verified**:
- 실 시나리오: 임시 Controller + Sensor 3개 + 매핑 4건 → DELETE → orphan 0 (PASS)
- 전체 DB orphan: 4 category 모두 0 유지

**안전점**: `pre-controller-cascade-fix`

### Phase 12-7 — 불변성 강화 6 sub-phase 통합 (근간 흔드는 변경 차단)

**배경**: Workflow 6 agent로 "근간 흔드는 변경" 전수 식별 (P0 1건 + P1 5건). PRD `docs/PRD_v4.8_Phase12-7_Immutability.md` 작성 후 진행.

**결재 4건 적용**: 명세 §6.3.4 = 코드 차단 / ActionEvent.created_at = 차단 / audit_logs DB TRIGGER = 적용 / Bulk atomicity = v4.9 분리

**Fixed (6 sub-phase)**:
- **7a** UserGroup.permissions P0 — `app/schemas/user.py` UserGroupUpdate에서 permissions 제거 + `extra="forbid"`
- **7b** Event 3종 PUT device_id/device_description 차단 — DetectionEventReplace/MalfunctionEventReplace/ConnectionEventReplace 신규 + 3 라우터 PUT 시그니처 변경
- **7c** /users/me AccountUserSelfUpdate 신설 — role/group_id/is_active 미노출 + `extra="forbid"`. AccountUserUpdate는 admin 경로 유지
- **7d** ActionEvent.created_at 차단 — Replace/Update에서 created_at 제거 (POST Create는 유지)
- **7e** EnclosureUpdate.door_status 일반 PATCH 우회 봉쇄 — 필드 제거 + `extra="forbid"`. 전용 /status 엔드포인트만 허용
- **7f** audit_logs / config_change_logs / user_login_logs DB-level TRIGGER — `app/migrations/v51_audit_immutability_triggers.sql` (BEFORE UPDATE/DELETE/TRUNCATE = RAISE EXCEPTION, append-only)

**Verified** (10/10 PASS):
- 7a/7b/7c/7d/7e: 6 시나리오 422 거부 PASS
- 7f: audit_logs UPDATE/DELETE EXCEPTION + INSERT 정상 PASS
- 정상 시나리오 보호: PUT /me {name:X} → 200 + name 변경

**안전점**: `pre-immutability-phase12-7` @ a9d4655

**Deferred (v4.9 / v5.0)**:
- v5.0: type_device sensor_type 분리 (외부 매니저 호환성) / ActionEvent batch-import endpoint / UserGroup permissions 전용 admin endpoint
- v4.9: Bulk atomicity (SAVEPOINT/dry-run)

### Phase 11 — controllers.py 문자열 리터럴 → Enum 통일

**Fixed**:
- `app/routers/controllers.py:320,422,516` — `_update_device_group_mappings(db, ..., "controller")` → `EnumDeviceCategory.CONTROLLER`
- DELETE 핸들러 cleanup 코드와 동일 타입 흐름 회복 (잠재 422/500 차단)

### Phase 12 — Event 도메인 전수 정밀 분석 + Action invariant 가드 + Det/Mal PATCH 가드 + 시드 정합 회복

**배경**: 차장님 추가 요청 "Event 4종 (Connection/Detection/Malfunction/Action) 추가/삭제/수정 응답 + DELETE cascade 무조건 다 확인"

**Workflow 11 agent 정밀 분석** (993K token / 20분): Discovery + Per-event audit 4 + Live API 실측 4 + Adversarial verify + Synthesize → 4 event × 6 dimension = 24 셀 검증
- **결론**: CASCADE 정책 4종 모두 ✅ MATCH (DB CASCADE/SET NULL 의도 == 실측)
- PARTIAL_GAP — 5 항목 즉시 정정

**Fixed (Phase 12-1: from_event_id 변경 원천 차단 — 차장님 결재)**:
- `app/schemas/event.py` ActionEventUpdate — `from_event_id` 필드 제거 + `model_config = ConfigDict(extra="forbid")`
- `app/schemas/event.py` ActionEventReplace 신규 클래스 — PUT 전용, `from_event_id` 없음, `extra="forbid"`
- `app/routers/actions.py:34` ActionEventReplace import 추가
- `app/routers/actions.py` PATCH `from_event_id` 검증 블록 제거 (dead code)
- `app/routers/actions.py:553` PUT 시그니처 `ActionEventCreate` → `ActionEventReplace`, `event.source_event` 폴리모픽 관계 재사용, `event.from_event_id`는 절대 수정 안 함
- 결과: PATCH/PUT 모두 `from_event_id` 전송 시 422 "Extra inputs are not permitted" 자동 거부

**Fixed (Phase 12-2: Detection/Malfunction PATCH `action_reported` 제거)**:
- `app/schemas/event.py:147` DetectionEventUpdate — `action_reported` 필드 제거
- `app/schemas/event.py:260` MalfunctionEventUpdate — `action_reported` 필드 제거
- 핸들러 무변경 (Pydantic `extra=ignore` 기본값으로 클라이언트 입력 자동 폐기)
- 결과: PATCH로 `action_reported='False'` 강제 후 DELETE → 409 가드 우회 위험 차단

**Migration (Phase 12-3: 시드 1:N invariant 정리)**:
- `app/migrations/v50_action_reported_invariant_fix.sql` 신설 — BEGIN/검증/UPDATE/검증/COMMIT 단일 트랜잭션
- 진단: detection 743 + malfunction 1256 = **1999건 invariant 위배** (`action_reported='True'`인데 actions_count=0)
- 결과: 1999건 True→False 정정, 잔여 위배 0
- 회복 후: `True` 5000건 (모두 ActionEvent 보유) / `False` 2997건 (모두 ActionEvent 0건) — 100% invariant 정합

**Fixed (Phase 12-4: 시드 코드 재발 방지)**:
- `app/utils/init_sample_data.py:876` _create_action_events 함수
- 제거: 무작위 ~2000건에 `action_reported='True'` 추가 박아넣기 (PRD v2.0 위배)
- 정정: 5000 targets만 `action_reported="True"` 설정 (= ActionEvent 매칭)
- docstring에 INVARIANT 명시 — "무작위 True 배정 금지"

**Verified**:
- 실측 4 시나리오: PATCH 422 / PUT 422 / Detection PATCH action_reported 폐기 / PUT 정상 — 모두 PASS
- DB invariant 100% 회복 (detection 0 위배 / malfunction 0 위배)
- POST/DELETE 기존 로직 (`update_source_action_reported` / `reset_source_action_reported`) 그대로 정상 — 6단계 시퀀스 검증 PASS
- Container Up healthy / Image rebuild

**안전점**: `pre-action-invariant-fix`

### Deferred (v5.0)

- 구조적 해결: `device_group_mappings.device_id`에 `devices.id` FK + ON DELETE CASCADE 또는 SQLAlchemy `before_delete` 이벤트 리스너
- P1 잔존: GET list `start_date/end_date` required vs Optional (차장 결재), Event 4종 PUT ConfigChangeLog 누락, Action POST device.status 광역화, Detection PUT detail 누락
- P2 6건 + P3 일괄: Workflow 11 agent 보고서 §recommended_phase_grouping 참조

---

## [v4.7] — 2026-06-21

**핵심**: Account/Auth/Session 도메인 전수 조사 (113 이슈, Verdict FAIL) + DELETE 응답 P0 정정 (4 endpoint)

### Added
- **Workflow 13 agent 전수 조사**: 1.15M token / 12분
  - 30 endpoints / 10 features / 6 DB tables / 8 enums 검토
  - 평균 완성도 62.5% / OWASP 커버리지 41점
  - 이슈 113건: critical 13 / high 38 / medium 39 / low 23
  - Adversarial: confirmed 105 / refuted 0 / additional 9
- 보고서: `docs/Analysis/Account_Auth_Session_Analysis_v4.6.md` (16KB, 236 라인)
- 보고서: `docs/Analysis/Device_Delete_Response_Verification_v4.6.md` (9KB)
- `docs/Analysis/` 디렉터리 신설 + `.gitignore` 예외 추가
- git tag `pre-delete-sweep` 안전점 (DELETE 작업 직전)

### Fixed
- **DELETE 응답 P0 정정 4건** (클라이언트팀 보고 — JsonReaderException):
  - `app/routers/lamps.py:409` — `ApiSingleResponse[dict]` → `[None]` + `data=None`
  - `app/routers/device_groups.py:608` — 동일
  - `app/routers/servers.py:461` — sweep
  - `app/routers/server_categories.py:370` — sweep
- 메시지에 id 보존: `f"Lamp {id} 삭제 성공"` — 감사 추적성 유지

### Top 5 Recommendations (v5.0 권고, 미적용 — 별도 결재)
1. **[critical 6h]** `require_admin/require_role` 의존성 신설 → RBAC 부재 해결 (F06/F08/F09/F10)
2. **[critical 6h]** `get_current_account_user`에 user_sessions 활성 검증 → JWT 무효화 우회 해결
3. **[critical 8h]** `decode_refresh_token` 분리 + payload['type']=='refresh' 강제 + rotation/blacklist
4. **[high 10h]** AuditLog 본문 보강 + SESSION_CREATED/REFRESH/FAILURE 누락 해소
5. **[high 15h]** 비밀번호 정책 정비 + 변경 시 세션 무효화 + 만료/재사용 금지

### Security Findings (OWASP)
- A01 Broken Access Control: 토큰 검증 시 UserSession 활성 미확인 (logout 후 토큰 유효, 24h)
- A04 Insecure Design: refresh 엔드포인트 `type=='refresh'` 검증 안 함 → access_token으로 refresh 가능
- A04: logout이 JWT 자체 무효화 안 함
- A07: Rate limiting 없음 (slowapi/Limiter 미도입) → brute force 가능
- A07: 미존재 user 즉시 401, 존재 bcrypt verify → 타이밍 사이드 채널
- A09: 로그인 성공 시 `AuditLog(SESSION_CREATED)` 미발행 + 실패 시 `UserLoginLog(FAILURE)` 미기록

### Verified
- OpenAPI 9 DELETE endpoint $ref = `ApiSingleResponse_NoneType_` 통일
- 실 API: Lamp/Server/ServerCategory/DeviceGroup DELETE → `data is None`
- Container Up healthy

### git tag
- `v4.7-final-stable` @ `0b3ea1a`
- `pre-delete-sweep` @ `a9ef6d6`

---

## [v4.6] — 2026-06-19

**핵심**: Critical Mismatch 정정 + Camera Preset 감시금지구역 + 시드 재설계 + pagination 검증

### Added
- **Camera Preset 감시금지구역**: `camera_presets.is_restricted_zone BOOLEAN DEFAULT false` 컬럼
  - true 시 매니저 측에서 통일 처리: VMS(RTSP 차단) / NVR(녹화 중지) / db_monitor(이벤트 발행 차단) / Central UI(화면 마스킹)
  - 가이드: `docs/v46_camera_preset_restricted_zone_guide.md`
- 마이그레이션: `app/migrations/v48_camera_preset_restricted_zone.sql`
- 시드 재설계: 제어기 4 / 센서 402 (펜스 100×2 + 복합 21×2 + 스마트복합 60 + 스마트 100) / 카메라 300 / 스피커 200 / 함체 30

### Fixed
- **M01 P0**: `GET /api/servers/categories/{id}` ServerCategory 500 버그 — Server 모델에 없는 `cpu_usage/ram_usage/disk_usage/network_throughput` 4개 인자 → `user_name/user_password/threshold_config` 교체 (v1.6 시점 잠복 부채)
- **M07**: `GET /api/servers/{id}/system-events` — `response_model=ApiSingleResponse[dict]` 부착 + envelope 표준화 (`data: {items, total, pagination}`)

### Changed (명세 정정 — 코드와 정합)
- **M02/M03 §6.5.1/§6.5.2**: detection-log `action`(1:1) → `actions`(1:N) — PRD_ActionEvent_1N v2.0 반영
- **M05 §8.6.3**: server metrics/latest 응답 키 — 코드 `server_id/server_name/latest_metrics`에 맞춤
- **M06 §10.4.4**: PDF 다운로드 — JSON envelope → `application/pdf` 바이너리 스트림 명시
- **M08 §6.2.5**: Malfunction PUT body에서 `action_reported` 제거 (v2.8 시스템 자동관리)
- **M09 §6.4.2**: Action GET query 모두 optional + `from_event_id` 필터 신규
- **M10 §6.4.5**: Action PUT body 2필드 예시 → 4 required (`type_event`, `content`, `user`, `from_event_id`)
- README v1.9 → v4.6, Database SQLite → PostgreSQL, 변경 이력 갱신

### Verified
- **Pagination 안정성**: Camera 30 pages × 10 (300 unique / 중복 0 / 누락 0) + Sensor 21 pages × 20 (402 unique / 중복 0 / 누락 0) — ORDER BY id ASC (PK NOT NULL) 정책 PASS
- DB 카운트: controllers=4 / sensors=402 / cameras=300 / speakers=200 / enclosures=30 / lamps=30
- Container Up healthy / Image rebuild 완료

### Deferred (v4.7+)
- **M04 high risk**: `GET /api/enclosure-metrics` envelope drift (코드 flat vs 명세 items/total) — item shape 결재 필요
- Cursor pagination 전환 (28K 이벤트 대응)
- 잔존 부채 G02/G03/G08/G15 (~52건)

### git tag
- `v4.6-final-stable` @ `536c0b8`

---

## [v4.5] — 2026-06-19

**핵심**: 잔존 부채 분석 + minimal 6 그룹 적용 (37 fail 회복)

### Added
- **Workflow 부채 정밀 분석 PRD**: 46 agent 동원 (3.5M token / 16분) — 15 그룹 × (분석 + minimal 시나리오 + full 시나리오)
- PRD: `docs/PRD_v4.5_Debt_Cleanup.md` (48KB)
- HTML 시각화: `docs/v45_3way_critical_mismatches.html` (37KB)

### Fixed (minimal 6 그룹)
- **G05 ActionEvent 레거시**: 11→8 fail 회복 (3건) — 2 모듈 skip + from_event_id detail dict 전환
- **G07 UserSession/Account**: 12→0 fail 회복 — role `admin`→`ADMIN` + UserSession 필드 + 7 skip
- **G10 Sensor/Speaker/Enclosure**: 9→0 fail 회복 — is_enable + SpeakerResponse + IpController→IoController
- **G11 EM 단일 라우터 envelope**: 7→2 fail 회복 — 3 라우터 DELETE 응답 `'data': {}`
- **G13 Enum**: 4→0 fail 회복 — EnumMappingEventCategory + 3→6
- **G14 Camera URLs (rtsp_uri/port)**: 4→0 fail 회복 — test kwargs 8 lines 삭제
- **합계**: 47 기대 → 37 실회복, 신규 회귀 0, Verdict PASS
- pytest 2218 passed / 126 failed / 35 skipped / 2 errors

### git tag
- `v4.5-final-stable` @ `e7a611e`

---

## [v4.4] — 2026-06-18

**핵심**: Bulk API 4단계 정합화 + 지향성 + JSON→JSONB + multi-line Column 정정

### Added
- **FR-13 Geolocation.heading**: Camera/Speaker/Sensor 부채꼴 시각화용 방위각 (0~360°)
- 마이그레이션: `app/migrations/v47_json_to_jsonb_and_heading.sql` (23 컬럼 ALTER + 402 row backfill)
- PRD 5 파일 (Spec Sync / PostMortem / Directional JsonB 등)

### Fixed
- **Bulk API GAP 14건 명세 정정**: §7.3.9 Request Body 6필드 교체 (`created_ids/config_ids` = 매핑 row PK 명시), 트리거명 정정, 정합성 6건
- **PR-A**: 3 라우터 ConfigLog `if` 가드 제거 (0건 case도 무조건 발행)
- **PR-B**: skipped/not_found_config_ids 실 분류 활성화
- **PR-C**: Lamp `color/buzzer_sound/light_mode` plain str → Pydantic Enum (color="Purple" 500 → 422)
- **PR-D**: EventMapping 6 핸들러 `response_model=ApiSingleResponse[T]` + 404 응답 정의
- **multi-line Column 5건**: with_variant 누락 정정 (Enclosure.geolocation/threshold_config, Lamp.geolocation, DetectionEvent.detail, MalfunctionEvent.detail)

### Changed
- **JSON → JSONB 23 컬럼** 일괄 ALTER (audit_logs / cameras / config_change_logs / event details 등)
- SQLAlchemy `Column(JSONB)` → `Column(JSON().with_variant(JSONB(), "postgresql"))` dialect-aware 패턴 (SQLite 테스트 호환)
- §7.5.7 번호 중복 재채번 (FR-10)

### Security
- **FR-1**: JWT_SECRET_KEY validator (staging/prod 디폴트 거부)
- **FR-3**: CORS 화이트리스트 (`*` 제거)
- **FR-5**: same-request dedup 보강
- **FR-9**: AUTH_MODE 환경별 분기

### Reverted
- **FR-2 user_password 응답 제거 → 복원** (운영 사용 케이스: 등록 직후 확인 / 관리자 화면 / 통합상황도 자동연결). 보안 정책은 후순위

### git tag
- `v4.4-final-stable` @ `050cf6d`

---

## [v4.3] — 2026-06-17

**핵심**: ActionEvent 1:N 관계 + Bulk API 7건 신설 + statement-level NATS 트리거

### Added
- **Bulk API 7건 신설**:
  - DeviceGroup: `DELETE /api/devices/groups/{group_id}/devices` (5.6.9, body: device_ids 1~100)
  - EM Camera: `POST .../cameras/bulk` (7.3.9) + `DELETE .../cameras` (7.3.10)
  - EM Speaker: `POST .../speakers/bulk` (7.4.9) + `DELETE .../speakers` (7.4.10)
  - EM Lamp: `POST .../lamps/bulk` (7.5.9) + `DELETE .../lamps` (7.5.10)
- 응답 3분류: `removed_device_ids` / `skipped_device_ids` / `not_found_device_ids` (멱등성 보장)
- AuditLog `DEVICE_GROUP_UNASSIGNED` action 추가

### Changed
- **Detection/Malfunction Action 조회 1:1 → 1:N** (6.1.7, 6.2.7): `/{event_id}/action` → `/{event_id}/actions` 복수형
- ActionEvent 1:1 제약 제거 → 1:N 관계: source event 하나에 여러 ActionEvent 가능
- 삭제 시 count 기반 복원: 남은 ActionEvent 0개일 때만 `action_reported` "False" 복원
- **NATS 트리거 statement-level 마이그레이션** (`device_group_mappings` + `event_mapping_cameras/speakers/lamps`): row-level → statement-level. 영향 받는 group_id/event_mapping_id당 1건만 SYNC 발행 (5건 등록/해제 시 80% 감소)

### Fixed
- FR-9 AuditLog hook revert (DeviceGroup out-of-domain)

---

## [v4.2] — 2026-03-03

### Added
- **Event Statistics API 신설** (§6.7):
  - `GET /api/events/statistics/summary` (원형 그래프 + 요약 카드)
  - `GET /api/events/statistics/trend` (시간대별 추이)
  - `GET /api/events/statistics/by-device` (제어기별/카메라별)
  - `GET /api/events/statistics/dashboard` (단일 호출 통합)
- ControllerStats `action` 필드 (제어기 소속 센서의 탐지 이벤트 조치 건수)
- 파생 메트릭: daily_averages, active_devices

---

## [v4.1] — 2026-02-15

### Added
- Camera Settings 통합 (`/api/devices/cameras/{id}/settings`)
- ProxyServer API 갱신
- Device Setting 7 enums

---

## [v4.0] — 2026-02-01

### Added
- **DetectionLog API** (§6.5): `GET /api/detection-logs` — DetectionEvent + ActionEvent LEFT JOIN 로그 화면 전용
- ApiResponse Split (envelope 표준화)
- Camera URLs JSONB 통합 (StreamUrls/HomepageUrl/OnvifUrl → `urls` JSONB)

### Removed
- `rtsp_uri`, `rtsp_port` 컬럼 (Camera URLs JSONB로 통합)

---

## [v3.x] — 2026-01

### Added (요약)
- Account / Auth 시스템 (`/api/auth/login`, `/api/users`, `/api/user-groups`)
- Lamp Device + EventMappingLamp API
- Audit Log + Config Change Log (`/api/audit-logs`, `/api/config-change-logs`)
- UserSession API
- Report Generation API (PDF 다운로드)
- ROI 정밀화 + XyPoint
- Camera Preset CRUD
- DeviceGroup Mapping
- Thumbnail API

### Changed (요약)
- `category_event_mapping` enum 분리 (DETECTION / MALFUNCTION / CONNECTION)
- Device polymorphic discriminator 내부화 (SPEC-6.1)
- is_enable 필드 필수화 (모든 디바이스)

---

## [v2.x] — 2025-12

### Added (요약)
- **PostgreSQL 16 마이그레이션** (SQLite → PostgreSQL, alembic 없이 수동 SQL)
- **ServerMetrics 별도 테이블 분리** (Server.cpu_usage/ram_usage/disk_usage/network_throughput 분리)
- **Enclosure Metrics** + 함체 Geolocation
- v1.9 Server Monitoring API + 한글 Swagger

### Changed
- `EnumEventCategory` 분리 + 폴리모픽 매핑 정정
- `action_reported` 시스템 자동관리 정책 도입 (v2.8)

---

## [v1.9] — 2025-12-29
- Server Monitoring API 추가, API 문서 한글화

## [v1.8] — 2025-11-29
- Camera Event Mapping API 추가

## [v1.7] — 2025-11-29
- Event Mapping API 추가

## [v1.6] — 2025-11-29
- Detection/Action 연결 기능 추가

## [v1.5] — 2025-11-28
- Connection 이벤트 API 추가

## [v1.4] — 2025-11-28
- Malfunction 이벤트 API 추가

## [v1.3] — 2025-11-28
- Detection/Action 이벤트 API 추가

---

**문서 버전**: v4.6 / **최종 업데이트**: 2026-06-19
