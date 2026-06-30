# PRD v5.2 — Stability Hotfix (서버 비정상 종료 진단 & 1차 처방)

| 항목 | 내용 |
|------|------|
| 버전 | v5.2 |
| 작성일 | 2026-06-30 |
| 작성자 | 이기호 차장 / Claude (Workflow 7 정밀 감사) |
| 상위 PRD | v5.1 RBAC Enforcement (`docs/PRD_v5.1_Server_RBAC.md`) |
| 범위 | 서버 가용성 — 컨테이너 비정상 종료, 메모리/풀 누수, async-동기 혼용, 호스트 자원 |
| 안전점 | `pre-stability-hotfix @ 6eced61` (HEAD before fix) |
| 결재 | 차장님 검토 후 v5.3 분리 PR 진행 가부 |

---

## 1. 배경 — 차장님 보고

> "API 서버가 가끔 죽는데 원인을 모르겠다. 5~9일 주기로 재기동되는 것 같다."

본 PRD는 위 한 줄 보고를 진단·치료·검증 사이클로 환원한 결과물이다.
조사 범위는 **단일 컨테이너 장애가 아닌 호스트/Docker daemon/PG/코드 6축**으로 확장하였다.

조사 도구
- Workflow 7 정밀 감사 agent (498K token, 6.5분 실행)
- Windows Event Log (Kernel-Power 41 / 6008)
- docker logs / inspect / system df
- PostgreSQL `pg_stat_activity`, `current_setting('statement_timeout')`
- 코드 정적 분석 (auth.py / users.py / user_sessions.py / middleware)

---

## 2. 진단 결과 — Health Score **58/100**

> **Dim 6축 매트릭스** (각 100점 만점)

| Dim | Component | Health | Findings | 죽음 후보 | 비고 |
|-----|-----------|--------|----------|-----------|------|
| A | container-events | 55 | 7 | 3 | OOM/SIGKILL 추정 + 모든 형제 컨테이너 동시 재기동 |
| B | memory-leak | 62 | 8 | 2 | APILoggingMiddleware 세션 누수, 스케줄 청소 부재 |
| C | db-connection | 72 | 7 | 1 | 풀 자체는 양호. statement_timeout=0이 결정타 |
| D | async-patterns | 42 | 8 | 3 | **최저점**. 동기 bcrypt가 이벤트루프를 차단 |
| E | startup-deps | 62 | 5 | 2 | depends_on 부재 / healthcheck endpoint 부정확 |
| F | endpoint-stress | 55 | 7 | 2 | /docs(3.6KB) healthcheck 자체가 부담 |

---

## 3. TOP 5 죽음 원인 (high confidence)

### 3.1 동기 bcrypt → 이벤트루프 블로킹
- 위치: `app/api/auth.py:303`, `app/api/auth.py:609`, `app/api/users.py:184`
- 증상: 동시 login 30건에서 응답 **4170ms (270배 폭증)** + CPU 95% pin
- 원인: `bcrypt.hashpw / checkpw`가 FastAPI async 핸들러 내부에서 **동기 호출**
- 영향: healthcheck 타임아웃 → Docker가 컨테이너를 unhealthy로 마크 → 재기동

### 3.2 호스트 C: 99% 풀
- 진단: Docker images 99GB + build cache 45GB 누적
- 영향: PG WAL 기록 실패 → 트랜잭션 abort → 서비스 통째로 거부

### 3.3 v5.1 자가 버그 — `force_logout_all_user_sessions` kwarg
> **본 세션 정직성 원칙: 자가 발견 / 자가 명시**
- 위치: `app/services/user_sessions.py:131, 146`
- 증상: kwarg `expires_in` 으로 호출 — 실제 시그니처는 `expires_at` → **TypeError 500**
- 발견 경위: v5.1 RBAC PR 머지 직후 force-logout 회귀 테스트에서 검출
- 단건 force-logout(`980abbc`)에서도 동일 패턴 잔존 확인

### 3.4 PostgreSQL 타임아웃 0
- 진단: `statement_timeout=0` + `idle_in_transaction_session_timeout=0`
- 영향: runaway 트랜잭션이 연결 풀을 **무한 점유** → 다른 요청 전부 대기

### 3.5 APILoggingMiddleware 세션 누수
- 위치: `app/middlewares/api_logging.py`
- 증상: 매 요청마다 **DB 세션 신규 생성/미반환** → 풀이 정상치의 2배 소모
- 영향: 부하 5분 후 풀 고갈 → 5xx 폭증

---

## 4. 호스트 절전 가설 — 확정 (HIGH)

> Windows Event Log 증거 기반.

| Event ID | 의미 | 발생 시각 (KST) |
|----------|------|-----------------|
| 41 / 6008 | Kernel-Power: unexpected shutdown | 2026-06-29 09:30 |
| 41 / 6008 | 동상 | 2026-06-24 08:38 |
| 41 / 6008 | 동상 | 2026-06-20 09:55 |

- **간격: 5~9일** → 차장님 보고와 정확히 일치
- 4개 형제 컨테이너가 2026-06-29 09:32 KST에 **일제 재기동** → Docker daemon 단위 재시작
- 결론: 컨테이너 OOM이 아니라 **호스트 자체가 비정상 종료** (절전/슬립/전원이벤트)

> NOTE — 차장님 PC 절전 비활성화는 v5.3 Deferred 항목으로 분리. 본 PRD는 코드/인프라 처방만 다룬다.

---

## 5. 즉시 처리 5건 (Fix-1 ~ Fix-5)

### Fix-1. Docker 디스크 회수

```bash
docker builder prune -af
docker image prune -af
```

- 회수: **45.63 GB (build cache) + 444 MB (dangling images)**
- 결과: C: 점유율 **99% → 98.1%**
- 검증: `docker system df` → Build Cache **0 B**

### Fix-2. v5.1 자가 버그 패치
> 본 PR의 핵심. 정직성 원칙에 따라 PRD에 투명하게 기재.

```python
# Before (app/services/user_sessions.py:131,146)
TokenBlacklist.add(token, expires_in=settings.JWT_EXPIRE_MIN)

# After
TokenBlacklist.add(token, expires_at=datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MIN))
```

- 동일 패턴이 단건 force-logout(`980abbc`)에 잔존 → 동시 수정
- 검증: 벌크 force_logout → **200 OK** + `token_blacklist`에 `FORCE_LOGOUT_BULK` 사유 등록 확인

### Fix-3. PostgreSQL 타임아웃 명시

```sql
ALTER DATABASE gop SET statement_timeout = '60s';
ALTER DATABASE gop SET idle_in_transaction_session_timeout = '5min';
```

- 검증: `SHOW statement_timeout;` → `60s`, `SHOW idle_in_transaction_session_timeout;` → `300s`

### Fix-4. docker-compose 로그 회전 YAML anchor

```yaml
x-default-logging: &default-logging
  driver: json-file
  options:
    max-size: "10m"
    max-file: "3"

services:
  api:
    logging: *default-logging
  db_monitor:
    logging: *default-logging
  # ... 모든 서비스 동일 적용
```

- 효과: 로그 1개당 **최대 30MB** 상한 → 디스크 무한 증가 차단
- 검증: `docker inspect <container> | grep LogConfig` → `{max-file: 3, max-size: 10m}`

### Fix-5. Healthcheck 경량화

```yaml
# Before
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/docs"]   # 3.6 KB

# After
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/api/tracking/health"]  # ~30 B JSON, 무인증
```

- 효과: 매 healthcheck 부하 **~120배 감소**
- 검증: `docker inspect <container> | jq .Config.Healthcheck.Test`

---

## 6. 실측 검증 — **5 / 5 PASS**

| # | 검증 명령 | 기대 | 실측 | 판정 |
|---|-----------|------|------|------|
| Fix-1 | `docker system df` | Build Cache 0 B | 0 B | PASS |
| Fix-2 | 벌크 force_logout API | 200 OK + blacklist 등록 | 200 + `FORCE_LOGOUT_BULK` | PASS |
| Fix-3 | `SHOW statement_timeout` | 60s / 300s | 60s / 300s | PASS |
| Fix-4 | `docker inspect .HostConfig.LogConfig` | json-file 10m/3 | json-file 10m/3 | PASS |
| Fix-5 | `docker inspect .Config.Healthcheck.Test` | `/api/tracking/health` | `/api/tracking/health` | PASS |

---

## 7. 9중 정합 — 본 PRD가 동기화하는 산출물

> 단일 변경이 9개 채널 전부에 반영되었는지 추적.

| # | 채널 | 상태 |
|---|------|------|
| 1 | 코드 (`user_sessions.py`, `docker-compose.yml`) | OK |
| 2 | 명세서 (`GOP_Restful_Api_연동설계.md` — 변경 없음, 회귀 패치) | OK |
| 3 | CHANGELOG `[v5.2]` 섹션 | TODO (본 머지 시 추가) |
| 4 | Docker Image 재빌드 | OK |
| 5 | Container 재기동 + healthcheck 통과 | OK |
| 6 | Swagger `/docs` — 회귀 endpoint 정상 노출 | OK |
| 7 | Gitea push + PR 링크 | TODO |
| 8 | PRD 문서 (본 파일) | OK |
| 9 | MEMORY.md `feedback_v5.2_hotfix.md` | TODO |

---

## 8. v5.3+ Deferred — 별도 PR 권고 8건

> 본 hotfix 범위 외. 영향도/공수가 크므로 분리 결재 권고.

| # | 항목 | 영역 | 예상 공수 |
|---|------|------|----------|
| D-1 | bcrypt async 전환 (`asyncio.to_thread`) — login + login_oauth2 + password change 3곳 | auth | 0.5d |
| D-2 | APScheduler + cachetools 도입 (token_blacklist / api_logs / user_sessions / track_points 자동 청소) | infra | 1.5d |
| D-3 | 트랜잭션 안전망 표준화 (`get_db` finally rollback) | infra | 0.5d |
| D-4 | APILoggingMiddleware 비동기 큐 분리 | middleware | 1d |
| D-5 | db_monitor 재시도 + autoheal 컨테이너 (`willfarrell/autoheal`) | ops | 0.5d |
| D-6 | `uptime_watch.ps1` 매분 docker inspect 스냅샷 | ops | 0.3d |
| D-7 | 차장님 PC 절전 비활성화 (제어판 → 전원옵션) | ops | 0.1d |
| D-8 | events / api_logs / audit_logs 보존 정책 (90일 / 180일 / 영구) PRD 결재 | data governance | PRD 별건 |

---

## 안전점 & 롤백

- 안전점 태그: **`pre-stability-hotfix @ 6eced61`** (HEAD before fix)
- 롤백 명령:
  ```bash
  git reset --hard pre-stability-hotfix
  docker-compose up -d --force-recreate
  ```
- 롤백 시 주의: Fix-3 (PG ALTER DATABASE)는 git 미반영 → 별도 `ALTER DATABASE gop RESET statement_timeout;` 필요

---

## 변경 이력

| 일자 | 버전 | 변경 |
|------|------|------|
| 2026-06-30 | v5.2.0 | 초안 작성, Fix-1~5 적용 + 5/5 PASS, v5.3 Deferred 8건 등록 |

---

### 관련 파일 (절대 경로)

- `C:\workspace_python\api-test-server\app\services\user_sessions.py` (Fix-2 대상)
- `C:\workspace_python\api-test-server\docker-compose.yml` (Fix-4, Fix-5)
- `C:\workspace_python\api-test-server\app\api\auth.py` (D-1 대상)
- `C:\workspace_python\api-test-server\app\api\users.py` (D-1 대상)
- `C:\workspace_python\api-test-server\app\middlewares\api_logging.py` (D-4)
- `C:\workspace_python\api-test-server\docs\PRD_v5.1_Server_RBAC.md` (상위)
- `C:\workspace_python\api-test-server\docs\PRD_v5.2_Stability_Hotfix.md` (본 파일)
