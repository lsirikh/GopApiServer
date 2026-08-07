# event-suppression-recurrence PRD — 억제(정비 창) 반복 스케줄

- **작성일**: 2026-08-04
- **상태**: Draft
- **버전**: v1.0
- **언어/프레임워크**: Python / FastAPI + SQLAlchemy(async) + PostgreSQL + NATS
- **대상 릴리즈**: `release/v6.3` (API 6.3.2 → 6.4) · 태그 후보 `v6.3-event_suppression_recurrence`
- **선행 PRD**: [event-suppression-schedule-prd.md](event-suppression-schedule-prd.md) v1.1(Approved) ·
  [event-suppression-multi-target-prd.md](event-suppression-multi-target-prd.md) ·
  [event-suppression-sync-message-prd.md](event-suppression-sync-message-prd.md) ·
  [event-suppression-hardening-prd.md](event-suppression-hardening-prd.md)
- **검증 근거**: **시뮬레이션 2회차 실측** — `docs/analyses/recurrence-sim/`
  (`sim_round1.log` 1,119행 / `sim_round2.log` 126행, 하네스 코드 포함)
- **작성자**: 이기호 차장(요청) / Claude(초안)

---

## 변경 이력

| 날짜 | 버전 | 변경 항목 | 변경 이유 | 영향 범위 |
|------|------|---------|---------|---------|
| 2026-08-04 | v1.0 | 초안 작성 | PM 요구 — "시작~끝 기간 안에서 **월~금 08:00~21:00** 처럼 반복 지정, **기간 제한 없음**도 가능해야" | 스키마 6컬럼 · 게이트/상태/스케줄러/SQL트리거 8지점 · REST 계약 · NATS 계약 · 서브시스템 문서 |

---

## 0. 두괄식 요약

> **결론**: `recurrence_type='weekly'` + **요일 비트마스크 · 로컬 일일 시각 · 유효기간(끝 NULL 허용)**
> 6개 컬럼을 추가한다. 기존 단발 창은 `recurrence_type='none'` 으로 **무변경 동작**한다.
> 시뮬레이션 결과 **occurrence 수학은 616검사 전건 통과**했고, 진짜 위험은 **기존 접합면 7곳**에 있었다.

### PM 요구 2가지 (그대로 표현 가능)

| 요구 | 표현 |
|---|---|
| `2026-08-09 ~ 2026-09-20`, 월~금 `08:00~21:00` | `valid_from=08-09, valid_until=09-21, days=월화수목금, daily=08:00~21:00` |
| **기간 제한 없음**, 월~금 `08:00~21:00` | `valid_from=…, valid_until=NULL, days=월화수목금, daily=08:00~21:00` |

### 시뮬레이션 실측 결과 (추정 아님)

| 회차 | 범위 | 결과 |
|---|---|---|
| **1회차** | occurrence 판정 수학 — 후보구현 vs **독립 오라클** 차등 테스트 | 시나리오 **119개 / 검사 616건 / 불일치 0** |
| **2회차** | 기존 서버 구조와의 **접합면 실측** | **이슈 7건 도출** (P0 3 · P1 3 · P2 1) |

> 1회차의 "불일치 0" 은 *구현이 옳다*는 뜻일 뿐 *설계에 문제가 없다*는 뜻이 아니다.
> 그래서 2회차를 접합면 실측으로 돌렸고, **거기서 전부 나왔다.**

### 2회차 도출 이슈와 확정 해법

| # | 등급 | 이슈 (실측) | 확정 해법 |
|---|---|---|---|
| **I-1** | **P0** | 반복 창은 **SQL WHERE 로 좁혀지지 않음** — 게이트가 전건 로드 후 파이썬 평가 | 파이썬 평가 채택. **I-6 실측이 근거** — 스케줄 100개도 **0.271ms/요청** |
| **I-3** | **P0** | 무제한 반복은 date-job **사전 예약 원리적 불가** | **occurrence 전이 잡을 아예 걸지 않음**(I-2 해법과 통합) |
| **I-4** | **P0** | 소비자 fail-safe 계약 붕괴 — `window_end` 가 무제한 반복에서 **없음** | 응답에 **`occurrence_start`/`occurrence_end`/`next_occurrence_start`** 신설, 타이머 기준을 `occurrence_end` 로 재정의 |
| **I-2** | **P1** | 무제한 반복 1개 = **연 520건** 전이 발행 (단발 2건 대비 **260배**), 창 50개면 **연 26,000건** | **occurrence 전이는 NATS 미발행.** 반복 규칙은 결정적이라 소비자가 로컬 계산 가능 + `/active` 폴링이 권위 |
| **I-5** | **P1** | `idle` 신규 status 가 유효기간의 **62.2%** — 기존 4종 enum 파괴 | **status 4종 고정 유지** + 신규 **`is_suppressing_now: bool`** 필드 분리 |
| **I-7** | **P1** | `/active` 가 유효기간을 담아 소비자가 **현재 억제 구간을 모름** | `/active` 정의를 **"현재 occurrence 진행 중인 창"** 으로 확정 + occurrence 필드 동반 |
| **I-8** | **P2** | 겹침 경고를 유효기간으로 판정하면 **대량 오탐**(월창 vs 토창은 100% 겹침으로 오판) | 겹침 = **요일 교집합 ∧ 시각 구간 교집합** 으로 재정의 |
| ~~I-6~~ | — | 게이트 계산 비용 | **이슈 미발생** — 1개 0.003ms / 100개 0.271ms (임계 5ms 대비 충분) |

---

## 1. 개요

### 목적

억제(정비 창)를 **반복 규칙**으로 지정할 수 있게 한다. 현행은 시작~끝 **연속 1구간**만 가능해,
"6주간 평일 업무시간에만 억제" 같은 실제 정비 패턴을 표현하지 못한다.

### 배경 및 동기

PM 요구 원문:

> 예를 들어서 시작이 20260809~20260920 까지 월~금 08:00~21:00 이런식으로 반복적으로 정할 수 있는 게
> 필요하다. 또한 제한기간 없음으로 해서 월~금 08:00~21:00 이렇게 넣을 수도 있어야겠지.

현행 구조로는 이를 표현하려면 **6주 × 5일 = 30개 창을 수동 생성**해야 하고, 무제한은 아예 불가능하다.

### 현행 구조의 핵심 전제 (이번에 깨지는 것)

```python
# app/services/event_suppression_service.py:110-111  (게이트)
EventSuppressionSchedule.window_start <= n,
EventSuppressionSchedule.window_end > n,
```

**"억제 여부 = 단일 timestamptz 구간 포함"** 이라는 전제가 코드 **8지점**에 박혀 있다:

| # | 위치 | 역할 |
|---|---|---|
| 1 | `event_suppression_service.py:110-111` | 게이트 후보 SQL (**가장 뜨거운 경로**) |
| 2 | `event_suppression_service.py:81-87` | `suppression_status()` 파생 상태 |
| 3 | `event_suppression_service.py:206-208` | `get_active_schedules()` — `/active` |
| 4 | `event_suppression_service.py:234` | `run_suppression_sweep()` |
| 5 | `routers/event_suppression_schedules.py:206-213` | 목록 status 필터 (SQL) |
| 6 | `db_triggers.py:591,607` | `fn_suppression_status()` SQL 함수 (NATS status) |
| 7 | `services/suppression_scheduler.py:128-130,167` | 창 경계 date-job |
| 8 | `models/event_suppression.py:67-68` | `ix_suppression_gate_window` 인덱스 |

---

## 2. 요구사항

### 기능 요구사항

| ID | 요구사항 | 우선순위 | 예상 태스크 수 |
|----|---------|---------|--------------|
| **FR-01** | 스키마 확장 — `recurrence_type`·`days_of_week`·`daily_start`·`daily_end` 신설(**`schedule_tz` 컬럼 없음** — §3.1-A), `window_end` **NULL 허용**. 마이그 v72 | **High** | ~4개 |
| **FR-02** | `current_occurrence(sched, now)` 도입 — 현재 occurrence `(start,end)` 반환. **모든 시간 판정의 단일 원천** | **High** | ~5개 |
| **FR-03** | 게이트(`is_suppressed`) 재작성 — SQL 1차 필터(유효기간·scope·revoked)로 좁힌 뒤 **파이썬에서 `current_occurrence` 평가** | **High** | ~4개 |
| **FR-04** | `status` **4종 고정 유지** + **`is_suppressing_now: bool`** 신규 필드. `idle` 값 **도입 금지** | **High** | ~3개 |
| **FR-05** | 응답에 **`occurrence_start` / `occurrence_end` / `next_occurrence_start`** 추가 — 소비자 fail-safe 재정의 | **High** | ~4개 |
| **FR-06** | `/active` 정의 확정 — **"현재 occurrence 가 진행 중인 창"** 만 반환 | **High** | ~2개 |
| **FR-07** | 스케줄러 — 반복 창은 **occurrence 경계 잡을 걸지 않음**. 유효기간 경계(`valid_from`/`valid_until`)만 date-job | **High** | ~4개 |
| **FR-08** | NATS — **occurrence 전이 미발행**. `SYNC_EVENT_SUPPRESSION` 은 **CRUD·유효기간 전이**에만. 브로커 명세 §9.12 개정 | **High** | ~3개 |
| **FR-09** | SQL 트리거 `fn_suppression_status()` — 반복 창은 **유효기간 기준 status** 만 계산(occurrence 미평가) | **High** | ~3개 |
| **FR-10** | 목록 `status` 필터 재작성 — 반복 창은 유효기간 기준. **`is_suppressing_now` 필터는 파이썬 후처리** | **Mid** | ~3개 |
| **FR-11** | 입력 검증 — 요일 비트 범위·`daily_*` 필수·`valid_from<valid_until`·**최대 유효기간 상한**(하드닝 §4-G 연계) | **Mid** | ~3개 |
| **FR-12** | 겹침 판정 재정의 — **요일 교집합 ∧ 시각 구간 교집합** (I-8) | **Low** | ~3개 |
| **FR-13** | 하위호환 — 기존 단발 창 **무변경 동작**. `recurrence_type='none'` 기본값 | **High** | ~2개 |
| **FR-14** | 테스트 — 시뮬레이션 119 시나리오를 **pytest 로 이식**(오라클 차등 포함) | **High** | ~5개 |
| **FR-15** | 5중 싱크 — REST 명세 §6.8 · 브로커 v1.7 · Swagger · Image · Container + 서브시스템 문서 | **Mid** | ~4개 |

### 비기능 요구사항

| ID | 항목 | 요구사항 | 검증 방법 |
|----|------|---------|---------|
| NFR-01 | 게이트 성능 | 활성 스케줄 100개에서 **요청당 ≤1ms** | 실측(2회차 I-6: **0.271ms** 확보) |
| NFR-02 | 정확성 | 요일·시각 판정은 **로컬 타임존(기본 Asia/Seoul)** 기준. UTC 요일 사용 금지 | 시나리오 E군(79검사) — KST 월 00:30 케이스 |
| NFR-03 | 자정 넘김 | `daily_start > daily_end` 인 야간 창 정상 동작 | 시나리오 D군(105검사) |
| NFR-04 | 경계 정밀 | 반열린 구간 `[start, end)` — 시작 정각 억제, 종료 정각 미억제 | probe ±1초/±1분 |
| NFR-05 | 하위호환 | 기존 단발 창 회귀 0 | 시나리오 A군(87검사) + 기존 47 테스트 |
| NFR-06 | 계약 호환 | `status` 4종·NATS `action` 3종 **무변경** | .NET 파서 계약 테스트 |
| NFR-07 | 발행량 | 반복 창 도입으로 NATS 발행량 **증가 없음** | 전이 발행 카운트(목표 0) |
| NFR-08 | 5중 싱크 | 코드·Swagger·명세·Image·Container 일치 | 배포 후 `openapi.json` 대조 |

---

## 3. 기술 설계

### 3.1 데이터 모델 (확정)

```sql
-- 마이그레이션 v72 (멱등)
ALTER TABLE event_suppression_schedules
    ADD COLUMN IF NOT EXISTS recurrence_type VARCHAR(16) NOT NULL DEFAULT 'none',
    ADD COLUMN IF NOT EXISTS days_of_week    SMALLINT     NULL,   -- 비트마스크 Mon=1..Sun=64
    ADD COLUMN IF NOT EXISTS daily_start     TIME         NULL,   -- 로컬 벽시계
    ADD COLUMN IF NOT EXISTS daily_end       TIME         NULL;

ALTER TABLE event_suppression_schedules ALTER COLUMN window_end DROP NOT NULL;  -- 무제한 반복
```

| 컬럼 | 의미 (`none`) | 의미 (`weekly`) |
|---|---|---|
| `window_start` | 창 시작 | **유효기간 시작** (`valid_from`) |
| `window_end` | 창 끝 (필수) | **유효기간 끝** — **NULL = 무제한** |
| `days_of_week` | — | 요일 비트마스크 (월=1 … 일=64) |
| `daily_start`/`daily_end` | — | 일일 반복 시각 (**로컬 벽시계**) |
| ~~`schedule_tz`~~ | — | **컬럼 없음** — 서버 `DISPLAY_TIMEZONE` 단일 원천(§3.1-A) |

> **컬럼 재사용 근거**: `valid_from`/`valid_until` 을 새로 만들지 않고 `window_start`/`window_end` 를
> 재해석한다. 인덱스·SQL 필터·기존 소비자 필드명이 그대로 살아 하위호환 비용이 가장 낮다.
> 대신 **의미가 모드에 따라 갈리므로 문서에 반드시 명시**한다.

### 3.1-A 타임존 — 컬럼 없음 / 서버 `DISPLAY_TIMEZONE` 단일 원천 (확정)

당초 `schedule_tz VARCHAR(64)` 컬럼 안이었으나 **제거**한다. PM 지시("타임존은 .env 설정을 따라가자")와
명세 §3.4(datetime-unification Option B — "해외 재배포 시 `DISPLAY_TIMEZONE` 만 바꾸면 된다")에 부합한다.

| 항목 | 확정 |
|---|---|
| 판정 tz | **`settings.display_tz`** (= `DISPLAY_TIMEZONE`). `settings.tz`(TIMEZONE) **참조 금지** |
| 컬럼 | **없음** |
| **응답 필드 `schedule_tz`** | **읽기전용으로 존치** — `_to_response()` 에서 `settings.DISPLAY_TIMEZONE` 투영 |
| 요청 필드 | **받지 않음**. `extra="forbid"` 라 보내면 **422** |
| UI | 미노출 (D-C 확정) |

**응답 필드를 남기는 이유** — 컬럼과 함께 응답까지 지우면 소비자가 tz 를 알 방법이 **완전히 사라진다**:
`daily_start`/`daily_end` 는 offset 없는 `TIME` 이고, 서버 tz 를 노출하는 엔드포인트가 없다.
그러면 .NET 소비자는 `"Asia/Seoul"` 하드코딩 또는 클라 PC 로컬 tz 중 택일하게 되는데 둘 다 서버와 갈릴 수 있다.
읽기전용 노출은 **되돌림 비용도 소멸**시킨다 — 부대별 tz 요구가 생기면 컬럼만 추가하면 되고 REST/NATS 계약 변경은 0.

---

### 3.1-B ★ 유효기간 입력은 명세 §3.4 "혼용 수용" 규약을 그대로 따른다

`window_start`/`window_end` 는 기존 datetime 입력 규약을 **변경 없이** 적용한다.

| 입력 형태 | 해석 |
|---|---|
| `"2026-08-09T00:00:00+09:00"` (offset) | 그대로 instant (**권장**) |
| `"2026-08-09T00:00:00Z"` | 그대로 instant |
| `"2026-08-09T00:00:00"` (naive) | `DISPLAY_TIMEZONE` 벽시계로 간주 후 UTC 변환 |
| **`"2026-08-09"`** (date-only) | 해당 TZ **00:00** |

> **끝일 처리(중요)**: PM 요구 원문은 `20260809~20260920` 처럼 **날짜만**이다.
> `window_end="2026-09-20"` 을 그대로 쓰면 `09-20 00:00` 이 되어 **09-20 하루가 통째로 빠진다.**
> 명세 §3.4 의 리포트 규약("끝일이 자정·date-only 면 그날 23:59:59.999999 로 자동 확장")과 동일하게,
> **`window_end` 가 date-only 또는 자정으로 오면 그날 끝까지 포함하도록 자동 확장**한다(FR-11).
> → `20260809~20260920` 입력 시 실제 유효기간은 `08-09 00:00 ~ 09-21 00:00` 이 된다.

`daily_start`/`daily_end` 는 **offset 없는 순수 `time`** 이다(§3.4 의 "offset 필수"는 datetime 필드 대상).
offset 이 실려 오면 **422** 로 거절한다 — pydantic v2 는 tz-aware time 을 조용히 수용하고
`datetime.combine(..., tzinfo=zone)` 이 이를 덮어써 **9시간 조용한 오해석**이 나기 때문이다(FR-11).

---

### 3.2 판정 로직 — 단일 원천 `current_occurrence()`

시뮬레이션 검증본(`docs/analyses/recurrence-sim/model.py`)을 그대로 이식한다.

```python
def current_occurrence(s, now_utc, zone: ZoneInfo) -> tuple[datetime, datetime] | None:
    if s.revoked_at and s.revoked_at <= now_utc: return None
    if s.recurrence_type == "none":
        return (s.window_start, s.window_end) if s.window_start <= now_utc < s.window_end else None
    # weekly
    if not (s.days_of_week and s.daily_start and s.daily_end): return None
    if s.window_start and now_utc < s.window_start: return None      # 유효기간 전
    if s.window_end and now_utc >= s.window_end:    return None      # 유효기간 후
    # ★ zone 은 호출부에서 settings.display_tz 를 1회 주입 (D-4)
    now_local = now_utc.replace(tzinfo=UTC).astimezone(zone)
    for day_offset in (0, -1):        # ★ 자정 넘김 대응 — 어제 시작분도 검사
        d = (now_local + timedelta(days=day_offset)).date()
        if not (s.days_of_week & (1 << d.weekday())): continue       # ★ 로컬 요일
        st_l = datetime.combine(d, s.daily_start, tzinfo=zone)
        end_day = d if s.daily_end > s.daily_start else d + timedelta(days=1)
        en_l = datetime.combine(end_day, s.daily_end, tzinfo=zone)
        st, en = to_naive_utc(st_l), to_naive_utc(en_l)
        st = max(st, s.window_start) if s.window_start else st       # 유효기간 클램프
        en = min(en, s.window_end) if s.window_end else en
        if st < en and st <= now_utc < en: return (st, en)
    return None
```

**설계 결정 3건** (시뮬레이션으로 검증됨):

| ID | 결정 | 근거 |
|---|---|---|
| **D-1** | 요일·시각은 **로컬 타임존** 기준 | UTC 요일이면 **KST 월요일 00:00~09:00 이 UTC 일요일**이 되어 "월~금"에서 빠짐. 시나리오 **E01** 로 검증 |
| **D-2** | 유효기간이 occurrence 중간을 자르면 **부분 occurrence 허용** (클램프) | 시나리오 **B16/B17/D06/D07** — 유효기간 경계가 창 한가운데인 케이스 |
| **D-3** | `daily_start == daily_end` 는 **24시간 종일**로 해석 | 0길이보다 의도에 부합. 시나리오 **H01** |
| **D-4** | 판정 tz = **`settings.display_tz`(DISPLAY_TIMEZONE)** 고정. `settings.tz`(TIMEZONE) **참조 금지** | 응답 `occurrence_*` 가 전역 인코더(`app/main.py:32`)로 **DISPLAY_TZ 렌더**된다. 판정과 렌더가 같아야 "`daily_start=08:00` 으로 만든 창이 08:00 으로 보인다"가 성립. naive 입력 해석(`app/models/types.py:33`)도 같은 값 → 입력·판정·표시 단일 정렬. `TIMEZONE` 은 마이그 origin 전용(`config.py:155`) |

### 3.3 I-1 해법 — 게이트: SQL 1차 필터 + 파이썬 평가

```python
# 1차: DB 가 좁힐 수 있는 것만 (revoked / 유효기간 / scope)
stmt = select(EventSuppressionSchedule).where(
    EventSuppressionSchedule.revoked_at.is_(None),
    or_(EventSuppressionSchedule.window_start.is_(None),
        EventSuppressionSchedule.window_start <= n),
    or_(EventSuppressionSchedule.window_end.is_(None),
        EventSuppressionSchedule.window_end > n),
    EventSuppressionSchedule.event_scope.in_([ALL, scope_for_category]),
).order_by(EventSuppressionSchedule.id)

# 2차: 파이썬에서 occurrence 평가 (요일·시각은 SQL 로 표현 불가)
for c in candidates:
    if current_occurrence(c, n) is None: continue
    ... 기존 대상 매칭 로직 ...
```

> **성능 근거(실측)**: 2회차 I-6 — 스케줄 **1개 0.003ms / 10개 0.027ms / 50개 0.136ms /
> 100개 0.271ms**. 이벤트 수신 hot path 에서도 충분하다. **인덱스 `ix_suppression_gate_window`
> 는 유효기간 1차 필터에 그대로 유효**하므로 유지한다.

### 3.4 I-4·I-7 해법 — 응답 필드 신설

| 신규 필드 | 타입 | 의미 |
|---|---|---|
| `is_suppressing_now` | bool | **지금 이 순간 억제 중인가** (모든 판단의 기준) |
| `occurrence_start` | datetime \| null | 현재 occurrence 시작 (억제 중일 때만) |
| `occurrence_end` | datetime \| null | **현재 occurrence 끝** — 소비자 로컬 타이머 기준 |
| `next_occurrence_start` | datetime \| null | 다음 occurrence 시작 (없으면 null) |

**fail-safe 계약 재정의** (기존 §2.8 대체):

```
[기존] 캐시한 window_end 로컬 타이머 만료로 해제        ← 무제한 반복에서 값이 없음
[신규] 캐시한 occurrence_end 로컬 타이머 만료로 해제    ← 항상 유효
       + GET /active 30~60초 폴링은 여전히 권위
       + 캐시 TTL(폴링주기×3) 초과 시 fail-open
```

### 3.5 I-2·I-3 해법 — occurrence 전이는 NATS 미발행

**측정**: 무제한 월~금 08:00~21:00 = **연 520건** 전이. 창 50개면 **연 26,000건**.

**확정**: occurrence 시작/종료는 **발행하지 않는다.**

| 발행 대상 | 발행? |
|---|---|
| 스케줄 생성/수정/대상교체/취소/하드삭제 | ✅ (기존대로) |
| **유효기간** 전이 (pending→active, active→expired) | ✅ (기존 date-job 유지) |
| **occurrence** 전이 (일일 08:00 시작 / 21:00 종료) | ❌ **미발행** |

**정당성**:
1. 반복 규칙은 **결정적(deterministic)** — 소비자가 규칙만 알면 로컬에서 정확히 계산 가능.
   1회차 시뮬레이션이 **독립 구현 2개가 616검사 전건 일치**함을 보여 이를 실증했다.
2. `/active` 폴링(30~60초)이 **이미 권위**이므로 최대 60초 내 자동 수렴.
3. 응답의 `occurrence_end`/`next_occurrence_start` 로 소비자가 정밀 타이머를 걸 수 있다.

→ **NFR-07 달성**: 반복 도입으로 NATS 발행량 증가 **0**. FR-07(스케줄러)도 자동 해결
(무제한 occurrence 잡을 걸 필요가 없어짐 = **I-3 소멸**).

### 3.6 I-5 해법 — status 4종 고정 + `is_suppressing_now` 분리

**측정**: PM요구1 기준, 유효기간 내인데 억제 안 하는 시간이 **62.2%**.

`idle` 을 status 에 추가하면 `.NET` 강타입 파서가 깨진다(SYNC 설계에서 `action` 3종을 고정한 것과 동일 논리).

| | 반복 창에서의 의미 |
|---|---|
| `status` (**4종 고정**) | `pending`=유효기간 전 / `active`=**유효기간 내** / `expired`=유효기간 후 / `cancelled` |
| **`is_suppressing_now`** | **지금 억제 중인가** — 배너·필터·게이트 판단은 전부 이 값 |

> ⚠ **반복 창에서 `status=active` 는 "지금 억제 중"을 뜻하지 않는다.** 62.2% 는 active 이면서
> 억제하지 않는 상태다. 소비자는 반드시 `is_suppressing_now` 를 봐야 한다.

### 3.7 FR-09 — SQL 트리거는 유효기간만 계산

`fn_suppression_status()` 에서 요일·타임존 반복을 평가하는 것은 과도하다.
→ 반복 창은 **유효기간 기준 status** 만 계산(파이썬과 동일 결과). occurrence 는 SQL 이 보지 않는다.
NATS `status` 필드도 같은 의미이므로 §3.5(occurrence 미발행)와 일관된다.

### 3.8 I-8 해법 — 겹침 판정 재정의

```
겹침(A,B) = 유효기간 교집합 ≠ ∅
          ∧ (A.days_of_week & B.days_of_week) ≠ 0        # 요일 교집합
          ∧ 시각구간 교집합 ≠ ∅                            # 자정 넘김 정규화 후
```

측정: A(월 08–12)와 B(토 08–12)는 유효기간 100% 겹치지만 **실제 occurrence 는 절대 안 겹침**.

---

## 4. 범위

### In Scope

- `app/models/event_suppression.py` · `app/schemas/event_suppression.py` · 마이그 **v72**
- `app/services/event_suppression_service.py` — `current_occurrence`/게이트/status//active/sweep
- `app/services/suppression_scheduler.py` — 유효기간 경계만 잡
- `app/routers/event_suppression_schedules.py` — 응답 필드·목록 필터·겹침·검증
- `app/db_triggers.py` — `fn_suppression_status()` 유효기간 기준
- `tests/test_event_suppression_recurrence.py` — 시뮬 119 시나리오 이식
- REST 명세 §6.8 · 브로커 명세 **v1.7 §9.12** · `docs/subsystems/event-suppression/` 전량

### Out of Scope

- **월간/연간 반복**(매월 첫째 주 월요일 등) — `recurrence_type` 확장 여지만 남김
- **RRULE(RFC 5545) 전면 채택** — 구조화 컬럼 대비 SQL·UI 비용 과다
- **예외일(holiday exclusion)** — 후속 PRD
- 기존 `recurrence_rule` 문자열 컬럼 활용 — **데드 필드로 유지**(하드닝 PRD 소관)
- 소비자(.NET) 구현 — 각 팀 소관

---

## 5. 의존성 및 전제 조건

| 항목 | 내용 |
|---|---|
| 브랜치 | `release/v6.3` (HEAD `71ee278`) |
| **롤백 포인트** | 착수 전 `pre-v6.3-event_suppression_recurrence` 태그 **필수** + 이미지 태그 |
| 마이그레이션 | **v72** (컬럼 5개 추가 + `window_end` NOT NULL 해제) |
| 선행 | 하드닝 PRD FR-01(PATCH 500) — **이미 반영 완료**(`b92082f`) |
| 배포 순서 | db-monitor → api-server (기존 규율 유지) |

---

### 5-C. 선행 조건 — `DISPLAY_TIMEZONE` 컨테이너 배선 (**FR-01 착수 전 필수**) ✅ 완료

`schedule_tz` 컬럼 제거는 tz 를 서버 설정으로 이관하는 결정인데, **호스트 `.env` 값이 컨테이너에
도달하지 못하는 구멍**이 있었다. 실측으로 확인하고 **선조치 완료**했다.

| 확인 항목 | 조치 전 (실측) | 조치 후 (실측) |
|---|---|---|
| `.dockerignore:53-54` | `.env`/`.env.*` 제외 → 이미지에 `.env` 없음 | (동일 — 시크릿 보호 유지) |
| 컨테이너 `/app/.env` | **없음** | (동일) |
| `docker-compose.yml` `env_file:` | **없음** | (동일) |
| api-server `environment:` tz 키 | **없음** (`TZ=Asia/Seoul` 만, `case_sensitive=True` 라 미매핑) | **`DISPLAY_TIMEZONE`/`TIMEZONE` 추가** |
| 컨테이너 `settings.DISPLAY_TIMEZONE` | `Asia/Seoul` (**코드 기본값**) | `Asia/Seoul` (**env 주입값**) |

조치 내역:
1. `docker-compose.yml` api-server `environment:` — `DISPLAY_TIMEZONE`/`TIMEZONE`/`TZ` 를
   `${DISPLAY_TIMEZONE:-Asia/Seoul}` 치환으로 배선. compose 는 호스트 `.env` 를 `${}` 치환용으로
   자동 로드하므로 `.dockerignore` 를 우회해 값이 전달된다.
2. `postgres` `PGTZ: ${DISPLAY_TIMEZONE:-Asia/Seoul}` — 단일 원천화(timestamptz 는 절대시각이라
   기존 데이터 무영향, 리포트 `date_trunc` 일별 버킷의 잠복 불일치도 동시 해소).
3. `.env.example` 에 `DISPLAY_TIMEZONE`/`TIMEZONE` 키 등재.
4. `app/config.py` 주석 — "`TZ` 는 `case_sensitive=True` 라 이 필드에 매핑되지 않는다" 명시.

검증: `DISPLAY_TIMEZONE=Europe/Budapest docker compose config` → 치환 확인. 재기동 후 컨테이너
`env` 에 `DISPLAY_TIMEZONE` 실재 + `settings.display_tz` 반영 확인.

> ※ 이 구멍은 반복 스케줄 이전에 **기존 §3.4 규약의 실제 결함**이었다 —
> 명세는 "해외 재배포 시 `DISPLAY_TIMEZONE` 만 바꾸면 된다"고 약속하는데 실제로는 안 바뀌었다.

---

### 5-D. `DISPLAY_TIMEZONE` 운영 중 변경은 **파괴적 변경**

컬럼이 없으므로 tz 가 행이 아니라 **프로세스 설정에 종속**된다. `window_start`/`window_end` 는
timestamptz(절대시각)라 안 움직이지만 `daily_start`/`daily_end` 는 `TIME`(벽시계)이라
**저장된 모든 `weekly` 창의 실제 억제 구간이 소급 이동**한다(08:00 KST → 08:00 CET = 8시간 이동).

**그리고 이 이동은 어디에도 기록되지 않는다** — 행 UPDATE 가 없어 `trg_notify_suppression_sync` 미발화
(SYNC 0건), sweep 백스톱은 유효기간 기준 status 만 비교하므로 미검출, 감사 로그는 CRUD 에만 걸린다.

| # | 방어 | 위치 |
|---|---|---|
| 1 | 기동 로그에 `DISPLAY_TIMEZONE` 출력 (+ `TIMEZONE` 과 다르면 WARN) | `app/main.py` 부팅 로그 |
| 2 | **지속 fingerprint** — 마지막 기동 tz 저장, 불일치 **AND** `weekly` 행 존재 시 강한 WARN 을 `system_events` 에 기록 | 신규(v72 동반) |
| 3 | 소비자 자동 감지 — 응답 `schedule_tz` 값 변화 시 로컬 계산 캐시 무효화 | RECURRENCE.md §9 |

**되돌림**: 부대별 tz 요구 발생 시 `schedule_tz` 컬럼 추가 + 현재 `DISPLAY_TIMEZONE` 으로 백필.
응답 필드는 이미 존재하므로 **REST/NATS 계약 변경 0**, 마이그 1회로 끝난다.

---

## 5-A. 검증 필요 항목

| ID | 검증 항목 | 검증 방법 | 확인 여부 |
|----|---------|---------|---------|
| V-01 | occurrence 판정 정확성 | **완료** — 1회차 119시나리오/616검사 불일치 0 (`sim_round1.log`) | **확인** |
| V-02 | 게이트 성능 | **완료** — 100개 0.271ms (`sim_round2.log` I-6) | **확인** |
| V-03 | `window_end` NOT NULL 해제가 기존 코드에 미치는 영향 전수 | 8지점 null 가드 추가 후 회귀 | 미확인 |
| V-04 | `.NET` 소비자가 `is_suppressing_now` 신규 필드를 무시해도 안전한지 | 각 팀 회신 | 미확인 |
| V-05 | **D-2(부분 occurrence 클램프)** 가 운영 의도와 맞는지 | PM 결정 | **미확인** |
| V-06 | **D-3(`daily_start==daily_end` = 24시간)** 이 의도와 맞는지 | PM 결정 | **미확인** |
| V-07 | 유효기간 최대 상한 값 | PM 결정(하드닝 §4-G 연계) | 미확인 |
| V-08 | `schedule_tz` 를 UI 에 노출할지(전부 Asia/Seoul 고정할지) | PM 결정 | 미확인 |

---

## 5-B. 인과 결합 분석

| 수정 항목 | 영향 받는 다른 플로우 | 대응 방안 |
|---|---|---|
| `window_end` NULL 허용 | **8지점 전부** — 특히 sweep(`window_end <= now`), 인덱스, 스키마 검증 | 각 지점에 null 가드. sweep 은 `window_end IS NOT NULL AND ...` |
| 게이트 파이썬 평가 전환 | 이벤트 수신 3핸들러 hot path | 성능 실측 완료(NFR-01). fail-open 유지 |
| `status` 의미 변경(반복 창에서 active≠억제중) | GIS 배너·목록 배지·NATS status·SQL 필터 | **`is_suppressing_now` 신규 필드로 분리**, 문서에 대문짝만하게 명시 |
| occurrence 전이 미발행 | SYNC 소비자의 "수신 시 재조회" 흐름 | 폴링이 권위라 무해. 문서에 "반복 창은 전이 알림 없음" 명시 |
| `/active` 정의 변경 | 배너·Phase 2 라이브 필터 | 의미가 **더 정확해지는 방향**(현재 억제 중만) |
| 겹침 판정 변경 | 하드닝 PRD §4-B(겹침 경고) | 하드닝 FR-04 와 **동시 설계** 필요 |
| 기존 단발 창 | — | `recurrence_type='none'` 기본값으로 **무변경**(A군 87검사 통과) |

---

## 6. 리스크

| 리스크 | 가능성 | 영향 | 대응 |
|--------|--------|------|------|
| 소비자가 `status=active` 를 "지금 억제 중"으로 오해 | **높음** | **높음** | `is_suppressing_now` 필수화 + 전 문서 경고. **62.2% 오판** 실측치 제시 |
| `window_end` NULL 가드 누락으로 런타임 500 | 중 | 높음 | 8지점 체크리스트 + 회귀 테스트 |
| D-2/D-3 설계 결정이 운영 의도와 다름 | 중 | 중 | V-05·V-06 **선결재** |
| 타임존 오설정(요일이 UTC 기준) | 낮음 | **매우 높음** | E군 시나리오를 pytest 로 이식(회귀 고정) |
| 자정 넘김 창 오동작 | 중 | 높음 | D군 105검사 이식 |
| 반복 규칙 로컬 계산을 각 팀이 다르게 구현 | 중 | 중 | 의사코드 + **테스트 벡터** 문서 제공 |

---

## 7. 완료 기준 (DoD)

- [ ] FR-01 ~ FR-15 구현 완료
- [ ] NFR-01 ~ NFR-08 검증 통과
- [ ] V-01·V-02 **완료**(시뮬레이션), V-03~V-08 확인
- [ ] **시뮬레이션 119 시나리오를 pytest 로 이식** — 오라클 차등 포함, 전건 통과
- [ ] 기존 억제 테스트 **47건 회귀 0**
- [ ] 라이브 E2E — PM 요구 2케이스(기간 있음/무제한) 실제 억제·해제 확인
- [ ] NATS 발행량 회귀 — 반복 창 운영 중 occurrence 전이 발행 **0건** 실측
- [ ] 5중 싱크 + 서브시스템 문서(통합본 포함) 갱신
- [ ] 롤백 태그 생성 확인

---

## 8. PM 결정 요청

| ID | 항목 | 선택지 | 권고 |
|----|------|-------|------|
| **D-A** | 유효기간이 occurrence 중간을 자를 때 | **부분 허용**(클램프) / 그 occurrence 통째 제외 | **부분 허용** — "09-20까지"면 그날 21:00 아니라 09-20 24:00 기준이 직관적 |
| **D-B** | `daily_start == daily_end` | **24시간 종일** / 422 거절 | **24시간** (또는 UI 에서 아예 못 만들게) |
| **D-C** | `schedule_tz` UI 노출 | 노출 / **Asia/Seoul 고정** | **고정** — 단일 부대 운영이라 혼선만 늘어남 |
| **D-D** | 유효기간 최대 상한 | 무제한 허용 / 상한(예 1년) + 무제한은 별도 플래그 | 무제한은 **명시적 체크박스**로만 |
| **D-E** | occurrence 전이 NATS 발행 | **미발행**(권고) / 발행 | **미발행** — 연 520건×창수, 폴링으로 충분 |

---

## 9. 부록 — 시뮬레이션 산출물

| 파일 | 내용 |
|---|---|
| `docs/analyses/recurrence-sim/model.py` | 후보 구현(서버 이식 대상) |
| `docs/analyses/recurrence-sim/oracle.py` | **독립 오라클** — 완전열거 방식(같은 버그 공유 방지) |
| `docs/analyses/recurrence-sim/scenarios.py` | 119 시나리오 / 616 probe |
| `docs/analyses/recurrence-sim/run_sim.py` | 1회차 러너 |
| `docs/analyses/recurrence-sim/run_sim2.py` | 2회차 러너(통합 실측) |
| **`sim_round1.log`** (1,119행) | 전 케이스 라인 로그 — `OK/FAIL`·occurrence 구간·status |
| **`sim_round2.log`** (126행) | 접합면 실측 + 이슈 7건 |

### 시나리오 카테고리별 결과 (1회차)

| 카테고리 | 검사 | 실패 | 내용 |
|---|---|---|---|
| one-shot | 87 | **0** | 기존 단발 창 하위호환 |
| weekly-bounded | 211 | **0** | 기간 있는 주간 반복(PM 요구 1) |
| weekly-unbounded | 65 | **0** | 무제한 반복(PM 요구 2) |
| overnight | 105 | **0** | 자정 넘김(22:00~06:00 등) |
| timezone | 79 | **0** | KST/UTC 요일 함정·DST |
| status | 12 | **0** | 상태 파생 |
| next-transition | 30 | **0** | 스케줄러 전이 계산 |
| guard | 27 | **0** | 이상 입력 방어 |
| **합계** | **616** | **0** | |
