# PRD: API 코드 표준화 가이드

**Version**: 1.0
**Date**: 2026-01-14
**Status**: Draft

---

## 1. 개요

### 1.1 목적

이 문서는 GOP API 서버의 코드 일관성을 확보하기 위한 표준화 가이드입니다.
다음 3가지 영역의 문제점을 분석하고 해결 방안을 제시합니다:

1. **Swagger API 설명 (Docstring) 형식 표준화**
2. **Schema 코드 형식 일관성**
3. **Device 관련 파일 구조 통합**

### 1.2 현재 문제점 요약

| 영역 | 문제점 | 영향 |
|------|--------|------|
| Router Docstrings | 4가지 다른 형식 혼재 | Swagger 문서 일관성 저하 |
| Schema 코드 | Field 사용법 불일치 | 코드 가독성 저하 |
| 파일 구조 | Enclosure 스키마 분리 | 유지보수 복잡성 증가 |

---

## 2. Swagger API 설명 (Docstring) 표준화

### 2.1 현황 분석

22개 라우터 파일에서 4가지 다른 docstring 패턴이 발견됨:

#### Pattern A: controllers.py 스타일 (권장 X)
```python
"""
제어기 목록 조회 (페이지네이션)

제어기 목록을 페이지네이션하여 조회합니다.

- **page**: 페이지 번호 (기본값: 1)
- **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)

**Response**: 제어기 목록 및 페이지네이션 정보
"""
```
- 파라미터 앞에 섹션 헤더 없음

#### Pattern B: sensors.py 스타일 (권장 O)
```python
"""
센서 목록 조회 (페이지네이션)

센서 목록을 페이지네이션하여 조회합니다. 다양한 필터 옵션을 지원합니다.

**파라미터**:
- **page**: 페이지 번호 (기본값: 1)
- **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)

**Response**: 센서 목록 및 페이지네이션 정보

**Error**:
- 404: 센서를 찾을 수 없음
"""
```
- 섹션 헤더 사용 (파라미터, Response, Error)

#### Pattern C: enclosures.py 스타일 (권장 X)
```python
"""
함체 목록 조회 (페이지네이션)

함체 목록을 페이지네이션하여 조회합니다.

- **page**: 페이지 번호 (기본값: 1)

**Response**: 함체 목록 및 페이지네이션 정보
"""
```
- 섹션 헤더 불규칙적 사용

#### Pattern D: device_groups.py 스타일 (고급)
```python
@router.get(
    "",
    response_model=ApiResponse[list[DeviceGroupResponse]],
    responses={
        200: {
            "description": "디바이스 그룹 목록 조회 성공",
            "content": {
                "application/json": {
                    "example": {...}
                }
            }
        },
        422: {...}
    }
)
```
- OpenAPI `responses={}` 데코레이터 사용
- Swagger에 예제 응답 표시

### 2.2 라우터별 현황

| Router 파일 | Pattern | 섹션 헤더 | OpenAPI responses | 일관성 |
|------------|---------|----------|-------------------|--------|
| controllers.py | A | 부분적 | X | 중 |
| sensors.py | B | **파라미터**: | X | 상 |
| cameras.py | B | **파라미터**: | X | 상 |
| speakers.py | A | - 리스트만 | X | 중 |
| enclosures.py | C | 혼합 | X | 하 |
| device_groups.py | D | 혼합 | O | 상 |
| event_mappings.py | B | **파라미터**: | X | 상 |
| detections.py | B | 예상 | X | - |
| camera_presets.py | - | - | X | - |
| rois.py | - | - | X | - |
| servers.py | - | - | X | - |

### 2.3 표준 Docstring 형식 (권장)

```python
@router.get("", response_model=ApiResponse[list[EntityResponse]])
async def get_entities(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    # ...
):
    """
    [제목] - 간결한 기능 요약 (한 줄)

    [상세 설명] - 기능에 대한 추가 설명 (1-2문장)

    **파라미터**:
    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 항목 수 (기본값: 20, 최대: 100)
    - **filter_name**: 필터 설명 (선택)

    **Request Body** (POST/PUT/PATCH만):
    - **field1**: 필드 설명 (필수)
    - **field2**: 필드 설명 (선택)

    **Response**: 응답 데이터 설명

    **Error**:
    - 404: 리소스를 찾을 수 없음
    - 422: 유효하지 않은 입력값

    **PRD Reference**: PRD_문서명.md (해당 시)
    """
```

### 2.4 OpenAPI 예제 추가 표준

중요 API (목록 조회, 생성)에는 `responses={}` 데코레이터 사용:

```python
@router.get(
    "",
    response_model=ApiResponse[list[EntityResponse]],
    responses={
        200: {
            "description": "조회 성공",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "조회 성공",
                        "data": [...],
                        "pagination": {"page": 1, "limit": 20, "total": 100, "total_pages": 5}
                    }
                }
            }
        }
    }
)
```

---

## 3. Schema 코드 형식 일관성

### 3.1 현황 분석

12개 스키마 파일에서 발견된 불일치:

#### 3.1.1 Field 정의 방식

**일관된 방식 (device.py):**
```python
class ControllerCreate(BaseModel):
    number_device: int = Field(..., description="장치 번호")
    name_device: str = Field(..., max_length=200, description="장치 이름")
    version: str = Field(..., max_length=50, description="버전")
    is_enable: bool = Field(True, description="장비 활성화 여부")
```

**불일치 발견 (일부 파일):**
```python
# 문제 1: Field 없이 타입만 사용
number_device: int  # description 없음

# 문제 2: default 위치 불일치
status: str = Field(default="ACTIVATED", description="...")  # default 키워드
status: str = Field("ACTIVATED", description="...")  # 위치 인자

# 문제 3: Optional 표기 혼용
version: Optional[str] = Field(None, description="...")
version: str | None = Field(None, description="...")  # Python 3.10+ 문법
```

#### 3.1.2 Docstring 형식

**상세 문서화 (device.py):**
```python
class DeviceNestedResponse(BaseModel):
    """
    폴리모픽 Device nested response 스키마

    Event 응답에서 Device 정보를 nested 객체로 반환할 때 사용합니다.

    공통 필드:
        id, number_device, group_device, name_device, type_device, version, status

    Controller 전용:
        ip_address, ip_port

    PRD Reference: PRD_Event_Api_Refactoring.md v1.2
    """
```

**최소 문서화 (일부 파일):**
```python
class SomeSchema(BaseModel):
    """Schema for some entity"""  # 단순 한 줄
```

### 3.2 스키마 파일별 현황

| Schema 파일 | Field 일관성 | Docstring 품질 | ConfigDict | PRD 참조 |
|-------------|--------------|----------------|------------|----------|
| device.py | O | 상세 | O | O |
| enclosure.py | O | 상세 | O | O |
| event.py | O | 상세 | O | O |
| camera_preset.py | O | 중간 | O | 부분 |
| device_group.py | O | 중간 | O | 부분 |
| integration.py | O | 중간 | O | O |
| server.py | 확인필요 | - | - | - |
| file_group.py | 확인필요 | - | - | - |
| common.py | O | 간단 | O | X |
| user.py | - | - | - | - |
| log.py | - | - | - | - |

### 3.3 표준 Schema 형식 (권장)

```python
"""
[모듈명] schemas: [Entity1], [Entity2], ...

PRD: [관련_PRD문서.md] - [섹션 번호]
- [주요 변경사항/기능 설명]
"""
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, List


class EntityCreate(BaseModel):
    """
    [Entity] 생성 스키마

    [추가 설명 - 용도, 제약사항 등]

    PRD: [관련_PRD.md] Section X.X
    """
    # 필수 필드 (...)
    required_field: int = Field(..., description="필드 설명")
    required_str: str = Field(..., max_length=200, description="필드 설명")

    # 선택 필드 (기본값)
    optional_field: Optional[str] = Field(None, description="필드 설명")
    bool_field: bool = Field(True, description="필드 설명")

    # 중첩 타입
    nested: Optional[NestedSchema] = Field(None, description="중첩 객체 설명")

    model_config = ConfigDict(from_attributes=True)


class EntityResponse(BaseModel):
    """
    [Entity] 응답 스키마

    [응답 데이터 구조 설명]
    """
    id: int = Field(..., description="Entity ID")
    # ... 필드들
    created_at: datetime = Field(..., description="생성 일시")
    updated_at: datetime = Field(..., description="수정 일시")

    model_config = ConfigDict(from_attributes=True)


class EntityUpdate(BaseModel):
    """
    [Entity] 수정 스키마 (PATCH)

    모든 필드가 선택적입니다. 제공된 필드만 업데이트됩니다.
    """
    # 모든 필드 Optional
    field1: Optional[int] = Field(None, description="필드 설명")
    field2: Optional[str] = Field(None, description="필드 설명")

    model_config = ConfigDict(from_attributes=True)
```

---

## 4. Device 관련 파일 구조 통합

### 4.1 현황 분석

Device 관련 파일이 3개 레이어에 걸쳐 분산되어 있음:

#### Models Layer (`app/models/`)
```
device.py  ← Controller, Sensor, Camera, Speaker, Enclosure 모두 포함 (통합)
```

#### Schemas Layer (`app/schemas/`)
```
device.py     ← Controller*, Sensor*, Camera*, Speaker* 스키마
enclosure.py  ← Enclosure* 스키마 (별도 파일) ⚠️ 불일치
```

#### Routers Layer (`app/routers/`)
```
controllers.py   ← /api/devices/controllers
sensors.py       ← /api/devices/sensors
cameras.py       ← /api/devices/cameras
speakers.py      ← /api/devices/speakers
enclosures.py    ← /api/devices/enclosures
```

### 4.2 문제점

1. **스키마 파일 불일치**
   - Speaker 스키마: `device.py`에 포함
   - Enclosure 스키마: `enclosure.py`로 분리
   - 일관성 없음 → 새 개발자 혼란

2. **파일 크기 문제**
   - `device.py` (schema): 706 lines - 점점 커짐
   - 모든 Device 스키마를 한 파일에 넣으면 관리 어려움

3. **순환 참조 위험**
   - Nested Response 스키마 간 상호 참조
   - `TYPE_CHECKING`으로 해결 중이지만 복잡

### 4.3 권장 구조 옵션

#### Option A: 현재 구조 유지 + Enclosure 통합 (권장)

**장점**: 최소 변경, 기존 패턴 유지
**단점**: device.py 파일 계속 커짐

```
app/schemas/
├── device.py           # 모든 Device 스키마 (Controller, Sensor, Camera, Speaker, Enclosure)
├── device_group.py     # DeviceGroup 관련
├── event.py            # Event 관련
└── ...
```

**변경 사항**:
- `enclosure.py` 내용을 `device.py`로 이동
- Import 경로 업데이트

#### Option B: Device 타입별 파일 분리 (대규모)

**장점**: 파일 크기 관리, 명확한 분리
**단점**: 많은 파일 변경 필요

```
app/schemas/
├── device/
│   ├── __init__.py        # Re-export all
│   ├── base.py            # 공통 스키마 (Geolocation, HardwareSpec, etc.)
│   ├── controller.py      # Controller* 스키마
│   ├── sensor.py          # Sensor* 스키마
│   ├── camera.py          # Camera* 스키마
│   ├── speaker.py         # Speaker* 스키마
│   └── enclosure.py       # Enclosure* 스키마
├── device_group.py
├── event.py
└── ...
```

#### Option C: 현재 구조 + 명확한 규칙

**장점**: 변경 없음, 규칙만 문서화
**단점**: 불일치 유지

```
규칙:
- 복잡한 Device (Enclosure): 별도 파일
- 단순한 Device (Speaker): device.py에 포함
```

### 4.4 권장 구현 방안

**Option A 선택** - Enclosure 스키마를 device.py로 통합

**이유**:
1. 모델 레이어(device.py)와 일관성 유지
2. 최소한의 코드 변경
3. 현재 Speaker 패턴과 동일하게 맞춤

**구현 단계**:
1. `enclosure.py` 내용을 `device.py` 끝에 복사
2. Import 구문 정리 (중복 제거)
3. `enclosure.py` import 사용처 변경
   - `app/routers/enclosures.py`
4. `enclosure.py` 파일 삭제 또는 re-export용으로 유지
5. 테스트 실행 및 검증

---

## 5. 구현 계획

### Phase 1: Docstring 표준화 (우선순위: 중)

| Task | 파일 | 예상 작업 |
|------|------|----------|
| 1.1 | controllers.py | 섹션 헤더 추가 |
| 1.2 | speakers.py | 섹션 헤더 추가 |
| 1.3 | enclosures.py | 형식 통일 |
| 1.4 | 기타 라우터 | 형식 검토 및 수정 |

### Phase 2: Schema 표준화 (우선순위: 하)

| Task | 파일 | 작업 내용 |
|------|------|----------|
| 2.1 | 전체 스키마 | Field 사용법 검토 |
| 2.2 | 전체 스키마 | Docstring 품질 개선 |
| 2.3 | 전체 스키마 | ConfigDict 확인 |

### Phase 3: 파일 구조 통합 (우선순위: 중)

| Task | 작업 내용 |
|------|----------|
| 3.1 | enclosure.py → device.py 이동 |
| 3.2 | Import 경로 업데이트 |
| 3.3 | 테스트 실행 |
| 3.4 | enclosure.py 정리 |

---

## 6. 참조 문서

- `PRD_Swagger_OpenAPI_Examples.md` - OpenAPI 예제 적용 방법
- `GOP_Restful_Api_연동설계.md` - API 스펙 원본
- `PRD_Device_Structure_Refactoring.md` - Device 구조 설계

---

## Appendix A: 전체 라우터 파일 목록

```
app/routers/
├── auth.py                    # 인증
├── logs.py                    # 로그
├── controllers.py             # Device - Controller
├── sensors.py                 # Device - Sensor
├── cameras.py                 # Device - Camera
├── speakers.py                # Device - Speaker
├── enclosures.py              # Device - Enclosure
├── device_groups.py           # DeviceGroup
├── camera_presets.py          # Camera Preset
├── rois.py                    # ROI
├── xypoints.py                # XyPoint
├── detections.py              # Event - Detection
├── malfunctions.py            # Event - Malfunction
├── connections.py             # Event - Connection
├── actions.py                 # Event - Action
├── event_mappings.py          # EventMapping
├── event_mapping_cameras.py   # EventMappingCamera
├── event_mapping_speakers.py  # EventMappingSpeaker
├── servers.py                 # Server
├── server_categories.py       # ServerCategory
└── file_groups.py             # FileGroup
```

## Appendix B: 전체 스키마 파일 목록

```
app/schemas/
├── __init__.py
├── common.py          # ApiResponse, PaginationMeta, etc.
├── device.py          # Controller, Sensor, Camera, Speaker schemas
├── enclosure.py       # Enclosure schemas (통합 대상)
├── device_group.py    # DeviceGroup schemas
├── camera_preset.py   # CameraPreset, ROI, XyPoint schemas
├── event.py           # Detection, Malfunction, Connection, Action schemas
├── integration.py     # EventMapping, EventMappingCamera, EventMappingSpeaker schemas
├── server.py          # Server, ServerCategory schemas
├── file_group.py      # FileGroup schemas
├── user.py            # User schemas
└── log.py             # Log schemas
```
