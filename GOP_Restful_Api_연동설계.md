# GOP RESTful API 연동 설계서

**작성일**: 2025-12-31  
**최종 수정일**: 2026-07-31  
**버전**: v6.3.2 (Swagger `6.3.2` 정합)  **작성자**: 이기호 차장  
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
     - 5.3.7 [카메라 설정 조회](#537-카메라-설정-조회) *(v3.7 수정)*
     - 5.3.8 [카메라 설정 수정 (부분)](#538-카메라-설정-수정-부분) *(v3.7 수정)*
     - 5.3.9 [카메라 설정 수정 (전체)](#539-카메라-설정-수정-전체) *(v3.7 신규)*
   - 5.4 [Speaker API](#54-speaker-api) *(v2.4 신규)*
   - 5.5 [Enclosure API](#55-enclosure-api) *(v2.4 신규)*
     - 5.5.13 [Enclosure Metrics 독립 목록 조회](#5513-enclosure-metrics-독립-목록-조회) *(v3.9 신규)*
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
   - 6.5 [Detection Log API](#65-detection-log-api) *(v3.8 신규)*
   - 6.6 [Thumbnail API](#66-thumbnail-api) *(v4.0 신규)*
   - 6.7 [Event Statistics API](#67-event-statistics-api) *(v4.2 신규)*
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
     - 8.3.7 [서버별 시스템 이벤트 조회](#837-서버별-시스템-이벤트-조회) *(v3.9 신규)*
   - 8.4 [Dashboard Summary API](#84-dashboard-summary-api)
   - 8.5 [기본 데이터 (Seed)](#85-기본-데이터-seed)
   - 8.6 [Server Metrics API](#86-server-metrics-api) *(v2.9 신규)*
   - 8.7 [System Events API](#87-system-events-api) *(v2.9 신규)*
   - 8.8 [프록시 설정 API](#88-프록시-설정-api) *(v3.7 수정)*
     - 8.8.1 프록시 설정 조회
     - 8.8.2 프록시 설정 수정 (부분) *(v3.7 제목 변경)*
     - 8.8.3 프록시 설정 수정 (전체) *(v3.7 신규)*
9. [Account API 설계](#9-account-api-설계) *(v3.0 신규)*
   - 9.1 [개요](#91-개요)
   - 9.2 [Auth API](#92-auth-api)
   - 9.3 [User API](#93-user-api)
   - 9.4 [UserGroup API](#94-usergroup-api)
   - 9.5 [UserSession API](#95-usersession-api)
   - 9.6 [Audit Logs API](#96-audit-logs-api) *(v3.1 신규)*
   - 9.7 [Config Change Logs API](#97-config-change-logs-api) *(v3.2 신규)*
   - 9.8 [Session Settings API](#98-session-settings-api-v52-신규) *(v5.2 신규)*
   - 9.9 [권한그룹 부여(Grant) API](#99-권한그룹-부여grant-api-v52-신규) *(v5.2 신규)*
10. [Report API 설계](#10-report-api-설계-v33-신규) *(v3.3 신규)*
    - 10.1 [개요](#101-개요)
    - 10.2 [Report Components API](#102-report-components-api)
    - 10.3 [Report Templates API](#103-report-templates-api)
    - 10.4 [Report Generations API](#104-report-generations-api)
    - 10.5 [Report Preview Page](#105-report-preview-page)
11. [추적 이력 API 설계](#11-추적-이력-api-설계-v411-신규) *(v4.11 신규)*
    - 11.1 [개요](#111-개요)
    - 11.2 [추적점 구간 조회](#112-추적점-구간-조회)
    - 11.3 [추적 세션 목록](#113-추적-세션-목록)
    - 11.4 [추적 가용성 체크](#114-추적-가용성-체크)
12. [에러 처리](#12-에러-처리)
13. [부록](#13-부록)
    - 13.1 [전체 Endpoint 목록](#131-전체-endpoint-목록)
    - 13.2 [Event-Device 리팩토링 변경사항 (v2.3)](#132-event-device-리팩토링-변경사항-v23)
    - 13.3 [EventMapping 리팩토링 변경사항 (v2.3)](#133-eventmapping-리팩토링-변경사항-v23)

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

#### 단건 성공 응답 (200, 201)

```json
{
  "success": true,
  "message": "...",
  "data": { ... },
  "meta": {
    "timestamp": "2025-01-10T10:30:00.000Z",
    "request_id": "..."
  }
}
```

#### 목록 성공 응답 (200)

```json
{
  "success": true,
  "message": "...",
  "data": [ ... ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "total_pages": 5
  },
  "meta": {
    "timestamp": "2025-01-10T10:30:00.000Z",
    "request_id": "..."
  }
}
```

> 단건 응답(ApiSingleResponse)은 pagination 필드를 포함하지 않습니다.

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

### 3.4 Datetime · 타임존 규약 (v6.3 후속, datetime-unification)

> **전역 원칙 (Option B)**: **저장 UTC · 출력 DISPLAY_TZ · 입력 aware 권장**. 특정 국가에 고정되지 않아 해외 사이트(예: 헝가리·미국) 재배포 시 환경변수(`DISPLAY_TIMEZONE`)만 바꾸면 된다.

| 구분 | 규약 |
|------|------|
| **저장(DB)** | 모든 datetime 컬럼은 `TIMESTAMP WITH TIME ZONE`(timestamptz)로 **UTC instant** 저장. (예외: `api_logs.timestamp` 는 파티션 키라 naive-UTC 벽시계 유지 — 표시 규약 동일) |
| **출력(응답)** | 모든 응답 datetime 은 서버 `DISPLAY_TIMEZONE` 기준 ISO 8601 offset 표기. 기본 `Asia/Seoul`(`+09:00`), DST 자동. 예: `"2026-07-31T19:50:00+09:00"`. `meta.timestamp`(성공·오류 **공통**) 동일. |
| **입력(요청)** | offset 포함 aware(`...+09:00`, `...Z`) **권장** — instant 로 정확 해석. offset 없는 naive 값은 `DISPLAY_TIMEZONE` 로 간주 후 UTC 변환. 날짜만(`2026-07-01`) 은 해당 TZ 00:00. |
| **설정** | 환경변수 `DISPLAY_TIMEZONE`(IANA TZ, 예 `Asia/Seoul`·`Europe/Budapest`·`America/New_York`). 미지정 시 `Asia/Seoul`. 저장은 항상 UTC 이므로 이 값 변경은 **표시에만** 영향(과거 데이터 불변). |

**클라이언트 가이드**: 요청 시 가능하면 offset 을 명시하라(`2026-07-01T00:00:00+09:00`). 응답 datetime 은 항상 offset 이 붙어 오므로 그대로 `DateTimeOffset`(.NET)/`ZonedDateTime` 으로 파싱하면 된다. naive 문자열로 파싱 후 로컬 TZ 를 임의 부여하지 말 것.

> **날짜 범위 필터 규약**: 조회·리포트의 `start_date`/`end_date`(서버 메트릭 GET 은 `start_time`/`end_time`) 필터는 **닫힌구간 `[start, end]`**(양끝 포함, `≥ start AND ≤ end`). 리포트 생성(`POST /reports/generate`)은 끝일이 **자정(00:00)·날짜만(date-only)** 으로 오면 그날 **23:59:59.999999 로 자동 확장해 끝일 전체 포함**한다. 입력 포맷은 `+09:00`·`Z`·naive·date-only 모두 수용(naive/date-only 는 DISPLAY_TZ 자정 기준).

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

#### EnumUserRole (사용자 등급 - 2종, v5.3 축소)
```python
# Python 정의 - app/utils/enums.py
class EnumUserRole(str, Enum):
    ADMIN = "ADMIN"   # 관리자 - require_admin/require_perm bypass (그룹 매트릭스 무관 전권)
    USER  = "USER"    # 일반 사용자 - 권한 = 배정 group_id 매트릭스 ∪ 유효 grant 합집합
```

> **v5.3(2026-07-02) 역할 축소**: 이전 5종(MAINTAINER/OPERATOR/VIEWER/GUEST)은 **USER 로 통합**됨(startup 자동 마이그레이션 v62). 실 기능권한은 role 라벨이 아니라 배정 그룹(`group_id`) 매트릭스로 결정된다(ADR_Permission_Model_v5.2).

**사용처**:
- `AccountUser.role`: 사용자 권한 등급(ADMIN 특권 라벨 / USER 일반)

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

#### EnumFocusMode (카메라 초점 모드 - 2종)

```python
# Python 정의 - app/utils/enums.py
class EnumFocusMode(str, Enum):
    """카메라 초점 모드 (ONVIF Focus.AutoFocusMode)"""
    AUTO = "AUTO"       # 자동 초점
    MANUAL = "MANUAL"   # 수동 초점
```

**사용처**:
- `CameraSetting.focus_mode`: 카메라 초점 모드

#### EnumIrisMode (카메라 조리개 모드 - 2종)

```python
# Python 정의 - app/utils/enums.py
class EnumIrisMode(str, Enum):
    """카메라 조리개 모드 (ONVIF Exposure.Mode)"""
    AUTO = "AUTO"       # 자동 조리개
    MANUAL = "MANUAL"   # 수동 조리개
```

**사용처**:
- `CameraSetting.iris_mode`: 카메라 조리개 모드

#### EnumTrackingStatus (추적 상태 - 3종)

```python
# Python 정의 - app/utils/enums.py
class EnumTrackingStatus(str, Enum):
    """추적 상태"""
    ACTIVE = "ACTIVE"   # 타겟 추적 중
    LOST = "LOST"       # 타겟 놓침
    IDLE = "IDLE"       # 추적 비활성
```

**사용처**:
- `CameraSetting.tracking`: 카메라 추적 상태

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
      "onvif_version": "2.4.2",
      "max_detection_range": 120.0
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
| hardware_spec | object | N | null | 하드웨어 사양 정보. 하위필드 `max_detection_range`(number, m) = 카메라 최대 탐지거리(GIS "특정 위치 확인" aim 반경/FOV 산출용) |
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
| hardware_spec | object | N | null | 하드웨어 사양 정보. 하위필드 `max_detection_range`(number, m) = 카메라 최대 탐지거리(GIS "특정 위치 확인" aim 반경/FOV 산출용) |
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
      "onvif_version": "2.4.2",
      "max_detection_range": 120.0
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

> **Note**: (PROXY 서버에 한해) 설정이 존재하지 않으면 기본값으로 자동 생성합니다 (Lazy 생성). 비-PROXY 서버는 **404** (lazy-create 하지 않음).

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
    "focus_mode": "AUTO",             //(EnumFocusMode)
    "iris_mode": "AUTO",              //(EnumIrisMode)
    "tracking": "IDLE",              //(EnumTrackingStatus)
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
  "tracking": "ACTIVE"
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
  "tracking": "ACTIVE"             //(EnumTrackingStatus)
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
| focus_mode | string | N | "AUTO" | 초점 모드 (EnumFocusMode) (현재 값 유지) |
| iris_mode | string | N | "AUTO" | 조리개 모드 (EnumIrisMode) (현재 값 유지) |
| tracking | string | N | "IDLE" | 추적 상태 (EnumTrackingStatus) (현재 값 유지) |
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
    "focus_mode": "AUTO",
    "iris_mode": "AUTO",
    "tracking": "ACTIVE",
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

#### 5.3.9 카메라 설정 수정 (전체)

**Endpoint**: `PUT /api/devices/cameras/{camera_id}/settings`

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| camera_id | integer | Y | Camera ID |

> **Note**: PUT은 전체 교체이므로 **모든 필드를 반드시 포함**합니다 (palette 제외). 설정이 존재하지 않으면 Upsert (자동 생성).

**Request Example**:
```http
PUT /api/devices/cameras/201/settings HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "weather_mode": "FOG",
  "camera_mode": "STABILIZATION",
  "heater": "on",
  "fan": "on",
  "headlight": "off",
  "day_night_mode": "NIGHT",
  "focus_mode": "MANUAL",
  "iris_mode": "AUTO",
  "tracking": "IDLE",
  "palette": null
}
```

**Request Body** (전체 교체 - palette 외 모든 필드 필수):

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| weather_mode | string | **Y** | 기상 모드 (EnumWeatherMode) |
| camera_mode | string | **Y** | 카메라 영상 모드 (EnumCameraVideoMode) |
| heater | string | **Y** | 히터 ON/OFF (EnumOnOff) |
| fan | string | **Y** | 팬 ON/OFF (EnumOnOff) |
| headlight | string | **Y** | 전조등 ON/OFF (EnumOnOff) |
| day_night_mode | string | **Y** | 주야간 모드 (EnumDayNightMode) |
| focus_mode | string | **Y** | 초점 모드 (EnumFocusMode) |
| iris_mode | string | **Y** | 조리개 모드 (EnumIrisMode) |
| tracking | string | **Y** | 추적 상태 (EnumTrackingStatus) |
| palette | string | N | 열화상 팔레트 (EnumPalette, nullable) |

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Camera settings replaced successfully",
  "data": {
    "id": 1,
    "camera_id": 201,
    "weather_mode": "FOG",
    "camera_mode": "STABILIZATION",
    "heater": "on",
    "fan": "on",
    "headlight": "off",
    "day_night_mode": "NIGHT",
    "focus_mode": "MANUAL",
    "iris_mode": "AUTO",
    "tracking": "IDLE",
    "palette": null,
    "created_at": "2026-02-06T12:00:00.000Z",
    "updated_at": "2026-02-09T14:30:00.150Z"
  },
  "meta": {
    "timestamp": "2026-02-09T14:30:00.200Z",
    "request_id": "550e8403-e29b-41d4-a716-446655440000"
  }
}
```

**Error Response (404 Not Found)**:
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Camera with id 999 not found",
    "details": "No camera exists with the specified ID"
  },
  "meta": {
    "timestamp": "2026-02-09T14:30:00.200Z",
    "request_id": "550e8403-e29b-41d4-a716-446655440000"
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
      "device_groups": [
        {"id": 1, "name": "GOP 1구역", "description": "GOP 1구역 장비 그룹", "device_count": 5}
      ],
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
    "device_groups": [
      {"id": 1, "name": "GOP 1구역", "description": "GOP 1구역 장비 그룹", "device_count": 5}
    ],
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
  },
  "group_ids": [1]
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
  },
  "group_ids": [1, 2] // (optional) 소속 디바이스 그룹 ID 배열 (N:N 관계)
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
| group_ids | array[int] | N | null | 소속 디바이스 그룹 ID 배열 (N:N 관계) |

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
    "device_groups": [
      {"id": 1, "name": "GOP 1구역", "description": "GOP 1구역 장비 그룹", "device_count": 5}
    ],
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
  },
  "group_ids": [1]
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
  },
  "group_ids": [1] // (optional) 소속 디바이스 그룹 ID 배열 변경
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
| group_ids | array[int] | N | - | 소속 디바이스 그룹 ID 배열 (현재 값 유지) |

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
    "device_groups": [
      {"id": 1, "name": "GOP 1구역", "description": "GOP 1구역 장비 그룹", "device_count": 5}
    ],
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
  },
  "group_ids": [1]
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
  },
  "group_ids": [1, 2] // (optional) 소속 디바이스 그룹 ID 배열 (N:N 관계)
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
| group_ids | array[int] | N | null | 소속 디바이스 그룹 ID 배열 (N:N 관계) |

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
    "device_groups": [
      {"id": 1, "name": "GOP 1구역", "description": "GOP 1구역 장비 그룹", "device_count": 5}
    ],
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
      "updated_at": "2026-01-08T10:00:00.000000",
      "device_groups": [
        {"id": 1, "name": "GOP 1구역", "description": "GOP 1구역 장비 그룹", "device_count": 5}
      ]
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
  },
  "group_ids": [1]
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
  "fan_enabled": false,
  "group_ids": [1, 2] // (optional) 소속 디바이스 그룹 ID 배열 (N:N 관계)
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
| group_ids | array[int] | N | null | 소속 디바이스 그룹 ID 배열 (N:N 관계) |

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
    "updated_at": "2026-01-08T11:00:00.000000",
    "device_groups": [
      {"id": 1, "name": "GOP 1구역", "description": "GOP 1구역 장비 그룹", "device_count": 5}
    ]
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
  "status": "DEACTIVATED",
  "group_ids": [1]
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
  "status": "DEACTIVATED",
  "group_ids": [1] // (optional) 소속 디바이스 그룹 ID 배열 변경
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
| group_ids | array[int] | N | - | 소속 디바이스 그룹 ID 배열 (현재 값 유지) |

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
    "updated_at": "2026-01-08T11:30:00.000000",
    "device_groups": [
      {"id": 1, "name": "GOP 1구역", "description": "GOP 1구역 장비 그룹", "device_count": 5}
    ]
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
  "fan_enabled": false,
  "group_ids": [1]
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
  "fan_enabled": false,
  "group_ids": [1, 2] // (optional) 소속 디바이스 그룹 ID 배열 (N:N 관계)
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
| group_ids | array[int] | N | null | 소속 디바이스 그룹 ID 배열 (N:N 관계) |

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
    "updated_at": "2026-01-08T12:00:00.000000",
    "device_groups": [
      {"id": 1, "name": "GOP 1구역", "description": "GOP 1구역 장비 그룹", "device_count": 5}
    ]
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

#### 5.5.13 Enclosure Metrics 독립 목록 조회 *(v3.9 신규)*

전체 함체 메트릭을 독립적으로 조회합니다 (flat_router 패턴).

**Endpoint**: `GET /api/enclosure-metrics`

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| page | integer | N | 1 | 페이지 번호 |
| limit | integer | N | 50 | 페이지당 항목 수 |
| enclosure_id | integer | N | - | 특정 함체 필터 |
| from_date | datetime | N | - | 시작 시간 (ISO 8601) |
| to_date | datetime | N | - | 종료 시간 (ISO 8601) |

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Enclosure metrics retrieved successfully",
  "data": {
    "items": [
      {
        "id": 1,
        "enclosure_id": 1,
        "temperature": 25.5,
        "humidity": 60.0,
        "voltage": 220.0,
        "current": 1.5,
        "created_at": "2026-02-13T10:00:00Z"
      }
    ],
    "total": 1
  },
  "pagination": {
    "page": 1,
    "limit": 50,
    "total_pages": 1
  }
}
```

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

#### 5.6.9 디바이스 그룹에서 디바이스 벌크 해제 *(v4.3 신규)*

**Endpoint**: `DELETE /api/devices/groups/{group_id}/devices`

여러 디바이스를 한 번의 요청으로 그룹에서 일괄 해제합니다. 단건 해제(`5.6.8`)의 N회 호출을 1회로 통합하여 그룹 편집 UI에서의 라운드트립을 최소화하고, NATS `SYNC_DEVICE_GROUP` 메시지를 statement-level 트리거로 영향 받는 group당 1건만 발행하여 다운스트림 폭주를 차단합니다.

**Request Example**:
```http
DELETE /api/devices/groups/1/devices HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "device_ids": [1, 2, 3, 999]
}
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| group_id | integer | Y | DeviceGroup ID |

**Request Body**:
```json
{
  "device_ids": [1, 2, 3, 999]
}
```

| 필드 | 타입 | 필수 | 제약 | 설명 |
|------|------|------|------|------|
| device_ids | array[integer] | Y | 1 ≤ len ≤ 100, 중복 자동 제거 | 그룹에서 해제할 디바이스 ID 목록 |

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "2개 디바이스 해제 완료, 1개 건너뜀, 1개 없음",
  "data": {
    "group_id": 1,
    "removed_device_ids": [1, 2],
    "skipped_device_ids": [3],
    "not_found_device_ids": [999],
    "message": "2개 디바이스 해제 완료, 1개 건너뜀, 1개 없음"
  },
  "meta": {
    "timestamp": "2026-06-17T10:41:00.302543+09:00",
    "request_id": null
  }
}
```

> `data.message` 형식: removed/skipped/not_found 중 **개수가 0이 아닌 절만** 콤마로 연결됩니다. 예: skipped=0, not_found=0이면 `"3개 디바이스 해제 완료"` 만 표시. envelope top-level `message` 필드도 동일 문자열로 미러링된다.
> `meta.timestamp`: 서버 `DISPLAY_TIMEZONE` 기준 ISO 8601 offset(기본 `+09:00`, 성공·오류 공통 — 전역 datetime 규약은 §3.4). `meta.request_id`: 클라이언트가 `X-Request-ID` 헤더를 보내면 그 값, 없으면 `null`.

| 응답 필드 | 타입 | 설명 |
|----------|------|------|
| group_id | integer | 대상 DeviceGroup ID |
| removed_device_ids | array[integer] | 실제 매핑이 삭제된 디바이스 ID 목록 |
| skipped_device_ids | array[integer] | device는 존재하지만 그룹 멤버가 아니라 처리할 게 없는 ID 목록 (멱등성 보장) |
| not_found_device_ids | array[integer] | device 자체가 DB에 존재하지 않는 ID 목록 (404가 아니라 분류 응답) |
| message | string | 처리 결과 요약 |

**Error Response** (404 Not Found — 그룹 미존재):
```json
{
  "success": false,
  "message": "DeviceGroup ID 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

**Error Response** (422 Unprocessable Entity — 빈 배열/100건 초과):
```json
{
  "success": false,
  "message": "device_ids must not be empty",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": null
  }
}
```

| HTTP 코드 | 발생 조건 |
|-----------|----------|
| 200 OK | 정상 처리 (전체/부분 해제 모두 200, 결과는 body 3분류로 구분) |
| 404 Not Found | `group_id`에 해당하는 DeviceGroup 미존재 |
| 422 Unprocessable Entity | `device_ids` 누락 / 빈 배열 / 100건 초과 / 타입 오류 |

**ConfigChangeLog 연동**:
- 리소스 타입: `EnumConfigResourceType.DEVICE_GROUP`
- 액션 타입: `EnumConfigActionType.UNASSIGNED`
- 요청당 **1건** 발행 (`before_state.device_ids`에 해제된 ID 리스트, `before_state.categories`에 `{device_id: category}` 매핑)
- `description`: `"DeviceGroup에서 N개 디바이스 해제 (bulk)"`
- `removed_device_ids`가 비어 있으면(전부 skipped/not_found) 미발행

> AuditLog(사용자/계정 행위 감사 도메인)는 본 엔드포인트와 무관 — DeviceGroup 멤버십 변경은 ConfigChangeLog 도메인 (`EnumAuditResourceType`은 `PRD_Audit_Log.md §2.2.2`에 따라 USER/USER_GROUP/USER_SESSION/PASSWORD 4종으로 제한됨).

**NATS SYNC 동작**:
- `device_group_mappings` 테이블의 statement-level 트리거가 발화하여, 영향 받는 `group_id`당 **`SYNC_DEVICE_GROUP/UPDATED` 1건만 발행** (PostgreSQL 10+ `REFERENCING OLD TABLE`).
- 등록(POST `/devices`)도 동일 트리거로 1건/group 발행 — 단건 호출 패턴의 N건 발행 대비 80%+ 감소.

**변경 이력**:
- v4.3 (2026-06-17): 신규. 단건 해제 API(`5.6.8`)의 벌크 보완. POST `/devices`(할당, `5.6.7`)와 메서드/응답 envelope 대칭 구조.

---

### 5.7 Camera Preset API

카메라의 프리셋(Preset)을 관리합니다. PTZ 카메라의 사전 정의된 위치/각도 설정을 저장하고 관리합니다.

**계층 구조**: `Camera` → `CameraPreset` → `ROI` → `XyPoint`

**v4.6 신규 — 감시금지구역 옵션 (차장 결재 2026-06-19)**:
- `is_restricted_zone` (bool, default=false): 감시금지구역 표시
  - true 시: 해당 프리셋으로 카메라가 이동했을 때 매니저 측에서 **통일 처리** (RTSP/녹화/이벤트/화면 모두 차단)
  - false 시: 정상 감시 동작
- 매니저별 처리: VMS(RTSP 차단) / NVR(녹화 중지) / db_monitor(이벤트 발행 차단) / Central UI(화면 마스킹) — 모두 `is_restricted_zone=true` 하나로 통일 트리거
- 매니저 통합 가이드: `docs/v46_camera_preset_restricted_zone_guide.md`

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
  },
  "group_ids": [1, 2] // (optional) 소속 디바이스 그룹 ID 배열 (N:N 관계)
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
| group_ids | array[int] | N | null | 소속 디바이스 그룹 ID 배열 (N:N 관계) |

**Response (201 Created)**: 생성된 Lamp 객체

#### 5.11.4 Lamp 수정 (PATCH)

**Endpoint**: `PATCH /api/devices/lamps/{id}`

**Request Body**: 수정할 필드만 포함 (모든 필드 선택적)

```json
{
  "name_device": "Lamp-A-1-Updated",
  "ip_port": 8080,
  "description": "GOP 1구역 전방 경광등 - 업데이트",
  "group_ids": [1] // (optional) 소속 디바이스 그룹 ID 배열 변경
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
> - `detail`: 상세 정보만 포함 (signal, thumbnail, **frame_width, frame_height**, objects, model, inference_ms). `frame_width/height`(px, v6.3)는 `objects[].bbox` 픽셀좌표 해석 기준
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
        "is_enable": true,
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
      "is_enable": true,
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
      "is_enable": true,
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
      "is_enable": true,
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
      "is_enable": true,
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
- ActionEvent 삭제 시 해당 source event에 남은 ActionEvent가 0개이면 `action_reported`가 자동으로 "False"로 복원됩니다

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

#### 6.1.7 Detection Event의 Action Event 목록 조회

**Endpoint**: `GET /api/events/detections/{event_id}/actions`

**Phase**: 20.1

**설명**:
특정 Detection Event에 연결된 Action Event 목록을 조회합니다.
- 1:N 관계: 하나의 Detection Event에 여러 개의 ActionEvent가 연결될 수 있습니다
- Action Event가 없는 경우 빈 리스트(`[]`) 반환 (404 아님)
- Response에 nested source event (DetectionEvent) 포함

**Path Parameters**:
- `event_id` (int, required): Detection Event ID

**Request Example**:
```http
GET /api/events/detections/1001/actions HTTP/1.1
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
  "message": "Action events retrieved successfully",
  "data": [
    {
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
          "is_enable": true,
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
    }
  ],
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
        "is_enable": true,
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
      "is_enable": true,
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
      "is_enable": true,
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
      "is_enable": true,
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
> **v2.8 정책 (v4.6 명세 정정)**: `action_reported` 필드는 **시스템 자동 관리** (ActionEvent 생성/삭제 시 자동 갱신). 클라이언트가 전송할 수 없으며, 전송해도 무시됨.

**Request Body** (전체 업데이트):
```json
{
  "device_id": 104,
  "type_event": "Fault", //(EnumEventType)
  "reason": "FAULT_ETC", //(EnumFaultType) - v2.6 별도 필드 (필수)
  "detail": { //(optional, 상세 정보만)
    "first_start": 2,
    "first_end": 2,
    "second_start": 5,
    "second_end": 5
  }
}
```
> `action_reported` 제외 (v2.8 자동 관리)

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
      "is_enable": true,
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
- ActionEvent 삭제 시 해당 source event에 남은 ActionEvent가 0개이면 `action_reported`가 자동으로 "False"로 복원됩니다

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

#### 6.2.7 Malfunction Event의 Action Event 목록 조회

**Endpoint**: `GET /api/events/malfunctions/{event_id}/actions`

**설명**:
특정 Malfunction Event에 연결된 Action Event 목록을 조회합니다.
- 1:N 관계: 하나의 Malfunction Event에 여러 개의 ActionEvent가 연결될 수 있습니다
- Action Event가 없는 경우 빈 리스트(`[]`) 반환 (404 아님)
- Response에 nested source event (MalfunctionEvent) 포함

**Path Parameters**:
- `event_id` (int, required): Malfunction Event ID

**Request Example**:
```http
GET /api/events/malfunctions/2001/actions HTTP/1.1
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
  "message": "Action events retrieved successfully",
  "data": [
    {
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
    }
  ],
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
        "is_enable": true,
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
        "is_enable": true,
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
      "is_enable": true,
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

> **참고 (v4.8 Phase 12-7b)**: `device_id` / `device_description`는 **PATCH/PUT 모두 수정 불가** (스냅샷 보존 — v2.1 불변식). device 재지정이 필요하면 DELETE 후 POST로 재생성한다. 클라이언트가 해당 필드를 전송하면 422가 반환된다.

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
- 1:N 관계: 하나의 source event에 여러 개의 ActionEvent를 생성할 수 있습니다
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
        "version": "1.0.0",
        "status": "ACTIVATED",
        "is_enable": true,
        "controller_id": 1,
        "geolocation": null,
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

**Query Parameters** (v4.6 정정 — 모두 optional, 코드 정책과 일치):
- `start_date` (datetime, optional): 조회 시작 시간 (ISO 8601). 미지정 시 1년 전 기본값
- `end_date` (datetime, optional): 조회 종료 시간 (ISO 8601). 미지정 시 현재 시각
- `user` (string, optional): 사용자 필터
- `from_event_id` (int, optional): 특정 source event(`DetectionEvent`/`MalfunctionEvent`) FK 필터 — **v4.6 추가**
- `page` (int, optional, default=1): 페이지 번호
- `limit` (int, optional, default=20): 페이지당 항목 수

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
          "is_enable": true,
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
          "is_enable": true,
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
        "is_enable": true,
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
        "is_enable": true,
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

**Request Example** (v4.6 정정 — 4 필드 모두 required):
```http
PUT /api/events/actions/4001 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "type_event": "Action",
  "content": "침입 탐지 재확인 - 실제 침입 확인됨, 경찰 출동 요청",
  "user": "operator_park",
  "from_event_id": 1002
}
```

**Request Body** (전체 업데이트, v4.6 정정 — 4 필드 모두 required):
```json
{
  "type_event": "Action", //(string, required)
  "content": "침입 탐지 재확인 - 실제 침입 확인됨, 경찰 출동 요청", //(string, required)
  "user": "operator_park", //(string, required)
  "from_event_id": 1002 //(int, required - source event(Detection/Malfunction) FK)
}
```
> v4.6 정정: 옛 예시는 `{content, user}` 2필드만 표기했으나 코드 스키마는 4 required. 매니저가 2필드만 전송 시 즉시 422 발생.

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
        "is_enable": true,
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
- ActionEvent 삭제 시 해당 source event에 남은 ActionEvent가 0개이면 `action_reported` 필드가 자동으로 "False"로 복원됩니다
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
ActionEvent는 DetectionEvent(침입 탐지), MalfunctionEvent(장애 발생)에 대한 조치 보고를 기록하며, source event와 1:N 관계를 유지합니다.

**생성 시 자동 동작**:

1. **Source Event 자동 업데이트**:
   - ActionEvent가 생성되면 source event의 `action_reported` 필드가 자동으로 "False" → "True"로 업데이트됩니다
   - 이는 해당 이벤트에 대한 조치가 이미 보고되었음을 나타냅니다
   - `updated_at` 타임스탬프도 자동으로 갱신됩니다

2. **대상 이벤트 타입**:
   - `Intrusion` (침입 탐지) → DetectionEvent 업데이트
   - `Fault` (장애 발생) → MalfunctionEvent 업데이트

3. **1:N 관계**:
   - 하나의 source event에 여러 개의 ActionEvent를 생성할 수 있습니다
   - 각 ActionEvent는 독립적으로 관리됩니다

**삭제 시 자동 동작**:

1. **Source Event 자동 복원**:
   - ActionEvent가 삭제되면 남은 ActionEvent 수를 확인하여, 0개이면 source event의 `action_reported` 필드가 "True" → "False"로 복원됩니다
   - 아직 다른 ActionEvent가 남아있으면 `action_reported`는 "True"를 유지합니다
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
4. ActionEvent 삭제 → 남은 ActionEvent 0개 → DetectionEvent.action_reported="False" (자동 복원)
   ↓
5. DetectionEvent 삭제 → 200 OK (삭제 성공)
```

---

### 6.5 Detection Log API *(v3.8 신규)*

탐지 이벤트와 조치보고를 JOIN하여 로그 화면 전용으로 제공하는 읽기 전용 API입니다.
**DetectionEvent 1 : N ActionEvent** 관계 (PRD_ActionEvent_1N_Refactoring v2.0 반영, v4.6 명세 정정). 미조치 탐지 이벤트도 포함되며, 이 경우 `actions`는 빈 리스트(`[]`)로 반환됩니다.

#### 6.5.1 Detection Log 목록 조회

- **Endpoint**: `GET /api/detection-logs`
- **설명**: 탐지 로그 목록 조회 (DetectionEvent + ActionEvent LEFT JOIN)

**Query Parameters:**

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|:----:|--------|------|
| `page` | int | X | 1 | 페이지 번호 |
| `limit` | int | X | 20 | 페이지당 항목 수 (최대 100) |
| `device_id` | int | X | - | 장치 ID 필터 |
| `action_reported` | string | X | - | 조치보고 여부 ("True"/"False") |
| `result` | string | X | - | 탐지 결과 유형 (EnumDetectionType) |
| `start_date` | datetime | X | - | 시작 날짜 (ISO 8601) |
| `end_date` | datetime | X | - | 종료 날짜 (ISO 8601) |

**Response (200 OK):**

```json
{
  "success": true,
  "message": "2 detection logs retrieved",
  "data": [
    {
      "id": 1001,
      "type_event": "Intrusion",
      "action_reported": "True",
      "result": "AI_DETECT",
      "device": {
        "id": 101,
        "number_device": 1,
        "group_device": 1, // (Deprecated 예정, 레거시)
        "name_device": "Sensor-A-1",
        "type_device": "Multi",
        "version": "v1.5.0",
        "status": "ACTIVATED",
        "is_enable": true,
        "controller_id": 1,
        "geolocation": null,
        "device_groups": []
      },
      "device_description": "[Multi] Sensor-A-1 (number: 1, id: 101)",
      "detail": {
        "thumbnail": "http://192.168.1.50:8080/events/1001/thumb.jpg",
        "signal": 1500,
        "objects": [{"label": "person", "confidence": 0.95, "bbox": [100, 200, 50, 100]}]
      },
      "actions": [
        {
          "id": 4001,
          "content": "침입 탐지 확인 및 순찰 출동 요청",
          "user": "operator_kim",
          "created_at": "2026-01-06T10:16:00.100Z",
          "updated_at": "2026-01-06T10:16:00.100Z"
        }
      ],
      "created_at": "2026-01-06T10:15:23.100Z",
      "updated_at": "2026-01-06T10:15:23.100Z"
    },
    {
      "id": 1002,
      "type_event": "Intrusion",
      "action_reported": "False",
      "result": "THERMAL_SENSOR",
      "device": { "..." },
      "device_description": "[Fence] Sensor-B-1 (number: 2, id: 102)",
      "detail": null,
      "actions": [],
      "created_at": "2026-01-06T10:20:00.100Z",
      "updated_at": "2026-01-06T10:20:00.100Z"
    }
  ],
  "pagination": { "page": 1, "limit": 20, "total": 2, "total_pages": 1 },
  "meta": { "timestamp": "2026-01-06T10:40:00.250Z", "request_id": "..." }
}
```

#### 6.5.2 Detection Log 단건 조회

- **Endpoint**: `GET /api/detection-logs/{event_id}`
- **설명**: 특정 탐지 로그 상세 조회 (ActionEvent JOIN 포함)

**Response (200 OK)**: `ApiSingleResponse[DetectionLogResponse]`
- DetectionEventResponse 전체 필드 + `actions` 필드 (list[ActionNested], 미조치 시 빈 리스트 `[]`)
- 동일 DetectionEvent에 다건 ActionEvent 누적 가능 (PRD_ActionEvent_1N_Refactoring v2.0)

**Error Response:**
- 404: 탐지 로그를 찾을 수 없음

---

### 6.6 Thumbnail API *(v4.0 신규)*

카메라 썸네일 이미지를 업로드, 저장, 조회, 삭제하는 API입니다.
이미지 파일은 서버 파일 시스템에 날짜별 폴더 구조(`{날짜}/{client_file_name}`)로 저장되며, DB에 메타데이터와 파일 경로를 관리합니다.
클라이언트가 파일명을 직접 지정하여 DetectionEvent와 병렬 등록이 가능합니다 (FK 없이 HTTP URL로 연결).

#### 6.6.1 썸네일 업로드

- **Endpoint**: `POST /api/thumbnails`
- **설명**: 썸네일 이미지 업로드 (multipart/form-data, 클라이언트 지정 파일명)

**Form Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|:----:|------|
| `file` | File | O | 이미지 파일 (image/jpeg, image/png, image/gif, image/webp) |
| `file_name` | string | O | 저장할 파일명 (클라이언트 지정, 예: `CAM-001_2026-02-19_14-30-25-123.jpg`) |

**Response (201 Created):**

```json
{
  "success": true,
  "message": "Thumbnail uploaded successfully",
  "data": {
    "id": 1,
    "file_path": "data/thumbnails/2026-02-19/CAM-001_2026-02-19_14-30-25-123.jpg",
    "file_name": "CAM-001_2026-02-19_14-30-25-123.jpg",
    "file_size": 245760,
    "mime_type": "image/jpeg",
    "width": 1920,
    "height": 1080,
    "image_url": "/api/thumbnails/images/CAM-001_2026-02-19_14-30-25-123.jpg",
    "created_at": "2026-02-19T14:30:25.123+09:00"
  }
}
```

**Error Response:**
- 400: 지원하지 않는 파일 형식
- 409: 동일 file_name 이미 존재
- 422: file_name 또는 file 누락

#### 6.6.2 썸네일 목록 조회

- **Endpoint**: `GET /api/thumbnails`
- **설명**: 썸네일 목록 조회 (날짜 범위 필터링, 페이지네이션)

**Query Parameters:**

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|:----:|--------|------|
| `page` | int | X | 1 | 페이지 번호 |
| `limit` | int | X | 20 | 페이지당 항목 수 (최대 100) |
| `start_date` | datetime | X | - | 시작 날짜 필터 |
| `end_date` | datetime | X | - | 종료 날짜 필터 |

**Response (200 OK):** `ApiResponse[list[ThumbnailResponse]]`

```json
{
  "success": true,
  "message": "Thumbnails retrieved successfully",
  "data": [
    {
      "id": 1,
      "file_path": "data/thumbnails/2026-02-19/CAM-001_2026-02-19_14-30-25-123.jpg",
      "file_name": "CAM-001_2026-02-19_14-30-25-123.jpg",
      "file_size": 245760,
      "mime_type": "image/jpeg",
      "width": null,
      "height": null,
      "image_url": "/api/thumbnails/images/CAM-001_2026-02-19_14-30-25-123.jpg",
      "created_at": "2026-02-19T14:30:25.123+09:00"
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

#### 6.6.3 썸네일 메타데이터 조회

- **Endpoint**: `GET /api/thumbnails/{id}`
- **설명**: 썸네일 메타데이터 단건 조회

**Response (200 OK):** `ApiSingleResponse[ThumbnailResponse]`

**Error Response:**
- 404: 썸네일을 찾을 수 없음

#### 6.6.4 썸네일 이미지 다운로드 (ID 기반)

- **Endpoint**: `GET /api/thumbnails/{id}/image`
- **설명**: 썸네일 이미지 바이너리 반환 (FileResponse, ID 기반)

**Response (200 OK):** `FileResponse` (Content-Type: image/*)

**Error Response:**
- 404: 썸네일 DB 레코드 없음 또는 파일이 디스크에 존재하지 않음

#### 6.6.5 썸네일 이미지 다운로드 (파일명 기반)

- **Endpoint**: `GET /api/thumbnails/images/{file_name}`
- **설명**: 파일명으로 이미지 바이너리 반환 (FileResponse). `DetectionEvent.detail.thumbnail`에 이 URL을 저장하여 서브시스템이 직접 조회 가능.

**Path Parameter:**

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| `file_name` | string | 저장된 파일명 (예: `CAM-001_2026-02-19_14-30-25-123.jpg`) |

**Response (200 OK):** `FileResponse` (Content-Type: image/*)

**Error Response:**
- 404: 해당 file_name의 DB 레코드 없음 또는 파일이 디스크에 존재하지 않음

#### 6.6.6 썸네일 삭제

- **Endpoint**: `DELETE /api/thumbnails/{id}`
- **설명**: 썸네일 삭제 (파일 + DB 레코드)

**동작:**
- 파일 시스템에서 이미지 파일 삭제
- DB에서 메타데이터 레코드 삭제
- 파일이 이미 없는 경우에도 DB 삭제 진행

**Response (200 OK):** `ApiSingleResponse` (data: null)

**Error Response:**
- 404: 썸네일을 찾을 수 없음

#### ThumbnailResponse 스키마

| 필드 | 타입 | 설명 |
|------|------|------|
| `id` | int | 고유 식별자 |
| `file_path` | string | 서버 파일 시스템 경로 |
| `file_name` | string | 클라이언트 지정 파일명 (UNIQUE) |
| `file_size` | int | 파일 크기 (bytes) |
| `mime_type` | string | MIME 타입 |
| `width` | int \| null | 이미지 너비 (px) |
| `height` | int \| null | 이미지 높이 (px) |
| `image_url` | string | 이미지 다운로드 URL (computed: `/api/thumbnails/images/{file_name}`) |
| `created_at` | datetime | 생성 시간 |

### 6.7 Event Statistics API *(v4.2 신규)*

이벤트 통계 집계 API — 대시보드 차트용 경량 응답을 제공합니다.
서버에서 SQL 집계 후 결과만 전송하여, 기존 전량 다운로드 방식 대비 응답 크기를 99% 감소시킵니다.
탐지 이벤트를 센서/카메라로 분리 집계하며, 3가지 차트 유형(원형·라인·막대)에 맞는 전용 데이터를 제공합니다.

#### 6.7.1 이벤트 요약 (원형 그래프 + 요약 카드)

- **Endpoint**: `GET /api/events/statistics/summary`
- **설명**: 이벤트 타입별 건수 요약, 일평균, 활성 장비 수

**Query Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|:----:|------|
| `start_date` | datetime | O | 조회 시작 시간 (ISO 8601) |
| `end_date` | datetime | O | 조회 종료 시간 (ISO 8601) |

**Response (200 OK):** `ApiSingleResponse[EventSummaryResponse]`

```json
{
  "success": true,
  "message": "Event summary statistics retrieved",
  "data": {
    "start_date": "2025-01-15T00:00:00",
    "end_date": "2025-01-22T00:00:00",
    "days_in_range": 7,
    "total": 275,
    "sensor_detection": 150,
    "camera_detection": 30,
    "malfunction": 45,
    "connection": 30,
    "action": 20,
    "daily_averages": {
      "sensor_detection": 21.4,
      "camera_detection": 4.3,
      "malfunction": 6.4,
      "connection": 4.3,
      "action": 2.9
    },
    "active_devices": {
      "sensors": 25,
      "cameras": 15,
      "controllers": 5
    }
  }
}
```

**필드 설명:**

| 필드 | 타입 | 설명 |
|------|------|------|
| `days_in_range` | int | 조회 기간 일수 (최소 1) |
| `total` | int | 전체 이벤트 건수 (5종 합계) |
| `sensor_detection` | int | 센서 탐지 건수 (Device.category_device == sensor) |
| `camera_detection` | int | 카메라(AI) 탐지 건수 (Device.category_device == camera) |
| `malfunction` | int | 장애 이벤트 건수 |
| `connection` | int | 연결 이벤트 건수 |
| `action` | int | 조치 이벤트 건수 |
| `daily_averages.*` | float | 각 타입의 일평균 (count / days_in_range, 소수점 1자리) |
| `active_devices.sensors` | int | 기간 내 이벤트 발생 센서 수 (DISTINCT device_id) |
| `active_devices.cameras` | int | 기간 내 이벤트 발생 카메라 수 (DISTINCT device_id) |
| `active_devices.controllers` | int | 기간 내 이벤트 발생 제어기 수 (DISTINCT controller_id) |

#### 6.7.2 이벤트 추이 (라인 차트)

- **Endpoint**: `GET /api/events/statistics/trend`
- **설명**: 시간대별 이벤트 건수 추이

**Query Parameters:**

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|:----:|--------|------|
| `start_date` | datetime | O | - | 조회 시작 시간 (ISO 8601) |
| `end_date` | datetime | O | - | 조회 종료 시간 (ISO 8601) |
| `interval` | string | X | `hour` | 집계 단위: `hour`, `day` |

**Response (200 OK):** `ApiSingleResponse[EventTrendResponse]`

```json
{
  "success": true,
  "message": "Event trend statistics retrieved",
  "data": {
    "interval": "hour",
    "start_date": "2025-01-15T00:00:00",
    "end_date": "2025-01-16T00:00:00",
    "series": [
      {
        "time_bucket": "2025-01-15 00",
        "sensor_detection": 3,
        "camera_detection": 1,
        "malfunction": 30,
        "connection": 0,
        "action": 2
      },
      {
        "time_bucket": "2025-01-15 01",
        "sensor_detection": 0,
        "camera_detection": 5,
        "malfunction": 28,
        "connection": 0,
        "action": 0
      }
    ]
  }
}
```

**time_bucket 형식:**
- `hour`: `"YYYY-MM-DD HH"` (예: `"2025-01-15 10"`)
- `day`: `"YYYY-MM-DD"` (예: `"2025-01-15"`)

#### 6.7.3 제어기별/카메라별 이벤트 (막대 그래프)

- **Endpoint**: `GET /api/events/statistics/by-device`
- **설명**: 제어기별 센서 이벤트 + 카메라별 AI 탐지 건수

**Query Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|:----:|------|
| `start_date` | datetime | O | 조회 시작 시간 (ISO 8601) |
| `end_date` | datetime | O | 조회 종료 시간 (ISO 8601) |

**Response (200 OK):** `ApiSingleResponse[EventByDeviceResponse]`

```json
{
  "success": true,
  "message": "Event statistics by device retrieved",
  "data": {
    "start_date": "2025-01-15T00:00:00",
    "end_date": "2025-01-16T00:00:00",
    "controllers": [
      {
        "controller_id": 1,
        "controller_name": "Controller-A",
        "controller_number": 1,
        "sensor_detection": 45,
        "malfunction": 12,
        "connection": 3,
        "action": 5
      }
    ],
    "cameras": [
      {
        "camera_id": 101,
        "camera_name": "AI-Camera-Front",
        "camera_number": 10,
        "camera_detection": 25
      }
    ]
  }
}
```

**설계 포인트:**
- `controllers[]`: Sensor.controller_id 기준 제어기별 집계 (sensor_detection, malfunction, connection, action)
- `controllers[].action`: ActionEvent.from_event_id → Event.device_id → Sensor.controller_id 경로로 집계
- `cameras[]`: Camera 기준 카메라별 AI 탐지 건수 (camera_detection)

#### 6.7.4 대시보드 통합

- **Endpoint**: `GET /api/events/statistics/dashboard`
- **설명**: summary + trend + by-device 3개 API 통합 단일 호출

**Query Parameters:**

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|:----:|--------|------|
| `start_date` | datetime | O | - | 조회 시작 시간 (ISO 8601) |
| `end_date` | datetime | O | - | 조회 종료 시간 (ISO 8601) |
| `interval` | string | X | `hour` | 추이 집계 단위: `hour`, `day` |

**Response (200 OK):** `ApiSingleResponse[EventDashboardResponse]`

```json
{
  "success": true,
  "message": "Event dashboard statistics retrieved",
  "data": {
    "summary": { "total": 275, "days_in_range": 7, "sensor_detection": 150, "..." : "..." },
    "trend": { "interval": "hour", "series": [ "..." ] },
    "by_device": { "controllers": [ "..." ], "cameras": [ "..." ] }
  }
}
```

> 단일 HTTP 호출로 3개 차트 데이터를 모두 가져올 수 있어 네트워크 라운드트립을 최소화합니다.

#### EventStatistics 스키마 요약

| 스키마 | 용도 | 주요 필드 |
|--------|------|-----------|
| `EventSummaryResponse` | 원형 그래프 + 요약 카드 | total, sensor/camera_detection, malfunction, connection, action, daily_averages, active_devices |
| `EventTrendResponse` | 라인 차트 | interval, series[EventTrendItem] |
| `EventTrendItem` | 시간 버킷별 건수 | time_bucket, sensor/camera_detection, malfunction, connection, action |
| `ControllerStats` | 제어기별 통계 | controller_id, controller_name, controller_number, sensor_detection, malfunction, connection, action |
| `CameraStats` | 카메라별 통계 | camera_id, camera_name, camera_number, camera_detection |
| `EventByDeviceResponse` | 막대 그래프 | controllers[ControllerStats], cameras[CameraStats] |
| `EventDashboardResponse` | 통합 대시보드 | summary, trend, by_device |

---

### 6.8 이벤트 억제 스케줄 API *(v6.3 신규)*

공사·설치·장애수리·AS 기간에 **대상(장비/그룹/전체) × 이벤트유형(연결/탐지/장애/전체) × 시간창**을 지정해 이벤트 수신을 억제하는 "정비 창(Maintenance Window)" 관리 API. 저장 테이블 `event_suppression_schedules`. 인가: `require_perm("events", view|edit|delete)`(role=ADMIN bypass, AUTH_MODE=token 강제). PRD: `docs/prds/event-suppression-schedule-prd.md` v1.1.

> ★ **범위 경계(Phase 1)**: DBApi 는 브로커상 발행 전용이라 장비 이벤트가 HTTP POST 로만 유입된다. 본 억제는 **저장(persistence) + DB 파생 다운스트림**(이벤트 로그·통계·보고서·장비 상태 자동전환)을 막는다. PidsProxy/AiAnalysis 가 직접 발행하는 **실시간 NATS 방송은 막지 않는다** — 각 서브시스템이 `GET .../active` 를 조회해 라이브 반응을 억제하는 것이 Phase 2(`docs/subsystems/event-suppression/` 안내 참조).

#### 6.8.1 Endpoint 목록

| Method | Endpoint | 설명 | 인가 | 섹션 |
|---|---|---|---|---|
| POST | `/api/event-suppression-schedules` | 억제 스케줄 생성 | events:edit | 6.8.2 |
| GET | `/api/event-suppression-schedules` | 목록(상태·대상 필터, 페이지) | events:view | 6.8.3 |
| GET | `/api/event-suppression-schedules/active` | 현재 활성 창(배너·서브시스템 조회 훅) | events:view | 6.8.4 |
| GET | `/api/event-suppression-schedules/{id}` | 단건 조회 | events:view | 6.8.5 |
| PATCH | `/api/event-suppression-schedules/{id}` | 부분 변경 | events:edit | 6.8.6 |
| DELETE | `/api/event-suppression-schedules/{id}` | 삭제(soft-cancel) | events:delete | 6.8.7 |
| POST | `/api/event-suppression-schedules/bulk-delete` | **취소·종료 스케줄 일괄 하드삭제**(목록 정리) | events:delete | 6.8.8 |
| — (NATS) | `sensorway.{부대ID}.all.sync.event-suppression` | **`SYNC_EVENT_SUPPRESSION` 발행** — 변경·창경계 전이 알림 | — | 6.8.9 |

**필드 요약** (Enum 은 §4 참조 — `# Python 정의 - app/utils/enums.py`):

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| name | string(200) | ✅ | 작업명/사유 |
| description | string(500) | | 상세 |
| target_type | enum | ✅ | `device` / `group` / `all` (EnumSuppressionTargetType) |
| target_device_ids | int[] | target=device 시 ≥1 | 대상 장비 devices.id **배열**(복수, v6.3 확장) |
| target_group_ids | int[] | target=group 시 ≥1 | 대상 그룹 device_groups.id **배열**(복수, v6.3 확장) |
| target_side | enum | | `detection` / `surveillance` / `both`(기본). group·all 에 적용(감지=sensor/controller, 감시=camera 파생) |
| event_scope | enum | ✅ | `connection` / `detection` / `malfunction` / `all` (EnumSuppressionEventScope) |
| window_start / window_end | datetime | ✅ | 억제 시간창(KST +09:00, 저장 UTC). end>start, end 필수(자동 만료) |
| status(응답) | enum | — | 파생 `pending`/`active`/`expired`/`cancelled`(EnumSuppressionStatus) |
| is_active(응답) | bool | — | sweep 비정규화(표시용). 억제 권위는 요청시점 창 계산 |
| revoked_at(응답) | datetime | — | soft-cancel 시각 |

#### 6.8.2 POST `/api/event-suppression-schedules`

**Request Body**:
```json
{
  "name": "GOP 3구역 펜스 보수",
  "target_type": "group",
  "target_group_ids": [5, 6],
  "target_side": "detection",
  "event_scope": "all",
  "window_start": "2026-08-01T09:00:00+09:00",
  "window_end": "2026-08-01T18:00:00+09:00"
}
```

**Response (201)**:
```json
{
  "success": true,
  "message": "억제 스케줄 생성 성공",
  "data": {
    "id": 12, "name": "GOP 3구역 펜스 보수", "description": null,
    "target_type": "group", "target_device_ids": [], "target_group_ids": [5, 6],
    "target_side": "detection", "event_scope": "all",
    "window_start": "2026-08-01T09:00:00+09:00", "window_end": "2026-08-01T18:00:00+09:00",
    "recurrence_rule": null, "is_active": true, "status": "pending",
    "revoked_at": null, "created_by": 1,
    "created_at": "2026-07-31T20:00:00+09:00", "updated_at": "2026-07-31T20:00:00+09:00"
  }
}
```

**Error**: 400(대상 device/group id 미존재 — 배열 원소 전부 검증) · 422(end≤start, device→ids≥1/group→ids≥1 위반, enum 불량) · 401/403(인가). ※ 대상은 모드 내 **복수**(device N개 / group N개), 응답도 `target_device_ids[]`/`target_group_ids[]` 배열.

#### 6.8.3 GET `/api/event-suppression-schedules`

Query: `page`(≥1), `limit`(1~100), `status`(pending/active/expired/cancelled), `target_type`, `device_id`, `group_id`. 응답: `ApiResponse[list]` + `pagination`.

#### 6.8.4 GET `/api/event-suppression-schedules/active`

현재 활성(진행 중) 창만 반환(revoked 제외, `window_start<=now<window_end`). UI 배너 및 외부 서브시스템(GIS/VMS/Proxy)의 조회 훅. 응답 형식은 6.8.3 목록과 동일(pagination 없음).

#### 6.8.5 GET `/api/event-suppression-schedules/{id}`
단건. **Error**: 404.

#### 6.8.6 PATCH `/api/event-suppression-schedules/{id}`
부분 변경(창/스코프/side/유형). target_type 변경 시 불일치 FK 자동 정리. **Error**: 404 · 422(end≤start, target 정합).

#### 6.8.7 DELETE `/api/event-suppression-schedules/{id}`
soft-cancel(`revoked_at` 세팅 + `is_active=false`, 물리삭제 아님). 응답에 취소된 스케줄(status=cancelled) 반환. **Error**: 404.

#### 6.8.8 POST `/api/event-suppression-schedules/bulk-delete`

취소·종료(terminal) 상태의 억제 스케줄을 **일괄 하드삭제**(물리 제거)한다. `DELETE /{id}`(soft-cancel)와
달리 행 + junction(`event_suppression_target_devices`/`_groups`)을 완전히 제거하며 **복구 불가**.
누적된 취소·종료 이력으로 목록이 비대해질 때 정리 용도.

**Request**

```json
POST /api/event-suppression-schedules/bulk-delete
{ "ids": [3, 5, 8] }
```

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| ids | int[] | ✔ | 삭제할 스케줄 id 목록. 1~500건, 중복 자동 제거 |

**Response 200**

```json
{
  "success": true,
  "message": "삭제 2건 · 스킵(활성/예정) 1건 · 없음 0건",
  "data": {
    "deleted_ids":   [3, 5],
    "skipped_ids":   [8],
    "not_found_ids": []
  }
}
```

| 필드 | 의미 |
|---|---|
| deleted_ids | 실제 물리 삭제된 id (status = `cancelled` 또는 `expired`) |
| skipped_ids | **활성(active)·예정(pending)이라 삭제하지 않음** — 먼저 `DELETE /{id}`로 취소해야 함(오삭제 방지 안전장치) |
| not_found_ids | 존재하지 않는 id |

- **안전장치**: 진행 중이거나 예정된 정비 창은 절대 삭제되지 않고 `skipped_ids`로 분리 보고된다.
- **동시성**: 대상 행을 `SELECT ... FOR UPDATE`로 잠근 뒤 최신 커밋 상태로 status 를 **재판정**한다
  (조회~삭제 사이 다른 세션의 PATCH 로 terminal→active 로 바뀐 행의 오삭제 차단, TOCTOU 안전).
- 삭제된 건마다 `config_change_logs` 에 `SUPPRESSION_SCHEDULE / DELETED` 감사 기록을 남긴다.
- **Error**: 422(`ids` 누락·빈 배열·500건 초과) · 401/403(인가).

#### 6.8.9 NATS 발행 — `SYNC_EVENT_SUPPRESSION`

억제 스케줄의 **변경**(생성/수정/대상교체/취소/하드삭제)과 **시간창 자연 전이**(창 시작·종료)는
NATS 로 브로드캐스트되어 전 서브시스템이 "현재 공사 상태"를 인지할 수 있다.

| 항목 | 값 |
|---|---|
| cmd | `SYNC_EVENT_SUPPRESSION` |
| Subject | `sensorway.{부대ID}.all.sync.event-suppression` |
| body | `{ "action": "CREATED\|UPDATED\|DELETED", "resource_id": 12, "status": "pending\|active\|expired\|cancelled" }` |

- **취소(`DELETE /{id}`)는 soft-cancel 이라 `action=UPDATED` + `status=cancelled`** 로 나간다.
  `action=DELETED` 는 **하드삭제(`POST /bulk-delete`)만**.
- 소비자는 알림 수신 후 `GET /{id}`(상세) 및 `GET /active`(공사 상태 재계산)를 호출한다.
- **억제 해제는 신호에 의존하지 않는다** — 소비자는 캐시한 `window_end` 로컬 타이머로 스스로 풀고,
  `/active` 30~60초 폴링을 유지한다(NATS Core at-most-once → 종료 신호 유실 시 영구 침묵 방지).
- 통지 지연 상한: 정상 **≤5초**(창 경계 date-job), 백스톱 **≤5분**(sweep). 억제 판정 자체는
  요청시점 계산이 권위라 지연 0.
- 상세 계약: 브로커 명세 `Gop_Message_Broker_연동설계_v1.6.md` **§9.12** (v1.6).

#### 6.8.10 억제 게이트 (이벤트 수신 핸들러 동작)

`POST /api/events/detections|malfunctions|connections` 이벤트가 활성 억제 창에 걸리면, 서버는 **201 대신 202** 를 반환하고 레코드를 생성하지 않으며 장비 상태 플립(탐지→ACTIVATED / 장애→ERROR)도 건너뛴다:

```json
HTTP/1.1 202 Accepted
{ "success": true, "suppressed": true,
  "message": "Event (detection) suppressed by active maintenance window",
  "schedule_id": 12 }
```

- 발행/POST 주체(PidsProxy/AiAnalysis)는 **202 를 성공(억제됨)으로 처리**(재시도 금지). 자세히는 `docs/subsystems/event-suppression/INTEGRATION.md` §2.6(202 계약)·§3.2(PidsProxy).
- `connection` POST 는 본 차수부터 라우트-레벨 `events:edit` 데코레이터 정합(기존에도 중앙 매트릭스로 token 모드 인가됨).
- 억제 판정은 요청시점 계산(권위), sweep(`SUPPRESSION_SWEEP_INTERVAL_MINUTES` 기본 5분)은 만료 창 `is_active` 정리(비권위 백스톱). 게이트 오류 시 **fail-open**(억제 안 함, 이벤트 정상 저장).

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

#### 7.3.8 MappingCamera 전체 목록 조회 (독립)

> **v3.8 신규**: 서브시스템 캐시 구성을 위한 독립 조회 API. EventMapping 구분 없이 전체 MappingCamera를 조회한다.

**Endpoint**: `GET /api/integrations/mapping-cameras`

**Query Parameters**:

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|------|--------|------|
| `event_mapping_id` | int | N | - | 특정 EventMapping으로 필터링 |
| `camera_id` | int | N | - | 특정 Camera로 필터링 |
| `is_enable` | boolean | N | - | 활성화 상태 필터 |

**Request Example**:
```http
GET /api/integrations/mapping-cameras?is_enable=true HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Mapping cameras retrieved successfully",
  "data": {
    "items": [
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
            {"id": 1, "name": "A구역 센서그룹", "description": null, "device_count": 0}
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
        "home_preset": null,
        "delay_time": 5,
        "is_enable": true,
        "priority": 1,
        "created_at": "2026-02-01T09:00:00Z",
        "updated_at": "2026-02-01T09:00:00Z"
      }
    ],
    "total": 1
  }
}
```

> **참고**: Response 스키마는 기존 7.3.1의 `EventMappingCameraResponse`와 동일. Nested 객체에 timestamp 미포함 (Nested Response 규칙 적용).

#### 7.3.9 카메라 벌크 등록 *(v4.3 신규)*

##### Endpoint

```
POST /api/integrations/event-mappings/{mapping_id}/cameras/bulk
```

##### Request Example

```http
POST /api/integrations/event-mappings/10/cameras/bulk HTTP/1.1
Host: 10.10.30.10:8000
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Content-Type: application/json

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

##### Path Parameters

| 필드          | 타입  | 필수 | 설명                              |
|---------------|-------|------|-----------------------------------|
| `mapping_id`  | int   | Y    | 카메라를 묶을 EventMapping의 PK   |

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

> v4.5 PR-D 정합화 (2026-06-18): 200 OK 응답에도 envelope `meta.timestamp` (KST +09:00) + `meta.request_id` 동봉. 라우터 `response_model=ApiSingleResponse[EventMappingCameraBulkCreateResponse]` 적용으로 Pydantic이 `meta` 기본값(`ResponseMeta` factory)을 자동 주입. 4xx/5xx 응답도 동일 envelope 유지. Swagger UI(`/docs`)에 정확한 응답 schema 노출.

##### Response Fields (`data`)

| 필드                     | 타입            | 설명                                                                                  |
|--------------------------|-----------------|---------------------------------------------------------------------------------------|
| `mapping_id`             | int             | 대상 EventMapping의 PK                                                                |
| `created_ids`            | `List[int]`     | 실제 INSERT에 성공한 **매핑 row PK (`event_mapping_cameras.id`) 목록** (요청 순서 보존). 단건 §7.3.6 DELETE path `{config_id}`와 동일 의미 — 카메라 PK가 아님 |
| `failed_items`           | `List[object]`  | 검증/DB 오류로 실패한 항목. 각 원소: `{ "index": int, "item": {...}, "error": str }`. `item`은 입력 row 원본 에코 |
| `skipped_config_ids`     | `List[int]`     | 이미 `(mapping_id, camera_id)` 매핑 row가 존재하여 INSERT를 건너뛴 **기존 매핑 row PK 목록** (v4.5 PR-B 신설 — 멱등성 보장). 같은 request 내 동일 `camera_id` 중복은 별개 — N건 모두 시도됨 (v4.6 별도 보강 권고) |
| `not_found_config_ids`   | `List[int]`     | `cameras` 테이블에 존재하지 않는 입력 `camera_id` 목록 (v4.5 PR-B 신설 — 매핑 row PK가 아닌 카메라 PK). `target_preset_id` / `home_preset_id` 부재는 `failed_items[*].error`로 노출 |
| `message`                | string          | 사람이 읽기 좋은 결과 요약                                                            |

##### Error Responses

| HTTP | 코드/사유                          | 설명                                                                  |
|------|------------------------------------|-----------------------------------------------------------------------|
| 404  | `EVENT_MAPPING_NOT_FOUND`          | `mapping_id`에 해당하는 EventMapping이 존재하지 않음                  |
| 422  | `VALIDATION_ERROR` (`items` 비어있음) | `items` 길이가 0인 경우                                            |
| 422  | `VALIDATION_ERROR` (`items` 초과)   | `items` 길이가 100을 초과하는 경우                                    |
| 500  | `INTERNAL_SERVER_ERROR`            | 트랜잭션/네트워크 등 서버 내부 오류                                   |

##### ConfigChangeLog

- 요청당 **무조건 1건** 기록 (v4.5 PR-A 정합화 — Camera/Speaker/Lamp 모두 동일 정책). 0건 케이스도 `after_state.config_ids=[], count=0` 으로 기록되어 매니저가 호출 사실 자체를 감사 가능
- `resource_type` = `EnumConfigResourceType.EVENT_MAPPING_CAMERA`
- `action_type` = `EnumConfigActionType.CREATED`
- `resource_id` = `mapping_id`
- `description`: `(bulk)` 토큰 포함 — 단건/벌크 구분 (예: `"EventMapping에 2개 Camera 연동 일괄 생성 (bulk)"`)
- `after_state` 예시 (`config_ids`는 매핑 row PK 리스트 — 카메라 PK가 아님):

```json
{
  "mapping_id": 10,
  "config_ids": [701, 702],
  "count": 2
}
```

##### NATS 이벤트

- 트리거: `trg_sync_emc_ins` (statement-level, `FOR EACH STATEMENT` + `REFERENCING NEW TABLE`)
- 통지 함수: `fn_notify_emc_stmt` — `SELECT DISTINCT event_mapping_id FROM new_rows` 루프
- 발행 형식: `cmd=SYNC_EVENT_MAPPING`, `action=UPDATED`, `target_id={event_mapping_id}` 단일 메시지 (벌크 등록/해제/단건 등록 공통)
- 동일 `mapping_id`에 대한 N건 INSERT는 **요청당 1 메시지**로 합쳐서 발행 (`per-row` 발행 아님). 단건 N회 호출 대비 N→1 감소

##### 변경 이력 노트

- v4.3 신설. 기존 단건 `POST /api/integrations/event-mappings/{mapping_id}/cameras` (§7.3.3)를 N건 등록 시 N회 호출하던 패턴을 1회 호출로 대체
- 일부 실패가 있어도 성공 row는 커밋되며, 실패 사유는 `failed_items` / `skipped_config_ids` / `not_found_config_ids`로 분리 반환
- §5.6.7 `POST /api/devices/groups/{id}/devices`(단건 할당의 N개 배열 입력) 응답 스키마 패턴과 동일 — 3분류(assigned/skipped/not_found) 시맨틱 차용

---

#### 7.3.10 카메라 벌크 해제 *(v4.3 신규)*

##### Endpoint

```
DELETE /api/integrations/event-mappings/{mapping_id}/cameras
```

##### Request Example

```http
DELETE /api/integrations/event-mappings/10/cameras HTTP/1.1
Host: 10.10.30.10:8000
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Content-Type: application/json

{
  "config_ids": [301, 302, 999]
}
```

##### Path Parameters

| 필드          | 타입  | 필수 | 설명                                  |
|---------------|-------|------|---------------------------------------|
| `mapping_id`  | int   | Y    | 카메라 매핑을 해제할 EventMapping PK  |

##### Request Body

| 필드          | 타입         | 필수 | 제약        | 설명                                                        |
|---------------|--------------|------|-------------|-------------------------------------------------------------|
| `config_ids`  | `List[int]`  | Y    | 1 ~ 100건   | 해제할 **매핑 row PK (`event_mapping_cameras.id`) 배열**. 단건 §7.3.6 DELETE path `{config_id}`와 동일 의미 — 카메라 PK가 아님 |

##### Response Example (200 OK)

```json
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

##### Response Fields (`data`)

| 필드                     | 타입         | 설명                                                                                  |
|--------------------------|--------------|---------------------------------------------------------------------------------------|
| `mapping_id`             | int          | 대상 EventMapping의 PK                                                                |
| `removed_config_ids`     | `List[int]`  | 실제로 DELETE된 **매핑 row PK (`event_mapping_cameras.id`) 목록** (요청 순서 보존)    |
| `skipped_config_ids`     | `List[int]`  | row는 존재하지만 `event_mapping_id`가 path와 불일치하여 처리하지 않은 매핑 row PK (다른 매핑 소속 — 멱등성 보장) |
| `not_found_config_ids`   | `List[int]`  | `event_mapping_cameras` row 자체가 DB에 존재하지 않는 PK 목록 (404가 아니라 분류 응답)|
| `message`                | string       | 사람이 읽기 좋은 결과 요약                                                            |

##### Error Responses

| HTTP | 코드/사유                            | 설명                                                                  |
|------|--------------------------------------|-----------------------------------------------------------------------|
| 404  | `EVENT_MAPPING_NOT_FOUND`            | `mapping_id`에 해당하는 EventMapping이 존재하지 않음                  |
| 422  | `VALIDATION_ERROR` (`config_ids` 비어있음) | `config_ids` 길이가 0인 경우                                    |
| 422  | `VALIDATION_ERROR` (`config_ids` 초과)     | `config_ids` 길이가 100을 초과하는 경우                         |
| 500  | `INTERNAL_SERVER_ERROR`              | 트랜잭션/네트워크 등 서버 내부 오류                                   |

##### ConfigChangeLog

- 요청당 **무조건 1건** 기록 (v4.5 PR-A 정합화). 0건 케이스도 `before_state.config_ids=[], count=0` 으로 기록
- `resource_type` = `EnumConfigResourceType.EVENT_MAPPING_CAMERA`
- `action_type` = `EnumConfigActionType.DELETED`
- `resource_id` = `mapping_id`
- `description`: `(bulk)` 토큰 포함 — 단건/벌크 구분 (예: `"EventMapping에서 2개 Camera 연동 일괄 해제 (bulk)"`)
- `before_state` 예시 (`config_ids`는 매핑 row PK 리스트 — 카메라 PK가 아님):

```json
{
  "mapping_id": 10,
  "config_ids": [701, 702],
  "count": 2
}
```

##### NATS 이벤트

- 트리거: `trg_sync_emc_del` (statement-level, `FOR EACH STATEMENT` + `REFERENCING OLD TABLE`)
- 통지 함수: `fn_notify_emc_stmt` — `SELECT DISTINCT event_mapping_id FROM old_rows` 루프
- 발행 형식: `cmd=SYNC_EVENT_MAPPING`, `action=UPDATED`, `target_id={event_mapping_id}` 단일 메시지 (벌크 등록과 동일 family)
- 동일 `mapping_id`에 대한 N건 DELETE는 **요청당 1 메시지**로 합쳐서 발행. `skipped` row는 트리거 발화에 포함되지 않으므로 통지에 영향 없음

##### 변경 이력 노트

- v4.3 신설. 기존 단건 `DELETE /api/integrations/event-mappings/{mapping_id}/cameras/{config_id}` (§7.3.6)를 N건 해제 시 N회 호출하던 패턴을 1회 호출로 대체
- 일부 `config_id`가 매핑되어 있지 않거나 카메라가 미존재해도 다른 row의 해제는 정상 커밋되며, 사유는 `skipped_config_ids` / `not_found_config_ids`로 분리 반환
- §5.6.9 `DELETE /api/devices/groups/{group_id}/devices`와 동일한 응답 스키마 패턴 — 3분류(removed/skipped/not_found) 시맨틱 차용
---

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

#### 7.4.8 MappingSpeaker 전체 목록 조회 (독립)

> **v3.8 신규**: 서브시스템 캐시 구성을 위한 독립 조회 API. EventMapping 구분 없이 전체 MappingSpeaker를 조회한다.

**Endpoint**: `GET /api/integrations/mapping-speakers`

**Query Parameters**:

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|------|--------|------|
| `event_mapping_id` | int | N | - | 특정 EventMapping으로 필터링 |
| `speaker_id` | int | N | - | 특정 Speaker로 필터링 |
| `is_enable` | boolean | N | - | 활성화 상태 필터 |

**Request Example**:
```http
GET /api/integrations/mapping-speakers?is_enable=true HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Mapping speakers retrieved successfully",
  "data": {
    "items": [
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
          "geolocation": null
        },
        "file_group": {
          "id": 501,
          "server_id": 1,
          "group_id": 1,
          "group_name": "경보음원 그룹A",
          "files": ["alarm_01.wav"]
        },
        "repeat_count": 3,
        "is_enable": true,
        "priority": 1,
        "created_at": "2026-02-01T09:00:00Z",
        "updated_at": "2026-02-01T09:00:00Z"
      }
    ],
    "total": 1
  }
}
```

> **참고**: Response 스키마는 기존 7.4.1의 `EventMappingSpeakerResponse`와 동일.

---

#### 7.4.9 EventMappingSpeaker 벌크 등록 *(v4.3 신규)*

**Endpoint**: `POST /api/integrations/event-mappings/{mapping_id}/speakers/bulk`

한 EventMapping에 여러 스피커 연동을 한 번의 요청으로 일괄 생성합니다. 단건 등록(`7.4.3`)의 N회 호출을 1회로 통합하여 매핑 마법사 다중선택 UX의 라운드트립과 NATS `SYNC_EVENT_MAPPING` 발행 폭주를 차단합니다.

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| mapping_id | integer | Y | EventMapping ID |

**Request Body**:
| 필드 | 타입 | 필수 | 제약 | 설명 |
|------|------|------|------|------|
| items | array[`EventMappingSpeakerCreate`] | Y | 1 ≤ len ≤ 100 | 일괄 생성할 스피커 연동 리스트 (단건 스키마 재사용) |

**items[].EventMappingSpeakerCreate**:
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| speaker_id | integer | Y | 대상 스피커 ID |
| file_group_id | integer | N | 방송 파일 그룹 ID |
| repeat_count | integer | N | 방송 반복 횟수 (기본값: 1, 최소값: 1) |
| is_enable | boolean | N | 활성화 여부 (기본값: true) |
| priority | integer | N | 실행 우선순위 (Optional) |

**Request Example**:
```http
POST /api/integrations/event-mappings/10/speakers/bulk HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "items": [
    {
      "speaker_id": 301,
      "file_group_id": 1,
      "repeat_count": 3,
      "is_enable": true,
      "priority": 1
    },
    {
      "speaker_id": 302,
      "file_group_id": 2,
      "repeat_count": 2,
      "is_enable": true,
      "priority": 2
    },
    {
      "speaker_id": 999,
      "repeat_count": 1,
      "is_enable": true
    }
  ]
}
```

**Response Example** (200 OK — 부분 성공):
```json
{
  "success": true,
  "message": "2개 Speaker 연동 생성 완료, 1개 실패",
  "data": {
    "mapping_id": 10,
    "created_ids": [501, 502],
    "failed_items": [
      {
        "index": 2,
        "item": {
          "speaker_id": 999,
          "file_group_id": null,
          "repeat_count": 1,
          "is_enable": true,
          "priority": null
        },
        "error": "Speaker with id 999 not found"
      }
    ],
    "message": "2개 Speaker 연동 생성 완료, 1개 실패"
  },
  "meta": {
    "timestamp": "2026-06-17T10:40:00.000+09:00",
    "request_id": "550e8408-e29b-41d4-a716-446655440000"
  }
}
```

| 응답 필드 | 타입 | 설명 |
|----------|------|------|
| mapping_id | integer | 대상 EventMapping ID |
| created_ids | array[integer] | 실제로 생성된 EventMappingSpeaker row PK 목록 (요청 items 순서 보존) |
| failed_items | array[object] | row-level 실패 상세 (`index` / `item` / `error`). FK 무효(존재하지 않는 `speaker_id`, `file_group_id`) 시 분류 |
| message | string | 처리 결과 요약 |

**Error Response** (404 Not Found — EventMapping 미존재):
```json
{
  "success": false,
  "message": "Event mapping with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

**Error Response** (422 Unprocessable Entity — 빈 배열 / 최대 초과):
```json
{
  "success": false,
  "message": "items must contain between 1 and 100 entries",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [
      {
        "loc": ["body", "items"],
        "msg": "List should have at least 1 item after validation, not 0",
        "type": "too_short"
      }
    ]
  }
}
```

| HTTP 코드 | 발생 조건 |
|-----------|----------|
| 200 OK | 정상 처리 (전체/부분 성공 모두 200, 결과는 body로 구분) |
| 404 Not Found | `mapping_id`에 해당하는 EventMapping 미존재 |
| 422 Unprocessable Entity | `items` 누락 / 빈 배열 / 101개 이상 / Pydantic 타입 오류 |
| 500 Internal Server Error | DB 트랜잭션 오류 |

**ConfigChangeLog 연동**:
- 리소스 타입: `EnumConfigResourceType.EVENT_MAPPING_SPEAKER`
- 액션 타입: `EnumConfigActionType.CREATED`
- `created_ids` ≥ 1일 때만 요청당 **1건** 발행 (`after_state.config_ids` 리스트 응축, `count` 필드 동봉)
- 전체 실패(`created_ids = []`) 시 미발행
- `description`에 `(bulk)` 토큰 포함 — 단건/벌크 구분

**NATS SYNC 발행**:
- 트리거: `trg_sync_ems_ins` / `trg_sync_ems_upd` / `trg_sync_ems_del` (statement-level, `FOR EACH STATEMENT`)
- 함수: `fn_notify_ems_stmt` — `REFERENCING NEW TABLE / OLD TABLE` + `SELECT DISTINCT event_mapping_id` 루프
- 발행 보장: 단일 매핑 벌크 INSERT N건 → `SYNC_EVENT_MAPPING/UPDATED/{event_mapping_id}` **1건**
- 다중 `event_mapping_id`가 한 statement에 섞이면 매핑 수만큼 정확히 발행

**처리 정책**:
- **트랜잭션**: row-level FK 검증 후 `db.add` 누적 → `db.flush()`(PK 채번) → 단일 `db.commit()`
- **Best-effort**: row-level 실패(FK 무효 등)는 `failed_items`로 분리, 성공한 row만 commit
- **per-row 부가 필드 보존**: `file_group_id` / `repeat_count` / `priority`를 단건과 동일하게 유지

**변경 이력**:
- v4.3 (2026-06-17): 신규. 단건 등록(`7.4.3`)의 벌크 보완. `7.3.9`(Camera 벌크 등록), `7.5.9`(Lamp 벌크 등록)와 동일 패턴.

---

#### 7.4.10 EventMappingSpeaker 벌크 해제 *(v4.3 신규)*

**Endpoint**: `DELETE /api/integrations/event-mappings/{mapping_id}/speakers`

한 EventMapping에서 여러 스피커 연동을 한 번의 요청으로 일괄 해제합니다. 단건 삭제(`7.4.6`)의 N회 호출을 1회로 통합하며, 중복 ID와 다른 매핑 소속 ID를 안전하게 처리하는 멱등 시맨틱을 제공합니다.

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| mapping_id | integer | Y | EventMapping ID |

**Request Body**:
| 필드 | 타입 | 필수 | 제약 | 설명 |
|------|------|------|------|------|
| config_ids | array[integer] | Y | 1 ≤ len ≤ 100 | 해제할 EventMappingSpeaker row PK 목록 (중복 자동 제거) |

**Request Example**:
```http
DELETE /api/integrations/event-mappings/10/speakers HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "config_ids": [501, 502, 503, 999]
}
```

**Response Example** (200 OK — 부분 성공):
```json
{
  "success": true,
  "message": "2개 Speaker 연동 해제 완료, 1개 건너뜀, 1개 없음",
  "data": {
    "mapping_id": 10,
    "removed_config_ids": [501, 502],
    "skipped_config_ids": [503],
    "not_found_config_ids": [999],
    "message": "2개 Speaker 연동 해제 완료, 1개 건너뜀, 1개 없음"
  },
  "meta": {
    "timestamp": "2026-06-17T10:41:00.000+09:00",
    "request_id": "550e8409-e29b-41d4-a716-446655440000"
  }
}
```

| 응답 필드 | 타입 | 설명 |
|----------|------|------|
| mapping_id | integer | 대상 EventMapping ID |
| removed_config_ids | array[integer] | 실제로 삭제된 EventMappingSpeaker row PK 목록 |
| skipped_config_ids | array[integer] | row는 DB에 존재하나 해당 `mapping_id`에 속하지 않아 건너뛴 ID 목록 (멱등) |
| not_found_config_ids | array[integer] | row 자체가 DB에 존재하지 않는 ID 목록 |
| message | string | 처리 결과 요약 |

**Error Response** (404 Not Found — EventMapping 미존재):
```json
{
  "success": false,
  "message": "Event mapping with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

**Error Response** (422 Unprocessable Entity — 빈 배열):
```json
{
  "success": false,
  "message": "config_ids must contain between 1 and 100 entries",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [
      {
        "loc": ["body", "config_ids"],
        "msg": "List should have at least 1 item after validation, not 0",
        "type": "too_short"
      }
    ]
  }
}
```

| HTTP 코드 | 발생 조건 |
|-----------|----------|
| 200 OK | 정상 처리 (전체/부분 해제 모두 200, 전부 skipped/not_found여도 200) |
| 404 Not Found | `mapping_id`에 해당하는 EventMapping 미존재 |
| 422 Unprocessable Entity | `config_ids` 누락 / 빈 배열 / 101개 이상 / Pydantic 타입 오류 |
| 500 Internal Server Error | DB 트랜잭션 오류 |

**멱등성 보장**:
- 동일 요청 재호출 시 두 번째는 `removed_config_ids = []`, `not_found_config_ids`에 전체 ID 분류
- 중복 ID(`[501, 501, 502]`)는 `dict.fromkeys`로 1회만 처리
- 다른 매핑 소속 row 잘못 호출 시 `skipped_config_ids`로 안전 분류 (삭제 X)

**ConfigChangeLog 연동**:
- 리소스 타입: `EnumConfigResourceType.EVENT_MAPPING_SPEAKER`
- 액션 타입: `EnumConfigActionType.DELETED`
- `removed_config_ids` ≥ 1일 때만 요청당 **1건** 발행 (`before_state.config_ids` 리스트 응축, `count` 필드 동봉)
- 전부 skipped/not_found 시 미발행
- `description`에 `(bulk)` 토큰 포함 — 단건/벌크 구분

**NATS SYNC 발행**:
- 트리거: `trg_sync_ems_del` (statement-level, `FOR EACH STATEMENT`)
- 함수: `fn_notify_ems_stmt` — `REFERENCING OLD TABLE` + `SELECT DISTINCT event_mapping_id` 루프
- 발행 보장: 단일 매핑 벌크 DELETE N건 → `SYNC_EVENT_MAPPING/UPDATED/{event_mapping_id}` **1건**

**처리 정책**:
- **트랜잭션**: 3-way 분류(removed/skipped/not_found) 후 단일 `db.commit()`
- **idempotent**: 중복/미소속/부재 ID 안전 처리, 전부 비정상이어도 200

**변경 이력**:
- v4.3 (2026-06-17): 신규. 단건 삭제(`7.4.6`)의 벌크 보완. 단건 시그니처는 완전 보존(deprecate 안 함). `7.3.10`(Camera 벌크 해제), `7.5.10`(Lamp 벌크 해제)와 동일 패턴.

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

#### 7.5.9 MappingLamp 전체 목록 조회 (독립)

> **v3.8 신규** (v4.6 FR-10 재채번 — 기존 §7.5.7 중복 해소, §7.5.9로 이동): 서브시스템 캐시 구성을 위한 독립 조회 API. EventMapping 구분 없이 전체 MappingLamp를 조회한다.

**Endpoint**: `GET /api/integrations/mapping-lamps`

**Query Parameters**:

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|------|--------|------|
| `event_mapping_id` | int | N | - | 특정 EventMapping으로 필터링 |
| `lamp_id` | int | N | - | 특정 Lamp로 필터링 |
| `is_enable` | boolean | N | - | 활성화 상태 필터 |

**Request Example**:
```http
GET /api/integrations/mapping-lamps?is_enable=true HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Mapping lamps retrieved successfully",
  "data": {
    "items": [
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
          "geolocation": null
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
    "total": 1
  }
}
```

> **참고**: Response 스키마는 기존 7.5.1의 `EventMappingLampResponse`와 동일.

---

#### 7.5.10 EventMappingLamp 벌크 등록 *(v4.3 신규)*

**Endpoint**: `POST /api/integrations/event-mappings/{mapping_id}/lamps/bulk`

여러 경광등 연동을 한 번의 요청으로 일괄 등록합니다. 단건 생성(`7.5.3`)의 N회 호출을 1회로 통합하여 매핑 마법사에서 다중 선택한 경광등 N개에 대한 라운드트립을 최소화하고, NATS `SYNC_EVENT_MAPPING` 메시지를 statement-level 트리거로 영향 받는 `event_mapping_id`당 1건만 발행하여 LampManager / GIS 등 다운스트림 캐시 무효화 폭주를 차단합니다. 부분 성공(best-effort) 시맨틱이므로 일부 row의 FK 검증이 실패해도 나머지는 정상 생성되며 HTTP 200을 반환합니다.

**Request Example**:
```http
POST /api/integrations/event-mappings/10/lamps/bulk HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "items": [
    {
      "event_mapping_id": 10,
      "lamp_id": 501,
      "color": "Red",
      "buzzer_time": 5,
      "buzzer_sound": "PI-PI-PI",
      "light_mode": "steady",
      "is_enable": true,
      "priority": 1
    },
    {
      "event_mapping_id": 10,
      "lamp_id": 502,
      "color": "Orange",
      "buzzer_time": 10,
      "buzzer_sound": "Emergency",
      "light_mode": "blinking",
      "is_enable": true,
      "priority": 2
    },
    {
      "event_mapping_id": 10,
      "lamp_id": 999,
      "color": "Green",
      "buzzer_time": 3,
      "buzzer_sound": "Ambulance",
      "light_mode": "steady",
      "is_enable": true,
      "priority": 3
    }
  ]
}
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| mapping_id | integer | Y | EventMapping ID (등록 대상의 신뢰원) |

**Request Body**:
| 필드 | 타입 | 필수 | 제약 | 설명 |
|------|------|------|------|------|
| items | array[EventMappingLampCreate] | Y | 1 ≤ len ≤ 100 | 일괄 등록할 경광등 연동 row 리스트 (단건 스키마 재사용) |

**`items[*]` 요소 필드** (단건 `EventMappingLampCreate`와 완전 동일):
| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| event_mapping_id | integer | Y | - | **무시됨** — 본문에 포함하더라도 path parameter `{mapping_id}`로 덮어써짐 (아래 주의 참조) |
| lamp_id | integer | Y | - | 대상 Lamp ID |
| color | string | N | "Red" | 경광등 색상 (EnumLampColor) |
| buzzer_time | integer | N | 5 | 부저 작동 시간 (초, ≥0) |
| buzzer_sound | string | N | "PI-PI-PI" | 부저 소리 패턴 (EnumBuzzerSound) |
| light_mode | string | N | "steady" | 점등 모드 (EnumLightMode) |
| is_enable | boolean | N | true | 활성화 여부 |
| priority | integer | N | 1 | 우선순위 (≥1, 낮을수록 높음) |

**Enum 허용값**: 단건 생성(`7.5.3`)과 동일.
- **color (EnumLampColor)**: Red, Orange, Green, Blue, White
- **buzzer_sound (EnumBuzzerSound)**: Fire A-WANG, Emergency, Ambulance, PI-PI-PI, PI_continue
- **light_mode (EnumLightMode)**: steady, blinking

> **v4.5 PR-C 정합화 (2026-06-18)**: `EventMappingLampCreate`/`Update`/`Replace`의 `color`/`buzzer_sound`/`light_mode`가 plain `str` → `EnumLampColor`/`EnumBuzzerSound`/`EnumLightMode` Pydantic 타입으로 전환됨. 허용값 외 입력은 Pydantic 422 검증에서 사전 차단(`Input should be 'Red', 'Orange', 'Green', 'Blue' or 'White'` 등 명확한 에러 메시지 반환). 더 이상 DB INSERT까지 도달하지 않으므로 enum 위반 500은 발생하지 않는다.

> **주의 — `items[*].event_mapping_id` 무시 정책**:
> 단건 스키마 재사용을 위해 `EventMappingLampCreate`에 정의된 `event_mapping_id` 필드를 본문에 포함할 수 있으나, 벌크 엔드포인트는 **path parameter `{mapping_id}`를 단일 신뢰원**으로 사용한다. `items` 각 요소의 `event_mapping_id`는 라우터에서 무시·덮어쓰기되므로 path와 body의 값이 달라도 path 값이 적용된다. 클라이언트는 `items[*].event_mapping_id`를 path와 동일한 값으로 채워 보내거나(권장), 0 등 placeholder를 넣어도 무방하다 — 어느 쪽이든 결과는 동일하다.

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "2개 Lamp 연동 생성 완료, 1개 실패",
  "data": {
    "mapping_id": 10,
    "created_ids": [701, 702],
    "failed_items": [
      {
        "index": 2,
        "item": {
          "event_mapping_id": 10,
          "lamp_id": 999,
          "color": "Green",
          "buzzer_time": 3,
          "buzzer_sound": "Ambulance",
          "light_mode": "steady",
          "is_enable": true,
          "priority": 3
        },
        "error": "Lamp with id 999 not found"
      }
    ],
    "skipped_config_ids": [],
    "not_found_config_ids": [],
    "message": "2개 Lamp 연동 생성 완료, 1개 실패"
  },
  "meta": {
    "timestamp": "2026-06-17T10:42:00.302543+09:00",
    "request_id": null
  }
}
```

> `data.message` 형식: `"N개 Lamp 연동 생성 완료"` + 실패가 1건 이상이면 `", N개 실패"` 절을 콤마로 연결한다. 전부 성공이면 후절은 생략된다.
> `data.skipped_config_ids` / `not_found_config_ids`: 등록 시에는 의미 없는 분류이나 해제 응답과의 envelope 일관성을 위해 빈 배열로 항상 포함된다.

| 응답 필드 | 타입 | 설명 |
|----------|------|------|
| mapping_id | integer | path parameter로 받은 EventMapping ID (메아리 응답) |
| created_ids | array[integer] | 실제로 생성된 EventMappingLamp row PK 목록 (요청 items 순서 보존) |
| failed_items | array[object] | 실패한 row 상세 (`index` / `item` / `error`) |
| failed_items[*].index | integer | 요청 `items` 내 0-based 인덱스 |
| failed_items[*].item | EventMappingLampCreate | 실패한 원본 입력 row (그대로 에코) |
| failed_items[*].error | string | 실패 사유 (예: `"Lamp with id 999 not found"`) |
| skipped_config_ids | array[integer] | (envelope 일관성용 빈 배열 — 등록 시 분류 없음) |
| not_found_config_ids | array[integer] | (envelope 일관성용 빈 배열 — 등록 시 분류 없음) |
| message | string | 처리 결과 요약 |

**Error Response** (404 Not Found — EventMapping 미존재):
```json
{
  "success": false,
  "message": "Event mapping with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

**Error Response** (422 Unprocessable Entity — 빈 배열/100건 초과/필드 검증 실패):
```json
{
  "success": false,
  "message": "items must not be empty",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": null
  }
}
```

| HTTP 코드 | 발생 조건 |
|-----------|----------|
| 200 OK | 정상 처리 (전체 성공/부분 성공/전체 row 실패 모두 200, 결과는 body `created_ids` / `failed_items`로 구분) |
| 404 Not Found | `mapping_id`에 해당하는 EventMapping 미존재 |
| 422 Unprocessable Entity | `items` 누락 / 빈 배열 / 100건 초과 / `lamp_id` 누락 / **Enum 값 오류** 등 Pydantic 검증 실패 (`color`/`buzzer_sound`/`light_mode` 모두 v4.5 PR-C에서 `EnumLampColor`/`EnumBuzzerSound`/`EnumLightMode` Pydantic 타입으로 전환되어 422 보장. 예: `color="Purple"` → `"Input should be 'Red', 'Orange', 'Green', 'Blue' or 'White'"`) |
| 500 Internal Server Error | DB 트랜잭션 오류 (Enum 제약 위반은 v4.5 PR-C 이후 422로 사전 차단됨) |

**ConfigChangeLog 연동**:
- 리소스 타입: `EnumConfigResourceType.EVENT_MAPPING_LAMP`
- 액션 타입: `EnumConfigActionType.CREATED`
- 요청당 **1건** 발행 (`after_state.config_ids`에 생성된 PK 리스트, `after_state.count`에 개수)
- `description`: `"EventMapping에 N개 Lamp 연동 일괄 생성 (bulk)"`
- `created_ids`가 비어 있으면(전체 row 실패) 미발행
- AuditLog는 EventMappingLamp 도메인 외 (`PRD_Audit_Log.md §2.2.2`에 따라 USER/USER_GROUP/USER_SESSION/PASSWORD 4종 한정)

**NATS SYNC 동작**:
- `event_mapping_lamps` 테이블의 statement-level 트리거(`trg_sync_eml_ins` + 통지 함수 `fn_notify_eml_stmt`)가 발화하여, 영향 받는 `event_mapping_id`당 **`SYNC_EVENT_MAPPING/UPDATED/{event_mapping_id}` 1건만 발행** (PostgreSQL 10+ `REFERENCING NEW TABLE`).
- 단건 N회 호출 시 발생하는 N건 발행 대비 80%+ 감소 (실측: 5건 일괄 등록 시 5건 → 1건).
- 단일 statement에 여러 `event_mapping_id`가 섞일 일은 없으나(path parameter로 고정), `SELECT DISTINCT event_mapping_id FROM new_rows`로 안전하게 1건 발행을 보장한다.

**변경 이력**:
- v4.3 (2026-06-17): 신규. 단건 생성 API(`7.5.3`)의 벌크 보완. `7.5.10`(벌크 해제)과 메서드/응답 envelope 대칭 구조. `7.3.9`(Camera) / `7.4.9`(Speaker) 벌크 등록과 동일 패턴 정렬 — Lamp 고유 per-row 부가 필드(`color/buzzer_time/buzzer_sound/light_mode`)만 보존.

---

#### 7.5.11 EventMappingLamp 벌크 해제 *(v4.3 신규)*

**Endpoint**: `DELETE /api/integrations/event-mappings/{mapping_id}/lamps`

여러 경광등 연동(EventMappingLamp row)을 한 번의 요청으로 일괄 해제합니다. 단건 삭제(`7.5.6`)의 N회 호출을 1회로 통합하여 매핑 마법사에서 다중 선택한 연동에 대한 라운드트립을 최소화하고, NATS `SYNC_EVENT_MAPPING` 메시지를 statement-level 트리거로 영향 받는 `event_mapping_id`당 1건만 발행하여 LampManager / GIS 등 다운스트림 캐시 무효화 폭주를 차단합니다. 멱등성(idempotent) 시맨틱이므로 동일 요청을 재호출해도 두 번째 호출은 모두 `skipped` / `not_found`로 분류되어 안전합니다.

**Request Example**:
```http
DELETE /api/integrations/event-mappings/10/lamps HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "config_ids": [701, 702, 703, 999]
}
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| mapping_id | integer | Y | EventMapping ID (해제 대상 매핑의 신뢰원) |

**Request Body**:
```json
{
  "config_ids": [701, 702, 703, 999]
}
```

| 필드 | 타입 | 필수 | 제약 | 설명 |
|------|------|------|------|------|
| config_ids | array[integer] | Y | 1 ≤ len ≤ 100, 중복 자동 제거 | 해제할 EventMappingLamp row PK 목록 |

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "2개 Lamp 연동 해제 완료, 1개 건너뜀, 1개 없음",
  "data": {
    "mapping_id": 10,
    "removed_config_ids": [701, 702],
    "skipped_config_ids": [703],
    "not_found_config_ids": [999],
    "message": "2개 Lamp 연동 해제 완료, 1개 건너뜀, 1개 없음"
  },
  "meta": {
    "timestamp": "2026-06-17T10:43:00.302543+09:00",
    "request_id": null
  }
}
```

> `data.message` 형식: `removed` / `skipped` / `not_found` 3분류 중 **개수가 0이 아닌 절만** 콤마로 연결됩니다. 예: skipped=0, not_found=0이면 `"3개 Lamp 연동 해제 완료"`만 표시.
> 동일 `config_ids` 재호출 시 1회차의 `removed`는 2회차에서 `not_found`(row 자체가 삭제됨)로 분류되어 결과적으로 멱등이다.

| 응답 필드 | 타입 | 설명 |
|----------|------|------|
| mapping_id | integer | path parameter로 받은 EventMapping ID (메아리 응답) |
| removed_config_ids | array[integer] | 실제 row가 삭제된 EventMappingLamp PK 목록 |
| skipped_config_ids | array[integer] | row는 DB에 존재하지만 `event_mapping_id`가 path와 불일치하여 처리하지 않은 ID (다른 매핑 소속 — 멱등성 보장) |
| not_found_config_ids | array[integer] | row 자체가 DB에 존재하지 않는 ID (404가 아니라 분류 응답) |
| message | string | 처리 결과 요약 |

**Error Response** (404 Not Found — EventMapping 미존재):
```json
{
  "success": false,
  "message": "Event mapping with id 999 not found",
  "error": {
    "code": "NOT_FOUND",
    "details": null
  }
}
```

**Error Response** (422 Unprocessable Entity — 빈 배열/100건 초과):
```json
{
  "success": false,
  "message": "config_ids must not be empty",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": null
  }
}
```

| HTTP 코드 | 발생 조건 |
|-----------|----------|
| 200 OK | 정상 처리 (전체/부분 해제, 전부 skipped/not_found 모두 200, 결과는 body 3분류로 구분) |
| 404 Not Found | `mapping_id`에 해당하는 EventMapping 미존재 |
| 422 Unprocessable Entity | `config_ids` 누락 / 빈 배열 / 100건 초과 / 타입 오류 |
| 500 Internal Server Error | DB 트랜잭션 오류 |

**ConfigChangeLog 연동**:
- 리소스 타입: `EnumConfigResourceType.EVENT_MAPPING_LAMP`
- 액션 타입: `EnumConfigActionType.DELETED`
- 요청당 **1건** 발행 (`before_state.config_ids`에 해제된 PK 리스트, `before_state.count`에 개수)
- `description`: `"EventMapping에서 N개 Lamp 연동 일괄 해제 (bulk)"`
- `removed_config_ids`가 비어 있으면(전부 skipped/not_found) 미발행
- AuditLog는 EventMappingLamp 도메인 외 (`PRD_Audit_Log.md §2.2.2`에 따라 USER/USER_GROUP/USER_SESSION/PASSWORD 4종 한정)

**NATS SYNC 동작**:
- `event_mapping_lamps` 테이블의 statement-level 트리거(`trg_sync_eml_del` + 통지 함수 `fn_notify_eml_stmt`)가 발화하여, 영향 받는 `event_mapping_id`당 **`SYNC_EVENT_MAPPING/UPDATED/{event_mapping_id}` 1건만 발행** (PostgreSQL 10+ `REFERENCING OLD TABLE`).
- `skipped` row(타 매핑 소속)는 트리거 발화에 포함되지 않으므로 통지에 영향이 없다.
- 등록(POST `/lamps/bulk`)도 동일 트리거 family로 1건/`event_mapping_id` 발행 — 단건 N회 호출의 N건 발행 대비 80%+ 감소.

**변경 이력**:
- v4.3 (2026-06-17): 신규. 단건 삭제 API(`7.5.6`)의 벌크 보완. `7.5.9`(벌크 등록)와 메서드/응답 envelope 대칭 구조. `7.3.10`(Camera) / `7.4.10`(Speaker) 벌크 해제와 동일 패턴 정렬 — DeviceGroup `5.6.9`(디바이스 벌크 해제)의 3분류 응답 시맨틱을 차용.

---

## 8. Server Monitoring API 설계

### 8.1 개요

서버 모니터링 API는 GOP 시스템을 구성하는 다양한 서버들의 상태를 관리하고 모니터링하기 위한 API입니다.

**주요 기능**:
- 서버 카테고리 관리 (10개 기본 카테고리)
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

#### 8.3.7 서버별 시스템 이벤트 조회 *(v3.9 신규)*

특정 서버에서 발생한 시스템 이벤트 목록을 조회합니다.

**Endpoint**: `GET /api/servers/{server_id}/system-events`

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| server_id | integer | Y | 서버 ID |

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| page | integer | N | 1 | 페이지 번호 |
| limit | integer | N | 50 | 페이지당 항목 수 |
| severity | string | N | - | 심각도 필터 (INFO, WARNING, ERROR, CRITICAL) |
| acknowledged | boolean | N | - | 확인 여부 필터 |

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "System events retrieved successfully",
  "data": {
    "items": [
      {
        "id": 1,
        "type_event": "threshold_warning",
        "severity": "WARNING",
        "source": "server_metrics",
        "message": "CPU usage exceeded 80%",
        "acknowledged": false,
        "server_description": "VMS Server #1",
        "created_at": "2026-02-13T10:00:00Z",
        "updated_at": "2026-02-13T10:00:00Z"
      }
    ],
    "total": 1
  },
  "pagination": {
    "page": 1,
    "limit": 50,
    "total_pages": 1
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

시스템 초기화 시 다음 10개의 기본 서버 카테고리가 자동 생성됩니다 (카테고리는 유형별 idempotent — 매 기동 시 없는 유형만 추가):

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
| 10 | 프록시 서버 | PROXY | PidsProxy 서버 (장비 등록/운용 관문) |

**필수 서버 유형 보장 (v6.3 후속 `proxy_mandatory_seed`)**: `PROXY / VMS / NVR_API / BROKER` 4종은 **유형 기준 보장** 대상 — 시스템 기동 시 해당 유형에 서버 인스턴스가 **하나도 없으면** 기본 인스턴스를 자동 생성한다. 이미 해당 유형 서버가 (사용자 등록분 포함) 존재하면 아무것도 만들지 않는다(중복 방지). 그 외 유형의 기본 인스턴스는 `servers` 테이블이 비어 있을 때만 최초 1회 시드된다.

---

### 8.6 Server Metrics API

서버의 리소스 사용량을 시계열로 기록하고 조회합니다.

> **collected_at 타임존 (v6.3 후속 `server_metrics_tz_fix`)**: `collected_at` 은 tz-aware(예: `2026-07-31T10:00:00+09:00`) 또는 naive 둘 다 허용하며, 서버가 **KST 벽시계 naive** 로 정규화해 저장한다(응답은 `+09:00` 표기). 이전엔 aware 값 전송 시 500 이었다.

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

**Response (200 OK)** (v4.6 정정 — 코드 `ServerMetricsLatestResponse` 구조에 맞춤):
```json
{
  "success": true,
  "message": "Latest server metrics retrieved successfully",
  "data": {
    "server_id": 1,
    "server_name": "VMS-Server-01",
    "latest_metrics": {
      "id": 10,
      "server_id": 1,
      "cpu_usage": 45.5,
      "ram_usage": 62.0,
      "collected_at": "2026-01-15T10:30:00.000000"
    }
  }
}
```
- 메트릭 미수집 시: `latest_metrics: null` (200 응답 유지)
- `threshold_config`는 서버 카테고리/서버 자체 응답(`§8.3.x`)에 포함됨 — 본 엔드포인트 응답에서는 제외

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
>
> **⚠ v6.3 후속 `proxy_settings_typed`**: 이 API(GET/PATCH/PUT)는 **PROXY 유형 서버 전용**입니다. 대상 서버의 카테고리가 PROXY 가 아니면 **404** 를 반환하며 설정을 lazy-create 하지 않습니다. (기존: 모든 서버 유형 허용 → **계약 변경**)

#### 8.8.1 프록시 설정 조회

```http
GET /api/servers/{server_id}/proxy-settings
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| server_id | integer | Y | Server ID |

> **Note**: (PROXY 서버에 한해) 설정이 존재하지 않으면 기본값으로 자동 생성합니다 (Lazy 생성). 비-PROXY 서버는 **404** (lazy-create 하지 않음).

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

#### 8.8.2 프록시 설정 수정 (부분)

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

#### 8.8.3 프록시 설정 수정 (전체)

```http
PUT /api/servers/{server_id}/proxy-settings
```

**Path Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| server_id | integer | Y | Server ID |

> **Note**: PUT은 전체 교체이므로 **모든 필드를 반드시 포함**합니다. 설정이 존재하지 않으면 Upsert (자동 생성).

**Request Example**:
```http
PUT /api/servers/1/proxy-settings HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
Accept: application/json

{
  "operation_mode": "REGISTER",
  "windy_mode": "wind2"
}
```

**Request Body** (전체 교체 - 모든 필드 필수):

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| operation_mode | string | **Y** | 운용 모드 (EnumOperationMode) |
| windy_mode | string | **Y** | 풍량 모드 (EnumWindyMode) |

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Proxy settings replaced successfully",
  "data": {
    "id": 1,
    "server_id": 1,
    "operation_mode": "REGISTER",
    "windy_mode": "wind2",
    "created_at": "2026-02-06T12:00:00.000Z",
    "updated_at": "2026-02-09T14:30:00.150Z"
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
| GET | `/api/auth/me/permissions` | 유효권한 스냅샷(grant 병합) *(v5.2)* | 9.2.6 |

#### 9.2.2 POST `/api/auth/login`

**Request Body**:
```json
{
  "login_id": "<your_login_id>",
  "password": "<your_password>"
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
    "session_id": "42",
    "user": {
      "id": 1,
      "login_id": "operator01",
      "name": "홍길동",
      "email": "operator01@gop.mil.kr",
      "department": "경계부대 1중대",
      "role": "USER",
      "group_id": 1,
      "permissions": {
        "modules": {"events": {"view": true, "edit": true}},
        "device_groups": [1, 2, 3]
      }
    }
  }
}
```

> **`session_id` (v5.2, Force-Logout FR-SVF-01)**: JWT `sid` 클레임(=UserSession.id)과 동일한 불변 세션 식별자. 클라는 이 값을 보관하여 강제 로그아웃 매칭(per-session NATS revoke subject)·세션 관리에 사용한다. refresh 시 **sid는 고정**되고 jti만 회전한다. 상세 계약: `docs/prds/CONTRACT_GOP_Server_v5.2.md`.

**Error — 로그인 실패 / 계정 잠금 (v6.3 후속 `lockout_policy`)**:

- **`401`** 비밀번호 불일치 — `lockout_threshold>0` 이면 잔여 횟수 안내 + 구조화 `error.details`:
  ```json
  {
    "success": false,
    "error": {
      "code": "UNAUTHORIZED",
      "message": "로그인 정보가 올바르지 않습니다. (5회 중 2회 실패, 3회 남음)",
      "details": { "failed_count": 2, "threshold": 5, "remaining": 3, "locked": false }
    }
  }
  ```
  - 이번 실패로 임계 도달 시 → `message`="실패 N회 초과로 계정이 잠겼습니다. 약 M분 후 자동 해제됩니다.", `details.locked=true`, `remaining=0`.
  - **미존재 계정**은 카운트 미노출(계정 열거 방지) — `message="Incorrect login_id or password"`, `details=null`. **틀린 이유(id/pw)는 구분 노출하지 않음.**
  - `lockout_threshold=0`(잠금 비활성)이면 카운트 없이 일반 메시지.
- **`403`** 계정 잠김 — 잠긴 계정 재로그인. `lockout_duration_minutes>0` 이면 `message="계정이 잠겼습니다. 약 M분 후 자동 해제됩니다."`. **duration 경과 후 로그인 시도 시 자동 해제**(실패카운트 리셋)되어 통과. 관리자 `POST /api/users/{id}/unlock` 은 즉시 해제(카운트 리셋 동반).
- **`403`** 비활성 계정 / **`429`** IP rate limit(300s/10회 초과, `Retry-After`).
- 잠금 정책 파라미터(`lockout_threshold`·`lockout_duration_minutes`)는 §9.8 세션 설정에서 런타임 편집.
- **감사**: 자동잠금·자동해제는 `audit_logs`에 `USER_LOCKED`/`USER_UNLOCKED`(행위자 `(system)`/`시스템(자동)`, 대상=해당 계정)로 기록되어 `GET /api/audit-logs`·정형 리포트 `SYSTEM_AUDIT_GRID`에 노출된다(`v6.3-audit_auto_lock`). 관리자 수동 lock/unlock(`USER_LOCKED`/`USER_UNLOCKED`, 행위자=관리자)과 동일 액션타입·다른 행위자로 구분.

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

> **세션 무효화 (v5.2, Force-Logout)**: logout 은 현재 세션의 **access + refresh 패밀리 jti를 모두 블랙리스트**에 등록한다(발급된 토큰이 exp까지 통과하던 구멍 차단). 이후 해당 토큰으로 보호 자원 접근 시 **401 `error.code=SESSION_REVOKED`** — 403(권한부족)과 구분되며, 클라는 즉시 재로그인 플로우로 전환한다(재시도 금지). 관리자 강제 로그아웃(`DELETE /api/user-sessions/{id}`·`/user/{user_id}`)도 동일하게 대상 세션 jti를 블랙리스트한다.

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
    "token_type": "bearer",
    "session_id": "42"
  }
}
```

> **(v5.2)** refresh 시 `session_id`(=`sid`)는 **그대로 승계**되고 access·refresh의 `jti`만 회전한다. 이전 refresh 토큰의 jti는 회전과 함께 블랙리스트된다(재사용 차단).

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
  "role": "USER",
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

#### 9.2.6 GET `/api/auth/me/permissions` *(v5.2)*

현재 사용자의 **유효권한 스냅샷**을 조회한다(인증 필요). 유효권한 = **배정 그룹(`group_id`) 매트릭스 ∪ 현재 유효 grant 매트릭스**(§9.9). role 은 ADMIN만 특권(bypass), 비-ADMIN은 라벨 — 권한 원천은 배정 그룹(ADR_Permission_Model_v5.2). 클라(Dotnet.Monitoring)가 grant 만료/변경으로 stale 된 권한을 재평가하는 경로. 로그인 응답 `data.user.permissions` 와 동일 계산.

**Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "modules": {
      "events": {"view": true, "edit": true, "delete": false, "control": true},
      "cameras": {"view": true, "edit": false, "delete": false, "control": true}
    },
    "device_groups": [1, 2, 3],
    "valid_until": "2026-07-01T14:00:00+09:00",
    "server_time": "2026-06-30T12:00:00+09:00"
  }
}
```
| 필드 | 설명 |
|------|------|
| modules | 모듈별 권한(view/edit/delete/control), 등급 ∪ grant 합집합(OR) |
| device_groups | 접근 가능 디바이스 그룹 ID(합집합) |
| valid_until | 활성 grant 중 **가장 임박한 만료**(KST, null=상시) — 클라 캐시 만료시점 |
| server_time | 서버 현재 시각(KST) — 폐쇄망 클라-서버 시계 편차 보정 |

> 클라 패턴: 로그인 시 permissions+`valid_until` 캐시 → `valid_until` 도달 또는 NATS `permissions_changed`(per-user subject) 수신 시 재조회. **실동작은 서버 응답(403)이 권위**, UI 게이팅은 보조.

### 9.3 User API

#### 9.3.1 Endpoint 목록

| Method | Endpoint | 설명 | 권한 |
|--------|----------|------|------|
| GET | `/api/users` | 사용자 목록 조회 | **ADMIN** |
| GET | `/api/users/{id}` | 사용자 상세 조회 | **ADMIN** |
| POST | `/api/users` | 사용자 생성 | **ADMIN** |
| PUT | `/api/users/{id}` | 사용자 수정 | **ADMIN** |
| DELETE | `/api/users/{id}` | 사용자 삭제 | **ADMIN** |
| POST | `/api/users/{id}/lock` | 계정 잠금 | **ADMIN** |
| POST | `/api/users/{id}/unlock` | 계정 잠금 해제 | **ADMIN** |
| POST | `/api/users/{id}/reset-password` | 비밀번호 초기화 | **ADMIN** |
| GET | `/api/users/me` | 내 정보 조회 | 본인(인증) |
| PUT | `/api/users/me` | 내 정보 수정 | 본인(인증) |
| PUT | `/api/users/me/password` | 내 비밀번호 변경 | 본인(인증) |
| POST | `/api/users/me/photo` | 본인 프로필 사진 업로드 (multipart) | 본인(인증) |
| DELETE | `/api/users/me/photo` | 본인 프로필 사진 삭제 (→ default 복귀) | 본인(인증) |
| GET | `/api/users/photo/{file_name}` | 프로필 사진 다운로드 | 인증 불필요 |
| POST | `/api/users/{id}/photo` | **관리자**: 대상 계정 프로필 사진 업로드 (multipart) | users:edit (+base-ADMIN 상승가드) |
| DELETE | `/api/users/{id}/photo` | **관리자**: 대상 계정 프로필 사진 삭제 (→ default 복귀) | users:edit (+base-ADMIN 상승가드) |

> **권한(RBAC) (v6.0-rbac_matrix_gate, 2026-07-07 — v4.12 정책 대체)**: 계정 관리 엔드포인트(목록/상세/생성/수정/삭제/lock/unlock/reset-password)는 **권한 매트릭스**(`require_perm("users", view|edit|delete|control)`, `app/routers/auth.py`)로 게이트한다. **유효권한 = 배정 그룹(`group_id`) 매트릭스 ∪ 현재 유효 grant 매트릭스**. `role=ADMIN` 만 전권 bypass, 비-ADMIN(USER)은 매트릭스로 동작하며 grant 로 한시 승격되면 그 그룹 권한으로 호출 가능하고 스케쥴 만료 시 원래 등급으로 복귀한다. 권한 미보유 시 **403**(`Insufficient permission: requires users:{verb}`).
> **상승 가드(한시성 복귀 보장)**: grant 로 승격된 USER 가 영구 승격을 자가 생성하는 경로는 base-ADMIN(`role==ADMIN`) 전용으로 잠근다 — ① `role`/`group_id` 변경(create/update), ② `POST /api/users/{id}/grants` 부여·회수, ③ 그룹 permissions 매트릭스 편집, ④ `role=ADMIN` **대상** 계정 변경(pw초기화/삭제/잠금/수정). 비-ADMIN 이 이를 시도하면 **403**(`Only ADMIN role can ...`). 이전 v4.12 는 이 8종을 `require_admin`(role 문자열만) 으로 막아 grant 매트릭스를 무시했으나, ADR_Permission_Model_v5.2 모델(role=ADMIN=bypass / USER=매트릭스)에 코드를 정합함.
> 본인 자원(`/me`·`/me/password`·`/me/photo`)은 인증된 본인 누구나(self-service, `role` 은 SelfUpdate 스키마가 422 거부), `GET /api/users/photo/{file_name}`은 인증 불필요(파일명 uuid). **서버측 RBAC가 권위 집행 지점**(클라 UI 게이팅은 보조·우회 가능).

> **프로필 사진 (v4.x, 2026-06-26)**: `POST /api/users/me/photo` 는 `multipart/form-data`(field `file`, image/jpeg·png·webp·gif, ≤5MB)를 받아 **호스트 바인드 마운트 `./data/profiles/`**(`PROFILE_STORAGE_PATH`)에 `{user_id}_{uuid8}.{ext}`로 저장하고, `account_users.photo_url`을 **절대 API URL**(`{base}/api/users/photo/{name}`)로 갱신한 뒤 갱신된 사용자를 반환한다. 이미지 바이트는 **DB가 아니라 파일시스템**(썸네일과 동일 패턴), DB에는 photo_url(VARCHAR500)만. `GET /api/users/photo/{file_name}` 는 `FileResponse`로 바이너리 반환(인증 불필요 — 파일명이 uuid라 비공개성 확보, 경로 traversal 차단). 컨테이너 재빌드/재생성에도 `./data`라 **영속**. **(v6.3-profile_photo_crud, 2026-07-13)** `DELETE /api/users/me/photo` 로 본인 사진 삭제 시 파일을 제거하고 `photo_url=null` 로 되돌린다(응답 스키마가 default `/api/users/photo/default.png` 로 채워 **default 아바타로 자동 복귀**, 사진 없어도 200 idempotent). 업로드는 `content_type`(클라 위조 가능) 대신 **실제 이미지 바이트(Pillow magic-byte)** 로 포맷을 판별하고, **재업로드 시 옛 파일을 삭제**해 orphan(PII) 누적을 막는다. `photo_url` 검증기(`AccountUserSelfUpdate`, `PUT /me`)는 `http(s)://` 또는 실제 서빙 경로 **`/api/users/photo/`** 로 시작만 허용 — 종전 허용값 `/static/profiles/` 는 실존하지 않아(StaticFiles 미마운트) 서버가 채운 default 를 클라가 되받을 때 **422** 나던 것을 정정(`javascript:`/`data:` 등 XSS 스킴은 계속 차단). **(v6.3-admin_photo_upload, 2026-07-21)** 관리자가 **타 계정** 사진을 설정하는 `POST /api/users/{id}/photo`·`DELETE /api/users/{id}/photo` 신설(`users:edit` + base-ADMIN 상승가드 — 비-ADMIN 은 ADMIN 대상 변경 시 403). 저장·magic-byte 검증·orphan 정리는 본인 경로와 동일 헬퍼(`_save_profile_photo`)를 대상 `{id}` 로 재사용하고, 감사에 **행위자(관리자) ≠ 대상**(`USER_PHOTO_CHANGED`/`USER_PHOTO_DELETED`)을 분리 기록한다. 종전엔 관리자용 `{id}` 경로가 없어 클라가 본인 경로(`/me/photo`)를 타 계정 편집에 재사용 → 토큰 소유자(관리자) 사진이 오염되던 사고(2026-07-13)의 서버측 근본 해소.

#### 9.3.2 GET `/api/users`

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| page | int | 아니오 | 페이지 번호 (기본값: 1) |
| limit | int | 아니오 | 페이지당 항목 수 (기본값: 100, 최대: 100) |
| role | string | 아니오 | 역할 필터 (ADMIN, USER) |
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
      "role": "USER",
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
  "role": "USER",
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
    "role": "USER",
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
| POST | `/api/user-groups/{id}/permissions` | 그룹 권한 변경 (ADMIN 전용, v5.0 신규) |

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

#### 9.4.7 POST `/api/user-groups/{group_id}/permissions` — 그룹 권한 변경 (ADMIN 전용, v5.0 신규)

일반 `PUT /api/user-groups/{id}`는 v4.8 Phase 12-7a 정책에 따라 `permissions` 필드 수정을 영구 차단한다(요청에 포함되면 무시 또는 422). 권한 변경은 보안 핵심 작업이므로 **전용 endpoint로 분리**하고, FastAPI 의존성 `Depends(require_admin)`을 endpoint 레벨에 강제하여 **ADMIN 역할만 호출 가능**하도록 인가를 일관 적용한다.

요청 본문은 `PermissionsSchema`(strict input)로 검증한다. `modules` 딕셔너리는 8종 모듈 키와 4 verb(StrictBool) 매트릭스로 구성되며, `extra='forbid'`가 적용되어 미정의 모듈/verb는 자동으로 422를 반환한다. 권한은 **전체 교체** 방식으로 적용되고(부분 병합 아님), JSONB 컬럼 호환을 위해 `model_dump(mode="json", exclude_none=True)`로 직렬화한 뒤 저장한다.

**Path Parameters**

| 필드 | 타입 | 설명 |
|------|------|------|
| `group_id` | integer | 권한을 변경할 그룹 ID (PK) |

**Request Body** (`PermissionsSchema`)

```json
{
  "modules": {
    "devices":  { "view": true, "edit": true,  "delete": false, "control": false },
    "events":   { "view": true, "edit": false, "delete": false, "control": false },
    "cameras":  { "view": true, "edit": true,  "delete": false, "control": true  }
  },
  "device_groups": [1, 5, 7]
}
```

- `modules`: `Dict[EnumPermissionModule, ModulePermission]`
  - **EnumPermissionModule (8종)**: `devices`, `events`, `reports`, `cameras`, `users`, `user_groups`, `audit_logs`, `servers`
  - **ModulePermission (4 verb, StrictBool)**: `view`, `edit`, `delete`, `control`
  - `extra='forbid'` — 미정의 모듈 키(예: `"foo"`) 또는 미정의 verb(예: `"manage"`)는 422 반환
  - **StrictBool** — `"yes"`, `1`, `"true"` 같은 truthy 값은 모두 422 (불리언 외 타입 거부)
- `device_groups`: `List[int]` (선택) — 그룹이 접근 가능한 디바이스 그룹 ID 목록

**Response (200 OK)**

```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "운영팀",
    "description": "기지 운영팀",
    "permissions": {
      "modules": {
        "devices":  { "view": true, "edit": true,  "delete": false, "control": false },
        "events":   { "view": true, "edit": false, "delete": false, "control": false },
        "cameras":  { "view": true, "edit": true,  "delete": false, "control": true  }
      },
      "device_groups": [1, 5, 7]
    },
    "user_count": 3,
    "created_at": "2026-06-19T10:03:44+09:00",
    "updated_at": "2026-06-29T10:23:29+09:00"
  }
}
```

**Error Responses**

| HTTP | 사유 |
|------|------|
| 403 | ADMIN 아님 (`require_admin` 실패) — `{"code":"FORBIDDEN","message":"Insufficient role"}` |
| 404 | 그룹 없음 — `{"code":"NOT_FOUND","message":"User group not found"}` |
| 422 | 스키마 위반 — 미정의 모듈/verb, StrictBool truthy 값, 누락 필드 등 |

**감사 로그**

- `action_type`: `PERMISSION_CHANGED`
- `resource_type`: `USER_GROUP`
- `resource_id`: `group.id`
- 변경 전/후 스냅샷(`before_perms`, `after_perms`)을 비교하여 `changes` 필드에 diff 저장
- append-only 트리거 적용 (UPDATE/DELETE 차단, v51.1 FK 익명화 예외만 허용)

> **NOTE** — JSONB 직렬화는 `permissions = permissions.model_dump(mode="json", exclude_none=True)`로 수행하며 **전체 교체** 방식이다. 부분 병합(merge)은 지원하지 않으므로, 클라이언트는 항상 완전한 권한 매트릭스를 송신해야 한다.

**구현 위치**

- `app/routers/user_groups.py:270` — POST endpoint (`dependencies=[Depends(require_admin)]`)
- `app/schemas/user.py:46` — `PermissionsSchema` (`modules` + `device_groups`, `extra='forbid'`)
- `app/schemas/user.py:31` — `ModulePermission` (4 verb StrictBool)
- `app/utils/enums.py:779` — `EnumPermissionModule` (8종)
- `app/utils/enums.py:791` — `EnumPermissionVerb` (4 verb)
- `app/routers/auth.py` — `require_admin = require_role(['ADMIN'])`

**Swagger 노출**

- `operationId`: `update_user_group_permissions`
- Request schema: `#/components/schemas/PermissionsSchema`
- Tag: `user-groups`

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
| GET | `/api/audit-logs` | 감사 로그 목록 조회 | ADMIN 또는 `audit_logs:view` |
| GET | `/api/audit-logs/{id}` | 감사 로그 상세 조회 | ADMIN 또는 `audit_logs:view` |

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
          "role": "USER"
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

> **NOTE (v51 hardening)**: 응답의 `action_type` / `resource_type` 는 **문자열(str)** 이다.
> 권장 값은 각각 `EnumAuditActionType` / `EnumAuditResourceType` 멤버이나, `audit_logs` 는
> append-only(UPDATE/DELETE 차단 — §7 Phase 12-7f)라 과거 비-enum 값(예: 테스트 `TEST_INS`/`TEST`)이
> 영구 잔존할 수 있다. strict enum 이면 목록 직렬화가 500 되므로 응답 스키마를 str(tolerant)로 완화했다.
> 생성 측 `AuditLogCreate` 도 동일하게 str — 응답/생성 정합.

> **NOTE (v51.1, 2026-06-26)**: 사용자 hard-delete(`DELETE /api/users/{id}`) 시 `audit_logs.actor_id` /
> `user_login_logs.user_id` / `config_change_logs.actor_id` FK가 `ON DELETE SET NULL`(=UPDATE)로 익명화된다.
> append-only 트리거(`fn_block_audit_modification`)는 **이 FK 익명화 UPDATE(링크 컬럼만 NULL, 그 외 불변)만 허용**하고
> 내용 변경·행 삭제는 계속 차단한다. (이전엔 이 UPDATE까지 막아 이력 있는 사용자 삭제가 500이던 버그 수정.)

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
      "before": {"role": "USER"},
      "after": {"role": "ADMIN"}
    },
    "description": "역할 변경: USER → ADMIN",
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
| GET | `/api/config-change-logs` | 설정 변경 로그 목록 조회 | ADMIN 또는 `audit_logs:view` |
| GET | `/api/config-change-logs/{id}` | 설정 변경 로그 상세 조회 | ADMIN 또는 `audit_logs:view` |

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

### 9.8 Session Settings API *(v5.2 신규)*

세션/인증 정책 **런타임 관리** API. `app_settings` 테이블에 저장되며 DB가 권위(.env는 최초 1회 기본값). 인가는 **`setup_system` 매트릭스**(`require_perm("setup_system", view|edit)`) — `role=ADMIN` bypass, 비-ADMIN 은 배정 그룹/grant 의 `setup_system` 권한 보유 시 호출 가능(v6.0-rbac_matrix_gate, 2026-07-07; 이전 `require_admin`). 참조 PRD: `PRD_GOP_Server_Session_Settings.md`.

#### 9.8.1 Endpoint 목록

| Method | Endpoint | 설명 | 인가 | 섹션 |
|--------|----------|------|------|------|
| GET | `/api/settings/session` | 세션/인증 정책 조회 | ADMIN | 9.8.2 |
| PUT | `/api/settings/session` | 세션/인증 정책 변경(부분) | ADMIN | 9.8.3 |

#### 9.8.2 GET `/api/settings/session`

**Response (200 OK)**:
```json
{
  "success": true,
  "data": {
    "session_timeout_hours": 24,
    "refresh_expiration_days": 7,
    "lockout_threshold": 5,
    "lockout_duration_minutes": 30,
    "session_enabled": true,
    "auth_mode": "public",
    "jwt_algorithm": "HS256",
    "session_concurrency_policy": "evict_all",
    "max_concurrent_sessions": 0,
    "session_self_replace_enabled": false,
    "session_history_retention_days": 0,
    "login_anomaly_event_enabled": false
  }
}
```

| 필드 | 타입 | 편집 | 제약 |
|------|------|------|------|
| session_timeout_hours | int | ✅ | 1 ~ 168 |
| refresh_expiration_days | int | ✅ | 1 ~ 90 |
| lockout_threshold | int | ✅ | **0(비활성) 또는 3 ~ 20** (1~2 금지) |
| lockout_duration_minutes | int | ✅ | **0(자동해제 없음=영구) 또는 1 ~ 1440**(분). 잠금 후 이 시간 경과 뒤 로그인 시도 시 자동 해제(+실패카운트 리셋) |
| session_enabled | bool | ✅ | — |
| auth_mode | string | ❌ 읽기전용 | 배포(.env) 전용 |
| jwt_algorithm | string | ❌ 읽기전용 | 배포 전용 |
| session_concurrency_policy | string | ✅ | `evict_all`(기본, 단일세션 강제) 또는 `allow`(계정 다중세션 공존). ★기본=현행 동작 |
| max_concurrent_sessions | int | ✅ | 0(무제한) ~ 100. `allow`에서 초과 시 최오래된 세션부터 evict |
| session_self_replace_enabled | bool | ✅ | 기본 false. `allow`+true 시 **동일 client_id** 재로그인만 자기 세션 교체(그 외 공존) |
| session_history_retention_days | int | ✅ | 0(무동작) ~ 3650. >0이면 sweep 시 오래된 비활성 세션 이력 DELETE |
| login_anomaly_event_enabled | bool | ✅ | 기본 false. (예약 — 신규 IP/UA 로그인 이상탐지 이벤트, 배선 후속) |

> `jwt_secret`은 **절대 응답에 노출되지 않는다**(NFR-SVS-03).

#### 9.8.3 PUT `/api/settings/session`

편집 가능 필드의 **부분집합만** 수용(미지정 필드 불변). 변경분은 `ConfigChangeLog` 감사 + 캐시 무효화 + 런타임 만료/잠금 즉시 반영.

**Request Body** (예: 일부만):
```json
{
  "session_timeout_hours": 8,
  "lockout_threshold": 5
}
```

**Response (200 OK)**: GET과 동일한 전체 스냅샷(`data`).

**Error**:
- `422` — 경계 위반. 특히 `lockout_threshold`가 0 또는 3~20 외(예: 1, 2) → 422. `session_concurrency_policy`가 `evict_all`/`allow` 외, `max_concurrent_sessions` 0~100 외, `session_history_retention_days` 0~3650 외 → 422.
- `401`/`403` — 미인증 / 비-ADMIN.

> **동시세션 정책(v6.3-session_concurrency)**: 기본 `evict_all`은 로그인 시 같은 계정의 기존 세션을 전부 강제폐기(단일세션). `allow`로 전환하면 계정 다중세션 공존(SSO 대비) — 신규 로그인부터 적용, 기존 세션 유지. 로그인 시 클라이언트는 `X-Client-Id` 헤더(또는 `client_id` 바디 필드, 1~64자 `[A-Za-z0-9._:-]`)로 자신을 식별하며, `session_self_replace_enabled=true`일 때 **동일 client_id** 재로그인만 자기 세션을 교체한다. 폐기된 토큰으로의 요청은 `401 SESSION_REVOKED`(`details.reason`=`DUPLICATE` 등)로 통일 응답.

---

### 9.9 권한그룹 부여(Grant) API *(v5.2 신규)*

권한그룹(UserGroup)을 사용자에게 **기간을 정해 부여**한다(상시=`valid_until` 생략, 한시=만료 지정). 유효권한 = **배정 그룹(`group_id`) 매트릭스 ∪ 현재 유효 grant 매트릭스**(요청시점 계산이 권위, sweep 미실행에도 만료 차단). role 은 ADMIN만 특권(bypass), 기능권한은 배정 그룹에서 — `name==role` 자동해석 폐기(ADR_Permission_Model_v5.2). 참조 PRD: `PRD_Permission_Group_Scheduling.md`. ⚠ 집행은 휴면 RBAC와 함께 `AUTH_MODE=token` 플립 시 활성(부여/조회/회수 관리 API는 AUTH_MODE 무관 즉시 동작).

#### 9.9.1 Endpoint 목록

| Method | Endpoint | 설명 | 인가 | 섹션 |
|--------|----------|------|------|------|
| POST | `/api/users/{user_id}/grants` | 그룹 부여 | **base-ADMIN 전용** | 9.9.2 |
| GET | `/api/users/{user_id}/grants` | 부여 목록(+status) | users:view | 9.9.3 |
| DELETE | `/api/grants/{grant_id}` | 부여 회수(soft) | **base-ADMIN 전용** | 9.9.4 |
| GET | `/api/grants` | 전체 부여 목록(관리자 대시보드) *(v5.4 신규)* | users:view | 9.9.5 |

> **인가(v6.0-rbac_matrix_gate, 2026-07-07)**: 조회(GET)는 `users:view` 매트릭스로 개방(ADMIN bypass). **부여(POST)·회수(DELETE)는 승격 메커니즘 자체이므로 `role=ADMIN` 전용 유지**(`require_admin`) — grant 로 한시 승격된 USER 가 자기에게 grant 를 자가발급해 영구 승격하는 경로 차단. 이전엔 4종 모두 `require_admin`.

> 사용자 본인 유효권한 재조회는 §9.2.6 `GET /api/auth/me/permissions`.

#### 9.9.2 POST `/api/users/{user_id}/grants`

**Request Body** (`GrantCreate`, extra 금지):
```json
{
  "group_id": 3,
  "valid_from": "2026-06-30T13:00:00+09:00",
  "valid_until": "2026-07-01T14:00:00+09:00"
}
```
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| group_id | int | Y | 부여할 권한그룹 ID |
| valid_from | datetime(KST) | Y | 유효 시작 일시 |
| valid_until | datetime(KST) | N | 만료 일시. **생략/null = 상시(무기한)** |

**Response (201 Created)** — `data`(`GrantResponse`):
```json
{
  "success": true,
  "data": {
    "id": 12, "user_id": 7, "group_id": 3, "group_name": "유지보수팀",
    "valid_from": "2026-06-30T13:00:00+09:00",
    "valid_until": "2026-07-01T14:00:00+09:00",
    "is_active": true, "status": "ACTIVE",
    "granted_by": 1, "revoked_at": null,
    "created_at": "2026-06-30T12:00:00+09:00"
  }
}
```
- **status**(파생): `ACTIVE`(유효) / `PENDING`(now<valid_from) / `EXPIRED`(valid_until≤now) / `REVOKED`(회수됨). 우선순위 REVOKED>PENDING>EXPIRED>ACTIVE.
- **is_active**: sweep 비정규화 표시 플래그 — **인가 권위는 status(요청시점)**.
- **Error**: `404`(user/group 없음) / `422`(`valid_until ≤ valid_from` 또는 과거 `valid_until`) / `401`·`403`.

#### 9.9.3 GET `/api/users/{user_id}/grants`

해당 사용자의 모든 부여를 `status` 파생값과 함께 배열로 반환(ADMIN). `data`: `GrantResponse[]`.

#### 9.9.4 DELETE `/api/grants/{grant_id}`

부여 **회수**(물리삭제 아님 — `revoked_at` 기록, 감사 `GRANT_REVOKED`). 회수 즉시 유효권한에서 제외(요청시점 판정). `data: null`.

---

## 10. Report API 설계 (v3.3 신규)

> **PRD 참조**: PRD_Report_System.md
> 보고서 템플릿 관리, 보고서 생성 및 다운로드 API


#### 9.9.5 GET `/api/grants` — 전체 부여 목록 (관리자 대시보드) *(v5.4 신규)*

REQ: `docs/REQ_Server_Grants_ListAll.md` (.NET GIS 클라 요청)

전체 부여 현황을 관리자 대시보드에서 한눈에 볼 수 있도록 신설. 이전엔 클라가 계정 N개 순회하며 `GET /api/users/{id}/grants`를 N회 호출(N+1 폭증 위험). 본 endpoint로 단일 조회 + 페이지네이션 + 필터 지원.

**Path**: `GET /api/grants` + `Depends(require_perm_async("users", "view"))` (v6.0-rbac_matrix_gate — ADMIN bypass 또는 `users:view` 매트릭스 보유)

**쿼리 파라미터** (모두 선택):

| 파라미터 | 타입 | 기본 | 설명 |
|---|---|---|---|
| page | int >=1 | 1 | 페이지 번호 |
| size | int 1~100 | 20 | 페이지 크기 |
| user_id | int? | - | 계정 필터 |
| group_id | int? | - | 그룹 필터 |
| status | str? | - | ACTIVE/PENDING/EXPIRED/REVOKED |
| active_only | bool | false | is_active=true 만 |

**Response 200**:

```json
{
  "success": true,
  "data": [{
    "id": 4, "user_id": 84,
    "user_login_id": "gop_maint", "user_name": "GOP MAINTAINER",
    "group_id": 11, "group_name": "Preset - 유지보수자",
    "valid_from": "2026-07-02T23:31:11+09:00",
    "valid_until": "2026-07-03T00:00:00+09:00",
    "is_active": false, "status": "EXPIRED",
    "granted_by": 1, "revoked_at": null,
    "created_at": "2026-07-02T23:31:28+09:00"
  }],
  "total": 4
}
```

**Error**: 401 (무인증) / 403 (require_admin) / 422 (page<1, size 범위, status 값)

**v5.4 GrantResponse 보강**: `user_login_id` + `user_name` 필드 추가 — 클라 GrantManagementPanel UserLabel 태깅 로직 제거 가능.

**정렬**: `created_at` 내림차순 (최신 부여 우선).

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
| GET | `/api/reports/status` | 보고서 엔진 Busy/Ready 상태 (read-only) |
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

PDF 파일을 직접 다운로드합니다 — JSON envelope 아님, **PDF 바이너리 스트림** 반환.

**Response (200 OK)** (COMPLETED 상태) — v4.6 정정:
- Content-Type: `application/pdf`
- Content-Disposition: `attachment; filename="report_{id}_{date}.pdf"`
- Body: PDF 바이너리 스트림 (`%PDF-1.4...`)
- 클라이언트(매니저)는 응답을 파일로 저장하거나 PDF 뷰어로 직접 처리. JSON 파싱 시도 시 `JSONDecodeError` 발생.

> 본 엔드포인트는 §3.x 표준 `ApiResponse` envelope의 공식 예외 (파일/렌더링 엔드포인트). HTML preview (`/preview-page`)도 동일 예외.

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

#### 10.4.6 GET `/api/reports/status`

보고서 엔진의 Busy/Ready 상태를 조회합니다 (read-only). 정형 보고서는 전체 페이지네이션으로 Chromium 렌더가 무거워 비동기 생성되므로, 클라이언트는 generation id 없이 본 엔드포인트를 polling 하여 진행 여부를 판단할 수 있습니다.

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Report engine status retrieved successfully",
  "data": {
    "busy": false,
    "ready": true,
    "in_progress_count": 0,
    "in_progress": [],
    "last_completed": {
      "id": 4,
      "title": "2026년 6월 운영 보고서",
      "completed_at": "2026-06-30T17:42:00+09:00",
      "pdf_download_url": "/api/reports/generations/4/download"
    }
  }
}
```

**필드 설명**:
| 필드 | 타입 | 설명 |
|------|------|------|
| busy | bool | 진행 중(PENDING/GENERATING) 작업 존재 여부 |
| ready | bool | `busy` 의 반대 (새 생성 즉시 처리 가능) |
| in_progress_count | int | 진행 중 작업 수 |
| in_progress[] | array | 진행 중 작업 목록 (id, title, status, created_at) |
| last_completed | object\|null | 최근 완료 보고서 (id, title, completed_at, pdf_download_url) |

> **참조**: PRD_Report_Master_Redesign — 보고서 PDF는 HTML(Chart.js)→Chromium 렌더 + PyMuPDF 무손실 재압축(~85% 축소). 정형=전 섹션 전체 페이지네이션, 비정형=template 컴포넌트(`enabled_components`) 선택. 본 status·download·preview 모두 동일 비동기 파이프라인 기준.

### 10.5 Report Preview Page

> 개발용 HTML 미리보기 페이지 (Swagger 미포함, Chart.js 기반)

#### 10.5.1 Endpoint

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/reports/generations/{generation_id}/preview-page` | HTML 미리보기 페이지 |

#### 10.5.2 GET `/api/reports/generations/{generation_id}/preview-page`

Chart.js 기반 HTML 미리보기 페이지를 렌더링합니다.

**Response**: HTML 페이지 (`text/html`)

**특징**:
- Jinja2 템플릿 기반 (`app/templates/reports/preview.html`)
- Chart.js CDN 연동 (Pie, Bar, Line 차트)
- 섹션별 차트 및 그리드 테이블 표시
- PDF 다운로드 버튼 포함 (COMPLETED 상태 시)

---

## 11. 추적 이력 API 설계 *(v4.11 신규)*

### 11.1 개요

GIS 추적(Tracking) 이력 영속·조회 API. NATS `sensorway.{부대ID}.gis.tracking-status`(TRACKING_STATUS, `targets[]`)로 브로드캐스트되는 추적 타겟을 **서버가 단일 구독·저장**(독립 워커 `gis-ingest`)하고, 클라이언트는 **read-only GET**으로 기간별 청크를 조회해 Playback 한다.

- **저장 주체**: 서버측 NATS 인제스트(`gis-ingest` 워커 — **구현됨**: docker-compose 서비스 `api-test-gis-ingest`, `db_monitor` 역방향 미러). **클라이언트는 POST 하지 않는다** — 다중 관제 스테이션이 각자 POST 시 N배 중복쓰기 발생.
- **멱등성**: `UNIQUE(track_id, observed_at)` — 재전송/다중 인제스트 안전(`INSERT ... ON CONFLICT DO NOTHING`).
- **페이지네이션**: keyset cursor(`(observed_at, id)` 단조 정렬). 1Hz append-only 시계열의 deep offset 성능 급락 회피.
- **인증**: 조회 2종(`/points`·`/sessions`)은 JWT(`AUTH_MODE=token` 시), `/health`는 무인증.
- **보존정책**: 기본 7일(`purge_track_points(retain_days)` 함수, 스케줄 호출은 운영 선택). 추적 테이블은 audit append-only 대상 아님(자유 삭제).

> **테이블**: `track_points` (마이그레이션 `app/migrations/v54_tracking_points.sql`, 앱 startup `create_all` 자동 생성). 컬럼: `id, camera_id, track_id, label, threat_level, latitude, longitude, distance_m, confidence, observed_at, tracking_state, speed_mps, session_seq, created_at`.

> **계약 정합**: TRACKING_STATUS **신버전 `targets[]`**(`track_id`·`observed_at`·`threat_level` 포함)을 전제로 한다. 메시지 상세는 `docs/Gop_Message_Broker_연동설계.md §8.3.7`.

#### 11.1.1 인제스트 매핑 (참고 — 서버측 `gis-ingest`, 클라 범위 밖)

| TRACKING_STATUS 필드 | track_points 컬럼 |
|---|---|
| `body.camera_id` | `camera_id` |
| `body.tracking` (`active`만 저장) | `tracking_state` |
| `targets[].track_id` | `track_id` |
| `targets[].label` | `label` |
| `targets[].threat_level` | `threat_level` |
| `targets[].confidence` | `confidence` |
| `targets[].observed_at` | `observed_at` |
| `targets[].location.latitude` | `latitude` |
| `targets[].location.longitude` | `longitude` |
| `targets[].location.distance_m` | `distance_m` |

---

### 11.2 추적점 구간 조회

- **Endpoint**: `GET /api/tracking/points`
- **설명**: 기간(`from`~`to`) 추적점을 keyset cursor 청크로 조회. Playback 핵심. 정렬 `observed_at ASC, id ASC`.

**Query Parameters:**

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|:----:|--------|------|
| `from` | datetime(ISO8601) | X | - | 구간 시작 (`observed_at ≥`) |
| `to` | datetime(ISO8601) | X | - | 구간 종료 (`observed_at ≤`) |
| `camera_id` | int | X | - | 카메라 필터 |
| `track_id` | string | X | - | 단일 트랙 필터 |
| `cursor` | string | X | - | 직전 응답의 `cursor.next_cursor` |
| `limit` | int | X | 1000 | 페이지 크기 (최대 5000) |

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Track points retrieved",
  "data": [
    {
      "id": 100123,
      "camera_id": 201,
      "track_id": "cam201-1738750245-007",
      "label": "person",
      "threat_level": "THREAT",
      "latitude": 38.1235,
      "longitude": 127.5680,
      "distance_m": 120.5,
      "confidence": 0.92,
      "observed_at": "2026-02-05T19:30:00+09:00",
      "tracking_state": "active",
      "speed_mps": null,
      "session_seq": null
    }
  ],
  "cursor": {
    "next_cursor": "MjAyNi0wMi0wNVQxOTozMDowMHwxMDAxMjM=",
    "limit": 1000,
    "has_more": true
  },
  "meta": {
    "timestamp": "2026-02-05T19:30:01.000+09:00",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

> **cursor 사용**: `cursor.next_cursor`가 `null`이 될 때까지 반복 호출하여 구간 전체를 청크로 적재한다. 표준 list envelope에 cursor 슬롯이 없어 전용 `cursor` 필드를 둔다(`pagination` 미사용).

**Error Response:**
- `400 BAD_REQUEST`: `cursor` 형식 오류
- `401 UNAUTHORIZED`: 인증 실패 (`AUTH_MODE=token`)

---

### 11.3 추적 세션 목록

- **Endpoint**: `GET /api/tracking/sessions`
- **설명**: Playback 타임라인용 세션 목록. `track_id`(+`camera_id`) 단위로 `MIN/MAX(observed_at)`·`COUNT(*)`를 집계(별도 세션 테이블 없는 파생). `from`/`to`는 구간 내 추적점만 집계한다.

**Query Parameters:**

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|:----:|--------|------|
| `from` | datetime(ISO8601) | X | - | 구간 시작 |
| `to` | datetime(ISO8601) | X | - | 구간 종료 |
| `camera_id` | int | X | - | 카메라 필터 |

**Response (200 OK):**

```json
{
  "success": true,
  "message": "Track sessions retrieved",
  "data": [
    {
      "track_id": "cam201-1738750245-007",
      "camera_id": 201,
      "label": "person",
      "start_at": "2026-02-05T19:30:00+09:00",
      "end_at": "2026-02-05T19:34:11+09:00",
      "point_count": 251,
      "session_seq": null
    }
  ],
  "meta": {
    "timestamp": "2026-02-05T19:34:12.000+09:00",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

**Error Response:**
- `401 UNAUTHORIZED`: 인증 실패 (`AUTH_MODE=token`)

---

### 11.4 추적 가용성 체크

- **Endpoint**: `GET /api/tracking/health`
- **설명**: Playback 진입 게이팅용. 추적 테이블 접근 가능하면 200, 아니면 503. **무인증**.

**Response (200 OK):**

```json
{ "status": "ok", "tracking_count": 12345 }
```

**Response (503 Service Unavailable):**

```json
{ "status": "unavailable", "tracking_count": 0 }
```

---

## 12. 에러 처리

### 12.1 에러 응답 형식

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

### 12.2 에러 코드 정의

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

### 12.3 에러 응답 예제

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

## 13. 부록

### 13.1 전체 Endpoint 목록

#### Device Endpoints

**Controllers**:
- `GET /api/devices/controllers` - 목록 조회
- `POST /api/devices/controllers` - 생성
- `GET /api/devices/controllers/{id}` - 단일 조회
- `PATCH /api/devices/controllers/{id}` - 수정 (부분)
- `PUT /api/devices/controllers/{id}` - 수정 (전체) *(v3.9 추가)*
- `DELETE /api/devices/controllers/{id}` - 삭제

**Sensors**:
- `GET /api/devices/sensors` - 목록 조회
- `POST /api/devices/sensors` - 생성
- `GET /api/devices/sensors/{id}` - 단일 조회
- `PATCH /api/devices/sensors/{id}` - 수정 (부분)
- `PUT /api/devices/sensors/{id}` - 수정 (전체) *(v3.9 추가)*
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
- `POST /api/devices/groups/{id}/devices` - 디바이스 할당 (벌크)
- `DELETE /api/devices/groups/{group_id}/devices/{device_id}` - 디바이스 제거 (단건)
- `DELETE /api/devices/groups/{group_id}/devices` - 디바이스 벌크 해제 *(v4.3 신규)*

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

**Enclosure Metrics 독립 목록** (v3.9 추가):
- `GET /api/enclosure-metrics` - 전체 함체 메트릭 목록 조회 (독립)

**Camera Settings** (v3.6 신규):
- `GET /api/devices/cameras/{camera_id}/settings` - 카메라 설정 조회
- `PATCH /api/devices/cameras/{camera_id}/settings` - 카메라 설정 수정 (부분)
- `PUT /api/devices/cameras/{camera_id}/settings` - 카메라 설정 수정 (전체)

**Lamps** (v3.4 신규):
- `GET /api/devices/lamps` - 경광등 목록 조회
- `POST /api/devices/lamps` - 경광등 생성
- `GET /api/devices/lamps/{id}` - 경광등 단일 조회
- `PATCH /api/devices/lamps/{id}` - 경광등 수정 (부분)
- `PUT /api/devices/lamps/{id}` - 경광등 수정 (전체)
- `DELETE /api/devices/lamps/{id}` - 경광등 삭제

#### Event Endpoints

**Detection Events**:
- `GET /api/events/detections` - 목록 조회
- `POST /api/events/detections` - 생성
- `GET /api/events/detections/{id}` - 단일 조회
- `PATCH /api/events/detections/{id}` - 수정 (부분)
- `PUT /api/events/detections/{id}` - 수정 (전체) *(v3.9 추가)*
- `DELETE /api/events/detections/{id}` - 삭제
- `GET /api/events/detections/{event_id}/actions` - Action Event 목록 조회

**Malfunction Events**:
- `GET /api/events/malfunctions` - 목록 조회
- `POST /api/events/malfunctions` - 생성
- `GET /api/events/malfunctions/{id}` - 단일 조회
- `PATCH /api/events/malfunctions/{id}` - 수정 (부분)
- `PUT /api/events/malfunctions/{id}` - 수정 (전체) *(v3.9 추가)*
- `DELETE /api/events/malfunctions/{id}` - 삭제
- `GET /api/events/malfunctions/{event_id}/actions` - Action Event 목록 조회

**Connection Events**:
- `GET /api/events/connections` - 목록 조회
- `POST /api/events/connections` - 생성
- `GET /api/events/connections/{id}` - 단일 조회
- `PATCH /api/events/connections/{id}` - 수정 (부분)
- `PUT /api/events/connections/{id}` - 수정 (전체) *(v3.9 추가)*
- `DELETE /api/events/connections/{id}` - 삭제

**Action Events**:
- `GET /api/events/actions` - 목록 조회
- `POST /api/events/actions` - 생성
- `GET /api/events/actions/{id}` - 단일 조회
- `PATCH /api/events/actions/{id}` - 수정 (부분)
- `PUT /api/events/actions/{id}` - 수정 (전체) *(v3.9 추가)*
- `DELETE /api/events/actions/{id}` - 삭제

**Detection Logs**:
- `GET /api/detection-logs` - 탐지 로그 목록 조회
- `GET /api/detection-logs/{event_id}` - 탐지 로그 단건 조회

**Event Statistics** (v4.2 신규):
- `GET /api/events/statistics/summary` - 이벤트 타입별 건수 요약 (원형 그래프 + 요약 카드)
- `GET /api/events/statistics/trend` - 시간대별 이벤트 건수 추이 (라인 차트)
- `GET /api/events/statistics/by-device` - 제어기별/카메라별 이벤트 건수 (막대 그래프)
- `GET /api/events/statistics/dashboard` - 대시보드 통합 (summary + trend + by-device)

**Event Suppression Schedules** (v6.3 신규):
- `POST /api/event-suppression-schedules` - 억제 스케줄 생성 (events:edit)
- `GET /api/event-suppression-schedules` - 목록(상태·대상 필터, 페이지) (events:view)
- `GET /api/event-suppression-schedules/active` - 현재 활성 창(배너·서브시스템 조회 훅) (events:view)
- `GET /api/event-suppression-schedules/{id}` - 단건 조회 (events:view)
- `PATCH /api/event-suppression-schedules/{id}` - 부분 변경 (events:edit)
- `DELETE /api/event-suppression-schedules/{id}` - 삭제(soft-cancel) (events:delete)

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
- `POST /api/integrations/event-mappings/{mapping_id}/cameras` - 카메라 연동 생성 (단건)
- `POST /api/integrations/event-mappings/{mapping_id}/cameras/bulk` - 카메라 연동 벌크 등록 *(v4.3 신규)*
- `GET /api/integrations/event-mappings/{mapping_id}/cameras/{config_id}` - 카메라 연동 단일 조회
- `PATCH /api/integrations/event-mappings/{mapping_id}/cameras/{config_id}` - 카메라 연동 수정 (부분)
- `PUT /api/integrations/event-mappings/{mapping_id}/cameras/{config_id}` - 카메라 연동 수정 (전체)
- `DELETE /api/integrations/event-mappings/{mapping_id}/cameras/{config_id}` - 카메라 연동 삭제 (단건)
- `DELETE /api/integrations/event-mappings/{mapping_id}/cameras` - 카메라 연동 벌크 해제 *(v4.3 신규)*

**Event Mapping Speakers** (v2.8 신규):
- `GET /api/integrations/event-mappings/{mapping_id}/speakers` - 스피커 연동 목록 조회
- `POST /api/integrations/event-mappings/{mapping_id}/speakers` - 스피커 연동 생성 (단건)
- `POST /api/integrations/event-mappings/{mapping_id}/speakers/bulk` - 스피커 연동 벌크 등록 *(v4.3 신규)*
- `GET /api/integrations/event-mappings/{mapping_id}/speakers/{config_id}` - 스피커 연동 단일 조회
- `PATCH /api/integrations/event-mappings/{mapping_id}/speakers/{config_id}` - 스피커 연동 수정 (부분)
- `PUT /api/integrations/event-mappings/{mapping_id}/speakers/{config_id}` - 스피커 연동 수정 (전체)
- `DELETE /api/integrations/event-mappings/{mapping_id}/speakers/{config_id}` - 스피커 연동 삭제 (단건)
- `DELETE /api/integrations/event-mappings/{mapping_id}/speakers` - 스피커 연동 벌크 해제 *(v4.3 신규)*

**Event Mapping Lamps** (v3.4 신규):
- `GET /api/integrations/event-mappings/{mapping_id}/lamps` - 경광등 연동 목록 조회
- `POST /api/integrations/event-mappings/{mapping_id}/lamps` - 경광등 연동 생성 (단건)
- `POST /api/integrations/event-mappings/{mapping_id}/lamps/bulk` - 경광등 연동 벌크 등록 *(v4.3 신규)*
- `GET /api/integrations/event-mappings/{mapping_id}/lamps/{config_id}` - 경광등 연동 단일 조회
- `PATCH /api/integrations/event-mappings/{mapping_id}/lamps/{config_id}` - 경광등 연동 수정 (부분)
- `PUT /api/integrations/event-mappings/{mapping_id}/lamps/{config_id}` - 경광등 연동 수정 (전체)
- `DELETE /api/integrations/event-mappings/{mapping_id}/lamps/{config_id}` - 경광등 연동 삭제 (단건)
- `DELETE /api/integrations/event-mappings/{mapping_id}/lamps` - 경광등 연동 벌크 해제 *(v4.3 신규)*

**Mapping SubResource 독립 List** (v3.8 신규):
| `GET` | `/api/integrations/mapping-cameras` | 전체 MappingCamera 조회 (독립) | v3.8 |
| `GET` | `/api/integrations/mapping-speakers` | 전체 MappingSpeaker 조회 (독립) | v3.8 |
| `GET` | `/api/integrations/mapping-lamps` | 전체 MappingLamp 조회 (독립) | v3.8 |

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

**Proxy Settings** (v3.6 신규):
- `GET /api/servers/{server_id}/proxy-settings` - 프록시 설정 조회
- `PATCH /api/servers/{server_id}/proxy-settings` - 프록시 설정 수정 (부분)
- `PUT /api/servers/{server_id}/proxy-settings` - 프록시 설정 수정 (전체)

**System Events** (v2.9 신규):
- `GET /api/system-events` - 이벤트 목록 조회
- `POST /api/system-events` - 이벤트 생성
- `GET /api/system-events/{id}` - 이벤트 상세 조회
- `PATCH /api/system-events/{id}` - 이벤트 수정
- `DELETE /api/system-events/{id}` - 이벤트 삭제
- `POST /api/system-events/{id}/acknowledge` - 이벤트 확인
- `GET /api/system-events/summary` - 요약 통계 조회
- `GET /api/servers/{server_id}/system-events` - 서버별 시스템 이벤트 조회 *(v3.9 추가)*

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
- `POST /api/users/me/photo` - 본인 프로필 사진 업로드 (multipart, v4.11 신규)
- `DELETE /api/users/me/photo` - 본인 프로필 사진 삭제 (→ default 복귀, v6.3 신규)
- `GET /api/users/photo/{file_name}` - 프로필 사진 다운로드 (무인증, v4.11 신규)
- `POST /api/users/{id}/photo` - **관리자**: 대상 계정 사진 업로드 (multipart, v6.3 신규)
- `DELETE /api/users/{id}/photo` - **관리자**: 대상 계정 사진 삭제 (→ default 복귀, v6.3 신규)

**UserGroups**:
- `GET /api/user-groups` - 그룹 목록 조회
- `POST /api/user-groups` - 그룹 생성
- `GET /api/user-groups/{id}` - 그룹 상세 조회
- `PUT /api/user-groups/{id}` - 그룹 수정
- `DELETE /api/user-groups/{id}` - 그룹 삭제
- `GET /api/user-groups/{id}/users` - 그룹 소속 사용자 목록
- `POST /api/user-groups/{group_id}/permissions` - 그룹 권한 변경 (ADMIN 전용, v5.0 신규)

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
- `GET /api/reports/status` - 보고서 엔진 Busy/Ready 상태 (read-only)
- `GET /api/reports/generations` - 생성 이력 목록 조회
- `GET /api/reports/generations/{id}` - 생성 이력 상세 조회
- `GET /api/reports/generations/{id}/download` - PDF 다운로드
- `GET /api/reports/generations/{id}/preview` - 미리보기 데이터

**Report Preview Page**:
- `GET /api/reports/generations/{generation_id}/preview-page` - HTML 미리보기 페이지

#### Thumbnail Endpoints (v4.0 신규)

**Thumbnails**:
- `POST /api/thumbnails` - 썸네일 이미지 업로드 (multipart form data, 클라이언트 지정 file_name)
- `GET /api/thumbnails` - 썸네일 목록 조회 (날짜 필터링, 페이지네이션)
- `GET /api/thumbnails/{id}` - 썸네일 메타데이터 조회
- `GET /api/thumbnails/{id}/image` - 썸네일 이미지 다운로드 (ID 기반, FileResponse)
- `GET /api/thumbnails/images/{file_name}` - 썸네일 이미지 다운로드 (파일명 기반, FileResponse)
- `DELETE /api/thumbnails/{id}` - 썸네일 삭제 (파일 + DB)

#### Tracking Endpoints *(v4.11 신규)*

- `GET /api/tracking/points` - 추적점 구간 조회 (keyset cursor)
- `GET /api/tracking/sessions` - 추적 세션 목록 (타임라인)
- `GET /api/tracking/health` - 추적 가용성 체크 (무인증)

### 13.2 Event-Device 리팩토링 변경사항 (v2.3)

#### 13.2.1 API Request 변경

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

#### 13.2.2 API Response 변경

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

#### 13.2.3 DeviceNestedResponse 스키마

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

#### 13.2.4 Event 영속성 보장

> **핵심 원칙**: Event 데이터는 어떤 경우에도 삭제되지 않아야 한다.

| 시나리오 | device_id | device_description | device (Response) |
|----------|-----------|-------------------|-------------------|
| Event 생성 | `101` | `"[Multi] Sensor-A-1..."` | Nested Object |
| Device 조회 | `101` | `"[Multi] Sensor-A-1..."` | Nested Object |
| **Device 삭제 후** | `NULL` | `"[Multi] Sensor-A-1..."` | `null` |

- **FK 설정**: `ondelete="SET NULL"` (CASCADE 사용 금지!)
- **device_description**: Device 삭제 후에도 과거 Device 정보 참조 가능

#### 13.2.5 마이그레이션 스크립트

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

### 13.3 EventMapping 리팩토링 변경사항 (v2.3)

#### 13.3.1 EventMapping 테이블 변경

| 필드 | Before (v2.2 이전) | After (v2.3) | 설명 |
|------|-------------------|--------------|------|
| `group_event` | VARCHAR(100) | **제거됨** | 자유 문자열, DeviceGroup과 무관 |
| `device_group_id` | - | INTEGER FK **신규** | DeviceGroup.id 참조 (SET NULL on delete) |

#### 13.3.2 API 변경 요약

| API | Before | After |
|-----|--------|-------|
| GET (목록) | `?group_event=xxx` 필터 | `?device_group_id=1` 필터 |
| GET (단건) | `group_event` 필드 반환 | `device_group_id` 필드 반환 |
| POST | `group_event` 문자열 입력 | `device_group_id` 정수 입력 |
| PATCH | `group_event` 수정 가능 | `device_group_id` 수정 가능 |
| PUT | `group_event` 필수 | `device_group_id` 필수 |

#### 13.3.3 이벤트-카메라 연동 흐름

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

#### 13.3.4 EventMapping FK 정책

| 관계 | 동작 | 정책 | 결과 |
|------|------|------|------|
| DeviceGroup → EventMapping | DeviceGroup 삭제 | `ON DELETE SET NULL` | EventMapping.device_group_id → NULL |

> **참고**: DeviceGroup이 삭제되어도 EventMapping 자체는 유지됨 (device_group_id만 NULL)

---

## 변경 이력

### [v6.3 후속] `event_put_lazyload_fix` — 이벤트 PUT/POST device lazy-load 500 수정 (2026-08-03)

> GIS 리포트(`docs/coordinations/GOP_Server_API_event_PUT_500_lazyload_REQUEST.md`) 검증 후 수정. `PUT /api/events/detections/{id}`·`PUT /api/events/connections/{id}` 가 응답 조립 시 `event.device` 를 async 컨텍스트에서 lazy-load(MissingGreenlet) → 500. ★UPDATE 는 commit 된 뒤 응답에서 터져 "저장됐는데 실패 표시"(데이터/화면 불일치).

- **수정**: 두 PUT 핸들러 조회에 `selectinload(...device).selectin_polymorphic([...])` 추가(detections.py:604·connections.py:545) — 목록/단건/PATCH/malfunctions PUT 과 동일 패턴.
- **동반 발견·수정(잔여 점검, GIS §4 요청)**: `POST /api/events/connections`(create) 도 device 를 `select(Device)` 로만 조회(폴리모픽 누락) → 생성 응답에서 동일 500(connection_events 생성 자체 불가 원인). connections.py:362 에 selectin_polymorphic 추가. detections/malfunctions POST 는 정상.
- **검증**: detection PUT 무변경 왕복 → 200+device / connection 생성→왕복 PUT→삭제 전 구간 200+device / event 목록·단건·PATCH 무회귀. 롤백태그 `pre-event_put_lazyload_fix`.
- **미해결(별건)**: 응답 조립 실패 시 commit-후-500 정책(부분 실패 노출) · 원격 테스트서버 bulk-delete 405 는 재배포 대기(코드 존재).

### [v6.3 후속] `event_suppression_multi_target` — 정비 창 대상 복수 선택 지원 (2026-08-01)

> GIS 요청(P1). 한 정비 창에 **복수 대상**(장비 N개 / 그룹 N개 / 전체) 지정. `target_type`(device/group/all 배타) 유지, 단일 FK → **배열 + junction 2테이블**. §6.8 필드/예시 배열화.

- **모델**: 단일 컬럼 `target_device_id`/`target_group_id` 제거 → junction `event_suppression_target_devices`·`event_suppression_target_groups`(각 schedule_id/device|group_id FK **CASCADE**, UNIQUE). 관계 `lazy="selectin"`(async 안전). 마이그 **v70**(기존 단일행→junction 이관 + 컬럼 DROP, 멱등·fresh no-op).
- **스키마/API**: Create/Update `target_device_ids: int[]`·`target_group_ids: int[]`(device→≥1/group→≥1 검증, 중복제거). Response·목록·/active 배열 반환. 목록 필터 `?device_id=`/`?group_id=`는 junction 포함 매치(EXISTS).
- **게이트 `is_suppressed()`**: DEVICE `device_id ∈ ids`, GROUP `set(group_ids) ∩ 소속그룹 ≠ ∅`. 그룹 멤버십은 후보 전체 group_ids 합집합 1회 배치조회(N+1 회피 유지). fail-open 등 안전장치 불변.
- **테스트** `tests/test_event_suppression.py` **32 passed**(멀티 device 집합·멀티 group 교집합·CRUD 다중그룹+필터·PATCH 대상교체). 회귀 0.
- **라이브 E2E**(EnclosureManager): 복수 device[11,12] 둘 다 202·대상외 13 정상 201·상태불변 / 복수 group[1,2] 교집합 억제·필터 매치 — **13/13 PASS**, DB 청결. 5중싱크(명세 §6.8·Swagger 배열·재빌드·v70 적용). 롤백 `pre-v6.3-event_suppression_multi_target`.

### [v6.3 후속] `session_concurrency` — 다중세션 정책 + 인증 하드닝 (evict_all/allow, RBAC-03, SEC-01, SSO 예약) (2026-07-31)

> 단일세션 강제 evict 를 **정책화**(SSO 다중세션 대비). §9.8 세션설정에 5키 추가, §9.2 로그인에 `X-Client-Id`. ★기본값=현행 100% 보존(evict_all·상한0·self_replace off) → 배포 직후 동작 0. 커밋 `9b7b8c0`(origin). 라이브: A01~A18 10/10 + allow공존 + RBAC403 + SEC-01.

- **설정(§9.8)**: `session_concurrency_policy`(evict_all|allow) · `max_concurrent_sessions`(0=무제한, 초과 시 최오래 evict) · `session_self_replace_enabled`(동일 client_id 재로그인만 교체) · `session_history_retention_days`(0=무동작, sweep DELETE) · `login_anomaly_event_enabled`(예약). `settings_service`/`schemas.settings`/`routers.settings` + `ConfigChangeLog` 감사.
- **스키마**: 마이그 `v68_session_client_id.sql`(멱등) — `user_sessions.client_id VARCHAR(64)` + **SSO 예약컴럼** `auth_source`(기본 'local')·`idp_subject`·`idp_session_id` + 부분 인덱스 2종. `UserSession` 모델 반영, `IDEMPOTENT_MIGRATIONS` 등재.
- **로그인(§9.2)**: `X-Client-Id` 헤더 우선(또는 `client_id` 바디, 1~64자 `[A-Za-z0-9._:-]`, invalid=무시). `allow`에서 정책 분기(evict_all=현행/allow=공존), cap 초과 evict_oldest, self-replace 게이트.
- **RBAC-03**: `enforce_matrix` 경로해석을 `request.url.path`로 교정 — 중첩마운트 상대경로 버그(전 라우트 무집행)를 실집행으로. integrations 등 등록경로 권한0 USER 쓰기 → **403**(수정 전 404).
- **SEC-01**: 폐기 토큰이 전역 enforcer 경유 쓰기에서도 `401 SESSION_REVOKED`(`details.reason` 보존) 동형 발화 — read/write shape 일치.
- **SSO 예약(로직 0)**: `config.py` `SSO_ENABLED=False`/`OIDC_*=""` — 실배선은 후속 SSO PRD. FR-FIX-01~04(P0 세션결함, 커밋 ff0126b) 선행.

### [v6.3 후속] `event_suppression` — 스케줄 기반 이벤트 수신 억제(정비 창) 신규 (2026-07-31)

> 신규기능(PRD→plan→dev→test). 공사·설치·장애수리·AS 기간에 **대상(장비/그룹/전체) × 이벤트유형(연결/탐지/장애/전체) × 시간창**을 지정해 이벤트 수신을 억제. §6.8 신규. ★범위=Phase 1(이 서버 **저장·DB파생 억제**; 라이브 NATS 방송 미차단=Phase 2 각 서브시스템 몫, `docs/subsystems/event-suppression/`).

- **데이터/enum**: `app/models/event_suppression.py` `EventSuppressionSchedule`(테이블 `event_suppression_schedules`, `UtcDateTime` 시간창, target FK `SET NULL`, soft-cancel) + `app/utils/enums.py` enum 4종(`EnumSuppressionTargetType`/`Side`/`EventScope`/`Status`) + `EnumConfigResourceType.SUPPRESSION_SCHEDULE`. 마이그 `v67_event_suppression_schedules.sql`(enum `ALTER TYPE ADD VALUE IF NOT EXISTS` 멱등 + `IDEMPOTENT_MIGRATIONS` 등재; 테이블은 create_all).
- **API(§6.8)**: 6개 엔드포인트 `POST/GET(목록·필터)/GET active/GET {id}/PATCH/DELETE(soft-cancel)`. `ApiResponse`/`ApiSingleResponse` 엔벌로프, 파생 status, `ConfigChangeLog` 감사. RBAC `require_perm("events", view|edit|delete)`, role=ADMIN bypass. 신규 쓰기 3라우트 `PERMISSION_MAP` 등록.
- **억제 게이트(핵심)**: 공유 서비스 `event_suppression_service.is_suppressed()` 를 `detections`/`malfunctions`/`connections` POST 핸들러의 **device 조회 후·장비 상태 플립 전·db.add 전** 삽입. 매치 시 **202 `{suppressed:true}`**(무저장, 상태 플립 생략). **fail-open**(게이트 오류 시 rollback 복구 후 정상 저장). lazy 요청시점 평가=권위, sweep(`SUPPRESSION_SWEEP_INTERVAL_MINUTES` 기본5m)=비권위 백스톱. `connections` POST 라우트-레벨 `events:edit` 데코레이터 정합.
- **감지/감시**: sensor/controller=detection, camera=surveillance, speaker/lamp/enclosure=보조(both일 때만 매치). group·all 스코프에 `target_side` 적용.
- **테스트**: `tests/test_event_suppression.py` **28 passed**(side파생·매치·status·게이트 device/group/all·side필터·category·window경계·revoked·ALL확장·action제외·CRUD수명주기·fail-open세션복구·PATCH혼합tz→422·PATCH FK정리). 회귀 0.
- **서브시스템 안내**: `docs/subsystems/event-suppression/`(README + Proxy/GIS/VMS/AiAnalysis/NVR/db_monitor) — 각 서브시스템이 완전 차단 위해 할 일(Proxy 202처리·발행skip / GIS 관리UI·배너·알람필터 / VMS·NVR 이벤트트리거 녹화·PTZ 억제).

### [v6.3 후속] `settings_config_enum` — 세션설정 변경 500 수정 (config enum SETTINGS 보강) (2026-07-31)

> clone/업그레이드 DB(옛 named volume 잔존)에서 Postgres 네이티브 enum `enumconfigresourcetype` 에 `SETTINGS` 값이 없어, 세션설정 변경(`PUT /api/settings/session`)의 감사 INSERT(`resource_type='SETTINGS'`)가 "invalid input value for enum" 로 500. `create_all()` 은 기존 enum 에 값 추가 불가 → startup 마이그레이션으로 자가치유.

- `app/migrations/v65_add_settings_config_enum.sql`: `ALTER TYPE enumconfigresourcetype ADD VALUE IF NOT EXISTS 'SETTINGS'`(멱등) + `IDEMPOTENT_MIGRATIONS` 등재 → 모든 DB 다음 기동 시 자가치유(fresh no-op / 옛 DB 값 추가). PG16 트랜잭션 내 ADD VALUE 정상 검증. 즉시 조치(재배포 전): 대상 DB 에서 위 `ALTER TYPE ...` 1줄 실행.

### [v6.3 후속] `datetime_unification` — 전 API datetime UTC 저장 + DISPLAY_TZ 출력 통일 (Option B) (2026-07-31)

> 문제: 저장 naive-KST / 출력 +09:00 / 입력 혼용이 뒤섞여 asyncpg(v6.0~)가 aware↔naive 혼용을 거부 → server_metrics·events·reports 등 **다수 500**, 해외 재배포 불가(KST 하드코딩). 근본 통일.

**규약 (§3.4 신설)**: 저장 UTC(timestamptz) · 출력 `DISPLAY_TIMEZONE`(기본 Asia/Seoul, DST 자동) · 입력 aware 권장(naive 는 DISPLAY_TZ 간주). 국가 비종속 — `DISPLAY_TIMEZONE` env 만 교체.

- **공용 유틸** `app/utils/datetime.py`: `utc_now`(aware UTC) · `to_utc` · `to_display`. **설정** `app/config.py` `DISPLAY_TIMEZONE`(+`display_tz` ZoneInfo).
- **타입레벨 차단** `app/models/types.py` `UtcDateTime(TypeDecorator, timezone=True)` — bind 시 aware→UTC 정규화(asyncpg 500 원천 차단). 모델 17파일 `Column(DateTime)`→`UtcDateTime`, 쓰기 default→`utc_now`.
- **마이그** `app/migrations/v66_datetime_to_utc.sql`(startup 멱등, `init_db` 등록): naive 컬럼만 `USING col AT TIME ZONE 'Asia/Seoul'`(과거 KST 벽시계→정확 UTC instant, 무손실) / `token_blacklist`=`'UTC'`. **api_logs 파티션·schema_migrations 제외**. → **git pull/번들 업그레이드 시 옛 원격 DB 도 자동 전환**(fresh=no-op). 직후 async 풀 `dispose`로 prepared-cache 무효화 전이 500 제거.
- **serializer** `schemas/common.py`·`main.py`: `KSTDatetime`/전역 encoder/오류 meta → `to_display`(DISPLAY_TZ), OpenAPI `format:date-time` 유지. **입력 정규화(FR-07)** `ReportGenerateRequest` 등 body 비교 전 `to_utc`. 라우터 정규화 헬퍼(`_to_naive_kst` 계열 6종)·리포트 범위 → `to_utc` 위임.
- **api_logs**: 파티션 키 ALTER 불가 → 컬럼은 naive 유지하되 저장을 **naive-UTC 벽시계**(`utc_now().replace(tzinfo=None)`)로 바꿔 전역 naive=UTC 규약과 정합(월파티션 ±offset 시프트는 인접월 안착). 업그레이드 직후 **구(舊) KST 행은 retention 소멸까지 표시 offset skew**(전환기, 신규 행 정확). 완전 timestamptz 재생성은 v67(선택) 이연.
- **라이브 검증(재빌드·재기동)**: 마이그 72 timestamptz / 10 제외(api_logs 9+schema_migrations). aware `collected_at +09:00` POST → **201**(저장 UTC 10:50 / 출력 +09:00). 읽기 GET 다수 200+`+09:00`. reports/generate aware 범위 → **201→COMPLETED**(역순=422, TypeError 아님). 오류 meta `+09:00`. 다국가 `to_display` 격리검증(Budapest `+02:00` DST). 롤백 3종: git `pre-datetime_unification` · 이미지 `pids-api-server:pre-datetime_unification` · DB덤프 `backups/datetime-unification-20260731/`.
- **후속 fix `gis-ingest`(`3e91dfe`)**: gis-ingest 워커(raw asyncpg)가 v66 timestamptz 전환 후 `track_points.observed_at` 을 naive-KST 로 바인딩 → asyncpg 가 naive 를 UTC 로 간주해 **+9h 미래로 조용히 저장**(데이터 오염) → `_parse_observed_at`/`ingested_at` 을 aware UTC 로 수정. 라이브 E2E(UTC 10:30 입력→10:30 저장) 복구, `test_gis_ingest` 8 passed, 이미지 재빌드.
- **후속 fix 리포트 끝일 경계(`c349a1d`)**: FR-07 validator 가 `end_date` 를 aware UTC 로 선변환하면서 리포트 FR-RCD-03 자정판정(`end_date.hour==0`)이 깨져 date-only/자정 end 가 23:59:59 로 확장 안 되어 **끝일 통째 누락**하던 회귀 → 판정을 DISPLAY_TZ 벽시계(`to_display`)로 교정 후 확장→`to_utc` 저장. 라이브: date-only `2026-01-06` end → 저장 `2026-01-06 14:59:59 UTC`(=23:59:59 KST, 끝일 포함) 복구. GIS 문의(Q2) 검증 중 발견. §3.4 날짜 범위 필터 규약 동반 신설.
- **후속 fix 응답 offset 누락(Q4)**: `camera_presets`·`enclosure_metrics`·`rois`·`xypoints` 라우터가 응답 dict 에 `X.created_at.isoformat()` 로 datetime 을 직접 문자열화 → 전역 encoder(`to_display`) 우회로 **`+00:00`(UTC) 출력**(규약 `+09:00` 위반, Pydantic KSTDatetime 미경유 dict 응답). 27곳 `to_display(...).isoformat()` 로 교정 → 응답 datetime 전 엔드포인트 `+09:00` 일관. EnclosureManager 계정 라이브 테스트 중 발견(enclosure `created_at` `+00:00`→`+09:00` 실측).

### [v6.3 후속] `detection_sync` — 탐지 이벤트 SYNC 발행 (PTZ 회전후 썸네일 갱신 통지) (2026-07-31)

> 신규기능(PRD→plan→dev). 탐지 이벤트 UPDATE/DELETE 시 NATS `SYNC_DETECTION` 발행. 1차 동인 = PTZ 회전 후 갱신된 `detail.thumbnail`을 GIS가 재수신.

- `app/db_triggers.py`: `fn_notify_detection_sync` 트리거(detection_events **AFTER UPDATE OR DELETE**, gop_sync 채널) — `{cmd:SYNC_DETECTION, action, resource_id}`. **INSERT 미발행**(필드 DETECT 중복 방지).
- `db_monitor/main.py`: `CMD_SUBJECT_MAP` `SYNC_DETECTION → all.sync.detection` (from=DBApi).
- `app/schemas/event.py`: `DetectionDetail`에 `frame_width`/`frame_height`(px) 추가 + Swagger 예시 4곳 — broker-v15 교차검증 GAP 해소. detail 서술 §이벤트 갱신.
- 라이브 검증: POST(생성)→**미발행**, PATCH detail→`{UPDATED,id}`, DELETE→`{DELETED,id}`, subject=`all.sync.detection`·from=DBApi. 단위 `tests/test_detection_detail_frame.py` 3 passed.
- 브로커 명세 `Gop_Message_Broker_연동설계_v1.6.md` §3.2/§6.1/§9.11/카탈로그 동반 갱신. 롤백태그 `pre-detection_sync`.

### [v6.3 후속] `server_metrics_tz_fix` — server_metrics collected_at 타임존 INSERT 실패 수정 (2026-07-31)

> ★ **동일자 `datetime_unification`(상단)으로 상위 통일됨** — `_to_naive_kst` 는 이제 `to_utc`(UTC) 위임, 컬럼은 timestamptz, 저장 UTC / 출력 +09:00. 아래는 최초 국소 수정 이력(보존).

> 기존 버그(배포 무관): `POST /api/servers/{id}/metrics` 에 tz-aware(KST +09:00) `collected_at` 을 보내면 asyncpg 가 naive 컬럼(`TIMESTAMP WITHOUT TIME ZONE`)에 aware 값을 못 넣어 500 → CPU/RAM/디스크 메트릭 저장 통째 실패.

- `app/routers/server_metrics.py`: `_to_naive_kst` 헬퍼로 aware `collected_at` 을 KST 벽시계 naive 로 정규화 후 저장(프로젝트 표준 naive-KST 정합, 응답은 `KSTDatetime` 이 +09:00 부여).
- 라이브 재현→수정: aware POST 500 → **201**, DB `collected_at`=`2026-07-31 10:00:00`(naive). `tests/test_server_metrics_tz.py` 4 passed. 롤백태그 `pre-server_metrics_tz_fix`.

### [v6.3 후속] `proxy_settings_typed` — proxy-settings PROXY 서버 전용 강제 (2026-07-31)

> PM 결정: `proxy-settings`(GET/PATCH/PUT)는 기획상 PROXY 서버 전용인데 코드가 모든 server_id 를 받아 비-PROXY 서버에도 lazy-create 되던 문제.

- `app/routers/proxy_settings.py`: `_get_proxy_server_or_404` 헬퍼 도입 — 대상 서버 카테고리가 `PROXY` 가 아니면 **404**(lazy-create 차단). GET/PATCH/PUT 3곳 공통 적용(§8.8).
- **계약 변경**: 기존엔 모든 서버 유형에서 200/upsert 가능 → 이제 비-PROXY 는 404. 현재 junk(비-PROXY) 설정 0건이라 정리 불필요. → **.NET 소비 클라 통지 대상**.
- 테스트 `tests/test_proxy_settings_router.py` **격리 async 재작성(11 passed)** — 기존 sync TestClient 가 async 라우터의 `get_async_db` 미오버라이드로 실 파일 DB(data/gop.db)를 읽던 **사전 격리 버그**도 함께 해소(리포 표준 = 엔드포인트 함수 직접 태우기).
- 라이브 검증: PROXY(id 17)=**200**, VMS(id 3)=**404**. 5중싱크(코드 + 명세 §8.8·본 체인지로그 + Swagger docstring + 이미지 재빌드 + 컨테이너 healthy). 롤백태그 `pre-proxy_settings_typed`.

### [v6.3 후속] `proxy_mandatory_seed` — 필수 서버 유형 기본 시드 보장 (2026-07-31)

> PM 지적: PROXY 가 기본 서버 시드에서 누락(다른 9종만 시드). 필수 서버 유형은 항상 등록 보장 필요.

- **카테고리**: `DEFAULT_SERVER_CATEGORIES` 에 `PROXY`(프록시 서버, sort_order 10) 추가 → 9종 → **10종**. 카테고리는 유형별 idempotent라 기존 DB 에도 다음 기동 시 자동 등록(§8.5).
- **필수 유형 보장**: `MANDATORY_SERVER_TYPES = {PROXY, VMS, NVR_API, BROKER}` 도입. `create_sample_servers`(+async) 가드를 **전체 count>0 통째 스킵 → 유형 기준 보장** 으로 교체 — 해당 유형에 서버가 하나도 없을 때만 기본 인스턴스 생성(사용자 등록분 존재 시 중복 미생성), 그 외 데모 유형은 `servers` 가 빌 때만 최초 시드.
- **실측**: 재배포 후 기동 seed 로그 `Servers ensured (mandatory +0, demo +0)`(운영 DB 에 PROXY 기존재 → 중복 미생성), 카테고리 10 / 서버 15. 단위 테스트 `tests/test_server_seed.py` **7 passed**(사용자 등록분 중복 방지 케이스 포함), 기존 서버 테스트 회귀 0(사전 44 실패는 `cpu_usage`→`ServerMetrics` 분리 후 stale 테스트로 무관).
- 파일: `app/utils/init_server_data.py`. 5중싱크(코드 + 명세 §8.1·§8.5·본 체인지로그 + 이미지 재빌드 + 컨테이너 재기동).

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| v6.3.2 | 2026-08-03 | **[event_suppression_bulk_delete]** 억제 스케줄 **일괄 하드삭제** 엔드포인트 출하 — `POST /api/event-suppression-schedules/bulk-delete`(events:delete, §6.8.8 신설). soft-cancel(`DELETE /{id}`)만으로는 취소·종료 이력이 목록에 무한 누적되어 정리 수단이 없던 문제 해소. **안전장치**: 활성(active)·예정(pending)은 삭제하지 않고 `skipped_ids` 분리 보고(먼저 취소 필요), 존재하지 않는 id 는 `not_found_ids`. **동시성**: `SELECT ... FOR UPDATE` 잠금 후 status 재판정(TOCTOU 오삭제 차단). 삭제 건별 `SUPPRESSION_SCHEDULE/DELETED` 감사 기록. 행 + junction(`event_suppression_target_devices`/`_groups`) cascade 제거(복구 불가). 기존 억제 게이트 절 §6.8.8→**§6.8.9** 재번호. `PERMISSION_MAP` 등재(중앙 매트릭스 커버). Swagger `info.version` 6.3.1→**6.3.2**. 커밋 `82ed70d`. ※ 코드는 2026-08-01 작성됐으나 명세·이미지·컨테이너 미반영(5중싱크 3/5 위반) 상태였던 것을 본 차수에서 완결. |
| v6.3.1 | 2026-07-31 | **버그픽스+기능 릴리즈** — **[proxy_mandatory_seed]** PROXY 기본 시드 누락 보강(기본 카테고리 9→10 + 필수 유형 보장 `{PROXY,VMS,NVR_API,BROKER}` 유형 기준: 해당 유형 서버 0개일 때만 기본 생성). **[proxy_settings_typed]** `proxy-settings`(GET/PATCH/PUT) **PROXY 서버 전용 강제**(비-PROXY 404 + lazy-create 차단, **계약 변경**). Swagger `info.version` 6.3.0→**6.3.1**. 라이브 검증(PROXY=200 / VMS=404 / seed `mandatory +0`), `tests/test_server_seed.py` 7 + `tests/test_proxy_settings_router.py` 11 passed. 커밋 `7ee1941`·`cbf63bd`. **[server_metrics_tz_fix]** collected_at aware→naive-KST(asyncpg 500 해소). **[settings_config_enum]** enum SETTINGS 보강(세션설정 500 자가치유, v65). **[detection_sync 기능]** 탐지 UPDATE/DELETE→`SYNC_DETECTION`@`all.sync.detection` 발행(INSERT 미발행·PTZ 회전후 썸네일 재수신)+`DetectionDetail` frame_width/height. 커밋 `735ae5b`. |
| v6.3 후속 | 2026-07-21 | **[grant_enforcement_hardening]** GIS 서버측 집행 분석(`Grant_Enforcement_Server_Analysis.md`) 검토 → 권한부여(grant) 시간기반 집행 하드닝. **API 계약 불변(6.3.0 / 129 paths)** — 실제 flip(NATS 활성·default-deny enforce)은 배포 게이트.<br><br>**[Phase 1 검증부채]** 경계초(`valid_until==now`) 삼중 회귀(순수 `grant_status` · sync `_active_grants` · async `_active_grants_async` 정합) · `AUTH_MODE=token` 집행 E2E · `async_db` 격리(운영 DB 무접촉) · async sweep 발행(사용자당 1회 dedup).<br><br>**[Phase 2 통지/집행]** ① per-grant 실시간 만료 통지(`app/services/grant_scheduler.py` — `valid_until` date job→`publish_permissions_changed`, 부팅 재등록) ② 스윕 주기 설정화 `GRANT_SWEEP_INTERVAL_MINUTES`(기본 10) ③ NATS `permissions_changed` 게이트 검증(발행부 기배선) ④ matrix 미등록경로 `MATRIX_DENY_MODE`(off/observe/enforce, **기본 off = 현행 default-allow 보존**).<br><br>**[신규 설정]** `GRANT_SWEEP_INTERVAL_MINUTES` · `GRANT_JOB_HORIZON_HOURS` · `MATRIX_DENY_MODE`.<br><br>**[검증]** 시뮬 128/128 · 유닛 신규 44+ passed · **라이브 A01~A18 10/10 · 계약 10 passed**(재빌드·재기동 후). 커밋 `c10cbbf`/`ccf08a3`/`6fab9bc`/`9d1f30d`. 산출물: PRD·시뮬리포트·GIS회신(`docs/`, 배포게이트로 flip 대기). |
| v6.3 후속 | 2026-07-21 | **[admin_photo_upload]** 관리자용 대상 계정 프로필 사진 API 신설 — `POST`/`DELETE /api/users/{id}/photo` (users:edit + base-ADMIN 상승가드, `_save_profile_photo` magic-byte·orphan 재사용, 감사 `USER_PHOTO_CHANGED`/`USER_PHOTO_DELETED` 행위자≠대상). 관리자 `{id}` 경로 부재로 클라가 `/me/photo` 재사용→토큰소유자(관리자) 사진 오염(2026-07-13)의 서버측 근본 해소. §9.3.1 표·설명·요약 동반 갱신. |
| v6.3 후속 | 2026-07-13~ | **계정 잠금 정책 완성 (`v6.3-lockout_policy`)**<br><br>**[배경]** PM 점검: ① 로그인 실패 횟수 안내 부재 ② 잠금 후 자동해제 부재(영구 잠금) ③ unlock 시 카운트 미리셋(해제 직후 1회 실패로 즉시 재잠금 트랩). 기존엔 임계 잠금(`lockout_threshold`)만 있고 나머지 3부품 결여.<br><br>**[㉰ 자동해제]** 신규 세션설정 **`lockout_duration_minutes`**(기본 30, 0=영구/수동해제만, 1~1440분). 잠금 후 경과 시 로그인 시도로 자동 해제(+카운트 리셋). `GET/PUT /api/settings/session` 노출·편집(§9.8, `seed_if_empty` 자동 시드).<br><br>**[㉯ 잔여 횟수 안내]** 로그인 오답 `401` 에 `"{N}회 중 {X}회 실패, {M}회 남음"` 메시지 + 구조화 **`error.details`**(`failed_count`/`threshold`/`remaining`/`locked`). 잠긴 순간엔 "약 N분 후 자동 해제" 안내. **틀린 이유(id vs pw)는 비노출**, 미존재 계정은 카운트 미노출(계정 열거 방지 유지), `lockout_threshold=0`이면 일반 메시지.<br><br>**[㉱ unlock 리셋]** `POST /api/users/{id}/unlock` 이 `failed_login_count=0`+`locked_at=null`+`lock_reason=null` 리셋 — 재잠금 트랩 제거.<br><br>**[검증]** 3회 실패 메시지/details 정확, 잠김→duration 경과→정답 로그인 **자동해제+성공**, unlock 후 count=0 실측. A01~A18 10/10·계약 10 passed 무회귀. 5중싱크: `settings_service`·`schemas/settings`·`routers/settings`·`auth`·`users` + §9.8 명세 + 재빌드.<br><br>**계정 잠금/해제 감사 (`v6.3-audit_auto_lock`, PRD/plan 프로세스 준수)**: auth.py 로그인의 **자동잠금(브루트포스 임계도달)·자동해제(타이머)**를 `audit_logs`에 `USER_LOCKED`/`USER_UNLOCKED`(시스템 행위자 `actor_id=None`·`actor_login_id="(system)"`·`actor_name="시스템(자동)"`, 대상=해당 계정)로 기록. 기존 auth.py `log_action` 0건 → 수동 lock/unlock만 감사되던 **비대칭 해소**. best-effort(`try/except`, 감사 실패해도 로그인/잠금 집행 불변), 정상 로그인엔 미발생. 산출물: `docs/prds/audit-auto-lock-unlock-prd.md`·`docs/plans/audit-auto-lock-unlock-prd-plan.md`. 실측 `USER_LOCKED`/`USER_UNLOCKED` row 생성 + A01~A18 10/10·계약 10 passed·정상로그인 audit 미발생.<br><br>**프로필 사진 CRUD 정합화 (`v6.3-profile_photo_crud`, Track B)**: PM 지적("프로필 사진 CRUD 문제"). **①[P0]** `AccountUserSelfUpdate.photo_url` validator 허용 상대경로 `/static/profiles/`(StaticFiles 미마운트=실존X) → 실제 서빙 경로 **`/api/users/photo/`** 로 정정 — 서버가 응답에 채우는 default(`/api/users/photo/default.png`)를 클라가 `PUT /me` 로 되받으면 **422** 나던 자가모순 봉합. **②[P1-D]** **`DELETE /api/users/me/photo`** 신설(파일 제거+`photo_url=null`→default 아바타 복귀, idempotent). **③[P1-U]** 재업로드 시 옛 파일 **orphan 제거**(`_delete_photo_file` — default/외부URL/traversal 방어, PII 무한적재 차단). **④[P2]** `content_type`(클라 위조 가능) 대신 **Pillow magic-byte**(`_detect_image_ext`)로 실제 이미지 검증. 파일 `schemas/user.py`·`routers/users.py` + 단위테스트 `tests/test_profile_photo_crud.py` **14/14 PASS**(TDD Red→Green). Swagger 자동반영(`me/photo`=post+delete). 5중싱크: 2코드 + §9.3 표·주석·부록 목록 + 재빌드.<br><br>**NATS DBApi 발행 정합 완성 (`v6.3-nats_sync_completion`, PRD/plan 프로세스 준수)**: `docs/DBApi_API서버.md`(NATS 발행 명세, 진실원본 Gop_Message_Broker v1.5) 대비 **db_triggers+db_monitor 5건 갭 정합**. ① SYNC_PRESET body에 `camera_id` 추가(camera_presets/rois) ② SYNC_CAMERA_SETTING `resource_id`→**`camera_id`** ③ SYNC_PROXY_SETTING `resource_id`→**`server_id`** (②③은 `camera_settings.id≠camera_id`·`proxy_settings.id≠server_id` 실버그, **기존 NATS 소비자 계약 변경** → 클라 통지 `docs/GOP_Server_API_nats_sync_completion_NOTIFY.md`) ④ **SYSTEM_EVENT 신설**(system_events INSERT 트리거→신규 `gop_event` 채널→`all.event.system` Full-DTO, `acknowledged`=is_acknowledged, enum→text) ⑤ **ENCLOSURE_METRICS 신설**(db_monitor 주기 태스크 `ENCLOSURE_METRICS_INTERVAL` 기본10s→`gis.enclosure-metrics`, measured_at=created_at). db_monitor `on_notify` body **통과 일반화**(하드코딩 resource_id 제거). 실측 NATS 수신 6종(위 5종 + SYNC_SERVER 무회귀) subject+body 문서 **100% 일치**. 5중싱크: `app/db_triggers.py`·`db_monitor/main.py`·`docker-compose.yml` + db-monitor/api-server 재빌드. 산출물 `docs/prds/nats-dbapi-sync-completion-prd.md`·`docs/plans/nats-dbapi-sync-completion-prd-plan.md`. |
| v6.3 | 2026-07-13 | **버전 승격 — `v6.0` 후속 누적분(21 topic + 07-08~13 보안 하드닝)을 `v6.3` 으로 확정**<br><br>**[배경]** 2026-07-05 v6.1/v6.2 태그 사고 후 "임의 minor 승격 금지 + `v6.0-{topic}` 누적" 규칙을 유지했으나, 8일간 21 topic(리포트 정합화·RBAC 매트릭스·보안 하드닝 3클러스터) 누적으로 단일 `v6.0` 표기가 실작업량과 괴리 → PM(차장) 결정에 따른 **의식적(비-임의) 승격**. v6.1/6.2 는 07-05 사고분이라 건너뜀.<br><br>**[5중 싱크]** Swagger `info.version` `6.0.0`→**`6.3.0`** + 명세서 헤더/본 행 + `main.py` description + `CLAUDE.md` yaml `6.3.0` + README 배지 + git 태그 `v6.3` + 컨테이너·이미지 재빌드. 산발 드리프트(CLAUDE.md `6.1.0`/session-context `v6.1`) 동시 해소.<br><br>**[포함 작업]** = 아래 `v6.0 후속` 롤링 항목 전체(리포트·인증계정·API계약·안정성·배포) + `[보안 하드닝]`(session_token_jti·migration_tracking·login_rate_limit·review0710 P0/P1·audit_logs_authz) + `[역할 표기 정합]`.<br><br>**[규칙 갱신]** `release/v6.3` 브랜치를 현 HEAD 에서 신규 컷하여 **canonical 로 승격**(branch 명=버전 일치, `release/v6.0` 은 frozen 보존). 향후 후속 태그는 `v6.3-{topic}`. |
| v6.0 후속 | 2026-07-04~12 | **clone 배포·운영 안정화 — `release/v6.0` 위 소분 태그(`v6.0-{topic}`) 누적**<br><br>**[리포트]** `report_fixes`(그리드 컬럼 확장·JSON preview↔HTML/PDF 필터 통일·라벨 통일·N+1 제거) / `report_lifecycle_persistence`(startup 재조정 PENDING·GENERATING→FAILED, PDF named volume 영속화, 파일 소실 시 **HTTP 410 `PDF_FILE_MISSING`**) / `report_progress_perf`(응답 `progress_pct`·`progress_stage`·`progress_updated_at` 3필드 + stall 워치도그(60s no-progress→FAILED) + SQL 집계 이관 + `GET /generations/{id}/detail.csv?type=…` 8 grid 신설) / `report_date_range`(`POST /generate`에 `start_date`·`end_date` Optional 커스텀 범위, `period_type="custom"`, 366일 상한).<br><br>**[인증·계정]** `auth_mode_secure_default`(docker-compose `AUTH_MODE` 기본 public→**token**, public 시 부팅 WARN + staging/prod 거부) / `account_rbac`·`account_managers_expand`(ADMIN Static seed 9종: admin/m_manager/vms_manager/popup_manager/CameraManager/BroadcastingManager/QLiteLampManager/NVRManager/EnclosureManager, pw sensorway1) / `role_seed_normalize`(role 규칙 v5.3 2종(ADMIN/USER) 시드·기존 데이터 재적용 — 모델 default VIEWER→USER + **startup 자동 마이그레이션 v62**로 옛 OPERATOR/VIEWER/MAINTAINER → USER) / `rbac_matrix_gate`(계정/그룹/세션/grant조회/세션설정 **`require_admin`→`require_perm` 매트릭스 전환** — `role=ADMIN` 만 bypass, USER 는 등급∪grant 매트릭스로 동작·만료 시 복귀. 상승 가드로 `role`/`group_id` 변경·grant 부여/회수·그룹 permissions 편집·`role=ADMIN` 대상 변경은 base-ADMIN 전용 잠금. §9 RBAC 노트 갱신, Live E2E 10/10 + `test_users_escalation_guards` 7 passed).<br><br>**[API 계약 — 응답 스키마 완화]** `servers_port_response_relax`(`ServerResponse.port` `ge=1`→`ge=0` + 목록 fault tolerance) / `users_role_response_relax`(`AccountUserResponse.role` Enum→str) / `response_schema_audit`(**전 `*Response` 스키마 Enum 지뢰 21건 전수 완화** — String 컬럼 + strict Enum 응답이 옛/임의 값에서 목록 500 나던 것 원천 차단. `report_type`·`period_type`·`status`·`type_event`·`result`·`reason`·`action`·`failure_reason`·`logout_reason`·`action_status`·`actor_role` 등 응답 필드 Enum→str, 요청 스키마는 strict 유지). **클라 영향 없음**(응답 JSON 값 동일, Swagger enum 표시만 사라짐).<br><br>**[안정성 버그]** `clone_deploy_bugfix`(신규 PC 6버그: **startup 자동 마이그레이션**(create_all이 기존 테이블에 컬럼 추가 못하는 문제 — `progress_pct` 등), connections `selectinload(DeviceGroupMapping.group)`(greenlet_spawn), event_statistics 4 endpoint tz-aware→naive KST 정규화, audit_role 완화) / `force_logout_tz_fix`(**세션 강제 로그아웃 500 수정** — `user_sessions.logged_out_at` tz-aware(Asia/Seoul)를 naive DateTime 컬럼에 넣어 asyncpg DataError → `DELETE /api/user-sessions/{id}` 전체 500 + 롤백으로 토큰도 안 막히던 이중 실패. `.replace(tzinfo=None)` 정합. 검증: 강제로그아웃 200 + 이후 토큰 401).<br><br>**[배포·인프라]** `rename_pids`(컨테이너/이미지 `api-test-*`→**`pids-api-*`**, 볼륨·데이터 보전) / `cert_installer_fix`(HTTPS 인증서 인스톨러 6버그, Dockerfile CMD 인증서 없으면 **fail-fast** + `ALLOW_HTTP_FALLBACK` opt-in) / `installer_ps2exe_path_fix`(PS2EXE EXE에서 `$PSScriptRoot` 빈 문자열 → `MainModule.FileName`로 근본 수정) / `bootstrap_automation`(신규 PC **1-Click** `bootstrap.ps1`: UAC 상승+인증서 발급+docker up+healthy 대기).<br><br>**[통지 문서]** `docs/GOP_Server_API_*_REPLY.md` 6건(servers_port0 / users_role / clone_deploy_bugfix / installer_ps2exe / response_schema_audit + report_updates_NOTIFY).<br><br>**[보안 하드닝 (2026-07-08~12)]** `session_token_jti`(E1/P1-10: `user_sessions.token`/`refresh_token` 원문 JWT→**jti 만 저장** + `refresh_expires_at` 컬럼, 원문 유출 표면 제거 + decode 없는 폐기, 마이그레이션 v64) / `migration_tracking`(DB-01/E3: `schema_migrations` 추적 테이블+checksum + **fail-fast** — 조용한 스키마 드리프트 기동 차단) / `login_rate_limit`(E4/P1-09: 로그인 IP 슬라이딩윈도우 300s/10회 초과 **429**, 무차별 대입 방어) / `test_reproducibility`(E2: `tests/` un-gitignore + conftest 운영DB 가드(비-sqlite `DATABASE_URL` 은 `ALLOW_DB_TESTS=1` opt-in 요구) + `requirements-test.txt`) / `review0710_p0`(**민감 GET 무인증 노출 차단** — `config-change-logs`/`system-events`/`event-statistics` GET 이 permission_map 미등록으로 `enforce_matrix` default-allow 를 타 무토큰 200 이던 것에 route-level 가드 부착(config-change=`require_perm(audit_logs,view)` strict, system-events·event-statistics=`require_perm_optional(events,view)`) + refresh 회전 시 **옛 access jti 도 블랙리스트**(orphan 토큰 제거)) / `review0710_p1`(logout 폐기를 `revoke_session_family` 로 통일(access static TTL→stored exp, logout·refresh·revoke·force_logout 동일 원천) + api-server `nats_external` 배선·`NATS_REVOKE_ENABLED` 게이트(기본 false, dormant) + **public GET allowlist 계약 테스트**(`tests/test_public_get_contract.py` — 무토큰 2xx 미노출 못박음, 실측 105 GET 중 공개 4건)).<br><br>**[역할 표기 정합 (2026-07-12)]** §4.5 `EnumUserRole` **5종→2종(ADMIN/USER)** 정정(v5.3 코드-명세 정합 지연분) + 잔존 폐기역할(MAINTAINER/OPERATOR/VIEWER/GUEST) 현행화: 사용자 역할 필터·감사/설정 로그 예시 payload → ADMIN/USER, 권한 컬럼 audit-logs·config-change-logs 공히 `ADMIN∨audit_logs:view`(`audit_logs_authz`: audit-logs GET 을 전 인증 사용자→`require_perm(audit_logs,view)` 로 **강화**, 감사도메인 인가 일관화).<br><br>**원칙**: Swagger `info.version`은 `6.0.0` 유지(release/v6.0 브랜치). 후속은 **minor 승격 없이 `v6.0-{topic}` 태그로 누적**(브랜치-태그 명명 규칙). |
| v6.0 | 2026-07-03 | **Async 대전환 — SQLAlchemy 2.x + asyncpg + AsyncSession 도입 (문서 A-7 근본 해결책 2)**<br><br>**[스코프]** 41 라우터 × 397 db.query() 호출 → `await db.execute(select())` 전환. Dual-stack 원칙(sync 병존) → 라우터별 점진 마이그레이션 안전 롤아웃. 총 12 Phase (P0~P11).<br><br>**[P0 Foundation]** asyncpg 드라이버(기존 requirements) + `create_async_engine` + `AsyncSessionLocal` + `get_async_db` 병존 도입. `_to_async_url()` postgresql:// → postgresql+asyncpg:// 자동 변환. sync engine 병존 유지 (라우터 마이그레이션 완료까지).<br><br>**[P1 Relationships]** 22 lazy='dynamic' hazards 사전 제거 (Tidy First, sync 상태). 6 라우터 × 28 changes.<br><br>**[P2 Middleware]** v5.4 to_thread + fire-and-forget 유지 결정 (batch queue v6.1 이월).<br><br>**[P3 Services dual-stack]** audit_service.log_action_async, grant_service.run_grant_sweep 내부 async, session_sweep_service.find_expired_sessions_async, api_logs_sweep_service 내부 async, token_blacklist_service.is_blacklisted_async/add_to_blacklist_async 병존. 스케줄러 3종 async 전환.<br><br>**[P4 Auth/Security Critical]** `get_current_account_user_async`, `_optional_async`, `require_role/admin/perm/perm_optional_async`, `_effective_allows_async`, `_active_grants_async`, `effective_permissions_payload_async` 11종 신설. matrix_enforcer.enforce_matrix 내부 async + `_resolve_user_from_request_async`. bcrypt CPU-bound → `hash_password_async`/`verify_password_async` (asyncio.to_thread 래퍼).<br><br>**[P5~P8 라우터 전환]** 39 라우터 (100% 커버 — __init__.py 제외):<br>&nbsp;&nbsp;• **P5 Simple (5)**: audit_logs, config_change_logs, event_mappings, tracking, logs<br>&nbsp;&nbsp;• **P6 Medium (15)**: camera_presets/settings, enclosures, file_groups, grants, lamps, proxy_settings, server_categories, server_metrics, settings, user_groups + enclosure_metrics, servers, system_events, thumbnails. settings_service/config_log_service dual-stack 추가.<br>&nbsp;&nbsp;• **P7 Device Polymorphic (4)**: controllers, sensors, speakers, cameras (selectinload preload).<br>&nbsp;&nbsp;• **P8 VeryComplex (15)**: detections, detection_logs, malfunctions, connections, actions (**selectin_polymorphic**(Event, [Detection/Malfunction/Connection]) + selectinload(Event.device).**selectin_polymorphic**([Sensor/Camera/Controller/Speaker/Enclosure/Lamp])), event_mapping_cameras/lamps/speakers (bulk flush), device_groups (**selectin_polymorphic**(Device)), rois, xypoints, users (bcrypt async), user_sessions, reports (report_service sync 병존 — v6.1 이월), event_statistics.<br><br>**[P9 init/main/Scheduler]** `app/main.py` lifespan startup에서 `initialize_database()` + `apply_triggers(engine)`를 `asyncio.to_thread`로 래핑 → 이벤트루프 자유. 스케줄러 3종 (Grant/Session/API logs sweep) P3 async 완료. init_*.py 내부 async 완전 전환은 v6.1 이월.<br><br>**[P10 통합 검증]** 50 GET no-param endpoints admin 토큰 스캔 → **500-FAIL 0** / success 46 / 422(필수 param) 4 / timeout 0. 전건 무결.<br><br>**[P11 5중 싱크]** 코드 async 완결 + Swagger `info.version` 5.4.0 → **6.0.0** + 명세서 v6.0 표(본 행) + CHANGELOG [v6.0] + Docker image 재빌드 + Container healthy + 태그 v6.0.<br><br>**[성능/안정성]** 이벤트루프 블로킹 원인 ② 제거 (문서 A-7). 매 요청 sync 커넥션 획득 절감. MissingGreenlet 회피 (polymorphic eager load 강제). postgres 커넥션 active=1 idle=4 안정.<br><br>**[v6.1 이월]** report_service.py 내부 async + report_master_builder + report_html_renderer 완전 async, init_*.py 5개 내부 async, APILoggingMiddleware batch INSERT queue, pytest 스위트 async fixture 복구, token_blacklist TTL 캐시 → Redis 분산 캐시.<br><br>**[하위 호환]** Dual-stack 유지 — 기존 sync 시그니처 전건 유지. 신규 라우터 작성 시 async 버전 사용 권장. |
| v5.4 | 2026-07-03 | **하루 1버전 통합: ① GET /api/grants 신설(클라 REQ) + ② P0 hotfix 6건(Workflow 393 시나리오) + ③ 클라 결함 5건 대응 + ④ AUTH_MODE public → token (User/Admin 2계층 인가 강화 발효)**<br><br>**[① 신설 — GET /api/grants]** 클라(.NET GIS) 요청서 `docs/REQ_Server_Grants_ListAll.md` 대응. `Depends(require_admin)` + 쿼리 6종(page/size/user_id/group_id/status/active_only). GrantResponse에 `user_login_id`+`user_name` 필드 추가(비정규화, UserLabel 태깅 로직 제거 가능). Swagger 5.3.5 → **5.4.0**. 12/12 PASS.<br><br>**[② P0 hotfix 6건]** Workflow 393 시나리오(30 fail) 결과 발견 회귀 봉합:<br>&nbsp;&nbsp;• **P0-1** `/reports/preview/{id}` **무인증 PII 창구 삭제** — `@app.get` 우회 + `include_in_schema=False` + logging 제외 3중 은폐 해체. `/api/reports/preview/{id}` 라우터로 이관(인증 강제).<br>&nbsp;&nbsp;• **P0-2** `AccountUserCreate/Update.role` `str` → **`EnumUserRole`** — v5.3 Phase 2 회귀 봉합. OPERATOR 등 삭제 role 422 차단, DB 오염 재발 차단.<br>&nbsp;&nbsp;• **P0-3** `DetectionEventCreate.type_event` `str` → **`EnumEventType`** — 'Bogus' 등 임의값 422 차단.<br>&nbsp;&nbsp;• **P0-4** Event Update 3종 `model_config = ConfigDict(extra='forbid')` — v4.8 Phase 12 docstring 의도 → 실제 코드화. PATCH 표면 방어 완성.<br>&nbsp;&nbsp;• **P0-5** `POST /api/reports/generate` template_id FK **raw 500 → 404 명시 매핑**. psycopg2 스택트레이스 노출 차단.<br>&nbsp;&nbsp;• **P0-6** `Server.port` `Field(ge=1, le=65535)` 검증.<br><br>**[③ 클라 결함 지적 5건 대응]** ① preview PII(P0-1로 해결), ② **reports verb RBAC 서버 집행** — `app/security/permission_map.py`에 reports view/edit/delete 매트릭스 등록, ③ **DELETE /api/reports/generations/{id}** 신설(PDF best-effort 삭제 + DB row 삭제), ④ **작성자 스냅샷** — POST /generate에서 `generator_id/name/department` 실적용, ⑤ **severity_filter 실동작** — `build_master_data`에 인자 추가, system_events 4개 쿼리에 `severity::text IN (...)` 화이트리스트 필터 적용.<br><br>**[④ AUTH_MODE 전환]** `.env` `AUTH_MODE=public` → **`token`**. matrix_enforcer 활성. Bearer 토큰 필수화. **User/Admin 2계층 인가 강화**: ADMIN=SuperUser(모든 경로 통과), USER=UserGroupGrant → UserGroup.permissions 매트릭스 게이팅. 미인증 요청 401 통일.<br><br>**[실측 검증]** 무인증 `/api/users`·`/api/reports/preview/7` → **401** / 이전 `/reports/preview/7` → **404** (엔드포인트 삭제) / admin 토큰 → 200 / `role=OPERATOR` 계정 생성 → **422** / `type_event=Bogus` → **422** / `template_id=99999` → **404** / `port=70000` → **422** / PATCH detection `device_id=99999` → **422** / DELETE unknown generation → **404**.<br><br>**[Notify 클라]** .NET 3종(GIS/Ironwall/RtspViewer)이 이미 Bearer 부착 완료된 상태여야 함(AUTH_MODE=token 전환됨). LoadAllGrantsAsync 계정 순회 → 단일 `GET /api/grants` 호출로 교체. UserLabel 태깅 로직 제거. 클라 UI 결함 대응 주석/우회 로직 5개 제거 가능.<br><br>**[v5.4 후속 — 클라 지적 계정 항목 4건 (같은 날 통합)]** v5.4 태그 직후 클라팀 지적 대응:<br>&nbsp;&nbsp;• **P0-B** `PUT /api/users/{id}` group_id=null 해제 지원 — `is not None` → `model_fields_set` 판정으로 변경. 요청 body에 명시적 null 포함 시 구성원 해제 실동작.<br>&nbsp;&nbsp;• **P1-A** UserSession sweep 스케줄러 신설 (`app/services/session_sweep_service.py`, 5분 간격) — `expires_at < now AND is_active=true` 세션에 `is_active=false + logout_reason=EXPIRED` 마킹.<br>&nbsp;&nbsp;• **P1-B** SUPERSEDED 핸들러 — `POST /api/auth/login`에서 동일 계정 활성 세션 자동 evict: (1) `is_active=false + logout_reason=DUPLICATE + logged_out_at`, (2) 각 access jti → `token_blacklist` 등재, (3) `publish_session_revoke()` NATS 발행(best-effort). 결과: 이전 로그인 토큰 즉시 401.<br>&nbsp;&nbsp;• **P0-A** `GET /api/audit-logs?action_status=…` 500 재확인 — v5.4 AUTH_MODE=token 이후 정상(200). 클라 콘솔 500은 AUTH_MODE 이전 상태 산물로 판단.<br><br>**[v5.4 후속 — GOPDB 통합 원인분석 대응 (문서 A-7 조치 부분 반영)]**<br>&nbsp;&nbsp;• `/health` 강화 — DB `SELECT 1` 실행 + 실패 시 503 반환 (silent failure 감지, Docker healthcheck unhealthy 발효).<br>&nbsp;&nbsp;• **APILoggingMiddleware 이벤트루프 블로킹 해소** — 요청당 sync `SessionLocal()` + `commit()` → `asyncio.to_thread`로 threadpool 이관. 이벤트루프 정지 방지(문서 A-7 #1).<br>&nbsp;&nbsp;• **카메라 N+1 폭발 해소** — `GET /api/devices/cameras` 목록 응답에서 `_get_device_groups_nested`를 카메라마다 호출하던 것을 배치 조회로 대체(전체 매핑 1회 조회 → in-memory dict). 문서 A-7 #3.<br>&nbsp;&nbsp;• **api_logs TTL sweep** — 일 1회(정오) 30일 초과 row 삭제 스케줄러 추가. 문서 A-7 #6.<br>&nbsp;&nbsp;• **async def → def 전환 / async 세션** — 오늘 스코프 외. **v6.0 별도 차수**로 이월(라우터 39개 × 쿼리 406곳 규모, 4~5일 소요).<br><br>**[v5.4 후속 (2) — 클라 REQ Reports verb-RBAC 서버 집행]** 요청서 `docs/REQUEST_Reports_Verb_RBAC_Enforcement.md` 대응. v5.4 P2-2에서 `PERMISSION_MAP`에 reports 10경로 등록했으나 중앙 `enforce_matrix`가 실제 게이팅 못함(perm=None default-allow) → 무권한 USER가 보고서 생성/삭제/PII 조회 가능. **A안 채택 (controllers.py 검증된 패턴 재사용)**: `app/routers/reports.py` 15개 endpoint 전건에 `dependencies=[Depends(require_perm_optional("reports", verb))]` 부착.<br>&nbsp;&nbsp;• **§4.2 필수 (9개)**: edit 3(POST /templates, PATCH /templates/{id}, POST /generate), delete 2(DELETE /templates/{id}, DELETE /generations/{id}), view 4(GET /preview/{id}, /generations/{id}/download, /generations/{id}/preview, /generations/{id}/preview-page). 요청서 §4.2의 PUT /templates/{id}는 코드 미존재 → 9개.<br>&nbsp;&nbsp;• **§4.3 선택·권장 (6개 view)**: /components, /status, /templates, /templates/{id}, /generations, /generations/{id} — 클라 UI 게이팅과 일관성 완결.<br>&nbsp;&nbsp;• **총 15개 endpoint**: edit 3 + delete 2 + view 10. `require_perm_optional`이 ADMIN bypass + jti 블랙리스트 + 403 응답 처리.<br>&nbsp;&nbsp;• **실측 (요청서 §6 완료 기준 준수)**: 무권한 USER(group_id=null) 토큰 → 15개 endpoint 전건 **403**. ADMIN → 통과(bypass). |
| v5.3 | 2026-07-02 | **하루 일괄 — Legacy User 모델 완전 삭제 + AccountUser 통일 (GIS 팀 요청 대응, 14/14 PASS)**<br><br>**[배경]** GIS 팀 요청 — User와 AccountUser 혼용 정리. Legacy users 테이블 admin 1건 + FK 참조 0건 확인. v5.1 FR-SV-08 잔존 소진.<br><br>**[Phase 2 라우터 sweep]** 30 파일에서 `get_current_user_optional` → `get_current_account_user_optional` (Device CRUD 7 + Event 4 + EventMapping 4 + Server 4 + DeviceGroup 3 + CameraPreset 3 + Log 3 + tracking/grants/settings 3).<br><br>**[Phase 3 Dead code 삭제]** auth.py Legacy 함수 3건(get_current_user + get_current_user_optional + login_oauth2) + models/user.py `class User` + schemas/user.py UserCreate/UserResponse + init_db.py create_admin_user() + tests/conftest.py User import.<br><br>**[Phase 4 DB]** `v56_drop_users_table.sql` 신설 + FK 파괴 0 확인 DO block + DROP TABLE users CASCADE. reverse migration 사전 작성.<br><br>**[Phase 5 실측 14/14 PASS]** admin login + /me + tracking(2) + users + user-groups + audit-logs + reports + servers + user-sessions + cameras + actions + detections + controllers + sensors 모두 200. Swagger UserResponse/UserCreate/oauth2 endpoint 제거 확정. AccountUserResponse 유지.<br><br>**[Phase 6 5-sync]** Image rebuild + Swagger version 5.2.0 → **5.3.0** + API Version 5.3 + Container Up healthy.<br><br>**[안전점/롤백]**: `pre-legacy-user-removal` (v5.2 마감 시점). 롤백 = `git reset --hard pre-legacy-user-removal` + `psql < v56_reverse.sql`.<br><br>**[Phase 2] Role 축소 (5→2) + 등급 그룹 → Preset Group 정리 (하루 1차수 묶음 원칙 준수, 같은 날 통합)**<br>차장님 지시 대응 — Admin과 User로만 남기고 기존 등급은 Preset 권한 그룹으로. v5.2 R10① 정신(role은 특권 라벨, 실 권한은 group_id) 스키마 완성.<br>**[Enum 축소]** `EnumUserRole` 5종 → 2종(ADMIN/USER). Legacy 4종(MAINTAINER/OPERATOR/VIEWER/GUEST)은 Preset 권한 그룹으로 이관.<br>**[DB 마이그레이션 v57]** account_users.role 값 UPDATE(admin 외 → USER, 7건), user_groups id=11/12/13 rename(→Preset-유지보수자/운영자/조회자), id=10 ADMIN 그룹 + id=14 GUEST 그룹 삭제(사용자 0명 검증), admin.group_id=NULL.<br>**[코드]** enums.py + init_db.py `ensure_role_permission_groups()` → Preset 3건 시드 + init_sample_data.py role="USER" 통일. Swagger version 5.3.0 → **5.3.5**.<br>**[실측 6/6 PASS]** admin login 200 + role=ADMIN, gop_maint/op/viewer/op_tester/monitor2 각 login 200 + role=USER + 각자 group_id 배정 매트릭스 유지(gop_maint: Preset-유지보수자 10 modules 매트릭스 유지, monitor2: 관제팀 8 modules 매트릭스 유지). Swagger EnumUserRole.enum=["ADMIN","USER"] 확정. 14 endpoint 응답 코드 유지.<br>**[클라 안내]** `docs/GOP_Server_API_v5.3_Phase2_Role_Simplification_NOTIFY.md` — Enum 축소 매트릭스 + 그룹 rename + role 조건 코드 조사 요청 + JWT payload Before/After + FAQ + 롤백 절차.<br>**[안전점]** `pre-role-simplification` @ (Phase 2 진입 직전). 롤백 `git reset --hard pre-role-simplification` + `psql < v57_reverse.sql`. |
| v5.2 | 2026-06-30 | **하루 일괄 — 서버 안정성 hotfix ("가끔 죽는" 원인 추적 + 즉시 5건 적용, Workflow 7 agent 감사 / 5/5 PASS)**<br><br>**[차수 배경]** 차장님 보고 "API 서버가 가끔 죽는데 원인 모름" → **Workflow 7 agent 정밀 감사**(498K token / 6.5분, 6 dimension A~F) 즉시 발주. 결과 **Health Score 58/100**(A 컨테이너 이벤트 55, B 메모리 누수 62, C DB 연결 72, D async 패턴 42, E 시작 의존 62, F 엔드포인트 스트레스 55 — 총 발견 42건 / 추정 죽음 원인 13건). 동시에 호스트 Windows Event 로그 분석에서 **Kernel-Power Event ID 41 + 6008**(unexpected shutdown) 패턴 확정: 2026-06-29 09:30 / 06-24 08:38 / 06-20 09:55 — 5~9일 간격 비정상 종료, 형제 4 컨테이너 09:32 KST 일제 재기동 = **Docker daemon 단위 재시작**(컨테이너 개별 crash 아님). 본 차수는 **TOP 5 죽음 원인**(high confidence) 중 즉시 적용 가능한 5건을 묶어 hotfix, 코드 광범위 수정이 필요한 항목(bcrypt async / APScheduler 청소 / 미들웨어 비동기 큐 등)은 **v5.3+ 별도 PR 권고**로 분리.<br><br>**[TOP 5 죽음 원인 (high confidence)]**:<br>- ① **async login 안 sync bcrypt** — 동시 30건 요청 4170ms 270배 폭증 + CPU 95% pin (`auth.py:303, 609` / `users.py:184`) → bcrypt CPU bound을 async 핸들러에서 직접 호출, 이벤트 루프 stall<br>- ② **호스트 C: 99% 디스크** — Docker images 99GB + build cache 45GB 누적 → 로그 쓰기/이미지 풀 실패로 daemon 불안정<br>- ③ **★본 세션 v5.1 자가 버그**: `force_logout_all_user_sessions` 벌크 핸들러 `add_to_token_blacklist` kwarg `expires_in`(실제 시그니처는 `expires_at`) → `TypeError 500` (`user_sessions.py:131, 146`). v5.1에서 단건 980abbc 패턴은 정상이나 벌크 경로만 누락<br>- ④ **PG `statement_timeout=0` + `idle_in_transaction_session_timeout=0`** — runaway tx가 connection을 무한 점유, 풀 고갈<br>- ⑤ **APILoggingMiddleware 매 요청 DB 세션 신규 생성** — 요청당 별도 SessionLocal(), 정상 풀 2배 소모<br><br>**[Fix-1 / 디스크 회수]** — `docker builder prune -af` + image prune 일괄 → **45.63GB + 444MB 회수**, C: 사용률 98.1% 까지 하강(이전 99% 임계). docker system df `Build Cache 0B` 확인(이전 45.63GB). ★ 정기 cron(주 1회)는 v5.3+ Deferred (별도 PR 권고).<br><br>**[Fix-2 / v5.1 자가 버그 fix — 투명성 명시]** — `app/routers/user_sessions.py:131, 146` 벌크 force_logout 경로 `expires_in=...` → `expires_at=...` 정정(단건 980abbc 패턴과 시그니처 일치). settings TTL(`SECURITY_ACCESS_TOKEN_EXPIRE_MINUTES` / `SECURITY_REFRESH_TOKEN_EXPIRE_DAYS`) 기반 `datetime.utcnow() + timedelta(...)` 계산식 통일. 실측: 벌크 force_logout 호출 **200 OK** + `token_blacklist` `reason='FORCE_LOGOUT_BULK'` 등록 확인. **v5.1 PRD 자체에 명시된 reason 라벨은 정상, kwarg만 누락된 회귀**(LIVE 직전 발견).<br><br>**[Fix-3 / PG 트랜잭션 타임아웃]** — `ALTER DATABASE gop SET statement_timeout='60s'` + `ALTER DATABASE gop SET idle_in_transaction_session_timeout='5min'`. 실측 `SHOW statement_timeout` → **60s**, `SHOW idle_in_transaction_session_timeout` → **300s**. runaway tx가 connection을 무한 점유하던 1순위 죽음 경로 차단(특히 db_monitor NATS callback 내 DB 연산 실패 시 미회수 잔존 tx).<br><br>**[Fix-4 / Docker 로그 회전]** — `docker-compose.yml` YAML anchor `&default-logging` 도입(driver: `json-file`, options: `max-size: 10m` / `max-file: 3`) + 모든 서비스(api/db_monitor/gis_ingest/postgres/redis/nats)에 `logging: *default-logging` 적용. 실측 `docker inspect ... LogConfig` → `{Type: json-file, max-file: 3, max-size: 10m}` 확인. 미회전 컨테이너 로그가 호스트 C: 잠식하던 경로 차단(이전 컨테이너당 GB 단위 누적).<br><br>**[Fix-5 / Healthcheck 엔드포인트 경량화]** — `docker-compose.yml` api 서비스 healthcheck `/docs`(3.6KB Swagger HTML, 인증 우회·정적 자원 의존) → **`/api/tracking/health`**(약 30B JSON `{"status":"ok"}`, 무인증 / v4.11 추적 라우터에 신설된 무의존 헬스 엔드포인트). 실측 `docker inspect ... Healthcheck.Test` → `curl /api/tracking/health` 확인. 매 30초 healthcheck 비용 100배 절감 + 정적 자원 응답 실패 false-positive 제거.<br><br>**[호스트 절전 가설 확정 / 운영 권고]** — Windows Event ID 41(Kernel-Power) + 6008(Unexpected shutdown) 3건 패턴 확정(2026-06-29 09:30 / 06-24 08:38 / 06-20 09:55). 컨테이너 4종 동시 재기동 = Docker daemon 단위 재시작 = **호스트 절전(슬립/하이브리드 절전) 진입 후 깨우기 실패** 시나리오와 정합. ★ **차장님 PC 절전 비활성화**(제어판 → 전원 옵션 → 절전 안 함 / USB selective suspend off) 운영 권고 — 본 차수 코드 fix는 daemon 재시작 자체를 막을 수 없으므로 **호스트 정책 변경이 단일 가장 큰 영향(High Impact)**. v5.3+ `uptime_watch.ps1` 매분 `docker inspect` 스냅샷 → 재기동 시점 자동 캡처.<br><br>**[실측 검증 5/5 PASS]**:<br>- ① Fix-2 벌크 force_logout 200 OK + `token_blacklist FORCE_LOGOUT_BULK` row 등록 확인<br>- ② Fix-3 `SHOW statement_timeout` → 60s, `SHOW idle_in_transaction_session_timeout` → 300s<br>- ③ Fix-4 `docker inspect LogConfig` → `{max-file: 3, max-size: 10m}` 모든 서비스<br>- ④ Fix-5 `docker inspect Healthcheck.Test` → `curl /api/tracking/health` + 응답 본문 `{"status":"ok"}` 200 OK<br>- ⑤ Fix-1 `docker system df` Build Cache 0B(이전 45.63GB) + C: 사용률 98.1% 하강<br><br>**[안전점/롤백]**: `pre-stability-hotfix` @ `6eced61`(본 차수 진입 직전 HEAD). 롤백 `git reset --hard pre-stability-hotfix`(v5.1 상태 복원, RBAC enforcement는 보존됨).<br><br>**[v5.3+ Deferred (별도 PR 권고)]**:<br>- ⓐ **bcrypt async 전환** (`asyncio.to_thread`) — login + login_oauth2 + password change 3곳 일괄, 동시성 부하 시험(현재 30건/4170ms → 목표 30건/300ms 이하)<br>- ⓑ **APScheduler + cachetools 도입** — `token_blacklist`(만료된 jti) / `api_logs`(90일) / `user_sessions`(만료 세션) / `track_points`(180일) 자동 청소 cron, 보존 정책 PRD 결재 선결<br>- ⓒ **트랜잭션 안전망 표준화** — `get_db()` 의존성 generator에 `rollback` on exception 명시(현재 일부 라우터만 `try/except` 수동)<br>- ⓓ **APILoggingMiddleware 비동기 큐 분리** — 요청당 DB 세션 신규 생성을 background task + 단일 큐 워커로 전환<br>- ⓔ **db_monitor 재시도 + autoheal 컨테이너** (`willfarrell/autoheal`) — healthcheck unhealthy 자동 재기동<br>- ⓕ **uptime_watch.ps1** 매분 `docker inspect` 스냅샷 — 재기동 시점 캡처 + Event ID 41/6008 상관 분석<br>- ⓖ **차장님 PC 절전 비활성화** 운영 권고(코드 외 운영 조치 / High Impact)<br>- ⓗ **events / api_logs / audit_logs 보존 정책**(90일 / 180일 / 영구) PRD 결재 — APScheduler purge 가동 전 보존 기간 합의 필수<br><br>**원칙 준수**: 하루 1차수 묶음 — 본 v5.2는 2026-06-30 단일 차수. **★ v5.1 자가 버그(Fix-2)는 동일 차수에 투명하게 명기**(별도 hotfix 차수로 분리하지 않음 — 원칙: "발견 즉시 동일 hotfix 묶음에 명시"). 추적성: `PRD_Stability_Hotfix.md`(workflow 7 agent 6 dimension 감사 보고서 첨부) + 본 row + `pre-stability-hotfix` 태그 3중 잠금.<br><br>**━━━ [2026-06-30 동일 차수 추가 — .NET 이관 PRD 실행: Force-Logout P1 + Session-Settings P2 + 휴면 RBAC + FR-SV-10 + 5-sync 배포] ━━━**<br><br>**[P1 Force-Logout (FR-SVF-01~12)]** (`f00f7ca`·`4ff9a05`·`785c313`) — logout 시 access+refresh **패밀리 일괄 무효화**(구멍 차단) / JWT **`sid` 클레임**(=UserSession.id) + login·refresh 응답 `data.session_id` 동봉(refresh 시 sid 고정·jti만 회전) / force_logout last-ADMIN 가드 / **per-session NATS revoke**(`sensorway.{unit}.account.{uid}.session.{sid}.revoke`, HMAC-SHA256 서명, 게이트 `NATS_REVOKE_ENABLED=False` 기본 OFF) / revoked 세션 접근 → **401 `error.code=SESSION_REVOKED`**(403 권한부족과 구분). 로컬 27건 PASS.<br><br>**[P2 Session-Settings (FR-SVS-01~06)]** (`73ecc5e`) — `app_settings` 테이블 신설(v55 마이그레이션, startup create_all 멱등) + **`GET`/`PUT /api/settings/session`**(require_admin): 편집 가능 `session_timeout_hours`(1~168)/`refresh_expiration_days`(1~90)/`lockout_threshold`(0 또는 3~20)/`session_enabled`, 읽기전용 `auth_mode`/`jwt_algorithm`(jwt_secret 미노출). auth.py 런타임 만료·잠금임계 적용 + ConfigChangeLog 감사. 로컬 11건 PASS.<br><br>**[휴면 RBAC — FR-SV-04/08 부분]** (`c49f0a4` 구조 헬퍼 → `require_perm_optional` → `9a6624c` 부착) — `require_perm_optional(module,verb)` 신설: **AUTH_MODE=public 무집행(현 동작 100% 보존)**, token 플립 시 활성. 비계정 write **27개**(cameras=`cameras`/sensors·controllers=`devices`/actions·detections·malfunctions=`events`/servers=`servers`; POST·PATCH·PUT=edit, DELETE=delete)에 데코레이터 부착. servers PATCH 기존 require_admin 유지. 도메인 회귀 0(사전실패 카운트 전후 동일), 단위 5/5 PASS. ★활성화(AUTH_MODE=token)는 클라 3종 Bearer 동시배포 게이트 — `docs/prds/GUIDE_RBAC_Activation_v5.2.md` 참조.<br><br>**[FR-SV-10 비번변경 세션 무효화]** (`b2f80c8`) — `PUT /api/users/me/password` 성공 시 본인 다른 활성 세션의 access+refresh jti 블랙리스트 + 비활성화(현재 세션 sid 보존). F07-01 구멍(발급 JWT가 exp까지 통과) 차단.<br><br>**[5-sync 배포]** — `docker compose build/up api-server` 재빌드·재기동(healthy), **Swagger version 5.0.0→5.2.0 라이브 확인**, app_settings 라이브 생성, 안전점 태그 `v5.2-pre-deploy`/`v5.2-deployed` + 롤백 이미지 `api-test-server:pre-v5.2`.<br><br>**[클라 배포용 산출물]** — `docs/prds/CONTRACT_GOP_Server_v5.2.md`(계약 4건 + canonical 골든벡터 V1·V2 + P2 스키마) / `docs/prds/GUIDE_RBAC_Activation_v5.2.md`(P5 활성화 절차 + 역할 매트릭스 + 클라 체크리스트) / `docs/memory/SESSION_COORDINATION.md`(멀티세션 협업 조율판).<br><br>**[본문 동기화]** — 본 차수에 §9.2 Auth(login/refresh `session_id` + 401 `SESSION_REVOKED`) + §9.8 Session Settings API 신설 반영(아래 본문 파트).<br><br>**[v5.2 잔존]** — P5 AUTH_MODE=token 플립(클라 Bearer 동시배포 게이트) / Force-Logout 활성화(`NATS_REVOKE_ENABLED=true`, 클라 subject 매칭 V-SVF-05) / FR-SV-07 audit append-only DB(RULE/RLS) / FR-SV-11 RTSP 마스킹 / gitea push(인증). **권한그룹 시간 스케쥴링**은 별도 PRD(`PRD_Permission_Group_Scheduling.md`, WS-B 세션) 진행 중 — 본 휴면 RBAC 헬퍼에 grant 합집합으로 올라탐.<br><br>**원칙 준수**: 하루 1차수 묶음 — 2026-06-30 hotfix + 본 추가 작업 **모두 동일 v5.2 단일 행에 append**(별도 차수 분리 금지). |
| v5.1 | 2026-06-29 | **하루 추가 일괄 — 서버 RBAC Enforcement 본격 도입 (`PRD_GOP_Server_RBAC_Enforcement.md` 8 FR 적용, 12/12 PASS)**<br><br>**[차수 배경]** 외부 세션 .NET 시뮬레이션 `wf_52155656`(22 agent / 218 시나리오 / 99 발견) 결과 PRD 도입 → 서버 RBAC 집행률 0% 확진(계정 외 도메인 전부 RBAC 부재 + reports 완전 무인증 + AUTH_MODE=public + 비계정 jti 미검사). 본 차수는 P0 5건 + P1 일부(SV-06/09) 즉시 적용. **AUTH_MODE=token 전환 + 비계정 라우터 require_perm 일괄 부착은 v5.2 권고** (.NET 클라 Bearer 동시 배포 조율 필수).<br><br>**[FR-SV-05] enums 모듈 확장 (선행 필수)** — `app/utils/enums.py:779` `EnumPermissionModule` 8종 → **12종** 확장: `MAP`('map') / `BROADCAST`('broadcast') / `SETUP_SYSTEM`('setup_system') / `SETUP_FEATURE`('setup_feature') 추가. 'cameras' 통일(클라 'cam' 오기 방지). PermissionsSchema/시드/JSONB는 기존 호환(미정의 모듈 422 자동 차단, v4.9 Phase 3 정책 유지).<br><br>**[FR-SV-04] `require_perm(module, verb)` 팩토리 신설** (`app/routers/auth.py:148~`) — `require_role` 확장형, jti 블랙리스트 검사 포함(get_current_account_user 의존 chain). **ADMIN bypass** + 역할명 등급 그룹 매트릭스(OQ-PG-01 Option A, login 정합 `auth.py:298~305`) 기반. 권한 부재 시 403 `Insufficient permission: requires {module}:{verb}`. 비계정 라우터 부착은 다음 차수 단계 적용.<br><br>**[FR-SV-03] `get_current_account_user_optional` 신설** (`app/routers/auth.py:175~`) — 레거시 `get_current_user_optional`(Legacy User 모델 + jti 미검사) 대체 헬퍼. AccountUser 기반 + jti 블랙리스트 검사 + AUTH_MODE 분기(public None 허용 / token 401 강제). 비계정 라우터 의존성 교체 시 사용 — **AUTH_MODE=token 전환 자체는 미실시** (클라 Bearer 동시 배포 후 v5.2).<br><br>**[FR-SV-01 잔여] user_sessions RBAC + 벌크 jti 블랙리스트** — `app/routers/user_sessions.py` GET '/' + GET '/{session_id}' + DELETE '/{session_id}' + DELETE '/user/{user_id}' 4건에 `dependencies=[Depends(require_admin)]` 부착. 벌크 force_logout 핸들러(L75)에 access+refresh jti 블랙리스트 등록(reason='FORCE_LOGOUT_BULK', 단건 980abbc 패턴 일관). T4 LIVE 위험 차단 — VIEWER가 ADMIN 세션 종료 시도 → 403. /me 계열은 self-service 유지.<br><br>**[FR-SV-02] reports.py 전 endpoint 인증** — `app/routers/reports.py:37` `router = APIRouter(dependencies=[Depends(get_current_account_user)])` 라우터 레벨 인증 강제. 12 endpoint(templates CRUD/components/generate/generations/download/preview) 무인증 PII 집계 노출 LIVE 차단. require_perm(reports, view/edit/delete) 도메인별 부착은 v5.2.<br><br>**[FR-SV-06] 마지막 ADMIN 원자 가드** — `app/routers/users.py:492` DELETE + `:381` PUT 핸들러에 `SELECT ... FOR UPDATE` 행 잠금 + 잔여 활성 ADMIN 카운트(`.with_for_update().all()` + `len()` PostgreSQL 호환). 마지막 ADMIN 삭제 또는 강등/비활성화 시도 → 409 `Cannot delete/demote the last ADMIN user`. TOCTOU 차단(동시 두 ADMIN 삭제 시도해도 1명 보존).<br><br>**[FR-SV-09] 누락 인가 보강** — `app/routers/servers.py:328` `PATCH /servers/{id}` + `app/routers/user_groups.py:19,54` GET 2종에 `dependencies=[Depends(require_admin)]` 부착. VIEWER/OPERATOR 권한 그룹 조회 + 인프라 설정 변경 차단.<br><br>**[실측 12/12 PASS]**:<br>- ① reports 무인증 → 401, ② reports admin → 200, ③ reports components 무인증 → 401<br>- ④ /user-sessions admin → 200, ⑤ /user-sessions OPERATOR → 403, ⑥~⑦ DELETE /user-sessions OPERATOR → 403 (2건)<br>- ⑧~⑨ /user-groups GET OPERATOR → 403 (목록+상세)<br>- ⑩ PATCH /servers/1 OPERATOR → 403<br>- ⑪ DELETE /users/1 (마지막 ADMIN) → 409, ⑫ PUT /users/1 role=OPERATOR (강등) → 409<br>- EnumPermissionModule Swagger 12종 노출 확인<br><br>**[안전점/롤백]**: `pre-rbac-enforcement` @ `40f926f`(본 차수 진입 직전). 롤백 `git reset --hard pre-rbac-enforcement` (v5.0 상태 복원).<br><br>**[v5.2 잔존 (Out of Scope)]**:<br>- FR-SV-03 ① `.env AUTH_MODE=public→token` 전환 (클라 Bearer 동시 배포 필요)<br>- FR-SV-04 require_perm 비계정 라우터 적용 (cameras/sensors/controllers/actions/detections/malfunctions write endpoint)<br>- FR-SV-07 감사 append-only DB 강제 (PostgreSQL RULE/RLS + 별도 app 계정 분리 + APScheduler purge)<br>- FR-SV-08 비계정 도메인 jti 검사 통일 (`get_current_user_optional` → `get_current_account_user_optional` 라우터 전수 교체)<br>- FR-SV-10 비번 변경 시 본인 타기기 세션 jti 무효화<br>- FR-SV-11 RTSP URL 마스킹 + NATS subject ACL<br>- PRD §5-A V-SV-01~08 검증 (이주율 / OQ-PG-04~07 PM 결정 / get_current_user_optional 사용처 전수)<br><br>**원칙 준수**: 하루 1차수 묶음 — 본 v5.1은 같은 2026-06-29 작업이지만 v5.0(권한 관리 endpoint + v4.12 정합 정리) 마감 후 별도 PRD(`PRD_GOP_Server_RBAC_Enforcement.md`) 도입에 따른 **차수 분리** (서로 다른 PRD 범위 + 독립 시뮬레이션 근거 + 별도 안전점). |
| v5.0 | 2026-06-29 | **하루 일괄 — 그룹 권한 관리 endpoint 신설(POST /api/user-groups/{id}/permissions, ADMIN 전용) + v4.12 후속 정합 정리 일괄 sweep**<br><br>**[권한 관리 §9.4.7]** `POST /api/user-groups/{group_id}/permissions` 신설(ADMIN 전용). 일반 `PUT /api/user-groups/{id}`은 v4.8 Phase 12-7a 영구 정책에 따라 `permissions` 필드 쓰기를 **차단**(메타만 갱신) — 일반 수정 경로로 권한 변경을 허용하면 **권한 상승 공격면**이 노출되므로, 권한 정책 갱신을 **별도 ADMIN endpoint로 분리**해 인가 집중·감사 일원화. `dependencies=[Depends(require_admin)]`(v4.12 §9.3.1 동일 패턴) 강제 — 비-ADMIN 호출은 라우팅 단계에서 **403**(`Insufficient role`).<br>- **Request**: `PermissionsSchema`(v4.9 Phase 3 도입, strict input) — `modules: Dict[EnumPermissionModule, ModulePermission]` + `device_groups: List[int]`(선택). `EnumPermissionModule` 8종(`devices`/`events`/`reports`/`cameras`/`users`/`user_groups`/`audit_logs`/`servers`), `ModulePermission` 4 verb `StrictBool`(`view`/`edit`/`delete`/`control`), `model_config = ConfigDict(extra='forbid')` → **미정의 모듈/verb는 422 자동 차단**(오탈자·신규 권한 누락 컴파일타임급 검출).<br>- **Response**: `UserGroupResponse`(갱신된 그룹, `permissions` 반영). **Error**: 403(RBAC) / 404(그룹 없음) / 422(스키마 위반).<br>- **JSONB 직렬화**: `permissions = schema.model_dump(mode='json', exclude_none=True)` — `user_groups.permissions` JSONB 컬럼 호환(EnumPermissionModule→string key 정규화, `None`은 누락 보존).<br>- **감사 로그 자동 기록**: `action_type='PERMISSION_CHANGED'`, `resource_type='USER_GROUP'`, `resource_id=group_id`, `resource_name=group.name`, `changes={'before': old_permissions, 'after': new_permissions}`(전/후 스냅샷), `actor_*`(login_id/id/name/role) 채움. **append-only 트리거**(v51.1, FK 익명화 예외 유지) 적용 — UPDATE/DELETE 차단, ACTOR_DELETED/RESOURCE_DELETED 익명화만 허용.<br>- **실측 검증**: admin POST → **200**(group.permissions 갱신, audit_logs 1행 `PERMISSION_CHANGED at 2026-06-29 10:23:29`), 비-ADMIN(VIEWER/USER) POST → **403**, 정의되지 않은 verb(`{"devices":{"view":true,"hack":true}}`) → **422**, 존재하지 않는 그룹 → **404**, Swagger `/docs` `operationId=update_user_group_permissions` + `schema=#/components/schemas/PermissionsSchema` `$ref` 노출 확인.<br>- 코드: `app/routers/user_groups.py:270` `@router.post("/{group_id}/permissions", dependencies=[Depends(require_admin)])`, 주석 `# PRD v5.0`. ⚠ 장비/이벤트/맵 쓰기 RBAC는 **v5.x 후속**(AUTH_MODE token 승격·.NET 클라 Bearer 부착 선결).<br><br>**[v4.12 후속 정합 정리 §부록]** 본 세션 2026-06-29 일괄 sweep — v4.12 차수 마감 후 누적된 운영·정합·보안 항목을 동일 차수에 묶어 처리(하루 1차수 묶음 원칙).<br>- **PII 차단**: `data/profiles/` `.gitignore` 등록(사용자 사진 3건 commit 방지) + `.gitkeep` 유지(디렉터리 영속). `c:workspace_python...txt`(경로 슬래시 누락으로 워크트리 루트에 생성된 사고 파일) 삭제 + 패턴 차단.<br>- **admin 계정 복구**: `failed_login_count=0` 리셋 + bcrypt `admin123` 재발급(평문 미저장, v4.10 user_password 평문 정책은 Camera/Lamp/Server 디바이스 자격증명에만 적용 — User 비밀번호는 bcrypt 해시 유지).<br>- **Swagger/PRD 정합**: Swagger `version` `1.6.0→4.12.0`, API Version `2.10→4.12`, PRD 목록 갱신(미반영 PRD 67건은 archive 후속).<br>- **이미지·컨테이너 재배포**: Image rebuild + Container force-recreate(`Created 2026-06-29T00:59:01`, v4.11 추적 이력 영속·v4.12 RBAC 코드 반영 확인).<br>- **token_blacklist 정리**: 17 row cleanup(외부 세션 잔재 jti 누적, collision/오탐 위험 제거). ⚠ 자동 청소 cron은 **v5.x 후속**.<br>- **메모리/세션 컨텍스트 갱신**: `session-context.md` 차수 `v4.10→v4.12`, HEAD/branch/안전점 표 갱신, `final-stable` 태그 4건 신설(v4.9/v4.10/v4.11/v4.12), 메모리 4건 신설(RBAC ADMIN 게이트·Tracking cursor·프로필 사진 정책·audit FK 익명화).<br>- **잔존 후속**: 장비/이벤트/맵 쓰기 RBAC(v5.x, AUTH_MODE token 승격 선결), `token_blacklist` 자동 청소 cron(v5.x), `before-*` 신규 3 태그 → `pre-*` 컨벤션 재명명, 67건 untracked PRD archive 정리.<br>- **안전점/롤백**: 본 차수 진입 직전 `pre-v5-spec-sync` 태그. 롤백 — 본 명세 commit 회귀 `git reset --hard pre-v5-spec-sync`(명세 v4.12 상태), 외부 세션 endpoint 자체 회귀 `git reset --hard v4.12-final-stable`, v4.12 정합 정리 회귀 `git reset --hard pre-v412-sync-cleanup`. |
| v4.12 | 2026-06-27 | **하루 일괄 — 계정 관리 RBAC(ADMIN 게이트·권한상승 T1 차단) + 추적 이력 인제스트 워커(gis-ingest) 구축**<br><br>**[User API §9.3.1]** 계정 CRUD/lock/unlock/reset-password 8개 엔드포인트에 `require_admin`(=`require_role("ADMIN")`, `app/routers/auth.py` 신설) 의존성 추가. 이전엔 인증(Bearer)만 검증하고 `role`을 인가에 미사용 → **임의 인증사용자가 `PUT /api/users/{id}` 본문에 `role=ADMIN`을 실어 자기/타인을 ADMIN으로 격상(권한상승 T1)** 가능했음. role 미달 시 **403**(`Insufficient role`). 본인 자원(`/me`·`/me/password`·`/me/photo`) self-service 유지, `GET /api/users/photo/{file_name}` 인증불요 유지.<br>- `require_role` 의존성 팩토리 신설(auth.py) + users.py 8개 데코레이터 `dependencies=[Depends(require_admin)]`<br>- E2E 검증: VIEWER GET/PUT/DELETE → 403, T1 격상 → 403, admin → 200, /me → 200, 테스트계정 정리<br>- 서버측 RBAC가 권위 집행 지점(클라 UI 게이팅은 보조·우회 가능). ⚠ 장비/이벤트/맵 쓰기 RBAC는 **후속 차수** — AUTH_MODE token 승격·인증 의존성 통일·.NET 클라 Bearer 부착이 선결(미선결 시 앱 쓰기 전면 401)<br>- 안전점 `before-account-rbac`, 브랜치 `feature/server-account-rbac`<br><br>**[② 추적 이력 인제스트 워커 §11 / gis-ingest]** TRACKING_STATUS(신 `targets[]`)를 NATS 구독→`track_points` 영속하는 워커 신설 — §11(v4.11)에서 "후속"으로 둔 저장 경로 실현. 독립 compose 서비스 `api-test-gis-ingest`(`db_monitor` 역방향 미러, asyncpg+nats-py, `nats_external` 망 연결). `sensorway.*.gis.tracking-status` 구독 → `tracking=="active"` targets[]만 행으로 `INSERT ... ON CONFLICT (track_id, observed_at) DO NOTHING`(멱등). `observed_at`(UTC)→naive KST 변환(읽기 API KSTDatetime 정합), 구버전 단일 `target` 방어 파싱 포함. **mock E2E 검증**: NATS 발행→인제스트→멱등(중복 발행 2회=1행)→`/points`·`/sessions` 조회 정상, 테스트 데이터 정리. 발행 시 `created_at` NOT-NULL(raw asyncpg는 ORM Python default 미적용) 명시 지정 버그 E2E로 발견·수정. ⚠ 실 `AiAnalysis`가 신 `targets[]` 포맷 발행하도록 **합의 미결**(방어 파싱으로 구버전 호환). (`gis_ingest/main.py`·`Dockerfile`·`requirements.txt`, `docker-compose.yml` gis-ingest 서비스, 브랜치 `feature/tracking-gis-ingest`) |
| v4.11 | 2026-06-26 | **하루 일괄 — 추적 이력(Tracking) REST API 신설 + 프로필 사진 업로드 + audit append-only 하드닝**<br><br>**[추적 이력 API 신설 §11]** GIS 추적(TRACKING_STATUS `targets[]`) 영속·조회 — `track_points` 테이블(`UNIQUE(track_id, observed_at)` 멱등 + `observed_at`/`(camera_id,observed_at)` 인덱스, 마이그레이션 v54) + **읽기전용 GET 3종**: `GET /api/tracking/points`(기간+keyset cursor 청크, Playback 핵심) · `GET /api/tracking/sessions`(track_id 단위 MIN/MAX/COUNT 파생집계) · `GET /api/tracking/health`(가용성 게이팅, 무인증). 저장은 **서버측 NATS 인제스트**(독립 `gis-ingest` 워커, `INSERT ... ON CONFLICT DO NOTHING`) — 클라 POST 배제(다중 스테이션 N배 중복 회피). 계약=신버전 `targets[]`(`docs/Gop_Message_Broker_연동설계.md §8.3.7`). §11 신설에 따라 기존 **§11 에러 처리→§12, §12 부록→§13 재번호**(TOC·부록 엔드포인트 목록 동기화).<br>**[프로필 사진 §9.3.1]** `POST /api/users/me/photo`(multipart, ≤5MB) → `./data/profiles/` 영속 + `account_users.photo_url` 갱신, `GET /api/users/photo/{file}`(무인증·경로 traversal 차단).<br>**[audit append-only 하드닝 §9.6.2]** 이력 있는 사용자 hard-delete 가능 — `fn_block_audit_modification`이 **FK 익명화(actor_id/user_id→NULL) UPDATE만 허용**(내용 변경·행 삭제는 계속 차단, v51.1). + audit-logs 500 수정: `AuditLogResponse.action_type/resource_type` strict enum→str(tolerant, append-only 비-enum 잔재 대응). |
| v4.10 | 2026-06-25 | **하루 일괄 — SEC-1 마스킹 정책 폐기 / 평문 응답 복원 (v4.9 Phase 5 회귀)**<br><br>**[차수 배경]** 2026-06-24 v4.9 Phase 5에서 `.NET v4.9 Review Issues` SEC-1 (P0 보안) 적용으로 Camera/Lamp/Server 응답 `user_password` 마스킹(`"********"`) 도입. 단 1일 만에 운영 한계 노출: (1) 마스킹된 응답을 평문으로 복원하는 **복호화 경로 미정**, (2) .NET 통합 UI가 NVR/VMS/Speaker/Lamp/외부 서버에 RTSP/SSH/HTTP 접속 시 평문 자격증명 필요, (3) 대안(별도 secret API / AES / RSA / 백엔드 프록시)은 모두 분량 큼(4~20h+) 및 .NET 측 변경 동반. **차장님 결재 (2026-06-25)**: *"야 그냥 평문으로 보내. 복호화방법도 없는거 같은데"* → 단순 평문 회귀 + 보안은 v5.x 별도 차수.<br><br>**[Phase 1] SEC-1 마스킹 정책 폐기 / 평문 응답 복원 (6/6 PASS)**<br>- **안전점**: `pre-v4.10-phase1` @ 31bb478<br>- **PRD**: `docs/PRD_v4.10_Phase1_mask_rollback.md` (6.4KB, Workflow 1 agent, Track B)<br>**Schema 회귀 (5건)**:<br>- `app/schemas/device.py:12` `from app.schemas._password_mask import mask_password_serializer` 제거<br>- `app/schemas/device.py:518-520` `CameraResponse._mask_user_password` `@field_serializer` 블록 제거<br>- `app/schemas/device.py:1073-1075` `LampResponse._mask_user_password` 블록 제거<br>- `app/schemas/server.py:7` import 제거<br>- `app/schemas/server.py:156-158` `ServerResponse._mask_user_password` 블록 제거<br>- `app/schemas/server.py:207-209` `ServerNestedResponse._mask_user_password` 블록 제거<br>- Field 설명 정정: `"접속 비밀번호 (응답 시 마스킹 — DB 평문 유지)"` → `"접속 비밀번호"` (4건)<br>**OpenAPI example 회귀 (4건)**:<br>- ServerResponse / ServerNestedResponse / ServerCategorySummary nested `"********"` → `"password123"`<br>- LampResponse example `"********"` → `"lamp1234"`<br>**명세 §5.3.x Camera 응답 예시 (L5103)**: `"user_password": "********"` → `"user_password": "admin1234"`<br>**유지**:<br>- `app/schemas/_password_mask.py` 파일 **heritage 보존** (사용처 0, v5.x secret API 재활용 가능)<br>- 명세 §9.2.2 로그인 자리표시자 `<your_login_id>/<your_password>` **유지** (로그인 자격증명 도메인, 마스킹 대상 아님)<br>- DB 평문 / Create/Update 요청 schema / 백엔드 내부 서비스 / 시드 / Audit Log `SENSITIVE_FIELDS` 모두 변경 없음 (변경 0)<br>**실측 검증 (6/6 PASS)**:<br>- ① Camera 단일 응답 `user_password = "sensorway1"` (DB 평문 그대로) ✅<br>- ② Lamp 단일 응답 `"lamp123"` ✅<br>- ③ Server 단일 응답 `"testpwd123"` ✅<br>- ④ Camera POST 응답 평문 `"plain_v410"` ✅<br>- ⑤ Camera POST DB 평문 `"plain_v410"` (3중 흐름 일치) ✅<br>- ⑥ OpenAPI ServerResponse example `"password123"` ✅<br>- Container Up healthy / Image rebuild / `grep mask_password_serializer` 0건 확인<br>**메모리 정책 재전환**:<br>- `feedback_password_masking_policy.md` (v4.9 Phase 5 정책) → **DEPRECATED** + `superseded_by: feedback_password_plaintext_policy`<br>- `feedback_password_plaintext_policy.md` → **RESTORED** (현행 정책 재명시)<br>- `MEMORY.md` 인덱스 한 줄 설명 갱신 (plaintext 현행 + masking DEPRECATED 동시 노출, 의사결정 이력 보존)<br>**.NET 회신 보강**:<br>- `docs/GOP_Server_API_v4.9_Review_RESPONSE.md` 하단에 `## POLICY UPDATE 2026-06-25 — v4.10 Phase 1 회귀` 섹션 append<br>- 24시간 만의 정책 회귀 인정 + 차장님 결재 인용 + 복호화 경로 부재 근거 + DTO shape 변경 0 재명시 + 보안 v5.x 예고<br>**Track B 적용** (5축 점수 3점: 파일 3 / 아키텍처 0 / 모듈 0 / 테스트 1 / 공수 1)<br><br>**[v4.10 잔존 (.NET v4.9 Review 다른 항목)]**<br>- P0: ENV-1 (Response envelope 5종 표준화) / AUTH-1 (`expires_in`/TTL) / AUTH-2 (PUT /me/password 본문)<br>- P1: FMT-1 / ENUM-1~2 / DEV-1~2 / EVT-1 / INT-1 / SVR-1 / AUTH-3~4 (10건)<br>- 잔존: B-4 / B-5 / B-7 / B-8 (4건, FollowupRequests 미적용)<br>- P2: DOC-1~3 (3건)<br>- 기존 v4.9 후속: A-1.3 Photo multipart / A-1.4 가드 7종 / A-3 audit trigger / B-2 NATS / B-3 RBAC / B-6 lock 메타 (~17h)<br>- 합계 ~38-50h (3~5일 작업)<br><br>**원칙 준수**: 하루 1 차수 묶음 (Phase 1 단일 작업, 2026-06-25 = v4.10 단일 차수). v4.9 Phase 5와 별도 차수 분리 — 다른 일자 작업이므로 정합.<br>**[Phase 2] HTTPS 도입 (mkcert 폐쇄망) + Inno Setup rootCA 인스톨러 (6/6 PASS)**<br>- **배경**: v4.10 Phase 1 평문 응답 정책 회복 직후, 폐쇄망 환경에서도 통신 구간 암호화 필요 (JWT Bearer 토큰 + user_password 평문 전송 위험 완화). 차장님 결재 (2026-06-25): *"가장 간단하고 쉬운거 신뢰되고. 우리 폐쇄망이야"* + *"GOP 운영 시나리오 (서버 1대 + 여러 클라 PC)"* + *"인증서 등록을 EXE 1클릭으로 일원화"*.<br>- **선정**: mkcert (외부 인터넷 불필요, OS 신뢰 저장소 자동 등록) + Inno Setup (.iss 정식 GUI 인스톨러).<br>- **안전점**: `pre-v4.10-phase2` @ 8089877<br>- **PRD**: `docs/PRD_v4.10_Phase2_HTTPS_mkcert_Inno.md` (11.2KB, Workflow 2 agent 옵션 비교 A/B/C → A 선정)<br>- **사용자 가이드**: `docs/GOP_RootCA_Installer_Guide.md` (.NET 팀 배포용 1페이지)<br>**[Phase 2-1] mkcert 인증서 발급**:<br>- mkcert v1.4.4 다운로드 (`~/bin/mkcert.exe` ~5MB)<br>- `mkcert -install` → Windows 신뢰 저장소에 local CA 자동 등록 (Java keytool 경고 무시)<br>- `mkcert -cert-file certs/server.crt -key-file certs/server.key localhost 127.0.0.1 ::1 host.docker.internal 192.168.202.160 192.168.1.1 10.0.0.1` (SAN 다중 + 만료 2028-09-25)<br>- `rootCA.pem` 위치: `C:\Users\gh\AppData\Local\mkcert\rootCA.pem` (CAROOT) → `certs/installer/payload/rootCA.pem` 복사<br>**[Phase 2-2] Docker HTTPS 적용**:<br>- `Dockerfile` (L37-41) CMD 정정 — `sh -c "if [ -f /app/certs/server.crt ] ... uvicorn --ssl-keyfile ... else uvicorn (HTTP fallback) fi"` (개발 환경 호환)<br>- `docker-compose.yml` api-server 서비스:<br>  - `volumes: ./certs:/app/certs:ro` 추가<br>  - `healthcheck: curl -fk https://localhost:8000/docs` (자체 서명이라 -k)<br>- Image rebuild + force-recreate → Container Up healthy + `Uvicorn running on https://0.0.0.0:8000` 확인<br>**[Phase 2-3] Inno Setup 인스톨러 (옵션 A 선정, 옵션 B PowerShell/C# 제외 사유: 차장님 UX + 폐쇄망 USB 운반 + 제어판 제거 자동)**:<br>- `certs/installer/` 디렉터리 신설 (8 소스 파일):<br>  - `src/install_gop_rootca.iss` (3.7KB) — Inno Setup 메인 스크립트 (PrivilegesRequired=admin + rootCA 임베드 + certutil 호출)<br>  - `src/post_install.ps1` (3.5KB) — certutil -addstore -f Root + 한국어 로그 (`%TEMP%\GOP-RootCA-Install.log`)<br>  - `src/pre_uninstall.ps1` (1.8KB) — certutil -delstore 신뢰 제거 (제어판 제거 시 자동 호출)<br>  - `src/LICENSE_KO.txt` (0.6KB) — 한국어 Welcome 페이지<br>  - `scripts/build.ps1` (2.9KB) — ISCC.exe 자동 탐색 + 컴파일<br>  - `scripts/verify.ps1` (1.1KB) — 등록 검증<br>  - `.gitignore` + `README.md` (빌드/사용 안내)<br>- payload: `certs/installer/payload/rootCA.pem` (mkcert root CA 임베드, 1.6KB)<br>- 빌드 산출물: `GOP-RootCA-Installer-v1.0.0.exe` (~1.5~2.5MB 예상, Inno Setup Compiler 빌드 시 생성)<br>- **빌드는 차장님 PC에서 별도 수행** (Inno Setup 6 사전 설치 필요, 빌드 가이드는 README.md 참조)<br>**[Phase 2-4] .gitignore 보안**:<br>- `certs/*.crt` / `certs/*.key` / `certs/*.pem` 차단 (commit 금지)<br>- `!certs/installer/` 예외 (소스는 commit OK)<br>- `certs/installer/build/*.exe` + `payload/rootCA.pem` 차단 (산출물 제외)<br>**[Phase 2-5] 실측 검증 (6/6 PASS)**:<br>- ① Uvicorn 시작 로그 `Uvicorn running on https://0.0.0.0:8000` ✅<br>- ② `curl -k https://localhost:8000/docs` → 200 + `ssl_verify_result=0` ✅<br>- ③ `http://localhost:8000/docs` → 000 (HTTP 차단됨, Uvicorn SSL 강제) ✅<br>- ④ 인증서 정보: `subject=mkcert development certificate, issuer=mkcert development CA, notAfter=2028-09-25` ✅<br>- ⑤ Bearer 토큰 발급 + `https://localhost:8000/api/auth/me` 200 ✅<br>- ⑥ Container `Up healthy` + healthcheck `curl -fk` 정상 ✅<br>**[Phase 2 잔존]**:<br>- Inno Setup Compiler 빌드는 차장님 PC에서 별도 (소스만 commit, build/*.exe는 .gitignore)<br>- HSTS 헤더 / Secure 쿠키 / CSP 등 추가 보안 헤더는 v5.x 권고<br>- adminer(8080) / NATS(4222) 등 다른 서비스 HTTPS는 별도 차수 권고<br>- 외부 IP / 내부 IP 환경 (메모리 project_environments)에서 SAN 추가 발급 필요 시 mkcert 재실행<br><br>**원칙 준수**: 하루 1 차수 묶음 (Phase 1+2 모두 v4.10 단일 행, 2026-06-25).<br>**롤백**: `git reset --hard pre-v4.10-phase2` (Phase 2만 회귀 → HTTPS 제거, 평문 응답 정책 유지). `git reset --hard pre-v4.10-phase1` (Phase 1+2 회귀 → v4.9 Phase 5 마스킹 정책 복원). `git reset --hard pre-v4.9-phase5` (v4.9 Phase 5 자체 회귀, 마스킹 도입 직전). `git reset --hard v4.8-final-stable` (v4.9 + v4.10 전체 회귀). |
| v4.9 | 2026-06-24 | **하루 일괄 — .NET 통합 UI 팀 31건 질의 회신 → Followup PRD 12항목 → 핵심 P0 7건 적용 (Phase 0~4 통합)**<br><br>**[차수 배경]** 2026-06-24 오전 .NET 팀에 v4.8 마감 후속 회신(`docs/GOP_Server_API_OpenQuestions_RESPONSE.md`, 31건) 작성 → 클라가 동일 일자 `docs/GOP_Server_API_FollowupRequests.md` (12 항목, P0 4 + P1 8) 제출 → 본 차수 12 항목 통합 정합화. Workflow 39 agent로 50 시나리오 + 시뮬레이션 2회 + PRD 작성. R1 1/45 PASS → R2 41/4 PASS 검증. 하루 1차수 묶음 원칙 준수 (Phase 0~4 모두 v4.9 단일 행, 2026-06-24).<br><br>**[Phase 0] .NET 31건 질의 회신 (commit 5274dbb @ 2026-06-24 오전)**<br>- Workflow 8 agent (653K token / 14분): A 인증 5 + B 권한 7 + C 사용자 8 + D 세션 3 + E 감사 3 + F NATS 1<br>- 산출: `docs/GOP_Server_API_OpenQuestions_RESPONSE.md` (14.5KB / 418줄, P0 3건 사전공지 + 명세 보강 권고 11건)<br>- 결과: .NET 팀이 이를 기반으로 본 차수 12항목 Followup 제출 → Phase 1~4 진입<br><br>**[Phase 1] 안전점 + 명세 3 위치 초기화 (commit 4544d7c @ 2026-06-24 오전)**<br>- `pre-followup-prd` @ 64fa905 (PRD 진입 직전) + `pre-v4.9-phase1` @ 8b28c9c (Phase 1 진입)<br>- 명세 헤더(L4-5) + 푸터(L15861-62) + 변경 이력 v4.9 / 2026-06-24 동시 갱신<br>- PRD: `docs/PRD_v4.9_Followup_AccountIntegration.md` (20.6KB / 536줄)<br><br>**[Phase 2] Auth 정합 — B-1 + A-3 + A-4 (commit 9068e46, 6/6 PASS)**<br>**Phase 2-B1: 글로벌 HTTPException 핸들러 WWW-Authenticate 헤더 보존 (RFC 6750/7235)**<br>- `app/main.py:470-489` http_exception_handler — `response_headers = getattr(exc, 'headers', None)` + `JSONResponse(..., headers=response_headers)` 추가<br>- 라우터의 `HTTPException(headers={"WWW-Authenticate": "Bearer"})` 이 envelope 직렬화 시 보존됨<br>- 실측 PASS: `curl /api/auth/me` 토큰 누락 시 응답 헤더에 `www-authenticate: Bearer` 포함 확인<br>**Phase 2-A3: refresh_token TTL settings 분리**<br>- `app/config.py:30` `JWT_REFRESH_EXPIRATION_DAYS: int = 7` 신설 (env override 가능, 이전 하드코딩 7일)<br>- `app/utils/auth.py:85` `timedelta(days=7)` → `timedelta(days=settings.JWT_REFRESH_EXPIRATION_DAYS)`<br>**Phase 2-A4: jti blacklist + refresh type 가드 (D1 결재: 잠정 DB 저장소)**<br>- `app/utils/auth.py:93` `decode_token(token, expected_type=None)` 시그니처 — payload `type=='refresh'` 강제 + jti/token_type 추출<br>- `app/schemas/user.py:331-336` `TokenData.jti` + `TokenData.token_type` 필드 추가<br>- `app/models/token_blacklist.py` 신설 — `token_blacklist` 테이블 (jti UNIQUE + expires_at + user_id FK + reason)<br>- `app/services/token_blacklist_service.py` 신설 — `is_blacklisted/add_to_blacklist/cleanup_expired` + in-memory TTLCache 60s<br>- `app/routers/auth.py:97-119` `get_current_account_user` — jti 블랙리스트 검증 추가 + `Token has been revoked` 401<br>- `app/routers/auth.py:356-372` logout 핸들러 — `add_to_blacklist(jti, reason="LOGOUT", token_type="access")` 등록<br>- `app/routers/auth.py:392-432` refresh 핸들러 — `decode_token(token, expected_type="refresh")` 가드 + 옛 jti rotation 등록<br>- `app/migrations/v52_token_blacklist.sql` 신설 — 테이블 + 3개 인덱스<br>- 실측 PASS (6/6): WWW-Authenticate / refresh type 가드(401) / 정상 refresh(200) / 옛 refresh rotation 차단(401) / 로그아웃 전 me(200) / 로그아웃 후 me 차단(401)<br><br>**[Phase 3] RBAC Permission 모델 — A-2 전건 (commit 9068e46, 5/5 PASS)**<br>**A-2.1 PermissionsSchema 라우터 적용 / A-2.2 미정의 모듈 422 / A-2.3 미정의 verb 422 / A-2.5 StrictBool 강제**<br>- `app/utils/enums.py` (마지막 라인) `EnumPermissionModule` (8종: devices/events/reports/cameras/users/user_groups/audit_logs/servers) + `EnumPermissionVerb` (4종: view/edit/delete/control) Static 시드 추가<br>- `app/schemas/user.py:32` `ModulePermission` (`extra="forbid"` + `StrictBool` view/edit/delete/control) 신설<br>- `app/schemas/user.py:47` `PermissionsSchema` (`modules: Dict[EnumPermissionModule, ModulePermission]` + `extra="forbid"`) 신설<br>- `app/schemas/user.py:62-90` `UserGroupCreate` — `permissions: Optional[PermissionsSchema]` 강타입 적용 + `model_config = ConfigDict(extra="forbid")`<br>- `app/routers/user_groups.py:121-128` POST 핸들러 — `perms_dict = group_data.permissions.model_dump(mode="json", exclude_none=True)` 추가 (JSONB 직렬화 호환)<br>**A-2.4 시드 정규화 + v53 마이그레이션 (D3 결재 적용)**<br>- `app/utils/init_sample_data.py:126-138` — flat `"rw"/"r"` 폐기, `_RW`/`_R`/`_CTRL` nested dict 적용<br>- `app/migrations/v53_permissions_normalization.sql` 신설 — `pg_temp.fn_normalize_permission_value` 함수 + 기존 시드 3개 그룹 (운영팀/관제팀/유지보수팀) flat → nested 변환<br>- 실측 PASS (5/5): 미정의 모듈(super_admin) 422 / 미정의 verb(destroy) 422 / StrictBool "yes" 422 / StrictBool 1(int) 422 / 정상 nested 201<br><br>**[Phase 4] Account Photo XSS Validator — A-1.2 (commit 9068e46, 6/6 PASS)**<br>- `app/schemas/user.py:212-230` `AccountUserSelfUpdate.validate_photo_url_scheme` `@field_validator` 신설<br>- 차단: `javascript:`/`data:`/`vbscript:`/`file:`/`about:` 스킴 → 422<br>- 허용: `http://`/`https://`/`/static/profiles/` 시작만<br>- 실측 PASS (6/6): javascript:/data:/vbscript:/file: 모두 422 / https & /static/profiles 200<br><br>**[Phase 4 잔존 — v4.9 후속 (같은 날 추가 처리 가능)]**<br>- A-1.1 분기 회복 (이미 코드에 존재 — `users.py:382` 확인) ✅<br>- A-1.3 `POST /api/users/me/photo` multipart 엔드포인트 신설 (잔존)<br>- A-1.4 업로드 가드 7종 (매직바이트/MIME/크기/race/PNG bomb 등) (잔존)<br><br>**[Phase 1~4 누적 실측 (17/17 PASS)]**<br>- Phase 2 6/6 (B-1 + A-3 + A-4 jti blacklist) ✅<br>- Phase 3 5/5 (A-2 미정의 차단 4 + 정상 1) ✅<br>- Phase 4-A.1.2 6/6 (XSS 차단 4 + 정상 2) ✅<br>- Container Up healthy / Image rebuild / OpenAPI: `ModulePermission`/`PermissionsSchema`/`EnumPermissionModule`/`EnumPermissionVerb` 신규 schema 노출 확인<br>- Track C 적용 (5축 점수 7점: 파일 8 + DB 마이그 2 / 아키텍처 2 / 모듈 4 / 테스트 1 / 공수 1)<br><br>**[v4.9 잔존 (오늘 추가 처리 가능 / 다음 세션)]**<br>- A-1.3 + A-1.4 (Photo multipart + 가드 7종, ~5h)<br>- A-3 ROLE_CHANGED/GROUP_ASSIGNED 트리거 분리 (1h)<br>- B-2 NATS SESSION_FORCED_LOGOUT push (4h)<br>- B-3 require_admin 의존성 + lock/unlock/delete/reset-password 적용 (5h)<br>- B-4 GET /api/users/check-login-id (1h)<br>- B-5 GET /api/users/{id}/login-history (1.5h)<br>- B-6 lock 메타 영속 (1.5h)<br>- B-7 permissions를 /me + refresh 응답 포함 (1h)<br>- B-8 list PaginationMeta 적용 확장 (1.5h)<br><br>**[v4.10 cross-item 분리]**: thumbnails.py 업로드 / 정적 자원 인증 / AuditChange.rejected 메타<br><br>**[Phase 5] SEC-1 user_password 응답 마스킹 (.NET v4.9 Review 회신, P0 보안)**<br>- **배경**: `docs/GOP_Server_API_v4.9_Review_Issues.md` SEC-1 (P0) — Camera/Lamp/Server 응답 user_password 평문 노출 지적<br>- **차장님 결재 (2026-06-24)**: "계정 비번 다 보호, 삭제가 아니라 마스킹"<br>- **PRD**: `docs/PRD_v4.10_SEC1_password_masking.md` (16.5KB, Track C / Workflow 4 agent)<br>- **안전점**: `pre-v4.9-phase5` @ 8afcc45<br>- **신규**: `app/schemas/_password_mask.py` — `PASSWORD_MASK = "********"` + `mask_password_serializer` (None→None / 평문→마스크)<br>- **4 Response 클래스 적용** (PRD §2 실 코드 검증으로 7→4 정정 — CameraNestedResponse/Sensor/Controller는 user_password 필드 자체 없음):<br>  - `app/schemas/device.py:480` CameraResponse — `@field_serializer("user_password")` 추가 (L519-521)<br>  - `app/schemas/device.py:1037` LampResponse — `@field_serializer` 추가 (L1074-1076)<br>  - `app/schemas/server.py:135` ServerResponse — `@field_serializer` 추가 (L154-156)<br>  - `app/schemas/server.py:178` ServerNestedResponse — `@field_serializer` 추가 (L194-196)<br>- **example 정합화 5건**:<br>  - ServerResponse `json_schema_extra` example `"password123"` → `"********"` (server.py:163)<br>  - ServerNestedResponse example `"password123"` → `"********"` (server.py:209)<br>  - ServerCategorySummary nested example `"password123"` → `"********"` (server.py:276)<br>  - ServerCreate request example → `"<your_password>"` 자리표시자 (server.py:96)<br>  - LampCreate/LampUpdate request example → `"<your_password>"` 자리표시자 (device.py:991, :1024)<br>  - LampResponse example `"lamp1234"` → `"********"` (device.py:1059)<br>- **명세 §9.2.2 로그인 예시 자리표시자**: `admin/admin123` → `<your_login_id>/<your_password>` (L14111-14114)<br>- **명세 §5.3.x Camera 응답 예시**: `"user_password": "admin1234"` → `"user_password": "********"` (L5103)<br>- **DB 평문 유지** (백엔드 NVR/Speaker/Lamp/외부 서버 SSH/HTTP/RTSP 접속용): 모델/마이그레이션 변경 0<br>- **DTO shape 변경 0** (필드 유지, 값만 변환) → .NET 클라이언트 호환성 100%<br>- **실측 8/8 PASS**:<br>  - ① Camera 목록 응답 user_password = `"********"` ✅<br>  - ② Camera 단일 응답 `"********"` ✅<br>  - ③ Lamp 단일 응답 `"********"` ✅<br>  - ④ Server 단일 응답 `"********"` (시드 `testpwd123` 주입 후 마스킹 확인) ✅<br>  - ⑤ DB 평문 유지 (`cameras.user_password='sensorway1'`, `servers.user_password='testpwd123'`) ✅<br>  - ⑥ OpenAPI ServerResponse example `"********"` 노출 ✅<br>  - ⑦ Camera POST: 요청 평문 → DB 평문 저장 (`verysecret123`) → 응답 마스킹 (3중 흐름 검증) ✅<br>  - ⑧ Container Up healthy / Image rebuild ✅<br>- **메모리 정책 갱신**: `feedback_password_plaintext_policy` (v4.4 Phase 5 복원 정책) → `feedback_password_masking_policy` 신설 (응답 마스킹, DB 평문 이원화)<br>- **.NET 회신 문서**: `docs/GOP_Server_API_v4.9_Review_RESPONSE.md` 작성 — SEC-1 적용 완료 통지<br>- Track C 적용 (5축 점수 5점: 파일 4 + helper 1 + 모듈 2 + example 7 + 명세 2 / 공수 0)<br><br>**[v4.9 Phase 5 잔존 (v4.10 권고 — .NET v4.9 Review 다른 항목)]**<br>- P0: ENV-1 (Response envelope 5종 표준화) / AUTH-1 (`expires_in`/TTL 응답) / AUTH-2 (PUT /me/password 본문 스키마)<br>- P1: FMT-1 (datetime timezone) / ENUM-1~2 (Enum 케이싱/예시 불일치) / DEV-1~2 / EVT-1 / INT-1 / SVR-1 / AUTH-3~4<br>- P2: DOC-1~3<br>- 기존 v4.9 후속 잔존 (A-1.3 Photo multipart / A-1.4 가드 / B-2~B-8 등 ~21h)<br><br>**원칙 준수**: 하루 1 차수 묶음 (Phase 0~5 모두 v4.9 단일 행, 2026-06-24). commit 메시지 5274dbb의 `docs(v4.8)` prefix는 명세상 v4.9 Phase 0로 흡수됨.<br>**롤백**: `git reset --hard pre-v4.9-phase5` (Phase 5만 회귀) / `git reset --hard pre-v4.9-phase1` (Phase 2~5 회귀 — Phase 0/1 docs 유지) / `git reset --hard pre-followup-prd` (Phase 1~5 회귀 — Phase 0 docs만 유지) / `git reset --hard v4.8-final-stable` (v4.9 전체 회귀). |
| v4.8 | 2026-06-22 | **하루 일괄 — DELETE 응답 envelope P1 sweep (11 endpoint) — 클라이언트 보고서 v2 §6 P1 일괄 정정**<br><br>**[차수 배경]** v4.7 (P0 4건) 정정 후 클라이언트팀이 보고서 갱신 — §6 P1로 EM 단건 / Reports / Users / UserGroups / UserSessions / ServerMetrics / EnclosureMetrics 등도 `data: dict` 또는 envelope 위반 명시. v4.6 Phase 9에서 추가한 EM 단건 DELETE `'data': {}` 정책도 포함됨. 동일 클라 증상(JsonReaderException) 재발 차단.<br><br>**[Phase 1] git 안전점 — pre-delete-sweep 태그 (v4.7에서 신설, 본 차수 진입 시 유효)**<br>- 사고 시 복귀: `git reset --hard pre-delete-sweep` (P0 + P1 모두 회귀)<br><br>**[Phase 2] EM 단건 DELETE 3건 — Phase 9 'data': {} 정책 정정**<br>- app/routers/event_mapping_cameras.py:442 — `ApiSingleResponse[dict]` → `[None]` + return body `'data': {}` → `'data': None`<br>- app/routers/event_mapping_speakers.py:354 — 동일<br>- app/routers/event_mapping_lamps.py:347 — 동일<br>- v4.5 Phase 9에서 추가한 빈 dict 정책은 클라 측 형 안전 역직렬화 불가 → null 통일이 정답<br>- 벌크 DELETE (`/cameras` 등 다중 unassign)는 `removed_config_ids/skipped/not_found` 3분류 필요 → dict 패턴 그대로 유지 (의미 보존)<br><br>**[Phase 3] 일반 단건 DELETE 8건 — envelope 표준화**<br>- app/routers/reports.py:293 templates/{template_id} — `ApiResponse` data={"id":...} → `data=None` (id는 message에 보존)<br>- app/routers/users.py:429 {user_id} — `{"success": True}` (envelope 위반) → 표준 envelope `{success, message, data:None}`<br>- app/routers/user_groups.py:265 {group_id} — 동일<br>- app/routers/user_sessions.py:75 user/{user_id} — `data={"count":...}` → `data=None` (count는 message에 보존)<br>- app/routers/user_sessions.py:175 me/{session_id} — envelope 보강<br>- app/routers/user_sessions.py:267 {session_id} — envelope 보강<br>- app/routers/server_metrics.py:339 {server_id}/metrics — `ApiSingleResponse[dict]` + `data={"server_id","deleted_count"}` → `[None]` + `data=None` (deleted_count는 message에)<br>- app/routers/enclosure_metrics.py:275 {enclosure_id}/metrics — 동일 패턴<br><br>**[Phase 4] 정보 보존 정책**<br>- 삭제 카운트 (server_metrics, enclosure_metrics, user_sessions): `data`에서 제거 + **message에 보존** — `f"Deleted {n} metrics for ..."` 형태<br>- 삭제 id (reports/templates, users, user_groups): `data`에서 제거 + **message에 id 포함** — `f"Report template {id} deleted successfully"` 형태<br>- 감사 추적성 손실 0: `log_action` / `log_config_change` 이미 캡처<br><br>**[Phase 5] 검증 (전수 통과)**<br>- OpenAPI 36 DELETE endpoint:<br>  - ✅ `ApiSingleResponse_NoneType_` (data: null 통일): **22** (v4.7 9 + v4.8 13)<br>  - ✅ `ApiSingleResponse_dict_` (자유형 dict 잔존): **0**<br>  - 🟡 `$ref` 없음 (response_model 미부착, 별도 작업 영역): 14<br>- Container Up healthy / Image rebuild 완료<br>- Track B 적용 (5축 점수 3점: 파일 4 / 아키텍처 0 / 모듈 0 / 테스트 1 / 공수 0)<br><br>**[Phase 6] 보고서 갱신**<br>- docs/Analysis/Device_Delete_Response_Verification_v4.6.md §P1 후속 sweep 표 + 최종 검증 결과 추가<br>- docs/API_Delete_Response_Inconsistency-report.md v2 (클라이언트팀 갱신본) 응답 완료<br><br>**[Phase 7] 잔존 (v4.9+)**<br>- `$ref` 없음 14 endpoint — response_model 일괄 부착 (별도 PRD)<br>- `ApiSingleResponse_Union[dict,None]` 4건 (detection/malfunction/connection/action events) — 보고서 §6 미명시, 동일 sweep 가능<br><br>**검증**: 코드 9 파일 변경 (DELETE 응답 envelope) / DB 변경 0 / Image rebuild / Container healthy / OpenAPI 정합. 매니저 영향: 클라 보고된 모든 dict 패턴 DELETE 해소.<br><br><br>**[Phase 8] Events 4건 DELETE Union[dict,None] → None sweep (같은 날 추가 — 클라이언트팀 잔존 리스크 보고)**<br>- 클라이언트팀 §4 잔존 리스크 보고 — events 4건이 `Optional[dict]`로 잔존, `<bool>` 역직렬화 시 JsonReaderException 위험<br>- 안전점: `pre-events-delete-sweep` 태그 신설 (`8547742` 시점)<br>- Workflow 6 agent 정밀 분석 (337K token / 5분, verdict safe_to_apply)<br>- 4 핸들러 정정:<br>  - app/routers/detections.py:626 — `ApiSingleResponse[Optional[dict]]` → `[None]` + `f"Detection event {event_id} ..."`<br>  - app/routers/malfunctions.py:629 — 동일 + `f"Malfunction event {event_id} ..."`<br>  - app/routers/connections.py:548 — 동일 + `f"Connection event {event_id} ..."`<br>  - app/routers/actions.py:626 — 동일 + `f"Action event {event_id} ..."`<br>- 실 응답 본문은 이미 `data=None` (단일 정상 경로) — response_model 타입만 정합화<br>- 4건 모두 동일 패턴(id 보존) — Phase 2~7 정책과 일관<br>- 검증: OpenAPI `NoneType` 통일 **26** (Phase 2~7 22 + Phase 8 4) / `Union[dict,None]` 0 / `dict` 0 / `$ref` 없음 14 (v5.x별도)<br>- 실 API: detection/connection/action DELETE → `data is None` + msg에 id 포함 PASS<br>- Track A 적용 (5축 점수 1점)<br><br>**[Phase 9] device_group_mappings polymorphic cascade 누락 정정 (같은 날 추가 — 클라이언트팀 보고서 v3)**<br>- 보고: 장비 DELETE 시 그룹 `device_count` 미갱신 (스피커 케이스). 라이브 검증: 긴급 방송장비 그룹 `device_count=92` vs 실 스피커 0 + 램프 30 → 약 62 orphan 매핑<br>- Workflow 3 agent 정밀 진단 (244K token / 10분): **차장님 가설 정정** — 보고는 "램프 정상 / 스피커 누락"이었으나 코드 실측은 **반대**. Camera/Controller/Sensor 3종만 라우터 cleanup ✅, Lamp/Speaker/Enclosure 3종이 누락 ❌<br>- **근본 원인**: `device_group_mappings.device_id`가 polymorphic FK (6개 자식 테이블 PK 참조) → 단일 DB FK 선언 불가 + ORM relationship `viewonly=True` → 자동 cascade 동작 안 함 → 라우터마다 명시 cleanup 필수<br>- **진단 결과**: SPEAKER 262 + SENSOR 242 = **504 orphan** 잔존<br>- 안전점: `pre-cascade-fix` 태그 신설<br>**[Phase 9-1] orphan 504건 일괄 정리 마이그레이션**<br>- `app/migrations/v49_device_group_cascade_cleanup.sql` 신설 — BEGIN/DELETE/검증/COMMIT 단일 트랜잭션<br>- DELETE 504 (SPEAKER 262 + SENSOR 242) → 4 category 모두 orphan **0** ✅<br>- 잔존 252건 (CONTROLLER 2 / SENSOR 160 / ENCLOSURE 30 / LAMP 60) 모두 실 장비 대응<br>**[Phase 9-2] 3 라우터 cleanup 추가 (Camera 패턴 일관)**<br>- app/routers/lamps.py:436 — `db.delete(lamp)` 직전 `DeviceGroupMapping.device_id == lamp_id, category=LAMP` 명시 정리<br>- app/routers/speakers.py:491 — 동일 패턴 (category=SPEAKER)<br>- app/routers/enclosures.py:459 — 동일 패턴 (category=ENCLOSURE)<br>- 6 라우터(Camera/Controller/Sensor/Speaker/Enclosure/Lamp) 모두 동일 패턴 통일<br>- `DeviceGroupMapping` + `EnumDeviceCategory` import는 이미 존재 (다른 헬퍼에서 사용 중)<br><br>**[Phase 10] Controller→Sensor cascade 우회 정정 (같은 날 추가 — Phase 9 회신 후 차장님 추가 검증으로 발견)**<br>- 차장님 의문: "Controller 삭제 시 자식 Sensor도 사라졌는데 왜 활성 버그?"<br>- 실측 검증 (임시 Ctrl 1957 + Sensor 1958/1959 + 매핑): Controller row 삭제 ✅ + 자식 Sensor row ORM cascade 자동 삭제 ✅ **그러나** `device_group_mappings(category=SENSOR)` 2건 잔존 ❌ → 활성 버그 확정<br>- **근본 원인 사슬**: `Controller.sensors = relationship(cascade='all, delete-orphan')` (`models/device.py:112-117`) → controller 삭제 시 ORM이 자식 sensor row 자동 삭제 → `sensors.py:534 delete_sensor` 핸들러는 호출 안 됨 → category=SENSOR 매핑 cleanup 우회 → polymorphic device_id에 FK 없어 DB cascade도 동작 불가<br>- **SENSOR 242 orphan의 진짜 원인**: 시드 후 controller 2개 삭제했을 때 자식 sensor 2 × 121 = 242개 row만 자동 삭제되고 매핑은 잔존 (Phase 9-1에서 정리한 242건의 실체)<br>- **클라이언트팀 미발견 이유**: 보고서는 "스피커 케이스" 한정 (스피커 직접 DELETE만 검증). controller cascade 경로는 별도 시나리오라 잠복<br>- **정정**: `app/routers/controllers.py:560` `db.delete(controller)` 직전에 자식 sensor.id 일괄 조회 → category=SENSOR 매핑 명시 정리. `child_sensor_ids = [sid for (sid,) in db.query(Sensor.id).filter(Sensor.controller_id == controller_id).all()]` → `if child_sensor_ids: db.query(DeviceGroupMapping).filter(DeviceGroupMapping.device_id.in_(child_sensor_ids), DeviceGroupMapping.category_device == EnumDeviceCategory.SENSOR).delete(synchronize_session=False)`<br>- **검증**: 정정 후 동일 시나리오 (Ctrl 1960 + Sensor 1961/1962/1963 + 매핑 4건) 재현 → DELETE controller → 매핑 4건 모두 정리 (orphan 0) ✅ + 전체 DB orphan 0 유지<br>- **안전점**: `pre-controller-cascade-fix` 신설<br><br>**[Phase 11] controllers.py 문자열 리터럴 → Enum 통일**<br>- `_update_device_group_mappings` 헬퍼 호출 3곳 (`POST` line 320 / `PATCH` line 422 / `PUT` line 516)에서 문자열 리터럴 `"controller"` 전달 — 헬퍼 시그니처는 `EnumDeviceCategory` 타입 (`line 81`)<br>- 현재 SQLAlchemy 자동 강제 변환으로 동작 중이나 잠재 버그 (PostgreSQL enum 검증 시점에 따라 422/500 가능)<br>- 정정: 3곳 모두 `EnumDeviceCategory.CONTROLLER`로 통일 (DELETE 핸들러 + 헬퍼 시그니처와 동일 타입)<br>- DELETE 핸들러 cleanup 코드와 완전히 일관된 타입 흐름 회복<br><br>**[Phase 9~11 정합 검증]**<br>- 실 시나리오: 임시 Controller 생성 → 자식 Sensor 3개 → 그룹 매핑 4건 → Controller DELETE → 매핑 0건 (PASS)<br>- 전체 회귀: CONTROLLER 2 / SENSOR 160 / ENCLOSURE 30 / LAMP 60 = 252건 모두 실 장비 대응 (orphan 0)<br>- Container Up 8s healthy / Image rebuild<br>- Track B 적용 (5축 점수 3점)<br><br>**[Phase 9~11 잔존 (v5.0)]**<br>- 구조적 해결: `device_group_mappings.device_id` → `devices.id` FK + ON DELETE CASCADE (polymorphic이지만 모든 자식이 devices.id 공유) 또는 SQLAlchemy `event.listens_for(Device, 'before_delete')` 도입 — 라우터 누락 구조적 차단<br>- Phase 12 보류 (트랜잭션 일관성 / ConfigChangeLog commit 전 이동): 회귀 위험으로 v5.0 권고<br><br>**[Phase 12] Event 도메인 전수 정밀 분석 + Action invariant 가드 + Det/Mal PATCH 가드 + 시드 정합 회복 (같은 날 추가 — 차장님 추가 요청)**<br>- 차장님 요청: "Event 4종 (Connection/Detection/Malfunction/Action) 추가/삭제/수정 응답 + DELETE cascade 무조건 다 확인"<br>- Workflow 11 agent 정밀 분석 (993K token / 20분): Discovery + Per-event audit 4 + Live API 실측 4 + Adversarial verify + Synthesize → 4 event × 6 dimension = 24 셀 검증<br>- **결론**: CASCADE 정책 4종 모두 ✅ MATCH (DB CASCADE/SET NULL 의도 == 실측). PARTIAL_GAP — 5 항목 즉시 정정 필요<br><br>**[Phase 12-1] Action PATCH/PUT `from_event_id` 변경 원천 차단 (차장님 결재)**<br>- 차장님 결재: "from_event_id 전환은 무조건 못 바꾸게. 시도 자체를 원천적으로 막자"<br>- 실측 GAP 확정: PATCH로 `from_event_id` 전환 시 양쪽 source `action_reported` 재계산 누락 → 1:N invariant 위배 (A=True 0건 / B=False 1건 양쪽 깨짐)<br>- **정정 방식**: 재계산 추가가 아니라 **변경 자체 차단** (스키마에서 필드 제거 + `extra="forbid"`)<br>- `app/schemas/event.py` ActionEventUpdate (L371) — `from_event_id` 필드 제거 + `model_config = ConfigDict(extra="forbid")` 추가<br>- `app/schemas/event.py` ActionEventReplace 신규 클래스 (ActionEventCreate 직후) — PUT 전용, `from_event_id` 없음, `extra="forbid"`<br>- `app/routers/actions.py:34` import ActionEventReplace 추가<br>- `app/routers/actions.py` PATCH 핸들러 (L494) — `from_event_id` 검증 블록 제거 (dead code)<br>- `app/routers/actions.py:553` PUT 핸들러 — 시그니처 `ActionEventCreate` → `ActionEventReplace`, `event.source_event` 폴리모픽 관계 재사용, `event.from_event_id`는 절대 수정 안 함<br>- 실측 PASS: PATCH 422 "Extra inputs are not permitted" / PUT 422 동일 / PUT 정상 시나리오(type_event/content/user) 200 PASS<br><br>**[Phase 12-2] Detection/Malfunction PATCH 스키마 `action_reported` 제거 (가드 우회 차단)**<br>- 실측 GAP: PATCH로 `action_reported="False"` 강제 후 DELETE 호출 → 409 가드 우회 → ActionEvent 잔존 상태로 Detection 삭제 → `action_events.from_event_id=NULL` 고아화<br>- `app/schemas/event.py:147` DetectionEventUpdate — `action_reported` 필드 제거<br>- `app/schemas/event.py:260` MalfunctionEventUpdate — `action_reported` 필드 제거<br>- 핸들러 무변경 (Pydantic `extra=ignore` 기본값으로 클라이언트 입력 자동 폐기)<br>- 실측 PASS: Detection PATCH `{action_reported:"False"}` 호출 → 200 응답이지만 DB `action_reported='True'` 유지 (필드 폐기 확인)<br><br>**[Phase 12-3] 시드 1:N invariant 정리 마이그레이션 (1999건 회복)**<br>- 진단: detection_events 743건 + malfunction_events 1256건 = **1999건 invariant 위배** (`action_reported='True'`인데 actions_count=0)<br>- 원인: 시드 코드 L890-901에서 무작위 ~2000건에 `action_reported='True'` 추가 박아넣음 ("보고는 했지만 조치 미등록" 의도) → PRD_ActionEvent_1N_Refactoring v2.0 위배<br>- `app/migrations/v50_action_reported_invariant_fix.sql` 신설 — BEGIN/검증/UPDATE/검증/COMMIT 단일 트랜잭션<br>  - BEFORE: detection 743 위배 / malfunction 1256 위배 (총 1999)<br>  - UPDATE: 743 + 1256 = 1999건 True→False (`action_events` 매칭 없는 경우만)<br>  - AFTER: 잔여 위배 0 / 0 확인<br>- 검증 결과: `True` 5000건 (모두 ActionEvent 보유 ✅) / `False` 2997건 (모두 ActionEvent 0건 ✅) — 100% invariant 정합<br><br>**[Phase 12-4] 시드 코드 정정 (재발 방지)**<br>- `app/utils/init_sample_data.py:876-946` _create_action_events 함수 정정<br>- 제거된 코드: `remaining = all_event_ids[5000:]; reported_no_action = remaining[:2000]; update_true_ids = list(target_set | reported_set)` (무작위 True 배정)<br>- 정정 후: 5000 targets 만이 `action_reported="True"` 설정 (= ActionEvent 매칭)<br>- 함수 docstring에 INVARIANT 명시 — "무작위 True 배정 금지 — PRD v2.0 1:N count 종속 규약"<br>- 향후 down -v 후 재시드해도 invariant 위배 0건 보장<br><br>**[Phase 12-5] 검증 (모두 PASS)**<br>- 실측 4 시나리오:<br>  - ① PATCH from_event_id 변경 시도 → **422 거부 (Extra inputs are not permitted)** ✅<br>  - ② PUT from_event_id 변경 시도 → **422 거부** ✅<br>  - ③ Detection PATCH action_reported='False' 강제 → 200 + DB 'True' 유지 (필드 폐기) ✅<br>  - ④ PUT 정상 (type_event/content/user 변경) → 200 + content 변경 확인 ✅<br>- DB invariant 회복: detection True 1891 (모두 has_act>=1) / detection False 1109 (모두 zero_act) / malfunction True 3109 (모두 has_act>=1) / malfunction False 1888 (모두 zero_act)<br>- POST/DELETE 기존 로직(`update_source_action_reported` / `reset_source_action_reported`) 그대로 정상 동작 — 시퀀스 검증: 0건→1건(True)→3건(True)→2건(True 유지)→1건(True 유지)→0건(False 자동 복원) 6단계 모두 PASS<br>- Container Up healthy / Image rebuild / OpenAPI: ActionEventUpdate/ActionEventReplace `from_event_id` 제거 확인<br>- Track C 적용 (5축 점수 6점: 파일 5 + DB 마이그 1 / 아키텍처 1 polymorphic / 모듈 2 / 테스트 1 / 공수 1)<br><br>**[Phase 12-6] 잔존 (v5.0)**<br>- P1 잔존: GET list `start_date/end_date` 명세 required vs 코드 Optional (Det/Mal/Conn 공통, 차장 결재 — 코드 vs 명세 정정 방향)<br>- P1 잔존: Event 4종 PUT 핸들러 ConfigChangeLog UPDATED 호출 누락 (systemic 감사 추적)<br>- P1 잔존: Action POST device.status=ACTIVATED 광역 강제 (Malfunction 한정 정책이어야)<br>- P1 잔존: Detection PUT event.detail 할당 누락 (Malfunction과 비대칭)<br>- P2 6건: Action GET list source=NULL skip+total 감산 / end_date<start_date 검증 부재 / GET enum 검증 누락 / Action GET source=NULL시 404 데드락 / /{id}/actions pagination / Malfunction POST device.status ConfigChangeLog 누락<br>- P3 일괄: PUT message 'replaced'/'updated' / 404 메시지 포맷 / device_groups Nested description/device_count / 명세 §6.1.3/§6.2.3 device.status 부수효과 문서화<br><br>**[Phase 12 안전점]**: `pre-action-invariant-fix` (실 commit 직전 시점)<br><br>**검증**: 코드 3 파일 변경 (schemas/event.py + routers/actions.py + utils/init_sample_data.py) + 마이그레이션 1건 / DB 1999건 invariant 회복 / Image rebuild / 실측 4 시나리오 PASS / Workflow 11 agent (993K token / 20분).<br>**원칙 준수**: 하루 1 차수 묶음 (Phase 2~12 모두 v4.8 단일 행, 2026-06-22).<br>**롤백**: `git reset --hard pre-action-invariant-fix` (Phase 12만 회귀) / `git reset --hard pre-controller-cascade-fix` (Phase 10~12 회귀) / `git reset --hard pre-cascade-fix` (Phase 9~12 회귀) / `git reset --hard pre-events-delete-sweep` (Phase 8~12 회귀) / `git reset --hard pre-delete-sweep` (v4.8 전체 회귀). |
| v4.7 | 2026-06-21 | **하루 일괄 — Account/Auth/Session 도메인 전수 조사 (113 이슈) + DELETE 응답 envelope P0 정정 (4 endpoint)**<br><br>**[차수 배경]** v4.6 마감 후 차장님 의뢰: 계정/로그인/세션 도메인 전수 조사 + 구현 상태 면밀 검토. 동일 일자에 클라이언트팀이 별도 보고서 (API_Delete_Response_Inconsistency-report.md) 제출 — 장비 DELETE 응답 `data` 형식 불일치로 JsonReaderException 발생. 두 작업 동일 일자 묶음.<br><br>**[Phase 1] git 안전점 — pre-delete-sweep 태그 신설 (DELETE 작업 직전 보호)**<br>- 의미: P0 4 endpoint 정정 작업 전 안전점. 사고 시 `git reset --hard pre-delete-sweep`<br><br>**[Phase 2] Account/Auth/Session 전수 조사 (Workflow 13 agent, 1.15M token / 12분)**<br>- Discovery 1 + Per-feature 10 + Adversarial verify 1 + Synthesize 1<br>- 30 endpoints / 10 features / 6 DB tables / 8 enums 검토<br>- 평균 완성도 62.5% / OWASP 커버리지 41점 / **Verdict: FAIL**<br>- 이슈 113건: critical 13 / high 38 / medium 39 / low 23<br>- Adversarial: confirmed 105 / refuted 0 / additional 9<br><br>**[Phase 3] Feature별 완성도 (10건)**<br>- F01 로그인 62% (12 이슈, C2/H5) Audit missing<br>- F02 로그아웃 55% (8 이슈) Audit partial<br>- F03 토큰 갱신 55% (10 이슈, C2/H3) Audit missing<br>- F04 /me 82% (7 이슈) Audit missing<br>- F05 OAuth2 legacy 55% (10 이슈, C3/H4) Audit missing<br>- F06 User CRUD 72% (14 이슈) Audit full<br>- F07 비밀번호 변경 55% (11 이슈, C1/H4) Audit partial<br>- F08 잠금/해제/리셋 62% (12 이슈, C2/H4) Audit partial<br>- F09 UserGroup/권한 72% (9 이슈) Audit partial<br>- F10 Session 관리 62% (12 이슈) Audit partial<br><br>**[Phase 4] Top 5 권고 (P0~P1, ~45h 분량, v5.0 권고)**<br>1. [critical 6h] `require_admin/require_role` 의존성 신설 → RBAC 부재 해결 (F06/F08/F09/F10)<br>2. [critical 6h] `get_current_account_user`에 user_sessions 활성 검증 + is_active/is_locked 가드 → JWT 무효화 우회 해결<br>3. [critical 8h] `decode_refresh_token` 분리 + payload['type']=='refresh' 강제 + rotation/blacklist (F03)<br>4. [high 10h] AuditLog 본문 보강 + SESSION_CREATED/REFRESH/FAILURE 누락 해소<br>5. [high 15h] 비밀번호 정책 정비 + 변경 시 세션 무효화 + 만료/재사용 금지<br><br>**[Phase 5] DELETE 응답 P0 정정 (4 endpoint)**<br>- 클라이언트팀 보고: Lamp/DG는 `data: {객체}` → 나머지 5건은 `data: null` → JsonReaderException 발생<br>- Workflow 8 agent 검증 (409K token / 4분): confirmed 2 / refuted 0 / additional 5<br>- app/routers/lamps.py:409 — `ApiSingleResponse[dict]` → `[None]` + return `data={"id":lamp_id,"deleted":True}` → `data=None`<br>- app/routers/device_groups.py:608 — `data={"id":group_id}` → `data=None`<br>- app/routers/servers.py:461 — sweep (보고서 §6 추가 발견)<br>- app/routers/server_categories.py:370 — sweep<br>- 메시지에 id 포함 보존: `f"Lamp {id} 삭제 성공"` — 감사 추적성 유지<br><br>**[Phase 6] 검증 (모두 PASS)**<br>- OpenAPI 9 endpoint $ref = `ApiSingleResponse_NoneType_` 통일 ✅<br>- 실 API: Lamp/Server/ServerCategory/DeviceGroup DELETE → `data is None: True` ✅<br>- Container Up 8s healthy / Image rebuild 완료<br>- Track B 적용 (5축 점수 3점)<br><br>**[Phase 7] 산출물**<br>- docs/Analysis/Account_Auth_Session_Analysis_v4.6.md (16KB / 236 라인)<br>- docs/Analysis/Device_Delete_Response_Verification_v4.6.md (9KB)<br>- v4.6 Phase 9 EM DELETE 'data': {}와의 차이 명시 (Device CRUD vs EM 도메인 별개)<br><br>**[Phase 8] v4.6 명세 정합 회복**<br>- v4.6에서 누락한 docs/Analysis/ 디렉터리 신설 + .gitignore 예외 추가<br>- 보고서 docs/Analysis/Device_Delete_Response_Verification_v4.6.md 신설<br><br>**검증**: 코드 4 파일 변경 / DB 변경 0 / Image rebuild / Container healthy / OpenAPI 9 endpoint NoneType 통일.<br>**원칙 준수**: 하루 1 차수 묶음 (Account 분석 + DELETE P0 정정 모두 v4.7 단일 행).<br>**롤백**: `git reset --hard pre-delete-sweep` (P0 4 endpoint 회귀). |
| v4.6 | 2026-06-19 | **하루 일괄 — Critical Mismatch 정정 (P0 1 + P1 8) + Camera Preset 감시금지구역 신설 + 매니저 통합 가이드**<br><br>**[차수 배경]** v4.5에서 발견한 26 도메인 × Workflow 28 agent 3-way 정합 검증에서 Critical Mismatch 10건 식별 (운영 500 1건 + 매니저 KeyError 4건 + 422 3건 + 응답형식 1건 + envelope 1건). 모든 mismatch는 옛 차수(v1.x~v4.3)에서 코드/PRD 변경 시 명세 본문 동기화 미실시로 누적된 잠복 부채. 우리 v4.4/v4.5 작업이 새로 만든 mismatch 0건 입증.<br><br>**[Phase 1] git 안전점 — v4.5-final-stable @ e7a611e 신설**<br>- 의미: v4.5 마감 시점 보호 (Workflow 분석 + minimal 6 그룹 적용 + multi-line Column 정정 후)<br>- 사고 시 복귀: `git reset --hard v4.5-final-stable`<br><br>**[Phase 2] M01 P0 핫픽스 — ServerCategory 500 차단**<br>- app/routers/server_categories.py:123-138 — Server 모델에 없는 `cpu_usage/ram_usage/disk_usage/network_throughput` 4개 인자 → ServerMetrics 분리(v2.9) 이후 잠복하다 발견. `user_name/user_password/threshold_config` 정확한 필드로 교체. 즉시 200 회복<br><br>**[Phase 3] 명세 정정 7건 (M02~M10 명세 본문)**<br>- M02/M03 §6.5.1/§6.5.2: detection-log `action`(1:1) → `actions`(1:N) — PRD ActionEvent 1N v2.0 반영. 도입부 + 응답 예시 4곳 + 본문 설명 일괄 정정<br>- M05 §8.6.3: server metrics/latest 응답 키 `data.metrics/threshold_config` → 코드 `data.server_id/server_name/latest_metrics`<br>- M06 §10.4.4: PDF 다운로드 JSON envelope → 실제 `application/pdf` 바이너리 스트림 (FileResponse 정합)<br>- M08 §6.2.5: Malfunction PUT body에서 `action_reported` 제거 (v2.8 시스템 자동관리 정책)<br>- M09 §6.4.2: Action GET query 모두 optional + `from_event_id` 필터 신규 명시<br>- M10 §6.4.5: Action PUT body 2필드 예시 → 4 필드 (`type_event`, `content`, `user`, `from_event_id`) 모두 required<br><br>**[Phase 4] M07 코드 정정 — system-events envelope 표준화**<br>- app/routers/servers.py:191 — `@router.get` 데코레이터에 `response_model=ApiSingleResponse[dict]` 부착<br>- 응답 body를 명세 §8.3.7 표준 envelope으로 변경: `data: {items, total, pagination}`<br>- Swagger OpenAPI 200 schema 정상 노출 ($ref 부착)<br><br>**[Phase 5] Camera Preset 감시금지구역 신설 (차장 결재 2026-06-19, 단순화 확정)**<br>- DB: app/migrations/v48_camera_preset_restricted_zone.sql — `camera_presets`에 `is_restricted_zone BOOLEAN NOT NULL DEFAULT false` 1 컬럼 추가. 기존 row backfill 자동 false<br>- Model: app/models/camera_preset.py — `CameraPreset.is_restricted_zone` Column 추가 (multi-line, JSON/JSONB 사용 안 함)<br>- Schema: app/schemas/camera_preset.py — `CameraPresetBase`/`Update`/`Response`/`DetailResponse` 4 클래스에 신규 필드 추가 (default=false로 backward-compatible)<br>- 명세: §5.7 Camera Preset 도입부에 `is_restricted_zone` 단일 플래그 명시 + 매니저 통일 처리 정책 (RTSP/녹화/이벤트/화면 모두 차단)<br>- 가이드: docs/v46_camera_preset_restricted_zone_guide.md 신설 — VMS/NVR/db_monitor/Central UI 4 매니저별 처리 가이드<br>- **단순화 경위**: 최초 Option C(`restricted_actions` 4종 enum list 선택)로 적용 → 차장 추가 결재로 단순화 (`is_restricted_zone` bool 1개로 통일). `restricted_actions` 컬럼/Enum/Schema 필드 모두 제거. **차장 의도 충실**: 매니저가 "감시금지 = 모두 차단" 단일 정책으로 통일 처리<br><br>**[Phase 6] 보류 — M04 high risk (차장 결재 필요)**<br>- M04 `GET /api/enclosure-metrics` — 코드 flat vs 명세 items/total/pagination drift<br>- backward-INCOMPATIBLE envelope 변경 위험 (Central UI 함체 모니터링 패널 영향)<br>- 결재 사항: item shape (코드 정정 vs 명세 정정 방향) — v4.7 차수로 분리 권고<br><br>**[Phase 7] PRD + 산출물**<br>- docs/PRD_v4.6_Critical_and_Preset.md (39KB, 임시 마크다운)<br>- docs/v46_camera_preset_restricted_zone_guide.md (매니저 통합 가이드)<br>- docs/v45_3way_critical_mismatches.html (37KB, 10건 시각화)<br>- Workflow Critical PRD: 11 agent / 680k token / 5.4분<br>- Workflow Camera Preset: 9 agent 설계 시도 → 죽음 → main에서 직접 적용<br><br>**[Phase 8] 검증 (모두 통과)**<br>- M01 검증: GET /api/servers/categories/1 → HTTP 200 (이전 500 해소)<br>- M07 검증: Swagger response 200 schema = ApiSingleResponse_dict_ $ref 정상<br>- Camera Preset 신규 필드: DB 2 컬럼 + OpenAPI CameraPresetResponse/Create에 노출<br>- Container: Up 8s healthy / Image rebuild 완료<br>- 명세 정정 7건 모두 본문 적용 확인<br><br>**[Phase 9] 정합 9중 (코드 ↔ 명세 ↔ Swagger ↔ DB ↔ Image ↔ Container ↔ PRD ↔ 가이드 ↔ git)**<br>- 코드 5 파일 변경 (server_categories / servers / camera_preset 모델/스키마 / enums)<br>- DB 마이그레이션 1건 (v48)<br>- 명세 정정 7 위치 + §5.7 도입부 갱신<br>- Swagger 노출 갱신 (response_model + 신규 스키마)<br>- 매니저 가이드 1 파일 신설<br>- PRD 본문 1 파일<br>- git commit + v4.6-final-stable 태그<br><br>**[Phase 10] 시드 데이터 재설계 + pagination 안정화 검증 (차장님 명세 — 같은 날 추가)**<br>- **차장님 시드 명세 (정확 매칭)**: 제어기 4 / 제어기1: 펜스센서 100(1~100) + 복합센서 21(180~200) / 제어기2: 동일 / 제어기3: 스마트복합 60(1~60) / 제어기4: 스마트센서 100(1~100) / 카메라 300 / 스피커 200 / 함체 30<br>- **시드 함수 재작성**: app/utils/init_sample_data.py L250~480 — `_create_devices` 전면 재구현. Sensors 350→**402**, Cameras 30→**300**, Speakers 30→**200**, Enclosures 30 유지. EnumDeviceType 매핑: 펜스→Fence, 복합→Multi, 스마트복합→SmartCompound, 스마트→SmartSensor<br>- **DeviceGroup 시드도 동기 조정**: 5구역(A~E) → 4구역(A~D). PTZ + 긴급방송 그룹 인덱스 시프트<br>- **Pagination 안정성 진단 결과**: 정책 `ORDER BY id ASC NOT NULL PK` — unique 보장됨. Camera 300/30 페이지 + Sensor 402/21 페이지 직접 호출 검증: 중복 0건 / 누락 0건 / 순서 ASC 100% 일관 → **PASS**<br>- **잠재 위험 7건 식별 (PRD 참조)**: row drift (동시 INSERT) / 큰 offset 성능 (28K 이벤트) / cursor pagination 미지원 / total count 캐시 부재 등. 현 디바이스 규모(<500)에선 미체감. v4.7+ 별도 PRD 권고<br>- **DB 재시드 절차**: TRUNCATE devices RESTART IDENTITY CASCADE + Container restart → 시드 startup hook 자동 재실행. 데이터 손실은 의도된 초기화 (시드만 영향)<br>- **검증**: DB 카운트 controllers=4 / sensors=402 / cameras=300 / speakers=200 / enclosures=30 / lamps=30 모두 명세 일치. 센서 분포 (ctrl/type/count/range): 1/Fence/100/1~100, 1/Multi/21/180~200, 2/Fence/100/1~100, 2/Multi/21/180~200, 3/SmartCompound/60/1~60, 4/SmartSensor/100/1~100 — 6 분포 모두 일치<br>- **Workflow 4 agent**: 357,749 token / 89 tool calls / 11분 (Inventory + Design + Apply + Verify)<br><br>**원칙 준수**: 하루 1 차수 묶음 (오늘 분량 모두 v4.6 단일 행 안). M04는 high risk라 v4.7로 분리.<br>**롤백**: 사고 시 `git reset --hard v4.5-final-stable` (commit 단위 revert 가능). DB 컬럼 drop SQL은 가이드 §8 참고 (데이터 보존 위해 권장 안 함). |
| v4.5 | 2026-06-19 | **하루 일괄 — 잔존 부채 정밀 식별 + 시나리오 시뮬레이션 + PRD 작성 (코드 변경 0)**<br><br>**[배경]** v4.4 마감 후 전체 pytest 실행 결과 174 fail 노출. v4.4가 새로 깨뜨린 건 0건 — 모두 옛 차수(v2.9~v4.0)에서 코드 변경 시 테스트 미동기화로 누적된 잔존 부채. 매니저 통합 시작 전 정밀 정리 PRD 필요.<br><br>**[Phase 1] git 안전점 — v4.4-final-stable 태그 신설**<br>- 태그: `v4.4-final-stable` @ commit `050cf6d`<br>- 의미: v4.4 완성 시점 보호 (Phase 1~5 + multi-line Column 5건 자체 정정 + user_password 평문 응답 복원). 사고 시 `git reset --hard v4.4-final-stable`<br><br>**[Phase 2] Workflow 46 agent 정밀 분석 — 부채 15 그룹 × (분석 + 시나리오 minimal + scenario full)**<br>- Discovery 1 agent + Per-Group Analysis 15 agent + Scenario Minimal 15 agent + Scenario Full 15 agent + PRD Synthesis 1 agent = **46 agent 병렬**<br>- 사용량: 3,492,386 token / 935 tool calls / 16분<br>- raw 결과: `tasks/w2uvtdbg0.output` (266KB)<br>- 결과 PRD: **`docs/PRD_v4.5_Debt_Cleanup.md`** (32KB)<br><br>**[Phase 3] 부채 인벤토리 — 15 그룹 / 174 fail / 30h 작업량**<br>- G01 Camera URLs 통합 (StreamUrls 삭제) — 23건 P2<br>- G02 Device is_enable 필수화 + nested 스키마 — 26건 P2<br>- G03 ConfigChangeLog 응답 envelope — 18건 P2<br>- G04 ServerMetrics 분리 — 14건 P2<br>- G05 ActionEvent 1:N 구조 변경 — 11건 P2<br>- G06 PDF/Report 시스템 변경 — 12건 P2<br>- G07 Account/Auth role enum 대문자 — 12건 P2<br>- G08 Camera Preset/ROI/include params — 11건 P2<br>- G09 Logs/Audit 1:N 응답 — 10건 **P1** (매니저 영향)<br>- G10 Sensor/Speaker/Enclosure geolocation 잔존 가정 — 9건 P2<br>- G11 EM 단건 라우터 envelope — 7건 P2<br>- G12 EM Bulk envelope 디테일 — 8건 **P1** (v4.4 직접 영향)<br>- G13 Enum NONE / device_category 추가 — 4건 P2<br>- G14 rtsp_uri/rtsp_port 컬럼 삭제 잔존 — 4건 P2<br>- G15 기타 (config/device_version/event base) — 8건 P3<br><br>**[Phase 4] 시나리오 결정 — 13 minimal + 2 full**<br>- **Minimal** (테스트 갱신만, 코드 변경 0): 13그룹 / 158건 회복 / ~23h<br>- **Full** (코드+테스트+명세 정합): 2그룹 (G09 + G12) / 16건 회복 / ~7h<br>- 합계: **30h 으로 174 fail 100% 해소 가능**<br><br>**[Phase 5] 차수별 분산 — 4차수 분할 권고**<br>- **v4.5** (즉시, 1주차) — G11/G14/G05/G13/G10/G07: **5.5h** (단순 minimal, CI Red 즉시 해소)<br>- **v4.6** (2주차, 매니저 통합 직전) — G09/G12 full: **13h** (매니저 영향 P1 정합)<br>- **v4.7** (3주차) — G02/G03/G08/G15: **7.3h** (잔존 minimal)<br>- **v5.x** (백로그) — G01/G04/G06: **4.5h** (구조 변경 동반, 매니저 통합 완료 후)<br><br>**[Phase 6] Open Decisions — 차장 결재 5건 (PRD §6 상세)**<br>- D1: ApiResponse envelope 표준화 — pagination 사이드카 vs 통합 (G03/G09 정합 방향)<br>- D2: EnumDeviceCategory LAMP 매니저(.NET Enums) 동기화 — NATS payload round-trip 검증 (G13 full 조건)<br>- D3: Server 인라인 메트릭 v2.9 분리 확정 — db_monitor 인제스트 경로 전환 (G04 v5.x 선행)<br>- D4: DetectionLog 1:1 → 1:N actions 계약 변경 공식화 — PRD + Central UI ViewModel 동시 수정 (G09 full 조건)<br>- D5: ROICreate.points 필수화 정책 확정 — '빈 ROI 생성' 워크플로 폐기 vs 유지 (G08 full 조건)<br>- 추가: SpeakerNestedResponse.category_device 제거(SPEC-6.1) / .env.example 듀얼 모드<br><br>**[Phase 7] Risk Log — 7건 (PRD §5 상세)**<br>- R1 매니저 영향 High: G09 DetectionLog action(single) → actions(list) 계약 변경 → Central UI + db_monitor 동시 수정 필요<br>- R2 매니저 영향 High: G12 EM Bulk ConfigChangeLog after_state key 변경 → 감사 리포트/UI 토스트 라벨 영향<br>- R3 매니저 영향 Medium: G07 /api/auth/me role 케이스 변경 — minimal에서 보류로 회피<br>- R4 매니저 영향 Medium: G04 Server 인라인 메트릭 db_monitor v1.6 잔존 — grep 후 v5.x 동시 전환<br>- R5/R6 사이드 이펙트: G02 conftest SQLAlchemy 환경 의존, G06 OS별 분기 회귀 가드<br>- R7 데이터 손실 Low: G09/G12 full은 OpenAPI 스키마만 변경, DB 마이그레이션 없음 (단 ActionEvent.from_event_id UNIQUE 점검 필요)<br><br>**[Phase 8] 명세서 — 본 행 신설 (코드/DB/Image/Container 변경 0)**<br>- 본 차수는 **분석 + 결재 차수** — 실제 정정 코드 변경은 v4.6/v4.7/v5.x에서 개시<br>- 영향: docs/PRD_v4.5_Debt_Cleanup.md 1 파일 + 명세 변경 이력 본 행 + git commit 1개<br><br>**[Phase 9] 즉시 minimal 6 그룹 적용 — 차장 결재 후 작업 (Workflow 8 agent, 같은 날 추가)**<br>- G05 ActionEvent 레거시: 11→8 (3 회복) — 2 모듈 skip + from_event_id detail dict 전환 + 3 method skip<br>- G07 UserSession/Account: 12→0 (12 회복) — UserRole `admin`→`ADMIN`, UserSession `login_at/last_activity`→`created_at/updated_at`, /me 토큰 종속 7건 skip<br>- G10 Sensor/Speaker/Enclosure: 9→0 (9 회복) — `is_enable=True` 4건 추가, SpeakerResponse `category_device` 제거, IpController→IoController 3건<br>- G11 EM 단일 라우터 envelope: 7→2 (5 회복) — speakers/lamps/cameras DELETE 응답에 `'data': {}` 추가 (운영 코드 3 파일 변경)<br>- G13 Enum: 4→0 (4 회복) — `EnumEventCategory`→`EnumMappingEventCategory`, `EnumDeviceCategory` 3→6 (SPEAKER/ENCLOSURE/LAMP)<br>- G14 Camera URLs: 4→0 (4 회복) — test_device_base_model.py rtsp_uri/rtsp_port kwargs 8 lines 삭제<br>**합계**: 47 기대 → **37 실회복** (G11 5/7, G05 3/11, 그 외 4그룹 100%), 신규 회귀 0, **verdict PASS**<br>**잔존 매핑**: G05 잔존 8건 → v4.6 G05-cleanup (레거시 모듈 2개 삭제), G11 잔존 2건 → v4.6 G11-full (cross-file 테스트 격리 결함)<br>**파일 변경**: 운영 코드 3 (event_mapping_cameras/speakers/lamps DELETE) + 테스트 17 = **20 파일**<br>**pytest 전체**: 2381 / passed **2218** (+30) / failed **126** (-48) / skipped **35** (+18) / errors 2<br>**Workflow 사용량**: 8 agent / 505,728 token / 119 tool calls / 15분<br><br>**검증**: 코드 변경 = 라우터 envelope 3건만 (DELETE `data: {}`), DB 변경 0, Image 변경 = 라우터 동기화 + 재시작, Container Up healthy, 실 API 정상, OpenAPI 정상.<br>**롤백**: 사고 시 `git reset --hard v4.4-final-stable` (commit 단위 revert 가능).<br>**원칙 준수**: 하루 1 차수 묶음 원칙 — Phase 1~9 모두 v4.5 1차수 안에 통합. |
| v4.4 | 2026-06-18 | **하루 일괄 — Bulk API 4단계 정합화 (Phase 1~4) + v4.5 분리 작업**<br><br>**[Phase 1] 명세 정정 — GAP 14건 (5.6.9 / 7.3.9 / 7.3.10 / 7.5.9 / 7.5.10)**<br>- G1 P0 치명 3건: §7.3.9 Request Body 6필드 교체, `created_ids/config_ids` = 매핑 row PK 명시 — 매니저가 명세대로 호출 시 즉시 422 실패 차단<br>- G2 P1 약속: skipped/not_found_config_ids placeholder 명시 → Phase 2에서 실 분류 활성화<br>- G3 P2 트리거명: §7.5.9/10 `trg_sync_eml_insert/delete` → `trg_sync_eml_ins/del`, "§6 매트릭스" dangling reference 제거<br>- G4 P3 정합성 6건: §5.6.9 meta.message → data.message, 영문 leak 제거, §7.5 헤더 중복 통합, §7.3.5 → §7.3.6, /members → /devices 등<br>- PRD: docs/PRD_v4.4_Phase1_SpecSync.md (구 PRD_BulkAPI_Spec_Sync_v4.4.md)<br>- 검증: docs/sim/raw_data.json 19 시나리오 + docs/workflow_audit_v3/a01~a09.md 9 agent<br>- 롤백 태그: pre-prd-v44, pre-spec-master-sync<br><br>**[Phase 2] 코드 보강 — PR-A/B/C/D**<br>- PR-A: 3 라우터 ConfigLog `if` 가드 제거 → 0건 case도 무조건 발행 (감사 가능)<br>- PR-B: skipped/not_found_config_ids 실 분류 활성화 (Camera/Speaker/Lamp 3 라우터)<br>- PR-C: Lamp `color/buzzer_sound/light_mode` plain str → Pydantic Enum (color="Purple" 500 → 422)<br>- PR-D: EventMapping 6 핸들러 `response_model=dict` → `ApiSingleResponse[T]` + 404 응답 정의 + meta envelope 자동 주입<br>- 롤백 태그: pre-v45<br><br>**[Phase 3] Post-Mortem — 보안 + 잔존 GAP 9건 (FR-1~12 중 P0/P1)**<br>- FR-1 JWT_SECRET_KEY validator (staging/prod 디폴트 거부) / ~~FR-2 user_password 응답 제거~~ → **Phase 5 결재로 응답 복원** (운영 사용 케이스: 등록 직후 확인 / 관리자 화면 / 통합상황도 자동연결. 보안 정책[롤 기반 / 별도 엔드포인트 / 마스킹]은 v4.5에서 결정) / FR-3 CORS 화이트리스트 / FR-4 .NET 사본 4곳 가이드 (docs/v44_sync_guide.md) / FR-5 same-request dedup 보강 / FR-8 db_triggers.py:97-108 dead branch 제거 / FR-9 AUTH_MODE 환경별 분기 / FR-10 §7.5.7 번호 중복 재채번 (`MappingLamp 독립 GET` → §7.5.9, 본 차수 §7.5.9/10 → §7.5.10/11 시프트) / FR-12 .gitignore PRD 추적 예외<br>- PRD: docs/PRD_v4.4_Phase3_PostMortem.md (구 PRD_BulkAPI_PostMortem_v4.6.md)<br>- 롤백 태그: pre-v46<br><br>**[Phase 4] 지향성 + JSON→JSONB 일관성 복원 — FR-13 / FR-14**<br>- FR-13: `Geolocation`에 `heading: Optional[float] (0~360°)` 추가 — Camera/Speaker/Sensor 부채꼴 시각화. 6 디바이스 테이블 row backfill (heading:null) 완료<br>- FR-14: **PRD ↔ 구현 일관성 복원** — PRD 파일명(JsonB) + Docstring 23곳 "JSONB" 의도였으나 SQLAlchemy `JSON` import 실수로 23 컬럼 모두 `json` 저장. 8 파일 18 사용처 정정 + ALTER TYPE jsonb 일괄 (한 트랜잭션). 데이터 손실 0<br>- 마이그레이션: app/migrations/v47_json_to_jsonb_and_heading.sql<br>- PRD: docs/PRD_v4.4_Phase4_Directional_JsonB.md (구 PRD_v4.7.md)<br>- 롤백 태그: pre-v47<br><br>**[Phase 5] FR-6/FR-7 — 본 차수 통합 처리 + JSONB SQLite 호환**<br>- FR-6 pytest 정합: 13건 → 8건 잔존 (envelope key `camera_ids/speaker_ids/lamp_ids` → `config_ids` 정정, FR-8 dead branch 옛 테스트 2건 skip 마크). 잔존 8건은 skip_duplicates / log_config_change 디테일 (매니저 영향 0)<br>- FR-7 단건 21건 response_model: `Column(JSON)` → `ApiSingleResponse[dict]` 일괄 (Camera/Speaker/Lamp 각 7건). OpenAPI Schema 노출 (data 구체 타입은 v4.5에서 정확화)<br>- **JSONB SQLite 호환** (Phase 4 사이드이펙트 정정): SQLAlchemy `Column(JSONB)` → `Column(JSON().with_variant(JSONB(), "postgresql"))` 패턴으로 dialect-aware. Postgres 운영=jsonb, SQLite 테스트=json fallback. 23개 컬럼 일괄 적용<br>- 검증: pytest 56/64 (skip 2건 + 잔존 8건). OpenAPI 21건 ApiSingleResponse[T] 노출 확인<br>- FR-11 (JWT jti 블랙리스트, 4.5h 분량)은 별도 차수(v4.5)로 분리<br><br>**검증**: 실 API 4 시나리오(CAM dedup, 0건 ConfigLog, LMP Purple 422, heading 응답) 모두 통과. pytest 53/66 (FR-8 dead branch 제거로 row-level 옛 테스트 2건 의도된 실패 + Phase 5 잔존). DB: json 0건 / jsonb 23건. Docker Image: api-test-server:latest (da8e01c0fad6, 2026-06-18 16:27).<br>**커밋 단위 추적성**: 13 commit 보존 (rebase 없음). 5개 롤백 태그 (pre-prd-v44, pre-spec-master-sync, pre-v45, pre-v46, pre-v47) commit hash 그대로 유효.<br>**원칙 준수**: 하루 1 차수 묶음 원칙 적용 (구 v4.4~v4.7 4 차수를 본 v4.4로 통합) |
| v4.3 | 2026-06-17 | **ActionEvent 1:N 관계 반영 + Bulk API 7건 신설 + statement-level 트리거 마이그레이션 (6.1.7, 6.2.7, 6.4, 5.6.9, 7.3.9, 7.3.10, 7.4.9, 7.4.10, 7.5.9, 7.5.10, 부록 12.1)**<br><br>**[1. Detection/Malfunction Action 조회 → 1:N (6.1.7, 6.2.7)]**<br>- Endpoint 변경: `/{event_id}/action` → `/{event_id}/actions` (복수형)<br>- 응답 형식 변경: 단건 객체 → 배열(`data: [...]`)<br>- 메시지 변경: "Action event retrieved" → "Action events retrieved"<br>- Action Event 미존재 시 빈 배열 반환 (404 제거)<br><br>**[2. Action 생성/삭제 로직 변경 (6.4.1, 6.4.6, 6.4.7)]**<br>- 1:1 제약 제거 → 1:N 관계: 하나의 source event에 여러 ActionEvent 생성 가능<br>- 삭제 시 count 기반 복원: 남은 ActionEvent가 0개일 때만 `action_reported`를 "False"로 복원<br>- 6.1.6/6.2.6 삭제 주석 동기화<br><br>**[3. DeviceGroup 디바이스 벌크 해제 신설 (5.6.9)]**<br>- 신규 엔드포인트: `DELETE /api/devices/groups/{group_id}/devices` (body: `device_ids: List[int]`, 1~100)<br>- 단건 해제(`5.6.8`)의 N회 호출을 1회로 통합 — 그룹 편집 UI 라운드트립 최소화<br>- 응답 3분류: `removed_device_ids` / `skipped_device_ids` / `not_found_device_ids` (멱등성 보장, 전체/부분 해제 모두 200)<br>- ConfigChangeLog: `EnumConfigResourceType.DEVICE_GROUP` / `EnumConfigActionType.UNASSIGNED` 1건/요청 (`before_state.device_ids` + categories)<br>- AuditLog 도메인 외 (AuditLog는 USER/USER_GROUP/USER_SESSION/PASSWORD에 한정, `PRD_Audit_Log.md §2.2.2`)<br>- NATS: `device_group_mappings` row-level → statement-level 트리거 마이그레이션 — 영향 받는 group_id당 `SYNC_DEVICE_GROUP/UPDATED` 1건만 발행 (등록 API도 자동 수혜, PostgreSQL 10+ `REFERENCING NEW/OLD TABLE` 필요)<br><br>**[4. EventMapping SubResource 벌크 API 6건 신설 — §7.3.9/§7.3.10/§7.4.9/§7.4.10/§7.5.9/§7.5.10 본문 신설 + 부록 §12.1 표 동기화 + Swagger OpenAPI 자동 노출]**<br>- Camera: `POST .../cameras/bulk` (벌크 등록 `items: List[Create]`), `DELETE .../cameras` (벌크 해제 `config_ids: List[int]`)<br>- Speaker: `POST .../speakers/bulk` + `DELETE .../speakers` (동일 패턴)<br>- Lamp: `POST .../lamps/bulk` + `DELETE .../lamps` (동일 패턴)<br>- 응답: 등록은 `created_ids` + `failed_items` (best-effort 부분 성공 시맨틱), 해제는 `removed/skipped/not_found_config_ids` 3분류 (DeviceGroup 미러)<br>- 기존 단건 CRUD(`{config_id}` 경로)는 그대로 유지 — 다중 선택 액션과 단건 액션 모두 지원<br>- NATS: `event_mapping_cameras/speakers/lamps` 3 테이블 row-level → statement-level 트리거 마이그레이션 — 영향 받는 `event_mapping_id`당 `SYNC_EVENT_MAPPING/UPDATED` 1건만 발행 (실측: 5건 등록/해제 시 5건 → 1건, 80% 감소)<br><br>**[5. §7.5 번호 중복 알림 (사후 정정 필요, 본 차수에서는 §7.5.9/§7.5.10으로 우회)]**<br>- 기존 명세에 #### 7.5.7 FK 정책 및 CASCADE 동작과 #### 7.5.7 MappingLamp 전체 목록 조회 (독립)가 같은 번호로 중복 채번됨 (v3.8에서 §7.3.8/§7.4.8 패턴 미준수)<br>- 본 차수에서는 신설 번호를 §7.5.9 / §7.5.10으로 부여하여 중복을 피하되, 기존 중복 자체는 차기 차수(v4.4)에서 후자 §7.5.7을 §7.5.9로 재채번하고 본 신설 번호를 §7.5.10/§7.5.11로 재조정 권장 |
| v4.2 | 2026-03-03 | **Event Statistics API 신규 (6.7)**<br><br>**[1. Event Statistics API 신규 (6.7)]**<br>- GET /api/events/statistics/summary: 이벤트 타입별 건수 요약 (원형 그래프 + 요약 카드)<br>- GET /api/events/statistics/trend: 시간대별 이벤트 건수 추이 (라인 차트)<br>- GET /api/events/statistics/by-device: 제어기별/카메라별 이벤트 건수 (막대 그래프)<br>- GET /api/events/statistics/dashboard: 대시보드 통합 (summary + trend + by-device 단일 호출)<br>- 탐지 이벤트 센서/카메라 분리 집계 (Device.category_device 기준)<br>- 파생 메트릭: daily_averages (일평균), active_devices (활성 장비 수)<br>- EventSummaryResponse, EventTrendResponse, EventByDeviceResponse, EventDashboardResponse 스키마<br><br>**[2. ControllerStats action 필드 추가 (6.7.3)]**<br>- controllers[].action: 제어기 소속 센서의 탐지 이벤트에 대한 조치 건수<br>- 집계 경로: ActionEvent.from_event_id → Event.device_id → Sensor.controller_id<br>- dashboard API (6.7.4) by_device.controllers에도 동일 적용 |
| v4.1 | 2026-02-26 | **DeviceGroup 지원 완성 (5.4, 5.5, 5.11)**<br><br>**[1. Speaker API DeviceGroup 지원 (5.4)]**<br>- Create/Update Request에 `group_ids` 필드 추가 (optional, array[int])<br>- Response에 `device_groups` 필드 추가 (목록조회, 상세조회, 생성, PATCH, PUT)<br><br>**[2. Enclosure API DeviceGroup 지원 (5.5)]**<br>- Create/Update Request에 `group_ids` 필드 추가 (optional, array[int])<br>- Response에 `device_groups` 필드 추가 (목록조회, 생성, PATCH, PUT)<br><br>**[3. Lamp API DeviceGroup Request 추가 (5.11)]**<br>- Create/Update Request에 `group_ids` 필드 추가 (optional, array[int])<br>- Response의 `device_groups`는 v3.4에서 이미 지원<br><br>**[결과]** 6개 장비 타입(Controller, Sensor, Camera, Speaker, Enclosure, Lamp) 모두 DeviceGroup N:N 관계 Request/Response 완전 지원 |
| v4.0 | 2026-02-19 | **Thumbnail API 신규 (6.6)**<br><br>**[1. Thumbnail API 신규 (6.6)]**<br>- POST /api/thumbnails: 썸네일 이미지 업로드 (multipart form data, 클라이언트 지정 file_name)<br>- GET /api/thumbnails: 썸네일 목록 조회 (날짜 필터링, 페이지네이션)<br>- GET /api/thumbnails/{id}: 썸네일 메타데이터 조회<br>- GET /api/thumbnails/{id}/image: 썸네일 이미지 다운로드 (ID 기반, FileResponse)<br>- GET /api/thumbnails/images/{file_name}: 썸네일 이미지 다운로드 (파일명 기반, FileResponse)<br>- DELETE /api/thumbnails/{id}: 썸네일 삭제 (파일 + DB)<br>- ThumbnailResponse 스키마: image_url computed field (`/api/thumbnails/images/{file_name}`)<br>- 파일 저장 구조: {날짜}/{client_file_name} (밀리초 포함 네이밍 컨벤션)<br>- DetectionEvent와 FK 없이 연결 (detail.thumbnail HTTP URL 참조) |
| v3.9 | 2026-02-13 | **API 엔드포인트 정합성 동기화 (12.1 부록 수정, 누락 섹션 추가)**<br><br>**[1. 12.1 부록 정합성 수정]**<br>- Lamps 6개 엔드포인트 추가<br>- Camera Settings 3개 엔드포인트 추가<br>- Proxy Settings 3개 엔드포인트 추가<br>- Event Mapping Lamps 6개 엔드포인트 추가<br>- Controllers, Sensors, Events(4종) PUT 엔드포인트 6건 추가<br>- Server system-events, Enclosure-metrics flat, Report preview-page 추가<br>- Report Preview (Non-API) 경로 수정<br><br>**[2. Server 시스템 이벤트 조회 추가 (8.3.7)]**<br>- GET /api/servers/{server_id}/system-events: 서버별 시스템 이벤트 필터 조회<br><br>**[3. Enclosure Metrics 독립 목록 추가 (5.5.13)]**<br>- GET /api/enclosure-metrics: 전체 함체 메트릭 독립 조회 (flat_router 패턴)<br><br>**[4. Report Preview Page 경로 수정 (10.5)]**<br>- GET /reports/preview/{id} → GET /api/reports/generations/{id}/preview-page |
| v3.8 | 2026-02-11 | **Detection Log API 추가**<br><br>**[1. Detection Log API 신규 (6.5)]**<br>- **GET /api/detection-logs**: 탐지 로그 목록 조회 (DetectionEvent + ActionEvent LEFT JOIN)<br>- **GET /api/detection-logs/{event_id}**: 탐지 로그 단건 조회<br>- **DetectionLogResponse 스키마**: DetectionEventResponse + action(ActionNested) 필드<br>- **ActionNested 스키마**: id, content, user, created_at, updated_at (경량, from_event 미포함)<br>- 읽기 전용 API (CRUD 미제공)<br>- 기존 Detection/Action API 변경 없음<br><br>**[5. MappingCamera/Speaker/Lamp 독립 List API 추가 (7.3.8, 7.4.8, 7.5.7)]**<br>- GET /api/integrations/mapping-cameras: 전체 MappingCamera 조회 (필터: event_mapping_id, camera_id, is_enable)<br>- GET /api/integrations/mapping-speakers: 전체 MappingSpeaker 조회 (필터: event_mapping_id, speaker_id, is_enable)<br>- GET /api/integrations/mapping-lamps: 전체 MappingLamp 조회 (필터: event_mapping_id, lamp_id, is_enable)<br>- 서브시스템 캐시용 독립 읽기 전용 API (기존 계층형 API 유지) |
| v3.7 | 2026-02-09 | **Device Setting PUT API 추가, CameraSetting focus_mode/iris_mode 필드 확장, Enum 2종 추가**<br><br>**[1. Device Setting Enum 추가 (4.9)]**<br>- **EnumFocusMode (2종)**: AUTO, MANUAL<br>- **EnumIrisMode (2종)**: AUTO, MANUAL<br>- **EnumTrackingStatus (3종)**: ACTIVE, LOST, IDLE<br><br>**[2. Camera Settings API 변경 (5.3.7~5.3.9)]**<br>- **5.3.7 GET 응답 변경**: focus_mode, iris_mode 필드 추가<br>- **5.3.8 PATCH 요청/응답 변경**: focus_mode, iris_mode 필드 추가<br>- **5.3.9 PUT /api/devices/cameras/{camera_id}/settings 신규**: 전체 교체 (Upsert)<br>- CameraSetting API에서 pan_tilt_speed, zoom_speed 삭제, tracking(EnumTrackingStatus) 추가<br><br>**[3. Proxy Settings API 변경 (8.8.2~8.8.3)]**<br>- **8.8.2 제목 변경**: "프록시 설정 수정" → "프록시 설정 수정 (부분)"<br>- **8.8.3 PUT /api/servers/{server_id}/proxy-settings 신규**: 전체 교체 (Upsert)<br><br>**[4. 공통 응답 형식 분리 (3.2)]**<br>- 공통 응답 형식 분리 — 단건 응답(ApiSingleResponse)에서 pagination 제거 |
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

**문서 버전**: v6.3.2 (Swagger `6.3.2` 정합; v6.3 후속 2026-08-03 — event_suppression_bulk_delete)
**최종 업데이트**: 2026-07-07
