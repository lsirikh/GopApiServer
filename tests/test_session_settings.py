"""
Session_Settings (P2) tests.
PRD: docs/prds/PRD_GOP_Server_Session_Settings.md (FR-SVS-01~06, NFR-SVS-01~05)
"""
import pytest

from app.models.app_settings import AppSettings
from app.services import settings_service
from app.services.settings_service import SettingKey


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    settings_service.invalidate_cache()
    yield
    settings_service.invalidate_cache()


class TestAppSettingsModel:
    def test_persists_key_value_type(self, test_db):
        test_db.add(AppSettings(setting_key="k", setting_value="24", value_type="int"))
        test_db.commit()
        got = test_db.query(AppSettings).filter(AppSettings.setting_key == "k").first()
        assert got.setting_value == "24" and got.value_type == "int"


class TestSettingsService:
    def test_seed_then_get_returns_typed_defaults(self, test_db):
        settings_service.seed_if_empty(test_db)
        assert settings_service.get(test_db, SettingKey.LOCKOUT_THRESHOLD) == 5
        assert settings_service.get(test_db, SettingKey.SESSION_ENABLED) is True

    def test_put_updates_value_and_invalidates_cache(self, test_db):
        settings_service.seed_if_empty(test_db)
        assert settings_service.get(test_db, SettingKey.LOCKOUT_THRESHOLD) == 5  # warm the cache
        settings_service.put(test_db, SettingKey.LOCKOUT_THRESHOLD, 10)
        assert settings_service.get(test_db, SettingKey.LOCKOUT_THRESHOLD) == 10  # cache invalidated → DB


class TestSessionSettingsApi:
    def test_get_returns_editable_and_readonly_without_secret(self, client, test_db):
        resp = client.get("/api/settings/session")
        assert resp.status_code == 200, resp.text
        data = resp.json()["data"]
        for k in ("session_timeout_hours", "refresh_expiration_days", "lockout_threshold",
                  "session_enabled", "auth_mode", "jwt_algorithm"):
            assert k in data, f"missing {k}"
        # NFR-SVS-03: secret never exposed
        assert "jwt_secret" not in data
        assert "secret" not in str(data).lower()

    def test_put_updates_editable_subset(self, client, test_db):
        resp = client.put("/api/settings/session", json={"lockout_threshold": 7})
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["lockout_threshold"] == 7

    def test_put_rejects_lockout_in_forbidden_band(self, client, test_db):
        # NFR-SVS-04: lockout_threshold 1~2 무의미 구간 → 422
        assert client.put("/api/settings/session", json={"lockout_threshold": 2}).status_code == 422

    def test_put_rejects_out_of_bounds(self, client, test_db):
        assert client.put("/api/settings/session", json={"session_timeout_hours": 999}).status_code == 422

    def test_put_records_config_change_log(self, client, test_db):
        from app.models.config_change_log import ConfigChangeLog
        from app.utils.enums import EnumConfigResourceType

        client.put("/api/settings/session", json={"session_enabled": False})
        log = test_db.query(ConfigChangeLog).filter(
            ConfigChangeLog.resource_type == EnumConfigResourceType.SETTINGS
        ).order_by(ConfigChangeLog.id.desc()).first()
        assert log is not None
        assert "session_enabled" in (log.after_state or {})
        assert log.before_state.get("session_enabled") is True
        assert log.after_state.get("session_enabled") is False


class TestRuntimeSettingsApplied:
    """FR-SVS-05: 토큰 만료·잠금 임계가 startup 상수가 아닌 settings_service 값을 사용."""

    def _make_user(self, test_db, login_id, password="right"):
        from app.models.user import AccountUser
        from app.utils.auth import hash_password
        u = AccountUser(login_id=login_id, password_hash=hash_password(password),
                        name="RT", role="VIEWER", is_active=True)
        test_db.add(u); test_db.commit()
        return u

    def test_token_expiry_reflects_runtime_setting(self, client, test_db):
        from datetime import datetime, timezone
        from jose import jwt
        from app.config import settings as cfg

        client.put("/api/settings/session", json={"session_timeout_hours": 1})
        self._make_user(test_db, "exp_user")
        resp = client.post("/api/auth/login", json={"login_id": "exp_user", "password": "right"})
        assert resp.status_code == 200, resp.text
        token = resp.json()["data"]["access_token"]

        payload = jwt.decode(token, cfg.JWT_SECRET_KEY, algorithms=[cfg.JWT_ALGORITHM])
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        delta_hours = (exp - datetime.now(timezone.utc)).total_seconds() / 3600
        assert 0.5 < delta_hours < 1.5, f"expected ~1h expiry, got {delta_hours:.2f}h"

    def test_lockout_uses_runtime_threshold(self, client, test_db):
        from app.models.user import AccountUser

        client.put("/api/settings/session", json={"lockout_threshold": 3})
        self._make_user(test_db, "lock_user")
        for _ in range(3):
            client.post("/api/auth/login", json={"login_id": "lock_user", "password": "wrong"})

        test_db.expire_all()
        u = test_db.query(AccountUser).filter(AccountUser.login_id == "lock_user").first()
        assert u.is_locked is True, "account must lock at the runtime threshold (3)"

    def test_lockout_disabled_when_threshold_zero(self, client, test_db):
        from app.models.user import AccountUser

        client.put("/api/settings/session", json={"lockout_threshold": 0})
        self._make_user(test_db, "nolock_user")
        for _ in range(6):
            client.post("/api/auth/login", json={"login_id": "nolock_user", "password": "wrong"})

        test_db.expire_all()
        u = test_db.query(AccountUser).filter(AccountUser.login_id == "nolock_user").first()
        assert u.is_locked is False, "threshold 0 must disable lockout"
