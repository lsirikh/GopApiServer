# PRD: 썸네일 이미지 관리 (Thumbnail Image) 시스템 설계

**문서 버전**: v1.1
**작성일**: 2026-02-19
**상태**: Draft

---

## 1. 개요

### 1.1 목적

GOP 통합 관제 시스템에서 감지 이벤트 발생 시 카메라 썸네일 이미지를 체계적으로 업로드, 저장, 조회, 삭제할 수 있는 API를 제공한다. 이미지는 서버 파일 시스템에 날짜별 폴더 구조로 저장되며, DB에 메타데이터와 파일 경로를 관리한다.

### 1.2 범위

- **포함**:
  - 이미지 업로드 API (multipart form data)
  - 이미지 파일 조회/다운로드 API
  - 썸네일 메타데이터 CRUD API
  - 클라이언트 지정 파일명 + 날짜별 폴더 구조
  - Docker 볼륨 마운트 구성

- **제외**:
  - 이미지 리사이징/변환 (향후 확장)

### 1.4 클라이언트 워크플로우

DetectionEvent 발생 시 클라이언트는 다음과 같은 병렬 처리 플로우를 사용한다:

```
1. 탐지 발생 → camera_id + timestamp(밀리초 포함) 확정 (EventMapping → CameraMapping 참조)
2. 클라이언트가 파일명 결정: "CAM-001_2026-02-19_14-30-25-123.jpg"
3. thumbnail URL 확정: "/api/thumbnails/images/CAM-001_2026-02-19_14-30-25-123.jpg"
4. 병렬 API 호출:
   ├─ POST /api/thumbnails (file + file_name)
   └─ POST /api/events/detections (detail.thumbnail = 위 URL)
5. Detection Response (DB ID 포함) → NATS Broker 발행 → 서브시스템 이벤트 처리
6. 서브시스템이 detail.thumbnail URL로 GET → 이미지 바이너리 반환
```

**핵심**:
- 파일 네이밍 컨벤션을 클라이언트가 제어하므로 타임스탬프 불일치 없이 병렬 호출이 가능
- `detail.thumbnail`에 **HTTP API URL**을 저장하여 서브시스템이 직접 이미지 조회 가능

### 1.3 기존 시스템과의 연관

| 구분 | DetectionDetail.thumbnail | **Thumbnail API (신규)** |
|------|---------------------------|--------------------------|
| 목적 | 외부 URL 참조 | **이미지 파일 저장/관리** |
| 저장 | URL 문자열만 | **파일 + DB 메타데이터** |
| 조회 | 직접 URL 접근 | **API를 통한 이미지 반환** |

---

## 2. 데이터 모델 설계

### 2.1 thumbnails 테이블

```sql
CREATE TABLE thumbnails (
    id SERIAL PRIMARY KEY,

    -- 파일 정보
    file_path VARCHAR(500) NOT NULL,
    file_name VARCHAR(200) NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type VARCHAR(50) NOT NULL,
    width INTEGER,
    height INTEGER,

    -- 타임스탬프
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE UNIQUE INDEX idx_thumbnails_file_name ON thumbnails(file_name);
CREATE INDEX idx_thumbnails_created_at ON thumbnails(created_at DESC);
```

### 2.2 필드 정의

| 필드명 | 타입 | NULL 허용 | 기본값 | 설명 |
|--------|------|-----------|--------|------|
| id | SERIAL | NO | AUTO | 고유 식별자 (PK) |
| file_path | VARCHAR(500) | NO | - | 서버 파일 시스템 절대 경로 |
| file_name | VARCHAR(200) | NO | - | 클라이언트 지정 파일명 (UNIQUE) |
| file_size | INTEGER | NO | - | 파일 크기 (bytes) |
| mime_type | VARCHAR(50) | NO | - | MIME 타입 (image/jpeg 등) |
| width | INTEGER | YES | NULL | 이미지 너비 (px, 업로드 시 자동 추출) |
| height | INTEGER | YES | NULL | 이미지 높이 (px, 업로드 시 자동 추출) |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 생성 시간 |

### 2.3 Event 연결 방식

Thumbnail과 DetectionEvent는 **FK 없이** 연결된다:
- DetectionEvent.detail.thumbnail 필드에 파일 경로 URL을 저장
- 병렬 호출 시 클라이언트가 파일명을 미리 결정하므로 양쪽이 동일한 URL을 참조
- Thumbnail 삭제 시 DetectionEvent에 영향 없음 (독립 자산)

### 2.4 SQLAlchemy 모델

```python
# app/models/thumbnail.py
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime as dt
from app.database import Base
from app.config import settings

class Thumbnail(Base):
    __tablename__ = "thumbnails"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(200), nullable=False, unique=True, index=True)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(50), nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: dt.now(settings.tz), nullable=False, index=True)
```

---

## 3. 파일 저장 설계

### 3.1 저장 경로 구조

```
{THUMBNAIL_STORAGE_PATH}/{YYYY-MM-DD}/{client_file_name}
```

- **날짜 디렉토리**: 서버가 요청 시점 기준 `YYYY-MM-DD` 폴더 자동 생성
- **파일명**: 클라이언트가 `file_name` 파라미터로 직접 지정

**예시** (클라이언트가 `CAM-001_2026-02-19_14-30-25-123.jpg`를 전송):
```
data/thumbnails/2026-02-19/CAM-001_2026-02-19_14-30-25-123.jpg
data/thumbnails/2026-02-19/CAM-002_2026-02-19_14-31-00-456.png
data/thumbnails/2026-02-20/CAM-001_2026-02-20_09-00-00-000.jpg
```

> **파일명 컨벤션**: `{camera_id}_{YYYY-MM-DD}_{HH-MM-SS-fff}.{ext}` (fff = 밀리초, 동일 카메라 1초 내 다중 탐지 구분)

> **Note**: 파일 네이밍 컨벤션은 클라이언트 책임. 서버는 전달받은 파일명을 그대로 사용한다.
> 이를 통해 DetectionEvent.detail.thumbnail URL과 실제 저장 경로가 일치함을 보장한다.

### 3.2 설정

```python
# app/config.py
THUMBNAIL_STORAGE_PATH: str = "data/thumbnails"  # 환경변수로 오버라이드 가능
```

### 3.3 MIME 타입 제한

| MIME Type | Extension |
|-----------|-----------|
| image/jpeg | .jpg, .jpeg |
| image/png | .png |
| image/gif | .gif |
| image/webp | .webp |

### 3.4 Docker 구성

```dockerfile
# Dockerfile 추가
RUN mkdir -p /app/data/thumbnails
```

```yaml
# docker-compose.yml — 기존 ./data:/app/data 마운트로 자동 커버
volumes:
  - ./data:/app/data  # thumbnails 디렉토리 포함
```

---

## 4. API 설계

### 4.1 썸네일 업로드

**Endpoint**: `POST /api/thumbnails`
**Content-Type**: `multipart/form-data`

**Form Parameters**:

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| file | File | YES | 이미지 파일 (image/jpeg, image/png, image/gif, image/webp) |
| file_name | string | YES | 저장할 파일명 (클라이언트 지정, 예: `CAM-001_2026-02-19_14-30-25-123.jpg`) |

**Response (201 Created)**:
```json
{
  "success": true,
  "message": "Thumbnail uploaded successfully",
  "data": {
    "id": 1,
    "file_path": "data/thumbnails/2026-02-19/CAM-001_2026-02-19_14-30-25-123.jpg",
    "file_name": "CAM-001_2026-02-19_14-30-25-123.jpg",
    "file_size": 245760,
    "mime_type": "image/jpeg",
    "width": 1920,
    "height": 1080,
    "image_url": "/api/thumbnails/images/CAM-001_2026-02-19_14-30-25-123.jpg",
    "created_at": "2026-02-19T14:30:25.123+09:00"
  }
}
```

> **Note**: `width`/`height`는 업로드 시 Pillow로 자동 추출됩니다. 손상된 이미지 등 추출 실패 시 null로 저장됩니다.

**Error Responses**:
- `400 Bad Request`: 지원하지 않는 파일 형식
- `409 Conflict`: 동일 file_name 이미 존재
- `422 Validation Error`: file_name 또는 file 누락

### 4.2 썸네일 목록 조회

**Endpoint**: `GET /api/thumbnails`

**Query Parameters**:

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|------|--------|------|
| page | integer | NO | 1 | 페이지 번호 |
| limit | integer | NO | 20 | 페이지당 항목 수 (max: 100) |
| start_date | datetime | NO | - | 시작 날짜 필터 |
| end_date | datetime | NO | - | 종료 날짜 필터 |

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Thumbnails retrieved successfully",
  "data": [
    {
      "id": 1,
      "file_path": "data/thumbnails/2026-02-19/CAM-001_2026-02-19_14-30-25-123.jpg",
      "file_name": "CAM-001_2026-02-19_14-30-25-123.jpg",
      "file_size": 245760,
      "mime_type": "image/jpeg",
      "width": 1920,
      "height": 1080,
      "image_url": "/api/thumbnails/images/CAM-001_2026-02-19_14-30-25-123.jpg",
      "created_at": "2026-02-19T14:30:25.123+09:00"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 1,
    "total_pages": 1
  },
  "meta": {
    "timestamp": "2026-02-19T14:30:30.000Z",
    "request_id": "..."
  }
}
```

### 4.3 썸네일 메타데이터 조회

**Endpoint**: `GET /api/thumbnails/{id}`

**Response (200 OK)**: `ApiSingleResponse[ThumbnailResponse]` (4.1과 동일한 data 구조)

**Error Response**: `404 Not Found`

### 4.4 썸네일 이미지 다운로드 (ID 기반)

**Endpoint**: `GET /api/thumbnails/{id}/image`

**Response (200 OK)**:
- Content-Type: `image/jpeg` (또는 원본 MIME 타입)
- Body: 이미지 바이너리 (FileResponse)

**Error Responses**:
- `404 Not Found`: DB 레코드 없음 또는 파일 없음

### 4.5 썸네일 이미지 다운로드 (파일명 기반)

**Endpoint**: `GET /api/thumbnails/images/{file_name}`

클라이언트/서브시스템이 파일명만으로 이미지를 조회하는 엔드포인트. `DetectionEvent.detail.thumbnail`에 이 URL을 저장하여 병렬 워크플로우를 지원한다.

**Path Parameter**:

| 파라미터 | 타입 | 설명 |
|----------|------|------|
| file_name | string | 저장된 파일명 (예: `CAM-001_2026-02-19_14-30-25-123.jpg`) |

**Response (200 OK)**:
- Content-Type: `image/jpeg` (또는 원본 MIME 타입)
- Body: 이미지 바이너리 (FileResponse)

**Error Responses**:
- `404 Not Found`: 해당 file_name의 DB 레코드 없음 또는 파일 없음

### 4.6 썸네일 삭제

**Endpoint**: `DELETE /api/thumbnails/{id}`

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Thumbnail deleted successfully",
  "data": null,
  "meta": {
    "timestamp": "2026-02-19T14:35:00.000Z",
    "request_id": "..."
  }
}
```

**Error Response**: `404 Not Found`

**동작**: 파일 시스템에서 파일 삭제 + DB 레코드 삭제 (파일이 이미 없어도 DB 삭제 진행)

---

## 5. Pydantic 스키마

```python
# app/schemas/thumbnail.py
from pydantic import BaseModel, ConfigDict, computed_field
from datetime import datetime
from typing import Optional

class ThumbnailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_path: str
    file_name: str
    file_size: int
    mime_type: str
    width: Optional[int] = None
    height: Optional[int] = None
    created_at: datetime

    @computed_field
    @property
    def image_url(self) -> str:
        return f"/api/thumbnails/images/{self.file_name}"
```
