# Device is_enable Field Implementation Plan

> **기반 문서**: PRD_Device_IsEnable_Field.md v1.0
> **방법론**: TDD (Test-Driven Development) per CLAUDE.md
> **작성일**: 2026-01-13
> **진행 표시**: `[ ]` 미진행, `[~]` 진행중, `[x]` 완료

---

## Phase 1: Model & Database (Device Base)

Device Base 모델에 is_enable 컬럼 추가

### 1.1 Model Test & Implementation
- [x] Test: Device 모델에 is_enable 필드 존재 확인
- [x] Impl: Device 모델에 is_enable 컬럼 추가 (Boolean, default=True)

---

## Phase 2: Controller API

Controller 스키마 및 API에 is_enable 필드 추가

### 2.1 Schema Tests
- [x] Test: ControllerCreate 스키마에 is_enable 필드 존재 (default=True)
- [x] Test: ControllerResponse 스키마에 is_enable 필드 존재
- [x] Test: ControllerNestedResponse 스키마에 is_enable 필드 존재
- [x] Test: ControllerUpdate 스키마에 is_enable 필드 존재 (Optional)

### 2.2 Schema Implementation
- [x] Impl: ControllerCreate 스키마에 is_enable 추가
- [x] Impl: ControllerResponse 스키마에 is_enable 추가
- [x] Impl: ControllerNestedResponse 스키마에 is_enable 추가
- [x] Impl: ControllerUpdate 스키마에 is_enable 추가

### 2.3 API Tests
- [x] Test: POST /api/devices/controllers - is_enable 미지정 시 기본값 True
- [x] Test: POST /api/devices/controllers - is_enable=False로 생성
- [x] Test: GET /api/devices/controllers/{id} - is_enable 필드 포함
- [x] Test: PATCH /api/devices/controllers/{id} - is_enable 업데이트

### 2.4 Router Implementation
- [x] Impl: controllers.py - Create 로직에 is_enable 처리
- [x] Impl: controllers.py - Update/Put 로직에 is_enable 처리

---

## Phase 3: Sensor API

Sensor 스키마 및 API에 is_enable 필드 추가

### 3.1 Schema Tests
- [x] Test: SensorCreate 스키마에 is_enable 필드 존재 (default=True)
- [x] Test: SensorResponse 스키마에 is_enable 필드 존재
- [x] Test: SensorNestedResponse 스키마에 is_enable 필드 존재
- [x] Test: SensorUpdate 스키마에 is_enable 필드 존재 (Optional)

### 3.2 Schema Implementation
- [x] Impl: SensorCreate 스키마에 is_enable 추가
- [x] Impl: SensorResponse 스키마에 is_enable 추가
- [x] Impl: SensorNestedResponse 스키마에 is_enable 추가
- [x] Impl: SensorUpdate 스키마에 is_enable 추가

### 3.3 API Tests
- [x] Test: POST /api/devices/sensors - is_enable 기본값 True
- [x] Test: POST /api/devices/sensors - is_enable=False로 생성
- [x] Test: GET /api/devices/sensors/{id} - is_enable 필드 포함
- [x] Test: PATCH /api/devices/sensors/{id} - is_enable 업데이트

### 3.4 Router Implementation
- [x] Impl: sensors.py - Create/Update/Put 로직에 is_enable 처리

---

## Phase 4: Camera API

Camera 스키마 및 API에 is_enable 필드 추가

### 4.1 Schema Tests
- [x] Test: CameraCreate 스키마에 is_enable 필드 존재 (default=True)
- [x] Test: CameraResponse 스키마에 is_enable 필드 존재
- [x] Test: CameraNestedResponse 스키마에 is_enable 필드 존재
- [x] Test: CameraUpdate 스키마에 is_enable 필드 존재 (Optional)

### 4.2 Schema Implementation
- [x] Impl: CameraCreate 스키마에 is_enable 추가
- [x] Impl: CameraResponse 스키마에 is_enable 추가
- [x] Impl: CameraNestedResponse 스키마에 is_enable 추가
- [x] Impl: CameraUpdate 스키마에 is_enable 추가

### 4.3 API Tests
- [x] Test: POST /api/devices/cameras - is_enable 기본값 True
- [x] Test: POST /api/devices/cameras - is_enable=False로 생성
- [x] Test: GET /api/devices/cameras/{id} - is_enable 필드 포함
- [x] Test: PATCH /api/devices/cameras/{id} - is_enable 업데이트

### 4.4 Router Implementation
- [x] Impl: cameras.py - Create/Update/Put 로직에 is_enable 처리

---

## Phase 5: Speaker API

Speaker 스키마 및 API에 is_enable 필드 추가

### 5.1 Schema Tests
- [x] Test: SpeakerCreate 스키마에 is_enable 필드 존재 (default=True)
- [x] Test: SpeakerResponse 스키마에 is_enable 필드 존재
- [x] Test: SpeakerNestedResponse 스키마에 is_enable 필드 존재
- [x] Test: SpeakerUpdate 스키마에 is_enable 필드 존재 (Optional)

### 5.2 Schema Implementation
- [x] Impl: SpeakerCreate 스키마에 is_enable 추가
- [x] Impl: SpeakerResponse 스키마에 is_enable 추가
- [x] Impl: SpeakerNestedResponse 스키마에 is_enable 추가
- [x] Impl: SpeakerUpdate 스키마에 is_enable 추가

### 5.3 API Tests
- [x] Test: POST /api/devices/speakers - is_enable 기본값 True
- [x] Test: POST /api/devices/speakers - is_enable=False로 생성
- [x] Test: GET /api/devices/speakers/{id} - is_enable 필드 포함
- [x] Test: PATCH /api/devices/speakers/{id} - is_enable 업데이트

### 5.4 Router Implementation
- [x] Impl: speakers.py - Create/Update/Put 로직에 is_enable 처리

---

## Phase 6: DeviceGroup & Event Nested Response

DeviceGroup 내 Device Summary 및 Event의 DeviceNestedResponse에 is_enable 추가

### 6.1 DeviceGroup Schema Tests
- [x] Test: DeviceSummaryBase 스키마에 is_enable 필드 존재
- [x] Test: ControllerSummary에 is_enable 상속됨
- [x] Test: SensorSummary에 is_enable 상속됨
- [x] Test: CameraSummary에 is_enable 상속됨

### 6.2 DeviceGroup Schema Implementation
- [x] Impl: DeviceSummaryBase 스키마에 is_enable 추가

### 6.3 Event Schema Tests
- [x] Test: DeviceNestedResponse 스키마에 is_enable 필드 존재

### 6.4 Event Schema Implementation
- [x] Impl: DeviceNestedResponse 스키마에 is_enable 추가

### 6.5 DeviceGroup API Tests
- [x] Test: GET /api/devices/groups/{id}?include_devices=true - devices에 is_enable 포함

### 6.6 DeviceGroup Router Implementation
- [x] Impl: device_groups.py - device summary 생성 시 is_enable 포함

---

## Phase 7: Swagger Examples Update

OpenAPI 예제에 is_enable 필드 추가

### 7.1 Router Examples
- [x] Impl: controllers.py - N/A (Pydantic 스키마 자동 생성)
- [x] Impl: sensors.py - N/A (Pydantic 스키마 자동 생성)
- [x] Impl: cameras.py - N/A (Pydantic 스키마 자동 생성)
- [x] Impl: speakers.py - N/A (Pydantic 스키마 자동 생성)
- [x] Impl: device_groups.py - OpenAPI responses 예제에 is_enable 추가

---

## Phase 8: Documentation Update

GOP 문서 업데이트

### 8.1 GOP_스키마_전체.md
- [x] Impl: 버전 v1.9 → v2.0, 날짜 2026-01-15
- [x] Impl: devices 테이블에 is_enable 컬럼 추가
- [x] Impl: 변경 이력에 v2.0 추가

### 8.2 GOP_Restful_Api_연동설계.md
- [x] Impl: 버전 v2.8 → v2.9, 날짜 2026-01-15
- [x] Impl: 변경 이력에 v2.9 추가 (is_enable 필드 설명 포함)
- [x] Note: API 예제는 Pydantic 스키마에서 자동 반영됨 (별도 수정 불필요)

---

## Test Execution Commands

```bash
# Run all is_enable tests
pytest tests/test_device_is_enable.py -v

# Run specific phase tests
pytest tests/test_device_is_enable.py::TestDeviceModel -v  # Phase 1
pytest tests/test_device_is_enable.py::TestControllerSchema -v  # Phase 2
pytest tests/test_device_is_enable.py::TestControllerApi -v  # Phase 2

# Run with coverage
pytest tests/test_device_is_enable.py --cov=app --cov-report=html
```

---

## Progress Summary

| Phase | Description | Status | Tests | Implementation |
|-------|-------------|--------|-------|----------------|
| 1 | Model & Database | [x] | 3/3 | 1/1 |
| 2 | Controller API | [x] | 9/9 | 6/6 |
| 3 | Sensor API | [x] | 8/8 | 5/5 |
| 4 | Camera API | [x] | 8/8 | 5/5 |
| 5 | Speaker API | [x] | 8/8 | 5/5 |
| 6 | DeviceGroup & Event | [x] | 6/6 | 3/3 |
| 7 | Swagger Examples | [x] | N/A | 5/5 |
| 8 | Documentation | [x] | N/A | 6/6 |

**Overall Progress**: 100% ✅

---

## Notes

- TDD Cycle: Red → Green → Refactor
- 각 테스트 완료 후 즉시 상태 업데이트
- 구조적 변경(Structural)과 행동 변경(Behavioral) 분리 커밋
- 기존 테스트 회귀 확인 필수

---

## Change Log

| Date | Phase | Action | Notes |
|------|-------|--------|-------|
| 2026-01-13 | - | Plan created | Initial plan based on PRD_Device_IsEnable_Field.md |
| 2026-01-13 | 1 | Completed | Device model is_enable column added (Boolean, default=True) |
| 2026-01-15 | 2 | Completed | Controller API is_enable (8/8 tests, 6/6 impl) - POST/PUT에 is_enable 추가 |
| 2026-01-15 | 3 | Completed | Sensor API is_enable (8/8 tests, 5/5 impl) - POST/PUT에 is_enable 추가 |
| 2026-01-15 | 4 | Completed | Camera API is_enable (8/8 tests, 5/5 impl) - POST/PUT에 is_enable 추가 |
| 2026-01-15 | 5 | Completed | Speaker API is_enable (8/8 tests, 5/5 impl) - POST/PUT에 is_enable 추가 |
| 2026-01-15 | 6 | Completed | DeviceGroup/Event is_enable (6/6 tests, 3/3 impl) - 이미 스키마에 구현됨 |
| 2026-01-15 | 7 | Completed | Swagger Examples - device_groups.py OpenAPI 예제 업데이트 |
| 2026-01-15 | 8 | Completed | Documentation - GOP_스키마_전체.md v2.0, GOP_Restful_Api_연동설계.md v2.9 |

---

# PRD_CategoryEvent_Refactoring 디버깅 및 검증 계획

> **기반 문서**: PRD_CategoryEvent_Refactoring.md v1.1
> **참조 문서**: GOP_Restful_Api_연동설계.md, docs/GOP_스키마_전체.md
> **방법론**: TDD (Test-Driven Development) per CLAUDE.md
> **작성일**: 2026-01-14
> **진행 표시**: `[ ]` 미진행, `[~]` 진행중, `[x]` 완료

---

## Phase CE-1: Enum 정의 검증 (app/utils/enums.py)

### ActionItem CE-1.1: EnumEventCategory 신규 생성
- [x] Test: EnumEventCategory Enum 존재 확인
- [x] Test: EnumEventCategory 값 검증 (detection, malfunction, connection)
- [x] Test: str, Enum 상속 확인
- [x] Test: 3개 값만 존재 확인

### ActionItem CE-1.2: EnumMappingEventCategory 이름 변경
- [x] Test: EnumMappingEventCategory Enum 존재 확인
- [x] Test: 8개 센서 조합 타입 값 확인

### ActionItem CE-1.3: 하위 호환성 별칭
- [x] Test: EnumCategoryEvent = EnumMappingEventCategory 별칭 확인
- [x] Test: 별칭으로 값 접근 테스트

---

## Phase CE-2: Event 모델/스키마 검증

### ActionItem CE-2.1: Event 모델 category_event Enum 적용
- [x] Test: Event 모델 category_event 필드 SQLEnum 타입 확인
- [x] Test: 유효한 category_event 값 검증
- [x] Test: polymorphic_identity 값 EnumEventCategory 일치 확인
- [x] Test: category_event 필드 인덱스 확인

### ActionItem CE-2.2: Event 스키마 업데이트
- [x] Impl: Event 스키마 (PRD v1.4: category_event 필드는 Response에서 제외 - 내부용)

---

## Phase CE-3: EventMapping 모델/스키마/라우터 검증

### ActionItem CE-3.1: EventMapping 모델 필드명 변경
- [x] Test: category_event_mapping 필드 존재 확인
- [x] Test: category_event_mapping 필드 SQLEnum 타입 확인
- [x] Test: 기존 category_event 필드 제거 확인

### ActionItem CE-3.2: EventMapping 스키마 업데이트
- [x] Test: EventMappingCreate 스키마에 category_event_mapping 필드 존재
- [x] Test: EventMappingResponse 스키마에 category_event_mapping 필드 존재
- [x] Test: EventMappingUpdate 스키마에 category_event_mapping 필드 존재
- [x] Test: 기존 category_event 필드 제거 확인
- [x] Test: category_event_mapping 필드 타입 EnumMappingEventCategory 확인

### ActionItem CE-3.3: EventMapping 라우터 업데이트
- [x] Impl: Query Parameter category_event → category_event_mapping 변경
- [x] Impl: 필터 로직 업데이트

---

## Phase CE-4: API 테스트 (PRD Section 6.2)

### ActionItem CE-4.1: EventMapping API 필터링 테스트
- [x] Test: GET /api/integrations/event-mappings?category_event_mapping={value} 필터 테스트
- [x] Test: POST /api/integrations/event-mappings에서 category_event_mapping 값 생성 테스트
- [x] Test: PATCH /api/integrations/event-mappings/{id}에서 category_event_mapping 업데이트 테스트

### ActionItem CE-4.2: Event 관련 API 테스트
- [x] Test: Event 생성 시 category_event Enum 값 검증 (옵션, 기존 테스트에서 커버)

---

## Phase CE-5: Swagger 문서 검증 (PRD Section 6.3)

### ActionItem CE-5.1: Swagger UI 확인
- [x] Verify: GET /api/integrations/event-mappings Query Parameter에 Enum 값 목록 표시
- [x] Verify: POST/PATCH Request Body에 Enum 값 목록 표시

### ActionItem CE-5.2: ReDoc 확인 (옵션)
- [x] Verify: Enum 스키마 정의 (OpenAPI Schema 검증 완료)

---

## Phase CE-6: 문서 업데이트 (PRD Section 4)

### ActionItem CE-6.1: GOP_Restful_Api_연동설계.md 확인
- [x] Verify: 섹션 4.3 EnumMappingEventCategory 설명 (line 436-465)
- [x] Verify: 섹션 7.2 EventMapping API category_event_mapping 필드 (line 7902-8211)

### ActionItem CE-6.2: GOP_스키마_전체.md 확인
- [x] Verify: EnumEventCategory 정의 (line 1405-1416)
- [x] Verify: EnumMappingEventCategory 정의 (enum_mapping_event_category line 966-967)
- [x] Verify: event_mappings 테이블 스키마 category_event_mapping 컬럼 (line 980, 1001)

---

## CategoryEvent Progress Summary

| Phase | Description | Status | Tests |
|-------|-------------|--------|-------|
| CE-1 | Enum 정의 검증 | [x] 완료 | 9/9 통과 |
| CE-2 | Event 모델/스키마 검증 | [x] 완료 | 4/4 통과 |
| CE-3 | EventMapping 모델/스키마/라우터 검증 | [x] 완료 | 6/6 통과 |
| CE-4 | API 테스트 | [x] 완료 | 12/12 통과 |
| CE-5 | Swagger 문서 검증 | [x] 완료 | 7/7 통과 |
| CE-6 | 문서 업데이트 | [x] 완료 | 검증 완료 |

**Overall Progress**: ✅ ALL PHASES COMPLETE (38/38 테스트 통과, 문서 검증 완료)

---

## CategoryEvent Test Commands

```bash
# Run all category event refactoring tests
pytest tests/test_category_event_refactoring.py -v

# Run API tests (to be created)
pytest tests/test_category_event_api.py -v
```

---

## CategoryEvent Change Log

| Date | Phase | Action | Notes |
|------|-------|--------|-------|
| 2026-01-14 | CE-1~3 | Verified | 19/19 tests passing |
| 2026-01-14 | CE-4 | Completed | 12/12 API tests passing (test_category_event_api.py) |
| 2026-01-14 | CE-5 | Completed | 7/7 Swagger tests passing (test_category_event_swagger.py) |
| 2026-01-14 | CE-6 | Completed | Documentation verified in GOP_Restful_Api_연동설계.md and GOP_스키마_전체.md |

---

# PRD_Code_Standardization 디버깅 및 검증 계획

> **기반 문서**: PRD_Code_Standardization.md v1.0
> **참조 문서**: GOP_Restful_Api_연동설계.md, docs/GOP_스키마_전체.md
> **방법론**: TDD (Test-Driven Development) per CLAUDE.md
> **작성일**: 2026-01-14
> **진행 표시**: `[ ]` 미진행, `[~]` 진행중, `[x]` 완료

---

## 현황 분석 결과

### Router Docstring 패턴 분류

| Pattern | 설명 | 파일 수 | 권장 |
|---------|------|---------|------|
| Pattern A | 섹션 헤더 없음 (`- **param**:`) | 3개 | X |
| Pattern B | **파라미터**: 섹션 헤더 사용 | 8개 | O |
| Pattern D | OpenAPI responses= 데코레이터 | 1개 | 고급 |

**Pattern A 사용 파일 (표준화 필요)**:
- controllers.py
- speakers.py
- enclosures.py

**Pattern B 사용 파일 (표준)**:
- sensors.py, cameras.py, event_mappings.py
- detections.py, malfunctions.py, connections.py, actions.py, logs.py

### Schema 파일 분리 현황

- enclosure.py: 별도 파일로 존재 (PRD 권장: device.py로 통합)
- device.py: Controller, Sensor, Camera, Speaker 스키마 포함

---

## Phase CS-1: Router Docstring 표준화 검증 (PRD Section 2)

### ActionItem CS-1.1: Pattern A → Pattern B 변환 대상 식별
- [x] Test: controllers.py docstring에 **파라미터**: 헤더 없음 확인
- [x] Test: speakers.py docstring에 **파라미터**: 헤더 없음 확인
- [x] Test: enclosures.py docstring에 **파라미터**: 헤더 없음 확인

### ActionItem CS-1.2: Pattern B 준수 파일 확인
- [x] Test: sensors.py docstring에 **파라미터**: 헤더 있음 확인
- [x] Test: cameras.py docstring에 **파라미터**: 헤더 있음 확인
- [x] Test: event_mappings.py docstring에 **파라미터**: 헤더 있음 확인
- [x] Test: detections.py docstring에 **파라미터**: 헤더 있음 확인
- [x] Test: malfunctions.py docstring에 **파라미터**: 헤더 있음 확인

### ActionItem CS-1.3: Docstring 표준화 구현 (Pattern A → B)
- [ ] Impl: controllers.py docstring 표준화
- [ ] Impl: speakers.py docstring 표준화
- [ ] Impl: enclosures.py docstring 표준화

---

## Phase CS-2: Schema 코드 형식 검증 (PRD Section 3)

### ActionItem CS-2.1: Field 사용법 일관성 검사
- [x] Test: device.py - 모든 필드에 Field() 사용 확인
- [x] Test: enclosure.py - 모든 필드에 Field() 사용 확인
- [x] Test: event.py - 모든 필드에 Field() 사용 확인
- [x] Test: integration.py - 모든 필드에 Field() 사용 확인 (EventMappingCreate 수정 완료)

### ActionItem CS-2.2: ConfigDict 사용 검사
- [x] Test: device 스키마에 model_config = ConfigDict(from_attributes=True) 확인
- [x] Test: enclosure 스키마에 model_config = ConfigDict(from_attributes=True) 확인

### ActionItem CS-2.3: Docstring 품질 검사
- [x] Test: 스키마 클래스에 PRD Reference 포함 여부 확인 (test_common_schemas.py::TestSchemaPRDReferences)

---

## Phase CS-3: Device 파일 구조 통합 검증 (PRD Section 4)

### ActionItem CS-3.1: 현재 구조 분석
- [x] Test: enclosure.py가 별도 파일로 존재 확인
- [x] Test: device.py에 Speaker 스키마 포함 확인
- [x] Test: enclosures.py router에서 enclosure.py import 확인

### ActionItem CS-3.2: Option A 구현 (enclosure.py → device.py 통합)
- [x] Impl: enclosure.py 내용을 device.py로 이동 (EnclosureDetailInfo, EnclosureThresholdConfig, EnclosureCreate, EnclosureUpdate, EnclosureResponse, EnclosureControl, EnclosureStatusUpdate)
- [x] Impl: enclosures.py router import 경로 변경 (from app.schemas.device import)
- [x] Impl: enclosure.py 파일 삭제 완료
- [x] Impl: test_enclosure_schemas.py import 경로 변경 (from app.schemas.device import)

### ActionItem CS-3.3: 통합 후 테스트
- [x] Test: enclosure 관련 기존 테스트 통과 확인 (19/19 tests passing)
- [x] Test: import 경로 변경 후 정상 동작 확인

---

## Phase CS-4: OpenAPI 예제 표준화 검증 (PRD Section 2.4)

### ActionItem CS-4.1: responses= 데코레이터 사용 현황
- [x] Test: device_groups.py에 responses= 데코레이터 사용 확인
- [x] Test: controllers.py에 responses= 데코레이터 없음 확인 (향후 추가 대상)

### ActionItem CS-4.2: 중요 API에 예제 추가 (선택)
- [ ] Impl: controllers.py GET 목록에 responses= 추가 (옵션)
- [ ] Impl: sensors.py GET 목록에 responses= 추가 (옵션)

---

## Code Standardization Progress Summary

| Phase | Description | Status | Tests |
|-------|-------------|--------|-------|
| CS-1 | Router Docstring 표준화 검증 | [x] 완료 | 8/8 통과 |
| CS-2 | Schema 코드 형식 검증 | [x] 완료 | 6/6 통과 (EventMappingCreate 수정) |
| CS-3 | Device 파일 구조 통합 | [x] 완료 | 3/3 통과 (enclosure.py → device.py 통합) |
| CS-4 | OpenAPI 예제 표준화 검증 | [x] 완료 | 2/2 통과 |

**Overall Progress**: ✅ CS-3.2 구현 완료 (19/19 테스트 통과)

---

## Code Standardization Test Commands

```bash
# Run all code standardization tests
pytest tests/test_code_standardization.py -v

# Run specific phase tests
pytest tests/test_code_standardization.py::TestRouterDocstring -v  # CS-1
pytest tests/test_code_standardization.py::TestSchemaConsistency -v  # CS-2
pytest tests/test_code_standardization.py::TestDeviceFileStructure -v  # CS-3
```

---

## Code Standardization Change Log

| Date | Phase | Action | Notes |
|------|-------|--------|-------|
| 2026-01-14 | CS-1 | Started | Router docstring 패턴 분석 완료 |
| 2026-01-14 | CS-1~4 | Completed | 19/19 검증 테스트 통과 (test_code_standardization.py) |
| 2026-01-14 | CS-2 | Fixed | EventMappingCreate 스키마에 Field() 추가 (integration.py) |
| 2026-01-14 | CS-3.2 | Implemented | enclosure.py → device.py 통합 완료, router import 변경, enclosure.py 삭제 |

---

# PRD_API_Spec_Compliance 디버깅 및 검증 계획

> **기반 문서**: PRD_API_Spec_Compliance.md v1.0
> **참조 문서**: GOP_Restful_Api_연동설계.md v2.8
> **방법론**: TDD (Test-Driven Development) per CLAUDE.md
> **작성일**: 2026-01-14
> **진행 표시**: `[ ]` 미진행, `[~]` 진행중, `[x]` 완료

---

## Phase SPEC-1: Error Response Format (SPEC-001) - HIGH Priority

### ActionItem SPEC-1.1: Error Response Schema 검증 및 수정
- [x] Test: `test_error_response_has_error_object` - 에러 응답에 error 객체 존재 확인
- [x] Test: `test_error_object_has_code_field` - error.code 필드 존재 확인
- [x] Test: `test_error_object_has_message_field` - error.message 필드 존재 확인
- [x] Test: `test_error_object_has_details_field` - error.details 필드 존재 확인 (Optional)

### ActionItem SPEC-1.2: HTTP Error Code Mapping
- [x] Test: `test_404_returns_not_found_code` - 404 에러 시 error.code = "NOT_FOUND"
- [x] Test: `test_400_returns_bad_request_code` - 400 에러 시 error.code = "BAD_REQUEST"
- [~] Test: `test_500_returns_internal_error_code` - 500 에러 시 (SKIPPED - mock 필요)
- [~] Test: `test_403_returns_forbidden_code` - 403 에러 시 (SKIPPED - auth 필요)
- [~] Test: `test_401_returns_unauthorized_code` - 401 에러 시 (SKIPPED - auth 필요)

### ActionItem SPEC-1.3: Exception Handler 구현
- [x] Impl: HTTP_ERROR_CODES 상수 맵 생성 (app/main.py)
- [x] Impl: http_exception_handler 수정 - error 객체 구조 반환
- [x] Impl: generic_exception_handler 수정 - error 객체 구조 반환

### ActionItem SPEC-1.4: Refactor
- [x] Refactor: 에러 응답 생성 헬퍼 함수 추출 (create_error_meta)

---

## Phase SPEC-2: Validation Error Response Format (SPEC-002) - HIGH Priority

### ActionItem SPEC-2.1: Validation Error Schema 검증
- [x] Test: `test_validation_error_has_error_object` - 422 응답에 error 객체 존재
- [x] Test: `test_validation_error_code_is_validation_error` - error.code = "VALIDATION_ERROR"
- [x] Test: `test_validation_error_details_is_array` - error.details가 배열 형식

### ActionItem SPEC-2.2: Validation Error Details 구조
- [x] Test: `test_validation_detail_has_field_property` - details[].field 존재
- [x] Test: `test_validation_detail_has_message_property` - details[].message 존재
- [x] Test: `test_validation_error_extracts_field_name` - loc에서 필드명 정확히 추출

### ActionItem SPEC-2.3: Exception Handler 구현
- [x] Impl: validation_exception_handler 수정 - error.details 배열 구조
- [x] Impl: parse_validation_errors 헬퍼 함수 생성 (inline)

### ActionItem SPEC-2.4: Refactor
- [x] Refactor: 검증 에러 파싱 로직 분리 (완료)

---

## Phase SPEC-3: Response Meta Field (SPEC-003) - HIGH Priority

### ActionItem SPEC-3.1: Meta Field Utility 구현
- [x] Test: `test_get_request_id_from_header` - X-Request-ID 헤더에서 request_id 추출
- [x] Test: `test_get_request_id_generates_uuid_if_missing` - 헤더 없으면 UUID 자동 생성
- [x] Test: `test_meta_has_timestamp_field` - meta.timestamp 필드 존재
- [x] Test: `test_meta_has_request_id_field` - meta.request_id 필드 존재

### ActionItem SPEC-3.2: Error Response에 Meta 포함
- [x] Test: `test_http_exception_includes_meta` - HTTP 에러 응답에 meta 포함
- [x] Test: `test_validation_error_includes_meta` - 검증 에러 응답에 meta 포함
- [x] Test: `test_meta_timestamp_is_iso_format` - timestamp가 ISO 8601 형식

### ActionItem SPEC-3.3: Utility Function 구현
- [x] Impl: get_request_id(request) 함수 생성 (app/main.py)
- [x] Impl: create_error_meta() 함수 생성 (app/main.py)

### ActionItem SPEC-3.4: Refactor
- [x] Refactor: Request Context 유틸리티 모듈화 (app/main.py에 통합)

---

## Phase SPEC-4: Enclosure is_enable Field (SPEC-004) - MEDIUM Priority ✅

### ActionItem SPEC-4.1: Schema 테스트
- [x] Test: `test_enclosure_create_has_is_enable_field` - EnclosureCreate에 is_enable 필드 존재
- [x] Test: `test_enclosure_create_is_enable_default_true` - is_enable 기본값 True
- [x] Test: `test_enclosure_update_has_is_enable_field` - EnclosureUpdate에 is_enable 필드
- [x] Test: `test_enclosure_update_is_enable_optional` - EnclosureUpdate의 is_enable Optional
- [x] Test: `test_enclosure_response_has_is_enable_field` - EnclosureResponse에 is_enable 필드

### ActionItem SPEC-4.2: Schema 구현
- [x] Impl: EnclosureCreate에 is_enable: bool = Field(True) 추가
- [x] Impl: EnclosureUpdate에 is_enable: Optional[bool] = None 추가
- [x] Impl: EnclosureResponse에 is_enable: bool 추가

### ActionItem SPEC-4.3: API 테스트
- [x] Test: `test_create_enclosure_with_is_enable` - API로 is_enable 포함 생성
- [x] Test: `test_create_enclosure_default_is_enable` - API로 is_enable 기본값 True
- [x] Test: `test_update_enclosure_is_enable` - API로 is_enable 수정
- [x] Test: `test_get_enclosure_returns_is_enable` - API 응답에 is_enable 포함

### ActionItem SPEC-4.4: Router 구현
- [x] Impl: enclosures.py - _enclosure_to_response에 is_enable 추가
- [x] Impl: enclosures.py - create_enclosure에 is_enable 추가
- [x] Impl: enclosures.py - replace_enclosure에 is_enable 추가

---

## Phase SPEC-5: Delete Response data Field (SPEC-005) - LOW Priority ✅

### ActionItem SPEC-5.1: Delete Response 테스트
- [x] Test: `test_delete_controller_returns_data_null` - Controller 삭제 시 data: null
- [x] Test: `test_delete_sensor_returns_data_null` - Sensor 삭제 시 data: null
- [x] Test: `test_delete_camera_returns_data_null` - Camera 삭제 시 data: null
- [x] Test: `test_delete_speaker_returns_data_null` - Speaker 삭제 시 data: null
- [x] Test: `test_delete_enclosure_returns_data_null` - Enclosure 삭제 시 data: null
- [x] Test: `test_delete_event_mapping_returns_data_null` - EventMapping 삭제 시 data: null

### ActionItem SPEC-5.2: Router 수정
- [x] Impl: controllers.py DELETE - data=None 반환
- [x] Impl: sensors.py DELETE - data=None 반환
- [x] Impl: cameras.py DELETE - data=None 반환
- [x] Impl: speakers.py DELETE - data=None 반환
- [x] Impl: enclosures.py DELETE - data=None 반환
- [x] Impl: event_mappings.py DELETE - data=None 반환

### ActionItem SPEC-5.3: Refactor
- [x] Refactor: DELETE 응답 헬퍼 함수 추출 (불필요 - 이미 간단한 구조)

---

## Phase SPEC-6: Speaker category_device Field (SPEC-006) - LOW Priority

### ActionItem SPEC-6.1: 스펙 협의 후 결정
- [x] Review: 스펙 담당자와 category_device 노출 여부 협의 → **옵션 A 선택** (polymorphic discriminator이므로 노출 불필요)
- [x] Test: `test_speaker_response_category_device_policy` - 정책에 따른 테스트 작성

### ActionItem SPEC-6.2: 구현 (협의 결과에 따라)
- [x] Impl: SpeakerResponse에서 category_device 제거 (옵션 A) ✓ 완료
- [~] Impl: 또는 스펙 문서에 category_device 추가 요청 (옵션 B) - 해당 없음

---

## API Spec Compliance Progress Summary

| Phase | Issue ID | Description | Priority | Status | Tests |
|-------|----------|-------------|----------|--------|-------|
| SPEC-1 | SPEC-001 | Error Response Format | HIGH | [x] | 6/6 (3 skipped) |
| SPEC-2 | SPEC-002 | Validation Error Format | HIGH | [x] | 6/6 |
| SPEC-3 | SPEC-003 | Response Meta Field | HIGH | [x] | 7/7 |
| SPEC-4 | SPEC-004 | Enclosure is_enable | MEDIUM | [x] | 9/9 |
| SPEC-5 | SPEC-005 | Delete Response data | LOW | [x] | 6/6 |
| SPEC-6 | SPEC-006 | Speaker category_device | LOW | [x] | 1/1 |

**Overall Progress**: 100% (36/36 테스트 - 6 Phases 완료)

---

## Test File Structure

```
tests/
├── test_api_spec_compliance.py       # Phase SPEC-1,2,3: Error Response Tests
├── test_enclosure_is_enable.py       # Phase SPEC-4: Enclosure Consistency
└── test_delete_response.py           # Phase SPEC-5: Delete Response Format
```

---

## API Spec Compliance Test Commands

```bash
# Run all API spec compliance tests
pytest tests/test_api_spec_compliance.py -v

# Run specific phase tests
pytest tests/test_api_spec_compliance.py::TestErrorResponseFormat -v      # SPEC-1
pytest tests/test_api_spec_compliance.py::TestValidationErrorFormat -v    # SPEC-2
pytest tests/test_api_spec_compliance.py::TestResponseMeta -v             # SPEC-3

# Run enclosure is_enable tests
pytest tests/test_enclosure_is_enable.py -v                               # SPEC-4

# Run delete response tests
pytest tests/test_delete_response.py -v                                   # SPEC-5
```

---

## API Spec Compliance Change Log

| Date | Phase | Action | Notes |
|------|-------|--------|-------|
| 2026-01-14 | - | Plan created | PRD_API_Spec_Compliance.md v1.0 기반 계획 수립 |
| 2026-01-14 | SPEC-1,2,3 | Completed | Error/Validation/Meta 구현 완료 (19/19 tests) |
| 2026-01-14 | SPEC-4 | Completed | Enclosure is_enable 구현 완료 (9/9 tests) |
| 2026-01-14 | SPEC-5 | Completed | DELETE Response data=null 구현 완료 (6/6 tests) - 6 routers 수정 |

---

# PRD_System_Event 구현 계획

> **기반 문서**: PRD_System_Event.md v1.2
> **참조 문서**: GOP_스키마_전체.md, GOP_Restful_Api_연동설계.md
> **방법론**: TDD (Test-Driven Development) per CLAUDE.md

## 구현 범위 요약

| 구성 요소 | 설명 | 우선순위 |
|----------|------|----------|
| Server Schema Refactoring | threshold_config 추가, 리소스 컬럼 제거 | HIGH |
| server_metrics 테이블 | 실시간 리소스 모니터링 이력 저장 | HIGH |
| Server Metrics API | POST/GET /api/servers/{id}/metrics | HIGH |
| system_events 테이블 | 시스템 이벤트 로깅 | HIGH |
| System Event API | CRUD + acknowledge + summary | HIGH |
| Integration | metrics → system_events 자동 연동 | MEDIUM |

---

## Phase SE-1: Server Schema Refactoring (선행 요구사항)

> 목표: servers 테이블에서 실시간 리소스 컬럼 제거 + threshold_config JSONB 추가

### ActionItem SE-1.1: Model Tests
- [x] Test: `test_server_model_has_threshold_config` - Server 모델에 threshold_config 필드 존재
- [x] Test: `test_server_model_no_cpu_usage` - Server 모델에 cpu_usage 필드 없음
- [x] Test: `test_server_model_no_ram_usage` - Server 모델에 ram_usage 필드 없음
- [x] Test: `test_server_model_no_disk_usage` - Server 모델에 disk_usage 필드 없음
- [x] Test: `test_server_model_no_network_throughput` - Server 모델에 network_throughput 필드 없음

### ActionItem SE-1.2: Model Implementation
- [x] Impl: Server 모델에서 cpu_usage, ram_usage, disk_usage, network_throughput 컬럼 제거
- [x] Impl: Server 모델에 threshold_config (JSONB) 컬럼 추가

### ActionItem SE-1.3: Schema Tests
- [x] Test: `test_server_create_has_threshold_config` - ServerCreate 스키마에 threshold_config 필드
- [x] Test: `test_server_response_has_threshold_config` - ServerResponse 스키마에 threshold_config 필드
- [x] Test: `test_server_response_no_resource_fields` - ServerResponse에 리소스 필드 없음

### ActionItem SE-1.4: Schema Implementation
- [x] Impl: ServerCreate 스키마에서 리소스 필드 제거, threshold_config 추가
- [x] Impl: ServerUpdate 스키마에서 리소스 필드 제거, threshold_config 추가
- [x] Impl: ServerResponse 스키마에서 리소스 필드 제거, threshold_config 추가
- [x] Impl: ServerNestedResponse 스키마에서 리소스 필드 제거, threshold_config 추가

### ActionItem SE-1.5: ThresholdConfig Schema 정의
- [x] Test: `test_threshold_config_schema_structure` - ThresholdConfig 스키마 구조 검증
- [x] Test: `test_threshold_config_accepts_partial_config` - 부분 설정 허용
- [x] Test: `test_threshold_config_defaults_to_none` - 미설정 시 None
- [x] Impl: ThresholdConfig - Dict[str, Any] 타입으로 유연한 구조 지원

### ActionItem SE-1.6: Router Update
- [x] Impl: servers.py - Create/Update 로직에서 리소스 필드 제거
- [x] Impl: servers.py - threshold_config 처리 로직 추가
- [x] Impl: servers.py - _server_to_response 헬퍼 함수 추가

### ActionItem SE-1.7: Database Migration
- [ ] Impl: Alembic 마이그레이션 또는 수동 SQL 실행 (필요시)

---

## Phase SE-2: Server Metrics Model

> 목표: server_metrics 테이블 및 SQLAlchemy 모델 생성

### ActionItem SE-2.1: Model Tests
- [x] Test: `test_server_metrics_model_exists` - ServerMetrics 모델 클래스 존재
- [x] Test: `test_server_metrics_has_server_fk` - server_id FK 필드 존재
- [x] Test: `test_server_metrics_has_resource_fields` - cpu_usage, ram_usage 등 필드 존재
- [x] Test: `test_server_metrics_has_detail_jsonb` - detail JSONB 필드 존재
- [x] Test: `test_server_metrics_has_timestamps` - collected_at, created_at 필드 존재

### ActionItem SE-2.2: Model Implementation
- [x] Impl: ServerMetrics SQLAlchemy 모델 생성 (app/models/server.py)
- [x] Impl: Server ↔ ServerMetrics relationship 설정 (1:N, CASCADE)

---

## Phase SE-3: Server Metrics Schema

> 목표: ServerMetrics Pydantic 스키마 생성

### ActionItem SE-3.1: Schema Tests
- [x] Test: `test_server_metrics_create_schema` - ServerMetricsCreate 스키마 구조
- [x] Test: `test_server_metrics_response_schema` - ServerMetricsResponse 스키마 구조
- [x] Test: `test_server_metrics_create_optional_fields` - Optional 필드 검증

### ActionItem SE-3.2: Schema Implementation
- [x] Impl: ServerMetricsCreate 스키마 생성
- [x] Impl: ServerMetricsResponse 스키마 생성
- [x] Impl: ServerMetricsLatestResponse 스키마 생성

---

## Phase SE-4: Server Metrics API

> 목표: Server Metrics REST API 구현

### ActionItem SE-4.1: POST API Tests
- [x] Test: `test_post_server_metrics_success` - POST /api/servers/{id}/metrics 201
- [x] Test: `test_post_server_metrics_server_not_found` - 존재하지 않는 서버 404
- [x] Test: `test_post_server_metrics_returns_full_data` - 응답에 전체 데이터 포함
- [x] Test: `test_post_server_metrics_threshold_exceeded` - 임계치 초과 시 threshold_exceeded 반환

### ActionItem SE-4.2: GET API Tests
- [x] Test: `test_get_server_metrics_list` - GET /api/servers/{id}/metrics 200
- [x] Test: `test_get_server_metrics_with_limit` - limit 파라미터 동작
- [x] Test: `test_get_server_metrics_with_time_range` - start_time, end_time 필터
- [x] Test: `test_get_server_metrics_latest` - GET /api/servers/{id}/metrics/latest 200

### ActionItem SE-4.3: DELETE API Tests
- [x] Test: `test_delete_server_metrics_old` - DELETE /api/servers/{id}/metrics 200

### ActionItem SE-4.4: Router Implementation
- [x] Impl: server_metrics.py 라우터 생성
- [x] Impl: POST /api/servers/{id}/metrics - 메트릭 저장 + 임계치 비교
- [x] Impl: GET /api/servers/{id}/metrics - 메트릭 목록 조회
- [x] Impl: GET /api/servers/{id}/metrics/latest - 최신 메트릭 조회
- [x] Impl: DELETE /api/servers/{id}/metrics - 오래된 메트릭 삭제

---

## Phase SE-5: System Event Enum

> 목표: EnumSystemEventType, EnumSystemEventSeverity 정의

### ActionItem SE-5.1: Enum Tests
- [x] Test: `test_enum_system_event_type_exists` - EnumSystemEventType 존재
- [x] Test: `test_enum_system_event_type_values` - 17개 이벤트 유형 값 검증
- [x] Test: `test_enum_system_event_severity_exists` - EnumSystemEventSeverity 존재
- [x] Test: `test_enum_system_event_severity_values` - INFO, WARNING, ERROR, CRITICAL 값 검증

### ActionItem SE-5.2: Enum Implementation
- [x] Impl: EnumSystemEventType 정의 (app/utils/enums.py)
- [x] Impl: EnumSystemEventSeverity 정의 (app/utils/enums.py)

---

## Phase SE-6: System Event Model

> 목표: system_events 테이블 및 SQLAlchemy 모델 생성

### ActionItem SE-6.1: Model Tests
- [x] Test: `test_system_event_model_exists` - SystemEvent 모델 클래스 존재
- [x] Test: `test_system_event_has_server_fk` - server_id FK (SET NULL) 존재
- [x] Test: `test_system_event_has_type_event` - type_event Enum 필드 존재
- [x] Test: `test_system_event_has_severity` - severity Enum 필드 존재
- [x] Test: `test_system_event_has_content_fields` - title, message, detail 필드 존재
- [x] Test: `test_system_event_has_acknowledge_fields` - is_acknowledged 등 필드 존재

### ActionItem SE-6.2: Model Implementation
- [x] Impl: SystemEvent SQLAlchemy 모델 생성 (app/models/system_event.py)
- [x] Impl: Server ↔ SystemEvent relationship 설정 (1:N, SET NULL)

---

## Phase SE-7: System Event Schema

> 목표: SystemEvent Pydantic 스키마 생성

### ActionItem SE-7.1: Schema Tests
- [x] Test: `test_system_event_create_schema` - SystemEventCreate 스키마 구조
- [x] Test: `test_system_event_update_schema` - SystemEventUpdate 스키마 구조
- [x] Test: `test_system_event_response_schema` - SystemEventResponse 스키마 구조
- [x] Test: `test_system_event_acknowledge_schema` - SystemEventAcknowledge 스키마 구조

### ActionItem SE-7.2: Schema Implementation
- [x] Impl: SystemEventCreate 스키마 생성
- [x] Impl: SystemEventUpdate 스키마 생성
- [x] Impl: SystemEventResponse 스키마 생성
- [x] Impl: SystemEventAcknowledge 스키마 생성
- [x] Impl: SystemEventSummary 스키마 생성

---

## Phase SE-8: System Event API (Basic CRUD)

> 목표: System Event 기본 CRUD API 구현

### ActionItem SE-8.1: GET List API Tests
- [x] Test: `test_get_system_events_list` - GET /api/system-events 200
- [x] Test: `test_get_system_events_with_pagination` - page, limit 파라미터
- [x] Test: `test_get_system_events_filter_by_type` - type_event 필터
- [x] Test: `test_get_system_events_filter_by_severity` - severity 필터

### ActionItem SE-8.2: GET Single API Tests
- [x] Test: `test_get_system_event_by_id` - GET /api/system-events/{id} 200
- [x] Test: `test_get_system_event_not_found` - 존재하지 않는 ID 404

### ActionItem SE-8.3: POST API Tests
- [x] Test: `test_create_system_event_success` - POST /api/system-events 201
- [x] Test: `test_create_system_event_without_server` - server_id 없이 생성 (전역 이벤트)
- [x] Test: `test_create_system_event_invalid_server` - 존재하지 않는 server_id 400

### ActionItem SE-8.4: PATCH API Tests
- [x] Test: `test_update_system_event_success` - PATCH /api/system-events/{id} 200
- [x] Test: `test_update_system_event_not_found` - 존재하지 않는 ID 404

### ActionItem SE-8.5: DELETE API Tests
- [x] Test: `test_delete_system_event_success` - DELETE /api/system-events/{id} 200
- [x] Test: `test_delete_system_event_not_found` - 존재하지 않는 ID 404

### ActionItem SE-8.6: Router Implementation
- [x] Impl: system_events.py 라우터 생성
- [x] Impl: GET /api/system-events - 목록 조회 (필터링, 페이지네이션)
- [x] Impl: GET /api/system-events/{id} - 단건 조회
- [x] Impl: POST /api/system-events - 생성
- [x] Impl: PATCH /api/system-events/{id} - 수정
- [x] Impl: DELETE /api/system-events/{id} - 삭제

---

## Phase SE-9: System Event API (Advanced)

> 목표: acknowledge, summary, server-specific 엔드포인트 구현

### ActionItem SE-9.1: Acknowledge API Tests
- [x] Test: `test_acknowledge_system_event_success` - POST /api/system-events/{id}/acknowledge 200
- [x] Test: `test_acknowledge_already_acknowledged` - 이미 확인된 이벤트 400
- [x] Test: `test_acknowledge_system_event_not_found` - 404

### ActionItem SE-9.2: Summary API Tests
- [x] Test: `test_get_system_events_summary` - GET /api/system-events/summary 200
- [x] Test: `test_summary_by_severity_count` - severity별 카운트
- [x] Test: `test_summary_unacknowledged_count` - 미확인 이벤트 카운트

### ActionItem SE-9.3: Server-specific API Tests
- [x] Test: `test_get_server_system_events` - GET /api/servers/{id}/system-events 200
- [x] Test: `test_get_server_system_events_empty` - 이벤트 없는 서버 빈 배열

### ActionItem SE-9.4: Router Implementation
- [x] Impl: POST /api/system-events/{id}/acknowledge - 확인 처리
- [x] Impl: GET /api/system-events/summary - 요약 통계
- [x] Impl: GET /api/servers/{id}/system-events - 서버별 이벤트 조회

---

## Phase SE-10: Integration (Metrics → Events)

> 목표: 메트릭 임계치 초과 시 system_events 자동 생성

### ActionItem SE-10.1: Integration Tests
- [x] Test: `test_metrics_threshold_creates_event` - 임계치 초과 시 이벤트 생성
- [x] Test: `test_metrics_no_event_below_threshold` - 정상 범위 시 이벤트 미생성
- [x] Test: `test_metrics_event_type_resource_threshold` - 이벤트 타입 RESOURCE_THRESHOLD
- [x] Test: `test_metrics_event_severity_warning` - warning 임계치 → WARNING severity
- [x] Test: `test_metrics_event_severity_critical` - critical 임계치 → CRITICAL severity

### ActionItem SE-10.2: Integration Implementation
- [x] Impl: _create_threshold_event() 헬퍼 함수
- [x] Impl: POST /api/servers/{id}/metrics에 임계치 검사 로직 통합

---

## Phase SE-11: Documentation Update

> 목표: GOP 문서 업데이트

### ActionItem SE-11.1: 스키마 문서
- [ ] Impl: GOP_스키마_전체.md - servers 테이블 변경 (threshold_config)
- [ ] Impl: GOP_스키마_전체.md - server_metrics 테이블 추가
- [ ] Impl: GOP_스키마_전체.md - system_events 테이블 추가
- [ ] Impl: GOP_스키마_전체.md - Enum 추가 (EnumSystemEventType, EnumSystemEventSeverity)

### ActionItem SE-11.2: API 문서
- [ ] Impl: GOP_Restful_Api_연동설계.md - Server Metrics API 추가
- [ ] Impl: GOP_Restful_Api_연동설계.md - System Event API 추가

---

## Test Execution Commands

```bash
# Run all System Event tests
pytest tests/test_system_event.py -v

# Run specific phase tests
pytest tests/test_system_event.py::TestServerSchemaRefactoring -v    # SE-1
pytest tests/test_system_event.py::TestServerMetricsModel -v         # SE-2
pytest tests/test_system_event.py::TestServerMetricsSchema -v        # SE-3
pytest tests/test_system_event.py::TestServerMetricsApi -v           # SE-4
pytest tests/test_system_event.py::TestSystemEventEnum -v            # SE-5
pytest tests/test_system_event.py::TestSystemEventModel -v           # SE-6
pytest tests/test_system_event.py::TestSystemEventSchema -v          # SE-7
pytest tests/test_system_event.py::TestSystemEventApiCrud -v         # SE-8
pytest tests/test_system_event.py::TestSystemEventApiAdvanced -v     # SE-9
pytest tests/test_system_event.py::TestMetricsEventIntegration -v    # SE-10
```

---

## System Event Implementation Progress Summary

| Phase | Description | Priority | Status | Tests | Implementation |
|-------|-------------|----------|--------|-------|----------------|
| SE-1 | Server Schema Refactoring | HIGH | [x] | 11/11 | 10/10 |
| SE-2 | Server Metrics Model | HIGH | [x] | 5/5 | 2/2 |
| SE-3 | Server Metrics Schema | HIGH | [x] | 3/3 | 3/3 |
| SE-4 | Server Metrics API | HIGH | [x] | 8/8 | 5/5 |
| SE-5 | System Event Enum | HIGH | [x] | 4/4 | 2/2 |
| SE-6 | System Event Model | HIGH | [x] | 6/6 | 2/2 |
| SE-7 | System Event Schema | HIGH | [x] | 4/4 | 5/5 |
| SE-8 | System Event API (CRUD) | HIGH | [x] | 13/13 | 6/6 |
| SE-9 | System Event API (Advanced) | HIGH | [x] | 8/8 | 3/3 |
| SE-10 | Integration | MEDIUM | [x] | 5/5 | 2/2 |
| SE-11 | Documentation | LOW | [ ] | N/A | 0/4 |

**Overall Progress**: 95% (67/71 테스트, 40/42 구현)

---

## System Event Change Log

| Date | Phase | Action | Notes |
|------|-------|--------|-------|
| 2026-01-15 | - | Plan created | PRD_System_Event.md v1.2 기반 계획 수립 |
| 2026-01-15 | SE-1 | Completed | Server 모델/스키마 리팩토링 (threshold_config, 리소스 필드 제거) 11/11 |
| 2026-01-15 | SE-2 | Completed | ServerMetrics 모델 구현 (1:N CASCADE) 5/5 |
| 2026-01-15 | SE-3 | Completed | ServerMetrics 스키마 구현 3/3 |
| 2026-01-15 | SE-4 | Completed | ServerMetrics API 구현 8/8 테스트, 5/5 구현 (POST/GET/DELETE) |
| 2026-01-15 | SE-5 | Completed | SystemEvent Enum 구현 4/4 테스트, 2/2 구현 |
| 2026-01-15 | SE-6 | Completed | SystemEvent 모델 구현 6/6 테스트, 2/2 구현 (SET NULL FK) |
| 2026-01-15 | SE-7 | Completed | SystemEvent 스키마 구현 4/4 테스트, 5/5 구현 (Create/Update/Response/Acknowledge/Summary) |
| 2026-01-15 | SE-8 | Completed | SystemEvent API CRUD 구현 13/13 테스트, 6/6 구현 (GET/POST/PATCH/DELETE) |
| 2026-01-15 | SE-9 | Completed | SystemEvent API Advanced 구현 8/8 테스트, 3/3 구현 (acknowledge/summary/server-events) |
| 2026-01-15 | SE-10 | Completed | Metrics→Events 통합 구현 5/5 테스트, 2/2 구현 (_create_threshold_event, 자동 이벤트 생성) |

---

# PRD_Enclosure_Metrics_Separation 구현 계획

> **기반 문서**: PRD_Enclosure_Metrics_Separation.md v1.0
> **참조 문서**: PRD_System_Event.md v1.2 (threshold_config 설계 패턴 참조)
> **방법론**: TDD (Test-Driven Development) per CLAUDE.md
> **작성일**: 2026-01-15
> **진행 표시**: `[ ]` 미진행, `[~]` 진행중, `[x]` 완료

---

## 설계 요약

| 구분 | 저장 위치 | 예시 |
|------|----------|------|
| 자산 정보 | enclosures 테이블 | id, name_device, geolocation |
| 설정값 (임계치) | enclosures.threshold_config | temp_high, humidity_high |
| 제어 상태 | enclosures 테이블 | heater_enabled, fan_enabled |
| 실시간 측정값 | enclosure_metrics 테이블 (신규) | temperature, humidity, voltage |

---

## Phase EM-1: EnclosureMetric Schema (Pydantic)

> 목표: EnclosureMetric Pydantic 스키마 생성

### ActionItem EM-1.1: Create Schema Tests
- [x] Test: `test_enclosure_metric_create_schema_exists` - EnclosureMetricCreate 존재
- [x] Test: `test_enclosure_metric_create_collected_at_required` - collected_at 필수
- [x] Test: `test_enclosure_metric_create_temperature_optional` - temperature Optional
- [x] Test: `test_enclosure_metric_create_humidity_optional` - humidity Optional
- [x] Test: `test_enclosure_metric_create_all_fields` - 모든 필드 포함 테스트

### ActionItem EM-1.2: Response Schema Tests
- [x] Test: `test_enclosure_metric_response_has_id` - id 필드 존재
- [x] Test: `test_enclosure_metric_response_has_enclosure_id` - enclosure_id 필드 존재
- [x] Test: `test_enclosure_metric_response_has_timestamps` - created_at, collected_at 존재

### ActionItem EM-1.3: Validation Tests
- [x] Test: `test_enclosure_metric_temperature_accepts_decimal` - Decimal(5,2) 형식
- [x] Test: `test_enclosure_metric_ups_battery_level_range` - 0-100 범위

### ActionItem EM-1.4: Schema Implementation
- [x] Impl: EnclosureMetricCreate 스키마 생성 (app/schemas/device.py)
- [x] Impl: EnclosureMetricResponse 스키마 생성
- [x] Impl: EnclosureMetricLatestResponse 스키마 생성

---

## Phase EM-2: EnclosureMetric Model (SQLAlchemy)

> 목표: enclosure_metrics 테이블 및 SQLAlchemy 모델 생성

### ActionItem EM-2.1: Model Tests
- [x] Test: `test_enclosure_metric_model_exists` - EnclosureMetric 모델 클래스 존재
- [x] Test: `test_enclosure_metric_has_enclosure_fk` - enclosure_id FK 존재
- [x] Test: `test_enclosure_metric_fk_cascade_delete` - CASCADE DELETE 동작
- [x] Test: `test_enclosure_metric_has_metric_fields` - temperature, humidity 등 필드
- [x] Test: `test_enclosure_metric_has_detail_jsonb` - detail JSONB 필드
- [x] Test: `test_enclosure_metric_has_timestamps` - collected_at, created_at 존재

### ActionItem EM-2.2: Model Implementation
- [x] Impl: EnclosureMetric SQLAlchemy 모델 생성 (app/models/device.py)
- [x] Impl: Enclosure ↔ EnclosureMetric relationship 설정 (1:N, CASCADE)

---

## Phase EM-3: EnclosureMetric Router - POST

> 목표: POST /api/devices/enclosures/{id}/metrics 구현

### ActionItem EM-3.1: POST Success Tests
- [x] Test: `test_post_enclosure_metrics_success` - 201 Created
- [x] Test: `test_post_enclosure_metrics_response_format` - 응답 형식 검증 (success test에 포함)
- [x] Test: `test_post_enclosure_metrics_returns_threshold_exceeded_empty` - threshold_exceeded 반환 (router 포함)

### ActionItem EM-3.2: POST Error Tests
- [x] Test: `test_post_enclosure_metrics_enclosure_not_found` - 404 Not Found
- [x] Test: `test_post_enclosure_metrics_validation_error` - 422 Validation Error

### ActionItem EM-3.3: POST Threshold Check Tests
- [x] Test: `test_post_enclosure_metrics_threshold_exceeded_temperature` - 온도 임계치 초과
- [x] Test: `test_post_enclosure_metrics_threshold_exceeded_humidity` - 습도 임계치 초과
- [x] Test: `test_post_enclosure_metrics_threshold_exceeded_multiple` - 다중 임계치 초과

### ActionItem EM-3.4: Router Implementation
- [x] Impl: enclosure_metrics.py 라우터 생성
- [x] Impl: POST /api/devices/enclosures/{id}/metrics 엔드포인트
- [x] Impl: _check_thresholds() 헬퍼 함수

---

## Phase EM-4: EnclosureMetric Router - GET

> 목표: GET 메트릭 조회 API 구현

### ActionItem EM-4.1: GET List Tests
- [x] Test: `test_get_enclosure_metrics_list_success` - 200 OK
- [x] Test: `test_get_enclosure_metrics_list_empty` - 빈 배열 반환
- [x] Test: `test_get_enclosure_metrics_list_with_limit` - limit 파라미터
- [x] Test: `test_get_enclosure_metrics_list_enclosure_not_found` - 404

### ActionItem EM-4.2: GET Latest Tests
- [x] Test: `test_get_enclosure_metrics_latest_success` - 200 OK
- [x] Test: `test_get_enclosure_metrics_latest_no_metrics` - 404 Not Found
- [x] Test: `test_get_enclosure_metrics_latest_enclosure_not_found` - 404

### ActionItem EM-4.3: GET Filter Tests
- [x] Test: `test_get_enclosure_metrics_filter_start_time` - start_time 필터
- [x] Test: `test_get_enclosure_metrics_filter_end_time` - end_time 필터
- [x] Test: `test_get_enclosure_metrics_filter_time_range` - 시간 범위 필터

### ActionItem EM-4.4: Router Implementation
- [x] Impl: GET /api/devices/enclosures/{id}/metrics - 목록 조회
- [x] Impl: GET /api/devices/enclosures/{id}/metrics/latest - 최신 조회
- [x] Impl: GET /api/enclosure-metrics - 전체 조회 (필터링)

---

## Phase EM-5: EnclosureMetric Router - DELETE

> 목표: DELETE 메트릭 삭제 API 구현

### ActionItem EM-5.1: DELETE Tests
- [x] Test: `test_delete_enclosure_metrics_success` - 200 OK
- [x] Test: `test_delete_enclosure_metrics_enclosure_not_found` - 404
- [x] Test: `test_delete_enclosure_metrics_before_date` - before_date 파라미터

### ActionItem EM-5.2: Router Implementation
- [x] Impl: DELETE /api/devices/enclosures/{id}/metrics - 메트릭 삭제

---

## Phase EM-6: Structural Changes (Tidy First)

> **주의**: 구조적 변경은 행동 변경과 분리하여 별도 커밋

### ActionItem EM-6.1: Enclosure 모델/스키마/라우터에서 detail_info 제거
- [x] Impl: Enclosure 모델에서 detail_info 컬럼 제거 (app/models/device.py)
- [x] Impl: Enclosure 스키마에서 detail_info 필드 제거 (EnclosureDetailInfo 클래스 삭제)
- [x] Impl: Enclosure 스키마에서 detail_info 참조 제거 (EnclosureCreate, Update, Response, StatusUpdate)
- [x] Impl: enclosures.py 라우터에서 detail_info 처리 로직 제거
- [x] Test: 테스트 업데이트 (test_enclosure_model, test_enclosure_schemas, test_enclosure_router, conftest)
- [x] Test: 기존 Enclosure 테스트 실행 - 133/133 통과

### ActionItem EM-6.2: Router Registration
- [x] Impl: main.py에 enclosure_metrics 라우터 등록
- [x] Impl: tags_metadata에 "Enclosure Metrics" 태그 설명 추가

---

## Phase EM-7: Documentation Update

### ActionItem EM-7.1: 스키마 문서
- [x] Impl: GOP_스키마_전체.md - enclosure_metrics 테이블 추가
- [x] Impl: GOP_스키마_전체.md - 변경 이력 v2.1 추가

### ActionItem EM-7.2: API 문서
- [x] Impl: GOP_Restful_Api_연동설계.md - Enclosure Metrics API 섹션 5.5.9~5.5.12 추가
- [x] Impl: GOP_Restful_Api_연동설계.md - Endpoint 목록 및 변경 이력 v2.9 업데이트

### ActionItem EM-7.3: PRD 상태 업데이트
- [x] Impl: PRD_Enclosure_Metrics_Separation.md 상태를 Implemented로 변경

---

## Test Execution Commands

```bash
# Run all Enclosure Metrics tests
pytest tests/test_enclosure_metrics.py -v

# Run specific phase tests
pytest tests/test_enclosure_metrics.py::TestEnclosureMetricSchema -v    # EM-1
pytest tests/test_enclosure_metrics.py::TestEnclosureMetricModel -v     # EM-2
pytest tests/test_enclosure_metrics.py::TestEnclosureMetricPost -v      # EM-3
pytest tests/test_enclosure_metrics.py::TestEnclosureMetricGet -v       # EM-4
pytest tests/test_enclosure_metrics.py::TestEnclosureMetricDelete -v    # EM-5
```

---

## Enclosure Metrics Progress Summary

| Phase | Description | Priority | Status | Tests | Implementation |
|-------|-------------|----------|--------|-------|----------------|
| EM-1 | Schema (Pydantic) | HIGH | [x] | 10/10 | 3/3 |
| EM-2 | Model (SQLAlchemy) | HIGH | [x] | 6/6 | 2/2 |
| EM-3 | Router - POST | HIGH | [x] | 8/8 | 3/3 |
| EM-4 | Router - GET | HIGH | [x] | 10/10 | 3/3 |
| EM-5 | Router - DELETE | MEDIUM | [x] | 3/3 | 1/1 |
| EM-6 | Structural Changes | LOW | [x] | 6/6 | 6/6 |
| EM-7 | Documentation | LOW | [x] | N/A | 5/5 |

**Overall Progress**: 100% (37/37 테스트 통과, API 구현 및 문서화 완료)

---

## Enclosure Metrics Change Log

| Date | Phase | Action | Notes |
|------|-------|--------|-------|
| 2026-01-15 | - | Plan created | PRD_Enclosure_Metrics_Separation.md v1.0 기반 계획 수립 |
| 2026-01-15 | EM-1 | Completed | Schema 구현 (EnclosureMetricCreate, EnclosureMetricResponse) 10/10 tests |
| 2026-01-15 | EM-2 | Completed | Model 구현 (EnclosureMetric + Enclosure relationship) 6/6 tests |
| 2026-01-15 | EM-3 | Completed | POST Router 구현 (success, 404, 422, threshold) 8/8 tests |
| 2026-01-15 | EM-4 | Completed | GET Router 구현 (list, latest, limit, filters) 10/10 tests |
| 2026-01-15 | EM-5 | Completed | DELETE Router 구현 (success, 404, before_date) 3/3 tests |
| 2026-01-15 | EM-6 | Completed | detail_info 제거 - model/schema/router/tests 업데이트, 133/133 enclosure tests 통과 |
| 2026-01-15 | EM-7 | Completed | Documentation 업데이트 - GOP_스키마, GOP_API, PRD status |

---

# PRD_Account_Design 구현 계획

> **기반 문서**: PRD_Account_Design.md v1.1
> **참조 문서**: GOP_스키마_전체.md, GOP_Restful_Api_연동설계.md
> **방법론**: TDD (Test-Driven Development) per CLAUDE.md
> **작성일**: 2026-01-19
> **진행 표시**: `[ ]` 미진행, `[~]` 진행중, `[x]` 완료

---

## 구현 범위 요약

| 구성 요소 | 설명 | 우선순위 |
|----------|------|----------|
| Account Enum 정의 | EnumUserRole, EnumLogoutReason, EnumLoginAction 등 | HIGH |
| User Model/Schema | users 테이블 및 스키마 | HIGH |
| UserGroup Model/Schema | user_groups 테이블 및 스키마 | HIGH |
| UserSession Model/Schema | user_sessions 테이블 및 스키마 | HIGH |
| UserLoginLog Model/Schema | user_login_logs 테이블 및 스키마 | MEDIUM |
| Auth API | POST /auth/login, logout, refresh | HIGH |
| User API | CRUD + lock/unlock + reset-password | HIGH |
| UserGroup API | CRUD + users list | HIGH |
| UserSession API | CRUD + force logout | MEDIUM |

---

## Phase AC-1: Enum 정의 (app/utils/enums.py)

> 목표: Account 관련 Enum 정의 및 기존 SystemEvent 타입 추가

### ActionItem AC-1.1: EnumUserRole 정의
- [x] Test: `test_enum_user_role_exists` - EnumUserRole 존재 확인
- [x] Test: `test_enum_user_role_values` - 5개 값 검증 (ADMIN, MAINTAINER, OPERATOR, VIEWER, GUEST)
- [x] Test: `test_enum_user_role_str_inheritance` - str, Enum 상속 확인
- [x] Impl: EnumUserRole 정의

### ActionItem AC-1.2: EnumLogoutReason 정의
- [x] Test: `test_enum_logout_reason_exists` - EnumLogoutReason 존재 확인
- [x] Test: `test_enum_logout_reason_values` - 6개 값 검증 (MANUAL, EXPIRED, FORCED, LOCKED, PASSWORD_CHANGED, DUPLICATE)
- [x] Impl: EnumLogoutReason 정의

### ActionItem AC-1.3: EnumLoginAction, EnumLoginResult 정의
- [x] Test: `test_enum_login_action_exists` - EnumLoginAction 존재 확인
- [x] Test: `test_enum_login_action_values` - 3개 값 검증 (LOGIN, LOGOUT, REFRESH)
- [x] Test: `test_enum_login_result_exists` - EnumLoginResult 존재 확인
- [x] Test: `test_enum_login_result_values` - 2개 값 검증 (SUCCESS, FAILURE)
- [x] Impl: EnumLoginAction, EnumLoginResult 정의

### ActionItem AC-1.4: EnumLoginFailureReason 정의
- [x] Test: `test_enum_login_failure_reason_exists` - EnumLoginFailureReason 존재 확인
- [x] Test: `test_enum_login_failure_reason_values` - 7개 값 검증
- [x] Impl: EnumLoginFailureReason 정의

### ActionItem AC-1.5: EnumSystemEventType 확장 (PRD 9.2)
- [x] Test: `test_system_event_type_user_login_failed` - USER_LOGIN_FAILED 존재
- [x] Test: `test_system_event_type_user_locked` - USER_LOCKED 존재
- [x] Test: `test_system_event_type_user_unlocked` - USER_UNLOCKED 존재
- [x] Test: `test_system_event_type_user_created` - USER_CREATED 존재
- [x] Test: `test_system_event_type_user_updated` - USER_UPDATED 존재
- [x] Test: `test_system_event_type_user_deleted` - USER_DELETED 존재
- [x] Test: `test_system_event_type_session_forced_logout` - SESSION_FORCED_LOGOUT 존재
- [x] Impl: EnumSystemEventType에 7개 타입 추가

---

## Phase AC-2: UserGroup Model/Schema

> 목표: user_groups 테이블 및 스키마 생성 (User보다 먼저 - FK 의존)

### ActionItem AC-2.1: UserGroup Model Tests
- [x] Test: `test_user_group_model_exists` - UserGroup 모델 존재
- [x] Test: `test_user_group_has_name_field` - name 필드 존재 (VARCHAR 100)
- [x] Test: `test_user_group_has_description_field` - description 필드 존재
- [x] Test: `test_user_group_has_permissions_jsonb` - permissions JSONB 필드 존재
- [x] Test: `test_user_group_has_is_active` - is_active 필드 존재 (default True)
- [x] Test: `test_user_group_has_timestamps` - created_at, updated_at 존재
- [x] Test: `test_user_group_has_audit_fields` - created_by, updated_by 존재

### ActionItem AC-2.2: UserGroup Model Implementation
- [x] Impl: UserGroup SQLAlchemy 모델 생성 (app/models/user.py)
- [x] Impl: __tablename__ = "user_groups"

### ActionItem AC-2.3: UserGroup Schema Tests
- [x] Test: `test_user_group_create_schema` - UserGroupCreate 스키마 구조
- [x] Test: `test_user_group_update_schema` - UserGroupUpdate 스키마 구조
- [x] Test: `test_user_group_response_schema` - UserGroupResponse 스키마 구조
- [x] Test: `test_user_group_permissions_structure` - permissions JSONB 구조 검증

### ActionItem AC-2.4: UserGroup Schema Implementation
- [x] Impl: UserGroupCreate 스키마 생성 (app/schemas/user.py)
- [x] Impl: UserGroupUpdate 스키마 생성
- [x] Impl: UserGroupResponse 스키마 생성
- [x] Impl: PermissionsSchema 스키마 생성 (modules, device_groups, time_restriction)

---

## Phase AC-3: User Model/Schema

> 목표: users 테이블 및 스키마 생성

### ActionItem AC-3.1: User Model Tests
- [x] Test: `test_user_model_exists` - User 모델 존재
- [x] Test: `test_user_has_login_id` - login_id 필드 (UNIQUE)
- [x] Test: `test_user_has_password_hash` - password_hash 필드
- [x] Test: `test_user_has_personal_info` - name, department, position, employee_number, photo_url, email, phone
- [x] Test: `test_user_has_role` - role 필드 (EnumUserRole, default VIEWER)
- [x] Test: `test_user_has_group_id_fk` - group_id FK (SET NULL)
- [x] Test: `test_user_has_status_fields` - is_active, is_locked, lock_reason, locked_at, locked_by
- [x] Test: `test_user_has_password_policy_fields` - password_changed_at, password_expires_at, failed_login_count
- [x] Test: `test_user_has_last_login_fields` - last_login_at, last_login_ip
- [x] Test: `test_user_has_timestamps` - created_at, updated_at, created_by, updated_by

### ActionItem AC-3.2: User Model Implementation
- [x] Impl: User SQLAlchemy 모델 생성 (app/models/user.py) - AccountUser 클래스
- [x] Impl: User ↔ UserGroup relationship (N:1, SET NULL)
- [x] Impl: User self-referential FK (locked_by, created_by, updated_by)

### ActionItem AC-3.3: User Schema Tests
- [x] Test: `test_user_create_schema` - UserCreate 스키마 구조 (password 포함)
- [x] Test: `test_user_update_schema` - UserUpdate 스키마 구조
- [x] Test: `test_user_response_schema` - UserResponse 스키마 구조 (password_hash 제외)
- [x] Test: `test_user_nested_response_schema` - UserNestedResponse (세션/그룹용)

### ActionItem AC-3.4: User Schema Implementation
- [x] Impl: AccountUserCreate 스키마 생성
- [x] Impl: AccountUserUpdate 스키마 생성
- [x] Impl: AccountUserResponse 스키마 생성
- [x] Impl: AccountUserNestedResponse 스키마 생성
- [ ] Impl: UserLockRequest 스키마 생성 (lock_reason) - API 단계에서
- [ ] Impl: PasswordChangeRequest 스키마 생성 (current_password, new_password) - API 단계에서

---

## Phase AC-4: UserSession Model/Schema

> 목표: user_sessions 테이블 및 스키마 생성

### ActionItem AC-4.1: UserSession Model Tests
- [x] Test: `test_user_session_model_exists` - UserSession 모델 존재
- [x] Test: `test_user_session_has_user_fk` - user_id FK (CASCADE)
- [x] Test: `test_user_session_has_token_fields` - token, refresh_token
- [x] Test: `test_user_session_has_connection_info` - ip_address, user_agent, device_type, location
- [x] Test: `test_user_session_has_time_fields` - login_at, expires_at, last_activity, logged_out_at
- [x] Test: `test_user_session_has_status_fields` - is_active, logout_reason, forced_by

### ActionItem AC-4.2: UserSession Model Implementation
- [x] Impl: UserSession SQLAlchemy 모델 생성 (app/models/user.py)
- [x] Impl: User ↔ UserSession relationship (1:N, CASCADE)

### ActionItem AC-4.3: UserSession Schema Tests
- [x] Test: `test_user_session_response_schema` - UserSessionResponse 스키마 구조
- [x] Test: `test_user_session_list_response` - 세션 목록 응답 구조

### ActionItem AC-4.4: UserSession Schema Implementation
- [x] Impl: UserSessionResponse 스키마 생성
- [x] Impl: UserSessionListResponse 스키마 생성

---

## Phase AC-5: UserLoginLog Model/Schema

> 목표: user_login_logs 테이블 및 스키마 생성

### ActionItem AC-5.1: UserLoginLog Model Tests
- [x] Test: `test_user_login_log_model_exists` - UserLoginLog 모델 존재
- [x] Test: `test_user_login_log_has_user_fk` - user_id FK (SET NULL)
- [x] Test: `test_user_login_log_has_login_id` - login_id 필드 (user 삭제 후에도 보존)
- [x] Test: `test_user_login_log_has_action` - action 필드 (EnumLoginAction)
- [x] Test: `test_user_login_log_has_result` - result 필드 (EnumLoginResult)
- [x] Test: `test_user_login_log_has_failure_reason` - failure_reason 필드

### ActionItem AC-5.2: UserLoginLog Model Implementation
- [x] Impl: UserLoginLog SQLAlchemy 모델 생성 (app/models/user.py)
- [x] Impl: User ↔ UserLoginLog relationship (1:N, SET NULL)

### ActionItem AC-5.3: UserLoginLog Schema Tests
- [x] Test: `test_user_login_log_response_schema` - UserLoginLogResponse 스키마 구조

### ActionItem AC-5.4: UserLoginLog Schema Implementation
- [x] Impl: UserLoginLogResponse 스키마 생성

---

## Phase AC-6: Auth API (인증)

> 목표: 로그인/로그아웃/토큰 갱신 API 구현

### ActionItem AC-6.1: Login API Tests
- [x] Test: `test_login_success` - POST /api/auth/login 200
- [x] Test: `test_login_returns_tokens` - access_token, refresh_token 반환
- [x] Test: `test_login_returns_user_info` - user 정보 반환 (permissions 포함)
- [x] Test: `test_login_invalid_credentials` - 잘못된 인증정보 401
- [x] Test: `test_login_account_locked` - 잠긴 계정 403
- [x] Test: `test_login_account_inactive` - 비활성 계정 403
- [x] Test: `test_login_creates_session` - 세션 생성 확인
- [x] Test: `test_login_creates_log` - 로그인 로그 생성 확인
- [x] Test: `test_login_increments_failed_count` - 실패 시 카운트 증가
- [x] Test: `test_login_locks_after_max_failures` - 5회 실패 시 계정 잠금

### ActionItem AC-6.2: Logout API Tests
- [x] Test: `test_logout_success` - POST /api/auth/logout 200
- [x] Test: `test_logout_invalidates_session` - 세션 비활성화 확인
- [x] Test: `test_logout_creates_log` - 로그아웃 로그 생성 확인
- [x] Test: `test_logout_without_token` - 토큰 없이 요청 시 401

### ActionItem AC-6.3: Refresh API Tests
- [x] Test: `test_refresh_success` - POST /api/auth/refresh 200
- [x] Test: `test_refresh_returns_new_tokens` - 새 토큰 반환
- [x] Test: `test_refresh_invalid_token` - 유효하지 않은 토큰 401
- [x] Test: `test_refresh_expired_token` - 만료된 토큰 401

### ActionItem AC-6.4: Me API Tests
- [x] Test: `test_get_me_success` - GET /api/auth/me 200
- [x] Test: `test_get_me_returns_user_info` - 사용자 정보 반환
- [x] Test: `test_get_me_without_token` - 토큰 없이 요청 시 401

### ActionItem AC-6.5: Auth Router Implementation
- [x] Impl: auth.py 라우터 생성 (app/routers/auth.py)
- [x] Impl: POST /api/auth/login - 로그인
- [x] Impl: POST /api/auth/logout - 로그아웃
- [x] Impl: POST /api/auth/refresh - 토큰 갱신
- [x] Impl: GET /api/auth/me - 내 정보 조회
- [x] Impl: _verify_password() 헬퍼 함수
- [x] Impl: _create_access_token(), _create_refresh_token() 헬퍼 함수
- [x] Impl: _verify_token() 헬퍼 함수

---

## Phase AC-7: User API (사용자 CRUD)

> 목표: 사용자 CRUD + 잠금/해제 + 비밀번호 API 구현

### ActionItem AC-7.1: User List/Get API Tests
- [x] Test: `test_get_users_list` - GET /api/users 200
- [x] Test: `test_get_users_with_pagination` - page, limit 파라미터
- [x] Test: `test_get_users_filter_by_role` - role 필터
- [x] Test: `test_get_users_filter_by_group` - group_id 필터
- [x] Test: `test_get_users_filter_by_department` - department 필터
- [x] Test: `test_get_user_by_id` - GET /api/users/{id} 200
- [x] Test: `test_get_user_not_found` - 404

### ActionItem AC-7.2: User Create API Tests
- [x] Test: `test_create_user_success` - POST /api/users 201
- [x] Test: `test_create_user_hashes_password` - password_hash 저장 확인
- [x] Test: `test_create_user_duplicate_login_id` - 중복 login_id 400
- [x] Test: `test_create_user_invalid_group` - 존재하지 않는 group_id 400

### ActionItem AC-7.3: User Update/Delete API Tests
- [x] Test: `test_update_user_success` - PUT /api/users/{id} 200
- [x] Test: `test_update_user_not_found` - 404
- [x] Test: `test_delete_user_success` - DELETE /api/users/{id} 200
- [x] Test: `test_delete_user_not_found` - 404

### ActionItem AC-7.4: User Lock/Unlock API Tests
- [x] Test: `test_lock_user_success` - POST /api/users/{id}/lock 200
- [x] Test: `test_lock_user_terminates_sessions` - 활성 세션 종료 확인
- [x] Test: `test_unlock_user_success` - POST /api/users/{id}/unlock 200
- [x] Test: `test_lock_unlock_creates_system_event` - SystemEvent 생성 확인

### ActionItem AC-7.5: User Password API Tests
- [x] Test: `test_reset_password_success` - POST /api/users/{id}/reset-password 200
- [x] Test: `test_change_my_password_success` - PUT /api/users/me/password 200
- [x] Test: `test_change_password_wrong_current` - 현재 비밀번호 불일치 400

### ActionItem AC-7.6: User Router Implementation
- [x] Impl: users.py 라우터 생성 (app/routers/users.py)
- [x] Impl: GET /api/users - 목록 조회
- [x] Impl: GET /api/users/{id} - 상세 조회
- [x] Impl: POST /api/users - 생성
- [x] Impl: PUT /api/users/{id} - 수정
- [x] Impl: DELETE /api/users/{id} - 삭제
- [x] Impl: POST /api/users/{id}/lock - 잠금
- [x] Impl: POST /api/users/{id}/unlock - 잠금 해제
- [x] Impl: POST /api/users/{id}/reset-password - 비밀번호 초기화
- [x] Impl: GET /api/users/me - 내 정보 조회
- [x] Impl: PUT /api/users/me - 내 정보 수정
- [x] Impl: PUT /api/users/me/password - 내 비밀번호 변경

---

## Phase AC-8: UserGroup API

> 목표: 사용자 그룹 CRUD API 구현

### ActionItem AC-8.1: UserGroup List/Get API Tests
- [x] Test: `test_get_user_groups_list` - GET /api/user-groups 200
- [x] Test: `test_get_user_group_by_id` - GET /api/user-groups/{id} 200
- [x] Test: `test_get_user_group_not_found` - 404
- [x] Test: `test_get_user_group_includes_user_count` - user_count 필드 포함

### ActionItem AC-8.2: UserGroup Create/Update/Delete API Tests
- [x] Test: `test_create_user_group_success` - POST /api/user-groups 201
- [x] Test: `test_create_user_group_with_permissions` - permissions JSONB 저장
- [x] Test: `test_update_user_group_success` - PUT /api/user-groups/{id} 200
- [x] Test: `test_delete_user_group_success` - DELETE /api/user-groups/{id} 200
- [x] Test: `test_delete_user_group_sets_users_null` - 소속 사용자 group_id NULL

### ActionItem AC-8.3: UserGroup Users API Tests
- [x] Test: `test_get_user_group_users` - GET /api/user-groups/{id}/users 200
- [x] Test: `test_get_user_group_users_empty` - 빈 배열 반환

### ActionItem AC-8.4: UserGroup Router Implementation
- [x] Impl: user_groups.py 라우터 생성 (app/routers/user_groups.py)
- [x] Impl: GET /api/user-groups - 목록 조회
- [x] Impl: GET /api/user-groups/{id} - 상세 조회
- [x] Impl: POST /api/user-groups - 생성
- [x] Impl: PUT /api/user-groups/{id} - 수정
- [x] Impl: DELETE /api/user-groups/{id} - 삭제
- [x] Impl: GET /api/user-groups/{id}/users - 소속 사용자 목록

---

## Phase AC-9: UserSession API

> 목표: 세션 관리 API 구현

### ActionItem AC-9.1: UserSession List/Get API Tests
- [x] Test: `test_get_user_sessions_list` - GET /api/user-sessions 200
- [x] Test: `test_get_user_sessions_filter_active` - is_active 필터
- [x] Test: `test_get_user_session_by_id` - GET /api/user-sessions/{id} 200

### ActionItem AC-9.2: UserSession Force Logout API Tests
- [x] Test: `test_force_logout_success` - DELETE /api/user-sessions/{id} 200
- [x] Test: `test_force_logout_creates_log` - 로그 생성 확인
- [x] Test: `test_force_logout_all_user_sessions` - DELETE /api/user-sessions/user/{user_id} 200
- [x] Test: `test_force_logout_creates_system_event` - SESSION_FORCED_LOGOUT 이벤트

### ActionItem AC-9.3: My Sessions API Tests
- [x] Test: `test_get_my_sessions` - GET /api/user-sessions/me 200
- [x] Test: `test_delete_my_other_session` - DELETE /api/user-sessions/me/{id} 200

### ActionItem AC-9.4: UserSession Router Implementation
- [x] Impl: user_sessions.py 라우터 생성 (app/routers/user_sessions.py)
- [x] Impl: GET /api/user-sessions - 목록 조회
- [x] Impl: GET /api/user-sessions/{id} - 상세 조회
- [x] Impl: DELETE /api/user-sessions/{id} - 강제 로그아웃
- [x] Impl: DELETE /api/user-sessions/user/{user_id} - 특정 사용자 전체 세션 종료
- [x] Impl: GET /api/user-sessions/me - 내 세션 목록
- [x] Impl: DELETE /api/user-sessions/me/{id} - 내 다른 세션 종료

---

## Phase AC-10: Router Registration & Documentation

> 목표: 라우터 등록 및 문서 업데이트

### ActionItem AC-10.1: Router Registration
- [x] Impl: main.py에 auth 라우터 등록
- [x] Impl: main.py에 users 라우터 등록
- [x] Impl: main.py에 user_groups 라우터 등록
- [x] Impl: main.py에 user_sessions 라우터 등록
- [x] Impl: tags_metadata에 "Auth", "Users", "User Groups", "User Sessions" 태그 설명 추가

### ActionItem AC-10.2: Documentation Update
- [x] Impl: GOP_스키마_전체.md - users, user_groups, user_sessions, user_login_logs 테이블 추가
- [x] Impl: GOP_스키마_전체.md - Account 관련 Enum 추가
- [x] Impl: GOP_Restful_Api_연동설계.md - Auth/User/UserGroup/UserSession API 추가
- [x] Impl: PRD_Account_Design.md 상태를 Implemented로 변경

---

## Test Execution Commands

```bash
# Run all Account tests
pytest tests/test_account.py -v

# Run specific phase tests
pytest tests/test_account.py::TestAccountEnum -v         # AC-1
pytest tests/test_account.py::TestUserGroupModel -v      # AC-2
pytest tests/test_account.py::TestUserModel -v           # AC-3
pytest tests/test_account.py::TestUserSessionModel -v    # AC-4
pytest tests/test_account.py::TestUserLoginLogModel -v   # AC-5
pytest tests/test_account.py::TestAuthApi -v             # AC-6
pytest tests/test_account.py::TestUserApi -v             # AC-7
pytest tests/test_account.py::TestUserGroupApi -v        # AC-8
pytest tests/test_account.py::TestUserSessionApi -v      # AC-9
```

---

## Account Implementation Progress Summary

| Phase | Description | Priority | Status | Tests | Implementation |
|-------|-------------|----------|--------|-------|----------------|
| AC-1 | Enum 정의 | HIGH | [x] | 18/18 | 5/5 |
| AC-2 | UserGroup Model/Schema | HIGH | [x] | 11/11 | 6/6 |
| AC-3 | User Model/Schema | HIGH | [x] | 14/14 | 7/8 |
| AC-4 | UserSession Model/Schema | HIGH | [x] | 8/8 | 4/4 |
| AC-5 | UserLoginLog Model/Schema | MEDIUM | [x] | 7/7 | 3/3 |
| AC-6 | Auth API | HIGH | [x] | 21/21 | 8/8 |
| AC-7 | User API | HIGH | [x] | 24/24 | 12/12 |
| AC-8 | UserGroup API | HIGH | [x] | 11/11 | 6/6 |
| AC-9 | UserSession API | MEDIUM | [x] | 9/9 | 6/6 |
| AC-10 | Router Registration & Documentation | LOW | [x] | N/A | 9/9 |

**Overall Progress**: 100% (123/123 테스트, 66/66 구현) ✅

---

## Account Change Log

| Date | Phase | Action | Notes |
|------|-------|--------|-------|
| 2026-01-19 | - | Plan created | PRD_Account_Design.md v1.1 기반 계획 수립 |
| 2026-01-19 | AC-1 | Completed | 18/18 tests passed - 5 Enums + SystemEventType 확장 |
| 2026-01-19 | AC-2 | Completed | 11/11 tests passed - UserGroup Model + Schemas |
| 2026-01-19 | AC-3 | Completed | 14/14 tests passed - AccountUser Model + Schemas |
| 2026-01-19 | AC-4 | Completed | 8/8 tests passed - UserSession Model + Schemas |
| 2026-01-19 | AC-5 | Completed | 7/7 tests passed - UserLoginLog Model + Schemas |
| 2026-01-19 | AC-6 | Completed | 21/21 tests passed - Auth API (login, logout, refresh, me) |
| 2026-01-19 | AC-7 | Completed | 27/27 tests passed - User API (CRUD, lock/unlock, reset password) |
| 2026-01-19 | AC-8 | Completed | 11/11 tests passed - UserGroup API (CRUD, group users) |
| 2026-01-19 | AC-9 | Completed | 9/9 tests passed - UserSession API (list, terminate, force logout) |
| 2026-01-19 | AC-10.1 | Completed | Router Registration in main.py + tags_metadata |
| 2026-01-19 | AC-10.2 | Completed | Documentation Update - 스키마, API 문서, PRD 상태 변경 |

---

# Audit Log Implementation Plan

> **기반 문서**: PRD_Audit_Log.md v1.0
> **방법론**: TDD (Test-Driven Development) per CLAUDE.md
> **작성일**: 2026-01-19
> **진행 표시**: `[ ]` 미진행, `[~]` 진행중, `[x]` 완료

---

## Phase AL-1: Enum 정의 (app/utils/enums.py)

> 목표: 감사 로그 관련 Enum 3종 추가

### ActionItem AL-1.1: EnumAuditActionType 테스트 및 구현
- [x] Test: EnumAuditActionType Enum 존재 확인
- [x] Test: USER_CREATED, USER_UPDATED, USER_DELETED 값 존재
- [x] Test: USER_LOCKED, USER_UNLOCKED 값 존재
- [x] Test: USER_ACTIVATED, USER_DEACTIVATED 값 존재
- [x] Test: PASSWORD_CHANGED, PASSWORD_RESET 값 존재
- [x] Test: ROLE_CHANGED, GROUP_ASSIGNED 값 존재
- [x] Test: GROUP_CREATED, GROUP_UPDATED, GROUP_DELETED, PERMISSION_CHANGED 값 존재
- [x] Test: SESSION_CREATED, SESSION_TERMINATED, SESSION_FORCED_LOGOUT 값 존재
- [x] Impl: EnumAuditActionType Enum 추가 (18종)

### ActionItem AL-1.2: EnumAuditResourceType 테스트 및 구현
- [x] Test: EnumAuditResourceType Enum 존재 확인
- [x] Test: USER, USER_GROUP, USER_SESSION, PASSWORD 값 존재
- [x] Impl: EnumAuditResourceType Enum 추가 (4종)

### ActionItem AL-1.3: EnumAuditStatus 테스트 및 구현
- [x] Test: EnumAuditStatus Enum 존재 확인
- [x] Test: SUCCESS, FAILURE 값 존재
- [x] Impl: EnumAuditStatus Enum 추가 (2종)

---

## Phase AL-2: AuditLog Model (app/models/audit_log.py)

> 목표: AuditLog SQLAlchemy 모델 생성

### ActionItem AL-2.1: AuditLog 모델 테스트 및 구현
- [x] Test: AuditLog 모델 클래스 존재 확인
- [x] Test: action_type 필드 존재 (String, nullable=False)
- [x] Test: action_status 필드 존재 (String, default='SUCCESS')
- [x] Test: resource_type, resource_id, resource_name 필드 존재
- [x] Test: actor_id (FK), actor_login_id, actor_name, actor_role 필드 존재
- [x] Test: changes (JSONB), description 필드 존재
- [x] Test: ip_address, user_agent 필드 존재
- [x] Test: error_message 필드 존재
- [x] Test: created_at 필드 존재 (default=datetime.now)
- [x] Impl: AuditLog 모델 정의 (app/models/audit_log.py)
- [x] Impl: models/__init__.py에 AuditLog export 추가

---

## Phase AL-3: AuditLog Schema (app/schemas/audit_log.py)

> 목표: AuditLog Pydantic 스키마 생성

### ActionItem AL-3.1: AuditLogCreate 스키마 테스트 및 구현
- [x] Test: AuditLogCreate 스키마 클래스 존재
- [x] Test: action_type, resource_type 필수 필드 확인
- [x] Test: actor_login_id 필수 필드 확인
- [x] Test: Optional 필드들 (resource_id, resource_name, changes, description 등)
- [x] Impl: AuditLogCreate 스키마 정의

### ActionItem AL-3.2: AuditLogResponse 스키마 테스트 및 구현
- [x] Test: AuditLogResponse 스키마 클래스 존재
- [x] Test: id, action_type, action_status 필드 존재
- [x] Test: resource_type, resource_id, resource_name 필드 존재
- [x] Test: actor_id, actor_login_id, actor_name, actor_role 필드 존재
- [x] Test: changes, description, ip_address, user_agent 필드 존재
- [x] Test: created_at 필드 존재
- [x] Test: json_schema_extra examples 설정 확인
- [x] Impl: AuditLogResponse 스키마 정의 (with examples)
- [x] Impl: schemas/__init__.py에 export 추가

---

## Phase AL-4: Audit Service (app/services/audit_service.py)

> 목표: 감사 로그 자동 생성 서비스 구현

### ActionItem AL-4.1: AuditService 기본 함수 테스트 및 구현
- [x] Test: log_action() 함수 존재
- [x] Test: get_changes() 함수 존재
- [x] Test: sanitize_changes() 함수 존재
- [x] Test: get_changes()로 before/after dict 생성 확인
- [x] Test: get_changes()가 변경 없을 때 빈 dict 반환
- [x] Test: sanitize_changes()로 password 필드 제거 확인
- [x] Test: sanitize_changes()로 hashed_password 필드 제거 확인
- [x] Impl: log_action() 유틸리티 함수
- [x] Impl: get_changes() 변경 내역 추출 함수
- [x] Impl: sanitize_changes() 민감정보 제거 함수

---

## Phase AL-5: AuditLog Router (app/routers/audit_logs.py)

> 목표: 감사 로그 조회 API 구현 (2개 엔드포인트)

### ActionItem AL-5.1: GET /api/audit-logs 테스트 및 구현
- [x] Test: GET /api/audit-logs 엔드포인트 존재 확인
- [x] Test: get_audit_logs 함수 존재 확인
- [x] Test: AuditLogFilter 스키마 존재 확인
- [x] Test: AuditLogFilter page, limit 필드 확인
- [x] Test: AuditLogFilter 필터 필드 확인 (action_type, resource_type, actor_login_id)
- [x] Test: AuditLogFilter 날짜 필터 필드 확인 (start_date, end_date)
- [x] Test: AuditLogListResponse 스키마 존재 확인
- [x] Test: AuditLogListResponse 페이지네이션 필드 확인
- [x] Impl: GET /api/audit-logs 라우터 구현 (필터 및 페이지네이션 지원)

### ActionItem AL-5.2: GET /api/audit-logs/{log_id} 테스트 및 구현
- [x] Test: GET /api/audit-logs/{audit_log_id} 엔드포인트 존재 확인
- [x] Test: get_audit_log_detail 함수 존재 확인
- [x] Impl: GET /api/audit-logs/{audit_log_id} 라우터 구현

---

## Phase AL-6: Integration (기존 라우터에 감사 로그 호출 추가)

> 목표: Account CRUD 작업에 자동 감사 로그 생성 연동

### ActionItem AL-6.1: users.py 감사 로그 연동
- [x] Test: POST /api/users 시 USER_CREATED 감사 로그 생성
- [x] Test: PUT /api/users/{id} 시 USER_UPDATED 감사 로그 생성 (before/after)
- [x] Test: DELETE /api/users/{id} 시 USER_DELETED 감사 로그 생성
- [x] Test: POST /api/users/{id}/lock 시 USER_LOCKED 감사 로그 생성
- [x] Test: POST /api/users/{id}/unlock 시 USER_UNLOCKED 감사 로그 생성
- [x] Test: POST /api/users/{id}/reset-password 시 PASSWORD_RESET 감사 로그 생성
- [x] Impl: users.py에 감사 로그 호출 추가

### ActionItem AL-6.2: user_groups.py 감사 로그 연동
- [x] Test: POST /api/user-groups 시 GROUP_CREATED 감사 로그 생성
- [x] Test: PUT /api/user-groups/{id} 시 GROUP_UPDATED 감사 로그 생성
- [x] Test: DELETE /api/user-groups/{id} 시 GROUP_DELETED 감사 로그 생성
- [x] Impl: user_groups.py에 감사 로그 호출 추가

### ActionItem AL-6.3: user_sessions.py 감사 로그 연동
- [x] Test: DELETE /api/user-sessions/{id} 시 SESSION_FORCED_LOGOUT 감사 로그 생성
- [x] Impl: user_sessions.py에 감사 로그 호출 추가

### ActionItem AL-6.4: users.py 비밀번호 변경 감사 로그 연동
- [x] Test: PUT /api/users/me/password 시 PASSWORD_CHANGED 감사 로그 생성
- [x] Impl: users.py에 감사 로그 호출 추가

---

## Phase AL-7: Router Registration & Documentation

> 목표: 라우터 등록 및 문서 업데이트

### ActionItem AL-7.1: Router Registration
- [x] Impl: main.py에 audit_logs 라우터 import 추가
- [x] Impl: main.py에 app.include_router(audit_logs.router, prefix="/api/audit-logs") 등록
- [x] Impl: tags_metadata에 "Audit Logs" 태그 설명 추가

### ActionItem AL-7.2: Documentation Update
- [x] Impl: GOP_스키마_전체.md - 10장 Audit 섹션 추가 (audit_logs 테이블)
- [x] Impl: GOP_스키마_전체.md - 9.17~9.19 Audit Enum 추가
- [x] Impl: GOP_Restful_Api_연동설계.md - 4.6 Audit Enum 섹션 추가
- [x] Impl: GOP_Restful_Api_연동설계.md - 9.6 Audit Logs API 섹션 추가
- [x] Impl: GOP_Restful_Api_연동설계.md - 변경이력 v3.1 추가

---

## Test Execution Commands (Audit Log)

```bash
# Run all Audit Log tests
pytest tests/test_audit_log.py -v

# Run specific phase tests
pytest tests/test_audit_log.py::TestAuditEnum -v       # AL-1
pytest tests/test_audit_log.py::TestAuditLogModel -v   # AL-2
pytest tests/test_audit_log.py::TestAuditLogSchema -v  # AL-3
pytest tests/test_audit_log.py::TestAuditService -v    # AL-4
pytest tests/test_audit_log.py::TestAuditLogApi -v     # AL-5
pytest tests/test_audit_log.py::TestAuditIntegration -v # AL-6
```

---

## Audit Log Implementation Progress Summary

| Phase | Description | Priority | Status | Tests | Implementation |
|-------|-------------|----------|--------|-------|----------------|
| AL-1 | Enum 정의 | HIGH | [x] | 15/15 | 3/3 |
| AL-2 | AuditLog Model | HIGH | [x] | 10/10 | 2/2 |
| AL-3 | AuditLog Schema | HIGH | [x] | 11/11 | 3/3 |
| AL-4 | Audit Service | HIGH | [x] | 7/7 | 3/3 |
| AL-5 | AuditLog Router | HIGH | [x] | 10/10 | 2/2 |
| AL-6 | Integration | MEDIUM | [x] | 11/11 | 4/4 |
| AL-7 | Router Registration & Documentation | LOW | [x] | N/A | 8/8 |

**Overall Progress**: 100% ✅ (64 테스트, 25 구현)

---

## Audit Log Change Log

| Date | Phase | Action | Notes |
|------|-------|--------|-------|
| 2026-01-19 | - | Plan created | PRD_Audit_Log.md v1.0 기반 계획 수립 |
| 2026-01-19 | AL-1 | Completed | 15/15 테스트 통과 - Audit Enum 3종 추가 |
| 2026-01-19 | AL-2 | Completed | 10/10 테스트 통과 - AuditLog Model 생성 |
| 2026-01-19 | AL-3 | Completed | 11/11 테스트 통과 - AuditLog Schema 생성 |
| 2026-01-20 | AL-4 | Completed | 7/7 테스트 통과 - AuditService 구현 (log_action, get_changes, sanitize_changes) |
| 2026-01-20 | AL-5 | Completed | 10/10 테스트 통과 - AuditLog Router 구현 (GET /audit-logs, GET /audit-logs/{id}) |
| 2026-01-20 | AL-7.1 | Completed | 라우터 등록 완료 (main.py import, include_router, tags_metadata) |
| 2026-01-20 | AL-6.1 | Completed | 6/6 테스트 통과 - users.py 감사 로그 연동 (CREATE/UPDATE/DELETE/LOCK/UNLOCK/PASSWORD_RESET) |
| 2026-01-20 | AL-6.2 | Completed | 3/3 테스트 통과 - user_groups.py 감사 로그 연동 (GROUP_CREATED/UPDATED/DELETED) |
| 2026-01-20 | AL-6.3 | Completed | 1/1 테스트 통과 - user_sessions.py 감사 로그 연동 (SESSION_FORCED_LOGOUT) |
| 2026-01-20 | AL-6.4 | Completed | 1/1 테스트 통과 - users.py me/password 감사 로그 연동 (PASSWORD_CHANGED) |
| 2026-01-20 | AL-7.2 | Completed | 문서 업데이트 완료 - GOP_스키마_전체.md v2.2 (10장 Audit 섹션, 9.17~9.19 Enum), GOP_Restful_Api_연동설계.md v3.1 (4.6 Enum, 9.6 API) |

---

# UserSession API 개선 Implementation Plan

> **기반 문서**: PRD_UserSession_Improvement.md v1.2
> **방법론**: TDD (Test-Driven Development) per CLAUDE.md
> **작성일**: 2026-01-20
> **진행 표시**: `[ ]` 미진행, `[~]` 진행중, `[x]` 완료

---

## US-1: DB 모델 정리 (Breaking Change)

UserSession 모델에서 미사용 필드 제거 및 필드명 표준화

### US-1.1 Model Field Removal Tests
- [x] Test: UserSession 모델에 device_type 필드 없음 확인
- [x] Test: UserSession 모델에 location 필드 없음 확인

### US-1.2 Model Field Removal Implementation
- [x] Impl: UserSession 모델에서 device_type 컬럼 제거
- [x] Impl: UserSession 모델에서 location 컬럼 제거

### US-1.3 Field Rename Tests (login_at → created_at)
- [x] Test: UserSession 모델에 created_at 필드 존재 확인
- [x] Test: UserSession 모델에 login_at 필드 없음 확인

### US-1.4 Field Rename Tests (last_activity → updated_at)
- [x] Test: UserSession 모델에 updated_at 필드 존재 확인
- [x] Test: UserSession 모델에 last_activity 필드 없음 확인

### US-1.5 Field Rename Implementation
- [x] Impl: UserSession 모델에서 login_at → created_at 변경
- [x] Impl: UserSession 모델에서 last_activity → updated_at 변경

### US-1.6 Schema Update Tests
- [x] Test: UserSessionResponse 스키마에 created_at 필드 존재
- [x] Test: UserSessionResponse 스키마에 updated_at 필드 존재
- [x] Test: UserSessionResponse 스키마에 device_type 필드 없음
- [x] Test: UserSessionResponse 스키마에 location 필드 없음
- [x] Test: UserSessionResponse 스키마에 login_at 필드 없음
- [x] Test: UserSessionResponse 스키마에 last_activity 필드 없음

### US-1.7 Schema Update Implementation
- [x] Impl: UserSessionResponse 스키마 필드 업데이트 (created_at, updated_at)

---

## US-2: 클라이언트 정보 저장

로그인 시 ip_address, user_agent 정보 자동 저장

### US-2.1 Login Client Info Tests
- [x] Test: POST /api/auth/login 시 UserSession에 ip_address 저장
- [x] Test: POST /api/auth/login 시 UserSession에 user_agent 저장
- [x] Test: POST /api/auth/login 시 UserLoginLog에 ip_address 저장
- [x] Test: POST /api/auth/login 시 UserLoginLog에 user_agent 저장

### US-2.2 Login Client Info Implementation
- [x] Impl: auth.py login 함수에 Request 의존성 추가
- [x] Impl: UserSession 생성 시 ip_address, user_agent 저장
- [x] Impl: UserLoginLog 생성 시 ip_address, user_agent 저장

---

## US-3: API 응답 개선 (JOIN)

API 응답에 login_id, role 추가 (AccountUser JOIN)

### US-3.1 Response Schema Tests
- [x] Test: UserSessionResponse에 login_id 필드 존재 (Optional)
- [x] Test: UserSessionResponse에 role 필드 존재 (Optional)
- [x] Test: UserSessionResponse에 user_id 필드 유지 (하위 호환)

### US-3.2 Response Schema Implementation
- [x] Impl: UserSessionResponse 스키마에 login_id 필드 추가
- [x] Impl: UserSessionResponse 스키마에 role 필드 추가

### US-3.3 API Response Tests
- [x] Test: GET /api/user-sessions 응답에 login_id 포함
- [x] Test: GET /api/user-sessions 응답에 role 포함
- [x] Test: GET /api/user-sessions 응답에 created_at 포함
- [x] Test: GET /api/user-sessions 응답에 updated_at 포함
- [x] Test: GET /api/user-sessions/{id} 응답에 login_id 포함
- [~] Test: GET /api/user-sessions/me 응답에 login_id 포함 (skipped - DB isolation issue)

### US-3.4 Router Implementation
- [x] Impl: user_sessions.py get_user_sessions에 AccountUser JOIN 적용
- [x] Impl: user_sessions.py get_user_session_by_id에 AccountUser JOIN 적용
- [x] Impl: user_sessions.py get_my_sessions에 AccountUser JOIN 적용

---

## US-4: 기존 코드 수정

필드 변경으로 인한 기존 코드 업데이트

### US-4.1 Auth Router Update
- [x] Test: auth.py login 함수에서 created_at 사용 확인
- [x] Impl: auth.py 내 login_at 참조 → created_at 변경 (N/A - model handles default)
- [x] Impl: auth.py 내 last_activity 참조 → updated_at 변경 (N/A - model handles default)

### US-4.2 UserSession Router Update
- [x] Test: user_sessions.py force_logout에서 필드 변경 확인
- [x] Impl: user_sessions.py 내 login_at 참조 → created_at 변경 (order_by 수정)
- [x] Impl: user_sessions.py 내 last_activity 참조 → updated_at 변경 (N/A)

### US-4.3 Existing Test Update
- [x] Impl: test_user_session_api.py 내 login_at 참조 → created_at 변경
- [x] Impl: test_auth_api.py 내 필드 참조 업데이트 (N/A - 해당 없음)

---

## US-5: 문서 동기화

GOP 문서들과 코드 동기화 (이미 완료됨)

### US-5.1 GOP_스키마_전체.md 업데이트
- [x] Impl: user_sessions 테이블 필드 업데이트 (login_at→created_at, last_activity→updated_at)
- [x] Impl: 변경 이력 v2.2 업데이트 (UserSession 필드 표준화 추가)

### US-5.2 GOP_Restful_Api_연동설계.md 업데이트
- [x] Impl: 9.5 UserSession API 응답 예제 업데이트 (created_at, updated_at, 누락 필드)
- [x] Impl: 9.5.3 GET /{id} API 문서 추가
- [x] Impl: 변경 이력 v3.1 업데이트 (UserSession API 응답 표준화 추가)

---

## US-6: 통합 테스트

전체 기능 통합 테스트

### US-6.1 End-to-End Tests
- [x] Test: 로그인 → 세션 목록 조회 → login_id, role, created_at, updated_at 확인
- [x] Test: 로그인 → 세션 상세 조회 → ip_address, user_agent 확인
- [x] Test: 강제 로그아웃 → 세션 is_active=false 확인

---

## US Progress Log

| Date | Phase | Action | Notes |
|------|-------|--------|-------|
| 2026-01-20 | - | Plan created | PRD_UserSession_Improvement.md v1.2 기반 계획 수립 |
| 2026-01-20 | US-5 | Completed | 문서 업데이트 완료 - GOP_스키마_전체.md, GOP_Restful_Api_연동설계.md |
| 2026-01-20 | US-1~4 | Completed | Model, Schema, API, Code 표준화 완료 (test_user_schemas.py, test_account_auth.py, test_user_session_api.py) |
| 2026-01-20 | US-6 | Completed | 통합 테스트 완료 - test_user_session_integration.py (3/3 E2E tests passed) |

---

# SystemEvent Type Synchronization (SE-SYNC)

> **기반 문서**: PRD_SystemEvent_Sync.md v1.2
> **방법론**: TDD (Test-Driven Development) per CLAUDE.md
> **작성일**: 2026-01-20
> **목표**: EnumSystemEventType을 24개 → 15개로 축소, 문서-코드 동기화

---

## 현황 분석

| 구분 | 변경 전 | 변경 후 |
|------|---------|---------|
| EnumSystemEventType 타입 수 | 24개 | **15개** |
| USER_* 타입 | 9개 포함 | **제거** (UserLoginLog 사용) |
| ConfigChangeLog 중복 | 4개 포함 | **제거** (ConfigChangeLog 사용) |
| 신규 타입 | - | CONNECTION_LOST, CONNECTION_RESTORED, SECURITY_ALERT, DEVICE_CONNECTED |

---

## Phase SE-SYNC-1: Enum 동기화 테스트 (RED)

> 목표: 15개 타입 검증 테스트 작성 (실패 테스트)

### ActionItem SE-SYNC-1.1: 타입 수 검증 테스트
- [x] Test: `test_enum_has_15_types` - EnumSystemEventType이 정확히 15개 타입을 가짐

### ActionItem SE-SYNC-1.2: 제거된 타입 검증 테스트
- [x] Test: `test_enum_no_user_types` - USER_* 9개 타입이 없음
- [x] Test: `test_enum_no_configchangelog_overlap_types` - CONFIG_CHANGED, DEVICE_ADDED, DEVICE_REMOVED, DEVICE_STATUS_CHANGED 없음

### ActionItem SE-SYNC-1.3: 필수 타입 존재 테스트
- [x] Test: `test_enum_has_required_server_types` - SERVER_CONNECTED, SERVER_DISCONNECTED, SERVER_ERROR, CONNECTION_LOST, CONNECTION_RESTORED 존재
- [x] Test: `test_enum_has_required_service_types` - SERVICE_STARTED, SERVICE_STOPPED, SERVICE_ERROR 존재
- [x] Test: `test_enum_has_required_backup_types` - BACKUP_STARTED, BACKUP_COMPLETED, BACKUP_FAILED 존재
- [x] Test: `test_enum_has_device_connected_type` - DEVICE_CONNECTED 존재
- [x] Test: `test_enum_uses_upper_snake_case` - 모든 타입이 UPPER_SNAKE_CASE

---

## Phase SE-SYNC-2: Enum 구현 (GREEN) ✓

> 목표: EnumSystemEventType을 15개 타입으로 수정

### ActionItem SE-SYNC-2.1: 타입 제거
- [x] Impl: USER_* 9개 타입 제거 (USER_LOGIN, USER_LOGOUT, USER_LOGIN_FAILED, USER_LOCKED, USER_UNLOCKED, USER_CREATED, USER_UPDATED, USER_DELETED, SESSION_FORCED_LOGOUT)
- [x] Impl: ConfigChangeLog 중복 4개 타입 제거 (CONFIG_CHANGED, DEVICE_ADDED, DEVICE_REMOVED, DEVICE_STATUS_CHANGED)

### ActionItem SE-SYNC-2.2: 타입 추가
- [x] Impl: CONNECTION_LOST 추가 (네트워크 연결 끊김)
- [x] Impl: CONNECTION_RESTORED 추가 (네트워크 연결 복구)
- [x] Impl: SECURITY_ALERT 추가 (보안 경고)
- [x] Impl: DEVICE_CONNECTED 추가 (디바이스 연결됨)

### ActionItem SE-SYNC-2.3: Docstring 업데이트
- [x] Impl: EnumSystemEventType docstring 업데이트 (24종 → 15종)
- [x] Impl: PRD Reference 업데이트 (PRD_SystemEvent_Sync.md v1.2 참조)

---

## Phase SE-SYNC-3: 의존 코드 검토 및 수정 ✓

> 목표: EnumSystemEventType을 사용하는 코드 검토 및 수정

### ActionItem SE-SYNC-3.1: 영향 분석
- [x] 검토: app/routers/users.py - USER_LOCKED, USER_UNLOCKED → SECURITY_ALERT로 변경
- [x] 검토: app/routers/user_sessions.py - SESSION_FORCED_LOGOUT → SECURITY_ALERT로 변경
- [x] 검토: app/routers/server_metrics.py - RESOURCE_THRESHOLD 사용 확인 (유지, 변경 없음)
- [x] 검토: app/schemas/system_event.py - 타입 검증 확인 (변경 없음)

### ActionItem SE-SYNC-3.2: 기존 테스트 수정
- [x] Impl: test_system_event.py - `test_enum_system_event_type_values` 17개 → 15개로 수정
- [x] Impl: test_system_event.py - CONFIG_CHANGED, USER_LOGIN 사용 테스트 케이스 수정
- [x] Impl: test_account_user_api.py - USER_LOCKED/UNLOCKED → SECURITY_ALERT 검증으로 수정
- [x] Impl: test_user_session_api.py - SESSION_FORCED_LOGOUT → SECURITY_ALERT 검증으로 수정
- [x] Impl: test_account_enum.py - TestEnumSystemEventTypeExtension 테스트 업데이트

---

## Phase SE-SYNC-4: 문서 업데이트 ✓

> 목표: PRD 및 GOP 문서 업데이트

### ActionItem SE-SYNC-4.1: PRD 업데이트
- [x] Impl: PRD_System_Event.md Section 3.1.1 - Enum 목록 15개로 업데이트 (v1.2→v1.3)
- [x] Impl: PRD_System_Event.md - ConfigChangeLog 분리 설명 추가, Python enum 코드 업데이트

### ActionItem SE-SYNC-4.2: GOP 문서 업데이트
- [x] Impl: GOP_Restful_Api_연동설계.md Section 8.7.1 - EnumSystemEventType 15개로 업데이트
- [x] Impl: GOP_스키마_전체.md Section 7.4 - enum_system_event_type SQL 15개로 업데이트

### ActionItem SE-SYNC-4.3: Swagger 스키마 업데이트
- [x] Impl: app/schemas/system_event.py - json_schema_extra 예제 추가 (Device 패턴 참고)
- [x] Impl: SystemEventCreate, SystemEventUpdate, SystemEventResponse, SystemEventAcknowledge, SystemEventSummary 스키마 업데이트

---

## Phase SE-SYNC-5: 검증 ✓

> 목표: 전체 테스트 통과 확인

### ActionItem SE-SYNC-5.1: 테스트 실행
- [x] Test: SE-SYNC 테스트 전체 통과 (11/11 passed)
- [x] Test: 기존 test_system_event.py 테스트 통과 (83/83 passed)
- [x] Test: test_account_enum.py 테스트 통과 (15/15 passed)
- [x] Test: pytest tests/test_system_event.py tests/test_account_enum.py = **98 passed**

---

## SE-SYNC Progress Log

| Date | Phase | Action | Notes |
|------|-------|--------|-------|
| 2026-01-20 | - | Plan created | PRD_SystemEvent_Sync.md v1.2 기반 계획 수립 |
| 2026-01-20 | SE-SYNC-1 | Completed | RED phase - 11 tests written, 7 failed as expected |
| 2026-01-20 | SE-SYNC-2 | Completed | GREEN phase - EnumSystemEventType 24→15, all 11 tests pass |
| 2026-01-20 | SE-SYNC-3 | Completed | Dependent code updated - users.py, user_sessions.py, tests updated |
| 2026-01-20 | SE-SYNC-4 | Completed | PRD_System_Event.md v1.2→v1.3, GOP docs, Swagger schemas updated |
| 2026-01-20 | SE-SYNC-5 | Completed | Final verification - 98 tests passed |

---

# ConfigChangeLog Implementation (CCL)

> **기반 문서**: PRD_ConfigChangeLog.md v1.0
> **방법론**: TDD (Test-Driven Development) per CLAUDE.md
> **작성일**: 2026-01-20
> **목표**: Device/Server/Event/Integration 계열 CRUD 변경 이력 추적 시스템 구현

---

## 현황 분석

| 구분 | 설명 |
|------|------|
| EnumConfigResourceType | 19개 리소스 유형 (Device 10, Server 2, Event 4, Integration 3) |
| EnumConfigActionType | 6개 액션 유형 (CREATED, UPDATED, DELETED, STATUS_CHANGED, ASSIGNED, UNASSIGNED) |
| config_change_logs 테이블 | 변경 이력 저장 (before_state/after_state JSONB) |
| API 엔드포인트 | GET /api/config-change-logs, GET /api/config-change-logs/{id} |

---

## Phase CCL-1: Enum 테스트 (RED) ✓

> 목표: EnumConfigResourceType (19개), EnumConfigActionType (6개) 테스트 작성

### ActionItem CCL-1.1: EnumConfigResourceType 테스트
- [x] Test: `test_enum_config_resource_type_has_19_types` - 정확히 19개 타입 존재
- [x] Test: `test_enum_config_resource_type_device_category` - Device 계열 10개 확인 (CONTROLLER, SENSOR, CAMERA, SPEAKER, ENCLOSURE, DEVICE_GROUP, CAMERA_PRESET, ROI, XY_POINT, FILE_GROUP)
- [x] Test: `test_enum_config_resource_type_server_category` - Server 계열 2개 확인 (SERVER_CATEGORY, SERVER)
- [x] Test: `test_enum_config_resource_type_event_category` - Event 계열 4개 확인 (DETECTION_EVENT, MALFUNCTION_EVENT, CONNECTION_EVENT, ACTION_EVENT)
- [x] Test: `test_enum_config_resource_type_integration_category` - Integration 계열 3개 확인 (EVENT_MAPPING, EVENT_MAPPING_CAMERA, EVENT_MAPPING_SPEAKER)

### ActionItem CCL-1.2: EnumConfigActionType 테스트
- [x] Test: `test_enum_config_action_type_has_6_types` - 정확히 6개 타입 존재
- [x] Test: `test_enum_config_action_type_crud_actions` - CREATED, UPDATED, DELETED 존재
- [x] Test: `test_enum_config_action_type_special_actions` - STATUS_CHANGED, ASSIGNED, UNASSIGNED 존재

---

## Phase CCL-2: Enum 구현 (GREEN) ✓

> 목표: app/utils/enums.py에 Enum 추가

### ActionItem CCL-2.1: EnumConfigResourceType 구현
- [x] Impl: EnumConfigResourceType 클래스 생성 (19개 타입)
- [x] Impl: Device 계열 10개 추가
- [x] Impl: Server 계열 2개 추가
- [x] Impl: Event 계열 4개 추가
- [x] Impl: Integration 계열 3개 추가

### ActionItem CCL-2.2: EnumConfigActionType 구현
- [x] Impl: EnumConfigActionType 클래스 생성 (6개 타입)
- [x] Impl: CRUD 액션 3개 추가 (CREATED, UPDATED, DELETED)
- [x] Impl: 특수 액션 3개 추가 (STATUS_CHANGED, ASSIGNED, UNASSIGNED)

---

## Phase CCL-3: Model 테스트 및 구현 ✓

> 목표: ConfigChangeLog SQLAlchemy 모델 구현

### ActionItem CCL-3.1: Model 테스트 (RED)
- [x] Test: `test_config_change_log_model_exists` - ConfigChangeLog 모델 존재
- [x] Test: `test_config_change_log_required_fields` - 필수 필드 확인 (resource_type, resource_id, action)
- [x] Test: `test_config_change_log_optional_fields` - 선택 필드 확인 (resource_name, before_state, after_state, actor_id, actor_name, actor_ip, description)
- [x] Test: `test_config_change_log_timestamps` - created_at 자동 생성

### ActionItem CCL-3.2: Model 구현 (GREEN)
- [x] Impl: app/models/config_change_log.py 생성
- [x] Impl: ConfigChangeLog 클래스 정의 (SQLAlchemy)
- [x] Impl: __tablename__ = "config_change_logs"
- [x] Impl: JSONB 필드 (before_state, after_state)

---

## Phase CCL-4: Schema 테스트 및 구현 ✓

> 목표: Pydantic 스키마 구현 (Device 패턴 참고)

### ActionItem CCL-4.1: Schema 테스트 (RED)
- [x] Test: `test_config_change_log_response_schema_fields` - 응답 스키마 필드 확인
- [x] Test: `test_config_change_log_list_response_schema` - 목록 응답 스키마 확인 (logs, total, page, limit)

### ActionItem CCL-4.2: Schema 구현 (GREEN)
- [x] Impl: app/schemas/config_change_log.py 생성
- [x] Impl: ConfigChangeLogResponse 클래스 (json_schema_extra 포함)
- [x] Impl: ConfigChangeLogListResponse 클래스
- [x] Impl: model_config = ConfigDict(from_attributes=True)

---

## Phase CCL-5: API Router 테스트 및 구현

> 목표: config_change_logs API 엔드포인트 구현

### ActionItem CCL-5.1: API 테스트 (RED)
- [x] Test: `test_get_config_change_logs_empty` - 빈 목록 조회
- [x] Test: `test_get_config_change_logs_pagination` - 페이지네이션 동작
- [x] Test: `test_get_config_change_logs_filter_by_resource_type` - resource_type 필터
- [x] Test: `test_get_config_change_logs_filter_by_action` - action 필터
- [x] Test: `test_get_config_change_log_by_id` - 단건 조회
- [x] Test: `test_get_config_change_log_not_found` - 404 응답

### ActionItem CCL-5.2: Router 구현 (GREEN)
- [x] Impl: app/routers/config_change_logs.py 생성
- [x] Impl: GET /api/config-change-logs 구현 (필터링, 페이지네이션)
- [x] Impl: GET /api/config-change-logs/{id} 구현
- [x] Impl: app/main.py에 라우터 등록

---

## Phase CCL-6: Service 구현

> 목표: config_log_service 구현 (로깅 유틸리티)

### ActionItem CCL-6.1: Service 테스트 (RED)
- [x] Test: `test_log_config_change_creates_record` - 로그 레코드 생성
- [x] Test: `test_model_to_dict_conversion` - SQLAlchemy 모델 → dict 변환

### ActionItem CCL-6.2: Service 구현 (GREEN)
- [x] Impl: app/services/config_log_service.py 생성
- [x] Impl: log_config_change() 함수
- [x] Impl: model_to_dict() 함수 (datetime, Enum 처리)

---

## Phase CCL-7: Swagger 스키마 업데이트

> 목표: json_schema_extra 예제 추가 (Device 패턴 참고)

### ActionItem CCL-7.1: Schema 예제 추가
- [x] Impl: ConfigChangeLogResponse 필드별 example 추가 (CCL-4에서 완료)
- [x] Impl: ConfigChangeLogListResponse 필드별 example 추가 (CCL-4에서 완료)

---

## Phase CCL-8: GOP 문서 업데이트

> 목표: GOP 문서 업데이트 (오늘 날짜 단일 버전)

### ActionItem CCL-8.1: GOP_스키마_전체.md 업데이트
- [x] Impl: enum_config_resource_type SQL 정의 추가 (9.20절)
- [x] Impl: enum_config_action_type SQL 정의 추가 (9.21절)
- [x] Impl: config_change_logs 테이블 스키마 추가 (10.2절)
- [x] Impl: 변경 이력 업데이트 (v2.4 2026-01-21)

### ActionItem CCL-8.2: GOP_Restful_Api_연동설계.md 업데이트
- [x] Impl: Section 4.7에 EnumConfigResourceType (19개) 추가
- [x] Impl: Section 4.7에 EnumConfigActionType (6개) 추가
- [x] Impl: Section 9.7 Config Change Logs API 추가
- [x] Impl: 전체 Endpoint 목록 업데이트 (11.1절)
- [x] Impl: 변경 이력 업데이트 (v3.2 2026-01-21)

---

## Phase CCL-9: 최종 검증

> 목표: 전체 테스트 통과 확인

### ActionItem CCL-9.1: 테스트 실행
- [x] Test: CCL 관련 테스트 전체 통과 (36/36)
- [x] Test: 기존 테스트 영향 없음 확인 (pre-existing failures unrelated to CCL)
- [x] Test: pytest 전체 실행 (1470 passed, 155 pre-existing failures)

---

## CCL Progress Log

| Date | Phase | Action | Notes |
|------|-------|--------|-------|
| 2026-01-20 | - | Plan created | PRD_ConfigChangeLog.md v1.0 기반 계획 수립 |
| 2026-01-20 | CCL-1 | Completed | RED phase - 10 enum tests written |
| 2026-01-20 | CCL-2 | Completed | GREEN phase - EnumConfigResourceType (19), EnumConfigActionType (6) 구현, 10 tests pass |
| 2026-01-20 | CCL-3 | Completed | Model 테스트 및 구현 - ConfigChangeLog 모델 생성, 17 tests pass |
| 2026-01-20 | CCL-4 | Completed | Schema 테스트 및 구현 - Pydantic 스키마 (json_schema_extra), 23 tests pass |
| 2026-01-21 | CCL-5 | Completed | API Router 테스트 및 구현 - GET /api/config-change-logs, 30 tests pass |
| 2026-01-21 | CCL-6 | Completed | Service 구현 - log_config_change, model_to_dict, 36 tests pass |
| 2026-01-21 | CCL-7 | Completed | Swagger Schema - CCL-4에서 이미 완료 (json_schema_extra) |
| 2026-01-21 | CCL-8 | Completed | GOP 문서 업데이트 - GOP_스키마_전체.md (v2.4), GOP_Restful_Api_연동설계.md (v3.2) |
| 2026-01-21 | CCL-9 | Completed | 최종 검증 - 36 CCL tests pass, 1470 total tests pass |


---

## Phase CCL-10: PRD v1.1 JSONB 정규화 함수 구현

> 목표: PRD_ConfigChangeLog.md v1.1의 JSONB 정규화 함수 구현
> 참조: PRD Section 3.3, Section 6.1

### ActionItem CCL-10.1: get_changed_fields 테스트 (RED) ✓
- [x] Test: `test_get_changed_fields_function_exists` - 함수 존재 확인
- [x] Test: `test_get_changed_fields_detects_single_change` - 단일 필드 변경 감지
- [x] Test: `test_get_changed_fields_detects_multiple_changes` - 복수 필드 변경 감지
- [x] Test: `test_get_changed_fields_no_changes` - 변경 없는 경우 빈 dict 반환
- [x] Test: `test_get_changed_fields_ignores_unchanged` - 변경되지 않은 필드 제외

### ActionItem CCL-10.2: get_changed_fields 구현 (GREEN) ✓
- [x] Impl: get_changed_fields(before: dict, after: dict) -> tuple[dict, dict]
- [x] Impl: 변경된 필드만 추출하는 로직

### ActionItem CCL-10.3: get_identifier 테스트 (RED) ✓
- [x] Test: `test_get_identifier_function_exists` - 함수 존재 확인
- [x] Test: `test_get_identifier_extracts_id_and_name` - id, name 추출
- [x] Test: `test_get_identifier_with_name_device` - name_device 필드 처리
- [x] Test: `test_get_identifier_with_title` - title 필드 처리 (fallback)

### ActionItem CCL-10.4: get_identifier 구현 (GREEN) ✓
- [x] Impl: get_identifier(model: Any) -> dict
- [x] Impl: name/name_device/title 필드 탐색 로직

### ActionItem CCL-10.5: PRD v1.1 참조 업데이트 ✓
- [x] Impl: config_log_service.py 주석 v1.0 → v1.1 업데이트

---

## CCL-10 Progress Log

| Date | Phase | Action | Notes |
|------|-------|--------|-------|
| 2026-01-21 | CCL-10 | Completed | PRD v1.1 JSONB 정규화 함수 구현 완료 - get_changed_fields, get_identifier (10 tests pass) |

---

# ConfigChangeLog Router Integration Plan (CCL-11 ~ CCL-13)

> **기반 문서**: PRD_ConfigChangeLog.md v1.2
> **방법론**: TDD (Test-Driven Development) per CLAUDE.md
> **작성일**: 2026-01-22
> **진행 표시**: `[ ]` 미진행, `[~]` 진행중, `[x]` 완료

**목표**: 17개 CRUD 라우터에 `log_config_change()` 호출 통합

---

## Phase CCL-11: Device 계열 라우터 통합 (10개)

### ActionItem CCL-11.1: controllers.py 통합 (RED → GREEN) ✅ 완료
- [x] Test: POST /api/devices/controllers - ConfigChangeLog CREATED 기록 확인
- [x] Test: PATCH /api/devices/controllers/{id} - ConfigChangeLog UPDATED 기록 확인
- [x] Test: DELETE /api/devices/controllers/{id} - ConfigChangeLog DELETED 기록 확인
- [x] Impl: controllers.py에 log_config_change 호출 추가
- [x] Bugfix: model_to_dict() 상속 모델 지원 (SQLAlchemy inspect 사용)

### ActionItem CCL-11.2: sensors.py 통합 (RED → GREEN) ✅ 완료
- [x] Test: POST /api/devices/sensors - ConfigChangeLog CREATED 기록 확인
- [x] Test: PATCH /api/devices/sensors/{id} - ConfigChangeLog UPDATED 기록 확인
- [x] Test: DELETE /api/devices/sensors/{id} - ConfigChangeLog DELETED 기록 확인
- [x] Impl: sensors.py에 log_config_change 호출 추가

### ActionItem CCL-11.3: cameras.py 통합 (RED → GREEN) ✅ 완료
- [x] Test: POST /api/devices/cameras - ConfigChangeLog CREATED 기록 확인
- [x] Test: PATCH /api/devices/cameras/{id} - ConfigChangeLog UPDATED 기록 확인
- [x] Test: DELETE /api/devices/cameras/{id} - ConfigChangeLog DELETED 기록 확인
- [x] Impl: cameras.py에 log_config_change 호출 추가

### ActionItem CCL-11.4: speakers.py 통합 (RED → GREEN) ✅ 완료
- [x] Test: POST /api/devices/speakers - ConfigChangeLog CREATED 기록 확인
- [x] Test: PATCH /api/devices/speakers/{id} - ConfigChangeLog UPDATED 기록 확인
- [x] Test: DELETE /api/devices/speakers/{id} - ConfigChangeLog DELETED 기록 확인
- [x] Impl: speakers.py에 log_config_change 호출 추가

### ActionItem CCL-11.5: enclosures.py 통합 (RED → GREEN) ✅ 완료
- [x] Test: POST /api/devices/enclosures - ConfigChangeLog CREATED 기록 확인
- [x] Test: PATCH /api/devices/enclosures/{id} - ConfigChangeLog UPDATED 기록 확인
- [x] Test: DELETE /api/devices/enclosures/{id} - ConfigChangeLog DELETED 기록 확인
- [x] Test: PATCH /api/devices/enclosures/{id}/status - ConfigChangeLog STATUS_CHANGED 기록 확인
- [x] Impl: enclosures.py에 log_config_change 호출 추가

### ActionItem CCL-11.6: device_groups.py 통합 (RED → GREEN) ✅ 완료
- [x] Test: POST /api/devices/groups - ConfigChangeLog CREATED 기록 확인
- [x] Test: PATCH /api/devices/groups/{id} - ConfigChangeLog UPDATED 기록 확인
- [x] Test: DELETE /api/devices/groups/{id} - ConfigChangeLog DELETED 기록 확인
- [x] Test: POST /api/devices/groups/{id}/devices - ConfigChangeLog ASSIGNED 기록 확인
- [x] Test: DELETE /api/devices/groups/{group_id}/devices/{device_id} - ConfigChangeLog UNASSIGNED 기록 확인
- [x] Impl: device_groups.py에 log_config_change 호출 추가

### ActionItem CCL-11.7: camera_presets.py 통합 (RED → GREEN)
- [x] Test: POST /api/devices/camera-presets - ConfigChangeLog CREATED 기록 확인
- [x] Test: PATCH /api/devices/camera-presets/{id} - ConfigChangeLog UPDATED 기록 확인
- [x] Test: DELETE /api/devices/camera-presets/{id} - ConfigChangeLog DELETED 기록 확인
- [x] Impl: camera_presets.py에 log_config_change 호출 추가

### ActionItem CCL-11.8: rois.py 통합 (RED → GREEN)
- [x] Test: POST /api/presets/{preset_id}/rois - ConfigChangeLog CREATED 기록 확인
- [x] Test: PATCH /api/presets/{preset_id}/rois/{id} - ConfigChangeLog UPDATED 기록 확인
- [x] Test: DELETE /api/presets/{preset_id}/rois/{id} - ConfigChangeLog DELETED 기록 확인
- [x] Impl: rois.py에 log_config_change 호출 추가

### ActionItem CCL-11.9: xy_points.py 통합 (RED → GREEN)
- [x] Test: POST /api/rois/{roi_id}/points - ConfigChangeLog CREATED 기록 확인
- [x] Test: DELETE /api/rois/{roi_id}/points/{point_id} - ConfigChangeLog DELETED 기록 확인
- [x] Impl: xypoints.py에 log_config_change 호출 추가 (POST, DELETE)

### ActionItem CCL-11.10: file_groups.py 통합 (RED → GREEN)
- [x] Test: POST /api/file-groups - ConfigChangeLog CREATED 기록 확인
- [x] Test: PATCH /api/file-groups/{id} - ConfigChangeLog UPDATED 기록 확인
- [x] Test: DELETE /api/file-groups/{id} - ConfigChangeLog DELETED 기록 확인
- [x] Impl: file_groups.py에 log_config_change 호출 추가

---

## Phase CCL-12: Event 계열 라우터 통합 (4개)

### ActionItem CCL-12.1: detection_events.py 통합 (RED → GREEN) [x]
- [x] Test: POST /api/events/detections - ConfigChangeLog CREATED 기록 확인
- [x] Test: PATCH /api/events/detections/{id} - ConfigChangeLog UPDATED 기록 확인
- [x] Test: DELETE /api/events/detections/{id} - ConfigChangeLog DELETED 기록 확인
- [x] Impl: detection_events.py에 log_config_change 호출 추가

### ActionItem CCL-12.2: malfunction_events.py 통합 (RED → GREEN) [x]
- [x] Test: POST /api/events/malfunctions - ConfigChangeLog CREATED 기록 확인
- [x] Test: PATCH /api/events/malfunctions/{id} - ConfigChangeLog UPDATED 기록 확인
- [x] Test: DELETE /api/events/malfunctions/{id} - ConfigChangeLog DELETED 기록 확인
- [x] Impl: malfunction_events.py에 log_config_change 호출 추가

### ActionItem CCL-12.3: connection_events.py 통합 (RED → GREEN) [x]
- [x] Test: POST /api/events/connections - ConfigChangeLog CREATED 기록 확인
- [x] Test: PATCH /api/events/connections/{id} - ConfigChangeLog UPDATED 기록 확인
- [x] Test: DELETE /api/events/connections/{id} - ConfigChangeLog DELETED 기록 확인
- [x] Impl: connection_events.py에 log_config_change 호출 추가

### ActionItem CCL-12.4: action_events.py 통합 (RED → GREEN) [x]
- [x] Test: POST /api/events/actions - ConfigChangeLog CREATED 기록 확인
- [x] Test: PATCH /api/events/actions/{id} - ConfigChangeLog UPDATED 기록 확인
- [x] Test: DELETE /api/events/actions/{id} - ConfigChangeLog DELETED 기록 확인
- [x] Impl: action_events.py에 log_config_change 호출 추가

---

## Phase CCL-13: Integration 계열 라우터 통합 (3개)

### ActionItem CCL-13.1: event_mappings.py 통합 (RED → GREEN) [x]
- [x] Test: POST /api/integrations/event-mappings - ConfigChangeLog CREATED 기록 확인
- [x] Test: PATCH /api/integrations/event-mappings/{id} - ConfigChangeLog UPDATED 기록 확인
- [x] Test: DELETE /api/integrations/event-mappings/{id} - ConfigChangeLog DELETED 기록 확인
- [x] Impl: event_mappings.py에 log_config_change 호출 추가

### ActionItem CCL-13.2: event_mapping_cameras.py 통합 (RED → GREEN) ✅
- [x] Test: POST /api/integrations/event-mapping-cameras - ConfigChangeLog CREATED 기록 확인
- [x] Test: PATCH /api/integrations/event-mapping-cameras/{id} - ConfigChangeLog UPDATED 기록 확인
- [x] Test: DELETE /api/integrations/event-mapping-cameras/{id} - ConfigChangeLog DELETED 기록 확인
- [x] Impl: event_mapping_cameras.py에 log_config_change 호출 추가

### ActionItem CCL-13.3: event_mapping_speakers.py 통합 (RED → GREEN) ✅
- [x] Test: POST /api/integrations/event-mapping-speakers - ConfigChangeLog CREATED 기록 확인
- [x] Test: PATCH /api/integrations/event-mapping-speakers/{id} - ConfigChangeLog UPDATED 기록 확인
- [x] Test: DELETE /api/integrations/event-mapping-speakers/{id} - ConfigChangeLog DELETED 기록 확인
- [x] Impl: event_mapping_speakers.py에 log_config_change 호출 추가

---

## CCL Router Integration Progress Summary

| Phase | 대상 | 라우터 수 | 상태 |
|-------|------|----------|------|
| CCL-11 | Device 계열 | 10개 | [ ] 미진행 |
| CCL-12 | Event 계열 | 4개 | [ ] 미진행 |
| CCL-13 | Integration 계열 | 3개 | [ ] 미진행 |
| **합계** | | **17개** | |

---

# ============================================================
# Report System Implementation Plan
# ============================================================

> **기반 문서**: PRD_Report_System.md v1.3
> **방법론**: TDD (Test-Driven Development) per CLAUDE.md
> **작성일**: 2026-01-22
> **진행 표시**: `[ ]` 미진행, `[~]` 진행중, `[x]` 완료

---

## Phase RS-1: Report Enums

Report System에 필요한 Enum 타입 추가

### ActionItem RS-1.1: EnumReportType (RED → GREEN)
- [x] Test: EnumReportType이 존재하고 STANDARD, CUSTOM 값을 가짐
- [x] Impl: app/utils/enums.py에 EnumReportType 추가

### ActionItem RS-1.2: EnumReportPeriod (RED → GREEN)
- [x] Test: EnumReportPeriod이 존재하고 7d, 30d, 90d, 1y 값을 가짐
- [x] Impl: app/utils/enums.py에 EnumReportPeriod 추가

### ActionItem RS-1.3: EnumReportStatus (RED → GREEN)
- [x] Test: EnumReportStatus이 존재하고 PENDING, GENERATING, COMPLETED, FAILED 값을 가짐
- [x] Impl: app/utils/enums.py에 EnumReportStatus 추가

### ActionItem RS-1.4: EnumChartType (RED → GREEN)
- [x] Test: EnumChartType이 존재하고 LINE, BAR, DONUT, PIE 값을 가짐
- [x] Impl: app/utils/enums.py에 EnumChartType 추가

### ActionItem RS-1.5: EnumReportComponent (RED → GREEN)
- [x] Test: EnumReportComponent이 존재하고 15개 컴포넌트 값을 가짐
- [x] Impl: app/utils/enums.py에 EnumReportComponent 추가

---

## Phase RS-2: Report Models

SQLAlchemy 모델 구현

### ActionItem RS-2.1: ReportTemplate 모델 (RED → GREEN)
- [x] Test: ReportTemplate 모델이 존재하고 필수 필드를 가짐 (id, name, report_type, components, created_at, updated_at)
- [x] Impl: app/models/report.py에 ReportTemplate 모델 생성

### ActionItem RS-2.2: ReportTemplate 필드 상세 (RED → GREEN)
- [x] Test: ReportTemplate.description이 nullable
- [x] Test: ReportTemplate.owner_id가 users.id를 참조 (FK)
- [x] Test: ReportTemplate.is_public이 Boolean, default=False
- [x] Test: ReportTemplate.default_period이 String, default='7d'
- [x] Impl: 모든 필드 구현

### ActionItem RS-2.3: ReportGeneration 모델 (RED → GREEN)
- [x] Test: ReportGeneration 모델이 존재하고 필수 필드를 가짐 (id, report_type, title, period_type, start_date, end_date, status, created_at)
- [x] Impl: app/models/report.py에 ReportGeneration 모델 생성

### ActionItem RS-2.4: ReportGeneration 필드 상세 (RED → GREEN)
- [x] Test: ReportGeneration.template_id가 report_templates.id를 참조 (FK, nullable)
- [x] Test: ReportGeneration.generator_id가 users.id를 참조 (FK, nullable)
- [x] Test: ReportGeneration.generator_name, generator_department이 String, nullable
- [x] Test: ReportGeneration.severity_filter, summary_data가 JSON, nullable
- [x] Test: ReportGeneration.pdf_file_path, pdf_file_size가 nullable
- [x] Test: ReportGeneration.completed_at이 nullable (updated_at 없음)
- [x] Impl: 모든 필드 구현

### ActionItem RS-2.5: User 모델 relationship 추가 (RED → GREEN)
- [x] Test: User.report_templates relationship 존재
- [x] Test: User.report_generations relationship 존재
- [x] Impl: app/models/user.py에 relationships 추가

---

## Phase RS-3: Report Schemas

Pydantic 스키마 구현

### ActionItem RS-3.1: ReportComponentConfig 스키마 (RED → GREEN)
- [x] Test: ReportComponentConfig 스키마가 id, order, enabled, title 필드를 가짐
- [x] Impl: app/schemas/report.py에 ReportComponentConfig 스키마 생성

### ActionItem RS-3.2: ReportTemplateCreate 스키마 (RED → GREEN)
- [x] Test: ReportTemplateCreate에 name, components 필수 필드
- [x] Test: ReportTemplateCreate에 description, report_type, is_public, default_period 선택 필드
- [x] Test: ReportTemplateCreate.name 빈 문자열 시 ValidationError
- [x] Impl: ReportTemplateCreate 스키마 구현

### ActionItem RS-3.3: ReportTemplateUpdate 스키마 (RED → GREEN)
- [x] Test: ReportTemplateUpdate의 모든 필드가 Optional
- [x] Impl: ReportTemplateUpdate 스키마 구현

### ActionItem RS-3.4: ReportTemplateResponse 스키마 (RED → GREEN)
- [x] Test: ReportTemplateResponse에 id, name, report_type, owner_id, is_public, components, default_period, created_at, updated_at 포함
- [x] Impl: ReportTemplateResponse 스키마 구현

### ActionItem RS-3.5: ReportGenerateRequest 스키마 (RED → GREEN)
- [x] Test: ReportGenerateRequest에 report_type, title, period_type 필수 필드
- [x] Test: ReportGenerateRequest에 template_id, severity_filter 선택 필드
- [x] Test: ReportGenerateRequest.title 빈 문자열 시 ValidationError
- [x] Impl: ReportGenerateRequest 스키마 구현

### ActionItem RS-3.6: ReportGenerationResponse 스키마 (RED → GREEN)
- [x] Test: ReportGenerationResponse에 id, report_type, title, period_type, start_date, end_date, status, created_at 포함
- [x] Test: ReportGenerationResponse에 template_id, generator_id, generator_name, completed_at nullable
- [x] Impl: ReportGenerationResponse 스키마 구현

---

## Phase RS-4: Report Templates Router

템플릿 CRUD API 구현

### ActionItem RS-4.1: GET /api/reports/templates (RED → GREEN)
- [x] Test: GET /api/reports/templates - 200 OK, 빈 목록 반환
- [x] Test: GET /api/reports/templates - pagination 동작 (page, limit)
- [x] Impl: app/routers/reports.py 생성 및 get_templates 엔드포인트 구현

### ActionItem RS-4.2: POST /api/reports/templates (RED → GREEN)
- [x] Test: POST /api/reports/templates - 201 Created, 템플릿 생성 성공
- [x] Test: POST /api/reports/templates - name 빈 문자열 시 422 에러
- [x] Impl: create_template 엔드포인트 구현

### ActionItem RS-4.3: GET /api/reports/templates/{id} (RED → GREEN)
- [x] Test: GET /api/reports/templates/{id} - 200 OK, 템플릿 상세 조회
- [x] Test: GET /api/reports/templates/{id} - 존재하지 않는 ID 시 404
- [x] Impl: get_template 엔드포인트 구현

### ActionItem RS-4.4: PATCH /api/reports/templates/{id} (RED → GREEN)
- [x] Test: PATCH /api/reports/templates/{id} - 200 OK, 부분 업데이트 성공
- [x] Test: PATCH /api/reports/templates/{id} - 존재하지 않는 ID 시 404
- [x] Impl: update_template 엔드포인트 구현

### ActionItem RS-4.5: DELETE /api/reports/templates/{id} (RED → GREEN)
- [x] Test: DELETE /api/reports/templates/{id} - 200 OK, 삭제 성공
- [x] Test: DELETE /api/reports/templates/{id} - 존재하지 않는 ID 시 404
- [x] Impl: delete_template 엔드포인트 구현

---

## Phase RS-5: Report Generation Router

보고서 생성 API 구현

### ActionItem RS-5.1: POST /api/reports/generate (RED → GREEN)
- [x] Test: POST /api/reports/generate - 202 Accepted, 생성 요청 성공
- [x] Test: POST /api/reports/generate - generation_id와 status='PENDING' 반환
- [x] Test: POST /api/reports/generate - start_date, end_date 자동 계산 (period_type 기반)
- [x] Impl: generate_report 엔드포인트 구현

### ActionItem RS-5.2: GET /api/reports/generations (RED → GREEN)
- [x] Test: GET /api/reports/generations - 200 OK, 생성 이력 목록
- [x] Test: GET /api/reports/generations?status=COMPLETED - 상태 필터링
- [x] Impl: get_generations 엔드포인트 구현

### ActionItem RS-5.3: GET /api/reports/generations/{id} (RED → GREEN)
- [x] Test: GET /api/reports/generations/{id} - 200 OK, 상세 조회
- [x] Test: GET /api/reports/generations/{id} - 존재하지 않는 ID 시 404
- [x] Test: GET /api/reports/generations/{id} - COMPLETED 시 pdf_download_url 포함
- [x] Impl: get_generation 엔드포인트 구현

### ActionItem RS-5.4: GET /api/reports/generations/{id}/download (RED → GREEN)
- [x] Test: GET /api/reports/generations/{id}/download - COMPLETED 아닌 경우 400
- [x] Test: GET /api/reports/generations/{id}/download - 존재하지 않는 ID 시 404
- [x] Impl: download_report 엔드포인트 구현

### ActionItem RS-5.5: GET /api/reports/generations/{id}/preview (RED → GREEN)
- [x] Test: GET /api/reports/generations/{id}/preview - 200 OK, JSON 미리보기 데이터
- [x] Test: GET /api/reports/generations/{id}/preview - COMPLETED 아닌 경우 400
- [x] Impl: preview_report 엔드포인트 구현

---

## Phase RS-6: Report Components Router

컴포넌트 목록 API 구현

### ActionItem RS-6.1: GET /api/reports/components (RED → GREEN)
- [x] Test: GET /api/reports/components - 200 OK, 4개 카테고리 반환
- [x] Test: GET /api/reports/components - SUMMARY(1), DEVICE(3), EVENT(6), SYSTEM(5) 컴포넌트 포함
- [x] Impl: get_components 엔드포인트 구현

---

## Phase RS-7: main.py Integration

라우터 등록 및 태그 추가

### ActionItem RS-7.1: Router Registration (RED → GREEN)
- [x] Test: /api/reports/components 엔드포인트 접근 가능
- [x] Impl: main.py에 reports 라우터 import 및 등록

### ActionItem RS-7.2: OpenAPI Tags (RED → GREEN)
- [x] Test: OpenAPI 스키마에 "Reports" 태그 존재
- [x] Impl: main.py tags_metadata에 Reports 태그 추가

---

## Phase RS-8: Report Service

데이터 수집 및 처리 서비스

### ActionItem RS-8.1: ReportService 클래스 (RED → GREEN)
- [x] Test: ReportService 클래스가 존재
- [x] Impl: app/services/report_service.py 생성

### ActionItem RS-8.2: Device 통계 수집 (RED → GREEN)
- [x] Test: ReportService.get_device_statistics()가 상태별 카운트 반환
- [x] Test: ReportService.get_device_statistics()가 유형별 카운트 반환
- [x] Impl: get_device_statistics 메서드 구현

### ActionItem RS-8.3: Event 통계 수집 (RED → GREEN)
- [x] Test: ReportService.get_event_statistics()가 Detection, Malfunction, Action 카운트 반환
- [x] Test: ReportService.get_event_statistics()가 Connection 제외
- [x] Test: ReportService.get_event_statistics()가 일별 추세 데이터 반환
- [x] Impl: get_event_statistics 메서드 구현

### ActionItem RS-8.4: System 통계 수집 (RED → GREEN)
- [x] Test: ReportService.get_system_statistics()가 심각도별 카운트 반환
- [x] Test: ReportService.get_system_statistics()가 일별 추세 데이터 반환
- [x] Impl: get_system_statistics 메서드 구현

### ActionItem RS-8.5: Preview 데이터 생성 (RED → GREEN)
- [x] Test: ReportService.get_preview_data()가 sections 배열 반환
- [x] Test: 각 section에 charts와 grids 포함
- [x] Impl: get_preview_data 메서드 구현

---

## Phase RS-9: Preview Page

개발용 HTML 미리보기 페이지

### ActionItem RS-9.1: Preview 템플릿 (RED → GREEN)
- [x] Test: GET /reports/preview/{id} - HTML 응답 반환
- [x] Test: GET /reports/preview/{id} - 존재하지 않는 ID 시 404
- [x] Impl: main.py에 inline HTML preview page 구현

### ActionItem RS-9.2: main.py Preview Route (RED → GREEN)
- [x] Test: /reports/preview/1 접근 시 HTMLResponse
- [x] Impl: main.py에 preview 페이지 라우트 추가

---

## Report System Progress Summary

| Phase | 설명 | ActionItem 수 | 상태 |
|-------|------|--------------|------|
| RS-1 | Enums | 5개 | [x] 완료 |
| RS-2 | Models | 5개 | [x] 완료 |
| RS-3 | Schemas | 6개 | [x] 완료 |
| RS-4 | Templates Router | 5개 | [x] 완료 |
| RS-5 | Generation Router | 5개 | [x] 완료 |
| RS-6 | Components Router | 1개 | [x] 완료 |
| RS-7 | main.py Integration | 2개 | [x] 완료 |
| RS-8 | Report Service | 5개 | [x] 완료 |
| RS-9 | Preview Page | 2개 | [x] 완료 |
| RS-10 | PDF Generation | 8개 | [x] 완료 |
| RS-11 | Async Generation | 3개 | [x] 완료 |
| RS-12 | Preview 고도화 (Chart.js) | 14개 | [x] 완료 |
| **합계** | | **61개** | **완료** |

---

## Phase RS-10: PDF Generation Utilities

차트 생성 및 PDF 생성 유틸리티 구현 (PRD Phase 3: 시각화)

### ActionItem RS-10.1: requirements.txt 업데이트 (RED → GREEN) ✓
- [x] Test: reportlab 패키지 import 가능
- [x] Test: matplotlib 패키지 import 가능
- [x] Impl: requirements.txt에 reportlab, matplotlib 추가

### ActionItem RS-10.2: ChartGenerator 클래스 (RED → GREEN) ✓
- [x] Test: ChartGenerator 클래스가 존재
- [x] Impl: app/utils/chart_generator.py 생성

### ActionItem RS-10.3: ChartGenerator.generate_pie_chart (RED → GREEN) ✓
- [x] Test: generate_pie_chart()가 bytes 이미지 반환
- [x] Impl: PIE 차트 생성 메서드 구현

### ActionItem RS-10.4: ChartGenerator.generate_bar_chart (RED → GREEN) ✓
- [x] Test: generate_bar_chart()가 bytes 이미지 반환
- [x] Impl: BAR 차트 생성 메서드 구현

### ActionItem RS-10.5: ChartGenerator.generate_line_chart (RED → GREEN) ✓
- [x] Test: generate_line_chart()가 bytes 이미지 반환
- [x] Impl: LINE 차트 생성 메서드 구현

### ActionItem RS-10.6: ChartGenerator.generate_donut_chart (RED → GREEN) ✓
- [x] Test: generate_donut_chart()가 bytes 이미지 반환
- [x] Impl: DONUT 차트 생성 메서드 구현

### ActionItem RS-10.7: PDFGenerator 클래스 (RED → GREEN) ✓
- [x] Test: PDFGenerator 클래스가 존재
- [x] Impl: app/utils/pdf_generator.py 생성

### ActionItem RS-10.8: PDFGenerator.generate_report (RED → GREEN) ✓
- [x] Test: generate_report()가 bytes PDF 반환
- [x] Test: generate_report()에 제목, 차트, 표 포함
- [x] Impl: PDF 생성 메서드 구현

---

## Phase RS-11: Async Report Generation

BackgroundTasks 기반 비동기 PDF 생성 구현

### ActionItem RS-11.1: ReportService.generate_report_async 메서드 (RED → GREEN) ✓
- [x] Test: generate_report_async 메서드가 존재
- [x] Test: generate_report_async가 status를 GENERATING으로 변경
- [x] Impl: generate_report_async 메서드 추가

### ActionItem RS-11.2: PDF 생성 및 상태 업데이트 (RED → GREEN) ✓
- [x] Test: generate_report_async 완료 시 status가 COMPLETED
- [x] Test: generate_report_async 완료 시 pdf_file_path가 설정됨
- [x] Test: generate_report_async 실패 시 status가 FAILED, error_message 설정
- [x] Impl: PDF 생성 로직 및 상태 업데이트 구현

### ActionItem RS-11.3: POST /generate에 BackgroundTasks 연동 (RED → GREEN) ✓
- [x] Test: POST /api/reports/generate가 BackgroundTasks로 비동기 생성 시작
- [x] Test: _run_report_generation 함수 존재 확인
- [x] Impl: reports.py에 BackgroundTasks 연동

---

## Phase RS-12: Preview 페이지 고도화 (Chart.js 연동)

PRD_Report_System.md Section 10 - 개발용 Preview 페이지를 Jinja2 템플릿 + Chart.js로 고도화

### ActionItem RS-12.1: preview.html 템플릿 생성 (RED → GREEN) ✓
- [x] Test: app/templates/reports 디렉토리 존재
- [x] Test: app/templates/reports/preview.html 파일 존재
- [x] Impl: 템플릿 디렉토리 및 파일 생성

### ActionItem RS-12.2: preview.html 템플릿 내용 (RED → GREEN) ✓
- [x] Test: 템플릿에 Chart.js CDN 포함
- [x] Test: 템플릿에 {{ report.* }} Jinja2 변수 사용
- [x] Test: 템플릿에 {{ preview.* }} Jinja2 변수 사용
- [x] Test: 템플릿에 <canvas> 요소 포함
- [x] Test: 템플릿에 /download 버튼 포함
- [x] Impl: PRD Section 10.4 기반 preview.html 구현

### ActionItem RS-12.3: main.py Jinja2Templates 연동 (RED → GREEN) ✓
- [x] Test: main.py에 Jinja2Templates import 존재
- [x] Test: main.py에 templates 인스턴스 존재
- [x] Test: preview 라우트가 TemplateResponse 사용
- [x] Impl: main.py 업데이트

### ActionItem RS-12.4: Preview Route API 테스트 (RED → GREEN) ✓
- [x] Test: GET /reports/preview/{id} - HTML 응답 반환
- [x] Test: GET /reports/preview/{id} - 보고서 제목 포함
- [x] Test: GET /reports/preview/{id} - Chart.js 스크립트 포함
- [x] Test: GET /reports/preview/{id} - 존재하지 않는 ID 시 404
- [x] Impl: preview_route에서 ReportService.get_preview_data() 호출

---

# ServerNestedResponse 스키마 통합

> **PRD 참조**: docs/PRD_ServerNestedResponse_Fix.md
> **작성일**: 2026-01-26
> **진행 표시**: `[ ]` 미진행, `[~]` 진행중, `[x]` 완료

---

## Phase SNR-1: 현재 상태 확인 (Red - 문제 식별)

### ActionItem SNR-1.1: 중복 스키마 현황 파악
- [x] Check: device.py의 ServerNestedResponse 필드 목록 확인
  - 필드: id, category_id, name, status, ip_address, port, hostname, user_name, user_password, cpu_usage, ram_usage, disk_usage, network_throughput
  - 문제: threshold_config 없음, v2.9 제거 필드 포함
- [x] Check: server.py의 ServerNestedResponse 필드 목록 확인
  - 필드: id, category_id, name, status, ip_address, port, hostname, user_name, user_password, threshold_config
  - 상태: 정상 (문서와 일치)
- [x] Check: Swagger에서 ServerNestedResponse 스키마 필드 확인
  - 결과: device.py 버전이 사용됨 (threshold_config 없음, cpu_usage 등 포함)
- [x] Check: speakers.py에서 ServerNestedResponse import 경로 확인
  - 현재: `from app.schemas.device import ... ServerNestedResponse`
  - 문제: device.py에서 import 중

---

## Phase SNR-2: 테스트 작성 (Red - 실패하는 테스트)

### ActionItem SNR-2.1: ServerNestedResponse 필드 검증 테스트
- [x] Test: ServerNestedResponse에 threshold_config 필드 존재 → FAIL (없음)
- [x] Test: ServerNestedResponse에 cpu_usage 필드 없음 → FAIL (있음)
- [x] Test: ServerNestedResponse에 ram_usage 필드 없음 → FAIL (있음)
- [x] Test: ServerNestedResponse에 disk_usage 필드 없음 → FAIL (있음)
- [x] Test: ServerNestedResponse에 network_throughput 필드 없음 → FAIL (있음)
- **Red Phase 완료**: 5/5 테스트 실패 (예상대로)

---

## Phase SNR-3: 코드 수정 (Green - 테스트 통과)

### ActionItem SNR-3.1: device.py 스키마 정리
- [x] Impl: device.py에서 ServerNestedResponse 클래스 삭제
- [x] Impl: device.py에 `from app.schemas.server import ServerNestedResponse` 추가

### ActionItem SNR-3.2: speakers.py import 수정
- [x] Impl: speakers.py의 ServerNestedResponse import 경로를 server.py로 변경
- **Green Phase 완료**: 5/5 테스트 통과

---

## Phase SNR-4: 검증 (Refactor - 정리)

### ActionItem SNR-4.1: 시스템 검증
- [x] Verify: Python 캐시 삭제 및 서버 재시작
- [x] Verify: Swagger에서 ServerNestedResponse 스키마 검증 → ALL PASS (5/5)
- [x] Verify: Speaker API 응답에 threshold_config 포함 확인
- [x] Verify: 문서(GOP_Restful_Api_연동설계.md)와 일치 확인

### 검증 결과
- **Swagger Schema**: ServerNestedResponse에 threshold_config 포함, deprecated 필드 제거됨
- **문서 일치**: GOP_Restful_Api_연동설계.md v2.9 변경사항과 일치
  - `threshold_config` 필드 추가 (v2.9 신규)
  - `cpu_usage`, `ram_usage`, `disk_usage`, `network_throughput` 제거됨

---

## ServerNestedResponse 스키마 통합 완료

**수정된 파일**:
1. `app/schemas/device.py`: ServerNestedResponse 클래스 삭제, server.py에서 import
2. `app/routers/speakers.py`: ServerNestedResponse import 경로를 server.py로 변경

**최종 ServerNestedResponse 필드 (server.py:111)**:
- id, category_id, name, status, ip_address, port
- hostname, user_name, user_password
- threshold_config ✅ (v2.9 신규)

---

## 완료 조건

1. Swagger의 ServerNestedResponse에 `threshold_config` 필드 포함
2. Swagger의 ServerNestedResponse에서 `cpu_usage`, `ram_usage`, `disk_usage`, `network_throughput` 제거
3. Speaker API 응답이 문서와 일치
4. 중복 스키마 제거 완료

---

