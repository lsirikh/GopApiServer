# 이벤트 억제 — **반복 스케줄** 서브시스템 연동 안내 (예정 변경)

> **상태: 설계 확정 · 구현 착수 전.** 이 문서는 **사전 통지**입니다.
> 배포 시점에 [INTEGRATION.md](INTEGRATION.md) §6 으로 흡수되며, 그때 이 파일은 포인터가 됩니다.

- **문서 버전**: v1.0 · **작성일**: 2026-08-04
- **대상 API**: 6.3.2 → **6.4** (예정) · **브로커 명세 v1.7 §9.12 개정 예정**
- **PRD**: `docs/prds/event-suppression-recurrence-prd.md`
- **검증 근거**: 시뮬레이션 2회차 실측 (`docs/analyses/recurrence-sim/`, 119시나리오 / 616검사)

---

## 0. 두괄식 — 무엇이 바뀌나

정비 창을 **반복 규칙**으로 지정할 수 있게 됩니다.

```
"2026-08-09 ~ 2026-09-20, 월~금 08:00~21:00"     ← 기간 있는 반복
"기간 제한 없음,          월~금 08:00~21:00"     ← 무제한 반복
```

### 팀별 영향 (한눈에)

| 서브시스템 | 필수 대응 | 난이도 |
|---|---|---|
| **GIS** | ★ 반복 설정 UI(요일 다중선택 + 일일 시각) · **`is_suppressing_now` 로 배너 판단** · occurrence 필드 표시 | **높음** |
| **PidsProxy** | **`is_suppressing_now`** 로 판단 · `occurrence_end` 로 로컬 타이머 | 중 |
| **AiAnalysis** | 동일 | 중 |
| **VMS** | 동일 | 중 |
| **NVRManager** | 동일 | 중 |
| **BroadcastingManager** | 동일 | 낮 |
| **Central** | 동일 (폴링) | 중 |
| **db_monitor** | 서버측 — 변경 없음 | — |

### ★★ 전 팀 필독 — 딱 3가지

1. **`status=active` 가 더 이상 "지금 억제 중"을 뜻하지 않습니다.**
   반복 창에서 `active` 는 **유효기간 내**라는 뜻일 뿐입니다.
   **실측: 유효기간의 62.2% 가 `active` 이면서 억제하지 않는 시간이었습니다.**
   → 억제 판단은 **반드시 신규 필드 `is_suppressing_now`** 로 하세요.

2. **`window_end` 가 `null` 일 수 있습니다** (무제한 반복).
   기존 fail-safe 계약("`window_end` 로컬 타이머로 해제")이 **성립하지 않습니다.**
   → 타이머 기준을 **`occurrence_end`** 로 바꾸세요.

3. **반복 창은 occurrence 전이(매일 08:00 시작 / 21:00 종료)를 NATS 로 알리지 않습니다.**
   `SYNC_EVENT_SUPPRESSION` 은 **정의 변경(CRUD)과 유효기간 전이**에만 옵니다.
   → 일일 전이는 **`GET /active` 폴링(30~60초)** 또는 응답의 `occurrence_end` 타이머로 파악하세요.
   (측정: 무제한 반복 1개가 occurrence 전이를 발행하면 **연 520건**, 창 50개면 **연 26,000건** — 그래서 안 보냅니다)

---

## 1. 요청 필드 (신규)

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `recurrence_type` | enum | | **`none`**(기본, 기존 단발) \| `weekly` |
| `days_of_week` | int | `weekly` 시 ✔ | **요일 비트마스크** — 월=1, 화=2, 수=4, 목=8, 금=16, 토=32, 일=64 |
| `daily_start` | time | `weekly` 시 ✔ | 일일 시작 (**로컬 벽시계**, `"08:00:00"`) |
| `daily_end` | time | `weekly` 시 ✔ | 일일 종료 (`"21:00:00"`) |
| `schedule_tz` | string | | 기본 `Asia/Seoul` (UI 미노출 권고) |

### `window_start` / `window_end` 의 의미가 모드에 따라 달라집니다 ★

| | `recurrence_type=none` (기존) | `recurrence_type=weekly` (신규) |
|---|---|---|
| `window_start` | 창 시작 | **유효기간 시작** |
| `window_end` | 창 끝 (**필수**) | **유효기간 끝** — **`null` 허용 = 무제한** |

### 요일 비트마스크

```
월  1     화  2     수  4     목  8     금 16     토 32     일 64

월~금  = 1+2+4+8+16 = 31
주말   = 32+64      = 96
매일   = 127
월수금 = 1+4+16     = 21
```

---

## 2. 요청 예시

### 2.1 PM 요구 1 — 기간 있는 반복

```json
POST /api/event-suppression-schedules
{
  "name": "GOP 3구역 펜스 보수 (평일 주간)",
  "target_type": "device",
  "target_device_ids": [1351, 1352],
  "event_scope": "all",

  "recurrence_type": "weekly",
  "days_of_week": 31,                       // 월~금
  "daily_start": "08:00:00",
  "daily_end":   "21:00:00",

  "window_start": "2026-08-09T00:00:00+09:00",   // 유효기간 시작
  "window_end":   "2026-09-21T00:00:00+09:00"    // 유효기간 끝
}
```

### 2.2 PM 요구 2 — 무제한 반복

```json
{
  "name": "상시 야간 정비 창",
  "target_type": "all",
  "event_scope": "malfunction",

  "recurrence_type": "weekly",
  "days_of_week": 31,
  "daily_start": "08:00:00",
  "daily_end":   "21:00:00",

  "window_start": "2026-08-09T00:00:00+09:00",
  "window_end":   null                      // ★ 무제한
}
```

### 2.3 야간 창 (자정 넘김) — 지원됩니다

```json
{
  "recurrence_type": "weekly",
  "days_of_week": 31,
  "daily_start": "22:00:00",
  "daily_end":   "06:00:00"      // start > end → 다음날 06:00 까지
}
```

> 월요일 22:00 에 시작한 창은 **화요일 06:00** 에 끝납니다.
> 금요일 22:00 시작분은 **토요일 06:00** 까지 이어집니다(토요일이 미선택이어도).

---

## 3. 응답 필드 (신규) ★ 가장 중요

```json
{
  "id": 42,
  "recurrence_type": "weekly",
  "days_of_week": 31,
  "daily_start": "08:00:00",
  "daily_end": "21:00:00",
  "schedule_tz": "Asia/Seoul",
  "window_start": "2026-08-09T00:00:00+09:00",
  "window_end": null,

  "status": "active",                                    // ← 유효기간 내라는 뜻일 뿐!
  "is_suppressing_now": true,                            // ★ 지금 억제 중인가
  "occurrence_start": "2026-08-10T08:00:00+09:00",       // ★ 현재 구간 시작
  "occurrence_end":   "2026-08-10T21:00:00+09:00",       // ★ 현재 구간 끝 (타이머 기준)
  "next_occurrence_start": "2026-08-11T08:00:00+09:00"   // 다음 구간 시작
}
```

| 필드 | 용도 |
|---|---|
| **`is_suppressing_now`** | **모든 억제 판단의 기준.** 배너 표시·발행 skip·녹화 억제 전부 이 값 |
| **`occurrence_end`** | **로컬 타이머 기준.** 이 시각에 억제를 스스로 해제 |
| `next_occurrence_start` | 다음 억제 시작 예고 (배너 "다음 정비 08-11 08:00" 등) |
| `status` | **유효기간** 기준 4종 유지 (`pending`/`active`/`expired`/`cancelled`) |

> `is_suppressing_now=false` 인데 `status=active` 인 상태가 **정상**입니다(평일 밤·주말).
> 단발 창(`recurrence_type=none`)에서는 `status=active` ⇔ `is_suppressing_now=true` 로 일치합니다.

---

## 4. status 4종은 그대로 — 값 추가 없음

`.NET` 강타입 파서 보호를 위해 **`EnumSuppressionStatus` 에 값을 추가하지 않습니다.**

| status | `none` | `weekly` |
|---|---|---|
| `pending` | 창 시작 전 | **유효기간 시작 전** |
| `active` | 창 진행 중 (=억제 중) | **유효기간 내** (억제 중일 수도, 아닐 수도) |
| `expired` | 창 종료 | **유효기간 종료** |
| `cancelled` | 취소 | 취소 |

---

## 5. `GET /active` 의미 확정

**"현재 occurrence 가 진행 중인 창"만** 반환합니다.

- 반복 창이 유효기간 내이지만 지금 08:00~21:00 밖이면 **`/active` 에 나오지 않습니다.**
- 즉 `/active` 에 있는 창은 전부 `is_suppressing_now=true` 입니다.
- 배너는 `/active` 결과를 그대로 쓰면 됩니다.

---

## 6. fail-safe 계약 (개정) ★

```
[기존] 캐시한 window_end 로컬 타이머 만료로 해제
       → 무제한 반복은 window_end 가 null 이라 성립 불가

[개정] 캐시한 occurrence_end 로컬 타이머 만료로 해제      ← 1차 권위
       + GET /active 30~60초 폴링 존치                    ← 권위
       + 캐시 TTL(폴링주기 ×3) 초과 시 억제 해제(fail-open)
```

안전 비대칭은 그대로입니다 — **억제가 안 걸리는 건 허용, 안 풀리는 건 금지.**

---

## 7. 반복 규칙 로컬 계산 (선택 — 즉시성이 필요한 팀만)

occurrence 전이가 NATS 로 오지 않으므로, 60초보다 정밀한 반응이 필요하면 로컬 계산하세요.
**규칙은 결정적**이라 서버와 동일 결과가 나옵니다(독립 구현 2개가 616검사 전건 일치 — 실증됨).

```
is_suppressing(now):
    if revoked_at != null and revoked_at <= now:            return false
    if recurrence_type == "none":
        return window_start <= now < window_end

    if window_start != null and now <  window_start:        return false   # 유효기간 전
    if window_end   != null and now >= window_end:          return false   # 유효기간 후

    now_local = now.ToTimeZone(schedule_tz)                 # ★ 반드시 로컬
    for day_offset in [0, -1]:                              # ★ 자정 넘김 대응
        d = (now_local + day_offset일).Date
        if (days_of_week & (1 << d.DayOfWeekMon0)) == 0:    continue
        start_local = d + daily_start
        end_local   = (daily_end > daily_start ? d : d+1일) + daily_end
        st = start_local.ToUtc();  en = end_local.ToUtc()
        st = max(st, window_start);  en = min(en, window_end)   # null 이면 클램프 없음
        if st < en and st <= now < en:                      return true
    return false
```

### 반드시 지킬 3가지

| # | 규칙 | 안 지키면 |
|---|---|---|
| 1 | **요일은 로컬(KST) 기준** | KST 월요일 00:00~09:00 이 **UTC 일요일**이라 "월~금"에서 빠짐 |
| 2 | **`day_offset = -1` 도 검사** | 자정 넘김 창(22:00~06:00)의 새벽 구간을 통째로 놓침 |
| 3 | **반열린 구간 `[start, end)`** | 종료 정각에 1분 더 억제됨 |

### 테스트 벡터 (구현 검증용 — 서버 실측값)

`days_of_week=31(월~금)`, `daily=08:00~21:00`, `tz=Asia/Seoul`, `window_start=2026-08-09`, `window_end=null`

| now (KST) | 기대 `is_suppressing_now` | 비고 |
|---|---|---|
| 2026-08-10(월) 07:59:59 | `false` | 시작 직전 |
| 2026-08-10(월) 08:00:00 | **`true`** | 시작 정각 포함 |
| 2026-08-10(월) 12:00:00 | `true` | |
| 2026-08-10(월) 20:59:59 | `true` | |
| 2026-08-10(월) 21:00:00 | **`false`** | 종료 정각 **미포함** |
| 2026-08-10(월) 23:30:00 | `false` | |
| 2026-08-15(토) 12:00:00 | `false` | 주말 |
| 2026-08-16(일) 12:00:00 | `false` | 주말 |
| 2027-05-10(월) 12:00:00 | `true` | 무제한이라 계속 |

야간 창 `daily=22:00~06:00`, `days=31(월~금)`:

| now (KST) | 기대 | 비고 |
|---|---|---|
| 2026-08-10(월) 21:59 | `false` | |
| 2026-08-10(월) 22:00 | **`true`** | 월요일분 시작 |
| 2026-08-11(화) 02:00 | **`true`** | **전날 시작분이 이어짐** ← 흔한 버그 지점 |
| 2026-08-11(화) 06:00 | `false` | 종료 정각 |
| 2026-08-15(토) 03:00 | **`true`** | **금요일 시작분이 토요일 새벽까지** |
| 2026-08-15(토) 23:00 | `false` | 토요일은 미선택 |

로컬 요일 함정 검증 — `days_of_week=1(월만)`, `daily=00:00~09:00`:

| now (KST) | 기대 | 비고 |
|---|---|---|
| 2026-08-09(일) 23:30 | `false` | |
| 2026-08-10(월) 00:30 | **`true`** | **UTC 로는 일요일 15:30 — UTC 요일 쓰면 실패** |
| 2026-08-10(월) 08:30 | `true` | |
| 2026-08-10(월) 09:30 | `false` | |

---

## 8. 팀별 상세

### 8.1 GIS — 영향 최대

**반복 설정 UI 신설**

| 입력 | 위젯 |
|---|---|
| 반복 여부 | 라디오: 단발 / **주간 반복** |
| 요일 | **다중 체크박스**(월~일) → 비트마스크 합산 |
| 일일 시각 | 시작·종료 시각 선택 |
| 유효기간 | 시작일 + 종료일 · **"기간 제한 없음" 체크박스**(→ `window_end: null`) |

- **`daily_start == daily_end` 는 24시간으로 해석**됩니다 → UI 에서 막는 걸 권장.
- **자정 넘김**(시작 > 종료)은 정상 입력이므로 "다음날 종료" 안내 문구 표시.

**목록·배지**
- 배지는 `status`(4종) 유지, **"지금 억제 중" 표시는 `is_suppressing_now`**.
- 반복 창은 `"월~금 08:00~21:00"` 요약 문자열을 별도 표시 권장.

**배너**
- `GET /active` 결과 그대로 사용(이제 현재 억제 중인 창만 옴).
- `occurrence_end` 로 "~21:00 까지" 표시, `next_occurrence_start` 로 "다음 08-11 08:00" 예고.

### 8.2 PidsProxy / AiAnalysis

- 202 억제 응답 처리 — **변경 없음**.
- Phase 2 라이브 발행 skip 시 판단을 **`is_suppressing_now`** 로.
- `occurrence_end` 로컬 타이머 + `/active` 폴링 유지.

### 8.3 VMS / NVRManager

- 감시쪽 대상 산출 로직 — **변경 없음**.
- 억제 on/off 판단만 `is_suppressing_now` 로 교체.
- 이벤트 트리거 녹화가 **매일 08:00 꺼지고 21:00 켜지는** 패턴이 되므로,
  녹화 정책(상시 녹화 유지 여부)을 다시 확인하세요.

### 8.4 Central

- NATS 미수신 — `GET /active` 폴링만. 위 계약 그대로 적용.

---

## 9. 체크리스트

**전 팀 공통 (필수)**
- [ ] 억제 판단을 **`is_suppressing_now`** 로 교체 (`status=active` 사용 중단)
- [ ] 로컬 타이머 기준을 **`occurrence_end`** 로 교체 (`window_end` 사용 중단)
- [ ] **`window_end: null`** 수용 (역직렬화 시 nullable)
- [ ] 반복 창에는 occurrence 전이 NATS 가 **오지 않음**을 전제로 폴링 유지
- [ ] `recurrence_type`·`days_of_week`·`daily_*`·`schedule_tz` 신규 필드 파싱(무시해도 안전하나 표시엔 필요)

**GIS 추가**
- [ ] 반복 설정 UI(요일 다중선택 + 일일 시각 + 무제한 체크박스)
- [ ] 비트마스크 합산/역산
- [ ] 반복 요약 문자열 표시("월~금 08:00~21:00")
- [ ] 자정 넘김 안내 · `daily_start==daily_end` 입력 차단
- [ ] 배너에 `occurrence_end` / `next_occurrence_start` 반영

**로컬 계산을 하는 팀만**
- [ ] §7 의사코드 이식
- [ ] §7 **테스트 벡터 전건 통과** (특히 야간 창 화요일 02:00, 로컬 요일 월 00:30)

---

## 10. 미결 — PM 결정 대기

| ID | 항목 | 기본안 |
|----|------|-------|
| D-A | 유효기간이 occurrence 중간을 자를 때 | **부분 허용**(클램프) |
| D-B | `daily_start == daily_end` | **24시간 종일** |
| D-C | `schedule_tz` UI 노출 | **Asia/Seoul 고정** |
| D-D | 유효기간 최대 상한 | 무제한은 명시적 체크박스로만 |
| D-E | occurrence 전이 NATS 발행 | **미발행** |

결정 후 이 문서와 [INTEGRATION.md](INTEGRATION.md) 를 확정본으로 갱신합니다.

---

## 11. 문의

| 항목 | 위치 |
|---|---|
| 현행 계약(반복 도입 전) | [INTEGRATION.md](INTEGRATION.md) |
| PRD | `docs/prds/event-suppression-recurrence-prd.md` |
| 시뮬레이션 증적 | `docs/analyses/recurrence-sim/` (119시나리오 / 616검사 / 로그 1,245행) |
| 담당 | 이기호 차장 |
