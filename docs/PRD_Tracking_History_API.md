# PRD: Tracking History API (추적 이력 영속·조회 API + NATS 인제스트)

- **Version**: 1.0
- **Date**: 2026-06-26
- **Status**: Draft
- **Target**: API 서버 (Python FastAPI) + 신규 독립 워커 `gis-ingest`
- **Language/Framework**: Python / FastAPI / SQLAlchemy / asyncpg / PostgreSQL (테스트 SQLite 호환)
- **연동 SoT(계약)**: `docs/Gop_Message_Broker_연동설계.md §8.3.7 TRACKING_STATUS` (**신버전 `targets[]`** — 아래 §1.2)
- **소비 클라(.NET)**: `Ironwall.Dotnet.Libraries` PRD `Tracking_GIS_Visualization_Playback` §8 (서버 API 구성 가이드), `ITrackingApiService` GET 호출

---

## 1. Background (배경)

### 1.1 현재 상황
- GIS 추적(Tracking)은 NATS subject `sensorway.{부대ID}.gis.tracking-status` 한 채널로 **N개 관제 스테이션에 동시 브로드캐스트**된다. 라이브 오버레이는 각 클라가 NATS 직수신으로 표시하므로 영향이 없다 — **영속/Playback만 본 PRD의 대상**이다.
- 현재 GOP REST API(v4.10)에는 **추적 이력 엔드포인트가 전무**하다(명세서 §5~§10 어디에도 없음). 클라는 임시로 로컬 DB에 자체 저장 중이나, 다중 스테이션에서 N배 중복·스테이션별 이력 분기·오프라인 공백이 발생한다.
- **결정(.NET·서버 합의)**: 추적 이력은 **서버가 NATS를 단일 구독·저장**하고 클라는 **read-only GET**으로 기간별 청크를 조회해 Playback 한다. 클라 POST는 배제(N배 중복 회피).

### 1.2 ★ 메시지 계약 — 신버전 `targets[]` 채택 (선결 동기화)
`TRACKING_STATUS §8.3.7`은 **두 버전**이 존재하며 본 PRD는 **신버전을 권위로 삼는다**:

| | 구버전(서버 사본 — stale) | **신버전(.NET 사본 — 채택)** |
|---|---|---|
| 구조 | 단일 `target` (카메라당 1개) | **`targets[]` 배열** |
| `track_id` | ❌ | ✅ **Y** — 객체 식별 키 |
| `observed_at` | ❌ | ✅ **Y** — 관측 시각(UTC ms), 역전 방지 |
| `threat_level` | ❌ | ✅ Y (`NORMAL`/`CAUTION`/`THREAT`) |
| `ttl_sec`·`frame_w/h` | ❌ | ✅ |

> **선결 조건**: 서버 사본 `docs/Gop_Message_Broker_연동설계.md §8.3.7`을 신버전(`targets[]`)으로 **동기화**해야 하며(Phase 0), 실제 발행자 **AiAnalysis가 신버전 포맷을 발행하도록 합의**가 필요하다(`PROJECT_SCHEDULE_잔여핵심작업_상세.md:476` 미결 항목). 합의 전까지 인제스트 워커는 신버전 스키마를 가정하되, **방어적 파싱**(구버전 단일 `target` 수신 시 1개짜리 `targets[]`로 정규화)을 포함한다.

### 1.3 신버전 `TRACKING_STATUS` body (인제스트 입력)
```json
{
  "cmd": "TRACKING_STATUS", "from": "AiAnalysis",
  "body": {
    "camera_id": 201, "tracking": "active",
    "ttl_sec": 5, "frame_width": 1280, "frame_height": 720,
    "targets": [
      {
        "track_id": "cam201-1738750245-007",
        "label": "person", "threat_level": "THREAT", "confidence": 0.92,
        "observed_at": "2026-02-05T10:30:00.000Z",
        "location": { "latitude": 38.1235, "longitude": 127.5680, "distance_m": 120.5 },
        "bbox": [150,220,60,120], "thumbnail": "http://.../frame_001.jpg"
      }
    ]
  }
}
```
- `tracking == "active"` → `targets[]`의 각 타겟을 1행으로 영속.
- `tracking == "lost"|"idle"` → `targets[]` 빈 배열 가능 → 저장 행 없음(세션 종료 신호로만 활용).

---

## 2. Goals (목표)

### 핵심 목표
- [ ] 서버가 `TRACKING_STATUS`를 **단일 구독·멱등 저장**(독립 워커 `gis-ingest`)
- [ ] 클라가 **기간별 청크**로 과거 추적점을 조회(`GET /api/tracking/points`, cursor 페이지네이션)
- [ ] Playback 타임라인용 **세션 목록**(`GET /api/tracking/sessions`)
- [ ] Playback 진입 게이팅용 **헬스체크**(`GET /api/tracking/health`)
- [ ] 5-싱크(명세서·코드·Swagger·이미지·컨테이너) + 일일버전(v4.11) 준수

### 비목표 (Out of Scope)
- 클라(.NET) 측 `ITrackingApiService`/Playback 구현 — 별도(.NET PRD §P4/P5)
- 라이브 오버레이 경로 변경 — NATS 직수신 그대로(영향 없음)
- MP4 내보내기, 실시간 WebSocket 푸시
- 권한 세분화(추적 이력 RBAC) — 기존 JWT 인증만 적용(읽기)

---

## 3. 프로젝트 구조 참조 (코드 grounding)

### 3.1 도메인 추가 패턴 (audit_logs 미러)
| 레이어 | 기준 파일 | 신규 |
|---|---|---|
| Model (SQLAlchemy ORM) | `app/models/audit_log.py` | `app/models/tracking.py` |
| Schema (Pydantic v2) | `app/schemas/audit_log.py` | `app/schemas/tracking.py` |
| Router (APIRouter) | `app/routers/audit_logs.py` | `app/routers/tracking.py` |
| 등록 | `app/main.py:36` import / `:582` include_router / `:61` tags_metadata | 동일 패턴 추가 |
| 응답 래퍼 | `app/schemas/common.py` `ApiResponse[T]`/`ApiSingleResponse[T]`/`PaginationMeta`/`KSTDatetime` | `CursorMeta` 추가 |
| 인증 | `app/routers/auth.py:130` `get_current_user_optional` | `/points`·`/sessions`에 적용, `/health` 공개 |

- **DB 접근**: SQLAlchemy ORM + per-request `Session`(`get_db()` `app/dependencies.py:9`). 테이블은 startup `Base.metadata.create_all`(`app/utils/init_db.py:21`)이 **신규 테이블 자동 생성**. (마이그레이션 SQL은 명시·인덱스·운영용.)
- **cursor/keyset 페이지네이션은 repo에 전무** → 신규 패턴. `ApiResponse.pagination`은 `PaginationMeta`(page/limit/total) 전용이므로 **`CursorMeta`**(next_cursor/limit/has_more)를 신설해 `meta` 곁에 실어 보낸다.

### 3.2 인제스트 워커 패턴 (db_monitor 미러)
- 기존 `db_monitor/`(독립 compose 서비스)는 `asyncpg` LISTEN + `nats-py` publish 브리지. **본 워커는 역방향**: NATS subscribe → asyncpg INSERT.
- `nats-py>=2.6.0`·`asyncpg>=0.29.0`는 **이미 설치**. 브로커는 외부 docker망 `nats-core_nats-network`(`nats-server-01:4222`)로 연결.
- ⚠ 기존 `app/`(FastAPI)에는 **인프로세스 백그라운드 워커 패턴이 없음**(lifespan만). 그래서 **독립 서비스 `gis-ingest`**로 분리(결정 D3) → 크래시/백프레셔 격리, api-server 이미지 무변경.

### 3.3 스키마 규약
- PK: 고볼륨 시계열 → `BIGSERIAL`(선례 `token_blacklist`).
- 타임스탬프: `TIMESTAMPTZ`(UTC 저장, 명세 정본 규약).
- 멱등성: repo는 `ON CONFLICT` 미사용(IF NOT EXISTS/WHERE 가드로 달성)이나, **인제스트는 raw asyncpg `INSERT ... ON CONFLICT (track_id, observed_at) DO NOTHING`**(db_monitor와 같은 raw 경로 → ORM 무관, 신규지만 허용).
- ⚠ `threat_level`은 외부(AiAnalysis) 입력 → **`VARCHAR(16)` + 앱 허용셋 검증**(audit 교훈: 외부 enum은 strict 금지). 전용 `CREATE TYPE`은 회피.
- `camera_id`는 **FK 미설정(plain INTEGER index)** — 이력은 카메라 자산 수명에 독립해야 함(CASCADE면 카메라 삭제 시 이력 소실, SET NULL이면 링크 소실). 설계 결정으로 비-FK 유지.

---

## 4. DB 설계

### 4.1 `track_points` 테이블
```
track_points
├── id              BIGSERIAL PK
├── camera_id       INTEGER     NOT NULL           -- body.camera_id (비-FK, index)
├── track_id        VARCHAR(64) NOT NULL           -- targets[].track_id
├── label           VARCHAR(32)                    -- targets[].label (person/car/vehicle/animal)
├── threat_level    VARCHAR(16)                    -- targets[].threat_level (NORMAL/CAUTION/THREAT, tolerant)
├── latitude        DOUBLE PRECISION NOT NULL      -- targets[].location.latitude
├── longitude       DOUBLE PRECISION NOT NULL      -- targets[].location.longitude
├── distance_m      DOUBLE PRECISION               -- targets[].location.distance_m (nullable)
├── confidence      DOUBLE PRECISION               -- targets[].confidence (nullable)
├── observed_at     TIMESTAMPTZ NOT NULL           -- targets[].observed_at (keyset 정렬키)
├── tracking_state  VARCHAR(16)                    -- body.tracking (active 고정; 세션경계 참고)
├── speed_mps       DOUBLE PRECISION               -- (선택) 서버 계산/미저장 시 클라 재계산
├── session_seq     INTEGER                        -- (선택) 세션 시퀀스
└── created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP   -- 인제스트 시각

제약/인덱스
├── UNIQUE (track_id, observed_at)                 -- 멱등 인제스트 (재전송/다중 안전)
├── INDEX  idx_track_points_observed_at (observed_at)          -- keyset 페이지네이션
└── INDEX  idx_track_points_camera_observed (camera_id, observed_at)  -- 카메라 필터 조회
```

### 4.2 세션(`/sessions`)은 **파생 집계**(별도 테이블 없음)
- `GROUP BY camera_id, track_id` 후 `MIN(observed_at)=start_at`, `MAX(observed_at)=end_at`, `COUNT(*)=point_count`로 산출. 별도 `track_sessions` 테이블은 v1 미도입(중복 영속·동기화 부담 회피).

### 4.3 보존정책 (retention)
- 기본 7일 경과분 청크 DELETE(append-only 시계열, 볼륨 작음). v1은 **마이그레이션에 purge 함수만 정의**하고 스케줄 호출은 운영 선택(또는 후속 cron). 추적 테이블은 **audit append-only 트리거 대상 아님**(자유 삭제 가능).

---

## 5. API 설계

### 5.1 추적점 구간 조회 (Playback 핵심)
```
GET /api/tracking/points
```
**Query Parameters**:
| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|:--:|---|---|
| `from` | datetime(ISO8601) | NO | - | 구간 시작(observed_at ≥) |
| `to` | datetime(ISO8601) | NO | - | 구간 종료(observed_at ≤) |
| `camera_id` | int | NO | - | 카메라 필터 |
| `track_id` | string | NO | - | 단일 트랙 필터 |
| `cursor` | string | NO | - | keyset 커서(직전 응답 `next_cursor`) |
| `limit` | int | NO | 1000 | 페이지 크기(최대 5000) |

**정렬**: `observed_at ASC, id ASC`. **페이지네이션**: keyset — `cursor`는 `base64("{observed_at_iso}|{id}")`, 조건 `(observed_at, id) > (cursor_ts, cursor_id)`. `limit+1` 조회로 `has_more`·`next_cursor` 산출.

**Response (200 OK)** — `ApiResponse[list[TrackPointResponse]]` + `meta.cursor`:
```json
{
  "success": true,
  "message": "Track points retrieved",
  "data": [
    {
      "id": 100123, "camera_id": 201, "track_id": "cam201-1738750245-007",
      "label": "person", "threat_level": "THREAT",
      "latitude": 38.1235, "longitude": 127.5680, "distance_m": 120.5,
      "confidence": 0.92, "observed_at": "2026-02-05T19:30:00.000+09:00",
      "speed_mps": null, "session_seq": null
    }
  ],
  "meta": {
    "timestamp": "...", "request_id": "...",
    "cursor": { "next_cursor": "MjAyNi0wMi0wNS4uLnwxMDAxMjM=", "limit": 1000, "has_more": true }
  }
}
```
**인증**: `Depends(get_current_user_optional)`(AUTH_MODE=token이면 401, public이면 통과).

---

### 5.2 세션 목록 (타임라인)
```
GET /api/tracking/sessions
```
**Query Parameters**:
| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---|---|:--:|---|---|
| `from` | datetime | NO | - | 세션 겹침 구간 시작 |
| `to` | datetime | NO | - | 세션 겹침 구간 종료 |
| `camera_id` | int | NO | - | 카메라 필터 |

**Response (200 OK)** — `ApiResponse[list[TrackSessionResponse]]`:
```json
{
  "success": true, "message": "Track sessions retrieved",
  "data": [
    { "track_id": "cam201-1738750245-007", "camera_id": 201, "label": "person",
      "start_at": "2026-02-05T19:30:00+09:00", "end_at": "2026-02-05T19:34:11+09:00",
      "point_count": 251, "session_seq": null }
  ],
  "meta": { "timestamp": "...", "request_id": "..." }
}
```
**구현**: `GROUP BY camera_id, track_id`(+`label`은 `MAX`/대표값) · `MIN/MAX(observed_at)` · `COUNT(*)`. 페이지네이션 불필요(세션 수 소). 인증 동일.

---

### 5.3 헬스 게이팅
```
GET /api/tracking/health
```
**Response**: `200 {"status":"ok","tracking_count":<int>}` (테이블 존재·접근 가능) / 비정상 시 `503`. **무인증**(공개, `main.py:636 health_check` 미러).

---

## 6. Pydantic 스키마
```python
# app/schemas/tracking.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from app.schemas.common import KSTDatetime

class CursorMeta(BaseModel):
    next_cursor: Optional[str] = None
    limit: int
    has_more: bool = False

class TrackPointResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    camera_id: int
    track_id: str
    label: Optional[str] = None
    threat_level: Optional[str] = None
    latitude: float
    longitude: float
    distance_m: Optional[float] = None
    confidence: Optional[float] = None
    observed_at: KSTDatetime
    speed_mps: Optional[float] = None
    session_seq: Optional[int] = None

class TrackSessionResponse(BaseModel):
    track_id: str
    camera_id: int
    label: Optional[str] = None
    start_at: KSTDatetime
    end_at: KSTDatetime
    point_count: int
    session_seq: Optional[int] = None
```
> `CursorMeta`는 공유 `app/schemas/common.py`(PaginationMeta 곁)로 올릴지 `tracking.py`에 둘지 구현 시 택1 — 본 PRD 기본은 `tracking.py` 지역 정의(영향 최소).

---

## 7. 인제스트 워커 `gis-ingest` (신규 독립 서비스)

### 7.1 구조 (db_monitor 미러)
```
gis_ingest/
├── main.py            # nats.subscribe("sensorway.*.gis.tracking-status") → asyncpg INSERT ... ON CONFLICT DO NOTHING
├── requirements.txt   # asyncpg>=0.29.0, nats-py>=2.6.0
└── Dockerfile         # FROM python:3.11-slim; COPY main.py + requirements; CMD python main.py
```

### 7.2 처리 로직
```
on_message(msg):
  env = json.loads(msg.data)
  body = env["body"]
  if body.get("tracking") != "active": return         # lost/idle → 저장 없음
  targets = body.get("targets") or _normalize_legacy(body)   # 구버전 단일 target 방어
  for t in targets:
     INSERT INTO track_points
       (camera_id, track_id, label, threat_level, latitude, longitude,
        distance_m, confidence, observed_at, tracking_state)
     VALUES (...) ON CONFLICT (track_id, observed_at) DO NOTHING
```
- `_normalize_legacy`: 구버전 `body.target`+`body.target_location` 수신 시 `track_id` 합성(`f"{camera_id}-{epoch}"`)·`observed_at`=`env.created`로 1개짜리 배열 정규화(합의 전 호환).
- 와일드카드 `*`는 `sensorway.<unit>.gis.tracking-status`의 단일 unit 토큰 매칭.
- 견고성: NATS 재연결(`nats.connect(..., reconnect_time_wait, max_reconnect_attempts=-1)`), INSERT 예외는 로그 후 메시지 스킵(워커 죽지 않음).

### 7.3 docker-compose 추가
```yaml
gis-ingest:
  build: ./gis_ingest
  image: api-test-gis-ingest:latest
  container_name: api-test-gis-ingest
  environment:
    - DATABASE_URL=${MONITOR_DATABASE_URL}
    - NATS_URL=${NATS_URL:-nats://nats-server-01:4222}
    - UNIT_ID=${UNIT_ID:-unit001}
  depends_on: { postgres: { condition: service_healthy } }
  networks: [default, nats_external]
  restart: unless-stopped
```

---

## 8. Breaking Changes
- REST: **없음**(신규 엔드포인트만 추가, 기존 무변경).
- 메시지 계약: `TRACKING_STATUS` 단일 `target` → `targets[]` **전면 교체(하위호환 없음)** — 단 이는 **이미 .NET이 채택한 신버전**을 서버 사본에 동기화하는 것이며, 인제스트는 구버전 방어 파싱 포함. 실발행자(AiAnalysis) 합의 필요(선결).

---

## 9. 파일 구조 (5-싱크 대상 전부)
| File | Action | 설명 |
|---|---|---|
| `app/models/tracking.py` | **신규** | `TrackPoint` ORM(§4.1, UniqueConstraint+Index) |
| `app/schemas/tracking.py` | **신규** | `TrackPointResponse`/`TrackSessionResponse`/`CursorMeta`(§6) |
| `app/routers/tracking.py` | **신규** | `/points`·`/sessions`·`/health`(§5) |
| `app/main.py` | **수정** | import(L36) + include_router(prefix `/api/tracking`) + tags_metadata |
| `app/models/__init__.py` | **수정** | `TrackPoint` re-export(관례) |
| `app/migrations/v54_tracking_points.sql` | **신규** | 명시 테이블+인덱스+UNIQUE+purge 함수(멱등) |
| `gis_ingest/main.py` | **신규** | 인제스트 워커(§7.2) |
| `gis_ingest/requirements.txt` | **신규** | asyncpg, nats-py |
| `gis_ingest/Dockerfile` | **신규** | 워커 이미지 |
| `docker-compose.yml` | **수정** | `gis-ingest` 서비스(§7.3) |
| `tests/test_tracking.py` | **신규** | TDD(§11) |
| `GOP_Restful_Api_연동설계.md` | **수정** | §11 추적 이력 API 신설(에러처리→§12·부록→§13 재번호+TOC+부록 엔드포인트목록) + `## 변경 이력` v4.11 행 + footer |
| `docs/Gop_Message_Broker_연동설계.md` | **수정** | §8.3.7을 신버전 `targets[]`로 동기화(선결) |
| `CHANGELOG.md` | **수정** | `[Unreleased]` → **v4.11(2026-06-26)** 통합 컷(오늘 작업 일괄) |

---

## 10. 명세서·버전 동기화 규칙 (규칙 1~3 준수)
1. **5-싱크**: 명세서(§11+변경이력+footer) · 코드(model/schema/router/main) · Swagger(FastAPI 자동+tags_metadata) · 이미지(api-server 재빌드 + gis-ingest 신규 빌드) · 컨테이너(recreate + `health` 200 검증).
2. **일일버전 1차수**: 오늘(2026-06-26) 작업은 **단일 v4.11**로 통합. CHANGELOG `[Unreleased]`에 이미 적재된 오늘분(프로필 사진 업로드·audit FK 익명화)도 **같은 v4.11 행**에 Phase로 묶는다(별도 버전 신설 금지).
3. **명세서 구조 정합**(누락·중복 금지): 신 §11 삽입 시 현 §11 에러처리→§12, §12 부록→§13 **연쇄 재번호** + 목차(L12~) 갱신 + 부록 `전체 Endpoint 목록`에 3개 GET 추가. 엔드포인트 문서화는 §6.5 Detection-Log GET 템플릿(Endpoint/설명/Query Params 표/Response/Error) 준수.

---

## 11. TDD Phases (Kent Beck — Red→Green→Refactor, Tidy First)

> 각 Phase 안에서 TEST(빨강)→IMPL(초록)→REFACTOR, 매 단계 전체 pytest. 구조변경/행위변경 커밋 분리. 테스트 통과+lint 클린일 때만 commit. 커밋 메시지에 structural/behavioral 명시.

### Phase 0: 선결 (계약 동기화 + 안전점)
- [ ] 0.1 STRUCTURAL: 롤백 태그 `before-tracking-api` + 피처 브랜치 `feature/tracking-history-api`
- [ ] 0.2 DOC: `docs/Gop_Message_Broker_연동설계.md §8.3.7` 구버전 단일 target → 신버전 `targets[]`로 동기화(.NET 사본 대조)
- [ ] 0.3 NOTE: AiAnalysis 발행 포맷 합의 항목을 README/스케줄 문서에 기록(미결 트래킹)

### Phase 1: 마이그레이션 + ORM 모델
- [ ] 1.1 TEST: should_create_track_points_table_with_unique_when_migrated (create_all 후 테이블·UNIQUE 존재)
- [ ] 1.2 IMPL: `app/models/tracking.py` `TrackPoint`(UniqueConstraint(track_id, observed_at) + Index 2종)
- [ ] 1.3 IMPL: `app/migrations/v54_tracking_points.sql`(IF NOT EXISTS + 인덱스 + purge 함수)
- [ ] 1.4 IMPL: `app/models/__init__.py` re-export
- [ ] 1.5 VERIFY: 전체 pytest 회귀 0

### Phase 2: 스키마
- [ ] 2.1 TEST: should_serialize_track_point_when_orm_row (from_attributes, KSTDatetime +09:00)
- [ ] 2.2 TEST: should_build_cursor_meta_when_has_more
- [ ] 2.3 IMPL: `app/schemas/tracking.py`(§6)

### Phase 3: `/points` (keyset cursor)
- [ ] 3.1 TEST: should_return_empty_when_no_points
- [ ] 3.2 IMPL: `app/routers/tracking.py` `/points` 기본 조회 + `app/main.py` 등록
- [ ] 3.3 TEST: should_filter_by_camera_id_and_track_id_when_given
- [ ] 3.4 TEST: should_filter_by_from_to_when_range_given
- [ ] 3.5 TEST: should_order_by_observed_at_asc
- [ ] 3.6 TEST: should_paginate_by_keyset_cursor_when_limit_exceeded (limit+1 → next_cursor → 다음 페이지 연속·중복 0)
- [ ] 3.7 IMPL: cursor 인코딩/디코딩 + tuple 비교 + has_more
- [ ] 3.8 TEST: should_require_token_when_auth_mode_token (선택, AUTH_MODE 토글)
- [ ] 3.9 VERIFY: 전체 pytest

### Phase 4: `/sessions`
- [ ] 4.1 TEST: should_return_empty_sessions_when_no_points
- [ ] 4.2 TEST: should_group_one_session_per_track_with_start_end_count
- [ ] 4.3 TEST: should_filter_sessions_by_camera_and_range
- [ ] 4.4 IMPL: GROUP BY 집계 핸들러
- [ ] 4.5 VERIFY: 전체 pytest

### Phase 5: `/health`
- [ ] 5.1 TEST: should_return_ok_with_count_when_table_ready
- [ ] 5.2 IMPL: health 핸들러(무인증)

### Phase 6: 인제스트 워커 (파싱·멱등 — 단위 테스트 가능)
- [ ] 6.1 TEST: should_extract_rows_from_active_targets_message (신버전 targets[] → N행 매핑)
- [ ] 6.2 TEST: should_skip_when_tracking_is_lost_or_idle
- [ ] 6.3 TEST: should_normalize_legacy_single_target_when_no_targets_array (구버전 방어)
- [ ] 6.4 TEST: should_be_idempotent_on_conflict_when_same_track_id_observed_at (ON CONFLICT DO NOTHING)
- [ ] 6.5 IMPL: `gis_ingest/main.py` 파서 + asyncpg INSERT(순수 파싱 함수 분리해 단위 테스트)
- [ ] 6.6 IMPL: `gis_ingest/requirements.txt` + `gis_ingest/Dockerfile`

### Phase 7: 인프라 5-싱크 (이미지·컨테이너)
- [ ] 7.1 IMPL: `docker-compose.yml` `gis-ingest` 서비스(§7.3)
- [ ] 7.2 VERIFY: `docker compose build api-server gis-ingest && docker compose up -d` → api-server·gis-ingest·postgres healthy
- [ ] 7.3 VERIFY: `GET /api/tracking/health` 200 + Swagger에 Tracking 태그 노출

### Phase 8: 명세서 5-싱크 (문서)
- [ ] 8.1 IMPL: `GOP_Restful_Api_연동설계.md` §11 추적 이력 API 신설 + §11/§12 재번호 + TOC + 부록 엔드포인트목록
- [ ] 8.2 IMPL: `## 변경 이력` v4.11(2026-06-26, 하루 일괄) 행 + footer v4.11
- [ ] 8.3 IMPL: `CHANGELOG.md` [Unreleased] → v4.11 컷(오늘분 통합)

### Phase 9: 전체 검증 + E2E
- [ ] 9.1 VERIFY: 전체 pytest 통과 + 기존 회귀 0
- [ ] 9.2 VERIFY(E2E, opt-in): mock 발행 `TRACKING_STATUS active` → gis-ingest INSERT → `GET /points` 기간조회·cursor 연속 → `GET /sessions` 집계 확인
- [ ] 9.3 STRUCTURAL/BEHAVIORAL 커밋 분리 정리 + 버전 브랜치 컷(관례 시)

---

## 12. 리스크
| 리스크 | 영향 | 대응 |
|---|---|---|
| AiAnalysis 발행 포맷 미합의(신 targets[]) | 인제스트 0행 | 구버전 방어 파싱 + 합의 트래킹(Phase 0.3). mock 발행으로 선검증 |
| `INIT_SAMPLE_DATA` 재시드 크래시 | 컨테이너 부팅 실패 | 사용 중 DB는 `=false` 유지(절대 true 금지). gis-ingest는 시드 무관 |
| cursor SQLite/PG 차이 | 테스트 불일치 | `tuple_()` 비교는 양쪽 호환, 단조 정렬키(observed_at,id) 사용 |
| 추적 테이블 무한 증가 | 디스크 | 7일 purge 함수(§4.3) + 운영 스케줄(후속) |
| 명세서 재번호 누락/중복 | 문서 오염 | 규칙 3 — 전체 구조 확인 후 §11/§12 연쇄 재번호 + TOC 동시 갱신 |

---

## 13. Definition of Done
- [ ] 3개 GET 엔드포인트 동작 + keyset cursor 연속성(중복 0) 검증
- [ ] gis-ingest 멱등 인제스트(ON CONFLICT) + active만 저장 검증
- [ ] 5-싱크 완료(명세서 §11+변경이력+footer / 코드 / Swagger / 이미지 / 컨테이너 healthy)
- [ ] CHANGELOG·명세서 변경이력 v4.11 동기화(오늘분 일괄)
- [ ] 전체 pytest green + 기존 회귀 0
- [ ] (합의 시) 실 AiAnalysis 발행 E2E
