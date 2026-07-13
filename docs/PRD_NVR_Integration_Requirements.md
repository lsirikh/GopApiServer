# NVR 연동 기능 정의서

**문서 버전**: v1.0
**작성일**: 2026-01-16
**상태**: Draft

---

## 1. 개요

### 1.1 목적
GOP 시스템과 NVR(Network Video Recorder) 간의 연동 기능을 정의하고, 향후 NVR 업체의 메시지 브로커 지원 시 **NVR API Manager 통합 이관**을 위한 요구사항을 정리한다.

### 1.2 연동 구조

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              GOP 통합 시스템                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────────┐  │
│  │  영상분석서버  │    │   DB API     │    │       NATS 브로커            │  │
│  │ (AI Server)  │    │   Server     │    │    (Message Broker)          │  │
│  └──────┬───────┘    └──────┬───────┘    └──────────────┬───────────────┘  │
│         │                   │                           │                   │
│         ▼                   ▼                           ▼                   │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      NVR API Manager                                  │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │ 자산 관리    │  │ 스트리밍 제어│  │ 녹화 관리   │  │ 이벤트 처리  │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
└────────────────────────────────────┼────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              NVR 시스템                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ 카메라    │  │ 녹화저장  │  │ PTZ제어   │  │ 스트리밍  │  │ 저장소   │      │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 NVR API Manager 이관 시나리오
NVR 업체에서 메시지 브로커(NATS)를 통한 연동을 지원할 경우:
- GOP의 NVR API Manager 모듈을 NVR 업체에 **통으로 이관**
- NVR 업체는 동일한 NATS 메시지 규격 및 DB API 규격 준수
- GOP는 추상화된 인터페이스만 유지

---

## 2. 연동 대상 기능 분류

### 2.1 DB API 기반 (자산관리 - REST API)
| 분류 | 설명 |
|------|------|
| 카메라 자산 | 카메라 등록/조회/수정/삭제 |
| 프리셋 관리 | PTZ 프리셋 위치 저장 |
| ROI 설정 | 관심영역 좌표 관리 |
| 서버 등록 | NVR 서버 인스턴스 관리 |
| 이벤트 매핑 | 이벤트-카메라 연동 설정 |
| 녹화 설정 | 카메라별 녹화 활성화 |
| 장비 그룹 | 카메라 그룹화 관리 |

### 2.2 NATS 브로커 기반 (제어/상태 - Pub/Sub)
| 분류 | 설명 |
|------|------|
| PTZ 제어 | Pan/Tilt/Zoom 실시간 제어 |
| 프리셋 이동 | 저장된 프리셋으로 카메라 이동 |
| 녹화 제어 | 녹화 시작/중지 명령 |
| 스트리밍 요청 | 실시간 영상 스트림 요청 |
| 카메라 상태 | 연결/오류 상태 수신 |
| 녹화 상태 | 녹화 진행 상태 수신 |
| 저장소 알림 | 디스크 용량 경고 |
| 이벤트 알림 | 탐지 이벤트 발생 알림 |

---

## 3. 영상분석서버 ↔ NVR 연동

### 3.1 연동 흐름

```
┌─────────────────┐                    ┌─────────────────┐
│   영상분석서버    │                    │       NVR       │
│  (AI Analysis)  │                    │                 │
└────────┬────────┘                    └────────┬────────┘
         │                                      │
         │  1. 스트림 요청 (NATS)               │
         │─────────────────────────────────────▶│
         │                                      │
         │  2. RTSP 스트림 제공                  │
         │◀─────────────────────────────────────│
         │                                      │
         │  3. AI 분석 수행                      │
         │  (객체탐지, 이벤트 감지)               │
         │                                      │
         │  4. 탐지 이벤트 발생 (NATS)           │
         │─────────────────────────────────────▶│
         │                                      │
         │  5. 이벤트 녹화 시작                  │
         │  6. 이벤트 영상 클립 저장              │
         │                                      │
         │  7. 썸네일/클립 URL 반환              │
         │◀─────────────────────────────────────│
         │                                      │
```

### 3.2 영상분석서버 → NVR 전달 데이터

| 항목 | 필드명 | 타입 | 설명 |
|------|--------|------|------|
| 카메라 ID | camera_id | Integer | 분석 대상 카메라 |
| 탐지 유형 | detection_type | Enum | AI_DETECT, THERMAL_SENSOR 등 |
| 탐지 시간 | detected_at | DateTime | 이벤트 발생 시각 |
| 신뢰도 | confidence | Float | AI 탐지 신뢰도 (0.0~1.0) |
| 객체 정보 | objects | JSONB | 탐지된 객체 목록 (bbox, class) |
| ROI 정보 | roi_id | Integer | 탐지 발생 ROI (optional) |
| 녹화 요청 | request_recording | Boolean | 이벤트 녹화 요청 여부 |

### 3.3 NVR → 영상분석서버 제공 데이터

| 항목 | 필드명 | 타입 | 설명 |
|------|--------|------|------|
| 스트림 URL | stream_url | String | RTSP/HLS 스트림 URL |
| 썸네일 URL | thumbnail_url | String | 이벤트 스냅샷 URL |
| 클립 URL | clip_url | String | 이벤트 영상 클립 URL |
| 녹화 상태 | recording_status | Enum | RECORDING, STOPPED |

---

## 4. DB API 자산관리 항목

### 4.1 카메라 관리 (Cameras)

**테이블**: `devices` + `cameras` (Joined Table Inheritance)

| API | Method | Endpoint | 설명 |
|-----|--------|----------|------|
| 카메라 목록 조회 | GET | `/cameras` | 필터링, 페이징 지원 |
| 카메라 상세 조회 | GET | `/cameras/{id}` | 단일 카메라 정보 |
| 카메라 등록 | POST | `/cameras` | 신규 카메라 추가 |
| 카메라 수정 | PUT | `/cameras/{id}` | 카메라 정보 변경 |
| 카메라 삭제 | DELETE | `/cameras/{id}` | 카메라 제거 (CASCADE) |

**Camera 필드 (NVR 관련)**:
```
cameras
├── id                  # PK (devices.id 상속)
├── number_device       # 장비 번호
├── name_device         # 카메라 이름
├── ip_address          # 카메라 IP
├── ip_port             # 포트
├── user_name           # 인증 사용자명
├── user_password       # 인증 비밀번호
├── urls                # JSONB: RTSP/HTTP URL 정보
│   ├── rtsp_main       # 메인 스트림 RTSP URL
│   ├── rtsp_sub        # 서브 스트림 RTSP URL
│   ├── http_snapshot   # HTTP 스냅샷 URL
│   └── onvif_service   # ONVIF 서비스 URL
├── mode                # ONVIF, EMSTONE_API, INNODEP_API, ETC
├── category            # FIXED, PTZ
├── is_record           # 녹화 활성화 여부
├── hardware_spec       # JSONB: 하드웨어 스펙
├── geolocation         # JSONB: 위치 정보
├── status              # ACTIVATED, ERROR, DEACTIVATED
├── is_enable           # 장비 활성화 여부
├── created_at
└── updated_at
```

### 4.2 카메라 프리셋 관리 (Camera Presets)

**테이블**: `camera_presets`

| API | Method | Endpoint | 설명 |
|-----|--------|----------|------|
| 프리셋 목록 | GET | `/cameras/{camera_id}/presets` | 카메라별 프리셋 |
| 프리셋 상세 | GET | `/camera-presets/{id}` | 프리셋 정보 |
| 프리셋 등록 | POST | `/cameras/{camera_id}/presets` | 프리셋 추가 |
| 프리셋 수정 | PUT | `/camera-presets/{id}` | 프리셋 변경 |
| 프리셋 삭제 | DELETE | `/camera-presets/{id}` | 프리셋 제거 |

**CameraPreset 필드**:
```
camera_presets
├── id                  # PK
├── camera_id           # FK → cameras.id (CASCADE)
├── camera_name         # 카메라명 (참조용)
├── preset_index        # 프리셋 인덱스 (카메라 내 고유)
├── preset_name         # 프리셋 표시명
├── touring_time        # Home → Preset 이동 시간 (초)
├── created_at
└── updated_at
```

### 4.3 ROI 관리 (Region of Interest)

**테이블**: `rois`, `xy_points`

| API | Method | Endpoint | 설명 |
|-----|--------|----------|------|
| ROI 목록 | GET | `/camera-presets/{preset_id}/rois` | 프리셋별 ROI |
| ROI 상세 | GET | `/rois/{id}` | ROI 정보 + 포인트 |
| ROI 등록 | POST | `/camera-presets/{preset_id}/rois` | ROI 추가 |
| ROI 수정 | PUT | `/rois/{id}` | ROI 변경 |
| ROI 삭제 | DELETE | `/rois/{id}` | ROI 제거 (CASCADE) |

**ROI 필드**:
```
rois
├── id                  # PK
├── preset_id           # FK → camera_presets.id (CASCADE)
├── name                # ROI 이름
├── resolution_width    # 참조 해상도 너비
├── resolution_height   # 참조 해상도 높이
├── is_enable           # 활성화 여부
├── created_at
└── updated_at

xy_points
├── id                  # PK
├── roi_id              # FK → rois.id (CASCADE)
├── x                   # X 좌표 (정규화 또는 픽셀)
├── y                   # Y 좌표
├── order               # 다각형 순서
├── created_at
└── updated_at
```

### 4.4 NVR 서버 관리 (Servers)

**테이블**: `server_categories`, `servers`

| API | Method | Endpoint | 설명 |
|-----|--------|----------|------|
| NVR 서버 목록 | GET | `/servers?type=NVR_API` | NVR 서버 필터링 |
| NVR 서버 상세 | GET | `/servers/{id}` | 서버 정보 |
| NVR 서버 등록 | POST | `/servers` | 서버 추가 |
| NVR 서버 수정 | PUT | `/servers/{id}` | 서버 변경 |
| NVR 서버 삭제 | DELETE | `/servers/{id}` | 서버 제거 |

**Server 필드 (NVR 관련)**:
```
servers
├── id                  # PK
├── category_id         # FK → server_categories.id
├── name                # 서버명 (예: "NVR-Primary")
├── status              # NORMAL, WARNING, ERROR
├── ip_address          # 서버 IP
├── port                # API 포트
├── hostname            # 호스트명
├── user_name           # 인증 사용자
├── user_password       # 인증 비밀번호
├── threshold_config    # JSONB: 임계치 설정
├── created_at
└── updated_at

server_categories
├── id
├── name                # "NVR API 서버"
├── type_server         # NVR_API (EnumServerType)
├── description
├── sort_order
├── created_at
└── updated_at
```

### 4.5 이벤트 매핑 관리 (Event Mappings)

**테이블**: `event_mappings`, `event_mapping_cameras`

| API | Method | Endpoint | 설명 |
|-----|--------|----------|------|
| 매핑 목록 | GET | `/event-mappings` | 이벤트 매핑 목록 |
| 매핑 상세 | GET | `/event-mappings/{id}` | 매핑 + 카메라 액션 |
| 매핑 등록 | POST | `/event-mappings` | 매핑 추가 |
| 매핑 수정 | PUT | `/event-mappings/{id}` | 매핑 변경 |
| 매핑 삭제 | DELETE | `/event-mappings/{id}` | 매핑 제거 (CASCADE) |
| 카메라 액션 추가 | POST | `/event-mappings/{id}/cameras` | 카메라 연동 |
| 카메라 액션 수정 | PUT | `/event-mapping-cameras/{id}` | 액션 변경 |
| 카메라 액션 삭제 | DELETE | `/event-mapping-cameras/{id}` | 액션 제거 |

**EventMapping 필드**:
```
event_mappings
├── id                      # PK
├── name_event              # 매핑 이름
├── device_group_id         # FK → device_groups.id (SET NULL)
├── category_event_mapping  # Enum: 센서 조합 타입
├── description
├── status                  # 활성화 여부
├── created_at
└── updated_at

event_mapping_cameras
├── id                  # PK
├── event_mapping_id    # FK → event_mappings.id (CASCADE)
├── camera_id           # FK → cameras.id (SET NULL)
├── target_preset_id    # FK → camera_presets.id (SET NULL)
├── home_preset_id      # FK → camera_presets.id (SET NULL)
├── delay_time          # 타겟 프리셋 대기 시간
├── is_enable           # 활성화 여부
├── priority            # 우선순위
├── created_at
└── updated_at
```

### 4.6 장비 그룹 관리 (Device Groups)

**테이블**: `device_groups`, `device_group_mappings`

| API | Method | Endpoint | 설명 |
|-----|--------|----------|------|
| 그룹 목록 | GET | `/device-groups` | 장비 그룹 목록 |
| 그룹 상세 | GET | `/device-groups/{id}` | 그룹 + 멤버 |
| 그룹 등록 | POST | `/device-groups` | 그룹 추가 |
| 그룹 수정 | PUT | `/device-groups/{id}` | 그룹 변경 |
| 그룹 삭제 | DELETE | `/device-groups/{id}` | 그룹 제거 |
| 멤버 추가 | POST | `/device-groups/{id}/devices` | 장비 추가 |
| 멤버 제거 | DELETE | `/device-group-mappings/{id}` | 장비 제거 |

---

## 5. NATS 브로커 메시지 항목

### 5.1 메시지 토픽 구조

```
gop.nvr.{action}.{target}
├── gop.nvr.control.ptz          # PTZ 제어
├── gop.nvr.control.preset       # 프리셋 이동
├── gop.nvr.control.recording    # 녹화 제어
├── gop.nvr.request.stream       # 스트림 요청
├── gop.nvr.status.camera        # 카메라 상태
├── gop.nvr.status.recording     # 녹화 상태
├── gop.nvr.status.storage       # 저장소 상태
├── gop.nvr.event.detection      # 탐지 이벤트
└── gop.nvr.event.system         # 시스템 이벤트
```

### 5.2 제어 메시지 (Command → NVR)

#### 5.2.1 PTZ 제어 (`gop.nvr.control.ptz`)
```json
{
  "message_id": "uuid",
  "timestamp": "2026-01-16T10:00:00+09:00",
  "camera_id": 123,
  "command": "MOVE",           // MOVE, ZOOM, FOCUS, STOP
  "pan": 45.0,                 // -180 ~ 180
  "tilt": 30.0,                // -90 ~ 90
  "zoom": 1.5,                 // 1.0 ~ max
  "speed": 5,                  // 1 ~ 10
  "duration_ms": 0             // 0 = continuous
}
```

#### 5.2.2 프리셋 이동 (`gop.nvr.control.preset`)
```json
{
  "message_id": "uuid",
  "timestamp": "2026-01-16T10:00:00+09:00",
  "camera_id": 123,
  "command": "GOTO",           // GOTO, SAVE, DELETE
  "preset_index": 5,
  "preset_name": "감시구역A",
  "speed": 7
}
```

#### 5.2.3 녹화 제어 (`gop.nvr.control.recording`)
```json
{
  "message_id": "uuid",
  "timestamp": "2026-01-16T10:00:00+09:00",
  "camera_id": 123,
  "command": "START",          // START, STOP, SCHEDULE
  "event_id": 456,             // 이벤트 연동 녹화 시
  "duration_sec": 300,         // 녹화 시간 (0 = 무제한)
  "pre_event_sec": 10,         // 이벤트 전 녹화
  "post_event_sec": 30         // 이벤트 후 녹화
}
```

#### 5.2.4 스트림 요청 (`gop.nvr.request.stream`)
```json
{
  "message_id": "uuid",
  "timestamp": "2026-01-16T10:00:00+09:00",
  "camera_id": 123,
  "stream_type": "RTSP",       // RTSP, HLS, WEBRTC
  "quality": "MAIN",           // MAIN, SUB
  "requester": "ai_analysis_01"
}
```

### 5.3 상태 메시지 (NVR → System)

#### 5.3.1 카메라 상태 (`gop.nvr.status.camera`)
```json
{
  "message_id": "uuid",
  "timestamp": "2026-01-16T10:00:00+09:00",
  "camera_id": 123,
  "status": "CONNECTED",       // CONNECTED, DISCONNECTED, ERROR
  "error_code": null,
  "error_message": null,
  "current_preset": 5,
  "ptz_position": {
    "pan": 45.0,
    "tilt": 30.0,
    "zoom": 1.5
  }
}
```

#### 5.3.2 녹화 상태 (`gop.nvr.status.recording`)
```json
{
  "message_id": "uuid",
  "timestamp": "2026-01-16T10:00:00+09:00",
  "camera_id": 123,
  "status": "RECORDING",       // RECORDING, STOPPED, ERROR
  "event_id": 456,
  "started_at": "2026-01-16T10:00:00+09:00",
  "file_path": "/recordings/2026/01/16/cam123_event456.mp4",
  "file_size_mb": 125.5
}
```

#### 5.3.3 저장소 상태 (`gop.nvr.status.storage`)
```json
{
  "message_id": "uuid",
  "timestamp": "2026-01-16T10:00:00+09:00",
  "server_id": 1,
  "status": "WARNING",         // NORMAL, WARNING, CRITICAL
  "total_gb": 10240,
  "used_gb": 9216,
  "free_gb": 1024,
  "usage_percent": 90.0,
  "retention_days": 30,
  "oldest_recording": "2025-12-17T00:00:00+09:00"
}
```

### 5.4 이벤트 메시지

#### 5.4.1 탐지 이벤트 (`gop.nvr.event.detection`)
```json
{
  "message_id": "uuid",
  "timestamp": "2026-01-16T10:00:00+09:00",
  "event_id": 456,
  "camera_id": 123,
  "event_type": "INTRUSION",   // INTRUSION, MOTION, OBJECT
  "detection_type": "AI_DETECT",
  "confidence": 0.95,
  "objects": [
    {
      "class": "person",
      "confidence": 0.95,
      "bbox": {"x": 100, "y": 200, "w": 80, "h": 160}
    }
  ],
  "roi_id": 10,
  "thumbnail_url": "/thumbnails/event_456.jpg",
  "clip_url": "/clips/event_456.mp4"
}
```

#### 5.4.2 시스템 이벤트 (`gop.nvr.event.system`)
```json
{
  "message_id": "uuid",
  "timestamp": "2026-01-16T10:00:00+09:00",
  "server_id": 1,
  "event_type": "SERVER_ERROR",
  "severity": "ERROR",
  "title": "녹화 스토리지 오류",
  "message": "디스크 쓰기 오류 발생",
  "detail": {
    "disk_id": "sda1",
    "error_code": "IO_ERROR"
  }
}
```

---

## 6. 이벤트 연동 시나리오

### 6.1 센서 탐지 → 카메라 연동

```
1. 센서 탐지 이벤트 발생
   └─ DetectionEvent (DB) 생성

2. EventMapping 조회
   └─ device_group_id 매칭
   └─ event_mapping_cameras 조회

3. 각 카메라에 프리셋 이동 명령 전송 (NATS)
   └─ gop.nvr.control.preset
   └─ target_preset_id로 이동

4. 이벤트 녹화 시작 (NATS)
   └─ gop.nvr.control.recording
   └─ pre_event + post_event 녹화

5. delay_time 후 홈 프리셋 복귀 (NATS)
   └─ gop.nvr.control.preset
   └─ home_preset_id로 이동

6. 녹화 완료 후 썸네일/클립 URL 수신 (NATS)
   └─ gop.nvr.status.recording
```

### 6.2 AI 분석 → 이벤트 녹화

```
1. 영상분석서버에서 객체 탐지
   └─ AI 모델 추론

2. 탐지 이벤트 전송 (NATS)
   └─ gop.nvr.event.detection
   └─ request_recording: true

3. NVR에서 이벤트 녹화 수행
   └─ 썸네일 생성
   └─ 영상 클립 저장

4. DetectionEvent 생성 (DB API)
   └─ detail.thumbnail_url
   └─ detail.clip_url
   └─ detail.objects (AI 탐지 정보)
```

---

## 7. NVR 업체 지원 요구사항

### 7.1 DB API 연동 (필수)

NVR 업체는 다음 DB API 엔드포인트를 통해 자산 데이터를 축적/조회해야 합니다:

| 우선순위 | 항목 | 설명 |
|----------|------|------|
| **P1** | 카메라 등록/수정 | 카메라 자산 동기화 |
| **P1** | 카메라 상태 업데이트 | 연결/오류 상태 반영 |
| **P1** | 이벤트 생성 | 탐지/시스템 이벤트 기록 |
| **P2** | 프리셋 등록/수정 | PTZ 프리셋 동기화 |
| **P2** | 서버 메트릭 전송 | 리소스 사용량 기록 |
| **P3** | ROI 동기화 | 관심영역 설정 동기화 |

### 7.2 NATS 브로커 연동 (권장)

| 우선순위 | 토픽 | 방향 | 설명 |
|----------|------|------|------|
| **P1** | gop.nvr.status.camera | NVR→GOP | 카메라 상태 수신 |
| **P1** | gop.nvr.control.preset | GOP→NVR | 프리셋 이동 명령 |
| **P1** | gop.nvr.event.detection | NVR→GOP | 탐지 이벤트 수신 |
| **P2** | gop.nvr.control.recording | GOP→NVR | 녹화 제어 명령 |
| **P2** | gop.nvr.status.recording | NVR→GOP | 녹화 상태 수신 |
| **P2** | gop.nvr.request.stream | GOP→NVR | 스트림 URL 요청 |
| **P3** | gop.nvr.control.ptz | GOP→NVR | PTZ 실시간 제어 |
| **P3** | gop.nvr.status.storage | NVR→GOP | 저장소 알림 |

### 7.3 NVR API Manager 이관 조건

NVR 업체가 메시지 브로커를 직접 지원할 경우:

1. **NATS 클라이언트 구현**
   - 위 토픽들에 대한 Pub/Sub 처리
   - 메시지 포맷 규격 준수

2. **DB API 클라이언트 구현**
   - 자산 데이터 CRUD 호출
   - 이벤트 데이터 생성 호출

3. **인증/인가 연동**
   - GOP 인증 시스템과 통합
   - API 키 또는 JWT 토큰 사용

---

## 8. 부록

### 8.1 관련 EnumServerType
```python
class EnumServerType(str, Enum):
    VMS = "VMS"                 # VMS 서버
    NVR_API = "NVR_API"         # NVR API 서버
    STREAMING = "STREAMING"     # 스트리밍 서버
    RECORDING = "RECORDING"     # 녹화 서버
    STORAGE = "STORAGE"         # 스토리지 서버
    AI_ANALYSIS = "AI_ANALYSIS" # 지능형영상 분석 서버
    # ... 기타
```

### 8.2 관련 EnumDetectionType
```python
class EnumDetectionType(str, Enum):
    AI_DETECT = "AI_DETECT"             # AI 탐지
    THERMAL_SENSOR = "THERMAL_SENSOR"   # 열화상 센서
    PIR_SENSOR = "PIR_SENSOR"           # PIR 센서
    # ... 기타
```

### 8.3 관련 문서
- `GOP_요구사항_통합정리.md` - 시스템 요구사항
- `GOP_Restful_Api_연동설계.md` - API 설계서
- `GOP_스키마_전체.md` - 데이터베이스 스키마
- `시스템 연동 인터페이스_v0.7_only.pdf` - 연동 구조

---

## 9. 변경 이력

| 버전 | 일자 | 작성자 | 변경 내용 |
|------|------|--------|-----------|
| v1.0 | 2026-01-16 | - | 초안 작성 |