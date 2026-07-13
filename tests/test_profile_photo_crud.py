"""프로필 사진 CRUD 정합화 단위 테스트 (v6.3-profile_photo_crud, 2026-07-13).

권장 조치 4건 검증:
- P0: photo_url validator 가 실제 서빙 경로(/api/users/photo/)를 허용 (종전 /static/profiles/ 오류)
- P1-U/D: _delete_photo_file 이 로컬 업로드만 삭제, default/외부/None 은 보존
- P2: _detect_image_ext 이 magic-byte 로 실제 이미지만 통과 (content_type 위조 방어)

async 라우터+Postgres 통합은 별도 라이브 E2E 로 확인. 여기서는 순수 로직/스키마를 격리 검증.
"""
import io

import pytest
from pydantic import ValidationError

from app.schemas.user import AccountUserSelfUpdate
from app.routers.users import _detect_image_ext, _delete_photo_file
from app.utils.default_profile import DEFAULT_PROFILE_FILENAME


# ── P0: photo_url validator 경로 정합 ─────────────────────────────────
class TestSelfUpdatePhotoUrlValidator:
    def test_should_accept_api_photo_path_when_self_update(self):
        m = AccountUserSelfUpdate(photo_url="/api/users/photo/1_abcd1234.jpg")
        assert m.photo_url == "/api/users/photo/1_abcd1234.jpg"

    def test_should_accept_default_photo_url_when_roundtrip(self):
        # 회귀: 서버가 응답에 채우는 default 를 그대로 되받아도 422 가 아니어야 한다(P0 버그).
        m = AccountUserSelfUpdate(photo_url="/api/users/photo/default.png")
        assert m.photo_url == "/api/users/photo/default.png"

    def test_should_accept_absolute_https_url_when_self_update(self):
        url = "https://192.168.0.10:8000/api/users/photo/1_abcd1234.jpg"
        assert AccountUserSelfUpdate(photo_url=url).photo_url == url

    def test_should_accept_none_when_self_update(self):
        assert AccountUserSelfUpdate(photo_url=None).photo_url is None

    def test_should_reject_javascript_scheme_when_self_update(self):
        with pytest.raises(ValidationError):
            AccountUserSelfUpdate(photo_url="javascript:alert(1)")

    def test_should_reject_data_scheme_when_self_update(self):
        with pytest.raises(ValidationError):
            AccountUserSelfUpdate(photo_url="data:text/html,<script>")

    def test_should_reject_unknown_relative_path_when_self_update(self):
        # /static/profiles/ 는 실존하지 않는 경로 → 더 이상 허용하지 않음
        with pytest.raises(ValidationError):
            AccountUserSelfUpdate(photo_url="/static/profiles/x.png")


# ── P2: magic-byte 이미지 검증 ────────────────────────────────────────
def _png_bytes() -> bytes:
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), (10, 20, 30)).save(buf, format="PNG")
    return buf.getvalue()


class TestDetectImageExt:
    def test_should_return_png_when_real_png_bytes(self):
        assert _detect_image_ext(_png_bytes()) == "png"

    def test_should_return_none_when_not_an_image(self):
        # content_type 을 image/png 로 위조해도 바이트가 이미지가 아니면 거부되어야 한다.
        assert _detect_image_ext(b"this is definitely not an image") is None

    def test_should_return_none_when_empty(self):
        assert _detect_image_ext(b"") is None


# ── P1: orphan/삭제 파일 정리 ─────────────────────────────────────────
class TestDeletePhotoFile:
    def test_should_delete_local_file_when_uploaded_url(self, tmp_path, monkeypatch):
        from app.config import settings
        monkeypatch.setattr(settings, "PROFILE_STORAGE_PATH", str(tmp_path))
        f = tmp_path / "1_abcd1234.jpg"
        f.write_bytes(b"x")
        _delete_photo_file("https://host:8000/api/users/photo/1_abcd1234.jpg")
        assert not f.exists()

    def test_should_keep_default_when_photo_url_is_default(self, tmp_path, monkeypatch):
        from app.config import settings
        monkeypatch.setattr(settings, "PROFILE_STORAGE_PATH", str(tmp_path))
        f = tmp_path / DEFAULT_PROFILE_FILENAME
        f.write_bytes(b"x")
        _delete_photo_file(f"/api/users/photo/{DEFAULT_PROFILE_FILENAME}")
        assert f.exists()  # default 는 보존

    def test_should_ignore_external_url_when_deleting(self, tmp_path, monkeypatch):
        from app.config import settings
        monkeypatch.setattr(settings, "PROFILE_STORAGE_PATH", str(tmp_path))
        # 외부 URL 은 로컬 파일과 무관 → 예외 없이 no-op
        _delete_photo_file("https://cdn.example.com/some/photo.jpg")

    def test_should_noop_when_photo_url_is_none(self):
        _delete_photo_file(None)  # 예외 없이 통과
