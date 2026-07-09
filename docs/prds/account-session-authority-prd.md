# Account 세션 권위 모델 통합 (Session Authority) PRD

- **작성일**: 2026-07-09
- **상태**: Approved
- **버전**: v1.0
- **언어/프레임워크**: Python / FastAPI (SQLAlchemy 2.x async, PostgreSQL 16, JWT HS256)
- **연관 분석**: docs/Analysis/Account_Auth_Session_Analysis_20260708.md (§5, §11.1, §12)
- **관련 메모리**: project_account_session_analysis, project_gop_force_logout_contracts

---

## 변경 이력

| 날짜 | 버전 | 변경 항목 | 변경 이유 | 영향 범위 |
|------|------|---------|---------|---------|
| 2026-07-09 | v1.0 | 초안 작성 | ACC-P0-02/03/04 세션권위 결함 실측 확인 | auth 코어(login/refresh/인증 dependency), users 관리 |
| 2026-07-09 | v1.0 | 선결 검증 V-01~V-05 해소 + FR-03 정제(expires_at→is_active) | 착수 전 가정 확인, V-02로 정상 refresh 오거부 위험 발견 | FR-03 세션 검증 기준 |
| 2026-07-09 | 1.0 | 사용자 승인 | "세션 권위 모델 승인 — 사용자 진행 지시" | 상태 Draft → Approved |

---

## 1. 개요

### 목적
"JWT가 유효한가"만 확인하던 인증 구조를 **사용자 상태(active/locked) · 세션 상태(존재/활성/만료) · token family**가 하나의 권위 모델로 일관되게 움직이도록 통합한다. 이 작업이 끝나야 계정 잠금·비활성화·강제 로그아웃·세션 만료·중복 로그인이 실제 보안 계약대로 동작한다.

### 배경 및 동기
Account/세션 분석(2026-07-08)에서 **코드로 실측 확인된** P0 결함 3건:

- **ACC-P0-02**: strict 인증(`get_current_account_user_async`, auth.py:905-912)이 JWT 서명/exp/blacklist/사용자존재만 검사하고 **`is_active`·`is_locked`를 안 봄**. (optional 버전(954)은 검사하는데 strict가 오히려 약함.) → 잠긴/비활성 계정의 기존 access token이 blacklist되지 않았다면 계속 보호 API 호출 가능.
- **ACC-P0-03**: refresh(auth.py:722-740)가 user 존재만 확인하고 **토큰을 무조건 발급**한 뒤, 세션은 있으면 갱신·없으면 통과하고 **토큰을 반환**. 세션 부재/비활성/만료여도 새 access token이 나오고, user `is_active`/`is_locked`도 미검사. → 종료·만료 세션 부활, 잠긴 계정 refresh로 재무장 가능.
- **ACC-P0-04**: 중복 로그인 처리(auth.py:448-453)가 이전 세션의 **access JTI만** blacklist하고 **refresh JTI는 남김**. → 이전 기기의 refresh token으로 (세션 검증 없는) refresh API를 호출해 재로그인 가능.

근본 원인: 폐기 경로(logout/중복로그인/lock/deactivate/reset)가 **제각각의 규칙**으로 구현되어 어떤 경로는 refresh를 빠뜨리고, 인증/refresh는 상태를 안 본다. → 공통 `revoke_session_family()` 서비스로 통합하고, 인증/refresh에 상태 검사를 추가한다(분석 §12.1/§12.2).

---

## 2. 요구사항

### 기능 요구사항 (Functional Requirements)

| ID | 요구사항 | 우선순위 | 예상 태스크 수 |
|----|---------|---------|--------------|
| FR-01 | **공통 `revoke_session_family(db, session, reason, actor_id, publish_nats, commit)` 서비스** 신설 — 세션의 access+refresh JTI를 **각 JWT의 실제 `exp`로** blacklist UPSERT, 세션 inactive/logged_out/reason 마킹, (옵션) NATS revoke 발행, caller 트랜잭션 참여. 모든 폐기 경로가 이 하나를 호출 | High | ~6개 |
| FR-02 | **strict 인증에 상태 검사 추가** (ACC-P0-02) — `get_current_account_user_async`가 `AccountUser.is_active==True AND is_locked==False` 확인, 위반 시 401. (optional 버전과 정합) | High | ~3개 |
| FR-03 | **refresh 상태·세션 검증을 발급 전에 수행** (ACC-P0-03) — user active/unlocked 필수, sid 필수, sid가 가리키는 UserSession 존재+**`is_active`**(종료/폐기 아님) 확인, 실패 시 **토큰 발급 전 401**. 조건 통과 후에만 rotation. ※ V-02: `session.expires_at`(=access 만료)로 판정 금지 — 정상 refresh 거부됨. 시간 만료는 refresh JWT 자체 exp가 담당, 세션 검증은 `is_active` 기준 | High | ~5개 |
| FR-04 | **중복 로그인 시 이전 세션을 `revoke_session_family`로 폐기** (ACC-P0-04) — access+refresh 둘 다 blacklist. 기존 access-only 로직 대체 | High | ~2개 |
| FR-05 | **lock/deactivate/admin-reset-password에서 대상 사용자의 모든 활성 세션을 `revoke_session_family`로 폐기** — DB 상태 변경과 token 폐기를 일치시킴(P1-01 부분). lock은 이미 세션 is_active=false만 하던 것을 token blacklist까지 확장 | High | ~4개 |
| FR-06 | **A01~A18 회귀 테스트 스위트** — 분석 §14 시나리오를 `should_X_when_Y` 패턴으로 작성(전용 test 경로). auth 코어 변경의 안전망 | High | ~6개 |

### 비기능 요구사항 (Non-Functional Requirements)

| ID | 항목 | 요구사항 | 검증 방법 |
|----|------|---------|---------|
| NFR-01 | 보안 — 인증/세션 | 잠금·비활성·세션종료·중복로그인·admin reset 후 **이전 access/refresh 모두 401** | 단위/통합 테스트(A01~A18) + 수동 취약점 검증 |
| NFR-02 | 성능 — auth 핫패스 | strict 인증에 추가되는 DB 조회는 **요청당 1회 이내**(이미 user 조회 중 → 컬럼 재사용, 추가 쿼리 지양). 세션 검사 추가 시 인덱스 사용 | 응답 시간 측정(p95 회귀 없음) |
| NFR-03 | 호환성 — public 모드 | `AUTH_MODE=public`에서 기존 동작 100% 보존(strict 검사는 token 모드 의미와 무관하게 항상? — §5-A V-04에서 확정) | public/token 양모드 스모크 |
| NFR-04 | 원자성 | 폐기 시 두 JTI blacklist + 세션 마킹이 **하나의 트랜잭션**(부분 폐기로 refresh만 남는 상태 금지) | 트랜잭션 롤백 시나리오 테스트 |
| NFR-05 | 무회귀 — 관리자 | 정상 active·unlocked 사용자와 base-ADMIN은 영향 없음(로그인·refresh·API 정상) | 회귀 스모크 |

---

## 3. 기술 설계

### 아키텍처 결정 및 이유

**결정 1 — 공통 폐기 서비스(`revoke_session_family`) 단일 진입점.**
분석 §12.2 방향. 현재 폐기 로직이 logout/중복로그인/lock 등에 흩어져 refresh 누락·TTL 불일치가 발생. 하나의 서비스로 모으면 "access+refresh 둘 다, 실제 exp로, 원자적으로" 규칙이 강제된다.

```python
# app/services/session_revoke_service.py (신설)
async def revoke_session_family(
    db: AsyncSession,
    session: UserSession,
    reason: str,
    actor_id: int | None = None,
    publish_nats: bool = True,
    commit: bool = False,
) -> None:
    # 1) session.token / session.refresh_token 을 decode → 각 jti + 실제 exp 추출
    # 2) 두 jti 를 add_to_blacklist_async (expires_at = 각 JWT 의 exp claim)  ← TTL 추정 제거
    # 3) session.is_active=False, logged_out_at=naive KST, logout_reason=reason
    # 4) publish_nats and NATS_REVOKE_ENABLED → publish_session_revoke (best-effort, lock 밖)
    # 5) commit=True 면 await db.commit(), 아니면 caller 트랜잭션에 참여
```

**결정 2 — 인증 권위는 "JWT + 상태" 이원.** 매 요청 세션 DB 조회(§12.1 full model)는 비용이 크므로, **1차로 user 상태(is_active/is_locked)**만 strict에 추가(FR-02). **세션 상태 검사(sid 존재/활성)**는 refresh에 우선 적용(FR-03)하고, 매 요청 세션 검증은 이번 범위에서 제외(Out of Scope, 후속). 잠금 즉시성은 lock이 token을 blacklist(FR-05)하므로 blacklist hit로 보장.

**결정 3 — TTL은 JWT 실제 `exp` 사용.** 설정값 추정(24h/7d) 대신 decode한 `exp` claim을 blacklist.expires_at으로 저장(ACC-P1-02 동반 해결). `session_enabled=false`(10년 토큰)와 TTL 불일치 제거.

### 주요 컴포넌트

| 컴포넌트 | 변경 |
|---|---|
| `app/services/session_revoke_service.py` | **신설** — `revoke_session_family` |
| `app/routers/auth.py` | strict 인증 상태검사(FR-02), refresh 검증순서 재배치(FR-03), 중복로그인 폐기 교체(FR-04) |
| `app/routers/users.py` | lock/delete(deactivate)/reset-password가 `revoke_session_family` 호출(FR-05) |
| `app/services/token_blacklist_service.py` | `add_to_blacklist_async`가 exp claim 기반 TTL 수용(이미 expires_at 파라미터 존재 → 호출측에서 exp 전달) |
| `tests/test_session_authority.py` | **신설** — A01~A18 |

### 데이터 모델
스키마 변경 없음. 기존 `UserSession(token, refresh_token, is_active, expires_at, logout_reason, logged_out_at)` + `TokenBlacklist(jti, expires_at, reason, token_type)` 재사용. (분석 §4.2 권장 JTI/hash 저장 마이그레이션은 Out of Scope — 별도 PRD.)

### API/인터페이스 설계
외부 API 계약(요청/응답 스키마) **무변경**. 동작만 강화:
- 잠긴/비활성 계정의 보호 API 호출: 200 → **401**
- 세션 부재/비활성 refresh: 200(새 토큰) → **401**
- 중복 로그인 후 이전 refresh로 refresh: 200 → **401**

---

## 4. 범위

### In Scope
- FR-01~06 (공통 폐기 서비스, strict 상태검사, refresh 검증, 중복로그인·lock/deactivate/reset 폐기 통합, 실제 exp TTL, A01~A18)

### Out of Scope (후속 PRD)
- 매 요청 세션 상태 DB 검사(§12.1 full model) — 성능 설계 필요
- refresh rotation race compare-and-swap(ACC-P1-07) — 동시성 별도
- UserSession token 원문 → JTI/hash 저장 마이그레이션(ACC-P1-10)
- 실패 로그인 UserLoginLog + rate limit(ACC-P1-09)
- 멀티 인스턴스 cache invalidation, inactive group/device scope 집행, auth 완전 async화(refresh의 sync get_db)
- 고정 ADMIN·개발 키(SEC-02, 사용자 보류)

---

## 5. 의존성 및 전제 조건
- `decode_token`이 `exp`/`jti`/`sid` claim을 안정적으로 반환(기존 사용 중)
- `add_to_blacklist_async` / `is_blacklisted_async` (기존)
- `publish_session_revoke` (기존, NATS_REVOKE_ENABLED 게이트)
- 이번 세션에서 등록한 blacklist cleanup 스케줄러(ACC-P1-05, 완료) — TTL 이후 정리

---

## 5-A. 검증 필요 항목 (Verification Prerequisites)

| ID | 검증 항목 | 검증 방법 | 확인 여부 |
|----|---------|---------|---------|
| V-01 | 현재 발급 토큰에 `sid` claim이 항상 존재하는가 | 활성 세션 토큰 decode | ✅ **확인** — 활성 세션(id=398) 토큰 sid=398 존재. sid 없는 레거시는 refresh에서 skip 폴백 유지 |
| V-02 | `UserSession.expires_at` 만료정책 의미 | 코드 확인(auth.py:468, session_sweep) | ✅ **확인** — expires_at=**access 만료**. refresh 검증은 `is_active` 기준(expires_at 사용 시 정상 refresh 오거부). FR-03 반영 |
| V-03 | refresh 핸들러 sync `get_db` 영향 | auth.py:649 | ✅ **확인** — refresh는 `db: Session=Depends(get_db)`(sync). 검증도 sync 쿼리로 최소 추가(async 전환은 Out of Scope) |
| V-04 | strict 상태검사 public 모드 적용 여부 | strict 사용처 확인 | ✅ **확인** — strict는 이미 bearer 필수(reports/users/… 직접 사용, 양 모드 토큰 요구). is_active/is_locked 무조건 적용 안전(모드 분기 불요) |
| V-05 | `session.token`이 항상 decode 가능한 원문인지 | 로그인 경로(auth.py:461-484) | ✅ **확인** — placeholder는 flush용 임시, 발급 후 실토큰 교체(483-484). 활성 세션은 실토큰. revoke 서비스는 decode 실패 방어(세션 마킹은 유지) |

---

## 5-B. 인과 결합 분석 (Causal Coupling Analysis)

| 수정 항목 | 영향 받는 다른 플로우 | 대응 방안 |
|---------|-------------------|---------|
| strict 인증에 is_active/is_locked 검사(FR-02) | **모든 보호 API**. 정상 사용자엔 무영향, 그러나 "비활성인데 쓰던" 통합/머신 계정이 있으면 차단될 수 있음 | 배포 전 active=false 계정 사용 현황 점검(V), 회귀 스모크 |
| refresh 검증 순서 재배치(FR-03) | **.NET 클라 refresh 플로우**. 정상 세션은 무영향, 그러나 클라가 세션종료 후에도 refresh 재시도하면 이제 401 | 클라 통지(NOTIFY 문서), 401 처리 확인 |
| 중복로그인 refresh 폐기(FR-04) | 같은 계정 다중기기 사용자 → 새 로그인 시 이전 기기 완전 로그아웃(현재는 access만) | 의도된 강화. 다중세션 허용정책이면 재검토(현재 DUPLICATE 정리 정책 유지 전제) |
| lock/deactivate token 폐기(FR-05) | 관리자 lock UX — 이제 즉시 무효 | 마지막 ADMIN lock 가드(ACC-P1-08, 완료)와 결합해 관리자 lockout 방지 |
| exp 기반 TTL(FR-01) | blacklist row TTL이 길어질 수 있음(10년 토큰) | cleanup 스케줄러(완료)가 exp 후 정리 |

---

## 6. 리스크

| 리스크 | 가능성 | 영향 | 대응 방안 |
|--------|--------|------|---------|
| auth 코어 변경으로 전체 로그인/refresh 회귀 | 중간 | 치명 | 롤백 태그 필수, 단계적(FR-02→05 순), A01~A18 회귀 게이트, 정상 사용자 스모크 |
| 비활성/머신 계정 차단으로 통합 파손 | 중간 | 높음 | V로 사용현황 점검, 필요시 예외 정책 |
| refresh sync get_db와 async 혼용 부작용 | 낮음 | 중간 | V-03 확인 후 최소 변경, 필요시 async 전환은 별도 |
| placeholder 토큰 decode 실패로 폐기 누락 | 낮음 | 중간 | V-05, revoke 서비스에서 decode 실패 방어(세션 마킹은 유지) |

---

## 7. 완료 기준 (Definition of Done)

- [ ] FR-01~06 구현 완료
- [ ] NFR-01 회귀(A01~A18) 전부 통과 — 특히:
  - A01 잠긴 계정 기존 access → 401
  - A02 비활성 계정 기존 access → 401
  - A03 잠긴/비활성 refresh → 401
  - A04 세션 부재/비활성/만료 refresh → 401
  - A05 중복로그인 이전 access/refresh 둘 다 → 401
  - A07 admin reset 후 이전 토큰 → 401
  - A08 lock/deactivate 후 세션 family → 401
  - A11 10년 토큰 revoke → 실제 exp까지 blacklist 유지
- [ ] NFR-05 무회귀: 정상 사용자·base-ADMIN 로그인/refresh/API 정상
- [ ] 선결 검증 V-01~V-05 확인
- [ ] 단위 테스트 `should_X_when_Y` 명명
- [ ] 5중 싱크(코드·Swagger·명세서·Image·Container) + CHANGELOG
- [ ] .NET 클라 통지 문서(동작 강화 3건: 잠금/세션종료/중복로그인 후 401)
- [ ] 롤백 태그 생성 후 착수, 검증 후 정리
