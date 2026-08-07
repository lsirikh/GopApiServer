"""반복 억제 스케줄 — 후보 데이터 모델 + 판정 구현 (v1).

시뮬레이션 대상. 실제 서버 코드에 이식할 후보 로직을 여기서 먼저 검증한다.

설계 전제
---------
- 저장은 naive-UTC(기존 UtcDateTime 규약 유지).
- **요일·시각은 로컬 벽시계(기본 Asia/Seoul)** 기준. UTC 기준으로 요일을 보면
  KST 월요일 00:00~09:00 이 UTC 일요일이 되어 "월~금" 에서 빠지는 치명적 오류가 난다.
- 기존 단발(one-shot) 창은 `recurrence_type='none'` 으로 그대로 동작(하위호환).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

UTC = timezone.utc

# 요일 비트마스크: Mon=1<<0 ... Sun=1<<6  (Python weekday() 와 동일 순서)
MON, TUE, WED, THU, FRI, SAT, SUN = (1 << i for i in range(7))
WEEKDAYS = MON | TUE | WED | THU | FRI
WEEKEND = SAT | SUN
ALLDAYS = WEEKDAYS | WEEKEND


@dataclass
class Sched:
    """후보 스키마.

    recurrence_type='none'  : window_start~window_end 단발 (현행)
    recurrence_type='weekly': valid_from~valid_until 유효기간 안에서
                              days_of_week 요일의 daily_start~daily_end 반복
    """
    id: int = 1
    recurrence_type: str = "none"          # none | weekly

    # 단발용 (naive-UTC)
    window_start: datetime | None = None
    window_end: datetime | None = None

    # 반복용
    valid_from: datetime | None = None     # naive-UTC. None = 즉시부터
    valid_until: datetime | None = None    # naive-UTC. None = 무제한
    days_of_week: int = 0                  # 비트마스크
    daily_start: time | None = None        # 로컬 벽시계
    daily_end: time | None = None          # 로컬 벽시계
    tz: str = "Asia/Seoul"

    revoked_at: datetime | None = None

    def zone(self) -> ZoneInfo:
        return ZoneInfo(self.tz)


def _to_local(dt_naive_utc: datetime, zone: ZoneInfo) -> datetime:
    return dt_naive_utc.replace(tzinfo=UTC).astimezone(zone)


def _to_naive_utc(dt_aware: datetime) -> datetime:
    return dt_aware.astimezone(UTC).replace(tzinfo=None)


def current_occurrence(s: Sched, now_utc: datetime):
    """now 를 포함하는 occurrence 의 (start_utc, end_utc). 없으면 None.

    반환값은 naive-UTC. 반열린 구간 [start, end) 규약.
    """
    if s.revoked_at is not None and s.revoked_at <= now_utc:
        return None

    if s.recurrence_type == "none":
        if s.window_start is None or s.window_end is None:
            return None
        if s.window_start <= now_utc < s.window_end:
            return (s.window_start, s.window_end)
        return None

    # ---- weekly ----
    if not s.days_of_week or s.daily_start is None or s.daily_end is None:
        return None
    # 유효기간 밖이면 즉시 탈락
    if s.valid_from is not None and now_utc < s.valid_from:
        return None
    if s.valid_until is not None and now_utc >= s.valid_until:
        return None

    zone = s.zone()
    now_local = _to_local(now_utc, zone)

    # 자정 넘김(daily_start > daily_end) 대응: 오늘 시작분 + 어제 시작분 둘 다 검사
    for day_offset in (0, -1):
        d = (now_local + timedelta(days=day_offset)).date()
        if not (s.days_of_week & (1 << d.weekday())):
            continue
        start_local = datetime.combine(d, s.daily_start, tzinfo=zone)
        if s.daily_end > s.daily_start:
            end_local = datetime.combine(d, s.daily_end, tzinfo=zone)
        elif s.daily_end < s.daily_start:
            end_local = datetime.combine(d + timedelta(days=1), s.daily_end, tzinfo=zone)
        else:
            # daily_start == daily_end → 24시간 종일로 해석 (설계 결정 D-3)
            end_local = datetime.combine(d + timedelta(days=1), s.daily_end, tzinfo=zone)

        st = _to_naive_utc(start_local)
        en = _to_naive_utc(end_local)

        # 유효기간으로 클램프 (설계 결정 D-2: 부분 occurrence 허용)
        if s.valid_from is not None and st < s.valid_from:
            st = s.valid_from
        if s.valid_until is not None and en > s.valid_until:
            en = s.valid_until
        if st >= en:
            continue

        if st <= now_utc < en:
            return (st, en)
    return None


def is_suppressing(s: Sched, now_utc: datetime) -> bool:
    return current_occurrence(s, now_utc) is not None


def next_transition(s: Sched, now_utc: datetime, horizon_days: int = 400):
    """now 이후 최초로 억제 상태가 바뀌는 시각(naive-UTC). 없으면 None.

    스케줄러가 date-job 을 걸 지점. 무제한 반복이라 미리 다 걸 수 없으므로
    '다음 1개'만 예약하고 발화 시 다시 계산하는 롤링 방식의 근거가 된다.
    """
    occ = current_occurrence(s, now_utc)
    if occ is not None:
        return occ[1]  # 현재 occurrence 의 끝

    if s.recurrence_type == "none":
        if s.window_start is not None and now_utc < s.window_start:
            return s.window_start
        return None

    if not s.days_of_week or s.daily_start is None or s.daily_end is None:
        return None
    if s.valid_until is not None and now_utc >= s.valid_until:
        return None

    zone = s.zone()
    base = max(now_utc, s.valid_from) if s.valid_from else now_utc
    base_local = _to_local(base, zone)
    for i in range(horizon_days):
        d = (base_local + timedelta(days=i)).date()
        if not (s.days_of_week & (1 << d.weekday())):
            continue
        start_local = datetime.combine(d, s.daily_start, tzinfo=zone)
        st = _to_naive_utc(start_local)
        if s.valid_from is not None and st < s.valid_from:
            st = s.valid_from
        if s.valid_until is not None and st >= s.valid_until:
            return None
        if st > now_utc:
            return st
    return None


def derived_status(s: Sched, now_utc: datetime) -> str:
    """파생 상태. 반복 도입으로 의미가 갈라지는 지점 — 시뮬레이션의 핵심 관심사.

    cancelled > (유효기간 기준) pending/expired > (occurrence 기준) active/idle
    """
    if s.revoked_at is not None and s.revoked_at <= now_utc:
        return "cancelled"
    if s.recurrence_type == "none":
        if s.window_start is None or s.window_end is None:
            return "expired"
        if now_utc < s.window_start:
            return "pending"
        if now_utc >= s.window_end:
            return "expired"
        return "active"
    # weekly
    if s.valid_from is not None and now_utc < s.valid_from:
        return "pending"
    if s.valid_until is not None and now_utc >= s.valid_until:
        return "expired"
    return "active" if is_suppressing(s, now_utc) else "idle"
