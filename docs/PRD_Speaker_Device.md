# PRD: Speaker Device (방송장비) 구현

**문서 버전**: v1.0
**작성일**: 2026-01-07
**작성자**: Claude Code Assistant
**상태**: Draft
**참조 문서**:
- `pdfs/20251230_스피커 nats메시지 정의.pdf`
- `GOP_Restful_Api_연동설계.md`
- `PRD_Device_Structure_Refactoring.md`

---

## 목차

1. [개요](#1-개요)
2. [설계 원칙](#2-설계-원칙)
3. [Enum 정의](#3-enum-정의)
4. [데이터 모델](#4-데이터-모델)
5. [스키마 정의](#5-스키마-정의)
6. [API Endpoints](#6-api-endpoints)
7. [Response 포맷](#7-response-포맷)
8. [구현 계획](#8-구현-계획)
9. [변경 이력](#9-변경-이력)

---

## 1. 개요

### 1.1 목표

방송장비(IP Speaker)를 Device Polymorphic 구조에 통합하여 DB API에서 관리합니다.

### 1.2 범위

| 포함 | 제외 |
|------|------|
| Speaker 장비 정보 CRUD | 방송 제어 (파일/TTS/음원 방송) |
| FileGroup (방송음원 파일풀) CRUD | 실시간 방송 시작/중지 |
| Server 참조 (FK) | NATS 브로커 통신 |
| Device Polymorphic 상속 | 단말기 그룹 방송 |

### 1.3 핵심 요구사항

1. **Device Polymorphic 상속**: `Device` → `Speaker` (Joined Table Inheritance)
2. **Server 참조**: `server_id` FK로 SPEAKER_API 서버 연결
3. **FileGroup 관리**: 방송음원 파일 풀 별도 테이블
4. **기존 Enum 활용**: `EnumDeviceType.IpSpeaker`, `EnumDeviceStatus` 재사용

---

## 2. 설계 원칙

### 2.1 Device 상속 구조

```
devices (Base Table)
    │
    ├── controllers
    ├── sensors
    ├── cameras
    └── speakers  ← NEW (v2.5)
```

### 2.2 Enum 통합 전략

| PDF 문서 Enum | GOP Enum 매핑 | 설명 |
|---------------|---------------|------|
| `EnumBcastDeviceStatus` | `EnumDeviceStatus` | ACTIVATED/ERROR/DEACTIVATED 동일 |
| `EnumBcastDeviceType` | `EnumSpeakerType` (신규) | NORMAL/ADMIN/MONITOR/DEV |
| `EnumBcastServerStatus` | `EnumServerStatus` | NORMAL(=OK)/ERROR 매핑 |

### 2.3 Server 연동

- Speaker는 `server_id`로 Server(SPEAKER_API 유형) 참조
- Server 모델의 기존 구조 활용 (ip_address, port, user_name, user_password 등)

---

## 3. Enum 정의

### 3.1 EnumDeviceCategory 확장

```python
class EnumDeviceCategory(str, Enum):
    CONTROLLER = "controller"
    SENSOR = "sensor"
    CAMERA = "camera"
    SPEAKER = "speaker"  # NEW (v2.5)
```

### 3.2 EnumSpeakerType (신규)

```python
class EnumSpeakerType(str, Enum):
    """
    Speaker device type enumeration
    Based on EnumBcastDeviceType from NATS message spec
    """
    NORMAL = "NORMAL"     # 일반 스피커 단말
    ADMIN = "ADMIN"       # 관리자 단말
    MONITOR = "MONITOR"   # 모니터링 단말
    DEV = "DEV"           # 음원/마이크 단말 (입력 장치)
```

### 3.3 기존 Enum 재사용

| Enum | 용도 |
|------|------|
| `EnumDeviceStatus` | Speaker 상태 (ACTIVATED/ERROR/DEACTIVATED) |
| `EnumDeviceType.IpSpeaker` | Device 타입 식별 |
| `EnumServerStatus` | 연결된 Server 상태 |

---

## 4. 데이터 모델

### 4.1 speakers 테이블 (Device 상속)

```sql
-- PostgreSQL CREATE TABLE
CREATE TABLE speakers (
    -- FK/PK to devices (Joined Table Inheritance)
    id INTEGER PRIMARY KEY REFERENCES devices(id) ON DELETE CASCADE,

    -- Speaker 전용 필드
    speaker_type VARCHAR(20) NOT NULL DEFAULT 'NORMAL',  -- EnumSpeakerType

    -- Server 연결 (FK)
    server_id INTEGER REFERENCES servers(id) ON DELETE SET NULL,

    -- 스피커 속성
    description VARCHAR(500)             -- 설명
);

-- Indexes
CREATE INDEX idx_speakers_id ON speakers(id);
CREATE INDEX idx_speakers_server_id ON speakers(server_id);
-- number_device는 Device Base에서 상속받아 사용
CREATE UNIQUE INDEX uq_speakers_server_number ON speakers(server_id, id);
```

### 4.2 필드 정의

| 필드 | 타입 | NULL | 기본값 | 설명 |
|------|------|:----:|--------|------|
| id | INTEGER | N | - | FK/PK → devices.id (CASCADE) |
| speaker_type | ENUM | N | NORMAL | 스피커 유형 (EnumSpeakerType) |
| server_id | INTEGER | Y | NULL | FK → servers.id (SET NULL) |
| description | VARCHAR(500) | Y | NULL | 설명 |

> **Note**: `server_id`는 DB 테이블 및 Create/Update 스키마에서 사용됩니다. Response에서는 `server_id` 대신 `server` 객체로 Server 전체 정보를 제공합니다 (Nested 원칙: created_at, updated_at 제외).

### 4.3 Device Base 필드 (상속)

| 필드 | 설명 | Speaker 용도 |
|------|------|--------------|
| category_device | "speaker" | Polymorphic Discriminator |
| number_device | 장비 번호 | **단말 번호 (예: 2401)** ← NATS의 device_no 통합 |
| group_device | 그룹 번호 | Legacy 호환 |
| name_device | 장비명 | 표시명 (예: "VCS_2401") |
| type_device | IpSpeaker | EnumDeviceType |
| status | 상태 | EnumDeviceStatus |

> **Note**: NATS 메시지의 `device_no` (문자열 "2401")는 Device Base의 `number_device` (정수 2401)로 통합됩니다.

### 4.4 file_groups 테이블 (방송음원 파일풀)

```sql
CREATE TABLE file_groups (
    id SERIAL PRIMARY KEY,
    server_id INTEGER NOT NULL REFERENCES servers(id) ON DELETE CASCADE,

    -- FileGroup 정보
    group_id INTEGER NOT NULL,              -- 방송서버의 파일그룹 ID
    group_name VARCHAR(100) NOT NULL,       -- 그룹명 (예: "화재경보")
    files JSONB,                            -- 파일 목록 (JSONB 배열)

    -- 타임스탬프
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    UNIQUE(server_id, group_id)
);

-- Indexes
CREATE INDEX idx_file_groups_server_id ON file_groups(server_id);
CREATE INDEX idx_file_groups_files ON file_groups USING GIN (files);
```

### 4.5 file_groups 필드 정의

| 필드 | 타입 | NULL | 기본값 | 설명 |
|------|------|:----:|--------|------|
| id | SERIAL | N | AUTO | 고유 식별자 (PK) |
| server_id | INTEGER | N | - | FK → servers.id (CASCADE) |
| group_id | INTEGER | N | - | 방송서버의 파일그룹 ID |
| group_name | VARCHAR(100) | N | - | 그룹명 |
| files | JSONB | Y | NULL | 파일 목록 (JSONB 배열) |
| created_at | TIMESTAMP | N | NOW | 생성 시간 |
| updated_at | TIMESTAMP | N | NOW | 수정 시간 |

### 4.6 files JSONB 포맷

```json
["music01.mp3", "music02.mp3", "music03.mp3"]
```

> **Note**: NATS 메시지의 `file_name` (쉼표 구분 문자열 "music01.mp3,music02.mp3")은 JSONB 배열로 변환하여 저장합니다.

---

## 5. 스키마 정의

### 5.1 Speaker Schemas

```python
# app/schemas/speaker.py

class SpeakerCreate(BaseModel):
    """Speaker 생성 스키마"""
    # Device Base 필드
    number_device: int                # 단말 번호 (NATS device_no 통합, 예: 2401)
    group_device: int = 0
    name_device: str                  # 표시명 (예: "VCS_2401")
    type_device: EnumDeviceType = EnumDeviceType.IpSpeaker
    version: Optional[str] = None
    status: EnumDeviceStatus = EnumDeviceStatus.ACTIVATED

    # Speaker 전용 필드
    speaker_type: EnumSpeakerType = EnumSpeakerType.NORMAL
    server_id: Optional[int] = None   # 방송서버 ID (FK)
    description: Optional[str] = None


class SpeakerUpdate(BaseModel):
    """Speaker 수정 스키마 (PATCH)"""
    # Device Base 필드 (Optional)
    number_device: Optional[int] = None
    group_device: Optional[int] = None
    name_device: Optional[str] = None
    version: Optional[str] = None
    status: Optional[EnumDeviceStatus] = None

    # Speaker 전용 필드 (Optional)
    speaker_type: Optional[EnumSpeakerType] = None
    server_id: Optional[int] = None
    description: Optional[str] = None


class SpeakerResponse(BaseModel):
    """Speaker 응답 스키마"""
    # Device Base 필드
    id: int
    category_device: str = "speaker"
    number_device: int                # 단말 번호 (NATS device_no)
    group_device: int
    name_device: str
    type_device: str
    version: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    # Speaker 전용 필드
    speaker_type: str
    description: Optional[str] = None

    # Nested Server 정보 (server_id 대신 server 객체로 제공)
    server: Optional[ServerNestedResponse] = None

    model_config = ConfigDict(from_attributes=True)


class SpeakerNestedResponse(BaseModel):
    """Speaker Nested 응답 (Event 등에서 사용)"""
    id: int
    category_device: str = "speaker"
    number_device: int                # 단말 번호 (NATS device_no)
    name_device: str
    type_device: str
    status: str
    speaker_type: str

    model_config = ConfigDict(from_attributes=True)
```

### 5.2 FileGroup Schemas

```python
# app/schemas/file_group.py
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class FileGroupCreate(BaseModel):
    """FileGroup 생성 스키마"""
    server_id: int
    group_id: int
    group_name: str
    files: Optional[List[str]] = None  # JSONB: ["file1.mp3", "file2.mp3"]


class FileGroupUpdate(BaseModel):
    """FileGroup 수정 스키마 (PATCH)"""
    group_name: Optional[str] = None
    files: Optional[List[str]] = None


class FileGroupResponse(BaseModel):
    """FileGroup 응답 스키마"""
    id: int
    server_id: int
    group_id: int
    group_name: str
    files: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

### 5.3 ServerNestedResponse (Speaker용)

```python
class ServerNestedResponse(BaseModel):
    """Server Nested 응답 (Speaker에서 사용) - created_at, updated_at 제외"""
    id: int
    category_id: int
    name: str
    status: str
    ip_address: str
    port: int
    hostname: Optional[str] = None
    user_name: Optional[str] = None
    user_password: Optional[str] = None
    cpu_usage: Optional[float] = None
    ram_usage: Optional[float] = None
    disk_usage: Optional[float] = None
    network_throughput: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
```

---

## 6. API Endpoints

### 6.1 Speaker Endpoints

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/devices/speakers` | Speaker 목록 조회 |
| GET | `/api/devices/speakers/{id}` | Speaker 상세 조회 |
| POST | `/api/devices/speakers` | Speaker 생성 |
| PATCH | `/api/devices/speakers/{id}` | Speaker 부분 수정 |
| PUT | `/api/devices/speakers/{id}` | Speaker 전체 수정 |
| DELETE | `/api/devices/speakers/{id}` | Speaker 삭제 |

> **URL 패턴**: GOP_Restful_Api_연동설계.md 섹션 2.2 준수 - `/api/devices/{device-type}`

### 6.2 FileGroup Endpoints

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/file-groups` | FileGroup 목록 조회 |
| GET | `/api/file-groups/{id}` | FileGroup 상세 조회 |
| POST | `/api/file-groups` | FileGroup 생성 |
| PATCH | `/api/file-groups/{id}` | FileGroup 부분 수정 |
| PUT | `/api/file-groups/{id}` | FileGroup 전체 수정 |
| DELETE | `/api/file-groups/{id}` | FileGroup 삭제 |

> **참고**: FileGroup은 Device가 아닌 독립 리소스이므로 `/api/file-groups` 경로 사용

### 6.3 Query Parameters

```
GET /api/devices/speakers?server_id=1&status=ACTIVATED&speaker_type=NORMAL&page=1&limit=20
GET /api/file-groups?server_id=1&page=1&limit=20
```

---

## 7. Response 포맷

### 7.1 Speaker Response

```json
{
  "success": true,
  "message": "Speaker retrieved successfully",
  "data": {
    "id": 101,
    "category_device": "speaker",
    "number_device": 2401,
    "group_device": 0,
    "name_device": "VCS_2401",
    "type_device": "IpSpeaker",
    "version": null,
    "status": "ACTIVATED",
    "created_at": "2026-01-07T10:00:00.000000",
    "updated_at": "2026-01-07T10:00:00.000000",
    "speaker_type": "NORMAL",
    "description": "1구역 스피커",
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
      "cpu_usage": 25.5,
      "ram_usage": 40.2,
      "disk_usage": 55.0,
      "network_throughput": "50MB/s"
    }
  }
}
```

### 7.2 Speaker 목록 Response

```json
{
  "success": true,
  "message": "Speakers retrieved successfully",
  "data": [
    {
      "id": 101,
      "category_device": "speaker",
      "number_device": 2401,
      "group_device": 0,
      "name_device": "VCS_2401",
      "type_device": "IpSpeaker",
      "version": null,
      "status": "ACTIVATED",
      "created_at": "2026-01-07T10:00:00.000000",
      "updated_at": "2026-01-07T10:00:00.000000",
      "speaker_type": "NORMAL",
      "description": "1구역 스피커",
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
        "cpu_usage": 25.5,
        "ram_usage": 40.2,
        "disk_usage": 55.0,
        "network_throughput": "50MB/s"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 35,
    "total_pages": 2
  }
}
```

### 7.3 FileGroup Response

```json
{
  "success": true,
  "message": "FileGroup retrieved successfully",
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

### 7.4 Create Request Body

#### Speaker Create

```json
{
  "number_device": 2401,
  "group_device": 0,
  "name_device": "VCS_2401",
  "type_device": "IpSpeaker",
  "status": "ACTIVATED",
  "speaker_type": "NORMAL",
  "server_id": 1,
  "description": "1구역 스피커"
}
```

#### FileGroup Create

```json
{
  "server_id": 1,
  "group_id": 2,
  "group_name": "화재경보",
  "files": ["music01.mp3", "music02.mp3"]
}
```

---

## 8. 구현 계획

### 8.1 Phase 1: Enum 및 Model

| 순서 | 작업 | 파일 |
|:----:|------|------|
| 1 | EnumDeviceCategory에 SPEAKER 추가 | `app/utils/enums.py` |
| 2 | EnumSpeakerType 추가 | `app/utils/enums.py` |
| 3 | Speaker Model 생성 | `app/models/speaker.py` |
| 4 | FileGroup Model 생성 | `app/models/file_group.py` |
| 5 | Model __init__ 업데이트 | `app/models/__init__.py` |

### 8.2 Phase 2: Schema

| 순서 | 작업 | 파일 |
|:----:|------|------|
| 6 | Speaker Schema 생성 | `app/schemas/speaker.py` |
| 7 | FileGroup Schema 생성 | `app/schemas/file_group.py` |
| 8 | Schema __init__ 업데이트 | `app/schemas/__init__.py` |

### 8.3 Phase 3: Router & CRUD

| 순서 | 작업 | 파일 |
|:----:|------|------|
| 9 | Speaker CRUD 함수 | `app/crud/speaker.py` |
| 10 | FileGroup CRUD 함수 | `app/crud/file_group.py` |
| 11 | Speaker Router | `app/routers/speakers.py` |
| 12 | FileGroup Router | `app/routers/file_groups.py` |
| 13 | Router 등록 | `app/main.py` |

> **Router 등록 시 prefix**:
> - Speaker: `prefix="/api/devices/speakers"` (Device 하위 리소스)
> - FileGroup: `prefix="/api/file-groups"` (독립 리소스)

### 8.4 Phase 4: Device Schema 통합

| 순서 | 작업 | 파일 |
|:----:|------|------|
| 14 | SpeakerNestedResponse를 Device Union에 추가 | `app/schemas/device.py` |
| 15 | Event Response의 device 필드에 Speaker 포함 | `app/schemas/event.py` |

### 8.5 Phase 5: 테스트

| 순서 | 작업 | 파일 |
|:----:|------|------|
| 16 | Speaker Model 테스트 | `tests/test_speaker_model.py` |
| 17 | Speaker API 테스트 | `tests/test_speaker_api.py` |
| 18 | FileGroup API 테스트 | `tests/test_file_group_api.py` |

---

## 9. 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| v1.0 | 2026-01-07 | 초안 작성 |

---

## 부록 A: ERD 다이어그램

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          devices (Base Table)                            │
├─────────────────────────────────────────────────────────────────────────┤
│  id (PK), category_device, number_device, group_device, name_device     │
│  type_device, version, status, created_at, updated_at                   │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │ Joined Table Inheritance
          ┌─────────────┬───────────┼───────────┬─────────────┐
          │             │           │           │             │
          ▼             ▼           ▼           ▼             ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ controllers │ │   sensors   │ │   cameras   │ │  speakers   │ ← NEW
├─────────────┤ ├─────────────┤ ├─────────────┤ ├─────────────┤
│ id (FK/PK)  │ │ id (FK/PK)  │ │ id (FK/PK)  │ │ id (FK/PK)  │
│ ip_address  │ │controller_id│ │ ip_address  │ │speaker_type │
│ ip_port     │ │             │ │ ip_port     │ │ server_id ──┼──┐
│             │ │             │ │ user_name   │ │ description │  │
│             │ │             │ │ user_pwd    │ │             │  │
│             │ │             │ │ urls (JSON) │ │             │  │
│             │ │             │ │ mode        │ │             │  │
│             │ │             │ │ category    │ │             │  │
│ Identity:   │ │ Identity:   │ │ Identity:   │ │ Identity:   │  │
│"controller" │ │ "sensor"    │ │ "camera"    │ │ "speaker"   │  │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘  │
                                                                  │
                    ┌─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────┐     ┌─────────────────────────────────┐
│           servers               │     │         file_groups              │
├─────────────────────────────────┤     ├─────────────────────────────────┤
│ id (PK)                         │◄────│ server_id (FK)                  │
│ category_id                     │     │ id (PK)                         │
│ name                            │     │ group_id                        │
│ status                          │     │ group_name                      │
│ ip_address                      │     │ file_names                      │
│ port                            │     │ created_at, updated_at          │
│ user_name (v2.4)                │     │                                 │
│ user_password (v2.4)            │     │ UNIQUE(server_id, group_id)     │
│ ...                             │     │                                 │
└─────────────────────────────────┘     └─────────────────────────────────┘
```

---

## 부록 B: NATS 메시지 vs DB API 매핑

| NATS 메시지 필드 | DB API 필드 | 설명 |
|------------------|-------------|------|
| `device_id` | `id` (devices) | Device PK (자동 생성) |
| `device_type` | `speaker_type` | Speaker 유형 |
| `device_name` | `name_device` | 장비명 |
| `device_no` | `number_device` | **단말 번호 (통합)** |
| `device_status` | `status` | 장비 상태 |
| `server_id` | `server_id` (FK) | 방송서버 참조 |
| `group_id` | `file_groups.group_id` | 파일그룹 ID |
| `group_name` | `file_groups.group_name` | 파일그룹명 |
| `file_name` | `file_groups.files` | **파일 목록 (JSONB)** |

> **Note**:
> - NATS의 `device_no`는 문자열 ("2401")이지만, DB API의 `number_device`는 정수 (2401)입니다.
> - NATS의 `file_name` (쉼표 구분 문자열 "music01.mp3,music02.mp3")은 DB API의 `files` JSONB 배열 `["music01.mp3", "music02.mp3"]`로 변환됩니다.

---

## 부록 C: 제외 항목 (방송 제어)

아래 NATS 메시지 명령은 DB API 범위에서 제외됩니다:

| 명령 | 설명 | 제외 사유 |
|------|------|-----------|
| `BROADCAST_FILE_START` | 파일 방송 시작 | 제어 명령 |
| `BROADCAST_TTS_START` | TTS 방송 시작 | 제어 명령 |
| `BROADCAST_DEVICE_SOURCE_START` | 음원/마이크 방송 | 제어 명령 |
| `BROADCAST_SERVER_STATUS_GET` | 서버 상태 조회 | Server API 대체 |

---

**문서 종료**
