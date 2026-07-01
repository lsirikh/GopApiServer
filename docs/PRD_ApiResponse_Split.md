# PRD: ApiResponse 분리 — 단건 응답에서 pagination 제거

**작성일**: 2026-02-09
**변경 유형**: 구조 변경 (Structural)

---

## 1. 배경 및 목적

### 1.1 문제

현재 모든 API 엔드포인트가 동일한 `ApiResponse[T]` 제네릭 클래스를 사용한다. 이 클래스에는 `pagination: Optional[PaginationMeta] = None` 필드가 포함되어 있어, **단건 조회(GET by ID), 생성(POST), 수정(PATCH/PUT), 삭제(DELETE)** 등 pagination이 불필요한 엔드포인트에서도 Swagger/Redoc 문서에 `pagination` 속성이 노출된다.

```python
# 현재 구조 — app/schemas/common.py
class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str
    data: T
    pagination: Optional[PaginationMeta] = None  # ← 단건에서도 노출
    meta: ResponseMeta = Field(default_factory=ResponseMeta)
```

**영향**: Swagger UI, Redoc, OpenAPI JSON/YAML 문서에서 ~99개 단건 엔드포인트의 응답 스키마에 불필요한 `pagination` 객체가 표시되어, 클라이언트 개발자에게 혼란을 줄 수 있다.

### 1.2 목표

- **단건 응답**: `pagination` 필드 없는 `ApiSingleResponse[T]` 사용
- **목록 응답**: 기존 `ApiResponse[T]` 유지 (pagination 포함)
- **런타임 영향 없음**: 실제 JSON 응답 내용은 변하지 않음 (현재도 단건은 `pagination: null`)
- **Swagger/Redoc 정확성**: 단건 엔드포인트에서 pagination 스키마 제거

---

## 2. 스키마 변경

파일: `app/schemas/common.py`

### 2.1 신규 추가: ApiSingleResponse

```python
class ApiSingleResponse(BaseModel, Generic[T]):
    """Standard API response format for single-item endpoints (no pagination)"""
    success: bool = True
    message: str
    data: T
    meta: ResponseMeta = Field(default_factory=ResponseMeta)
```

### 2.2 기존 유지: ApiResponse (변경 없음)

```python
class ApiResponse(BaseModel, Generic[T]):
    """Standard API response format for list endpoints (with pagination)"""
    success: bool = True
    message: str
    data: T
    pagination: Optional[PaginationMeta] = None
    meta: ResponseMeta = Field(default_factory=ResponseMeta)
```

### 2.3 용도 구분

| 클래스 | 용도 | pagination | 사용 위치 |
|--------|------|-----------|-----------|
| `ApiResponse[T]` | 목록 조회 (GET list) | O (Optional) | `response_model=ApiResponse[list[...]]` |
| `ApiSingleResponse[T]` | 단건 (GET by ID, POST, PATCH, PUT, DELETE) | X | `response_model=ApiSingleResponse[...]` |

---

## 3. 엔드포인트 분류

### 3.1 목록 엔드포인트 — ApiResponse 유지 (21개)

pagination을 return문에서 실제로 사용하는 엔드포인트. **변경 없음**.

| # | Router | Method | Path | response_model |
|---|--------|--------|------|---------------|
| 1 | controllers | GET | /api/devices/controllers | `ApiResponse[list[ControllerResponse]]` |
| 2 | sensors | GET | /api/devices/sensors | `ApiResponse[list[SensorResponse]]` |
| 3 | cameras | GET | /api/devices/cameras | `ApiResponse[list[CameraResponse]]` |
| 4 | enclosures | GET | /api/devices/enclosures | `ApiResponse[list[EnclosureResponse]]` |
| 5 | speakers | GET | /api/devices/speakers | `ApiResponse[list[SpeakerResponse]]` |
| 6 | lamps | GET | /api/devices/lamps | `ApiResponse[list[LampResponse]]` |
| 7 | device_groups | GET | /api/device-groups | `ApiResponse[list[DeviceGroupResponse]]` |
| 8 | camera_presets | GET | /cameras/{id}/presets | `ApiResponse[CameraPresetListData]` |
| 9 | rois | GET | /presets/{id}/rois | `ApiResponse[ROIListData]` |
| 10 | xypoints | GET | /rois/{id}/points | `ApiResponse[XyPointListData]` |
| 11 | detections | GET | /api/events/detections | `ApiResponse[list[DetectionEventResponse]]` |
| 12 | malfunctions | GET | /api/events/malfunctions | `ApiResponse[list[MalfunctionEventResponse]]` |
| 13 | connections | GET | /api/events/connections | `ApiResponse[list[ConnectionEventResponse]]` |
| 14 | actions | GET | /api/events/actions | `ApiResponse[list[ActionEventResponse]]` |
| 15 | event_mappings | GET | /api/integrations/event-mappings | `ApiResponse[list[EventMappingResponse]]` |
| 16 | servers | GET | /api/servers | `ApiResponse[list[ServerResponse]]` |
| 17 | server_categories | GET | /api/servers/categories | `ApiResponse[list[ServerCategoryResponse]]` |
| 18 | file_groups | GET | /api/file-groups | `ApiResponse[list[FileGroupResponse]]` |
| 19 | audit_logs | GET | /api/audit-logs | `ApiResponse[List[AuditLogResponse]]` |
| 20 | config_change_logs | GET | /api/config-change-logs | `ApiResponse[list[ConfigChangeLogResponse]]` |
| 21 | logs | GET | /api/logs | `ApiResponse[list[ApiLogResponse]]` |

### 3.2 단건 엔드포인트 — ApiSingleResponse로 변경 대상

pagination을 사용하지 않는 모든 엔드포인트. `response_model`의 `ApiResponse` → `ApiSingleResponse` 변경 + return문의 `ApiResponse(` → `ApiSingleResponse(` 변경.

#### controllers (5개)

| Method | Path | 현재 response_model |
|--------|------|-------------------|
| GET | /{controller_id} | `ApiResponse[ControllerResponse]` |
| POST | / | `ApiResponse[ControllerResponse]` |
| PATCH | /{controller_id} | `ApiResponse[ControllerResponse]` |
| PUT | /{controller_id} | `ApiResponse[ControllerResponse]` |
| DELETE | /{controller_id} | `ApiResponse[None]` |

#### sensors (5개)

| Method | Path | 현재 response_model |
|--------|------|-------------------|
| GET | /{sensor_id} | `ApiResponse[SensorResponse]` |
| POST | / | `ApiResponse[SensorResponse]` |
| PATCH | /{sensor_id} | `ApiResponse[SensorResponse]` |
| PUT | /{sensor_id} | `ApiResponse[SensorResponse]` |
| DELETE | /{sensor_id} | `ApiResponse[None]` |

#### cameras (5개)

| Method | Path | 현재 response_model |
|--------|------|-------------------|
| GET | /{camera_id} | *(response_model 없음 — return문만 변경)* |
| POST | / | `ApiResponse[CameraResponse]` |
| PATCH | /{camera_id} | `ApiResponse[CameraResponse]` |
| PUT | /{camera_id} | `ApiResponse[CameraResponse]` |
| DELETE | /{camera_id} | `ApiResponse[None]` |

#### enclosures (7개)

| Method | Path | 현재 response_model |
|--------|------|-------------------|
| GET | /{enclosure_id} | `ApiResponse[EnclosureResponse]` |
| POST | / | `ApiResponse[EnclosureResponse]` |
| PATCH | /{enclosure_id} | `ApiResponse[EnclosureResponse]` |
| PUT | /{enclosure_id} | `ApiResponse[EnclosureResponse]` |
| DELETE | /{enclosure_id} | `ApiResponse[None]` |
| PATCH | /{enclosure_id}/status | `ApiResponse[EnclosureResponse]` |
| POST | /{enclosure_id}/control | `ApiResponse[EnclosureResponse]` |

#### speakers (5개)

| Method | Path | 현재 response_model |
|--------|------|-------------------|
| GET | /{speaker_id} | `ApiResponse[SpeakerResponse]` |
| POST | / | `ApiResponse[SpeakerResponse]` |
| PATCH | /{speaker_id} | `ApiResponse[SpeakerResponse]` |
| PUT | /{speaker_id} | `ApiResponse[SpeakerResponse]` |
| DELETE | /{speaker_id} | `ApiResponse[None]` |

#### lamps (5개)

| Method | Path | 현재 response_model |
|--------|------|-------------------|
| GET | /{lamp_id} | `ApiResponse[LampResponse]` |
| POST | / | `ApiResponse[LampResponse]` |
| PATCH | /{lamp_id} | `ApiResponse[LampResponse]` |
| PUT | /{lamp_id} | `ApiResponse[LampResponse]` |
| DELETE | /{lamp_id} | `ApiResponse[dict]` |

#### camera_presets (5개)

| Method | Path | 현재 response_model |
|--------|------|-------------------|
| GET | /{camera_id}/presets/{preset_id} | `ApiResponse[CameraPresetDetailResponse]` |
| POST | /{camera_id}/presets | `ApiResponse[CameraPresetResponse]` |
| PATCH | /{camera_id}/presets/{preset_id} | `ApiResponse[CameraPresetResponse]` |
| PUT | /{camera_id}/presets/{preset_id} | `ApiResponse[CameraPresetResponse]` |
| DELETE | /{camera_id}/presets/{preset_id} | `ApiResponse[None]` |

#### rois (5개)

| Method | Path | 현재 response_model |
|--------|------|-------------------|
| GET | /{preset_id}/rois/{roi_id} | `ApiResponse[ROIDetailResponse]` |
| POST | /{preset_id}/rois | `ApiResponse[ROIResponse]` |
| PATCH | /{preset_id}/rois/{roi_id} | `ApiResponse[ROIResponse]` |
| PUT | /{preset_id}/rois/{roi_id} | `ApiResponse[ROIResponse]` |
| DELETE | /{preset_id}/rois/{roi_id} | `ApiResponse[None]` |

#### xypoints (3개)

| Method | Path | 현재 response_model |
|--------|------|-------------------|
| POST | /{roi_id}/points | `ApiResponse[XyPointListItem]` |
| PUT | /{roi_id}/points | `ApiResponse[XyPointBulkReplaceData]` |
| DELETE | /{roi_id}/points/{point_id} | `ApiResponse[None]` |

#### camera_settings (3개)

| Method | Path | 현재 response_model |
|--------|------|-------------------|
| GET | /{camera_id}/settings | `ApiResponse[CameraSettingResponse]` |
| PATCH | /{camera_id}/settings | `ApiResponse[CameraSettingResponse]` |
| PUT | /{camera_id}/settings | `ApiResponse[CameraSettingResponse]` |

#### proxy_settings (3개)

| Method | Path | 현재 response_model |
|--------|------|-------------------|
| GET | /{server_id}/proxy-settings | `ApiResponse[ProxySettingResponse]` |
| PATCH | /{server_id}/proxy-settings | `ApiResponse[ProxySettingResponse]` |
| PUT | /{server_id}/proxy-settings | `ApiResponse[ProxySettingResponse]` |

#### detections (6개)

| Method | Path | 현재 response_model |
|--------|------|-------------------|
| GET | /{event_id} | `ApiResponse[DetectionEventResponse]` |
| POST | / | `ApiResponse[DetectionEventResponse]` |
| PATCH | /{event_id} | `ApiResponse[DetectionEventResponse]` |
| PUT | /{event_id} | `ApiResponse[DetectionEventResponse]` |
| DELETE | /{event_id} | `ApiResponse[Optional[dict]]` |
| GET | /{event_id}/action | `ApiResponse[ActionEventResponse]` |

#### malfunctions (6개)

| Method | Path | 현재 response_model |
|--------|------|-------------------|
| GET | /{event_id} | `ApiResponse[MalfunctionEventResponse]` |
| POST | / | `ApiResponse[MalfunctionEventResponse]` |
| PATCH | /{event_id} | `ApiResponse[MalfunctionEventResponse]` |
| PUT | /{event_id} | `ApiResponse[MalfunctionEventResponse]` |
| DELETE | /{event_id} | `ApiResponse[Optional[dict]]` |
| GET | /{event_id}/action | `ApiResponse[ActionEventResponse]` |

#### connections (5개)

| Method | Path | 현재 response_model |
|--------|------|-------------------|
| GET | /{event_id} | `ApiResponse[ConnectionEventResponse]` |
| POST | / | `ApiResponse[ConnectionEventResponse]` |
| PATCH | /{event_id} | `ApiResponse[ConnectionEventResponse]` |
| PUT | /{event_id} | `ApiResponse[ConnectionEventResponse]` |
| DELETE | /{event_id} | `ApiResponse[Optional[dict]]` |

#### actions (5개)

| Method | Path | 현재 response_model |
|--------|------|-------------------|
| GET | /{event_id} | `ApiResponse[ActionEventResponse]` |
| POST | / | `ApiResponse[ActionEventResponse]` |
| PATCH | /{event_id} | `ApiResponse[ActionEventResponse]` |
| PUT | /{event_id} | `ApiResponse[ActionEventResponse]` |
| DELETE | /{event_id} | `ApiResponse[Optional[dict]]` |

#### event_mappings (5개)

| Method | Path | 현재 response_model |
|--------|------|-------------------|
| GET | /{mapping_id} | `ApiResponse[EventMappingResponse]` |
| POST | / | `ApiResponse[EventMappingResponse]` |
| PATCH | /{mapping_id} | `ApiResponse[EventMappingResponse]` |
| PUT | /{mapping_id} | `ApiResponse[EventMappingResponse]` |
| DELETE | /{mapping_id} | `ApiResponse[None]` |

#### device_groups (6개)

| Method | Path | 현재 response_model |
|--------|------|-------------------|
| POST | / | `ApiResponse[DeviceGroupResponse]` |
| PATCH | /{group_id} | `ApiResponse[DeviceGroupResponse]` |
| PUT | /{group_id} | `ApiResponse[DeviceGroupResponse]` |
| DELETE | /{group_id} | `ApiResponse[dict]` |
| POST | /{group_id}/devices | `ApiResponse[DeviceAssignResponse]` |
| DELETE | /{group_id}/devices/{device_id} | `ApiResponse[DeviceRemoveResponse]` |

#### servers (7개)

| Method | Path | 현재 response_model |
|--------|------|-------------------|
| GET | /summary | `ApiResponse[list[ServerCategorySummary]]` |
| GET | /{server_id} | `ApiResponse[ServerResponse]` |
| GET | /{server_id}/system-events | *(response_model 없음 — return문만 변경)* |
| POST | / | `ApiResponse[ServerResponse]` |
| PATCH | /{server_id} | `ApiResponse[ServerResponse]` |
| PUT | /{server_id} | `ApiResponse[ServerResponse]` |
| DELETE | /{server_id} | `ApiResponse[dict]` |

#### server_categories (5개)

| Method | Path | 현재 response_model |
|--------|------|-------------------|
| GET | /{category_id} | `ApiResponse[ServerCategoryWithServers]` |
| POST | / | `ApiResponse[ServerCategoryResponse]` |
| PATCH | /{category_id} | `ApiResponse[ServerCategoryResponse]` |
| PUT | /{category_id} | `ApiResponse[ServerCategoryResponse]` |
| DELETE | /{category_id} | `ApiResponse[dict]` |

#### server_metrics (4개)

| Method | Path | 현재 response_model |
|--------|------|-------------------|
| POST | /{server_id}/metrics | `ApiResponse[ServerMetricsResponse]` |
| GET | /{server_id}/metrics | `ApiResponse[list[ServerMetricsResponse]]` |
| GET | /{server_id}/metrics/latest | `ApiResponse[ServerMetricsLatestResponse]` |
| DELETE | /{server_id}/metrics | `ApiResponse[dict]` |

#### file_groups (5개)

| Method | Path | 현재 response_model |
|--------|------|-------------------|
| GET | /{file_group_id} | `ApiResponse[FileGroupResponse]` |
| POST | / | `ApiResponse[FileGroupResponse]` |
| PATCH | /{file_group_id} | `ApiResponse[FileGroupResponse]` |
| PUT | /{file_group_id} | `ApiResponse[FileGroupResponse]` |
| DELETE | /{file_group_id} | `ApiResponse` |

#### audit_logs (1개)

| Method | Path | 현재 response_model |
|--------|------|-------------------|
| GET | /{log_id} | `ApiResponse[AuditLogResponse]` |

#### config_change_logs (1개)

| Method | Path | 현재 response_model |
|--------|------|-------------------|
| GET | /{log_id} | `ApiResponse[ConfigChangeLogResponse]` |

**단건 엔드포인트 합계: ~99개**

### 3.3 ApiResponse를 사용하지 않는 라우터 (변경 불필요)

다음 라우터는 `ApiResponse`를 사용하지 않으므로 본 작업 범위에서 제외한다.

| Router | 설명 |
|--------|------|
| `auth.py` | 자체 응답 스키마 (Token, AccountUserResponse 등) |
| `users.py` | 자체 응답 스키마 |
| `user_groups.py` | 자체 응답 스키마 |
| `user_sessions.py` | 자체 응답 스키마 |
| `reports.py` | 자체 응답 스키마 (response_model 없음, dict 반환) |
| `system_events.py` | 자체 응답 스키마 (ApiResponse 미사용) |
| `enclosure_metrics.py` | 자체 응답 스키마 |
| `event_mapping_cameras.py` | ApiResponse 미사용 |
| `event_mapping_speakers.py` | ApiResponse 미사용 |
| `event_mapping_lamps.py` | ApiResponse 미사용 |

---

## 4. 라우터별 변경 상세

각 라우터 파일에서 수행할 작업은 동일하다:

### 4.1 import 변경

```python
# Before
from app.schemas.common import ApiResponse

# After (목록+단건 모두 있는 라우터)
from app.schemas.common import ApiResponse, ApiSingleResponse

# After (단건만 있는 라우터)
from app.schemas.common import ApiSingleResponse
```

### 4.2 response_model 변경

```python
# Before
@router.get("/{id}", response_model=ApiResponse[SomeResponse])

# After
@router.get("/{id}", response_model=ApiSingleResponse[SomeResponse])
```

### 4.3 return문 변경

```python
# Before
return ApiResponse(success=True, message="...", data=...)

# After
return ApiSingleResponse(success=True, message="...", data=...)
```

### 4.4 import 변경 라우터 분류

**ApiResponse + ApiSingleResponse 둘 다 import** (목록 GET + 단건 CRUD 모두 있는 라우터):

| Router 파일 | 목록 | 단건 |
|------------|------|------|
| controllers.py | 1 | 5 |
| sensors.py | 1 | 5 |
| cameras.py | 1 | 5 |
| enclosures.py | 1 | 7 |
| speakers.py | 1 | 5 |
| lamps.py | 1 | 5 |
| camera_presets.py | 1 | 5 |
| rois.py | 1 | 5 |
| xypoints.py | 1 | 3 |
| detections.py | 1 | 6 |
| malfunctions.py | 1 | 6 |
| connections.py | 1 | 5 |
| actions.py | 1 | 5 |
| event_mappings.py | 1 | 5 |
| device_groups.py | 1 | 6 |
| servers.py | 1 | 7 |
| server_categories.py | 1 | 5 |
| file_groups.py | 1 | 5 |
| audit_logs.py | 1 | 1 |
| config_change_logs.py | 1 | 1 |
| logs.py | 1 | 0 |

**ApiSingleResponse만 import** (단건만 있는 라우터):

| Router 파일 | 단건 |
|------------|------|
| camera_settings.py | 3 |
| proxy_settings.py | 3 |
| server_metrics.py | 4 |

---

## 5. 문서 업데이트

### 5.1 GOP_Restful_Api_연동설계.md (v3.7 유지 — 같은 날 변경 통합)

| 위치 | 작업 |
|------|------|
| 버전/날짜 | v3.7 유지 (2026-02-09) |
| Section 3.2 Response 형식 | "성공 응답 (200, 201)" 을 "단건 성공 응답 (200, 201)"과 "목록 성공 응답 (200)"으로 분리. 단건에서 pagination 없음을 명시 |
| Section 5~8 모든 단건 API Response 예시 | `"pagination": {...}` 속성 제거 확인 (현재 단건 예시에 pagination이 없으면 변경 불필요) |
| 부록 변경이력 | v3.7 엔트리에 내용 추가: "공통 응답 형식 분리 — 단건 응답(ApiSingleResponse)에서 pagination 제거" |

### 5.2 GOP_스키마_전체.md (v2.9 유지 — 같은 날 변경 통합)

이번 변경은 **DB 스키마에 영향 없음** (Pydantic 스키마 레벨 변경). 그러나 공통 응답 구조를 기록하는 섹션이 존재하지 않으므로 **변경 불필요**. 다만 기준 API 버전 참조가 이미 v3.7이므로 변경 없음.

| 위치 | 작업 |
|------|------|
| 버전/날짜 | v2.9 유지 (2026-02-09) |
| 기준 API 버전 | v3.7 유지 (변경 없음) |
| Section 13 변경 이력 | v2.9 엔트리에 내용 추가: "공통 응답 형식 분리 (ApiSingleResponse) 반영" |

### 5.3 문서 규칙 (공통)

- 해당하는 항목 위치의 내용을 업데이트하거나 추가한다
- 변경된 사항은 삭제한다
- 문서 초반에 날짜와 버전을 정리한다
- 부록 변경이력에 금일 해당 날짜에 전부 같은 버전으로 묶고 같은 날짜에 변경된 내용을 묶어서 정리한다
- PRD 참조 문구 제외

---

## 6. 수정 대상 파일 목록

| 구분 | 파일 | 작업 |
|------|------|------|
| **수정** | `app/schemas/common.py` | `ApiSingleResponse` 클래스 추가 |
| **수정** | `app/routers/controllers.py` | import 추가, 단건 5개 → ApiSingleResponse |
| **수정** | `app/routers/sensors.py` | import 추가, 단건 5개 → ApiSingleResponse |
| **수정** | `app/routers/cameras.py` | import 추가, 단건 5개 → ApiSingleResponse (GET by ID는 return문만 변경) |
| **수정** | `app/routers/enclosures.py` | import 추가, 단건 7개 → ApiSingleResponse |
| **수정** | `app/routers/speakers.py` | import 추가, 단건 5개 → ApiSingleResponse |
| **수정** | `app/routers/lamps.py` | import 추가, 단건 5개 → ApiSingleResponse |
| **수정** | `app/routers/camera_presets.py` | import 추가, 단건 5개 → ApiSingleResponse |
| **수정** | `app/routers/rois.py` | import 추가, 단건 5개 → ApiSingleResponse |
| **수정** | `app/routers/xypoints.py` | import 추가, 단건 3개 → ApiSingleResponse |
| **수정** | `app/routers/camera_settings.py` | import 변경 (ApiResponse → ApiSingleResponse), 3개 변경 |
| **수정** | `app/routers/proxy_settings.py` | import 변경 (ApiResponse → ApiSingleResponse), 3개 변경 |
| **수정** | `app/routers/detections.py` | import 추가, 단건 6개 → ApiSingleResponse |
| **수정** | `app/routers/malfunctions.py` | import 추가, 단건 6개 → ApiSingleResponse |
| **수정** | `app/routers/connections.py` | import 추가, 단건 5개 → ApiSingleResponse |
| **수정** | `app/routers/actions.py` | import 추가, 단건 5개 → ApiSingleResponse |
| **수정** | `app/routers/event_mappings.py` | import 추가, 단건 5개 → ApiSingleResponse |
| **수정** | `app/routers/device_groups.py` | import 추가, 단건 6개 → ApiSingleResponse |
| **수정** | `app/routers/servers.py` | import 추가, 단건 7개 → ApiSingleResponse (system-events는 return문만 변경) |
| **수정** | `app/routers/server_categories.py` | import 추가, 단건 5개 → ApiSingleResponse |
| **수정** | `app/routers/server_metrics.py` | import 변경, 단건 4개 → ApiSingleResponse |
| **수정** | `app/routers/file_groups.py` | import 추가, 단건 5개 → ApiSingleResponse |
| **수정** | `app/routers/audit_logs.py` | import 추가, 단건 1개 → ApiSingleResponse |
| **수정** | `app/routers/config_change_logs.py` | import 추가, 단건 1개 → ApiSingleResponse |
| **수정** | `GOP_Restful_Api_연동설계.md` | v3.7 통합: Section 3.2 응답 형식 분리, 부록 변경이력 |
| **수정** | `docs/GOP_스키마_전체.md` | v2.9 통합: 변경이력에 응답 형식 분리 내용 추가 |

---

## 7. TDD 실행 계획

### Phase 1: ApiSingleResponse 스키마 추가 (Structural)

- [ ] 1.1 TEST: ApiSingleResponse 클래스에 success, message, data, meta 필드 존재 확인
- [ ] 1.2 TEST: ApiSingleResponse 클래스에 pagination 필드 없음 확인
- [ ] 1.3 TEST: ApiResponse 클래스에 pagination 필드 여전히 존재 확인 (기존 유지)
- [ ] 1.4 IMPL: common.py에 ApiSingleResponse 추가
- [ ] 1.5 VERIFY: 테스트 통과

### Phase 2: Device 라우터 변경 (Structural)

- [ ] 2.1 IMPL: controllers.py — 단건 5개 엔드포인트 변경
- [ ] 2.2 IMPL: sensors.py — 단건 5개 엔드포인트 변경
- [ ] 2.3 IMPL: cameras.py — 단건 5개 엔드포인트 변경 (GET by ID는 return문만)
- [ ] 2.4 IMPL: enclosures.py — 단건 7개 엔드포인트 변경
- [ ] 2.5 IMPL: speakers.py — 단건 5개 엔드포인트 변경
- [ ] 2.6 IMPL: lamps.py — 단건 5개 엔드포인트 변경
- [ ] 2.7 VERIFY: 기존 테스트 전체 통과 (런타임 영향 없음 확인)

### Phase 3: Camera Preset/ROI/XyPoint 라우터 변경 (Structural)

- [ ] 3.1 IMPL: camera_presets.py — 단건 5개 엔드포인트 변경
- [ ] 3.2 IMPL: rois.py — 단건 5개 엔드포인트 변경
- [ ] 3.3 IMPL: xypoints.py — 단건 3개 엔드포인트 변경
- [ ] 3.4 VERIFY: 기존 테스트 전체 통과

### Phase 4: Device Setting 라우터 변경 (Structural)

- [ ] 4.1 IMPL: camera_settings.py — 3개 엔드포인트 변경 (import 완전 교체)
- [ ] 4.2 IMPL: proxy_settings.py — 3개 엔드포인트 변경 (import 완전 교체)
- [ ] 4.3 VERIFY: 기존 테스트 전체 통과

### Phase 5: Event 라우터 변경 (Structural)

- [ ] 5.1 IMPL: detections.py — 단건 6개 엔드포인트 변경
- [ ] 5.2 IMPL: malfunctions.py — 단건 6개 엔드포인트 변경
- [ ] 5.3 IMPL: connections.py — 단건 5개 엔드포인트 변경
- [ ] 5.4 IMPL: actions.py — 단건 5개 엔드포인트 변경
- [ ] 5.5 VERIFY: 기존 테스트 전체 통과

### Phase 6: Integration/DeviceGroup/Server 라우터 변경 (Structural)

- [ ] 6.1 IMPL: event_mappings.py — 단건 5개 엔드포인트 변경
- [ ] 6.2 IMPL: device_groups.py — 단건 6개 엔드포인트 변경
- [ ] 6.3 IMPL: servers.py — 단건 7개 엔드포인트 변경 (system-events는 return문만)
- [ ] 6.4 IMPL: server_categories.py — 단건 5개 엔드포인트 변경
- [ ] 6.5 IMPL: server_metrics.py — 단건 4개 엔드포인트 변경
- [ ] 6.6 IMPL: file_groups.py — 단건 5개 엔드포인트 변경
- [ ] 6.7 IMPL: audit_logs.py — 단건 1개 엔드포인트 변경
- [ ] 6.8 IMPL: config_change_logs.py — 단건 1개 엔드포인트 변경
- [ ] 6.9 VERIFY: 전체 테스트 수트 통과

### Phase 7: GOP_Restful_Api_연동설계.md 업데이트 (v3.7 통합)

- [ ] 7.1 IMPL: Section 3.2 Response 형식 — 단건/목록 분리
- [ ] 7.2 IMPL: 부록 변경이력 v3.7 엔트리에 내용 추가

### Phase 8: GOP_스키마_전체.md 업데이트 (v2.9 통합)

- [ ] 8.1 IMPL: Section 13 변경이력 v2.9 엔트리에 내용 추가

### Phase 9: 최종 검증 및 커밋

- [ ] 9.1 VERIFY: 전체 테스트 수트 통과
- [ ] 9.2 VERIFY: App import OK
- [ ] 9.3 COMMIT (structural): ApiSingleResponse 스키마 추가 + 전체 라우터 response_model 변경
- [ ] 9.4 COMMIT (docs): API 문서 v3.7 통합 + 스키마 문서 v2.9 통합 업데이트
