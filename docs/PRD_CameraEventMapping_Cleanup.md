# PRD: CameraEventMapping 레거시 코드 정리

**문서 버전**: v1.0
**작성일**: 2026-01-07
**상태**: 완료

---

## 1. 개요

### 1.1 목적

레거시 `CameraEventMapping` API를 제거하고, 새로운 `EventMappingCamera` API로 완전히 대체합니다.

### 1.2 배경

- **기존**: `CameraEventMapping` - 카메라별로 이벤트 매핑을 관리하는 구조
- **신규**: `EventMappingCamera` - EventMapping을 Base Node로 하여 카메라 동작을 관리하는 구조 (PRD_CameraEventMapping_Refactoring.md v2.1)

신규 API가 완성되었으므로 레거시 코드를 정리합니다.

---

## 2. 제거 대상

### 2.1 라우터 파일

| 파일 | 설명 | 액션 |
|------|------|------|
| `app/routers/camera_event_mappings.py` | 레거시 CameraEventMapping 라우터 | **삭제** |

### 2.2 main.py 변경

```python
# 제거할 import
from app.routers import camera_event_mappings

# 제거할 라우터 등록
app.include_router(camera_event_mappings.router, prefix="/api/integrations/camera-event-mappings", tags=["CameraEventMappings"])

# 제거할 태그 메타데이터
{
    "name": "CameraEventMappings",
    "description": "카메라 이벤트 매핑 API. 카메라별 이벤트 연동 설정을 관리합니다.",
}
```

### 2.3 Swagger 태그 변경

| 기존 | 신규 |
|------|------|
| `CameraEventMappings` | **제거** |
| `Event Mapping Cameras` | **유지** (위치 조정) |

---

## 3. 유지 대상

### 3.1 신규 API (유지)

| 파일 | 설명 |
|------|------|
| `app/routers/event_mapping_cameras.py` | EventMappingCamera 라우터 |
| `app/models/event_mapping_camera.py` | EventMappingCamera 모델 |
| `app/schemas/event_mapping_camera.py` | EventMappingCamera 스키마 |

### 3.2 레거시 모델/스키마 (유지 - 별도 정리 필요)

> **Note**: 모델과 스키마는 이번 정리 범위에서 제외합니다.
> DB 마이그레이션이 필요한 경우 별도 PRD로 진행합니다.

| 파일 | 설명 | 이번 액션 |
|------|------|----------|
| `app/models/integration.py` | CameraEventMapping 모델 포함 | 유지 |
| `app/schemas/integration.py` | CameraEventMapping 스키마 포함 | 유지 |

---

## 4. 실행 계획

### Phase 1: main.py 정리

1. `camera_event_mappings` import 제거
2. `CameraEventMappings` 태그 메타데이터 제거
3. `camera_event_mappings.router` 등록 제거
4. `Event Mapping Cameras` 태그 위치를 `Integration` 다음으로 이동

### Phase 2: 라우터 파일 삭제

1. `app/routers/camera_event_mappings.py` 파일 삭제

### Phase 3: 테스트 확인

1. 전체 테스트 실행하여 영향 확인
2. 필요시 레거시 테스트 파일 정리

---

## 5. 영향 분석

### 5.1 제거되는 API 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/integrations/camera-event-mappings` | 목록 조회 |
| GET | `/api/integrations/camera-event-mappings/{id}` | 단일 조회 |
| POST | `/api/integrations/camera-event-mappings` | 생성 |
| PATCH | `/api/integrations/camera-event-mappings/{id}` | 수정 |
| DELETE | `/api/integrations/camera-event-mappings/{id}` | 삭제 |

### 5.2 대체 API 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/integrations/event-mappings/{mapping_id}/cameras` | 목록 조회 |
| GET | `/api/integrations/event-mappings/{mapping_id}/cameras/{config_id}` | 단일 조회 |
| POST | `/api/integrations/event-mappings/{mapping_id}/cameras` | 생성 |
| PATCH | `/api/integrations/event-mappings/{mapping_id}/cameras/{config_id}` | 수정 |
| PUT | `/api/integrations/event-mappings/{mapping_id}/cameras/{config_id}` | 전체 교체 |
| DELETE | `/api/integrations/event-mappings/{mapping_id}/cameras/{config_id}` | 삭제 |

---

## 6. 체크리스트

- [x] Phase 1: main.py 정리
  - [x] import 제거
  - [x] 태그 메타데이터 제거
  - [x] 라우터 등록 제거
  - [x] 태그 위치 조정
- [x] Phase 2: 라우터 파일 삭제
  - [x] `app/routers/camera_event_mappings.py` 삭제
  - [x] `app/routers/__init__.py` 업데이트
- [x] Phase 3: 테스트 확인
  - [x] 전체 테스트 실행 (77/77 passed)
  - [ ] Swagger UI 확인 (수동 확인 필요)

---

## 7. 롤백 계획

Git을 통해 변경 전 상태로 복구 가능:

```bash
git checkout HEAD~1 -- app/main.py
git checkout HEAD~1 -- app/routers/camera_event_mappings.py
```

---

## 8. 승인

| 역할 | 이름 | 승인 |
|------|------|------|
| 작성자 | Claude | - |
| 승인자 | - | **대기** |

---

**승인 후 "go" 또는 "실행" 명령으로 작업을 시작합니다.**
