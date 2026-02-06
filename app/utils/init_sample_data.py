"""
Sample data initialization for development/demo environment.
Creates comprehensive sample data across all GOP schema tables.

Requirements:
- Events: 110+ records (60 detection, 25 malfunction, 25 connection)
- Devices: Controllers 3, Sensors 300 (100 per controller), others 30 each
- Users: 5 (excluding admin)
- Login logs, sessions, system events, config change logs, audit logs

Idempotent: Safe to call multiple times — skips if data already exists.
"""
import random
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.user import UserGroup, AccountUser, UserSession, UserLoginLog
from app.models.device import Device, Controller, Sensor, Camera, Speaker, Enclosure, Lamp
from app.models.event import Event, DetectionEvent, MalfunctionEvent, ConnectionEvent, ActionEvent
from app.models.system_event import SystemEvent
from app.models.config_change_log import ConfigChangeLog
from app.models.audit_log import AuditLog
from app.models.server import Server, ServerCategory
from app.models.device_setting import ProxySetting, CameraSetting
from app.utils.enums import (
    EnumDeviceType, EnumDeviceStatus,
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
)
from app.utils.auth import hash_password
from app.config import settings

# Reproducible random for consistent sample data
random.seed(42)


# ── Helpers ──────────────────────────────────────────────

def _rand_dt(days_back: int = 30) -> datetime:
    """Random datetime within the last N days."""
    now = datetime.now(settings.tz)
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

    data = [
        {"name": "운영팀", "description": "시스템 운영 담당",
         "permissions": {"devices": "rw", "events": "rw", "reports": "rw"}, "is_active": True},
        {"name": "관제팀", "description": "관제 모니터링 담당",
         "permissions": {"devices": "r", "events": "r", "reports": "r"}, "is_active": True},
        {"name": "유지보수팀", "description": "장비 유지보수 담당",
         "permissions": {"devices": "rw", "events": "r", "reports": "r"}, "is_active": True},
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

SAMPLE_USERS = [
    {"login_id": "operator1", "name": "김운영", "role": "OPERATOR",
     "email": "operator1@gop.kr", "department": "운영부", "position": "주임",
     "employee_number": "EMP001", "phone": "010-1234-5001", "group_key": "운영팀"},
    {"login_id": "operator2", "name": "이운영", "role": "OPERATOR",
     "email": "operator2@gop.kr", "department": "운영부", "position": "대리",
     "employee_number": "EMP002", "phone": "010-1234-5002", "group_key": "운영팀"},
    {"login_id": "monitor1", "name": "박관제", "role": "VIEWER",
     "email": "monitor1@gop.kr", "department": "관제센터", "position": "사원",
     "employee_number": "EMP003", "phone": "010-1234-5003", "group_key": "관제팀"},
    {"login_id": "monitor2", "name": "최관제", "role": "VIEWER",
     "email": "monitor2@gop.kr", "department": "관제센터", "position": "사원",
     "employee_number": "EMP004", "phone": "010-1234-5004", "group_key": "관제팀"},
    {"login_id": "maintainer1", "name": "정유지", "role": "MAINTAINER",
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

SENSOR_TYPES = [
    EnumDeviceType.Fence, EnumDeviceType.PIR, EnumDeviceType.Contact,
    EnumDeviceType.Underground, EnumDeviceType.Cable, EnumDeviceType.Laser,
]


def _create_devices(db: Session) -> dict:
    """Create all devices. Returns {category: [ids]} mapping."""
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

    ids = {"controllers": [], "sensors": [], "cameras": [], "speakers": [], "enclosures": [], "lamps": []}

    # ── Controllers (3) ──
    ctrl_configs = [
        ("A구역 제어기", "10.0.1.1", 9010),
        ("B구역 제어기", "10.0.2.1", 9011),
        ("C구역 제어기", "10.0.3.1", 9012),
    ]
    for i, (name, ip, port) in enumerate(ctrl_configs):
        c = Controller(
            number_device=i + 1, group_device=1, name_device=name,
            type_device=EnumDeviceType.Controller, status=EnumDeviceStatus.ACTIVATED,
            is_enable=True, version="v2.1.0",
            ip_address=ip, ip_port=port,
        )
        db.add(c)
        db.flush()
        ids["controllers"].append(c.id)

    # ── Sensors (300 = 100 per controller) ──
    for ctrl_idx, ctrl_id in enumerate(ids["controllers"]):
        for j in range(100):
            num = ctrl_idx * 100 + j + 1
            s = Sensor(
                number_device=num, group_device=ctrl_idx + 1,
                name_device=f"센서-{num:04d}",
                type_device=random.choice(SENSOR_TYPES),
                status=random.choices(
                    [EnumDeviceStatus.ACTIVATED, EnumDeviceStatus.ERROR, EnumDeviceStatus.DEACTIVATED],
                    weights=[85, 10, 5],
                )[0],
                is_enable=random.choices([True, False], weights=[95, 5])[0],
                version=f"v1.{random.randint(0, 5)}.{random.randint(0, 9)}",
                controller_id=ctrl_id,
            )
            db.add(s)
    db.flush()
    ids["sensors"] = [s.id for s in db.query(Sensor).all()]

    # ── Cameras (30) ──
    cam_modes = [EnumCameraMode.ONVIF, EnumCameraMode.EMSTONE_API, EnumCameraMode.INNODEP_API]
    cam_types = [EnumCameraType.FIXED, EnumCameraType.PTZ]
    for i in range(30):
        cam = Camera(
            number_device=i + 1, group_device=1,
            name_device=f"카메라-{i + 1:03d}",
            type_device=EnumDeviceType.IpCamera,
            status=random.choices([EnumDeviceStatus.ACTIVATED, EnumDeviceStatus.ERROR], weights=[90, 10])[0],
            is_enable=True, version=f"v3.{random.randint(0, 3)}.{random.randint(0, 9)}",
            ip_address=f"10.1.1.{i + 1}", ip_port=554,
            user_name="admin", user_password="camera123",
            mode=random.choice(cam_modes), category=random.choice(cam_types),
            is_record=random.choice([True, False]),
        )
        db.add(cam)
    db.flush()
    ids["cameras"] = [c.id for c in db.query(Camera).all()]

    # ── Speakers (30) ──
    spk_types = [EnumSpeakerType.NORMAL, EnumSpeakerType.ADMIN, EnumSpeakerType.MONITOR]
    for i in range(30):
        spk = Speaker(
            number_device=i + 1, group_device=1,
            name_device=f"스피커-{i + 1:03d}",
            type_device=EnumDeviceType.IpSpeaker,
            status=random.choices([EnumDeviceStatus.ACTIVATED, EnumDeviceStatus.DEACTIVATED], weights=[90, 10])[0],
            is_enable=True, version=f"v1.{random.randint(0, 2)}.0",
            speaker_type=random.choice(spk_types),
            description=f"스피커 {i + 1} - {chr(65 + i % 3)}구역",
        )
        db.add(spk)
    db.flush()
    ids["speakers"] = [s.id for s in db.query(Speaker).all()]

    # ── Enclosures (30) ──
    for i in range(30):
        enc = Enclosure(
            number_device=i + 1, group_device=1,
            name_device=f"함체-{i + 1:03d}",
            type_device=EnumDeviceType.Enclosure,
            status=random.choices(
                [EnumDeviceStatus.ACTIVATED, EnumDeviceStatus.ERROR, EnumDeviceStatus.DEACTIVATED],
                weights=[80, 10, 10],
            )[0],
            is_enable=True, version=f"v1.{random.randint(0, 3)}.0",
            door_status=random.choices([EnumDoorStatus.CLOSED, EnumDoorStatus.OPEN], weights=[85, 15])[0],
            heater_enabled=random.choice([True, False]),
            fan_enabled=random.choice([True, False]),
        )
        db.add(enc)
    db.flush()
    ids["enclosures"] = [e.id for e in db.query(Enclosure).all()]

    # ── Lamps (30) ──
    for i in range(30):
        lmp = Lamp(
            number_device=i + 1, group_device=1,
            name_device=f"경광등-{i + 1:03d}",
            type_device=EnumDeviceType.Lamp,
            status=random.choices([EnumDeviceStatus.ACTIVATED, EnumDeviceStatus.DEACTIVATED], weights=[90, 10])[0],
            is_enable=True, version=f"v1.0.{random.randint(0, 5)}",
            ip_address=f"10.3.1.{i + 1}", ip_port=80,
            description=f"경광등 {i + 1} - {chr(65 + i % 3)}구역",
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


# ── Events ───────────────────────────────────────────────

DETECTION_TYPES = [t for t in EnumDetectionType if t != EnumDetectionType.NONE]
FAULT_TYPES = list(EnumFaultType)


def _create_events(db: Session, device_ids: dict) -> dict:
    """Create 110 events. Returns {category: [event_ids]}."""
    existing = db.query(Event).count()
    if existing > 0:
        print(f"  [OK] Events already exist: {existing}")
        return {
            "detection": [e.id for e in db.query(DetectionEvent).all()],
            "malfunction": [e.id for e in db.query(MalfunctionEvent).all()],
            "connection": [e.id for e in db.query(ConnectionEvent).all()],
        }

    sensor_ids = device_ids.get("sensors", [])
    all_ids = []
    for v in device_ids.values():
        all_ids.extend(v)

    eids = {"detection": [], "malfunction": [], "connection": []}

    # ── Detection events (60) ──
    for _ in range(60):
        dev_id = random.choice(sensor_ids) if sensor_ids else (random.choice(all_ids) if all_ids else None)
        dt = _rand_dt(30)
        e = DetectionEvent(
            type_event="Intrusion",
            device_id=dev_id,
            device_description=f"센서 탐지 - 장비#{dev_id}",
            result=random.choice(DETECTION_TYPES),
            action_reported=random.choice(["True", "False"]),
            created_at=dt, updated_at=dt,
        )
        db.add(e)
        db.flush()
        eids["detection"].append(e.id)

    # ── Malfunction events (25) ──
    for _ in range(25):
        dev_id = random.choice(all_ids) if all_ids else None
        dt = _rand_dt(30)
        e = MalfunctionEvent(
            type_event="Fault",
            device_id=dev_id,
            device_description=f"장비 장애 - 장비#{dev_id}",
            reason=random.choice(FAULT_TYPES),
            action_reported=random.choice(["True", "False"]),
            created_at=dt, updated_at=dt,
        )
        db.add(e)
        db.flush()
        eids["malfunction"].append(e.id)

    # ── Connection events (25) ──
    for _ in range(25):
        dev_id = random.choice(all_ids) if all_ids else None
        dt = _rand_dt(30)
        e = ConnectionEvent(
            type_event="Connection",
            device_id=dev_id,
            device_description=f"연결 이벤트 - 장비#{dev_id}",
            created_at=dt, updated_at=dt,
        )
        db.add(e)
        db.flush()
        eids["connection"].append(e.id)

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
    """Create action events for ~50% of detection and ~30% of malfunction events."""
    existing = db.query(ActionEvent).count()
    if existing > 0:
        print(f"  [OK] Action events already exist: {existing}")
        return

    targets = []
    for eid in event_ids.get("detection", []):
        if random.random() < 0.5:
            targets.append(eid)
    for eid in event_ids.get("malfunction", []):
        if random.random() < 0.3:
            targets.append(eid)

    for from_id in targets:
        dt = _rand_dt(25)
        a = ActionEvent(
            from_event_id=from_id,
            type_event="Action",
            content=random.choice(ACTION_CONTENTS),
            user=random.choice(user_names),
            created_at=dt, updated_at=dt,
        )
        db.add(a)

    db.commit()
    print(f"  [OK] Action events created: {len(targets)}")


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
            actor_role="OPERATOR",
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

    now = datetime.now(settings.tz)
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
         "headlight": EnumOnOff.OFF, "day_night_mode": EnumDayNightMode.AUTO, "pan_tilt_speed": 50, "zoom_speed": 50},
        {"weather_mode": EnumWeatherMode.FOG, "heater": EnumOnOff.ON, "fan": EnumOnOff.ON,
         "headlight": EnumOnOff.ON, "day_night_mode": EnumDayNightMode.DAY, "pan_tilt_speed": 70, "zoom_speed": 60},
        {"weather_mode": EnumWeatherMode.RAIN, "heater": EnumOnOff.ON, "fan": EnumOnOff.OFF,
         "headlight": EnumOnOff.OFF, "day_night_mode": EnumDayNightMode.NIGHT, "pan_tilt_speed": 30, "zoom_speed": 40,
         "camera_mode": EnumCameraVideoMode.NIGHT_ENHANCE},
        {"weather_mode": EnumWeatherMode.NORMAL, "heater": EnumOnOff.OFF, "fan": EnumOnOff.OFF,
         "headlight": EnumOnOff.OFF, "day_night_mode": EnumDayNightMode.AUTO, "palette": EnumPalette.WHITE_HOT},
        {"weather_mode": EnumWeatherMode.SNOW, "heater": EnumOnOff.ON, "fan": EnumOnOff.ON,
         "headlight": EnumOnOff.ON, "day_night_mode": EnumDayNightMode.AUTO, "palette": EnumPalette.IRONBOW},
        {"weather_mode": EnumWeatherMode.NORMAL, "heater": EnumOnOff.OFF, "fan": EnumOnOff.OFF,
         "headlight": EnumOnOff.OFF, "day_night_mode": EnumDayNightMode.AUTO,
         "camera_mode": EnumCameraVideoMode.STABILIZATION, "pan_tilt_speed": 80, "zoom_speed": 80},
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

    # 3. Devices
    device_ids = _create_devices(db)

    # 4. Events
    event_ids = _create_events(db, device_ids)

    # 5. Action events
    _create_action_events(db, event_ids, user_names)

    # 6. System events
    _create_system_events(db, server_ids)

    # 7. Config change logs
    _create_config_change_logs(db, user_ids)

    # 8. Audit logs
    _create_audit_logs(db, user_ids)

    # 9. User sessions
    _create_user_sessions(db, user_ids)

    # 10. Login logs
    _create_login_logs(db, user_ids)

    # 11. Device settings (proxy + camera)
    _create_proxy_settings(db, server_ids)
    _create_camera_settings(db)

    print("[OK] Sample data initialization complete")
