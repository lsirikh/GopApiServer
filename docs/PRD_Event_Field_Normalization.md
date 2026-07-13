# PRD: Event 필드 정규화 (result/reason 분리)

**버전**: v1.0
**작성일**: 2026-01-09
**상태**: Draft

---

## 1. 개요

### 1.1 목적

Event 스키마를 정규화하여 핵심 분류 필드(`result`, `reason`)는 별도 컬럼/API 필드로 유지하고, 상세 정보는 `detail` JSONB에 저장하도록 구조를 정리한다.

### 1.2 목표 구조

#### DetectionEvent
| 구분 | 필드 | 저장 위치 |
|------|------|----------|
| 핵심 분류 | `result` | 별도 컬럼/필드 (EnumDetectionType) |
| 상세 정보 | `signal`, `thumbnail`, `objects`, `model`, `inference_ms` | `detail` JSONB |

#### MalfunctionEvent
| 구분 | 필드 | 저장 위치 |
|------|------|----------|
| 핵심 분류 | `reason` | 별도 컬럼/필드 (EnumFaultType) |
| 상세 정보 | `first_start`, `first_end`, `second_start`, `second_end` | `detail` JSONB |

### 1.3 변경 범위

**코드 변경 필요**:
1. `app/models/event.py`: MalfunctionEvent에서 `first_start`, `first_end`, `second_start`, `second_end` 컬럼 제거
2. `app/schemas/event.py`: MalfunctionEventCreate/Update/Response 스키마 변경
3. `app/routers/malfunction_events.py`: detail 처리 로직 변경

**문서 변경**:
1. `docs/GOP_스키마_전체.md`: 테이블 스키마 업데이트
2. `GOP_Restful_Api_연동설계.md`: API Request/Response 업데이트

---

## 2. 상세 설계

### 2.1 DetectionEvent 구조 (변경 없음)

현재 코드가 이미 목표 구조와 일치:

**Model (app/models/event.py)**:
```python
class DetectionEvent(Event):
    id = Column(Integer, ForeignKey("events.id"), primary_key=True)
    action_reported = Column(String(10), nullable=False, default="False")
    result = Column(SQLEnum(EnumDetectionType), nullable=False)  # 별도 컬럼
    detail = Column(JSON, nullable=True)  # 보조 정보
```

**detail JSON 구조**:
```json
{
  "signal": 1500,
  "thumbnail": "http://192.168.1.50:8080/events/12345/thumb.jpg",
  "objects": [
    {"label": "person", "confidence": 0.92, "bbox": [100, 200, 150, 300]}
  ],
  "model": "yolov8n",
  "inference_ms": 45
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| signal | int | N | 탐지 신호 크기 |
| thumbnail | string | N | 썸네일 HTTP URL |
| objects | array | N | 탐지 객체 목록 |
| objects[].label | string | Y | 객체 레이블 |
| objects[].confidence | float | Y | 신뢰도 (0.0~1.0) |
| objects[].bbox | array | Y | 바운딩 박스 [x, y, width, height] |
| model | string | N | AI 모델명 |
| inference_ms | int | N | 추론 소요 시간 (ms) |

---

### 2.2 MalfunctionEvent 구조 (코드 변경 필요)

**현재 구조** (변경 전):
```python
class MalfunctionEvent(Event):
    id = Column(Integer, ForeignKey("events.id"), primary_key=True)
    action_reported = Column(String(10), nullable=False, default="False")
    reason = Column(SQLEnum(EnumFaultType), nullable=False)
    first_start = Column(Integer, nullable=False)   # 별도 컬럼
    first_end = Column(Integer, nullable=False)     # 별도 컬럼
    second_start = Column(Integer, nullable=False)  # 별도 컬럼
    second_end = Column(Integer, nullable=False)    # 별도 컬럼
    detail = Column(JSON, nullable=True)
```

**목표 구조** (변경 후):
```python
class MalfunctionEvent(Event):
    id = Column(Integer, ForeignKey("events.id"), primary_key=True)
    action_reported = Column(String(10), nullable=False, default="False")
    reason = Column(SQLEnum(EnumFaultType), nullable=False)  # 별도 컬럼 유지
    detail = Column(JSON, nullable=True)  # 케이블 위치 정보 포함
```

**detail JSON 구조**:
```json
{
  "first_start": 10,
  "first_end": 15,
  "second_start": 20,
  "second_end": 25
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| first_start | int | N | 첫 번째 케이블 끊어진 위치 시작점 |
| first_end | int | N | 첫 번째 케이블 끊어진 위치 끝점 |
| second_start | int | N | 두 번째 케이블 끊어진 위치 시작점 |
| second_end | int | N | 두 번째 케이블 끊어진 위치 끝점 |

---

## 3. 코드 변경 상세

### 3.1 Model 변경 (app/models/event.py)

**변경 전**:
```python
class MalfunctionEvent(Event):
    __tablename__ = "malfunction_events"

    id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), primary_key=True)
    action_reported = Column(String(10), nullable=False, default="False")
    reason = Column(SQLEnum(EnumFaultType), nullable=False)
    first_start = Column(Integer, nullable=False)
    first_end = Column(Integer, nullable=False)
    second_start = Column(Integer, nullable=False)
    second_end = Column(Integer, nullable=False)
    detail = Column(JSON, nullable=True)
```

**변경 후**:
```python
class MalfunctionEvent(Event):
    __tablename__ = "malfunction_events"

    id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), primary_key=True)
    action_reported = Column(String(10), nullable=False, default="False")
    reason = Column(SQLEnum(EnumFaultType), nullable=False)
    # first_start, first_end, second_start, second_end → detail JSONB로 이동
    detail = Column(JSON, nullable=True, doc="오동작 상세 정보 (케이블 위치)")
```

---

### 3.2 Schema 변경 (app/schemas/event.py)

#### 3.2.1 MalfunctionEventCreate

**변경 전**:
```python
class MalfunctionEventCreate(BaseModel):
    type_event: str
    device_id: int
    reason: str
    first_start: int
    first_end: int
    second_start: int
    second_end: int
    detail: Optional[Dict[str, Any]] = None
```

**변경 후**:
```python
class MalfunctionEventCreate(BaseModel):
    type_event: str = Field(..., description="이벤트 유형 (Fault)")
    device_id: int = Field(..., description="장치 ID (Device FK)")
    reason: str = Field(..., description="오동작 원인 (EnumFaultType)")
    detail: Optional[Dict[str, Any]] = Field(None, description="오동작 상세 정보 (케이블 위치)")
```

#### 3.2.2 MalfunctionEventResponse

**변경 전**:
```python
class MalfunctionEventResponse(BaseModel):
    id: int
    type_event: str
    action_reported: str
    reason: str
    first_start: int
    first_end: int
    second_start: int
    second_end: int
    device: Optional[...]
    device_description: Optional[str]
    detail: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
```

**변경 후**:
```python
class MalfunctionEventResponse(BaseModel):
    id: int
    type_event: str
    action_reported: str
    reason: str  # 별도 필드 유지
    device: Optional[...]
    device_description: Optional[str]
    detail: Optional[Dict[str, Any]]  # 케이블 위치 정보 포함
    created_at: datetime
    updated_at: datetime
```

#### 3.2.3 MalfunctionEventUpdate

**변경 전**:
```python
class MalfunctionEventUpdate(BaseModel):
    type_event: Optional[str] = None
    action_reported: Optional[str] = None
    reason: Optional[str] = None
    first_start: Optional[int] = None
    first_end: Optional[int] = None
    second_start: Optional[int] = None
    second_end: Optional[int] = None
    detail: Optional[Dict[str, Any]] = None
```

**변경 후**:
```python
class MalfunctionEventUpdate(BaseModel):
    type_event: Optional[str] = None
    action_reported: Optional[str] = None
    reason: Optional[str] = None
    detail: Optional[Dict[str, Any]] = None  # 케이블 위치 정보 포함
```

---

### 3.3 Router 변경 (app/routers/malfunction_events.py)

- `first_start`, `first_end`, `second_start`, `second_end` 처리 로직 제거
- `detail` JSONB 저장/조회 로직 유지

---

## 4. 문서 변경 상세

### 4.1 GOP_스키마_전체.md 변경

#### 4.1.1 detection_events 테이블 (5.2)

**변경사항 주석 수정**:
> **v1.10 변경사항**: `result`는 별도 컬럼, `detail`에는 보조 정보만 저장 (result 제외)

**CREATE TABLE**:
```sql
CREATE TABLE detection_events (
    id INTEGER PRIMARY KEY REFERENCES events(id) ON DELETE CASCADE,
    action_reported VARCHAR(10) NOT NULL DEFAULT 'False',
    result enum_detection_type NOT NULL,  -- 탐지 결과 (별도 컬럼)
    detail JSONB                          -- 보조 정보 (optional)
);
```

**필드 정의**:

| 필드명 | 타입 | NULL 허용 | 기본값 | 설명 |
|--------|------|-----------|--------|------|
| id | INTEGER | NO | - | FK/PK → events.id (CASCADE DELETE) |
| action_reported | VARCHAR(10) | NO | False | 조치 보고 여부 |
| result | enum_detection_type | NO | - | 탐지 결과 (별도 컬럼) |
| detail | JSONB | YES | NULL | 보조 정보 (signal, thumbnail, objects 등) |

**detail JSON 구조**:
```json
{
  "signal": 1500,
  "thumbnail": "http://192.168.1.50:8080/events/12345/thumb.jpg",
  "objects": [
    {"label": "person", "confidence": 0.92, "bbox": [100, 200, 150, 300]}
  ],
  "model": "yolov8n",
  "inference_ms": 45
}
```

---

#### 4.1.2 malfunction_events 테이블 (5.3)

**변경사항 주석 수정**:
> **v1.10 변경사항**: `reason`은 별도 컬럼, `first_start/end`, `second_start/end`는 `detail` JSONB로 이동

**CREATE TABLE**:
```sql
CREATE TABLE malfunction_events (
    id INTEGER PRIMARY KEY REFERENCES events(id) ON DELETE CASCADE,
    action_reported VARCHAR(10) NOT NULL DEFAULT 'False',
    reason enum_fault_type NOT NULL,  -- 오동작 원인 (별도 컬럼)
    detail JSONB                      -- 케이블 위치 정보
);
```

**필드 정의**:

| 필드명 | 타입 | NULL 허용 | 기본값 | 설명 |
|--------|------|-----------|--------|------|
| id | INTEGER | NO | - | FK/PK → events.id (CASCADE DELETE) |
| action_reported | VARCHAR(10) | NO | False | 조치 보고 여부 |
| reason | enum_fault_type | NO | - | 오동작 원인 (별도 컬럼) |
| detail | JSONB | YES | NULL | 케이블 위치 정보 |

**detail JSON 구조**:
```json
{
  "first_start": 10,
  "first_end": 15,
  "second_start": 20,
  "second_end": 25
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| first_start | int | N | 첫 번째 케이블 끊어진 위치 시작점 |
| first_end | int | N | 첫 번째 케이블 끊어진 위치 끝점 |
| second_start | int | N | 두 번째 케이블 끊어진 위치 시작점 |
| second_end | int | N | 두 번째 케이블 끊어진 위치 끝점 |

---

#### 4.1.3 변경 이력 추가

```markdown
| **v1.10** | 2026-01-09 | **Event 필드 정규화**<br>• **detection_events**: `result` 별도 컬럼 유지, `detail`에는 보조 정보만 (signal, thumbnail, objects, model, inference_ms)<br>• **malfunction_events**: `reason` 별도 컬럼 유지, `first_start/end`, `second_start/end`는 `detail` JSONB로 이동<br>• 문서-코드 동기화 완료 |
```

---

### 4.2 GOP_Restful_Api_연동설계.md 변경

#### 4.2.1 문서 헤더

- **최종 수정일**: 2026-01-09
- **버전**: v2.7

#### 4.2.2 Detection Event API (6.1)

**Request Body** (POST):
```json
{
  "device_id": 101,
  "type_event": "Intrusion",
  "result": "THERMAL_SENSOR",
  "detail": {
    "thumbnail": "http://192.168.1.50:8080/events/1002/thumb.jpg",
    "signal": 1800,
    "objects": [
      {"label": "person", "confidence": 0.92, "bbox": [150, 220, 60, 120]}
    ],
    "model": "yolov8n",
    "inference_ms": 42
  }
}
```

**Response Body**:
```json
{
  "id": 1001,
  "type_event": "Intrusion",
  "action_reported": "True",
  "result": "AI_PERSON",
  "device": { ... },
  "device_description": "[Multi] Sensor-A-1 (number: 1, id: 101)",
  "detail": {
    "thumbnail": "http://192.168.1.50:8080/events/1001/thumb.jpg",
    "signal": 1500,
    "objects": [
      {"label": "person", "confidence": 0.95, "bbox": [100, 200, 50, 100]}
    ],
    "model": "yolov8n",
    "inference_ms": 45
  },
  "created_at": "2026-01-06T10:15:23.100Z",
  "updated_at": "2026-01-06T10:15:23.100Z"
}
```

**필드 정의**:

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| device_id | int | Y | 장치 ID (Device FK) |
| type_event | string | Y | 이벤트 유형 (Intrusion) |
| result | string | **Y** | 탐지 결과 (EnumDetectionType) - **별도 필드** |
| detail | object | N | 보조 정보 (signal, thumbnail, objects 등) |

---

#### 4.2.3 Malfunction Event API (6.2)

**Request Body** (POST):
```json
{
  "device_id": 104,
  "type_event": "Fault",
  "reason": "FAULT_FENCE",
  "detail": {
    "first_start": 3,
    "first_end": 3,
    "second_start": 0,
    "second_end": 0
  }
}
```

**Response Body**:
```json
{
  "id": 2001,
  "type_event": "Fault",
  "action_reported": "True",
  "reason": "FAULT_CABLE_CUTTING",
  "device": { ... },
  "device_description": "[Fence] Sensor-A-3 (number: 3, id: 103)",
  "detail": {
    "first_start": 10,
    "first_end": 15,
    "second_start": 20,
    "second_end": 25
  },
  "created_at": "2026-01-06T14:20:00.500Z",
  "updated_at": "2026-01-06T14:20:00.500Z"
}
```

**필드 정의**:

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| device_id | int | Y | 장치 ID (Device FK) |
| type_event | string | Y | 이벤트 유형 (Fault) |
| reason | string | **Y** | 오동작 원인 (EnumFaultType) - **별도 필드** |
| detail | object | N | 케이블 위치 정보 (first_start/end, second_start/end) |

> **v2.7 변경**: `first_start`, `first_end`, `second_start`, `second_end`가 `detail` JSONB로 이동

---

#### 4.2.4 변경 이력 추가

```markdown
| v2.7 | 2026-01-09 | **Event 필드 정규화**<br>- **Detection Event**: `result` 별도 필드 유지, `detail`에는 보조 정보만 (signal, thumbnail, objects, model, inference_ms)<br>- **Malfunction Event**: `reason` 별도 필드 유지, `first_start/end`, `second_start/end`는 `detail` JSONB로 이동<br>- Request/Response 스키마 간소화 |
```

---

## 5. 구현 체크리스트

### 5.1 코드 변경
- [ ] `app/models/event.py`: MalfunctionEvent에서 first_start/end, second_start/end 컬럼 제거
- [ ] `app/schemas/event.py`: MalfunctionEventCreate에서 first_start/end, second_start/end 필드 제거
- [ ] `app/schemas/event.py`: MalfunctionEventResponse에서 first_start/end, second_start/end 필드 제거
- [ ] `app/schemas/event.py`: MalfunctionEventUpdate에서 first_start/end, second_start/end 필드 제거
- [ ] `app/routers/malfunction_events.py`: detail 처리 로직 수정

### 5.2 문서 변경
- [ ] `docs/GOP_스키마_전체.md`: detection_events 테이블 스키마 수정
- [ ] `docs/GOP_스키마_전체.md`: malfunction_events 테이블 스키마 수정
- [ ] `docs/GOP_스키마_전체.md`: 변경 이력 v1.10 추가
- [ ] `GOP_Restful_Api_연동설계.md`: 문서 버전/날짜 업데이트 (v2.7, 2026-01-09)
- [ ] `GOP_Restful_Api_연동설계.md`: 6.1 Detection Event API 수정
- [ ] `GOP_Restful_Api_연동설계.md`: 6.2 Malfunction Event API 수정
- [ ] `GOP_Restful_Api_연동설계.md`: 변경 이력 v2.7 추가

### 5.3 테스트
- [ ] TDD 테스트 작성 (MalfunctionEvent 구조 변경)
- [ ] 기존 테스트 수정
- [ ] 전체 테스트 통과 확인

---

## 6. 예상 영향도

### 6.1 Breaking Change

⚠️ **MalfunctionEvent API Breaking Change**:
- Request: `first_start`, `first_end`, `second_start`, `second_end` 필드가 `detail` 객체 안으로 이동
- Response: 동일하게 `detail` 객체 안으로 이동

### 6.2 마이그레이션

기존 MalfunctionEvent 데이터의 `first_start`, `first_end`, `second_start`, `second_end` 값을 `detail` JSONB로 마이그레이션 필요:

```sql
-- 마이그레이션 예시
UPDATE malfunction_events
SET detail = jsonb_build_object(
    'first_start', first_start,
    'first_end', first_end,
    'second_start', second_start,
    'second_end', second_end
)
WHERE detail IS NULL;
```

---

**문서 종료**
