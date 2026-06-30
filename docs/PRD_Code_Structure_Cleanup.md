# PRD: 코드 구조 정리 (모델/스키마/라우터 통합)

**버전**: v1.0
**작성일**: 2026-01-08
**상태**: Completed
**완료일**: 2026-01-08

---

## 1. 개요

### 1.1 배경

현재 코드베이스에 다음과 같은 구조적 문제가 있음:

1. **레거시 모델 잔존**: `CameraEventMapping`, `CameraEventPreset`가 `integration.py`에 남아있지만, 실제로는 `EventMapping` + `EventMappingCamera`로 대체됨
2. **파일 분리 불일치**: `EventMappingCamera`가 `event_mapping_camera.py`로 분리되어 있지만, 논리적으로 `integration.py`에 속해야 함
3. **Device 계열 분산**: `Speaker`가 Device의 polymorphic child인데 별도 파일(`speaker.py`)로 분리됨
4. **스키마 파일 분산**: 모델 구조와 스키마 파일 구조가 불일치

### 1.2 목표

1. 레거시 모델/스키마/라우터 제거
2. 관련 모델을 논리적 그룹으로 통합
3. 코드 구조 일관성 확보
4. 문서 업데이트

---

## 2. 현재 구조 분석

### 2.1 Models (app/models/)

| 파일명 | 내용 | 상태 |
|--------|------|------|
| `device.py` | Device, Controller, Sensor, Camera | **유지** |
| `speaker.py` | Speaker (Device child) | **통합 대상** → device.py |
| `event.py` | Event, DetectionEvent, MalfunctionEvent, ConnectionEvent, ActionEvent | **유지** |
| `integration.py` | EventMapping, CameraEventMapping(레거시), CameraEventPreset(레거시) | **정리 필요** |
| `event_mapping_camera.py` | EventMappingCamera | **통합 대상** → integration.py |
| `camera_preset.py` | CameraPreset | **유지** |
| `device_group.py` | DeviceGroup, DeviceGroupMapping | **유지** |
| `server.py` | Server, ServerCategory | **유지** |
| `file_group.py` | FileGroup | **유지** |
| `log.py` | ApiLog | **유지** |
| `user.py` | User | **유지** |

### 2.2 Schemas (app/schemas/)

| 파일명 | 내용 | 상태 |
|--------|------|------|
| `device.py` | Device, Controller, Sensor, Camera 스키마 | **유지** |
| `speaker.py` | Speaker 스키마 | **통합 대상** → device.py |
| `event.py` | Event 스키마 | **유지** |
| `integration.py` | EventMapping, CameraEventMapping(레거시) 스키마 | **정리 필요** |
| `event_mapping_camera.py` | EventMappingCamera 스키마 | **통합 대상** → integration.py |
| `camera_preset.py` | CameraPreset 스키마 | **유지** |
| `device_group.py` | DeviceGroup 스키마 | **유지** |
| `server.py` | Server 스키마 | **유지** |
| `file_group.py` | FileGroup 스키마 | **유지** |
| `log.py` | ApiLog 스키마 | **유지** |
| `user.py` | User 스키마 | **유지** |
| `common.py` | 공통 스키마 | **유지** |

### 2.3 Routers (app/routers/)

| 파일명 | 엔드포인트 | 상태 |
|--------|-----------|------|
| `cameras.py` | `/api/devices/cameras` | **유지** |
| `controllers.py` | `/api/devices/controllers` | **유지** |
| `sensors.py` | `/api/devices/sensors` | **유지** |
| `speakers.py` | `/api/devices/speakers` | **유지** |
| `event_mappings.py` | `/api/integrations/event-mappings` | **유지** |
| `event_mapping_cameras.py` | `/api/integrations/event-mappings/{id}/cameras` | **유지** |
| `camera_presets.py` | `/api/devices/cameras/{id}/presets` | **유지** |
| `device_groups.py` | `/api/device-groups` | **유지** |
| `detections.py` | `/api/events/detections` | **유지** |
| `malfunctions.py` | `/api/events/malfunctions` | **유지** |
| `connections.py` | `/api/events/connections` | **유지** |
| `actions.py` | `/api/events/actions` | **유지** |
| `servers.py` | `/api/servers` | **유지** |
| `server_categories.py` | `/api/server-categories` | **유지** |
| `file_groups.py` | `/api/file-groups` | **유지** |
| `rois.py` | `/api/devices/cameras/{id}/rois` | **유지** |
| `xypoints.py` | `/api/devices/cameras/{id}/rois/{id}/points` | **유지** |
| `logs.py` | `/api/logs` | **유지** |
| `auth.py` | `/api/auth` | **유지** |

---

## 3. 변경 계획

### 3.1 레거시 제거

#### 3.1.1 CameraEventMapping 레거시 제거

**삭제 대상 (app/models/integration.py)**:
```python
# 삭제
class CameraEventMapping(Base):
    ...

# 삭제
class CameraEventPreset(Base):
    ...
```

**삭제 대상 (app/schemas/integration.py)**:
```python
# CameraEventMapping 관련 스키마 삭제
```

**삭제 대상 (app/routers/)**:
- `camera_event_mappings.py` (존재하는 경우) - 레거시 라우터

**DB 테이블**:
- `camera_event_mappings` - 데이터 마이그레이션 후 삭제
- `camera_event_presets` - 데이터 마이그레이션 후 삭제

### 3.2 모델 통합

#### 3.2.1 Speaker → device.py 통합

**변경 전**:
```
app/models/
├── device.py        # Device, Controller, Sensor, Camera
└── speaker.py       # Speaker (별도 파일)
```

**변경 후**:
```
app/models/
└── device.py        # Device, Controller, Sensor, Camera, Speaker
```

**작업**:
1. `speaker.py` 내용을 `device.py`로 이동
2. `speaker.py` 파일 삭제
3. import 경로 업데이트

#### 3.2.2 EventMappingCamera → integration.py 통합

**변경 전**:
```
app/models/
├── integration.py           # EventMapping, CameraEventMapping(레거시), CameraEventPreset(레거시)
└── event_mapping_camera.py  # EventMappingCamera (별도 파일)
```

**변경 후**:
```
app/models/
└── integration.py           # EventMapping, EventMappingCamera
```

**작업**:
1. `event_mapping_camera.py` 내용을 `integration.py`로 이동
2. `event_mapping_camera.py` 파일 삭제
3. 레거시 `CameraEventMapping`, `CameraEventPreset` 삭제
4. import 경로 업데이트

### 3.3 스키마 통합

#### 3.3.1 Speaker 스키마 → device.py 통합

**변경 전**:
```
app/schemas/
├── device.py        # Device, Controller, Sensor, Camera 스키마
└── speaker.py       # Speaker 스키마 (별도 파일)
```

**변경 후**:
```
app/schemas/
└── device.py        # Device, Controller, Sensor, Camera, Speaker 스키마
```

#### 3.3.2 EventMappingCamera 스키마 → integration.py 통합

**변경 전**:
```
app/schemas/
├── integration.py           # EventMapping, CameraEventMapping(레거시) 스키마
└── event_mapping_camera.py  # EventMappingCamera 스키마 (별도 파일)
```

**변경 후**:
```
app/schemas/
└── integration.py           # EventMapping, EventMappingCamera 스키마
```

---

## 4. 최종 구조

### 4.1 Models (app/models/)

```
app/models/
├── __init__.py
├── device.py              # Device(Base), Controller, Sensor, Camera, Speaker
├── event.py               # Event(Base), DetectionEvent, MalfunctionEvent, ConnectionEvent, ActionEvent
├── integration.py         # EventMapping, EventMappingCamera
├── camera_preset.py       # CameraPreset
├── device_group.py        # DeviceGroup, DeviceGroupMapping
├── server.py              # Server, ServerCategory
├── file_group.py          # FileGroup
├── log.py                 # ApiLog
└── user.py                # User
```

### 4.2 Schemas (app/schemas/)

```
app/schemas/
├── __init__.py
├── device.py              # Device, Controller, Sensor, Camera, Speaker 스키마
├── event.py               # Event 스키마
├── integration.py         # EventMapping, EventMappingCamera 스키마
├── camera_preset.py       # CameraPreset 스키마
├── device_group.py        # DeviceGroup 스키마
├── server.py              # Server 스키마
├── file_group.py          # FileGroup 스키마
├── log.py                 # ApiLog 스키마
├── user.py                # User 스키마
└── common.py              # 공통 스키마
```

### 4.3 Routers (변경 없음)

라우터는 현재 구조 유지 (API 엔드포인트 변경 없음)

---

## 5. 마이그레이션 계획

### 5.1 데이터 마이그레이션

레거시 테이블 데이터 마이그레이션:
- `camera_event_mappings` → 필요 시 `event_mappings` + `event_mapping_cameras`로 변환
- `camera_event_presets` → 삭제 (EventMappingCamera가 camera_presets 직접 참조)

### 5.2 DB 스키마 정리

```sql
-- 레거시 테이블 삭제 (데이터 마이그레이션 후)
DROP TABLE IF EXISTS camera_event_presets;
DROP TABLE IF EXISTS camera_event_mappings;
```

---

## 6. 구현 순서

### Phase 1: 레거시 제거
1. CameraEventMapping, CameraEventPreset 모델 삭제 (integration.py)
2. 관련 스키마 삭제 (schemas/integration.py)
3. import 경로 정리
4. 테스트 실행

### Phase 2: Speaker 통합
1. Speaker 모델을 device.py로 이동
2. Speaker 스키마를 schemas/device.py로 이동
3. speaker.py 파일 삭제 (models/, schemas/)
4. import 경로 업데이트
5. 테스트 실행

### Phase 3: EventMappingCamera 통합
1. EventMappingCamera 모델을 integration.py로 이동
2. EventMappingCamera 스키마를 schemas/integration.py로 이동
3. event_mapping_camera.py 파일 삭제 (models/, schemas/)
4. import 경로 업데이트
5. 테스트 실행

### Phase 4: __init__.py 정리
1. models/__init__.py 업데이트
2. schemas/__init__.py 업데이트
3. 전체 테스트 실행

### Phase 5: 문서 업데이트
1. GOP_스키마_전체.md 업데이트
2. 기타 관련 문서 업데이트

---

## 7. Breaking Changes

| 항목 | 변경 내용 | 영향 |
|------|----------|------|
| import 경로 | `from app.models.speaker import Speaker` → `from app.models.device import Speaker` | 내부 코드만 영향 |
| import 경로 | `from app.models.event_mapping_camera import EventMappingCamera` → `from app.models.integration import EventMappingCamera` | 내부 코드만 영향 |
| DB 테이블 | `camera_event_mappings`, `camera_event_presets` 삭제 | 레거시 데이터 손실 가능 |

**API 변경 없음**: 외부 API 엔드포인트는 변경되지 않음

---

## 8. 파일 삭제 목록

### 8.1 삭제 예정 파일

| 파일 | 사유 |
|------|------|
| `app/models/speaker.py` | device.py로 통합 |
| `app/models/event_mapping_camera.py` | integration.py로 통합 |
| `app/schemas/speaker.py` | device.py로 통합 |
| `app/schemas/event_mapping_camera.py` | integration.py로 통합 |

### 8.2 삭제 예정 코드

| 파일 | 삭제 대상 |
|------|----------|
| `app/models/integration.py` | `CameraEventMapping`, `CameraEventPreset` 클래스 |
| `app/schemas/integration.py` | CameraEventMapping 관련 스키마 |

---

## 9. 테스트 계획

### 9.1 단위 테스트
- [x] Device, Controller, Sensor, Camera, Speaker 모델 테스트 (31 passed)
- [x] EventMapping, EventMappingCamera 모델 테스트 (69 passed)
- [x] 모든 스키마 테스트 (66 passed)

### 9.2 API 테스트
- [x] Speaker API 정상 동작 확인
- [x] EventMapping API 정상 동작 확인
- [x] EventMappingCamera API 정상 동작 확인

### 9.3 Import 테스트
- [x] 모든 라우터의 import 경로 정상 동작 확인 (App loaded successfully)

---

## 10. 참고 자료

### 10.1 현재 의존성

**Speaker 모델 사용처**:
- `app/routers/speakers.py`
- `app/schemas/speaker.py`
- `app/models/__init__.py`

**EventMappingCamera 모델 사용처**:
- `app/routers/event_mapping_cameras.py`
- `app/schemas/event_mapping_camera.py`
- `app/models/__init__.py`
- `app/models/integration.py` (EventMapping.cameras relationship)

### 10.2 관련 문서

- `docs/GOP_스키마_전체.md`
- `GOP_Restful_Api_연동설계.md`
- `docs/PRD_Speaker_Device.md`
- `docs/PRD_CameraEventMapping_Refactoring.md`
