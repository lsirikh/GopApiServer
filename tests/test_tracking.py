"""
Tracking History API tests
PRD: PRD_Tracking_History_API.md v1.0

대상: GET /api/tracking/points (keyset cursor), /sessions (파생 집계), /health
"""
from datetime import datetime

from app.models.tracking import TrackPoint


# ============================================================
# Helper
# ============================================================

def _seed(db, **kw):
    """track_points 1행 시드. observed_at 은 naive(=KST 벽시계로 해석)."""
    defaults = dict(
        camera_id=201,
        track_id="cam201-1",
        label="person",
        threat_level="THREAT",
        latitude=38.1235,
        longitude=127.5680,
        distance_m=120.5,
        confidence=0.92,
        observed_at=datetime(2026, 2, 5, 19, 30, 0),
        tracking_state="active",
    )
    defaults.update(kw)
    row = TrackPoint(**defaults)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


# ============================================================
# GET /api/tracking/points
# ============================================================

class TestTrackPointsEndpoint:

    def test_should_return_empty_when_no_points(self, client):
        resp = client.get("/api/tracking/points")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"] == []
        assert body["cursor"]["has_more"] is False
        assert body["cursor"]["next_cursor"] is None

    def test_should_filter_by_camera_id_and_track_id_when_given(self, client, test_db):
        _seed(test_db, camera_id=201, track_id="a", observed_at=datetime(2026, 2, 5, 19, 30, 0))
        _seed(test_db, camera_id=202, track_id="b", observed_at=datetime(2026, 2, 5, 19, 31, 0))

        by_cam = client.get("/api/tracking/points", params={"camera_id": 201}).json()["data"]
        assert len(by_cam) == 1 and by_cam[0]["camera_id"] == 201

        by_track = client.get("/api/tracking/points", params={"track_id": "b"}).json()["data"]
        assert len(by_track) == 1 and by_track[0]["track_id"] == "b"

    def test_should_filter_by_from_to_when_range_given(self, client, test_db):
        _seed(test_db, track_id="early", observed_at=datetime(2026, 2, 5, 10, 0, 0))
        _seed(test_db, track_id="mid", observed_at=datetime(2026, 2, 5, 12, 0, 0))
        _seed(test_db, track_id="late", observed_at=datetime(2026, 2, 5, 14, 0, 0))

        data = client.get(
            "/api/tracking/points",
            params={"from": "2026-02-05T11:00:00", "to": "2026-02-05T13:00:00"},
        ).json()["data"]
        assert [d["track_id"] for d in data] == ["mid"]

    def test_should_order_by_observed_at_asc(self, client, test_db):
        _seed(test_db, track_id="late", observed_at=datetime(2026, 2, 5, 14, 0, 0))
        _seed(test_db, track_id="early", observed_at=datetime(2026, 2, 5, 10, 0, 0))

        data = client.get("/api/tracking/points").json()["data"]
        assert [d["track_id"] for d in data] == ["early", "late"]

    def test_should_paginate_by_keyset_cursor_when_limit_exceeded(self, client, test_db):
        for i in range(5):
            _seed(test_db, track_id=f"t{i}", observed_at=datetime(2026, 2, 5, 10, 0, i))

        page1 = client.get("/api/tracking/points", params={"limit": 2}).json()
        assert len(page1["data"]) == 2
        assert page1["cursor"]["has_more"] is True
        cur1 = page1["cursor"]["next_cursor"]
        assert cur1

        page2 = client.get("/api/tracking/points", params={"limit": 2, "cursor": cur1}).json()
        assert len(page2["data"]) == 2
        ids1 = {d["id"] for d in page1["data"]}
        ids2 = {d["id"] for d in page2["data"]}
        assert ids1.isdisjoint(ids2)  # 중복 0

        page3 = client.get(
            "/api/tracking/points", params={"limit": 2, "cursor": page2["cursor"]["next_cursor"]}
        ).json()
        assert len(page3["data"]) == 1
        assert page3["cursor"]["has_more"] is False
        assert page3["cursor"]["next_cursor"] is None

    def test_should_return_400_when_cursor_is_invalid(self, client, test_db):
        _seed(test_db)
        resp = client.get("/api/tracking/points", params={"cursor": "!!!not-a-cursor!!!"})
        assert resp.status_code == 400

    def test_should_serialize_kst_and_all_fields_when_row_present(self, client, test_db):
        _seed(test_db, track_id="x", threat_level="CAUTION", observed_at=datetime(2026, 2, 5, 19, 30, 0))
        d = client.get("/api/tracking/points").json()["data"][0]
        assert d["threat_level"] == "CAUTION"
        assert d["label"] == "person"
        assert d["latitude"] == 38.1235
        assert d["observed_at"].endswith("+09:00")


# ============================================================
# GET /api/tracking/sessions
# ============================================================

class TestTrackSessionsEndpoint:

    def test_should_return_empty_sessions_when_no_points(self, client):
        resp = client.get("/api/tracking/sessions")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_should_group_one_session_per_track_with_start_end_count(self, client, test_db):
        _seed(test_db, camera_id=201, track_id="s1", observed_at=datetime(2026, 2, 5, 19, 30, 0))
        _seed(test_db, camera_id=201, track_id="s1", observed_at=datetime(2026, 2, 5, 19, 34, 11))
        _seed(test_db, camera_id=201, track_id="s2", observed_at=datetime(2026, 2, 5, 20, 0, 0))

        data = client.get("/api/tracking/sessions").json()["data"]
        assert len(data) == 2
        s1 = next(s for s in data if s["track_id"] == "s1")
        assert s1["point_count"] == 2
        assert s1["start_at"].startswith("2026-02-05T19:30")
        assert s1["end_at"].startswith("2026-02-05T19:34")

    def test_should_filter_sessions_by_camera_and_range(self, client, test_db):
        _seed(test_db, camera_id=201, track_id="s1", observed_at=datetime(2026, 2, 5, 19, 30, 0))
        _seed(test_db, camera_id=202, track_id="s2", observed_at=datetime(2026, 2, 5, 19, 30, 0))

        data = client.get("/api/tracking/sessions", params={"camera_id": 202}).json()["data"]
        assert len(data) == 1 and data[0]["camera_id"] == 202


# ============================================================
# GET /api/tracking/health
# ============================================================

class TestTrackingHealth:

    def test_should_return_ok_with_count_when_table_ready(self, client, test_db):
        _seed(test_db, track_id="h1", observed_at=datetime(2026, 2, 5, 19, 30, 0))
        resp = client.get("/api/tracking/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["tracking_count"] >= 1
