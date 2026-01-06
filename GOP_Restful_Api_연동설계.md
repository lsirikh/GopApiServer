# GOP RESTful API 연동 설계서

**작성일**: 2025-12-31  
**최종 수정일**: 2026-01-06  
**작성자**: 이기호 차장  
**목적**: GOP용 통제시스템에 연동하기 위한 RESTful API기반 메시지 시스템 구성  
**설계 원칙**: 기존 DTO 구조를 그대로 사용하여 일관성 확보  

---

## 목차

1. [개요](#1-개요)
2. [API 구조 및 규칙](#2-api-구조-및-규칙)
3. [공통 사양](#3-공통-사양)
4. [Enum 타입 정의](#4-enum-타입-정의)
5. [Device API 설계](#5-device-api-설계)
   - 5.1 [Controller API](#51-controller-api)
   - 5.2 [Sensor API](#52-sensor-api)
   - 5.3 [Camera API](#53-camera-api)
   - 5.4 [DeviceGroup API](#54-devicegroup-api)
   - 5.5 [Camera Preset API](#55-camera-preset-api) *(v2.1 신규)*
   - 5.6 [ROI API](#56-roi-api) *(v2.1 신규)*
   - 5.7 [XyPoint API](#57-xypoint-api) *(v2.1 신규)*
6. [Event API 설계](#6-event-api-설계)
7. [Integration API 설계](#7-integration-api-설계)
8. [Server Monitoring API 설계](#8-server-monitoring-api-설계)
9. [에러 처리](#9-에러-처리)
10. [부록](#10-부록)
    - 10.1 [전체 Endpoint 목록](#101-전체-endpoint-목록)
    - 10.2 [Event-Device 리팩토링 변경사항 (v2.3)](#102-event-device-리팩토링-변경사항-v23)
    - 10.3 [EventMapping 리팩토링 변경사항 (v2.3)](#103-eventmapping-리팩토링-변경사항-v23)

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

#### EnumDeviceCategory (v2.0 신규)
```python
# Python 정의 - app/utils/enums.py
# Device Polymorphic Discriminator (Joined Table Inheritance)
class EnumDeviceCategory(str, Enum):
    CONTROLLER = "controller"   # 컨트롤러
    SENSOR = "sensor"           # 센서
    CAMERA = "camera"           # 카메라
```

**사용처**:
- `DeviceGroupMapping.category_device`: 디바이스 그룹 매핑 시 디바이스 종류 구분
- Device 모델의 Polymorphic Discriminator (Joined Table Inheritance)
- API 요청 시 디바이스 카테고리 필터링

**참고**: 이 Enum은 `type_device`(EnumDeviceType)와 다릅니다:
- `category_device`: 상위 카테고리 (controller, sensor, camera)
- `type_device`: 구체적인 장치 유형 (Controller, Multi, Fence, IpCamera 등)

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

### 4.4 Server Monitoring Enum

#### EnumServerType
```python
# Python 정의 - app/utils/enums.py
class EnumServerType(str, Enum):
    VMS = "VMS"                     # Video Management System
    NVR_API = "NVR_API"             # Network Video Recorder API
    STREAMING = "STREAMING"          # 스트리밍 서버
    TRANSCODER = "TRANSCODER"        # 트랜스코더 서버
    MEDIA = "MEDIA"                  # 미디어 서버
    RECORDING = "RECORDING"          # 녹화 서버
    PLAYBACK = "PLAYBACK"            # 재생 서버
    STORAGE = "STORAGE"              # 스토리지 서버
    AI_ANALYSIS = "AI_ANALYSIS"      # 지능형영상 분석 서버
    AI_TRAINING = "AI_TRAINING"      # AI 학습 서버
    AI_INFERENCE = "AI_INFERENCE"    # AI 추론 서버
    ANALYTICS = "ANALYTICS"          # 분석 서버
    DB_API = "DB_API"               # 데이터베이스 API 서버
    SPEAKER_API = "SPEAKER_API"     # 스피커 제어 API 서버
    ENCLOSURE_API = "ENCLOSURE_API" # 함체 관리 API 서버
    PIDS_API = "PIDS_API"           # PIDS API 서버
    WEB = "WEB"                     # 웹 서버
    AUTH = "AUTH"                   # 인증 서버
    PROXY = "PROXY"                 # 프록시 서버
    BROKER = "BROKER"               # 메시지 브로커 서버
    GATEWAY = "GATEWAY"             # 게이트웨이 서버
    PUSH = "PUSH"                   # 푸시 알림 서버
    LOG = "LOG"                     # 로그 서버
    BACKUP = "BACKUP"               # 백업 서버
    MONITORING = "MONITORING"        # 모니터링 서버
    ETC = "ETC"                     # 기타
```

#### EnumServerStatus
```python
# Python 정의 - app/utils/enums.py
class EnumServerStatus(str, Enum):
    NORMAL = "NORMAL"       # 정상 상태
    WARNING = "WARNING"     # 경고 상태 (리소스 사용률 높음)
    ERROR = "ERROR"         # 에러 상태 (서버 응답 없음/장애)
```

---

## 5. Device API 설계

### 5.1 Controller API

#### 5.1.1 Controller 목록 조회

**Endpoint**: `GET /api/devices/controllers`

**Query Parameters**:
- `group_device` (int, optional): 디바이스 그룹 필터 (레거시 1:1 관계)
- `group_id` (int, optional): DeviceGroup ID로 필터링 (N:N 관계)
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
      "group_device": 1, // (Deprecated 예정, 레거시)
      "name_device": "Controller-A",
      "type_device": "Controller", //(EnumDeviceType)
      "version": "v2.1.0",
      "status": "ACTIVATED", //(EnumDeviceStatus)
      "ip_address": "192.168.1.100",
      "ip_port": 8001,
      "created_at": "2025-01-01T00:00:00.000Z",
      "updated_at": "2025-01-10T10:30:00.000Z",
      "device_groups": [
        {"id": 1, "name": "GOP 1구역", "description": "GOP 1구역 장비 그룹", "device_count": 5}
      ]
    },
    {
      "id": 2,
      "number_device": 2,
      "group_device": 1, // (Deprecated 예정, 레거시)
      "name_device": "Controller-B",
      "type_device": "Controller", //(EnumDeviceType)
      "version": "v2.1.0",
      "status": "ACTIVATED", //(EnumDeviceStatus)
      "ip_address": "192.168.1.101",
      "ip_port": 8001,
      "created_at": "2025-01-02T00:00:00.000Z",
      "updated_at": "2025-01-10T10:29:00.000Z",
      "device_groups": []
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

**Response Example** (200 OK, `include_sensors=true`):
```json
{
  "success": true,
  "message": "2 controllers retrieved",
  "data": [
    {
      "id": 1,
      "number_device": 1,
      "group_device": 1, // (Deprecated 예정, 레거시)
      "name_device": "Controller-A",
      "type_device": "Controller", //(EnumDeviceType)
      "version": "v2.1.0",
      "status": "ACTIVATED", //(EnumDeviceStatus)
      "ip_address": "192.168.1.100",
      "ip_port": 8001,
      "created_at": "2025-01-01T00:00:00.000Z",
      "updated_at": "2025-01-10T10:30:00.000Z",
      "sensors": [
        {
          "id": 101,
          "number_device": 1,
          "group_device": 1, // (Deprecated 예정, 레거시)
          "name_device": "Sensor-A-1",
          "type_device": "Multi", //(EnumDeviceType)
          "version": "v1.5.0",
          "status": "ACTIVATED", //(EnumDeviceStatus)
          "controller_id": 1,
          "device_groups": [
            {"id": 1, "name": "GOP 1구역", "description": "GOP 1구역 장비 그룹", "device_count": 5}
          ]
        }
      ],
      "device_groups": [
        {"id": 1, "name": "GOP 1구역", "description": "GOP 1구역 장비 그룹", "device_count": 5}
      ]
    },
    {
      "id": 2,
      "number_device": 2,
      "group_device": 1, // (Deprecated 예정, 레거시)
      "name_device": "Controller-B",
      "type_device": "Controller", //(EnumDeviceType)
      "version": "v2.1.0",
      "status": "ACTIVATED", //(EnumDeviceStatus)
      "ip_address": "192.168.1.101",
      "ip_port": 8001,
      "created_at": "2025-01-02T00:00:00.000Z",
      "updated_at": "2025-01-10T10:29:00.000Z",
      "sensors": [],
      "device_groups": []
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
GET /api/devices/controllers/1 HTTP/1.1
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
    "group_device": 1, // (Deprecated 예정, 레거시)
    "name_device": "Controller-A",
    "type_device": "Controller", //(EnumDeviceType)
    "version": "v2.1.0",
    "status": "ACTIVATED", //(EnumDeviceStatus)
    "ip_address": "192.168.1.100",
    "ip_port": 8001,
    "sensors": null,
    "created_at": "2025-01-01T00:00:00.000Z",
    "updated_at": "2025-01-10T10:30:00.000Z",
    "device_groups": [
      {"id": 1, "name": "GOP 1구역", "description": "GOP 1구역 장비 그룹", "device_count": 5}
    ]
  },
  "meta": {
    "timestamp": "2025-01-10T10:31:00.050Z",
    "request_id": "550e8401-e29b-41d4-a716-446655440000"
  }
}
```

**Response Example** (200 OK, `include_sensors=true`):
```json
{
  "success": true,
  "message": "Controller retrieved successfully",
  "data": {
    "id": 1,
    "number_device": 1,
    "group_device": 1, // (Deprecated 예정, 레거시)
    "name_device": "Controller-A",
    "type_device": "Controller", //(EnumDeviceType)
    "version": "v2.1.0",
    "status": "ACTIVATED", //(EnumDeviceStatus)
    "ip_address": "192.168.1.100",
    "ip_port": 8001,
    "sensors": [
      {
        "id": 101,
        "number_device": 1,
        "group_device": 1, // (Deprecated 예정, 레거시)
        "name_device": "Sensor-A-1",
        "type_device": "Multi", //(EnumDeviceType)
        "version": "v1.5.0",
        "status": "ACTIVATED", //(EnumDeviceStatus)
        "controller_id": 1,
        "device_groups": [
          {"id": 1, "name": "GOP 1구역", "description": "GOP 1구역 장비 그룹", "device_count": 5}
        ]
      },
      {
        "id": 102,
        "number_device": 2,
        "group_device": 1, // (Deprecated 예정, 레거시)
        "name_device": "Sensor-A-2",
        "type_device": "Fence", //(EnumDeviceType)
        "version": "v1.5.0",
        "status": "ACTIVATED", //(EnumDeviceStatus)
        "controller_id": 1,
        "device_groups": []
      }
    ],
    "created_at": "2025-01-01T00:00:00.000Z",
    "updated_at": "2025-01-10T10:30:00.000Z",
    "device_groups": [
      {"id": 1, "name": "GOP 1구역", "description": "GOP 1구역 장비 그룹", "device_count": 5}
    ]
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
  "group_device": 1, // (Deprecated 예정, 레거시) 
  "name_device": "Controller-C",
  "type_device": "Controller", //(EnumDeviceType)
  "version": "v2.1.0",
  "status": "DEACTIVATED", //(EnumDeviceStatus)
  "ip_address": "192.168.1.102",
  "ip_port": 8001,
  "group_ids": [1, 2] // (optional) 소속 디바이스 그룹 ID 배열 (N:N 관계)
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
    "group_device": 1, // (Deprecated 예정, 레거시) 
    "name_device": "Controller-C",
    "type_device": "Controller", //(EnumDeviceType)
    "version": "v2.1.0",
    "status": "DEACTIVATED", //(EnumDeviceStatus)
    "ip_address": "192.168.1.102",
    "ip_port": 8001,
    "created_at": "2025-01-10T10:34:00.100Z",
    "updated_at": "2025-01-10T10:34:00.100Z",
    "device_groups": [
      {"id": 1, "name": "GOP 1구역", "description": "GOP 1구역 장비 그룹", "device_count": 6},
      {"id": 2, "name": "GOP 2구역", "description": "GOP 2구역 장비 그룹", "device_count": 3}
    ]
  },
  "meta": {
    "timestamp": "2025-01-10T10:34:00.100Z",
    "request_id": "550e8404-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 5.1.4 Controller 수정 (부분)

**Endpoint**: `PATCH /api/devices/controllers/{id}`

**Query Parameters**:
- `include_sensors` (boolean, optional): 센서 목록 포함 여부 (기본값: false)

**Request Body** (부분 업데이트):
```json
{
  "name_device": "Controller-C-Updated",
  "status": "ACTIVATED", //(EnumDeviceStatus)
  "version": "v2.2.0",
  "group_ids": [1] // (optional) 소속 디바이스 그룹 ID 배열 변경
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
    "group_device": 1, // (Deprecated 예정, 레거시)
    "name_device": "Controller-C-Updated",
    "type_device": "Controller", //(EnumDeviceType)
    "version": "v2.2.0",
    "status": "ACTIVATED", //(EnumDeviceStatus)
    "ip_address": "192.168.1.102",
    "ip_port": 8001,
    "created_at": "2025-01-10T10:34:00.100Z",
    "updated_at": "2025-01-10T10:35:00.150Z",
    "device_groups": [
      {"id": 1, "name": "GOP 1구역", "description": "GOP 1구역 장비 그룹", "device_count": 6}
    ]
  },
  "meta": {
    "timestamp": "2025-01-10T10:35:00.150Z",
    "request_id": "550e8405-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 5.1.5 Controller 수정 (전체)

**Endpoint**: `PUT /api/devices/controllers/{id}`

**Query Parameters**:
- `include_sensors` (boolean, optional): 센서 목록 포함 여부 (기본값: false)

**Request Body** (전체 업데이트):
```json
{
  "number_device": 3,
  "group_device": 1,
  "name_device": "Controller-C-Complete-Update",
  "type_device": "Controller",
  "version": "v2.3.0",
  "status": "ACTIVATED",
  "ip_address": "192.168.1.103",
  "ip_port": 8002
}
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Controller replaced successfully",
  "data": {
    "id": 3,
    "number_device": 3,
    "group_device": 1,
    "name_device": "Controller-C-Complete-Update",
    "type_device": "Controller",
    "version": "v2.3.0",
    "status": "ACTIVATED",
    "ip_address": "192.168.1.103",
    "ip_port": 8002,
    "created_at": "2025-01-10T10:34:00.100Z",
    "updated_at": "2025-01-10T10:36:00.200Z",
    "sensors": null,
    "device_groups": [
      {"id": 1, "name": "GOP 1구역", "description": "GOP 1구역 장비 그룹", "device_count": 6}
    ]
  },
  "meta": {
    "timestamp": "2025-01-10T10:36:00.200Z",
    "request_id": "550e8406-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 5.1.6 Controller 삭제

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
- `group_device` (int, optional): 디바이스 그룹 필터 (레거시 1:1 관계)
- `group_id` (int, optional): DeviceGroup ID로 필터링 (N:N 관계)
- `type_device` (string, optional): 센서 타입 필터 (Multi, Fence, Underground, PIR 등)
- `status` (string, optional): 상태 필터
- `controller_id` (int, optional): 제어기 ID 필터
- `include_controller` (boolean, optional): 컨트롤러 정보 포함 여부 (기본값: false)
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
      "group_device": 1, // (Deprecated 예정, 레거시)
      "name_device": "Sensor-A-1",
      "type_device": "Multi", //(EnumDeviceType)
      "version": "v1.5.0",
      "status": "ACTIVATED", //(EnumDeviceStatus)
      "controller_id": 1,
      "created_at": "2025-01-01T00:00:00.000Z",
      "updated_at": "2025-01-10T10:30:00.000Z",
      "device_groups": [
        {"id": 1, "name": "GOP 1구역", "description": "GOP 1구역 장비 그룹", "device_count": 5}
      ],
      "controller": null
    },
    {
      "id": 102,
      "number_device": 2,
      "group_device": 1, // (Deprecated 예정, 레거시)
      "name_device": "Sensor-A-2",
      "type_device": "Fence", //(EnumDeviceType)
      "version": "v1.5.0",
      "status": "ACTIVATED", //(EnumDeviceStatus)
      "controller_id": 1,
      "created_at": "2025-01-01T00:00:00.000Z",
      "updated_at": "2025-01-10T10:30:00.000Z",
      "device_groups": [],
      "controller": null
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

**Response Example** (200 OK, `include_controller=true`):
```json
{
  "success": true,
  "message": "15 sensors retrieved",
  "data": [
    {
      "id": 101,
      "number_device": 1,
      "group_device": 1, // (Deprecated 예정, 레거시)
      "name_device": "Sensor-A-1",
      "type_device": "Multi", //(EnumDeviceType)
      "version": "v1.5.0",
      "status": "ACTIVATED", //(EnumDeviceStatus)
      "controller_id": 1,
      "created_at": "2025-01-01T00:00:00.000Z",
      "updated_at": "2025-01-10T10:30:00.000Z",
      "device_groups": [
        {"id": 1, "name": "GOP 1구역", "description": "GOP 1구역 장비 그룹", "device_count": 5}
      ],
      "controller": {
        "id": 1,
        "number_device": 1,
        "group_device": 1, // (Deprecated 예정, 레거시)
        "name_device": "Controller-A",
        "type_device": "MainController",
        "version": "v2.0.0",
        "status": "ACTIVATED",
        "ip_address": "192.168.1.101",
        "ip_port": 8080,
        "device_groups": [
          {"id": 2, "name": "GOP 2구역", "description": "GOP 2구역 장비 그룹", "device_count": 3}
        ]
      }
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
- `include_controller` (boolean, optional): 컨트롤러 정보 포함 여부 (기본값: false)

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
    "group_device": 1, // (Deprecated 예정, 레거시)
    "name_device": "Sensor-A-1",
    "type_device": "Multi", //(EnumDeviceType)
    "version": "v1.5.0",
    "status": "ACTIVATED", //(EnumDeviceStatus)
    "controller_id": 1,
    "created_at": "2025-01-01T00:00:00.000Z",
    "updated_at": "2025-01-10T10:30:00.000Z",
    "device_groups": [
      {"id": 1, "name": "GOP 1구역", "description": "GOP 1구역 장비 그룹", "device_count": 5}
    ],
    "controller": null
  },
  "meta": {
    "timestamp": "2025-01-10T10:38:00.050Z",
    "request_id": "550e8408-e29b-41d4-a716-446655440000"
  }
}
```

**Response Example** (200 OK, `include_controller=true`):
```json
{
  "success": true,
  "message": "Sensor retrieved successfully",
  "data": {
    "id": 101,
    "number_device": 1,
    "group_device": 1, // (Deprecated 예정, 레거시)
    "name_device": "Sensor-A-1",
    "type_device": "Multi", //(EnumDeviceType)
    "version": "v1.5.0",
    "status": "ACTIVATED", //(EnumDeviceStatus)
    "controller_id": 1,
    "created_at": "2025-01-01T00:00:00.000Z",
    "updated_at": "2025-01-10T10:30:00.000Z",
    "device_groups": [
      {"id": 1, "name": "GOP 1구역", "description": "GOP 1구역 장비 그룹", "device_count": 5}
    ],
    "controller": {
      "id": 1,
      "number_device": 1,
      "group_device": 1, // (Deprecated 예정, 레거시)
      "name_device": "Controller-A",
      "type_device": "MainController",
      "version": "v2.0.0",
      "status": "ACTIVATED",
      "ip_address": "192.168.1.101",
      "ip_port": 8080,
      "device_groups": [
        {"id": 2, "name": "GOP 2구역", "description": "GOP 2구역 장비 그룹", "device_count": 3}
      ]
    }
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
  "group_device": 1, // (Deprecated 예정, 레거시)
  "name_device": "Fence-001",
  "type_device": "Fence", //(EnumDeviceType)
  "version": "v2.1.0",
  "status": "DEACTIVATED", //(EnumDeviceStatus)
  "controller_id": 1,
  "group_ids": [1, 2] // (optional) 소속 디바이스 그룹 ID 배열 (N:N 관계)
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
    "group_device": 1, // (Deprecated 예정, 레거시)
    "name_device": "Fence-001",
    "type_device": "Fence", //(EnumDeviceType)
    "version": "v2.1.0",
    "status": "DEACTIVATED", //(EnumDeviceStatus)
    "controller_id": 1,
    "created_at": "2025-01-10T10:39:00.100Z",
    "updated_at": "2025-01-10T10:39:00.100Z",
    "device_groups": [
      {"id": 1, "name": "GOP 1구역", "description": "GOP 1구역 장비 그룹", "device_count": 6},
      {"id": 2, "name": "GOP 2구역", "description": "GOP 2구역 장비 그룹", "device_count": 3}
    ]
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

**Query Parameters**:
- `include_controller` (boolean, optional): 컨트롤러 정보 포함 여부 (기본값: false)

**Request Body** (부분 업데이트):
```json
{
  "name_device": "Fence-001-Updated",
  "status": "ACTIVATED", //(EnumDeviceStatus)
  "version": "v2.2.0",
  "group_ids": [1] // (optional) 소속 디바이스 그룹 ID 배열 변경
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
    "group_device": 1, // (Deprecated 예정, 레거시)
    "name_device": "Fence-001-Updated",
    "type_device": "Fence", //(EnumDeviceType)
    "version": "v2.2.0",
    "status": "ACTIVATED", //(EnumDeviceStatus)
    "controller_id": 1,
    "created_at": "2025-01-10T10:39:00.100Z",
    "updated_at": "2025-01-10T10:40:00.150Z",
    "device_groups": [
      {"id": 1, "name": "GOP 1구역", "description": "GOP 1구역 장비 그룹", "device_count": 6}
    ]
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

**Query Parameters**:
- `include_controller` (boolean, optional): 컨트롤러 정보 포함 여부 (기본값: false)

**Request Body** (전체 업데이트):
```json
{
  "number_device": 3,
  "group_device": 1, // (Deprecated 예정, 레거시)
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
    "group_device": 1, // (Deprecated 예정, 레거시)
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
- `group_device` (int, optional): 디바이스 그룹 필터 (레거시 1:1 관계)
- `group_id` (int, optional): DeviceGroup ID로 필터링 (N:N 관계)
- `type_device` (string, optional): 장치 유형 필터 (IpCamera 등)
- `mode` (string, optional): 카메라 모드 필터 (NONE, ONVIF, EMSTONE_API, INNODEP_API, ETC)
- `category` (string, optional): 카메라 타입 필터 (NONE, FIXED, PTZ)
- `status` (string, optional): 상태 필터 (ACTIVATED, ERROR, DEACTIVATED)
- `page` (int, optional): 페이지 번호 (기본값: 1)
- `limit` (int, optional): 페이지당 항목 수 (기본값: 20, 최대 100개)

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "3 cameras retrieved",
  "data": [
    {
      "id": 201,
      "number_device": 109,
      "group_device": 1, // (Deprecated 예정, 레거시)
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
      "is_record": false,
      "hardware_spec": {
        "name": "GOP 1구역 PTZ 카메라",
        "location": "GOP 1구역 전방 초소",
        "manufacturer": "Hanwha Vision",
        "model": "XNP-6320RH",
        "firmware": "2.41.01",
        "mac_address": "00:09:18:AB:CD:EF"
      },
      "geolocation": {
        "location": "GOP 1구역 전방 초소",
        "latitude": 38.1234,
        "longitude": 127.5678,
        "altitude": 245.5
      },
      "device_groups": [
        {"id": 1, "name": "GOP 1구역", "description": "GOP 1구역 장비 그룹", "device_count": 5}
      ],
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
    "group_device": 1, // (Deprecated 예정, 레거시)
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
    "is_record": true,
    "hardware_spec": {
      "name": "GOP 1구역 PTZ 카메라",
      "location": "GOP 1구역 전방 초소",
      "manufacturer": "Hanwha Vision",
      "model": "XNP-6320RH",
      "hardware": "PTZ 32x Optical Zoom",
      "firmware": "2.41.01",
      "device_id": "HWV-XNP-001",
      "mac_address": "00:09:18:AB:CD:EF",
      "onvif_version": "2.4.2"
    },
    "geolocation": {
      "location": "GOP 1구역 전방 초소",
      "latitude": 38.1234,
      "longitude": 127.5678,
      "altitude": 245.5
    },
    "device_groups": [
      {"id": 1, "name": "GOP 1구역", "description": "GOP 1구역 장비 그룹", "device_count": 5},
      {"id": 3, "name": "야간 감시", "description": "야간 감시 그룹", "device_count": 3}
    ],
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
  "group_device": 1, // (Deprecated 예정, 레거시)
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
  "is_record": false,
  "hardware_spec": {
    "name": "신규 카메라",
    "manufacturer": "Hanwha Vision",
    "model": "XNP-6320RH"
  },
  "geolocation": {
    "latitude": 38.1234,
    "longitude": 127.5678
  },
  "group_ids": [1, 2]
}
```

> **Note**: `group_ids`는 N:N 관계로 여러 그룹에 할당 (권장), `group_device`는 레거시 호환용

**Response Example** (201 Created):
```json
{
  "success": true,
  "message": "Camera created successfully",
  "data": {
    "id": 202,
    "number_device": 110,
    "group_device": 1, // (Deprecated 예정, 레거시)
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
    "is_record": false,
    "hardware_spec": {
      "name": "신규 카메라",
      "manufacturer": "Hanwha Vision",
      "model": "XNP-6320RH"
    },
    "geolocation": {
      "latitude": 38.1234,
      "longitude": 127.5678
    },
    "device_groups": [
      {"id": 1, "name": "GOP 1구역", "description": "GOP 1구역 장비 그룹", "device_count": 6},
      {"id": 2, "name": "GOP 2구역", "description": "GOP 2구역 장비 그룹", "device_count": 3}
    ],
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

**Request Body** (부분 업데이트 - 변경할 필드만 포함):
```json
{
  "name_device": "Camera-110-Updated",
  "status": "ACTIVATED", //(EnumDeviceStatus)
  "user_password": "newpassword456",
  "is_record": true,
  "hardware_spec": {
    "firmware": "2.42.00",
    "location": "GOP 1구역 후방 초소"
  },
  "geolocation": {
    "latitude": 38.1250,
    "longitude": 127.5700,
    "altitude": 250.0,
    "install_location": "GOP 1구역 후방 초소"
  },
  "group_ids": [1, 3]
}
```

> **Note**: PATCH는 부분 업데이트이므로 변경할 필드만 포함합니다. `hardware_spec`, `geolocation`도 부분 업데이트가 가능하며, 기존 값에 병합됩니다.

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Camera updated successfully",
  "data": {
    "id": 202,
    "number_device": 110,
    "group_device": 1, // (Deprecated 예정, 레거시)
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
    "is_record": true,
    "hardware_spec": {
      "name": "신규 카메라",
      "location": "GOP 1구역 후방 초소",
      "manufacturer": "Hanwha Vision",
      "model": "XNP-6320RH",
      "firmware": "2.42.00"
    },
    "geolocation": {
      "latitude": 38.1250,
      "longitude": 127.5700,
      "altitude": 250.0,
      "install_location": "GOP 1구역 후방 초소"
    },
    "device_groups": [
      {"id": 1, "name": "GOP 1구역", "description": "GOP 1구역 장비 그룹", "device_count": 5},
      {"id": 3, "name": "야간 감시", "description": "야간 감시 그룹", "device_count": 3}
    ],
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

**Request Body** (전체 업데이트 - 모든 필드 필수):
```json
{
  "number_device": 110,
  "group_device": 1, // (Deprecated 예정, 레거시)
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
  "is_record": true,
  "hardware_spec": {
    "name": "GOP 1구역 PTZ 카메라",
    "location": "GOP 1구역 전방 초소",
    "manufacturer": "Hanwha Vision",
    "model": "XNP-6320RH",
    "hardware": "PTZ 32x Optical Zoom",
    "firmware": "2.42.00",
    "device_id": "HWV-XNP-001",
    "mac_address": "00:09:18:AB:CD:EF",
    "onvif_version": "2.4.2"
  },
  "geolocation": {
    "location": "GOP 1구역 전방 초소",
    "latitude": 38.1234,
    "longitude": 127.5678,
    "altitude": 245.5,
    "install_location": "GOP 1구역 전방 초소"
  },
  "group_ids": [1, 3]
}
```

> **Note**: PUT은 전체 업데이트이므로 모든 필드를 포함해야 합니다. 누락된 필드는 기본값 또는 null로 설정됩니다.

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Camera updated successfully",
  "data": {
    "id": 202,
    "number_device": 110,
    "group_device": 1, // (Deprecated 예정, 레거시)
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
    "is_record": true,
    "hardware_spec": {
      "name": "GOP 1구역 PTZ 카메라",
      "location": "GOP 1구역 전방 초소",
      "manufacturer": "Hanwha Vision",
      "model": "XNP-6320RH",
      "hardware": "PTZ 32x Optical Zoom",
      "firmware": "2.42.00",
      "device_id": "HWV-XNP-001",
      "mac_address": "00:09:18:AB:CD:EF",
      "onvif_version": "2.4.2"
    },
    "geolocation": {
      "location": "GOP 1구역 전방 초소",
      "latitude": 38.1234,
      "longitude": 127.5678,
      "altitude": 245.5,
      "install_location": "GOP 1구역 전방 초소"
    },
    "device_groups": [
      {"id": 1, "name": "GOP 1구역", "description": "GOP 1구역 장비 그룹", "device_count": 5},
      {"id": 3, "name": "야간 감시", "description": "야간 감시 그룹", "device_count": 3}
    ],
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

### 5.4 DeviceGroup API

디바이스 그룹은 여러 디바이스(Controller, Sensor, Camera)를 논리적으로 묶어 관리하는 기능입니다.
- N:N 관계: 하나의 디바이스는 여러 그룹에 속할 수 있고, 하나의 그룹은 여러 디바이스를 포함할 수 있습니다.
- 폴리모픽 응답: 그룹 상세 조회 시 디바이스 타입별로 다른 필드를 반환합니다.

#### 5.4.1 DeviceGroup 목록 조회

**Endpoint**: `GET /api/devices/groups`

**Query Parameters**:
- `name` (string, optional): 이름으로 필터링 (부분 검색)
- `page` (int, optional): 페이지 번호 (기본값: 1)
- `limit` (int, optional): 페이지당 항목 수 (기본값: 20, 최대 100개)

**Request Example**:
```http
GET /api/devices/groups?name=GOP&page=1&limit=20 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "디바이스 그룹 목록 조회 성공",
  "data": [
    {
      "id": 1,
      "name": "GOP 1구역",
      "description": "GOP 1구역 장비 그룹",
      "device_count": 5,
      "created_at": "2025-01-01T00:00:00.000Z",
      "updated_at": "2025-01-01T00:00:00.000Z"
    },
    {
      "id": 2,
      "name": "GOP 2구역",
      "description": "GOP 2구역 장비 그룹",
      "device_count": 3,
      "created_at": "2025-01-02T00:00:00.000Z",
      "updated_at": "2025-01-02T00:00:00.000Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 2,
    "total_pages": 1
  },
  "meta": {
    "timestamp": "2025-01-10T10:30:00.000Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 5.4.2 DeviceGroup 상세 조회 (폴리모픽 디바이스 목록 포함)

**Endpoint**: `GET /api/devices/groups/{id}`

**Path Parameters**:
- `id` (int, required): DeviceGroup ID

**Request Example**:
```http
GET /api/devices/groups/1 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "디바이스 그룹 조회 성공",
  "data": {
    "id": 1,
    "name": "GOP 1구역",
    "description": "GOP 1구역 장비 그룹",
    "device_count": 3,
    "created_at": "2025-01-01T00:00:00.000Z",
    "updated_at": "2025-01-01T00:00:00.000Z",
    "devices": [
      {
        "id": 1,
        "number_device": 1,
        "group_device": 1, // (Deprecated 예정, 레거시)
        "name_device": "Controller-A",
        "type_device": "Controller",
        "version": "v2.1.0",
        "status": "ACTIVATED",
        "ip_address": "192.168.1.100",
        "ip_port": 8001
      },
      {
        "id": 101,
        "number_device": 1,
        "group_device": 1, // (Deprecated 예정, 레거시)
        "name_device": "Sensor-A-1",
        "type_device": "Multi",
        "version": "v1.5.0",
        "status": "ACTIVATED",
        "controller_id": 1
      },
      {
        "id": 201,
        "number_device": 1,
        "group_device": 1, // (Deprecated 예정, 레거시)
        "name_device": "Camera-A-1",
        "type_device": "IpCamera",
        "version": "v1.0.0",
        "status": "ACTIVATED",
        "ip_address": "192.168.1.200",
        "ip_port": 80,
        "user_name": "admin",
        "user_password": "admin1234",
        "rtsp_uri": "rtsp://192.168.1.200:554/stream1",
        "rtsp_port": 554,
        "mode": "RTSP",
        "camera_category": "PTZ",
        "is_record": true,
        "hardware_spec": {
          "manufacturer": "Samsung",
          "model": "SNP-6320H",
          "firmware": "2.20.01"
        },
        "geolocation": {
          "location": "GOP 1구역 전방 초소",
          "latitude": 38.1234,
          "longitude": 127.5678
        }
      }
    ]
  },
  "meta": {
    "timestamp": "2025-01-10T10:31:00.000Z",
    "request_id": "550e8401-e29b-41d4-a716-446655440000"
  }
}
```

> **Note**: `devices` 배열은 폴리모픽 응답으로, 디바이스 타입에 따라 다른 필드를 포함합니다:
> - **Controller**: `ip_address`, `ip_port`
> - **Sensor**: `controller_id`
> - **Camera**: `ip_address`, `ip_port`, `user_name`, `user_password`, `rtsp_uri`, `rtsp_port`, `mode`, `camera_category`, `is_record`, `hardware_spec`, `geolocation`

**Error Response** (404 Not Found):
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "DeviceGroup ID 999 not found",
    "details": "No device group exists with the specified ID"
  },
  "meta": {
    "timestamp": "2025-01-10T10:31:00.000Z",
    "request_id": "550e8401-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 5.4.3 DeviceGroup 생성

**Endpoint**: `POST /api/devices/groups`

**Request Body**:
```json
{
  "name": "GOP 3구역",
  "description": "GOP 3구역 장비 그룹"
}
```

**Response Example** (201 Created):
```json
{
  "success": true,
  "message": "디바이스 그룹 생성 성공",
  "data": {
    "id": 3,
    "name": "GOP 3구역",
    "description": "GOP 3구역 장비 그룹",
    "device_count": 0,
    "created_at": "2025-01-10T10:35:00.000Z",
    "updated_at": "2025-01-10T10:35:00.000Z"
  },
  "meta": {
    "timestamp": "2025-01-10T10:35:00.000Z",
    "request_id": "550e8402-e29b-41d4-a716-446655440000"
  }
}
```

**Error Response** (400 Bad Request - 이름 중복):
```json
{
  "success": false,
  "error": {
    "code": "BAD_REQUEST",
    "message": "DeviceGroup name 'GOP 3구역' already exists",
    "details": "Group name must be unique"
  },
  "meta": {
    "timestamp": "2025-01-10T10:35:00.000Z",
    "request_id": "550e8402-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 5.4.4 DeviceGroup 수정 (부분)

**Endpoint**: `PATCH /api/devices/groups/{id}`

**Request Body** (부분 업데이트):
```json
{
  "description": "GOP 3구역 장비 그룹 - 수정됨"
}
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "디바이스 그룹 수정 성공",
  "data": {
    "id": 3,
    "name": "GOP 3구역",
    "description": "GOP 3구역 장비 그룹 - 수정됨",
    "device_count": 0,
    "created_at": "2025-01-10T10:35:00.000Z",
    "updated_at": "2025-01-10T10:36:00.000Z"
  },
  "meta": {
    "timestamp": "2025-01-10T10:36:00.000Z",
    "request_id": "550e8403-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 5.4.5 DeviceGroup 수정 (전체)

**Endpoint**: `PUT /api/devices/groups/{id}`

**Request Body** (전체 업데이트):
```json
{
  "name": "GOP 3구역 - 전체수정",
  "description": "GOP 3구역 장비 그룹 - 전체 수정됨"
}
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "디바이스 그룹 수정 성공",
  "data": {
    "id": 3,
    "name": "GOP 3구역 - 전체수정",
    "description": "GOP 3구역 장비 그룹 - 전체 수정됨",
    "device_count": 0,
    "created_at": "2025-01-10T10:35:00.000Z",
    "updated_at": "2025-01-10T10:37:00.000Z"
  },
  "meta": {
    "timestamp": "2025-01-10T10:37:00.000Z",
    "request_id": "550e8404-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 5.4.6 DeviceGroup 삭제

**Endpoint**: `DELETE /api/devices/groups/{id}`

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "디바이스 그룹 삭제 성공",
  "data": {
    "id": 3
  },
  "meta": {
    "timestamp": "2025-01-10T10:38:00.000Z",
    "request_id": "550e8405-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 5.4.7 디바이스 그룹에 디바이스 할당

**Endpoint**: `POST /api/devices/groups/{id}/devices`

**Request Body**:
```json
{
  "device_ids": [1, 2, 3]
}
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "2개 디바이스 할당 완료, 1개 건너뜀",
  "data": {
    "group_id": 1,
    "assigned_device_ids": [1, 2],
    "skipped_device_ids": [3],
    "message": "2개 디바이스 할당 완료, 1개 건너뜀"
  },
  "meta": {
    "timestamp": "2025-01-10T10:39:00.000Z",
    "request_id": "550e8406-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 5.4.8 디바이스 그룹에서 디바이스 제거

**Endpoint**: `DELETE /api/devices/groups/{group_id}/devices/{device_id}`

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "디바이스 그룹에서 제거 성공",
  "data": {
    "group_id": 1,
    "device_id": 2,
    "message": "디바이스 그룹에서 제거 성공"
  },
  "meta": {
    "timestamp": "2025-01-10T10:40:00.000Z",
    "request_id": "550e8407-e29b-41d4-a716-446655440000"
  }
}
```

**Error Response** (404 Not Found):
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Device ID 999 is not assigned to group 1",
    "details": "The device is not a member of this group"
  },
  "meta": {
    "timestamp": "2025-01-10T10:40:00.000Z",
    "request_id": "550e8407-e29b-41d4-a716-446655440000"
  }
}
```

---

### 5.5 Camera Preset API

카메라의 프리셋(Preset)을 관리합니다. PTZ 카메라의 사전 정의된 위치/각도 설정을 저장하고 관리합니다.

**계층 구조**: `Camera` → `CameraPreset` → `ROI` → `XyPoint`

#### 5.5.1 CameraPreset 목록 조회

**Endpoint**: `GET /api/devices/cameras/{camera_id}/presets`

**Path Parameters**:
- `camera_id` (int, required): 카메라 ID

**Query Parameters**:
- `include_rois` (bool, optional): ROI 정보 포함 여부 (기본값: false)
- `page` (int, optional): 페이지 번호 (기본값: 1)
- `limit` (int, optional): 페이지당 항목 수 (기본값: 10, 최대: 100)

**Request Example**:
```http
GET /api/devices/cameras/201/presets?include_rois=true&page=1&limit=10 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Response Example** (200 OK, `include_rois=false` 기본값):
```json
{
  "success": true,
  "message": "Camera presets retrieved successfully",
  "data": {
    "items": [
      {
        "id": 1,
        "camera_id": 201,
        "camera_name": "Camera-A-1",
        "preset_index": 1,
        "preset_name": "입구 정면",
        "touring_time": 10,
        "roi_count": 2,
        "created_at": "2025-01-01T00:00:00.000Z",
        "updated_at": "2025-01-01T00:00:00.000Z"
      }
    ],
    "total": 1
  },
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 1,
    "total_pages": 1
  }
}
```

**Response Example** (200 OK, `include_rois=true`):
```json
{
  "success": true,
  "message": "Camera presets retrieved successfully",
  "data": {
    "items": [
      {
        "id": 1,
        "camera_id": 201,
        "camera_name": "Camera-A-1",
        "preset_index": 1,
        "preset_name": "입구 정면",
        "touring_time": 10,
        "roi_count": 2,
        "created_at": "2025-01-01T00:00:00.000Z",
        "updated_at": "2025-01-01T00:00:00.000Z",
        "rois": [
          {
            "id": 1,
            "name": "출입구 영역",
            "resolution_width": 1920.0,
            "resolution_height": 1080.0,
            "is_enable": true,
            "point_count": 4
          }
        ]
      }
    ],
    "total": 1
  },
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 1,
    "total_pages": 1
  }
}
```

---

#### 5.5.2 CameraPreset 상세 조회 (ROI 포함)

**Endpoint**: `GET /api/devices/cameras/{camera_id}/presets/{preset_id}`

**Path Parameters**:
- `camera_id` (int, required): 카메라 ID
- `preset_id` (int, required): 프리셋 ID

> **Nested Response 규칙**: `rois` nested 객체에서 `created_at`, `updated_at` 제외 (주체인 Preset만 timestamp 포함)

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Camera preset retrieved successfully",
  "data": {
    "id": 1,
    "camera_id": 201,
    "camera_name": "Camera-A-1",
    "preset_index": 1,
    "preset_name": "입구 정면",
    "touring_time": 10,
    "created_at": "2025-01-01T00:00:00.000Z",
    "updated_at": "2025-01-01T00:00:00.000Z",
    "rois": [
      {
        "id": 1,
        "preset_id": 1,
        "name": "출입구 영역",
        "resolution_width": 1920.0,
        "resolution_height": 1080.0,
        "is_enable": true,
        "points": [
          {"id": 1, "x": 0.1, "y": 0.1, "order": 0},
          {"id": 2, "x": 0.9, "y": 0.1, "order": 1},
          {"id": 3, "x": 0.9, "y": 0.9, "order": 2},
          {"id": 4, "x": 0.1, "y": 0.9, "order": 3}
        ]
      }
    ]
  }
}
```

---

#### 5.5.3 CameraPreset 생성

**Endpoint**: `POST /api/devices/cameras/{camera_id}/presets`

**Path Parameters**:
- `camera_id` (int, required): 카메라 ID

**Request Body**:
```json
{
  "preset_index": 1,
  "preset_name": "입구 정면",
  "touring_time": 15
}
```

**Response Example** (201 Created):
```json
{
  "success": true,
  "message": "Camera preset created successfully",
  "data": {
    "id": 1,
    "camera_id": 201,
    "camera_name": "Camera-A-1",
    "preset_index": 1,
    "preset_name": "입구 정면",
    "touring_time": 15,
    "roi_count": 0,
    "created_at": "2025-01-10T10:00:00.000Z",
    "updated_at": "2025-01-10T10:00:00.000Z"
  }
}
```

**Error Response** (409 Conflict - 중복 preset_index):
```json
{
  "success": false,
  "error": {
    "code": "CONFLICT",
    "message": "Preset with index 1 already exists for this camera",
    "details": "preset_index must be unique within the same camera"
  }
}
```

---

#### 5.5.4 CameraPreset 수정 (PATCH)

**Endpoint**: `PATCH /api/devices/cameras/{camera_id}/presets/{preset_id}`

**Request Body** (부분 업데이트):
```json
{
  "preset_name": "입구 정면 - 수정",
  "touring_time": 20
}
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Camera preset updated successfully",
  "data": {
    "id": 1,
    "camera_id": 201,
    "camera_name": "Camera-A-1",
    "preset_index": 1,
    "preset_name": "입구 정면 - 수정",
    "touring_time": 20,
    "roi_count": 2,
    "created_at": "2025-01-01T00:00:00.000Z",
    "updated_at": "2025-01-10T10:30:00.000Z"
  }
}
```

---

#### 5.5.5 CameraPreset 수정 (PUT - 전체)

**Endpoint**: `PUT /api/devices/cameras/{camera_id}/presets/{preset_id}`

**Request Body** (모든 필드 필수):
```json
{
  "preset_index": 1,
  "preset_name": "입구 정면 - 전체 수정",
  "touring_time": 25
}
```

---

#### 5.5.6 CameraPreset 삭제

**Endpoint**: `DELETE /api/devices/cameras/{camera_id}/presets/{preset_id}`

> **Note**: CASCADE 삭제로 인해 하위 ROI 및 XyPoint도 함께 삭제됩니다.

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Camera preset deleted successfully",
  "data": null
}
```

---

### 5.6 ROI API

프리셋 내 관심 영역(Region of Interest)을 관리합니다. ROI는 영상 내 다각형 영역을 정의합니다.

#### 5.6.1 ROI 목록 조회

**Endpoint**: `GET /api/presets/{preset_id}/rois`

**Path Parameters**:
- `preset_id` (int, required): 프리셋 ID

**Query Parameters**:
- `include_points` (bool, optional): Points 정보 포함 여부 (기본값: false)
- `page` (int, optional): 페이지 번호 (기본값: 1)
- `limit` (int, optional): 페이지당 항목 수 (기본값: 10, 최대: 100)

**Response Example** (200 OK, `include_points=false` 기본값):
```json
{
  "success": true,
  "message": "ROIs retrieved successfully",
  "data": {
    "items": [
      {
        "id": 1,
        "preset_id": 1,
        "name": "출입구 영역",
        "resolution_width": 1920.0,
        "resolution_height": 1080.0,
        "is_enable": true,
        "point_count": 4,
        "created_at": "2025-01-01T00:00:00.000Z",
        "updated_at": "2025-01-01T00:00:00.000Z"
      }
    ],
    "total": 1
  },
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 1,
    "total_pages": 1
  }
}
```

**Response Example** (200 OK, `include_points=true`):
```json
{
  "success": true,
  "message": "ROIs retrieved successfully",
  "data": {
    "items": [
      {
        "id": 1,
        "preset_id": 1,
        "name": "출입구 영역",
        "resolution_width": 1920.0,
        "resolution_height": 1080.0,
        "is_enable": true,
        "point_count": 4,
        "created_at": "2025-01-01T00:00:00.000Z",
        "updated_at": "2025-01-01T00:00:00.000Z",
        "points": [
          {"id": 1, "x": 0.1, "y": 0.1, "order": 0},
          {"id": 2, "x": 0.9, "y": 0.1, "order": 1},
          {"id": 3, "x": 0.9, "y": 0.9, "order": 2},
          {"id": 4, "x": 0.1, "y": 0.9, "order": 3}
        ]
      }
    ],
    "total": 1
  },
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 1,
    "total_pages": 1
  }
}
```

---

#### 5.6.2 ROI 상세 조회 (Points 포함)

**Endpoint**: `GET /api/presets/{preset_id}/rois/{roi_id}`

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "ROI retrieved successfully",
  "data": {
    "id": 1,
    "preset_id": 1,
    "name": "출입구 영역",
    "resolution_width": 1920.0,
    "resolution_height": 1080.0,
    "is_enable": true,
    "created_at": "2025-01-01T00:00:00.000Z",
    "updated_at": "2025-01-01T00:00:00.000Z",
    "points": [
      {"id": 1, "x": 0.1, "y": 0.1, "order": 0},
      {"id": 2, "x": 0.9, "y": 0.1, "order": 1},
      {"id": 3, "x": 0.9, "y": 0.9, "order": 2},
      {"id": 4, "x": 0.1, "y": 0.9, "order": 3}
    ]
  }
}
```

---

#### 5.6.3 ROI 생성 (Points 포함)

**Endpoint**: `POST /api/presets/{preset_id}/rois`

**Request Body**:
```json
{
  "name": "새로운 감시 영역",
  "resolution_width": 1920.0,
  "resolution_height": 1080.0,
  "is_enable": true,
  "points": [
    {"x": 0.2, "y": 0.2, "order": 0},
    {"x": 0.8, "y": 0.2, "order": 1},
    {"x": 0.8, "y": 0.8, "order": 2},
    {"x": 0.2, "y": 0.8, "order": 3}
  ]
}
```

**Response Example** (201 Created):
```json
{
  "success": true,
  "message": "ROI created successfully",
  "data": {
    "id": 2,
    "preset_id": 1,
    "name": "새로운 감시 영역",
    "resolution_width": 1920.0,
    "resolution_height": 1080.0,
    "is_enable": true,
    "point_count": 4,
    "created_at": "2025-01-10T10:00:00.000Z",
    "updated_at": "2025-01-10T10:00:00.000Z"
  }
}
```

---

#### 5.6.4 ROI 수정 (PATCH)

**Endpoint**: `PATCH /api/presets/{preset_id}/rois/{roi_id}`

**Request Body** (부분 업데이트):
```json
{
  "name": "감시 영역 - 수정",
  "is_enable": false
}
```

---

#### 5.6.5 ROI 수정 (PUT - 전체)

**Endpoint**: `PUT /api/presets/{preset_id}/rois/{roi_id}`

**Request Body** (모든 필드 필수):
```json
{
  "name": "감시 영역 - 전체 수정",
  "resolution_width": 1280.0,
  "resolution_height": 720.0,
  "is_enable": true
}
```

---

#### 5.6.6 ROI 삭제

**Endpoint**: `DELETE /api/presets/{preset_id}/rois/{roi_id}`

> **Note**: CASCADE 삭제로 인해 하위 XyPoint도 함께 삭제됩니다.

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "ROI deleted successfully",
  "data": null
}
```

---

### 5.7 XyPoint API

ROI 다각형의 꼭지점 좌표를 관리합니다. 좌표는 정규화된 값(0.0~1.0) 또는 픽셀 좌표를 사용할 수 있습니다.

#### 5.7.1 XyPoint 목록 조회

**Endpoint**: `GET /api/rois/{roi_id}/points`

**Path Parameters**:
- `roi_id` (int, required): ROI ID

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "4 points retrieved",
  "data": {
    "points": [
      {"id": 1, "roi_id": 1, "x": 0.1, "y": 0.1, "order": 0},
      {"id": 2, "roi_id": 1, "x": 0.9, "y": 0.1, "order": 1},
      {"id": 3, "roi_id": 1, "x": 0.9, "y": 0.9, "order": 2},
      {"id": 4, "roi_id": 1, "x": 0.1, "y": 0.9, "order": 3}
    ]
  }
}
```

---

#### 5.7.2 XyPoint 생성

**Endpoint**: `POST /api/rois/{roi_id}/points`

**Request Body**:
```json
{
  "x": 0.5,
  "y": 0.5,
  "order": 4
}
```

**Response Example** (201 Created):
```json
{
  "success": true,
  "message": "Point created successfully",
  "data": {
    "id": 5,
    "roi_id": 1,
    "x": 0.5,
    "y": 0.5,
    "order": 4,
    "created_at": "2025-01-10T10:00:00.000Z",
    "updated_at": "2025-01-10T10:00:00.000Z"
  }
}
```

---

#### 5.7.3 XyPoint 일괄 수정 (전체 교체)

**Endpoint**: `PUT /api/rois/{roi_id}/points`

> **Note**: 기존 포인트를 모두 삭제하고 새 포인트로 교체합니다.

**Request Body**:
```json
{
  "points": [
    {"x": 0.15, "y": 0.15, "order": 0},
    {"x": 0.85, "y": 0.15, "order": 1},
    {"x": 0.85, "y": 0.85, "order": 2},
    {"x": 0.15, "y": 0.85, "order": 3},
    {"x": 0.5, "y": 0.5, "order": 4}
  ]
}
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "5 points updated",
  "data": {
    "points": [
      {"id": 13, "roi_id": 1, "x": 0.15, "y": 0.15, "order": 0},
      {"id": 14, "roi_id": 1, "x": 0.85, "y": 0.15, "order": 1},
      {"id": 15, "roi_id": 1, "x": 0.85, "y": 0.85, "order": 2},
      {"id": 16, "roi_id": 1, "x": 0.15, "y": 0.85, "order": 3},
      {"id": 17, "roi_id": 1, "x": 0.5, "y": 0.5, "order": 4}
    ]
  }
}
```

---

#### 5.7.4 XyPoint 삭제

**Endpoint**: `DELETE /api/rois/{roi_id}/points/{point_id}`

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Point deleted successfully",
  "data": null
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
- `device_id` (int, optional): 장치 ID 필터 (PRD v2.2)
- `type_event` (string, optional): 이벤트 타입 필터 (Intrusion)
- `action_reported` (string, optional): 조치 보고 여부 필터 (True, False)
- `result` (string, optional): 탐지 결과 필터 (PIR_SENSOR, THERMAL_SENSOR 등)
- `page` (int, optional): 페이지 번호
- `limit` (int, optional): 페이지당 항목 수

> **PRD v2.2 변경**: `controller`, `sensor`, `type_device`, `group_event` → `device_id` 단일 FK로 통합
> **PRD v1.3 변경**: Response에서 `device_id`, `sequence` 필드 제거 (device.id에 포함, sequence는 Request 전용)

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "25 detection events retrieved",
  "data": [
    {
      "id": 1001,
      "type_event": "Intrusion",
      "action_reported": "True",
      "result": "PIR_SENSOR",
      "device": {
        "id": 101,
        "number_device": 1,
        "group_device": 1, // (Deprecated 예정, 레거시)
        "name_device": "Sensor-A-1",
        "type_device": "Multi",
        "version": "v1.5.0",
        "status": "ACTIVATED",
        "controller_id": 1,
        "device_groups": [
          {"id": 1, "name": "A구역 센서그룹", "description": "A구역 센서 장비 그룹", "device_count": 5}
        ]
      },
      "device_description": "[Multi] Sensor-A-1 (number: 1, id: 101)",
      "created_at": "2026-01-06T10:15:23.100Z",
      "updated_at": "2026-01-06T10:15:23.100Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 25,
    "total_pages": 2
  },
  "meta": {
    "timestamp": "2026-01-06T10:40:00.250Z",
    "request_id": "550e8500-e29b-41d4-a716-446655440000"
  }
}
```

**Response Example (Device 삭제된 경우)**:
```json
{
  "success": true,
  "message": "Detection event retrieved",
  "data": [
    {
      "id": 1001,
      "type_event": "Intrusion",
      "action_reported": "True",
      "result": "PIR_SENSOR",
      "device": null,
      "device_description": "[Multi] Sensor-A-1 (number: 1, id: 101)",
      "created_at": "2026-01-06T10:15:23.100Z",
      "updated_at": "2026-01-06T10:15:23.100Z"
    }
  ]
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
    "type_event": "Intrusion", //(EnumEventType)
    "action_reported": "True", //(EnumTrueFalse)
    "result": "PIR_SENSOR", //(EnumDetectionType)
    "device": {
      "id": 101,
      "number_device": 1,
      "group_device": 1, // (Deprecated 예정, 레거시)
      "name_device": "Sensor-A-1",
      "type_device": "Multi",
      "version": "v1.5.0",
      "status": "ACTIVATED",
      "controller_id": 1,
      "device_groups": [
        {"id": 1, "name": "A구역 센서그룹", "description": "A구역 센서 장비 그룹", "device_count": 5}
      ]
    },
    "device_description": "[Multi] Sensor-A-1 (number: 1, id: 101)",
    "created_at": "2026-01-06T10:15:23.100Z",
    "updated_at": "2026-01-06T10:15:23.100Z"
  },
  "meta": {
    "timestamp": "2026-01-06T10:50:00.050Z",
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
    "timestamp": "2026-01-06T10:50:00.050Z",
    "request_id": "550e8418-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 6.1.3 Detection Event 생성

**Endpoint**: `POST /api/events/detections`

> **PRD v2.2 변경**: `controller`, `sensor`, `type_device`, `group_event` → `device_id` 단일 FK로 통합
> **자동 생성**: `device_description`은 서버에서 자동 생성됨

**Request Body**:
```json
{
  "device_id": 101,
  "type_event": "Intrusion", //(EnumEventType)
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
    "type_event": "Intrusion", //(EnumEventType)
    "action_reported": "False", //(EnumTrueFalse)
    "result": "THERMAL_SENSOR", //(EnumDetectionType)
    "device": {
      "id": 101,
      "number_device": 1,
      "group_device": 1, // (Deprecated 예정, 레거시)
      "name_device": "Sensor-A-1",
      "type_device": "Multi",
      "version": "v1.5.0",
      "status": "ACTIVATED",
      "controller_id": 1,
      "device_groups": [
        {"id": 1, "name": "A구역 센서그룹", "description": "A구역 센서 장비 그룹", "device_count": 5}
      ]
    },
    "device_description": "[Multi] Sensor-A-1 (number: 1, id: 101)",
    "created_at": "2026-01-06T10:51:00.100Z",
    "updated_at": "2026-01-06T10:51:00.100Z"
  },
  "meta": {
    "timestamp": "2026-01-06T10:51:00.100Z",
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
  "type_event": "Intrusion", //(EnumEventType, optional)
  "result": "VIBRATION_SENSOR" //(EnumDetectionType, optional)
}
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Detection event updated successfully",
  "data": {
    "id": 1002,
    "type_event": "Intrusion", //(EnumEventType)
    "action_reported": "False", //(EnumTrueFalse)
    "result": "VIBRATION_SENSOR", //(EnumDetectionType)
    "device": {
      "id": 101,
      "number_device": 1,
      "group_device": 1, // (Deprecated 예정, 레거시)
      "name_device": "Sensor-A-1",
      "type_device": "Multi",
      "version": "v1.5.0",
      "status": "ACTIVATED",
      "controller_id": 1,
      "device_groups": [
        {"id": 1, "name": "A구역 센서그룹", "description": "A구역 센서 장비 그룹", "device_count": 5}
      ]
    },
    "device_description": "[Multi] Sensor-A-1 (number: 1, id: 101)",
    "created_at": "2026-01-06T10:51:00.100Z",
    "updated_at": "2026-01-06T10:52:00.150Z"
  },
  "meta": {
    "timestamp": "2026-01-06T10:52:00.150Z",
    "request_id": "550e8420-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 6.1.5 Detection Event 수정 (전체)

**Endpoint**: `PUT /api/events/detections/{id}`

> **PRD v2.2 변경**: `controller`, `sensor`, `type_device`, `group_event` → `device_id` 단일 FK로 통합

**Request Body** (전체 업데이트):
```json
{
  "device_id": 101,
  "type_event": "Intrusion", //(EnumEventType)
  "action_reported": "True", //(EnumTrueFalse)
  "result": "DISTANCE_SENSOR" //(EnumDetectionType)
}
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Detection event updated successfully",
  "data": {
    "id": 1002,
    "type_event": "Intrusion", //(EnumEventType)
    "action_reported": "True", //(EnumTrueFalse)
    "result": "DISTANCE_SENSOR", //(EnumDetectionType)
    "device": {
      "id": 101,
      "number_device": 1,
      "group_device": 1, // (Deprecated 예정, 레거시)
      "name_device": "Sensor-A-1",
      "type_device": "Multi",
      "version": "v1.5.0",
      "status": "ACTIVATED",
      "controller_id": 1,
      "device_groups": [
        {"id": 1, "name": "A구역 센서그룹", "description": "A구역 센서 장비 그룹", "device_count": 5}
      ]
    },
    "device_description": "[Multi] Sensor-A-1 (number: 1, id: 101)",
    "created_at": "2026-01-06T10:51:00.100Z",
    "updated_at": "2026-01-06T10:53:00.200Z"
  },
  "meta": {
    "timestamp": "2026-01-06T10:53:00.200Z",
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

> **PRD v1.3**: `from_event` 내부는 현재 Detection/Malfunction/Connection Event Response 포맷을 따름
> - `device` nested 포함 (Device 삭제 시 null)
> - `device_description` 포함
> - 레거시 필드 (`group_event`, `controller`, `sensor`, `type_device`, `sequence`, `device_id`) 제거됨

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
      "type_event": "Intrusion",
      "action_reported": "True",
      "result": "PIR_SENSOR",
      "device": {
        "id": 103,
        "number_device": 3,
        "group_device": 1,
        "name_device": "Sensor-A-3",
        "type_device": "Fence",
        "version": "v1.5.0",
        "status": "ACTIVATED",
        "controller_id": 1,
        "device_groups": [
          {"id": 1, "name": "A구역 센서그룹"}
        ]
      },
      "device_description": "[Fence] Sensor-A-3 (number: 3, id: 103)",
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
- `device_id` (int, optional): 장치 ID 필터 (PRD v2.2)
- `reason` (string, optional): 장애 원인 필터 (FAULT_CONTROLLER, FAULT_FENCE, FAULT_CABLE_CUTTING 등)
- `action_reported` (string, optional): 조치 보고 여부 필터 (True, False)
- `page` (int, optional): 페이지 번호
- `limit` (int, optional): 페이지당 항목 수

> **PRD v2.2 변경**: `controller`, `sensor`, `type_device`, `group_event` → `device_id` 단일 FK로 통합
> **PRD v1.3 변경**: Response에서 `device_id`, `sequence` 필드 제거 (device.id에 포함, sequence는 Request 전용)

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "5 malfunction events retrieved",
  "data": [
    {
      "id": 2001,
      "type_event": "Fault",
      "action_reported": "True",
      "reason": "FAULT_CABLE_CUTTING",
      "first_start": 10,
      "first_end": 15,
      "second_start": 20,
      "second_end": 25,
      "device": {
        "id": 103,
        "number_device": 3,
        "group_device": 1, // (Deprecated 예정, 레거시)
        "name_device": "Sensor-A-3",
        "type_device": "Fence",
        "version": "v1.5.0",
        "status": "ACTIVATED",
        "controller_id": 1,
        "device_groups": [
          {"id": 1, "name": "A구역 센서그룹", "description": "A구역 센서 장비 그룹", "device_count": 5}
        ]
      },
      "device_description": "[Fence] Sensor-A-3 (number: 3, id: 103)",
      "created_at": "2026-01-06T14:20:00.500Z",
      "updated_at": "2026-01-06T14:20:00.500Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 5,
    "total_pages": 1
  },
  "meta": {
    "timestamp": "2026-01-06T10:42:00.300Z",
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
    "type_event": "Fault", //(EnumEventType)
    "action_reported": "True", //(EnumTrueFalse)
    "reason": "FAULT_CABLE_CUTTING", //(EnumFaultType)
    "first_start": 5,
    "first_end": 5,
    "second_start": 0,
    "second_end": 0,
    "device": {
      "id": 103,
      "number_device": 3,
      "group_device": 1, // (Deprecated 예정, 레거시)
      "name_device": "Sensor-A-3",
      "type_device": "Fence",
      "version": "v1.5.0",
      "status": "ACTIVATED",
      "controller_id": 1,
      "device_groups": [
        {"id": 1, "name": "A구역 센서그룹", "description": "A구역 센서 장비 그룹", "device_count": 5}
      ]
    },
    "device_description": "[Fence] Sensor-A-3 (number: 3, id: 103)",
    "created_at": "2026-01-06T14:20:00.500Z",
    "updated_at": "2026-01-06T14:20:00.500Z"
  },
  "meta": {
    "timestamp": "2026-01-06T10:55:00.050Z",
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
    "timestamp": "2026-01-06T10:55:00.050Z",
    "request_id": "550e8423-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 6.2.3 Malfunction Event 생성

**Endpoint**: `POST /api/events/malfunctions`

> **PRD v2.2 변경**: `controller`, `sensor`, `type_device`, `group_event` → `device_id` 단일 FK로 통합
> **자동 생성**: `device_description`은 서버에서 자동 생성됨

**Request Body**:
```json
{
  "device_id": 104,
  "type_event": "Fault", //(EnumEventType)
  "reason": "FAULT_FENCE", //(EnumFaultType)
  "first_start": 3,
  "first_end": 3,
  "second_start": 0,
  "second_end": 0
}
```

**Response Example** (201 Created):
```json
{
  "success": true,
  "message": "Malfunction event created successfully",
  "data": {
    "id": 2002,
    "type_event": "Fault", //(EnumEventType)
    "action_reported": "False", //(EnumTrueFalse)
    "reason": "FAULT_FENCE", //(EnumFaultType)
    "first_start": 3,
    "first_end": 3,
    "second_start": 0,
    "second_end": 0,
    "device": {
      "id": 104,
      "number_device": 4,
      "group_device": 1, // (Deprecated 예정, 레거시)
      "name_device": "Sensor-A-4",
      "type_device": "Multi",
      "version": "v1.5.0",
      "status": "ACTIVATED",
      "controller_id": 1,
      "device_groups": [
        {"id": 1, "name": "A구역 센서그룹", "description": "A구역 센서 장비 그룹", "device_count": 5}
      ]
    },
    "device_description": "[Multi] Sensor-A-4 (number: 4, id: 104)",
    "created_at": "2026-01-06T10:56:00.100Z",
    "updated_at": "2026-01-06T10:56:00.100Z"
  },
  "meta": {
    "timestamp": "2026-01-06T10:56:00.100Z",
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
  "type_event": "Fault", //(EnumEventType, optional)
  "reason": "FAULT_MULTI", //(EnumFaultType, optional)
  "first_start": 3, //(optional)
  "first_end": 3, //(optional)
  "second_start": 0, //(optional)
  "second_end": 0 //(optional)
}
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Malfunction event updated successfully",
  "data": {
    "id": 2002,
    "type_event": "Fault", //(EnumEventType)
    "action_reported": "False", //(EnumTrueFalse)
    "reason": "FAULT_MULTI", //(EnumFaultType)
    "first_start": 3,
    "first_end": 3,
    "second_start": 0,
    "second_end": 0,
    "device": {
      "id": 104,
      "number_device": 4,
      "group_device": 1, // (Deprecated 예정, 레거시)
      "name_device": "Sensor-A-4",
      "type_device": "Multi",
      "version": "v1.5.0",
      "status": "ACTIVATED",
      "controller_id": 1,
      "device_groups": [
        {"id": 1, "name": "A구역 센서그룹", "description": "A구역 센서 장비 그룹", "device_count": 5}
      ]
    },
    "device_description": "[Multi] Sensor-A-4 (number: 4, id: 104)",
    "created_at": "2026-01-06T10:56:00.100Z",
    "updated_at": "2026-01-06T10:57:00.150Z"
  },
  "meta": {
    "timestamp": "2026-01-06T10:57:00.150Z",
    "request_id": "550e8425-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 6.2.5 Malfunction Event 수정 (전체)

**Endpoint**: `PUT /api/events/malfunctions/{id}`

> **PRD v2.2 변경**: `controller`, `sensor`, `type_device`, `group_event` → `device_id` 단일 FK로 통합

**Request Body** (전체 업데이트):
```json
{
  "device_id": 104,
  "type_event": "Fault", //(EnumEventType)
  "action_reported": "True", //(EnumTrueFalse)
  "reason": "FAULT_ETC", //(EnumFaultType)
  "first_start": 2,
  "first_end": 2,
  "second_start": 5,
  "second_end": 5
}
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Malfunction event updated successfully",
  "data": {
    "id": 2002,
    "type_event": "Fault", //(EnumEventType)
    "action_reported": "True", //(EnumTrueFalse)
    "reason": "FAULT_ETC", //(EnumFaultType)
    "first_start": 2,
    "first_end": 2,
    "second_start": 5,
    "second_end": 5,
    "device": {
      "id": 104,
      "number_device": 4,
      "group_device": 1, // (Deprecated 예정, 레거시)
      "name_device": "Sensor-A-4",
      "type_device": "Multi",
      "version": "v1.5.0",
      "status": "ACTIVATED",
      "controller_id": 1,
      "device_groups": [
        {"id": 1, "name": "A구역 센서그룹", "description": "A구역 센서 장비 그룹", "device_count": 5}
      ]
    },
    "device_description": "[Multi] Sensor-A-4 (number: 4, id: 104)",
    "created_at": "2026-01-06T10:56:00.100Z",
    "updated_at": "2026-01-06T10:58:00.200Z"
  },
  "meta": {
    "timestamp": "2026-01-06T10:58:00.200Z",
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

> **PRD v1.3**: `from_event` 내부는 현재 Malfunction Event Response 포맷을 따름
> - `device` nested 포함 (Device 삭제 시 null)
> - `device_description` 포함
> - 레거시 필드 (`group_event`, `controller`, `sensor`, `type_device`, `sequence`, `device_id`) 제거됨

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
      "type_event": "Fault",
      "action_reported": "True",
      "reason": "FAULT_CONTROLLER",
      "first_start": 100,
      "first_end": 200,
      "second_start": 300,
      "second_end": 400,
      "device": {
        "id": 2,
        "number_device": 2,
        "group_device": 1,
        "name_device": "Controller-B",
        "type_device": "Controller",
        "status": "Error",
        "version": "v2.0.0",
        "ip_address": "192.168.1.102",
        "ip_port": 8080,
        "device_groups": [
          { "id": 2, "name": "B구역 컨트롤러 그룹" }
        ]
      },
      "device_description": "[Controller] Controller-B (number: 2, id: 2)",
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
- `device_id` (int, optional): 장치 ID 필터 (PRD v2.2)
- `page` (int, optional): 페이지 번호
- `limit` (int, optional): 페이지당 항목 수

> **PRD v2.2 변경**: `controller`, `sensor`, `type_device`, `group_event` → `device_id` 단일 FK로 통합
> **PRD v1.3 변경**: Response에서 `device_id`, `sequence` 필드 제거 (device.id에 포함, sequence는 Request 전용)

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "10 connection events retrieved",
  "data": [
    {
      "id": 3001,
      "type_event": "Connection",
      "device": {
        "id": 101,
        "number_device": 1,
        "group_device": 1, // (Deprecated 예정, 레거시)
        "name_device": "Sensor-A-1",
        "type_device": "Fence",
        "version": "v1.5.0",
        "status": "ACTIVATED",
        "controller_id": 1,
        "device_groups": [
          {"id": 1, "name": "A구역 센서그룹", "description": "A구역 센서 장비 그룹", "device_count": 5}
        ]
      },
      "device_description": "[Fence] Sensor-A-1 (number: 1, id: 101)",
      "created_at": "2026-01-06T09:00:00.100Z",
      "updated_at": "2026-01-06T09:00:00.100Z"
    },
    {
      "id": 3002,
      "type_event": "Connection",
      "device": {
        "id": 102,
        "number_device": 2,
        "group_device": 1, // (Deprecated 예정, 레거시)
        "name_device": "Sensor-A-2",
        "type_device": "Multi",
        "version": "v1.5.0",
        "status": "ACTIVATED",
        "controller_id": 1,
        "device_groups": [
          {"id": 1, "name": "A구역 센서그룹", "description": "A구역 센서 장비 그룹", "device_count": 5}
        ]
      },
      "device_description": "[Multi] Sensor-A-2 (number: 2, id: 102)",
      "created_at": "2026-01-06T09:05:00.100Z",
      "updated_at": "2026-01-06T09:05:00.100Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 10,
    "total_pages": 1
  },
  "meta": {
    "timestamp": "2026-01-06T11:00:00.250Z",
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
    "type_event": "Connection", //(EnumEventType)
    "device": {
      "id": 101,
      "number_device": 1,
      "group_device": 1, // (Deprecated 예정, 레거시)
      "name_device": "Sensor-A-1",
      "type_device": "Fence",
      "version": "v1.5.0",
      "status": "ACTIVATED",
      "controller_id": 1,
      "device_groups": [
        {"id": 1, "name": "A구역 센서그룹", "description": "A구역 센서 장비 그룹", "device_count": 5}
      ]
    },
    "device_description": "[Fence] Sensor-A-1 (number: 1, id: 101)",
    "created_at": "2026-01-06T09:00:00.100Z",
    "updated_at": "2026-01-06T09:00:00.100Z"
  },
  "meta": {
    "timestamp": "2026-01-06T11:01:00.050Z",
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
    "timestamp": "2026-01-06T11:01:00.050Z",
    "request_id": "550e8429-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 6.3.3 Connection Event 생성

**Endpoint**: `POST /api/events/connections`

> **PRD v2.2 변경**: `controller`, `sensor`, `type_device`, `group_event` → `device_id` 단일 FK로 통합
> **자동 생성**: `device_description`은 서버에서 자동 생성됨

**Request Body**:
```json
{
  "device_id": 103,
  "type_event": "Connection" //(EnumEventType)
}
```

**Response Example** (201 Created):
```json
{
  "success": true,
  "message": "Connection event created successfully",
  "data": {
    "id": 3003,
    "type_event": "Connection", //(EnumEventType)
    "device": {
      "id": 103,
      "number_device": 3,
      "group_device": 1, // (Deprecated 예정, 레거시)
      "name_device": "Sensor-A-3",
      "type_device": "Underground",
      "version": "v1.5.0",
      "status": "ACTIVATED",
      "controller_id": 1,
      "device_groups": [
        {"id": 1, "name": "A구역 센서그룹", "description": "A구역 센서 장비 그룹", "device_count": 5}
      ]
    },
    "device_description": "[Underground] Sensor-A-3 (number: 3, id: 103)",
    "created_at": "2026-01-06T11:02:00.100Z",
    "updated_at": "2026-01-06T11:02:00.100Z"
  },
  "meta": {
    "timestamp": "2026-01-06T11:02:00.100Z",
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
  "type_event": "Connection" //(EnumEventType)
}
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Connection event updated successfully",
  "data": {
    "id": 3003,
    "type_event": "Connection", //(EnumEventType)
    "device": {
      "id": 103,
      "number_device": 3,
      "group_device": 1, // (Deprecated 예정, 레거시)
      "name_device": "Sensor-A-3",
      "type_device": "Underground",
      "version": "v1.5.0",
      "status": "ACTIVATED",
      "controller_id": 1,
      "device_groups": [
        {"id": 1, "name": "A구역 센서그룹", "description": "A구역 센서 장비 그룹", "device_count": 5}
      ]
    },
    "device_description": "[Underground] Sensor-A-3 (number: 3, id: 103)",
    "created_at": "2026-01-06T11:02:00.100Z",
    "updated_at": "2026-01-06T11:03:00.150Z"
  },
  "meta": {
    "timestamp": "2026-01-06T11:03:00.150Z",
    "request_id": "550e8431-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 6.3.5 Connection Event 수정 (전체)

**Endpoint**: `PUT /api/events/connections/{id}`

> **PRD v2.2 변경**: `controller`, `sensor`, `type_device`, `group_event` → `device_id` 단일 FK로 통합

**Request Body** (전체 업데이트):
```json
{
  "device_id": 104,
  "type_event": "Connection" //(EnumEventType)
}
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Connection event updated successfully",
  "data": {
    "id": 3003,
    "type_event": "Connection", //(EnumEventType)
    "device": {
      "id": 104,
      "number_device": 4,
      "group_device": 1, // (Deprecated 예정, 레거시)
      "name_device": "Sensor-A-4",
      "type_device": "PIR",
      "version": "v1.5.0",
      "status": "ACTIVATED",
      "controller_id": 1,
      "device_groups": [
        {"id": 1, "name": "A구역 센서그룹", "description": "A구역 센서 장비 그룹", "device_count": 5}
      ]
    },
    "device_description": "[PIR] Sensor-A-4 (number: 4, id: 104)",
    "created_at": "2026-01-06T11:02:00.100Z",
    "updated_at": "2026-01-06T11:04:00.200Z"
  },
  "meta": {
    "timestamp": "2026-01-06T11:04:00.200Z",
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
  "type_event": "Action",
  "content": "침입 탐지 확인 및 순찰 출동 요청",
  "user": "operator_kim",
  "from_event_id": 1001
}
```

> **PRD v1.5**: `from_type_event` 필드 제거됨. `from_event_id`만으로 원본 이벤트를 참조하며, polymorphic relationship을 통해 이벤트 타입이 자동으로 확인됩니다.

**성공 응답 예시** (201 Created):
```json
{
  "success": true,
  "message": "Action event created successfully",
  "data": {
    "id": 3001,
    "type_event": "Action",
    "content": "침입 탐지 확인 및 순찰 출동 요청",
    "user": "operator_kim",
    "from_event": {
      "id": 1001,
      "type_event": "Intrusion",
      "action_reported": "True",
      "result": "PIR_SENSOR",
      "device": {
        "id": 2,
        "number_device": 101,
        "group_device": 999,
        "name_device": "Test Sensor",
        "type_device": "Fence",
        "status": "ACTIVATED",
        "version": "1.0.0",
        "ip_address": null,
        "ip_port": null,
        "controller_id": 1,
        "rtsp_uri": null,
        "rtsp_port": null,
        "mode": null,
        "category": null,
        "is_record": null,
        "device_groups": []
      },
      "device_description": "[Fence] Test Sensor (number: 101, id: 2)",
      "created_at": "2025-01-14T11:50:23.736735",
      "updated_at": "2025-01-14T11:50:25.123456"
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
        "type_event": "Intrusion", //(EnumEventType)
        "action_reported": "True", //(EnumTrueFalse)
        "result": "THERMAL_SENSOR", //(EnumDetectionType)
        "device": {
          "id": 102,
          "number_device": 2,
          "group_device": 1,
          "name_device": "Sensor-A-2",
          "type_device": "Fence",
          "version": "v1.5.0",
          "status": "ACTIVATED",
          "controller_id": 1,
          "device_groups": []
        },
        "device_description": "[Fence] Sensor-A-2 (number: 2, id: 102)",
        "created_at": "2025-01-10T10:15:00.100Z",
        "updated_at": "2025-01-10T10:16:00.100Z"
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
        "type_event": "Fault", //(EnumEventType)
        "action_reported": "True", //(EnumTrueFalse)
        "reason": "FAULT_ETC", //(EnumFaultType)
        "first_start": 2,
        "first_end": 2,
        "second_start": 5,
        "second_end": 5,
        "device": {
          "id": 104,
          "number_device": 4,
          "group_device": 1,
          "name_device": "Sensor-A-4",
          "type_device": "Multi",
          "version": "v1.5.0",
          "status": "ACTIVATED",
          "controller_id": 1,
          "device_groups": []
        },
        "device_description": "[Multi] Sensor-A-4 (number: 4, id: 104)",
        "created_at": "2025-01-10T10:18:00.150Z",
        "updated_at": "2025-01-10T10:20:00.150Z"
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
      "type_event": "Intrusion", //(EnumEventType)
      "action_reported": "True", //(EnumTrueFalse)
      "result": "THERMAL_SENSOR", //(EnumDetectionType)
      "device": {
        "id": 102,
        "number_device": 2,
        "group_device": 1,
        "name_device": "Sensor-A-2",
        "type_device": "Fence",
        "version": "v1.5.0",
        "status": "ACTIVATED",
        "controller_id": 1,
        "device_groups": []
      },
      "device_description": "[Fence] Sensor-A-2 (number: 2, id: 102)",
      "created_at": "2025-01-10T10:15:00.100Z",
      "updated_at": "2025-01-10T10:16:00.100Z"
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
      "type_event": "Intrusion", //(EnumEventType)
      "action_reported": "True", //(EnumTrueFalse)
      "result": "THERMAL_SENSOR", //(EnumDetectionType)
      "device": {
        "id": 102,
        "number_device": 2,
        "group_device": 1,
        "name_device": "Sensor-A-2",
        "type_device": "Fence",
        "version": "v1.5.0",
        "status": "ACTIVATED",
        "controller_id": 1,
        "device_groups": []
      },
      "device_description": "[Fence] Sensor-A-2 (number: 2, id: 102)",
      "created_at": "2025-01-10T10:15:00.100Z",
      "updated_at": "2025-01-10T10:16:00.100Z"
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
  "user": "operator_park"
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
      "type_event": "Intrusion", //(EnumEventType)
      "action_reported": "True", //(EnumTrueFalse)
      "result": "THERMAL_SENSOR", //(EnumDetectionType)
      "device": {
        "id": 102,
        "number_device": 2,
        "group_device": 1,
        "name_device": "Sensor-A-2",
        "type_device": "Fence",
        "version": "v1.5.0",
        "status": "ACTIVATED",
        "controller_id": 1,
        "device_groups": []
      },
      "device_description": "[Fence] Sensor-A-2 (number: 2, id: 102)",
      "created_at": "2025-01-10T10:15:00.100Z",
      "updated_at": "2025-01-10T10:16:00.100Z"
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

> **v2.3 변경사항 (PRD v2.1)**: `group_event` (VARCHAR) → `device_group_id` (FK) 변경
> - EventMapping이 DeviceGroup과 FK 관계로 연결됨
> - Device → DeviceGroup → EventMapping → CameraPreset 흐름으로 이벤트-카메라 연동 가능

#### 7.2.1 EventMapping 목록 조회

**Endpoint**: `GET /api/integrations/event-mappings`

**Query Parameters**:
- `name_event` (string, optional): 이벤트 이름 필터
- `device_group_id` (int, optional): DeviceGroup ID 필터 **(v2.3 변경: group_event → device_group_id)**
- `category_event` (string, optional): 이벤트 카테고리 필터
- `status` (boolean, optional): 활성화 상태 필터
- `page` (int, optional, default=1): 페이지 번호
- `limit` (int, optional, default=20): 페이지당 항목 수

**Request Example**:
```http
GET /api/integrations/event-mappings?device_group_id=1&status=true&page=1&limit=20 HTTP/1.1
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
      "device_group_id": 1,
      "category_event": "detection",
      "description": "센서 침입 탐지 이벤트 매핑",
      "status": true,
      "created_at": "2026-01-06T09:00:00.000Z",
      "updated_at": "2026-01-06T09:00:00.000Z"
    },
    {
      "id": 2,
      "name_event": "장애 발생",
      "device_group_id": 2,
      "category_event": "malfunction",
      "description": "센서 장애 발생 이벤트 매핑",
      "status": true,
      "created_at": "2026-01-06T09:10:00.000Z",
      "updated_at": "2026-01-06T09:10:00.000Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 2,
    "total_pages": 1
  },
  "meta": {
    "timestamp": "2026-01-06T11:00:00.250Z",
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
    "device_group_id": 1,
    "category_event": "detection",
    "description": "센서 침입 탐지 이벤트 매핑",
    "status": true,
    "created_at": "2026-01-06T09:00:00.000Z",
    "updated_at": "2026-01-06T09:00:00.000Z"
  },
  "meta": {
    "timestamp": "2026-01-06T11:01:00.050Z",
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
  "device_group_id": 3,
  "category_event": "connection",
  "description": "센서 연결 상태 변경 이벤트 매핑",
  "status": true
}
```

> **v2.3 변경**: `group_event` (VARCHAR) → `device_group_id` (INT, FK) 변경. DeviceGroup.id를 참조합니다.

**Response Example** (201 Created):
```json
{
  "success": true,
  "message": "Event mapping created successfully",
  "data": {
    "id": 3,
    "name_event": "연결 상태 변경",
    "device_group_id": 3,
    "category_event": "connection",
    "description": "센서 연결 상태 변경 이벤트 매핑",
    "status": true,
    "created_at": "2026-01-06T11:15:00.000Z",
    "updated_at": "2026-01-06T11:15:00.000Z"
  },
  "meta": {
    "timestamp": "2026-01-06T11:15:00.100Z",
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
  "device_group_id": 2,
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
    "device_group_id": 2,
    "category_event": "detection",
    "description": "센서 침입 탐지 이벤트 - 수정된 설명",
    "status": false,
    "created_at": "2026-01-06T09:00:00.000Z",
    "updated_at": "2026-01-06T11:20:00.000Z"
  },
  "meta": {
    "timestamp": "2026-01-06T11:20:00.150Z",
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
  "device_group_id": 1,
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
    "device_group_id": 1,
    "category_event": "detection",
    "description": "전체 업데이트된 설명",
    "status": true,
    "created_at": "2026-01-06T09:00:00.000Z",
    "updated_at": "2026-01-06T11:25:00.000Z"
  },
  "meta": {
    "timestamp": "2026-01-06T11:25:00.200Z",
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

## 8. Server Monitoring API 설계

### 8.1 개요

서버 모니터링 API는 GOP 시스템을 구성하는 다양한 서버들의 상태를 관리하고 모니터링하기 위한 API입니다.

**주요 기능**:
- 서버 카테고리 관리 (9개 기본 카테고리)
- 서버 인스턴스 CRUD
- 대시보드용 서버 상태 요약

**리소스 구조**:
```
/api/servers/categories      - 서버 카테고리 (VMS, AI_ANALYSIS 등)
/api/servers/categories/{id} - 특정 카테고리
/api/servers                 - 서버 인스턴스 목록
/api/servers/{id}            - 특정 서버 인스턴스
/api/servers/summary         - 대시보드 요약
```

### 8.2 Server Category API

서버를 유형별로 분류하는 카테고리를 관리합니다.

#### 8.2.1 카테고리 목록 조회

```http
GET /api/servers/categories
```

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| page | integer | N | 페이지 번호 (기본값: 1) |
| limit | integer | N | 페이지당 항목 수 (기본값: 20, 최대: 100) |

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Server categories retrieved successfully",
  "data": [
    {
      "id": 1,
      "name": "VMS 서버",
      "type_server": "VMS",
      "description": "Video Management System",
      "sort_order": 1,
      "created_at": "2025-12-29T06:46:01.050121",
      "updated_at": "2025-12-29T06:46:01.050121"
    },
    {
      "id": 2,
      "name": "지능형영상 분석 서버",
      "type_server": "AI_ANALYSIS",
      "description": "AI 기반 영상 분석 서버",
      "sort_order": 2,
      "created_at": "2025-12-29T06:46:01.058259",
      "updated_at": "2025-12-29T06:46:01.058259"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 9,
    "total_pages": 1
  }
}
```

#### 8.2.2 카테고리 상세 조회 (서버 목록 포함)

```http
GET /api/servers/categories/{category_id}
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| category_id | integer | Y | 카테고리 ID |

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Server category retrieved successfully",
  "data": {
    "id": 1,
    "name": "VMS 서버",
    "type_server": "VMS",
    "description": "Video Management System",
    "sort_order": 1,
    "created_at": "2025-12-29T06:46:01.050121",
    "updated_at": "2025-12-29T06:46:01.050121",
    "servers": [
      {
        "id": 1,
        "category_id": 1,
        "name": "VMS-ab1120",
        "status": "NORMAL",
        "ip_address": "192.168.1.10",
        "port": 8080,
        "hostname": "vms-server-01",
        "cpu_usage": 45.0,
        "ram_usage": 62.0,
        "disk_usage": 78.0,
        "network_throughput": "125MB/s",
        "created_at": "2025-12-29T06:46:01.150000",
        "updated_at": "2025-12-29T06:46:01.150000"
      }
    ]
  }
}
```

#### 8.2.3 카테고리 생성

```http
POST /api/servers/categories
```

**Request Body**:
```json
{
  "name": "새로운 서버 카테고리",
  "type_server": "ETC",
  "description": "카테고리 설명",
  "sort_order": 10
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| name | string | Y | 카테고리명 |
| type_server | EnumServerType | Y | 서버 유형 (Enum 값) |
| description | string | N | 설명 |
| sort_order | integer | N | 정렬 순서 (기본값: 0) |

**Response (201 Created)**:
```json
{
  "success": true,
  "message": "Server category created successfully",
  "data": {
    "id": 10,
    "name": "새로운 서버 카테고리",
    "type_server": "ETC",
    "description": "카테고리 설명",
    "sort_order": 10,
    "created_at": "2025-12-29T07:00:00.000000",
    "updated_at": "2025-12-29T07:00:00.000000"
  }
}
```

**Error Response (409 Conflict)** - 중복 type_server:
```json
{
  "success": false,
  "error": {
    "code": "DUPLICATE_TYPE_SERVER",
    "message": "Server category with type_server 'VMS' already exists"
  }
}
```

#### 8.2.4 카테고리 수정 (부분)

```http
PATCH /api/servers/categories/{category_id}
```

**Request Body** (모든 필드 선택적):
```json
{
  "description": "수정된 설명",
  "sort_order": 5
}
```

**Response (200 OK)**: 수정된 카테고리 데이터 반환

#### 8.2.5 카테고리 수정 (전체)

```http
PUT /api/servers/categories/{category_id}
```

**Request Body** (모든 필드 필수):
```json
{
  "name": "수정된 카테고리명",
  "type_server": "VMS",
  "description": "수정된 설명",
  "sort_order": 1
}
```

#### 8.2.6 카테고리 삭제

```http
DELETE /api/servers/categories/{category_id}
```

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Server category deleted successfully",
  "data": {
    "id": 10
  }
}
```

> **주의**: 카테고리 삭제 시 해당 카테고리에 속한 모든 서버도 함께 삭제됩니다 (Cascade Delete).

---

### 8.3 Server Instance API

개별 서버 인스턴스를 관리합니다.

#### 8.3.1 서버 목록 조회

```http
GET /api/servers
```

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| page | integer | N | 페이지 번호 (기본값: 1) |
| limit | integer | N | 페이지당 항목 수 (기본값: 20, 최대: 100) |
| category_id | integer | N | 카테고리 ID 필터 |
| status | string | N | 상태 필터 (NORMAL, WARNING, ERROR) |

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Servers retrieved successfully",
  "data": [
    {
      "id": 1,
      "category_id": 1,
      "name": "VMS-ab1120",
      "status": "NORMAL",
      "ip_address": "192.168.1.10",
      "port": 8080,
      "hostname": "vms-server-01",
      "cpu_usage": 45.0,
      "ram_usage": 62.0,
      "disk_usage": 78.0,
      "network_throughput": "125MB/s",
      "created_at": "2025-12-29T06:46:01.150000",
      "updated_at": "2025-12-29T06:46:01.150000"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 9,
    "total_pages": 1
  }
}
```

#### 8.3.2 서버 상세 조회

```http
GET /api/servers/{server_id}
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| server_id | integer | Y | 서버 ID |

**Response (200 OK)**: 서버 상세 정보 반환

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Server with id 999 not found"
  }
}
```

#### 8.3.3 서버 생성

```http
POST /api/servers
```

**Request Body**:
```json
{
  "category_id": 1,
  "name": "VMS-ab1122",
  "status": "NORMAL",
  "ip_address": "192.168.1.12",
  "port": 8080,
  "hostname": "vms-server-03",
  "cpu_usage": 35.0,
  "ram_usage": 48.0,
  "disk_usage": 55.0,
  "network_throughput": "100MB/s"
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| category_id | integer | Y | 카테고리 ID |
| name | string | Y | 서버 이름 |
| status | EnumServerStatus | N | 상태 (기본값: NORMAL) |
| ip_address | string | N | IP 주소 |
| port | integer | N | 포트 번호 |
| hostname | string | N | 호스트명 |
| cpu_usage | float | N | CPU 사용률 (%) |
| ram_usage | float | N | RAM 사용률 (%) |
| disk_usage | float | N | 디스크 사용률 (%) |
| network_throughput | string | N | 네트워크 처리량 |

**Response (201 Created)**: 생성된 서버 데이터 반환

#### 8.3.4 서버 수정 (부분)

```http
PATCH /api/servers/{server_id}
```

**Request Body** (모든 필드 선택적):
```json
{
  "status": "WARNING",
  "cpu_usage": 85.0,
  "ram_usage": 78.0
}
```

> **사용 사례**: 서버 메트릭 주기적 업데이트에 사용

**Response (200 OK)**: 수정된 서버 데이터 반환

#### 8.3.5 서버 수정 (전체)

```http
PUT /api/servers/{server_id}
```

모든 필드를 포함한 전체 데이터로 교체합니다.

#### 8.3.6 서버 삭제

```http
DELETE /api/servers/{server_id}
```

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Server deleted successfully",
  "data": {
    "id": 1
  }
}
```

---

### 8.4 Dashboard Summary API

대시보드에서 사용할 서버 상태 요약 정보를 제공합니다.

#### 8.4.1 서버 요약 조회

```http
GET /api/servers/summary
```

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Server summary retrieved successfully",
  "data": [
    {
      "id": 1,
      "name": "VMS 서버",
      "type_server": "VMS",
      "total": 2,
      "normal": 2,
      "warning": 0,
      "error": 0,
      "servers": [
        {
          "id": 1,
          "category_id": 1,
          "name": "VMS-ab1120",
          "status": "NORMAL",
          "ip_address": "192.168.1.10",
          "port": 8080,
          "hostname": "vms-server-01",
          "cpu_usage": 45.0,
          "ram_usage": 62.0,
          "disk_usage": 78.0,
          "network_throughput": "125MB/s",
          "created_at": "2025-12-29T06:46:01.150000",
          "updated_at": "2025-12-29T06:46:01.150000"
        }
      ]
    },
    {
      "id": 2,
      "name": "지능형영상 분석 서버",
      "type_server": "AI_ANALYSIS",
      "total": 3,
      "normal": 2,
      "warning": 1,
      "error": 0,
      "servers": []
    },
    {
      "id": 5,
      "name": "브로커서버",
      "type_server": "BROKER",
      "total": 2,
      "normal": 1,
      "warning": 0,
      "error": 1,
      "servers": []
    }
  ]
}
```

**응답 필드 설명**:
| 필드 | 타입 | 설명 |
|------|------|------|
| id | integer | 카테고리 ID |
| name | string | 카테고리명 |
| type_server | string | 서버 유형 (EnumServerType) |
| total | integer | 총 서버 수 |
| normal | integer | 정상 상태 서버 수 |
| warning | integer | 경고 상태 서버 수 |
| error | integer | 에러 상태 서버 수 |
| servers | array | 해당 카테고리의 서버 목록 |

---

### 8.5 기본 데이터 (Seed)

시스템 초기화 시 다음 9개의 기본 서버 카테고리가 자동 생성됩니다:

| sort_order | name | type_server | description |
|------------|------|-------------|-------------|
| 1 | VMS 서버 | VMS | Video Management System |
| 2 | 지능형영상 분석 서버 | AI_ANALYSIS | AI 기반 영상 분석 서버 |
| 3 | 스트리밍 서버 | STREAMING | 실시간 스트리밍 서버 |
| 4 | 트랜스코더 서버 | TRANSCODER | 영상 변환 서버 |
| 5 | 브로커서버 | BROKER | 메시지 브로커 서버 |
| 6 | DB API 서버 | DB_API | 데이터베이스 API 서버 |
| 7 | NVR API 서버 | NVR_API | Network Video Recorder API 서버 |
| 8 | SPEAKER API 서버 | SPEAKER_API | 스피커 제어 API 서버 |
| 9 | 함체관리 API 서버 | ENCLOSURE_API | 함체 관리 API 서버 |

---

## 9. 에러 처리

### 9.1 에러 응답 형식

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

### 9.2 에러 코드 정의

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

### 9.3 에러 응답 예제

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

## 10. 부록

### 10.1 전체 Endpoint 목록

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
- `PATCH /api/devices/cameras/{id}` - 수정 (부분)
- `PUT /api/devices/cameras/{id}` - 수정 (전체)
- `DELETE /api/devices/cameras/{id}` - 삭제

**DeviceGroups** (v2.0 신규):
- `GET /api/devices/groups` - 그룹 목록 조회
- `POST /api/devices/groups` - 그룹 생성
- `GET /api/devices/groups/{id}` - 그룹 상세 조회 (폴리모픽 디바이스 목록 포함)
- `PATCH /api/devices/groups/{id}` - 그룹 수정 (부분)
- `PUT /api/devices/groups/{id}` - 그룹 수정 (전체)
- `DELETE /api/devices/groups/{id}` - 그룹 삭제 (Cascade)
- `POST /api/devices/groups/{id}/devices` - 디바이스 할당
- `DELETE /api/devices/groups/{group_id}/devices/{device_id}` - 디바이스 제거

**Camera Presets** (v2.1 신규):
- `GET /api/devices/cameras/{camera_id}/presets` - 프리셋 목록 조회 (`include_rois` 지원)
- `POST /api/devices/cameras/{camera_id}/presets` - 프리셋 생성
- `GET /api/devices/cameras/{camera_id}/presets/{preset_id}` - 프리셋 상세 조회 (ROI/Points 포함)
- `PATCH /api/devices/cameras/{camera_id}/presets/{preset_id}` - 프리셋 수정 (부분)
- `PUT /api/devices/cameras/{camera_id}/presets/{preset_id}` - 프리셋 수정 (전체)
- `DELETE /api/devices/cameras/{camera_id}/presets/{preset_id}` - 프리셋 삭제 (Cascade)

**ROIs** (v2.1 신규):
- `GET /api/presets/{preset_id}/rois` - ROI 목록 조회 (`include_points` 지원)
- `POST /api/presets/{preset_id}/rois` - ROI 생성 (Points 포함 가능)
- `GET /api/presets/{preset_id}/rois/{roi_id}` - ROI 상세 조회 (Points 포함)
- `PATCH /api/presets/{preset_id}/rois/{roi_id}` - ROI 수정 (부분)
- `PUT /api/presets/{preset_id}/rois/{roi_id}` - ROI 수정 (전체)
- `DELETE /api/presets/{preset_id}/rois/{roi_id}` - ROI 삭제 (Cascade)

**XyPoints** (v2.1 신규):
- `GET /api/rois/{roi_id}/points` - 포인트 목록 조회
- `POST /api/rois/{roi_id}/points` - 포인트 생성
- `PUT /api/rois/{roi_id}/points` - 포인트 일괄 수정 (전체 교체)
- `DELETE /api/rois/{roi_id}/points/{point_id}` - 포인트 삭제

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

#### Server Monitoring Endpoints

**Server Categories**:
- `GET /api/servers/categories` - 카테고리 목록 조회
- `POST /api/servers/categories` - 카테고리 생성
- `GET /api/servers/categories/{id}` - 카테고리 상세 조회 (서버 목록 포함)
- `PATCH /api/servers/categories/{id}` - 카테고리 수정 (부분)
- `PUT /api/servers/categories/{id}` - 카테고리 수정 (전체)
- `DELETE /api/servers/categories/{id}` - 카테고리 삭제 (Cascade)

**Servers**:
- `GET /api/servers` - 서버 목록 조회
- `POST /api/servers` - 서버 생성
- `GET /api/servers/{id}` - 서버 상세 조회
- `PATCH /api/servers/{id}` - 서버 수정 (부분)
- `PUT /api/servers/{id}` - 서버 수정 (전체)
- `DELETE /api/servers/{id}` - 서버 삭제
- `GET /api/servers/summary` - 대시보드 요약 조회

### 10.2 Event-Device 리팩토링 변경사항 (v2.3)

> **PRD 문서**: `docs/PRD_Event_ActionEvent_Refactoring.md` v2.1, `docs/PRD_Event_Api_Refactoring.md` v1.3

#### 10.2.1 API Request 변경

| Event Type | Before (v2.1 이전) | After (v2.2) | After (v2.3) |
|------------|-------------------|--------------|--------------|
| Detection | `controller`, `sensor`, `type_device`, `group_event` | `device_id`, `group_event` | `device_id` (group_event **제거**) |
| Malfunction | `controller`, `sensor`, `type_device`, `group_event` | `device_id`, `group_event` | `device_id` (group_event **제거**) |
| Connection | `controller`, `sensor`, `type_device`, `group_event` | `device_id`, `group_event` | `device_id` (group_event **제거**) |

> **v2.3 변경**: Event Request에서 `group_event` 필드 제거됨. DeviceGroup은 Device를 통해 조회.

**v2.3 Request 예시**:
```json
{
  "type_event": "Intrusion",
  "device_id": 101,
  "result": "PIR_SENSOR"
}
```

#### 10.2.2 API Response 변경

| 필드 | v2.2 | v2.3 | 설명 |
|------|------|------|------|
| `device` | ✅ | ✅ | Device nested 객체. Device 삭제 시 `null` |
| `device_description` | ✅ | ✅ | Device 정보 스냅샷. Device 삭제 후에도 유지 |
| `device_id` | ✅ | ❌ **제거** | `device.id`에 포함되어 중복 |
| `sequence` | ✅ | ❌ **제거** | Request 전용 필드, Response에 불필요 |
| `group_event` | ✅ | ❌ **제거** | DeviceGroup은 `device.device_groups[]`로 조회 |

> **v2.3 변경 (PRD v1.3)**: Response에서 `device_id`, `sequence`, `group_event` 필드 제거됨.

**v2.3 Response 예시 (Device 존재)**:
```json
{
  "id": 1001,
  "type_event": "Intrusion",
  "action_reported": "False",
  "result": "PIR_SENSOR",
  "device": {
    "id": 101,
    "number_device": 1,
    "group_device": 1, // (Deprecated 예정, 레거시)
    "name_device": "Sensor-A-1",
    "type_device": "Multi",
    "version": "v1.5.0",
    "status": "ACTIVATED",
    "controller_id": 1,
    "device_groups": [
      {"id": 1, "name": "A구역 센서그룹", "description": "A구역 센서 장비 그룹", "device_count": 5}
    ]
  },
  "device_description": "[Multi] Sensor-A-1 (number: 1, id: 101)",
  "created_at": "2026-01-06T10:15:23.100Z",
  "updated_at": "2026-01-06T10:15:23.100Z"
}
```

**v2.3 Response 예시 (Device 삭제됨)**:
```json
{
  "id": 1001,
  "type_event": "Intrusion",
  "action_reported": "False",
  "result": "PIR_SENSOR",
  "device": null,
  "device_description": "[Multi] Sensor-A-1 (number: 1, id: 101)",
  "created_at": "2026-01-06T10:15:23.100Z",
  "updated_at": "2026-01-06T10:15:23.100Z"
}
```

#### 10.2.3 DeviceNestedResponse 스키마

**폴리모픽 Device 응답** - Device 타입에 따라 다른 필드 포함:

| 필드 | 타입 | 공통/타입별 | 설명 |
|------|------|-------------|------|
| `id` | `int` | 공통 | Device ID (FK) |
| `number_device` | `int` | 공통 | 디바이스 번호 |
| `group_device` | `int` | 공통 | 디바이스 그룹 |
| `name_device` | `string` | 공통 | 디바이스 이름 |
| `type_device` | `string` | 공통 | 디바이스 타입 (EnumDeviceType) |
| `version` | `string` (nullable) | 공통 | 펌웨어 버전 |
| `status` | `string` | 공통 | 상태 (EnumDeviceStatus) |
| `ip_address` | `string` (nullable) | Controller, Camera | IP 주소 |
| `ip_port` | `int` (nullable) | Controller, Camera | 포트 번호 |
| `controller_id` | `int` (nullable) | Sensor | 연결된 Controller ID |
| `rtsp_uri` | `string` (nullable) | Camera | RTSP URI |
| `rtsp_port` | `int` (nullable) | Camera | RTSP 포트 |
| `mode` | `string` (nullable) | Camera | 카메라 모드 (EnumCameraMode) |
| `category` | `string` (nullable) | Camera | 카메라 카테고리 (EnumCameraType) |
| `is_record` | `boolean` (nullable) | Camera | 녹화 여부 |
| `device_groups` | `array` | 공통 | **v2.3 신규**: 소속 DeviceGroup 목록 (EventMapping 연동 필수) |

> **v2.3 추가 (PRD v1.2)**: `device_groups` 필드 추가. EventMapping.device_group_id와 매칭하여 카메라 프리셋 실행에 사용.

**device_groups 필드 예시**:
```json
{
  "device_groups": [
    {"id": 1, "name": "A구역 센서그룹", "description": "A구역 센서 장비 그룹", "device_count": 5},
    {"id": 3, "name": "북측 경계그룹", "description": "북측 경계 장비 그룹", "device_count": 8}
  ]
}
```

#### 10.2.4 Event 영속성 보장

> **핵심 원칙**: Event 데이터는 어떤 경우에도 삭제되지 않아야 한다.

| 시나리오 | device_id | device_description | device (Response) |
|----------|-----------|-------------------|-------------------|
| Event 생성 | `101` | `"[Multi] Sensor-A-1..."` | Nested Object |
| Device 조회 | `101` | `"[Multi] Sensor-A-1..."` | Nested Object |
| **Device 삭제 후** | `NULL` | `"[Multi] Sensor-A-1..."` | `null` |

- **FK 설정**: `ondelete="SET NULL"` (CASCADE 사용 금지!)
- **device_description**: Device 삭제 후에도 과거 Device 정보 참조 가능

#### 10.2.5 마이그레이션 스크립트

**위치**: `scripts/migrate_event_device_id.py`

**사용법**:
```bash
# Dry-run (변경 없이 미리보기)
python scripts/migrate_event_device_id.py --dry-run

# 실제 마이그레이션 실행
python scripts/migrate_event_device_id.py
```

**마이그레이션 단계**:
1. `device_id`, `device_description` 컬럼 추가 (nullable)
2. 기존 `controller`/`sensor`/`type_device` 기반 `device_id` 매핑
3. `device_description` 자동 생성
4. FK 제약 추가 (`ondelete="SET NULL"`)

---

### 10.3 EventMapping 리팩토링 변경사항 (v2.3)

> **PRD 문서**: `docs/PRD_Event_ActionEvent_Refactoring.md` v2.1

#### 10.3.1 EventMapping 테이블 변경

| 필드 | Before (v2.2 이전) | After (v2.3) | 설명 |
|------|-------------------|--------------|------|
| `group_event` | VARCHAR(100) | **제거됨** | 자유 문자열, DeviceGroup과 무관 |
| `device_group_id` | - | INTEGER FK **신규** | DeviceGroup.id 참조 (SET NULL on delete) |

#### 10.3.2 API 변경 요약

| API | Before | After |
|-----|--------|-------|
| GET (목록) | `?group_event=xxx` 필터 | `?device_group_id=1` 필터 |
| GET (단건) | `group_event` 필드 반환 | `device_group_id` 필드 반환 |
| POST | `group_event` 문자열 입력 | `device_group_id` 정수 입력 |
| PATCH | `group_event` 수정 가능 | `device_group_id` 수정 가능 |
| PUT | `group_event` 필수 | `device_group_id` 필수 |

#### 10.3.3 이벤트-카메라 연동 흐름

```
이벤트 발생 시 카메라 프리셋 연동 흐름 (v2.3):

1. DetectionEvent 발생 (device_id = 101)
2. Event Response에서 device.device_groups[] 확인
3. device_groups[].id → EventMapping.device_group_id 매칭
4. EventMapping에서 category_event + device_group_id로 조회
5. 매핑된 CameraEventMapping → CameraEventPreset 실행

┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Event Response │     │  EventMapping   │     │ CameraPreset    │
│  ─────────────  │     │  ─────────────  │     │ ─────────────   │
│  device: {      │────►│ device_group_id │────►│ 프리셋 실행      │
│    device_groups│     │ category_event  │     │                 │
│    [{id: 1}]   │     │                 │     │                 │
│  }              │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

#### 10.3.4 EventMapping FK 정책

| 관계 | 동작 | 정책 | 결과 |
|------|------|------|------|
| DeviceGroup → EventMapping | DeviceGroup 삭제 | `ON DELETE SET NULL` | EventMapping.device_group_id → NULL |

> **참고**: DeviceGroup이 삭제되어도 EventMapping 자체는 유지됨 (device_group_id만 NULL)

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| v2.3 | 2026-01-06 | **API 전면 리팩토링 및 Nested Response 규칙 적용**<br><br>**[1. Event API 변경]**<br>- **Request 필드 통합**: `controller`, `sensor`, `type_device`, `group_event` → `device_id` 단일 FK로 통합<br>- **Response 필드 제거**: `device_id` (중복), `sequence` (완전 제거), `group_event` (`device.device_groups[]`로 대체)<br>- **Response 필드 추가**: `device` (Polymorphic), `device_description` (스냅샷)<br>- **`action_reported` 자동 관리**: Create 시 항상 "False", ActionEvent 생성/삭제 시 시스템 자동 업데이트<br>- **DB 변경**: `events.sequence` 컬럼 `NOT NULL` → `NULL` 허용 (레거시 호환)<br><br>**[2. Device Polymorphic Response]**<br>- Event Response `device` 필드가 타입별 다른 스키마 반환:<br>  • Sensor → SensorNestedResponse (controller_id 포함)<br>  • Controller → ControllerNestedResponse (ip_address, ip_port 포함)<br>  • Camera → CameraNestedResponse (rtsp_uri, mode, category 등 포함)<br><br>**[3. ActionEvent API 변경]**<br>- **Request 필드 제거**: `from_type_event` 제거 - `from_event_id`만으로 원본 이벤트 참조<br>- **Request 필드명 변경**: `from_event` → `from_event_id`<br>- **Polymorphic Relationship**: `from_event_id`가 `events.id` FK를 참조하여 이벤트 타입 자동 확인<br><br>**[4. Nested Response 규칙 일관성 적용]**<br>- **규칙**: 주체 Entity만 `created_at`, `updated_at` 포함, Nested 객체는 제외<br>- **Device API**: `device_groups`, `sensors` nested 객체에서 timestamp 제거<br>- **Sensor API**: `controller` nested 객체에서 timestamp 제거, `include_controller` 파라미터 추가<br>- **Camera Preset API**: `rois`, `points` nested 객체에서 timestamp 제거<br>- **신규 스키마**: `ControllerNestedResponse`, `ROINestedResponse`, `ROIListNestedResponse`, `XyPointNestedResponse`<br><br>**[5. Device `number_device` unique 제약 해제]**<br>- **변경**: 동일한 장치 번호를 여러 디바이스에서 사용 가능<br>- **스키마**: `number_device` 설명에서 "(유니크)" 제거, 409 중복 에러 제거<br>- **확인**: DB 스키마와 모델 모두 이미 `unique=False` 상태<br><br>**[6. EventMapping API 변경]**<br>- `group_event` (VARCHAR) → `device_group_id` (INTEGER FK) 변경<br>- 쿼리 파라미터: `?group_event=xxx` → `?device_group_id=1`<br><br>**[7. 문서 업데이트]**<br>- 10.3 EventMapping 리팩토링 변경사항 추가<br>- Camera PATCH/PUT API: `is_record`, `hardware_spec`, `geolocation`, `group_ids` 필드 추가<br>- PRD 참조: v1.3, v1.5, v2.2, v2.7, v2.8, v2.9 |
| v2.2 | 2025-12-31 | **Event-Device 관계 리팩토링 (PRD v1.1)**<br>- **[변경] Event API Request**: `controller`, `sensor`, `type_device` 3개 필드 → `device_id` 단일 FK로 통합<br>- **[변경] Event API Response**: `device` nested 객체 추가 (Optional, Device 삭제 시 null)<br>- **[신규] `device_description` 필드**: Device 정보 스냅샷 자동 생성 (형식: `[{type_device}] {name_device} (number: {number_device}, id: {id})`)<br>- **[중요] Event 영속성 보장**: Device 삭제 시 Event.device_id → NULL (CASCADE 금지, SET NULL 사용)<br>- **[중요] device_description 유지**: Device 삭제 후에도 device_description은 보존되어 과거 Device 정보 참조 가능<br>- Detection/Malfunction/Connection Event 모두 동일한 패턴 적용<br>- Action Event의 `from_event` 내에도 `device`, `device_description` 포함<br>- 마이그레이션 스크립트 추가: `scripts/migrate_event_device_id.py`<br>- PRD 문서: `docs/PRD_Event_Device_Refactoring.md` v1.1 참조 |
| v2.1 | 2025-12-31 | **Camera Preset, ROI, XyPoint API 추가**<br>- **[신규] 5.5 Camera Preset API**: PTZ 카메라 프리셋 CRUD API 추가<br>- **[신규] 5.6 ROI API**: Region of Interest CRUD API 추가 (`include_points` 파라미터 지원)<br>- **[신규] 5.7 XyPoint API**: ROI 다각형 꼭지점 좌표 CRUD API 추가<br>- 계층 구조: Camera → CameraPreset → ROI → XyPoint (1:N:N:N)<br>- CameraPreset 목록 조회 시 `include_rois` 파라미터로 ROI 정보 포함 가능<br>- ROI 목록 조회 시 `include_points` 파라미터로 Points 정보 포함 가능<br>- CameraPreset 상세 조회 시 ROI 및 Points 전체 중첩 구조 반환<br>- XyPoint 일괄 수정(PUT) 시 기존 포인트 전체 교체 방식<br>- CASCADE DELETE 지원: Camera 삭제 시 Preset → ROI → XyPoint 순차 삭제<br>- 부록 10.1 Endpoint 목록에 Camera Presets, ROIs, XyPoints 섹션 추가 |
| v2.0 | 2025-12-31 | **Device Group N:N 관계 및 폴리모픽 응답 지원**<br>- **[신규] EnumDeviceCategory**: 디바이스 카테고리 Enum 추가 (controller, sensor, camera) - Polymorphic Discriminator<br>- **[신규] 5.4 DeviceGroup API**: 디바이스 그룹 CRUD 및 디바이스 할당/제거 API 추가<br>- DeviceGroup 상세 조회 시 폴리모픽 디바이스 목록 반환 (Controller/Sensor/Camera 타입별 다른 필드)<br>- **Controller API 업데이트**: `device_groups` 배열 필드 추가 (응답), `group_ids` 배열 필드 추가 (요청), `group_id` 쿼리 파라미터 추가<br>- **Sensor API 업데이트**: `device_groups` 배열 필드 추가 (응답), `group_ids` 배열 필드 추가 (요청), `group_id` 쿼리 파라미터 추가<br>- **Camera API 업데이트**: `device_groups` 배열 필드 추가 (응답), `group_ids` 배열 필드 추가 (요청), `group_id` 쿼리 파라미터 추가, `is_record`, `hardware_spec`, `geolocation` 필드 추가<br>- Camera `hardware_spec`: 제조사, 모델명, 펌웨어, MAC주소, ONVIF버전 등 JSON 객체<br>- Camera `geolocation`: 위도, 경도, 고도, 설치위치 등 JSON 객체<br>- `version` 필드 nullable 변경 (PRD v1.2 반영) |
| v1.9 | 2025-12-29 | **Server Monitoring API 추가**<br>- 섹션 8 Server Monitoring API 설계 신규 추가<br>- `EnumServerType` (26종): VMS, NVR_API, STREAMING, AI_ANALYSIS 등 서버 유형 정의<br>- `EnumServerStatus` (3종): NORMAL, WARNING, ERROR 서버 상태 정의<br>- Server Category CRUD API: `GET/POST/PATCH/PUT/DELETE /api/servers/categories`<br>- Server Instance CRUD API: `GET/POST/PATCH/PUT/DELETE /api/servers`<br>- Dashboard Summary API: `GET /api/servers/summary` (카테고리별 상태 요약)<br>- 9개 기본 서버 카테고리 Seed 데이터 정의<br>- Category 삭제 시 하위 Server Cascade 삭제 지원 |
| v1.8 | 2025-11-29 | **Enum 타입 통합 및 정리**<br>- 모든 Enum 정의를 `app/utils/enums.py`로 통합 (Single Source of Truth)<br>- `app/models/event.py`, `app/models/device.py`에서 중복 Enum 정의 제거<br>- `EnumCameraType`에서 `FISHEYES`, `THERMAL` 제거 (사용하지 않음)<br>- `EnumTrueFalse`는 Python 키워드 충돌 방지를 위해 `False_`, `True_` 사용<br>- `EnumEventType`에서 `None_` 사용 (Python None 키워드 충돌 방지)<br>- `_missing_` 메서드로 "False"→`False_`, "True"→`True_`, "None"→`None_` 자동 매핑 |
| v1.7 | 2025-11-27 | **Phase 28: CameraEventPreset URL Schema Refactor**<br>- `CameraEventPreset.rtsp_uri` 단일 필드 → `urls` 객체로 변경<br>- `urls` 객체 구조: `{ "live": "rtsp://...", "record": "rtsp://..." }`<br>- DB 컬럼 변경: `rtsp_uri` → `url_live`, `url_record` 분리<br>- 모든 CameraEventMapping API 영향 (GET/POST/PUT/PATCH)<br>- Breaking Change: API Request/Response 구조 변경 |
| v1.6 | 2025-11-26 | **Enum 타입 업데이트**<br>- EnumEventType에 `Lowlight`, `DetectionMode`, `TrackingMode` 추가<br>- EnumCameraType에서 `FISHEYES`, `THERMAL` 제거<br>- Swagger UI 문서 개선: 모든 스키마 필드에 enum 허용값 설명 추가<br><br>**Phase 27: CameraEventMapping Enum Fix**<br>- `EnumGroupEvent` 삭제 (더 이상 사용하지 않음)<br>- `EnumCategoryEvent` 값 변경: `SENSOR_ONLY`, `SENSOR_WITH_CAMERA`, `SENSOR_WITH_AI_DETECT`, `AI_DETECT_ONLY`, `MOTION_DETECT`, `ETC`<br>- `CameraEventMapping.group_event`: Enum → Plain String(100)으로 변경<br>- `CameraEventMapping.category_event`: EnumCategoryEvent Enum 유지<br>- Router에서 group_event 유효성 검사 제거 (자유 텍스트 허용) |
| v1.5 | 2025-01-17 | **Phase 21: Event Timestamp 필드 리팩토링**<br>- 모든 Event 모델에서 `datetime` 필드 제거<br>- `created_at`, `updated_at` 필드만 유지 (자동 생성)<br>- Detection/Malfunction/Connection Event 모든 API에서 `datetime` 제거<br>- `created_at`에 index 추가하여 조회 성능 최적화<br>- Request Body에서 `datetime` 파라미터 제거 (자동 생성)<br>- Response Body에서 `datetime` 필드 제거 |
| v1.4 | 2025-01-14 | **Phase 20: Detection/Malfunction Event에서 Action Event 조회 API 추가**<br>- 섹션 6.1.7 추가: Detection Event의 Action Event 조회 API (`GET /api/events/detections/{event_id}/action`)<br>- 섹션 6.2.7 추가: Malfunction Event의 Action Event 조회 API (`GET /api/events/malfunctions/{event_id}/action`)<br>- 1:1 관계를 활용한 효율적인 ActionEvent 조회 기능 제공<br>- Nested source event 응답 구조 문서화 |
| v1.3 | 2025-01-14 | **Phase 17-19: Action Event 동작 로직 및 DELETE 응답 표준화**<br>- Event DELETE 응답 표준화: 모든 Event DELETE API에서 `data=null` 반환<br>- Action Event 생성 시 자동 동작 로직 설명 추가 (source event의 `action_reported` 자동 업데이트)<br>- Action Event 삭제 시 자동 복원 로직 설명 추가 (source event의 `action_reported` 자동 복원)<br>- Source Event 삭제 제약 조건 추가 (`action_reported="True"`인 경우 삭제 불가)<br>- 409 Conflict 응답 예시 추가 (Detection/Malfunction Event DELETE)<br>- 1:1 관계 제약 설명 추가 (1개 source event = 최대 1개 ActionEvent) <br>- 7.2 EventMapping API의 Error Response Json 포멧 수정 |
| v1.2 | 2025-11-13 | **Integration API 추가 및 ActionEvent 필드 표준화**<br>- Integration API 설계 추가 (EventMapping CRUD)<br>- ActionEvent 필드명 변경: `from_event_type` → `from_type_event`<br>- ActionEvent 타입 값 표준화: `detection/malfunction/connection` → `Intrusion/Fault/Connection` |
| v1.1 | 2025-11-12 | **초안 작성**<br>- 전체 API 설계 초안 작성<br>- Device API, Event API 기본 구조 정의 |

---

**문서 버전**: v2.3
**최종 업데이트**: 2026-01-06