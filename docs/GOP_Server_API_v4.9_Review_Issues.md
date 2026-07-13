# GOP RESTful API v4.9 — 전수 검토 이슈리스트 (서버팀 회신 요청)

> **배경**: v4.9(2026-06-24) 명세를 .NET 클라이언트 연동 관점에서 **전 도메인 전수 검토**했습니다(§1~§12, 약 15,700줄). v4.7~v4.9에서 인증을 적극 하드닝해 주신 점 감사합니다.
> **목적**: GOP-00(Direct-DB 인증 → JWT Bearer 전환) 착수 전, 클라이언트 자동 역직렬화를 막는 결함을 확정·정리합니다.
> **이 문서와 기존 `GOP_Server_API_FollowupRequests.md`의 관계**: 기존 문서는 **Account 도메인 한정**이며 B-4/5/7/8이 잔존 상태입니다(§6 참조). 본 문서는 **전 도메인 신규 이슈 + 횡단 결함**을 다룹니다.
> **작성일**: 2026-06-24 / **작성**: .NET 통합 UI 팀
> **표기**: 위치 라인 번호는 v4.9 원문(`GOP_Restful_Api_연동설계.md`) 기준 근사값입니다.

---

## 0. 요약 — P0부터 봐 주세요

| 우선 | ID | 한 줄 | 분류 |
|---|---|---|---|
| **P0** | SEC-1 | `user_password` 평문 응답 노출(다수 도메인) | 보안 |
| **P0** | ENV-1 | Response 봉투(envelope) 표준 1종 미확정 → 역직렬화 분기 폭발 | 연동차단 |
| **P0** | AUTH-1 | 토큰 `expires_in`/TTL이 응답에 없음 | 인증 |
| **P0** | AUTH-2 | `PUT /users/me/password` 요청 본문 스키마 부재 | 인증 |
| P1 | FMT-1 | datetime timezone 표기 3종 혼재 | 정합성 |
| P1 | ENUM-1 | Enum 직렬화 케이싱 7종 + 특수문자 값 | 정합성 |
| P1 | ENUM-2 | Enum **정의 ≠ 예시** 값 불일치 | 역직렬화 |
| P1 | DEV-1~2 · EVT-1 · INT-1 · SVR-1 · RPT-1 | 도메인별 신규 결함 | 정합성 |
| P1 | AUTH-3·4 + 기존 B-4/5/7/8 잔존 | 인증 완전화 | 인증 |
| P2 | DOC-1~3 | JSON 예시 린트·예시 누락 | 문서품질 |

---

## 1. P0 — 보안 / 연동 차단 (착수 전 확정 필요)

### SEC-1 🔴 `user_password` 평문 응답 노출 (보안)
- **현황**: GET/POST/PATCH 응답에 비밀번호가 평문으로 포함.
  - §5.3.2 Camera 단일조회 `"user_password":"password123"` (단, §5.3.1 목록은 `********` 마스킹 — **동일 리소스 내 비일관**)
  - §5.4 Speaker nested `server.user_password` 평문 (L3444/3532/3663/3806)
  - §8.3.2 / 8.3.3 / 8.3.4 / 8.4.1 Server·Dashboard `"user_password":"password123"`
  - §9.2.2 로그인 예시에 평문 기본 자격증명 `admin / admin123`
- **요청**: 응답 DTO에서 password를 **write-only**(전 응답 제거 또는 마스킹) 처리. 로그인 예시는 자리표시자(`<your_password>`)로 치환.
- **사유**: 클라가 수신·로그에 기록할 위험. 응답에서 비밀번호가 나갈 이유가 없음.

### ENV-1 🔴 Response 봉투 표준 1종 확정 + 전 섹션 sweep (연동 차단)
클라이언트가 **단일 역직렬화 경로**를 가질 수 없게 만드는 최대 결함입니다. 아래 5개 하위 항목을 하나의 표준으로 못박아 주세요.

1. **목록 `data` 형태 3종 혼재**:
   - `data:[...]` + 상위 `pagination` (표준, 다수)
   - `data:{items:[...], total:N}` (§7.3/7.4 Camera/Speaker mapping, §8.3.7) — `total`이 `data.total`·`pagination.total` **이중**
   - `data:{points:[...]}` (§5.9 XyPoint), `data:[...]` raw·pagination/meta 없음 (§5.10 FileGroup, §5.11 Lamp, §7.5.1 Lamp, §9.3 users, §9.5 sessions)
   → **요청**: `data:[...]` + 상위 `pagination{page,limit,total,total_pages}` 단일 형태로 통일.
2. **에러 봉투 4종 혼재** → 표준 `{success:false, error:{code,message,details}, meta}` 로 통일. 특히 **FastAPI raw `{"detail":...}` 제거** (§9.2.4 401, §10.3.3 404).
3. **`/api/auth/me`가 봉투 없이 raw user 객체 반환** (§9.2.5) → `{success, data:{...}}` 적용.
4. **`meta`(timestamp/request_id) 누락** → §5.5 Enclosure, §5.10 FileGroup, §5.11 Lamp, §7.x 삭제 응답에 추가.
5. **DELETE 응답 통일**: §3.3 표에 200·204 **동시 명시(모순)**. data 형태도 `{deleted:true,id}` / `{id}` / `data:null` / 없음 혼재. → 한 형태로 확정.

### AUTH-1 🔴 토큰 `expires_in`/TTL 응답 노출 (§9.2)
- **현황**: `POST /auth/login`·`/auth/refresh` 응답에 access/refresh **만료시간이 없음**. 변경이력에만 `JWT_REFRESH_EXPIRATION_DAYS=7`.
- **요청**: 로그인/refresh 응답에 `expires_in`(초)·`refresh_expires_in` 추가. access TTL 값 본문 명문화.
- **사유**: 클라가 토큰 갱신 시점을 계산할 수 없음.

### AUTH-2 🔴 `PUT /api/users/me/password` 요청 본문 스키마 부재 (§9.3.1)
- **현황**: 엔드포인트만 나열, 요청 본문(`current_password`/`new_password`)·응답·검증규칙(현재 비번 불일치 시 코드) 없음.
- **요청**: 본문 스키마 + 400/422 매핑 명시.
- **사유**: ChangePassword 게이트웨이 구현 불가.

### AUTH-3 🟠 비밀번호 해싱 / 토큰 서명 알고리즘 명세 본문화 (§9)
- **현황**: bcrypt/argon2·HS256/RS256 언급이 §9 본문에 없음(변경이력에만).
- **요청**: §9.1 또는 §9.2에 알고리즘·서명키 정책 1줄.

---

## 2. P1 — 횡단 정합성 (정책으로 한 번 확정)

### FMT-1 🟠 datetime timezone 표기 통일 (S3)
- **현황**: 동일 의미 필드가 섹션마다 다름 — `....000Z`(UTC,ms: Controller/Sensor/Camera) / `....000000`(no-tz,μs: Speaker §5.4, Enclosure §5.5, FileGroup §5.10) / `...+09:00`(KST: §6.6/8.4/9/7.3·7.4) / `"2025-01-15 00"`(비-ISO: §6.7 time_bucket).
- **요청**: §3/§4 상단에 **ISO 8601 + 단일 오프셋(`Z` 또는 `+09:00`)** 정책 명문화 후 전 예시 통일.
- **사유**: no-tz 문자열은 C# `DateTimeOffset`이 Local로 해석 → UTC 비교 오류.

### ENUM-1 🟠 Enum 직렬화 케이싱 정책 (S4)
- **현황**: 케이싱 7종 혼용 — UPPER_CASE(주류) / lowercase(`EnumOnOff:on/off`, `EnumWindyMode:wind0`, `EnumLightMode`, `EnumDeviceCategory`) / PascalCase(`EnumDeviceType`, `EnumEventType`, `EnumTrueFalse`) / Title(`EnumLampColor:Red`) / **특수(`EnumBuzzerSound:"Fire A-WANG"` — 공백+하이픈)**.
- **요청**: 케이싱 정책 명문화(가능하면 UPPER_SNAKE 통일). 특히 **`EnumBuzzerSound` 값의 공백/하이픈은 URL 쿼리 파라미터 인코딩 문제** → 토큰형 값 재검토. `EnumTrueFalse`(bool 대신 존재 이유)·사용처 명시.

### ENUM-2 🟠 Enum 정의 ≠ 예시 값 불일치 (S5, 역직렬화 실패 유발)
- §8.7 `EnumSystemEventType` 정의는 UPPER_SNAKE(`RESOURCE_THRESHOLD`)인데 예시는 `threshold_warning`/`custom`(소문자, 정의에 없는 값)
- `type_device`: §5.2 nested에 `MainController` vs 상위 `Controller`
- Speaker `type_device`: §7.4.1 `Speaker` vs §7.4.8 `IpSpeaker`
- `EnumDetectionType` 정수값 **4 누락** (0,1,2,3,5,6,…) → `(EnumDetectionType)4` 미정의
- `action_reported` 쿼리 파라미터: 문자열 `"True"/"False"` vs bool `true/false` 불명확
- **요청**: 정의(§4)와 예시·필터를 교차 동기화. 누락 정수값은 `// 제거됨`/`RESERVED` 명시.

---

## 3. P1 — 도메인별 신규 결함

### DEV-1 🟠 §5.7 `is_restricted_zone`(v4.6 승인) 필드가 모든 Preset 예시에서 누락
- 섹션 서두(L5707)에만 설명, POST/PATCH/PUT 필드표·전 응답 예시에서 빠짐 → 클라가 송수신 코드 작성 불가.
- **요청**: 5.7.3 필드표 + 5.7.1~5.7.5 응답 `data`에 `is_restricted_zone:false` 추가.

### DEV-2 🟠 §5.5.9 메트릭 수치 필드 number→string 직렬화
- 요청 `"temperature":25.5`(number) → 응답 `"temperature":"25.5"`(string). humidity/current/voltage 동일. **§5.5.13 독립조회는 number** → 동일 엔티티 타입 불일치.
- **요청**: 전 메트릭 응답에서 number로 통일. (C# `double` 역직렬화 실패 방지)
- (관련) §5.5.10 메트릭 목록 `pagination` 누락 · §5.3 `location` vs `install_location` 키 혼재 · §5.2 `include=false` 시 null vs 키생략 계약 명시.

### EVT-1 🟠 §6 Event
- **§6.2.7 `from_event.detail.reason` 구포맷 잔존** — v2.6은 `reason` top-level인데 nested from_event만 구포맷 → C# `null` 역직렬화.
- **§6.2.5 PUT 응답 `action_reported:"True"` 모순** (해당 문맥에 ActionEvent 없음, v2.8 정책상 서버 자동관리).
- §6.1.1 device-deleted 응답 `pagination` 누락 · §6.3.5 PUT body에 `device_id`(불변 정책 위반) · §6.6 thumbnail 최대크기/캐시/상대·절대 URL 불명 · §6.7 time_bucket 비-ISO.

### INT-1 🟠 §7 Integration — Lamp 비대칭 / 벌크 정책 불일치
- **§7.5.1 Lamp 목록 `data:[...]` 배열 직접** (Cam/Spk은 `{items,total}`) → 통일.
- **§7.5.3 / 7.5.10 Lamp body에 `event_mapping_id`** — path와 중복/충돌. (Cam/Spk은 body에 없음) → body에서 제거.
- §7.5.2/7.5.4/7.5.5 Lamp 응답 예시·필드표 **부재**.
- §7.4.9 Speaker 벌크 응답에 `skipped_config_ids`/`not_found_config_ids` 누락(Cam/Lamp은 포함).
- **ConfigChangeLog 발행 정책 불일치**: Camera 벌크=무조건 1건 / Speaker·Lamp 벌크=`created_ids≥1`일 때만 → 통일 또는 의도 명시.

### SVR-1 🟠 §8 Server / §10 Report
- **§8.7 `acknowledged`(per-server) vs `is_acknowledged`(전역) 필드명 불일치** → 동일 DTO 역직렬화 시 한쪽 default.
- §8.8 `EnumOperationMode`/`EnumWindyMode` **허용값 목록 미정의**(예시만) → §8.1/8.8에 전체 값 테이블 + 422 예시.
- §8.3.7 pagination 구조 `{items,total}` + `total` 없음(`total_pages`만) → 표준화.
- **§10.4 리포트 비동기 생성 라이프사이클 미완성**: 상태전이(`PENDING→GENERATING→COMPLETED|FAILED`)·polling 엔드포인트·`error_message` 필드 부재 → 명시.
- §10.1 "컴포넌트 15종" vs §10.2.2 실제 21종 카운트 불일치.

### AUTH-4 🟠 인증 기타 (§9/§11)
- 로그인 실패(401)·계정잠금 응답 형식이 §11 표준 봉투와 불일치(FastAPI raw). **§11.2 표준 표에 `423 Locked` 없음** → 잠금 HTTP 코드 확정.
- `PATCH /api/users/{id}` 존재 여부 모순: §9.3.1·§12.1은 PUT-only, §9.6.4 audit표엔 PATCH → 3곳 동기화.

---

## 4. P2 — 문서 품질 / 편집 잔재

### DOC-1 JSON 예시 유효성 (S7)
- **§5.3.3 trailing comma → JSON 파싱 실패**(예시 그대로 복사 시 오류).
- **JSON 인라인 주석** `// (optional)`·`// Deprecated` (§5.6/5.7/5.11) — JSON 표준 위반.
- §6.5.1 `"device":{"..."}` placeholder, §12.1 불릿 내 표 행 삽입(markdown 깨짐), 연도 2025/2026 혼재(삭제 예시·§11.1 meta·§7.2.6).

### DOC-2 응답 예시 누락
- §5.5.2 Enclosure 상세, §5.11 Lamp 상세/POST/PATCH/PUT, §7.5 Lamp 응답 예시 — 통합 불가 수준이므로 완전한 JSON 예시 추가.
- §5.8.5 ROI PUT의 `points` 생략 시 동작(유지 vs 삭제) 명시.

### DOC-3 위험한 기본값 / 기타
- §5.5.12 메트릭 bulk DELETE에서 `before_date` 미지정 시 **전체 삭제** → `confirm=true` 요구 또는 422.
- §3.1 Authorization 헤더 필수/선택(로그인 제외) 명시 · §2.4 페이지네이션 지원 엔드포인트·`sort` 허용필드 정의.

---

## 5. P1 — 기존 후속요청(`GOP_Server_API_FollowupRequests.md`) v4.9 반영 현황

| 기존 ID | 항목 | v4.9 상태 | 잔존 요청 |
|---|---|---|---|
| B-1 | access_token 강제 무효화 | ✅ jti 블랙리스트 적용 | (확인) access까지 확장됐는지 |
| B-3 | 서버측 RBAC 게이트 | ✅ RBAC 강타입(422) | — |
| A-2 | permissions.modules enum | ✅ `EnumPermissionModule`(8)·`Verb`(4) | enum 전체 값 명세 §4 반영 확인 |
| A-4 | 401 envelope·WWW-Authenticate | ✅ 헤더 보존 | 401 본문이 §11 표준봉투인지(AUTH-4 참조) |
| **B-4** | login_id 중복확인 `GET /users/check-login-id` | 🔲 **잔존** | **v4.10 일정 확정** (IsUsernameTaken) |
| **B-5** | 로그인 이력 `GET /users/{id}/login-history` | 🔲 **잔존** | **v4.10 일정 확정** (GetLatestLogin) |
| **B-7** | permissions를 `/users/me`(+refresh)에 포함 | 🔲 **잔존** | **권한 갱신 단일호출 위해 필요** |
| **B-8** | 목록 응답 pagination meta | 🔲 **잔존** | users/sessions/user-groups 목록 |
| B-2 | 강제 로그아웃 NATS 채널 | (메시지 브로커 문서 영역) | 별도 확인 |
| B-6 | 계정 잠금 메타데이터 영속 | 🔲 확인 필요 | `lock_reason`/`locked_at`/`locked_by` |

---

## 6. 회신 요청

1. **P0 4건(SEC-1·ENV-1·AUTH-1·AUTH-2)** — 결재 여부 + 목표 버전/일자. 특히 **ENV-1(봉투 표준)**은 전 도메인 클라 모델을 좌우하므로 표준안을 **결재 전 미리 공유**해 주시면 클라가 선반영하겠습니다.
2. **기존 잔존 B-4/5/7/8** — v4.10 일정 확정 요청(GOP-00 게이트웨이 직접 의존).
3. **FMT-1·ENUM-1** 정책(datetime/enum 케이싱)은 한 번 정하면 광범위 영향 → 방향만이라도 회신 부탁드립니다.

> 전체 근거·라인 참조는 클라이언트 내부 검토 리포트(`Docs/analysis/GOP_Restful_Api_v4.9_Review-analysis.md`)에 있습니다. 항목별 상세가 필요하시면 알려주세요.
> 문의: 본 문서 댓글 또는 PR 채널 — .NET 통합 UI 팀
