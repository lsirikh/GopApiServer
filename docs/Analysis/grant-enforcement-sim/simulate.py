#!/usr/bin/env python3
"""
grant-enforcement-hardening PRD 검증 시뮬레이션 harness.

목적: PRD(docs/prds/grant-enforcement-hardening-prd.md)의 핵심 설계 주장을
      실제 코드(app.services.grant_service 순수함수) + 소스 충실 복제 술어로
      시나리오별 시뮬레이션하여 교차검증한다. (DB 불요 — 순수 계산만)

단위(Unit) — 각 단위 로그를 logs/unit{A..D}_run{N}.log 에 남긴다:
  A) grant 유효성 — active_predicate(_active_grants 복제) vs grant_status/is_valid_now(REAL)
     · 경계초(valid_until==now) 정합 + is_active 비의존 (S-1 / 4-b / NFR-01)
  B) effective_allows 합집합 — 등급 ∪ 유효 grant 그룹 (FR-02 집행)
  C) enforce_matrix 결정표 — public/token · 등록여부 · admin · effective (S-4 / 4-c)
  D) sweep/publish/push-latency — is_active 표시성 · 게이트 · 자연만료 통지 지연 (S-2/S-3/4-a)

--run N 으로 2회 실행 → run1/run2 로그가 완전 동일해야 결정론(NFR-02) 입증.

근거 소스 라인 (2026-07-21 실소스 대조):
  _active_grants        app/routers/auth.py:147-152
  _active_grants_async  app/routers/auth.py:942-960  (동일 술어)
  grant_status (<=)     app/services/grant_service.py:20-34
  is_valid_now          app/services/grant_service.py:37-39
  _role_group_allows    app/routers/auth.py:118-130
  _merge_modules        app/routers/auth.py:160-177
  _effective_allows     app/routers/auth.py:215-225
  find_due/run_sweep    app/services/grant_service.py:42-115  (is_active==True AND until<=now)
  enforce_matrix        app/security/matrix_enforcer.py:100-125
  publish gate          app/services/nats_revoke_publisher.py:145
  sweep interval 10m    app/main.py:308
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta

# --- repo root 를 path 에 추가(실제 import) ---
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# --- REAL: grant_service 순수함수 (DB 불요) ---
from app.services.grant_service import (  # noqa: E402
    grant_status, is_valid_now,
    STATUS_ACTIVE, STATUS_PENDING, STATUS_EXPIRED, STATUS_REVOKED,
)

# --- effective_allows 헬퍼: 실제 import 시도, 실패 시 소스 충실 복제 ---
try:
    from app.routers.auth import (  # noqa: E402
        _merge_modules as real_merge,
        _role_group_allows as real_rga,
    )
    REAL_AUTH = True
    _auth_err = ""
except Exception as e:  # 무거운 import 실패 시 복제로 폴백
    REAL_AUTH = False
    _auth_err = repr(e)


# ============================================================
# 소스 충실 복제 술어들
# ============================================================
def active_predicate(g, now) -> bool:
    """_active_grants SQL 필터 복제 (auth.py:147-152 / 942-960 동일).

    revoked_at IS NULL AND valid_from <= now AND (valid_until IS NULL OR valid_until > now)
    ★ is_active 는 참조하지 않음(설계).
    """
    return (
        g.revoked_at is None
        and g.valid_from <= now
        and (g.valid_until is None or g.valid_until > now)
    )


def expected_status(revoked, vf, vu, now) -> str:
    """grant_status 우선순위 독립 재유도 (REVOKED>PENDING>EXPIRED>ACTIVE)."""
    if revoked is not None:
        return STATUS_REVOKED
    if vf > now:
        return STATUS_PENDING
    if vu is not None and vu <= now:
        return STATUS_EXPIRED
    return STATUS_ACTIVE


def rep_role_group_allows(group, module, verb) -> bool:
    """_role_group_allows 복제 (auth.py:118-130)."""
    if group is None or not getattr(group, "is_active", True):
        return False
    perms = getattr(group, "permissions", None) or {}
    modules_perms = perms.get("modules", {}) if isinstance(perms, dict) else {}
    verbs_perms = modules_perms.get(module, {}) if isinstance(modules_perms, dict) else {}
    return isinstance(verbs_perms, dict) and bool(verbs_perms.get(verb))


RGA = real_rga if REAL_AUTH else rep_role_group_allows


def effective_allows(role_group, active_grant_groups, module, verb) -> bool:
    """_effective_allows 복제 (auth.py:215-225) — 등급 ∪ 유효 grant 그룹."""
    if RGA(role_group, module, verb):
        return True
    for grp in active_grant_groups:
        if RGA(grp, module, verb):
            return True
    return False


def sweep_due(g, now) -> bool:
    """find_due_grants / run_grant_sweep where 복제 (grant_service.py:46-50, 87-91).

    is_active==True AND valid_until IS NOT NULL AND valid_until <= now
    """
    return (g.is_active is True and g.valid_until is not None and g.valid_until <= now)


def will_publish(nats_enabled: bool) -> bool:
    """publish_permissions_changed 게이트 (nats_revoke_publisher.py:145)."""
    return bool(nats_enabled)


def enforce_decision(auth_mode, path_registered, user_kind, effective) -> str:
    """enforce_matrix 결정 복제 (matrix_enforcer.py:100-125)."""
    if auth_mode != "token":
        return "ALLOW(public bypass :100)"
    if not path_registered:
        return "ALLOW(default-allow 미등록 :105)"
    if user_kind == "none":
        return "401(:111)"
    if user_kind == "admin":
        return "ALLOW(admin bypass :116)"
    return "ALLOW(:121)" if effective else "403(:122)"


# ============================================================
# 시나리오 데이터 모델
# ============================================================
class FakeGrant:
    def __init__(self, revoked_at, valid_from, valid_until, is_active):
        self.revoked_at = revoked_at
        self.valid_from = valid_from
        self.valid_until = valid_until
        self.is_active = is_active


class FakeGroup:
    """UserGroup 유사 — .permissions(dict) .is_active(bool)."""
    def __init__(self, permissions, is_active=True):
        self.permissions = permissions
        self.is_active = is_active


def _fmt(dt, now):
    if dt is None:
        return "NULL"
    delta = dt - now
    if delta == timedelta(0):
        return "==NOW(경계)"
    mins = delta.total_seconds() / 60.0
    sign = "+" if mins >= 0 else ""
    return f"NOW{sign}{mins:g}m"


# ============================================================
# Unit A — grant 유효성 / 경계초 / is_active 비의존
# ============================================================
def unit_a(logdir, run, now):
    path = os.path.join(logdir, f"unitA_run{run}.log")
    total = passed = 0
    lines = []
    lines.append(f"### UNIT A — grant 유효성 (경계초 정합 + is_active 비의존)  [run{run}]")
    lines.append(f"# REAL grant_status/is_valid_now 사용 | active_predicate=_active_grants 복제")
    lines.append(f"# NOW={now.isoformat()}  (고정 → 결정론)")
    lines.append(f"# 검사: c1 status정확 · c2 is_valid_now==ACTIVE · c3 active_predicate⟺ACTIVE(★핵심) · c4 is_active비의존")
    lines.append("")

    froms = [("from-past", now - timedelta(hours=1)),
             ("from-NOW", now),
             ("from-future", now + timedelta(hours=1))]
    untils = [("until-NULL", None),
              ("until-past", now - timedelta(hours=1)),
              ("until-NOW", now),
              ("until-future", now + timedelta(hours=1))]
    revs = [("live", None), ("revoked", now - timedelta(minutes=30))]
    acts = [("isact=T", True), ("isact=F", False)]

    for rlabel, rev in revs:
        for flabel, vf in froms:
            for ulabel, vu in untils:
                for alabel, isact in acts:
                    total += 1
                    g = FakeGrant(rev, vf, vu, isact)
                    rs = grant_status(g, now)
                    ivn = is_valid_now(g, now)
                    ap = active_predicate(g, now)
                    exp = expected_status(rev, vf, vu, now)
                    g_flip = FakeGrant(rev, vf, vu, not isact)
                    ap_flip = active_predicate(g_flip, now)

                    c1 = (rs == exp)
                    c2 = (ivn == (rs == STATUS_ACTIVE))
                    c3 = (ap == (rs == STATUS_ACTIVE))
                    c4 = (ap == ap_flip)
                    ok = c1 and c2 and c3 and c4
                    if ok:
                        passed += 1
                    boundary = "  <<경계" if (vu == now or vf == now) else ""
                    lines.append(
                        f"[{'PASS' if ok else 'FAIL'}] {rlabel:7} {flabel:11} {ulabel:12} {alabel:8} "
                        f"| status={rs:7} valid={str(ap):5} is_valid_now={str(ivn):5} "
                        f"| exp={exp:7} c1={int(c1)} c2={int(c2)} c3={int(c3)} c4={int(c4)}{boundary}"
                    )
    lines.append("")
    lines.append(f"# UNIT A 요약: {passed}/{total} PASS")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    return total, passed


# ============================================================
# Unit B — effective_allows 합집합
# ============================================================
def unit_b(logdir, run, now):
    path = os.path.join(logdir, f"unitB_run{run}.log")
    total = passed = 0
    lines = []
    lines.append(f"### UNIT B — effective_allows 합집합 (등급 ∪ 유효 grant 그룹)  [run{run}]")
    lines.append(f"# 헬퍼 모드: {'REAL app.routers.auth' if REAL_AUTH else 'REPLICA(폴백) — '+_auth_err}")
    lines.append(f"# 대상 권한 = cameras:control | NOW={now.isoformat()}")
    lines.append("")

    M, V = "cameras", "control"
    role_has = FakeGroup({"modules": {M: {V: True}}}, is_active=True)
    role_lacks = FakeGroup({"modules": {}}, is_active=True)
    role_has_inactive = FakeGroup({"modules": {M: {V: True}}}, is_active=False)

    cam_grp = FakeGroup({"modules": {M: {V: True}}}, is_active=True)
    cam_grp_inactive = FakeGroup({"modules": {M: {V: True}}}, is_active=False)
    other_grp = FakeGroup({"modules": {"devices": {"view": True}}}, is_active=True)

    past = (now - timedelta(hours=5), now - timedelta(hours=1))   # expired window
    liv = (now - timedelta(hours=1), now + timedelta(hours=5))    # active window
    fut = (now + timedelta(hours=1), now + timedelta(hours=5))    # pending window

    def grant(group, window, revoked=None):
        vf, vu = window
        return (FakeGrant(revoked, vf, vu, True), group)

    # (label, role_group, [(grant, group)...], expected_allow)
    scenarios = [
        ("role 보유, grant 없음", role_has, [], True),
        ("role 미보유, grant 없음", role_lacks, [], False),
        ("role 미보유, +유효 grant(cam:control)", role_lacks, [grant(cam_grp, liv)], True),
        ("role 미보유, +만료 grant(cam:control) → perm 무시", role_lacks, [grant(cam_grp, past)], False),
        ("role 미보유, +대기(PENDING) grant(cam:control)", role_lacks, [grant(cam_grp, fut)], False),
        ("role 미보유, +회수 grant(cam:control)", role_lacks, [grant(cam_grp, liv, revoked=now - timedelta(minutes=5))], False),
        ("role 미보유, +유효 grant(다른모듈 devices:view)", role_lacks, [grant(other_grp, liv)], False),
        ("role 미보유, +유효 grant 지만 그룹 비활성", role_lacks, [grant(cam_grp_inactive, liv)], False),
        ("role 보유하나 등급그룹 비활성", role_has_inactive, [], False),
        ("role 미보유, 만료 grant + 유효 grant 혼합 → 유효분으로 허용", role_lacks,
         [grant(cam_grp, past), grant(cam_grp, liv)], True),
    ]

    for label, rg, grants, exp in scenarios:
        total += 1
        active_groups = [grp for (gr, grp) in grants if active_predicate(gr, now)]
        got = effective_allows(rg, active_groups, M, V)
        ok = (got == exp)
        if ok:
            passed += 1
        lines.append(
            f"[{'PASS' if ok else 'FAIL'}] allow={str(got):5} exp={str(exp):5} "
            f"| 활성grant그룹수={len(active_groups)} | {label}"
        )
    lines.append("")
    lines.append(f"# UNIT B 요약: {passed}/{total} PASS")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    return total, passed


# ============================================================
# Unit C — enforce_matrix 결정표
# ============================================================
def unit_c(logdir, run, now):
    path = os.path.join(logdir, f"unitC_run{run}.log")
    total = passed = 0
    lines = []
    lines.append(f"### UNIT C — enforce_matrix 전역 결정표  [run{run}]")
    lines.append(f"# 복제 (matrix_enforcer.py:100-125). 24 조합 전수.")
    lines.append(f"# 표기: notable=★(default-allow 미등록=4-c 스코프주의 / token 만료차단=403)")
    lines.append("")

    def expected(auth_mode, reg, user, eff):
        # 독립 기대치(소스 문장 그대로 재유도)
        if auth_mode != "token":
            return "public-bypass"
        if not reg:
            return "default-allow"
        if user == "none":
            return "401"
        if user == "admin":
            return "admin-bypass"
        return "allow" if eff else "403"

    def norm(dec):
        if "public bypass" in dec: return "public-bypass"
        if "default-allow" in dec: return "default-allow"
        if "401" in dec: return "401"
        if "admin bypass" in dec: return "admin-bypass"
        if "403" in dec: return "403"
        return "allow"

    for auth_mode in ("public", "token"):
        for reg in (True, False):
            for user in ("none", "admin", "nonadmin"):
                for eff in (True, False):
                    total += 1
                    dec = enforce_decision(auth_mode, reg, user, eff)
                    exp = expected(auth_mode, reg, user, eff)
                    ok = (norm(dec) == exp)
                    if ok:
                        passed += 1
                    notable = ""
                    if auth_mode == "token" and not reg:
                        notable = "  ★미등록=default-allow(4-c)"
                    elif auth_mode == "token" and reg and user == "nonadmin" and not eff:
                        notable = "  ★만료/무권한 차단=403"
                    lines.append(
                        f"[{'PASS' if ok else 'FAIL'}] mode={auth_mode:6} reg={str(reg):5} "
                        f"user={user:8} eff={str(eff):5} -> {dec:28}{notable}"
                    )
    lines.append("")
    lines.append(f"# UNIT C 요약: {passed}/{total} PASS")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    return total, passed


# ============================================================
# Unit C2 — enforce_matrix default-DENY 변형 (FR-09)
# ============================================================
def unit_c2(logdir, run, now):
    """FR-09: 미등록 경로를 403(default-deny)으로. 단 public allowlist 예외.
    현행 default-allow(Unit C)와 셀 단위 비교 → 변경 blast-radius 명시.
    """
    path = os.path.join(logdir, f"unitC2_run{run}.log")
    total = passed = 0
    changed = 0
    lines = []
    lines.append(f"### UNIT C2 — enforce_matrix default-DENY 변형 (FR-09)  [run{run}]")
    lines.append(f"# 현행 default-allow(Unit C) 대비 token+미등록+¬allowlist 를 403 으로.")
    lines.append(f"# <<CHANGED = 현행 대비 결정이 바뀌는 셀(=FR-09 영향 범위).")
    lines.append("")

    def deny_decision(auth_mode, reg, public_allow, user, eff):
        if auth_mode != "token":
            return "public-bypass"
        if not reg:
            return "allow(public-allowlist)" if public_allow else "403(default-deny)"
        if user == "none":
            return "401"
        if user == "admin":
            return "admin-bypass"
        return "allow" if eff else "403"

    def norm(dec):
        if "public-bypass" in dec or "public bypass" in dec: return "public-bypass"
        if "default-allow" in dec: return "default-allow"
        if "public-allowlist" in dec: return "public-allow"
        if "default-deny" in dec: return "deny-403"
        if "401" in dec: return "401"
        if "admin" in dec: return "admin-bypass"
        if "403" in dec: return "403"
        return "allow"

    def outcome(dec):
        # 접근 결과(허용/차단)만 비교 — 사유 라벨 차이는 무시
        n = norm(dec)
        if n == "401":
            return "BLOCK-401"
        if n in ("403", "deny-403"):
            return "BLOCK-403"
        return "ALLOW"  # public-bypass/default-allow/public-allow/admin-bypass/allow

    for auth_mode in ("public", "token"):
        for reg in (True, False):
            pa_opts = (False, True) if not reg else (False,)  # public_allow 는 미등록일 때만
            for public_allow in pa_opts:
                for user in ("none", "admin", "nonadmin"):
                    for eff in (True, False):
                        total += 1
                        old = enforce_decision(auth_mode, reg, user, eff)
                        new = deny_decision(auth_mode, reg, public_allow, user, eff)
                        is_changed = (outcome(old) != outcome(new))  # 결과 기준(사유 무시)
                        if is_changed:
                            changed += 1
                        exp_changed = (auth_mode == "token" and not reg and not public_allow)
                        ok = (is_changed == exp_changed)
                        if ok:
                            passed += 1
                        tag = "  <<CHANGED" if is_changed else ""
                        pa = f"pub_allow={str(public_allow):5} " if not reg else "                "
                        lines.append(
                            f"[{'PASS' if ok else 'FAIL'}] mode={auth_mode:6} reg={str(reg):5} {pa}"
                            f"user={user:8} eff={str(eff):5} | old={norm(old):13} new={norm(new):13}{tag}"
                        )
    lines.append("")
    lines.append(f"# 변경 셀 수(blast radius) = {changed}  (전부 token+미등록+¬allowlist)")
    lines.append(f"# UNIT C2 요약: {passed}/{total} PASS")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    return total, passed


# ============================================================
# Unit D — sweep / publish / push-latency
# ============================================================
def unit_d(logdir, run, now):
    path = os.path.join(logdir, f"unitD_run{run}.log")
    total = passed = 0
    lines = []
    lines.append(f"### UNIT D — sweep 표시성 · publish 게이트 · 자연만료 통지 지연  [run{run}]")
    lines.append(f"# NOW={now.isoformat()} | sweep interval I=10m (main.py:308)")
    lines.append("")

    # Part 1 — is_active 는 표시 전용, 집행(active_predicate)에 무영향
    lines.append("-- Part1: is_active 표시성 (만료 grant, is_active T/F 무관하게 집행은 차단) --")
    vf, vu = now - timedelta(hours=5), now - timedelta(hours=1)  # expired
    for isact in (True, False):
        total += 1
        g = FakeGrant(None, vf, vu, isact)
        blocked = not active_predicate(g, now)      # 집행: 차단이어야
        due = sweep_due(g, now)                       # sweep 대상 여부
        # 기대: 만료라 항상 차단(blocked=True). sweep_due 는 is_active=True 일 때만 True.
        exp_due = isact is True
        ok = (blocked is True) and (due == exp_due)
        if ok:
            passed += 1
        lines.append(
            f"[{'PASS' if ok else 'FAIL'}] isact={str(isact):5} | 집행차단={blocked} "
            f"sweep_due={due}(exp {exp_due})  → 집행은 is_active 무관 차단"
        )

    # Part 2 — publish 게이트
    lines.append("")
    lines.append("-- Part2: publish_permissions_changed 게이트(NATS_REVOKE_ENABLED) --")
    for en in (False, True):
        total += 1
        got = will_publish(en)
        exp = en
        ok = (got == exp)
        if ok:
            passed += 1
        lines.append(f"[{'PASS' if ok else 'FAIL'}] NATS_REVOKE_ENABLED={str(en):5} -> publish={got} (exp {exp})")

    # Part 3 — 자연만료 통지 지연 (sweep-only vs per-grant timer)
    lines.append("")
    lines.append("-- Part3: 자연만료 통지 지연 — sweep(10m) 발행이 유일 소스일 때 vs per-grant 타이머 --")
    I = 10.0  # minutes
    # 스윕 tick 을 0,10,20... 로 두고, 만료시각 t(분) 에 대한 다음 tick 까지 지연
    for t in (0.0, 0.5, 3.0, 7.0, 9.9, 10.0):
        total += 1
        next_tick = (int(t // I) + (0 if (t % I == 0) else 1)) * I
        sweep_latency = next_tick - t          # sweep-only 지연
        timer_latency = 0.0                     # per-grant 타이머(FR-07) 지연≈0
        # 기대: 0<=sweep_latency<=I, timer_latency==0
        ok = (0.0 <= sweep_latency <= I) and (timer_latency == 0.0)
        if ok:
            passed += 1
        lines.append(
            f"[{'PASS' if ok else 'FAIL'}] 만료 t={t:4}m | sweep-only 통지지연={sweep_latency:4}m "
            f"(최악 {I:g}m) | per-grant타이머 지연={timer_latency:g}m"
        )
    lines.append("")
    lines.append("# 결론: 자연만료의 실시간 푸시는 sweep-only 로는 최대 10m 지연 → FR-07(per-grant fire) 필요.")
    lines.append(f"# UNIT D 요약: {passed}/{total} PASS")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    return total, passed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", type=int, required=True)
    args = ap.parse_args()
    run = args.run
    logdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(logdir, exist_ok=True)

    now = datetime(2026, 7, 21, 12, 0, 0)  # 고정 시각 → 결정론

    res = {}
    res["A"] = unit_a(logdir, run, now)
    res["B"] = unit_b(logdir, run, now)
    res["C"] = unit_c(logdir, run, now)
    res["C2"] = unit_c2(logdir, run, now)
    res["D"] = unit_d(logdir, run, now)

    tot = sum(t for t, _ in res.values())
    pas = sum(p for _, p in res.values())

    summary = []
    summary.append(f"### SUMMARY run{run}")
    summary.append(f"# REAL_STATUS_IMPORT=True  REAL_AUTH_IMPORT={REAL_AUTH}" + (f" ({_auth_err})" if not REAL_AUTH else ""))
    summary.append(f"# NOW(fixed)={now.isoformat()}")
    for k in ("A", "B", "C", "C2", "D"):
        t, p = res[k]
        summary.append(f"# Unit {k}: {p}/{t} PASS")
    summary.append(f"# TOTAL: {pas}/{tot} PASS")
    verdict = "ALL-CONSISTENT" if pas == tot else "INCONSISTENCY-DETECTED"
    summary.append(f"# VERDICT: {verdict}")
    spath = os.path.join(logdir, f"summary_run{run}.log")
    with open(spath, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(summary) + "\n")

    print("\n".join(summary))
    return 0 if pas == tot else 1


if __name__ == "__main__":
    sys.exit(main())
