"""
PostgreSQL pg_notify triggers for GOP master data sync.
PRD: PRD_DB_Change_Monitor.md Section 4

Fix: Triggers are placed on the `devices` base table (not sub-type tables)
to handle SQLAlchemy Joined Table Inheritance correctly.
When PATCH updates base Device fields (name_device, status, etc.),
only the `devices` table is updated — sub-type triggers would never fire.
"""
from sqlalchemy import text

GET_NOTIFY_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION fn_notify_gop_sync()
RETURNS trigger AS $$
DECLARE
    payload JSONB;
    action_type TEXT;
    resource_id INTEGER;
    category TEXT;
BEGIN
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

    IF TG_TABLE_NAME = 'devices' THEN
        -- category_device로 서브타입 판별 (Joined Table Inheritance 대응)
        -- PATCH가 base 필드만 바꿔도 devices 테이블만 UPDATE되므로 여기서 처리
        IF TG_OP = 'DELETE' THEN
            category := OLD.category_device::text;
        ELSE
            category := NEW.category_device::text;
        END IF;
        IF LOWER(category) NOT IN ('controller','sensor','camera','speaker','enclosure','lamp') THEN
            RETURN NULL;
        END IF;
        payload := jsonb_build_object(
            'cmd', 'SYNC_DEVICE',
            'action', action_type,
            'type_device', INITCAP(LOWER(category)),
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
"""

GET_TRIGGER_SQLS = [
    # Migration: remove old sub-type triggers (if they exist from previous deployment)
    """
    DROP TRIGGER IF EXISTS trg_sync_controllers ON controllers;
    DROP TRIGGER IF EXISTS trg_sync_sensors ON sensors;
    DROP TRIGGER IF EXISTS trg_sync_cameras ON cameras;
    DROP TRIGGER IF EXISTS trg_sync_speakers ON speakers;
    DROP TRIGGER IF EXISTS trg_sync_enclosures ON enclosures;
    DROP TRIGGER IF EXISTS trg_sync_lamps ON lamps;
    """,
    # Device: trigger on devices base table (covers ALL PATCH/PUT/POST/DELETE)
    # SQLAlchemy Joined Table Inheritance always updates devices table regardless
    # of which fields changed (base or sub-type specific)
    """
    DROP TRIGGER IF EXISTS trg_sync_devices ON devices;
    CREATE TRIGGER trg_sync_devices
        AFTER INSERT OR UPDATE OR DELETE ON devices
        FOR EACH ROW EXECUTE FUNCTION fn_notify_gop_sync();
    """,
    # Master data triggers (standalone tables, not joined inheritance)
    """
    DROP TRIGGER IF EXISTS trg_sync_servers ON servers;
    CREATE TRIGGER trg_sync_servers
        AFTER INSERT OR UPDATE OR DELETE ON servers
        FOR EACH ROW EXECUTE FUNCTION fn_notify_gop_sync();
    """,
    """
    DROP TRIGGER IF EXISTS trg_sync_server_categories ON server_categories;
    CREATE TRIGGER trg_sync_server_categories
        AFTER INSERT OR UPDATE OR DELETE ON server_categories
        FOR EACH ROW EXECUTE FUNCTION fn_notify_gop_sync();
    """,
    """
    DROP TRIGGER IF EXISTS trg_sync_device_groups ON device_groups;
    CREATE TRIGGER trg_sync_device_groups
        AFTER INSERT OR UPDATE OR DELETE ON device_groups
        FOR EACH ROW EXECUTE FUNCTION fn_notify_gop_sync();
    """,
    """
    DROP TRIGGER IF EXISTS trg_sync_event_mappings ON event_mappings;
    CREATE TRIGGER trg_sync_event_mappings
        AFTER INSERT OR UPDATE OR DELETE ON event_mappings
        FOR EACH ROW EXECUTE FUNCTION fn_notify_gop_sync();
    """,
    """
    DROP TRIGGER IF EXISTS trg_sync_camera_presets ON camera_presets;
    CREATE TRIGGER trg_sync_camera_presets
        AFTER INSERT OR UPDATE OR DELETE ON camera_presets
        FOR EACH ROW EXECUTE FUNCTION fn_notify_gop_sync();
    """,
    """
    DROP TRIGGER IF EXISTS trg_sync_file_groups ON file_groups;
    CREATE TRIGGER trg_sync_file_groups
        AFTER INSERT OR UPDATE OR DELETE ON file_groups
        FOR EACH ROW EXECUTE FUNCTION fn_notify_gop_sync();
    """,
    """
    DROP TRIGGER IF EXISTS trg_sync_camera_settings ON camera_settings;
    CREATE TRIGGER trg_sync_camera_settings
        AFTER INSERT OR UPDATE OR DELETE ON camera_settings
        FOR EACH ROW EXECUTE FUNCTION fn_notify_gop_sync();
    """,
    """
    DROP TRIGGER IF EXISTS trg_sync_proxy_settings ON proxy_settings;
    CREATE TRIGGER trg_sync_proxy_settings
        AFTER INSERT OR UPDATE OR DELETE ON proxy_settings
        FOR EACH ROW EXECUTE FUNCTION fn_notify_gop_sync();
    """,
]


def apply_triggers(engine) -> None:
    """Apply pg_notify triggers to PostgreSQL. Skips if using SQLite."""
    dialect = engine.dialect.name
    if dialect != "postgresql":
        return

    with engine.connect() as conn:
        conn.execute(text(GET_NOTIFY_FUNCTION_SQL))
        for sql in GET_TRIGGER_SQLS:
            conn.execute(text(sql))
        conn.commit()
