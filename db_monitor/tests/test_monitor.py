"""
TDD tests for db_monitor/main.py
PRD: PRD_DB_Change_Monitor.md Phase 3
"""


# CMD → NATS subject suffix mappings
CMD_SUBJECT_CASES = [
    ("SYNC_DEVICE",         "all.sync.device"),
    ("SYNC_SERVER",         "all.sync.server"),
    ("SYNC_CATEGORY",       "all.sync.category"),
    ("SYNC_DEVICE_GROUP",   "all.sync.device-group"),
    ("SYNC_EVENT_MAPPING",  "all.sync.event-mapping"),
    ("SYNC_PRESET",         "all.sync.preset"),
    ("SYNC_FILE_GROUP",     "all.sync.file-group"),
    ("SYNC_CAMERA_SETTING", "all.sync.camera-setting"),
    ("SYNC_PROXY_SETTING",  "all.sync.proxy-setting"),
]


def test_sync_device_subject():
    from db_monitor.main import cmd_to_subject
    assert cmd_to_subject("SYNC_DEVICE", "unit001") == "sensorway.unit001.all.sync.device"


def test_sync_server_subject():
    from db_monitor.main import cmd_to_subject
    assert cmd_to_subject("SYNC_SERVER", "unit001") == "sensorway.unit001.all.sync.server"


def test_sync_category_subject():
    from db_monitor.main import cmd_to_subject
    assert cmd_to_subject("SYNC_CATEGORY", "unit001") == "sensorway.unit001.all.sync.category"


def test_sync_device_group_subject():
    from db_monitor.main import cmd_to_subject
    assert cmd_to_subject("SYNC_DEVICE_GROUP", "unit001") == "sensorway.unit001.all.sync.device-group"


def test_sync_event_mapping_subject():
    from db_monitor.main import cmd_to_subject
    assert cmd_to_subject("SYNC_EVENT_MAPPING", "unit001") == "sensorway.unit001.all.sync.event-mapping"


def test_sync_preset_subject():
    from db_monitor.main import cmd_to_subject
    assert cmd_to_subject("SYNC_PRESET", "unit001") == "sensorway.unit001.all.sync.preset"


def test_sync_file_group_subject():
    from db_monitor.main import cmd_to_subject
    assert cmd_to_subject("SYNC_FILE_GROUP", "unit001") == "sensorway.unit001.all.sync.file-group"


def test_sync_camera_setting_subject():
    from db_monitor.main import cmd_to_subject
    assert cmd_to_subject("SYNC_CAMERA_SETTING", "unit001") == "sensorway.unit001.all.sync.camera-setting"


def test_sync_proxy_setting_subject():
    from db_monitor.main import cmd_to_subject
    assert cmd_to_subject("SYNC_PROXY_SETTING", "unit001") == "sensorway.unit001.all.sync.proxy-setting"


def test_unknown_cmd_returns_none():
    from db_monitor.main import cmd_to_subject
    assert cmd_to_subject("UNKNOWN_CMD", "unit001") is None


def test_build_envelope_structure():
    from db_monitor.main import build_nats_envelope
    body = {"action": "UPDATED", "resource_id": 42}
    envelope = build_nats_envelope("SYNC_DEVICE", body)
    assert "id" in envelope
    assert envelope["m_type"] == "PUB"
    assert envelope["cmd"] == "SYNC_DEVICE"
    assert envelope["from"] == "DBApi"
    assert envelope["body"] == body
    assert "created" in envelope


def test_envelope_id_is_unique():
    from db_monitor.main import build_nats_envelope
    body = {"action": "CREATED", "resource_id": 1}
    e1 = build_nats_envelope("SYNC_SERVER", body)
    e2 = build_nats_envelope("SYNC_SERVER", body)
    assert e1["id"] != e2["id"]
