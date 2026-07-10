"""
TDD tests for app/db_triggers.py
PRD: PRD_DB_Change_Monitor.md Phase 2.1
"""
import pytest


# Tables that must have triggers
# Note: device sub-types (sensors, cameras, etc.) use the devices base table trigger
# to correctly handle SQLAlchemy Joined Table Inheritance PATCH behavior
EXPECTED_TABLES = [
    "devices",
    "servers", "server_categories", "device_groups", "event_mappings",
    "camera_presets", "file_groups", "camera_settings", "proxy_settings",
    # PRD_SYNC_Child_Table_Triggers v1.0: 하위 테이블
    "event_mapping_cameras", "event_mapping_speakers", "event_mapping_lamps",
    "device_group_mappings", "rois",
]

# SYNC commands that must appear in trigger SQL
EXPECTED_SYNC_CMDS = [
    "SYNC_DEVICE",
    "SYNC_SERVER",
    "SYNC_CATEGORY",
    "SYNC_DEVICE_GROUP",
    "SYNC_EVENT_MAPPING",
    "SYNC_PRESET",
    "SYNC_FILE_GROUP",
    "SYNC_CAMERA_SETTING",
    "SYNC_PROXY_SETTING",
]


def test_module_has_apply_triggers_function():
    from app.db_triggers import apply_triggers
    assert callable(apply_triggers)


def test_get_notify_function_sql_contains_plpgsql():
    from app.db_triggers import GET_NOTIFY_FUNCTION_SQL
    assert "plpgsql" in GET_NOTIFY_FUNCTION_SQL.lower()
    assert "pg_notify" in GET_NOTIFY_FUNCTION_SQL
    assert "gop_sync" in GET_NOTIFY_FUNCTION_SQL


def test_trigger_sqls_cover_all_tables():
    from app.db_triggers import GET_TRIGGER_SQLS
    combined = " ".join(GET_TRIGGER_SQLS).lower()
    for table in EXPECTED_TABLES:
        assert table in combined, f"Missing trigger SQL for table: {table}"


def test_trigger_sqls_cover_all_sync_cmds():
    from app.db_triggers import GET_NOTIFY_FUNCTION_SQL
    for cmd in EXPECTED_SYNC_CMDS:
        assert cmd in GET_NOTIFY_FUNCTION_SQL, f"Missing SYNC cmd in function SQL: {cmd}"


def test_notify_function_uses_lower_for_category_comparison():
    from app.db_triggers import GET_NOTIFY_FUNCTION_SQL
    # category_device enum is stored UPPERCASE (e.g. 'SENSOR') — must use LOWER() to compare
    assert "LOWER(category)" in GET_NOTIFY_FUNCTION_SQL


@pytest.mark.skip(reason="v4.4 FR-8: row-level ELSIF branch removed (statement-level triggers used instead)")
def test_child_table_event_mapping_cameras_in_notify_function():
    """1.1 fn_notify_gop_sync에 event_mapping 하위 테이블 분기 포함"""
    from app.db_triggers import GET_NOTIFY_FUNCTION_SQL
    # v4.4 FR-8: row-level 분기 제거됨 (statement-level 트리거로 대체) — skip 마크 적용
    assert "event_mapping_cameras" not in GET_NOTIFY_FUNCTION_SQL
    assert "event_mapping_speakers" not in GET_NOTIFY_FUNCTION_SQL
    assert "event_mapping_lamps" not in GET_NOTIFY_FUNCTION_SQL


def test_child_table_device_group_mappings_in_notify_function():
    """1.2 fn_notify_gop_sync에 device_group_mappings 분기 포함"""
    from app.db_triggers import GET_NOTIFY_FUNCTION_SQL
    assert "device_group_mappings" in GET_NOTIFY_FUNCTION_SQL


def test_child_table_rois_in_notify_function():
    """1.3 fn_notify_gop_sync에 rois 분기 포함"""
    from app.db_triggers import GET_NOTIFY_FUNCTION_SQL
    # rois 테이블이 SYNC_PRESET을 발행하는 분기
    assert "'rois'" in GET_NOTIFY_FUNCTION_SQL or "rois" in GET_NOTIFY_FUNCTION_SQL


@pytest.mark.skip(reason="v4.4 FR-8: row-level ELSIF branch removed (statement-level triggers used instead)")
def test_child_tables_use_parent_fk_as_resource_id():
    """하위 테이블이 부모 FK를 resource_id로 사용하는지 확인"""
    from app.db_triggers import GET_NOTIFY_FUNCTION_SQL
    # event_mapping 하위: event_mapping_id를 resource_id로 (v4.4 FR-8 — statement-level로 이동, skip)
    # device_group_mappings: group_id를 resource_id로
    assert "group_id" in GET_NOTIFY_FUNCTION_SQL
    # rois: preset_id를 resource_id로
    assert "preset_id" in GET_NOTIFY_FUNCTION_SQL


def test_apply_triggers_skips_sqlite():
    from unittest.mock import MagicMock
    from app.db_triggers import apply_triggers

    mock_engine = MagicMock()
    mock_engine.dialect.name = "sqlite"

    apply_triggers(mock_engine)

    mock_engine.connect.assert_not_called()


# =============================================================================
# PRD_DeviceGroup_BulkUnassign §5.3 — statement-level trigger for device_group_mappings
# =============================================================================

class TestDeviceGroupMappingsStatementLevelTrigger:
    """device_group_mappings 트리거가 row-level → statement-level로 교체되었는지 검증."""

    def test_should_define_statement_level_function_fn_notify_dgm_stmt(self):
        from app.db_triggers import GET_TRIGGER_SQLS
        joined = "\n".join(GET_TRIGGER_SQLS)
        assert "fn_notify_dgm_stmt" in joined
        assert "FOR EACH STATEMENT" in joined

    def test_should_use_referencing_new_and_old_table(self):
        from app.db_triggers import GET_TRIGGER_SQLS
        joined = "\n".join(GET_TRIGGER_SQLS)
        assert "REFERENCING NEW TABLE AS new_rows" in joined
        assert "REFERENCING OLD TABLE AS old_rows" in joined

    def test_should_loop_distinct_group_id_for_dedup(self):
        from app.db_triggers import GET_TRIGGER_SQLS
        joined = "\n".join(GET_TRIGGER_SQLS)
        # 같은 statement 내 N rows → DISTINCT group_id 만큼만 notify
        assert "SELECT DISTINCT group_id FROM new_rows" in joined
        assert "SELECT DISTINCT group_id FROM old_rows" in joined

    def test_should_drop_old_row_level_trigger(self):
        from app.db_triggers import GET_TRIGGER_SQLS
        joined = "\n".join(GET_TRIGGER_SQLS)
        # 옛 row-level 트리거명 DROP (멱등 배포)
        assert "DROP TRIGGER IF EXISTS trg_sync_device_group_mappings" in joined

    def test_should_create_three_statement_level_triggers(self):
        from app.db_triggers import GET_TRIGGER_SQLS
        joined = "\n".join(GET_TRIGGER_SQLS)
        # INSERT/DELETE/UPDATE 세 개의 statement-level 트리거
        assert "trg_sync_dgm_ins" in joined
        assert "trg_sync_dgm_del" in joined
        assert "trg_sync_dgm_upd" in joined

    def test_should_publish_sync_device_group_cmd(self):
        from app.db_triggers import GET_TRIGGER_SQLS
        joined = "\n".join(GET_TRIGGER_SQLS)
        assert "'SYNC_DEVICE_GROUP'" in joined
