# PRD: Event Mapping Speaker API

**문서 버전**: v1.0
**작성일**: 2026-01-12
**상태**: Completed
**관련 문서**:
- GOP_Restful_Api_연동설계.md v2.6
- GOP_스키마_전체.md v1.8
- PRD_CameraEventMapping_Refactoring.md
- PRD_Speaker_Device.md

---

## 1. 개요

### 1.1 목적

본 문서는 이벤트 발생 시 스피커 방송 액션을 자동으로 실행하는 **Event Mapping Speaker API**의 설계 및 구현 요구사항을 정의합니다.

### 1.2 배경

현재 GOP 시스템에서 EventMapping은 다양한 Action 타입(Camera, Speaker, 3rd Party)의 **Base 노드**로 설계되어 있습니다.

- ✅ **EventMappingCamera**: 이벤트 발생 시 PTZ 카메라 프리셋 이동 (v2.4 구현 완료)
- ❌ **EventMappingSpeaker**: 이벤트 발생 시 스피커 방송 재생 (본 PRD 대상)

침입 탐지/장애 이벤트 발생 시 자동 경보 방송 기능을 통해 현장 대응 시간을 단축하고 보안 효과를 높이고자 합니다.

### 1.3 범위

| 구분 | 내용 |
|------|------|
| In Scope | event_mapping_speakers 테이블 설계, CRUD API, Swagger 문서화 |
| Out of Scope | 실제 방송 실행 로직 (외부 Speaker API 서버에서 처리), 실시간 방송 제어 |

---

## 2. 아키텍처

### 2.1 이벤트-스피커 연동 흐름

```
┌─────────────────┐
│  Detection/     │
│  Malfunction    │     ┌─────────────────────────────────┐
│  Event 발생     │     │     EventMapping (Base Node)    │
└────────┬────────┘     │  - device_group_id (FK)         │
         │              │  - category_event_mapping       │
         ▼              │  - status                       │
┌─────────────────┐     └───────────────┬─────────────────┘
│ Device의        │                     │
│ DeviceGroup     │◄────────────────────┘
│ 목록 조회       │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EventMapping Actions                          │
├────────────────────────┬────────────────────────────────────────┤
│  EventMappingCamera    │   EventMappingSpeaker (신규)            │
│  - camera_id           │   - speaker_id                          │
│  - target_preset_id    │   - file_group_id                       │
│  - home_preset_id      │   - repeat_count                        │
│  - delay_time          │   - is_enable                           │
│  - priority            │   - priority                            │
└────────────────────────┴────────────────────────────────────────┘
         │                          │
         ▼                          ▼
┌─────────────────┐     ┌─────────────────────────────────────────┐
│  PTZ 프리셋     │     │  Speaker API 서버                        │
│  이동 실행      │     │  (FileGroup 음원 재생 요청)               │
└─────────────────┘     └─────────────────────────────────────────┘
```

### 2.2 관계 다이어그램

```
┌─────────────────┐     ┌─────────────────────────┐     ┌─────────────────┐
│  event_mappings │     │  event_mapping_speakers │     │    speakers     │
├─────────────────┤     ├─────────────────────────┤     ├─────────────────┤
│ id (PK)         │◄────│ event_mapping_id (FK)   │     │ id (PK)         │
│ name_event      │     │ CASCADE DELETE          │     │ speaker_type    │
│ device_group_id │     │                         │     │ server_id (FK)  │
│ status          │     │ speaker_id (FK) ────────┼────►│                 │
└─────────────────┘     │ SET NULL                │     └─────────────────┘
                        │                         │
                        │ file_group_id (FK) ─────┼────►┌─────────────────┐
                        │ SET NULL                │     │   file_groups   │
                        │                         │     ├─────────────────┤
                        │ repeat_count            │     │ id (PK)         │
                        │ is_enable               │     │ server_id (FK)  │
                        │ priority                │     │ group_id        │
                        │ created_at              │     │ group_name      │
                        │ updated_at              │     │ files (JSONB)   │
                        └─────────────────────────┘     └─────────────────┘
```

---

## 3. 데이터베이스 스키마

### 3.1 event_mapping_speakers 테이블

> **설계 원칙**: EventMappingCamera와 동일한 패턴 적용
> - 실제 방송 제어(volume, repeat 등)는 외부 Speaker API 서버(NATS)에서 처리
> - DB API는 "어떤 이벤트 발생 시 → 어떤 스피커 + 어떤 음원"의 **매핑 정보만 관리**

#### PostgreSQL CREATE TABLE

```sql
CREATE TABLE event_mapping_speakers (
    id SERIAL PRIMARY KEY,
    event_mapping_id INTEGER NOT NULL REFERENCES event_mappings(id) ON DELETE CASCADE,
    speaker_id INTEGER REFERENCES speakers(id) ON DELETE SET NULL,
    file_group_id INTEGER REFERENCES file_groups(id) ON DELETE SET NULL,
    repeat_count INTEGER NOT NULL DEFAULT 1 CHECK (repeat_count >= 1),
    is_enable BOOLEAN NOT NULL DEFAULT TRUE,
    priority INTEGER,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_event_mapping_speakers_id ON event_mapping_speakers(id);
CREATE INDEX idx_event_mapping_speakers_event_mapping_id ON event_mapping_speakers(event_mapping_id);
CREATE INDEX idx_event_mapping_speakers_speaker_id ON event_mapping_speakers(speaker_id);
CREATE INDEX idx_event_mapping_speakers_file_group_id ON event_mapping_speakers(file_group_id);
```

#### 필드 정의

| 필드명 | 타입 | NULL 허용 | 기본값 | 설명 |
|--------|------|-----------|--------|------|
| id | SERIAL | NO | AUTO | 고유 식별자 (PK) |
| event_mapping_id | INTEGER | NO | - | FK → event_mappings.id (CASCADE DELETE) |
| speaker_id | INTEGER | YES | NULL | FK → speakers.id (SET NULL on delete) |
| file_group_id | INTEGER | YES | NULL | FK → file_groups.id (SET NULL on delete) |
| repeat_count | INTEGER | NO | 1 | 방송 반복 횟수 (1 이상) |
| is_enable | BOOLEAN | NO | TRUE | 활성화 여부 |
| priority | INTEGER | YES | NULL | 실행 우선순위 (Optional) |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 생성 시간 |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 수정 시간 |

#### 제외된 필드 (외부 Speaker API 서버 관할)

| 필드 | 제외 사유 |
|------|-----------|
| volume | 방송 볼륨은 Speaker 장비 또는 Server 설정에서 관리 |
| delay_time | 스피커 방송에는 지연 시간 불필요 (카메라 PTZ 이동과 다름) |

#### FK Behavior

| FK | ON DELETE | 설명 |
|----|-----------|------|
| event_mapping_id → event_mappings.id | CASCADE | EventMapping 삭제 시 함께 삭제 |
| speaker_id → speakers.id | SET NULL | Speaker 삭제 시 연결만 해제 |
| file_group_id → file_groups.id | SET NULL | FileGroup 삭제 시 연결만 해제 |

---

## 4. API 설계

### 4.1 Endpoint 목록

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/integrations/event-mappings/{mapping_id}/speakers` | 목록 조회 |
| GET | `/api/integrations/event-mappings/{mapping_id}/speakers/{config_id}` | 단일 조회 |
| POST | `/api/integrations/event-mappings/{mapping_id}/speakers` | 생성 |
| PATCH | `/api/integrations/event-mappings/{mapping_id}/speakers/{config_id}` | 부분 수정 |
| PUT | `/api/integrations/event-mappings/{mapping_id}/speakers/{config_id}` | 전체 수정 |
| DELETE | `/api/integrations/event-mappings/{mapping_id}/speakers/{config_id}` | 삭제 |

---

### 4.2 EventMappingSpeaker 목록 조회

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
          "id": 101,
          "number_device": 1,
          "group_device": 1,
          "name_device": "IP-Speaker-01",
          "type_device": "IpSpeaker",
          "version": "1.0.0",
          "status": "ACTIVATED",
          "speaker_type": "NORMAL",
          "server_id": 1,
          "description": "GOP 1초소 경보 스피커",
          "geolocation": {
            "location": "GOP 1초소 정문",
            "latitude": 38.1234,
            "longitude": 127.5678,
            "altitude": 245.5
          },
          "device_groups": [
            { "id": 1, "name": "1구역 센서 그룹", "description": "1구역 감시 장비", "device_count": 5 }
          ]
        },
        "file_group": {
          "id": 5,
          "server_id": 1,
          "group_id": 2,
          "group_name": "침입경보",
          "files": ["intrusion_alert_01.mp3", "intrusion_alert_02.mp3"]
        },
        "repeat_count": 3,
        "is_enable": true,
        "priority": 1,
        "created_at": "2026-01-12T10:00:00.000+09:00",
        "updated_at": "2026-01-12T10:00:00.000+09:00"
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

---

### 4.3 EventMappingSpeaker 단일 조회

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
      "id": 101,
      "number_device": 1,
      "group_device": 1,
      "name_device": "IP-Speaker-01",
      "type_device": "IpSpeaker",
      "version": "1.0.0",
      "status": "ACTIVATED",
      "speaker_type": "NORMAL",
      "server_id": 1,
      "description": "GOP 1초소 경보 스피커",
      "geolocation": null,
      "device_groups": []
    },
    "file_group": {
      "id": 5,
      "server_id": 1,
      "group_id": 2,
      "group_name": "침입경보",
      "files": ["intrusion_alert_01.mp3", "intrusion_alert_02.mp3"]
    },
    "repeat_count": 3,
    "is_enable": true,
    "priority": 1,
    "created_at": "2026-01-12T10:00:00.000+09:00",
    "updated_at": "2026-01-12T10:00:00.000+09:00"
  }
}
```

---

### 4.4 EventMappingSpeaker 생성

**Endpoint**: `POST /api/integrations/event-mappings/{mapping_id}/speakers`

**Path Parameters**:
- `mapping_id` (int, required): EventMapping ID

**Request Body**:

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| speaker_id | integer | Y | 대상 스피커 ID |
| file_group_id | integer | N | 재생할 파일 그룹 ID |
| repeat_count | integer | N | 반복 횟수 (기본값: 1) |
| is_enable | boolean | N | 활성화 여부 (기본값: true) |
| priority | integer | N | 실행 우선순위 (Optional) |

**Request Example**:
```http
POST /api/integrations/event-mappings/10/speakers HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "speaker_id": 101,
  "file_group_id": 5,
  "repeat_count": 3,
  "is_enable": true,
  "priority": 1
}
```

**Response Example** (201 Created):
```json
{
  "success": true,
  "message": "Event mapping speaker created successfully",
  "data": {
    "id": 1,
    "event_mapping_id": 10,
    "speaker": {
      "id": 101,
      "number_device": 1,
      "group_device": 1,
      "name_device": "IP-Speaker-01",
      "type_device": "IpSpeaker",
      "version": "1.0.0",
      "status": "ACTIVATED",
      "speaker_type": "NORMAL",
      "server_id": 1,
      "description": "GOP 1초소 경보 스피커",
      "geolocation": null,
      "device_groups": []
    },
    "file_group": {
      "id": 5,
      "server_id": 1,
      "group_id": 2,
      "group_name": "침입경보",
      "files": ["intrusion_alert_01.mp3", "intrusion_alert_02.mp3"]
    },
    "repeat_count": 3,
    "is_enable": true,
    "priority": 1,
    "created_at": "2026-01-12T10:00:00.000+09:00",
    "updated_at": "2026-01-12T10:00:00.000+09:00"
  }
}
```

**Error Responses**:

404 Not Found (EventMapping):
```json
{
  "success": false,
  "message": "Event mapping not found with id=999"
}
```

404 Not Found (Speaker):
```json
{
  "success": false,
  "message": "Speaker not found with id=999"
}
```

404 Not Found (FileGroup):
```json
{
  "success": false,
  "message": "FileGroup not found with id=999"
}
```

422 Validation Error (repeat_count):
```json
{
  "success": false,
  "message": "Validation error",
  "errors": [
    {
      "field": "repeat_count",
      "message": "repeat_count must be at least 1"
    }
  ]
}
```

---

### 4.5 EventMappingSpeaker 수정 (부분)

**Endpoint**: `PATCH /api/integrations/event-mappings/{mapping_id}/speakers/{config_id}`

**Path Parameters**:
- `mapping_id` (int, required): EventMapping ID
- `config_id` (int, required): EventMappingSpeaker ID

**Request Body** (모든 필드 Optional):

| 필드 | 타입 | 설명 |
|------|------|------|
| speaker_id | integer | 대상 스피커 ID |
| file_group_id | integer | 재생할 파일 그룹 ID |
| repeat_count | integer | 반복 횟수 |
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
    "speaker": { ... },
    "file_group": { ... },
    "repeat_count": 5,
    "is_enable": false,
    "priority": 1,
    "created_at": "2026-01-12T10:00:00.000+09:00",
    "updated_at": "2026-01-12T11:00:00.000+09:00"
  }
}
```

---

### 4.6 EventMappingSpeaker 수정 (전체)

**Endpoint**: `PUT /api/integrations/event-mappings/{mapping_id}/speakers/{config_id}`

**Path Parameters**:
- `mapping_id` (int, required): EventMapping ID
- `config_id` (int, required): EventMappingSpeaker ID

**Request Body**:

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| speaker_id | integer | Y | 대상 스피커 ID |
| file_group_id | integer | N | 재생할 파일 그룹 ID |
| repeat_count | integer | Y | 반복 횟수 |
| is_enable | boolean | Y | 활성화 여부 |
| priority | integer | N | 실행 우선순위 |

**Request Example**:
```http
PUT /api/integrations/event-mappings/10/speakers/1 HTTP/1.1
Host: control-service.company.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "speaker_id": 102,
  "file_group_id": 6,
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
    "speaker": { ... },
    "file_group": { ... },
    "repeat_count": 2,
    "is_enable": true,
    "priority": 2,
    "created_at": "2026-01-12T10:00:00.000+09:00",
    "updated_at": "2026-01-12T12:00:00.000+09:00"
  }
}
```

---

### 4.7 EventMappingSpeaker 삭제

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
  "message": "Event mapping speaker deleted successfully",
  "data": null
}
```

**Error Response** (404 Not Found):
```json
{
  "success": false,
  "message": "Event mapping speaker not found with id=999"
}
```

---

## 5. Pydantic 스키마

### 5.1 Request Schemas

```python
from pydantic import BaseModel, Field
from typing import Optional


class EventMappingSpeakerCreate(BaseModel):
    """EventMappingSpeaker 생성 스키마"""
    speaker_id: int = Field(..., description="대상 스피커 ID")
    file_group_id: Optional[int] = Field(None, description="재생할 파일 그룹 ID")
    repeat_count: int = Field(1, ge=1, description="반복 횟수")
    is_enable: bool = Field(True, description="활성화 여부")
    priority: Optional[int] = Field(None, description="실행 우선순위")

    class Config:
        json_schema_extra = {
            "example": {
                "speaker_id": 101,
                "file_group_id": 5,
                "repeat_count": 3,
                "is_enable": True,
                "priority": 1
            }
        }


class EventMappingSpeakerUpdate(BaseModel):
    """EventMappingSpeaker 부분 수정 스키마 (PATCH)"""
    speaker_id: Optional[int] = Field(None, description="대상 스피커 ID")
    file_group_id: Optional[int] = Field(None, description="재생할 파일 그룹 ID")
    repeat_count: Optional[int] = Field(None, ge=1, description="반복 횟수")
    is_enable: Optional[bool] = Field(None, description="활성화 여부")
    priority: Optional[int] = Field(None, description="실행 우선순위")


class EventMappingSpeakerReplace(BaseModel):
    """EventMappingSpeaker 전체 수정 스키마 (PUT)"""
    speaker_id: int = Field(..., description="대상 스피커 ID")
    file_group_id: Optional[int] = Field(None, description="재생할 파일 그룹 ID")
    repeat_count: int = Field(..., ge=1, description="반복 횟수")
    is_enable: bool = Field(..., description="활성화 여부")
    priority: Optional[int] = Field(None, description="실행 우선순위")
```

### 5.2 Response Schemas

```python
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List


class SpeakerNestedResponse(BaseModel):
    """EventMappingSpeaker Response에 포함되는 Speaker Nested 객체"""
    id: int
    number_device: int
    group_device: int
    name_device: str
    type_device: str
    version: Optional[str]
    status: str
    speaker_type: str
    server_id: Optional[int]
    description: Optional[str]
    geolocation: Optional[dict]
    device_groups: List[dict] = []


class FileGroupNestedResponse(BaseModel):
    """EventMappingSpeaker Response에 포함되는 FileGroup Nested 객체"""
    id: int
    server_id: int
    group_id: int
    group_name: str
    files: Optional[List[str]]


class EventMappingSpeakerResponse(BaseModel):
    """EventMappingSpeaker 응답 스키마"""
    id: int
    event_mapping_id: int
    speaker: Optional[SpeakerNestedResponse]
    file_group: Optional[FileGroupNestedResponse]
    repeat_count: int
    is_enable: bool
    priority: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

---

## 6. SQLAlchemy 모델

```python
from sqlalchemy import Column, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class EventMappingSpeaker(Base):
    """EventMappingSpeaker 모델 - 이벤트 매핑 스피커 액션"""
    __tablename__ = "event_mapping_speakers"

    id = Column(Integer, primary_key=True, index=True)
    event_mapping_id = Column(
        Integer,
        ForeignKey("event_mappings.id", ondelete="CASCADE"),
        nullable=False
    )
    speaker_id = Column(
        Integer,
        ForeignKey("speakers.id", ondelete="SET NULL"),
        nullable=True
    )
    file_group_id = Column(
        Integer,
        ForeignKey("file_groups.id", ondelete="SET NULL"),
        nullable=True
    )
    repeat_count = Column(Integer, nullable=False, default=1)
    is_enable = Column(Boolean, nullable=False, default=True)
    priority = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    event_mapping = relationship("EventMapping", back_populates="speakers")
    speaker = relationship("Speaker", back_populates="event_mapping_speakers")
    file_group = relationship("FileGroup", back_populates="event_mapping_speakers")
```

---

## 7. 사용 시나리오

### 7.1 시나리오 1: 침입 탐지 시 자동 경보 방송

1. **설정 단계**:
   - EventMapping 생성 (device_group_id = 1, category = FENCE_SENSOR_ONLY)
   - EventMappingSpeaker 생성:
     - speaker_id = 101 (현장 스피커)
     - file_group_id = 5 (침입경보 음원)
     - repeat_count = 5

2. **실행 단계**:
   - Fence 센서에서 DetectionEvent 발생
   - DeviceGroup 1에 매핑된 EventMapping 조회
   - EventMappingSpeaker 실행 → 침입경보 5회 반복 재생

### 7.2 시나리오 2: 장애 발생 시 경고 방송

1. **설정 단계**:
   - EventMapping 생성 (device_group_id = 2, category = MULTI_SENSOR_ONLY)
   - EventMappingSpeaker 생성:
     - speaker_id = 102 (관제실 스피커)
     - file_group_id = 6 (장애경고 음원)
     - repeat_count = 2

2. **실행 단계**:
   - MalfunctionEvent 발생
   - 장애경고 방송 2회 반복 실행

### 7.3 시나리오 3: 다중 스피커 동시 방송

1. **설정 단계**:
   - 동일 EventMapping에 여러 EventMappingSpeaker 생성:
     - Speaker A: priority = 1, repeat_count = 3
     - Speaker B: priority = 2, repeat_count = 2
     - Speaker C: priority = 3, repeat_count = 1

2. **실행 단계**:
   - 이벤트 발생 시 priority 순서대로 방송 실행
   - 동시 또는 순차 실행은 Speaker API 서버에서 결정

---

## 8. 구현 체크리스트

### 8.1 데이터베이스
- [ ] event_mapping_speakers 테이블 생성 (Alembic 마이그레이션)
- [ ] 인덱스 생성 확인
- [ ] FK Constraint 확인 (CASCADE, SET NULL)

### 8.2 모델
- [ ] EventMappingSpeaker SQLAlchemy 모델 작성
- [ ] EventMapping 모델에 `speakers` relationship 추가
- [ ] Speaker 모델에 `event_mapping_speakers` relationship 추가
- [ ] FileGroup 모델에 `event_mapping_speakers` relationship 추가

### 8.3 스키마
- [ ] EventMappingSpeakerCreate 스키마 작성
- [ ] EventMappingSpeakerUpdate 스키마 작성
- [ ] EventMappingSpeakerReplace 스키마 작성
- [ ] EventMappingSpeakerResponse 스키마 작성
- [ ] SpeakerNestedResponse 스키마 작성
- [ ] FileGroupNestedResponse 스키마 작성

### 8.4 API Router
- [ ] GET /event-mappings/{mapping_id}/speakers (목록)
- [ ] GET /event-mappings/{mapping_id}/speakers/{config_id} (단일)
- [ ] POST /event-mappings/{mapping_id}/speakers (생성)
- [ ] PATCH /event-mappings/{mapping_id}/speakers/{config_id} (부분 수정)
- [ ] PUT /event-mappings/{mapping_id}/speakers/{config_id} (전체 수정)
- [ ] DELETE /event-mappings/{mapping_id}/speakers/{config_id} (삭제)

### 8.5 테스트
- [ ] 단위 테스트 작성
- [ ] 통합 테스트 작성
- [ ] API 문서 (/docs, /redoc) 확인

### 8.6 문서 업데이트
- [ ] GOP_Restful_Api_연동설계.md 업데이트 (7.4절 추가)
- [ ] GOP_스키마_전체.md 업데이트 (6.3절 추가)

---

## 9. 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| v1.0 | 2026-01-12 | 초기 문서 작성 |

---

**문서 종료**
