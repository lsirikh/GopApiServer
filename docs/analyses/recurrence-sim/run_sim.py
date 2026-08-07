"""시뮬레이션 러너 — 후보 구현 vs 독립 오라클 차등 테스트.

사용: python run_sim.py <round_no>
출력: sim_round<N>.log (전 케이스 라인 로그) + 콘솔 요약
"""
from __future__ import annotations

import io
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import model
import oracle
from scenarios import SCENARIOS, total_probes

KST = ZoneInfo("Asia/Seoul")
ROUND = sys.argv[1] if len(sys.argv) > 1 else "1"
LOG = open(f"sim_round{ROUND}.log", "w", encoding="utf-8", newline="\n")


def log(msg=""):
    LOG.write(msg + "\n")


def kst(dt):
    return dt.replace(tzinfo=model.UTC).astimezone(KST).strftime("%Y-%m-%d(%a) %H:%M:%S")


log("=" * 100)
log(f"반복 억제 스케줄 시뮬레이션 — ROUND {ROUND}")
log(f"실행 시각: {datetime.now().isoformat(timespec='seconds')}")
log(f"시나리오 {len(SCENARIOS)}건 / 검사 시점(probe) {total_probes()}건")
log("판정: 후보구현(model.current_occurrence) vs 독립오라클(oracle 완전열거) 차등 비교")
log("=" * 100)

fail_supp = []
fail_next = []
by_cat = {}
n_checks = 0

for sc in SCENARIOS:
    s, sid, cat = sc["sched"], sc["id"], sc["cat"]
    by_cat.setdefault(cat, {"n": 0, "f": 0})
    log("")
    log(f"[{sid}] ({cat}) {sc['desc']}")
    log(f"    type={s.recurrence_type} dow={s.days_of_week:07b} daily={s.daily_start}~{s.daily_end} "
        f"tz={s.tz}")
    log(f"    valid={s.valid_from}~{s.valid_until} window={s.window_start}~{s.window_end} "
        f"revoked={s.revoked_at}")

    for now in sc["probes"]:
        n_checks += 1
        by_cat[cat]["n"] += 1
        try:
            got = model.is_suppressing(s, now)
        except Exception as e:
            got = f"EXC:{type(e).__name__}:{e}"
        try:
            exp = oracle.oracle_is_suppressing(s, now)
        except Exception as e:
            exp = f"EXC:{type(e).__name__}:{e}"
        ok = (got == exp)
        if not ok:
            fail_supp.append((sid, cat, now, got, exp, sc["desc"]))
            by_cat[cat]["f"] += 1
        occ = None
        try:
            occ = model.current_occurrence(s, now)
        except Exception:
            pass
        st = None
        try:
            st = model.derived_status(s, now)
        except Exception as e:
            st = f"EXC:{e}"
        mark = "OK  " if ok else "FAIL"
        log(f"    {mark} now={kst(now)}  supp(impl)={got}  supp(oracle)={exp}  status={st}"
            + (f"  occ=[{kst(occ[0])} ~ {kst(occ[1])}]" if occ else ""))

# next_transition 은 G 카테고리에서만 정밀 비교(오라클이 느림)
log("")
log("=" * 100)
log("next_transition 차등 검증 (스케줄러 date-job 지점)")
log("=" * 100)
for sc in SCENARIOS:
    if sc["cat"] != "next-transition":
        continue
    s = sc["sched"]
    for now in sc["probes"]:
        n_checks += 1
        by_cat.setdefault("next-transition", {"n": 0, "f": 0})
        by_cat["next-transition"]["n"] += 1
        try:
            got = model.next_transition(s, now)
        except Exception as e:
            got = f"EXC:{e}"
        try:
            exp = oracle.oracle_next_transition(s, now, horizon_days=60)
        except Exception as e:
            exp = f"EXC:{e}"
        ok = (got == exp)
        if not ok:
            fail_next.append((sc["id"], now, got, exp, sc["desc"]))
            by_cat["next-transition"]["f"] += 1
        log(f"    {'OK  ' if ok else 'FAIL'} [{sc['id']}] now={kst(now)}  "
            f"next(impl)={kst(got) if isinstance(got, datetime) else got}  "
            f"next(oracle)={kst(exp) if isinstance(exp, datetime) else exp}")

log("")
log("=" * 100)
log("요약")
log("=" * 100)
log(f"  총 검사 {n_checks}건")
log(f"  억제판정 불일치 {len(fail_supp)}건")
log(f"  다음전이 불일치 {len(fail_next)}건")
log("")
log("  카테고리별:")
for c, v in sorted(by_cat.items()):
    log(f"    {c:20s} 검사 {v['n']:4d}  실패 {v['f']:3d}")

if fail_supp:
    log("")
    log("  ── 억제판정 불일치 상세 ──")
    for sid, cat, now, got, exp, desc in fail_supp:
        log(f"    [{sid}] {cat} @ {kst(now)}  impl={got} oracle={exp}")
        log(f"           {desc}")
if fail_next:
    log("")
    log("  ── 다음전이 불일치 상세 ──")
    for sid, now, got, exp, desc in fail_next:
        log(f"    [{sid}] @ {kst(now)}  impl={kst(got) if isinstance(got, datetime) else got} "
            f"oracle={kst(exp) if isinstance(exp, datetime) else exp}")
        log(f"           {desc}")

LOG.close()

print(f"ROUND {ROUND} 완료")
print(f"  시나리오 {len(SCENARIOS)} / 검사 {n_checks}")
print(f"  억제판정 불일치 {len(fail_supp)} / 다음전이 불일치 {len(fail_next)}")
print(f"  로그: sim_round{ROUND}.log")
for c, v in sorted(by_cat.items()):
    flag = "  <-- 실패" if v["f"] else ""
    print(f"    {c:20s} {v['n']:4d}건 중 {v['f']:3d} 실패{flag}")
if fail_supp:
    print("\n  억제판정 불일치:")
    for sid, cat, now, got, exp, desc in fail_supp[:25]:
        print(f"    [{sid}] {cat} @ {kst(now)} impl={got} oracle={exp} | {desc[:50]}")
if fail_next:
    print("\n  다음전이 불일치:")
    for sid, now, got, exp, desc in fail_next[:25]:
        g = kst(got) if isinstance(got, datetime) else got
        e = kst(exp) if isinstance(exp, datetime) else exp
        print(f"    [{sid}] @ {kst(now)} impl={g} oracle={e}")
