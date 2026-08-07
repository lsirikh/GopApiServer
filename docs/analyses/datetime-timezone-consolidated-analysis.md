# DateTime / Timezone 혼용 — 통합 분석 (스펙 × 라이브 실측 × 코드 검증)

- 작성일: 2026-07-31
- 대상: GOP API Server v6.3.1 (배포 사이트 포함)
- 근거 소스 3종(상호 확증):
  1. **스펙** — `GOP_Restful_Api_연동설계.md` 형식 분포 분석 (본 세션)
  2. **라이브 실측** — [`docs/API_DateTime_Timezone_Audit_2026-07-31.md`](../API_DateTime_Timezone_Audit_2026-07-31.md) (실서버 HTTPS 호출 측정)
  3. **코드 검증** — datetime-mixing-analysis 워크플로우 (25 에이전트, 33 필드 전수 + 적대적 검증)

---

## 1. 결론 (두괄식)

1. **근본은 "스펙에 datetime 단일 규약이 없음"** 이다. 명세서가 `Z`(UTC)·`+09:00`(KST)·offset 없음(naive) 세 형식을 섹션마다 뒤섞어 예시하고, **validation 에러 메시지는 클라에게 `Z`를 쓰라고 안내**한다. 전역 "날짜/시간 형식" 섹션이 존재하지 않는다.
2. **컨벤션(naive-KST 저장) 자체는 정해졌으나, 경계 정규화 유틸이 없어** 라우터마다 가드를 재구현하거나 누락한다. 그 결과 **목록/삭제 엔드포인트 다수가 aware 날짜필터에 HTTP 500**(라이브에서 12개 실측·코드로 확증), 리포트 응답은 `Z`/`+09:00`가 뒤섞이며, 일부 정리(sweep) 로직은 ~9h 편차가 난다.

> 요약: **스펙이 통일을 안 했다 → 코드가 제각각 구현했다 → 500·드리프트가 났다.** 스펙 규약 신설 + 공용 경계 유틸이 유일한 근본 해법.

---

## 2. 스펙(GOP_Restful_Api_연동설계.md) 형식 분포

| 형식 | 위치 | 문제 |
|---|---|---|
| `...Z` (UTC) | 문서 대부분(171~12154행 수백 개) + **validation 에러 예시** `2026-01-06T00:00:00Z` | 클라에게 Z를 유도 → naive-KST 서버에서 500 |
| `...+09:00` (KST) | 계정·세션·grant(14260~), 일부 이벤트(10452~11506), `meta.timestamp`(5649) | 최신 섹션 |
| offset 없음(naive) | NATS/인제스트·일부(3429~7059, 12515~), 날짜만 | 벽시계 |

- **명시 정의는 2곳뿐**: `meta.timestamp = +09:00`(5649행), `collected_at` = aware/naive→서버 naive-KST 정규화(13478·16378행, 2026-07-31 추가).
- 전역 규약 섹션 부재(헤더 확인: 존재하는 건 `12.1 에러 응답 형식`뿐).

---

## 3. 혼용 맵 (코드 검증, 33 필드 → 상태별)

### 3.1 LIVE_BUG — 즉시 크래시(HTTP 500)

| 필드 / 엔드포인트 | 트리거 | 근거(file:line) |
|---|---|---|
| **ServerMetrics DELETE cutoff** | **무조건 100% 500** (cutoff=`now(tz)`가 항상 aware) | `server_metrics.py:396,400-403` |
| **GET /api/logs 필터** | 번들 로그뷰어가 **항상 Z 전송 → 매번 500** | `logs.py:56-63,596,599` |
| GET /detection-logs | aware start/end vs naive | `detection_logs.py:216-219` |
| GET /action-events (목록) | 목록 필터만 무가드(write/통계는 가드) | `actions.py:292-295` |
| GET /api/system-events | 무가드 start/end | `system_events.py:182-186` |
| GET /servers/{id}/metrics | aware start_time/end_time, read만 누락 | `server_metrics.py:289-292` |
| GET·DELETE /devices/enclosures/{id}/metrics | 가드 헬퍼 전무 | `enclosure_metrics.py:214-217,312-313` |
| GET /api/audit-logs | aware vs naive, 라우터 예시가 +09:00 유도 | `audit_logs.py:129-134` |
| GET /api/config-change-logs | 동일 패턴 | `config_change_logs.py:169-175` |

> 라이브 감사(§3.5)는 여기에 `/api/events/detections·malfunctions·connections·actions`, `/api/thumbnails`까지 포함해 **12개 endpoint 500을 실측**. 코드 맵이 메커니즘·정확 라인으로 확증 + **ServerMetrics DELETE(무조건 500)** 을 신규 발견.

### 3.2 LIVE_BUG — 조용한 오차(500 아님, 잘못된 값)

| 필드 | 증상 | 근거 |
|---|---|---|
| ReportGeneration.start_date/end_date | timestamptz→UTC-naive strip(KST 변환 누락) → **모든 기간 리포트 창 9h 조기 이동, 최근 9h 이벤트 누락** | `reports.py:601-602`, `report_master_builder.py:108-109` |
| ReportGeneration.completed_at | timestamptz에 naive write → 응답 **`+00:00` 방출**(형제 created_at은 `+09:00`) → 클라 표시 9h 역전 | `reports.py:626`, `schemas/common.py:12-22` |
| api_logs 30일 sweep | cutoff=`utcnow()-30d`(naive UTC) vs naive-KST → **~9h 과보존** | `api_logs_sweep_service.py:29-33` |
| token_blacklist cleanup | utcnow cutoff로 KST-basis 행 ~9h 과보존(fail-closed·존재확인만 → 실질 무해) | `token_blacklist_service.py:174-175` |

### 3.3 GUARDED — 지금은 안전하나 가드가 load-bearing

| 필드 | 비고 |
|---|---|
| Event.created_at (event_statistics 4 endpoint) | `_naive_kst` 정규화 = **레퍼런스 픽스** |
| UserGroupGrant.valid_from/valid_until | write에 `_to_naive_kst`, 제거 시 INSERT-500 재발 |
| UserSession.expires_at/refresh_expires_at | 자기 비교 naive-KST 일관 |
| ReportGeneration.progress_updated_at | 컨테이너 TZ+PGTZ=Asia/Seoul 정렬 의존(어긋나면 watchdog 9h 오작동) |

### 3.4 OK / DRIFT / COSMETIC

- **OK**: `*.created_at`(naive 표준)·SystemEvent.acknowledged_at·AccountUser.locked_at·TrackPoint.created_at·v60 파티션 경계.
- **이미 수정**: `server_metrics.collected_at`(write, v6.3-server_metrics_tz_fix)·event_statistics(4)·`UserSession.logged_out_at`(v6.0-force_logout_tz_fix).
- **DRIFT(잠재)**: grant_scheduler run_date(스케줄러 UTC면 9h 지연)·AccountUser.password_expires_at(**문서=aware vs 모델=naive**, dormant → 문서대로 writer 생기면 INSERT-500)·TrackPoint.observed_at 수작업 커서 offset.
- **COSMETIC**: ApiLog.timestamp 모델 default aware(.replace 누락, 미들웨어가 override)·TokenBlacklist.revoked_at(utcnow, 미비교).

---

## 4. 근본 원인 (코드 검증 종합)

컨벤션은 **naive-KST**(`TIMESTAMP WITHOUT TIME ZONE`, write=`datetime.now(settings.tz).replace(tzinfo=None)`)인데—

1. 목록/삭제 라우터가 날짜 쿼리를 `Optional[datetime]`로 받아 **tz-aware ISO(+09:00/Z)를 허용**(Swagger·스펙 예시가 유도)하고, asyncpg가 aware 값을 naive 컬럼 코덱에 바인딩하며 **compare-500**.
2. 이를 막는 경계 정규화 헬퍼(`_naive_kst`/`_to_naive_kst` — 동일 로직 `astimezone(settings.tz).replace(tzinfo=None)`)가 **event_statistics·server_metrics-write 2곳에만** 존재, 형제 라우터로 미이식.
3. 리포트 2컬럼만 `DateTime(timezone=True)`로 이탈 + 읽기 strip이 **UTC→KST 변환 누락** → 9h 드리프트.
4. 일부 cutoff가 `datetime.utcnow()`로 KST-naive 컬럼과 비교 → 9h 편차.

→ **경계 공용 정규화 유틸 부재 + 컬럼 타입 레벨 가드 부재**로 라우터마다 가드를 재구현/누락하는 **구조적 결함**. 그리고 그 위에 **스펙이 단일 규약을 안 줘서** 애초에 클라가 aware(Z)를 보내도록 유도된다.

---

## 5. 수정 계획 (우선순위)

### 코드
- **P0-1**: `server_metrics.py:396` DELETE cutoff를 `datetime.now(settings.tz).replace(tzinfo=None) - td`로 (무조건 100% 파손).
- **P0-2**: `logs.py:56-63` GET /logs start/end에 `to_naive_kst()` (번들 뷰어가 항상 Z → 매번 500).
- **P1-3**: detection_logs·actions(목록)·system_events·server_metrics(GET)·enclosure_metrics(GET+DELETE)·audit_logs·config_change_logs의 client start/end/before에 정규화 헬퍼 적용.
- **P1-4**: 리포트 read-back strip을 `astimezone(settings.tz).replace(tzinfo=None)`로. 근본책은 `report.py:62-63,92` 컬럼을 **naive-KST로 마이그레이션**, completed_at write도 naive-KST 통일.
- **P2-5**: api_logs sweep·token_blacklist cutoff를 KST-naive로. `models/log.py:18` default에 `.replace(tzinfo=None)`.
- **P3-6**: grant_scheduler tz=Asia/Seoul assert, tracking cursor tz-strip, password_expires_at 문서/모델 정합.

### 리팩토링(근본)
- **공용 유틸** `app/utils/datetime.py`에 `to_naive_kst(dt)`/`kst_now_naive()` 신설 → 파일별 사본(`_naive_kst`·`_to_naive_kst`·`_to_kst_naive`) 전량 대체.
- **타입 레벨 가드**: naive `DateTime` 컬럼용 SQLAlchemy `TypeDecorator`가 bind 시 aware→KST-naive strip → 라우터 실수와 무관하게 차단. + 쿼리 파라미터 정규화 공용 의존성/validator.
- **출력 serializer**: `_kst_isoformat`에 `else: v = v.astimezone(KST)` 추가(aware도 KST로 변환) → 리포트 Z/+09:00 혼용 소멸. 오류 meta도 `+09:00`로 통일.

### 스펙(근본)
- **전역 "datetime 규약" 섹션 신설**: 입력=aware 허용+서버 KST-naive 정규화 / 출력=전 필드 `+09:00` / 저장=naive-KST 단일.
- **validation 에러 예시를 `Z` → `+09:00`으로 수정** (현재 스펙이 500 나는 형식을 안내).

### 테스트
- 전 list/delete 엔드포인트를 aware(`+09:00`/`Z`)·naive로 파라미터라이즈 회귀.
- 리포트 창은 KST 경계 이벤트 포함/제외 골든 테스트.

---

## 6. 배포 사이트 영향

방금 업그레이드한 v6.3.1 사이트에 위 **§3.1 500·§3.2 드리프트가 그대로 존재**(업그레이드 무관·기존 결함). 특히 **ServerMetrics DELETE는 호출 시 무조건 500**, **로그뷰어 날짜필터는 매번 500**. 운영 영향이 큰 순: P0-1·P0-2 → P1.
