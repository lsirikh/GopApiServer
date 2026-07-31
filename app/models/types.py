"""SQLAlchemy 커스텀 타입 — UTC 저장 timestamptz 컬럼용 (datetime-unification Option B).

`impl = DateTime(timezone=True)` = Postgres `TIMESTAMP WITH TIME ZONE`(timestamptz). bind 시 naive
값은 `DISPLAY_TZ`로 간주해 UTC-aware로 정규화(세션 tz 의존 제거), aware 값은 UTC로 변환한다.
timestamptz 는 aware 를 네이티브 수용하므로 asyncpg aware/naive 500 이 원천 소멸한다(V-01 확인).
파이썬 레벨 비교/산술은 bind 를 안 거치므로 `to_utc()` 로 별도 정규화한다(2중 방어).
"""
from __future__ import annotations

from datetime import timezone

from sqlalchemy import DateTime
from sqlalchemy.types import TypeDecorator

from app.config import settings


class UtcDateTime(TypeDecorator):
    """UTC 저장 timestamptz 컬럼. bind: naive→DISPLAY_TZ→UTC, aware→UTC."""

    impl = DateTime
    cache_ok = True

    def __init__(self, *args, **kwargs):
        # 항상 timestamptz. 모델의 `Column(DateTime)` / `Column(DateTime(timezone=True))` 를
        # 일괄 `UtcDateTime` 로 치환해도 동작하도록 Column-level kwargs(timezone= 등)는 무시하고 강제 True.
        super().__init__(timezone=True)

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if getattr(value, "tzinfo", None) is None:
            value = value.replace(tzinfo=settings.display_tz)
        return value.astimezone(timezone.utc)
