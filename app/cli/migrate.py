"""
Standalone DB 마이그레이션 CLI — git pull 후 마이그레이션 반영/검증 단일 진입점.

배경(중요): docker-compose 의 api-server 는 Dockerfile `COPY . .` 로 코드가 **이미지에 구워진다**
(app/ 바인드마운트 아님). 따라서 host 에서 `git pull` 만 해도 **실행 중 컨테이너는 옛 코드**라
새 마이그레이션이 반영되지 않는다 → 반드시 이미지 rebuild + 컨테이너 recreate 필요.
기동 lifespan(app/main.py) 이 `apply_idempotent_migrations` 를 자동 호출하므로, recreate 만 하면
대기 마이그레이션이 멱등·checksum추적·fail-fast 로 적용된다.

본 CLI 는 그 **동일 함수를 재사용**(단일 진실 소스)해 아래를 제공한다:

  python -m app.cli.migrate            # 대기 마이그레이션 적용 (기동과 동일 경로, 멱등)
  python -m app.cli.migrate --status   # 적용 이력 + 대기 목록 출력 (변경 없음, 읽기전용)
  python -m app.cli.migrate --check    # 대기 마이그레이션 있으면 exit 1 (배포 전/후 점검·CI)

용법 위치: DATABASE_URL 이 compose 네트워크의 `postgres` 호스트를 가리키므로 **컨테이너 안**에서 실행.
  - 재기동 후 검증:   docker compose exec -T api-server python -m app.cli.migrate --status
  - 재기동 없이 선반영: docker compose run --rm api-server python -m app.cli.migrate
    (단, 코드가 이미지에 구워지므로 새 마이그레이션을 담으려면 rebuild 가 선행돼야 함)
"""
from __future__ import annotations

import hashlib
import os
import sys

from app.database import engine
from app.utils.init_db import IDEMPOTENT_MIGRATIONS, apply_idempotent_migrations

_MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "migrations")


def _load_applied() -> dict[str, str]:
    """schema_migrations 에서 {filename: checksum} 로드 (추적테이블 없으면 보장 생성)."""
    raw = engine.raw_connection()
    try:
        cur = raw.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            "  filename VARCHAR(255) PRIMARY KEY,"
            "  checksum VARCHAR(64) NOT NULL,"
            "  applied_at TIMESTAMP NOT NULL DEFAULT now())"
        )
        raw.commit()
        cur.execute("SELECT filename, checksum FROM schema_migrations")
        applied = {row[0]: row[1] for row in cur.fetchall()}
        cur.close()
        return applied
    finally:
        raw.close()


def _compute_pending(applied: dict[str, str]) -> list[str]:
    """whitelist 대비 대기(미적용/checksum 변경) 마이그레이션 목록 — 러너와 동일 checksum 규칙."""
    pending: list[str] = []
    for fname in IDEMPOTENT_MIGRATIONS:
        path = os.path.join(_MIGRATIONS_DIR, fname)
        if not os.path.exists(path):
            pending.append(f"{fname} (파일없음)")
            continue
        with open(path, "r", encoding="utf-8") as f:
            checksum = hashlib.sha256(f.read().encode("utf-8")).hexdigest()
        if applied.get(fname) != checksum:
            pending.append(fname)
    return pending


def _pending_basenames(pending: list[str]) -> set[str]:
    return {p.split(" ", 1)[0] for p in pending}


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    mode = argv[0] if argv else "apply"

    if engine.dialect.name != "postgresql":
        print(f"[migrate] dialect={engine.dialect.name} — idempotent 마이그레이션은 PostgreSQL 전용, 무동작")
        return 0

    applied = _load_applied()
    pending = _compute_pending(applied)
    pending_base = _pending_basenames(pending)

    if mode in ("--status", "status"):
        print(f"[migrate] whitelist {len(IDEMPOTENT_MIGRATIONS)}건 · 적용 {len(applied)}건 · 대기 {len(pending)}건")
        for fname in IDEMPOTENT_MIGRATIONS:
            if fname in pending_base:
                mark = "PEND"
            elif fname in applied:
                mark = "OK  "
            else:
                mark = "??  "
            print(f"  [{mark}] {fname}")
        if pending:
            print("[migrate] 대기:", ", ".join(pending))
        return 0

    if mode in ("--check", "check"):
        if pending:
            print(f"[migrate] 대기 마이그레이션 {len(pending)}건:", ", ".join(pending))
            return 1
        print("[migrate] 대기 마이그레이션 없음 (스키마 최신)")
        return 0

    # apply (기본) — 기동과 동일한 단일 진실 소스 함수 재사용 (멱등, fail-fast)
    if not pending:
        print("[migrate] 대기 마이그레이션 없음 — 변경 없음")
        return 0
    print(f"[migrate] 대기 {len(pending)}건 적용 시작:", ", ".join(pending))
    apply_idempotent_migrations(engine)
    print("[migrate] 완료 — 스키마 최신")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
