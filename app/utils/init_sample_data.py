"""
Sample data initialization for development/demo environment.
Creates comprehensive sample data across all GOP schema tables.

Requirements:
- Events: 28000+ records (3000 detection/3일, 5000 malfunction/5일, 20000 connection)
- Action events: 5000 (조치보고), ~1000 events remain unreported
- Devices: Controllers 4 (A/B/C/D), Sensors 402 (Ctrl1:Fence 100+Multi 21, Ctrl2:Fence 100+Multi 21, Ctrl3:SmartCompound 60, Ctrl4:SmartSensor 100), Cameras 300, Speakers 200, Enclosures 30, Lamps 30
- DeviceGroups: 5 groups with device mappings
- Users: 5 (excluding admin)
- Login logs, sessions, system events, config change logs, audit logs
- CameraPresets + ROI + XyPoints for PTZ cameras
- EnclosureMetrics time-series data
- DetectionEvent detail JSONB (AI 탐지 상세)

Idempotent: Safe to call multiple times — skips if data already exists.
"""
import random
import uuid
from datetime import datetime, timedelta
from sqlalchemy import insert, select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.user import UserGroup, AccountUser, UserSession, UserLoginLog
from app.models.device import Device, Controller, Sensor, Camera, Speaker, Enclosure, Lamp, EnclosureMetric
from app.models.device_group import DeviceGroup, DeviceGroupMapping
from app.models.camera_preset import CameraPreset, ROI, XyPoint
from app.models.event import Event, DetectionEvent, MalfunctionEvent, ConnectionEvent, ActionEvent
from app.models.system_event import SystemEvent
from app.models.config_change_log import ConfigChangeLog
from app.models.audit_log import AuditLog
from app.models.server import Server, ServerCategory
from app.models.device_setting import ProxySetting, CameraSetting
from app.utils.enums import (
    EnumDeviceType, EnumDeviceStatus, EnumDeviceCategory,
    EnumCameraMode, EnumCameraType, EnumSpeakerType, EnumDoorStatus,
    EnumDetectionType, EnumFaultType,
    EnumSystemEventType, EnumSystemEventSeverity,
    EnumLoginAction, EnumLoginResult,
    EnumAuditActionType, EnumAuditResourceType, EnumAuditStatus,
    EnumConfigResourceType, EnumConfigActionType,
    EnumServerType, EnumServerStatus,
    EnumOperationMode, EnumWindyMode,
    EnumWeatherMode, EnumCameraVideoMode, EnumOnOff,
    EnumDayNightMode, EnumPalette,
    EnumFocusMode, EnumIrisMode, EnumTrackingStatus,
)
from app.utils.auth import hash_password
from app.config import settings

# Reproducible random for consistent sample data
random.seed(42)


# ── GOP 좌표 데이터 ─────────────────────────────────────
# 실제 GOP(일반전초) 경계 지역 기반 가상 좌표 (강원도 철원~화천 일대)

GOP_COORDS = [
    # A구역 (서쪽) — 철원 일대
    {"location": "A구역-초소1", "latitude": 38.3145, "longitude": 127.1312, "altitude": 285.0},
    {"location": "A구역-초소2", "latitude": 38.3178, "longitude": 127.1401, "altitude": 310.0},
    {"location": "A구역-초소3", "latitude": 38.3201, "longitude": 127.1489, "altitude": 295.0},
    {"location": "A구역-감시탑", "latitude": 38.3220, "longitude": 127.1350, "altitude": 340.0},
    # B구역 (중앙) — 화천 일대
    {"location": "B구역-초소1", "latitude": 38.3310, "longitude": 127.1620, "altitude": 320.0},
    {"location": "B구역-초소2", "latitude": 38.3342, "longitude": 127.1708, "altitude": 305.0},
    {"location": "B구역-초소3", "latitude": 38.3375, "longitude": 127.1795, "altitude": 330.0},
    {"location": "B구역-감시탑", "latitude": 38.3390, "longitude": 127.1700, "altitude": 365.0},
    # C구역 (동쪽)
    {"location": "C구역-초소1", "latitude": 38.3480, "longitude": 127.1950, "altitude": 340.0},
    {"location": "C구역-초소2", "latitude": 38.3512, "longitude": 127.2038, "altitude": 355.0},
    {"location": "C구역-초소3", "latitude": 38.3545, "longitude": 127.2125, "altitude": 370.0},
    {"location": "C구역-감시탑", "latitude": 38.3560, "longitude": 127.2050, "altitude": 395.0},
    # D구역 (동북쪽) — 양구 일대
    {"location": "D구역-초소1", "latitude": 38.4215, "longitude": 127.8820, "altitude": 310.0},
    {"location": "D구역-초소2", "latitude": 38.4248, "longitude": 127.8905, "altitude": 325.0},
    {"location": "D구역-초소3", "latitude": 38.4280, "longitude": 127.8990, "altitude": 340.0},
    {"location": "D구역-감시탑", "latitude": 38.4295, "longitude": 127.8870, "altitude": 375.0},
    # E구역 (북쪽) — 인제 일대
    {"location": "E구역-초소1", "latitude": 38.3890, "longitude": 128.1620, "altitude": 295.0},
    {"location": "E구역-초소2", "latitude": 38.3920, "longitude": 128.1710, "altitude": 315.0},
    {"location": "E구역-초소3", "latitude": 38.3955, "longitude": 128.1800, "altitude": 330.0},
    {"location": "E구역-감시탑", "latitude": 38.3970, "longitude": 128.1700, "altitude": 360.0},
]


def _geo(zone_idx: int, sub_idx: int = 0) -> dict:
    """Generate geolocation for zone (0=A, 1=B, 2=C) with sub-offset."""
    base = GOP_COORDS[zone_idx * 4 + (sub_idx % 4)]
    offset_lat = random.uniform(-0.002, 0.002)
    offset_lng = random.uniform(-0.002, 0.002)
    return {
        "location": base["location"],
        "latitude": round(base["latitude"] + offset_lat, 6),
        "longitude": round(base["longitude"] + offset_lng, 6),
        "altitude": round(base["altitude"] + random.uniform(-10, 10), 1),
    }


# ── Helpers ──────────────────────────────────────────────

def _rand_dt(days_back: int = 30) -> datetime:
    """Random datetime within the last N days."""
    now = datetime.now(settings.tz).replace(tzinfo=None)
    delta = timedelta(
        days=random.randint(0, days_back),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )
    return now - delta


def _rand_ip(prefix: str = "192.168") -> str:
    return f"{prefix}.{random.randint(1, 254)}.{random.randint(1, 254)}"


# ── User Groups ──────────────────────────────────────────

def _create_user_groups(db: Session) -> dict:
    """Create 3 user groups. Returns {name: id} mapping."""
    if db.query(UserGroup).count() > 0:
        groups = db.query(UserGroup).all()
        print(f"  [OK] User groups already exist: {len(groups)}")
        return {g.name: g.id for g in groups}

    # PRD v4.9 Phase 3 (A-2.4): nested dict 정규화 — flat 'rw'/'r' 폐기
    # 시드 재실행 시에도 PermissionsSchema 통과 보장
    _RW = {"view": True, "edit": True, "delete": False, "control": False}
    _R = {"view": True, "edit": False, "delete": False, "control": False}
    _CTRL = {"view": True, "edit": True, "delete": False, "control": True}
    data = [
        {"name": "운영팀", "description": "시스템 운영 담당",
         "permissions": {"modules": {"devices": _RW, "events": _RW, "reports": _RW, "cameras": _CTRL}}, "is_active": True},
        {"name": "관제팀", "description": "관제 모니터링 담당",
         "permissions": {"modules": {"devices": _R, "events": _R, "reports": _R, "cameras": _R}}, "is_active": True},
        {"name": "유지보수팀", "description": "장비 유지보수 담당",
         "permissions": {"modules": {"devices": _RW, "events": _R, "reports": _R}}, "is_active": True},
    ]
    result = {}
    for d in data:
        g = UserGroup(**d)
        db.add(g)
        db.flush()
        result[g.name] = g.id
    db.commit()
    print(f"  [OK] User groups created: {len(data)}")
    return result


# ── Users ────────────────────────────────────────────────

# v5.3 Phase 2 (2026-07-02): role = "USER" 통일 (Role 축소, PRD_Role_Simplification).
# 권한은 group_key로 배정된 그룹의 매트릭스에서 산출 — role은 특권 라벨(ADMIN 여부)만.
SAMPLE_USERS = [
    {"login_id": "operator1", "name": "김운영", "role": "USER",
     "email": "operator1@gop.kr", "department": "운영부", "position": "주임",
     "employee_number": "EMP001", "phone": "010-1234-5001", "group_key": "운영팀"},
    {"login_id": "operator2", "name": "이운영", "role": "USER",
     "email": "operator2@gop.kr", "department": "운영부", "position": "대리",
     "employee_number": "EMP002", "phone": "010-1234-5002", "group_key": "운영팀"},
    {"login_id": "monitor1", "name": "박관제", "role": "USER",
     "email": "monitor1@gop.kr", "department": "관제센터", "position": "사원",
     "employee_number": "EMP003", "phone": "010-1234-5003", "group_key": "관제팀"},
    {"login_id": "monitor2", "name": "최관제", "role": "USER",
     "email": "monitor2@gop.kr", "department": "관제센터", "position": "사원",
     "employee_number": "EMP004", "phone": "010-1234-5004", "group_key": "관제팀"},
    {"login_id": "maintainer1", "name": "정유지", "role": "USER",
     "email": "maintainer1@gop.kr", "department": "기술부", "position": "과장",
     "employee_number": "EMP005", "phone": "010-1234-5005", "group_key": "유지보수팀"},
]


def _create_users(db: Session, group_map: dict) -> list[int]:
    """Create 5 sample users (excluding admin). Returns list of user IDs."""
    existing = db.query(AccountUser).filter(AccountUser.login_id != "admin").count()
    if existing >= 5:
        users = db.query(AccountUser).filter(AccountUser.login_id != "admin").all()
        print(f"  [OK] Sample users already exist: {existing}")
        return [u.id for u in users]

    pw = hash_password("user123")
    ids = []
    for ud in SAMPLE_USERS:
        group_key = ud.pop("group_key")
        u = AccountUser(
            password_hash=pw,
            is_active=True,
            is_locked=False,
            group_id=group_map.get(group_key),
            **ud,
        )
        ud["group_key"] = group_key  # restore for re-entrant safety
        db.add(u)
        db.flush()
        ids.append(u.id)
    db.commit()
    print(f"  [OK] Sample users created: {len(ids)}")
    return ids


# ── Servers ──────────────────────────────────────────────

def _create_servers(db: Session) -> list[int]:
    """Create sample servers. Returns list of server IDs."""
    existing = db.query(Server).count()
    if existing > 0:
        print(f"  [OK] Servers already exist: {existing}")
        return [s.id for s in db.query(Server.id).all()]

    categories = db.query(ServerCategory).all()
    if not categories:
        print("  [WARN] No server categories — skipping servers")
        return []
    cat_map = {c.type_server: c.id for c in categories}

    servers = [
        {"category_id": cat_map.get(EnumServerType.VMS), "name": "VMS-01",
         "status": EnumServerStatus.NORMAL, "ip_address": "192.168.1.10", "port": 8080, "hostname": "vms-01"},
        {"category_id": cat_map.get(EnumServerType.VMS), "name": "VMS-02",
         "status": EnumServerStatus.NORMAL, "ip_address": "192.168.1.11", "port": 8080, "hostname": "vms-02"},
        {"category_id": cat_map.get(EnumServerType.AI_ANALYSIS), "name": "AI-01",
         "status": EnumServerStatus.NORMAL, "ip_address": "192.168.1.20", "port": 8081, "hostname": "ai-01"},
        {"category_id": cat_map.get(EnumServerType.AI_ANALYSIS), "name": "AI-02",
         "status": EnumServerStatus.WARNING, "ip_address": "192.168.1.21", "port": 8081, "hostname": "ai-02"},
        {"category_id": cat_map.get(EnumServerType.STREAMING), "name": "STREAM-01",
         "status": EnumServerStatus.NORMAL, "ip_address": "192.168.1.30", "port": 1935, "hostname": "stream-01"},
        {"category_id": cat_map.get(EnumServerType.STREAMING), "name": "STREAM-02",
         "status": EnumServerStatus.NORMAL, "ip_address": "192.168.1.31", "port": 1935, "hostname": "stream-02"},
        {"category_id": cat_map.get(EnumServerType.BROKER), "name": "BROKER-01",
         "status": EnumServerStatus.ERROR, "ip_address": "192.168.1.50", "port": 5672, "hostname": "broker-01"},
        {"category_id": cat_map.get(EnumServerType.BROKER), "name": "BROKER-02",
         "status": EnumServerStatus.NORMAL, "ip_address": "192.168.1.51", "port": 5672, "hostname": "broker-02"},
        {"category_id": cat_map.get(EnumServerType.DB_API), "name": "DBAPI-01",
         "status": EnumServerStatus.NORMAL, "ip_address": "192.168.1.60", "port": 5000, "hostname": "dbapi-01"},
        {"category_id": cat_map.get(EnumServerType.NVR_API), "name": "NVR-01",
         "status": EnumServerStatus.NORMAL, "ip_address": "192.168.1.70", "port": 8082, "hostname": "nvr-01"},
        {"category_id": cat_map.get(EnumServerType.SPEAKER_API), "name": "SPKAPI-01",
         "status": EnumServerStatus.NORMAL, "ip_address": "192.168.1.80", "port": 5001, "hostname": "spkapi-01"},
        {"category_id": cat_map.get(EnumServerType.ENCLOSURE_API), "name": "ENCAPI-01",
         "status": EnumServerStatus.NORMAL, "ip_address": "192.168.1.90", "port": 5002, "hostname": "encapi-01"},
    ]

    ids = []
    for sd in servers:
        if sd["category_id"] is not None:
            s = Server(**sd)
            db.add(s)
            db.flush()
            ids.append(s.id)
    db.commit()
    print(f"  [OK] Servers created: {len(ids)}")
    return ids


# ── Devices ──────────────────────────────────────────────


def _create_devices(db: Session, server_ids: list[int]) -> dict:
    """Create all devices with realistic GOP data. Returns {category: [ids]} mapping."""
    existing = db.query(Device).count()
    if existing > 0:
        print(f"  [OK] Devices already exist: {existing}")
        return {
            "controllers": [c.id for c in db.query(Controller).all()],
            "sensors": [s.id for s in db.query(Sensor).all()],
            "cameras": [c.id for c in db.query(Camera).all()],
            "speakers": [s.id for s in db.query(Speaker).all()],
            "enclosures": [e.id for e in db.query(Enclosure).all()],
            "lamps": [l.id for l in db.query(Lamp).all()],
        }

    # SPEAKER_API 서버 ID 찾기
    spk_server_id = None
    if server_ids:
        spk_servers = db.query(Server).join(ServerCategory).filter(
            ServerCategory.type_server == EnumServerType.SPEAKER_API
        ).all()
        if spk_servers:
            spk_server_id = spk_servers[0].id

    ids = {"controllers": [], "sensors": [], "cameras": [], "speakers": [], "enclosures": [], "lamps": []}

    # ── Controllers (4) — A/B/C/D 구역별 제어기 (E구역 제거 v4.6) ──
    ctrl_configs = [
        ("A구역 제어기", "10.0.1.1", 9010, 0),
        ("B구역 제어기", "10.0.2.1", 9011, 1),
        ("C구역 제어기", "10.0.3.1", 9012, 2),
        ("D구역 제어기", "10.0.4.1", 9013, 3),
    ]
    for i, (name, ip, port, zone) in enumerate(ctrl_configs):
        c = Controller(
            number_device=i + 1, group_device=i + 1, name_device=name,
            type_device=EnumDeviceType.Controller, status=EnumDeviceStatus.ACTIVATED,
            is_enable=True, version="v2.1.0",
            ip_address=ip, ip_port=port,
            geolocation=_geo(zone, 3),  # 감시탑 위치
        )
        db.add(c)
        db.flush()
        ids["controllers"].append(c.id)

    # ── Sensors (402 총합) — 제어기별 타입 분기 (v4.6 명세) ──
    # Ctrl1(A): Fence 100개(1~100) + Multi 21개(180~200) = 121
    # Ctrl2(B): Fence 100개(1~100) + Multi 21개(180~200) = 121
    # Ctrl3(C): SmartCompound 60개(1~60) = 60
    # Ctrl4(D): SmartSensor 100개(1~100) = 100
    sensor_specs = [
        # (ctrl_idx, type, num_range, name_prefix)
        (0, EnumDeviceType.Fence, range(1, 101), "펜스센서-A"),
        (0, EnumDeviceType.Multi, range(180, 201), "복합센서-A"),
        (1, EnumDeviceType.Fence, range(1, 101), "펜스센서-B"),
        (1, EnumDeviceType.Multi, range(180, 201), "복합센서-B"),
        (2, EnumDeviceType.SmartCompound, range(1, 61), "스마트복합-C"),
        (3, EnumDeviceType.SmartSensor, range(1, 101), "스마트센서-D"),
    ]
    for ctrl_idx, sensor_type, num_range, name_prefix in sensor_specs:
        ctrl_id = ids["controllers"][ctrl_idx]
        version_major = 2 if sensor_type == EnumDeviceType.Multi else 1
        for num in num_range:
            s = Sensor(
                number_device=num, group_device=ctrl_idx + 1,
                name_device=f"{name_prefix}{num:03d}",
                type_device=sensor_type,
                status=random.choices(
                    [EnumDeviceStatus.ACTIVATED, EnumDeviceStatus.ERROR, EnumDeviceStatus.DEACTIVATED],
                    weights=[85, 10, 5],
                )[0],
                is_enable=random.choices([True, False], weights=[95, 5])[0],
                version=f"v{version_major}.{random.randint(0, 5)}.{random.randint(0, 9)}",
                controller_id=ctrl_id,
                geolocation=_geo(ctrl_idx, num % 4),
            )
            db.add(s)

    db.flush()
    ids["sensors"] = [s.id for s in db.query(Sensor).all()]

    # ── Cameras (300) — RTSP URL + 하드웨어 스펙 포함 (v4.6: 4구역, PTZ 100대) ──
    cam_modes = [EnumCameraMode.ONVIF, EnumCameraMode.EMSTONE_API, EnumCameraMode.INNODEP_API]
    cam_types = [EnumCameraType.FIXED, EnumCameraType.PTZ]
    hw_specs = [
        {"manufacturer": "Hanwha Vision", "model": "XNO-8080R", "resolution": "3840x2160",
         "sensor": "1/1.8\" 8MP CMOS", "lens": "3.9~9.4mm"},
        {"manufacturer": "Hanwha Vision", "model": "XNP-9300RW", "resolution": "3840x2160",
         "sensor": "1/1.8\" 8MP CMOS", "lens": "4.44~142.6mm (32x)"},
        {"manufacturer": "IDIS", "model": "DC-S6282HRXA", "resolution": "1920x1080",
         "sensor": "1/2.8\" 2MP CMOS", "lens": "4.5~135mm (30x)"},
        {"manufacturer": "EMSTONE", "model": "EV-8240AI", "resolution": "3840x2160",
         "sensor": "1/1.2\" 8MP CMOS", "lens": "3.6~11mm (3x)"},
        {"manufacturer": "INNODEP", "model": "IDB-IR480", "resolution": "640x480",
         "sensor": "Uncooled VOx FPA", "lens": "35mm thermal"},
    ]
    for i in range(300):
        zone_idx = i % 4  # v4.6: A/B/C/D 4구역 매핑 (E구역 제거)
        cam_ip = f"10.1.{zone_idx + 1}.{(i % 254) + 1}"
        cam_type = cam_types[0] if i % 3 != 2 else cam_types[1]  # 매 3번째는 PTZ
        cam_mode = cam_modes[i % len(cam_modes)]
        hw = hw_specs[i % len(hw_specs)]
        cam = Camera(
            number_device=i + 1, group_device=zone_idx + 1,
            name_device=f"카메라-{chr(65 + zone_idx)}{(i // 4) + 1:03d}",
            type_device=EnumDeviceType.IpCamera,
            status=random.choices([EnumDeviceStatus.ACTIVATED, EnumDeviceStatus.ERROR], weights=[90, 10])[0],
            is_enable=True, version=f"v3.{random.randint(0, 3)}.{random.randint(0, 9)}",
            ip_address=cam_ip, ip_port=554,
            user_name="admin", user_password="camera123",
            urls={
                "homepage": {"url": f"http://{cam_ip}/"},
                "onvif": {"device_service": f"http://{cam_ip}:8000/onvif/device_service"},
                "streams": {
                    "rtsp": {
                        "main": f"rtsp://{cam_ip}:554/Streaming/Channels/101",
                        "sub": f"rtsp://{cam_ip}:554/Streaming/Channels/102",
                    },
                },
                "snapshot": {"ch1": f"http://{cam_ip}/cgi-bin/snapshot.cgi"},
            },
            mode=cam_mode, category=cam_type,
            is_record=random.choice([True, False]),
            hardware_spec=hw,
            geolocation=_geo(zone_idx, i % 4),
        )
        db.add(cam)
    db.flush()
    ids["cameras"] = [c.id for c in db.query(Camera).all()]

    # ── Speakers (200) — server_id 연결 + geolocation (v4.6: 4구역) ──
    spk_types = [EnumSpeakerType.NORMAL, EnumSpeakerType.ADMIN, EnumSpeakerType.MONITOR]
    for i in range(200):
        zone_idx = i % 4
        spk = Speaker(
            number_device=i + 1, group_device=zone_idx + 1,
            name_device=f"스피커-{chr(65 + zone_idx)}{(i // 4) + 1:03d}",
            type_device=EnumDeviceType.IpSpeaker,
            status=random.choices([EnumDeviceStatus.ACTIVATED, EnumDeviceStatus.DEACTIVATED], weights=[90, 10])[0],
            is_enable=True, version=f"v1.{random.randint(0, 2)}.0",
            speaker_type=random.choice(spk_types),
            server_id=spk_server_id,
            description=f"스피커 {i + 1} - {chr(65 + zone_idx)}구역 {['초소1', '초소2', '초소3', '감시탑'][i % 4]}",
            geolocation=_geo(zone_idx, i % 4),
        )
        db.add(spk)
    db.flush()
    ids["speakers"] = [s.id for s in db.query(Speaker).all()]

    # ── Enclosures (30) — threshold_config + geolocation (v4.6: 4구역) ──
    for i in range(30):
        zone_idx = i % 4
        enc = Enclosure(
            number_device=i + 1, group_device=zone_idx + 1,
            name_device=f"함체-{chr(65 + zone_idx)}{(i // 4) + 1:02d}",
            type_device=EnumDeviceType.Enclosure,
            status=random.choices(
                [EnumDeviceStatus.ACTIVATED, EnumDeviceStatus.ERROR, EnumDeviceStatus.DEACTIVATED],
                weights=[80, 10, 10],
            )[0],
            is_enable=True, version=f"v1.{random.randint(0, 3)}.0",
            door_status=random.choices([EnumDoorStatus.CLOSED, EnumDoorStatus.OPEN], weights=[85, 15])[0],
            heater_enabled=random.choice([True, False]),
            fan_enabled=random.choice([True, False]),
            geolocation=_geo(zone_idx, i % 4),
            threshold_config={
                "temperature": {"min": -20.0, "max": 55.0, "unit": "°C"},
                "humidity": {"min": 10.0, "max": 90.0, "unit": "%"},
                "voltage": {"min": 11.0, "max": 14.5, "unit": "V"},
                "current": {"min": 0.0, "max": 10.0, "unit": "A"},
                "vibration": {"max": 80, "unit": "level"},
                "ups_battery_level": {"min": 20, "unit": "%"},
            },
        )
        db.add(enc)
    db.flush()
    ids["enclosures"] = [e.id for e in db.query(Enclosure).all()]

    # ── Lamps (30) — user_name/user_password + geolocation (v4.6: 4구역) ──
    for i in range(30):
        zone_idx = i % 4
        lmp = Lamp(
            number_device=i + 1, group_device=zone_idx + 1,
            name_device=f"경광등-{chr(65 + zone_idx)}{(i // 4) + 1:02d}",
            type_device=EnumDeviceType.Lamp,
            status=random.choices([EnumDeviceStatus.ACTIVATED, EnumDeviceStatus.DEACTIVATED], weights=[90, 10])[0],
            is_enable=True, version=f"v1.0.{random.randint(0, 5)}",
            ip_address=f"10.3.{zone_idx + 1}.{i + 1}", ip_port=80,
            user_name="admin",
            user_password="lamp123",
            description=f"경광등 {i + 1} - {chr(65 + zone_idx)}구역 {['초소1', '초소2', '초소3', '감시탑'][i % 4]}",
            geolocation=_geo(zone_idx, i % 4),
        )
        db.add(lmp)
    db.flush()
    ids["lamps"] = [l.id for l in db.query(Lamp).all()]

    db.commit()
    total = sum(len(v) for v in ids.values())
    print(f"  [OK] Devices created: {total} "
          f"(ctrl:{len(ids['controllers'])} sens:{len(ids['sensors'])} "
          f"cam:{len(ids['cameras'])} spk:{len(ids['speakers'])} "
          f"enc:{len(ids['enclosures'])} lamp:{len(ids['lamps'])})")
    return ids


# ── Device Groups ────────────────────────────────────────

def _create_device_groups(db: Session, device_ids: dict):
    """Create 5 device groups with device mappings."""
    existing = db.query(DeviceGroup).count()
    if existing > 0:
        print(f"  [OK] Device groups already exist: {existing}")
        return

    groups_data = [
        {"name": "A구역 전체", "description": "A구역(서쪽) 전체 장비 그룹 — 철원 일대"},
        {"name": "B구역 전체", "description": "B구역(중앙) 전체 장비 그룹 — 화천 일대"},
        {"name": "C구역 전체", "description": "C구역(동쪽) 전체 장비 그룹"},
        {"name": "D구역 전체", "description": "D구역(동북쪽) 전체 장비 그룹 — 양구 일대"},
        {"name": "PTZ 카메라", "description": "PTZ 회전형 카메라 전체"},
        {"name": "긴급 방송장비", "description": "긴급 방송용 스피커 + 경광등 그룹"},
    ]

    group_objs = []
    for gd in groups_data:
        g = DeviceGroup(**gd)
        db.add(g)
        db.flush()
        group_objs.append(g)

    # 구역별 매핑 (A=group_device 1, B=2, C=3, D=4) — v4.6 E구역 제거
    zone_groups = {
        1: group_objs[0].id, 2: group_objs[1].id, 3: group_objs[2].id,
        4: group_objs[3].id,
    }
    category_map = {
        "controllers": EnumDeviceCategory.CONTROLLER,
        "sensors": EnumDeviceCategory.SENSOR,
        "cameras": EnumDeviceCategory.CAMERA,
        "speakers": EnumDeviceCategory.SPEAKER,
        "enclosures": EnumDeviceCategory.ENCLOSURE,
        "lamps": EnumDeviceCategory.LAMP,
    }

    count = 0
    for cat_key, cat_enum in category_map.items():
        dev_ids = device_ids.get(cat_key, [])
        for dev_id in dev_ids:
            # group_device로 구역 판별 (1=A, 2=B, 3=C)
            if cat_key == "controllers":
                dev = db.query(Controller).filter(Controller.id == dev_id).first()
            elif cat_key == "sensors":
                dev = db.query(Sensor).filter(Sensor.id == dev_id).first()
            elif cat_key == "cameras":
                dev = db.query(Camera).filter(Camera.id == dev_id).first()
            elif cat_key == "speakers":
                dev = db.query(Speaker).filter(Speaker.id == dev_id).first()
            elif cat_key == "enclosures":
                dev = db.query(Enclosure).filter(Enclosure.id == dev_id).first()
            else:
                dev = db.query(Lamp).filter(Lamp.id == dev_id).first()

            if dev and dev.group_device in zone_groups:
                mapping = DeviceGroupMapping(
                    device_id=dev_id,
                    category_device=cat_enum,
                    group_id=zone_groups[dev.group_device],
                )
                db.add(mapping)
                count += 1

    # PTZ 카메라 그룹 (category == PTZ) — v4.6 group_objs[4]
    ptz_cameras = db.query(Camera).filter(Camera.category == EnumCameraType.PTZ).all()
    for cam in ptz_cameras:
        mapping = DeviceGroupMapping(
            device_id=cam.id,
            category_device=EnumDeviceCategory.CAMERA,
            group_id=group_objs[4].id,
        )
        db.add(mapping)
        count += 1

    # 긴급 방송장비 그룹 (ADMIN 스피커 + 전체 경광등) — v4.6 group_objs[5]
    admin_speakers = db.query(Speaker).filter(Speaker.speaker_type == EnumSpeakerType.ADMIN).all()
    for spk in admin_speakers:
        mapping = DeviceGroupMapping(
            device_id=spk.id,
            category_device=EnumDeviceCategory.SPEAKER,
            group_id=group_objs[5].id,
        )
        db.add(mapping)
        count += 1

    all_lamps = db.query(Lamp).all()
    for lmp in all_lamps:
        mapping = DeviceGroupMapping(
            device_id=lmp.id,
            category_device=EnumDeviceCategory.LAMP,
            group_id=group_objs[5].id,
        )
        db.add(mapping)
        count += 1

    db.commit()
    print(f"  [OK] Device groups created: {len(groups_data)}, mappings: {count}")


# ── Camera Presets + ROI + XyPoints ──────────────────────

def _create_camera_presets(db: Session):
    """Create camera presets with ROI and XyPoints for PTZ cameras."""
    existing = db.query(CameraPreset).count()
    if existing > 0:
        print(f"  [OK] Camera presets already exist: {existing}")
        return

    ptz_cameras = db.query(Camera).filter(Camera.category == EnumCameraType.PTZ).all()
    if not ptz_cameras:
        print("  [WARN] No PTZ cameras — skipping camera presets")
        return

    preset_templates = [
        {"preset_name": "Home", "touring_time": 0, "is_restricted_zone": False},
        {"preset_name": "좌측 경계", "touring_time": 8, "is_restricted_zone": False},
        {"preset_name": "우측 경계", "touring_time": 10, "is_restricted_zone": False},
        {"preset_name": "정문 감시", "touring_time": 12, "is_restricted_zone": False},
        {"preset_name": "후방 감시", "touring_time": 15, "is_restricted_zone": False},
    ]
    # v4.6 시연용: 첫 번째 PTZ 카메라에만 '감시금지 시연' preset 1건 추가
    restricted_demo_preset = {"preset_name": "감시금지 시연", "touring_time": 0, "is_restricted_zone": True}

    roi_templates = [
        {"name": "침입 감지 영역", "resolution_width": 1920.0, "resolution_height": 1080.0,
         "points": [(0.1, 0.3), (0.9, 0.3), (0.9, 0.9), (0.1, 0.9)]},
        {"name": "배회 감지 영역", "resolution_width": 1920.0, "resolution_height": 1080.0,
         "points": [(0.2, 0.2), (0.8, 0.2), (0.8, 0.8), (0.2, 0.8)]},
        {"name": "철조망 영역", "resolution_width": 3840.0, "resolution_height": 2160.0,
         "points": [(0.0, 0.4), (1.0, 0.4), (1.0, 0.7), (0.0, 0.7)]},
    ]

    preset_count = 0
    roi_count = 0
    point_count = 0

    for cam_idx, cam in enumerate(ptz_cameras):
        for idx, pt in enumerate(preset_templates):
            preset = CameraPreset(
                camera_id=cam.id,
                camera_name=cam.name_device,
                preset_index=idx + 1,
                preset_name=pt["preset_name"],
                touring_time=pt["touring_time"],
                is_restricted_zone=pt["is_restricted_zone"],
            )
            db.add(preset)
            db.flush()
            preset_count += 1

            # Home 프리셋에만 ROI 2~3개 추가
            if idx == 0:
                num_rois = random.randint(2, 3)
                for ri in range(num_rois):
                    rt = roi_templates[ri % len(roi_templates)]
                    roi = ROI(
                        preset_id=preset.id,
                        name=rt["name"],
                        resolution_width=rt["resolution_width"],
                        resolution_height=rt["resolution_height"],
                        is_enable=True,
                    )
                    db.add(roi)
                    db.flush()
                    roi_count += 1

                    for order, (x, y) in enumerate(rt["points"]):
                        pt_obj = XyPoint(
                            roi_id=roi.id,
                            x=x, y=y, order=order,
                        )
                        db.add(pt_obj)
                        point_count += 1

        # v4.6 시연용: 첫 번째 PTZ 카메라에만 '감시금지 시연' preset 1건 추가
        if cam_idx == 0:
            demo_preset = CameraPreset(
                camera_id=cam.id,
                camera_name=cam.name_device,
                preset_index=len(preset_templates) + 1,
                preset_name=restricted_demo_preset["preset_name"],
                touring_time=restricted_demo_preset["touring_time"],
                is_restricted_zone=restricted_demo_preset["is_restricted_zone"],
            )
            db.add(demo_preset)
            db.flush()
            preset_count += 1

    db.commit()
    print(f"  [OK] Camera presets created: {preset_count}, ROIs: {roi_count}, XyPoints: {point_count}")


# ── Enclosure Metrics ────────────────────────────────────

def _create_enclosure_metrics(db: Session):
    """Create time-series enclosure metrics (last 24h, every 30min per enclosure)."""
    existing = db.query(EnclosureMetric).count()
    if existing > 0:
        print(f"  [OK] Enclosure metrics already exist: {existing}")
        return

    enclosures = db.query(Enclosure).limit(10).all()  # First 10 enclosures only (to limit data volume)
    if not enclosures:
        print("  [WARN] No enclosures — skipping enclosure metrics")
        return

    now = datetime.now(settings.tz).replace(tzinfo=None)
    count = 0
    for enc in enclosures:
        base_temp = random.uniform(-5.0, 25.0)  # 계절별 기본 온도
        base_humidity = random.uniform(30.0, 70.0)
        base_voltage = random.uniform(12.0, 13.8)

        # 24시간 * 2 (30분 간격) = 48 레코드
        for slot in range(48):
            ts = now - timedelta(minutes=30 * slot)
            # 시간에 따른 온도 변동 (낮에 높고, 밤에 낮음)
            hour = ts.hour
            temp_offset = 5.0 * (1 - abs(hour - 14) / 14)  # 14시에 최고
            temp = round(base_temp + temp_offset + random.uniform(-2, 2), 1)
            humidity = round(base_humidity + random.uniform(-5, 5), 1)
            voltage = round(base_voltage + random.uniform(-0.5, 0.5), 2)
            current = round(random.uniform(0.5, 3.5), 2)

            metric = EnclosureMetric(
                enclosure_id=enc.id,
                temperature=str(temp),
                humidity=str(humidity),
                voltage=str(voltage),
                current=str(current),
                vibration=random.randint(0, 15),
                ups_battery_level=random.randint(70, 100),
                ups_charging=random.choice([True, False]),
                detail={
                    "door_open_count": random.randint(0, 2),
                    "power_source": random.choice(["AC", "UPS"]),
                },
                created_at=ts,
            )
            db.add(metric)
            count += 1

    db.commit()
    print(f"  [OK] Enclosure metrics created: {count}")


# ── Events ───────────────────────────────────────────────

DETECTION_TYPES = [t for t in EnumDetectionType if t != EnumDetectionType.NONE]
FAULT_TYPES = list(EnumFaultType)

# AI 탐지 상세 정보 템플릿
DETECTION_DETAILS = [
    {"thumbnail": None, "ai_objects": [
        {"class": "person", "confidence": 0.92, "bbox": [120, 80, 340, 520]},
    ], "zone": "침입 감지 영역"},
    {"thumbnail": None, "ai_objects": [
        {"class": "person", "confidence": 0.87, "bbox": [200, 100, 380, 480]},
        {"class": "person", "confidence": 0.73, "bbox": [500, 120, 650, 490]},
    ], "zone": "철조망 영역"},
    {"thumbnail": None, "ai_objects": [
        {"class": "vehicle", "confidence": 0.95, "bbox": [50, 200, 600, 450]},
    ], "zone": "정문 감시"},
    {"thumbnail": None, "ai_objects": [
        {"class": "animal", "confidence": 0.68, "bbox": [300, 350, 420, 450]},
    ], "zone": "배회 감지 영역"},
    {"thumbnail": None, "ai_objects": [
        {"class": "person", "confidence": 0.96, "bbox": [150, 50, 350, 500]},
    ], "zone": "좌측 경계", "alarm_level": "HIGH"},
    None,  # 일부 이벤트는 detail 없음
]


def _create_events(db: Session, device_ids: dict) -> dict:
    """Create bulk events: 3000 detection (3일), 5000 malfunction (5일), 20000 connection.
    Returns {category: [event_ids]}."""
    existing = db.query(Event).count()
    if existing > 0:
        print(f"  [OK] Events already exist: {existing}")
        return {
            "detection": [e.id for e in db.query(DetectionEvent.id).all()],
            "malfunction": [e.id for e in db.query(MalfunctionEvent.id).all()],
            "connection": [e.id for e in db.query(ConnectionEvent.id).all()],
        }

    sensor_ids = device_ids.get("sensors", [])
    camera_ids = device_ids.get("cameras", [])
    all_ids = []
    for v in device_ids.values():
        all_ids.extend(v)

    # device_description 생성을 위한 디바이스 정보 캐시
    # 형식: "[{type_device}] {name_device} (number: {number_device}, id: {id})"
    device_cache: dict[int, str] = {}
    for dev in db.query(Device).all():
        type_val = dev.type_device.value if hasattr(dev.type_device, 'value') else dev.type_device
        device_cache[dev.id] = f"[{type_val}] {dev.name_device} (number: {dev.number_device}, id: {dev.id})"

    def _desc(dev_id: int | None) -> str | None:
        if dev_id is None:
            return None
        return device_cache.get(dev_id, f"[Unknown] device (id: {dev_id})")

    now = datetime.now(settings.tz).replace(tzinfo=None)
    eids = {"detection": [], "malfunction": [], "connection": []}

    # ── Detection events (3000건, 3일간 = 하루 ~1000건) ──
    print("    Creating detection events (3000)...", flush=True)
    for i in range(3000):
        # 3일 범위 내 시간 분산
        dt = now - timedelta(
            days=random.randint(0, 2),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59),
        )
        # 70% 센서 탐지, 30% 카메라 AI 탐지
        if random.random() < 0.7 and sensor_ids:
            dev_id = random.choice(sensor_ids)
            detail = random.choice([None, None, None, DETECTION_DETAILS[-1]])
        elif camera_ids:
            dev_id = random.choice(camera_ids)
            detail = random.choice(DETECTION_DETAILS)
        else:
            dev_id = random.choice(all_ids) if all_ids else None
            detail = None

        e = DetectionEvent(
            type_event="Intrusion",
            device_id=dev_id,
            device_description=_desc(dev_id),
            result=random.choice(DETECTION_TYPES),
            action_reported="False",  # action_reported는 아래에서 일괄 설정
            detail=detail,
            created_at=dt, updated_at=dt,
        )
        db.add(e)

        # 500건마다 flush (메모리 절약)
        if (i + 1) % 500 == 0:
            db.flush()

    db.flush()
    eids["detection"] = [e.id for e in db.query(DetectionEvent.id).all()]

    # ── Malfunction events (5000건, 5일간 = 하루 ~1000건) ──
    print("    Creating malfunction events (5000)...", flush=True)
    for i in range(5000):
        dt = now - timedelta(
            days=random.randint(0, 4),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59),
        )
        dev_id = random.choice(all_ids) if all_ids else None
        fault = random.choice(FAULT_TYPES)
        e = MalfunctionEvent(
            type_event="Fault",
            device_id=dev_id,
            device_description=_desc(dev_id),
            reason=fault,
            action_reported="False",
            detail={
                "fault_code": f"ERR-{random.randint(1000, 9999)}",
                "duration_seconds": random.randint(10, 3600),
                "auto_recovered": random.choice([True, False]),
            } if random.random() < 0.6 else None,
            created_at=dt, updated_at=dt,
        )
        db.add(e)

        if (i + 1) % 500 == 0:
            db.flush()

    db.flush()
    eids["malfunction"] = [e.id for e in db.query(MalfunctionEvent.id).all()]

    # ── Connection events (20000건) ──
    print("    Creating connection events (20000)...", flush=True)
    for i in range(20000):
        dt = now - timedelta(
            days=random.randint(0, 7),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59),
        )
        dev_id = random.choice(all_ids) if all_ids else None
        e = ConnectionEvent(
            type_event="Connection",
            device_id=dev_id,
            device_description=_desc(dev_id),
            created_at=dt, updated_at=dt,
        )
        db.add(e)

        if (i + 1) % 1000 == 0:
            db.flush()

    db.flush()
    eids["connection"] = [e.id for e in db.query(ConnectionEvent.id).all()]

    db.commit()
    total = sum(len(v) for v in eids.values())
    print(f"  [OK] Events created: {total} "
          f"(det:{len(eids['detection'])} mal:{len(eids['malfunction'])} conn:{len(eids['connection'])})")
    return eids


# ── Action Events ────────────────────────────────────────

ACTION_CONTENTS = [
    "현장 확인 완료", "CCTV 확인 후 오경보 처리", "순찰조 출동 조치",
    "장비 재시작 완료", "센서 교체 완료", "케이블 점검 완료",
    "정상 복구 확인", "유지보수 접수", "해당 구역 순찰 완료",
    "AI 분석 결과 동물 판별", "경계 강화 조치", "담당자 보고 완료",
]


def _create_action_events(db: Session, event_ids: dict, user_names: list[str]):
    """Create 5000 action events. Remaining ~3000 detection+malfunction events stay action_reported=False.

    INVARIANT (PRD_ActionEvent_1N_Refactoring v2.0 + v4.8 Phase 12):
        action_reported == "True"  iff  COUNT(ActionEvent WHERE from_event_id = event.id) >= 1
        action_reported == "False" iff  no ActionEvent references this event

        시드에서 ActionEvent 없이 action_reported="True" 박아넣기 금지.
        무작위 True 배정 금지 — 재발 시 1:N 데이터 무결성 위배.
    """
    existing = db.query(ActionEvent).count()
    if existing > 0:
        print(f"  [OK] Action events already exist: {existing}")
        return

    # 탐지 + 장애 이벤트 합치기
    det_ids = list(event_ids.get("detection", []))
    mal_ids = list(event_ids.get("malfunction", []))
    all_event_ids = det_ids + mal_ids  # 3000 + 5000 = 8000
    random.shuffle(all_event_ids)

    # 5000건만 조치 대상 (= ActionEvent 1건 이상 매칭 → action_reported=True)
    # 나머지 ~3000건은 action_reported=False 유지 (초기값)
    targets = all_event_ids[:5000]

    # invariant 유지: ActionEvent 매칭될 5000건만 action_reported="True" 일괄 설정
    print("    Updating action_reported for target events (ActionEvent-backed only)...", flush=True)
    det_id_set = set(det_ids)
    mal_id_set = set(mal_ids)
    det_update = [eid for eid in targets if eid in det_id_set]
    mal_update = [eid for eid in targets if eid in mal_id_set]

    for batch_start in range(0, len(det_update), 1000):
        batch = det_update[batch_start:batch_start + 1000]
        db.query(DetectionEvent).filter(DetectionEvent.id.in_(batch)).update(
            {"action_reported": "True"}, synchronize_session=False
        )
    for batch_start in range(0, len(mal_update), 1000):
        batch = mal_update[batch_start:batch_start + 1000]
        db.query(MalfunctionEvent).filter(MalfunctionEvent.id.in_(batch)).update(
            {"action_reported": "True"}, synchronize_session=False
        )
    db.flush()

    # 5000건 조치 이벤트 생성
    print("    Creating action events (5000)...", flush=True)
    now = datetime.now(settings.tz).replace(tzinfo=None)
    for i, from_id in enumerate(targets):
        dt = now - timedelta(
            days=random.randint(0, 5),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59),
        )
        a = ActionEvent(
            from_event_id=from_id,
            type_event="Action",
            content=random.choice(ACTION_CONTENTS),
            user=random.choice(user_names),
            created_at=dt, updated_at=dt,
        )
        db.add(a)

        if (i + 1) % 500 == 0:
            db.flush()

    db.commit()
    unreported = len(all_event_ids) - len(targets)
    print(f"  [OK] Action events created: {len(targets)} "
          f"(reported: {len(targets)}, unreported: ~{unreported})")


# ── System Events ────────────────────────────────────────

SYS_EVENT_TEMPLATES = [
    (EnumSystemEventType.SERVER_CONNECTED, EnumSystemEventSeverity.INFO, "서버 연결 성공"),
    (EnumSystemEventType.SERVER_DISCONNECTED, EnumSystemEventSeverity.WARNING, "서버 연결 해제"),
    (EnumSystemEventType.SERVER_ERROR, EnumSystemEventSeverity.ERROR, "서버 오류 발생"),
    (EnumSystemEventType.SERVICE_STARTED, EnumSystemEventSeverity.INFO, "서비스 시작"),
    (EnumSystemEventType.SERVICE_STOPPED, EnumSystemEventSeverity.WARNING, "서비스 중지"),
    (EnumSystemEventType.SERVICE_ERROR, EnumSystemEventSeverity.ERROR, "서비스 오류"),
    (EnumSystemEventType.RESOURCE_THRESHOLD, EnumSystemEventSeverity.WARNING, "리소스 임계치 초과"),
    (EnumSystemEventType.BACKUP_STARTED, EnumSystemEventSeverity.INFO, "백업 시작"),
    (EnumSystemEventType.BACKUP_COMPLETED, EnumSystemEventSeverity.INFO, "백업 완료"),
    (EnumSystemEventType.BACKUP_FAILED, EnumSystemEventSeverity.ERROR, "백업 실패"),
    (EnumSystemEventType.CONNECTION_LOST, EnumSystemEventSeverity.ERROR, "연결 끊김"),
    (EnumSystemEventType.CONNECTION_RESTORED, EnumSystemEventSeverity.INFO, "연결 복구"),
    (EnumSystemEventType.SECURITY_ALERT, EnumSystemEventSeverity.CRITICAL, "보안 경고"),
    (EnumSystemEventType.DEVICE_CONNECTED, EnumSystemEventSeverity.INFO, "디바이스 연결됨"),
    (EnumSystemEventType.SYSTEM_UPDATE, EnumSystemEventSeverity.INFO, "시스템 업데이트"),
]


def _create_system_events(db: Session, server_ids: list[int]):
    """Create 30 system events."""
    existing = db.query(SystemEvent).count()
    if existing > 0:
        print(f"  [OK] System events already exist: {existing}")
        return

    for i in range(30):
        typ, sev, title = random.choice(SYS_EVENT_TEMPLATES)
        srv_id = random.choice(server_ids) if server_ids else None
        dt = _rand_dt(30)
        se = SystemEvent(
            server_id=srv_id,
            server_description=f"서버#{srv_id}" if srv_id else None,
            type_event=typ, severity=sev,
            title=title,
            message=f"{title} - 샘플 이벤트 #{i + 1}",
            source="system_monitor",
            is_acknowledged=random.choice([True, False]),
            created_at=dt,
        )
        db.add(se)

    db.commit()
    print(f"  [OK] System events created: 30")


# ── Config Change Logs ───────────────────────────────────

CONFIG_TEMPLATES = [
    (EnumConfigResourceType.CONTROLLER, EnumConfigActionType.CREATED, "제어기 생성"),
    (EnumConfigResourceType.SENSOR, EnumConfigActionType.CREATED, "센서 생성"),
    (EnumConfigResourceType.SENSOR, EnumConfigActionType.UPDATED, "센서 설정 변경"),
    (EnumConfigResourceType.CAMERA, EnumConfigActionType.CREATED, "카메라 등록"),
    (EnumConfigResourceType.CAMERA, EnumConfigActionType.UPDATED, "카메라 설정 변경"),
    (EnumConfigResourceType.SPEAKER, EnumConfigActionType.CREATED, "스피커 등록"),
    (EnumConfigResourceType.SPEAKER, EnumConfigActionType.DELETED, "스피커 삭제"),
    (EnumConfigResourceType.ENCLOSURE, EnumConfigActionType.STATUS_CHANGED, "함체 상태 변경"),
    (EnumConfigResourceType.LAMP, EnumConfigActionType.CREATED, "경광등 등록"),
    (EnumConfigResourceType.EVENT_MAPPING, EnumConfigActionType.CREATED, "이벤트 매핑 설정"),
    (EnumConfigResourceType.EVENT_MAPPING, EnumConfigActionType.UPDATED, "이벤트 매핑 변경"),
]


def _create_config_change_logs(db: Session, user_ids: list[int]):
    """Create 20 config change logs."""
    existing = db.query(ConfigChangeLog).count()
    if existing > 0:
        print(f"  [OK] Config change logs already exist: {existing}")
        return

    user_names = ["김운영", "이운영", "박관제", "최관제", "정유지"]

    for i in range(20):
        res_type, action, desc = random.choice(CONFIG_TEMPLATES)
        idx = random.randint(0, len(user_ids) - 1) if user_ids else 0
        actor_id = user_ids[idx] if user_ids else None
        dt = _rand_dt(30)
        is_update = action in (EnumConfigActionType.UPDATED, EnumConfigActionType.STATUS_CHANGED)
        cl = ConfigChangeLog(
            resource_type=res_type,
            resource_id=random.randint(1, 100),
            resource_name=f"{res_type.value}-{random.randint(1, 50):03d}",
            action=action,
            before_state={"status": "ACTIVATED"} if is_update else None,
            after_state={"status": "DEACTIVATED"} if is_update else None,
            actor_id=actor_id,
            actor_name=user_names[idx] if idx < len(user_names) else "system",
            actor_ip=_rand_ip(),
            description=desc,
            created_at=dt,
        )
        db.add(cl)

    db.commit()
    print(f"  [OK] Config change logs created: 20")


# ── Audit Logs ───────────────────────────────────────────

AUDIT_TEMPLATES = [
    (EnumAuditActionType.USER_CREATED, EnumAuditResourceType.USER, "사용자 생성"),
    (EnumAuditActionType.USER_UPDATED, EnumAuditResourceType.USER, "사용자 정보 수정"),
    (EnumAuditActionType.PASSWORD_CHANGED, EnumAuditResourceType.PASSWORD, "비밀번호 변경"),
    (EnumAuditActionType.ROLE_CHANGED, EnumAuditResourceType.USER, "역할 변경"),
    (EnumAuditActionType.SESSION_CREATED, EnumAuditResourceType.USER_SESSION, "세션 생성"),
    (EnumAuditActionType.SESSION_TERMINATED, EnumAuditResourceType.USER_SESSION, "세션 종료"),
    (EnumAuditActionType.GROUP_CREATED, EnumAuditResourceType.USER_GROUP, "그룹 생성"),
    (EnumAuditActionType.GROUP_ASSIGNED, EnumAuditResourceType.USER, "그룹 할당"),
]


def _create_audit_logs(db: Session, user_ids: list[int]):
    """Create 20 audit logs."""
    existing = db.query(AuditLog).count()
    if existing > 0:
        print(f"  [OK] Audit logs already exist: {existing}")
        return

    login_ids = ["operator1", "operator2", "monitor1", "monitor2", "maintainer1"]
    names = ["김운영", "이운영", "박관제", "최관제", "정유지"]

    for i in range(20):
        action_type, resource_type, desc = random.choice(AUDIT_TEMPLATES)
        idx = random.randint(0, len(user_ids) - 1) if user_ids else 0
        actor_id = user_ids[idx] if user_ids else None
        dt = _rand_dt(30)
        al = AuditLog(
            action_type=action_type.value,
            action_status=EnumAuditStatus.SUCCESS.value,
            resource_type=resource_type.value,
            resource_id=random.randint(1, 10),
            resource_name=f"리소스-{random.randint(1, 10)}",
            actor_id=actor_id,
            actor_login_id=login_ids[idx] if idx < len(login_ids) else "admin",
            actor_name=names[idx] if idx < len(names) else "관리자",
            actor_role="USER",  # v6.0-clone_deploy_bugfix (#2): 레거시 OPERATOR → USER (v5.3 정책)
            description=desc,
            ip_address=_rand_ip(),
            created_at=dt,
        )
        db.add(al)

    db.commit()
    print(f"  [OK] Audit logs created: 20")


# ── User Sessions ────────────────────────────────────────

def _create_user_sessions(db: Session, user_ids: list[int]):
    """Create 2 sessions per user (1 active, 1 expired)."""
    existing = db.query(UserSession).count()
    if existing > 0:
        print(f"  [OK] User sessions already exist: {existing}")
        return

    now = datetime.now(settings.tz).replace(tzinfo=None)
    count = 0
    for uid in user_ids:
        # Active session
        db.add(UserSession(
            user_id=uid,
            token=str(uuid.uuid4()),
            refresh_token=str(uuid.uuid4()),
            ip_address=_rand_ip(),
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            expires_at=now + timedelta(hours=8),
            is_active=True,
            created_at=now - timedelta(hours=random.randint(1, 4)),
        ))
        # Expired session
        expired = now - timedelta(days=random.randint(1, 7))
        db.add(UserSession(
            user_id=uid,
            token=str(uuid.uuid4()),
            refresh_token=str(uuid.uuid4()),
            ip_address=_rand_ip(),
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            expires_at=expired + timedelta(hours=8),
            logged_out_at=expired + timedelta(hours=random.randint(2, 8)),
            is_active=False,
            logout_reason="EXPIRED",
            created_at=expired,
        ))
        count += 2

    db.commit()
    print(f"  [OK] User sessions created: {count}")


# ── Login Logs ───────────────────────────────────────────

def _create_login_logs(db: Session, user_ids: list[int]):
    """Create 6 login logs per user (3 success + 1 failure + 1 logout + 1 refresh)."""
    existing = db.query(UserLoginLog).count()
    if existing > 0:
        print(f"  [OK] Login logs already exist: {existing}")
        return

    users = db.query(AccountUser).filter(AccountUser.id.in_(user_ids)).all()
    user_map = {u.id: u.login_id for u in users}

    count = 0
    for uid in user_ids:
        lid = user_map.get(uid, f"user_{uid}")

        # 3 successful logins
        for _ in range(3):
            dt = _rand_dt(30)
            db.add(UserLoginLog(
                user_id=uid, login_id=lid,
                action=EnumLoginAction.LOGIN.value,
                result=EnumLoginResult.SUCCESS.value,
                ip_address=_rand_ip(), user_agent="Mozilla/5.0",
                created_at=dt,
            ))
            count += 1

        # 1 failed login
        dt = _rand_dt(30)
        db.add(UserLoginLog(
            user_id=uid, login_id=lid,
            action=EnumLoginAction.LOGIN.value,
            result=EnumLoginResult.FAILURE.value,
            failure_reason="INVALID_CREDENTIALS",
            ip_address=_rand_ip(), user_agent="Mozilla/5.0",
            created_at=dt,
        ))
        count += 1

        # 1 logout
        dt = _rand_dt(30)
        db.add(UserLoginLog(
            user_id=uid, login_id=lid,
            action=EnumLoginAction.LOGOUT.value,
            result=EnumLoginResult.SUCCESS.value,
            ip_address=_rand_ip(), user_agent="Mozilla/5.0",
            created_at=dt,
        ))
        count += 1

        # 1 token refresh
        dt = _rand_dt(30)
        db.add(UserLoginLog(
            user_id=uid, login_id=lid,
            action=EnumLoginAction.REFRESH.value,
            result=EnumLoginResult.SUCCESS.value,
            ip_address=_rand_ip(), user_agent="Mozilla/5.0",
            created_at=dt,
        ))
        count += 1

    db.commit()
    print(f"  [OK] Login logs created: {count}")


def _create_proxy_settings(db: Session, server_ids: list[int]):
    """Create sample proxy settings for servers."""
    existing = db.query(ProxySetting).count()
    if existing > 0:
        print(f"  [OK] Proxy settings already exist: {existing}")
        return

    windy_modes = [EnumWindyMode.WIND0, EnumWindyMode.WIND1, EnumWindyMode.WIND2, EnumWindyMode.WIND3]
    count = 0
    for i, sid in enumerate(server_ids[:4]):  # First 4 servers
        setting = ProxySetting(
            server_id=sid,
            operation_mode=EnumOperationMode.NORMAL,
            windy_mode=windy_modes[i % len(windy_modes)],
        )
        db.add(setting)
        count += 1

    db.commit()
    print(f"  [OK] Proxy settings created: {count}")


def _create_camera_settings(db: Session):
    """Create sample camera settings for cameras."""
    existing = db.query(CameraSetting).count()
    if existing > 0:
        print(f"  [OK] Camera settings already exist: {existing}")
        return

    camera_ids = [c.id for c in db.query(Camera.id).limit(6).all()]
    if not camera_ids:
        print("  [WARN] No cameras — skipping camera settings")
        return

    presets = [
        {"weather_mode": EnumWeatherMode.NORMAL, "heater": EnumOnOff.OFF, "fan": EnumOnOff.OFF,
         "headlight": EnumOnOff.OFF, "day_night_mode": EnumDayNightMode.AUTO,
         "focus_mode": EnumFocusMode.AUTO, "iris_mode": EnumIrisMode.AUTO,
         "tracking": EnumTrackingStatus.IDLE},
        {"weather_mode": EnumWeatherMode.FOG, "heater": EnumOnOff.ON, "fan": EnumOnOff.ON,
         "headlight": EnumOnOff.ON, "day_night_mode": EnumDayNightMode.DAY,
         "focus_mode": EnumFocusMode.AUTO, "iris_mode": EnumIrisMode.AUTO,
         "tracking": EnumTrackingStatus.ACTIVE},
        {"weather_mode": EnumWeatherMode.RAIN, "heater": EnumOnOff.ON, "fan": EnumOnOff.OFF,
         "headlight": EnumOnOff.OFF, "day_night_mode": EnumDayNightMode.NIGHT,
         "focus_mode": EnumFocusMode.MANUAL, "iris_mode": EnumIrisMode.AUTO,
         "tracking": EnumTrackingStatus.LOST,
         "camera_mode": EnumCameraVideoMode.NIGHT_ENHANCE},
        {"weather_mode": EnumWeatherMode.NORMAL, "heater": EnumOnOff.OFF, "fan": EnumOnOff.OFF,
         "headlight": EnumOnOff.OFF, "day_night_mode": EnumDayNightMode.AUTO,
         "focus_mode": EnumFocusMode.AUTO, "iris_mode": EnumIrisMode.AUTO,
         "palette": EnumPalette.WHITE_HOT},
        {"weather_mode": EnumWeatherMode.SNOW, "heater": EnumOnOff.ON, "fan": EnumOnOff.ON,
         "headlight": EnumOnOff.ON, "day_night_mode": EnumDayNightMode.AUTO,
         "focus_mode": EnumFocusMode.AUTO, "iris_mode": EnumIrisMode.MANUAL,
         "palette": EnumPalette.IRONBOW},
        {"weather_mode": EnumWeatherMode.NORMAL, "heater": EnumOnOff.OFF, "fan": EnumOnOff.OFF,
         "headlight": EnumOnOff.OFF, "day_night_mode": EnumDayNightMode.AUTO,
         "focus_mode": EnumFocusMode.MANUAL, "iris_mode": EnumIrisMode.MANUAL,
         "tracking": EnumTrackingStatus.ACTIVE,
         "camera_mode": EnumCameraVideoMode.STABILIZATION},
    ]

    count = 0
    for i, cid in enumerate(camera_ids):
        preset = presets[i % len(presets)]
        setting = CameraSetting(camera_id=cid, **preset)
        db.add(setting)
        count += 1

    db.commit()
    print(f"  [OK] Camera settings created: {count}")


# ── Main Entry Point ─────────────────────────────────────

def initialize_sample_data(db: Session):
    """
    Initialize comprehensive sample data for development/demo.

    Insertion order respects all FK constraints.
    Each step is idempotent — skips if data already exists.
    """
    print("Initializing sample data...")

    # 1. Users
    group_map = _create_user_groups(db)
    user_ids = _create_users(db, group_map)
    user_names = [u["name"] for u in SAMPLE_USERS]

    # 2. Servers (categories already exist from init_server_data)
    server_ids = _create_servers(db)

    # 3. Devices (with geolocation, urls, hardware_spec, threshold_config)
    device_ids = _create_devices(db, server_ids)

    # 4. Device groups + mappings (N:N)
    _create_device_groups(db, device_ids)

    # 5. Camera presets + ROI + XyPoints (PTZ cameras)
    _create_camera_presets(db)

    # 6. Enclosure metrics (time-series)
    _create_enclosure_metrics(db)

    # 7. Events (with detail JSONB)
    event_ids = _create_events(db, device_ids)

    # 8. Action events
    _create_action_events(db, event_ids, user_names)

    # 9. System events
    _create_system_events(db, server_ids)

    # 10. Config change logs
    _create_config_change_logs(db, user_ids)

    # 11. Audit logs
    _create_audit_logs(db, user_ids)

    # 12. User sessions
    _create_user_sessions(db, user_ids)

    # 13. Login logs
    _create_login_logs(db, user_ids)

    # 14. Device settings (proxy + camera)
    _create_proxy_settings(db, server_ids)
    _create_camera_settings(db)

    print("[OK] Sample data initialization complete")


# ============================================================
# Async variants (v6.0 Phase 2 — dual-stack)
# ============================================================
# 원칙:
#   - 기존 sync 함수는 완전 유지 (테스트/caller 호환)
#   - 신규 `_async` 접미사 함수 병설
#   - 벌크 삽입은 `insert(Model), [dict, ...]` executemany + 500건 chunk
#   - `db.query(X).filter(...).first()` → `(await db.execute(select(X).where(...))).scalars().first()`
#   - `db.commit()` → `await db.commit()`, `db.flush()` → `await db.flush()`
#   - INIT_SAMPLE_DATA=false 경로는 caller(init_db_async)에서 스킵 — 이 모듈은 진입 시 항상 seed 시도
# ============================================================

_BULK_CHUNK = 500


async def _bulk_insert_async(db: AsyncSession, model, rows: list[dict], chunk: int = _BULK_CHUNK) -> int:
    """Chunked executemany bulk insert. Returns inserted count."""
    total = 0
    if not rows:
        return 0
    stmt = insert(model)
    for i in range(0, len(rows), chunk):
        batch = rows[i:i + chunk]
        await db.execute(stmt, batch)
        total += len(batch)
    return total


# ── User Groups (async) ──────────────────────────────────

async def _create_user_groups_async(db: AsyncSession) -> dict:
    """Create 3 user groups. Returns {name: id} mapping."""
    existing_count = (await db.execute(select(func.count()).select_from(UserGroup))).scalar() or 0
    if existing_count > 0:
        rows = (await db.execute(select(UserGroup))).scalars().all()
        print(f"  [OK] User groups already exist: {len(rows)}")
        return {g.name: g.id for g in rows}

    _RW = {"view": True, "edit": True, "delete": False, "control": False}
    _R = {"view": True, "edit": False, "delete": False, "control": False}
    _CTRL = {"view": True, "edit": True, "delete": False, "control": True}
    data = [
        {"name": "운영팀", "description": "시스템 운영 담당",
         "permissions": {"modules": {"devices": _RW, "events": _RW, "reports": _RW, "cameras": _CTRL}}, "is_active": True},
        {"name": "관제팀", "description": "관제 모니터링 담당",
         "permissions": {"modules": {"devices": _R, "events": _R, "reports": _R, "cameras": _R}}, "is_active": True},
        {"name": "유지보수팀", "description": "장비 유지보수 담당",
         "permissions": {"modules": {"devices": _RW, "events": _R, "reports": _R}}, "is_active": True},
    ]
    result = {}
    for d in data:
        g = UserGroup(**d)
        db.add(g)
        await db.flush()
        result[g.name] = g.id
    await db.commit()
    print(f"  [OK] User groups created: {len(data)}")
    return result


# ── Users (async) ────────────────────────────────────────

async def _create_users_async(db: AsyncSession, group_map: dict) -> list[int]:
    """Create 5 sample users (excluding admin). Returns list of user IDs."""
    existing = (await db.execute(
        select(func.count()).select_from(AccountUser).where(AccountUser.login_id != "admin")
    )).scalar() or 0
    if existing >= 5:
        rows = (await db.execute(
            select(AccountUser).where(AccountUser.login_id != "admin")
        )).scalars().all()
        print(f"  [OK] Sample users already exist: {existing}")
        return [u.id for u in rows]

    pw = hash_password("user123")
    ids = []
    for ud in SAMPLE_USERS:
        group_key = ud.pop("group_key")
        u = AccountUser(
            password_hash=pw,
            is_active=True,
            is_locked=False,
            group_id=group_map.get(group_key),
            **ud,
        )
        ud["group_key"] = group_key
        db.add(u)
        await db.flush()
        ids.append(u.id)
    await db.commit()
    print(f"  [OK] Sample users created: {len(ids)}")
    return ids


# ── Servers (async) ──────────────────────────────────────

async def _create_servers_async(db: AsyncSession) -> list[int]:
    """Create sample servers. Returns list of server IDs."""
    existing = (await db.execute(select(func.count()).select_from(Server))).scalar() or 0
    if existing > 0:
        print(f"  [OK] Servers already exist: {existing}")
        rows = (await db.execute(select(Server.id))).scalars().all()
        return list(rows)

    categories = (await db.execute(select(ServerCategory))).scalars().all()
    if not categories:
        print("  [WARN] No server categories — skipping servers")
        return []
    cat_map = {c.type_server: c.id for c in categories}

    servers = [
        {"category_id": cat_map.get(EnumServerType.VMS), "name": "VMS-01",
         "status": EnumServerStatus.NORMAL, "ip_address": "192.168.1.10", "port": 8080, "hostname": "vms-01"},
        {"category_id": cat_map.get(EnumServerType.VMS), "name": "VMS-02",
         "status": EnumServerStatus.NORMAL, "ip_address": "192.168.1.11", "port": 8080, "hostname": "vms-02"},
        {"category_id": cat_map.get(EnumServerType.AI_ANALYSIS), "name": "AI-01",
         "status": EnumServerStatus.NORMAL, "ip_address": "192.168.1.20", "port": 8081, "hostname": "ai-01"},
        {"category_id": cat_map.get(EnumServerType.AI_ANALYSIS), "name": "AI-02",
         "status": EnumServerStatus.WARNING, "ip_address": "192.168.1.21", "port": 8081, "hostname": "ai-02"},
        {"category_id": cat_map.get(EnumServerType.STREAMING), "name": "STREAM-01",
         "status": EnumServerStatus.NORMAL, "ip_address": "192.168.1.30", "port": 1935, "hostname": "stream-01"},
        {"category_id": cat_map.get(EnumServerType.STREAMING), "name": "STREAM-02",
         "status": EnumServerStatus.NORMAL, "ip_address": "192.168.1.31", "port": 1935, "hostname": "stream-02"},
        {"category_id": cat_map.get(EnumServerType.BROKER), "name": "BROKER-01",
         "status": EnumServerStatus.ERROR, "ip_address": "192.168.1.50", "port": 5672, "hostname": "broker-01"},
        {"category_id": cat_map.get(EnumServerType.BROKER), "name": "BROKER-02",
         "status": EnumServerStatus.NORMAL, "ip_address": "192.168.1.51", "port": 5672, "hostname": "broker-02"},
        {"category_id": cat_map.get(EnumServerType.DB_API), "name": "DBAPI-01",
         "status": EnumServerStatus.NORMAL, "ip_address": "192.168.1.60", "port": 5000, "hostname": "dbapi-01"},
        {"category_id": cat_map.get(EnumServerType.NVR_API), "name": "NVR-01",
         "status": EnumServerStatus.NORMAL, "ip_address": "192.168.1.70", "port": 8082, "hostname": "nvr-01"},
        {"category_id": cat_map.get(EnumServerType.SPEAKER_API), "name": "SPKAPI-01",
         "status": EnumServerStatus.NORMAL, "ip_address": "192.168.1.80", "port": 5001, "hostname": "spkapi-01"},
        {"category_id": cat_map.get(EnumServerType.ENCLOSURE_API), "name": "ENCAPI-01",
         "status": EnumServerStatus.NORMAL, "ip_address": "192.168.1.90", "port": 5002, "hostname": "encapi-01"},
    ]

    ids = []
    for sd in servers:
        if sd["category_id"] is not None:
            s = Server(**sd)
            db.add(s)
            await db.flush()
            ids.append(s.id)
    await db.commit()
    print(f"  [OK] Servers created: {len(ids)}")
    return ids


# ── Devices (async) ──────────────────────────────────────

async def _create_devices_async(db: AsyncSession, server_ids: list[int]) -> dict:
    """Create all devices with realistic GOP data. Returns {category: [ids]} mapping."""
    existing = (await db.execute(select(func.count()).select_from(Device))).scalar() or 0
    if existing > 0:
        print(f"  [OK] Devices already exist: {existing}")
        return {
            "controllers": list((await db.execute(select(Controller.id))).scalars().all()),
            "sensors": list((await db.execute(select(Sensor.id))).scalars().all()),
            "cameras": list((await db.execute(select(Camera.id))).scalars().all()),
            "speakers": list((await db.execute(select(Speaker.id))).scalars().all()),
            "enclosures": list((await db.execute(select(Enclosure.id))).scalars().all()),
            "lamps": list((await db.execute(select(Lamp.id))).scalars().all()),
        }

    spk_server_id = None
    if server_ids:
        spk_servers = (await db.execute(
            select(Server).join(ServerCategory).where(
                ServerCategory.type_server == EnumServerType.SPEAKER_API
            )
        )).scalars().all()
        if spk_servers:
            spk_server_id = spk_servers[0].id

    ids = {"controllers": [], "sensors": [], "cameras": [], "speakers": [], "enclosures": [], "lamps": []}

    # Controllers (4)
    ctrl_configs = [
        ("A구역 제어기", "10.0.1.1", 9010, 0),
        ("B구역 제어기", "10.0.2.1", 9011, 1),
        ("C구역 제어기", "10.0.3.1", 9012, 2),
        ("D구역 제어기", "10.0.4.1", 9013, 3),
    ]
    for i, (name, ip, port, zone) in enumerate(ctrl_configs):
        c = Controller(
            number_device=i + 1, group_device=i + 1, name_device=name,
            type_device=EnumDeviceType.Controller, status=EnumDeviceStatus.ACTIVATED,
            is_enable=True, version="v2.1.0",
            ip_address=ip, ip_port=port,
            geolocation=_geo(zone, 3),
        )
        db.add(c)
        await db.flush()
        ids["controllers"].append(c.id)

    # Sensors (402)
    sensor_specs = [
        (0, EnumDeviceType.Fence, range(1, 101), "펜스센서-A"),
        (0, EnumDeviceType.Multi, range(180, 201), "복합센서-A"),
        (1, EnumDeviceType.Fence, range(1, 101), "펜스센서-B"),
        (1, EnumDeviceType.Multi, range(180, 201), "복합센서-B"),
        (2, EnumDeviceType.SmartCompound, range(1, 61), "스마트복합-C"),
        (3, EnumDeviceType.SmartSensor, range(1, 101), "스마트센서-D"),
    ]
    for ctrl_idx, sensor_type, num_range, name_prefix in sensor_specs:
        ctrl_id = ids["controllers"][ctrl_idx]
        version_major = 2 if sensor_type == EnumDeviceType.Multi else 1
        for num in num_range:
            s = Sensor(
                number_device=num, group_device=ctrl_idx + 1,
                name_device=f"{name_prefix}{num:03d}",
                type_device=sensor_type,
                status=random.choices(
                    [EnumDeviceStatus.ACTIVATED, EnumDeviceStatus.ERROR, EnumDeviceStatus.DEACTIVATED],
                    weights=[85, 10, 5],
                )[0],
                is_enable=random.choices([True, False], weights=[95, 5])[0],
                version=f"v{version_major}.{random.randint(0, 5)}.{random.randint(0, 9)}",
                controller_id=ctrl_id,
                geolocation=_geo(ctrl_idx, num % 4),
            )
            db.add(s)
    await db.flush()
    ids["sensors"] = list((await db.execute(select(Sensor.id))).scalars().all())

    # Cameras (300)
    cam_modes = [EnumCameraMode.ONVIF, EnumCameraMode.EMSTONE_API, EnumCameraMode.INNODEP_API]
    cam_types = [EnumCameraType.FIXED, EnumCameraType.PTZ]
    hw_specs = [
        {"manufacturer": "Hanwha Vision", "model": "XNO-8080R", "resolution": "3840x2160",
         "sensor": "1/1.8\" 8MP CMOS", "lens": "3.9~9.4mm"},
        {"manufacturer": "Hanwha Vision", "model": "XNP-9300RW", "resolution": "3840x2160",
         "sensor": "1/1.8\" 8MP CMOS", "lens": "4.44~142.6mm (32x)"},
        {"manufacturer": "IDIS", "model": "DC-S6282HRXA", "resolution": "1920x1080",
         "sensor": "1/2.8\" 2MP CMOS", "lens": "4.5~135mm (30x)"},
        {"manufacturer": "EMSTONE", "model": "EV-8240AI", "resolution": "3840x2160",
         "sensor": "1/1.2\" 8MP CMOS", "lens": "3.6~11mm (3x)"},
        {"manufacturer": "INNODEP", "model": "IDB-IR480", "resolution": "640x480",
         "sensor": "Uncooled VOx FPA", "lens": "35mm thermal"},
    ]
    for i in range(300):
        zone_idx = i % 4
        cam_ip = f"10.1.{zone_idx + 1}.{(i % 254) + 1}"
        cam_type = cam_types[0] if i % 3 != 2 else cam_types[1]
        cam_mode = cam_modes[i % len(cam_modes)]
        hw = hw_specs[i % len(hw_specs)]
        cam = Camera(
            number_device=i + 1, group_device=zone_idx + 1,
            name_device=f"카메라-{chr(65 + zone_idx)}{(i // 4) + 1:03d}",
            type_device=EnumDeviceType.IpCamera,
            status=random.choices([EnumDeviceStatus.ACTIVATED, EnumDeviceStatus.ERROR], weights=[90, 10])[0],
            is_enable=True, version=f"v3.{random.randint(0, 3)}.{random.randint(0, 9)}",
            ip_address=cam_ip, ip_port=554,
            user_name="admin", user_password="camera123",
            urls={
                "homepage": {"url": f"http://{cam_ip}/"},
                "onvif": {"device_service": f"http://{cam_ip}:8000/onvif/device_service"},
                "streams": {
                    "rtsp": {
                        "main": f"rtsp://{cam_ip}:554/Streaming/Channels/101",
                        "sub": f"rtsp://{cam_ip}:554/Streaming/Channels/102",
                    },
                },
                "snapshot": {"ch1": f"http://{cam_ip}/cgi-bin/snapshot.cgi"},
            },
            mode=cam_mode, category=cam_type,
            is_record=random.choice([True, False]),
            hardware_spec=hw,
            geolocation=_geo(zone_idx, i % 4),
        )
        db.add(cam)
    await db.flush()
    ids["cameras"] = list((await db.execute(select(Camera.id))).scalars().all())

    # Speakers (200)
    spk_types = [EnumSpeakerType.NORMAL, EnumSpeakerType.ADMIN, EnumSpeakerType.MONITOR]
    for i in range(200):
        zone_idx = i % 4
        spk = Speaker(
            number_device=i + 1, group_device=zone_idx + 1,
            name_device=f"스피커-{chr(65 + zone_idx)}{(i // 4) + 1:03d}",
            type_device=EnumDeviceType.IpSpeaker,
            status=random.choices([EnumDeviceStatus.ACTIVATED, EnumDeviceStatus.DEACTIVATED], weights=[90, 10])[0],
            is_enable=True, version=f"v1.{random.randint(0, 2)}.0",
            speaker_type=random.choice(spk_types),
            server_id=spk_server_id,
            description=f"스피커 {i + 1} - {chr(65 + zone_idx)}구역 {['초소1', '초소2', '초소3', '감시탑'][i % 4]}",
            geolocation=_geo(zone_idx, i % 4),
        )
        db.add(spk)
    await db.flush()
    ids["speakers"] = list((await db.execute(select(Speaker.id))).scalars().all())

    # Enclosures (30)
    for i in range(30):
        zone_idx = i % 4
        enc = Enclosure(
            number_device=i + 1, group_device=zone_idx + 1,
            name_device=f"함체-{chr(65 + zone_idx)}{(i // 4) + 1:02d}",
            type_device=EnumDeviceType.Enclosure,
            status=random.choices(
                [EnumDeviceStatus.ACTIVATED, EnumDeviceStatus.ERROR, EnumDeviceStatus.DEACTIVATED],
                weights=[80, 10, 10],
            )[0],
            is_enable=True, version=f"v1.{random.randint(0, 3)}.0",
            door_status=random.choices([EnumDoorStatus.CLOSED, EnumDoorStatus.OPEN], weights=[85, 15])[0],
            heater_enabled=random.choice([True, False]),
            fan_enabled=random.choice([True, False]),
            geolocation=_geo(zone_idx, i % 4),
            threshold_config={
                "temperature": {"min": -20.0, "max": 55.0, "unit": "°C"},
                "humidity": {"min": 10.0, "max": 90.0, "unit": "%"},
                "voltage": {"min": 11.0, "max": 14.5, "unit": "V"},
                "current": {"min": 0.0, "max": 10.0, "unit": "A"},
                "vibration": {"max": 80, "unit": "level"},
                "ups_battery_level": {"min": 20, "unit": "%"},
            },
        )
        db.add(enc)
    await db.flush()
    ids["enclosures"] = list((await db.execute(select(Enclosure.id))).scalars().all())

    # Lamps (30)
    for i in range(30):
        zone_idx = i % 4
        lmp = Lamp(
            number_device=i + 1, group_device=zone_idx + 1,
            name_device=f"경광등-{chr(65 + zone_idx)}{(i // 4) + 1:02d}",
            type_device=EnumDeviceType.Lamp,
            status=random.choices([EnumDeviceStatus.ACTIVATED, EnumDeviceStatus.DEACTIVATED], weights=[90, 10])[0],
            is_enable=True, version=f"v1.0.{random.randint(0, 5)}",
            ip_address=f"10.3.{zone_idx + 1}.{i + 1}", ip_port=80,
            user_name="admin",
            user_password="lamp123",
            description=f"경광등 {i + 1} - {chr(65 + zone_idx)}구역 {['초소1', '초소2', '초소3', '감시탑'][i % 4]}",
            geolocation=_geo(zone_idx, i % 4),
        )
        db.add(lmp)
    await db.flush()
    ids["lamps"] = list((await db.execute(select(Lamp.id))).scalars().all())

    await db.commit()
    total = sum(len(v) for v in ids.values())
    print(f"  [OK] Devices created: {total} "
          f"(ctrl:{len(ids['controllers'])} sens:{len(ids['sensors'])} "
          f"cam:{len(ids['cameras'])} spk:{len(ids['speakers'])} "
          f"enc:{len(ids['enclosures'])} lamp:{len(ids['lamps'])})")
    return ids


# ── Device Groups (async) ────────────────────────────────

async def _create_device_groups_async(db: AsyncSession, device_ids: dict) -> None:
    """Create 5 device groups with device mappings."""
    existing = (await db.execute(select(func.count()).select_from(DeviceGroup))).scalar() or 0
    if existing > 0:
        print(f"  [OK] Device groups already exist: {existing}")
        return

    groups_data = [
        {"name": "A구역 전체", "description": "A구역(서쪽) 전체 장비 그룹 — 철원 일대"},
        {"name": "B구역 전체", "description": "B구역(중앙) 전체 장비 그룹 — 화천 일대"},
        {"name": "C구역 전체", "description": "C구역(동쪽) 전체 장비 그룹"},
        {"name": "D구역 전체", "description": "D구역(동북쪽) 전체 장비 그룹 — 양구 일대"},
        {"name": "PTZ 카메라", "description": "PTZ 회전형 카메라 전체"},
        {"name": "긴급 방송장비", "description": "긴급 방송용 스피커 + 경광등 그룹"},
    ]

    group_objs = []
    for gd in groups_data:
        g = DeviceGroup(**gd)
        db.add(g)
        await db.flush()
        group_objs.append(g)

    zone_groups = {
        1: group_objs[0].id, 2: group_objs[1].id, 3: group_objs[2].id,
        4: group_objs[3].id,
    }
    category_map = {
        "controllers": EnumDeviceCategory.CONTROLLER,
        "sensors": EnumDeviceCategory.SENSOR,
        "cameras": EnumDeviceCategory.CAMERA,
        "speakers": EnumDeviceCategory.SPEAKER,
        "enclosures": EnumDeviceCategory.ENCLOSURE,
        "lamps": EnumDeviceCategory.LAMP,
    }

    # 디바이스 group_device 캐시 (per-category)
    caches: dict[str, dict[int, int]] = {}
    for cat_key, model in [
        ("controllers", Controller),
        ("sensors", Sensor),
        ("cameras", Camera),
        ("speakers", Speaker),
        ("enclosures", Enclosure),
        ("lamps", Lamp),
    ]:
        rows = (await db.execute(select(model.id, model.group_device))).all()
        caches[cat_key] = {r[0]: r[1] for r in rows}

    count = 0
    for cat_key, cat_enum in category_map.items():
        dev_ids = device_ids.get(cat_key, [])
        cache = caches[cat_key]
        for dev_id in dev_ids:
            gd_val = cache.get(dev_id)
            if gd_val is not None and gd_val in zone_groups:
                mapping = DeviceGroupMapping(
                    device_id=dev_id,
                    category_device=cat_enum,
                    group_id=zone_groups[gd_val],
                )
                db.add(mapping)
                count += 1

    # PTZ 카메라 그룹
    ptz_cameras = (await db.execute(
        select(Camera).where(Camera.category == EnumCameraType.PTZ)
    )).scalars().all()
    for cam in ptz_cameras:
        db.add(DeviceGroupMapping(
            device_id=cam.id,
            category_device=EnumDeviceCategory.CAMERA,
            group_id=group_objs[4].id,
        ))
        count += 1

    # 긴급 방송장비 그룹
    admin_speakers = (await db.execute(
        select(Speaker).where(Speaker.speaker_type == EnumSpeakerType.ADMIN)
    )).scalars().all()
    for spk in admin_speakers:
        db.add(DeviceGroupMapping(
            device_id=spk.id,
            category_device=EnumDeviceCategory.SPEAKER,
            group_id=group_objs[5].id,
        ))
        count += 1

    all_lamps = (await db.execute(select(Lamp))).scalars().all()
    for lmp in all_lamps:
        db.add(DeviceGroupMapping(
            device_id=lmp.id,
            category_device=EnumDeviceCategory.LAMP,
            group_id=group_objs[5].id,
        ))
        count += 1

    await db.commit()
    print(f"  [OK] Device groups created: {len(groups_data)}, mappings: {count}")


# ── Camera Presets + ROI + XyPoints (async) ──────────────

async def _create_camera_presets_async(db: AsyncSession) -> None:
    """Create camera presets with ROI and XyPoints for PTZ cameras."""
    existing = (await db.execute(select(func.count()).select_from(CameraPreset))).scalar() or 0
    if existing > 0:
        print(f"  [OK] Camera presets already exist: {existing}")
        return

    ptz_cameras = (await db.execute(
        select(Camera).where(Camera.category == EnumCameraType.PTZ)
    )).scalars().all()
    if not ptz_cameras:
        print("  [WARN] No PTZ cameras — skipping camera presets")
        return

    preset_templates = [
        {"preset_name": "Home", "touring_time": 0, "is_restricted_zone": False},
        {"preset_name": "좌측 경계", "touring_time": 8, "is_restricted_zone": False},
        {"preset_name": "우측 경계", "touring_time": 10, "is_restricted_zone": False},
        {"preset_name": "정문 감시", "touring_time": 12, "is_restricted_zone": False},
        {"preset_name": "후방 감시", "touring_time": 15, "is_restricted_zone": False},
    ]
    restricted_demo_preset = {"preset_name": "감시금지 시연", "touring_time": 0, "is_restricted_zone": True}

    roi_templates = [
        {"name": "침입 감지 영역", "resolution_width": 1920.0, "resolution_height": 1080.0,
         "points": [(0.1, 0.3), (0.9, 0.3), (0.9, 0.9), (0.1, 0.9)]},
        {"name": "배회 감지 영역", "resolution_width": 1920.0, "resolution_height": 1080.0,
         "points": [(0.2, 0.2), (0.8, 0.2), (0.8, 0.8), (0.2, 0.8)]},
        {"name": "철조망 영역", "resolution_width": 3840.0, "resolution_height": 2160.0,
         "points": [(0.0, 0.4), (1.0, 0.4), (1.0, 0.7), (0.0, 0.7)]},
    ]

    preset_count = 0
    roi_count = 0
    point_count = 0

    for cam_idx, cam in enumerate(ptz_cameras):
        for idx, pt in enumerate(preset_templates):
            preset = CameraPreset(
                camera_id=cam.id,
                camera_name=cam.name_device,
                preset_index=idx + 1,
                preset_name=pt["preset_name"],
                touring_time=pt["touring_time"],
                is_restricted_zone=pt["is_restricted_zone"],
            )
            db.add(preset)
            await db.flush()
            preset_count += 1

            if idx == 0:
                num_rois = random.randint(2, 3)
                for ri in range(num_rois):
                    rt = roi_templates[ri % len(roi_templates)]
                    roi = ROI(
                        preset_id=preset.id,
                        name=rt["name"],
                        resolution_width=rt["resolution_width"],
                        resolution_height=rt["resolution_height"],
                        is_enable=True,
                    )
                    db.add(roi)
                    await db.flush()
                    roi_count += 1

                    for order, (x, y) in enumerate(rt["points"]):
                        db.add(XyPoint(roi_id=roi.id, x=x, y=y, order=order))
                        point_count += 1

        if cam_idx == 0:
            demo_preset = CameraPreset(
                camera_id=cam.id,
                camera_name=cam.name_device,
                preset_index=len(preset_templates) + 1,
                preset_name=restricted_demo_preset["preset_name"],
                touring_time=restricted_demo_preset["touring_time"],
                is_restricted_zone=restricted_demo_preset["is_restricted_zone"],
            )
            db.add(demo_preset)
            await db.flush()
            preset_count += 1

    await db.commit()
    print(f"  [OK] Camera presets created: {preset_count}, ROIs: {roi_count}, XyPoints: {point_count}")


# ── Enclosure Metrics (async, bulk) ──────────────────────

async def _create_enclosure_metrics_async(db: AsyncSession) -> None:
    """Create time-series enclosure metrics (last 24h, 30min intervals) via bulk insert."""
    existing = (await db.execute(select(func.count()).select_from(EnclosureMetric))).scalar() or 0
    if existing > 0:
        print(f"  [OK] Enclosure metrics already exist: {existing}")
        return

    enclosures = (await db.execute(select(Enclosure).limit(10))).scalars().all()
    if not enclosures:
        print("  [WARN] No enclosures — skipping enclosure metrics")
        return

    now = datetime.now(settings.tz).replace(tzinfo=None)
    rows: list[dict] = []
    for enc in enclosures:
        base_temp = random.uniform(-5.0, 25.0)
        base_humidity = random.uniform(30.0, 70.0)
        base_voltage = random.uniform(12.0, 13.8)

        for slot in range(48):
            ts = now - timedelta(minutes=30 * slot)
            hour = ts.hour
            temp_offset = 5.0 * (1 - abs(hour - 14) / 14)
            temp = round(base_temp + temp_offset + random.uniform(-2, 2), 1)
            humidity = round(base_humidity + random.uniform(-5, 5), 1)
            voltage = round(base_voltage + random.uniform(-0.5, 0.5), 2)
            current = round(random.uniform(0.5, 3.5), 2)

            rows.append({
                "enclosure_id": enc.id,
                "temperature": str(temp),
                "humidity": str(humidity),
                "voltage": str(voltage),
                "current": str(current),
                "vibration": random.randint(0, 15),
                "ups_battery_level": random.randint(70, 100),
                "ups_charging": random.choice([True, False]),
                "detail": {
                    "door_open_count": random.randint(0, 2),
                    "power_source": random.choice(["AC", "UPS"]),
                },
                "created_at": ts,
            })

    count = await _bulk_insert_async(db, EnclosureMetric, rows)
    await db.commit()
    print(f"  [OK] Enclosure metrics created: {count}")


# ── Events (async, bulk) ─────────────────────────────────

async def _create_events_async(db: AsyncSession, device_ids: dict) -> dict:
    """Create 28k+ events via chunked bulk insert (500 rows/batch executemany)."""
    existing = (await db.execute(select(func.count()).select_from(Event))).scalar() or 0
    if existing > 0:
        print(f"  [OK] Events already exist: {existing}")
        return {
            "detection": list((await db.execute(select(DetectionEvent.id))).scalars().all()),
            "malfunction": list((await db.execute(select(MalfunctionEvent.id))).scalars().all()),
            "connection": list((await db.execute(select(ConnectionEvent.id))).scalars().all()),
        }

    sensor_ids = device_ids.get("sensors", [])
    camera_ids = device_ids.get("cameras", [])
    all_ids: list[int] = []
    for v in device_ids.values():
        all_ids.extend(v)

    # device_description 캐시
    device_cache: dict[int, str] = {}
    devs = (await db.execute(select(Device))).scalars().all()
    for dev in devs:
        type_val = dev.type_device.value if hasattr(dev.type_device, 'value') else dev.type_device
        device_cache[dev.id] = f"[{type_val}] {dev.name_device} (number: {dev.number_device}, id: {dev.id})"

    def _desc(dev_id: int | None) -> str | None:
        if dev_id is None:
            return None
        return device_cache.get(dev_id, f"[Unknown] device (id: {dev_id})")

    now = datetime.now(settings.tz).replace(tzinfo=None)
    eids = {"detection": [], "malfunction": [], "connection": []}

    # Detection events (3000, 3일)
    print("    Creating detection events (3000)...", flush=True)
    det_rows: list[dict] = []
    for i in range(3000):
        dt = now - timedelta(
            days=random.randint(0, 2),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59),
        )
        if random.random() < 0.7 and sensor_ids:
            dev_id = random.choice(sensor_ids)
            detail = random.choice([None, None, None, DETECTION_DETAILS[-1]])
        elif camera_ids:
            dev_id = random.choice(camera_ids)
            detail = random.choice(DETECTION_DETAILS)
        else:
            dev_id = random.choice(all_ids) if all_ids else None
            detail = None
        det_rows.append({
            "type_event": "Intrusion",
            "device_id": dev_id,
            "device_description": _desc(dev_id),
            "result": random.choice(DETECTION_TYPES),
            "action_reported": "False",
            "detail": detail,
            "created_at": dt,
            "updated_at": dt,
        })
    await _bulk_insert_async(db, DetectionEvent, det_rows)
    await db.flush()
    eids["detection"] = list((await db.execute(select(DetectionEvent.id))).scalars().all())

    # Malfunction events (5000, 5일)
    print("    Creating malfunction events (5000)...", flush=True)
    mal_rows: list[dict] = []
    for i in range(5000):
        dt = now - timedelta(
            days=random.randint(0, 4),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59),
        )
        dev_id = random.choice(all_ids) if all_ids else None
        fault = random.choice(FAULT_TYPES)
        mal_rows.append({
            "type_event": "Fault",
            "device_id": dev_id,
            "device_description": _desc(dev_id),
            "reason": fault,
            "action_reported": "False",
            "detail": {
                "fault_code": f"ERR-{random.randint(1000, 9999)}",
                "duration_seconds": random.randint(10, 3600),
                "auto_recovered": random.choice([True, False]),
            } if random.random() < 0.6 else None,
            "created_at": dt,
            "updated_at": dt,
        })
    await _bulk_insert_async(db, MalfunctionEvent, mal_rows)
    await db.flush()
    eids["malfunction"] = list((await db.execute(select(MalfunctionEvent.id))).scalars().all())

    # Connection events (20000)
    print("    Creating connection events (20000)...", flush=True)
    conn_rows: list[dict] = []
    for i in range(20000):
        dt = now - timedelta(
            days=random.randint(0, 7),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59),
        )
        dev_id = random.choice(all_ids) if all_ids else None
        conn_rows.append({
            "type_event": "Connection",
            "device_id": dev_id,
            "device_description": _desc(dev_id),
            "created_at": dt,
            "updated_at": dt,
        })
    await _bulk_insert_async(db, ConnectionEvent, conn_rows)
    await db.flush()
    eids["connection"] = list((await db.execute(select(ConnectionEvent.id))).scalars().all())

    await db.commit()
    total = sum(len(v) for v in eids.values())
    print(f"  [OK] Events created: {total} "
          f"(det:{len(eids['detection'])} mal:{len(eids['malfunction'])} conn:{len(eids['connection'])})")
    return eids


# ── Action Events (async, bulk) ──────────────────────────

async def _create_action_events_async(db: AsyncSession, event_ids: dict, user_names: list[str]) -> None:
    """Create 5000 action events. Invariant: action_reported="True" iff ActionEvent exists."""
    existing = (await db.execute(select(func.count()).select_from(ActionEvent))).scalar() or 0
    if existing > 0:
        print(f"  [OK] Action events already exist: {existing}")
        return

    det_ids = list(event_ids.get("detection", []))
    mal_ids = list(event_ids.get("malfunction", []))
    all_event_ids = det_ids + mal_ids
    random.shuffle(all_event_ids)

    targets = all_event_ids[:5000]

    print("    Updating action_reported for target events (ActionEvent-backed only)...", flush=True)
    det_id_set = set(det_ids)
    mal_id_set = set(mal_ids)
    det_update = [eid for eid in targets if eid in det_id_set]
    mal_update = [eid for eid in targets if eid in mal_id_set]

    for batch_start in range(0, len(det_update), 1000):
        batch = det_update[batch_start:batch_start + 1000]
        await db.execute(
            update(DetectionEvent)
            .where(DetectionEvent.id.in_(batch))
            .values(action_reported="True")
        )
    for batch_start in range(0, len(mal_update), 1000):
        batch = mal_update[batch_start:batch_start + 1000]
        await db.execute(
            update(MalfunctionEvent)
            .where(MalfunctionEvent.id.in_(batch))
            .values(action_reported="True")
        )
    await db.flush()

    print("    Creating action events (5000)...", flush=True)
    now = datetime.now(settings.tz).replace(tzinfo=None)
    rows: list[dict] = []
    for from_id in targets:
        dt = now - timedelta(
            days=random.randint(0, 5),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59),
        )
        rows.append({
            "from_event_id": from_id,
            "type_event": "Action",
            "content": random.choice(ACTION_CONTENTS),
            "user": random.choice(user_names),
            "created_at": dt,
            "updated_at": dt,
        })
    await _bulk_insert_async(db, ActionEvent, rows)

    await db.commit()
    unreported = len(all_event_ids) - len(targets)
    print(f"  [OK] Action events created: {len(targets)} "
          f"(reported: {len(targets)}, unreported: ~{unreported})")


# ── System Events (async) ────────────────────────────────

async def _create_system_events_async(db: AsyncSession, server_ids: list[int]) -> None:
    existing = (await db.execute(select(func.count()).select_from(SystemEvent))).scalar() or 0
    if existing > 0:
        print(f"  [OK] System events already exist: {existing}")
        return

    rows: list[dict] = []
    for i in range(30):
        typ, sev, title = random.choice(SYS_EVENT_TEMPLATES)
        srv_id = random.choice(server_ids) if server_ids else None
        dt = _rand_dt(30)
        rows.append({
            "server_id": srv_id,
            "server_description": f"서버#{srv_id}" if srv_id else None,
            "type_event": typ,
            "severity": sev,
            "title": title,
            "message": f"{title} - 샘플 이벤트 #{i + 1}",
            "source": "system_monitor",
            "is_acknowledged": random.choice([True, False]),
            "created_at": dt,
        })
    await _bulk_insert_async(db, SystemEvent, rows)
    await db.commit()
    print(f"  [OK] System events created: 30")


# ── Config Change Logs (async) ───────────────────────────

async def _create_config_change_logs_async(db: AsyncSession, user_ids: list[int]) -> None:
    existing = (await db.execute(select(func.count()).select_from(ConfigChangeLog))).scalar() or 0
    if existing > 0:
        print(f"  [OK] Config change logs already exist: {existing}")
        return

    user_names = ["김운영", "이운영", "박관제", "최관제", "정유지"]
    rows: list[dict] = []
    for i in range(20):
        res_type, action, desc = random.choice(CONFIG_TEMPLATES)
        idx = random.randint(0, len(user_ids) - 1) if user_ids else 0
        actor_id = user_ids[idx] if user_ids else None
        dt = _rand_dt(30)
        is_update = action in (EnumConfigActionType.UPDATED, EnumConfigActionType.STATUS_CHANGED)
        rows.append({
            "resource_type": res_type,
            "resource_id": random.randint(1, 100),
            "resource_name": f"{res_type.value}-{random.randint(1, 50):03d}",
            "action": action,
            "before_state": {"status": "ACTIVATED"} if is_update else None,
            "after_state": {"status": "DEACTIVATED"} if is_update else None,
            "actor_id": actor_id,
            "actor_name": user_names[idx] if idx < len(user_names) else "system",
            "actor_ip": _rand_ip(),
            "description": desc,
            "created_at": dt,
        })
    await _bulk_insert_async(db, ConfigChangeLog, rows)
    await db.commit()
    print(f"  [OK] Config change logs created: 20")


# ── Audit Logs (async) ───────────────────────────────────

async def _create_audit_logs_async(db: AsyncSession, user_ids: list[int]) -> None:
    existing = (await db.execute(select(func.count()).select_from(AuditLog))).scalar() or 0
    if existing > 0:
        print(f"  [OK] Audit logs already exist: {existing}")
        return

    login_ids = ["operator1", "operator2", "monitor1", "monitor2", "maintainer1"]
    names = ["김운영", "이운영", "박관제", "최관제", "정유지"]
    rows: list[dict] = []
    for i in range(20):
        action_type, resource_type, desc = random.choice(AUDIT_TEMPLATES)
        idx = random.randint(0, len(user_ids) - 1) if user_ids else 0
        actor_id = user_ids[idx] if user_ids else None
        dt = _rand_dt(30)
        rows.append({
            "action_type": action_type.value,
            "action_status": EnumAuditStatus.SUCCESS.value,
            "resource_type": resource_type.value,
            "resource_id": random.randint(1, 10),
            "resource_name": f"리소스-{random.randint(1, 10)}",
            "actor_id": actor_id,
            "actor_login_id": login_ids[idx] if idx < len(login_ids) else "admin",
            "actor_name": names[idx] if idx < len(names) else "관리자",
            "actor_role": "USER",  # v6.0-clone_deploy_bugfix (#2): 레거시 OPERATOR → USER
            "description": desc,
            "ip_address": _rand_ip(),
            "created_at": dt,
        })
    await _bulk_insert_async(db, AuditLog, rows)
    await db.commit()
    print(f"  [OK] Audit logs created: 20")


# ── User Sessions (async, bulk) ──────────────────────────

async def _create_user_sessions_async(db: AsyncSession, user_ids: list[int]) -> None:
    existing = (await db.execute(select(func.count()).select_from(UserSession))).scalar() or 0
    if existing > 0:
        print(f"  [OK] User sessions already exist: {existing}")
        return

    now = datetime.now(settings.tz).replace(tzinfo=None)
    rows: list[dict] = []
    for uid in user_ids:
        rows.append({
            "user_id": uid,
            "token": str(uuid.uuid4()),
            "refresh_token": str(uuid.uuid4()),
            "ip_address": _rand_ip(),
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "expires_at": now + timedelta(hours=8),
            "is_active": True,
            "created_at": now - timedelta(hours=random.randint(1, 4)),
        })
        expired = now - timedelta(days=random.randint(1, 7))
        rows.append({
            "user_id": uid,
            "token": str(uuid.uuid4()),
            "refresh_token": str(uuid.uuid4()),
            "ip_address": _rand_ip(),
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "expires_at": expired + timedelta(hours=8),
            "logged_out_at": expired + timedelta(hours=random.randint(2, 8)),
            "is_active": False,
            "logout_reason": "EXPIRED",
            "created_at": expired,
        })
    count = await _bulk_insert_async(db, UserSession, rows)
    await db.commit()
    print(f"  [OK] User sessions created: {count}")


# ── Login Logs (async, bulk) ─────────────────────────────

async def _create_login_logs_async(db: AsyncSession, user_ids: list[int]) -> None:
    existing = (await db.execute(select(func.count()).select_from(UserLoginLog))).scalar() or 0
    if existing > 0:
        print(f"  [OK] Login logs already exist: {existing}")
        return

    users = (await db.execute(
        select(AccountUser).where(AccountUser.id.in_(user_ids))
    )).scalars().all()
    user_map = {u.id: u.login_id for u in users}

    rows: list[dict] = []
    for uid in user_ids:
        lid = user_map.get(uid, f"user_{uid}")
        # 3 successful logins
        for _ in range(3):
            rows.append({
                "user_id": uid, "login_id": lid,
                "action": EnumLoginAction.LOGIN.value,
                "result": EnumLoginResult.SUCCESS.value,
                "ip_address": _rand_ip(), "user_agent": "Mozilla/5.0",
                "created_at": _rand_dt(30),
            })
        # 1 failed login
        rows.append({
            "user_id": uid, "login_id": lid,
            "action": EnumLoginAction.LOGIN.value,
            "result": EnumLoginResult.FAILURE.value,
            "failure_reason": "INVALID_CREDENTIALS",
            "ip_address": _rand_ip(), "user_agent": "Mozilla/5.0",
            "created_at": _rand_dt(30),
        })
        # 1 logout
        rows.append({
            "user_id": uid, "login_id": lid,
            "action": EnumLoginAction.LOGOUT.value,
            "result": EnumLoginResult.SUCCESS.value,
            "ip_address": _rand_ip(), "user_agent": "Mozilla/5.0",
            "created_at": _rand_dt(30),
        })
        # 1 refresh
        rows.append({
            "user_id": uid, "login_id": lid,
            "action": EnumLoginAction.REFRESH.value,
            "result": EnumLoginResult.SUCCESS.value,
            "ip_address": _rand_ip(), "user_agent": "Mozilla/5.0",
            "created_at": _rand_dt(30),
        })
    count = await _bulk_insert_async(db, UserLoginLog, rows)
    await db.commit()
    print(f"  [OK] Login logs created: {count}")


# ── Proxy/Camera Settings (async) ────────────────────────

async def _create_proxy_settings_async(db: AsyncSession, server_ids: list[int]) -> None:
    existing = (await db.execute(select(func.count()).select_from(ProxySetting))).scalar() or 0
    if existing > 0:
        print(f"  [OK] Proxy settings already exist: {existing}")
        return

    windy_modes = [EnumWindyMode.WIND0, EnumWindyMode.WIND1, EnumWindyMode.WIND2, EnumWindyMode.WIND3]
    count = 0
    for i, sid in enumerate(server_ids[:4]):
        db.add(ProxySetting(
            server_id=sid,
            operation_mode=EnumOperationMode.NORMAL,
            windy_mode=windy_modes[i % len(windy_modes)],
        ))
        count += 1
    await db.commit()
    print(f"  [OK] Proxy settings created: {count}")


async def _create_camera_settings_async(db: AsyncSession) -> None:
    existing = (await db.execute(select(func.count()).select_from(CameraSetting))).scalar() or 0
    if existing > 0:
        print(f"  [OK] Camera settings already exist: {existing}")
        return

    camera_ids = list((await db.execute(select(Camera.id).limit(6))).scalars().all())
    if not camera_ids:
        print("  [WARN] No cameras — skipping camera settings")
        return

    presets = [
        {"weather_mode": EnumWeatherMode.NORMAL, "heater": EnumOnOff.OFF, "fan": EnumOnOff.OFF,
         "headlight": EnumOnOff.OFF, "day_night_mode": EnumDayNightMode.AUTO,
         "focus_mode": EnumFocusMode.AUTO, "iris_mode": EnumIrisMode.AUTO,
         "tracking": EnumTrackingStatus.IDLE},
        {"weather_mode": EnumWeatherMode.FOG, "heater": EnumOnOff.ON, "fan": EnumOnOff.ON,
         "headlight": EnumOnOff.ON, "day_night_mode": EnumDayNightMode.DAY,
         "focus_mode": EnumFocusMode.AUTO, "iris_mode": EnumIrisMode.AUTO,
         "tracking": EnumTrackingStatus.ACTIVE},
        {"weather_mode": EnumWeatherMode.RAIN, "heater": EnumOnOff.ON, "fan": EnumOnOff.OFF,
         "headlight": EnumOnOff.OFF, "day_night_mode": EnumDayNightMode.NIGHT,
         "focus_mode": EnumFocusMode.MANUAL, "iris_mode": EnumIrisMode.AUTO,
         "tracking": EnumTrackingStatus.LOST,
         "camera_mode": EnumCameraVideoMode.NIGHT_ENHANCE},
        {"weather_mode": EnumWeatherMode.NORMAL, "heater": EnumOnOff.OFF, "fan": EnumOnOff.OFF,
         "headlight": EnumOnOff.OFF, "day_night_mode": EnumDayNightMode.AUTO,
         "focus_mode": EnumFocusMode.AUTO, "iris_mode": EnumIrisMode.AUTO,
         "palette": EnumPalette.WHITE_HOT},
        {"weather_mode": EnumWeatherMode.SNOW, "heater": EnumOnOff.ON, "fan": EnumOnOff.ON,
         "headlight": EnumOnOff.ON, "day_night_mode": EnumDayNightMode.AUTO,
         "focus_mode": EnumFocusMode.AUTO, "iris_mode": EnumIrisMode.MANUAL,
         "palette": EnumPalette.IRONBOW},
        {"weather_mode": EnumWeatherMode.NORMAL, "heater": EnumOnOff.OFF, "fan": EnumOnOff.OFF,
         "headlight": EnumOnOff.OFF, "day_night_mode": EnumDayNightMode.AUTO,
         "focus_mode": EnumFocusMode.MANUAL, "iris_mode": EnumIrisMode.MANUAL,
         "tracking": EnumTrackingStatus.ACTIVE,
         "camera_mode": EnumCameraVideoMode.STABILIZATION},
    ]

    count = 0
    for i, cid in enumerate(camera_ids):
        preset = presets[i % len(presets)]
        db.add(CameraSetting(camera_id=cid, **preset))
        count += 1
    await db.commit()
    print(f"  [OK] Camera settings created: {count}")


# ── Async Main Entry Point ───────────────────────────────

async def initialize_sample_data_async(db: AsyncSession) -> None:
    """
    Initialize comprehensive sample data for development/demo (async variant).

    v6.0 Phase 2 dual-stack:
      - INIT_SAMPLE_DATA=false 시 caller에서 스킵 (이 함수는 항상 seed 시도, 각 step 자체 idempotent)
      - 28k+ events 등 대량 데이터는 `_bulk_insert_async`로 500건 단위 executemany
      - 각 step 함수는 count 확인 후 skip → 재실행 안전

    Args:
        db: Async database session
    """
    print("Initializing sample data (async)...")

    # 1. Users
    group_map = await _create_user_groups_async(db)
    user_ids = await _create_users_async(db, group_map)
    user_names = [u["name"] for u in SAMPLE_USERS]

    # 2. Servers
    server_ids = await _create_servers_async(db)

    # 3. Devices
    device_ids = await _create_devices_async(db, server_ids)

    # 4. Device groups + mappings
    await _create_device_groups_async(db, device_ids)

    # 5. Camera presets + ROI + XyPoints
    await _create_camera_presets_async(db)

    # 6. Enclosure metrics
    await _create_enclosure_metrics_async(db)

    # 7. Events (bulk 28k)
    event_ids = await _create_events_async(db, device_ids)

    # 8. Action events (bulk 5k)
    await _create_action_events_async(db, event_ids, user_names)

    # 9. System events
    await _create_system_events_async(db, server_ids)

    # 10. Config change logs
    await _create_config_change_logs_async(db, user_ids)

    # 11. Audit logs
    await _create_audit_logs_async(db, user_ids)

    # 12. User sessions
    await _create_user_sessions_async(db, user_ids)

    # 13. Login logs
    await _create_login_logs_async(db, user_ids)

    # 14. Device settings
    await _create_proxy_settings_async(db, server_ids)
    await _create_camera_settings_async(db)

    print("[OK] Sample data initialization complete")
