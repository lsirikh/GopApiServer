# PRD: Detection Log API

**버전**: v1.0
**작성일**: 2026-02-11
**상태**: Draft

---

## 1. 배경 및 목적

### 1.1 현재 문제

현재 탐지 이벤트(DetectionEvent)와 조치보고(ActionEvent)는 별도 API로 분리되어 있다:

- `GET /api/events/detections` → 탐지 이벤트 목록 (action 정보 없음)
- `GET /api/events/actions` → 조치보고 목록 (source event nested 포함)

**Frontend 로그 화면의 문제**:

1. 탐지 로그와 조치보고는 운영상 **하나의 단위**로 표시해야 함
2. Frontend가 두 API를 각각 호출 → 자체 JOIN → 비효율적이고 비현실적
3. ActionEvent 기준으로 조회하면 **미조치 탐지 이벤트가 누락**됨

### 1.2 해결 방향

DetectionEvent를 기준으로 LEFT JOIN ActionEvent 하는 **읽기 전용 API**를 별도 엔드포인트로 제공한다.

| 방향 | 조치완료 탐지 | 미조치 탐지 | 적합성 |
|------|:---:|:---:|:---:|
| ActionEvent 기준 | O | **X (누락)** | 부적합 |
| **DetectionEvent 기준 (LEFT JOIN)** | **O** | **O (action=null)** | **적합** |

### 1.3 설계 원칙

- 기존 `GET /api/events/detections` Response 스키마를 **변경하지 않음**
- 별도 엔드포인트 `GET /api/detection-logs`로 분리
- DB 스키마 변경 없음 (기존 테이블 그대로 사용)
- 읽기 전용 (GET만 제공, CRUD 없음)

---

## 2. API 설계

### 2.1 엔드포인트

| Method | Path | 설명 | Response |
|--------|------|------|----------|
| GET | `/api/detection-logs` | 탐지 로그 목록 조회 (ActionEvent JOIN 포함) | `ApiResponse[list[DetectionLogResponse]]` |
| GET | `/api/detection-logs/{event_id}` | 탐지 로그 단건 조회 | `ApiSingleResponse[DetectionLogResponse]` |

### 2.2 Query Parameters (목록 조회)

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|----------|------|:----:|--------|------|
| `page` | int | X | 1 | 페이지 번호 (≥ 1) |
| `limit` | int | X | 20 | 페이지당 항목 수 (1~100) |
| `device_id` | int | X | - | 장치 ID 필터 |
| `action_reported` | string | X | - | 조치보고 여부 필터 ("True" / "False") |
| `result` | string | X | - | 탐지 결과 유형 필터 (EnumDetectionType) |
| `start_date` | datetime | X | - | 시작 날짜 필터 (이벤트 생성일 >=) |
| `end_date` | datetime | X | - | 종료 날짜 필터 (이벤트 생성일 <=) |

### 2.3 Response Schema

#### DetectionLogResponse

DetectionEventResponse의 모든 필드 + `action` 필드 추가.

```
DetectionLogResponse
├── id: int                          # 탐지 이벤트 ID
├── type_event: EnumEventType        # 이벤트 유형
├── action_reported: EnumTrueFalse   # 조치보고 여부
├── result: EnumDetectionType        # 탐지 결과
├── device: Optional[DeviceNested]   # Polymorphic Device (삭제 시 null)
├── device_description: Optional[str] # Device 정보 스냅샷
├── detail: Optional[dict]           # 탐지 상세 (JSONB)
├── action: Optional[ActionNested]   # ★ LEFT JOIN된 ActionEvent (없으면 null)
├── created_at: datetime             # 탐지 이벤트 생성 일시
└── updated_at: datetime             # 탐지 이벤트 수정 일시
```

#### ActionNested (신규 스키마)

ActionEvent의 핵심 필드만 포함하는 경량 Nested 스키마.
`from_event` 필드는 **포함하지 않음** (부모인 DetectionLogResponse에 이미 탐지 정보가 있으므로 순환 참조 방지).

```
ActionNested
├── id: int              # ActionEvent ID
├── content: str         # 조치 내용
├── user: str            # 조치자
├── created_at: datetime # 조치 일시
└── updated_at: datetime # 수정 일시
```

### 2.4 Response 예시

#### 목록 조회 (조치완료 + 미조치 혼합)

```json
{
  "success": true,
  "message": "2 detection logs retrieved",
  "data": [
    {
      "id": 1001,
      "type_event": "Intrusion",
      "action_reported": "True",
      "result": "PIR_SENSOR",
      "device": {
        "id": 101,
        "number_device": 1,
        "group_device": "A",
        "name_device": "Sensor-A-1",
        "type_device": "Multi",
        "version": null,
        "status": "NORMAL",
        "is_enable": true,
        "controller_id": 1,
        "device_groups": []
      },
      "device_description": "[Multi] Sensor-A-1 (number: 1, id: 101)",
      "result": "AI_DETECT",
      "detail": {
        "thumbnail": "http://192.168.1.50:8080/events/1001/thumb.jpg",
        "signal": 1500,
        "objects": [{"label": "person", "confidence": 0.95, "bbox": [100, 200, 50, 100]}],
        "model": "yolov8n",
        "inference_ms": 45
      },
      "action": {
        "id": 4001,
        "content": "침입 탐지 확인 및 순찰 출동 요청",
        "user": "operator_kim",
        "created_at": "2026-01-06T10:16:00.100Z",
        "updated_at": "2026-01-06T10:16:00.100Z"
      },
      "created_at": "2026-01-06T10:15:23.100Z",
      "updated_at": "2026-01-06T10:15:23.100Z"
    },
    {
      "id": 1002,
      "type_event": "Intrusion",
      "action_reported": "False",
      "result": "THERMAL_SENSOR",
      "device": {
        "id": 102,
        "number_device": 2,
        "group_device": "B",
        "name_device": "Sensor-B-1",
        "type_device": "Fence",
        "version": null,
        "status": "NORMAL",
        "is_enable": true,
        "controller_id": 1,
        "device_groups": []
      },
      "device_description": "[Fence] Sensor-B-1 (number: 2, id: 102)",
      "detail": null,
      "action": null,
      "created_at": "2026-01-06T10:20:00.100Z",
      "updated_at": "2026-01-06T10:20:00.100Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 2,
    "total_pages": 1
  },
  "meta": {
    "timestamp": "2026-01-06T10:40:00.250Z",
    "request_id": "abc-123"
  }
}
```

### 2.5 Error Response

| HTTP Status | 상황 | 엔드포인트 |
|:-----------:|------|:----------:|
| 404 | 탐지 로그를 찾을 수 없음 | 단건 조회 |

---

## 3. 구현 상세

### 3.1 DB 쿼리 전략

```python
# LEFT JOIN: DetectionEvent + ActionEvent
query = db.query(DetectionEvent).options(
    joinedload(DetectionEvent.device),   # 기존: Device eager loading
    joinedload(DetectionEvent.actions)   # 신규: ActionEvent eager loading
)
```

- `DetectionEvent.actions` 관계는 **이미 Event 모델에 정의**되어 있음 (Event.actions → ActionEvent)
- LEFT JOIN이므로 ActionEvent가 없으면 빈 리스트 반환 → `action: null` 처리
- 1:1 관계이므로 `actions[0]` 또는 `None` 처리

### 3.2 파일 변경 목록

| 파일 | 변경 유형 | 설명 |
|------|-----------|------|
| `app/schemas/event.py` | **수정** | `ActionNested`, `DetectionLogResponse` 스키마 추가 |
| `app/routers/detection_logs.py` | **신규** | Detection Log 라우터 (GET 목록, GET 단건) |
| `app/main.py` | **수정** | 라우터 등록 (`/api/detection-logs`) |
| `GOP_Restful_Api_연동설계.md` | **수정** | Section 6.5 추가, 목차/부록/변경이력 업데이트 |
| `docs/GOP_스키마_전체.md` | **수정** | 변경이력 업데이트 (DB 변경 없음, API 스키마 추가 기록) |

### 3.3 Pydantic 스키마 추가 (app/schemas/event.py)

```python
class ActionNested(BaseModel):
    """ActionEvent 경량 Nested 스키마 (DetectionLog 전용)"""
    id: int = Field(..., description="ActionEvent ID")
    content: str = Field(..., description="조치 내용")
    user: str = Field(..., description="조치자")
    created_at: datetime = Field(..., description="조치 일시")
    updated_at: datetime = Field(..., description="수정 일시")

    model_config = ConfigDict(from_attributes=True)


class DetectionLogResponse(BaseModel):
    """Detection Log 응답 스키마 (DetectionEvent + ActionEvent JOIN)"""
    id: int = Field(..., description="탐지 이벤트 ID")
    type_event: EnumEventType = Field(..., description="이벤트 유형")
    action_reported: EnumTrueFalse = Field(..., description="조치보고 여부")
    result: EnumDetectionType = Field(..., description="탐지 결과")
    device: Optional[Union["SensorNestedResponse", "ControllerNestedResponse", "CameraNestedResponse"]] = Field(None, description="장치 정보")
    device_description: Optional[str] = Field(None, description="장치 정보 스냅샷")
    detail: Optional[Dict[str, Any]] = Field(None, description="탐지 상세 정보")
    action: Optional[ActionNested] = Field(None, description="조치보고 정보 (없으면 null)")
    created_at: datetime = Field(..., description="생성 일시")
    updated_at: datetime = Field(..., description="수정 일시")

    model_config = ConfigDict(from_attributes=True)
```

### 3.4 라우터 구현 (app/routers/detection_logs.py)

- `GET /` → 목록 조회 (페이지네이션, 필터링)
- `GET /{event_id}` → 단건 조회 (404 처리)
- `_build_device_nested_response()` 헬퍼: detections.py의 기존 로직 재사용
- 응답 변환 시 `event.actions` 리스트에서 첫 번째 항목을 `ActionNested`로 변환

### 3.5 main.py 라우터 등록

```python
from app.routers import detection_logs
app.include_router(detection_logs.router, prefix="/api/detection-logs", tags=["Detection Logs"])
```

Swagger 태그 위치: Event API 섹션 근처 (detections, malfunctions, connections, actions 다음).

---

## 4. 문서 업데이트

### 4.1 GOP_Restful_Api_연동설계.md

**버전**: v3.7 → v3.8
**최종 수정일**: 2026-02-09 → 2026-02-11

#### 4.1.1 목차 업데이트

```
6. Event API 설계
   - 6.1 Detection Event API
   - 6.2 Malfunction Event API
   - 6.3 Connection Event API
   - 6.4 Action Event API
   - 6.5 Detection Log API *(v3.8 신규)*    ← 추가
```

#### 4.1.2 Section 6.5 Detection Log API 추가

**작성 내용**:

1. **6.5.1 Detection Log 목록 조회**
   - `GET /api/detection-logs`
   - Query Parameters 표 (page, limit, device_id, action_reported, result, start_date, end_date)
   - Response 스키마 (DetectionLogResponse): DetectionEventResponse 필드 + action(ActionNested) 필드
   - Response 예시 (조치완료 1건 + 미조치 1건)
   - Pagination 포함

2. **6.5.2 Detection Log 단건 조회**
   - `GET /api/detection-logs/{event_id}`
   - Response 스키마 (ApiSingleResponse[DetectionLogResponse])
   - Error: 404 Not Found

#### 4.1.3 부록 12.1 Endpoint 목록 업데이트

Detection Logs 섹션 추가:

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/detection-logs` | 탐지 로그 목록 조회 |
| GET | `/api/detection-logs/{event_id}` | 탐지 로그 단건 조회 |

#### 4.1.4 변경 이력 추가

```
| v3.8 | 2026-02-11 | **Detection Log API 추가**
  [1. Detection Log API 신규 (6.5)]
  - GET /api/detection-logs: 탐지 로그 목록 조회 (DetectionEvent + ActionEvent LEFT JOIN)
  - GET /api/detection-logs/{event_id}: 탐지 로그 단건 조회
  - DetectionLogResponse 스키마: DetectionEventResponse + action(ActionNested) 필드
  - ActionNested 스키마: id, content, user, created_at, updated_at
  - 읽기 전용 API (CRUD 미제공)
  - 기존 Detection/Action API 변경 없음 |
```

### 4.2 GOP_스키마_전체.md

**버전**: v2.9 → v2.10
**최종 업데이트**: 2026-02-09 → 2026-02-11
**기준 API 버전**: v3.7 → v3.8

#### 4.2.1 변경이력 추가

DB 테이블/컬럼 변경 없음. API 스키마 추가만 기록:

```
| v2.10 | 2026-02-11 | **Detection Log API 스키마 추가 (DB 변경 없음)**
  - DetectionLogResponse: DetectionEventResponse + action 필드 (API 전용 스키마)
  - ActionNested: ActionEvent 경량 Nested 스키마 (id, content, user, timestamps)
  - 기존 detection_events, action_events 테이블 변경 없음
  - 기존 events 테이블의 actions relationship 활용 (LEFT JOIN) |
```

---

## 5. 구현 순서 (TDD)

### Phase 1: 스키마 테스트 및 구현
- [ ] 1.1 TEST: ActionNested 스키마 필드 검증
- [ ] 1.2 TEST: DetectionLogResponse 스키마 필드 검증 (action 필드 포함)
- [ ] 1.3 TEST: DetectionLogResponse.action이 Optional임을 검증
- [ ] 1.4 IMPL: ActionNested, DetectionLogResponse 스키마 구현 (app/schemas/event.py)

### Phase 2: 목록 조회 API 테스트 및 구현
- [ ] 2.1 TEST: GET /api/detection-logs 기본 조회 (200, pagination 포함)
- [ ] 2.2 TEST: GET /api/detection-logs action_reported 필터 검증
- [ ] 2.3 TEST: GET /api/detection-logs 응답에 action 필드 포함 검증 (조치완료 시 ActionNested, 미조치 시 null)
- [ ] 2.4 IMPL: detection_logs.py 라우터 목록 조회 구현
- [ ] 2.5 IMPL: main.py 라우터 등록

### Phase 3: 단건 조회 API 테스트 및 구현
- [ ] 3.1 TEST: GET /api/detection-logs/{event_id} 정상 조회 (200)
- [ ] 3.2 TEST: GET /api/detection-logs/{event_id} 404 검증
- [ ] 3.3 IMPL: detection_logs.py 단건 조회 구현

### Phase 4: 문서 업데이트
- [ ] 4.1 GOP_Restful_Api_연동설계.md 업데이트 (Section 6.5, 목차, 부록, 변경이력)
- [ ] 4.2 GOP_스키마_전체.md 업데이트 (버전, 변경이력)

### Phase 5: 최종 검증 및 커밋
- [ ] 5.1 VERIFY: 전체 테스트 통과
- [ ] 5.2 VERIFY: App import OK, Swagger 확인
- [ ] 5.3 COMMIT (behavioral): Detection Log API 구현 (스키마 + 라우터 + main.py)
- [ ] 5.4 COMMIT (docs): API 문서 v3.8 + 스키마 문서 v2.10 업데이트
