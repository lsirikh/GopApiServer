# PRD: GOP_Restful_Api 연동설계 v4.6 — Bulk API Post-Mortem (잔존 GAP 12건 정리)

> **차수**: v4.5 → v4.6
> **작성자**: 이기호 차장
> **작성일**: 2026-06-19
> **선행 산출물**: `docs/workflow_health_v46/A~J.md` (Workflow w/r91vn26e 9 agent + synthesis health check), `docs/PRD_BulkAPI_Spec_Sync_v4.4.md` (v4.4 산출물)
> **롤백 태그 후보**: pre-v46 (적용 직전 HEAD = de15ba0)
> **차수 결정 근거**: v4.5와 같은 권역(Bulk API + 매니저 통합 사전 정리), 같은 주, 매니저 통합 시작 전 정리. v4.7 분리 시 일정 인플레이션.

---

## §1. 개요

### 1.1 두괄식 — 왜 v4.6이 필요한가

v4.5 PR-A/B/C/D 적용으로 Bulk API의 명세-구현-Swagger 셋이 정합화됐으나, 매니저 4종(GIS/VMS/NVR/Speaker) 통합 시작 전 종합 health check(Workflow w/r91vn26e, 9 agent + synthesis) 결과 **잔존 GAP 12건**이 발견됐다. 그중 **P0 4건**(JWT 시크릿 고정값, user_password 평문 노출, CORS 와일드카드, .NET 사본 stale)은 매니저 통합 차단 위험. **P1 5건**(PR-B 같은 request 중복, pytest 11실패, 단건 14건 response_model, dead code, AUTH_MODE public 디폴트)은 통합 안전성에 직접 영향. **P2 3건**(§7.5.7 번호 중복, JWT 회전 부재, PRD git 추적)은 후속 처리 가능. v4.6은 P0+P1 9건을 한 차수로 일괄 정리하여 매니저 통합 진입 안전 상태를 확보한다.

### 1.2 영향 컴포넌트

| # | 컴포넌트 | v4.6 영향 | FR |
|---|---------|----------|---|
| C1 | **DBApi (api-test-server)** | 코드 변경 대다수 — JWT/CORS/user_password/PR-B 보강/단건 response_model/dead code | FR-1~3, 5, 7, 8, 9 |
| C2 | **db_monitor / NATS** | 무영향 (Agent D: PR-A 0건 ConfigLog는 `gop_sync` 채널 무관, statement-level 정합) | regression 가드 추가 |
| C3 | **Central UI (Ironwall)** | user_password 응답 마스킹 변경 시 디버그 화면 영향 | FR-2 |
| C4 | **GIS Manager** | Camera/DeviceGroup 정합 | FR-2, 4, 5 |
| C5 | **VMS Manager** | Camera bulk + 단건 정합 | FR-2, 5, 7 |
| C6 | **NVRManager** | Lamp Enum + .NET 사본 동기화 | FR-2, 4, 7 |
| C7 | **Speaker Manager** | Speaker bulk + 단건 | FR-2, 5, 7 |

### 1.3 일정

| 단계 | 산출물 | 기한 | 책임 |
|------|--------|------|------|
| **본 PRD 결재** | `PRD_BulkAPI_PostMortem_v4.6.md` | 2026-06-19 | 이기호 차장 |
| **P0 4건 처리** | FR-1, 2, 3, 4 적용 | 2026-06-19 (당일) | DBApi 담당 |
| **P1 5건 처리** | FR-5, 6, 7, 8, 9 적용 | 2026-06-20 | DBApi 담당 |
| **P2 3건 처리** | FR-10, 11, 12 적용 | 2026-06-23 (별도 미니 차수 가능) | DBApi 담당 |
| **명세 v4.6 갱신 + Image rebuild** | `GOP_Restful_Api_연동설계.md` v4.6 + Docker Image | 2026-06-23 | DBApi 담당 |
| **매니저 통합 시작** | C4~C7 동시 진입 | 2026-06-23~ | 매니저 담당 |

### 1.4 v4.5와의 관계

v4.5 (HEAD=de15ba0, 2026-06-18) 작업 완료 후 발견된 잔존 위험을 v4.6 (이 PRD)으로 처리. v4.5의 PR-A(0건 ConfigLog)/PR-B(분류 로직)/PR-C(Lamp Enum)/PR-D(response_model)는 변경 없이 유지하며, v4.6은 그 **이후 발견된** 9 차원 점검 결과를 반영.

---

## §2. 요구사항

### 2.1 Functional Requirements (12건)

#### P0 (즉시, 매니저 통합 차단 위험) — 4건

| # | 제목 | 설명 |
|---|---|---|
| **FR-1** | JWT_SECRET_KEY 환경 분리 + 랜덤화 | `.env` / `app/config.py:22` / `docker-compose.yml:34` 세 곳 모두 `your-secret-key-change-in-production-please-use-strong-random-key` 리터럴 — 운영 토큰 위조 가능. `os.urandom(32)` 헥스 + 환경별 분리(dev/staging/prod) + Pydantic validator로 디폴트 거부 |
| **FR-2** | user_password 응답 마스킹 | `LampResponse`(device.py:1046), `ServerResponse`(server.py:78/117/143/190), `Lamp Create/Update`(device.py:979/1012)가 `user_password: Optional[str]` 평문 노출. `LampResponseSecure`/`ServerResponseSecure` 신설하고 라우터 응답 타입 교체 |
| **FR-3** | CORS 화이트리스트 | `app/main.py:550` `allow_origins=["*"]` + `allow_methods=["*"]` + `allow_headers=["*"]` → 매니저 4종 도메인만 명시(`settings.CORS_ORIGINS`), credentials 허용 + 메서드/헤더 한정 |
| **FR-4** | .NET 사본 4곳 동기화 안내 | (1) `Ironwall.Dotnet.Libraries\Docs\` v4.2 stale (Critical, NVR/VMS 공통 라이브러리, 7개월 갭) → v4.5 동기화 (2) `Dotnet.Rtsp.Viewer.Ui\Docs\` v4.3 (통합상황도 VMS UI, High) → v4.5 동기화 (3) `Dotnet.Monitoring.Solution\Docs\` v1.6 (Medium, DB 동기화 위주) → v4.5 동기화. 가이드 문서(`docs/v45_sync_guide.md`) 작성하여 매니저 팀에 메일 전송 |

#### P1 (차수 내, 통합 안전 영향) — 5건

| # | 제목 | 설명 |
|---|---|---|
| **FR-5** | PR-B 한계 보강 — 같은 request 내 중복 device_id 분류 | v4.5 PR-B의 `skipped_config_ids`는 DB 선존 매핑만 잡고 같은 페이로드 중복은 N건 모두 INSERT 시도 → DB UNIQUE 충돌 시 `failed_items`로 추락. 매니저가 UI에서 같은 카메라 두 번 토글 후 일괄전송 시 UX 혼란. in-memory `seen_in_request: set[int]` 추적으로 사전 분류 (신규 응답 필드 `skipped_in_request_ids` 또는 기존 `skipped_config_ids`에 통합) |
| **FR-6** | pytest 11건 envelope 정합화 | Agent A 결과 — 9건 P3 (테스트 코드 envelope key 갱신만, `camera_ids/speaker_ids/lamp_ids` → 공통 `config_ids`), 2건 P2 (lamps `skip_duplicates`/cameras `skip_duplicates` — 멱등성 코드 검토 필요). FR-5 적용 후 자동 통과 |
| **FR-7** | EventMapping 단건 CRUD 14건 response_model 명시 | v4.5 PR-D가 bulk 6건만 정정. Camera/Speaker/Lamp 각 단건 GET 목록/단건 조회/POST/PATCH/PUT/DELETE/독립 GET 등 14건이 여전히 `response_model=dict` → OpenAPI `additionalProperties:true`. 매니저가 단건 API 사용 시 타입 추정 불가. 모두 `ApiSingleResponse[T]` 또는 `ApiResponse[T]` (페이지네이션) 명시 |
| **FR-8** | `fn_notify_gop_sync()` row-level EventMapping 분기 제거 | `db_triggers.py:98~108` ELSIF 블록 (`event_mapping_cameras/speakers/lamps`)은 v4.3 마이그레이션에서 statement-level로 교체됐으나 잔존 — 운영자가 마이그레이션 되돌리면 SYNC_EVENT_MAPPING 이중 발행 위험 |
| **FR-9** | AUTH_MODE 기본값 token 권고 + 환경별 분기 | `.env:2` `AUTH_MODE=public` 디폴트 → 토큰 없으면 `None` 반환, 통합 환경에 그대로 가면 무인증 호출 가능. dev=public, staging=token, prod=token 권고 + `.env.example` 명시 |

#### P2 (후속 처리 가능) — 3건

| # | 제목 | 설명 |
|---|---|---|
| **FR-10** | §7.5.7 번호 중복 재채번 | `GOP_Restful_Api_연동설계.md` L12051 `7.5.7 FK 정책 및 CASCADE`와 L12073 `7.5.7 MappingLamp 전체 목록 조회 (독립)` 같은 번호. 후자를 §7.5.9 재채번, 본 차수 §7.5.9/10을 §7.5.10/11 시프트. 부록 §12.1 표 동기화 |
| **FR-11** | JWT 토큰 회전 정책 (jti 블랙리스트) | Access 24h/Refresh 7d지만 jti 블랙리스트/회수 로직 없음 → 로그아웃 무효. Redis 또는 DB 테이블에 만료 토큰 jti 저장 + auth.py 검증 로직 추가. **공수 4.5h로 v4.7로 분리 가능** |
| **FR-12** | docs/PRD_*.md git 추적 정책 | `.gitignore`에 `docs/` 전체 포함 — PC 손상 시 PRD 산출물 손실. `!docs/PRD_*.md` 예외 추가하여 PRD만 git 추적 (시뮬레이션/workflow 산출물은 그대로 외부) |

### 2.2 Non-Functional Requirements

| # | 제목 | 설명 |
|---|---|---|
| **NFR-1** | 성능 | FR-5 in-memory 추적은 O(N) 추가, 100건 제약이므로 무영향 |
| **NFR-2** | 가용성 | FR-1 JWT 시크릿 변경 시 기존 토큰 전수 invalidate → 매니저 사전 통지 + 재로그인 강제 |
| **NFR-3** | 보안 | OWASP Top 10 기준: A02 (시크릿 노출), A05 (보안 설정 오류), A07 (식별 및 인증 실패) 동시 정정 |
| **NFR-4** | 매니저 호환성 | FR-5의 응답 envelope 신규 필드는 backward-compatible (추가 키). 매니저 디코더 strict 모드 시 lenient로 설정 안내 |
| **NFR-5** | 회귀 보장 | pytest 70/70 (기존 66 + 신규 4) + 시뮬레이션 19+α 시나리오 100% 통과 |

---

## §3. API 명세 (변경 영역)

### 3.1 변경되는 엔드포인트 인벤토리

| 영역 | 변경 종류 | 대상 |
|---|---|---|
| **EventMapping 단건 CRUD 14건 (G7/FR-7)** | `response_model=dict` → `ApiSingleResponse[T]` / `ApiResponse[T]` | Camera/Speaker/Lamp 각 7건 (목록 GET / 단건 GET / POST / PATCH / PUT / DELETE / 독립 GET) — 단 동작 무변경 |
| **EventMapping bulk create 3건 (G5/FR-5)** | 응답 envelope에 분류 보강 | `bulk_create_event_mapping_cameras/speakers/lamps` — 같은 request 내 중복 처리 |
| **모든 인증 라우터 (G9/FR-9)** | AUTH_MODE 권고 변경 | 동작 변경 없음, 환경 설정만 |
| **모든 라우터 (G3/FR-3)** | CORS 헤더 화이트리스트 | 동작 변경 없음 |
| **Lamp 응답 라우터 + Server 응답 라우터 (G2/FR-2)** | 응답 스키마 `Secure` 변형 | user_password 필드 제거 |

### 3.2 응답 envelope 정합 (PR-D 결과 + 단건 적용)

```json
// 200 OK (모든 7+14=21 엔드포인트 통일)
{
  "success": true,
  "message": "string",
  "data": { ... },
  "meta": { "timestamp": "2026-06-19T10:00:00+09:00", "request_id": "uuid" }
}

// 422 Validation Error (현재 정합 OK)
{
  "success": false,
  "message": "Validation error",
  "error": { "code": "VALIDATION_ERROR", "details": [{"field": "x", "message": "y"}] },
  "meta": { ... }
}

// 404 Not Found (현재 정합 OK)
{
  "success": false,
  "error": { "code": "NOT_FOUND", "message": "string", "details": null },
  "meta": { ... }
}
```

---

## §4. DTO (스키마 변경)

### 4.1 신규 스키마

```python
# app/schemas/device.py (FR-2)
class LampResponseSecure(BaseModel):
    """v4.6 FR-2: user_password 제외 응답 스키마 (Central UI 노출용)"""
    id: int
    lamp_id: int
    color: EnumLampColor
    buzzer_time: int
    buzzer_sound: EnumBuzzerSound
    light_mode: EnumLightMode
    is_enable: bool
    # user_password 필드 부재 ← v4.5 대비 차이
    geolocation: Optional[Geolocation]
    device_groups: List[DeviceGroupNestedResponse]

# app/schemas/server.py (FR-2)
class ServerResponseSecure(BaseModel):
    """v4.6 FR-2: user_password 제외 Server 응답"""
    # 기존 ServerResponse에서 user_password만 제외
    ...
```

### 4.2 변경되는 스키마

| 스키마 | 변경 | 비고 |
|---|---|---|
| `EventMappingCameraBulkCreateResponse.skipped_config_ids` description | v4.5 placeholder → v4.6 실 분류 의미 | FR-5 적용 후 |
| `EventMappingSpeakerBulkCreateResponse.skipped_config_ids` description | 동일 | FR-5 |
| `EventMappingLampBulkCreateResponse.skipped_config_ids` description | 동일 | FR-5 |

### 4.3 영향 없는 스키마 (v4.5 안정)

- `DeviceUnassignRequest` / `DeviceBulkRemoveResponse` (DeviceGroup §5.6.9)
- `EventMappingCamera/Speaker/LampBulkUnassignRequest/Response`
- `ApiSingleResponse[T]` / `ResponseMeta` (PR-D)

---

## §5. NATS 정책

### 5.1 본 차수 변경 없음

Workflow Agent D 점검 결과 **무영향**:
- PR-A 0건 ConfigLog 발행은 `gop_sync` 채널의 `cmd_to_subject() → None`으로 차단됨 (db_monitor의 `CMD_SUBJECT_MAP`에 `SYNC_CONFIG_CHANGE_LOG` 미포함)
- statement-level 트리거 정합 유지 (`fn_notify_emc/ems/eml_stmt` `SELECT DISTINCT event_mapping_id`)
- 매니저 시그널 노이즈 0

### 5.2 신규 추가 작업

- **ConfigLog regression 가드 테스트 1건** (synthesis #2 권고) — PR-A의 0건 발행 정책이 향후 회귀로 되돌아가지 않도록 `tests/test_config_log_regression.py` 신설

---

## §6. ConfigChangeLog

### 6.1 본 차수 변경 없음

v4.5 PR-A에서 0건 발행 정책 확정. v4.6은 변경 없음. AuditLog 도메인 외 유지 (PRD_Audit_Log §2.2.2).

---

## §7. 사이드이펙트 분석

| FR | 사이드이펙트 | 영향 컴포넌트 | 완화 방법 |
|---|---|---|---|
| FR-1 | 기존 발급 토큰 전수 invalidate → 재로그인 강제 | 매니저 4종, Central UI | 사전 통지 + 점검 시간대 적용 |
| FR-2 | Central UI 디버그 화면이 평문 의존 시 영향 | C3 | `user_password` 의존 화면 사전 발견 + Secure 버전 사용 |
| FR-3 | 매니저 측 cross-origin 호출 사전 등록 필요 | C4~C7 | 매니저 도메인 화이트리스트 등록 |
| FR-5 | 응답 envelope에 신규 분류 추가 (backward-compatible) | C4, C5, C7 | strict 모드 디코더 → lenient로 사전 안내 |
| FR-6 | 테스트 코드만 변경 | DBApi 내부 | 무 |
| FR-7 | 14 단건 핸들러 OpenAPI 정확화, 동작 무변경 | 매니저 자동 생성 클라이언트 | 재생성 권장 |
| FR-8 | dead branch 제거, 운영자 마이그레이션 실수 차단 | 운영팀 | 무 |
| FR-9 | 환경별 AUTH_MODE 강제 → dev/staging/prod 분리 | 매니저 시연 환경 | dev=public 유지 안내 |
| FR-10 | §7.5 절 번호 시프트 (§7.5.9/10 → §7.5.10/11) | 매니저 명세 참조 | 변경 이력에 명시 + 차수 일시 |
| FR-11 | jti 블랙리스트 추가, 기존 클라이언트 호환 | 매니저 4종 | jti 무시 시 호환 |
| FR-12 | `.gitignore` 예외, PRD 산출물 git 추적 시작 | DBApi 팀 | 무 (오히려 보존성 향상) |

---

## §8. 호환성 (매니저 4종별)

| 매니저 | 영향 FR | 변경 인식 필요? | 사전 작업 |
|---|---|---|---|
| **GIS Manager (C4)** | FR-2 (Camera 응답 user_password 마스킹), FR-5 (Camera 벌크 중복), FR-7 (Camera 단건 14건) | Yes | DTO 재생성 + lenient 디코더 + .NET 사본 v4.5→v4.6 동기화 |
| **VMS Manager (C5)** | FR-2 + FR-5 + FR-7 + FR-4 (`Dotnet.Rtsp.Viewer.Ui` 통합상황도) | Yes | 동일 + 사본 동기화 우선 |
| **NVRManager (C6)** | FR-2 (Lamp/Server) + FR-4 Critical (`Ironwall.Dotnet.Libraries` 7개월 stale) + FR-7 | Yes | **사본 동기화 최우선** + Lamp 응답 마스킹 확인 |
| **Speaker Manager (C7)** | FR-2 (Speaker) + FR-5 + FR-7 | Yes | DTO 재생성 + 사본 동기화 |

### 8.1 .NET 사본 동기화 가이드 (FR-4 산출물)

별도 문서 `docs/v45_sync_guide.md` 작성:
1. **Ironwall.Dotnet.Libraries (Critical)** → `c:\workspace_python\api-test-server\GOP_Restful_Api_연동설계.md` 복사
2. **Dotnet.Rtsp.Viewer.Ui (High)** → 동일
3. **Dotnet.Monitoring.Solution (Medium)** → 동일
4. **Backup\pre_docs** → 손대지 않음 (이력 보관)

---

## §9. 변경 파일 인벤토리

### 9.1 코드

| 파일 | FR | 변경 |
|---|---|---|
| `app/config.py:22` | FR-1, 9 | JWT_SECRET_KEY validator + AUTH_MODE 환경별 분기 |
| `app/main.py:550` | FR-3 | CORS 화이트리스트 |
| `app/schemas/device.py:1046, 979, 1012` | FR-2 | LampResponseSecure 신설 + LampResponse user_password 제외 |
| `app/schemas/server.py:78, 117, 143, 190` | FR-2 | ServerResponseSecure 신설 |
| `app/routers/event_mapping_cameras.py:572~` | FR-5, 7 | in-memory dedup + 단건 7건 response_model |
| `app/routers/event_mapping_speakers.py:465~` | FR-5, 7 | 동일 |
| `app/routers/event_mapping_lamps.py:458~` | FR-5, 7 | 동일 |
| `app/db_triggers.py:98~108` | FR-8 | row-level ELSIF 블록 제거 |
| `app/utils/auth.py` | FR-11 (v4.7 분리 가능) | jti 블랙리스트 (지연 가능) |

### 9.2 명세서

| 파일 | FR | 변경 |
|---|---|---|
| `GOP_Restful_Api_연동설계.md` | FR-10 | §7.5.7 재채번 (후자 → §7.5.9, 본 차수 §7.5.9/10 → §7.5.10/11) |
| 동 파일 | 모든 FR | 변경 이력 v4.6 행 추가 + 푸터 일자 갱신 |

### 9.3 테스트

| 파일 | FR | 변경 |
|---|---|---|
| `tests/test_event_mapping_cameras_bulk.py` | FR-6 | 4건 envelope key 정합화 + URL 정정 |
| `tests/test_event_mapping_speakers_bulk.py` | FR-6 | 동일 |
| `tests/test_event_mapping_lamps_bulk.py` | FR-6 | 동일 |
| `tests/test_config_log_regression.py` (신규) | regression | PR-A 0건 발행 가드 |
| `tests/test_security_response_schema.py` (신규) | FR-2 | LampResponseSecure 검증 |
| `tests/test_same_request_dedup.py` (신규) | FR-5 | 같은 request 내 중복 분류 검증 |
| `tests/test_lamp_enum_validation.py` (신규) | regression | PR-C "Purple" → 422 |

### 9.4 인프라

| 파일 | FR | 변경 |
|---|---|---|
| `.env.example` | FR-1, 3, 9 | JWT 랜덤화 안내 + CORS_ORIGINS + AUTH_MODE 환경별 |
| `docker-compose.yml:34` | FR-1 | JWT_SECRET_KEY 디폴트 제거 (env 강제) |
| `.gitignore` | FR-12 | `!docs/PRD_*.md` 예외 추가 |

### 9.5 가이드

| 파일 | FR | 변경 |
|---|---|---|
| `docs/v45_sync_guide.md` (신규) | FR-4 | .NET 사본 4곳 동기화 가이드 |

---

## §10. 테스트 계획

### 10.1 기존 pytest 11 실패 처리 (FR-6)

| # | 테스트 케이스 | 현재 실패 원인 | v4.6 처리 |
|---|---|---|---|
| 1 | cameras `not_found_when_preset_id_absent` | 라우터는 invalid preset_id를 `failed_items`로 처리, 테스트는 `not_found_config_ids` 기대 | 테스트 → 명세 일치 (preset 미존재는 failed_items) |
| 2 | cameras `skip_duplicates` | 동일 요청 내 중복 created=3, 테스트는 1 기대 | **FR-5 적용 후 자동 통과** (skipped_in_request=2) |
| 3 | cameras `log_config_change camera_ids` | after_state 키 `config_ids` vs 테스트 `camera_ids` | 테스트 envelope key 통일 |
| 4 | cameras `404 DELETE URL` | `DELETE /cameras/bulk` (테스트) vs `/cameras` (실제) | 테스트 URL 정정 |
| 5~8 | speakers 4건 | cameras와 동일 (file_group_id, dup, speaker_ids, URL) | 동일 처리 |
| 9 | lamps `skip_duplicates` | UNIQUE 충돌 → 422, 테스트는 200+멱등 기대 | **FR-5 적용 후 통과** |
| 10 | lamps `log_config_change lamp_ids` | lamp_ids vs config_ids | 테스트 key 통일 |
| 11 | lamps `404 DELETE URL` | URL 부재 | 테스트 정정 |

### 10.2 신규 추가 테스트 (4건)

| 테스트 | FR | 시나리오 |
|---|---|---|
| `test_config_log_regression.py::test_should_emit_zero_count_log` | regression | bulk_create with 0 valid items → ConfigChangeLog 발행 확인 (PR-A 회귀 가드) |
| `test_security_response_schema.py::test_should_not_expose_user_password_in_lamp_response` | FR-2 | GET /lamps/{id} 응답에 user_password 키 부재 검증 |
| `test_same_request_dedup.py::test_should_classify_dup_in_request_as_skipped` | FR-5 | items=[camera_id=356, camera_id=356, camera_id=356] → created=1 + skipped_in_request=2 |
| `test_lamp_enum_validation.py::test_should_return_422_for_invalid_color` | regression | color="Purple" → HTTP 422 + Pydantic error (PR-C 회귀 가드) |

### 10.3 회귀 기준

본 차수 적용 후:
- pytest **70/70** 통과 (기존 66 + 신규 4)
- 시뮬레이션 19+α 시나리오 100% 통과
- OpenAPI 7 Bulk + 14 단건 = 21 엔드포인트 응답 스키마 정확 노출
- 시작 컨테이너 healthy + Image rebuild 후 정합 검증

---

## §11. 명세 패치 (Edit Pair)

본 PRD 결재 후 본 메인이 `GOP_Restful_Api_연동설계.md`에 적용할 주요 Edit Pair (간략):

| # | 영역 | 변경 |
|---|---|---|
| EP-1 | §7.5.7 헤더 (L12073) | `#### 7.5.7 MappingLamp 전체 목록 조회 (독립)` → `#### 7.5.9 MappingLamp 전체 목록 조회 (독립)` |
| EP-2 | §7.5.9/10 헤더 (L12143/12324) | `#### 7.5.9 EventMappingLamp 벌크 등록` → `#### 7.5.10` / 7.5.10 → 7.5.11 |
| EP-3 | 부록 §12.1 표 | 7.5.10/7.5.11 동기화 |
| EP-4 | §7.3.9 Response Fields 표 | `skipped_config_ids` description: v4.5 placeholder → v4.6 실 분류 (`(mapping_id, device_id)` DB 선존 + 같은 request 내 중복) |
| EP-5 | §7.3.9 본문 (단건 14건) | `response_model=ApiSingleResponse[EventMappingCameraResponse]` 명시 (Camera/Speaker/Lamp 7건씩) |
| EP-6 | 변경 이력 v4.6 행 신규 추가 | FR-1~12 요약 + 검증 결과 |
| EP-7 | 푸터 | `**문서 버전**: v4.5` → `v4.6`, 일자 `2026-06-18` → `2026-06-23` (적용 완료일) |

---

## §12. 공수

| FR | 작업 | 코드 | 테스트 | 명세/문서 | 총 |
|---|---|---|---|---|---|
| FR-1 | JWT 시크릿 환경 분리 | 30분 | - | 5분 | **35분** |
| FR-2 | user_password 마스킹 (Secure 스키마 + 라우터) | 1.5h | 30분 | 15분 | **2.25h** |
| FR-3 | CORS 화이트리스트 | 15분 | - | 10분 | **25분** |
| FR-4 | .NET 사본 가이드 작성 | - | - | 30분 | **30분** |
| FR-5 | PR-B 중복 보강 (3 라우터 in-memory) | 1.5h | 30분 | 15분 | **2.25h** |
| FR-6 | pytest 11건 정합 | - | 1.5h | - | **1.5h** |
| FR-7 | 단건 14건 response_model | 1h | 30분 | 20분 | **1.75h** |
| FR-8 | dead branch 제거 | 20분 | 10분 | - | **30분** |
| FR-9 | AUTH_MODE 환경별 분기 | 15분 | - | 10분 | **25분** |
| FR-10 | §7.5.7 재채번 | - | - | 30분 | **30분** |
| FR-11 | JWT 회전 (v4.7 분리 가능) | 3h | 1h | 20분 | **4.5h** |
| FR-12 | PRD git 추적 | 5분 | - | - | **5분** |
| **합계 (FR-11 포함)** | | **~9h** | **~4h** | **~3h** | **~16h (2일)** |
| **합계 (FR-11 v4.7 분리 시)** | | **~6h** | **~3h** | **~2.5h** | **~11.5h (1.5일)** |

권고: **FR-11을 v4.7로 분리**하여 v4.6 11건 완료 후 매니저 통합 시작.

---

## §13. 리스크

| # | 리스크 | 가능성 | 영향 | 완화 |
|---|---|---|---|---|
| R1 | JWT 시크릿 변경 → 운영 토큰 전수 invalidate | High | High | 사전 통지 + 점검 시간대 적용 + 매니저 재로그인 강제 가이드 |
| R2 | .NET 사본 동기화 지연 → 매니저 작업 충돌 | Medium | Critical | FR-4 가이드 발송 + 매니저별 동기화 confirm 요청 |
| R3 | FR-5 응답 envelope 신규 필드 → 매니저 strict 디코더 실패 | Medium | Medium | backward-compatible 사전 announce + sample JSON 공유 |
| R4 | FR-11 JWT 회전 분량 큼 (4.5h) | Low | Low | **v4.7로 분리 권고** (별도 PRD) |
| R5 | pytest 11건 중 2건 (skip_duplicates) 보더라인 — 명세 결정 필요 | Medium | Low | FR-5 적용으로 자동 해결 |
| R6 | CORS 화이트리스트 → 매니저 도메인 미등록 시 호출 실패 | High | Medium | FR-3 + 매니저 도메인 사전 수집 + 환경별 화이트리스트 (dev=*, prod=화이트리스트) |
| R7 | LampResponseSecure 신설 → 기존 단건 라우터 응답 타입 swap | Medium | Low | Pydantic 호환 (필드 제거는 backward-compatible) |

---

## §14. 롤백 정책

### 14.1 롤백 단위

| 영역 | 단위 | 명령 |
|---|---|---|
| **전체 v4.6** | 본 차수 commit 전체 | `git reset --hard pre-v46` (적용 직전 HEAD = de15ba0) |
| **FR별 독립** | FR-별 commit | `git revert <commit-hash>` |
| **Docker Image** | rebuild 전 Image | `docker tag api-test-server:pre-v46 api-test-server:latest` (사전 tag 후) |

### 14.2 PR 단위 권고

각 FR별 독립 PR로 진행하여 부분 롤백 용이:
- PR-46-1: FR-1 (JWT)
- PR-46-2: FR-2 (user_password)
- PR-46-3: FR-3 (CORS)
- PR-46-4: FR-4 (.NET 가이드)
- PR-46-5: FR-5 (중복 분류)
- PR-46-6: FR-6 (pytest)
- PR-46-7: FR-7 (단건 response_model)
- PR-46-8: FR-8 (dead branch)
- PR-46-9: FR-9 (AUTH_MODE)
- PR-46-10: FR-10 (§7.5.7 재채번)
- PR-46-12: FR-12 (PRD git 추적)
- (FR-11은 v4.7 분리)

### 14.3 데이터 영향 없음

본 차수는 스키마/마이그레이션 변경 없음. ConfigChangeLog 정책 동일. 데이터 손실 위험 0.

---

## §15. 구현 스케치

### 15.1 FR-1 JWT 시크릿

```python
# app/config.py
import os
from pydantic import field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    JWT_SECRET_KEY: str = Field(
        ...,  # required, no default
        min_length=32,
        description="HS256 시크릿. 환경별 분리 + os.urandom(32).hex() 권장",
    )

    @field_validator('JWT_SECRET_KEY')
    @classmethod
    def reject_default(cls, v: str) -> str:
        if 'your-secret-key' in v or 'change-in-production' in v:
            raise ValueError("JWT_SECRET_KEY는 운영용 랜덤값으로 교체 필수 (예: python -c 'import os; print(os.urandom(32).hex())')")
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY는 최소 32자 이상")
        return v
```

```bash
# .env.example
# JWT_SECRET_KEY 생성: python -c "import os; print(os.urandom(32).hex())"
JWT_SECRET_KEY=  # 환경별로 다른 값을 반드시 설정 — 디폴트값 사용 시 부팅 실패
```

### 15.2 FR-2 user_password 마스킹

```python
# app/schemas/device.py (LampResponseSecure 신설)
class LampResponseSecure(BaseModel):
    """v4.6 FR-2: user_password 제외 — Central UI/매니저 응답용"""
    id: int
    lamp_id: int
    color: EnumLampColor
    buzzer_time: int
    buzzer_sound: EnumBuzzerSound
    light_mode: EnumLightMode
    is_enable: bool
    geolocation: Optional[Geolocation] = None
    device_groups: List[DeviceGroupNestedResponse] = []
    # user_password 필드 부재 ← v4.5 LampResponse 대비 유일 차이

    model_config = ConfigDict(from_attributes=True)

# app/routers/lamps.py
@router.get("/{lamp_id}", response_model=ApiSingleResponse[LampResponseSecure])
def get_lamp(lamp_id: int, ...):
    ...
```

### 15.3 FR-3 CORS

```python
# app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),  # ".env에서 콤마 구분"
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

# .env.example
CORS_ORIGINS=http://localhost:6173,http://localhost:5173,https://gop-central.company.com
```

### 15.4 FR-5 PR-B 중복 보강

```python
# app/routers/event_mapping_cameras.py:572~
created_ids: list[int] = []
failed_items: list[EventMappingCameraBulkCreateFailure] = []
created_rows: list[EventMappingCamera] = []
skipped_config_ids: list[int] = []     # DB 선존 매핑 → 기존 row PK
not_found_config_ids: list[int] = []
skipped_in_request_ids: list[int] = []  # v4.6 FR-5 신규: 같은 request 내 중복 → camera_id

seen_in_request: set[int] = set()
for idx, item in enumerate(request.items):
    if item.camera_id in seen_in_request:
        skipped_in_request_ids.append(item.camera_id)  # 신규 분류
        continue
    seen_in_request.add(item.camera_id)
    # FR-B: Camera FK 미존재 → not_found_config_ids
    camera = db.query(Camera).filter(Camera.id == item.camera_id).first()
    if not camera:
        not_found_config_ids.append(item.camera_id)
        continue
    # FR-B: DB 선존 매핑 → skipped_config_ids
    existing = db.query(EventMappingCamera).filter(
        EventMappingCamera.event_mapping_id == mapping_id,
        EventMappingCamera.camera_id == item.camera_id,
    ).first()
    if existing:
        skipped_config_ids.append(existing.id)
        continue
    # ... 이하 기존 로직 (target_preset_id, home_preset_id 검증)
```

응답 envelope에 `skipped_in_request_ids` 필드 추가 (스키마 `EventMappingCameraBulkCreateResponse`).

### 15.5 FR-7 단건 14건 response_model

```python
# app/routers/event_mapping_cameras.py (목록 GET)
@router.get(
    "/{mapping_id}/cameras",
    response_model=ApiResponse[EventMappingCameraResponse],  # 페이지네이션
    responses={404: {"description": "Event mapping not found"}},
)
def list_event_mapping_cameras(...): ...

# 단건 GET
@router.get(
    "/{mapping_id}/cameras/{config_id}",
    response_model=ApiSingleResponse[EventMappingCameraResponse],
    responses={404: {"description": "Camera config not found"}},
)
def get_event_mapping_camera(...): ...

# 단건 POST (이미 ApiSingleResponse 적용? — 검증 필요)
# 단건 PATCH/PUT/DELETE 동일 패턴
```

### 15.6 FR-8 dead branch 제거

```sql
-- app/db_triggers.py:98~108 ELSIF 블록 제거
CREATE OR REPLACE FUNCTION fn_notify_gop_sync()
RETURNS trigger AS $$
DECLARE
    payload_data jsonb;
BEGIN
    IF TG_TABLE_NAME = 'controllers' THEN
        ...
    ELSIF TG_TABLE_NAME = 'sensors' THEN
        ...
    -- ELSIF TG_TABLE_NAME IN ('event_mapping_cameras', 'event_mapping_speakers', 'event_mapping_lamps') THEN
    --     ↑ 이 분기 제거. v4.3 마이그레이션에서 statement-level로 대체됨 (fn_notify_emc_stmt/ems_stmt/eml_stmt)
    END IF;
    ...
END $$;
```

### 15.7 FR-9 AUTH_MODE 환경별

```python
# app/config.py
class Settings(BaseSettings):
    AUTH_MODE: Literal["public", "token"] = Field(
        "token",  # 디폴트 token (이전엔 public)
        description="dev=public 허용, staging/prod=token 강제",
    )

    @field_validator('AUTH_MODE')
    @classmethod
    def validate_env_consistency(cls, v: str, info: ValidationInfo) -> str:
        env = os.environ.get('ENVIRONMENT', 'dev')
        if env in ('staging', 'prod') and v != 'token':
            raise ValueError(f"AUTH_MODE={v} not allowed in {env} (use token)")
        return v
```

### 15.8 FR-12 PRD git 추적

```gitignore
# .gitignore
docs/
Docs/

# 예외: PRD 파일은 git에 추적 (FR-12)
!docs/PRD_*.md
!docs/v45_sync_guide.md
```

---

## §16. 변경 이력

| 버전 | 일자 | 작성자 | 변경 내용 |
|------|------|--------|----------|
| v1.0 | 2026-06-19 | 이기호 차장 | 신규 작성 — v4.5 PR-A/B/C/D 적용 후 잔존 GAP 12건 정리. Workflow `wr91vn26e` 9 agent + synthesis health check 기반. P0 4건 (보안 3 + .NET 사본 1) + P1 5건 + P2 3건 분류. FR-11 (JWT 회전) v4.7 분리 권고로 v4.6은 11건 처리. 매니저 4종 통합 시작 전 안전 확보 목표. |

---

## 부록 A. 관련 산출물

| 파일 | 설명 |
|---|---|
| `docs/workflow_health_v46/A_pytest_11fail.md` | pytest 11 실패 정밀 분석 |
| `docs/workflow_health_v46/B_v46_unresolved.md` | 미해결 권고 인벤토리 |
| `docs/workflow_health_v46/C_security.md` | 보안 점검 (JWT/CORS/user_password) |
| `docs/workflow_health_v46/D_nats_db_monitor.md` | NATS 정합성 (무영향 확인) |
| `docs/workflow_health_v46/E_dotnet_sopies.md` | .NET 사본 4곳 stale 분석 |
| `docs/workflow_health_v46/F_manager_integration.md` | 매니저 통합 ready status |
| `docs/workflow_health_v46/G_dead_code.md` | dead code / stale references |
| `docs/workflow_health_v46/H_main_merge.md` | main 머지 위험 |
| `docs/workflow_health_v46/I_prd_preservation.md` | PRD 보존 정책 |
| `docs/workflow_health_v46/J_synthesis_go_nogo.md` | Go/No-Go 종합 결정 |
| `docs/PRD_BulkAPI_Spec_Sync_v4.4.md` | v4.4 PRD (이전 차수) |
| `docs/sim/raw_data.json` | 시뮬레이션 19 시나리오 |

## 부록 B. v4.7 차기 차수 후보 (본 PRD 범위 외)

| 항목 | 사유 |
|---|---|
| **FR-11 JWT 토큰 회전 (jti 블랙리스트)** | 공수 4.5h — v4.6 분량 초과, 별도 PRD 권고 |
| **G7 _get_device_groups_nested 중복 추출** | P3 cosmetic, 7개 라우터 DRY 위반 → `app/utils/device_group_helpers.py` 추출 |
| **단건 CRUD 외 다른 라우터 response_model 점검** | account/server/event 등 |

## 부록 C. 결재 체크리스트

차장님 결재 시 확인 항목:

- [ ] v4.6 차수 명명 동의 (v4.7 분리 안 함)
- [ ] FR-11 JWT 회전 v4.7 분리 동의
- [ ] FR-1 JWT 시크릿 변경 → 운영 토큰 invalidate 사전 통지 일정 합의
- [ ] FR-2 LampResponseSecure 신설 vs 기존 LampResponse 정정 중 어느 쪽
- [ ] FR-3 CORS 화이트리스트 매니저 도메인 수집 책임자
- [ ] FR-4 .NET 사본 동기화 가이드 발송 일자
- [ ] FR-5 응답 envelope 신규 필드 (`skipped_in_request_ids`) 명명 동의
- [ ] PR-46-N 단위 commit 분리 동의
- [ ] 일정 (당일 P0 / 익일 P1 / 06-23 P2) 동의
- [ ] 롤백 태그 `pre-v46` 사전 생성 동의

---

**문서 버전**: v1.0
**최종 업데이트**: 2026-06-19
