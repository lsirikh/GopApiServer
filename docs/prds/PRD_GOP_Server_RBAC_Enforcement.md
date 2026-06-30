# GOP 서버(API) RBAC 집행 PRD

- **작성일**: 2026-06-29
- **상태**: Draft
- **버전**: v1.0
- **위치/이관**: 본 PRD는 **api-test-server 레포 `docs/`로 이관**됨(서버 세션이 구현·관리). 원작성=2026-06-29 .NET GOP 작업 세션(시뮬레이션 wf_52155656). 승인/plan/dev는 서버 세션이 진행.
- **대상 레포**: `api-test-server` (Python / FastAPI, Docker, PostgreSQL)
- **상위 PRD**(Ironwall.Dotnet.Libraries 레포의 docs/prds/): GOP_Permission_Enforcement-prd.md (권한 실제집행 — 크로스커팅) / GOP_Permission_Gate_Feature-prd.md (PRD-GOP-01 — 모델·매트릭스 권위)
- **시뮬레이션 근거**: `wf_52155656`(22 에이전트, 시나리오 218·발견 99·8도메인) 중 **서버측 도출분**

> 📍 본 PRD는 GOP_Permission_Enforcement에서 **서버(API) 측만 분리**한 것이다. 클라(GMaps.Ui/Devices.Ui/PTZ) 집행은 상위 PRD가 담당. 서버는 별도 레포·팀·배포(5-sync+도커)라 독립 PRD로 추적한다. **권한의 "권위 집행 지점"은 서버 RBAC**(클라는 보조·UX) — FR-PG-13.

---

## 변경 이력

| 날짜 | 버전 | 변경 항목 | 변경 이유 | 영향 범위 |
|------|------|---------|---------|---------|
| 2026-06-29 | v1.0 | 초안 작성 | 서버 RBAC 집행률 0% (AUTH_MODE=public + require_perm 부재) — 시뮬레이션 218시나리오로 확증된 서버측 보안 갭 구체화 | api-test-server 전반(auth·라우터·enums·DB) |
| 2026-06-29 | v1.0 | 서버 레포로 이관 | 서버 작업을 서버 세션에 직접 이관(사용자 지시) | .NET docs/prds → api-test-server docs/ |

---

## 1. 개요

### 목적
GOP API 서버가 권한(등급별 매트릭스)을 **실제로 집행**하도록 한다. 현재 서버는 계정 도메인 `require_admin` 외에는 RBAC을 전혀 집행하지 않으며, `AUTH_MODE=public` + 다수 무인증 엔드포인트로 **curl 직접 호출 시 모든 쓰기 API가 통과**한다.

### 배경 및 동기 (시뮬레이션 확증)
- **서버 RBAC 0%**: `require_role`/`require_admin`은 auth·users·user_groups 3파일에만 존재. cameras/sensors/devices/events/reports 등 비계정 라우터는 `get_current_user_optional`(레거시, jti 미검사) 또는 무인증.
- **AUTH_MODE=public**: `get_current_user_optional`이 None 허용 → 비인증 요청 통과. require_perm 추가해도 단독으론 무력.
- **T4 LIVE**: `DELETE /user-sessions`에 `require_admin` 누락 → VIEWER가 ADMIN 세션 종료. *jti 블랙리스트 부분은 본 PRD 진행 중 선반영(`980abbc`)*.
- **reports.py 완전 무인증**: 토큰 없이 보고서·템플릿 CRUD(PII 집계 노출).
- **jti 블랙리스트 도메인 불일치**: 계정도메인만 jti 검사 → 로그아웃/강등 후 구 JWT로 비계정 write API 24h 지속.
- **마지막 ADMIN TOCTOU**, **감사 append-only DB 미강제**(ORM/마이그레이션 우회 가능).

---

## 2. 요구사항

### 기능 요구사항 (FR)

> 우선순위: **P0(보안 긴급) → P1(집행 기반) → P2(보강)**. 모든 서버 변경은 **5-sync(코드·명세서·swagger·도커이미지·컨테이너) + 안전점 태그** 필수.

| ID | 요구사항 | 우선순위 | 예상 태스크 |
|----|---------|---------|-----------|
| **FR-SV-01** | **T4 긴급**: `user_sessions.py` `DELETE /{session_id}`·`DELETE /user/{user_id}`·`GET ` 에 `Depends(require_admin)` 추가. force_logout(단건+벌크) 처리 후 피해자 access+refresh **jti `add_to_blacklist`**. ※단건 jti는 `980abbc`로 선반영 — **require_admin 3종 + 벌크(`/user/{id}`) jti가 잔여** | P0 | ~2 |
| **FR-SV-02** | **reports.py 인증·인가**: 전 엔드포인트에 `get_current_account_user` 추가(무인증 차단, AUTH_MODE 무관). 이후 `require_perm`: GET=`report:view`, POST/PATCH=`report:edit`, DELETE=`report:delete` | P0 | ~2 |
| **FR-SV-03** | **3선결조건(서버 ②선)**: ① `.env AUTH_MODE=public→token`(account_users 이주 확인 후) ② **`get_current_account_user_optional` 신규**(AccountUser 기반·jti 블랙리스트 검사·optional 허용) — 레거시 `get_current_user_optional` 대체. ③(클라 Bearer 부착)은 상위 PRD. **②①은 동시 배포**(분리 시 비계정 도메인 전원 401/무방어) | P0 | ~3 |
| **FR-SV-04** | **`require_perm(module, verb)` 팩토리**(auth.py): `require_role` 확장, ADMIN bypass, jti 검사 포함. cameras·sensors·controllers·actions·detections·malfunctions·servers·audit_logs **write 엔드포인트에 순차 삽입**(FR-SV-03 완료 후) | P0 | ~8 |
| **FR-SV-05** | **enums 모듈 추가**: 서버 `enums.py`에 `Map`·`Broadcast`·`SetupSystem`·`SetupFeature` 모듈 + (클라 EnumPermissionModule 동기). PermissionsSchema·시드 갱신. 모듈명 **`cameras` 통일**(클라 `cam` 오기 방지 계약). ★require_perm 삽입보다 선행(미정의 시 422/영구차단) | P0 | ~3 |
| **FR-SV-06** | **마지막 ADMIN 원자 가드**: `DELETE /users/{id}`·`PUT /users/{id}`(role 변경)에 `SELECT COUNT(*) … role='ADMIN' FOR UPDATE`(count==1→409). 역할 강등 시 대상 **전체 세션 jti 블랙리스트**(원격 강등 집행, FR-PG-12) | P1 | ~4 |
| **FR-SV-07** | **감사 append-only DB 강제**: `audit_logs.py` DELETE 라우터 405 stub + `GET /audit-logs/export`(require_perm audit:view, ADMIN·MAINTAINER)·`PATCH /audit-logs/retention`(require_admin) + APScheduler 자동 purge(+purge 감사기록) + **PostgreSQL RULE/RLS로 DB레벨 DELETE 거부** | P1 | ~6 |
| **FR-SV-08** | **비계정 도메인 jti 검사 통일**: cameras/sensors/actions 등이 쓰는 인증 의존성을 `get_current_account_user_optional`(jti 검사 포함, FR-SV-03②)로 통일 → 로그아웃/강등 후 구 JWT 비계정 write 우회(GOP-09) 차단 | P1 | ~3 |
| **FR-SV-09** | **누락 인가 보강**: `servers.py PATCH/{id}` role 검사 추가(require_perm `setup:system`) · `user_groups.py` GET 엔드포인트 `require_admin` 누락 점검·보강(VIEWER 권한그룹 조회 차단) | P1 | ~3 |
| **FR-SV-10** | **비번 변경 세션 무효화**: `PUT /users/me/password` 성공 시 본인 **타 기기 세션 jti 블랙리스트**(현재 무효화 안 함, F07-01) | P2 | ~2 |
| **FR-SV-11** | **민감정보 노출 차단**: `GET /cameras` 응답의 RTSP URL을 `cam:view` 없는 역할에 마스킹 + (선택) NATS subject ACL로 broadcast 발행 서버측 최종 방어선 | P2 | ~3 |

### 비기능 요구사항 (NFR)

| ID | 항목 | 요구사항 | 검증 방법 |
|----|------|---------|---------|
| NFR-SV-01 | 보안(인가 커버리지) | 모든 write 엔드포인트가 인증+역할/권한 검사 통과 필수(무인증·무권한 → 401/403) | 단위 테스트(pytest) + curl 비인증/저권한 퍼징 |
| NFR-SV-02 | 보안(토큰 무효화) | 로그아웃·강제로그아웃·강등·비번변경 후 해당 jti 전 도메인에서 401 | 라이브 E2E(도메인별 구토큰 요청 401 확인) |
| NFR-SV-03 | 성능 | require_perm은 jti 60s TTL 캐시로 매 요청 DB조회 회피, 권한 판정 Δ<5ms | 응답시간 측정(부하 전후) |
| NFR-SV-04 | 무결성(원자성) | 마지막 ADMIN 동시 삭제/강등에도 ADMIN≥1 | TOCTOU 동시성 테스트(SELECT FOR UPDATE) |
| NFR-SV-05 | 무결성(append-only) | 감사 레코드는 ADMIN 포함 누구도 물리삭제 불가(DB레벨) | DB 직접 DELETE 시도 거부 테스트 |
| NFR-SV-06 | 가용성 | AUTH_MODE 전환 시 이주 미완 계정 401 급증 방지(이주율 사전 확인) | 이주율 측정 + 단계 전환 |

---

## 3. 기술 설계

### 3.1 아키텍처 결정 — 서버가 권위 집행
- 클라 UI 게이팅은 보조·UX. **모든 write 엔드포인트의 서버 RBAC가 권위 집행 지점**(FR-PG-13). curl 우회는 서버에서만 차단 가능.
- **단, PTZ·방송·맵은 서버 미경유**(ONVIF 직결 / NATS 직접발행 / MariaDB 직접) → 서버 집행 대상 아님(상위 PRD의 클라 단독 집행). 본 PRD는 **GOP-REST 경유 도메인**(장비/이벤트/보고서/감사/계정/세션)만.

### 3.2 require_perm 팩토리 (FR-SV-04)
```python
def require_perm(module: str, verb: str):
    def _checker(current_user: AccountUser = Depends(get_current_account_user)) -> AccountUser:
        if current_user.role == "ADMIN":           # ADMIN bypass
            return current_user
        grp = _role_group(db, current_user.role)    # 역할명 등급그룹(OQ-PG-01 Option A)
        mods = (grp.permissions or {}).get("modules", {}) if grp else {}
        if not (mods.get(module, {}).get(verb)):
            raise HTTPException(403, f"requires {module}:{verb}")
        return current_user
    return _checker
```
- 권한 원천 = **역할명 등급그룹의 매트릭스**(OQ-PG-01 Option A, `12fc48d`로 로그인은 이미 역할기반). require_perm도 동일 원천 사용 → UI/서버 일관.

### 3.3 3선결조건 순서 (FR-SV-03) — ★배포 주의
1. `get_current_account_user_optional` 신규 구현(AccountUser·jti검사) → 비계정 라우터 의존성 교체(FR-SV-08).
2. 클라(상위 PRD): Device/Event/Camera ApiService에 BearerAuthHandler 주입(토큰 부착).
3. **위 1·2 배포 후** `.env AUTH_MODE=token` 전환. → **순서 어기면 앱 전원 401**.

### 3.4 감사 append-only (FR-SV-07)
- 라우터에 DELETE 미존재만으론 ORM/마이그레이션 우회 → **PostgreSQL RULE `ON DELETE DO INSTEAD NOTHING` 또는 RLS + 별도 app 계정**으로 DB레벨 거부. purge는 시간기반 자동 + 그 행위도 감사.

### 3.5 5-sync 규칙
모든 변경: 코드 + 명세서(`docs/API_Documentation.md`는 자동생성이므로 route docstring=swagger 원천) + 도커 이미지 재빌드 + 컨테이너 재기동 + 안전점 태그. ([[reference_api_test_server]])

---

## 4. 범위

### In Scope (api-test-server)
- 인증/인가: require_perm 팩토리 + write 엔드포인트 적용, get_current_account_user_optional, AUTH_MODE 전환
- 보안 패치: T4 require_admin, reports 인증, 마지막ADMIN 원자가드, 비번변경 세션무효화
- 무결성: 감사 append-only DB강제
- enums 모듈 추가, 누락 인가 보강

### Out of Scope
- **클라(.NET) 집행**: GMaps.Ui/Devices.Ui/Events.Ui 게이팅·PTZ·역할강등 재평가 → `GOP_Permission_Enforcement-prd.md`
- **PTZ/방송/맵 서버 집행**: 서버 미경유 → 구조적 불가(장기 ONVIF relay 신설은 별도)
- PM 결정 대기 항목(OQ-PG-02/04/06/07)의 정책 자체 결정

---

## 5. 의존성 및 전제 조건
- **FR-SV-05(모듈 정의) → FR-SV-04(require_perm 삽입) 선행**(미정의 시 422/영구차단).
- **FR-SV-03(get_current_account_user_optional + 클라 Bearer) → AUTH_MODE=token 전환 선행**.
- 클라 측 Bearer 부착(상위 PRD)과 **동시 배포** 조율 필요.
- 서버 변경은 5-sync + 도커 재배포. audit 테이블 append-only([[reference_api_test_server]]).

---

## 5-A. 검증 필요 항목 (Verification Prerequisites)

| ID | 검증 항목 | 검증 방법 | 확인 |
|----|---------|---------|------|
| V-SV-01 | account_users 이주율 (AUTH_MODE 전환 전 레거시 계정 401 위험) | DB 카운트 | 미확인 |
| V-SV-02 | audit_logs FK `ON DELETE`(actor_id/resource_id) — 비부인성 | 스키마 확인 | 미확인 |
| V-SV-03 | `servers.py PATCH`·`user_groups.py GET` 현재 인가 상태 | 코드 확인 | 미확인 |
| V-SV-04 | T1: `PUT /users/{id}` require_admin 적용 확인 + PATCH 경로 존재 여부 | 코드 확인 | ✅ PUT 적용(users.py:380), PATCH 추가확인 |
| V-SV-05 | OQ-PG-04 cam:imaging → 별도 토큰이면 서버 PermissionsSchema 변경 필요 | **PM 결정** | 미확인 |
| V-SV-06 | OQ-PG-06 GUEST 폐지 시 서버 EnumUserRole·시드 영향 | **PM 결정** | 미확인 |
| V-SV-07 | OQ-PG-07 비ADMIN 본인삭제 → `DELETE /users/me` 설계 | **PM 결정** | 미확인 |
| V-SV-08 | `get_current_user_optional` 사용 라우터 전수 목록(교체 대상) | grep | 미확인 |

---

## 5-B. 인과 결합 분석 (Causal Coupling)

| 수정 항목 | 영향 받는 플로우 | 대응 |
|---------|---------------|------|
| `AUTH_MODE=token` 단독 전환 | get_current_user_optional 도메인 전원 401 + 클라 Bearer 미부착 시 앱 전체 마비 | FR-SV-03 묶음 + 클라 Bearer 동시 배포 |
| require_perm을 모듈 미정의 상태로 삽입 | OPERATOR/MAINTAINER 422/영구차단 | FR-SV-05 선행 |
| 비계정 의존성 통일(get_current_user_optional 제거) | 레거시 User 토큰 사용처 깨짐 | 사용처 전수(V-SV-08) 후 교체 |
| 감사 DB레벨 DELETE 거부(RULE/RLS) | 정상 마이그레이션/테스트 정리 스크립트 영향 | 별도 app 계정 분리 or purge 전용 경로 |
| 마지막 ADMIN 가드(FOR UPDATE) | 대량 사용자 일괄삭제 트랜잭션 잠금 | 가드는 ADMIN 대상에만 적용 |

---

## 6. 리스크

| 리스크 | 가능성 | 영향 | 대응 |
|--------|--------|------|------|
| **AUTH_MODE 전환 순서 오류 → 앱 전원 401** | 높음 | 심각 | FR-SV-03 묶음+클라 Bearer 동시, 롤백 태그, 단계 전환 |
| **reports.py 무인증 (현재 LIVE)** | 높음 | 높음 | FR-SV-02 즉시 |
| **T4 세션 DoS require_admin 누락 (현재 LIVE)** | 높음 | 심각 | FR-SV-01(jti 선반영, require_admin 잔여) |
| **비계정 도메인 jti 미검사 → 구토큰 24h 우회** | 높음 | 높음 | FR-SV-08 |
| 모듈 미정의 시 require_perm이 OPERATOR/MAINTAINER 차단 | 높음 | 중간 | FR-SV-05 선행 |
| 마지막 ADMIN TOCTOU | 낮음 | 심각 | FR-SV-06 SELECT FOR UPDATE |
| 감사 DB레벨 미강제 → ORM/마이그레이션 우회 삭제 | 중간 | 높음 | FR-SV-07 RULE/RLS |

---

## 7. 완료 기준 (DoD)
- [ ] P0 FR(SV-01~05) 구현 — 보안 긴급 + require_perm 기반
- [ ] P1 FR(SV-06~09) 구현 — 원자가드·감사·jti통일·누락보강
- [ ] NFR-SV-01~05 검증(curl 우회 차단·도메인별 구토큰 401·TOCTOU·DB DELETE 거부 라이브)
- [ ] pytest `should_X_when_Y` + 회귀 통과
- [ ] V-SV-01~08(특히 PM 결정 05~07, 이주율 01) 확정
- [ ] **5-sync 완료**(코드·docstring/swagger·도커·컨테이너) + 안전점 태그
- [ ] 문서(CHANGELOG·session-context·INDEX) 갱신

---

## 부록. 현재까지 서버 선반영(본 PRD 일부)
- `980abbc` force_logout jti 블랙리스트(FR-SV-01 jti 부분, 라이브 401 검증) — **require_admin 3종 + 벌크 jti는 잔여**
- `12fc48d` 로그인 역할기반 권한 유도(OQ-PG-01 Option A) — require_perm의 권한 원천 동일
- `c71c8ce` `POST /user-groups/{id}/permissions`(권한 편집저장, ADMIN) — 집행 아닌 관리
- 서버 푸시 브랜치 `feature/gop-account-permission`(단 980abbc는 `feature/tracking-gis-ingest`에 있음 — 다음 푸시 시 정리)
