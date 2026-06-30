# PRD: Camera Preset & ROI Management

**문서 버전**: v1.2
**작성일**: 2025-12-31
**작성자**: Claude AI
**상태**: Draft

---

## 1. 개요

### 1.1 목적

카메라의 프리셋(Preset), ROI(Region of Interest), 좌표점(XyPoint)을 관리하는 API를 설계합니다.
PTZ 카메라의 프리셋 위치와 각 프리셋에서의 관심 영역(ROI)을 정의하고 관리할 수 있습니다.

### 1.2 범위

- Camera Preset CRUD API
- ROI CRUD API
- XyPoint CRUD API
- 계층 구조: Camera → Preset → ROI → XyPoint

### 1.3 용어 정의

| 용어 | 설명 |
|------|------|
| **Preset** | PTZ 카메라의 사전 정의된 위치/각도 설정. 투어링 시 이동할 위치 |
| **ROI** | Region of Interest. 영상 내 관심 영역을 다각형으로 정의 |
| **XyPoint** | ROI 다각형의 꼭지점 좌표 (정규화된 0.0~1.0 또는 픽셀 좌표) |
| **Touring Time** | Home 위치에서 해당 프리셋 위치로 이동하는 데 걸리는 시간 (초) |

---

## 2. 데이터 모델 설계

### 2.1 ERD (Entity Relationship Diagram)

```
┌─────────────┐       ┌─────────────────┐       ┌─────────────┐       ┌─────────────┐
│   Camera    │ 1   N │  CameraPreset   │ 1   N │     ROI     │ 1   N │   XyPoint   │
│─────────────│───────│─────────────────│───────│─────────────│───────│─────────────│
│ id (PK)     │       │ id (PK)         │       │ id (PK)     │       │ id (PK)     │
│ name_device │       │ camera_id (FK)  │       │ preset_id(FK│       │ roi_id (FK) │
│ ...         │       │ camera_name     │       │ name        │       │ x           │
└─────────────┘       │ preset_index    │       │ res_width   │       │ y           │
                      │ preset_name     │       │ res_height  │       │ order       │
                      │ touring_time    │       │ is_enable   │       │ created_at  │
                      │ created_at      │       │ created_at  │       │ updated_at  │
                      │ updated_at      │       │ updated_at  │       └─────────────┘
                      └─────────────────┘       └─────────────┘
```

### 2.2 테이블 상세 설계

#### 2.2.1 CameraPreset (camera_presets)

카메라의 프리셋 정보를 저장합니다.

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| `id` | INTEGER | PK, AUTO_INCREMENT | 프리셋 고유 ID |
| `camera_id` | INTEGER | FK → cameras.id, NOT NULL | 소속 카메라 ID |
| `camera_name` | VARCHAR(200) | NOT NULL | 카메라 이름 (참고용, 자동생성) |
| `preset_index` | INTEGER | NOT NULL | 프리셋 인덱스 (카메라 내 순번) |
| `preset_name` | VARCHAR(100) | NOT NULL | 프리셋 이름 |
| `touring_time` | INTEGER | NOT NULL, DEFAULT 10 | Home에서 해당 프리셋으로 이동하는 시간 (초) |
| `created_at` | DATETIME | NOT NULL | 생성 일시 |
| `updated_at` | DATETIME | NOT NULL | 수정 일시 |

**인덱스**:
- `idx_preset_camera_id` ON (camera_id)
- `UNIQUE idx_preset_camera_index` ON (camera_id, preset_index)

**관계**:
- `Camera` 1:N `CameraPreset` (CASCADE DELETE)
- `CameraPreset` 1:N `ROI` (CASCADE DELETE)

#### 2.2.2 ROI (rois)

프리셋 내 관심 영역(Region of Interest)을 저장합니다.

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| `id` | INTEGER | PK, AUTO_INCREMENT | ROI 고유 ID |
| `preset_id` | INTEGER | FK → camera_presets.id, NOT NULL | 소속 프리셋 ID |
| `name` | VARCHAR(100) | NOT NULL | ROI 이름 |
| `resolution_width` | FLOAT | NOT NULL | 해상도 너비 (픽셀 또는 비율) |
| `resolution_height` | FLOAT | NOT NULL | 해상도 높이 (픽셀 또는 비율) |
| `is_enable` | BOOLEAN | NOT NULL, DEFAULT TRUE | 활성화 여부 |
| `created_at` | DATETIME | NOT NULL | 생성 일시 |
| `updated_at` | DATETIME | NOT NULL | 수정 일시 |

**인덱스**:
- `idx_roi_preset_id` ON (preset_id)

**관계**:
- `CameraPreset` 1:N `ROI` (CASCADE DELETE)
- `ROI` 1:N `XyPoint` (CASCADE DELETE)

#### 2.2.3 XyPoint (xy_points)

ROI 다각형의 꼭지점 좌표를 저장합니다.

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| `id` | INTEGER | PK, AUTO_INCREMENT | 포인트 고유 ID |
| `roi_id` | INTEGER | FK → rois.id, NOT NULL | 소속 ROI ID |
| `x` | FLOAT | NOT NULL | X 좌표 (0.0 ~ 1.0 정규화 또는 픽셀) |
| `y` | FLOAT | NOT NULL | Y 좌표 (0.0 ~ 1.0 정규화 또는 픽셀) |
| `order` | INTEGER | NOT NULL | 점 순서 (다각형 그리기 순서) |
| `created_at` | DATETIME | NOT NULL | 생성 일시 |
| `updated_at` | DATETIME | NOT NULL | 수정 일시 |

**인덱스**:
- `idx_xypoint_roi_id` ON (roi_id)
- `UNIQUE idx_xypoint_roi_order` ON (roi_id, order)

**관계**:
- `ROI` 1:N `XyPoint` (CASCADE DELETE)

---

## 3. API 설계

### 3.1 API 엔드포인트 요약

#### CameraPreset API

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/devices/cameras/{camera_id}/presets` | 카메라의 프리셋 목록 조회 |
| GET | `/api/devices/cameras/{camera_id}/presets/{preset_id}` | 프리셋 상세 조회 (ROI 포함) |
| POST | `/api/devices/cameras/{camera_id}/presets` | 프리셋 생성 |
| PATCH | `/api/devices/cameras/{camera_id}/presets/{preset_id}` | 프리셋 부분 수정 |
| PUT | `/api/devices/cameras/{camera_id}/presets/{preset_id}` | 프리셋 전체 수정 |
| DELETE | `/api/devices/cameras/{camera_id}/presets/{preset_id}` | 프리셋 삭제 |

#### ROI API

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/presets/{preset_id}/rois` | 프리셋의 ROI 목록 조회 |
| GET | `/api/presets/{preset_id}/rois/{roi_id}` | ROI 상세 조회 (Points 포함) |
| POST | `/api/presets/{preset_id}/rois` | ROI 생성 |
| PATCH | `/api/presets/{preset_id}/rois/{roi_id}` | ROI 부분 수정 |
| PUT | `/api/presets/{preset_id}/rois/{roi_id}` | ROI 전체 수정 |
| DELETE | `/api/presets/{preset_id}/rois/{roi_id}` | ROI 삭제 |

#### XyPoint API

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/rois/{roi_id}/points` | ROI의 포인트 목록 조회 |
| POST | `/api/rois/{roi_id}/points` | 포인트 생성 |
| PUT | `/api/rois/{roi_id}/points` | 포인트 일괄 수정 (전체 교체) |
| DELETE | `/api/rois/{roi_id}/points/{point_id}` | 포인트 삭제 |

---

### 3.2 CameraPreset API 상세

#### 3.2.1 프리셋 목록 조회

**Endpoint**: `GET /api/devices/cameras/{camera_id}/presets`

**Path Parameters**:
- `camera_id` (int, required): 카메라 ID

**Query Parameters**:
- `include_rois` (bool, optional): ROI 정보 포함 여부 (기본값: false)
- `page` (int, optional): 페이지 번호 (기본값: 1)
- `limit` (int, optional): 페이지당 항목 수 (기본값: 20)

**Response Example** (200 OK, `include_rois=false` 기본값):
```json
{
  "success": true,
  "message": "Camera presets retrieved successfully",
  "data": {
    "items": [
      {
        "id": 1,
        "camera_id": 201,
        "camera_name": "Camera-A-1",
        "preset_index": 1,
        "preset_name": "입구 정면",
        "touring_time": 10,
        "roi_count": 2,
        "created_at": "2025-01-01T00:00:00.000Z",
        "updated_at": "2025-01-01T00:00:00.000Z"
      },
      {
        "id": 2,
        "camera_id": 201,
        "camera_name": "Camera-A-1",
        "preset_index": 2,
        "preset_name": "좌측 펜스",
        "touring_time": 15,
        "roi_count": 1,
        "created_at": "2025-01-01T00:00:00.000Z",
        "updated_at": "2025-01-01T00:00:00.000Z"
      }
    ],
    "total": 2
  },
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 2,
    "total_pages": 1
  }
}
```

**Response Example** (200 OK, `include_rois=true`):
```json
{
  "success": true,
  "message": "Camera presets retrieved successfully",
  "data": {
    "items": [
      {
        "id": 1,
        "camera_id": 201,
        "camera_name": "Camera-A-1",
        "preset_index": 1,
        "preset_name": "입구 정면",
        "touring_time": 10,
        "roi_count": 2,
        "created_at": "2025-01-01T00:00:00.000Z",
        "updated_at": "2025-01-01T00:00:00.000Z",
        "rois": [
          {
            "id": 1,
            "name": "출입구 영역",
            "resolution_width": 1920.0,
            "resolution_height": 1080.0,
            "is_enable": true,
            "point_count": 4
          },
          {
            "id": 2,
            "name": "경계 영역",
            "resolution_width": 1920.0,
            "resolution_height": 1080.0,
            "is_enable": true,
            "point_count": 4
          }
        ]
      },
      {
        "id": 2,
        "camera_id": 201,
        "camera_name": "Camera-A-1",
        "preset_index": 2,
        "preset_name": "좌측 펜스",
        "touring_time": 15,
        "roi_count": 1,
        "created_at": "2025-01-01T00:00:00.000Z",
        "updated_at": "2025-01-01T00:00:00.000Z",
        "rois": [
          {
            "id": 3,
            "name": "펜스 감시 영역",
            "resolution_width": 1920.0,
            "resolution_height": 1080.0,
            "is_enable": true,
            "point_count": 5
          }
        ]
      }
    ],
    "total": 2
  },
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 2,
    "total_pages": 1
  }
}
```

#### 3.2.2 프리셋 상세 조회 (ROI 포함)

**Endpoint**: `GET /api/devices/cameras/{camera_id}/presets/{preset_id}`

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "Preset retrieved successfully",
  "data": {
    "id": 1,
    "camera_id": 201,
    "camera_name": "Camera-A-1",
    "preset_index": 1,
    "preset_name": "입구 정면",
    "touring_time": 10,
    "created_at": "2025-01-01T00:00:00.000Z",
    "updated_at": "2025-01-01T00:00:00.000Z",
    "rois": [
      {
        "id": 1,
        "name": "출입구 영역",
        "resolution_width": 1920.0,
        "resolution_height": 1080.0,
        "is_enable": true,
        "points": [
          {"id": 1, "x": 0.1, "y": 0.1, "order": 0},
          {"id": 2, "x": 0.9, "y": 0.1, "order": 1},
          {"id": 3, "x": 0.9, "y": 0.9, "order": 2},
          {"id": 4, "x": 0.1, "y": 0.9, "order": 3}
        ]
      },
      {
        "id": 2,
        "name": "경계 영역",
        "resolution_width": 1920.0,
        "resolution_height": 1080.0,
        "is_enable": true,
        "points": [
          {"id": 5, "x": 0.0, "y": 0.0, "order": 0},
          {"id": 6, "x": 0.3, "y": 0.0, "order": 1},
          {"id": 7, "x": 0.3, "y": 0.5, "order": 2},
          {"id": 8, "x": 0.0, "y": 0.5, "order": 3}
        ]
      }
    ]
  }
}
```

#### 3.2.3 프리셋 생성

**Endpoint**: `POST /api/devices/cameras/{camera_id}/presets`

**Request Body**:
```json
{
  "preset_index": 3,
  "preset_name": "우측 펜스",
  "touring_time": 20
}
```

**Response Example** (201 Created):
```json
{
  "success": true,
  "message": "Preset created successfully",
  "data": {
    "id": 3,
    "camera_id": 201,
    "camera_name": "Camera-A-1",
    "preset_index": 3,
    "preset_name": "우측 펜스",
    "touring_time": 20,
    "roi_count": 0,
    "created_at": "2025-01-10T10:00:00.000Z",
    "updated_at": "2025-01-10T10:00:00.000Z"
  }
}
```

#### 3.2.4 프리셋 수정 (PATCH)

**Endpoint**: `PATCH /api/devices/cameras/{camera_id}/presets/{preset_id}`

**Request Body** (부분 업데이트):
```json
{
  "preset_name": "우측 펜스 - 수정",
  "touring_time": 25
}
```

#### 3.2.5 프리셋 삭제

**Endpoint**: `DELETE /api/devices/cameras/{camera_id}/presets/{preset_id}`

> **Note**: CASCADE 삭제로 인해 하위 ROI 및 XyPoint도 함께 삭제됩니다.

---

### 3.3 ROI API 상세

#### 3.3.1 ROI 목록 조회

**Endpoint**: `GET /api/presets/{preset_id}/rois`

**Path Parameters**:
- `preset_id` (int, required): 프리셋 ID

**Query Parameters**:
- `include_points` (bool, optional): Points 정보 포함 여부 (기본값: false)
- `page` (int, optional): 페이지 번호 (기본값: 1)
- `limit` (int, optional): 페이지당 항목 수 (기본값: 10, 최대: 100)

**Response Example** (200 OK, `include_points=false` 기본값):
```json
{
  "success": true,
  "message": "ROIs retrieved successfully",
  "data": {
    "items": [
      {
        "id": 1,
        "preset_id": 1,
        "name": "출입구 영역",
        "resolution_width": 1920.0,
        "resolution_height": 1080.0,
        "is_enable": true,
        "point_count": 4,
        "created_at": "2025-01-01T00:00:00.000Z",
        "updated_at": "2025-01-01T00:00:00.000Z"
      }
    ],
    "total": 1
  },
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 1,
    "total_pages": 1
  }
}
```

**Response Example** (200 OK, `include_points=true`):
```json
{
  "success": true,
  "message": "ROIs retrieved successfully",
  "data": {
    "items": [
      {
        "id": 1,
        "preset_id": 1,
        "name": "출입구 영역",
        "resolution_width": 1920.0,
        "resolution_height": 1080.0,
        "is_enable": true,
        "point_count": 4,
        "created_at": "2025-01-01T00:00:00.000Z",
        "updated_at": "2025-01-01T00:00:00.000Z",
        "points": [
          {"id": 1, "x": 0.1, "y": 0.1, "order": 0},
          {"id": 2, "x": 0.9, "y": 0.1, "order": 1},
          {"id": 3, "x": 0.9, "y": 0.9, "order": 2},
          {"id": 4, "x": 0.1, "y": 0.9, "order": 3}
        ]
      }
    ],
    "total": 1
  },
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 1,
    "total_pages": 1
  }
}
```

#### 3.3.2 ROI 상세 조회 (Points 포함)

**Endpoint**: `GET /api/presets/{preset_id}/rois/{roi_id}`

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "ROI retrieved successfully",
  "data": {
    "id": 1,
    "preset_id": 1,
    "name": "출입구 영역",
    "resolution_width": 1920.0,
    "resolution_height": 1080.0,
    "is_enable": true,
    "created_at": "2025-01-01T00:00:00.000Z",
    "updated_at": "2025-01-01T00:00:00.000Z",
    "points": [
      {"id": 1, "x": 0.1, "y": 0.1, "order": 0},
      {"id": 2, "x": 0.9, "y": 0.1, "order": 1},
      {"id": 3, "x": 0.9, "y": 0.9, "order": 2},
      {"id": 4, "x": 0.1, "y": 0.9, "order": 3}
    ]
  }
}
```

#### 3.3.3 ROI 생성 (Points 포함)

**Endpoint**: `POST /api/presets/{preset_id}/rois`

**Request Body**:
```json
{
  "name": "새로운 감시 영역",
  "resolution_width": 1920.0,
  "resolution_height": 1080.0,
  "is_enable": true,
  "points": [
    {"x": 0.2, "y": 0.2, "order": 0},
    {"x": 0.8, "y": 0.2, "order": 1},
    {"x": 0.8, "y": 0.8, "order": 2},
    {"x": 0.2, "y": 0.8, "order": 3}
  ]
}
```

**Response Example** (201 Created):
```json
{
  "success": true,
  "message": "ROI created successfully",
  "data": {
    "id": 3,
    "preset_id": 1,
    "name": "새로운 감시 영역",
    "resolution_width": 1920.0,
    "resolution_height": 1080.0,
    "is_enable": true,
    "created_at": "2025-01-10T10:00:00.000Z",
    "updated_at": "2025-01-10T10:00:00.000Z",
    "points": [
      {"id": 9, "x": 0.2, "y": 0.2, "order": 0},
      {"id": 10, "x": 0.8, "y": 0.2, "order": 1},
      {"id": 11, "x": 0.8, "y": 0.8, "order": 2},
      {"id": 12, "x": 0.2, "y": 0.8, "order": 3}
    ]
  }
}
```

#### 3.3.4 ROI 수정 (PATCH)

**Endpoint**: `PATCH /api/presets/{preset_id}/rois/{roi_id}`

**Request Body**:
```json
{
  "name": "감시 영역 - 수정",
  "is_enable": false
}
```

---

### 3.4 XyPoint API 상세

#### 3.4.1 포인트 목록 조회

**Endpoint**: `GET /api/rois/{roi_id}/points`

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "4 points retrieved",
  "data": [
    {"id": 1, "roi_id": 1, "x": 0.1, "y": 0.1, "order": 0},
    {"id": 2, "roi_id": 1, "x": 0.9, "y": 0.1, "order": 1},
    {"id": 3, "roi_id": 1, "x": 0.9, "y": 0.9, "order": 2},
    {"id": 4, "roi_id": 1, "x": 0.1, "y": 0.9, "order": 3}
  ]
}
```

#### 3.4.2 포인트 일괄 수정 (전체 교체)

**Endpoint**: `PUT /api/rois/{roi_id}/points`

> **Note**: 기존 포인트를 모두 삭제하고 새 포인트로 교체합니다.

**Request Body**:
```json
{
  "points": [
    {"x": 0.15, "y": 0.15, "order": 0},
    {"x": 0.85, "y": 0.15, "order": 1},
    {"x": 0.85, "y": 0.85, "order": 2},
    {"x": 0.15, "y": 0.85, "order": 3},
    {"x": 0.5, "y": 0.5, "order": 4}
  ]
}
```

**Response Example** (200 OK):
```json
{
  "success": true,
  "message": "5 points updated",
  "data": [
    {"id": 13, "roi_id": 1, "x": 0.15, "y": 0.15, "order": 0},
    {"id": 14, "roi_id": 1, "x": 0.85, "y": 0.15, "order": 1},
    {"id": 15, "roi_id": 1, "x": 0.85, "y": 0.85, "order": 2},
    {"id": 16, "roi_id": 1, "x": 0.15, "y": 0.85, "order": 3},
    {"id": 17, "roi_id": 1, "x": 0.5, "y": 0.5, "order": 4}
  ]
}
```

---

## 4. Enum 정의

이 기능에는 새로운 Enum이 필요하지 않습니다. 기존 Enum을 활용합니다.

---

## 5. 구현 순서

### Phase 1: 모델 및 스키마 정의
1. `app/models/camera_preset.py` - CameraPreset, ROI, XyPoint 모델 생성
2. `app/schemas/camera_preset.py` - Pydantic 스키마 정의
3. `app/utils/enums.py` - 필요시 Enum 추가
4. DB 마이그레이션 및 테이블 생성

### Phase 2: CameraPreset API 구현
1. `app/routers/camera_presets.py` - 라우터 생성
2. CRUD 엔드포인트 구현 (목록, 상세, 생성, 수정, 삭제)
3. Camera와의 연관 관계 처리

### Phase 3: ROI API 구현
1. ROI CRUD 엔드포인트 구현
2. Preset과의 연관 관계 처리
3. Points 중첩 응답 처리

### Phase 4: XyPoint API 구현
1. XyPoint CRUD 엔드포인트 구현
2. 일괄 수정(PUT) 기능 구현
3. Order 정렬 처리

### Phase 5: 테스트 및 문서화
1. 단위 테스트 작성
2. 통합 테스트 작성
3. API 문서(GOP_Restful_Api_연동설계.md) 업데이트

---

## 6. 고려사항

### 6.1 데이터 무결성

- **CASCADE DELETE**: Camera 삭제 시 Preset → ROI → XyPoint 순차 삭제
- **preset_index UNIQUE**: 동일 카메라 내 프리셋 인덱스 중복 방지
- **order UNIQUE**: 동일 ROI 내 포인트 순서 중복 방지

### 6.2 성능 최적화

- Preset 목록 조회 시 `roi_count` 계산 최적화 (subquery 또는 JOIN)
- ROI 상세 조회 시 Points 즉시 로딩 (eager loading)
- 인덱스 활용한 조회 성능 보장

### 6.3 좌표 체계

좌표는 두 가지 방식 중 선택 가능:

1. **정규화 좌표** (권장): 0.0 ~ 1.0 범위
   - 해상도 변경에 독립적
   - `resolution_width`, `resolution_height`는 참조용

2. **픽셀 좌표**: 실제 픽셀 위치
   - `resolution_width`, `resolution_height`와 함께 사용
   - 해상도 변경 시 재계산 필요

### 6.4 다각형 유효성

- 최소 3개 이상의 점 필요 (삼각형 이상)
- 점 순서(order)는 시계방향 또는 반시계방향 일관성 유지 권장
- 자기 교차(self-intersection) 검증은 클라이언트 책임

---

## 7. 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| v1.0 | 2025-12-31 | 초안 작성 - Camera Preset, ROI, XyPoint 설계 |
| v1.1 | 2025-12-31 | ROI 목록 조회 API에 `include_points` 파라미터 추가 |
| v1.2 | 2025-12-31 | CameraPreset 목록 조회 API 응답 형식을 `data.items` 구조로 수정, `include_rois=true` 시 ROI 데이터 포함 구현 |

---

**문서 끝**
