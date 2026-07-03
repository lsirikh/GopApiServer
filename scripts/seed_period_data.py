"""
Seed period data — 2026-06-01 ~ 2026-07-03 (33일)

규칙 (사용자 확정):
1. Controllers 6개 + Sensors 48개(Fence 24, SmartSensor 12, SmartSensor2 12)
2. Cameras 30, Lamps 10, Speakers 10, Enclosures 10
3. DetectionEvent 2000/day → 센서 48개 기반 (Fence/SmartSensor/SmartSensor2만)
4. MalfunctionEvent 800/day → Controllers 6 + Sensors 48 = 54 장비 기반
5. ActionEvent 500/day → Detection/Malfunction 이벤트 subset을 from_event_id로 참조

실행:
    docker exec api-test-server python scripts/seed_period_data.py [--clean]

옵션:
    --clean: 기존 시드용 devices(number_device >= 1000) + 기간 내 events 삭제 후 재생성
"""
from __future__ import annotations

import argparse
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import SessionLocal
# 모든 모델 import로 SQLAlchemy relationship 매핑 등록 (AuditLog → AccountUser 등 참조 관계)
from app import models  # noqa: F401  (__init__.py 로드)
from app.models import user as _user_m  # noqa: F401  (AccountUser 등)
from app.models import log as _log_m  # noqa: F401  (ApiLog)
from app.models import report as _report_m  # noqa: F401  (ReportTemplate/Generation)
from app.models import config_change_log as _cfg_m  # noqa: F401
from app.models import token_blacklist as _tb_m  # noqa: F401
from app.models import app_settings as _appset_m  # noqa: F401
from app.models.device import (
    Device, Controller, Sensor, Camera, Speaker, Enclosure, Lamp,
)
from app.models.event import (
    Event, DetectionEvent, MalfunctionEvent, ActionEvent,
)
from app.utils.enums import (
    EnumDeviceCategory, EnumDeviceType, EnumDeviceStatus,
    EnumCameraMode, EnumCameraType, EnumSpeakerType, EnumDoorStatus,
    EnumDetectionType, EnumFaultType,
)


# ── 설정 ─────────────────────────────────────────────────────────
SEED_NUMBER_BASE = 1000  # number_device 시작값 (기존 데이터 충돌 회피)
START_DATE = datetime(2026, 6, 1, 0, 0, 0)
END_DATE = datetime(2026, 7, 4, 0, 0, 0)  # exclusive → 6/1 ~ 7/3 포함 (33일)

DETECTIONS_PER_DAY = 2000
MALFUNCTIONS_PER_DAY = 800
ACTIONS_PER_DAY = 500

BATCH_SIZE = 500
RANDOM_SEED = 20260703


# ── 재현성 확보 ─────────────────────────────────────────────────
random.seed(RANDOM_SEED)


# ── 유틸 ─────────────────────────────────────────────────────────
def _now_naive():
    return datetime.utcnow()


def _weighted_hour():
    """야간(00-06) / 저녁(18-23) 가중 → 실제 침입/장애 패턴 근사."""
    # 확률 분포: 0-5시 25%, 6-17시 40%, 18-23시 35%
    r = random.random()
    if r < 0.25:
        return random.randint(0, 5)
    elif r < 0.65:
        return random.randint(6, 17)
    else:
        return random.randint(18, 23)


def _random_moment_in_day(day: datetime) -> datetime:
    return day.replace(
        hour=_weighted_hour(),
        minute=random.randint(0, 59),
        second=random.randint(0, 59),
        microsecond=0,
    )


# ── 클린 (옵션) ─────────────────────────────────────────────────
def clean_previous_seed(db: Session):
    """이전 시드(시드 범위 devices + 대상 기간 events) 정리."""
    print("[CLEAN] 기존 시드 정리 중...")

    # 1) 대상 기간 이벤트 삭제 (action_events → child event tables → events)
    #    ActionEvent from_event_id는 SET NULL이라 event 삭제 시 자동 처리되지만,
    #    이 스크립트가 만든 action은 명시 시각으로 함께 지우는 게 청결.
    db.execute(text("DELETE FROM action_events WHERE created_at >= :s AND created_at < :e"),
               {"s": START_DATE, "e": END_DATE})
    db.execute(text("DELETE FROM detection_events WHERE id IN (SELECT id FROM events WHERE created_at >= :s AND created_at < :e)"),
               {"s": START_DATE, "e": END_DATE})
    db.execute(text("DELETE FROM malfunction_events WHERE id IN (SELECT id FROM events WHERE created_at >= :s AND created_at < :e)"),
               {"s": START_DATE, "e": END_DATE})
    db.execute(text("DELETE FROM connection_events WHERE id IN (SELECT id FROM events WHERE created_at >= :s AND created_at < :e)"),
               {"s": START_DATE, "e": END_DATE})
    db.execute(text("DELETE FROM events WHERE created_at >= :s AND created_at < :e"),
               {"s": START_DATE, "e": END_DATE})

    # 2) 시드 devices(number_device >= 1000) 삭제 — CASCADE로 child 정리
    db.execute(text("DELETE FROM devices WHERE number_device >= :n"),
               {"n": SEED_NUMBER_BASE})
    db.commit()
    print("[CLEAN] 완료")


# ── Device 생성 ─────────────────────────────────────────────────
def create_devices(db: Session) -> dict:
    """
    반환:
        {
          "controllers": [Controller, ...],  # 6
          "sensors":     [Sensor, ...],      # 48 (Fence 24 + SS 12 + SS2 12)
          "cameras":     [Camera, ...],      # 30
          "lamps":       [Lamp, ...],        # 10
          "speakers":    [Speaker, ...],     # 10
          "enclosures":  [Enclosure, ...],   # 10
        }
    """
    print("[DEVICE] 인벤토리 생성 중...")
    now = _now_naive()

    # -- Controllers (6) --
    controllers = []
    for i in range(6):
        c = Controller(
            category_device=EnumDeviceCategory.CONTROLLER,
            number_device=SEED_NUMBER_BASE + i,
            group_device=(i // 2) + 1,  # 3 그룹 (2대씩)
            name_device=f"제어기_{i+1:02d}",
            type_device=EnumDeviceType.Controller,
            version="v3.2",
            status=EnumDeviceStatus.ACTIVATED,
            is_enable=True,
            ip_address=f"192.168.100.{10 + i}",
            ip_port=8000,
            geolocation={
                "location": f"전방구역-{chr(65+i)}",
                "latitude": 38.0 + i * 0.01,
                "longitude": 127.0 + i * 0.01,
            },
            created_at=now, updated_at=now,
        )
        db.add(c)
        controllers.append(c)
    db.flush()  # id 확보

    # -- Sensors (48 = Fence 24 + SmartSensor 12 + SmartSensor2 12) --
    sensors = []
    sensor_types = (
        [EnumDeviceType.Fence] * 24
        + [EnumDeviceType.SmartSensor] * 12
        + [EnumDeviceType.SmartSensor2] * 12
    )
    random.shuffle(sensor_types)
    for i, sensor_type in enumerate(sensor_types):
        controller = controllers[i % len(controllers)]
        s = Sensor(
            category_device=EnumDeviceCategory.SENSOR,
            number_device=SEED_NUMBER_BASE + 100 + i,
            group_device=controller.group_device,
            name_device=f"{sensor_type.value}_{i+1:03d}",
            type_device=sensor_type,
            version="v2.1",
            status=EnumDeviceStatus.ACTIVATED,
            is_enable=True,
            controller_id=controller.id,
            geolocation={
                "location": f"센서-{i+1:03d}",
                "latitude": 38.0 + i * 0.001,
                "longitude": 127.0 + i * 0.001,
            },
            created_at=now, updated_at=now,
        )
        db.add(s)
        sensors.append(s)

    # -- Cameras (30) --
    cameras = []
    for i in range(30):
        cam = Camera(
            category_device=EnumDeviceCategory.CAMERA,
            number_device=SEED_NUMBER_BASE + 200 + i,
            group_device=(i // 5) + 1,  # 6 그룹 (5대씩)
            name_device=f"카메라_{i+1:02d}",
            type_device=EnumDeviceType.IpCamera,
            version="v4.0",
            status=EnumDeviceStatus.ACTIVATED,
            is_enable=True,
            ip_address=f"192.168.101.{10 + i}",
            ip_port=554,
            user_name="admin",
            user_password="camera_pw",
            urls={"rtsp": f"rtsp://192.168.101.{10+i}:554/stream1"},
            mode=EnumCameraMode.ONVIF,
            category=(EnumCameraType.PTZ if i % 3 == 0 else EnumCameraType.FIXED),
            is_record=(i % 4 == 0),
            geolocation={
                "location": f"카메라구역-{i+1:02d}",
                "latitude": 38.05 + i * 0.001,
                "longitude": 127.05 + i * 0.001,
            },
            created_at=now, updated_at=now,
        )
        db.add(cam)
        cameras.append(cam)

    # -- Lamps (10) --
    lamps = []
    for i in range(10):
        lp = Lamp(
            category_device=EnumDeviceCategory.LAMP,
            number_device=SEED_NUMBER_BASE + 300 + i,
            group_device=(i // 3) + 1,
            name_device=f"경광등_{i+1:02d}",
            type_device=EnumDeviceType.Lamp,
            version="v1.1",
            status=EnumDeviceStatus.ACTIVATED,
            is_enable=True,
            ip_address=f"192.168.102.{10 + i}",
            ip_port=80,
            user_name="admin",
            user_password="lamp_pw",
            description=f"경광등 #{i+1} — 초소 앞 배치",
            geolocation={
                "location": f"경광등-{i+1:02d}",
                "latitude": 38.1 + i * 0.001,
                "longitude": 127.1 + i * 0.001,
            },
            created_at=now, updated_at=now,
        )
        db.add(lp)
        lamps.append(lp)

    # -- Speakers (10) --
    speakers = []
    for i in range(10):
        sp = Speaker(
            category_device=EnumDeviceCategory.SPEAKER,
            number_device=SEED_NUMBER_BASE + 400 + i,
            group_device=(i // 3) + 1,
            name_device=f"스피커_{i+1:02d}",
            type_device=EnumDeviceType.IpSpeaker,
            version="v2.0",
            status=EnumDeviceStatus.ACTIVATED,
            is_enable=True,
            speaker_type=(EnumSpeakerType.MONITOR if i == 0 else EnumSpeakerType.NORMAL),
            server_id=None,
            description=f"스피커 #{i+1} — 방송용",
            geolocation={
                "location": f"스피커-{i+1:02d}",
                "latitude": 38.15 + i * 0.001,
                "longitude": 127.15 + i * 0.001,
            },
            created_at=now, updated_at=now,
        )
        db.add(sp)
        speakers.append(sp)

    # -- Enclosures (10) --
    enclosures = []
    for i in range(10):
        enc = Enclosure(
            category_device=EnumDeviceCategory.ENCLOSURE,
            number_device=SEED_NUMBER_BASE + 500 + i,
            group_device=(i // 3) + 1,
            name_device=f"함체_{i+1:02d}",
            type_device=EnumDeviceType.Enclosure,
            version="v1.1",
            status=EnumDeviceStatus.ACTIVATED,
            is_enable=True,
            door_status=EnumDoorStatus.CLOSED,
            geolocation={
                "location": f"함체-{i+1:02d}",
                "latitude": 38.2 + i * 0.001,
                "longitude": 127.2 + i * 0.001,
            },
            threshold_config={
                "temperature_warning": 40,
                "temperature_critical": 50,
                "humidity_warning": 80,
                "humidity_critical": 90,
            },
            heater_enabled=False,
            fan_enabled=(i % 2 == 0),
            created_at=now, updated_at=now,
        )
        db.add(enc)
        enclosures.append(enc)

    db.commit()
    print(
        f"[DEVICE] 생성 완료 — "
        f"Controllers {len(controllers)}, Sensors {len(sensors)} "
        f"(Fence {sum(1 for s in sensors if s.type_device == EnumDeviceType.Fence)} "
        f"+ SmartSensor {sum(1 for s in sensors if s.type_device == EnumDeviceType.SmartSensor)} "
        f"+ SmartSensor2 {sum(1 for s in sensors if s.type_device == EnumDeviceType.SmartSensor2)}), "
        f"Cameras {len(cameras)}, Lamps {len(lamps)}, "
        f"Speakers {len(speakers)}, Enclosures {len(enclosures)}"
    )
    return {
        "controllers": controllers,
        "sensors": sensors,
        "cameras": cameras,
        "lamps": lamps,
        "speakers": speakers,
        "enclosures": enclosures,
    }


# ── 센서 타입별 탐지 결과 매핑 ──────────────────────────────────
DETECTION_BY_SENSOR_TYPE = {
    EnumDeviceType.Fence: [
        EnumDetectionType.CABLE_CUTTING,
        EnumDetectionType.CABLE_CONNECTED,
        EnumDetectionType.VIBRATION_SENSOR,
    ],
    EnumDeviceType.SmartSensor: [
        EnumDetectionType.PIR_SENSOR,
        EnumDetectionType.AI_DETECT,
        EnumDetectionType.CONTACT_SENSOR,
    ],
    EnumDeviceType.SmartSensor2: [
        EnumDetectionType.THERMAL_SENSOR,
        EnumDetectionType.AI_DETECT,
        EnumDetectionType.DISTANCE_SENSOR,
    ],
}

# 장비 타입별 장애 원인 매핑
FAULT_BY_DEVICE_TYPE = {
    EnumDeviceType.Controller: [
        EnumFaultType.FAULT_CONTROLLER,
        EnumFaultType.FAULT_ETC,
    ],
    EnumDeviceType.Fence: [
        EnumFaultType.FAULT_FENCE,
        EnumFaultType.FAULT_CABLE_CUTTING,
        EnumFaultType.FAULT_MULTI,
    ],
    EnumDeviceType.SmartSensor: [
        EnumFaultType.FAULT_ETC,
        EnumFaultType.FAULT_MULTI,
    ],
    EnumDeviceType.SmartSensor2: [
        EnumFaultType.FAULT_ETC,
        EnumFaultType.FAULT_MULTI,
    ],
}


# ── Event 생성 ──────────────────────────────────────────────────
def create_events(db: Session, inv: dict):
    print("[EVENT] 이벤트 생성 시작...")
    sensors = inv["sensors"]
    controllers = inv["controllers"]
    # 장애 대상 = controllers + sensors (54개)
    fault_targets = controllers + sensors

    total_days = (END_DATE - START_DATE).days
    print(f"  기간: {START_DATE.date()} ~ {(END_DATE - timedelta(days=1)).date()} ({total_days}일)")
    print(f"  하루 볼륨: Detection {DETECTIONS_PER_DAY} + Malfunction {MALFUNCTIONS_PER_DAY} + Action {ACTIONS_PER_DAY}")
    print(f"  총 예상: Detection {DETECTIONS_PER_DAY * total_days:,} + "
          f"Malfunction {MALFUNCTIONS_PER_DAY * total_days:,} + "
          f"Action {ACTIONS_PER_DAY * total_days:,}")

    all_source_event_ids = []  # 조치가 참조 가능한 (detection + malfunction) event id 저장

    for day_offset in range(total_days):
        day = START_DATE + timedelta(days=day_offset)

        # ── Detection ──
        detections_today = []
        for _ in range(DETECTIONS_PER_DAY):
            sensor = random.choice(sensors)
            result = random.choice(DETECTION_BY_SENSOR_TYPE[sensor.type_device])
            ts = _random_moment_in_day(day)
            det = DetectionEvent(
                category_event="detection",
                type_event="Intrusion",
                device_id=sensor.id,
                device_description=f"{sensor.type_device.value}:{sensor.name_device}",
                result=result,
                action_reported="False",
                detail={
                    "thumbnail": f"http://cam.local/thumb/{random.randint(1, 30):02d}.jpg",
                    "signal": random.randint(30, 100),
                },
                created_at=ts, updated_at=ts,
            )
            db.add(det)
            detections_today.append(det)
        db.flush()
        all_source_event_ids.extend(d.id for d in detections_today)

        # ── Malfunction ──
        malfunctions_today = []
        for _ in range(MALFUNCTIONS_PER_DAY):
            target = random.choice(fault_targets)
            reason = random.choice(FAULT_BY_DEVICE_TYPE.get(
                target.type_device,
                [EnumFaultType.FAULT_ETC],
            ))
            ts = _random_moment_in_day(day)
            mal = MalfunctionEvent(
                category_event="malfunction",
                type_event="Fault",
                device_id=target.id,
                device_description=f"{target.type_device.value}:{target.name_device}",
                reason=reason,
                action_reported="False",
                detail={
                    "first_start": random.randint(0, 200),
                    "first_end": random.randint(200, 500),
                },
                created_at=ts, updated_at=ts,
            )
            db.add(mal)
            malfunctions_today.append(mal)
        db.flush()
        all_source_event_ids.extend(m.id for m in malfunctions_today)

        # ── Action ── (Detection/Malfunction 중 subset을 참조)
        source_pool = [d.id for d in detections_today] + [m.id for m in malfunctions_today]
        for _ in range(ACTIONS_PER_DAY):
            src_id = random.choice(source_pool)
            ts = _random_moment_in_day(day)
            act = ActionEvent(
                from_event_id=src_id,
                type_event="Action",
                content=random.choice([
                    "현장 확인 결과 이상 없음",
                    "침입 확인 및 경비 출동",
                    "장비 재부팅으로 복구",
                    "센서 청소 후 정상화",
                    "케이블 교체 완료",
                    "야생동물 감지로 오탐 처리",
                ]),
                user=random.choice(["operator1", "operator2", "operator3", "admin"]),
                created_at=ts, updated_at=ts,
            )
            db.add(act)

        db.commit()
        if (day_offset + 1) % 5 == 0 or day_offset == total_days - 1:
            print(f"  [{day_offset+1:02d}/{total_days}] {day.date()} 커밋")

    print("[EVENT] 완료")


# ── 검증 ────────────────────────────────────────────────────────
def verify(db: Session):
    print("\n[VERIFY] 결과 카운트")
    rows = db.execute(
        text("""
        SELECT 'controllers' AS kind, COUNT(*) FROM controllers
        UNION ALL SELECT 'sensors_fence', COUNT(*) FROM sensors s JOIN devices d ON d.id=s.id WHERE d.type_device='Fence'
        UNION ALL SELECT 'sensors_smart', COUNT(*) FROM sensors s JOIN devices d ON d.id=s.id WHERE d.type_device='SmartSensor'
        UNION ALL SELECT 'sensors_smart2', COUNT(*) FROM sensors s JOIN devices d ON d.id=s.id WHERE d.type_device='SmartSensor2'
        UNION ALL SELECT 'cameras', COUNT(*) FROM cameras
        UNION ALL SELECT 'lamps', COUNT(*) FROM lamps
        UNION ALL SELECT 'speakers', COUNT(*) FROM speakers
        UNION ALL SELECT 'enclosures', COUNT(*) FROM enclosures
        UNION ALL SELECT 'events (period)', COUNT(*) FROM events WHERE created_at >= :s AND created_at < :e
        UNION ALL SELECT 'detections (period)', COUNT(*) FROM detection_events d JOIN events e ON e.id=d.id WHERE e.created_at >= :s AND e.created_at < :e
        UNION ALL SELECT 'malfunctions (period)', COUNT(*) FROM malfunction_events m JOIN events e ON e.id=m.id WHERE e.created_at >= :s AND e.created_at < :e
        UNION ALL SELECT 'actions (period)', COUNT(*) FROM action_events WHERE created_at >= :s AND created_at < :e
        """),
        {"s": START_DATE, "e": END_DATE},
    ).all()
    for r in rows:
        print(f"  {r[0]:26s} = {r[1]:,}")


# ── main ────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", action="store_true", help="기존 시드(number_device>=1000) + 기간 이벤트 삭제 후 재생성")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.clean:
            clean_previous_seed(db)

        # 이미 시드가 있으면 device 생성 스킵
        exists = db.execute(
            text("SELECT COUNT(*) FROM devices WHERE number_device >= :n"),
            {"n": SEED_NUMBER_BASE},
        ).scalar()
        if exists and not args.clean:
            print(f"[DEVICE] 기존 시드 감지 (number_device>={SEED_NUMBER_BASE} 총 {exists}개) — device 생성 스킵")
            # 이벤트 생성은 기존 시드 device 참조로 이어감
            controllers = db.query(Controller).filter(Controller.number_device >= SEED_NUMBER_BASE).all()
            sensors = db.query(Sensor).filter(
                Sensor.number_device >= SEED_NUMBER_BASE,
                Sensor.type_device.in_([EnumDeviceType.Fence, EnumDeviceType.SmartSensor, EnumDeviceType.SmartSensor2]),
            ).all()
            inv = {"controllers": controllers, "sensors": sensors}
        else:
            inv = create_devices(db)

        create_events(db, inv)
        verify(db)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
