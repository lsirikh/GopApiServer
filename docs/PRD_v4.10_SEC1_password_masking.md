# PRD v4.10 — SEC-1 user_password 응답 마스킹 (.NET 통합 UI 팀 보안 요청 회신)

**작성일**: 2026-06-24  
**차수**: v4.10 (신설 또는 v4.9 Phase 5 — 차장님 결재)  
**Track**: C (4파일+ + 메모리 정책 변경 + 외부 회신)  
**기준 문서**: `docs/GOP_Server_API_v4.9_Review_Issues.md` SEC-1 (P0 보안)  
**차장님 결재**: "계정 비번 다 보호, 삭제가 아니라 마스킹" (2026-06-24)

---

## 1.1 배경

.NET Ironwall 팀이 발행한 명세 리뷰 문서 `docs/GOP_Server_API_v4.9_Review_Issues.md`의 **SEC-1 (P0 보안)** 지적이 본 차수의 기점이다.

- **지적 내용**: Camera/Lamp/Controller/Sensor/Server 등 장비·계정 응답 DTO가 `user_password` 필드를 **평문 그대로** 직렬화하여 클라이언트(.NET UI, Postman, 로그 파이프라인)로 노출 중.
- **위험도**: HTTPS 종단(브라우저 DevTools, fiddler, 로그 수집기)에서 비번 평문 노출 → OWASP A02:2021 (Cryptographic Failures), CWE-256/319 직접 위반.
- **현행 정책 충돌**: 메모리 `feedback_password_plaintext_policy.md`는 "Device/Server 계정·비번 응답에 평문 유지"였으나, 이는 **백엔드 장비 접속 편의** 명목의 임시 정책으로, 외부 감사·보안 검토 시 즉시 결함으로 판정될 사항이었다.

## 1.2 차장님 결재 (2026-06-24)

> **"계정 비번 다 보호, 삭제가 아니라 마스킹"** — 이기호 차장, 2026-06-24

결재 핵심 3축:

| 항목 | 결정 | 사유 |
|------|------|------|
| **응답 평문 노출** | **차단 (마스킹)** | SEC-1 P0 수용, 보안 감사 통과 |
| **DTO 필드 제거** | **금지 (필드 유지)** | .NET 클라이언트 100% 호환성 보장 |
| **마스킹 형식** | `"********"` (8자 고정) | 길이 추정 불가 + 단순성 |
| **DB 평문 저장** | **유지** | 백엔드 장비 SSH/HTTP 접속용, 운영 필수 |

→ **정책 전환**: 평문 응답 정책 폐기, **응답 마스킹 + DB 평문 유지** 이원화로 갱신.

## 1.3 메모리 정책 갱신

- `MEMORY.md`의 `feedback_password_plaintext_policy.md` 항목을 **마스킹 정책**으로 갱신 (본 차수 Phase 종료 직후).
- 신규 메모리 키: `feedback_password_masking_policy.md` — "응답 마스킹 `********`, DB 평문 유지, DTO shape 불변".
- 구 정책 메모리는 **deprecated 표기 후 보존** (의사결정 이력 추적).

## 1.4 적용 범위 (In-Scope)

### 1.4.1 Response 클래스 (7종)

| # | 도메인 | 클래스 | 위치 (예상) |
|---|--------|--------|-------------|
| 1 | Camera | `CameraResponse` | `app/schemas/camera.py` |
| 2 | Lamp | `LampResponse` | `app/schemas/lamp.py` |
| 3 | Controller | `ControllerResponse` | `app/schemas/controller.py` |
| 4 | Sensor | `SensorResponse` | `app/schemas/sensor.py` |
| 5 | Server | `ServerResponse` | `app/schemas/server.py` |
| 6 | Server | `ServerAccountResponse` (있을 시) | `app/schemas/server.py` |
| 7 | 공통 | 목록/상세 응답 wrapper (7종 포함 시) | 각 라우터 |

→ Pydantic `field_serializer` 또는 `@computed_field`로 직렬화 시점 마스킹 (DB→ORM 매핑은 평문 유지).

### 1.4.2 명세 문서

- `GOP_Restful_Api_연동설계.md` **§9.2.2 로그인 응답 예시** JSON 블록 `user_password` 값을 `"********"`로 교체.
- 본 마스터 파일은 `c:\workspace_python\api-test-server\` 추적본만 수정 (사본 5곳은 후속 동기화 잡으로 일괄 처리).

## 1.5 적용 범위 외 (Out-of-Scope)

- **DB 스키마 변경 없음** — `users.user_password`, `cameras.user_password` 등 평문 컬럼 유지.
- **인증/세션/RBAC 흐름 변경 없음** — 본 차수는 **응답 직렬화 계층만** 손댄다.
- **bcrypt/argon2 해시 도입은 별도 차수** (v5.x 후보, 현재 잔여작업에 등록).
- **Request 측 `user_password` 처리 변경 없음** — PUT/POST 입력은 평문 그대로 수신.

## 1.6 호환성 보증

- **DTO shape 불변**: `user_password` 필드 자체는 응답 JSON에 그대로 존재, 값만 `"********"`.
- **.NET DataContract 영향 0** — 역직렬화 시 `string` 그대로 매핑, 별도 분기 불필요.
- **OpenAPI 스키마 영향 0** — 타입/필수 여부 동일.

## 1.7 안전점

- **Pre-checkpoint**: `pre-v4.10-phase1` (Phase 1 진입 직전 신설 예정, 본 PRD 승인 후 첫 커밋 직전 태깅).
- 회복 시나리오: 마스킹 직렬화 회귀 발견 시 `git reset --hard pre-v4.10-phase1`로 즉시 원복.

## 1.8 분량 추정 (Track C)

| Sub-Phase | 작업 | 추정 |
|-----------|------|------|
| P1 | TDD: 7 Response 클래스 마스킹 테스트 작성 (Red) | 25m |
| P2 | Pydantic serializer 구현 (Green) | 20m |
| P3 | 명세 §9.2.2 예시 교체 + 사본 5곳 검증 | 15m |
| P4 | 회귀 테스트(전체) + .NET DTO shape 검증 | 20m |
| P5 | 메모리 정책 키 갱신 + session-context + PR | 20m |
| **합계** | | **~1.5h** |

→ Track C 단일 일자(2026-06-24) 내 마감 가능, **하루 1 차수 원칙** 준수 (v4.10 단일 차수로 묶음).


---

## 0. 요약 (두괄식)

| 항목 | 결정 |
|---|---|
| 마스킹 방식 | **Pydantic v2 `@field_serializer`** — 응답 직렬화 시점에만 변환, 모델/DB는 평문 유지 |
| 마스킹 토큰 | `PASSWORD_MASK = "********"` (8자 고정, ASCII 별표) |
| 변환 규칙 | `None` → `None` 유지, 평문 문자열 → `"********"` 변환 |
| 공통 헬퍼 위치 | `app/schemas/_password_mask.py` **신설** (언더스코어 prefix = 내부 헬퍼) |
| 적용 응답 클래스 수 | **5개 + 1개 example 수정** (Controller/Sensor는 `user_password` 필드 자체가 없어 적용 대상 아님 — 명세 정정) |
| 비적용 (의도된 평문 유지) | DB 컬럼 / Create·Update 요청 schema / 백엔드 장비 접속(NVR·Speaker 등) / 시드 데이터 |

> **명세 정정**: `app/schemas/device.py` 코드 검증 결과 `ControllerResponse(L262)`·`SensorResponse(L364)`는 `user_password` 필드 미보유. 본 PRD에서 두 클래스는 적용 범위에서 제외하고, 실제 후보를 **5개 Response 클래스**로 확정한다.

---

## 1. 공통 헬퍼 설계

### 1.1 파일: `app/schemas/_password_mask.py` (신설)

```python
"""Password masking helper for Response schemas (PRD v4.10 §2).

- DB / Create·Update 요청 / 모델은 평문을 유지한다.
- 본 모듈은 **Response 직렬화 시점**에만 평문을 마스크로 치환한다.
- None 은 None 으로 그대로 흘려보낸다 (필드 미설정과 마스킹된 평문의 구분 유지).
"""
from typing import Optional

PASSWORD_MASK: str = "********"  # 8자 고정. 길이 노출 방지.


def mask_password_serializer(value: Optional[str]) -> Optional[str]:
    """Pydantic v2 field_serializer 본체.

    Args:
        value: ORM/DB에서 읽어온 평문 비밀번호 또는 None.
    Returns:
        None 그대로 / 평문이면 PASSWORD_MASK.
    """
    if value is None:
        return None
    return PASSWORD_MASK
```

### 1.2 사용 패턴 (Pydantic v2 `@field_serializer`)

```python
from pydantic import field_serializer
from app.schemas._password_mask import mask_password_serializer

class CameraResponse(BaseModel):
    ...
    user_password: Optional[str] = Field(None, description="접속 비밀번호 (응답 시 마스킹)")

    @field_serializer("user_password")
    def _mask_user_password(self, v: Optional[str]) -> Optional[str]:
        return mask_password_serializer(v)
```

- `from_attributes=True` 와 호환 — ORM → schema 변환 시 평문이 들어오고, JSON 직렬화 단계에서 마스킹된다.
- `model_dump()` / `.model_dump_json()` / FastAPI `response_model` 경로 모두에서 동일 동작.

---

## 2. 적용 위치 매핑 (검증된 라인 기준)

### 2.1 적용 대상 — Response 클래스 5개

| # | 클래스 | 파일 | 클래스 선언 라인 | `user_password` 필드 라인 | 비고 |
|---|---|---|---:|---:|---|
| 1 | `CameraResponse` | `app/schemas/device.py` | **L478** | **L503** | v4.4 Phase 5 노출 복원 주석 동반 |
| 2 | `CameraNestedResponse` | `app/schemas/device.py` | **L545** | **L601** | 명세 §554 "user_password 제외" 주석은 v4.4 이전 정책 — **현행 코드는 노출 중**, 본 PRD에서 마스킹 적용 |
| 3 | `LampResponse` | `app/schemas/device.py` | **L1032** | **L1054** | v4.4 Phase 5 노출 복원, `LampNestedResponse(L1071)`는 `user_password` 미노출 — 제외 |
| 4 | `ServerResponse` | `app/schemas/server.py` | **L133** | **L143** | json_schema_extra example(L163)의 `"password123"` → `"********"` 동시 갱신 |
| 5 | `ServerNestedResponse` | `app/schemas/server.py` | **L176** | **L191** | example(L209) `"password123"` → `"********"` 동시 갱신 |

### 2.2 부수 영향 — example 데이터만 수정

| 위치 | 라인 | 변경 |
|---|---:|---|
| `ServerCategorySummary.json_schema_extra` | `app/schemas/server.py:262` | `"user_password": "password123"` → `"user_password": "********"` (Swagger 노출 표본 일관성) |
| `LampResponse.user_password` example | `app/schemas/device.py:1054` | `"example": "lamp1234"` → `"example": "********"` |
| `CameraNestedResponse` 클래스 주석 | `app/schemas/device.py:554` | "user_password 제외" → "user_password 마스킹 노출 (PRD v4.10 §2)" 갱신 |

### 2.3 명세서 (Swagger / md) 자리표시자

- `GOP_Restful_Api_연동설계.md` **§9.2.2 (L14107~14115)** `/api/auth/login` Request example
  - `"login_id": "admin"` → `"login_id": "<your_login_id>"`
  - `"password": "admin123"` → `"password": "<your_password>"`
  - 우측 주석 `//현재 기본 아이디/비번` 제거

---

## 3. 비적용 (의도된 평문 유지) — 위배 금지 영역

| 영역 | 사유 |
|---|---|
| DB 컬럼 (`cameras.user_password`, `servers.user_password`, `lamps.user_password`) | 백엔드 → NVR/Speaker/Lamp 장비 접속 시 평문 필요. 모델·마이그레이션 변경 없음 |
| `CameraCreate(L443)`, `CameraUpdate(L580)`, `LampCreate`, `LampUpdate(L1019)`, `ServerCreate`, `ServerUpdate(L117)` | POST/PUT/PATCH 요청은 평문 입력을 그대로 받아 DB에 저장 |
| 백엔드 내부 서비스(`device_service`, `nats_publisher` 등) | 평문 사용 가능 — 응답 schema 통과 없이 사용 |
| 시드 데이터 (`data/seed/*.json`, 정적 카테고리/장비 seed) | Static seed 정책(메모리 `feedback_static_vs_runtime_seed`) — 평문 유지 |
| `audit_service.SENSITIVE_FIELDS (L13)` | **이미 감사 로그 단계에서 redact 수행 중**. 응답 직렬화에는 미작용 → 본 PRD가 보완 |

---

## 4. 적용 라인 매핑 표 (실행 체크리스트)

| Step | 파일 | 액션 | 라인 |
|---|---|---|---:|
| S1 | `app/schemas/_password_mask.py` | **신규 생성** — `PASSWORD_MASK`, `mask_password_serializer` 정의 | (신설) |
| S2 | `app/schemas/device.py` | `CameraResponse`에 `@field_serializer("user_password")` 추가 | L503 이후 |
| S3 | `app/schemas/device.py` | `CameraNestedResponse`에 동일 serializer 추가 + 클래스 docstring 갱신 | L545~601 |
| S4 | `app/schemas/device.py` | `LampResponse`에 동일 serializer + example 값 `********`로 갱신 | L1032~1054 |
| S5 | `app/schemas/server.py` | `ServerResponse` serializer 추가 + example 갱신 | L133~163 |
| S6 | `app/schemas/server.py` | `ServerNestedResponse` serializer 추가 + example 갱신 | L176~213 |
| S7 | `app/schemas/server.py` | `ServerCategorySummary.json_schema_extra` example 평문 치환 | L262 |
| S8 | `GOP_Restful_Api_연동설계.md` | §9.2.2 로그인 예시 자리표시자 치환 | L14111~14114 |
| S9 | `tests/` | Response 직렬화 단위테스트 — `should_mask_password_when_response_serialized` (`None` 유지 / 평문→`********` / DB 평문 무손상) | (신규) |

---

## 5. 위험·검토 사항

1. **CameraNestedResponse 노출 정책 변경** — 기존 주석은 "민감정보 제외"였으나 현행 코드는 노출 중. 본 PRD가 "마스킹 노출"로 정책을 공식화하며 코드/주석 정합을 맞춘다.
2. **`from_attributes=True` + `field_serializer` 호환** — Pydantic v2.x에서 검증 완료된 표준 패턴. ORM 객체 직접 주입 경로(`Model.model_validate(orm_obj)`)에서도 직렬화 단계는 동일하게 작동.
3. **Audit log 이중방어** — `audit_service.SENSITIVE_FIELDS`는 변경 없음. 응답 schema 마스킹은 별도 계층으로, 두 방어선이 독립 작동.
4. **테스트 격리** — 평문이 DB에 그대로 보존되는지(역회복) 확인하는 통합테스트 1건 필수: `should_keep_plaintext_in_db_when_response_masked`.
5. **하위호환** — Response 키 구조는 불변(`user_password` 키 유지), 값만 마스킹 → 클라이언트(Central UI / 통합상황도) Breaking change 없음.


---

# 3. 검증 시나리오 + 9중 정합 절차 + 위험

## 3.1 검증 시나리오 8건 (PASS/FAIL 매트릭스)

본 차수(v4.10 Phase 1)의 변경은 "응답 스키마에서 `user_password` 필드를 마스킹 문자열 `"********"`로 치환" 하는 단일 행위에 한정된다. 따라서 검증 시나리오는 **응답 경로 전수 + DB 평문 보존 + Swagger example** 3축으로 구성한다.

| # | 시나리오 | 입력 / 호출 | 기대 결과 | 판정 기준 |
|---|---------|------------|----------|----------|
| 1 | Camera 목록 응답 마스킹 | `GET /api/devices/cameras` (admin/admin123) | `items[*].user_password == "********"` | 모든 행에 대해 마스킹 적용. 평문 1건이라도 노출 시 FAIL |
| 2 | Camera 단일 응답 마스킹 | `GET /api/devices/cameras/{id}` (시드 카메라 ID) | `user_password == "********"` | 단일 객체 응답 동일 정책 |
| 3 | Camera POST 직후 응답 마스킹 | `POST /api/devices/cameras` body에 `user_password="real_pw"` 포함 | 응답 body `user_password == "********"`, DB는 `real_pw` 저장 | 응답 마스킹 ∧ DB 평문 보존 동시 만족 |
| 4 | Camera PATCH 응답 마스킹 | `PATCH /api/devices/cameras/{id}` body에 `user_password="changed_pw"` | 응답 `user_password == "********"`, DB는 `changed_pw` | 변경 반영 확인 + 응답 마스킹 |
| 5 | Lamp 단일 응답 마스킹 | `GET /api/devices/lamps/{id}` (시드 Lamp) | `user_password == "********"` (시드값이 NULL이면 N/A로 처리) | Camera와 동일 정책 일관성 확인 |
| 6 | Server 단일 응답 마스킹 | `GET /api/servers/{id}` | 현재 시드 `user_password = None` → 응답 `null` 그대로. 시드 데이터 변경 후 평문 시드 시 `"********"` | 시드 데이터에 따라 N/A 또는 PASS. 시드 변경 시 재검증 |
| 7 | DB 직접 조회로 평문 보존 확인 | `SELECT user_password FROM cameras WHERE id=X` (psql 또는 컨테이너 진입) | 평문 그대로 저장 (`real_pw`, `changed_pw` 등) | DB에 `"********"` 가 저장되면 절대 FAIL — 저장 경로 오염 의미 |
| 8 | Swagger OpenAPI example 마스킹 | `GET /openapi.json` 또는 Swagger UI Camera/Lamp/Server 스키마 example | example 값이 `"********"` | 시드 평문이 example로 새어나오면 FAIL. example=마스킹 고정 |

**PASS 기준**: 1~5, 7, 8 모두 PASS + 6은 PASS 또는 N/A 명시. 단 1건이라도 FAIL 시 차수 미완(rollback 또는 hotfix 결정).

**보조 검증 항목**:
- pytest 기존 통과 케이스 회귀 0건 (응답 스키마 변경 후 기존 `assert user_password == ...` 패턴 테스트 영향 분석 필수)
- audit log의 `SENSITIVE_FIELDS` 마스킹은 **별도 경로** — 본 차수 변경으로 audit 로그가 영향받으면 안 됨 (분리 검증)

## 3.2 9중 정합 절차

본 프로젝트의 v4.x 차수는 단일 코드 변경이 **9개 레이어 모두 동기화**되어야 차수 완료로 간주한다. v4.10 Phase 1의 9중 정합 체크리스트는 다음과 같다.

| 레이어 | 점검 대상 | 검증 명령/방법 | 완료 조건 |
|-------|----------|---------------|----------|
| 1. 코드 | `app/schemas/*.py`, response_model 또는 serializer | grep `user_password`, 마스킹 처리 위치 확인 | 응답 직렬화 시 `"********"` 치환 1개소 집중 (DRY) |
| 2. Swagger | `/openapi.json` example | `curl /openapi.json | jq` | Camera/Lamp/Server 스키마 example 모두 `"********"` |
| 3. 명세서 | `GOP_Restful_Api_연동설계.md` (마스터 경로) | 문서 내 응답 예시 갱신 | `user_password: "********"` 표기 통일 |
| 4. DB | `cameras.user_password` 컬럼 평문 보존 | `psql -c "SELECT user_password FROM cameras LIMIT 5"` | 평문 그대로. 마스킹 문자열 저장 0건 |
| 5. Image | Docker 이미지 재빌드 후 응답 검증 | `docker build` + 컨테이너 응답 호출 | 빌드 후 동일 PASS |
| 6. Container | 실행 중 컨테이너 응답 | `docker exec` 또는 외부 호출 | 빌드 산출물과 일치 |
| 7. CHANGELOG | `CHANGELOG.md` v4.10-phase1 항목 | 파일 갱신 | 변경 사유/범위/롤백 안전점 명시 |
| 8. session-context | `docs/memory/session-context.md` | Phase 진행 상황 기록 | 차수/Phase/안전점 갱신 |
| 9. Gitea | 원격 push 및 PR/이슈 링크 | `git push` + 원격 확인 | 로컬과 원격 SHA 일치 |

**정합 실패 패턴**: 과거 v4.x 차수에서 "코드는 됐는데 Swagger example이 평문" 또는 "DB에 마스킹 문자열이 저장됨" 같은 정합 깨짐이 반복되었으므로, 본 차수에서는 1~9 모두 통과 후에만 차수 종료를 선언한다.

## 3.3 위험 (Risk) 및 완화책

### 위험 1. .NET 클라이언트(Central UI / Ironwall.Dotnet) 호환성 깨짐
- **시나리오**: .NET 측이 카메라 일반 GET 응답에서 `user_password` 평문을 읽어 RTSP/ONVIF 연결에 직접 사용 중이라면, 응답이 `"********"`로 바뀌는 순간 연결 실패 가능.
- **완화**: 
  - 회신 문서(`docs/PRD_v4.10_Phase1_Response_Masking.md` 또는 동등)에 **"GET 응답의 `user_password`는 마스킹됩니다. 평문 자격증명이 필요한 경로는 별도 엔드포인트 또는 서버측 프록시로 분리하십시오"** 명시.
  - DTO 호환성: 필드 자체는 유지(`string`), 값만 마스킹 → 역직렬화 깨짐 없음 강조.
  - .NET 팀에 사전 통보 + 회귀 영향 사전 점검 (외부 IP 환경 502 이슈와 별개로 본 변경의 영향만 격리 확인).

### 위험 2. 시드 데이터 평문이 OpenAPI example로 노출
- **시나리오**: FastAPI가 시드 데이터 또는 Pydantic 기본값을 그대로 OpenAPI example로 출력할 경우, 시드의 평문 비밀번호가 `/openapi.json`에 노출.
- **완화**: 스키마 정의에서 `user_password` 필드의 `Field(..., example="********")` 또는 `model_config`에 example 명시. 시드 값 기반 example 자동 생성 경로 차단. 시나리오 #8에서 직접 검증.

### 위험 3. audit log 마스킹 정책과 응답 마스킹 정책 충돌
- **현황**: audit log의 `SENSITIVE_FIELDS`는 이미 마스킹 적용 중. 응답 마스킹은 **신규** 추가 정책.
- **위험**: 두 경로가 한 곳에서 처리되도록 묶이면 향후 변경 시 한쪽 망가짐.
- **완화**: 
  - audit 경로(`app/audit/*` 또는 미들웨어)와 응답 직렬화 경로(`app/schemas/*` 또는 response serializer)를 **물리적으로 분리** 유지.
  - 마스킹 상수(`MASKED_VALUE = "********"`)는 공유 가능하나, 적용 지점은 독립.
  - 코드 리뷰 체크리스트에 "응답 마스킹과 audit 마스킹은 분리된 경로에서 처리되는가?" 항목 추가.

### 위험 4. 시드 데이터 변경으로 시나리오 #6 결과 변동
- 현재 Server 시드 `user_password = None` → 마스킹 결과 `null`. 향후 시드에 평문이 들어오면 `"********"` 반환되어야 함. 시나리오 #6은 시드 변경 시 **재실행 의무**로 명시.

## 3.4 롤백 (Rollback)

- **안전점**: `pre-v4.10-phase1` 태그(또는 동등 브랜치 포인터)를 차수 시작 직전 커밋에 부여.
- **롤백 절차**: 단일 `git reset --hard pre-v4.10-phase1` 으로 코드 원복. DB는 변경 없음(평문 그대로 저장되었으므로 데이터 손상 없음). Swagger/CHANGELOG/session-context는 코드 reset에 따라 자동 일관.
- **롤백 후 검증**: 8개 시나리오 중 1~5, 8 만 다시 평문 반환 상태로 회귀했는지 확인 → 회귀 정상이면 롤백 완료.
- **롤백 트리거 조건**: 
  - 시나리오 7 FAIL (DB에 마스킹 저장 = 데이터 오염): 즉시 롤백.
  - .NET 호환성 이슈로 운영 중단 보고 시: 회신 문서 보강 후 재배포 또는 롤백.
  - 9중 정합 중 4개(DB) 또는 1개(코드) FAIL: 즉시 롤백.

본 절은 v4.10 Phase 1 "응답 스키마 user_password 마스킹"의 검증·정합·위험·롤백을 단일 차수 내에서 닫는 절차를 정의한다.


---

## 4. .NET 회신 계획 + DoD + 차수 종결

### 4.1 .NET 회신 문서 (한 줄 요약)

- **문서명**: `docs/GOP_Server_API_v4.9_Review_RESPONSE.md` (또는 `docs/SEC1_RESPONSE.md`)
- **수신**: GOP Central / Ironwall.Dotnet 팀 (C# 검토 회신본 작성자)
- **발신**: API Test Server 팀 (이기호 차장)
- **버전**: v4.10 종결 직후 작성, Gitea 푸시 동시 공유

### 4.2 회신 핵심 메시지 (5줄 요약, 두괄식)

| # | 메시지 | 상세 |
|---|--------|------|
| 1 | **SEC-1 적용 완료** | 모든 Response DTO에서 `user_password` 평문 노출 차단. 마스킹 토큰 `"********"` 8자 고정 적용 |
| 2 | **DTO shape 변경 없음** | 필드명/타입/존재 여부 모두 유지. 단 응답 직렬화 단계에서 값만 치환 |
| 3 | **.NET 측 코드 변경 불필요** | 기존 `UserPassword` 역직렬화 그대로 작동. 단, 비번 표시 UI에서 `"********"` 그대로 표시되거나 빈 처리 권장 |
| 4 | **DB 평문 유지** | 백엔드 장비 접속용(Camera/NVR/Server) 평문 보존. 응답 단계만 마스킹. v4.x 범위 외로 정책 고정 |
| 5 | **로그인 예시 자리표시자 치환** | 명세 §9.2.2의 실제 자격증명 노출 → `"<USERNAME>"` / `"<PASSWORD>"` 자리표시자로 치환 완료 |

### 4.3 다른 P0 처리 방침 (별도 차수 권고)

| Finding | 권고 차수 | 사유 |
|---------|----------|------|
| **ENV-1** (환경/Secret 분리) | v4.11 | 인프라 변경 동반, 별도 결재 필요 |
| **AUTH-1** (토큰 정책) | v4.12 | OIDC/JWT 정책 결정 선행 |
| **AUTH-2** (RBAC 강화) | v4.13 | RBAC 결재 5건 중 1건과 연계 |

> v4.10은 SEC-1 단일 집중. "하루 1 차수 묶음" 원칙 준수 — 다른 P0 끼워넣기 절대 금지.

### 4.4 DoD 체크리스트 (10건 — 전수 통과 시 차수 종결)

```
[ ] 1. _password_mask.py 신설 + 7 Response 적용
[ ] 2. 8 검증 시나리오 PASS (단건/리스트/상세/검색/필터/페이징/에러/타입)
[ ] 3. Swagger OpenAPI example "********" 확인
[ ] 4. 명세 §9.2.2 자리표시자 치환 (<USERNAME>/<PASSWORD>)
[ ] 5. 명세 v4.10 행 + CHANGELOG + session-context 갱신
[ ] 6. Image rebuild + Container force-recreate (--force-recreate)
[ ] 7. DB 평문 유지 검증 (장비 접속 정상)
[ ] 8. 메모리 feedback_password_plaintext_policy 정책 갱신
[ ] 9. .NET 회신 문서 작성 (RESPONSE.md)
[ ] 10. Gitea push + 안전점(tag) push
```

### 4.5 차수 종결 시점

- **조건**: 위 10건 **모두 체크** + code-review GREEN + 회귀 테스트 PASS
- **종결 액션**:
  1. `docs/memory/session-context.md`에 v4.10 종결 라인 추가
  2. Git tag `v4.10-sec1-password-mask` 부여 + Gitea push
  3. v4.11 착수 결재 요청 (ENV-1 우선 검토)
- **종결 후 금지 사항**: v4.10 범위로 ENV-1/AUTH-1/AUTH-2 끼워넣기 금지 (1일 1차수 원칙)
- **회신 발송 타이밍**: 차수 종결 직후 Gitea push와 동시 .NET 팀 공유, 회신본 URL 함께 전달

### 4.6 리스크 및 롤백 플랜

- **롤백 트리거**: 검증 시나리오 1건이라도 FAIL, 또는 .NET 측 역직렬화 오류 보고
- **롤백 방법**: `_password_mask.py` 미적용 커밋으로 되돌리기 (구조적 변경만 단일 커밋 분리되어 있어 안전)
- **모니터링**: 종결 후 24h, .NET Central UI 로그인/장비 접속 정상 여부 추적


---
