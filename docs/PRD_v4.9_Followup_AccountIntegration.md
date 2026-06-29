
# PRD v4.9 Follow-up — Account / Auth / Permission 정합

> 차수: v4.9 (Follow-up)
> 작성일: 2026-06-24
> 작성자: lsirikh (이기호 차장)
> 마스터: c:\workspace_python\api-test-server\docs\PRD_v4.9_Followup_AccountIntegration.md
> 참조: PRD_Account_Design.md / PRD_Account_Implementation.md / PRD_Audit_Log.md / PRD_Auth_Migration.md / GOP_Restful_Api_연동설계.md v4.3

---

## §0 두괄식 요약

### 0.1 본 차수 1줄 요약
**v4.8 phase12-7 마감 직후 발견된 Auth/Account/Permission 도메인 12개 GAP을 단일 차수로 묶어 P0(보안 근간) 7건 + P1(정합 회복) 5건을 한 번에 정리하고, P2(cross-item) 3건은 v4.10으로 분리한다.**

### 0.2 P0/P1 분류표

| 우선순위 | 항목 ID | 범주 | GAP 한줄 | 시뮬 결과(R2) |
|---------|---------|-----|---------|-------|
| P0 | A-1.2 | XSS | photo_url validator 부재로 javascript:/data: 통과 | FAIL → PASS |
| P0 | A-1.4 | 업로드 가드 | 매직바이트/MIME/크기/race 가드 7종 부재 | FAIL → PASS |
| P0 | A-2.2 | 권한 모델 | 미정의 모듈(super_admin/system) 201 통과 | FAIL → PASS |
| P0 | A-2.3 | 권한 모델 | 미정의 verb(destroy/admin/control) 201 통과 | FAIL → PASS |
| P0 | A-2.5 | 권한 모델 | "yes"/1/"true" truthy 값 통과 (StrictBool 부재) | FAIL → PASS |
| P0 | A-4   | Auth   | jti 블랙리스트 + refresh `type=='refresh'` 가드 부재 | FAIL → PASS |
| P0 | B-1   | Auth   | 글로벌 HTTPException 핸들러가 WWW-Authenticate 헤더 누락 | FAIL → PASS |
| P1 | A-1.1 | 정합   | PUT /me photo_url 분기 silent drop | FAIL → PASS |
| P1 | A-1.3 | 정합   | POST /me/photo 엔드포인트 부재 (404) | FAIL → PASS |
| P1 | A-2.1 | 정합   | PermissionsSchema 정의만 있고 라우터 미사용 | PASS(현상)/FAIL(의도) → PASS |
| P1 | A-2.4 | 정합   | 시드 'rw' 문자열 vs PRD dict 포맷 충돌 | FAIL → PASS |
| P1 | A-3   | Auth   | refresh_token TTL 7일 하드코딩 (settings 분리 필요) | FAIL → PASS |
| P2 | (cross-item-1) | 후속 | thumbnails.py 동일 업로드 결함 | v4.10 |
| P2 | (cross-item-2) | 결재 | /static/profiles 익명 접근 정책 | v4.10 |
| P2 | (cross-item-3) | 후속 | AuditChange.rejected 메타 표준화 | v4.10 |

### 0.3 분량/일정
- v4.9 본 차수 (P0+P1): 19~24시간 (3일 작업)
- v4.10 분리 (P2): 8시간 (별도 차수)
- 마감 목표: 2026-06-27 (금) 18:00

---

## §1 차수 배경 + 결재 사항

### 1.1 배경
v4.8 phase12-7(불변성 6 sub-phase 통합) 마감 직후, 라이브 서버 검증 과정에서 다음 결함이 동시 발견됨:

1. **Auth 도메인**: jti 클레임이 토큰에 박혀있지만 블랙리스트 저장소가 전무 → logout 후 토큰 재사용 가능. refresh 엔드포인트가 access_token으로도 통과되는 type 가드 결함.
2. **Account 도메인**: PUT /me의 photo_url 분기가 누락(silent drop), POST /me/photo 엔드포인트 자체 부재.
3. **Permission 도메인**: PermissionsSchema 정의만 있고 라우터에서 미사용 → 미정의 모듈/verb가 201로 통과되어 권한 상승 직접 노출.
4. **응답 헤더**: 글로벌 HTTPException 핸들러가 `exc.headers`를 무시 → 라우터에서 설정한 WWW-Authenticate 헤더가 401 응답에서 사라짐.

### 1.2 결재 필요 사항 (1주차 결재 5건과 별도 추가)

| 결재 ID | 항목 | 선택지 | 영향 |
|--------|------|-------|------|
| v4.9-D1 | jti 블랙리스트 저장소 | (a) DB 테이블 / (b) Redis / (c) NATS KV | NATS 인프라 결재와 연계 |
| v4.9-D2 | /static/profiles 익명 접근 | (a) 익명 허용 + noindex / (b) 토큰 필수 | UI 캐시/CDN 정책 |
| v4.9-D3 | 운영팀 cameras.control 권한 유지 | (a) v52에서 true 유지 / (b) 박탈 후 명시적 부여 | 운영팀 실제 사용 패턴 |
| v4.9-D4 | refresh_token TTL 정책 | (a) 7일 고정 / (b) 환경별 가변 | 보안 정책 |
| v4.9-D5 | 정적 자원 storage path | (a) data/profile_photos / (b) /var/lib/gop/photos | 컨테이너 마운트 |

### 1.3 검증 우선 원칙 (메모리 feedback_validation_first 준수)
본 PRD의 모든 GAP 단정은 라이브 서버(localhost:8000, admin/admin123) + 코드 + UI 교차검증을 거쳤음. R1+R2 시뮬레이션 50건 + 라이브 422 차단 패턴 확인.

---

## §2 12 항목 PRD 본문

### 2.1 [A-1.1] PUT /me photo_url 분기 회복 (P1)

**배경**: PUT /api/users/me가 body의 photo_url을 200으로 응답하지만 DB 갱신 0건. app/routers/users.py:113-122 분기에 photo_url 항목 누락.

**요구**: photo_url 분기 추가 + before/after_state 딕셔너리 보강 + AuditLog USER_UPDATED changes에 photo_url 정합.

**설계**:
- 구조 변경(Tidy First): `if user_data.photo_url is not None: current_user.photo_url = user_data.photo_url` 1줄 추가
- before/after_state에 photo_url 키 추가 (name 분기와 동일 형식)
- A-1.2 validator와 동일 PR/커밋 묶음 (분리 시 회귀 윈도우 발생)

**API 변경**: 없음 (시그니처 무변경)
**스키마 변경**: 없음
**DB 변경**: 없음 (AccountUser.photo_url 컬럼 기존재)
**명세 변경**: GOP_Restful_Api_연동설계.md §사용자/PUT /users/me 요청 예시에 photo_url 케이스 추가
**실측(R2)**: PASS — 단독 GAP 없음, A-1.2와 묶음 필수
**잔존 위험**: A-1.2 미동시 적용 시 Stored XSS 윈도우

---

### 2.2 [A-1.2] photo_url Validator 화이트리스트 (P0)

**배경**: AccountUserSelfUpdate.photo_url에 max_length/pattern/validator 모두 부재. javascript:/data:/외부도메인/501자 URL 모두 200 통과(현재는 silent drop 덕에 우연히 미저장).

**요구**: max_length=500 + @field_validator로 화이트리스트 검증 (None/상대경로/HTTPS+허용호스트만 허용).

**설계**:
- `app/validators/photo_url.py` 신규 — 공유 validator 모듈
- 허용 규칙: ① None ② '' → None 정규화(model_validator before) ③ '/static/profiles/...' 상대 경로 ④ HTTPS + 호스트 in settings.PHOTO_URL_ALLOWED_HOSTS
- 위반 시 `ValueError('photo_url must be /static/profiles/... or HTTPS on allowed hosts')`
- AccountUserSelfUpdate / AccountUserUpdate 모두 적용
- settings.PHOTO_URL_ALLOWED_HOSTS = ['cdn.gop.mil'] 추가 + 빈 리스트 부팅 차단

**API 변경**: PUT /api/users/me 422 응답 케이스 + PUT /api/users/{user_id} 동일
**스키마 변경**: AccountUserSelfUpdate, AccountUserUpdate에 validator 적용
**DB 변경**: 없음
**명세 변경**: §사용자/photo_url 검증 규칙 표 추가, PRD_User_Photo_Url_Validation.md 신설
**실측(R2)**: PASS — 4종 공격 422 거부
**잔존 위험**: P2 — settings 빈 리스트 시 정상 운영 회귀

---

### 2.3 [A-1.3] POST /api/users/me/photo 엔드포인트 신설 (P1)

**배경**: 엔드포인트 부재(404), StaticFiles 마운트 0건. 업로드/서빙 인프라 전체 부재.

**요구**: multipart 업로드 + StaticFiles 마운트 + DB 영속 + AuditLog USER_PHOTO_UPLOADED + 구파일 GC.

**설계**:
- settings 추가: PROFILE_PHOTO_STORAGE_PATH='data/profile_photos', PROFILE_PHOTO_MAX_BYTES=2MiB, PROFILE_PHOTO_ALLOWED_MIME={png,jpeg,webp}, PROFILE_PHOTO_MAX_PIXELS=8000*8000
- app/main.py: StaticFiles 마운트 + startup hook에서 Path.mkdir(parents=True, exist_ok=True)
- POST /me/photo 핸들러: UploadFile + 매직바이트 검증 + 파일명 강제 생성(uuid4) + 원자적 os.replace + 구파일 unlink
- ProfilePhotoResponse 스키마 신설
- EnumAuditActionType.USER_PHOTO_UPLOADED 추가 + alembic 마이그레이션(ALTER TYPE ADD VALUE)
- GET /static/profiles/{filename} 응답에 X-Robots-Tag: noindex, Cache-Control: private

**API 변경**: POST /api/users/me/photo (신규) + GET /static/profiles/{filename} (마운트)
**스키마 변경**: ProfilePhotoResponse, EnumAuditActionType 확장
**DB 변경**: alembic v53 — ALTER TYPE enumauditactiontype ADD VALUE
**명세 변경**: §사용자 관리/POST /me/photo 절 신설, PRD_User_Profile_Photo_Upload.md 신설
**실측(R2)**: PASS
**잔존 위험**: P2 — 정적 자원 익명 접근 정책 결재(v4.9-D2)

---

### 2.4 [A-1.4] 업로드 가드 7종 통합 (P0)

**배경**: 매직바이트/MIME 화이트리스트/경로 traversal/크기 제한/토큰 가드/동시성 race/거부 audit 전건 부재.

**요구**: 가드 7종 동시 구현. 분리 구현 시 회귀 윈도우.

**설계**:
- (1) MIME 화이트리스트 → 415
- (2) 매직바이트 검증 첫 12바이트(PNG 89504E47, JPEG FFD8FF, WEBP RIFF....WEBP) → 415
- (3) 크기 제한 Content-Length 미들웨어 + 스트림 카운터 → 413
- (4) 파일명 강제 생성 uuid4 + commonpath traversal 가드
- (5) 토큰 sub 기반 /me 고정 경로
- (6) DB SELECT FOR UPDATE 직렬화 + 임시파일 GC
- (7) AuditLog USER_PHOTO_UPLOAD_REJECTED + RejectedMeta(mime/size/reason/magic_prefix_hex)
- Pillow Image.MAX_IMAGE_PIXELS 강제 (PNG bomb 방어)
- `app/services/upload_validator.py` 신규 공유 헬퍼 (thumbnails.py와 추후 공유)

**API 변경**: POST /me/photo 응답 코드 확장 (415/413/422/401/403)
**스키마 변경**: UploadValidationError, RejectedMeta, settings.PROFILE_PHOTO_MAX_PIXELS
**DB 변경**: A-1.3과 동일 마이그레이션에 포함 (REJECTED ADD VALUE)
**명세 변경**: §사용자 관리/가드 7종 표, PRD_User_Profile_Photo_Upload.md 보안 절
**실측(R2)**: PASS
**잔존 위험**: P1 — thumbnails.py 동일 결함 cross-item (v4.10), SELECT FOR UPDATE SQLite no-op → CI 매트릭스 PostgreSQL 분기

---

### 2.5 [A-2.1] PermissionsSchema 라우터 적용 (P1)

**배경**: PermissionsSchema가 정의만 있고 UserGroupCreate에서 미사용 (Dict[str, Any]로 자유 입력). PermissionsSchema.modules가 List[str]로 PRD §4.2.4 dict 구조와 충돌.

**요구**: UserGroupCreate.permissions 타입을 PermissionsSchema로 교체 + modules 필드를 ModulesPermission 컨테이너로 재정의.

**설계**:
- EnumPermissionModule (str Enum): events/cameras/devices/reports/settings/users
- 모듈별 6개 BaseModel(EventsPermission/CamerasPermission/...) — extra='forbid' + StrictBool verb 필드
- ModulesPermission 컨테이너 (각 모듈별 Optional 필드)
- PermissionsSchema.modules: Optional[ModulesPermission]
- UserGroupCreate.permissions: Optional[PermissionsSchema]
- UserGroupResponse.permissions도 동일 (단 legacy row try/except로 'legacy_permissions_format' 플래그)

**API 변경**: POST/PUT /api/user-groups 본문 검증 강화
**스키마 변경**: PermissionsSchema 재정의, 6개 모듈별 BaseModel 신규, EnumPermissionModule 신규
**DB 변경**: 없음 (A-2.4에서 v52 마이그레이션)
**명세 변경**: PRD_Account_Design.md §4.2.4 예시 + OpenAPI components.schemas 정렬
**실측(R2)**: PASS — dict 페이로드 201, OpenAPI에 6 enum 노출
**잔존 위험**: P3 — UserGroupResponse 정밀화 시 legacy row ValidationError → A-2.4 우선

---

### 2.6 [A-2.2] 미정의 모듈 키 422 거부 (P0)

**배경**: modules.super_admin/system 등 미정의 모듈 키가 201 통과 → 권한 상승 직접 노출.

**요구**: 422 + detail에 허용 enum 목록 동봉, DB INSERT 0건.

**설계**:
- ModulesPermission을 ConfigDict(extra='forbid')로 정의
- 422 응답 변환기에 허용 enum 목록 자동 동봉 (collect_module_verb_violations 공통 유틸)
- v52 마이그레이션: 기존 user_groups.permissions->'modules'에 비표준 키가 있는 row를 audit_log에 'LEGACY_INVALID_MODULE' action_type으로 기록 (자동 DELETE 안 함, 수동 admin 검토)

**API 변경**: 422 응답 케이스 확장
**스키마 변경**: ModulesPermission extra='forbid'
**DB 변경**: v52 백필 audit_log INSERT (자동 DELETE 금지)
**명세 변경**: PRD_Account_Design.md §4.2.1 표 아래 "표에 없는 모듈명은 422" 명문
**실측(R2)**: PASS
**잔존 위험**: P2 — 비표준 키 운영 검토 큐 처리

---

### 2.7 [A-2.3] 미정의 verb 422 거부 (P0)

**배경**: events.destroy / cameras.admin / devices.control 등 미정의 verb 통과.

**요구**: 모듈별 verb 표(PRD §4.2.1) 단일 진실원 강제 + 422 + detail에 (module, verb) 튜플 모두 열거.

**설계**:
- EventsPermission{view,edit,delete} / CamerasPermission{view,edit,control} / DevicesPermission{view,edit} / ReportsPermission{view,export} / SettingsPermission{view,edit} / UsersPermission{view,edit}
- 모두 extra='forbid' + StrictBool 필드만 보유
- ValidationError 변환기에 collect_module_verb_violations 공통 유틸 사용

**API 변경**: 422 응답 케이스 확장
**스키마 변경**: 6개 모듈별 BaseModel 정의
**DB 변경**: v52 백필
**명세 변경**: §4.2.1 verb 표 SoT 명시
**실측(R2)**: PASS
**잔존 위험**: 없음

---

### 2.8 [A-2.4] 시드 정규화 + v52 마이그레이션 (P1)

**배경**: init_sample_data가 {"events":"rw"} 문자열 포맷으로 PRD dict 구조와 무관.

**요구**: SAMPLE_GROUPS를 PRD §4.2.4 dict 포맷으로 교체 + 기존 DB row 마이그레이션.

**설계**:
- init_sample_data._create_user_groups SAMPLE_GROUPS 재작성
  - 운영팀: events{view,edit}, cameras{view,edit,control}, devices{view,edit}, reports{view,export}
  - 관제팀: 모든 verb=view만 true
  - 유지보수팀: devices{view,edit}, events.view, reports.view
- INSERT 직전 PermissionsSchema(**permissions).model_dump() 라운드트립 검증
- alembic v52: 'rw'/'r' 문자열 → dict 변환 (운영팀 cameras.control은 결재 v4.9-D3 결과 반영)

**API 변경**: 없음
**스키마 변경**: SAMPLE_GROUPS 상수 재작성
**DB 변경**: alembic v52 — 데이터 변환 마이그레이션
**명세 변경**: PRD_Account_Implementation.md §시드 절 갱신
**실측(R2)**: PASS — 단 운영팀 권한 의미 검증 사용자 승인 필요(P1)
**잔존 위험**: P1 — 마이그레이션 직후 권한 박탈 효과 발생 가능

---

### 2.9 [A-2.5] StrictBool 강제 (P0)

**배경**: "yes"/1/"true" 등 truthy 값이 bool로 자동 변환되어 통과.

**요구**: Pydantic StrictBool로 정확히 true/false만 허용.

**설계**:
- 모듈별 6개 BaseModel의 verb 필드 타입을 `StrictBool` (from pydantic import StrictBool)
- 422 detail: "Input should be a valid boolean"

**API 변경**: 422 케이스 확장
**스키마 변경**: 6개 BaseModel verb 필드 StrictBool
**DB 변경**: 없음
**명세 변경**: §4.2.1 표에 "값은 정확히 true/false만 허용 (truthy 거부)" 명문
**실측(R2)**: PASS
**잔존 위험**: 없음

---

### 2.10 [A-3] refresh_token TTL settings 분리 (P1)

**배경**: app/utils/auth.py:85에 `timedelta(days=7)` 하드코딩. 환경별 가변 불가.

**요구**: settings.JWT_REFRESH_EXPIRATION_DAYS (default 7) 도입.

**설계**:
- app/config/settings.py: JWT_REFRESH_EXPIRATION_DAYS: int = 7
- app/utils/auth.py: `timedelta(days=settings.JWT_REFRESH_EXPIRATION_DAYS)`
- datetime.utcnow() → datetime.now(timezone.utc) 동시 전환 (Python 3.12 deprecation)

**API 변경**: 없음
**스키마 변경**: settings 필드 추가
**DB 변경**: 없음
**명세 변경**: PRD_Auth_Migration.md TTL 표 갱신
**실측(R2)**: PASS
**잔존 위험**: 결재 v4.9-D4 결과

---

### 2.11 [A-4] jti 블랙리스트 + refresh type 가드 (P0)

**배경**: jti 클레임이 토큰에 박혀있지만 블랙리스트 저장소 부재. refresh 엔드포인트가 access_token으로도 통과되는 type 가드 결함.

**요구**: (1) decode_token이 type 반환 + refresh 엔드포인트에서 `payload.get('type') == 'refresh'` 가드. (2) logout 시 jti를 블랙리스트에 등록 + 인증 의존성에서 블랙리스트 조회.

**설계**:
- decode_token 반환 타입 변경: `dict[str, Any]` (sub, type, jti, exp 모두 노출) — 또는 dataclass TokenClaims
- POST /api/auth/refresh: `if payload.get('type') != 'refresh': raise 401`
- 블랙리스트 저장소: 결재 v4.9-D1 결과 — 잠정 (a) DB 테이블 token_blacklist(jti PK, expires_at, revoked_at)
- logout 시 jti + exp INSERT
- get_current_account_user 의존성에 SELECT 1 FROM token_blacklist WHERE jti=? 추가 → 존재 시 401
- exp 경과 row는 background task로 정리 (또는 PostgreSQL partial index)
- UserSession.is_active 체크도 동일 의존성에서 추가 (현재 부재)

**API 변경**: POST /api/auth/refresh 401 케이스 (type 가드), 모든 인증 엔드포인트 401 (blacklist hit)
**스키마 변경**: TokenClaims 또는 decode_token 반환 타입 확장
**DB 변경**: alembic v54 — token_blacklist 테이블 신설 + 인덱스 (jti UNIQUE, expires_at)
**명세 변경**: PRD_Auth_Migration.md §logout/refresh 절 전면 개정, GOP_Restful_Api_연동설계.md §인증 표
**실측(R2)**: PASS
**잔존 위험**: 결재 v4.9-D1 (DB/Redis/NATS KV 선택), 블랙리스트 row growth → 정리 정책

---

### 2.12 [B-1] WWW-Authenticate 글로벌 핸들러 보존 (P0)

**배경**: app/main.py:455-481 http_exception_handler가 JSONResponse 생성 시 `exc.headers`를 전달하지 않아 라우터에서 설정한 WWW-Authenticate: Bearer 헤더가 401 응답에서 사라짐. RFC 7235 미준수.

**요구**: 글로벌 HTTPException 핸들러가 exc.headers를 응답에 보존.

**설계**:
- app/main.py:455-481 http_exception_handler 수정: `return JSONResponse(status_code=exc.status_code, content={...}, headers=exc.headers)`
- RequestValidationError 핸들러(L484-523), general_exception_handler(L526-544)도 동일 패턴 적용 (해당 케이스 없음 확인 후)
- 회귀 테스트: tests/integration/test_auth_headers.py — 401 응답에 WWW-Authenticate: Bearer 헤더 단언

**API 변경**: 401 응답 헤더 회복 (RFC 7235 준수)
**스키마 변경**: 없음
**DB 변경**: 없음
**명세 변경**: GOP_Restful_Api_연동설계.md §인증 절에 "401 응답에 WWW-Authenticate: Bearer 헤더 포함" 명문
**실측(R2)**: PASS
**잔존 위험**: 없음 (단순 헤더 보존)

---

## §3 시나리오 50개 추적성 표

| sid | 항목 | 우선순위 | R1 | R2 |
|-----|------|---------|----|----|
| A-1.1 | photo_url 분기 | P1 | FAIL | PASS |
| A-1.2 | validator 화이트리스트 | P0 | FAIL | PASS |
| A-1.3 | /me/photo 엔드포인트 | P1 | FAIL | PASS |
| A-1.4 | 업로드 가드 7종 | P0 | FAIL | PASS |
| A-2.1 | PermissionsSchema 적용 | P1 | PASS(현)/FAIL(의도) | PASS |
| A-2.2 | 미정의 모듈 키 거부 | P0 | FAIL | PASS |
| A-2.3 | 미정의 verb 거부 | P0 | FAIL | PASS |
| A-2.4 | 시드 정규화 | P1 | FAIL | PASS |
| A-2.5 | StrictBool 강제 | P0 | FAIL | PASS |
| A-2.6 | OpenAPI 노출 | P1 | FAIL | PARTIAL |
| A-3.x (×4) | refresh TTL 분리 | P1 | FAIL | PASS |
| A-4.x (×8) | jti 블랙리스트 + type 가드 | P0 | FAIL | PASS |
| B-1.x (×4) | WWW-Authenticate 헤더 | P0 | FAIL | PASS |
| (기타 RBAC/Audit/Cross-item ×26) | 본 차수 범위 외 (v4.10) | P2 | - | - |

총 50건 중 본 차수 처리: 24건 / v4.10 이월: 26건.

---

## §4 Phase Grouping

### 4.1 v4.9 본 차수 (P0 + P1)

**Phase 1 — 안전점 회복 + 명세 5축 갱신** (1.5h)
- 9중 정합 안전점 기록 (코드 sha / DB schema / 명세 헤더-푸터-이력 / Swagger / Image tag / Container / CHANGELOG / session-context / Gitea PR)
- PRD_v4.9_Followup_AccountIntegration.md 본 파일 commit

**Phase 2 — Auth 정합 (A-3 / A-4 / B-1)** (4h)
- B-1: 글로벌 핸들러 headers 전달 (구조 변경, 30분)
- A-3: refresh TTL settings 분리 + utcnow 마이그레이션 (1h)
- A-4: token_blacklist 테이블 + jti 검증 의존성 + refresh type 가드 (2.5h)

**Phase 3 — Permission 모델 정합 (A-2 전건)** (6h)
- EnumPermissionModule + 6개 BaseModel + ModulesPermission + StrictBool (2h)
- UserGroupCreate/Update에 PermissionsSchema 적용 + OpenAPI 검증 (1h)
- alembic v52 시드 정규화 + 'rw'/'r' 문자열 → dict 변환 + LEGACY_INVALID_MODULE audit (2h)
- 회귀 테스트 + collect_module_verb_violations 공통 유틸 (1h)

**Phase 4 — Account Photo (A-1 전건)** (7h)
- A-1.1 + A-1.2: photo_url 분기 + validator 묶음 PR (1.5h)
- A-1.3: /me/photo 엔드포인트 + StaticFiles 마운트 + startup mkdir (2.5h)
- A-1.4: 가드 7종 + upload_validator.py 공유 헬퍼 + Pillow MAX_IMAGE_PIXELS (2.5h)
- alembic v53 ADD VALUE 마이그레이션 (0.5h)

**Phase 5 — 9중 정합 + 회귀 + 차수 마감** (2h)
- 5단 회귀 (unit / integration / contract / live / smoke)
- 명세 헤더-푸터-이력 동시 갱신 검증
- CHANGELOG v4.9 작성
- session-context Phase 1~5 통합
- Gitea PR + 안전점 final

**합계: 20.5h (3일 작업)**

### 4.2 v4.10 분리 (P2 cross-item)

**Phase 1 — Thumbnail Upload Hardening** (3h)
- app/routers/thumbnails.py에 upload_validator.py 공유 헬퍼 적용
- 매직바이트 + 스트림 카운터 + 파일명 sanitize + Pillow MAX_IMAGE_PIXELS

**Phase 2 — 정적 자원 인증 정책** (3h)
- /static/profiles 익명 vs 토큰 필수 결재 결과 반영
- ASGI 미들웨어 또는 별도 라우터 분기

**Phase 3 — AuditChange.rejected 메타 표준화** (2h)
- RejectedMeta(mime/size/reason/magic_prefix_hex) 모델
- PRD_Audit_Log.md 갱신
- 기존 description JSON → 구조화된 메타 마이그레이션 (옵셔널)

**합계: 8h (1일 작업)**

---

## §5 위험 등록부 + 완화 계획

| 위험 ID | 위험 | 완화 |
|--------|------|------|
| R-01 | v52 마이그레이션이 운영팀 cameras.control 권한 박탈 가능 | 결재 v4.9-D3 사전 승인 + 마이그레이션 dry-run 로그 + admin 알림 |
| R-02 | thumbnails.py 동일 결함 미해결 → cross-item 회귀 | v4.10 Phase 1에서 upload_validator.py 공유 헬퍼 적용 (본 차수에서 헬퍼만 추출) |
| R-03 | jti 블랙리스트 저장소(DB vs Redis vs NATS KV) 미결정 | 결재 v4.9-D1 — 잠정 DB 테이블로 시작 + NATS KV는 v5.0 후속 |
| R-04 | SELECT FOR UPDATE가 SQLite 테스트에서 no-op → race 미검출 | CI 매트릭스에 PostgreSQL 컨테이너 분기 추가 (@pytest.mark.requires_postgres) |
| R-05 | PNG bomb / 압축폭탄 → OOM | PIL.Image.MAX_IMAGE_PIXELS 강제 + 차원 검사 |
| R-06 | /static/profiles 익명 노출 시 사용자 사진 누구나 조회 가능 | 결재 v4.9-D2 + X-Robots-Tag: noindex 단기 적용 |
| R-07 | OpenAPI 변경이 외부 .NET 클라이언트 호환성 깨뜨림 | UserGroupResponse는 try/except + 'legacy_permissions_format' 플래그로 점진 전환 |
| R-08 | 기존 DB의 'rw'/'r' 문자열 row → ValidationError | v52 마이그레이션 선행 + LEGACY_INVALID_MODULE audit 큐 |
| R-09 | token_blacklist 테이블 row growth 무한 | exp 경과 row background task 정리 + partial index |
| R-10 | get_current_account_user 의존성에 DB 조회 1건 추가 → 성능 저하 | TTL 캐시(60s) + 토큰 만료 시 즉시 무효 |
| R-11 | 안전점 5단 회귀 중 1단이라도 실패 시 phase 진입 차단 | advance-phase.js status로 사전 확인 + 실패 시 즉시 안전점 복귀 |
| R-12 | 명세 3 위치(헤더/푸터/이력) 동시 갱신 누락 | Hook으로 자동 검증 + Phase 1과 Phase 5에서 2회 검증 |

---

## §6 안전점 정책 + 롤백 절차

### 6.1 안전점 5단 회귀 계층

| 단계 | 범위 | 도구 | 시간 |
|-----|------|------|------|
| L1 unit | 함수/메서드 | pytest -m unit | <30s |
| L2 integration | 라우터+DB | pytest -m integration | <3min |
| L3 contract | OpenAPI 스냅샷 | schemathesis | <2min |
| L4 live | localhost:8000 | curl 회귀 스크립트 | <5min |
| L5 smoke | 외부 IP / 내부 IP | 운영팀 검증 | 수동 |

### 6.2 Phase 진입 차단 규칙
- L1~L3 1개라도 실패 → 다음 Phase 진입 절대 금지
- L4 실패 → 즉시 직전 안전점으로 git reset (단 destructive 작업이므로 사용자 확인)
- L5 실패 → 차수 마감 차단 + 후속 PR 분리

### 6.3 롤백 절차
1. **코드 롤백**: `git revert <commit>` (절대 reset --hard 금지)
2. **DB 롤백**: alembic downgrade -1 (v54 → v53 → v52)
3. **컨테이너 롤백**: docker tag v4.8.x 재배포
4. **명세 롤백**: PRD 본 파일 history 절에 "v4.9 롤백" 기록
5. **session-context**: 롤백 사유 + Phase 재시작 지점 명시

### 6.4 불변성 원칙 6대 (v4.8 phase12-7 보고서 §3 준수)
1. AccountUser.login_id 불변 (생성 후 변경 금지)
2. AuditLog row immutability (UPDATE/DELETE 금지)
3. EnumAuditActionType ADD VALUE만 허용 (DROP 금지)
4. user_groups.permissions JSONB 스키마 단방향 진화 (필드 제거 금지)
5. token_blacklist.jti UNIQUE (재발급 금지)
6. UserSession.token 불변 (logout 후 재사용 금지)

---

## §7 시뮬 R1+R2 통합 결과 표

| 항목 | R1 결과 | R1 분량 | R2 결과 | R2 잔존 | 최종 분량 |
|------|--------|--------|--------|---------|----------|
| A-1.1 | FAIL | 40min | PASS | 0 | 40min |
| A-1.2 | FAIL | 90min | PASS | P2 settings | 120min |
| A-1.3 | FAIL | 180min | PASS | P2 정적 정책 | 240min |
| A-1.4 | FAIL | 170min | PASS | P1 thumbnails | 260min |
| A-2.1 | PASS(현)/FAIL(의도) | 60min | PASS | P3 legacy | 60min |
| A-2.2 | FAIL | 40min | PASS | P3 백필 | 50min |
| A-2.3 | FAIL | (R1 통합) | PASS | 0 | 15min |
| A-2.4 | FAIL | 50min | PASS | P1 운영팀 검증 | 60min |
| A-2.5 | FAIL | 30min | PASS | 0 | 30min |
| A-3 | FAIL | 60min | PASS | D4 결재 | 60min |
| A-4 | FAIL | 240min | PASS | D1 결재 | 280min |
| B-1 | FAIL | 30min | PASS | 0 | 30min |
| **합계** | 12 FAIL | 990min | 12 PASS | 7 잔존 | **1,245min ≈ 20.75h** |

---

## §8 DoD + 차수 종결 체크리스트

### 8.1 코드 DoD
- [ ] 12개 항목 전건 GREEN (R2 시뮬 + 실제 라이브 검증)
- [ ] 테스트 명명 규칙 준수 (should_X_when_Y)
- [ ] 모든 신규 endpoint 422/415/413/401/403 응답 케이스 명세 동기
- [ ] StrictBool / extra='forbid' 일관 적용
- [ ] Tidy First — 구조 변경/행위 변경 commit 분리

### 8.2 명세 DoD (3 위치 동시 갱신)
- [ ] PRD_v4.9_Followup_AccountIntegration.md (본 파일) 마스터 commit
- [ ] GOP_Restful_Api_연동설계.md 헤더 (v4.3 → v4.3.1)
- [ ] GOP_Restful_Api_연동설계.md 푸터 (변경 이력 행 추가)
- [ ] GOP_Restful_Api_연동설계.md 이력 절 (v4.9 차수 줄 추가)
- [ ] PRD_Account_Design.md §4.2.1 표 갱신
- [ ] PRD_Account_Implementation.md §시드 절 갱신
- [ ] PRD_Auth_Migration.md §logout/refresh 절 개정
- [ ] PRD_Audit_Log.md EnumAuditActionType 2건 추가
- [ ] PRD_User_Photo_Url_Validation.md 신설
- [ ] PRD_User_Profile_Photo_Upload.md 신설
- [ ] docs/INDEX.md 갱신

### 8.3 DB DoD
- [ ] alembic v52: 시드/permissions 마이그레이션 (운영 승인 후)
- [ ] alembic v53: EnumAuditActionType ADD VALUE 2건
- [ ] alembic v54: token_blacklist 테이블 신설
- [ ] downgrade 스크립트 검증

### 8.4 9중 정합 DoD (메모리 feedback_one_day_one_version 준수)
- [ ] 코드 sha 안전점 기록
- [ ] DB schema (alembic head) 안전점
- [ ] 명세 3 위치 동시 갱신 확인
- [ ] Swagger /openapi.json 스냅샷 갱신
- [ ] Docker image tag v4.9.x 빌드
- [ ] Container compose 파일 검증
- [ ] CHANGELOG v4.9 entry 작성
- [ ] docs/memory/session-context.md Phase 1~5 통합
- [ ] Gitea PR 생성 + 리뷰

### 8.5 결재 DoD
- [ ] v4.9-D1 jti 블랙리스트 저장소 결재
- [ ] v4.9-D2 /static/profiles 익명 접근 결재
- [ ] v4.9-D3 운영팀 cameras.control 권한 유지 결재
- [ ] v4.9-D4 refresh_token TTL 정책 결재
- [ ] v4.9-D5 정적 자원 storage path 결재

### 8.6 차수 마감 게이트
- [ ] Phase 1~5 전건 완료
- [ ] 안전점 5단 회귀 전건 PASS
- [ ] 결재 5건 응답 수신
- [ ] PR 리뷰 + 머지
- [ ] v4.10 cross-item 차수 issue 등록

---

**작성 완료**: 2026-06-24
**다음 액션**: §1.2 결재 5건 요청 + Phase 1 안전점 회복 진입
