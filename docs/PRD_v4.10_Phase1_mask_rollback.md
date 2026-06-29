# PRD v4.10 Phase 1 — SEC-1 마스킹 정책 폐기 / 평문 응답 복원

> **차수**: v4.10 (2026-06-25 단일 차수, 하루 1차수 묶음 원칙 준수)
> **Phase**: 1 — 응답 마스킹 회귀 (Track B, 5파일 수정)
> **안전점**: `pre-v4.10-phase1` @ commit 31bb478 (직전 c48c1f6 = v4.9 Phase 5 적용 직후)
> **결재**: 이기호 차장 2026-06-25 — *"야 그냥 평문으로 보내. 복호화방법도 없는거 같은데"*

---

## 0. 두괄식 (정책 회귀)

| 항목 | 상태 |
|---|---|
| **v4.9 Phase 5 SEC-1 마스킹 정책** | **폐기 (DEPRECATED)** |
| **응답 user_password** | **평문 회귀 (RESTORED)** — Camera/Lamp/Server 4 Response 클래스 |
| **DTO shape 변경** | **0** — 필드 그대로 유지, 값만 평문으로 회귀 |
| **.NET 호환성** | **100%** — 클라이언트 코드 변경 불필요 (역직렬화 string?/string 그대로) |
| **DB 영향** | **0** — 평문 저장은 이미 유지 중이었음 |
| **회귀 범위** | schema 5건 / example 4건 / 명세 2건 + `_password_mask.py` 사용처 0건 (파일 보존) |

---

## 1. 배경

### 1.1 차장님 결재 (2026-06-25)

> *"야 그냥 평문으로 보내. 복호화방법도 없는거 같은데"*

### 1.2 v4.9 Phase 5 마스킹의 근본 한계 — 복호화 경로 부재

v4.9 Phase 5에서 `mask_password_serializer`로 응답을 `"********"` 8자 고정 마스크로 치환했으나, **복호화 방법이 정의되지 않음**. 결과적으로:

- .NET 통합 UI가 NVR(VMS) / Speaker / Lamp / 외부 서버에 RTSP/SSH/HTTP 접속할 때 필요한 평문 자격증명을 받을 수 없음
- 별도 secret API / AES / RSA / 보안 프록시 등 대안은 모두 분량이 큼 (각 옵션 4~20h+, .NET 측 변경 동반)
- 운영 사용 케이스 5건 (등록 직후 확인 / 관리자 화면 / 통합상황도 자동연결 / 백업·이관 / 감사 화면) 회복 필요

### 1.3 결재 의도

- **단순 평문 응답으로 회귀** — v4.4 Phase 5 ~ v4.9 Phase 4 정책 재적용
- 보안 정책은 v5.x 별도 차수에서 복호화 경로(secret API 등)와 함께 재설계
- `_password_mask.py` 파일은 **heritage 보존** — v5.x 재사용 가능, 단 사용처 0

---

## 2. 회귀 대상 (코드 5건 + example 4건 + 명세 2건)

### 2.1 Schema 회귀 (`@field_serializer` 제거 + import 제거)

| # | 파일 | 위치 | 회귀 내용 |
|---|---|---|---|
| 1 | `app/schemas/device.py` | L12 | `from app.schemas._password_mask import mask_password_serializer` **제거** |
| 2 | `app/schemas/device.py` | L518-520 | `CameraResponse._mask_user_password` `@field_serializer` 블록 **제거** |
| 3 | `app/schemas/device.py` | L1073-1075 | `LampResponse._mask_user_password` `@field_serializer` 블록 **제거** |
| 4 | `app/schemas/server.py` | L7 | `from app.schemas._password_mask import mask_password_serializer` **제거** |
| 5 | `app/schemas/server.py` | L156-158 | `ServerResponse._mask_user_password` **제거** |
| 6 | `app/schemas/server.py` | L207-209 | `ServerNestedResponse._mask_user_password` **제거** |

> Field 설명 문구 정정: `"접속 비밀번호 (응답 시 마스킹 — DB 평문 유지)"` → `"접속 비밀번호"`

### 2.2 OpenAPI example 회귀 (4건)

| # | 위치 | 변경 |
|---|---|---|
| 1 | `ServerResponse.json_schema_extra.example.user_password` | `"********"` → `"password123"` |
| 2 | `ServerNestedResponse.json_schema_extra.example.user_password` | `"********"` → `"password123"` |
| 3 | `ServerCategorySummary` nested servers example user_password | `"********"` → `"password123"` |
| 4 | `LampResponse` `user_password` Field example (device.py:1059) | `"********"` → `"lamp1234"` |

> Field 설명 문구도 정정: `"접속 비밀번호 (응답 시 마스킹 — DB 평문 유지)"` → `"접속 비밀번호 (max: 255)"`

### 2.3 명세 (`GOP_Restful_Api_연동설계.md`) 회귀 (2건)

| # | 위치 | 변경 |
|---|---|---|
| 1 | §5.3.x Camera 응답 예시 (L2413, L5103) | `"user_password": "********"` → `"user_password": "admin1234"` |
| 2 | §9.2.2 `/api/auth/login` request 예시 (L14112-14113) | `<your_login_id>/<your_password>` 자리표시자는 **유지** (로그인 자격증명은 도메인 다름 — 마스킹 대상 아님) |

> 명세 다른 위치 `"password123"` / `"lamp1234"` 등은 v4.9 Phase 5 이전부터 평문이었으므로 변경 불필요.

### 2.4 `_password_mask.py` 처리

- **파일 유지** (`app/schemas/_password_mask.py` 29 lines)
- 사용처는 0으로 줄어듦 (import 4건 모두 제거)
- 헤더 docstring에 `(deprecated v4.10, retained for v5.x secret API)` 한 줄 추가

---

## 3. 비적용 영역 (어제와 동일)

| 영역 | 상태 | 사유 |
|---|---|---|
| DB 컬럼 (cameras/lamps/servers.user_password VARCHAR) | **변경 0** | 백엔드 장비 접속용 평문 필요 |
| `CameraCreate` / `LampCreate` / `ServerCreate` 등 요청 schema | **변경 0** | POST/PUT/PATCH는 평문 입력 받음 |
| `CameraUpdate` / `LampUpdate` / `ServerUpdate` 요청 schema | **변경 0** | 동일 |
| 백엔드 서비스 (`device_service`, NATS publisher 등) | **변경 0** | ORM 모델에서 직접 평문 사용 중 |
| 시드 (`init_sample_data.py`) | **변경 0** | Static seed 평문 (admin/admin123 등) |
| Audit Log `changes` 필터 (§14.5 — user_password 마스킹 목록) | **변경 0** | 로그 기록 제외는 별도 안전망 — 유지 |

---

## 4. 검증 시나리오 (5건, bash 명령 포함)

| # | 시나리오 | 기대 결과 |
|---|---|---|
| 1 | Camera 단일 응답 평문 | `curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/cameras/1 \| jq -r '.data.user_password'` → DB 평문 그대로 (예: `sensorway1`) |
| 2 | Lamp 단일 응답 평문 | `curl ... /api/lamps/1 \| jq -r '.data.user_password'` → DB 평문 (예: `lamp1234`) |
| 3 | Server 단일 응답 평문 | `curl ... /api/servers/1 \| jq -r '.data.user_password'` → DB 평문 |
| 4 | Camera POST 응답 평문 (요청 평문 → DB 저장 → 응답 평문 3중 흐름) | `curl -X POST ... -d '{"user_password":"newpwd"}' /api/cameras` → 응답 `user_password` = `"newpwd"`, DB SELECT = `"newpwd"` |
| 5 | OpenAPI example 평문 | `curl -s http://localhost:8000/openapi.json \| jq -r '.components.schemas.ServerResponse.example.user_password'` → `"password123"` |

---

## 5. 메모리 정책 전환

| 메모리 | 전환 |
|---|---|
| `feedback_password_masking_policy.md` | **DEPRECATED** 표기 + `superseded_by: feedback_password_plaintext_policy` |
| `feedback_password_plaintext_policy.md` | **RESTORED** — DEPRECATED 표기 제거, 현행 정책 재명시 |
| `MEMORY.md` 한 줄 설명 | masking 메모리는 `(DEPRECATED 2026-06-25)` / plaintext는 `RESTORED` 갱신 |

---

## 6. .NET 회신 보강

`docs/GOP_Server_API_v4.9_Review_RESPONSE.md` 하단에 **"POLICY UPDATE 2026-06-25 — v4.10 Phase 1 회귀"** 섹션을 append:

- v4.9 Phase 5 SEC-1 마스킹은 24시간 만에 정책 회귀
- 차장님 결재 인용 + 복호화 경로 부재 근거
- DTO shape 변경 0 / 클라이언트 코드 변경 불필요 재명시
- 보안은 v5.x 별도 차수 (secret API 등) 예고

---

## 7. DoD + 9중 정합 체크리스트

| # | 정합 항목 | 검증 |
|---|---|---|
| 1 | Schema `@field_serializer` 4건 모두 제거 | `grep -n "_mask_user_password" app/schemas/*.py` → 0건 |
| 2 | Schema import 2건 제거 | `grep -n "_password_mask" app/schemas/device.py app/schemas/server.py` → 0건 |
| 3 | example 4건 회귀 | grep `"\\*\\*\\*\\*\\*\\*\\*\\*"` → schemas 파일에서 0건 |
| 4 | 명세 §5.3.x Camera 응답 예시 회귀 | grep `"user_password": "\\*\\*\\*\\*\\*\\*\\*\\*"` → 0건 (명세에서) |
| 5 | DB 평문 유지 (변경 0) | `git diff alembic/versions/` → 0 changes |
| 6 | 요청 schema 변경 0 | `git diff app/schemas/device.py` 상 CameraCreate/LampCreate 미변경 |
| 7 | 검증 5/5 PASS | §4 시나리오 모두 평문 반환 |
| 8 | 메모리 2건 전환 | masking→DEPRECATED, plaintext→RESTORED |
| 9 | .NET 회신 POLICY UPDATE 섹션 append | `docs/GOP_Server_API_v4.9_Review_RESPONSE.md` 갱신 |

**DoD**: 위 9건 전수 PASS + Container healthy + OpenAPI example 평문 확인.

---

## 8. 롤백

- **단일 명령**: `git reset --hard pre-v4.10-phase1`
- 안전점 commit: `31bb478` (직전 작업 = c48c1f6 v4.9 Phase 5 적용 완료 상태)
- 회귀 자체가 v4.9 Phase 5 복원이므로 추가 롤백 절차 불필요
