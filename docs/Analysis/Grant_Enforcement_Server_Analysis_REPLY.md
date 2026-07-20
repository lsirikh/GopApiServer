# [서버팀 회신] Grant 시간기반 집행 — 서버측 분석 검토 결과

- **작성일**: 2026-07-21
- **대상**: GIS 팀 `Grant_Enforcement_Server_Analysis.md` (2026-07-20)
- **회신 주체**: API 서버팀 (`C:\workspace_python\api-test-server`)
- **관련 산출물**: PRD `docs/prds/grant-enforcement-hardening-prd.md` (v3.0) · 시뮬 `docs/Analysis/grant-enforcement-sim/SIMULATION_REPORT.md` (128/128)

---

## 0. 총평 — 채택

문서에 박힌 **코드 인용 ~30건을 실소스와 1:1 대조 → 100% 일치**했고, 핵심 판정(요청시점 라이브 계산 → 만료 시 정확 403, `is_active` 스윕 비의존, 경계초 `>` vs `<=` 정합)이 **옳음을 확인**했습니다. 추가로 **실행 시뮬(128/128)** + **회귀 테스트 신규 18건**으로 재입증했습니다. 이슈 S-1~S-6 전부 실재. 아래는 **보강/정정 4건**입니다.

---

## 1. 커버리지 정정 (§2 관련) — ★ 중요

### 1-1. `test_matrix_enforcer.py` 3개 테스트가 현재 **FAIL** 상태
문서 §2는 `test_matrix_enforcer` 가 "403 / ADMIN bypass" 를 커버한다고 기재했으나, **실측 결과 3개가 실패**합니다:

| 테스트 | 상태 | 원인 |
|---|---|---|
| `test_should_deny_when_role_lacks_permission` | ❌ FAIL | sync `db_session` 을 **async** `enforce_matrix` 에 전달 → `await db.execute(...)` 불가 |
| `test_should_bypass_when_admin` | ❌ FAIL | 〃 (user 해석 단계에서 async 세션 필요) |
| `test_should_allow_when_grant_adds_permission` | ❌ FAIL | 〃 |

→ v6.0 Async 대전환 때 `enforce_matrix` 가 async 화됐으나 이 테스트는 sync 세션 그대로라 **미갱신된 사전 실패**입니다(집행 코드 자체는 정상 — 시뮬·신규 테스트로 확인). public/401/미등록/permission_map 4건은 정상(async 경로 미진입).

### 1-2. 본 작업의 재커버 (FR-02)
서버팀이 **실 `AsyncSession`(격리 aiosqlite) 로 `enforce_matrix` 를 직접 구동**하는 `tests/test_grant_enforcement_http.py` 를 신설해 grant 수명주기를 재커버했습니다 — **7 passed**:
유효→ALLOW / 만료→403 / 회수→403 / PENDING→403 / 무권한→403 / ADMIN→ALLOW / 무토큰→401.

### 1-3. grant 발행기 게이트 전용 테스트 부재
`publish_permissions_changed`(grant 통지)의 **게이트(off→무발행) 전용 단위테스트는 부재**합니다. `test_revoke_publisher` 의 게이트 테스트는 **세션-revoke 발행기(`publish_session_revoke`)** 대상이라 별개입니다(동일 `NATS_REVOKE_ENABLED` 플래그라 동작은 동치). 본 작업에서 `run_grant_sweep` 의 사용자당 1회 발행(dedup)은 신규 `test_grant_sweep_async.py` 로 커버.

---

## 2. 표기 정정 2건 (경미)

| 문서 | 기재 | 실제 |
|---|---|---|
| §1.4 | "`grant_service.py:54` 주석 '보안 비의존'" | 해당 주석은 **`:56`** (`:54`는 docstring 시작 라인) |
| §2/S-1 | "테스트는 `now - 1h`만 사용" | 실제 오프셋은 `±1h/±5h/±10h/+2h` — 취지(정확 경계초 미검증)는 정확하나 문구가 느슨 |

---

## 3. 스코프 경계 공유 — 4-c (미등록 경로 default-allow)

`enforce_matrix` 는 `PERMISSION_MAP` **미등록 경로를 token 모드에서 default-allow** 합니다(`matrix_enforcer.py:105-106`). 즉 문서는 "grant 평가 시 만료가 정확" 을 증명했지만, "grant-gated 경로가 실제로 매트릭스에 게이트되는가" 는 별개입니다.

- **시뮬 Unit C2**: default-deny 전환 시 결과가 바뀌는 셀 = **정확히 6개**(`token+미등록+¬allowlist`), 그리고 **`user=none`·`user=admin` 도 403** 이 됩니다 → 전 라우트 분류 audit(미분류 0)이 절대 선결.
- 서버팀은 이를 **FR-09(default-deny 전환)** 로 편입해 처리 예정(관찰모드 선행 + allowlist + 계약테스트). 실제 활성은 배포 게이트.

---

## 4. 본 작업(Phase 1) 요약 — 검증 부채 상환

| 항목 | 결과 |
|---|---|
| 경계초 삼중 회귀 (`test_grant_boundary.py`) | 7 passed (2회 결정론) — `valid_until==now`→EXPIRED/차단, is_active 무관 |
| token 집행 (`test_grant_enforcement_http.py`) | 7 passed — 실 async enforce_matrix 경로 |
| async sweep 발행 (`test_grant_sweep_async.py`) | 2 passed — 만료 flag+감사+사용자당 1회 발행 |
| `async_db` 격리 가드 (`test_async_db_guard.py`) | 2 passed — 기본 격리 aiosqlite(S-6 해소) |
| 회귀 | 사전 실패 13건 불변, **신규 실패 0** |

> Phase 2(NATS 실시간 통지 활성 S-2 / 스윕 주기 S-3 / 자연만료 per-grant fire 4-a / default-deny 4-c)는 런타임 변경분으로 별도 진행. **S-2/S-3/4-a/4-c 문의 감사합니다 — 전부 FR로 반영됐습니다.**
