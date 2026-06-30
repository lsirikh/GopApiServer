# PRD: Category Event 필드 리팩토링

**버전**: v1.1
**작성일**: 2026-01-08
**상태**: Draft

---

## 1. 개요

### 1.1 배경

현재 시스템에서 `category_event`라는 필드명이 여러 모델에서 서로 다른 의미로 사용되어 혼란을 야기함:

| 모델 | 필드명 | 현재 타입 | 값 예시 |
|------|--------|----------|---------|
| **Event** (Base) | `category_event` | String | `"detection"`, `"malfunction"`, `"connection"` |
| **EventMapping** | `category_event` | String | `"detection"`, `"malfunction"`, `"connection"` |

추가로 `EnumEventCategory`라는 Enum이 존재하지만, 이는 센서 조합 타입(`FENCE_SENSOR_ONLY`, `AI_CAMERA_ONLY` 등)을 정의하며 위 모델들과 연동되지 않음.

### 1.2 문제점

1. **Enum 미사용**: Event/EventMapping 모델의 `category_event`가 단순 문자열로, Enum으로 정의되지 않아 타입 안전성 부족
2. **Enum 이름 혼란**: 기존 `EnumEventCategory`는 센서 조합 타입인데, 이름이 Event 카테고리와 혼동됨
3. **문서 불일치**: GOP 연동설계 문서에서 `EnumEventCategory` 설명이 모호함

### 1.3 목표

1. Event 모델의 `category_event`를 Enum으로 정의하여 타입 안전성 확보
2. EventMapping 모델에 센서 조합 타입 필드 추가 (명확한 이름으로)
3. Enum 이름을 용도에 맞게 정리
4. 문서와 코드의 일관성 확보
5. Swagger 문서 자동 업데이트

---

## 2. 변경 사항

### 2.1 Enum 정의 (app/utils/enums.py)

#### 2.1.1 EnumEventCategory (신규)
Event 모델의 polymorphic discriminator용 Enum

```python
class EnumEventCategory(str, Enum):
    """Event category enumeration for Event polymorphic discriminator"""
    DETECTION = "detection"       # 침입 탐지 이벤트
    MALFUNCTION = "malfunction"   # 장애 이벤트
    CONNECTION = "connection"     # 연결 이벤트
```

#### 2.1.2 EnumMappingEventCategory (기존 EnumEventCategory 이름 변경)
EventMapping의 센서 조합 타입용 Enum

```python
class EnumMappingEventCategory(str, Enum):
    """Mapping event category enumeration for EventMapping sensor combination type"""
    NONE = "NONE"                                       # 미정의
    FENCE_SENSOR_ONLY = "FENCE_SENSOR_ONLY"             # 펜스센서 단독
    FENCE_SENSOR_WITH_MULTI_SENSOR = "FENCE_SENSOR_WITH_MULTI_SENSOR"  # 펜스센서와 멀티센서 And 조건
    MULTI_SENSOR_ONLY = "MULTI_SENSOR_ONLY"             # 멀티센서 단독
    SENSOR_WITH_CAMERA = "SENSOR_WITH_CAMERA"           # 센서와 카메라 적용
    SENSOR_WITH_AI_CAMERA = "SENSOR_WITH_AI_CAMERA"     # 센서와 AI 카메라 판단 적용
    AI_CAMERA_ONLY = "AI_CAMERA_ONLY"                   # AI 카메라 판단 단독
    CAMERA_ONLY = "CAMERA_ONLY"                         # 카메라 단독
```

### 2.2 모델 변경

#### 2.2.1 Event 모델 (app/models/event.py)

**변경 전:**
```python
category_event = Column(String(50), nullable=False, index=True)
```

**변경 후:**
```python
category_event = Column(
    SQLEnum(EnumEventCategory),
    nullable=False,
    index=True,
    doc="이벤트 카테고리 (detection/malfunction/connection)"
)
```

#### 2.2.2 EventMapping 모델 (app/models/integration.py)

**변경 전:**
```python
category_event = Column(String(50), nullable=False, index=True)
```

**변경 후:**
```python
# 기존 필드 이름 변경
category_event_mapping = Column(
    SQLEnum(EnumMappingEventCategory),
    nullable=False,
    index=True,
    doc="이벤트 매핑 카테고리 (센서 조합 타입)"
)
```

### 2.3 스키마 변경 (app/schemas/)

#### 2.3.1 Event 스키마 (app/schemas/event.py)
- `category_event`: `EnumEventCategory` Enum 타입으로 변경
- Swagger에 Enum 값 목록 자동 표시

#### 2.3.2 EventMapping 스키마 (app/schemas/integration.py)
- `category_event` → `category_event_mapping` 필드명 변경
- `EnumMappingEventCategory` Enum 타입 적용

### 2.4 라우터 변경

#### 2.4.1 EventMapping 라우터 (app/routers/event_mappings.py)
- Query Parameter: `category_event` → `category_event_mapping`
- 필터 로직 업데이트

---

## 3. 필드명/Enum 요약

### 3.1 최종 구조

| 모델 | 필드명 | Enum | 값 |
|------|--------|------|-----|
| **Event** | `category_event` | `EnumEventCategory` | `detection`, `malfunction`, `connection` |
| **EventMapping** | `category_event_mapping` | `EnumMappingEventCategory` | `FENCE_SENSOR_ONLY`, `AI_CAMERA_ONLY` 등 |

### 3.2 Enum 이름 변경

| 변경 전 | 변경 후 | 용도 |
|---------|---------|------|
| - (신규) | `EnumEventCategory` | Event polymorphic discriminator |
| `EnumEventCategory` (기존) | `EnumMappingEventCategory` | EventMapping 센서 조합 타입 |
| `EnumCategoryEvent` (별칭) | `EnumMappingEventCategory` (별칭 유지) | 하위 호환성 |

---

## 4. 문서 업데이트

### 4.1 GOP_Restful_Api_연동설계.md

1. **섹션 4.3 Integration Enum**:
   - 제목 변경: "EnumEventCategory" → "EnumMappingEventCategory"
   - 설명 업데이트: EventMapping 센서 조합 타입용임을 명시

2. **섹션 4.x Event Enum** (신규 추가):
   - `EnumEventCategory` 정의 (Event용)
   - 값: `detection`, `malfunction`, `connection`

3. **섹션 7.2 EventMapping API**:
   - `category_event` → `category_event_mapping` 필드명 변경
   - Request/Response 예시 업데이트
   - Query Parameter 업데이트

4. **섹션 6.x Event API**:
   - `category_event` 필드에 `EnumEventCategory` Enum 설명 추가

### 4.2 GOP_스키마_전체.md

1. **Enum 섹션**:
   - `EnumEventCategory` 정의 추가 (Event용)
   - `EnumMappingEventCategory` 정의 추가 (EventMapping용)

2. **테이블 스키마**:
   - `events` 테이블: `category_event` 컬럼 타입을 `EnumEventCategory`로 설명
   - `event_mappings` 테이블: `category_event` → `category_event_mapping` 변경, 타입 `EnumMappingEventCategory`

---

## 5. 마이그레이션 계획

### 5.1 DB 마이그레이션

```sql
-- EventMapping 테이블: 컬럼명 변경
ALTER TABLE event_mappings RENAME COLUMN category_event TO category_event_mapping;

-- Event 테이블: 컬럼명 유지, 타입만 Enum으로 변경 (SQLite는 ALTER 제한)
-- SQLite의 경우 테이블 재생성 필요할 수 있음
```

### 5.2 데이터 마이그레이션

- Event.category_event: 기존 문자열 값 (`detection`, `malfunction`, `connection`) 유지 (Enum 값과 동일)
- EventMapping.category_event_mapping: 기존 값이 있다면 `EnumMappingEventCategory` 값으로 변환 필요

---

## 6. 테스트 계획

### 6.1 단위 테스트
- [ ] EnumEventCategory 값 검증 (`detection`, `malfunction`, `connection`)
- [ ] EnumMappingEventCategory 값 검증 (`FENCE_SENSOR_ONLY` 등)
- [ ] Event 모델 category_event Enum 적용 테스트
- [ ] EventMapping 모델 category_event_mapping 필드 테스트

### 6.2 API 테스트
- [ ] Event API: category_event 필터링 테스트
- [ ] EventMapping API: category_event_mapping 필터링 테스트

### 6.3 문서 검증
- [ ] Swagger UI에 Enum 값 목록 표시 확인
- [ ] ReDoc에 Enum 값 목록 표시 확인

---

## 7. 구현 순서 (TDD)

### Phase 1: Enum 정의 (app/utils/enums.py)
1. `EnumEventCategory` 신규 생성 (Event용: `detection`, `malfunction`, `connection`)
2. 기존 `EnumEventCategory` → `EnumMappingEventCategory`로 이름 변경
3. 하위 호환성 별칭 설정 (`EnumCategoryEvent = EnumMappingEventCategory`)

### Phase 2: Event 모델/스키마
1. Event 모델 `category_event` Enum 적용
2. Event 스키마 업데이트
3. Swagger 확인

### Phase 3: EventMapping 모델/스키마
1. EventMapping 모델 `category_event` → `category_event_mapping` 변경
2. EventMapping 스키마 업데이트
3. EventMapping 라우터 업데이트

### Phase 4: 문서 업데이트
1. GOP_Restful_Api_연동설계.md 업데이트
2. GOP_스키마_전체.md 업데이트
3. Swagger/ReDoc 최종 확인

---

## 8. Breaking Changes

| 항목 | 변경 내용 | 영향 |
|------|----------|------|
| EventMapping API | `category_event` → `category_event_mapping` | Request/Response 필드명 변경 |
| EventMapping DB | 컬럼명 변경 | 마이그레이션 필요 |
| Enum 이름 | `EnumEventCategory` → `EnumMappingEventCategory` | import 경로 변경 |

**클라이언트 대응**: EventMapping API 필드명 변경에 따른 클라이언트 코드 수정 필요

---

## 9. 레거시 정리

### 9.1 CameraEventMapping (레거시)

`CameraEventMapping` 모델은 레거시로, 현재 `EventMapping` + `EventMappingCamera`로 대체됨.
이 PRD에서는 CameraEventMapping 변경은 다루지 않음.

향후 레거시 정리 시 별도 PRD로 처리.

---

## 10. 참고 자료

- Event 모델: `app/models/event.py`
- EventMapping 모델: `app/models/integration.py`
- Enum 정의: `app/utils/enums.py`
- GOP 연동설계: `GOP_Restful_Api_연동설계.md`
- 스키마 문서: `docs/GOP_스키마_전체.md`
