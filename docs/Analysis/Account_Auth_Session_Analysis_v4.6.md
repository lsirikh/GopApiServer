# Account / Auth / Session 종합 분석 보고서 v4.6

> **작성일**: 2026-06-19 | **분석 범위**: 10개 feature / 30개 endpoint / OWASP Top 10 / 매니저 영향 / 잔존 위험
> **종합 판정**: **FAIL** (Critical 13건 포함, 평균 완성도 62.5%)

---

## 1. Executive Summary

**결론**: Account/Auth/Session 도메인은 **기능 동작은 가능하나 군 시스템 보안 기준 미달**입니다. 30개 endpoint가 모두 구현되었고 bcrypt/JWT 인프라도 작동하나, **Critical 13건 / High 38건 / Medium 39건 / Low 23건 / Info 1건 (총 114건)** 이 식별되었고 verifier가 추가 9건(GLOBAL)을 발견했습니다.

**가장 시급한 리스크 3건**: (1) **모든 mutation endpoint에 RBAC 부재** — VIEWER 토큰으로 ADMIN 계정 생성·삭제·잠금·세션 강제 종료 가능 (F06-I01, F08-S01, F09-S01, F10-S01). (2) **Logout/잠금 후 JWT가 만료까지 유효** — 세션 무효화 우회로 매니저(VMS/NVR/Speaker) 제어 권한이 탈취 토큰으로 통과 (F01-S-01, F02-001, F08-S02, F10-S02). (3) **Refresh 엔드포인트가 token type을 검증하지 않음** — access_token으로 7일 refresh 발급 가능 (F03-I01).

**완성도 평균 62.5%**, **OWASP 커버리지 41점/100점**. 매니저 통합 직접 영향은 중간이나, 인증 계층이 전 매니저 호출의 전제이므로 **간접 영향은 전체**입니다. v4.6~v4.7 차수에 분할 적용 권고: P0 6건(약 24h) → P1 11건(약 44h) → P2 30건(약 96h).

---

## 2. 통계 카드

| 지표 | 값 | 비고 |
|------|---:|------|
| 총 Feature | 10건 | F01~F10 |
| 총 Endpoint | 30건 | inventory 기준 |
| Critical 이슈 | 13건 | 즉시 패치 권고 |
| High 이슈 | 38건 | v4.6 차수 내 처리 |
| Medium 이슈 | 39건 | v4.7 차수 |
| Low 이슈 | 23건 | v5 major 또는 백로그 |
| Info 이슈 | 1건 | UX 개선 제안 |
| Verifier 추가(GLOBAL) | 9건 | High 2 / Medium 4 / Low 3 |
| **총 이슈** | **114건** | refuted 0건 |
| 평균 완성도 | **62.5%** | 최저 F03/F05 55%, 최고 F04 82% |
| OWASP 커버리지 점수 | **41/100** | A01·A04·A07·A09 다수 FAIL |
| AuditLog 커버리지 | full 1 / partial 5 / missing 4 | F06만 full |

---

## 3. Feature별 상세 표 (10건)

| ID | Feature | 완성도 | C/H/M/L | Audit | 매니저 영향 | 핵심 결함 |
|----|---------|------:|:-------:|:-----:|:----------:|----------|
| F01 | 로그인 (POST /auth/login) | 62% | 2/4/3/3 | missing | 중(간접) | 세션 무효화 우회, refresh type 미검증 |
| F02 | 로그아웃 (POST /auth/logout) | 55% | 1/3/3/2 | partial | 중 | JWT 미무효화, AuditLog 누락 |
| F03 | 토큰 갱신 (POST /auth/refresh) | 55% | 2/3/3/2 | missing | 무(직접) | type 클레임 미검증, rotation 부재 |
| F04 | 현재 사용자 (GET /auth/me) | 82% | 0/1/3/2 | missing | 무(직접) | 세션 검증 부재, last_login_at NULL |
| F05 | OAuth2 Legacy (POST /login/oauth2) | 55% | 3/4/2/1 | missing | 무(직접) | RBAC·잠금·revoke 모두 부재 |
| F06 | User CRUD (/users + /users/{id}) | 72% | 1/3/7/3 | **full** | 높음 | RBAC 부재, self-delete 가드 없음 |
| F07 | 비밀번호 변경 (PUT /users/me/password) | 55% | 1/4/3/2 | partial | 중 | 세션 무효화 누락, 정책 미구현 |
| F08 | 잠금/해제/리셋 (POST /users/{id}/lock\|unlock\|reset) | 62% | 2/4/5/1 | partial | 높음 | RBAC 부재, JWT 미무효화 |
| F09 | UserGroup CRUD (/user-groups) | 72% | 1/3/3/2 | partial | 중 | RBAC 부재, 권한 자기상승 가능 |
| F10 | Session 관리 (/user-sessions/*) | 62% | 1/3/4/3 | partial | 중 | RBAC 부재, logout_reason enum drift |

> **요약**: F04(/me) 외 9건이 완성도 75% 미만. F06만 AuditLog full. C(Critical) 합계 14건은 F01·F02·F03·F05·F06·F07·F08·F09·F10에 골고루 분포 — **공통 결함은 RBAC 부재와 JWT 무효화 부재**.

---

## 4. 발견된 이슈 종합 (severity별)

### 4.1 Severity 분포 요약

| Severity | 건수 | 누적 공수(h) | 권고 차수 |
|----------|----:|-----------:|----------|
| Critical | 13 | ~50h | v4.6 즉시 |
| High | 38 | ~115h | v4.6 |
| Medium | 39 | ~95h | v4.7 |
| Low | 23 | ~35h | v5 major / 백로그 |
| Info | 1 | ~2h | 백로그 |
| GLOBAL High | 2 | ~10h | v4.6 |
| GLOBAL Medium | 4 | ~16h | v4.7 |
| GLOBAL Low | 3 | ~6h | 백로그 |
| **합계** | **123** | **~329h** | — |

### 4.2 Critical 13건 상세

| ID | Feature | Title | 공수 |
|----|---------|-------|----:|
| F01-S-01 | F01 | Logout 후 토큰이 만료까지 유효 (세션 무효화 우회) | 4h |
| F01-S-02 | F01 | Refresh 엔드포인트가 access_token으로 동작 (type 미검증) | 1h |
| F02-001 | F02 | JWT 토큰 무효화 부재 — logout 후 24h 유효 | 5h |
| F03-I01 | F03 | Refresh token type claim 미검증 | 2h |
| F03-I02 | F03 | Refresh token rotation 미흡 — 재사용 detection 불가 | 6h |
| F05-S01 | F05 | Legacy User 토큰 발급 시 is_active/is_locked 미검사 | 2h |
| F05-S02 | F05 | 감사 로그 전무 (UserLoginLog/AuditLog) | 3h |
| F05-S03 | F05 | UserSession 미생성 → logout revoke 불가 | 4h |
| F06-I01 | F06 | 관리자 전용 mutation에 RBAC 미적용 | 6h |
| F07-01 | F07 | 비밀번호 변경 후 세션/토큰 무효화 누락 | 4h |
| F08-S01 | F08 | RBAC 부재 — 모든 인증자가 lock/unlock/reset 호출 | 2h |
| F08-S02 | F08 | 잠금된 사용자 JWT가 만료 시까지 유효 | 3h |
| F09-S01 | F09 | RBAC 미적용 — 비-ADMIN이 그룹 CRUD/권한 수정 | 6h |
| F10-S01 | F10 | RBAC 부재 — OPERATOR가 ADMIN 세션 강제 종료 가능 | 4h |
| **합계** | | | **~52h** |

### 4.3 High 38건 핵심 (요약, 전체 표는 부록)

| 카테고리 | 대표 이슈 | 영향 |
|----------|----------|------|
| Rate Limiting 부재 | F01-S-03, F02-006, F03-I07, F06-I03, F08(rate), F07-04 | brute-force / DoS 무방어 |
| AuditLog 누락 | F01-A-04/05, F02-002, F03-I05, F05-S02, F07-04 | 보안 감사 추적 불가 |
| 세션 무효화 부재 | F03-I04, F04-I01, F07-01, F08-S04 | 비밀번호 변경 후에도 토큰 유효 |
| spec drift | F01-D-10, F02-003, F05-S05/S06, F08-S06, F09-S03/S07 | envelope·enum·필드 불일치 |
| 비밀번호 정책 | F06-I08/I09, F07-02/03/05 | NIST 미달 / 만료 / 재사용 |
| Self/Last-admin 가드 | F06-I02 | 시스템 락아웃 가능 |

### 4.4 Verifier 발견 GLOBAL 9건

| Severity | Title | 영향 |
|----------|-------|------|
| High | CORS 화이트리스트 검증기 부재 (`*` + credentials 디폴트) | prod 배포 가드 미흡 |
| High | 보안 응답 헤더 미설정 (HSTS/X-Frame/CSP 등) | 토큰 절취/클릭재킹 |
| Medium | log_action 실패 시 감사 로그 무음 손실 | '몰래 변경' 가능 |
| Medium | AuditLog 무결성 보호 부재 (변조/삭제 방어 없음) | A09 |
| Medium | JWT realm 미분리 (Legacy ↔ Account 토큰 혼용) | 권한 모호 |
| Medium | 동시 로그인/멀티 디바이스 정책 enforce 부재 | DUPLICATE/MAX 무력화 |
| Low | 사용자 삭제 시 user_login_logs 영속 보존 (익명화 없음) | 개인정보 보호 |
| Low | Request body 최대 크기 제한 부재 | DoS via 거대 JSON |
| Low | Refresh token jti dead claim | rotation 미적용 |

---

## 5. OWASP A01~A10 매핑 표

| OWASP | 위협 | 코드 | 평가 | 비고 |
|-------|------|------|:----:|------|
| A01 | Broken Access Control | F06/F08/F09/F10 RBAC 부재 | **FAIL** | 모든 mutation 무방어 |
| A02 | Cryptographic Failures | bcrypt OK, 토큰 평문 저장 | **PARTIAL** | F10 token at-rest 평문 |
| A03 | Injection | SQLAlchemy ORM + Pydantic | **PASS** | permissions free-form 제외 |
| A04 | Insecure Design | Logout/lock 후 JWT 유효 | **FAIL** | 세션 무효화 우회 |
| A05 | Security Misconfiguration | JWT_SECRET validator | **PARTIAL** | CORS 가드 미적용 |
| A06 | Vulnerable Components | 의존성 스캔 미확인 | **NA** | 본 분석 범위 외 |
| A07 | Identification & Auth Failures | rate limit / refresh rotation / enumeration | **FAIL** | 다수 결함 |
| A08 | Software & Data Integrity | jose JWT 서명, Pydantic 강타입 | **PASS** | 감사 무결성은 별건 |
| A09 | Logging Failures | AuditLog 9/10 partial-missing, IP/UA 누락 | **FAIL** | 추적성 결손 |
| A10 | SSRF | 외부 호출 없음 | **NA** | 본 도메인 무관 |

**점수**: PASS 2 · PARTIAL 2 · FAIL 4 · NA 2 → **41/100 (Top 10 본질 항목 8건 기준)**

---

## 6. Top 권고 사항 (우선순위 5건)

| 순위 | 권고 | 대상 이슈 | 공수 | 우선 차수 |
|----:|------|----------|----:|----------|
| 1 | **require_admin / require_role 의존성 신설 후 모든 mutation·세션 관리에 일괄 적용** | F06-I01, F08-S01, F09-S01, F10-S01 | 6h | v4.6 |
| 2 | **get_current_account_user에 user_sessions 활성 검증 추가 + is_active/is_locked 가드** (JWT 무효화 우회 해결) | F01-S-01, F02-001, F04-I01, F07-01, F08-S02, F10-S02 | 6h | v4.6 |
| 3 | **decode_refresh_token 분리 + payload['type']=='refresh' 강제 + refresh rotation/blacklist** | F03-I01, F03-I02, F03-I03, F03-I04 | 8h | v4.6 |
| 4 | **AuditLog 본문 보강(before/after, ip, ua, changes) + log_action best-effort 처리** + SESSION_CREATED/REFRESH/FAILURE 기록 | F01-A-04/05, F02-002, F03-I05, F05-S02, F06-I05, F08-S07, F09-S03/S05, GLOBAL log_action | 10h | v4.6 |
| 5 | **비밀번호 정책 정비 + 변경 시 세션 무효화 + password_changed_at 갱신 + 만료/재사용 금지** | F06-I08/I09, F07-01/02/03/05 | 15h | v4.7 |

---

## 7. 매니저 통합 영향

| 매니저 | 직접 영향 | 간접 영향 | 핵심 시나리오 |
|--------|:---------:|:---------:|--------------|
| GIS | 무 | 중 | RBAC 부재 시 GIS 도구·device_group 권한 무력화(F09-S02) |
| VMS | 무 | **높음** | 도난 토큰 24h 유효 → PTZ 제어/라이브뷰 우회(F01-S-01) |
| NVR | 무 | **높음** | 잠금된 사용자 토큰 → 녹화/재생 제어 우회(F08-S02) |
| Speaker | 무 | **높음** | logout 후에도 방송 명령 가능(F02-001) |

**결론**: 인증/세션 계층 변경은 **매니저 직접 통신 없음**이나 **JWT 검증을 매니저들이 동일하게 신뢰**하므로 간접 영향은 전반에 걸침. v4.6 P0 적용 시 매니저별 별도 호환성 영향은 **없음**(추가 검증만 강화).

---

## 8. 차장님 결재 사항

| # | 결재 사항 | 옵션 | 권고 |
|--:|----------|------|------|
| 1 | **JWT 무효화 전략** | (a) user_sessions JOIN 검증 / (b) Redis jti 블랙리스트 | (a) 우선, (b)는 v5 |
| 2 | **PermissionsSchema 구조** | (A) List[str] / (B) Dict-of-Dict (view/edit/delete) | (B) 권장 — spec과 일치 |
| 3 | **EnumLogoutReason 통일** | (A) SELF_LOGOUT 추가 / (B) DUPLICATE 유지 + MANUAL 통합 | (B) — 마이그레이션 스크립트 동반 |
| 4 | **동시 세션 정책(MAX_SESSIONS)** | (a) 자동 종료(DUPLICATE) / (b) 신규 거부 / (c) 비활성 | (a) 권장 — 운영자 UX |
| 5 | **OAuth2 Legacy 제거 시점** | (a) v4.6 즉시 410 / (b) v4.7 Sunset 헤더 후 / (c) v5 | (b) — Ironwall SDK 영향 확인 |
| 6 | **비밀번호 정책 (NIST/군 기준)** | 길이 8/12, 복잡도 3/4종, 만료 90일 | 길이 12·4종·90일·재사용 5건 금지 |
| 7 | **CORS prod 가드 신설** | validator 추가하여 staging/prod에서 `*` 거부 | 즉시 적용 |
| 8 | **감사 로그 무결성** | (a) WORM trigger / (b) hash chain / (c) 외부 SIEM 전송 | (a)+(c) 병행 |
| 9 | **user_login_logs 보존/익명화** | (a) 무기한 / (b) N년 + 익명화 / (c) 외부 보관 | PRD 별도 결재 |

---

## 9. 작업 분량 추정

### 9.1 총 합계

| 차수 | Severity 범위 | 공수 | 비고 |
|------|--------------|----:|------|
| v4.6 (즉시) | Critical 14 + High P0 5 | ~52h + 24h = **~76h** | RBAC + JWT 무효화 + refresh + audit |
| v4.6 (가능 시) | High 나머지 + GLOBAL High 2 | **~90h** | rate limit, spec drift, CORS, 헤더 |
| v4.7 | Medium 39 + GLOBAL Medium 4 | **~111h** | 비밀번호 정책, lock_reason, last_activity |
| v5 / 백로그 | Low 23 + Info 1 + GLOBAL Low 3 | **~42h** | UX, 페이지네이션, 익명화 |
| **합계** | 123건 | **~319h** | |

### 9.2 우선순위별 권고 패키지

| 패키지 | 포함 이슈 | 공수 | 차수 |
|--------|----------|----:|------|
| **P0-A** RBAC 일괄 적용 | F06-I01, F08-S01, F09-S01, F10-S01 | 6h | v4.6 |
| **P0-B** 세션 검증 | F01-S-01, F02-001, F04-I01, F07-01, F08-S02, F10-S02 | 6h | v4.6 |
| **P0-C** Refresh 보강 | F03-I01/I02/I03/I04 | 8h | v4.6 |
| **P0-D** AuditLog 보강 | F01-A-04/05, F02-002, F05-S02, F06-I05, F08-S07, F09-S03/S05 + GLOBAL audit | 10h | v4.6 |
| **P0-E** 비밀번호 변경 세션 무효화 + 정책 골격 | F07-01/02/03 | 5h | v4.6 |
| **P1-A** Rate limiting 도입 | F01-S-03, F02-006, F03-I07, F06-I03, F07-04 | 12h | v4.6 |
| **P1-B** Spec drift 통일 | F01-D-10/D-11, F02-003, F08-S06, F09-S07, F10-S04 | 10h | v4.6 |
| **P1-C** Self/Last-admin/시스템 그룹 보호 | F06-I02, F09-S04 | 6h | v4.6 |
| **P1-D** CORS/보안 헤더 | GLOBAL 2건 | 6h | v4.6 |
| **P2-A** 비밀번호 만료/재사용 금지 | F06-I08, F07-03/05 | 14h | v4.7 |
| **P2-B** Last activity / MAX_SESSIONS | F10-S05/S06 | 9h | v4.7 |
| **P2-C** Lock metadata / Permissions 강타입 | F08-S06, F09-S02/S07 | 16h | v4.7 |

---

## 10. 잔존 위험 (계속 모니터링)

| # | 위험 | 모니터링 지표 | 대응 시점 |
|--:|------|-------------|----------|
| 1 | **JWT stateless + 무효화 부재**의 근본 한계 — user_sessions JOIN으로 임시 완화 후에도 분산 환경에서 race 가능 | 강제 로그아웃 후 401 누설 빈도, 매니저 401 분포 | v5: Redis 블랙리스트 도입 |
| 2 | **Legacy User / AccountUser** 이중 인증 경로 — F05 제거 전까지 sub 네임스페이스 충돌 위험 | /login/oauth2 호출량, Ironwall SDK 사용 여부 | F05 410 전환 시 해소 |
| 3 | **permissions JSONB free-form** — 권한 모델이 enforce 코드에 흡수되기 전까지 자기상승 위험 | NATS subscription 권한 필터 적용 여부 | v4.7 PermissionsSchema 결재 후 |
| 4 | **AuditLog 무결성** — WORM/hash chain 없으면 ADMIN 또는 DBA가 사후 변조 가능 | audit_logs UPDATE/DELETE 통계, 백업 비교 | v5: trigger 도입 |
| 5 | **동시성 race** (failed_login_count, force_logout 동시 호출, name 중복) | 자동 잠금 우회 빈도, force_logout 이중 commit | 모니터링 후 v4.7 패치 |
| 6 | **개인정보 보존 정책** — user_login_logs/IP 무기한 보존 | retention 정책 결재 | PRD 별도 |
| 7 | **CORS_ORIGINS 디폴트 `*`** — .env 누락 시 prod 사고 | 환경별 validator 적용 여부 | P1-D 적용 시 해소 |
| 8 | **PRD_Account_Design.md ↔ 코드 비밀번호 정책 drift** — 8자 vs 6자 등 | password_changed_at 분포, 짧은 비밀번호 비율 | P0-E + P2-A 적용 후 |
| 9 | **매니저 측 JWT 신뢰** — Central 측 보안 강화가 매니저에 전파되지 않으면 우회 가능 | 매니저별 401/403 로그 | 매니저별 패치 동기화 |

---

## 부록: 핵심 코드 위치

- 인증: `app/routers/auth.py` (180~471), `app/utils/auth.py` (14~125)
- 사용자: `app/routers/users.py` (전체 652라인)
- 그룹: `app/routers/user_groups.py` (전체 352라인)
- 세션: `app/routers/user_sessions.py` (전체 354라인)
- 모델: `app/models/user.py` (38~194)
- 스키마: `app/schemas/user.py` (20~343)
- 감사: `app/services/audit_service.py`
- 설정: `app/config.py` (27~84)
- 명세: `c:\workspace_python\api-test-server\GOP_Restful_Api_연동설계.md` §9.2~9.6 (L14101~14600)
