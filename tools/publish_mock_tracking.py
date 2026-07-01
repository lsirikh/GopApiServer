"""
publish_mock_tracking.py — NATS로 모의(mock) 추적 세션 발행

목적: .NET GIS 앱의 추적 Playback/캘린더 테스트용 데이터 적재.
경로: 발행기 → NATS(sensorway.unit001.gis.tracking-status)
      → 앱(TrackingStatusNatsSyncService) → 로컬 MariaDB(CameraTrackPoints)
      → Playback 콘솔에서 기간 조회/재생.

⚠ 전제: .NET 앱이 실행 중이고 NATS(localhost:4222)에 연결돼 구독 중이어야
   메시지가 로컬 DB에 영속된다(NATS core는 비영속 — 구독자 없으면 그냥 버려짐).

생성물:
  - 20 세션(= 고유 track_id 20개), 각 120점(>100) 1Hz 보행 경로.
  - 최근 7일(KST)에 분산 — D-1~D-6 세션은 저녁(20:30/21:30/22:30 KST)에 배치해
    Playback 캘린더로 그 날짜를 '하루 통째' 선택해도 MaxPlaybackHours(기본 6h)
    클램프 윈도(해당일 18:00~24:00) 안에 들어오게 함.
    오늘(D-0) 세션은 '미래 금지'(앱이 now+5분 초과 observed_at 드롭) 때문에
    최근 과거(now−10/22/34분)로 재배치 → '최근 N분' 프리셋으로 조회 권장.

실행: python tools/publish_mock_tracking.py
      (옵션 환경변수: NATS_URL, UNIT_ID, SESSIONS, POINTS)
"""
import asyncio
import json
import math
import os
import random
import uuid
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import sys

import nats

# Windows 콘솔(cp949)에서도 한글/em-dash 출력이 깨지거나 죽지 않도록 UTF-8 강제
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

KST = ZoneInfo("Asia/Seoul")

NATS_URL = os.environ.get("NATS_URL", "nats://localhost:4222")
UNIT_ID = os.environ.get("UNIT_ID", "unit001")
SUBJECT = f"sensorway.{UNIT_ID}.gis.tracking-status"
SESSIONS = int(os.environ.get("SESSIONS", "20"))
POINTS = int(os.environ.get("POINTS", "120"))   # 세션당 점 수(>100)

BASE_LAT, BASE_LNG = 37.39404047, 126.96630120  # 적재 기준 좌표(세션컨텍스트)
EVENING_SLOTS = [(20, 30), (21, 30), (22, 30)]   # KST 저녁 슬롯(시,분)
LABELS = ["person", "vehicle", "animal"]
THREATS = ["NORMAL", "CAUTION", "THREAT"]

random.seed(20260629)   # 재현성


def session_start_utc(s: int, now_utc: datetime, now_kst: datetime) -> datetime:
    """세션 s의 시작 시각(UTC, tz-aware). 과거 보장."""
    day_offset = s % 7          # 0(오늘) ~ 6
    slot = s // 7               # 0,1,2 → 저녁 슬롯
    h, m = EVENING_SLOTS[slot]
    date_kst = (now_kst - timedelta(days=day_offset)).date()
    start_kst = datetime(date_kst.year, date_kst.month, date_kst.day, h, m, tzinfo=KST)
    start_utc = start_kst.astimezone(timezone.utc)
    # 미래(또는 너무 임박) 방지: 오늘 저녁이 아직 안 왔으면 최근 과거로 재배치
    if start_utc + timedelta(seconds=POINTS) > now_utc - timedelta(seconds=30):
        start_utc = now_utc - timedelta(minutes=10 + 12 * slot) - timedelta(seconds=POINTS)
    return start_utc


def make_targets(start_utc: datetime, track_id: str, label: str, threat: str) -> list[dict]:
    """세션 1건의 targets[] — 1Hz 보행 경로(랜덤워크)."""
    lat = BASE_LAT + random.uniform(-0.003, 0.003)   # 세션별 시작 분산(~±300m)
    lng = BASE_LNG + random.uniform(-0.003, 0.003)
    heading = random.uniform(0, 2 * math.pi)
    targets = []
    for i in range(POINTS):
        step = random.uniform(0.8, 1.8) * 1e-5        # 보행자 ~1.4 m/s
        heading += random.uniform(-0.3, 0.3)          # 완만한 방향 변화
        lat += step * math.cos(heading)
        lng += step * math.sin(heading) / math.cos(math.radians(lat))
        ts = start_utc + timedelta(seconds=i)
        targets.append({
            "track_id": track_id,
            "label": label,
            "threat_level": threat,
            "confidence": round(random.uniform(0.6, 0.98), 3),
            "observed_at": ts.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "location": {
                "latitude": round(lat, 7),
                "longitude": round(lng, 7),
                "distance_m": round(random.uniform(5, 120), 1),
            },
        })
    return targets


def build_envelope(cam: int, targets: list[dict]) -> dict:
    """Gop_Message_Broker §8.3.7 TRACKING_STATUS envelope."""
    return {
        "id": str(uuid.uuid4()),
        "m_type": "PUB",
        "cmd": "TRACKING_STATUS",
        "from": "MockPublisher",
        "body": {
            "camera_id": cam,
            "tracking": "active",
            "ttl_sec": 5,
            "frame_width": 1920,
            "frame_height": 1080,
            "targets": targets,
        },
        "created": datetime.now(KST).isoformat(),
    }


async def main() -> None:
    now_utc = datetime.now(timezone.utc)
    now_kst = now_utc.astimezone(KST)

    nc = await nats.connect(NATS_URL)
    print(f"[mock-pub] connected {NATS_URL} → {SUBJECT}")
    print(f"[mock-pub] now(KST)={now_kst:%Y-%m-%d %H:%M:%S}  sessions={SESSIONS} points/session={POINTS}\n")
    print(f"{'track_id':22} {'cam':>4} {'label':8} {'threat':8} {'관측구간(KST)':32} {'점':>4}")
    print("-" * 86)

    total = 0
    for s in range(SESSIONS):
        cam = 101 + (s % 6)
        label = LABELS[s % 3]
        threat = THREATS[s % 3]
        start_utc = session_start_utc(s, now_utc, now_kst)
        start_kst = start_utc.astimezone(KST)
        end_kst = (start_utc + timedelta(seconds=POINTS - 1)).astimezone(KST)
        track_id = f"mock-{start_kst:%Y%m%d}-{s:02d}"

        targets = make_targets(start_utc, track_id, label, threat)
        await nc.publish(SUBJECT, json.dumps(build_envelope(cam, targets)).encode())
        total += len(targets)

        span = f"{start_kst:%m-%d %H:%M:%S}~{end_kst:%H:%M:%S}"
        print(f"{track_id:22} {cam:>4} {label:8} {threat:8} {span:32} {len(targets):>4}")
        await asyncio.sleep(0.03)   # 완만한 송출

    await nc.flush()
    await asyncio.sleep(0.3)        # 앱 측 버퍼 소비 여유
    await nc.drain()
    print("-" * 86)
    print(f"[mock-pub] DONE — {SESSIONS} 세션 / 총 {total} 점 발행 완료.")
    print("[mock-pub] 앱이 떠 있었다면 로컬 DB에 적재됨 → Playback에서 위 날짜로 조회.")


if __name__ == "__main__":
    asyncio.run(main())
