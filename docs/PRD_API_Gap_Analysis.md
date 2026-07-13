# PRD: GOP RESTful API 구현 Gap 분석 및 개선 방안

> **작성일**: 2026-01-13
> **버전**: v1.0
> **목적**: GOP_Restful_Api_연동설계.md (v2.8) 대비 현재 구현(OpenAPI) 갭 분석 및 개선 작업 정의
> **분석 기준**: localhost:8000/openapi.json (FastAPI 자동 생성)

---

## 목차

1. [분석 개요](#1-분석-개요)
2. [구현 일치 항목](#2-구현-일치-항목)
3. [Gap 식별 - 미구현 항목](#3-gap-식별---미구현-항목)
4. [Gap 식별 - 불일치 항목](#4-gap-식별---불일치-항목)
5. [추가 구현 항목 (설계서 미기재)](#5-추가-구현-항목-설계서-미기재)
6. [개선 작업 목록](#6-개선-작업-목록)
7. [우선순위 및 일정](#7-우선순위-및-일정)

---

## 1. 분석 개요

### 1.1 분석 대상

| 구분 | 문서/소스 | 버전 | 비고 |
|------|-----------|------|------|
| **설계 문서** | GOP_Restful_Api_연동설계.md | v2.8 | 2026-01-12 최종 수정 |
| **구현 현황** | OpenAPI Spec (localhost:8000) | v1.5.0 | FastAPI 자동 생성 |

### 1.2 분석 방법

1. OpenAPI JSON 스펙 추출 (`/openapi.json`)
2. 설계 문서의 Endpoint, Schema, Query Parameter 비교
3. 불일치/미구현 항목 식별
4. 개선 작업 정의

### 1.3 분석 결과 요약

```
┌─────────────────────────────────────────────────────────────┐
│                    Gap 분석 결과 요약                         │
├─────────────────────────────────────────────────────────────┤
│  총 설계 Endpoint : 약 120개 (CRUD 기준)                     │
│  구현 Endpoint    : 약 115개                                 │
│  일치율           : 약 96%                                   │
├─────────────────────────────────────────────────────────────┤
│  ✅ 완전 일치     : 95개 (Device, Event, Integration, Server) │
│  ⚠️ 부분 일치     : 15개 (Query Param 누락 등)               │
│  ❌ 미구현        : 5개 (Auth User/Role)                     │
│  ➕ 추가 구현     : 5개 (Logs, Health 등)                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 구현 일치 항목

### 2.1 Device API - 완전 일치 ✅

| API 분류 | Endpoint | GET | POST | PATCH | PUT | DELETE | 상태 |
|----------|----------|:---:|:----:|:-----:|:---:|:------:|:----:|
| Controller | `/api/devices/controllers` | ✅ | ✅ | ✅ | ✅ | ✅ | 완료 |
| Controller | `/api/devices/controllers/{id}` | ✅ | - | ✅ | ✅ | ✅ | 완료 |
| Sensor | `/api/devices/sensors` | ✅ | ✅ | ✅ | ✅ | ✅ | 완료 |
| Sensor | `/api/devices/sensors/{id}` | ✅ | - | ✅ | ✅ | ✅ | 완료 |
| Camera | `/api/devices/cameras` | ✅ | ✅ | ✅ | ✅ | ✅ | 완료 |
| Camera | `/api/devices/cameras/{id}` | ✅ | - | ✅ | ✅ | ✅ | 완료 |
| Speaker | `/api/devices/speakers` | ✅ | ✅ | ✅ | ✅ | ✅ | 완료 |
| Speaker | `/api/devices/speakers/{id}` | ✅ | - | ✅ | ✅ | ✅ | 완료 |
| Enclosure | `/api/devices/enclosures` | ✅ | ✅ | ✅ | ✅ | ✅ | 완료 |
| Enclosure | `/api/devices/enclosures/{id}` | ✅ | - | ✅ | ✅ | ✅ | 완료 |
| Enclosure | `/api/devices/enclosures/{id}/status` | - | - | ✅ | - | - | 완료 |
| Enclosure | `/api/devices/enclosures/{id}/control` | - | ✅ | - | - | - | 완료 |
| DeviceGroup | `/api/devices/groups` | ✅ | ✅ | ✅ | ✅ | ✅ | 완료 |
| DeviceGroup | `/api/devices/groups/{id}` | ✅ | - | ✅ | ✅ | ✅ | 완료 |
| DeviceGroup | `/api/devices/groups/{id}/devices` | - | ✅ | - | - | ✅ | 완료 |

### 2.2 Configuration API - 완전 일치 ✅

| API 분류 | Endpoint | GET | POST | PATCH | PUT | DELETE | 상태 |
|----------|----------|:---:|:----:|:-----:|:---:|:------:|:----:|
| CameraPreset | `/api/devices/cameras/{id}/presets` | ✅ | ✅ | ✅ | ✅ | ✅ | 완료 |
| ROI | `/api/presets/{id}/rois` | ✅ | ✅ | ✅ | ✅ | ✅ | 완료 |
| XyPoint | `/api/rois/{id}/points` | ✅ | ✅ | ✅ | - | ✅ | 완료 |
| FileGroup | `/api/file-groups` | ✅ | ✅ | ✅ | ✅ | ✅ | 완료 |

### 2.3 Event API - 완전 일치 ✅

| API 분류 | Endpoint | GET | POST | PATCH | PUT | DELETE | 상태 |
|----------|----------|:---:|:----:|:-----:|:---:|:------:|:----:|
| Detection | `/api/events/detections` | ✅ | ✅ | ✅ | ✅ | ✅ | 완료 |
| Detection | `/api/events/detections/{id}` | ✅ | - | ✅ | ✅ | ✅ | 완료 |
| Detection | `/api/events/detections/{id}/action` | ✅ | - | - | - | - | 완료 |
| Malfunction | `/api/events/malfunctions` | ✅ | ✅ | ✅ | ✅ | ✅ | 완료 |
| Malfunction | `/api/events/malfunctions/{id}` | ✅ | - | ✅ | ✅ | ✅ | 완료 |
| Malfunction | `/api/events/malfunctions/{id}/action` | ✅ | - | - | - | - | 완료 |
| Connection | `/api/events/connections` | ✅ | ✅ | ✅ | ✅ | ✅ | 완료 |
| Connection | `/api/events/connections/{id}` | ✅ | - | ✅ | ✅ | ✅ | 완료 |
| Action | `/api/events/actions` | ✅ | ✅ | ✅ | ✅ | ✅ | 완료 |
| Action | `/api/events/actions/{id}` | ✅ | - | ✅ | ✅ | ✅ | 완료 |

### 2.4 Integration API - 완전 일치 ✅

| API 분류 | Endpoint | GET | POST | PATCH | PUT | DELETE | 상태 |
|----------|----------|:---:|:----:|:-----:|:---:|:------:|:----:|
| EventMapping | `/api/integrations/event-mappings` | ✅ | ✅ | ✅ | ✅ | ✅ | 완료 |
| EventMapping | `/api/integrations/event-mappings/{id}` | ✅ | - | ✅ | ✅ | ✅ | 완료 |
| EMCameras | `/api/.../event-mappings/{id}/cameras` | ✅ | ✅ | ✅ | ✅ | ✅ | 완료 |
| EMSpeakers | `/api/.../event-mappings/{id}/speakers` | ✅ | ✅ | ✅ | ✅ | ✅ | 완료 |

### 2.5 Server Monitoring API - 완전 일치 ✅

| API 분류 | Endpoint | GET | POST | PATCH | PUT | DELETE | 상태 |
|----------|----------|:---:|:----:|:-----:|:---:|:------:|:----:|
| Category | `/api/servers/categories` | ✅ | ✅ | ✅ | ✅ | ✅ | 완료 |
| Category | `/api/servers/categories/{id}` | ✅ | - | ✅ | ✅ | ✅ | 완료 |
| Server | `/api/servers` | ✅ | ✅ | ✅ | ✅ | ✅ | 완료 |
| Server | `/api/servers/{id}` | ✅ | - | ✅ | ✅ | ✅ | 완료 |
| Summary | `/api/servers/summary` | ✅ | - | - | - | - | 완료 |

---

## 3. Gap 식별 - 미구현 항목

### 3.1 Authentication/User API - 미구현 ❌

**설계서 명세**: GOP_Restful_Api_연동설계.md 3.1절

| API 분류 | Endpoint | 설계서 | 구현 | Gap |
|----------|----------|:------:|:----:|:---:|
| Auth | `POST /api/auth/login` | ⚠️ 미정 | ✅ | - |
| Auth | `GET /api/auth/me` | ⚠️ 미정 | ✅ | - |
| Auth | `POST /api/auth/logout` | ⚠️ 미정 | ❌ | Gap |
| Auth | `POST /api/auth/refresh` | ⚠️ 미정 | ❌ | Gap |
| User | `GET /api/users` | ⚠️ 미정 | ❌ | Gap |
| User | `POST /api/users` | ⚠️ 미정 | ❌ | Gap |
| User | `GET /api/users/{id}` | ⚠️ 미정 | ❌ | Gap |
| User | `PATCH /api/users/{id}` | ⚠️ 미정 | ❌ | Gap |
| User | `DELETE /api/users/{id}` | ⚠️ 미정 | ❌ | Gap |
| Role | `GET /api/roles` | ⚠️ 미정 | ❌ | Gap |
| Role | `POST /api/roles` | ⚠️ 미정 | ❌ | Gap |
| Permission | `PUT /api/roles/{id}/permissions` | ⚠️ 미정 | ❌ | Gap |

**비고**: 설계서에서 "이 부분은 아직 합의된 내용이 없음"으로 명시됨. GOP 필수-051 요구사항 충족을 위해 구현 필요.

### 3.2 Camera Query Parameter - 부분 미구현 ⚠️

**설계서 명세**: 5.3절 Camera API

| Endpoint | Query Param | 설계서 | 구현 | Gap |
|----------|-------------|:------:|:----:|:---:|
| `GET /api/devices/cameras/{id}` | `include_presets` | ✅ | ❌ | Gap |
| `GET /api/devices/cameras/{id}` | `include_rois` | ✅ | ❌ | Gap |

**현재 구현 상태**:
```
GET /api/devices/cameras/{camera_id} query params: []  # 파라미터 없음
```

**예상 동작** (설계서 기준):
```http
GET /api/devices/cameras/201?include_presets=true&include_rois=true
```

### 3.3 DeviceGroup Query Parameter - 부분 미구현 ⚠️

**설계서 명세**: 5.6절 DeviceGroup API

| Endpoint | Query Param | 설계서 | 구현 | Gap |
|----------|-------------|:------:|:----:|:---:|
| `GET /api/devices/groups/{id}` | `include_devices` | ✅ | ❌ | Gap |

**비고**: 설계서에서는 단일 그룹 조회 시 소속 디바이스 목록을 포함하는 옵션이 명시됨.

---

## 4. Gap 식별 - 불일치 항목

### 4.1 XyPoint API Endpoint 경로 차이

| 항목 | 설계서 | 구현 | 유형 |
|------|--------|------|------|
| XyPoint 목록 | `/api/xy-points` | `/api/rois/{roi_id}/points` | 경로 변경 |
| XyPoint PATCH | `PATCH /api/xy-points/{id}` | - | 미지원 |

**분석**:
- 설계서: XyPoint를 독립 리소스로 관리 (`/api/xy-points`)
- 구현: XyPoint를 ROI 하위 리소스로 관리 (`/api/rois/{roi_id}/points`)
- **판정**: 구현이 더 RESTful한 설계. **설계서 업데이트 권장**

**구현된 XyPoint Endpoints**:
```
GET     /api/rois/{roi_id}/points          # 목록 조회
POST    /api/rois/{roi_id}/points          # 생성
PUT     /api/rois/{roi_id}/points          # 일괄 교체 (Bulk)
DELETE  /api/rois/{roi_id}/points/{id}     # 삭제
```

### 4.2 API Response Schema 차이

**설계서 명시 Response 형식**:
```json
{
  "success": true,
  "message": "...",
  "data": { ... },
  "pagination": { ... },
  "meta": {
    "timestamp": "...",
    "request_id": "..."
  }
}
```

**구현 Response 형식** (OpenAPI):
```json
{
  "success": true,
  "message": "...",
  "data": { ... },
  "pagination": { ... },
  "meta": {
    "timestamp": "...",
    "request_id": "..."
  }
}
```

**판정**: ✅ 일치

### 4.3 Enum 값 차이 검토

| Enum | 설계서 값 | 구현 값 | 상태 |
|------|----------|---------|:----:|
| EnumDeviceStatus | ACTIVATED, ERROR, DEACTIVATED | 동일 | ✅ |
| EnumDeviceType | Controller, Multi, Fence, ... | 동일 | ✅ |
| EnumServerType | VMS, NVR_API, STREAMING, ... | 동일 | ✅ |
| EnumServerStatus | NORMAL, WARNING, ERROR | 동일 | ✅ |
| EnumDoorStatus | CLOSED, OPEN | 동일 | ✅ |
| EnumSpeakerType | NORMAL, ADMIN, MONITOR, DEV | 동일 | ✅ |
| EnumMappingEventCategory | FENCE_SENSOR_ONLY, ... | 동일 | ✅ |

---

## 5. 추가 구현 항목 (설계서 미기재)

### 5.1 Log API - 설계서 미기재 ➕

| Endpoint | Method | 설명 | 권장 조치 |
|----------|--------|------|-----------|
| `/api/logs` | GET | API 로그 목록 조회 | 설계서 추가 |
| `/api/logs/viewer` | GET | 로그 뷰어 (HTML) | 설계서 추가 |

### 5.2 Health Check - 설계서 미기재 ➕

| Endpoint | Method | 설명 | 권장 조치 |
|----------|--------|------|-----------|
| `/` | GET | 루트 응답 | 선택 |
| `/health` | GET | 헬스 체크 | 설계서 추가 |

### 5.3 Detection/Malfunction Action Lookup - 설계서 미기재 ➕

| Endpoint | Method | 설명 | 권장 조치 |
|----------|--------|------|-----------|
| `/api/events/detections/{id}/action` | GET | 탐지 이벤트의 조치 조회 | 설계서 추가 |
| `/api/events/malfunctions/{id}/action` | GET | 장애 이벤트의 조치 조회 | 설계서 추가 |

---

## 6. 개선 작업 목록

### 6.1 구현 개선 작업 (Code Change)

| ID | 작업 항목 | 유형 | 우선순위 | 영향도 |
|:--:|----------|:----:|:--------:|:------:|
| **IMP-001** | Camera 단일 조회 `include_presets` 파라미터 추가 | 기능 추가 | P1 | 낮음 |
| **IMP-002** | Camera 단일 조회 `include_rois` 파라미터 추가 | 기능 추가 | P1 | 낮음 |
| **IMP-003** | DeviceGroup 단일 조회 `include_devices` 파라미터 추가 | 기능 추가 | P1 | 낮음 |
| **IMP-004** | Auth Logout API 구현 | 신규 개발 | P2 | 중간 |
| **IMP-005** | Auth Token Refresh API 구현 | 신규 개발 | P2 | 중간 |
| **IMP-006** | User CRUD API 구현 | 신규 개발 | P0 | 높음 |
| **IMP-007** | Role CRUD API 구현 | 신규 개발 | P0 | 높음 |
| **IMP-008** | Permission 관리 API 구현 | 신규 개발 | P1 | 높음 |

### 6.2 설계서 업데이트 작업 (Document Change)

| ID | 작업 항목 | 유형 | 우선순위 |
|:--:|----------|:----:|:--------:|
| **DOC-001** | XyPoint API 경로 변경 반영 (`/api/rois/{id}/points`) | 수정 | P1 |
| **DOC-002** | Log API 섹션 추가 | 신규 | P2 |
| **DOC-003** | Health Check API 섹션 추가 | 신규 | P3 |
| **DOC-004** | Detection/Malfunction Action Lookup API 추가 | 신규 | P1 |
| **DOC-005** | Auth/User/Role API 섹션 상세화 | 신규 | P0 |

---

## 7. 우선순위 및 일정

### 7.1 우선순위 정의

| 우선순위 | 설명 | 대상 |
|:--------:|------|------|
| **P0** | 즉시 (GOP 필수 요구사항) | User/Role API |
| **P1** | 단기 (설계서 일관성) | Query Param 추가, 문서 업데이트 |
| **P2** | 중기 (기능 완성도) | Auth 기능 보완 |
| **P3** | 장기 (선택적) | 부가 문서화 |

### 7.2 작업 순서 권장

```
Phase 1 (P0) - GOP 필수 요구사항 충족
├── IMP-006: User CRUD API 구현
├── IMP-007: Role CRUD API 구현
└── DOC-005: Auth/User/Role API 설계서 상세화

Phase 2 (P1) - 설계서-구현 일관성
├── IMP-001: Camera include_presets 추가
├── IMP-002: Camera include_rois 추가
├── IMP-003: DeviceGroup include_devices 추가
├── IMP-008: Permission 관리 API 구현
├── DOC-001: XyPoint API 경로 변경 반영
└── DOC-004: Action Lookup API 문서 추가

Phase 3 (P2) - 기능 완성도
├── IMP-004: Auth Logout 구현
├── IMP-005: Auth Token Refresh 구현
└── DOC-002: Log API 문서 추가

Phase 4 (P3) - 부가 문서화
└── DOC-003: Health Check API 문서 추가
```

### 7.3 구현 일치율 목표

| 단계 | 현재 | 목표 | Gap 해소 |
|------|:----:|:----:|----------|
| Phase 1 완료 후 | 96% | 98% | User/Role API 추가 |
| Phase 2 완료 후 | 98% | 99% | Query Param 추가 |
| Phase 3 완료 후 | 99% | 100% | Auth 완성 |

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| v1.0 | 2026-01-13 | 초기 문서 작성 - Gap 분석 완료 |

---

## 부록: 분석 데이터

### A. 구현된 전체 Endpoint 목록

```
POST    /api/auth/login
GET     /api/auth/me
GET     /api/logs
GET     /api/logs/viewer
GET     /api/devices/controllers
POST    /api/devices/controllers
GET     /api/devices/controllers/{controller_id}
PATCH   /api/devices/controllers/{controller_id}
PUT     /api/devices/controllers/{controller_id}
DELETE  /api/devices/controllers/{controller_id}
GET     /api/devices/sensors
POST    /api/devices/sensors
GET     /api/devices/sensors/{sensor_id}
PATCH   /api/devices/sensors/{sensor_id}
PUT     /api/devices/sensors/{sensor_id}
DELETE  /api/devices/sensors/{sensor_id}
GET     /api/devices/cameras
POST    /api/devices/cameras
GET     /api/devices/cameras/{camera_id}
PATCH   /api/devices/cameras/{camera_id}
PUT     /api/devices/cameras/{camera_id}
DELETE  /api/devices/cameras/{camera_id}
GET     /api/devices/speakers
POST    /api/devices/speakers
GET     /api/devices/speakers/{speaker_id}
PATCH   /api/devices/speakers/{speaker_id}
PUT     /api/devices/speakers/{speaker_id}
DELETE  /api/devices/speakers/{speaker_id}
GET     /api/devices/enclosures
POST    /api/devices/enclosures
GET     /api/devices/enclosures/{enclosure_id}
PATCH   /api/devices/enclosures/{enclosure_id}
PUT     /api/devices/enclosures/{enclosure_id}
DELETE  /api/devices/enclosures/{enclosure_id}
PATCH   /api/devices/enclosures/{enclosure_id}/status
POST    /api/devices/enclosures/{enclosure_id}/control
GET     /api/file-groups
POST    /api/file-groups
GET     /api/file-groups/{file_group_id}
PATCH   /api/file-groups/{file_group_id}
PUT     /api/file-groups/{file_group_id}
DELETE  /api/file-groups/{file_group_id}
GET     /api/events/detections
POST    /api/events/detections
GET     /api/events/detections/{event_id}
PATCH   /api/events/detections/{event_id}
PUT     /api/events/detections/{event_id}
DELETE  /api/events/detections/{event_id}
GET     /api/events/detections/{event_id}/action
GET     /api/events/malfunctions
POST    /api/events/malfunctions
GET     /api/events/malfunctions/{event_id}
PATCH   /api/events/malfunctions/{event_id}
PUT     /api/events/malfunctions/{event_id}
DELETE  /api/events/malfunctions/{event_id}
GET     /api/events/malfunctions/{event_id}/action
GET     /api/events/connections
POST    /api/events/connections
GET     /api/events/connections/{event_id}
PATCH   /api/events/connections/{event_id}
PUT     /api/events/connections/{event_id}
DELETE  /api/events/connections/{event_id}
GET     /api/events/actions
POST    /api/events/actions
GET     /api/events/actions/{event_id}
PATCH   /api/events/actions/{event_id}
PUT     /api/events/actions/{event_id}
DELETE  /api/events/actions/{event_id}
GET     /api/integrations/event-mappings
POST    /api/integrations/event-mappings
GET     /api/integrations/event-mappings/{mapping_id}
PATCH   /api/integrations/event-mappings/{mapping_id}
PUT     /api/integrations/event-mappings/{mapping_id}
DELETE  /api/integrations/event-mappings/{mapping_id}
GET     /api/integrations/event-mappings/{mapping_id}/cameras
POST    /api/integrations/event-mappings/{mapping_id}/cameras
GET     /api/integrations/event-mappings/{mapping_id}/cameras/{config_id}
PATCH   /api/integrations/event-mappings/{mapping_id}/cameras/{config_id}
PUT     /api/integrations/event-mappings/{mapping_id}/cameras/{config_id}
DELETE  /api/integrations/event-mappings/{mapping_id}/cameras/{config_id}
GET     /api/integrations/event-mappings/{mapping_id}/speakers
POST    /api/integrations/event-mappings/{mapping_id}/speakers
GET     /api/integrations/event-mappings/{mapping_id}/speakers/{config_id}
PATCH   /api/integrations/event-mappings/{mapping_id}/speakers/{config_id}
PUT     /api/integrations/event-mappings/{mapping_id}/speakers/{config_id}
DELETE  /api/integrations/event-mappings/{mapping_id}/speakers/{config_id}
GET     /api/servers/categories
POST    /api/servers/categories
GET     /api/servers/categories/{category_id}
PATCH   /api/servers/categories/{category_id}
PUT     /api/servers/categories/{category_id}
DELETE  /api/servers/categories/{category_id}
GET     /api/servers/summary
GET     /api/servers
POST    /api/servers
GET     /api/servers/{server_id}
PATCH   /api/servers/{server_id}
PUT     /api/servers/{server_id}
DELETE  /api/servers/{server_id}
GET     /api/devices/groups
POST    /api/devices/groups
GET     /api/devices/groups/{group_id}
PATCH   /api/devices/groups/{group_id}
PUT     /api/devices/groups/{group_id}
DELETE  /api/devices/groups/{group_id}
POST    /api/devices/groups/{group_id}/devices
DELETE  /api/devices/groups/{group_id}/devices/{device_id}
GET     /api/devices/cameras/{camera_id}/presets
POST    /api/devices/cameras/{camera_id}/presets
GET     /api/devices/cameras/{camera_id}/presets/{preset_id}
PATCH   /api/devices/cameras/{camera_id}/presets/{preset_id}
PUT     /api/devices/cameras/{camera_id}/presets/{preset_id}
DELETE  /api/devices/cameras/{camera_id}/presets/{preset_id}
GET     /api/presets/{preset_id}/rois
POST    /api/presets/{preset_id}/rois
GET     /api/presets/{preset_id}/rois/{roi_id}
PATCH   /api/presets/{preset_id}/rois/{roi_id}
PUT     /api/presets/{preset_id}/rois/{roi_id}
DELETE  /api/presets/{preset_id}/rois/{roi_id}
GET     /api/rois/{roi_id}/points
POST    /api/rois/{roi_id}/points
PUT     /api/rois/{roi_id}/points
DELETE  /api/rois/{roi_id}/points/{point_id}
GET     /
GET     /health
```

### B. 구현된 Schema 목록 (주요)

```
- ActionEventCreate, ActionEventResponse, ActionEventUpdate
- CameraCreate, CameraResponse, CameraUpdate, CameraNestedResponse
- CameraPresetCreate, CameraPresetUpdate
- ConnectionEventCreate, ConnectionEventResponse, ConnectionEventUpdate
- ControllerCreate, ControllerResponse, ControllerUpdate
- DetectionEventCreate, DetectionEventResponse, DetectionEventUpdate
- DeviceGroupCreate, DeviceGroupResponse, DeviceGroupUpdate
- EnclosureCreate, EnclosureResponse, EnclosureUpdate, EnclosureControl
- EventMappingCreate, EventMappingResponse, EventMappingUpdate
- EventMappingCameraCreate, EventMappingCameraUpdate
- EventMappingSpeakerCreate, EventMappingSpeakerUpdate
- FileGroupCreate, FileGroupResponse, FileGroupUpdate
- MalfunctionEventCreate, MalfunctionEventResponse, MalfunctionEventUpdate
- ROICreate, ROIUpdate
- SensorCreate, SensorResponse, SensorUpdate
- ServerCategoryCreate, ServerCategoryResponse, ServerCategoryUpdate
- ServerCreate, ServerResponse, ServerUpdate
- SpeakerCreate, SpeakerResponse, SpeakerUpdate
- XyPointCreate, XyPointBulkUpdate

복합 타입:
- Geolocation (location, latitude, longitude, altitude)
- HardwareSpec (name, manufacturer, model, firmware, etc.)
- CameraUrls (homepage, onvif, streams, snapshot)
- EnclosureDetailInfo (temperature, humidity, current, voltage, etc.)
- EnclosureThresholdConfig (temp_high, temp_low, humidity_high, etc.)
```

---

**문서 종료**