"""시나리오 카탈로그 — 120+ 케이스.

각 시나리오 = (id, 분류, 설명, Sched, [검사할 now 시각들])
now 시각은 경계 ±1분/±1초를 의도적으로 포함시켜 off-by-one 을 노린다.
"""
from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from model import Sched, MON, TUE, WED, THU, FRI, SAT, SUN, WEEKDAYS, WEEKEND, ALLDAYS

KST = ZoneInfo("Asia/Seoul")
UTC = timezone.utc


def k(y, mo, d, h=0, mi=0, s=0):
    """KST 벽시계 → naive-UTC 저장값."""
    return datetime(y, mo, d, h, mi, s, tzinfo=KST).astimezone(UTC).replace(tzinfo=None)


def probes_around(*points, deltas=(-timedelta(minutes=1), -timedelta(seconds=1),
                                   timedelta(0), timedelta(seconds=1), timedelta(minutes=1))):
    out = []
    for p in points:
        for d in deltas:
            out.append(p + d)
    return out


SCENARIOS = []


def add(sid, cat, desc, sched, probes):
    SCENARIOS.append(dict(id=sid, cat=cat, desc=desc, sched=sched, probes=probes))


# ─────────────────────────────────────────────────────────────
# A. 하위호환 — 기존 단발(one-shot) 창 (10)
# ─────────────────────────────────────────────────────────────
for i, (h1, h2) in enumerate([(9, 18), (0, 24), (23, 24), (0, 1), (12, 13)], 1):
    ws = k(2026, 8, 10, h1)
    we = k(2026, 8, 10, 0) + timedelta(hours=h2)
    add(f"A{i:02d}", "one-shot", f"단발 {h1}시~{h2}시(KST)",
        Sched(recurrence_type="none", window_start=ws, window_end=we),
        probes_around(ws, we) + [ws + timedelta(hours=1)])

add("A06", "one-shot", "단발 — 취소된 창",
    Sched(recurrence_type="none", window_start=k(2026, 8, 10, 9), window_end=k(2026, 8, 10, 18),
          revoked_at=k(2026, 8, 10, 12)),
    probes_around(k(2026, 8, 10, 12)) + [k(2026, 8, 10, 10), k(2026, 8, 10, 15)])
add("A07", "one-shot", "단발 — 다중일(3일) 연속",
    Sched(recurrence_type="none", window_start=k(2026, 8, 10, 9), window_end=k(2026, 8, 13, 9)),
    probes_around(k(2026, 8, 10, 9), k(2026, 8, 13, 9)) + [k(2026, 8, 11, 3)])
add("A08", "one-shot", "단발 — 1분짜리",
    Sched(recurrence_type="none", window_start=k(2026, 8, 10, 9), window_end=k(2026, 8, 10, 9, 1)),
    probes_around(k(2026, 8, 10, 9), k(2026, 8, 10, 9, 1)))
add("A09", "one-shot", "단발 — 과거 창(이미 종료)",
    Sched(recurrence_type="none", window_start=k(2026, 1, 1, 9), window_end=k(2026, 1, 1, 18)),
    [k(2026, 8, 10, 12), k(2026, 1, 1, 12)])
add("A10", "one-shot", "단발 — 미래 창(아직 시작 전)",
    Sched(recurrence_type="none", window_start=k(2026, 12, 1, 9), window_end=k(2026, 12, 1, 18)),
    [k(2026, 8, 10, 12), k(2026, 12, 1, 12)])


# ─────────────────────────────────────────────────────────────
# B. 핵심 요구 — 기간 있는 주간 반복 (25)
#    "20260809~20260920 월~금 08:00~21:00"
# ─────────────────────────────────────────────────────────────
BASE = dict(recurrence_type="weekly", days_of_week=WEEKDAYS,
            daily_start=time(8, 0), daily_end=time(21, 0),
            valid_from=k(2026, 8, 9), valid_until=k(2026, 9, 21))

add("B01", "weekly-bounded", "PM 요구 원본: 08-09~09-20 월~금 08:00~21:00",
    Sched(**BASE),
    probes_around(k(2026, 8, 10, 8), k(2026, 8, 10, 21)) +   # 월
    probes_around(k(2026, 8, 14, 8), k(2026, 8, 14, 21)))     # 금

add("B02", "weekly-bounded", "같은 창 — 주말(토/일)은 미억제",
    Sched(**BASE),
    [k(2026, 8, 15, 12), k(2026, 8, 16, 12),                  # 토, 일
     k(2026, 8, 15, 8), k(2026, 8, 16, 20, 59)])

add("B03", "weekly-bounded", "같은 창 — 유효기간 시작일(일요일 08-09)은 요일 미매치",
    Sched(**BASE), probes_around(k(2026, 8, 9, 8), k(2026, 8, 9, 21)))

add("B04", "weekly-bounded", "같은 창 — 유효기간 종료 경계(09-21 00:00)",
    Sched(**BASE), probes_around(k(2026, 9, 21, 0)) + [k(2026, 9, 18, 12), k(2026, 9, 21, 12)])

add("B05", "weekly-bounded", "같은 창 — 매일 종료 직후(21:00~08:00 사이)",
    Sched(**BASE), [k(2026, 8, 11, 21, 30), k(2026, 8, 11, 23, 59), k(2026, 8, 12, 7, 59)])

for i, day in enumerate([MON, TUE, WED, THU, FRI, SAT, SUN], 1):
    add(f"B{5+i:02d}", "weekly-bounded", f"단일 요일 반복 (bit={day})",
        Sched(recurrence_type="weekly", days_of_week=day, daily_start=time(10, 0),
              daily_end=time(12, 0), valid_from=k(2026, 8, 1), valid_until=k(2026, 9, 1)),
        [k(2026, 8, 10 + n, 11) for n in range(7)] + probes_around(k(2026, 8, 10, 10)))

add("B13", "weekly-bounded", "주말만 반복 (토·일)",
    Sched(recurrence_type="weekly", days_of_week=WEEKEND, daily_start=time(0, 0),
          daily_end=time(23, 59), valid_from=k(2026, 8, 1), valid_until=k(2026, 9, 1)),
    [k(2026, 8, 15, 12), k(2026, 8, 16, 12), k(2026, 8, 17, 12)])

add("B14", "weekly-bounded", "전 요일 반복",
    Sched(recurrence_type="weekly", days_of_week=ALLDAYS, daily_start=time(9, 0),
          daily_end=time(10, 0), valid_from=k(2026, 8, 1), valid_until=k(2026, 9, 1)),
    [k(2026, 8, 10 + n, 9, 30) for n in range(7)])

add("B15", "weekly-bounded", "유효기간이 하루뿐",
    Sched(recurrence_type="weekly", days_of_week=WEEKDAYS, daily_start=time(8, 0),
          daily_end=time(21, 0), valid_from=k(2026, 8, 10), valid_until=k(2026, 8, 11)),
    probes_around(k(2026, 8, 10, 8), k(2026, 8, 10, 21), k(2026, 8, 11, 0)))

add("B16", "weekly-bounded", "유효기간 시작이 occurrence 한가운데 (월 12:00 시작)",
    Sched(recurrence_type="weekly", days_of_week=WEEKDAYS, daily_start=time(8, 0),
          daily_end=time(21, 0), valid_from=k(2026, 8, 10, 12), valid_until=k(2026, 9, 1)),
    probes_around(k(2026, 8, 10, 12)) + [k(2026, 8, 10, 9), k(2026, 8, 10, 20)])

add("B17", "weekly-bounded", "유효기간 끝이 occurrence 한가운데 (금 15:00 종료)",
    Sched(recurrence_type="weekly", days_of_week=WEEKDAYS, daily_start=time(8, 0),
          daily_end=time(21, 0), valid_from=k(2026, 8, 1), valid_until=k(2026, 8, 14, 15)),
    probes_around(k(2026, 8, 14, 15)) + [k(2026, 8, 14, 10), k(2026, 8, 14, 20)])

add("B18", "weekly-bounded", "유효기간이 occurrence 를 하나도 안 포함(주말만 걸침)",
    Sched(recurrence_type="weekly", days_of_week=WEEKDAYS, daily_start=time(8, 0),
          daily_end=time(21, 0), valid_from=k(2026, 8, 15), valid_until=k(2026, 8, 17)),
    [k(2026, 8, 15, 12), k(2026, 8, 16, 12)])

add("B19", "weekly-bounded", "취소된 반복 창",
    Sched(recurrence_type="weekly", days_of_week=WEEKDAYS, daily_start=time(8, 0),
          daily_end=time(21, 0), valid_from=k(2026, 8, 1), valid_until=k(2026, 9, 1),
          revoked_at=k(2026, 8, 12, 10)),
    probes_around(k(2026, 8, 12, 10)) + [k(2026, 8, 11, 12), k(2026, 8, 13, 12)])

add("B20", "weekly-bounded", "월/수/금만",
    Sched(recurrence_type="weekly", days_of_week=MON | WED | FRI, daily_start=time(8, 0),
          daily_end=time(21, 0), valid_from=k(2026, 8, 1), valid_until=k(2026, 9, 1)),
    [k(2026, 8, 10 + n, 12) for n in range(7)])

add("B21", "weekly-bounded", "짧은 일일창 1분",
    Sched(recurrence_type="weekly", days_of_week=WEEKDAYS, daily_start=time(8, 0),
          daily_end=time(8, 1), valid_from=k(2026, 8, 1), valid_until=k(2026, 9, 1)),
    probes_around(k(2026, 8, 10, 8), k(2026, 8, 10, 8, 1)))

add("B22", "weekly-bounded", "일일창 00:00~23:59 (거의 종일)",
    Sched(recurrence_type="weekly", days_of_week=WEEKDAYS, daily_start=time(0, 0),
          daily_end=time(23, 59), valid_from=k(2026, 8, 1), valid_until=k(2026, 9, 1)),
    probes_around(k(2026, 8, 10, 0), k(2026, 8, 10, 23, 59)))

add("B23", "weekly-bounded", "valid_from == valid_until (빈 기간)",
    Sched(recurrence_type="weekly", days_of_week=WEEKDAYS, daily_start=time(8, 0),
          daily_end=time(21, 0), valid_from=k(2026, 8, 10), valid_until=k(2026, 8, 10)),
    [k(2026, 8, 10, 12), k(2026, 8, 10, 8)])

add("B24", "weekly-bounded", "긴 기간(1년) 월~금",
    Sched(recurrence_type="weekly", days_of_week=WEEKDAYS, daily_start=time(8, 0),
          daily_end=time(21, 0), valid_from=k(2026, 1, 1), valid_until=k(2027, 1, 1)),
    [k(2026, 3, 10, 12), k(2026, 7, 15, 12), k(2026, 11, 20, 12), k(2026, 3, 14, 12)])

add("B25", "weekly-bounded", "days_of_week=0 (요일 미선택 — 무효)",
    Sched(recurrence_type="weekly", days_of_week=0, daily_start=time(8, 0),
          daily_end=time(21, 0), valid_from=k(2026, 8, 1), valid_until=k(2026, 9, 1)),
    [k(2026, 8, 10, 12), k(2026, 8, 11, 9)])


# ─────────────────────────────────────────────────────────────
# C. 무제한 반복 (valid_until = None) (12)
# ─────────────────────────────────────────────────────────────
add("C01", "weekly-unbounded", "무제한 월~금 08:00~21:00 (PM 요구 2)",
    Sched(recurrence_type="weekly", days_of_week=WEEKDAYS, daily_start=time(8, 0),
          daily_end=time(21, 0), valid_from=k(2026, 8, 1), valid_until=None),
    probes_around(k(2026, 8, 10, 8), k(2026, 8, 10, 21)) +
    [k(2027, 5, 10, 12), k(2030, 1, 7, 12), k(2026, 8, 15, 12)])

add("C02", "weekly-unbounded", "무제한 + valid_from 도 None (즉시~영구)",
    Sched(recurrence_type="weekly", days_of_week=WEEKDAYS, daily_start=time(8, 0),
          daily_end=time(21, 0), valid_from=None, valid_until=None),
    [k(2026, 8, 10, 12), k(2026, 8, 15, 12), k(2020, 3, 4, 12), k(2035, 6, 6, 12)])

add("C03", "weekly-unbounded", "무제한 — valid_from 이 미래",
    Sched(recurrence_type="weekly", days_of_week=WEEKDAYS, daily_start=time(8, 0),
          daily_end=time(21, 0), valid_from=k(2026, 12, 1), valid_until=None),
    probes_around(k(2026, 12, 1, 8)) + [k(2026, 8, 10, 12), k(2026, 12, 2, 12)])

add("C04", "weekly-unbounded", "무제한 주말 야간",
    Sched(recurrence_type="weekly", days_of_week=WEEKEND, daily_start=time(20, 0),
          daily_end=time(23, 0), valid_from=k(2026, 8, 1), valid_until=None),
    [k(2026, 8, 15, 21), k(2026, 8, 15, 19), k(2026, 8, 17, 21)])

add("C05", "weekly-unbounded", "무제한 — 취소",
    Sched(recurrence_type="weekly", days_of_week=WEEKDAYS, daily_start=time(8, 0),
          daily_end=time(21, 0), valid_from=k(2026, 8, 1), valid_until=None,
          revoked_at=k(2026, 8, 12)),
    [k(2026, 8, 11, 12), k(2026, 8, 13, 12), k(2027, 1, 5, 12)])

for i, (ds, de) in enumerate([(time(0, 0), time(12, 0)), (time(12, 0), time(23, 59)),
                              (time(6, 30), time(7, 15)), (time(1, 5), time(1, 6)),
                              (time(9, 0), time(9, 30)), (time(18, 45), time(19, 0)),
                              (time(23, 0), time(23, 59))], 6):
    add(f"C{i:02d}", "weekly-unbounded", f"무제한 월~금 {ds}~{de}",
        Sched(recurrence_type="weekly", days_of_week=WEEKDAYS, daily_start=ds, daily_end=de,
              valid_from=k(2026, 8, 1), valid_until=None),
        probes_around(datetime.combine(datetime(2026, 8, 10).date(), ds, tzinfo=KST)
                      .astimezone(UTC).replace(tzinfo=None)))


# ─────────────────────────────────────────────────────────────
# D. 자정 넘김 (daily_start > daily_end) — 최대 난이도 (18)
# ─────────────────────────────────────────────────────────────
add("D01", "overnight", "야간 22:00~06:00 월~금 (월 시작분)",
    Sched(recurrence_type="weekly", days_of_week=WEEKDAYS, daily_start=time(22, 0),
          daily_end=time(6, 0), valid_from=k(2026, 8, 1), valid_until=k(2026, 9, 1)),
    probes_around(k(2026, 8, 10, 22), k(2026, 8, 11, 6)) +
    [k(2026, 8, 11, 2), k(2026, 8, 10, 21, 30), k(2026, 8, 11, 7)])

add("D02", "overnight", "야간 22:00~06:00 — 금요일 시작분은 토요일 새벽까지",
    Sched(recurrence_type="weekly", days_of_week=WEEKDAYS, daily_start=time(22, 0),
          daily_end=time(6, 0), valid_from=k(2026, 8, 1), valid_until=k(2026, 9, 1)),
    [k(2026, 8, 14, 23), k(2026, 8, 15, 3), k(2026, 8, 15, 7), k(2026, 8, 15, 23)])

add("D03", "overnight", "야간 — 일요일 시작분은 월요일 새벽까지(일 미선택 시 없어야)",
    Sched(recurrence_type="weekly", days_of_week=WEEKDAYS, daily_start=time(22, 0),
          daily_end=time(6, 0), valid_from=k(2026, 8, 1), valid_until=k(2026, 9, 1)),
    [k(2026, 8, 16, 23), k(2026, 8, 17, 3), k(2026, 8, 17, 23)])

add("D04", "overnight", "야간 23:59~00:01 (극단적으로 짧은 자정 넘김)",
    Sched(recurrence_type="weekly", days_of_week=ALLDAYS, daily_start=time(23, 59),
          daily_end=time(0, 1), valid_from=k(2026, 8, 1), valid_until=k(2026, 9, 1)),
    probes_around(k(2026, 8, 10, 23, 59), k(2026, 8, 11, 0, 1)))

add("D05", "overnight", "야간 20:00~08:00 (12시간)",
    Sched(recurrence_type="weekly", days_of_week=WEEKDAYS, daily_start=time(20, 0),
          daily_end=time(8, 0), valid_from=k(2026, 8, 1), valid_until=k(2026, 9, 1)),
    probes_around(k(2026, 8, 10, 20), k(2026, 8, 11, 8)) + [k(2026, 8, 11, 4)])

add("D06", "overnight", "야간 + 유효기간 끝이 새벽 구간 중간",
    Sched(recurrence_type="weekly", days_of_week=WEEKDAYS, daily_start=time(22, 0),
          daily_end=time(6, 0), valid_from=k(2026, 8, 1), valid_until=k(2026, 8, 12, 3)),
    probes_around(k(2026, 8, 12, 3)) + [k(2026, 8, 12, 1), k(2026, 8, 12, 5)])

add("D07", "overnight", "야간 + 유효기간 시작이 새벽 구간 중간",
    Sched(recurrence_type="weekly", days_of_week=WEEKDAYS, daily_start=time(22, 0),
          daily_end=time(6, 0), valid_from=k(2026, 8, 11, 3), valid_until=k(2026, 9, 1)),
    probes_around(k(2026, 8, 11, 3)) + [k(2026, 8, 11, 1), k(2026, 8, 11, 5)])

add("D08", "overnight", "야간 무제한",
    Sched(recurrence_type="weekly", days_of_week=WEEKDAYS, daily_start=time(22, 0),
          daily_end=time(6, 0), valid_from=k(2026, 8, 1), valid_until=None),
    [k(2027, 3, 9, 2), k(2027, 3, 9, 23), k(2027, 3, 14, 2)])

add("D09", "overnight", "토요일만 야간 (일요일 새벽까지 이어짐)",
    Sched(recurrence_type="weekly", days_of_week=SAT, daily_start=time(23, 0),
          daily_end=time(5, 0), valid_from=k(2026, 8, 1), valid_until=k(2026, 9, 1)),
    [k(2026, 8, 15, 23, 30), k(2026, 8, 16, 3), k(2026, 8, 16, 23, 30), k(2026, 8, 16, 6)])

add("D10", "overnight", "일요일만 야간 (월요일 새벽까지)",
    Sched(recurrence_type="weekly", days_of_week=SUN, daily_start=time(23, 0),
          daily_end=time(5, 0), valid_from=k(2026, 8, 1), valid_until=k(2026, 9, 1)),
    [k(2026, 8, 16, 23, 30), k(2026, 8, 17, 3), k(2026, 8, 17, 23, 30)])

for i, (ds, de) in enumerate([(time(21, 0), time(3, 0)), (time(23, 0), time(1, 0)),
                              (time(18, 0), time(9, 0)), (time(22, 30), time(6, 30)),
                              (time(0, 30), time(0, 15)), (time(12, 0), time(11, 0)),
                              (time(23, 59), time(23, 58)), (time(2, 0), time(1, 0))], 11):
    add(f"D{i:02d}", "overnight", f"자정 넘김 {ds}~{de} 월~금",
        Sched(recurrence_type="weekly", days_of_week=WEEKDAYS, daily_start=ds, daily_end=de,
              valid_from=k(2026, 8, 1), valid_until=k(2026, 9, 1)),
        [k(2026, 8, 10, 23), k(2026, 8, 11, 2), k(2026, 8, 11, 12), k(2026, 8, 15, 2),
         k(2026, 8, 16, 23)])


# ─────────────────────────────────────────────────────────────
# E. 시간대 함정 — KST 자정 근처 / UTC 요일 불일치 (15)
# ─────────────────────────────────────────────────────────────
add("E01", "timezone", "★ KST 월요일 00:00~09:00 은 UTC 일요일 — 요일 판정이 로컬이어야",
    Sched(recurrence_type="weekly", days_of_week=MON, daily_start=time(0, 0),
          daily_end=time(9, 0), valid_from=k(2026, 8, 1), valid_until=k(2026, 9, 1)),
    [k(2026, 8, 10, 0, 30), k(2026, 8, 10, 8, 30), k(2026, 8, 9, 23, 30), k(2026, 8, 10, 9, 30)])

add("E02", "timezone", "★ KST 금요일 23:00 은 UTC 금요일 14:00 (경계 무해) / 월 00:30 대조",
    Sched(recurrence_type="weekly", days_of_week=FRI, daily_start=time(22, 0),
          daily_end=time(23, 59), valid_from=k(2026, 8, 1), valid_until=k(2026, 9, 1)),
    [k(2026, 8, 14, 23), k(2026, 8, 14, 21), k(2026, 8, 15, 0, 30)])

add("E03", "timezone", "KST 00:00 정각 시작 (UTC 전날 15:00)",
    Sched(recurrence_type="weekly", days_of_week=WEEKDAYS, daily_start=time(0, 0),
          daily_end=time(1, 0), valid_from=k(2026, 8, 1), valid_until=k(2026, 9, 1)),
    probes_around(k(2026, 8, 10, 0), k(2026, 8, 10, 1)))

add("E04", "timezone", "UTC 타임존 스케줄 (tz=UTC)",
    Sched(recurrence_type="weekly", days_of_week=WEEKDAYS, daily_start=time(8, 0),
          daily_end=time(21, 0), valid_from=k(2026, 8, 1), valid_until=k(2026, 9, 1), tz="UTC"),
    [datetime(2026, 8, 10, 9), datetime(2026, 8, 10, 22), datetime(2026, 8, 10, 7)])

add("E05", "timezone", "DST 있는 타임존 (America/New_York) 봄 전환 주",
    Sched(recurrence_type="weekly", days_of_week=ALLDAYS, daily_start=time(1, 0),
          daily_end=time(4, 0), valid_from=datetime(2026, 3, 1), valid_until=datetime(2026, 4, 1),
          tz="America/New_York"),
    [datetime(2026, 3, 8, 6), datetime(2026, 3, 8, 7), datetime(2026, 3, 8, 8),
     datetime(2026, 3, 10, 7)])

add("E06", "timezone", "DST 가을 전환 주 (America/New_York)",
    Sched(recurrence_type="weekly", days_of_week=ALLDAYS, daily_start=time(1, 0),
          daily_end=time(3, 0), valid_from=datetime(2026, 10, 1), valid_until=datetime(2026, 12, 1),
          tz="America/New_York"),
    [datetime(2026, 11, 1, 5), datetime(2026, 11, 1, 6), datetime(2026, 11, 1, 7)])

for i, hh in enumerate([0, 1, 8, 9, 14, 15, 16, 23], 7):
    add(f"E{i:02d}", "timezone", f"KST {hh}시 경계 정밀 — 월~금 {hh}:00~{(hh+1)%24}:00",
        Sched(recurrence_type="weekly", days_of_week=WEEKDAYS, daily_start=time(hh, 0),
              daily_end=time((hh + 1) % 24, 0), valid_from=k(2026, 8, 1), valid_until=k(2026, 9, 1)),
        probes_around(k(2026, 8, 10, hh)) + [k(2026, 8, 10, hh) + timedelta(minutes=30)])

add("E15", "timezone", "KST 일요일 23:30 시작 → 월요일 새벽 (일 선택)",
    Sched(recurrence_type="weekly", days_of_week=SUN, daily_start=time(23, 30),
          daily_end=time(2, 0), valid_from=k(2026, 8, 1), valid_until=k(2026, 9, 1)),
    [k(2026, 8, 16, 23, 45), k(2026, 8, 17, 1), k(2026, 8, 17, 3), k(2026, 8, 16, 23)])


# ─────────────────────────────────────────────────────────────
# F. 상태(status) 의미 — 반복 도입으로 갈라지는 지점 (12)
# ─────────────────────────────────────────────────────────────
_st = Sched(recurrence_type="weekly", days_of_week=WEEKDAYS, daily_start=time(8, 0),
            daily_end=time(21, 0), valid_from=k(2026, 8, 10), valid_until=k(2026, 8, 21))
for i, (t, note) in enumerate([
        (k(2026, 8, 5, 12), "유효기간 전 → pending"),
        (k(2026, 8, 10, 7), "유효기간 내·occurrence 전 → ?"),
        (k(2026, 8, 10, 12), "occurrence 내 → active"),
        (k(2026, 8, 10, 22), "occurrence 후·유효기간 내 → ?"),
        (k(2026, 8, 15, 12), "주말·유효기간 내 → ?"),
        (k(2026, 8, 25, 12), "유효기간 후 → expired"),
        (k(2026, 8, 21, 0), "유효기간 끝 경계"),
        (k(2026, 8, 10, 8), "occurrence 시작 정각"),
        (k(2026, 8, 10, 21), "occurrence 끝 정각"),
        (k(2026, 8, 20, 20, 59), "마지막 목요일 종료 직전"),
        (k(2026, 8, 14, 21, 1), "금 종료 직후"),
        (k(2026, 8, 17, 8), "다음주 월 시작"), ], 1):
    add(f"F{i:02d}", "status", f"status 판정 — {note}", _st, [t])


# ─────────────────────────────────────────────────────────────
# G. next_transition (스케줄러 date-job 지점) (15)
# ─────────────────────────────────────────────────────────────
_nt = Sched(recurrence_type="weekly", days_of_week=WEEKDAYS, daily_start=time(8, 0),
            daily_end=time(21, 0), valid_from=k(2026, 8, 10), valid_until=k(2026, 9, 21))
for i, t in enumerate([
        k(2026, 8, 10, 7), k(2026, 8, 10, 8), k(2026, 8, 10, 12), k(2026, 8, 10, 20, 59),
        k(2026, 8, 10, 21), k(2026, 8, 10, 23), k(2026, 8, 14, 21, 1), k(2026, 8, 15, 12),
        k(2026, 8, 16, 23), k(2026, 9, 18, 20), k(2026, 9, 20, 12), k(2026, 9, 21, 1),
        k(2026, 8, 9, 12), k(2026, 8, 11, 0), k(2026, 8, 13, 8)], 1):
    add(f"G{i:02d}", "next-transition", f"다음 전이 계산 @ {t}", _nt, [t])


# ─────────────────────────────────────────────────────────────
# H. 이상/방어 입력 (12)
# ─────────────────────────────────────────────────────────────
add("H01", "guard", "daily_start == daily_end (24시간 해석?)",
    Sched(recurrence_type="weekly", days_of_week=WEEKDAYS, daily_start=time(8, 0),
          daily_end=time(8, 0), valid_from=k(2026, 8, 1), valid_until=k(2026, 9, 1)),
    probes_around(k(2026, 8, 10, 8)) + [k(2026, 8, 10, 20), k(2026, 8, 11, 7)])

add("H02", "guard", "weekly 인데 daily_start 누락",
    Sched(recurrence_type="weekly", days_of_week=WEEKDAYS, daily_start=None,
          daily_end=time(21, 0), valid_from=k(2026, 8, 1), valid_until=k(2026, 9, 1)),
    [k(2026, 8, 10, 12)])

add("H03", "guard", "weekly 인데 daily_end 누락",
    Sched(recurrence_type="weekly", days_of_week=WEEKDAYS, daily_start=time(8, 0),
          daily_end=None, valid_from=k(2026, 8, 1), valid_until=k(2026, 9, 1)),
    [k(2026, 8, 10, 12)])

add("H04", "guard", "valid_from > valid_until (역전)",
    Sched(recurrence_type="weekly", days_of_week=WEEKDAYS, daily_start=time(8, 0),
          daily_end=time(21, 0), valid_from=k(2026, 9, 1), valid_until=k(2026, 8, 1)),
    [k(2026, 8, 15, 12), k(2026, 8, 10, 12)])

add("H05", "guard", "none 인데 window 누락",
    Sched(recurrence_type="none", window_start=None, window_end=None),
    [k(2026, 8, 10, 12)])

add("H06", "guard", "none 인데 window 역전",
    Sched(recurrence_type="none", window_start=k(2026, 8, 10, 18), window_end=k(2026, 8, 10, 9)),
    [k(2026, 8, 10, 12), k(2026, 8, 10, 20)])

add("H07", "guard", "revoked_at 이 미래 (아직 유효)",
    Sched(recurrence_type="weekly", days_of_week=WEEKDAYS, daily_start=time(8, 0),
          daily_end=time(21, 0), valid_from=k(2026, 8, 1), valid_until=k(2026, 9, 1),
          revoked_at=k(2026, 8, 20)),
    [k(2026, 8, 10, 12), k(2026, 8, 25, 12)])

add("H08", "guard", "days_of_week 에 비트 범위 밖 값 (128)",
    Sched(recurrence_type="weekly", days_of_week=128, daily_start=time(8, 0),
          daily_end=time(21, 0), valid_from=k(2026, 8, 1), valid_until=k(2026, 9, 1)),
    [k(2026, 8, 10, 12)])

add("H09", "guard", "unknown recurrence_type",
    Sched(recurrence_type="monthly", days_of_week=WEEKDAYS, daily_start=time(8, 0),
          daily_end=time(21, 0), valid_from=k(2026, 8, 1), valid_until=k(2026, 9, 1)),
    [k(2026, 8, 10, 12)])

add("H10", "guard", "valid_until 이 과거 (이미 만료)",
    Sched(recurrence_type="weekly", days_of_week=WEEKDAYS, daily_start=time(8, 0),
          daily_end=time(21, 0), valid_from=k(2025, 1, 1), valid_until=k(2025, 2, 1)),
    [k(2026, 8, 10, 12)])

add("H11", "guard", "초 단위 daily 경계 (08:00:30)",
    Sched(recurrence_type="weekly", days_of_week=WEEKDAYS, daily_start=time(8, 0, 30),
          daily_end=time(21, 0, 30), valid_from=k(2026, 8, 1), valid_until=k(2026, 9, 1)),
    probes_around(k(2026, 8, 10, 8, 0, 30)))

add("H12", "guard", "윤년 2월 29일 포함 기간",
    Sched(recurrence_type="weekly", days_of_week=ALLDAYS, daily_start=time(8, 0),
          daily_end=time(21, 0), valid_from=k(2028, 2, 25), valid_until=k(2028, 3, 5)),
    [k(2028, 2, 29, 12), k(2028, 2, 29, 7), k(2028, 3, 1, 12)])


def total_probes():
    return sum(len(s["probes"]) for s in SCENARIOS)
