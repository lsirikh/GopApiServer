"""
db_monitor: PostgreSQL pg_notify → NATS bridge
PRD: PRD_DB_Change_Monitor.md Section 5
"""
import asyncio
import json
import os
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")

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
    """Return asyncpg listener callback that publishes to NATS."""
    async def on_notify(conn, pid, channel, payload):
        data = json.loads(payload)
        cmd = data.get("cmd")
        subject = cmd_to_subject(cmd, unit_id)
        if subject is None:
            return

        body = {
            "action": data["action"],
            "resource_id": data["resource_id"],
        }
        if "type_device" in data:
            body["type_device"] = data["type_device"]

        envelope = build_nats_envelope(cmd, body)
        await nc.publish(subject, json.dumps(envelope).encode())

    return on_notify


async def listen_and_publish(db_url: str, nats_url: str, unit_id: str) -> None:
    """Connect to PostgreSQL and NATS, then relay pg_notify → NATS."""
    import asyncpg
    import nats

    nc = await nats.connect(nats_url)
    conn = await asyncpg.connect(db_url)
    handler = make_handler(nc, unit_id)

    await conn.add_listener("gop_sync", handler)
    print(f"[db_monitor] Listening on gop_sync → NATS {nats_url} (unit_id={unit_id})")

    try:
        while True:
            await asyncio.sleep(1)
    finally:
        await conn.remove_listener("gop_sync", handler)
        await conn.close()
        await nc.close()


if __name__ == "__main__":
    db_url = os.environ["DATABASE_URL"]
    nats_url = os.environ.get("NATS_URL", "nats://localhost:4222")
    unit_id = os.environ.get("UNIT_ID", "unit001")
    asyncio.run(listen_and_publish(db_url, nats_url, unit_id))
