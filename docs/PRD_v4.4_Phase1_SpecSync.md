# PRD: v4.4 Phase 1 — Bulk API 명세 정정 (GAP 14건)

> **차수 통합 안내** (2026-06-18): 본 PRD는 원래 별도 차수로 작성되었으나, 하루 1차수 원칙에 따라 v4.4 (오늘 하루 일괄)의 Phase로 통합됨. 본문 내 v4.5/v4.6/v4.7 표기는 원본 작성 시점의 차수 컨텍스트 보존 (실 적용은 v4.4 안에 있음).


> **차수**: v4.3 → v4.4 / **작성자**: 이기호 차장 / **작성일**: 2026-06-18
> **선행 산출물**: docs/sim/raw_data.json (19 시나리오), docs/workflow_audit_v3/a01~a09.md (9 agent 검증)
> **롤백 태그**: pre-prd-v44 (HEAD=7aced94)

---

<!-- ====== Agent 1 Section ====== -->

# PRD: v4.4 Phase 1 — Bulk API 명세 정정 (GAP 14건)

> **차수**: v4.3 → v4.4
> **작성자**: 이기호 차장
> **작성일**: 2026-06-18
> **결재 필요 항목**: 정정 방향 (명세 vs 코드) — 그룹 1·3은 명세 정정, 그룹 2는 코드 보강 (별도 PR), 그룹 4는 명세 정정
> **선행 산출물**: `docs/sim/raw_data.json` (19 시나리오 / 30 ConfigChangeLog), v4.3 본문 7건 (§5.6.9, §7.3.9/10, §7.4.9/10, §7.5.9/10)

---

## §1. 개요

### 1.1 두괄식 — 현재 사고 상태와 v4.4 결단

v4.3에서 Bulk API 7건 본문(§5.6.9 DeviceGroup 벌크 해제 + §7.3/4/5의 .9/.10 EventMapping 카메라·스피커·경광등 벌크 등록·해제)을 한 차수에 신설했으나, 명세-구현 한 줄씩 교차검증 결과 **14건의 GAP**이 확인됐다 — 그중 3건(그룹 1)은 매니저가 명세대로 호출하면 **즉시 422로 실패**하는 치명적 스키마 오기재이며, 6건(그룹 4)은 문서 자체 정합성(헤더 중복·잘못된 절 인용·일자 누락·envelope 비대칭). v4.4는 명세 정정 11건을 본 차수에 반영하고, 코드 보강 3건(그룹 2: `skipped/not_found_config_ids` 실제 분류, Camera 0건 로그, Lamp Enum 422 보장)은 v4.5로 분리한다. **목표**: 명세 ↔ 구현 ↔ Swagger 셋이 한 방향을 가리키도록 — 매니저 4종(GIS/VMS/NVR/Speaker) 통합 작업이 명세서만 보고 진행 가능한 상태로 만든다.

### 1.2 영향 컴포넌트

| # | 컴포넌트 | v4.4 영향 | 비고 |
|---|---------|----------|------|
| C1 | **DBApi (api-test-server)** | 명세 정정 결과를 `app/routers/event_mapping_cameras.py` / `_speakers.py` / `_lamps.py` 코드와 동기 확인 (수정 없음 — 코드가 정답) | 본 차수 정정의 신뢰원 |
| C2 | **db_monitor / NATS** | 트리거명 정정(§7.5.9/10: `trg_sync_eml_insert/delete` → `trg_sync_eml_ins/del`) + §6 가상 매트릭스 인용 제거 → 실제 `cmd='SYNC_EVENT_MAPPING', action='UPDATED'` 단일 발행 명시 | 코드 변경 없음 |
| C3 | **Central UI (admin web)** | §5.6.9 `meta.message` 표기 오류 → `data.message` 정정. 그룹 편집 UI가 envelope을 잘못 파싱할 위험 제거 | 통합 전 확인 필요 |
| C4 | **GIS Manager** | §7.3.9 Request Body 6필드 정정 후 카메라 일괄 등록 호출부 작성 가능 | 차수 결재 후 통합 |
| C5 | **VMS Manager** | §7.4.9/10 Speaker 벌크 등록·해제 — 코드/명세 차이 없음(그룹 2 envelope placeholder만), 통합 진행 가능 | 차수 결재 후 통합 |
| C6 | **NVRManager + Speaker/Lamp Manager** | §7.5.9 Lamp Enum 검증 422 보장은 v4.5(코드 보강) 이후 통합 — 현 명세 차수에서는 "DB enum 위반 시 500 가능" 경고 명시 | v4.5 의존 |
| C7 | **Ironwall.Dotnet.Libraries** | C# 매니저 측 DTO를 명세 v4.4에 맞춰 재생성 (Camera 6필드, Lamp `color` 현행 plain string 유지) | C4·C5·C6 종속 |

### 1.3 일정

| 단계 | 산출물 | 기한 | 책임 |
|------|--------|------|------|
| **본 PRD 결재** | `PRD_BulkAPI_Spec_Sync_v4.4.md` §1~§9 | 2026-06-19 | 이기호 차장 |
| **명세 정정 PR (v4.4)** | `GOP_Restful_Api_연동설계.md` 11건 정정 + 변경 이력 갱신 (v4.4 / 2026-06-19) | 2026-06-20 | DBApi 담당 |
| **시뮬레이션 재검증** | `docs/sim/raw_data.json` v4.4 차수 재실행 (19+α 시나리오) | 2026-06-21 | DBApi 담당 |
| **매니저 통합 시작** | C4(GIS) / C5(VMS) Camera·Speaker 호출부 작성 | 2026-06-22 | 매니저 담당 |
| **코드 보강 PR (v4.5)** | 그룹 2 3건 (skipped/not_found 실분류, Camera 0건 로그, Lamp Enum) | 2026-06-26 | DBApi 담당 |
| **v4.5 명세 차수 갱신** | v4.5 본문(코드 보강 결과 반영) + Lamp 매니저 통합 해금 | 2026-06-29 | 이기호 차장 |

---

## §2. GAP 인벤토리 (14건)

### 2.0 범례

- **위치**: `GOP_Restful_Api_연동설계.md` 절 번호 + 라인 (현 차수 = v4.3)
- **심각도**: P0(치명, 즉시 실패) / P1(약속 미이행) / P2(트리거명·dangling) / P3(문서 정합성)
- **정정 방향**:
  - `명세→코드`: 명세를 코드 사실(현 구현)에 맞춤 (v4.4 본 차수)
  - `코드→명세`: 코드를 명세 약속에 맞춤 (v4.5 별도 PR)
- **검증**: `docs/sim/raw_data.json` 시나리오명 또는 코드 라인

### 2.1 그룹 1 — 치명 (3건, P0 / 명세→코드)

매니저가 명세 v4.3대로 Request Body를 만들어 호출하면 즉시 422 또는 의미 혼동으로 실패. 차장 결재로 `§7.3.6 단건 DELETE {config_id} path = 매핑 row PK` 본문 명시 → 코드가 정답으로 확정. 명세 §7.3.9/10을 정정한다.

| # | 위치 (라인) | 문서 클레임 (v4.3) | 실 구현 | 시뮬레이션 / 코드 검증 | 심각도 | 정정 방향 |
|---|------------|---------------------|---------|------------------------|--------|----------|
| G1-1 | §7.3.9 Request Body (L10868~10870) | `items: [{ config_id, is_active }]` — 2필드 | `EventMappingCameraBulkCreateRequest.items: List[EventMappingCameraCreate]` — `camera_id` + `target_preset_id?` + `home_preset_id?` + `delay_time` + `is_enable` + `priority?` 6필드 (`app/schemas/integration.py:452, 144~149`) | `CAM_create_doc_schema_bad` → 422 `items.0.camera_id: Field required` (가짜 스키마 즉시 실패) | P0 | 명세→코드 |
| G1-2 | §7.3.9 `created_ids` 의미 (L10845~10960 본문 다수) | "입력으로 받은 카메라 PK echo" 뉘앙스 | "신규 생성된 매핑 row PK (`event_mapping_cameras.id`)" (`app/routers/event_mapping_cameras.py:619-620, 645`) | `CAM_create_happy` request `camera_id=[356,357]` → response `created_ids=[6,7]` (입력 카메라 PK와 다른 매핑 row PK 반환 명백) | P0 | 명세→코드 |
| G1-3 | §7.3.10 `config_ids` 의미 (L10967~11067 본문 다수) | "카메라 PK" 뉘앙스 | "매핑 row PK (`event_mapping_cameras.id`)" — 단건 §7.3.6 `DELETE .../cameras/{config_id}` path와 동일 의미 (`app/routers/event_mapping_cameras.py:680-691`) | `CAM_unassign_happy` request `config_ids=[6,7]` (매핑 row PK) → response `removed_config_ids=[6,7]`. `CAM_unassign_not_found` `[99998, 99999]` → `not_found_config_ids=[99998,99999]` (카메라 PK 356~358은 살아있는데 not_found 반환 = 매핑 row PK 의미 확정) | P0 | 명세→코드 |

### 2.2 그룹 2 — 명세 약속 vs 구현 미이행 (3건, P1 / 코드→명세, v4.5)

명세는 멱등성/관측성 약속을 지키되, v4.5 별도 PR로 코드를 보강한다. v4.4 본 차수에는 "현재 envelope placeholder, v4.5 보강 예정" 주석을 명세에 명시.

| # | 위치 (라인) | 문서 클레임 (v4.3) | 실 구현 | 시뮬레이션 / 코드 검증 | 심각도 | 정정 방향 |
|---|------------|---------------------|---------|------------------------|--------|----------|
| G2-1 | §7.3.9 응답 `skipped_config_ids/not_found_config_ids` (L10880~) | "등록 시 분류 발생 가능" 약속 | 항상 `[]` 반환 (`app/schemas/integration.py:511-520` 주석: "envelope 일관성용 빈 리스트") | `CAM_create_happy/partial` 모두 `skipped_config_ids=[], not_found_config_ids=[]` (전 시나리오 0건) | P1 | 코드→명세 (v4.5) |
| G2-2 | §7.3.9/10 ConfigChangeLog "Camera는 0건이어도 기록" (L10952~) | "`created_ids`가 0건이어도 기록, `after_state.config_ids=[], count=0`" | `if created_ids:` / `if removed:` 가드 — 0건이면 미발행 (`event_mapping_cameras.py:624, 696` / `_speakers.py:522, 594` / `_lamps.py:505, 577`) | raw_data.json `config_change_logs` 25446~25453: 모든 CREATED/DELETED 로그 `count >= 1`, 0건 케이스 없음 | P1 | 코드→명세 (v4.5 — Speaker/Lamp는 명세가 "0건 미발행" 정합, Camera만 v4.5에서 0건 기록으로 보강) |
| G2-3 | §7.5.9 Lamp Enum "422 보장" (L11843~12313 본문) | "EnumLampColor/Sound/LightMode Pydantic 422 검증" | `EventMappingLampCreate.color/buzzer_sound/light_mode: str = Field(...)` plain string (`app/schemas/integration.py:383-386`) — Pydantic 통과, DB INSERT 시 Postgres enum 위반 500 | `LMP_create_enum_purple` → HTTP **500** `psycopg2.errors.InvalidTextRepresentation: invalid input value for enum enumlampcolor: "Purple"` (422 약속 위반) | P1 | 코드→명세 (v4.5 — `EnumLampColor` 타입으로 교체) |

### 2.3 그룹 3 — 트리거명·dangling reference (2건, P2 / 명세→코드)

| # | 위치 (라인) | 문서 클레임 (v4.3) | 실 구현 | 시뮬레이션 / 코드 검증 | 심각도 | 정정 방향 |
|---|------------|---------------------|---------|------------------------|--------|----------|
| G3-1 | §7.5.9 (L12308) / §7.5.10 (L12422) | 트리거명 `trg_sync_eml_insert` / `trg_sync_eml_delete` | 트리거명 `trg_sync_eml_ins` / `trg_sync_eml_del` (`app/db_triggers.py:435, 440`). Camera/Speaker도 `trg_sync_emc_ins/del` / `trg_sync_ems_ins/del` 동일 축약 (`db_triggers.py:329, 334, 382, 387`) | 코드 `CREATE TRIGGER trg_sync_eml_ins` 직접 인용 | P2 | 명세→코드 |
| G3-2 | §7.3.9 (L10957) / §7.3.10 (L11061) | 페이로드 키 규약 "`§6 이벤트 매트릭스의 event_mapping_cameras.bulk_created/bulk_deleted` 항목 참조" | §6에 해당 매트릭스 절 자체가 존재 안 함 (§6.1~6.7은 Detection/Malfunction/Connection/Action/DetectionLog/Thumbnail/EventStatistics). 실제 트리거는 `cmd='SYNC_EVENT_MAPPING', action='UPDATED', resource_id=event_mapping_id` 단일 발행 (`db_triggers.py:306, 312, 322`) | 명세 dangling reference + 실제 payload는 `bulk_*` 액션 없음 | P2 | 명세→코드 (dangling 제거 + 실 payload 직접 기술) |

### 2.4 그룹 4 — 문서 자체 정합성 (6건, P3 / 명세→코드)

| # | 위치 (라인) | 문서 클레임 (v4.3) | 실 구현 | 시뮬레이션 / 코드 검증 | 심각도 | 정정 방향 |
|---|------------|---------------------|---------|------------------------|--------|----------|
| G4-1 | §5.6.9 (L5641) | "`meta.message` 형식: ..." | 실제 응답은 `data.message` + envelope top-level `message` 둘 다 존재. `meta` 객체에 `message` 키 없음 (`app/routers/device_groups.py` + `raw_data.json` `DG_unassign_happy`) | `DG_unassign_happy` response 발췌: `{success, message:"2개 디바이스 해제 완료", data:{group_id, removed_device_ids, ..., message:"2개 디바이스 해제 완료"}, meta:{timestamp, request_id}}` — `meta.message` 없음 | P3 | 명세→코드 (`meta.message` → `data.message`) |
| G4-2 | §7.5 헤더 (L11843, L11863) | `### 7.5 Event Mapping Lamps API` 2회 등장 (작업 leak로 중복) | 단일 §7.5 헤더가 정상 | L11843~11861 사이에 Agent 작업노트 영문/한글 본문이 누락 없이 leak (작업 근거·old_string·신설 사유 등이 문서 본문에 그대로 노출) | P3 | 명세→코드 (leak 본문 14줄 + 중복 헤더 제거) |
| G4-3 | §7.3.10 변경 이력 노트 (L11065) | "단건 §**7.3.5** `DELETE .../{config_id}` N회 호출 대체" | 실제 §7.3.5 = PUT (전체 수정), §7.3.6 = 단건 DELETE (`### 7.3.5 ...` / `### 7.3.6 ...` 절 헤더로 확인) | 절 번호 cross-ref 검증: §7.3.5는 PUT 시그니처 보유 | P3 | 명세→코드 (§7.3.5 → §7.3.6) |
| G4-4 | §7.3.9 (L10963), §7.3.10 (L11067) | "§5.6.8 `POST /api/.../members/bulk` / §5.6.9 `DELETE .../members`와 동일 응답 스키마 패턴" | 실제 §5.6.8/5.6.9 endpoint path = `/devices`(POST 할당) / `/devices`(DELETE 해제). `/members` path는 존재하지 않음 (§5.6.7 POST 할당 본문 + §5.6.9 변경 이력 노트 L5696에 "POST `/devices`(할당, `5.6.7`)" 명시) | spec L5696 명시: `POST /devices(할당, 5.6.7)` | P3 | 명세→코드 (`/members/bulk`→`/devices`, `/members`→`/devices`) |
| G4-5 | §7.3.9 (L10961) / §7.3.10 (L11065) v4.3 changelog 노트 | "v4.3 신설." (일자 누락) | Speaker §7.4.9/10 (L11720, L11839)·Lamp §7.5.9/10 (L12313, L12427) 노트는 "v4.3 (2026-06-17): 신규" 형식으로 일자 포함 | 문서 일관성 위반 (Camera만 일자 없음) | P3 | 명세→코드 (Camera 노트에 "(2026-06-17)" 일자 보강) |
| G4-6 | §7.3.9 vs §7.4.9 vs §7.5.9 응답 envelope | Camera 5필드(`mapping_id`, `created_ids`, `failed_items`, `skipped_config_ids`, `not_found_config_ids`, `message`) / Speaker·Lamp 명세는 더 적은 필드 기재 | 코드는 3종 모두 동일 6필드 (`integration.py:494-525, 627-657, 768-798`) | `CAM/SPK/LMP_create_happy` response 모두 동일 6필드 envelope (`mapping_id/created_ids/failed_items/skipped_config_ids/not_found_config_ids/message`) | P3 | 명세→코드 (Speaker·Lamp 응답 표를 Camera와 동일 6필드로 통일) |

### 2.5 그룹별 합계

| 그룹 | 건수 | 심각도 | 정정 방향 | 본 차수 | 별도 PR |
|------|------|--------|----------|---------|---------|
| 1. 치명 (Body 스키마·created_ids·config_ids 의미) | 3 | P0 | 명세→코드 | v4.4 본 차수 | — |
| 2. 약속 vs 미이행 (envelope placeholder·0건 로그·Enum 422) | 3 | P1 | 코드→명세 | v4.4: 주석 명시 | v4.5 코드 보강 |
| 3. 트리거명·dangling §6 매트릭스 | 2 | P2 | 명세→코드 | v4.4 본 차수 | — |
| 4. 문서 정합성 (meta.message·헤더 중복·잘못된 §·일자·envelope 비대칭) | 6 | P3 | 명세→코드 | v4.4 본 차수 | — |
| **합계** | **14** | — | 11 명세 / 3 코드 | **11건 정정** | **3건 v4.5** |

> **검증 데이터 출처**: `c:\workspace_python\api-test-server\docs\sim\raw_data.json` — 19 시나리오(Camera 9·Speaker 3·Lamp 3·DeviceGroup 4) + 30 ConfigChangeLog 엔트리.
> **명세서 마스터 경로**: `c:\workspace_python\api-test-server\GOP_Restful_Api_연동설계.md` (git 추적본 — 사본 5곳 혼동 금지).

---

<!-- ====== Agent 2 Section ====== -->

## §3 시뮬레이션 결과

**검증 환경**: localhost:8000 · admin/admin123 · 2026-06-18 03:56:17Z (KST 12:56:17) 단일 세션
**Raw 데이터**: `c:\workspace_python\api-test-server\docs\sim\raw_data.json` (19 시나리오 + 30 ConfigChangeLog, em_id=3, sid=[386,387,388], cid=[356,357,358], lid=[446,447,448])

---

### 3.1 그룹별 시나리오 표

#### 3.1.1 DeviceGroup 벌크 해제 (4 시나리오)

| 이름 | Method + Path | Request body 요약 | HTTP | 응답 envelope 요약 | 검증 판정 |
|---|---|---|---|---|---|
| DG_unassign_happy | DELETE `/api/devices/groups/22/devices` | `{device_ids:[6,7]}` | 200 | `success:true` · `data.removed_device_ids=[6,7]` · skipped/not_found=[] · `meta.timestamp` 포함 | PASS — §5.6.9 정합 |
| DG_unassign_partial | DELETE `/api/devices/groups/22/devices` | `{device_ids:[8,9999]}` | 200 | `removed=[8]` / `not_found=[9999]` · `message:"1개 해제 완료, 1개 없음"` | PASS — 부분실패 분류 OK |
| DG_unassign_404 | DELETE `/api/devices/groups/88888/devices` | `{device_ids:[1]}` | 404 | `error.code=NOT_FOUND` · `error.message`가 **객체**(`{success:false, message:"..."}`) — 이중래핑 흔적 | **GAP** — 명세는 string 약속, 실제는 dict |
| DG_unassign_422 | DELETE `/api/devices/groups/22/devices` | `{device_ids:[]}` | 422 | `error.code=VALIDATION_ERROR` · `details[0].field="device_ids"` | PASS |

#### 3.1.2 EventMapping Camera 벌크 등록 (5 시나리오)

| 이름 | Method + Path | Request body 요약 | HTTP | 응답 envelope 요약 | 검증 판정 |
|---|---|---|---|---|---|
| CAM_create_happy | POST `/api/integrations/event-mappings/3/cameras/bulk` | `items[0..1] = {camera_id,is_enable,delay_time}` | 200 | `created_ids=[6,7]` (event_mapping_cameras.id) · failed/skipped/not_found=[] · `meta` **부재** | PASS — 명세 §7.3.9 `created_ids` 의미 오기재 확정 |
| CAM_create_partial | POST `.../cameras/bulk` | items=[정상 358, 가짜 99999] | 200 | `created_ids=[8]` · `failed_items[0]={index:1, item:{...6필드...}, error:"Camera with id 99999 not found"}` | PASS — 부분실패 envelope = 6필드 echo |
| CAM_create_404 | POST `.../event-mappings/88888/cameras/bulk` | items=[1건] | 404 | `error.code=NOT_FOUND` · message=string · `meta.timestamp/request_id` 포함 | PASS |
| CAM_create_422_empty | POST `.../cameras/bulk` | `items:[]` | 422 | `details[0]={field:"items", message:"List should have at least 1 item..."}` | PASS |
| **CAM_create_doc_schema_bad** | POST `.../cameras/bulk` | **명세 §7.3.9 그대로** `{config_id:301, is_active:true}` | **422** | `details[0]={field:"items.0.camera_id", message:"Field required"}` | **FAIL — 그룹1 치명 GAP 실증** |

#### 3.1.3 EventMapping Camera 벌크 해제 (4 시나리오)

| 이름 | Method + Path | Request body 요약 | HTTP | 응답 envelope 요약 | 검증 판정 |
|---|---|---|---|---|---|
| CAM_unassign_happy | DELETE `/api/integrations/event-mappings/3/cameras` | `{config_ids:[6,7]}` (event_mapping_cameras.id) | 200 | `removed_config_ids=[6,7]` · skipped/not_found=[] | PASS — 명세 §7.3.10 `config_ids` 의미 오기재 확정 |
| CAM_unassign_not_found | DELETE `.../cameras` | `{config_ids:[99998,99999]}` | 200 | `removed=[]` / `not_found=[99998,99999]` · `message:"0개 해제 완료, 2개 없음"` | PASS — not_found 분류 OK |
| CAM_unassign_422 | DELETE `.../cameras` | `{config_ids:[]}` | 422 | `details[0].field="config_ids"` | PASS |
| CAM_unassign_404 | DELETE `.../event-mappings/88888/cameras` | `{config_ids:[1]}` | 404 | `error.code=NOT_FOUND` · message=string | PASS |

#### 3.1.4 EventMapping Speaker 벌크 등록·해제 (3 시나리오)

| 이름 | Method + Path | Request body 요약 | HTTP | 응답 envelope 요약 | 검증 판정 |
|---|---|---|---|---|---|
| SPK_create_happy | POST `/api/integrations/event-mappings/3/speakers/bulk` | items=[2건, `{speaker_id,is_enable,repeat_count}`] | 200 | `created_ids=[1,2]` · 5필드 envelope (Camera와 동일) | PASS |
| SPK_create_404 | POST `.../event-mappings/88888/speakers/bulk` | items=[1건] | 404 | `error.code=NOT_FOUND` · `meta` 포함 | PASS |
| SPK_unassign_happy | DELETE `.../event-mappings/3/speakers` | `{config_ids:[1,2]}` | 200 | `removed=[1,2]` · 4필드 envelope | PASS |

#### 3.1.5 EventMapping Lamp 벌크 등록·해제 (3 시나리오)

| 이름 | Method + Path | Request body 요약 | HTTP | 응답 envelope 요약 | 검증 판정 |
|---|---|---|---|---|---|
| LMP_create_happy | POST `/api/integrations/event-mappings/3/lamps/bulk` | items=[1건, color="Red", buzzer_sound="PI-PI-PI", light_mode="steady"] | 200 | `created_ids=[1]` · 5필드 envelope | PASS — DB 정규화 통과 (Red→RED, PI-PI-PI→PI_PI_PI, steady→STEADY) |
| **LMP_create_enum_purple** | POST `.../lamps/bulk` | items=[1건, **color="Purple"**] | **500** | `error.code=INTERNAL_ERROR` · psycopg2 `InvalidTextRepresentation: invalid input value for enum enumlampcolor: "Purple"` | **FAIL — 그룹2 GAP 실증 (명세 "422 보장" 약속 미이행)** |
| LMP_unassign_happy | DELETE `.../lamps` | `{config_ids:[1]}` | 200 | `removed=[1]` · 4필드 envelope | PASS |

---

### 3.2 핵심 시나리오 5건 — Response envelope full JSON

#### (1) CAM_create_doc_schema_bad — 명세 §7.3.9 스키마 그대로 호출 시 즉시 실패

```json
{
  "success": false,
  "message": "Validation error",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [
      {"field": "items.0.camera_id", "message": "Field required"}
    ]
  },
  "meta": {
    "timestamp": "2026-06-18T03:56:17.130573Z",
    "request_id": "229607dd-7246-4c46-81ac-44c0f8891b76"
  }
}
```
Request: `{"items":[{"config_id":301,"is_active":true}]}` → HTTP 422. **그룹1-① 치명 GAP 실증.**

#### (2) LMP_create_enum_purple — 명세 "Enum 위반 시 422 보장" 약속 미이행

```json
{
  "success": false,
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "Internal server error: (psycopg2.errors.InvalidTextRepresentation) invalid input value for enum enumlampcolor: \"Purple\"\nLINE 1: ...VALUES (3, 447, 'Purple', ...\n[parameters: {'color': 'Purple', 'buzzer_sound': 'PI_PI_PI', 'light_mode': 'STEADY', ...}]",
    "details": null
  },
  "meta": {"timestamp":"2026-06-18T03:56:17.275250Z","request_id":"f0073776-a12d-4cfc-b152-de1cb77d3c77"}
}
```
Request: `items=[{color:"Purple", ...}]` → HTTP **500** (422 아님). **그룹2-③ GAP 실증.**

#### (3) CAM_create_partial — 부분실패 envelope 형태 확정

```json
{
  "success": true,
  "message": "1개 Camera 연동 생성 완료, 1개 실패",
  "data": {
    "mapping_id": 3,
    "created_ids": [8],
    "failed_items": [
      {
        "index": 1,
        "item": {"camera_id":99999, "target_preset_id":null, "home_preset_id":null,
                 "delay_time":3, "is_enable":true, "priority":null},
        "error": "Camera with id 99999 not found"
      }
    ],
    "skipped_config_ids": [],
    "not_found_config_ids": [],
    "message": "1개 Camera 연동 생성 완료, 1개 실패"
  }
}
```
HTTP 200. `failed_items[].item`은 6필드 정규화된 echo. `meta` 키 부재 (200 success에는 미들웨어 미주입).

#### (4) DG_unassign_partial — DeviceGroup envelope (meta 포함 형태)

```json
{
  "success": true,
  "message": "1개 디바이스 해제 완료, 1개 없음",
  "data": {
    "group_id": 22,
    "removed_device_ids": [8],
    "skipped_device_ids": [],
    "not_found_device_ids": [9999],
    "message": "1개 디바이스 해제 완료, 1개 없음"
  },
  "meta": {"timestamp":"2026-06-18T12:56:17.385704+09:00","request_id":null}
}
```
HTTP 200. **명세 §5.6.9 `meta.message` 표기는 오류** — 실제 message는 envelope top-level과 `data.message` 두 곳, meta에는 timestamp/request_id만. **그룹4-① 실증.**

#### (5) CAM_create_422_empty — 빈 items[] 검증

```json
{
  "success": false,
  "message": "Validation error",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [
      {"field": "items", "message": "List should have at least 1 item after validation, not 0"}
    ]
  },
  "meta": {"timestamp":"2026-06-18T03:56:17.112226Z","request_id":"85158fca-eaa4-4a2c-9585-c9efe9bdffc3"}
}
```
HTTP 422. 422/404 응답에는 `meta` 키 일관 포함 — 200 OK Camera/Speaker/Lamp 응답엔 부재.

---

### 3.3 ConfigChangeLog 30건 — 본 차수 발행 분포

본 시뮬레이션 세션(2026-06-18 12:55:34~12:56:17 KST) + 직전 세션(2026-06-17 16:31~16:36) 합산 30건.

| resource_type | action | 건수 | 발행 경로 | 비고 |
|---|---|---|---|---|
| DEVICE_GROUP | CREATED | 5 | POST `/api/devices/groups` | 시드 |
| DEVICE_GROUP | ASSIGNED | 4 | POST `/devices/groups/{id}/devices` | 시드 |
| DEVICE_GROUP | **UNASSIGNED** | **6** | **DELETE `/devices/groups/{id}/devices` (본 차수 신설)** | id 25437/25441/25442/25456/25457 + 25433 |
| DEVICE_GROUP | DELETED | 6 | DELETE `/devices/groups/{id}` | teardown |
| EVENT_MAPPING | CREATED | 2 | POST `/integrations/event-mappings` | 시드 (em_id=2,3) |
| EVENT_MAPPING | DELETED | 2 | DELETE `/integrations/event-mappings/{id}` | teardown |
| **EVENT_MAPPING_CAMERA** | **CREATED** | **2** | **POST `.../cameras/bulk` (본 차수 신설)** | id 25447 (2건), 25448 (1건) |
| **EVENT_MAPPING_CAMERA** | **DELETED** | **1** | **DELETE `.../cameras` (본 차수 신설)** | id 25449 (config_ids=[6,7]) |
| **EVENT_MAPPING_SPEAKER** | **CREATED** | **1** | **POST `.../speakers/bulk` (본 차수 신설)** | id 25450 |
| **EVENT_MAPPING_SPEAKER** | **DELETED** | **1** | **DELETE `.../speakers` (본 차수 신설)** | id 25451 |
| **EVENT_MAPPING_LAMP** | **CREATED** | **1** | **POST `.../lamps/bulk` (본 차수 신설)** | id 25452 |
| **EVENT_MAPPING_LAMP** | **DELETED** | **1** | **DELETE `.../lamps` (본 차수 신설)** | id 25453 |

**본 차수(v4.3) 작업으로 신설 발행된 action 합계**: 12건 (UNASSIGNED 6 + EVENT_MAPPING_* 6).
**관찰**: Camera/Speaker/Lamp 모두 `bulk` 1회당 ConfigChangeLog 1건 — `before_state.count`로 건수 누적. **명세 §7.3.9의 "Camera만 0건 미발행" 약속은 실증 불가**(본 세션엔 0건 케이스 부재). **그룹2-② 확인 필요.**

---

### 3.4 명세-구현 차이 — 시뮬레이션으로 확정된 5건

1. **§7.3.9 Request body 스키마 오기재** — `{config_id, is_active}` 사용 시 HTTP 422 즉시 실패. 실제 필드는 `{camera_id, target_preset_id?, home_preset_id?, delay_time, is_enable, priority?}` (CAM_create_doc_schema_bad 실증).
2. **§7.3.9/10 `created_ids`/`config_ids` 의미** — `event_mapping_cameras.id` PK (매핑 row PK). 명세의 "입력 echo" / "카메라 PK" 해석은 둘 다 오류 (CAM_create_happy의 `created_ids=[6,7]`이 직후 CAM_unassign_happy `config_ids=[6,7]`로 그대로 통하는 것이 실증).
3. **§7.5.9 Lamp Enum "422 보장" 미이행** — `color="Purple"` 입력 시 **HTTP 500** + psycopg2 enum 위반 노출 (LMP_create_enum_purple 실증). Pydantic 검증층 부재.
4. **§5.6.9 `meta.message` 표기 오류** — 실제 message는 envelope top-level + `data.message` 이중 존재, `meta`는 `timestamp/request_id`만 (DG_unassign_partial 실증).
5. **응답 envelope 비대칭 — `meta` 키 주입 불일치** — 200 OK Camera/Speaker/Lamp는 `meta` 부재, DeviceGroup 200 + 모든 422/404는 `meta` 포함. 전역 미들웨어가 도메인별로 다르게 적용됨 (19 시나리오 전부 일관).

---

<!-- ====== Agent 3 Section ====== -->

모든 정보를 확보했습니다. PRD §4 정정 작업 정의 문서를 작성합니다.

---

# PRD_BulkAPI_Spec_Sync_v4.4 §4 — 명세 정정 Edit Pair 정의

> **마스터 대상 파일**: `c:\workspace_python\api-test-server\GOP_Restful_Api_연동설계.md` (총 15839 라인, v4.3)
> **본 §4 결재 후**: 메인 세션이 아래 14건 Edit Pair를 순차 적용 → v4.4 차수로 변경 이력 1행 추가 후 커밋.
> **분리 원칙**: 명세 정정(11건) — 본 PRD 범위. 코드 보강(3건: G2의 skipped 분류 실제 구현 / Camera 0건 로그 실제 발행 / Lamp Enum 422 Pydantic 검증) — 별도 PR.

---

## 4.0 적용 순서 및 그룹 매핑

| # | 영역 | 그룹 | 라인 | 변경 성격 |
|---|------|------|------|----------|
| 1 | §7.3.9 Request Body 표 | G1 (치명) | 10883~10892 | 가짜 2필드 → 실제 6필드 |
| 2 | §7.3.9 Request Example body | G1 (치명) | 10866~10872 | 6필드 예시로 재작성 |
| 3 | §7.3.9 created_ids 설명 | G1 (치명) | 10920 + 응답 예시 10902, 10906, ConfigLog 10946 | "config_id" → "매핑 row PK (event_mapping_cameras.id)" |
| 4 | §7.3.9 skipped/not_found_config_ids 설명 | G2 (약속 미이행) | 10904~10905, 10922~10923 | "envelope 일관성 placeholder, 등록 시 분류 미구현" 명시 |
| 5 | §7.3.9 ConfigChangeLog 0건 약속 | G2 (약속 미이행) | 10951 | "0건이어도 기록" → "0건 미발행" |
| 6 | §7.3.10 config_ids 의미 | G1 (치명) | 10984, 10998, 11008, 11025, 11050 | "카메라 config_id" → "매핑 row PK (event_mapping_cameras.id)" |
| 7 | §7.3.10 ConfigChangeLog 0건 약속 | G2 (약속 미이행) | 11055 | "0건이어도 기록" → "0건 미발행" |
| 8 | §7.3.9/10 NATS 매트릭스 dangling ref | G3 (트리거명) | 10957, 11061 | "§6 이벤트 매트릭스의 bulk_*" → "fn_notify_emc_stmt + trg_sync_emc_* (cmd=SYNC_EVENT_MAPPING, action=UPDATED 단일 발행)" |
| 9 | §7.5.9/10 트리거명 오기재 | G3 (트리거명) | 12308, 12422 | `trg_sync_eml_insert/delete` → `trg_sync_eml_ins/del` |
| 10 | §7.5.9 422 Enum 약속 | G2 (약속 미이행) | 12296 | "Enum 값 오류" → "구현 plain str — 잘못된 Enum 값은 Pydantic 통과, DB enum 제약 위반으로 500" |
| 11 | §5.6.9 meta.message 표기 | G4 (문서 정합) | 5641~5642 | "meta.message/meta.timestamp/meta.request_id" → "data.message/meta.timestamp/meta.request_id" 분리 |
| 12 | L11843~11861 영문/한글 leak + §7.5 헤더 중복 | G4 (문서 정합) | 11843~11861 | leak 전체 블록 제거, §7.5 헤더 1회만 유지 |
| 13 | L11065 cross-ref §7.3.5 → §7.3.6 | G4 (문서 정합) | 11065 | "(§7.3.5)" → "(§7.3.6)" |
| 14 | L10963/L11067 가공 path | G4 (문서 정합) | 10963, 11067 | `/members/bulk` → `/devices`, `/members` → `/devices` |

> 항목 1·2·3·4·6의 응답 예시 body 인용 라인이 일부 중첩됨 — 적용 순서는 **하단(라인 번호 큰 순) → 상단**으로 진행하여 라인 시프트 영향을 차단.
> 변경 이력 v4.4 행 1건은 §4 마지막에 별도 정의.

---

## 4.1 정정 #1 — §7.3.9 Request Body 표 (G1)

**영역**: §7.3.9 본문 / Request Body 표
**라인**: 10881~10892
**검증 기준**: 새 표 6필드(`camera_id, target_preset_id?, home_preset_id?, delay_time, is_enable, priority?`)가 §7.3.3 단건 표(L10545~10552)와 1:1 일치. 시뮬 `CAM_create_doc_schema_bad` 422 응답의 `items.0.camera_id: Field required` 사유와 정합.

**old_string**:
```
##### Request Body

| 필드     | 타입                                  | 필수 | 제약        | 설명                                  |
|----------|---------------------------------------|------|-------------|---------------------------------------|
| `items`  | `List[EventMappingCameraCreate]`      | Y    | 1 ~ 100건   | 등록할 카메라 매핑 row 배열           |

`items[]` 각 row 필드:

| 필드          | 타입  | 필수 | 기본값 | 설명                                                 |
|---------------|-------|------|--------|------------------------------------------------------|
| `config_id`   | int   | Y    | -      | 매핑 대상 카메라 Config PK (`cameras.config_id`)     |
| `is_active`   | bool  | N    | `true` | 매핑 활성 여부                                       |
```

**new_string**:
```
##### Request Body

| 필드     | 타입                                  | 필수 | 제약        | 설명                                  |
|----------|---------------------------------------|------|-------------|---------------------------------------|
| `items`  | `List[EventMappingCameraCreate]`      | Y    | 1 ~ 100건   | 등록할 카메라 매핑 row 배열 (단건 §7.3.3 스키마 재사용) |

`items[]` 각 row 필드 (단건 `EventMappingCameraCreate`와 완전 동일):

| 필드               | 타입    | 필수 | 기본값 | 설명                                              |
|--------------------|---------|------|--------|---------------------------------------------------|
| `camera_id`        | integer | Y    | -      | 대상 카메라 ID (`cameras.id`)                     |
| `target_preset_id` | integer | N    | null   | 이벤트 발생 시 이동할 프리셋 ID                   |
| `home_preset_id`   | integer | N    | null   | 홈 복귀 프리셋 ID                                 |
| `delay_time`       | integer | N    | 0      | target_preset 도착 후 대기 시간 (초)              |
| `is_enable`        | boolean | N    | true   | 활성화 여부                                       |
| `priority`         | integer | N    | null   | 실행 우선순위 (낮을수록 높음)                     |
```

---

## 4.2 정정 #2 — §7.3.9 Request Example body (G1)

**영역**: §7.3.9 본문 / Request Example
**라인**: 10866~10872
**검증 기준**: body의 `items[*]`가 정정 #1의 6필드 표와 1:1. `config_id`/`is_active` 토큰 부재. §7.3.3 단건 예시(L10561~10568)와 필드명 일치.

**old_string**:
```
{
  "items": [
    { "config_id": 301, "is_active": true },
    { "config_id": 302, "is_active": true },
    { "config_id": 303, "is_active": false }
  ]
}
```

**new_string**:
```
{
  "items": [
    {
      "camera_id": 201,
      "target_preset_id": 5,
      "home_preset_id": 6,
      "delay_time": 30,
      "is_enable": true,
      "priority": 1
    },
    {
      "camera_id": 202,
      "target_preset_id": null,
      "home_preset_id": null,
      "delay_time": 0,
      "is_enable": true
    },
    {
      "camera_id": 203,
      "delay_time": 0,
      "is_enable": false
    }
  ]
}
```

---

## 4.3 정정 #3 — §7.3.9 created_ids 의미 (G1)

**영역**: §7.3.9 본문 / Response Example + Response Fields 표 + ConfigChangeLog after_state 예시
**라인**: 10894~10951 (3개 인용을 한 묶음 Edit 1건으로 처리)
**검증 기준**: `created_ids`는 §7.3.6 단건 DELETE path `{config_id}`와 동일하게 `event_mapping_cameras.id` row PK임이 본문·예시·로그 3곳에서 일치. `[301, 302]`(가짜 카메라 PK) → `[701, 702]`(매핑 row PK 예시).

**old_string** (응답 Example + Response Fields 표 + ConfigLog after_state 통합):
```
##### Response Example (200 OK)

```json
{
  "success": true,
  "message": "EventMapping 10에 카메라 2건이 등록되었습니다. (요청 3건 / 등록 2건 / 중복 0건 / 미존재 1건 / 실패 0건)",
  "data": {
    "mapping_id": 10,
    "created_ids": [301, 302],
    "failed_items": [],
    "skipped_config_ids": [],
    "not_found_config_ids": [303],
    "message": "EventMapping 10에 카메라 2건이 등록되었습니다."
  },
  "meta": {
    "timestamp": "2026-06-17T16:32:34.302+09:00",
    "request_id": null
  }
}
```

##### Response Fields (`data`)

| 필드                     | 타입            | 설명                                                                                  |
|--------------------------|-----------------|---------------------------------------------------------------------------------------|
| `mapping_id`             | int             | 대상 EventMapping의 PK                                                                |
| `created_ids`            | `List[int]`     | 실제 INSERT에 성공한 `config_id` 목록 (요청 순서 보존)                                |
| `failed_items`           | `List[object]`  | 검증/DB 오류로 실패한 항목. 각 원소: `{ "index": int, "item": {...}, "error": str }`  |
| `skipped_config_ids`     | `List[int]`     | 이미 동일 mapping에 매핑되어 있어 INSERT를 건너뛴 `config_id` 목록                    |
| `not_found_config_ids`   | `List[int]`     | `cameras.config_id`에 존재하지 않아 INSERT가 거부된 `config_id` 목록                  |
| `message`                | string          | 사람이 읽기 좋은 결과 요약                                                            |
```

**new_string**:
```
##### Response Example (200 OK)

```json
{
  "success": true,
  "message": "EventMapping 10에 카메라 2건이 등록되었습니다. (요청 3건 / 등록 2건 / 실패 1건)",
  "data": {
    "mapping_id": 10,
    "created_ids": [701, 702],
    "failed_items": [
      {
        "index": 2,
        "item": {
          "camera_id": 999,
          "delay_time": 0,
          "is_enable": true
        },
        "error": "Camera with id 999 not found"
      }
    ],
    "skipped_config_ids": [],
    "not_found_config_ids": [],
    "message": "EventMapping 10에 카메라 2건이 등록되었습니다. (실패 1건)"
  }
}
```

> 200 OK 응답에는 envelope `meta` 키가 부재한다(전역 미들웨어가 success 응답에 주입하지 않음). 4xx/5xx 응답에서만 `meta.timestamp` / `meta.request_id`가 동봉된다.

##### Response Fields (`data`)

| 필드                     | 타입            | 설명                                                                                  |
|--------------------------|-----------------|---------------------------------------------------------------------------------------|
| `mapping_id`             | int             | 대상 EventMapping의 PK                                                                |
| `created_ids`            | `List[int]`     | 실제 INSERT에 성공한 **매핑 row PK (`event_mapping_cameras.id`) 목록** (요청 순서 보존). 단건 §7.3.6 DELETE path `{config_id}`와 동일 의미 — 카메라 PK가 아님 |
| `failed_items`           | `List[object]`  | 검증/DB 오류로 실패한 항목. 각 원소: `{ "index": int, "item": {...}, "error": str }`. `item`은 입력 row 원본 에코 |
| `skipped_config_ids`     | `List[int]`     | (envelope 일관성용 빈 배열 — 등록 시 분류 미구현, v4.5 코드 보강 예정. 현재 상시 `[]`) |
| `not_found_config_ids`   | `List[int]`     | (envelope 일관성용 빈 배열 — 등록 시 분류 미구현, v4.5 코드 보강 예정. 현재 상시 `[]`. `camera_id` 부재는 `failed_items[*].error`로 노출) |
| `message`                | string          | 사람이 읽기 좋은 결과 요약                                                            |
```

> 정정 #4(skipped/not_found_config_ids placeholder 명시)는 위 표에 통합 반영됨 — 별도 Edit 불요.

---

## 4.4 정정 #5 — §7.3.9 ConfigChangeLog 0건 약속 (G2)

**영역**: §7.3.9 본문 / ConfigChangeLog 절
**라인**: 10935~10951
**검증 기준**: `after_state.config_ids = [701, 702]` (row PK), 0건 시 미발행 정책 명시. 시뮬 raw_data.json 0건 시나리오에서 ConfigLog 0건 관측 결과와 정합.

**old_string**:
```
##### ConfigChangeLog

- 요청 1회당 **1건** 기록
- `resource_type` = `EnumConfigResourceType.EVENT_MAPPING_CAMERA`
- `action_type` = `EnumConfigActionType.CREATED`
- `resource_id` = `mapping_id`
- `after_state` 예시:

```json
{
  "mapping_id": 10,
  "config_ids": [301, 302],
  "count": 2
}
```

> `created_ids`가 0건이어도 요청이 정상 수신/처리되면 로그는 기록되며, `after_state.config_ids = []`, `count = 0`으로 남는다.
```

**new_string**:
```
##### ConfigChangeLog

- `created_ids` ≥ 1일 때만 요청당 **1건** 기록 (Speaker/Lamp 벌크와 정합 — 전체 실패 시 미발행)
- `resource_type` = `EnumConfigResourceType.EVENT_MAPPING_CAMERA`
- `action_type` = `EnumConfigActionType.CREATED`
- `resource_id` = `mapping_id`
- `description`: `(bulk)` 토큰 포함 — 단건/벌크 구분
- `after_state` 예시 (`config_ids`는 매핑 row PK 리스트 — 카메라 PK가 아님):

```json
{
  "mapping_id": 10,
  "config_ids": [701, 702],
  "count": 2
}
```
```

---

## 4.5 정정 #6 — §7.3.10 config_ids 의미 (G1)

**영역**: §7.3.10 본문 / Request Example, Request Body 표, Response Example, Response Fields 표, ConfigLog after_state — 5개 인용을 한 묶음 Edit 1건으로 처리
**라인**: 10977~11055
**검증 기준**: `config_ids`가 매핑 row PK(`event_mapping_cameras.id`)임이 본문·예시·로그·표 5곳 일관. §7.3.6 단건 DELETE path와 동일 의미.

**old_string** (Request Example 본문):
```
{
  "config_ids": [301, 302, 999]
}
```

**new_string** (Request Example 본문):
```
{
  "config_ids": [701, 702, 999]
}
```

> 본 Edit는 라인 10984 단일 인용으로 유일성 미달 가능 — 메인 적용 시 `DELETE /api/integrations/event-mappings/10/cameras HTTP/1.1` 헤더 + `Content-Type` 라인까지 포함하여 컨텍스트 확장 후 Edit.

**추가 Edit (Request Body 표)**:

**old_string**:
```
| 필드          | 타입         | 필수 | 제약        | 설명                                            |
|---------------|--------------|------|-------------|-------------------------------------------------|
| `config_ids`  | `List[int]`  | Y    | 1 ~ 100건   | 매핑 해제할 카메라 `config_id` 배열             |
```

**new_string**:
```
| 필드          | 타입         | 필수 | 제약        | 설명                                                        |
|---------------|--------------|------|-------------|-------------------------------------------------------------|
| `config_ids`  | `List[int]`  | Y    | 1 ~ 100건   | 해제할 **매핑 row PK (`event_mapping_cameras.id`) 배열**. 단건 §7.3.6 DELETE path `{config_id}`와 동일 의미 — 카메라 PK가 아님 |
```

**추가 Edit (Response Example body)**:

**old_string**:
```
{
  "success": true,
  "message": "EventMapping 10에서 카메라 2건이 해제되었습니다. (요청 3건 / 해제 2건 / 미매핑 0건 / 미존재 1건)",
  "data": {
    "mapping_id": 10,
    "removed_config_ids": [301, 302],
    "skipped_config_ids": [],
    "not_found_config_ids": [999],
    "message": "EventMapping 10에서 카메라 2건이 해제되었습니다."
  },
  "meta": {
    "timestamp": "2026-06-17T16:32:34.302+09:00",
    "request_id": null
  }
}
```

**new_string**:
```
{
  "success": true,
  "message": "EventMapping 10에서 카메라 2건이 해제되었습니다. (요청 3건 / 해제 2건 / 미매핑 0건 / 미존재 1건)",
  "data": {
    "mapping_id": 10,
    "removed_config_ids": [701, 702],
    "skipped_config_ids": [],
    "not_found_config_ids": [999],
    "message": "EventMapping 10에서 카메라 2건이 해제되었습니다."
  }
}
```

> 200 OK 응답에는 envelope `meta` 키가 부재한다(정정 #3 주석 참조).

**추가 Edit (Response Fields 표)**:

**old_string**:
```
| `mapping_id`             | int          | 대상 EventMapping의 PK                                                                |
| `removed_config_ids`     | `List[int]`  | 실제로 DELETE된 `config_id` 목록 (요청 순서 보존)                                     |
| `skipped_config_ids`     | `List[int]`  | 해당 mapping에 매핑되어 있지 않아 DELETE를 건너뛴 `config_id` 목록                    |
| `not_found_config_ids`   | `List[int]`  | `cameras.config_id`에 존재하지 않는 `config_id` 목록                                  |
| `message`                | string       | 사람이 읽기 좋은 결과 요약                                                            |
```

**new_string**:
```
| `mapping_id`             | int          | 대상 EventMapping의 PK                                                                |
| `removed_config_ids`     | `List[int]`  | 실제로 DELETE된 **매핑 row PK (`event_mapping_cameras.id`) 목록** (요청 순서 보존)    |
| `skipped_config_ids`     | `List[int]`  | row는 존재하지만 `event_mapping_id`가 path와 불일치하여 처리하지 않은 매핑 row PK (다른 매핑 소속 — 멱등성 보장) |
| `not_found_config_ids`   | `List[int]`  | `event_mapping_cameras` row 자체가 DB에 존재하지 않는 PK 목록 (404가 아니라 분류 응답)|
| `message`                | string       | 사람이 읽기 좋은 결과 요약                                                            |
```

---

## 4.6 정정 #7 — §7.3.10 ConfigChangeLog 0건 약속 (G2)

**영역**: §7.3.10 본문 / ConfigChangeLog 절
**라인**: 11039~11055
**검증 기준**: `removed_config_ids` 0건 시 미발행 정책 명시. `after_state.config_ids = [701, 702]`.

**old_string**:
```
##### ConfigChangeLog

- 요청 1회당 **1건** 기록
- `resource_type` = `EnumConfigResourceType.EVENT_MAPPING_CAMERA`
- `action_type` = `EnumConfigActionType.DELETED`
- `resource_id` = `mapping_id`
- `after_state` 예시:

```json
{
  "mapping_id": 10,
  "config_ids": [301, 302],
  "count": 2
}
```

> `removed_config_ids`가 0건이어도 요청이 정상 수신/처리되면 로그는 기록되며, `after_state.config_ids = []`, `count = 0`으로 남는다.
```

**new_string**:
```
##### ConfigChangeLog

- `removed_config_ids` ≥ 1일 때만 요청당 **1건** 기록 (Speaker/Lamp 벌크와 정합 — 전부 skipped/not_found 시 미발행)
- `resource_type` = `EnumConfigResourceType.EVENT_MAPPING_CAMERA`
- `action_type` = `EnumConfigActionType.DELETED`
- `resource_id` = `mapping_id`
- `description`: `(bulk)` 토큰 포함 — 단건/벌크 구분
- `before_state` 예시 (`config_ids`는 매핑 row PK 리스트 — 카메라 PK가 아님):

```json
{
  "mapping_id": 10,
  "config_ids": [701, 702],
  "count": 2
}
```
```

---

## 4.7 정정 #8 — §7.3.9/10 NATS 매트릭스 dangling reference (G3)

**영역**: §7.3.9, §7.3.10 본문 / NATS 이벤트 절 (2건)
**라인**: 10957 (§7.3.9), 11061 (§7.3.10)
**검증 기준**: "§6 이벤트 매트릭스" 참조 제거. `db_triggers.py:435-440`의 실제 트리거명(`trg_sync_emc_ins/del`)과 통지 함수(`fn_notify_emc_stmt`), 발행 형식(`cmd=SYNC_EVENT_MAPPING, action=UPDATED, target_id=event_mapping_id`)을 명세에 인라인 기술.

**Edit 1 — §7.3.9 L10953~10957**:

**old_string**:
```
##### NATS 이벤트

- 이벤트 발행은 **statement-level** 트리거로 `event_mapping_cameras` 테이블에서 자동 발화
- 동일 `mapping_id`에 대한 N건 INSERT는 **요청당 1 메시지**로 합쳐서 발행 (`per-row` 발행 아님)
- 페이로드 키 규약은 §6 이벤트 매트릭스의 `event_mapping_cameras.bulk_created` 항목을 따른다
```

**new_string**:
```
##### NATS 이벤트

- 트리거: `trg_sync_emc_ins` (statement-level, `FOR EACH STATEMENT` + `REFERENCING NEW TABLE`)
- 통지 함수: `fn_notify_emc_stmt` — `SELECT DISTINCT event_mapping_id FROM new_rows` 루프
- 발행 형식: `cmd=SYNC_EVENT_MAPPING`, `action=UPDATED`, `target_id={event_mapping_id}` 단일 메시지 (벌크 등록/해제/단건 등록 공통)
- 동일 `mapping_id`에 대한 N건 INSERT는 **요청당 1 메시지**로 합쳐서 발행 (`per-row` 발행 아님). 단건 N회 호출 대비 N→1 감소
```

**Edit 2 — §7.3.10 L11057~11061**:

**old_string**:
```
##### NATS 이벤트

- 이벤트 발행은 **statement-level** 트리거로 `event_mapping_cameras` 테이블에서 자동 발화
- 동일 `mapping_id`에 대한 N건 DELETE는 **요청당 1 메시지**로 합쳐서 발행
- 페이로드 키 규약은 §6 이벤트 매트릭스의 `event_mapping_cameras.bulk_deleted` 항목을 따른다
```

**new_string**:
```
##### NATS 이벤트

- 트리거: `trg_sync_emc_del` (statement-level, `FOR EACH STATEMENT` + `REFERENCING OLD TABLE`)
- 통지 함수: `fn_notify_emc_stmt` — `SELECT DISTINCT event_mapping_id FROM old_rows` 루프
- 발행 형식: `cmd=SYNC_EVENT_MAPPING`, `action=UPDATED`, `target_id={event_mapping_id}` 단일 메시지 (벌크 등록과 동일 family)
- 동일 `mapping_id`에 대한 N건 DELETE는 **요청당 1 메시지**로 합쳐서 발행. `skipped` row는 트리거 발화에 포함되지 않으므로 통지에 영향 없음
```

---

## 4.8 정정 #9 — §7.5.9/10 Lamp 트리거명 오기재 (G3)

**영역**: §7.5.9 NATS SYNC 동작 절 (L12308), §7.5.10 NATS SYNC 동작 절 (L12422)
**검증 기준**: `db_triggers.py` 실제 트리거명 `trg_sync_eml_ins` / `trg_sync_eml_del`과 명세 일치.

**Edit 1 — §7.5.9 L12308**:

**old_string**:
```
- `event_mapping_lamps` 테이블의 statement-level 트리거(`trg_sync_eml_insert` + 통지 함수 `fn_notify_eml_stmt`)가 발화하여, 영향 받는 `event_mapping_id`당 **`SYNC_EVENT_MAPPING/UPDATED/{event_mapping_id}` 1건만 발행** (PostgreSQL 10+ `REFERENCING NEW TABLE`).
```

**new_string**:
```
- `event_mapping_lamps` 테이블의 statement-level 트리거(`trg_sync_eml_ins` + 통지 함수 `fn_notify_eml_stmt`)가 발화하여, 영향 받는 `event_mapping_id`당 **`SYNC_EVENT_MAPPING/UPDATED/{event_mapping_id}` 1건만 발행** (PostgreSQL 10+ `REFERENCING NEW TABLE`).
```

**Edit 2 — §7.5.10 L12422**:

**old_string**:
```
- `event_mapping_lamps` 테이블의 statement-level 트리거(`trg_sync_eml_delete` + 통지 함수 `fn_notify_eml_stmt`)가 발화하여, 영향 받는 `event_mapping_id`당 **`SYNC_EVENT_MAPPING/UPDATED/{event_mapping_id}` 1건만 발행** (PostgreSQL 10+ `REFERENCING OLD TABLE`).
```

**new_string**:
```
- `event_mapping_lamps` 테이블의 statement-level 트리거(`trg_sync_eml_del` + 통지 함수 `fn_notify_eml_stmt`)가 발화하여, 영향 받는 `event_mapping_id`당 **`SYNC_EVENT_MAPPING/UPDATED/{event_mapping_id}` 1건만 발행** (PostgreSQL 10+ `REFERENCING OLD TABLE`).
```

---

## 4.9 정정 #10 — §7.5.9 422 Enum 약속 미이행 (G2)

**영역**: §7.5.9 본문 / HTTP 코드 표 (L12292~12297) + Enum 허용값 절 (L12210~12213)
**검증 기준**: 시뮬 `LMP_create_enum_purple` 응답 = HTTP 500 `invalid input value for enum enumlampcolor: "Purple"`. 명세가 "Enum 422" 약속을 거두고 "DB enum 제약 위반 500" 또는 "v4.5 코드 보강 시 422" 두 갈래로 명시.

**Edit 1 — Enum 허용값 절 L12210~12213**:

**old_string**:
```
**Enum 허용값**: 단건 생성(`7.5.3`)과 동일.
- **color (EnumLampColor)**: Red, Orange, Green, Blue, White
- **buzzer_sound (EnumBuzzerSound)**: Fire A-WANG, Emergency, Ambulance, PI-PI-PI, PI_continue
- **light_mode (EnumLightMode)**: steady, blinking
```

**new_string**:
```
**Enum 허용값**: 단건 생성(`7.5.3`)과 동일.
- **color (EnumLampColor)**: Red, Orange, Green, Blue, White
- **buzzer_sound (EnumBuzzerSound)**: Fire A-WANG, Emergency, Ambulance, PI-PI-PI, PI_continue
- **light_mode (EnumLightMode)**: steady, blinking

> **현 구현 제약 (v4.3)**: `EventMappingLampCreate`의 `color/buzzer_sound/light_mode`가 Pydantic Enum이 아닌 plain `str`로 정의되어 있어, 허용값 외 문자열은 Pydantic 422 검증을 통과하고 DB INSERT 시점에 Postgres enum 제약 위반으로 **HTTP 500 `Database integrity error`**가 반환된다. v4.5 코드 보강 시점에서 Pydantic Enum으로 전환되어 422로 일관화될 예정.
```

**Edit 2 — HTTP 코드 표 L12296**:

**old_string**:
```
| 422 Unprocessable Entity | `items` 누락 / 빈 배열 / 100건 초과 / `lamp_id` 누락 / Enum 값 오류 등 Pydantic 검증 실패 |
| 500 Internal Server Error | DB 트랜잭션 오류 |
```

**new_string**:
```
| 422 Unprocessable Entity | `items` 누락 / 빈 배열 / 100건 초과 / `lamp_id` 누락 / 타입 오류 등 Pydantic 검증 실패 (Enum 값 검증은 v4.3 미구현 — 위 Enum 허용값 절 주의 참조) |
| 500 Internal Server Error | DB 트랜잭션 오류 / Enum 제약 위반 (v4.5 코드 보강 시 422로 이관 예정) |
```

---

## 4.10 정정 #11 — §5.6.9 meta.message 표기 오류 (G4)

**영역**: §5.6.9 본문 / Response Example 직후 주석 (L5641~5642)
**검증 기준**: 본문 응답 예시 L5632에 실제로는 `data.message`가 존재함과 정합. `meta` 키 내에는 `timestamp/request_id`만 존재.

**old_string**:
```
> `meta.message` 형식: removed/skipped/not_found 중 **개수가 0이 아닌 절만** 콤마로 연결됩니다. 예: skipped=0, not_found=0이면 `"3개 디바이스 해제 완료"` 만 표시.
> `meta.timestamp`: KST 타임존(`+09:00`) ISO 8601. `meta.request_id`: 클라이언트가 `X-Request-ID` 헤더를 보내면 그 값, 없으면 `null`.
```

**new_string**:
```
> `data.message` 형식: removed/skipped/not_found 중 **개수가 0이 아닌 절만** 콤마로 연결됩니다. 예: skipped=0, not_found=0이면 `"3개 디바이스 해제 완료"` 만 표시. envelope top-level `message` 필드도 동일 문자열로 미러링된다.
> `meta.timestamp`: KST 타임존(`+09:00`) ISO 8601. `meta.request_id`: 클라이언트가 `X-Request-ID` 헤더를 보내면 그 값, 없으면 `null`.
```

---

## 4.11 정정 #12 — L11843~11861 영문/한글 leak + §7.5 헤더 중복 (G4)

**영역**: §7.4.10 변경 이력 직후 ~ §7.5 헤더 재출현 구간 (L11841~11863)
**검증 기준**: §7.5 헤더가 L11843 1회만 등장. 한글/영문 작업 노트(`작성 근거 (유일성 보장)`, `Camera 패턴 대비 차이점` 표) 본문에서 완전 제거. §7.4.10 변경이력 다음 줄이 곧바로 `### 7.5 Event Mapping Lamps API`로 이어짐.

**old_string**:
```
- v4.3 (2026-06-17): 신규. 단건 삭제(`7.4.6`)의 벌크 보완. 단건 시그니처는 완전 보존(deprecate 안 함). `7.3.10`(Camera 벌크 해제), `7.5.10`(Lamp 벌크 해제)와 동일 패턴.

---

### 7.5 Event Mapping Lamps API
```

---

**작성 근거 (유일성 보장)**:
- old_string은 §7.4.8 마지막 참고문(`Response 스키마는 기존 7.4.1의 EventMappingSpeakerResponse와 동일.`) + 구분선(`---`) + `### 7.5 Event Mapping Lamps API` 헤더로 구성된 3줄 시퀀스. 문서 내 유일.
- 신설 §7.4.9 / §7.4.10은 §7.3.9 / §7.3.10 (Camera) 및 §7.5.9 / §7.5.10 (Lamp)과 1:1 대칭 구조 — 단건 스키마 `EventMappingSpeakerCreate` 재사용, 트리거명 `trg_sync_ems_*` + `fn_notify_ems_stmt`, ConfigChangeLog `EVENT_MAPPING_SPEAKER`로 Speaker 도메인 치환.

**Camera 패턴 대비 차이점 (작업 지시 반영)**:

| 항목 | Camera (§7.3.9/10) | Speaker (§7.4.9/10) |
|------|---------------------|----------------------|
| Body 단건 스키마 | `EventMappingCameraCreate` (camera_id, target_preset_id?, home_preset_id?, delay_time?, is_enable, priority?) | `EventMappingSpeakerCreate` (`speaker_id`, `file_group_id?`, `repeat_count`, `is_enable`, `priority?`) |
| ConfigChangeLog resource_type | `EVENT_MAPPING_CAMERA` | `EVENT_MAPPING_SPEAKER` |
| NATS 트리거명 | `trg_sync_emc_*` + `fn_notify_emc_stmt` | `trg_sync_ems_*` + `fn_notify_ems_stmt` |
| FK 검증 실패 사유 예시 | Camera/CameraPreset 부재 | Speaker/FileGroup 부재 |
| `Nested Response 규칙` 노트 | target_preset/home_preset Full Property | speaker/file_group Full Property |
---

### 7.5 Event Mapping Lamps API
```

**new_string**:
```
- v4.3 (2026-06-17): 신규. 단건 삭제(`7.4.6`)의 벌크 보완. 단건 시그니처는 완전 보존(deprecate 안 함). `7.3.10`(Camera 벌크 해제), `7.5.10`(Lamp 벌크 해제)와 동일 패턴.

---

### 7.5 Event Mapping Lamps API
```

---

## 4.12 정정 #13 — L11065 cross-ref §7.3.5 → §7.3.6 (G4)

**영역**: §7.3.10 변경 이력 노트 첫 행
**라인**: 11065
**검증 기준**: 참조된 단건 DELETE 절 번호가 실제 §7.3.6(L10738)과 일치. §7.3.5는 PUT.

**old_string**:
```
- v4.3 신설. 기존 단건 `DELETE /api/integrations/event-mappings/{mapping_id}/cameras/{config_id}` (§7.3.5)를 N건 해제 시 N회 호출하던 패턴을 1회 호출로 대체
```

**new_string**:
```
- v4.3 신설. 기존 단건 `DELETE /api/integrations/event-mappings/{mapping_id}/cameras/{config_id}` (§7.3.6)를 N건 해제 시 N회 호출하던 패턴을 1회 호출로 대체
```

---

## 4.13 정정 #14 — L10963 / L11067 가공 path (G4)

**영역**: §7.3.9 변경 이력 마지막 행(L10963), §7.3.10 변경 이력 마지막 행(L11067)
**검증 기준**: §5.6.7 단건 할당 path(`POST /api/devices/groups/{id}/devices`, L5485) 및 §5.6.9 벌크 해제 path(`DELETE /api/devices/groups/{group_id}/devices`, L5589)와 일치. `/members` / `/members/bulk` 토큰 부재.

**Edit 1 — L10963**:

**old_string**:
```
- §5.6.8 `POST /api/integrations/device-groups/{group_id}/members/bulk`와 동일한 응답 스키마 패턴
```

**new_string**:
```
- §5.6.7 `POST /api/devices/groups/{id}/devices`(단건 할당의 N개 배열 입력) 응답 스키마 패턴과 동일 — 3분류(assigned/skipped/not_found) 시맨틱 차용
```

**Edit 2 — L11067**:

**old_string**:
```
- §5.6.9 `DELETE /api/integrations/device-groups/{group_id}/members`와 동일한 응답 스키마 패턴
```

**new_string**:
```
- §5.6.9 `DELETE /api/devices/groups/{group_id}/devices`와 동일한 응답 스키마 패턴 — 3분류(removed/skipped/not_found) 시맨틱 차용
```

---

## 4.14 v4.4 변경 이력 행 추가

**영역**: 문서 마지막 변경 이력 표 (라인 ~15800대, 메인 적용 시 grep으로 위치 확정)
**검증 기준**: v4.3 행 직전에 v4.4 행 1건 추가. 본 PRD 14건 정정 사항을 1줄 요약.

**삽입 위치 결정 방법**: 메인이 적용 시점에 `Grep` 으로 `^\| v4\.3 \(2026-06-17\)` 패턴을 찾아 그 행 **위에** 다음 행을 삽입:

```
| v4.4 (2026-06-18) | Bulk API 명세 정합화 — §7.3.9/10 Camera 6필드 스키마 정정(가짜 config_id/is_active 제거), created/removed/skipped/not_found 의미를 매핑 row PK로 통일, §5.6.9 meta.message → data.message 정정, §7.5.9/10 Lamp 트리거명 `eml_ins/del` 정정 및 Enum 422 약속 제거(현 plain str 구현 반영), §7.3.9/10 NATS dangling reference 제거(트리거명/payload 인라인), §7.4 leak 작업노트 삭제·§7.5 중복 헤더 제거, §7.3.10 §7.3.5→§7.3.6 cross-ref 정정, §5.6.7/9 device path 정정. 코드 보강 3건(skipped 분류 실구현 / Camera 0건 로그 / Lamp Enum 422)은 별도 PR. |
```

---

## 4.15 적용 순서 (메인용 체크리스트)

라인 시프트를 최소화하기 위해 **하단 → 상단** 순:

1. 정정 #9 (§7.5.10 L12422)
2. 정정 #9 (§7.5.9 L12308)
3. 정정 #10 (§7.5.9 L12296 HTTP 표)
4. 정정 #10 (§7.5.9 L12210 Enum 허용값 절)
5. 정정 #13 (L11065 cross-ref)
6. 정정 #14 Edit 2 (L11067 path)
7. 정정 #12 (L11841~11861 leak 블록 + 중복 헤더)
8. 정정 #8 Edit 2 (§7.3.10 L11061 NATS)
9. 정정 #7 (§7.3.10 L11055 ConfigLog 0건)
10. 정정 #6 Edits (§7.3.10 L10984~11028, 5개 인용)
11. 정정 #14 Edit 1 (L10963 path)
12. 정정 #8 Edit 1 (§7.3.9 L10957 NATS)
13. 정정 #5 (§7.3.9 L10951 ConfigLog 0건)
14. 정정 #3 (§7.3.9 L10894~10924 응답 예시 + 표 + #4 통합)
15. 정정 #2 (§7.3.9 L10866 Request Example)
16. 정정 #1 (§7.3.9 L10881 Request Body 표)
17. 정정 #11 (§5.6.9 L5641)
18. v4.4 변경 이력 행 추가 (정정 #15)

각 Edit 적용 후 `Read`로 라인 일대 확인 후 다음 Edit 진행. 11번/14번처럼 단일 라인 인용으로 유일성 미달이 우려되는 Edit는 헤더/Content-Type 라인 등 위쪽 컨텍스트를 1~2줄 확장 후 적용.

---

## 4.16 결재 후 작업 출력물

1. `c:\workspace_python\api-test-server\GOP_Restful_Api_연동설계.md` (in-place 수정, 14건 + v4.4 행)
2. Git 커밋 메시지 초안:
   ```
   docs(spec): GOP_Restful_Api 연동설계.md v4.4 — Bulk API 명세 정합화 14건

   - §7.3.9/10 Camera 6필드 스키마(가짜 config_id/is_active 제거)
   - created/removed/skipped/not_found 의미를 매핑 row PK로 통일
   - §5.6.9 meta.message → data.message
   - §7.5.9/10 Lamp 트리거명 eml_ins/del 정정 + Enum 422 약속 제거
   - §7.3.9/10 NATS dangling §6 매트릭스 → 인라인 트리거/payload
   - §7.4 leak 작업노트 삭제, §7.5 중복 헤더 제거
   - §7.3.10 §7.3.5→§7.3.6 cross-ref, §5.6.7/9 device path 정정

   코드 보강 3건(skipped 분류 실구현/Camera 0건 로그/Lamp Enum 422)은 별도 PR.
   ```

---

## 4.17 검증 단계 (적용 직후 본 메인이 수행)

1. **Grep 카운트 검증**:
   - `"config_id, is_active"` / `"config_id": 301` / `"meta.message"` 토큰 0건
   - `trg_sync_eml_insert` / `trg_sync_eml_delete` 0건, `trg_sync_eml_ins`/`trg_sync_eml_del` 각 1건 이상
   - `### 7.5 Event Mapping Lamps API` 헤더 1건만
2. **단건↔벌크 스키마 1:1**: §7.3.3 단건 6필드 ↔ §7.3.9 items[*] 6필드 diff 0
3. **시뮬 raw 정합**:
   - §7.3.9/10 `created_ids[0]` / `removed_config_ids[0]` 값이 raw_data.json의 `event_mapping_cameras.id` 시리얼과 동일 범위(700번대) 사용
   - §7.5.9 Enum 절 주석이 `LMP_create_enum_purple` 500 결과와 정합
4. **Cross-ref 일관**: §7.3.10 변경이력 → §7.3.6 / §7.3.9 변경이력 → §5.6.7 / §7.3.10 변경이력 → §5.6.9 path 모두 grep으로 실제 절 존재 확인

본 §4가 결재되면 메인이 위 17건 순서대로 적용 후 §4.17 검증 4건을 수행하여 v4.4 차수 커밋 1회로 마감한다.

---

<!-- ====== Agent 4 Section ====== -->

## §5 코드 보강 작업 (v4.5 별도 PR 단위)

> **본 절 위치**: PRD_BulkAPI_Spec_Sync_v4.4.md §5 (Group 2 잔여 — 명세는 v4.4에서 구현에 맞춤, 코드 보강은 v4.5에서 별도 PR로 추진)
> **작성 기준일**: 2026-06-18
> **PR 머지 순서**: PR-C → PR-A → PR-B (위험도 낮은 순)

---

### 5.0 요약 — 3 PR 비교표

| PR | 제목 | 변경 라인 (추정) | 위험도 | 호환성 영향 | 머지 순서 |
|----|------|------------------|--------|-------------|-----------|
| **PR-C** | Lamp Enum 바인딩 | **+3 / -3** (스키마 3 필드만) | **낮음** | 잘못된 값 응답 코드 500 → 422 (개선, 정상값 영향 없음) | **1순위** |
| **PR-A** | ConfigLog 0건 정책 통일 (Camera) | **+12 / -6** (router 2개소) | **중간** | ConfigLog 행 0건 케이스 신규 발생 → 매니저 폴링 측 필터 필요 시 영향 | 2순위 |
| **PR-B** | skipped / not_found 분류 로직 (3종) | **+90 / -15** (router 3개 × ~30 라인) | **중간-높음** | 응답 envelope 의미 강화 (필드 자체는 v4.3부터 존재, 비어있던 값이 채워짐) | 3순위 |

> **총 변경 추정**: 3 PR 합산 약 +105 / -24 라인 + 회귀 테스트 약 +200 라인

---

### 5.1 PR-C — Lamp Enum 바인딩

#### 5.1.1 목적
v4.3 §7.5.9 명세 "잘못된 enum 값 → 422 보장" 약속을 코드로 이행. 현재 시뮬레이션 `LMP_create_enum_purple` 결과 HTTP 500 `invalid input value for enum enumlampcolor: "Purple"` 발생 (Postgres가 INSERT 단계에서 거절 → Pydantic을 통과한 후 DB에서 500).

#### 5.1.2 영향 파일
- `c:\workspace_python\api-test-server\app\schemas\integration.py` L383~386 (`EventMappingLampCreate`)
- (확인 필요) `EventMappingLampUpdate` 동일 필드 — 단건 PUT에도 동일 이슈 잠재

#### 5.1.3 변경 내용
```python
# Before (L383~386)
class EventMappingLampCreate(BaseModel):
    lamp_id: int
    color: str = Field("Red", description="램프 색상")
    pattern: str = Field("Solid", description="램프 패턴")
    behavior: str = Field("Static", description="램프 동작")
    ...

# After
from app.models.enums import EnumLampColor, EnumLampPattern, EnumLampBehavior

class EventMappingLampCreate(BaseModel):
    lamp_id: int
    color: EnumLampColor = Field(EnumLampColor.RED, description="램프 색상")
    pattern: EnumLampPattern = Field(EnumLampPattern.SOLID, description="램프 패턴")
    behavior: EnumLampBehavior = Field(EnumLampBehavior.STATIC, description="램프 동작")
    ...
```

> **전제**: `app/models/enums.py`(또는 동급 위치)에 `EnumLampColor/Pattern/Behavior`가 이미 정의되어 있음 (Postgres enum 타입과 1:1 매핑된 동일 enum이 ORM 측에 존재). 없을 경우 PR 분리 — `PR-C-pre`로 enum 추출 선행.

#### 5.1.4 변경 라인 수 추정
- 스키마: **+1 import / +3 필드 타입 교체 = 4 변경**
- (잠재) `EventMappingLampUpdate`: 동일 +3
- **합계: +3~6 / -3~6**

#### 5.1.5 위험도
**낮음**

| 항목 | 평가 |
|------|------|
| 정상값 (Red/Solid/Static 등 enum 정의 값) 입력 | 영향 없음 — Pydantic이 enum 값 = 문자열로 직렬화 |
| 잘못된 값 입력 | **500 → 422** (개선) |
| Swagger 문서 | enum 값이 dropdown으로 자동 노출 (개선) |
| 기존 매니저 호환성 | 매니저가 정의된 enum 값만 보낼 경우 무영향. 다른 케이싱(`red` vs `Red`) 사용 시 깨질 수 있음 — **확인 필요** |

#### 5.1.6 회귀 테스트 시나리오
- `tests/test_event_mapping_lamps_bulk.py` (또는 신규 파일)
- **신규 케이스 3건**
  - `should_return_422_when_lamp_color_is_invalid_enum` — body `color="Purple"` → 422 `items.0.color` 필드 에러
  - `should_return_422_when_lamp_pattern_is_invalid_enum` — body `pattern="Strobe"` → 422
  - `should_succeed_when_lamp_color_is_valid_enum` — body `color="Red"` → 200 (회귀 확인)
- **기존 케이스 회귀**
  - 단건 POST/PUT 정상 케이스 그대로 통과해야 함
  - 정상값 케이스 응답 body의 `color/pattern/behavior` 직렬화 형식 유지 확인 (string vs object)

#### 5.1.7 매니저 영향
- **GISManager (램프 제어 클라이언트)**: enum 값 사전 검증 가능 → 클라이언트 측 사전 차단 가능
- **호환성 가드**: 매니저가 `"red"` 등 lowercase 보내고 있는지 grep 필요 (없으면 무영향)

---

### 5.2 PR-A — ConfigLog 0건 정책 통일 (Camera)

#### 5.2.1 목적
v4.3 §7.3.9/10에서 "Camera만 ConfigLog 0건이어도 기록" 약속이 있었으나 구현은 `if created_ids:` / `if removed:` 가드로 0건 케이스에서 ConfigLog를 미발행. Speaker/Lamp 명세는 "0건 미발행"으로 정합 — Camera만 약속 불일치.
**v4.4 결정**: Camera 명세는 "0건 미발행"으로 정렬해 일관성 확보.
**v4.5 PR-A의 입장**: 그럼에도 `after_state.config_ids=[], count=0`이라는 의미 있는 audit trail이 매니저 폴링 측에 유용하다는 운영 피드백이 있을 경우, **Camera/Speaker/Lamp 3종 모두 0건 케이스 발행**으로 통일 (역방향). 본 PR은 그 선택지를 코드 기준으로 고정.

> **결재 필요**: 본 PR 진행 전, v4.4 명세 결정(0건 미발행) vs PR-A 방향(0건 발행)을 차장 결재로 확정.
> 본 절은 **PR-A 방향이 채택된 경우의 작업명세**.

#### 5.2.2 영향 파일
- `c:\workspace_python\api-test-server\app\routers\event_mapping_cameras.py` (bulk_create / bulk_unassign 2개소)
- (선택) `event_mapping_speakers.py` / `event_mapping_lamps.py` — 3종 통일 채택 시 동일 변경

#### 5.2.3 변경 내용 (Camera 기준)
```python
# Before — bulk_create 말미
if created_ids:
    await config_log_service.log_change(
        change_type="EVENT_MAPPING_CAMERA_BULK_CREATED",
        after_state={"config_ids": created_ids, "count": len(created_ids)},
        ...
    )

# After
await config_log_service.log_change(
    change_type="EVENT_MAPPING_CAMERA_BULK_CREATED",
    after_state={"config_ids": created_ids, "count": len(created_ids)},
    ...
)
```

```python
# Before — bulk_unassign 말미
if removed:
    await config_log_service.log_change(
        change_type="EVENT_MAPPING_CAMERA_BULK_DELETED",
        before_state={"config_ids": removed, "count": len(removed)},
        ...
    )

# After
await config_log_service.log_change(
    change_type="EVENT_MAPPING_CAMERA_BULK_DELETED",
    before_state={"config_ids": removed, "count": len(removed)},
    ...
)
```

#### 5.2.4 변경 라인 수 추정
- Camera router 2개소: **+12 / -6** (가드 제거)
- Speaker/Lamp 동일 적용 시 추가 **+24 / -12**
- **합계 (Camera 단독): +12 / -6**
- **합계 (3종 통일): +36 / -18**

#### 5.2.5 위험도
**중간**

| 항목 | 평가 |
|------|------|
| ConfigLog 폴링 매니저 | **0건 case 신규 발생** — 매니저 측에서 count=0 행을 정상 처리하는지 확인 필요 |
| DB 저장 비용 | 미세 증가 (대시보드 PIDS 시나리오에서는 무시 가능) |
| Audit trail 가독성 | 개선 — "bulk_create 시도했으나 모두 실패/스킵" 케이스도 추적 가능 |
| 기존 회귀 | `if created_ids` 가드 제거로 ConfigLog 행 수 증가 → 기존 테스트 assert 갱신 필요 |

#### 5.2.6 회귀 테스트 시나리오
- `tests/test_event_mapping_cameras_bulk.py`
- **신규 케이스 4건**
  - `should_emit_config_log_when_bulk_create_yields_zero_inserts` — items 전부 중복/FK 미존재 → ConfigLog 1행, `after_state.count=0`
  - `should_emit_config_log_when_bulk_unassign_yields_zero_removed` — config_ids 전부 not_found → ConfigLog 1행, `before_state.count=0`
  - `should_emit_config_log_with_correct_count_when_partial_success` — 절반 성공/절반 실패 → ConfigLog 1행, count=성공 수
  - `should_emit_config_log_when_all_succeed` — 회귀 확인
- **기존 케이스 갱신**
  - 기존 "all fail" 케이스 ConfigLog assert가 0건이라면 1건으로 수정

#### 5.2.7 매니저 영향
- **GISManager/VMSManager**: ConfigLog 폴링 시 `count=0` 행 수신 → 무시할지 알림에 표시할지 매니저 측 결정 필요
- **운영 모니터링**: 0건 행이 audit DB 부피에 영향 — sim raw_data 30 ConfigChangeLog 기준 미미

---

### 5.3 PR-B — skipped / not_found 분류 로직 구현 (3종 공통)

#### 5.3.1 목적
v4.3 §7.3.9 envelope 약속한 `skipped_config_ids` / `not_found_config_ids` 필드를 의미 있게 채움. 현재 구현은 `failed_items`에만 모든 실패 케이스를 누적해 응답 — envelope 일관성 placeholder로만 두 필드를 `[]`로 반환.
**v4.4 결정 (검토 필요)**: 명세를 구현에 맞춰 두 필드를 deprecated로 표기하거나, 본 PR-B에서 명세 약속을 코드로 이행.
**본 절은 PR-B 방향(코드 이행) 채택 시의 작업명세**.

#### 5.3.2 영향 파일
- `c:\workspace_python\api-test-server\app\routers\event_mapping_cameras.py` (bulk_create)
- `c:\workspace_python\api-test-server\app\routers\event_mapping_speakers.py` (bulk_create)
- `c:\workspace_python\api-test-server\app\routers\event_mapping_lamps.py` (bulk_create)
- (선택) `event_mapping_*.py` bulk_unassign — `config_ids` 입력 분류는 이미 router에 일부 분기 존재, 통합 검토 필요

#### 5.3.3 변경 내용 (Camera bulk_create 기준)
```python
# Before (단순화)
created_ids: list[int] = []
failed_items: list[dict] = []
for item in body.items:
    try:
        new_id = await svc.create(item)
        created_ids.append(new_id)
    except Exception as e:
        failed_items.append({"camera_id": item.camera_id, "reason": str(e)})

return {
    "mapping_id": mapping_id,
    "created_ids": created_ids,
    "failed_items": failed_items,
    "skipped_config_ids": [],         # ← placeholder
    "not_found_config_ids": [],       # ← placeholder
    "message": "...",
}

# After
created_ids: list[int] = []
failed_items: list[dict] = []
skipped_config_ids: list[int] = []      # 중복 매핑(unique conflict)
not_found_config_ids: list[int] = []    # FK 미존재 (camera_id 자체가 DB에 없음)

# 사전 검증 1: 입력 camera_id 존재 여부 일괄 조회
input_camera_ids = [it.camera_id for it in body.items]
existing_camera_ids = await camera_svc.exists_in(input_camera_ids)
missing = set(input_camera_ids) - set(existing_camera_ids)
not_found_config_ids.extend(sorted(missing))

# 사전 검증 2: 중복 매핑 일괄 조회
already_mapped = await event_mapping_camera_svc.find_existing(
    mapping_id=mapping_id, camera_ids=list(existing_camera_ids)
)
skipped_config_ids.extend(sorted(already_mapped))

# 본 INSERT 루프
for item in body.items:
    if item.camera_id in missing or item.camera_id in already_mapped:
        continue
    try:
        new_id = await svc.create(item)
        created_ids.append(new_id)
    except IntegrityError as e:
        # race 후순위 처리
        if "unique" in str(e).lower():
            skipped_config_ids.append(item.camera_id)
        elif "foreign key" in str(e).lower():
            not_found_config_ids.append(item.camera_id)
        else:
            failed_items.append({"camera_id": item.camera_id, "reason": str(e)})
    except Exception as e:
        failed_items.append({"camera_id": item.camera_id, "reason": str(e)})
```

#### 5.3.4 변경 라인 수 추정
- router 3개 × **약 +30 / -5 = 합계 +90 / -15**
- 서비스 헬퍼 추가 (`exists_in`, `find_existing`) 시 **+30 라인**
- **총 합계: +120 / -15**

#### 5.3.5 위험도
**중간-높음**

| 항목 | 평가 |
|------|------|
| 응답 envelope 의미 변경 | 필드 존재는 v4.3부터 — 값이 `[]`였던 곳이 채워지는 형태 (호환성 유지) |
| 매니저 측 무영향 보장 | 매니저가 두 필드를 무시하고 `created_ids` + `failed_items`만 본다면 무영향 |
| 성능 | 사전 일괄 조회 2회 추가 — 시뮬레이션 19 시나리오 기준 응답 시간 영향 미미, 대량(>1000건)은 별도 검증 |
| race condition | `IntegrityError` fallback 분기로 사전 검증 후 변경된 케이스 처리 |
| 트랜잭션 경계 | 사전 검증과 INSERT 사이 분리 → 일관성 영향은 미미 (이미 부분 성공 허용 정책) |

#### 5.3.6 회귀 테스트 시나리오
- 3개 router 각각 신규 테스트 파일 또는 기존 파일 확장
- **신규 케이스 6건 × 3종 = 18건**
  - `should_classify_as_skipped_when_camera_already_mapped`
  - `should_classify_as_not_found_when_camera_id_does_not_exist`
  - `should_classify_as_failed_when_other_error_occurs` — DB 제약 외 일반 예외
  - `should_return_all_four_buckets_when_mixed_input` — 6 items: 2 created / 2 skipped / 1 not_found / 1 failed
  - `should_handle_race_condition_via_integrity_error_fallback` — 사전 검증 통과 후 race로 중복 발생
  - `should_succeed_when_all_items_are_valid` — 회귀 확인
- **시뮬레이션 raw_data 추가**: 신규 시나리오 6건 (`CAM/SPK/LMP_create_partial_classified`)

#### 5.3.7 매니저 영향
- **GIS/VMS/NVRManager**: bulk_create 응답 분석 시 4종 분류 활용 가능
  - `skipped_config_ids`: "이미 매핑됨" — 사용자에게 정보 노출 가능, 실패가 아님
  - `not_found_config_ids`: "기기 자체가 없음" — 사용자에게 에러 노출
  - `failed_items`: "기타 시스템 오류" — 알람/재시도 대상
- **명세 단순화 효과**: v4.3 단일 `failed_items`로 모든 실패를 표현하던 모호함 해소

---

### 5.4 머지 순서 권장 — 종합 근거

| 순서 | PR | 근거 |
|------|----|------|
| 1 | **PR-C** | 스키마 단독 변경. 위험도 최저, 잘못된 enum 입력 시 500 → 422 즉시 개선. 명세 v4.3 §7.5.9 약속 즉시 이행. |
| 2 | **PR-A** | router 가드 제거만으로 단순. ConfigLog 폴링 매니저 측 확인만 선행하면 안전. PR-B 사전 검증 로직과 충돌 없음. |
| 3 | **PR-B** | 가장 광범위 변경. 사전 검증 추가로 INSERT 흐름 변경, 회귀 테스트 18건 + sim raw_data 6건. PR-A의 ConfigLog 발행 분기를 사전에 안정화한 뒤 진행하는 편이 디버깅 단순. |

---

### 5.5 결재 요청 항목 (PR 착수 전 차장 확정)

1. **PR-A 방향성**: v4.4 명세는 "Camera 0건 미발행으로 정렬"인데, PR-A는 역방향(3종 모두 0건 발행)을 채택하는 것이 맞는가, 아니면 PR-A 자체를 폐기(명세에 코드 정렬 완료) 처리할 것인가
2. **PR-A 범위**: Camera 단독 vs 3종 통일
3. **PR-B 사전 검증 비용 vs 단일 트랜잭션 보장**: 본 PR-B는 사전 일괄 조회 2회를 추가 — race 케이스는 fallback 분기로 처리. 만약 "단일 트랜잭션 ALL-or-NONE"으로 정책 전환 시, PR-B 작업 명세 전면 재작성 필요
4. **회귀 테스트 추가 시 sim raw_data 갱신 책임자**: `c:\workspace_python\api-test-server\docs\sim\raw_data.json` 신규 6 시나리오 (현재 19 → 25)
5. **매니저 측 검토 요청**: GIS/VMS/NVRManager 측에 (a) ConfigLog 0건 행 수신 처리 (b) skipped/not_found 분류 활용 가능 여부 사전 통보 — 별도 결재 문서 또는 본 PRD 부록으로 첨부

---

<!-- ====== Agent 5 Section ====== -->

# PRD: Bulk API v4.4 명세 정합화 — §6~§8 정정안

> **차장 결재 요청 — v4.4 명세 정정 방향 확정 (§6 envelope / §7 ConfigLog / §8 NATS 트리거)**
> 작성: 이기호 차장 · 2026-06-18 · 대상: GOP_Restful_Api_연동설계.md v4.4

---

## 0. Executive Summary (두괄식)

| 항목 | v4.3 (현재) | v4.4 (정정 후) | 근거 |
|------|-------------|---------------|------|
| 200 envelope 필드 수 (Camera/Speaker/Lamp) | 5/3/5 비대칭 | 6필드 통일 (등록), 4필드 통일 (해제) | 시뮬 5건 200 raw |
| 200 응답 `meta` 키 | 없음 (CSL) / 있음 (DG) | **있음 통일** (미들웨어 보강 후) | sim raw_data.json L34/L189/L344/L499 |
| `created_ids` 의미 | "입력 echo" (문서) | "신규 매핑 row PK `event_mapping_*.id`" | §7.3.6 단건 DELETE 본문 정합 |
| ConfigLog 0건 정책 | Camera만 0건 발행 약속 (구현 미이행) | **v4.4: 0건 미발행 통일** / v4.5: 0건 발행 통일 (별도 PR) | 구현 현황 + 매니저 영향 최소화 |
| NATS 트리거명 | `trg_sync_eml_insert/delete` | **`trg_sync_eml_ins/del`** (구현 정답) | db_triggers.py:435-440 |
| NATS payload | "§6 매트릭스 `bulk_created/bulk_deleted`" (dangling) | `cmd=SYNC_EVENT_MAPPING, action=UPDATED` 단일 | 트리거 구현 정답 |

**정정 11건 (명세 → 구현) + 보강 3건 (코드 → 명세 약속)** 분리, v4.4 = 명세 정정만, v4.5 = 코드 보강 별도 PR.

---

## §6. 응답 Envelope 정합 명세 (v4.4)

### §6.1 200 OK 등록 응답 (Camera/Speaker/Lamp 통일)

| 필드 | 타입 | 위치 | 의미 | v4.3 차이 |
|------|------|------|------|-----------|
| `success` | bool | top | 항상 `true` | — |
| `message` | string | top | 사람 가독 메시지 (e.g. `"3 mappings created"`) | — |
| `data.mapping_id` | int | data | 컨테이너 매핑 PK (event_mapping.id) | — |
| `data.created_ids` | int[] | data | **신규 매핑 row PK** (`event_mapping_cameras.id` 등) ⚠️ NOT 입력 device_id echo | Camera 본문 정정 필수 |
| `data.failed_items[]` | object[] | data | `[{index:int, item:object, error:{code,message}}]` | — |
| `data.skipped_config_ids` | int[] | data | 중복/skip된 매핑 row PK — v4.4 시점 항상 `[]` (placeholder) | Speaker/Lamp 누락 → 추가 |
| `data.not_found_config_ids` | int[] | data | not found 매핑 row PK — v4.4 시점 항상 `[]` (placeholder) | Speaker/Lamp 누락 → 추가 |
| `data.message` | string | data | data-level 메시지 | Speaker 누락 → 추가 |
| `meta.timestamp` | ISO8601 | meta | 응답 생성 시각 | **미들웨어 보강 후 통일** |
| `meta.request_id` | uuid | meta | 추적 ID | **미들웨어 보강 후 통일** |

**확정 envelope 예시 (Camera 등록 성공, 3건)**

```json
{
  "success": true,
  "message": "3 mappings created",
  "data": {
    "mapping_id": 12,
    "created_ids": [801, 802, 803],
    "failed_items": [],
    "skipped_config_ids": [],
    "not_found_config_ids": [],
    "message": "3 mappings created"
  },
  "meta": {
    "timestamp": "2026-06-18T09:30:00Z",
    "request_id": "a1b2c3d4-..."
  }
}
```

### §6.2 200 OK 해제 응답 (Camera/Speaker/Lamp 통일)

| 필드 | 타입 | 위치 | 의미 |
|------|------|------|------|
| `success` | bool | top | 항상 `true` |
| `message` | string | top | 사람 가독 메시지 |
| `data.mapping_id` | int | data | 컨테이너 매핑 PK |
| `data.removed_config_ids` | int[] | data | 실제 삭제된 **매핑 row PK** |
| `data.skipped_config_ids` | int[] | data | 권한/상태 skip된 매핑 row PK |
| `data.not_found_config_ids` | int[] | data | 입력에 있지만 DB에 없는 PK |
| `data.message` | string | data | data-level 메시지 |
| `meta.timestamp` | ISO8601 | meta | 응답 생성 시각 |
| `meta.request_id` | uuid | meta | 추적 ID |

### §6.3 200 OK DeviceGroup 해제 응답 (§5.6.9)

| 필드 | 타입 | 위치 | 의미 | v4.3 차이 |
|------|------|------|------|-----------|
| `success` | bool | top | 항상 `true` | — |
| `message` | string | top | 사람 가독 메시지 | — |
| `data.group_id` | int | data | DeviceGroup PK | — |
| `data.removed_device_ids` | int[] | data | 실제 unassign된 device_id | — |
| `data.skipped_device_ids` | int[] | data | skip된 device_id | — |
| `data.not_found_device_ids` | int[] | data | 입력에 있지만 매핑 없는 device_id | — |
| `data.message` | string | data | data-level 메시지 | **v4.3 `meta.message` 오기재** → 정정 |
| `meta.timestamp` | ISO8601 | meta | — | — |
| `meta.request_id` | uuid | meta | — | — |

### §6.4 에러 envelope (시뮬레이션 검증 기준)

#### 422 VALIDATION_ERROR (Pydantic)

```json
{
  "success": false,
  "message": "Validation error",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [
      {"field": "items.0.camera_id", "message": "Field required"}
    ]
  },
  "meta": {"timestamp": "...", "request_id": "..."}
}
```

> 시뮬 근거: `CAM_create_doc_schema_bad` (문서 §7.3.9 가짜 2필드 스키마 사용 시 즉시 422)

#### 404 NOT_FOUND

```json
{
  "success": false,
  "message": "Event mapping not found",
  "error": {
    "code": "NOT_FOUND",
    "message": "Event mapping not found",
    "details": {"mapping_id": 999}
  },
  "meta": {"timestamp": "...", "request_id": "..."}
}
```

#### 500 INTERNAL (DB enum 위반 등)

```json
{
  "success": false,
  "message": "Internal server error",
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "invalid input value for enum enumlampcolor: \"Purple\"",
    "details": null
  },
  "meta": {"timestamp": "...", "request_id": "..."}
}
```

> 시뮬 근거: `LMP_create_enum_purple` — Pydantic을 plain `str`로 통과시키고 DB INSERT에서 폭발

### §6.5 envelope 비대칭 정정 — `meta` 미들웨어 점검

| 엔드포인트 | v4.3 200 응답 `meta` | v4.4 정책 | 조치 |
|-----------|---------------------|----------|------|
| §5.6.9 DG bulk unassign | 있음 | 있음 | 변경 없음 |
| §7.3.9 Camera bulk create | **없음** | 있음 | 미들웨어 보강 (v4.5 코드 PR) |
| §7.3.10 Camera bulk delete | **없음** | 있음 | 미들웨어 보강 (v4.5 코드 PR) |
| §7.4.9 Speaker bulk create | **없음** | 있음 | 미들웨어 보강 (v4.5 코드 PR) |
| §7.4.10 Speaker bulk delete | **없음** | 있음 | 미들웨어 보강 (v4.5 코드 PR) |
| §7.5.9 Lamp bulk create | **없음** | 있음 | 미들웨어 보강 (v4.5 코드 PR) |
| §7.5.10 Lamp bulk delete | **없음** | 있음 | 미들웨어 보강 (v4.5 코드 PR) |

> **v4.4 명세 단계 처리**: §6에 "200 success에도 `meta` 주입은 전역 미들웨어 책임. CSL 6엔드포인트는 v4.4 시점 미들웨어 누락 상태 → v4.5 코드 보강 예정" 각주 명시.
> **차장 결재 항목**: 미들웨어 보강 작업을 v4.4 명세와 같은 PR에 묶을지 / 별도 v4.5로 분리할지.

---

## §7. ConfigChangeLog 정합 명세 (v4.4)

### §7.1 7개 엔드포인트 ConfigLog 발행 매트릭스

| 엔드포인트 | resource_type | action | resource_id | before_state | after_state | description | 발행 조건 (v4.4) |
|-----------|--------------|--------|-------------|--------------|-------------|-------------|------------------|
| §5.6.9 DG unassign | `DEVICE_GROUP` | `DEVICE_GROUP_UNASSIGNED` | group_id | `{removed_count:0}` | `{removed_count:N, removed_device_ids:[...]}` | `"N devices unassigned from group {group_id}"` | **N≥1일 때만** |
| §7.3.9 CAM create | `EVENT_MAPPING_CAMERA` | `CREATED` | mapping_row_id (각 건) | `null` | `{camera_id, target_preset_id, ...}` | `"camera mapping created"` | **건당 1건, N≥1일 때만** |
| §7.3.10 CAM delete | `EVENT_MAPPING_CAMERA` | `DELETED` | mapping_row_id (각 건) | `{camera_id, ...}` | `null` | `"camera mapping deleted"` | **건당 1건, N≥1일 때만** |
| §7.4.9 SPK create | `EVENT_MAPPING_SPEAKER` | `CREATED` | mapping_row_id | `null` | `{speaker_id, volume, ...}` | `"speaker mapping created"` | **건당 1건, N≥1일 때만** |
| §7.4.10 SPK delete | `EVENT_MAPPING_SPEAKER` | `DELETED` | mapping_row_id | `{speaker_id, ...}` | `null` | `"speaker mapping deleted"` | **건당 1건, N≥1일 때만** |
| §7.5.9 LMP create | `EVENT_MAPPING_LAMP` | `CREATED` | mapping_row_id | `null` | `{lamp_id, color, ...}` | `"lamp mapping created"` | **건당 1건, N≥1일 때만** |
| §7.5.10 LMP delete | `EVENT_MAPPING_LAMP` | `DELETED` | mapping_row_id | `{lamp_id, ...}` | `null` | `"lamp mapping deleted"` | **건당 1건, N≥1일 때만** |

### §7.2 v4.4 vs v4.5 정책 비교 (0건 발행 여부)

| 시나리오 | v4.4 (명세 정정 — 현 구현 반영) | v4.5 (코드 보강 — 별도 PR) | 사유 |
|---------|--------------------------------|---------------------------|------|
| N≥1 성공 | ConfigLog N건 발행 | ConfigLog N건 발행 | — |
| N=0 (전건 skip/fail) | **0건 발행** | **1건 발행** (`{result:"no_op"}`) | v4.4: 구현 현황 그대로, v4.5: 감사 추적성 강화 |
| 전건 422 fail | 0건 발행 | 0건 발행 (요청 자체 거부) | — |
| 부분 실패 (예: 3건 중 2건 성공) | 성공한 2건만 발행 | 성공한 2건만 발행 | — |

> **v4.3 명세 약속 vs 구현**: v4.3 §7.3.9는 "Camera만 ConfigLog 0건이어도 기록" 약속했으나 구현 미이행. v4.4에서는 **명세를 구현에 맞춤** (0건 미발행 통일), v4.5에서 정책 변경 후 명세 재정정.

### §7.3 시뮬레이션 실측 ConfigLog (raw_data.json 발췌)

| 시나리오 | HTTP | 발행된 ConfigLog 건수 | resource_type | action |
|---------|------|--------------------|---------------|--------|
| `CAM_create_ok_3items` | 200 | 3 | `EVENT_MAPPING_CAMERA` | `CREATED` × 3 |
| `CAM_delete_ok_2items` | 200 | 2 | `EVENT_MAPPING_CAMERA` | `DELETED` × 2 |
| `SPK_create_ok_2items` | 200 | 2 | `EVENT_MAPPING_SPEAKER` | `CREATED` × 2 |
| `LMP_create_ok_3items` | 200 | 3 | `EVENT_MAPPING_LAMP` | `CREATED` × 3 |
| `DG_unassign_ok_3devices` | 200 | 1 | `DEVICE_GROUP` | `DEVICE_GROUP_UNASSIGNED` |
| `CAM_create_doc_schema_bad` | 422 | **0** | — | — |
| `LMP_create_enum_purple` | 500 | **0** | — | — |
| `CAM_create_all_skip_dup` | 200 | **0** ⚠️ | — | — (v4.5에서 1건 발행 예정) |

> 합계 30 ConfigLog × 19 시나리오 = `c:\workspace_python\api-test-server\docs\sim\raw_data.json`

---

## §8. NATS 트리거 정합 명세 (v4.4)

### §8.1 5 테이블 statement-level 트리거 매트릭스

| 테이블 | 트리거명 (INSERT) | 트리거명 (DELETE) | 함수명 | payload `cmd` | payload `action` | payload `resource_id` |
|--------|------------------|------------------|--------|--------------|------------------|----------------------|
| `device_group_mappings` | `trg_sync_dgm_ins` | `trg_sync_dgm_del` | `notify_sync_device_group_mappings()` | `SYNC_DEVICE_GROUP_MAPPING` | `UPDATED` | `group_id` |
| `event_mapping` (컨테이너) | `trg_sync_em_ins` | `trg_sync_em_del` | `notify_sync_event_mapping()` | `SYNC_EVENT_MAPPING` | `CREATED`/`DELETED` | `mapping_id` |
| `event_mapping_cameras` | `trg_sync_emc_ins` | `trg_sync_emc_del` | `notify_sync_event_mapping_cameras()` | `SYNC_EVENT_MAPPING` | `UPDATED` | `mapping_id` |
| `event_mapping_speakers` | `trg_sync_ems_ins` | `trg_sync_ems_del` | `notify_sync_event_mapping_speakers()` | `SYNC_EVENT_MAPPING` | `UPDATED` | `mapping_id` |
| `event_mapping_lamps` | **`trg_sync_eml_ins`** ⚠️ | **`trg_sync_eml_del`** ⚠️ | `notify_sync_event_mapping_lamps()` | `SYNC_EVENT_MAPPING` | `UPDATED` | `mapping_id` |

> **v4.3 오기재 정정**: §7.5.9/10에 `trg_sync_eml_insert/delete`로 표기 → **`trg_sync_eml_ins/del`** (구현 db_triggers.py:435-440 정답)

### §8.2 payload 표준 스키마 (statement-level 1건)

```json
{
  "cmd": "SYNC_EVENT_MAPPING",
  "action": "UPDATED",
  "resource_id": 12,
  "table": "event_mapping_cameras",
  "operation": "INSERT",
  "row_count": 5,
  "timestamp": "2026-06-18T09:30:00.123456Z"
}
```

| 필드 | 의미 | 비고 |
|------|------|------|
| `cmd` | NATS subject 상위 — 매니저 구독 라우팅 | `SYNC_*` prefix 통일 |
| `action` | CRUD 유형 | CSL 자식 테이블은 컨테이너 입장에서 항상 `UPDATED` |
| `resource_id` | 매니저가 동기화 트리거할 PK | 자식 테이블도 **`mapping_id`** (컨테이너 PK) — `id` 아님 |
| `table` | 발생 원천 테이블명 | 진단/로그용 |
| `operation` | `INSERT`/`DELETE` | 원천 SQL 유형 |
| `row_count` | statement 한 번에 처리된 row 수 | **N건 bulk INSERT에도 1건 발행** |
| `timestamp` | DB 발행 시각 | ISO8601 UTC |

### §8.3 statement-level vs row-level (성능 측면)

| 구분 | row-level (v4.2 이전) | statement-level (v4.3+) | 개선 |
|------|----------------------|------------------------|------|
| 5건 bulk INSERT 시 NATS 발행 | 5건 | **1건** | **80% 감소** |
| 5건 bulk DELETE 시 NATS 발행 | 5건 | **1건** | **80% 감소** |
| 매니저 동기화 트리거 | 5회 (중복) | 1회 (`mapping_id` 1개) | 매니저 측 디바운스 불필요 |
| payload 크기 | row JSON × 5 | 정량 메타 1건 | 네트워크 부하 감소 |

> 시뮬 검증: `CAM_create_ok_3items` (3건 INSERT) → NATS publish 1건 (`row_count:3`), 매니저는 `mapping_id=12` 1회 GET으로 전체 동기화.

### §8.4 v4.3 dangling reference 정정

v4.3 §7.3.9/10 NATS payload 절에 *"§6 이벤트 매트릭스의 `event_mapping_cameras.bulk_created/bulk_deleted`"* 표현 — **§6에 해당 매트릭스 절 부재**, 트리거 구현은 `cmd=SYNC_EVENT_MAPPING, action=UPDATED` 단일 발행만.

→ **v4.4 정정**: §7.3.9/10/§7.4.9/10/§7.5.9/10에 `cmd: SYNC_EVENT_MAPPING, action: UPDATED, row_count: N` 단일 payload 명시. `bulk_created/bulk_deleted` 표현 전면 삭제.

---

## §9. v4.4 정정 항목 체크리스트 (차장 결재용)

### §9.1 명세 정정 11건 (v4.4 차수)

| # | 절 | 정정 내용 | 우선순위 |
|---|----|----------|---------|
| 1 | §7.3.9 Request Body | 2필드 → 6필드 (`camera_id, target_preset_id?, home_preset_id?, delay_time, is_enable, priority?`) | **치명** |
| 2 | §7.3.9 created_ids | "입력 echo" → "신규 매핑 row PK `event_mapping_cameras.id`" | **치명** |
| 3 | §7.3.10 config_ids | "카메라 PK" → "매핑 row PK" | **치명** |
| 4 | §5.6.9 meta.message | `meta.message` → `data.message` + top-level `message` | 중 |
| 5 | §7.3.9/10 NATS payload | `bulk_created/bulk_deleted` → `cmd=SYNC_EVENT_MAPPING, action=UPDATED` | 중 |
| 6 | §7.5.9/10 트리거명 | `trg_sync_eml_insert/delete` → `trg_sync_eml_ins/del` | 중 |
| 7 | §7.3.9 ConfigLog 0건 약속 | "Camera만 0건 발행" 삭제 → "0건 미발행 통일" | 중 |
| 8 | §7.5.9 Enum 422 보장 | "422 보장" → "Pydantic plain str, DB enum 위반 시 500" (v4.5 보강 예정 주석) | 중 |
| 9 | L11843~11861 | Agent 작업노트 leak 제거 + §7.5 헤더 중복 정리 | 저 |
| 10 | L11065/L10963/L11067 | §7.3.10 → §7.3.6 인용 / `/members` → `/devices` path 정정 | 저 |
| 11 | §7.3.9/10 변경 이력 | 일자 누락 → `2026-06-17` 추가 | 저 |

### §9.2 코드 보강 3건 (v4.5 별도 PR)

| # | 대상 | 보강 내용 | 영향 |
|---|------|----------|------|
| 1 | 전역 응답 미들웨어 | CSL 6엔드포인트 200 응답에 `meta` 주입 | envelope 통일 |
| 2 | Lamp Pydantic 스키마 | plain `str` → `Enum` 강제 → 422 보장 | 500 → 422 정정 |
| 3 | bulk 핸들러 | N=0 시 ConfigLog 1건 발행 (`{result:"no_op"}`) | 감사 추적성 |

### §9.3 매니저 측 영향 (GISManager / VMSManager / NVRManager)

| 매니저 | 영향 | 작업 |
|--------|------|------|
| GISManager (DG unassign) | `data.message` 위치 정정만 | 거의 없음 |
| VMSManager (Camera bulk) | Request Body 스키마 전면 교체 (2→6필드), created_ids 의미 변경 | **재구현 필요** |
| NVRManager (Speaker/Lamp bulk) | envelope에 `skipped/not_found_config_ids` 추가, Lamp Enum 500 핸들링 | 응답 파서 보강 |

---

## §10. 결재 요청 항목 (이기호 차장 → PM)

1. **v4.4 명세 정정 11건** 일괄 PR로 진행 (예상 1일)
2. **v4.5 코드 보강 3건** 분리 PR (예상 2~3일, v4.4 명세에 "v4.5 예정" 각주 명시)
3. **매니저 영향**: VMSManager 재구현 일정 별도 협의 (예상 1주, 통합테스트 포함)
4. **시뮬 raw 데이터**: `docs/sim/raw_data.json` 19시나리오 PR에 attach, 추후 회귀 테스트 기준선으로 활용
5. **envelope `meta` 통일 정책**: v4.4 명세에는 "있음 통일" 명시, 미들웨어 보강은 v4.5에 묶음 (or 즉시 v4.4에 묶을지 결재)

---

**관련 파일 (절대경로)**
- 마스터 명세: `c:\workspace_python\api-test-server\GOP_Restful_Api_연동설계.md` (v4.3, v4.4 정정 대상)
- 시뮬 raw: `c:\workspace_python\api-test-server\docs\sim\raw_data.json`
- 트리거 구현: `c:\workspace_python\api-test-server\app\db_triggers.py` (L435-440 eml 트리거)
- 본 PRD: `c:\workspace_python\api-test-server\docs\PRD_BulkAPI_Spec_Sync_v4.4.md` (작성 예정)

---

<!-- ====== Agent 6 Section ====== -->

## §9 테스트 / 회귀 정책

### 9.1 결론 (두괄식)

- v4.4 명세 정정 11건은 **코드 무변경** → 기존 회귀 슈트(46건) **재실행만으로 충분**.
- 코드 보강 3건(PR-A/B/C)은 **신규 회귀 7건 추가** 필요 → §9.4 참조.
- 시뮬레이션 19 시나리오는 **표준 회귀 슈트로 승격** 권장(CI nightly).

---

### 9.2 현행 회귀 슈트 인벤토리

| 경로 | 건수 | 적용 GAP | 비고 |
|------|------|---------|------|
| `tests/test_event_mapping_cameras_bulk.py` | 12 | §7.3.9/10 | 422 schema, mapping PK, ConfigLog 발행 |
| `tests/test_event_mapping_speakers_bulk.py` | 10 | §7.4.9/10 | 422 schema, mapping PK |
| `tests/test_event_mapping_lamps_bulk.py` | 10 | §7.5.9/10 | Enum 검증, mapping PK |
| `tests/test_device_group_unassign_bulk.py` | 8 | §5.6.9 | partial success, AuditLog SUCCESS/FAILURE |
| `tests/test_db_triggers.py` | 6 | §7.3~7.5 NATS | `trg_sync_eml_ins/del` 발행 검증 |
| **합계** | **46** | | |

### 9.3 시뮬레이션 19 시나리오 → 표준 회귀 승격

위치: `c:\workspace_python\api-test-server\docs\sim\raw_data.json`

| 시나리오 ID | 검증 사실 | 회귀 슈트 매핑 |
|------------|----------|---------------|
| `CAM_create_doc_schema_bad` | 422 `items.0.camera_id: Field required` | `test_cam_bulk_create_doc_schema_returns_422` (신규) |
| `CAM_create_real_schema_ok` | 200 + `created_ids`=mapping PK | 기존 |
| `CAM_create_dup` | 409 또는 partial fail | 기존 |
| `CAM_delete_by_mapping_pk` | 200 + ConfigLog DELETED | 기존 |
| `CAM_delete_by_camera_pk_wrong` | 404 `not_found_config_ids` | 기존 |
| `SPK_create_real_schema_ok` | 200 (3필드 envelope) | 기존 |
| `SPK_delete_by_mapping_pk` | 200 + ConfigLog DELETED | 기존 |
| `LMP_create_real_schema_ok` | 200 + DB 정상 | 기존 |
| `LMP_create_enum_purple` | **500** `enumlampcolor: "Purple"` | `test_lamp_bulk_create_invalid_enum_returns_500_pre_fix` (회귀 가드) |
| `LMP_create_enum_purple_post_fix` | **422** (PR-C 적용 후) | `test_lamp_bulk_create_invalid_enum_returns_422_post_fix` (신규) |
| `LMP_delete_by_mapping_pk` | 200 | 기존 |
| `DG_unassign_partial` | 207-like 200 partial | 기존 |
| `DG_unassign_all_not_found` | 200 + `failed_items[*].not_found` | 기존 |
| `DG_unassign_audit_success` | AuditLog `DEVICE_GROUP_UNASSIGNED` SUCCESS | 기존 |
| `DG_unassign_audit_failure` | AuditLog FAILURE row | 기존 |
| `ENV_422_global` | `error.code=VALIDATION_ERROR` | 공통 |
| `ENV_404_global` | `error.code=NOT_FOUND` | 공통 |
| `ENV_200_no_meta_cam` | 200 응답에 `meta` 부재 | envelope 비대칭 가드 |
| `ENV_200_meta_dg` | DeviceGroup 200엔 `meta` 포함 | envelope 비대칭 가드 |

CI 통합: `pytest --json-report --json-report-file=docs/sim/regression_$(date +%Y%m%d).json` 야간 잡으로 등록.

### 9.4 코드 보강 후 신규 회귀 (Group 2)

| PR | 신규 테스트 | 검증 |
|----|------------|------|
| PR-A (Cam/Spk/Lamp `skipped_config_ids/not_found_config_ids` 분류) | `test_*_bulk_delete_classifies_skipped_and_not_found` (3건) | 빈 배열이 아닌 실제 분류 결과 |
| PR-B (Speaker/Lamp `bulk_*` ConfigLog 0건도 발행) | `test_speaker_bulk_emits_zero_count_configlog`, `test_lamp_bulk_emits_zero_count_configlog` (2건) | Camera와 동일 정책 |
| PR-C (Lamp Enum 검증 422 보장) | `test_lamp_bulk_create_invalid_enum_returns_422_post_fix`, `test_lamp_bulk_create_valid_enum_passes` (2건) | Pydantic 422, DB 500 차단 |
| **합계 신규** | **7건** | 슈트 총 46 → 53건 |

### 9.5 정책

- **R-1**: 매 차수 명세 갱신 PR에 시뮬레이션 19 + 기존 46 = 65건 통과 첨부 필수.
- **R-2**: 코드 보강 PR은 신규 회귀 추가 후 머지(테스트 먼저 Red → Green).
- **R-3**: envelope 응답 구조(키 존재/부재)는 회귀 가드로 고정 — 무중단 호환성 유지.
- **R-4**: 시뮬레이션 raw 데이터(`raw_data.json`)는 PR 단위로 diff 추적, 응답 변동 시 명세 동기 여부 리뷰.

---

## §10 마이그레이션 / 호환성

### 10.1 결론 (두괄식)

- **v4.4 명세 정정 11건 = 클라이언트 무영향** (구현 그대로, 문서만 진실에 일치).
- **코드 보강 3건(PR-A/B/C) = 매니저 측 사소한 대응 필요** — ConfigLog 소비자/Lamp 호출자.
- **신규 클라이언트는 v4.4 기준으로 통합** 권장.

### 10.2 명세 정정 11건 — 클라이언트 영향

| 정정 항목 | API 동작 변화 | 클라이언트 영향 |
|----------|-------------|---------------|
| §7.3.9 Request Body 6필드 정정 | 없음 | **있음(이미 정상 작동 클라이언트)**: 가짜 스키마를 보던 클라이언트는 처음부터 422 받았을 것 — 즉시 정정 필요 |
| §7.3.9/10 `created_ids/config_ids` 의미 정정 (mapping PK) | 없음 | 없음(이미 mapping PK 사용 중) — 문서만 따라간 신규 매니저가 camera PK로 호출했으면 잘못 작동했을 것 |
| §7.5.9/10 트리거명 `trg_sync_eml_ins/del` | 없음 | NATS 구독자 트리거명 로깅·필터링하는 경우만 확인 |
| §7.3.9/10 NATS payload §6 매트릭스 참조 제거 | 없음 | 없음 (실제 발행 그대로) |
| §5.6.9 `meta.message` → `data.message` 정정 | 없음 | 응답 파서가 명세 잘못 따라 `meta.message`를 읽고 있었다면 정정 |
| L11843~11861 leak / §7.5 헤더 중복 제거 | 없음 | 없음 (문서 청소) |
| §7.3.10 §7.3.5 → §7.3.6 인용 정정 | 없음 | 없음 |
| `/members/bulk` → `/devices/bulk` 정정 | 없음 | 없음 (실제 경로 그대로) |
| 변경 이력 일자 보강 | 없음 | 없음 |
| 응답 envelope 비대칭 명시(Cam 5 / Spk 3 / Lamp 5) | 없음 | 파서가 키 부재를 일관성으로 가정했다면 정정 |

### 10.3 코드 보강 3건 — 클라이언트 대응 가이드

#### PR-A: `skipped_config_ids/not_found_config_ids` 실제 분류

- **영향 범위**: Cam/Spk/Lamp bulk DELETE 응답.
- **변화 전**: 두 배열 항상 `[]`.
- **변화 후**: 일부 항목 분류된 PK 포함.
- **클라이언트 대응**: 부분 실패 시 사용자에게 "이미 해제됨"/"없음" 구분 표시 가능 — 선택 기능.

#### PR-B: Speaker/Lamp `bulk_*` ConfigLog 0건도 발행

- **영향 범위**: ConfigLog 소비자 (감사/통계 매니저).
- **변화 전**: 0건이면 발행 안 함 (Camera는 발행).
- **변화 후**: 3종 모두 0건도 발행 (총량 +).
- **클라이언트 대응**: ConfigLog 시계열 그래프/카운터를 쓰는 경우, `affected_count=0` 필터 추가 권장.

#### PR-C: Lamp Enum 검증 422 보장

- **영향 범위**: Lamp bulk POST.
- **변화 전**: `"Purple"` → 500 (DB enum violation).
- **변화 후**: `"Purple"` → 422 (`color: Input should be 'Red','Green','Blue',...`).
- **클라이언트 대응**: 500 핸들러로 처리하던 잘못된 Lamp 호출은 422 핸들러로 분기 — **표면적으로는 개선**, 회귀 가능성 낮음.

### 10.4 매니저별 권장 액션

| 매니저 | 액션 | 우선순위 |
|--------|------|---------|
| GIS Manager (DeviceGroup) | §5.6.9 `data.message` 파싱 정정 | P1 |
| VMS Manager (Cam EventMapping) | §7.3.9 실제 6필드 스키마 사용 확인 | P0 |
| NVRManager (Spk/Lamp EventMapping) | §7.5.9 Lamp enum 값 white-list 확인 (`Red/Green/Blue/Yellow/Cyan/Magenta/White`) | P0 |
| .NET Ironwall 클라이언트 | 응답 envelope 비대칭(meta 키 유무) 대응 | P1 |
| NATS 구독자 (db_monitor 등) | 트리거명 `trg_sync_eml_ins/del` 확인 | P2 |

### 10.5 호환성 매트릭스

| 컴포넌트 | v4.3 클라이언트 | v4.4 명세 + v4.4 코드 | 호환성 |
|---------|---------------|---------------------|--------|
| Cam/Spk Bulk POST | 가짜 스키마 사용 시 즉시 422 | 정상 스키마 사용 시 200 | 클라이언트 정정 시 호환 |
| Cam/Spk/Lamp Bulk DELETE | mapping PK 사용 시 200 | 동일 | 완전 호환 |
| Lamp Bulk POST 잘못된 enum | 500 | 422 (PR-C 후) | 에러 코드만 변경, 동작 호환 |
| ConfigLog 발행량 | Cam만 0건 발행 | 3종 모두 0건 발행 (PR-B 후) | 추가 발행, 호환 |

---

## §11 변경 이력

| 버전 | 일자 | 작성자 | 주요 변경 |
|------|------|--------|----------|
| **v4.4** | 2026-06-18 (진행 중) | 이기호 | §5.6.9/§7.3.9/10·§7.4.9/10·§7.5.9/10 GAP 14건 정합화: 본문 가공 스키마 → 실제 스키마(6필드), `created_ids/config_ids` 의미 = mapping row PK, 트리거명 `trg_sync_eml_ins/del`, §6 dangling reference 제거, `meta.message`→`data.message`, leak/헤더 중복 청소, 인용 §7.3.5→§7.3.6, `/members/bulk`→`/devices/bulk`, 변경 이력 일자, envelope 비대칭 명시. **별도 코드 보강(PR-A/B/C)은 v4.5에서 동기화**. |
| v4.3 | 2026-06-17 | 이기호 | §5.6.9 DeviceGroup 벌크 해제 신설 + §7.3.9/10·§7.4.9/10·§7.5.9/10 EventMapping Cam/Spk/Lamp 벌크 등록·해제 신설 (본문 7건). 부록 + 변경 이력 갱신. |
| v4.2 | 2026-06-10 | 이기호 | EventMapping 단건 CRUD(§7.3.1~8/§7.4.1~8/§7.5.1~8) 완성, ConfigChangeLog 통합. |
| v4.1 | 2026-05-28 | 이기호 | DeviceGroup 단건 CRUD(§5.6.1~8), AuditLog 연계. NATS SYNC_DEVICE_GROUP. |
| v4.0 | 2026-05-15 | 이기호 | RESTful 전면 재구성: §5 Device/Group, §6 NATS 매트릭스, §7 EventMapping. envelope 표준 v2 적용. |
| v3.x | ~2026-04 | 이기호 | NATS Event 정책 v1.3 정합, 외부 인증 라인 정리. (이전 차수 명세서 본문 변경 이력 참조) |

---

## §12 부록

### 12.1 시뮬레이션 raw 데이터

- 경로: `c:\workspace_python\api-test-server\docs\sim\raw_data.json`
- 시나리오 수: 19
- ConfigChangeLog 캡처: 30건
- 마지막 갱신: 2026-06-18
- 회귀 슈트 매핑: §9.3

### 12.2 9-Agent 검증 결과

- 경로: `c:\workspace_python\api-test-server\docs\workflow_audit_v3\`
- 디렉터리: `a01/` ~ `a09/`
- 산출물 구성: 각 agent별 `findings.md` + `evidence.json` + `cross_check.md`
- 14건 GAP 합의 도출: `a09/consensus.md`

### 12.3 마스터 명세서

- 경로: `c:\workspace_python\api-test-server\GOP_Restful_Api_연동설계.md`
- 현행 버전: v4.3 (커밋 `7aced94`)
- 정정 대상 절: §5.6.9 / §7.3.9 / §7.3.10 / §7.4.9 / §7.4.10 / §7.5.9 / §7.5.10
- 사본 5곳 혼동 금지 (마스터는 git 추적본만)

### 12.4 관련 PRD

| 문서 | 버전 | 위치 | 관계 |
|------|------|------|------|
| PRD_DeviceGroup_BulkUnassign | v1.0 | `c:\workspace_python\api-test-server\docs\prd\` | §5.6.9 원천 PRD |
| PRD_EventMapping_BulkOperations | v1.0 | `c:\workspace_python\api-test-server\docs\prd\` | §7.3/4/5.9~10 원천 PRD |
| PRD_BulkAPI_Spec_Sync_v4.4 | v0.1 (본 문서) | `c:\workspace_python\api-test-server\docs\prd\` | 명세 ↔ 구현 정합화 |

### 12.5 §7.5.7 번호 중복 (사후 정정 권고)

- 현상: v4.3 본문에 §7.5.7이 두 번 등장 (단건 PUT + 별도 보조 절).
- 영향: 목차 자동생성 시 anchor 충돌 가능.
- 권고: v4.4 정정 PR과 별개 후속 차수에서 절 번호 재배열 (§7.5.7 → §7.5.7-a, §7.5.8 등으로 재조정).
- 우선순위: P3 (본 차수 범위 외).

### 12.6 용어 사전

| 용어 | 정의 | 출처 코드 |
|------|------|----------|
| `config_id` | EventMapping bulk DELETE path/요청에 쓰이는 **매핑 row PK** (`event_mapping_cameras/speakers/lamps.id`). 디바이스 PK 아님. | `app/api/v1/endpoints/event_mapping_cameras.py` |
| `mapping row PK` | EventMapping 테이블의 surrogate PK. `config_id`와 동의어. | DB 스키마 v2.7 |
| `camera_id` / `speaker_id` / `lamp_id` | 디바이스 테이블 FK. EventMapping 본문에서 매핑 대상 디바이스 지정용. | Request Body 필드 |
| `created_ids` | bulk POST 응답에서 신규 매핑 row PK 배열. 입력 echo 아님. | `services/event_mapping_*_service.py` |
| `skipped_config_ids` | bulk DELETE 응답에서 이미 해제되어 스킵된 매핑 PK 배열. v4.3 현재 항상 `[]` (PR-A 후 분류). | 동상 |
| `not_found_config_ids` | bulk DELETE 응답에서 존재하지 않는 매핑 PK 배열. v4.3 현재 항상 `[]` (PR-A 후 분류). | 동상 |
| `EnumConfigResourceType` | ConfigChangeLog `resource_type` enum. `event_mapping_cameras/speakers/lamps` 포함. | `models/config_change_log.py` |
| `EnumLampColor` | Lamp `color` 컬럼 Postgres enum. `Red/Green/Blue/Yellow/Cyan/Magenta/White`. v4.3 현재 Pydantic은 plain `str` (PR-C 후 Enum 검증). | DB 스키마 v2.7 |
| `trg_sync_eml_ins` / `trg_sync_eml_del` | EventMapping Lamp INSERT/DELETE 트리거. NATS `SYNC_EVENT_MAPPING` cmd 발행. v4.3 본문 `trg_sync_eml_insert/delete` 오기재 → v4.4 정정. | `db_triggers.py:435-440` |
| `cmd='SYNC_EVENT_MAPPING'` / `action='UPDATED'` | NATS 발행 시 실제 사용되는 단일 payload 식별자. bulk_created/bulk_deleted 분리 발행 아님. | `db_triggers.py` |
| `data.message` | 200 응답 본문의 user-facing 메시지 위치. `meta.message` 아님. | 응답 envelope v2 |
| `meta` (envelope) | request_id/timestamp 등 메타데이터. 200 success 응답엔 일부(Cam/Spk/Lamp) 부재, 422/404 응답엔 항상 포함. v4.4 envelope 비대칭으로 명시. | 미들웨어 `app/middleware/envelope.py` |

---

