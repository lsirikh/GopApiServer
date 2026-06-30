# PRD: Report Preview System - Gap Analysis & Implementation Guide

**Version:** 1.0
**Date:** 2026-02-03
**Reference Mockup:** `docs/preview_mockup.html`
**Reference Template:** `app/templates/reports/preview.html`
**Reference Service:** `app/services/report_service.py`

---

## 1. Overview

이 문서는 `docs/preview_mockup.html`에 정의된 보고서 프리뷰 목표 구조와 현재 구현된 코드 사이의 차이(Gap)를 분석하고, mockup과 동일한 보고서를 실제 시스템에서 생성하기 위해 필요한 수정사항을 정리한다.

### 1.1 현재 시스템 구성

| Component | File | Role |
|-----------|------|------|
| SQLAlchemy Model | `app/models/report.py` | ReportTemplate, ReportGeneration |
| Pydantic Schema | `app/schemas/report.py` | Request/Response 스키마 |
| Router | `app/routers/reports.py` | API 엔드포인트 |
| Service | `app/services/report_service.py` | 데이터 수집, PDF 생성 |
| Jinja2 Template | `app/templates/reports/preview.html` | HTML 프리뷰 렌더링 |
| PDF Generator | `app/utils/pdf_generator.py` | ReportLab PDF 생성 |
| Chart Generator | `app/utils/chart_generator.py` | Matplotlib 차트 이미지 |
| Preview Route | `app/main.py:583-609` | `/reports/preview/{id}` |
| Mockup Target | `docs/preview_mockup.html` | 목표 디자인 |

---

## 2. Mockup 목표 구조 (11 Sections)

```
┌─────────────────────────────────────────────┐
│  Cover Page                                  │
│  ├─ 제목: 주간 현황보고                         │
│  ├─ 기간, 생성자, 보고서유형, 상태               │
│  └─ TOC (목차 1~11)                           │
├─────────────────────────────────────────────┤
│  1. 요약 (Summary Cards)                     │
│  ├─ 장비 현황 카드 (6종류 × 정상/전체)           │
│  ├─ 이벤트 현황 카드 (탐지/장애/조치보고)         │
│  └─ 시스템 현황 카드 (서버별 상태/수량)           │
├─────────────────────────────────────────────┤
│  2~4. 차트 묶음 (Single Paper)               │
│  ├─ 2. 장비 현황: 상태 분포 PIE + 유형 BAR      │
│  ├─ 3. 이벤트 현황: 유형 PIE + 추이 LINE        │
│  └─ 4. 시스템 현황: 심각도 BAR + 추이 LINE       │
├─────────────────────────────────────────────┤
│  5. 사용자 현황 (Charts)                      │
│  ├─ 역할 PIE + 로그인추이 LINE                  │
│  └─ 로그인결과 PIE                              │
├─────────────────────────────────────────────┤
│  6. 장비 목록 (DataGrid)                      │
├─────────────────────────────────────────────┤
│  7. 이벤트 상세 (DataGrid)                    │
│  ├─ 탐지 이벤트 (120건, 자동 페이지 분할)        │
│  │   → ID,일시,탐지유형,장비유형,장비명,          │
│  │     조치보고일자,조치자,조치내용               │
│  └─ 장애 이벤트 (3건)                           │
│      → ID,일시,장애유형,장비유형,장비명,          │
│        조치보고일자,조치자,조치내용               │
├─────────────────────────────────────────────┤
│  8. 시스템 이벤트 (DataGrid)                   │
├─────────────────────────────────────────────┤
│  9. 설정 변경 이력 (DataGrid, 자동 분할)         │
├─────────────────────────────────────────────┤
│  10. 감사 로그 (DataGrid)                     │
├─────────────────────────────────────────────┤
│  11. 사용자 상세 (DataGrid)                   │
│  ├─ 사용자 목록                                │
│  ├─ 로그인 이력                                │
│  └─ 세션 목록                                  │
└─────────────────────────────────────────────┘
```

### 핵심 레이아웃 원칙
1. **차트는 앞쪽**, **DataGrid는 뒤쪽**에 배치 (동일 계열 묶음)
2. 각 DataGrid 섹션은 **A4 용지 기준으로 자동 페이지 분할**
3. 하나의 Paper에 ~22행 (첫 페이지 20행, 계속 페이지 24행)
4. 계속 페이지는 `"7. 이벤트 상세 (계속)"` 형태의 제목 + thead 반복

---

## 3. Gap Analysis: 치명적 버그 (Critical Bugs)

### BUG-1: DetectionEvent 필드명 오류

**파일:** `app/services/report_service.py:262`
```python
# CURRENT (BUG):
e.type_detection or "",

# CORRECT:
e.result.value if hasattr(e.result, 'value') else str(e.result) if e.result else "",
```

**원인:** `DetectionEvent` 모델에는 `type_detection` 필드가 존재하지 않음. 실제 필드명은 `result` (EnumDetectionType).

**영향:** `get_detection_grid_data()` 호출 시 `AttributeError` 발생 → 보고서 생성 FAILED.

---

### BUG-2: MalfunctionEvent 필드명 오류

**파일:** `app/services/report_service.py:284`
```python
# CURRENT (BUG):
e.type_fault or "",

# CORRECT:
e.reason.value if hasattr(e.reason, 'value') else str(e.reason) if e.reason else "",
```

**원인:** `MalfunctionEvent` 모델에는 `type_fault` 필드가 존재하지 않음. 실제 필드명은 `reason` (EnumFaultType).

**영향:** `get_malfunction_grid_data()` 호출 시 `AttributeError` 발생 → 보고서 생성 FAILED.

---

### BUG-3: DetectionEvent에 `zone` 필드 없음

**파일:** `app/services/report_service.py:263`
```python
# CURRENT (BUG):
getattr(e, 'zone', "") or "",

# NOTE:
# DetectionEvent에는 zone 필드가 없음. getattr 사용으로 에러는 안 나지만 항상 "" 반환.
# mockup 기준으로는 장비유형(device.type_device)과 장비명(device.name_device)이 필요.
```

---

### BUG-4: Event 통계 그룹핑 불일치

**파일:** `app/services/report_service.py:84-91`
```python
# CURRENT:
self.db.query(Event.type_event, func.count(Event.id))
    .filter(Event.type_event.notin_(excluded_types))
    .group_by(Event.type_event)
```

**문제:** `type_event`은 이벤트의 상세 유형 문자열이고, mockup이 필요로 하는 것은 **category_event** (detection/malfunction) 기준 집계.

**mockup 기대값:**
```json
{"탐지(Detection)": 120, "장애(Malfunction)": 3, "조치(Action)": 5}
```

**현재 반환값 예시:**
```json
{"Intrusion": 15, "Fault": 3}  // type_event 값 기반
```

---

## 4. Gap Analysis: 데이터 구조 차이

### GAP-1: 요약 섹션 - 장비 카드 데이터 부재

**mockup 요구:**
```
Controller: 2/2 (정상/전체) [all-normal]
Sensor:     4/5 (정상/전체) [has-issue]
Camera:     3/3
Speaker:    1/2 [has-issue]
Enclosure:  1/1
Lamp:       1/1
```

**현재 서비스 제공:**
```python
get_device_statistics() → {
    "status_counts": {"ACTIVATED": 12, "ERROR": 1, "DEACTIVATED": 1},
    "type_counts": {"controller": 2, "sensor": 5, ...}
}
```

**Gap:** 카테고리별 정상(ACTIVATED) 수 / 전체 수를 제공하지 않음.

**필요한 신규 쿼리:**
```python
def get_device_category_summary(self) -> List[Dict]:
    """카테고리별 장비 정상/전체 현황"""
    results = (
        self.db.query(
            Device.category_device,
            func.count(Device.id).label('total'),
            func.count(case((Device.status == 'ACTIVATED', 1))).label('normal')
        )
        .group_by(Device.category_device)
        .all()
    )
    return [
        {
            "category": r.category_device.value,
            "total": r.total,
            "normal": r.normal,
            "status": "all-normal" if r.normal == r.total else "has-issue"
        }
        for r in results
    ]
```

---

### GAP-2: 요약 섹션 - 이벤트 카드 데이터 부재

**mockup 요구:**
```
탐지:     120건 (detection card, blue gradient)
장애:     3건  (malfunction card, red gradient)
조치보고:  5건  (action card, purple gradient)
```

**현재 서비스:**
`event_type_counts`는 `type_event` 기준 집계 (잘못된 그룹핑, BUG-4 참조)

**필요한 신규 쿼리:**
```python
def get_event_category_counts(self, days: int = 7) -> Dict[str, int]:
    """이벤트 카테고리별 건수"""
    start_date = datetime.now() - timedelta(days=days)

    detection_count = self.db.query(func.count(DetectionEvent.id)).filter(
        DetectionEvent.created_at >= start_date
    ).scalar() or 0

    malfunction_count = self.db.query(func.count(MalfunctionEvent.id)).filter(
        MalfunctionEvent.created_at >= start_date
    ).scalar() or 0

    action_count = self.db.query(func.count(ActionEvent.id)).filter(
        ActionEvent.created_at >= start_date
    ).scalar() or 0

    return {
        "detection": detection_count,
        "malfunction": malfunction_count,
        "action": action_count
    }
```

---

### GAP-3: 요약 섹션 - 서버 상태 카드 부재

**mockup 요구:**
```
VMS 서버:       정상(green), 2대
AI 분석 서버:    주의(yellow), 3대
스트리밍 서버:   정상(green), 2대
브로커 서버:     오류(red), 2대
DB API 서버:    정상(green), 1대
```

**현재 서비스:** 서버/시스템 통계가 전혀 없음. `get_system_statistics()`는 SystemEvent의 severity 집계만 제공.

**필요한 신규 쿼리:**
```python
def get_server_status_summary(self) -> List[Dict]:
    """서버 카테고리별 상태 요약"""
    from app.models.server import ServerCategory, Server

    categories = self.db.query(ServerCategory).order_by(ServerCategory.sort_order).all()
    result = []
    for cat in categories:
        servers = self.db.query(Server).filter(Server.category_id == cat.id).all()
        worst_status = "normal"
        for s in servers:
            if s.status and s.status.value == "ERROR":
                worst_status = "error"
                break
            elif s.status and s.status.value == "WARNING" and worst_status != "error":
                worst_status = "warning"
        result.append({
            "name": cat.name,
            "status": worst_status,
            "count": len(servers)
        })
    return result
```

---

### GAP-4: 이벤트 추이 LINE - 유형별 분리 필요

**mockup 요구 (3개 데이터셋):**
```javascript
datasets: [
    { label: '탐지', data: [10,14,12,18,22,20,16,8] },
    { label: '장애', data: [0,1,0,1,0,0,1,0] },
    { label: '조치', data: [0,1,0,1,1,1,1,0] }
]
```

**현재 서비스:**
```python
# 전체 이벤트 합산 추이만 제공 (유형 미분리)
daily_query = self.db.query(
    func.date(Event.created_at), func.count(Event.id)
).filter(Event.type_event.notin_(excluded_types))...
```

**필요한 수정:** 카테고리별 일별 추이를 각각 쿼리하여 3개 데이터셋 반환

---

### GAP-5: 탐지 이벤트 Grid 컬럼 불일치

| # | Mockup Column | Current Column | Gap |
|---|---------------|----------------|-----|
| 1 | ID | ID | OK |
| 2 | 일시 | 일시 | OK |
| 3 | **탐지유형** | **탐지유형** | **BUG**: `e.type_detection` → `e.result` |
| 4 | **장비유형** | **존** | **MISSING**: Device JOIN 필요 |
| 5 | **장비명** | **장비ID** | **MISSING**: Device JOIN 필요 |
| 6 | **조치보고일자** | (없음) | **MISSING**: ActionEvent JOIN 필요 |
| 7 | **조치자** | (없음) | **MISSING**: ActionEvent JOIN 필요 |
| 8 | **조치내용** | (없음) | **MISSING**: ActionEvent JOIN 필요 |

**필요한 수정:** `get_detection_grid_data()`를 Device, ActionEvent와 JOIN하도록 재작성

```python
def get_detection_grid_data(self, days: int = 7) -> Dict[str, Any]:
    columns = ["ID", "일시", "탐지유형", "장비유형", "장비명",
               "조치보고일자", "조치자", "조치내용"]
    start_date = datetime.now() - timedelta(days=days)

    events = (
        self.db.query(DetectionEvent)
        .outerjoin(Device, DetectionEvent.device_id == Device.id)
        .filter(DetectionEvent.created_at >= start_date)
        .order_by(DetectionEvent.created_at.desc())
        .all()
    )
    rows = []
    for e in events:
        # ActionEvent 조회
        action = self.db.query(ActionEvent).filter(
            ActionEvent.from_event_id == e.id
        ).first()

        rows.append([
            e.id,
            e.created_at.strftime('%Y-%m-%d %H:%M:%S') if e.created_at else "",
            e.result.value if e.result else "",
            e.device.type_device.value if e.device and e.device.type_device else "",
            e.device.name_device if e.device else "",
            action.created_at.strftime('%Y-%m-%d %H:%M:%S') if action else "-",
            action.user if action else "-",
            action.content if action else "-",
        ])
    return {"columns": columns, "rows": rows, "total_rows": len(rows)}
```

---

### GAP-6: 장애 이벤트 Grid 컬럼 불일치

| # | Mockup Column | Current Column | Gap |
|---|---------------|----------------|-----|
| 1 | ID | ID | OK |
| 2 | 일시 | 일시 | OK |
| 3 | **장애유형** | **장애유형** | **BUG**: `e.type_fault` → `e.reason` |
| 4 | **장비유형** | (없음) | **MISSING**: Device JOIN 필요 |
| 5 | **장비명** | **장비ID** | **MISSING**: Device JOIN 필요 |
| 6 | **조치보고일자** | (없음) | **MISSING**: ActionEvent JOIN 필요 |
| 7 | **조치자** | (없음) | **MISSING**: ActionEvent JOIN 필요 |
| 8 | **조치내용** | (없음) | **MISSING**: ActionEvent JOIN 필요 |

> **Note:** 장애 이벤트도 탐지 이벤트와 동일하게 조치보고(ActionEvent) 정보를 포함해야 한다.
> 탐지/장애 모두 `ActionEvent.from_event_id`로 연결되므로 동일한 JOIN 패턴 적용.

**필요한 수정:**
```python
def get_malfunction_grid_data(self, days: int = 7) -> Dict[str, Any]:
    columns = ["ID", "일시", "장애유형", "장비유형", "장비명",
               "조치보고일자", "조치자", "조치내용"]
    start_date = datetime.now() - timedelta(days=days)

    events = (
        self.db.query(MalfunctionEvent)
        .outerjoin(Device, MalfunctionEvent.device_id == Device.id)
        .filter(MalfunctionEvent.created_at >= start_date)
        .order_by(MalfunctionEvent.created_at.desc())
        .all()
    )
    rows = []
    for e in events:
        action = self.db.query(ActionEvent).filter(
            ActionEvent.from_event_id == e.id
        ).first()
        rows.append([
            e.id,
            e.created_at.strftime('%Y-%m-%d %H:%M:%S') if e.created_at else "",
            e.reason.value if e.reason else "",
            e.device.type_device.value if e.device and e.device.type_device else "",
            e.device.name_device if e.device else "",
            action.created_at.strftime('%Y-%m-%d %H:%M:%S') if action else "-",
            action.user if action else "-",
            action.content if action else "-",
        ])
    return {"columns": columns, "rows": rows, "total_rows": len(rows)}
```

---

### GAP-7: 장비 Grid 컬럼 불일치

| # | Mockup Column | Current Column | Gap |
|---|---------------|----------------|-----|
| 1 | ID | ID | OK |
| 2 | **장비명** | **유형** | 순서 다름 |
| 3 | **장비유형** | **이름** | 순서 다름 |
| 4 | **버전** | **상태** | `version` 필드 미포함 |
| 5 | **상태** | **IP** | 순서 다름 |
| 6 | **활성** | (없음) | `is_enable` 필드 미포함 |

**필요한 수정:**
```python
columns = ["ID", "장비명", "장비유형", "버전", "상태", "활성"]
rows.append([
    d.id,
    d.name_device or "",
    d.type_device.value if d.type_device else d.category_device.value,
    d.version or "",
    d.status.value if hasattr(d.status, 'value') else str(d.status),
    str(d.is_enable),
])
```

---

## 5. Gap Analysis: Template (preview.html) 구조 차이

### GAP-8: Cover Page 부재

**현재:** header div에 제목/기간/생성자/다운로드 버튼만 표시
**mockup:** 독립적인 Cover Page (로고, 제목, 부제, 기간, 생성자 정보, 11항목 TOC)

---

### GAP-9: A4 Paper 레이아웃 부재

**현재:** 단일 페이지 연속 스크롤
**mockup:** `.paper` div로 A4 크기 분리, gray 배경에 white paper cards, print 시 page-break

필요한 CSS:
```css
.paper {
    width: 210mm;
    min-height: 297mm;
    margin: 0 auto 30px auto;
    padding: 15mm;
    background: white;
    box-shadow: 0 4px 24px rgba(0,0,0,0.15);
}
@media print {
    .paper { page-break-after: always; }
}
```

---

### GAP-10: 섹션 분리 방식 차이

**현재 서비스:** 5개 섹션 (요약/장비/이벤트/시스템/사용자), 각 섹션에 차트+그리드 혼합
**mockup:** 11개 섹션, **차트(2~5)와 그리드(6~11) 분리**

```
현재 구조:                    목표 구조:
섹션 1: 요약                   섹션 1: 요약 (카드)
섹션 2: 장비 [차트+그리드]       섹션 2: 장비 현황 [차트만]
섹션 3: 이벤트 [차트+그리드]     섹션 3: 이벤트 현황 [차트만]
섹션 4: 시스템 [차트+그리드]     섹션 4: 시스템 현황 [차트만]
섹션 5: 사용자 [차트+그리드]     섹션 5: 사용자 현황 [차트만]
                              섹션 6: 장비 목록 [그리드]
                              섹션 7: 이벤트 상세 [그리드]
                              섹션 8: 시스템 이벤트 [그리드]
                              섹션 9: 설정 변경 이력 [그리드]
                              섹션 10: 감사 로그 [그리드]
                              섹션 11: 사용자 상세 [그리드]
```

---

### GAP-11: 요약 카드 구조 완전 상이

**현재 template:**
```html
<!-- 단순한 gradient card에 숫자 3개 -->
<div class="summary-card">
    <div class="value">{{ chart.data.device_count }}</div>
    <div class="label">총 장비 수</div>
</div>
```

**mockup 요구:**
```html
<!-- 3개 카테고리 (장비/이벤트/서버), 각각 다른 카드 유형 -->

<!-- 장비: 6종류 device-card with icon, normal/total count, status -->
<div class="device-card all-normal">
    <div class="icon">🖥️</div>
    <div class="name">Controller</div>
    <div class="count">
        <span class="normal">2</span>/<span class="total">2</span>
    </div>
</div>

<!-- 이벤트: 3종류 event-card with gradient background -->
<div class="event-card detection">
    <div class="event-count">120 <span class="event-unit">건</span></div>
</div>

<!-- 서버: N개 server-card with status dot -->
<div class="server-card">
    <div class="server-status normal"><span class="status-dot green"></span> 정상</div>
    <div class="server-count">2 <span class="server-count-label">대</span></div>
</div>
```

---

### GAP-12: DataGrid 자동 페이지 분할 (Auto-Pagination) 부재

**현재 template:** 그리드를 10행으로 잘라서 표시 (`grid.rows[:10]`)
**mockup:** 전체 데이터를 표시하되, A4 넘침 시 자동으로 여러 paper로 분할

mockup의 JS pagination 로직:
- 첫 페이지 20행, 계속 페이지 24행
- 계속 페이지에 `"(계속)"` 제목 + thead 반복
- 다른 grid-section은 마지막 페이지에 이동

---

## 6. Gap Analysis: PDF 생성 차이

### GAP-13: PDF에 Cover Page / TOC 없음

**현재:** 제목+기간 텍스트만 상단에 배치
**mockup:** 별도 cover page + TOC 필요

### GAP-14: PDF 섹션 구성이 flat

**현재:** 모든 차트와 테이블이 순차적으로 나열됨 (차트/그리드 분리 없음)
**mockup:** 차트 영역 → 그리드 영역 순서로 구분

### GAP-15: PDF 테이블 페이지 분할 미구현

**현재:** ReportLab `Table`은 기본적으로 페이지를 넘기지만, 헤더 반복이나 제목 반복 없음
**필요:** `repeatRows=1` 옵션으로 thead 반복 + 섹션 제목 반복 로직

---

## 7. Gap Analysis: 데이터 Enum 매핑

### GAP-16: 장비 상태 Pie Chart

**mockup:**
```javascript
labels: ['ACTIVATED', 'DEACTIVATED', 'ERROR']
data: [12, 1, 1]
colors: ['#4CAF50', '#9E9E9E', '#F44336']
```

**현재 서비스:**
```python
# status_counts의 key가 Enum 객체일 수 있음 (string 변환 미확인)
status_counts[status] = count  # status가 EnumDeviceStatus enum 객체
```

**문제:** `device_stats["status_counts"]`의 키가 Enum 객체(`EnumDeviceStatus.ACTIVATED`)인 경우, JSON 직렬화 시 문제 발생 가능. Enum `.value` 변환 필요.

### GAP-17: 장비 유형 Bar Chart

**mockup:**
```javascript
labels: ['Controller', 'Sensor', 'Camera', 'Speaker', 'Enclosure', 'Lamp']
```

**현재 서비스:**
```python
# category_device 기준 집계 → key가 "controller", "sensor" 등 소문자
type_counts[category.value] = count
```

**문제:** mockup은 `Controller` (PascalCase), 서비스는 `controller` (lowercase). 프론트에서 매핑하거나 서비스에서 capitalize 필요.

실제 `EnumDeviceType` 값 (`Controller`, `Multi`, `Fence`, `PIR` 등)과 `EnumDeviceCategory` 값 (`controller`, `sensor`, `camera` 등) 중 어떤 것을 사용할지 결정 필요.

mockup은 **category** 기준 (Controller, Sensor, Camera, Speaker, Enclosure, Lamp).

---

## 8. 수정 우선순위 및 작업 목록

### Phase 1: Critical Bug Fix (보고서 생성 실패 방지)

| # | Task | File | Priority |
|---|------|------|----------|
| 1 | BUG-1: `type_detection` → `result` | report_service.py:262 | **P0** |
| 2 | BUG-2: `type_fault` → `reason` | report_service.py:284 | **P0** |
| 3 | BUG-4: Event 통계를 category_event 기준으로 변경 | report_service.py:84-91 | **P0** |

### Phase 2: Service Data 보강 (mockup 데이터 구조 맞춤)

| # | Task | GAP | Priority |
|---|------|-----|----------|
| 4 | 장비 카테고리별 정상/전체 카운트 쿼리 추가 | GAP-1 | **P1** |
| 5 | 이벤트 카테고리별 카운트 쿼리 추가 | GAP-2 | **P1** |
| 6 | 서버 카테고리별 상태 요약 쿼리 추가 | GAP-3 | **P1** |
| 7 | 이벤트 추이를 유형별 분리 (3 datasets) | GAP-4 | **P1** |
| 8 | 탐지 이벤트 Grid: Device+Action JOIN | GAP-5 | **P1** |
| 9 | 장애 이벤트 Grid: Device JOIN, reason 필드 | GAP-6 | **P1** |
| 10 | 장비 Grid: 컬럼 순서/버전/활성 추가 | GAP-7 | **P1** |
| 11 | Enum key 직렬화 (status, category) | GAP-16,17 | **P1** |

### Phase 3: get_structured_preview_data() 재구성

| # | Task | GAP | Priority |
|---|------|-----|----------|
| 12 | 11개 섹션 구조로 변경 (차트/그리드 분리) | GAP-10 | **P2** |
| 13 | 요약 섹션에 카테고리별 카드 데이터 포함 | GAP-1,2,3 | **P2** |
| 14 | Structured data schema 업데이트 | - | **P2** |

### Phase 4: Jinja2 Template 재작성

| # | Task | GAP | Priority |
|---|------|-----|----------|
| 15 | Cover Page + TOC 추가 | GAP-8 | **P2** |
| 16 | A4 Paper 레이아웃 CSS | GAP-9 | **P2** |
| 17 | 요약 카드 3종 (장비/이벤트/서버) | GAP-11 | **P2** |
| 18 | 차트 섹션 렌더링 (Chart.js) | GAP-10 | **P2** |
| 19 | DataGrid 자동 페이지 분할 JS | GAP-12 | **P2** |
| 20 | Print CSS (@media print) | GAP-9 | **P2** |

### Phase 5: PDF Generator 개선

| # | Task | GAP | Priority |
|---|------|-----|----------|
| 21 | Cover Page + TOC 생성 | GAP-13 | **P3** |
| 22 | 차트→그리드 순서 정렬 | GAP-14 | **P3** |
| 23 | 테이블 페이지 분할 (repeatRows) | GAP-15 | **P3** |
| 24 | 한글 폰트 지원 (현재 미확인) | - | **P3** |

---

## 9. get_structured_preview_data() 목표 반환 구조

```python
{
    "sections": [
        # ─── 1. 요약 ───
        {
            "name": "summary",
            "title": "1. 요약",
            "summary_data": {
                "device_categories": [
                    {"category": "controller", "icon": "🖥️", "label": "Controller",
                     "normal": 2, "total": 2, "status": "all-normal"},
                    {"category": "sensor", "icon": "📡", "label": "Sensor",
                     "normal": 4, "total": 5, "status": "has-issue"},
                    # ... (6종)
                ],
                "event_counts": {
                    "detection": 120,
                    "malfunction": 3,
                    "action": 5
                },
                "server_status": [
                    {"name": "VMS 서버", "status": "normal", "count": 2},
                    {"name": "AI 분석 서버", "status": "warning", "count": 3},
                    # ...
                ]
            },
            "charts": [],
            "grids": []
        },

        # ─── 2. 장비 현황 (Charts Only) ───
        {
            "name": "device_charts",
            "title": "2. 장비 현황",
            "charts": [
                {
                    "id": "DEVICE_STATUS_PIE", "title": "장비 상태 분포",
                    "type": "PIE",
                    "data": {
                        "labels": ["ACTIVATED", "DEACTIVATED", "ERROR"],
                        "values": [12, 1, 1],
                        "colors": ["#4CAF50", "#9E9E9E", "#F44336"]
                    }
                },
                {
                    "id": "DEVICE_TYPE_BAR", "title": "유형별 장비 현황",
                    "type": "BAR",
                    "data": {
                        "labels": ["Controller", "Sensor", "Camera", "Speaker", "Enclosure", "Lamp"],
                        "values": [2, 5, 3, 2, 1, 1]
                    }
                }
            ],
            "grids": []
        },

        # ─── 3. 이벤트 현황 (Charts Only) ───
        {
            "name": "event_charts",
            "title": "3. 이벤트 현황",
            "charts": [
                {
                    "id": "EVENT_SUMMARY_PIE", "title": "이벤트 유형 분포",
                    "type": "PIE",
                    "data": {
                        "labels": ["탐지(Detection)", "장애(Malfunction)", "조치(Action)"],
                        "values": [120, 3, 5]
                    }
                },
                {
                    "id": "EVENT_TREND_LINE", "title": "이벤트 발생 추이",
                    "type": "LINE",
                    "data": {
                        "labels": ["01-26", "01-27", ...],
                        "datasets": [
                            {"label": "탐지", "values": [10, 14, 12, ...], "color": "#3b82f6"},
                            {"label": "장애", "values": [0, 1, 0, ...], "color": "#ef4444"},
                            {"label": "조치", "values": [0, 1, 0, ...], "color": "#8b5cf6"}
                        ]
                    }
                }
            ],
            "grids": []
        },

        # ─── 4. 시스템 현황 (Charts Only) ───
        {
            "name": "system_charts",
            "title": "4. 시스템 현황",
            "charts": [
                {"id": "SYSTEM_SEVERITY_BAR", "type": "BAR", ...},
                {"id": "SYSTEM_TREND_LINE", "type": "LINE", ...}
            ],
            "grids": []
        },

        # ─── 5. 사용자 현황 (Charts Only) ───
        {
            "name": "user_charts",
            "title": "5. 사용자 현황",
            "charts": [
                {"id": "USER_ROLE_PIE", "type": "PIE", ...},
                {"id": "USER_LOGIN_TREND_LINE", "type": "LINE", ...},
                {"id": "USER_LOGIN_RESULT_PIE", "type": "PIE", ...}
            ],
            "grids": []
        },

        # ─── 6. 장비 목록 (Grid Only) ───
        {
            "name": "device_grid",
            "title": "6. 장비 목록",
            "charts": [],
            "grids": [{
                "id": "DEVICE_GRID", "title": "장비 목록",
                "columns": ["ID", "장비명", "장비유형", "버전", "상태", "활성"],
                "rows": [...],
                "total_rows": 14
            }]
        },

        # ─── 7. 이벤트 상세 (Grids Only) ───
        {
            "name": "event_grids",
            "title": "7. 이벤트 상세",
            "charts": [],
            "grids": [
                {
                    "id": "EVENT_DETECTION_GRID",
                    "title": "탐지 이벤트 목록",
                    "columns": ["ID", "일시", "탐지유형", "장비유형", "장비명",
                                "조치보고일자", "조치자", "조치내용"],
                    "rows": [...],
                    "total_rows": 120
                },
                {
                    "id": "EVENT_MALFUNCTION_GRID",
                    "title": "장애 이벤트 목록",
                    "columns": ["ID", "일시", "장애유형", "장비유형", "장비명",
                                "조치보고일자", "조치자", "조치내용"],
                    "rows": [...],
                    "total_rows": 3
                }
            ]
        },

        # ─── 8~10. 시스템 관련 Grids ───
        # 8: 시스템 이벤트 (SYSTEM_EVENT_GRID)
        # 9: 설정 변경 이력 (SYSTEM_CONFIG_GRID)
        # 10: 감사 로그 (SYSTEM_AUDIT_GRID)

        # ─── 11. 사용자 상세 (Grids) ───
        {
            "name": "user_grids",
            "title": "11. 사용자 상세",
            "charts": [],
            "grids": [
                {"id": "USER_GRID", ...},
                {"id": "USER_LOGIN_GRID", ...},
                {"id": "USER_SESSION_GRID", ...}
            ]
        }
    ]
}
```

---

## 10. Schema 변경 필요사항

### 10.1 ChartData - LINE 차트용 datasets 지원 필요

**현재:**
```python
class ChartData(BaseModel):
    labels: List[str]
    values: List[Any]  # 단일 데이터셋만 지원
    colors: Optional[List[str]] = None
```

**필요:**
```python
class ChartDataset(BaseModel):
    label: str
    values: List[Any]
    color: Optional[str] = None

class ChartData(BaseModel):
    labels: List[str]
    values: Optional[List[Any]] = None           # PIE/BAR 단일 데이터셋
    datasets: Optional[List[ChartDataset]] = None # LINE 다중 데이터셋
    colors: Optional[List[str]] = None
```

### 10.2 ReportSection - summary_data 추가 필요

```python
class ReportSection(BaseModel):
    name: str
    title: str
    charts: List[ChartConfig] = []
    grids: List[GridConfig] = []
    summary_data: Optional[Dict[str, Any]] = None  # 요약 섹션용
```

---

## 11. Jinja2 Template 재작성 가이드

### 11.1 Template 구조 (목표)

```html
<!-- Cover Page (paper 1) -->
<div class="paper">
    <div class="cover">
        <div class="cover-top">title, period, info</div>
        <div class="toc">목차</div>
    </div>
</div>

<!-- 1. 요약 (paper 2) -->
<div class="paper">
    {% include "reports/_summary_cards.html" %}
</div>

<!-- 2~4. 차트 묶음 (paper 3) -->
<div class="paper">
    {% for section in chart_sections %}
        <div class="section">
            <div class="section-title">{{ section.title }}</div>
            <div class="charts-row">
                {% for chart in section.charts %}
                    <div class="chart-box">
                        <canvas id="chart-{{ chart.id }}"></canvas>
                    </div>
                {% endfor %}
            </div>
        </div>
    {% endfor %}
</div>

<!-- 5. 사용자 현황 (paper 4) -->
<!-- ... -->

<!-- 6~11. DataGrid sections (paper 5+) -->
{% for section in grid_sections %}
<div class="paper">
    <div class="section">
        <div class="section-title">{{ section.title }}</div>
        {% for grid in section.grids %}
            <div class="grid-section">
                <h4>{{ grid.title }} <span class="badge">{{ grid.total_rows }}건</span></h4>
                <table>
                    <thead><tr>{% for col in grid.columns %}<th>{{ col }}</th>{% endfor %}</tr></thead>
                    <tbody id="grid-{{ grid.id }}">
                        {% for row in grid.rows %}
                        <tr>{% for cell in row %}<td>{{ cell }}</td>{% endfor %}</tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        {% endfor %}
    </div>
</div>
{% endfor %}

<!-- Auto-pagination JS -->
<script>/* pagination logic from mockup */</script>
```

### 11.2 Chart.js 초기화 패턴

```javascript
// Template에서 section.charts 데이터를 JSON으로 변환하여 전달
var chartConfigs = {{ chart_configs | tojson | safe }};

chartConfigs.forEach(function(cfg) {
    var type = cfg.type.toLowerCase();
    var data;

    if (cfg.data.datasets) {
        // LINE chart with multiple datasets
        data = {
            labels: cfg.data.labels,
            datasets: cfg.data.datasets.map(function(ds, i) {
                return {
                    label: ds.label,
                    data: ds.values,
                    borderColor: ds.color,
                    fill: type === 'line',
                    tension: 0.3
                };
            })
        };
    } else {
        // PIE/BAR with single dataset
        data = {
            labels: cfg.data.labels,
            datasets: [{ data: cfg.data.values, backgroundColor: cfg.data.colors || defaultColors }]
        };
    }

    new Chart(document.getElementById('chart-' + cfg.id), {
        type: type, data: data, options: { responsive: true, maintainAspectRatio: false }
    });
});
```

---

## 12. 디버깅 체크리스트

### 12.1 서버 기동 후 확인사항

```bash
# 1. DB 초기화 확인
# → init_report_data.py에서 5개 템플릿 생성됐는지 확인
GET /api/reports/templates

# 2. 보고서 생성 요청
POST /api/reports/generate
{
    "report_type": "STANDARD",
    "title": "주간 현황보고",
    "period_type": "7d"
}

# 3. 생성 상태 확인 (COMPLETED 될 때까지)
GET /api/reports/generations/{id}

# 4. 미리보기 데이터 확인 (JSON)
GET /api/reports/generations/{id}/preview

# 5. HTML 미리보기 확인
GET /reports/preview/{id}

# 6. PDF 다운로드
GET /api/reports/generations/{id}/download
```

### 12.2 예상되는 에러 시나리오

| Step | Error | Cause | Fix |
|------|-------|-------|-----|
| 3 | status=FAILED | BUG-1 or BUG-2 | Phase 1 수정 |
| 3 | status=FAILED | `AttributeError: 'NoneType'` | Device가 삭제된 경우 FK null |
| 4 | Empty sections | `event_type_counts = {}` | DB에 이벤트 데이터 없음 |
| 5 | Template render error | Jinja2 변수 미정의 | Template 변수와 context 불일치 |
| 6 | 404 PDF not found | `reports/` 디렉토리 미생성 | `os.makedirs` 권한 문제 |
| 6 | 한글 깨짐 | ReportLab 한글 폰트 미등록 | TTFont 등록 필요 |

### 12.3 데이터 존재 여부 확인 쿼리

```sql
-- 장비 데이터
SELECT category_device, status, COUNT(*) FROM devices GROUP BY category_device, status;

-- 이벤트 데이터
SELECT category_event, COUNT(*) FROM events GROUP BY category_event;

-- 탐지 이벤트
SELECT result, COUNT(*) FROM detection_events GROUP BY result;

-- 시스템 이벤트
SELECT severity, COUNT(*) FROM system_events GROUP BY severity;

-- 설정 변경
SELECT resource_type, action, COUNT(*) FROM config_change_logs GROUP BY resource_type, action;

-- 감사 로그
SELECT action_type, action_status, COUNT(*) FROM audit_logs GROUP BY action_type, action_status;

-- 사용자
SELECT role, COUNT(*) FROM account_users GROUP BY role;

-- 서버
SELECT sc.name, s.status, COUNT(*) FROM servers s
JOIN server_categories sc ON s.category_id = sc.id
GROUP BY sc.name, s.status;
```

---

## 13. 참고: 현재 DB에 필요한 테스트 데이터

mockup 수준의 보고서를 생성하려면 다음 데이터가 DB에 존재해야 한다:

| Table | Required Count | Notes |
|-------|---------------|-------|
| devices | 14건 | 6종 카테고리 |
| detection_events | 120건+ | result: THERMAL_SENSOR, PIR_SENSOR 등 |
| malfunction_events | 3건+ | reason: SENSOR_FAULT, COMMUNICATION_ERROR 등 |
| action_events | 5건+ | from_event_id로 detection과 연결 |
| system_events | 10건+ | 4종 severity |
| config_change_logs | 100건+ | resource_type, action 다양하게 |
| audit_logs | 12건+ | action_type, resource_type 다양하게 |
| account_users | 4건+ | 3종 role |
| user_login_logs | 7건+ | SUCCESS/FAILURE 포함 |
| user_sessions | 3건+ | - |
| server_categories | 5건 | VMS, AI, Streaming, Broker, DB API |
| servers | 10건+ | 카테고리별 분배 |

---

## 14. 요약: 작업 로드맵

```
Phase 1 (Bug Fix) ──→ Phase 2 (Data Query) ──→ Phase 3 (Service Restructure)
     P0 긴급              P1 핵심                  P2 구조 변경
     3건                  8건                     3건

                    ──→ Phase 4 (Template Rewrite) ──→ Phase 5 (PDF Improvement)
                           P2 UI                         P3 개선
                           6건                          4건
```

**총 24건** 작업 항목, 이 중 **P0 (3건)** 은 현재 보고서 생성 자체가 실패하는 원인이므로 즉시 수정 필요.
