# PRD: EventMapping Bulk Create / Bulk Unassign Endpoints (Cameras / Speakers / Lamps)

**문서 버전**: v1.0
**작성일**: 2026-06-17
**참조 PRD**: `docs/PRD_DeviceGroup_BulkUnassign.md`, `docs/PRD_CameraEventMapping_Refactoring.md`, `docs/PRD_EventMappingSpeaker.md`, `docs/PRD_Lamp_Device.md`
**상태**: Draft
**유형**: 신규 기능 추가 (Additive — Non-breaking)

---

## 1. 개요

### 1.1 한 줄 결론

**EventMapping 3종(cameras/speakers/lamps)은 현재 등록(POST)·해제(DELETE) 모두 단건만 제공하여 다중선택 시 N회 호출이 발생하는 비대칭/비효율을 해소하기 위해, 3종 동일 패턴의 `POST .../{collection}/bulk` 벌크 등록 + `DELETE .../{collection}` 벌크 해제 엔드포인트를 신설한다.**

### 1.2 목적

| 항목 | 내용 |
|------|------|
| 비효율 해소 | 등록 N건·해제 N건 → 등록 1회·해제 1회 (양방향 동시 벌크화) |
| DeviceGroup 대칭 | DeviceGroup이 `POST /devices`(벌크)+`DELETE /devices`(벌크 추가 예정)와 동일 패턴 정렬 |
| 네트워크 폭주 차단 | UI 다중선택 시 N회 호출 → 1회 호출 |
| NATS 발행 폭주 차단 | row-level 트리거 N건 → statement-level 1건/`event_mapping_id` (트리거 마이그레이션 동반) |
| 감사 로그 가독성 | `UNASSIGNED`/`CREATED` 로그 N줄 → 1줄 (`config_ids` 리스트로 응축) |

### 1.3 배경

- 인벤토리 확인 결과 3종 라우터 모두 **단건 POST(`/{mapping_id}/cameras` 등) + 단건 DELETE(`/{mapping_id}/cameras/{config_id}` 등)**만 존재 (`app/routers/event_mapping_cameras.py:183-260, 436-492` / `event_mapping_speakers.py:160-227, 348-403` / `event_mapping_lamps.py:158-218, 341-396`).
- DeviceGroupMapping의 벌크 할당(`POST /api/devices/groups/{id}/devices`)은 이미 검증됨. 벌크 해제는 본 시점 PRD_DeviceGroup_BulkUnassign에서 동시 진행 중.
- Central UI는 이벤트 매핑 마법사에서 카메라/스피커/경광등을 다중선택하므로 단건 N회 호출은 직접적 UX 병목.
- 3종 트리거 모두 `FOR EACH ROW`(`app/db_triggers.py:211-227`) → 벌크 시 N건 `SYNC_EVENT_MAPPING/UPDATED` 발화. db_monitor 1:1 전달이므로 NATS 메시지 폭증.
- `device_group_mappings`는 이미 statement-level 트리거 마이그레이션이 완료(`db_triggers.py:228-281`)되어 동일 패턴 차용 가능.

---

## 2. 요구사항

### 2.1 기능 요구사항

| ID | 요구사항 | 우선순위 |
|----|---------|---------|
| FR-1 | 단일 HTTP 호출로 한 EventMapping에 N개 Camera 연동을 일괄 생성할 수 있어야 함 | Must |
| FR-2 | 단일 HTTP 호출로 한 EventMapping에 N개 Speaker 연동을 일괄 생성할 수 있어야 함 | Must |
| FR-3 | 단일 HTTP 호출로 한 EventMapping에 N개 Lamp 연동을 일괄 생성할 수 있어야 함 | Must |
| FR-4 | 단일 HTTP 호출로 한 EventMapping에서 N개 연동(config_id 기준)을 일괄 해제할 수 있어야 함 (3종 각각) | Must |
| FR-5 | per-row 부가 필드 보존 — Camera는 `target_preset_id/home_preset_id/delay_time/priority`, Speaker는 `file_group_id/repeat_count/priority`, Lamp는 `color/buzzer_time/buzzer_sound/light_mode/priority` | Must |
| FR-6 | 부분 성공 허용 — 벌크 등록은 `created_ids` / `failed_items`, 벌크 해제는 `removed_config_ids` / `skipped_config_ids` / `not_found_config_ids` | Must |
| FR-7 | 멱등성 보장 (벌크 해제) — 동일 요청 재호출 시 두 번째는 `skipped_config_ids`로 분류 | Must |
| FR-8 | EventMapping 부재 시 404 (등록/해제 공통) | Must |
| FR-9 | 빈 배열 / 최대 초과 시 422 (Pydantic `min_length=1`, `max_length=100`) | Must |
| FR-10 | 기존 단건 POST/DELETE 엔드포인트 유지 (deprecate 안 함) | Must |
| FR-11 | ConfigChangeLog 1건/요청 발행 — 벌크 등록: `EVENT_MAPPING_CAMERA/SPEAKER/LAMP` + `CREATED` (`after_state.config_ids`), 벌크 해제: 동일 resource_type + `DELETED` (`before_state.config_ids`) | Must |
| FR-12 | AuditLog 발행 정책은 DeviceGroup_BulkUnassign과 동일 (SUCCESS/FAILURE 모두). 단, 본 PRD 범위에선 EventMapping은 ConfigChangeLog만 필수로 강제하고 AuditLog는 Should | Should |

### 2.2 비기능 요구사항

| ID | 항목 | 목표 |
|----|------|------|
| NFR-1 | 성능 — 50개 일괄 등록/해제 응답 시간 | 단건 50회 합산의 1/10 이하 |
| NFR-2 | DB 트랜잭션 | 단일 `db.commit()` 1회 (원자성) |
| NFR-3 | NATS `SYNC_EVENT_MAPPING/UPDATED/{event_mapping_id}` 발행 건수 | **1건/`event_mapping_id`** (statement-level 트리거 패치 전제) |
| NFR-4 | 호환성 — 기존 단건 POST/DELETE | 시그니처/응답 envelope 완전 보존 |
| NFR-5 | OpenAPI SemVer | MINOR (additive only) |
| NFR-6 | 최대 처리 건수 | items / config_ids 최대 100개 |

---

## 3. API 명세

### 3.1 엔드포인트 (3종 공통 — `{sub}` ∈ `cameras` / `speakers` / `lamps`)

| 작업 | Method | Path | operation_id |
|------|--------|------|-------------|
| 벌크 등록 | `POST` | `/api/integrations/event-mappings/{mapping_id}/{sub}/bulk` | `bulk_create_event_mapping_{sub}` |
| 벌크 해제 | `DELETE` | `/api/integrations/event-mappings/{mapping_id}/{sub}` | `bulk_unassign_event_mapping_{sub}` |

**메서드/경로 선택 근거**:
- 벌크 등록은 body 구조가 단건(`<Sub>Create`)과 다르고(`List[<Sub>Create]`), Swagger 분리 명확성을 위해 `/bulk` action sub-resource 사용 (DeviceGroup 인벤토리 권장안).
- 벌크 해제는 컬렉션 DELETE + body(`config_ids: List[int]`) — DeviceGroupMapping `DELETE /{group_id}/devices`와 완전 동일 패턴.

### 3.2 인증/태그/공통

| 항목 | 값 |
|------|-----|
| 인증 | 각 라우터 현 정책 일치 (Camera/Speaker/Lamp 라우터 동일 dependency) |
| Tag | `Event Mapping Cameras` / `Event Mapping Speakers` / `Event Mapping Lamps` |
| 응답 envelope | `ApiSingleResponse[...]` |

### 3.3 Request (벌크 등록) — Camera 예시

**Headers**:
```http
Authorization: Bearer <token>
Content-Type: application/json
Accept: application/json
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `mapping_id` | integer | Y | EventMapping ID |

**Request Body**:
```json
{
  "items": [
    {
      "camera_id": 11,
      "target_preset_id": 101,
      "home_preset_id": 102,
      "delay_time": 5,
      "is_enable": true,
      "priority": 1
    },
    {
      "camera_id": 12,
      "delay_time": 0,
      "is_enable": true
    }
  ]
}
```

| 필드 | 타입 | 필수 | 제약 | 설명 |
|------|------|------|------|------|
| `items` | array[`EventMappingCameraCreate`] | Y | 1 ≤ len ≤ 100 | 일괄 생성할 Camera 연동 리스트 (단건 스키마 재사용) |

> **Speaker 차이**: `items: List[EventMappingSpeakerCreate]` (`speaker_id`, `file_group_id?`, `repeat_count`, `is_enable`, `priority?`)
> **Lamp 차이**: `items: List[EventMappingLampCreate]` (`lamp_id`, `color`, `buzzer_time`, `buzzer_sound`, `light_mode`, `is_enable`, `priority`)

### 3.4 Response (벌크 등록, 200 OK)

```json
{
  "success": true,
  "message": "2개 Camera 연동 생성 완료, 0개 실패",
  "data": {
    "mapping_id": 7,
    "created_ids": [301, 302],
    "failed_items": [],
    "message": "2개 Camera 연동 생성 완료, 0개 실패"
  },
  "meta": {
    "timestamp": "2026-06-17T10:40:00.000Z",
    "request_id": "550e8408-e29b-41d4-a716-446655440000"
  }
}
```

> **응답 시맨틱 (벌크 등록)**:
> - `created_ids`: 실제로 생성된 config row PK 목록 (요청 items 순서 보존)
> - `failed_items`: `{index: int, item: <Sub>Create, error: str}` — FK 무효(예: 존재하지 않는 camera_id) 등 row-level 실패. 전체 실패해도 HTTP 200 (부분 성공 시맨틱)

### 3.5 Request (벌크 해제) — 3종 공통

```json
{
  "config_ids": [301, 302, 303, 999]
}
```

| 필드 | 타입 | 필수 | 제약 | 설명 |
|------|------|------|------|------|
| `config_ids` | array[integer] | Y | 1 ≤ len ≤ 100 | 해제할 연동 row PK 목록 (중복 자동 제거) |

### 3.6 Response (벌크 해제, 200 OK)

```json
{
  "success": true,
  "message": "2개 Camera 연동 해제 완료, 1개 건너뜀, 1개 없음",
  "data": {
    "mapping_id": 7,
    "removed_config_ids": [301, 302],
    "skipped_config_ids": [303],
    "not_found_config_ids": [999],
    "message": "2개 Camera 연동 해제 완료, 1개 건너뜀, 1개 없음"
  },
  "meta": { "timestamp": "...", "request_id": "..." }
}
```

> **응답 시맨틱 (벌크 해제)**:
> - `removed_config_ids`: 실제 삭제된 연동 row PK
> - `skipped_config_ids`: row는 DB에 존재하나 해당 `mapping_id`에 속하지 않음 (멱등 — 다른 매핑에 속한 row를 잘못 호출했을 때)
> - `not_found_config_ids`: row가 DB에 존재하지 않음
> - 전부 skipped/not_found여도 HTTP 200

### 3.7 에러 응답 표 (3종 공통)

| HTTP | Code | 조건 | 발생 시점 |
|------|------|------|----------|
| 200 | — | 일괄 등록/해제 성공 (부분 성공 포함) | 정상 |
| 404 | `NOT_FOUND` | EventMapping `mapping_id` 부재 | 매핑 검증 단계 |
| 422 | `VALIDATION_ERROR` | `items`/`config_ids` 누락·빈 배열·최대 초과·Pydantic 검증 실패 | Pydantic |
| 500 | `INTERNAL_ERROR` | DB 오류 등 | 트랜잭션 단계 |

---

## 4. 데이터 모델 / DTO

### 4.1 신규 스키마 — `app/schemas/integration.py`

| 클래스 | 역할 | 인접 위치 |
|--------|------|---------|
| `EventMappingCameraBulkCreateRequest` | Camera 벌크 등록 body | `EventMappingCameraCreate`(L138) 이후 |
| `EventMappingCameraBulkCreateResponse` | Camera 벌크 등록 응답 | `EventMappingCameraResponse`(L170) 이후 |
| `EventMappingCameraBulkUnassignRequest` | Camera 벌크 해제 body | 위 동일 |
| `EventMappingCameraBulkUnassignResponse` | Camera 벌크 해제 응답 | 위 동일 |
| (동일 4종 × Speaker × Lamp) | | `EventMappingSpeakerCreate`(L223), `EventMappingLampCreate`(L375) 인접 |

### 4.2 `<Sub>BulkCreateRequest` (3종 공통 시그니처)

| 필드 | 타입 | 제약 | 설명 |
|------|------|------|------|
| `items` | `List[<Sub>Create]` | `min_length=1`, `max_length=100` | 단건 Create 스키마 재사용 |

`field_validator`로 빈 배열 거부.

### 4.3 `<Sub>BulkCreateResponse`

| 필드 | 타입 | 기본 | 설명 |
|------|------|------|------|
| `mapping_id` | `int` | (필수) | EventMapping ID |
| `created_ids` | `List[int]` | `[]` | 생성된 config row PK |
| `failed_items` | `List[<Sub>BulkCreateFailure]` | `[]` | 실패 row 상세 |
| `message` | `str` | (필수) | 결과 요약 |

`<Sub>BulkCreateFailure`:
| 필드 | 타입 | 설명 |
|------|------|------|
| `index` | `int` | 요청 items 내 0-based 인덱스 |
| `item` | `<Sub>Create` | 원본 입력 |
| `error` | `str` | 실패 사유 (예: "Camera 11 not found") |

### 4.4 `<Sub>BulkUnassignRequest`

| 필드 | 타입 | 제약 | 설명 |
|------|------|------|------|
| `config_ids` | `List[int]` | `min_length=1`, `max_length=100` | 해제할 row PK 목록 |

### 4.5 `<Sub>BulkUnassignResponse`

| 필드 | 타입 | 기본 | 설명 |
|------|------|------|------|
| `mapping_id` | `int` | (필수) | EventMapping ID |
| `removed_config_ids` | `List[int]` | `[]` | 실제 삭제된 row PK |
| `skipped_config_ids` | `List[int]` | `[]` | row는 존재하나 mapping_id 불일치(=멱등) |
| `not_found_config_ids` | `List[int]` | `[]` | row 자체 부재 |
| `message` | `str` | (필수) | 결과 요약 |

### 4.6 스키마 재사용 vs 분리 결정

| 옵션 | 결정 |
|------|------|
| 단건 `<Sub>Create` 재사용 (items에 그대로) | **채택** — 필드 정합성 보장, 단건/벌크 동시 진화 시 동기화 자동 |
| `device_ids: List[int]` 류 단순 ID 리스트 | **비채택** — Camera는 `target_preset_id/delay_time` 등 per-row 부가 필드 필수, Speaker는 `file_group_id/repeat_count`, Lamp는 `color/buzzer_time/buzzer_sound/light_mode` 필수. 단순 ID 리스트로 표현 불가 |
| 벌크 해제 시 `config_ids: List[int]` (단순 ID) | **채택** — 해제는 PK만으로 충분, DeviceGroup `device_ids` 패턴과 완전 일치 |

---

## 5. NATS SYNC 발행 정책

### 5.1 현재 동작 (트리거 row-level)

`app/db_triggers.py:211-227`의 3개 트리거(`trg_sync_event_mapping_cameras`, `_speakers`, `_lamps`)는 모두 **FOR EACH ROW** + `fn_notify_gop_sync` → `SYNC_EVENT_MAPPING/UPDATED/{event_mapping_id}` 발화. 벌크 INSERT/DELETE N건 → **N건 발행**. db_monitor 1:1 전달.

### 5.2 옵션 비교 (DeviceGroup_BulkUnassign §5.2와 동일 프레임)

| 항목 | A. db_monitor 디바운싱 | B. 라우터 명시 NOTIFY + 트리거 비활성 | **C. statement-level 트리거 (권장)** | D. SET LOCAL 세션 변수로 트리거 억제 |
|------|----------------------|--------------------------------------|------------------------------------|---------------------------------|
| 폭주 해소 | O (100~300ms 윈도우) | O | **O (자연 1건/event_mapping_id)** | O (조건부) |
| CASCADE/수동 SQL 보호 | O | X | **O (모든 경로)** | △ |
| 라우터 누락 회귀 위험 | 무 | **고** | 무 | 중 |
| 상태 관리 | stateful (큐) | stateless | **stateless** | stateless |
| 등록/해제 자동 수혜 | O | X (수동) | **O** | X |
| 롤백 안전성 | 코드 revert | 라우터 1곳 누락 시 동기 깨짐 | 마이그레이션 revert | 코드+SQL revert |
| PostgreSQL 버전 요구 | 무 | 무 | PG10+ (REFERENCING NEW/OLD TABLE) | 무 |

### 5.3 권장안 — 옵션 C (statement-level 트리거, 3종 동시 마이그레이션)

**1건 발행 보장 메커니즘**:
- `AFTER INSERT/UPDATE/DELETE ON event_mapping_cameras FOR EACH STATEMENT` + `REFERENCING NEW TABLE / OLD TABLE`
- `SELECT DISTINCT event_mapping_id FROM (new|old)_rows`로 영향 받은 매핑 수만큼만 `pg_notify` 발화
- 단일 매핑 벌크 INSERT 50건 → `SYNC_EVENT_MAPPING/UPDATED/{event_mapping_id}` **1건**
- 다중 `event_mapping_id`가 한 statement에 섞이면 매핑 수만큼 정확히 발행
- **3종 모두 동일 패턴 적용** (cameras/speakers/lamps)

**비채택 사유**:
- B/D: 라우터 누락 회귀 위험 + CASCADE 미보호
- A 단독: 자연 시맨틱(트랜잭션 1건 = 통지 1건)을 표현 못 함

### 5.4 트리거 패치 범위

| 테이블 | 범위 |
|--------|------|
| `event_mapping_cameras` | 본 PRD 패치 |
| `event_mapping_speakers` | 본 PRD 패치 |
| `event_mapping_lamps` | 본 PRD 패치 |
| `device_group_mappings` | 별도 PRD (PRD_DeviceGroup_BulkUnassign §5.4) — 이미 statement-level 완료 |

### 5.5 SQLite 환경

`apply_triggers` (`db_triggers.py:295`)가 dialect 체크로 SQLite를 skip 처리하므로 **테스트 환경 무영향**. PostgreSQL 운영 환경만 마이그레이션 적용.

---

## 6. ConfigChangeLog / AuditLog 정책

### 6.1 옵션 비교 (벌크 등록 / 벌크 해제 공통)

| 항목 | A. N건 발행 | **B. 1건 + 리스트 (권장)** | C. `CREATED_BATCH` / `UNASSIGNED_BATCH` 신규 enum |
|------|-----------|-------------------------|-------------------------------|
| 단건/벌크 대칭 | X (1 vs N) | **O (1 vs 1)** | X (다른 액션) |
| DB 부하 | N INSERT | **1 INSERT** | 1 INSERT |
| UI 가독성 | N줄 노이즈 | **1줄 응축** | 1줄, 필터 신규 |
| Enum 오염 | 무 | **무** | enum 추가 |
| 단건 API 변경 필요 | — | **불필요** | 단건도 BATCH 분기? |

### 6.2 권장안 — 옵션 B (DeviceGroup_BulkUnassign과 동일 정책)

**ConfigChangeLog 페이로드 (벌크 등록 — Camera 예시)**:
```python
log_config_change(
    db=db,
    resource_type=EnumConfigResourceType.EVENT_MAPPING_CAMERA,
    resource_id=mapping_id,
    resource_name=f"EventMapping-{mapping_id} cameras (bulk)",
    action=EnumConfigActionType.CREATED,
    after_state={"config_ids": created_ids, "count": len(created_ids)},
    description=f"EventMapping에 {len(created_ids)}개 Camera 연동 일괄 생성 (bulk)",
)
```

**ConfigChangeLog 페이로드 (벌크 해제 — Camera 예시)**:
```python
log_config_change(
    db=db,
    resource_type=EnumConfigResourceType.EVENT_MAPPING_CAMERA,
    resource_id=mapping_id,
    resource_name=f"EventMapping-{mapping_id} cameras (bulk)",
    action=EnumConfigActionType.DELETED,
    before_state={"config_ids": removed_config_ids, "count": len(removed_config_ids)},
    description=f"EventMapping에서 {len(removed_config_ids)}개 Camera 연동 일괄 해제 (bulk)",
)
```

**Speaker / Lamp**: `EVENT_MAPPING_SPEAKER` / `EVENT_MAPPING_LAMP` resource_type만 교체 (Enum 인벤토리 확인 결과 v3.2부터 3종 모두 존재).

### 6.3 발행 조건

| 시나리오 | ConfigChangeLog | AuditLog (Should) |
|---------|-----------------|---------|
| 벌크 등록 `created` ≥ 1건 | 발행 (1건, `CREATED`) | 발행 (SUCCESS) |
| 벌크 등록 전체 실패 (created=0) | **미발행** | 발행 (SUCCESS, description에 failure 카운트) |
| 벌크 해제 `removed` ≥ 1건 | 발행 (1건, `DELETED`) | 발행 (SUCCESS) |
| 벌크 해제 전부 skipped/not_found | **미발행** | 발행 (SUCCESS, description에 skip 카운트) |
| 매핑 404 | 미발행 | 발행 (FAILURE) |
| 422 검증 실패 | 미발행 | (Pydantic 단계 — 글로벌 핸들러 필요 시 별도 결재) |

### 6.4 단건 API 정합성 (별도 Tidy First 커밋 권장)

현재 단건 POST/DELETE는 row당 1건 ConfigChangeLog 발행. 차기 구조 커밋에서 `after_state.config_ids: [id]` / `before_state.config_ids: [id]`(복수) + `count: 1`로 통일하면 단건/벌크 동일 스키마로 응축 가능. **본 PRD 범위 외**.

---

## 7. 사이드이펙트 분석

### 7.1 라우터

| 파일 | 영향 | 조치 |
|------|------|------|
| `app/routers/event_mapping_cameras.py` | 단건 POST/PATCH/PUT/DELETE 시그니처 **불변** | 보존. 벌크 2개 핸들러 추가 (단건 POST 위에 bulk POST, 단건 DELETE 위에 bulk DELETE) |
| `app/routers/event_mapping_speakers.py` | 동일 | 동일 |
| `app/routers/event_mapping_lamps.py` | 동일 | 동일 |
| `_resolve_*` 헬퍼 부재 | 등록·해제 검증 로직 3중 중복 위험 | 후속 Tidy First 커밋으로 `services/event_mapping_bulk_service.py` 추출 검토 |
| 라우트 등록 순서 | `/{config_id}` int 파싱과 정적 `/bulk` 충돌 가능 | `/bulk` 핸들러를 `/{config_id}` 핸들러보다 **위에** 등록 |

### 7.2 트리거 (`app/db_triggers.py`)

| 영역 | 영향 | 조치 |
|------|------|------|
| `trg_sync_event_mapping_cameras` row-level (L211-215) | statement-level INSERT/UPDATE/DELETE 트리거 3개로 분리 | `fn_notify_emc_stmt` 신설 + DROP IF EXISTS + 재생성 |
| `trg_sync_event_mapping_speakers` row-level (L217-221) | 동일 | `fn_notify_ems_stmt` |
| `trg_sync_event_mapping_lamps` row-level (L223-227) | 동일 | `fn_notify_eml_stmt` |
| `device_group_mappings` 트리거 패턴 | 검증된 레퍼런스 (L228-281) | 차용 — `DISTINCT group_id` → `DISTINCT event_mapping_id`로 치환 |
| `EnumConfigActionType.CREATED/DELETED` 재사용 | 단건/벌크 구분은 `description`의 `(bulk)` 토큰으로 표시 | enum 확장 안 함 |

### 7.3 테스트

| 파일 | 영향 |
|------|------|
| `tests/test_event_mapping_camera_router.py` (29) | 중간 — 단건 POST/DELETE 회귀 검증 |
| `tests/test_event_mapping_camera_model.py`, `_schema.py`, `_integration.py` | 중간 — 신규 스키마 케이스 보강 |
| `tests/test_event_mapping_speaker_router.py` (34) | 중간 — 회귀 검증 |
| `tests/test_event_mapping_speaker_model.py`, `_schema.py` | 중간 — 스키마 케이스 보강 |
| `tests/test_event_mapping_lamp_router.py` (32) | 중간 — 회귀 검증 |
| `tests/test_event_mapping_lamp_model.py`, `_schema.py` | 중간 — 스키마 케이스 보강 |
| 신규 `tests/test_event_mapping_camera_bulk.py` | 신설 — 8+종 케이스 |
| 신규 `tests/test_event_mapping_speaker_bulk.py` | 신설 — 8+종 케이스 |
| 신규 `tests/test_event_mapping_lamp_bulk.py` | 신설 — 8+종 케이스 |

### 7.4 명세서 (`GOP_Restful_Api_연동설계.md` v4.3)

| 영역 | 변경 |
|------|------|
| §12.1 부록 표 | Cameras/Speakers/Lamps 도메인별 일괄 등록·해제 2행씩 총 6행 추가 |
| §7.3 / §7.4 / §7.5 본문 | 본 PRD에서는 부록 표 위주 갱신, 상세 §x.x 신설은 후속 단계 (라우터 안정화 후) |
| 변경 이력 v4.3 | EventMapping 벌크 등록·해제 항목 추가 |

### 7.5 OpenAPI / 클라이언트

| 영역 | 영향 | 조치 |
|------|------|------|
| SemVer | additive → MINOR | `main.py:286` version bump |
| operation_id 충돌 | `generate_unique_id_function=lambda r: r.name` → 함수명 고유 필수 | `bulk_create_event_mapping_cameras` 등 6개 명명 |
| OpenAPI examples | response_model + responses(200/404/422) 모두 필수 | 기존 라우터 패턴 준수 |
| CORS | wildcard 허용 | 무변경 |
| 에러 envelope | 글로벌 `http_exception_handler` 표준화 | 그대로 |

### 7.6 타 매니저 (간접 영향)

| 매니저 | 영향 | 비고 |
|--------|------|------|
| DBApi | 직접 (구현) | 본 PRD 책임 |
| Central UI | 직접 (UI 신설) | 매핑 마법사 다중선택 일괄 등록/해제 UX |
| db_monitor | 무영향 | 트리거 statement-level 변경 후에도 1:1 publish 동일 |
| GIS | 간접 | `SYNC_EVENT_MAPPING` 수신 후 캐시 무효화 (기존 메커니즘) |
| VMS / NVRManager | 간접 | 카메라 연동 캐시 무효화 (기존) |
| BroadcastEngine (Speaker) | 간접 | 스피커 연동 캐시 무효화 (기존) |
| LampManager | 간접 | 경광등 연동 캐시 무효화 (기존) |

---

## 8. 호환성

### 8.1 기존 단건 API 유지 정책

| 항목 | 결정 |
|------|------|
| `POST /{mapping_id}/cameras` 단건 시그니처 | **완전 보존** (Speaker/Lamp 동일) |
| `DELETE /{mapping_id}/cameras/{config_id}` 단건 시그니처 | **완전 보존** (Speaker/Lamp 동일) |
| 단건 응답 envelope | **완전 보존** |
| Deprecation 마킹 (`deprecated=True`) | **본 PRD 범위 외** — 운영 안정화 후 별도 결재 |
| OpenAPI Swagger UI 노출 | 단건/벌크 양쪽 표시 |

### 8.2 호환성 매트릭스

| 클라이언트 패턴 | 영향 |
|---------------|------|
| 기존 단건 POST/DELETE 호출 | 변화 없음 |
| 신규 벌크 POST/DELETE 호출 | 정상 동작 |
| 단건 + 벌크 혼용 | 정상 동작 (멱등 보장) |

---

## 9. 변경 파일 목록

| 파일 (절대경로) | 영역 | 변경 유형 |
|---------------|------|----------|
| `c:\workspace_python\api-test-server\app\schemas\integration.py` | L138~187 (Camera), L223~327 (Speaker), L375~446 (Lamp) | 추가 — 3종 × 4개 Bulk 스키마 (총 12개) |
| `c:\workspace_python\api-test-server\app\routers\event_mapping_cameras.py` | L16~30 import, L183 직전 (bulk POST), L436 직전 (bulk DELETE) | 추가 — 신규 스키마 import + 핸들러 2개 |
| `c:\workspace_python\api-test-server\app\routers\event_mapping_speakers.py` | L16~30 import, L160 직전, L348 직전 | 추가 — 핸들러 2개 |
| `c:\workspace_python\api-test-server\app\routers\event_mapping_lamps.py` | L16~30 import, L158 직전, L341 직전 | 추가 — 핸들러 2개 |
| `c:\workspace_python\api-test-server\app\db_triggers.py` | L211~227 | 수정 — statement-level 트리거 3종으로 교체 + DROP IF EXISTS + `fn_notify_emc_stmt/ems_stmt/eml_stmt` 신설 |
| `c:\workspace_python\api-test-server\app\main.py` | L286 (version) | 수정 — MINOR bump |
| `c:\workspace_python\api-test-server\tests\test_event_mapping_camera_bulk.py` | 신규 파일 | 추가 — 8+종 |
| `c:\workspace_python\api-test-server\tests\test_event_mapping_speaker_bulk.py` | 신규 파일 | 추가 — 8+종 |
| `c:\workspace_python\api-test-server\tests\test_event_mapping_lamp_bulk.py` | 신규 파일 | 추가 — 8+종 |
| `c:\workspace_python\api-test-server\tests\test_event_mapping_camera_schema.py` | 신규 케이스 영역 | 추가 — Bulk 스키마 검증 케이스 |
| `c:\workspace_python\api-test-server\tests\test_event_mapping_speaker_schema.py` | 동일 | 추가 |
| `c:\workspace_python\api-test-server\tests\test_event_mapping_lamp_schema.py` | 동일 | 추가 |
| `e:\01.사업관련자료\20.통제UI정리\Docs\GOP_Restful_Api_연동설계.md` | §12.1 Cameras/Speakers/Lamps 블록 | 갱신 — 6행 추가 |
| `e:\01.사업관련자료\20.통제UI정리\Docs\GOP_Restful_Api_연동설계.md` | 변경 이력 v4.3 행 | 갱신 — 벌크 항목 누적 |

**신규 추가 파일**: 3개 라우터 테스트 + 3개 스키마 테스트 추가 영역 (트리거 마이그레이션은 `db_triggers.py` 수정)
**무변경 확인**: `app/main.py` 라우터 prefix, CORS, 글로벌 에러 핸들러

---

## 10. 테스트 계획

### 10.1 신규 테스트 — Camera 벌크 (`tests/test_event_mapping_camera_bulk.py`)

| # | 케이스 (`should_X_when_Y`) | 분류 | 검증 포인트 |
|---|---------------------------|------|-----------|
| 1 | `should_create_all_cameras_when_items_are_valid` | happy | 200, `created_ids=[A,B,C]`, `failed_items=[]` |
| 2 | `should_partially_create_when_some_camera_ids_not_found` | 부분 | 200, `created_ids=[A]`, `failed_items` 1건 (error 메시지 포함) |
| 3 | `should_return_404_when_mapping_not_found` | 매핑부재 | 404, `detail.success=false` |
| 4 | `should_return_422_when_items_is_empty` | 검증 | 422, Pydantic `min_length=1` |
| 5 | `should_return_422_when_items_exceeds_max` | 검증 | 422, 101개 입력 |
| 6 | `should_unassign_all_configs_when_all_belong_to_mapping` | happy | 200, `removed_config_ids=[A,B,C]`, 나머지 [] |
| 7 | `should_partial_unassign_when_some_belong_to_other_mapping` | 부분 | 200, `removed=[A]`, `skipped=[B]` |
| 8 | `should_classify_into_not_found_when_config_id_absent` | not_found | 200, `not_found_config_ids=[99999]` |
| 9 | `should_be_idempotent_when_config_ids_have_duplicates` | 멱등 | 1회: removed, 2회: skipped/not_found |
| 10 | `should_log_config_change_with_count_when_bulk_created` | 로깅 | `action=CREATED`, `after_state.count=N` |
| 11 | `should_log_config_change_with_count_when_bulk_unassigned` | 로깅 | `action=DELETED`, `before_state.count=N` |

### 10.2 신규 테스트 — Speaker 벌크 (`tests/test_event_mapping_speaker_bulk.py`)

> Camera 테스트와 동일 11종 + Speaker 고유 검증:

| # | 추가 케이스 | 검증 |
|---|------------|------|
| 12 | `should_preserve_file_group_id_when_bulk_created` | per-row 부가 필드 보존 |
| 13 | `should_preserve_repeat_count_when_bulk_created` | per-row 부가 필드 보존 |

### 10.3 신규 테스트 — Lamp 벌크 (`tests/test_event_mapping_lamp_bulk.py`)

> Camera 테스트와 동일 11종 + Lamp 고유 검증:

| # | 추가 케이스 | 검증 |
|---|------------|------|
| 12 | `should_preserve_color_and_buzzer_when_bulk_created` | per-row Enum 필드 보존 |
| 13 | `should_preserve_light_mode_when_bulk_created` | per-row Enum 필드 보존 |

### 10.4 트리거 테스트

| # | 케이스 | 검증 |
|---|--------|------|
| T-1 | `should_publish_one_sync_event_mapping_when_bulk_insert_n_cameras` | statement-level → 1건/`event_mapping_id` |
| T-2 | `should_publish_one_sync_event_mapping_when_bulk_delete_n_cameras` | 동일, DELETE 측 |
| T-3 | `should_publish_distinct_sync_per_mapping_when_cascade_delete_mapping` | DISTINCT event_mapping_id loop |
| T-4 | `should_publish_one_sync_when_bulk_speakers` | Speaker 측 동일 보장 |
| T-5 | `should_publish_one_sync_when_bulk_lamps` | Lamp 측 동일 보장 |

### 10.5 기존 회귀 검증

| 파일 | 회귀 항목 |
|------|----------|
| `test_event_mapping_camera_router.py` (29) | 단건 POST/PATCH/PUT/DELETE 응답 envelope 보존 |
| `test_event_mapping_speaker_router.py` (34) | 단건 동일 |
| `test_event_mapping_lamp_router.py` (32) | 단건 동일 |
| 3종 model/schema/integration 테스트 | 단건 시그니처 무회귀 |
| 전체 합계 95+ 케이스 | 회귀 0건 목표 |

### 10.6 conftest fixture 재사용

| Fixture | 활용 |
|---------|------|
| `client`, `test_db` | 그대로 |
| 기존 `test_event_mapping`, `test_camera`, `test_speaker`, `test_lamp`, `test_camera_preset`, `test_file_group` | 그대로 |
| 신규(선택) `test_event_mapping_with_n_cameras` | 벌크 해제 시드 |

---

## 11. 명세 v4.3 패치

### 11.1 §12.1 부록 표 갱신 (위치: L14538/L14546/L14554 다음)

기존 3개 도메인 블록에 각각 일괄 등록·해제 2행씩 추가:

```markdown
**Event Mapping Cameras** (v2.4 신규):
- ... 기존 6행 ...
- `POST /api/integrations/event-mappings/{mapping_id}/cameras/bulk` - 카메라 연동 일괄 생성 *(v4.3 추가)*
- `DELETE /api/integrations/event-mappings/{mapping_id}/cameras` - 카메라 연동 일괄 해제 *(v4.3 추가)*

**Event Mapping Speakers** (v2.8 신규):
- ... 기존 6행 ...
- `POST /api/integrations/event-mappings/{mapping_id}/speakers/bulk` - 스피커 연동 일괄 생성 *(v4.3 추가)*
- `DELETE /api/integrations/event-mappings/{mapping_id}/speakers` - 스피커 연동 일괄 해제 *(v4.3 추가)*

**Event Mapping Lamps** (v3.4 신규):
- ... 기존 6행 ...
- `POST /api/integrations/event-mappings/{mapping_id}/lamps/bulk` - 경광등 연동 일괄 생성 *(v4.3 추가)*
- `DELETE /api/integrations/event-mappings/{mapping_id}/lamps` - 경광등 연동 일괄 해제 *(v4.3 추가)*
```

### 11.2 v4.3 Changelog (PRD_DeviceGroup_BulkUnassign과 같은 행에 누적)

```markdown
- EventMapping 3종(Cameras/Speakers/Lamps) 벌크 등록·해제 엔드포인트 신설 — POST .../{collection}/bulk + DELETE .../{collection}
- statement-level 트리거 마이그레이션으로 SYNC_EVENT_MAPPING 1건/event_mapping_id 발행 보장
```

---

## 12. 작업 공수 / 일정

| Phase | 항목 | 공수 |
|-------|------|------|
| Phase 1 | 신규 스키마 12개 (3종 × 4개) + 단위 테스트 | 0.5일 |
| Phase 2 | 라우터 핸들러 6개 (3종 × 2개) + ConfigChangeLog 발행 | 0.7일 |
| Phase 3 | 트리거 statement-level 마이그레이션 (3종) + 트리거 테스트 5건 | 0.5일 |
| Phase 4 | 신규 라우터 테스트 30+종 + 회귀 검증 | 0.7일 |
| Phase 5 | 명세서 §12.1 + 변경 이력 갱신 | 0.1일 |
| Phase 6 | OpenAPI version bump + Swagger 검증 | 0.1일 |
| **합계** | 백엔드만 (Central UI 별도) | **2.6일** |

---

## 13. 리스크 및 완화책

| # | 리스크 | 발생 가능성 | 영향 | 완화책 |
|---|--------|-----------|------|-------|
| R-1 | statement-level 트리거 PG 버전 미지원 | 낮 | 고 | 운영 PG10+ 사전 확인 (DeviceGroup 마이그레이션에서 이미 검증). 미지원 시 옵션 A(디바운싱) 임시 채택 |
| R-2 | 트리거 교체 중 NATS SYNC 미발화 | 중 | 중 | 마이그레이션 트랜잭션 내 DROP+CREATE 단일 실행. 직후 smoke test |
| R-3 | 기존 단건 POST/DELETE 응답 envelope 변경 사고 | 낮 | 고 | 3종 router 회귀 테스트 95+ 케이스 게이트 |
| R-4 | `/bulk` 라우트와 `/{config_id}` int 파싱 충돌 | 중 | 중 | bulk 핸들러를 단건 핸들러보다 **위에** 등록, 라우트 등록 순서 테스트 추가 |
| R-5 | 벌크 등록 시 부분 실패에 대한 트랜잭션 정책 모호 | 중 | 중 | "all-or-nothing" vs "best-effort" 결재 필요. 본 PRD는 **best-effort** 채택 (`failed_items` 분리 반환, 성공한 것만 commit) |
| R-6 | `EnumConfigActionType.CREATED/DELETED` 단일값 재사용으로 단건/벌크 구분 모호 | 낮 | 저 | description `(bulk)` 토큰 + after_state/before_state의 `count` 필드로 구분 |
| R-7 | UI에서 100개 초과 요청 시 422 | 중 | 저 | 클라이언트 측 chunking 가이드 명세에 명시 |
| R-8 | 다중 `event_mapping_id`가 한 statement에 섞일 때 트리거 누락 | 낮 | 중 | `SELECT DISTINCT event_mapping_id FROM (new\|old)_rows` 루프로 보장 (DeviceGroup 패턴 검증됨) |
| R-9 | operation_id 충돌 (`bulk_create_event_mapping_cameras` 등 6개) | 낮 | 저 | PR 전 `grep "^async def " app/routers/event_mapping_*.py` |
| R-10 | 단건 POST/DELETE는 row당 ConfigChangeLog 1건 발행 — 벌크와 스키마 불일치 | 중 | 저 | 차기 Tidy First 커밋으로 단건도 `config_ids: [id]` + `count: 1`로 통일 |

---

## 14. 롤백 계획

| 단계 | 절차 |
|------|------|
| 1. 라우터 롤백 | 3개 라우터의 신규 bulk 핸들러 6개 제거 — git revert |
| 2. 스키마 롤백 | `app/schemas/integration.py` 신규 Bulk 스키마 12개 제거 |
| 3. 트리거 롤백 | 마이그레이션 down — statement-level 트리거 3종 DROP + row-level 트리거 3종 재생성 |
| 4. version 롤백 | `main.py` MINOR bump revert |
| 5. 명세서 롤백 | §12.1 6행 + 변경 이력 누적 항목 revert |
| 6. 테스트 롤백 | `test_event_mapping_*_bulk.py` 3개 + schema 추가 케이스 삭제 |
| 7. 검증 | 단건 POST/DELETE 회귀 95+ 케이스 통과 확인 |

**롤백 안전성**: additive-only 변경이므로 단순 revert로 완전 복구 가능. 트리거만 마이그레이션 별도 필요.

---

## 15. 부록 — 신규 라우터 핸들러 스케치 (Camera 예시)

### 15.1 스키마 (`app/schemas/integration.py`, Camera 영역)

```python
class EventMappingCameraBulkCreateRequest(BaseModel):
    """카메라 연동 벌크 생성 요청"""
    items: List[EventMappingCameraCreate] = Field(
        ..., min_length=1, max_length=100,
        description="일괄 생성할 Camera 연동 리스트 (1~100)"
    )


class EventMappingCameraBulkCreateFailure(BaseModel):
    index: int = Field(..., description="요청 items 내 0-based 인덱스")
    item: EventMappingCameraCreate
    error: str


class EventMappingCameraBulkCreateResponse(BaseModel):
    """카메라 연동 벌크 생성 응답"""
    mapping_id: int
    created_ids: List[int] = Field(default_factory=list)
    failed_items: List[EventMappingCameraBulkCreateFailure] = Field(default_factory=list)
    message: str


class EventMappingCameraBulkUnassignRequest(BaseModel):
    """카메라 연동 벌크 해제 요청"""
    config_ids: List[int] = Field(
        ..., min_length=1, max_length=100,
        description="해제할 연동 row PK 목록 (1~100)"
    )

    @field_validator('config_ids')
    @classmethod
    def validate_config_ids(cls, v):
        if not v:
            raise ValueError('config_ids must not be empty')
        return v


class EventMappingCameraBulkUnassignResponse(BaseModel):
    """카메라 연동 벌크 해제 응답"""
    mapping_id: int
    removed_config_ids: List[int] = Field(default_factory=list)
    skipped_config_ids: List[int] = Field(default_factory=list)
    not_found_config_ids: List[int] = Field(default_factory=list)
    message: str
```

> **Speaker / Lamp**: 동일 패턴으로 `items: List[EventMappingSpeakerCreate]` / `items: List[EventMappingLampCreate]`로 치환.

### 15.2 라우터 핸들러 — 벌크 등록 (`app/routers/event_mapping_cameras.py`, 단건 POST 위에 배치)

```python
@router.post(
    "/{mapping_id}/cameras/bulk",
    response_model=ApiSingleResponse[EventMappingCameraBulkCreateResponse],
    responses={
        200: {"description": "벌크 등록 성공 (부분 성공 포함)"},
        404: {"description": "EventMapping not found"},
        422: {"description": "items 검증 실패"},
    },
)
async def bulk_create_event_mapping_cameras(
    mapping_id: int,
    request: EventMappingCameraBulkCreateRequest,
    db: Session = Depends(get_db),
):
    """카메라 연동 벌크 생성 (한 매핑에 N개 연동 일괄 등록)"""
    mapping = db.query(EventMapping).filter(EventMapping.id == mapping_id).first()
    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False,
                    "message": f"EventMapping with id {mapping_id} not found"},
        )

    created_ids: list[int] = []
    failed_items: list[EventMappingCameraBulkCreateFailure] = []
    created_rows: list[EventMappingCamera] = []

    for idx, item in enumerate(request.items):
        # Camera 존재 검증
        camera = db.query(Camera).filter(Camera.id == item.camera_id).first()
        if not camera:
            failed_items.append(EventMappingCameraBulkCreateFailure(
                index=idx, item=item, error=f"Camera {item.camera_id} not found"
            ))
            continue
        # (target_preset_id / home_preset_id 검증 동일 패턴)

        row = EventMappingCamera(
            event_mapping_id=mapping_id,
            camera_id=item.camera_id,
            target_preset_id=item.target_preset_id,
            home_preset_id=item.home_preset_id,
            delay_time=item.delay_time,
            is_enable=item.is_enable,
            priority=item.priority,
        )
        db.add(row)
        created_rows.append(row)

    db.flush()  # PK 채번
    for row in created_rows:
        created_ids.append(row.id)

    db.commit()  # 단일 commit

    if created_ids:
        log_config_change(
            db=db,
            resource_type=EnumConfigResourceType.EVENT_MAPPING_CAMERA,
            resource_id=mapping_id,
            resource_name=f"EventMapping-{mapping_id} cameras (bulk)",
            action=EnumConfigActionType.CREATED,
            after_state={"config_ids": created_ids, "count": len(created_ids)},
            description=f"EventMapping에 {len(created_ids)}개 Camera 연동 일괄 생성 (bulk)",
        )

    parts = [f"{len(created_ids)}개 Camera 연동 생성 완료"]
    if failed_items:
        parts.append(f"{len(failed_items)}개 실패")
    message = ", ".join(parts)

    return ApiSingleResponse(
        success=True,
        data=EventMappingCameraBulkCreateResponse(
            mapping_id=mapping_id,
            created_ids=created_ids,
            failed_items=failed_items,
            message=message,
        ),
        message=message,
    )
```

### 15.3 라우터 핸들러 — 벌크 해제 (단건 DELETE 위에 배치)

```python
@router.delete(
    "/{mapping_id}/cameras",
    response_model=ApiSingleResponse[EventMappingCameraBulkUnassignResponse],
    responses={
        200: {"description": "벌크 해제 성공 (부분 성공 포함)"},
        404: {"description": "EventMapping not found"},
        422: {"description": "config_ids 검증 실패"},
    },
)
async def bulk_unassign_event_mapping_cameras(
    mapping_id: int,
    request: EventMappingCameraBulkUnassignRequest,
    db: Session = Depends(get_db),
):
    """카메라 연동 벌크 해제 (한 매핑에서 N개 연동 일괄 삭제)"""
    mapping = db.query(EventMapping).filter(EventMapping.id == mapping_id).first()
    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False,
                    "message": f"EventMapping with id {mapping_id} not found"},
        )

    # 중복 ID 제거 (멱등성)
    unique_ids = list(dict.fromkeys(request.config_ids))

    removed: list[int] = []
    skipped: list[int] = []
    not_found: list[int] = []

    for config_id in unique_ids:
        row = db.query(EventMappingCamera).filter(
            EventMappingCamera.id == config_id
        ).first()
        if not row:
            not_found.append(config_id)
            continue
        if row.event_mapping_id != mapping_id:
            skipped.append(config_id)
            continue
        db.delete(row)
        removed.append(config_id)

    db.commit()  # 단일 commit

    if removed:
        log_config_change(
            db=db,
            resource_type=EnumConfigResourceType.EVENT_MAPPING_CAMERA,
            resource_id=mapping_id,
            resource_name=f"EventMapping-{mapping_id} cameras (bulk)",
            action=EnumConfigActionType.DELETED,
            before_state={"config_ids": removed, "count": len(removed)},
            description=f"EventMapping에서 {len(removed)}개 Camera 연동 일괄 해제 (bulk)",
        )

    parts = [f"{len(removed)}개 Camera 연동 해제 완료"]
    if skipped:
        parts.append(f"{len(skipped)}개 건너뜀")
    if not_found:
        parts.append(f"{len(not_found)}개 없음")
    message = ", ".join(parts)

    return ApiSingleResponse(
        success=True,
        data=EventMappingCameraBulkUnassignResponse(
            mapping_id=mapping_id,
            removed_config_ids=removed,
            skipped_config_ids=skipped,
            not_found_config_ids=not_found,
            message=message,
        ),
        message=message,
    )
```

### 15.4 트리거 패치 (`app/db_triggers.py`, Camera 예시 — Speaker/Lamp 동일 패턴)

```sql
-- DROP 기존 row-level 트리거 (3종 모두 동일 패턴)
DROP TRIGGER IF EXISTS trg_sync_event_mapping_cameras ON event_mapping_cameras;

-- 신규 statement-level 함수
CREATE OR REPLACE FUNCTION fn_notify_emc_stmt()
RETURNS trigger AS $$
DECLARE r RECORD;
BEGIN
    IF TG_OP IN ('INSERT', 'UPDATE') THEN
        FOR r IN SELECT DISTINCT event_mapping_id FROM new_rows LOOP
            PERFORM pg_notify('gop_sync', jsonb_build_object(
                'cmd','SYNC_EVENT_MAPPING','action','UPDATED','resource_id',r.event_mapping_id
            )::text);
        END LOOP;
    END IF;
    IF TG_OP IN ('UPDATE', 'DELETE') THEN
        FOR r IN SELECT DISTINCT event_mapping_id FROM old_rows LOOP
            PERFORM pg_notify('gop_sync', jsonb_build_object(
                'cmd','SYNC_EVENT_MAPPING','action','UPDATED','resource_id',r.event_mapping_id
            )::text);
        END LOOP;
    END IF;
    RETURN NULL;
END $$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sync_emc_ins
  AFTER INSERT ON event_mapping_cameras
  REFERENCING NEW TABLE AS new_rows
  FOR EACH STATEMENT EXECUTE FUNCTION fn_notify_emc_stmt();

CREATE TRIGGER trg_sync_emc_upd
  AFTER UPDATE ON event_mapping_cameras
  REFERENCING NEW TABLE AS new_rows OLD TABLE AS old_rows
  FOR EACH STATEMENT EXECUTE FUNCTION fn_notify_emc_stmt();

CREATE TRIGGER trg_sync_emc_del
  AFTER DELETE ON event_mapping_cameras
  REFERENCING OLD TABLE AS old_rows
  FOR EACH STATEMENT EXECUTE FUNCTION fn_notify_emc_stmt();

-- Speaker / Lamp는 위 패턴에서 테이블명/함수명만 치환 (ems_stmt / eml_stmt)
```

---

## 16. 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| v1.0 | 2026-06-17 | 초안 — EventMapping 3종(Cameras/Speakers/Lamps) 벌크 등록 + 벌크 해제 엔드포인트 신설, statement-level 트리거 + ConfigChangeLog 1건 정책. PRD_DeviceGroup_BulkUnassign과 동일 패턴 차용 |

---

**문서 끝**
