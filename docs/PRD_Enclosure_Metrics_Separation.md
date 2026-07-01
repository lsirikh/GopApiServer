# PRD: Enclosure Metrics 분리 설계

**문서 버전**: v1.0
**작성일**: 2026-01-15
**상태**: Implemented
**관련 문서**:
- PRD_System_Event.md v1.2 (threshold_config 설계 패턴 참조)
- GOP_Restful_Api_연동설계.md (Section 5.5 Enclosure API)
- GOP_스키마_전체.md

---

## 1. 개요

### 1.1 목적

Enclosure(함체) 테이블에서 **실시간 측정 데이터**(`detail_info`)를 분리하여 별도의 **enclosure_metrics** 테이블로 관리하고, Enclosure 기본 스키마를 **자산 정보 + 설정값** 중심으로 재구성합니다.

### 1.2 배경 및 문제점

현재 Enclosure 테이블 구조에서 `detail_info` JSONB 컬럼에 **실시간 측정 데이터**가 자산 정보와 함께 저장되고 있습니다.

**현재 구조의 문제점**:

| 구분 | 데이터 | 문제점 |
|------|--------|--------|
| **detail_info** | temperature, humidity, current, voltage, vibration, ups_battery_level | 실시간으로 변동하는 측정값이 자산 테이블에 저장됨 |
| **자산 정보** | id, name_device, geolocation, threshold_config | 변경이 드문 설정/자산 정보 |
| **혼재** | 측정값 + 설정값 | 데이터 성격이 다른 항목이 같은 테이블에 혼재 |

**PRD_System_Event.md의 설계 원칙** (Section 2.3~2.4):

> 실시간 리소스 모니터링 데이터는 **별도 테이블 + 전용 API**로 분리하여 관리
> - **임계치 설정** → 주 테이블의 `threshold_config`
> - **실시간 값** → `server_metrics` 별도 테이블
> - **임계치 초과 알림** → `system_events` 이벤트 테이블

이 동일한 패턴을 Enclosure에도 적용해야 합니다.

### 1.3 핵심 설계 원칙

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        데이터 분류 원칙                                      │
├───────────────────┬────────────────────────┬───────────────────────────────┤
│ 분류              │ 저장 위치               │ 예시                           │
├───────────────────┼────────────────────────┼───────────────────────────────┤
│ 자산 정보         │ enclosures 테이블       │ id, name_device, geolocation  │
│ 설정값 (임계치)   │ enclosures.threshold_config │ temp_high, humidity_high │
│ 제어 상태         │ enclosures 테이블       │ heater_enabled, fan_enabled   │
│ 실시간 측정값     │ enclosure_metrics 테이블│ temperature, humidity, voltage│
│ 이벤트/알림       │ events (malfunction 등)  │ 임계치 초과 시 자동 생성       │
└───────────────────┴────────────────────────┴───────────────────────────────┘
```

---

## 2. 현재 vs 변경 후 비교

### 2.1 현재 구조 (Before)

```json
{
  "id": 1,
  "number_device": 101,
  "group_device": 1,
  "name_device": "GOP 3초소 함체",
  "type_device": "IoController",
  "version": "v1.0.0",
  "status": "ACTIVATED",
  "door_status": "CLOSED",
  "detail_info": {
    "temperature": 25.5,       // ❌ 실시간 변동 - DB 컬럼 부적합
    "humidity": 45.0,          // ❌ 실시간 변동
    "current": 2.5,            // ❌ 실시간 변동
    "voltage": 220.0,          // ❌ 실시간 변동
    "vibration": 0.1,          // ❌ 실시간 변동
    "ups_battery_level": 100,  // ❌ 실시간 변동
    "ups_charging": true,      // ❌ 실시간 변동
    "last_updated": "2026-01-08T10:00:00Z"
  },
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
```

### 2.2 변경 후 구조 (After)

#### 2.2.1 Enclosure 기본 스키마 (자산 + 설정)

```json
{
  "id": 1,
  "number_device": 101,
  "group_device": 1,
  "name_device": "GOP 3초소 함체",
  "type_device": "IoController",
  "version": "v1.0.0",
  "status": "ACTIVATED",
  "door_status": "CLOSED",
  "geolocation": {                    // ✅ 위치 정보 (거의 변경 안 됨)
    "location": "GOP 3초소",
    "latitude": 38.1234,
    "longitude": 127.5678,
    "altitude": 150.0
  },
  "threshold_config": {               // ✅ 임계치 설정 (변경 드묾)
    "temp_high": 40.0,
    "temp_low": -10.0,
    "humidity_high": 85.0,
    "humidity_low": 20.0,
    "vibration_threshold": 5.0
  },
  "heater_enabled": false,            // ✅ 제어 상태 (명령에 의해 변경)
  "fan_enabled": false,               // ✅ 제어 상태
  "created_at": "2026-01-08T10:00:00.000000",
  "updated_at": "2026-01-08T10:00:00.000000"
}
```

#### 2.2.2 Enclosure Metrics (별도 테이블)

```json
{
  "id": 12345,
  "enclosure_id": 1,
  "temperature": 25.5,
  "humidity": 45.0,
  "current": 2.5,
  "voltage": 220.0,
  "vibration": 0.1,
  "ups_battery_level": 100,
  "ups_charging": true,
  "door_status": "CLOSED",
  "detail": {
    "internal_temp": 28.0,
    "external_temp": 15.0
  },
  "collected_at": "2026-01-15T10:30:00.000Z",
  "created_at": "2026-01-15T10:30:01.000Z"
}
```

---

## 3. 데이터 모델 설계

### 3.1 enclosure_metrics 테이블

```sql
CREATE TABLE enclosure_metrics (
    id SERIAL PRIMARY KEY,

    -- Enclosure FK (CASCADE DELETE - 함체 삭제 시 메트릭도 삭제)
    enclosure_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,

    -- Environment Metrics
    temperature DECIMAL(5,2),         -- 온도 (°C)
    humidity DECIMAL(5,2),            -- 습도 (%)
    current DECIMAL(8,3),             -- 전류 (A)
    voltage DECIMAL(8,2),             -- 전압 (V)
    vibration DECIMAL(6,3),           -- 진동 (G)

    -- UPS Metrics
    ups_battery_level INTEGER,        -- UPS 배터리 잔량 (%)
    ups_charging BOOLEAN,             -- UPS 충전 중 여부

    -- Physical Status Snapshot
    door_status VARCHAR(20),          -- 수집 시점의 도어 상태

    -- Additional Metrics (Optional)
    detail JSONB,                     -- 추가 메트릭 (확장용)

    -- Timestamps
    collected_at TIMESTAMP WITH TIME ZONE NOT NULL,     -- 측정 시각
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_enclosure_metrics_enclosure_id ON enclosure_metrics(enclosure_id);
CREATE INDEX idx_enclosure_metrics_collected_at ON enclosure_metrics(collected_at DESC);
CREATE INDEX idx_enclosure_metrics_enc_collected ON enclosure_metrics(enclosure_id, collected_at DESC);
```

### 3.2 threshold_config JSONB 구조

```json
{
  "temperature": {
    "high": 40.0,              // 고온 경고 임계치 (°C)
    "low": -10.0,              // 저온 경고 임계치 (°C)
    "critical_high": 50.0,     // 고온 심각 임계치 (°C)
    "critical_low": -20.0      // 저온 심각 임계치 (°C)
  },
  "humidity": {
    "high": 85.0,              // 고습 경고 임계치 (%)
    "low": 20.0,               // 저습 경고 임계치 (%)
    "critical_high": 95.0,     // 고습 심각 임계치 (%)
    "critical_low": 10.0       // 저습 심각 임계치 (%)
  },
  "vibration": {
    "warning": 3.0,            // 진동 경고 임계치 (G)
    "critical": 5.0            // 진동 심각 임계치 (G)
  },
  "voltage": {
    "high": 240.0,             // 고전압 경고 (V)
    "low": 200.0               // 저전압 경고 (V)
  },
  "ups_battery": {
    "low": 20,                 // 배터리 부족 경고 (%)
    "critical": 10             // 배터리 위험 (%)
  }
}
```

### 3.3 필드 정의

#### enclosure_metrics 테이블

| 필드명 | 타입 | NULL | 설명 |
|--------|------|------|------|
| id | SERIAL | NO | PK |
| enclosure_id | INTEGER | NO | FK → devices.id (CASCADE) |
| temperature | DECIMAL(5,2) | YES | 온도 (°C) |
| humidity | DECIMAL(5,2) | YES | 습도 (%) |
| current | DECIMAL(8,3) | YES | 전류 (A) |
| voltage | DECIMAL(8,2) | YES | 전압 (V) |
| vibration | DECIMAL(6,3) | YES | 진동 (G) |
| ups_battery_level | INTEGER | YES | UPS 배터리 잔량 (%) |
| ups_charging | BOOLEAN | YES | UPS 충전 상태 |
| door_status | VARCHAR(20) | YES | 수집 시점 도어 상태 |
| detail | JSONB | YES | 추가 메트릭 |
| collected_at | TIMESTAMP | NO | 측정 시각 |
| created_at | TIMESTAMP | NO | 레코드 생성 시각 |

---

## 4. API 설계

### 4.1 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/devices/enclosures/{id}/metrics` | 메트릭 전송 (IoT → Server) |
| GET | `/api/devices/enclosures/{id}/metrics` | 메트릭 조회 (최근 N개) |
| GET | `/api/devices/enclosures/{id}/metrics/latest` | 최신 메트릭 1건 조회 |
| GET | `/api/enclosure-metrics` | 전체 메트릭 조회 (필터링) |
| DELETE | `/api/devices/enclosures/{id}/metrics` | 오래된 메트릭 삭제 |

### 4.2 POST /api/devices/enclosures/{id}/metrics

**Request Body** (IoT 장비가 주기적으로 전송):

```json
{
  "temperature": 25.5,
  "humidity": 45.0,
  "current": 2.5,
  "voltage": 220.0,
  "vibration": 0.1,
  "ups_battery_level": 100,
  "ups_charging": true,
  "door_status": "CLOSED",
  "detail": {
    "internal_temp": 28.0,
    "external_temp": 15.0
  },
  "collected_at": "2026-01-15T10:30:00Z"
}
```

**Response (201 Created)**:

```json
{
  "success": true,
  "message": "Enclosure metrics recorded successfully",
  "data": {
    "id": 12345,
    "enclosure_id": 1,
    "temperature": 25.5,
    "humidity": 45.0,
    "current": 2.5,
    "voltage": 220.0,
    "vibration": 0.1,
    "ups_battery_level": 100,
    "ups_charging": true,
    "door_status": "CLOSED",
    "collected_at": "2026-01-15T10:30:00.000Z",
    "created_at": "2026-01-15T10:30:01.000Z",
    "threshold_exceeded": []
  },
  "meta": {
    "timestamp": "2026-01-15T10:30:01.000Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

**임계치 초과 시 Response**:

```json
{
  "success": true,
  "message": "Enclosure metrics recorded with threshold alerts",
  "data": {
    "id": 12346,
    "enclosure_id": 1,
    "temperature": 45.5,
    "humidity": 90.0,
    "current": 2.5,
    "voltage": 220.0,
    "vibration": 6.5,
    "ups_battery_level": 15,
    "ups_charging": false,
    "door_status": "CLOSED",
    "collected_at": "2026-01-15T10:31:00.000Z",
    "created_at": "2026-01-15T10:31:01.000Z",
    "threshold_exceeded": [
      { "metric": "temperature", "level": "warning", "value": 45.5, "threshold": 40.0 },
      { "metric": "humidity", "level": "warning", "value": 90.0, "threshold": 85.0 },
      { "metric": "vibration", "level": "critical", "value": 6.5, "threshold": 5.0 },
      { "metric": "ups_battery", "level": "warning", "value": 15, "threshold": 20 }
    ]
  },
  "meta": {
    "timestamp": "2026-01-15T10:31:01.000Z",
    "request_id": "550e8401-e29b-41d4-a716-446655440000"
  }
}
```

### 4.3 GET /api/devices/enclosures/{id}/metrics

**Query Parameters**:

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| limit | integer | N | 조회 개수 (기본값: 100, 최대: 1000) |
| start_time | string | N | 시작 시간 (ISO 8601) |
| end_time | string | N | 종료 시간 (ISO 8601) |

**Response (200 OK)**:

```json
{
  "success": true,
  "message": "Enclosure metrics retrieved successfully",
  "data": [
    {
      "id": 12345,
      "enclosure_id": 1,
      "temperature": 25.5,
      "humidity": 45.0,
      "current": 2.5,
      "voltage": 220.0,
      "vibration": 0.1,
      "ups_battery_level": 100,
      "ups_charging": true,
      "door_status": "CLOSED",
      "collected_at": "2026-01-15T10:30:00.000Z"
    }
  ],
  "pagination": {
    "limit": 100,
    "total": 1440
  }
}
```

### 4.4 GET /api/devices/enclosures/{id}/metrics/latest

**Response (200 OK)**:

```json
{
  "success": true,
  "message": "Latest enclosure metrics retrieved successfully",
  "data": {
    "id": 12345,
    "enclosure_id": 1,
    "temperature": 25.5,
    "humidity": 45.0,
    "current": 2.5,
    "voltage": 220.0,
    "vibration": 0.1,
    "ups_battery_level": 100,
    "ups_charging": true,
    "door_status": "CLOSED",
    "detail": {
      "internal_temp": 28.0,
      "external_temp": 15.0
    },
    "collected_at": "2026-01-15T10:30:00.000Z",
    "created_at": "2026-01-15T10:30:01.000Z"
  }
}
```

---

## 5. 데이터 흐름

```
┌──────────────────┐     POST /api/devices/enclosures/{id}/metrics    ┌─────────────────┐
│   함체 IoT 장비   │ ──────────────────────────────────────────────►  │   GOP Server    │
│  (측정값 수집)    │         (주기: 1분 또는 설정값)                     │   (API Server)  │
└──────────────────┘                                                  └────────┬────────┘
                                                                               │
                                                                               ▼
                                                      ┌──────────────────────────────────────┐
                                                      │            처리 로직                  │
                                                      │  1. enclosure_metrics 테이블 저장      │
                                                      │  2. threshold_config 비교              │
                                                      │  3. 초과 시 malfunction event 생성     │
                                                      │  4. heater/fan 자동 제어 (Optional)    │
                                                      └──────────────────────────────────────┘
                                                                               │
                                ┌───────────────────┬──────────────────────────┘
                                ▼                   ▼
                    ┌─────────────────────┐  ┌─────────────────────────┐
                    │ enclosure_metrics   │  │ malfunctions (events)   │
                    │   (이력 저장)        │  │ (알림/이벤트)            │
                    └─────────────────────┘  └─────────────────────────┘
```

---

## 6. heater_enabled / fan_enabled 분리 이유

### 6.1 데이터 성격 분류

| 필드 | 데이터 성격 | 변경 트리거 | 저장 위치 |
|------|------------|------------|----------|
| `temperature` | **측정값** (Measurement) | 센서가 주기적으로 읽음 | enclosure_metrics |
| `humidity` | **측정값** (Measurement) | 센서가 주기적으로 읽음 | enclosure_metrics |
| `heater_enabled` | **제어 상태** (Control State) | 관리자/시스템 명령 | enclosures |
| `fan_enabled` | **제어 상태** (Control State) | 관리자/시스템 명령 | enclosures |
| `threshold_config` | **설정값** (Configuration) | 관리자 설정 | enclosures |

### 6.2 상세 설명

**측정값 (Measurement)**:
- 센서가 **자동으로** 읽어들이는 값
- **주기적으로** 변동 (1분마다 등)
- **이력 보관**이 필요 (트렌드 분석, 장애 추적)
- 예: temperature, humidity, voltage, vibration

**제어 상태 (Control State)**:
- 관리자 또는 시스템이 **명시적으로 명령**한 결과
- **명령 기반**으로 변경 (측정 기반 아님)
- **현재 상태**만 중요 (이력은 별도 로그로 관리)
- 예: heater_enabled, fan_enabled

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       제어 상태 vs 측정값                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  [관리자] ──► "히터 켜" ──► heater_enabled = true  (제어 명령)            │
│                                                                         │
│  [센서]   ──► 온도 읽기 ──► temperature = 25.5°C  (측정값)               │
│                                                                         │
│  ※ 히터가 켜졌다고 온도가 바로 변하지 않음                                │
│  ※ heater_enabled는 "설정된 상태"                                        │
│  ※ temperature는 "측정된 현재값"                                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.3 왜 Enclosures 테이블에 남아있는가?

`heater_enabled`와 `fan_enabled`는 다음 이유로 Enclosures 테이블에 유지:

1. **현재 설정 상태**: "지금 히터가 켜져 있는가?"를 빠르게 확인
2. **명령 기반 변경**: 측정값처럼 주기적으로 변하지 않음
3. **장비 제어 API와 연동**: `PATCH /api/devices/enclosures/{id}` 로 제어
4. **이력 불필요**: 제어 이력은 Action Event 또는 별도 로그로 관리

```python
# 제어 명령 예시
PATCH /api/devices/enclosures/1
{
  "heater_enabled": true,    # 관리자가 히터를 켬
  "fan_enabled": false       # 팬은 끔
}
```

---

## 7. Migration 계획

### 7.1 Phase 1: 테이블 생성

```sql
-- 1. enclosure_metrics 테이블 생성
CREATE TABLE enclosure_metrics (
    id SERIAL PRIMARY KEY,
    enclosure_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    temperature DECIMAL(5,2),
    humidity DECIMAL(5,2),
    current DECIMAL(8,3),
    voltage DECIMAL(8,2),
    vibration DECIMAL(6,3),
    ups_battery_level INTEGER,
    ups_charging BOOLEAN,
    door_status VARCHAR(20),
    detail JSONB,
    collected_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2. 인덱스 생성
CREATE INDEX idx_enclosure_metrics_enclosure_id ON enclosure_metrics(enclosure_id);
CREATE INDEX idx_enclosure_metrics_collected_at ON enclosure_metrics(collected_at DESC);
CREATE INDEX idx_enclosure_metrics_enc_collected ON enclosure_metrics(enclosure_id, collected_at DESC);
```

### 7.2 Phase 2: detail_info 컬럼 처리

**Option A**: 컬럼 삭제 (권장)
```sql
ALTER TABLE enclosures DROP COLUMN IF EXISTS detail_info;
```

**Option B**: 컬럼 유지 (Deprecated 표시)
```sql
COMMENT ON COLUMN enclosures.detail_info IS 'DEPRECATED: Use enclosure_metrics table instead';
```

### 7.3 Phase 3: API 구현

| 순서 | 작업 | 파일 |
|------|------|------|
| 1 | EnclosureMetric 모델 생성 | app/models/device.py |
| 2 | EnclosureMetric 스키마 생성 | app/schemas/device.py |
| 3 | enclosure_metrics 라우터 생성 | app/routers/enclosure_metrics.py |
| 4 | 기존 Enclosure 스키마에서 detail_info 제거 | app/schemas/device.py |
| 5 | 문서 업데이트 | GOP_Restful_Api_연동설계.md |

---

## 8. 데이터 보존 정책

| 데이터 유형 | 보존 기간 | 정리 방법 |
|------------|----------|----------|
| Raw Metrics (1분 간격) | 7일 | 자동 삭제 또는 집계 후 삭제 |
| Hourly Aggregated | 30일 | 자동 삭제 |
| Daily Aggregated | 1년 | 아카이브 |
| Malfunction Events | 영구 | 수동 삭제 |

---

## 9. 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| v1.0 | 2026-01-15 | 초안 작성 |

---

## 10. 참조 문서

- [PRD_System_Event.md](./PRD_System_Event.md) - Server Metrics 분리 패턴 참조
- [GOP_스키마_전체.md](./GOP_스키마_전체.md) - 전체 데이터베이스 스키마
- [GOP_Restful_Api_연동설계.md](../GOP_Restful_Api_연동설계.md) - RESTful API 설계서

---

**문서 끝**
