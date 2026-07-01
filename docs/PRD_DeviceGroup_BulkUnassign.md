# PRD: DeviceGroup Bulk Unassign Endpoint

**문서 버전**: v1.0
**작성일**: 2026-06-17
**참조 PRD**: `docs/PRD_DeviceGroup_Assign_Fix.md`, `docs/PRD_Device_Structure_Refactoring.md`
**상태**: Draft
**유형**: 신규 기능 추가 (Additive — Non-breaking)

---

## 1. 개요

### 1.1 한 줄 결론

**디바이스 그룹 할당(POST)은 N건을 1회 호출로 처리하나 해제는 단건 DELETE만 존재하는 성능 비대칭을 해소하기 위해, `DELETE /api/devices/groups/{id}/devices` 벌크 해제 엔드포인트를 신설한다.**

### 1.2 목적

| 항목 | 내용 |
|------|------|
| 비대칭 해소 | 할당(`POST /devices`) vs 해제(`DELETE /devices/{device_id}` 단건만) → 양방향 동등 처리 |
| 네트워크 폭주 차단 | UI에서 다중선택 후 N회 호출 → 1회 호출 |
| NATS 발행 폭주 차단 | row-level 트리거 N건 → statement-level 1건/그룹 (별도 트리거 패치) |
| 감사 로그 가독성 | UNASSIGNED 로그 N줄 → 1줄(`before_state.device_ids: [...]`) |

### 1.3 배경

- 현재 `app/routers/device_groups.py:737`의 단건 `DELETE /{group_id}/devices/{device_id}`만 존재
- 동일 라우터의 `POST /{group_id}/devices`(L655)는 이미 `device_ids: List[int]` 벌크 패턴
- Central UI에서 50개 디바이스 일괄 해제 시 50회 HTTP 호출 + 50회 `SYNC_DEVICE_GROUP` NATS 발행 발생
- GIS/VMS 동기화 지연 및 통제UI 응답성 저하 보고 누적

---

## 2. 요구사항

### 2.1 기능 요구사항

| ID | 요구사항 | 우선순위 |
|----|---------|---------|
| FR-1 | 단일 HTTP 호출로 N개 디바이스를 그룹에서 해제할 수 있어야 함 | Must |
| FR-2 | 폴리모픽 디바이스(Controller/Sensor/Camera/Speaker/Enclosure/Lamp) 모두 지원 | Must |
| FR-3 | 부분 성공 허용 — `removed_device_ids` / `skipped_device_ids` / `not_found_device_ids` 분리 응답 | Must |
| FR-4 | 멱등성 보장 — 동일 요청 재호출 시 두 번째는 `skipped_device_ids`로 분류 | Must |
| FR-5 | 그룹 부재 시 404 | Must |
| FR-6 | 빈 배열(`device_ids: []`) 요청 시 422 (Pydantic `min_length=1`) | Must |
| FR-7 | 기존 단건 DELETE 엔드포인트 유지(deprecate 시점 별도 결재) | Must |
| FR-8 | ConfigChangeLog UNASSIGNED 1건 발행 (`before_state.device_ids` + `categories`) | Must |
| FR-9 | AuditLog `DEVICE_GROUP_UNASSIGN` 발행 (SUCCESS/FAILURE 모두) | Should |

### 2.2 비기능 요구사항

| ID | 항목 | 목표 |
|----|------|------|
| NFR-1 | 성능 — 50개 일괄 해제 응답 시간 | 단건 50회 합산의 1/10 이하 |
| NFR-2 | DB 트랜잭션 | 단일 `db.commit()` 1회 (원자성) |
| NFR-3 | NATS `SYNC_DEVICE_GROUP` 발행 건수 | **1건/그룹** (statement-level 트리거 패치 전제) |
| NFR-4 | 호환성 — 기존 단건 DELETE | 시그니처/응답 envelope 완전 보존 |
| NFR-5 | OpenAPI SemVer | MINOR (1.5.0 → 1.6.0) — additive only |
| NFR-6 | 최대 처리 건수 | `device_ids` 최대 100개 |

---

## 3. API 명세

### 3.1 엔드포인트

| 항목 | 값 |
|------|-----|
| Method | `DELETE` |
| Path | `/api/devices/groups/{id}/devices` |
| 인증 | `get_current_user_optional` (기존 라우터 정책 일치) |
| Tag | `DeviceGroups` |
| operation_id | `bulk_unassign_devices_from_group` |

### 3.2 Request

**Headers**:
```http
Authorization: Bearer <token>
Content-Type: application/json
Accept: application/json
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `id` | integer | Y | DeviceGroup ID |

**Request Body**:
```json
{
  "device_ids": [1, 101, 201, 301]
}
```

| 필드 | 타입 | 필수 | 제약 | 설명 |
|------|------|------|------|------|
| `device_ids` | array[integer] | Y | 1 ≤ len ≤ 100 | 해제할 디바이스 ID 목록 |

### 3.3 Response (200 OK)

```json
{
  "success": true,
  "message": "2개 디바이스 해제 완료, 1개 건너뜀, 1개 없음",
  "data": {
    "group_id": 1,
    "removed_device_ids": [1, 101],
    "skipped_device_ids": [201],
    "not_found_device_ids": [999],
    "message": "2개 디바이스 해제 완료, 1개 건너뜀, 1개 없음"
  },
  "meta": {
    "timestamp": "2026-06-17T10:40:00.000Z",
    "request_id": "550e8408-e29b-41d4-a716-446655440000"
  }
}
```

### 3.4 에러 응답 표

| HTTP | Code | 조건 | 발생 시점 |
|------|------|------|----------|
| 200 | — | 일괄 해제 성공(부분 성공 포함) | 정상 |
| 404 | `NOT_FOUND` | DeviceGroup `id` 부재 | 그룹 검증 단계 |
| 422 | `VALIDATION_ERROR` | `device_ids` 누락/빈 배열/최대 초과 | Pydantic 검증 |
| 500 | `INTERNAL_ERROR` | DB 오류 등 | 트랜잭션 단계 |

**404 예시**:
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "DeviceGroup with id 999 not found",
    "details": null
  },
  "meta": { "timestamp": "...", "request_id": "..." }
}
```

---

## 4. 데이터 모델 / DTO

### 4.1 신규 스키마 (`app/schemas/device_group.py`)

| 클래스 | 역할 | 위치 |
|--------|------|------|
| `DeviceUnassignRequest` | 요청 바디 | `DeviceAssignRequest`(L350) 인접 |
| `DeviceBulkRemoveResponse` | 응답 바디 (`ApiSingleResponse.data`) | `DeviceRemoveResponse`(L387) 인접 |

### 4.2 `DeviceUnassignRequest`

| 필드 | 타입 | 제약 | 설명 |
|------|------|------|------|
| `device_ids` | `List[int]` | `min_length=1`, `max_length=100` | 해제할 디바이스 ID 목록 |

`field_validator`로 빈 배열 거부.

### 4.3 `DeviceBulkRemoveResponse`

| 필드 | 타입 | 기본 | 설명 |
|------|------|------|------|
| `group_id` | `int` | (필수) | 그룹 ID |
| `removed_device_ids` | `List[int]` | `[]` | 실제 매핑 삭제된 ID |
| `skipped_device_ids` | `List[int]` | `[]` | device는 존재하나 그룹 멤버 아님(=멱등) |
| `not_found_device_ids` | `List[int]` | `[]` | device 자체 부재 |
| `message` | `str` | (필수) | 결과 요약 메시지 |

### 4.4 스키마 재사용 vs 분리 결정

| 옵션 | 결정 |
|------|------|
| `DeviceAssignRequest` 재사용 | 비채택 — OpenAPI 의도 명확화 위해 별도 정의 |
| `DeviceRemoveResponse`(단건) 확장 | 비채택 — 단건은 `device_id`(단수), 벌크는 `*_device_ids`(복수)로 키 구조가 다름 |

---

## 5. NATS SYNC 발행 정책

### 5.1 현재 동작 (트리거 row-level)

`app/db_triggers.py:109-119, 229-233`의 `trg_sync_device_group_mappings`는 **FOR EACH ROW** + `action=UPDATED` 하드코딩. 벌크 DELETE N건 → `SYNC_DEVICE_GROUP/UPDATED/{group_id}` **N건 발행**. db_monitor에는 dedup 없음(1:1 전달).

### 5.2 옵션 비교

| 항목 | A. db_monitor 디바운싱 | B. 라우터 명시 NOTIFY + 트리거 비활성 | **C. statement-level 트리거 (권장)** | D. SET LOCAL 세션 변수로 트리거 억제 |
|------|----------------------|--------------------------------------|------------------------------------|---------------------------------|
| 폭주 해소 | O (100~300ms 윈도우) | O (라우터 직접 1건) | **O (자연 1건/group)** | O (라우터에서 SET LOCAL 시) |
| CASCADE/수동 SQL 보호 | O (모든 경로) | X | **O (모든 경로)** | △ (SET LOCAL 안 한 경로 폭주) |
| 라우터 누락 회귀 위험 | 무 | **고** | 무 | 중 |
| 상태 관리 | stateful (큐) | stateless | **stateless** | stateless |
| 등록 API 자동 수혜 | O | X (수동) | **O** | X (수동) |
| 롤백 안전성 | 코드 revert | 라우터 1곳 누락 시 동기 깨짐 | 마이그레이션 revert | 코드+SQL revert |
| PostgreSQL 버전 요구 | 무 | 무 | PG10+ (REFERENCING NEW/OLD TABLE) | 무 |

### 5.3 권장안 — 옵션 C (statement-level 트리거)

**1건 발행 보장 메커니즘**:
- `AFTER INSERT/DELETE ON device_group_mappings FOR EACH STATEMENT` + `REFERENCING NEW TABLE / OLD TABLE`
- `SELECT DISTINCT group_id FROM (new|old)_rows`로 영향 받은 group 수만큼만 `pg_notify` 발화
- 단일 그룹 벌크 DELETE 50건 → `SYNC_DEVICE_GROUP/UPDATED/{group_id}` **1건**
- 다중 그룹이 한 statement에 섞이면 그룹 수만큼 정확히 발행

**보조안**: 운영 1주 실측 후 폭주 잔존 시 옵션 A를 db_monitor 측에 추가 도입.

**비채택 사유**:
- B/D: 라우터 누락 회귀 위험 + CASCADE 미보호
- A 단독: 자연 시맨틱(트랜잭션 1건 = 통지 1건)을 표현 못 함

### 5.4 트리거 패치 범위

| 테이블 | 범위 |
|--------|------|
| `device_group_mappings` | 본 PRD 패치 대상 |
| `event_mapping_cameras/_speakers/_lamps` | 별도 PRD (동일 패턴 잠재 적용 — 본 PRD 범위 외) |

---

## 6. ConfigChangeLog / AuditLog 정책

### 6.1 옵션 비교

| 항목 | A. N건 발행 | **B. 1건 + 리스트 (권장)** | C. `UNASSIGNED_BATCH` 신규 enum |
|------|-----------|-------------------------|-------------------------------|
| 등록(ASSIGNED) 대칭 | X (1 vs N) | **O (1 vs 1)** | X (다른 액션) |
| DB 부하 | 50 INSERT | **1 INSERT** | 1 INSERT |
| UI 가독성 | 50줄 노이즈 | **1줄 응축** | 1줄, 필터 신규 |
| Enum 오염 | 무 | **무** | `UNASSIGNED_BATCH` 추가 |
| 등록 API 변경 필요 | 등록도 N건화 | **불필요** | 등록도 BATCH 추가? |

### 6.2 권장안 — 옵션 B

**ConfigChangeLog 페이로드**:
```python
log_config_change(
    db=db,
    resource_type=EnumConfigResourceType.DEVICE_GROUP,
    resource_id=group_id,
    resource_name=f"DeviceGroup-{group_id} ({group.name})",
    action=EnumConfigActionType.UNASSIGNED,
    before_state={
        "device_ids": removed,
        "categories": removed_categories  # {device_id: category_device.value}
    },
    description=f"DeviceGroup에서 {len(removed)}개 디바이스 해제 (bulk)"
)
```

| 측면 | 등록(ASSIGNED) | 해제(UNASSIGNED) | 대칭 |
|------|---------------|-----------------|------|
| 변화 방향 | `None → after_state` | `before_state → None` | O |
| 키 이름 | `device_ids`, `categories` | `device_ids`, `categories` | O (동일) |
| 건수 | 1건/요청 | 1건/요청 | O |

### 6.3 발행 조건

| 시나리오 | ConfigChangeLog | AuditLog |
|---------|-----------------|---------|
| `removed` ≥ 1건 | 발행 (1건) | 발행 (SUCCESS) |
| 전부 skipped/not_found (removed=0) | **미발행** | 발행 (SUCCESS, description에 skip 카운트) |
| 그룹 404 | 미발행 | 발행 (FAILURE) |
| 422 검증 실패 | 미발행 | 발행 (FAILURE) |

### 6.4 단건 DELETE 키 통일 (별도 Tidy First 커밋 권장)

현재 단건 DELETE는 `before_state.device_id`(단수). 차기 구조 커밋에서 `before_state.device_ids: [id]`(복수) + `categories: {id: cat}`로 통일 → 모든 UNASSIGNED 로그 동일 스키마.

---

## 7. 사이드이펙트 분석

### 7.1 라우터 (`app/routers/device_groups.py`)

| 영역 | 영향 | 조치 |
|------|------|------|
| 단건 DELETE 핸들러 | 시그니처/응답 envelope **불변** | 보존 |
| `_resolve_category_for_device()` 헬퍼 부재 | 등록·단건·신규 벌크에 동일 패턴 3중 중복 | 후속 Tidy First 커밋 (`services/device_group_service.py` 추출) |
| 라우트 등록 순서 | `/devices/{device_id}` int 파싱 강제 → 정적 path 충돌 없음 | 신규 함수는 단건 핸들러 위에 배치(가독성) |

### 7.2 트리거 (`app/db_triggers.py`)

| 영역 | 영향 | 조치 |
|------|------|------|
| `device_group_mappings` row-level 트리거 1개 | statement-level INSERT/DELETE 트리거 2개로 분리 | DROP IF EXISTS + 재생성 마이그레이션 |
| `devices` CASCADE | 자동 statement-level 적용 → 자연 dedup | 검증 케이스 추가 |
| `EnumConfigActionType.UNASSIGNED` | 단건/벌크 구분은 `description`의 `(bulk)` 토큰으로 표시 | enum 확장 안 함 |

### 7.3 테스트 (9개 device_group 테스트 파일, 총 112 케이스)

| 파일 | 영향 |
|------|------|
| `test_device_group_router.py` (15) | 중간 — Remove 시리즈 회귀 검증 |
| `test_device_group_assign_fix.py` (18) | 중간 — Remove ConfigChangeLog 키 정책 검증 |
| `test_device_group_include_devices.py` (3) | 무 |
| `test_device_group_lamp.py` (17) | 무 |
| `test_device_group_mapping_enum.py` (3) | 무 (단, Enum 일관성 검증) |
| `test_device_group_model.py` (11) | 무 |
| `test_device_group_schema.py` (17) | 중간 — 신규 스키마 케이스 보강 |
| `test_device_group_support.py` (25) | 무 |
| `test_device_groups_camera_urls.py` (3) | 무 |
| 신규 `test_device_group_unassign_bulk.py` | 신설 — 6+종 케이스 |

### 7.4 명세서 (`GOP_Restful_Api_연동설계.md` v4.3)

| 영역 | 변경 |
|------|------|
| §5.6.9 (신설) | 라인 5585(`§5.6.8` 종료) 와 라인 5587(`§5.7`) 사이 삽입 |
| §12.1 부록 표 | L14404 다음 줄에 `DELETE /api/devices/groups/{id}/devices` 추가 |

### 7.5 OpenAPI / 클라이언트

| 영역 | 영향 | 조치 |
|------|------|------|
| SemVer | additive → MINOR | `main.py:286` version "1.5.0" → "1.6.0", description "API Version: 2.9" → "2.10" |
| operation_id 충돌 | `generate_unique_id_function=lambda r: r.name` → 함수명 고유 필수 | `bulk_unassign_devices_from_group` 명명 |
| OpenAPI examples | response_model + responses(200/404/422) 모두 필수 | 기존 device_groups.py 패턴 준수 |
| CORS | wildcard 허용 → 자동 통과 | 무변경 |
| 에러 envelope | 글로벌 `http_exception_handler` 표준화 | `raise HTTPException` 그대로 |

### 7.6 타 매니저 (간접 영향)

| 매니저 | 영향 | 비고 |
|--------|------|------|
| DBApi | 직접 (구현) | 본 PRD 책임 |
| Central UI | 직접 (UI 신설) | 다중선택 일괄 해제 UX |
| db_monitor | 무영향 | 트리거 statement-level 변경 후에도 1:1 publish 동일 |
| GIS | 간접 | NATS SYNC_DEVICE_GROUP 수신 후 폴리곤/POI 캐시 무효화 (기존 메커니즘) |
| VMS / NVRManager | 간접 | 카메라 그룹 매핑 변동 캐시 무효화 (기존 메커니즘) |
| PidsProxy | 무영향 | — |

---

## 8. 호환성

### 8.1 기존 단건 DELETE 유지 정책

| 항목 | 결정 |
|------|------|
| `DELETE /api/devices/groups/{group_id}/devices/{device_id}` 시그니처 | **완전 보존** |
| 응답 envelope (`data.device_id`, `data.message`) | **완전 보존** |
| `ConfigChangeLog.before_state.device_id`(단수) | 보존 (Tidy First 커밋에서 복수형 통일 별도 진행) |
| Deprecation 마킹 (`deprecated=True`) | **본 PRD 범위 외** — 차장 결재 후 별도 커밋 |
| OpenAPI Swagger UI 노출 | 단건/벌크 양쪽 표시 |

### 8.2 호환성 매트릭스

| 클라이언트 패턴 | 영향 |
|---------------|------|
| 기존 단건 DELETE 호출 | 변화 없음 |
| 신규 벌크 DELETE 호출 | 정상 동작 |
| 동일 디바이스 단건 + 벌크 혼용 | 정상 동작 (멱등) |

---

## 9. 변경 파일 목록

| 파일 (절대경로) | 라인 | 변경 유형 |
|---------------|------|----------|
| `c:\workspace_python\api-test-server\app\schemas\device_group.py` | L350~395 영역 | 추가 — `DeviceUnassignRequest`, `DeviceBulkRemoveResponse` |
| `c:\workspace_python\api-test-server\app\routers\device_groups.py` | L16~30 import | 추가 — 신규 스키마 import |
| `c:\workspace_python\api-test-server\app\routers\device_groups.py` | L737 직전 | 핸들러 추가 — `bulk_unassign_devices_from_group` |
| `c:\workspace_python\api-test-server\app\db_triggers.py` | L109~119, L229~233 | 수정 — statement-level 트리거로 교체 + DROP IF EXISTS |
| `c:\workspace_python\api-test-server\app\main.py` | L286 (version), L283 (description) | 수정 — 1.5.0 → 1.6.0, "API Version: 2.10" |
| `c:\workspace_python\api-test-server\tests\test_device_group_unassign_bulk.py` | 신규 파일 | 추가 — 6+종 케이스 |
| `c:\workspace_python\api-test-server\tests\test_device_group_schema.py` | 신규 케이스 영역 | 추가 — 스키마 검증 케이스 |
| `e:\01.사업관련자료\20.통제UI정리\Docs\GOP_Restful_Api_연동설계.md` | L5585 직후 | 추가 — §5.6.9 신설 |
| `e:\01.사업관련자료\20.통제UI정리\Docs\GOP_Restful_Api_연동설계.md` | L14404 다음 | 추가 — 부록 §12.1 표 갱신 |

**신규 추가 파일**: 2개 (테스트 1, 트리거 마이그레이션은 `db_triggers.py` 수정)
**무변경 확인**: `app/main.py` 라우터 prefix, CORS, 글로벌 에러 핸들러

---

## 10. 테스트 계획

### 10.1 신규 테스트 (`tests/test_device_group_unassign_bulk.py`)

| # | 케이스 (`should_X_when_Y`) | 분류 | 검증 포인트 |
|---|---------------------------|------|-----------|
| 1 | `should_unassign_all_devices_when_all_are_members` | happy | 200, `removed_device_ids=[A,B,C]`, 나머지 [] |
| 2 | `should_partial_unassign_when_some_are_not_members` | 부분 | 200, `removed=[A]`, `skipped=[B]` |
| 3 | `should_classify_into_not_found_when_device_id_absent` | not_found | 200, `not_found_device_ids=[99999]` |
| 4 | `should_return_404_when_group_not_found` | 그룹부재 | 404, `detail.success=false` |
| 5 | `should_return_422_when_device_ids_is_empty` | 검증 | 422, Pydantic `min_length=1` |
| 6 | `should_be_idempotent_when_device_ids_have_duplicates` | 멱등 | 1회: removed, 2회: skipped |
| 7 | `should_log_config_change_with_categories_when_unassigned` | 로깅 | `action=UNASSIGNED`, `before_state.categories` 존재 |
| 8 | `should_unassign_mixed_device_types_polymorphically` | 폴리모픽 | Controller+Sensor+Camera 동시 해제 |

### 10.2 트리거 테스트

| # | 케이스 | 검증 |
|---|--------|------|
| T-1 | `should_publish_one_sync_device_group_when_bulk_remove_n_devices` | statement-level → 1건/group |
| T-2 | `should_publish_distinct_sync_per_group_when_cascade_delete_device_in_multiple_groups` | DISTINCT group_id loop 검증 |
| T-3 | `should_publish_one_sync_device_group_when_bulk_assign_n_devices` | 등록 측 자동 수혜 검증 |

### 10.3 기존 회귀 검증

| 파일 | 회귀 항목 |
|------|----------|
| `test_device_group_router.py::test_remove_device_from_group` | 단건 응답 envelope `data.device_id` 보존 |
| `test_device_group_assign_fix.py::TestRemoveSensor/Camera/Speaker*` (7건) | 단건 폴리모픽 동작 보존 |
| `test_device_group_assign_fix.py::TestRemoveConfigChangeLog` | `before_state.category_device`(단수) 보존 |
| `test_device_group_mapping_enum.py` (3건) | Enum 매핑 일관성 |
| 전체 112 케이스 | 회귀 0건 목표 |

### 10.4 conftest fixture 재사용

| Fixture | 활용 |
|---------|------|
| `client`, `test_db` | 그대로 |
| `test_controller/sensor/camera/speaker/lamp/enclosure` | 폴리모픽 시드 |
| 신규(선택) `test_device_group_with_members` | 6 케이스 중복 setup 제거 |

---

## 11. 명세 v4.3 패치

### 11.1 §5.6.9 신설 (위치: L5585 직후)

| 항목 | 값 |
|------|-----|
| 제목 | `#### 5.6.9 디바이스 그룹에서 디바이스 일괄 제거 (v4.3 신규)` |
| Endpoint | `DELETE /api/devices/groups/{id}/devices` |
| Path Param | `id: integer (Y)` |
| Body | `{"device_ids": [...]}` (1~100) |
| Response 키 | `removed_device_ids` / `skipped_device_ids` / `not_found_device_ids` |
| 에러 코드 표 | 200 / 404(NOT_FOUND) / 422(VALIDATION_ERROR) / 500 |

### 11.2 §12.1 부록 표 갱신 (위치: L14404 다음 줄)

기존 `DELETE /api/devices/groups/{group_id}/devices/{device_id}` 뒤에 한 줄 추가:
```markdown
- `DELETE /api/devices/groups/{group_id}/devices/{device_id}` - 디바이스 제거 (단건)
- `DELETE /api/devices/groups/{id}/devices` - 디바이스 일괄 제거 *(v4.3 추가)*
```

### 11.3 v4.3 Changelog

```markdown
- §5.6.9 신설 — POST 할당과 대칭되는 벌크 해제 엔드포인트 추가
```

---

## 12. 작업 공수 / 일정

| Phase | 항목 | 공수 |
|-------|------|------|
| Phase 1 | 신규 스키마 2개 (`DeviceUnassignRequest`, `DeviceBulkRemoveResponse`) + 단위 테스트 | 0.2일 |
| Phase 2 | 라우터 핸들러 + ConfigChangeLog 발행 | 0.3일 |
| Phase 3 | 트리거 statement-level 마이그레이션 + 트리거 테스트 3건 | 0.3일 |
| Phase 4 | 신규 테스트 6+종 + 회귀 검증 | 0.3일 |
| Phase 5 | 명세서 §5.6.9 + 부록 갱신 | 0.1일 |
| Phase 6 | OpenAPI version bump + Swagger 검증 | 0.1일 |
| **합계** | 백엔드만 (Central UI 별도) | **1.3일** |

---

## 13. 리스크 및 완화책

| # | 리스크 | 발생 가능성 | 영향 | 완화책 |
|---|--------|-----------|------|-------|
| R-1 | statement-level 트리거 PG 버전 미지원 | 낮 | 고 | 운영 PG10+ 사전 확인. 미지원 시 옵션 A(디바운싱) 임시 채택 |
| R-2 | 트리거 교체 중 NATS SYNC 미발화 | 중 | 중 | 마이그레이션 트랜잭션 내 DROP+CREATE 단일 실행. 직후 smoke test |
| R-3 | 기존 단건 DELETE 응답 envelope 변경 사고 | 낮 | 고 | `test_device_group_router.py::test_remove_device_from_group` 회귀 게이트 |
| R-4 | `EnumConfigActionType` 단일값 재사용으로 단건/벌크 구분 모호 | 낮 | 저 | description `(bulk)` 토큰 + before_state 키 구조 차이로 구분 |
| R-5 | UI에서 100개 초과 요청 시 422 발생 | 중 | 저 | 클라이언트 측 chunking 가이드 명세에 명시 |
| R-6 | AuditLog 추가 미구현 | 중 | 중 | Phase 2 DoD에 포함, code review 체크 |
| R-7 | 다중 group_id가 한 statement에 섞일 때 트리거 누락 | 낮 | 중 | `SELECT DISTINCT group_id FROM old_rows` 루프로 보장 |
| R-8 | operation_id 충돌 (`bulk_unassign_devices_from_group`) | 낮 | 저 | PR 전 `grep "^async def " app/routers/device_groups.py` |

---

## 14. 롤백 계획

| 단계 | 절차 |
|------|------|
| 1. 라우터 롤백 | `app/routers/device_groups.py` 신규 핸들러 제거 — git revert |
| 2. 스키마 롤백 | `app/schemas/device_group.py` 신규 클래스 2개 제거 |
| 3. 트리거 롤백 | 마이그레이션 down — statement-level 트리거 DROP + row-level 트리거 재생성 |
| 4. version 롤백 | `main.py` 1.6.0 → 1.5.0 |
| 5. 명세서 롤백 | §5.6.9 + 부록 §12.1 revert |
| 6. 테스트 롤백 | `test_device_group_unassign_bulk.py` 삭제 |
| 7. 검증 | 단건 DELETE 회귀 테스트 통과 확인 |

**롤백 안전성**: additive-only 변경이므로 단순 revert로 완전 복구 가능. 트리거만 마이그레이션 별도 필요.

---

## 15. 부록 — 신규 라우터 핸들러 스케치

### 15.1 스키마 (`app/schemas/device_group.py`)

```python
class DeviceUnassignRequest(BaseModel):
    """디바이스 벌크 해제 요청"""
    device_ids: List[int] = Field(
        ..., min_length=1, max_length=100,
        description="해제할 디바이스 ID 목록 (1~100)",
        json_schema_extra={"example": [1, 101, 201]}
    )

    @field_validator('device_ids')
    @classmethod
    def validate_device_ids(cls, v):
        if not v:
            raise ValueError('device_ids must not be empty')
        return v


class DeviceBulkRemoveResponse(BaseModel):
    """디바이스 벌크 해제 응답"""
    group_id: int = Field(..., json_schema_extra={"example": 1})
    removed_device_ids: List[int] = Field(default_factory=list,
        json_schema_extra={"example": [1, 101]})
    skipped_device_ids: List[int] = Field(default_factory=list,
        json_schema_extra={"example": [201]})
    not_found_device_ids: List[int] = Field(default_factory=list,
        json_schema_extra={"example": [999]})
    message: str = Field(..., json_schema_extra={
        "example": "2개 디바이스 해제, 1개 건너뜀, 1개 없음"
    })
```

### 15.2 라우터 핸들러 (`app/routers/device_groups.py`, 단건 DELETE 위에 배치)

```python
@router.delete(
    "/{group_id}/devices",
    response_model=ApiSingleResponse[DeviceBulkRemoveResponse],
    responses={
        200: {"description": "벌크 해제 성공 (부분 성공 포함)"},
        404: {"description": "DeviceGroup not found"},
        422: {"description": "device_ids 검증 실패"},
    },
)
async def bulk_unassign_devices_from_group(
    group_id: int,
    request: DeviceUnassignRequest,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """디바이스 그룹에서 디바이스 일괄 해제 (벌크)"""
    group = db.query(DeviceGroup).filter(DeviceGroup.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False,
                    "message": f"DeviceGroup with id {group_id} not found"},
        )

    # 중복 ID 제거 (멱등성)
    unique_ids = list(dict.fromkeys(request.device_ids))

    removed: list[int] = []
    skipped: list[int] = []
    not_found: list[int] = []
    removed_categories: dict[int, str] = {}

    for device_id in unique_ids:
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            not_found.append(device_id)
            continue

        mapping = db.query(DeviceGroupMapping).filter(
            DeviceGroupMapping.device_id == device_id,
            DeviceGroupMapping.category_device == device.category_device,
            DeviceGroupMapping.group_id == group_id,
        ).first()

        if not mapping:
            skipped.append(device_id)
            continue

        db.delete(mapping)
        removed.append(device_id)
        removed_categories[device_id] = device.category_device.value

    db.commit()  # 단일 commit (원자성)

    # ConfigChangeLog — removed가 있을 때만 1건 발행
    if removed:
        log_config_change(
            db=db,
            resource_type=EnumConfigResourceType.DEVICE_GROUP,
            resource_id=group_id,
            resource_name=f"DeviceGroup-{group_id} ({group.name})",
            action=EnumConfigActionType.UNASSIGNED,
            before_state={
                "device_ids": removed,
                "categories": removed_categories,
            },
            description=f"DeviceGroup에서 {len(removed)}개 디바이스 해제 (bulk)",
        )

    # AuditLog — 성공/실패 모두 발행 (skipped/not_found만 있어도)
    # audit_service.log_action(
    #     action_type="DEVICE_GROUP_UNASSIGN",
    #     resource_id=group_id,
    #     action_status="SUCCESS",
    #     changes={"before": {"device_ids": removed}},
    #     description=f"removed={len(removed)}, skipped={len(skipped)}, "
    #                 f"not_found={len(not_found)}",
    # )

    parts = [f"{len(removed)}개 디바이스 해제 완료"]
    if skipped:
        parts.append(f"{len(skipped)}개 건너뜀")
    if not_found:
        parts.append(f"{len(not_found)}개 없음")
    message = ", ".join(parts)

    return ApiSingleResponse(
        success=True,
        data=DeviceBulkRemoveResponse(
            group_id=group_id,
            removed_device_ids=removed,
            skipped_device_ids=skipped,
            not_found_device_ids=not_found,
            message=message,
        ),
        message=message,
    )
```

### 15.3 트리거 패치 (`app/db_triggers.py`)

```sql
-- DROP 기존 row-level 트리거
DROP TRIGGER IF EXISTS trg_sync_device_group_mappings ON device_group_mappings;

-- 신규 statement-level 함수
CREATE OR REPLACE FUNCTION fn_notify_dgm_stmt()
RETURNS trigger AS $$
DECLARE r RECORD;
BEGIN
    IF TG_OP = 'INSERT' THEN
        FOR r IN SELECT DISTINCT group_id FROM new_rows LOOP
            PERFORM pg_notify('gop_sync', jsonb_build_object(
                'cmd','SYNC_DEVICE_GROUP','action','UPDATED','resource_id',r.group_id
            )::text);
        END LOOP;
    ELSIF TG_OP = 'DELETE' THEN
        FOR r IN SELECT DISTINCT group_id FROM old_rows LOOP
            PERFORM pg_notify('gop_sync', jsonb_build_object(
                'cmd','SYNC_DEVICE_GROUP','action','UPDATED','resource_id',r.group_id
            )::text);
        END LOOP;
    END IF;
    RETURN NULL;
END $$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sync_dgm_ins
  AFTER INSERT ON device_group_mappings
  REFERENCING NEW TABLE AS new_rows
  FOR EACH STATEMENT EXECUTE FUNCTION fn_notify_dgm_stmt();

CREATE TRIGGER trg_sync_dgm_del
  AFTER DELETE ON device_group_mappings
  REFERENCING OLD TABLE AS old_rows
  FOR EACH STATEMENT EXECUTE FUNCTION fn_notify_dgm_stmt();
```

---

## 16. 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| v1.0 | 2026-06-17 | 초안 — POST 할당 대칭 벌크 해제 엔드포인트 신설, statement-level 트리거 + ConfigChangeLog 1건 정책 |

---

**문서 끝**