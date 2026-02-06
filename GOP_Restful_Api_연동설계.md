# GOP RESTful API 연동 설계서

**작성일**: 2025-12-31  
**최종 수정일**: 2026-02-06  
**버전**: v3.6  
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
     - 5.3.7 [카메라 설정 조회](#537-카메라-설정-조회) *(v3.6 신규)*
     - 5.3.8 [카메라 설정 수정 (부분)](#538-카메라-설정-수정-부분) *(v3.6 신규)*
   - 5.4 [Speaker API](#54-speaker-api) *(v2.4 신규)*
   - 5.5 [Enclosure API](#55-enclosure-api) *(v2.4 신규)*
   - 5.6 [DeviceGroup API](#56-devicegroup-api)
   - 5.7 [Camera Preset API](#57-camera-preset-api) *(v2.1 신규)*
   - 5.8 [ROI API](#58-roi-api) *(v2.1 신규)*
   - 5.9 [XyPoint API](#59-xypoint-api) *(v2.1 신규)*
   - 5.10 [FileGroup API](#510-filegroup-api) *(v2.4 신규)*
   - 5.11 [Lamp API](#511-lamp-api) *(v3.4 신규)*
6. [Event API 설계](#6-event-api-설계)
   - 6.1 [Detection Event API](#61-detection-event-api)
   - 6.2 [Malfunction Event API](#62-malfunction-event-api)
   - 6.3 [Connection Event API](#63-connection-event-api)
   - 6.4 [Action Event API](#64-action-event-api)
7. [Integration API 설계](#7-integration-api-설계)
   - 7.1 [개요](#71-개요)
   - 7.2 [EventMapping API](#72-eventmapping-api)
   - 7.3 [Event Mapping Cameras API](#73-event-mapping-cameras-api) *(v2.4 신규)*
   - 7.4 [Event Mapping Speakers API](#74-event-mapping-speakers-api) *(v2.8 신규)*
   - 7.5 [Event Mapping Lamps API](#75-event-mapping-lamps-api) *(v3.4 신규)*
8. [Server Monitoring API 설계](#8-server-monitoring-api-설계)
   - 8.1 [개요](#81-개요)
   - 8.2 [Server Category API](#82-server-category-api)
   - 8.3 [Server Instance API](#83-server-instance-api)
   - 8.4 [Dashboard Summary API](#84-dashboard-summary-api)
   - 8.5 [기본 데이터 (Seed)](#85-기본-데이터-seed)
   - 8.6 [Server Metrics API](#86-server-metrics-api) *(v2.9 신규)*
   - 8.7 [System Events API](#87-system-events-api) *(v2.9 신규)*
   - 8.8 [프록시 설정 API](#88-프록시-설정-api) *(v3.6 신규)*
9. [Account API 설계](#9-account-api-설계) *(v3.0 신규)*
   - 9.1 [개요](#91-개요)
   - 9.2 [Auth API](#92-auth-api)
   - 9.3 [User API](#93-user-api)
   - 9.4 [UserGroup API](#94-usergroup-api)
   - 9.5 [UserSession API](#95-usersession-api)
   - 9.6 [Audit Logs API](#96-audit-logs-api) *(v3.1 신규)*
   - 9.7 [Config Change Logs API](#97-config-change-logs-api) *(v3.2 신규)*
10. [Report API 설계](#10-report-api-설계-v33-신규) *(v3.3 신규)*
    - 10.1 [개요](#101-개요)
    - 10.2 [Report Components API](#102-report-components-api)
    - 10.3 [Report Templates API](#103-report-templates-api)
    - 10.4 [Report Generations API](#104-report-generations-api)
    - 10.5 [Report Preview Page](#105-report-preview-page)
11. [에러 처리](#11-에러-처리)
12. [부록](#12-부록)
    - 12.1 [전체 Endpoint 목록](#121-전체-endpoint-목록)
    - 12.2 [Event-Device 리팩토링 변경사항 (v2.3)](#122-event-device-리팩토링-변경사항-v23)
    - 12.3 [EventMapping 리팩토링 변경사항 (v2.3)](#123-eventmapping-리팩토링-변경사항-v23)

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
Authorization: Bearer {access_token}
X-Client-UUID: {client-uuid} //선택적 참고용
X-Request-ID: {request-uuid} //선택적 참고용
```

**필수 헤더**:
- `Content-Type`: POST, PUT, PATCH 요청 시 필수
- `Authorization`: JWT Bearer 토큰 (HTTPBearer 방식) - POST /api/auth/login으로 발급

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
    Fence_Group = 17,      // "Fence_Group" - 펜스 그룹
    Lamp = 18,             // "Lamp" - 경광등 (v3.4 신규)
    Enclosure = 19         // "Enclosure" - 함체 (v3.5 신규)
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

#### EnumDeviceCategory (v2.0 신규, v2.4 확장)
```python
# Python 정의 - app/utils/enums.py
# Device Polymorphic Discriminator (Joined Table Inheritance)
class EnumDeviceCategory(str, Enum):
    CONTROLLER = "controller"   # 컨트롤러
    SENSOR = "sensor"           # 센서
    CAMERA = "camera"           # 카메라
    SPEAKER = "speaker"         # 스피커 (v2.4 신규)
    ENCLOSURE = "enclosure"     # 함체관리장비 (v2.4 신규)
```

**사용처**:
- `DeviceGroupMapping.category_device`: 디바이스 그룹 매핑 시 디바이스 종류 구분
- Device 모델의 Polymorphic Discriminator (Joined Table Inheritance)
- API 요청 시 디바이스 카테고리 필터링

**참고**: 이 Enum은 `type_device`(EnumDeviceType)와 다릅니다:
- `category_device`: 상위 카테고리 (controller, sensor, camera, speaker, enclosure)
- `type_device`: 구체적인 장치 유형 (Controller, Multi, Fence, IpCamera, IpSpeaker, IoController 등)

#### EnumSpeakerType (v2.4 신규)
```python
# Python 정의 - app/utils/enums.py
class EnumSpeakerType(str, Enum):
    """Speaker device type enumeration (NATS EnumBcastDeviceType 기반)"""
    NORMAL = "NORMAL"     # 일반 스피커 단말
    ADMIN = "ADMIN"       # 관리자 단말
    MONITOR = "MONITOR"   # 모니터링 단말
    DEV = "DEV"           # 음원/마이크 단말 (입력 장치)
```

**사용처**:
- `Speaker.speaker_type`: 스피커 장비 유형 구분
- Query Parameter: `?speaker_type=NORMAL`

#### EnumDoorStatus (v2.4 신규)
```python
# Python 정의 - app/utils/enums.py
class EnumDoorStatus(str, Enum):
    """함체 도어 센서 물리적 상태"""
    CLOSED = "CLOSED"     # 도어 닫힘
    OPEN = "OPEN"         # 도어 열림
```

**사용처**:
- `Enclosure.door_status`: 함체 도어 센서 물리적 상태
- Query Parameter: `?door_status=CLOSED`

**참고**: `status`(EnumDeviceStatus)와 구분됩니다:
- `door_status`: 도어 물리적 상태 (CLOSED/OPEN)
- `status`: 장비 운영 상태 (ACTIVATED/DEACTIVATED/ERROR) - Device 상속

#### EnumLampColor (v3.4 신규)
```python
# Python 정의 - app/utils/enums.py
class EnumLampColor(str, Enum):
    """경광등 색상"""
    RED = "Red"           # 빨간색 (기본값, 경보 상황)
    ORANGE = "Orange"     # 주황색 (주의 상황)
    GREEN = "Green"       # 녹색 (정상 상황)
    BLUE = "Blue"         # 파란색 (정보 상황)
    WHITE = "White"       # 흰색 (일반 상황)
```

**사용처**:
- `EventMappingLamp.color`: 경광등 점등 색상
- Query Parameter: `?color=Red`

#### EnumBuzzerSound (v3.4 신규)
```python
# Python 정의 - app/utils/enums.py
class EnumBuzzerSound(str, Enum):
    """경광등 부저 소리 패턴"""
    FIRE_AWANG = "Fire A-WANG"    # 화재 경보음
    EMERGENCY = "Emergency"        # 비상 경보음
    AMBULANCE = "Ambulance"        # 구급차 사이렌
    PI_PI_PI = "PI-PI-PI"          # 단속음 (기본값)
    PI_CONTINUE = "PI_continue"    # 연속음
```

**사용처**:
- `EventMappingLamp.buzzer_sound`: 경광등 부저 소리 패턴
- Query Parameter: `?buzzer_sound=PI-PI-PI`

#### EnumLightMode (v3.4 신규)
```python
# Python 정의 - app/utils/enums.py
class EnumLightMode(str, Enum):
    """경광등 점등 모드"""
    STEADY = "steady"         # 계속 점등 (기본값)
    BLINKING = "blinking"     # 점멸
```

**사용처**:
- `EventMappingLamp.light_mode`: 경광등 점등 모드
- Query Parameter: `?light_mode=steady`

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

### 4.3 Integration Enum

#### EnumEventCategory (Event 모델용)
```python
# Python 정의 - app/utils/enums.py
# PRD: PRD_CategoryEvent_Refactoring.md v1.1
class EnumEventCategory(str, Enum):
    """Event category for Event polymorphic discriminator"""
    DETECTION = "detection"       # 침입 탐지 이벤트
    MALFUNCTION = "malfunction"   # 장애 이벤트
    CONNECTION = "connection"     # 연결 이벤트
```

**참고**: Event 모델의 `category_event` 필드 (polymorphic discriminator)로 사용됩니다.

#### EnumMappingEventCategory (EventMapping 모델용)
```csharp
//C# 데이터 (참고용) - 2026-01-08 업데이트
// PRD: PRD_CategoryEvent_Refactoring.md v1.1
public enum EnumMappingEventCategory
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
- EventMapping 모델의 `category_event_mapping` 필드: `EnumMappingEventCategory` Enum 사용 (위 값 중 하나)
- ⚠️ **Breaking Change**: `category_event` → `category_event_mapping` 필드명 변경 (PRD v1.1)
- 기존 `EnumCategoryEvent`는 `EnumMappingEventCategory`의 별칭으로 유지되어 하위 호환성 보장
- `group_event` 필드는 `device_group_id` (FK)로 변경됨 (PRD v2.1)

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

### 4.5 Account Enum (v3.0 신규)

> **v3.0 신규**: PRD_Account_Design.md 참조
> 사용자 인증, 세션, 로그인 로그 관련 Enum

#### EnumUserRole (사용자 등급 - 5종)
```python
# Python 정의 - app/utils/enums.py
class EnumUserRole(str, Enum):
    ADMIN = "ADMIN"           # 관리자 - 시스템 전체 관리
    MAINTAINER = "MAINTAINER" # 유지보수자 - 장비/시스템 관리
    OPERATOR = "OPERATOR"     # 운영자 - 일반 운영
    VIEWER = "VIEWER"         # 조회자 - 조회 전용
    GUEST = "GUEST"           # 게스트 - 제한된 접근
```

**사용처**:
- `AccountUser.role`: 사용자 권한 등급

#### EnumLogoutReason (로그아웃 사유 - 6종)
```python
# Python 정의 - app/utils/enums.py
class EnumLogoutReason(str, Enum):
    MANUAL = "MANUAL"               # 사용자 직접 로그아웃
    SELF_LOGOUT = "SELF_LOGOUT"     # 다른 세션에서 자신의 세션 종료
    EXPIRED = "EXPIRED"             # 세션 만료
    FORCED = "FORCED"               # 관리자 강제 로그아웃
    LOCKED = "LOCKED"               # 계정 잠금으로 인한 로그아웃
    PASSWORD_CHANGED = "PASSWORD_CHANGED" # 비밀번호 변경
```

**사용처**:
- `UserSession.logout_reason`: 세션 종료 사유

#### EnumLoginAction (로그인 행위 - 3종)
```python
# Python 정의 - app/utils/enums.py
class EnumLoginAction(str, Enum):
    LOGIN = "LOGIN"     # 로그인 시도
    LOGOUT = "LOGOUT"   # 로그아웃
    REFRESH = "REFRESH" # 토큰 갱신
```

**사용처**:
- `UserLoginLog.action`: 로그인 로그 행위 유형

#### EnumLoginResult (로그인 결과 - 2종)
```python
# Python 정의 - app/utils/enums.py
class EnumLoginResult(str, Enum):
    SUCCESS = "SUCCESS"   # 성공
    FAILURE = "FAILURE"   # 실패
```

**사용처**:
- `UserLoginLog.result`: 로그인 결과

#### EnumLoginFailureReason (로그인 실패 사유 - 7종)
```python
# Python 정의 - app/utils/enums.py
class EnumLoginFailureReason(str, Enum):
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"   # 아이디/비밀번호 불일치
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"             # 계정 잠금
    ACCOUNT_INACTIVE = "ACCOUNT_INACTIVE"         # 비활성화 계정
    PASSWORD_EXPIRED = "PASSWORD_EXPIRED"         # 비밀번호 만료
    IP_BLOCKED = "IP_BLOCKED"                     # IP 차단
    TIME_RESTRICTED = "TIME_RESTRICTED"           # 접속 시간 제한
    MAX_SESSIONS = "MAX_SESSIONS"                 # 최대 세션 수 초과
```

**사용처**:
- `UserLoginLog.failure_reason`: 로그인 실패 사유

### 4.6 Audit Enum (v3.1 신규)

> **v3.1 신규**: PRD_Audit_Log.md 참조
> 사용자 활동 감사 로그 관련 Enum

#### EnumAuditActionType (감사 행위 유형 - 18종)
```python
# Python 정의 - app/utils/enums.py
class EnumAuditActionType(str, Enum):
    # 사용자 관리 (7종)
    USER_CREATED = "USER_CREATED"           # 사용자 생성
    USER_UPDATED = "USER_UPDATED"           # 사용자 정보 수정
    USER_DELETED = "USER_DELETED"           # 사용자 삭제
    USER_LOCKED = "USER_LOCKED"             # 계정 잠금
    USER_UNLOCKED = "USER_UNLOCKED"         # 계정 잠금 해제
    USER_ACTIVATED = "USER_ACTIVATED"       # 계정 활성화
    USER_DEACTIVATED = "USER_DEACTIVATED"   # 계정 비활성화

    # 비밀번호 관리 (2종)
    PASSWORD_CHANGED = "PASSWORD_CHANGED"   # 비밀번호 변경 (본인)
    PASSWORD_RESET = "PASSWORD_RESET"       # 비밀번호 초기화 (관리자)

    # 권한/역할 관리 (2종)
    ROLE_CHANGED = "ROLE_CHANGED"           # 역할 변경
    GROUP_ASSIGNED = "GROUP_ASSIGNED"       # 그룹 할당

    # 그룹 관리 (4종)
    GROUP_CREATED = "GROUP_CREATED"         # 그룹 생성
    GROUP_UPDATED = "GROUP_UPDATED"         # 그룹 수정
    GROUP_DELETED = "GROUP_DELETED"         # 그룹 삭제
    PERMISSION_CHANGED = "PERMISSION_CHANGED" # 권한 변경

    # 세션 관리 (3종)
    SESSION_CREATED = "SESSION_CREATED"     # 세션 생성 (로그인)
    SESSION_TERMINATED = "SESSION_TERMINATED" # 세션 종료 (로그아웃)
    SESSION_FORCED_LOGOUT = "SESSION_FORCED_LOGOUT" # 강제 로그아웃
```

**사용처**:
- `AuditLog.action_type`: 감사 로그 행위 유형

#### EnumAuditResourceType (감사 대상 리소스 유형 - 4종)
```python
# Python 정의 - app/utils/enums.py
class EnumAuditResourceType(str, Enum):
    USER = "USER"               # 사용자 (AccountUser)
    USER_GROUP = "USER_GROUP"   # 사용자 그룹 (UserGroup)
    USER_SESSION = "USER_SESSION" # 사용자 세션 (UserSession)
    PASSWORD = "PASSWORD"       # 비밀번호
```

**사용처**:
- `AuditLog.resource_type`: 감사 대상 리소스 유형

#### EnumAuditStatus (감사 결과 상태 - 2종)
```python
# Python 정의 - app/utils/enums.py
class EnumAuditStatus(str, Enum):
    SUCCESS = "SUCCESS"   # 성공
    FAILURE = "FAILURE"   # 실패
```

**사용처**:
- `AuditLog.action_status`: 감사 결과 상태

### 4.7 Config Change Log Enum (v3.2 신규)

> **참조**: PRD_ConfigChangeLog.md v1.2

#### EnumConfigResourceType (설정 리소스 유형 - 17종)
```python
# Python 정의 - app/utils/enums.py
class EnumConfigResourceType(str, Enum):
    """
    설정 변경 대상 리소스 유형 (17종)
    Note: SERVER, SERVER_CATEGORY는 SystemEvent에서 관리
    """
    # Device 계열 (10종)
    CONTROLLER = "CONTROLLER"             # 제어기
    SENSOR = "SENSOR"                     # 센서
    CAMERA = "CAMERA"                     # 카메라
    SPEAKER = "SPEAKER"                   # 스피커
    ENCLOSURE = "ENCLOSURE"               # 함체
    DEVICE_GROUP = "DEVICE_GROUP"         # 장비 그룹
    CAMERA_PRESET = "CAMERA_PRESET"       # 카메라 프리셋
    ROI = "ROI"                           # 관심 영역
    XY_POINT = "XY_POINT"                 # XY 포인트
    FILE_GROUP = "FILE_GROUP"             # 파일 그룹

    # Event 계열 (4종)
    DETECTION_EVENT = "DETECTION_EVENT"   # 탐지 이벤트
    MALFUNCTION_EVENT = "MALFUNCTION_EVENT" # 오동작 이벤트
    CONNECTION_EVENT = "CONNECTION_EVENT" # 연결 이벤트
    ACTION_EVENT = "ACTION_EVENT"         # 액션 이벤트

    # Integration 계열 (3종)
    EVENT_MAPPING = "EVENT_MAPPING"       # 이벤트 매핑
    EVENT_MAPPING_CAMERA = "EVENT_MAPPING_CAMERA" # 이벤트 매핑 카메라
    EVENT_MAPPING_SPEAKER = "EVENT_MAPPING_SPEAKER" # 이벤트 매핑 스피커
```

> **SystemEvent에서 관리**: SERVER, SERVER_CATEGORY

**사용처**:
- `ConfigChangeLog.resource_type`: 변경된 설정 리소스 유형

#### EnumConfigActionType (설정 변경 액션 - 6종)
```python
# Python 정의 - app/utils/enums.py
class EnumConfigActionType(str, Enum):
    CREATED = "CREATED"           # 생성
    UPDATED = "UPDATED"           # 수정
    DELETED = "DELETED"           # 삭제
    STATUS_CHANGED = "STATUS_CHANGED"   # 상태 변경
    ASSIGNED = "ASSIGNED"         # 할당 (그룹에 장비 추가)
    UNASSIGNED = "UNASSIGNED"     # 할당 해제 (그룹에서 장비 제거)
```

**사용처**:
- `ConfigChangeLog.action`: 설정 변경 액션 유형

### 4.8 Report Enum (v3.3 신규)

> **PRD 참조**: PRD_Report_System.md Section 3

#### EnumReportType (보고서 유형 - 2종)
```python
# Python 정의 - app/utils/enums.py
class EnumReportType(str, Enum):
    """보고서 유형"""
    STANDARD = "STANDARD"   # 정형 보고서
    CUSTOM = "CUSTOM"       # 비정형 보고서 (사용자 정의 템플릿)
```

**사용처**:
- `ReportTemplate.report_type`: 템플릿 보고서 유형
- `ReportGeneration.report_type`: 생성된 보고서 유형

#### EnumReportPeriod (보고서 기간 - 4종)
```python
# Python 정의 - app/utils/enums.py
class EnumReportPeriod(str, Enum):
    """보고서 기간"""
    DAYS_7 = "7d"       # 7일
    DAYS_30 = "30d"     # 30일 (1개월)
    DAYS_90 = "90d"     # 90일 (3개월)
    YEAR_1 = "1y"       # 1년
```

**사용처**:
- `ReportTemplate.default_period`: 기본 조회 기간
- `ReportGeneration.period_type`: 보고서 생성 기간

#### EnumReportStatus (보고서 상태 - 4종)
```python
# Python 정의 - app/utils/enums.py
class EnumReportStatus(str, Enum):
    """보고서 생성 상태"""
    PENDING = "PENDING"         # 대기 중
    GENERATING = "GENERATING"   # 생성 중
    COMPLETED = "COMPLETED"     # 완료
    FAILED = "FAILED"           # 실패
```

**사용처**:
- `ReportGeneration.status`: 보고서 생성 상태

#### EnumChartType (차트 유형 - 4종)
```python
# Python 정의 - app/utils/enums.py
class EnumChartType(str, Enum):
    """차트 유형"""
    LINE = "LINE"       # 라인 차트
    BAR = "BAR"         # 막대 차트
    DONUT = "DONUT"     # 도넛 차트
    PIE = "PIE"         # 파이 차트
```

**사용처**:
- Preview 페이지 Chart.js 렌더링

#### EnumReportComponent (보고서 컴포넌트 - 21종)
```python
# Python 정의 - app/utils/enums.py
class EnumReportComponent(str, Enum):
    """보고서 컴포넌트"""
    # SUMMARY (1종)
    SUMMARY_CARD = "SUMMARY_CARD"               # 요약 카드

    # DEVICE (3종)
    DEVICE_STATUS_PIE = "DEVICE_STATUS_PIE"     # 장비 상태 파이 차트
    DEVICE_TYPE_BAR = "DEVICE_TYPE_BAR"         # 장비 유형 막대 차트
    DEVICE_GRID = "DEVICE_GRID"                 # 장비 그리드

    # EVENT (6종)
    EVENT_SUMMARY_PIE = "EVENT_SUMMARY_PIE"     # 이벤트 요약 파이 차트
    EVENT_TREND_LINE = "EVENT_TREND_LINE"       # 이벤트 추이 라인 차트
    EVENT_DAILY_BAR = "EVENT_DAILY_BAR"         # 일별 이벤트 막대 차트
    EVENT_DETECTION_GRID = "EVENT_DETECTION_GRID"   # 탐지 이벤트 그리드
    EVENT_MALFUNCTION_GRID = "EVENT_MALFUNCTION_GRID" # 장애 이벤트 그리드
    EVENT_ACTION_GRID = "EVENT_ACTION_GRID"     # 조치 이벤트 그리드

    # SYSTEM (5종)
    SYSTEM_SEVERITY_BAR = "SYSTEM_SEVERITY_BAR" # 심각도 막대 차트
    SYSTEM_TREND_LINE = "SYSTEM_TREND_LINE"     # 시스템 추이 라인 차트
    SYSTEM_CONFIG_GRID = "SYSTEM_CONFIG_GRID"   # 설정 변경 그리드
    SYSTEM_EVENT_GRID = "SYSTEM_EVENT_GRID"     # 시스템 이벤트 그리드
    SYSTEM_AUDIT_GRID = "SYSTEM_AUDIT_GRID"     # 감사 로그 그리드

    # USER (6종) - v1.4
    USER_ROLE_PIE = "USER_ROLE_PIE"             # 역할별 사용자 분포
    USER_LOGIN_TREND_LINE = "USER_LOGIN_TREND_LINE" # 일별 로그인 추이
    USER_LOGIN_RESULT_PIE = "USER_LOGIN_RESULT_PIE" # 로그인 성공/실패 분포
    USER_GRID = "USER_GRID"                     # 사용자 목록
    USER_LOGIN_GRID = "USER_LOGIN_GRID"         # 로그인 이력
    USER_SESSION_GRID = "USER_SESSION_GRID"     # 세션 목록
```

**사용처**:
- `ReportTemplate.components[].id`: 템플릿 컴포넌트 ID
- `GET /api/reports/components`: 컴포넌트 목록 조회

### 4.9 Device Setting Enum (v3.6 신규)

> 장비 설정 관련 Enum

#### EnumOperationMode (운용 모드 - 2종)
```python
# Python 정의 - app/utils/enums.py
class EnumOperationMode(str, Enum):
    """프록시 운용 모드"""
    NORMAL = "NORMAL"       # 일반 운용 모드
    REGISTER = "REGISTER"   # 장비 등록 모드
```

**사용처**:
- `ProxySetting.operation_mode`: 프록시 운용 모드

#### EnumWindyMode (풍량 모드 - 4종)
```python
# Python 정의 - app/utils/enums.py
class EnumWindyMode(str, Enum):
    """풍량 모드"""
    wind0 = "wind0"   # 풍량 모드 OFF
    wind1 = "wind1"   # 1단계
    wind2 = "wind2"   # 2단계
    wind3 = "wind3"   # 3단계 강풍
```

**사용처**:
- `ProxySetting.windy_mode`: 프록시 풍량 모드

#### EnumWeatherMode (기상 모드 - 7종)
```python
# Python 정의 - app/utils/enums.py
class EnumWeatherMode(str, Enum):
    """기상 모드"""
    NORMAL = "NORMAL"           # 평시
    FOG = "FOG"                 # 안개
    SEA_FOG = "SEA_FOG"         # 해무
    YELLOW_DUST = "YELLOW_DUST" # 황사
    RAIN = "RAIN"               # 강우
    SNOW = "SNOW"               # 강설
    HEAT_HAZE = "HEAT_HAZE"     # 아지랑이
```

**사용처**:
- `CameraSetting.weather_mode`: 카메라 기상 모드

#### EnumCameraVideoMode (카메라 영상 모드 - 4종)
```python
# Python 정의 - app/utils/enums.py
class EnumCameraVideoMode(str, Enum):
    """카메라 영상 모드"""
    NORMAL = "NORMAL"               # 보통
    STABILIZATION = "STABILIZATION" # 흔들림 보정
    BLC = "BLC"                     # 역광 보정
    NIGHT_ENHANCE = "NIGHT_ENHANCE" # 야간 영상 개선
```

**사용처**:
- `CameraSetting.camera_mode`: 카메라 영상 모드

#### EnumOnOff (켜짐/꺼짐 - 2종)
```python
# Python 정의 - app/utils/enums.py
class EnumOnOff(str, Enum):
    """켜짐/꺼짐"""
    on = "on"     # 켜짐
    off = "off"   # 꺼짐
```

**사용처**:
- `CameraSetting.heater`: 히터 ON/OFF
- `CameraSetting.fan`: 팬 ON/OFF
- `CameraSetting.headlight`: 전조등 ON/OFF

#### EnumDayNightMode (주야간 모드 - 3종)
```python
# Python 정의 - app/utils/enums.py
class EnumDayNightMode(str, Enum):
    """주야간 모드"""
    AUTO = "AUTO"     # 자동 전환
    DAY = "DAY"       # 주간 모드
    NIGHT = "NIGHT"   # 야간 모드
```

**사용처**:
- `CameraSetting.day_night_mode`: 카메라 주야간 모드

#### EnumPalette (열화상 팔레트 - 4종)
```python
# Python 정의 - app/utils/enums.py
class EnumPalette(str, Enum):
    """열화상 팔레트"""
    WHITE_HOT = "WHITE_HOT"   # 열원 흰색
    BLACK_HOT = "BLACK_HOT"   # 열원 검정색
    RAINBOW = "RAINBOW"       # 무지개
    IRONBOW = "IRONBOW"       # 철 색상
```

**사용처**:
- `CameraSetting.palette`: 열화상 카메라 팔레트 (열화상 카메라만 해당, nullable)

---

## 5. Device API 설계

### Device Polymorphic 구조 (Joined Table Inheritance)

Device는 Joined Table Inheritance 패턴을 사용하여 다형성을 지원합니다. 공통 속성은 `devices` 테이블에, 타입별 특화 속성은 각 하위 테이블에 저장됩니다.

```
                    ┌─────────────────────────────────────┐
                    │              devices                │
                    │  (Base Table - 공통 속성)           │
                    ├─────────────────────────────────────┤
                    │  id (PK)                            │
                    │  number_device                      │
                    │  group_device (레거시)              │
                    │  name_device                        │
                    │  type_device (EnumDeviceType)       │
                    │  version                            │
                    │  status (EnumDeviceStatus)          │
                    │  category_device (Discriminator)    │
                    │  created_at, updated_at             │
                    └───────────────┬─────────────────────┘
                                    │
        ┌───────────────┬───────────┼───────────┬───────────────┐
        │               │           │           │               │
        ▼               ▼           ▼           ▼               ▼
┌────────────────┐ ┌───────────┐ ┌─────────┐ ┌─────────────┐ ┌────────────────┐
│  controllers   │ │  sensors  │ │ cameras │ │  speakers   │ │   enclosures   │
│  (v1.0~)       │ │  (v1.0~)  │ │ (v1.0~) │ │  (v2.4~)    │ │   (v2.4~)      │
├────────────────┤ ├───────────┤ ├─────────┤ ├─────────────┤ ├────────────────┤
│ id (FK→devices)│ id (FK)     │ │ id (FK) │ │ id (FK)     │ │ id (FK)        │
│ ip_address     │ │controller │ │ip_address│ │speaker_type│ │ door_status    │
│ ip_port        │ │id (FK)    │ │ip_port  │ │server_id    │ │ geolocation    │
└────────────────┘ └───────────┘ │mode     │ │description  │ │ threshold_conf │
                                 │category │ └─────────────┘ │ heater_enabled │
                                 │urls(JSONB)                │ fan_enabled    │
                                 └─────────┘                 └────────────────┘
                                                            
```

**Discriminator 컬럼**: `category_device` (EnumDeviceCategory)
- `controller`, `sensor`, `camera`, `speaker`, `enclosure`

**FK 정책**: 모든 하위 테이블의 `id`는 `devices.id`를 참조하며, `CASCADE DELETE` 적용

---

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
      "is_enable": true,
      "ip_address": "192.168.1.100",
      "ip_port": 8001,
      "geolocation": null,
      "sensors": null,
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
      "is_enable": true,
      "ip_address": "192.168.1.101",
      "ip_port": 8001,
      "geolocation": null,
      "sensors": null,
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
      "is_enable": true,
      "ip_address": "192.168.1.100",
      "ip_port": 8001,
      "geolocation": null,
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
          "is_enable": true,
          "controller_id": 1,
          "geolocation": null,
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
      "is_enable": true,
      "ip_address": "192.168.1.101",
      "ip_port": 8001,
      "geolocation": null,
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

**Error Response (422 Validation Error)** - 잘못된 쿼리 파라미터:
```json
{
  "success": false,
  "message": "Validation error",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [
      {"field": "page", "message": "Page must be greater than 0"},
      {"field": "limit", "message": "Limit must be between 1 and 100"}
    ]
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
    "is_enable": true,
    "ip_address": "192.168.1.100",
    "ip_port": 8001,
    "geolocation": null,
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
    "is_enable": true,
    "ip_address": "192.168.1.100",
    "ip_port": 8001,
    "geolocation": null,
    "sensors": [
      {
        "id": 101,
        "number_device": 1,
        "group_device": 1, // (Deprecated 예정, 레거시)
        "name_device": "Sensor-A-1",
        "type_device": "Multi", //(EnumDeviceType)
        "version": "v1.5.0",
        "status": "ACTIVATED", //(EnumDeviceStatus)
        "is_enable": true,
        "controller_id": 1,
        "geolocation": null,
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
        "is_enable": true,
        "controller_id": 1,
        "geolocation": null,
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

**Request Example**:
```http
POST /api/devices/controllers HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "number_device": 3,
  "name_device": "Controller-C",
  "ip_address": "192.168.1.102",
  "ip_port": 8001,
  "version": "v2.1.0",
  "status": "DEACTIVATED",
  "geolocation": {
    "location": "GOP 3초소 1제어기",
    "latitude": 38.1234,
    "longitude": 127.5678
  },
  "group_ids": [1, 2]
}
```

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
  "geolocation": {  // (optional, v2.4 신규) 위치 정보
    "location": "GOP 3초소 1제어기",
    "latitude": 38.1234,
    "longitude": 127.5678,
    "altitude": 245.5
  },
  "group_ids": [1, 2] // (optional) 소속 디바이스 그룹 ID 배열 (N:N 관계)
}
```

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| number_device | integer | Y | - | 장치 번호 |
| group_device | integer | N | 0 | 디바이스 그룹 (Deprecated 예정, 레거시) |
| name_device | string | Y | - | 장치 이름 |
| type_device | string | Y | - | 장치 타입 (EnumDeviceType) |
| version | string | N | null | 펌웨어 버전 |
| status | string | Y | - | 상태 (EnumDeviceStatus) |
| is_enable | boolean | N | true | 장비 활성화 여부 |
| ip_address | string | Y | - | IP 주소 |
| ip_port | integer | Y | - | 포트 번호 |
| geolocation | object | N | null | 위치 정보 (v2.4 신규) |
| group_ids | array[int] | N | null | 소속 디바이스 그룹 ID 배열 (N:N 관계) |

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
    "is_enable": true,
    "ip_address": "192.168.1.102",
    "ip_port": 8001,
    "geolocation": {  // (v2.4 신규) 위치 정보
      "location": "GOP 3초소 1제어기",
      "latitude": 38.1234,
      "longitude": 127.5678,
      "altitude": 245.5
    },
    "sensors": null,
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

**Error Response (422 Validation Error)**:
```json
{
  "success": false,
  "message": "Validation error",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [
      {"field": "ip_address", "message": "Invalid IP address format"},
      {"field": "number_device", "message": "Field required"}
    ]
  }
}
```

---

#### 5.1.4 Controller 수정 (부분)

**Endpoint**: `PATCH /api/devices/controllers/{id}`

**Request Example**:
```http
PATCH /api/devices/controllers/3 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "name_device": "Controller-C-Updated",
  "status": "ACTIVATED",
  "version": "v2.2.0",
  "group_ids": [1]
}
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| id | integer | Y | Controller ID |

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

**필드 설명** (PATCH - 모든 필드 선택적):
| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| number_device | integer | N | - | 장치 번호 |
| group_device | integer | N | - | 디바이스 그룹 (Deprecated 예정, 레거시) |
| name_device | string | N | - | 장치 이름 |
| type_device | string | N | - | 장치 타입 (EnumDeviceType) |
| version | string | N | - | 펌웨어 버전 |
| status | string | N | - | 상태 (EnumDeviceStatus) |
| is_enable | boolean | N | - | 장비 활성화 여부 |
| ip_address | string | N | - | IP 주소 |
| ip_port | integer | N | - | 포트 번호 |
| geolocation | object | N | - | 위치 정보 |
| group_ids | array[int] | N | - | 소속 디바이스 그룹 ID 배열 (N:N 관계) |

> **참고**: PATCH는 부분 업데이트로, 제공된 필드만 수정됩니다. 기본값 컬럼의 `-`는 "현재 값 유지"를 의미합니다.

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
    "is_enable": true,
    "ip_address": "192.168.1.102",
    "ip_port": 8001,
    "geolocation": null,
    "sensors": null,
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

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "Controller with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

---

#### 5.1.5 Controller 수정 (전체)

**Endpoint**: `PUT /api/devices/controllers/{id}`

**Request Example**:
```http
PUT /api/devices/controllers/3 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "number_device": 3,
  "group_device": 1,
  "name_device": "Controller-C-Complete-Update",
  "type_device": "Controller",
  "version": "v2.3.0",
  "status": "ACTIVATED",
  "is_enable": true,
  "ip_address": "192.168.1.103",
  "ip_port": 8002,
  "geolocation": null,
  "group_ids": [1]
}
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| id | integer | Y | Controller ID |

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
  "is_enable": true,
  "ip_address": "192.168.1.103",
  "ip_port": 8002,
  "geolocation": null,
  "group_ids": [1]
}
```

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| number_device | integer | Y | - | 장치 번호 |
| group_device | integer | N | 0 | 디바이스 그룹 (Deprecated 예정, 레거시) |
| name_device | string | Y | - | 장치 이름 |
| type_device | string | Y | - | 장치 타입 (EnumDeviceType) |
| version | string | N | null | 펌웨어 버전 |
| status | string | Y | - | 상태 (EnumDeviceStatus) |
| is_enable | boolean | N | true | 장비 활성화 여부 |
| ip_address | string | Y | - | IP 주소 |
| ip_port | integer | Y | - | 포트 번호 |
| geolocation | object | N | null | 위치 정보 |
| group_ids | array[int] | N | null | 소속 디바이스 그룹 ID 배열 (N:N 관계) |

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
    "is_enable": true,
    "ip_address": "192.168.1.103",
    "ip_port": 8002,
    "geolocation": null,
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

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "Controller with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

---

#### 5.1.6 Controller 삭제

**Endpoint**: `DELETE /api/devices/controllers/{id}`

**Request Example**:
```http
DELETE /api/devices/controllers/3 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| id | integer | Y | Controller ID |

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

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "Controller with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
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

**Request Example**:
```http
GET /api/devices/sensors?type_device=Fence&status=ACTIVATED&include_controller=true HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

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
      "is_enable": true,
      "controller_id": 1,
      "geolocation": null,
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
      "is_enable": true,
      "controller_id": 1,
      "geolocation": null,
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
      "is_enable": true,
      "controller_id": 1,
      "geolocation": null,
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
        "is_enable": true,
        "ip_address": "192.168.1.101",
        "ip_port": 8080,
        "geolocation": null,
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

**Error Response (422 Validation Error)** - 잘못된 쿼리 파라미터:
```json
{
  "success": false,
  "message": "Validation error",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [
      {"field": "page", "message": "Page must be greater than 0"},
      {"field": "limit", "message": "Limit must be between 1 and 100"}
    ]
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
    "is_enable": true,
    "controller_id": 1,
    "geolocation": null,
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
    "is_enable": true,
    "controller_id": 1,
    "geolocation": null,
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
      "is_enable": true,
      "ip_address": "192.168.1.101",
      "ip_port": 8080,
      "geolocation": null,
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

**Request Example**:
```http
POST /api/devices/sensors HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "number_device": 3,
  "name_device": "Fence-001",
  "type_device": "Fence",
  "controller_id": 1,
  "version": "v2.1.0",
  "status": "DEACTIVATED",
  "geolocation": {
    "location": "GOP 3초소 철책 A구간",
    "latitude": 38.1235,
    "longitude": 127.5680
  },
  "group_ids": [1, 2]
}
```

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
  "geolocation": {  // (optional, v2.4 신규) 위치 정보
    "location": "GOP 3초소 철책 A구간",
    "latitude": 38.1235,
    "longitude": 127.5680,
    "altitude": 148.5
  },
  "group_ids": [1, 2] // (optional) 소속 디바이스 그룹 ID 배열 (N:N 관계)
}
```

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| number_device | integer | Y | - | 장치 번호 |
| group_device | integer | N | 0 | 디바이스 그룹 (Deprecated 예정, 레거시) |
| name_device | string | Y | - | 장치 이름 |
| type_device | string | Y | - | 센서 타입 (EnumDeviceType) |
| version | string | N | null | 펌웨어 버전 |
| status | string | Y | - | 상태 (EnumDeviceStatus) |
| is_enable | boolean | N | true | 장비 활성화 여부 |
| controller_id | integer | Y | - | 연결된 제어기 ID |
| geolocation | object | N | null | 위치 정보 (v2.4 신규) |
| group_ids | array[int] | N | null | 소속 디바이스 그룹 ID 배열 (N:N 관계) |

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
    "is_enable": true,
    "controller_id": 1,
    "geolocation": {  // (v2.4 신규) 위치 정보
      "location": "GOP 3초소 철책 A구간",
      "latitude": 38.1235,
      "longitude": 127.5680,
      "altitude": 148.5
    },
    "created_at": "2025-01-10T10:39:00.100Z",
    "updated_at": "2025-01-10T10:39:00.100Z",
    "device_groups": [
      {"id": 1, "name": "GOP 1구역", "description": "GOP 1구역 장비 그룹", "device_count": 6},
      {"id": 2, "name": "GOP 2구역", "description": "GOP 2구역 장비 그룹", "device_count": 3}
    ],
    "controller": null
  },
  "meta": {
    "timestamp": "2025-01-10T10:39:00.100Z",
    "request_id": "550e8409-e29b-41d4-a716-446655440000"
  }
}
```

**Error Response (422 Validation Error)**:
```json
{
  "success": false,
  "message": "Validation error",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [
      {"field": "number_device", "message": "Field required"},
      {"field": "name_device", "message": "Field required"}
    ]
  }
}
```

---

#### 5.2.4 Sensor 수정 (부분)

**Endpoint**: `PATCH /api/devices/sensors/{id}`

**Request Example**:
```http
PATCH /api/devices/sensors/103 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "name_device": "Fence-001-Updated",
  "status": "ACTIVATED",
  "version": "v2.2.0",
  "group_ids": [1]
}
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| id | integer | Y | Sensor ID |

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

**필드 설명** (PATCH - 모든 필드 선택적):
| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| number_device | integer | N | - | 장치 번호 |
| group_device | integer | N | - | 디바이스 그룹 (Deprecated 예정, 레거시) |
| name_device | string | N | - | 장치 이름 |
| type_device | string | N | - | 센서 타입 (EnumDeviceType) |
| version | string | N | - | 펌웨어 버전 |
| status | string | N | - | 상태 (EnumDeviceStatus) |
| is_enable | boolean | N | - | 장비 활성화 여부 |
| controller_id | integer | N | - | 연결된 제어기 ID |
| geolocation | object | N | - | 위치 정보 |
| group_ids | array[int] | N | - | 소속 디바이스 그룹 ID 배열 (N:N 관계) |

> **참고**: PATCH는 부분 업데이트로, 제공된 필드만 수정됩니다. 기본값 컬럼의 `-`는 "현재 값 유지"를 의미합니다.

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
    "is_enable": true,
    "controller_id": 1,
    "geolocation": null,
    "created_at": "2025-01-10T10:39:00.100Z",
    "updated_at": "2025-01-10T10:40:00.150Z",
    "device_groups": [
      {"id": 1, "name": "GOP 1구역", "description": "GOP 1구역 장비 그룹", "device_count": 6}
    ],
    "controller": null
  },
  "meta": {
    "timestamp": "2025-01-10T10:40:00.150Z",
    "request_id": "550e8410-e29b-41d4-a716-446655440000"
  }
}
```

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "Sensor with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

---

#### 5.2.5 Sensor 수정 (전체)

**Endpoint**: `PUT /api/devices/sensors/{id}`

**Request Example**:
```http
PUT /api/devices/sensors/103 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "number_device": 3,
  "group_device": 1,
  "name_device": "Fence-001-Complete-Update",
  "type_device": "Fence",
  "version": "v2.3.0",
  "status": "ACTIVATED",
  "is_enable": true,
  "controller_id": 1,
  "geolocation": {
    "location": "GOP 3초소 철책 A구간",
    "latitude": 38.1235,
    "longitude": 127.5680
  },
  "group_ids": [1, 2]
}
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| id | integer | Y | Sensor ID |

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
  "is_enable": true,
  "controller_id": 1,
  "geolocation": {
    "location": "GOP 3초소 철책 A구간",
    "latitude": 38.1235,
    "longitude": 127.5680
  },
  "group_ids": [1, 2]
}
```

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| number_device | integer | Y | - | 장치 번호 |
| group_device | integer | N | 0 | 디바이스 그룹 (Deprecated 예정, 레거시) |
| name_device | string | Y | - | 장치 이름 |
| type_device | string | Y | - | 센서 타입 (EnumDeviceType) |
| version | string | N | null | 펌웨어 버전 |
| status | string | Y | - | 상태 (EnumDeviceStatus) |
| is_enable | boolean | N | true | 장비 활성화 여부 |
| controller_id | integer | Y | - | 연결된 제어기 ID |
| geolocation | object | N | null | 위치 정보 |
| group_ids | array[int] | N | null | 소속 디바이스 그룹 ID 배열 (N:N 관계) |

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
    "is_enable": true,
    "controller_id": 1,
    "geolocation": null,
    "created_at": "2025-01-10T10:39:00.100Z",
    "updated_at": "2025-01-10T10:41:00.200Z",
    "device_groups": [],
    "controller": null
  },
  "meta": {
    "timestamp": "2025-01-10T10:41:00.200Z",
    "request_id": "550e8411-e29b-41d4-a716-446655440000"
  }
}
```

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "Sensor with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

---

#### 5.2.6 Sensor 삭제

**Endpoint**: `DELETE /api/devices/sensors/{id}`

**Request Example**:
```http
DELETE /api/devices/sensors/103 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| id | integer | Y | Sensor ID |

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

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "Sensor with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
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

**Request Example**:
```http
GET /api/devices/cameras?mode=ONVIF&category=PTZ&status=ACTIVATED HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

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
      "is_enable": true,
      "ip_address": "192.168.1.109",
      "ip_port": 80,
      "user_name": "admin",
      "user_password": "********",
      "mode": "ONVIF", //(EnumCameraMode)
      "category": "PTZ", //(EnumCameraType)
      "is_record": false,
      "urls": {
        "homepage": {"url": "http://192.168.1.109/"},
        "onvif": {"device_service": "http://192.168.1.109:8000/onvif/device_service"},
        "streams": {
          "rtsp": {"main": "rtsp://192.168.1.109:554/Streaming/Channels/101", "sub": "rtsp://192.168.1.109:554/Streaming/Channels/102"},
          "webrtc": {"main": "https://192.168.1.109/webrtc/main"}
        },
        "snapshot": {"ch1": "http://192.168.1.109/cgi-bin/snapshot.cgi"}
      },
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

**Error Response (422 Validation Error)** - 잘못된 쿼리 파라미터:
```json
{
  "success": false,
  "message": "Validation error",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [
      {"field": "page", "message": "Page must be greater than 0"},
      {"field": "limit", "message": "Limit must be between 1 and 100"}
    ]
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
    "is_enable": true,
    "ip_address": "192.168.1.109",
    "ip_port": 80,
    "user_name": "admin",
    "user_password": "password123",
    "mode": "ONVIF", //(EnumCameraMode)
    "category": "PTZ", //(EnumCameraType)
    "is_record": true,
    "urls": {
      "homepage": {"url": "http://192.168.1.109/"},
      "onvif": {"device_service": "http://192.168.1.109:8000/onvif/device_service"},
      "streams": {
        "rtsp": {"main": "rtsp://192.168.1.109:554/Streaming/Channels/101", "sub": "rtsp://192.168.1.109:554/Streaming/Channels/102"},
        "webrtc": {"main": "https://192.168.1.109/webrtc/main"}
      },
      "snapshot": {"ch1": "http://192.168.1.109/cgi-bin/snapshot.cgi"}
    },
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

**Request Example**:
```http
POST /api/devices/cameras HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "number_device": 110,
  "name_device": "Camera-110",
  "type_device": "IpCamera",
  "ip_address": "192.168.1.110",
  "ip_port": 80,
  "user_name": "admin",
  "user_password": "password123",
  "mode": "ONVIF",
  "category": "FIXED",
  "is_record": false,
  "urls": {
    "homepage": {"url": "http://192.168.1.109/"},
    "onvif": {"device_service": "http://192.168.1.109:8000/onvif/device_service"},
    "streams": {
      "rtsp": {"main": "rtsp://192.168.1.109:554/Streaming/Channels/101", "sub": "rtsp://192.168.1.109:554/Streaming/Channels/102"},
      "webrtc": {"main": "https://192.168.1.109/webrtc/main"}
    },
    "snapshot": {"ch1": "http://192.168.1.109/cgi-bin/snapshot.cgi"}
  },
}
```

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
  "mode": "ONVIF", //(EnumCameraMode)
  "category": "FIXED", //(EnumCameraType)
  "is_record": false,
  "urls": {
    "homepage": {"url": "http://192.168.1.109/"},
    "onvif": {"device_service": "http://192.168.1.109:8000/onvif/device_service"},
    "streams": {
      "rtsp": {"main": "rtsp://192.168.1.109:554/Streaming/Channels/101", "sub": "rtsp://192.168.1.109:554/Streaming/Channels/102"},
      "webrtc": {"main": "https://192.168.1.109/webrtc/main"}
    },
    "snapshot": {"ch1": "http://192.168.1.109/cgi-bin/snapshot.cgi"}
  },
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

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| number_device | integer | Y | - | 장치 번호 |
| group_device | integer | N | 0 | 디바이스 그룹 (Deprecated 예정, 레거시) |
| name_device | string | Y | - | 장치 이름 |
| type_device | string | Y | - | 장치 타입 (EnumDeviceType) |
| version | string | N | null | 펌웨어 버전 |
| status | string | Y | - | 상태 (EnumDeviceStatus) |
| is_enable | boolean | N | true | 장비 활성화 여부 |
| ip_address | string | Y | - | IP 주소 |
| ip_port | integer | Y | - | 포트 번호 |
| user_name | string | N | null | 카메라 접속 사용자명 |
| user_password | string | N | null | 카메라 접속 비밀번호 |
| mode | string | Y | - | 카메라 모드 (EnumCameraMode) |
| category | string | Y | - | 카메라 타입 (EnumCameraType) |
| is_record | boolean | N | false | 녹화 여부 |
| urls | object | N | null | 카메라 URL 정보 (JSONB) |
| hardware_spec | object | N | null | 하드웨어 사양 정보 |
| geolocation | object | N | null | 위치 정보 |
| group_ids | array[int] | N | null | 소속 디바이스 그룹 ID 배열 (N:N 관계) |

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
    "is_enable": true,
    "ip_address": "192.168.1.110",
    "ip_port": 80,
    "user_name": "admin",
    "user_password": "password123",
    "mode": "ONVIF", //(EnumCameraMode)
    "category": "FIXED", //(EnumCameraType)
    "is_record": false,
    "urls": {
      "homepage": {"url": "http://192.168.1.109/"},
      "onvif": {"device_service": "http://192.168.1.109:8000/onvif/device_service"},
      "streams": {
        "rtsp": {"main": "rtsp://192.168.1.109:554/Streaming/Channels/101", "sub": "rtsp://192.168.1.109:554/Streaming/Channels/102"},
        "webrtc": {"main": "https://192.168.1.109/webrtc/main"}
      },
      "snapshot": {"ch1": "http://192.168.1.109/cgi-bin/snapshot.cgi"}
    },
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

**Error Response (422 Validation Error)**:
```json
{
  "success": false,
  "message": "Validation error",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [
      {"field": "ip_address", "message": "Invalid IP address format"},
      {"field": "number_device", "message": "Field required"}
    ]
  }
}
```

---

#### 5.3.4 Camera 수정 (부분)

**Endpoint**: `PATCH /api/devices/cameras/{id}`

**Request Example**:
```http
PATCH /api/devices/cameras/202 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "name_device": "Camera-110-Updated",
  "status": "ACTIVATED",
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

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| id | integer | Y | Camera ID |

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

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| number_device | integer | N | - | 장치 번호 (현재 값 유지) |
| group_device | integer | N | - | 디바이스 그룹 (Deprecated 예정, 레거시) (현재 값 유지) |
| name_device | string | N | - | 장치 이름 (현재 값 유지) |
| type_device | string | N | - | 장치 타입 (EnumDeviceType) (현재 값 유지) |
| version | string | N | - | 펌웨어 버전 (현재 값 유지) |
| status | string | N | - | 상태 (EnumDeviceStatus) (현재 값 유지) |
| is_enable | boolean | N | - | 장비 활성화 여부 (현재 값 유지) |
| ip_address | string | N | - | IP 주소 (현재 값 유지) |
| ip_port | integer | N | - | 포트 번호 (현재 값 유지) |
| user_name | string | N | - | 카메라 접속 사용자명 (현재 값 유지) |
| user_password | string | N | - | 카메라 접속 비밀번호 (현재 값 유지) |
| mode | string | N | - | 카메라 모드 (EnumCameraMode) (현재 값 유지) |
| category | string | N | - | 카메라 타입 (EnumCameraType) (현재 값 유지) |
| is_record | boolean | N | - | 녹화 여부 (현재 값 유지) |
| urls | object | N | - | 카메라 URL 정보 (JSONB) (현재 값 유지) |
| hardware_spec | object | N | - | 하드웨어 사양 정보 (부분 병합) |
| geolocation | object | N | - | 위치 정보 (부분 병합) |
| group_ids | array[int] | N | - | 소속 디바이스 그룹 ID 배열 (현재 값 유지) |

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
    "is_enable": true,
    "ip_address": "192.168.1.110",
    "ip_port": 80,
    "user_name": "admin",
    "user_password": "newpassword456",
    "mode": "ONVIF", //(EnumCameraMode)
    "category": "FIXED", //(EnumCameraType)
    "is_record": true,
    "urls": {
      "homepage": {"url": "http://192.168.1.109/"},
      "onvif": {"device_service": "http://192.168.1.109:8000/onvif/device_service"},
      "streams": {
        "rtsp": {"main": "rtsp://192.168.1.109:554/Streaming/Channels/101", "sub": "rtsp://192.168.1.109:554/Streaming/Channels/102"},
        "webrtc": {"main": "https://192.168.1.109/webrtc/main"}
      },
      "snapshot": {"ch1": "http://192.168.1.109/cgi-bin/snapshot.cgi"}
    },
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

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "Camera with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

---

#### 5.3.5 Camera 수정 (전체)

**Endpoint**: `PUT /api/devices/cameras/{id}`

**Request Example**:
```http
PUT /api/devices/cameras/202 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "number_device": 110,
  "group_device": 1,
  "name_device": "Camera-110-Complete-Update",
  "type_device": "IpCamera",
  "version": "v3.3.0",
  "status": "ACTIVATED",
  "is_enable": true,
  "ip_address": "192.168.1.110",
  "ip_port": 80,
  "user_name": "admin",
  "user_password": "completepassword789",
  "mode": "ONVIF",
  "category": "PTZ",
  "is_record": true,
  "urls": {
    "homepage": {"url": "http://192.168.1.109/"},
    "onvif": {"device_service": "http://192.168.1.109:8000/onvif/device_service"},
    "streams": {
      "rtsp": {"main": "rtsp://192.168.1.109:554/Streaming/Channels/101", "sub": "rtsp://192.168.1.109:554/Streaming/Channels/102"},
      "webrtc": {"main": "https://192.168.1.109/webrtc/main"}
    },
    "snapshot": {"ch1": "http://192.168.1.109/cgi-bin/snapshot.cgi"}
  },
  "hardware_spec": {
    "name": "GOP 1구역 PTZ 카메라",
    "location": "GOP 1구역 전방 초소",
    "manufacturer": "Hanwha Vision",
    "model": "XNP-6320RH"
  },
  "geolocation": {
    "location": "GOP 1구역 전방 초소",
    "latitude": 38.1234,
    "longitude": 127.5678
  },
  "group_ids": [1, 3]
}
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| id | integer | Y | Camera ID |

**Request Body** (전체 업데이트):
```json
{
  "number_device": 110,
  "group_device": 1, // (Deprecated 예정, 레거시)
  "name_device": "Camera-110-Complete-Update",
  "type_device": "IpCamera", //(EnumDeviceType)
  "version": "v3.3.0",
  "status": "ACTIVATED", //(EnumDeviceStatus)
  "is_enable": true,
  "ip_address": "192.168.1.110",
  "ip_port": 80,
  "user_name": "admin",
  "user_password": "completepassword789",
  "mode": "ONVIF", //(EnumCameraMode)
  "category": "PTZ", //(EnumCameraType)
  "is_record": true,
  "urls": {
    "homepage": {"url": "http://192.168.1.110/"},
    "onvif": {"device_service": "http://192.168.1.110:8000/onvif/device_service"},
    "streams": {
      "rtsp": {"main": "rtsp://192.168.1.110:554/Streaming/Channels/101", "sub": "rtsp://192.168.1.110:554/Streaming/Channels/102"}
    }
  },
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

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| number_device | integer | Y | - | 장치 번호 |
| group_device | integer | N | 0 | 디바이스 그룹 (Deprecated 예정, 레거시) |
| name_device | string | Y | - | 장치 이름 |
| type_device | string | Y | - | 장치 타입 (EnumDeviceType) |
| version | string | N | null | 펌웨어 버전 |
| status | string | Y | - | 상태 (EnumDeviceStatus) |
| is_enable | boolean | N | true | 장비 활성화 여부 |
| ip_address | string | Y | - | IP 주소 |
| ip_port | integer | Y | - | 포트 번호 |
| user_name | string | N | null | 카메라 접속 사용자명 |
| user_password | string | N | null | 카메라 접속 비밀번호 |
| mode | string | Y | - | 카메라 모드 (EnumCameraMode) |
| category | string | Y | - | 카메라 타입 (EnumCameraType: NONE, FIXED, PTZ) |
| is_record | boolean | N | false | 녹화 여부 |
| urls | object | N | null | 카메라 URL 정보 (JSONB) |
| hardware_spec | object | N | null | 하드웨어 사양 정보 |
| geolocation | object | N | null | 위치 정보 |
| group_ids | array[int] | N | null | 소속 디바이스 그룹 ID 배열 (N:N 관계) |

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
    "is_enable": true,
    "ip_address": "192.168.1.110",
    "ip_port": 80,
    "user_name": "admin",
    "user_password": "completepassword789",
    "mode": "ONVIF", //(EnumCameraMode)
    "category": "PTZ", //(EnumCameraType)
    "is_record": true,
    "urls": {
      "homepage": {"url": "http://192.168.1.110/"},
      "onvif": {"device_service": "http://192.168.1.110:8000/onvif/device_service"},
      "streams": {
        "rtsp": {"main": "rtsp://192.168.1.110:554/Streaming/Channels/101", "sub": "rtsp://192.168.1.110:554/Streaming/Channels/102"}
      }
    },
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

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "Camera with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

---

#### 5.3.6 Camera 삭제

**Endpoint**: `DELETE /api/devices/cameras/{id}`

**Request Example**:
```http
DELETE /api/devices/cameras/202 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| id | integer | Y | Camera ID |

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

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "Camera with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

---

#### 5.3.7 카메라 설정 조회

**Endpoint**: `GET /api/devices/cameras/{camera_id}/settings`

**Path Parameters**:
- `camera_id` (int, required): Camera ID

> **Note**: 설정이 존재하지 않으면 기본값으로 자동 생성합니다 (Lazy 생성).

**Request Example**:
```http
GET /api/devices/cameras/201/settings HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Camera settings retrieved successfully",
  "data": {
    "id": 1,
    "camera_id": 201,
    "weather_mode": "NORMAL",       //(EnumWeatherMode)
    "camera_mode": "NORMAL",        //(EnumCameraVideoMode)
    "heater": "off",                //(EnumOnOff)
    "fan": "off",                   //(EnumOnOff)
    "headlight": "off",             //(EnumOnOff)
    "day_night_mode": "AUTO",       //(EnumDayNightMode)
    "pan_tilt_speed": 50,
    "zoom_speed": 50,
    "palette": null,                //(EnumPalette, nullable)
    "created_at": "2026-02-06T12:00:00.000Z",
    "updated_at": "2026-02-06T12:00:00.000Z"
  },
  "meta": {
    "timestamp": "2026-02-06T12:00:00.050Z",
    "request_id": "550e8403-e29b-41d4-a716-446655440000"
  }
}
```

**Error Response** (404 Not Found):
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Camera with id 999 not found",
    "details": "No camera exists with the specified ID"
  },
  "meta": {
    "timestamp": "2026-02-06T12:00:00.050Z",
    "request_id": "550e8403-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 5.3.8 카메라 설정 수정 (부분)

**Endpoint**: `PATCH /api/devices/cameras/{camera_id}/settings`

**Request Example**:
```http
PATCH /api/devices/cameras/201/settings HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "weather_mode": "FOG",
  "heater": "on",
  "fan": "on",
  "pan_tilt_speed": 80
}
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| camera_id | integer | Y | Camera ID |

**Request Body** (부분 업데이트 - 변경할 필드만 포함):
```json
{
  "weather_mode": "FOG",           //(EnumWeatherMode)
  "heater": "on",                  //(EnumOnOff)
  "fan": "on",                     //(EnumOnOff)
  "pan_tilt_speed": 80
}
```

> **Note**: PATCH는 부분 업데이트이므로 변경할 필드만 포함합니다. 설정이 존재하지 않으면 Upsert (자동 생성 + 요청 필드 적용).

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| weather_mode | string | N | "NORMAL" | 기상 모드 (EnumWeatherMode) (현재 값 유지) |
| camera_mode | string | N | "NORMAL" | 카메라 영상 모드 (EnumCameraVideoMode) (현재 값 유지) |
| heater | string | N | "off" | 히터 ON/OFF (EnumOnOff) (현재 값 유지) |
| fan | string | N | "off" | 팬 ON/OFF (EnumOnOff) (현재 값 유지) |
| headlight | string | N | "off" | 전조등 ON/OFF (EnumOnOff) (현재 값 유지) |
| day_night_mode | string | N | "AUTO" | 주야간 모드 (EnumDayNightMode) (현재 값 유지) |
| pan_tilt_speed | integer | N | 50 | 팬틸트 속도 (0~100) (현재 값 유지) |
| zoom_speed | integer | N | 50 | 줌 속도 (0~100) (현재 값 유지) |
| palette | string | N | null | 열화상 팔레트 (EnumPalette, nullable) (현재 값 유지) |

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Camera settings updated successfully",
  "data": {
    "id": 1,
    "camera_id": 201,
    "weather_mode": "FOG",
    "camera_mode": "NORMAL",
    "heater": "on",
    "fan": "on",
    "headlight": "off",
    "day_night_mode": "AUTO",
    "pan_tilt_speed": 80,
    "zoom_speed": 50,
    "palette": null,
    "created_at": "2026-02-06T12:00:00.000Z",
    "updated_at": "2026-02-06T12:30:00.150Z"
  },
  "meta": {
    "timestamp": "2026-02-06T12:30:00.150Z",
    "request_id": "550e8415-e29b-41d4-a716-446655440000"
  }
}
```

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "Camera with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

---

### 5.4 Speaker API


Speaker(방송장비)는 Device Polymorphic 상속 구조를 따르며, Server(SPEAKER_API)와 FK 관계를 가집니다.

#### 5.4.1 Speaker 목록 조회

**Endpoint**: `GET /api/devices/speakers`

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| page | integer | N | 페이지 번호 (기본값: 1) |
| limit | integer | N | 페이지당 항목 수 (기본값: 20, 최대: 100) |
| server_id | integer | N | 서버 ID 필터 |
| status | string | N | 상태 필터 (ACTIVATED, ERROR, DEACTIVATED) |
| speaker_type | string | N | 스피커 유형 (NORMAL, ADMIN, MONITOR, DEV) |

**Request Example**:
```http
GET /api/devices/speakers?status=ACTIVATED&speaker_type=NORMAL HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Speakers retrieved successfully",
  "data": [
    {
      "id": 101,
      "number_device": 2401,
      "group_device": 0,
      "name_device": "VCS_2401",
      "type_device": "IpSpeaker",
      "version": null,
      "status": "ACTIVATED",
      "is_enable": true,
      "created_at": "2026-01-07T10:00:00.000000",
      "updated_at": "2026-01-07T10:00:00.000000",
      "speaker_type": "NORMAL",
      "description": "1구역 스피커",
      "geolocation": {
        "location": "GOP 3초소 방송실",
        "latitude": 38.1234,
        "longitude": 127.5678,
        "altitude": 245.5
      },
      "server": {
        "id": 1,
        "category_id": 10,
        "name": "방송서버-01",
        "status": "NORMAL",
        "ip_address": "192.168.1.100",
        "port": 8080,
        "hostname": "bcast-srv-01",
        "user_name": "admin",
        "user_password": "password123",
        "threshold_config": {
          "cpu": {"warning": 80, "critical": 95},
          "ram": {"warning": 75, "critical": 90},
          "disk": {"warning": 80, "critical": 95},
          "network": {"warning_mbps": 800, "critical_mbps": 950}
        }
      }
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 35,
    "total_pages": 2
  },
  "meta": {
    "timestamp": "2026-01-07T10:00:00.000Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

**Error Response (422 Validation Error)** - 잘못된 쿼리 파라미터:
```json
{
  "success": false,
  "message": "Validation error",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [
      {"field": "page", "message": "Page must be greater than 0"},
      {"field": "limit", "message": "Limit must be between 1 and 100"}
    ]
  }
}
```

> **Nested Response 규칙**: `server` nested 객체에서 `created_at`, `updated_at` 제외
> **v2.6 추가**: `geolocation` JSONB 필드 추가 (PRD_Speaker_Geolocation.md v1.0)

---

#### 5.4.2 Speaker 상세 조회

**Endpoint**: `GET /api/devices/speakers/{id}`

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| id | integer | Y | Speaker ID |

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Speaker retrieved successfully",
  "data": {
    "id": 101,
    "number_device": 2401,
    "group_device": 0,
    "name_device": "VCS_2401",
    "type_device": "IpSpeaker",
    "version": null,
    "status": "ACTIVATED",
    "is_enable": true,
    "created_at": "2026-01-07T10:00:00.000000",
    "updated_at": "2026-01-07T10:00:00.000000",
    "speaker_type": "NORMAL",
    "description": "1구역 스피커",
    "geolocation": {
      "location": "GOP 3초소 방송실",
      "latitude": 38.1234,
      "longitude": 127.5678,
      "altitude": 245.5
    },
    "server": {
      "id": 1,
      "category_id": 10,
      "name": "방송서버-01",
      "status": "NORMAL",
      "ip_address": "192.168.1.100",
      "port": 8080,
      "hostname": "bcast-srv-01",
      "user_name": "admin",
      "user_password": "password123",
      "threshold_config": {
        "cpu": {"warning": 80, "critical": 95},
        "ram": {"warning": 75, "critical": 90},
        "disk": {"warning": 80, "critical": 95},
        "network": {"warning_mbps": 800, "critical_mbps": 950}
      }
    }
  },
  "meta": {
    "timestamp": "2026-01-07T10:00:00.000Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440001"
  }
}
```

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "Speaker with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

---

#### 5.4.3 Speaker 생성

**Endpoint**: `POST /api/devices/speakers`

**Request Example**:
```http
POST /api/devices/speakers HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "number_device": 2401,
  "name_device": "VCS_2401",
  "type_device": "IpSpeaker",
  "status": "ACTIVATED",
  "speaker_type": "NORMAL",
  "server_id": 1,
  "description": "1구역 스피커",
  "geolocation": {
    "location": "GOP 3초소 방송실",
    "latitude": 38.1234,
    "longitude": 127.5678
  }
}
```

**Request Body**:
```json
{
  "number_device": 2401,
  "group_device": 0,
  "name_device": "VCS_2401",
  "type_device": "IpSpeaker",
  "status": "ACTIVATED",
  "speaker_type": "NORMAL",
  "server_id": 1,
  "description": "1구역 스피커",
  "geolocation": {
    "location": "GOP 3초소 방송실",
    "latitude": 38.1234,
    "longitude": 127.5678,
    "altitude": 245.5
  }
}
```

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| number_device | integer | Y | - | 단말 번호 (NATS device_no 통합) |
| group_device | integer | N | 0 | 그룹 번호 (레거시) |
| name_device | string | Y | - | 장비명 |
| type_device | string | N | IpSpeaker | EnumDeviceType |
| version | string | N | null | 펌웨어 버전 |
| status | string | N | ACTIVATED | EnumDeviceStatus |
| is_enable | boolean | N | true | 장비 활성화 여부 |
| speaker_type | string | N | NORMAL | EnumSpeakerType |
| server_id | integer | N | null | 방송서버 ID (FK) |
| description | string | N | null | 설명 |
| geolocation | object | N | null | 좌표/위치 정보 (JSON) |

**Response (201 Created)**:
```json
{
  "success": true,
  "message": "Speaker created successfully",
  "data": {
    "id": 101,
    "number_device": 2401,
    "group_device": 0,
    "name_device": "VCS_2401",
    "type_device": "IpSpeaker",
    "version": null,
    "status": "ACTIVATED",
    "is_enable": true,
    "created_at": "2026-01-07T10:00:00.000000",
    "updated_at": "2026-01-07T10:00:00.000000",
    "speaker_type": "NORMAL",
    "description": "1구역 스피커",
    "geolocation": {
      "location": "GOP 3초소 방송실",
      "latitude": 38.1234,
      "longitude": 127.5678,
      "altitude": 245.5
    },
    "server": {
      "id": 1,
      "category_id": 10,
      "name": "방송서버-01",
      "status": "NORMAL",
      "ip_address": "192.168.1.100",
      "port": 8080,
      "hostname": "bcast-srv-01",
      "user_name": "admin",
      "user_password": "password123",
      "threshold_config": {
        "cpu": {"warning": 80, "critical": 95},
        "ram": {"warning": 75, "critical": 90},
        "disk": {"warning": 80, "critical": 95},
        "network": {"warning_mbps": 800, "critical_mbps": 950}
      }
    }
  },
  "meta": {
    "timestamp": "2026-01-07T10:00:00.000Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440002"
  }
}
```

**Error Response (422 Validation Error)**:
```json
{
  "success": false,
  "message": "Validation error",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [
      {"field": "number_device", "message": "Field required"},
      {"field": "name_device", "message": "Field required"}
    ]
  }
}
```

**Error Response (404 Not Found)** - server_id가 존재하지 않을 경우:
```json
{
  "success": false,
  "message": "Server with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

---

#### 5.4.4 Speaker 수정 (부분)

**Endpoint**: `PATCH /api/devices/speakers/{id}`

**Request Example**:
```http
PATCH /api/devices/speakers/101 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "name_device": "VCS_2401_Updated",
  "speaker_type": "ADMIN",
  "description": "1구역 관리자 스피커로 변경",
  "geolocation": {
    "location": "GOP 3초소 방송실 (이동)",
    "latitude": 38.1235,
    "longitude": 127.5679,
    "altitude": 246.0
  }
}
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| id | integer | Y | Speaker ID |

**Request Body** (모든 필드 선택):
```json
{
  "name_device": "VCS_2401_Updated",
  "speaker_type": "ADMIN",
  "description": "1구역 관리자 스피커로 변경",
  "geolocation": {
    "location": "GOP 3초소 방송실 (이동)",
    "latitude": 38.1235,
    "longitude": 127.5679,
    "altitude": 246.0
  }
}
```

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| number_device | integer | N | - | 단말 번호 (현재 값 유지) |
| group_device | integer | N | - | 그룹 번호 (현재 값 유지) |
| name_device | string | N | - | 장비명 (현재 값 유지) |
| type_device | string | N | - | EnumDeviceType (현재 값 유지) |
| version | string | N | - | 버전 (현재 값 유지) |
| status | string | N | - | EnumDeviceStatus (현재 값 유지) |
| is_enable | boolean | N | - | 장비 활성화 여부 (현재 값 유지) |
| speaker_type | string | N | - | EnumSpeakerType (현재 값 유지) |
| server_id | integer | N | - | 방송서버 ID (null 허용) (현재 값 유지) |
| description | string | N | - | 설명 (현재 값 유지) |
| geolocation | object | N | - | 좌표/위치 정보 (현재 값 유지) |

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Speaker updated successfully",
  "data": {
    "id": 101,
    "number_device": 2401,
    "group_device": 0,
    "name_device": "VCS_2401_Updated",
    "type_device": "IpSpeaker",
    "version": null,
    "status": "ACTIVATED",
    "is_enable": true,
    "created_at": "2026-01-07T10:00:00.000000",
    "updated_at": "2026-01-07T11:30:00.000000",
    "speaker_type": "ADMIN",
    "description": "1구역 관리자 스피커로 변경",
    "geolocation": {
      "location": "GOP 3초소 방송실 (이동)",
      "latitude": 38.1235,
      "longitude": 127.5679,
      "altitude": 246.0
    },
    "server": {
      "id": 1,
      "category_id": 10,
      "name": "방송서버-01",
      "status": "NORMAL",
      "ip_address": "192.168.1.100",
      "port": 8080,
      "hostname": "bcast-srv-01",
      "user_name": "admin",
      "user_password": "password123",
      "threshold_config": {
        "cpu": {"warning": 80, "critical": 95},
        "ram": {"warning": 75, "critical": 90},
        "disk": {"warning": 80, "critical": 95},
        "network": {"warning_mbps": 800, "critical_mbps": 950}
      }
    }
  },
  "meta": {
    "timestamp": "2026-01-07T11:30:00.000Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440003"
  }
}
```

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "Speaker with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

---

#### 5.4.5 Speaker 수정 (전체)

**Endpoint**: `PUT /api/devices/speakers/{id}`

**Request Example**:
```http
PUT /api/devices/speakers/101 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "number_device": 2401,
  "group_device": 0,
  "name_device": "VCS_2401_Replaced",
  "type_device": "IpSpeaker",
  "status": "ACTIVATED",
  "is_enable": true,
  "speaker_type": "MONITOR",
  "server_id": 2,
  "description": "모니터링 전용 스피커",
  "geolocation": {
    "location": "GOP 본부 상황실",
    "latitude": 38.1300,
    "longitude": 127.5700,
    "altitude": 250.0
  }
}
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| id | integer | Y | Speaker ID |

**Request Body** (전체 업데이트):
```json
{
  "number_device": 2401,
  "group_device": 0,
  "name_device": "VCS_2401_Replaced",
  "type_device": "IpSpeaker",
  "status": "ACTIVATED",
  "is_enable": true,
  "speaker_type": "MONITOR",
  "server_id": 2,
  "description": "모니터링 전용 스피커",
  "geolocation": {
    "location": "GOP 본부 상황실",
    "latitude": 38.1300,
    "longitude": 127.5700,
    "altitude": 250.0
  }
}
```

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| number_device | integer | Y | - | 단말 번호 |
| group_device | integer | N | 0 | 그룹 번호 (레거시) |
| name_device | string | Y | - | 장비명 |
| type_device | string | N | IpSpeaker | EnumDeviceType |
| version | string | N | null | 펌웨어 버전 |
| status | string | N | ACTIVATED | EnumDeviceStatus |
| is_enable | boolean | N | true | 장비 활성화 여부 |
| speaker_type | string | N | NORMAL | EnumSpeakerType |
| server_id | integer | N | null | 방송서버 ID |
| description | string | N | null | 설명 |
| geolocation | object | N | null | 좌표/위치 정보 |

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Speaker replaced successfully",
  "data": {
    "id": 101,
    "number_device": 2401,
    "group_device": 0,
    "name_device": "VCS_2401_Replaced",
    "type_device": "IpSpeaker",
    "version": null,
    "status": "ACTIVATED",
    "is_enable": true,
    "created_at": "2026-01-07T10:00:00.000000",
    "updated_at": "2026-01-07T12:00:00.000000",
    "speaker_type": "MONITOR",
    "description": "모니터링 전용 스피커",
    "geolocation": {
      "location": "GOP 본부 상황실",
      "latitude": 38.1300,
      "longitude": 127.5700,
      "altitude": 250.0
    },
    "server": {
      "id": 2,
      "category_id": 10,
      "name": "방송서버-02",
      "status": "NORMAL",
      "ip_address": "192.168.1.101",
      "port": 8080,
      "hostname": "bcast-srv-02",
      "user_name": "admin",
      "user_password": "password456",
      "threshold_config": {
        "cpu": {"warning": 80, "critical": 95},
        "ram": {"warning": 75, "critical": 90},
        "disk": {"warning": 80, "critical": 95},
        "network": {"warning_mbps": 800, "critical_mbps": 950}
      }
    }
  },
  "meta": {
    "timestamp": "2026-01-07T12:00:00.000Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440004"
  }
}
```

**Error Response (404 Not Found)** - Speaker 없음:
```json
{
  "success": false,
  "message": "Speaker with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

**Error Response (404 Not Found)** - Server 없음:
```json
{
  "success": false,
  "message": "Server with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

---

#### 5.4.6 Speaker 삭제

**Endpoint**: `DELETE /api/devices/speakers/{id}`

**Request Example**:
```http
DELETE /api/devices/speakers/101 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| id | integer | Y | Speaker ID |

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Speaker deleted successfully",
  "data": {
    "id": 101
  },
  "meta": {
    "timestamp": "2026-01-07T12:30:00.000Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440005"
  }
}
```

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "Speaker with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

---

### 5.5 Enclosure API

함체관리장비(Enclosure)는 GOP 현장에 설치되어 환경 모니터링 및 제어를 수행하는 장비입니다.
Device Polymorphic 상속 구조를 따르며, `enclosures` 테이블에 함체 특화 속성을 저장합니다.

**핵심 특성**:
- **도어 상태 모니터링**: `door_status` (CLOSED/OPEN) - 물리적 도어 센서 상태
- **위치 정보**: `geolocation` (JSONB) - GPS 좌표, 설치 위치명
- **알람 임계값**: `threshold_config` (JSONB) - 환경 모니터링 알람 설정
- **제어 기능**: 히터/팬 ON/OFF 제어

> **환경 모니터링 데이터**: 온도, 습도, 전류, 전압, 진동 등 실시간 측정값은 `enclosure_metrics` API를 통해 별도 관리됩니다.
> - PRD 참조: PRD_Enclosure_Metrics_Separation.md v1.0

#### 5.5.1 Enclosure 목록 조회

**Endpoint**: `GET /api/devices/enclosures`

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| page | integer | N | 페이지 번호 (기본값: 1) |
| limit | integer | N | 페이지당 항목 수 (기본값: 20, 최대: 100) |
| door_status | string | N | 도어 상태 필터 (CLOSED/OPEN) |
| status | string | N | 장비 운영 상태 필터 (ACTIVATED/DEACTIVATED/ERROR) |
| name_device | string | N | 장비명 검색 (부분 일치) |

**Request Example**:
```http
GET /api/devices/enclosures?door_status=CLOSED&status=ACTIVATED HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Enclosures retrieved successfully",
  "data": [
    {
      "id": 1,
      "number_device": 101,
      "group_device": 1,
      "name_device": "GOP 3초소 함체",
      "type_device": "IoController",
      "version": "v1.0.0",
      "status": "ACTIVATED",
      "is_enable": true,
      "door_status": "CLOSED",
      "geolocation": {
        "location": "GOP 3초소",
        "latitude": 38.1234,
        "longitude": 127.5678,
        "altitude": 150.0
      },
      "threshold_config": {
        "temp_high": 40.0,
        "temp_low": -10.0,
        "humidity_high": 85.0,
        "humidity_low": 20.0,
        "vibration_threshold": 5.0
      },
      "heater_enabled": false,
      "fan_enabled": false,
      "created_at": "2026-01-08T10:00:00.000000",
      "updated_at": "2026-01-08T10:00:00.000000"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 5,
    "total_pages": 1
  }
}
```

> **Note**: 환경 모니터링 데이터(온도, 습도 등)는 `GET /api/devices/enclosures/{id}/metrics` API를 통해 조회합니다.

**Error Response (422 Validation Error)** - 잘못된 쿼리 파라미터:
```json
{
  "success": false,
  "message": "Validation error",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [
      {"field": "page", "message": "Page must be greater than 0"},
      {"field": "limit", "message": "Limit must be between 1 and 100"}
    ]
  }
}
```

#### 5.5.2 Enclosure 상세 조회

**Endpoint**: `GET /api/devices/enclosures/{id}`

**Path Parameters**:
- `id` (integer, required): 함체 ID

**Response (200 OK)**: 단일 함체 상세 정보 반환

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "Enclosure with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

#### 5.5.3 Enclosure 생성

**Endpoint**: `POST /api/devices/enclosures`

**Request Example**:
```http
POST /api/devices/enclosures HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "number_device": 102,
  "name_device": "GOP 4초소 함체",
  "status": "ACTIVATED",
  "door_status": "CLOSED",
  "geolocation": {
    "location": "GOP 4초소",
    "latitude": 38.1234,
    "longitude": 127.5678
  }
}
```

**Request Body**:
```json
{
  "number_device": 102,
  "name_device": "GOP 4초소 함체",
  "group_device": 1,
  "status": "ACTIVATED",
  "door_status": "CLOSED",
  "geolocation": {
    "location": "GOP 4초소",
    "latitude": 38.2345,
    "longitude": 127.6789
  },
  "threshold_config": {
    "temp_high": 45.0,
    "temp_low": -15.0
  },
  "heater_enabled": false,
  "fan_enabled": false
}
```

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| number_device | integer | Y | - | 장비 번호 |
| name_device | string | Y | - | 장비 이름 |
| group_device | integer | N | 0 | 장치 그룹 번호 (레거시) |
| type_device | string | N | IoController | EnumDeviceType |
| version | string | N | null | 장비 버전 |
| status | string | N | ACTIVATED | EnumDeviceStatus |
| is_enable | boolean | N | true | 장비 활성화 여부 |
| door_status | string | N | CLOSED | EnumDoorStatus |
| geolocation | object | N | null | 위치 정보 (JSONB) |
| threshold_config | object | N | null | 알람 임계값 (JSONB) |
| heater_enabled | boolean | N | false | 히터 활성화 |
| fan_enabled | boolean | N | false | 팬 활성화 |

> **Note**: 환경 모니터링 데이터(온도, 습도 등)는 `POST /api/devices/enclosures/{id}/metrics` API를 통해 별도 저장합니다.

**Response (201 Created)**:
```json
{
  "success": true,
  "message": "Enclosure created successfully",
  "data": {
    "id": 2,
    "number_device": 102,
    "group_device": 1,
    "name_device": "GOP 4초소 함체",
    "type_device": "IoController",
    "version": null,
    "status": "ACTIVATED",
    "is_enable": true,
    "door_status": "CLOSED",
    "geolocation": {
      "location": "GOP 4초소",
      "latitude": 38.2345,
      "longitude": 127.6789
    },
    "threshold_config": {
      "temp_high": 45.0,
      "temp_low": -15.0
    },
    "heater_enabled": false,
    "fan_enabled": false,
    "created_at": "2026-01-08T11:00:00.000000",
    "updated_at": "2026-01-08T11:00:00.000000"
  }
}
```

**Error Response (422 Validation Error)**:
```json
{
  "success": false,
  "message": "Validation error",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [
      {"field": "number_device", "message": "Field required"},
      {"field": "name_device", "message": "Field required"}
    ]
  }
}
```

#### 5.5.4 Enclosure 수정 (부분)

**Endpoint**: `PATCH /api/devices/enclosures/{id}`

**Request Example**:
```http
PATCH /api/devices/enclosures/1 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "name_device": "GOP 3초소 함체 (수정)",
  "door_status": "OPEN",
  "status": "DEACTIVATED"
}
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| id | integer | Y | 함체 ID |

**Request Body** (모든 필드 선택):
```json
{
  "name_device": "GOP 3초소 함체 (수정)",
  "door_status": "OPEN",
  "status": "DEACTIVATED"
}
```

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| number_device | integer | N | - | 장비 번호 (현재 값 유지) |
| name_device | string | N | - | 장비 이름 (현재 값 유지) |
| group_device | integer | N | - | 장치 그룹 번호 (레거시) (현재 값 유지) |
| type_device | string | N | - | EnumDeviceType (현재 값 유지) |
| version | string | N | - | 장비 버전 (현재 값 유지) |
| status | string | N | - | EnumDeviceStatus (현재 값 유지) |
| is_enable | boolean | N | - | 장비 활성화 여부 (현재 값 유지) |
| door_status | string | N | - | EnumDoorStatus (현재 값 유지) |
| geolocation | object | N | - | 위치 정보 (JSONB) (현재 값 유지) |
| threshold_config | object | N | - | 알람 임계값 (JSONB) (현재 값 유지) |
| heater_enabled | boolean | N | - | 히터 활성화 (현재 값 유지) |
| fan_enabled | boolean | N | - | 팬 활성화 (현재 값 유지) |

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Enclosure updated successfully",
  "data": {
    "id": 1,
    "number_device": 101,
    "group_device": 1,
    "name_device": "GOP 3초소 함체 (수정)",
    "type_device": "IoController",
    "version": "v1.0.0",
    "status": "DEACTIVATED",
    "is_enable": true,
    "door_status": "OPEN",
    "geolocation": {
      "location": "GOP 3초소",
      "latitude": 38.1234,
      "longitude": 127.5678
    },
    "threshold_config": null,
    "heater_enabled": false,
    "fan_enabled": false,
    "created_at": "2026-01-08T10:00:00.000000",
    "updated_at": "2026-01-08T11:30:00.000000"
  }
}
```

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "Enclosure with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

#### 5.5.5 Enclosure 수정 (전체)

**Endpoint**: `PUT /api/devices/enclosures/{id}`

**Request Example**:
```http
PUT /api/devices/enclosures/1 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "number_device": 101,
  "name_device": "GOP 3초소 함체 (전체수정)",
  "group_device": 1,
  "type_device": "IoController",
  "version": "v1.1.0",
  "status": "ACTIVATED",
  "is_enable": true,
  "door_status": "CLOSED",
  "geolocation": {
    "location": "GOP 3초소 (수정)",
    "latitude": 38.1234,
    "longitude": 127.5678
  },
  "threshold_config": {
    "temp_high": 45.0,
    "temp_low": -15.0
  },
  "heater_enabled": true,
  "fan_enabled": false
}
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| id | integer | Y | 함체 ID |

전체 필드를 교체합니다. 필수 필드는 반드시 포함해야 합니다.

**Request Body** (전체 업데이트):
```json
{
  "number_device": 101,
  "name_device": "GOP 3초소 함체 (전체수정)",
  "group_device": 1,
  "type_device": "IoController",
  "version": "v1.1.0",
  "status": "ACTIVATED",
  "is_enable": true,
  "door_status": "CLOSED",
  "geolocation": {
    "location": "GOP 3초소 (수정)",
    "latitude": 38.1234,
    "longitude": 127.5678
  },
  "threshold_config": {
    "temp_high": 45.0,
    "temp_low": -15.0
  },
  "heater_enabled": true,
  "fan_enabled": false
}
```

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| number_device | integer | Y | - | 장비 번호 |
| name_device | string | Y | - | 장비 이름 |
| group_device | integer | N | 0 | 장치 그룹 번호 (레거시) |
| type_device | string | N | IoController | EnumDeviceType |
| version | string | N | null | 장비 버전 |
| status | string | N | ACTIVATED | EnumDeviceStatus |
| is_enable | boolean | N | true | 장비 활성화 여부 |
| door_status | string | N | CLOSED | EnumDoorStatus |
| geolocation | object | N | null | 위치 정보 (JSONB) |
| threshold_config | object | N | null | 알람 임계값 (JSONB) |
| heater_enabled | boolean | N | false | 히터 활성화 |
| fan_enabled | boolean | N | false | 팬 활성화 |

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Enclosure replaced successfully",
  "data": {
    "id": 1,
    "number_device": 101,
    "group_device": 1,
    "name_device": "GOP 3초소 함체 (전체수정)",
    "type_device": "IoController",
    "version": "v1.1.0",
    "status": "ACTIVATED",
    "is_enable": true,
    "door_status": "CLOSED",
    "geolocation": {
      "location": "GOP 3초소 (수정)",
      "latitude": 38.1234,
      "longitude": 127.5678
    },
    "threshold_config": {
      "temp_high": 45.0,
      "temp_low": -15.0
    },
    "heater_enabled": true,
    "fan_enabled": false,
    "created_at": "2026-01-08T10:00:00.000000",
    "updated_at": "2026-01-08T12:00:00.000000"
  }
}
```

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "Enclosure with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

#### 5.5.6 Enclosure 삭제

**Endpoint**: `DELETE /api/devices/enclosures/{id}`

**Request Example**:
```http
DELETE /api/devices/enclosures/1 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| id | integer | Y | Enclosure ID |

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Enclosure deleted successfully",
  "data": {
    "id": 1
  }
}
```

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "Enclosure with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

**FK 정책**: Enclosure 삭제 시 Device 레코드도 CASCADE 삭제

#### 5.5.7 도어 상태 업데이트 (특수 엔드포인트)

**Endpoint**: `PATCH /api/devices/enclosures/{id}/status`

외부 센서 장비에서 도어 상태를 업데이트할 때 사용합니다.

> **Note**: 환경 모니터링 데이터(온도, 습도 등)는 `POST /api/devices/enclosures/{id}/metrics` API를 통해 별도 저장합니다.
> - PRD 참조: PRD_Enclosure_Metrics_Separation.md v1.0

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| id | integer | Y | 함체 ID |

**Request Example**:
```http
PATCH /api/devices/enclosures/1/status HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "door_status": "OPEN"
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| door_status | string | N | 도어 물리적 상태 (CLOSED/OPEN) |

**Response Example (200 OK)**:
```json
{
  "success": true,
  "message": "Enclosure status updated successfully",
  "data": {
    "id": 1,
    "number_device": 101,
    "group_device": 1,
    "name_device": "GOP 3초소 함체",
    "type_device": "IoController",
    "version": "v1.0.0",
    "status": "ACTIVATED",
    "is_enable": true,
    "door_status": "OPEN",
    "geolocation": {
      "location": "GOP 3초소",
      "latitude": 38.1234,
      "longitude": 127.5678
    },
    "threshold_config": {
      "temp_high": 45.0,
      "temp_low": -15.0
    },
    "heater_enabled": false,
    "fan_enabled": false,
    "created_at": "2026-01-08T10:00:00.000000",
    "updated_at": "2026-01-08T11:00:00.000000"
  }
}
```

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "Enclosure with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

#### 5.5.8 히터/팬 제어 (특수 엔드포인트)

**Endpoint**: `POST /api/devices/enclosures/{id}/control`

함체 내부 온도 조절을 위한 히터 및 팬을 제어합니다.

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| id | integer | Y | 함체 ID |

**Request Example**:
```http
POST /api/devices/enclosures/1/control HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "heater_enabled": true,
  "fan_enabled": false
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| heater_enabled | boolean | N | 히터 ON/OFF |
| fan_enabled | boolean | N | 팬 ON/OFF |

**Response Example (200 OK)**:
```json
{
  "success": true,
  "message": "Enclosure control updated successfully",
  "data": {
    "id": 1,
    "number_device": 101,
    "group_device": 1,
    "name_device": "GOP 3초소 함체",
    "type_device": "IoController",
    "version": "v1.0.0",
    "status": "ACTIVATED",
    "is_enable": true,
    "door_status": "CLOSED",
    "geolocation": {
      "location": "GOP 3초소",
      "latitude": 38.1234,
      "longitude": 127.5678
    },
    "threshold_config": {
      "temp_high": 45.0,
      "temp_low": -15.0
    },
    "heater_enabled": true,
    "fan_enabled": false,
    "created_at": "2026-01-08T10:00:00.000000",
    "updated_at": "2026-01-08T11:30:00.000000"
  }
}
```

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "Enclosure with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

#### 5.5.9 Enclosure 메트릭 저장 *(v2.9 신규)*

> **PRD 참조**: PRD_Enclosure_Metrics_Separation.md v1.0

함체의 환경 모니터링 메트릭 데이터를 시계열로 저장합니다. 실시간 측정값은 `enclosure_metrics` 테이블에 별도 저장됩니다.

**Endpoint**: `POST /api/devices/enclosures/{enclosure_id}/metrics`

**Path Parameters**:
- `enclosure_id` (integer, required): Enclosure ID

**Request Body**:
```json
{
  "temperature": 25.5,
  "humidity": 45.0,
  "current": 2.5,
  "voltage": 220.0,
  "vibration": 10,
  "ups_battery_level": 85,
  "ups_charging": true,
  "detail": {
    "door_open_count": 3,
    "last_maintenance": "2026-01-10"
  }
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| temperature | number | N | 온도 (°C) |
| humidity | number | N | 습도 (%) |
| current | number | N | 전류 (A) |
| voltage | number | N | 전압 (V) |
| vibration | integer | N | 진동 레벨 (0-100) |
| ups_battery_level | integer | N | UPS 배터리 잔량 (%) |
| ups_charging | boolean | N | UPS 충전 중 여부 |
| detail | object | N | 추가 상세 정보 (JSONB) |

**Response (201 Created)**:
```json
{
  "success": true,
  "message": "Enclosure metric saved successfully",
  "data": {
    "id": 1,
    "enclosure_id": 1,
    "temperature": "25.5",
    "humidity": "45.0",
    "current": "2.5",
    "voltage": "220.0",
    "vibration": 10,
    "ups_battery_level": 85,
    "ups_charging": true,
    "detail": {
      "door_open_count": 3,
      "last_maintenance": "2026-01-10"
    },
    "created_at": "2026-01-15T10:30:00.123456"
  },
  "threshold_exceeded": [
    {
      "field": "temperature",
      "value": 25.5,
      "threshold": 25.0,
      "type": "HIGH"
    }
  ]
}
```

**Response 특이사항**:
- `threshold_exceeded`: Enclosure의 `threshold_config`에 설정된 임계값 초과 시 경고 정보 반환
- `type`: `HIGH` (상한 초과) 또는 `LOW` (하한 미만)

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "Enclosure with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

#### 5.5.10 Enclosure 메트릭 목록 조회 *(v2.9 신규)*

함체의 환경 모니터링 메트릭 이력을 조회합니다.

**Endpoint**: `GET /api/devices/enclosures/{enclosure_id}/metrics`

**Path Parameters**:
- `enclosure_id` (integer, required): Enclosure ID

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| limit | integer | N | 조회할 최대 개수 (기본값: 100, 최대: 1000) |
| start_time | datetime | N | 시작 시간 필터 (ISO 8601) |
| end_time | datetime | N | 종료 시간 필터 (ISO 8601) |

**Request Example**:
```http
GET /api/devices/enclosures/1/metrics?start_time=2026-01-15T00:00:00Z&limit=50 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Enclosure metrics retrieved successfully",
  "data": [
    {
      "id": 10,
      "enclosure_id": 1,
      "temperature": "25.5",
      "humidity": "45.0",
      "current": "2.5",
      "voltage": "220.0",
      "vibration": 10,
      "ups_battery_level": 85,
      "ups_charging": true,
      "detail": null,
      "created_at": "2026-01-15T10:30:00.123456"
    },
    {
      "id": 9,
      "enclosure_id": 1,
      "temperature": "24.8",
      "humidity": "46.2",
      "current": "2.4",
      "voltage": "219.5",
      "vibration": 8,
      "ups_battery_level": 84,
      "ups_charging": true,
      "detail": null,
      "created_at": "2026-01-15T10:00:00.123456"
    }
  ]
}
```

**Response 특이사항**:
- 결과는 `created_at` 기준 **내림차순** (최신순) 정렬
- 시간 범위 필터 지원: `start_time` ~ `end_time`

#### 5.5.11 Enclosure 최신 메트릭 조회 *(v2.9 신규)*

함체의 가장 최근 환경 모니터링 메트릭을 조회합니다.

**Endpoint**: `GET /api/devices/enclosures/{enclosure_id}/metrics/latest`

**Path Parameters**:
- `enclosure_id` (integer, required): Enclosure ID

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Latest enclosure metric retrieved successfully",
  "data": {
    "id": 10,
    "enclosure_id": 1,
    "temperature": "25.5",
    "humidity": "45.0",
    "current": "2.5",
    "voltage": "220.0",
    "vibration": 10,
    "ups_battery_level": 85,
    "ups_charging": true,
    "detail": null,
    "created_at": "2026-01-15T10:30:00.123456"
  }
}
```

**Error Response (404 Not Found)** - 메트릭이 없는 경우:
```json
{
  "success": false,
  "message": "No metrics found for enclosure 1",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

#### 5.5.12 Enclosure 메트릭 삭제 *(v2.9 신규)*

함체의 환경 모니터링 메트릭을 삭제합니다.

**Endpoint**: `DELETE /api/devices/enclosures/{enclosure_id}/metrics`

**Path Parameters**:
- `enclosure_id` (integer, required): Enclosure ID

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| before_date | datetime | N | 이 날짜 이전 메트릭만 삭제 (ISO 8601) |

**Request Example**:
```http
DELETE /api/devices/enclosures/1/metrics?before_date=2026-01-01T00:00:00Z HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Deleted 150 metrics",
  "data": {
    "deleted_count": 150
  }
}
```

**주의사항**:
- `before_date` 미지정 시 해당 Enclosure의 **모든 메트릭** 삭제
- 삭제된 데이터는 복구 불가

---

### 5.6 DeviceGroup API

디바이스 그룹은 여러 디바이스(Controller, Sensor, Camera, Speaker, Enclosure 등)를 논리적으로 묶어 관리하는 기능입니다.
- N:N 관계: 하나의 디바이스는 여러 그룹에 속할 수 있고, 하나의 그룹은 여러 디바이스를 포함할 수 있습니다.
- 폴리모픽 응답: 그룹 상세 조회 시 디바이스 타입별로 다른 필드를 반환합니다.

#### 5.6.1 DeviceGroup 목록 조회

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

**Error Response (422 Validation Error)** - 잘못된 쿼리 파라미터:
```json
{
  "success": false,
  "message": "Validation error",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [
      {"field": "page", "message": "Page must be greater than 0"},
      {"field": "limit", "message": "Limit must be between 1 and 100"}
    ]
  }
}
```

---

#### 5.6.2 DeviceGroup 상세 조회 (폴리모픽 디바이스 목록 포함)

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
    "device_count": 5,
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
        "is_enable": true,
        "ip_address": "192.168.1.100",
        "ip_port": 8001,
        "geolocation": null
      },
      {
        "id": 101,
        "number_device": 1,
        "group_device": 1, // (Deprecated 예정, 레거시)
        "name_device": "Sensor-A-1",
        "type_device": "Multi",
        "version": "v1.5.0",
        "status": "ACTIVATED",
        "is_enable": true,
        "controller_id": 1,
        "geolocation": null
      },
      {
        "id": 201,
        "number_device": 1,
        "group_device": 1, // (Deprecated 예정, 레거시)
        "name_device": "Camera-A-1",
        "type_device": "IpCamera",
        "version": "v1.0.0",
        "status": "ACTIVATED",
        "is_enable": true,
        "ip_address": "192.168.1.200",
        "ip_port": 80,
        "user_name": "admin",
        "user_password": "admin1234",
        "mode": "RTSP",
        "camera_category": "PTZ",
        "is_record": true,
        "urls": {
          "streams": {
            "rtsp": {"main": "rtsp://192.168.1.200:554/stream1"}
          }
        },
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
      },
      {
        "id": 301,
        "number_device": 2401,
        "group_device": 1,
        "name_device": "VCS_2401",
        "type_device": "IpSpeaker",
        "version": "v1.0.0",
        "status": "ACTIVATED",
        "is_enable": true,
        "speaker_type": "NORMAL",
        "server_id": 1,
        "description": "1구역 스피커",
        "geolocation": {
          "location": "GOP 1구역 스피커",
          "latitude": 38.1234,
          "longitude": 127.5678
        }
      },
      {
        "id": 401,
        "number_device": 3001,
        "group_device": 1,
        "name_device": "Enclosure-A-1",
        "type_device": "Enclosure",
        "version": "v1.0.0",
        "status": "ACTIVATED",
        "is_enable": true,
        "door_status": "CLOSED",
        "heater_enabled": false,
        "fan_enabled": false,
        "threshold_config": {
          "temperature": {"warning": 40, "critical": 50}
        },
        "geolocation": {
          "location": "GOP 1구역 함체",
          "latitude": 38.1234,
          "longitude": 127.5678
        }
      },
      {
        "id": 501,
        "number_device": 5001,
        "group_device": 1,
        "name_device": "Lamp-A-1",
        "type_device": "Lamp",
        "version": "v1.0.0",
        "status": "ACTIVATED",
        "is_enable": true,
        "ip_address": "192.168.1.109",
        "ip_port": 80,
        "description": "GOP 1구역 전방 경광등",
        "geolocation": {
          "location": "GOP 1구역 경광등",
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
> - **공통 필드**: `id`, `number_device`, `group_device`, `name_device`, `type_device`, `version`, `status`, `is_enable`
> - **Controller 추가 필드**: `ip_address`, `ip_port`, `geolocation`
> - **Sensor 추가 필드**: `controller_id`, `geolocation`
> - **Camera 추가 필드**: `ip_address`, `ip_port`, `user_name`, `user_password`, `urls`, `mode`, `camera_category`, `is_record`, `hardware_spec`, `geolocation`
> - **Speaker 추가 필드**: `speaker_type`, `server_id`, `description`, `geolocation`
> - **Enclosure 추가 필드**: `door_status`, `heater_enabled`, `fan_enabled`, `threshold_config`, `geolocation`
> - **Lamp 추가 필드**: `ip_address`, `ip_port`, `description`, `geolocation` *(v3.4 신규)*

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

#### 5.6.3 DeviceGroup 생성

**Endpoint**: `POST /api/devices/groups`

**Request Example**:
```http
POST /api/devices/groups HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "name": "GOP 3구역",
  "description": "GOP 3구역 장비 그룹"
}
```

**Request Body**:
```json
{
  "name": "GOP 3구역",
  "description": "GOP 3구역 장비 그룹"
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| name | string | Y | 그룹명 (UNIQUE) |
| description | string | N | 그룹 설명 |

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

**Error Response (422 Validation Error)**:
```json
{
  "success": false,
  "message": "Validation error",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [
      {"field": "name", "message": "Field required"}
    ]
  }
}
```

---

#### 5.6.4 DeviceGroup 수정 (부분)

**Endpoint**: `PATCH /api/devices/groups/{id}`

**Request Example**:
```http
PATCH /api/devices/groups/3 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "description": "GOP 3구역 장비 그룹 - 수정됨"
}
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| id | integer | Y | DeviceGroup ID |

**Request Body** (부분 업데이트):
```json
{
  "description": "GOP 3구역 장비 그룹 - 수정됨"
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| name | string | N | 그룹 이름 |
| description | string | N | 그룹 설명 |

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

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "DeviceGroup with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

---

#### 5.6.5 DeviceGroup 수정 (전체)

**Endpoint**: `PUT /api/devices/groups/{id}`

**Request Example**:
```http
PUT /api/devices/groups/3 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "name": "GOP 3구역 - 전체수정",
  "description": "GOP 3구역 장비 그룹 - 전체 수정됨"
}
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| id | integer | Y | DeviceGroup ID |

**Request Body** (전체 업데이트):
```json
{
  "name": "GOP 3구역 - 전체수정",
  "description": "GOP 3구역 장비 그룹 - 전체 수정됨"
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| name | string | Y | 그룹 이름 |
| description | string | N | 그룹 설명 |

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

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "DeviceGroup with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

---

#### 5.6.6 DeviceGroup 삭제

**Endpoint**: `DELETE /api/devices/groups/{id}`

**Request Example**:
```http
DELETE /api/devices/groups/3 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| id | integer | Y | DeviceGroup ID |

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

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "DeviceGroup with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

---

#### 5.6.7 디바이스 그룹에 디바이스 할당

**Endpoint**: `POST /api/devices/groups/{id}/devices`

**Request Example**:
```http
POST /api/devices/groups/1/devices HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "device_ids": [1, 2, 3]
}
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| id | integer | Y | DeviceGroup ID |

**Request Body**:
```json
{
  "device_ids": [1, 2, 3]
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| device_ids | array[integer] | Y | 할당할 디바이스 ID 목록 |

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

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "DeviceGroup with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

---

#### 5.6.8 디바이스 그룹에서 디바이스 제거

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

### 5.7 Camera Preset API

카메라의 프리셋(Preset)을 관리합니다. PTZ 카메라의 사전 정의된 위치/각도 설정을 저장하고 관리합니다.

**계층 구조**: `Camera` → `CameraPreset` → `ROI` → `XyPoint`

#### 5.7.1 CameraPreset 목록 조회

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
  },
  "meta": {
    "timestamp": "2025-01-10T10:00:00.000Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
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
  },
  "meta": {
    "timestamp": "2025-01-10T10:00:00.000Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440001"
  }
}
```

---

#### 5.7.2 CameraPreset 상세 조회 (ROI 포함)

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
  },
  "meta": {
    "timestamp": "2025-01-10T10:00:00.000Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440002"
  }
}
```

---

#### 5.7.3 CameraPreset 생성

**Endpoint**: `POST /api/devices/cameras/{camera_id}/presets`

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| camera_id | integer | Y | 카메라 ID |

**Request Example**:
```http
POST /api/devices/cameras/201/presets HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "preset_index": 1,
  "preset_name": "입구 정면",
  "touring_time": 15
}
```

**Request Body**:
```json
{
  "preset_index": 1,
  "preset_name": "입구 정면",
  "touring_time": 15
}
```

**Request Body 필드 설명**:
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| preset_index | integer | Y | 프리셋 인덱스 (카메라 내 고유) |
| preset_name | string | Y | 프리셋 이름 |
| touring_time | integer | N | 투어링 시간 (초) |

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
  },
  "meta": {
    "timestamp": "2025-01-10T10:00:00.000Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

**Error Response** (409 Conflict - 중복 preset_index):
```json
{
  "success": false,
  "message": "Preset with index 1 already exists for this camera",
  "error": {
    "code": "CONFLICT",
    "details": "preset_index must be unique within the same camera"
  }
}
```

**Error Response (422 Validation Error)**:
```json
{
  "success": false,
  "message": "Validation error",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [
      {"field": "preset_index", "message": "Field required"},
      {"field": "preset_name", "message": "Field required"}
    ]
  }
}
```

---

#### 5.7.4 CameraPreset 수정 (PATCH)

**Endpoint**: `PATCH /api/devices/cameras/{camera_id}/presets/{preset_id}`

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| camera_id | integer | Y | 카메라 ID |
| preset_id | integer | Y | 프리셋 ID |

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
  },
  "meta": {
    "timestamp": "2025-01-10T10:30:00.000Z",
    "request_id": "550e8401-e29b-41d4-a716-446655440000"
  }
}
```

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "CameraPreset with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

---

#### 5.7.5 CameraPreset 수정 (PUT - 전체)

**Endpoint**: `PUT /api/devices/cameras/{camera_id}/presets/{preset_id}`

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| camera_id | integer | Y | 카메라 ID |
| preset_id | integer | Y | 프리셋 ID |

**Request Body** (모든 필드 필수):
```json
{
  "preset_index": 1,
  "preset_name": "입구 정면 - 전체 수정",
  "touring_time": 25
}
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Camera preset replaced successfully",
  "data": {
    "id": 1,
    "camera_id": 201,
    "camera_name": "Camera-A-1",
    "preset_index": 1,
    "preset_name": "입구 정면 - 전체 수정",
    "touring_time": 25,
    "roi_count": 2,
    "created_at": "2025-01-01T00:00:00.000Z",
    "updated_at": "2025-01-10T11:00:00.000Z"
  },
  "meta": {
    "timestamp": "2025-01-10T11:00:00.000Z",
    "request_id": "550e8402-e29b-41d4-a716-446655440000"
  }
}
```

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "CameraPreset with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

---

#### 5.7.6 CameraPreset 삭제

**Endpoint**: `DELETE /api/devices/cameras/{camera_id}/presets/{preset_id}`

**Request Example**:
```http
DELETE /api/devices/cameras/202/presets/3 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| camera_id | integer | Y | 카메라 ID |
| preset_id | integer | Y | 프리셋 ID |

> **Note**: CASCADE 삭제로 인해 하위 ROI 및 XyPoint도 함께 삭제됩니다.

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Camera preset deleted successfully",
  "data": null,
  "meta": {
    "timestamp": "2025-01-10T11:30:00.000Z",
    "request_id": "550e8403-e29b-41d4-a716-446655440000"
  }
}
```

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "CameraPreset with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

---

### 5.8 ROI API

프리셋 내 관심 영역(Region of Interest)을 관리합니다. ROI는 영상 내 다각형 영역을 정의합니다.

#### 5.8.1 ROI 목록 조회

**Endpoint**: `GET /api/presets/{preset_id}/rois`

**Path Parameters**:
- `preset_id` (int, required): 프리셋 ID

**Query Parameters**:
- `include_points` (bool, optional): Points 정보 포함 여부 (기본값: false)
- `page` (int, optional): 페이지 번호 (기본값: 1)
- `limit` (int, optional): 페이지당 항목 수 (기본값: 10, 최대: 100)

**Request Example**:
```http
GET /api/presets/1/rois?include_points=true HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

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
  },
  "meta": {
    "timestamp": "2025-01-10T10:00:00.000Z",
    "request_id": "550e8410-e29b-41d4-a716-446655440000"
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
  },
  "meta": {
    "timestamp": "2025-01-10T10:00:00.000Z",
    "request_id": "550e8411-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 5.8.2 ROI 상세 조회 (Points 포함)

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
  },
  "meta": {
    "timestamp": "2025-01-10T10:00:00.000Z",
    "request_id": "550e8412-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 5.8.3 ROI 생성 (Points 포함)

**Endpoint**: `POST /api/presets/{preset_id}/rois`

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| preset_id | integer | Y | 프리셋 ID |

**Request Example**:
```http
POST /api/presets/1/rois HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "name": "새로운 감시 영역",
  "resolution_width": 1920.0,
  "resolution_height": 1080.0,
  "is_enable": true,
  "points": [
    {"x": 0.1, "y": 0.1, "order": 0},
    {"x": 0.9, "y": 0.1, "order": 1},
    {"x": 0.9, "y": 0.9, "order": 2},
    {"x": 0.1, "y": 0.9, "order": 3}
  ]
}
```

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

**Request Body 필드 설명**:
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| name | string | Y | ROI 이름 |
| resolution_width | float | N | 해상도 너비 (기본값: 1920.0) |
| resolution_height | float | N | 해상도 높이 (기본값: 1080.0) |
| is_enable | boolean | N | 활성화 여부 (기본값: true) |
| points | array | N | 다각형 꼭지점 배열 |
| points[].x | float | Y | X 좌표 (0.0~1.0 정규화) |
| points[].y | float | Y | Y 좌표 (0.0~1.0 정규화) |
| points[].order | integer | Y | 꼭지점 순서 |

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
  },
  "meta": {
    "timestamp": "2025-01-10T10:00:00.000Z",
    "request_id": "550e8413-e29b-41d4-a716-446655440000"
  }
}
```

**Error Response (422 Validation Error)**:
```json
{
  "success": false,
  "message": "Validation error",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [
      {"field": "name", "message": "Field required"}
    ]
  }
}
```

---

#### 5.8.4 ROI 수정 (PATCH)

**Endpoint**: `PATCH /api/presets/{preset_id}/rois/{roi_id}`

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| preset_id | integer | Y | 프리셋 ID |
| roi_id | integer | Y | ROI ID |

**Request Body** (부분 업데이트):
```json
{
  "name": "감시 영역 - 수정",
  "is_enable": false
}
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "ROI updated successfully",
  "data": {
    "id": 1,
    "preset_id": 1,
    "name": "감시 영역 - 수정",
    "resolution_width": 1920.0,
    "resolution_height": 1080.0,
    "is_enable": false,
    "point_count": 4,
    "created_at": "2025-01-01T00:00:00.000Z",
    "updated_at": "2025-01-10T11:00:00.000Z"
  },
  "meta": {
    "timestamp": "2025-01-10T11:00:00.000Z",
    "request_id": "550e8414-e29b-41d4-a716-446655440000"
  }
}
```

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "ROI with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

---

#### 5.8.5 ROI 수정 (PUT - 전체)

**Endpoint**: `PUT /api/presets/{preset_id}/rois/{roi_id}`

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| preset_id | integer | Y | 프리셋 ID |
| roi_id | integer | Y | ROI ID |

**Request Body** (모든 필드 필수):
```json
{
  "name": "감시 영역 - 전체 수정",
  "resolution_width": 1280.0,
  "resolution_height": 720.0,
  "is_enable": true
}
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "ROI replaced successfully",
  "data": {
    "id": 1,
    "preset_id": 1,
    "name": "감시 영역 - 전체 수정",
    "resolution_width": 1280.0,
    "resolution_height": 720.0,
    "is_enable": true,
    "point_count": 4,
    "created_at": "2025-01-01T00:00:00.000Z",
    "updated_at": "2025-01-10T12:00:00.000Z"
  },
  "meta": {
    "timestamp": "2025-01-10T12:00:00.000Z",
    "request_id": "550e8415-e29b-41d4-a716-446655440000"
  }
}
```

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "ROI with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

---

#### 5.8.6 ROI 삭제

**Endpoint**: `DELETE /api/presets/{preset_id}/rois/{roi_id}`

**Request Example**:
```http
DELETE /api/presets/1/rois/2 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| preset_id | integer | Y | 프리셋 ID |
| roi_id | integer | Y | ROI ID |

> **Note**: CASCADE 삭제로 인해 하위 XyPoint도 함께 삭제됩니다.

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "ROI deleted successfully",
  "data": null,
  "meta": {
    "timestamp": "2025-01-10T12:30:00.000Z",
    "request_id": "550e8416-e29b-41d4-a716-446655440000"
  }
}
```

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "ROI with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

---

### 5.9 XyPoint API

ROI 다각형의 꼭지점 좌표를 관리합니다. 좌표는 정규화된 값(0.0~1.0) 또는 픽셀 좌표를 사용할 수 있습니다.

#### 5.9.1 XyPoint 목록 조회

**Endpoint**: `GET /api/rois/{roi_id}/points`

**Path Parameters**:
- `roi_id` (int, required): ROI ID

**Request Example**:
```http
GET /api/rois/1/points HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

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
  },
  "meta": {
    "timestamp": "2025-01-10T10:00:00.000Z",
    "request_id": "550e8420-e29b-41d4-a716-446655440000"
  }
}
```

---

#### 5.9.2 XyPoint 생성

**Endpoint**: `POST /api/rois/{roi_id}/points`

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| roi_id | integer | Y | ROI ID |

**Request Example**:
```http
POST /api/rois/1/points HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "x": 0.5,
  "y": 0.5,
  "order": 4
}
```

**Request Body**:
```json
{
  "x": 0.5,
  "y": 0.5,
  "order": 4
}
```

**Request Body 필드 설명**:
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| x | float | Y | X 좌표 (0.0~1.0 정규화) |
| y | float | Y | Y 좌표 (0.0~1.0 정규화) |
| order | integer | Y | 꼭지점 순서 |

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
  },
  "meta": {
    "timestamp": "2025-01-10T10:00:00.000Z",
    "request_id": "550e8421-e29b-41d4-a716-446655440000"
  }
}
```

**Error Response (422 Validation Error)**:
```json
{
  "success": false,
  "message": "Validation error",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [
      {"field": "x", "message": "Field required"},
      {"field": "y", "message": "Field required"},
      {"field": "order", "message": "Field required"}
    ]
  }
}
```

---

#### 5.9.3 XyPoint 일괄 수정 (전체 교체)

**Endpoint**: `PUT /api/rois/{roi_id}/points`

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| roi_id | integer | Y | ROI ID |

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
  },
  "meta": {
    "timestamp": "2025-01-10T10:30:00.000Z",
    "request_id": "550e8422-e29b-41d4-a716-446655440000"
  }
}
```

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "ROI with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

---

#### 5.9.4 XyPoint 삭제

**Endpoint**: `DELETE /api/rois/{roi_id}/points/{point_id}`

**Request Example**:
```http
DELETE /api/rois/1/points/5 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| roi_id | integer | Y | ROI ID |
| point_id | integer | Y | Point ID |

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Point deleted successfully",
  "data": null,
  "meta": {
    "timestamp": "2025-01-10T11:00:00.000Z",
    "request_id": "550e8423-e29b-41d4-a716-446655440000"
  }
}
```

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "XyPoint not found",
  "error": {
    "code": "NOT_FOUND",
    "details": "XyPoint with id 999 not found"
  }
}
```

---

### 5.10 FileGroup API


FileGroup은 방송음원 파일풀을 관리하는 독립 리소스입니다.

#### 5.10.1 FileGroup 목록 조회

**Endpoint**: `GET /api/file-groups`

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| page | integer | N | 페이지 번호 (기본값: 1) |
| limit | integer | N | 페이지당 항목 수 (기본값: 20, 최대: 100) |
| server_id | integer | N | 서버 ID 필터 |

**Request Example**:
```http
GET /api/file-groups?server_id=1 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "FileGroups retrieved successfully",
  "data": [
    {
      "id": 1,
      "server_id": 1,
      "group_id": 2,
      "group_name": "화재경보",
      "files": ["music01.mp3", "music02.mp3"],
      "created_at": "2026-01-07T10:00:00.000000",
      "updated_at": "2026-01-07T10:00:00.000000"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 5,
    "total_pages": 1
  }
}
```

**Error Response (422 Validation Error)** - 잘못된 쿼리 파라미터:
```json
{
  "success": false,
  "message": "Validation error",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [
      {"field": "page", "message": "Page must be greater than 0"},
      {"field": "limit", "message": "Limit must be between 1 and 100"}
    ]
  }
}
```

#### 5.10.2 FileGroup 상세 조회

**Endpoint**: `GET /api/file-groups/{id}`

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| id | integer | Y | FileGroup ID |

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "FileGroup retrieved",
  "data": {
    "id": 1,
    "server_id": 1,
    "group_id": 2,
    "group_name": "화재경보",
    "files": ["music01.mp3", "music02.mp3"],
    "created_at": "2026-01-07T10:00:00.000000",
    "updated_at": "2026-01-07T10:00:00.000000"
  }
}
```

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "FileGroup with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

---

#### 5.10.3 FileGroup 생성

**Endpoint**: `POST /api/file-groups`

**Request Example**:
```http
POST /api/file-groups HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "server_id": 1,
  "group_id": 2,
  "group_name": "화재경보",
  "files": ["music01.mp3", "music02.mp3"]
}
```

**Request Body**:
```json
{
  "server_id": 1,
  "group_id": 2,
  "group_name": "화재경보",
  "files": ["music01.mp3", "music02.mp3"]
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| server_id | integer | Y | 방송서버 ID (FK) |
| group_id | integer | Y | 방송서버의 파일그룹 ID |
| group_name | string | Y | 그룹명 |
| files | array[string] | N | 파일 목록 (JSONB) |

**Constraint**: `UNIQUE(server_id, group_id)`

**Response (201 Created)**:
```json
{
  "success": true,
  "message": "FileGroup created",
  "data": {
    "id": 1,
    "server_id": 1,
    "group_id": 2,
    "group_name": "화재경보",
    "files": ["music01.mp3", "music02.mp3"],
    "created_at": "2026-01-07T10:00:00.000000",
    "updated_at": "2026-01-07T10:00:00.000000"
  }
}
```

**Error Response (404 Not Found)** - Server가 없는 경우:
```json
{
  "success": false,
  "message": "Server with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

**Error Response (409 Conflict)** - 중복 생성 시도:
```json
{
  "success": false,
  "message": "Resource already exists",
  "error": {
    "code": "CONFLICT",
    "details": "FileGroup with server_id=1 and group_id=2 already exists"
  }
}
```

**Error Response (422 Validation Error)**:
```json
{
  "success": false,
  "message": "Validation error",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [
      {"field": "server_id", "message": "Field required"},
      {"field": "group_id", "message": "Field required"}
    ]
  }
}
```

---

#### 5.10.4 FileGroup 수정 (부분)

**Endpoint**: `PATCH /api/file-groups/{id}`

**Request Example**:
```http
PATCH /api/file-groups/2 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "group_name": "비상경보",
  "files": ["alarm01.mp3", "alarm02.mp3", "alarm03.mp3"]
}
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| id | integer | Y | FileGroup ID |

**Request Body** (모든 필드 선택):
```json
{
  "group_name": "비상경보",
  "files": ["alarm01.mp3", "alarm02.mp3", "alarm03.mp3"]
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| group_name | string | N | 그룹명 |
| files | array[string] | N | 파일 목록 (JSONB) |

> **Note**: `server_id`, `group_id`는 PATCH로 수정 불가 (UNIQUE 제약 보호)

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "FileGroup updated",
  "data": {
    "id": 1,
    "server_id": 1,
    "group_id": 2,
    "group_name": "비상경보",
    "files": ["alarm01.mp3", "alarm02.mp3", "alarm03.mp3"],
    "created_at": "2026-01-07T10:00:00.000000",
    "updated_at": "2026-01-07T11:30:00.000000"
  }
}
```

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "FileGroup with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

---

#### 5.10.5 FileGroup 수정 (전체)

**Endpoint**: `PUT /api/file-groups/{id}`

**Request Example**:
```http
PUT /api/file-groups/2 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "server_id": 1,
  "group_id": 2,
  "group_name": "긴급대피안내",
  "files": ["evacuation01.mp3", "evacuation02.mp3"]
}
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| id | integer | Y | FileGroup ID |

**Request Body** (모든 필드 필수):
```json
{
  "server_id": 1,
  "group_id": 2,
  "group_name": "긴급대피안내",
  "files": ["evacuation01.mp3", "evacuation02.mp3"]
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| server_id | integer | Y | 방송서버 ID (FK) |
| group_id | integer | Y | 방송서버의 파일그룹 ID |
| group_name | string | Y | 그룹명 |
| files | array[string] | N | 파일 목록 (미제공 시 null) |

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "FileGroup replaced",
  "data": {
    "id": 1,
    "server_id": 1,
    "group_id": 2,
    "group_name": "긴급대피안내",
    "files": ["evacuation01.mp3", "evacuation02.mp3"],
    "created_at": "2026-01-07T10:00:00.000000",
    "updated_at": "2026-01-07T12:00:00.000000"
  }
}
```

**Error Response (404 Not Found)** - FileGroup 없음:
```json
{
  "success": false,
  "message": "FileGroup with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

**Error Response (404 Not Found)** - 변경할 Server 없음:
```json
{
  "success": false,
  "message": "Server with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

---

#### 5.10.6 FileGroup 삭제

**Endpoint**: `DELETE /api/file-groups/{id}`

**Request Example**:
```http
DELETE /api/file-groups/2 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| id | integer | Y | FileGroup ID |

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "FileGroup deleted",
  "data": {
    "id": 1
  }
}
```

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "FileGroup with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

**FK 정책**: Server 삭제 시 FileGroup CASCADE 삭제

---

### 5.11 Lamp API

> **v3.4 신규**: PRD_Lamp_Device.md v1.1 참조
> 경광등(Lamp) 장비 CRUD API. Device Joined Table Inheritance 구조.

**리소스 구조**:
```
/api/devices/lamps           - Lamp 목록/생성
/api/devices/lamps/{id}      - Lamp 상세/수정/삭제
```

#### 5.11.1 Lamp 목록 조회

**Endpoint**: `GET /api/devices/lamps`

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| page | integer | N | 1 | 페이지 번호 |
| limit | integer | N | 20 | 페이지당 항목 수 (max: 100) |
| status | string | N | - | EnumDeviceStatus 필터 (ACTIVATED/DEACTIVATED/ERROR) |
| is_enable | boolean | N | - | 활성화 여부 필터 |

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Lamp 목록 조회 성공",
  "data": [
    {
      "id": 501,
      "number_device": 5001,
      "group_device": 0,
      "name_device": "Lamp-A-1",
      "type_device": "Lamp",
      "version": "v1.0.0",
      "status": "ACTIVATED",
      "is_enable": true,
      "ip_address": "192.168.1.109",
      "ip_port": 80,
      "user_name": "admin",
      "description": "GOP 1구역 전방 경광등",
      "geolocation": {
        "location": "GOP 1구역 전방 초소",
        "latitude": 38.1234,
        "longitude": 127.5678,
        "altitude": 245.5
      },
      "device_groups": [
        {"id": 1, "name": "GOP 1구역", "description": "GOP 1구역 장비 그룹", "device_count": 5}
      ],
      "created_at": "2026-01-26T10:00:00.000Z",
      "updated_at": "2026-01-26T10:00:00.000Z"
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

> **참고**: Response에 `user_password`는 보안상 제외됩니다.

#### 5.11.2 Lamp 상세 조회

**Endpoint**: `GET /api/devices/lamps/{id}`

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| id | integer | Y | Lamp ID |

**Response (200 OK)**: 목록 조회와 동일한 단일 객체 구조

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "Lamp with id 999 not found",
  "error": {"code": "NOT_FOUND", "details": null}
}
```

#### 5.11.3 Lamp 생성

**Endpoint**: `POST /api/devices/lamps`

**Request Body**:
```json
{
  "number_device": 5001,
  "group_device": 0,
  "name_device": "Lamp-A-1",
  "type_device": "Lamp",
  "version": "v1.0.0",
  "status": "ACTIVATED",
  "is_enable": true,
  "ip_address": "192.168.1.109",
  "ip_port": 80,
  "user_name": "admin",
  "user_password": "lamp1234",
  "description": "GOP 1구역 전방 경광등",
  "geolocation": {
    "location": "GOP 1구역 전방 초소",
    "latitude": 38.1234,
    "longitude": 127.5678,
    "altitude": 245.5
  }
}
```

**Request Body 필드**:
| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| number_device | integer | Y | - | 장비 번호 |
| group_device | integer | N | 0 | 그룹 번호 (레거시) |
| name_device | string | Y | - | 장비명 (max: 200) |
| type_device | string | N | "Lamp" | EnumDeviceType |
| version | string | N | null | 펌웨어 버전 (max: 50) |
| status | string | N | "ACTIVATED" | EnumDeviceStatus |
| is_enable | boolean | N | true | 활성화 여부 |
| ip_address | string | Y | - | IP 주소 (max: 45) |
| ip_port | integer | N | 80 | 포트 번호 (1-65535) |
| user_name | string | N | null | 접속 사용자명 (max: 100) |
| user_password | string | N | null | 접속 비밀번호 (max: 255) |
| description | string | N | null | 설명 (max: 500) |
| geolocation | object | N | null | 좌표/위치 정보 (JSONB) |

**Response (201 Created)**: 생성된 Lamp 객체

#### 5.11.4 Lamp 수정 (PATCH)

**Endpoint**: `PATCH /api/devices/lamps/{id}`

**Request Body**: 수정할 필드만 포함 (모든 필드 선택적)

```json
{
  "name_device": "Lamp-A-1-Updated",
  "ip_port": 8080,
  "description": "GOP 1구역 전방 경광등 - 업데이트"
}
```

**Response (200 OK)**: 수정된 Lamp 객체

#### 5.11.5 Lamp 수정 (PUT)

**Endpoint**: `PUT /api/devices/lamps/{id}`

**Request Body**: 전체 필드 포함 (LampCreate와 동일)

**Response (200 OK)**: 수정된 Lamp 객체

#### 5.11.6 Lamp 삭제

**Endpoint**: `DELETE /api/devices/lamps/{id}`

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Lamp deleted successfully"
}
```

#### 5.11.7 FK 정책 및 CASCADE 동작

| 관계 | 동작 | 정책 | 설명 |
|------|------|------|------|
| Device → Lamp | Device 삭제 | `CASCADE` | Lamp 하위 테이블 데이터 삭제 |
| Lamp → EventMappingLamp | Lamp 삭제 | `SET NULL` | EventMappingLamp.lamp_id → NULL |

> **참고**: Lamp 삭제 시 EventMappingLamp 자체는 유지되며, `lamp_id`만 NULL로 설정됩니다.

#### 5.11.8 ConfigChangeLog 연동

Lamp CRUD 작업 시 자동으로 ConfigChangeLog가 생성됩니다.

| 작업 | resource_type | action |
|------|---------------|--------|
| POST | LAMP | CREATED |
| PATCH/PUT | LAMP | UPDATED |
| DELETE | LAMP | DELETED |

---

## 6. Event API 설계

### 6.1 Detection Event API

> **v2.6 변경사항 (PRD_Event_Field_Normalization.md v1.0)**:
> - `result`: 별도 필드로 유지 (핵심 분류 필드, 필수)
> - `detail`: 상세 정보만 포함 (signal, thumbnail, objects, model, inference_ms)
> - Request/Response 모두 result가 별도 필드로 분리됨

#### 6.1.1 Detection Event 목록 조회

**Endpoint**: `GET /api/events/detections`

**Query Parameters**:
- `start_date` (datetime, required): 조회 시작 시간 (ISO 8601)
- `end_date` (datetime, required): 조회 종료 시간 (ISO 8601)
- `device_id` (int, optional): 장치 ID 필터 (v2.2)
- `type_event` (string, optional): 이벤트 타입 필터 (Intrusion)
- `action_reported` (string, optional): 조치 보고 여부 필터 (True, False)
- `result` (string, optional): 탐지 결과 필터 (PIR_SENSOR, THERMAL_SENSOR 등)
- `page` (int, optional): 페이지 번호
- `limit` (int, optional): 페이지당 항목 수

**Request Example**:
```http
GET /api/events/detections?start_date=2025-01-01T00:00:00&end_date=2025-01-31T23:59:59&type_event=Intrusion HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

> ** v2.2 변경**: `controller`, `sensor`, `type_device`, `group_event` → `device_id` 단일 FK로 통합
> ** v1.3 변경**: Response에서 `device_id`, `sequence` 필드 제거 (device.id에 포함, sequence는 Request 전용)

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
      "device": {
        "id": 101,
        "number_device": 1,
        "group_device": 1, // (Deprecated 예정, 레거시)
        "name_device": "Sensor-A-1",
        "type_device": "Multi",
        "version": "v1.5.0",
        "status": "ACTIVATED",
        "controller_id": 1,
        "geolocation": null,
        "device_groups": [
          {"id": 1, "name": "A구역 센서그룹", "description": "A구역 센서 장비 그룹", "device_count": 5}
        ]
      },
      "device_description": "[Multi] Sensor-A-1 (number: 1, id: 101)",
      "result": "AI_DETECT", //(EnumDetectionType) - v2.6 별도 필드
      "detail": {
        "thumbnail": "http://192.168.1.50:8080/events/1001/thumb.jpg",
        "signal": 1500,
        "objects": [
          {"label": "person", "confidence": 0.95, "bbox": [100, 200, 50, 100]}
        ],
        "model": "yolov8n",
        "inference_ms": 45
      },
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
      "device": null,
      "device_description": "[Multi] Sensor-A-1 (number: 1, id: 101)",
      "result": "PIR_SENSOR", //(EnumDetectionType) - v2.6 별도 필드
      "detail": null,
      "created_at": "2026-01-06T10:15:23.100Z",
      "updated_at": "2026-01-06T10:15:23.100Z"
    }
  ]
}
```

**Error Response (422 Validation Error)** - 잘못된 날짜 형식:
```json
{
  "success": false,
  "message": "Validation error",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [
      {"field": "start_date", "message": "Invalid datetime format. Use ISO 8601 format (e.g., 2026-01-06T00:00:00Z)"},
      {"field": "end_date", "message": "end_date must be greater than start_date"}
    ]
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
    "type_event": "Intrusion", //(EnumEventType)
    "action_reported": "True", //(EnumTrueFalse)
    "device": {
      "id": 101,
      "number_device": 1,
      "group_device": 1, // (Deprecated 예정, 레거시)
      "name_device": "Sensor-A-1",
      "type_device": "Multi",
      "version": "v1.5.0",
      "status": "ACTIVATED",
      "controller_id": 1,
      "geolocation": null,
      "device_groups": [
        {"id": 1, "name": "A구역 센서그룹", "description": "A구역 센서 장비 그룹", "device_count": 5}
      ]
    },
    "device_description": "[Multi] Sensor-A-1 (number: 1, id: 101)",
    "result": "AI_DETECT", //(EnumDetectionType) - v2.6 별도 필드
    "detail": {
      "thumbnail": "http://192.168.1.50:8080/events/1001/thumb.jpg",
      "signal": 1500,
      "objects": [
        {"label": "person", "confidence": 0.95, "bbox": [100, 200, 50, 100]}
      ],
      "model": "yolov8n",
      "inference_ms": 45
    },
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

> **변경**: `controller`, `sensor`, `type_device`, `group_event` → `device_id` 단일 FK로 통합
> **자동 생성**: `device_description`은 서버에서 자동 생성됨

**Request Example**:
```http
POST /api/events/detections HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "device_id": 101,
  "type_event": "Intrusion",
  "result": "THERMAL_SENSOR",
  "detail": {
    "thumbnail": "http://192.168.1.50:8080/events/1002/thumb.jpg",
    "signal": 1800
  }
}
```

**Request Body**:
```json
{
  "device_id": 101,
  "type_event": "Intrusion", //(EnumEventType)
  "result": "THERMAL_SENSOR", //(EnumDetectionType) - v2.6 별도 필드 (필수)
  "detail": { //(optional, 상세 정보만)
    "thumbnail": "http://192.168.1.50:8080/events/1002/thumb.jpg",
    "signal": 1800,
    "objects": [
      {"label": "person", "confidence": 0.92, "bbox": [150, 220, 60, 120]}
    ],
    "model": "yolov8n",
    "inference_ms": 42
  }
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
    "device": {
      "id": 101,
      "number_device": 1,
      "group_device": 1, // (Deprecated 예정, 레거시)
      "name_device": "Sensor-A-1",
      "type_device": "Multi",
      "version": "v1.5.0",
      "status": "ACTIVATED",
      "controller_id": 1,
      "geolocation": null,
      "device_groups": [
        {"id": 1, "name": "A구역 센서그룹", "description": "A구역 센서 장비 그룹", "device_count": 5}
      ]
    },
    "device_description": "[Multi] Sensor-A-1 (number: 1, id: 101)",
    "result": "THERMAL_SENSOR", //(EnumDetectionType) - v2.6 별도 필드
    "detail": {
      "thumbnail": "http://192.168.1.50:8080/events/1002/thumb.jpg",
      "signal": 1800,
      "objects": [
        {"label": "person", "confidence": 0.92, "bbox": [150, 220, 60, 120]}
      ],
      "model": "yolov8n",
      "inference_ms": 42
    },
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

**Request Example**:
```http
PATCH /api/events/detections/1002 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "type_event": "Intrusion",
  "result": "VIBRATION_SENSOR",
  "detail": {
    "thumbnail": "http://192.168.1.50:8080/events/1002/thumb_updated.jpg",
    "signal": 2000,
    "model": "yolov8n_updated"
  }
}
```

**Request Body** (부분 업데이트):
```json
{
  "type_event": "Intrusion", //(EnumEventType, optional)
  "result": "VIBRATION_SENSOR", //(EnumDetectionType, optional) - v2.6 별도 필드
  "detail": { //(optional, 상세 정보만)
    "thumbnail": "http://192.168.1.50:8080/events/1002/thumb_updated.jpg",
    "signal": 2000,
    "model": "yolov8n_updated"
  }
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
    "device": {
      "id": 101,
      "number_device": 1,
      "group_device": 1, // (Deprecated 예정, 레거시)
      "name_device": "Sensor-A-1",
      "type_device": "Multi",
      "version": "v1.5.0",
      "status": "ACTIVATED",
      "controller_id": 1,
      "geolocation": null,
      "device_groups": [
        {"id": 1, "name": "A구역 센서그룹", "description": "A구역 센서 장비 그룹", "device_count": 5}
      ]
    },
    "device_description": "[Multi] Sensor-A-1 (number: 1, id: 101)",
    "result": "VIBRATION_SENSOR", //(EnumDetectionType) - v2.6 별도 필드
    "detail": {
      "thumbnail": "http://192.168.1.50:8080/events/1002/thumb_updated.jpg",
      "signal": 2000,
      "model": "yolov8n_updated"
    },
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

**Request Example**:
```http
PUT /api/events/detections/1002 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "device_id": 101,
  "type_event": "Intrusion",
  "action_reported": "True",
  "result": "DISTANCE_SENSOR",
  "detail": {
    "thumbnail": "http://192.168.1.50:8080/events/1002/thumb_full.jpg",
    "signal": 2500,
    "model": "yolov8m"
  }
}
```

> **v2.2 변경**: `controller`, `sensor`, `type_device`, `group_event` → `device_id` 단일 FK로 통합

**Request Body** (전체 업데이트):
```json
{
  "device_id": 101,
  "type_event": "Intrusion", //(EnumEventType)
  "action_reported": "True", //(EnumTrueFalse)
  "result": "DISTANCE_SENSOR", //(EnumDetectionType) - v2.6 별도 필드 (필수)
  "detail": { //(optional, 상세 정보만)
    "thumbnail": "http://192.168.1.50:8080/events/1002/thumb_full.jpg",
    "signal": 2500,
    "objects": [
      {"label": "vehicle", "confidence": 0.88, "bbox": [200, 300, 80, 60]}
    ],
    "model": "yolov8m",
    "inference_ms": 65
  }
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
    "device": {
      "id": 101,
      "number_device": 1,
      "group_device": 1, // (Deprecated 예정, 레거시)
      "name_device": "Sensor-A-1",
      "type_device": "Multi",
      "version": "v1.5.0",
      "status": "ACTIVATED",
      "controller_id": 1,
      "geolocation": null,
      "device_groups": [
        {"id": 1, "name": "A구역 센서그룹", "description": "A구역 센서 장비 그룹", "device_count": 5}
      ]
    },
    "device_description": "[Multi] Sensor-A-1 (number: 1, id: 101)",
    "result": "DISTANCE_SENSOR", //(EnumDetectionType) - v2.6 별도 필드
    "detail": {
      "thumbnail": "http://192.168.1.50:8080/events/1002/thumb_full.jpg",
      "signal": 2500,
      "objects": [
        {"label": "vehicle", "confidence": 0.88, "bbox": [200, 300, 80, 60]}
      ],
      "model": "yolov8m",
      "inference_ms": 65
    },
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

**Request Example**:
```http
DELETE /api/events/detections/1002 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

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

> **v1.3**: `from_event` 내부는 현재 Detection/Malfunction/Connection Event Response 포맷을 따름
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
      "device": {
        "id": 103,
        "number_device": 3,
        "group_device": 1,
        "name_device": "Sensor-A-3",
        "type_device": "Fence",
        "version": "v1.5.0",
        "status": "ACTIVATED",
        "controller_id": 1,
        "geolocation": null,
        "device_groups": [
          {"id": 1, "name": "A구역 센서그룹"}
        ]
      },
      "device_description": "[Fence] Sensor-A-3 (number: 3, id: 103)",
      "result": "PIR_SENSOR", //(EnumDetectionType) - v2.6 별도 필드
      "detail": {
        "thumbnail": "http://192.168.1.50:8080/events/1001/thumb.jpg",
        "signal": 1500
      },
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

> **v2.6 변경사항 (PRD_Event_Field_Normalization.md v1.0)**:
> - `reason`: 별도 필드로 유지 (핵심 분류 필드, 필수)
> - `detail`: 상세 정보만 포함 (first_start, first_end, second_start, second_end)
> - Request/Response 모두 reason이 별도 필드로 분리됨

#### 6.2.1 Malfunction Event 목록 조회

**Endpoint**: `GET /api/events/malfunctions`

**Query Parameters**:
- `start_date` (datetime, required): 조회 시작 시간
- `end_date` (datetime, required): 조회 종료 시간
- `device_id` (int, optional): 장치 ID 필터 (v2.2)
- `reason` (string, optional): 장애 원인 필터 (FAULT_CONTROLLER, FAULT_FENCE, FAULT_CABLE_CUTTING 등)
- `action_reported` (string, optional): 조치 보고 여부 필터 (True, False)
- `page` (int, optional): 페이지 번호
- `limit` (int, optional): 페이지당 항목 수

**Request Example**:
```http
GET /api/events/malfunctions?start_date=2025-01-01T00:00:00&end_date=2025-01-31T23:59:59&reason=FAULT_FENCE HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

> **v2.2 변경**: `controller`, `sensor`, `type_device`, `group_event` → `device_id` 단일 FK로 통합  
> **v1.3 변경**: Response에서 `device_id`, `sequence` 필드 제거 (device.id에 포함, sequence는 Request 전용)

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
      "device": {
        "id": 103,
        "number_device": 3,
        "group_device": 1, // (Deprecated 예정, 레거시)
        "name_device": "Sensor-A-3",
        "type_device": "Fence",
        "version": "v1.5.0",
        "status": "ACTIVATED",
        "controller_id": 1,
        "geolocation": null,
        "device_groups": [
          {"id": 1, "name": "A구역 센서그룹", "description": "A구역 센서 장비 그룹", "device_count": 5}
        ]
      },
      "device_description": "[Fence] Sensor-A-3 (number: 3, id: 103)",
      "reason": "FAULT_CABLE_CUTTING", //(EnumFaultType) - v2.6 별도 필드
      "detail": {
        "first_start": 10,
        "first_end": 15,
        "second_start": 20,
        "second_end": 25
      },
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
- `reason` (string, required): 장애 원인 (EnumFaultType) - v2.6 별도 필드
  - FAULT_CONTROLLER, FAULT_FENCE, FAULT_MULTI, FAULT_CABLE_CUTTING, FAULT_ETC
- `detail` (object, optional): 오동작 상세 정보
  - `first_start` (int): 첫 번째 케이블 시작점
  - `first_end` (int): 첫 번째 케이블 끝점
  - `second_start` (int): 두 번째 케이블 시작점
  - `second_end` (int): 두 번째 케이블 끝점

**Error Response (422 Validation Error)** - 잘못된 날짜 형식:
```json
{
  "success": false,
  "message": "Validation error",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [
      {"field": "start_date", "message": "Invalid datetime format. Use ISO 8601 format (e.g., 2026-01-06T00:00:00Z)"},
      {"field": "end_date", "message": "end_date must be greater than start_date"}
    ]
  }
}
```

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
    "device": {
      "id": 103,
      "number_device": 3,
      "group_device": 1, // (Deprecated 예정, 레거시)
      "name_device": "Sensor-A-3",
      "type_device": "Fence",
      "version": "v1.5.0",
      "status": "ACTIVATED",
      "controller_id": 1,
      "geolocation": null,
      "device_groups": [
        {"id": 1, "name": "A구역 센서그룹", "description": "A구역 센서 장비 그룹", "device_count": 5}
      ]
    },
    "device_description": "[Fence] Sensor-A-3 (number: 3, id: 103)",
    "reason": "FAULT_CABLE_CUTTING", //(EnumFaultType) - v2.6 별도 필드
    "detail": {
      "first_start": 5,
      "first_end": 5,
      "second_start": 0,
      "second_end": 0
    },
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

> **v2.2 변경**: `controller`, `sensor`, `type_device`, `group_event` → `device_id` 단일 FK로 통합
> **자동 생성**: `device_description`은 서버에서 자동 생성됨

**Request Example**:
```http
POST /api/events/malfunctions HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "device_id": 103,
  "type_event": "Fault",
  "reason": "FAULT_CABLE_CUTTING",
  "detail": {
    "first_start": 10,
    "first_end": 15,
    "second_start": 20,
    "second_end": 25
  }
}
```

**Request Body**:
```json
{
  "device_id": 104,
  "type_event": "Fault", //(EnumEventType)
  "reason": "FAULT_FENCE", //(EnumFaultType) - v2.6 별도 필드 (필수)
  "detail": { //(optional, 상세 정보만)
    "first_start": 3,
    "first_end": 3,
    "second_start": 0,
    "second_end": 0
  }
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
    "device": {
      "id": 104,
      "number_device": 4,
      "group_device": 1, // (Deprecated 예정, 레거시)
      "name_device": "Sensor-A-4",
      "type_device": "Multi",
      "version": "v1.5.0",
      "status": "ACTIVATED",
      "controller_id": 1,
      "geolocation": null,
      "device_groups": [
        {"id": 1, "name": "A구역 센서그룹", "description": "A구역 센서 장비 그룹", "device_count": 5}
      ]
    },
    "device_description": "[Multi] Sensor-A-4 (number: 4, id: 104)",
    "reason": "FAULT_FENCE", //(EnumFaultType) - v2.6 별도 필드
    "detail": {
      "first_start": 3,
      "first_end": 3,
      "second_start": 0,
      "second_end": 0
    },
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

**Request Example**:
```http
PATCH /api/events/malfunctions/2002 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "type_event": "Fault",
  "reason": "FAULT_MULTI",
  "detail": {
    "first_start": 3,
    "first_end": 3
  }
}
```

**Request Body** (부분 업데이트):
```json
{
  "type_event": "Fault", //(EnumEventType, optional)
  "reason": "FAULT_MULTI", //(EnumFaultType, optional) - v2.6 별도 필드
  "detail": { //(optional, 상세 정보만)
    "first_start": 3, //(optional)
    "first_end": 3 //(optional)
  }
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
    "device": {
      "id": 104,
      "number_device": 4,
      "group_device": 1, // (Deprecated 예정, 레거시)
      "name_device": "Sensor-A-4",
      "type_device": "Multi",
      "version": "v1.5.0",
      "status": "ACTIVATED",
      "controller_id": 1,
      "geolocation": null,
      "device_groups": [
        {"id": 1, "name": "A구역 센서그룹", "description": "A구역 센서 장비 그룹", "device_count": 5}
      ]
    },
    "device_description": "[Multi] Sensor-A-4 (number: 4, id: 104)",
    "reason": "FAULT_MULTI", //(EnumFaultType) - v2.6 별도 필드
    "detail": {
      "first_start": 3,
      "first_end": 3,
      "second_start": 0,
      "second_end": 0
    },
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

**Request Example**:
```http
PUT /api/events/malfunctions/2002 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "device_id": 104,
  "type_event": "Fault",
  "action_reported": "True",
  "reason": "FAULT_ETC",
  "detail": {
    "first_start": 2,
    "first_end": 2,
    "second_start": 5,
    "second_end": 5
  }
}
```

> **v2.2 변경**: `controller`, `sensor`, `type_device`, `group_event` → `device_id` 단일 FK로 통합

**Request Body** (전체 업데이트):
```json
{
  "device_id": 104,
  "type_event": "Fault", //(EnumEventType)
  "action_reported": "True", //(EnumTrueFalse)
  "reason": "FAULT_ETC", //(EnumFaultType) - v2.6 별도 필드 (필수)
  "detail": { //(optional, 상세 정보만)
    "first_start": 2,
    "first_end": 2,
    "second_start": 5,
    "second_end": 5
  }
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
    "device": {
      "id": 104,
      "number_device": 4,
      "group_device": 1, // (Deprecated 예정, 레거시)
      "name_device": "Sensor-A-4",
      "type_device": "Multi",
      "version": "v1.5.0",
      "status": "ACTIVATED",
      "controller_id": 1,
      "geolocation": null,
      "device_groups": [
        {"id": 1, "name": "A구역 센서그룹", "description": "A구역 센서 장비 그룹", "device_count": 5}
      ]
    },
    "device_description": "[Multi] Sensor-A-4 (number: 4, id: 104)",
    "reason": "FAULT_ETC", //(EnumFaultType) - v2.6 별도 필드
    "detail": {
      "first_start": 2,
      "first_end": 2,
      "second_start": 5,
      "second_end": 5
    },
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

**Request Example**:
```http
DELETE /api/events/malfunctions/2002 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

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

> **v1.3**: `from_event` 내부는 현재 Malfunction Event Response 포맷을 따름
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
        "geolocation": null,
        "device_groups": [
          { "id": 2, "name": "B구역 컨트롤러 그룹" }
        ]
      },
      "device_description": "[Controller] Controller-B (number: 2, id: 2)",
      "detail": {
        "reason": "FAULT_CONTROLLER", //(EnumFaultType)
        "first_start": 100,
        "first_end": 200,
        "second_start": 300,
        "second_end": 400
      },
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
- `device_id` (int, optional): 장치 ID 필터 ( v2.2)
- `page` (int, optional): 페이지 번호
- `limit` (int, optional): 페이지당 항목 수

**Request Example**:
```http
GET /api/events/connections?start_date=2025-01-01T00:00:00&end_date=2025-01-31T23:59:59 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

> **v2.2 변경**: `controller`, `sensor`, `type_device`, `group_event` → `device_id` 단일 FK로 통합
> **v1.3 변경**: Response에서 `device_id`, `sequence` 필드 제거 (device.id에 포함, sequence는 Request 전용)

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
        "geolocation": null,
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
        "geolocation": null,
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

**Error Response (422 Validation Error)** - 잘못된 날짜 형식:
```json
{
  "success": false,
  "message": "Validation error",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [
      {"field": "start_date", "message": "Invalid datetime format. Use ISO 8601 format (e.g., 2026-01-06T00:00:00Z)"},
      {"field": "end_date", "message": "end_date must be greater than start_date"}
    ]
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
      "geolocation": null,
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

> **v2.2 변경**: `controller`, `sensor`, `type_device`, `group_event` → `device_id` 단일 FK로 통합
> **자동 생성**: `device_description`은 서버에서 자동 생성됨

**Request Example**:
```http
POST /api/events/connections HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "device_id": 101,
  "type_event": "Connection"
}
```

**Request Body**:
```json
{
  "device_id": 103,
  "type_event": "Connection" //(EnumEventType)
}
```

**필드 설명**:
| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| device_id | Integer | Y | 장치 ID (Device FK) |
| type_event | String | Y | 이벤트 유형 (EnumEventType: Connection) |

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
      "is_enable": true,
      "controller_id": 1,
      "geolocation": null,
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

**Request Example**:
```http
PATCH /api/events/connections/3002 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "type_event": "Connection"
}
```

**Request Body** (부분 업데이트):
```json
{
  "type_event": "Connection" //(EnumEventType)
}
```

**필드 설명**:
| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| type_event | String | N | 이벤트 유형 (EnumEventType: Connection) |

> **참고**: `device_id`는 PATCH로 수정 불가 (PUT 전체 교체만 가능)

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
      "is_enable": true,
      "controller_id": 1,
      "geolocation": null,
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

**Request Example**:
```http
PUT /api/events/connections/3003 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "device_id": 104,
  "type_event": "Connection"
}
```

> **v2.2 변경**: `controller`, `sensor`, `type_device`, `group_event` → `device_id` 단일 FK로 통합

**Request Body** (전체 업데이트):
```json
{
  "device_id": 104,
  "type_event": "Connection" //(EnumEventType)
}
```

**필드 설명**:
| 필드명 | 타입 | 필수 | 설명 |
|--------|------|------|------|
| device_id | Integer | Y | 장치 ID (Device FK) |
| type_event | String | Y | 이벤트 유형 (EnumEventType: Connection) |

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
      "is_enable": true,
      "controller_id": 1,
      "geolocation": null,
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

**Request Example**:
```http
DELETE /api/events/connections/3002 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

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

**Request Example**:
```http
POST /api/events/actions HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "type_event": "Action",
  "content": "침입 탐지 확인 및 순찰 출동 요청",
  "user": "operator_kim",
  "from_event_id": 1001
}
```

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

> **v1.5**: `from_type_event` 필드 제거됨. `from_event_id`만으로 원본 이벤트를 참조하며, polymorphic relationship을 통해 이벤트 타입이 자동으로 확인됩니다.

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
        "geolocation": null,
        "urls": null,
        "mode": null,
        "category": null,
        "is_record": null,
        "device_groups": []
      },
      "device_description": "[Fence] Test Sensor (number: 101, id: 2)",
      "result": "PIR_SENSOR", //(EnumDetectionType) - v2.6 별도 필드
      "detail": {
        "thumbnail": "http://192.168.1.50:8080/events/1001/thumb.jpg",
        "signal": 1500
      },
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

**Request Example**:
```http
GET /api/events/actions?start_date=2025-01-01T00:00:00&end_date=2025-01-31T23:59:59&user=operator_kim HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

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
        "device": {
          "id": 102,
          "number_device": 2,
          "group_device": 1,
          "name_device": "Sensor-A-2",
          "type_device": "Fence",
          "version": "v1.5.0",
          "status": "ACTIVATED",
          "controller_id": 1,
          "geolocation": null,
          "device_groups": []
        },
        "device_description": "[Fence] Sensor-A-2 (number: 2, id: 102)",
        "result": "THERMAL_SENSOR", //(EnumDetectionType) - v2.6 별도 필드
        "detail": {
          "thumbnail": "http://192.168.1.50:8080/events/1002/thumb.jpg",
          "signal": 1800
        },
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
        "device": {
          "id": 104,
          "number_device": 4,
          "group_device": 1,
          "name_device": "Sensor-A-4",
          "type_device": "Multi",
          "version": "v1.5.0",
          "status": "ACTIVATED",
          "controller_id": 1,
          "geolocation": null,
          "device_groups": []
        },
        "device_description": "[Multi] Sensor-A-4 (number: 4, id: 104)",
        "reason": "FAULT_ETC", //(EnumFaultType) - v2.6 별도 필드
        "detail": {
          "first_start": 2,
          "first_end": 2,
          "second_start": 5,
          "second_end": 5
        },
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

**Error Response (422 Validation Error)** - 잘못된 날짜 형식:
```json
{
  "success": false,
  "message": "Validation error",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [
      {"field": "start_date", "message": "Invalid datetime format. Use ISO 8601 format (e.g., 2026-01-06T00:00:00Z)"},
      {"field": "end_date", "message": "end_date must be greater than start_date"}
    ]
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
      "device": {
        "id": 102,
        "number_device": 2,
        "group_device": 1,
        "name_device": "Sensor-A-2",
        "type_device": "Fence",
        "version": "v1.5.0",
        "status": "ACTIVATED",
        "controller_id": 1,
        "geolocation": null,
        "device_groups": []
      },
      "device_description": "[Fence] Sensor-A-2 (number: 2, id: 102)",
      "result": "THERMAL_SENSOR", //(EnumDetectionType) - v2.6 별도 필드
      "detail": {
        "thumbnail": "http://192.168.1.50:8080/events/1002/thumb.jpg",
        "signal": 1800
      },
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

**Request Example**:
```http
PATCH /api/events/actions/4001 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "content": "침입 탐지 확인 완료 - 오탐지로 판명",
  "user": "operator_kim"
}
```

**Request Body** (부분 업데이트):
```json
{
  "content": "침입 탐지 확인 완료 - 오탐지로 판명", // 이중 하나
  "user": "operator_kim" // 이중 하나
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
      "device": {
        "id": 102,
        "number_device": 2,
        "group_device": 1,
        "name_device": "Sensor-A-2",
        "type_device": "Fence",
        "version": "v1.5.0",
        "status": "ACTIVATED",
        "controller_id": 1,
        "geolocation": null,
        "device_groups": []
      },
      "device_description": "[Fence] Sensor-A-2 (number: 2, id: 102)",
      "result": "THERMAL_SENSOR", //(EnumDetectionType) - v2.6 별도 필드
      "detail": {
        "thumbnail": "http://192.168.1.50:8080/events/1002/thumb.jpg",
        "signal": 1800
      },
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

**Request Example**:
```http
PUT /api/events/actions/4001 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "content": "침입 탐지 재확인 - 실제 침입 확인됨, 경찰 출동 요청",
  "user": "operator_park"
}
```

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
      "device": {
        "id": 102,
        "number_device": 2,
        "group_device": 1,
        "name_device": "Sensor-A-2",
        "type_device": "Fence",
        "version": "v1.5.0",
        "status": "ACTIVATED",
        "controller_id": 1,
        "geolocation": null,
        "device_groups": []
      },
      "device_description": "[Fence] Sensor-A-2 (number: 2, id: 102)",
      "result": "THERMAL_SENSOR", //(EnumDetectionType) - v2.6 별도 필드
      "detail": {
        "thumbnail": "http://192.168.1.50:8080/events/1002/thumb.jpg",
        "signal": 1800
      },
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

**Request Example**:
```http
DELETE /api/events/actions/4001 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

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

> **v2.3 변경사항 (v2.1)**: `group_event` (VARCHAR) → `device_group_id` (FK) 변경
> - EventMapping이 DeviceGroup과 FK 관계로 연결됨
> - Device → DeviceGroup → EventMapping → CameraPreset 흐름으로 이벤트-카메라 연동 가능
>
> **v2.4 변경사항 (PRD_CategoryEvent_Refactoring.md v1.1)**: ⚠️ **Breaking Change**
> - `category_event` (VARCHAR) → `category_event_mapping` (Enum) 필드명 변경
> - 타입: `EnumMappingEventCategory` (FENCE_SENSOR_ONLY, MULTI_SENSOR_ONLY 등)

#### 7.2.1 EventMapping 목록 조회

**Endpoint**: `GET /api/integrations/event-mappings`

**Query Parameters**:
- `name_event` (string, optional): 이벤트 이름 필터
- `device_group_id` (int, optional): DeviceGroup ID 필터 **(v2.3 변경: group_event → device_group_id)**
- `category_event_mapping` (EnumMappingEventCategory, optional): 이벤트 매핑 카테고리 필터 **(v2.4 변경: category_event → category_event_mapping)**
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
      "category_event_mapping": "FENCE_SENSOR_ONLY",
      "description": "센서 침입 탐지 이벤트 매핑",
      "status": true,
      "created_at": "2026-01-06T09:00:00.000Z",
      "updated_at": "2026-01-06T09:00:00.000Z"
    },
    {
      "id": 2,
      "name_event": "장애 발생",
      "device_group_id": 2,
      "category_event_mapping": "MULTI_SENSOR_ONLY",
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

**Error Response (422 Validation Error)** - 잘못된 쿼리 파라미터:
```json
{
  "success": false,
  "message": "Validation error",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [
      {"field": "page", "message": "page must be a positive integer"},
      {"field": "limit", "message": "limit must be between 1 and 100"}
    ]
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
    "category_event_mapping": "FENCE_SENSOR_ONLY",
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

**Request Example**:
```http
POST /api/integrations/event-mappings HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "name_event": "연결 상태 변경",
  "device_group_id": 3,
  "category_event_mapping": "SENSOR_WITH_CAMERA",
  "description": "센서 연결 상태 변경 이벤트 매핑",
  "status": true
}
```

**Request Body**:
```json
{
  "name_event": "연결 상태 변경",
  "device_group_id": 3,
  "category_event_mapping": "SENSOR_WITH_CAMERA",
  "description": "센서 연결 상태 변경 이벤트 매핑",
  "status": true
}
```

> **v2.3 변경**: `group_event` (VARCHAR) → `device_group_id` (INT, FK) 변경. DeviceGroup.id를 참조합니다.
> **v2.4 변경**: `category_event` (VARCHAR) → `category_event_mapping` (EnumMappingEventCategory) 변경.

**Response Example** (201 Created):
```json
{
  "success": true,
  "message": "Event mapping created successfully",
  "data": {
    "id": 3,
    "name_event": "연결 상태 변경",
    "device_group_id": 3,
    "category_event_mapping": "SENSOR_WITH_CAMERA",
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

**Request Example**:
```http
PATCH /api/integrations/event-mappings/1 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "device_group_id": 2,
  "description": "센서 침입 탐지 이벤트 - 수정된 설명",
  "status": false
}
```

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
    "category_event_mapping": "FENCE_SENSOR_ONLY",
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

**Request Example**:
```http
PUT /api/integrations/event-mappings/1 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "name_event": "침입 탐지 업데이트",
  "device_group_id": 1,
  "category_event_mapping": "FENCE_SENSOR_ONLY",
  "description": "전체 업데이트된 설명",
  "status": true
}
```

**Path Parameters**:
- `id` (int, required): EventMapping ID

**Request Body** (모든 필드 필수):
```json
{
  "name_event": "침입 탐지 업데이트",
  "device_group_id": 1,
  "category_event_mapping": "FENCE_SENSOR_ONLY",
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
    "category_event_mapping": "FENCE_SENSOR_ONLY",
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

### 7.3 Event Mapping Cameras API

Event Mapping에 연동된 카메라 동작(PTZ 프리셋 이동 등)을 관리합니다.

> **아키텍처 원칙**:
> - EventMapping은 다양한 Action 타입(Camera, Speaker, 3rd Party)의 **Base 노드**
> - 각 Action 타입은 독립적인 하위 API로 관리 (`/cameras`, `/speakers`, `/externals`)
> - EventMapping API에 `include_cameras` 같은 특정 타입 종속 파라미터 **사용하지 않음**

#### 7.3.1 EventMappingCamera 목록 조회

**Endpoint**: `GET /api/integrations/event-mappings/{mapping_id}/cameras`

**Path Parameters**:
- `mapping_id` (int, required): EventMapping ID

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| page | integer | N | 페이지 번호 (기본값: 1) |
| limit | integer | N | 페이지당 항목 수 (기본값: 20, 최대: 100) |

**Request Example**:
```http
GET /api/integrations/event-mappings/10/cameras?page=1&limit=20 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Response Example** (200 OK):

> **Nested Response 규칙**:
> - 주체(EventMappingCamera)의 `created_at`, `updated_at` 포함
> - Nested 객체(camera, target_preset, home_preset)는 **Full Property** (timestamp 제외)

```json
{
  "success": true,
  "message": "Event mapping cameras retrieved successfully",
  "data": {
    "items": [
      {
        "id": 1,
        "event_mapping_id": 10,
        "camera": {
          "id": 201,
          "number_device": 1,
          "group_device": 1,
          "name_device": "PTZ-Camera-01",
          "type_device": "IpCamera",
          "version": "1.0.0",
          "status": "ACTIVATED",
          "ip_address": "192.168.1.101",
          "ip_port": 80,
          "mode": "ONVIF",
          "category": "PTZ",
          "is_record": true,
          "hardware_spec": {
            "name": "AXIS P5655-E",
            "manufacturer": "Axis Communications",
            "model": "P5655-E",
            "firmware": "10.12.114"
          },
          "geolocation": {
            "location": "GOP 1구역 전방 초소",
            "latitude": 37.123456,
            "longitude": 127.123456
          },
          "urls": {
            "homepage": { "url": "https://192.168.1.101/" },
            "streams": {
              "rtsp": { "main": "rtsp://192.168.1.101:554/Streaming/Channels/101" }
            }
          },
          "device_groups": [
            { "id": 1, "name": "1구역 센서 그룹", "description": "1구역 감시 장비", "device_count": 5 }
          ]
        },
        "target_preset": {
          "id": 5,
          "camera_id": 201,
          "camera_name": "PTZ-Camera-01",
          "preset_index": 1,
          "preset_name": "입구 정면",
          "touring_time": 10
        },
        "home_preset": {
          "id": 6,
          "camera_id": 201,
          "camera_name": "PTZ-Camera-01",
          "preset_index": 0,
          "preset_name": "Home",
          "touring_time": 0
        },
        "delay_time": 30,
        "is_enable": true,
        "priority": 1,
        "created_at": "2026-01-07T10:00:00.000+09:00",
        "updated_at": "2026-01-07T10:00:00.000+09:00"
      }
    ],
    "total": 1
  },
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 1,
    "total_pages": 1
  }
}
```

**Error Response** (404 Not Found):
```json
{
  "success": false,
  "message": "Event mapping not found with id=999"
}
```

**Error Response (422 Validation Error)** - 잘못된 쿼리 파라미터:
```json
{
  "success": false,
  "message": "Validation error",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [
      {"field": "page", "message": "page must be a positive integer"},
      {"field": "limit", "message": "limit must be between 1 and 100"}
    ]
  }
}
```

#### 7.3.2 EventMappingCamera 단일 조회

**Endpoint**: `GET /api/integrations/event-mappings/{mapping_id}/cameras/{config_id}`

**Path Parameters**:
- `mapping_id` (int, required): EventMapping ID
- `config_id` (int, required): EventMappingCamera ID

**Request Example**:
```http
GET /api/integrations/event-mappings/10/cameras/1 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Event mapping camera retrieved successfully",
  "data": {
    "id": 1,
    "event_mapping_id": 10,
    "camera": {
      "id": 201,
      "number_device": 1,
      "group_device": 1,
      "name_device": "PTZ-Camera-01",
      "type_device": "IpCamera",
      "version": "1.0.0",
      "status": "ACTIVATED",
      "ip_address": "192.168.1.101",
      "ip_port": 80,
      "mode": "ONVIF",
      "category": "PTZ",
      "is_record": true,
      "hardware_spec": null,
      "geolocation": null,
      "urls": {
        "streams": { "rtsp": { "main": "rtsp://192.168.1.101:554/Streaming/Channels/101" } }
      },
      "device_groups": []
    },
    "target_preset": {
      "id": 5,
      "camera_id": 201,
      "camera_name": "PTZ-Camera-01",
      "preset_index": 1,
      "preset_name": "입구 정면",
      "touring_time": 10
    },
    "home_preset": {
      "id": 6,
      "camera_id": 201,
      "camera_name": "PTZ-Camera-01",
      "preset_index": 0,
      "preset_name": "Home",
      "touring_time": 0
    },
    "delay_time": 30,
    "is_enable": true,
    "priority": 1,
    "created_at": "2026-01-07T10:00:00.000+09:00",
    "updated_at": "2026-01-07T10:00:00.000+09:00"
  }
}
```

#### 7.3.3 EventMappingCamera 생성

**Endpoint**: `POST /api/integrations/event-mappings/{mapping_id}/cameras`

**Path Parameters**:
- `mapping_id` (int, required): EventMapping ID

**Request Body**:

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| camera_id | integer | Y | 대상 카메라 ID |
| target_preset_id | integer | N | 이벤트 발생 시 이동할 프리셋 ID |
| home_preset_id | integer | N | 홈 복귀 프리셋 ID |
| delay_time | integer | N | target_preset 도착 후 대기 시간 (초, 기본값: 0) |
| is_enable | boolean | N | 활성화 여부 (기본값: true) |
| priority | integer | N | 실행 우선순위 (Optional) |

**Request Example**:
```http
POST /api/integrations/event-mappings/10/cameras HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "camera_id": 201,
  "target_preset_id": 5,
  "home_preset_id": 6,
  "delay_time": 30,
  "is_enable": true,
  "priority": 1
}
```

**Response Example** (201 Created):
```json
{
  "success": true,
  "message": "Event mapping camera created successfully",
  "data": {
    "id": 1,
    "event_mapping_id": 10,
    "camera": {
      "id": 201,
      "number_device": 1,
      "group_device": 1,
      "name_device": "PTZ-Camera-01",
      "type_device": "IpCamera",
      "version": "1.0.0",
      "status": "ACTIVATED",
      "ip_address": "192.168.1.101",
      "ip_port": 80,
      "mode": "ONVIF",
      "category": "PTZ",
      "is_record": true,
      "hardware_spec": null,
      "geolocation": null,
      "urls": null,
      "device_groups": []
    },
    "target_preset": {
      "id": 5,
      "camera_id": 201,
      "camera_name": "PTZ-Camera-01",
      "preset_index": 1,
      "preset_name": "입구 정면",
      "touring_time": 10
    },
    "home_preset": {
      "id": 6,
      "camera_id": 201,
      "camera_name": "PTZ-Camera-01",
      "preset_index": 0,
      "preset_name": "Home",
      "touring_time": 0
    },
    "delay_time": 30,
    "is_enable": true,
    "priority": 1,
    "created_at": "2026-01-07T10:00:00.000+09:00",
    "updated_at": "2026-01-07T10:00:00.000+09:00"
  }
}
```

**Error Response** (404 Not Found):
```json
{
  "success": false,
  "message": "Camera not found with id=999"
}
```

#### 7.3.4 EventMappingCamera 수정 (부분)

**Endpoint**: `PATCH /api/integrations/event-mappings/{mapping_id}/cameras/{config_id}`

**Path Parameters**:
- `mapping_id` (int, required): EventMapping ID
- `config_id` (int, required): EventMappingCamera ID

**Request Body** (모든 필드 Optional):

| 필드 | 타입 | 설명 |
|------|------|------|
| camera_id | integer | 대상 카메라 ID |
| target_preset_id | integer | 이벤트 발생 시 이동할 프리셋 ID |
| home_preset_id | integer | 홈 복귀 프리셋 ID |
| delay_time | integer | target_preset 도착 후 대기 시간 (초) |
| is_enable | boolean | 활성화 여부 |
| priority | integer | 실행 우선순위 |

**Request Example**:
```http
PATCH /api/integrations/event-mappings/10/cameras/1 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "delay_time": 60,
  "is_enable": false
}
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Event mapping camera updated successfully",
  "data": {
    "id": 1,
    "event_mapping_id": 10,
    "camera": { ... },
    "target_preset": { ... },
    "home_preset": { ... },
    "delay_time": 60,
    "is_enable": false,
    "priority": 1,
    "created_at": "2026-01-07T10:00:00.000+09:00",
    "updated_at": "2026-01-07T11:00:00.000+09:00"
  }
}
```

#### 7.3.5 EventMappingCamera 수정 (전체)

**Endpoint**: `PUT /api/integrations/event-mappings/{mapping_id}/cameras/{config_id}`

**Path Parameters**:
- `mapping_id` (int, required): EventMapping ID
- `config_id` (int, required): EventMappingCamera ID

**Request Body** (모든 필드 교체):

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| camera_id | integer | Y | 대상 카메라 ID |
| target_preset_id | integer | N | 이벤트 발생 시 이동할 프리셋 ID |
| home_preset_id | integer | N | 홈 복귀 프리셋 ID |
| delay_time | integer | N | target_preset 도착 후 대기 시간 (초, 기본값: 0) |
| is_enable | boolean | N | 활성화 여부 (기본값: true) |
| priority | integer | N | 실행 우선순위 |

**Request Example**:
```http
PUT /api/integrations/event-mappings/10/cameras/1 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "camera_id": 202,
  "target_preset_id": 10,
  "home_preset_id": 11,
  "delay_time": 45,
  "is_enable": true,
  "priority": 2
}
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Event mapping camera replaced successfully",
  "data": {
    "id": 1,
    "event_mapping_id": 10,
    "camera": { ... },
    "target_preset": { ... },
    "home_preset": { ... },
    "delay_time": 45,
    "is_enable": true,
    "priority": 2,
    "created_at": "2026-01-07T10:00:00.000+09:00",
    "updated_at": "2026-01-07T12:00:00.000+09:00"
  }
}
```

#### 7.3.6 EventMappingCamera 삭제

**Endpoint**: `DELETE /api/integrations/event-mappings/{mapping_id}/cameras/{config_id}`

**Path Parameters**:
- `mapping_id` (int, required): EventMapping ID
- `config_id` (int, required): EventMappingCamera ID

**Request Example**:
```http
DELETE /api/integrations/event-mappings/10/cameras/1 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Event mapping camera deleted successfully",
  "data": null
}
```

#### 7.3.7 FK 정책 및 CASCADE 동작

| 관계 | 동작 | 정책 | 설명 |
|------|------|------|------|
| EventMapping → EventMappingCamera | EventMapping 삭제 | `CASCADE` | 연결된 EventMappingCamera 모두 삭제 |
| Camera → EventMappingCamera | Camera 삭제 | `SET NULL` | EventMappingCamera.camera_id → NULL |
| CameraPreset → EventMappingCamera | CameraPreset 삭제 | `SET NULL` | target_preset_id, home_preset_id → NULL |

> **참고**: Camera/CameraPreset 삭제 시 EventMappingCamera 자체는 유지되며, 연결만 해제됩니다.
> EventMapping 삭제 시에만 EventMappingCamera가 함께 삭제됩니다.

### 7.4 Event Mapping Speakers API

Event Mapping에 연동된 스피커 방송 동작을 관리합니다.

> **아키텍처 원칙**:
> - EventMapping은 다양한 Action 타입(Camera, Speaker, 3rd Party)의 **Base 노드**
> - 각 Action 타입은 독립적인 하위 API로 관리 (`/cameras`, `/speakers`, `/externals`)
> - EventMapping API에 `include_speakers` 같은 특정 타입 종속 파라미터 **사용하지 않음**

#### 7.4.1 EventMappingSpeaker 목록 조회

**Endpoint**: `GET /api/integrations/event-mappings/{mapping_id}/speakers`

**Path Parameters**:
- `mapping_id` (int, required): EventMapping ID

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| page | integer | N | 페이지 번호 (기본값: 1) |
| limit | integer | N | 페이지당 항목 수 (기본값: 20, 최대: 100) |

**Request Example**:
```http
GET /api/integrations/event-mappings/10/speakers?page=1&limit=20 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Response Example** (200 OK):

> **Nested Response 규칙**:
> - 주체(EventMappingSpeaker)의 `created_at`, `updated_at` 포함
> - Nested 객체(speaker, file_group)는 **Full Property** (timestamp 제외)

```json
{
  "success": true,
  "message": "Event mapping speakers retrieved successfully",
  "data": {
    "items": [
      {
        "id": 1,
        "event_mapping_id": 10,
        "speaker": {
          "id": 301,
          "number_device": 1,
          "group_device": 1,
          "name_device": "Main-Speaker-01",
          "type_device": "Speaker",
          "version": "1.0.0",
          "status": "ACTIVATED",
          "is_enable": true,
          "speaker_type": "NORMAL",
          "server_id": 1,
          "description": "메인 방송용 스피커",
          "geolocation": null
        },
        "file_group": {
          "id": 1,
          "server_id": 1,
          "group_id": 100,
          "group_name": "경고 방송 그룹",
          "files": ["alert_01.wav", "alert_02.wav"]
        },
        "repeat_count": 3,
        "is_enable": true,
        "priority": 1,
        "created_at": "2026-01-07T10:00:00.000+09:00",
        "updated_at": "2026-01-07T10:00:00.000+09:00"
      }
    ],
    "total": 1
  }
}
```

**Error Response** (404 Not Found):
```json
{
  "success": false,
  "message": "Event mapping with id 999 not found"
}
```

**Error Response (422 Validation Error)** - 잘못된 쿼리 파라미터:
```json
{
  "success": false,
  "message": "Validation error",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [
      {"field": "page", "message": "page must be a positive integer"},
      {"field": "limit", "message": "limit must be between 1 and 100"}
    ]
  }
}
```

#### 7.4.2 EventMappingSpeaker 단일 조회

**Endpoint**: `GET /api/integrations/event-mappings/{mapping_id}/speakers/{config_id}`

**Path Parameters**:
- `mapping_id` (int, required): EventMapping ID
- `config_id` (int, required): EventMappingSpeaker ID

**Request Example**:
```http
GET /api/integrations/event-mappings/10/speakers/1 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Event mapping speaker retrieved successfully",
  "data": {
    "id": 1,
    "event_mapping_id": 10,
    "speaker": {
      "id": 301,
      "number_device": 1,
      "group_device": 1,
      "name_device": "Main-Speaker-01",
      "type_device": "Speaker",
      "version": "1.0.0",
      "status": "ACTIVATED",
      "is_enable": true,
      "speaker_type": "NORMAL",
      "server_id": 1,
      "description": "메인 방송용 스피커",
      "geolocation": null
    },
    "file_group": {
      "id": 1,
      "server_id": 1,
      "group_id": 100,
      "group_name": "경고 방송 그룹",
      "files": ["alert_01.wav", "alert_02.wav"]
    },
    "repeat_count": 3,
    "is_enable": true,
    "priority": 1,
    "created_at": "2026-01-07T10:00:00.000+09:00",
    "updated_at": "2026-01-07T10:00:00.000+09:00"
  }
}
```

#### 7.4.3 EventMappingSpeaker 생성

**Endpoint**: `POST /api/integrations/event-mappings/{mapping_id}/speakers`

**Path Parameters**:
- `mapping_id` (int, required): EventMapping ID

**Request Body**:

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| speaker_id | integer | Y | 대상 스피커 ID |
| file_group_id | integer | N | 방송 파일 그룹 ID |
| repeat_count | integer | N | 방송 반복 횟수 (기본값: 1, 최소값: 1) |
| is_enable | boolean | N | 활성화 여부 (기본값: true) |
| priority | integer | N | 실행 우선순위 (Optional) |

**Request Example**:
```http
POST /api/integrations/event-mappings/10/speakers HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "speaker_id": 301,
  "file_group_id": 1,
  "repeat_count": 3,
  "is_enable": true,
  "priority": 1
}
```

**Response Example** (201 Created):

> **Nested Response 규칙**:
> - 주체(EventMappingSpeaker)의 `created_at`, `updated_at` 포함
> - Nested 객체(speaker, file_group)는 **Full Property** (timestamp 제외)

```json
{
  "success": true,
  "message": "Event mapping speaker created successfully",
  "data": {
    "id": 1,
    "event_mapping_id": 10,
    "speaker": {
      "id": 301,
      "number_device": 1,
      "group_device": 1,
      "name_device": "Main-Speaker-01",
      "type_device": "Speaker",
      "version": "1.0.0",
      "status": "ACTIVATED",
      "is_enable": true,
      "speaker_type": "NORMAL",
      "server_id": 1,
      "description": "메인 방송용 스피커",
      "geolocation": null
    },
    "file_group": {
      "id": 1,
      "server_id": 1,
      "group_id": 100,
      "group_name": "경고 방송 그룹",
      "files": ["alert_01.wav", "alert_02.wav"]
    },
    "repeat_count": 3,
    "is_enable": true,
    "priority": 1,
    "created_at": "2026-01-07T10:00:00.000+09:00",
    "updated_at": "2026-01-07T10:00:00.000+09:00"
  }
}
```

**Error Response** (404 Not Found):
```json
{
  "success": false,
  "message": "Speaker with id 999 not found"
}
```

**Error Response** (422 Unprocessable Entity):
```json
{
  "detail": [
    {
      "loc": ["body", "repeat_count"],
      "msg": "Input should be greater than or equal to 1",
      "type": "value_error"
    }
  ]
}
```

#### 7.4.4 EventMappingSpeaker 수정 (부분)

**Endpoint**: `PATCH /api/integrations/event-mappings/{mapping_id}/speakers/{config_id}`

**Path Parameters**:
- `mapping_id` (int, required): EventMapping ID
- `config_id` (int, required): EventMappingSpeaker ID

**Request Body** (모든 필드 Optional):

| 필드 | 타입 | 설명 |
|------|------|------|
| speaker_id | integer | 대상 스피커 ID |
| file_group_id | integer | 방송 파일 그룹 ID |
| repeat_count | integer | 방송 반복 횟수 (최소값: 1) |
| is_enable | boolean | 활성화 여부 |
| priority | integer | 실행 우선순위 |

**Request Example**:
```http
PATCH /api/integrations/event-mappings/10/speakers/1 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "repeat_count": 5,
  "is_enable": false
}
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Event mapping speaker updated successfully",
  "data": {
    "id": 1,
    "event_mapping_id": 10,
    "speaker": {
      "id": 301,
      "number_device": 1,
      "group_device": 1,
      "name_device": "Main-Speaker-01",
      "type_device": "Speaker",
      "version": "1.0.0",
      "status": "ACTIVATED",
      "is_enable": true,
      "speaker_type": "NORMAL",
      "server_id": 1,
      "description": "메인 방송용 스피커",
      "geolocation": null
    },
    "file_group": {
      "id": 1,
      "server_id": 1,
      "group_id": 100,
      "group_name": "경고 방송 그룹",
      "files": ["alert_01.wav", "alert_02.wav"]
    },
    "repeat_count": 5,
    "is_enable": false,
    "priority": 1,
    "created_at": "2026-01-07T10:00:00.000+09:00",
    "updated_at": "2026-01-07T10:30:00.000+09:00"
  }
}
```

#### 7.4.5 EventMappingSpeaker 수정 (전체)

**Endpoint**: `PUT /api/integrations/event-mappings/{mapping_id}/speakers/{config_id}`

**Path Parameters**:
- `mapping_id` (int, required): EventMapping ID
- `config_id` (int, required): EventMappingSpeaker ID

**Request Body** (모든 필드 교체):

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| speaker_id | integer | Y | 대상 스피커 ID |
| file_group_id | integer | N | 방송 파일 그룹 ID |
| repeat_count | integer | Y | 방송 반복 횟수 (최소값: 1) |
| is_enable | boolean | Y | 활성화 여부 |
| priority | integer | N | 실행 우선순위 |

**Request Example**:
```http
PUT /api/integrations/event-mappings/10/speakers/1 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "speaker_id": 302,
  "file_group_id": 2,
  "repeat_count": 2,
  "is_enable": true,
  "priority": 2
}
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Event mapping speaker replaced successfully",
  "data": {
    "id": 1,
    "event_mapping_id": 10,
    "speaker": {
      "id": 302,
      "number_device": 2,
      "group_device": 1,
      "name_device": "Sub-Speaker-02",
      "type_device": "Speaker",
      "version": "1.0.0",
      "status": "ACTIVATED",
      "is_enable": true,
      "speaker_type": "NORMAL",
      "server_id": 1,
      "description": "서브 방송용 스피커",
      "geolocation": null
    },
    "file_group": {
      "id": 2,
      "server_id": 1,
      "group_id": 101,
      "group_name": "긴급 방송 그룹",
      "files": ["emergency_01.wav"]
    },
    "repeat_count": 2,
    "is_enable": true,
    "priority": 2,
    "created_at": "2026-01-07T10:00:00.000+09:00",
    "updated_at": "2026-01-07T11:00:00.000+09:00"
  }
}
```

#### 7.4.6 EventMappingSpeaker 삭제

**Endpoint**: `DELETE /api/integrations/event-mappings/{mapping_id}/speakers/{config_id}`

**Path Parameters**:
- `mapping_id` (int, required): EventMapping ID
- `config_id` (int, required): EventMappingSpeaker ID

**Request Example**:
```http
DELETE /api/integrations/event-mappings/10/speakers/1 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Event mapping speaker deleted successfully"
}
```

#### 7.4.7 FK 정책 및 CASCADE 동작

| 관계 | 동작 | 정책 | 설명 |
|------|------|------|------|
| EventMapping → EventMappingSpeaker | EventMapping 삭제 | `CASCADE` | 연결된 EventMappingSpeaker 모두 삭제 |
| Speaker → EventMappingSpeaker | Speaker 삭제 | `SET NULL` | EventMappingSpeaker.speaker_id → NULL |
| FileGroup → EventMappingSpeaker | FileGroup 삭제 | `SET NULL` | EventMappingSpeaker.file_group_id → NULL |

> **참고**: Speaker/FileGroup 삭제 시 EventMappingSpeaker 자체는 유지되며, 연결만 해제됩니다.
> EventMapping 삭제 시에만 EventMappingSpeaker가 함께 삭제됩니다.

---

### 7.5 Event Mapping Lamps API

> **v3.4 신규**: PRD_Lamp_Device.md v1.1 참조
> EventMapping에 연동된 경광등 설정 CRUD API.

**리소스 구조**:
```
/api/integrations/event-mappings/{mapping_id}/lamps           - EventMappingLamp 목록/생성
/api/integrations/event-mappings/{mapping_id}/lamps/{id}      - EventMappingLamp 상세/수정/삭제
```

#### 7.5.1 EventMappingLamp 목록 조회

**Endpoint**: `GET /api/integrations/event-mappings/{mapping_id}/lamps`

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| mapping_id | integer | Y | EventMapping ID |

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| page | integer | N | 1 | 페이지 번호 |
| limit | integer | N | 20 | 페이지당 항목 수 (max: 100) |
| lamp_id | integer | N | - | Lamp ID 필터 |
| is_enable | boolean | N | - | 활성화 여부 필터 |

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Event mapping lamps retrieved successfully",
  "data": [
    {
      "id": 1,
      "event_mapping": {
        "id": 10,
        "name_event": "침입 감지 경광등 연동",
        "category_event_mapping": "FENCE_SENSOR_ONLY"
      },
      "lamp": {
        "id": 501,
        "number_device": 5001,
        "group_device": 0,
        "name_device": "Lamp-A-1",
        "type_device": "Lamp",
        "version": "v1.0.0",
        "status": "ACTIVATED",
        "is_enable": true,
        "ip_address": "192.168.1.109",
        "ip_port": 80,
        "user_name": "admin",
        "description": "GOP 1구역 전방 경광등",
        "geolocation": {
          "location": "GOP 1구역 전방 초소",
          "latitude": 38.1234,
          "longitude": 127.5678
        }
      },
      "color": "Red",
      "buzzer_time": 5,
      "buzzer_sound": "PI-PI-PI",
      "light_mode": "steady",
      "is_enable": true,
      "priority": 1,
      "created_at": "2026-01-26T10:00:00.000Z",
      "updated_at": "2026-01-26T10:00:00.000Z"
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

> **참고**: Nested Response에서 `lamp.user_password`는 보안상 제외됩니다.

#### 7.5.2 EventMappingLamp 단일 조회

**Endpoint**: `GET /api/integrations/event-mappings/{mapping_id}/lamps/{id}`

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| mapping_id | integer | Y | EventMapping ID |
| id | integer | Y | EventMappingLamp ID |

**Response (200 OK)**: 목록 조회의 단일 객체 구조

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "Event mapping lamp with id 999 not found",
  "error": {"code": "NOT_FOUND", "details": null}
}
```

#### 7.5.3 EventMappingLamp 생성

**Endpoint**: `POST /api/integrations/event-mappings/{mapping_id}/lamps`

**Request Body**:
```json
{
  "event_mapping_id": 10,
  "lamp_id": 501,
  "color": "Red",
  "buzzer_time": 5,
  "buzzer_sound": "PI-PI-PI",
  "light_mode": "steady",
  "is_enable": true,
  "priority": 1
}
```

**Request Body 필드**:
| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| event_mapping_id | integer | Y | - | EventMapping ID |
| lamp_id | integer | Y | - | Lamp ID |
| color | string | N | "Red" | 경광등 색상 (EnumLampColor) |
| buzzer_time | integer | N | 5 | 부저 작동 시간 (초, ≥0) |
| buzzer_sound | string | N | "PI-PI-PI" | 부저 소리 패턴 (EnumBuzzerSound) |
| light_mode | string | N | "steady" | 점등 모드 (EnumLightMode) |
| is_enable | boolean | N | true | 활성화 여부 |
| priority | integer | N | 1 | 우선순위 (≥1, 낮을수록 높음) |

**Enum 허용값**:
- **color (EnumLampColor)**: Red, Orange, Green, Blue, White
- **buzzer_sound (EnumBuzzerSound)**: Fire A-WANG, Emergency, Ambulance, PI-PI-PI, PI_continue
- **light_mode (EnumLightMode)**: steady, blinking

**Response (201 Created)**: 생성된 EventMappingLamp 객체 (Nested Response)

**Error Response (409 Conflict)** - 중복 매핑:
```json
{
  "success": false,
  "message": "EventMappingLamp with event_mapping_id 10 and lamp_id 501 already exists",
  "error": {"code": "CONFLICT", "details": null}
}
```

#### 7.5.4 EventMappingLamp 수정 (PATCH)

**Endpoint**: `PATCH /api/integrations/event-mappings/{mapping_id}/lamps/{id}`

**Request Body**: 수정할 필드만 포함 (모든 필드 선택적)
```json
{
  "color": "Orange",
  "buzzer_time": 10,
  "light_mode": "blinking"
}
```

**Response (200 OK)**: 수정된 EventMappingLamp 객체

#### 7.5.5 EventMappingLamp 수정 (PUT)

**Endpoint**: `PUT /api/integrations/event-mappings/{mapping_id}/lamps/{id}`

**Request Body**: 전체 필드 포함 (EventMappingLampCreate와 동일, 모든 필수 필드 포함)

**Response (200 OK)**: 수정된 EventMappingLamp 객체

#### 7.5.6 EventMappingLamp 삭제

**Endpoint**: `DELETE /api/integrations/event-mappings/{mapping_id}/lamps/{id}`

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Event mapping lamp deleted successfully"
}
```

#### 7.5.7 FK 정책 및 CASCADE 동작

| 관계 | 동작 | 정책 | 설명 |
|------|------|------|------|
| EventMapping → EventMappingLamp | EventMapping 삭제 | `CASCADE` | 연결된 EventMappingLamp 모두 삭제 |
| Lamp → EventMappingLamp | Lamp 삭제 | `SET NULL` | EventMappingLamp.lamp_id → NULL |

> **참고**: Lamp 삭제 시 EventMappingLamp 자체는 유지되며, `lamp_id`만 NULL로 설정됩니다.
> EventMapping 삭제 시에만 EventMappingLamp가 함께 삭제됩니다.

#### 7.5.8 ConfigChangeLog 연동

EventMappingLamp CRUD 작업 시 자동으로 ConfigChangeLog가 생성됩니다.

| 작업 | resource_type | action |
|------|---------------|--------|
| POST | EVENT_MAPPING_LAMP | CREATED |
| PATCH/PUT | EVENT_MAPPING_LAMP | UPDATED |
| DELETE | EVENT_MAPPING_LAMP | DELETED |

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

**Endpoint**: `GET /api/servers/categories`

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| page | integer | N | 페이지 번호 (기본값: 1) |
| limit | integer | N | 페이지당 항목 수 (기본값: 20, 최대: 100) |

**Request Example**:
```http
GET /api/servers/categories?page=1&limit=20 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

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

**Error Response (422 Validation Error)** - 잘못된 쿼리 파라미터:
```json
{
  "success": false,
  "message": "Validation error",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [
      {"field": "page", "message": "page must be a positive integer"},
      {"field": "limit", "message": "limit must be between 1 and 100"}
    ]
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
        "user_name": "admin",
        "user_password": "password123",
        "threshold_config": {
          "cpu": {"warning": 80, "critical": 95},
          "ram": {"warning": 75, "critical": 90},
          "disk": {"warning": 80, "critical": 95},
          "network": {"warning_mbps": 800, "critical_mbps": 950}
        },
        "created_at": "2025-12-29T06:46:01.150000",
        "updated_at": "2025-12-29T06:46:01.150000"
      }
    ]
  }
}
```

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "Server category with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

#### 8.2.3 카테고리 생성

**Endpoint**: `POST /api/servers/categories`

**Request Example**:
```http
POST /api/servers/categories HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "name": "새로운 서버 카테고리",
  "type_server": "ETC",
  "description": "카테고리 설명",
  "sort_order": 10
}
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

**Endpoint**: `PATCH /api/servers/categories/{category_id}`

**Request Example**:
```http
PATCH /api/servers/categories/10 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "description": "수정된 설명",
  "sort_order": 5
}
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| category_id | integer | Y | 카테고리 ID |

**Request Body** (모든 필드 선택적):
```json
{
  "description": "수정된 설명",
  "sort_order": 5
}
```

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Server category updated successfully",
  "data": {
    "id": 10,
    "name": "VMS 서버",
    "type_server": "VMS",
    "description": "수정된 설명",
    "sort_order": 5,
    "created_at": "2025-12-29T07:00:00.000000",
    "updated_at": "2026-01-12T10:30:00.000000"
  }
}
```

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "Server category with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

#### 8.2.5 카테고리 수정 (전체)

**Endpoint**: `PUT /api/servers/categories/{category_id}`

**Request Example**:
```http
PUT /api/servers/categories/10 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "name": "수정된 카테고리명",
  "type_server": "VMS",
  "description": "수정된 설명",
  "sort_order": 1
}
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| category_id | integer | Y | 카테고리 ID |

**Request Body** (모든 필드 필수):
```json
{
  "name": "수정된 카테고리명",
  "type_server": "VMS",
  "description": "수정된 설명",
  "sort_order": 1
}
```

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Server category replaced successfully",
  "data": {
    "id": 10,
    "name": "수정된 카테고리명",
    "type_server": "VMS",
    "description": "수정된 설명",
    "sort_order": 1,
    "created_at": "2025-12-29T07:00:00.000000",
    "updated_at": "2026-01-12T10:35:00.000000"
  }
}
```

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "Server category with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

#### 8.2.6 카테고리 삭제

**Endpoint**: `DELETE /api/servers/categories/{category_id}`

**Request Example**:
```http
DELETE /api/servers/categories/10 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| category_id | integer | Y | 카테고리 ID |

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

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "Server category with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

> **주의**: 카테고리 삭제 시 해당 카테고리에 속한 모든 서버도 함께 삭제됩니다 (Cascade Delete).

---

### 8.3 Server Instance API

개별 서버 인스턴스를 관리합니다.

#### 8.3.1 서버 목록 조회

**Endpoint**: `GET /api/servers`

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| page | integer | N | 페이지 번호 (기본값: 1) |
| limit | integer | N | 페이지당 항목 수 (기본값: 20, 최대: 100) |
| category_id | integer | N | 카테고리 ID 필터 |
| status | string | N | 상태 필터 (NORMAL, WARNING, ERROR) |

**Request Example**:
```http
GET /api/servers?category_id=1&status=NORMAL HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

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
      "user_name": "admin",
      "user_password": "password123",
      "threshold_config": {
        "cpu": {"warning": 80, "critical": 95},
        "ram": {"warning": 75, "critical": 90},
        "disk": {"warning": 80, "critical": 95},
        "network": {"warning_mbps": 800, "critical_mbps": 950}
      },
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

> **Note (v2.9 변경)**: `cpu_usage`, `ram_usage`, `disk_usage`, `network_throughput` 필드는 `server_metrics` API로 분리되었습니다. 실시간 리소스 모니터링은 [8.6 Server Metrics API](#86-server-metrics-api)를 사용하세요.

**Error Response (422 Validation Error)** - 잘못된 쿼리 파라미터:
```json
{
  "success": false,
  "message": "Validation error",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [
      {"field": "page", "message": "page must be a positive integer"},
      {"field": "limit", "message": "limit must be between 1 and 100"},
      {"field": "status", "message": "status must be one of: NORMAL, WARNING, ERROR"}
    ]
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

**Request Example**:
```http
GET /api/servers/1 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Response Example (200 OK)**:
```json
{
  "success": true,
  "message": "Server retrieved successfully",
  "data": {
    "id": 1,
    "category_id": 1,
    "name": "VMS-ab1120",
    "status": "NORMAL",
    "ip_address": "192.168.1.10",
    "port": 8080,
    "hostname": "vms-server-01",
    "user_name": "admin",
    "user_password": "password123",
    "threshold_config": {
      "cpu": {"warning": 80, "critical": 95},
      "ram": {"warning": 75, "critical": 90},
      "disk": {"warning": 80, "critical": 95},
      "network": {"warning_mbps": 800, "critical_mbps": 950}
    },
    "created_at": "2025-12-29T06:46:01.150000",
    "updated_at": "2025-12-29T06:46:01.150000"
  },
  "meta": {
    "timestamp": "2026-01-12T10:00:00.100Z",
    "request_id": "550e8500-e29b-41d4-a716-446655440000"
  }
}
```

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "Server with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

#### 8.3.3 서버 생성

```http
POST /api/servers
```

**Request Example**:
```http
POST /api/servers HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "category_id": 1,
  "name": "VMS-ab1122",
  "status": "NORMAL",
  "ip_address": "192.168.1.12",
  "port": 8080,
  "hostname": "vms-server-03",
  "user_name": "admin",
  "user_password": "password123",
  "threshold_config": {
    "cpu": {"warning": 80, "critical": 95},
    "ram": {"warning": 75, "critical": 90},
    "disk": {"warning": 80, "critical": 95},
    "network": {"warning_mbps": 800, "critical_mbps": 950}
  }
}
```

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| category_id | integer | Y | - | 카테고리 ID |
| name | string | Y | - | 서버 이름 |
| status | EnumServerStatus | N | NORMAL | 상태 |
| ip_address | string | Y | - | IP 주소 |
| port | integer | Y | - | 포트 번호 |
| hostname | string | N | null | 호스트명 |
| user_name | string | N | null | 접속 사용자명 *(v2.4 신규)* |
| user_password | string | N | null | 접속 비밀번호 *(v2.4 신규)* |
| threshold_config | object | N | null | 임계치 설정 JSONB *(v2.9 신규)* |

> **Note (v2.9 변경)**: `cpu_usage`, `ram_usage`, `disk_usage`, `network_throughput` 필드가 제거되었습니다. 리소스 메트릭은 [8.6 Server Metrics API](#86-server-metrics-api)를 통해 기록합니다.

**Response Example (201 Created)**:
```json
{
  "success": true,
  "message": "Server created successfully",
  "data": {
    "id": 10,
    "category_id": 1,
    "name": "VMS-ab1122",
    "status": "NORMAL",
    "ip_address": "192.168.1.12",
    "port": 8080,
    "hostname": "vms-server-03",
    "user_name": "admin",
    "user_password": "password123",
    "threshold_config": {
      "cpu": {"warning": 80, "critical": 95},
      "ram": {"warning": 75, "critical": 90},
      "disk": {"warning": 80, "critical": 95},
      "network": {"warning_mbps": 800, "critical_mbps": 950}
    },
    "created_at": "2026-01-12T10:30:00.000000",
    "updated_at": "2026-01-12T10:30:00.000000"
  },
  "meta": {
    "timestamp": "2026-01-12T10:30:00.100Z",
    "request_id": "550e8501-e29b-41d4-a716-446655440000"
  }
}
```

**Error Response (404 Not Found)** - 존재하지 않는 카테고리:
```json
{
  "success": false,
  "message": "ServerCategory with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

**Error Response (422 Validation Error)**:
```json
{
  "success": false,
  "message": "Validation error",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [
      {"field": "category_id", "message": "Field required"},
      {"field": "name", "message": "Field required"}
    ]
  }
}
```

#### 8.3.4 서버 수정 (부분)

**Endpoint**: `PATCH /api/servers/{server_id}`

**Request Example**:
```http
PATCH /api/servers/1 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "status": "WARNING",
  "threshold_config": {
    "cpu": {"warning": 80, "critical": 95},
    "ram": {"warning": 75, "critical": 90},
    "disk": {"warning": 80, "critical": 95},
    "network": {"warning_mbps": 800, "critical_mbps": 950}
  }
}
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| server_id | integer | Y | 서버 ID |

**Request Body** (모든 필드 선택적):
```json
{
  "status": "WARNING",
  "threshold_config": {
    "cpu": {"warning": 80, "critical": 95},
    "ram": {"warning": 75, "critical": 90},
    "disk": {"warning": 80, "critical": 95},
    "network": {"warning_mbps": 800, "critical_mbps": 950}
  }
}
```

> **사용 사례 (v2.9 변경)**: 서버 상태 및 임계치 설정 업데이트에 사용. 리소스 메트릭(CPU, RAM 등)은 [8.6 Server Metrics API](#86-server-metrics-api)를 통해 기록합니다.

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Server updated successfully",
  "data": {
    "id": 1,
    "category_id": 1,
    "name": "VMS-ab1120",
    "status": "WARNING",
    "ip_address": "192.168.1.10",
    "port": 8080,
    "hostname": "vms-server-01",
    "user_name": "admin",
    "user_password": "password123",
    "threshold_config": {
      "cpu": {"warning": 80, "critical": 95},
      "ram": {"warning": 75, "critical": 90},
      "disk": {"warning": 80, "critical": 95},
      "network": {"warning_mbps": 800, "critical_mbps": 950}
    },
    "created_at": "2025-12-29T07:00:00.000000",
    "updated_at": "2026-01-12T11:00:00.000000"
  }
}
```

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "Server with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

#### 8.3.5 서버 수정 (전체)

**Endpoint**: `PUT /api/servers/{server_id}`

**Request Example**:
```http
PUT /api/servers/1 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "category_id": 1,
  "name": "VMS-ab1120-updated",
  "status": "NORMAL",
  "ip_address": "192.168.1.10",
  "port": 8080,
  "hostname": "vms-server-01",
  "user_name": "admin",
  "user_password": "newpassword123",
  "threshold_config": {
    "cpu": {"warning": 80, "critical": 95},
    "ram": {"warning": 75, "critical": 90},
    "disk": {"warning": 80, "critical": 95},
    "network": {"warning_mbps": 800, "critical_mbps": 950}
  }
}
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| server_id | integer | Y | 서버 ID |

**Request Body** (모든 필드 필수):
```json
{
  "category_id": 1,
  "name": "VMS-ab1120-updated",
  "status": "NORMAL",
  "ip_address": "192.168.1.10",
  "port": 8080,
  "hostname": "vms-server-01",
  "user_name": "admin",
  "user_password": "newpassword123",
  "threshold_config": {
    "cpu": {"warning": 80, "critical": 95},
    "ram": {"warning": 75, "critical": 90},
    "disk": {"warning": 80, "critical": 95},
    "network": {"warning_mbps": 800, "critical_mbps": 950}
  }
}
```

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| category_id | integer | Y | - | 카테고리 ID |
| name | string | Y | - | 서버 이름 |
| status | EnumServerStatus | N | NORMAL | 상태 |
| ip_address | string | Y | - | IP 주소 |
| port | integer | Y | - | 포트 번호 |
| hostname | string | N | null | 호스트명 |
| user_name | string | N | null | 접속 사용자명 |
| user_password | string | N | null | 접속 비밀번호 |
| threshold_config | object | N | null | 임계치 설정 JSONB *(v2.9 신규)* |

> **Note (v2.9 변경)**: `cpu_usage`, `ram_usage`, `disk_usage`, `network_throughput` 필드가 제거되었습니다.

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Server replaced successfully",
  "data": {
    "id": 1,
    "category_id": 1,
    "name": "VMS-ab1120-updated",
    "status": "NORMAL",
    "ip_address": "192.168.1.10",
    "port": 8080,
    "hostname": "vms-server-01",
    "user_name": "admin",
    "user_password": "newpassword123",
    "threshold_config": {
      "cpu": {"warning": 80, "critical": 95},
      "ram": {"warning": 75, "critical": 90},
      "disk": {"warning": 80, "critical": 95},
      "network": {"warning_mbps": 800, "critical_mbps": 950}
    },
    "created_at": "2025-12-29T07:00:00.000000",
    "updated_at": "2026-01-12T11:05:00.000000"
  }
}
```

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "Server with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

#### 8.3.6 서버 삭제

**Endpoint**: `DELETE /api/servers/{server_id}`

**Request Example**:
```http
DELETE /api/servers/1 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| server_id | integer | Y | 서버 ID |

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

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "Server with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
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
          "user_name": "admin",
          "user_password": "password123",
          "threshold_config": {
            "cpu": {"warning": 80, "critical": 95},
            "ram": {"warning": 75, "critical": 90},
            "disk": {"warning": 80, "critical": 95},
            "network": {"warning_mbps": 800, "critical_mbps": 950}
          },
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

### 8.6 Server Metrics API

서버의 리소스 사용량을 시계열로 기록하고 조회합니다.

> **PRD Reference**: PRD_System_Event.md Section 2.4

**리소스 구조**:
```
/api/servers/{server_id}/metrics        - 서버 메트릭 CRUD
/api/servers/{server_id}/metrics/latest - 최신 메트릭 조회
```

#### 8.6.1 메트릭 기록 (Create)

**Endpoint**: `POST /api/servers/{server_id}/metrics`

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| server_id | integer | Y | 서버 ID |

**Request Body**:
```json
{
  "cpu_usage": 45.5,
  "ram_usage": 62.0,
  "ram_total_gb": 64.0,
  "ram_used_gb": 39.68,
  "disk_usage": 78.5,
  "disk_total_gb": 500.0,
  "disk_used_gb": 392.5,
  "network_in_mbps": 125.0,
  "network_out_mbps": 50.0,
  "process_count": 142,
  "detail": {"gpu_usage": 35.0},
  "collected_at": "2026-01-15T10:30:00.000000"
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| cpu_usage | float | N | CPU 사용률 (%) |
| ram_usage | float | N | RAM 사용률 (%) |
| ram_total_gb | float | N | 전체 RAM (GB) |
| ram_used_gb | float | N | 사용 RAM (GB) |
| disk_usage | float | N | 디스크 사용률 (%) |
| disk_total_gb | float | N | 전체 디스크 (GB) |
| disk_used_gb | float | N | 사용 디스크 (GB) |
| network_in_mbps | float | N | 수신 네트워크 (Mbps) |
| network_out_mbps | float | N | 송신 네트워크 (Mbps) |
| process_count | integer | N | 프로세스 수 |
| detail | object | N | 추가 상세 정보 (JSONB) |
| collected_at | datetime | N | 수집 시간 (기본값: 현재 시간) |

**Response (201 Created)**:
```json
{
  "success": true,
  "message": "Server metrics recorded successfully",
  "data": {
    "id": 1,
    "server_id": 1,
    "cpu_usage": 45.5,
    "ram_usage": 62.0,
    "ram_total_gb": 64.0,
    "ram_used_gb": 39.68,
    "disk_usage": 78.5,
    "disk_total_gb": 500.0,
    "disk_used_gb": 392.5,
    "network_in_mbps": 125.0,
    "network_out_mbps": 50.0,
    "process_count": 142,
    "detail": {"gpu_usage": 35.0},
    "collected_at": "2026-01-15T10:30:00.000000",
    "created_at": "2026-01-15T10:30:01.000000",
    "threshold_exceeded": {
      "disk": {"level": "warning", "value": 78.5, "threshold": 70.0}
    }
  }
}
```

**임계치 초과 시**: 서버의 `threshold_config`에 설정된 임계치를 초과하면 자동으로 `SystemEvent`가 생성됩니다.

#### 8.6.2 메트릭 이력 조회

**Endpoint**: `GET /api/servers/{server_id}/metrics`

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| start_date | datetime | N | 시작 일시 (ISO 8601) |
| end_date | datetime | N | 종료 일시 (ISO 8601) |
| limit | integer | N | 최대 조회 건수 (기본값: 100, 최대: 1000) |

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Server metrics retrieved successfully",
  "data": [
    {
      "id": 10,
      "server_id": 1,
      "cpu_usage": 45.5,
      "ram_usage": 62.0,
      "collected_at": "2026-01-15T10:30:00.000000"
    }
  ]
}
```

#### 8.6.3 최신 메트릭 조회

**Endpoint**: `GET /api/servers/{server_id}/metrics/latest`

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Latest server metrics retrieved successfully",
  "data": {
    "metrics": {
      "id": 10,
      "server_id": 1,
      "cpu_usage": 45.5,
      "ram_usage": 62.0,
      "collected_at": "2026-01-15T10:30:00.000000"
    },
    "threshold_config": {
      "cpu": {"warning": 80, "critical": 95},
      "ram": {"warning": 75, "critical": 90},
      "disk": {"warning": 80, "critical": 95},
      "network": {"warning_mbps": 800, "critical_mbps": 950}
    }
  }
}
```

#### 8.6.4 메트릭 삭제

**Endpoint**: `DELETE /api/servers/{server_id}/metrics`

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| before_date | datetime | N | 이 날짜 이전의 메트릭 삭제 |

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Deleted 150 metrics",
  "data": {"deleted_count": 150}
}
```

---

### 8.7 System Events API

서버 레벨의 시스템 이벤트(로그, 알람)를 관리합니다.

> **PRD Reference**: PRD_System_Event.md Section 3

**리소스 구조**:
```
/api/system-events          - 이벤트 목록/생성
/api/system-events/{id}     - 단건 조회/수정/삭제
/api/system-events/{id}/acknowledge - 확인 처리
/api/system-events/summary  - 요약 통계
```

#### 8.7.1 이벤트 유형 및 심각도

**EnumSystemEventType** (이벤트 유형 - 15종, PRD_SystemEvent_Sync.md v1.2):

> **v3.1 업데이트**: USER_* 9종 → UserLoginLog 이전, ConfigChangeLog 중복 4종 제거

| 값 | 설명 | 분류 |
|----|------|------|
| RESOURCE_THRESHOLD | 리소스 임계치 초과 | 리소스 (1종) |
| SERVER_CONNECTED | 서버 연결됨 | 서버 상태 (3종) |
| SERVER_DISCONNECTED | 서버 연결 해제됨 | 서버 상태 |
| SERVER_ERROR | 서버 오류 | 서버 상태 |
| SERVICE_STARTED | 서비스 시작됨 | 서비스 상태 (3종) |
| SERVICE_STOPPED | 서비스 중지됨 | 서비스 상태 |
| SERVICE_ERROR | 서비스 오류 | 서비스 상태 |
| CONNECTION_LOST | 연결 끊김 | 연결 상태 (2종) |
| CONNECTION_RESTORED | 연결 복구됨 | 연결 상태 |
| SECURITY_ALERT | 보안 경고 | 보안 (1종) |
| DEVICE_CONNECTED | 디바이스 연결됨 | 디바이스 연결 (1종) |
| BACKUP_STARTED | 백업 시작됨 | 백업 (3종) |
| BACKUP_COMPLETED | 백업 완료됨 | 백업 |
| BACKUP_FAILED | 백업 실패함 | 백업 |
| SYSTEM_UPDATE | 시스템 업데이트 | 시스템 (1종) |

**EnumSystemEventSeverity** (심각도):
| 값 | 설명 |
|----|------|
| INFO | 정보 |
| WARNING | 경고 |
| ERROR | 오류 |
| CRITICAL | 심각 |

#### 8.7.2 이벤트 목록 조회

**Endpoint**: `GET /api/system-events`

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| page | integer | N | 페이지 번호 (기본값: 1) |
| limit | integer | N | 페이지당 항목 수 (기본값: 20, 최대: 100) |
| server_id | integer | N | 서버 ID 필터 |
| type_event | string | N | 이벤트 유형 필터 |
| severity | string | N | 심각도 필터 |
| is_acknowledged | boolean | N | 확인 여부 필터 |
| start_date | datetime | N | 시작 일시 |
| end_date | datetime | N | 종료 일시 |

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "System events retrieved successfully",
  "data": [
    {
      "id": 1,
      "server_id": 1,
      "server_description": "VMS-ab1120",
      "type_event": "threshold_warning",
      "severity": "WARNING",
      "title": "CPU 사용률 임계치 초과",
      "message": "CPU 사용률이 70%를 초과했습니다 (현재: 75.5%)",
      "detail": {"resource": "cpu", "value": 75.5, "threshold": 70},
      "source": "server_metrics",
      "is_acknowledged": false,
      "acknowledged_by": null,
      "acknowledged_at": null,
      "created_at": "2026-01-15T10:30:00.000000",
      "updated_at": null
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

#### 8.7.3 이벤트 상세 조회

**Endpoint**: `GET /api/system-events/{event_id}`

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "System event retrieved successfully",
  "data": {
    "id": 1,
    "server_id": 1,
    "server_description": "VMS-ab1120",
    "type_event": "threshold_warning",
    "severity": "WARNING",
    "title": "CPU 사용률 임계치 초과",
    "message": "CPU 사용률이 70%를 초과했습니다",
    "detail": {"resource": "cpu", "value": 75.5, "threshold": 70},
    "source": "server_metrics",
    "is_acknowledged": false,
    "acknowledged_by": null,
    "acknowledged_at": null,
    "created_at": "2026-01-15T10:30:00.000000",
    "updated_at": null
  }
}
```

#### 8.7.4 이벤트 생성

**Endpoint**: `POST /api/system-events`

**Request Body**:
```json
{
  "server_id": 1,
  "server_description": "VMS-ab1120",
  "type_event": "custom",
  "severity": "INFO",
  "title": "시스템 점검 완료",
  "message": "정기 시스템 점검이 완료되었습니다.",
  "detail": {"inspector": "admin", "duration_minutes": 30},
  "source": "manual"
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| server_id | integer | N | 서버 ID (전역 이벤트는 NULL) |
| server_description | string | N | 서버 설명 (서버 삭제 후에도 유지) |
| type_event | EnumSystemEventType | Y | 이벤트 유형 |
| severity | EnumSystemEventSeverity | N | 심각도 (기본값: INFO) |
| title | string | Y | 이벤트 제목 (최대 200자) |
| message | string | N | 이벤트 메시지 (최대 1000자) |
| detail | object | N | 추가 상세 정보 (JSONB) |
| source | string | N | 이벤트 발생 소스 (최대 100자) |

**Response (201 Created)**:
```json
{
  "success": true,
  "message": "System event created successfully",
  "data": {
    "id": 2,
    "server_id": 1,
    "server_description": "VMS-ab1120",
    "type_event": "custom",
    "severity": "INFO",
    "title": "시스템 점검 완료",
    "message": "정기 시스템 점검이 완료되었습니다.",
    "detail": {"inspector": "admin", "duration_minutes": 30},
    "source": "manual",
    "is_acknowledged": false,
    "acknowledged_by": null,
    "acknowledged_at": null,
    "created_at": "2026-01-15T11:00:00.000000",
    "updated_at": null
  }
}
```

#### 8.7.5 이벤트 확인 (Acknowledge)

**Endpoint**: `POST /api/system-events/{event_id}/acknowledge`

**Request Body**:
```json
{
  "acknowledged_by": "admin_user"
}
```

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "System event acknowledged successfully",
  "data": {
    "id": 1,
    "is_acknowledged": true,
    "acknowledged_by": "admin_user",
    "acknowledged_at": "2026-01-15T11:30:00.000000"
  }
}
```

#### 8.7.6 이벤트 수정

**Endpoint**: `PATCH /api/system-events/{event_id}`

**Request Body** (부분 업데이트):
```json
{
  "severity": "ERROR",
  "message": "CPU 사용률이 계속 높습니다"
}
```

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "System event updated successfully",
  "data": {
    "id": 1,
    "severity": "ERROR",
    "message": "CPU 사용률이 계속 높습니다",
    "updated_at": "2026-01-15T12:00:00.000000"
  }
}
```

#### 8.7.7 이벤트 삭제

**Endpoint**: `DELETE /api/system-events/{event_id}`

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "System event deleted successfully",
  "data": null
}
```

#### 8.7.8 요약 통계 조회

**Endpoint**: `GET /api/system-events/summary`

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "System event summary retrieved successfully",
  "data": {
    "total_count": 150,
    "unacknowledged_count": 12,
    "by_severity": {
      "INFO": 100,
      "WARNING": 35,
      "ERROR": 10,
      "CRITICAL": 5
    },
    "by_type": {
      "threshold_warning": 25,
      "threshold_critical": 5,
      "server_start": 50,
      "connection_lost": 10
    },
    "recent_critical": [
      {
        "id": 145,
        "title": "디스크 용량 위험",
        "severity": "CRITICAL",
        "created_at": "2026-01-15T09:00:00.000000"
      }
    ]
  }
}
```

---

### 8.8 프록시 설정 API

> **v3.6 신규**: PidsProxy 서버 운용 설정 (operation_mode, windy_mode) 관리

#### 8.8.1 프록시 설정 조회

```http
GET /api/servers/{server_id}/proxy-settings
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| server_id | integer | Y | Server ID |

> **Note**: 설정이 존재하지 않으면 기본값으로 자동 생성합니다 (Lazy 생성).

**Request Example**:
```http
GET /api/servers/1/proxy-settings HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Proxy settings retrieved successfully",
  "data": {
    "id": 1,
    "server_id": 1,
    "operation_mode": "NORMAL",       //(EnumOperationMode)
    "windy_mode": "wind0",            //(EnumWindyMode)
    "created_at": "2026-02-06T12:00:00.000Z",
    "updated_at": "2026-02-06T12:00:00.000Z"
  }
}
```

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "Server with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

---

#### 8.8.2 프록시 설정 수정

```http
PATCH /api/servers/{server_id}/proxy-settings
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| server_id | integer | Y | Server ID |

> **Note**: PATCH는 부분 업데이트이므로 변경할 필드만 포함합니다. 설정이 존재하지 않으면 Upsert (자동 생성 + 요청 필드 적용).

**Request Example**:
```http
PATCH /api/servers/1/proxy-settings HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "operation_mode": "REGISTER",
  "windy_mode": "wind2"
}
```

**Request Body** (부분 업데이트 - 변경할 필드만 포함):

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| operation_mode | string | N | "NORMAL" | 운용 모드 (EnumOperationMode) (현재 값 유지) |
| windy_mode | string | N | "wind0" | 풍량 모드 (EnumWindyMode) (현재 값 유지) |

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Proxy settings updated successfully",
  "data": {
    "id": 1,
    "server_id": 1,
    "operation_mode": "REGISTER",
    "windy_mode": "wind2",
    "created_at": "2026-02-06T12:00:00.000Z",
    "updated_at": "2026-02-06T12:30:00.150Z"
  }
}
```

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "message": "Server with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

---

## 9. Account API 설계

> **v3.0 신규**: 사용자 인증, 계정 관리, 그룹 관리, 세션 관리 API

### 9.1 개요

Account API는 사용자 인증 및 계정 관리 기능을 제공합니다.

| 기능 | 설명 |
|------|------|
| **Auth** | 로그인, 로그아웃, 토큰 갱신, 현재 사용자 정보 |
| **User** | 사용자 CRUD, 잠금/해제, 비밀번호 관리 |
| **UserGroup** | 사용자 그룹 관리, 권한 설정 |
| **UserSession** | 세션 모니터링, 강제 로그아웃 |

### 9.2 Auth API

#### 9.2.1 Endpoint 목록

| Method | Endpoint | 설명 | 섹션 |
|--------|----------|------|------|
| POST | `/api/auth/login` | 로그인 | 9.2.2 |
| POST | `/api/auth/logout` | 로그아웃 | 9.2.3 |
| POST | `/api/auth/refresh` | 토큰 갱신 | 9.2.4 |
| GET | `/api/auth/me` | 현재 사용자 정보 | 9.2.5 |

#### 9.2.2 POST `/api/auth/login`

**Request Body**:
```json
{
  "login_id": "admin", //현재 기본 아이디
  "password": "admin123" //현재 기본 비번
}
```

**Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "login_id": "operator01",
      "name": "홍길동",
      "email": "operator01@gop.mil.kr",
      "department": "경계부대 1중대",
      "role": "OPERATOR",
      "group_id": 1,
      "permissions": {
        "modules": {"events": {"view": true, "edit": true}},
        "device_groups": [1, 2, 3]
      }
    }
  }
}
```

#### 9.2.3 POST `/api/auth/logout`

**Request Header**:
```
Authorization: Bearer {access_token}
```

**Response (200 OK)**:
```json
{
  "success": true
}
```

#### 9.2.4 POST `/api/auth/refresh`

Refresh token을 사용하여 새로운 access token을 발급합니다.

**Request Body**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| refresh_token | string | Y | 리프레시 토큰 |

**Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer"
  }
}
```

**Error Response (401 Unauthorized)**:
```json
{
  "detail": "Invalid refresh token"
}
```

#### 9.2.5 GET `/api/auth/me`

현재 인증된 사용자의 정보를 조회합니다.

**Request Header**:
```
Authorization: Bearer {access_token}
```

**Response (200 OK)**:
```json
{
  "id": 1,
  "login_id": "operator01",
  "name": "홍길동",
  "email": "operator01@gop.mil.kr",
  "department": "경계부대 1중대",
  "position": "상병",
  "employee_number": "21-12345678",
  "phone": "010-1234-5678",
  "role": "OPERATOR",
  "group_id": 1,
  "is_active": true,
  "is_locked": false,
  "lock_reason": null,
  "locked_at": null,
  "last_login_at": "2026-01-19T08:30:00+09:00",
  "last_login_ip": "192.168.1.100",
  "created_at": "2026-01-01T09:00:00+09:00",
  "updated_at": "2026-01-19T08:30:00+09:00"
}
```

### 9.3 User API

#### 9.3.1 Endpoint 목록

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/users` | 사용자 목록 조회 |
| GET | `/api/users/{id}` | 사용자 상세 조회 |
| POST | `/api/users` | 사용자 생성 |
| PUT | `/api/users/{id}` | 사용자 수정 |
| DELETE | `/api/users/{id}` | 사용자 삭제 |
| POST | `/api/users/{id}/lock` | 계정 잠금 |
| POST | `/api/users/{id}/unlock` | 계정 잠금 해제 |
| POST | `/api/users/{id}/reset-password` | 비밀번호 초기화 |
| GET | `/api/users/me` | 내 정보 조회 |
| PUT | `/api/users/me` | 내 정보 수정 |
| PUT | `/api/users/me/password` | 내 비밀번호 변경 |

#### 9.3.2 GET `/api/users`

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| page | int | 아니오 | 페이지 번호 (기본값: 1) |
| limit | int | 아니오 | 페이지당 항목 수 (기본값: 100, 최대: 100) |
| role | string | 아니오 | 역할 필터 (ADMIN, MAINTAINER, OPERATOR, VIEWER, GUEST) |
| group_id | int | 아니오 | 그룹 ID 필터 |
| department | string | 아니오 | 부서 필터 |

**Response (200 OK)**:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "login_id": "operator01",
      "name": "홍길동",
      "email": "operator01@gop.mil.kr",
      "department": "경계부대 1중대",
      "position": "상병",
      "employee_number": "21-12345678",
      "photo_url": null,
      "phone": "010-1234-5678",
      "role": "OPERATOR",
      "group_id": 1,
      "is_active": true,
      "is_locked": false,
      "lock_reason": null,
      "locked_at": null,
      "last_login_at": "2026-01-19T08:30:00+09:00",
      "last_login_ip": "192.168.1.100",
      "created_at": "2026-01-01T09:00:00+09:00",
      "updated_at": "2026-01-19T08:30:00+09:00"
    }
  ]
}
```

#### 9.3.3 POST `/api/users`

**Request Body**:
```json
{
  "login_id": "operator01",
  "password": "SecureP@ss123!",
  "name": "홍길동",
  "email": "operator01@gop.mil.kr",
  "department": "경계부대 1중대",
  "position": "상병",
  "employee_number": "21-12345678",
  "photo_url": null,
  "phone": "010-1234-5678",
  "role": "OPERATOR",
  "group_id": 1
}
```

**Response (201 Created)**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "login_id": "operator01",
    "name": "홍길동",
    "email": "operator01@gop.mil.kr",
    "department": "경계부대 1중대",
    "position": "상병",
    "employee_number": "21-12345678",
    "photo_url": null,
    "phone": "010-1234-5678",
    "role": "OPERATOR",
    "group_id": 1,
    "is_active": true,
    "is_locked": false,
    "lock_reason": null,
    "locked_at": null,
    "last_login_at": null,
    "last_login_ip": null,
    "created_at": "2026-01-23T09:00:00+09:00",
    "updated_at": "2026-01-23T09:00:00+09:00"
  }
}
```

### 9.4 UserGroup API

#### 9.4.1 Endpoint 목록

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/user-groups` | 그룹 목록 조회 |
| GET | `/api/user-groups/{id}` | 그룹 상세 조회 |
| POST | `/api/user-groups` | 그룹 생성 |
| PUT | `/api/user-groups/{id}` | 그룹 수정 |
| DELETE | `/api/user-groups/{id}` | 그룹 삭제 |
| GET | `/api/user-groups/{id}/users` | 그룹 소속 사용자 목록 |

#### 9.4.2 POST `/api/user-groups`

**Request Body**:
```json
{
  "name": "1중대 운영팀",
  "description": "1중대 경계 시스템 운영 담당",
  "permissions": {
    "modules": {
      "events": {"view": true, "edit": true, "delete": false},
      "cameras": {"view": true, "edit": false, "control": true}
    },
    "device_groups": [1, 2, 3]
  },
  "is_active": true
}
```

**Response (201 Created)**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "1중대 운영팀",
    "is_active": true
  }
}
```

### 9.5 UserSession API

#### 9.5.1 Endpoint 목록

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/user-sessions` | 활성 세션 목록 |
| GET | `/api/user-sessions/{id}` | 세션 상세 조회 |
| DELETE | `/api/user-sessions/{id}` | 강제 로그아웃 |
| DELETE | `/api/user-sessions/user/{user_id}` | 특정 사용자 전체 세션 종료 |
| GET | `/api/user-sessions/me` | 내 세션 목록 |
| DELETE | `/api/user-sessions/me/{id}` | 내 다른 세션 종료 |

#### 9.5.2 GET `/api/user-sessions`

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| page | int | 아니오 | 페이지 번호 (기본값: 1) |
| limit | int | 아니오 | 페이지당 항목 수 (기본값: 100, 최대: 100) |
| is_active | boolean | 아니오 | 활성 상태 필터 |

**Response (200 OK)**:
```json
{
  "success": true,
  "data": [
    {
      "id": 101,
      "user_id": 1,
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0",
      "expires_at": "2026-01-19T20:30:00+09:00",
      "is_active": true,
      "logout_reason": null,
      "forced_by": null,
      "logged_out_at": null,
      "created_at": "2026-01-19T08:30:00+09:00",
      "updated_at": "2026-01-19T10:15:00+09:00"
    }
  ]
}
```

> **필드 설명**:
> - `created_at`: 세션 생성(로그인) 시간
> - `updated_at`: 마지막 활동 시간
> - `forced_by`: 강제 로그아웃 처리자 User ID (강제 로그아웃 시)

#### 9.5.3 GET `/api/user-sessions/{id}`

**Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "id": 101,
    "user_id": 1,
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0",
    "expires_at": "2026-01-19T20:30:00+09:00",
    "is_active": true,
    "logout_reason": null,
    "forced_by": null,
    "logged_out_at": null,
    "created_at": "2026-01-19T08:30:00+09:00",
    "updated_at": "2026-01-19T10:15:00+09:00"
  }
}
```

#### 9.5.4 DELETE `/api/user-sessions/{id}`

강제 로그아웃 처리. SystemEvent가 생성됩니다.

**Response (200 OK)**:
```json
{
  "success": true
}
```

### 9.6 Audit Logs API

> **v3.1 신규**: PRD_Audit_Log.md 참조
> 사용자 활동 감사 로그 조회 API. 읽기 전용으로 생성/수정/삭제 API는 제공하지 않습니다.

#### 9.6.1 Endpoint 목록

| Method | Endpoint | 설명 | 권한 |
|--------|----------|------|------|
| GET | `/api/audit-logs` | 감사 로그 목록 조회 | ADMIN, MAINTAINER |
| GET | `/api/audit-logs/{id}` | 감사 로그 상세 조회 | ADMIN, MAINTAINER |

> **참고**: 감사 로그는 보안 목적으로 **생성/수정/삭제 API를 제공하지 않음**. 시스템 내부에서만 자동 생성됩니다.

#### 9.6.2 GET `/api/audit-logs`

**Query Parameters**:

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| page | int | 아니오 | 페이지 번호 (기본값: 1) |
| limit | int | 아니오 | 페이지당 항목 수 (기본값: 20, 최대: 100) |
| action_type | string | 아니오 | 행위 유형 필터 (EnumAuditActionType) |
| resource_type | string | 아니오 | 리소스 유형 필터 (EnumAuditResourceType) |
| resource_id | int | 아니오 | 리소스 ID 필터 |
| actor_login_id | string | 아니오 | 행위자 로그인 ID 필터 |
| action_status | string | 아니오 | 결과 상태 필터 (SUCCESS, FAILURE) |
| start_date | datetime | 아니오 | 시작 일시 |
| end_date | datetime | 아니오 | 종료 일시 |

**Request Example**:
```http
GET /api/audit-logs?action_type=USER_CREATED&limit=20 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "data": [
    {
      "id": 100,
      "action_type": "USER_CREATED",
      "action_status": "SUCCESS",
      "resource_type": "USER",
      "resource_id": 5,
      "resource_name": "홍길동 (operator01)",
      "actor_id": 1,
      "actor_login_id": "admin",
      "actor_name": "관리자",
      "actor_role": "ADMIN",
      "changes": {
        "after": {
          "login_id": "operator01",
          "name": "홍길동",
          "role": "OPERATOR"
        }
      },
      "description": "사용자 생성: operator01",
      "ip_address": "192.168.1.100",
      "user_agent": null,
      "error_message": null,
      "created_at": "2026-01-19T10:30:00+09:00"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 1250,
    "total_pages": 63
  }
}
```

#### 9.6.3 GET `/api/audit-logs/{id}`

**Path Parameters**:

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| id | int | 예 | 감사 로그 ID |

**Response Example** (200 OK):
```json
{
  "success": true,
  "data": {
    "id": 100,
    "action_type": "ROLE_CHANGED",
    "action_status": "SUCCESS",
    "resource_type": "USER",
    "resource_id": 5,
    "resource_name": "홍길동 (operator01)",
    "actor_id": 1,
    "actor_login_id": "admin",
    "actor_name": "관리자",
    "actor_role": "ADMIN",
    "changes": {
      "before": {"role": "VIEWER"},
      "after": {"role": "OPERATOR"}
    },
    "description": "역할 변경: VIEWER → OPERATOR",
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "error_message": null,
    "created_at": "2026-01-19T10:30:00+09:00"
  }
}
```

**Response (404 Not Found)**:
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Audit log not found"
  }
}
```

#### 9.6.4 자동 감사 로그 생성

다음 API 호출 시 감사 로그가 자동 생성됩니다:

| API Endpoint | Action Type | Resource Type | 변경 내역 기록 |
|--------------|-------------|---------------|----------------|
| POST `/api/users` | USER_CREATED | USER | after만 기록 |
| PATCH `/api/users/{id}` | USER_UPDATED | USER | before/after 기록 |
| PUT `/api/users/{id}` | USER_UPDATED | USER | before/after 기록 |
| DELETE `/api/users/{id}` | USER_DELETED | USER | before만 기록 |
| POST `/api/users/{id}/lock` | USER_LOCKED | USER | reason 기록 |
| POST `/api/users/{id}/unlock` | USER_UNLOCKED | USER | - |
| PUT `/api/users/me/password` | PASSWORD_CHANGED | PASSWORD | - (비밀번호 미기록) |
| POST `/api/users/{id}/reset-password` | PASSWORD_RESET | PASSWORD | - (비밀번호 미기록) |
| POST `/api/user-groups` | GROUP_CREATED | USER_GROUP | after만 기록 |
| PUT `/api/user-groups/{id}` | GROUP_UPDATED | USER_GROUP | before/after 기록 |
| DELETE `/api/user-groups/{id}` | GROUP_DELETED | USER_GROUP | before만 기록 |
| DELETE `/api/user-sessions/{id}` | SESSION_FORCED_LOGOUT | USER_SESSION | reason 기록 |

> **민감 정보 제외**: `password`, `password_hash`, `hashed_password`, `token`, `refresh_token`, `user_password` 등 민감 정보는 `changes`에 기록하지 않습니다. (PRD_Audit_Log.md Section 5.2)

### 9.7 Config Change Logs API

> **v3.2 신규**: PRD_ConfigChangeLog.md v1.1 참조
> 설정 변경 이력 조회 API. 읽기 전용으로 생성/수정/삭제 API는 제공하지 않습니다.
>
> **JSONB 정규화 (v1.1)**: `before_state`/`after_state`는 변경된 필드만 저장합니다.
> - CREATED: `after_state`에 `{id, name}` 식별 정보만
> - UPDATED: 변경된 필드만 `before_state`/`after_state`에
> - DELETED: `before_state`에 `{id, name}` 식별 정보만

#### 9.7.1 Endpoint 목록

| Method | Endpoint | 설명 | 권한 |
|--------|----------|------|------|
| GET | `/api/config-change-logs` | 설정 변경 로그 목록 조회 | ADMIN, MAINTAINER |
| GET | `/api/config-change-logs/{id}` | 설정 변경 로그 상세 조회 | ADMIN, MAINTAINER |

> **참고**: 설정 변경 로그는 **생성/수정/삭제 API를 제공하지 않음**. 시스템 내부에서만 자동 생성됩니다.

#### 9.7.2 설정 변경 로그 목록 조회

**Endpoint**: `GET /api/config-change-logs`

**Query Parameters**:
- `page` (int, optional): 페이지 번호 (기본값: 1)
- `limit` (int, optional): 페이지당 항목 수 (기본값: 20, 최대: 100)
- `resource_type` (string, optional): 리소스 유형 필터 (EnumConfigResourceType)
- `resource_id` (int, optional): 리소스 ID 필터
- `action` (string, optional): 액션 유형 필터 (EnumConfigActionType)
- `actor_id` (int, optional): 수행자 ID 필터
- `start_date` (datetime, optional): 시작 일시
- `end_date` (datetime, optional): 종료 일시

**Request Example**:
```http
GET /api/config-change-logs?resource_type=CAMERA&action=CREATED&limit=20 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "3 config change logs retrieved",
  "data": [
    {
      "id": 150,
      "resource_type": "CAMERA",
      "resource_id": 201,
      "resource_name": "Camera-201 (정문 CCTV)",
      "action": "CREATED",
      "before_state": null,
      "after_state": {
        "id": 201,
        "name": "정문 CCTV"
      },
      "actor_id": 1,
      "actor_name": "관리자",
      "actor_ip": "192.168.1.100",
      "description": "Camera 생성: Camera-201 (정문 CCTV)",
      "created_at": "2026-01-21T10:30:00+09:00"
    },
    {
      "id": 149,
      "resource_type": "CAMERA",
      "resource_id": 201,
      "resource_name": "Camera-201 (정문 CCTV)",
      "action": "UPDATED",
      "before_state": {
        "name": "정문 카메라"
      },
      "after_state": {
        "name": "정문 CCTV"
      },
      "actor_id": 1,
      "actor_name": "관리자",
      "actor_ip": "192.168.1.100",
      "description": "Camera 수정: Camera-201",
      "created_at": "2026-01-21T09:15:00+09:00"
    },
    {
      "id": 148,
      "resource_type": "CAMERA",
      "resource_id": 200,
      "resource_name": "Camera-200 (후문 CCTV)",
      "action": "DELETED",
      "before_state": {
        "id": 200,
        "name": "후문 CCTV"
      },
      "after_state": null,
      "actor_id": 2,
      "actor_name": "유지보수담당자",
      "actor_ip": "192.168.1.105",
      "description": "Camera 삭제: Camera-200 (후문 CCTV)",
      "created_at": "2026-01-21T08:00:00+09:00"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 850,
    "total_pages": 43
  },
  "meta": {
    "timestamp": "2026-01-21T10:30:00.150Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

#### 9.7.3 설정 변경 로그 단일 조회

**Endpoint**: `GET /api/config-change-logs/{id}`

**Path Parameters**:
- `id` (int, required): 설정 변경 로그 ID

**Request Example**:
```http
GET /api/config-change-logs/150 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Config change log retrieved successfully",
  "data": {
    "id": 150,
    "resource_type": "SENSOR",
    "resource_id": 105,
    "resource_name": "Sensor-105 (북측 펜스)",
    "action": "UPDATED",
    "before_state": {
      "status": "DEACTIVATED",
      "description": "북측 펜스 센서"
    },
    "after_state": {
      "status": "ACTIVATED",
      "description": "북측 펜스 센서 (점검완료)"
    },
    "actor_id": 2,
    "actor_name": "유지보수담당자",
    "actor_ip": "192.168.1.105",
    "description": "Sensor 상태 변경: DEACTIVATED → ACTIVATED",
    "created_at": "2026-01-21T11:45:00+09:00"
  },
  "meta": {
    "timestamp": "2026-01-21T11:45:00.050Z",
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
    "message": "Config change log not found with Id=999",
    "details": "No config change log exists with the specified ID"
  },
  "meta": {
    "timestamp": "2026-01-21T11:45:00.050Z",
    "request_id": "550e8401-e29b-41d4-a716-446655440000"
  }
}
```

#### 9.7.4 자동 설정 변경 로그 생성

다음 리소스의 CRUD 작업 시 설정 변경 로그가 자동 생성됩니다:

| Resource Type | 대상 API | 기록 내용 |
|---------------|----------|-----------|
| **Device 계열** | | |
| CONTROLLER | `/api/controllers` | 제어기 생성/수정/삭제 |
| SENSOR | `/api/sensors` | 센서 생성/수정/삭제 |
| CAMERA | `/api/cameras` | 카메라 생성/수정/삭제 |
| SPEAKER | `/api/speakers` | 스피커 생성/수정/삭제 |
| ENCLOSURE | `/api/enclosures` | 함체 생성/수정/삭제 |
| DEVICE_GROUP | `/api/device-groups` | 장비 그룹 생성/수정/삭제 |
| DEVICE_GROUP_MAPPING | `/api/device-groups/{id}/devices` | 장비 그룹 할당/해제 |
| CAMERA_PRESET | `/api/camera-presets` | 카메라 프리셋 생성/수정/삭제 |
| ROI | `/api/rois` | ROI 생성/수정/삭제 |
| **Server 계열** | | |
| SERVER | `/api/servers` | 서버 생성/수정/삭제 |
| SERVER_CATEGORY | `/api/server-categories` | 서버 카테고리 생성/수정/삭제 |
| **Integration 계열** | | |
| EVENT_MAPPING | `/api/event-mappings` | 이벤트 매핑 생성/수정/삭제 |
| EVENT_MAPPING_CAMERA | `/api/event-mappings/{id}/cameras` | 매핑 카메라 생성/수정/삭제 |
| EVENT_MAPPING_SPEAKER | `/api/event-mappings/{id}/speakers` | 매핑 스피커 생성/수정/삭제 |

> **상태 변경 (STATUS_CHANGED)**: 리소스의 `status` 필드가 변경될 때 자동으로 `STATUS_CHANGED` 액션으로 기록됩니다.

---

## 10. Report API 설계 (v3.3 신규)

> **PRD 참조**: PRD_Report_System.md
> 보고서 템플릿 관리, 보고서 생성 및 다운로드 API

### 10.1 개요

Report API는 정형/비정형 보고서의 생성 및 관리 기능을 제공합니다.

| 기능 | 설명 |
|------|------|
| **Components** | 보고서 컴포넌트 목록 조회 (15종) |
| **Templates** | 비정형 보고서 템플릿 CRUD |
| **Generations** | 보고서 생성 요청 및 이력 관리 |
| **Preview** | 보고서 미리보기 (Chart.js 기반 HTML) |

### 10.2 Report Components API

#### 10.2.1 Endpoint 목록

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/reports/components` | 컴포넌트 목록 조회 |

#### 10.2.2 GET `/api/reports/components`

사용 가능한 보고서 컴포넌트 목록을 카테고리별로 조회합니다.

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Report components retrieved successfully",
  "data": [
    {
      "category": "SUMMARY",
      "components": [
        {"id": "SUMMARY_CARD", "name": "요약 카드", "description": "전체 현황 요약"}
      ]
    },
    {
      "category": "DEVICE",
      "components": [
        {"id": "DEVICE_STATUS_PIE", "name": "장비 상태 파이", "description": "장비 상태별 분포"},
        {"id": "DEVICE_TYPE_BAR", "name": "장비 유형 바", "description": "장비 유형별 현황"},
        {"id": "DEVICE_GRID", "name": "장비 그리드", "description": "장비 목록 테이블"}
      ]
    },
    {
      "category": "EVENT",
      "components": [
        {"id": "EVENT_SUMMARY_PIE", "name": "이벤트 요약 파이", "description": "이벤트 유형별 분포"},
        {"id": "EVENT_TREND_LINE", "name": "이벤트 추이 라인", "description": "이벤트 발생 추이"},
        {"id": "EVENT_DAILY_BAR", "name": "일별 이벤트 바", "description": "일별 이벤트 현황"},
        {"id": "EVENT_DETECTION_GRID", "name": "탐지 이벤트 그리드", "description": "탐지 이벤트 목록"},
        {"id": "EVENT_MALFUNCTION_GRID", "name": "장애 이벤트 그리드", "description": "장애 이벤트 목록"},
        {"id": "EVENT_ACTION_GRID", "name": "조치 이벤트 그리드", "description": "조치 이벤트 목록"}
      ]
    },
    {
      "category": "SYSTEM",
      "components": [
        {"id": "SYSTEM_SEVERITY_BAR", "name": "심각도 바", "description": "심각도별 분포"},
        {"id": "SYSTEM_TREND_LINE", "name": "시스템 추이 라인", "description": "시스템 현황 추이"},
        {"id": "SYSTEM_CONFIG_GRID", "name": "설정 그리드", "description": "시스템 설정 목록"},
        {"id": "SYSTEM_EVENT_GRID", "name": "시스템 이벤트 그리드", "description": "시스템 이벤트 목록"},
        {"id": "SYSTEM_AUDIT_GRID", "name": "감사 로그 그리드", "description": "감사 로그 목록"}
      ]
    },
    {
      "category": "USER",
      "components": [
        {"id": "USER_ROLE_PIE", "name": "역할별 사용자 분포", "description": "역할별 사용자 현황"},
        {"id": "USER_LOGIN_TREND_LINE", "name": "일별 로그인 추이", "description": "일별 로그인 시도 추이"},
        {"id": "USER_LOGIN_RESULT_PIE", "name": "로그인 결과 분포", "description": "로그인 성공/실패 분포"},
        {"id": "USER_GRID", "name": "사용자 그리드", "description": "사용자 상세 목록"},
        {"id": "USER_LOGIN_GRID", "name": "로그인 이력 그리드", "description": "로그인 시도 이력"},
        {"id": "USER_SESSION_GRID", "name": "세션 그리드", "description": "사용자 세션 목록"}
      ]
    }
  ]
}
```

### 10.3 Report Templates API

> 비정형 보고서 템플릿 관리 (사용자 정의 컴포넌트 조합)

#### 10.3.1 Endpoint 목록

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/reports/templates` | 템플릿 목록 조회 |
| POST | `/api/reports/templates` | 템플릿 생성 |
| GET | `/api/reports/templates/{id}` | 템플릿 상세 조회 |
| PATCH | `/api/reports/templates/{id}` | 템플릿 수정 |
| DELETE | `/api/reports/templates/{id}` | 템플릿 삭제 |

#### 10.3.2 GET `/api/reports/templates`

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| page | int | 아니오 | 페이지 번호 (기본값: 1) |
| limit | int | 아니오 | 페이지당 항목 수 (기본값: 20, 최대: 100) |

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Report templates retrieved successfully",
  "data": [
    {
      "id": 1,
      "name": "주간 이벤트 보고서",
      "description": "주간 탐지/장애 이벤트 종합 보고서",
      "report_type": "CUSTOM",
      "owner_id": 1,
      "is_public": true,
      "components": [
        {"id": "SUMMARY_CARD", "order": 1, "enabled": true, "title": "전체 현황"},
        {"id": "EVENT_SUMMARY_PIE", "order": 2, "enabled": true, "title": null},
        {"id": "EVENT_TREND_LINE", "order": 3, "enabled": true, "title": null}
      ],
      "default_period": "7d",
      "created_at": "2026-01-20T10:00:00+09:00",
      "updated_at": "2026-01-20T10:00:00+09:00"
    }
  ]
}
```

#### 10.3.3 GET `/api/reports/templates/{id}`

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| id | int | 예 | 템플릿 ID |

**Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "주간 이벤트 보고서",
    "description": "주간 탐지/장애 이벤트 종합 보고서",
    "report_type": "CUSTOM",
    "owner_id": 1,
    "is_public": true,
    "components": [
      {"id": "SUMMARY_CARD", "order": 1, "enabled": true, "title": "전체 현황"},
      {"id": "EVENT_SUMMARY_PIE", "order": 2, "enabled": true, "title": null},
      {"id": "EVENT_TREND_LINE", "order": 3, "enabled": true, "title": null}
    ],
    "default_period": "7d",
    "created_at": "2026-01-20T10:00:00+09:00",
    "updated_at": "2026-01-20T10:00:00+09:00"
  }
}
```

**Response (404 Not Found)**:
```json
{
  "detail": "Report template not found"
}
```

#### 10.3.4 POST `/api/reports/templates`

**Request Body**:
```json
{
  "name": "주간 이벤트 보고서",
  "description": "주간 탐지/장애 이벤트 종합 보고서",
  "report_type": "CUSTOM",
  "is_public": true,
  "components": [
    {"id": "SUMMARY_CARD", "order": 1, "enabled": true, "title": "전체 현황"},
    {"id": "EVENT_SUMMARY_PIE", "order": 2, "enabled": true},
    {"id": "EVENT_TREND_LINE", "order": 3, "enabled": true}
  ],
  "default_period": "7d"
}
```

**필드 설명**:
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| name | string | 예 | 템플릿 이름 (1~100자) |
| description | string | 아니오 | 템플릿 설명 (최대 500자) |
| report_type | string | 아니오 | 보고서 유형 (기본값: CUSTOM) |
| is_public | boolean | 아니오 | 공개 여부 (기본값: false) |
| components | array | 예 | 컴포넌트 설정 목록 |
| default_period | string | 아니오 | 기본 기간 (기본값: 7d) |

**Component 필드 설명**:
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| id | string | 예 | EnumReportComponent 값 |
| order | int | 예 | 출력 순서 |
| enabled | boolean | 예 | 활성화 여부 |
| title | string | 아니오 | 커스텀 제목 |

**Response (201 Created)**:
```json
{
  "success": true,
  "message": "Report template created successfully",
  "data": {
    "id": 1,
    "name": "주간 이벤트 보고서",
    "report_type": "CUSTOM",
    "created_at": "2026-01-20T10:00:00+09:00"
  }
}
```

#### 10.3.5 PATCH `/api/reports/templates/{id}`

**Request Body** (변경할 필드만 포함):
```json
{
  "name": "월간 이벤트 보고서",
  "default_period": "30d"
}
```

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Report template updated successfully",
  "data": {
    "id": 1,
    "name": "월간 이벤트 보고서",
    "default_period": "30d",
    "updated_at": "2026-01-21T10:00:00+09:00"
  }
}
```

#### 10.3.6 DELETE `/api/reports/templates/{id}`

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Report template deleted successfully",
  "data": {"id": 1}
}
```

### 10.4 Report Generations API

> 보고서 생성 요청 및 이력 관리

#### 10.4.1 Endpoint 목록

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/reports/generate` | 보고서 생성 요청 |
| GET | `/api/reports/generations` | 생성 이력 목록 조회 |
| GET | `/api/reports/generations/{id}` | 생성 이력 상세 조회 |
| GET | `/api/reports/generations/{id}/download` | PDF 다운로드 |
| GET | `/api/reports/generations/{id}/preview` | 미리보기 데이터 |

#### 10.4.2 POST `/api/reports/generate`

보고서 생성을 요청합니다. 생성 작업은 BackgroundTasks로 비동기 실행됩니다.

**Request Body**:
```json
{
  "report_type": "STANDARD",
  "title": "2026년 1월 3주차 주간 보고서",
  "period_type": "7d",
  "template_id": null,
  "severity_filter": null
}
```

**필드 설명**:
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| report_type | string | 예 | 보고서 유형 (STANDARD, CUSTOM) |
| title | string | 예 | 보고서 제목 |
| period_type | string | 예 | 기간 유형 (7d, 30d, 90d, 1y) |
| template_id | int | 아니오 | CUSTOM 보고서 시 템플릿 ID |
| severity_filter | array | 아니오 | 심각도 필터 |

**Response (202 Accepted)**:
```json
{
  "success": true,
  "message": "Report generation requested successfully",
  "data": {
    "id": 1,
    "report_type": "STANDARD",
    "title": "2026년 1월 3주차 주간 보고서",
    "period_type": "7d",
    "start_date": "2026-01-16T00:00:00+09:00",
    "end_date": "2026-01-23T00:00:00+09:00",
    "status": "PENDING",
    "created_at": "2026-01-23T10:00:00+09:00"
  }
}
```

> **Note**: HTTP 202 Accepted - 비동기 작업 요청 수락

#### 10.4.3 GET `/api/reports/generations`

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| page | int | 아니오 | 페이지 번호 (기본값: 1) |
| limit | int | 아니오 | 페이지당 항목 수 (기본값: 20, 최대: 100) |
| status | string | 아니오 | 상태 필터 (PENDING, GENERATING, COMPLETED, FAILED) |

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Report generations retrieved successfully",
  "data": [
    {
      "id": 1,
      "report_type": "STANDARD",
      "template_id": null,
      "title": "2026년 1월 3주차 주간 보고서",
      "period_type": "7d",
      "start_date": "2026-01-16T00:00:00+09:00",
      "end_date": "2026-01-23T00:00:00+09:00",
      "generator_id": 1,
      "generator_name": "관리자",
      "status": "COMPLETED",
      "created_at": "2026-01-23T10:00:00+09:00",
      "completed_at": "2026-01-23T10:01:30+09:00",
      "pdf_download_url": "/api/reports/generations/1/download"
    }
  ]
}
```

#### 10.4.4 GET `/api/reports/generations/{id}/download`

PDF 파일 다운로드를 요청합니다.

**Response (200 OK)** (COMPLETED 상태):
```json
{
  "success": true,
  "message": "Report download initiated",
  "data": {
    "id": 1,
    "pdf_file_path": "/reports/2026/01/report_1_20260123.pdf"
  }
}
```

**Response (400 Bad Request)** (COMPLETED 아닌 상태):
```json
{
  "success": false,
  "error": {
    "code": "BAD_REQUEST",
    "message": "Report is not COMPLETED yet"
  }
}
```

#### 10.4.5 GET `/api/reports/generations/{id}/preview`

보고서 미리보기 데이터를 조회합니다.

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Report preview retrieved successfully",
  "data": {
    "id": 1,
    "title": "2026년 1월 3주차 주간 보고서",
    "report_type": "STANDARD",
    "period_type": "7d",
    "start_date": "2026-01-16T00:00:00+09:00",
    "end_date": "2026-01-23T00:00:00+09:00",
    "summary_data": {
      "device_count": 150,
      "event_count": 245,
      "detection_count": 180,
      "malfunction_count": 45,
      "action_count": 20
    },
    "created_at": "2026-01-23T10:00:00+09:00",
    "completed_at": "2026-01-23T10:01:30+09:00"
  }
}
```

### 10.5 Report Preview Page

> 개발용 HTML 미리보기 페이지 (Swagger 미포함, Chart.js 기반)

#### 10.5.1 Endpoint

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/reports/preview/{generation_id}` | HTML 미리보기 페이지 |

#### 10.5.2 GET `/reports/preview/{generation_id}`

Chart.js 기반 HTML 미리보기 페이지를 렌더링합니다.

**Response**: HTML 페이지 (`text/html`)

**특징**:
- Jinja2 템플릿 기반 (`app/templates/reports/preview.html`)
- Chart.js CDN 연동 (Pie, Bar, Line 차트)
- 섹션별 차트 및 그리드 테이블 표시
- PDF 다운로드 버튼 포함 (COMPLETED 상태 시)

---

## 11. 에러 처리

### 11.1 에러 응답 형식

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

### 11.2 에러 코드 정의

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

### 11.3 에러 응답 예제

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

## 12. 부록

### 12.1 전체 Endpoint 목록

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

**Speakers** (v2.4 신규):
- `GET /api/devices/speakers` - 스피커 목록 조회
- `POST /api/devices/speakers` - 스피커 생성
- `GET /api/devices/speakers/{id}` - 스피커 단일 조회
- `PATCH /api/devices/speakers/{id}` - 스피커 수정 (부분)
- `PUT /api/devices/speakers/{id}` - 스피커 수정 (전체)
- `DELETE /api/devices/speakers/{id}` - 스피커 삭제

**FileGroups** (v2.4 신규):
- `GET /api/file-groups` - 파일그룹 목록 조회
- `POST /api/file-groups` - 파일그룹 생성
- `GET /api/file-groups/{id}` - 파일그룹 단일 조회
- `PATCH /api/file-groups/{id}` - 파일그룹 수정 (부분)
- `PUT /api/file-groups/{id}` - 파일그룹 수정 (전체)
- `DELETE /api/file-groups/{id}` - 파일그룹 삭제

**Enclosures** (v2.4 신규):
- `GET /api/devices/enclosures` - 함체 목록 조회
- `POST /api/devices/enclosures` - 함체 생성
- `GET /api/devices/enclosures/{id}` - 함체 단일 조회
- `PATCH /api/devices/enclosures/{id}` - 함체 수정 (부분)
- `PUT /api/devices/enclosures/{id}` - 함체 수정 (전체)
- `DELETE /api/devices/enclosures/{id}` - 함체 삭제
- `PATCH /api/devices/enclosures/{id}/status` - 함체 환경 데이터 업데이트
- `POST /api/devices/enclosures/{id}/control` - 함체 제어 (히터/팬)

**Enclosure Metrics** (v2.9 신규):
- `POST /api/devices/enclosures/{enclosure_id}/metrics` - 메트릭 저장
- `GET /api/devices/enclosures/{enclosure_id}/metrics` - 메트릭 목록 조회
- `GET /api/devices/enclosures/{enclosure_id}/metrics/latest` - 최신 메트릭 조회
- `DELETE /api/devices/enclosures/{enclosure_id}/metrics` - 메트릭 삭제

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

**Event Mapping Cameras** (v2.4 신규):
- `GET /api/integrations/event-mappings/{mapping_id}/cameras` - 카메라 연동 목록 조회
- `POST /api/integrations/event-mappings/{mapping_id}/cameras` - 카메라 연동 생성
- `GET /api/integrations/event-mappings/{mapping_id}/cameras/{config_id}` - 카메라 연동 단일 조회
- `PATCH /api/integrations/event-mappings/{mapping_id}/cameras/{config_id}` - 카메라 연동 수정 (부분)
- `PUT /api/integrations/event-mappings/{mapping_id}/cameras/{config_id}` - 카메라 연동 수정 (전체)
- `DELETE /api/integrations/event-mappings/{mapping_id}/cameras/{config_id}` - 카메라 연동 삭제

**Event Mapping Speakers** (v2.8 신규):
- `GET /api/integrations/event-mappings/{mapping_id}/speakers` - 스피커 연동 목록 조회
- `POST /api/integrations/event-mappings/{mapping_id}/speakers` - 스피커 연동 생성
- `GET /api/integrations/event-mappings/{mapping_id}/speakers/{config_id}` - 스피커 연동 단일 조회
- `PATCH /api/integrations/event-mappings/{mapping_id}/speakers/{config_id}` - 스피커 연동 수정 (부분)
- `PUT /api/integrations/event-mappings/{mapping_id}/speakers/{config_id}` - 스피커 연동 수정 (전체)
- `DELETE /api/integrations/event-mappings/{mapping_id}/speakers/{config_id}` - 스피커 연동 삭제

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

**Server Metrics** (v2.9 신규):
- `POST /api/servers/{server_id}/metrics` - 메트릭 기록
- `GET /api/servers/{server_id}/metrics` - 메트릭 이력 조회
- `GET /api/servers/{server_id}/metrics/latest` - 최신 메트릭 조회
- `DELETE /api/servers/{server_id}/metrics` - 메트릭 삭제

**System Events** (v2.9 신규):
- `GET /api/system-events` - 이벤트 목록 조회
- `POST /api/system-events` - 이벤트 생성
- `GET /api/system-events/{id}` - 이벤트 상세 조회
- `PATCH /api/system-events/{id}` - 이벤트 수정
- `DELETE /api/system-events/{id}` - 이벤트 삭제
- `POST /api/system-events/{id}/acknowledge` - 이벤트 확인
- `GET /api/system-events/summary` - 요약 통계 조회

#### Account Endpoints (v3.0 신규)

**Auth**:
- `POST /api/auth/login` - 로그인
- `POST /api/auth/logout` - 로그아웃
- `POST /api/auth/refresh` - 토큰 갱신
- `GET /api/auth/me` - 현재 사용자 정보

**Users**:
- `GET /api/users` - 사용자 목록 조회
- `POST /api/users` - 사용자 생성
- `GET /api/users/{id}` - 사용자 상세 조회
- `PUT /api/users/{id}` - 사용자 수정
- `DELETE /api/users/{id}` - 사용자 삭제
- `POST /api/users/{id}/lock` - 계정 잠금
- `POST /api/users/{id}/unlock` - 계정 잠금 해제
- `POST /api/users/{id}/reset-password` - 비밀번호 초기화
- `GET /api/users/me` - 내 정보 조회
- `PUT /api/users/me` - 내 정보 수정
- `PUT /api/users/me/password` - 내 비밀번호 변경

**UserGroups**:
- `GET /api/user-groups` - 그룹 목록 조회
- `POST /api/user-groups` - 그룹 생성
- `GET /api/user-groups/{id}` - 그룹 상세 조회
- `PUT /api/user-groups/{id}` - 그룹 수정
- `DELETE /api/user-groups/{id}` - 그룹 삭제
- `GET /api/user-groups/{id}/users` - 그룹 소속 사용자 목록

**UserSessions**:
- `GET /api/user-sessions` - 활성 세션 목록
- `GET /api/user-sessions/{id}` - 세션 상세 조회
- `DELETE /api/user-sessions/{id}` - 강제 로그아웃
- `DELETE /api/user-sessions/user/{user_id}` - 특정 사용자 전체 세션 종료
- `GET /api/user-sessions/me` - 내 세션 목록
- `DELETE /api/user-sessions/me/{id}` - 내 다른 세션 종료

**Audit Logs (v3.1 신규)**:
- `GET /api/audit-logs` - 감사 로그 목록 조회
- `GET /api/audit-logs/{id}` - 감사 로그 상세 조회

**Config Change Logs (v3.2 신규)**:
- `GET /api/config-change-logs` - 설정 변경 로그 목록 조회
- `GET /api/config-change-logs/{id}` - 설정 변경 로그 상세 조회

#### Report Endpoints (v3.3 신규)

**Report Components**:
- `GET /api/reports/components` - 컴포넌트 목록 조회

**Report Templates**:
- `GET /api/reports/templates` - 템플릿 목록 조회
- `POST /api/reports/templates` - 템플릿 생성
- `GET /api/reports/templates/{id}` - 템플릿 상세 조회
- `PATCH /api/reports/templates/{id}` - 템플릿 수정
- `DELETE /api/reports/templates/{id}` - 템플릿 삭제

**Report Generations**:
- `POST /api/reports/generate` - 보고서 생성 요청
- `GET /api/reports/generations` - 생성 이력 목록 조회
- `GET /api/reports/generations/{id}` - 생성 이력 상세 조회
- `GET /api/reports/generations/{id}/download` - PDF 다운로드
- `GET /api/reports/generations/{id}/preview` - 미리보기 데이터

**Report Preview (Non-API)**:
- `GET /reports/preview/{generation_id}` - HTML 미리보기 페이지

### 12.2 Event-Device 리팩토링 변경사항 (v2.3)

#### 12.2.1 API Request 변경

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
  "detail": {
    "result": "PIR_SENSOR" //(EnumDetectionType)
  }
}
```

#### 12.2.2 API Response 변경

| 필드 | v2.2 | v2.3 | 설명 |
|------|------|------|------|
| `device` | ✅ | ✅ | Device nested 객체. Device 삭제 시 `null` |
| `device_description` | ✅ | ✅ | Device 정보 스냅샷. Device 삭제 후에도 유지 |
| `device_id` | ✅ | ❌ **제거** | `device.id`에 포함되어 중복 |
| `sequence` | ✅ | ❌ **제거** | Request 전용 필드, Response에 불필요 |
| `group_event` | ✅ | ❌ **제거** | DeviceGroup은 `device.device_groups[]`로 조회 |

> **v2.3 변경 (v1.3)**: Response에서 `device_id`, `sequence`, `group_event` 필드 제거됨.

**v2.3 Response 예시 (Device 존재)**:
```json
{
  "id": 1001,
  "type_event": "Intrusion",
  "action_reported": "False",
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
  "detail": {
    "result": "PIR_SENSOR" //(EnumDetectionType)
  },
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
  "device": null,
  "device_description": "[Multi] Sensor-A-1 (number: 1, id: 101)",
  "detail": {
    "result": "PIR_SENSOR" //(EnumDetectionType)
  },
  "created_at": "2026-01-06T10:15:23.100Z",
  "updated_at": "2026-01-06T10:15:23.100Z"
}
```

#### 12.2.3 DeviceNestedResponse 스키마

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
| `urls` | `object` (nullable) | Camera | **v2.4 변경**: 카메라 URL 통합 스키마 (JSONB) |
| `mode` | `string` (nullable) | Camera | 카메라 모드 (EnumCameraMode) |
| `category` | `string` (nullable) | Camera | 카메라 카테고리 (EnumCameraType) |
| `is_record` | `boolean` (nullable) | Camera | 녹화 여부 |
| `device_groups` | `array` | 공통 | **v2.3 신규**: 소속 DeviceGroup 목록 (EventMapping 연동 필수) |

> **v2.3 추가 (v1.2)**: `device_groups` 필드 추가. EventMapping.device_group_id와 매칭하여 카메라 프리셋 실행에 사용.

**device_groups 필드 예시**:
```json
{
  "device_groups": [
    {"id": 1, "name": "A구역 센서그룹", "description": "A구역 센서 장비 그룹", "device_count": 5},
    {"id": 3, "name": "북측 경계그룹", "description": "북측 경계 장비 그룹", "device_count": 8}
  ]
}
```

#### 12.2.4 Event 영속성 보장

> **핵심 원칙**: Event 데이터는 어떤 경우에도 삭제되지 않아야 한다.

| 시나리오 | device_id | device_description | device (Response) |
|----------|-----------|-------------------|-------------------|
| Event 생성 | `101` | `"[Multi] Sensor-A-1..."` | Nested Object |
| Device 조회 | `101` | `"[Multi] Sensor-A-1..."` | Nested Object |
| **Device 삭제 후** | `NULL` | `"[Multi] Sensor-A-1..."` | `null` |

- **FK 설정**: `ondelete="SET NULL"` (CASCADE 사용 금지!)
- **device_description**: Device 삭제 후에도 과거 Device 정보 참조 가능

#### 12.2.5 마이그레이션 스크립트

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

### 12.3 EventMapping 리팩토링 변경사항 (v2.3)

#### 12.3.1 EventMapping 테이블 변경

| 필드 | Before (v2.2 이전) | After (v2.3) | 설명 |
|------|-------------------|--------------|------|
| `group_event` | VARCHAR(100) | **제거됨** | 자유 문자열, DeviceGroup과 무관 |
| `device_group_id` | - | INTEGER FK **신규** | DeviceGroup.id 참조 (SET NULL on delete) |

#### 12.3.2 API 변경 요약

| API | Before | After |
|-----|--------|-------|
| GET (목록) | `?group_event=xxx` 필터 | `?device_group_id=1` 필터 |
| GET (단건) | `group_event` 필드 반환 | `device_group_id` 필드 반환 |
| POST | `group_event` 문자열 입력 | `device_group_id` 정수 입력 |
| PATCH | `group_event` 수정 가능 | `device_group_id` 수정 가능 |
| PUT | `group_event` 필수 | `device_group_id` 필수 |

#### 12.3.3 이벤트-카메라 연동 흐름

```
이벤트 발생 시 카메라 프리셋 연동 흐름 (v2.4):

1. DetectionEvent 발생 (device_id = 101)
2. Event Response에서 device.device_groups[] 확인
3. device_groups[].id → EventMapping.device_group_id 매칭
4. EventMapping에서 category_event_mapping + device_group_id로 조회
5. 매핑된 EventMappingCamera → CameraPreset 실행

┌─────────────────┐     ┌─────────────────────┐     ┌─────────────────┐
│  Event Response │     │    EventMapping     │     │ CameraPreset    │
│  ─────────────  │     │  ─────────────────  │     │ ─────────────   │
│  device: {      │────►│ device_group_id     │────►│ 프리셋 실행      │
│    device_groups│     │ category_event_     │     │                 │
│    [{id: 1}]    │     │ mapping (Enum)      │     │                 │
│  }              │     │                     │     │                 │
└─────────────────┘     └─────────────────────┘     └─────────────────┘
```

#### 12.3.4 EventMapping FK 정책

| 관계 | 동작 | 정책 | 결과 |
|------|------|------|------|
| DeviceGroup → EventMapping | DeviceGroup 삭제 | `ON DELETE SET NULL` | EventMapping.device_group_id → NULL |

> **참고**: DeviceGroup이 삭제되어도 EventMapping 자체는 유지됨 (device_group_id만 NULL)

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| v3.6 | 2026-02-06 | **Device Setting API 추가 (Camera Settings GET/PATCH, Proxy Settings GET/PATCH), Enum 7종 추가 (EnumOperationMode, EnumWindyMode, EnumWeatherMode, EnumCameraVideoMode, EnumOnOff, EnumDayNightMode, EnumPalette)**<br><br>**[1. Device Setting Enum 추가 (4.9)]**<br>- **EnumOperationMode (2종)**: NORMAL, REGISTER<br>- **EnumWindyMode (4종)**: wind0, wind1, wind2, wind3<br>- **EnumWeatherMode (7종)**: NORMAL, FOG, SEA_FOG, YELLOW_DUST, RAIN, SNOW, HEAT_HAZE<br>- **EnumCameraVideoMode (4종)**: NORMAL, STABILIZATION, BLC, NIGHT_ENHANCE<br>- **EnumOnOff (2종)**: on, off<br>- **EnumDayNightMode (3종)**: AUTO, DAY, NIGHT<br>- **EnumPalette (4종)**: WHITE_HOT, BLACK_HOT, RAINBOW, IRONBOW<br><br>**[2. Camera Settings API (5.3.7~5.3.8)]**<br>- **GET /api/devices/cameras/{camera_id}/settings**: 카메라 설정 조회 (Lazy 생성)<br>- **PATCH /api/devices/cameras/{camera_id}/settings**: 카메라 설정 수정 (Upsert)<br>- **설정 필드**: weather_mode, camera_mode, heater, fan, headlight, day_night_mode, pan_tilt_speed, zoom_speed, palette<br><br>**[3. Proxy Settings API (8.8)]**<br>- **GET /api/servers/{server_id}/proxy-settings**: 프록시 설정 조회 (Lazy 생성)<br>- **PATCH /api/servers/{server_id}/proxy-settings**: 프록시 설정 수정 (Upsert)<br>- **설정 필드**: operation_mode, windy_mode |
| v3.5 | 2026-02-02 | **Audit Log SENSITIVE_FIELDS 정합성 수정**<br><br>**[1. 민감필드 목록 동기화 (9.6.4)]**<br>- `password_hash`, `hashed_password`, `refresh_token`, `user_password` 추가<br>- PRD_Audit_Log.md Section 5.2와 완전 동기화<br>- audit_service.py SENSITIVE_FIELDS 코드와 문서 일치<br><br>**[2. 테스트 수정]**<br>- `test_session_forced_logout_audit_log`: UserSession `login_at` → `created_at` 동기화 (PRD_UserSession_Improvement.md v1.2) |
| v3.4 | 2026-01-26 | **Lamp Device 및 EventMappingLamp API 추가 (PRD_Lamp_Device.md v1.1)**<br><br>**[1. Lamp Enum 추가 (4.1)]**<br>- **EnumDeviceType 확장**: `Lamp = 18` 추가<br>- **EnumLampColor (5종)**: Red, Orange, Green, Blue, White<br>- **EnumBuzzerSound (6종)**: PI-PI-PI, Beep, Siren, Ambulance, Emergency, Mute<br>- **EnumLightMode (3종)**: steady, blinking, rotating<br><br>**[2. Lamp API (5.11)]**<br>- **Endpoint**: `/api/devices/lamps`<br>- **CRUD 지원**: GET (목록/단건), POST, PATCH, PUT, DELETE<br>- **Device Polymorphic 상속**: ip_address, ip_port, description, geolocation<br>- **Nested Response**: device_groups 포함<br>- **ConfigChangeLog 연동**: LAMP 리소스 자동 로깅<br><br>**[3. EventMappingLamp API (7.5)]**<br>- **Endpoint**: `/api/integrations/event-mappings/{mapping_id}/lamps`<br>- **CRUD 지원**: GET (목록/단건), POST, PATCH, PUT, DELETE<br>- **FK 관계**: event_mapping_id (CASCADE), lamp_id (SET NULL)<br>- **동작 설정**: color, buzzer_time, buzzer_sound, light_mode, is_enable, priority<br>- **Nested Response**: event_mapping, lamp 상세 정보 포함<br>- **ConfigChangeLog 연동**: EVENT_MAPPING_LAMP 리소스 자동 로깅<br><br>**[4. DeviceGroup 폴리모픽 응답 확장 (5.6.2)]**<br>- **LampSummary 추가**: ip_address, ip_port, description, geolocation<br>- **DeviceSummary Union 확장**: 6종 지원 (Controller, Sensor, Camera, Speaker, Enclosure, Lamp) |
| v3.3 | 2026-01-23 | **Report API 추가, User API 문서 정합성 수정, DeviceGroup 폴리모픽 응답 확장**<br><br>**[1. Report API 신규 (PRD_Report_System.md)]**<br>- **Report Enum 추가 (4.8)**: EnumReportType (2종), EnumReportPeriod (4종), EnumReportStatus (4종), EnumChartType (4종), EnumReportComponent (15종)<br>- **Report API (10절)**: GET /api/reports/components, templates CRUD, POST /api/reports/generate, generations 조회/다운로드/미리보기<br>- **Report Preview Page (10.5)**: Chart.js 기반 HTML 미리보기<br>- **섹션 번호 변경**: 10 → 11 (에러 처리), 11 → 12 (부록)<br><br>**[2. User API 문서 정합성 수정]**<br>- **GET /api/users (9.3.2)**: department 파라미터 추가, 누락 필드 10개 추가 (email, position, employee_number 등)<br>- **POST /api/users (9.3.3)**: 누락 필드 4개 추가, Response 18개 필드로 확장<br>- **AccountUserCreate/Response 스키마와 완전 동기화**<br><br>**[3. DeviceGroup 폴리모픽 응답 확장 (5.6.2)]**<br>- **SpeakerSummary 추가**: speaker_type, server_id, description, geolocation<br>- **EnclosureSummary 추가**: door_status, heater_enabled, fan_enabled, threshold_config, geolocation<br>- **DeviceSummary Union 확장**: Controller, Sensor, Camera, Speaker, Enclosure 5종 지원<br>- **devices 배열 예시 업데이트**: Speaker, Enclosure 예시 추가 |
| v3.2 | 2026-01-21 | **Config Change Logs API 추가 (PRD_ConfigChangeLog.md v1.1)**<br><br>**[1. Config Change Log Enum 추가 (4.7)]**<br>- **EnumConfigResourceType (19종)**: Device 10종, Server 2종, Event 4종, Integration 3종<br>  - Device: DEVICE, CONTROLLER, SENSOR, CAMERA, SPEAKER, ENCLOSURE, DEVICE_GROUP, DEVICE_GROUP_MAPPING, CAMERA_PRESET, ROI<br>  - Server: SERVER, SERVER_CATEGORY<br>  - Event: EVENT, DETECTION_EVENT, MALFUNCTION_EVENT, CONNECTION_EVENT<br>  - Integration: EVENT_MAPPING, EVENT_MAPPING_CAMERA, EVENT_MAPPING_SPEAKER<br>- **EnumConfigActionType (6종)**: CREATED, UPDATED, DELETED, STATUS_CHANGED, ASSIGNED, UNASSIGNED<br><br>**[2. Config Change Logs API 신규 (9.7)]**<br>- **GET /api/config-change-logs**: 설정 변경 로그 목록 조회 (필터링, 페이지네이션)<br>- **GET /api/config-change-logs/{id}**: 설정 변경 로그 상세 조회<br>- **읽기 전용 API**: 생성/수정/삭제 API 미제공 (시스템 자동 생성)<br>- **자동 로깅**: Device, Server, Event, Integration 계열 리소스 CRUD 시 자동 변경 로그 생성<br>- **스냅샷 보존**: 삭제된 리소스/수행자 정보 유지<br><br>**[3. JSONB 정규화 (v1.1 신규)]**<br>- **변경된 필드만 저장**: 전체 모델 스냅샷 대신 변경된 필드만 기록<br>- **CREATED**: after_state에 `{id, name}` 식별 정보만 저장<br>- **UPDATED**: 변경된 필드만 before/after에 저장<br>- **DELETED**: before_state에 `{id, name}` 식별 정보만 저장<br>- **유틸리티 함수**: `get_changed_fields()`, `get_identifier()` (config_log_service.py) |
| v3.1 | 2026-01-20 | **EnumSystemEventType 15종 동기화, Audit Log API 추가, UserSession API 응답 표준화 (PRD_SystemEvent_Sync.md v1.2, PRD_Audit_Log.md v1.0)**<br><br>**[1. EnumSystemEventType 15종 동기화 (8.7.1)]** (PRD_SystemEvent_Sync.md v1.2)<br>- **USER_* 9종 제거** → UserLoginLog로 이전 (PRD_Account_Design.md Section 9.2)<br>- **ConfigChangeLog 중복 4종 제거**: CONFIG_CHANGED, DEVICE_ADDED, DEVICE_REMOVED, DEVICE_STATUS_CHANGED<br>- **최종 15종**: RESOURCE_THRESHOLD, SERVER_CONNECTED, SERVER_DISCONNECTED, SERVER_ERROR, SERVICE_STARTED, SERVICE_STOPPED, SERVICE_ERROR, CONNECTION_LOST, CONNECTION_RESTORED, SECURITY_ALERT, DEVICE_CONNECTED, BACKUP_STARTED, BACKUP_COMPLETED, BACKUP_FAILED, SYSTEM_UPDATE<br>- **Swagger 스키마 업데이트**: json_schema_extra 예제 추가 (app/schemas/system_event.py)<br><br>**[2. Audit Enum 추가 (4.6)]**<br>- **EnumAuditActionType (18종)**: USER_CREATED, USER_UPDATED, USER_DELETED, USER_LOCKED, USER_UNLOCKED, USER_ACTIVATED, USER_DEACTIVATED, PASSWORD_CHANGED, PASSWORD_RESET, ROLE_CHANGED, GROUP_ASSIGNED, GROUP_CREATED, GROUP_UPDATED, GROUP_DELETED, PERMISSION_CHANGED, SESSION_CREATED, SESSION_TERMINATED, SESSION_FORCED_LOGOUT<br>- **EnumAuditResourceType (4종)**: USER, USER_GROUP, USER_SESSION, PASSWORD<br>- **EnumAuditStatus (2종)**: SUCCESS, FAILURE<br><br>**[3. Audit Logs API 신규 (9.6)]**<br>- **GET /api/audit-logs**: 목록 조회 (필터링, 페이지네이션)<br>- **GET /api/audit-logs/{id}**: 상세 조회<br>- **읽기 전용 API**: 생성/수정/삭제 API 미제공 (시스템 자동 생성)<br>- **자동 로깅**: Account CRUD 작업 시 자동 감사 로그 생성<br>- **변경 내역 추적**: before/after JSON 기록<br>- **스냅샷 보존**: 삭제된 리소스/행위자 정보 유지<br>- **민감 정보 제외**: password, password_hash, token 등 미기록<br><br>**[4. UserSession API 응답 표준화 (9.5)]**<br>- **필드명 변경**: `login_at` → `created_at`, `last_activity` → `updated_at` (다른 모델과 일관성 확보)<br>- **누락 필드 추가**: `logout_reason`, `logged_out_at`, `updated_at` 필드 문서에 반영<br>- **GET /api/user-sessions/{id}**: 상세 조회 API 문서 추가 (9.5.3)<br>- **Query Parameters 업데이트**: `page`, `limit` 파라미터 추가 |
| v3.0 | 2026-01-19 | **Account API 완성 및 Auth Migration (Phase 1)**<br><br>**[1. Account Enum 섹션 추가 (4.5)]**<br>- **EnumUserRole (5종)**: ADMIN, MAINTAINER, OPERATOR, VIEWER, GUEST<br>- **EnumLogoutReason (6종)**: USER_LOGOUT, SESSION_EXPIRED, ADMIN_FORCED, PASSWORD_CHANGED, DUPLICATE_LOGIN, SYSTEM_MAINTENANCE<br>- **EnumLoginAction (3종)**: LOGIN, LOGOUT, TOKEN_REFRESH<br>- **EnumLoginResult (2종)**: SUCCESS, FAILURE<br>- **EnumLoginFailureReason (7종)**: INVALID_CREDENTIALS, ACCOUNT_LOCKED, ACCOUNT_INACTIVE, PASSWORD_EXPIRED, IP_BLOCKED, TOO_MANY_ATTEMPTS, SYSTEM_ERROR<br><br>**[2. Auth API HTTPBearer Migration]**<br>- **인증 방식 변경**: OAuth2PasswordBearer → HTTPBearer<br>- **Swagger UI 개선**: Authorize 버튼으로 Bearer 토큰 직접 입력 가능<br>- **Request 헤더 문서 업데이트**: Authorization 설명 명확화 (`JWT Bearer 토큰 (HTTPBearer 방식) - POST /api/auth/login으로 발급`)<br><br>**[3. Swagger Example 스키마 추가]** (app/schemas/user.py)<br>- **AccountLoginRequest**: login_id: "admin", password: "admin123"<br>- **AccountUserCreate**: login_id, password, name, email, department, position, role, group_id 등 전체 필드<br>- **AccountUserUpdate**: name, email, department, position, role, group_id, is_active 등 전체 필드<br>- **AccountUserResponse**: id, login_id, name, role, is_active, is_locked, created_at 등 전체 필드<br>- **RefreshTokenRequest**: refresh_token example 추가<br>- **PasswordResetRequest, PasswordChangeRequest**: new_password, current_password example 추가<br>- **UserGroupCreate**: name, description, permissions example 추가<br><br>**[4. 스키마 문서 업데이트]** (GOP_스키마_전체.md)<br>- **user_sessions 테이블**: `last_activity` 필드 추가 (마지막 활동 시간) |
| v2.9 | 2026-01-15 | **Device is_enable 필드 추가, Enclosure Metrics API, Server Metrics/System Events API 추가**<br><br>**[1. Device 공통 필드 추가]** (PRD_Device_IsEnable_Field.md v1.0)<br>- **is_enable (BOOLEAN)**: 장비 활성화 여부 (기본값: TRUE)<br>- Controller, Sensor, Camera, Speaker, Enclosure 모든 Device 타입에 적용<br><br>**[2. API 스키마 변경 (is_enable)]**<br>- **Create 스키마**: `is_enable` 필드 추가 (optional, default=true)<br>- **Response 스키마**: `is_enable` 필드 포함<br>- **Update 스키마**: `is_enable` 필드 추가 (optional)<br>- **NestedResponse 스키마**: `is_enable` 필드 포함<br><br>**[3. DeviceGroup/Event 연관 스키마]**<br>- DeviceGroup devices 배열 내 Device 객체에 is_enable 포함<br>- Event device nested 객체에 is_enable 포함<br><br>**[4. Enclosure Metrics API 신규]** (PRD_Enclosure_Metrics_Separation.md v1.0)<br>- **5.5.9 POST /{enclosure_id}/metrics**: 환경 모니터링 메트릭 저장<br>- **5.5.10 GET /{enclosure_id}/metrics**: 메트릭 목록 조회 (시간 필터링 지원)<br>- **5.5.11 GET /{enclosure_id}/metrics/latest**: 최신 메트릭 단건 조회<br>- **5.5.12 DELETE /{enclosure_id}/metrics**: 메트릭 삭제 (before_date 필터)<br>- **threshold_exceeded**: POST 응답에 임계치 초과 경고 정보 포함<br>- **자산/시계열 데이터 분리**: enclosures (자산) ↔ enclosure_metrics (측정값)<br>- **⚠️ Enclosure API 변경**: `detail_info` 필드 제거 → enclosure_metrics API로 이관<br>- **5.5.7 엔드포인트 변경**: "환경 데이터 업데이트" → "도어 상태 업데이트" (door_status만 지원)<br><br>**[5. Server Metrics API 신규]** (PRD_System_Event.md v1.2 Section 2.4)<br>- **8.6.1 POST /servers/{server_id}/metrics**: 서버 리소스 메트릭 기록<br>- **8.6.2 GET /servers/{server_id}/metrics**: 메트릭 이력 조회 (시간 필터링 지원)<br>- **8.6.3 GET /servers/{server_id}/metrics/latest**: 최신 메트릭 조회 (threshold_config 포함)<br>- **8.6.4 DELETE /servers/{server_id}/metrics**: 메트릭 삭제 (before_date 필터)<br>- **threshold_exceeded**: POST 응답에 임계치 초과 경고 정보 포함<br>- **자동 SystemEvent 생성**: 임계치 초과 시 threshold_warning/threshold_critical 이벤트 자동 생성<br>- **servers.threshold_config JSONB**: 서버별 임계치 설정 (cpu, ram, disk, network - warning/critical 레벨)<br><br>**[6. System Events API 신규]** (PRD_System_Event.md v1.2 Section 3)<br>- **8.7.1 GET /system-events**: 이벤트 목록 조회 (필터링, 페이지네이션)<br>- **8.7.2 GET /system-events/{id}**: 이벤트 상세 조회<br>- **8.7.3 POST /system-events**: 이벤트 생성<br>- **8.7.4 POST /system-events/{id}/acknowledge**: 이벤트 확인 처리<br>- **8.7.5 PATCH /system-events/{id}**: 이벤트 수정<br>- **8.7.6 DELETE /system-events/{id}**: 이벤트 삭제<br>- **8.7.7 GET /system-events/summary**: 요약 통계 (severity별, type별, 미확인 수 등)<br>- **EnumSystemEventType (14종)**: server_start, server_stop, threshold_warning, threshold_critical, connection_lost 등<br>- **EnumSystemEventSeverity (4종)**: INFO, WARNING, ERROR, CRITICAL<br>- **source 필드 (PRD 3.2)**: 이벤트 발생 소스 (server_metrics, manual 등)<br>- **updated_at 필드 (PRD 3.2)**: 수정 시간 자동 관리<br>- **server_description 스냅샷**: 서버 삭제 후에도 이벤트 기록 유지 |
| v2.8 | 2026-01-12 | **Event Mapping Speakers API 추가**<br><br>**[1. EventMappingSpeaker API 신규 (7.4 섹션)]**<br>- **Endpoint**: `/api/integrations/event-mappings/{mapping_id}/speakers`<br>- **CRUD 지원**: GET (목록/단건), POST, PATCH, PUT, DELETE<br>- **아키텍처**: EventMapping을 Base 노드로 하는 확장 가능한 Speaker Action 구조<br>- **FK 관계**:<br>  • `event_mapping_id` (CASCADE): EventMapping 삭제 시 함께 삭제<br>  • `speaker_id` (SET NULL): Speaker 삭제 시 연결만 해제<br>  • `file_group_id` (SET NULL): FileGroup 삭제 시 연결만 해제<br>- **주요 필드**: repeat_count (방송 반복 횟수), is_enable, priority<br>- **Nested Response**: speaker, file_group 상세 정보 포함 |
| v2.6 | 2026-01-09 | **Speaker Geolocation 추가 및 Event 필드 정규화**<br><br>**[1. Speaker Geolocation 추가]** (PRD_Speaker_Geolocation.md v1.0)<br>- **speakers.geolocation JSONB 추가**: Speaker 장비 위치 정보<br>- **API 변경**: POST/PATCH/PUT Request에 geolocation 필드 추가<br>- **Response 변경**: GET 응답에 geolocation 필드 포함<br>- **Swagger/Docs 업데이트**: SpeakerCreate, SpeakerUpdate, SpeakerResponse 스키마에 geolocation 필드 추가<br><br>**[2. Event 필드 정규화]** (PRD_Event_Field_Normalization.md v1.0)<br>- **Detection Event**: `result` 별도 필드로 분리 (핵심 분류 필드, 필수)<br>  - `detail`: 상세 정보만 포함 (signal, thumbnail, objects, model, inference_ms)<br>  - 모든 Request/Response에서 result가 별도 필드<br>- **Malfunction Event**: `reason` 별도 필드로 분리 (핵심 분류 필드, 필수)<br>  - `detail`: 상세 정보만 포함 (first_start, first_end, second_start, second_end)<br>  - 모든 Request/Response에서 reason이 별도 필드<br>- **Action Event**: `from_event` nested response에 분리된 필드 적용 |
| v2.4 | 2026-01-08 | **Camera URLs, Speaker/Enclosure Device, Controller/Sensor Geolocation, EventMappingCamera API**<br><br>**[0. ⚠️ Breaking Change: Category Event Refactoring]** (PRD_CategoryEvent_Refactoring.md v1.1)<br>- **EventMapping 필드명 변경**: `category_event` (VARCHAR) → `category_event_mapping` (Enum)<br>- **EnumEventCategory 신규**: Event 모델 polymorphic discriminator용 (DETECTION, MALFUNCTION, CONNECTION)<br>- **EnumMappingEventCategory**: EventMapping 센서 조합 타입용 (FENCE_SENSOR_ONLY, MULTI_SENSOR_ONLY 등)<br>- **Query Parameter 변경**: `?category_event=xxx` → `?category_event_mapping=FENCE_SENSOR_ONLY`<br><br>**[1. Camera URL 스키마 변경]**<br>- **rtsp_uri, rtsp_port 제거** → `urls` JSONB 필드로 통합<br>- **유연한 dict 기반 구조**: homepage, onvif, streams, snapshot 등<br><br>**[2. EventMappingCamera API 신규 (7.3 섹션)]**<br>- **Endpoint**: `/api/integrations/event-mappings/{mapping_id}/cameras`<br>- **CRUD 지원**: GET (목록/단건), POST, PATCH, PUT, DELETE<br>- **레거시 CameraEventMappings API 제거**<br><br>**[3. Server 인증 정보 필드 추가]**<br>- **Server 모델 필드 추가**: `user_name`, `user_password`<br><br>**[4. Speaker Device API 신규]**<br>- **[신규] 5.8 Speaker API**: `/api/devices/speakers` - Device Polymorphic 상속 구조<br>- **[신규] 5.9 FileGroup API**: `/api/file-groups` - 방송음원 파일풀 관리<br>- **EnumDeviceCategory 확장**: `SPEAKER = "speaker"` 추가<br>- **EnumSpeakerType 신규**: NORMAL, ADMIN, MONITOR, DEV<br><br>**[5. Enclosure Device API 신규]** (PRD_Enclosure_Device.md v1.1)<br>- **[신규] 5.10 Enclosure API**: `/api/devices/enclosures` - 함체관리장비<br>- **CRUD 지원**: GET (목록/단건), POST, PATCH, PUT, DELETE<br>- **특수 엔드포인트**: `PATCH /{id}/status` (환경 데이터), `POST /{id}/control` (히터/팬 제어)<br>- **EnumDeviceCategory 확장**: `ENCLOSURE = "enclosure"` 추가<br>- **EnumDoorStatus 신규**: CLOSED, OPEN - 도어 물리적 상태<br>- **Enclosure 테이블**: door_status, detail_info (JSONB), geolocation (JSONB), threshold_config (JSONB), heater_enabled, fan_enabled<br><br>**[6. Controller/Sensor Geolocation 추가]** (PRD_Controller_Sensor_Geolocation.md v1.0)<br>- **controllers.geolocation JSONB 추가**: Controller 장비 위치 정보<br>- **sensors.geolocation JSONB 추가**: Sensor 장비 위치 정보<br>- **geolocation JSON 구조**: `{location, latitude, longitude, altitude}` |
| v2.3 | 2026-01-06 | **API 전면 리팩토링 및 Nested Response 규칙 적용**<br><br>**[1. Event API 변경]**<br>- **Request 필드 통합**: `controller`, `sensor`, `type_device`, `group_event` → `device_id` 단일 FK로 통합<br>- **Response 필드 제거**: `device_id` (중복), `sequence` (완전 제거), `group_event` (`device.device_groups[]`로 대체)<br>- **Response 필드 추가**: `device` (Polymorphic), `device_description` (스냅샷)<br>- **`action_reported` 자동 관리**: Create 시 항상 "False", ActionEvent 생성/삭제 시 시스템 자동 업데이트<br>- **DB 변경**: `events.sequence` 컬럼 `NOT NULL` → `NULL` 허용 (레거시 호환)<br><br>**[2. Device Polymorphic Response]**<br>- Event Response `device` 필드가 타입별 다른 스키마 반환:<br>  • Sensor → SensorNestedResponse (controller_id 포함)<br>  • Controller → ControllerNestedResponse (ip_address, ip_port 포함)<br>  • Camera → CameraNestedResponse (rtsp_uri, mode, category 등 포함)<br><br>**[3. ActionEvent API 변경]**<br>- **Request 필드 제거**: `from_type_event` 제거 - `from_event_id`만으로 원본 이벤트 참조<br>- **Request 필드명 변경**: `from_event` → `from_event_id`<br>- **Polymorphic Relationship**: `from_event_id`가 `events.id` FK를 참조하여 이벤트 타입 자동 확인<br><br>**[4. Nested Response 규칙 일관성 적용]**<br>- **규칙**: 주체 Entity만 `created_at`, `updated_at` 포함, Nested 객체는 제외<br>- **Device API**: `device_groups`, `sensors` nested 객체에서 timestamp 제거<br>- **Sensor API**: `controller` nested 객체에서 timestamp 제거, `include_controller` 파라미터 추가<br>- **Camera Preset API**: `rois`, `points` nested 객체에서 timestamp 제거<br>- **신규 스키마**: `ControllerNestedResponse`, `ROINestedResponse`, `ROIListNestedResponse`, `XyPointNestedResponse`<br><br>**[5. Device `number_device` unique 제약 해제]**<br>- **변경**: 동일한 장치 번호를 여러 디바이스에서 사용 가능<br>- **스키마**: `number_device` 설명에서 "(유니크)" 제거, 409 중복 에러 제거<br>- **확인**: DB 스키마와 모델 모두 이미 `unique=False` 상태<br><br>**[6. EventMapping API 변경]**<br>- `group_event` (VARCHAR) → `device_group_id` (INTEGER FK) 변경<br>- 쿼리 파라미터: `?group_event=xxx` → `?device_group_id=1`<br><br>**[7. 문서 업데이트]**<br>- 10.3 EventMapping 리팩토링 변경사항 추가<br>- Camera PATCH/PUT API: `is_record`, `hardware_spec`, `geolocation`, `group_ids` 필드 추가<br>-  참조: v1.3, v1.5, v2.2, v2.7, v2.8, v2.9 |
| v2.2 | 2025-12-31 | **Event-Device 관계 리팩토링 ( v1.1)**<br>- **[변경] Event API Request**: `controller`, `sensor`, `type_device` 3개 필드 → `device_id` 단일 FK로 통합<br>- **[변경] Event API Response**: `device` nested 객체 추가 (Optional, Device 삭제 시 null)<br>- **[신규] `device_description` 필드**: Device 정보 스냅샷 자동 생성 (형식: `[{type_device}] {name_device} (number: {number_device}, id: {id})`)<br>- **[중요] Event 영속성 보장**: Device 삭제 시 Event.device_id → NULL (CASCADE 금지, SET NULL 사용)<br>- **[중요] device_description 유지**: Device 삭제 후에도 device_description은 보존되어 과거 Device 정보 참조 가능<br>- Detection/Malfunction/Connection Event 모두 동일한 패턴 적용<br>- Action Event의 `from_event` 내에도 `device`, `device_description` 포함<br>- 마이그레이션 스크립트 추가: `scripts/migrate_event_device_id.py`<br>-  v1.1 참조 |
| v2.1 | 2025-12-31 | **Camera Preset, ROI, XyPoint API 추가**<br>- **[신규] 5.5 Camera Preset API**: PTZ 카메라 프리셋 CRUD API 추가<br>- **[신규] 5.6 ROI API**: Region of Interest CRUD API 추가 (`include_points` 파라미터 지원)<br>- **[신규] 5.7 XyPoint API**: ROI 다각형 꼭지점 좌표 CRUD API 추가<br>- 계층 구조: Camera → CameraPreset → ROI → XyPoint (1:N:N:N)<br>- CameraPreset 목록 조회 시 `include_rois` 파라미터로 ROI 정보 포함 가능<br>- ROI 목록 조회 시 `include_points` 파라미터로 Points 정보 포함 가능<br>- CameraPreset 상세 조회 시 ROI 및 Points 전체 중첩 구조 반환<br>- XyPoint 일괄 수정(PUT) 시 기존 포인트 전체 교체 방식<br>- CASCADE DELETE 지원: Camera 삭제 시 Preset → ROI → XyPoint 순차 삭제<br>- 부록 10.1 Endpoint 목록에 Camera Presets, ROIs, XyPoints 섹션 추가 |
| v2.0 | 2025-12-31 | **Device Group N:N 관계 및 폴리모픽 응답 지원**<br>- **[신규] EnumDeviceCategory**: 디바이스 카테고리 Enum 추가 (controller, sensor, camera) - Polymorphic Discriminator<br>- **[신규] 5.4 DeviceGroup API**: 디바이스 그룹 CRUD 및 디바이스 할당/제거 API 추가<br>- DeviceGroup 상세 조회 시 폴리모픽 디바이스 목록 반환 (Controller/Sensor/Camera 타입별 다른 필드)<br>- **Controller API 업데이트**: `device_groups` 배열 필드 추가 (응답), `group_ids` 배열 필드 추가 (요청), `group_id` 쿼리 파라미터 추가<br>- **Sensor API 업데이트**: `device_groups` 배열 필드 추가 (응답), `group_ids` 배열 필드 추가 (요청), `group_id` 쿼리 파라미터 추가<br>- **Camera API 업데이트**: `device_groups` 배열 필드 추가 (응답), `group_ids` 배열 필드 추가 (요청), `group_id` 쿼리 파라미터 추가, `is_record`, `hardware_spec`, `geolocation` 필드 추가<br>- Camera `hardware_spec`: 제조사, 모델명, 펌웨어, MAC주소, ONVIF버전 등 JSON 객체<br>- Camera `geolocation`: 위도, 경도, 고도, 설치위치 등 JSON 객체<br>- `version` 필드 nullable 변경 (v1.2 반영) |
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

**문서 버전**: v3.6
**최종 업데이트**: 2026-02-06