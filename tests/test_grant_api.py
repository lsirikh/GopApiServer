"""
부여 관리 API 테스트 — FR-03
PRD: PRD_Permission_Group_Scheduling.md §3.4
WS-B / TDD Phase 3
"""
from datetime import datetime, timedelta

from app.config import settings


def _kst_iso(hours_from_now: float) -> str:
    base = datetime.now(settings.tz) + timedelta(hours=hours_from_now)
    return base.isoformat()


def _make_user(test_db, login_id="grant_target"):
    from app.models.user import AccountUser
    from app.utils.auth import hash_password
    u = AccountUser(login_id=login_id, password_hash=hash_password("pw123456"),
                    name="대상", role="VIEWER")
    test_db.add(u)
    test_db.commit()
    test_db.refresh(u)
    return u


def _make_group(test_db, name="임시정비"):
    from app.models.user import UserGroup
    g = UserGroup(name=name, permissions={"modules": {"cameras": {"control": True}}})
    test_db.add(g)
    test_db.commit()
    test_db.refresh(g)
    return g


class TestGrantApi:
    def test_should_create_grant_when_admin(self, client, test_db):
        user = _make_user(test_db)
        group = _make_group(test_db)

        resp = client.post(f"/api/users/{user.id}/grants", json={
            "group_id": group.id,
            "valid_from": _kst_iso(-1),
            "valid_until": _kst_iso(25),
        })

        assert resp.status_code == 201, resp.text
        data = resp.json()["data"]
        assert data["user_id"] == user.id
        assert data["group_id"] == group.id
        assert data["group_name"] == group.name
        assert data["status"] == "ACTIVE"

    def test_should_create_permanent_grant_when_valid_until_omitted(self, client, test_db):
        user = _make_user(test_db, "grant_perm")
        group = _make_group(test_db, "유지보수")

        resp = client.post(f"/api/users/{user.id}/grants", json={
            "group_id": group.id, "valid_from": _kst_iso(-1),
        })
        assert resp.status_code == 201, resp.text
        assert resp.json()["data"]["valid_until"] is None
        assert resp.json()["data"]["status"] == "ACTIVE"

    def test_should_404_when_user_missing(self, client, test_db):
        group = _make_group(test_db, "g404")
        resp = client.post("/api/users/999999/grants", json={
            "group_id": group.id, "valid_from": _kst_iso(-1),
        })
        assert resp.status_code == 404

    def test_should_422_when_valid_until_before_valid_from(self, client, test_db):
        user = _make_user(test_db, "grant_bad1")
        group = _make_group(test_db, "gbad1")
        resp = client.post(f"/api/users/{user.id}/grants", json={
            "group_id": group.id, "valid_from": _kst_iso(5), "valid_until": _kst_iso(2),
        })
        assert resp.status_code == 422

    def test_should_422_when_valid_until_in_past(self, client, test_db):
        user = _make_user(test_db, "grant_bad2")
        group = _make_group(test_db, "gbad2")
        resp = client.post(f"/api/users/{user.id}/grants", json={
            "group_id": group.id, "valid_from": _kst_iso(-5), "valid_until": _kst_iso(-1),
        })
        assert resp.status_code == 422

    def test_should_list_grants_with_status(self, client, test_db):
        user = _make_user(test_db, "grant_list")
        group = _make_group(test_db, "glist")
        client.post(f"/api/users/{user.id}/grants", json={
            "group_id": group.id, "valid_from": _kst_iso(2), "valid_until": _kst_iso(10),
        })
        resp = client.get(f"/api/users/{user.id}/grants")
        assert resp.status_code == 200
        items = resp.json()["data"]
        assert len(items) == 1
        assert items[0]["status"] == "PENDING"  # valid_from 미래

    def test_should_soft_revoke_when_delete(self, client, test_db):
        from app.models.user import UserGroupGrant
        user = _make_user(test_db, "grant_revoke")
        group = _make_group(test_db, "grevoke")
        created = client.post(f"/api/users/{user.id}/grants", json={
            "group_id": group.id, "valid_from": _kst_iso(-1), "valid_until": _kst_iso(10),
        }).json()["data"]

        resp = client.delete(f"/api/grants/{created['id']}")
        assert resp.status_code == 200

        g = test_db.get(UserGroupGrant, created["id"])
        assert g.revoked_at is not None      # soft (물리삭제 아님)
        assert g.is_active is False

    def test_should_404_when_revoke_missing_grant(self, client, test_db):
        resp = client.delete("/api/grants/888888")
        assert resp.status_code == 404
