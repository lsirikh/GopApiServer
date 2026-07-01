# PRD: ROI Point Validation & PUT Points Fix

**문서 버전**: v1.0
**작성일**: 2026-01-30
**참조 PRD**: `docs/PRD_Camera_Preset_ROI.md` v1.2
**상태**: Draft

---

## 1. 개요

### 1.1 목적

ROI(Region of Interest) API에서 발견된 2건의 버그를 수정합니다.
ROI는 다각형(polygon) 영역이므로 최소 3개의 꼭짓점(XyPoint)이 있어야 면적이 형성됩니다.
현재 구현은 이 제약 조건을 강제하지 않으며, PUT 엔드포인트에서 Points 데이터를 무시합니다.

### 1.2 버그 요약

| # | 엔드포인트 | 증상 | 심각도 |
|---|-----------|------|--------|
| BUG-1 | `POST /api/presets/{preset_id}/rois` | 포인트 1개로 ROI 생성 성공 (최소 3개 필요) | High |
| BUG-2 | `PUT /api/presets/{preset_id}/rois/{roi_id}` | 3개 포인트를 전송했으나 1개만 저장됨 (points 무시) | Critical |

---

## 2. 현재 상태 분석 (AS-IS)

### 2.1 BUG-1: POST 포인트 최소 개수 미검증

**재현 절차**:
```
POST /api/presets/1/rois
Body: {
  "name": "Test ROI",
  "resolution_width": 1920,
  "resolution_height": 1080,
  "points": [
    {"x": 0.1, "y": 0.1, "order": 0}   ← 1개만 전송
  ]
}
```

**현재 결과**: `201 Created` (성공 — 오동작)
**기대 결과**: `422 Unprocessable Entity` (최소 3개 포인트 필요)

**근본 원인**:

| 파일 | 라인 | 코드 | 문제 |
|------|------|------|------|
| `app/schemas/camera_preset.py` | 66 | `points: Optional[List[XyPointCreate]] = Field(default=None)` | `min_length` 제약 없음 |
| `app/routers/rois.py` | 192 | `if roi_data.points:` | points 개수 검증 없이 그대로 저장 |

**참고**: `app/routers/xypoints.py:23`에는 이미 올바른 검증이 존재:
```python
points: List[XyPointCreate] = Field(..., min_length=3, description="Minimum 3 points for polygon")
```

### 2.2 BUG-2: PUT 엔드포인트 Points 무시

**재현 절차**:
```
PUT /api/presets/1/rois/1
Body: {
  "name": "Updated ROI",
  "resolution_width": 1920,
  "resolution_height": 1080,
  "points": [
    {"x": 0.1, "y": 0.1, "order": 0},
    {"x": 0.9, "y": 0.1, "order": 1},
    {"x": 0.5, "y": 0.9, "order": 2}   ← 3개 전송
  ]
}
```

**현재 결과**: `200 OK`, `point_count: 1` (기존 포인트 유지, 새 포인트 무시)
**기대 결과**: `200 OK`, `point_count: 3` (기존 포인트 삭제 후 새 3개로 교체)

**근본 원인**:

| 파일 | 라인 | 코드 | 문제 |
|------|------|------|------|
| `app/routers/rois.py` | 337-341 | `roi.name = roi_data.name` ... | ROI 스칼라 필드만 업데이트 |
| `app/routers/rois.py` | - | (코드 없음) | **points 처리 코드 자체가 존재하지 않음** |

`replace_roi()` 함수의 현재 구현 (337-344행):
```python
# Replace all fields
roi.name = roi_data.name
roi.resolution_width = roi_data.resolution_width
roi.resolution_height = roi_data.resolution_height
roi.is_enable = roi_data.is_enable if roi_data.is_enable is not None else True

db.commit()
db.refresh(roi)
```

→ `roi_data.points`를 읽지도, 처리하지도 않음. 완전히 누락된 코드.

---

## 3. 수정 설계 (TO-BE)

### 3.1 BUG-1 수정: POST 포인트 최소 3개 검증

#### 3.1.1 Schema 변경

**파일**: `app/schemas/camera_preset.py`

```python
# AS-IS (line 66)
points: Optional[List[XyPointCreate]] = Field(default=None, description="Polygon vertices")

# TO-BE
points: List[XyPointCreate] = Field(..., min_length=3, description="Polygon vertices (minimum 3 points for polygon)")
```

**변경 사항**:
- `Optional` → 필수 (다각형 형성에 points가 반드시 필요)
- `min_length=3` 추가 (Pydantic이 자동 422 반환)
- `default=None` 제거

#### 3.1.2 Router 변경 (선택적)

`create_roi()` 내부에서 추가 검증은 불필요. Pydantic `min_length=3`이 이미 422를 반환하므로.

기존 `if roi_data.points:` 분기도 항상 true가 되므로 간소화 가능:
```python
# AS-IS
if roi_data.points:
    for point_data in roi_data.points:
        ...

# TO-BE (points는 항상 존재, 항상 >= 3개)
for point_data in roi_data.points:
    ...
```

#### 3.1.3 에러 응답

Pydantic이 자동 생성하는 422 응답:
```json
{
  "detail": [
    {
      "type": "too_short",
      "loc": ["body", "points"],
      "msg": "List should have at least 3 items after validation, not 1",
      "input": [{"x": 0.1, "y": 0.1, "order": 0}],
      "ctx": {"field_type": "List", "min_length": 3, "actual_length": 1}
    }
  ]
}
```

### 3.2 BUG-2 수정: PUT 엔드포인트 Points 교체 로직 추가

#### 3.2.1 Router 변경

**파일**: `app/routers/rois.py` — `replace_roi()` 함수

```python
# TO-BE: Points 교체 로직 추가
@router.put("/{preset_id}/rois/{roi_id}", response_model=ApiResponse[ROIResponse])
async def replace_roi(preset_id, roi_id, roi_data: ROICreate, db, current_user):
    # ... (기존 preset/roi 존재 확인 로직 유지)

    # Replace scalar fields
    roi.name = roi_data.name
    roi.resolution_width = roi_data.resolution_width
    roi.resolution_height = roi_data.resolution_height
    roi.is_enable = roi_data.is_enable if roi_data.is_enable is not None else True

    # ★ NEW: Replace all points (delete existing → create new)
    db.query(XyPoint).filter(XyPoint.roi_id == roi_id).delete()
    for point_data in roi_data.points:
        point = XyPoint(
            roi_id=roi_id,
            x=point_data.x,
            y=point_data.y,
            order=point_data.order
        )
        db.add(point)

    db.commit()
    db.refresh(roi)

    # ... (응답 반환)
```

**핵심 변경**:
1. 기존 XyPoint 전체 삭제: `db.query(XyPoint).filter(XyPoint.roi_id == roi_id).delete()`
2. 새 XyPoint 일괄 생성: `roi_data.points` 순회하며 생성
3. `ROICreate` schema의 `min_length=3` 적용으로 최소 3개 보장

> 이 패턴은 `xypoints.py:173-186` (`replace_points()`)에 이미 검증된 동일 로직이 존재함.

### 3.3 ConfigChangeLog 통합

PUT 엔드포인트에 ConfigChangeLog 기록 추가 (현재 누락):

```python
# before_state 캡처 (points 포함)
before_state = model_to_dict(roi)
before_state["point_count"] = roi.points.count()

# ... (수정 수행)

# after_state 캡처
after_state = model_to_dict(roi)
after_state["point_count"] = len(roi_data.points)

# ConfigChangeLog 기록
log_config_change(
    db=db,
    resource_type=EnumConfigResourceType.ROI,
    resource_id=roi.id,
    resource_name=f"ROI-{roi.id} ({roi.name})",
    action=EnumConfigActionType.UPDATED,
    before_state=before_changes,
    after_state=after_changes,
    description="ROI 전체 수정 (PUT)"
)
```

---

## 4. 영향 범위 분석

### 4.1 수정 대상 파일

| 파일 | 변경 내용 | 유형 |
|------|----------|------|
| `app/schemas/camera_preset.py` | `ROICreate.points`: Optional → Required, min_length=3 | Behavioral |
| `app/routers/rois.py` | `replace_roi()`: Points 삭제/재생성 로직 추가 | Behavioral |
| `app/routers/rois.py` | `replace_roi()`: ConfigChangeLog 추가 | Behavioral |
| `app/routers/rois.py` | `create_roi()`: `if roi_data.points:` 분기 제거 (항상 존재) | Structural |

### 4.2 호환성 영향

| 항목 | 영향 | 대응 |
|------|------|------|
| POST: points 없이 ROI 생성 | **Breaking** — 422 오류 | 클라이언트가 항상 3개 이상 포인트 전송 필요 |
| PUT: points 전송 시 교체됨 | **Breaking** — 기존에는 무시됐으나 이제 실제 교체 | 의도한 동작으로 오히려 정상화 |
| PUT: points 없이 전송 | **Breaking** — 422 오류 | ROICreate.points가 필수이므로 항상 전송 필요 |
| GET 응답 | 변경 없음 | - |
| PATCH | 변경 없음 | ROIUpdate schema는 points 필드 없음 |
| XyPoint 개별 API | 변경 없음 | 별도 라우터, 별도 스키마 |

### 4.3 기존 테스트 영향

| 테스트 | 현재 상태 | 수정 후 |
|--------|----------|---------|
| `test_creates_roi_without_points` | PASS (201) | **FAIL** → 수정 필요 (points 필수화) |
| `test_creates_roi_with_points` | PASS (3 points) | PASS (유지) |
| `test_replaces_all_roi_fields` | PASS (points 없이) | **FAIL** → 수정 필요 (points 필수화) |
| 그 외 ROI 테스트 | PASS | PASS (유지) |

---

## 5. TDD 구현 계획

### Phase 1: Schema Fix — ROICreate.points 필수화 (Structural + Behavioral)

| # | ActionItem | Type | File |
|---|-----------|------|------|
| 1.1 | TEST: POST ROI with 1 point → 422 | RED | `tests/test_roi_router.py` |
| 1.2 | TEST: POST ROI with 0 points (omitted) → 422 | RED | `tests/test_roi_router.py` |
| 1.3 | TEST: POST ROI with 2 points → 422 | RED | `tests/test_roi_router.py` |
| 1.4 | TEST: POST ROI with 3 points → 201 | RED (기존 테스트 확인) | `tests/test_roi_router.py` |
| 1.5 | IMPL: ROICreate.points → `List[XyPointCreate] = Field(..., min_length=3)` | GREEN | `app/schemas/camera_preset.py` |
| 1.6 | FIX: create_roi() `if roi_data.points:` 분기 제거 (항상 존재) | TIDY | `app/routers/rois.py` |
| 1.7 | FIX: test_creates_roi_without_points → points 3개 포함으로 수정 | GREEN | `tests/test_roi_router.py` |
| 1.8 | Verify: 전체 ROI 테스트 통과 | - | - |

### Phase 2: PUT Points Replace — 교체 로직 추가 (Behavioral)

| # | ActionItem | Type | File |
|---|-----------|------|------|
| 2.1 | TEST: PUT ROI with 3 points → point_count == 3 | RED | `tests/test_roi_router.py` |
| 2.2 | TEST: PUT ROI replaces existing points (기존 4개 → 새 3개) | RED | `tests/test_roi_router.py` |
| 2.3 | TEST: PUT ROI with 1 point → 422 (min_length=3) | RED | `tests/test_roi_router.py` |
| 2.4 | IMPL: replace_roi() — 기존 XyPoint 삭제 + 새 XyPoint 생성 | GREEN | `app/routers/rois.py` |
| 2.5 | FIX: test_replaces_all_roi_fields → points 3개 포함으로 수정 | GREEN | `tests/test_roi_router.py` |
| 2.6 | Verify: PUT 동작 확인 (DB에 3개 포인트 저장) | - | - |

### Phase 3: ConfigChangeLog & Verification (Behavioral)

| # | ActionItem | Type | File |
|---|-----------|------|------|
| 3.1 | TEST: PUT ROI → ConfigChangeLog 기록 확인 | RED | `tests/test_roi_router.py` |
| 3.2 | IMPL: replace_roi() ConfigChangeLog 추가 | GREEN | `app/routers/rois.py` |
| 3.3 | Verify: 전체 테스트 통과 (ROI + 전체) | - | - |
| 3.4 | Commit | - | - |

---

## 6. Summary

| Phase | Description | Items |
|-------|-------------|-------|
| Phase 1 | Schema Fix — ROICreate.points 필수화 | 8 |
| Phase 2 | PUT Points Replace — 교체 로직 추가 | 6 |
| Phase 3 | ConfigChangeLog & Verification | 4 |
| **Total** | | **18** |

---

## 7. 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| v1.0 | 2026-01-30 | 초안 작성 — BUG-1 (POST 포인트 미검증), BUG-2 (PUT 포인트 무시) |

---

**문서 끝**
