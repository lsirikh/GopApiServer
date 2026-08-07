# PRD — Legacy User 모델 삭제 + AccountUser 통일

- **작성일**: 2026-07-02
- **상태**: Approved
- **버전**: v1.0
- **언어/프레임워크**: Python 3.11 / FastAPI (SQLAlchemy + PostgreSQL 16)
- **요청 배경**: GIS 팀(외부 세션 wf_52155656 관련) 요청 — "`User`와 `AccountUser` 두 파트가 혼용되어 있어 레거시는 정리 삭제하는 게 좋겠다"
- **연관 잔존 작업**: v5.1 PRD_GOP_Server_RBAC_Enforcement FR-SV-08 (30 라우터 이주와 동일 범위)
- **관련 세션 조율**: `docs/memory/SESSION_COORDINATION.md` — auth.py는 WS-B 단독 소유. **본 작업은 WS-B 마감 후 실행 권고**

---

## 변경 이력

| 날짜 | 버전 | 변경 항목 | 변경 이유 | 영향 범위 |
|------|------|---------|---------|---------|
| 2026-07-02 | v1.0 | 초안 작성 | GIS 팀 요청 대응 | 35 라우터 + models/user.py + auth.py + DB users 테이블 |
| 2026-07-02 | 1.0 | 사용자 승인 | "GIS 팀 요청 대응 v5.3 진행 — Legacy User 제거 + AccountUser 통일" | 상태 Draft → Approved |

---

## 1. 개요

### 목적

`app/models/user.py`에 공존하는 **Legacy `User` 모델**과 **신규 `AccountUser` 모델**을 통일한다. Legacy `User`(6 컬럼, DB 1 row, FK 참조 0건)를 완전 제거하고, 모든 인증/인가 경로가 `AccountUser` 기반으로 통일되도록 코드 sweep + DB 마이그레이션을 수행한다.

### 배경 및 동기

**현재 상태**:

| 항목 | Legacy `User` | 신규 `AccountUser` |
|---|---|---|
| DB 테이블 | `users` (1 row, admin만) | `account_users` (8 rows, 실 계정) |
| 컬럼 | 6개 (`id/username/hashed_password/role/created_at/updated_at`) | 26개 (login_id + 프로필 + lock 메타 + audit) |
| FK 참조 (다른 테이블 → 이 테이블) | **0건** | 9건 (audit_logs / config_change_logs / user_sessions / token_blacklist / user_group_grants / user_login_logs / report_generations / report_templates / app_settings) |
| 코드 import | 2 파일 | 11 파일 |
| Auth helper | `get_current_user` / `get_current_user_optional` (jti 미검사, Legacy) | `get_current_account_user` / `get_current_account_user_optional` (jti 검사, v5.1 신설) |
| 라우터 사용 (Legacy) | **35 라우터**에서 `Depends(get_current_user_optional)` 사용 | 7 라우터 (계정 + v5.x 신규 도메인) |

**혼용 발생 문제**:

1. **인증 일관성 부재** — 계정 도메인 8 endpoint(v4.12 RBAC)는 `AccountUser` 기반 완전 검증(jti 블랙리스트 + is_active + is_locked), 나머지 35 라우터는 `User` 조회만 하고 실 검증 없음(현 `AUTH_MODE=public` 상태로 무동작)
2. **v5.1 FR-SV-08 잔존** — 이미 명시된 이주 대상. `get_current_user_optional` → `get_current_account_user_optional` 전수 교체
3. **GIS 팀 API 통합 시 혼란** — .NET 클라 팀이 두 모델의 존재를 인지, 어느 쪽을 참조해야 할지 불명확
4. **Dead code 유지비용** — Legacy `User`는 사실상 사용 안 되는데 클래스/함수/테이블만 유지되어 code review·mental load 발생

**해결 방향**:

- **Phase 1** — 35 라우터의 `get_current_user_optional` → `get_current_account_user_optional` 일괄 교체 (안전, 무동작 이주)
- **Phase 2** — `User` 클래스 + Legacy auth 함수 dead code 삭제
- **Phase 3** — `users` 테이블 DROP 마이그레이션

**리스크 극소** — 현재 `AUTH_MODE=public`이라 `get_current_user_optional`은 실 로직에서 무동작(None 반환). 신규 helper는 이미 v5.1에서 존재 확인.

---

## 2. 요구사항

### 기능 요구사항 (Functional Requirements)

| ID | 요구사항 | 우선순위 | 예상 태스크 수 |
|----|---------|---------|--------------|
| **FR-LU-01** | 35 라우터의 `Depends(get_current_user_optional)` → `Depends(get_current_account_user_optional)` 일괄 교체 | High | ~10개 (라우터 그룹별 5~7 파일씩 sweep + 검증) |
| **FR-LU-02** | 35 라우터 import 정정 — `from app.routers.auth import get_current_user_optional` → `get_current_account_user_optional` | High | ~2개 (sed sweep + 검증) |
| **FR-LU-03** | `current_user` 파라미터 타입 힌트 갱신 — 기존 `User \| None` → `AccountUser \| None` (타입만 표현, 런타임 영향 없음) | Mid | ~2개 |
| **FR-LU-04** | `app/models/user.py:221` `class User` 클래스 삭제 (dead code) | High | ~1개 |
| **FR-LU-05** | `app/routers/auth.py` Legacy 함수 삭제 — `get_current_user` + `get_current_user_optional` + (사용처 확인 후) `login_oauth2` | High | ~2개 (사용처 grep + 삭제) |
| **FR-LU-06** | `app/schemas/user.py` `UserResponse` (Legacy용) 삭제 검토 + 관련 import 정리 | Mid | ~2개 |
| **FR-LU-07** | `app/migrations/v56_drop_users_table.sql` 신설 — `DROP TABLE users;` (트랜잭션 + 검증) | High | ~2개 |
| **FR-LU-08** | `app/utils/init_db.py` / `init_sample_data.py`에서 `users` 테이블 생성/시드 코드 삭제 | High | ~2개 |
| **FR-LU-09** | 회귀 테스트 — 35 라우터 모두 정상 응답 확인 (AUTH_MODE=public에서 200 유지) + 계정 도메인 200 유지 + Swagger 정합 | High | ~3개 (테스트 스위트 + 실 API 검증) |
| **FR-LU-10** | .NET 클라 팀 통지 — GOP_Restful_Api_연동설계.md에 "Legacy User 모델 제거" 명시 + Swagger 변경사항 안내 | Mid | ~2개 |
| **FR-LU-11** | Container rebuild + Image + Swagger 5-sync + 안전점 태그 (`pre-legacy-user-removal` + `v5.3-final-stable`) | High | ~2개 |

**합계**: 예상 태스크 ~30개, 실 작업 시간 ~3~5h (안전한 sweep이라 병렬 가능)

### 비기능 요구사항 (Non-Functional Requirements)

| ID | 항목 | 요구사항 | 검증 방법 |
|----|------|---------|---------|
| NFR-LU-01 | 무회귀 | 기존 35 라우터의 응답 형식/코드 100% 유지 (AUTH_MODE=public에서 무영향) | 회귀 pytest 전수 + 실 API curl 스팟 검사 |
| NFR-LU-02 | DB 정합 | `DROP TABLE users` 성공 + 다른 테이블 FK 파괴 0 | `\dt` + `\d+ users` 확인 + FK 검증 SQL |
| NFR-LU-03 | Swagger 정합 | `UserResponse` schema 제거 반영 + 30 라우터 OpenAPI response_model 유지 | `curl /openapi.json` + 이전/이후 diff |
| NFR-LU-04 | 이주 안전 | `AUTH_MODE=public`에서 라우터 응답 코드 100% 동일 (before/after 매트릭스) | 25 endpoint × before/after 각 200/401/404 매트릭스 |
| NFR-LU-05 | Dead code 0 | 이주 후 `grep get_current_user\b app/` = 0건, `grep 'class User' app/models/` = 0건 | grep 검증 |
| NFR-LU-06 | 롤백 안전 | `pre-legacy-user-removal` 태그로 완전 회귀 가능 (코드 + DB migration reverse) | 안전점 태그 + reverse migration SQL 준비 |

---

## 3. 기술 설계

### 3.1 아키텍처 결정 및 이유

**결정**: **점진적 sweep + DB DROP** (in-place 이주, 별도 flag 없음).

**대안 비교**:

| 대안 | 장점 | 단점 | 선정 |
|---|---|---|:---:|
| A. Legacy 유지 + Deprecation warning만 | 리스크 0 | 혼용 상태 계속, GIS 팀 요청 미충족 | ✗ |
| **B. 3-Phase Sweep + DROP (본 PRD)** | 완전 정리, 이미 신규 helper 존재 | 35 라우터 편집 (안전한 sed 패턴) | ✅ |
| C. Legacy 유지 + AUTH_MODE=token 전환 시에만 검증 | 점진 이주 | 두 헬퍼 계속 유지 = 혼용 상태 지속 | ✗ |
| D. Legacy `User` = `AccountUser` alias 처리 | Import 변경 불필요 | 근본 정리 X, 컬럼 스키마 다름 | ✗ |

**선정 사유**:

1. FK 참조 0건 → DB 삭제 무위험
2. 신규 helper `get_current_account_user_optional`는 v5.1에서 이미 신설 (auth.py:206)
3. `AUTH_MODE=public`에서 두 helper 모두 None 반환 → 이주 시 응답 동일
4. GIS 팀 요청 대응 + v5.1 FR-SV-08 잔존 작업 소진 = 두 마리 토끼

### 3.2 주요 컴포넌트

**삭제 대상**:

```
app/models/user.py
  └─ class User (L221~)                    ← 삭제

app/routers/auth.py
  ├─ async def get_current_user            ← 삭제
  ├─ async def get_current_user_optional   ← 삭제
  └─ async def login_oauth2 (조건부)       ← 사용처 확인 후 삭제

app/schemas/user.py
  └─ UserResponse (Legacy, 조건부)         ← 사용처 확인 후 삭제

app/utils/init_db.py
  └─ users 테이블 생성 코드                ← 삭제

app/utils/init_sample_data.py
  └─ users 시드 코드 (admin 1건)           ← 삭제

DB
  └─ users 테이블                          ← DROP TABLE
```

**변경 대상** (35 라우터):

```
Import 교체:
  from app.routers.auth import get_current_user_optional
    ↓
  from app.routers.auth import get_current_account_user_optional

Depends 교체:
  Depends(get_current_user_optional)
    ↓
  Depends(get_current_account_user_optional)

타입 힌트 갱신 (선택):
  current_user: User | None = ...
    ↓
  current_user: AccountUser | None = ...
```

### 3.3 데이터 모델

**Before**:

```
users (Legacy)              account_users (신규)
├─ id                       ├─ id
├─ username                 ├─ login_id
├─ hashed_password          ├─ password_hash
├─ role                     ├─ name / email / department / position / employee_number
├─ created_at               ├─ photo_url / phone
└─ updated_at               ├─ role / group_id
                            ├─ is_active / is_locked / lock_reason / locked_at / locked_by
                            ├─ password_changed_at / password_expires_at
                            ├─ failed_login_count / last_login_at / last_login_ip
                            └─ created_at / updated_at / created_by / updated_by
```

**After**:

```
account_users만 유지 (26 컬럼 그대로)
```

**마이그레이션 SQL** (`app/migrations/v56_drop_users_table.sql`):

```sql
BEGIN;

-- 검증 1: 다른 테이블 FK 참조 0 확인
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE contype='f'
      AND pg_get_constraintdef(oid) LIKE '%REFERENCES users(%'
  ) THEN
    RAISE EXCEPTION 'users 테이블 FK 참조가 남아있음 — DROP 불가';
  END IF;
END $$;

-- 검증 2: users 테이블에 admin 이외 row 없음 확인 (안전 가드)
DO $$
DECLARE
  cnt INTEGER;
BEGIN
  SELECT count(*) INTO cnt FROM users WHERE username != 'admin';
  IF cnt > 0 THEN
    RAISE EXCEPTION 'users 테이블에 admin 외 %건 row 존재 — 확인 필요', cnt;
  END IF;
END $$;

-- DROP
DROP TABLE IF EXISTS users CASCADE;

-- 검증 3: DROP 완료 확인
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_tables WHERE tablename='users' AND schemaname='public') THEN
    RAISE EXCEPTION 'users 테이블 DROP 실패';
  END IF;
END $$;

COMMIT;
```

**Reverse migration** (`app/migrations/v56_drop_users_table_reverse.sql`, 롤백용):

```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(50) UNIQUE NOT NULL,
  hashed_password VARCHAR(255) NOT NULL,
  role VARCHAR(20) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX ix_users_id ON users(id);
```

### 3.4 API/인터페이스 설계

**변경 없음** — 35 라우터의 URL/method/response schema/응답 코드 모두 유지. Internal helper만 교체.

**단**: `POST /api/auth/login-oauth2` (Legacy용) endpoint 존재 여부 확인 후 삭제 검토 — 있으면 GOP 명세서에서도 제거 + .NET 팀 통지.

---

## 4. 범위

### In Scope

- `User` 클래스 삭제 (`app/models/user.py`)
- Legacy auth 함수 삭제 (`get_current_user`, `get_current_user_optional`, 조건부 `login_oauth2`)
- 35 라우터 sweep — `get_current_user_optional` → `get_current_account_user_optional`
- `users` 테이블 DROP + 마이그레이션 (v56)
- 시드 코드 정리 (init_db.py + init_sample_data.py)
- 회귀 테스트 + 5-sync (코드/명세/CHANGELOG/Image/Container/Swagger)
- .NET 팀 통지 (명세서 + 회신 문서)

### Out of Scope

- **AUTH_MODE=token 전환** — 별도 차수 (v5.4+, 클라 Bearer 동시 배포 필수)
- **require_perm 활성화** — v5.1/v5.2에서 휴면 상태로 이미 존재 (본 PRD와 무관)
- **UserGroup / UserSession / UserLoginLog 리팩토링** — `account_users` FK 유지, 변경 없음
- **GOP_스키마_전체.md 대규모 갱신** — 필요 시 별도 마이그레이션 PRD
- **admin 계정 이주** — `users`의 admin 1건은 `account_users`에 이미 존재 (별도 계정), Legacy admin은 사용 안 됨 확인 후 단순 DROP

---

## 5. 의존성 및 전제 조건

- **v5.1에서 `get_current_account_user_optional` 신설 확정** (`auth.py:206`) — 이주 대상 helper 존재
- **`AUTH_MODE=public` 상태 유지** — 이주 시 응답 무영향 조건
- **`docs/memory/SESSION_COORDINATION.md`의 WS-B 단독 소유 auth.py** — 본 작업은 auth.py 대규모 변경 → **WS-B 마감 후 실행 필수**
- **`account_users.admin`은 이미 존재** (admin, admin123 bcrypt) — Legacy `users.admin` 삭제 시 login 영향 없음
- **35 라우터의 `current_user` 파라미터가 실 로직에서 사용되지 않음** 사전 확인 (grep으로 `current_user.` 참조 있는 파일 검증)

---

## 5-A. 검증 필요 항목 (Verification Prerequisites)

| ID | 검증 항목 | 검증 방법 | 확인 여부 |
|----|---------|---------|---------|
| V-LU-01 | 35 라우터 각 `current_user.` 참조 존재 여부 (있으면 attr 호환 확인 — `User.id` / `User.username` vs `AccountUser.id` / `AccountUser.login_id`) | grep + Read | 미확인 |
| V-LU-02 | `login_oauth2` endpoint 실 사용처 (.NET 클라 코드 검색 or Swagger 호출 이력) | 클라팀 확인 요청 | 미확인 |
| V-LU-03 | `UserResponse` schema 참조 라우터 목록 (사용되면 유지, 안 쓰면 삭제) | grep app/routers/ + schemas/ | 미확인 |
| V-LU-04 | `users.admin` row 실 사용처 (login endpoint가 어느 테이블 조회하는지) | auth.py:226 코드 확인 (login은 `account_users` 조회 확정) | ✅ 확정 (auth.py:226 `AccountUser` 사용) |
| V-LU-05 | `AUTH_MODE=public` 확정 (docker-compose.yml + .env) | `docker exec printenv AUTH_MODE` | ✅ 확정 (public) |
| V-LU-06 | WS-B 세션 소유권 해제 시점 (`docs/memory/SESSION_COORDINATION.md`) | SESSION_COORDINATION.md 확인 후 차장님 조율 결재 | 미확인 |
| V-LU-07 | 회귀 테스트 스위트가 Legacy User attribute 참조 여부 (`test_*.py` grep) | grep tests/ | 미확인 |

---

## 5-B. 인과 결합 분석 (Causal Coupling Analysis)

| 수정 항목 | 영향 받는 다른 플로우 | 대응 방안 |
|---|---|---|
| `User` 클래스 삭제 | `app/schemas/user.py` `UserResponse` — Legacy 응답 스키마 | V-LU-03 확인 후 사용처 있으면 유지, 없으면 삭제 |
| `get_current_user_optional` 삭제 | 35 라우터 import — 미교체 파일 있으면 즉시 ImportError | FR-LU-01/02 완료 후 삭제 (Phase 2에서 실행) |
| `users` 테이블 DROP | `admin` 로그인 — `auth.py:226`은 `AccountUser` 조회라 무영향 확정 | V-LU-04 확인 (이미 확정) |
| `login_oauth2` 삭제 (조건부) | .NET 클라 통합 — 사용처 있으면 breaking change | V-LU-02 확인 후 결재 |
| 35 라우터 helper 교체 | AUTH_MODE=token 전환 시 각 라우터에 Bearer 강제 | AUTH_MODE 전환은 별도 차수 (Out of Scope) |
| `UserResponse` 삭제 (조건부) | Swagger 응답 schema — 없어져도 실 API 응답 형식 동일 | V-LU-03 확인 |

**핵심 인과 사슬**:

```
Phase 1 (라우터 sweep) → Phase 2 (User/helper 삭제) → Phase 3 (DB DROP)
        ↑                          ↑                       ↑
   무동작 이주                dead code 정리          FK 참조 0 확인
```

각 Phase는 이전 Phase 완료가 선결 조건 (역순 진행 불가).

---

## 6. 리스크

| 리스크 | 가능성 | 영향 | 대응 방안 |
|--------|:---:|:---:|---|
| **WS-B 세션이 auth.py 편집 중일 때 충돌** | 중간 | 심각 | **본 PRD는 WS-B 마감 후 실행** (SESSION_COORDINATION.md 준수). 안전점 태그 + 차장님 조율 결재 필수 |
| `current_user.` 실 참조 발견 (예: `current_user.username` vs `.login_id`) | 낮음 | 중간 | V-LU-01 사전 검증. 참조 발견 시 attr 매핑 (Legacy `username` → 신규 `login_id`, `hashed_password` → `password_hash`) |
| `login_oauth2` .NET 클라 실 사용 | 낮음 | 높음 | V-LU-02 확인 전 삭제 금지. 사용처 있으면 유지 + `AccountUser` 기반 재작성 |
| DB DROP 후 롤백 필요 상황 | 매우 낮음 | 심각 | reverse migration SQL 사전 준비. 안전점 태그 `pre-legacy-user-removal`로 즉시 회귀 가능 |
| `UserResponse` 사용처 있는데 삭제 | 낮음 | 중간 | V-LU-03 확인 후 결정. 있으면 유지 (Legacy 유물 최소화) |
| 회귀 테스트 실패 (Legacy User attr 의존) | 낮음 | 중간 | V-LU-07 확인. Legacy 참조 테스트는 별도 skip 또는 `AccountUser` 기반으로 재작성 |
| 시드 재실행 시 users 테이블 재생성 | 중간 | 낮음 | FR-LU-08에서 init_db.py + init_sample_data.py 정리 필수 |

---

## 7. 완료 기준 (Definition of Done)

- [ ] 모든 FR 구현 완료 (FR-LU-01 ~ FR-LU-11)
- [ ] NFR 검증 통과 (NFR-LU-01 무회귀 / NFR-LU-02 DB 정합 / NFR-LU-03 Swagger / NFR-LU-04 응답 코드 매트릭스 / NFR-LU-05 dead code 0 / NFR-LU-06 롤백 안전)
- [ ] 단위 테스트 작성 및 통과 (`should_X_when_Y` 명명 준수) — 35 라우터 회귀 + auth helper 이주 검증
- [ ] 선결 검증 항목 확인 완료 (V-LU-01 ~ V-LU-07 중 미확인 5건)
- [ ] `grep get_current_user\b app/` = 0건 확정
- [ ] `grep 'class User' app/models/` = 0건 확정
- [ ] `docker exec psql \dt users` = "Did not find any relation" 확정
- [ ] Image rebuild + Container Up healthy + Swagger 정합 검증
- [ ] 안전점 태그 `pre-legacy-user-removal` + `v5.3-final-stable` 신설 + Gitea push
- [ ] 명세서 (`GOP_Restful_Api_연동설계.md`) v5.3 차수 행 추가 — Legacy User 제거 + 이주 완료 명시
- [ ] CHANGELOG [v5.3] 섹션 신설 (Removed/Changed/Migration/Verified/Deferred)
- [ ] `.NET` 클라 팀 통지 문서 (`docs/GOP_Server_API_v5.3_Legacy_User_Removal_NOTIFY.md`)
- [ ] GIS 팀 요청 대응 회신 (요청자 지정 채널)
- [ ] `docs/memory/session-context.md` v5.3 갱신 + 안전점 표 + 작업 흐름 타임라인

---

## 부록 A. 실행 순서 (Phase별 sequence)

```
Phase 0 — 사전 검증 (V-LU-01~07 확인)
  ├─ WS-B 세션 auth.py 소유권 해제 결재 (차장님)
  ├─ current_user. 실 참조 grep (35 라우터)
  ├─ UserResponse / login_oauth2 사용처 grep
  └─ 회귀 테스트 스위트 Legacy 참조 확인
       ↓
Phase 1 — 라우터 sweep (35 파일)
  ├─ import 교체 (35 파일 × 1 line)
  ├─ Depends() 교체 (35 파일 × N line)
  ├─ 타입 힌트 갱신 (선택)
  └─ 라이브 API 검증 (25 endpoint × before/after 200 확인)
       ↓
Phase 2 — Dead code 삭제
  ├─ app/models/user.py User 클래스 삭제
  ├─ app/routers/auth.py Legacy 함수 삭제
  ├─ app/schemas/user.py UserResponse 삭제 (조건부)
  └─ init_db.py / init_sample_data.py 시드 정리
       ↓
Phase 3 — DB 마이그레이션
  ├─ v56_drop_users_table.sql 신설 + 실행
  ├─ FK 검증 (0건 확인)
  └─ 시드 재실행 검증 (users 테이블 재생성 안 함 확정)
       ↓
Phase 4 — 5-sync + 배포
  ├─ Image rebuild + Container restart
  ├─ Swagger 검증
  ├─ 명세 v5.3 + CHANGELOG + PRD Completed
  └─ 안전점 + Gitea push + final-stable 태그
       ↓
Phase 5 — 통지
  ├─ .NET 팀 회신 문서
  ├─ GIS 팀 요청 대응 회신
  └─ SESSION_COORDINATION.md 갱신
```

---

## 부록 B. 위험 매트릭스 요약

| Phase | 위험 | 해소 |
|---|---|---|
| Phase 0 | WS-B 충돌 | 차장님 결재 필수 |
| Phase 1 | current_user 실참조 attr 불일치 | V-LU-01 사전 확인 |
| Phase 2 | login_oauth2 breaking change | V-LU-02 사전 확인 |
| Phase 3 | DB DROP 후 롤백 | reverse migration + 안전점 태그 |
| Phase 4 | Container 회귀 | 실측 검증 매트릭스 |
| Phase 5 | 클라 팀 준비 부족 | 배포 전 통지 |

---

**문서 버전**: v1.0 / **최종 수정**: 2026-07-02 / **상태**: **Draft** (사용자 승인 대기)
