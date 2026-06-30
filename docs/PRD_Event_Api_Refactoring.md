# PRD: Event API Request/Response 스펙 정의서

**문서 버전**: v1.3
**작성일**: 2026-01-05
**상태**: Current Implementation
**기반 문서**: PRD_Event_ActionEvent_Refactoring.md v2.1

---

## 1. 개요

### 1.1 목적

이 문서는 Event API의 현재 구현된 Request/Response 포맷을 정의합니다.
PRD_Event_ActionEvent_Refactoring.md v2.1 기반으로 구현된 최종 API 스펙입니다.

### 1.2 주요 변경사항 (v2.1 적용)

| 변경 항목 | Before | After |
|-----------|--------|-------|
| Device 참조 | `controller`, `sensor`, `type_device` (분리) | `device_id` (단일 FK) |
| 그룹 필드 | `group_event` (문자열) | **제거됨** |
| Device 정보 | 없음 | `device` (nested 객체) + `device_description` (스냅샷) |

---

## 2. 공통 스키마

### 2.1 ApiResponse (공통 응답 래퍼)

모든 API 응답은 다음 형식으로 래핑됩니다.

```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": { ... },
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "total_pages": 5
  },
  "meta": {
    "timestamp": "2026-01-05T09:00:00.000Z",
    "request_id": null
  }
}
```

### 2.2 DeviceNestedResponse

Event 응답에 포함되는 Device nested 객체입니다.
Device 타입(Controller, Sensor, Camera)에 따라 포함되는 필드가 다릅니다.

> **참고**: 원본 Device API Response 스펙은 `GOP_Restful_Api_연동설계.md` Section 5.1~5.3 참조

```json
{
  "id": 1,
  "number_device": 1,
  "group_device": 1,
  "name_device": "Test Controller",
  "type_device": "Controller",
  "status": "ACTIVATED",
  "version": "1.0.0",

  // Controller 전용
  "ip_address": "192.168.1.1",
  "ip_port": 8080,

  // Sensor 전용
  "controller_id": 1,

  // Camera 전용
  "rtsp_uri": "rtsp://192.168.1.100:554/stream",
  "rtsp_port": 554,
  "mode": "DETECTION",
  "category": "PTZ",
  "is_record": true
}
```

#### 2.2.1 DeviceNestedResponse 필드 정의

| # | 필드 | 타입 | 필수 | 설명 |
|---|------|------|------|------|
| 1 | `id` | integer | O | Device ID |
| 2 | `number_device` | integer | O | 장치 번호 |
| 3 | `group_device` | integer | O | 장치 그룹 번호 (레거시) |
| 4 | `name_device` | string | O | 장치 이름 |
| 5 | `type_device` | string | O | 장치 타입 (Controller/Multi/Fence/IpCamera 등) |
| 6 | `status` | string | O | 장치 상태 (ACTIVATED/DEACTIVATED) |
| 7 | `version` | string | X | 장치 버전 |
| 8 | `ip_address` | string | X | IP 주소 (Controller, Camera) |
| 9 | `ip_port` | integer | X | 포트 번호 (Controller, Camera) |
| 10 | `controller_id` | integer | X | 소속 컨트롤러 ID (Sensor) |
| 11 | `rtsp_uri` | string | X | RTSP 스트림 URI (Camera) |
| 12 | `rtsp_port` | integer | X | RTSP 포트 (Camera) |
| 13 | `mode` | string | X | 카메라 모드 (Camera) |
| 14 | `category` | string | X | 카메라 카테고리 (Camera) |
| 15 | `is_record` | boolean | X | 녹화 활성화 여부 (Camera) |
| 16 | `device_groups` | array | O | **소속 DeviceGroup 목록 (EventMapping 조회 필수)** |

> **⚠️ 중요**: `device_groups` 필드는 EventMapping 연동을 위해 **필수**입니다.
> Event 발생 시 `device_groups[].id` → `EventMapping.device_group_id` 매칭으로 카메라 프리셋 실행을 결정합니다.

---

#### 2.2.2 원본 Device Response vs DeviceNestedResponse 비교

DeviceNestedResponse는 Event 응답에 포함되는 **경량화된 버전**입니다.
원본 Device API Response에서 불필요한 필드를 제외하고 핵심 정보만 포함합니다.

##### Controller Response 비교

| # | 필드 | 원본 ControllerResponse | DeviceNestedResponse | 비고 |
|---|------|:----------------------:|:--------------------:|------|
| 1 | `id` | ✅ | ✅ | 동일 |
| 2 | `number_device` | ✅ | ✅ | 동일 |
| 3 | `group_device` | ✅ | ✅ | 동일 |
| 4 | `name_device` | ✅ | ✅ | 동일 |
| 5 | `type_device` | ✅ | ✅ | 동일 |
| 6 | `version` | ✅ | ✅ | 동일 |
| 7 | `status` | ✅ | ✅ | 동일 |
| 8 | `ip_address` | ✅ | ✅ | 동일 |
| 9 | `ip_port` | ✅ | ✅ | 동일 |
| 10 | `created_at` | ✅ | ❌ | **제외** - Event에 자체 timestamp 존재 |
| 11 | `updated_at` | ✅ | ❌ | **제외** - Event에 자체 timestamp 존재 |
| 12 | `sensors` | ✅ (optional) | ❌ | **제외** - 센서 목록 불필요 |
| 13 | `device_groups` | ✅ | ✅ | **포함** - EventMapping 연동 필수 (FK 역할) |

##### Sensor Response 비교

| # | 필드 | 원본 SensorResponse | DeviceNestedResponse | 비고 |
|---|------|:-------------------:|:--------------------:|------|
| 1 | `id` | ✅ | ✅ | 동일 |
| 2 | `number_device` | ✅ | ✅ | 동일 |
| 3 | `group_device` | ✅ | ✅ | 동일 |
| 4 | `name_device` | ✅ | ✅ | 동일 |
| 5 | `type_device` | ✅ | ✅ | 동일 |
| 6 | `version` | ✅ | ✅ | 동일 |
| 7 | `status` | ✅ | ✅ | 동일 |
| 8 | `controller_id` | ✅ | ✅ | 동일 |
| 9 | `created_at` | ✅ | ❌ | **제외** - Event에 자체 timestamp 존재 |
| 10 | `updated_at` | ✅ | ❌ | **제외** - Event에 자체 timestamp 존재 |
| 11 | `controller` | ✅ (optional) | ❌ | **제외** - 컨트롤러 nested 불필요 |
| 12 | `device_groups` | ✅ | ✅ | **포함** - EventMapping 연동 필수 (FK 역할) |

##### Camera Response 비교

| # | 필드 | 원본 CameraResponse | DeviceNestedResponse | 비고 |
|---|------|:-------------------:|:--------------------:|------|
| 1 | `id` | ✅ | ✅ | 동일 |
| 2 | `number_device` | ✅ | ✅ | 동일 |
| 3 | `group_device` | ✅ | ✅ | 동일 |
| 4 | `name_device` | ✅ | ✅ | 동일 |
| 5 | `type_device` | ✅ | ✅ | 동일 |
| 6 | `version` | ✅ | ✅ | 동일 |
| 7 | `status` | ✅ | ✅ | 동일 |
| 8 | `ip_address` | ✅ | ✅ | 동일 |
| 9 | `ip_port` | ✅ | ✅ | 동일 |
| 10 | `user_name` | ✅ | ❌ | **제외** - 보안 정보 |
| 11 | `user_password` | ✅ | ❌ | **제외** - 보안 정보 |
| 12 | `rtsp_uri` | ✅ | ✅ | 동일 |
| 13 | `rtsp_port` | ✅ | ✅ | 동일 |
| 14 | `mode` | ✅ | ✅ | 동일 |
| 15 | `category` | ✅ | ✅ | 동일 |
| 16 | `is_record` | ✅ | ✅ | 동일 |
| 17 | `hardware_spec` | ✅ (JSON) | ❌ | **제외** - 상세 하드웨어 정보 불필요 |
| 18 | `geolocation` | ✅ (JSON) | ❌ | **제외** - 위치 정보 불필요 |
| 19 | `created_at` | ✅ | ❌ | **제외** - Event에 자체 timestamp 존재 |
| 20 | `updated_at` | ✅ | ❌ | **제외** - Event에 자체 timestamp 존재 |
| 21 | `device_groups` | ✅ | ✅ | **포함** - EventMapping 연동 필수 (FK 역할) |

---

#### 2.2.3 제외된 필드 요약

| 구분 | 제외된 필드 | 제외 사유 |
|------|------------|-----------|
| **공통** | `created_at`, `updated_at` | Event 자체에 timestamp 존재하여 중복 |
| **Controller** | `sensors` | 센서 목록은 Event 조회 시 불필요 |
| **Sensor** | `controller` | 컨트롤러 nested 객체는 불필요 (controller_id로 충분) |
| **Camera** | `user_name`, `user_password` | 보안 정보는 Event 응답에 노출 금지 |
| **Camera** | `hardware_spec`, `geolocation` | 상세 정보는 Device API에서 별도 조회 |

#### 2.2.4 포함 필수 필드 (EventMapping 연동)

| 필드 | 포함 사유 |
|------|-----------|
| `device_groups` | **EventMapping FK 역할**: Event 발생 시 `device_groups[].id` → `EventMapping.device_group_id` 매칭으로 카메라 프리셋 자동 실행 |

```
[Event 발생] → device.device_groups[].id → EventMapping.device_group_id → 카메라 프리셋 실행
```

---

#### 2.2.5 Device 타입별 DeviceNestedResponse 예시

##### Controller 예시
```json
{
  "id": 1,
  "number_device": 1,
  "group_device": 1,
  "name_device": "Controller-A",
  "type_device": "Controller",
  "status": "ACTIVATED",
  "version": "v2.1.0",
  "ip_address": "192.168.1.100",
  "ip_port": 8001,
  "controller_id": null,
  "rtsp_uri": null,
  "rtsp_port": null,
  "mode": null,
  "category": null,
  "is_record": null,
  "device_groups": [
    {"id": 1, "name": "GOP 1구역"}
  ]
}
```

##### Sensor 예시
```json
{
  "id": 101,
  "number_device": 1,
  "group_device": 1,
  "name_device": "Sensor-A-1",
  "type_device": "Multi",
  "status": "ACTIVATED",
  "version": "v1.5.0",
  "ip_address": null,
  "ip_port": null,
  "controller_id": 1,
  "rtsp_uri": null,
  "rtsp_port": null,
  "mode": null,
  "category": null,
  "is_record": null,
  "device_groups": [
    {"id": 1, "name": "GOP 1구역"},
    {"id": 2, "name": "야간 감시"}
  ]
}
```

##### Camera 예시
```json
{
  "id": 201,
  "number_device": 109,
  "group_device": 1,
  "name_device": "Camera-109",
  "type_device": "IpCamera",
  "status": "ACTIVATED",
  "version": "v3.2.1",
  "ip_address": "192.168.1.109",
  "ip_port": 80,
  "controller_id": null,
  "rtsp_uri": "rtsp://192.168.1.109:554/stream1",
  "rtsp_port": 554,
  "mode": "ONVIF",
  "category": "PTZ",
  "is_record": true,
  "device_groups": [
    {"id": 1, "name": "GOP 1구역"},
    {"id": 3, "name": "PTZ 카메라"}
  ]
}
```

### 2.3 Enum Values

#### 2.3.1 type_event
```
None | Intrusion | ContactOn | ContactOff | Connection | Action | Fault | WindyMode | Lowlight | DetectionMode | TrackingMode
```

#### 2.3.2 type_device
```
NONE | Controller | Multi | Fence | Underground | Contact | PIR | IoController | Laser | Cable | IpCamera | SmartSensor | SmartSensor2 | SmartCompound | IpSpeaker | Radar | OpticalCable | Fence_Group
```

#### 2.3.3 result (Detection)
```
NONE | CABLE_CUTTING | CABLE_CONNECTED | PIR_SENSOR | THERMAL_SENSOR | VIBRATION_SENSOR | CONTACT_SENSOR | DISTANCE_SENSOR | AI_DETECT
```

#### 2.3.4 reason (Malfunction)
```
FAULT_CONTROLLER | FAULT_FENCE | FAULT_MULTI | FAULT_CABLE_CUTTING | FAULT_ETC
```

#### 2.3.5 action_reported
```
True | False
```

---

## 3. Detection Event API

탐지 이벤트(침입 감지 등) 관리 API

### 3.1 GET /api/events/detections

탐지 이벤트 목록 조회 (페이지네이션)

#### Query Parameters

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|------|--------|------|
| `page` | integer | X | 1 | 페이지 번호 |
| `limit` | integer | X | 20 | 페이지당 항목 수 (최대 100) |
| `device_id` | integer | X | - | 장치 ID로 필터링 |
| `action_reported` | string | X | - | 조치보고 여부로 필터링 |
| `result` | string | X | - | 결과 유형으로 필터링 |
| `start_date` | datetime | X | - | 시작 날짜 필터 |
| `end_date` | datetime | X | - | 종료 날짜 필터 |

#### Response (200 OK)

```json
{
  "success": true,
  "message": "Detection events retrieved successfully",
  "data": [
    {
      "id": 1,
      "category_event": "detection",
      "type_event": "Intrusion",
      "action_reported": "False",
      "result": "PIR_SENSOR",
      "device": {
        "id": 1,
        "number_device": 1,
        "group_device": 1,
        "name_device": "Test Controller",
        "type_device": "Controller",
        "status": "ACTIVATED",
        "version": "1.0.0",
        "ip_address": "192.168.1.1",
        "ip_port": 8080,
        "controller_id": null,
        "rtsp_uri": null,
        "rtsp_port": null,
        "mode": null,
        "category": null,
        "is_record": null,
        "device_groups": [
          {"id": 1, "name": "GOP 1구역"}
        ]
      },
      "device_description": "[Controller] Test Controller (number: 1, id: 1)",
      "created_at": "2026-01-05T18:23:52.097738",
      "updated_at": "2026-01-05T18:23:52.097738"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 1,
    "total_pages": 1
  }
}
```

> **v1.3 변경사항**: Response에서 `device_id`, `sequence` 필드 제거됨
> - `device_id`: Device nested 객체에 `id` 포함되어 중복
> - `sequence`: Request 전용 필드로, Response에 불필요

### 3.2 GET /api/events/detections/{event_id}

탐지 이벤트 단건 조회

#### Path Parameters

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `event_id` | integer | O | 이벤트 ID |

#### Response (200 OK)

```json
{
  "success": true,
  "message": "Detection event retrieved successfully",
  "data": {
    "id": 1,
    "category_event": "detection",
    "type_event": "Intrusion",
    "action_reported": "False",
    "result": "PIR_SENSOR",
    "device": { ... },
    "device_description": "[Controller] Test Controller (number: 1, id: 1)",
    "created_at": "2026-01-05T18:23:52.097738",
    "updated_at": "2026-01-05T18:23:52.097738"
  }
}
```

### 3.3 POST /api/events/detections

탐지 이벤트 생성

#### Request Body

```json
{
  "type_event": "Intrusion",
  "device_id": 1,
  "sequence": 1,
  "action_reported": "False",
  "result": "PIR_SENSOR"
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `type_event` | string | O | 이벤트 유형 |
| `device_id` | integer | O | 장치 ID (Device FK) |
| `sequence` | integer | O | 시퀀스 번호 |
| `action_reported` | string | O | 조치 보고 여부 ("True"/"False") |
| `result` | string | O | 탐지 결과 |

> **Note**: `group_event`, `controller`, `sensor`, `type_device` 필드는 PRD v2.1에서 제거되었습니다.

#### Response (201 Created)

```json
{
  "success": true,
  "message": "Detection event created successfully",
  "data": {
    "id": 1,
    "category_event": "detection",
    "type_event": "Intrusion",
    "action_reported": "False",
    "result": "PIR_SENSOR",
    "device": {
      "id": 1,
      "number_device": 1,
      "group_device": 1,
      "name_device": "Test Controller",
      "type_device": "Controller",
      "status": "ACTIVATED",
      "version": "1.0.0",
      "ip_address": "192.168.1.1",
      "ip_port": 8080,
      "device_groups": [...]
    },
    "device_description": "[Controller] Test Controller (number: 1, id: 1)",
    "created_at": "2026-01-05T18:23:52.097738",
    "updated_at": "2026-01-05T18:23:52.097738"
  }
}
```

### 3.4 PATCH /api/events/detections/{event_id}

탐지 이벤트 부분 수정

#### Request Body (모든 필드 선택적)

```json
{
  "type_event": "Intrusion",
  "sequence": 2,
  "action_reported": "True",
  "result": "THERMAL_SENSOR"
}
```

> **Note**: `device_id`는 수정 불가 (이벤트 생성 시에만 설정)

### 3.5 PUT /api/events/detections/{event_id}

탐지 이벤트 전체 수정

#### Request Body (모든 필드 필수)

```json
{
  "type_event": "Intrusion",
  "device_id": 1,
  "sequence": 1,
  "action_reported": "False",
  "result": "PIR_SENSOR"
}
```

### 3.6 DELETE /api/events/detections/{event_id}

탐지 이벤트 삭제

#### Response (200 OK)

```json
{
  "success": true,
  "message": "Detection event deleted successfully",
  "data": null
}
```

---

## 4. Malfunction Event API

장애 이벤트 관리 API

### 4.1 GET /api/events/malfunctions

장애 이벤트 목록 조회 (페이지네이션)

#### Query Parameters

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|------|--------|------|
| `page` | integer | X | 1 | 페이지 번호 |
| `limit` | integer | X | 20 | 페이지당 항목 수 (최대 100) |
| `device_id` | integer | X | - | 장치 ID로 필터링 |
| `action_reported` | string | X | - | 조치보고 여부로 필터링 |
| `reason` | string | X | - | 장애 원인으로 필터링 |
| `start_date` | datetime | X | - | 시작 날짜 필터 |
| `end_date` | datetime | X | - | 종료 날짜 필터 |

#### Response (200 OK)

```json
{
  "success": true,
  "message": "Malfunction events retrieved successfully",
  "data": [
    {
      "id": 2,
      "category_event": "malfunction",
      "type_event": "Fault",
      "action_reported": "False",
      "reason": "FAULT_CONTROLLER",
      "first_start": 0,
      "first_end": 0,
      "second_start": 0,
      "second_end": 0,
      "device": {
        "id": 1,
        "number_device": 1,
        "group_device": 1,
        "name_device": "Test Controller",
        "type_device": "Controller",
        "status": "ACTIVATED",
        "version": "1.0.0",
        "ip_address": "192.168.1.1",
        "ip_port": 8080,
        "device_groups": [...]
      },
      "device_description": "[Controller] Test Controller (number: 1, id: 1)",
      "created_at": "2026-01-05T18:24:07.478959",
      "updated_at": "2026-01-05T18:24:07.478959"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 1,
    "total_pages": 1
  }
}
```

> **v1.3 변경사항**: Response에서 `device_id`, `sequence` 필드 제거됨

### 4.2 POST /api/events/malfunctions

장애 이벤트 생성

#### Request Body

```json
{
  "type_event": "Fault",
  "device_id": 1,
  "sequence": 1,
  "action_reported": "False",
  "reason": "FAULT_CONTROLLER",
  "first_start": 0,
  "first_end": 0,
  "second_start": 0,
  "second_end": 0
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `type_event` | string | O | 이벤트 유형 |
| `device_id` | integer | O | 장치 ID (Device FK) |
| `sequence` | integer | O | 시퀀스 번호 |
| `action_reported` | string | O | 조치 보고 여부 |
| `reason` | string | O | 장애 원인 |
| `first_start` | integer | O | 첫 번째 구간 시작 |
| `first_end` | integer | O | 첫 번째 구간 종료 |
| `second_start` | integer | O | 두 번째 구간 시작 |
| `second_end` | integer | O | 두 번째 구간 종료 |

#### Response (201 Created)

```json
{
  "success": true,
  "message": "Malfunction event created successfully",
  "data": {
    "id": 2,
    "category_event": "malfunction",
    "type_event": "Fault",
    "action_reported": "False",
    "reason": "FAULT_CONTROLLER",
    "first_start": 0,
    "first_end": 0,
    "second_start": 0,
    "second_end": 0,
    "device": { ... },
    "device_description": "[Controller] Test Controller (number: 1, id: 1)",
    "created_at": "2026-01-05T18:24:07.478959",
    "updated_at": "2026-01-05T18:24:07.478959"
  }
}
```

---

## 5. Connection Event API

연결 이벤트 관리 API

### 5.1 GET /api/events/connections

연결 이벤트 목록 조회 (페이지네이션)

#### Query Parameters

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|------|--------|------|
| `page` | integer | X | 1 | 페이지 번호 |
| `limit` | integer | X | 20 | 페이지당 항목 수 (최대 100) |
| `device_id` | integer | X | - | 장치 ID로 필터링 |
| `start_date` | datetime | X | - | 시작 날짜 필터 |
| `end_date` | datetime | X | - | 종료 날짜 필터 |

#### Response (200 OK)

```json
{
  "success": true,
  "message": "Connection events retrieved successfully",
  "data": [
    {
      "id": 3,
      "category_event": "connection",
      "type_event": "Connection",
      "device": {
        "id": 1,
        "number_device": 1,
        "group_device": 1,
        "name_device": "Test Controller",
        "type_device": "Controller",
        "status": "ACTIVATED",
        "version": "1.0.0",
        "ip_address": "192.168.1.1",
        "ip_port": 8080,
        "device_groups": [...]
      },
      "device_description": "[Controller] Test Controller (number: 1, id: 1)",
      "created_at": "2026-01-05T18:24:13.699879",
      "updated_at": "2026-01-05T18:24:13.699879"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 1,
    "total_pages": 1
  }
}
```

> **v1.3 변경사항**: Response에서 `device_id`, `sequence` 필드 제거됨

### 5.2 POST /api/events/connections

연결 이벤트 생성

#### Request Body

```json
{
  "type_event": "Connection",
  "device_id": 1,
  "sequence": 1
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `type_event` | string | O | 이벤트 유형 |
| `device_id` | integer | O | 장치 ID (Device FK) |
| `sequence` | integer | O | 시퀀스 번호 |

> **Note**: Connection Event는 Detection/Malfunction과 달리 `action_reported`, `result`, `reason` 등의 추가 필드가 없습니다.

#### Response (201 Created)

```json
{
  "success": true,
  "message": "Connection event created successfully",
  "data": {
    "id": 3,
    "category_event": "connection",
    "type_event": "Connection",
    "device": { ... },
    "device_description": "[Controller] Test Controller (number: 1, id: 1)",
    "created_at": "2026-01-05T18:24:13.699879",
    "updated_at": "2026-01-05T18:24:13.699879"
  }
}
```

### 5.3 PATCH /api/events/connections/{event_id}

연결 이벤트 부분 수정

#### Request Body (모든 필드 선택적)

```json
{
  "type_event": "Connection",
  "sequence": 2
}
```

> **Note**: `device_id`는 수정 불가

### 5.4 PUT /api/events/connections/{event_id}

연결 이벤트 전체 수정

#### Request Body (모든 필드 필수)

```json
{
  "type_event": "Connection",
  "device_id": 1,
  "sequence": 1
}
```

---

## 6. Action Event API

조치 이벤트 관리 API (Detection/Malfunction/Connection 이벤트에 대한 조치 기록)

### 6.1 POST /api/events/detections/{event_id}/action

탐지 이벤트에 대한 조치 생성

#### Request Body

```json
{
  "type_event": "Action",
  "content": "침입 확인 및 경비 출동",
  "user": "operator1",
  "from_event_id": 1
}
```

> **PRD v1.5**: `from_type_event` 필드 제거됨. `from_event_id`만으로 원본 이벤트를 참조하며, polymorphic relationship을 통해 이벤트 타입이 자동으로 확인됩니다.

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `type_event` | string | O | 이벤트 유형 ("Action") |
| `content` | string | O | 조치 내용 |
| `user` | string | O | 조치자 |
| `from_event_id` | integer | O | 원본 이벤트 ID (events.id FK) |
| `created_at` | datetime | X | 생성 일시 (미입력시 자동) |

#### Response (201 Created)

```json
{
  "success": true,
  "message": "Action event created successfully",
  "data": {
    "id": 1,
    "type_event": "Action",
    "content": "침입 확인 및 경비 출동",
    "user": "operator1",
    "from_event": {
      "id": 1,
      "type_event": "Intrusion",
      "action_reported": "True",
      "result": "PIR_SENSOR",
      "device": { ... },
      "device_description": "[Controller] Test Controller (number: 1, id: 1)",
      "created_at": "2026-01-05T18:23:52.097738",
      "updated_at": "2026-01-05T18:23:52.097738"
    },
    "created_at": "2026-01-05T18:30:00.000000",
    "updated_at": "2026-01-05T18:30:00.000000"
  }
}
```

### 6.2 GET /api/events/detections/{event_id}/action

특정 탐지 이벤트의 조치 조회

---

## 7. Response 필드 상세

### 7.1 Detection Event Response

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `id` | integer | O | 이벤트 ID |
| `type_event` | string | O | 이벤트 유형 |
| `action_reported` | string | O | 조치 보고 여부 |
| `result` | string | O | 탐지 결과 |
| `device` | object | X | 장치 정보 (Device 삭제 시 null) |
| `device_description` | string | X | 장치 정보 스냅샷 (Device 삭제 후에도 유지) |
| `created_at` | datetime | O | 생성 일시 |
| `updated_at` | datetime | O | 수정 일시 |

> **v1.3**: `device_id`, `sequence` 필드 제거됨 (device.id에 포함, sequence는 Request 전용)
> **v1.4**: `category_event` 필드 제거됨 (polymorphic inheritance 내부용 필드)

### 7.2 Malfunction Event Response

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `id` | integer | O | 이벤트 ID |
| `type_event` | string | O | 이벤트 유형 |
| `action_reported` | string | O | 조치 보고 여부 |
| `reason` | string | O | 장애 원인 |
| `first_start` | integer | O | 첫 번째 구간 시작 |
| `first_end` | integer | O | 첫 번째 구간 종료 |
| `second_start` | integer | O | 두 번째 구간 시작 |
| `second_end` | integer | O | 두 번째 구간 종료 |
| `device` | object | X | 장치 정보 |
| `device_description` | string | X | 장치 정보 스냅샷 |
| `created_at` | datetime | O | 생성 일시 |
| `updated_at` | datetime | O | 수정 일시 |

> **v1.3**: `device_id`, `sequence` 필드 제거됨 (device.id에 포함, sequence는 Request 전용)
> **v1.4**: `category_event` 필드 제거됨 (polymorphic inheritance 내부용 필드)

### 7.3 Connection Event Response

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `id` | integer | O | 이벤트 ID |
| `type_event` | string | O | 이벤트 유형 |
| `device` | object | X | 장치 정보 |
| `device_description` | string | X | 장치 정보 스냅샷 |
| `created_at` | datetime | O | 생성 일시 |
| `updated_at` | datetime | O | 수정 일시 |

> **v1.3**: `device_id`, `sequence` 필드 제거됨 (device.id에 포함, sequence는 Request 전용)
> **v1.4**: `category_event` 필드 제거됨 (polymorphic inheritance 내부용 필드)

---

## 8. device_description 포맷

이벤트 생성 시 `device_description`이 자동으로 생성됩니다.

### 8.1 포맷

```
"[{type_device}] {name_device} (number: {number_device}, id: {device_id})"
```

### 8.2 예시

```
"[Controller] Test Controller (number: 1, id: 1)"
"[Fence] Sensor-A-1 (number: 5, id: 101)"
"[IpCamera] Camera-A-1 (number: 1, id: 201)"
```

### 8.3 동기화 규칙

| 시나리오 | device_id | device_description |
|----------|-----------|-------------------|
| Event 생성 | Device ID | 자동 생성 |
| Device 삭제 | NULL | 기존 값 유지 (영속성) |
| PUT으로 device_id 변경 | 새 Device ID | 새 Device 정보로 업데이트 |

---

## 9. 에러 응답

### 9.1 400 Bad Request

```json
{
  "success": false,
  "message": "Device with id 999 not found",
  "data": null
}
```

### 9.2 404 Not Found

```json
{
  "success": false,
  "message": "Detection event with id 999 not found",
  "data": null
}
```

### 9.3 422 Unprocessable Entity

```json
{
  "success": false,
  "message": "Validation error: body.device_id: Field required",
  "data": null
}
```

### 9.4 500 Internal Server Error

```json
{
  "success": false,
  "message": "Internal server error: ...",
  "data": null
}
```

---

## 10. 제거된 필드 (PRD v2.1)

다음 필드들은 PRD v2.1에서 제거되었으며, API에서 더 이상 사용되지 않습니다.

### 10.1 Request에서 제거된 필드

| 필드 | 대체 방법 |
|------|-----------|
| `group_event` | 제거됨 (DeviceGroup은 device_id를 통해 조회) |
| `controller` | `device_id`로 대체 |
| `sensor` | `device_id`로 대체 |
| `type_device` | `device_id`로 Device 조회 후 확인 |

### 10.2 Query Parameter에서 제거된 필드

| 필드 | 대체 방법 |
|------|-----------|
| `controller` | `device_id` |
| `sensor` | `device_id` |
| `type_device` | `device_id` |
| `group_event` | 제거됨 |

---

## 11. 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| **v1.0** | 2026-01-05 | 초기 문서 작성 (PRD v2.1 기반 현재 구현 상태 문서화) |
| **v1.1** | 2026-01-05 | Section 2.2 DeviceNestedResponse 상세화: 원본 Device Response와 비교표 추가 (Controller/Sensor/Camera 각 타입별), 제외 필드 사유, 타입별 예시 추가 |
| **v1.2** | 2026-01-05 | `device_groups` 필드 **포함** 변경: EventMapping 연동을 위한 FK 역할로 필수 포함 (Section 2.2.4 추가) |
| **v1.3** | 2026-01-05 | **Event Response에서 `device_id`, `sequence` 필드 제거**<br>• `device_id`: Device nested 객체에 `id` 포함되어 중복<br>• `sequence`: Request 전용 필드로, Response에 불필요<br>• 영향 API: Detection/Malfunction/Connection Event 모든 Response |
| **v1.4** | 2026-01-06 | **Event Response에서 `category_event` 필드 제거**<br>• `category_event`: polymorphic inheritance 내부용 필드로 Response에 불필요<br>• 영향 API: Detection/Malfunction/Connection Event 모든 Response |
| **v1.5** | 2026-01-06 | **ActionEvent Request에서 `from_type_event` 필드 제거**<br>• `from_type_event`: `from_event_id`가 `events.id`를 참조하므로 polymorphic relationship으로 이벤트 타입 자동 확인 가능<br>• `from_event` → `from_event_id`로 필드명 변경 (명확성)<br>• 영향 API: ActionEvent 생성/수정 (POST, PATCH, PUT)<br>• 코드 변경: `actions.py`에서 `build_source_event_response()` 함수 사용, polymorphic query 적용 |

---

**문서 종료**
