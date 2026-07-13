"""
gis_ingest: NATS TRACKING_STATUS → PostgreSQL track_points 인제스트 워커
PRD: PRD_Tracking_History_API.md §7

db_monitor(pg_notify→NATS publish)의 **역방향** 미러:
  NATS subscribe(sensorway.*.gis.tracking-status) → asyncpg INSERT ON CONFLICT DO NOTHING

- 신버전 TRACKING_STATUS body.targets[] 를 행으로 영속(tracking == "active" 만).
- 구버전(단일 body.target/target_location) 수신 시 방어 정규화(합의 전 호환).
- 멱등: UNIQUE(track_id, observed_at) → ON CONFLICT DO NOTHING.
- observed_at(UTC ISO) → naive KST 변환(읽기 API KSTDatetime 직렬화 정합).
"""
import asyncio
import json
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")

SUBJECT = "sensorway.*.gis.tracking-status"

INSERT_SQL = """
INSERT INTO track_points
    (camera_id, track_id, label, threat_level, latitude, longitude,
     distance_m, confidence, observed_at, tracking_state, created_at)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
ON CONFLICT (track_id, observed_at) DO NOTHING
"""


def _parse_observed_at(iso_str: str) -> datetime:
    """ISO 8601(UTC, Z 허용) → naive KST datetime. 파싱 실패 시 ValueError."""
    s = iso_str.replace("Z", "+00:00")
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)  # tz 없으면 UTC 가정
    return dt.astimezone(KST).replace(tzinfo=None)


def _normalize_legacy(body: dict, envelope: dict) -> list[dict]:
    """구버전 단일 target → 신버전 targets[] 1개로 정규화(합의 전 방어).

    구버전엔 track_id/observed_at 가 없어 camera_id/created 로 합성한다.
    """
    target = body.get("target")
    if not target:
        return []
    loc = body.get("target_location") or {}
    camera_id = body.get("camera_id")
    return [{
        "track_id": f"{camera_id}-legacy",
        "label": target.get("label"),
        "threat_level": None,
        "confidence": target.get("confidence"),
        "observed_at": envelope.get("created"),
        "location": {
            "latitude": loc.get("latitude"),
            "longitude": loc.get("longitude"),
            "distance_m": loc.get("distance_m"),
        },
    }]


def parse_tracking_status(envelope: dict) -> list[dict]:
    """TRACKING_STATUS envelope → track_points 행 dict 리스트 (순수 함수).

    - tracking != "active" → [] (lost/idle 는 저장 안 함)
    - targets[] 없으면 구버전 단일 target 방어 정규화
    - 필수 필드(track_id/observed_at/lat/lng) 결손 타겟은 스킵
    """
    body = envelope.get("body") or {}
    tracking_state = body.get("tracking")
    if tracking_state != "active":
        return []

    targets = body.get("targets")
    if not targets:
        targets = _normalize_legacy(body, envelope)

    camera_id = body.get("camera_id")
    rows: list[dict] = []
    for t in targets:
        try:
            loc = t.get("location") or {}
            track_id = t.get("track_id")
            observed = t.get("observed_at")
            lat = loc.get("latitude")
            lng = loc.get("longitude")
            if track_id is None or observed is None or lat is None or lng is None:
                continue
            rows.append({
                "camera_id": camera_id,
                "track_id": str(track_id),
                "label": t.get("label"),
                "threat_level": t.get("threat_level"),
                "latitude": float(lat),
                "longitude": float(lng),
                "distance_m": loc.get("distance_m"),
                "confidence": t.get("confidence"),
                "observed_at": _parse_observed_at(observed),
                "tracking_state": tracking_state,
            })
        except Exception:
            continue  # 잘못된 타겟 1건이 메시지 전체를 죽이지 않도록
    return rows


async def _insert_rows(pool, rows: list[dict]) -> int:
    if not rows:
        return 0
    # created_at = 인제스트 시각(naive KST). raw asyncpg 경로라 ORM Python default 미적용 →
    # 명시 지정(컬럼 NOT NULL, DB default 없음).
    ingested_at = datetime.now(KST).replace(tzinfo=None)
    params = [
        (r["camera_id"], r["track_id"], r["label"], r["threat_level"],
         r["latitude"], r["longitude"], r["distance_m"], r["confidence"],
         r["observed_at"], r["tracking_state"], ingested_at)
        for r in rows
    ]
    async with pool.acquire() as conn:
        await conn.executemany(INSERT_SQL, params)
    return len(rows)


async def _connect_db(asyncpg, db_url: str):
    """DB 기동 대기(컨테이너 startup 레이스 대비) 후 풀 생성."""
    for attempt in range(30):
        try:
            return await asyncpg.create_pool(db_url, min_size=1, max_size=4)
        except Exception as e:
            print(f"[gis-ingest] DB 연결 대기({attempt + 1}/30): {e}")
            await asyncio.sleep(2)
    raise RuntimeError("DB 연결 실패(timeout)")


async def run(db_url: str, nats_url: str, unit_id: str) -> None:
    import asyncpg
    import nats

    pool = await _connect_db(asyncpg, db_url)
    nc = await nats.connect(
        nats_url,
        reconnect_time_wait=2,
        max_reconnect_attempts=-1,  # 무한 재연결
    )

    async def handler(msg):
        try:
            envelope = json.loads(msg.data.decode())
            rows = parse_tracking_status(envelope)
            n = await _insert_rows(pool, rows)
            if n:
                cam = (envelope.get("body") or {}).get("camera_id")
                print(f"[gis-ingest] +{n} track_points (cam={cam})")
        except Exception as e:
            print(f"[gis-ingest] ERROR(skip msg): {e}")

    await nc.subscribe(SUBJECT, cb=handler)
    print(f"[gis-ingest] Subscribed {SUBJECT} → postgres (unit_id={unit_id}, nats={nats_url})")

    try:
        while True:
            await asyncio.sleep(1)
    finally:
        await nc.close()
        await pool.close()


if __name__ == "__main__":
    db_url = os.environ["DATABASE_URL"]
    nats_url = os.environ.get("NATS_URL", "nats://localhost:4222")
    unit_id = os.environ.get("UNIT_ID", "unit001")
    asyncio.run(run(db_url, nats_url, unit_id))
