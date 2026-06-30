# GOP 서버(API) 세션 설정 런타임 관리 PRD

- **작성일**: 2026-06-30
- **상태**: Draft
- **버전**: v1.0
- **위치/이관**: 본 PRD는 **api-test-server 레포 `docs/`에 작성**(서버 세션이 구현·관리). 원작성=2026-06-30 .NET GOP 작업 세션. 승인/plan/dev는 서버 세션이 진행.
- **대상 레포**: `api-test-server` (Python / FastAPI, SQLite/PostgreSQL)
- **상위/짝 PRD**(Ironwall.Dotnet.Libraries 레포 docs/prds/): `GOP_Session_Settings_Admin-prd.md` (클라이언트 측 — "세션 설정" 탭 편집 UI + IAccountApiService 배선)
- **근거**: 2026-06-30 세션설정 분석 — `app/config.py`(JWT_EXPIRATION_HOURS=24, JWT_REFRESH_EXPIRATION_DAYS=7, AUTH_MODE) + `auth.py`(잠금 임계 하드코딩 5, 토큰 만료 startup 상수 계산) 확인.

> 📍 본 PRD는 짝 PRD(`GOP_Session_Settings_Admin`)에서 **서버(API) 측만 분리**한 것. 클라 편집 UI는 짝 PRD가 담당. 서버는 별도 레포·5-sync·배포라 독립 추적.
> ⚠️ 서버 변경은 **5-sync 필수 + 도커 재빌드** (test 서버 동기화 규칙).

---

## 변경 이력

| 날짜 | 버전 | 변경 항목 | 변경 이유 | 영향 범위 |
|------|------|---------|---------|---------|
| 2026-06-30 | v1.0 | 초안 작성 | 세션/인증 정책(만료·refresh·잠금)이 `.env`/startup 상수라 런타임 조회·변경 불가 — 관리자 운영 중 조정 요구 | config·auth·신규 settings 라우터/모델/서비스·DB |

---

## 1. 개요

### 목적
세션/인증 정책의 **안전 부분집합**을 **런타임으로 조회·변경**하는 서버 API를 제공한다(서버 재시작 없이 적용). 관리자가 클라 콘솔 "세션 설정" 탭에서 호출.

### 배경 및 동기
- 현재 `JWT_EXPIRATION_HOURS`(24h)·`JWT_REFRESH_EXPIRATION_DAYS`(7d)·`AUTH_MODE`는 Pydantic `Settings`로 **startup-load**, 잠금 임계는 `auth.py:355` **하드코딩(`>= 5`)**.
- 조회/변경 API가 없어 운영 중 정책 조정 = 코드/`.env` 수정 + 재시작 필요.
- → DB 기반 런타임 설정 저장소 + require_admin API + `auth.py`가 그 값을 읽도록 리팩토링.

---

## 2. 요구사항

### 기능 요구사항 (Functional Requirements)

| ID | 요구사항 | 우선순위 | 예상 태스크 수 |
|----|---------|---------|--------------|
| **FR-SVS-01** | `app_settings` 저장소 신설(key-value 테이블): `setting_key`, `setting_value`, `value_type`, `updated_at`, `updated_by`. 마이그레이션 포함. | High | ~2 |
| **FR-SVS-02** | `settings_service` — 메모리 캐시 + 최초조회/startup 시 비어있으면 **`.env` 기본값으로 시드**, PUT 시 캐시 무효화. 단일 인스턴스 가정. | High | ~3 |
| **FR-SVS-03** | `GET /settings/session` (require_admin) → 편집가능값 + 읽기전용값(auth_mode·algorithm) 반환. **시크릿 값은 절대 미반환**. | High | ~2 |
| **FR-SVS-04** | `PUT /settings/session` (require_admin) → 편집 부분집합만 수용, **경계 검증(422)**, 영속, `ConfigChangeLog` 감사(이전→이후·actor), 캐시 무효화. | High | ~3 |
| **FR-SVS-05** | `auth.py` 리팩토링 — 토큰 만료(`create_access_token`/`create_refresh_token`)·로그인 잠금 임계를 **startup 상수/하드코딩 대신 `settings_service`**에서 읽기. | High | ~3 |
| **FR-SVS-06** | 시드/우선순위 정책: app_settings가 권위(시드 후), `.env`는 최초 1회 기본값. AUTH_MODE/secret은 settings_service 경유 **읽기전용 노출만**(편집 불가). | Mid | ~2 |

### 편집 대상 vs 제외 (보안 스코프)

| 키 | 런타임 편집 | 경계/검증 |
|----|:---:|------|
| `session_timeout_hours` (=JWT_EXPIRATION_HOURS) | ✅ | 1 ≤ n ≤ 168 |
| `refresh_expiration_days` (=JWT_REFRESH_EXPIRATION_DAYS) | ✅ | 1 ≤ n ≤ 90 |
| `lockout_threshold` (auth.py 하드코딩 5 대체) | ✅ | n=0(비활성) 또는 3 ≤ n ≤ 20 |
| `session_enabled` (만료 enforce on/off) | ✅(선택) | bool |
| `auth_mode` | ❌ 읽기전용 | 배포/.env 전용(UI 변경 시 전원 인증해제/잠금 위험) |
| `jwt_secret` / `jwt_algorithm` | ❌ 미노출/읽기전용 | 시크릿 — 값 반환 금지 |

### 비기능 요구사항 (Non-Functional Requirements)

| ID | 항목 | 요구사항 | 검증 방법 |
|----|------|---------|---------|
| NFR-SVS-01 | 보안-권한 | GET/PUT require_admin, 비관리자 403 | pytest + 수동 |
| NFR-SVS-02 | 보안-감사 | 변경 ConfigChangeLog append-only(누가/언제/이전→이후) | 감사 조회 |
| NFR-SVS-03 | 보안-시크릿 | jwt_secret 값 응답/로그 절대 노출 금지 | 응답·로그 검사 |
| NFR-SVS-04 | 입력검증 | 경계 밖/타입 오류 422 | 경계값·퍼징 |
| NFR-SVS-05 | 런타임 적용 | 변경이 재시작 없이 **다음 토큰 발급/잠금 판정부터** 반영 | 변경 후 신규 로그인 토큰 exp·잠금 측정 |

---

## 3. 기술 설계

### 데이터 모델 (`app_settings`)
```
app_settings (
  setting_key   TEXT PRIMARY KEY,   -- 'session_timeout_hours' 등
  setting_value TEXT NOT NULL,      -- 직렬화 문자열
  value_type    TEXT NOT NULL,      -- 'int' | 'bool' | 'str'
  updated_at    TIMESTAMP,
  updated_by    INTEGER             -- user.id (actor)
)
```
- startup 시 키 부재 → `.env`/config 기본값으로 INSERT(시드).

### API 계약
```
GET /settings/session            (require_admin)
 → 200 {
     session_timeout_hours:int, refresh_expiration_days:int,
     lockout_threshold:int, session_enabled:bool,
     auth_mode:str(readonly), jwt_algorithm:str(readonly)   # secret 미포함
   }
PUT /settings/session            (require_admin)
   body {session_timeout_hours?, refresh_expiration_days?, lockout_threshold?, session_enabled?}
 → 200 (갱신 후 전체) | 422(경계/타입) | 403(비관리자)
   부수효과: app_settings UPSERT + settings_service 캐시 무효화 + ConfigChangeLog
```

### auth.py 리팩토링 지점
- `create_access_token`: `timedelta(hours = settings_service.get('session_timeout_hours'))`
- `create_refresh_token`: `timedelta(days = settings_service.get('refresh_expiration_days'))`
- 로그인 잠금: `if user.failed_login_count >= settings_service.get('lockout_threshold')` (현 하드코딩 `>= 5` 대체; threshold=0이면 잠금 비활성)

---

## 4. 범위

### In Scope
- 편집 부분집합 런타임 조회/변경 API + DB 저장소 + 캐시 + auth.py 연동 + 감사.

### Out of Scope
- AUTH_MODE/JWT_SECRET 런타임 편집(배포전용).
- 기존 발급 토큰 즉시 무효화/일괄 revoke(→ 강제로그아웃 전파 PRD).
- 다중 서버 인스턴스 설정 동기화(단일 인스턴스 가정).
- 비밀번호 정책·MFA 등 그 외 인증 정책(차기).

---

## 5. 의존성 및 전제 조건
- require_admin 의존성(완료) + ConfigChangeLog/감사(존재) + DB 마이그레이션 도구.
- 클라(짝 PRD FR-SS-C*)는 본 API 계약 확정·배포 후 진행.

## 5-A. 검증 필요 항목

| ID | 검증 항목 | 검증 방법 | 확인 |
|----|---------|---------|----|
| V-01 | auth.py 토큰 만료가 startup 상수로 계산되는 정확한 지점 범위 | create_access/refresh_token·login 검토 | 확인(상수 사용) |
| V-02 | 잠금 임계 하드코딩 위치 | auth.py:355 `>= 5` | 확인 |
| V-03 | `.env`↔DB 우선순위(시드 후 DB 권위) 구현안 | settings_service 설계 | 미확인 |
| V-04 | 단일 인스턴스 가정 유효성(멀티 배포 여부) | 배포 토폴로지 확인 | 미확인 |

---

## 6. 리스크

| 리스크 | 가능성 | 영향 | 대응 |
|--------|--------|------|------|
| AUTH_MODE/secret 편집 노출 → 전원 잠금/토큰 전체 무효 | 높음 | 치명 | PUT 스키마 제외 + GET에서 secret 미반환(NFR-SVS-03) |
| 만료 축소가 기존 토큰 미반영(향후만) | 중간 | 혼동 | 응답/문서에 "신규 발급부터" 명시. 즉시무효=강제로그아웃 PRD |
| 캐시-DB 불일치(멀티 인스턴스) | 낮음 | 중 | 단일 인스턴스 가정 명시, 멀티는 Out of Scope |
| 경계 밖 값으로 운영 불능(만료 0 등) | 중간 | 중 | 경계 검증 + 안전 기본값 fallback |
| 5-sync/도커 미반영으로 환경 불일치 | 중간 | 중 | 5-sync 체크리스트 준수 |

---

## 7. 완료 기준 (Definition of Done)
- [ ] FR-SVS-01~06 구현 + pytest(권한·검증·런타임적용)
- [ ] NFR-SVS-01~05 검증(require_admin·감사·시크릿 비노출·검증·재시작 없는 적용)
- [ ] V-01~V-04 확인
- [ ] E2E: ADMIN이 session_timeout 변경 → 신규 로그인 토큰 exp가 새 값 반영 / 비관리자 403
- [ ] 5-sync + 도커 재빌드 반영
- [ ] 클라 짝 PRD에 API 계약 확정 통지
