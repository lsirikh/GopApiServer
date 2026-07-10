"""
Thumbnail Image API Tests — PRD v1.1

TDD tests for thumbnail upload, storage, retrieval, and deletion.
- client-specified file_name (no camera_id, no event_id)
- file_name UNIQUE constraint
- GET /images/{file_name} endpoint for HTTP URL-based image serving
"""
import pytest
import os
from datetime import datetime
from io import BytesIO
from PIL import Image
from app.config import settings


def _create_test_image(width=100, height=80, fmt="JPEG"):
    """Helper: create a valid image binary in memory"""
    img = Image.new("RGB", (width, height), color=(255, 0, 0))
    buf = BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    return buf.read()


# ===== Phase 1: Configuration =====

def test_settings_has_thumbnail_storage_path():
    """Settings should have THUMBNAIL_STORAGE_PATH with default 'data/thumbnails'"""
    assert hasattr(settings, "THUMBNAIL_STORAGE_PATH")
    assert settings.THUMBNAIL_STORAGE_PATH == "data/thumbnails"


# ===== Phase 2: Model =====

def test_thumbnail_model_create_and_persist(test_db):
    """Should create and persist a Thumbnail record with all fields"""
    from app.models.thumbnail import Thumbnail

    thumbnail = Thumbnail(
        file_path="data/thumbnails/2026-02-19/CAM-001_2026-02-19_14-30-25-123.jpg",
        file_name="CAM-001_2026-02-19_14-30-25-123.jpg",
        file_size=245760,
        mime_type="image/jpeg",
    )
    test_db.add(thumbnail)
    test_db.commit()
    test_db.refresh(thumbnail)

    assert thumbnail.id is not None
    assert thumbnail.file_size == 245760
    assert thumbnail.mime_type == "image/jpeg"
    assert thumbnail.width is None
    assert thumbnail.height is None
    assert thumbnail.created_at is not None


def test_thumbnail_file_name_unique(test_db):
    """file_name should have UNIQUE constraint"""
    from app.models.thumbnail import Thumbnail
    from sqlalchemy.exc import IntegrityError

    t1 = Thumbnail(
        file_path="data/thumbnails/2026-02-19/test.jpg",
        file_name="duplicate.jpg",
        file_size=1024,
        mime_type="image/jpeg",
    )
    test_db.add(t1)
    test_db.commit()

    t2 = Thumbnail(
        file_path="data/thumbnails/2026-02-19/test2.jpg",
        file_name="duplicate.jpg",
        file_size=2048,
        mime_type="image/jpeg",
    )
    test_db.add(t2)
    with pytest.raises(IntegrityError):
        test_db.commit()
    test_db.rollback()


# ===== Phase 3: Schema =====

def test_thumbnail_response_schema_serialization():
    """ThumbnailResponse should serialize with computed image_url using file_name"""
    from app.schemas.thumbnail import ThumbnailResponse

    response = ThumbnailResponse(
        id=1,
        file_path="data/thumbnails/2026-02-19/CAM-001_2026-02-19_14-30-25-123.jpg",
        file_name="CAM-001_2026-02-19_14-30-25-123.jpg",
        file_size=245760,
        mime_type="image/jpeg",
        width=None,
        height=None,
        created_at=datetime(2026, 2, 19, 14, 30, 25),
    )

    assert response.id == 1
    assert response.image_url == "/api/thumbnails/images/CAM-001_2026-02-19_14-30-25-123.jpg"
    assert response.mime_type == "image/jpeg"

    data = response.model_dump()
    assert "image_url" in data
    assert data["image_url"] == "/api/thumbnails/images/CAM-001_2026-02-19_14-30-25-123.jpg"


# ===== Fixtures =====

@pytest.fixture
def thumbnail_client(client, tmp_path, monkeypatch):
    """Client with thumbnail storage path set to tmp_path"""
    monkeypatch.setattr(settings, "THUMBNAIL_STORAGE_PATH", str(tmp_path / "thumbnails"))
    return client


def _upload_thumbnail(thumbnail_client, file_name="CAM-001_2026-02-19_14-30-25-123.jpg"):
    """Helper: upload a thumbnail with a valid image and return the response"""
    image_bytes = _create_test_image(100, 80)
    return thumbnail_client.post(
        "/api/thumbnails",
        files={"file": ("test.jpg", image_bytes, "image/jpeg")},
        data={"file_name": file_name},
    )


# ===== Phase 4: Upload POST =====

def test_upload_thumbnail_success(thumbnail_client):
    """POST /api/thumbnails with file + file_name should return 201 with width/height"""
    response = _upload_thumbnail(thumbnail_client)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["file_name"] == "CAM-001_2026-02-19_14-30-25-123.jpg"
    assert data["data"]["mime_type"] == "image/jpeg"
    assert data["data"]["file_size"] > 0
    assert data["data"]["width"] == 100
    assert data["data"]["height"] == 80
    assert data["data"]["image_url"] == "/api/thumbnails/images/CAM-001_2026-02-19_14-30-25-123.jpg"


def test_upload_thumbnail_creates_file_on_disk(thumbnail_client):
    """After upload, the file should exist on disk"""
    response = _upload_thumbnail(thumbnail_client)
    file_path = response.json()["data"]["file_path"]
    assert os.path.exists(file_path)


def test_upload_thumbnail_uses_client_file_name(thumbnail_client):
    """Server should use the client-specified file_name, not generate its own"""
    response = _upload_thumbnail(thumbnail_client, file_name="MY-CUSTOM-NAME_2026-02-19_10-00-00-456.png")
    data = response.json()["data"]
    assert data["file_name"] == "MY-CUSTOM-NAME_2026-02-19_10-00-00-456.png"
    assert data["file_path"].endswith("MY-CUSTOM-NAME_2026-02-19_10-00-00-456.png")


def test_upload_thumbnail_duplicate_file_name(thumbnail_client):
    """POST with duplicate file_name should return 409"""
    _upload_thumbnail(thumbnail_client, file_name="duplicate-test.jpg")
    response = _upload_thumbnail(thumbnail_client, file_name="duplicate-test.jpg")
    assert response.status_code == 409


def test_upload_thumbnail_missing_file_name(thumbnail_client):
    """POST without file_name should return 422"""
    image_bytes = _create_test_image()
    response = thumbnail_client.post(
        "/api/thumbnails",
        files={"file": ("test.jpg", image_bytes, "image/jpeg")},
    )
    assert response.status_code == 422


def test_upload_thumbnail_invalid_mime_type(thumbnail_client):
    """POST with non-image file should return 400"""
    response = thumbnail_client.post(
        "/api/thumbnails",
        files={"file": ("test.txt", b"hello world", "text/plain")},
        data={"file_name": "test.txt"},
    )
    assert response.status_code == 400


def test_upload_thumbnail_file_path_has_date_directory(thumbnail_client):
    """File path should contain date directory: {storage}/{YYYY-MM-DD}/{file_name}"""
    response = _upload_thumbnail(thumbnail_client, file_name="CAM-TEST_2026-02-19_14-30-25-000.jpg")
    file_path = response.json()["data"]["file_path"]
    # Should have a date directory component
    parts = file_path.replace("\\", "/").split("/")
    # Find the date-like part
    date_parts = [p for p in parts if len(p) == 10 and p.count("-") == 2]
    assert len(date_parts) >= 1


# ===== Phase 5: Image GET /{id}/image (ID-based) =====

def test_get_thumbnail_image_by_id_success(thumbnail_client):
    """GET /{id}/image should return image binary with image content-type"""
    upload = _upload_thumbnail(thumbnail_client)
    thumbnail_id = upload.json()["data"]["id"]

    response = thumbnail_client.get(f"/api/thumbnails/{thumbnail_id}/image")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/")


def test_get_thumbnail_image_by_id_not_found(thumbnail_client):
    """GET /{id}/image with non-existent id should return 404"""
    response = thumbnail_client.get("/api/thumbnails/99999/image")
    assert response.status_code == 404


def test_get_thumbnail_image_by_id_file_missing(thumbnail_client):
    """GET /{id}/image when file is deleted from disk should return 404"""
    upload = _upload_thumbnail(thumbnail_client)
    data = upload.json()["data"]
    os.remove(data["file_path"])

    response = thumbnail_client.get(f"/api/thumbnails/{data['id']}/image")
    assert response.status_code == 404


# ===== Phase 5b: Image GET /images/{file_name} (file_name-based) =====

def test_get_thumbnail_image_by_file_name_success(thumbnail_client):
    """GET /images/{file_name} should return image binary"""
    file_name = "CAM-001_2026-02-19_14-30-25-789.jpg"
    _upload_thumbnail(thumbnail_client, file_name=file_name)

    response = thumbnail_client.get(f"/api/thumbnails/images/{file_name}")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/")


def test_get_thumbnail_image_by_file_name_not_found(thumbnail_client):
    """GET /images/{file_name} with non-existent file_name should return 404"""
    response = thumbnail_client.get("/api/thumbnails/images/nonexistent.jpg")
    assert response.status_code == 404


def test_get_thumbnail_image_by_file_name_file_missing(thumbnail_client):
    """GET /images/{file_name} when file is deleted from disk should return 404"""
    file_name = "CAM-DISK-MISSING_2026-02-19_14-30-25-000.jpg"
    upload = _upload_thumbnail(thumbnail_client, file_name=file_name)
    os.remove(upload.json()["data"]["file_path"])

    response = thumbnail_client.get(f"/api/thumbnails/images/{file_name}")
    assert response.status_code == 404


# ===== Phase 6: Metadata GET /{id} =====

def test_get_thumbnail_metadata_success(thumbnail_client):
    """GET /{id} should return thumbnail metadata"""
    upload = _upload_thumbnail(thumbnail_client)
    thumbnail_id = upload.json()["data"]["id"]

    response = thumbnail_client.get(f"/api/thumbnails/{thumbnail_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == thumbnail_id
    assert "image_url" in data["data"]
    assert data["data"]["image_url"].startswith("/api/thumbnails/images/")


def test_get_thumbnail_metadata_not_found(thumbnail_client):
    """GET /{id} with non-existent id should return 404"""
    response = thumbnail_client.get("/api/thumbnails/99999")
    assert response.status_code == 404


# ===== Phase 7: List GET / =====

def test_list_thumbnails_empty(thumbnail_client):
    """GET /api/thumbnails should return empty list when no thumbnails"""
    response = thumbnail_client.get("/api/thumbnails")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"] == []
    assert data["pagination"] is not None


def test_list_thumbnails_returns_items(thumbnail_client):
    """After uploads, list should return items"""
    _upload_thumbnail(thumbnail_client, file_name="file1.jpg")
    _upload_thumbnail(thumbnail_client, file_name="file2.jpg")

    response = thumbnail_client.get("/api/thumbnails")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2
    assert data["pagination"]["total"] == 2


def test_list_thumbnails_filter_by_date_range(thumbnail_client):
    """GET with date range should filter by created_at"""
    _upload_thumbnail(thumbnail_client)

    # Future date range — should return 0
    response = thumbnail_client.get(
        "/api/thumbnails?start_date=2099-01-01T00:00:00&end_date=2099-12-31T23:59:59"
    )
    assert response.status_code == 200
    assert len(response.json()["data"]) == 0

    # Past-to-future range — should return 1
    response = thumbnail_client.get(
        "/api/thumbnails?start_date=2020-01-01T00:00:00&end_date=2099-12-31T23:59:59"
    )
    assert response.status_code == 200
    assert len(response.json()["data"]) == 1


def test_list_thumbnails_pagination(thumbnail_client):
    """Pagination should limit results correctly"""
    for i in range(5):
        _upload_thumbnail(thumbnail_client, file_name=f"CAM-{i:03d}_2026-02-19_14-30-{i:02d}-000.jpg")

    response = thumbnail_client.get("/api/thumbnails?page=1&limit=2")
    data = response.json()
    assert len(data["data"]) == 2
    assert data["pagination"]["total"] == 5
    assert data["pagination"]["total_pages"] == 3


# ===== Phase 8: Delete DELETE /{id} =====

def test_delete_thumbnail_success(thumbnail_client, test_db):
    """DELETE /{id} should delete DB record"""
    upload = _upload_thumbnail(thumbnail_client)
    thumbnail_id = upload.json()["data"]["id"]

    response = thumbnail_client.delete(f"/api/thumbnails/{thumbnail_id}")
    assert response.status_code == 200
    assert response.json()["success"] is True

    # DB record should be gone
    get_response = thumbnail_client.get(f"/api/thumbnails/{thumbnail_id}")
    assert get_response.status_code == 404


def test_delete_thumbnail_removes_file(thumbnail_client):
    """After DELETE, the file should no longer exist on disk"""
    upload = _upload_thumbnail(thumbnail_client)
    data = upload.json()["data"]
    assert os.path.exists(data["file_path"])

    thumbnail_client.delete(f"/api/thumbnails/{data['id']}")
    assert not os.path.exists(data["file_path"])


def test_delete_thumbnail_not_found(thumbnail_client):
    """DELETE with non-existent id should return 404"""
    response = thumbnail_client.delete("/api/thumbnails/99999")
    assert response.status_code == 404


def test_delete_thumbnail_file_already_missing(thumbnail_client):
    """DELETE should succeed even if file is already deleted from disk"""
    upload = _upload_thumbnail(thumbnail_client)
    data = upload.json()["data"]
    os.remove(data["file_path"])  # Remove file first

    response = thumbnail_client.delete(f"/api/thumbnails/{data['id']}")
    assert response.status_code == 200
    assert response.json()["success"] is True
