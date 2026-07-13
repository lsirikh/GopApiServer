# PRD: EventMapping 기반 Action 연동 아키텍처 리팩토링

**문서 버전**: v2.1
**작성일**: 2026-01-07
**작성자**: Claude AI
**상태**: Draft
**기준 API 버전**: v2.3

---

## 1. 개요

### 1.1 목적

현재 `CameraEventMapping` 및 `CameraEventPreset` 구조의 문제점을 분석하고, `EventMapping`을 **다양한 Action 타입의 Base 노드**로 활용하는 확장 가능한 아키텍처로 리팩토링합니다.

### 1.2 핵심 아키텍처 원칙

> **EventMapping은 이벤트 연동을 위한 Base(부모) 노드입니다.**
>
> EventMapping을 기반으로 다양한 Action 타입을 연동할 수 있습니다:
> - **Camera Action**: PTZ 카메라 프리셋 이동, 화면 전환
> - **Speaker Action**: 방송 장비 음성 송출
> - **3rd Party Action**: 외부 시스템 API 호출, 알림 전송

따라서 EventMapping API에 `include_cameras`와 같은 특정 타입에 종속된 파라미터를 사용하지 않습니다.
대신 각 Action 타입별로 **독립적인 하위 리소스 API**를 제공합니다.

### 1.3 배경

#### 현재 문제점

| 구분 | 문제점 | 영향 |
|------|--------|------|
| **1. 명명 불일치** | `CameraEventPreset`는 실제 프리셋이 아닌 "카메라 연동 설정"임 | 개발자 혼란, 실제 `CameraPreset`과 이름 충돌 |
| **2. group_event 레거시** | `CameraEventMapping.group_event`가 아직 VARCHAR(string) 사용 | `EventMapping.device_group_id`(FK)와 불일치 |
| **3. cam_id 비정규화** | `CameraEventPreset.cam_id`가 cameras 테이블과 FK 관계 없음 | 참조 무결성 없음, Camera 삭제 시 고아 데이터 |
| **4. category 역할 불명확** | `CameraEventPreset.category` VARCHAR - 역할 불분명 | 무엇을 나타내는지 알 수 없음 |
| **5. preset_id 타입 불일치** | `CameraEventPreset.preset_id` VARCHAR - 실제 preset과 연결 안됨 | 정수 ID와 문자열 혼용 |
| **6. URL 구조 분리** | `url_live`, `url_record` 별도 컬럼 | Camera 자체에서 관리해야 할 속성 |
| **7. 계층 구조 부재** | EventMapping → CameraEventMapping 관계 없음 | 논리적으로 연결되어야 할 데이터가 독립적 |
| **8. 중복 시간 설정** | `touring_time`, `preset_time`이 `CameraPreset.touring_time`과 중복 | 불필요한 데이터 중복 |

#### 참고 모델: CameraPreset 구조

```
Camera (1) ─────────────▶ CameraPreset (N) ─────────────▶ ROI (N) ─────────────▶ XyPoint (N)
  │                           │                              │                       │
  │ FK: camera_id             │ FK: preset_id                │ FK: roi_id            │
  │ CASCADE DELETE            │ CASCADE DELETE               │ CASCADE DELETE        │
  │                           │                              │                       │
  └─ 명확한 소유 관계          └─ 명확한 소유 관계            └─ 명확한 소유 관계      │
```

**장점**:
- 명확한 계층 구조 (Parent → Child → Grandchild)
- FK를 통한 참조 무결성
- CASCADE DELETE로 자동 정리
- Nested Response 패턴 적용

---

## 2. 현재 구조 분석

### 2.1 현재 ERD

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│ 현재 구조 (문제점 많음)                                                            │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  ┌─────────────────────┐                    ┌─────────────────────────────┐       │
│  │  CameraEventMapping │                    │    CameraEventPreset        │       │
│  ├─────────────────────┤                    ├─────────────────────────────┤       │
│  │ id (PK)             │◀── mapping_id ────│ id (PK)                      │       │
│  │ name_event          │                    │ mapping_id (FK)              │       │
│  │ group_event (!)     │ ← VARCHAR, not FK  │ cam_id (!) ← FK 없음         │       │
│  │ category_event      │                    │ url_live                     │       │
│  │ description         │                    │ url_record                   │       │
│  │ status              │                    │ category (!) ← 역할 불명     │       │
│  │ created_at          │                    │ preset_id (!) ← VARCHAR      │       │
│  │ updated_at          │                    │ preset_time                  │       │
│  └─────────────────────┘                    │ home_preset                  │       │
│                                             │ preset_time                  │       │
│        ↓                                    └─────────────────────────────┘       │
│    EventMapping과의                                                               │
│    관계 없음!                                                                      │
│                                                                                   │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 현재 모델 (app/models/integration.py)

```python
class CameraEventMapping(Base):
    __tablename__ = "camera_event_mappings"

    id = Column(Integer, primary_key=True)
    name_event = Column(String(200), nullable=False)
    group_event = Column(String(100), nullable=False)  # ❌ VARCHAR, not FK
    category_event = Column(SQLEnum(EnumCategoryEvent))
    description = Column(String(500))
    status = Column(Boolean, default=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    camera_presets = relationship("CameraEventPreset", back_populates="mapping")


class CameraEventPreset(Base):
    __tablename__ = "camera_event_presets"

    id = Column(Integer, primary_key=True)
    mapping_id = Column(Integer, ForeignKey("camera_event_mappings.id"))
    cam_id = Column(Integer)  # ❌ FK 없음
    url_live = Column(String(500))  # ❌ Camera에서 관리해야 함
    url_record = Column(String(500))  # ❌ Camera에서 관리해야 함
    category = Column(String(20))  # ❌ 역할 불명확
    preset_id = Column(String(50))  # ❌ VARCHAR
    preset_time = Column(Integer, default=0)  # ❌ CameraPreset.touring_time과 중복
    home_preset = Column(Integer, default=0)
    home_time = Column(Integer, default=0)
```

### 2.3 현재 스키마 (app/schemas/integration.py)

```python
class CameraEventPresetCreate(BaseModel):
    cam_id: int
    urls: Optional[CameraUrls] = None  # url_live, url_record wrapping
    category: str  # ❌ 역할 불명확
    preset_id: Optional[str] = None  # ❌ 왜 문자열?
    preset_time: int = 0
    home_preset: int = 0
    home_time: int = 0


class CameraEventMappingCreate(BaseModel):
    name_event: str
    group_event: str  # ❌ device_group_id여야 함
    category_event: str
    description: Optional[str] = None
    status: bool = True
    camera_presets: List[CameraEventPresetCreate] = []
```

---

## 3. 설계 결정사항

### 3.1 제거/변경 대상 필드 분석

#### touring_time 제거, delay_time 신규 정의

| 필드 | 현재 위치 | 문제점 | 결정 |
|------|-----------|--------|------|
| `touring_time` | CameraEventPreset | `CameraPreset.touring_time`과 중복 | **제거** - CameraPreset에서 참조 |
| `home_time` | CameraEventPreset | 네이밍 불명확 | **→ `delay_time`으로 변경** |

**이유**:
- `CameraPreset.touring_time`은 "Home → 해당 프리셋 이동 시간"으로 이미 정의됨
- 이벤트 연동 시 이동 시간은 target_preset에서 가져오면 됨
- `delay_time`은 "target_preset 도착 후 대기하는 시간"을 의미 (홈 복귀 전 대기)

#### URL 제거 및 Camera.urls JSONB 통합

| 현재 | 개선 방향 | 비고 |
|------|-----------|------|
| `CameraEventPreset.url_live` | **제거** | Camera.urls에서 관리 |
| `CameraEventPreset.url_record` | **제거** | Camera.urls에서 관리 |
| `Camera.rtsp_uri` | **제거** | Camera.urls.streams.rtsp로 통합 |
| `Camera.rtsp_port` | **제거** | Camera.urls.streams.rtsp에 포함 |

> **참고**: Camera URLs JSONB 통합에 대한 상세 내용은 **[PRD_Camera_Urls_JsonB.md](PRD_Camera_Urls_JsonB.md)** 참조

**Camera.urls JSONB 구조**:

```json
{
  "homepage": { "url": "https://192.168.0.10/" },
  "onvif": { "device_service": "http://192.168.0.10:8000/onvif/device_service" },
  "streams": {
    "rtsp": {
      "main": "rtsp://192.168.0.10:554/Streaming/Channels/101",
      "sub": "rtsp://192.168.0.10:554/Streaming/Channels/102"
    },
    "webrtc": { "main": "https://192.168.0.10/webrtc/main" },
    "hls": { "main": "https://192.168.0.10/hls/live.m3u8" }
  },
  "snapshot": { "ch1": "http://192.168.0.10/cgi-bin/snapshot.cgi" }
}
```

#### priority 필드 분석

**priority가 필요한 상황**:

| 상황 | 설명 | 필요 여부 |
|------|------|-----------|
| **순차 PTZ 이동** | 1번 카메라 이동 완료 후 2번 카메라 이동 | 가능성 있음 |
| **화면 표시 순서** | 멀티뷰어에서 우선 표시할 카메라 | 가능성 있음 |
| **리소스 제한** | 동시 스트림 수 제한 시 우선순위 | 가능성 있음 |
| **현재 시스템** | 명확한 요구사항 없음 | 불필요 |

**결정**: **Optional로 유지** (기본값 0, 필요 시 사용)

---

## 4. 개선 방안: 다중 Action 타입 지원 아키텍처

### 4.1 핵심 아이디어

> **EventMapping = Base Node for Multiple Action Types**

1. **EventMapping은 Base 노드**: 이벤트 연동의 공통 설정 (이벤트 소스, 카테고리 등)
2. **Action 타입별 하위 테이블**: 각 Action 타입은 독립적인 테이블로 분리
   - `EventMappingCamera`: 카메라 프리셋 액션
   - `EventMappingSpeaker`: 방송 장비 액션 (향후)
   - `EventMappingExternal`: 3rd Party 액션 (향후)
3. **타입별 독립 API**: `/api/integrations/event-mappings/{id}/cameras`, `/api/integrations/event-mappings/{id}/speakers` 등
4. **확장성**: 새로운 Action 타입 추가 시 기존 구조에 영향 없음

### 4.2 개념적 아키텍처

```
                              ┌─────────────────────────────────────────────────────┐
                              │                   EventMapping                       │
                              │            (이벤트 연동 Base Node)                    │
                              │  - 이벤트 소스 (DeviceGroup)                          │
                              │  - 이벤트 카테고리 (detection/malfunction/connection) │
                              │  - 상태 (활성화/비활성화)                              │
                              └────────────────────┬────────────────────────────────┘
                                                   │
                    ┌──────────────────────────────┼──────────────────────────────┐
                    │                              │                              │
                    ▼                              ▼                              ▼
       ┌────────────────────────┐    ┌────────────────────────┐    ┌────────────────────────┐
       │  EventMappingCamera    │    │  EventMappingSpeaker   │    │  EventMappingExternal  │
       │  (카메라 프리셋 액션)    │    │  (방송 장비 액션)        │    │  (3rd Party 액션)       │
       │                        │    │                        │    │                        │
       │  - camera_id (FK)      │    │  - speaker_id (FK)     │    │  - endpoint_url        │
       │  - target_preset_id    │    │  - message_template_id │    │  - http_method         │
       │  - home_preset_id      │    │  - volume              │    │  - payload_template    │
       │  - delay_time          │    │  - repeat_count        │    │  - auth_type           │
       │  - priority            │    │  - priority            │    │  - priority            │
       └────────────────────────┘    └────────────────────────┘    └────────────────────────┘
                    │                              │                              │
                    ▼                              ▼                              ▼
            Camera/CameraPreset           Speaker/MessageTemplate          External System
```

### 4.3 새로운 ERD (Camera Action 구현)

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ 새로운 구조 (CameraPreset 패턴 적용, 간소화)                                               │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  ┌───────────────────┐                                                                   │
│  │    DeviceGroup    │                                                                   │
│  ├───────────────────┤                                                                   │
│  │ id (PK)           │◀────────────────────────────────────────────────────────┐        │
│  │ name              │                                                          │        │
│  └───────────────────┘                                                          │        │
│                                                                                  │        │
│  ┌───────────────────┐       1:N        ┌─────────────────────────────┐         │        │
│  │   EventMapping    │─────────────────▶│   EventMappingCamera        │         │        │
│  ├───────────────────┤                  ├─────────────────────────────┤         │        │
│  │ id (PK)           │                  │ id (PK)                      │         │        │
│  │ name_event        │                  │ event_mapping_id (FK)        │         │        │
│  │ device_group_id   │──────────────────│ camera_id (FK)───────────────│──┐      │        │
│  │ category_event    │                  │ target_preset_id (FK)────────│──│─┐    │        │
│  │ description       │                  │ home_preset_id (FK)──────────│──│─│─┐  │        │
│  │ status            │                  │ delay_time                   │  │ │ │  │        │
│  │ created_at        │                  │ is_enable                    │  │ │ │  │        │
│  │ updated_at        │                  │ priority (Optional)          │  │ │ │  │        │
│  └───────────────────┘                  │ created_at                   │  │ │ │  │        │
│                                         │ updated_at                   │  │ │ │  │        │
│                                         └─────────────────────────────┘  │ │ │  │        │
│                                                                           │ │ │  │        │
│                                                        ┌──────────────────┘ │ │  │        │
│  ┌───────────────────┐                                 │  ┌─────────────────┘ │  │        │
│  │     Camera        │◀────────────────────────────────┘  │  ┌────────────────┘  │        │
│  ├───────────────────┤                                    │  │                   │        │
│  │ id (PK)           │                                    │  │                   │        │
│  │ name_device       │                                    │  │                   │        │
│  │ ...               │                                    │  │                   │        │
│  │ (streaming_urls)  │ ← 향후 확장                         │  │                   │        │
│  └───────────────────┘                                    │  │                   │        │
│          │                                                │  │                   │        │
│          │ 1:N                                            ▼  ▼                   │        │
│          ▼                                         ┌─────────────────────┐       │        │
│  ┌───────────────────┐                             │   CameraPreset      │       │        │
│  │   CameraPreset    │                             │   (기존 테이블)      │       │        │
│  ├───────────────────┤                             │                     │       │        │
│  │ id (PK)           │◀────────────────────────────│ touring_time 참조    │       │        │
│  │ camera_id (FK)    │                             └─────────────────────┘       │        │
│  │ preset_index      │                                                           │        │
│  │ preset_name       │                                                           │        │
│  │ touring_time      │ ← 이동 시간은 여기서 참조                                   │        │
│  └───────────────────┘                                                           │        │
│                                                                                  │        │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 테이블 설계

#### event_mapping_cameras (새 테이블)

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| `id` | SERIAL | PK | 고유 식별자 |
| `event_mapping_id` | INTEGER | FK → event_mappings.id, NOT NULL, CASCADE | 소속 이벤트 매핑 |
| `camera_id` | INTEGER | FK → cameras.id, SET NULL | 대상 카메라 |
| `target_preset_id` | INTEGER | FK → camera_presets.id, SET NULL | 이벤트 발생 시 이동할 프리셋 |
| `home_preset_id` | INTEGER | FK → camera_presets.id, SET NULL | 홈으로 돌아갈 프리셋 |
| `delay_time` | INTEGER | NOT NULL, DEFAULT 0 | target_preset 도착 후 대기 시간 (초) |
| `is_enable` | BOOLEAN | NOT NULL, DEFAULT TRUE | 활성화 여부 |
| `priority` | INTEGER | NULL, DEFAULT NULL | 실행 우선순위 (Optional) |
| `created_at` | TIMESTAMP | NOT NULL | 생성 시간 |
| `updated_at` | TIMESTAMP | NOT NULL | 수정 시간 |

**제거된 필드**:
- `touring_time`: CameraPreset.touring_time에서 참조
- `urls`: 향후 Camera 테이블에서 관리

**관계**:
- `EventMapping` 1:N `EventMappingCamera` (CASCADE DELETE)
- `Camera` 1:N `EventMappingCamera` (SET NULL - 카메라 삭제 시 연결만 해제)
- `CameraPreset` 1:N `EventMappingCamera.target_preset_id` (SET NULL)
- `CameraPreset` 1:N `EventMappingCamera.home_preset_id` (SET NULL)

---

## 5. 새로운 API 설계

### 5.1 엔드포인트 구조

기존 `/api/camera-event-mappings`를 제거하고, `EventMapping` 하위에 카메라 설정 API를 추가합니다.

#### 기존 엔드포인트 (제거 대상)

```
DELETE  /api/camera-event-mappings             # 제거
DELETE  /api/camera-event-mappings/{id}        # 제거
```

#### 새로운 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/integrations/event-mappings/{mapping_id}/cameras` | 카메라 연동 목록 조회 |
| GET | `/api/integrations/event-mappings/{mapping_id}/cameras/{config_id}` | 카메라 연동 상세 조회 |
| POST | `/api/integrations/event-mappings/{mapping_id}/cameras` | 카메라 연동 생성 |
| PATCH | `/api/integrations/event-mappings/{mapping_id}/cameras/{config_id}` | 카메라 연동 부분 수정 |
| PUT | `/api/integrations/event-mappings/{mapping_id}/cameras/{config_id}` | 카메라 연동 전체 수정 |
| DELETE | `/api/integrations/event-mappings/{mapping_id}/cameras/{config_id}` | 카메라 연동 삭제 |

### 5.2 API 상세

#### 5.2.1 카메라 연동 목록 조회

**Endpoint**: `GET /api/integrations/event-mappings/{mapping_id}/cameras`

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
            "onvif": { "device_service": "http://192.168.1.101:8000/onvif/device_service" },
            "streams": {
              "rtsp": {
                "main": "rtsp://192.168.1.101:554/Streaming/Channels/101",
                "sub": "rtsp://192.168.1.101:554/Streaming/Channels/102"
              },
              "webrtc": { "main": "https://192.168.1.101/webrtc/main" }
            },
            "snapshot": { "ch1": "http://192.168.1.101/cgi-bin/snapshot.cgi" }
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
      },
      {
        "id": 2,
        "event_mapping_id": 10,
        "camera": {
          "id": 202,
          "number_device": 2,
          "group_device": 1,
          "name_device": "PTZ-Camera-02",
          "type_device": "IpCamera",
          "version": "1.0.0",
          "status": "ACTIVATED",
          "ip_address": "192.168.1.102",
          "ip_port": 80,
          "mode": "ONVIF",
          "category": "PTZ",
          "is_record": false,
          "hardware_spec": null,
          "geolocation": null,
          "urls": {
            "streams": {
              "rtsp": { "main": "rtsp://192.168.1.102:554/Streaming/Channels/101" }
            }
          },
          "device_groups": [
            { "id": 1, "name": "1구역 센서 그룹", "description": "1구역 감시 장비", "device_count": 5 }
          ]
        },
        "target_preset": null,
        "home_preset": null,
        "delay_time": 0,
        "is_enable": true,
        "priority": null,
        "created_at": "2026-01-07T10:00:00.000+09:00",
        "updated_at": "2026-01-07T10:00:00.000+09:00"
      }
    ],
    "total": 2
  },
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 2,
    "total_pages": 1
  }
}
```

#### 5.2.2 카메라 연동 생성

**Endpoint**: `POST /api/integrations/event-mappings/{mapping_id}/cameras`

**Request Body**:

```json
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
        "onvif": { "device_service": "http://192.168.1.101:8000/onvif/device_service" },
        "streams": {
          "rtsp": {
            "main": "rtsp://192.168.1.101:554/Streaming/Channels/101",
            "sub": "rtsp://192.168.1.101:554/Streaming/Channels/102"
          },
          "webrtc": { "main": "https://192.168.1.101/webrtc/main" }
        },
        "snapshot": { "ch1": "http://192.168.1.101/cgi-bin/snapshot.cgi" }
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
}
```

#### 5.2.3 EventMapping API 설계 원칙

> **중요**: EventMapping은 다양한 Action 타입(Camera, Speaker, 3rd Party)의 Base 노드입니다.
> 따라서 `include_cameras`와 같은 특정 타입에 종속된 파라미터를 사용하지 않습니다.

**❌ 잘못된 접근 (사용하지 않음)**:
```
GET /api/integrations/event-mappings/{mapping_id}?include_cameras=true  ← 특정 타입에 종속
GET /api/integrations/event-mappings/{mapping_id}?include_speakers=true ← 파라미터 증가
GET /api/integrations/event-mappings/{mapping_id}?include_all=true      ← 불필요한 데이터 조회
```

**✅ 올바른 접근 (독립 API)**:
```
GET /api/integrations/event-mappings/{mapping_id}                       ← Base 정보만
GET /api/integrations/event-mappings/{mapping_id}/cameras               ← Camera Action 목록
GET /api/integrations/event-mappings/{mapping_id}/speakers              ← Speaker Action 목록 (향후)
GET /api/integrations/event-mappings/{mapping_id}/externals             ← 3rd Party Action 목록 (향후)
```

**이유**:
1. **확장성**: 새로운 Action 타입 추가 시 EventMapping API 수정 불필요
2. **관심사 분리**: 각 Action 타입은 독립적으로 관리
3. **성능**: 필요한 Action 타입만 조회 (불필요한 JOIN 방지)
4. **명확성**: API 엔드포인트가 리소스 구조를 명확히 표현

#### 5.2.4 EventMapping 상세 조회 (Base 정보만)

**Endpoint**: `GET /api/integrations/event-mappings/{mapping_id}`

**Response Example** (200 OK):

> EventMapping은 Base 정보만 반환합니다.
> Camera/Speaker/External Action은 각각의 하위 API에서 조회합니다.

```json
{
  "success": true,
  "message": "Event mapping retrieved successfully",
  "data": {
    "id": 10,
    "name_event": "1구역 침입 감지",
    "device_group": {
      "id": 1,
      "name": "1구역 센서 그룹",
      "description": "1구역 감시 장비"
    },
    "category_event": "detection",
    "description": "1구역 침입 감지 시 카메라/방송 연동",
    "status": true,
    "created_at": "2026-01-01T00:00:00.000+09:00",
    "updated_at": "2026-01-07T10:00:00.000+09:00"
  }
}
```

> **Note**: `device_group_id` 필드는 Response에서 제거됩니다. `device_group.id`로 접근하세요.

#### 5.2.5 Action 타입별 API 구조 (확장 계획)

| Action 타입 | 엔드포인트 | 구현 상태 |
|-------------|-----------|-----------|
| **Camera Action** | `/api/integrations/event-mappings/{id}/cameras` | 본 PRD에서 구현 |
| **Speaker Action** | `/api/integrations/event-mappings/{id}/speakers` | 향후 PRD |
| **External Action** | `/api/integrations/event-mappings/{id}/externals` | 향후 PRD |

**향후 확장 예시**:
```
POST /api/integrations/event-mappings/{id}/speakers
{
  "speaker_id": 1,
  "message_template_id": 5,
  "volume": 80,
  "repeat_count": 3,
  "is_enable": true,
  "priority": 2
}

POST /api/integrations/event-mappings/{id}/externals
{
  "name": "SMS 알림",
  "endpoint_url": "https://sms.example.com/send",
  "http_method": "POST",
  "payload_template": "{\"phone\": \"$user.phone\", \"message\": \"$event.description\"}",
  "auth_type": "bearer",
  "is_enable": true,
  "priority": 3
}
```

---

## 6. 스키마 설계

### 6.1 새로운 Pydantic 스키마

```python
# app/schemas/event_mapping_camera.py

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime


# ============================================================
# Nested Response Schemas (Full Property, timestamp 제외)
# ============================================================

class CameraNestedResponse(BaseModel):
    """카메라 Nested 응답 - Full Property (timestamp 제외)

    참고: PRD_Camera_Urls_JsonB.md
    - rtsp_uri, rtsp_port 제거
    - urls JSONB 필드로 통합
    """
    id: int
    number_device: int
    group_device: int
    name_device: str
    type_device: str
    version: Optional[str] = None
    status: str
    ip_address: str
    ip_port: int
    mode: str
    category: str
    is_record: bool
    hardware_spec: Optional[HardwareSpec] = None  # 하드웨어 스펙 정보
    geolocation: Optional[Geolocation] = None      # 좌표/위치 정보
    urls: Optional[CameraUrls] = None              # 카메라 URL 정보 (JSONB)
    device_groups: List[DeviceGroupNestedResponse] = []  # 소속 디바이스 그룹 목록

    model_config = ConfigDict(from_attributes=True)


class PresetNestedResponse(BaseModel):
    """프리셋 Nested 응답 - Full Property (timestamp 제외)"""
    id: int
    camera_id: int
    camera_name: str
    preset_index: int
    preset_name: str
    touring_time: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Create/Update Schemas
# ============================================================

class EventMappingCameraCreate(BaseModel):
    """카메라 연동 생성 스키마"""
    camera_id: int = Field(..., description="대상 카메라 ID")
    target_preset_id: Optional[int] = Field(None, description="이벤트 발생 시 이동할 프리셋 ID")
    home_preset_id: Optional[int] = Field(None, description="홈 복귀 프리셋 ID")
    delay_time: int = Field(0, ge=0, description="target_preset 도착 후 대기 시간 (초)")
    is_enable: bool = Field(True, description="활성화 여부")
    priority: Optional[int] = Field(None, ge=0, description="실행 우선순위 (Optional)")


class EventMappingCameraUpdate(BaseModel):
    """카메라 연동 수정 스키마 (PATCH)"""
    camera_id: Optional[int] = None
    target_preset_id: Optional[int] = None
    home_preset_id: Optional[int] = None
    delay_time: Optional[int] = Field(None, ge=0)
    is_enable: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=0)


# ============================================================
# Response Schemas
# ============================================================

class EventMappingCameraResponse(BaseModel):
    """카메라 연동 응답 스키마 (주체용 - timestamp 포함)"""
    id: int
    event_mapping_id: int
    camera: Optional[CameraNestedResponse] = None
    target_preset: Optional[PresetNestedResponse] = None
    home_preset: Optional[PresetNestedResponse] = None
    delay_time: int
    is_enable: bool
    priority: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventMappingCameraNestedResponse(BaseModel):
    """카메라 연동 Nested 응답 (EventMapping 내 nested용 - timestamp 제외)"""
    id: int
    camera: Optional[CameraNestedResponse] = None
    target_preset: Optional[PresetNestedResponse] = None
    home_preset: Optional[PresetNestedResponse] = None
    delay_time: int
    is_enable: bool
    priority: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
```

### 6.2 EventMapping 스키마 (변경 없음)

> **중요**: EventMapping은 Base 노드이므로, 특정 Action 타입을 포함하지 않습니다.
> 기존 `EventMappingResponse` 스키마를 그대로 사용합니다.

```python
# app/schemas/integration.py (기존 유지)

class EventMappingResponse(BaseModel):
    """EventMapping 응답 - Base 정보만 반환

    Note: device_group_id는 Response에서 제거됨.
    device_group Nested 객체로 접근 (device_group.id)
    """
    id: int
    name_event: str
    device_group: Optional[DeviceGroupNestedResponse] = None  # FK 대신 Nested 객체
    category_event: str
    description: Optional[str]
    status: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ❌ 제거된 스키마 (사용하지 않음)
# class EventMappingWithCamerasResponse - include_cameras 파라미터 방식 폐기
```

**설계 원칙**:
- EventMapping API는 Action 타입과 무관하게 Base 정보만 반환
- Camera/Speaker/External Action은 각각의 하위 API에서 전용 스키마로 반환
- 이를 통해 확장성과 관심사 분리를 확보

---

## 7. 모델 설계

### 7.1 새로운 SQLAlchemy 모델

```python
# app/models/event_mapping_camera.py

from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from app.config import settings


class EventMappingCamera(Base):
    """
    이벤트 매핑 카메라 연동 설정

    EventMapping에서 특정 이벤트 발생 시 실행할 카메라 동작을 정의합니다.
    touring_time은 target_preset.touring_time에서 참조합니다.
    """
    __tablename__ = "event_mapping_cameras"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # FK: EventMapping (CASCADE DELETE)
    event_mapping_id = Column(
        Integer,
        ForeignKey("event_mappings.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # FK: Camera (SET NULL - 카메라 삭제 시 연결만 해제)
    camera_id = Column(
        Integer,
        ForeignKey("cameras.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # FK: 이동 대상 프리셋 (SET NULL)
    # touring_time은 이 preset에서 참조
    target_preset_id = Column(
        Integer,
        ForeignKey("camera_presets.id", ondelete="SET NULL"),
        nullable=True
    )

    # FK: 홈 복귀 프리셋 (SET NULL)
    home_preset_id = Column(
        Integer,
        ForeignKey("camera_presets.id", ondelete="SET NULL"),
        nullable=True
    )

    # target_preset 도착 후 대기 시간 (홈 복귀 전 대기)
    delay_time = Column(Integer, nullable=False, default=0)

    # 상태 및 우선순위
    is_enable = Column(Boolean, nullable=False, default=True)
    priority = Column(Integer, nullable=True, default=None)  # Optional

    # 타임스탬프
    created_at = Column(DateTime, default=lambda: datetime.now(settings.tz), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(settings.tz),
                       onupdate=lambda: datetime.now(settings.tz), nullable=False)

    # Relationships
    event_mapping = relationship("EventMapping", back_populates="cameras")
    camera = relationship("Camera", foreign_keys=[camera_id])
    target_preset = relationship("CameraPreset", foreign_keys=[target_preset_id])
    home_preset = relationship("CameraPreset", foreign_keys=[home_preset_id])
```

### 7.2 기존 EventMapping 모델 수정

> **주의**: EventMapping에 `cameras` relationship을 추가하되, 이것이 "Camera 전용"이 아닌
> "여러 Action 타입 중 하나"임을 명확히 합니다.

```python
# app/models/integration.py 수정

class EventMapping(Base):
    """
    EventMapping Model - 이벤트 연동 Base Node

    다양한 Action 타입의 Base 노드로 사용됩니다:
    - Camera Action: cameras relationship
    - Speaker Action: speakers relationship (향후)
    - External Action: externals relationship (향후)
    """
    __tablename__ = "event_mappings"

    # ... 기존 필드 ...

    # ============================================
    # Action Type Relationships
    # 각 Action 타입은 독립적인 하위 테이블로 관리
    # ============================================

    # Camera Actions
    cameras = relationship(
        "EventMappingCamera",
        back_populates="event_mapping",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    # Speaker Actions (향후 구현)
    # speakers = relationship(
    #     "EventMappingSpeaker",
    #     back_populates="event_mapping",
    #     cascade="all, delete-orphan",
    #     lazy="dynamic"
    # )

    # External Actions (향후 구현)
    # externals = relationship(
    #     "EventMappingExternal",
    #     back_populates="event_mapping",
    #     cascade="all, delete-orphan",
    #     lazy="dynamic"
    # )
```

---

## 8. 마이그레이션 계획

### 8.1 단계별 마이그레이션

#### Phase 1: 새 테이블 생성 (하위 호환 유지)

1. `event_mapping_cameras` 테이블 생성
2. 기존 `camera_event_mappings`, `camera_event_presets` 테이블 유지
3. 새 API 엔드포인트 추가 (`/api/integrations/event-mappings/{id}/cameras`)

#### Phase 2: 데이터 마이그레이션

```sql
-- 기존 CameraEventMapping → EventMapping + EventMappingCamera 변환
-- (수동 마이그레이션 필요 - 비즈니스 로직 확인 후)

INSERT INTO event_mapping_cameras (
    event_mapping_id, camera_id, target_preset_id, home_preset_id,
    delay_time, is_enable, priority
)
SELECT
    em.id,  -- 매핑되는 EventMapping.id (수동 매핑 필요)
    cep.cam_id,
    NULL,  -- target_preset_id (기존 preset_id가 VARCHAR라 매핑 불가)
    cep.home_preset,
    cep.home_time,  -- → delay_time으로 마이그레이션
    TRUE,
    NULL
FROM camera_event_presets cep
JOIN camera_event_mappings cem ON cep.mapping_id = cem.id
JOIN event_mappings em ON cem.group_event = em.name_event;  -- 조건 확인 필요
```

#### Phase 3: 기존 API Deprecation

1. 기존 `/api/camera-event-mappings` API에 Deprecation 경고 추가
2. 클라이언트 마이그레이션 기간 (2~4주)

#### Phase 4: 기존 테이블 제거

1. `camera_event_presets` 테이블 삭제
2. `camera_event_mappings` 테이블 삭제
3. 기존 API 엔드포인트 제거

---

## 9. 구현 순서

### Phase 1: 모델 및 스키마 (1일)
1. `app/models/event_mapping_camera.py` 생성
2. `app/schemas/event_mapping_camera.py` 생성
3. EventMapping 모델에 `cameras` relationship 추가
4. DB 마이그레이션

### Phase 2: API 구현 (2일)
1. `app/routers/event_mapping_cameras.py` 생성
2. CRUD 엔드포인트 구현
3. EventMapping API에 `include_cameras` 파라미터 추가

### Phase 3: 데이터 마이그레이션 (1일)
1. 마이그레이션 스크립트 작성
2. 테스트 환경에서 검증
3. 운영 데이터 마이그레이션

### Phase 4: 정리 (1일)
1. 기존 API Deprecation
2. 기존 테이블 제거
3. 문서 업데이트

---

## 10. 고려사항

### 10.1 하위 호환성

- 기존 클라이언트가 사용하는 `/api/camera-event-mappings` API는 당분간 유지
- Deprecation 기간 동안 경고 헤더 추가: `Deprecation: true`
- 새 API로 마이그레이션 가이드 제공

### 10.2 데이터 무결성

- `camera_id` SET NULL: 카메라 삭제 시 연동 설정은 유지 (camera=null)
- `target_preset_id`, `home_preset_id` SET NULL: 프리셋 삭제 시 연동 설정 유지
- `event_mapping_id` CASCADE: EventMapping 삭제 시 카메라 연동도 삭제

### 10.3 Nested Response 규칙 적용

| 응답 타입 | 규칙 | timestamp |
|-----------|------|-----------|
| `EventMappingCameraResponse` | 주체 | `created_at`, `updated_at` 포함 |
| `EventMappingCameraNestedResponse` | nested | `created_at`, `updated_at` 제외 |
| `CameraNestedResponse` | nested의 nested | Full Property, timestamp 제외 |
| `PresetNestedResponse` | nested의 nested | Full Property, timestamp 제외 |

### 10.4 제거된 필드 정리

| 필드 | 이유 |
|------|------|
| `touring_time` | `CameraPreset.touring_time`에서 참조 |
| `url_live`, `url_record` | Camera.urls JSONB로 통합 (PRD_Camera_Urls_JsonB.md 참조) |
| `rtsp_uri`, `rtsp_port` | Camera.urls JSONB로 통합 (PRD_Camera_Urls_JsonB.md 참조) |
| `category` | 용도 불명확, 불필요 |
| `preset_time` | `touring_time`과 동일, 중복 |

### 10.5 Camera URLs JSONB 통합

> **참고**: Camera URLs JSONB 통합에 대한 상세 내용은 **[PRD_Camera_Urls_JsonB.md](PRD_Camera_Urls_JsonB.md)** 참조

```python
# cameras 테이블의 urls JSONB 컬럼
urls = Column(JSON, nullable=True)
"""
{
    "homepage": { "url": "https://192.168.0.10/" },
    "onvif": { "device_service": "http://192.168.0.10:8000/onvif/device_service" },
    "streams": {
        "rtsp": { "main": "rtsp://...", "sub": "rtsp://..." },
        "webrtc": { "main": "https://..." },
        "hls": { "main": "https://..." }
    },
    "snapshot": { "ch1": "http://..." }
}
"""
```

---

## 11. 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| **v2.1** | 2026-01-07 | **Camera URLs JSONB 통합 반영**<br>- PRD_Camera_Urls_JsonB.md 연동<br>- `rtsp_uri`, `rtsp_port` → `urls` JSONB로 변경<br>- CameraNestedResponse 스키마에 `urls` 필드 추가<br>- API Response 예시에 urls JSONB 구조 반영<br>- 제거된 필드 정리 업데이트 |
| **v2.0** | 2026-01-07 | **EventMapping Base Node 아키텍처 적용**<br>- 문서 제목 변경: "EventMapping 기반 Action 연동 아키텍처 리팩토링"<br>- EventMapping을 다중 Action 타입(Camera/Speaker/3rd Party)의 Base 노드로 재정의<br>- `include_cameras` 파라미터 방식 폐기<br>- 각 Action 타입별 독립 API 구조 정의<br>- 향후 확장 계획 (Speaker Action, External Action) 추가<br>- 개념적 아키텍처 다이어그램 추가 |
| **v1.1** | 2026-01-07 | **필드 정리 및 Nested Response 규칙 적용**<br>- `touring_time` 제거 (CameraPreset에서 참조)<br>- `urls` 제거 (향후 Camera 확장)<br>- `priority` Optional로 변경<br>- Nested Response Full Property 적용 (timestamp 제외)<br>- API Response 예시 상세화 |
| **v1.0** | 2026-01-07 | 초안 작성 - CameraEventMapping 리팩토링 PRD |

---

## 12. 핵심 요약

### EventMapping = Base Node

```
EventMapping (Base)
    ├── EventMappingCamera    ← 본 PRD에서 구현
    ├── EventMappingSpeaker   ← 향후 PRD
    └── EventMappingExternal  ← 향후 PRD
```

### API 구조

```
/api/event-mappings                           ← Base 정보
/api/integrations/event-mappings/{id}/cameras              ← Camera Action (본 PRD)
/api/integrations/event-mappings/{id}/speakers             ← Speaker Action (향후)
/api/integrations/event-mappings/{id}/externals            ← External Action (향후)
```

### 설계 원칙

1. **EventMapping API에 특정 Action 타입 포함 금지** (`include_cameras` ❌)
2. **각 Action 타입은 독립 API로 관리**
3. **새로운 Action 타입 추가 시 기존 구조 영향 없음**

---

**문서 끝**
