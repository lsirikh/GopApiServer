# PRD: System Event API

**문서 버전**: v1.3
**작성일**: 2026-01-20
**작성자**: AI Assistant
**상태**: Draft
**변경사항**: EnumSystemEventType 17종 → 15종 동기화 (PRD_SystemEvent_Sync.md v1.2 반영)

---

## 1. 개요

### 1.1 목적

GOP 시스템을 구성하는 서버들의 상태 변화, 리소스 현황, 시스템 알림 등을 로깅하고 관리하기 위한 **System Event API**를 설계합니다.

### 1.2 배경

현재 GOP 시스템에는 다음과 같은 Event 유형이 존재합니다:
- **Detection Event**: 센서 침입 탐지 이벤트
- **Malfunction Event**: 장비 오동작 이벤트
- **Connection Event**: 장비 연결 상태 이벤트
- **Action Event**: 조치 이벤트

이들은 모두 **Device(장비)** 기반의 이벤트로, `events` 테이블을 상속하는 구조입니다.

그러나 **Server(서버)** 레벨의 이벤트 (서버 상태 변화, 리소스 임계치 초과, 시스템 경고 등)를 기록하는 메커니즘이 없습니다. System Event는 Device Event와 독립적인 별도 스키마로 설계하여, 서버 모니터링 및 시스템 운영에 필요한 로그를 저장합니다.

### 1.3 핵심 원칙

1. **독립 스키마**: 기존 `events` 테이블과 무관한 독립적인 테이블 구조
2. **Server FK 참조**: `servers.id`를 FK로 참조하여 서버별 이벤트 추적
3. **확장 가능성**: 다양한 시스템 이벤트 유형을 수용할 수 있는 유연한 구조
4. **경량 설계**: 로깅 목적에 맞는 최소한의 필수 필드

---

## 2. 요구사항

### 2.1 기능 요구사항

| ID | 요구사항 | 우선순위 |
|----|----------|----------|
| FR-001 | Server FK를 통해 특정 서버의 이벤트를 기록할 수 있어야 함 | HIGH |
| FR-002 | 이벤트 유형(type)을 분류할 수 있어야 함 | HIGH |
| FR-003 | 이벤트 심각도(severity)를 구분할 수 있어야 함 | HIGH |
| FR-004 | 상세 정보를 JSONB로 유연하게 저장할 수 있어야 함 | MEDIUM |
| FR-005 | 시간대별, 서버별, 유형별 필터링 조회가 가능해야 함 | HIGH |
| FR-006 | 페이지네이션을 지원해야 함 | HIGH |
| FR-007 | Server 삭제 시 관련 System Event는 유지 (SET NULL) | MEDIUM |

### 2.2 비기능 요구사항

| ID | 요구사항 | 우선순위 |
|----|----------|----------|
| NFR-001 | 대량 로그 저장을 위한 효율적인 인덱스 설계 | HIGH |
| NFR-002 | 기존 Event 스키마와 네이밍 충돌 방지 | HIGH |
| NFR-003 | REST API 일관성 유지 (GOP API 설계 원칙 준수) | HIGH |

### 2.3 선행 요구사항: Server 스키마 리팩토링

> ⚠️ **현재 문제점**
> 1. `servers` 테이블에 리소스 현재 값(`cpu_usage`, `ram_usage`, `disk_usage`, `network_throughput`)이 컬럼으로 존재
> 2. 이 값들은 **실시간으로 변하는 데이터**이므로 DB 컬럼으로 저장하기 부적합
> 3. **임계치(threshold) 설정 값이 없어** `RESOURCE_THRESHOLD` 이벤트 발생 기준 없음

#### 제안: 리소스 현황 컬럼 제거 + threshold_config JSONB 추가

**Before (현재)**:
```json
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
  "cpu_usage": 45.0,          // ❌ 실시간 변동 - DB 저장 부적합
  "ram_usage": 62.0,          // ❌ 실시간 변동 - DB 저장 부적합
  "disk_usage": 78.0,         // ❌ 실시간 변동 - DB 저장 부적합
  "network_throughput": "125MB/s",  // ❌ 실시간 변동 - DB 저장 부적합
  "created_at": "...",
  "updated_at": "..."
}
```

**After (제안)**:
```json
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
  "threshold_config": {       // ✅ 설정값 - DB 저장 적합
    "cpu": { "warning": 80, "critical": 95 },
    "ram": { "warning": 75, "critical": 90 },
    "disk": { "warning": 80, "critical": 95 },
    "network": { "warning_mbps": 800, "critical_mbps": 950 }
  },
  "created_at": "...",
  "updated_at": "..."
}
```

#### SQL 변경 (Migration)

```sql
-- 1. 실시간 리소스 컬럼 제거
ALTER TABLE servers
DROP COLUMN IF EXISTS cpu_usage,
DROP COLUMN IF EXISTS ram_usage,
DROP COLUMN IF EXISTS disk_usage,
DROP COLUMN IF EXISTS network_throughput;

-- 2. 임계치 설정 컬럼 추가
ALTER TABLE servers
ADD COLUMN threshold_config JSONB DEFAULT NULL;
```

#### 설계 근거

| 데이터 유형 | 저장 위치 | 이유 |
|------------|----------|------|
| **리소스 현재 값** (cpu 45%) | System Event 로그 | 실시간 변동, 이력 필요 |
| **임계치 설정** (cpu warning 80%) | servers.threshold_config | 설정값, 변경 드묾 |
| **상태 변경 이력** (NORMAL→WARNING) | System Event 로그 | 이벤트 기반 추적 |

#### threshold_config JSON 구조

```json
{
  "cpu": {
    "warning": 80,
    "critical": 95
  },
  "ram": {
    "warning": 75,
    "critical": 90
  },
  "disk": {
    "warning": 80,
    "critical": 95
  },
  "network": {
    "warning_mbps": 800,
    "critical_mbps": 950
  }
}
```

| 필드 | 설명 |
|------|------|
| `cpu.warning` | CPU 경고 임계치 (%) |
| `cpu.critical` | CPU 심각 임계치 (%) |
| `ram.warning` | RAM 경고 임계치 (%) |
| `ram.critical` | RAM 심각 임계치 (%) |
| `disk.warning` | Disk 경고 임계치 (%) |
| `disk.critical` | Disk 심각 임계치 (%) |
| `network.warning_mbps` | 네트워크 경고 임계치 (MB/s) |
| `network.critical_mbps` | 네트워크 심각 임계치 (MB/s) |

#### 기본값 예시

```json
{
  "cpu": { "warning": 80, "critical": 95 },
  "ram": { "warning": 75, "critical": 90 },
  "disk": { "warning": 80, "critical": 95 }
}
```

> **Alternative**: 전역 설정이 필요한 경우 `server_categories` 테이블에 `default_threshold_config`를 추가하고, 개별 서버에서 override 가능하도록 설계할 수도 있습니다.

### 2.4 Server Resource Monitoring API (서버 리소스 모니터링)

> **핵심 개념**: 실시간 리소스 모니터링 데이터는 **별도 테이블 + 전용 API**로 분리하여 관리

#### 배경 및 필요성

| 구분 | 저장 위치 | 이유 |
|------|----------|------|
| **임계치 설정** | `servers.threshold_config` | 설정값, 변경 드묾 |
| **실시간 리소스 값** | `server_metrics` (신규) | 주기적 수집, 이력 필요, 대량 데이터 |
| **임계치 초과 알림** | `system_events` | 이벤트 기반 알림 |

#### server_metrics 테이블 설계

```sql
CREATE TABLE server_metrics (
    id SERIAL PRIMARY KEY,

    -- Server FK
    server_id INTEGER NOT NULL REFERENCES servers(id) ON DELETE CASCADE,

    -- Resource Metrics
    cpu_usage DECIMAL(5,2),           -- CPU 사용률 (%)
    ram_usage DECIMAL(5,2),           -- RAM 사용률 (%)
    ram_total_gb DECIMAL(10,2),       -- 총 RAM (GB)
    ram_used_gb DECIMAL(10,2),        -- 사용 RAM (GB)
    disk_usage DECIMAL(5,2),          -- Disk 사용률 (%)
    disk_total_gb DECIMAL(10,2),      -- 총 Disk (GB)
    disk_used_gb DECIMAL(10,2),       -- 사용 Disk (GB)
    network_in_mbps DECIMAL(10,2),    -- 네트워크 수신 (MB/s)
    network_out_mbps DECIMAL(10,2),   -- 네트워크 송신 (MB/s)

    -- Process Info (Optional)
    process_count INTEGER,            -- 실행 중 프로세스 수

    -- Additional Info
    detail JSONB,                     -- 추가 메트릭 (GPU, 온도 등)

    -- Timestamp
    collected_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_server_metrics_server_id ON server_metrics(server_id);
CREATE INDEX idx_server_metrics_collected_at ON server_metrics(collected_at DESC);
CREATE INDEX idx_server_metrics_server_collected ON server_metrics(server_id, collected_at DESC);
```

#### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/servers/{id}/metrics` | 리소스 메트릭 전송 (Agent → Server) |
| GET | `/api/servers/{id}/metrics` | 서버 메트릭 조회 (최근 N개) |
| GET | `/api/servers/{id}/metrics/latest` | 최신 메트릭 1건 조회 |
| GET | `/api/server-metrics` | 전체 서버 메트릭 조회 (필터링) |
| DELETE | `/api/servers/{id}/metrics` | 오래된 메트릭 삭제 (보존 정책) |

#### POST /api/servers/{id}/metrics - 메트릭 전송

**Request Body** (Agent가 주기적으로 전송):
```json
{
  "cpu_usage": 45.5,
  "ram_usage": 62.3,
  "ram_total_gb": 32.0,
  "ram_used_gb": 19.94,
  "disk_usage": 78.0,
  "disk_total_gb": 500.0,
  "disk_used_gb": 390.0,
  "network_in_mbps": 25.5,
  "network_out_mbps": 12.3,
  "process_count": 156,
  "detail": {
    "gpu_usage": 30.0,
    "gpu_memory_usage": 45.0,
    "temperature_cpu": 65,
    "temperature_gpu": 72
  },
  "collected_at": "2026-01-15T10:30:00Z"
}
```

**Response (201 Created)**:
```json
{
  "success": true,
  "message": "Server metrics recorded successfully",
  "data": {
    "id": 12345,
    "server_id": 1,
    "cpu_usage": 45.5,
    "ram_usage": 62.3,
    "ram_total_gb": 32.0,
    "ram_used_gb": 19.94,
    "disk_usage": 78.0,
    "disk_total_gb": 500.0,
    "disk_used_gb": 390.0,
    "network_in_mbps": 25.5,
    "network_out_mbps": 12.3,
    "process_count": 156,
    "detail": {
      "gpu_usage": 30.0,
      "gpu_memory_usage": 45.0,
      "temperature_cpu": 65,
      "temperature_gpu": 72
    },
    "collected_at": "2026-01-15T10:30:00.000Z",
    "created_at": "2026-01-15T10:30:01.000Z",
    "threshold_exceeded": []
  },
  "meta": {
    "timestamp": "2026-01-15T10:30:01.000Z"
  }
}
```

**임계치 초과 시 Response**:
```json
{
  "success": true,
  "message": "Server metrics recorded with threshold alerts",
  "data": {
    "id": 12346,
    "server_id": 1,
    "cpu_usage": 96.5,
    "ram_usage": 92.3,
    "ram_total_gb": 32.0,
    "ram_used_gb": 29.54,
    "disk_usage": 78.0,
    "disk_total_gb": 500.0,
    "disk_used_gb": 390.0,
    "network_in_mbps": 25.5,
    "network_out_mbps": 12.3,
    "process_count": 180,
    "detail": {
      "gpu_usage": 30.0,
      "gpu_memory_usage": 45.0,
      "temperature_cpu": 65,
      "temperature_gpu": 72
    },
    "collected_at": "2026-01-15T10:31:00.000Z",
    "created_at": "2026-01-15T10:31:01.000Z",
    "threshold_exceeded": [
      { "resource": "cpu", "level": "critical", "value": 96.5, "threshold": 95 },
      { "resource": "ram", "level": "critical", "value": 92.3, "threshold": 90 }
    ]
  },
  "meta": {
    "timestamp": "2026-01-15T10:31:01.000Z",
    "request_id": "550e8401-e29b-41d4-a716-446655440000"
  }
}
```

> **자동 연동**: 메트릭 전송 시 `threshold_config`와 비교하여 임계치 초과 시 `system_events`에 자동 기록

#### GET /api/servers/{id}/metrics - 메트릭 조회

**Query Parameters**:

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| limit | integer | N | 조회 개수 (기본값: 100, 최대: 1000) |
| start_time | string | N | 시작 시간 (ISO 8601) |
| end_time | string | N | 종료 시간 (ISO 8601) |
| interval | string | N | 집계 간격 (1m, 5m, 1h, 1d) |

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Server metrics retrieved successfully",
  "data": [
    {
      "id": 12345,
      "server_id": 1,
      "cpu_usage": 45.5,
      "ram_usage": 62.3,
      "disk_usage": 78.0,
      "network_in_mbps": 25.5,
      "network_out_mbps": 12.3,
      "collected_at": "2026-01-15T10:30:00.000Z"
    },
    {
      "id": 12344,
      "server_id": 1,
      "cpu_usage": 42.1,
      "ram_usage": 60.5,
      "disk_usage": 78.0,
      "network_in_mbps": 20.3,
      "network_out_mbps": 10.1,
      "collected_at": "2026-01-15T10:29:00.000Z"
    }
  ],
  "pagination": {
    "limit": 100,
    "total": 1440
  },
  "meta": {
    "timestamp": "2026-01-15T10:35:00.000Z"
  }
}
```

#### 데이터 흐름 다이어그램

```
┌──────────────────┐     POST /api/servers/{id}/metrics     ┌─────────────────┐
│   Server Agent   │ ─────────────────────────────────────► │   GOP Server    │
│  (모니터링 수집)   │         (주기: 1분 또는 설정값)           │   (API Server)  │
└──────────────────┘                                        └────────┬────────┘
                                                                     │
                                                                     ▼
                                                  ┌──────────────────────────────────┐
                                                  │          처리 로직               │
                                                  │  1. server_metrics 테이블 저장    │
                                                  │  2. threshold_config 비교         │
                                                  │  3. 초과 시 system_events 생성    │
                                                  └──────────────────────────────────┘
                                                                     │
                              ┌───────────────────┬──────────────────┘
                              ▼                   ▼
                    ┌─────────────────┐  ┌─────────────────┐
                    │ server_metrics  │  │ system_events   │
                    │   (이력 저장)    │  │ (알림/이벤트)    │
                    └─────────────────┘  └─────────────────┘
```

#### 데이터 보존 정책

| 데이터 유형 | 보존 기간 | 정리 방법 |
|------------|----------|----------|
| Raw Metrics (1분 간격) | 7일 | 자동 삭제 또는 집계 후 삭제 |
| Hourly Aggregated | 30일 | 자동 삭제 |
| Daily Aggregated | 1년 | 아카이브 |
| System Events | 영구 | 수동 삭제 |

> **구현 옵션**: PostgreSQL의 `pg_cron` 또는 애플리케이션 레벨 스케줄러로 정리 작업 수행

---

## 3. 데이터 모델

### 3.1 Enum 정의

#### 3.1.1 EnumSystemEventType (이벤트 유형 - 15종)

> **참조**: PRD_SystemEvent_Sync.md v1.2
> **Note**: USER_* 9종은 UserLoginLog로, ConfigChangeLog 중복 4종(CONFIG_CHANGED, DEVICE_ADDED, DEVICE_REMOVED, DEVICE_STATUS_CHANGED)은 ConfigChangeLog로 분리됨

```sql
CREATE TYPE enum_system_event_type AS ENUM (
    -- 리소스 관련 (1종)
    'RESOURCE_THRESHOLD',      -- 리소스 임계치 초과 (CPU, RAM, Disk)

    -- 서버 상태 (3종)
    'SERVER_CONNECTED',        -- 서버 연결됨
    'SERVER_DISCONNECTED',     -- 서버 연결 해제됨
    'SERVER_ERROR',            -- 서버 오류

    -- 서비스 상태 (3종)
    'SERVICE_STARTED',         -- 서비스 시작됨
    'SERVICE_STOPPED',         -- 서비스 중지됨
    'SERVICE_ERROR',           -- 서비스 오류

    -- 연결 상태 (2종)
    'CONNECTION_LOST',         -- 연결 끊김
    'CONNECTION_RESTORED',     -- 연결 복구됨

    -- 보안 (1종)
    'SECURITY_ALERT',          -- 보안 경고

    -- 디바이스 연결 (1종)
    'DEVICE_CONNECTED',        -- 디바이스 연결됨

    -- 백업 관련 (3종)
    'BACKUP_STARTED',          -- 백업 시작됨
    'BACKUP_COMPLETED',        -- 백업 완료됨
    'BACKUP_FAILED',           -- 백업 실패함

    -- 시스템 업데이트 (1종)
    'SYSTEM_UPDATE'            -- 시스템 업데이트
);
```

#### 3.1.2 EnumSystemEventSeverity (심각도)

```sql
CREATE TYPE enum_system_event_severity AS ENUM (
    'INFO',      -- 정보성 메시지
    'WARNING',   -- 경고 (주의 필요)
    'ERROR',     -- 오류 (조치 필요)
    'CRITICAL'   -- 심각 (즉시 조치 필요)
);
```

### 3.2 system_events 테이블

```sql
-- Table Definition
CREATE TABLE system_events (
    id SERIAL PRIMARY KEY,

    -- Server FK (SET NULL on delete - Event 영속성 보장)
    server_id INTEGER REFERENCES servers(id) ON DELETE SET NULL,
    server_description VARCHAR(200),       -- Server 스냅샷 (삭제 대비)

    -- Event Classification
    type_event enum_system_event_type NOT NULL,
    severity enum_system_event_severity NOT NULL DEFAULT 'INFO',

    -- Event Content
    title VARCHAR(200) NOT NULL,           -- 이벤트 제목 (요약)
    message TEXT,                          -- 상세 메시지
    detail JSONB,                          -- 추가 정보 (유연한 확장)

    -- Source Information
    source VARCHAR(100),                   -- 이벤트 발생 소스 (서비스명, 모듈명)

    -- Status
    is_acknowledged BOOLEAN NOT NULL DEFAULT FALSE,  -- 확인 여부
    acknowledged_at TIMESTAMP WITH TIME ZONE,        -- 확인 시각
    acknowledged_by VARCHAR(100),                    -- 확인자

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_system_events_id ON system_events(id);
CREATE INDEX idx_system_events_server_id ON system_events(server_id);
CREATE INDEX idx_system_events_type_event ON system_events(type_event);
CREATE INDEX idx_system_events_severity ON system_events(severity);
CREATE INDEX idx_system_events_created_at ON system_events(created_at DESC);
CREATE INDEX idx_system_events_is_acknowledged ON system_events(is_acknowledged);

-- Composite Index for common queries
CREATE INDEX idx_system_events_server_type ON system_events(server_id, type_event);
CREATE INDEX idx_system_events_server_created ON system_events(server_id, created_at DESC);
```

### 3.3 필드 정의

| 필드명 | 타입 | NULL 허용 | 기본값 | 설명 |
|--------|------|-----------|--------|------|
| id | SERIAL | NO | AUTO | 고유 식별자 (PK) |
| server_id | INTEGER | YES | - | FK → servers.id (SET NULL on delete) |
| server_description | VARCHAR(200) | YES | NULL | Server 정보 스냅샷 |
| type_event | ENUM | NO | - | 이벤트 유형 (EnumSystemEventType) |
| severity | ENUM | NO | INFO | 심각도 (EnumSystemEventSeverity) |
| title | VARCHAR(200) | NO | - | 이벤트 제목 |
| message | TEXT | YES | NULL | 상세 메시지 |
| detail | JSONB | YES | NULL | 추가 정보 (JSON) |
| source | VARCHAR(100) | YES | NULL | 이벤트 발생 소스 |
| is_acknowledged | BOOLEAN | NO | FALSE | 확인 여부 |
| acknowledged_at | TIMESTAMP | YES | NULL | 확인 시각 |
| acknowledged_by | VARCHAR(100) | YES | NULL | 확인자 |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 생성 시간 |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 수정 시간 |

### 3.4 detail JSONB 구조 예시

#### RESOURCE_THRESHOLD (리소스 임계치)
```json
{
  "resource_type": "CPU",
  "threshold": 90,
  "current_value": 95.5,
  "unit": "%",
  "duration_seconds": 300
}
```

#### SERVER_STATUS_CHANGE (상태 변경)
```json
{
  "previous_status": "NORMAL",
  "new_status": "WARNING",
  "reason": "High CPU usage detected"
}
```

#### CONNECTION_LOST (연결 끊김)
```json
{
  "target_ip": "192.168.1.100",
  "target_port": 8080,
  "last_seen": "2026-01-15T10:30:00Z",
  "retry_count": 3
}
```

#### BACKUP_COMPLETED (백업 완료)
```json
{
  "backup_type": "FULL",
  "file_path": "/backup/2026-01-15/db_full.tar.gz",
  "file_size_mb": 1024,
  "duration_seconds": 180
}
```

### 3.5 FK Behavior

| FK | ON DELETE | 설명 |
|----|-----------|------|
| server_id → servers.id | SET NULL | Server 삭제 시 이벤트는 유지, server_id만 NULL |

> **Note**: Server 삭제 시에도 System Event 기록은 유지됩니다. `server_description` 필드에 Server 정보 스냅샷을 저장하여 삭제 후에도 참조 가능합니다.

---

## 4. API 설계

### 4.1 리소스 구조

```
/api/system-events              - System Event 목록 (GET, POST)
/api/system-events/{id}         - 특정 System Event (GET, PATCH, DELETE)
/api/system-events/{id}/acknowledge - System Event 확인 처리 (POST)
/api/system-events/summary      - System Event 요약 (GET)
/api/servers/{id}/system-events - 특정 서버의 System Event 목록 (GET)
```

### 4.2 System Event 목록 조회

**Endpoint**: `GET /api/system-events`

**Query Parameters**:

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| page | integer | N | 페이지 번호 (기본값: 1) |
| limit | integer | N | 페이지당 항목 수 (기본값: 20, 최대: 100) |
| server_id | integer | N | 서버 ID 필터 |
| type_event | string | N | 이벤트 유형 필터 (EnumSystemEventType) |
| severity | string | N | 심각도 필터 (EnumSystemEventSeverity) |
| is_acknowledged | boolean | N | 확인 여부 필터 |
| start_date | string | N | 시작일 (ISO 8601) |
| end_date | string | N | 종료일 (ISO 8601) |
| source | string | N | 소스 필터 |

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "System events retrieved successfully",
  "data": [
    {
      "id": 1,
      "server_id": 1,
      "server_description": "VMS-ab1120 (192.168.1.10)",
      "type_event": "RESOURCE_THRESHOLD",
      "severity": "WARNING",
      "title": "CPU 사용률 임계치 초과",
      "message": "CPU 사용률이 90%를 초과했습니다. 현재: 95.5%",
      "detail": {
        "resource_type": "CPU",
        "threshold": 90,
        "current_value": 95.5,
        "unit": "%"
      },
      "source": "ResourceMonitor",
      "is_acknowledged": false,
      "acknowledged_at": null,
      "acknowledged_by": null,
      "created_at": "2026-01-15T10:30:00.000Z",
      "updated_at": "2026-01-15T10:30:00.000Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "total_pages": 8
  },
  "meta": {
    "timestamp": "2026-01-15T10:35:00.000Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### 4.3 System Event 단건 조회

**Endpoint**: `GET /api/system-events/{id}`

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "System event retrieved successfully",
  "data": {
    "id": 1,
    "server_id": 1,
    "server_description": "VMS-ab1120 (192.168.1.10)",
    "type_event": "RESOURCE_THRESHOLD",
    "severity": "WARNING",
    "title": "CPU 사용률 임계치 초과",
    "message": "CPU 사용률이 90%를 초과했습니다. 현재: 95.5%",
    "detail": {
      "resource_type": "CPU",
      "threshold": 90,
      "current_value": 95.5,
      "unit": "%",
      "duration_seconds": 300
    },
    "source": "ResourceMonitor",
    "is_acknowledged": false,
    "acknowledged_at": null,
    "acknowledged_by": null,
    "created_at": "2026-01-15T10:30:00.000Z",
    "updated_at": "2026-01-15T10:30:00.000Z",
    "server": {
      "id": 1,
      "name": "VMS-ab1120",
      "category_id": 1,
      "status": "WARNING",
      "ip_address": "192.168.1.10"
    }
  },
  "meta": {
    "timestamp": "2026-01-15T10:35:00.000Z",
    "request_id": "550e8401-e29b-41d4-a716-446655440000"
  }
}
```

### 4.4 System Event 생성

**Endpoint**: `POST /api/system-events`

**Request Body**:
```json
{
  "server_id": 1,
  "type_event": "RESOURCE_THRESHOLD",
  "severity": "WARNING",
  "title": "CPU 사용률 임계치 초과",
  "message": "CPU 사용률이 90%를 초과했습니다. 현재: 95.5%",
  "detail": {
    "resource_type": "CPU",
    "threshold": 90,
    "current_value": 95.5,
    "unit": "%"
  },
  "source": "ResourceMonitor"
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| server_id | integer | N | 관련 서버 ID (NULL 가능 - 전역 이벤트) |
| type_event | string | Y | 이벤트 유형 (EnumSystemEventType) |
| severity | string | N | 심각도 (기본값: INFO) |
| title | string | Y | 이벤트 제목 |
| message | string | N | 상세 메시지 |
| detail | object | N | 추가 정보 (JSONB) |
| source | string | N | 이벤트 발생 소스 |

**Response (201 Created)**:
```json
{
  "success": true,
  "message": "System event created successfully",
  "data": {
    "id": 2,
    "server_id": 1,
    "server_description": "VMS-ab1120 (192.168.1.10)",
    "type_event": "RESOURCE_THRESHOLD",
    "severity": "WARNING",
    "title": "CPU 사용률 임계치 초과",
    "message": "CPU 사용률이 90%를 초과했습니다. 현재: 95.5%",
    "detail": {
      "resource_type": "CPU",
      "threshold": 90,
      "current_value": 95.5,
      "unit": "%"
    },
    "source": "ResourceMonitor",
    "is_acknowledged": false,
    "acknowledged_at": null,
    "acknowledged_by": null,
    "created_at": "2026-01-15T10:36:00.000Z",
    "updated_at": "2026-01-15T10:36:00.000Z"
  },
  "meta": {
    "timestamp": "2026-01-15T10:36:00.000Z",
    "request_id": "550e8402-e29b-41d4-a716-446655440000"
  }
}
```

### 4.5 System Event 확인 처리

**Endpoint**: `POST /api/system-events/{id}/acknowledge`

**Request Body**:
```json
{
  "acknowledged_by": "admin@example.com"
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
    "acknowledged_at": "2026-01-15T10:40:00.000Z",
    "acknowledged_by": "admin@example.com"
  },
  "meta": {
    "timestamp": "2026-01-15T10:40:00.000Z",
    "request_id": "550e8403-e29b-41d4-a716-446655440000"
  }
}
```

### 4.6 System Event 수정 (부분)

**Endpoint**: `PATCH /api/system-events/{id}`

**Request Body**:
```json
{
  "severity": "CRITICAL",
  "message": "CPU 사용률이 지속적으로 높습니다. 즉시 확인이 필요합니다."
}
```

**Response (200 OK)**: 수정된 System Event 반환

### 4.7 System Event 삭제

**Endpoint**: `DELETE /api/system-events/{id}`

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "System event deleted successfully",
  "data": null,
  "meta": {
    "timestamp": "2026-01-15T10:45:00.000Z",
    "request_id": "550e8404-e29b-41d4-a716-446655440000"
  }
}
```

### 4.8 System Event 요약 (Dashboard)

**Endpoint**: `GET /api/system-events/summary`

**Query Parameters**:

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| hours | integer | N | 최근 N시간 내 이벤트 (기본값: 24) |

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "System event summary retrieved successfully",
  "data": {
    "total": 150,
    "by_severity": {
      "INFO": 80,
      "WARNING": 45,
      "ERROR": 20,
      "CRITICAL": 5
    },
    "by_type": {
      "RESOURCE_THRESHOLD": 50,
      "SERVER_STATUS_CHANGE": 30,
      "CONNECTION_LOST": 15,
      "SERVICE_RESTART": 10,
      "OTHER": 45
    },
    "unacknowledged": 25,
    "recent_critical": [
      {
        "id": 100,
        "server_id": 3,
        "server_description": "AI-Server-01 (192.168.1.30)",
        "type_event": "SERVICE_STOP",
        "severity": "CRITICAL",
        "title": "AI 분석 서비스 중단",
        "created_at": "2026-01-15T10:25:00.000Z"
      }
    ]
  },
  "meta": {
    "timestamp": "2026-01-15T10:35:00.000Z",
    "request_id": "550e8405-e29b-41d4-a716-446655440000"
  }
}
```

### 4.9 특정 서버의 System Event 조회

**Endpoint**: `GET /api/servers/{server_id}/system-events`

**Query Parameters**: 4.2와 동일 (server_id 제외)

**Response**: 4.2와 동일한 형식

---

## 5. ERD 다이어그램

```
┌─────────────────────────┐       ┌─────────────────────────────────────────────┐
│    server_categories    │       │                system_events                │
├─────────────────────────┤       ├─────────────────────────────────────────────┤
│ id (PK)                 │       │ id (PK)                                     │
│ name                    │       │ server_id (FK) ─────────────────────────────┼──┐
│ type_server (UNIQUE)    │       │ server_description                          │  │
│ description             │       │ type_event (ENUM)                           │  │
│ sort_order              │       │ severity (ENUM)                             │  │
│ created_at              │       │ title                                       │  │
│ updated_at              │       │ message                                     │  │
└─────────────────────────┘       │ detail (JSONB)                              │  │
          │                       │ source                                      │  │
          │ 1:N                   │ is_acknowledged                             │  │
          ▼                       │ acknowledged_at                             │  │
┌─────────────────────────┐       │ acknowledged_by                             │  │
│         servers         │       │ created_at                                  │  │
├─────────────────────────┤       │ updated_at                                  │  │
│ id (PK)               ◄─┼───────┴─────────────────────────────────────────────┘  │
│ category_id (FK)        │                                1:N (SET NULL)          │
│ name                    │◄───────────────────────────────────────────────────────┘
│ status                  │                                                        │
│ ip_address              │       ┌─────────────────────────────────────────────┐  │
│ port                    │       │              server_metrics                 │  │
│ hostname                │       ├─────────────────────────────────────────────┤  │
│ user_name               │       │ id (PK)                                     │  │
│ user_password           │       │ server_id (FK) ─────────────────────────────┼──┘
│ threshold_config (JSONB)│       │ cpu_usage                                   │
│ created_at              │       │ ram_usage                                   │
│ updated_at              │       │ ram_total_gb, ram_used_gb                   │
└─────────────────────────┘       │ disk_usage                                  │
                                  │ disk_total_gb, disk_used_gb                 │
                                  │ network_in_mbps, network_out_mbps           │
                                  │ process_count                               │
                                  │ detail (JSONB)                              │
                                  │ collected_at                                │
                                  │ created_at                                  │
                                  └─────────────────────────────────────────────┘
                                                    1:N (CASCADE)

※ 설계 원칙:
   - threshold_config: 임계치 설정 (변경 드묾) → servers 테이블에 저장
   - server_metrics: 실시간 리소스 현황 (주기적 수집) → 별도 테이블로 분리
   - system_events: 임계치 초과 알림/이벤트 → 자동 생성
```

---

## 6. 구현 가이드

### 6.1 SQLAlchemy Model

```python
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class EnumSystemEventType(str, enum.Enum):
    """
    System Event type enumeration (15종)
    참조: PRD_SystemEvent_Sync.md v1.2
    Note: USER_* 9종은 UserLoginLog로, ConfigChangeLog 중복 4종은 제거됨
    """
    # 리소스 관련 (1종)
    RESOURCE_THRESHOLD = "RESOURCE_THRESHOLD"

    # 서버 상태 (3종)
    SERVER_CONNECTED = "SERVER_CONNECTED"
    SERVER_DISCONNECTED = "SERVER_DISCONNECTED"
    SERVER_ERROR = "SERVER_ERROR"

    # 서비스 상태 (3종)
    SERVICE_STARTED = "SERVICE_STARTED"
    SERVICE_STOPPED = "SERVICE_STOPPED"
    SERVICE_ERROR = "SERVICE_ERROR"

    # 연결 상태 (2종)
    CONNECTION_LOST = "CONNECTION_LOST"
    CONNECTION_RESTORED = "CONNECTION_RESTORED"

    # 보안 (1종)
    SECURITY_ALERT = "SECURITY_ALERT"

    # 디바이스 연결 (1종)
    DEVICE_CONNECTED = "DEVICE_CONNECTED"

    # 백업 관련 (3종)
    BACKUP_STARTED = "BACKUP_STARTED"
    BACKUP_COMPLETED = "BACKUP_COMPLETED"
    BACKUP_FAILED = "BACKUP_FAILED"

    # 시스템 업데이트 (1종)
    SYSTEM_UPDATE = "SYSTEM_UPDATE"

class EnumSystemEventSeverity(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class SystemEvent(Base):
    __tablename__ = "system_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    server_id = Column(Integer, ForeignKey("servers.id", ondelete="SET NULL"), nullable=True)
    server_description = Column(String(200), nullable=True)

    type_event = Column(Enum(EnumSystemEventType), nullable=False)
    severity = Column(Enum(EnumSystemEventSeverity), nullable=False, default=EnumSystemEventSeverity.INFO)

    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=True)
    detail = Column(JSONB, nullable=True)
    source = Column(String(100), nullable=True)

    is_acknowledged = Column(Boolean, nullable=False, default=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(String(100), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationship
    server = relationship("Server", back_populates="system_events")
```

### 6.2 Pydantic Schema

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class SystemEventCreate(BaseModel):
    server_id: Optional[int] = Field(None, description="관련 서버 ID")
    type_event: str = Field(..., description="이벤트 유형")
    severity: str = Field("INFO", description="심각도")
    title: str = Field(..., max_length=200, description="이벤트 제목")
    message: Optional[str] = Field(None, description="상세 메시지")
    detail: Optional[dict] = Field(None, description="추가 정보 (JSONB)")
    source: Optional[str] = Field(None, max_length=100, description="이벤트 발생 소스")

class SystemEventResponse(BaseModel):
    id: int
    server_id: Optional[int]
    server_description: Optional[str]
    type_event: str
    severity: str
    title: str
    message: Optional[str]
    detail: Optional[dict]
    source: Optional[str]
    is_acknowledged: bool
    acknowledged_at: Optional[datetime]
    acknowledged_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

---

## 7. 사용 시나리오

### 7.1 리소스 임계치 모니터링

```python
# 서버 리소스 모니터링 시 CPU 90% 초과 감지
system_event = {
    "server_id": 1,
    "type_event": "RESOURCE_THRESHOLD",
    "severity": "WARNING",
    "title": "CPU 사용률 임계치 초과",
    "message": "CPU 사용률이 90%를 초과했습니다.",
    "detail": {
        "resource_type": "CPU",
        "threshold": 90,
        "current_value": 95.5,
        "unit": "%"
    },
    "source": "ResourceMonitor"
}
```

### 7.2 서비스 상태 변경

```python
# 서비스 중단 감지
system_event = {
    "server_id": 3,
    "type_event": "SERVICE_STOP",
    "severity": "CRITICAL",
    "title": "AI 분석 서비스 중단",
    "message": "AI 영상 분석 서비스가 예기치 않게 중단되었습니다.",
    "detail": {
        "service_name": "ai-analysis-service",
        "pid": 12345,
        "exit_code": 1,
        "last_log": "Out of memory"
    },
    "source": "ServiceWatcher"
}
```

### 7.3 백업 완료 로깅

```python
# 백업 성공 기록
system_event = {
    "server_id": 5,
    "type_event": "BACKUP_COMPLETED",
    "severity": "INFO",
    "title": "데이터베이스 전체 백업 완료",
    "message": "GOP 데이터베이스 전체 백업이 완료되었습니다.",
    "detail": {
        "backup_type": "FULL",
        "file_path": "/backup/2026-01-15/gop_db_full.tar.gz",
        "file_size_mb": 2048,
        "duration_seconds": 360,
        "tables_count": 25
    },
    "source": "BackupScheduler"
}
```

---

## 8. 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| v1.0 | 2026-01-15 | 초안 작성 - System Event 스키마 및 API 설계 |
| v1.1 | 2026-01-15 | **Server Threshold 확장 추가**<br>• 섹션 2.3: servers.threshold_config JSONB 컬럼 추가 제안<br>• CPU/RAM/Disk/Network 임계치 설정 구조 정의<br>• 카테고리별 기본값 override 방안 제시 |
| v1.2 | 2026-01-15 | **Server Resource Monitoring API 추가**<br>• 섹션 2.4: server_metrics 테이블 설계<br>• POST/GET /api/servers/{id}/metrics API 정의<br>• Agent → Server 메트릭 전송 흐름 설계<br>• 임계치 초과 시 system_events 자동 연동<br>• 데이터 보존 정책 정의 |

---

## 9. 참조 문서

- [GOP_스키마_전체.md](./GOP_스키마_전체.md) - 전체 데이터베이스 스키마
- [GOP_Restful_Api_연동설계.md](../GOP_Restful_Api_연동설계.md) - RESTful API 설계서
- [PRD_Event_Detail_JsonB.md](./PRD_Event_Detail_JsonB.md) - Event Detail JSONB 설계

---

**문서 끝**
