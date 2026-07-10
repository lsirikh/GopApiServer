"""
Test: Swagger tags_metadata에 모든 라우터 태그가 등록되어 있는지 확인
"""
from app.main import tags_metadata


def test_tags_metadata_contains_detection_logs():
    """Detection Logs 태그가 tags_metadata에 포함되어야 한다"""
    tag_names = [tag["name"] for tag in tags_metadata]
    assert "Detection Logs" in tag_names, "Detection Logs tag missing from tags_metadata"


def test_tags_metadata_contains_mapping_cameras():
    """Mapping Cameras 태그가 tags_metadata에 포함되어야 한다"""
    tag_names = [tag["name"] for tag in tags_metadata]
    assert "Mapping Cameras" in tag_names, "Mapping Cameras tag missing from tags_metadata"


def test_tags_metadata_contains_mapping_speakers():
    """Mapping Speakers 태그가 tags_metadata에 포함되어야 한다"""
    tag_names = [tag["name"] for tag in tags_metadata]
    assert "Mapping Speakers" in tag_names, "Mapping Speakers tag missing from tags_metadata"


def test_tags_metadata_contains_mapping_lamps():
    """Mapping Lamps 태그가 tags_metadata에 포함되어야 한다"""
    tag_names = [tag["name"] for tag in tags_metadata]
    assert "Mapping Lamps" in tag_names, "Mapping Lamps tag missing from tags_metadata"
