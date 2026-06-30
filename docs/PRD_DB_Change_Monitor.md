# PRD: DB Change Monitor — PostgreSQL pg_notify → NATS 브리지

**문서 버전**: v1.0
**작성일**: 2026-03-04
**상태**: Draft
**참조 문서**: `Gop_Message_Broker_연동설계.md` v1.2 (Section 9. 마스터 데이터 동기화)

---

## 1. 개요

### 1.1 목적

GOP 통제시스템의 마스터 데이터(장비, 서버, 이벤트매핑 등)가 DBApi를 통해 변경될 때, 변경 사실을 NATS를 통해 모든 서브시스템에 실시간으로 브로드캐스트한다.

기존 설계(`Gop_Message_Broker_연동설계.md` Section 9)에서 DBApi가 SYNC 메시지를 발행해야 한다고 명시되어 있으나, **현재 구현이 없는 상태**다. 본 PRD는 이를 **DB 레벨에서 보장**하는 방식으로 구현한다.

### 1.2 핵심 원칙

- **DB 레벨 보장**: FastAPI 앱 크래시와 무관하게 DB 변경 시 알림이 발행됨 (PostgreSQL 트리거)
- **알림만 전달**: NATS 메시지에 데이터 없음, `{action, resource_id}`만 포함 (기존 설계 준수)
- **단일 채널**: 모든 테이블의 변경을 `gop_sync` 채널 하나로 통합, cmd로 라우팅
- **서브시스템 자율 조회**: 알림 수신 후 각 서브시스템이 REST API 직접 호출하여 최신 데이터 캐싱

### 1.3 기존 설계와의 관계

```
Gop_Message_Broker_연동설계.md Section 9에서 정의:
  DBApi → NATS SYNC_* → 서브시스템 → REST API 조회 → 캐시 갱신

본 PRD가 구현하는 것:
  "DBApi가 어떻게 SYNC 메시지를 발행하는가"
  → PostgreSQL 트리거 + db_monitor 서비스로 구현
```

---

## 2. 아키텍처

### 2.1 전체 흐름

```
┌──────────────────────────────────────────────────────────────────┐
│  Central / GIS (HTTP Client)                                      │
└──────────────┬───────────────────────────────────────────────────┘
               │ POST/PATCH/DELETE /api/devices/{id}
               ▼
┌─────────────────────────┐
│   DBApi (FastAPI)        │
│   app/routers/*.py       │
└──────────┬──────────────┘
           │ SQLAlchemy write
           ▼
┌─────────────────────────────────────────────────────────────────┐
│   PostgreSQL (gop DB)                                            │
│                                                                  │
│  [devices 테이블 INSERT/UPDATE/DELETE]                           │
│       │                                                          │
│       ▼                                                          │
│  [트리거: trg_sync_devices]                                      │
│       │                                                          │
│       ▼                                                          │
│  pg_notify('gop_sync',                                           │
│    '{"cmd":"SYNC_DEVICE","action":"UPDATED",                     │
│      "type_device":"Camera","resource_id":201}')                 │
└─────────────────────────┬───────────────────────────────────────┘
                          │ LISTEN gop_sync (asyncpg)
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│   db_monitor (별도 Python 프로세스)                               │
│                                                                  │
│   1. asyncpg LISTEN gop_sync                                     │
│   2. 알림 파싱: cmd, action, resource_id                         │
│   3. NATS Subject 결정:                                          │
│      sensorway.{UNIT_ID}.all.sync.device                         │
│   4. NATS Envelope 생성 (기존 설계 준수)                          │
│   5. nats.publish(subject, payload)                              │
└─────────────────────────┬───────────────────────────────────────┘
                          │ PUB
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│   NATS Core                                                      │
│   subject: sensorway.unit001.all.sync.device                     │
│   body: {"action":"UPDATED","type_device":"Camera",              │
│          "resource_id":201}                                      │
└───┬──────┬──────┬──────┬──────┬──────┬──────────────────────────┘
    │      │      │      │      │      │
    ▼      ▼      ▼      ▼      ▼      ▼
  GIS    VMS   NVR   PIDS  BCAST  AI
  [캐시 갱신: GET /api/devices/cameras/201]
```

### 2.2 컴포넌트 역할

| 컴포넌트 | 역할 | 기술 |
|---------|------|------|
| PostgreSQL 트리거 | 마스터 데이터 변경 감지 → `pg_notify()` | SQL PL/pgSQL |
| `db_monitor` 서비스 | LISTEN 수신 → NATS 발행 | Python, asyncpg, nats-py |
| NATS | 메시지 브로커 | nats:2.10-alpine |
| 서브시스템 | SYNC 알림 구독 → REST API 조회 | 기존 서브시스템 |

---

## 3. SYNC 대상 테이블 및 채널 매핑

### 3.1 트리거 등록 대상 테이블

기존 `Gop_Message_Broker_연동설계.md` Section 9 SYNC 설계와 1:1 매핑:

| 테이블 | SYNC cmd | NATS Subject (suffix) | type_device 포함 |
|--------|----------|----------------------|:----------------:|
| `devices`, `controllers`, `sensors`, `cameras`, `speakers`, `enclosures`, `lamps` | `SYNC_DEVICE` | `all.sync.device` | ✅ |
| `servers` | `SYNC_SERVER` | `all.sync.server` | - |
| `server_categories` | `SYNC_CATEGORY` | `all.sync.category` | - |
| `device_groups` | `SYNC_DEVICE_GROUP` | `all.sync.device-group` | - |
| `event_mappings` | `SYNC_EVENT_MAPPING` | `all.sync.event-mapping` | - |
| `camera_presets` | `SYNC_PRESET` | `all.sync.preset` | - |
| `file_groups` | `SYNC_FILE_GROUP` | `all.sync.file-group` | - |
| `camera_settings` | `SYNC_CAMERA_SETTING` | `all.sync.camera-setting` | - |
| `proxy_settings` | `SYNC_PROXY_SETTING` | `all.sync.proxy-setting` | - |

> **제외 테이블**: `events`, `detection_events`, `malfunction_events`, `connection_events`, `action_events` — 이벤트는 SYNC가 아닌 별도의 이벤트 메시지(Section 6)로 처리

### 3.2 type_device 결정 방식

`devices` 계층 구조에서 서브 타입을 판별:

| 테이블 | type_device 값 |
|--------|---------------|
| `controllers` | `"Controller"` |
| `sensors` | `"Sensor"` (구체 타입은 `devices.type_device`) |
| `cameras` | `"Camera"` |
| `speakers` | `"Speaker"` |
| `enclosures` | `"Enclosure"` |
| `lamps` | `"Lamp"` |

---

## 4. PostgreSQL 트리거 설계

### 4.1 통합 트리거 함수

단일 채널 `gop_sync`를 사용하며, pg_notify payload(JSON)에 라우팅 정보 포함:

```sql
-- 공통 트리거 함수 (각 테이블에서 재사용)
CREATE OR REPLACE FUNCTION fn_notify_gop_sync()
RETURNS trigger AS $$
DECLARE
    payload JSONB;
    action_type TEXT;
    resource_id INTEGER;
BEGIN
    -- TG_OP: INSERT, UPDATE, DELETE
    IF TG_OP = 'DELETE' THEN
        action_type := 'DELETED';
        resource_id := OLD.id;
    ELSIF TG_OP = 'INSERT' THEN
        action_type := 'CREATED';
        resource_id := NEW.id;
    ELSE
        action_type := 'UPDATED';
        resource_id := NEW.id;
    END IF;

    -- 테이블별 분기는 TG_TABLE_NAME 사용
    IF TG_TABLE_NAME = 'devices' THEN
        RETURN NULL;  -- devices는 서브타입 테이블이 처리
    ELSIF TG_TABLE_NAME IN ('controllers','sensors','cameras','speakers','enclosures','lamps') THEN
        payload := jsonb_build_object(
            'cmd', 'SYNC_DEVICE',
            'action', action_type,
            'type_device', TG_ARGV[0],  -- 트리거 등록 시 파라미터
            'resource_id', resource_id
        );
    ELSIF TG_TABLE_NAME = 'servers' THEN
        payload := jsonb_build_object(
            'cmd', 'SYNC_SERVER',
            'action', action_type,
            'resource_id', resource_id
        );
    ELSIF TG_TABLE_NAME = 'server_categories' THEN
        payload := jsonb_build_object(
            'cmd', 'SYNC_CATEGORY',
            'action', action_type,
            'resource_id', resource_id
        );
    ELSIF TG_TABLE_NAME = 'device_groups' THEN
        payload := jsonb_build_object(
            'cmd', 'SYNC_DEVICE_GROUP',
            'action', action_type,
            'resource_id', resource_id
        );
    ELSIF TG_TABLE_NAME = 'event_mappings' THEN
        payload := jsonb_build_object(
            'cmd', 'SYNC_EVENT_MAPPING',
            'action', action_type,
            'resource_id', resource_id
        );
    ELSIF TG_TABLE_NAME = 'camera_presets' THEN
        payload := jsonb_build_object(
            'cmd', 'SYNC_PRESET',
            'action', action_type,
            'resource_id', resource_id
        );
    ELSIF TG_TABLE_NAME = 'file_groups' THEN
        payload := jsonb_build_object(
            'cmd', 'SYNC_FILE_GROUP',
            'action', action_type,
            'resource_id', resource_id
        );
    ELSIF TG_TABLE_NAME = 'camera_settings' THEN
        payload := jsonb_build_object(
            'cmd', 'SYNC_CAMERA_SETTING',
            'action', action_type,
            'resource_id', resource_id
        );
    ELSIF TG_TABLE_NAME = 'proxy_settings' THEN
        payload := jsonb_build_object(
            'cmd', 'SYNC_PROXY_SETTING',
            'action', action_type,
            'resource_id', resource_id
        );
    ELSE
        RETURN NULL;
    END IF;

    PERFORM pg_notify('gop_sync', payload::text);
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;
```

### 4.2 트리거 등록

```sql
-- Device 서브타입별 트리거
CREATE TRIGGER trg_sync_controllers
    AFTER INSERT OR UPDATE OR DELETE ON controllers
    FOR EACH ROW EXECUTE FUNCTION fn_notify_gop_sync();

CREATE TRIGGER trg_sync_sensors
    AFTER INSERT OR UPDATE OR DELETE ON sensors
    FOR EACH ROW EXECUTE FUNCTION fn_notify_gop_sync();

CREATE TRIGGER trg_sync_cameras
    AFTER INSERT OR UPDATE OR DELETE ON cameras
    FOR EACH ROW EXECUTE FUNCTION fn_notify_gop_sync();

CREATE TRIGGER trg_sync_speakers
    AFTER INSERT OR UPDATE OR DELETE ON speakers
    FOR EACH ROW EXECUTE FUNCTION fn_notify_gop_sync();

CREATE TRIGGER trg_sync_enclosures
    AFTER INSERT OR UPDATE OR DELETE ON enclosures
    FOR EACH ROW EXECUTE FUNCTION fn_notify_gop_sync();

CREATE TRIGGER trg_sync_lamps
    AFTER INSERT OR UPDATE OR DELETE ON lamps
    FOR EACH ROW EXECUTE FUNCTION fn_notify_gop_sync();

-- 마스터 데이터 트리거
CREATE TRIGGER trg_sync_servers
    AFTER INSERT OR UPDATE OR DELETE ON servers
    FOR EACH ROW EXECUTE FUNCTION fn_notify_gop_sync();

CREATE TRIGGER trg_sync_server_categories
    AFTER INSERT OR UPDATE OR DELETE ON server_categories
    FOR EACH ROW EXECUTE FUNCTION fn_notify_gop_sync();

CREATE TRIGGER trg_sync_device_groups
    AFTER INSERT OR UPDATE OR DELETE ON device_groups
    FOR EACH ROW EXECUTE FUNCTION fn_notify_gop_sync();

CREATE TRIGGER trg_sync_event_mappings
    AFTER INSERT OR UPDATE OR DELETE ON event_mappings
    FOR EACH ROW EXECUTE FUNCTION fn_notify_gop_sync();

CREATE TRIGGER trg_sync_camera_presets
    AFTER INSERT OR UPDATE OR DELETE ON camera_presets
    FOR EACH ROW EXECUTE FUNCTION fn_notify_gop_sync();

CREATE TRIGGER trg_sync_file_groups
    AFTER INSERT OR UPDATE OR DELETE ON file_groups
    FOR EACH ROW EXECUTE FUNCTION fn_notify_gop_sync();

CREATE TRIGGER trg_sync_camera_settings
    AFTER INSERT OR UPDATE OR DELETE ON camera_settings
    FOR EACH ROW EXECUTE FUNCTION fn_notify_gop_sync();

CREATE TRIGGER trg_sync_proxy_settings
    AFTER INSERT OR UPDATE OR DELETE ON proxy_settings
    FOR EACH ROW EXECUTE FUNCTION fn_notify_gop_sync();
```

### 4.3 트리거 적용 방법

SQLAlchemy `event.listen` + `DDL`을 통해 앱 시작 시 자동 적용:

```python
# app/db_triggers.py
from sqlalchemy import text
from app.database import engine

TRIGGER_SQL = """
-- 위 4.1, 4.2의 SQL 전체
"""

def apply_triggers():
    with engine.connect() as conn:
        conn.execute(text(TRIGGER_SQL))
        conn.commit()
```

`app/main.py` startup 이벤트에서 호출:

```python
@app.on_event("startup")
def on_startup():
    apply_triggers()
    # 기존 init_db() ...
```

---

## 5. db_monitor 서비스 설계

### 5.1 역할

| 단계 | 동작 |
|------|------|
| 1 | asyncpg로 PostgreSQL 연결 후 `LISTEN gop_sync` |
| 2 | 알림 수신 시 JSON 파싱 → `{cmd, action, resource_id, type_device?}` |
| 3 | cmd → NATS Subject 변환 |
| 4 | NATS Envelope 생성 (기존 설계 준수) |
| 5 | NATS PUB 발행 |

### 5.2 NATS Subject 변환표

| pg_notify payload.cmd | NATS Subject |
|-----------------------|-------------|
| `SYNC_DEVICE` | `sensorway.{UNIT_ID}.all.sync.device` |
| `SYNC_SERVER` | `sensorway.{UNIT_ID}.all.sync.server` |
| `SYNC_CATEGORY` | `sensorway.{UNIT_ID}.all.sync.category` |
| `SYNC_DEVICE_GROUP` | `sensorway.{UNIT_ID}.all.sync.device-group` |
| `SYNC_EVENT_MAPPING` | `sensorway.{UNIT_ID}.all.sync.event-mapping` |
| `SYNC_PRESET` | `sensorway.{UNIT_ID}.all.sync.preset` |
| `SYNC_FILE_GROUP` | `sensorway.{UNIT_ID}.all.sync.file-group` |
| `SYNC_CAMERA_SETTING` | `sensorway.{UNIT_ID}.all.sync.camera-setting` |
| `SYNC_PROXY_SETTING` | `sensorway.{UNIT_ID}.all.sync.proxy-setting` |

### 5.3 NATS Envelope 구조 (기존 설계 완전 준수)

```json
{
  "id": "uuid-v4",
  "m_type": "PUB",
  "cmd": "SYNC_DEVICE",
  "from": "DBApi",
  "body": {
    "action": "UPDATED",
    "type_device": "Camera",
    "resource_id": 201
  },
  "created": "2026-03-04T14:30:00.000+09:00"
}
```

`body`는 `Gop_Message_Broker_연동설계.md` Section 9.2~9.10 정의와 동일.

### 5.4 Python 구현 스케치

```python
# db_monitor/main.py
import asyncio
import json
import uuid
import asyncpg
import nats
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")

CMD_TO_SUBJECT = {
    "SYNC_DEVICE":         "all.sync.device",
    "SYNC_SERVER":         "all.sync.server",
    "SYNC_CATEGORY":       "all.sync.category",
    "SYNC_DEVICE_GROUP":   "all.sync.device-group",
    "SYNC_EVENT_MAPPING":  "all.sync.event-mapping",
    "SYNC_PRESET":         "all.sync.preset",
    "SYNC_FILE_GROUP":     "all.sync.file-group",
    "SYNC_CAMERA_SETTING": "all.sync.camera-setting",
    "SYNC_PROXY_SETTING":  "all.sync.proxy-setting",
}

async def main(unit_id: str, db_url: str, nats_url: str):
    nc = await nats.connect(nats_url)
    conn = await asyncpg.connect(db_url)

    async def on_notify(conn, pid, channel, payload):
        data = json.loads(payload)
        cmd = data.get("cmd")
        suffix = CMD_TO_SUBJECT.get(cmd)
        if not suffix:
            return

        subject = f"sensorway.{unit_id}.{suffix}"
        body = {
            "action":      data["action"],
            "resource_id": data["resource_id"],
        }
        if "type_device" in data:
            body["type_device"] = data["type_device"]

        envelope = {
            "id":      str(uuid.uuid4()),
            "m_type":  "PUB",
            "cmd":     cmd,
            "from":    "DBApi",
            "body":    body,
            "created": datetime.now(KST).isoformat(),
        }
        await nc.publish(subject, json.dumps(envelope).encode())

    await conn.add_listener("gop_sync", on_notify)

    try:
        while True:
            await asyncio.sleep(1)
    finally:
        await conn.remove_listener("gop_sync", on_notify)
        await conn.close()
        await nc.close()
```

### 5.5 환경변수

| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| `DATABASE_URL` | `postgresql://gop_user:gop_pass@postgres:5432/gop` | PostgreSQL 연결 |
| `NATS_URL` | `nats://nats:4222` | NATS 서버 |
| `UNIT_ID` | `unit001` | Subject의 부대 ID |

---

## 6. Docker 구성

### 6.1 전제 조건

> **NATS 서버는 별도 인프라에서 이미 운영 중**이다. `db_monitor`는 NATS 서버를 구동하지 않으며,
> 기존 NATS 서버에 **클라이언트로 접속**하기만 한다. `NATS_URL` 환경변수에 접속 주소(IP:Port)를 지정한다.

### 6.2 docker-compose.yml 변경

```yaml
services:
  # 기존 postgres, api_server-fastapi, db-admin 유지

  db-monitor:
    build:
      context: ./db_monitor
      dockerfile: Dockerfile
    container_name: gop-db-monitor
    environment:
      - DATABASE_URL=postgresql://gop_user:gop_pass@postgres:5432/gop
      - NATS_URL=nats://192.168.1.100:4222   # 기존 NATS 서버 IP:Port
      - UNIT_ID=unit001
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped
```

### 6.3 db_monitor/Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir asyncpg nats-py
COPY main.py .
CMD ["python", "main.py"]
```

### 6.4 app/database.py 트리거 적용

기존 PostgreSQL 마이그레이션으로 생성된 DB에 트리거를 적용하므로 `app/db_triggers.py` 모듈을 추가하고 `main.py` startup에 호출.

---

## 7. NATS 메시지 수신 검증 방법

### 7.1 NATS CLI로 수신 확인

```bash
# 모든 SYNC 메시지 수신
nats sub "sensorway.unit001.all.sync.>"

# Device 변경만 수신
nats sub "sensorway.unit001.all.sync.device"
```

### 7.2 e2e 테스트 시나리오

```
1. NATS sub 열기: sensorway.unit001.all.sync.>
2. REST API: PATCH /api/devices/cameras/201 (이름 변경)
3. NATS 메시지 수신 확인:
   {"id":"...", "cmd":"SYNC_DEVICE", "from":"DBApi",
    "body":{"action":"UPDATED","type_device":"Camera","resource_id":201}}
4. REST API: GET /api/devices/cameras/201 → 변경된 데이터 확인
```

---

## 8. 에러 처리 및 복원력

### 8.1 db_monitor 재연결

- PostgreSQL 연결 끊김 → `asyncpg.exceptions.ConnectionDoesNotExistError` 캐치 → 5초 후 재연결
- NATS 연결 끊김 → `nats-py`의 자동 재연결 (`reconnect_time_wait=2`)

### 8.2 알림 누락 시나리오

| 상황 | 동작 |
|------|------|
| db_monitor 다운 중 DB 변경 발생 | pg_notify 알림 유실 (LISTEN 없으면 버림) → 재시작 후 누락분 없음 |
| NATS 다운 중 db_monitor 동작 | publish 실패 → 로그 기록, 재시도 3회 |

> **한계**: pg_notify는 at-most-once 보장. 고가용성이 필요하면 Debezium + Kafka 검토 필요 (현재 범위 밖)

### 8.3 pg_notify payload 크기 제한

PostgreSQL pg_notify payload 최대 **8000 bytes**. `{cmd, action, resource_id, type_device}`만 포함하므로 실제 ~100 bytes → 제한 없음.

---

## 9. 구현 계획 (TDD Phases)

### Phase 1: 사전 준비
- [ ] 1.1 기존 NATS 서버 IP:Port 확인 및 `NATS_URL` 환경변수 값 결정
- [ ] 1.2 `requirements.txt` — `nats-py>=2.6.0`, `asyncpg>=0.29.0` 추가
- [ ] 1.3 VERIFY: `nats-py` 클라이언트로 기존 NATS 서버 접속 테스트

### Phase 2: PostgreSQL 트리거
- [ ] 2.1 TEST: `tests/test_db_triggers.py` — 트리거 미적용 시 pg_notify 없음 확인 (RED)
- [ ] 2.2 IMPL: `app/db_triggers.py` — `fn_notify_gop_sync()` 함수 + 트리거 등록 SQL
- [ ] 2.3 IMPL: `app/main.py` — startup 이벤트에 `apply_triggers()` 호출
- [ ] 2.4 VERIFY GREEN: DB 변경 시 `LISTEN gop_sync`로 payload 수신 확인

### Phase 3: db_monitor 서비스
- [ ] 3.1 TEST: `db_monitor/test_monitor.py` — cmd → NATS subject 변환 단위 테스트
- [ ] 3.2 IMPL: `db_monitor/main.py` — asyncpg LISTEN + NATS publish 구현
- [ ] 3.3 IMPL: `db_monitor/Dockerfile` 생성
- [ ] 3.4 IMPL: `docker-compose.yml` — `db-monitor` 서비스 추가
- [ ] 3.5 VERIFY: `docker-compose up --build db-monitor` 기동 확인

### Phase 4: 통합 검증
- [ ] 4.1 VERIFY: NATS sub 열고 REST API PATCH 후 SYNC 메시지 수신 확인 (SYNC_DEVICE)
- [ ] 4.2 VERIFY: SYNC_SERVER, SYNC_EVENT_MAPPING 수신 확인
- [ ] 4.3 VERIFY: DELETE 시 `action: DELETED` 메시지 수신 확인
- [ ] 4.4 VERIFY: db_monitor 재시작 후 정상 동작 확인

### Phase 5: 문서 업데이트
- [ ] 5.1 `Gop_Message_Broker_연동설계.md` — 구현 방법 기술 (v1.3)

---

## 10. Critical Files

| 파일 | 액션 |
|------|------|
| `app/db_triggers.py` | 신규 생성 — pg_notify 트리거 SQL |
| `app/main.py` | startup에 `apply_triggers()` 호출 추가 |
| `docker-compose.yml` | db-monitor 서비스 추가 (NATS 서버는 외부 기존 인프라 사용) |
| `db_monitor/main.py` | 신규 생성 — asyncpg LISTEN + NATS publish |
| `db_monitor/Dockerfile` | 신규 생성 |
| `requirements.txt` | nats-py, asyncpg 추가 |

---

## 11. 미결 사항 / 의사결정 필요 항목

| 항목 | 현재 결정 | 대안 |
|------|----------|------|
| UNIT_ID 출처 | 환경변수 `UNIT_ID=unit001` | DB에서 서버 설정 조회 |
| pg_notify 누락 대처 | 무시 (at-most-once) | Debezium + WAL 복제 |
| db_monitor 위치 | 별도 Docker 서비스 | FastAPI background task |
| NATS 서버 | 외부 기존 인프라 사용 (클라이언트 접속만) | 로컬 NATS 서버 별도 구동 |
| NATS JetStream | 기존 서버 설정 따름 (Core NATS 가정) | JetStream으로 at-least-once 보장 |
