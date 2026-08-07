"""독립 오라클 — 후보 구현과 **같은 버그를 공유하지 않도록** 일부러 다른 방식으로 구현.

후보(model.py)는 "now 를 포함하는 occurrence 를 역산" 하는 빠른 방식이고,
오라클은 "유효기간 전체를 하루씩 앞에서부터 훑어 occurrence 구간 목록을 만든 뒤 포함 여부만 확인"
하는 느리지만 자명한 방식이다. 두 결과가 갈리면 둘 중 하나가 틀린 것 → 실제 버그.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

UTC = timezone.utc


def enumerate_occurrences(s, scan_from, scan_to):
    """[scan_from, scan_to) 범위와 겹치는 occurrence 구간을 **앞에서부터 전부 생성**.

    반환: [(start_naive_utc, end_naive_utc), ...]
    """
    if s.recurrence_type == "none":
        if s.window_start is None or s.window_end is None:
            return []
        return [(s.window_start, s.window_end)]

    if not s.days_of_week or s.daily_start is None or s.daily_end is None:
        return []

    zone = ZoneInfo(s.tz)
    lo = s.valid_from if s.valid_from is not None else scan_from
    hi = s.valid_until if s.valid_until is not None else scan_to
    lo = max(lo, scan_from - timedelta(days=3))
    hi = min(hi, scan_to + timedelta(days=3))
    if lo >= hi:
        return []

    out = []
    # 로컬 날짜를 하루씩 전진하며 그날 시작하는 occurrence 를 만든다
    d = (lo.replace(tzinfo=UTC).astimezone(zone) - timedelta(days=2)).date()
    end_date = (hi.replace(tzinfo=UTC).astimezone(zone) + timedelta(days=2)).date()
    while d <= end_date:
        if s.days_of_week & (1 << d.weekday()):
            st_l = datetime.combine(d, s.daily_start, tzinfo=zone)
            if s.daily_end > s.daily_start:
                en_l = datetime.combine(d, s.daily_end, tzinfo=zone)
            else:
                en_l = datetime.combine(d + timedelta(days=1), s.daily_end, tzinfo=zone)
            st = st_l.astimezone(UTC).replace(tzinfo=None)
            en = en_l.astimezone(UTC).replace(tzinfo=None)
            if s.valid_from is not None and st < s.valid_from:
                st = s.valid_from
            if s.valid_until is not None and en > s.valid_until:
                en = s.valid_until
            if st < en:
                out.append((st, en))
        d += timedelta(days=1)
    return out


def oracle_is_suppressing(s, now_utc) -> bool:
    """가장 단순한 판정: occurrence 목록을 만들고 포함 여부만 본다."""
    if s.revoked_at is not None and s.revoked_at <= now_utc:
        return False
    if s.recurrence_type == "weekly":
        if s.valid_from is not None and now_utc < s.valid_from:
            return False
        if s.valid_until is not None and now_utc >= s.valid_until:
            return False
    occs = enumerate_occurrences(s, now_utc - timedelta(days=2), now_utc + timedelta(days=2))
    return any(st <= now_utc < en for st, en in occs)


def oracle_next_transition(s, now_utc, horizon_days=400):
    """now 이후 상태가 바뀌는 최초 시각 — 분 단위 완전 탐색(가장 자명한 방식)."""
    cur = oracle_is_suppressing(s, now_utc)
    t = now_utc
    limit = now_utc + timedelta(days=horizon_days)
    # 1분 단위로 전진하되, 성능을 위해 먼저 시간 단위로 훑고 그 시간 안에서 분 단위 정밀화
    while t < limit:
        nxt_h = t + timedelta(hours=1)
        if oracle_is_suppressing(s, nxt_h) != cur:
            m = t
            while m < nxt_h:
                m2 = m + timedelta(minutes=1)
                if oracle_is_suppressing(s, m2) != cur:
                    return m2
                m = m2
            return nxt_h
        t = nxt_h
    return None
