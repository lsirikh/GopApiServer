# GOP 서버 API v6.0 (release/v6.0) 리포트/계정 업데이트 통지 — 클라(.NET) 대상

- **작성일**: 2026-07-05
- **작성**: 서버 세션
- **대상**: .NET 클라 세션 (Ironwall/Dotnet.Monitoring.Solution/Rtsp.Viewer.Ui)
- **브랜치/버전**: `release/v6.0` (Swagger info.version=6.0.0 유지)
- **연관 태그** (같은 브랜치 위 4개 소분):
  - `v6.0-report_fixes` (2026-07-04) — 리포트 데이터 정합화
  - `v6.0-account_rbac` (2026-07-05) — ADMIN 3계정 시드
  - `v6.0-report_lifecycle_persistence` (2026-07-05) — 수명주기 + PDF 영속화
  - `v6.0-report_progress_perf` (2026-07-05) — 진행률 + Stall 워치도그 + 성능
- **참조 PRD (원작성=.NET 세션, 서버가 구현)**:
  - `PRD_GOP_Server_Reports_Generation_Lifecycle.md` (Draft)
  - `PRD_GOP_Server_Reports_PDF_Persistence.md` (Draft)

---

## 📌 두괄식 필독 요약

| # | 항목 | 클라 조치 필요? |
|---|---|---|
| **1** | 리포트 생성 응답에 **진행률(progress_pct/stage/updated_at) 필드 3개 추가** | ✅ 폴링 시 표시 권장 |
| **2** | 다운로드 실패가 **404(없음) vs 410(파일 소실)** 로 분화 | ✅ 안내 문구 분기 |
| **3** | 상세 CSV 다운로드 **신규 endpoint** (`GET /generations/{id}/detail.csv?type=…`) | ✅ 옵션 버튼 |
| **4** | 리포트 세션/설정/시스템/감사 그리드 **컬럼 확장** (누가/어디/무엇을) | ✅ 렌더링 반영 |
| **5** | 정형 7d 리포트 **~9x 성능 개선** (id=31 실측: 20s 완료. 이전 사이클 180s FAILED) | 특별 조치 없음 |
| **6** | **wall-clock timeout 제거** — 정상 진행 시 시간 무제한. Stall 60s 감지만 FAILED | 폴링 시간 상한 재검토 가능 |
| **7** | 컨테이너 recreate 시 in-flight 리포트 **자동 FAILED 정리** — "생성중" 무한 잔류 소멸 | UX 개선(자연 해소) |
| **8** | 기본 ADMIN 계정 3종 시드 (**m_manager / vms_manager / popup_manager**, pw: `sensorway1`) | 필요 시 개발/시연 로그인 |

---

## 1. API 계약 변경

### 1-1. 리포트 생성 상세 조회 응답 스키마 확장

**Endpoint**: `GET /api/reports/generations/{generation_id}`

`data` 오브젝트에 3필드 추가:

| 필드 | 타입 | 값 예시 | 의미 |
|------|------|---------|------|
| `progress_pct` | int (0~100) | `80` | 현재 진행률 % |
| `progress_stage` | string \| null | `"html"` | 현재 stage (아래 표 참조) |
| `progress_updated_at` | timestamp \| null | `"2026-07-05T09:03:10"` | 마지막 progress 갱신 시각 |

**Stage 값**:
| stage | pct | 의미 |
|---|---|---|
| `start` | 5 | GENERATING 마킹 직후 |
| `setup` | 10 | 서비스/메타 준비 완료 |
| `master_data` | 60 | 마스터 데이터 빌드 완료 (SQL 집계) |
| `html` | 80 | HTML 렌더 완료 (Jinja) |
| `pdf` | 95 | PDF 렌더 완료 (Playwright) |
| `done` | 100 | 파일 저장 + DB 커밋 완료 |

**응답 예시** (진행 중):
```json
{
  "success": true,
  "data": {
    "id": 31,
    "status": "GENERATING",
    "progress_pct": 60,
    "progress_stage": "master_data",
    "progress_updated_at": "2026-07-05T09:03:03.123456",
    "title": "월간 표준보고서",
    "period_type": "7d",
    "start_date": "2026-06-28T00:01:04.339461Z",
    "end_date": "2026-07-05T00:01:04.339461Z",
    "created_at": "2026-07-05T09:01:04.340270+09:00",
    "completed_at": null,
    "preview_html_url": "/api/reports/preview/31"
  }
}
```

**응답 예시** (완료):
```json
{
  "success": true,
  "data": {
    "id": 31,
    "status": "COMPLETED",
    "progress_pct": 100,
    "progress_stage": "done",
    "progress_updated_at": "2026-07-05T09:03:22.999999",
    "completed_at": "2026-07-05T09:03:22.999999Z",
    "pdf_download_url": "/api/reports/generations/31/download",
    "preview_html_url": "/api/reports/preview/31"
  }
}
```

**응답 예시** (stall FAILED):
```json
{
  "data": {
    "id": 32,
    "status": "FAILED",
    "progress_pct": 60,
    "progress_stage": "master_data",
    "progress_updated_at": "2026-07-05T10:00:00",
    "completed_at": "2026-07-05T10:01:00",
    "error_message": "generation stalled (60s no progress)"
  }
}
```

**클라 UX 권장**:
- 폴링 응답에서 `progress_pct` 표시 (예: "리포트 생성 중… 60% (master_data)")
- `status=FAILED` + `error_message` 확인해 사유 안내 (stall / 서버 재시작 / 일반 실패)

---

### 1-2. 다운로드 응답 분화 (404 vs 410)

**Endpoint**: `GET /api/reports/generations/{generation_id}/download`

| 케이스 | HTTP | 응답 body | 의미 | 클라 안내 |
|---|---|---|---|---|
| 레코드 자체 없음 | **404** | `{ "detail": "Report generation not found" }` | 존재하지 않는 보고서 ID | "없는 보고서" |
| 생성 미완료 | **400** | `{ "detail": "Report is not COMPLETED yet" }` | 아직 생성 중 or 실패 | "생성 완료 후 다시 시도" |
| pdf_file_path NULL | **404** | `{ "detail": "PDF file not found" }` | 생성 실패 잔재 (path 미기록) | "PDF 파일 없음 — 재생성 필요" |
| **파일 소실 (신규)** | **410 Gone** | `{ "error_code": "PDF_FILE_MISSING", "message": "PDF file has been removed from storage (report re-generation required)", "report_id": N }` | 컨테이너 recreate 등으로 실물 파일 소실. **DB는 살아있음** | "PDF 소실됨 — 재생성 필요" |
| 성공 | **200** | `application/pdf` 바이트 | | 저장 |

**클라 조치**:
- 기존 "PDF 없음" 안내를 **404와 410으로 분화**하여 UX 정확도 향상
- 410 시 "재생성 버튼" 강조 (실제로 새로 생성하면 볼륨에 저장되어 이후 유지됨)

---

### 1-3. 상세 CSV 다운로드 (신규 endpoint)

**Endpoint**: `GET /api/reports/generations/{generation_id}/detail.csv?type={grid}`

PDF 상세 그리드는 v6.0-report_progress_perf부터 **상위 500행만 표시**됩니다 (성능/가독성). 감사/분석용 전량 rows는 이 CSV로 제공.

| Query Param | 필수 | 유효값 |
|---|---|---|
| `type` | ✅ | `detection` \| `malfunction` \| `action` \| `system` \| `config` \| `audit` \| `login` \| `session` |

**응답**:
- Content-Type: `text/csv; charset=utf-8`
- BOM: `﻿` 프리픽스 (Excel 한글 호환)
- Content-Disposition: `attachment; filename="report_{id}_{type}.csv"`
- 기간 필터: generation.start_date/end_date 범위 사용 (session은 전량)
- 권한: `reports.view`

**CSV 헤더** (type별):

| type | 컬럼 |
|---|---|
| detection | ID, 일시, 장비명, 탐지유형, 조치보고, 구역, 조치건수, 장비설명 |
| malfunction | ID, 일시, 장애유형, 장비명, 구역, 조치건수, 장비설명 |
| action | ID, 일시, 유형, 내용, 조치자 |
| system | ID, 일시, 유형, 심각도, 제목, 메시지 |
| config | ID, 일시, 행위자, IP, 리소스유형, 리소스명, 리소스ID, 액션, 변경설명 |
| audit | ID, 일시, 액션, 상태, 리소스, 행위자 |
| login | ID, 일시, 로그인ID, 액션, 결과, IP |
| session | ID, 로그인ID, 사용자명, IP, 생성일, 만료일 |

**클라 UX 권장**:
- PDF 미리보기 근처에 "상세 CSV" 드롭다운 (8종) 또는 "전체 이벤트 CSV 다운로드" 버튼

---

## 2. 리포트 데이터 표시 개선 (v6.0-report_fixes)

리포트 뷰(PDF/HTML 프리뷰/JSON preview)의 그리드 컬럼이 확장됨. 클라가 렌더링 시 새 컬럼을 반영해야 합니다.

### 2-1. 세션 목록 (`USER_SESSION_GRID`)

| 이전 | 신규 |
|---|---|
| `[ID, 사용자ID(정수), IP, 생성일, 만료일]` | `[ID, 로그인ID, 사용자명, IP, 생성일, 만료일]` |

`account_users` LEFT JOIN 반영. `user_id` 정수 → `login_id` + `name` 노출.

### 2-2. 감사 로그 (`SYSTEM_AUDIT_GRID`)

`행위자` 컬럼이 이전엔 `actor_name` (nullable) 만 사용 → `COALESCE(actor_name, actor_login_id, '(system)')` 폴백. 시스템 감사도 "(system)"으로 표시.

### 2-3. 설정 변경 이력 (`SYSTEM_CONFIG_GRID`)

| 이전 (5컬럼) | 신규 (8컬럼) |
|---|---|
| `[ID, 일시, 리소스유형, 액션, 리소스ID]` | `[ID, 일시, 행위자, IP, 리소스유형, 리소스명, 액션, 변경설명]` |

`누가 무엇을 어떻게 바꿨는지` 감사 핵심 정보 노출.

### 2-4. 시스템 이벤트 (`SYSTEM_EVENT_GRID`)

| 이전 (5컬럼) | 신규 (6컬럼) |
|---|---|
| `[ID, 일시, 유형, 심각도, 메시지]` | `[ID, 일시, 유형, 심각도, 제목, 메시지]` |

`title` 컬럼 추가 (NOT NULL 필드).

### 2-5. 라벨 통일 (JSON preview)

역할/심각도/탐지유형/장애유형/장비카테고리 등 소스에 따라 원문("ADMIN") vs 한국어("관리자")로 달랐던 라벨을 **모두 한국어 통일**. JSON preview도 이제 HTML/PDF와 동일 값.

### 2-6. 필터 윈도우 통일

같은 리포트를 JSON preview와 HTML/PDF로 열면 서로 다른 기간이 적용되던 버그 수정. 두 뷰 모두 `generation.start_date/end_date` 기준.

**클라 조치**:
- 리포트 UI/데이터 바인딩에서 새 컬럼 반영
- 리포트 preview vs PDF의 데이터 불일치가 있었다면 해소됨

---

## 3. 리포트 수명주기 (v6.0-report_lifecycle_persistence)

### 3-1. 컨테이너 재시작 자동 정리

서버 부팅 시(main.py lifespan) `PENDING`/`GENERATING`인 모든 generation을 **자동으로 `FAILED` 전이**:
- `error_message = "server restarted during generation"`
- `completed_at = NOW()`

**의미**: 클라가 이전에 겪던 "생성중" 무한 잔류 케이스가 서버 재시작만으로 해소됨. 클라는 특별한 조치 필요 없음 — 목록 새로고침 시 자연스레 "실패"로 표시됨.

### 3-2. Wall-clock timeout 제거 → Stall watchdog

이전 (v6.0-report_lifecycle_persistence):
- `REPORT_GEN_TIMEOUT_SEC=180` — 정상 진행 중이어도 180s 초과 시 강제 FAILED

현재 (v6.0-report_progress_perf):
- Wall-clock timeout **제거**
- **Stall watchdog**: `progress_updated_at`이 60s 이상 정체되면 FAILED
- 정상 진행 중인 큰 리포트는 시간 무제한 완료 가능

**FAILED 종류별 error_message**:
| 사유 | error_message |
|---|---|
| 서버 재시작 | `"server restarted during generation"` |
| Stall 감지 (60s no progress) | `"generation stalled (60s no progress)"` |
| 일반 예외 | `str(exception)` (그대로) |
| 사용자 취소 | 별도 status `CANCELLED`, message `"Cancelled by user"` |

**클라 폴링 권장**:
- 현재 클라 폴링 창(~135s)이 충분. 필요 시 상한 상향 가능 (진행률로 살아있음 확인)
- `progress_updated_at`이 오래 갱신 안 되면 클라도 "지연" 안내 표시 가능 (서버 stall watchdog와 별개로 UX)

### 3-3. PDF 영속화

`docker-compose.yml`에 `api-test-reports:/app/reports` named volume 마운트. 컨테이너 recreate/재빌드에도 PDF 유지.

**의미**:
- 다운로드 404가 대폭 감소
- 다만 v6.0-report_lifecycle_persistence 이전에 생성된 리포트(dangling)는 파일 없음 상태 유지 → 410 응답
- 정책: dangling COMPLETED은 그대로 두고 사용자 재생성 유도 (FR-RPP-02 정책 a)

---

## 4. 기본 계정 시드 (v6.0-account_rbac)

컨테이너 빌드 시 자동으로 시드되는 ADMIN 계정 (기존 admin 외 3종 신규):

| login_id | password | role | 이름 |
|---|---|---|---|
| admin | admin123 | ADMIN | 슈퍼사용자 |
| **m_manager** | **sensorway1** | ADMIN | M 매니저 |
| **vms_manager** | **sensorway1** | ADMIN | VMS 매니저 |
| **popup_manager** | **sensorway1** | ADMIN | 팝업 매니저 |

- 저장은 `bcrypt` 해시. group_id NULL (ADMIN bypass).
- Idempotent — 재빌드 시 이미 존재하면 스킵 (사용자가 변경한 password 보존).
- Dev/시연 기본값. 프로덕션 배포 시 최초 로그인 후 변경 권장.

**클라 조치**: 개발/시연/QA 로그인 시 활용 가능.

---

## 5. 성능 개선 (참고)

### 5-1. build_master_data_async SQL 집계 이관

이전엔 파이썬 `Counter`로 66k+ 이벤트 for 루프 → GROUP BY SQL로 이관. 파이썬 iter 병목 제거.

### 5-2. 상세 그리드 LIMIT 500

`§3 탐지 / §4 장애 / §5 조치 / §6 시스템 / §7 config / §8 감사 / §9 로그인·세션` 상세 rows가 LIMIT 500으로 제한됩니다. 통계·요약은 전체 대상 정확도 유지.

**전량 필요 시**: `GET /generations/{id}/detail.csv?type={grid}` (§1-3 참조).

### 5-3. 실측 (2026-07-05)

| 리포트 | 이전 (v6.0-report_lifecycle_persistence, wall-clock 180s) | v6.0-report_progress_perf |
|---|---|---|
| id=30 (7d, 66k det + 26k mal) | 180s → FAILED "generation timeout" | — |
| id=31 (동일 조건) | — | **T+10s 80% (html), T+20s 100% (done)** |

---

## 6. 클라 액션 체크리스트

- [ ] 리포트 폴링에서 `progress_pct`/`progress_stage` 사용 → UI에 진행률 표시
- [ ] 다운로드 응답 처리에 **HTTP 410 분기** 추가 (안내 문구 세분화)
- [ ] "상세 CSV" 다운로드 옵션 UI (8 grid type 드롭다운 또는 단일 종합 버튼)
- [ ] 리포트 그리드 렌더링에 확장 컬럼 반영:
  - USER_SESSION_GRID: `[로그인ID, 사용자명]` 신규
  - SYSTEM_CONFIG_GRID: `[행위자, IP, 리소스명, 변경설명]` 신규
  - SYSTEM_EVENT_GRID: `[제목]` 신규
  - SYSTEM_AUDIT_GRID: `(system)` 폴백 표시 확인
- [ ] JSON preview vs PDF 데이터 일관성 QA (필터/라벨 통일 확인)
- [ ] "PDF 렌더 실패" 안내 문구 분화:
  - `"server restarted during generation"` → "서버 재시작으로 실패 — 재생성"
  - `"generation stalled (…)"` → "생성 지연으로 중단 — 재시도"
  - `"Cancelled by user"` → "취소됨"
- [ ] (선택) 클라 폴링 상한 재검토 — Stall watchdog가 서버측에서 hang 방지하므로 클라 timeout 상향 가능

---

## 7. 미해결/별도 트랙 (참고)

서버측 다음 사이클에 다룰 항목 (클라 조치 무관):

| 항목 | 상태 |
|---|---|
| **config_change_logs actor_id 95% NULL** | 로깅 서비스 레이어 감사 필요 (별도 사이클) |
| **FR-RPP-04 healthcheck TLS readiness** | 부팅 중 TLS 미준비 시 클라가 재시도로 대응 이미 구현됨 |
| **FR-RGL-05 durable queue** | dev 단계 미필요 (현재 stall watchdog로 충분) |
| **두 리포트 파이프라인 단일화** | 유지보수 개선 (JSON preview 정본 승격 후보) |
| **system_events 발화 소스** | 서버 헬스체크 워커 (인프라) |
| **PDF 렌더 시 "500행 표시" 안내 문구** | HTML 템플릿 개선 예정 |

---

## 8. 참조

- **CHANGELOG**: `CHANGELOG.md` — `v6.0-report_fixes` / `v6.0-account_rbac` / `v6.0-report_lifecycle_persistence` / `v6.0-report_progress_perf` 섹션
- **Swagger**: `https://{server}:8000/docs` (info.version=6.0.0)
- **커밋 이력**:
  - `afeec2d` v6.0-report_fixes
  - `6264972` v6.0-account_rbac
  - `9aab36c` v6.0-report_lifecycle_persistence
  - `bd5152b` v6.0-report_progress_perf
- **저장소**: origin=github.com/lsirikh/GopApiServer, gitea=192.168.202.160:3000/Sensorway_SW/GOP-Api-Db-Server

문의/피드백은 서버 세션으로 회신 바랍니다.
