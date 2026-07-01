# PRD: ConfigChangeLog (설정 변경 로그) 시스템

**문서 버전**: v1.2
**작성일**: 2026-01-20
**최종 수정일**: 2026-01-22
**작성자**: AI Assistant
**상태**: Draft

**변경 이력**:
| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| v1.0 | 2026-01-20 | 초안 작성 |
| v1.1 | 2026-01-21 | JSONB 정규화 규칙 추가 (Section 3.3) |
| v1.2 | 2026-01-22 | SERVER, SERVER_CATEGORY 제거 (→ SystemEvent로 이관), 17개 리소스 유형으로 축소 |

---

## 1. 개요

### 1.1 목적

Device, Event, Integration 계열 리소스의 CRUD 작업에 대한 변경 이력을 추적하는 **ConfigChangeLog** 시스템을 구현한다.

> **Note**: Server, ServerCategory는 SystemEvent에서 관리합니다.

### 1.2 배경

현재 로깅 시스템 현황:

| 시스템 | 목적 | 대상 |
|--------|------|------|
| **AuditLog** | 계정 감사 | AccountUser, UserGroup, UserSession, Password |
| **SystemEvent** | 서버/디바이스 모니터링 | 장애, 경고, 상태변경 |
| **UserLoginLog** | 인증 이력 | 로그인/로그아웃 |

**문제점**: Device, Event, Integration 계열의 설정 변경에 대한 이력 추적이 없음.

**로그 시스템 역할 분담**:
| 시스템 | 담당 범위 |
|--------|----------|
| **ConfigChangeLog** | Device, DeviceGroup, CameraPreset, ROI, XYPoint, FileGroup, Event, Integration CRUD |
| **SystemEvent** | Server, ServerCategory, ServerMetrics |
| **AuditLog** | User, UserGroup, UserSession, Authentication |

### 1.3 범위

#### 포함 (In Scope)

- ConfigChangeLog 모델 및 스키마 구현
- Enum 타입 정의 (EnumConfigResourceType, EnumConfigActionType)
- 설정 변경 로깅 서비스 구현
- API 엔드포인트 구현 (GET /api/config-change-logs)
- 기존 CRUD 라우터에 로깅 통합
- GOP 문서 업데이트

#### 제외 (Out of Scope)

- Enclosure Control 기능 (제거됨)
- 메트릭 데이터 변경 로깅 (대량 데이터)

---

## 2. Enum 타입 정의

### 2.1 EnumConfigResourceType (17개)

```python
class EnumConfigResourceType(str, Enum):
    """
    설정 변경 대상 리소스 유형 (17종)

    Note: Server, ServerCategory는 SystemEvent에서 관리
    """

    # Device 계열 (10개)
    CONTROLLER = "CONTROLLER"
    SENSOR = "SENSOR"
    CAMERA = "CAMERA"
    SPEAKER = "SPEAKER"
    ENCLOSURE = "ENCLOSURE"
    DEVICE_GROUP = "DEVICE_GROUP"
    CAMERA_PRESET = "CAMERA_PRESET"
    ROI = "ROI"
    XY_POINT = "XY_POINT"
    FILE_GROUP = "FILE_GROUP"

    # Event 계열 (4개)
    DETECTION_EVENT = "DETECTION_EVENT"
    MALFUNCTION_EVENT = "MALFUNCTION_EVENT"
    CONNECTION_EVENT = "CONNECTION_EVENT"
    ACTION_EVENT = "ACTION_EVENT"

    # Integration 계열 (3개)
    EVENT_MAPPING = "EVENT_MAPPING"
    EVENT_MAPPING_CAMERA = "EVENT_MAPPING_CAMERA"
    EVENT_MAPPING_SPEAKER = "EVENT_MAPPING_SPEAKER"
```

> **제외된 리소스** (SystemEvent에서 관리):
> - SERVER_CATEGORY
> - SERVER

### 2.2 EnumConfigActionType (6개)

```python
class EnumConfigActionType(str, Enum):
    """설정 변경 액션 유형"""
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    DELETED = "DELETED"
    STATUS_CHANGED = "STATUS_CHANGED"  # Enclosure status
    ASSIGNED = "ASSIGNED"              # DeviceGroup에 디바이스 할당
    UNASSIGNED = "UNASSIGNED"          # DeviceGroup에서 디바이스 제거
```

---

## 3. 데이터베이스 스키마

### 3.1 config_change_logs 테이블

```sql
CREATE TABLE config_change_logs (
    id SERIAL PRIMARY KEY,

    -- 변경 대상
    resource_type VARCHAR(50) NOT NULL,  -- EnumConfigResourceType
    resource_id INTEGER NOT NULL,
    resource_name VARCHAR(200),          -- 식별용 (예: "Camera-201")

    -- 변경 내용
    action VARCHAR(20) NOT NULL,         -- EnumConfigActionType
    before_state JSONB,                  -- 변경 전 상태
    after_state JSONB,                   -- 변경 후 상태

    -- 수행자
    actor_id INTEGER REFERENCES account_users(id),
    actor_name VARCHAR(100),
    actor_ip VARCHAR(45),

    -- 메타
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 인덱스
CREATE INDEX idx_config_change_logs_resource ON config_change_logs(resource_type, resource_id);
CREATE INDEX idx_config_change_logs_actor ON config_change_logs(actor_id);
CREATE INDEX idx_config_change_logs_created_at ON config_change_logs(created_at DESC);
CREATE INDEX idx_config_change_logs_action ON config_change_logs(action);
```

### 3.2 SQLAlchemy 모델

```python
# app/models/config_change_log.py

from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.database import Base
from app.utils.enums import EnumConfigResourceType, EnumConfigActionType


class ConfigChangeLog(Base):
    __tablename__ = "config_change_logs"

    id = Column(Integer, primary_key=True, index=True)

    # 변경 대상
    resource_type = Column(Enum(EnumConfigResourceType), nullable=False)
    resource_id = Column(Integer, nullable=False)
    resource_name = Column(String(200))

    # 변경 내용
    action = Column(Enum(EnumConfigActionType), nullable=False)
    before_state = Column(JSONB)
    after_state = Column(JSONB)

    # 수행자
    actor_id = Column(Integer, ForeignKey("account_users.id"))
    actor_name = Column(String(100))
    actor_ip = Column(String(45))

    # 메타
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

### 3.3 JSONB 정규화 규칙 (v1.1)

`before_state`와 `after_state`는 **변경된 필드만** 저장합니다.

#### 3.3.1 설계 원칙

- **최소 정보 원칙**: 전체 모델 스냅샷 대신 변경된 필드만 저장
- **액션별 차등 적용**: 각 액션 유형에 맞는 최소 정보 저장
- **일관된 식별자**: `id`, `name` 필드로 리소스 식별

#### 3.3.2 액션별 JSONB 구조

| Action | before_state | after_state | 설명 |
|--------|--------------|-------------|------|
| CREATED | `null` | `{id, name}` | 생성된 리소스 식별 정보 |
| UPDATED | `{변경된 필드}` | `{변경된 필드}` | 변경 전/후 값만 저장 |
| DELETED | `{id, name}` | `null` | 삭제된 리소스 식별 정보 |
| STATUS_CHANGED | `{status: "OLD"}` | `{status: "NEW"}` | 상태 필드만 저장 |
| ASSIGNED | `null` | `{target_id, target_name}` | 할당 대상 정보 |
| UNASSIGNED | `{target_id, target_name}` | `null` | 해제 대상 정보 |

#### 3.3.3 예시

**CREATED (Camera 생성)**
```json
{
  "before_state": null,
  "after_state": {
    "id": 201,
    "name": "정문 CCTV"
  }
}
```

**UPDATED (Camera 이름 변경)**
```json
{
  "before_state": {
    "name": "정문 CCTV"
  },
  "after_state": {
    "name": "정문 CCTV (수정)"
  }
}
```

**UPDATED (Camera 복수 필드 변경)**
```json
{
  "before_state": {
    "name": "정문 CCTV",
    "ip_address": "192.168.1.100"
  },
  "after_state": {
    "name": "정문 CCTV (수정)",
    "ip_address": "192.168.1.101"
  }
}
```

**STATUS_CHANGED (Enclosure 상태 변경)**
```json
{
  "before_state": {
    "status": "ACTIVATED"
  },
  "after_state": {
    "status": "DEACTIVATED"
  }
}
```

**DELETED (Camera 삭제)**
```json
{
  "before_state": {
    "id": 201,
    "name": "정문 CCTV"
  },
  "after_state": null
}
```

**ASSIGNED (DeviceGroup에 디바이스 할당)**
```json
{
  "before_state": null,
  "after_state": {
    "device_id": 201,
    "device_name": "정문 CCTV"
  }
}
```

**UNASSIGNED (DeviceGroup에서 디바이스 해제)**
```json
{
  "before_state": {
    "device_id": 201,
    "device_name": "정문 CCTV"
  },
  "after_state": null
}
```

---

## 4. Pydantic 스키마

### 4.1 app/schemas/config_change_log.py

```python
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Any, Dict
from datetime import datetime

from app.utils.enums import EnumConfigResourceType, EnumConfigActionType


class ConfigChangeLogResponse(BaseModel):
    """
    설정 변경 로그 응답 스키마

    Note: before_state/after_state는 v1.1 정규화 규칙에 따라
    변경된 필드만 저장합니다.
    """
    id: int = Field(
        ...,
        description="로그 ID",
        json_schema_extra={"example": 1}
    )
    resource_type: EnumConfigResourceType = Field(
        ...,
        description="리소스 유형 (17종: Device 10, Event 4, Integration 3)",
        json_schema_extra={"example": "CAMERA"}
    )
    resource_id: int = Field(
        ...,
        description="리소스 ID",
        json_schema_extra={"example": 201}
    )
    resource_name: Optional[str] = Field(
        None,
        description="리소스 식별명",
        json_schema_extra={"example": "Camera-201 (정문 CCTV)"}
    )
    action: EnumConfigActionType = Field(
        ...,
        description="액션 유형 (CREATED, UPDATED, DELETED, STATUS_CHANGED, ASSIGNED, UNASSIGNED)",
        json_schema_extra={"example": "UPDATED"}
    )
    before_state: Optional[Dict[str, Any]] = Field(
        None,
        description="변경 전 상태 (변경된 필드만)",
        json_schema_extra={"example": {"name": "정문 CCTV"}}
    )
    after_state: Optional[Dict[str, Any]] = Field(
        None,
        description="변경 후 상태 (변경된 필드만)",
        json_schema_extra={"example": {"name": "정문 CCTV (수정)"}}
    )
    actor_id: Optional[int] = Field(
        None,
        description="수행자 ID",
        json_schema_extra={"example": 1}
    )
    actor_name: Optional[str] = Field(
        None,
        description="수행자 이름",
        json_schema_extra={"example": "admin"}
    )
    actor_ip: Optional[str] = Field(
        None,
        description="수행자 IP",
        json_schema_extra={"example": "192.168.1.100"}
    )
    description: Optional[str] = Field(
        None,
        description="설명",
        json_schema_extra={"example": "Camera 정보 수정"}
    )
    created_at: datetime = Field(
        ...,
        description="생성 시간",
        json_schema_extra={"example": "2026-01-20T10:30:00"}
    )

    model_config = ConfigDict(from_attributes=True)


class ConfigChangeLogListResponse(BaseModel):
    """설정 변경 로그 목록 응답"""
    logs: list[ConfigChangeLogResponse] = Field(
        ...,
        description="로그 목록"
    )
    total: int = Field(
        ...,
        description="전체 로그 수",
        json_schema_extra={"example": 150}
    )
    page: int = Field(
        ...,
        description="현재 페이지",
        json_schema_extra={"example": 1}
    )
    limit: int = Field(
        ...,
        description="페이지당 항목 수",
        json_schema_extra={"example": 50}
    )
```

---

## 5. API 엔드포인트

### 5.1 GET /api/config-change-logs

설정 변경 로그 목록 조회

**Query Parameters**:

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| page | int | N | 페이지 번호 (기본값: 1) |
| limit | int | N | 페이지당 항목 수 (기본값: 50, 최대: 100) |
| resource_type | string | N | 리소스 유형 필터 |
| resource_id | int | N | 리소스 ID 필터 |
| action | string | N | 액션 유형 필터 |
| actor_id | int | N | 수행자 ID 필터 |
| start_date | datetime | N | 시작 일시 |
| end_date | datetime | N | 종료 일시 |

**Response** (200 OK):

```json
{
  "success": true,
  "message": "Config change logs retrieved successfully",
  "data": {
    "logs": [
      {
        "id": 1,
        "resource_type": "CAMERA",
        "resource_id": 201,
        "resource_name": "Camera-201 (정문 CCTV)",
        "action": "UPDATED",
        "before_state": {
          "name": "정문 CCTV"
        },
        "after_state": {
          "name": "정문 CCTV (수정)"
        },
        "actor_id": 1,
        "actor_name": "admin",
        "actor_ip": "192.168.1.100",
        "description": "Camera 정보 수정",
        "created_at": "2026-01-20T10:30:00+09:00"
      },
      {
        "id": 2,
        "resource_type": "CAMERA",
        "resource_id": 202,
        "resource_name": "Camera-202 (후문 CCTV)",
        "action": "CREATED",
        "before_state": null,
        "after_state": {
          "id": 202,
          "name": "후문 CCTV"
        },
        "actor_id": 1,
        "actor_name": "admin",
        "actor_ip": "192.168.1.100",
        "description": "Camera 생성",
        "created_at": "2026-01-20T09:30:00+09:00"
      }
    ],
    "total": 150,
    "page": 1,
    "limit": 50
  }
}
```

### 5.2 GET /api/config-change-logs/{id}

설정 변경 로그 단건 조회

**Response** (200 OK):

```json
{
  "success": true,
  "message": "Config change log retrieved successfully",
  "data": {
    "id": 1,
    "resource_type": "CAMERA",
    "resource_id": 201,
    "resource_name": "Camera-201 (정문 CCTV)",
    "action": "UPDATED",
    "before_state": { ... },
    "after_state": { ... },
    "actor_id": 1,
    "actor_name": "admin",
    "actor_ip": "192.168.1.100",
    "description": "Camera 정보 수정",
    "created_at": "2026-01-20T10:30:00+09:00"
  }
}
```

---

## 6. 로깅 서비스 구현

### 6.1 app/services/config_log_service.py

```python
from sqlalchemy.orm import Session
from typing import Optional, Any

from app.models.config_change_log import ConfigChangeLog
from app.utils.enums import EnumConfigResourceType, EnumConfigActionType


def log_config_change(
    db: Session,
    resource_type: EnumConfigResourceType,
    resource_id: int,
    action: EnumConfigActionType,
    resource_name: Optional[str] = None,
    before_state: Optional[dict] = None,
    after_state: Optional[dict] = None,
    actor_id: Optional[int] = None,
    actor_name: Optional[str] = None,
    actor_ip: Optional[str] = None,
    description: Optional[str] = None
) -> ConfigChangeLog:
    """설정 변경 로그 기록"""

    log = ConfigChangeLog(
        resource_type=resource_type,
        resource_id=resource_id,
        resource_name=resource_name,
        action=action,
        before_state=before_state,
        after_state=after_state,
        actor_id=actor_id,
        actor_name=actor_name,
        actor_ip=actor_ip,
        description=description
    )

    db.add(log)
    # Note: commit은 호출자가 수행
    return log


def model_to_dict(model: Any, exclude: list = None) -> dict:
    """SQLAlchemy 모델을 딕셔너리로 변환"""
    if model is None:
        return None

    exclude = exclude or []
    result = {}

    for column in model.__table__.columns:
        if column.name not in exclude:
            value = getattr(model, column.name)
            # datetime 처리
            if hasattr(value, 'isoformat'):
                value = value.isoformat()
            # Enum 처리
            elif hasattr(value, 'value'):
                value = value.value
            result[column.name] = value

    return result


def get_changed_fields(before: dict, after: dict) -> tuple[dict, dict]:
    """
    두 dict를 비교하여 변경된 필드만 추출합니다. (v1.1)

    Args:
        before: 변경 전 상태 dict
        after: 변경 후 상태 dict

    Returns:
        (변경된 before 필드, 변경된 after 필드) 튜플
    """
    before_changes = {}
    after_changes = {}

    all_keys = set(before.keys()) | set(after.keys())

    for key in all_keys:
        before_val = before.get(key)
        after_val = after.get(key)

        if before_val != after_val:
            if key in before:
                before_changes[key] = before_val
            if key in after:
                after_changes[key] = after_val

    return before_changes, after_changes


def get_identifier(model: Any) -> dict:
    """
    모델의 식별 정보(id, name)만 추출합니다. (v1.1)

    Args:
        model: SQLAlchemy 모델 인스턴스

    Returns:
        {"id": ..., "name": ...} 형태의 dict
    """
    result = {"id": model.id}

    # name 필드 탐색 (name, name_device 등)
    for attr in ["name", "name_device", "title"]:
        if hasattr(model, attr):
            result["name"] = getattr(model, attr)
            break

    return result
```

---

## 7. 기존 라우터 통합

### 7.1 적용 대상 라우터 (17개)

| 라우터 파일 | 리소스 | 적용 API |
|-------------|--------|----------|
| controllers.py | CONTROLLER | POST, PATCH, PUT, DELETE |
| sensors.py | SENSOR | POST, PATCH, PUT, DELETE |
| cameras.py | CAMERA | POST, PATCH, PUT, DELETE |
| speakers.py | SPEAKER | POST, PATCH, PUT, DELETE |
| enclosures.py | ENCLOSURE | POST, PATCH, PUT, DELETE, /status |
| device_groups.py | DEVICE_GROUP | POST, PATCH, PUT, DELETE, /devices |
| camera_presets.py | CAMERA_PRESET | POST, PATCH, PUT, DELETE |
| rois.py | ROI | POST, PATCH, PUT, DELETE |
| xy_points.py | XY_POINT | POST, PUT, DELETE |
| file_groups.py | FILE_GROUP | POST, PATCH, PUT, DELETE |
| detection_events.py | DETECTION_EVENT | POST, PATCH, PUT, DELETE |
| malfunction_events.py | MALFUNCTION_EVENT | POST, PATCH, PUT, DELETE |
| connection_events.py | CONNECTION_EVENT | POST, PATCH, PUT, DELETE |
| action_events.py | ACTION_EVENT | POST, PATCH, PUT, DELETE |
| event_mappings.py | EVENT_MAPPING | POST, PATCH, PUT, DELETE |
| event_mapping_cameras.py | EVENT_MAPPING_CAMERA | POST, PATCH, PUT, DELETE |
| event_mapping_speakers.py | EVENT_MAPPING_SPEAKER | POST, PATCH, PUT, DELETE |

> **제외된 라우터** (SystemEvent에서 관리):
> - server_categories.py
> - servers.py

### 7.2 통합 예시 (Camera POST) - CREATED

```python
# app/routers/cameras.py

from app.services.config_log_service import log_config_change, get_identifier
from app.utils.enums import EnumConfigResourceType, EnumConfigActionType

@router.post("", status_code=201)
async def create_camera(
    camera_data: CameraCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: AccountUser = Depends(get_current_user_optional)
):
    # ... 카메라 생성 로직 ...

    db.add(new_camera)
    db.commit()
    db.refresh(new_camera)

    # 설정 변경 로그 기록 (v1.1: 식별 정보만 저장)
    log_config_change(
        db=db,
        resource_type=EnumConfigResourceType.CAMERA,
        resource_id=new_camera.id,
        action=EnumConfigActionType.CREATED,
        resource_name=f"Camera-{new_camera.id} ({new_camera.name_device})",
        before_state=None,  # CREATED: before는 null
        after_state=get_identifier(new_camera),  # {"id": 201, "name": "정문 CCTV"}
        actor_id=current_user.id if current_user else None,
        actor_name=current_user.name if current_user else None,
        actor_ip=request.client.host if request.client else None,
        description=f"Camera 생성: {new_camera.name_device}"
    )
    db.commit()

    return ApiResponse(...)
```

### 7.3 통합 예시 (Camera PATCH) - UPDATED

```python
from app.services.config_log_service import log_config_change, model_to_dict, get_changed_fields

@router.patch("/{camera_id}")
async def update_camera(
    camera_id: int,
    camera_data: CameraUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: AccountUser = Depends(get_current_user_optional)
):
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    # 변경 전 전체 상태 저장
    before_full = model_to_dict(camera)

    # ... 업데이트 로직 ...

    db.commit()
    db.refresh(camera)

    # 변경 후 전체 상태
    after_full = model_to_dict(camera)

    # v1.1: 변경된 필드만 추출
    before_changes, after_changes = get_changed_fields(before_full, after_full)

    # 변경 사항이 있는 경우에만 로깅
    if before_changes or after_changes:
        log_config_change(
            db=db,
            resource_type=EnumConfigResourceType.CAMERA,
            resource_id=camera.id,
            action=EnumConfigActionType.UPDATED,
            resource_name=f"Camera-{camera.id} ({camera.name_device})",
            before_state=before_changes,  # {"name": "정문 CCTV"}
            after_state=after_changes,    # {"name": "정문 CCTV (수정)"}
            actor_id=current_user.id if current_user else None,
            actor_name=current_user.name if current_user else None,
            actor_ip=request.client.host if request.client else None,
            description=f"Camera 수정: {camera.name_device}"
        )
        db.commit()

    return ApiResponse(...)
```

### 7.4 통합 예시 (Camera DELETE) - DELETED

```python
from app.services.config_log_service import log_config_change, get_identifier

@router.delete("/{camera_id}")
async def delete_camera(
    camera_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: AccountUser = Depends(get_current_user_optional)
):
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    # v1.1: 삭제 전 식별 정보 저장
    before_state = get_identifier(camera)  # {"id": 201, "name": "정문 CCTV"}
    camera_name = camera.name_device

    db.delete(camera)
    db.commit()

    # 설정 변경 로그 기록
    log_config_change(
        db=db,
        resource_type=EnumConfigResourceType.CAMERA,
        resource_id=camera_id,
        action=EnumConfigActionType.DELETED,
        resource_name=f"Camera-{camera_id} ({camera_name})",
        before_state=before_state,  # {"id": 201, "name": "정문 CCTV"}
        after_state=None,           # DELETED: after는 null
        actor_id=current_user.id if current_user else None,
        actor_name=current_user.name if current_user else None,
        actor_ip=request.client.host if request.client else None,
        description=f"Camera 삭제: {camera_name}"
    )
    db.commit()

    return ApiResponse(...)
```

### 7.5 통합 예시 (DeviceGroup Assign) - ASSIGNED

```python
@router.post("/{group_id}/devices")
async def assign_device_to_group(
    group_id: int,
    assign_data: DeviceAssign,
    request: Request,
    db: Session = Depends(get_db),
    current_user: AccountUser = Depends(get_current_user_optional)
):
    # ... 할당 로직 ...
    # device = db.query(Device).filter(Device.id == assign_data.device_id).first()

    # 설정 변경 로그 기록 (v1.1: 할당 대상 정보만 저장)
    log_config_change(
        db=db,
        resource_type=EnumConfigResourceType.DEVICE_GROUP,
        resource_id=group_id,
        action=EnumConfigActionType.ASSIGNED,
        resource_name=f"DeviceGroup-{group_id}",
        before_state=None,  # ASSIGNED: before는 null
        after_state={
            "device_id": device.id,
            "device_name": device.name_device
        },
        actor_id=current_user.id if current_user else None,
        actor_name=current_user.name if current_user else None,
        actor_ip=request.client.host if request.client else None,
        description=f"Device {device.name_device}을 DeviceGroup {group_id}에 할당"
    )
    db.commit()

    return ApiResponse(...)
```

---

## 8. GOP 문서 업데이트 명세

### 8.1 GOP_Restful_Api_연동설계.md 업데이트

#### 8.1.1 문서 헤더 업데이트

```markdown
**최종 수정일**: 2026-01-20
**버전**: v3.2
```

#### 8.1.2 목차 추가

```markdown
9. [Account API 설계](#9-account-api-설계)
   ...
   - 9.7 [Config Change Logs API](#97-config-change-logs-api) *(v3.2 신규)*
```

#### 8.1.3 Section 4 Enum 추가

```markdown
### 4.x EnumConfigResourceType

설정 변경 로그 대상 리소스 유형 (17종)

> Note: SERVER, SERVER_CATEGORY는 SystemEvent에서 관리

| 값 | 설명 |
|----|------|
| CONTROLLER | 컨트롤러 |
| SENSOR | 센서 |
| CAMERA | 카메라 |
| SPEAKER | 스피커 |
| ENCLOSURE | 함체 |
| DEVICE_GROUP | 디바이스 그룹 |
| CAMERA_PRESET | 카메라 프리셋 |
| ROI | ROI |
| XY_POINT | XY 포인트 |
| FILE_GROUP | 파일 그룹 |
| DETECTION_EVENT | 탐지 이벤트 |
| MALFUNCTION_EVENT | 고장 이벤트 |
| CONNECTION_EVENT | 연결 이벤트 |
| ACTION_EVENT | 액션 이벤트 |
| EVENT_MAPPING | 이벤트 매핑 |
| EVENT_MAPPING_CAMERA | 이벤트 매핑 카메라 |
| EVENT_MAPPING_SPEAKER | 이벤트 매핑 스피커 |

### 4.x EnumConfigActionType

설정 변경 액션 유형

| 값 | 설명 |
|----|------|
| CREATED | 생성 |
| UPDATED | 수정 |
| DELETED | 삭제 |
| STATUS_CHANGED | 상태 변경 |
| ASSIGNED | 할당 |
| UNASSIGNED | 할당 해제 |
```

#### 8.1.4 Section 9.7 신규 추가

```markdown
### 9.7 Config Change Logs API *(v3.2 신규)*

설정 변경 로그 관리 API

#### 9.7.1 Endpoint 목록

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/config-change-logs` | 로그 목록 조회 |
| GET | `/api/config-change-logs/{id}` | 로그 단건 조회 |

#### 9.7.2 before_state/after_state JSONB 정규화 규칙

**원칙**: 변경된 필드만 저장 (전체 스냅샷 대신)

| Action | before_state | after_state |
|--------|--------------|-------------|
| CREATED | null | {id, name} |
| UPDATED | {변경된 필드} | {변경된 필드} |
| DELETED | {id, name} | null |
| STATUS_CHANGED | {status} | {status} |
| ASSIGNED | null | {target_id, target_name} |
| UNASSIGNED | {target_id, target_name} | null |

#### 9.7.3 GET `/api/config-change-logs`

설정 변경 로그 목록 조회

**Query Parameters**:

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| page | int | N | 페이지 번호 (기본값: 1) |
| limit | int | N | 페이지당 항목 수 (기본값: 50, 최대: 100) |
| resource_type | string | N | 리소스 유형 필터 (EnumConfigResourceType) |
| resource_id | int | N | 리소스 ID 필터 |
| action | string | N | 액션 유형 필터 (EnumConfigActionType) |
| actor_id | int | N | 수행자 ID 필터 |
| start_date | datetime | N | 시작 일시 (ISO 8601) |
| end_date | datetime | N | 종료 일시 (ISO 8601) |

**Response** (200 OK):

\`\`\`json
{
  "success": true,
  "message": "Config change logs retrieved successfully",
  "data": {
    "logs": [
      {
        "id": 1,
        "resource_type": "CAMERA",
        "resource_id": 201,
        "resource_name": "Camera-201 (정문 CCTV)",
        "action": "UPDATED",
        "before_state": {
          "name": "정문 CCTV"
        },
        "after_state": {
          "name": "정문 CCTV (수정)"
        },
        "actor_id": 1,
        "actor_name": "admin",
        "actor_ip": "192.168.1.100",
        "description": "Camera 정보 수정",
        "created_at": "2026-01-20T10:30:00+09:00"
      },
      {
        "id": 2,
        "resource_type": "CAMERA",
        "resource_id": 202,
        "resource_name": "Camera-202 (후문 CCTV)",
        "action": "CREATED",
        "before_state": null,
        "after_state": {
          "id": 202,
          "name": "후문 CCTV"
        },
        "actor_id": 1,
        "actor_name": "admin",
        "actor_ip": "192.168.1.100",
        "description": "Camera 생성",
        "created_at": "2026-01-20T09:30:00+09:00"
      },
      {
        "id": 3,
        "resource_type": "CAMERA",
        "resource_id": 203,
        "resource_name": "Camera-203 (측면 CCTV)",
        "action": "DELETED",
        "before_state": {
          "id": 203,
          "name": "측면 CCTV"
        },
        "after_state": null,
        "actor_id": 1,
        "actor_name": "admin",
        "actor_ip": "192.168.1.100",
        "description": "Camera 삭제",
        "created_at": "2026-01-20T08:30:00+09:00"
      }
    ],
    "total": 150,
    "page": 1,
    "limit": 50
  }
}
\`\`\`

#### 9.7.4 GET `/api/config-change-logs/{id}`

설정 변경 로그 단건 조회

**Path Parameters**:

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| id | int | Y | 로그 ID |

**Response** (200 OK):

\`\`\`json
{
  "success": true,
  "message": "Config change log retrieved successfully",
  "data": {
    "id": 1,
    "resource_type": "CAMERA",
    "resource_id": 201,
    "resource_name": "Camera-201 (정문 CCTV)",
    "action": "UPDATED",
    "before_state": {
      "name": "정문 CCTV"
    },
    "after_state": {
      "name": "정문 CCTV (수정)"
    },
    "actor_id": 1,
    "actor_name": "admin",
    "actor_ip": "192.168.1.100",
    "description": "Camera 정보 수정",
    "created_at": "2026-01-20T10:30:00+09:00"
  }
}
\`\`\`

**Error Response** (404 Not Found):

\`\`\`json
{
  "success": false,
  "message": "Config change log with id 999 not found",
  "data": null
}
\`\`\`
```

#### 8.1.5 부록 업데이트

```markdown
### 11.x 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| v3.2 | 2026-01-20 | **ConfigChangeLog 시스템 추가**<br>- EnumConfigResourceType (19개 리소스 유형) 추가<br>- EnumConfigActionType (6개 액션 유형) 추가<br>- config_change_logs 테이블 스키마 추가<br>- GET /api/config-change-logs API 추가<br>- GET /api/config-change-logs/{id} API 추가<br>- 전체 CRUD 라우터에 설정 변경 로깅 통합 |
```

#### 8.1.6 전체 Endpoint 목록 업데이트

```markdown
#### Config Change Logs (v3.2)

- `GET /api/config-change-logs` - 로그 목록 조회
- `GET /api/config-change-logs/{id}` - 로그 단건 조회
```

### 8.2 GOP_스키마_전체.md 업데이트

#### 8.2.1 config_change_logs 테이블 추가

```markdown
### config_change_logs (v3.2 신규)

설정 변경 로그 테이블

| 컬럼명 | 타입 | NULL | 기본값 | 설명 |
|--------|------|------|--------|------|
| id | SERIAL | NOT NULL | AUTO | PK |
| resource_type | VARCHAR(50) | NOT NULL | - | EnumConfigResourceType |
| resource_id | INTEGER | NOT NULL | - | 대상 리소스 ID |
| resource_name | VARCHAR(200) | NULL | - | 리소스 식별명 |
| action | VARCHAR(20) | NOT NULL | - | EnumConfigActionType |
| before_state | JSONB | NULL | - | 변경 전 상태 |
| after_state | JSONB | NULL | - | 변경 후 상태 |
| actor_id | INTEGER | NULL | - | FK: account_users.id |
| actor_name | VARCHAR(100) | NULL | - | 수행자 이름 |
| actor_ip | VARCHAR(45) | NULL | - | 수행자 IP |
| description | TEXT | NULL | - | 설명 |
| created_at | TIMESTAMPTZ | NOT NULL | NOW() | 생성 일시 |

**인덱스**:
- idx_config_change_logs_resource (resource_type, resource_id)
- idx_config_change_logs_actor (actor_id)
- idx_config_change_logs_created_at (created_at DESC)
- idx_config_change_logs_action (action)

**FK 관계**:
- actor_id → account_users.id (ON DELETE SET NULL)
```

---

## 9. 구현 작업 목록

### 9.1 Phase 1: 기반 구현

| ID | 작업 | 파일 |
|----|------|------|
| CCL-1.1 | EnumConfigResourceType 정의 | app/utils/enums.py |
| CCL-1.2 | EnumConfigActionType 정의 | app/utils/enums.py |
| CCL-1.3 | ConfigChangeLog 모델 생성 | app/models/config_change_log.py |
| CCL-1.4 | ConfigChangeLog 스키마 생성 | app/schemas/config_change_log.py |
| CCL-1.5 | config_log_service 구현 | app/services/config_log_service.py |

### 9.2 Phase 2: API 구현

| ID | 작업 | 파일 |
|----|------|------|
| CCL-2.1 | config_change_logs 라우터 생성 | app/routers/config_change_logs.py |
| CCL-2.2 | GET /api/config-change-logs 구현 | app/routers/config_change_logs.py |
| CCL-2.3 | GET /api/config-change-logs/{id} 구현 | app/routers/config_change_logs.py |
| CCL-2.4 | main.py에 라우터 등록 | app/main.py |

### 9.3 Phase 3: 라우터 통합 (Device 계열)

| ID | 작업 | 파일 |
|----|------|------|
| CCL-3.1 | controllers.py 로깅 통합 | app/routers/controllers.py |
| CCL-3.2 | sensors.py 로깅 통합 | app/routers/sensors.py |
| CCL-3.3 | cameras.py 로깅 통합 | app/routers/cameras.py |
| CCL-3.4 | speakers.py 로깅 통합 | app/routers/speakers.py |
| CCL-3.5 | enclosures.py 로깅 통합 | app/routers/enclosures.py |
| CCL-3.6 | device_groups.py 로깅 통합 | app/routers/device_groups.py |
| CCL-3.7 | camera_presets.py 로깅 통합 | app/routers/camera_presets.py |
| CCL-3.8 | rois.py 로깅 통합 | app/routers/rois.py |
| CCL-3.9 | xy_points.py 로깅 통합 | app/routers/xy_points.py |
| CCL-3.10 | file_groups.py 로깅 통합 | app/routers/file_groups.py |

### 9.4 Phase 4: 라우터 통합 (Event 계열)

| ID | 작업 | 파일 |
|----|------|------|
| CCL-4.1 | detection_events.py 로깅 통합 | app/routers/detection_events.py |
| CCL-4.2 | malfunction_events.py 로깅 통합 | app/routers/malfunction_events.py |
| CCL-4.3 | connection_events.py 로깅 통합 | app/routers/connection_events.py |
| CCL-4.4 | action_events.py 로깅 통합 | app/routers/action_events.py |

### 9.5 Phase 5: 라우터 통합 (Integration 계열)

| ID | 작업 | 파일 |
|----|------|------|
| CCL-5.1 | event_mappings.py 로깅 통합 | app/routers/event_mappings.py |
| CCL-5.2 | event_mapping_cameras.py 로깅 통합 | app/routers/event_mapping_cameras.py |
| CCL-5.3 | event_mapping_speakers.py 로깅 통합 | app/routers/event_mapping_speakers.py |

### 9.6 Phase 6: 문서 업데이트

| ID | 작업 | 파일 |
|----|------|------|
| CCL-6.1 | GOP_스키마_전체.md 업데이트 | GOP_스키마_전체.md |
| CCL-6.2 | GOP_Restful_Api_연동설계.md 업데이트 | GOP_Restful_Api_연동설계.md |

### 9.7 Phase 7: 테스트

| ID | 작업 | 파일 |
|----|------|------|
| CCL-7.1 | ConfigChangeLog 모델 테스트 | tests/test_config_change_log.py |
| CCL-7.2 | config_log_service 테스트 | tests/test_config_log_service.py |
| CCL-7.3 | API 엔드포인트 테스트 | tests/test_config_change_logs_api.py |
| CCL-7.4 | 통합 테스트 | tests/test_config_change_log_integration.py |

---

## 10. 데이터 보존 정책

### 10.1 보존 기간

- **기본 보존**: 1년
- **장기 보존**: 아카이브 테이블로 이동 (선택적)

### 10.2 자동 정리

```python
# 90일 이전 로그 삭제 (선택적 구현)
DELETE FROM config_change_logs
WHERE created_at < NOW() - INTERVAL '90 days';
```

---

## 11. 완료 조건

- [ ] 모든 Enum 타입이 app/utils/enums.py에 정의됨
- [ ] ConfigChangeLog 모델이 구현되고 마이그레이션 완료
- [ ] 모든 CRUD 라우터에 로깅이 통합됨
- [ ] API 엔드포인트가 정상 동작함
- [ ] GOP_Restful_Api_연동설계.md가 v3.2로 업데이트됨
- [ ] GOP_스키마_전체.md가 업데이트됨
- [ ] 테스트가 모두 통과함

---

## 12. 부록

### 12.1 로깅 시스템 비교

| 시스템 | 목적 | 대상 | 보존 정책 |
|--------|------|------|----------|
| **AuditLog** | 보안 감사 | Account 시스템 CRUD | 영구 보존 |
| **ConfigChangeLog** | 운영 추적 | Device/Event/Integration CRUD | 1년 |
| **SystemEvent** | 모니터링 | 서버/디바이스 상태 | 설정 가능 |
| **UserLoginLog** | 인증 이력 | 로그인/로그아웃 | 설정 가능 |

### 12.2 EnumConfigResourceType 카테고리별 분류

| 카테고리 | 리소스 (개수) |
|----------|--------------|
| Device | CONTROLLER, SENSOR, CAMERA, SPEAKER, ENCLOSURE, DEVICE_GROUP, CAMERA_PRESET, ROI, XY_POINT, FILE_GROUP (10) |
| Event | DETECTION_EVENT, MALFUNCTION_EVENT, CONNECTION_EVENT, ACTION_EVENT (4) |
| Integration | EVENT_MAPPING, EVENT_MAPPING_CAMERA, EVENT_MAPPING_SPEAKER (3) |
| **합계** | **17개** |

> **SystemEvent에서 관리**: SERVER_CATEGORY, SERVER

### 12.3 EnumConfigActionType 적용 매핑

| 액션 | HTTP Method | 적용 예 |
|------|-------------|---------|
| CREATED | POST | POST /api/devices/cameras |
| UPDATED | PATCH, PUT | PATCH /api/devices/cameras/{id} |
| DELETED | DELETE | DELETE /api/devices/cameras/{id} |
| STATUS_CHANGED | PATCH | PATCH /api/devices/enclosures/{id}/status |
| ASSIGNED | POST | POST /api/devices/groups/{id}/devices |
| UNASSIGNED | DELETE | DELETE /api/devices/groups/{group_id}/devices/{device_id} |
