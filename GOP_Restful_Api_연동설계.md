# GOP RESTful API 연동 설계서

**작성일**: 2025-11-12  
**작성자**: 이기호 차장  
**목적**: GOP용 통제시스템에 연동하기 위한 RESTful API기반 메시지   시스템 구성  
**설계 원칙**: 기존 DTO 구조를 그대로 사용하여 일관성 확보

---

## 목차

1. [개요](#1-개요)
2. [API 구조 및 규칙](#2-api-구조-및-규칙)
3. [공통 사양](#3-공통-사양)
4. [Enum 타입 정의](#4-enum-타입-정의)
5. [Device API 설계](#5-device-api-설계)
6. [Event API 설계](#6-event-api-설계)
7. [Integration API 설계](#7-integration-api-설계)
8. [에러 처리](#8-에러-처리)
9. [부록](#9-부록)

---

## 1. 개요

### 1.1 설계 목적

기존 서비스를 **RESTful API 기반**으로 전환하여:

- ✅ **클라이언트**: DB 연결 불필요, HTTP API로 요청
- ✅ **통제 서비스 (Control Service)**: PostgreSQL DB 접근 권한 보유
- ✅ **보안 강화**: DB 접근 권한 중앙화
- ✅ **확장성**: 마이크로서비스 아키텍처 지원
- ✅ **DTO 일관성**: 기존 DTO 구조를 그대로 사용하여 호환성 유지
- ✅ **표준 준수**: HTTP 표준 메서드 및 상태 코드 사용

### 1.2 시스템 아키텍처

```
┌──────────────┐              ┌──────────────────┐               ┌──────────────┐
│   Client A   │              │  Control Service │               │ PostgreSQL   │
│ (NvrManager) │◄── HTTP ────►│  (RESTful API)   │◄─────────────►│   Database   │
└──────────────┘    Request   └──────────────────┘   Direct DB   └──────────────┘
                                       │               Access
┌──────────────┐                       │
│   Client B   │                       │
│    (GIS)     │◄──────────────────────┘
└──────────────┘
```

**핵심 원칙**:
- 클라이언트는 **HTTP Endpoint**로 요청
- 통제 서비스가 **PostgreSQL**에서 데이터 조회/수정
- Response는 JSON 형식으로 반환

---

## 2. API 구조 및 규칙

### 2.1 Base URL

```
http(s)://{server}:{port}/api
```

**예제**:
- 개발: `http://localhost:5000/api`
- 운영: `https://control-service.company.com/api`

### 2.2 URL 명명 규칙

**패턴**: `/api/{resource}/{sub-resource}/{id}`

**리소스 규칙**:
- 복수형 명사 사용 (devices, events)
- 소문자 사용
- 단어 구분은 하이픈(-) 사용

**예제**:
- `/api/devices/controllers` - Controller 목록
- `/api/devices/controllers/{id}` - 특정 Controller
- `/api/devices/sensors` - Sensor 목록
- `/api/devices/cameras` - Camera 목록
- `/api/events/detections` - Detection Event 목록
- `/api/events/malfunctions` - Malfunction Event 목록
- `/api/events/connections` - Connection Event 목록
- `/api/events/actions` - Action Event 목록

### 2.3 HTTP 메서드

| 메서드 | 용도 | 설명 |
|--------|------|------|
| GET | 조회 | 리소스 조회 (목록 또는 단일) |
| POST | 생성 | 새로운 리소스 생성 |
| PUT | 전체 수정 | 리소스 전체 데이터 수정 |
| PATCH | 부분 수정 | 리소스 일부 데이터 수정 |
| DELETE | 삭제 | 리소스 삭제 |

### 2.4 Query String 파라미터

목록 조회 시 필터링 및 페이징에 사용:

**예제**:
```
GET /api/devices/controllers?group_device=1&status=ACTIVATED&page=1&limit=20
GET /api/events/detections?start_date=2025-01-01T00:00:00.000Z&end_date=2025-01-31T23:59:59.999Z&status=True
```

**공통 파라미터**:
- `page`: 페이지 번호 (기본값: 1)
- `limit`: 페이지당 항목 수 (기본값: 20, 최대: 100)
- `sort`: 정렬 기준 (예: `created_at`, `-created_at`)

---

## 3. 공통 사양

### 3.1 Request 헤더

```http
Content-Type: application/json
Accept: application/json
Authorization: Bearer {token} (이 부분은 아직 합의된 내용이 없음)
X-Client-UUID: {client-uuid} //선택적 참고용
X-Request-ID: {request-uuid} //선택적 참고용
```

**필수 헤더**:
- `Content-Type`: POST, PUT, PATCH 요청 시 필수
- `Authorization`: 인증 토큰 (Bearer 방식)

**선택 헤더**:
- `X-Client-UUID`: 클라이언트 식별자
- `X-Request-ID`: 요청 추적용 UUID

### 3.2 Response 형식

#### 성공 응답 (200, 201)

```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": {
    // 실제 데이터
  },
  "meta": {
    "timestamp": "2025-01-10T10:30:00.000Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

#### 목록 응답 (200)

```json
{
  "success": true,
  "message": "25 items retrieved",
  "data": [
    // 배열 데이터
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 25,
    "total_pages": 2
  },
  "meta": {
    "timestamp": "2025-01-10T10:30:00.000Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

#### 에러 응답 (4xx, 5xx)

```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Controller not found with Id=999",
    "details": "No controller exists with the specified ID"
  },
  "meta": {
    "timestamp": "2025-01-10T10:30:00.000Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### 3.3 HTTP 상태 코드

| 코드 | 설명 | 사용 시점 |
|------|------|-----------|
| 200 OK | 성공 | GET, PUT, PATCH, DELETE 성공 |
| 201 Created | 생성 완료 | POST 성공 |
| 204 No Content | 내용 없음 | DELETE 성공 (응답 본문 없음) |
| 400 Bad Request | 잘못된 요청 | 요청 데이터 검증 실패 |
| 401 Unauthorized | 인증 실패 | 인증 토큰 없음 또는 만료 |
| 403 Forbidden | 권한 없음 | 리소스 접근 권한 없음 |
| 404 Not Found | 리소스 없음 | 요청한 리소스가 존재하지 않음 |
| 409 Conflict | 충돌 | 중복 리소스 생성 시도 |
| 422 Unprocessable Entity | 처리 불가 | 요청은 올바르나 비즈니스 로직 오류 |
| 500 Internal Server Error | 서버 오류 | 서버 내부 오류 |
| 503 Service Unavailable | 서비스 불가 | 서버 점검 또는 과부하 |

---

## 4. Enum 타입 정의

> **참조**: `Ironwall.Dotnet.Libraries.Enums` 프로젝트

모든 Enum은 **문자열(string)** 형식으로 전송됩니다.

### 4.1 Device Enum

#### EnumDeviceType
```csharp
//C# 데이터 (참고용)
public enum EnumDeviceType : int
{
    NONE = 0,              // "NONE"
    Controller = 1,        // "Controller" - 제어기
    Multi = 2,             // "Multi" - 복합 센서
    Fence = 3,             // "Fence" - 펜스 센서
    Underground = 4,       // "Underground" - 지중 센서
    Contact = 5,           // "Contact" - 접점 센서
    PIR = 6,               // "PIR" - PIR 센서
    IoController = 7,      // "IoController" - IO 제어기
    Laser = 8,             // "Laser" - 레이저 센서
    Cable = 9,             // "Cable" - 케이블 센서
    IpCamera = 10,         // "IpCamera" - IP 카메라
    SmartSensor = 11,      // "SmartSensor" - 스마트 센서
    SmartSensor2 = 12,     // "SmartSensor2" - 스마트 센서2
    SmartCompound = 13,    // "SmartCompound" - 스마트 복합
    IpSpeaker = 14,        // "IpSpeaker" - IP 스피커
    Radar = 15,            // "Radar" - 레이더
    OpticalCable = 16,     // "OpticalCable" - 광케이블
    Fence_Group = 17       // "Fence_Group" - 펜스 그룹
}
```

#### EnumDeviceStatus
```csharp
//C# 데이터 (참고용)
public enum EnumDeviceStatus
{
    ACTIVATED,      // "ACTIVATED" - 활성화
    ERROR,          // "ERROR" - 오류
    DEACTIVATED     // "DEACTIVATED" - 비활성화
}
```

#### EnumCameraMode
```csharp
//C# 데이터 (참고용)
public enum EnumCameraMode
{
    NONE,           // "NONE"
    ONVIF,          // "ONVIF" - ONVIF 프로토콜
    EMSTONE_API,    // "EMSTONE_API" - Emstone API
    INNODEP_API,    // "INNODEP_API" - Innodep API
    ETC             // "ETC" - 기타
}
```

#### EnumCameraType
```csharp
//C# 데이터 (참고용)
public enum EnumCameraType
{
    NONE,           // "NONE"
    FIXED,          // "FIXED" - 고정 카메라
    PTZ             // "PTZ" - Pan-Tilt-Zoom 카메라
}
```

### 4.2 Event Enum

#### EnumEventType
```csharp
//C# 데이터 (참고용) - 2025-11-28 업데이트
public enum EnumEventType : int
{
    None = 0,           // "None"
    Intrusion = 90,     // "Intrusion" - 침입 탐지 (0x5A)
    ContactOn = 86,     // "ContactOn" - 접점 켜기 (0x56)
    ContactOff = 102,   // "ContactOff" - 접점 끄기 (0x66)
    Connection = 104,   // "Connection" - 연결 보고 (0x68)
    Action = 192,       // "Action" - 조치 보고 (0xC0)
    Fault = 115,        // "Fault" - 장애 보고 (0x73)
    WindyMode = 118     // "WindyMode" - 풍량 모드 (0x76)
    // 제거됨: Lowlight, DetectionMode, TrackingMode
}
```

#### EnumTrueFalse
```csharp
//C# 데이터 (참고용)
public enum EnumTrueFalse
{
    False,          // "False" - 거짓
    True            // "True" - 참
}
```

#### EnumDetectionType
```csharp
//C# 데이터 (참고용) - 2025-11-28 업데이트
public enum EnumDetectionType : int
{
    NONE = 0,                   // "NONE"
    CABLE_CUTTING = 1,          // "CABLE_CUTTING" - 케이블 절단
    CABLE_CONNECTED = 2,        // "CABLE_CONNECTED" - 케이블 연결
    PIR_SENSOR = 3,             // "PIR_SENSOR" - PIR 센서
    THERMAL_SENSOR = 5,         // "THERMAL_SENSOR" - 열화상 센서
    VIBRATION_SENSOR = 6,       // "VIBRATION_SENSOR" - 진동 센서
    CONTACT_SENSOR = 10,        // "CONTACT_SENSOR" - 접점 센서
    DISTANCE_SENSOR = 11,       // "DISTANCE_SENSOR" - 거리 센서
    AI_DETECT = 12              // "AI_DETECT" - AI 탐지 (신규)
}
```

#### EnumFaultType
```csharp
//C# 데이터 (참고용)
public enum EnumFaultType : int
{
    FAULT_CONTROLLER = 1,       // "FAULT_CONTROLLER" - 제어기 장애
    FAULT_FENCE = 2,            // "FAULT_FENCE" - 펜스 장애
    FAULT_MULTI = 3,            // "FAULT_MULTI" - 복합 장애
    FAULT_CABLE_CUTTING = 4,    // "FAULT_CABLE_CUTTING" - 케이블 절단
    FAULT_ETC = 5               // "FAULT_ETC" - 기타 장애
}
```

### 4.3 Integration Enum (CameraEventMapping 전용)

#### EnumEventCategory (구 EnumCategoryEvent)
```csharp
//C# 데이터 (참고용) - 2025-11-28 업데이트
public enum EnumEventCategory
{
    NONE,                           // "NONE" - 미정의
    FENCE_SENSOR_ONLY,              // "FENCE_SENSOR_ONLY" - 펜스센서 단독
    FENCE_SENSOR_WITH_MULTI_SENSOR, // "FENCE_SENSOR_WITH_MULTI_SENSOR" - 펜스센서와 멀티센서 And 조건
    MULTI_SENSOR_ONLY,              // "MULTI_SENSOR_ONLY" - 멀티센서 단독
    SENSOR_WITH_CAMERA,             // "SENSOR_WITH_CAMERA" - 센서와 카메라 적용
    SENSOR_WITH_AI_CAMERA,          // "SENSOR_WITH_AI_CAMERA" - 센서와 AI 카메라 판단 적용
    AI_CAMERA_ONLY,                 // "AI_CAMERA_ONLY" - AI 카메라 판단 단독
    CAMERA_ONLY                     // "CAMERA_ONLY" - 카메라 단독
}
```

**하위 호환성 매핑** (기존 값 → 신규 값):
| 기존 값 | 신규 값 | 비고 |
|--------|--------|------|
| `SENSOR_ONLY` | `FENCE_SENSOR_ONLY` | 자동 매핑 |
| `SENSOR_WITH_AI_DETECT` | `SENSOR_WITH_AI_CAMERA` | 자동 매핑 |
| `AI_DETECT_ONLY` | `AI_CAMERA_ONLY` | 자동 매핑 |
| `MOTION_DETECT` | - | 제거됨 |
| `ETC` | - | 제거됨 |

**참고**:
- `category_event` 필드: `EnumEventCategory` Enum 사용 (위 값 중 하나)
- `group_event` 필드: 자유 문자열 (Enum 제약 없음, 예: "Intrusion", "Fault", "Action", "Connection" 등)
- 기존 `EnumCategoryEvent`는 `EnumEventCategory`의 별칭으로 유지되어 하위 호환성 보장

---

## 5. Device API 설계

### 5.1 Controller API

#### 5.1.1 Controller 목록 조회

**Endpoint**: `GET /api/devices/controllers`

**Query Parameters**:
- `group_device` (int, optional): 디바이스 그룹 필터
- `status` (string, optional): 상태 필터 ("ACTIVATED", "ERROR", "DEACTIVATED")
- `include_sensors` (boolean, optional): 센서 목록 포함 여부 (기본값: false)
- `page` (int, optional): 페이지 번호 (기본값: 1)
- `limit` (int, optional): 페이지당 항목 수 (기본값: 20, 최대 100개)

**Request Example**:
```http
GET /api/devices/controllers?group_device=1&status=ACTIVATED&include_sensors=true HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "2 controllers retrieved",
  "data": [
    {
      "id": 1,
      "number_device": 1,
      "group_device": 1,
      "name_device": "Controller-A",
      "type_device": "Controller", //(EnumDeviceType)
      "version": "v2.1.0",
      "status": "ACTIVATED", //(EnumDeviceStatus)
      "ip_address": "192.168.1.100",
      "ip_port": 8001,
      "created_at": "2025-01-01T00:00:00.000Z",
      "updated_at": "2025-01-10T10:30:00.000Z"
    },
    {
      "id": 2,
      "number_device": 2,
      "group_device": 1,
      "name_device": "Controller-B",
      "type_device": "Controller", //(EnumDeviceType)
      "version": "v2.1.0",
      "status": "ACTIVATED", //(EnumDeviceStatus)
      "ip_address": "192.168.1.101",
      "ip_port": 8001,
      "created_at": "2025-01-02T00:00:00.000Z",
      "updated_at": "2025-01-10T10:29:00.000Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 2,
    "total_pages": 1
  },
  "meta": {
    "timestamp": "2025-01-10T10:30:00.150Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 5.1.2 Controller 단일 조회

**Endpoint**: `GET /api/devices/controllers/{id}`

**Path Parameters**:
- `id` (int, required): Controller ID

**Query Parameters**:
- `include_sensors` (boolean, optional): 센서 목록 포함 여부 (기본값: false)

**Request Example**:
```http
GET /api/devices/controllers/1?include_sensors=true HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Controller retrieved successfully",
  "data": {
    "id": 1,
    "number_device": 1,
    "group_device": 1,
    "name_device": "Controller-A",
    "type_device": "Controller", //(EnumDeviceType)
    "version": "v2.1.0",
    "status": "ACTIVATED", //(EnumDeviceStatus)
    "ip_address": "192.168.1.100",
    "ip_port": 8001,
    "devices": [
      {
        "id": 101,
        "number_device": 1,
        "group_device": 1,
        "name_device": "Sensor-A-1",
        "type_device": "Multi", //(EnumDeviceType)
        "version": "v1.5.0",
        "status": "ACTIVATED" //(EnumDeviceStatus)
      },
      {
        "id": 102,
        "number_device": 2,
        "group_device": 1,
        "name_device": "Sensor-A-2",
        "type_device": "Fence", //(EnumDeviceType)
        "version": "v1.5.0",
        "status": "ACTIVATED" //(EnumDeviceStatus)
      }
    ],
    "created_at": "2025-01-01T00:00:00.000Z",
    "updated_at": "2025-01-10T10:30:00.000Z"
  },
  "meta": {
    "timestamp": "2025-01-10T10:31:00.050Z",
    "request_id": "550e8401-e29b-41d4-a716-446655440000"
  }
}
```

**Error Response** (404 Not Found):
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Controller not found with Id=999",
    "details": "No controller exists with the specified ID"
  },
  "meta": {
    "timestamp": "2025-01-10T10:31:00.050Z",
    "request_id": "550e8401-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 5.1.3 Controller 생성

**Endpoint**: `POST /api/devices/controllers`

**Request Body**:
```json
{
  "number_device": 3,
  "group_device": 1,
  "name_device": "Controller-C",
  "type_device": "Controller", //(EnumDeviceType)
  "version": "v2.1.0",
  "status": "DEACTIVATED", //(EnumDeviceStatus)
  "ip_address": "192.168.1.102",
  "ip_port": 8001
}
```

**Response Example** (201 Created):
```json
{
  "success": true,
  "message": "Controller created successfully",
  "data": {
    "id": 3,
    "number_device": 3,
    "group_device": 1,
    "name_device": "Controller-C",
    "type_device": "Controller", //(EnumDeviceType)
    "version": "v2.1.0",
    "status": "DEACTIVATED", //(EnumDeviceStatus)
    "ip_address": "192.168.1.102",
    "ip_port": 8001,
    "created_at": "2025-01-10T10:34:00.100Z",
    "updated_at": "2025-01-10T10:34:00.100Z"
  },
  "meta": {
    "timestamp": "2025-01-10T10:34:00.100Z",
    "request_id": "550e8404-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 5.1.4 Controller 수정

**Endpoint**: `PATCH /api/devices/controllers/{id}`

**Request Body** (부분 업데이트):
```json
{
  "name_device": "Controller-C-Updated",
  "status": "ACTIVATED", //(EnumDeviceStatus)
  "version": "v2.2.0"
}
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Controller updated successfully",
  "data": {
    "id": 3,
    "number_device": 3,
    "group_device": 1,
    "name_device": "Controller-C-Updated",
    "type_device": "Controller", //(EnumDeviceType)
    "version": "v2.2.0",
    "status": "ACTIVATED", //(EnumDeviceStatus)
    "ip_address": "192.168.1.102",
    "ip_port": 8001,
    "created_at": "2025-01-10T10:34:00.100Z",
    "updated_at": "2025-01-10T10:35:00.150Z"
  },
  "meta": {
    "timestamp": "2025-01-10T10:35:00.150Z",
    "request_id": "550e8405-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 5.1.5 Controller 삭제

**Endpoint**: `DELETE /api/devices/controllers/{id}`

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Controller deleted successfully",
  "data": {
    "deleted": true,
    "id": 3
  },
  "meta": {
    "timestamp": "2025-01-10T10:36:00.100Z",
    "request_id": "550e8406-e29b-41d4-a716-446655440000"
  }
}
```

---

### 5.2 Sensor API

#### 5.2.1 Sensor 목록 조회

**Endpoint**: `GET /api/devices/sensors`

**Query Parameters**:
- `group_device` (int, optional): 디바이스 그룹 필터
- `type_device` (string, optional): 센서 타입 필터 (Multi, Fence, Underground, PIR 등)
- `status` (string, optional): 상태 필터
- `controller_id` (int, optional): 제어기 ID 필터
- `page` (int, optional): 페이지 번호
- `limit` (int, optional): 페이지당 항목 수

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "15 sensors retrieved",
  "data": [
    {
      "id": 101,
      "number_device": 1,
      "group_device": 1,
      "name_device": "Sensor-A-1",
      "type_device": "Multi", //(EnumDeviceType)
      "version": "v1.5.0",
      "status": "ACTIVATED", //(EnumDeviceStatus)
      "controller_id": 1,
      "created_at": "2025-01-01T00:00:00.000Z",
      "updated_at": "2025-01-10T10:30:00.000Z"
    },
    {
      "id": 102,
      "number_device": 2,
      "group_device": 1,
      "name_device": "Sensor-A-2",
      "type_device": "Fence", //(EnumDeviceType)
      "version": "v1.5.0",
      "status": "ACTIVATED", //(EnumDeviceStatus)
      "controller_id": 1,
      "created_at": "2025-01-01T00:00:00.000Z",
      "updated_at": "2025-01-10T10:30:00.000Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 15,
    "total_pages": 1
  },
  "meta": {
    "timestamp": "2025-01-10T10:37:00.100Z",
    "request_id": "550e8407-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 5.2.2 Sensor 단일 조회

**Endpoint**: `GET /api/devices/sensors/{id}`

**Path Parameters**:
- `id` (int, required): Sensor ID

**Request Example**:
```http
GET /api/devices/sensors/101 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Sensor retrieved successfully",
  "data": {
    "id": 101,
    "number_device": 1,
    "group_device": 1,
    "name_device": "Sensor-A-1",
    "type_device": "Multi", //(EnumDeviceType)
    "version": "v1.5.0",
    "status": "ACTIVATED", //(EnumDeviceStatus)
    "controller_id": 1,
    "created_at": "2025-01-01T00:00:00.000Z",
    "updated_at": "2025-01-10T10:30:00.000Z"
  },
  "meta": {
    "timestamp": "2025-01-10T10:38:00.050Z",
    "request_id": "550e8408-e29b-41d4-a716-446655440000"
  }
}
```

**Error Response** (404 Not Found):
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Sensor not found with Id=999",
    "details": "No sensor exists with the specified ID"
  },
  "meta": {
    "timestamp": "2025-01-10T10:38:00.050Z",
    "request_id": "550e8408-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 5.2.3 Sensor 생성

**Endpoint**: `POST /api/devices/sensors`

**Request Body**:
```json
{
  "number_device": 3,
  "group_device": 1,
  "name_device": "Fence-001",
  "type_device": "Fence", //(EnumDeviceType)
  "version": "v2.1.0",
  "status": "DEACTIVATED", //(EnumDeviceStatus)
  "controller_id": 1
}
```

**Response Example** (201 Created):
```json
{
  "success": true,
  "message": "Sensor created successfully",
  "data": {
    "id": 103,
    "number_device": 3,
    "group_device": 1,
    "name_device": "Fence-001",
    "type_device": "Fence", //(EnumDeviceType)
    "version": "v2.1.0",
    "status": "DEACTIVATED", //(EnumDeviceStatus)
    "controller_id": 1,
    "created_at": "2025-01-10T10:39:00.100Z",
    "updated_at": "2025-01-10T10:39:00.100Z"
  },
  "meta": {
    "timestamp": "2025-01-10T10:39:00.100Z",
    "request_id": "550e8409-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 5.2.4 Sensor 수정 (부분)

**Endpoint**: `PATCH /api/devices/sensors/{id}`

**Request Body** (부분 업데이트):
```json
{
  "name_device": "Fence-001-Updated",
  "status": "ACTIVATED", //(EnumDeviceStatus)
  "version": "v2.2.0"
}
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Sensor updated successfully",
  "data": {
    "id": 103,
    "number_device": 3,
    "group_device": 1,
    "name_device": "Fence-001-Updated",
    "type_device": "Fence", //(EnumDeviceType)
    "version": "v2.2.0",
    "status": "ACTIVATED", //(EnumDeviceStatus)
    "controller_id": 1,
    "created_at": "2025-01-10T10:39:00.100Z",
    "updated_at": "2025-01-10T10:40:00.150Z"
  },
  "meta": {
    "timestamp": "2025-01-10T10:40:00.150Z",
    "request_id": "550e8410-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 5.2.5 Sensor 수정 (전체)

**Endpoint**: `PUT /api/devices/sensors/{id}`

**Request Body** (전체 업데이트):
```json
{
  "number_device": 3,
  "group_device": 1,
  "name_device": "Fence-001-Complete-Update",
  "type_device": "Fence", //(EnumDeviceType)
  "version": "v2.3.0",
  "status": "ACTIVATED", //(EnumDeviceStatus)
  "controller_id": 1
}
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Sensor updated successfully",
  "data": {
    "id": 103,
    "number_device": 3,
    "group_device": 1,
    "name_device": "Fence-001-Complete-Update",
    "type_device": "Fence", //(EnumDeviceType)
    "version": "v2.3.0",
    "status": "ACTIVATED", //(EnumDeviceStatus)
    "controller_id": 1,
    "created_at": "2025-01-10T10:39:00.100Z",
    "updated_at": "2025-01-10T10:41:00.200Z"
  },
  "meta": {
    "timestamp": "2025-01-10T10:41:00.200Z",
    "request_id": "550e8411-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 5.2.6 Sensor 삭제

**Endpoint**: `DELETE /api/devices/sensors/{id}`

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Sensor deleted successfully",
  "data": {
    "deleted": true,
    "id": 103
  },
  "meta": {
    "timestamp": "2025-01-10T10:42:00.100Z",
    "request_id": "550e8412-e29b-41d4-a716-446655440000"
  }
}
```

---

### 5.3 Camera API

#### 5.3.1 Camera 목록 조회

**Endpoint**: `GET /api/devices/cameras`

**Query Parameters**:
- `group_device` (int, optional): 디바이스 그룹 필터
- `mode` (string, optional): 카메라 모드 필터 (ONVIF, EMSTONE_API, INNODEP_API, ETC)
- `category` (string, optional): 카메라 타입 필터 (FIXED, PTZ, FISHEYES, THERMAL)
- `status` (string, optional): 상태 필터
- `page` (int, optional): 페이지 번호
- `limit` (int, optional): 페이지당 항목 수

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "3 cameras retrieved",
  "data": [
    {
      "id": 201,
      "number_device": 109,
      "group_device": 1,
      "name_device": "Camera-109",
      "type_device": "IpCamera", //(EnumDeviceType)
      "version": "v3.2.1",
      "status": "ACTIVATED", //(EnumDeviceStatus)
      "ip_address": "192.168.1.109",
      "ip_port": 80,
      "user_name": "admin",
      "user_password": "********",
      "rtsp_uri": "rtsp://192.168.1.109:554/stream1",
      "rtsp_port": 554,
      "mode": "ONVIF", //(EnumCameraMode)
      "category": "PTZ", //(EnumCameraType)
      "created_at": "2025-01-03T00:00:00.000Z",
      "updated_at": "2025-01-10T10:33:00.000Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 3,
    "total_pages": 1
  },
  "meta": {
    "timestamp": "2025-01-10T10:33:00.080Z",
    "request_id": "550e8403-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 5.3.2 Camera 단일 조회

**Endpoint**: `GET /api/devices/cameras/{id}`

**Path Parameters**:
- `id` (int, required): Camera ID

**Request Example**:
```http
GET /api/devices/cameras/201 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Camera retrieved successfully",
  "data": {
    "id": 201,
    "number_device": 109,
    "group_device": 1,
    "name_device": "Camera-109",
    "type_device": "IpCamera", //(EnumDeviceType)
    "version": "v3.2.1",
    "status": "ACTIVATED", //(EnumDeviceStatus)
    "ip_address": "192.168.1.109",
    "ip_port": 80,
    "user_name": "admin",
    "user_password": "password123",
    "rtsp_uri": "rtsp://192.168.1.109:554/stream1",
    "rtsp_port": 554,
    "mode": "ONVIF", //(EnumCameraMode)
    "category": "PTZ", //(EnumCameraType)
    "created_at": "2025-01-03T00:00:00.000Z",
    "updated_at": "2025-01-10T10:33:00.000Z"
  },
  "meta": {
    "timestamp": "2025-01-10T10:44:00.050Z",
    "request_id": "550e8413-e29b-41d4-a716-446655440000"
  }
}
```

**Error Response** (404 Not Found):
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Camera not found with Id=999",
    "details": "No camera exists with the specified ID"
  },
  "meta": {
    "timestamp": "2025-01-10T10:44:00.050Z",
    "request_id": "550e8413-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 5.3.3 Camera 생성

**Endpoint**: `POST /api/devices/cameras`

**Request Body**:
```json
{
  "number_device": 110,
  "group_device": 1,
  "name_device": "Camera-110",
  "type_device": "IpCamera", //(EnumDeviceType)
  "version": "v3.2.1",
  "status": "DEACTIVATED", //(EnumDeviceStatus)
  "ip_address": "192.168.1.110",
  "ip_port": 80,
  "user_name": "admin",
  "user_password": "password123",
  "rtsp_uri": "rtsp://192.168.1.110:554/stream1",
  "rtsp_port": 554,
  "mode": "ONVIF", //(EnumCameraMode)
  "category": "FIXED" //(EnumCameraType)
}
```

**Response Example** (201 Created):
```json
{
  "success": true,
  "message": "Camera created successfully",
  "data": {
    "id": 202,
    "number_device": 110,
    "group_device": 1,
    "name_device": "Camera-110",
    "type_device": "IpCamera", //(EnumDeviceType)
    "version": "v3.2.1",
    "status": "DEACTIVATED", //(EnumDeviceStatus)
    "ip_address": "192.168.1.110",
    "ip_port": 80,
    "user_name": "admin",
    "user_password": "password123",
    "rtsp_uri": "rtsp://192.168.1.110:554/stream1",
    "rtsp_port": 554,
    "mode": "ONVIF", //(EnumCameraMode)
    "category": "FIXED", //(EnumCameraType)
    "created_at": "2025-01-10T10:45:00.100Z",
    "updated_at": "2025-01-10T10:45:00.100Z"
  },
  "meta": {
    "timestamp": "2025-01-10T10:45:00.100Z",
    "request_id": "550e8414-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 5.3.4 Camera 수정 (부분)

**Endpoint**: `PATCH /api/devices/cameras/{id}`

**Request Body** (부분 업데이트):
```json
{
  "name_device": "Camera-110-Updated",
  "status": "ACTIVATED", //(EnumDeviceStatus)
  "user_password": "newpassword456"
}
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Camera updated successfully",
  "data": {
    "id": 202,
    "number_device": 110,
    "group_device": 1,
    "name_device": "Camera-110-Updated",
    "type_device": "IpCamera", //(EnumDeviceType)
    "version": "v3.2.1",
    "status": "ACTIVATED", //(EnumDeviceStatus)
    "ip_address": "192.168.1.110",
    "ip_port": 80,
    "user_name": "admin",
    "user_password": "newpassword456",
    "rtsp_uri": "rtsp://192.168.1.110:554/stream1",
    "rtsp_port": 554,
    "mode": "ONVIF", //(EnumCameraMode)
    "category": "FIXED", //(EnumCameraType)
    "created_at": "2025-01-10T10:45:00.100Z",
    "updated_at": "2025-01-10T10:46:00.150Z"
  },
  "meta": {
    "timestamp": "2025-01-10T10:46:00.150Z",
    "request_id": "550e8415-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 5.3.5 Camera 수정 (전체)

**Endpoint**: `PUT /api/devices/cameras/{id}`

**Request Body** (전체 업데이트):
```json
{
  "number_device": 110,
  "group_device": 1,
  "name_device": "Camera-110-Complete-Update",
  "type_device": "IpCamera", //(EnumDeviceType)
  "version": "v3.3.0",
  "status": "ACTIVATED", //(EnumDeviceStatus)
  "ip_address": "192.168.1.110",
  "ip_port": 80,
  "user_name": "admin",
  "user_password": "completepassword789",
  "rtsp_uri": "rtsp://192.168.1.110:554/stream2",
  "rtsp_port": 554,
  "mode": "ONVIF", //(EnumCameraMode)
  "category": "PTZ" //(EnumCameraType)
}
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Camera updated successfully",
  "data": {
    "id": 202,
    "number_device": 110,
    "group_device": 1,
    "name_device": "Camera-110-Complete-Update",
    "type_device": "IpCamera", //(EnumDeviceType)
    "version": "v3.3.0",
    "status": "ACTIVATED", //(EnumDeviceStatus)
    "ip_address": "192.168.1.110",
    "ip_port": 80,
    "user_name": "admin",
    "user_password": "completepassword789",
    "rtsp_uri": "rtsp://192.168.1.110:554/stream2",
    "rtsp_port": 554,
    "mode": "ONVIF", //(EnumCameraMode)
    "category": "PTZ", //(EnumCameraType)
    "created_at": "2025-01-10T10:45:00.100Z",
    "updated_at": "2025-01-10T10:47:00.200Z"
  },
  "meta": {
    "timestamp": "2025-01-10T10:47:00.200Z",
    "request_id": "550e8416-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 5.3.6 Camera 삭제

**Endpoint**: `DELETE /api/devices/cameras/{id}`

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Camera deleted successfully",
  "data": {
    "deleted": true,
    "id": 202
  },
  "meta": {
    "timestamp": "2025-01-10T10:48:00.100Z",
    "request_id": "550e8417-e29b-41d4-a716-446655440000"
  }
}
```

---

## 6. Event API 설계

### 6.1 Detection Event API

#### 6.1.1 Detection Event 목록 조회

**Endpoint**: `GET /api/events/detections`

**Query Parameters**:
- `start_date` (datetime, required): 조회 시작 시간 (ISO 8601)
- `end_date` (datetime, required): 조회 종료 시간 (ISO 8601)
- `group_device` (int, optional): 디바이스 그룹 필터
- `type_event` (string, optional): 이벤트 타입 필터 (Intrusion)
- `status` (string, optional): 상태 필터 (True, False)
- `result` (string, optional): 탐지 결과 필터 (PIR_SENSOR, THERMAL_SENSOR 등)
- `page` (int, optional): 페이지 번호
- `limit` (int, optional): 페이지당 항목 수

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "25 detection events retrieved",
  "data": [
    {
      "id": 1001,
      "group_event": "group_001",
      "type_event": "Intrusion",
      "controller": 1,
      "sensor": 1,
      "type_device": "Multi",
      "sequence": 10,
      "action_reported": "True",
      "result": "PIR_SENSOR",
      "created_at": "2025-01-10T10:15:23.100Z",
      "updated_at": "2025-01-10T10:15:23.100Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 25,
    "total_pages": 2
  },
  "meta": {
    "timestamp": "2025-01-10T10:40:00.250Z",
    "request_id": "550e8500-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 6.1.2 Detection Event 단일 조회

**Endpoint**: `GET /api/events/detections/{id}`

**Path Parameters**:
- `id` (int, required): Detection Event ID

**Request Example**:
```http
GET /api/events/detections/1001 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Detection event retrieved successfully",
  "data": {
    "id": 1001,
    "group_event": "group_001",
    "type_event": "Intrusion", //(EnumEventType)
    "controller": 1,
    "sensor": 1,
    "type_device": "Multi", //(EnumDeviceType)
    "sequence": 10,
    "action_reported": "True", //(EnumTrueFalse)
    "result": "PIR_SENSOR", //(EnumDetectionType)
    "created_at": "2025-01-10T10:15:23.100Z",
    "updated_at": "2025-01-10T10:15:23.100Z"
  },
  "meta": {
    "timestamp": "2025-01-10T10:50:00.050Z",
    "request_id": "550e8418-e29b-41d4-a716-446655440000"
  }
}
```

**Error Response** (404 Not Found):
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Detection event not found with Id=999",
    "details": "No detection event exists with the specified ID"
  },
  "meta": {
    "timestamp": "2025-01-10T10:50:00.050Z",
    "request_id": "550e8418-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 6.1.3 Detection Event 생성

**Endpoint**: `POST /api/events/detections`

**Request Body**:
```json
{
  "group_event": "group_002",
  "type_event": "Intrusion", //(EnumEventType)
  "controller": 1,
  "sensor": 2,
  "type_device": "Fence", //(EnumDeviceType)
  "sequence": 15,
  "action_reported": "False", //(EnumTrueFalse)
  "result": "THERMAL_SENSOR" //(EnumDetectionType)
}
```

**Response Example** (201 Created):
```json
{
  "success": true,
  "message": "Detection event created successfully",
  "data": {
    "id": 1002,
    "group_event": "group_002",
    "type_event": "Intrusion", //(EnumEventType)
    "controller": 1,
    "sensor": 2,
    "type_device": "Fence", //(EnumDeviceType)
    "sequence": 15,
    "action_reported": "True", //(EnumTrueFalse)
    "result": "THERMAL_SENSOR", //(EnumDetectionType)
    "created_at": "2025-01-10T10:51:00.100Z",
    "updated_at": "2025-01-10T10:51:00.100Z"
  },
  "meta": {
    "timestamp": "2025-01-10T10:51:00.100Z",
    "request_id": "550e8419-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 6.1.4 Detection Event 수정 (부분)

**Endpoint**: `PATCH /api/events/detections/{id}`

**Request Body** (부분 업데이트):
```json
{
  "status": "False", //(EnumTrueFalse)
  "result": "VIBRATION_SENSOR" //(EnumDetectionType)
}
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Detection event updated successfully",
  "data": {
    "id": 1002,
    "group_event": "group_002",
    "type_event": "Intrusion", //(EnumEventType)
    "controller": 1,
    "sensor": 2,
    "type_device": "Fence", //(EnumDeviceType)
    "sequence": 15,
    "action_reported": "False", //(EnumTrueFalse)
    "result": "VIBRATION_SENSOR", //(EnumDetectionType)
    "created_at": "2025-01-10T10:51:00.100Z",
    "updated_at": "2025-01-10T10:52:00.150Z"
  },
  "meta": {
    "timestamp": "2025-01-10T10:52:00.150Z",
    "request_id": "550e8420-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 6.1.5 Detection Event 수정 (전체)

**Endpoint**: `PUT /api/events/detections/{id}`

**Request Body** (전체 업데이트):
```json
{
  "group_event": "group_002_updated",
  "type_event": "Intrusion", //(EnumEventType)
  "controller": 1,
  "sensor": 2,
  "type_device": "Fence", //(EnumDeviceType)
  "sequence": 20,
  "action_reported": "True", //(EnumTrueFalse)
  "result": "DISTANCE_SENSOR", //(EnumDetectionType)
}
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Detection event updated successfully",
  "data": {
    "id": 1002,
    "group_event": "group_002_updated",
    "type_event": "Intrusion", //(EnumEventType)
    "controller": 1,
    "sensor": 2,
    "type_device": "Fence", //(EnumDeviceType)
    "sequence": 20,
    "action_reported": "True", //(EnumTrueFalse)
    "result": "DISTANCE_SENSOR", //(EnumDetectionType)
    "created_at": "2025-01-10T10:51:00.100Z",
    "updated_at": "2025-01-10T10:53:00.200Z"
  },
  "meta": {
    "timestamp": "2025-01-10T10:53:00.200Z",
    "request_id": "550e8421-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 6.1.6 Detection Event 삭제

**Endpoint**: `DELETE /api/events/detections/{id}`

**삭제 제약**:
- `action_reported="True"`인 DetectionEvent는 삭제할 수 없습니다
- 조치 보고가 등록된 경우, ActionEvent를 먼저 삭제해야 합니다
- ActionEvent 삭제 시 `action_reported`가 자동으로 "False"로 복원됩니다

**성공 응답 예시** (200 OK):
```json
{
  "success": true,
  "message": "Detection event deleted successfully",
  "data": null,
  "meta": {
    "timestamp": "2025-01-14T10:54:00.100Z",
    "request_id": "550e8422-e29b-41d4-a716-446655440000"
  }
}
```

**에러 응답 예시** (404 Not Found):
```json
{
  "success": false,
  "message": "Detection event not found with Id=999",
  "data": null,
  "meta": {
    "timestamp": "2025-01-14T10:54:00.100Z",
    "request_id": "550e8422-e29b-41d4-a716-446655440000"
  }
}
```

**에러 응답 예시** (409 Conflict):
```json
{
  "success": false,
  "message": "조치보고가 등록된 탐지 이벤트는 삭제할 수 없습니다. ActionEvent를 먼저 삭제해주세요. / Cannot delete Detection event with Action reported. Please delete the ActionEvent first.",
  "data": null,
  "meta": {
    "timestamp": "2025-01-14T10:54:00.100Z",
    "request_id": "550e8422-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 6.1.7 Detection Event의 Action Event 조회

**Endpoint**: `GET /api/events/detections/{event_id}/action`

**Phase**: 20.1

**설명**:
특정 Detection Event에 연결된 Action Event를 조회합니다.
- 1:1 관계를 활용한 효율적인 조회
- Action Event가 없는 경우 (action_reported="False") 404 반환
- Response에 nested source event (DetectionEvent) 포함

**Path Parameters**:
- `event_id` (int, required): Detection Event ID

**Request Example**:
```http
GET /api/events/detections/1001/action HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Action event retrieved successfully",
  "data": {
    "id": 4001,
    "type_event": "Action",
    "content": "침입 탐지 확인 및 순찰 출동 요청",
    "user": "operator_test",
    "from_event": {
      "id": 1001,
      "group_event": "group_001",
      "type_event": "Intrusion",
      "controller": 1,
      "sensor": 1,
      "type_device": "PIR",
      "sequence": 10,
      "action_reported": "True",
      "result": "PIR_SENSOR",
      "created_at": "2025-01-14T10:15:23.100Z",
      "updated_at": "2025-01-14T10:15:23.100Z"
    },
    "created_at": "2025-01-14T10:20:00.000Z",
    "updated_at": "2025-01-14T10:20:00.000Z"
  },
  "meta": {
    "timestamp": "2025-01-14T12:00:00.250Z",
    "request_id": "550e8500-e29b-41d4-a716-446655440000"
  }
}
```

**Error Response** (404 Not Found - Detection Event 없음):
```json
{
  "success": false,
  "message": "Detection event not found with Id=999",
  "data": null,
  "meta": {
    "timestamp": "2025-01-14T12:00:00.250Z",
    "request_id": "550e8500-e29b-41d4-a716-446655440000"
  }
}
```

**Error Response** (404 Not Found - Action Event 없음):
```json
{
  "success": false,
  "message": "조치 보고가 등록되지 않은 탐지 이벤트입니다. / No action event found for this detection event.",
  "data": null,
  "meta": {
    "timestamp": "2025-01-14T12:00:00.250Z",
    "request_id": "550e8500-e29b-41d4-a716-446655440000"
  }
}
```

---

### 6.2 Malfunction Event API

#### 6.2.1 Malfunction Event 목록 조회

**Endpoint**: `GET /api/events/malfunctions`

**Query Parameters**:
- `start_date` (datetime, required): 조회 시작 시간
- `end_date` (datetime, required): 조회 종료 시간
- `group_device` (int, optional): 디바이스 그룹 필터
- `type_device` (string, optional): 디바이스 타입 필터
- `reason` (string, optional): 장애 원인 필터 (FAULT_CONTROLLER, FAULT_FENCE, FAULT_CABLE_CUTTING 등)
- `status` (string, optional): 상태 필터

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "5 malfunction events retrieved",
  "data": [
    {
      "id": 2001,
      "group_event": "group_fault_001",
      "type_event": "Fault", //(EnumEventType)
      "controller": 1, //단 제어기 고장일 경우 sensor는 0
      "sensor": 3,
      "type_device": "Fence", //(EnumDeviceType)
      "sequence": 10,
      "action_reported": "True", //(EnumTrueFalse)
      "reason": "FAULT_CABLE_CUTTING", //(EnumFaultType)
      "first_start": 10,
      "first_end": 15,
      "second_start": 20,
      "second_end": 25,
      "created_at": "2025-01-03T14:20:00.500Z",
      "updated_at": "2025-01-03T14:20:00.500Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 5,
    "total_pages": 1
  },
  "meta": {
    "timestamp": "2025-01-10T10:42:00.300Z",
    "request_id": "550e8502-e29b-41d4-a716-446655440000"
  }
}
```

**Malfunction Event 필드 설명**:
- `reason` (string): 장애 원인 (EnumFaultType)
- `first_start` (int): 첫 번째 케이블 시작점
- `first_end` (int): 첫 번째 케이블 끝점
- `second_start` (int): 두 번째 케이블 시작점
- `second_end` (int): 두 번째 케이블 끝점

---

#### 6.2.2 Malfunction Event 단일 조회

**Endpoint**: `GET /api/events/malfunctions/{id}`

**Path Parameters**:
- `id` (int, required): Malfunction Event ID

**Request Example**:
```http
GET /api/events/malfunctions/2001 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Malfunction event retrieved successfully",
  "data": {
    "id": 2001,
    "group_event": "group_fault_001",
    "type_event": "Fault", //(EnumEventType)
    "controller": 1, //단 제어기 고장일 경우 sensor는 0
    "sensor": 3,
    "type_device": "Fence", //(EnumDeviceType)
    "sequence": 10,
    "action_reported": "True", //(EnumTrueFalse)
    "reason": "FAULT_CABLE_CUTTING", //(EnumFaultType)
    "first_start": 5,
    "first_end": 5,
    "second_start": 0,
    "second_end": 0,
    "created_at": "2025-01-03T14:20:00.500Z",
    "updated_at": "2025-01-03T14:20:00.500Z"
  },
  "meta": {
    "timestamp": "2025-01-10T10:55:00.050Z",
    "request_id": "550e8423-e29b-41d4-a716-446655440000"
  }
}
```

**Error Response** (404 Not Found):
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Malfunction event not found with Id=999",
    "details": "No malfunction event exists with the specified ID"
  },
  "meta": {
    "timestamp": "2025-01-10T10:55:00.050Z",
    "request_id": "550e8423-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 6.2.3 Malfunction Event 생성

**Endpoint**: `POST /api/events/malfunctions`

**Request Body**:
```json
{
  "group_event": "group_fault_002",
  "type_event": "Fault", //(EnumEventType)
  "controller": 1,
  "sensor": 4,
  "type_device": "Multi", //(EnumDeviceType)
  "sequence": 12,
  "action_reported": "True", //(EnumTrueFalse)
  "reason": "FAULT_FENCE", //(EnumFaultType)
  "first_start": 3,
  "first_end": 3,
  "second_start": 0,
  "second_end": 0,
}
```

**Response Example** (201 Created):
```json
{
  "success": true,
  "message": "Malfunction event created successfully",
  "data": {
    "id": 2002,
    "group_event": "group_fault_002",
    "type_event": "Fault", //(EnumEventType)
    "controller": 1,
    "sensor": 4,
    "type_device": "Multi", //(EnumDeviceType)
    "sequence": 12,
    "action_reported": "True", //(EnumTrueFalse)
    "reason": "FAULT_FENCE", //(EnumFaultType)
    "first_start": 3,
    "first_end": 3,
    "second_start": 0,
    "second_end": 0,
    "created_at": "2025-01-10T10:56:00.100Z",
    "updated_at": "2025-01-10T10:56:00.100Z"
  },
  "meta": {
    "timestamp": "2025-01-10T10:56:00.100Z",
    "request_id": "550e8424-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 6.2.4 Malfunction Event 수정 (부분)

**Endpoint**: `PATCH /api/events/malfunctions/{id}`

**Request Body** (부분 업데이트):
```json
{
  "action_reported": "False", //(EnumTrueFalse)
  "reason": "FAULT_MULTI" //(EnumFaultType)
}
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Malfunction event updated successfully",
  "data": {
    "id": 2002,
    "group_event": "group_fault_002",
    "type_event": "Fault", //(EnumEventType)
    "controller": 1,
    "sensor": 4,
    "type_device": "Multi", //(EnumDeviceType)
    "sequence": 12,
    "action_reported": "False", //(EnumTrueFalse)
    "reason": "FAULT_MULTI", //(EnumFaultType)
    "first_start": 3,
    "first_end": 3,
    "second_start": 0,
    "second_end": 0,
    "created_at": "2025-01-10T10:56:00.100Z",
    "updated_at": "2025-01-10T10:57:00.150Z"
  },
  "meta": {
    "timestamp": "2025-01-10T10:57:00.150Z",
    "request_id": "550e8425-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 6.2.5 Malfunction Event 수정 (전체)

**Endpoint**: `PUT /api/events/malfunctions/{id}`

**Request Body** (전체 업데이트):
```json
{
  "group_event": "group_fault_002_updated",
  "type_event": "Fault", //(EnumEventType)
  "controller": 1,
  "sensor": 4,
  "type_device": "Multi", //(EnumDeviceType)
  "sequence": 15,
  "action_reported": "True", //(EnumTrueFalse)
  "reason": "FAULT_ETC", //(EnumFaultType)
  "first_start": 2,
  "first_end": 2,
  "second_start": 5,
  "second_end": 5,
}
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Malfunction event updated successfully",
  "data": {
    "id": 2002,
    "group_event": "group_fault_002_updated",
    "type_event": "Fault", //(EnumEventType)
    "controller": 1,
    "sensor": 4,
    "type_device": "Multi", //(EnumDeviceType)
    "sequence": 15,
    "action_reported": "True", //(EnumTrueFalse)
    "reason": "FAULT_ETC", //(EnumFaultType)
    "first_start": 2,
    "first_end": 2,
    "second_start": 5,
    "second_end": 5,
    "created_at": "2025-01-10T10:56:00.100Z",
    "updated_at": "2025-01-10T10:58:00.200Z"
  },
  "meta": {
    "timestamp": "2025-01-10T10:58:00.200Z",
    "request_id": "550e8426-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 6.2.6 Malfunction Event 삭제

**Endpoint**: `DELETE /api/events/malfunctions/{id}`

**삭제 제약**:
- `action_reported="True"`인 MalfunctionEvent는 삭제할 수 없습니다
- 조치 보고가 등록된 경우, ActionEvent를 먼저 삭제해야 합니다
- ActionEvent 삭제 시 `action_reported`가 자동으로 "False"로 복원됩니다

**성공 응답 예시** (200 OK):
```json
{
  "success": true,
  "message": "Malfunction event deleted successfully",
  "data": null,
  "meta": {
    "timestamp": "2025-01-14T10:59:00.100Z",
    "request_id": "550e8427-e29b-41d4-a716-446655440000"
  }
}
```

**에러 응답 예시** (404 Not Found):
```json
{
  "success": false,
  "message": "Malfunction event not found with Id=999",
  "data": null,
  "meta": {
    "timestamp": "2025-01-14T10:59:00.100Z",
    "request_id": "550e8427-e29b-41d4-a716-446655440000"
  }
}
```

**에러 응답 예시** (409 Conflict):
```json
{
  "success": false,
  "message": "조치보고가 등록된 장애 이벤트는 삭제할 수 없습니다. ActionEvent를 먼저 삭제해주세요. / Cannot delete Malfunction event with Action reported. Please delete the ActionEvent first.",
  "data": null,
  "meta": {
    "timestamp": "2025-01-14T10:59:00.100Z",
    "request_id": "550e8427-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 6.2.7 Malfunction Event의 Action Event 조회

**Endpoint**: `GET /api/events/malfunctions/{event_id}/action`

**Phase**: 20.2

**설명**:
특정 Malfunction Event에 연결된 Action Event를 조회합니다.
- 1:1 관계를 활용한 효율적인 조회
- Action Event가 없는 경우 (action_reported="False") 404 반환
- Response에 nested source event (MalfunctionEvent) 포함

**Path Parameters**:
- `event_id` (int, required): Malfunction Event ID

**Request Example**:
```http
GET /api/events/malfunctions/2001/action HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Action event retrieved successfully",
  "data": {
    "id": 4002,
    "type_event": "Action",
    "content": "장애 확인 및 유지보수팀 연락",
    "user": "operator_malfunction",
    "from_event": {
      "id": 2001,
      "group_event": "group_002",
      "type_event": "Fault",
      "controller": 2,
      "sensor": 0,
      "type_device": "Controller",
      "sequence": 5,
      "action_reported": "True",
      "reason": "FAULT_CONTROLLER",
      "first_start": 100,
      "first_end": 200,
      "second_start": 300,
      "second_end": 400,
      "created_at": "2025-01-14T11:00:00.000Z",
      "updated_at": "2025-01-14T11:00:00.000Z"
    },
    "created_at": "2025-01-14T11:05:00.000Z",
    "updated_at": "2025-01-14T11:05:00.000Z"
  },
  "meta": {
    "timestamp": "2025-01-14T13:00:00.250Z",
    "request_id": "550e8501-e29b-41d4-a716-446655440000"
  }
}
```

**Error Response** (404 Not Found - Malfunction Event 없음):
```json
{
  "success": false,
  "message": "Malfunction event not found with Id=999",
  "data": null,
  "meta": {
    "timestamp": "2025-01-14T13:00:00.250Z",
    "request_id": "550e8501-e29b-41d4-a716-446655440000"
  }
}
```

**Error Response** (404 Not Found - Action Event 없음):
```json
{
  "success": false,
  "message": "조치 보고가 등록되지 않은 장애 이벤트입니다. / No action event found for this malfunction event.",
  "data": null,
  "meta": {
    "timestamp": "2025-01-14T13:00:00.250Z",
    "request_id": "550e8501-e29b-41d4-a716-446655440000"
  }
}
```

---

### 6.3 Connection Event API

#### 6.3.1 Connection Event 목록 조회

**Endpoint**: `GET /api/events/connections`

**Query Parameters**:
- `start_date` (datetime, required): 조회 시작 시간 (ISO 8601)
- `end_date` (datetime, required): 조회 종료 시간 (ISO 8601)
- `group_device` (int, optional): 디바이스 그룹 필터
- `type_device` (string, optional): 디바이스 타입 필터
- `page` (int, optional): 페이지 번호
- `limit` (int, optional): 페이지당 항목 수

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "10 connection events retrieved",
  "data": [
    {
      "id": 3001,
      "group_event": "group_conn_001",
      "type_event": "Connection", //(EnumEventType)
      "controller": 1,
      "sensor": 1,
      "type_device": "Fence", //(EnumDeviceType)
      "sequence": 5,
      "created_at": "2025-01-10T09:00:00.100Z",
      "updated_at": "2025-01-10T09:00:00.100Z"
    },
    {
      "id": 3002,
      "group_event": "group_conn_002",
      "type_event": "Connection", //(EnumEventType)
      "controller": 1,
      "sensor": 2,
      "type_device": "Multi", //(EnumDeviceType)
      "sequence": 6,
      "created_at": "2025-01-10T09:05:00.100Z",
      "updated_at": "2025-01-10T09:05:00.100Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 10,
    "total_pages": 1
  },
  "meta": {
    "timestamp": "2025-01-10T11:00:00.250Z",
    "request_id": "550e8428-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 6.3.2 Connection Event 단일 조회

**Endpoint**: `GET /api/events/connections/{id}`

**Path Parameters**:
- `id` (int, required): Connection Event ID

**Request Example**:
```http
GET /api/events/connections/3001 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Connection event retrieved successfully",
  "data": {
    "id": 3001,
    "group_event": "group_conn_001",
    "type_event": "Connection", //(EnumEventType)
    "controller": 1,
    "sensor": 1,
    "type_device": "Fence", //(EnumDeviceType)
    "sequence": 5,
    "created_at": "2025-01-10T09:00:00.100Z",
    "updated_at": "2025-01-10T09:00:00.100Z"
  },
  "meta": {
    "timestamp": "2025-01-10T11:01:00.050Z",
    "request_id": "550e8429-e29b-41d4-a716-446655440000"
  }
}
```

**Error Response** (404 Not Found):
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Connection event not found with Id=999",
    "details": "No connection event exists with the specified ID"
  },
  "meta": {
    "timestamp": "2025-01-10T11:01:00.050Z",
    "request_id": "550e8429-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 6.3.3 Connection Event 생성

**Endpoint**: `POST /api/events/connections`

**Request Body**:
```json
{
  "group_event": "group_conn_003",
  "type_event": "Connection", //(EnumEventType)
  "controller": 1,
  "sensor": 3,
  "type_device": "Underground", //(EnumDeviceType)
  "sequence": 8,
}
```

**Response Example** (201 Created):
```json
{
  "success": true,
  "message": "Connection event created successfully",
  "data": {
    "id": 3003,
    "group_event": "group_conn_003",
    "type_event": "Connection", //(EnumEventType)
    "controller": 1,
    "sensor": 3,
    "type_device": "Underground", //(EnumDeviceType)
    "sequence": 8,
    "created_at": "2025-01-10T11:02:00.100Z",
    "updated_at": "2025-01-10T11:02:00.100Z"
  },
  "meta": {
    "timestamp": "2025-01-10T11:02:00.100Z",
    "request_id": "550e8430-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 6.3.4 Connection Event 수정 (부분)

**Endpoint**: `PATCH /api/events/connections/{id}`

**Request Body** (부분 업데이트):
```json
{
  "sequence": 10,
}
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Connection event updated successfully",
  "data": {
    "id": 3003,
    "group_event": "group_conn_003",
    "type_event": "Connection", //(EnumEventType)
    "controller": 1,
    "sensor": 3,
    "type_device": "Underground", //(EnumDeviceType)
    "sequence": 10,
    "created_at": "2025-01-10T11:02:00.100Z",
    "updated_at": "2025-01-10T11:03:00.150Z"
  },
  "meta": {
    "timestamp": "2025-01-10T11:03:00.150Z",
    "request_id": "550e8431-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 6.3.5 Connection Event 수정 (전체)

**Endpoint**: `PUT /api/events/connections/{id}`

**Request Body** (전체 업데이트):
```json
{
  "group_event": "group_conn_003_updated",
  "type_event": "Connection", //(EnumEventType)
  "controller": 1,
  "sensor": 3,
  "type_device": "PIR", //(EnumDeviceType)
  "sequence": 12,
}
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Connection event updated successfully",
  "data": {
    "id": 3003,
    "group_event": "group_conn_003_updated",
    "type_event": "Connection", //(EnumEventType)
    "controller": 1,
    "sensor": 3,
    "type_device": "PIR", //(EnumDeviceType)
    "sequence": 12,
    "created_at": "2025-01-10T11:02:00.100Z",
    "updated_at": "2025-01-10T11:04:00.200Z"
  },
  "meta": {
    "timestamp": "2025-01-10T11:04:00.200Z",
    "request_id": "550e8432-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 6.3.6 Connection Event 삭제

**Endpoint**: `DELETE /api/events/connections/{id}`

**삭제 제약**: 없음 (ConnectionEvent는 `action_reported` 필드가 없으므로 언제든 삭제 가능)

**성공 응답 예시** (200 OK):
```json
{
  "success": true,
  "message": "Connection event deleted successfully",
  "data": null,
  "meta": {
    "timestamp": "2025-01-14T11:05:00.100Z",
    "request_id": "550e8433-e29b-41d4-a716-446655440000"
  }
}
```

**에러 응답 예시** (404 Not Found):
```json
{
  "success": false,
  "message": "Connection event not found with Id=999",
  "data": null,
  "meta": {
    "timestamp": "2025-01-14T11:05:00.100Z",
    "request_id": "550e8433-e29b-41d4-a716-446655440000"
  }
}
```

---

### 6.4 Action Event API

#### 6.4.1 Action Event 생성

**Endpoint**: `POST /api/events/actions`

**자동 동작**:
- ActionEvent 생성 시 source event의 `action_reported` 필드가 자동으로 "True"로 업데이트됩니다
- 1:1 관계: 하나의 source event에는 최대 하나의 ActionEvent만 생성 가능합니다
- 대상 이벤트 타입:
  - `Intrusion` → DetectionEvent 업데이트
  - `Fault` → MalfunctionEvent 업데이트

**Request Body**:
```json
{
  "content": "침입 탐지 확인 및 순찰 출동 요청",
  "user": "operator_kim",
  "from_event": 1001, //이벤트 Id
  "from_type_event": "Intrusion", //이벤트 타입 ("Intrusion", "Fault")
}
```

**성공 응답 예시** (201 Created):
```json
{
  "success": true,
  "message": "Action event created successfully",
  "data": {
    "id": 3001,
    "type_event": "Intrusion",
    "content": "침입 탐지 확인 및 순찰 출동 요청",
    "user": "operator_kim",
    "from_event": {
        "id": 1001,
        "group_event": "GROUP_TEST",
        "type_event": "Intrusion",
        "controller": 1,
        "sensor": 1,
        "type_device": "PIR",
        "sequence": 1,
        "action_reported": "True",  // ← 자동으로 "True"로 업데이트됨
        "result": "PIR_SENSOR",
        "created_at": "2025-01-14T11:50:23.736735",
        "updated_at": "2025-01-14T11:50:25.123456"  // ← updated_at도 자동 갱신
      },
    "created_at": "2025-01-14T10:43:00.150Z",
    "updated_at": "2025-01-14T10:43:00.150Z"
  },
  "meta": {
    "timestamp": "2025-01-14T10:43:00.150Z",
    "request_id": "550e8503-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 6.4.2 Action Event 목록 조회

**Endpoint**: `GET /api/events/actions`

**Query Parameters**:
- `start_date` (datetime, required): 조회 시작 시간 (ISO 8601)
- `end_date` (datetime, required): 조회 종료 시간 (ISO 8601)
- `user` (string, optional): 사용자 필터
- `page` (int, optional): 페이지 번호
- `limit` (int, optional): 페이지당 항목 수

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "8 action events retrieved",
  "data": [
    {
      "id": 4001,
      "type_event": "Action",
      "content": "침입 탐지 확인 및 순찰 출동 요청",
      "user": "operator_kim",
      "from_event": {
        "id": 1002,
        "group_event": "group_002",
        "type_event": "Intrusion", //(EnumEventType)
        "controller": 1,
        "sensor": 2,
        "type_device": "Fence", //(EnumDeviceType)
        "sequence": 15,
        "action_reported": "True", //(EnumTrueFalse)
        "result": "THERMAL_SENSOR", //(EnumDetectionType)
      },
      "created_at": "2025-01-10T10:16:00.100Z",
      "updated_at": "2025-01-10T10:16:00.100Z"
    },
    {
      "id": 4002,
      "type_event": "Action",
      "content": "장애 확인 및 유지보수팀 연락",
      "user": "operator_lee",
      "from_event": {
        "id": 1001,
        "group_event": "group_fault_002_updated",
        "type_event": "Fault", //(EnumEventType)
        "controller": 1,
        "sensor": 4,
        "type_device": "Multi", //(EnumDeviceType)
        "sequence": 15,
        "action_reported": "True", //(EnumTrueFalse)
        "reason": "FAULT_ETC", //(EnumFaultType)
        "first_start": 2,
        "first_end": 2,
        "second_start": 5,
        "second_end": 5,
      },
      "created_at": "2025-01-10T10:20:00.150Z",
      "updated_at": "2025-01-10T10:20:00.150Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 8,
    "total_pages": 1
  },
  "meta": {
    "timestamp": "2025-01-10T11:06:00.250Z",
    "request_id": "550e8434-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 6.4.3 Action Event 단일 조회

**Endpoint**: `GET /api/events/actions/{id}`

**Path Parameters**:
- `id` (int, required): Action Event ID

**Request Example**:
```http
GET /api/events/actions/4001 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Action event retrieved successfully",
  "data": {
    "id": 4001,
    "type_event": "Action",
    "content": "침입 탐지 확인 및 순찰 출동 요청",
    "user": "operator_kim",
    "from_event": {
      "id": 1002,
      "group_event": "group_002",
      "type_event": "Intrusion", //(EnumEventType)
      "controller": 1,
      "sensor": 2,
      "type_device": "Fence", //(EnumDeviceType)
      "sequence": 15,
      "action_reported": "True", //(EnumTrueFalse)
      "result": "THERMAL_SENSOR", //(EnumDetectionType)
    },
    "created_at": "2025-01-10T10:16:00.100Z",
    "updated_at": "2025-01-10T10:16:00.100Z"
  },
  "meta": {
    "timestamp": "2025-01-10T11:07:00.050Z",
    "request_id": "550e8435-e29b-41d4-a716-446655440000"
  }
}
```

**Error Response** (404 Not Found):
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Action event not found with Id=999",
    "details": "No action event exists with the specified ID"
  },
  "meta": {
    "timestamp": "2025-01-10T11:07:00.050Z",
    "request_id": "550e8435-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 6.4.4 Action Event 수정 (부분)

**Endpoint**: `PATCH /api/events/actions/{id}`

**Request Body** (부분 업데이트):
```json
{
  "content": "침입 탐지 확인 완료 - 오탐지로 판명", // 이중 하나
  "user": "operator_kim", // 이중 하나
}
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Action event updated successfully",
  "data": {
    "id": 4001,
    "type_event": "Action",
    "content": "침입 탐지 확인 완료 - 오탐지로 판명",
    "user": "operator_kim",
    "from_event": {
      "id": 1002,
      "group_event": "group_002",
      "type_event": "Intrusion", //(EnumEventType)
      "controller": 1,
      "sensor": 2,
      "type_device": "Fence", //(EnumDeviceType)
      "sequence": 15,
      "action_reported": "True", //(EnumTrueFalse)
      "result": "THERMAL_SENSOR", //(EnumDetectionType)
    },
    "created_at": "2025-01-10T10:16:00.100Z",
    "updated_at": "2025-01-10T11:08:00.150Z"
  },
  "meta": {
    "timestamp": "2025-01-10T11:08:00.150Z",
    "request_id": "550e8436-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 6.4.5 Action Event 수정 (전체)

**Endpoint**: `PUT /api/events/actions/{id}`

**Request Body** (전체 업데이트):
```json
{
  "content": "침입 탐지 재확인 - 실제 침입 확인됨, 경찰 출동 요청",
  "user": "operator_park",
}
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Action event updated successfully",
  "data": {
    "id": 4001,
    "type_event": "Action",
    "content": "침입 탐지 재확인 - 실제 침입 확인됨, 경찰 출동 요청",
    "user": "operator_park",
    "from_event": {
      "id": 1002,
      "group_event": "group_002",
      "type_event": "Intrusion", //(EnumEventType)
      "controller": 1,
      "sensor": 2,
      "type_device": "Fence", //(EnumDeviceType)
      "sequence": 15,
      "action_reported": "True", //(EnumTrueFalse)
      "result": "THERMAL_SENSOR", //(EnumDetectionType)
    },
    "created_at": "2025-01-10T10:16:00.100Z",
    "updated_at": "2025-01-10T11:09:00.200Z"
  },
  "meta": {
    "timestamp": "2025-01-10T11:09:00.200Z",
    "request_id": "550e8437-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 6.4.6 Action Event 삭제

**Endpoint**: `DELETE /api/events/actions/{id}`

**자동 동작**:
- ActionEvent 삭제 시 source event의 `action_reported` 필드가 자동으로 "False"로 복원됩니다
- 복원 후에는 source event를 삭제할 수 있게 됩니다
- 대상 이벤트 타입:
  - `Intrusion` → DetectionEvent 복원
  - `Fault` → MalfunctionEvent 복원
  - `Connection` → 영향 없음 (action_reported 필드 없음)

**성공 응답 예시** (200 OK):
```json
{
  "success": true,
  "message": "Action event deleted successfully",
  "data": null,
  "meta": {
    "timestamp": "2025-01-14T11:10:00.100Z",
    "request_id": "550e8438-e29b-41d4-a716-446655440000"
  }
}
```

**에러 응답 예시** (404 Not Found):
```json
{
  "success": false,
  "message": "Action event not found with Id=999",
  "data": null,
  "meta": {
    "timestamp": "2025-01-14T11:10:00.100Z",
    "request_id": "550e8438-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 6.4.7 Action Event 동작 로직 상세

**개요**:
ActionEvent는 DetectionEvent(침입 탐지), MalfunctionEvent(장애 발생)에 대한 조치 보고를 기록하며, source event와 1:1 관계를 유지합니다.

**생성 시 자동 동작**:

1. **Source Event 자동 업데이트**:
   - ActionEvent가 생성되면 source event의 `action_reported` 필드가 자동으로 "False" → "True"로 업데이트됩니다
   - 이는 해당 이벤트에 대한 조치가 이미 보고되었음을 나타냅니다
   - `updated_at` 타임스탬프도 자동으로 갱신됩니다

2. **대상 이벤트 타입**:
   - `Intrusion` (침입 탐지) → DetectionEvent 업데이트
   - `Fault` (장애 발생) → MalfunctionEvent 업데이트

3. **1:1 관계 제약**:
   - 하나의 source event에는 최대 하나의 ActionEvent만 생성 가능합니다
   - 이미 ActionEvent가 존재하는 경우, 기존 ActionEvent를 먼저 삭제해야 합니다

**삭제 시 자동 동작**:

1. **Source Event 자동 복원**:
   - ActionEvent가 삭제되면 source event의 `action_reported` 필드가 자동으로 "True" → "False"로 복원됩니다
   - 이는 조치 보고가 취소되었음을 나타냅니다
   - `updated_at` 타임스탬프도 자동으로 갱신됩니다

2. **Source Event 삭제 가능**:
   - 복원 후에는 source event를 정상적으로 삭제할 수 있게 됩니다
   - `action_reported="True"`인 상태에서는 source event를 삭제할 수 없습니다 (409 Conflict)

**Source Event 삭제 제약**:

1. **제약 조건**:
   - `action_reported="True"`인 DetectionEvent 또는 MalfunctionEvent는 삭제할 수 없습니다
   - ActionEvent를 먼저 삭제한 후 source event를 삭제해야 합니다

2. **에러 응답** (409 Conflict):
   - DetectionEvent: "조치보고가 등록된 탐지 이벤트는 삭제할 수 없습니다. ActionEvent를 먼저 삭제해주세요."
   - MalfunctionEvent: "조치보고가 등록된 장애 이벤트는 삭제할 수 없습니다. ActionEvent를 먼저 삭제해주세요."

3. **예외**:
   - ConnectionEvent는 `action_reported` 필드가 없으므로 언제든 삭제 가능합니다

**동작 흐름 예시**:

```
1. DetectionEvent 생성 (action_reported="False")
   ↓
2. ActionEvent 생성 → DetectionEvent.action_reported="True" (자동 업데이트)
   ↓
3. DetectionEvent 삭제 시도 → 409 Conflict (삭제 불가)
   ↓
4. ActionEvent 삭제 → DetectionEvent.action_reported="False" (자동 복원)
   ↓
5. DetectionEvent 삭제 → 200 OK (삭제 성공)
```

---

## 7. Integration API 설계

### 7.1 개요

Integration API는 GOP 시스템과 외부 시스템 간의 연동을 위한 설정 정보를 관리합니다. EventMapping API를 통해 이벤트 매핑 정보를 생성, 조회, 수정, 삭제할 수 있습니다.

**주요 기능**:
- ✅ 이벤트 매핑 설정 관리
- ✅ 이벤트 이름, 그룹, 카테고리 관리
- ✅ 매핑 활성화/비활성화 제어

---

### 7.2 EventMapping API

#### 7.2.1 EventMapping 목록 조회

**Endpoint**: `GET /api/integrations/event-mappings`

**Query Parameters**:
- `name_event` (string, optional): 이벤트 이름 필터
- `group_event` (string, optional): 이벤트 그룹 필터
- `category_event` (string, optional): 이벤트 카테고리 필터
- `status` (boolean, optional): 활성화 상태 필터
- `page` (int, optional, default=1): 페이지 번호
- `limit` (int, optional, default=20): 페이지당 항목 수

**Request Example**:
```http
GET /api/integrations/event-mappings?group_event=intrusion&status=true&page=1&limit=20 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Event mappings retrieved successfully",
  "data": [
    {
      "id": 1,
      "name_event": "침입 탐지",
      "group_event": "intrusion",
      "category_event": "detection",
      "description": "센서 침입 탐지 이벤트 매핑",
      "status": true,
      "created_at": "2025-01-10T09:00:00.000Z",
      "updated_at": "2025-01-10T09:00:00.000Z"
    },
    {
      "id": 2,
      "name_event": "장애 발생",
      "group_event": "malfunction",
      "category_event": "fault",
      "description": "센서 장애 발생 이벤트 매핑",
      "status": true,
      "created_at": "2025-01-10T09:10:00.000Z",
      "updated_at": "2025-01-10T09:10:00.000Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 2,
    "total_pages": 1
  },
  "meta": {
    "timestamp": "2025-01-10T11:00:00.250Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 7.2.2 EventMapping 단일 조회

**Endpoint**: `GET /api/integrations/event-mappings/{id}`

**Path Parameters**:
- `id` (int, required): EventMapping ID

**Request Example**:
```http
GET /api/integrations/event-mappings/1 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Event mapping retrieved successfully",
  "data": {
    "id": 1,
    "name_event": "침입 탐지",
    "group_event": "intrusion",
    "category_event": "detection",
    "description": "센서 침입 탐지 이벤트 매핑",
    "status": true,
    "created_at": "2025-01-10T09:00:00.000Z",
    "updated_at": "2025-01-10T09:00:00.000Z"
  },
  "meta": {
    "timestamp": "2025-01-10T11:01:00.050Z",
    "request_id": "550e8401-e29b-41d4-a716-446655440000"
  }
}
```

**Error Response** (404 Not Found):
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Event mapping not found with Id=999",
    "details": "No event mapping exists with the specified ID"
  },
  "meta": {
    "timestamp": "2025-01-10T11:01:00.050Z",
    "request_id": "550e8401-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 7.2.3 EventMapping 생성

**Endpoint**: `POST /api/integrations/event-mappings`

**Request Body**:
```json
{
  "name_event": "연결 상태 변경",
  "group_event": "connection",
  "category_event": "status",
  "description": "센서 연결 상태 변경 이벤트 매핑",
  "status": true
}
```

**Response Example** (201 Created):
```json
{
  "success": true,
  "message": "Event mapping created successfully",
  "data": {
    "id": 3,
    "name_event": "연결 상태 변경",
    "group_event": "connection",
    "category_event": "status",
    "description": "센서 연결 상태 변경 이벤트 매핑",
    "status": true,
    "created_at": "2025-01-10T11:15:00.000Z",
    "updated_at": "2025-01-10T11:15:00.000Z"
  },
  "meta": {
    "timestamp": "2025-01-10T11:15:00.100Z",
    "request_id": "550e8402-e29b-41d4-a716-446655440000"
  }
}
```

**Error Response** (400 Bad Request):
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": "Invalid request body"
  },
  "meta": {
    "timestamp": "2025-01-10T11:15:00.100Z",
    "request_id": "550e8402-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 7.2.4 EventMapping 수정 (부분)

**Endpoint**: `PATCH /api/integrations/event-mappings/{id}`

**Path Parameters**:
- `id` (int, required): EventMapping ID

**Request Body** (부분 수정 가능):
```json
{
  "description": "센서 침입 탐지 이벤트 - 수정된 설명",
  "status": false
}
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Event mapping updated successfully",
  "data": {
    "id": 1,
    "name_event": "침입 탐지",
    "group_event": "intrusion",
    "category_event": "detection",
    "description": "센서 침입 탐지 이벤트 - 수정된 설명",
    "status": false,
    "created_at": "2025-01-10T09:00:00.000Z",
    "updated_at": "2025-01-10T11:20:00.000Z"
  },
  "meta": {
    "timestamp": "2025-01-10T11:20:00.150Z",
    "request_id": "550e8403-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 7.2.5 EventMapping 수정 (전체)

**Endpoint**: `PUT /api/integrations/event-mappings/{id}`

**Path Parameters**:
- `id` (int, required): EventMapping ID

**Request Body** (모든 필드 필수):
```json
{
  "name_event": "침입 탐지 업데이트",
  "group_event": "intrusion",
  "category_event": "detection",
  "description": "전체 업데이트된 설명",
  "status": true
}
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Event mapping updated successfully",
  "data": {
    "id": 1,
    "name_event": "침입 탐지 업데이트",
    "group_event": "intrusion",
    "category_event": "detection",
    "description": "전체 업데이트된 설명",
    "status": true,
    "created_at": "2025-01-10T09:00:00.000Z",
    "updated_at": "2025-01-10T11:25:00.000Z"
  },
  "meta": {
    "timestamp": "2025-01-10T11:25:00.200Z",
    "request_id": "550e8404-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 7.2.6 EventMapping 삭제

**Endpoint**: `DELETE /api/integrations/event-mappings/{id}`

**Path Parameters**:
- `id` (int, required): EventMapping ID

**Request Example**:
```http
DELETE /api/integrations/event-mappings/3 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Event mapping deleted successfully",
  "data": null,
  "meta": {
    "timestamp": "2025-01-10T11:30:00.250Z",
    "request_id": "550e8405-e29b-41d4-a716-446655440000"
  }
}
```

**Error Response** (404 Not Found):
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Event mapping not found with Id=999",
    "details": "Cannot delete non-existent event mapping"
  },
  "meta": {
    "timestamp": "2025-01-10T11:30:00.250Z",
    "request_id": "550e8405-e29b-41d4-a716-446655440000"
  }
}
```

---

## 8. 에러 처리

### 8.1 에러 응답 형식

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": "Additional error details or suggestions",
    "field_errors": {
      "field_name": "Field-specific error message"
    }
  },
  "meta": {
    "timestamp": "2025-01-10T10:30:00.000Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### 8.2 에러 코드 정의

| HTTP 코드 | 에러 코드 | 설명 | 예제 시나리오 |
|-----------|-----------|------|---------------|
| 400 | `BAD_REQUEST` | 잘못된 요청 | 필수 파라미터 누락, 데이터 형식 오류 |
| 400 | `VALIDATION_ERROR` | 데이터 검증 실패 | 이메일 형식 오류, 범위 초과 값 |
| 401 | `UNAUTHORIZED` | 인증 실패 | 토큰 없음, 토큰 만료 |
| 403 | `FORBIDDEN` | 권한 없음 | 리소스 접근 권한 없음 |
| 404 | `NOT_FOUND` | 리소스 없음 | 존재하지 않는 ID 조회 |
| 409 | `CONFLICT` | 충돌 | 중복 리소스 생성 시도 |
| 422 | `UNPROCESSABLE_ENTITY` | 처리 불가 | 비즈니스 로직 오류 |
| 500 | `INTERNAL_ERROR` | 서버 내부 오류 | 예기치 않은 서버 오류 |
| 500 | `DB_ERROR` | 데이터베이스 오류 | DB 연결 실패, 쿼리 오류 |
| 503 | `SERVICE_UNAVAILABLE` | 서비스 불가 | 서버 점검, 과부하 |
| 504 | `TIMEOUT` | 타임아웃 | 요청 처리 시간 초과 |

### 8.3 에러 응답 예제

#### 400 Validation Error (데이터 검증 실패)

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed for one or more fields",
    "details": "Please check the field_errors for detailed information"
  },
  "meta": {
    "timestamp": "2025-01-10T10:30:00.000Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

#### 404 Not Found (리소스 없음)

```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Controller not found",
    "details": "No controller exists with Id=999"
  },
  "meta": {
    "timestamp": "2025-01-10T10:30:00.000Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

---

## 9. 부록

### 9.1 전체 Endpoint 목록

#### Device Endpoints

**Controllers**:
- `GET /api/devices/controllers` - 목록 조회
- `POST /api/devices/controllers` - 생성
- `GET /api/devices/controllers/{id}` - 단일 조회
- `PATCH /api/devices/controllers/{id}` - 수정
- `DELETE /api/devices/controllers/{id}` - 삭제

**Sensors**:
- `GET /api/devices/sensors` - 목록 조회
- `POST /api/devices/sensors` - 생성
- `GET /api/devices/sensors/{id}` - 단일 조회
- `PATCH /api/devices/sensors/{id}` - 수정
- `DELETE /api/devices/sensors/{id}` - 삭제

**Cameras**:
- `GET /api/devices/cameras` - 목록 조회
- `POST /api/devices/cameras` - 생성
- `GET /api/devices/cameras/{id}` - 단일 조회
- `PATCH /api/devices/cameras/{id}` - 수정
- `DELETE /api/devices/cameras/{id}` - 삭제

#### Event Endpoints

**Detection Events**:
- `GET /api/events/detections` - 목록 조회
- `POST /api/events/detections` - 생성
- `GET /api/events/detections/{id}` - 단일 조회
- `PATCH /api/events/detections/{id}` - 수정
- `DELETE /api/events/detections/{id}` - 삭제
- `GET /api/events/detections/{event_id}/action` - Action Event 조회

**Malfunction Events**:
- `GET /api/events/malfunctions` - 목록 조회
- `POST /api/events/malfunctions` - 생성
- `GET /api/events/malfunctions/{id}` - 단일 조회
- `PATCH /api/events/malfunctions/{id}` - 수정
- `DELETE /api/events/malfunctions/{id}` - 삭제
- `GET /api/events/malfunctions/{event_id}/action` - Action Event 조회

**Connection Events**:
- `GET /api/events/connections` - 목록 조회
- `POST /api/events/connections` - 생성
- `GET /api/events/connections/{id}` - 단일 조회
- `PATCH /api/events/connections/{id}` - 수정
- `DELETE /api/events/connections/{id}` - 삭제

**Action Events**:
- `GET /api/events/actions` - 목록 조회
- `POST /api/events/actions` - 생성
- `GET /api/events/actions/{id}` - 단일 조회
- `PATCH /api/events/actions/{id}` - 수정
- `DELETE /api/events/actions/{id}` - 삭제

#### Integration Endpoints

**Event Mappings**:
- `GET /api/integrations/event-mappings` - 목록 조회
- `POST /api/integrations/event-mappings` - 생성
- `GET /api/integrations/event-mappings/{id}` - 단일 조회
- `PATCH /api/integrations/event-mappings/{id}` - 수정 (부분)
- `PUT /api/integrations/event-mappings/{id}` - 수정 (전체)
- `DELETE /api/integrations/event-mappings/{id}` - 삭제

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| v1.7 | 2025-11-27 | **Phase 28: CameraEventPreset URL Schema Refactor**<br>- `CameraEventPreset.rtsp_uri` 단일 필드 → `urls` 객체로 변경<br>- `urls` 객체 구조: `{ "live": "rtsp://...", "record": "rtsp://..." }`<br>- DB 컬럼 변경: `rtsp_uri` → `url_live`, `url_record` 분리<br>- 모든 CameraEventMapping API 영향 (GET/POST/PUT/PATCH)<br>- Breaking Change: API Request/Response 구조 변경 |
| v1.6 | 2025-11-26 | **Enum 타입 업데이트**<br>- EnumEventType에 `Lowlight`, `DetectionMode`, `TrackingMode` 추가<br>- EnumCameraType에서 `FISHEYES`, `THERMAL` 제거<br>- Swagger UI 문서 개선: 모든 스키마 필드에 enum 허용값 설명 추가<br><br>**Phase 27: CameraEventMapping Enum Fix**<br>- `EnumGroupEvent` 삭제 (더 이상 사용하지 않음)<br>- `EnumCategoryEvent` 값 변경: `SENSOR_ONLY`, `SENSOR_WITH_CAMERA`, `SENSOR_WITH_AI_DETECT`, `AI_DETECT_ONLY`, `MOTION_DETECT`, `ETC`<br>- `CameraEventMapping.group_event`: Enum → Plain String(100)으로 변경<br>- `CameraEventMapping.category_event`: EnumCategoryEvent Enum 유지<br>- Router에서 group_event 유효성 검사 제거 (자유 텍스트 허용) |
| v1.5 | 2025-01-17 | **Phase 21: Event Timestamp 필드 리팩토링**<br>- 모든 Event 모델에서 `datetime` 필드 제거<br>- `created_at`, `updated_at` 필드만 유지 (자동 생성)<br>- Detection/Malfunction/Connection Event 모든 API에서 `datetime` 제거<br>- `created_at`에 index 추가하여 조회 성능 최적화<br>- Request Body에서 `datetime` 파라미터 제거 (자동 생성)<br>- Response Body에서 `datetime` 필드 제거 |
| v1.4 | 2025-01-14 | **Phase 20: Detection/Malfunction Event에서 Action Event 조회 API 추가**<br>- 섹션 6.1.7 추가: Detection Event의 Action Event 조회 API (`GET /api/events/detections/{event_id}/action`)<br>- 섹션 6.2.7 추가: Malfunction Event의 Action Event 조회 API (`GET /api/events/malfunctions/{event_id}/action`)<br>- 1:1 관계를 활용한 효율적인 ActionEvent 조회 기능 제공<br>- Nested source event 응답 구조 문서화 |
| v1.3 | 2025-01-14 | **Phase 17-19: Action Event 동작 로직 및 DELETE 응답 표준화**<br>- Event DELETE 응답 표준화: 모든 Event DELETE API에서 `data=null` 반환<br>- Action Event 생성 시 자동 동작 로직 설명 추가 (source event의 `action_reported` 자동 업데이트)<br>- Action Event 삭제 시 자동 복원 로직 설명 추가 (source event의 `action_reported` 자동 복원)<br>- Source Event 삭제 제약 조건 추가 (`action_reported="True"`인 경우 삭제 불가)<br>- 409 Conflict 응답 예시 추가 (Detection/Malfunction Event DELETE)<br>- 1:1 관계 제약 설명 추가 (1개 source event = 최대 1개 ActionEvent) <br>- 7.2 EventMapping API의 Error Response Json 포멧 수정 |
| v1.2 | 2025-11-13 | **Integration API 추가 및 ActionEvent 필드 표준화**<br>- Integration API 설계 추가 (EventMapping CRUD)<br>- ActionEvent 필드명 변경: `from_event_type` → `from_type_event`<br>- ActionEvent 타입 값 표준화: `detection/malfunction/connection` → `Intrusion/Fault/Connection` |
| v1.1 | 2025-11-12 | **초안 작성**<br>- 전체 API 설계 초안 작성<br>- Device API, Event API 기본 구조 정의 |

---

**문서 버전**: v1.7
**최종 업데이트**: 2025-11-27