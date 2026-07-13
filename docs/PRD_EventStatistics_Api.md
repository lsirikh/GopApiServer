# PRD: Event Statistics API (이벤트 통계 API)

- **Version**: 2.1
- **Date**: 2026-03-03
- **Status**: Draft
- **Target**: API 서버 (Python FastAPI)
- **Language/Framework**: Python / FastAPI / SQLAlchemy / SQLite (Production: PostgreSQL 호환)

---

## 1. Background (배경)

### 현재 상황
현재 클라이언트의 이벤트 대시보드는 3가지 차트를 렌더링하기 위해 **모든 이벤트 데이터를 전량 다운로드**합니다:

```
클라이언트 → GET /api/events/detections?page=1&limit=100 (반복)
           → GET /api/events/malfunctions?page=1&limit=100 (반복)
           → GET /api/events/connections?page=1&limit=100 (반복)
           → GET /api/events/actions?page=1&limit=100 (반복)
```

- **4종류 x 수천 건** = 수만 건의 전체 이벤트 데이터 전송
- 각 이벤트에 Device(중첩 객체), Detail, FromEvent 등 불필요한 속성 포함
- 실제 차트에서 사용하는 정보: **DateTime + 이벤트 타입 + 탐지 소스(센서/카메라) + 제어기 ID** 만 필요

### 차트별 필요 데이터 분석

| 차트 | 현재 데이터 소비 | 실제 필요한 메타데이터 |
|------|----------------|---------------------|
| **라인 차트** (시간대별 추이) | 전체 이벤트 → DateTime으로 시간 단위 GroupBy → Count | `{ time_bucket, sensor_detection, camera_detection, malfunction, connection, action }` |
| **막대 그래프** (제어기별 건수) | 전체 이벤트 → Device.Controller 매핑 → Controller별 Count | `{ controller_id, sensor_detection, malfunction, connection }` + 카메라별 별도 집계 |
| **원형 그래프** (이벤트 비율) | 전체 이벤트 → 타입별 Count → Sum | `{ sensor_detection, camera_detection, malfunction, connection, action }` |
| **요약 카드** (탭별 KPI) | 전체 이벤트 → 건수 + 일평균 + 장비수 | `{ total, daily_average, active_device_count }` per category |

### 탐지 이벤트의 소스 구분

탐지 이벤트(DetectionEvent)는 **두 가지 출처**에서 발생합니다:

| 구분 | 센서 탐지 | 카메라 탐지 (AI) |
|------|----------|----------------|
| **category_device** | `sensor` | `camera` |
| **type_device** | Multi, Fence, PIR, Underground, Contact 등 | **IpCamera** |
| **result (EnumDetectionType)** | PIR_SENSOR, THERMAL_SENSOR, VIBRATION_SENSOR, CABLE_CUTTING, CONTACT_SENSOR, DISTANCE_SENSOR | **AI_DETECT** |
| **controller_id** | 있음 (Sensor → Controller FK) | **없음** — Camera는 독립 장비 |
| **제어기별 집계** | Sensor.controller_id로 그룹 가능 | controller_id가 없으므로 **카메라별 별도 집계** 필요 |

### 동기
- 수천 건 이벤트를 전량 전송하면 **네트워크 대역폭 낭비** + **클라이언트 메모리 부하** + **로딩 시간 수십 초**
- 서버에서 SQL 집계 후 결과만 전송하면 응답 크기가 **수십 KB 이하**로 감소

---

## 2. Goals (목표)

### 핵심 목표
- [ ] 서버에서 이벤트 통계를 SQL로 집계하여 경량 응답 제공
- [ ] 탐지 이벤트를 센서/카메라로 분리하여 집계
- [ ] 3가지 차트 유형에 맞는 전용 API 엔드포인트 설계
- [ ] 클라이언트가 전체 이벤트 데이터 없이도 차트 렌더링 가능

### 비목표 (Out of Scope)
- 클라이언트 코드 변경 (별도 PRD로 진행)
- Report API와의 통합 (향후)
- 실시간 차트 업데이트 (WebSocket/NATS)

---

## 3. 프로젝트 구조 참조

### 3.1 DB 테이블 (Joined Table Inheritance)

```
events (Base)
├── id (PK, AUTOINCREMENT)
├── category_event (ENUM: detection/malfunction/connection)  -- Polymorphic Discriminator
├── type_event (STRING: Intrusion/Fault/Connection)
├── device_id (FK → devices.id, SET NULL)
├── created_at (DATETIME, INDEX)
└── updated_at (DATETIME)

detection_events (inherits events)
├── id (FK → events.id, CASCADE)
├── action_reported (STRING: True/False)
├── result (ENUM: PIR_SENSOR, THERMAL_SENSOR, AI_DETECT, ...)
└── detail (JSON)

malfunction_events (inherits events)
├── id (FK → events.id, CASCADE)
├── action_reported (STRING: True/False)
├── reason (ENUM: FAULT_CONTROLLER, FAULT_FENCE, ...)
└── detail (JSON)

connection_events (inherits events)
└── id (FK → events.id, CASCADE)

action_events (독립 테이블 — Event 상속 아님)
├── id (PK, AUTOINCREMENT)
├── from_event_id (FK → events.id, SET NULL)
├── type_event (STRING: Action)
├── content (STRING)
├── user (STRING)
├── created_at (DATETIME, INDEX)
└── updated_at (DATETIME)
```

### 3.2 Device 테이블 (Joined Table Inheritance)

```
devices (Base)
├── id (PK)
├── category_device (ENUM: controller/sensor/camera/speaker/enclosure/lamp)
├── type_device (ENUM: IpCamera, Multi, Fence, PIR, IoController, ...)
├── number_device (INT)
├── name_device (STRING)
└── ...

sensors (inherits devices)
├── id (FK → devices.id)
└── controller_id (FK → controllers.id)  ← 제어기 종속

cameras (inherits devices)
├── id (FK → devices.id)
└── (controller_id 없음)  ← 독립 장비

controllers (inherits devices)
├── id (FK → devices.id)
└── ip_address, ip_port, ...
```

### 3.3 센서/카메라 판별 기준

```python
# 방법 1: category_device 기반 (권장 — 명확하고 확장 안전)
Sensor:  Device.category_device == 'sensor'   → sensor_detection
Camera:  Device.category_device == 'camera'   → camera_detection

# 방법 2: result (EnumDetectionType) 기반 (보조)
DetectionEvent.result == 'AI_DETECT' → camera_detection
DetectionEvent.result != 'AI_DETECT' → sensor_detection
```

> **권장**: `category_device` 기반. device JOIN이 필요하지만, 향후 카메라 탐지 유형이 AI_DETECT 외에 추가되어도 안전합니다.

---

## 4. API 설계

### 4.1 Event Trend (라인 차트 — 시간대별 건수)

```
GET /api/events/statistics/trend
```

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 | 기본값 |
|---------|------|------|------|-------|
| start_date | datetime | YES | 조회 시작 시간 (ISO 8601) | - |
| end_date | datetime | YES | 조회 종료 시간 (ISO 8601) | - |
| interval | string | NO | 집계 단위: `hour`, `day` | `hour` |

**Response** (200 OK):
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
  },
  "meta": { "timestamp": "..." }
}
```

**응답 래퍼**: `ApiSingleResponse[EventTrendResponse]` — 집계 결과는 단건 응답 (pagination 불필요)

**SQLAlchemy 구현 방향**:
```python
# SQLite 호환: strftime('%Y-%m-%d %H', created_at) 으로 시간 단위 그룹핑
# hour: strftime('%Y-%m-%d %H', events.created_at)
# day:  strftime('%Y-%m-%d', events.created_at)

from sqlalchemy import func, case, literal

# Detection: device JOIN으로 sensor/camera 분류
sensor_case = case(
    (Device.category_device == 'camera', 'camera_detection'),
    else_='sensor_detection'
)

# Malfunction, Connection: events 테이블에서 category_event로 분류
# Action: action_events 별도 테이블에서 조회
```

---

### 4.2 Event Summary by Device (막대 그래프 — 제어기별 + 카메라별 건수)

```
GET /api/events/statistics/by-device
```

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 | 기본값 |
|---------|------|------|------|-------|
| start_date | datetime | YES | 조회 시작 시간 (ISO 8601) | - |
| end_date | datetime | YES | 조회 종료 시간 (ISO 8601) | - |

**Response** (200 OK):
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
        "connection": 3
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
  },
  "meta": { "timestamp": "..." }
}
```

**응답 래퍼**: `ApiSingleResponse[EventByDeviceResponse]`

**설계 포인트**:
- `controllers[]`: Sensor.controller_id 기준으로 제어기별 센서 이벤트 집계 (sensor_detection, malfunction, connection)
- `cameras[]`: Camera 기준으로 카메라별 AI 탐지 건수 집계 (camera_detection)
- ActionEvent는 device_id가 없으므로 by-device에서 **제외** (from_event_id 역참조는 성능 비용 대비 가치 없음)
- 카메라는 controller_id가 없으므로 별도 배열로 분리

**SQLAlchemy 구현 방향**:
```python
# Part 1: 제어기별 센서 이벤트 집계
# DetectionEvent + MalfunctionEvent + ConnectionEvent
# → JOIN Device → 조건: Device.category_device == 'sensor'
# → Sensor.controller_id로 GROUP BY
# → LEFT JOIN Controller (name, number)

# Part 2: 카메라별 AI 탐지 집계
# DetectionEvent → JOIN Device → 조건: Device.category_device == 'camera'
# → GROUP BY Device.id
```

---

### 4.3 Event Summary by Type (원형 그래프 + 요약 카드)

```
GET /api/events/statistics/summary
```

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 | 기본값 |
|---------|------|------|------|-------|
| start_date | datetime | YES | 조회 시작 시간 (ISO 8601) | - |
| end_date | datetime | YES | 조회 종료 시간 (ISO 8601) | - |

**Response** (200 OK):
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
  },
  "meta": { "timestamp": "..." }
}
```

**v2.1 추가 필드 설명**:

| 필드 | 설명 | 클라이언트 용도 |
|------|------|---------------|
| `days_in_range` | 조회 기간 일수 (end - start). 최소 1 | 일평균 계산 기반값 |
| `daily_averages.*` | 각 이벤트 타입의 일평균 (count / days_in_range, 소수점 1자리) | 카메라 탭 "일평균 42건" 카드 |
| `active_devices.sensors` | 조회 기간 중 이벤트가 발생한 센서 수 (DISTINCT device_id) | 센서 탭 요약 카드 |
| `active_devices.cameras` | 조회 기간 중 이벤트가 발생한 카메라 수 (DISTINCT device_id) | 카메라 탭 "카메라수 15대" 카드 |
| `active_devices.controllers` | 조회 기간 중 이벤트가 발생한 제어기 수 (DISTINCT controller_id) | 전체 대시보드 요약 |

> **카메라 이벤트 탭 매핑 예시**:
> ```
> ┌──────────┐  ┌──────────┐  ┌──────────┐
> │ 총 건수   │  │ 일평균    │  │ 카메라수  │
> │  30건    │  │  4.3건   │  │  15대    │
> └──────────┘  └──────────┘  └──────────┘
>   data.          data.daily_     data.active_
>   camera_        averages.       devices.
>   detection      camera_         cameras
>                  detection
> ```

**응답 래퍼**: `ApiSingleResponse[EventSummaryResponse]`

**SQLAlchemy 구현 방향**:
```python
# 5개의 개별 COUNT 쿼리 (서브쿼리보다 명확하고 SQLite 호환)
sensor_count = db.query(func.count(DetectionEvent.id)).join(
    Device, Event.device_id == Device.id
).filter(
    Device.category_device == 'sensor',
    Event.created_at.between(start_date, end_date)
).scalar()

camera_count = db.query(func.count(DetectionEvent.id)).join(
    Device, Event.device_id == Device.id
).filter(
    Device.category_device == 'camera',
    Event.created_at.between(start_date, end_date)
).scalar()

# ... malfunction, connection, action 동일 패턴

# 파생 메트릭 계산
days = max((end_date - start_date).days, 1)  # 최소 1일

daily_averages = {
    "sensor_detection": round(sensor_count / days, 1),
    "camera_detection": round(camera_count / days, 1),
    # ...
}

# active_devices: DISTINCT device_id COUNT
active_cameras = db.query(func.count(func.distinct(Event.device_id))).join(
    Device, Event.device_id == Device.id
).filter(
    Device.category_device == 'camera',
    Event.category_event == 'detection',
    Event.created_at.between(start_date, end_date)
).scalar()
```

---

### 4.4 Event Dashboard (통합 — 단일 호출)

```
GET /api/events/statistics/dashboard
```

**Query Parameters**:
| 파라미터 | 타입 | 필수 | 설명 | 기본값 |
|---------|------|------|------|-------|
| start_date | datetime | YES | 조회 시작 시간 (ISO 8601) | - |
| end_date | datetime | YES | 조회 종료 시간 (ISO 8601) | - |
| interval | string | NO | 추이 집계 단위 | `hour` |

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Event dashboard statistics retrieved",
  "data": {
    "summary": { "total": 275, "days_in_range": 7, "sensor_detection": 150, "camera_detection": 30, "malfunction": 45, "connection": 30, "action": 20, "daily_averages": { "sensor_detection": 21.4, "camera_detection": 4.3, "..." : "..." }, "active_devices": { "sensors": 25, "cameras": 15, "controllers": 5 } },
    "trend": { "interval": "hour", "series": [ { "time_bucket": "2025-01-15 00", "sensor_detection": 3, "camera_detection": 1, "malfunction": 30, "connection": 0, "action": 2 } ] },
    "by_device": { "controllers": [...], "cameras": [...] }
  },
  "meta": { "timestamp": "..." }
}
```

**응답 래퍼**: `ApiSingleResponse[EventDashboardResponse]`

> 단일 HTTP 호출로 3개 차트 데이터를 모두 가져올 수 있어 네트워크 라운드트립 최소화.

---

## 5. Pydantic 스키마

```python
# app/schemas/event_statistics.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


# ===== Trend (라인 차트) =====

class EventTrendItem(BaseModel):
    time_bucket: str = Field(..., description="집계 시간 구간 (예: '2025-01-15 10')")
    sensor_detection: int = Field(0, description="센서 탐지 건수")
    camera_detection: int = Field(0, description="카메라(AI) 탐지 건수")
    malfunction: int = Field(0, description="장애 이벤트 건수")
    connection: int = Field(0, description="연결 이벤트 건수")
    action: int = Field(0, description="조치 이벤트 건수")


class EventTrendResponse(BaseModel):
    interval: str = Field(..., description="집계 단위: hour/day")
    start_date: datetime
    end_date: datetime
    series: list[EventTrendItem] = Field(default_factory=list)


# ===== By Device (막대 그래프) =====

class ControllerStats(BaseModel):
    controller_id: int
    controller_name: Optional[str] = None
    controller_number: int
    sensor_detection: int = 0
    malfunction: int = 0
    connection: int = 0


class CameraStats(BaseModel):
    camera_id: int
    camera_name: Optional[str] = None
    camera_number: int
    camera_detection: int = 0


class EventByDeviceResponse(BaseModel):
    start_date: datetime
    end_date: datetime
    controllers: list[ControllerStats] = Field(default_factory=list)
    cameras: list[CameraStats] = Field(default_factory=list)


# ===== Summary (원형 그래프 + 요약 카드) =====

class DailyAverages(BaseModel):
    """일평균 건수 (count / days_in_range, 소수점 1자리)"""
    sensor_detection: float = 0.0
    camera_detection: float = 0.0
    malfunction: float = 0.0
    connection: float = 0.0
    action: float = 0.0


class ActiveDevices(BaseModel):
    """조회 기간 중 이벤트가 발생한 장비 수 (DISTINCT device_id)"""
    sensors: int = 0
    cameras: int = 0
    controllers: int = 0


class EventSummaryResponse(BaseModel):
    start_date: datetime
    end_date: datetime
    days_in_range: int = Field(1, description="조회 기간 일수 (최소 1)")
    total: int = 0
    sensor_detection: int = 0
    camera_detection: int = 0
    malfunction: int = 0
    connection: int = 0
    action: int = 0
    daily_averages: DailyAverages = Field(default_factory=DailyAverages)
    active_devices: ActiveDevices = Field(default_factory=ActiveDevices)


# ===== Dashboard (통합) =====

class EventDashboardResponse(BaseModel):
    summary: EventSummaryResponse
    trend: EventTrendResponse
    by_device: EventByDeviceResponse
```

---

## 6. Breaking Changes

없음. 기존 API 변경 없이 새 엔드포인트만 추가.

---

## 7. 파일 구조

| File | Action | 설명 |
|------|--------|------|
| `app/schemas/event_statistics.py` | **신규** | Pydantic 스키마 (5절 내용) |
| `app/routers/event_statistics.py` | **신규** | 라우터 (4개 엔드포인트) |
| `app/main.py` | **수정** | 라우터 등록 + tags_metadata 추가 |
| `tests/test_event_statistics.py` | **신규** | TDD 테스트 |

---

## 8. TDD Phases

### Phase 1: Schema

- [ ] 1.1 TEST: EventTrendItem 직렬화 확인
- [ ] 1.2 IMPL: `app/schemas/event_statistics.py` 생성
- [ ] 1.3 VERIFY: 전체 테스트 통과

### Phase 2: Summary API — 기본 건수 (원형 그래프)

- [ ] 2.1 TEST: `GET /api/events/statistics/summary` → 이벤트 없으면 전부 0
- [ ] 2.2 IMPL: `app/routers/event_statistics.py` 생성, `app/main.py` 등록
- [ ] 2.3 TEST: sensor + camera detection 분리 집계 확인
- [ ] 2.4 IMPL: Device JOIN + category_device 분류 로직
- [ ] 2.5 TEST: malfunction, connection, action 각각 카운트 확인
- [ ] 2.6 IMPL: 확인 (2.4 구현으로 통과 예상)
- [ ] 2.7 TEST: total = sensor + camera + malfunction + connection + action
- [ ] 2.8 VERIFY: 전체 테스트 통과

### Phase 2B: Summary API — 파생 메트릭 (요약 카드)

- [ ] 2B.1 TEST: days_in_range = (end_date - start_date).days, 최소 1
- [ ] 2B.2 TEST: daily_averages = 각 건수 / days_in_range (소수점 1자리)
- [ ] 2B.3 IMPL: days_in_range 계산 + daily_averages 계산
- [ ] 2B.4 TEST: active_devices.cameras = 기간 내 이벤트 발생 카메라 DISTINCT 수
- [ ] 2B.5 TEST: active_devices.sensors = 기간 내 이벤트 발생 센서 DISTINCT 수
- [ ] 2B.6 TEST: active_devices.controllers = 기간 내 이벤트 발생 제어기 DISTINCT 수
- [ ] 2B.7 IMPL: DISTINCT device_id / controller_id COUNT 쿼리
- [ ] 2B.8 VERIFY: 전체 테스트 통과

### Phase 3: Trend API (라인 차트)

- [ ] 3.1 TEST: `GET /api/events/statistics/trend` → 이벤트 없으면 빈 series
- [ ] 3.2 IMPL: strftime 기반 시간 그룹핑
- [ ] 3.3 TEST: hour 단위 그룹핑 → time_bucket 형식 "YYYY-MM-DD HH" 확인
- [ ] 3.4 TEST: day 단위 그룹핑 → time_bucket 형식 "YYYY-MM-DD" 확인
- [ ] 3.5 TEST: 센서/카메라 분리 집계가 trend에도 반영
- [ ] 3.6 VERIFY: 전체 테스트 통과

### Phase 4: By-Device API (막대 그래프)

- [ ] 4.1 TEST: `GET /api/events/statistics/by-device` → 이벤트 없으면 빈 배열
- [ ] 4.2 IMPL: 제어기별 + 카메라별 분리 집계
- [ ] 4.3 TEST: 제어기 1개 + 센서 이벤트 → controllers에 집계
- [ ] 4.4 TEST: 카메라 이벤트 → cameras에 집계
- [ ] 4.5 TEST: 제어기별 malfunction, connection 포함 확인
- [ ] 4.6 VERIFY: 전체 테스트 통과

### Phase 5: Dashboard API (통합)

- [ ] 5.1 TEST: `GET /api/events/statistics/dashboard` → summary + trend + by_device 모두 포함
- [ ] 5.2 IMPL: 기존 3개 API 로직 조합
- [ ] 5.3 VERIFY: 전체 테스트 통과

### Phase 6: 엣지 케이스

- [ ] 6.1 TEST: device_id가 NULL인 이벤트 → 집계에서 제외 (에러 없음)
- [ ] 6.2 TEST: start_date > end_date → 빈 결과 (에러 아님)
- [ ] 6.3 VERIFY: 전체 테스트 통과

### Phase 7: 전체 검증

- [ ] 7.1 VERIFY: 전체 테스트 수트 통과
- [ ] 7.2 VERIFY: 기존 테스트 깨지지 않음

---

## 9. 성능 비교

| 지표 | 현재 (전량 다운로드) | 개선 후 (통계 API) | 개선율 |
|------|-------------------|-------------------|-------|
| API 호출 수 | 4종 x N페이지 = 수십 호출 | 1~3 호출 | 90% 감소 |
| 전송 데이터 | 수천 건 x 풀 JSON ≈ 수 MB | 집계 결과 ≈ 5~30 KB | 99% 감소 |
| 서버 처리 | ORM 객체 직렬화 수천 건 | SQL GROUP BY 1회 | 95% 감소 |
| 예상 응답 시간 | 10~30초 (수천 건 페이지네이션) | <200ms | 99% 감소 |
