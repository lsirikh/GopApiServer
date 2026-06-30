# PRD: DeviceGroup Assign/Remove Polymorphic Fix

**문서 버전**: v1.0
**작성일**: 2026-01-30
**참조 PRD**: `docs/PRD_Device_Structure_Refactoring.md`, `docs/PRD_Device_Inheritance_Structure_Refactoring.md`
**상태**: Draft

---

## 1. 개요

### 1.1 목적

DeviceGroup의 디바이스 할당(Assign) 및 제거(Remove) API에서 발견된 3건의 버그를 수정합니다.
현재 구현은 Controller 디바이스만 처리하도록 하드코딩되어 있어, Sensor/Camera/Speaker/Enclosure/Lamp 디바이스를 그룹에 할당하거나 제거할 수 없습니다.

### 1.2 버그 요약

| # | 엔드포인트 | 증상 | 심각도 |
|---|-----------|------|--------|
| BUG-1 | `POST /{group_id}/devices` | Controller만 조회 — Sensor/Camera/Speaker/Enclosure/Lamp 디바이스 ID 전송 시 항상 skipped 처리 | Critical |
| BUG-2 | `POST /{group_id}/devices` | `category_device`가 항상 `CONTROLLER`로 저장 — Controller도 잘못된 카테고리가 될 수 있음 | Critical |
| BUG-3 | `DELETE /{group_id}/devices/{device_id}` | `category_device == CONTROLLER` 조건으로만 매핑 검색 — 비-Controller 디바이스 제거 불가 | High |

### 1.3 증상 재현

**시나리오**: Sensor(ID=101), Camera(ID=201)를 그룹에 할당

```
POST /api/devices/groups/1/devices
Body: {"device_ids": [101, 201]}
```

**현재 결과**:
```json
{
  "success": true,
  "data": {
    "group_id": 1,
    "assigned_device_ids": [],
    "skipped_device_ids": [101, 201],
    "message": "0개 디바이스 할당 완료, 2개 건너뜀"
  }
}
```
→ HTTP 200 성공 응답이지만 실제로는 아무 디바이스도 할당되지 않음.

**기대 결과**:
```json
{
  "success": true,
  "data": {
    "group_id": 1,
    "assigned_device_ids": [101, 201],
    "skipped_device_ids": [],
    "message": "2개 디바이스 할당 완료"
  }
}
```

---

## 2. 현재 상태 분석 (AS-IS)

### 2.1 BUG-1: Controller 테이블만 조회

**파일**: `app/routers/device_groups.py` — `assign_devices_to_group()` 함수

| 라인 | 코드 | 문제 |
|------|------|------|
| 684 | `device = db.query(Controller).filter(Controller.id == device_id).first()` | `Controller` 테이블만 조회. `Device` base class 미사용 |

Device 모델은 Polymorphic Joined Table Inheritance를 사용합니다 (`app/models/device.py:20-67`).
`db.query(Device)`로 조회하면 SQLAlchemy가 자동으로 polymorphic identity를 통해 올바른 자식 클래스(Controller, Sensor, Camera, Speaker, Enclosure, Lamp)를 반환합니다.

그러나 현재 코드는 `db.query(Controller)`로 조회하므로:
- Controller (ID 1~99): 정상 조회 → assigned ✅
- Sensor (ID 101~199): 조회 실패 → skipped ❌
- Camera (ID 201~299): 조회 실패 → skipped ❌
- Speaker (ID 301~399): 조회 실패 → skipped ❌
- Enclosure (ID 401~499): 조회 실패 → skipped ❌
- Lamp (ID 501~599): 조회 실패 → skipped ❌

### 2.2 BUG-2: category_device 하드코딩 (Assign)

**파일**: `app/routers/device_groups.py` — `assign_devices_to_group()` 함수

| 라인 | 코드 | 문제 |
|------|------|------|
| 692 | `DeviceGroupMapping.category_device == EnumDeviceCategory.CONTROLLER` | 중복 체크 시 항상 CONTROLLER로 검색 |
| 699 | `mapping = DeviceGroupMapping(device_id=device_id, category_device=EnumDeviceCategory.CONTROLLER, group_id=group_id)` | 매핑 생성 시 항상 CONTROLLER 카테고리 저장 |

**문제 시나리오** (BUG-1이 수정되었다고 가정):
1. Camera(ID=201)를 그룹 1에 할당
2. 매핑이 `(device_id=201, category_device=CONTROLLER, group_id=1)`로 저장됨
3. 그룹 상세 조회 시 `Device` 기반 조회로는 올바르게 Camera를 반환하지만, 카테고리 정보가 잘못됨
4. DeviceGroupMapping의 `UniqueConstraint('device_id', 'category_device', 'group_id')`에서 동일 device_id라도 category_device가 틀리면 중복으로 인식하지 못해 데이터 무결성 문제 발생 가능

### 2.3 BUG-3: category_device 하드코딩 (Remove)

**파일**: `app/routers/device_groups.py` — `remove_device_from_group()` 함수

| 라인 | 코드 | 문제 |
|------|------|------|
| 761 | `DeviceGroupMapping.category_device == EnumDeviceCategory.CONTROLLER` | 매핑 검색 시 항상 CONTROLLER로 필터 |

**재현**:
```
DELETE /api/devices/groups/1/devices/201
```

현재: `404 Not Found` — Camera(ID=201)의 매핑이 CONTROLLER 카테고리가 아니면 찾을 수 없음
(단, BUG-2로 인해 CONTROLLER로 저장되었다면 우연히 성공할 수도 있음 — 이중 버그)

### 2.4 정상 구현 참조 (Group Detail)

같은 파일의 `get_device_group()` 함수 (라인 316-407)는 올바른 구현을 가지고 있습니다:

```python
# 라인 322: Device base class로 polymorphic query
device = db.query(Device).filter(Device.id == mapping.device_id).first()

# 라인 337-391: isinstance()로 디바이스 타입별 분기
if isinstance(device, Controller):
    ...
elif isinstance(device, Sensor):
    ...
elif isinstance(device, Camera):
    ...
elif isinstance(device, Speaker):
    ...
elif isinstance(device, Enclosure):
    ...
elif isinstance(device, Lamp):
    ...
```

→ `assign_devices_to_group()`과 `remove_device_from_group()`도 동일한 패턴을 적용해야 합니다.

---

## 3. 수정 설계 (TO-BE)

### 3.1 BUG-1 + BUG-2 수정: assign_devices_to_group()

**파일**: `app/routers/device_groups.py`

#### 3.1.1 디바이스 조회 변경

```python
# AS-IS (라인 684)
device = db.query(Controller).filter(Controller.id == device_id).first()

# TO-BE: Device base class로 polymorphic query
device = db.query(Device).filter(Device.id == device_id).first()
```

#### 3.1.2 category_device 동적 추출

```python
# AS-IS (라인 690-693)
existing_mapping = db.query(DeviceGroupMapping).filter(
    DeviceGroupMapping.device_id == device_id,
    DeviceGroupMapping.category_device == EnumDeviceCategory.CONTROLLER,
    DeviceGroupMapping.group_id == group_id
).first()

# TO-BE: device.category_device 사용
existing_mapping = db.query(DeviceGroupMapping).filter(
    DeviceGroupMapping.device_id == device_id,
    DeviceGroupMapping.category_device == device.category_device,
    DeviceGroupMapping.group_id == group_id
).first()
```

```python
# AS-IS (라인 699)
mapping = DeviceGroupMapping(
    device_id=device_id,
    category_device=EnumDeviceCategory.CONTROLLER,
    group_id=group_id
)

# TO-BE: device.category_device 사용
mapping = DeviceGroupMapping(
    device_id=device_id,
    category_device=device.category_device,
    group_id=group_id
)
```

### 3.2 BUG-3 수정: remove_device_from_group()

**파일**: `app/routers/device_groups.py`

#### 3.2.1 매핑 검색 변경

디바이스 제거 시에도 먼저 Device를 조회하여 올바른 `category_device`를 확인해야 합니다.

```python
# AS-IS (라인 759-763)
mapping = db.query(DeviceGroupMapping).filter(
    DeviceGroupMapping.device_id == device_id,
    DeviceGroupMapping.category_device == EnumDeviceCategory.CONTROLLER,
    DeviceGroupMapping.group_id == group_id
).first()

# TO-BE: Device 조회 후 category_device 사용
device = db.query(Device).filter(Device.id == device_id).first()
if not device:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"success": False, "message": f"Device ID {device_id} not found"}
    )

mapping = db.query(DeviceGroupMapping).filter(
    DeviceGroupMapping.device_id == device_id,
    DeviceGroupMapping.category_device == device.category_device,
    DeviceGroupMapping.group_id == group_id
).first()
```

### 3.3 ConfigChangeLog 개선

Assign/Remove 로그에 `category_device` 정보 추가:

```python
# Assign 로그 (라인 706-715)
log_config_change(
    db=db,
    resource_type=EnumConfigResourceType.DEVICE_GROUP,
    resource_id=group_id,
    resource_name=f"DeviceGroup-{group_id} ({group.name})",
    action=EnumConfigActionType.ASSIGNED,
    after_state={"device_ids": assigned, "categories": assigned_categories},  # ★ categories 추가
    description=f"DeviceGroup에 {len(assigned)}개 디바이스 할당"
)

# Remove 로그 (라인 775-783)
log_config_change(
    db=db,
    resource_type=EnumConfigResourceType.DEVICE_GROUP,
    resource_id=group_id,
    resource_name=f"DeviceGroup-{group_id} ({group.name})",
    action=EnumConfigActionType.UNASSIGNED,
    before_state={"device_id": device_id, "category_device": device.category_device.value},  # ★ category 추가
    description=f"DeviceGroup에서 디바이스 {device_id} ({device.category_device.value}) 제거"
)
```

---

## 4. 영향 범위 분석

### 4.1 수정 대상 파일

| 파일 | 변경 내용 | 유형 |
|------|----------|------|
| `app/routers/device_groups.py` | `assign_devices_to_group()`: `Controller` → `Device` query | Behavioral |
| `app/routers/device_groups.py` | `assign_devices_to_group()`: `EnumDeviceCategory.CONTROLLER` → `device.category_device` | Behavioral |
| `app/routers/device_groups.py` | `remove_device_from_group()`: Device 조회 추가 + 동적 category_device | Behavioral |
| `app/routers/device_groups.py` | Assign/Remove ConfigChangeLog에 category 정보 추가 | Behavioral |

### 4.2 호환성 영향

| 항목 | 영향 | 대응 |
|------|------|------|
| Assign: Controller 할당 | 동일 동작 (기존 정상) | 기존 동작 유지 |
| Assign: Sensor/Camera/Speaker/Enclosure/Lamp | **수정됨** — 기존에는 항상 skipped, 이제 정상 assigned | 의도한 동작으로 정상화 |
| Remove: Controller 제거 | 동일 동작 (기존 정상) | 기존 동작 유지 |
| Remove: 비-Controller 제거 | **수정됨** — 기존에는 404, 이제 정상 제거 | 의도한 동작으로 정상화 |
| Group Detail 조회 | 변경 없음 | 이미 올바른 polymorphic 구현 |
| DeviceAssignRequest schema | 변경 없음 | `device_ids: List[int]`만 받음 |
| DeviceAssignResponse schema | 변경 없음 | assigned/skipped 구조 유지 |

### 4.3 기존 데이터 영향

기존에 잘못 저장된 매핑 데이터 확인 필요:
- `device_group_mappings`에서 `category_device = 'controller'`인데 실제 device가 Controller가 아닌 레코드
- 이러한 레코드는 수동 마이그레이션 또는 재할당으로 수정

---

## 5. TDD 구현 계획

### Phase 1: Assign Fix — Device Polymorphic Query (Behavioral)

| # | ActionItem | Type | File |
|---|-----------|------|------|
| 1.1 | TEST: Sensor 디바이스를 그룹에 할당 → assigned_device_ids에 포함 | RED | `tests/test_device_groups.py` |
| 1.2 | TEST: Camera 디바이스를 그룹에 할당 → assigned_device_ids에 포함 | RED | `tests/test_device_groups.py` |
| 1.3 | TEST: Speaker 디바이스를 그룹에 할당 → assigned_device_ids에 포함 | RED | `tests/test_device_groups.py` |
| 1.4 | TEST: Enclosure 디바이스를 그룹에 할당 → assigned_device_ids에 포함 | RED | `tests/test_device_groups.py` |
| 1.5 | TEST: Lamp 디바이스를 그룹에 할당 → assigned_device_ids에 포함 | RED | `tests/test_device_groups.py` |
| 1.6 | TEST: 여러 디바이스 타입 혼합 할당 (Controller + Sensor + Camera) → 모두 assigned | RED | `tests/test_device_groups.py` |
| 1.7 | IMPL: `db.query(Controller)` → `db.query(Device)` | GREEN | `app/routers/device_groups.py` |
| 1.8 | IMPL: `EnumDeviceCategory.CONTROLLER` → `device.category_device` (existing_mapping 조회) | GREEN | `app/routers/device_groups.py` |
| 1.9 | IMPL: `EnumDeviceCategory.CONTROLLER` → `device.category_device` (매핑 생성) | GREEN | `app/routers/device_groups.py` |
| 1.10 | Verify: Phase 1 전체 테스트 통과 | - | - |

### Phase 2: Assign Validation — category_device 정확성 (Behavioral)

| # | ActionItem | Type | File |
|---|-----------|------|------|
| 2.1 | TEST: Sensor 할당 후 매핑의 category_device == SENSOR 확인 | RED | `tests/test_device_groups.py` |
| 2.2 | TEST: Camera 할당 후 매핑의 category_device == CAMERA 확인 | RED | `tests/test_device_groups.py` |
| 2.3 | TEST: 동일 디바이스 중복 할당 시 skipped 처리 (category_device 포함 정확한 중복 체크) | RED | `tests/test_device_groups.py` |
| 2.4 | TEST: 존재하지 않는 device_id → skipped 처리 | RED | `tests/test_device_groups.py` |
| 2.5 | Verify: Phase 2 전체 테스트 통과 | - | - |

### Phase 3: Remove Fix — Polymorphic Remove (Behavioral)

| # | ActionItem | Type | File |
|---|-----------|------|------|
| 3.1 | TEST: Sensor 디바이스를 그룹에서 제거 → 성공 | RED | `tests/test_device_groups.py` |
| 3.2 | TEST: Camera 디바이스를 그룹에서 제거 → 성공 | RED | `tests/test_device_groups.py` |
| 3.3 | TEST: Speaker 디바이스를 그룹에서 제거 → 성공 | RED | `tests/test_device_groups.py` |
| 3.4 | TEST: 존재하지 않는 device_id 제거 시도 → 404 | RED | `tests/test_device_groups.py` |
| 3.5 | TEST: 그룹에 미할당된 device_id 제거 시도 → 404 | RED | `tests/test_device_groups.py` |
| 3.6 | IMPL: remove_device_from_group() — Device 조회 + 동적 category_device | GREEN | `app/routers/device_groups.py` |
| 3.7 | Verify: Phase 3 전체 테스트 통과 | - | - |

### Phase 4: Group Detail Verification & ConfigChangeLog (Behavioral)

| # | ActionItem | Type | File |
|---|-----------|------|------|
| 4.1 | TEST: 다양한 타입 할당 후 그룹 상세 조회 → 모든 디바이스 타입 포함 확인 | RED | `tests/test_device_groups.py` |
| 4.2 | TEST: Assign ConfigChangeLog에 category 정보 포함 확인 | RED | `tests/test_device_groups.py` |
| 4.3 | TEST: Remove ConfigChangeLog에 category 정보 포함 확인 | RED | `tests/test_device_groups.py` |
| 4.4 | IMPL: ConfigChangeLog에 category_device 정보 추가 | GREEN | `app/routers/device_groups.py` |
| 4.5 | Verify: 전체 테스트 통과 (device_groups + 전체) | - | - |
| 4.6 | Commit | - | - |

---

## 6. Summary

| Phase | Description | Items |
|-------|-------------|-------|
| Phase 1 | Assign Fix — Device Polymorphic Query | 10 |
| Phase 2 | Assign Validation — category_device 정확성 | 5 |
| Phase 3 | Remove Fix — Polymorphic Remove | 7 |
| Phase 4 | Group Detail Verification & ConfigChangeLog | 6 |
| **Total** | | **28** |

---

## 7. 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| v1.0 | 2026-01-30 | 초안 작성 — BUG-1 (Controller만 조회), BUG-2 (category_device 하드코딩), BUG-3 (Remove 하드코딩) |

---

**문서 끝**
