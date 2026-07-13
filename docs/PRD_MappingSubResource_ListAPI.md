# PRD: MappingCamera / MappingSpeaker / MappingLamp 독립 List API

**작성일**: 2026-02-11
**버전**: v1.0
**작성자**: 이기호 차장
**대상 API 버전**: v3.8 (예정)
**상태**: Draft

---

## 1. 개요

### 1.1 배경

현재 EventMappingCamera, EventMappingSpeaker, EventMappingLamp는 모두 EventMapping의 하위 리소스로만 조회 가능하다:

```
GET /api/integrations/event-mappings/{mapping_id}/cameras
GET /api/integrations/event-mappings/{mapping_id}/speakers
GET /api/integrations/event-mappings/{mapping_id}/lamps
```

서브시스템(VMS, AI분석 서버 등)은 이벤트 발생 시 **전체 MappingCamera/Speaker/Lamp 목록**을 캐시에 저장하고, 이벤트의 `device_group_id`와 매칭하여 연동 장비를 결정하는 로직이 필요하다.

### 1.2 문제점

현재 구조에서 전체 목록을 얻으려면:

1. `GET /api/integrations/event-mappings` → 전체 EventMapping ID 목록 조회
2. 각 `mapping_id`마다 `GET .../cameras`, `GET .../speakers`, `GET .../lamps` 호출
3. 결과를 클라이언트에서 병합

이는 **N+1 호출 문제**를 야기하며, 서브시스템 캐시 구성 시 비효율적이다.

### 1.3 목표

- 각 하위 리소스에 대해 **독립 List 엔드포인트**를 추가한다
- 서브시스템이 **단일 호출**로 전체 데이터를 확보할 수 있도록 한다
- 기존 계층형 엔드포인트(`/{mapping_id}/cameras` 등)는 그대로 유지한다

---

## 2. 신규 API 엔드포인트

### 2.1 MappingCamera 전체 목록 조회

**Endpoint**: `GET /api/integrations/mapping-cameras`

**설명**: 모든 EventMappingCamera를 EventMapping 구분 없이 전체 조회한다.

**Query Parameters**:

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|------|--------|------|
| `event_mapping_id` | int | N | - | 특정 EventMapping으로 필터링 |
| `camera_id` | int | N | - | 특정 Camera로 필터링 |
| `is_enable` | boolean | N | - | 활성화 상태 필터 |
| `page` | int | N | 1 | 페이지 번호 |
| `limit` | int | N | 20 | 페이지당 항목 수 |

**Request Example**:
```http
GET /api/integrations/mapping-cameras?is_enable=true&page=1&limit=50 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Response Example** (200 OK):
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "event_mapping_id": 10,
      "camera": {
        "id": 101,
        "number_device": 1,
        "group_device": 1,
        "name_device": "PTZ-Camera-01",
        "type_device": "IpCamera",
        "version": "2.1.0",
        "status": "ACTIVATED",
        "is_enable": true,
        "ip_address": "192.168.1.100",
        "ip_port": 554,
        "mode": "ONVIF",
        "category": "PTZ",
        "is_record": true,
        "hardware_spec": null,
        "geolocation": null,
        "urls": {"live": "rtsp://192.168.1.100:554/stream1"},
        "device_groups": [
          {"id": 1, "name": "A구역 센서그룹", "description": null, "device_count": 5}
        ]
      },
      "target_preset": {
        "id": 201,
        "camera_id": 101,
        "camera_name": "PTZ-Camera-01",
        "preset_index": 1,
        "preset_name": "Target-A",
        "touring_time": 10
      },
      "home_preset": {
        "id": 202,
        "camera_id": 101,
        "camera_name": "PTZ-Camera-01",
        "preset_index": 0,
        "preset_name": "Home",
        "touring_time": 0
      },
      "delay_time": 5,
      "is_enable": true,
      "priority": 1,
      "created_at": "2026-02-01T09:00:00Z",
      "updated_at": "2026-02-01T09:00:00Z"
    }
  ],
  "pagination": {
    "current_page": 1,
    "per_page": 50,
    "total_items": 25,
    "total_pages": 1
  }
}
```

**참고**: Response 스키마는 기존 `EventMappingCameraResponse`와 동일하다. Nested 객체(camera, target_preset, home_preset)에는 timestamp를 포함하지 않는다 (기존 Nested Response 규칙 적용).

---

### 2.2 MappingSpeaker 전체 목록 조회

**Endpoint**: `GET /api/integrations/mapping-speakers`

**설명**: 모든 EventMappingSpeaker를 EventMapping 구분 없이 전체 조회한다.

**Query Parameters**:

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|------|--------|------|
| `event_mapping_id` | int | N | - | 특정 EventMapping으로 필터링 |
| `speaker_id` | int | N | - | 특정 Speaker로 필터링 |
| `is_enable` | boolean | N | - | 활성화 상태 필터 |
| `page` | int | N | 1 | 페이지 번호 |
| `limit` | int | N | 20 | 페이지당 항목 수 |

**Request Example**:
```http
GET /api/integrations/mapping-speakers?is_enable=true&page=1&limit=50 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Response Example** (200 OK):
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "event_mapping_id": 10,
      "speaker": {
        "id": 301,
        "number_device": 1,
        "group_device": 1,
        "name_device": "IP-Speaker-01",
        "type_device": "IpSpeaker",
        "version": "1.0.0",
        "status": "ACTIVATED",
        "is_enable": true,
        "speaker_type": "NORMAL",
        "server_id": 1,
        "description": "A구역 스피커",
        "geolocation": {"latitude": 37.5665, "longitude": 126.9780}
      },
      "file_group": {
        "id": 501,
        "server_id": 1,
        "group_id": 1,
        "group_name": "경보음원 그룹A",
        "files": [
          {"file_id": 1, "file_name": "alarm_01.wav"}
        ]
      },
      "repeat_count": 3,
      "is_enable": true,
      "priority": 1,
      "created_at": "2026-02-01T09:00:00Z",
      "updated_at": "2026-02-01T09:00:00Z"
    }
  ],
  "pagination": {
    "current_page": 1,
    "per_page": 50,
    "total_items": 12,
    "total_pages": 1
  }
}
```

**참고**: Response 스키마는 기존 `EventMappingSpeakerResponse`와 동일하다.

---

### 2.3 MappingLamp 전체 목록 조회

**Endpoint**: `GET /api/integrations/mapping-lamps`

**설명**: 모든 EventMappingLamp를 EventMapping 구분 없이 전체 조회한다.

**Query Parameters**:

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|------|--------|------|
| `event_mapping_id` | int | N | - | 특정 EventMapping으로 필터링 |
| `lamp_id` | int | N | - | 특정 Lamp로 필터링 |
| `is_enable` | boolean | N | - | 활성화 상태 필터 |
| `page` | int | N | 1 | 페이지 번호 |
| `limit` | int | N | 20 | 페이지당 항목 수 |

**Request Example**:
```http
GET /api/integrations/mapping-lamps?is_enable=true&page=1&limit=50 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Response Example** (200 OK):
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "event_mapping": {
        "id": 10,
        "name_event": "A구역 침입감지",
        "category_event_mapping": "FENCE_SENSOR_ONLY"
      },
      "lamp": {
        "id": 401,
        "number_device": 1,
        "group_device": 1,
        "name_device": "경광등-01",
        "type_device": "Lamp",
        "version": "1.0.0",
        "status": "ACTIVATED",
        "is_enable": true,
        "ip_address": "192.168.1.200",
        "ip_port": 5000,
        "user_name": "admin",
        "description": "A구역 경광등",
        "geolocation": {"latitude": 37.5665, "longitude": 126.9780}
      },
      "color": "Red",
      "buzzer_time": 5,
      "buzzer_sound": "PI-PI-PI",
      "light_mode": "steady",
      "is_enable": true,
      "priority": 1,
      "created_at": "2026-02-01T09:00:00Z",
      "updated_at": "2026-02-01T09:00:00Z"
    }
  ],
  "pagination": {
    "current_page": 1,
    "per_page": 50,
    "total_items": 8,
    "total_pages": 1
  }
}
```

**참고**: Response 스키마는 기존 `EventMappingLampResponse`와 동일하다. Lamp의 `event_mapping` nested 필드와 `lamp` nested 필드 모두 포함.

---

## 3. 구현 상세

### 3.1 라우터 (Router)

각 독립 List API는 **기존 라우터 파일에 추가**하되, 새로운 prefix로 등록한다.

| 항목 | 내용 |
|------|------|
| **MappingCamera** | `app/routers/event_mapping_cameras.py`에 함수 추가 |
| **MappingSpeaker** | `app/routers/event_mapping_speakers.py`에 함수 추가 |
| **MappingLamp** | `app/routers/event_mapping_lamps.py`에 함수 추가 |

**main.py 라우터 등록** (신규 추가):

```python
# 독립 List API (기존 계층형 라우터와 별도)
app.include_router(
    event_mapping_cameras.flat_router,
    prefix="/api/integrations/mapping-cameras",
    tags=["Mapping Cameras"]
)
app.include_router(
    event_mapping_speakers.flat_router,
    prefix="/api/integrations/mapping-speakers",
    tags=["Mapping Speakers"]
)
app.include_router(
    event_mapping_lamps.flat_router,
    prefix="/api/integrations/mapping-lamps",
    tags=["Mapping Lamps"]
)
```

**Swagger 태그 분리**: 기존 `Event Mapping Cameras` 태그와 별도로 `Mapping Cameras`, `Mapping Speakers`, `Mapping Lamps` 태그를 사용하여 Swagger UI에서 명확히 구분한다.

### 3.2 스키마 (Schema)

기존 Response 스키마를 **재사용**한다. 신규 스키마 생성 불필요.

| 엔드포인트 | Response 스키마 | 비고 |
|------------|----------------|------|
| `GET /mapping-cameras` | `ApiPaginatedResponse[EventMappingCameraResponse]` | 기존 스키마 재사용 |
| `GET /mapping-speakers` | `ApiPaginatedResponse[EventMappingSpeakerResponse]` | 기존 스키마 재사용 |
| `GET /mapping-lamps` | `ApiPaginatedResponse[EventMappingLampResponse]` | 기존 스키마 재사용 |

### 3.3 서비스 / CRUD 레이어

기존 CRUD 함수에 **`mapping_id` 없이 전체 조회하는 함수**를 추가한다.

| 파일 | 추가 함수 | 설명 |
|------|-----------|------|
| `app/crud/event_mapping_camera.py` | `get_all_mapping_cameras()` | 전체 MappingCamera 페이지네이션 조회 |
| `app/crud/event_mapping_speaker.py` | `get_all_mapping_speakers()` | 전체 MappingSpeaker 페이지네이션 조회 |
| `app/crud/event_mapping_lamp.py` | `get_all_mapping_lamps()` | 전체 MappingLamp 페이지네이션 조회 |

각 함수는 기존 `get_mapping_cameras()` 등을 참고하되, `event_mapping_id` 필터를 선택적으로 적용한다.

### 3.4 모델 (Model)

모델 변경 없음. 기존 `EventMappingCamera`, `EventMappingSpeaker`, `EventMappingLamp` 모델을 그대로 사용한다.

### 3.5 DB 마이그레이션

DB 스키마 변경 없음. 신규 테이블이나 컬럼 추가가 필요하지 않다.

---

## 4. 기존 API와의 관계

| 구분 | 기존 API (유지) | 신규 API (추가) |
|------|----------------|----------------|
| **Camera** | `GET /{mapping_id}/cameras` | `GET /mapping-cameras` |
| **Speaker** | `GET /{mapping_id}/speakers` | `GET /mapping-speakers` |
| **Lamp** | `GET /{mapping_id}/lamps` | `GET /mapping-lamps` |
| **용도** | 특정 매핑의 하위 리소스 CRUD | 서브시스템 캐시용 전체 조회 |
| **CUD** | POST/PATCH/PUT/DELETE 지원 | 읽기 전용 (GET만 제공) |

> **원칙**: 신규 API는 **읽기 전용**(GET List만 제공)이다. 생성/수정/삭제는 기존 계층형 엔드포인트를 통해서만 수행한다.

---

## 5. 문서 업데이트 계획

### 5.1 GOP_Restful_Api_연동설계.md 업데이트

#### 5.1.1 문서 헤더 업데이트
- **최종 수정일**: 2026-02-11
- **버전**: v3.8

#### 5.1.2 섹션 추가/변경

| 위치 | 변경 유형 | 내용 |
|------|-----------|------|
| **7.3 뒤** (7.3.x) | 추가 | MappingCamera 독립 List API (GET /mapping-cameras) |
| **7.4 뒤** (7.4.x) | 추가 | MappingSpeaker 독립 List API (GET /mapping-speakers) |
| **7.5 뒤** (7.5.x) | 추가 | MappingLamp 독립 List API (GET /mapping-lamps) |
| **12.1 전체 Endpoint 목록** | 추가 | 신규 3개 엔드포인트 추가 |

각 섹션에 포함할 항목:
- Endpoint, Method, 설명
- Query Parameters 표
- Request Example
- Response Example (Nested Response 포함)
- Error Response (400, 401)

#### 5.1.3 변경 이력 업데이트

```
| v3.8 | 2026-02-11 | **MappingCamera/Speaker/Lamp 독립 List API 추가**<br><br>
**[1. MappingCamera 독립 List API (7.3.x)]**<br>
- GET /api/integrations/mapping-cameras: 전체 MappingCamera 조회<br>
- 필터: event_mapping_id, camera_id, is_enable<br>
**[2. MappingSpeaker 독립 List API (7.4.x)]**<br>
- GET /api/integrations/mapping-speakers: 전체 MappingSpeaker 조회<br>
- 필터: event_mapping_id, speaker_id, is_enable<br>
**[3. MappingLamp 독립 List API (7.5.x)]**<br>
- GET /api/integrations/mapping-lamps: 전체 MappingLamp 조회<br>
- 필터: event_mapping_id, lamp_id, is_enable |
```

#### 5.1.4 삭제 항목

해당 없음. 기존 엔드포인트 및 문서 내용 유지.

### 5.2 GOP_스키마_전체.md 업데이트

#### 5.2.1 문서 헤더 업데이트
- **최종 업데이트**: 2026-02-11
- **기준 API 버전**: v3.8

#### 5.2.2 변경 사항

DB 스키마 변경 없음. 다음 항목만 업데이트:

| 위치 | 변경 유형 | 내용 |
|------|-----------|------|
| **6. Integration 관련 테이블** 도입부 | 추가 | 독립 List API 안내 (읽기 전용, 스키마 변경 없음) |

---

## 6. 구현 작업 목록

> 순서대로 진행. 각 단계에서 테스트 통과 후 다음 단계로 진행.

### Phase 1: MappingCamera 독립 List API

| # | 작업 | 파일 | 유형 |
|---|------|------|------|
| 1-1 | 테스트 작성: `GET /api/integrations/mapping-cameras` 전체 조회 | `tests/` | 행위 변경 |
| 1-2 | CRUD 함수 추가: `get_all_mapping_cameras()` | `app/crud/event_mapping_camera.py` | 행위 변경 |
| 1-3 | flat_router 생성 및 엔드포인트 구현 | `app/routers/event_mapping_cameras.py` | 행위 변경 |
| 1-4 | main.py 라우터 등록 | `app/main.py` | 행위 변경 |
| 1-5 | 필터 테스트 추가 (event_mapping_id, camera_id, is_enable) | `tests/` | 행위 변경 |

### Phase 2: MappingSpeaker 독립 List API

| # | 작업 | 파일 | 유형 |
|---|------|------|------|
| 2-1 | 테스트 작성: `GET /api/integrations/mapping-speakers` 전체 조회 | `tests/` | 행위 변경 |
| 2-2 | CRUD 함수 추가: `get_all_mapping_speakers()` | `app/crud/event_mapping_speaker.py` | 행위 변경 |
| 2-3 | flat_router 생성 및 엔드포인트 구현 | `app/routers/event_mapping_speakers.py` | 행위 변경 |
| 2-4 | main.py 라우터 등록 | `app/main.py` | 행위 변경 |
| 2-5 | 필터 테스트 추가 (event_mapping_id, speaker_id, is_enable) | `tests/` | 행위 변경 |

### Phase 3: MappingLamp 독립 List API

| # | 작업 | 파일 | 유형 |
|---|------|------|------|
| 3-1 | 테스트 작성: `GET /api/integrations/mapping-lamps` 전체 조회 | `tests/` | 행위 변경 |
| 3-2 | CRUD 함수 추가: `get_all_mapping_lamps()` | `app/crud/event_mapping_lamp.py` | 행위 변경 |
| 3-3 | flat_router 생성 및 엔드포인트 구현 | `app/routers/event_mapping_lamps.py` | 행위 변경 |
| 3-4 | main.py 라우터 등록 | `app/main.py` | 행위 변경 |
| 3-5 | 필터 테스트 추가 (event_mapping_id, lamp_id, is_enable) | `tests/` | 행위 변경 |

### Phase 4: 문서 업데이트

| # | 작업 | 파일 | 유형 |
|---|------|------|------|
| 4-1 | GOP_Restful_Api_연동설계.md 헤더 버전/날짜 업데이트 | `GOP_Restful_Api_연동설계.md` | 문서 |
| 4-2 | 7.3 뒤 MappingCamera List API 섹션 추가 | `GOP_Restful_Api_연동설계.md` | 문서 |
| 4-3 | 7.4 뒤 MappingSpeaker List API 섹션 추가 | `GOP_Restful_Api_연동설계.md` | 문서 |
| 4-4 | 7.5 뒤 MappingLamp List API 섹션 추가 | `GOP_Restful_Api_연동설계.md` | 문서 |
| 4-5 | 12.1 전체 Endpoint 목록에 3개 추가 | `GOP_Restful_Api_연동설계.md` | 문서 |
| 4-6 | 변경 이력 v3.8 행 추가 | `GOP_Restful_Api_연동설계.md` | 문서 |
| 4-7 | GOP_스키마_전체.md 헤더 업데이트 | `docs/GOP_스키마_전체.md` | 문서 |
| 4-8 | GOP_스키마_전체.md Integration 섹션 안내 추가 | `docs/GOP_스키마_전체.md` | 문서 |

### Phase 5: Swagger / Docs / Redoc 확인

| # | 작업 | 유형 |
|---|------|------|
| 5-1 | Swagger UI(`/docs`)에서 신규 3개 태그 및 엔드포인트 노출 확인 | 검증 |
| 5-2 | Redoc(`/redoc`)에서 신규 엔드포인트 문서 정상 표시 확인 | 검증 |
| 5-3 | Response 스키마가 기존 계층형 API와 동일한지 확인 | 검증 |

---

## 7. 문서 업데이트 규칙

본 PRD 작업 시 GOP 문서 업데이트는 아래 규칙을 준수한다:

| # | 규칙 | 설명 |
|---|------|------|
| 5-1 | 항목 위치 기반 업데이트 | 해당하는 섹션의 위치에 내용을 추가/변경한다. Camera/Speaker/Lamp 각각의 Response 구조가 다른 곳에서 참조되는 경우 해당 위치도 함께 확인하고 업데이트한다. |
| 5-2 | 변경 항목 삭제 | 기존 내용 중 변경된 사항은 이전 내용을 삭제하고 새 내용으로 교체한다. |
| 5-3 | 문서 헤더 날짜/버전 | 문서 초반 헤더에 날짜와 버전을 업데이트한다. (최종 수정일: 2026-02-11, 버전: v3.8) |
| 5-4 | 부록 변경 이력 | 부록(변경 이력)에 금일 날짜(2026-02-11)로 같은 버전(v3.8)으로 묶어 변경 내용을 정리한다. |
| 5-5 | 참조 문서 제외 | PRD 문서에 대한 참조는 GOP 문서에 포함하지 않는다. |

---

## 8. 서브시스템 연동 흐름 (참고)

```
서브시스템 캐시 구성 흐름:

1. 서브시스템 기동 시 (또는 주기적 갱신)
   GET /api/integrations/mapping-cameras?is_enable=true  → 전체 MappingCamera 캐시
   GET /api/integrations/mapping-speakers?is_enable=true → 전체 MappingSpeaker 캐시
   GET /api/integrations/mapping-lamps?is_enable=true    → 전체 MappingLamp 캐시

2. 이벤트 발생 시
   DetectionEvent.device.device_groups[].id
     → 캐시에서 event_mapping_id 매칭
     → 연동 Camera/Speaker/Lamp 결정
     → 프리셋 실행 / 방송 / 경광등 동작

┌─────────────┐    ┌───────────────────────┐    ┌──────────────────┐
│  서브시스템   │───►│ GET /mapping-cameras  │───►│  로컬 캐시 저장   │
│  (VMS 등)    │    │ GET /mapping-speakers │    │  (전체 목록)      │
│              │    │ GET /mapping-lamps    │    │                  │
└─────────────┘    └───────────────────────┘    └──────────────────┘
                                                        │
                                                        ▼
┌─────────────┐    ┌───────────────────────┐    ┌──────────────────┐
│  이벤트 발생  │───►│ device_group_id 매칭  │───►│  Camera/Speaker/ │
│              │    │ (캐시 조회)           │    │  Lamp 연동 실행   │
└─────────────┘    └───────────────────────┘    └──────────────────┘
```
