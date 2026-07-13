"""
로그인 rate limit — P1-09 (2026-07-10). 무차별 대입 + 계정잠금 DoS 완화.

IP 기준 슬라이딩 윈도우: 윈도우 내 실패 횟수가 임계 초과면 429(Retry-After).
- 성공 로그인 시 해당 IP 카운터 리셋(정상 사용자 영향 최소).
- **단일 인스턴스 in-memory**(settings_service 캐시와 동일 가정). 멀티 인스턴스는 공유 저장소(Redis)
  필요 — follow-up. 프로세스 재시작 시 카운터 리셋(휴면 초기화).
- 계정 lockout(failed_login_count)과 독립·보완: lockout 은 계정 단위(피해자 DoS 소지),
  본 rate limit 은 공격자 IP 단위 → 공격자가 계정을 잠그기 전에 IP 를 throttle.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Optional

# 튜닝 상수 — 필요 시 settings 승격 가능(현재 최소판 상수).
WINDOW_SEC = 300          # 5분 창
MAX_FAILURES = 10         # IP 당 창 내 허용 실패 수(초과 시 429)

_attempts: dict[str, deque] = defaultdict(deque)  # ip -> deque[timestamp]


def _prune(dq: deque, now: float) -> None:
    cutoff = now - WINDOW_SEC
    while dq and dq[0] < cutoff:
        dq.popleft()


def is_rate_limited(ip: Optional[str]) -> bool:
    """해당 IP 가 현재 창에서 임계 이상 실패했는가(=차단 대상)."""
    if not ip:
        return False
    now = time.time()
    dq = _attempts[ip]
    _prune(dq, now)
    return len(dq) >= MAX_FAILURES


def record_failure(ip: Optional[str]) -> None:
    """실패 로그인 1건 기록."""
    if not ip:
        return
    now = time.time()
    dq = _attempts[ip]
    _prune(dq, now)
    dq.append(now)


def retry_after_seconds(ip: Optional[str]) -> int:
    """차단된 IP 의 Retry-After(초) — 가장 오래된 실패가 창을 벗어나는 시점까지."""
    if not ip or ip not in _attempts:
        return WINDOW_SEC
    dq = _attempts[ip]
    if not dq:
        return WINDOW_SEC
    remaining = int(dq[0] + WINDOW_SEC - time.time())
    return max(1, remaining)


def reset(ip: Optional[str]) -> None:
    """성공 로그인 시 해당 IP 카운터 클리어."""
    if ip:
        _attempts.pop(ip, None)
