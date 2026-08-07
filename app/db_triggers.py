"""
PostgreSQL pg_notify triggers for GOP master data sync.
PRD: PRD_DB_Change_Monitor.md Section 4

Fix: INSERT/UPDATE/DELETE of base Device fields fire the `devices` base-table
trigger (handles SQLAlchemy Joined Table Inheritance — PATCH of base fields only
updates `devices`).

MSG-01 (2026-07-09): subtype 전용 컬럼(예: cameras.mode)만 UPDATE 하면 `devices` 는
변경되지 않아 base 트리거가 발화하지 않는다. 이를 보완하기 위해 6개 subtype 테이블
(controllers/sensors/cameras/speakers/enclosures/lamps)에 **AFTER UPDATE** 트리거를 두어
동일한 SYNC_DEVICE payload 를 발행한다. 부모+자식이 같은 트랜잭션에서 함께 UPDATE 돼도
PostgreSQL 이 동일 (채널,payload) NOTIFY 를 1건으로 합쳐 전달하므로 중복이 자동 억제된다.
(INSERT/DELETE 는 조인상속상 `devices` 도 함께 바뀌어 base 트리거가 담당 → subtype 은 UPDATE 만.)
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
    ELSIF TG_TABLE_NAME IN ('controllers','sensors','cameras','speakers','enclosures','lamps') THEN
        -- MSG-01: subtype 전용 컬럼(camera.mode 등)만 UPDATE 되면 devices 는 미변경 →
        --   devices 트리거가 발화하지 않아 SYNC_DEVICE 누락. 여기서 보완 발행한다.
        --   ★ devices 트리거의 UPDATE payload 와 '완전히 동일'하게 만든다:
        --     같은 트랜잭션에서 부모(devices)+자식(cameras)이 함께 UPDATE 돼도
        --     PostgreSQL 은 동일 (채널,payload) NOTIFY 를 트랜잭션 내 1건으로 합쳐 전달한다
        --     → 중복 억제가 자동. (subtype 은 UPDATE 만 트리거 — INSERT/DELETE 는 조인상속상
        --      devices 도 함께 변경되어 devices 트리거가 담당.)
        payload := jsonb_build_object(
            'cmd', 'SYNC_DEVICE',
            'action', 'UPDATED',
            'type_device', CASE TG_TABLE_NAME
                WHEN 'controllers' THEN 'Controller'
                WHEN 'sensors'     THEN 'Sensor'
                WHEN 'cameras'     THEN 'Camera'
                WHEN 'speakers'    THEN 'Speaker'
                WHEN 'enclosures'  THEN 'Enclosure'
                WHEN 'lamps'       THEN 'Lamp'
            END,
            'resource_id', NEW.id
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
            'resource_id', resource_id,
            'camera_id', CASE WHEN TG_OP = 'DELETE' THEN OLD.camera_id ELSE NEW.camera_id END
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
            'camera_id', CASE WHEN TG_OP = 'DELETE' THEN OLD.camera_id ELSE NEW.camera_id END
        );
    ELSIF TG_TABLE_NAME = 'proxy_settings' THEN
        payload := jsonb_build_object(
            'cmd', 'SYNC_PROXY_SETTING',
            'action', action_type,
            'server_id', CASE WHEN TG_OP = 'DELETE' THEN OLD.server_id ELSE NEW.server_id END
        );
    -- v4.6 FR-8: event_mapping_cameras/speakers/lamps row-level 분기 제거
    --   v4.3 마이그레이션에서 statement-level 트리거(fn_notify_emc_stmt /
    --   fn_notify_ems_stmt / fn_notify_eml_stmt)로 대체됨. 이 row-level 분기는
    --   더 이상 호출되지 않으나, 잘못 마이그레이션 되돌리면 SYNC_EVENT_MAPPING
    --   이중 발행 위험. 안전을 위해 row-level 분기 제거.
    ELSIF TG_TABLE_NAME = 'device_group_mappings' THEN
        IF TG_OP = 'DELETE' THEN
            resource_id := OLD.group_id;
        ELSE
            resource_id := NEW.group_id;
        END IF;
        payload := jsonb_build_object(
            'cmd', 'SYNC_DEVICE_GROUP',
            'action', 'UPDATED',
            'resource_id', resource_id
        );
    ELSIF TG_TABLE_NAME = 'rois' THEN
        IF TG_OP = 'DELETE' THEN
            resource_id := OLD.preset_id;
        ELSE
            resource_id := NEW.preset_id;
        END IF;
        payload := jsonb_build_object(
            'cmd', 'SYNC_PRESET',
            'action', 'UPDATED',
            'resource_id', resource_id,
            'camera_id', (SELECT camera_id FROM camera_presets WHERE id = resource_id)
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
    # MSG-01: subtype 테이블 AFTER UPDATE 트리거 — 전용 컬럼 변경 시 SYNC_DEVICE 보완 발행.
    #   (기존엔 이 트리거들을 DROP 만 했음 → subtype-only UPDATE 가 NATS 미발행되던 결함.)
    #   INSERT/DELETE 는 devices 트리거가 담당하므로 여기선 UPDATE 만.
    #   부모+자식 동시 UPDATE 는 devices 트리거와 동일 payload → NOTIFY 자동 중복제거로 1건.
    """
    DROP TRIGGER IF EXISTS trg_sync_controllers ON controllers;
    DROP TRIGGER IF EXISTS trg_sync_sensors ON sensors;
    DROP TRIGGER IF EXISTS trg_sync_cameras ON cameras;
    DROP TRIGGER IF EXISTS trg_sync_speakers ON speakers;
    DROP TRIGGER IF EXISTS trg_sync_enclosures ON enclosures;
    DROP TRIGGER IF EXISTS trg_sync_lamps ON lamps;

    CREATE TRIGGER trg_sync_controllers AFTER UPDATE ON controllers
        FOR EACH ROW EXECUTE FUNCTION fn_notify_gop_sync();
    CREATE TRIGGER trg_sync_sensors AFTER UPDATE ON sensors
        FOR EACH ROW EXECUTE FUNCTION fn_notify_gop_sync();
    CREATE TRIGGER trg_sync_cameras AFTER UPDATE ON cameras
        FOR EACH ROW EXECUTE FUNCTION fn_notify_gop_sync();
    CREATE TRIGGER trg_sync_speakers AFTER UPDATE ON speakers
        FOR EACH ROW EXECUTE FUNCTION fn_notify_gop_sync();
    CREATE TRIGGER trg_sync_enclosures AFTER UPDATE ON enclosures
        FOR EACH ROW EXECUTE FUNCTION fn_notify_gop_sync();
    CREATE TRIGGER trg_sync_lamps AFTER UPDATE ON lamps
        FOR EACH ROW EXECUTE FUNCTION fn_notify_gop_sync();
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
    # PRD_SYNC_Child_Table_Triggers v1.0: 하위 테이블 트리거
    """
    DROP TRIGGER IF EXISTS trg_sync_event_mapping_cameras ON event_mapping_cameras;
    CREATE TRIGGER trg_sync_event_mapping_cameras
        AFTER INSERT OR UPDATE OR DELETE ON event_mapping_cameras
        FOR EACH ROW EXECUTE FUNCTION fn_notify_gop_sync();
    """,
    """
    DROP TRIGGER IF EXISTS trg_sync_event_mapping_speakers ON event_mapping_speakers;
    CREATE TRIGGER trg_sync_event_mapping_speakers
        AFTER INSERT OR UPDATE OR DELETE ON event_mapping_speakers
        FOR EACH ROW EXECUTE FUNCTION fn_notify_gop_sync();
    """,
    """
    DROP TRIGGER IF EXISTS trg_sync_event_mapping_lamps ON event_mapping_lamps;
    CREATE TRIGGER trg_sync_event_mapping_lamps
        AFTER INSERT OR UPDATE OR DELETE ON event_mapping_lamps
        FOR EACH ROW EXECUTE FUNCTION fn_notify_gop_sync();
    """,
    # device_group_mappings: statement-level 트리거로 변경 (PRD_DeviceGroup_BulkUnassign §5.3)
    # 벌크 INSERT/DELETE N건 → group_id 별 1건만 SYNC_DEVICE_GROUP 발행
    # 등록(POST .../devices)도 자동 수혜. PG10+ REFERENCING NEW/OLD TABLE 필요.
    """
    DROP TRIGGER IF EXISTS trg_sync_device_group_mappings ON device_group_mappings;
    DROP TRIGGER IF EXISTS trg_sync_dgm_ins ON device_group_mappings;
    DROP TRIGGER IF EXISTS trg_sync_dgm_del ON device_group_mappings;
    DROP TRIGGER IF EXISTS trg_sync_dgm_upd ON device_group_mappings;

    CREATE OR REPLACE FUNCTION fn_notify_dgm_stmt()
    RETURNS trigger AS $$
    DECLARE
        r RECORD;
    BEGIN
        IF TG_OP = 'INSERT' THEN
            FOR r IN SELECT DISTINCT group_id FROM new_rows LOOP
                PERFORM pg_notify('gop_sync', jsonb_build_object(
                    'cmd','SYNC_DEVICE_GROUP','action','UPDATED','resource_id',r.group_id
                )::text);
            END LOOP;
        ELSIF TG_OP = 'DELETE' THEN
            FOR r IN SELECT DISTINCT group_id FROM old_rows LOOP
                PERFORM pg_notify('gop_sync', jsonb_build_object(
                    'cmd','SYNC_DEVICE_GROUP','action','UPDATED','resource_id',r.group_id
                )::text);
            END LOOP;
        ELSIF TG_OP = 'UPDATE' THEN
            FOR r IN
                SELECT DISTINCT group_id FROM old_rows
                UNION
                SELECT DISTINCT group_id FROM new_rows
            LOOP
                PERFORM pg_notify('gop_sync', jsonb_build_object(
                    'cmd','SYNC_DEVICE_GROUP','action','UPDATED','resource_id',r.group_id
                )::text);
            END LOOP;
        END IF;
        RETURN NULL;
    END $$ LANGUAGE plpgsql;

    CREATE TRIGGER trg_sync_dgm_ins
        AFTER INSERT ON device_group_mappings
        REFERENCING NEW TABLE AS new_rows
        FOR EACH STATEMENT EXECUTE FUNCTION fn_notify_dgm_stmt();

    CREATE TRIGGER trg_sync_dgm_del
        AFTER DELETE ON device_group_mappings
        REFERENCING OLD TABLE AS old_rows
        FOR EACH STATEMENT EXECUTE FUNCTION fn_notify_dgm_stmt();

    CREATE TRIGGER trg_sync_dgm_upd
        AFTER UPDATE ON device_group_mappings
        REFERENCING OLD TABLE AS old_rows NEW TABLE AS new_rows
        FOR EACH STATEMENT EXECUTE FUNCTION fn_notify_dgm_stmt();
    """,
    """
    DROP TRIGGER IF EXISTS trg_sync_rois ON rois;
    CREATE TRIGGER trg_sync_rois
        AFTER INSERT OR UPDATE OR DELETE ON rois
        FOR EACH ROW EXECUTE FUNCTION fn_notify_gop_sync();
    """,
    # event_mapping_cameras: row-level → statement-level
    # 벌크 INSERT/DELETE N건 → event_mapping_id 별 1건만 SYNC_EVENT_MAPPING 발행
    # PRD_EventMapping_BulkOperations.md §5.3
    """
    DROP TRIGGER IF EXISTS trg_sync_event_mapping_cameras ON event_mapping_cameras;
    DROP TRIGGER IF EXISTS trg_sync_emc_ins ON event_mapping_cameras;
    DROP TRIGGER IF EXISTS trg_sync_emc_del ON event_mapping_cameras;
    DROP TRIGGER IF EXISTS trg_sync_emc_upd ON event_mapping_cameras;

    CREATE OR REPLACE FUNCTION fn_notify_emc_stmt()
    RETURNS trigger AS $$
    DECLARE
        r RECORD;
    BEGIN
        IF TG_OP = 'INSERT' THEN
            FOR r IN SELECT DISTINCT event_mapping_id FROM new_rows LOOP
                PERFORM pg_notify('gop_sync', jsonb_build_object(
                    'cmd','SYNC_EVENT_MAPPING','action','UPDATED','resource_id',r.event_mapping_id
                )::text);
            END LOOP;
        ELSIF TG_OP = 'DELETE' THEN
            FOR r IN SELECT DISTINCT event_mapping_id FROM old_rows LOOP
                PERFORM pg_notify('gop_sync', jsonb_build_object(
                    'cmd','SYNC_EVENT_MAPPING','action','UPDATED','resource_id',r.event_mapping_id
                )::text);
            END LOOP;
        ELSIF TG_OP = 'UPDATE' THEN
            FOR r IN
                SELECT DISTINCT event_mapping_id FROM old_rows
                UNION
                SELECT DISTINCT event_mapping_id FROM new_rows
            LOOP
                PERFORM pg_notify('gop_sync', jsonb_build_object(
                    'cmd','SYNC_EVENT_MAPPING','action','UPDATED','resource_id',r.event_mapping_id
                )::text);
            END LOOP;
        END IF;
        RETURN NULL;
    END $$ LANGUAGE plpgsql;

    CREATE TRIGGER trg_sync_emc_ins
        AFTER INSERT ON event_mapping_cameras
        REFERENCING NEW TABLE AS new_rows
        FOR EACH STATEMENT EXECUTE FUNCTION fn_notify_emc_stmt();

    CREATE TRIGGER trg_sync_emc_del
        AFTER DELETE ON event_mapping_cameras
        REFERENCING OLD TABLE AS old_rows
        FOR EACH STATEMENT EXECUTE FUNCTION fn_notify_emc_stmt();

    CREATE TRIGGER trg_sync_emc_upd
        AFTER UPDATE ON event_mapping_cameras
        REFERENCING OLD TABLE AS old_rows NEW TABLE AS new_rows
        FOR EACH STATEMENT EXECUTE FUNCTION fn_notify_emc_stmt();
    """,
    # event_mapping_speakers: row-level → statement-level
    """
    DROP TRIGGER IF EXISTS trg_sync_event_mapping_speakers ON event_mapping_speakers;
    DROP TRIGGER IF EXISTS trg_sync_ems_ins ON event_mapping_speakers;
    DROP TRIGGER IF EXISTS trg_sync_ems_del ON event_mapping_speakers;
    DROP TRIGGER IF EXISTS trg_sync_ems_upd ON event_mapping_speakers;

    CREATE OR REPLACE FUNCTION fn_notify_ems_stmt()
    RETURNS trigger AS $$
    DECLARE
        r RECORD;
    BEGIN
        IF TG_OP = 'INSERT' THEN
            FOR r IN SELECT DISTINCT event_mapping_id FROM new_rows LOOP
                PERFORM pg_notify('gop_sync', jsonb_build_object(
                    'cmd','SYNC_EVENT_MAPPING','action','UPDATED','resource_id',r.event_mapping_id
                )::text);
            END LOOP;
        ELSIF TG_OP = 'DELETE' THEN
            FOR r IN SELECT DISTINCT event_mapping_id FROM old_rows LOOP
                PERFORM pg_notify('gop_sync', jsonb_build_object(
                    'cmd','SYNC_EVENT_MAPPING','action','UPDATED','resource_id',r.event_mapping_id
                )::text);
            END LOOP;
        ELSIF TG_OP = 'UPDATE' THEN
            FOR r IN
                SELECT DISTINCT event_mapping_id FROM old_rows
                UNION
                SELECT DISTINCT event_mapping_id FROM new_rows
            LOOP
                PERFORM pg_notify('gop_sync', jsonb_build_object(
                    'cmd','SYNC_EVENT_MAPPING','action','UPDATED','resource_id',r.event_mapping_id
                )::text);
            END LOOP;
        END IF;
        RETURN NULL;
    END $$ LANGUAGE plpgsql;

    CREATE TRIGGER trg_sync_ems_ins
        AFTER INSERT ON event_mapping_speakers
        REFERENCING NEW TABLE AS new_rows
        FOR EACH STATEMENT EXECUTE FUNCTION fn_notify_ems_stmt();

    CREATE TRIGGER trg_sync_ems_del
        AFTER DELETE ON event_mapping_speakers
        REFERENCING OLD TABLE AS old_rows
        FOR EACH STATEMENT EXECUTE FUNCTION fn_notify_ems_stmt();

    CREATE TRIGGER trg_sync_ems_upd
        AFTER UPDATE ON event_mapping_speakers
        REFERENCING OLD TABLE AS old_rows NEW TABLE AS new_rows
        FOR EACH STATEMENT EXECUTE FUNCTION fn_notify_ems_stmt();
    """,
    # event_mapping_lamps: row-level → statement-level
    """
    DROP TRIGGER IF EXISTS trg_sync_event_mapping_lamps ON event_mapping_lamps;
    DROP TRIGGER IF EXISTS trg_sync_eml_ins ON event_mapping_lamps;
    DROP TRIGGER IF EXISTS trg_sync_eml_del ON event_mapping_lamps;
    DROP TRIGGER IF EXISTS trg_sync_eml_upd ON event_mapping_lamps;

    CREATE OR REPLACE FUNCTION fn_notify_eml_stmt()
    RETURNS trigger AS $$
    DECLARE
        r RECORD;
    BEGIN
        IF TG_OP = 'INSERT' THEN
            FOR r IN SELECT DISTINCT event_mapping_id FROM new_rows LOOP
                PERFORM pg_notify('gop_sync', jsonb_build_object(
                    'cmd','SYNC_EVENT_MAPPING','action','UPDATED','resource_id',r.event_mapping_id
                )::text);
            END LOOP;
        ELSIF TG_OP = 'DELETE' THEN
            FOR r IN SELECT DISTINCT event_mapping_id FROM old_rows LOOP
                PERFORM pg_notify('gop_sync', jsonb_build_object(
                    'cmd','SYNC_EVENT_MAPPING','action','UPDATED','resource_id',r.event_mapping_id
                )::text);
            END LOOP;
        ELSIF TG_OP = 'UPDATE' THEN
            FOR r IN
                SELECT DISTINCT event_mapping_id FROM old_rows
                UNION
                SELECT DISTINCT event_mapping_id FROM new_rows
            LOOP
                PERFORM pg_notify('gop_sync', jsonb_build_object(
                    'cmd','SYNC_EVENT_MAPPING','action','UPDATED','resource_id',r.event_mapping_id
                )::text);
            END LOOP;
        END IF;
        RETURN NULL;
    END $$ LANGUAGE plpgsql;

    CREATE TRIGGER trg_sync_eml_ins
        AFTER INSERT ON event_mapping_lamps
        REFERENCING NEW TABLE AS new_rows
        FOR EACH STATEMENT EXECUTE FUNCTION fn_notify_eml_stmt();

    CREATE TRIGGER trg_sync_eml_del
        AFTER DELETE ON event_mapping_lamps
        REFERENCING OLD TABLE AS old_rows
        FOR EACH STATEMENT EXECUTE FUNCTION fn_notify_eml_stmt();

    CREATE TRIGGER trg_sync_eml_upd
        AFTER UPDATE ON event_mapping_lamps
        REFERENCING OLD TABLE AS old_rows NEW TABLE AS new_rows
        FOR EACH STATEMENT EXECUTE FUNCTION fn_notify_eml_stmt();
    """,
    # SYSTEM_EVENT (nats-dbapi-sync-completion FR-04): system_events AFTER INSERT →
    #   신규 채널 gop_event 로 **Full-DTO** NOTIFY (SYNC 의 gop_sync '알림만' 과 분리).
    #   acknowledged=is_acknowledged 매핑, enum(type_event/severity) ::text 캐스트.
    #   트리거 실패가 INSERT 를 롤백하지 않도록 EXCEPTION WHEN OTHERS 로 방어(best-effort).
    """
    CREATE OR REPLACE FUNCTION fn_notify_system_event()
    RETURNS trigger AS $$
    BEGIN
        PERFORM pg_notify('gop_event', jsonb_build_object(
            'cmd', 'SYSTEM_EVENT',
            'id', NEW.id,
            'server_id', NEW.server_id,
            'type_event', NEW.type_event::text,
            'severity', NEW.severity::text,
            'source', NEW.source,
            'message', NEW.message,
            'acknowledged', NEW.is_acknowledged,
            'server_description', NEW.server_description,
            'created_at', NEW.created_at
        )::text);
        RETURN NULL;
    EXCEPTION WHEN OTHERS THEN
        RETURN NULL;
    END;
    $$ LANGUAGE plpgsql;

    DROP TRIGGER IF EXISTS trg_notify_system_event ON system_events;
    CREATE TRIGGER trg_notify_system_event
        AFTER INSERT ON system_events
        FOR EACH ROW EXECUTE FUNCTION fn_notify_system_event();
    """,
    # SYNC_DETECTION (detection-sync-message FR-01/02): detection_events AFTER UPDATE OR DELETE →
    #   gop_sync 채널 '알림만' NOTIFY {cmd, action, resource_id}. **INSERT 미발행**(필드 DETECT 중복/이중연동 방지).
    #   목적: PTZ 회전 후 detail(썸네일) 갱신을 GIS 가 재조회하도록 통지. from=DBApi·subject=all.sync.detection
    #   으로 필드 DETECT(all.event.detect, from=PidsProxy/AiAnalysis)와 완전 분리. 알림형이라 resource_id 만(Full-DTO 아님).
    #   트리거 실패가 detection UPDATE/DELETE 를 롤백하지 않도록 EXCEPTION WHEN OTHERS 방어(best-effort).
    """
    CREATE OR REPLACE FUNCTION fn_notify_detection_sync()
    RETURNS trigger AS $$
    BEGIN
        PERFORM pg_notify('gop_sync', jsonb_build_object(
            'cmd', 'SYNC_DETECTION',
            'action', CASE WHEN TG_OP = 'DELETE' THEN 'DELETED' ELSE 'UPDATED' END,
            'resource_id', CASE WHEN TG_OP = 'DELETE' THEN OLD.id ELSE NEW.id END
        )::text);
        RETURN NULL;
    EXCEPTION WHEN OTHERS THEN
        RETURN NULL;
    END;
    $$ LANGUAGE plpgsql;

    DROP TRIGGER IF EXISTS trg_notify_detection_sync ON detection_events;
    CREATE TRIGGER trg_notify_detection_sync
        AFTER UPDATE OR DELETE ON detection_events
        FOR EACH ROW EXECUTE FUNCTION fn_notify_detection_sync();
    """,
    # SYNC_EVENT_SUPPRESSION (event-suppression-sync-message):
    #   억제(정비 창) = **이벤트 파이프라인 통제** 상태. 누가 바꾸면 전 서브시스템이 인지하고
    #   "현재 공사 중"을 판정할 수 있어야 한다. 알림형(패턴3) {cmd, action, resource_id, status}.
    #
    #   ★ 트리거가 3벌인 이유 (하나라도 빠지면 사각지대):
    #   (1) 부모 row-level      — 생성/시간·이름 변경/취소(soft-cancel=UPDATE)/하드삭제
    #   (2) junction statement  — **대상 배열만 바꾸는 PATCH 는 부모 행이 dirty 가 안 돼 UPDATE 문이
    #       나가지 않는다**(router 가 스칼라만 setattr, 대상은 relationship 으로만 교체).
    #       MSG-01(subtype-only UPDATE 누락)과 동일한 구조적 함정 → junction 2테이블에 별도 트리거.
    #   (3) 창 경계 전이는 date-job(suppression_scheduler)이 notified_status 를 UPDATE → (1)이 포착.
    #
    #   ★ 중복 억제: junction 트리거는 `age(s.xmin) <> 0` 으로 **부모가 같은 트랜잭션에서 쓰인 경우 skip**.
    #     - 생성(부모 INSERT + junction INSERT) → 부모 CREATED 1건만
    #     - 스칼라+대상 동시 PATCH        → 부모 UPDATED 1건만
    #     - **대상만 PATCH**(부모 무변경)  → junction UPDATED 1건 (핵심 케이스)
    #     - 하드삭제(부모 DELETE + cascade) → JOIN 이 EXISTS 가드라 junction 0건, 부모 DELETED 1건
    #   ★ status 는 공용 SQL 함수로 계산해 부모/junction payload 를 완전 동일하게 유지
    #     (동일 (채널,payload) NOTIFY 는 PostgreSQL 이 트랜잭션 내에서 1건으로 병합).
    #     now() = 트랜잭션 시작시각이라 같은 트랜잭션 내 두 트리거가 같은 값을 본다.
    #   ★ 트리거 실패가 사용자 트랜잭션을 롤백시키지 않도록 EXCEPTION WHEN OTHERS 방어(best-effort).
    #     — fn_notify_gop_sync 는 EXCEPTION 가드가 없어 확장하지 않고 전용 함수를 둔다.
    """
    CREATE OR REPLACE FUNCTION fn_suppression_status(
        p_revoked timestamptz, p_start timestamptz, p_end timestamptz
    ) RETURNS TEXT AS $$
        SELECT CASE
            WHEN p_revoked IS NOT NULL THEN 'cancelled'
            WHEN p_start > now()       THEN 'pending'
            WHEN p_end  <= now()       THEN 'expired'
            ELSE 'active'
        END;
    $$ LANGUAGE sql STABLE;

    CREATE OR REPLACE FUNCTION fn_notify_suppression_sync()
    RETURNS trigger AS $$
    BEGIN
        IF TG_OP = 'DELETE' THEN
            PERFORM pg_notify('gop_sync', jsonb_build_object(
                'cmd', 'SYNC_EVENT_SUPPRESSION',
                'action', 'DELETED',
                'resource_id', OLD.id
            )::text);
        ELSE
            PERFORM pg_notify('gop_sync', jsonb_build_object(
                'cmd', 'SYNC_EVENT_SUPPRESSION',
                'action', CASE WHEN TG_OP = 'INSERT' THEN 'CREATED' ELSE 'UPDATED' END,
                'resource_id', NEW.id,
                'status', fn_suppression_status(NEW.revoked_at, NEW.window_start, NEW.window_end)
            )::text);
        END IF;
        RETURN NULL;
    EXCEPTION WHEN OTHERS THEN
        RETURN NULL;
    END;
    $$ LANGUAGE plpgsql;

    CREATE OR REPLACE FUNCTION fn_notify_suppression_target_stmt()
    RETURNS trigger AS $$
    DECLARE
        r RECORD;
    BEGIN
        FOR r IN
            SELECT s.id AS sid,
                   fn_suppression_status(s.revoked_at, s.window_start, s.window_end) AS st
            FROM (
                SELECT schedule_id FROM changed_rows
            ) c
            JOIN event_suppression_schedules s ON s.id = c.schedule_id
            -- 부모가 같은 트랜잭션에서 쓰였으면(생성/스칼라 PATCH) 부모 트리거가 담당 → skip.
            -- 하드삭제는 relationship passive_deletes=True 로 **부모 DELETE 가 먼저** 실행되므로,
            -- 뒤이은 FK CASCADE 시점에는 이 JOIN 이 부모를 못 찾아(같은 트랜잭션에서 이미 삭제됨)
            -- 0행 → 발행 없음. 즉 JOIN 자체가 삭제 가드다.
            WHERE age(s.xmin) <> 0
            GROUP BY s.id, s.revoked_at, s.window_start, s.window_end
        LOOP
            PERFORM pg_notify('gop_sync', jsonb_build_object(
                'cmd', 'SYNC_EVENT_SUPPRESSION',
                'action', 'UPDATED',
                'resource_id', r.sid,
                'status', r.st
            )::text);
        END LOOP;
        RETURN NULL;
    EXCEPTION WHEN OTHERS THEN
        RETURN NULL;
    END;
    $$ LANGUAGE plpgsql;

    DROP TRIGGER IF EXISTS trg_notify_suppression_sync ON event_suppression_schedules;
    CREATE TRIGGER trg_notify_suppression_sync
        AFTER INSERT OR UPDATE OR DELETE ON event_suppression_schedules
        FOR EACH ROW EXECUTE FUNCTION fn_notify_suppression_sync();

    DROP TRIGGER IF EXISTS trg_sup_tgt_dev_ins ON event_suppression_target_devices;
    DROP TRIGGER IF EXISTS trg_sup_tgt_dev_del ON event_suppression_target_devices;
    DROP TRIGGER IF EXISTS trg_sup_tgt_grp_ins ON event_suppression_target_groups;
    DROP TRIGGER IF EXISTS trg_sup_tgt_grp_del ON event_suppression_target_groups;

    CREATE TRIGGER trg_sup_tgt_dev_ins
        AFTER INSERT ON event_suppression_target_devices
        REFERENCING NEW TABLE AS changed_rows
        FOR EACH STATEMENT EXECUTE FUNCTION fn_notify_suppression_target_stmt();

    CREATE TRIGGER trg_sup_tgt_dev_del
        AFTER DELETE ON event_suppression_target_devices
        REFERENCING OLD TABLE AS changed_rows
        FOR EACH STATEMENT EXECUTE FUNCTION fn_notify_suppression_target_stmt();

    CREATE TRIGGER trg_sup_tgt_grp_ins
        AFTER INSERT ON event_suppression_target_groups
        REFERENCING NEW TABLE AS changed_rows
        FOR EACH STATEMENT EXECUTE FUNCTION fn_notify_suppression_target_stmt();

    CREATE TRIGGER trg_sup_tgt_grp_del
        AFTER DELETE ON event_suppression_target_groups
        REFERENCING OLD TABLE AS changed_rows
        FOR EACH STATEMENT EXECUTE FUNCTION fn_notify_suppression_target_stmt();
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
