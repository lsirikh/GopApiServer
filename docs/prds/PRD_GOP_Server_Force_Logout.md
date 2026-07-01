# GOP 서버(API) 강제 로그아웃 전파 — 서버측 PRD

- **작성일**: 2026-06-30
- **상태**: Draft
- **버전**: v1.0
- **위치/이관**: api-test-server `docs/prds/`. 서버 세션이 구현·관리. 원작성=2026-06-30 .NET GOP 세션.
- **대상 레포**: `api-test-server` (FastAPI / SQLite·PostgreSQL / NATS)
- **짝 PRD(클라)**: Ironwall.Dotnet.Libraries `docs/prds/GOP_Force_Logout_Propagation-prd.md` (클라 수신·GIS 로그아웃 전환, FR-FL-01~12)
- **근거**: 시뮬레이션 `wf_51097e44`(52 시나리오 / 51 갭) 중 **서버 계약 11항**.

> 📍 본 PRD는 강제 로그아웃 실시간 전파의 **서버(API) 측만** 분리. 클라 전환 UI/로그아웃 흐름은 짝 PRD. ⚠️ 서버 변경 = **5-sync + 도커 재빌드**.
> 핵심: 현재 force_logout은 jti 블랙리스트만 하고 **(a) 대상 클라에 실시간 통지 채널 없음 (b) 로그인 응답에 session_id 없음·JWT jti 매칭키 미보장 (c) refresh 패밀리 미무효화 (d) 블랙리스트 비영속**.

---

## 변경 이력

| 날짜 | 버전 | 변경 항목 | 변경 이유 | 영향 범위 |
|------|------|---------|---------|---------|
| 2026-06-30 | v1.0 | 초안(52시나리오 시뮬 서버계약) | 강제 로그아웃이 실시간 전파되려면 서버가 식별자 제공·토큰패밀리 무효화·NATS 발행·서명을 보장해야 함 | auth·user_sessions·tokens·NATS 발행·DB |

---

## 1. 개요

### 목적
관리자 강제 로그아웃 시, 대상 세션을 **확실히 무효화**하고 대상 클라에 **실시간 revoke를 안전하게 발행**하여 클라가 즉시 로그아웃 전환할 수 있도록 서버가 보장한다.

### 배경
- `auth.py`: access JWT에 jti 부여 여부/로그인 응답 session_id 부재 — 클라가 '내 세션' 식별 불가.
- 로그아웃/force_logout 시 access·refresh 토큰 패밀리 원자 무효화 미보장 → 401 폴백이 refresh로 부활 가능.
- jti 블랙리스트가 인메모리면 재기동 시 부활.
- per-session 타깃 NATS 발행 스킴·서명·발행 ACL 부재.

---

## 2. 기능 요구사항 (FR-SVF)

| ID | 우선 | 요구사항 |
|----|----|----|
| **FR-SVF-01** | High | 로그인(POST /auth/login)·refresh 응답 data에 **불변 session_id** 포함(세션 수명 동안 고정, refresh로 회전 안 함). |
| **FR-SVF-02** | High | access JWT에 **jti 클레임 실제 발급**(클라 매칭키), session_id를 **sid 클레임 또는 응답 필드**로 제공. |
| **FR-SVF-03** | High | force_logout 시 해당 세션의 **access+refresh jti(토큰 패밀리) 원자적·동시 블랙리스트** — refresh 반드시 실패. (현재 로그아웃 시 access조차 미블랙리스트 → 계약 확정) |
| **FR-SVF-04** | High | jti 블랙리스트 **영속 저장소(DB/Redis)** 보관 + 서버 재기동 시 활성세션 재검증. 인메모리 비영속 구성 금지. |
| **FR-SVF-05** | High | revoke를 **단일 세션 전용 NATS subject**로만 발행(`{domain}.{group}.all.>` 광역 금지). 클라 구독 와일드카드(EffectiveSubject/all.>)에 매칭되는 subject 스킴 확정. |
| **FR-SVF-06** | High | revoke 페이로드 스키마 + null 의미 문서화: `{message_id(UUID), session_id, jti, user_id, reason(enum 코드), issued_at(ts), signature}`. jti 있으면 해당 세션만 / jti 부재+user_id면 해당 user 전 세션. |
| **FR-SVF-07** | Mid | 페이로드 **서버 비밀키 서명(HMAC/JWS)** + issued_at 포함(클라 서명·replay 윈도우 검증 가능케). |
| **FR-SVF-08** | Mid | NATS revoke **발행 권한을 서버 계정으로 제한**(account/subject publish ACL) — 클라 공유 자격으로 임의 발행 불가. |
| **FR-SVF-09** | High | **last-ADMIN 보호**를 DELETE /user-sessions/{id}와 NATS 직접 발행 **양 경로** 모두 서버 권위 집행. |
| **FR-SVF-10** | Mid | 폐기 세션의 보호 API 응답 **401 통일**(권장) 또는 revoked 403을 `WWW-Authenticate error="revoked"`로 구분 가능하게(클라 폴백 일관 처리). |
| **FR-SVF-11** | Mid | force_logout은 **NATS 발행 성공에 비의존**(블랙리스트가 무효화 권위). 발행 실패는 로깅·모니터링·재시도하되 클라 무한대기 미유발. |
| **FR-SVF-12** | Mid | reason은 **사전 정의 사유 코드(enum)** 집합으로 한정, 자유 텍스트/URL 미발행(클라 피싱 표면 제거). |

### 비기능 요구사항

| ID | 항목 | 요구사항 | 검증 |
|----|------|---------|------|
| NFR-SVF-01 | 보안-무효화 | force_logout 후 해당 세션 access·refresh 모두 거부(401) | pytest: 폐기 후 refresh 401 |
| NFR-SVF-02 | 영속성 | 재기동 후에도 폐기 jti 거부 유지 | 재기동 시나리오 |
| NFR-SVF-03 | 보안-발행 | revoke 발행은 서버만, 서명 검증 가능 | ACL/서명 테스트 |
| NFR-SVF-04 | 가용성 | last-ADMIN 잠금 방지 | 마지막 ADMIN 세션 강제로그아웃 거부 테스트 |

---

## 3. 기술 설계 (지점)
- `app/utils/auth.py`: `create_access_token`에 jti 부여 확인(이미 jti 추가됨 — sid/session_id 제공 추가), 로그인 응답에 session_id.
- `app/routers/auth.py` 로그인: UserSession 생성 시 session_id 발급·반환.
- `app/routers/user_sessions.py` force_logout(DELETE): access+refresh jti 패밀리 블랙리스트 + NATS revoke 발행(서명).
- `app/services/token_blacklist_service.py`: 영속화(DB 모델 `token_blacklist` 존재 — 확인) + 재기동 재검증.
- NATS 발행 유틸: 단일 세션 subject + 서명 + ACL.

---

## 4. 범위
### In Scope
- session_id/jti 제공, 토큰 패밀리 무효화, 영속 블랙리스트, per-session NATS revoke(서명/ACL), last-ADMIN 보호, 401 통일.
### Out of Scope
- 클라 수신·UI 전환(짝 PRD). 다중 인스턴스 NATS 라우팅 토폴로지.

## 5-A. 검증 필요 (V-SVF)
| ID | 항목 | 확인 |
|----|------|----|
| V-SVF-01 | access JWT에 jti 클레임 실제 포함되는가(현 auth.py create_access_token: jti 추가됨) | 확인(jti 있음) |
| V-SVF-02 | 로그인 응답에 session_id 추가가 기존 계약과 충돌 없는가 / sid 클레임 대체 | 미확인 |
| V-SVF-03 | force_logout이 refresh 패밀리까지 무효화하는가(같은 트랜잭션) | 미확인 |
| V-SVF-04 | token_blacklist 영속 저장(모델 존재)·재기동 재검증 동작 | 미확인 |
| V-SVF-05 | 'account.session.revoke' subject가 클라 구독 와일드카드에 매칭되는가 | 미확인(클라와 협의) |

---

## 6. 리스크
| 리스크 | 가능성 | 대응 |
|--------|----|------|
| refresh 패밀리 미무효화 → 401 폴백 부활(보안우회) | 높음 | FR-SVF-03 access+refresh 원자 블랙리스트 |
| 블랙리스트 비영속 → 재기동 부활 | 중간 | FR-SVF-04 영속 + 재검증 |
| 광역 subject 오발행 → 다수 클라 동시 강제로그아웃 | 중간 | FR-SVF-05 단일 세션 subject + FR-SVF-08 ACL |
| 위조 revoke(평문 NATS) → 표적 DoS | 중간 | FR-SVF-07 서명 + FR-SVF-08 ACL |
| last-ADMIN 세션 폐기 → 운영자 잠금 | 중간 | FR-SVF-09 양 경로 보호 |

## 7. 미해결 질문
- session_id 제공: 응답 필드 vs JWT sid 클레임 — 어느 쪽?
- force_logout이 refresh 패밀리를 같은 트랜잭션으로 무효화 가능한가?
- NATS subject publish ACL을 인프라에서 실제 강제 가능한가? 서명키 배포·회전?
- 'account.session.revoke' subject 스킴(클라 구독 와일드카드 매칭) 최종 확정.

## 8. 완료 기준 (DoD)
- [ ] FR-SVF-01~12 구현 + pytest(무효화·영속·서명·ACL·last-ADMIN)
- [ ] NFR-SVF-01~04 통과
- [ ] V-SVF-01~05 확인(클라와 subject/계약 합의)
- [ ] E2E: 강제로그아웃→대상 세션 access/refresh 401, revoke 1회 서명 발행, 타 세션 영향 없음
- [ ] 5-sync + 도커 재빌드
- [ ] 클라 짝 PRD에 계약 확정 통지
