#!/usr/bin/env bash
# git pull 후 무인 재배포 + DB 마이그레이션 자동 적용 (Linux / macOS / Git-Bash).
#
# api-server 코드는 Dockerfile `COPY . .` 로 이미지에 구워진다(바인드마운트 아님).
# host 에서 git pull 만 하면 실행 중 컨테이너는 옛 코드라 새 마이그레이션이 반영되지 않는다.
# 본 스크립트가 올바른 순서를 캡슐화한다: pull -> build -> recreate(기동시 멱등 마이그레이션 자동 적용) -> healthy 검증.
#
# 사용: bash deploy/update.sh            (새 커밋 없으면 무동작)
#       FORCE=1 bash deploy/update.sh    (강제 재배포)
#       NO_BUILD=1 bash deploy/update.sh (rebuild 생략, recreate 만)
set -euo pipefail

SERVICE="${SERVICE:-api-server}"
CONTAINER="${CONTAINER:-pids-api-server}"

# repo 루트로 이동 (스크립트 위치의 상위)
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
echo "==> repo: $ROOT"

before="$(git rev-parse HEAD)"
echo "==> git pull --ff-only (현재 ${before:0:7})"
if ! git pull --ff-only; then
  echo "!! git pull 실패 — 로컬 미커밋 변경/충돌 가능. 'git status' 확인 후 재시도." >&2
  exit 1
fi
after="$(git rev-parse HEAD)"

if [ "$before" = "$after" ] && [ "${FORCE:-0}" != "1" ]; then
  echo "==> 이미 최신 (${after:0:7}). 변경 없음 — 종료. (강제 재배포: FORCE=1)"
  exit 0
fi

if [ "$before" != "$after" ]; then
  changed="$(git diff --name-only "$before" "$after" -- app/migrations app/utils/init_db.py || true)"
  if [ -n "$changed" ]; then
    echo "==> 마이그레이션/스키마 관련 변경 감지:"
    echo "$changed" | sed 's/^/     /'
  else
    echo "==> 코드 변경 감지 (마이그레이션 파일 변경은 없음)"
  fi
fi

if [ "${NO_BUILD:-0}" != "1" ]; then
  echo "==> docker compose build $SERVICE"
  docker compose build "$SERVICE"
else
  echo "==> build 생략 (NO_BUILD=1)"
fi

echo "==> docker compose up -d --force-recreate $SERVICE"
docker compose up -d --force-recreate "$SERVICE"

echo "==> healthy 대기 (최대 120s)"
ok=0
for _ in $(seq 1 40); do
  sleep 3
  st="$(docker inspect "$CONTAINER" --format '{{.State.Health.Status}}' 2>/dev/null || echo '')"
  if [ "$st" = "healthy" ]; then ok=1; break; fi
  if [ "$st" = "unhealthy" ]; then break; fi
done
if [ "$ok" != "1" ]; then
  echo "!! 컨테이너 healthy 실패 — 최근 로그 40줄:" >&2
  docker logs "$CONTAINER" --tail 40 || true
  echo "" >&2
  echo "!! 마이그레이션 실패(fail-fast) 가능. 롤백:" >&2
  echo "     git reset --hard $before" >&2
  echo "     docker compose build $SERVICE && docker compose up -d --force-recreate $SERVICE" >&2
  exit 1
fi

echo "==> 마이그레이션 적용 상태:"
docker compose exec -T "$SERVICE" python -m app.cli.migrate --status

echo ""
echo "==> 완료: ${before:0:7} -> ${after:0:7} (healthy)"
