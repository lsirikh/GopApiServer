# PRD: 보고서 마스터 디자인 재설계 (정형/비정형 통합)

**문서 버전**: 1.0
**작성일**: 2026-06-30
**상태**: Implemented
**기반**: 레퍼런스 `docs/경보 분석보고서 (2026-05-31 ~ 2026-06-30).pdf` (네이비/골드 전문 보고서)

---

## 1. 배경 / 문제

기존 보고서는 **출력 경로가 3갈래**(reportlab PDF / Jinja preview.html / 죽은 4섹션 함수)로 갈라져 서로 다르고, 기획(FIGMA)과도 달랐다. PDF는 표지/카드 없는 평면 나열, 표는 열 오버플로·행 잘림이 있었다.

→ **단일 데이터→단일 HTML→PDF** 파이프라인으로 통합하고, 레퍼런스의 네이비/골드 디자인을 재현한다.

## 2. 목표

- 표지(사이드바·골드 액센트·목차) + 섹션(번호칩) + 그라데이션 KPI카드 + 분석요약 박스 + Chart.js(도넛/바/라인) + 깔끔한 표.
- **표 깨짐 해결**: `table-layout:fixed` + `colgroup`(폭 합 100%) + 행단위 사전 페이지네이션(22행/p, 헤더 반복) → 열 오버플로/행 잘림 0.
- **정형(STANDARD)** = 전 섹션 + 전체 페이지네이션. **비정형(CUSTOM)** = `report_templates.components`(enabled_components)로 섹션/컴포넌트 선택.
- **모든 Enum → 한글** 매핑.
- **프리뷰 HTML == PDF** (동일 렌더러).

## 3. 섹션 (정형 = 전 10개)

| # | 섹션 | 차트 | 그리드 |
|---|------|------|--------|
| 1 | 종합 요약 | KPI 카드 6 + 분석요약 | — |
| 2 | 장비 현황 | 상태 도넛, 유형 바 | 장비 목록 |
| 3 | 탐지 이벤트 | 유형·구역 도넛, 시간대 바 | 탐지 목록 |
| 4 | 장애 이벤트 | 유형 바 | 장애 목록 |
| 5 | 조치 이벤트 | — | 조치 목록 |
| 6 | 시스템/운영 로그 | 심각도 바, 추이 라인 | 시스템 이벤트 |
| 7 | 설정 변경 이력 | — | 설정 변경 |
| 8 | 감사 로그 | — | 감사 로그 |
| 9 | 사용자 현황 | 역할·결과 도넛, 로그인 추이 | 사용자/로그인/세션 |
| 10 | 서버 현황 | 상태 도넛 | 서버 목록 |

## 4. 아키텍처

```
ReportGeneration ─▶ report_master_builder.build_master_data(db, start, end, meta, enabled_components)
                      └ SQLAlchemy text() 전 도메인 추출 + 집계 + report_labels(Enum→한글) + 컴포넌트 태깅/필터
                    ─▶ report_html_renderer.render_report_html(data, mode)   # full=전체 / compact=그리드당 2p
                      └ 표지/섹션/카드/차트/그리드 + 전체 페이지네이션, 자산 inline(report.css/charts.js/chart.umd.js)
                    ─▶ html_to_pdf.html_to_pdf_bytes(html)                   # Playwright + Chromium(headless) → A4 PDF
```

| 파일 | 역할 |
|------|------|
| `app/utils/report_labels.py` | Enum→한글 중앙 매핑 (탐지/장애/카테고리/상태/심각도/역할/결과/시스템이벤트/설정/감사/로그인/조치) |
| `app/services/report_master_builder.py` | DB→제네릭 섹션(cards/summary/charts/grid), `build_report_meta()` 공통 메타 |
| `app/services/report_html_renderer.py` | 섹션→풀 HTML(페이지네이션) |
| `app/templates/reports/assets/` | report.css, charts.js, chart.umd.js (오프라인 inline) |
| `app/utils/html_to_pdf.py` | Playwright Chromium HTML→PDF + PyMuPDF 무손실 재압축(~85% 축소) |
| `app/services/report_service.py` | `generate_report_async` 신규 경로. 구 reportlab은 `_generate_report_legacy` 보존 |
| `app/main.py` `/reports/preview/{id}` | 동일 HTML 서빙(기본 compact, `?mode=full`) |

## 5. 렌더 엔진 결정

**Playwright + Chromium**(헤드리스). 승인된 Chart.js/CSS 디자인을 1:1 재현하기 위함. Dockerfile에 `playwright install --with-deps chromium` 추가(이미지 +약 350MB). 백그라운드 태스크(스레드)에서 동기 API 사용, `--no-sandbox`.

대안 WeasyPrint(+matplotlib)는 경량이나 JS 미지원(차트 이미지화)·CSS 재조정 필요로 미채택.

## 6. 검증 (2026-06-30, 실데이터)

- 정형 E2E: `generate_report_async` → COMPLETED, **787p / 66MB**, 에러 0.
- 표 깨짐 0(22행/p, 헤더 반복), Enum 전부 한글, 표지/목차 실제 페이지번호.
- 컨테이너(api-test-server) Chromium 렌더 정상.

## 7. 산출물 샘플

`reports/preview/마스터샘플_정형보고서_{compact,full}_2026-06-30.{html,pdf}`

## 8. 스코프 외 / 후속

- 비정형(CUSTOM) 프런트 UI 연동(컴포넌트 선택) — 백엔드 필터는 구현됨.
- 대용량(정형 787p, 66MB) 렌더 시간/메모리 — 필요 시 상세표 옵션화(요약 중심 + CSV 별첨).
- 구 `app/templates/reports/preview.html`, `pdf_generator.py`, `_generate_report_legacy` 정리(현재 보존).

## 9. 변경 이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-06-30 | 초기 구현 — 정형 전 섹션 통합, 표 수정, Enum 한글, Playwright 통합 |
