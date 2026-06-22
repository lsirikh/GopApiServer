# Changelog

GOP RESTful API Test Server 변경 이력. [Keep a Changelog](https://keepachangelog.com/) 형식 따름.

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

### Phase 11 — controllers.py 문자열 리터럴 → Enum 통일

**Fixed**:
- `app/routers/controllers.py:320,422,516` — `_update_device_group_mappings(db, ..., "controller")` → `EnumDeviceCategory.CONTROLLER`
- DELETE 핸들러 cleanup 코드와 동일 타입 흐름 회복 (잠재 422/500 차단)

### Deferred (v5.0)

- 구조적 해결: `device_group_mappings.device_id`에 `devices.id` FK + ON DELETE CASCADE 또는 SQLAlchemy `before_delete` 이벤트 리스너
- Phase 12 보류 (ConfigChangeLog commit 전 이동) — 트랜잭션 일관성, 회귀 위험으로 v5.0 권고

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
