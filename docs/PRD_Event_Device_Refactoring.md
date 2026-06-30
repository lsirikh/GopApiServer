# PRD: Event-Device 관계 리팩토링

**문서 버전**: v1.1
**작성일**: 2025-12-31
**작성자**: Claude Code Assistant
**상태**: Draft

---

## 1. 개요

### 1.1 배경

현재 Event 모델(DetectionEvent, MalfunctionEvent, ConnectionEvent)은 Device를 참조할 때 `controller`, `sensor`, `type_device` 3개의 별도 필드를 사용하고 있습니다. 이는 다음과 같은 문제를 야기합니다:

1. **참조 무결성 부재**: FK가 없어 존재하지 않는 Device를 참조할 수 있음
2. **정규화 위반**: `type_device`가 Device 테이블과 Event 테이블에 중복 저장
3. **복잡한 조회**: Device 정보를 가져오려면 `number_device` 기반 수동 조회 필요
4. **Polymorphic 구조 미활용**: Device가 상속 구조임에도 단일 FK로 참조하지 않음

### 1.2 목표

- Event 모델에서 `device_id` 단일 FK로 Device 참조
- Response에서 `device` nested 객체로 폴리모픽 Device 정보 반환
- 참조 무결성 및 정규화 달성
- API 스펙 간소화
- **Event 데이터 영속성 보장**: Device 삭제 시에도 Event 데이터 유지
- **device_description 필드 추가**: Device 정보의 스냅샷 저장

### 1.3 범위

| 대상 | 포함 여부 |
|------|----------|
| DetectionEvent | O |
| MalfunctionEvent | O |
| ConnectionEvent | O |
| ActionEvent | O (from_event nested 내 device 포함) |

---

## 2. 현재 구조 분석

### 2.1 현재 Event Model 필드

```python
# DetectionEvent, MalfunctionEvent, ConnectionEvent 공통
controller = Column(Integer, nullable=False)      # Controller의 number_device
sensor = Column(Integer, nullable=False)          # Sensor의 number_device
type_device = Column(SQLEnum(EnumDeviceType))     # Device 타입 (중복 저장)
```

### 2.2 현재 API Request/Response

**Request:**
```json
{
  "controller": 1,
  "sensor": 2,
  "type_device": "Fence",
  ...
}
```

**Response:**
```json
{
  "controller": 1,
  "sensor": 2,
  "type_device": "Fence",
  ...
}
```

### 2.3 문제점

| 문제 | 설명 |
|------|------|
| **FK 부재** | `controller`, `sensor`는 단순 Integer로 Device.id가 아닌 number_device 저장 |
| **참조 무결성 없음** | 존재하지 않는 controller/sensor 번호도 저장 가능 |
| **중복 저장** | `type_device`가 Device와 Event에 모두 저장됨 |
| **조회 복잡** | Device 정보 조회 시 number_device 기반 수동 매핑 필요 |

---

## 3. 변경 설계

### 3.1 Model 변경

#### 3.1.1 Event Base 필드 변경

**Before:**
```python
controller = Column(Integer, nullable=False, index=True)
sensor = Column(Integer, nullable=False, index=True)
type_device = Column(SQLEnum(EnumDeviceType), nullable=False)
```

**After:**
```python
# FK with SET NULL on delete - Event 데이터는 Device 삭제 시에도 유지
device_id = Column(Integer, ForeignKey("devices.id", ondelete="SET NULL"), nullable=True, index=True)
device = relationship("Device")  # Polymorphic relationship

# Device 정보 스냅샷 - device_id 할당 시 자동 생성
device_description = Column(String(500), nullable=True)
```

#### 3.1.2 device_description 필드 상세

**목적**: Device가 삭제되더라도 Event에서 참조했던 Device 정보를 유지

**자동 생성 규칙**: `device_id` 할당 시 아래 형식으로 자동 생성

```
"[{type_device}] {name_device} (number: {number_device}, id: {device_id})"
```

**예시:**
```
"[Controller] Controller-A (number: 1, id: 1)"
"[Fence] Sensor-A-1 (number: 1, id: 101)"
"[IpCamera] Camera-A-1 (number: 1, id: 201)"
```

**동작 시나리오:**

| 시나리오 | device_id | device_description | device (Response) |
|----------|-----------|-------------------|-------------------|
| Event 생성 | 101 | "[Fence] Sensor-A..." | Nested Object |
| Device 조회 | 101 | "[Fence] Sensor-A..." | Nested Object |
| Device 삭제 후 | NULL | "[Fence] Sensor-A..." | null |

#### 3.1.3 Cascade 정책 (중요)

> **핵심 원칙: Event 데이터는 어떤 경우에도 삭제되지 않아야 한다.**

| 동작 | 정책 | 결과 |
|------|------|------|
| Device 삭제 | `ondelete="SET NULL"` | Event.device_id → NULL, Event 유지 |
| Event 삭제 | 독립적 | Device 영향 없음 |

```python
# 올바른 FK 설정 (CASCADE 사용 금지!)
device_id = Column(
    Integer,
    ForeignKey("devices.id", ondelete="SET NULL"),  # NOT CASCADE!
    nullable=True,  # SET NULL 허용을 위해 nullable
    index=True
)
```

#### 3.1.4 적용 대상 모델

| Model | 변경 사항 |
|-------|----------|
| DetectionEvent | `controller`, `sensor`, `type_device` → `device_id`, `device_description` |
| MalfunctionEvent | `controller`, `sensor`, `type_device` → `device_id`, `device_description` |
| ConnectionEvent | `controller`, `sensor`, `type_device` → `device_id`, `device_description` |

### 3.2 Schema 변경

#### 3.2.1 Request Schema

**DetectionEventCreate:**
```python
class DetectionEventCreate(BaseModel):
    group_event: str
    type_event: str = "Intrusion"
    device_id: int                    # 변경: 단일 FK
    sequence: int
    result: str                       # EnumDetectionType
```

**MalfunctionEventCreate:**
```python
class MalfunctionEventCreate(BaseModel):
    group_event: str
    type_event: str = "Fault"
    device_id: int                    # 변경: 단일 FK
    sequence: int
    reason: str                       # EnumFaultType
    first_start: int
    first_end: int
    second_start: int
    second_end: int
```

**ConnectionEventCreate:**
```python
class ConnectionEventCreate(BaseModel):
    group_event: str
    type_event: str = "Connection"
    device_id: int                    # 변경: 단일 FK
    sequence: int
```

#### 3.2.2 Response Schema

**DeviceNestedResponse (폴리모픽):**
```python
class DeviceNestedResponse(BaseModel):
    """폴리모픽 Device Response - 타입에 따라 다른 필드 포함"""
    id: int
    number_device: int
    group_device: int
    name_device: str
    type_device: str                  # EnumDeviceType
    version: Optional[str]
    status: str                       # EnumDeviceStatus

    # Controller 전용
    ip_address: Optional[str] = None
    ip_port: Optional[int] = None

    # Sensor 전용
    controller_id: Optional[int] = None

    # Camera 전용 (필요시)
    rtsp_uri: Optional[str] = None
    mode: Optional[str] = None
    category: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
```

**DetectionEventResponse:**
```python
class DetectionEventResponse(BaseModel):
    id: int
    group_event: str
    type_event: str
    sequence: int
    action_reported: str
    result: str
    device: Optional[DeviceNestedResponse] = None  # Device 삭제 시 null
    device_description: Optional[str] = None       # Device 정보 스냅샷 (항상 유지)
    created_at: datetime
    updated_at: datetime
```

---

## 4. API 스펙 변경

### 4.1 Detection Event

#### POST /api/events/detections

**Request:**
```json
{
  "group_event": "GROUP_001",
  "type_event": "Intrusion",
  "device_id": 101,
  "sequence": 10,
  "result": "PIR_SENSOR"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Detection event created successfully",
  "data": {
    "id": 1001,
    "group_event": "GROUP_001",
    "type_event": "Intrusion",
    "sequence": 10,
    "action_reported": "False",
    "result": "PIR_SENSOR",
    "device": {
      "id": 101,
      "number_device": 1,
      "group_device": 1,
      "name_device": "Sensor-A-1",
      "type_device": "Multi",
      "version": "v1.5.0",
      "status": "ACTIVATED",
      "controller_id": 1
    },
    "device_description": "[Multi] Sensor-A-1 (number: 1, id: 101)",
    "created_at": "2025-01-10T10:15:23.100Z",
    "updated_at": "2025-01-10T10:15:23.100Z"
  }
}
```

#### GET /api/events/detections/{id}

**Response (200 OK) - Device 존재:**
```json
{
  "success": true,
  "message": "Detection event retrieved successfully",
  "data": {
    "id": 1001,
    "group_event": "GROUP_001",
    "type_event": "Intrusion",
    "sequence": 10,
    "action_reported": "False",
    "result": "PIR_SENSOR",
    "device": {
      "id": 101,
      "number_device": 1,
      "group_device": 1,
      "name_device": "Sensor-A-1",
      "type_device": "Multi",
      "version": "v1.5.0",
      "status": "ACTIVATED",
      "controller_id": 1
    },
    "device_description": "[Multi] Sensor-A-1 (number: 1, id: 101)",
    "created_at": "2025-01-10T10:15:23.100Z",
    "updated_at": "2025-01-10T10:15:23.100Z"
  }
}
```

**Response (200 OK) - Device 삭제됨:**
```json
{
  "success": true,
  "message": "Detection event retrieved successfully",
  "data": {
    "id": 1001,
    "group_event": "GROUP_001",
    "type_event": "Intrusion",
    "sequence": 10,
    "action_reported": "False",
    "result": "PIR_SENSOR",
    "device": null,
    "device_description": "[Multi] Sensor-A-1 (number: 1, id: 101)",
    "created_at": "2025-01-10T10:15:23.100Z",
    "updated_at": "2025-01-10T10:15:23.100Z"
  }
}
```

### 4.2 Malfunction Event

#### POST /api/events/malfunctions

**Request:**
```json
{
  "group_event": "GROUP_FAULT_001",
  "type_event": "Fault",
  "device_id": 1,
  "sequence": 5,
  "reason": "FAULT_CONTROLLER",
  "first_start": 10,
  "first_end": 15,
  "second_start": 0,
  "second_end": 0
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Malfunction event created successfully",
  "data": {
    "id": 2001,
    "group_event": "GROUP_FAULT_001",
    "type_event": "Fault",
    "sequence": 5,
    "action_reported": "False",
    "reason": "FAULT_CONTROLLER",
    "first_start": 10,
    "first_end": 15,
    "second_start": 0,
    "second_end": 0,
    "device": {
      "id": 1,
      "number_device": 1,
      "group_device": 1,
      "name_device": "Controller-A",
      "type_device": "Controller",
      "version": "v2.1.0",
      "status": "ERROR",
      "ip_address": "192.168.1.100",
      "ip_port": 8001
    },
    "device_description": "[Controller] Controller-A (number: 1, id: 1)",
    "created_at": "2025-01-10T14:20:00.500Z",
    "updated_at": "2025-01-10T14:20:00.500Z"
  }
}
```

### 4.3 Connection Event

#### POST /api/events/connections

**Request:**
```json
{
  "group_event": "GROUP_CONN_001",
  "type_event": "Connection",
  "device_id": 102,
  "sequence": 3
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Connection event created successfully",
  "data": {
    "id": 3001,
    "group_event": "GROUP_CONN_001",
    "type_event": "Connection",
    "sequence": 3,
    "device": {
      "id": 102,
      "number_device": 2,
      "group_device": 1,
      "name_device": "Fence-Sensor-02",
      "type_device": "Fence",
      "version": "v1.5.0",
      "status": "ACTIVATED",
      "controller_id": 1
    },
    "device_description": "[Fence] Fence-Sensor-02 (number: 2, id: 102)",
    "created_at": "2025-01-10T09:00:00.100Z",
    "updated_at": "2025-01-10T09:00:00.100Z"
  }
}
```

### 4.4 Action Event

#### POST /api/events/actions

**Request:**
```json
{
  "content": "침입 탐지 확인 및 순찰 출동 요청",
  "user": "operator_kim",
  "from_event": 1001,
  "from_type_event": "Intrusion"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Action event created successfully",
  "data": {
    "id": 4001,
    "type_event": "Action",
    "content": "침입 탐지 확인 및 순찰 출동 요청",
    "user": "operator_kim",
    "from_event": {
      "id": 1001,
      "group_event": "GROUP_001",
      "type_event": "Intrusion",
      "sequence": 10,
      "action_reported": "True",
      "result": "PIR_SENSOR",
      "device": {
        "id": 101,
        "number_device": 1,
        "group_device": 1,
        "name_device": "Sensor-A-1",
        "type_device": "Multi",
        "version": "v1.5.0",
        "status": "ACTIVATED",
        "controller_id": 1
      },
      "device_description": "[Multi] Sensor-A-1 (number: 1, id: 101)",
      "created_at": "2025-01-10T10:15:23.100Z",
      "updated_at": "2025-01-10T10:20:00.000Z"
    },
    "created_at": "2025-01-10T10:20:00.000Z",
    "updated_at": "2025-01-10T10:20:00.000Z"
  }
}
```

---

## 5. 데이터베이스 마이그레이션

### 5.1 마이그레이션 전략

1. **새 컬럼 추가**: `device_id`, `device_description` 컬럼을 nullable로 추가
2. **데이터 마이그레이션**: 기존 `controller`, `sensor`, `type_device` 조합으로 Device.id 매핑
3. **device_description 자동 생성**: 매핑된 Device 정보로 description 생성
4. **FK 제약 추가**: `ondelete="SET NULL"` (CASCADE 금지!)
5. **기존 컬럼 제거**: `controller`, `sensor`, `type_device` 컬럼 삭제

> **중요**: `device_id`는 nullable로 유지 (SET NULL을 위해)

### 5.2 마이그레이션 SQL (예시)

```sql
-- Step 1: 새 컬럼 추가
ALTER TABLE detection_events ADD COLUMN device_id INTEGER;
ALTER TABLE detection_events ADD COLUMN device_description VARCHAR(500);
ALTER TABLE malfunction_events ADD COLUMN device_id INTEGER;
ALTER TABLE malfunction_events ADD COLUMN device_description VARCHAR(500);
ALTER TABLE connection_events ADD COLUMN device_id INTEGER;
ALTER TABLE connection_events ADD COLUMN device_description VARCHAR(500);

-- Step 2: 데이터 마이그레이션 (Sensor 기준)
UPDATE detection_events de
SET device_id = (
    SELECT d.id FROM devices d
    JOIN sensors s ON d.id = s.id
    WHERE d.number_device = de.sensor
    AND d.category_device = 'sensor'
    LIMIT 1
);

-- Step 3: device_description 자동 생성
UPDATE detection_events de
SET device_description = (
    SELECT '[' || d.type_device || '] ' || d.name_device || ' (number: ' || d.number_device || ', id: ' || d.id || ')'
    FROM devices d
    WHERE d.id = de.device_id
);

-- Step 4: FK 제약 추가 (SET NULL - CASCADE 금지!)
ALTER TABLE detection_events
    ADD CONSTRAINT fk_detection_device
    FOREIGN KEY (device_id) REFERENCES devices(id)
    ON DELETE SET NULL;  -- 중요: CASCADE 사용 금지!

-- Step 5: 기존 컬럼 제거 (선택적)
-- ALTER TABLE detection_events DROP COLUMN controller;
-- ALTER TABLE detection_events DROP COLUMN sensor;
-- ALTER TABLE detection_events DROP COLUMN type_device;
```

### 5.3 하위 호환성 옵션

기존 API와의 호환성을 위해 두 가지 접근법 가능:

**Option A: Breaking Change**
- 기존 `controller`, `sensor`, `type_device` 완전 제거
- 클라이언트 업데이트 필수

**Option B: 점진적 마이그레이션**
- 기존 필드 유지 (deprecated)
- Request에서 `device_id` 또는 `controller`+`sensor` 둘 다 허용
- Response에서 `device` nested + 기존 필드 모두 반환

---

## 6. Device Nested Response 상세

### 6.1 폴리모픽 필드 매핑

| Device Type | 추가 필드 |
|-------------|----------|
| Controller | `ip_address`, `ip_port` |
| Sensor | `controller_id` |
| Camera | `ip_address`, `ip_port`, `user_name`, `rtsp_uri`, `rtsp_port`, `mode`, `category`, `is_record`, `hardware_spec`, `geolocation` |

### 6.2 Response 예시 - Controller

```json
{
  "device": {
    "id": 1,
    "number_device": 1,
    "group_device": 1,
    "name_device": "Controller-A",
    "type_device": "Controller",
    "version": "v2.1.0",
    "status": "ACTIVATED",
    "ip_address": "192.168.1.100",
    "ip_port": 8001
  }
}
```

### 6.3 Response 예시 - Sensor

```json
{
  "device": {
    "id": 101,
    "number_device": 1,
    "group_device": 1,
    "name_device": "Sensor-A-1",
    "type_device": "Multi",
    "version": "v1.5.0",
    "status": "ACTIVATED",
    "controller_id": 1
  }
}
```

### 6.4 Response 예시 - Camera

```json
{
  "device": {
    "id": 201,
    "number_device": 1,
    "group_device": 1,
    "name_device": "Camera-A-1",
    "type_device": "IpCamera",
    "version": "v3.2.1",
    "status": "ACTIVATED",
    "ip_address": "192.168.1.200",
    "ip_port": 80,
    "rtsp_uri": "rtsp://192.168.1.200:554/stream1",
    "rtsp_port": 554,
    "mode": "ONVIF",
    "category": "PTZ",
    "is_record": true
  }
}
```

---

## 7. 구현 계획

### 7.1 Phase 1: Model 및 Schema 변경

| 단계 | 작업 | 파일 |
|------|------|------|
| 1.1 | DeviceNestedResponse 스키마 생성 | `app/schemas/device.py` |
| 1.2 | Event Model에 device_id FK 추가 | `app/models/event.py` |
| 1.3 | Event Schema 변경 (Request/Response) | `app/schemas/event.py` |

### 7.2 Phase 2: Router 변경

| 단계 | 작업 | 파일 |
|------|------|------|
| 2.1 | Detection Router 수정 | `app/routers/detections.py` |
| 2.2 | Malfunction Router 수정 | `app/routers/malfunctions.py` |
| 2.3 | Connection Router 수정 | `app/routers/connections.py` |
| 2.4 | Action Router 수정 (nested 포함) | `app/routers/actions.py` |

### 7.3 Phase 3: 테스트

| 단계 | 작업 |
|------|------|
| 3.1 | Event Model 테스트 |
| 3.2 | Event Schema 테스트 |
| 3.3 | Event Router 테스트 |
| 3.4 | 통합 테스트 |

### 7.4 Phase 4: 마이그레이션

| 단계 | 작업 |
|------|------|
| 4.1 | 마이그레이션 스크립트 작성 |
| 4.2 | 테스트 DB 마이그레이션 |
| 4.3 | 운영 DB 마이그레이션 |

---

## 8. 변경 요약

### 8.1 Request 변경

| Event Type | Before | After |
|------------|--------|-------|
| Detection | `controller`, `sensor`, `type_device` | `device_id` |
| Malfunction | `controller`, `sensor`, `type_device` | `device_id` |
| Connection | `controller`, `sensor`, `type_device` | `device_id` |
| Action | 변경 없음 | 변경 없음 |

### 8.2 Response 변경

| Event Type | Before | After |
|------------|--------|-------|
| Detection | `controller`, `sensor`, `type_device` (Integer/String) | `device` (Nested, nullable), `device_description` (String) |
| Malfunction | `controller`, `sensor`, `type_device` (Integer/String) | `device` (Nested, nullable), `device_description` (String) |
| Connection | `controller`, `sensor`, `type_device` (Integer/String) | `device` (Nested, nullable), `device_description` (String) |
| Action | `from_event` 내 기존 필드 | `from_event.device` (Nested), `from_event.device_description` (String) |

### 8.3 주요 이점

1. **단순화**: 3개 필드 → 1개 필드 (Request)
2. **참조 무결성**: FK로 Device 존재 보장 (soft reference)
3. **정규화**: `type_device` 중복 제거
4. **풍부한 정보**: Response에서 Device 전체 정보 제공
5. **폴리모픽 지원**: Device 타입별 다른 필드 자동 포함
6. **Event 영속성**: Device 삭제 시에도 Event 데이터 유지
7. **Device 정보 보존**: `device_description`으로 삭제된 Device 정보 참조 가능

---

## 9. 참고 사항

### 9.1 관련 문서

- [PRD_Device_Structure_Refactoring.md](PRD_Device_Structure_Refactoring.md)
- [PRD_Device_Inheritance_Structure_Refactoring.md](PRD_Device_Inheritance_Structure_Refactoring.md)
- [GOP_Restful_Api_연동설계.md](../GOP_Restful_Api_연동설계.md)

### 9.2 주의 사항

- `category_device`는 Polymorphic Discriminator 용도이므로 API Response에 포함하지 않음
- 기존 데이터 마이그레이션 시 `number_device` → `device.id` 매핑 주의
- Camera 타입의 경우 민감 정보(`user_password`) Response 포함 여부 검토 필요

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| v1.0 | 2025-12-31 | 초안 작성 |
| v1.1 | 2025-12-31 | Event 영속성 요구사항 추가: CASCADE 삭제 금지, device_description 필드 추가 |