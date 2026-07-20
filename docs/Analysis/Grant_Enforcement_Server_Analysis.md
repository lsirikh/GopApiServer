# 권한 부여(Grant) 시간기반 집행 — 서버측 분석

- **작성일**: 2026-07-20
- **대상**: `C:\workspace_python\api-test-server` (GOP FastAPI 서버)
- **범위**: A(요청시점 집행) + B-서버(변경 통지 발행). 클라측은 별도 문서 `Grant_Enforcement_Client_Analysis.md`.
- **관련**: 권한 부여 UI/API 검증(`docs/reports/grant-verification-report.md`) — 그 검증은 **관리 화면·API 배선**까지였고, 본 문서는 **실제 시간기반 집행**을 다룬다.

---

## 0. 한줄 결론

**서버 집행은 올바르다.** 접근 허용은 `valid_from ≤ 요청시각 < valid_until` 을 **요청마다 라이브 계산**하며(스윕 플래그 `is_active` 비의존), `valid_until` 도달 시 정확히 403을 반환한다. 즉 **"권한이 기간 내 동작하고 만료 시 딱 차단"은 서버에서 구조적으로 보장**된다. 다만 (1) 정확 경계초(`valid_until == now`) 미테스트, (2) NATS 만료 통지 기본 OFF, (3) `AUTH_MODE=token` HTTP 통합 미테스트, (4) 테스트 픽스처의 운영 DB 접촉 위험 — 4개 보완점이 있다.

---

## 1. 집행 메커니즘 (근거 포함)

### 1.1 유효 grant 필터 — `_active_grants`
`app/routers/auth.py:147-152`(sync) · `:942-960`(async). 매 호출 라이브 계산:
```
valid ⇔ revoked_at IS NULL
      AND valid_from <= now
      AND (valid_until IS NULL OR valid_until > now)
```
- 좌경계 **포함**(`valid_from <= now`) — grant는 `valid_from` **부터** 유효.
- 우경계 **배타**(`valid_until > now`) — grant는 `valid_until` **에** 만료(1초 뒤 아님).
- `valid_until IS NULL` = 무기한(상시).
- `revoked_at IS NULL` = soft-revoke 반영.
- **`is_active` 컬럼은 의도적으로 보지 않음** (`auth.py:143` 주석 "sweep 비정규화는 보지 않는다"). → 스윕 지연과 무관하게 보안은 정확.
- `now = _kst_now()`(`auth.py:133-136`): `datetime.now(settings.tz).replace(tzinfo=None)` (Asia/Seoul → naive). DB 값도 naive KST 저장 → 동일존 naive 비교.

### 1.2 파생상태 경계 정합 — `grant_status`
`app/services/grant_service.py:32`: `if valid_until is not None and valid_until <= now: return EXPIRED`.
- `<=` 사용 → `valid_until == now` 이면 EXPIRED.
- `_active_grants` 의 `> now` 와 **정확히 정합**: `valid_until == now` 순간 → active 집합서 제외(=차단) & status=EXPIRED. 두 함수가 경계초에서 일치.

### 1.3 요청시점 인가 — `_effective_allows` + `require_perm` + 전역 미들웨어
- `_effective_allows[_async]`(`auth.py:215-225`, `:1005-1017`): 비ADMIN = **등급그룹 매트릭스 ∪ 유효 grant 그룹 매트릭스들의 합집합**. 하나라도 `module:verb` 허용 시 True.
- `require_perm[_async]`(`auth.py:228-259`, `:1137-1158`): FastAPI `Depends`. ① ADMIN 무조건 bypass ② `_effective_allows` (기본 `now=_kst_now()`) ③ False면 403. **캐시·세션상태 없음 = 매 요청 라이브.**
- 전역 `enforce_matrix`(`security/matrix_enforcer.py:88-125`) — `main.py:427` 에서 `FastAPI(dependencies=[Depends(enforce_matrix)])` 로 마운트, 매 요청 실행. `AUTH_MODE=token` 시 `_effective_allows_async` 호출(라이브 now), `public` 시 `:100` 단락, ADMIN bypass `:116-117`.

### 1.4 스윕은 보안 경계가 아님
- `grant_service.py:53-64` `expire_due_grants` / `run_grant_sweep`(`:67-115`): 만료 grant의 `is_active=False` 로 내림 — **표시·통지·정리용**(`:54` 주석 "보안 비의존"). 스케줄러 `main.py:308` `interval, minutes=10`.
- 즉 스윕이 늦어도(최대 10분) 인가 차단은 §1.1 라이브 계산이 즉시 담당.

### 1.5 변경 통지 발행부
- `grants.py:136` `GRANT_CREATED` / `grants.py:277` `GRANT_REVOKED` / `grant_service.py:114` `GRANT_EXPIRED`(스윕) 시 `publish_permissions_changed(user_id, reason)`.

---

## 2. 서버 테스트 커버리지

| 테스트 파일 | 커버 시나리오 |
|---|---|
| `test_grant_enforcement.py` | 무grant→거부 / 유효구간→허용 / 만료(`is_active=True`여도)→거부(NFR-01 핵심) / PENDING(미래 from)→거부 / 상시(until=None)→허용 / 회수(revoked_at)→거부 |
| `test_grant_status.py` | `grant_status` 순수함수: 구간내 ACTIVE / until=null ACTIVE / from前 PENDING / until後 EXPIRED / revoked REVOKED / 우선순위 REVOKED>EXPIRED |
| `test_grant_sweep.py` | `expire_due_grants`: 만료→is_active=False / 유효→불변 / 상시→불변 |
| `test_grant_api.py` | 생성(ADMIN)→201+ACTIVE / until=null→상시 / 404 없는 user / 422 until<from / 422 과거 until / GET PENDING 표시 / DELETE soft-revoke / 404 없는 grant |
| `test_permissions_changed_publish.py` | per-user subject 포맷 / 서명 payload 검증 / 변조 payload 거부 |
| `test_revoke_publisher.py` | 게이트 off→False·미연결 / NATS 다운→False·무예외 / force-logout 배선 |
| `test_matrix_enforcer.py` | 전역 미들웨어: public 통과 / permission_map / 403 / ADMIN bypass |

**커버리지 갭**
- **정확 경계초(`valid_until == now`, 마이크로초)** 미검증 — 테스트는 `now - 1h`만 사용.
- 전역 `enforce_matrix` → 만료 grant HTTP 경로 통합 미검증.
- `run_grant_sweep`(async)의 `publish_permissions_changed` 호출 미검증(sync `expire_due_grants`만).
- **`AUTH_MODE=token` + 만료 grant end-to-end HTTP** 미검증 — `conftest.py:126` 이 API 테스트를 `AUTH_MODE=public` 로 강제.

---

## 3. 발견 이슈 (심각도·성격)

| # | 이슈 | 근거 | 심각도 | 성격 |
|---|------|------|--------|------|
| S-1 | 경계초(`valid_until==now`) 미테스트 — `auth.py:151`(`>`) vs `grant_service.py:32`(`<=`) 는 **정합**하나 회귀 방지 테스트 부재 | auth.py:151, grant_service.py:32 | P3 | by-design·미테스트 |
| S-2 | **NATS `permissions_changed` 기본 OFF** (`NATS_REVOKE_ENABLED=False`) → 만료/생성/회수 통지 무발행 → 클라 실시간 만료 인지 불가(폴링/재조회 의존) | config.py:43, nats_revoke_publisher.py:145 | **P2** | by-design 게이트·운영 갭 |
| S-3 | 스윕 10분 주기 → `is_active` 표시 플래그가 만료 후 최대 10분 지연 | main.py:308 | P3 | by-design·표시만(보안 무관) |
| S-4 | `AUTH_MODE=token` HTTP 통합 집행 경로 미테스트 (conftest가 public 강제) | conftest.py:126 | **P2** | 테스트 갭 |
| S-5 | 클라 시계보정용 `server_time` 이 `/me/permissions` 응답에만 존재(전용 `/server-time` 없음) → 로그인 전 시계비교 불가 | auth.py:1224 | P3 | 경미 |
| S-6 | `async_db` 픽스처가 실 Postgres(`AsyncSessionLocal`) 타깃 → async 테스트 오실행 시 운영 DB 접촉 위험(현재 grant 테스트는 async_db 미사용) | conftest.py:169-174 | **P1** | 테스트 인프라 안전 |

> 보안 정확성은 이상 없음(S-1~S-5 어느 것도 인가 차단을 약화하지 않음). S-6은 테스트 실행 안전 문제로 서버팀 확인 권장.

---

## 4. 권고 (서버팀)

1. **S-2 (운영)**: 클라 실시간 컷오프가 필요하면 `NATS_REVOKE_ENABLED=true` 활성(3-게이트 절차: 클라 구독 준비·ACL·배포). 미활성 시 클라는 `/me/permissions` 재조회/폴링으로만 만료 인지 → **클라 문서의 폴링 요건과 연동**.
2. **S-4/S-1**: `AUTH_MODE=token` 에서 (a) 유효구간 허용, (b) `valid_until` 도달 즉시 403, (c) 회수 즉시 403, (d) PENDING 거부, (e) 경계초 를 HTTP end-to-end 로 검증하는 통합테스트 추가. (프리즈 클럭 픽스처로 경계초 결정론화.)
3. **S-6**: `async_db` 픽스처를 격리 테스트 DB로 고정하고 `ALLOW_DB_TESTS` 가드 강화 — 운영 DB 접촉 원천 차단.
4. **S-3**: 표시 최신성이 중요하면 스윕 주기 단축은 선택(보안엔 무관).

---

## 5. 클라측과의 관계 (요약)

- 서버는 **요청시점 권위 집행** — 만료 후 행위는 반드시 403. (클라 UI가 늦게 꺼져도 실제 행위는 서버가 차단.)
- 그러나 **"UI가 만료 순간 딱 꺼지는가"** 는 (S-2 통지 발행) + (클라 구독/재조회) 의 협업 → 상세는 `Grant_Enforcement_Client_Analysis.md`.

---
*본 문서는 `C:\workspace_app\Ironwall.Dotnet.Libraries\docs\analyses\` 원본이며 `api-test-server\docs\` 에 복사본이 배치된다.*
