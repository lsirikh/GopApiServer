# PRD: GOP_Restful_Api 연동설계 v4.7 — 지향성 도메인 확장 + v4.6 분리 3건 통합

> **차수**: v4.6 → v4.7
> **작성자**: 이기호 차장
> **작성일**: 2026-06-23
> **선행 산출물**: `docs/PRD_BulkAPI_PostMortem_v4.6.md` (P0/P1 9건 정리 완료), `docs/PRD_BulkAPI_Spec_Sync_v4.4.md`
> **롤백 태그**: `pre-v47` (적용 직전 HEAD = 6a2430a)
> **차수 결정 근거**: v4.6 마감 직전 차장님 도메인 지적(디바이스 지향성 누락)으로 신규 FR-13 발생. v4.6 P2 분리 3건(FR-6 pytest 잔존 / FR-7 단건 14건 / FR-11 JWT 회전)과 묶어 한 차수로 처리 — 매니저 통합 1단계 완성 + 보안 강화 동시 종결.

---

## §1. 개요

### 1.1 두괄식 — 왜 v4.7이 필요한가

v4.6에서 P0 4건(JWT 시크릿/user_password/CORS/.NET 사본) + P1 5건(중복 분류/dead code/AUTH_MODE 등) 9건을 정리하여 매니저 통합 진입 안전 상태를 확보했으나, **마감 직전 차장님 도메인 지적**으로 디바이스 스키마에 **지향성(heading)이 누락**된 것이 드러났다(FR-13 신규). 현재 `Geolocation`(`app/schemas/device.py:113`)은 `location/latitude/longitude/altitude` 4필드만 보유 — 디바이스의 **위치**만 표현하고 **어느 방향을 향하는지**는 표현 불가. Camera 정면, Speaker 음원 콘, Sensor(PIDS/PIR) 감지 범위 중심 방향이 모두 통합상황도(VMS UI) 부채꼴/원뿔 시각화에 필수임에도 표현 수단이 없다. 동시에 v4.6에서 공수 사유로 분리한 3건(FR-6 pytest 잔존 11건, FR-7 단건 14건 response_model, FR-11 JWT jti 회전)이 매니저 통합 1단계 완료 전 반드시 마감되어야 한다. v4.7은 **신규 FR-13 + 분리 3건 = 총 4 FR**을 한 차수로 일괄 처리하여 도메인 정합 + 매니저 OpenAPI 완성 + 보안 강화를 종결한다.

### 1.2 영향 컴포넌트

| # | 컴포넌트 | v4.7 영향 | FR |
|---|---------|----------|----|
| C1 | **DBApi (api-test-server)** | 스키마 1곳(`Geolocation.heading`) + 단건 라우터 14건 + JWT 회전 모듈 신설 + pytest 11건 정합 — 코드 변경 최대 | FR-6, 7, 11, 13 |
| C2 | **db_monitor / NATS** | 무영향 — `geolocation` JSON 컬럼이 기존 SYNC 페이로드에 그대로 흐름, statement-level 트리거 미수정 | regression 가드만 추가 |
| C3 | **Central UI (Ironwall)** | 디바이스 등록/수정 화면에 heading 입력 위젯 추가(0~360°). 단건 14건 OpenAPI 정확화로 자동 생성 모델 갱신 | FR-7, 13 |
| C4 | **GIS Manager** | 지도 상에 카메라/스피커/센서 부채꼴 아이콘 렌더링 — heading 소비 1순위 | FR-13 |
| C5 | **VMS Manager** | Camera 단건 14건 응답 모델 + heading 시각화 | FR-7, 13 |
| C6 | **NVRManager** | Lamp 단건 응답 모델 (Lamp는 무방향이지만 envelope 공통) | FR-7 |
| C7 | **Speaker Manager** | Speaker 단건 14건 + 음원 콘 방향 | FR-7, 13 |

### 1.3 일정

| 단계 | 산출물 | 기한 | 책임 | 공수 |
|------|--------|------|------|------|
| **본 PRD 결재** | `PRD_v4.7.md` | 2026-06-23 | 이기호 차장 | — |
| **FR-13 heading 필드 추가** | `Geolocation.heading` + 6 디바이스 Nested 응답 반영 | 2026-06-23 (당일) | DBApi 담당 | 1.5h |
| **FR-7 단건 14건 response_model** | Camera/Speaker 단건 14건 → `ApiSingleResponse[T]` / `ApiResponse[T]` | 2026-06-23 | DBApi 담당 | 1.75h |
| **FR-6 pytest 잔존 11건 정합** | envelope key 통일 + URL + 멱등 가정 케이스 | 2026-06-24 | DBApi 담당 | 1.5h |
| **FR-11 JWT jti 블랙리스트** | `token_blacklist` 테이블 + auth.py 검증 + `/auth/logout` 라우터 | 2026-06-24 | DBApi 담당 | 4.5h |
| **명세 v4.7 갱신 + Image rebuild** | `GOP_Restful_Api_연동설계.md` v4.7 + Docker Image | 2026-06-25 | DBApi 담당 | — |
| **매니저 통합 1단계 완료** | C4~C7 heading 소비 + 단건 모델 회귀 통과 | 2026-06-26~ | 매니저 담당 | — |

**총 코드 공수 약 9.25h (1.2 인일).**

### 1.4 v4.6과의 관계

- v4.6 (HEAD=6a2430a, 2026-06-19) FR-1~5, 8, 9, 10, 12는 변경 없이 유지.
- v4.6 §2.1 P2 표에서 `공수 4.5h로 v4.7로 분리 가능`으로 보류한 FR-11(JWT 회전)을 본 차수에서 동일 번호로 승계 — 매니저 디코더 호환 위해 번호 유지.
- v4.6 PR-D는 bulk 6건만 정정 → 단건 14건 잔존(FR-7)을 본 차수에서 종결.
- v4.6 FR-6 pytest 11건은 FR-5 dedup 효과로 일부 자동 해결되었으나 envelope/URL/멱등 가정 잔존 → 본 차수에서 종결.
- 신규 FR-13(지향성)은 v4.6 점검 범위 밖이었던 도메인 GAP — v4.7 단독 발생.

---

## §2. 요구사항

### 2.1 Functional Requirements (4건)

| # | 우선순위 | 제목 | 설명 |
|---|---------|------|------|
| **FR-6** | P1 (승계) | pytest 잔존 11건 envelope/URL 정합 종결 | v4.6 FR-5(dedup) 적용 후 일부 자동 통과했으나, ① envelope key 불일치 잔존(`camera_ids/speaker_ids/lamp_ids` → 공통 `config_ids`로 sed 미적용분), ② URL 경로 변경 미반영(v4.5 PR-D 리네이밍), ③ 멱등 가정 케이스(`skip_duplicates` 플래그 의존) 11건 처리. AAA 패턴 + `should_X_when_Y` 명명 준수 |
| **FR-7** | P1 (승계) | EventMapping 단건 CRUD 14건 `response_model` 명시 | v4.6 PR-D가 bulk 6건만 정정했고 단건은 잔존. Camera 7건(목록 GET/단건 GET/POST/PATCH/PUT/DELETE/독립 GET), Speaker 7건 — 합 14건이 `response_model=dict` → OpenAPI `additionalProperties:true`로 노출. 모두 `ApiSingleResponse[T]`(단건) 또는 `ApiResponse[T]`(페이지) 명시. Lamp는 v4.6에서 일부 처리되어 잔여분만 확인 |
| **FR-11** | P2 (승계) | JWT 토큰 회전 — jti 블랙리스트 | Access 24h / Refresh 7d 발급은 v4.6 FR-1 시크릿 정정 후 정상 동작하나 jti 블랙리스트 부재 → 로그아웃 사실상 무효. ① `token_blacklist` 테이블 신설(jti, user_id, exp, revoked_at), ② `auth.py`에 `is_revoked(jti)` 검증 진입점, ③ `POST /api/auth/logout` 라우터에서 현재 access/refresh jti 등록, ④ 만료된 jti 일일 cleanup cron. Redis 도입은 후속 차수 |
| **FR-13** | P0 (신규) | 디바이스 지향성 — `Geolocation.heading` 필드 추가 | `app/schemas/device.py:113 Geolocation`에 `heading: Optional[float] = Field(None, ge=0.0, lt=360.0, description="방위각(정북=0, 시계방향)", examples=[135.0])` 추가. 6 디바이스 테이블의 `geolocation` JSON(B) 컬럼에 자동 반영. Lamp/Enclosure는 무방향이지만 스키마는 공통 사용 — 송신측이 `null`로 보내면 됨. Backfill 마이그레이션으로 기존 row의 JSON에 `"heading": null` 명시적 추가 |
| **FR-14** | P0 (신규) | **JSON ↔ JSONB 일관성 복원 — PRD 기획대로 23개 컬럼 일괄 전환** | **버그 수정 성격**: PRD 파일명(`PRD_Camera_Urls_JsonB.md`, `PRD_Event_Detail_JsonB.md`) + Docstring/주석 23곳에서 일관되게 "JSONB" 의도 명시되었으나, 실제 구현은 `from sqlalchemy import JSON`(dialect-agnostic, PostgreSQL의 `json`에 매핑) 사용 → 시스템 전체 23개 JSON 컬럼이 모두 `json` 타입으로 잘못 저장. 매니저들은 PRD를 보고 jsonb 동작(인덱스, 빠른 검색)을 기대하나 실제는 매번 파싱 + 인덱스 불가. <br><br>**대상 23개 컬럼**: `audit_logs.changes` / `config_change_logs.before_state, after_state` / `cameras.geolocation, hardware_spec, urls` / `controllers.geolocation` / `detection_events.detail` / `enclosure_metrics.detail` / `enclosures.geolocation, threshold_config` / `file_groups.files` / `lamps.geolocation` / `malfunction_events.detail` / `report_generations.severity_filter, summary_data` / `report_templates.components` / `sensors.geolocation` / `server_metrics.detail` / `servers.threshold_config` / `speakers.geolocation` / `system_events.detail` / `user_groups.permissions` <br><br>**작업**: ① SQLAlchemy import — `from sqlalchemy.dialects.postgresql import JSONB` 추가, `Column(JSON)` → `Column(JSONB)` (8 파일, 23 위치). ② Alembic 마이그레이션 — `ALTER TABLE ... ALTER COLUMN ... TYPE jsonb USING ...::jsonb` (23 컬럼). FR-13 Backfill과 같은 트랜잭션. <br><br>**사이드이펙트 분석 (Workflow 결재 반영)**: 데이터 손실 0 / 응답 envelope 동일 / Pydantic 무영향 / 응답 키 순서만 알파벳 정렬됨(매니저 strict 디코더 영향 가능, lenient는 무영향). 저장 공간 +10%, Insert 약간 느림(<1ms), Select 압도적 빠름(파싱 없음 + GIN 인덱스 가능). |

#### FR-13 범위 결정 (차장님 결재)

| 항목 | v4.7 포함 | v4.8+로 분리 | 사유 |
|------|----------|-------------|------|
| `heading` (방위각, 0~360°) | O | — | 시각화 최소 단위 — 부채꼴 회전각 |
| `tilt` (틸트, -90~90°) | — | O | 3D 시각화 단계에서 필요, v4.7 통합상황도 2D만 |
| `fov` (시야각, 0~360°) | — | O | Camera만 의미, Speaker/Sensor는 별도 모델 필요 |
| `roll` (롤, -180~180°) | — | O | 거의 0, PTZ preset 영역 |
| PTZ 동적 회전 | — | O | Camera preset 별도 라우터(`/api/cameras/{id}/presets`)로 분리 |

### 2.2 Non-Functional Requirements

| # | 제목 | 설명 |
|---|------|------|
| **NFR-1** | 성능 | FR-11 jti 검증은 토큰 유효 시간 24h 동안만 추가 SELECT 1회 — 인덱스 `idx_token_blacklist_jti UNIQUE` 보장 시 무영향. FR-13 heading은 JSON 컬럼 한 키 추가뿐 |
| **NFR-2** | 가용성 | FR-11 토큰 회전 시 기존 발급 토큰은 영향 없음(이번 차수 invalidate 없음). 신규 발급분부터 회수 가능 |
| **NFR-3** | 보안 | OWASP A07(인증 실패) — 로그아웃 토큰 회수 부재 정정. FR-13은 보안 무영향 |
| **NFR-4** | 매니저 호환성 | FR-13 heading은 backward-compatible(Optional 신규 키, 기존 응답 디코더는 미인식 키 무시). FR-7 단건 14건 모델 강화는 strict 디코더 사용 매니저에 영향 → 사전 통지 + OpenAPI 재생성 가이드 |
| **NFR-5** | 회귀 보장 | pytest 80/80 (v4.6 70 + 신규 10) + 시뮬레이션 19+α 시나리오 100% 통과. FR-13 회귀: `should_serialize_geolocation_with_heading_when_set` 등 4건 신설 |

---

## §3. API 명세 (변경 영역)

### 3.1 변경되는 엔드포인트 인벤토리

| 영역 | 변경 종류 | 대상 | 동작 변경 |
|------|----------|------|----------|
| **6 디바이스 응답 전 영역 (FR-13)** | `geolocation.heading` 키 추가 | Camera/Speaker/Sensor/Controller/Lamp/Enclosure × (Create Request / Update Request / Response / NestedResponse) = 약 25 위치 | 없음 (Optional 추가) |
| **EventMapping 단건 CRUD 14건 (FR-7)** | `response_model=dict` → `ApiSingleResponse[T]` / `ApiResponse[T]` | Camera 7건 + Speaker 7건 | 없음 — 페이로드 동일, OpenAPI만 정확 |
| **인증 라우터 (FR-11)** | `POST /api/auth/logout` 신설 + 모든 보호 라우터에 jti 검증 미들웨어 | `auth.py` 전반 | 로그아웃 실 효력 발생 |
| **pytest fixtures (FR-6)** | envelope key + URL + 멱등 가정 정합 | `tests/test_event_mapping_*.py` 11건 | 테스트 코드만 |

### 3.2 FR-13 — 디바이스 응답 예시 (Camera)

```json
// GET /api/cameras/{id} — 200 OK
{
  "success": true,
  "data": {
    "id": 12,
    "name": "GOP-1구역-CAM-03",
    "geolocation": {
      "location": "GOP 1구역 전방 초소",
      "latitude": 38.1234,
      "longitude": 127.5678,
      "altitude": 150.0,
      "heading": 135.0   // v4.7 신규 — 정북=0, 시계방향, 0~360 (exclusive)
    },
    "device_groups": [/* ... */]
  },
  "meta": { "timestamp": "2026-06-25T10:00:00+09:00", "request_id": "uuid" }
}
```

- `heading: null` 허용 — 무방향 디바이스(Lamp/Enclosure) 또는 미설정 시
- 송신측이 키 자체를 생략해도 통과 (Optional + default None)
- DB 저장 형태: `devices.geolocation` JSON 컬럼 내 `"heading": 135.0`
- 360.0은 422 거부 (`lt=360.0`) — 0°와 동치이므로 일관성 위해 0 정규화 요구

### 3.3 FR-7 — 단건 14건 OpenAPI 정확화

```python
# Before (v4.6)
@router.get("/api/event-mappings/cameras/{id}", response_model=dict)

# After (v4.7)
@router.get(
    "/api/event-mappings/cameras/{id}",
    response_model=ApiSingleResponse[EventMappingCameraResponse],
)
```

대상 14건 인벤토리:

| 디바이스 | 메서드 × 경로 | 응답 모델 |
|---------|-------------|----------|
| Camera | `GET /api/event-mappings/cameras` (페이지) | `ApiResponse[EventMappingCameraResponse]` |
| Camera | `GET /api/event-mappings/cameras/{id}` | `ApiSingleResponse[EventMappingCameraResponse]` |
| Camera | `POST /api/event-mappings/cameras` | `ApiSingleResponse[EventMappingCameraResponse]` |
| Camera | `PATCH /api/event-mappings/cameras/{id}` | 동일 |
| Camera | `PUT /api/event-mappings/cameras/{id}` | 동일 |
| Camera | `DELETE /api/event-mappings/cameras/{id}` | `ApiSingleResponse[DeleteAck]` |
| Camera | `GET /api/event-mappings/cameras/by-event/{event_id}` (독립) | `ApiResponse[EventMappingCameraResponse]` |
| Speaker | 위 7건 동형 | `ApiSingleResponse/ApiResponse[EventMappingSpeakerResponse]` |

→ Camera 7 + Speaker 7 = **14건**. Lamp는 v4.6에서 일부 처리, 잔여분은 코드 검토 후 동일 패턴 적용.

### 3.4 FR-11 — JWT 토큰 회전 흐름

```
[1] POST /api/auth/login              → access(jti=A, exp=24h), refresh(jti=R, exp=7d) 발급
[2] (보호 라우터 호출)                → auth.py: is_revoked(A) == False → 200 OK
[3] POST /api/auth/logout (Auth: A)   → INSERT token_blacklist(jti=A, exp=24h후, revoked_at=now)
                                       → INSERT token_blacklist(jti=R, exp=7d후, revoked_at=now)
                                       → 204 No Content
[4] (보호 라우터 재호출 with A)       → auth.py: is_revoked(A) == True → 401 TOKEN_REVOKED
[5] (daily cleanup cron 03:00 KST)    → DELETE FROM token_blacklist WHERE exp < NOW()
```

- 신규 응답 코드: `401 { "error": { "code": "TOKEN_REVOKED", ... } }`
- `token_blacklist` 테이블 스키마: `id BIGSERIAL`, `jti VARCHAR(64) UNIQUE NOT NULL`, `user_id BIGINT NOT NULL`, `exp TIMESTAMPTZ NOT NULL`, `revoked_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`, `INDEX idx_jti(jti)`
- Redis 미도입 — DB 테이블 + 인덱스로 충분 (검증 일일 평균 호출량 < 50k 가정)
- Refresh 회전 시 이전 access도 자동 회수 (refresh가 access의 부모 토큰 관계로 묶임)

### 3.5 응답 envelope 정합 (v4.6 PR-D 결과 + 단건 14건 완성)

v4.6에서 bulk 6건 + Lamp 일부가 통일됐고, v4.7 FR-7로 Camera/Speaker 단건 14건이 합류하여 **EventMapping 전 영역 21+건 envelope 완전 통일** 달성.

```json
// 200 OK 공통
{
  "success": true,
  "message": "string",
  "data": { /* ... */ },
  "meta": { "timestamp": "ISO8601+09:00", "request_id": "uuid" }
}

// 401 (FR-11 신규)
{
  "success": false,
  "error": { "code": "TOKEN_REVOKED", "message": "Token has been revoked", "details": null },
  "meta": { /* ... */ }
}
```

---

## §4. DTO (스키마 변경)

### 4.1 FR-13 — Geolocation 지향성 확장 (Pydantic만)

`app/schemas/device.py:113` `Geolocation` 클래스에 `heading` 1필드 추가. 25곳 사용처(Controller/Sensor/Camera/Speaker/Enclosure/Lamp × Create/Update/Response/Nested)는 `Geolocation` 참조만 하므로 **자동 전파** — 사용처 코드 수정 0건.

```python
class Geolocation(BaseModel):
    location: Optional[str]  = Field(None, max_length=500)
    latitude: Optional[float]  = Field(None, ge=-90.0,  le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    altitude: Optional[float]  = Field(None)
    # v4.7 신규 (FR-13) — 본체 정면 방위각 (정북=0, 시계방향)
    heading: Optional[float]   = Field(
        None, ge=0.0, le=360.0,
        description="Device facing direction in degrees (0=N, 90=E, 180=S, 270=W). "
                    "PTZ dynamic rotation is handled separately via preset.",
        examples=[90.0]
    )
```

**의미 가이드** (OpenAPI description에 명시):

| 디바이스 | heading 의미 | 권장 |
|---|---|---|
| Camera | 본체 정면 (PTZ 동적 회전은 `preset.pan` 별도) | ✅ 사용 |
| Speaker | 음원 콘 중심축 | ✅ 사용 |
| Sensor (PIDS/PIR) | 감지 범위 중심축 | ✅ 사용 |
| Controller / Enclosure / Lamp | 지향성 약함 (Lamp 360°) | 선택 (`null` 가능) |

### 4.2 FR-13 Backfill 마이그레이션 (차장님 결재 반영)

**DB 스키마 변경 불필요** (6 디바이스 테이블 모두 `geolocation` JSON 컬럼). 다만 **응답 JSON 키 일관성** 보장을 위해 기존 row에 `heading: null` 명시적 추가:

```python
# alembic/versions/xxxx_v47_add_heading_backfill.py
from alembic import op

def upgrade():
    """v4.7 FR-13: 6 디바이스 테이블의 기존 row geolocation JSON에 heading:null 추가"""
    for table in ['cameras', 'speakers', 'sensors', 'controllers', 'enclosures', 'lamps']:
        op.execute(f"""
            UPDATE {table}
            SET geolocation = jsonb_set(
                geolocation::jsonb,
                '{{heading}}',
                'null'::jsonb,
                true   -- create if missing
            )::json
            WHERE geolocation IS NOT NULL
              AND NOT (geolocation::jsonb ? 'heading');
        """)

def downgrade():
    """v4.7 롤백: heading 키 제거"""
    for table in ['cameras', 'speakers', 'sensors', 'controllers', 'enclosures', 'lamps']:
        op.execute(f"""
            UPDATE {table}
            SET geolocation = (geolocation::jsonb - 'heading')::json
            WHERE geolocation IS NOT NULL
              AND geolocation::jsonb ? 'heading';
        """)
```

**효과**: 모든 디바이스 응답에 `heading` 키 명시적 존재 (`null` 또는 숫자). 매니저 strict 디코더도 호환.

### 4.3 FR-7 — 단건 14건 response_model 정정

```python
# 변경 전 (v4.6 잔존)
@router.get("/event-mappings/{eid}/cameras", response_model=dict)
@router.post(".../cameras", response_model=dict)
...

# 변경 후 (v4.7)
@router.get("/event-mappings/{eid}/cameras",
            response_model=ApiResponse[List[EventMappingCameraResponse]])
@router.post(".../cameras",
             response_model=ApiSingleResponse[EventMappingCameraResponse])
```

대상 14건 = Camera 7 (목록 GET / 단건 GET / POST / PATCH / PUT / DELETE / 독립 GET) + Speaker 7 (동일).

### 4.4 FR-11 — TokenBlacklist 신규 모델

```python
# app/models/token_blacklist.py (신규)
class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"
    jti = Column(String(36), primary_key=True)  # UUID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_type = Column(Enum("access", "refresh", name="token_type"), nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)  # TTL cleanup용
    revoked_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    reason = Column(Enum("logout", "rotation", "admin_revoke", name="revoke_reason"),
                    nullable=False)
```

Alembic 마이그레이션 `token_blacklist` 테이블 신규 생성.

---

## §5. NATS 정책

### 5.1 FR-13 영향 — 무신설

`geolocation.heading` 변경은 기존 디바이스 업데이트 경로(`PATCH /api/devices/{id}`)에 흡수 — **신규 NATS subject 불필요**. 기존 SYNC 메시지 페이로드의 `device.geolocation` 객체에 `heading` 키 자동 포함.

VMS 측 통합상황도는 SYNC 수신 시 `heading` 존재하면 부채꼴/원뿔 아이콘 회전, 없으면 점 아이콘 — **backward-compatible** (Optional 필드).

### 5.2 FR-7 / FR-11 / FR-6 영향

NATS 무영향. FR-7은 OpenAPI 메타데이터, FR-11은 인증, FR-6은 테스트.

---

## §6. ConfigChangeLog / AuditLog

### 6.1 FR-13 — ConfigChangeLog 자동 확장

기존 디바이스 PATCH 핸들러는 `before_state` / `after_state`에 `Geolocation` 객체 전체를 직렬화 — **코드 변경 없이** `heading` 필드 자동 포함.

```json
{
  "before_state": {"geolocation": {"latitude": 37.5, "longitude": 127.0, "heading": null}},
  "after_state":  {"geolocation": {"latitude": 37.5, "longitude": 127.0, "heading": 90.0}}
}
```

매니저 감사 화면에서 "방위각 0° → 90° 변경" 표시 가능.

### 6.2 FR-11 — 신규 AuditLog 액션

| Action | 발생 시점 | actor | target |
|---|---|---|---|
| `TOKEN_REVOKED_LOGOUT` | 사용자 로그아웃 | 본인 | 본인 `user_id` |
| `TOKEN_REVOKED_ROTATION` | Refresh 회전 | 본인 | 본인 `user_id` |
| `TOKEN_REVOKED_ADMIN` | 관리자 강제 회수 | admin | 대상 `user_id` |

`details`에 `jti`, `token_type`, `reason` 포함. SUCCESS만 기록.

### 6.3 FR-7 / FR-6 영향

ConfigLog/AuditLog 무영향.

---

## §7. 사이드이펙트 분석

### 7.1 FR-13 (heading)

- **Backward Compatibility**: 완전 호환 (Optional 필드)
- **DB 스키마**: 변경 0건 (JSON 컬럼)
- **Backfill 마이그레이션**: ~분 단위 (6 테이블, 인덱스 영향 없음, 수십만~수백만 row 추정 → `jsonb_set` 빠름)
- **매니저 영향**: lenient 디코더 = 즉시 호환. strict 디코더 = Backfill 후 호환

### 7.2 FR-7 (단건 14건)

- **Runtime 영향**: 0
- **OpenAPI 메타데이터만** 정정 → Swagger UI 정합화
- **위험**: 응답 dict에 스키마 외 키 있을 경우 FastAPI 자동 필터링 → 사전 pytest로 키 일치 확인

### 7.3 FR-11 (JWT 회전)

- **기존 발급 토큰**: 그대로 유효 (jti 클레임 없음 → 블랙리스트 조회 스킵)
- **신규 발급분부터** jti 추적
- **운영 위험**: Redis 다운 시 인증 차단 → 초기 DB 백엔드 + Redis는 옵션
- **TTL cleanup**: 만료 + 1d 후 cron 삭제

### 7.4 FR-6 (pytest 11건)

- **프로덕션 영향 0** (테스트 코드만)
- FR-5 dedup과 시너지로 4~5건 자동 해결 예상

---

## §8. 매니저 호환성 (4종 + .NET 사본 4곳)

| 매니저 | FR-13 영향 | FR-7 영향 | FR-11 영향 | 우선순위 |
|---|---|---|---|---|
| **GIS Manager** | Camera/DeviceGroup 지향성 마커 | 단건 CRUD 응답 타입 | 로그아웃 즉시 반영 | 중 |
| **VMS Manager** | **핵심** — 부채꼴/원뿔 아이콘 렌더링 | Camera EventMapping 단건 | 동일 | **상** |
| **NVRManager** | Lamp 360° 무관 / Server 무관 — 영향 0 | Lamp 단건 타입 | 동일 | 하 |
| **Speaker Manager** | Speaker 콘 방향 시각화 | Speaker EventMapping 단건 | 동일 | 중 |

**.NET 사본 4곳 v4.7 동기화**:
1. `Ironwall.Dotnet.Libraries.Devices` — `Geolocation` DTO에 `Heading: double?` + `[Range(0, 360)]` 검증
2. `Ironwall.Dotnet.Libraries.Restful` — 단건 14건 응답 타입 일치 확인
3. `Ironwall.Dotnet.Libraries.Authentication` — `JwtPayload`에 `jti` 클레임 파싱 (서버측 검증만)
4. `Central UI Common Models` — `Geolocation.Heading` 바인딩 + UI 단위(°) 표시

`docs/v45_sync_guide.md` → `docs/v47_sync_guide.md`로 갱신.

---

## §9. 변경 파일 인벤토리

### 9.1 코드 (서버)

| 파일 | 변경 | FR |
|---|---|---|
| `app/schemas/device.py:113~139` (`Geolocation`) | `heading` 필드 추가 | FR-13 |
| `app/routers/event_mapping_cameras.py` | 7 단건 핸들러 `response_model` | FR-7 |
| `app/routers/event_mapping_speakers.py` | 동일 | FR-7 |
| `app/routers/event_mapping_lamps.py` | 동일 | FR-7 |
| `app/models/token_blacklist.py` (신규) | TokenBlacklist 모델 | FR-11 |
| `app/utils/auth.py` | jti 클레임 + verify_token 블랙리스트 조회 | FR-11 |
| `app/routers/auth.py` | `/logout` 엔드포인트에 blacklist insert | FR-11 |
| `app/services/audit_service.py` | TOKEN_REVOKED_* 액션 추가 | FR-11 |

### 9.2 인프라 / DB

| 파일 | 변경 | FR |
|---|---|---|
| `alembic/versions/xxxx_v47_add_heading_backfill.py` (신규) | 6 테이블 geolocation에 heading:null Backfill | FR-13 |
| `alembic/versions/xxxx_v47_create_token_blacklist.py` (신규) | token_blacklist 테이블 신규 | FR-11 |
| `.env.example` | `TOKEN_BLACKLIST_BACKEND=db` (기본) | FR-11 |

### 9.3 명세서

| 파일 | 변경 | FR |
|---|---|---|
| `GOP_Restful_Api_연동설계.md` | §디바이스 공통 `Geolocation` 표에 heading 행 | FR-13 |
| 동 파일 | §EventMapping 단건 14건 "Response Schema: ApiSingleResponse[T]" | FR-7 |
| 동 파일 | §인증 절 토큰 회전 정책 | FR-11 |
| 동 파일 | 변경 이력 v4.7 행 + 푸터 일자 | 모든 FR |

### 9.4 테스트

| 파일 | 변경 | FR |
|---|---|---|
| `tests/test_event_mapping_*_bulk.py` 11건 | envelope/URL/멱등 정합 | FR-6 |
| `tests/test_geolocation_heading.py` (신규) | heading 범위 검증 (0~360, None 허용) | FR-13 |
| `tests/test_event_mapping_single_response_model.py` (신규) | 단건 14건 envelope 검증 | FR-7 |
| `tests/test_jwt_blacklist.py` (신규) | jti 블랙리스트 + 로그아웃 즉시 무효화 | FR-11 |

### 9.5 가이드

| 파일 | 변경 |
|---|---|
| `docs/v47_sync_guide.md` (신규, v45_sync_guide.md 갱신) | .NET 사본 4곳 v4.7 동기화 안내 |

---

## §10 테스트 계획

### 10.1 v4.6 잔존 11건 처리 (FR-6 후속)

v4.6에서 envelope key 일부 sed 정합화 완료, FR-5 dedup 적용으로 자동 통과 기대분도 포함. v4.7에서는 잔존 11건을 envelope key / URL prefix / 멱등 가정 3축으로 분류하여 테스트 fixture만 정정한다(라우터 코드 변경 없음).

| # | 테스트 케이스 | 잔존 원인 | v4.7 처리 |
|---|---|---|---|
| 1 | cameras `log_config_change camera_ids` | after_state 키 `config_ids` vs 테스트 `camera_ids` 잔존 | 테스트 envelope key → `config_ids` 일괄 통일 |
| 2 | cameras `404 DELETE URL` | `/cameras/bulk` (테스트) vs `/cameras` (라우터) | 테스트 URL 정정 + 명세 §부록 URL 표 재확인 |
| 3 | cameras `skip_duplicates` 멱등 가정 | FR-5 적용 후에도 응답 envelope `skipped_in_request` 키 미반영 | 테스트 fixture key 정합 |
| 4~7 | speakers 4건 | cameras와 동형 (file_group_id 키, dup, speaker_ids, URL) | 동일 처리 (envelope/URL/멱등) |
| 8 | lamps `log_config_change lamp_ids` | lamp_ids vs config_ids 잔존 | 테스트 key 통일 |
| 9 | lamps `404 DELETE URL` | URL 정합 부재 | 테스트 URL 정정 |
| 10 | lamps `skip_duplicates` 멱등 가정 | v4.6 FR-5 적용 후에도 fixture 미정합 | 테스트 fixture key 정합 |
| 11 | shared `bulk_create_with_empty_items` envelope | `failed_items` 키 누락 | FR-7 단건 14건 response_model 강제로 자동 검증 부수효과 |

### 10.2 신규 추가 테스트 (10건)

| 테스트 | FR | 시나리오 |
|---|---|---|
| `test_geolocation_heading.py::test_should_accept_heading_when_in_valid_range` | FR-13 | heading=0, 90, 180, 270, 359.9 → 200 OK + 응답에 echo |
| `test_geolocation_heading.py::test_should_reject_heading_when_below_zero` | FR-13 | heading=-1 → 422 Pydantic ge 위반 |
| `test_geolocation_heading.py::test_should_reject_heading_when_above_360` | FR-13 | heading=360.0 → 422 (exclusive max, 360°=0°와 동치) |
| `test_geolocation_heading.py::test_should_allow_heading_none_when_omitted` | FR-13 | heading 키 부재 / null → 200 + 응답 null (backward-compatible) |
| `test_geolocation_heading.py::test_should_apply_heading_to_camera_speaker_sensor` | FR-13 | 3종 디바이스 동시 검증 (Camera/Speaker/Sensor — Controller/Enclosure/Lamp는 의미 없음) |
| `test_single_response_schema.py::test_should_return_api_single_response_envelope_for_14_endpoints` | FR-7 | 14건 단건 API 응답에 `success/data/timestamp` 3-key 검증 |
| `test_single_response_schema.py::test_openapi_should_expose_specific_schema_not_additional_properties` | FR-7 | OpenAPI JSON dump → `additionalProperties:true` 부재 검증 |
| `test_jwt_rotation.py::test_should_reject_revoked_token_after_logout` | FR-11 | login → logout → revoked jti로 API 호출 → 401 |
| `test_jwt_rotation.py::test_should_allow_refresh_with_valid_refresh_token` | FR-11 | refresh 회전 후 새 access 발급 + 이전 access는 블랙리스트 |
| `test_jwt_rotation.py::test_should_expire_blacklist_entry_after_token_natural_expiry` | FR-11 | jti TTL = 토큰 자연 만료 시각 + 1h (DB cron GC) |

### 10.3 회귀 기준

본 차수 적용 후:
- pytest **80/80** 통과 (기존 70 + 신규 10)
- 시뮬레이션 19+α 시나리오 100% 통과 (heading 필드 추가에 따른 fixture 갱신 포함)
- OpenAPI 21 엔드포인트 (7 Bulk + 14 단건) 모두 구체 schema 노출 (`additionalProperties:true` 0건)
- Geolocation 25개 Pydantic 사용처 모두 heading 필드 옵션 노출 (Swagger UI 확인)
- JWT 토큰 회전: 로그아웃 후 회수된 access/refresh로 API 호출 시 100% 401 응답
- 시작 컨테이너 healthy + Image rebuild 후 정합 검증

---

## §11 명세 패치 (Edit Pair)

본 PRD 결재 후 본 메인이 `GOP_Restful_Api_연동설계.md` v4.6 → v4.7로 갱신할 주요 Edit Pair.

| # | 영역 | 변경 |
|---|---|---|
| EP-1 | §디바이스 공통 Geolocation 필드 표 (L1425, L1532, L1645 등 사용처 표) | `heading` 행 추가 — 타입 `float`, 필수 N, 기본값 `null`, 범위 `0 ≤ heading < 360`, 단위 `도(°)`, 설명 `디바이스 정면 방위각 (정북=0, 시계방향). Camera/Speaker/Sensor에만 의미. v4.7 신규` |
| EP-2 | §디바이스 응답/요청 예시 JSON (L1384-L1388, L1404-L1409, L1444-L1449 등) | `geolocation` 객체에 `"heading": 135.0` 라인 추가 (Camera/Speaker/Sensor 예시 한정, Controller/Enclosure/Lamp는 `null` 유지) |
| EP-3 | §7.3.x / §7.5.x 단건 14건 본문 (Camera/Speaker/Lamp × 독립 GET/목록/단건/POST/PATCH/PUT/DELETE) | 각 엔드포인트에 `**Response Schema**: ApiSingleResponse[T]` 라인 명시 (T=EventMappingCameraResponse 등). 기존 `dict` 표기 제거 |
| EP-4 | §6.x JWT 인증 절 | 신규 하위 절 `**6.x.y 토큰 회전 및 회수 정책 (v4.7 신규)**` 추가 — (1) 로그아웃 시 access/refresh jti 블랙리스트 등록, (2) refresh 회전 시 이전 access 자동 회수, (3) 블랙리스트 저장소: DB `token_blacklist` 테이블 (TTL=토큰 자연 만료 + 1h, daily GC cron), (4) 검증 미들웨어가 매 요청 시 jti 조회 |
| EP-5 | §변경 이력 표 | v4.7 행 신규 추가 — `2026-06-25 \| v4.7 \| FR-13 Geolocation heading 추가, FR-7 단건 14건 ApiSingleResponse 명시, FR-11 JWT 회전(jti 블랙리스트), FR-6 잔존 11건 정합 \| 이기호 차장` |
| EP-6 | 푸터 | `**문서 버전**: v4.6` → `v4.7`, 일자 `2026-06-23` → `2026-06-25` |

**검증 절차**: EP 적용 후 (1) Swagger UI에서 Geolocation 스키마에 heading 필드 노출 확인, (2) 14건 단건 응답 모델이 구체 클래스로 노출되는지 확인(`additionalProperties:true` 부재), (3) §변경 이력과 푸터 버전 일치 확인.

---

## §12 공수 산정

본 차수는 신규 FR-13(지향성) 1건 + v4.6 분리 잔존 3건(FR-7/11/6)을 한 차수로 통합 처리한다. 코드/테스트/명세 3축으로 분해한 공수는 아래와 같다.

| FR | 항목 | 코드 | 테스트 | 명세 | 소계 |
|---|---|---|---|---|---|
| FR-13 | Geolocation.heading 추가 | 30분 | 30분 | 30분 | 1.5h |
| FR-7 | 단건 14건 response_model 정정 | 1h | 30분 | 15분 | 1.75h |
| FR-11 | JWT jti 블랙리스트/회수 | 3h | 1h | 30분 | 4.5h |
| FR-6 | pytest envelope 잔존 11건 | - | 1.5h | - | 1.5h |
| **합계** | | **~4.5h** | **~3.5h** | **~1.25h** | **~9.25h (1.2일)** |

### 세부 분해

- **FR-13**: `app/schemas/device.py:113` Geolocation에 `heading: float | None = Field(None, ge=0, lt=360)` 1필드 추가. 25곳 사용처는 nested 상속으로 자동 전파 — 수정 없음. 테스트는 경계값(0/359.99/360 reject/-1 reject) 4케이스. 명세는 §3 공통 스키마 + §부록 변경이력만 갱신.
- **FR-7**: 14개 엔드포인트의 `response_model=dict` → 각 도메인 Response 모델로 교체. 단순 치환이라 코드 1h. 테스트는 OpenAPI schema dump 1건 + 14건 응답 shape 회귀 1건.
- **FR-11**: `token_blacklist` 테이블 신규(jti/user_id/expires_at/revoked_at), `auth.py`에 검증 hook 추가, `/auth/logout`에 INSERT, 만료 토큰 청소 cron(daily). Redis 미도입 결정 — DB 백엔드로 시작. 테스트는 로그아웃 후 토큰 거부 + jti 재사용 거부 + 만료 자동 GC 3건.
- **FR-6**: v4.6 sed 후 잔존 11건 — envelope key 통일(`data`/`items`/`meta`) + URL prefix(`/api/v1`) + 멱등성 가정(DELETE 2회). 코드 변경 없음 — 테스트 fixture만 정정.

## §13 리스크 및 완화

| ID | 리스크 | 영향 | 확률 | 완화 |
|---|---|---|---|---|
| R1 | FR-13: 매니저 측 .NET DTO 재생성 필요 | 중 | 높음 | OpenAPI codegen 자동 — 매니저에 sync guide 즉시 발송 |
| R2 | FR-11: Redis vs DB 백엔드 선택 | 중 | 중 | 단순 시작 원칙 — DB(MySQL) 채택, Redis는 v5.x 부하 분산 시 재검토 |
| R3 | FR-7: envelope에 `meta` 자동 추가(v4.5 PR-D 부가효과) | 낮 | 높음 | 매니저 lenient JSON 디코더 적용 — `meta` 미사용 시 무시 처리 권고 |
| R4 | FR-13: 데이터 마이그레이션 | 낮 | 낮 | `geolocation` JSON 컬럼이라 DDL 불필요 — 기존 row는 `heading` 누락(NULL 동등) |
| R5 | v4.7 작업 중 매니저 통합 병행 | 중 | 높음 | sync guide 즉시 발송 + v4.7 머지 시점 명세 v4.7 동시 배포 |
| R6 | FR-11 logout 미호출 클라이언트 잔존 토큰 | 중 | 중 | Access 24h 자연 만료 허용 + 강제 회수는 admin API 별도 제공 |

R2/R3는 의사결정 사안 — 본 PRD 결재 시 차장님 확정 필요.

## §14 롤백 정책

### 14.1 단위 원칙

- **FR별 독립 PR**: PR-47-13(heading), PR-47-7(response_model), PR-47-11(JWT 회전), PR-47-6(pytest) — 4건 분리 머지로 부분 롤백 가능.
- **commit 단위 revert**: 각 PR은 코드/테스트/명세 3 commit으로 구성, `git revert <sha>` 단독 적용 가능.
- **롤백 태그**: `pre-v47` (HEAD=6a2430a, v4.6 docs commit 직후, 본 차수 직전 상태)에서 본 차수 진입 전 상태로 즉시 복원.

### 14.2 데이터 영향

| FR | 스키마 변경 | 롤백 시 처리 |
|---|---|---|
| FR-13 | 없음 (JSON 컬럼 내 키 추가) | 무동작 — `heading` 키는 잔존 가능, 신 코드 미사용 |
| FR-7 | 없음 (응답 shape만) | 무동작 |
| FR-11 | `token_blacklist` 테이블 신규 | `DROP TABLE token_blacklist;` — 사용자 영향 없음 (재로그인만) |
| FR-6 | 없음 (테스트 fixture) | 무동작 |

### 14.3 롤백 절차

1. 장애 인지 시 `git revert <PR-merge-sha>` 또는 `git reset --hard pre-v47` (개발 환경 한정).
2. FR-11만 영향이면 `token_blacklist` DROP + auth.py revert 단독 적용.
3. Docker Image 재빌드 + 명세 v4.7 → v4.6 회수 공지(매니저 측).
4. 회수 후 24h 내 원인 분석 보고 + v4.7.1 재투입 계획 수립.

### 14.4 부분 머지 시나리오

FR-11 JWT 회전이 가장 무거우므로(4.5h, 전체 49%) 다음 순서를 권고한다.

1. **1차 머지**: FR-13 + FR-7 + FR-6 (~4.75h, 저위험) → 명세 v4.7-rc1.
2. **2차 머지**: FR-11 단독 (~4.5h, 보안 핵심) → 명세 v4.7 정식.

이 분할로 매니저 통합은 1차 머지 직후 시작 가능하며 FR-11 지연 시에도 v4.7-rc1로 부분 배포 가능하다.

---

## §15. 구현 스케치

### 15.1 FR-13 — Geolocation.heading (가장 단순)

```python
# app/schemas/device.py:113~ Geolocation 클래스
class Geolocation(BaseModel):
    """좌표/방향 정보 — v4.7 FR-13에서 heading 추가"""
    location: Optional[str] = Field(None, max_length=500, ...)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, ...)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, ...)
    altitude: Optional[float] = Field(None, ...)
    # v4.7 FR-13 신설
    heading: Optional[float] = Field(
        None, ge=0.0, le=360.0,
        description="Device facing direction in degrees (0=N, 90=E, 180=S, 270=W). "
                    "PTZ dynamic rotation is handled separately via preset.",
        examples=[135.0]
    )
    model_config = ConfigDict(from_attributes=True)
```

25곳 사용처(Controller/Sensor/Camera/Speaker/Enclosure/Lamp × Create/Update/Response/Nested)는 `Geolocation` 참조만 하므로 **자동 전파** — 수정 0건.

### 15.2 FR-13 — Backfill 마이그레이션 (차장님 결재 반영)

```python
# alembic/versions/xxxx_v47_add_heading_backfill.py
"""v4.7 FR-13: 기존 디바이스 geolocation JSON에 heading:null 추가"""
from alembic import op

revision = "xxxx_v47_heading_backfill"
down_revision = "<v46_last>"

DEVICE_TABLES = ['cameras', 'speakers', 'sensors',
                 'controllers', 'enclosures', 'lamps']

def upgrade():
    for table in DEVICE_TABLES:
        op.execute(f"""
            UPDATE {table}
            SET geolocation = jsonb_set(
                geolocation::jsonb,
                '{{heading}}',
                'null'::jsonb,
                true   -- create if missing
            )::json
            WHERE geolocation IS NOT NULL
              AND NOT (geolocation::jsonb ? 'heading');
        """)

def downgrade():
    for table in DEVICE_TABLES:
        op.execute(f"""
            UPDATE {table}
            SET geolocation = (geolocation::jsonb - 'heading')::json
            WHERE geolocation IS NOT NULL
              AND geolocation::jsonb ? 'heading';
        """)
```

**예상 소요**: 6 테이블 × 수십만 row, 인덱스 영향 0, 트랜잭션 1개로 수십 초 내 완료.

### 15.3 FR-7 — 단건 14건 response_model

```python
# app/routers/event_mapping_cameras.py 등
from app.schemas.common import ApiSingleResponse, ApiResponse

@router.get(
    "/{mapping_id}/cameras",
    response_model=ApiResponse[EventMappingCameraResponse],  # 페이지
    responses={404: {"description": "Event mapping not found"}},
)
def list_event_mapping_cameras(...): ...

@router.get(
    "/{mapping_id}/cameras/{config_id}",
    response_model=ApiSingleResponse[EventMappingCameraResponse],
    responses={404: {"description": "Camera config not found"}},
)
def get_event_mapping_camera(...): ...

# POST/PATCH/PUT/DELETE/독립 GET 동일 패턴
```

### 15.4 FR-11 — JWT jti 블랙리스트

```python
# app/models/token_blacklist.py (신규)
from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, Index
from app.db.base import Base
import datetime

class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"

    jti = Column(String(36), primary_key=True)   # UUID hex
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_type = Column(Enum("access", "refresh", name="token_type"),
                        nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)   # TTL cleanup
    revoked_at = Column(DateTime, nullable=False,
                        default=datetime.datetime.utcnow)
    reason = Column(Enum("logout", "rotation", "admin_revoke",
                          name="revoke_reason"), nullable=False)

    __table_args__ = (
        Index("ix_tb_user_revoked", "user_id", "revoked_at"),
    )

# app/utils/auth.py
import uuid

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    to_encode["jti"] = str(uuid.uuid4())   # v4.7 FR-11
    to_encode["exp"] = datetime.utcnow() + (expires_delta or timedelta(hours=24))
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY,
                      algorithm=settings.JWT_ALGORITHM)

def verify_token(token: str, db: Session) -> dict:
    payload = jwt.decode(token, settings.JWT_SECRET_KEY,
                         algorithms=[settings.JWT_ALGORITHM])
    jti = payload.get("jti")
    if jti:
        # v4.7 FR-11: 블랙리스트 조회 (인덱스 hit, O(1) PK lookup)
        revoked = db.query(TokenBlacklist).filter(
            TokenBlacklist.jti == jti
        ).first()
        if revoked:
            raise HTTPException(
                status_code=401,
                detail={"code": "TOKEN_REVOKED",
                        "message": f"Token revoked ({revoked.reason})"}
            )
    return payload

# app/routers/auth.py (신규 logout)
@router.post("/logout")
def logout(
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    payload = jwt.decode(credentials.credentials, settings.JWT_SECRET_KEY,
                        algorithms=[settings.JWT_ALGORITHM])
    db.add(TokenBlacklist(
        jti=payload["jti"],
        user_id=current_user.id,
        token_type="access",
        expires_at=datetime.utcfromtimestamp(payload["exp"]),
        reason="logout",
    ))
    # AuditLog: TOKEN_REVOKED_LOGOUT
    log_action(action_type="TOKEN_REVOKED_LOGOUT", ...)
    db.commit()
    return {"success": True, "message": "Logged out"}
```

### 15.5 FR-6 — pytest 11건 정합

```python
# tests/test_event_mapping_cameras_bulk.py 등
# Before
assert "camera_ids" in body["data"]["after_state"]

# After (envelope key 공통화)
assert "config_ids" in body["data"]["after_state"]

# URL 정정
# Before: client.post(f"/api/event-mappings/{eid}/cameras/bulk", ...)
# After:  client.post(f"/api/integrations/event-mappings/{eid}/cameras/bulk", ...)

# 멱등 가정 case — FR-13 dedup으로 자동 통과 (별도 변경 불요)
```

### 15.6 신규 테스트 (4건)

```python
# tests/test_geolocation_heading.py (FR-13)
def test_should_serialize_heading_when_set(test_db):
    cam = Camera(geolocation={"latitude": 38.0, "heading": 90.0}, ...)
    response = Geolocation.model_validate(cam.geolocation)
    assert response.heading == 90.0

def test_should_reject_heading_out_of_range():
    with pytest.raises(ValidationError):
        Geolocation(heading=361.0)

# tests/test_jwt_blacklist.py (FR-11)
def test_should_reject_revoked_token(client, test_db):
    tok = create_access_token({"sub": "admin"})
    client.post("/api/auth/logout",
                headers={"Authorization": f"Bearer {tok}"})
    r = client.get("/api/devices/cameras",
                   headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "TOKEN_REVOKED"
```

---

## §16. 변경 이력

| 버전 | 일자 | 작성자 | 변경 내용 |
|------|------|--------|----------|
| v1.0 | 2026-06-23 | 이기호 차장 | 신규 작성 — v4.6 마감 직전 차장님 도메인 지적(`Geolocation` 지향성 누락)으로 FR-13 신설 + v4.6 P2 분리 3건(FR-6/7/11) 통합. 매니저 통합 1단계 완성 + 보안 강화 동시 종결. Workflow `wgijej47s` 6 agent 풀로 16 섹션 병렬 작성, 본 메인이 Backfill 마이그레이션 항목 차장님 결재 반영 후 §4/§9/§15에 통합. |

---

## 부록 A. 관련 산출물

| 파일 | 설명 |
|---|---|
| `docs/workflow_prd_v47/s01~s06.md` | 6 agent raw 결과 |
| `docs/PRD_BulkAPI_PostMortem_v4.6.md` | v4.6 PRD (선행 차수) |
| `docs/PRD_BulkAPI_Spec_Sync_v4.4.md` | v4.4 PRD (베이스) |
| `docs/v45_sync_guide.md` | .NET 사본 동기화 가이드 (v4.7 갱신 예정) |

## 부록 B. v4.8+ 분리 항목

| 항목 | 사유 |
|---|---|
| `tilt` (-90~90°) + `fov` (0~360°) | 3D 시각화 + Camera 시야각 — v4.7 2D 통합상황도 단계에선 불요 |
| `roll` (-180~180°) | 거의 0, PTZ preset 영역 |
| PTZ 동적 회전 라우터 분리 | `/api/cameras/{id}/presets` 별도 |
| Redis 백엔드 TokenBlacklist | 초기 DB로 시작, 부하 발생 시 마이그레이션 |

## 부록 C. 결재 체크리스트

- [ ] v4.7 차수 명명 동의 (v4.8 분리 안 함)
- [ ] FR-13 범위 — heading만 (tilt/fov는 v4.8) 동의
- [ ] **Backfill 마이그레이션 포함** 동의 (✅ 차장님 결재 완료)
- [ ] FR-11 백엔드 선택 — DB (Redis는 v4.8+) 동의
- [ ] 분할 머지 — 1차 (FR-13/7/6) → 2차 (FR-11) 동의
- [ ] 매니저 통보 발송 일자
- [ ] 롤백 태그 `pre-v47` (HEAD=6a2430a) 사전 생성 동의 (✅ 생성 완료)

---

**문서 버전**: v1.0
**최종 업데이트**: 2026-06-23
