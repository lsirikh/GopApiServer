# PRD: Device is_enable 필드 추가

**문서 버전**: v1.0
**작성일**: 2026-01-13
**상태**: Draft

---

## 1. 개요

### 1.1 목적

Device Base 테이블에 `is_enable` boolean 필드를 추가하여 장비 활성화/비활성화 상태를 관리합니다.

### 1.2 배경

- 기존 `status` 필드(ACTIVATED/DEACTIVATED/ERROR)는 장비의 운영 상태를 나타냄
- `is_enable`은 시스템 관리자가 장비를 논리적으로 활성화/비활성화하는 플래그
- 두 필드의 역할 분리:
  - `status`: 장비의 실제 운영 상태 (자동/수동 변경)
  - `is_enable`: 시스템에서 장비 사용 여부 (관리자 제어)

### 1.3 영향 범위

| 구분 | 대상 |
|------|------|
| **Device 모델** | Device (Base), Controller, Sensor, Camera, Speaker, Enclosure |
| **Device 스키마** | Create, Response, NestedResponse, Update 전체 |
| **DeviceGroup 스키마** | ControllerSummary, SensorSummary, CameraSummary, DeviceSummaryBase |
| **Event 스키마** | DeviceNestedResponse |
| **문서** | GOP_스키마_전체.md (v1.9 → v2.0), GOP_Restful_Api_연동설계.md (v2.8 → v2.9) |

---

## 2. 데이터베이스 변경

### 2.1 devices 테이블 변경

```sql
-- 컬럼 추가
ALTER TABLE devices ADD COLUMN is_enable BOOLEAN NOT NULL DEFAULT TRUE;

-- 인덱스 추가 (필터링 성능 최적화)
CREATE INDEX idx_devices_is_enable ON devices(is_enable);
```

### 2.2 필드 정의

| 필드명 | 타입 | NULL 허용 | 기본값 | 설명 |
|--------|------|-----------|--------|------|
| is_enable | BOOLEAN | NO | TRUE | 장비 활성화 여부 (관리자 제어) |

### 2.3 마이그레이션 영향

- **기존 데이터**: 모든 기존 Device에 `is_enable=True` 자동 적용 (기본값)
- **하위 호환성**: 기존 API 클라이언트는 영향 없음 (필드 추가만)

---

## 3. 모델 변경

### 3.1 Device Base 모델 (app/models/device.py)

```python
class Device(Base):
    __tablename__ = "devices"

    # ... 기존 필드 ...

    # 신규 필드
    is_enable = Column(Boolean, nullable=False, default=True, comment="장비 활성화 여부")
```

> **상속 특성**: Controller, Sensor, Camera, Speaker, Enclosure는 Device를 상속하므로 자동으로 is_enable 필드 포함

---

## 4. 스키마 변경

### 4.1 변경 대상 스키마 목록

| 파일 | 스키마 | 변경 내용 |
|------|--------|-----------|
| app/schemas/device.py | ControllerCreate | is_enable 필드 추가 (Optional, default=True) |
| app/schemas/device.py | ControllerResponse | is_enable 필드 추가 |
| app/schemas/device.py | ControllerNestedResponse | is_enable 필드 추가 |
| app/schemas/device.py | ControllerUpdate | is_enable 필드 추가 (Optional) |
| app/schemas/device.py | SensorCreate | is_enable 필드 추가 (Optional, default=True) |
| app/schemas/device.py | SensorResponse | is_enable 필드 추가 |
| app/schemas/device.py | SensorNestedResponse | is_enable 필드 추가 |
| app/schemas/device.py | SensorUpdate | is_enable 필드 추가 (Optional) |
| app/schemas/device.py | CameraCreate | is_enable 필드 추가 (Optional, default=True) |
| app/schemas/device.py | CameraResponse | is_enable 필드 추가 |
| app/schemas/device.py | CameraNestedResponse | is_enable 필드 추가 |
| app/schemas/device.py | CameraUpdate | is_enable 필드 추가 (Optional) |
| app/schemas/device.py | SpeakerCreate | is_enable 필드 추가 (Optional, default=True) |
| app/schemas/device.py | SpeakerResponse | is_enable 필드 추가 |
| app/schemas/device.py | SpeakerNestedResponse | is_enable 필드 추가 |
| app/schemas/device.py | SpeakerUpdate | is_enable 필드 추가 (Optional) |
| app/schemas/device.py | DeviceNestedResponse | is_enable 필드 추가 |
| app/schemas/device_group.py | DeviceSummaryBase | is_enable 필드 추가 |
| app/schemas/device_group.py | ControllerSummary | 상속으로 자동 포함 |
| app/schemas/device_group.py | SensorSummary | 상속으로 자동 포함 |
| app/schemas/device_group.py | CameraSummary | 상속으로 자동 포함 |

### 4.2 스키마 필드 정의

```python
# Create 스키마 (선택적, 기본값 True)
is_enable: bool = Field(True, description="장비 활성화 여부 (기본값: True)")

# Response 스키마 (필수)
is_enable: bool = Field(..., description="장비 활성화 여부")

# Update 스키마 (선택적)
is_enable: Optional[bool] = Field(None, description="장비 활성화 여부")

# Swagger Example
json_schema_extra={"example": True}
```

---

## 5. API 응답 변경

### 5.1 Controller API

#### GET /api/devices/controllers/{id} Response 변경

```json
{
  "success": true,
  "message": "Controller retrieved successfully",
  "data": {
    "id": 1,
    "number_device": 1,
    "group_device": 1,
    "name_device": "Controller-A",
    "type_device": "Controller",
    "version": "v2.1.0",
    "status": "ACTIVATED",
    "is_enable": true,
    "ip_address": "192.168.1.100",
    "ip_port": 8001,
    "geolocation": {...},
    "created_at": "2025-01-01T00:00:00.000Z",
    "updated_at": "2025-01-01T00:00:00.000Z",
    "device_groups": [...]
  }
}
```

### 5.2 Sensor API

#### GET /api/devices/sensors/{id} Response 변경

```json
{
  "success": true,
  "message": "Sensor retrieved successfully",
  "data": {
    "id": 101,
    "number_device": 1,
    "group_device": 1,
    "name_device": "Sensor-A-1",
    "type_device": "Multi",
    "version": "v1.5.0",
    "status": "ACTIVATED",
    "is_enable": true,
    "controller_id": 1,
    "geolocation": {...},
    "created_at": "2025-01-01T00:00:00.000Z",
    "updated_at": "2025-01-01T00:00:00.000Z",
    "device_groups": [...]
  }
}
```

### 5.3 Camera API

#### GET /api/devices/cameras/{id} Response 변경

```json
{
  "success": true,
  "message": "Camera retrieved successfully",
  "data": {
    "id": 201,
    "number_device": 1,
    "group_device": 1,
    "name_device": "Camera-A-1",
    "type_device": "IpCamera",
    "version": "v1.0.0",
    "status": "ACTIVATED",
    "is_enable": true,
    "ip_address": "192.168.1.200",
    "ip_port": 80,
    "user_name": "admin",
    "user_password": "admin1234",
    "mode": "RTSP",
    "category": "PTZ",
    "is_record": true,
    "urls": {...},
    "hardware_spec": {...},
    "geolocation": {...},
    "created_at": "2025-01-01T00:00:00.000Z",
    "updated_at": "2025-01-01T00:00:00.000Z",
    "device_groups": [...]
  }
}
```

### 5.4 Speaker API

#### GET /api/devices/speakers/{id} Response 변경

```json
{
  "success": true,
  "message": "Speaker retrieved successfully",
  "data": {
    "id": 301,
    "number_device": 2401,
    "group_device": 0,
    "name_device": "VCS_2401",
    "type_device": "IpSpeaker",
    "version": null,
    "status": "ACTIVATED",
    "is_enable": true,
    "speaker_type": "NORMAL",
    "description": "1구역 스피커",
    "geolocation": {...},
    "created_at": "2025-01-01T00:00:00.000Z",
    "updated_at": "2025-01-01T00:00:00.000Z",
    "server": {...}
  }
}
```

### 5.5 DeviceGroup API (Nested Device)

#### GET /api/devices/groups/{id} Response 변경

```json
{
  "success": true,
  "message": "디바이스 그룹 조회 성공",
  "data": {
    "id": 1,
    "name": "GOP 1구역",
    "description": "GOP 1구역 장비 그룹",
    "device_count": 3,
    "devices": [
      {
        "id": 1,
        "number_device": 1,
        "group_device": 1,
        "name_device": "Controller-A",
        "type_device": "Controller",
        "version": "v2.1.0",
        "status": "ACTIVATED",
        "is_enable": true,
        "ip_address": "192.168.1.100",
        "ip_port": 8001,
        "geolocation": {...},
        "device_groups": [...]
      },
      {
        "id": 101,
        "number_device": 1,
        "group_device": 1,
        "name_device": "Sensor-A-1",
        "type_device": "Multi",
        "version": "v1.5.0",
        "status": "ACTIVATED",
        "is_enable": true,
        "controller_id": 1,
        "geolocation": {...},
        "device_groups": [...]
      },
      {
        "id": 201,
        "number_device": 1,
        "group_device": 1,
        "name_device": "Camera-A-1",
        "type_device": "IpCamera",
        "version": "v1.0.0",
        "status": "ACTIVATED",
        "is_enable": true,
        "ip_address": "192.168.1.200",
        "ip_port": 80,
        "urls": {...},
        "mode": "RTSP",
        "camera_category": "PTZ",
        "is_record": true,
        "hardware_spec": {...},
        "geolocation": {...},
        "device_groups": [...]
      }
    ],
    "created_at": "2025-01-01T00:00:00.000Z",
    "updated_at": "2025-01-01T00:00:00.000Z"
  }
}
```

### 5.6 Event API (DeviceNestedResponse)

Event 응답의 `device` nested 객체에도 `is_enable` 필드 포함:

```json
{
  "device": {
    "id": 101,
    "number_device": 1,
    "group_device": 1,
    "name_device": "Sensor-A-1",
    "type_device": "Multi",
    "status": "ACTIVATED",
    "is_enable": true,
    "controller_id": 1,
    "device_groups": [...]
  }
}
```

---

## 6. 문서 업데이트 가이드

### 6.1 GOP_스키마_전체.md 업데이트

**버전**: v1.9 → v2.0
**날짜**: 2026-01-13

#### 업데이트 항목

| 섹션 | 변경 내용 |
|------|-----------|
| 헤더 | 버전 v2.0, 날짜 2026-01-13 |
| 2.1 devices 테이블 | is_enable 컬럼 추가 |
| 10. 변경 이력 | v2.0 변경 내용 추가 |

#### 2.1 devices 테이블 필드 정의 추가

```markdown
| is_enable | BOOLEAN | NO | TRUE | 장비 활성화 여부 (관리자 제어) |
```

#### 2.1 devices 테이블 CREATE TABLE 수정

```sql
CREATE TABLE devices (
    id SERIAL PRIMARY KEY,
    category_device enum_device_category NOT NULL,
    number_device INTEGER NOT NULL,
    group_device INTEGER NOT NULL,
    name_device VARCHAR(200) NOT NULL,
    type_device enum_device_type NOT NULL,
    version VARCHAR(50),
    status enum_device_status NOT NULL DEFAULT 'ACTIVATED',
    is_enable BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_devices_id ON devices(id);
CREATE INDEX idx_devices_category_device ON devices(category_device);
CREATE INDEX idx_devices_number_device ON devices(number_device);
CREATE INDEX idx_devices_group_device ON devices(group_device);
CREATE INDEX idx_devices_is_enable ON devices(is_enable);
```

#### 변경 이력 추가

```markdown
| **v2.0** | 2026-01-13 | **Device is_enable 필드 추가**<br>• **devices.is_enable BOOLEAN 추가**: 장비 활성화 여부 (기본값: TRUE)<br>• **인덱스 추가**: idx_devices_is_enable<br>• **상속 적용**: Controller, Sensor, Camera, Speaker, Enclosure에 자동 적용 |
```

---

### 6.2 GOP_Restful_Api_연동설계.md 업데이트

**버전**: v2.8 → v2.9
**날짜**: 2026-01-13

#### 업데이트 항목

| 섹션 | 변경 내용 |
|------|-----------|
| 헤더 | 버전 v2.9, 최종 수정일 2026-01-13 |
| 5.1 Controller API | Request/Response에 is_enable 필드 추가 |
| 5.2 Sensor API | Request/Response에 is_enable 필드 추가 |
| 5.3 Camera API | Request/Response에 is_enable 필드 추가 |
| 5.4 Speaker API | Request/Response에 is_enable 필드 추가 |
| 5.5 Enclosure API | Request/Response에 is_enable 필드 추가 |
| 5.6 DeviceGroup API | Nested Device에 is_enable 필드 추가 |
| 6.x Event API | DeviceNestedResponse에 is_enable 필드 추가 |
| 변경 이력 | v2.9 변경 내용 추가 |

#### Request Body 필드 추가 (POST, PATCH, PUT)

```markdown
| is_enable | boolean | N | 장비 활성화 여부 (기본값: true) |
```

#### Response 필드 추가

```markdown
| is_enable | boolean | 장비 활성화 여부 |
```

#### 변경 이력 추가

```markdown
| v2.9 | 2026-01-13 | **Device is_enable 필드 추가**<br><br>**[1. Device Base 공통 필드 추가]**<br>- **is_enable 필드 추가**: boolean, 기본값 true<br>- **용도**: 시스템 관리자가 장비를 논리적으로 활성화/비활성화<br>- **status와 구분**: status는 운영 상태, is_enable은 사용 여부<br><br>**[2. 영향 받는 API]**<br>- **Controller API**: POST/PATCH/PUT Request, GET Response에 is_enable 추가<br>- **Sensor API**: POST/PATCH/PUT Request, GET Response에 is_enable 추가<br>- **Camera API**: POST/PATCH/PUT Request, GET Response에 is_enable 추가<br>- **Speaker API**: POST/PATCH/PUT Request, GET Response에 is_enable 추가<br>- **Enclosure API**: POST/PATCH/PUT Request, GET Response에 is_enable 추가<br>- **DeviceGroup API**: Nested Device Response에 is_enable 추가<br>- **Event API**: DeviceNestedResponse에 is_enable 추가 |
```

---

## 7. Swagger/OpenAPI 업데이트

### 7.1 자동 업데이트 항목

Pydantic 스키마 변경 시 FastAPI가 자동으로 Swagger/ReDoc 업데이트:

- `/docs` (Swagger UI)
- `/redoc` (ReDoc)
- `/openapi.json` (OpenAPI 스펙)

### 7.2 Example 업데이트

각 Device API 라우터의 `responses` OpenAPI 예제에 `is_enable` 필드 추가 필요:

- `app/routers/controllers.py`
- `app/routers/sensors.py`
- `app/routers/cameras.py`
- `app/routers/speakers.py`
- `app/routers/enclosures.py`
- `app/routers/device_groups.py`

---

## 8. 구현 순서

### Phase 1: 데이터베이스 및 모델 변경

1. [ ] `app/models/device.py`: Device 클래스에 is_enable 컬럼 추가
2. [ ] DB 마이그레이션 스크립트 작성 (Alembic 또는 수동)
3. [ ] 마이그레이션 실행 및 검증

### Phase 2: 스키마 변경

1. [ ] `app/schemas/device.py`: Controller 스키마 업데이트
2. [ ] `app/schemas/device.py`: Sensor 스키마 업데이트
3. [ ] `app/schemas/device.py`: Camera 스키마 업데이트
4. [ ] `app/schemas/device.py`: Speaker 스키마 업데이트
5. [ ] `app/schemas/device.py`: DeviceNestedResponse 업데이트
6. [ ] `app/schemas/device_group.py`: DeviceSummaryBase 업데이트

### Phase 3: API 라우터 업데이트

1. [ ] `app/routers/controllers.py`: Create/Update 로직에 is_enable 처리
2. [ ] `app/routers/sensors.py`: Create/Update 로직에 is_enable 처리
3. [ ] `app/routers/cameras.py`: Create/Update 로직에 is_enable 처리
4. [ ] `app/routers/speakers.py`: Create/Update 로직에 is_enable 처리
5. [ ] `app/routers/enclosures.py`: Create/Update 로직에 is_enable 처리

### Phase 4: Swagger 예제 업데이트

1. [ ] `app/routers/controllers.py`: OpenAPI responses 예제에 is_enable 추가
2. [ ] `app/routers/sensors.py`: OpenAPI responses 예제에 is_enable 추가
3. [ ] `app/routers/cameras.py`: OpenAPI responses 예제에 is_enable 추가
4. [ ] `app/routers/speakers.py`: OpenAPI responses 예제에 is_enable 추가
5. [ ] `app/routers/enclosures.py`: OpenAPI responses 예제에 is_enable 추가
6. [ ] `app/routers/device_groups.py`: OpenAPI responses 예제에 is_enable 추가

### Phase 5: 문서 업데이트

1. [ ] `docs/GOP_스키마_전체.md`: v2.0으로 업데이트
2. [ ] `GOP_Restful_Api_연동설계.md`: v2.9로 업데이트

### Phase 6: 테스트 및 검증

1. [ ] 단위 테스트 작성 및 실행
2. [ ] API 통합 테스트
3. [ ] Swagger UI 검증
4. [ ] 기존 기능 회귀 테스트

---

## 9. 테스트 케이스

### 9.1 Controller API 테스트

```python
def test_create_controller_with_is_enable_default():
    """is_enable 미지정 시 기본값 True"""
    response = client.post("/api/devices/controllers", json={...})
    assert response.json()["data"]["is_enable"] == True

def test_create_controller_with_is_enable_false():
    """is_enable=False로 생성"""
    response = client.post("/api/devices/controllers", json={"is_enable": False, ...})
    assert response.json()["data"]["is_enable"] == False

def test_update_controller_is_enable():
    """is_enable 업데이트"""
    response = client.patch("/api/devices/controllers/1", json={"is_enable": False})
    assert response.json()["data"]["is_enable"] == False
```

### 9.2 DeviceGroup API 테스트

```python
def test_device_group_devices_include_is_enable():
    """DeviceGroup 조회 시 devices에 is_enable 포함"""
    response = client.get("/api/devices/groups/1?include_devices=true")
    devices = response.json()["data"]["devices"]
    for device in devices:
        assert "is_enable" in device
```

---

## 10. 롤백 계획

### 10.1 데이터베이스 롤백

```sql
ALTER TABLE devices DROP COLUMN is_enable;
DROP INDEX IF EXISTS idx_devices_is_enable;
```

### 10.2 코드 롤백

Git revert를 통해 이전 상태로 복원 가능

---

**문서 종료**
