"""공용 datetime 유틸 — datetime-unification 규약(Option B): 저장 UTC / 출력 DISPLAY_TZ / 입력 aware 권장.

- `utc_now()`     : aware UTC now — 저장/쓰기 표준.
- `to_utc(dt)`    : 입력 정규화 — aware→UTC, naive→DISPLAY_TZ(배포 표시tz) 가정→UTC.
                    비교·산술·DB 접근 **전** 경계에서 호출해 asyncpg aware/naive 500을 방지한다.
- `to_display(dt)`: 출력 변환 — UTC(또는 aware)→DISPLAY_TZ. serializer가 사용.

파일별 사본 헬퍼(`_naive_kst`/`_to_naive_kst`/`_to_kst_naive`)를 이 함수들로 대체한다.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.config import settings


def utc_now() -> datetime:
    """aware UTC now — 저장/쓰기 표준(`datetime.now(timezone.utc)`)."""
    return datetime.now(timezone.utc)


def to_utc(value: datetime | None) -> datetime | None:
    """입력 정규화: aware→UTC. naive→`DISPLAY_TZ`(배포 표시tz)로 간주 후 UTC. None-safe.

    한 요청 내 aware/naive 혼합을 UTC-aware로 통일해 비교·산술·DB 바인딩 500을 방지한다.
    """
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=settings.display_tz)
    return value.astimezone(timezone.utc)


def to_display(value: datetime | None) -> datetime | None:
    """출력 변환: aware(또는 UTC)→`DISPLAY_TZ`. naive 는 UTC 로 간주(방어) 후 변환. None-safe."""
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(settings.display_tz)
