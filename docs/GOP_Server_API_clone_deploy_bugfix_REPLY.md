# GOP API Server — clone 배포 후 6개 버그 리포트 처리 결과 통지

- **작성일**: 2026-07-07
- **응답 대상**: 다른 PC 설치/테스트 팀 (`docs/reports/BUG_REPORT_*.md` 6건 작성 팀)
- **응답 세션**: `pids-api-server` 서버 세션
- **커밋/태그**: `release/v6.0-cert_patch` 위 → `v6.0-clone_deploy_bugfix`
- **원 리포트**: `docs/reports/` 6개 파일

---

## 📌 두괄식 결론

| # | 버그 리포트 | 근본 원인 | 처리 | 실측 |
|---|---|---|---|---|
| 1 | USER_ROLE_ENUM_MISMATCH | 응답 role strict Enum + 생성 기본값 VIEWER + 샘플 OPERATOR 시드 | ✅ 응답완화(선행) + **생성 기본값 USER + 샘플 정리** | 200 |
| 2 | AUDIT_LOGS_ENUM_MISMATCH | `AuditLogResponse.actor_role` strict Enum + append-only 옛값 | ✅ Enum→str + 목록 fault tolerance | 200(OPERATOR 행 노출) |
| 3 | CONNECTIONS_LAZYLOAD_ASYNC | `mapping.group` async lazy-load → greenlet_spawn | ✅ `selectinload(DeviceGroupMapping.group)` | 200 |
| 4 | EVENT_STATISTICS_TIMEZONE | tz-aware 입력 ↔ naive `created_at` 비교 500 | ✅ 4 endpoint 진입부 naive KST 정규화 | tz-aware 200 + naive 200 |
| 5 | REPORT_GENERATIONS_LIST_SCHEMA | `progress_pct` 컬럼 DB 미적용 (v61 미실행) | ✅ **startup 자동 마이그레이션** | 200 |
| 6 | REPORT_STATUS_SCHEMA | 동일 (progress_pct 없음) | ✅ 동일 (자동 마이그레이션) | 200 |

**6개 전부 근본 해결 + 로컬 실측 검증 완료.**

---

## 1. 근본 원인 3갈래

이 버그들은 모두 **신규 PC clone 배포** 환경 특유입니다:

### (A) 응답 스키마 strict Enum 반복 (#1, #2)
`v5.3`에서 `EnumUserRole` 을 5종 → 2종(ADMIN/USER) 축소했으나, **응답 스키마가 여전히 strict Enum**이고 DB엔 옛 값이 남아 목록 응답이 500. (이미 `servers.port`, `users.role` 에서 같은 패턴을 겪음 → Postel's Law: 요청 엄격, 응답 관대)

### (B) 마이그레이션 자동적용 부재 (#5, #6)
`create_all()` 은 **이미 존재하는 테이블에 새 컬럼을 추가하지 않는다.** 기존 볼륨을 가진 PC가 `git pull` 만 하면 모델엔 `progress_pct` 가 있지만 DB엔 없어 `UndefinedColumnError(500)`. v61 마이그레이션이 수동 실행이라 신규 배포에 누락됨.

### (C) 개별 코드 버그 (#3, #4)
- #3: async 세션에서 relationship lazy-load 함정 (`greenlet_spawn`)
- #4: naive `created_at` 컬럼과 tz-aware 입력 비교 시 asyncpg 거부

---

## 2. 왜 개발 PC(현재 프로젝트)에선 문제가 없었나

| 버그 | 개발 PC 무문제 이유 |
|---|---|
| #5, #6 | 서버 세션이 v61 마이그레이션을 **수동 적용**함 → 개발 DB엔 컬럼 존재. 신규 PC는 `create_all()` 만 돌아 컬럼 없음 |
| #1, #2 | 개발 PC `.env` 는 `INIT_SAMPLE_DATA=false`. 그러나 **docker-compose 기본값은 `:-true`** → 신규 PC 는 샘플 시드 실행 → `init_sample_data.py` 가 `actor_role="OPERATOR"` 레거시 값 주입 → 응답 500 |
| #3, #4 | 순수 코드 버그 — 개발 PC 에서도 해당 endpoint 를 그 조건(tz-aware / connections nested)으로 호출한 적이 없어 미발견 |

**한 문장**: 개발 PC 는 이미 스키마·데이터가 갖춰져 있고 샘플 시드가 꺼져 있어 취약 경로를 밟지 않았으며, 신규 PC 조건 재현 테스트를 하지 않아 잠복했습니다. (자동설치 PS2EXE 이슈와 동일한 교훈)

---

## 3. 수정 상세

### #5·#6 — startup 자동 마이그레이션 (근본)
`app/utils/init_db.py` + `app/main.py`:
- `IDEMPOTENT_MIGRATIONS` 화이트리스트 (v61 등 `ADD COLUMN IF NOT EXISTS` 만) — **파괴적 마이그레이션(v56_drop_users 등)은 절대 제외**
- `apply_idempotent_migrations(engine)` — BEGIN/COMMIT strip 후 psycopg2 raw cursor 로 실행 (idempotent)
- `main.py lifespan` 에서 `apply_triggers` 옆에 결선 → 매 startup 스키마 보정
- **주의**: multi-statement + 명시적 BEGIN/COMMIT 은 psycopg2 자동 트랜잭션과 충돌해 조용히 no-op 됨 → BEGIN/COMMIT 을 제거하고 raw cursor + `raw.commit()` 으로 실행해야 실제 반영됨 (실측으로 확인)

### #2 — audit_logs actor_role 완화
`app/schemas/audit_log.py`: `actor_role: Optional[EnumUserRole]` → `Optional[str]`.
`app/routers/audit_logs.py`: 목록 직렬화 try/except + WARN skip (한 행이 목록 전체 죽이지 않도록).

### #3 — connections lazy-load
`app/routers/connections.py` `_build_device_nested_response`:
`select(DeviceGroupMapping)` → `.options(selectinload(DeviceGroupMapping.group))` 추가 (detection_logs/malfunctions 패턴과 동일).

### #4 — event_statistics timezone
`app/routers/event_statistics.py`: `_naive_kst(dt)` 헬퍼 신설, 4 endpoint(summary/by_device/trend/dashboard) 진입부에서 `start_date`/`end_date` 를 naive KST 로 정규화.

### #1 잔여 — 생성 기본값 + 샘플 레거시
`app/routers/users.py`: `role=user_data.role or "VIEWER"` → `or "USER"`.
`app/utils/init_sample_data.py`: 감사로그 시드 `actor_role="OPERATOR"` → `"USER"` (sync + async 2곳).

---

## 4. 실측 검증 (2026-07-07)

| 검증 | 결과 |
|---|---|
| **#5·#6 자동복구** | 컬럼 3개 `DROP` (신규 PC 조건 재현) → GET /reports/generations **500** → `docker restart` → startup 로그 `[OK] idempotent migration applied: v61...` → 컬럼 3개 복구 → GET **200** |
| #3 GET /events/connections | **200** |
| #4 tz-aware `+09:00` 입력 | **200** (이전 500) |
| #4 naive 입력 (회귀) | **200** 유지 |
| #2 audit_logs OPERATOR 주입 | GET **200**, 응답에 OPERATOR 행 정상 노출 (이전 500) |
| #1 생성 기본 role | 코드 `USER` 확정 |

---

## 5. 다른 PC 즉시 적용

```bash
git pull origin release/v6.0-cert_patch   # (또는 병합된 브랜치)
docker compose build api-server
docker compose up -d --no-deps api-server
# → startup 에서 v61 자동 적용 (progress_pct 등 복구)
# → 옛 role/actor_role 값이 있어도 목록 API 500 없음
```

**추가 데이터 위생(선택)** — 옛 role 값을 정리하려면:
```sql
UPDATE account_users SET role='USER' WHERE role IN ('OPERATOR','MAINTAINER','VIEWER','GUEST');
-- audit_logs.actor_role 은 append-only 라 이력 보존 목적상 남겨도 무방 (응답은 이제 str 이라 안전)
```

---

## 6. 재발 방지

1. **응답 스키마에 요청 제약을 복사하지 않는다** (Enum/ge 등) — Postel's Law
2. **목록 API 는 행별 fault tolerance** — 한 행이 전체를 죽이지 않도록
3. **스키마 변경은 startup 자동 마이그레이션으로 정합 보장** — `create_all()` 에만 의존 금지
4. **샘플 시드는 현행 Enum 값만 사용** — 폐지된 role 주입 금지
5. **신규 PC 조건(빈 볼륨/기존 볼륨/샘플 on) 릴리스 전 재현 검증**
6. **async 경로에서 relationship 은 selectinload** — lazy-load 금지
7. **tz 경계는 입력에서 naive KST 정규화** (naive DateTime 컬럼 컨벤션)

### 남은 과제 (별도 사이클)
- `v6.0-response_schema_audit` — 전 `*Response` 스키마 Enum/제약 필드 일괄 스캔 (반복 재발 원천 차단)
- startup validation — 필수 컬럼 부재 시 명확한 헬스체크 경고

---

## 7. 참조

- **원 리포트**: `docs/reports/BUG_REPORT_*.md` 6건
- **선행 REPLY**: `docs/GOP_Server_API_servers_port0_issue_REPLY.md`, `docs/GOP_Server_API_users_role_response_relax_REPLY.md` (동일 패턴 A)
- **서버 커밋**: 태그 `v6.0-clone_deploy_bugfix`
- **CHANGELOG**: `CHANGELOG.md` → v6.0-clone_deploy_bugfix 섹션
- **저장소**: origin=`github.com/lsirikh/GopApiServer`, gitea=`192.168.202.160:3000/Sensorway_SW/GOP-Api-Db-Server`
