# E1 — 세션 토큰 원문 저장 제거 (jti 저장) PRD

- **작성일**: 2026-07-10
- **상태**: Approved (사용자 배치 승인 "E1→E4 순차 전부")
- **버전**: v1.0
- **언어/프레임워크**: Python / FastAPI (SQLAlchemy 2.x, PostgreSQL 16, JWT HS256)
- **연관 분석**: Account_Auth_Session_Analysis_20260708.md §4.2, ACC-P1-10
- **Stage**: 필수 4건 중 1/4

---

## 1. 개요

### 목적
`UserSession.token`/`refresh_token` 에 **access/refresh JWT 원문**이 저장돼 DB·로그·백업 유출 시 즉시 토큰 탈취가 가능한 노출(§4.2)을 제거한다.

### 배경
- 원문 토큰 = 진짜 크리덴셜(서명 포함). DB 열람자가 그대로 Bearer 로 사용 가능.
- `jti`(JWT ID) = 서명 없는 식별자 → **그 자체로는 위조·인증 불가**(비-크리덴셜). jti 만 저장하면 노출 제거.
- revoke/force_logout 은 어차피 jti 로 블랙리스트하므로, jti 직접 저장 시 **decode 불필요**해져 더 단순.

---

## 2. 요구사항 (FR)

| ID | 요구사항 | 우선순위 | 태스크 |
|----|---------|---------|-------|
| FR-01 | `UserSession.token`/`refresh_token` 컬럼에 **원문 대신 jti** 저장(의미 전환). `refresh_expires_at` 컬럼 신설(access 는 기존 `expires_at`). | High | ~2 |
| FR-02 | 멱등 마이그레이션 — 신 컬럼 추가 + **기존 활성 세션 무효화**(원문→jti 전환 불가 rows 는 is_active=false, 사용자 재로그인) | High | ~2 |
| FR-03 | login/refresh 재바인딩: 발급 토큰의 jti/exp 를 추출(`_extract_jti_exp`)해 token=access_jti, refresh_token=refresh_jti, expires_at=access_exp, refresh_expires_at=refresh_exp 저장 | High | ~3 |
| FR-04 | refresh CAS(P1-07) 를 jti 비교로: `session.refresh_token != token_data.jti` | High | ~1 |
| FR-05 | logout 조회를 jti 로: incoming access decode→jti→`UserSession.token == jti` 조회 | High | ~1 |
| FR-06 | revoke_session_family / force_logout(단건·벌크): **decode 제거**, stored `token`(access_jti)+`refresh_token`(refresh_jti) 를 직접 블랙리스트, 만료는 stored `expires_at`/`refresh_expires_at` 사용 | High | ~3 |

## NFR
| ID | 항목 | 요구사항 | 검증 |
|----|------|---------|------|
| NFR-01 | 보안 | 신규 세션의 token/refresh_token 컬럼에 **JWT 원문(`eyJ...`) 미저장** | DB 조회로 값이 uuid 형태(jti)인지 확인 |
| NFR-02 | 무회귀 | 로그인·refresh·logout·force_logout·lock/reset 폐기 전부 기존과 동일 결과 | 세션권위 E2E(A01~A18) 재실행 |

---

## 3. 기술 설계

**결정 — jti 저장(hash 아님)**: jti 는 비-크리덴셜이라 저장해도 안전하고, revoke 가 decode 없이 바로 블랙리스트 가능. hash 방식은 CAS 는 되나 revoke 가 여전히 decode 필요 → jti 가 더 단순·안전.

**스키마**: `UserSession` 에 `refresh_expires_at DateTime NULL` 추가. `token`(unique,NOT NULL)·`refresh_token`(unique,NULL) 컬럼은 그대로 두되 **내용을 jti 로** 저장(uuid 라 unique 유지). VARCHAR(500) 이라 길이 문제 없음.

**exp 소스**: 블랙리스트 TTL = stored `expires_at`(access)·`refresh_expires_at`(refresh). decode 로 exp 뽑던 것 대체(ACC-P1-02 정합 유지).

**컴포넌트**: `models/user.py`(컬럼), `migrations/v64_*.sql`(신규), `auth.py`(login/refresh/logout), `user_sessions.py`(force logout ×2), `session_revoke_service.py`(decode→stored jti).

---

## 4. 범위
- **In**: 위 FR-01~06.
- **Out**: token hash 이중저장, 세션 조회 API 응답에서 토큰 필드 제거(현재도 원문 미노출), refresh rotation 외 세션 관리 변경.

## 5-A. 검증 필요 (V)
| ID | 항목 | 확인 |
|----|------|------|
| V-01 | logout 핸들러가 incoming access token 을 decode 해 jti 획득 가능한지 | 구현 중 확인 |
| V-02 | force_logout 이 session.token/refresh_token 을 decode 하는 현재 구조 | 구현 중 확인 |
| V-03 | create_access/refresh_token 후 jti/exp 재추출 경로(_extract_jti_exp) 동작 | 구현 중 확인 |

## 5-B. 인과 결합
| 수정 | 영향 | 대응 |
|------|------|------|
| token 컬럼 의미 전환(원문→jti) | logout/force_logout/revoke 전부 이 컬럼 읽음 | 6 사이트 동시 수정, E2E 재검증 |
| 기존 활성 세션 무효화 | 현재 로그인 사용자 재로그인 필요 | ~1 활성 세션, 배포 시점 재로그인 수용 |

## 6. 리스크
| 리스크 | 가능성 | 영향 | 대응 |
|--------|--------|------|------|
| 6 사이트 중 누락으로 폐기 실패 | 중 | 높음 | 롤백태그 + A01~A18 E2E 게이트 |
| 마이그레이션이 기존 세션에 orphan 유발 | 낮음 | 중 | 기존 활성 세션 무효화(깨끗한 전환) |

## 7. DoD
- [ ] FR-01~06 구현
- [ ] 신규 세션 DB에 JWT 원문 미저장(값=jti) 실측
- [ ] A01~A18 E2E 재실행 통과(로그인/refresh/중복/reset/lock 폐기 무회귀)
- [ ] 5중 싱크 + CHANGELOG
- [ ] 롤백태그 생성/정리
