# PRD: Event Detail JSONB 필드 추가

**문서 버전**: v1.0
**작성일**: 2026-01-08
**작성자**: Claude AI Assistant
**상태**: 승인 대기

---

## 1. 개요

### 1.1 배경

현재 Detection Event와 Malfunction Event는 고정된 필드만 지원하여 다양한 탐지 정보를 저장하기 어렵습니다.
- **Detection Event**: 센서 탐지와 카메라 AI 탐지를 구분 없이 동일한 `result` 필드로 처리
- **Malfunction Event**: 2선 케이블 제어기 시스템의 장애 위치 데이터(first_start/end, second_start/end: 케이블 끊어진 위치)가 개별 컬럼으로 분리되어 확장성 부족

### 1.2 목적

Detection Event와 Malfunction Event에 `detail` JSONB 필드를 추가하여:
- **유연한 데이터 저장**: 디바이스 타입별 다양한 탐지 정보 저장
- **AI 탐지 지원**: 카메라 AI 탐지 시 썸네일, 객체 정보, 모델명 등 저장
- **케이블 장애 위치 통합**: Malfunction의 2선 케이블 끊어진 위치 데이터를 JSONB로 통합
- **확장성 확보**: 향후 새로운 탐지 정보 추가 용이

### 1.3 범위

| 항목 | 포함 여부 |
|------|----------|
| detection_events 테이블 수정 | O |
| malfunction_events 테이블 수정 | O |
| Event 모델 수정 | O |
| Event 스키마 수정 | O |
| Event API 라우터 수정 | O |
| Swagger/OpenAPI 문서 자동 반영 | O |
| GOP_스키마_전체.md 업데이트 | O |
| GOP_Restful_Api_연동설계.md 업데이트 | O |

---

## 2. 요구사항

### 2.1 기능 요구사항

#### FR-1: Detection Event `detail` JSONB 필드 추가

**목적**: 센서/카메라 AI 탐지 정보를 유연하게 저장

**디바이스 타입 구분**: 기존 `device.category_device`로 센서/카메라 구분 (별도 discriminator 불필요)

**Detection Event detail 구조 (AI 탐지)**:
```json
{
  "result": "AI_PERSON",
  "signal": 0,
  "thumbnail": "http://192.168.1.50:8080/events/12345/thumb.jpg",
  "objects": [
    {"label": "person", "confidence": 0.92, "bbox": [100, 200, 150, 300]},
    {"label": "vehicle", "confidence": 0.85, "bbox": [400, 300, 200, 150]}
  ],
  "model": "yolov8n",
  "inference_ms": 45
}
```

**Detection Event detail 구조 (센서 탐지)**:
```json
{
  "result": "Fence",
  "signal": 2300,
  "thumbnail": "http://192.168.1.50:8080/events/12346/thumb.jpg",
  "objects": null,
  "model": null,
  "inference_ms": null
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| result | string | N | 탐지 결과 |
| signal | int | N | 탐지 신호 크기 |
| thumbnail | string | Y | 썸네일 HTTP URL (카메라 연동 시 필수) |
| objects | array | N | AI 탐지 객체 목록 |
| objects[].label | string | Y | 객체 레이블 (person, vehicle 등) |
| objects[].confidence | float | Y | 신뢰도 (0.0~1.0) |
| objects[].bbox | array | Y | 바운딩 박스 [x, y, width, height] |
| model | string | N | AI 모델명 |
| inference_ms | int | N | 추론 소요 시간 (ms) |

#### FR-2: Malfunction Event `detail` JSONB 필드 추가

**목적**: 2선 케이블 제어기 시스템의 장애 위치 데이터를 JSONB로 통합 (케이블 끊어진 위치 정보)

**Malfunction Event detail 구조**:
```json
{
  "reason": "CABLE_CUT",
  "first_start": 5,
  "first_end": 5,
  "second_start": 0,
  "second_end": 0
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| reason | string | N | 고장 사유 |
| first_start | int | N | 첫 번째 케이블 끊어진 위치 시작점 |
| first_end | int | N | 첫 번째 케이블 끊어진 위치 끝점 |
| second_start | int | N | 두 번째 케이블 끊어진 위치 시작점 |
| second_end | int | N | 두 번째 케이블 끊어진 위치 끝점 |

### 2.2 비기능 요구사항

- **NFR-1**: 기존 API 하위 호환성 유지 (기존 필드 유지, detail은 선택적)
- **NFR-2**: JSONB 인덱싱을 통한 쿼리 성능 최적화
- **NFR-3**: Swagger 문서 자동 생성 지원

---

## 3. 데이터베이스 스키마 변경

### 3.1 detection_events 테이블 변경

```sql
-- 기존 테이블에 detail JSONB 컬럼 추가
ALTER TABLE detection_events
ADD COLUMN detail JSONB DEFAULT NULL;

-- JSONB 검색 성능 최적화 인덱스 (선택적)
CREATE INDEX idx_detection_events_detail ON detection_events USING GIN (detail);
```

**변경 후 테이블 구조**:
```sql
CREATE TABLE detection_events (
    id INTEGER PRIMARY KEY REFERENCES events(id) ON DELETE CASCADE,
    action_reported VARCHAR(10) NOT NULL DEFAULT 'False',
    result VARCHAR(50) NOT NULL,      -- 기존 필드 유지 (하위 호환)
    detail JSONB                       -- v1.8 신규: 확장 탐지 정보
);
```

### 3.2 malfunction_events 테이블 변경

```sql
-- 기존 테이블에 detail JSONB 컬럼 추가
ALTER TABLE malfunction_events
ADD COLUMN detail JSONB DEFAULT NULL;

-- JSONB 검색 성능 최적화 인덱스 (선택적)
CREATE INDEX idx_malfunction_events_detail ON malfunction_events USING GIN (detail);
```

**변경 후 테이블 구조**:
```sql
CREATE TABLE malfunction_events (
    id INTEGER PRIMARY KEY REFERENCES events(id) ON DELETE CASCADE,
    action_reported VARCHAR(10) NOT NULL DEFAULT 'False',
    reason VARCHAR(50) NOT NULL,       -- 기존 필드 유지 (하위 호환)
    first_start INTEGER NOT NULL,      -- 기존 필드 유지 (하위 호환)
    first_end INTEGER NOT NULL,
    second_start INTEGER NOT NULL,
    second_end INTEGER NOT NULL,
    detail JSONB                        -- v1.8 신규: 확장 장애 정보
);
```

---

## 4. API 스키마 변경

### 4.1 Detection Event 스키마

#### DetectionEventCreate 변경
```python
class DetectionEventCreate(BaseModel):
    type_event: str
    device_id: int
    result: str
    detail: Optional[DetectionDetail] = None  # v2.5 신규
```

#### DetectionDetail 스키마 (신규)
```python
class DetectionDetailObject(BaseModel):
    """AI 탐지 객체 정보"""
    label: str = Field(..., description="객체 레이블 (person, vehicle 등)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="신뢰도")
    bbox: List[int] = Field(..., min_length=4, max_length=4, description="바운딩 박스 [x, y, w, h]")

class DetectionDetail(BaseModel):
    """Detection Event 확장 정보"""
    result: Optional[str] = Field(None, description="탐지 결과")
    signal: Optional[int] = Field(None, description="탐지 신호 크기")
    thumbnail: str = Field(..., description="썸네일 HTTP URL (카메라 연동 시 필수)")
    objects: Optional[List[DetectionDetailObject]] = Field(None, description="탐지 객체 목록")
    model: Optional[str] = Field(None, description="AI 모델명")
    inference_ms: Optional[int] = Field(None, description="추론 시간 (ms)")
```

#### DetectionEventResponse 변경
```python
class DetectionEventResponse(BaseModel):
    id: int
    type_event: str
    action_reported: str
    result: str
    detail: Optional[DetectionDetail] = None  # v2.5 신규
    device: Optional[Union[SensorNestedResponse, ControllerNestedResponse, CameraNestedResponse]]
    device_description: Optional[str]
    created_at: datetime
    updated_at: datetime
```

### 4.2 Malfunction Event 스키마

#### MalfunctionEventCreate 변경
```python
class MalfunctionEventCreate(BaseModel):
    type_event: str
    device_id: int
    reason: str
    first_start: int
    first_end: int
    second_start: int
    second_end: int
    detail: Optional[MalfunctionDetail] = None  # v2.5 신규
```

#### MalfunctionDetail 스키마 (신규)
```python
class MalfunctionDetail(BaseModel):
    """Malfunction Event 확장 정보 (2선 케이블 제어기 시스템용)"""
    reason: Optional[str] = Field(None, description="고장 사유")
    first_start: Optional[int] = Field(None, description="첫 번째 케이블 끊어진 위치 시작점")
    first_end: Optional[int] = Field(None, description="첫 번째 케이블 끊어진 위치 끝점")
    second_start: Optional[int] = Field(None, description="두 번째 케이블 끊어진 위치 시작점")
    second_end: Optional[int] = Field(None, description="두 번째 케이블 끊어진 위치 끝점")
```

#### MalfunctionEventResponse 변경
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
    detail: Optional[MalfunctionDetail] = None  # v2.5 신규
    device: Optional[Union[SensorNestedResponse, ControllerNestedResponse, CameraNestedResponse]]
    device_description: Optional[str]
    created_at: datetime
    updated_at: datetime
```

---

## 5. API 엔드포인트

### 5.1 Detection Event API

기존 엔드포인트 유지, Request/Response에 `detail` 필드 추가:

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| GET | /api/events/detections | 목록 조회 |
| GET | /api/events/detections/{id} | 단일 조회 |
| POST | /api/events/detections | 생성 (detail 포함 가능) |
| PATCH | /api/events/detections/{id} | 수정 (detail 포함 가능) |
| DELETE | /api/events/detections/{id} | 삭제 |

**POST 예시 (센서 탐지)**:
```json
{
  "type_event": "Intrusion",
  "device_id": 3,
  "result": "PIR_SENSOR",
  "detail": {
    "result": "Fence",
    "signal": 2300,
    "thumbnail": "http://192.168.1.50:8080/events/12346/thumb.jpg"
  }
}
```

**POST 예시 (AI 탐지)**:
```json
{
  "type_event": "Intrusion",
  "device_id": 5,
  "result": "AI_PERSON",
  "detail": {
    "result": "AI_PERSON",
    "signal": 0,
    "thumbnail": "http://192.168.1.50:8080/events/12345/thumb.jpg",
    "objects": [
      {"label": "person", "confidence": 0.92, "bbox": [100, 200, 150, 300]}
    ],
    "model": "yolov8n",
    "inference_ms": 45
  }
}
```

### 5.2 Malfunction Event API

기존 엔드포인트 유지, Request/Response에 `detail` 필드 추가:

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| GET | /api/events/malfunctions | 목록 조회 |
| GET | /api/events/malfunctions/{id} | 단일 조회 |
| POST | /api/events/malfunctions | 생성 (detail 포함 가능) |
| PATCH | /api/events/malfunctions/{id} | 수정 (detail 포함 가능) |
| DELETE | /api/events/malfunctions/{id} | 삭제 |

**POST 예시 (신호 데이터 포함)**:
```json
{
  "type_event": "Fault",
  "device_id": 3,
  "reason": "FAULT_CABLE_CUTTING",
  "first_start": 5,
  "first_end": 5,
  "second_start": 0,
  "second_end": 0,
  "detail": {
    "reason": "CABLE_CUT",
    "first_start": 5,
    "first_end": 5,
    "second_start": 0,
    "second_end": 0
  }
}
```

---

## 6. 구현 계획

### Phase 1: 모델 및 스키마 변경

| 단계 | 작업 | 파일 |
|------|------|------|
| 1.1 | DetectionDetail, MalfunctionDetail 스키마 추가 | app/schemas/event.py |
| 1.2 | DetectionEventCreate/Response에 detail 추가 | app/schemas/event.py |
| 1.3 | MalfunctionEventCreate/Response에 detail 추가 | app/schemas/event.py |
| 1.4 | DetectionEvent 모델에 detail 컬럼 추가 | app/models/event.py |
| 1.5 | MalfunctionEvent 모델에 detail 컬럼 추가 | app/models/event.py |

### Phase 2: API 라우터 수정

| 단계 | 작업 | 파일 |
|------|------|------|
| 2.1 | Detection POST 핸들러에 detail 처리 추가 | app/routers/detections.py |
| 2.2 | Detection PATCH 핸들러에 detail 처리 추가 | app/routers/detections.py |
| 2.3 | Detection Response 빌더에 detail 포함 | app/routers/detections.py |
| 2.4 | Malfunction POST 핸들러에 detail 처리 추가 | app/routers/malfunctions.py |
| 2.5 | Malfunction PATCH 핸들러에 detail 처리 추가 | app/routers/malfunctions.py |
| 2.6 | Malfunction Response 빌더에 detail 포함 | app/routers/malfunctions.py |

### Phase 3: 테스트 작성

| 단계 | 작업 | 파일 |
|------|------|------|
| 3.1 | Detection detail 모델 테스트 | tests/test_event_detail.py |
| 3.2 | Detection detail 스키마 테스트 | tests/test_event_detail.py |
| 3.3 | Detection detail API 테스트 | tests/test_event_detail.py |
| 3.4 | Malfunction detail 모델 테스트 | tests/test_event_detail.py |
| 3.5 | Malfunction detail 스키마 테스트 | tests/test_event_detail.py |
| 3.6 | Malfunction detail API 테스트 | tests/test_event_detail.py |

### Phase 4: 문서 업데이트

| 단계 | 작업 | 파일 |
|------|------|------|
| 4.1 | GOP_스키마_전체.md 업데이트 | docs/GOP_스키마_전체.md |
| 4.2 | GOP_Restful_Api_연동설계.md 업데이트 | GOP_Restful_Api_연동설계.md |

---

## 7. 문서 업데이트 가이드

### 7.1 GOP_스키마_전체.md 업데이트

**업데이트 항목**:
1. 문서 버전: v1.7 → v1.8
2. 최종 업데이트 날짜: 2026-01-08
3. detection_events 테이블 섹션에 `detail` JSONB 컬럼 추가
4. malfunction_events 테이블 섹션에 `detail` JSONB 컬럼 추가
5. detail JSON 구조 문서화
6. 변경 이력에 v1.8 추가

### 7.2 GOP_Restful_Api_연동설계.md 업데이트

**업데이트 항목**:
1. 문서 버전: v2.4 → v2.5
2. 최종 수정일: 2026-01-08
3. 6.1 Detection Event API 섹션에 detail 필드 추가
4. 6.2 Malfunction Event API 섹션에 detail 필드 추가
5. 변경 이력에 v2.5 추가

---

## 8. 하위 호환성

### 8.1 기존 필드 유지

- Detection Event의 `result` 컬럼 유지
- Malfunction Event의 `reason`, `first_start`, `first_end`, `second_start`, `second_end` 컬럼 유지
- `detail` 필드는 **선택적** (Optional)

### 8.2 마이그레이션

기존 데이터는 변경 없음. 새로운 이벤트 생성 시에만 detail 사용 가능.

---

## 9. 체크리스트

### 9.1 개발 체크리스트

- [ ] DetectionDetail 스키마 추가
- [ ] MalfunctionDetail 스키마 추가
- [ ] DetectionEvent 모델에 detail 컬럼 추가
- [ ] MalfunctionEvent 모델에 detail 컬럼 추가
- [ ] detections.py 라우터 수정
- [ ] malfunctions.py 라우터 수정
- [ ] 테스트 작성 및 통과

### 9.2 문서 체크리스트

- [ ] GOP_스키마_전체.md 업데이트
- [ ] GOP_Restful_Api_연동설계.md 업데이트
- [ ] Swagger 문서 확인

---

## 10. 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| v1.0 | 2026-01-08 | 초기 문서 작성 |

---

**문서 종료**
