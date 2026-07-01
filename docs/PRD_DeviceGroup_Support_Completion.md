# PRD: 장비 DeviceGroup 지원 완성 (Speaker, Enclosure, Lamp)

**문서 버전**: v1.0
**작성일**: 2026-02-25
**상태**: Draft

---

## 1. 개요

### 1.1 배경

GOP 시스템의 6개 장비 타입 중 Controller, Sensor, Camera는 DeviceGroup N:N 관계를 완전히 지원하지만, Speaker, Enclosure, Lamp는 누락되거나 불완전한 상태이다.

**현재 구현 상태:**

| 장비 | Response `device_groups` | Create `group_ids` | Update `group_ids` | Router 처리 |
|------|:-:|:-:|:-:|:-:|
| Controller | O | O | O | O |
| Sensor | O | O | O | O |
| Camera | O | O | O | O |
| **Speaker** | **X** | **X** | **X** | **X** |
| **Enclosure** | **X** | **X** | **X** | **X** |
| **Lamp** | O | **X** | **X** | **X** (깨진 코드) |

### 1.2 목적

- Speaker, Enclosure, Lamp에 DeviceGroup N:N 관계 지원을 Controller/Sensor/Camera와 동일한 수준으로 완성한다.
- 모든 장비 타입에서 일관된 `device_groups` 응답과 `group_ids` 입력을 보장한다.

### 1.3 범위

| 항목 | 포함 여부 |
|------|----------|
| Speaker 스키마/라우터 DeviceGroup 지원 추가 | O |
| Enclosure 스키마/라우터 DeviceGroup 지원 추가 | O |
| Lamp 스키마 `group_ids` 추가 및 라우터 수정 | O |
| NestedResponse 스키마 변경 | X (Event 내 nested에는 불필요) |
| DB 모델/테이블 변경 | X (Device.group_mappings 이미 존재) |

---

## 2. 요구사항

### 2.1 기능 요구사항

#### FR-1: Speaker DeviceGroup 지원 (전체 누락)

**스키마 변경:**

- `SpeakerCreate`: `group_ids: Optional[List[int]]` 추가
- `SpeakerUpdate`: `group_ids: Optional[List[int]]` 추가
- `SpeakerResponse`: `device_groups: List[DeviceGroupNestedResponse]` 추가

**라우터 변경 (`app/routers/speakers.py`):**

- `_get_device_groups_nested()` 헬퍼 추가
- `_update_device_group_mappings()` 헬퍼 추가
- POST(생성), PATCH(수정), PUT(교체) 시 `group_ids` 처리
- GET(조회) 시 `device_groups` 응답 포함

#### FR-2: Enclosure DeviceGroup 지원 (전체 누락)

**스키마 변경:**

- `EnclosureCreate`: `group_ids: Optional[List[int]]` 추가
- `EnclosureUpdate`: `group_ids: Optional[List[int]]` 추가
- `EnclosureResponse`: `device_groups: List[DeviceGroupNestedResponse]` 추가

**라우터 변경 (`app/routers/enclosures.py`):**

- `_get_device_groups_nested()` 헬퍼 추가
- `_update_device_group_mappings()` 헬퍼 추가
- POST(생성), PATCH(수정), PUT(교체) 시 `group_ids` 처리
- GET(조회) 시 `device_groups` 응답 포함

#### FR-3: Lamp DeviceGroup 지원 (부분 누락 + 깨진 코드 수정)

**스키마 변경:**

- `LampCreate`: `group_ids: Optional[List[int]]` 추가
- `LampUpdate`: `group_ids: Optional[List[int]]` 추가
- `LampResponse`: 이미 `device_groups` 있음 (변경 없음)

**라우터 변경 (`app/routers/lamps.py`):**

- `_lamp_to_response()` 의 깨진 group_mappings 접근 수정 → 정상 패턴(`DeviceGroupMapping` 쿼리)으로 교체
- POST(생성), PATCH(수정), PUT(교체) 시 `group_ids` 처리 추가

### 2.2 비기능 요구사항

- **NFR-1**: Controller/Sensor/Camera와 동일한 패턴 사용 (일관성)
- **NFR-2**: 기존 API 하위 호환성 유지 (`group_ids`는 Optional)
- **NFR-3**: `group_ids` 미전달 시 기존 그룹 매핑 유지 (null과 빈 배열 구분)

---

## 3. API 스키마 변경

### 3.1 Speaker

**SpeakerCreate 추가 필드:**
```python
group_ids: Optional[List[int]] = Field(None, description="소속 디바이스 그룹 ID 배열 (N:N 관계)")
```

**SpeakerUpdate 추가 필드:**
```python
group_ids: Optional[List[int]] = Field(None, description="소속 디바이스 그룹 ID 배열 (N:N 관계)")
```

**SpeakerResponse 추가 필드:**
```python
device_groups: List[DeviceGroupNestedResponse] = Field(
    default=[], description="소속 디바이스 그룹 목록 (N:N 관계)"
)
```

### 3.2 Enclosure

**EnclosureCreate 추가 필드:**
```python
group_ids: Optional[List[int]] = Field(None, description="소속 디바이스 그룹 ID 배열 (N:N 관계)")
```

**EnclosureUpdate 추가 필드:**
```python
group_ids: Optional[List[int]] = Field(None, description="소속 디바이스 그룹 ID 배열 (N:N 관계)")
```

**EnclosureResponse 추가 필드:**
```python
device_groups: List[DeviceGroupNestedResponse] = Field(
    default=[], description="소속 디바이스 그룹 목록 (N:N 관계)"
)
```

### 3.3 Lamp

**LampCreate 추가 필드:**
```python
group_ids: Optional[List[int]] = Field(None, description="소속 디바이스 그룹 ID 배열 (N:N 관계)")
```

**LampUpdate 추가 필드:**
```python
group_ids: Optional[List[int]] = Field(None, description="소속 디바이스 그룹 ID 배열 (N:N 관계)")
```

### 3.4 Response 예시 (공통)

```json
{
  "success": true,
  "message": "...",
  "data": {
    "id": 1,
    "name_device": "장비명",
    "...": "...",
    "device_groups": [
      {
        "id": 1,
        "name": "GOP 1구역",
        "description": "GOP 1구역 장비 그룹",
        "device_count": 5
      },
      {
        "id": 3,
        "name": "야간 감시",
        "description": "야간 감시 그룹",
        "device_count": 3
      }
    ]
  }
}
```

### 3.5 Create/Update 예시 (공통)

```json
{
  "name_device": "장비명",
  "...": "...",
  "group_ids": [1, 3]
}
```

---

## 4. 라우터 변경

### 4.1 참조 패턴 (Controller/Sensor/Camera 공통)

각 라우터에는 두 개의 헬퍼 함수가 있다:

**조회용 헬퍼:**
```python
def _get_device_groups_nested(db: Session, device_id: int) -> List[DeviceGroupNestedResponse]:
    """DeviceGroupMapping 테이블에서 해당 장비의 그룹 목록 조회"""
    mappings = db.query(DeviceGroupMapping).filter(
        DeviceGroupMapping.device_id == device_id
    ).all()
    group_ids = [m.group_id for m in mappings]
    if not group_ids:
        return []
    groups = db.query(DeviceGroup).filter(DeviceGroup.id.in_(group_ids)).all()
    return [
        DeviceGroupNestedResponse(
            id=g.id, name=g.name, description=g.description,
            device_count=db.query(DeviceGroupMapping).filter(
                DeviceGroupMapping.group_id == g.id
            ).count()
        ) for g in groups
    ]
```

**수정용 헬퍼:**
```python
def _update_device_group_mappings(db: Session, device_id: int, category: EnumDeviceCategory, group_ids: List[int]):
    """DeviceGroupMapping 동기화 (기존 삭제 → 새로 삽입)"""
    db.query(DeviceGroupMapping).filter(
        DeviceGroupMapping.device_id == device_id,
        DeviceGroupMapping.category_device == category
    ).delete()
    for gid in group_ids:
        db.add(DeviceGroupMapping(device_id=device_id, group_id=gid, category_device=category))
```

### 4.2 적용 대상

| 라우터 | 헬퍼 추가 | POST | PATCH | PUT | GET 응답 |
|--------|:-:|:-:|:-:|:-:|:-:|
| `speakers.py` | O | O | O | O | O |
| `enclosures.py` | O | O | O | O | O |
| `lamps.py` | 수정 | O | O | O | 수정 |

### 4.3 Lamp 라우터 수정 사항

기존 `_lamp_to_response()`의 깨진 코드:
```python
# 기존 (동작 안 함 - relationship 미정의)
if hasattr(lamp, 'group_mappings') and lamp.group_mappings:
    for mapping in lamp.group_mappings:
        group = mapping.device_group  # ← 존재하지 않는 relationship
```

정상 패턴으로 교체:
```python
# 수정 후 (DeviceGroupMapping 직접 쿼리)
device_groups = _get_device_groups_nested(db, lamp.id)
```

---

## 5. 구현 계획

### 5.1 영향받는 파일

| 파일 | 변경 내용 |
|------|----------|
| `app/schemas/device.py` | Speaker/Enclosure/Lamp Create/Update/Response 스키마 수정 |
| `app/routers/speakers.py` | 헬퍼 함수 + CRUD group_ids 처리 추가 |
| `app/routers/enclosures.py` | 헬퍼 함수 + CRUD group_ids 처리 추가 |
| `app/routers/lamps.py` | 깨진 코드 수정 + CRUD group_ids 처리 추가 |

### 5.2 TDD 구현 단계

| Phase | 테스트 | 구현 |
|-------|--------|------|
| 1 | Speaker 스키마 단위 테스트 (group_ids, device_groups 필드) | SpeakerCreate/Update/Response 스키마 수정 |
| 2 | Speaker API 통합 테스트 (POST with group_ids, GET device_groups) | speakers.py 라우터 수정 |
| 3 | Enclosure 스키마 단위 테스트 | EnclosureCreate/Update/Response 스키마 수정 |
| 4 | Enclosure API 통합 테스트 | enclosures.py 라우터 수정 |
| 5 | Lamp 스키마 단위 테스트 | LampCreate/Update 스키마 수정 |
| 6 | Lamp API 통합 테스트 (깨진 코드 수정 포함) | lamps.py 라우터 수정 |

### 5.3 `group_ids` null vs 빈 배열 처리 규칙

| 입력값 | 동작 |
|--------|------|
| `group_ids` 미전달 (null) | 기존 그룹 매핑 유지 (변경 없음) |
| `group_ids: []` (빈 배열) | 모든 그룹 매핑 제거 |
| `group_ids: [1, 3]` | 기존 매핑 삭제 후 새로 설정 |

---

## 6. GOP 문서 업데이트

- [ ] `docs/GOP_Restful_Api_연동설계.md` — Speaker/Enclosure/Lamp API Response에 `device_groups` 추가
- [ ] `docs/GOP_Restful_Api_연동설계.md` — Speaker/Enclosure/Lamp Create/Update Request에 `group_ids` 추가