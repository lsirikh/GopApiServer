# PRD: 보고서 PDF ↔ Preview 데이터 동기화

**문서 버전**: 1.0
**작성일**: 2026-02-12
**상태**: Draft

---

## 1. 문제 정의

`GET /api/reports/generations/{id}/preview` (Preview)와 `GET /api/reports/generations/{id}/download` (PDF)의 **콘텐츠가 크게 다르다**.

Preview는 11개 섹션(9개 차트 + 14개 그리드)을 제공하지만, PDF는 4개 차트 + 10개 테이블만 포함. 또한 Enum 값이 `EnumDeviceStatus.ACTIVATED`처럼 클래스 표현으로 출력되어 데이터가 깨진다.

---

## 2. 근본 원인 분석

### 2.1 BUG: Enum `.value` 변환 누락 (3건)

SQLAlchemy `group_by` 쿼리 결과에서 Enum 객체를 dict 키나 테이블 셀에 **그대로 사용**하여, `str()`호출 시 `EnumClassName.VALUE` 형태로 출력됨.

| # | 위치 | 코드 | 출력 | 기대값 |
|---|------|------|------|--------|
| 1 | `report_service.py:90` | `status_counts[status] = count` | `EnumDeviceStatus.ACTIVATED` | `ACTIVATED` |
| 2 | `report_service.py:502` | `log.resource_type or ""` | `EnumConfigResourceType.EVENT_MAPPING_CAMERA` | `EVENT_MAPPING_CAMERA` |
| 3 | `report_service.py:503` | `log.action or ""` | `EnumConfigActionType.CREATED` | `CREATED` |

**참고 — 이미 올바르게 변환된 코드:**
- `report_service.py:101` — `type_counts[category.value if hasattr(category, 'value') else category]` ✅
- `report_service.py:277` — `severity.value if hasattr(severity, 'value') else severity` ✅

**추가 잠재 Enum 미변환 (Preview 전용 — PDF에서 차트 미구현이므로 현재 미노출):**
- `report_service.py:327` — `role_counts[role] = count` (role은 Enum 객체)
- `report_service.py:356` — `login_result_counts[result] = count` (result은 Enum 객체)

→ 차트 5건 추가 시 함께 수정 필요.

### 2.2 GAP: PDF 누락 차트 5건

`generate_report_async()`에서 4개 차트만 생성. Preview에 존재하는 5개 차트가 PDF에 미구현:

| # | Component ID | Preview 섹션 | 차트 유형 | 데이터 소스 |
|---|---|---|---|---|
| 1 | `EVENT_TREND_LINE` | 3. 이벤트 현황 | LINE | `event_stats["daily_trend"]` + `event_stats["daily_labels"]` |
| 2 | `SYSTEM_TREND_LINE` | 4. 시스템 현황 | LINE | `system_stats["daily_trend"]` (date, count) |
| 3 | `USER_ROLE_PIE` | 5. 사용자 현황 | PIE | `user_stats["role_counts"]` |
| 4 | `USER_LOGIN_TREND_LINE` | 5. 사용자 현황 | LINE | `user_stats["login_daily_trend"]` (date, count) |
| 5 | `USER_LOGIN_RESULT_PIE` | 5. 사용자 현황 | PIE | `user_stats["login_result_counts"]` |

**ChartGenerator 현황:**
- `generate_pie_chart()` — 사용 가능 (PIE)
- `generate_bar_chart()` — 사용 가능 (BAR)
- `generate_line_chart()` — 사용 가능 (LINE, `labels` + `datasets[{"label", "data"}]` 형식)
- `generate_donut_chart()` — 사용 가능 (DONUT)

### 2.3 BUG: 요약 텍스트 줄바꿈 미작동

`generate_report_async()` line 1043-1050에서 `\n`을 사용하지만, reportlab `Paragraph`는 `\n`을 무시하고 한 줄로 출력.

**현재 출력:**
```
보고서 기간: 2026-02-05 ~ 2026-02-12 총 장비 수: 4대 총 이벤트 수: 19건 총 시스템 이벤트 수: 30건 총 사용자 수: 6명
```

**기대 출력:**
```
보고서 기간: 2026-02-05 ~ 2026-02-12
총 장비 수: 4대
총 이벤트 수: 19건
총 시스템 이벤트 수: 30건
총 사용자 수: 6명
```

**수정**: `\n` → `<br/>` 변환.

### 2.4 BUG: 테이블 페이지 오버플로

reportlab `Table`에 `colWidths` 미지정. A4 가용 폭(170mm = 약 482pt)에서:

| 테이블 | 컬럼 수 | 문제 |
|--------|---------|------|
| 탐지 이벤트 | 8 | "조치내용" 컬럼 잘림 |
| 장애 이벤트 | 8 | 동일 |
| 설정 변경 이력 | 5 | Enum 전체 클래스명(50자+)으로 컬럼 초과 |

**수정**: `Table(data)` → `Table(data, colWidths=[...])` 또는 페이지 가용 폭 기반 자동 배분, 그리고 셀 내 `Paragraph` 워드랩 적용.

### 2.5 GAP: 섹션 번호 불일치

| 항목 | Preview | PDF |
|------|---------|-----|
| 섹션 번호 | 전 섹션 번호 (1~11) | "1. 요약"만 번호, 나머지 제목만 |

**수정**: PDF 섹션 제목에 순번 부여.

---

## 3. 수정 명세

### 3.1 Enum `.value` 변환 (report_service.py)

**대상 5건:**

```python
# BUG-1: get_device_statistics() line 90
# Before:
status_counts[status] = count
# After:
status_counts[status.value if hasattr(status, 'value') else status] = count

# BUG-2: get_config_grid_data() line 502
# Before:
log.resource_type or "",
# After:
log.resource_type.value if hasattr(log.resource_type, 'value') else str(log.resource_type) if log.resource_type else "",

# BUG-3: get_config_grid_data() line 503
# Before:
log.action or "",
# After:
log.action.value if hasattr(log.action, 'value') else str(log.action) if log.action else "",

# BUG-4: get_user_statistics() line 327
# Before:
role_counts[role] = count
# After:
role_counts[role.value if hasattr(role, 'value') else role] = count

# BUG-5: get_user_statistics() line 356
# Before:
login_result_counts[result] = count
# After:
login_result_counts[result.value if hasattr(result, 'value') else result] = count
```

**영향 범위**: Preview API 응답 + PDF 차트 라벨 + PDF 테이블 셀 모두 수정됨. Preview 측은 프론트엔드가 이미 `.value` 문자열을 기대하므로 호환성 문제 없음.

### 3.2 누락 차트 5건 추가 (generate_report_async)

`generate_report_async()`의 차트 생성 블록(line 999~1036)에 추가:

```python
# EVENT_TREND_LINE: 이벤트 발생 추이
if _is_enabled("EVENT_TREND_LINE") and event_stats.get("daily_labels"):
    datasets = [
        {"label": d["label"], "data": d["values"]}
        for d in event_stats["daily_trend"]
    ]
    event_trend = ChartGenerator.generate_line_chart(
        labels=event_stats["daily_labels"],
        datasets=datasets,
        title="이벤트 발생 추이",
        xlabel="날짜", ylabel="건수"
    )
    charts.append(("이벤트 발생 추이", event_trend))

# SYSTEM_TREND_LINE: 시스템 이벤트 추이
if _is_enabled("SYSTEM_TREND_LINE") and system_stats.get("daily_trend"):
    sys_labels = [d["date"] for d in system_stats["daily_trend"]]
    sys_values = [d["count"] for d in system_stats["daily_trend"]]
    system_trend = ChartGenerator.generate_line_chart(
        labels=sys_labels,
        datasets=[{"label": "시스템 이벤트", "data": sys_values}],
        title="시스템 이벤트 추이",
        xlabel="날짜", ylabel="건수"
    )
    charts.append(("시스템 이벤트 추이", system_trend))

# USER_ROLE_PIE: 역할별 사용자 분포
if _is_enabled("USER_ROLE_PIE") and user_stats["role_counts"]:
    role_pie = ChartGenerator.generate_pie_chart(
        data=user_stats["role_counts"],
        title="역할별 사용자 분포"
    )
    charts.append(("역할별 사용자 분포", role_pie))

# USER_LOGIN_TREND_LINE: 일별 로그인 추이
if _is_enabled("USER_LOGIN_TREND_LINE") and user_stats.get("login_daily_trend"):
    login_labels = [d["date"] for d in user_stats["login_daily_trend"]]
    login_values = [d["count"] for d in user_stats["login_daily_trend"]]
    login_trend = ChartGenerator.generate_line_chart(
        labels=login_labels,
        datasets=[{"label": "로그인", "data": login_values}],
        title="일별 로그인 추이",
        xlabel="날짜", ylabel="건수"
    )
    charts.append(("일별 로그인 추이", login_trend))

# USER_LOGIN_RESULT_PIE: 로그인 성공/실패 분포
if _is_enabled("USER_LOGIN_RESULT_PIE") and user_stats.get("login_result_counts"):
    login_result_pie = ChartGenerator.generate_pie_chart(
        data=user_stats["login_result_counts"],
        title="로그인 결과 분포"
    )
    charts.append(("로그인 결과 분포", login_result_pie))
```

**CHART_COMPONENT_MAP 업데이트** (report_service.py 상단 상수):

```python
CHART_COMPONENT_MAP = {
    "DEVICE_STATUS_PIE": "장비 상태 분포",
    "DEVICE_TYPE_BAR": "장비 유형별 현황",
    "EVENT_SUMMARY_PIE": "이벤트 유형 분포",
    "SYSTEM_SEVERITY_BAR": "시스템 이벤트 심각도",
    # 신규 5건
    "EVENT_TREND_LINE": "이벤트 발생 추이",
    "SYSTEM_TREND_LINE": "시스템 이벤트 추이",
    "USER_ROLE_PIE": "역할별 사용자 분포",
    "USER_LOGIN_TREND_LINE": "일별 로그인 추이",
    "USER_LOGIN_RESULT_PIE": "로그인 결과 분포",
}
```

### 3.3 요약 텍스트 줄바꿈 (generate_report_async)

```python
# Before (line 1043-1050):
"content": (
    f"보고서 기간: {generation.start_date.strftime('%Y-%m-%d')} ~ "
    f"{generation.end_date.strftime('%Y-%m-%d')}\n"
    f"총 장비 수: {sum(device_stats['type_counts'].values())}대\n"
    ...
)

# After:
"content": (
    f"보고서 기간: {generation.start_date.strftime('%Y-%m-%d')} ~ "
    f"{generation.end_date.strftime('%Y-%m-%d')}<br/>"
    f"총 장비 수: {sum(device_stats['type_counts'].values())}대<br/>"
    f"총 이벤트 수: {sum(event_stats['event_type_counts'].values())}건<br/>"
    f"총 시스템 이벤트 수: {sum(system_stats['severity_counts'].values())}건<br/>"
    f"총 사용자 수: {sum(user_stats['role_counts'].values())}명"
)
```

### 3.4 테이블 오버플로 수정 (pdf_generator.py)

`_build_table()` 메서드에서 A4 가용 폭 기반으로 `colWidths`를 자동 배분:

```python
@classmethod
def _build_table(cls, table_data: Dict[str, Any]) -> List:
    story = []
    headers = table_data.get('headers', [])
    rows = table_data.get('rows', [])
    data = [headers] + rows

    # A4 가용 폭 계산
    available_width = A4[0] - 2 * cls.PAGE_MARGIN
    col_count = len(headers)

    # 셀 내용을 Paragraph로 래핑 (워드랩 지원)
    cell_style = ParagraphStyle(
        'TableCell', fontName=cls.FONT_NAME, fontSize=8, leading=10
    )
    header_style = ParagraphStyle(
        'TableHeader', fontName=cls.FONT_NAME, fontSize=9,
        leading=11, textColor=colors.whitesmoke
    )

    wrapped_data = []
    for i, row in enumerate(data):
        style = header_style if i == 0 else cell_style
        wrapped_data.append([
            Paragraph(str(cell), style) for cell in row
        ])

    col_width = available_width / col_count
    table = Table(wrapped_data, colWidths=[col_width] * col_count)
    # ... (기존 TableStyle 유지)
```

### 3.5 섹션 번호 부여 (generate_report_async)

PDF 섹션 제목에 순번을 자동 부여:

```python
# 차트/테이블 섹션 추가 시 섹션 번호 카운터 사용
section_num = 2  # "1. 요약" 다음부터

for title, chart_image in charts:
    sections.append({
        "title": f"{section_num}. {title}",
        "chart_image": chart_image
    })
    section_num += 1

for table_title, grid_data in grid_tables:
    if grid_data and grid_data["rows"]:
        sections.append({
            "title": f"{section_num}. {table_title}",
            "table": { ... }
        })
        section_num += 1
```

---

## 4. 수정 대상 파일

| 파일 | 변경 내용 |
|------|----------|
| `app/services/report_service.py` | Enum 변환 5건, 차트 5건 추가, 요약 줄바꿈, 섹션 번호, CHART_COMPONENT_MAP 업데이트 |
| `app/utils/pdf_generator.py` | `_build_table()` 테이블 오버플로 수정 (colWidths + Paragraph 래핑) |

---

## 5. 스코프 외 (이번 수정에서 제외)

| 항목 | 사유 |
|------|------|
| Summary 시각적 카드 (device_categories, server_status) | PDF에서 카드형 레이아웃 구현은 별도 디자인 이슈 |
| Preview 섹션 그룹핑과 PDF 섹션 그룹핑 일치 | 구조 변경은 별도 이슈 |
| 감사 로그 데이터 유무 | 코드는 이미 구현됨. 데이터가 없으면 자동 스킵 (정상 동작) |

---

## 6. 검증 방법

1. **Enum 변환**: 장비 상태 PIE 차트 라벨이 `ACTIVATED`로 표시 (not `EnumDeviceStatus.ACTIVATED`)
2. **설정변경 테이블**: `resource_type`이 `EVENT_MAPPING_CAMERA`로 표시
3. **누락 차트**: PDF에 9개 차트(기존 4 + 신규 5) 포함 확인
4. **요약 줄바꿈**: 각 통계 항목이 별도 행으로 표시
5. **테이블 오버플로**: 8컬럼 테이블이 A4 페이지 내에 수용, 긴 텍스트 워드랩
6. **섹션 번호**: 모든 섹션에 순번 부여 확인
7. **회귀**: 기존 Preview API 응답이 정상 유지
