"""
gis_ingest 워커 — 순수 파싱 함수 단위 테스트 (NATS/DB 불요)
PRD: PRD_Tracking_History_API.md §7 / Phase 6

parse_tracking_status(envelope) → track_points 행 dict 리스트
"""
from datetime import datetime

from gis_ingest.main import parse_tracking_status, _parse_observed_at


def _envelope(targets, tracking="active", camera_id=201,
              created="2026-02-05T10:30:00.000Z"):
    return {
        "cmd": "TRACKING_STATUS", "from": "AiAnalysis", "created": created,
        "body": {"camera_id": camera_id, "tracking": tracking,
                 "ttl_sec": 5, "targets": targets},
    }


class TestParseTrackingStatus:

    def test_should_extract_rows_from_active_targets_message(self):
        env = _envelope([
            {"track_id": "t1", "label": "person", "threat_level": "THREAT",
             "confidence": 0.9, "observed_at": "2026-02-05T10:30:00.000Z",
             "location": {"latitude": 38.1, "longitude": 127.5, "distance_m": 120.5}},
            {"track_id": "t2", "label": "car", "threat_level": "CAUTION",
             "confidence": 0.8, "observed_at": "2026-02-05T10:30:00.000Z",
             "location": {"latitude": 38.2, "longitude": 127.6}},
        ])
        rows = parse_tracking_status(env)
        assert len(rows) == 2
        assert rows[0]["track_id"] == "t1" and rows[0]["camera_id"] == 201
        assert rows[0]["threat_level"] == "THREAT"
        assert rows[0]["distance_m"] == 120.5
        assert rows[0]["tracking_state"] == "active"
        assert rows[1]["distance_m"] is None
        # observed_at UTC 10:30 → naive KST 19:30
        assert rows[0]["observed_at"] == datetime(2026, 2, 5, 19, 30, 0)

    def test_should_skip_when_tracking_is_lost_or_idle(self):
        assert parse_tracking_status(_envelope([], tracking="lost")) == []
        assert parse_tracking_status(
            _envelope([{"track_id": "t", "observed_at": "2026-02-05T10:30:00.000Z",
                        "location": {"latitude": 1, "longitude": 2}}], tracking="idle")
        ) == []

    def test_should_normalize_legacy_single_target_when_no_targets_array(self):
        env = {
            "cmd": "TRACKING_STATUS", "created": "2026-02-05T10:30:00.000Z",
            "body": {
                "camera_id": 201, "tracking": "active",
                "target": {"label": "person", "confidence": 0.92},
                "target_location": {"latitude": 38.1, "longitude": 127.5, "distance_m": 120.5},
            },
        }
        rows = parse_tracking_status(env)
        assert len(rows) == 1
        assert rows[0]["camera_id"] == 201
        assert rows[0]["track_id"] == "201-legacy"
        assert rows[0]["latitude"] == 38.1
        assert rows[0]["observed_at"] == datetime(2026, 2, 5, 19, 30, 0)  # created 기반

    def test_should_skip_targets_missing_required_fields(self):
        env = _envelope([
            {"track_id": "t1", "observed_at": "2026-02-05T10:30:00.000Z",
             "location": {"latitude": 38.1, "longitude": 127.5}},                     # valid
            {"label": "x", "observed_at": "2026-02-05T10:30:00.000Z",
             "location": {"latitude": 1, "longitude": 2}},                            # no track_id
            {"track_id": "t3", "location": {"latitude": 1, "longitude": 2}},          # no observed_at
            {"track_id": "t4", "observed_at": "not-a-date",
             "location": {"latitude": 1, "longitude": 2}},                            # bad observed_at
            {"track_id": "t5", "observed_at": "2026-02-05T10:30:00.000Z",
             "location": {}},                                                         # no lat/lng
        ])
        rows = parse_tracking_status(env)
        assert [r["track_id"] for r in rows] == ["t1"]

    def test_should_return_empty_when_active_but_no_targets(self):
        assert parse_tracking_status(_envelope([])) == []


class TestParseObservedAt:

    def test_should_convert_utc_z_to_naive_kst(self):
        assert _parse_observed_at("2026-02-05T10:30:00.000Z") == datetime(2026, 2, 5, 19, 30, 0)

    def test_should_convert_utc_offset_to_naive_kst(self):
        assert _parse_observed_at("2026-02-05T10:30:00+00:00") == datetime(2026, 2, 5, 19, 30, 0)

    def test_should_assume_utc_when_naive_input(self):
        assert _parse_observed_at("2026-02-05T10:30:00") == datetime(2026, 2, 5, 19, 30, 0)
