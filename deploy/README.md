# deploy — git pull 후 무인 업데이트 + DB 마이그레이션

## 왜 `git pull` 만으로는 부족한가

`api-server` 는 Dockerfile `COPY . .` 로 **코드가 이미지에 구워진다**(app/ 바인드마운트 아님).
그래서 host 에서 `git pull` 만 하면 **실행 중 컨테이너는 여전히 옛 코드**라 새 마이그레이션 SQL 이
반영되지 않는다. 새 코드·마이그레이션을 반영하려면 **이미지 rebuild + 컨테이너 recreate** 가 필요하다.

DB 마이그레이션 자체는 기동 시 `app/main.py` lifespan → `apply_idempotent_migrations` 가
**멱등 · checksum 추적 · fail-fast** 로 자동 적용한다(`schema_migrations` 테이블 기록). 즉 recreate 만 하면
대기 마이그레이션이 스스로 적용된다. 아래 스크립트가 그 순서를 캡슐화한다.

## 업데이트 (서버 PC repo 루트에서)

**Windows / Docker Desktop:**
```powershell
powershell -ExecutionPolicy Bypass -File deploy\update.ps1
```

**Linux / macOS / Git-Bash:**
```bash
bash deploy/update.sh
```

동작: `git pull --ff-only` → (변경 있으면) `docker compose build` → `up -d --force-recreate`
→ healthy 대기 → 마이그레이션 적용 상태 출력. **새 커밋 없으면 무동작**(강제: `-Force` / `FORCE=1`).
healthy 실패 시 로그 40줄 + 롤백 명령을 출력한다(마이그레이션 fail-fast 가정).

## 마이그레이션만 단독 확인/적용 (컨테이너 안)

```bash
docker compose exec -T api-server python -m app.cli.migrate --status  # 적용/대기 목록 (읽기전용)
docker compose exec -T api-server python -m app.cli.migrate --check   # 대기 있으면 exit 1 (점검/CI)
docker compose exec -T api-server python -m app.cli.migrate           # 대기분 적용 (멱등)
```

`migrate` CLI 는 기동 lifespan 과 **동일한 `apply_idempotent_migrations` 를 재사용**한다(단일 진실 소스).
`DATABASE_URL` 이 compose 네트워크의 `postgres` 를 가리키므로 반드시 컨테이너 안에서 실행한다.

## 새 마이그레이션 추가 절차 (개발자)

1. `app/migrations/vNN_<name>.sql` 작성 — **반드시 idempotent**(`ADD COLUMN IF NOT EXISTS`, `WHERE` 조건부 등). 파괴적 DDL 금지.
2. `app/utils/init_db.py` 의 `IDEMPOTENT_MIGRATIONS` 리스트에 파일명 등재.
3. push → 서버에서 `deploy/update.ps1` 실행 → recreate 시 자동 적용, `--status` 로 확인.
