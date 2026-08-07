"""
db_monitor: PostgreSQL pg_notify → NATS bridge
PRD: PRD_DB_Change_Monitor.md Section 5

MSG-02 (2026-07-09): 연결 감독(supervision) 추가.
- 기존: 1회 연결 후 `while True: sleep(1)` 만 → PostgreSQL 재시작 시 LISTEN 이 조용히 유실돼
  이후 SYNC 가 영구 중단(컨테이너는 Up).
- 개선: PostgreSQL liveness 프로브(SELECT 1) 로 단절 감지 → 지수 백오프+지터 재연결.
  하트비트 파일(/tmp/db_monitor_heartbeat)로 Docker healthcheck 노출 → autoheal(label=all) 이 감시.
  NATS 는 클라이언트 자체 무한 재연결(max_reconnect_attempts=-1).
"""
import asyncio
import json
import os
import random
import time
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")

HEARTBEAT_FILE = os.environ.get("DB_MONITOR_HEARTBEAT", "/tmp/db_monitor_heartbeat")
LIVENESS_INTERVAL = 3.0   # 초 — SELECT 1 liveness 프로브 + 하트비트 주기
BACKOFF_MAX = 30.0        # 초 — 재연결 백오프 상한

CMD_SUBJECT_MAP = {
    "SYNC_DEVICE":         "all.sync.device",
    "SYNC_SERVER":         "all.sync.server",
    "SYNC_CATEGORY":       "all.sync.category",
    "SYNC_DEVICE_GROUP":   "all.sync.device-group",
    "SYNC_EVENT_MAPPING":  "all.sync.event-mapping",
    "SYNC_PRESET":         "all.sync.preset",
    "SYNC_FILE_GROUP":     "all.sync.file-group",
    "SYNC_CAMERA_SETTING": "all.sync.camera-setting",
    "SYNC_PROXY_SETTING":  "all.sync.proxy-setting",
    "SYNC_DETECTION":      "all.sync.detection",     # 탐지 갱신 알림 (detection-sync-message, UPDATE/DELETE만, from=DBApi)
    "SYNC_EVENT_SUPPRESSION": "all.sync.event-suppression",  # 억제(정비 창) 변경·창경계 전이 알림 — 이벤트 파이프라인 통제 상태
    "SYSTEM_EVENT":        "all.event.system",       # Full-DTO (gop_event 채널)
    "ENCLOSURE_METRICS":   "gis.enclosure-metrics",  # 주기 텔레메트리 (주기 태스크)
}


def cmd_to_subject(cmd: str, unit_id: str) -> str | None:
    """Convert pg_notify cmd to NATS subject. Returns None for unknown cmds."""
    suffix = CMD_SUBJECT_MAP.get(cmd)
    if suffix is None:
        return None
    return f"sensorway.{unit_id}.{suffix}"


def build_nats_envelope(cmd: str, body: dict) -> dict:
    """Build NATS message envelope per Gop_Message_Broker_연동설계.md."""
    return {
        "id": str(uuid.uuid4()),
        "m_type": "PUB",
        "cmd": cmd,
        "from": "DBApi",
        "body": body,
        "created": datetime.now(KST).isoformat(),
    }


def make_handler(nc, unit_id: str):
    """Return asyncpg listener callback that publishes to NATS.

    gop_sync(SYNC 알림만) + gop_event(SYSTEM_EVENT Full-DTO) 공용 핸들러.
    body = payload 의 cmd 제외 전 필드 통과 — 트리거가 식별자를 결정하므로
    (resource_id/camera_id/server_id/type_device 등) monitor 는 운반만 한다.
    (nats-dbapi-sync-completion FR-06: 하드코딩 resource_id 제거 → 식별자 갭 자동 수용.)
    """
    async def on_notify(conn, pid, channel, payload):
        data = json.loads(payload)
        cmd = data.pop("cmd", None)
        subject = cmd_to_subject(cmd, unit_id)
        if subject is None:
            # ★ 무성 유실 방지: 트리거는 새 cmd 를 쏘는데 db_monitor 가 구버전이면 조용히 버려진다.
            #   배포 순서(db_monitor 먼저)를 어겼을 때 즉시 드러나도록 경고를 남긴다.
            print(f"[db_monitor][WARN] unmapped cmd '{cmd}' — dropped. "
                  f"CMD_SUBJECT_MAP 등재 누락 또는 db_monitor 구버전(배포 순서 확인)", flush=True)
            return
        envelope = build_nats_envelope(cmd, data)  # data = cmd 제외 잔여 = body
        await nc.publish(subject, json.dumps(envelope).encode())

    return on_notify


async def _enclosure_metrics_loop(db_url: str, nc, unit_id: str, interval: float):
    """ENCLOSURE_METRICS (nats-dbapi-sync-completion FR-05): 주기 텔레메트리.

    이벤트가 아닌 주기 push 이므로 트리거로 발화할 수 없다 → db_monitor 가 함체별 최신
    metrics 를 조회해 발행한다. 리스너 연결과 **분리된 전용 asyncpg 연결** 사용
    (asyncpg 연결은 동시 쿼리 비안전). measured_at = REST created_at 대응.
    """
    import asyncpg
    subject = f"sensorway.{unit_id}.gis.enclosure-metrics"

    def _f(v):
        try:
            return float(v) if v is not None else None
        except (TypeError, ValueError):
            return None

    conn = await asyncpg.connect(db_url, server_settings={"application_name": "db_monitor_encl"})
    try:
        while True:
            rows = await conn.fetch(
                "SELECT DISTINCT ON (enclosure_id) enclosure_id, temperature, humidity, "
                "voltage, current, created_at FROM enclosure_metrics "
                "ORDER BY enclosure_id, created_at DESC"
            )
            for r in rows:
                body = {
                    "enclosure_id": r["enclosure_id"],
                    "temperature": _f(r["temperature"]),
                    "humidity": _f(r["humidity"]),
                    "voltage": _f(r["voltage"]),
                    "current": _f(r["current"]),
                    "measured_at": r["created_at"].isoformat() if r["created_at"] else None,
                }
                envelope = build_nats_envelope("ENCLOSURE_METRICS", body)
                await nc.publish(subject, json.dumps(envelope).encode())
            await asyncio.sleep(interval)
    finally:
        try:
            await conn.close()
        except Exception:
            pass


def _write_heartbeat() -> None:
    """하트비트 파일에 현재 epoch 기록 (Docker healthcheck 신선도 판정용)."""
    try:
        with open(HEARTBEAT_FILE, "w") as f:
            f.write(str(int(time.time())))
    except Exception as e:
        print(f"[db_monitor] heartbeat write failed: {e}")


async def _connect_and_listen(db_url: str, nats_url: str, unit_id: str, encl_interval: float) -> None:
    """1회 연결 세션: PostgreSQL LISTEN(gop_sync/gop_event) + ENCLOSURE_METRICS 주기 태스크 + NATS 발행.

    liveness 프로브(SELECT 1) 가 실패하면(연결 단절) 예외로 이탈해 상위 감독 루프가 재연결한다.
    주기 태스크가 죽어도 세션을 재시작한다(finally 에서 취소·정리).
    """
    import asyncpg
    import nats

    nc = await nats.connect(
        nats_url, reconnect_time_wait=2, max_reconnect_attempts=-1,
        name=f"db_monitor-{unit_id}",
    )
    # application_name 지정 — pg_stat_activity 관측/운영 진단 및 타깃 종료에 사용
    conn = await asyncpg.connect(db_url, server_settings={"application_name": "db_monitor"})
    handler = make_handler(nc, unit_id)
    await conn.add_listener("gop_sync", handler)     # SYNC 9종 (알림만)
    await conn.add_listener("gop_event", handler)    # SYSTEM_EVENT (Full-DTO)
    # ENCLOSURE_METRICS 주기 발행 태스크 (전용 연결)
    encl_task = asyncio.create_task(_enclosure_metrics_loop(db_url, nc, unit_id, encl_interval))
    print(f"[db_monitor] Listening gop_sync/gop_event → NATS {nats_url} "
          f"(unit_id={unit_id}, encl_interval={encl_interval}s)")
    _write_heartbeat()

    try:
        while True:
            # PostgreSQL liveness — 죽은 연결이면 여기서 예외 → 재연결
            await conn.execute("SELECT 1")
            if encl_task.done():  # 주기 태스크가 종료되면 세션 재시작(전용 연결 단절 등)
                raise RuntimeError(f"enclosure metrics task ended: {encl_task.exception()!r}")
            if not nc.is_connected:
                print("[db_monitor] NATS disconnected (client auto-reconnecting)…")
            _write_heartbeat()
            await asyncio.sleep(LIVENESS_INTERVAL)
    finally:
        encl_task.cancel()
        for ch in ("gop_sync", "gop_event"):
            try:
                await conn.remove_listener(ch, handler)
            except Exception:
                pass
        try:
            await conn.close()
        except Exception:
            pass
        try:
            await nc.close()
        except Exception:
            pass


async def run_supervised(db_url: str, nats_url: str, unit_id: str, encl_interval: float) -> None:
    """감독 루프 — 연결 세션이 단절/오류로 끝나면 지수 백오프+지터로 무한 재연결."""
    backoff = 1.0
    while True:
        try:
            await _connect_and_listen(db_url, nats_url, unit_id, encl_interval)
            backoff = 1.0
        except Exception as e:
            capped = min(backoff, BACKOFF_MAX)
            wait = capped + random.uniform(0, capped * 0.3)
            print(f"[db_monitor] session ended: {e!r} — reconnect in {wait:.1f}s")
            await asyncio.sleep(wait)
            backoff = min(backoff * 2, BACKOFF_MAX)


if __name__ == "__main__":
    db_url = os.environ["DATABASE_URL"]
    nats_url = os.environ.get("NATS_URL", "nats://localhost:4222")
    unit_id = os.environ.get("UNIT_ID", "unit001")
    encl_interval = float(os.environ.get("ENCLOSURE_METRICS_INTERVAL", "10"))
    asyncio.run(run_supervised(db_url, nats_url, unit_id, encl_interval))
