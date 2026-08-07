# DateTime / TimeZone 전수 감사 — 엔드포인트 인벤토리 + 실측 검증

- **작성일**: 2026-08-07 · **대상**: API **6.3.2** (`release/v6.3`) · **환경**: 개발 서버 `localhost:8000`
- **검증 방식**: 추정 배제. 모든 결론은 **실행 중인 컨테이너·DB에 실제 질의한 출력**과 **file:line** 근거만 사용.
- **원천**: 컨테이너에서 받은 `openapi.json`(251 operation) + `psql` 직접 조회 + 실 HTTP 호출

---

## 0. 두괄식 — PM 질문에 대한 답

> ".env 의 TimeZone 정보를 기반으로 DateTime 에 사용하는 날짜시간정보를 **생성**하게 되는 건가?"

**아니오 — "생성"은 UTC 고정이고, `.env` 의 tz 는 "해석"과 "표시"에만 관여합니다.** 4단계를 분리해야 정확합니다.

| 단계 | 무엇이 결정하나 | `.env` tz 의존 | 근거 |
|---|---|---|---|
| **① 생성** (서버가 새 시각을 만듦) | `utc_now()` = `datetime.now(timezone.utc)` | **없음 (UTC 고정)** | [datetime.py:17-19](app/utils/datetime.py#L17-L19) · 60곳 사용 |
| **② 저장** (DB 기록) | 항상 **UTC 순간** | 없음(정규화 결과만) | [types.py:29-34](app/models/types.py#L29-L34) |
| **③ 입력 해석** (offset 없는 값) | **`DISPLAY_TIMEZONE`** | **있음** | [datetime.py:29-31](app/utils/datetime.py#L29-L31) |
| **④ 출력 렌더** (응답 문자열) | **`DISPLAY_TIMEZONE`** | **있음** | [datetime.py:38-40](app/utils/datetime.py#L38-L40) |

즉 **시각값 자체는 UTC로 만들어 UTC로 저장**하고, `.env` 의 `DISPLAY_TIMEZONE` 은
**"offset 안 붙은 입력을 몇 시로 알아들을지"** 와 **"응답에 몇 시로 찍을지"** 만 정합니다.

---

## 1. 검증 대상 인벤토리 (OpenAPI 251 operation 전수 기계추출)

| 구분 | 수 |
|---|---|
| 전체 operation | **251** |
| 시간정보를 다루는 operation | **180** |
| ├ 쿼리/경로 파라미터로 시간 수신 | **19** |
| ├ 요청 body 로 시간 수신 | **6** |
| └ 응답에 시간 포함 | **178** |

DB 측: 시간 컬럼을 가진 테이블 **45개**. `timestamptz` 43개 / **naive 예외 2개**
(`api_logs.timestamp` 전 파티션, `schema_migrations.applied_at`).


### A. 쿼리/경로 파라미터로 시간을 받는 엔드포인트 — **19개**

| # | Method | Path | 시간 파라미터 | 선언 타입 |
|---|---|---|---|---|
| 1 | GET | `/api/audit-logs` | `start_date` · `end_date` | date-time |
| 2 | GET | `/api/config-change-logs` | `start_date` · `end_date` | date-time |
| 3 | GET | `/api/detection-logs` | `start_date` · `end_date` | date-time |
| 4 | GET | `/api/devices/enclosures/{enclosure_id}/metrics` | `start_time` · `end_time` | date-time |
| 5 | DELETE | `/api/devices/enclosures/{enclosure_id}/metrics` | `before_date` | date-time |
| 6 | GET | `/api/events/actions` | `start_date` · `end_date` | date-time |
| 7 | GET | `/api/events/connections` | `start_date` · `end_date` | date-time |
| 8 | GET | `/api/events/detections` | `start_date` · `end_date` | date-time |
| 9 | GET | `/api/events/malfunctions` | `start_date` · `end_date` | date-time |
| 10 | GET | `/api/events/statistics/by-device` | `start_date` · `end_date` | date-time |
| 11 | GET | `/api/events/statistics/dashboard` | `start_date` · `end_date` | date-time |
| 12 | GET | `/api/events/statistics/summary` | `start_date` · `end_date` | date-time |
| 13 | GET | `/api/events/statistics/trend` | `start_date` · `end_date` | date-time |
| 14 | GET | `/api/logs` | `start_date` · `end_date` | **string(비타입)** |
| 15 | GET | `/api/servers/{server_id}/metrics` | `start_time` · `end_time` | date-time |
| 16 | GET | `/api/system-events` | `start_date` · `end_date` | date-time |
| 17 | GET | `/api/thumbnails` | `start_date` · `end_date` | date-time |
| 18 | GET | `/api/tracking/points` | `from` · `to` | date-time |
| 19 | GET | `/api/tracking/sessions` | `from` · `to` | date-time |

### B. 요청 body 로 시간을 받는 엔드포인트 — **6개**

| # | Method | Path | 시간 필드 |
|---|---|---|---|
| 1 | POST | `/api/event-suppression-schedules` | `window_start` · `window_end` |
| 2 | PATCH | `/api/event-suppression-schedules/{schedule_id}` | `window_start` · `window_end` |
| 3 | POST | `/api/events/actions` | `created_at` |
| 4 | POST | `/api/reports/generate` | `start_date` · `end_date` |
| 5 | POST | `/api/servers/{server_id}/metrics` | `collected_at` |
| 6 | POST | `/api/users/{user_id}/grants` | `valid_from` · `valid_until` |

### C. 응답에 시간을 담는 엔드포인트 — **178개** (태그별 분포)

| 태그 | 수 | | 태그 | 수 |
|---|---|---|---|---|
| Enclosures | 8 | | Server Categories | 6 |
| DeviceGroups | 8 | | Cameras | 5 |
| Event Mapping Cameras | 8 | | Event Statistics | 4 |
| Event Mapping Lamps | 8 | | XyPoints | 4 |
| Event Mapping Speakers | 8 | | Server Metrics | 4 |
| Servers | 8 | | Thumbnails | 4 |
| Event Suppression | 7 | | Camera Settings | 3 |
| Detections | 7 | | Proxy Settings | 3 |
| Malfunctions | 7 | | User Sessions | 3 |
| CameraPresets | 6 | | Audit Logs | 2 |
| Controllers | 6 | | Config Change Logs | 2 |
| Lamps | 6 | | Detection Logs | 2 |
| Sensors | 6 | | Tracking | 2 |
| Speakers | 6 | | Authentication | 1 |
| Actions | 6 | | Mapping Cameras | 1 |
| Connections | 6 | | Mapping Lamps | 1 |
| FileGroups | 6 | | Mapping Speakers | 1 |
| Integration | 6 | | Logs | 1 |
| ROIs | 6 | |  |  |

---

## 2. 입력 해석 검증 — 같은 벽시계를 4형태로 전송

**설계**: 벽시계 `2026-07-01T12:00:00` 을 offset(`+09:00`) / Z / naive / date-only 로 각각 전송하고,
결과 건수를 **DB에서 두 가지 해석으로 직접 센 값**과 대조. 두 해석의 건수가 다른 밀집 구간을 골라야 판별 가능.

### 판별 성공 (오라클 건수가 갈린 구간)

| 엔드포인트 | 오라클 KST | 오라클 UTC | A(offset) | B(Z) | C(naive) | 판정 |
|---|---|---|---|---|---|---|
| `/api/events/detections` | 5,290 | 4,533 | 5,290 | 5,290 | **5,290** | ✔ naive→KST |
| `/api/events/malfunctions` | 2,060 | 1,756 | 2,060 | 2,060 | **2,060** | ✔ naive→KST |
| `/api/detection-logs` | 5,290 | 4,533 | 5,290 | 5,290 | **5,290** | ✔ naive→KST |
| `/api/logs` (naive 컬럼) | 23,196 | 22,928 | 23,196 | 23,196 | **23,196** | ✔ naive→KST |

**결론: offset 없는 입력은 `DISPLAY_TIMEZONE`(KST)으로 해석된다.** 명세 §3.4 혼용 수용 규약과 일치.
`A == B` 가 전 엔드포인트에서 성립 — 같은 순간을 offset/Z 어느 쪽으로 보내도 결과가 같다.

### date-only 입력

`2026-07-01` → 오라클 "KST 자정" 건수와 **정확히 일치**(detections 6,165 = 6,165). 자정 기준 해석 확인.

### 잘못된 값 (`NOT-A-DATE`)

18개 엔드포인트 **422**, `/api/logs` 만 **500** → [결함 F-3](#f-3).

---

## 3. 저장 검증 — 요청 body → DB 실측

`POST /api/event-suppression-schedules` 에 같은 벽시계를 4형태로 전송하고 DB 저장 순간을 직접 조회.

| 전송 형태 | 보낸 값 | DB 저장(UTC) | POST 응답 | GET 재조회 |
|---|---|---|---|---|
| offset | `2026-09-10T08:00:00+09:00` | `2026-09-09 23:00:00` | `08:00+09:00` ✔ | `08:00+09:00` ✔ |
| Z | `2026-09-09T23:00:00Z` | `2026-09-09 23:00:00` | `08:00+09:00` ✔ | `08:00+09:00` ✔ |
| **naive** | `2026-09-10T08:00:00` | `2026-09-09 23:00:00` ✔ | **`17:00+09:00`** ✘ | `08:00+09:00` ✔ |
| **date-only** | `2026-09-10` | `2026-09-09 15:00:00` ✔ | **`09:00+09:00`** ✘ | `00:00+09:00` ✔ |

**저장은 4형태 모두 정확**(offset/Z/naive 가 동일 순간 `23:00 UTC` 로 수렴).
그러나 **naive·date-only 입력 시 생성 직후 응답만 9시간 틀림** → [결함 F-2](#f-2).

---

## 4. 출력 검증 — GET 97개 실제 호출

| 항목 | 결과 |
|---|---|
| 호출 성공(200) | 71개 |
| 발견된 datetime 문자열 | **254개** (최상위 필드 기준 — JSONB 내부는 [F-4](#f-4) 예외) |
| offset 표기 | **전부 `+09:00`** |
| offset 누락 예외 | **0건** |

**DB 원본 ↔ API 응답 대조** (두 컬럼 종류 모두 정상):

| 테이블 | DB 원본 | API 응답 | 판정 |
|---|---|---|---|
| `api_logs` (naive UTC) | `2026-08-07 02:19:32.581999` | `2026-08-07T11:19:32.581999+09:00` | ✔ 정확히 +9h |
| `audit_logs` (timestamptz) | `2026-07-31 12:46:16 UTC` | `2026-07-31T21:46:16.259756+09:00` | ✔ 동일 순간 |

렌더 지점은 **2곳뿐이며 둘 다 `to_display` 경유** — [common.py:16](app/schemas/common.py#L16) (`KSTDatetime` serializer),
[common.py:36](app/schemas/common.py#L36) (`_add_kst_recursive`, `ApiResponse`/`ApiSingleResponse` 의 before-validator).

---

## 5. 발견된 결함 7건 (전부 실측 확인)

### F-1 · 정형 보고서 CSV/PDF 시각이 **UTC 로 출력** — 영향도 최상

`report_service.py` 22곳이 ORM datetime 에 `to_display` 없이 `.strftime()` 을 직접 호출합니다.
asyncpg 는 `timestamptz` 를 **UTC-aware** 로 돌려주므로, `strftime` 은 UTC 벽시계를 찍습니다.

**실제 산출물로 확인** — 리포트 45번 `detail.csv` 의 이벤트 92574:

| 경로 | 값 |
|---|---|
| DB (KST) | `2026-07-20 11:26:19` |
| API JSON | `2026-07-20T11:26:19+09:00` |
| **리포트 CSV** | **`2026-07-20 02:26`** ← 9시간 이름 |

대표 보고용 산출물의 모든 시각이 9시간 이르게 인쇄됩니다.
※ 리포트의 **기간 필터**는 [reports.py:752](app/routers/reports.py#L752) 에서 `to_display` 를 제대로 쓰므로 정상 —
**출력 행의 시각 표기만** 틀립니다.

### F-0 · `server_time` 이 **9시간 틀림** — 클라 시계보정용 필드 · 영향도 최상

`GET /api/auth/me/permissions` 의 `data.server_time` 은 docstring 상 **"클라-서버 시계 편차 보정용"** 인데,
값 자체가 9시간 틀립니다. 이 값으로 보정하는 클라이언트는 오차를 그대로 학습합니다.

| 항목 | 값 |
|---|---|
| 컨테이너 실제 시각 | `2026-08-07 11:56:15 KST` |
| **응답 `server_time`** | **`2026-08-07T02:56:31+09:00`** ← 숫자는 UTC, 라벨만 `+09:00` |

원인 2단:

1. [auth.py:134-137](app/routers/auth.py#L134-L137) `_kst_now()` 가 docstring("settings.tz 기준 naive now")과 달리
   **`utc_now()`(aware UTC)를 반환**합니다. `from app.config import settings` 는 쓰이지도 않습니다.
2. [auth.py:1249](app/routers/auth.py#L1249) 이 그 값에 `astimezone`/`to_display` 가 아니라
   **`.replace(tzinfo=settings.tz)`** 를 걸어 **변환 없이 라벨만** 바꿉니다. 같은 문제가 `:1248` `valid_until`, `:683` 에도 있습니다.

> ※ 이 결함은 두 tz 설정을 같게 둬서 생긴 게 **아닙니다**. `TIMEZONE != UTC` 인 한 항상 발생합니다.

### F-1b · 리포트 표지 기간이 **하루 앞으로** 표기 — 대외 제출 문서

[report_master_builder.py:59,66-67](app/services/report_master_builder.py#L59) 이 aware UTC 를 그대로 `strftime` 합니다.

| 항목 | 값 |
|---|---|
| DB (KST) | `2026-07-13 00:00:00+09` ~ `2026-07-21 23:59:59+09` |
| ORM 반환 (UTC) | `2026-07-12 15:00:00+00` ~ `2026-07-21 14:59:59+00` |
| **표지 렌더(현행)** | **`2026.07.12 ~ 2026.07.21`** ← 시작일 하루 앞 |
| 올바른 값 | `2026.07.13 ~ 2026.07.21` |

### F-1c · 통계·리포트 **일별 버킷이 UTC 기준** — 야간 이벤트가 전날로 이동

앱의 DB 세션 tz 가 **UTC** 라서 `date_trunc`/`extract` 기반 일별 집계가 KST 자정이 아닌 UTC 자정으로 끊깁니다.

**실측** (`user_login_logs` 동일 데이터, 동일 SQL):

| 세션 | 08-04 | 08-05 | 08-06 |
|---|---|---|---|
| 앱 (UTC) | 56 | **8** | 47 |
| psql (KST) | 22 | **47** | 47 |

KST `00:00~09:00` 이벤트가 전날 버킷으로 밀립니다. **야간 침입이 몰리는 GOP 특성상
일별 건수와 피크 시간대가 체계적으로 왜곡**됩니다.

> **⚠ 이전 판단 정정**: 커밋 `a6c5f07` 은 postgres 컨테이너에 `PGTZ` 를 넣어 이 불일치가
> "함께 해소된다"고 적었습니다. **틀렸습니다.** `PGTZ` 는 postgres 컨테이너 내부 libpq
> **클라이언트** 변수라 `psql` 에만 적용되고, api-server 의 asyncpg 세션은
> `postgresql.conf` 의 `timezone = UTC` 를 그대로 씁니다 — 실측 `SHOW timezone = UTC`,
> api-server 컨테이너에 `PGTZ` 환경변수 **부재**. 해당 주석은 이번 차수에 정정했습니다.

### F-4 · 한 응답 안에 offset 이 **3종 혼재** (config-change-logs)

`before_state`/`after_state` 가 `Dict[str, Any]` JSONB 라 재귀 변환을 우회하고,
[config_log_service.py:97,110](app/services/config_log_service.py#L97) 이 `to_display` 없이 `isoformat()` 한 값이
그대로 굳어 저장됩니다.

**실측** — `config_change_logs` id 1626 한 건의 응답:

| offset | 개수 | 예시 |
|---|---|---|
| `+09:00` | 1 | `created_at = 2026-08-07T11:44:25.818356+09:00` |
| `+00:00` | 3 | `before_state.updated_at = 2026-08-07T02:44:25.726996+00:00` |
| **없음** | 1 | `after_state.window_start = 2026-09-11T08:00:00` |

"응답 datetime 은 전부 `+09:00`"이라는 §4 의 결론은 **최상위 필드에만** 해당합니다.
JSONB 내부는 예외입니다.


### F-2 · 생성/수정 응답이 naive 입력 시 9시간 오차

`AsyncSessionLocal` 이 [database.py:70](app/database.py#L70) `expire_on_commit=False` 라
commit 후에도 객체가 **입력받은 naive 값을 그대로** 들고 있습니다.
[event_suppression_schedules.py:180](app/routers/event_suppression_schedules.py#L180) 은 refresh 없이 이를 직렬화하고,
`to_display` 는 naive 를 방어적으로 UTC 로 간주해 +9h 를 더합니다.

- **영향**: `POST` · `PATCH /api/event-suppression-schedules` — 응답만. **DB 저장·GET 재조회는 정확**
- **비영향 확인**: `POST /api/servers/{id}/metrics` 는 [server_metrics.py:234](app/routers/server_metrics.py#L234) `db.refresh()` 덕분에 정상
- **증상**: GIS 가 naive 로 POST 하고 응답을 그대로 화면에 쓰면 08:00 창이 17:00 으로 보임

### F-3 · `GET /api/logs` 잘못된 날짜 → **500**

251개 시간 파라미터 중 유일하게 `str` 로 선언되어 Pydantic 검증을 우회하고,
[logs.py:57](app/routers/logs.py#L57) 이 `datetime.fromisoformat()` 을 직접 호출합니다.

```
ValueError: Invalid isoformat string: 'NOT-A-DATE'   →  HTTP 500
```

다른 18개 엔드포인트는 전부 **422**. 계약 불일치이며 스택트레이스가 로그로 샙니다.

---

## 6. 잠재 위험 2건 (현재는 무증상)

### R-1 · `TIMEZONE ≠ DISPLAY_TIMEZONE` 이면 29곳이 어긋난다

`datetime.now()` (tz 인자 없음) 29곳이 **OS 로컬 벽시계**(= `TIMEZONE`)를 만드는데,
`UtcDateTime` bind 는 그 naive 를 **`DISPLAY_TIMEZONE`** 으로 해석합니다. 두 값이 갈리면 그대로 오차입니다.

**컨테이너 실증**:

| 조건 | `utc_now()` 저장 | `datetime.now()` 저장 | 오차 |
|---|---|---|---|
| 둘 다 `Asia/Seoul` (현재) | `02:18:44.486061Z` | `02:18:44.486064Z` | 3µs |
| `DISPLAY_TIMEZONE=Europe/Budapest` | `02:18:44Z` | **`09:18:44Z`** | **7시간** |

명세 §3.4 가 약속한 "해외 재배포 시 `DISPLAY_TIMEZONE` 만 변경" 조작이 **바로 이 29곳을 깨뜨립니다**.
29곳 전부 `reports.py` · `report_service.py` — F-1 과 같은 파일군.

### R-2 · `db_monitor` NATS 엔벨로프의 tz 하드코딩

[db_monitor/main.py:60](db_monitor/main.py#L60) `datetime.now(KST).isoformat()` — 설정이 아닌 **상수 KST**.
해외 배포 시 서버 응답과 NATS 메시지의 tz 가 갈립니다.

---

## 7. 검증 한계 (정직하게 남김)

| 항목 | 사유 |
|---|---|
| `/api/events/actions`, `/api/tracking/*`, 통계 4종의 **입력 tz 판별** | 오라클 SQL 이 라우터의 실제 필터 조건과 달라 건수가 안 맞음. `A==B==C` 일관성은 확인했으나 KST/UTC 확정은 못 함 |
| `DELETE /api/devices/enclosures/{id}/metrics` (`before_date`) | 파괴적이라 실호출 생략. OpenAPI 상 `date-time` 타입인 것만 확인 |
| 응답 검증 26개 엔드포인트 | 경로 파라미터 ID 가 실재하지 않아 404 |
| PDF 렌더 경로 | CSV 로만 확인. 같은 22곳 함수를 공유하나 PDF 산출물 직접 대조는 미실시 |

---

## 8. 조치 제안 (PM 결정 필요)

| # | 결함 | 사용자 체감 | 제안 | 규모 |
|---|---|---|---|---|
| 1 | **F-0** `server_time` 9시간 | .NET 클라 3종이 시계보정에 사용 → 오차 전파 | `_kst_now()` 정리 + `replace(tzinfo=)` → `to_display()` | `auth.py` 4곳 |
| 2 | **F-1** 리포트 CSV/PDF UTC 출력 | 대표 보고 문서 시각 9시간 이름 | `to_display(x).strftime(...)` 치환 | `report_service.py` 23곳 |
| 3 | **F-1b** 표지 기간 하루 앞 | 대외 제출 문서 대상기간 오표기 | 동일 | `report_master_builder.py` 3곳 |
| 4 | **F-1c** 일별 버킷 UTC 기준 | 야간 이벤트가 전날로 → 통계 왜곡 | 앱 연결에 tz 지정 or `AT TIME ZONE` 명시 | 설계 결정 필요 |
| 5 | **F-2** POST/PATCH 응답 +9h | GIS 가 응답을 화면에 쓰면 오표시 | `_to_response` 전 `db.refresh()` | 라우터 2곳 |
| 6 | **F-3** `/api/logs` 500 | 계약 불일치 + 스택트레이스 유출 | 파라미터 `Optional[datetime]` 승격 | `logs.py` 4줄 |
| 7 | **F-4** JSONB offset 혼재 | 소비자가 tz 를 오판 | `config_log_service` 에 `to_display` 적용 | 1파일 2곳 |
| 8 | **R-1** `datetime.now()` 29곳 | (해외 배포 시) 7시간 오차 | `utc_now()` 치환 | 2파일 |
| 9 | **R-2** db_monitor KST 하드코딩 | (해외 배포 시) NATS/REST tz 불일치 | env 주입 | 1파일 |

**우선순위**: 1~3 은 **대외 산출물·클라 연동에 직접 노출**되므로 최우선.
4 는 집계 의미가 바뀌는 설계 결정이라 별도 검토. 5~7 은 계약 정합. 8~9 는 해외 재배포 선행 조건.

**공통 원인 한 줄**: asyncpg 가 `timestamptz` 를 **UTC-aware** 로 돌려주는데,
`to_display` 를 거치지 않고 `strftime`/`isoformat`/`replace(tzinfo=)` 로 바로 표기한 지점들.
