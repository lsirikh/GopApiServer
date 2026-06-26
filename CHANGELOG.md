# Changelog

GOP RESTful API Test Server 변경 이력. [Keep a Changelog](https://keepachangelog.com/) 형식 따름.

## [Unreleased]

## [v4.12] — 2026-06-27

> 하루 1차수 묶음 원칙 — 2026-06-27 작업을 단일 차수 v4.12로 관리.

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
