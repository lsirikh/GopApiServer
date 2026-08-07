"""시뮬레이션 2회차 — **통합 지점 실측**.

1회차는 occurrence 수학의 내부 정합성만 봤다(불일치 0).
2회차는 실제로 깨지는 곳 = **기존 서버 구조와의 접합면**을 수치로 측정한다.

측정 항목
---------
I-1  게이트 SQL 사전필터 가능성 — 현행은 WHERE 로 후보를 좁히는데 반복 창은 좁혀지는가
I-2  NATS 전이 발행량 폭증 — 무제한 반복 시 연간 몇 건인가
I-3  스케줄러 date-job 수 — 현행 방식(창당 2잡)을 그대로 쓰면 몇 개인가
I-4  소비자 fail-safe 계약 붕괴 — window_end 로컬타이머가 반복 창에 통하는가
I-5  status 값 분포 — 'idle' 신규 값이 실제로 얼마나 발생하는가(계약 파급)
I-6  게이트 계산 비용 — 스케줄 N개일 때 요청당 소요
I-7  /active 응답 의미 — 유효기간과 현재 occurrence 의 괴리
I-8  겹침 판정 비용 — 반복 창끼리 겹치는지 검사
"""
from __future__ import annotations

import io
import sys
import time as timemod
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import model
from model import Sched, WEEKDAYS, ALLDAYS, MON, SAT, SUN
from scenarios import k

KST = ZoneInfo("Asia/Seoul")
LOG = open("sim_round2.log", "w", encoding="utf-8", newline="\n")
ISSUES = []


def log(m=""):
    LOG.write(m + "\n")


def issue(code, sev, title, evidence, impact):
    ISSUES.append(dict(code=code, sev=sev, title=title, evidence=evidence, impact=impact))
    log(f"\n  >>> [{code}] {sev} — {title}")
    log(f"      근거: {evidence}")
    log(f"      영향: {impact}")


def kst(dt):
    return dt.replace(tzinfo=model.UTC).astimezone(KST).strftime("%Y-%m-%d(%a) %H:%M")


log("=" * 100)
log("반복 억제 스케줄 시뮬레이션 — ROUND 2 (통합 지점 실측)")
log(f"실행 시각: {datetime.now().isoformat(timespec='seconds')}")
log("=" * 100)

PM1 = Sched(id=1, recurrence_type="weekly", days_of_week=WEEKDAYS,
            daily_start=time(8, 0), daily_end=time(21, 0),
            valid_from=k(2026, 8, 9), valid_until=k(2026, 9, 21))
PM2 = Sched(id=2, recurrence_type="weekly", days_of_week=WEEKDAYS,
            daily_start=time(8, 0), daily_end=time(21, 0),
            valid_from=k(2026, 8, 9), valid_until=None)
ONESHOT = Sched(id=3, recurrence_type="none",
                window_start=k(2026, 8, 10, 9), window_end=k(2026, 8, 10, 18))

# ── I-1. 게이트 SQL 사전필터 가능성 ─────────────────────────────
log("\n" + "=" * 100)
log("I-1. 게이트 SQL 사전필터 가능성")
log("=" * 100)
log("  현행 게이트(event_suppression_service.is_suppressed) SQL:")
log("     WHERE revoked_at IS NULL AND window_start <= now AND window_end > now AND event_scope IN (...)")
log("  → DB 가 후보를 좁혀서 보통 0~2행만 파이썬으로 온다.")
log("")
log("  반복 창에 같은 WHERE 를 적용하면?")
now = k(2026, 8, 10, 3)   # 월 새벽 3시 — occurrence 밖
sql_pass = (PM2.valid_from <= now) and (PM2.valid_until is None or PM2.valid_until > now)
really = model.is_suppressing(PM2, now)
log(f"    now={kst(now)} (월요일 새벽 3시, 08:00~21:00 창 밖)")
log(f"    유효기간 WHERE 통과 여부 = {sql_pass}   실제 억제 여부 = {really}")
if sql_pass and not really:
    issue("I-1", "P0",
          "반복 창은 SQL WHERE 로 좁혀지지 않는다 — 게이트가 전건 로드 후 파이썬 평가로 바뀜",
          f"유효기간만으로 필터하면 통과({sql_pass})하지만 실제 억제는 {really}. "
          "요일·시각 조건은 timestamptz 비교로 표현 불가",
          "현행 '0~2행 로드'가 '유효기간 내 전 스케줄 로드'로 바뀐다. "
          "이벤트 수신 3핸들러 모든 요청 경로에 영향(가장 뜨거운 경로)")

# 유효기간 내 스케줄 수에 따른 로드량 시뮬
log("")
log("  유효기간이 겹치는 스케줄이 N개일 때 게이트가 파이썬으로 평가해야 하는 행 수:")
for n in (1, 5, 20, 50, 100):
    log(f"    스케줄 {n:3d}개 → SQL 반환 {n:3d}행 (전부 파이썬 평가) "
        f"vs 현행 단발이면 ~{min(n,2)}행")

# ── I-2. NATS 전이 발행량 ──────────────────────────────────────
log("\n" + "=" * 100)
log("I-2. NATS 전이 발행량 (SYNC_EVENT_SUPPRESSION)")
log("=" * 100)


def count_transitions(s, frm, to):
    c, t = 0, frm
    guard = 0
    while t < to and guard < 20000:
        guard += 1
        nt = model.next_transition(s, t, horizon_days=800)
        if nt is None or nt >= to:
            break
        c += 1
        t = nt
    return c


y0, y1 = k(2026, 8, 9), k(2027, 8, 9)
c_oneshot = 2
c_pm1 = count_transitions(PM1, PM1.valid_from, PM1.valid_until)
c_pm2 = count_transitions(PM2, y0, y1)
log(f"  단발 창 1개              : 전이 {c_oneshot}건 (시작+종료)")
log(f"  PM요구1 (6주 월~금)      : 전이 {c_pm1}건")
log(f"  PM요구2 (무제한 월~금)   : 전이 {c_pm2}건/년")
log(f"  → 무제한 반복 1개 = 단발 대비 {c_pm2 // c_oneshot}배")
for n in (10, 50):
    log(f"  → 그런 창 {n}개 운영 시 연간 {c_pm2*n:,}건 (일 평균 {c_pm2*n/365:.1f}건)")
if c_pm2 > 100:
    issue("I-2", "P1",
          "무제한 반복 1개가 연 500여 건 전이 발행 — 창 개수에 비례해 선형 증가",
          f"월~금 08:00~21:00 무제한 = 연 {c_pm2}건. 창 10개면 연 {c_pm2*10:,}건",
          "SYNC_EVENT_SUPPRESSION 발행량 급증. 소비자가 수신할 때마다 GET /active 재조회하는 "
          "현행 권장 처리(§2.7)를 그대로 두면 재조회 폭주")

# ── I-3. 스케줄러 date-job 수 ──────────────────────────────────
log("\n" + "=" * 100)
log("I-3. 스케줄러 date-job 수 (현행 방식 그대로 적용 시)")
log("=" * 100)
log("  현행 suppression_scheduler: 창 1개당 start/end date-job 2건 사전 예약")
log(f"  반복 창을 '모든 occurrence 미리 예약' 방식으로 하면:")
log(f"    PM요구1(6주)     : {c_pm1}잡")
log(f"    PM요구2(무제한)  : **무한** — 사전 예약 불가")
issue("I-3", "P0",
      "무제한 반복은 date-job 사전 예약이 원리적으로 불가 — 롤링 방식 필수",
      "valid_until=None 이면 occurrence 가 무한. 현행 schedule_window_boundaries() 는 "
      "start/end 2건을 미리 거는 구조",
      "스케줄러를 '다음 전이 1건만 예약 → 발화 시 재계산' 롤링으로 전면 재작성 필요. "
      "부팅 복원(reschedule_future_windows)도 같은 방식으로")

# ── I-4. 소비자 fail-safe 계약 붕괴 ────────────────────────────
log("\n" + "=" * 100)
log("I-4. 소비자 fail-safe 계약 (INTEGRATION.md §2.8) 붕괴 여부")
log("=" * 100)
log("  현행 계약: '캐시한 window_end 로컬 타이머 만료로 스스로 억제 해제' ← 1차 권위")
log("")
t_in = k(2026, 8, 10, 12)
occ = model.current_occurrence(PM2, t_in)
log(f"  반복 창에서 now={kst(t_in)} 일 때")
log(f"    valid_from  = {kst(PM2.valid_from)}")
log(f"    valid_until = None (무제한)")
log(f"    현재 occurrence = [{kst(occ[0])} ~ {kst(occ[1])}]")
log(f"  → 소비자가 'window_end' 로 타이머를 걸면 잡을 값이 **없다**(무제한).")
log(f"    occurrence_end({kst(occ[1])}) 를 써야 하는데 이는 응답에 없는 신규 필드.")
issue("I-4", "P0",
      "소비자 fail-safe 계약이 반복 창에서 성립하지 않음 — window_end 가 무의미해짐",
      f"무제한 반복은 window_end/valid_until 이 None. 해제 기준으로 쓸 값이 없다. "
      f"실제 필요한 값은 현재 occurrence 의 끝({kst(occ[1])})",
      "INTEGRATION.md §2.8 규범과 7개 서브시스템 구현이 전부 무효. "
      "응답에 occurrence_start/occurrence_end/next_occurrence_start 신규 필드 필요")

# ── I-5. status 값 분포 ────────────────────────────────────────
log("\n" + "=" * 100)
log("I-5. status 값 분포 — 'idle' 신규 값의 실제 발생 비율")
log("=" * 100)
from collections import Counter
cnt = Counter()
t = PM1.valid_from
step = timedelta(minutes=10)
while t < PM1.valid_until:
    cnt[model.derived_status(PM1, t)] += 1
    t += step
tot = sum(cnt.values())
log(f"  PM요구1 유효기간 전체를 10분 간격으로 샘플 ({tot}개 시점):")
for s_, n_ in cnt.most_common():
    log(f"    {s_:10s} {n_:6d}회  ({n_/tot*100:5.1f}%)")
idle_pct = cnt.get("idle", 0) / tot * 100
log(f"\n  → 유효기간 내인데 억제 안 하는 시간이 {idle_pct:.1f}%")
if idle_pct > 30:
    issue("I-5", "P1",
          "'idle' 신규 status 가 유효기간의 과반 — 기존 4종 enum 계약 파괴",
          f"PM요구1 기준 idle {idle_pct:.1f}%. 현행 EnumSuppressionStatus 는 "
          "pending/active/expired/cancelled 4종 고정",
          ".NET 강타입 파서 파손 위험(브로커 §9.12 status 필드에도 실림). "
          "목록 status 필터(SQL)도 재작성 필요 — SQL 로 idle 을 표현 못 함")

# ── I-6. 게이트 계산 비용 ──────────────────────────────────────
log("\n" + "=" * 100)
log("I-6. 게이트 계산 비용 (요청당)")
log("=" * 100)
scheds = [Sched(id=i, recurrence_type="weekly", days_of_week=WEEKDAYS,
                daily_start=time(8, 0), daily_end=time(21, 0),
                valid_from=k(2026, 1, 1), valid_until=None) for i in range(100)]
probe = k(2026, 8, 10, 12)
for n in (1, 10, 50, 100):
    t0 = timemod.perf_counter()
    R = 200
    for _ in range(R):
        for s_ in scheds[:n]:
            model.is_suppressing(s_, probe)
    el = (timemod.perf_counter() - t0) / R * 1000
    log(f"    스케줄 {n:3d}개 평가 → {el:.3f} ms/요청")
    if n == 100 and el > 5:
        issue("I-6", "P2", "스케줄 100개 시 게이트 계산이 요청당 5ms 초과",
              f"{el:.2f} ms/요청 (ZoneInfo 변환 × 후보일 2개 × N)",
              "이벤트 수신 hot path. tz 객체 캐시·조기탈락 최적화 필요")

# ── I-7. /active 응답 의미 괴리 ────────────────────────────────
log("\n" + "=" * 100)
log("I-7. GET /active 응답 의미 — 유효기간 vs 현재 occurrence")
log("=" * 100)
for t_ in (k(2026, 8, 10, 12), k(2026, 8, 10, 3), k(2026, 8, 15, 12)):
    o = model.current_occurrence(PM1, t_)
    st = model.derived_status(PM1, t_)
    log(f"    now={kst(t_)}  status={st:8s} occurrence={'없음' if not o else f'[{kst(o[0])}~{kst(o[1])}]'}")
    log(f"        현행 응답 필드 window_start/window_end 는 {kst(PM1.valid_from)}~{kst(PM1.valid_until)} "
        f"(= 유효기간, 지금 억제 중인지와 무관)")
issue("I-7", "P1",
      "/active 와 응답 필드가 '유효기간'을 담아 소비자가 현재 억제 구간을 알 수 없음",
      "window_start/window_end 가 반복 창에서는 유효기간 의미로 바뀌는데 "
      "소비자는 '지금 언제까지 억제인가'가 필요",
      "/active 는 현재 occurrence 가 있는 창만 반환하도록 정의 변경 + "
      "occurrence_start/occurrence_end 필드 추가 필요")

# ── I-8. 겹침 판정 ─────────────────────────────────────────────
log("\n" + "=" * 100)
log("I-8. 반복 창 겹침(overlap) 판정")
log("=" * 100)
A = Sched(id=10, recurrence_type="weekly", days_of_week=MON, daily_start=time(8, 0),
          daily_end=time(12, 0), valid_from=k(2026, 8, 1), valid_until=None)
B = Sched(id=11, recurrence_type="weekly", days_of_week=SAT, daily_start=time(8, 0),
          daily_end=time(12, 0), valid_from=k(2026, 8, 1), valid_until=None)
C = Sched(id=12, recurrence_type="weekly", days_of_week=MON, daily_start=time(10, 0),
          daily_end=time(14, 0), valid_from=k(2026, 8, 1), valid_until=None)
log("  유효기간이 완전히 겹쳐도 실제 occurrence 는 안 겹칠 수 있다:")
log("    A: 월 08:00~12:00 무제한 / B: 토 08:00~12:00 무제한  → 유효기간 100% 겹침")
t_ = k(2026, 8, 10, 10)
log(f"    now={kst(t_)}  A억제={model.is_suppressing(A,t_)}  B억제={model.is_suppressing(B,t_)} → 실제 겹침 없음")
t2 = k(2026, 8, 10, 11)
log(f"    A vs C(월 10:00~14:00): now={kst(t2)} A={model.is_suppressing(A,t2)} C={model.is_suppressing(C,t2)} → 실제 겹침")
issue("I-8", "P2",
      "겹침 경고(하드닝 §4-B)를 유효기간 비교로 판정하면 대량 오탐",
      "A(월 08-12)와 B(토 08-12)는 유효기간이 100% 겹치지만 실제 occurrence 는 절대 안 겹침",
      "겹침 검사는 '요일 교집합 ∧ 시각 구간 교집합' 으로 재정의 필요")

# ── 요약 ───────────────────────────────────────────────────────
log("\n" + "=" * 100)
log("ROUND 2 요약 — 도출 이슈")
log("=" * 100)
for i in ISSUES:
    log(f"  [{i['code']}] {i['sev']}  {i['title']}")
LOG.close()

print("ROUND 2 완료 — 통합 지점 실측")
print(f"  도출 이슈 {len(ISSUES)}건")
for i in ISSUES:
    print(f"    [{i['code']}] {i['sev']:3s} {i['title']}")
print("  로그: sim_round2.log")
