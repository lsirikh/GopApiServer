# PRD: 비정형 보고서 템플릿 컴포넌트 필터링

> **Version**: 1.0
> **Date**: 2026-02-12
> **Status**: Draft

---

## 1. 문제 정의

### 1.1 현상

비정형(CUSTOM) 템플릿으로 생성된 보고서의 응답 데이터가 정형(STANDARD) 템플릿으로 생성된 보고서와 **완전히 동일**하다.

### 1.2 원인 분석

3개 지점에서 `report_type`과 `template.components`를 **전혀 참조하지 않음**:

#### 원인 1: Preview API — `GET /api/reports/generations/{id}/preview`

```python
# reports.py:554-558 (현재 코드)
service = ReportService(db)
days = period_days.get(generation.period_type, 7)
structured_data = service.get_structured_preview_data(days)  # ← 항상 전체 11섹션 반환
```

- `generation.report_type` 확인 없음
- `generation.template_id`로 템플릿 조회 없음
- 컴포넌트 필터링 없음

#### 원인 2: 서비스 레이어 — `get_structured_preview_data()`

```python
# report_service.py:549 (현재 시그니처)
def get_structured_preview_data(self, days: int = 7) -> Dict[str, Any]:
```

- `enabled_components` 파라미터 없음
- 하드코딩된 11개 섹션 / 21개 컴포넌트 전체를 항상 반환
- STANDARD든 CUSTOM이든 동일한 결과

#### 원인 3: PDF 생성 — `generate_report_async()`

```python
# report_service.py:868-1055 (현재 코드)
preview_data = self.get_preview_data()
device_stats = self.get_device_statistics()
# ... 모든 통계 수집, 모든 차트 생성, 모든 그리드 포함
```

- 템플릿 컴포넌트 참조 없이 전체 데이터 수집
- 모든 차트/그리드를 PDF에 포함

### 1.3 영향 범위

| 영향 | 설명 |
|------|------|
| Preview API | CUSTOM 보고서 미리보기에 불필요한 섹션 포함 |
| PDF 생성 | CUSTOM 보고서 PDF에 불필요한 차트/테이블 포함 |
| HTML 미리보기 | 프론트엔드에서 필터링 불가 (서버가 전체 데이터 전송) |
| 성능 | 불필요한 DB 쿼리 실행 (사용하지 않는 컴포넌트 데이터도 수집) |

---

## 2. 컴포넌트-섹션 매핑 구조

현재 `get_structured_preview_data()`의 11개 섹션과 21개 `EnumReportComponent`의 매핑:

| Section Name | Section Title | 포함 컴포넌트 ID |
|---|---|---|
| `summary` | 1. 요약 | `SUMMARY_CARD` |
| `device_charts` | 2. 장비 현황 | `DEVICE_STATUS_PIE`, `DEVICE_TYPE_BAR` |
| `event_charts` | 3. 이벤트 현황 | `EVENT_SUMMARY_PIE`, `EVENT_TREND_LINE` |
| `system_charts` | 4. 시스템 현황 | `SYSTEM_SEVERITY_BAR`, `SYSTEM_TREND_LINE` |
| `user_charts` | 5. 사용자 현황 | `USER_ROLE_PIE`, `USER_LOGIN_TREND_LINE`, `USER_LOGIN_RESULT_PIE` |
| `device_grid` | 6. 장비 목록 | `DEVICE_GRID` |
| `event_grids` | 7. 이벤트 상세 | `EVENT_DETECTION_GRID`, `EVENT_MALFUNCTION_GRID`, `EVENT_ACTION_GRID` |
| `system_event_grid` | 8. 시스템 이벤트 | `SYSTEM_EVENT_GRID` |
| `config_grid` | 9. 설정 변경 이력 | `SYSTEM_CONFIG_GRID` |
| `audit_grid` | 10. 감사 로그 | `SYSTEM_AUDIT_GRID` |
| `user_grids` | 11. 사용자 상세 | `USER_GRID`, `USER_LOGIN_GRID`, `USER_SESSION_GRID` |

> **핵심**: `EVENT_DAILY_BAR`는 `COMPONENT_CATEGORIES`에 정의되어 있으나 `get_structured_preview_data()`에서 구현되지 않음 (기존 미구현 — 이번 스코프 아님)

---

## 3. 수정 설계

### 3.1 정형(STANDARD) vs 비정형(CUSTOM) 동작 차이

| | STANDARD (정형) | CUSTOM (비정형) |
|---|---|---|
| 템플릿 참조 | 불필요 (`template_id = null`) | 필수 (`template_id` → 컴포넌트 목록) |
| 반환 섹션 | 전체 11섹션 / 21컴포넌트 | 템플릿에서 `enabled=true`인 컴포넌트만 |
| 섹션 순서 | 고정 (1~11) | 템플릿 `components[].order` 순서 |
| DB 쿼리 | 전체 실행 | 필요한 통계만 실행 (성능 최적화) |

### 3.2 수정 대상 파일

| 파일 | 수정 내용 |
|---|---|
| `app/services/report_service.py` | `get_structured_preview_data()`에 `enabled_components` 파라미터 추가, 필터링 로직 |
| `app/routers/reports.py` | Preview 엔드포인트에서 `report_type` 분기 + 템플릿 컴포넌트 조회 |

### 3.3 `get_structured_preview_data()` 수정

```python
def get_structured_preview_data(
    self,
    days: int = 7,
    enabled_components: Optional[List[str]] = None  # 추가
) -> Dict[str, Any]:
```

**필터링 로직**:
1. `enabled_components`가 `None`이면 → 전체 반환 (STANDARD 동작, 기존과 동일)
2. `enabled_components`가 제공되면 → 각 섹션의 charts/grids에서 `id`가 목록에 있는 것만 포함
3. 필터링 후 charts와 grids가 모두 비어있는 섹션은 제거 (단, summary는 summary_data가 있으면 유지)
4. 불필요한 DB 쿼리 스킵 (해당 카테고리 컴포넌트가 하나도 없으면 통계 수집 생략)

### 3.4 Preview 엔드포인트 수정

```python
@router.get("/generations/{generation_id}/preview")
def preview_report(generation_id: int, db: Session = Depends(get_db)):
    generation = ...  # 기존 조회

    # CUSTOM 타입이면 템플릿 컴포넌트 조회
    enabled_components = None
    if generation.report_type == "CUSTOM" and generation.template_id:
        template = db.query(ReportTemplate).filter(
            ReportTemplate.id == generation.template_id
        ).first()
        if template and template.components:
            enabled_components = [
                c["id"] for c in template.components
                if c.get("enabled", True)
            ]

    service = ReportService(db)
    days = period_days.get(generation.period_type, 7)
    structured_data = service.get_structured_preview_data(days, enabled_components)
    ...
```

### 3.5 `generate_report_async()` 수정

PDF 생성 시에도 동일한 필터링 적용:
- CUSTOM이면 `generation.template_id`로 템플릿 조회
- 활성화된 컴포넌트만 차트 생성 및 그리드 포함

---

## 4. 비수정 대상

| 항목 | 사유 |
|---|---|
| DB 스키마 | 테이블/컬럼 변경 없음 |
| Pydantic 스키마 | 기존 응답 구조 유지 (sections 배열의 내용만 달라짐) |
| 기존 STANDARD 동작 | `enabled_components=None` 시 기존과 100% 동일 |
| `EVENT_DAILY_BAR` 미구현 | 기존 미구현 상태 유지 (별도 이슈) |
| GOP 문서 | API 시그니처 변경 없음, 응답 내용물 필터링만 달라짐 |

---

## 5. 작업 목록

| # | 작업 | 유형 |
|---|---|---|
| 1 | `get_structured_preview_data()` 필터링 테스트 작성 | Test |
| 2 | `get_structured_preview_data()` 에 `enabled_components` 파라미터 + 필터링 로직 구현 | Code |
| 3 | Preview 엔드포인트 CUSTOM 분기 테스트 작성 | Test |
| 4 | Preview 엔드포인트에서 CUSTOM 시 템플릿 컴포넌트 조회 + 전달 구현 | Code |
| 5 | `generate_report_async()` 필터링 테스트 작성 | Test |
| 6 | `generate_report_async()` CUSTOM 시 차트/그리드 필터링 구현 | Code |
| 7 | 기존 STANDARD 동작 회귀 테스트 확인 | Test |
