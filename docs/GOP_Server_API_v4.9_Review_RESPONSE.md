# GOP API v4.9 Review — 회신 (Phase 5: SEC-1 적용 완료)

> **수신**: .NET 통합 UI 팀
> **발신**: API Server 팀 (이기호)
> **회신 일자**: 2026-06-24
> **근거**: 귀팀 `docs/GOP_Server_API_v4.9_Review_Issues.md` (전 도메인 전수 검토)
> **빌드**: `feature/device-group-bulk-unassign` commit (Phase 5 적용 직후)

---

## 0. 두괄식

| 항목 | 상태 |
|---|---|
| **SEC-1 (P0)** — Camera/Lamp/Server `user_password` 평문 노출 | **✅ 적용 완료** (v4.9 Phase 5, 8/8 PASS) |
| **DTO shape 변경** | **없음** (필드 유지, 값만 마스킹) → .NET 클라이언트 코드 변경 불필요 |
| **DB 영향** | **없음** (평문 저장 유지 — 백엔드 NVR/Speaker/Lamp/외부 서버 접속용) |
| **로그인 예시 자리표시자** | **적용 완료** (`<your_login_id>` / `<your_password>`) |
| **다른 P0/P1/P2 항목** | v4.10 별도 차수 권고 (하단 §3 일정) |

---

## 1. SEC-1 적용 상세 — 응답 마스킹

### 1.1 적용 방식

차장님 결재 (2026-06-24): **"계정 비번 다 보호, 삭제가 아니라 마스킹"**

- **공통 헬퍼**: `app/schemas/_password_mask.py` 신설
  - `PASSWORD_MASK = "********"` (8자 고정 — 길이 추정 차단)
  - `mask_password_serializer(value)`: None → None / 평문 → `"********"`
- **Pydantic v2 `@field_serializer("user_password")`** 패턴 — Response 직렬화 시점에만 변환
- **DB / Create·Update 요청 / 백엔드 내부 서비스**는 평문 유지 (장비 직접 접속 필요)

### 1.2 적용 4 Response 클래스

| Response 클래스 | 위치 | 마스킹 시점 |
|---|---|---|
| `CameraResponse` | `app/schemas/device.py:480` | GET 목록/단일/POST/PATCH/PUT 모든 응답 |
| `LampResponse` | `app/schemas/device.py:1037` | 동일 |
| `ServerResponse` | `app/schemas/server.py:135` | 동일 |
| `ServerNestedResponse` (Speaker nested 등) | `app/schemas/server.py:178` | 동일 |

> **정정**: 귀팀 §SEC-1에서 지적한 Camera nested `server.user_password` 평문은 ServerNestedResponse 경유 — 본 적용으로 자동 해소. CameraNestedResponse / Sensor / Controller는 `user_password` 필드 자체 미보유 → 마스킹 불필요 (이미 응답 노출 0).

### 1.3 example / 명세 자리표시자 정합화

| 위치 | 변경 |
|---|---|
| `ServerResponse.json_schema_extra` example | `"password123"` → `"********"` |
| `ServerNestedResponse.json_schema_extra` example | `"password123"` → `"********"` |
| `ServerCategorySummary` nested example | `"password123"` → `"********"` |
| `LampResponse.user_password` example | `"lamp1234"` → `"********"` |
| `ServerCreate` request example | `"password123"` → `"<your_password>"` |
| `LampCreate` / `LampUpdate` request example | → `"<your_password>"` |
| 명세 §9.2.2 `/api/auth/login` request | `"admin/admin123"` → `"<your_login_id>/<your_password>"` |
| 명세 §5.3.x Camera 응답 예시 | `"admin1234"` → `"********"` |

### 1.4 실측 검증 8/8 PASS

| # | 시나리오 | 결과 |
|---|---|:---:|
| 1 | Camera 목록 응답 `user_password` | `"********"` ✅ |
| 2 | Camera 단일 응답 | `"********"` ✅ |
| 3 | Lamp 단일 응답 | `"********"` ✅ |
| 4 | Server 단일 응답 (시드 `testpwd123` 주입 후) | `"********"` ✅ |
| 5 | DB 평문 유지 (`cameras.user_password='sensorway1'`, `servers.user_password='testpwd123'`) | ✅ |
| 6 | OpenAPI `/openapi.json` ServerResponse example | `"********"` ✅ |
| 7 | Camera POST: 요청 평문 → DB 평문 저장 → 응답 마스킹 (3중 흐름) | ✅ |
| 8 | Container Up healthy / Image rebuild 완료 | ✅ |

### 1.5 클라이언트 영향 (요약)

- ✅ **.NET 측 코드 변경 불필요** — DTO shape 동일, 필드 유지
- ✅ **역직렬화 코드 그대로 사용 가능** — `string?` 또는 `string`으로 받으면 됨
- ✅ **사용 시점 비번 표시 UI** — `"********"` 그대로 표시 (이미 보안 UI 패턴)
- ⚠️ **본 응답으로 RTSP/SSH 직접 접속 시도 시 실패** — 그러나 일반적인 GET 응답으로 자격증명 사용은 부적절한 패턴. 별도 secret API가 필요하면 v4.10에서 협의 가능.

---

## 2. 차수 정합 (하루 1차수 묶음 원칙)

본 작업은 v4.10 신설이 아니라 **v4.9 Phase 5**로 통합. 사유:
- 2026-06-24 작업 → 메모리 `feedback_one_day_one_version` 절대 원칙
- 명세 v4.9 행 안에 Phase 0~5 통합 기재
- 안전점: `pre-v4.9-phase5` @ 8afcc45 (롤백 단일 회귀점)

---

## 3. .NET v4.9 Review 다른 항목 — v4.10+ 일정 권고

| 우선 | ID | 항목 | 권고 차수 | 분량 |
|---|---|---|---|---|
| **P0** | ENV-1 | Response envelope 5종 표준화 (목록/에러/me/meta/DELETE) | v4.10 | ~8-12h |
| **P0** | AUTH-1 | 토큰 `expires_in`/TTL 응답 노출 | v4.10 | ~30m |
| **P0** | AUTH-2 | `PUT /api/users/me/password` 본문 스키마 명세화 | v4.10 | ~1h |
| P1 | FMT-1 | datetime timezone 통일 (`Z` 또는 `+09:00`) | v4.10 | ~4h |
| P1 | ENUM-1 | Enum 케이싱 정책 + `EnumBuzzerSound` 특수문자 | v4.10 | ~3h |
| P1 | ENUM-2 | Enum 정의 ≠ 예시 불일치 (8.7 / type_device / EnumDetectionType 4) | v4.10 | ~3h |
| P1 | DEV-1 | §5.7 `is_restricted_zone` Preset 예시 누락 | v4.10 | ~30m |
| P1 | DEV-2 | 메트릭 number→string 직렬화 불일치 | v4.10 | ~2h |
| P1 | EVT-1 | §6.2.7 `from_event.detail.reason` 구포맷 / §6.3.5 PUT body `device_id` (불변 정책 위반!) | v4.10 | ~3h |
| P1 | INT-1 | Lamp 비대칭 (`data:[...]` / `event_mapping_id` body 중복 / 응답 예시 부재) | v4.10 | ~3h |
| P1 | SVR-1 | `acknowledged` vs `is_acknowledged` / Report 라이프사이클 / pagination 구조 | v4.10 | ~4h |
| P1 | AUTH-3 | bcrypt / HS256 알고리즘 §9 본문화 | v4.10 | ~30m |
| P1 | AUTH-4 | 423 Locked 코드 / PATCH vs PUT 3곳 동기화 | v4.10 | ~1h |
| **잔존** | B-4 | `GET /api/users/check-login-id` | v4.10 | ~1h |
| **잔존** | B-5 | `GET /api/users/{id}/login-history` | v4.10 | ~1.5h |
| **잔존** | B-7 | permissions를 `/users/me` + refresh에 포함 | v4.10 | ~1h |
| **잔존** | B-8 | 목록 응답 pagination meta 통일 | v4.10 | ~1.5h |
| P2 | DOC-1~3 | JSON 예시 lint / 응답 예시 누락 / 위험한 기본값 | v4.11 | ~3h |

**총 v4.10 예상**: P0 3건 + P1 10건 + 잔존 4건 ≈ **38-45h** (3~5일 분량)

---

## 4. ENV-1 (목록 응답 형태) 클라이언트 협의 요청

귀팀이 지적한 5종 혼재를 단일 표준으로 정렬할 때, 클라가 가장 쉬운 형태가 어느 쪽인지 확인 요청:

**Option A (권고)**: `data: [...]` + 상위 `pagination: {page, limit, total, total_pages}`
**Option B**: `data: { items: [...], pagination: {...} }` (items 묶음형)

→ Option A로 가면 §7.3/7.4 Camera/Speaker mapping의 `data: {items, total}` 형태가 광범위 변경됨. 그쪽 클라가 의존하는 부분 있으면 회신 부탁드립니다.

---

## 5. 회신 받고 싶은 사항 (한 줄)

1. **SEC-1 적용 확인** — 본 회신 확인 후 .NET 빌드 회귀 발생 여부 (예상: 없음)
2. **ENV-1 옵션 선호** — Option A vs B
3. **v4.10 진입 일자** — 2026-06-25부터 진행해도 무방한지

---

문의: 본 문서 댓글 또는 PR 채널 — API Server 팀 (lsirikh@gmail.com)

---

## POLICY UPDATE 2026-06-25 — v4.10 Phase 1 회귀 (SEC-1 마스킹 → 평문 응답)

**상태**: v4.9 Phase 5 (SEC-1 응답 마스킹)는 적용 24시간 만에 **정책 회귀**.

**결재 (2026-06-25)**: 이기호 차장 — *"야 그냥 평문으로 보내. 복호화방법도 없는거 같은데"*

**회귀 사유**:
- 마스킹된 `"********"` 응답을 평문으로 되돌릴 **복호화 경로 미정**
- .NET이 NVR / Speaker / Lamp / 외부 서버에 RTSP/SSH/HTTP 접속할 때 평문 자격증명 필요
- 별도 secret API / AES / RSA / 보안 프록시 등 대안은 모두 분량 큼 (4~20h+, .NET 측 변경 동반) → 본 차수 범위 외

**적용 결과 (v4.10 Phase 1, 6/6 PASS)**:
- Camera/Lamp/Server 4 Response 클래스에서 `@field_serializer("user_password")` 제거
- 응답 `user_password` = **DB 평문 그대로** (예: `"sensorway1"`, `"lamp123"`, `"password123"`)
- **DTO shape 변경 0** — `.NET` 클라이언트 역직렬화 코드 변경 불필요
- OpenAPI example도 평문 회귀 (`"password123"` 등)
- `app/schemas/_password_mask.py` 파일은 **heritage 보존** (사용처 0, v5.x secret API 재활용 가능)

**보안 트랙 예고**: 별도 차수(v5.x)에서 secret API + 복호화 경로 + .NET 측 사용 시점 호출 패턴까지 종합 재설계 예정. 본 차수에서는 단순 회귀만 적용.

**P1/P2 항목**: 별도 차수 일정은 위 §3 권고 유지 (v4.10 ~38-50h).

---

## SECURITY UPDATE 2026-06-25 — v4.10 Phase 2: HTTPS 도입 (mkcert 폐쇄망)

**상태**: Phase 1 평문 응답 정책 회복 직후 통신 구간 보안 강화 — **GOP API 서버는 HTTPS만 노출**.

**결재 (2026-06-25)**: 이기호 차장 — *"가장 간단하고 쉬운거 신뢰되고. 우리 폐쇄망이야"* + *"서버 1대 + 여러 클라 PC"* + *"EXE 1클릭 자동 등록"*

**적용 결과**:
- 서버 인증서 = `mkcert` (외부 인터넷 불필요, OS 신뢰 저장소 자동 등록, 만료 2028-09-25)
- Docker `Uvicorn https://0.0.0.0:8000` 시작 + 평문 HTTP 차단
- 6/6 실측 PASS

**클라이언트 PC 배포 도구** (`Ironwall.Dotnet.Libraries` UI 팀 + 다른 사용자 PC):
- `GOP-RootCA-Installer-v1.0.0.exe` (Inno Setup 정식 GUI 인스톨러, 1.5~2.5MB)
- 사용법: USB 받기 → 더블클릭 → UAC "예" → "다음/다음/완료" → 완료 (5초)
- 인스톨러 동작: `certutil -addstore -f Root rootCA.pem` (Windows `신뢰할 수 있는 루트 인증 기관`에 등록)
- 제어판 → 프로그램 추가/제거에서 깔끔 제거 가능 (자동 등록)
- 가이드: `docs/GOP_RootCA_Installer_Guide.md`

**.NET HttpClient 영향**:
- 인스톨러 실행한 PC에서는 `https://192.168.x.x:8000` 자동 신뢰 (별도 코드 변경 없음)
- `ServerCertificateCustomValidationCallback` 우회 코드 **불필요** (제거 권고)
- `BaseAddress`만 `http://` → `https://` 변경

**클라 측 변경 요청**:
1. .NET 통합 UI 빌드의 `BaseAddress` HTTPS로 변경
2. 모든 .NET 팀 PC에 `GOP-RootCA-Installer-v1.0.0.exe` 1회 실행 (USB 전달 예정)
3. 인증서 신뢰 우회 코드 (`SSLValidation = false` 등) 있으면 제거

**P0 ENV-1 우선순위 영향**: HTTPS 적용으로 envelope 표준화 작업의 우선순위는 유지하되, 평문 노출 위험은 즉시 완화됨.
