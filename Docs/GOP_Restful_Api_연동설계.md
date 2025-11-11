# GOP RESTful API 연동 설계서 v1.0

**작성일**: 2025-11-10  
**작성자**: GHLee  
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
7. [에러 처리](#7-에러-처리)
8. [부록](#8-부록)

---

## 1. 개요

### 1.1 설계 목적

기존 `Ironwall.Dotnet.Libraries.Devices.Db`와 `Ironwall.Dotnet.Libraries.Events.Db` 서비스를 **RESTful API 기반**으로 전환하여:

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
- **DTO 구조를 그대로 사용**: 기존 C# 모델과 100% 호환

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
    PTZ,            // "PTZ" - Pan-Tilt-Zoom 카메라
    FISHEYES,       // "FISHEYES" - 어안 카메라
    THERMAL         // "THERMAL" - 열화상 카메라
}
```

### 4.2 Event Enum

#### EnumEventType
```csharp
//C# 데이터 (참고용)
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
//C# 데이터 (참고용)
public enum EnumDetectionType : int
{
    NONE = 0,                   // "NONE"
    CABLE_CUTTING = 1,          // "CABLE_CUTTING" - 케이블 절단
    CABLE_CONNECTED = 2,        // "CABLE_CONNECTED" - 케이블 연결
    PIR_SENSOR = 3,             // "PIR_SENSOR" - PIR 센서
    THERMAL_SENSOR = 5,         // "THERMAL_SENSOR" - 열화상 센서
    VIBRATION_SENSOR = 6,       // "VIBRATION_SENSOR" - 진동 센서
    CONTACT_SENSOR = 10,        // "CONTACT_SENSOR" - 접점 센서
    DISTANCE_SENSOR = 11        // "DISTANCE_SENSOR" - 거리 센서
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
- `include_controller` (boolean, optional): 제어기 정보 포함 여부 (기본값: false)
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

**Query Parameters**:
- `include_controller` (boolean, optional): 제어기 정보 포함 여부 (기본값: false)

**Request Example**:
```http
GET /api/devices/sensors/101?include_controller=true HTTP/1.1
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
    "controller": {
      "id": 1,
      "number_device": 1,
      "group_device": 1,
      "name_device": "Controller-A",
      "type_device": "Controller", //(EnumDeviceType)
      "version": "v2.1.0",
      "status": "ACTIVATED", //(EnumDeviceStatus)
      "ip_address": "192.168.1.100",
      "ip_port": 8001
    },
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
      "type_event": "Intrusion", //(EnumEventType)
      "device": {
        "id": 101,
        "number_device": 1,
        "group_device": 1,
        "name_device": "Sensor-A-1",
        "type_device": "Multi", //(EnumDeviceType)
        "version": "v1.5.0",
        "status": "ACTIVATED", //(EnumDeviceStatus)
        "controller_id": 1
      },
      "status": "True", //(EnumTrueFalse)
      "datetime": "2025-01-10T10:15:23.000Z",
      "result": "PIR_SENSOR", //(EnumDetectionType)
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
    "datetime": "2025-01-10T10:15:23.000Z",
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
  "result": "THERMAL_SENSOR", //(EnumDetectionType)
  "datetime": "2025-01-10T10:20:00.000Z"
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
    "datetime": "2025-01-10T10:20:00.000Z",
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
    "datetime": "2025-01-10T10:20:00.000Z",
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
  "datetime": "2025-01-10T10:25:00.000Z"
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
    "datetime": "2025-01-10T10:25:00.000Z",
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

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Detection event deleted successfully",
  "data": {
    "deleted": true,
    "id": 1002
  },
  "meta": {
    "timestamp": "2025-01-10T10:54:00.100Z",
    "request_id": "550e8422-e29b-41d4-a716-446655440000"
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
      "device": {
        "id": 103,
        "number_device": 3,
        "group_device": 1,
        "name_device": "Sensor-A-3",
        "type_device": "Fence", //(EnumDeviceType)
        "version": "v1.5.0",
        "status": "ERROR", //(EnumDeviceStatus)
        "controller_id": 1
      },
      "action_reported": "True", //(EnumTrueFalse)
      "datetime": "2025-01-03T14:20:00.000Z",
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
    "datetime": "2025-01-03T14:20:00.000Z",
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
  "datetime": "2025-01-10T11:00:00.000Z"
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
    "datetime": "2025-01-10T11:00:00.000Z",
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
    "datetime": "2025-01-10T11:00:00.000Z",
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
  "datetime": "2025-01-10T11:05:00.000Z"
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
    "datetime": "2025-01-10T11:05:00.000Z",
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

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Malfunction event deleted successfully",
  "data": {
    "deleted": true,
    "id": 2002
  },
  "meta": {
    "timestamp": "2025-01-10T10:59:00.100Z",
    "request_id": "550e8427-e29b-41d4-a716-446655440000"
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
      "datetime": "2025-01-10T09:00:00.000Z",
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
      "datetime": "2025-01-10T09:05:00.000Z",
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
    "datetime": "2025-01-10T09:00:00.000Z",
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
  "datetime": "2025-01-10T11:10:00.000Z"
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
    "datetime": "2025-01-10T11:10:00.000Z",
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
  "datetime": "2025-01-10T11:15:00.000Z"
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
    "datetime": "2025-01-10T11:15:00.000Z",
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
  "datetime": "2025-01-10T11:20:00.000Z"
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
    "datetime": "2025-01-10T11:20:00.000Z",
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

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Connection event deleted successfully",
  "data": {
    "deleted": true,
    "id": 3003
  },
  "meta": {
    "timestamp": "2025-01-10T11:05:00.100Z",
    "request_id": "550e8433-e29b-41d4-a716-446655440000"
  }
}
```

---

### 6.4 Action Event API

#### 6.4.1 Action Event 생성

**Endpoint**: `POST /api/events/actions`

**Request Body**:
```json
{
  "content": "침입 탐지 확인 및 순찰 출동 요청",
  "user": "operator_kim",
  "from_event": 1001, //이벤트 Id
  "datetime": "2025-01-10T10:16:00.000Z"
}
```

**Response Example** (201 Created):
```json
{
  "success": true,
  "message": "Action event created successfully",
  "data": {
    "id": 3001,
    "content": "침입 탐지 확인 및 순찰 출동 요청",
    "user": "operator_kim",
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
       "datetime": "2025-01-10T11:05:00.000Z",
    },
    "datetime": "2025-01-10T10:16:00.000Z",
    "created_at": "2025-01-10T10:43:00.150Z",
    "updated_at": "2025-01-10T10:43:00.150Z"
  },
  "meta": {
    "timestamp": "2025-01-10T10:43:00.150Z",
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
      "content": "침입 탐지 확인 및 순찰 출동 요청",
      "user": "operator_kim",
      "from_event": {
        "id": 1001,
        "group_event": "group_001",
        "type_event": "Intrusion" //(EnumEventType)
      },
      "datetime": "2025-01-10T10:16:00.000Z",
      "created_at": "2025-01-10T10:16:00.100Z",
      "updated_at": "2025-01-10T10:16:00.100Z"
    },
    {
      "id": 4002,
      "content": "장애 확인 및 유지보수팀 연락",
      "user": "operator_lee",
      "from_event": {
        "id": 2001,
        "group_event": "group_fault_001",
        "type_event": "Fault" //(EnumEventType)
      },
      "datetime": "2025-01-10T10:20:00.000Z",
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
      "datetime": "2025-01-10T10:20:00.000Z",
    },
    "datetime": "2025-01-10T10:16:00.000Z",
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
  "content": "침입 탐지 확인 완료 - 오탐지로 판명",
  "datetime": "2025-01-10T10:18:00.000Z"
}
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Action event updated successfully",
  "data": {
    "id": 4001,
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
      "datetime": "2025-01-10T10:20:00.000Z",
    },
    "datetime": "2025-01-10T10:18:00.000Z",
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
  "from_event": 1001,
  "datetime": "2025-01-10T10:25:00.000Z"
}
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Action event updated successfully",
  "data": {
    "id": 4001,
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
      "datetime": "2025-01-10T10:20:00.000Z",
    },
    "datetime": "2025-01-10T10:25:00.000Z",
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

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Action event deleted successfully",
  "data": {
    "deleted": true,
    "id": 4001
  },
  "meta": {
    "timestamp": "2025-01-10T11:10:00.100Z",
    "request_id": "550e8438-e29b-41d4-a716-446655440000"
  }
}
```

---

## 7. 에러 처리

### 7.1 에러 응답 형식

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

### 7.2 에러 코드 정의

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

### 7.3 에러 응답 예제

#### 400 Validation Error (데이터 검증 실패)

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed for one or more fields",
    "details": "Please check the field_errors for detailed information",
    "field_errors": {
      "number_device": "device_number must be between 1 and 999",
      "ip_address": "Invalid IP address format",
      "status": "status must be one of: ACTIVATED, ERROR, DEACTIVATED"
    }
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

## 8. 부록

### 8.1 전체 Endpoint 목록

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

**Connection Events**:
- `GET /api/events/connections` - 목록 조회
- `POST /api/events/connections` - 생성
- `GET /api/events/connections/{id}` - 단일 조회
- `PATCH /api/events/connections/{id}` - 수정
- `DELETE /api/events/connections/{id}` - 삭제

**Malfunction Events**:
- `GET /api/events/malfunctions` - 목록 조회
- `POST /api/events/malfunctions` - 생성
- `GET /api/events/malfunctions/{id}` - 단일 조회
- `PATCH /api/events/malfunctions/{id}` - 수정
- `DELETE /api/events/malfunctions/{id}` - 삭제

**Action Events**:
- `GET /api/events/actions` - 목록 조회
- `POST /api/events/actions` - 생성
- `GET /api/events/actions/{id}` - 단일 조회
- `PATCH /api/events/actions/{id}` - 수정
- `DELETE /api/events/actions/{id}` - 삭제

### 8.2 DTO 모델 매핑

#### Device 모델

**BaseDeviceModel 필드**:
- `id` (int): 디바이스 ID
- `number_device` (int): 디바이스 번호
- `group_device` (int): 디바이스 그룹
- `name_device` (string): 디바이스 이름
- `type_device` (EnumDeviceType): 디바이스 타입
- `version` (string): 버전
- `status` (EnumDeviceStatus): 상태 (JsonIgnore이지만 API 응답에 포함)
- `created_at` (datetime): 생성 시간
- `updated_at` (datetime): 수정 시간

**ControllerDeviceModel 추가 필드**:
- `ip_address` (string): IP 주소
- `ip_port` (int): 포트 번호
- `devices` (List<IBaseDeviceModel>): 연결된 센서 목록 (JsonIgnore, include_sensors=true 시 포함)

**SensorDeviceModel 추가 필드**:
- `controller` (IControllerDeviceModel): 연결된 제어기 정보 (include_controller=true 시 포함)

**CameraDeviceModel 추가 필드**:
- `ip_address` (string): IP 주소
- `ip_port` (int): 포트 번호
- `user_name` (string): 사용자명
- `user_password` (string): 비밀번호
- `rtsp_uri` (string): RTSP URI
- `rtsp_port` (int): RTSP 포트
- `mode` (EnumCameraMode): 카메라 모드
- `category` (EnumCameraType): 카메라 타입

#### Event 모델

**BaseEventModel 필드**:
- `id` (int): 이벤트 ID
- `type_event` (EnumEventType): 이벤트 타입
- `datetime` (datetime): 이벤트 발생 시간
- `created_at` (datetime): 생성 시간
- `updated_at` (datetime): 수정 시간

**ExEventModel 추가 필드**:
- `group_event` (string): 이벤트 그룹
- `device` (IBaseDeviceModel): 연결된 디바이스
- `status` (EnumTrueFalse): 이벤트 상태

**DetectionEventModel 추가 필드**:
- `result` (EnumDetectionType): 탐지 결과

**MalfunctionEventModel 추가 필드**:
- `reason` (EnumFaultType): 장애 원인
- `first_start` (int): 첫 번째 신호 시작점
- `first_end` (int): 첫 번째 신호 끝점
- `second_start` (int): 두 번째 신호 시작점
- `second_end` (int): 두 번째 신호 끝점

**ActionEventModel 필드**:
- `content` (string): 조치 내용
- `user` (string): 조치 사용자
- `from_event` (이벤트모델): 원본 이벤트
- `datetime` (datetime): 조치 시간


---
**문서 버전**: v1.0  
**최종 업데이트**: 2025-11-10